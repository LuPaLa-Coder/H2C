#!/usr/bin/env python3
"""H2C Protocol Test Harness — deterministic validation of .h2c chain files.

Usage:
    python3 conformance/run.py              # Run all tests
    python3 conformance/run.py --verbose    # Detailed output per test
    python3 conformance/run.py --json       # JSON report output
    python3 conformance/run.py test1        # Run single test (test1-test5)

Exit code: 0 = all passed, 1 = at least one failure.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT))

from h2c.parser import parse  # noqa: E402
from h2c.runtime import Agent  # noqa: E402
from h2c.state import StateMachine  # noqa: E402
from h2c.validator import Validator  # noqa: E402

# ── Test definitions ──────────────────────────────────────────────────────────

TESTS = [
    {
        "id": "test1",
        "name": "Hello World",
        "complexity": "Simple",
        "file": "test1-hello-world.h2c",
        "description": (
            "Basic project: CTX:NEGOTIATE handshake + ARCH:PLAN + BUILD chain + ORCH:END"
        ),
        "checks": {
            "min_blocks": 5,
            "must_start_with": "CTX:NEGOTIATE",
            "must_end_with": "ORCH:END",
            "must_contain": ["STATE:ACK", "ARCH:PLAN", "BUILD:EXEC", "BUILD:DONE"],
        },
    },
    {
        "id": "test2",
        "name": "Calculator CLI",
        "complexity": "Medium",
        "file": "test2-calculator.h2c",
        "description": (
            "Calculator with fix cycle: TEST:FAIL → BUILD:FIX → BUILD:DONE → TEST:PASS"
        ),
        "checks": {
            "min_blocks": 8,
            "must_start_with": "CTX:NEGOTIATE",
            "must_end_with": "ORCH:END",
            "must_contain": [
                "BUILD:FIX", "TEST:FAIL", "TEST:PASS",
            ],
            "must_have_fields": [
                "cycle_id", "retry_n", "fail_count", "pass_count", "base_rev", "rev"
            ],
        },
    },
    {
        "id": "test3",
        "name": "Clean Architecture",
        "complexity": "Advanced",
        "file": "test3-clean-arch.h2c",
        "description": (
            "Refactoring with context management: CTX:PRIMITIVES, CTX:UPDATE, STATE:FINDINGS"
        ),
        "checks": {
            "min_blocks": 10,
            "must_start_with": "CTX:NEGOTIATE",
            "must_end_with": "ORCH:END",
            "must_contain": [
                "CTX:PRIMITIVES", "CTX:UPDATE", "STATE:FINDINGS",
            ],
        },
    },
    {
        "id": "test4",
        "name": "RAG Pipeline",
        "complexity": "Very Complex",
        "file": "test4-rag-pipeline.h2c",
        "description": (
            "Multi-agent RAG pipeline with multiple fix cycles, distinct cycle_id values"
        ),
        "checks": {
            "min_blocks": 12,
            "must_start_with": "CTX:NEGOTIATE",
            "must_end_with": "ORCH:END",
            "must_contain": [
                "BUILD:FIX", "TEST:PASS", "STATE:FINDINGS",
            ],
        },
    },
    {
        "id": "test5",
        "name": "Stress Test",
        "complexity": "Stress",
        "file": "test5-stress-130msg.h2c",
        "description": (  # noqa: E501
            "60+ messages: PRUNE every 5, COMPACT every 20, FREEZE beyond 100, "
            "BUILD:NACK, DAG validation"
        ),
        "checks": {
            "min_blocks": 60,
            "must_start_with": "CTX:NEGOTIATE",
            "must_end_with": "ORCH:END",
            "must_contain": [
                "CTX:PRUNE", "CTX:COMPACT", "BUILD:NACK",
            ],
        },
    },
]


def run_test(test_def: dict, verbose: bool = False) -> dict:
    """Run a single test and return its result."""
    result = {
        "id": test_def["id"],
        "name": test_def["name"],
        "complexity": test_def["complexity"],
        "passed": True,
        "checks": {},
        "errors": [],
        "stats": {},
    }

    filepath = FIXTURES / test_def["file"]
    if not filepath.exists():
        result["passed"] = False
        result["errors"].append(f"Fixture not found: {filepath}")
        return result

    text = filepath.read_text()

    # ── Phase 1: Parse ───────────────────────────────────────────────────
    try:
        message = parse(text)
    except Exception as e:
        result["passed"] = False
        result["errors"].append(f"Parse error: {e}")
        return result

    # ── Phase 2: Validate ─────────────────────────────────────────────────
    validator = Validator()
    validation = validator.validate(message)

    # Basic block count
    block_count = len(message.blocks)
    min_blocks = test_def["checks"].get("min_blocks", 0)
    result["checks"]["block_count"] = {
        "actual": block_count,
        "expected_min": min_blocks,
        "ok": block_count >= min_blocks,
    }
    if not result["checks"]["block_count"]["ok"]:
        result["passed"] = False
        result["errors"].append(
            f"Block count: {block_count} < {min_blocks} minimum"
        )

    # First/last block checks
    if message.blocks:
        first_key = f"{message.blocks[0].type}:{message.blocks[0].subtype}"
        expected_first = test_def["checks"].get("must_start_with", "")
        result["checks"]["first_block"] = {
            "actual": first_key,
            "expected": expected_first,
            "ok": first_key == expected_first,
        }
        if not result["checks"]["first_block"]["ok"]:
            result["passed"] = False
            result["errors"].append(f"First block: {first_key} != {expected_first}")

        last_key = f"{message.blocks[-1].type}:{message.blocks[-1].subtype}"
        expected_last = test_def["checks"].get("must_end_with", "")
        result["checks"]["last_block"] = {
            "actual": last_key,
            "expected": expected_last,
            "ok": last_key == expected_last,
        }
        if not result["checks"]["last_block"]["ok"]:
            result["passed"] = False
            result["errors"].append(f"Last block: {last_key} != {expected_last}")

    # Must-contain checks
    present_keys = {f"{b.type}:{b.subtype}" for b in message.blocks}
    for required_key in test_def["checks"].get("must_contain", []):
        ok = required_key in present_keys
        result["checks"][f"contains_{required_key}"] = {
            "ok": ok,
            "detail": f"{required_key}: {'found' if ok else 'MISSING'}",
        }
        if not ok:
            result["passed"] = False
            result["errors"].append(f"Missing required block: {required_key}")

    # Must-have-fields check (across all blocks)
    required_fields = test_def["checks"].get("must_have_fields", [])
    if required_fields:
        all_field_keys = set()
        for b in message.blocks:
            for f in b.fields:
                all_field_keys.add(f.key)
        for field_name in required_fields:
            ok = field_name in all_field_keys
            result["checks"][f"field_{field_name}"] = {
                "ok": ok,
                "detail": f"{field_name}: {'found' if ok else 'MISSING'}",
            }
            if not ok:
                result["passed"] = False
                result["errors"].append(f"Missing required field: {field_name}")

    # Validation errors (only real errors, not warnings)
    error_count = sum(1 for e in validation.errors if e.level == "error")
    result["checks"]["validation_errors"] = {
        "count": error_count,
        "ok": error_count == 0,
    }
    if error_count > 0:
        result["passed"] = False
        errors_detail = [e.message for e in validation.errors if e.level == "error"]
        result["errors"].append(f"Validation errors: {errors_detail}")

    # ── Phase 3: State Machine ────────────────────────────────────────────
    try:
        fsm = StateMachine()
        for block in message.blocks:
            fsm.transition(block)
        reached_term = fsm.is_terminal()
        result["checks"]["state_machine"] = {
            "final_state": fsm.current_state.value,
            "reached_terminal": reached_term,
            "ok": reached_term,
        }
        if not reached_term:
            result["passed"] = False
            result["errors"].append(
                f"State machine did not reach TERM (final: {fsm.current_state.value})"
            )
    except Exception as e:
        result["checks"]["state_machine"] = {"ok": False, "error": str(e)}
        result["passed"] = False
        result["errors"].append(f"State machine error: {e}")

    # ── Phase 4: Agent Runtime ────────────────────────────────────────────
    try:
        agent = Agent()
        agent.run(message)
        result["checks"]["agent_runtime"] = {
            "msg_counter": agent.state_machine.memory.msg_counter,
            "final_state": agent.state_machine.current_state.value,
            "ok": True,
        }
    except Exception as e:
        result["checks"]["agent_runtime"] = {"ok": False, "error": str(e)}
        result["passed"] = False
        result["errors"].append(f"Agent runtime error: {e}")

    # ── Stats ─────────────────────────────────────────────────────────────
    result["stats"] = {
        "blocks": block_count,
        "validation": {
            "total": validation.stats.get("total_blocks", 0),
            "valid": validation.stats.get("valid_blocks", 0),
        },
    }

    return result


def print_summary(results: list, verbose: bool = False):
    """Print test results summary."""
    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print()
    print("=" * 72)
    print(f"  H2C Protocol Test Harness — Results: {passed}/{total} passed")
    print("=" * 72)
    print()

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        icon = "✅" if r["passed"] else "❌"
        print(f"  {icon} {r['id']:6s} {r['name']:<25s} [{r['complexity']:12s}]  {status}")

        if verbose or not r["passed"]:
            for check_name, check_val in r["checks"].items():
                if isinstance(check_val, dict) and not check_val.get("ok", True):
                    print(f"       └─ {check_name}: FAIL — {check_val.get('detail', '')}")
            for err in r["errors"]:
                print(f"       └─ ERROR: {err}")

    print()
    if passed == total:
        print("  ✅ All tests passed.")
    else:
        print(f"  ❌ {total - passed} test(s) failed.")
    print()


def print_json_report(results: list):
    """Print results as JSON."""
    report = {
        "protocol": "h2c_v1.4",
        "passed": sum(1 for r in results if r["passed"]),
        "total": len(results),
        "tests": [],
    }
    for r in results:
        report["tests"].append({
            "id": r["id"],
            "name": r["name"],
            "complexity": r["complexity"],
            "passed": r["passed"],
            "checks": {k: v for k, v in r["checks"].items() if isinstance(v, dict)},
            "errors": r["errors"],
            "stats": r["stats"],
        })
    print(json.dumps(report, indent=2))


def main():
    import argparse
    p = argparse.ArgumentParser(description="H2C Protocol Test Harness")
    p.add_argument("filter", nargs="?", help="Run single test by id (e.g. test1)")
    p.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    p.add_argument("--json", action="store_true", help="JSON report output")
    args = p.parse_args()

    to_run = TESTS
    if args.filter:
        to_run = [t for t in TESTS if t["id"] == args.filter]
        if not to_run:
            print(f"Unknown test: {args.filter}. Available: {[t['id'] for t in TESTS]}")
            sys.exit(1)

    results = [run_test(t, verbose=args.verbose) for t in to_run]

    if args.json:
        print_json_report(results)
    else:
        print_summary(results, verbose=args.verbose)

    passed = all(r["passed"] for r in results)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
