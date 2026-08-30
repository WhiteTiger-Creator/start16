// Resume planner shipped before the run review.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
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

func main() {
	input := flag.String("input", "/app/data/checkpoint_registry.json", "checkpoint registry")
	outputDir := flag.String("output-dir", "/app/output", "output directory")
	flag.Parse()

	var entries []entry
	var shards []dataShard
	var inc incident
	var pol policy
	// the catalogue, the incident and the policy live at fixed paths;
	// --input selects the registry
	readJSON("/app/data/shard_catalog.json", &shards)
	readJSON("/app/data/data_incident.json", &inc)
	readJSON("/app/data/resume_policy.json", &pol)
	readJSON(*input, &entries)

	worldSize := int(pol.Default["world_size"])
	budget := pol.Default["refetch_budget_bytes"]
	maxRefetch := int(pol.Default["max_refetch_shards"])

	// which checkpoints count as complete
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

	// admissibility against the incident window
	// admissibility against the incident window
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
			if !present[s][key{r, "model"}] {
				complete = false
				break
			}
		}
		admissible := complete
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

	// which shards go back on the fetch queue
	// which shards go back on the fetch queue
	poisoned := map[int]bool{}
	for _, ep := range inc.PoisonedEpochs {
		poisoned[ep] = true
	}
	needed := make([]refetchRow, 0)
	for _, s := range shards {
		reason := ""
		if s.StoredChecksum != s.ExpectedChecksum {
			reason = "checksum_mismatch"
			if poisoned[s.Epoch] {
				reason = "poisoned_epoch"
			}
		}
		if reason != "" {
			needed = append(needed, refetchRow{s.ShardID, s.Epoch, s.Bytes, reason})
		}
	}
	// emission order for the fetch queue
	sort.Slice(needed, func(i, j int) bool {
		if needed[i].Bytes != needed[j].Bytes {
			return needed[i].Bytes > needed[j].Bytes
		}
		return needed[i].ShardID < needed[j].ShardID
	})

	planned := make([]refetchRow, 0)
	deferred := make([]refetchRow, 0)
	var spent int64
	for _, row := range needed {
		if len(planned) < maxRefetch && spent+row.Bytes <= budget {
			planned = append(planned, row)
			spent += row.Bytes
			continue
		}
		deferred = append(deferred, row)
	}

	if err := os.MkdirAll(*outputDir, 0o755); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
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
