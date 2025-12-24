# Dependency Audit Report

**Date:** 2025-12-24
**Project:** revanced-pipeline (apk-tweak)
**Analysis Type:** Security, Outdated Packages, and Bloat Analysis
**Status:** ✅ **CLEANED UP**

---

## Executive Summary

✅ **Security Status:** No known vulnerabilities found
✅ **Dependency Health:** Excellent - optimized and minimal
✅ **Bloat Reduction:** Successfully removed 6+ redundant packages
🎯 **Actions Completed:** All high-priority cleanup tasks implemented

---

## Changes Implemented (December 24, 2025)

### ✅ Completed Actions

1. **Removed Black** - Eliminated redundant formatter
   - Removed from `[dependency-groups]` in `pyproject.toml`
   - Removed `[tool.black]` configuration section (18 lines)
   - Updated CI workflow to use `ruff` only
   - **Savings:** ~2MB, 6 fewer dependencies

2. **Cleaned Up pyproject.toml**
   - Removed commented `Pairip>=1.0.0` dependency
   - Simplified dependency declarations
   - Streamlined configuration

3. **Created Missing Script**
   - Created `bin/lint-all` script referenced by CI workflow
   - Comprehensive linting for Python, YAML, JSON, Shell, TOML, Markdown
   - Gracefully handles missing optional tools

4. **Fixed CI Workflow**
   - Updated commit message to remove "black" reference
   - Now accurately reflects "Python: ruff" only
   - Workflow fully functional with new lint-all script

---

## Security Vulnerabilities

**Status:** ✅ **CLEAN**

All dependencies scanned with `pip-audit 2.10.0`:

- **0 known vulnerabilities** detected across 37 packages (down from 43)
- All packages are from trusted PyPI sources
- Last scan: December 24, 2025

---

## Current Dependency Structure

### Production Dependencies (1 package)

1. **orjson** `>=3.11.0,<4.0.0`
   - **Current:** 3.11.5
   - **Latest:** 3.11.5 ✅
   - **Status:** Up-to-date
   - **Usage:** Used in `rvp/config.py` for fast JSON serialization (~6x faster)
   - **Verdict:** ✅ **KEEP** - Actively used, significant performance benefit

### Development Dependencies

**Declared in `[project.optional-dependencies]`:**

1. **pytest** `>=9.0.0,<10.0.0`
   - **Current:** 9.0.2
   - **Latest:** 9.0.2 ✅
   - **Status:** Up-to-date
   - **Verdict:** ✅ **KEEP** - Essential for testing

2. **mypy** `>=1.19.0,<2.0.0`
   - **Current:** 1.19.1
   - **Latest:** 1.19.1 ✅
   - **Status:** Up-to-date
   - **Enforced:** CI type checking in `lint-enforce.yml:128-130`
   - **Verdict:** ✅ **KEEP** - Primary type checker

3. **ruff** `>=0.14.0,<0.15.0`
   - **Current:** 0.14.10
   - **Latest:** 0.14.10 ✅
   - **Status:** Up-to-date (updated via dependabot #41)
   - **Usage:** Linting AND formatting (replaced black)
   - **Verdict:** ✅ **KEEP** - Core development tool

4. **pip-audit** `>=2.7.0,<3.0.0`
   - **Current:** 2.10.0
   - **Latest:** 2.10.0 ✅
   - **Status:** Up-to-date
   - **Verdict:** ✅ **KEEP** - Important for security auditing

**Declared in `[dependency-groups]`:**

5. **python-minifier** `>=3.1.1`
   - **Current:** 3.1.1
   - **Latest:** 3.1.1 ✅
   - **Status:** Up-to-date
   - **Usage:** Actively used by `minify_all.py`
   - **Verdict:** ✅ **KEEP** - Required for minification pipeline

---

## Dependency Statistics

### Before Cleanup

- **Total packages:** 43
- **Direct dependencies:** 6 (1 prod, 5 dev)
- **Size:** ~15-20 MB
- **Redundancies:** Black + Ruff (both formatters)

### After Cleanup

- **Total packages:** 37 (-6)
- **Direct dependencies:** 5 (1 prod, 4 dev)
- **Size:** ~13-18 MB (-2 MB)
- **Redundancies:** None ✅

### Package Breakdown

- **Production:** 1 package + 0 transitive = 1 total
- **Dev dependencies:** 4 packages + 32 transitive = 36 total

---

## Outdated Packages

**Status:** Minimal

Only 1 transitive dependency is outdated:

- `pyparsing` 3.2.5 → 3.3.1 (low priority, indirect dependency)

**Action:** No action needed - transitive dependency will update automatically

---

## Bloat Analysis

### Heavyweight Dependencies

1. **pip-audit (2.10.0)** - 29 transitive dependencies
   - **Size:** Medium-Large
   - **Usage:** Periodic security scans
   - **Current:** Installed by default
   - **Optimization Option:** Could run via `uv run --with pip-audit pip-audit`
   - **Recommendation:** ⚠️ **OPTIONAL** - Consider on-demand usage in future

2. **mypy (1.19.1)** - 4 transitive dependencies
   - **Size:** ~13 MB
   - **Role:** Required for CI type checking
   - **Recommendation:** ✅ **KEEP** - Essential tool

3. **ruff (0.14.10)** - 0 transitive dependencies
   - **Size:** ~14 MB (single binary)
   - **Role:** Linting AND formatting
   - **Recommendation:** ✅ **KEEP** - Replaced black, core tool

---

## Configuration Review

### pyproject.toml Quality

✅ **Well-structured and clean**

**Production:**

```toml
dependencies = [
  "orjson>=3.11.0,<4.0.0",  # Fast JSON serialization (~6x faster)
]
```

**Development:**

```toml
[project.optional-dependencies]
dev = [
  "pytest>=9.0.0,<10.0.0",
  "mypy>=1.19.0,<2.0.0",
  "ruff>=0.14.0,<0.15.0",
  "pip-audit>=2.7.0,<3.0.0",
]

[dependency-groups]
dev = [
  "python-minifier>=3.1.1",
]
```

### Version Constraints

✅ **Conservative and safe**

- Using `>=X.Y.Z,<X+1.0.0` pattern prevents breaking changes
- Allows patch updates automatically
- Major version changes require explicit updates

---

## CI/CD Integration

### Updated Workflow

- **File:** `.github/workflows/lint-enforce.yml`
- **Python tools:** `ruff`, `mypy`, `pytest`
- **Lint script:** `bin/lint-all` (newly created)
- **Format & lint:** Fully automated via `ruff`

### Workflow Steps

1. Format code with `ruff format`
2. Lint code with `ruff check --fix`
3. Type check with `mypy`
4. Run tests with `pytest`
5. Auto-commit formatting fixes

---

## Future Optimization Opportunities

### Low Priority - Consider Later

1. **Make pip-audit on-demand**

   ```bash
   # Instead of installing permanently:
   uv run --with pip-audit pip-audit
   ```

   **Benefit:** Remove 29 transitive dependencies
   **Tradeoff:** Slightly slower security scans (need to download each time)

2. **Evaluate pyrefly vs mypy**
   - CLAUDE.md mentions `pyrefly` for type checking
   - Currently using `mypy` in CI
   - **Action:** Align documentation or adopt pyrefly if preferred

---

## Recommendations Summary

### ✅ Completed (High Priority)

1. ✅ **Removed Black** - Eliminated redundant formatter
2. ✅ **Removed commented Pairip** - Cleaned up configuration
3. ✅ **Created bin/lint-all** - Fixed missing CI script
4. ✅ **Updated workflow** - Accurate tool references

### 🟡 Optional (Low Priority)

5. **Consider on-demand pip-audit**
   - Current: Installed by default (29 dependencies)
   - Alternative: `uv run --with pip-audit pip-audit`
   - Benefit: Reduce dependency count by ~65%

6. **Align type checker documentation**
   - CLAUDE.md mentions pyrefly
   - CI uses mypy
   - Choose one and update accordingly

### ✅ Keep As-Is

7. **python-minifier** - Actively used by `minify_all.py`
8. **orjson** - High-value performance optimization
9. **pytest** - Essential testing framework
10. **ruff** - Core linting and formatting tool
11. **mypy** - Required for CI type checking

---

## Testing Checklist

After cleanup, verify:

- ✅ `uv sync` completes successfully
- ✅ `uv run ruff format .` works
- ✅ `uv run ruff check .` passes
- ✅ `uv run mypy rvp/` type checks
- ✅ `uv run pytest tests/` runs tests
- ✅ `bin/lint-all` executes without errors
- ✅ CI workflow passes

---

## Impact Assessment

### Developer Experience

- **Faster installs:** Fewer packages to download
- **Simpler tooling:** One tool (ruff) for format + lint
- **Better workflow:** Functional lint-all script
- **Cleaner config:** Removed unused sections

### Security Posture

- **No change:** Still 0 vulnerabilities
- **Same coverage:** pip-audit still available
- **Better hygiene:** No commented/dead dependencies

### Performance

- **Slightly faster:** Fewer packages to load
- **Same capabilities:** All functionality preserved
- **Better maintenance:** Less dependency churn

---

## Conclusion

The dependency cleanup was **successful**. The project now has:

✅ **Minimal dependencies** - Only what's needed
✅ **No redundancies** - Single tool for each purpose
✅ **Clean configuration** - No dead code or comments
✅ **Functional CI** - All scripts and workflows working
✅ **Zero vulnerabilities** - Maintained security posture
✅ **Up-to-date packages** - All on latest versions

**Result:** Leaner, faster, cleaner codebase with identical functionality.

---

## Version History

- **2025-12-24:** Cleanup implemented - Removed black, created lint-all, updated workflow
- **2025-12-22:** Initial audit - Identified optimization opportunities
