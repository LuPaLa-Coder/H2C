"""H2C-to-MCP codegen.

Implements the MCP tool call format from docs/compiler/pipeline.md section 3.3.
"""

from typing import Any, Dict, List

from h2c.parser.ast import Block, Message


class MCPCodegen:
    """Transpiles H2C blocks into MCP (Model Context Protocol) tool calls."""

    def generate(self, block: Block, request_id: int = 1) -> Dict[str, Any]:
        """Generate a single MCP tool call for an H2C block."""
        tool_name = f"h2c_{block.type.lower()}_{block.subtype.lower()}"
        arguments = self._extract_arguments(block)

        return {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": request_id,
        }

    def generate_batch(self, message: Message) -> List[Dict[str, Any]]:
        """Generate MCP tool calls for all blocks in a message."""
        return [
            self.generate(block, request_id=i + 1)
            for i, block in enumerate(message.blocks)
        ]

    def _extract_arguments(self, block: Block) -> Dict[str, Any]:
        from h2c.parser.ast import (
            IntegerValue,
            ListValue,
            RevisionValue,
            SignedIntValue,
            StringValue,
        )

        args = {}
        for field in block.fields:
            key = field.key.lstrip("~")
            val = field.value
            if isinstance(val, StringValue):
                args[key] = val.data
            elif isinstance(val, IntegerValue):
                args[key] = val.data
            elif isinstance(val, SignedIntValue):
                args[key] = val.data
            elif isinstance(val, ListValue):
                args[key] = val.data
            elif isinstance(val, RevisionValue):
                args[key] = {"file": val.file, "rev": val.rev}
        return args
