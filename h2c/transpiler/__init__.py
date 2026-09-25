from h2c.parser.ast import Block, Message
from h2c.transpiler.json_codegen import JSONCodegen
from h2c.transpiler.mcp import MCPCodegen
from h2c.transpiler.nl import NLCodegen
from h2c.transpiler.reverse import ReverseCompiler
from h2c.transpiler.serializer import H2CSerializer, serialize, serialize_block
from h2c.transpiler.yaml_codegen import YAMLCodegen


def transpile(message: Message, target: str = "nl") -> str:
    """Transpile a Message AST to the target format.

    Args:
        message: The parsed H2C Message.
        target: One of 'nl', 'json', 'mcp', 'yaml', 'h2c'.

    Returns:
        Transpiled string in the target format.
    """
    if target == "nl":
        return NLCodegen().generate(message)
    elif target == "json":
        return JSONCodegen().generate(message)
    elif target == "mcp":
        import json as _json
        return _json.dumps(
            MCPCodegen().generate_batch(message), indent=2
        )
    elif target == "yaml":
        return YAMLCodegen().generate(message)
    elif target == "h2c":
        return H2CSerializer().serialize(message)
    else:
        raise ValueError(f"Unknown target format: {target}")


__all__ = [
    "Block",
    "Message",
    "NLCodegen",
    "JSONCodegen",
    "MCPCodegen",
    "YAMLCodegen",
    "ReverseCompiler",
    "H2CSerializer",
    "serialize",
    "serialize_block",
    "transpile",
]
