"""H2C Global Memory Model.

Implements the 7 shared-memory components from
docs/specification/semantics.md section 6.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GlobalMemory:
    """Shared memory space between agents in an H2C chain.

    This memory is implicitly reconstructible by parsing the block history.
    The runtime maintains it explicitly for efficiency.
    """

    protocol_version: str = ""
    capabilities: List[str] = field(default_factory=list)
    msg_counter: int = 0
    prune_counter: int = 0
    compact_counter: int = 0
    context_state: Dict[str, Any] = field(default_factory=lambda: {
        "layer": "",
        "status": "",
        "next": "",
        "active_files": {},
    })
    revision_table: Dict[str, int] = field(default_factory=dict)
    cycle_registry: Dict[str, dict] = field(default_factory=dict)
    findings: List[dict] = field(default_factory=list)

    def increment_message(self):
        self.msg_counter += 1
        self.prune_counter += 1
        self.compact_counter += 1

    def reset_prune_counter(self):
        self.prune_counter = 0

    def reset_compact_counter(self):
        self.compact_counter = 0

    def reset_all_counters(self):
        self.prune_counter = 0
        self.compact_counter = 0

    def register_cycle(self, cycle_id: str):
        if cycle_id not in self.cycle_registry:
            self.cycle_registry[cycle_id] = {
                "retry_n": 0,
                "fail_count": 0,
                "pass_count": 0,
                "status": "open",
            }

    def increment_retry(self, cycle_id: str):
        self.register_cycle(cycle_id)
        self.cycle_registry[cycle_id]["retry_n"] += 1

    def increment_fail(self, cycle_id: str):
        self.register_cycle(cycle_id)
        self.cycle_registry[cycle_id]["fail_count"] += 1

    def increment_pass(self, cycle_id: str):
        self.register_cycle(cycle_id)
        self.cycle_registry[cycle_id]["pass_count"] += 1

    def close_cycle(self, cycle_id: str):
        if cycle_id in self.cycle_registry:
            self.cycle_registry[cycle_id]["status"] = "closed"

    def update_revision(self, file: str, rev: int):
        self.revision_table[file] = rev

    def add_finding(self, finding: dict):
        self.findings.append(finding)
