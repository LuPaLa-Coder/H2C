"""H2C validation result types.

Implements the validation output format from
docs/compiler/pipeline.md section 5.3.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationError:
    """A single validation finding."""

    level: str            # "error" | "warning"
    rule: str             # "VALIDATOR-1" | "R1" | ...
    message: str
    location: Optional[Dict[str, int]] = None  # {"line": N, "block": M}

    def to_dict(self) -> dict:
        d: Dict[str, Any] = {
            "level": self.level,
            "rule": self.rule,
            "message": self.message,
        }
        if self.location:
            d["location"] = self.location
        return d


@dataclass
class ValidationResult:
    """Aggregated validation result for a Message."""

    valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        "total_blocks": 0,
        "valid_blocks": 0,
        "errors": 0,
        "warnings": 0,
    })

    def add_error(self, error: ValidationError):
        self.errors.append(error)
        if error.level == "error":
            self.valid = False
            self.stats["errors"] += 1
        else:
            self.stats["warnings"] += 1

    def to_json(self) -> dict:
        """Emit validation result in the JSON format from pipeline.md §5.3."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "stats": self.stats,
        }

    def summary(self) -> str:
        s = self.stats
        status = "PASS" if self.valid else "FAIL"
        return (
            f"{status}: {s['total_blocks']} blocks, "
            f"{s['valid_blocks']} valid, "
            f"{s['errors']} errors, {s['warnings']} warnings"
        )
