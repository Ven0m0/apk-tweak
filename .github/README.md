# apk-tweak (rvp)

**apk-tweak** is an extensible pipeline system for Android APK modification and packaging. It provides a modular framework for chaining multiple patching engines—including ReVanced, LSPatch, and Magisk—into a single automated workflow.

## 🚀 Features

- **Pipeline Architecture**: Chain multiple processing engines sequentially.
- **Modular Engines**:
  - **ReVanced**: YouTube/app patching via ReVanced CLI.
  - **LSPatch**: LSPosed module integration.
  - **Magisk**: Automated Magisk module packaging.
  - **DTL-X**: APK analysis and optimization (stub).
- **Plugin System**: Hook-based event system (`pre_pipeline`, `pre_engine`, etc.) for custom logic.
- **CI/CD Ready**: Integrated with GitHub Actions for automated builds and releases.

## 📂 Project Structure

```text
apk-tweak/
├── rvp/                    # Core Python package (ReVanced Pipeline)
│   ├── cli.py              # CLI entry point
│   ├── core.py             # Pipeline orchestration & engine registry
│   ├── context.py          # Shared state dataclass
│   ├── engines/            # Processing engines
│   └── plugins/            # Hook-based plugin system
├── bin/rvp                 # Bash wrapper for CLI
└── .github/workflows/      # Automated CI pipelines
