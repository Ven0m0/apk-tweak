"""Configuration schema for RVP."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json

@dataclass
class Config:
    input_apk: Optional[str] = None
    output_dir: str = "out"
    engines: List[str] = field(default_factory=lambda: ["revanced"])
    
    # Engine specific configs
    dtlx_analyze: bool = False
    dtlx_optimize: bool = False
    
    # Tool paths (can be set via config file)
    revanced_cli_path: str = "revanced-cli.jar"
    revanced_patches_path: str = "patches.jar"
    revanced_integrations_path: str = "integrations.apk"

    @classmethod
    def load_from_file(cls, path: Path) -> 'Config':
        """Load config from a JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
            return cls(**data)
