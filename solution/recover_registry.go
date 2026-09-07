// Stage one of the reference: rebuild the checkpoint registry the failed storage
// migration truncated at /app/data/checkpoint_registry.json.
//
// Governed by #ML-6170 (replay semantics) and #ML-6174 (shape of the result).
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strconv"
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

type change struct {
	Seq     int    `json:"seq"`
	EntryID string `json:"entry_id"`
	Kind    string `json:"kind"`
	Field   string `json:"field"`
	Value   any    `json:"value"`
}

func readJSON(path string, into any) {
	raw, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	// UseNumber, not a plain Unmarshal: a journal value decoded into `any` lands
	// as float64, and a float64 cannot hold every int64. 9007199254740993 comes
	// back 9007199254740992 -- a byte figure the contract says may take any value
	// up to the int64 ceiling, silently rewritten by one on the way in. A
	// json.Number keeps the digits as written and is converted exactly below.
	// Fields decoded into typed int64 struct members were never affected; only
	// the amendment's untyped value was.
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := decoder.Decode(into); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func asInt64(value any) (int64, bool) {
	switch t := value.(type) {
	case json.Number:
		// the digits exactly as the journal wrote them, so a value past 2^53
		// keeps every one of them
		n, err := t.Int64()
		return n, err == nil
	case float64:
		return int64(t), true
	case string:
		n, err := strconv.ParseInt(t, 10, 64)
		return n, err == nil
	}
	return 0, false
}

// #ML-6170 says an amendment "overwrites the named field in place" and does not
// restrict which field it may name, so every field the record declares is
// settable here. Covering only checksum, shard_id and bytes silently dropped an
// amendment against any of the others rather than applying it.
func setField(e *entry, field string, value any) {
	switch field {
	case "entry_id":
		if s, ok := value.(string); ok {
			e.EntryID = s
		}
	case "kind":
		if s, ok := value.(string); ok {
			e.Kind = s
		}
	case "checksum":
		if s, ok := value.(string); ok {
			e.Checksum = s
		}
	case "shard_id":
		if s, ok := value.(string); ok {
			e.ShardID = s
		}
	case "step":
		if n, ok := asInt64(value); ok {
			e.Step = n
		}
	case "rank":
		if n, ok := asInt64(value); ok {
			e.Rank = int(n)
		}
	case "written_seq":
		if n, ok := asInt64(value); ok {
			e.WrittenSeq = int(n)
		}
	case "bytes":
		if n, ok := asInt64(value); ok {
			e.Bytes = n
		}
	}
}

func main() {
	var snapshot []entry
	var journal []change
	readJSON("/app/data/registry_snapshot_pre_migration.json", &snapshot)
	readJSON("/app/data/registry_journal.json", &journal)

	live := make(map[string]*entry, len(snapshot))
	for i := range snapshot {
		e := snapshot[i]
		live[e.EntryID] = &e
	}
	// #ML-6170: an invalidation takes the entry out but the migrator keeps it, so a
	// later reinstatement returns it exactly as it stood when invalidated -- an
	// amendment posted before survives, one posted while it was out is lost.
	held := map[string]entry{}

	sort.Slice(journal, func(i, j int) bool { return journal[i].Seq < journal[j].Seq })
	for _, c := range journal {
		switch c.Kind {
		case "amend":
			if e, ok := live[c.EntryID]; ok {
				setField(e, c.Field, c.Value)
			}
		case "invalidate":
			if e, ok := live[c.EntryID]; ok {
				held[c.EntryID] = *e
				delete(live, c.EntryID)
			}
		case "reinstate":
			if e, ok := held[c.EntryID]; ok {
				restored := e
				live[c.EntryID] = &restored
				delete(held, c.EntryID)
			}
		}
	}

	out := make([]entry, 0, len(live))
	for _, e := range live {
		out = append(out, *e)
	}
	// #ML-6174: ascending step, then rank, then kind, then entry id.
	sort.Slice(out, func(i, j int) bool {
		a, b := out[i], out[j]
		if a.Step != b.Step {
			return a.Step < b.Step
		}
		if a.Rank != b.Rank {
			return a.Rank < b.Rank
		}
		if a.Kind != b.Kind {
			return a.Kind < b.Kind
		}
		return a.EntryID < b.EntryID
	})

	encoded, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile("/app/data/checkpoint_registry.json", append(encoded, '\n'), 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Fprintf(os.Stderr, "recovered %d entries\n", len(out))
}
