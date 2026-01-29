#!/usr/bin/env bash

set -euo pipefail

# Comprehensive linting and formatting script for apk-tweak
# This script runs all linters and formatters in the correct order

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Starting comprehensive lint & format"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall success
OVERALL_SUCCESS=0

run_check() {
  local name="$1"
  shift
  echo ""
  echo -e "${YELLOW}Running: $name${NC}"
  if "$@"; then
    echo -e "${GREEN}✓ $name passed${NC}"
  else
    echo -e "${RED}✗ $name failed${NC}"
    OVERALL_SUCCESS=1
  fi
}

# 1. Python formatting with ruff
run_check "Python formatting (ruff)" ruff format .

# 2. Python linting with ruff (auto-fix)
run_check "Python linting (ruff)" ruff check . --fix

# 3. YAML formatting (if yamlfmt is available)
if command -v yamlfmt &>/dev/null; then
  run_check "YAML formatting (yamlfmt)" yamlfmt -quiet .
else
  echo -e "${YELLOW}⊘ yamlfmt not found, skipping YAML formatting${NC}"
fi

# 4. YAML linting (if yamllint is available)
if command -v yamllint &>/dev/null; then
  run_check "YAML linting (yamllint)" yamllint . || true
else
  echo -e "${YELLOW}⊘ yamllint not found, skipping YAML linting${NC}"
fi

# 5. JSON/Markdown formatting with prettier (if available)
if command -v prettier &>/dev/null; then
  run_check "JSON/Markdown formatting (prettier)" prettier --write "**/*.{json,md}" --ignore-path .gitignore
else
  echo -e "${YELLOW}⊘ prettier not found, skipping JSON/Markdown formatting${NC}"
fi

# 6. Markdown linting (if markdownlint is available)
if command -v markdownlint &>/dev/null; then
  run_check "Markdown linting (markdownlint)" markdownlint --fix "**/*.md" --ignore node_modules || true
else
  echo -e "${YELLOW}⊘ markdownlint not found, skipping Markdown linting${NC}"
fi

# 7. Shell script formatting (if shfmt is available)
if command -v shfmt &>/dev/null; then
  run_check "Shell formatting (shfmt)" shfmt -w -i 2 -ci -bn .
else
  echo -e "${YELLOW}⊘ shfmt not found, skipping shell formatting${NC}"
fi

# 8. Shell script linting (if shellcheck is available)
if command -v shellcheck &>/dev/null; then
  run_check "Shell linting (shellcheck)" find . -name "*.sh" -type f -not -path "*/node_modules/*" -not -path "*/.venv/*" -exec shellcheck {} + || true
else
  echo -e "${YELLOW}⊘ shellcheck not found, skipping shell linting${NC}"
fi

# 9. TOML formatting (if taplo is available)
if command -v taplo &>/dev/null; then
  run_check "TOML formatting (taplo)" taplo format
else
  echo -e "${YELLOW}⊘ taplo not found, skipping TOML formatting${NC}"
fi

# 10. GitHub Actions linting (if actionlint is available)
if command -v actionlint &>/dev/null; then
  run_check "GitHub Actions linting (actionlint)" actionlint || true
else
  echo -e "${YELLOW}⊘ actionlint not found, skipping Actions linting${NC}"
fi

echo ""
echo "========================================="
if [ $OVERALL_SUCCESS -eq 0 ]; then
  echo -e "${GREEN}All linting and formatting complete!${NC}"
else
  echo -e "${RED}Some checks failed. Please review above.${NC}"
fi
echo "========================================="

exit $OVERALL_SUCCESS
