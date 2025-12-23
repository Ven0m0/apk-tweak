# Dependency Audit Report

**Date:** 2025-12-22
**Project:** revanced-pipeline (apk-tweak)
**Analysis Type:** Security, Outdated Packages, and Bloat Analysis

---

## Executive Summary

✅ **Security Status:** No known vulnerabilities found
✅ **Dependency Health:** Generally good
⚠️ **Opportunities:** Several dev dependencies could be removed to reduce bloat

---

## Security Vulnerabilities

**Status:** ✅ **CLEAN**

All 36 dependencies scanned with `pip-audit 2.10.0`:
- **0 known vulnerabilities** detected
- All packages are from trusted PyPI sources
- Security audit passed successfully

---

## Production Dependencies Analysis

### Currently Declared (pyproject.toml)

1. **orjson** `>=3.11.0,<4.0.0`
   - **Current:** 3.11.5
   - **Latest:** 3.11.5 ✅
   - **Status:** Up-to-date
   - **Usage:** Used in `rvp/config.py` for fast JSON serialization (~6x faster than stdlib)
   - **Verdict:** ✅ **KEEP** - Actively used and provides significant performance benefits

2. **Pairip** (commented out)
   - **Status:** Not installed
   - **Purpose:** APK decompilation/rebuilding
   - **Verdict:** ✅ **REMOVE** - Already commented out, should be fully removed from pyproject.toml

---

## Development Dependencies Analysis

### Declared in `[project.optional-dependencies]`

1. **pytest** `>=9.0.0,<10.0.0`
   - **Current:** 9.0.2
   - **Latest:** ~9.0.2 ✅
   - **Status:** Up-to-date
   - **Verdict:** ✅ **KEEP** - Essential for testing

2. **mypy** `>=1.19.0,<2.0.0`
   - **Current:** 1.19.1
   - **Latest:** ~1.19.1 ✅
   - **Status:** Up-to-date
   - **Notes:** Configured in `pyproject.toml` and enforced in CI as the primary type checker
   - **Verdict:** ✅ **KEEP** - Actively used for static type checking

3. **ruff** `>=0.14.0,<0.15.0`
   - **Current:** 0.14.9
   - **Latest:** ~0.14.9 ✅
   - **Status:** Up-to-date
   - **Verdict:** ✅ **KEEP** - Actively used for linting and formatting

4. **pip-audit** `>=2.7.0,<3.0.0`
   - **Current:** 2.10.0
   - **Latest:** ~2.10.0 ✅
   - **Status:** Up-to-date
   - **Verdict:** ✅ **KEEP** - Important for security auditing

### Declared in `[dependency-groups]`

5. **black** `>=25.12.0`
   - **Current:** 25.12.0
   - **Latest:** 25.12.0 ✅
   - **Status:** Up-to-date
   - **Notes:** Ruff can handle formatting (configured in pyproject.toml)
   - **Verdict:** ⚠️ **CONSIDER REMOVING** - Redundant with Ruff's formatting capabilities

6. **python-minifier** `>=3.1.1`
   - **Current:** 3.1.1
   - **Latest:** ~3.1.1 ✅
   - **Status:** Up-to-date
   - **Usage:** Actively used by `minify_all.py` for Python code minification
   - **Verdict:** ✅ **KEEP** - Required for the active minification pipeline

---

## Bloat Analysis

### Total Dependencies Installed: 44 packages

Most of these are transitive dependencies (required by the packages we explicitly declare).

### Heavyweight Dependencies

1. **black (25.12.0)**
   - **Size:** ~1.4-1.9 MB (platform-dependent)
   - **Dependencies:** 6 packages (click, mypy-extensions, packaging, pathspec, platformdirs, pytokens)
   - **Redundancy:** Ruff can format code using `ruff format`
   - **Recommendation:** ❌ **REMOVE** - Use `ruff format` instead

2. **mypy (1.19.1)**
   - **Size:** Medium
   - **Dependencies:** 4 packages (librt, mypy-extensions, pathspec, typing-extensions)
   - **Redundancy:** CLAUDE.md specifies using `pyrefly` for type checking
   - **Recommendation:** ❌ **REMOVE** if pyrefly is the standard

3. **pip-audit (2.10.0)**
   - **Size:** Medium-Large
   - **Dependencies:** 29+ packages including cyclonedx-python-lib, requests, rich, etc.
   - **Usage:** Security auditing (run periodically, not continuously)
   - **Recommendation:** ⚠️ **OPTIONAL** - Could be run via `uv run --with pip-audit` instead of installing permanently

### Minimal Footprint Recommendation

**Production:**
```toml
dependencies = [
  "orjson>=3.11.0,<4.0.0",
]
```

**Development (minimal):**
```toml
[project.optional-dependencies]
dev = [
  "pytest>=9.0.0,<10.0.0",
  "ruff>=0.14.0,<0.15.0",
]
```

**On-demand tools** (not installed by default):
- `pip-audit` - Run via `uv run --with pip-audit pip-audit`
- `python-minifier` - Run via `uv run --with python-minifier pyminify ...` if needed

---

## Recommendations Summary

### 🔴 HIGH PRIORITY - Remove

1. **Remove Black** - Redundant with Ruff
   ```bash
   # pyproject.toml: Remove black from [dependency-groups]
   # Use: uv run ruff format .
   ```

2. **Remove commented Pairip dependency** - Clean up pyproject.toml
   ```toml
   # Remove this line:
   # "Pairip>=1.0.0",  # RKPairip APK decompilation/rebuilding
   ```

### 🟡 MEDIUM PRIORITY - Consider

3. **Align type-checking tooling**
   ```bash
   # Current setup: mypy is configured and enforced in CI.
   # Optionally evaluate pyrefly. If you adopt it:
   #  - Add pyrefly as a dependency
   #  - Integrate it into CI alongside or instead of mypy
   # Only then reconsider removing mypy to avoid breaking checks.
   ```

4. **Make pip-audit optional** - Use on-demand instead
   ```bash
   # Remove from dev dependencies
   # Run when needed: uv run --with pip-audit pip-audit
   ```

### ✅ LOW PRIORITY - Keep

5. **Keep python-minifier** - Actively used via `minify_all.py` (uses `pyminify`)
6. **Keep orjson** - Actively used, good performance benefit
7. **Keep pytest** - Essential for testing
8. **Keep ruff** - Primary linter and formatter

---

## Version Constraints Review

Current constraints are well-structured:
- **Production:** Using conservative ranges (`>=X.Y.Z,<X+1.0.0`)
- **Development:** Same conservative approach
- **Benefits:** Prevents breaking changes while allowing patches

**Recommendation:** ✅ Maintain current versioning strategy

---

## Configuration Cleanup Needed

### pyproject.toml Issues

1. **Black configuration present but tool is redundant**
   - Lines 142-159: `[tool.black]` section
   - **Action:** Remove if switching fully to Ruff

2. **Commented dependency**
   - Line 16: Commented Pairip dependency
   - **Action:** Remove entirely

---

## Next Steps

1. **Immediate Actions:**
   - Remove `black` from `[dependency-groups]`
   - Remove commented Pairip line
   - Remove `[tool.black]` configuration section
   - Update workflows to use `ruff format` instead of `black`

2. **Verify and Act:**
   - Check if `python-minifier` is used (check `minify_all.py`)
   - Verify `pyrefly` is working and remove `mypy` if confirmed

3. **Optimize:**
   - Move `pip-audit` to on-demand usage
   - Update CI/CD to use `uv run --with` pattern for security audits

4. **Test:**
   - Run full test suite after removals
   - Verify formatting still works with Ruff
   - Ensure CI/CD pipelines pass

---

## Estimated Impact

**Current total dev dependencies:** ~44 packages
**After cleanup:** ~20-25 packages
**Size reduction:** ~40-50%
**Security impact:** None (no vulnerabilities currently)
**Functionality impact:** None (using better alternatives)

---

## Conclusion

The project has a clean security posture with no vulnerabilities. However, there are opportunities to reduce bloat by:
- Removing redundant tools (Black, potentially Mypy)
- Moving infrequent tools to on-demand usage (pip-audit)
- Cleaning up unused/commented dependencies

These changes will simplify the dependency tree, reduce installation time, and maintain the same functionality with better tooling (Ruff).
