# APK Tweak - ReVanced Pipeline (RVP)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://github.com/python/mypy)

Extensible pipeline for APK modifications using ReVanced, Magisk modules,
LSPatch, DTL-X, and media optimization.

## Features

- **🔧 Multi-Engine Support**: ReVanced, Magisk, LSPatch, DTL-X, Media Optimizer
- **🖼️ Media Optimization**: PNG/JPG compression, MP3/OGG re-encoding, DPI-aware resource filtering
- **🔌 Plugin System**: Extensible hook-based plugin architecture
- **⚡ Performance**: O(n) complexity, efficient caching
- **📦 Type Safe**: Full mypy strict mode compliance
- **🧪 Well Tested**: Comprehensive test coverage
- **🎯 Clean Code**: PEP 8, PEP 257, ruff formatted

## Installation

```bash
# Clone repository
git clone https://github.com/Ven0m0/apk-tweak.git
cd apk-tweak

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Basic usage with ReVanced
rvp input.apk

# Multiple engines
rvp input.apk -e revanced -e magisk

# With config file
rvp -c config.json

# Enable DTL-X analysis
rvp input.apk -e dtlx --dtlx-analyze --dtlx-optimize

# Media optimization - compress images and audio
rvp input.apk -e media_optimizer --optimize-images --optimize-audio

# Target specific DPI (keep only xhdpi and xxhdpi resources)
rvp input.apk -e media_optimizer --target-dpi xhdpi,xxhdpi

# Combine media optimization with other engines
rvp input.apk -e media_optimizer -e revanced --optimize-images \
  --target-dpi xxhdpi
```

## Configuration

Create a `config.json` file:

```json
{
  "input_apk": "app.apk",
  "output_dir": "output",
  "engines": ["revanced", "magisk"],
  "dtlx_analyze": true,
  "dtlx_optimize": false,
  "revanced_cli_path": "tools/revanced-cli.jar",
  "revanced_patches_path": "tools/patches.jar"
}
```

## Architecture

### Pipeline Flow

```text
Input APK → Engine 1 → Engine 2 → ... → Output APK
             ↓          ↓              ↓
          Plugins    Plugins        Plugins
```

### Engines

- **ReVanced**: Apply ReVanced patches to APKs
- **Magisk**: Package APK as Magisk module
- **LSPatch**: Apply LSPatch modifications
- **DTL-X**: Analyze/optimize with DTL-X
- **Media Optimizer**: Compress images (PNG/JPG), optimize audio (MP3/OGG), filter DPI-specific resources

### Plugin System

Plugins hook into pipeline stages:

- `pre_pipeline` / `post_pipeline`
- `pre_engine:{name}` / `post_engine:{name}`

Example plugin:

```python
from rvp.context import Context

def handle_hook(ctx: Context, stage: str) -> None:
  """Handle pipeline hooks."""
  ctx.log(f"Plugin triggered at: {stage}")
```

### Media Optimizer

The media optimizer engine reduces APK size through:

#### Image Optimization

- **PNG**: Lossy compression using `pngquant` (65-80% quality range)
- **JPEG**: Optimization using `jpegoptim` (85% quality, metadata stripped)

#### Audio Optimization

- **MP3**: Re-encode using `ffmpeg` with libmp3lame (96k bitrate)
- **OGG**: Re-encode using `ffmpeg` with libvorbis (96k bitrate)

#### DPI Resource Filtering

Remove drawable resources for non-target screen densities:

- **ldpi** (120 dpi)
- **mdpi** (160 dpi)
- **hdpi** (240 dpi)
- **xhdpi** (320 dpi) - Common for most modern phones
- **xxhdpi** (480 dpi) - Common for high-end phones
- **xxxhdpi** (640 dpi) - Highest density
- **tvdpi** (213 dpi) - TV screens
- **nodpi** - Always preserved (density-independent)

**Usage:**

```bash
# Optimize everything for xxhdpi devices
rvp app.apk -e media_optimizer --optimize-images --optimize-audio \
  --target-dpi xxhdpi

# Keep multiple DPIs (comma-separated)
rvp app.apk -e media_optimizer --target-dpi xhdpi,xxhdpi

# Only optimize images
rvp app.apk -e media_optimizer --optimize-images
```

**Dependencies:**

```bash
# Arch Linux
pacman -S pngquant jpegoptim ffmpeg

# Debian/Ubuntu
apt-get install pngquant jpegoptim ffmpeg
```

## Development

```bash
# Run tests
pytest tests/ -v

# Lint & format
ruff check .
ruff format .

# Type check
mypy rvp/ --strict

# Run all checks
ruff check . && ruff format . && mypy rvp/ --strict && pytest tests/
```

## Project Structure

```text
apk-tweak/
├── rvp/                    # Main package
│   ├── __init__.py         # Package exports
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration schema
│   ├── context.py          # Pipeline context
│   ├── core.py             # Pipeline orchestration
│   ├── utils.py            # Shared utilities
│   ├── engines/            # Engine modules
│   │   ├── revanced.py
│   │   ├── magisk.py
│   │   ├── lspatch.py
│   │   └── dtlx.py
│   └── plugins/            # Plugin modules
│       └── example_plugin.py
├── tests/                  # Test suite
│   ├── test_core.py
│   ├── test_engines.py
│   ├── test_utils.py
│   ├── test_plugins.py
│   └── test_cli.py
├── pyproject.toml          # Project metadata & config
└── README.md               # This file
```

## Performance

- **Dynamic Discovery**: O(n) engine/plugin loading where n = module count
- **File Operations**: Optimized with streaming I/O
- **Caching**: Global caching for discovered engines/plugins
- **Type Safety**: Zero runtime overhead from type hints

## Best Practices

1. **Engine Development**:

- Accept `Context` as sole parameter
- Update `ctx.current_apk` after modification
- Use `ctx.log()` for output
- Raise exceptions on failure

2. **Plugin Development**:

- Implement `handle_hook(ctx, stage)`
- Use lightweight operations
- Catch exceptions internally

3. **Testing**:

- Use `tmp_path` fixture
- Test both success and failure paths
- Verify state changes in context

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

Ensure all checks pass:

```bash
ruff check . && mypy rvp/ --strict && pytest tests/
```

## License

This project is open source. See repository for details.

## Credits

- **ReVanced**: https://github.com/revanced
- **Magisk**: https://github.com/topjohnwu/Magisk
- **LSPatch**: https://github.com/LSPosed/LSPatch
- **DTL-X**: https://github.com/Gameye98/DTL-X

---

**Note**: This is a pipeline framework. Actual tool binaries (revanced-cli.jar,
etc.) must be obtained separately.
