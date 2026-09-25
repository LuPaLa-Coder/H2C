"""H2C — Structured Agent Handoff Protocol — Runtime library."""

from h2c._version import __version__  # noqa: F401
from h2c.parser import parse
from h2c.validator import Validator, ValidationError, ValidationResult
from h2c.state import StateMachine, State
from h2c.runtime import Agent, run_chain
from h2c.transpiler import transpile

__all__ = [
    "__version__",
    "parse",
    "Validator",
    "ValidationError",
    "ValidationResult",
    "StateMachine",
    "State",
    "Agent",
    "run_chain",
    "transpile",
]
