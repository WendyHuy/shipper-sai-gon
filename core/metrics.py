from dataclasses import dataclass, field


@dataclass
class Metrics:
    states_processed: int = 0
    planning_ms: float = 0
    replans: int = 0
    path_changes: int = 0
    blocked_attempts: int = 0
    npc_contacts: int = 0
    waits: int = 0
    records: list = field(default_factory=list)
