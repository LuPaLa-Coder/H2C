"""H2C Reverse Compiler — Natural Language to H2C blocks.

Implements the pattern-matching strategy from docs/compiler/pipeline.md section 4.
Converts natural language prompts into H2C blocks.
Status: RESEARCH level — best-effort pattern matching.
"""

import re
from typing import List, Optional

from h2c.parser.ast import (
    Block,
    Field,
    ListValue,
    Message,
    StringValue,
)


class ReverseCompiler:
    """Compiles natural language prompts into H2C blocks.

    Uses pattern matching on typical prompt engineering structures:
    - "Crea un ... in ..." → id + fw
    - "Usa ... per ..." → lib
    - "Richiede ..." → auth
    - Technical notes in parentheses → notes
    """

    def compile(self, text: str) -> Message:
        """Convert NL text into H2C blocks. Returns a Message."""
        blocks: List[Block] = []

        arch_block = self._extract_architecture(text)
        if arch_block:
            blocks.append(arch_block)

        build_block = self._extract_build(text)
        if build_block:
            blocks.append(build_block)

        return Message(blocks=blocks)

    def _extract_architecture(self, text: str) -> Optional[Block]:
        """Extract ARCH:PLAN from NL text."""
        text_lower = text.lower()
        fields: List[Field] = []

        # id: project name
        m = re.search(
            r"(?:crea|create|build|sviluppa|implementa)\s+(?:un|un'|a|an|il)\s+"
            r"([a-zA-Z][a-zA-Z0-9_-]*)",
            text_lower,
        )
        if m:
            project = m.group(1)
            fields.append(Field(key="id", value=StringValue(data=project)))

        # fw: framework/language
        frameworks = [
            "python", "python3", "typescript", "javascript", "go", "rust",
            "c#", "java", "kotlin", "swift", "ruby", "php",
        ]
        for fw in frameworks:
            if fw in text_lower:
                fields.append(Field(key="fw", value=StringValue(data=fw)))
                break
        else:
            # Guess from context
            if "python" in text_lower or "fastapi" in text_lower or "django" in text_lower:
                fields.append(Field(key="fw", value=StringValue(data="python3")))
            elif "typescript" in text_lower or "react" in text_lower or "node" in text_lower:
                fields.append(Field(key="fw", value=StringValue(data="typescript")))

        # lib: libraries
        libs = []
        lib_patterns = [
            r"usa\s+([a-zA-Z0-9_/, ]+?)(?:\s+per|\s+come|\s*$|\.|,)",
            r"use\s+([a-zA-Z0-9_/, ]+?)(?:\s+for|\s+as|\s*$|\.|,)",
            r"con\s+([a-zA-Z0-9_/, ]+?)(?:\s+per|\s+come|\s*$|\.|,)",
            r"with\s+([a-zA-Z0-9_/, ]+?)(?:\s+for|\s+as|\s*$|\.|,)",
        ]
        for pat in lib_patterns:
            m = re.search(pat, text_lower)
            if m:
                lib_names = [l.strip() for l in m.group(1).split(",")]
                libs.extend(lib_names)
                break
        if libs:
            fields.append(Field(key="lib", value=StringValue(data=",".join(libs))))

        # auth
        if re.search(r"(?:auth|autenticaz|api[\s_-]?key|jwt|oauth)", text_lower):
            fields.append(Field(key="auth", value=StringValue(data="APIKey")))

        # notes
        notes = []
        note_patterns = [
            r"cache\s+(?:ttl\s+)?(\d+)\s*(?:min|sec)",
            r"(?:cache|ttl)[\s:]+(\d+)\s*(?:min|sec)",
            r"rate[\s_-]?limit",
            r"(?:solo|only|stdlib)[\s_-]?(?:stdlib|only|solo)",
        ]
        for pat in note_patterns:
            m = re.search(pat, text_lower)
            if m:
                if "cache" in pat or "ttl" in pat:
                    notes.append(f"cache_TTL_{m.group(1)}min")
                elif "rate" in pat:
                    notes.append("rate-limit")
                elif "stdlib" in pat or "solo" in pat:
                    notes.append("stdlib_only")
        if notes:
            fields.append(Field(key="notes", value=ListValue(data=notes)))

        if not fields:
            return None

        # Ensure required fields
        has_id = any(f.key == "id" for f in fields)
        has_fw = any(f.key == "fw" for f in fields)
        if not has_id:
            fields.insert(0, Field(key="id", value=StringValue(data="unnamed")))
        if not has_fw:
            fields.append(Field(key="fw", value=StringValue(data="python3")))

        return Block(type="ARCH", subtype="PLAN", fields=fields)

    def _extract_build(self, text: str) -> Optional[Block]:
        """Extract BUILD:EXEC from NL text."""
        # Look for file targets
        m = re.search(
            r"(?:file|crea|modifica|implementa|nel\s+file|in)\s+"
            r"([a-zA-Z0-9_/.-]+\.[a-zA-Z]+)",
            text.lower(),
        )
        if not m:
            return None

        target = m.group(1)
        fields = [
            Field(key="id", value=StringValue(data="m1")),
            Field(key="target", value=StringValue(data=target)),
        ]

        # desc: rest of the request
        desc_match = re.search(r"(?:per|to)\s+(.+?)(?:\.|$)", text.lower())
        if desc_match:
            desc = desc_match.group(1).strip()[:80]
            fields.append(Field(key="desc", value=StringValue(data=desc)))

        return Block(type="BUILD", subtype="EXEC", fields=fields)
