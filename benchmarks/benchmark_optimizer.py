import os
import shutil
import tempfile
import time
from pathlib import Path


def setup_test_data(base_dir: Path, num_files: int = 5000, depth: int = 5) -> None:
  """Creates a deep directory structure with mix of files."""
  base = Path(base_dir)
  res = base / "res"
  res.mkdir()

  dirs = [res]
  # Create some directories
  current = res
  for i in range(depth):
    current = current / f"dir_{i}"
    current.mkdir()
    dirs.append(current)

  # Populate
  count = 0
  for d in dirs:
    # Create normal files
    for i in range(num_files // len(dirs)):
      (d / f"file_{i}.xml").touch()
      count += 1

    # Create target files
    (d / "file.txt~").touch()
    (d / "temp~").touch()
    (d / ".DS_Store").touch()

  print(
    f"Created {count} normal files and {len(dirs) * 3} target files in {len(dirs)} directories."
  )


def baseline(extract_dir: Path):
  res_dir = extract_dir / "res"
  removed_count = 0

  # Pass 1
  for backup_file in res_dir.rglob("*~"):
    if backup_file.is_file():
      try:
        backup_file.unlink()
        removed_count += 1
      except OSError:
        continue

  # Pass 2
  for ds_store in res_dir.rglob(".DS_Store"):
    if ds_store.is_file():
      try:
        ds_store.unlink()
        removed_count += 1
      except OSError:
        continue
  return removed_count


def optimized_scandir(extract_dir: Path):
  res_dir = extract_dir / "res"
  removed_count = 0

  # Use os.walk which uses scandir under the hood in modern Python
  for root, _, files in os.walk(res_dir):
    for name in files:
      if name == ".DS_Store" or name.endswith("~"):
        file_path = os.path.join(root, name)  # noqa: PTH118
        try:
          os.unlink(file_path)  # noqa: PTH108
          removed_count += 1
        except OSError:
          continue
  return removed_count


def optimized_pathlib_rglob(extract_dir: Path):
  res_dir = extract_dir / "res"
  removed_count = 0

  for file_path in res_dir.rglob("*"):
    name = file_path.name
    if (name == ".DS_Store" or name.endswith("~")) and file_path.is_file():
      try:
        file_path.unlink()
        removed_count += 1
      except OSError:
        continue
  return removed_count


def run_benchmark():
  with tempfile.TemporaryDirectory() as tmp_root:
    root = Path(tmp_root)
    master_data = root / "master"
    master_data.mkdir()

    print("Generating test data...")
    setup_test_data(master_data)

    # Test Baseline
    work_dir = root / "run_baseline"
    shutil.copytree(master_data, work_dir)

    start = time.time()
    count_baseline = baseline(work_dir)
    end = time.time()
    time_baseline = end - start
    print(f"Baseline: {time_baseline:.4f}s (removed {count_baseline})")

    # Test Optimized os.walk
    work_dir = root / "run_optimized_walk"
    shutil.copytree(master_data, work_dir)

    start = time.time()
    count_opt = optimized_scandir(work_dir)
    end = time.time()
    time_opt = end - start
    print(f"Optimized (os.walk): {time_opt:.4f}s (removed {count_opt})")

    # Test Optimized pathlib
    work_dir = root / "run_optimized_pathlib"
    shutil.copytree(master_data, work_dir)

    start = time.time()
    count_pathlib = optimized_pathlib_rglob(work_dir)
    end = time.time()
    time_pathlib = end - start
    print(
      f"Optimized (pathlib single pass): {time_pathlib:.4f}s (removed {count_pathlib})"
    )

    if time_baseline > 0:
      speedup = time_baseline / time_opt
      print(f"Speedup (os.walk): {speedup:.2f}x")


if __name__ == "__main__":
  run_benchmark()
