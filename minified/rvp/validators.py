from __future__ import annotations
from pathlib import Path
class ValidationError(Exception):0
def validate_apk_path(apk):
	A=apk
	if not A.exists():raise ValidationError(f"APK file not found: {A}")
	if not A.is_file():raise ValidationError(f"APK path is not a file: {A}")
	if A.suffix.lower()!='.apk':raise ValidationError(f"File is not an APK: {A}")
	if A.stat().st_size==0:raise ValidationError(f"APK file is empty: {A}")
def validate_output_dir(output_dir):
	A=output_dir
	if A.exists()and not A.is_dir():raise ValidationError(f"Output path exists but is not a directory: {A}")
def validate_engine_names(engines,available):A=[A for A in engines if A not in available];return A