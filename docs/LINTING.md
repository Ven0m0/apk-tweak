# Linting & Formatting Guide

Comprehensive lint+format enforcement system for apk-tweak.

## Quick Start

```bash
# Run all linters and formatters
./bin/lint-all

# Auto-format Python code
ruff format .
black .

# Auto-format shell scripts (requires shfmt)
shfmt -w -i 2 -ln bash -bn -s bin/rvp
```

## Architecture

### File Types & Tools

| File Type | Formatter | Linter | Config File |
|-----------|-----------|--------|-------------|
| **YAML** | yamlfmt | yamllint | `.yamllint.yml` |
| **JSON** | prettier/biome | - | `.prettierrc.yml` |
| **Shell** | shfmt | shellcheck | `.shellcheckrc` |
| **Python** | ruff+black | ruff | `pyproject.toml` |
| **Markdown** | mdformat/prettier | markdownlint | `.markdownlint.json` |
| **TOML** | taplo | - | - |
| **Actions** | yamlfmt | actionlint | `.yamllint.yml` |

### Indentation Standards

**All files use 2-space indentation** (enforced via `.editorconfig`):

- Shell scripts: 2 spaces
- Python: 2 spaces (configured in `pyproject.toml`)
- YAML: 2 spaces
- JSON: 2 spaces
- TOML: 2 spaces
- Markdown: 2 spaces

### Tool Detection

The `lint-all` script automatically detects available tools and falls back gracefully:

- **Required**: `rg` (ripgrep)
- **Recommended**: `fd`, `prettier`, `ruff`, `black`, `eslint`
- **Optional**: `yamlfmt`, `yamllint`, `shfmt`, `shellcheck`, `mdformat`, `markdownlint`, `taplo`, `actionlint`

## Configuration Files

### `.editorconfig`

Master configuration for all editors. Defines:

- Indentation: 2 spaces (except Python: 2 spaces per project standard)
- Line endings: LF
- Charset: UTF-8
- Max line length: 120 (Python/YAML/JSON), 80 (Markdown)

### `pyproject.toml`

Python-specific configuration:

```toml
[tool.ruff]
line-length = 120
indent-width = 2
target-version = "py311"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"

[tool.black]
line-length = 120
target-version = ['py311']
```

### `.yamllint.yml`

YAML linting rules:

- 2-space indentation
- 120 char line length
- Unix line endings
- No document start/end markers

### `.prettierrc.yml`

JSON/YAML/Markdown formatting:

- Print width: 120
- Tab width: 2
- Single quotes for JS/TS
- Double quotes for JSON
- Markdown prose wrap: 80 chars

### `.shellcheckrc`

Shell script linting:

- Shell: bash
- Enable all optional checks
- Ignore: SC1090, SC1091

### `.markdownlint.json`

Markdown linting rules:

- Line length: 80 (headings: 120)
- Heading style: ATX (`#`)
- List style: dash (`-`)
- Code blocks: fenced (backticks)

## CI/CD Integration

### GitHub Actions Workflow

See `.github/workflows/lint-enforce.yml`:

1. **Lint & Format**: Runs `lint-all` on every push/PR
2. **Auto-fix**: Automatically commits formatting fixes
3. **Type Check**: Runs `mypy` on Python code
4. **Tests**: Runs `pytest` on test suite
5. **Fail on Error**: Returns non-zero exit code if errors remain

### Local Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
set -e

echo "Running linters..."
./bin/lint-all

if [[ $? -ne 0 ]]; then
  echo "❌ Linting failed. Fix errors before committing."
  exit 1
fi

echo "✅ Linting passed"
```

## Manual Linting

### Python

```bash
# Format
ruff format .
black .

# Lint
ruff check --fix .

# Type check
mypy rvp/

# Test
pytest tests/
```

### Shell Scripts

```bash
# Format
shfmt -w -i 2 -ln bash -bn -s bin/rvp

# Lint
shellcheck bin/rvp

# Harden
shellharden --check bin/rvp
```

### YAML

```bash
# Format
yamlfmt -formatter indent=2,max_line_length=120 *.yml

# Lint
yamllint -f parsable *.yml
```

### JSON

```bash
# Format
prettier --write *.json

# Or with biome
biome format --write *.json
```

### Markdown

```bash
# Format
mdformat --wrap 80 *.md

# Or with prettier
prettier --write *.md

# Lint
markdownlint --fix *.md
```

### GitHub Actions

```bash
# Format
yamlfmt .github/workflows/*.yml

# Lint
actionlint .github/workflows/*.yml
```

## Disabling Rules

### Python (ruff)

Add to `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
  "E501",  # line too long
  "PLR0913",  # too many arguments
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow asserts in tests
```

### Shell (shellcheck)

Add to `.shellcheckrc`:

```bash
disable=SC2086  # Disable specific check
```

Or inline:

```bash
# shellcheck disable=SC2086
command $unquoted_var
```

### YAML (yamllint)

Add to `.yamllint.yml`:

```yaml
rules:
  line-length:
    max: 150  # Override line length
```

### Markdown (markdownlint)

Add to `.markdownlint.json`:

```json
{
  "MD013": {
    "line_length": 100
  }
}
```

## Troubleshooting

### "Tool not found" errors

Install missing tools:

```bash
# Arch/Manjaro
paru -S fd ripgrep shfmt shellcheck prettier yamlfmt yamllint actionlint

# Debian/Ubuntu
apt-get install fd-find ripgrep
npm install -g prettier markdownlint-cli
pip install ruff black yamllint
```

### "Indentation errors"

Run formatters before linters:

```bash
# Format first
ruff format .
prettier --write .

# Then lint
ruff check .
yamllint .
```

### "Line too long" errors

Most formatters auto-wrap. For manual fixes:

- Python: Use implicit string concatenation or `textwrap`
- Shell: Use line continuation `\`
- YAML: Use block scalars `|` or `>`

### "Files modified but not committed"

The CI workflow auto-commits formatting fixes. Pull changes:

```bash
git pull --rebase origin your-branch
```

## Best Practices

1. **Run linters locally** before pushing
2. **Use editor integration** (VS Code, Vim, Emacs plugins)
3. **Format on save** to catch issues early
4. **Review CI output** for remaining errors
5. **Fix root causes** not just symptoms

## Editor Integration

### VS Code

Install extensions:

- `charliermarsh.ruff` (Python)
- `esbenp.prettier-vscode` (JSON/YAML/MD)
- `timonwong.shellcheck` (Shell)
- `redhat.vscode-yaml` (YAML)
- `DavidAnson.vscode-markdownlint` (Markdown)

Add to `settings.json`:

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[json]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[yaml]": {
    "editor.formatOnSave": true
  }
}
```

### Vim/Neovim

Use ALE or null-ls:

```vim
let g:ale_linters = {
\   'python': ['ruff', 'mypy'],
\   'sh': ['shellcheck'],
\   'yaml': ['yamllint'],
\}

let g:ale_fixers = {
\   'python': ['ruff', 'black'],
\   'sh': ['shfmt'],
\   'yaml': ['prettier'],
\   'json': ['prettier'],
\}
```

## Resources

- **Ruff**: https://docs.astral.sh/ruff/
- **Black**: https://black.readthedocs.io/
- **ShellCheck**: https://www.shellcheck.net/
- **Prettier**: https://prettier.io/
- **yamllint**: https://yamllint.readthedocs.io/
- **EditorConfig**: https://editorconfig.org/
