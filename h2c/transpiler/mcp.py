"""H2C-to-MCP codegen.

Implements the MCP tool call format from docs/compiler/pipeline.md section 3.3.
"""

from typing import Any

from h2c.parser.ast import Block, Message


class MCPCodegen:
    """Transpiles H2C blocks into MCP (Model Context Protocol) tool calls."""

    def generate(self, block: Block, request_id: int = 1) -> dict[str, Any]:
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

    def generate_batch(self, message: Message) -> list[dict[str, Any]]:
        """Generate MCP tool calls for all blocks in a message."""
        return [
            self.generate(block, request_id=i + 1)
            for i, block in enumerate(message.blocks)
        ]

    def _extract_arguments(self, block: Block) -> dict[str, Any]:
        from h2c.parser.ast import (
            IntegerValue,
            ListValue,
            RevisionValue,
            SignedIntValue,
            StringValue,
        )

        args: dict[str, Any] = {}
        for field in block.fields:
            key = field.key.lstrip("~")
            val = field.value
            if isinstance(val, (StringValue, IntegerValue, SignedIntValue, ListValue)):
                args[key] = val.data
            elif isinstance(val, RevisionValue):
                args[key] = {"file": val.file, "rev": val.rev}
        return args
