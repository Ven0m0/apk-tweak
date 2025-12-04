# Claude Instructions: APK Tweak / ReVanced Pipeline

## Project Overview

**apk-tweak** is an extensible pipeline system for Android APK modification and
packaging. It provides a modular framework for integrating multiple APK patching
and packaging engines:

- **ReVanced**: YouTube/app patching via ReVanced CLI
- **LSPatch**: LSPosed module integration
- **Magisk**: Magisk module packaging
- **DTL-X**: APK analysis and optimization

### Architecture

```
apk-tweak/
├── rvp/                    # Python package (ReVanced Pipeline)
│   ├── cli.py              # CLI argument parsing & entry point
│   ├── core.py             # Pipeline orchestration & plugin system
│   ├── context.py          # Shared context/state dataclass
│   ├── engines/            # Processing engines (extensible)
│   │   ├── revanced.py     # ReVanced CLI integration
│   │   ├── lspatch.py      # LSPatch integration
│   │   ├── magisk.py       # Magisk module builder
│   │   └── dtlx.py         # DTL-X analyzer/optimizer
│   └── plugins/            # Hook-based plugin system
│       ├── __init__.py
│       └── example_plugin.py
├── bin/rvp                 # Bash wrapper for Python CLI
├── .github/
│   ├── agents.yml          # Specialized AI agents
│   ├── chat-modes.yml      # Chat mode configurations
│   ├── workflows/          # CI/CD pipelines
│   └── instructions/       # Language-specific coding standards
├── pyproject.toml          # Python package config
├── gradle.properties       # Gradle/Android build config
└── CLAUDE.MD               # This file
```

### Core Design Patterns

1. **Pipeline Architecture**: Chain multiple engines sequentially
2. **Context Object**: Shared state (`Context` dataclass) passed through
   pipeline
3. **Plugin Hooks**: Event-driven hooks (`pre_pipeline`, `pre_engine:*`,
   `post_engine:*`, `post_pipeline`)
4. **Engine Registry**: Modular engine registration in `core.py:_ENGINES`
5. **Stub Implementations**: Current engines are stubs ready for real
   integrations

---

## Core Directives

Autonomous execution. Minimal confirmations. Token-efficient responses. Dual
focus: **Bash scripts** for tooling & **Python** for core pipeline.

## Operating Principles

- **Direct Execution**: Edit files immediately without requesting permission
- **Confirm Only Critical Changes**: Wide-scope architectural changes only
- **Quality-Driven**: Thorough validation, best practices, fact verification
- **Edit Over Create**: Modify existing files preferentially
- **Multi-Approach Analysis**: Compare pros/cons when multiple solutions exist
- **Efficient Planning**: Outline complex approaches before implementation

### Communication Style

Language: Technical English | Tone: Professional, concise | Complexity: Advanced
| Emojis: Minimal usage | Naming: Brief, clear

### Abbreviations Reference

y=Yes n=No c=Continue r=Review u=Undo | cfg=config impl=implementation
arch=architecture deps=dependencies val=validation sec=security err=error
opt=optimization Δ=change mgr=manager fn=function mod=modify rm=remove w/=with
dup=duplicate

---

## Python Development Standards

### Code Style (PEP 8)

- **Indentation**: 4 spaces (enforced via `.editorconfig`)
- **Line Length**: 88 characters (Black-compatible), 120 max for complex lines
- **Type Hints**: Mandatory for all function signatures
- **Imports**: `from __future__ import annotations` at top
- **Docstrings**: PEP 257 format for public functions/classes

### Modern Python Patterns

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Callable

# Use dataclasses for state
@dataclass
class Context:
    work_dir: Path
    options: Dict[str, Any] = field(default_factory=dict)

    def log(self, msg: str) -> None:
        """Log with [rvp] prefix."""
        print(f"[rvp] {msg}")

# Type aliases for clarity
EngineFn = Callable[[Context], None]

# Prefer Path over strings
def process_apk(apk_path: Path) -> Path:
    return apk_path.resolve()
```

### File Operations

- Use `Path` from `pathlib` (not `os.path`)
- Use `shutil.copy2` for file copying (preserves metadata)
- Create dirs with `path.mkdir(parents=True, exist_ok=True)`

### Error Handling

```python
# Validate inputs early
if not apk.is_file():
    print(f"Error: APK not found: {apk}", file=sys.stderr)
    return 1

# Use context managers for resources
with open(file_path, encoding="utf-8") as f:
    content = f.read()
```

### Testing Requirements

- **Unit Tests**: Critical paths for all engines
- **Edge Cases**: Empty inputs, invalid types, missing files
- **Docstring Tests**: Document test cases in docstrings
- **Type Checking**: Run `mypy` on all Python code

---

## Bash Script Standards

### Canonical Template

```bash
#!/usr/bin/env bash
export LC_ALL=C LANG=C

# Color definitions
BLK=$'\e[30m' RED=$'\e[31m' GRN=$'\e[32m' YLW=$'\e[33m'
BLU=$'\e[34m' MGN=$'\e[35m' CYN=$'\e[36m' WHT=$'\e[37m'
LBLU=$'\e[38;5;117m' PNK=$'\e[38;5;218m' BWHT=$'\e[97m'
DEF=$'\e[0m' BLD=$'\e[1m'

# Utility functions
has() { command -v "$1" &>/dev/null; }

# Script safety
set -Eeuo pipefail
shopt -s nullglob globstar
IFS=$'\n\t'

# Cleanup trap
cleanup() {
  set +e
  [[ -d ${WORKDIR:-} ]] && rm -rf "${WORKDIR}" || :
}
trap 'cleanup' EXIT
trap 'echo "Error at line $LINENO" >&2' ERR
```

### Code Patterns

#### Package Management

- **Detection Chain**: `paru` → `yay` → `pacman` (Arch-based) | `apt`/`dpkg`
  (Debian-based)
- **Pre-Installation Checks**: `pacman -Q pkg` | `flatpak list` |
  `cargo install --list`
- **Distro-Specific Hints**: Include installation commands for both ecosystems
  - Example: `(Arch: pacman -S tool)` `(Debian: apt-get install -y tool)`

#### Data Handling & Performance

- **Array Population**: `mapfile -t arr < <(command)` — avoids subshell
  performance penalties
- **Prohibitions**: Never parse `ls` output
- **Associative Arrays**: `declare -A cfg=([dry_run]=0 [debug]=0 [verbose]=0)`
- **Modern Tool Preferences**:
  - File finding: `fd` → `find`
  - Text search: `rg` → `grep`
  - File viewing: `bat` → `cat`
  - Text substitution: `sd` → `sed`
  - Download: `aria2` → `curl` → `wget` (no aria2 for piped output)
  - JSON processing: `jaq` → `jq`
  - Fuzzy selection: `sk` → `fzf`
- **Optimization Focus**: Batch operations, minimize subprocess spawning

#### Interactive Mode

- **Fuzzy Finder Integration**: Use fzf for path selection when args missing
- **Fallback Pattern**: `has fd && fd -t f | fzf || find . -type f | fzf`
- **AUR Helper Flags**:
  `--needed --noconfirm --removemake --cleanafter --sudoloop --skipreview --batchinstall`

#### Network Operations

- **Standard Flags**: `curl -fsL --http2`
- **Documentation**: Update README curl snippets when modifying entrypoints

---

## Tooling Standards

### Code Quality Pipeline

**Python**:

```bash
# Format with black
black rvp/

# Type check
mypy rvp/

# Lint
ruff check rvp/
```

**Bash**:

```bash
shfmt -i 2 -ln bash -bn -s file.sh && \
shellcheck -f diff file.sh | patch -Np1 && \
shellharden --replace file.sh
```

### Linting Configuration

- **MegaLinter**: Configured in `.megalinter.yml` (runs on CI)
- **Enabled**: BASH, PYTHON, JSON, YAML, MARKDOWN, DOCKERFILE
- **Bash**: shellcheck + shfmt + shellharden
- **Python**: ruff (default style)
- **YAML/JSON**: yamllint + prettier (config: `.prettierrc.yml`)

### Editor Configuration

- `.editorconfig`: Defines indentation, line endings, charset
  - Python: 4 spaces, 88 char line length
  - Bash: 2 spaces
  - YAML/JSON: 2 spaces, 120 char line length
  - Markdown: 2 spaces, 80 char line length

---

## Development Practices

### Test-Driven Development

Process: Write failing test (Red) → Implement minimal passing code (Green) →
Refactor for quality

### Change Classification

- **Structural**: Organization, formatting (no behavior changes)
- **Behavioral**: Function addition, modification, deletion
- **Rule**: Never mix in same commit

### Commit Requirements

All must be true: Tests pass | Zero warnings | Single logical unit | Clear
message Preference: Small, frequent, independent commits

### Code Quality Standards

- Single responsibility per function/module
- Loose coupling via interfaces
- Early returns for clarity
- Avoid premature abstraction
- Eliminate duplication immediately
- Explicit dependencies, clear intent
- Small, focused functions

### Prohibited Patterns

❌ Hardcoded values (use constants/config/environment) ❌ Repetitive code blocks
(create functions) ❌ Duplicated error handling (unify patterns) ❌ Replicated
logic (abstract appropriately)

---

## Pipeline Extension Guide

### Adding a New Engine

1. **Create engine file**: `rvp/engines/yourengine.py`
2. **Implement `run(ctx: Context) -> None`**:

   ```python
   from __future__ import annotations
   from ..context import Context

   def run(ctx: Context) -> None:
       """Process APK with YourEngine."""
       ctx.log("yourengine: starting")
       input_apk = ctx.current_apk or ctx.input_apk
       output_apk = ctx.output_dir / f"{input_apk.stem}.yourengine.apk"

       # Your processing logic here

       ctx.log(f"yourengine: output -> {output_apk}")
       ctx.set_current_apk(output_apk)
   ```

3. **Register in `core.py`**:

   ```python
   from .engines import revanced, magisk, lspatch, dtlx, yourengine

   _ENGINES: Dict[str, EngineFn] = {
       "revanced": revanced.run,
       "magisk": magisk.run,
       "lspatch": lspatch.run,
       "dtlx": dtlx.run,
       "yourengine": yourengine.run,
   }
   ```

4. **Update CLI help**: Add to `cli.py` engine description

### Creating Plugins

Plugins hook into pipeline stages via the
`handle_hook(ctx: Context, stage: str)` pattern:

```python
def handle_hook(ctx: Context, stage: str) -> None:
    """React to pipeline events."""
    if stage == "pre_pipeline":
        ctx.log("[plugin] Initializing...")
    elif stage.startswith("pre_engine:"):
        engine = stage.split(":", 1)[1]
        ctx.log(f"[plugin] Before {engine}")
    elif stage == "post_pipeline":
        ctx.log("[plugin] Cleanup...")
```

**Available Stages**:

- `pre_pipeline` / `post_pipeline`
- `pre_engine:{name}` / `post_engine:{name}` (e.g., `pre_engine:revanced`)

---

## Agent System

Available specialized agents (see `.github/agents.yml`):

- **bash-expert**: Script design & architecture, modern Bash patterns
- **performance-optimizer**: Profiling & optimization across stack
- **code-janitor**: Tech debt elimination, code simplification
- **critical-thinker**: Challenge assumptions, root cause analysis
- **code-reviewer**: Constructive feedback on quality/security
- **doc-writer**: Technical writing & documentation

Invoke: `@agent-name [task]`

## Chat Modes

Available modes (see `.github/chat-modes.yml`):

- `quick-fix`: Fast bug fixes (temp 0.2, 1000 tokens)
- `refactor`: Code quality improvement (temp 0.3, 2000 tokens)
- `feature`: New feature development (temp 0.4, 3000 tokens)
- `debug`: Problem investigation (temp 0.2, 2000 tokens)
- `optimize`: Performance tuning (temp 0.2, 2000 tokens)
- `review`: Code quality assessment (temp 0.3, 2000 tokens)
- `explain`: Concept explanation (temp 0.5, 2000 tokens)
- `script`: Bash script generation (temp 0.3, 2000 tokens)

Activate: `/mode [mode-name]`

---

## Git Workflow

### Branch Strategy

- **Main**: `main` (or `master`)
- **Claude Branches**: `claude/*` (auto-generated for AI sessions)
- **CI Triggers**: Pushes to `main`, `master`, `claude/**` branches

### Commit Discipline

- **Format**: Conventional Commits style preferred
- **Scope**: Single logical unit per commit
- **Message**: Clear, descriptive, imperative mood
- **Validation**: All tests pass, zero linter warnings

### CI/CD Pipelines

**MegaLinter** (`.github/workflows/mega-linter.yml`):

- Runs on all pushes/PRs
- Auto-applies formatting fixes
- Generates reports as artifacts

**Build Telegram** (`.github/workflows/build-telegram.yml`):

- APK building/patching workflow
- Telegram integration for notifications

**Validate Configs** (`.github/workflows/validate-configs.yml`):

- YAML/JSON schema validation

**Image Optimizer** (`.github/workflows/image-optimizer.yml`):

- Optimizes images in PRs

---

## Configuration Files Reference

| File                | Purpose                        |
| ------------------- | ------------------------------ |
| `.editorconfig`     | Cross-editor formatting rules  |
| `.megalinter.yml`   | Linter/formatter configuration |
| `.prettierrc.yml`   | YAML/JSON formatting           |
| `.yamllint.yml`     | YAML linting rules             |
| `.shellcheckrc`     | Bash linting configuration     |
| `pyproject.toml`    | Python package metadata        |
| `gradle.properties` | Android/Gradle JVM settings    |
| `.gitignore`        | VCS ignore patterns            |

---

## Current State & Next Steps

### Implemented ✅

- [x] Modular pipeline architecture
- [x] Context sharing between engines
- [x] Plugin hook system
- [x] CLI with argparse
- [x] Bash wrapper for Python CLI
- [x] Stub engines (revanced, lspatch, magisk, dtlx)
- [x] Comprehensive linting setup
- [x] CI/CD workflows

### Pending 🚧

- [ ] Real ReVanced CLI integration (`revanced.py`)
- [ ] LSPatch implementation (`lspatch.py`)
- [ ] Magisk module layout (`magisk.py`)
- [x] DTL-X analyzer/optimizer (`dtlx.py`) — ✅ Integrated with subprocess CLI
      calls
- [ ] Plugin discovery system (filesystem/config-based)
- [ ] Unit test suite (pytest)
- [ ] Integration tests
- [ ] CLI documentation (README)
- [ ] API documentation (Sphinx/mkdocs)

---

## Token Efficiency Symbols

**Flow**: → leads, ⇒ converts, ← rollback, ⇄ bidirectional, » then, ∴ therefore,
∵ because **Status**: ✅ done, ❌ fail, ⚠️ warn, 🔄 active, ⏳ pending, 🚨
critical **Domains**: ⚡ perf, 🔍 analysis, 🔧 cfg, 🛡️ sec, 📦 deploy, 🎨 UI, 🏗️
arch, 🗄️ DB, ⚙️ backend, 🧪 test **Operators**: & and, | or

---

## Quick Reference: Common Tasks

### Run the pipeline

```bash
# Via Bash wrapper
./bin/rvp path/to/app.apk -e revanced -e magisk -o output/

# Via Python module
python3 -m rvp.cli path/to/app.apk --engine revanced --out output/

# Multiple engines
./bin/rvp app.apk -e revanced -e lspatch -e dtlx --dtlx-analyze
```

### Linting workflow

```bash
# Format all code
shfmt -i 2 -ln bash -bn -s -w bin/rvp
black rvp/

# Lint
shellcheck bin/rvp
ruff check rvp/
mypy rvp/

# Full MegaLinter (local)
docker run --rm -v $(pwd):/tmp/lint oxsecurity/megalinter:v9
```

### Testing

```bash
# Unit tests (when implemented)
pytest rvp/

# Type checking
mypy rvp/

# Integration test (manual)
./bin/rvp test_data/example.apk -e revanced -o /tmp/out
```

---

## Resources

- **ReVanced**: https://github.com/revanced/revanced-cli
- **LSPatch**: https://github.com/LSPosed/LSPatch
- **Magisk Modules**: https://topjohnwu.github.io/Magisk/guides.html
- **Python Best Practices**: https://docs.python-guide.org/
- **Bash Manual**: https://www.gnu.org/software/bash/manual/
- **ShellCheck Wiki**: https://www.shellcheck.net/wiki/
- **PEP 8**: https://peps.python.org/pep-0008/

---

_Optimized for Claude's context window and reasoning capabilities_ _Last
updated: 2025-12-04_
