#!/usr/bin/env python3
"""Script to minify all Python files in the rvp directory."""

import subprocess
from pathlib import Path

source_dir = Path("rvp")
output_dir = Path("minified/rvp")

# Create output directory
output_dir.mkdir(parents=True, exist_ok=True)

# Find all Python files
python_files = list(source_dir.rglob("*.py"))

print(f"Found {len(python_files)} Python files to minify")

for py_file in python_files:
  # Calculate relative path and output path
  rel_path = py_file.relative_to(source_dir)
  out_file = output_dir / rel_path

  # Create parent directories
  out_file.parent.mkdir(parents=True, exist_ok=True)

  # Minify the file
  print(f"Minifying {py_file} -> {out_file}")
  subprocess.run(
    [
      "pyminify",
      str(py_file),
      "--output",
      str(out_file),
      "--remove-literal-statements",
    ],
    check=True,
  )

print("Minification complete!")
