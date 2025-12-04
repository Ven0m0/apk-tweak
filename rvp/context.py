from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List

# Configure default logger
logger = logging.getLogger("rvp")

@dataclass
class Context:
    work_dir: Path
    input_apk: Path
    output_dir: Path
    engines: List[str]
    options: Dict[str, Any] = field(default_factory=dict)

    # State
    current_apk: Path | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize defaults."""
        self.current_apk = self.input_apk
        # Ensure directories exist
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, level: int = logging.INFO) -> None:
        """Log a message using standard logging."""
        logger.log(level, msg)

    def set_current_apk(self, apk: Path) -> None:
        """Set the current APK and validate existence."""
        if not apk.exists():
            logger.error(f"Attempted to set missing APK: {apk}")
            raise FileNotFoundError(f"APK not found: {apk}")
        self.current_apk = apk
        self.log(f"Current APK updated: {apk.name}")
