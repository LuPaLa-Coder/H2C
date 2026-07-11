#!/bin/bash
# H2C Protocol Conformance Test Runner
# Usage: ./conformance/run.sh [--verbose] [--json] [test_id]
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 conformance/run.py "$@"
