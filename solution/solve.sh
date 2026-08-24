#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export GOCACHE=/tmp/gocache GO111MODULE=off GOPATH=/tmp/gopath

# --- Step 1: rebuild the authoritative checkpoint registry (#ML-6170) -------
# The migration left /app/data/checkpoint_registry.json holding a truncated
# prefix. Replay the migrator journal onto the pre-migration snapshot and write
# the result back to that path.

go run "${SCRIPT_DIR}/recover_registry.go"

# --- Step 2: restore the planner and produce the resume artifacts -----------

cp "${SCRIPT_DIR}/plan_resume_fixed.go" /app/workflow/plan_resume.go
go run /app/workflow/plan_resume.go --output-dir /app/output
