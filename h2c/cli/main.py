"""H2C CLI — command-line interface for the H2C protocol runtime.

Usage:
    h2c parse <file>       Parse .h2c file, output AST as JSON
    h2c validate <file>    Validate against protocol rules
    h2c transpile <file>   Transpile to nl|json|yaml|mcp
    h2c run <file>         Process chain through agent runtime
    h2c stats <file>       Show token savings statistics
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = _create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="h2c",
        description="H2C Semantic Compression Protocol — CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # parse
    p_parse = sub.add_parser("parse", help="Parse an H2C file and output JSON AST")
    p_parse.add_argument("file", help="Path to .h2c file")
    p_parse.add_argument("--compact", action="store_true", help="Compact JSON output")
    p_parse.set_defaults(func=_cmd_parse)

    # validate
    p_val = sub.add_parser("validate", help="Validate an H2C file against protocol rules")
    p_val.add_argument("file", help="Path to .h2c file")
    p_val.add_argument("--json", action="store_true", help="Output as JSON")
    p_val.set_defaults(func=_cmd_validate)

    # transpile
    p_trans = sub.add_parser("transpile", help="Transpile H2C to another format")
    p_trans.add_argument("file", help="Path to .h2c file")
    p_trans.add_argument("--to", dest="target", default="nl",
                         choices=["nl", "json", "yaml", "mcp"],
                         help="Target format (default: nl)")
    p_trans.add_argument("-o", "--output", help="Output file path")
    p_trans.set_defaults(func=_cmd_transpile)

    # run
    p_run = sub.add_parser("run", help="Run an H2C chain through the agent runtime")
    p_run.add_argument("file", help="Path to .h2c file")
    p_run.add_argument("--json", action="store_true", help="Output stats as JSON")
    p_run.set_defaults(func=_cmd_run)

    # stats
    p_stats = sub.add_parser("stats", help="Show token savings statistics")
    p_stats.add_argument("file", help="Path to .h2c file")
    p_stats.add_argument("--json", action="store_true", help="Output as JSON")
    p_stats.set_defaults(func=_cmd_stats)

    return parser


# ── Command implementations ──────────────────────────────────────────────────


def _print_diagnostics(diagnostics) -> bool:
    """Print parser diagnostics to stderr. Return True if any is error-level."""
    has_error = False
    for d in diagnostics:
        if d.level == "error":
            has_error = True
        loc = f" (line {d.line})" if d.line >= 0 else ""
        print(f"  [{d.level.upper()}] {d.code}: {d.message}{loc}", file=sys.stderr)
    return has_error


def _cmd_parse(args):
    from h2c.parser import parse_with_diagnostics

    text = Path(args.file).read_text()
    result = parse_with_diagnostics(text)

    indent = None if args.compact else 2
    output = json.dumps(result.message.to_json_ast(), indent=indent, ensure_ascii=False)
    print(output)

    if _print_diagnostics(result.diagnostics):
        sys.exit(1)


def _cmd_validate(args):
    from h2c.parser import parse_with_diagnostics
    from h2c.validator import Validator

    text = Path(args.file).read_text()
    parsed = parse_with_diagnostics(text)
    message = parsed.message
    parse_has_error = _print_diagnostics(parsed.diagnostics)
    validator = Validator()
    result = validator.validate(message)

    if args.json:
        print(json.dumps(result.to_json(), indent=2))
    else:
        print(result.summary())
        for e in result.errors:
            loc = f" (block {e.location['block']})" if e.location else ""
            print(f"  [{e.level.upper()}] {e.rule}: {e.message}{loc}")

    sys.exit(0 if (result.valid and not parse_has_error) else 1)


def _cmd_transpile(args):
    from h2c.parser import parse as parse_h2c
    from h2c.transpiler import transpile

    text = Path(args.file).read_text()
    message = parse_h2c(text)
    output = transpile(message, args.target)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


def _cmd_run(args):
    from h2c.runtime.agent import run_chain

    stats = run_chain(args.file)

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print(f"Blocks processed:  {stats['blocks_processed']}")
        print(f"Final state:       {stats['final_state']}")
        print(f"Message counter:   {stats['msg_counter']}")
        print(f"Revision table:    {stats['revision_table']}")
        print(f"Cycles tracked:    {stats['cycle_registry']}")
        print(f"Findings:          {stats['findings_count']}")


def _cmd_stats(args):
    from h2c.parser import parse_with_diagnostics

    text = Path(args.file).read_text()
    parsed = parse_with_diagnostics(text)
    message = parsed.message

    # Count blocks by type
    type_counts = {}
    for b in message.blocks:
        key = f"{b.type}:{b.subtype}"
        type_counts[key] = type_counts.get(key, 0) + 1

    tokens, exact = _count_tokens(text)

    if args.json:
        output = {
            "protocol": "h2c_v1.4",
            "blocks": len(message.blocks),
            "block_types": type_counts,
            "h2c_tokens": tokens,
            "token_count_exact": exact,
        }
        print(json.dumps(output, indent=2))
    else:
        method = "tiktoken cl100k_base" if exact else "rough estimate (install tiktoken for exact)"
        print("H2C v1.4 — Token Statistics")
        print()
        print(f"  Blocks:           {len(message.blocks)}")
        print(f"  Block types:      {len(type_counts)}")
        print()
        print(f"  H2C tokens:        {tokens}  [{method}]")
        print()
        print("  Note: token savings depend entirely on the natural-language")
        print("  baseline you compare against — run conformance/benchmark.py")
        print("  with a real prompt to measure it, don't assume a fixed ratio.")
        print()
        print("  Block type breakdown:")
        for k, v in sorted(type_counts.items()):
            print(f"    {k:25s} {v}")

    if _print_diagnostics(parsed.diagnostics):
        sys.exit(1)


def _count_tokens(text: str) -> tuple[int, bool]:
    """Return (token_count, is_exact).

    Uses tiktoken cl100k_base when available (exact). The fallback is a coarse
    chars/token heuristic and is flagged as inexact — it must never be presented
    as a measured savings figure.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text)), True
    except Exception:
        # H2C wire text measured at ~2.7 chars/token on cl100k_base.
        return max(1, round(len(text) / 2.7)), False


def _estimate_tokens(text: str) -> int:
    """Back-compat shim: token count only (see :func:`_count_tokens`)."""
    return _count_tokens(text)[0]


if __name__ == "__main__":
    main()
