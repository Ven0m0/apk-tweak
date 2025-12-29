from __future__ import annotations
import logging
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from.types import PipelineOptions
logger=logging.getLogger('rvp')
@dataclass
class Context:
	work_dir:Path;input_apk:Path;output_dir:Path;engines:list[str];options:PipelineOptions=field(default_factory=dict);current_apk:Path|None=None;metadata:dict[str,Any]=field(default_factory=dict)
	def __post_init__(A):B=True;A.current_apk=A.input_apk;A.work_dir.mkdir(parents=B,exist_ok=B);A.output_dir.mkdir(parents=B,exist_ok=B)
	def log(A,msg,level=logging.INFO):logger.log(level,msg)
	def set_current_apk(B,apk):
		A=apk
		if not A.exists():logger.error(f"Attempted to set missing APK: {A}");raise FileNotFoundError(f"APK not found: {A}")
		B.current_apk=A;B.log(f"Current APK updated: {A.name}")