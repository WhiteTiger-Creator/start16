#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# CGO_ENABLED=0 because the contract says the planner is built with cgo off.
# The image sets it too; saying it here keeps the reference run honest on its
# own terms rather than on the environment's.
export GOCACHE=/tmp/gocache GO111MODULE=off GOPATH=/tmp/gopath CGO_ENABLED=0

# --- Step 1: rebuild the authoritative checkpoint registry (#ML-6170) -------
# The migration left /app/data/checkpoint_registry.json holding a truncated
# prefix. Replay the migrator journal onto the pre-migration snapshot and write
# the result back to that path.

go run "${SCRIPT_DIR}/recover_registry.go"

# --- Step 2: restore the planner and produce the resume artifacts -----------

cp "${SCRIPT_DIR}/plan_resume_fixed.go" /app/workflow/plan_resume.go
go run /app/workflow/plan_resume.go --output-dir /app/output
