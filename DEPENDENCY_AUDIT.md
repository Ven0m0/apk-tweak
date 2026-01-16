# Dependency Audit Report

**Date:** 2026-01-16
**Project:** apk-tweak (revanced-pipeline)
**Python Version:** 3.11+

## Executive Summary

This project maintains an **exceptionally lean and well-maintained dependency profile**. All dependencies are up-to-date except for one minor version update available for `ruff`. No security vulnerabilities were detected. The project follows best practices with minimal direct dependencies and justified use of performance-oriented libraries.

**Overall Grade: A** 🟢

## Dependency Analysis

### Production Dependencies

| Package | Current | Latest | Status | Notes |
|---------|---------|--------|--------|-------|
| orjson  | 3.11.5  | 3.11.5 | ✅ Current | Performance-critical JSON library (~6x faster) |

**Analysis:**
- **orjson**: Single production dependency, used for config file parsing/serialization
  - Provides ~6x performance improvement over stdlib `json`
  - Has fallback to stdlib `json` if not available
  - Actively maintained with Python 3.14+ support
  - Download stats: 90M+ monthly downloads
  - **Justification:** ✅ Well-justified for performance-sensitive APK processing pipeline

### Development Dependencies

| Package    | Current | Latest  | Status | Notes |
|------------|---------|---------|--------|-------|
| pytest     | 9.0.2   | 9.0.2   | ✅ Current | Testing framework |
| mypy       | 1.19.1  | 1.19.1  | ✅ Current | Type checking |
| ruff       | 0.14.11 | 0.14.13 | ⚠️ Minor update | Linter & formatter |
| pip-audit  | 2.10.0  | 2.10.0  | ✅ Current | Security scanning |

**Analysis:**
- All dev dependencies actively used and essential for code quality
- `ruff`: 2 patch versions behind (0.14.11 → 0.14.13)
  - Note: Version 0.14.13 is identical to 0.14.12 (WASM packaging fix)
  - Safe to upgrade, no breaking changes expected

### Transitive Dependencies

**Total packages:** 40 (including dev dependencies)

All transitive dependencies are necessary and stem from the four dev tools:
- **mypy** → librt, mypy-extensions, pathspec, typing-extensions
- **pytest** → iniconfig, packaging, pluggy, pygments
- **ruff** → (standalone binary, minimal deps)
- **pip-audit** → cachecontrol, cyclonedx-python-lib, pip-api, pip-requirements-parser, platformdirs, requests, rich, tomli, tomli-w

**Bloat Assessment:** ✅ No unnecessary dependencies detected

## Security Audit

**Tool Used:** pip-audit 2.10.0
**Database:** Python Packaging Advisory Database (PyPI)
**Scan Date:** 2026-01-16

```
Result: No known vulnerabilities found ✅
```

All dependencies were checked against the PyPI security database with no reported CVEs or security advisories.

## Recommendations

### High Priority

1. **Update ruff** (Low risk, immediate)
   ```bash
   uv add --dev ruff --upgrade-package ruff
   ```
   - Upgrade from 0.14.11 → 0.14.13
   - Minimal changes (packaging fixes only)
   - Estimated time: < 1 minute

### Medium Priority

None identified. All other dependencies are current.

### Low Priority / Monitoring

1. **Monitor Python 3.14+ compatibility**
   - Current: Python 3.11+
   - All dependencies support Python 3.14+
   - Consider testing on Python 3.13/3.14 beta when available

2. **Consider pyproject.toml version constraints**
   - Current constraints are appropriate: `>=X.Y.Z,<MAJOR+1.0.0`
   - Prevents accidental major version upgrades
   - ✅ No changes needed

## Dependency Upgrade Strategy

### Regular Maintenance

Run these commands monthly to check for updates:

```bash
# Check for outdated packages
uv tree

# Security audit
uv run pip-audit --desc

# View available updates (manual check on PyPI)
# orjson: https://pypi.org/project/orjson/
# pytest: https://pypi.org/project/pytest/
# mypy: https://pypi.org/project/mypy/
# ruff: https://pypi.org/project/ruff/
# pip-audit: https://pypi.org/project/pip-audit/
```

### Upgrade Best Practices

1. **Before upgrading:**
   - Check changelog for breaking changes
   - Review migration guides for major versions
   - Ensure compatibility with Python 3.11+

2. **After upgrading:**
   ```bash
   # Format and lint
   uv run ruff format .
   uv run ruff check . --fix

   # Type check
   uv run mypy rvp/ --strict

   # Run tests
   uv run pytest -v
   ```

3. **For major version upgrades:**
   - Test on a separate branch
   - Run full CI pipeline
   - Review all deprecation warnings
   - Update version constraints in pyproject.toml

## Performance Considerations

### Current Setup

- **orjson**: Provides 6x faster JSON parsing/serialization
  - Critical for config loading in APK processing pipeline
  - Fallback ensures compatibility

### Potential Optimizations

None identified. The project already uses optimal dependencies for its use case.

## Compliance & Licensing

All dependencies use permissive licenses compatible with open source projects:
- **orjson**: MIT License
- **pytest**: MIT License
- **mypy**: MIT License
- **ruff**: MIT License
- **pip-audit**: Apache 2.0 License

✅ No licensing conflicts detected

## Action Items

- [ ] Upgrade ruff to 0.14.13 (immediate, low risk)
- [ ] Set up automated dependency scanning (e.g., Dependabot, Renovate)
- [ ] Schedule quarterly dependency review
- [ ] Add dependency audit to CI/CD pipeline

## Conclusion

This project demonstrates excellent dependency management:

✅ **Minimal dependencies** (1 production, 4 dev)
✅ **All up-to-date** (except 1 minor patch)
✅ **No security vulnerabilities**
✅ **No unnecessary bloat**
✅ **Well-justified dependencies**
✅ **Active maintenance**

The only recommendation is a minor ruff upgrade. Continue current dependency management practices.

## References

- [orjson PyPI](https://pypi.org/project/orjson/)
- [pytest PyPI](https://pypi.org/project/pytest/)
- [mypy PyPI](https://pypi.org/project/mypy/)
- [ruff PyPI](https://pypi.org/project/ruff/)
- [pip-audit PyPI](https://pypi.org/project/pip-audit/)
- [orjson GitHub](https://github.com/ijl/orjson)
- [ruff GitHub Releases](https://github.com/astral-sh/ruff/releases)
- [mypy Changelog](https://mypy.readthedocs.io/en/stable/changelog.html)

---

**Generated by:** Claude Code CLI
**Auditor:** Dependency Analysis Agent
**Next Review:** 2026-04-16 (quarterly)
