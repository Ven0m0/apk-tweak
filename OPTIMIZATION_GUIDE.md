# APK Optimization Guide

This guide explains how to use the advanced APK optimization features in RVP.

## Overview

RVP now supports comprehensive APK optimization including:

- **Multi-Patch Support**: Apply multiple ReVanced patch bundles sequentially
- **Debloating**: Remove ads, analytics, and bloatware
- **Minification**: Remove unnecessary resources
- **Optimization**: Zipalign and optimize APK structure

## Quick Example

```json
{
  "input_apk": "youtube.apk",
  "output_dir": "optimized",
  "engines": ["revanced"],
  
  "revanced_cli_path": "tools/revanced-cli.jar",
  "revanced_patch_bundles": [
    "tools/revanced-patches-official.jar",
    "tools/revanced-patches-extended.jar"
  ],
  "revanced_integrations_path": "tools/revanced-integrations.apk",
  
  "revanced_optimize": true,
  "revanced_debloat": true,
  "revanced_minify": true
}
```

## Multi-Patch Support

### Why Multiple Patch Bundles?

Different patch bundles may provide:
- Official ReVanced patches
- Extended patches with additional features
- Custom patches for specific needs
- Community patches

### Configuration

```json
{
  "revanced_patch_bundles": [
    "patches/official-v2.1.jar",
    "patches/extended-v1.5.jar",
    "patches/custom-youtube.jar"
  ]
}
```

Patches are applied **sequentially** in the order specified. Each patch bundle modifies the APK produced by the previous one.

### Patch Selection

Include only specific patches:

```json
{
  "revanced_include_patches": [
    "hide-ads",
    "custom-branding",
    "premium-heading",
    "sponsorblock"
  ]
}
```

Exclude unwanted patches:

```json
{
  "revanced_exclude_patches": [
    "swipe-controls",
    "experimental-feature"
  ]
}
```

## Debloating

### What Gets Removed?

Debloating removes unwanted code and assets from your APK:

- Advertisement SDKs (AdMob, Facebook Ads, etc.)
- Analytics and tracking (Google Analytics, Crashlytics, etc.)
- Telemetry modules
- Unused features

### Default Debloat Patterns

```json
{
  "debloat_patterns": [
    "*/admob/*",
    "*/google/ads/*",
    "*/facebook/ads/*",
    "*/analytics/*",
    "*/crashlytics/*",
    "*/firebase/analytics/*"
  ]
}
```

### Custom Debloat Patterns

Add your own patterns using glob syntax:

```json
{
  "debloat_patterns": [
    "**/admob",              
    "com/unity3d/ads/*",     
    "*/tracking/**",         
    "assets/unused_*",       
    "lib/*/libadmob.so"      
  ]
}
```

**Pattern Syntax:**
- `*` - Matches any characters except `/`
- `**` - Matches any characters including `/`
- `?` - Matches single character
- `[abc]` - Matches any character in brackets

### Disable Debloating

```json
{
  "revanced_debloat": false
}
```

## Resource Minification

### What Gets Minified?

Remove unnecessary resources to reduce APK size:

- Extra-high DPI drawables (xxxhdpi, xxhdpi)
- Large audio files (MP3, WAV, OGG)
- Unused assets
- Redundant language resources

### Default Minify Patterns

```json
{
  "minify_patterns": [
    "res/drawable-xxxhdpi/*",
    "res/raw/*.mp3",
    "res/raw/*.wav"
  ]
}
```

### Custom Minification

```json
{
  "minify_patterns": [
    "res/drawable-xxxhdpi/*",
    "res/drawable-xxhdpi/*",
    "res/raw/*.mp3",
    "res/raw/*.ogg",
    "assets/videos/*.mp4",
    "res/values-de/*",
    "res/values-fr/*"
  ]
}
```

**Size Reduction Examples:**
- Removing xxxhdpi: 10-30% size reduction
- Removing audio: 5-20% size reduction
- Removing unused languages: 5-15% size reduction

### Disable Minification

```json
{
  "revanced_minify": false
}
```

## Complete Optimization Pipeline

The optimization process follows these steps:

### 1. Patching Phase

```
Input APK → Patch Bundle 1 → Patch Bundle 2 → ... → Patched APK
```

Each patch bundle is applied sequentially using ReVanced CLI.

### 2. Optimization Phase

```
Patched APK
    ↓
Decompile (apktool d)
    ↓
Debloat (remove bloatware)
    ↓
Minify (remove unused resources)
    ↓
Recompile (apktool b)
    ↓
Zipalign (optimize alignment)
    ↓
Optimized APK
```

### Full Configuration Example

```json
{
  "input_apk": "youtube.apk",
  "output_dir": "output",
  "engines": ["revanced"],
  
  "revanced_cli_path": "tools/revanced-cli.jar",
  "revanced_patch_bundles": [
    "tools/revanced-patches-official.jar",
    "tools/revanced-patches-extended.jar"
  ],
  "revanced_integrations_path": "tools/revanced-integrations.apk",
  
  "revanced_optimize": true,
  "revanced_debloat": true,
  "revanced_minify": true,
  
  "revanced_include_patches": [
    "hide-ads",
    "custom-branding"
  ],
  
  "debloat_patterns": [
    "*/admob/*",
    "*/google/ads/*",
    "*/analytics/*",
    "*/crashlytics/*",
    "*/firebase/analytics/*",
    "com/unity3d/ads/*"
  ],
  
  "minify_patterns": [
    "res/drawable-xxxhdpi/*",
    "res/drawable-xxhdpi/*",
    "res/raw/*.mp3",
    "res/raw/*.wav",
    "res/raw/*.ogg",
    "assets/unused_*"
  ],
  
  "apktool_path": "tools/apktool.jar",
  "zipalign_path": "tools/zipalign"
}
```

## Tool Requirements

### Required Tools

1. **ReVanced CLI** (`revanced-cli.jar`)
   - Download: https://github.com/revanced/revanced-cli/releases
   - Java 11+ required

2. **Patch Bundles** (`.jar` files)
   - Official: https://github.com/revanced/revanced-patches/releases
   - Extended: https://github.com/inotia00/revanced-patches/releases

3. **ReVanced Integrations** (`integrations.apk`)
   - Download: https://github.com/revanced/revanced-integrations/releases

4. **apktool** (for optimization)
   - Download: https://ibotpeaches.github.io/Apktool/
   - Java runtime required

5. **zipalign** (part of Android SDK)
   - Included in Android SDK build-tools
   - Path: `$ANDROID_HOME/build-tools/<version>/zipalign`

### Optional Tools

- **aapt2**: Advanced APK optimization (future feature)

### Tool Installation Example

```bash
# Create tools directory
mkdir -p tools && cd tools

# Download ReVanced CLI
wget https://github.com/revanced/revanced-cli/releases/latest/download/revanced-cli.jar

# Download patches
wget https://github.com/revanced/revanced-patches/releases/latest/download/revanced-patches.jar

# Download integrations
wget https://github.com/revanced/revanced-integrations/releases/latest/download/revanced-integrations.apk

# Download apktool
wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool
wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar -O apktool.jar
chmod +x apktool

# Zipalign (from Android SDK)
# Install Android SDK, then:
# export PATH=$PATH:$ANDROID_HOME/build-tools/34.0.0
```

## Performance Considerations

### Speed vs Size Trade-off

- **Patching Only**: Fast, no size reduction
- **Patching + Debloat**: Medium speed, 10-30% size reduction
- **Full Optimization**: Slower, 20-50% size reduction

### Optimization Times

For a 100MB APK:
- Patching: 30-60 seconds
- Debloating: 10-20 seconds  
- Minification: 5-15 seconds
- Recompilation: 60-120 seconds
- Zipalign: 5-10 seconds

**Total**: 2-4 minutes for full optimization

### Disable Optimization for Testing

```json
{
  "revanced_optimize": false
}
```

This skips debloat/minify/zipalign and only applies patches (much faster).

## Troubleshooting

### APK Won't Install

1. **Sign the APK**: Optimized APKs need to be signed
   ```bash
   apksigner sign --ks keystore.jks output.apk
   ```

2. **Check AndroidManifest.xml**: Ensure no critical elements were removed

### App Crashes After Optimization

1. **Reduce debloat patterns**: Some patterns may remove required code
2. **Disable minification**: Test without minification first
3. **Check logs**: Use `adb logcat` to see crash details

### Large APK Size

If APK isn't getting smaller:
1. Check which resources are actually in the APK
2. Adjust minify_patterns to target larger files
3. Consider removing entire feature modules

### Tools Not Found

```bash
# Check tool paths
which apktool
which zipalign

# Or specify full paths in config
{
  "apktool_path": "/usr/local/bin/apktool",
  "zipalign_path": "/home/user/Android/Sdk/build-tools/34.0.0/zipalign"
}
```

## Best Practices

1. **Test Incrementally**: Start with patches only, then add optimizations
2. **Keep Backups**: Always keep original APK
3. **Version Control Config**: Track your config.json in git
4. **Monitor Size**: Check APK size before/after
5. **Test Thoroughly**: Test all app features after optimization
6. **Use CI/CD**: Automate the pipeline for reproducibility

## Examples

See the `examples/` directory for:
- `advanced-revanced-config.json` - Complete configuration
- `basic-config.json` - Simple patching only
- `full-pipeline-config.json` - Multi-engine pipeline

## Future Enhancements

Planned features:
- [ ] Automatic signature/alignment
- [ ] Resource shrinking with aapt2
- [ ] Dex optimization
- [ ] ProGuard/R8 integration
- [ ] Resource deduplication
- [ ] Automatic language selection

---

For more information, see the main README.md or open an issue on GitHub.
