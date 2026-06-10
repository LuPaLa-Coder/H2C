"""H2C-to-JSON codegen.

Implements the JSON output format from docs/compiler/pipeline.md section 3.2
and the schema from docs/parser/schema.md.
"""

import json as _json
from typing import Any, Dict, List, Optional

from h2c.parser.ast import (
    Block,
    Field,
    IntegerValue,
    ListValue,
    Message,
    RevisionValue,
    SignedIntValue,
    StringValue,
)


class JSONCodegen:
    """Transpiles H2C AST to structured JSON."""

    def generate(self, message: Message, indent: int = 2) -> str:
        return _json.dumps(self.generate_ast(message), indent=indent)

    def generate_ast(self, message: Message) -> Dict[str, Any]:
        return {
            "protocol": "h2c_v1.4",
            "messages": [self.generate_block(b) for b in message.blocks],
        }

    def generate_block(self, block: Block) -> Dict[str, Any]:
        return {
            "type": block.type,
            "subtype": block.subtype,
            "fields": {f.key: _value_to_json(f.value) for f in block.fields},
        }


def _value_to_json(v) -> Any:
    if isinstance(v, StringValue):
        return v.data
    elif isinstance(v, IntegerValue):
        return v.data
    elif isinstance(v, SignedIntValue):
        return v.data
    elif isinstance(v, RevisionValue):
        return {"file": v.file, "rev": v.rev}
    elif isinstance(v, ListValue):
        # Parse list items: revision and signed_int strings become objects
        items = []
        for item in v.data:
            parsed = _parse_list_item(item)
            items.append(parsed)
        return items
    return str(v)


def _parse_list_item(item: str) -> Any:
    """Parse a single list element into its typed JSON form."""
    import re

    # Revision: file~N
    m = re.match(r"^(.+)~(\d+)$", item)
    if m:
        return {"file": m.group(1), "rev": int(m.group(2))}

    # Signed int: +N or -N
    m = re.match(r"^[+-]\d+$", item)
    if m:
        return int(item)

    # Integer: N
    m = re.match(r"^\d+$", item)
    if m:
        return int(item)

    # String
    return item
