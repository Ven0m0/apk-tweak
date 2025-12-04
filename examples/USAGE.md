# Usage Examples

## Basic ReVanced Patching

Simple patching with one patch bundle:

```bash
rvp youtube.apk -c examples/basic-config.json
```

**Config** (`basic-config.json`):

```json
{
  "input_apk": "youtube.apk",
  "output_dir": "output",
  "engines": ["revanced"],
  "revanced_cli_path": "tools/revanced-cli.jar",
  "revanced_patches_path": "tools/patches.jar",
  "revanced_integrations_path": "tools/integrations.apk"
}
```

## Multi-Patch with Optimization

Apply multiple patches and optimize:

```bash
rvp youtube.apk -c examples/advanced-revanced-config.json
```

**Expected Output:**

```
[12:00:00] [INFO] rvp.core: Starting pipeline for: youtube.apk
[12:00:00] [INFO] rvp.context: Current APK updated: youtube.apk
[12:00:01] [INFO] rvp: revanced: starting multi-patch pipeline
[12:00:01] [INFO] rvp: revanced: Applying patch bundle 1/3: revanced-patches-official.jar
[12:00:30] [INFO] rvp: revanced: Applying patch bundle 2/3: revanced-patches-extended.jar
[12:01:00] [INFO] rvp: revanced: Applying patch bundle 3/3: custom-patches.jar
[12:01:30] [INFO] rvp: revanced: Starting optimization phase
[12:01:31] [INFO] rvp: optimizer: Decompiling youtube.patched.apk
[12:02:00] [INFO] rvp: optimizer: Starting debloat process
[12:02:05] [INFO] rvp: optimizer: Debloat complete - removed 147 items
[12:02:05] [INFO] rvp: optimizer: Starting resource minification
[12:02:10] [INFO] rvp: optimizer: Minification complete - removed 312 files (45MB)
[12:02:10] [INFO] rvp: optimizer: Recompiling APK to youtube.recompiled.apk
[12:03:30] [INFO] rvp: optimizer: Running zipalign on youtube.recompiled.apk
[12:03:35] [INFO] rvp: revanced: Optimization complete - output/youtube.revanced.apk
[12:03:35] [INFO] rvp.core: Pipeline finished. Final APK: output/youtube.revanced.apk
```

**Results:**

- Original: 150MB
- Patched: 150MB
- Optimized: 98MB (35% reduction)

## Magisk Module from Patched APK

Create a Magisk module from an optimized APK:

```bash
rvp youtube.apk -c examples/full-pipeline-config.json
```

**Config** (`full-pipeline-config.json`):

```json
{
  "input_apk": "youtube.apk",
  "output_dir": "output",
  "engines": ["revanced", "magisk"],
  "revanced_patch_bundles": ["tools/patches.jar"],
  "revanced_optimize": true,
  "magisk_id": "revanced_youtube"
}
```

**Output:**

- `output/youtube.revanced.apk` - Optimized APK
- `output/revanced_youtube-magisk.zip` - Magisk module

## Custom Debloat Configuration

Remove specific components:

```json
{
  "input_apk": "app.apk",
  "engines": ["revanced"],
  "revanced_optimize": true,
  "debloat_patterns": [
    "**/admob",
    "**/google/ads",
    "**/facebook/ads",
    "**/analytics",
    "**/crashlytics",
    "**/firebase/analytics",
    "com/unity3d/ads/**",
    "assets/admob_*",
    "lib/**/libadmob.so"
  ]
}
```

## Aggressive Minification

Remove all high-DPI resources and media:

```json
{
  "minify_patterns": [
    "res/drawable-xxxhdpi/*",
    "res/drawable-xxhdpi/*",
    "res/drawable-xhdpi/*",
    "res/raw/*.mp3",
    "res/raw/*.wav",
    "res/raw/*.ogg",
    "res/raw/*.mp4",
    "assets/videos/*",
    "assets/music/*"
  ]
}
```

## Selective Patching

Apply only specific patches:

```json
{
  "revanced_patch_bundles": ["tools/all-patches.jar"],
  "revanced_include_patches": [
    "hide-ads",
    "hide-shorts-button",
    "sponsorblock",
    "return-youtube-dislike",
    "custom-branding"
  ],
  "revanced_exclude_patches": ["premium-heading", "swipe-controls"]
}
```

## Fast Mode (No Optimization)

Skip optimization for faster testing:

```json
{
  "input_apk": "app.apk",
  "engines": ["revanced"],
  "revanced_patch_bundles": ["tools/patches.jar"],
  "revanced_optimize": false
}
```

**Speed Comparison:**

- With optimization: 3-4 minutes
- Without optimization: 30-60 seconds

## Complete Production Configuration

Full-featured config for production use:

```json
{
  "input_apk": "youtube-v18.apk",
  "output_dir": "release",
  "engines": ["revanced"],

  "revanced_cli_path": "tools/revanced-cli-latest.jar",
  "revanced_patch_bundles": [
    "tools/revanced-patches-official-v2.1.jar",
    "tools/revanced-patches-extended-v1.5.jar",
    "tools/custom-youtube-patches.jar"
  ],
  "revanced_integrations_path": "tools/revanced-integrations-latest.apk",

  "revanced_optimize": true,
  "revanced_debloat": true,
  "revanced_minify": true,

  "revanced_include_patches": [
    "hide-ads",
    "hide-shorts-button",
    "sponsorblock",
    "return-youtube-dislike",
    "custom-branding",
    "premium-heading",
    "enable-debugging"
  ],

  "revanced_exclude_patches": [
    "swipe-controls",
    "tablet-layout",
    "hdr-brightness"
  ],

  "debloat_patterns": [
    "**/admob",
    "**/google/ads",
    "**/doubleclick",
    "**/analytics",
    "**/crashlytics",
    "**/firebase/analytics",
    "**/measurement",
    "com/google/android/gms/ads/**",
    "com/google/firebase/analytics/**"
  ],

  "minify_patterns": [
    "res/drawable-xxxhdpi/*",
    "res/drawable-xxhdpi/*",
    "res/raw/*.mp3",
    "res/raw/*.ogg",
    "assets/unused_*"
  ],

  "apktool_path": "tools/apktool-2.9.3.jar",
  "zipalign_path": "/usr/local/bin/zipalign"
}
```

## Checking Results

After running the pipeline:

```bash
# Check final APK size
ls -lh output/youtube.revanced.apk

# Compare with original
du -h youtube.apk output/youtube.revanced.apk

# Verify APK structure
unzip -l output/youtube.revanced.apk | grep -E "(admob|ads|analytics)"

# Test APK (requires Android device/emulator)
adb install output/youtube.revanced.apk
```

## Troubleshooting

### Error: "ReVanced CLI not found"

```bash
# Download ReVanced CLI
wget https://github.com/revanced/revanced-cli/releases/latest/download/revanced-cli.jar -O tools/revanced-cli.jar
```

### Error: "apktool not found"

```bash
# Install apktool
# Linux/Mac:
sudo apt install apktool
# Or download manually:
wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool
```

### Error: "zipalign not found"

```bash
# Install Android SDK build-tools
# Then add to PATH:
export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
```

### APK Installation Failed

```bash
# Sign the APK
apksigner sign --ks ~/.android/debug.keystore output/youtube.revanced.apk

# Or use jarsigner
jarsigner -verbose -keystore ~/.android/debug.keystore output/youtube.revanced.apk androiddebugkey
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Patched APK

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install RVP
        run: pip install -e .

      - name: Download Tools
        run: |
          mkdir tools
          wget https://github.com/revanced/revanced-cli/releases/latest/download/revanced-cli.jar -O tools/revanced-cli.jar
          wget https://github.com/revanced/revanced-patches/releases/latest/download/revanced-patches.jar -O tools/patches.jar

      - name: Build APK
        run: rvp input.apk -c config.json

      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: patched-apk
          path: output/*.apk
```

## Best Practices

1. **Version Control**: Track your config.json in git
2. **Test Incrementally**: Start simple, add features gradually
3. **Keep Tools Updated**: Update ReVanced components regularly
4. **Backup Originals**: Keep unmodified APKs
5. **Monitor Logs**: Check output for warnings/errors
6. **Test Thoroughly**: Test all app features after patching

---

For more details, see [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
