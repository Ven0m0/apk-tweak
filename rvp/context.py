from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List


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
    # Performance: Control log storage to avoid memory overhead
    store_logs: bool = False

    def log(self, msg: str) -> None:
        """
        Log a message with [rvp] prefix.

        Performance optimization: Only stores logs in memory if store_logs=True,
        avoiding redundant string operations and memory usage.
        """
        line = f"[rvp] {msg}"
        print(line)
        # Only store logs if explicitly requested (performance optimization)
        if self.store_logs:
            self.logs.append(line)

    def set_current_apk(self, apk: Path) -> None:
        """Set the current APK being processed."""
        self.current_apk = apk
        self.log(f"Current APK set to: {apk}")
