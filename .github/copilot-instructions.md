# GitHub Copilot Instructions - APK Tweak

## Project Context

**APK Tweak (ReVanced Pipeline)** is an extensible Python pipeline for APK modifications supporting ReVanced, LSPatch, DTL-X, and media optimization engines.

**Stack**: Python 3.11+ | uv (package manager) | pytest | mypy (strict mode) | ruff

## Critical Rules

### Package Management

**ONLY use `uv`, NEVER `pip`**:

```bash
uv add <package>          # Add runtime dependency
uv add --dev <package>    # Add dev dependency
uv run <command>          # Run tools (pytest, mypy, ruff, etc.)
```

**FORBIDDEN**: `uv pip install`, `pip install`, `@latest` syntax

### Code Quality - MANDATORY

After EVERY code change, run:

```bash
uv run ruff format .        # Format code
uv run ruff check . --fix   # Fix linting issues
uv run mypy rvp/            # Type check (strict mode)
uv run pytest               # Run tests
```

## Architecture Quick Reference

### Key Files (@ prefix)

- `@rvp/core.py` - Pipeline orchestration, auto-discovery
- `@rvp/context.py` - Runtime state container
- `@rvp/types.py` - TypedDict definitions
- `@rvp/cli.py` - CLI argument parsing
- `@rvp/utils.py` - Subprocess execution, file utilities
- `@rvp/engines/*.py` - Engine implementations

### Pipeline Flow

```
Input APK → Engine 1 → Engine 2 → ... → Output APK
             ↓          ↓              ↓
          Plugins    Plugins        Plugins
```

### Context Object

Every engine receives a `Context` object:

```python
from rvp.context import Context

def run(ctx: Context) -> None:
    """Engine entry point."""
    # ctx.current_apk - Path to current APK
    # ctx.options - PipelineOptions TypedDict
    # ctx.log(msg) - Logging method
    # ctx.metadata - Dict for storing results
    # ctx.set_current_apk(path) - Update current APK
```

## Code Style

### Type Safety (mypy strict)

- **MANDATORY**: Type hints for all functions, variables, return values
- Use `Optional[T]` for nullable types
- Add explicit None checks: `if x is not None:`
- Use TypedDict for configuration options
- Run `uv run mypy rvp/` after every change

### Formatting (ruff)

- **Line length**: 88 characters max
- **Indentation**: 2 spaces (NOT tabs)
- **Strings**: Double quotes, f-strings for formatting
- **Imports**: Force single-line, sorted by isort

### Naming (PEP 8)

- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Handlers: `handle_*` prefix
- Engine entry points: `run(ctx: Context) -> None`

### Documentation

- Public APIs require docstrings (PEP 257 style)
- Keep docstrings concise and informative
- Example:

```python
def run(ctx: Context) -> None:
    """
    Execute ReVanced patching on the input APK.

    Args:
        ctx: Pipeline context containing input APK and options.

    Raises:
        ValueError: If required options are missing.
        FileNotFoundError: If input APK doesn't exist.
    """
```

## Development Patterns

### Engine Development Template

```python
from pathlib import Path
from rvp.context import Context
from rvp.utils import require_input_apk, run_command

def run(ctx: Context) -> None:
    """Engine description."""
    # 1. Get input APK
    input_apk = require_input_apk(ctx)

    # 2. Validate dependencies/options
    if not ctx.options.get("some_option"):
        raise ValueError("Missing required option: some_option")

    # 3. Process APK
    output_apk = ctx.work_dir / "output.apk"

    # 4. Update context
    ctx.set_current_apk(output_apk)
    ctx.metadata["engine_name"] = {"status": "success"}
```

### Error Handling

Use early returns and guard clauses:

```python
# Good
def process(input_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    if not input_path.suffix == ".apk":
        raise ValueError("Input must be an APK file")

    # Main logic here

# Bad - nested conditions
def process(input_path: Path) -> None:
    if input_path.exists():
        if input_path.suffix == ".apk":
            # Main logic here
```

### File Operations

Always use `pathlib.Path`:

```python
from pathlib import Path

# Good
input_path = Path("input.apk")
output_path = work_dir / "output.apk"

if not input_path.exists():
    raise FileNotFoundError(f"APK not found: {input_path}")

# Bad
import os
input_path = "input.apk"
output_path = os.path.join(work_dir, "output.apk")
```

### Subprocess Execution

Use `run_command` from `rvp.utils`:

```python
from rvp.utils import run_command

result = run_command(
    ["tool", "--option", str(input_path)],
    ctx=ctx,
    description="Tool description for logging"
)
```

## Testing (pytest)

- Test files: `tests/test_*.py`
- Use `tmp_path` fixture for file operations
- Test both success and error paths
- **REQUIRED**: New features need tests, bug fixes need regression tests

Example:

```python
def test_engine_success(tmp_path):
    """Test engine processes APK successfully."""
    input_apk = tmp_path / "input.apk"
    input_apk.touch()

    ctx = Context(
        work_dir=tmp_path,
        input_apk=input_apk,
        output_dir=tmp_path / "output",
        engines=["test_engine"],
        options={}
    )

    run(ctx)

    assert ctx.current_apk is not None
    assert ctx.current_apk.exists()
```

## Git Workflow

### Commit Style

Use conventional commit format: `type(scope): description`

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`

Examples:

- `feat(revanced): add multi-patch support`
- `fix(cli): handle missing config file`
- `chore(deps): update ruff to 0.15.0`
- `docs(readme): update installation instructions`

### Pre-Commit Checklist

Before committing:

- [ ] Code formatted: `uv run ruff format .`
- [ ] Linting passed: `uv run ruff check . --fix`
- [ ] Type check passed: `uv run mypy rvp/`
- [ ] Tests passed: `uv run pytest`
- [ ] Changes are minimal and focused
- [ ] Public APIs have docstrings

## Best Practices

### DO

- ✅ Read existing code before modifying
- ✅ Make minimal, focused changes
- ✅ Follow existing patterns exactly
- ✅ Use early returns to avoid nesting
- ✅ Keep functions small and focused
- ✅ Use constants instead of magic values
- ✅ Prefer editing existing files over creating new ones

### DON'T

- ❌ Use `pip` or `uv pip install`
- ❌ Mix formatting and logic changes in the same commit
- ❌ Add features beyond what was requested
- ❌ Add error handling for impossible scenarios
- ❌ Create abstractions for one-time operations
- ❌ Add backwards-compatibility hacks
- ❌ Over-engineer solutions

## Common Type Issues

### Optional Types

```python
# Bad - mypy error
def process(path: Path | None) -> str:
    return str(path.name)

# Good - explicit None check
def process(path: Path | None) -> str:
    if path is None:
        raise ValueError("Path is required")
    return str(path.name)
```

### TypedDict Access

```python
from typing import cast
from rvp.types import PipelineOptions

# Good - safe access
def get_option(options: PipelineOptions) -> bool:
    return options.get("dtlx_analyze", False)

# Or use cast when needed
def get_option(options: dict) -> bool:
    typed_options = cast(PipelineOptions, options)
    return typed_options.get("dtlx_analyze", False)
```

## Philosophy

**Priority order**:

1. **Simplicity** - Write straightforward code
2. **Readability** - Make code easy to understand
3. **Less Code = Less Debt** - Minimize code footprint
4. **Maintainability** - Write code that's easy to update
5. **Testability** - Ensure code is testable
6. **Performance** - Consider performance without sacrificing readability

## CI/CD

GitHub Actions runs:

1. `./lint-all.sh` - All formatters/linters, auto-commits fixes
2. `mypy rvp/` - Type checking
3. `pytest tests/ -v` - Test suite

**All jobs must pass** before merging.

## Quick Commands

```bash
# Run pipeline
uv run rvp input.apk -e revanced

# Quality checks
uv run ruff format . && uv run ruff check . --fix && uv run mypy rvp/

# Full lint
./lint-all.sh

# Tests
uv run pytest -v
```

---

**Remember**: Quality over speed. Always run checks. Keep it simple.
