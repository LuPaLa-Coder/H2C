"""H2C Serializer — AST back to H2C wire format.

Public API for the round-trip: parse → modify AST → serialize.
"""

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


class H2CSerializer:
    """Serializes an H2C AST back to H2C wire format text."""

    def serialize(self, message: Message) -> str:
        """Serialize a full Message to H2C text.

        Blocks are separated by a blank line.
        """
        return "\n\n".join(
            self.serialize_block(b) for b in message.blocks
        )

    def serialize_block(self, block: Block) -> str:
        """Serialize a single Block to H2C text."""
        header = f"[{block.type}:{block.subtype}]"
        field_strs = []
        for field in block.fields:
            val_str = _value_to_str(field.value)
            key = field.key
            field_strs.append(f"{key}:{val_str}")
        return header + "\n" + "|".join(field_strs)


def _value_to_str(v) -> str:
    """Convert a value node back to its H2C wire representation."""
    if isinstance(v, StringValue):
        return v.data
    elif isinstance(v, IntegerValue):
        return str(v.data)
    elif isinstance(v, SignedIntValue):
        return f"+{v.data}" if v.data >= 0 else str(v.data)
    elif isinstance(v, RevisionValue):
        return f"{v.file}~{v.rev}"
    elif isinstance(v, ListValue):
        return "[" + ",".join(v.data) + "]"
    return str(v)


def serialize(message: Message) -> str:
    """Convenience function: serialize a Message to H2C text."""
    return H2CSerializer().serialize(message)


def serialize_block(block: Block) -> str:
    """Convenience function: serialize a single Block to H2C text."""
    return H2CSerializer().serialize_block(block)
