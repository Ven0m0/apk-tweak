"""Pipeline execution context and state management."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configure default logger
logger = logging.getLogger("rvp")


@dataclass
class Context:
  """
  Runtime context for pipeline execution.

  Attributes:
      work_dir: Temporary working directory for intermediate files.
      input_apk: Original input APK path.
      output_dir: Directory for final output files.
      engines: List of engine names to execute.
      options: Configuration options for engines and tools.
      current_apk: Path to the current APK in the pipeline (updated by engines).
      metadata: Arbitrary metadata dict for storing engine results.
  """

  work_dir: Path
  input_apk: Path
  output_dir: Path
  engines: list[str]
  options: dict[str, Any] = field(default_factory=dict)

  # State
  current_apk: Path | None = None
  metadata: dict[str, Any] = field(default_factory=dict)

  def __post_init__(self) -> None:
    """Initialize defaults and ensure directories exist."""
    self.current_apk = self.input_apk
    # Ensure directories exist
    self.work_dir.mkdir(parents=True, exist_ok=True)
    self.output_dir.mkdir(parents=True, exist_ok=True)

  def log(self, msg: str, level: int = logging.INFO) -> None:
    """
    Log a message using standard logging.

    Args:
        msg: Message to log.
        level: Logging level (default: INFO).
    """
    logger.log(level, msg)

  def set_current_apk(self, apk: Path) -> None:
    """
    Update the current APK and validate its existence.

    Args:
        apk: Path to the new current APK.

    Raises:
        FileNotFoundError: If the APK file doesn't exist.
    """
    if not apk.exists():
      logger.error(f"Attempted to set missing APK: {apk}")
      raise FileNotFoundError(f"APK not found: {apk}")
    self.current_apk = apk
    self.log(f"Current APK updated: {apk.name}")
