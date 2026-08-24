FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

ENV DEBIAN_FRONTEND=noninteractive

# The task is Go-only, so the canonical Go image carries the toolchain
# rather than a Python base with golang-go bolted on.
ENV GOCACHE=/tmp/gocache \
    GOPATH=/tmp/gopath \
    GO111MODULE=off

# Least-volatile layers first: fix the working directory before the apt and
# dependency layers so a change to those never invalidates the WORKDIR layer.
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

# /app/data/checkpoint_registry.json ships TRUNCATED exactly as the failed
# migration left it; the pre-migration snapshot and the migrator journal beside
# it are the recovery sources. All values are synthetic.
COPY app/ /app/
RUN cp /app/workflow/plan_resume.go /app/workflow/.plan_resume.original.go \
    && chmod a-w /app/workflow/.plan_resume.original.go
