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


def _cmd_parse(args):
    from h2c.parser import parse as parse_h2c

    text = Path(args.file).read_text()
    message = parse_h2c(text)

    indent = None if args.compact else 2
    output = json.dumps(message.to_json_ast(), indent=indent, ensure_ascii=False)
    print(output)


def _cmd_validate(args):
    from h2c.parser import parse as parse_h2c
    from h2c.validator import Validator

    text = Path(args.file).read_text()
    message = parse_h2c(text)
    validator = Validator()
    result = validator.validate(message)

    if args.json:
        print(json.dumps(result.to_json(), indent=2))
    else:
        print(result.summary())
        for e in result.errors:
            loc = f" (block {e.location['block']})" if e.location else ""
            print(f"  [{e.level.upper()}] {e.rule}: {e.message}{loc}")

    sys.exit(0 if result.valid else 1)


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
    from h2c.parser import parse as parse_h2c

    text = Path(args.file).read_text()
    message = parse_h2c(text)

    # Count blocks by type
    type_counts = {}
    for b in message.blocks:
        key = f"{b.type}:{b.subtype}"
        type_counts[key] = type_counts.get(key, 0) + 1

    # Estimate token counts
    h2c_tokens = _estimate_tokens(text)
    # Estimate NL equivalent: ~6 tokens per H2C token
    nl_tokens = h2c_tokens * 6
    savings = nl_tokens - h2c_tokens
    pct = (savings / nl_tokens * 100) if nl_tokens > 0 else 0

    if args.json:
        output = {
            "protocol": "h2c_v1.4",
            "blocks": len(message.blocks),
            "block_types": type_counts,
            "h2c_tokens": h2c_tokens,
            "nl_tokens_estimated": nl_tokens,
            "tokens_saved": savings,
            "savings_pct": round(pct, 1),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"H2C v1.4 — Token Statistics")
        print()
        print(f"  Blocks:           {len(message.blocks)}")
        print(f"  Block types:      {len(type_counts)}")
        print()
        print(f"  H2C tokens:       {h2c_tokens}")
        print(f"  NL tokens (est):  {nl_tokens}")
        print(f"  Tokens saved:     {savings} (~{pct:.0f}%)")
        print()
        print(f"  Block type breakdown:")
        for k, v in sorted(type_counts.items()):
            print(f"    {k:25s} {v}")


def _estimate_tokens(text: str) -> int:
    """Estimate token count. Uses tiktoken if available, else len/3.2 fallback."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except (ImportError, Exception):
        return max(1, int(len(text) / 3.2))


if __name__ == "__main__":
    main()
