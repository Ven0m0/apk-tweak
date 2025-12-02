from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional


@dataclass
class Context:
    work_dir: Path
    input_apk: Path
    output_dir: Path
    engines: List[str]
    options: Dict[str, Any] = field(default_factory=dict)

    # populated as we go
    current_apk: Path | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    def log(self, msg: str) -> None:
        line = f"[rvp] {msg}"
        print(line)
        self.logs.append(line)

    def set_current_apk(self, apk: Path) -> None:
        self.current_apk = apk
        self.log(f"Current APK set to: {apk}")
