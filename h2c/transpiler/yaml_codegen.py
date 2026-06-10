"""H2C-to-YAML codegen.

Implements the YAML output format from docs/compiler/pipeline.md section 3.4.
"""

from typing import Any, Dict, List

from h2c.parser.ast import (
    Block,
    IntegerValue,
    ListValue,
    Message,
    RevisionValue,
    SignedIntValue,
    StringValue,
)


class YAMLCodegen:
    """Transpiles H2C AST to YAML format."""

    def generate(self, message: Message) -> str:
        """Generate YAML string (simple emitter, no PyYAML dependency)."""
        return _emit_yaml({"messages": [self.generate_block(b) for b in message.blocks]})

    def generate_block(self, block: Block) -> Dict[str, Any]:
        fields = {}
        for f in block.fields:
            v = f.value
            if isinstance(v, StringValue):
                fields[f.key] = v.data
            elif isinstance(v, IntegerValue):
                fields[f.key] = v.data
            elif isinstance(v, SignedIntValue):
                fields[f.key] = v.data
            elif isinstance(v, ListValue):
                fields[f.key] = v.data
            elif isinstance(v, RevisionValue):
                fields[f.key] = {"file": v.file, "rev": v.rev}
        return {f"{block.type.lower()}_{block.subtype.lower()}": fields}


def _emit_yaml(obj, indent: int = 0) -> str:
    """Minimal YAML emitter (no external dependency)."""
    prefix = "  " * indent
    lines = []

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        for key, value in obj.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(_emit_yaml(value, indent + 1))
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{prefix}{key}: []")
                else:
                    lines.append(f"{prefix}{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            lines.append(f"{prefix}  -")
                            lines.append(_emit_yaml(item, indent + 2))
                        else:
                            lines.append(f"{prefix}  - {_yaml_str(item)}")
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
            elif isinstance(value, int):
                lines.append(f"{prefix}{key}: {value}")
            elif value is None:
                lines.append(f"{prefix}{key}: null")
            else:
                lines.append(f"{prefix}{key}: {_yaml_str(value)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.append(_emit_yaml(item, indent + 1))
            else:
                lines.append(f"{prefix}- {_yaml_str(item)}")
    else:
        lines.append(f"{prefix}{_yaml_str(obj)}")

    return "\n".join(filter(None, lines))


def _yaml_str(value) -> str:
    """Quote a string for YAML if needed."""
    s = str(value)
    # Simple heuristic: quote strings that look like they need it
    if any(c in s for c in (":", "#", "{", "}", "[", "]", ",", "&", "*", "!", ">", "|", "'", '"', "%", "@", "`")):
        return f'"{s}"'
    return s
