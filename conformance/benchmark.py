#!/usr/bin/env python3
"""H2C v1.4 Deterministic Benchmark Runner.

Elimina il problema del benchmark originale: ogni LLM contava l'NL reference
in modo diverso, invalidando il confronto.

Workflow:
  1. python3 conformance/benchmark.py data    → mostra metriche NL pre-calcolate
  2. python3 conformance/benchmark.py prompt   → genera prompt da dare all'LLM
  3. Incolla il prompt nell'LLM, salva output in un file
  4. python3 conformance/benchmark.py report < output_llm.txt → report finale

In uno step solo (prompt + analisi già fatta):
  python3 conformance/benchmark.py report --model "Claude Sonnet 5" < output_llm.txt
"""

import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT / "conformance" / "benchmark_prompt.md"

# ── Constants ───────────────────────────────────────────────────────────────────

CHARS_PER_TOKEN_H2C = 3.7
CHARS_PER_TOKEN_NL = 1.3


# ── Counting utilities (deterministic) ──────────────────────────────────────────

def count_chars(text: str) -> int:
    return len(text)


def count_words(text: str) -> int:
    return len(text.split())


def est_tokens(text: str, ratio: float) -> int:
    return round(len(text) / ratio)


def est_tokens_h2c(text: str) -> int:
    return est_tokens(text, CHARS_PER_TOKEN_H2C)


def est_tokens_nl(text: str) -> int:
    return est_tokens(text, CHARS_PER_TOKEN_NL)


# ── Extract NL references from benchmark_prompt.md ─────────────────────────────

def extract_nl_references() -> list[dict]:
    """Parse benchmark_prompt.md and extract each NL reference text with its scenario name."""
    text = PROMPT_FILE.read_text(encoding="utf-8")

    scenarios = []
    # Pattern: "## Scenario N — Name" followed by "**Reference NL (FIXED ...):**" then ``` ... ```
    # We look for scenario headers and then the first fenced code block after "Reference NL"
    parts = re.split(r"^## Scenario \d+.*?$", text, flags=re.MULTILINE)[1:]  # skip intro

    current_scenarios = re.findall(
        r"^## (Scenario \d+.*?)$", text, re.MULTILINE
    )

    scenario_names = []
    for s in current_scenarios:
        # Extract name from "Scenario N — Name (description)"
        m = re.match(r"Scenario \d+.*?[—–-]\s*(.*?)(?:\s*\(|$)", s)
        if m:
            scenario_names.append(m.group(1).strip())
        else:
            # Fallback: use the full line after the number
            m2 = re.match(r"Scenario \d+\s+(.*)", s)
            scenario_names.append(m2.group(1).strip() if m2 else s.strip())

    # Now for each scenario section, find the NL reference fenced block
    # Split on scenario headers
    sections = re.split(r"(?=^## Scenario \d+)", text, flags=re.MULTILINE)[1:]

    results = []
    for i, section in enumerate(sections):
        name = scenario_names[i] if i < len(scenario_names) else f"Scenario {i+1}"

        # Extract scenario description: everything between the title and "Reference NL"
        desc_match = re.search(
            r"(?:Reference NL|Genera la catena)",
            section,
        )
        desc = ""
        if desc_match:
            # Everything after the first line (the title was in the split) up to Reference NL / instructions
            # The section starts after the ## title; everything up to "Reference NL" or "Genera la catena" is the description
            desc_raw = section[: desc_match.start()].strip()
            # Remove trailing markdown formatting
            desc = re.sub(r"\*{0,2}$", "", desc_raw).strip()
        else:
            desc = section.strip()

        # Find fenced code block (```...```) that follows "Reference NL"
        nl_match = re.search(
            r"\*{0,2}Reference NL\s*\(FIXED[^)]*\):\*{0,2}\s*\n\s*```(?:\w*)\n(.*?)```",
            section,
            re.DOTALL,
        )
        if nl_match:
            ref_text = nl_match.group(1).strip()
            results.append({"name": name, "text": ref_text, "description": desc})
        else:
            results.append({"name": name, "text": "", "description": desc})

    return results


# ── NL metrics (pre-computed, deterministic) ────────────────────────────────────

def compute_nl_metrics(scenarios: list[dict]) -> list[dict]:
    """Compute deterministic NL metrics for each scenario."""
    results = []
    for s in scenarios:
        text = s["text"]
        c = count_chars(text)
        w = count_words(text)
        results.append({
            "name": s["name"],
            "chars": c,
            "words": w,
            "est_tokens": est_tokens_nl(text),
        })
    return results


# ── H2C chain extraction from LLM output ───────────────────────────────────────

def extract_h2c_chains(llm_output: str) -> list[dict]:
    """Extract H2C chains from delimited LLM output.

    Returns list of dicts: {name, h2c_text} for each scenario found.
    """
    chains = []

    # Try to split by === SCENARIO N: NAME === delimiters
    # Pattern: === SCENARIO N: anything === then content until next delimiter or end
    blocks = re.split(
        r"===+\s*SCENARIO\s+(\d+)\s*[:：]\s*(.*?)\s*===+",
        llm_output,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # re.split with 3 capturing groups produces: [before, num1, name1, content1, num2, name2, content2, ...]
    if len(blocks) >= 4:
        for i in range(1, len(blocks), 3):
            if i + 2 < len(blocks):
                num = blocks[i].strip()
                name = blocks[i + 1].strip()
                content = blocks[i + 2].strip()

                # Clean markdown fences if present
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```\s*$", "", content)
                content = content.strip()

                # Remove leading/trailing blank lines
                chains.append({
                    "number": int(num),
                    "name": name,
                    "h2c_text": content,
                })

    if not chains:
        # Fallback: extract H2C blocks directly (any [TYPE:SUBTYPE]... pattern)
        # This catches undelimited output
        blocks_raw = re.findall(
            r"(?:^|\n{2,})((?:\[[A-Z]+:[A-Z]+\]\n(?:[^\[]+(?:\n|$))?)+)",
            llm_output,
        )
        if blocks_raw:
            chains.append({
                "number": 1,
                "name": "Unnamed",
                "h2c_text": "\n\n".join(b.strip() for b in blocks_raw),
            })

    return chains


# ── H2C chain metrics ──────────────────────────────────────────────────────────

def compute_h2c_metrics(scenarios: list[dict], chains: list[dict]) -> list[dict]:
    """Match extracted chains to scenarios and compute metrics."""
    results = []

    for s in scenarios:
        name = s["name"]
        # Find matching chain by number or name
        match = None
        for c in chains:
            # Match by name substring (normalized) or position
            if name.lower() in c["name"].lower() or c["name"].lower() in name.lower():
                match = c
                break
        # If no name match, match by position
        if match is None and chains:
            idx = scenarios.index(s)
            if idx < len(chains):
                match = chains[idx]

        text = match["h2c_text"] if match else ""
        results.append({
            "name": name,
            "nl": {
                "chars": s["chars"],
                "words": s["words"],
                "est_tokens": s["est_tokens"],
            },
            "h2c": {
                "chars": count_chars(text),
                "words": count_words(text),
                "est_tokens": est_tokens_h2c(text),
                "text": text,
            },
            "found": match is not None,
        })

    return results


# ── Scenario name mappings (template abbreviations) ──────────────────────────

SCENARIO_NAMES_SHORT = [
    "Hello World",
    "Calculator",
    "Clean Arch",
    "RAG Pipe",
    "Stress",
]


def scenario_short_name(metrics_entry: dict, idx: int) -> str:
    """Return the abbreviated scenario name from the template."""
    if 0 <= idx < len(SCENARIO_NAMES_SHORT):
        return SCENARIO_NAMES_SHORT[idx]
    return metrics_entry.get("name", f"Scenario {idx+1}")


# ── Report generation ──────────────────────────────────────────────────────────

def generate_report(metrics: list[dict], model_name: str = "") -> str:
    """Generate the benchmark report in the EXACT format from benchmark_prompt.md.

    Template:
        === H2C v1.4 Deterministic Benchmark ===
        Date: <YYYY-MM-DD>
        Model: <model>

        | # | Scenario    | H2C chars | NL chars | Ch save | H2C words | NL words | Wd save | Est.H2C tok | Est.NL tok | Tok save |
        |---|-------------|-----------|----------|---------|-----------|----------|---------|-------------|------------|----------|
        ...
        TOTAL: H2C chars=<N> | NL chars=<N> | Avg char save=<X>% | Avg token save=<X>%

        v1.4 Features:
          CTX:NEGOTIATE [ ]  STATE:ACK [ ]  BUILD:NACK [ ]  STATE:FINDINGS [ ]
          CTX:PRUNE     [ ]  CTX:COMPACT [ ]  CTX:FREEZE [ ]  Fix cycle [ ]
          DAG closure   [ ]
    """
    lines = []
    lines.append("=== H2C v1.4 Deterministic Benchmark ===")
    lines.append(f"Date: 2026-07-11")
    lines.append(f"Model: {model_name}")
    lines.append("")
    lines.append("| # | Scenario    | H2C chars | NL chars | Ch save | H2C words | NL words | Wd save | Est.H2C tok | Est.NL tok | Tok save |")
    lines.append("|---|-------------|-----------|----------|---------|-----------|----------|---------|-------------|------------|----------|")

    total_h2c_chars = 0
    total_nl_chars = 0
    total_h2c_words = 0
    total_nl_words = 0
    total_h2c_tok = 0.0
    total_nl_tok = 0.0

    for i, m in enumerate(metrics):
        nl = m["nl"]
        h2c = m["h2c"]
        sname = scenario_short_name(m, i)

        # Use floats with one decimal for percentages and token estimates
        h2c_ch = h2c["chars"]
        nl_ch = nl["chars"]
        h2c_w = h2c["words"]
        nl_w = nl["words"]
        h2c_tok = h2c["est_tokens"]
        nl_tok = nl["est_tokens"]

        ch_save = round((1 - h2c_ch / nl_ch) * 100, 1) if nl_ch else 0.0
        wd_save = round((1 - h2c_w / nl_w) * 100, 1) if nl_w else 0.0
        tok_save = round((1 - h2c_tok / nl_tok) * 100, 1) if nl_tok else 0.0

        total_h2c_chars += h2c_ch
        total_nl_chars += nl_ch
        total_h2c_words += h2c_w
        total_nl_words += nl_w
        total_h2c_tok += h2c_tok
        total_nl_tok += nl_tok

        lines.append(
            f"| {i+1} | {sname:<11} | {h2c_ch:<9} | {nl_ch:<8} | "
            f"{f'{ch_save}%':<8} | {h2c_w:<9} | {nl_w:<8} | "
            f"{f'{wd_save}%':<8} | {h2c_tok:<11.1f} | {nl_tok:<10.1f} | {f'{tok_save}%':<8} |"
        )

    # TOTAL line
    avg_char_save = round((1 - total_h2c_chars / total_nl_chars) * 100, 1) if total_nl_chars else 0.0
    avg_tok_save = round((1 - total_h2c_tok / total_nl_tok) * 100, 1) if total_nl_tok else 0.0

    lines.append("")
    lines.append(
        f"TOTAL: H2C chars={total_h2c_chars} | NL chars={total_nl_chars} | "
        f"Avg char save={avg_char_save}% | Avg token save={avg_tok_save}%"
    )
    lines.append("")

    # Feature checklist — detect from H2C text
    checks = {
        "CTX:NEGOTIATE": False,
        "STATE:ACK": False,
        "BUILD:NACK": False,
        "STATE:FINDINGS": False,
        "CTX:PRUNE": False,
        "CTX:COMPACT": False,
        "CTX:FREEZE": False,
        "Fix cycle": False,
        "DAG closure": False,
    }

    for m in metrics:
        text = m["h2c"]["text"]
        if re.search(r"\[CTX:NEGOTIATE\]", text):
            checks["CTX:NEGOTIATE"] = True
        if re.search(r"\[STATE:ACK\]", text):
            checks["STATE:ACK"] = True
        if re.search(r"\[BUILD:NACK\]", text):
            checks["BUILD:NACK"] = True
        if re.search(r"\[STATE:FINDINGS\]", text):
            checks["STATE:FINDINGS"] = True
        if re.search(r"\[CTX:PRUNE\]", text):
            checks["CTX:PRUNE"] = True
        if re.search(r"\[CTX:COMPACT\]", text):
            checks["CTX:COMPACT"] = True
        if re.search(r"\[CTX:FREEZE\]", text):
            checks["CTX:FREEZE"] = True
        if re.search(r"cycle_id:", text):
            checks["Fix cycle"] = True
        if re.search(r"dag|transitive.closure|dependency.graph|DAG", text, re.IGNORECASE):
            checks["DAG closure"] = True

    lines.append("v1.4 Features:")
    lines.append(
        f"  CTX:NEGOTIATE [{'X' if checks['CTX:NEGOTIATE'] else ' '}]  "
        f"STATE:ACK [{'X' if checks['STATE:ACK'] else ' '}]  "
        f"BUILD:NACK [{'X' if checks['BUILD:NACK'] else ' '}]  "
        f"STATE:FINDINGS [{'X' if checks['STATE:FINDINGS'] else ' '}]"
    )
    lines.append(
        f"  CTX:PRUNE     [{'X' if checks['CTX:PRUNE'] else ' '}]  "
        f"CTX:COMPACT [{'X' if checks['CTX:COMPACT'] else ' '}]  "
        f"CTX:FREEZE [{'X' if checks['CTX:FREEZE'] else ' '}]  "
        f"Fix cycle [{'X' if checks['Fix cycle'] else ' '}]"
    )
    lines.append(
        f"  DAG closure   [{'X' if checks['DAG closure'] else ' '}]"
    )

    return "\n".join(lines)


def generate_final_report(all_model_metrics: list[dict]) -> str:
    """Aggregate multi-model report (shorter format with comparison tables)."""
    lines = [
        "# H2C v1.4 — Benchmark Results",
        "",
        "Benchmark eseguito con `conformance/benchmark.py` (deterministico).",
        "Data: 2026-07-11. Metodo: caratteri, parole, token stimati (chars÷3.7 H2C, chars÷1.3 NL).",
        "",
        "**Le metriche NL sono PRE-COMPUTATE e IDENTICHE per tutti i modelli.**",
        "Il confronto è valido perché solo le catene H2C provengono dal LLM.",
        "",
    ]

    for model_data in all_model_metrics:
        model_name = model_data.get("model", "Unknown")
        metrics = model_data.get("metrics", [])
        lines.append(f"## {model_name}")
        lines.append("")
        lines.append("| Scenario | H2C chars | NL chars | Ch save | H2C words | NL words | Wd save | Est.H2C tok | Est.NL tok | Tok save |")
        lines.append("|----------|-----------|----------|---------|-----------|----------|---------|-------------|------------|----------|")

        total_h2c_ch = 0
        total_nl_ch = 0
        total_h2c_w = 0
        total_nl_w = 0
        total_h2c_tok = 0.0
        total_nl_tok = 0.0

        for i, m in enumerate(metrics):
            nl = m["nl"]
            h2c = m["h2c"]
            sname = scenario_short_name(m, i)

            ch_save = round((1 - h2c["chars"] / nl["chars"]) * 100, 1) if nl["chars"] else 0.0
            wd_save = round((1 - h2c["words"] / nl["words"]) * 100, 1) if nl["words"] else 0.0
            tok_save = round((1 - h2c["est_tokens"] / nl["est_tokens"]) * 100, 1) if nl["est_tokens"] else 0.0

            total_h2c_ch += h2c["chars"]
            total_nl_ch += nl["chars"]
            total_h2c_w += h2c["words"]
            total_nl_w += nl["words"]
            total_h2c_tok += h2c["est_tokens"]
            total_nl_tok += nl["est_tokens"]

            lines.append(
                f"| {sname} | {h2c['chars']} | {nl['chars']} | "
                f"{f'{ch_save}%':<7} | {h2c['words']} | {nl['words']} | "
                f"{f'{wd_save}%':<7} | {h2c['est_tokens']:.1f} | {nl['est_tokens']:.1f} | {f'{tok_save}%':<7} |"
            )

        avg_ch_save = round((1 - total_h2c_ch / total_nl_ch) * 100, 1) if total_nl_ch else 0.0
        avg_tok_save = round((1 - total_h2c_tok / total_nl_tok) * 100, 1) if total_nl_tok else 0.0
        lines.append(
            f"| **TOTALE** | **{total_h2c_ch}** | **{total_nl_ch}** | "
            f"**{avg_ch_save}%** | **{total_h2c_w}** | **{total_nl_w}** | "
            f"**{round((1 - total_h2c_w / total_nl_w) * 100, 1) if total_nl_w else 0.0}%** | "
            f"**{total_h2c_tok:.1f}** | **{total_nl_tok:.1f}** | **{avg_tok_save}%** |"
        )
        lines.append("")

    # Summary table
    lines.append("## Riepilogo")
    lines.append("")
    lines.append("| Modello | H2C tok | NL tok | Risparmio | Avg char save |")
    lines.append("|---------|---------|--------|-----------|---------------|")

    sorted_models = sorted(
        all_model_metrics,
        key=lambda md: (
            round(
                (1 - sum(m["h2c"]["est_tokens"] for m in md["metrics"])
                 / sum(m["nl"]["est_tokens"] for m in md["metrics"])) * 100, 1
            )
            if sum(m["nl"]["est_tokens"] for m in md["metrics"]) else 0.0
        ),
        reverse=True,
    )

    for model_data in sorted_models:
        model_name = model_data.get("model", "Unknown")
        metrics = model_data["metrics"]
        total_h2c = sum(m["h2c"]["est_tokens"] for m in metrics)
        total_nl = sum(m["nl"]["est_tokens"] for m in metrics)
        total_h2c_ch = sum(m["h2c"]["chars"] for m in metrics)
        total_nl_ch = sum(m["nl"]["chars"] for m in metrics)
        save_tok = round((1 - total_h2c / total_nl) * 100, 1) if total_nl else 0.0
        save_ch = round((1 - total_h2c_ch / total_nl_ch) * 100, 1) if total_nl_ch else 0.0
        lines.append(f"| {model_name} | {total_h2c:.1f} | {total_nl:.1f} | **{save_tok}%** | {save_ch}% |")

    lines.append("")
    lines.append("### Osservazioni")
    lines.append("")
    lines.append("- **NL baseline identico per tutti**: le metriche NL sono pre-calcolate dallo script.")
    lines.append("- Il risparmio dipende solo dalla qualità della catena H2C generata dal modello.")
    lines.append("- I modelli che generano catene più compatte ottengono risparmi migliori.")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "*Report generato con `conformance/benchmark.py report`. "
        "NL baseline deterministico, identico per tutti i modelli.*"
    )

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def cmd_data():
    """Show pre-computed NL reference metrics."""
    scenarios = extract_nl_references()
    metrics = compute_nl_metrics(scenarios)

    print("=" * 72)
    print("  H2C Benchmark — NL Reference Metrics (pre-computed, deterministic)")
    print("=" * 72)
    print()
    print(f"{'#':>3} {'Scenario':<30} {'Chars':>8} {'Words':>8} {'Est.Tok':>8}")
    print(f"{'':3} {'':30} {'':8} {'':8} {'':8}")
    print("-" * 60)

    total_chars = 0
    total_words = 0
    total_tokens = 0

    for i, m in enumerate(metrics):
        print(f"{i+1:>3} {m['name']:<30} {m['chars']:>8} {m['words']:>8} {m['est_tokens']:>8}")
        total_chars += m["chars"]
        total_words += m["words"]
        total_tokens += m["est_tokens"]

    print("-" * 60)
    print(f"{'':3} {'TOTALE':<30} {total_chars:>8} {total_words:>8} {total_tokens:>8}")
    print()

    # Output as JSON for piping
    if "--json" in sys.argv:
        print(json.dumps(metrics, indent=2))


def cmd_report():
    """Read LLM output from a file (or stdin) and produce the report."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=None, help="File con output LLM (default: stdin)")
    parser.add_argument("--model", "-m", default="", help="Model name for the report")
    parser.add_argument("--save", "-s", default="", help="Save to file (append if model specified)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args, _ = parser.parse_known_args(sys.argv[2:])

    if args.file:
        llm_output = Path(args.file).read_text(encoding="utf-8")
    else:
        llm_output = sys.stdin.read()

    if not llm_output.strip():
        print("ERROR: Nessun input ricevuto.", file=sys.stderr)
        print("Usa: python3 conformance/benchmark.py report output_llm.txt --model NOME", file=sys.stderr)
        sys.exit(1)

    if not llm_output.strip():
        print("ERROR: Nessun input ricevuto.", file=sys.stderr)
        print("Usa: python3 conformance/benchmark.py report output_llm.txt --model NOME", file=sys.stderr)
        sys.exit(1)

    scenarios = extract_nl_references()
    metrics = compute_nl_metrics(scenarios)
    chains = extract_h2c_chains(llm_output)

    if not chains:
        print("ERROR: Nessuna catena H2C trovata nell'output.", file=sys.stderr)
        print("Assicurati che l'output contenga delimitatori === SCENARIO N: NOME ===", file=sys.stderr)
        print()
        print("--- Prime 500 caratteri dell'output ricevuto ---")
        print(llm_output[:500])
        sys.exit(1)

    result = compute_h2c_metrics(metrics, chains)

    # Print the per-model report
    report = generate_report(result, args.model)
    print(report)

    # Save to file if requested
    if args.save:
        save_path = Path(args.save)
        # If model is specified, create the aggregated report
        if args.model:
            # Check if file exists and has existing model data
            existing = []
            if save_path.exists():
                try:
                    existing = json.loads(save_path.read_text())
                except (json.JSONDecodeError, ValueError):
                    pass
            # Append new model data
            existing.append({
                "model": args.model,
                "metrics": result,
            })
            save_path.write_text(json.dumps(existing, indent=2, default=str))
            # Also generate the multi-model report
            final = generate_final_report(existing)
            final_path = save_path.with_name("Result.md")
            final_path.write_text(final)
            print(f"\n(Salvato: {save_path} e {final_path})")
        else:
            # Just save raw report
            save_path.write_text(report)
            print(f"\n(Salvato: {save_path})")

    # JSON output for piping
    if "--json" in sys.argv:
        print("---JSON---")
        print(json.dumps(result, indent=2, default=str))


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 conformance/benchmark.py data                      # Mostra metriche NL pre-calcolate")
        print("  python3 conformance/benchmark.py report [file] [opts]      # Analizza output LLM (file o stdin)")
        print("    file              File con output LLM (default: stdin)")
        print("    --model NAME      Nome modello da includere nel report")
        print("    --save FILE       Salva dati JSON (appende se --model è usato)")
        print("    --json            Output JSON per piping")
        print()
        print("Workflow:")
        print("  1. Copia-incolla conformance/benchmark_prompt.md nella chat LLM")
        print("  2. Salva la risposta in un file (es. output.txt)")
        print("  3. python3 conformance/benchmark.py report output.txt --model NOME")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "data":
        cmd_data()
    elif cmd == "report":
        cmd_report()
    else:
        print(f"Comando sconosciuto: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
