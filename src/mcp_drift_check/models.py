from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class Finding:
    client: str
    config_path: str
    server_name: str
    command: str
    package: str | None
    declared_version: str | None
    classification: str
    reason: str
    recommendation: str

    def to_dict(self):
        return asdict(self)
