# Development Guidelines

Critical information for working with this codebase. Follow these guidelines precisely.

## Project Overview

**APK Tweak (ReVanced Pipeline)** - An extensible Python pipeline for APK modifications supporting ReVanced, LSPatch, DTL-X, and media optimization engines.

## Package Management

**ONLY use uv, NEVER pip**

```bash
uv add package              # Install package
uv add --dev package        # Install dev package
uv run tool                 # Run tool (e.g., uv run pytest)
uv add package --upgrade-package package  # Upgrade package
```

**FORBIDDEN**: `uv pip install`, `@latest` syntax

## Code Quality

### Type Checking
- Type hints required for all code
- Run `uv run mypy rvp/` after every change and fix resulting errors
- Use mypy strict mode (configured in pyproject.toml)
- Explicit None checks for Optional types
- Type narrowing for strings
- Use TypedDict for configuration options (see `rvp/types.py`)

### Code Standards
- Line length: 88 chars maximum
- Indent width: 2 spaces
- Public APIs must have docstrings
- Functions must be focused and small
- Follow existing patterns exactly

### Naming Conventions (PEP 8)
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Handlers: prefix with `handle_`
- Engine entry points: `run(ctx: Context) -> None`

### Formatting
- Use f-strings for string formatting
- Use Ruff for code formatting
- Double quotes for strings
- Space-based indentation

## Testing

```bash
uv run pytest               # Run all tests
uv run pytest tests/ -v     # Verbose output
uv run pytest -k "test_name" # Run specific test
```

- Framework: pytest
- Test files: `tests/test_*.py`
- Coverage: test edge cases and errors
- New features require tests
- Bug fixes require regression tests
- Use `tmp_path` fixture for file operations

## Development Philosophy

Core principles in order of priority:

1. **Simplicity**: Write straightforward code, avoid clever solutions
2. **Readability**: Make code easy to understand
3. **Less Code = Less Debt**: Minimize code footprint
4. **Maintainability**: Write code that's easy to update
5. **Testability**: Ensure code is testable
6. **Performance**: Consider performance without sacrificing readability

## Codebase Architecture

### Project Structure

```text
apk-tweak/
├── rvp/                        # Main package
│   ├── __init__.py             # Package exports
│   ├── cli.py                  # Command-line interface (argparse)
│   ├── config.py               # Configuration schema (dataclass)
│   ├── constants.py            # Shared constants
│   ├── context.py              # Pipeline execution context
│   ├── core.py                 # Pipeline orchestration & module discovery
│   ├── types.py                # TypedDict definitions (PipelineOptions)
│   ├── utils.py                # Subprocess execution & file utilities
│   ├── validators.py           # Input validation
│   ├── optimizer.py            # APK optimization utilities
│   ├── ad_patterns.py          # Ad-blocking patterns
│   ├── engines/                # Engine modules (auto-discovered)
│   │   ├── __init__.py
│   │   ├── revanced.py         # ReVanced patching engine
│   │   ├── lspatch.py          # LSPatch engine
│   │   ├── dtlx.py             # DTL-X analysis/optimization
│   │   ├── rkpairip.py         # RKPairip engine
│   │   ├── whatsapp.py         # WhatsApp patcher
│   │   ├── media_optimizer.py  # Image/audio optimization
│   │   ├── string_cleaner.py   # Unused string removal
│   │   └── optimizer.py        # General APK optimizer
│   └── plugins/                # Plugin modules (auto-discovered)
│       └── __init__.py
├── tests/                      # Test suite
│   └── test_*.py
├── config/                     # Example pipeline configs (JSON)
├── pyproject.toml              # Project metadata & tool config
├── lint-all.sh                 # Comprehensive lint script
└── uv.lock                     # Dependency lock file
```

### Core Concepts

**Pipeline Flow**:
```text
Input APK → Engine 1 → Engine 2 → ... → Output APK
             ↓          ↓              ↓
          Plugins    Plugins        Plugins
```

**Context (`rvp/context.py`)**: Runtime state passed to all engines
- `ctx.current_apk`: Path to current APK in pipeline
- `ctx.options`: PipelineOptions TypedDict
- `ctx.log()`: Logging method
- `ctx.metadata`: Dict for storing engine results

**Engine Pattern** (`rvp/engines/*.py`):
```python
def run(ctx: Context) -> None:
    """Engine entry point. Must update ctx.current_apk on success."""
    input_apk = require_input_apk(ctx)
    # ... process APK ...
    ctx.set_current_apk(output_apk)
    ctx.metadata["engine_name"] = {"result": "data"}
```

**Auto-Discovery**: Engines/plugins are discovered via `pkgutil.iter_modules()` in `core.py`

### Key Files to Understand

| File | Purpose |
|------|---------|
| `rvp/core.py` | Pipeline orchestration, module discovery |
| `rvp/context.py` | Runtime state container |
| `rvp/types.py` | TypedDict definitions for options |
| `rvp/utils.py` | Subprocess execution with logging |
| `rvp/cli.py` | CLI argument parsing |

## Best Practices

### Code Organization
- Early returns to avoid nested conditions
- Keep core logic clean, push implementation details to edges
- Use `require_input_apk(ctx)` to get current APK
- Use `ctx.set_current_apk(path)` after modifying APK
- Store engine results in `ctx.metadata`

### Engine Development
- Accept `Context` as sole parameter
- Update `ctx.current_apk` after modification
- Use `ctx.log()` for output
- Raise exceptions on failure
- Use `validate_and_require_dependencies()` for tool checks

### Coding Style
- DRY (Don't Repeat Yourself)
- Use constants over functions where possible
- Prefer functional, immutable approaches when clear
- Only modify code related to the task
- Mark issues with `TODO:` prefix

### Iterative Development
1. Start with minimal functionality
2. Verify it works before adding complexity
3. Test frequently with realistic inputs
4. Create test environments for hard-to-validate components

## Git Workflow

### Branch Strategy
- Always use feature branches, never commit directly to `main`
- Branch naming: `fix/auth-timeout`, `feat/api-pagination`, `chore/ruff-fixes`
- One logical change per branch

### Commit Practices
- Atomic commits (one logical change per commit)
- Conventional commit style: `type(scope): short description`
- Examples: `feat(revanced): add multi-patch support`, `fix(cli): handle missing key`
- Keep granular history on feature branch, squash when merging to `main`

### Pull Requests
- Open draft PR early for visibility
- Convert to ready when complete and tests pass
- Create detailed PR description focusing on:
  - High-level problem description
  - How it's solved
  - Avoid code specifics unless they add clarity

### Issue Linking
- Reference existing issue or create one before starting
- Use `Fixes #123` in commit/PR messages for auto-linking

### Workflow Steps
1. Create or reference an issue
2. `git checkout -b feat/issue-123-description`
3. Commit in small, logical increments
4. `git push` and open draft PR early
5. Convert to ready when functionally complete and tests pass
6. Merge after reviews and checks pass

## Code Formatting & Linting

### Quick Commands
```bash
uv run ruff format .        # Format code
uv run ruff check .         # Check for issues
uv run ruff check . --fix   # Auto-fix issues
uv run mypy rvp/            # Type check (strict mode)
```

### Full Lint Script
```bash
./lint-all.sh               # Run all linters/formatters
```

This runs: ruff, yamlfmt, yamllint, prettier, markdownlint, shfmt, shellcheck, taplo, actionlint

### Critical Ruff Rules (from pyproject.toml)
- `E`, `W`: pycodestyle
- `F`: pyflakes
- `I`: isort (import sorting)
- `N`: pep8-naming
- `UP`: pyupgrade
- `B`: flake8-bugbear
- `PT`: flake8-pytest-style

### Line Wrapping
- Strings: use parentheses for multi-line
- Function calls: multi-line with proper indent
- Imports: split into multiple lines (force-single-line enabled)

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/lint-enforce.yml`) runs:

1. **lint-and-format**: Runs `./lint-all.sh`, auto-commits fixes
2. **python-type-check**: Runs `mypy rvp/`
3. **python-tests**: Runs `pytest tests/ -v`

All jobs must pass before merging.

## Error Resolution

### CI Failure Fix Order
1. Formatting (`uv run ruff format .`)
2. Linting (`uv run ruff check . --fix`)
3. Type errors (`uv run mypy rvp/`)
4. Tests (`uv run pytest`)

### Common Issues

**Line Length**:
- Break strings with parentheses
- Multi-line function calls
- Split imports

**Type Errors**:
- Get full line context
- Check Optional types
- Add type narrowing
- Verify function signatures
- Add explicit None checks
- Narrow string types
- Match existing patterns
- Use `cast()` for TypedDict access when needed

**Import Errors (I001)**:
- Run `ruff check . --fix` to auto-sort
- First-party imports: `rvp`

### Pre-Commit Checklist
- [ ] Check git status
- [ ] Run formatters (`uv run ruff format .`)
- [ ] Run linting (`uv run ruff check . --fix`)
- [ ] Run type check (`uv run mypy rvp/`)
- [ ] Run tests (`uv run pytest`)
- [ ] Keep changes minimal
- [ ] Follow existing patterns
- [ ] Document public APIs

## Running the Tool

```bash
# Basic usage
uv run rvp input.apk

# Multiple engines
uv run rvp input.apk -e revanced -e media_optimizer

# With config file
uv run rvp -c config/full_pipeline.json

# Media optimization
uv run rvp input.apk -e media_optimizer --optimize-images --target-dpi xxhdpi

# Verbose output
uv run rvp input.apk -v
```

## Dependencies

Runtime: `orjson>=3.11.0` (fast JSON serialization)

Dev: `pytest`, `mypy`, `ruff`, `pip-audit`

External tools (for engines): `revanced-cli`, `java`, `pngquant`, `jpegoptim`, `ffmpeg`
