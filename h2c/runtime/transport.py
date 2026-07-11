"""H2C Transport bindings.

Implements the 5 transport bindings from docs/agent-runtime/protocol.md section 4.
"""

from abc import ABC, abstractmethod
from typing import Optional

from h2c.parser.ast import Block, Message


class Transport(ABC):
    """Abstract transport layer for sending/receiving H2C blocks."""

    @abstractmethod
    def send(self, block: Block) -> None:
        """Send an H2C block."""

    @abstractmethod
    def receive(self) -> Optional[Block]:
        """Receive an H2C block, or None if no more input."""

    @abstractmethod
    def send_message(self, message: Message) -> None:
        """Send a full message (all blocks)."""

    @abstractmethod
    def receive_message(self) -> Optional[Message]:
        """Receive a full message."""

    @abstractmethod
    def close(self) -> None:
        """Close the transport."""


class StdinStdoutTransport(Transport):
    """Read/write H2C blocks on stdin/stdout.

    Each block is written as raw H2C text followed by a blank line.
    """

    def send(self, block: Block) -> None:
        text = _block_to_text(block)
        print(text)

    def receive(self) -> Optional[Block]:
        """Read a block from stdin. Returns None on EOF."""
        try:
            lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                lines.append(line)
            if not lines:
                return None
            from h2c.parser.parser import parse
            msg = parse("\n".join(lines))
            return msg.blocks[0] if msg.blocks else None
        except EOFError:
            return None

    def send_message(self, message: Message) -> None:
        for block in message.blocks:
            self.send(block)
            print()  # blank line between blocks

    def receive_message(self) -> Optional[Message]:
        """Read all blocks until a double-blank or EOF."""
        blocks = []
        while True:
            block = self.receive()
            if block is None:
                break
            blocks.append(block)
        return Message(blocks=blocks) if blocks else None

    def close(self) -> None:
        pass


class FileTransport(Transport):
    """Read/write H2C blocks from/to a .h2c file."""

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._output_lines: list = []

    def send(self, block: Block) -> None:
        self._output_lines.append(_block_to_text(block))

    def receive(self) -> Optional[Block]:
        raise NotImplementedError("Use receive_message for file transport")

    def send_message(self, message: Message) -> None:
        for block in message.blocks:
            self.send(block)

    def receive_message(self) -> Optional[Message]:
        try:
            with open(self._filepath) as f:
                text = f.read()
            from h2c.parser.parser import parse
            return parse(text)
        except FileNotFoundError:
            return None

    def flush(self):
        """Write accumulated blocks to the file."""
        with open(self._filepath, "w") as f:
            f.write("\n\n".join(self._output_lines) + "\n")

    def close(self) -> None:
        if self._output_lines:
            self.flush()


def _block_to_text(block: Block) -> str:
    """Serialize a Block back to H2C wire format.

    Delegates to H2CSerializer for consistency.
    """
    from h2c.transpiler.serializer import serialize_block
    return serialize_block(block)
