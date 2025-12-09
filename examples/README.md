# RVP Examples

This directory contains example configurations and plugins to help you get
started with the ReVanced Pipeline.

## Configuration Files

### basic-config.json

Simple configuration for ReVanced patching only.

```bash
rvp -c examples/basic-config.json
```

### magisk-config.json

Configuration for packaging an APK as a Magisk module.

```bash
rvp -c examples/magisk-config.json
```

### full-pipeline-config.json

Complete pipeline example using multiple engines (ReVanced → DTL-X → Magisk).

```bash
rvp -c examples/full-pipeline-config.json
```

## Custom Plugin

### custom_plugin.py

Example plugin demonstrating the hook system.

**To use:**

1. Copy to `rvp/plugins/` directory:

```bash
cp examples/custom_plugin.py rvp/plugins/
```
2. Run any pipeline - the plugin will be automatically discovered and loaded.

**Features demonstrated:**

- Hooking into all pipeline stages
- Accessing and modifying context
- Logging information
- Storing custom metadata

## Creating Your Own Engine

To create a custom engine:

1. Create a new file in `rvp/engines/` (e.g., `custom_engine.py`)
2. Implement a `run(ctx: Context) -> None` function
3. Use `ctx.current_apk` as input
4. Update `ctx.current_apk` with your output
5. The engine will be auto-discovered

Example:

```python
from pathlib import Path
from ..context import Context

def run(ctx: Context) -> None:
  """Custom engine implementation."""
  ctx.log("custom: starting")

  input_apk = ctx.current_apk
  if not input_apk:
    raise ValueError("No input APK")

  # Your processing logic here
  output_apk = ctx.output_dir / f"{input_apk.stem}.custom.apk"

  # ... process APK ...

  ctx.set_current_apk(output_apk)
  ctx.log(f"custom: complete - {output_apk}")
```

## Tips

- **Validation**: Always validate inputs and handle errors gracefully
- **Logging**: Use `ctx.log()` for all output
- **Metadata**: Store results in `ctx.metadata` for other engines/plugins
- **Paths**: Use `ctx.work_dir` for temporary files, `ctx.output_dir` for final
  output
- **Type Safety**: Add type hints for better IDE support and type checking
