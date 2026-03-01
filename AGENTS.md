# AI Agent Development Guide

Critical instructions for AI agents (Claude, Copilot, Gemini) working with this codebase.

## Project Identity

**APK Tweak (ReVanced Pipeline)** - Extensible Python pipeline for APK modifications supporting ReVanced, LSPatch, DTL-X, media optimization, and custom engines.

**Tech Stack**: Python 3.11+ | uv package manager | pytest | mypy (strict) | ruff

## Quick Reference

### Priority Files (@ prefix for reference)

| File               | Purpose                                |
| ------------------ | -------------------------------------- |
| @rvp/core.py       | Pipeline orchestration, auto-discovery |
| @rvp/context.py    | Runtime state container                |
| @rvp/types.py      | TypedDict definitions                  |
| @rvp/cli.py        | CLI argument parsing                   |
| @rvp/utils.py      | Subprocess execution, file ops         |
| @rvp/engines/\*.py | Engine implementations                 |
| @pyproject.toml    | Dependencies, tool config              |

### Critical Commands

```bash
# Package management (ONLY use uv, NEVER pip)
uv add <package>            # Add runtime dependency
uv add --dev <package>      # Add dev dependency
uv run <command>            # Run tool (pytest, mypy, etc.)

# Quality checks (run after EVERY code change)
uv run ruff format .        # Format code
uv run ruff check . --fix   # Auto-fix linting issues
uv run mypy rvp/            # Type check (strict mode)
uv run pytest               # Run tests

# Full quality pass
./lint-all.sh               # Run all formatters/linters
```

## Architecture

### Pipeline Flow

```
Input APK → Engine 1 → Engine 2 → ... → Output APK
             ↓          ↓              ↓
          Plugins    Plugins        Plugins
```

### Core Concepts

**Context (@rvp/context.py)**: Runtime state object passed to all engines

- `ctx.current_apk`: Path to current APK (updated by each engine)
- `ctx.options`: PipelineOptions TypedDict
- `ctx.log(msg)`: Logging method
- `ctx.metadata`: Dict for storing engine results

**Engine Pattern** (see @rvp/engines/revanced.py for example):

```python
def run(ctx: Context) -> None:
    """Engine entry point. MUST update ctx.current_apk on success."""
    input_apk = require_input_apk(ctx)
    # ... process APK ...
    ctx.set_current_apk(output_apk)
    ctx.metadata["engine_name"] = {"result": "data"}
```

**Auto-Discovery** (@rvp/core.py): Engines/plugins discovered via `pkgutil.iter_modules()`

### Project Structure

```
apk-tweak/
├── rvp/                        # Main package
│   ├── @cli.py                 # CLI (argparse)
│   ├── @config.py              # Config schema (dataclass)
│   ├── @constants.py           # Shared constants
│   ├── @context.py             # Pipeline context
│   ├── @core.py                # Orchestration & discovery
│   ├── @types.py               # TypedDict definitions
│   ├── @utils.py               # Subprocess & file utilities
│   ├── @validators.py          # Input validation
│   ├── @optimizer.py           # APK optimization
│   ├── @ad_patterns.py         # Ad-blocking patterns
│   ├── engines/                # Auto-discovered engines
│   │   ├── revanced.py         # ReVanced patching
│   │   ├── lspatch.py          # LSPatch
│   │   ├── dtlx.py             # DTL-X analysis
│   │   ├── rkpairip.py         # RKPairip
│   │   ├── whatsapp.py         # WhatsApp patcher
│   │   ├── media_optimizer.py  # Image/audio optimization
│   │   ├── string_cleaner.py   # String removal
│   │   └── optimizer.py        # General optimizer
│   └── plugins/                # Auto-discovered plugins
├── tests/                      # Test suite (currently empty)
├── config/                     # Example JSON configs
├── @pyproject.toml             # Project metadata & tools
├── @lint-all.sh                # Full lint script
└── uv.lock                     # Dependency lock
```

## Code Quality Requirements

### Type Safety (mypy strict mode)

- **MANDATORY**: Type hints for all functions, variables, return values
- **MANDATORY**: Explicit None checks for Optional types
- Use TypedDict for configuration options (@rvp/types.py)
- Use `cast()` when needed for TypedDict access
- Run `uv run mypy rvp/` after EVERY change

### Style & Formatting (ruff)

- **Line length**: 88 characters max
- **Indentation**: 2 spaces (NOT tabs)
- **Strings**: Double quotes, f-strings for formatting
- **Imports**: Force single-line, sorted by isort
- **Docstrings**: Required for public APIs (PEP 257)

### Naming Conventions (PEP 8)

- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Handlers: `handle_*` prefix
- Engine entry points: `run(ctx: Context) -> None`

### Testing (pytest)

- Framework: pytest
- Test files: `tests/test_*.py`
- Use `tmp_path` fixture for file operations
- Test edge cases and error paths
- **REQUIRED**: New features need tests, bug fixes need regression tests

## Development Workflow

### Change Process

1. **ALWAYS** read existing code before modifying
2. Make minimal, focused changes (avoid over-engineering)
3. Run quality checks: `uv run ruff format . && uv run ruff check . --fix && uv run mypy rvp/`
4. Run tests: `uv run pytest`
5. Commit atomically with conventional commit style

### Git Conventions

**Branch naming**: `feat/`, `fix/`, `chore/`, `docs/`

**Commit style**: `type(scope): description`

- Examples: `feat(revanced): add multi-patch support`, `fix(cli): handle missing key`

**Pre-commit checklist**:

- [ ] Code formatted (`uv run ruff format .`)
- [ ] Linting passed (`uv run ruff check . --fix`)
- [ ] Type check passed (`uv run mypy rvp/`)
- [ ] Tests passed (`uv run pytest`)
- [ ] Changes are minimal and focused

## Engine Development

### Requirements

- Accept `Context` as sole parameter
- Update `ctx.current_apk` after modifying APK
- Use `ctx.log()` for output
- Raise exceptions on failure
- Use `validate_and_require_dependencies()` for tool checks
- Store results in `ctx.metadata["engine_name"]`

### Template

```python
from pathlib import Path
from rvp.context import Context
from rvp.utils import require_input_apk

def run(ctx: Context) -> None:
    """Engine description."""
    input_apk = require_input_apk(ctx)

    # Validate dependencies
    # Process APK
    # Generate output

    output_apk = ctx.work_dir / "output.apk"
    ctx.set_current_apk(output_apk)
    ctx.metadata["engine_name"] = {"status": "success"}
```

## Plugin Development

### Requirements

- Implement `handle_hook(ctx: Context, stage: str) -> None`
- Use lightweight operations (hooks are called frequently)
- Catch exceptions internally (don't crash pipeline)

### Hook Stages

- `pre_pipeline` / `post_pipeline`
- `pre_engine:{name}` / `post_engine:{name}`

## Best Practices for AI Agents

### DO

- ✅ Read files before editing
- ✅ Make minimal, focused changes
- ✅ Follow existing patterns exactly
- ✅ Run quality checks after every change
- ✅ Use early returns to avoid nesting
- ✅ Keep functions small and focused
- ✅ Add docstrings to public APIs
- ✅ Use constants over functions where possible
- ✅ Prefer editing existing files over creating new ones

### DON'T

- ❌ Use `uv pip install` or `@latest` syntax
- ❌ Mix formatting and logic changes in same commit
- ❌ Add features/refactoring beyond what was asked
- ❌ Add error handling for impossible scenarios
- ❌ Create abstractions for one-time operations
- ❌ Add backwards-compatibility hacks (delete unused code)
- ❌ Propose changes to code you haven't read
- ❌ Over-engineer solutions

## Common Patterns

### Error Handling

```python
# Use early returns
if not condition:
    raise ValueError("Specific error message")

# Use guard clauses
if input_apk is None:
    raise ValueError("No input APK")
```

### File Operations

```python
from pathlib import Path

# Use Path objects, not strings
input_path = Path("input.apk")
output_path = work_dir / "output.apk"

# Check existence before operations
if not input_path.exists():
    raise FileNotFoundError(f"APK not found: {input_path}")
```

### Subprocess Execution

```python
from rvp.utils import run_command

# Use run_command from utils
result = run_command(
    ["tool", "--option", str(input_path)],
    ctx=ctx,
    description="Tool description"
)
```

## CI/CD Pipeline

**GitHub Actions** (@.github/workflows/lint-enforce.yml):

1. **lint-and-format**: Runs `./lint-all.sh`, auto-commits fixes
2. **python-type-check**: Runs `mypy rvp/`
3. **python-tests**: Runs `pytest tests/ -v`

**All jobs must pass** before merging.

## Error Resolution Order

1. Run `uv run ruff format .` (formatting)
2. Run `uv run ruff check . --fix` (linting)
3. Run `uv run mypy rvp/` (type errors)
4. Run `uv run pytest` (tests)

### Common Type Errors

- Missing type hints → Add explicit types
- Optional type issues → Add `if x is not None:` guards
- TypedDict access → Use `cast()` or `get()` with defaults
- String literal types → Narrow with type guards

## Dependencies

**Runtime**: `orjson>=3.11.0` (fast JSON)

**Dev**: `pytest`, `mypy`, `ruff`, `pip-audit`

**External tools** (for engines): `revanced-cli`, `java`, `pngquant`, `jpegoptim`, `ffmpeg`

## Usage Examples

```bash
# Basic ReVanced patching
uv run rvp input.apk

# Multiple engines
uv run rvp input.apk -e revanced -e media_optimizer

# Config file
uv run rvp -c config/full_pipeline.json

# Media optimization
uv run rvp input.apk -e media_optimizer --optimize-images --target-dpi xxhdpi

# Verbose output
uv run rvp input.apk -v
```

## Philosophy

**In order of priority**:

1. **Simplicity** - Write straightforward code
2. **Readability** - Make code easy to understand
3. **Less Code = Less Debt** - Minimize footprint
4. **Maintainability** - Easy to update
5. **Testability** - Easy to test
6. **Performance** - Consider without sacrificing readability

---

**Remember**: Quality over speed. Run all checks. Keep it simple.
