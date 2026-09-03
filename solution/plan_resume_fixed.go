// Stage two of the reference: the corrected resume planner.
//
// Every governing value is traced to its final dated entry in
// /app/incident/training_governance_log.md; resume_contract.json supplies the
// output contract only and no derivation rule.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
)

type entry struct {
	EntryID    string `json:"entry_id"`
	Step       int64  `json:"step"`
	Rank       int    `json:"rank"`
	Kind       string `json:"kind"`
	ShardID    string `json:"shard_id"`
	Bytes      int64  `json:"bytes"`
	Checksum   string `json:"checksum"`
	WrittenSeq int    `json:"written_seq"`
}

type dataShard struct {
	ShardID          string `json:"shard_id"`
	Epoch            int    `json:"epoch"`
	Bytes            int64  `json:"bytes"`
	ExpectedChecksum string `json:"expected_checksum"`
	StoredChecksum   string `json:"stored_checksum"`
}

type incident struct {
	PoisonedEpochs []int `json:"poisoned_epochs"`
	StepsPerEpoch  int64 `json:"steps_per_epoch"`
}

type policy struct {
	Default map[string]int64 `json:"default"`
}

type checkpointRow struct {
	Step        int64 `json:"step"`
	ShardCount  int   `json:"shard_count"`
	RankCount   int   `json:"rank_count"`
	Complete    bool  `json:"complete"`
	Admissible  bool  `json:"admissible"`
	TotalBytes  int64 `json:"total_bytes"`
}

type refetchRow struct {
	ShardID string `json:"shard_id"`
	Epoch   int    `json:"epoch"`
	Bytes   int64  `json:"bytes"`
	Reason  string `json:"reason"`
}

func readJSON(path string, into any) {
	raw, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := json.Unmarshal(raw, into); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func writeJSON(path string, value any) {
	encoded, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile(path, append(encoded, '\n'), 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// The policy is read from its fixed absolute path, and any field the file omits
// keeps its governed baseline. A missing Go map key is zero, not the baseline,
// so the fallback has to be explicit.
func policyValue(pol policy, field string, baseline int64) int64 {
	if value, ok := pol.Default[field]; ok {
		return value
	}
	return baseline
}

func main() {
	input := flag.String("input", "/app/data/checkpoint_registry.json", "checkpoint registry")
	outputDir := flag.String("output-dir", "/app/output", "output directory")
	flag.Parse()

	var entries []entry
	var shards []dataShard
	var inc incident
	var pol policy
	// #ML-6150: the shard catalogue, the data incident and the resume policy are
	// always read from their fixed absolute paths; --input selects the registry.
	readJSON("/app/data/shard_catalog.json", &shards)
	readJSON("/app/data/data_incident.json", &inc)
	readJSON("/app/data/resume_policy.json", &pol)
	readJSON(*input, &entries)

	worldSize := int(policyValue(pol, "world_size", 16))
	budget := policyValue(pol, "refetch_budget_bytes", 35000000000)
	maxRefetch := int(policyValue(pol, "max_refetch_shards", 120))

	// #ML-6182: a checkpoint is COMPLETE only when every rank of the world holds
	// both a model and an optimizer shard. A rank missing either one leaves the
	// whole checkpoint unusable, however many other shards landed.
	type key struct {
		rank int
		kind string
	}
	present := map[int64]map[key]bool{}
	bytesAt := map[int64]int64{}
	for _, e := range entries {
		if present[e.Step] == nil {
			present[e.Step] = map[key]bool{}
		}
		present[e.Step][key{e.Rank, e.Kind}] = true
		bytesAt[e.Step] += e.Bytes
	}

	// #ML-6186: the run trained through the poisoned epochs, so a checkpoint is
	// admissible only where it was written STRICTLY BEFORE the first step of the
	// earliest poisoned epoch. A later checkpoint has already learned from the
	// corrupt shards and cannot be resumed from, complete or not.
	firstPoisoned := int64(-1)
	for _, ep := range inc.PoisonedEpochs {
		start := int64(ep) * inc.StepsPerEpoch
		if firstPoisoned < 0 || start < firstPoisoned {
			firstPoisoned = start
		}
	}

	steps := make([]int64, 0, len(present))
	for s := range present {
		steps = append(steps, s)
	}
	sort.Slice(steps, func(i, j int) bool { return steps[i] < steps[j] })

	checkpoints := make([]checkpointRow, 0, len(steps))
	var resumeStep int64 = -1
	completeCount, admissibleCount := 0, 0
	for _, s := range steps {
		ranks := map[int]bool{}
		for k := range present[s] {
			ranks[k.rank] = true
		}
		complete := true
		for r := 0; r < worldSize; r++ {
			if !present[s][key{r, "model"}] || !present[s][key{r, "optimizer"}] {
				complete = false
				break
			}
		}
		admissible := complete && (firstPoisoned < 0 || s < firstPoisoned)
		if complete {
			completeCount++
		}
		if admissible {
			admissibleCount++
			if s > resumeStep {
				resumeStep = s
			}
		}
		checkpoints = append(checkpoints, checkpointRow{
			Step: s, ShardCount: len(present[s]), RankCount: len(ranks),
			Complete: complete, Admissible: admissible, TotalBytes: bytesAt[s],
		})
	}

	// #ML-6190: a data shard must be re-fetched when its stored checksum disagrees
	// with the catalogue's expected checksum. Every shard of a poisoned epoch is
	// re-fetched as well, whatever its checksum says, because the adapter that
	// wrote them is not trusted.
	poisoned := map[int]bool{}
	for _, ep := range inc.PoisonedEpochs {
		poisoned[ep] = true
	}
	needed := make([]refetchRow, 0)
	for _, s := range shards {
		reason := ""
		switch {
		case poisoned[s.Epoch]:
			reason = "poisoned_epoch"
		case s.StoredChecksum != s.ExpectedChecksum:
			reason = "checksum_mismatch"
		}
		if reason != "" {
			needed = append(needed, refetchRow{s.ShardID, s.Epoch, s.Bytes, reason})
		}
	}
	// #ML-6194: the queue is taken in ascending epoch, then shard id -- the oldest
	// data the run will read again comes back first, never the largest shard.
	sort.Slice(needed, func(i, j int) bool {
		if needed[i].Epoch != needed[j].Epoch {
			return needed[i].Epoch < needed[j].Epoch
		}
		return needed[i].ShardID < needed[j].ShardID
	})

	// #ML-6194 admits a PREFIX of the ordered set: shards go in "until either
	// the policy's refetch_budget_bytes would be exceeded or its
	// max_refetch_shards is reached", so the first shard that does not fit ends
	// the admission and everything from there on is deferred in the same order.
	// Continuing past it to pick up a smaller later shard reorders the queue
	// against the rule and admits a set the board never described.
	planned := make([]refetchRow, 0)
	deferred := make([]refetchRow, 0)
	var spent int64
	full := false
	for _, row := range needed {
		// budget-spent rather than spent+bytes: the sum overflows int64 for a
		// budget near the type's ceiling and wraps negative, which admits a
		// shard the budget cannot actually hold. spent never exceeds budget,
		// so the difference is non-negative and the comparison cannot wrap.
		if !full && len(planned) < maxRefetch && row.Bytes <= budget-spent {
			planned = append(planned, row)
			spent += row.Bytes
			continue
		}
		full = true
		deferred = append(deferred, row)
	}

	if err := os.MkdirAll(*outputDir, 0o755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	// The contract has the output directory carry exactly the three named files,
	// so anything an earlier run left there is cleared before this run writes.
	// The directory itself stays: the run does not own the path it writes into.
	if entries, err := os.ReadDir(*outputDir); err == nil {
		for _, e := range entries {
			os.RemoveAll(filepath.Join(*outputDir, e.Name()))
		}
	}
	summary := map[string]any{
		"schema_version":              "resume-plan-v1",
		"entry_count":                 len(entries),
		"checkpoint_count":            len(checkpoints),
		"complete_checkpoint_count":   completeCount,
		"admissible_checkpoint_count": admissibleCount,
		"resume_step":                 resumeStep,
		"first_poisoned_step":         firstPoisoned,
		"refetch_needed_count":        len(needed),
		"refetch_planned_count":       len(planned),
		"refetch_deferred_count":      len(deferred),
		"refetch_planned_bytes":       spent,
		"effective_world_size":        worldSize,
		"effective_refetch_budget":    budget,
		"effective_max_refetch":       maxRefetch,
	}
	writeJSON(*outputDir+"/summary.json", summary)
	writeJSON(*outputDir+"/resume_plan.json", map[string]any{
		"resume_step": resumeStep,
		"checkpoints": checkpoints,
		"refetch":     planned,
	})

	handle, err := os.Create(*outputDir + "/refetch_queue.jsonl")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer handle.Close()
	enc := json.NewEncoder(handle)
	for _, row := range deferred {
		if err := enc.Encode(row); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	fmt.Fprintf(os.Stderr, "resume at step %d, %d shards planned, %d deferred\n",
		resumeStep, len(planned), len(deferred))
}
