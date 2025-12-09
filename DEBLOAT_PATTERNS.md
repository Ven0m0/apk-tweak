# APK Debloating Pattern Reference

Comprehensive guide to debloating and minification patterns in apk-tweak.

## Overview

The pipeline supports two types of cleanup:
- **Debloat Patterns**: Remove unwanted code, libraries, and metadata
- **Minify Patterns**: Remove resource files to reduce APK size

All patterns use glob syntax and support wildcards (`*`, `**`, `?`).

---

## Debloat Patterns

### Ad Frameworks & Libraries

Remove advertising SDKs that bloat APKs and track users:

```json
"*/admob/*",           // Google AdMob
"*/google/ads/*",      // Google Ads SDK
"*/facebook/ads/*",    // Facebook Audience Network
"*/mopub/*",           // Twitter MoPub
"*/applovin/*",        // AppLovin MAX
"*/unity3d/ads/*",     // Unity Ads
"*/vungle/*",          // Vungle SDK
"*/chartboost/*",      // Chartboost
"*/inmobi/*",          // InMobi
"*/flurry/*",          // Yahoo Flurry
"assets/extensions/ads/*",    // Ad extension modules
"assets/extensions/search/*"  // Search extension modules
```

**Impact**: 2-15 MB saved, eliminates ad network trackers

---

### Analytics & Tracking

Remove telemetry, crash reporting, and user tracking:

```json
"*/analytics/*",                    // Generic analytics
"*/crashlytics/*",                  // Fabric Crashlytics
"*/firebase/analytics/*",           // Firebase Analytics
"*/firebase/crashlytics/*",         // Firebase Crashlytics
"*/google/firebase/analytics/*",    // Google Firebase Analytics
"*/adjust/*",                       // Adjust attribution
"*/branch/*",                       // Branch.io deep linking
"*/appsflyer/*",                    // AppsFlyer attribution
"*/kochava/*"                       // Kochava analytics
```

**Impact**: 1-8 MB saved, improved privacy

---

### License Files

Remove license and attribution files (legal review recommended):

```json
"LICENSE_UNICODE",       // Unicode license
"LICENSE_OFL",           // Open Font License
"LICENSE.txt",           // Generic licenses
"NOTICE.txt",            // Apache NOTICE files
"THIRD_PARTY_LICENSES",  // Third-party attributions
"*/licenses/*"           // License directories
```

**Impact**: 100 KB - 2 MB saved

**⚠️ Warning**: Removing licenses may violate open-source license terms. Only use for personal/testing purposes.

---

### Metadata & Build Artifacts

Remove Android build metadata and signature data:

```json
"META-INF/*",              // APK signatures (auto-regenerated on signing)
"car-app-api.level",       // Android Auto API level
"*.properties",            // Build properties
"*/build-data.properties"  // Build metadata
```

**Impact**: 500 KB - 5 MB saved

**⚠️ Note**: META-INF is regenerated during APK signing. Safe to remove pre-signing.

---

### Localization Data (Non-German/English)

Remove localization data for regions/languages you don't need:

#### Phone Number Libraries

```json
// Keep only German (DE) and US/UK data
"com/google/android/libraries/phonenumbers/data/PhoneNumberMetadataProto_A[CDEFGH]*",
"com/google/android/libraries/phonenumbers/data/PhoneNumberMetadataProto_[B-Z]*",
"com/google/android/libraries/phonenumbers/data/PhoneNumberAlternateFormatsProto_*"
```

#### Time Zone Data (Joda Time)

```json
"org/joda/time/format/messages_*.properties",  // Non-English messages
"org/joda/time/tz/data/Africa/*",              // African timezones
"org/joda/time/tz/data/America/*",             // American timezones
"org/joda/time/tz/data/Antarctica/*",          // Antarctic timezones
"org/joda/time/tz/data/Asia/*",                // Asian timezones
"org/joda/time/tz/data/Atlantic/*",            // Atlantic timezones
"org/joda/time/tz/data/Australia/*",           // Australian timezones
"org/joda/time/tz/data/Indian/*",              // Indian Ocean timezones
"org/joda/time/tz/data/Pacific/*"              // Pacific timezones
```

**Impact**: 500 KB - 3 MB saved

**Customization**: Adjust patterns to keep your locale. Example for German users:
```json
// Keep only Europe/Berlin timezone
"org/joda/time/tz/data/!(Europe)/*"
```

---

### Google Services Bloat

Remove Google Mobile Services (GMS) and Play Services code:

```json
"*/gms/*",                  // Google Mobile Services
"*/play/core/*",            // Google Play Core library
"*/android/gms/ads/*",      // GMS Ads
"*/android/gms/analytics/*" // GMS Analytics
```

**Impact**: 5-20 MB saved (if not using Play Services features)

**⚠️ Warning**: May break apps that rely on Google Play Services. Test thoroughly.

---

### Social SDK Bloat

Remove social media SDK integrations:

```json
"*/twitter/sdk/*",      // Twitter SDK (X)
"*/linkedin/platform/*",// LinkedIn SDK
"*/snapchat/kit/*"      // Snapchat Creative Kit
```

**Impact**: 1-5 MB saved per SDK

---

### Unused Assets

Remove debug, test, and unused asset directories:

```json
"assets/unused_*",  // Explicitly unused assets
"assets/debug/*",   // Debug-only assets
"assets/test/*"     // Test fixtures
```

**Impact**: Varies (1-10 MB)

---

## Minify Patterns

### High DPI Drawables

Remove extra-high-density graphics (most devices don't need xxxhdpi):

```json
"res/drawable-xxxhdpi/*",  // Extra-extra-extra-high DPI (640 dpi)
"res/drawable-xxhdpi/*"    // Extra-extra-high DPI (480 dpi)
```

**Impact**: 5-30 MB saved

**Trade-off**: Slight visual quality loss on 4K+ devices. Most users won't notice.

---

### Raw Media Files

Remove large audio/video files:

```json
// Audio
"res/raw/*.mp3",
"res/raw/*.wav",
"res/raw/*.ogg",
"res/raw/*.m4a",

// Video
"res/raw/*.mp4",
"res/raw/*.webm",
"assets/video/*"
```

**Impact**: 1-50 MB saved (highly variable)

**⚠️ Warning**: May break sound effects, music, or intro videos. Test app functionality.

---

### Large Image Assets

Remove non-essential image directories:

```json
"assets/kazoo/*",        // Kazoo music library assets
"assets/images/*.png",   // Generic image assets
"assets/images/*.jpg",
"assets/backgrounds/*",  // Background images
"assets/splash/*"        // Splash screens
```

**Impact**: 2-20 MB saved

---

### Fonts

Remove non-essential font weights:

```json
"res/font/*-bold.ttf",    // Bold variants
"res/font/*-light.ttf",   // Light variants
"assets/fonts/*-thin.ttf" // Thin variants
```

**Impact**: 500 KB - 3 MB saved

**Trade-off**: App may fall back to default system fonts.

---

### Unused Resources

Remove explicitly unused resource files:

```json
"res/raw/unused_*",
"assets/unused/*"
```

**Impact**: Varies

---

## Usage Examples

### Conservative (Safe)

Only remove ads, analytics, and licenses:

```json
{
  "debloat_patterns": [
    "*/admob/*",
    "*/google/ads/*",
    "*/analytics/*",
    "LICENSE_*"
  ],
  "minify_patterns": [
    "res/drawable-xxxhdpi/*"
  ]
}
```

---

### Moderate (Recommended)

Default configuration with good size reduction and low risk:

```json
{
  "revanced_debloat": true,
  "revanced_minify": true
}
```

Uses all patterns from `rvp/config.py` defaults.

---

### Aggressive (Maximum Size Reduction)

All patterns enabled + custom additions:

```json
{
  "debloat_patterns": [
    // All default patterns +
    "*/kotlin/**/*.kotlin_metadata",  // Kotlin metadata
    "*/kotlin/**/*.kotlin_builtins",  // Kotlin stdlib
    "assets/webkit/*",                // WebView assets
    "lib/*/libcrashlytics*"           // Native crash libs
  ],
  "minify_patterns": [
    // All default patterns +
    "res/drawable-xhdpi/*",           // High DPI (retain only hdpi/mdpi)
    "res/anim/*",                     // Animations
    "assets/sounds/*"                 // Sound effects
  ],
  "revanced_patch_ads": true          // Enable regex ad patching
}
```

**⚠️ Warning**: Thoroughly test APK functionality. May break features.

---

## Pattern Syntax

### Glob Wildcards

- `*` - Matches any characters within a path segment
- `**` - Matches any characters across path segments (recursive)
- `?` - Matches single character
- `[abc]` - Matches any character in set
- `[a-z]` - Matches any character in range
- `[!abc]` - Matches any character NOT in set

### Examples

```json
"*/ads/*"              // Match 'ads' at any depth
"**/com/google/ads/**" // Match 'com/google/ads' anywhere, recursively
"res/drawable-*hdpi/*" // Match all DPI variants (mdpi, hdpi, xhdpi, etc.)
"*.txt"                // Match all .txt files in root only
"**/*.txt"             // Match all .txt files recursively
"res/raw/*.mp[34]"     // Match .mp3 and .mp4 files
```

---

## Safety Guidelines

### Always Safe
✅ Ad frameworks (`*/ads/*`, `*/admob/*`)
✅ Analytics (`*/analytics/*`, `*/crashlytics/*`)
✅ xxxhdpi drawables (if not targeting 4K devices)
✅ Unused assets (`assets/unused/*`)

### Usually Safe
⚠️ License files (legal review recommended)
⚠️ META-INF (regenerated on signing)
⚠️ Properties files (`.properties`)
⚠️ Social SDKs (if app doesn't use them)

### Test Thoroughly
🚨 Google Play Services (`*/gms/*`) - may break core functionality
🚨 Localization data - verify app works in your locale
🚨 Media files - ensure sounds/videos still play
🚨 Fonts - check UI rendering

---

## Verification

After debloating, verify your APK:

```bash
# Check APK size reduction
ls -lh original.apk debloated.apk

# Decompile and inspect removed files
apktool d debloated.apk -o inspect/

# Test app functionality
adb install debloated.apk
# Run full app test suite
```

---

## Performance Impact

| Category | Size Saved | Risk Level | Test Priority |
|----------|------------|------------|---------------|
| Ads | 2-15 MB | Low | Medium |
| Analytics | 1-8 MB | Low | Low |
| Licenses | 0.1-2 MB | Low | Low |
| Localization | 0.5-3 MB | Medium | High |
| xxxhdpi | 5-30 MB | Low | Medium |
| Media | 1-50 MB | High | Critical |
| GMS | 5-20 MB | High | Critical |

---

## Customization Tips

### App-Specific Patterns

Create custom configs for specific apps:

**YouTube**:
```json
"debloat_patterns": [
  "*/youtube/ads/*",
  "*/youtube/analytics/*",
  "assets/youtube/backgrounds/*"
]
```

**Spotify**:
```json
"debloat_patterns": [
  "*/spotify/ads/*",
  "*/spotify/partner-ads/*"
]
```

### Conditional Patterns

Use separate configs for different use cases:

- `config-minimal.json` - Only remove ads
- `config-standard.json` - Default patterns
- `config-aggressive.json` - Maximum reduction

---

## Tools Integration

### With DTL-X Engine

```bash
./bin/rvp app.apk -e dtlx --dtlx-optimize
```

DTL-X provides additional optimization:
- `--rmads4` - Remove ad loaders
- `--rmtrackers` - Remove tracker code
- `--rmnop` - Remove NOP instructions

### With ReVanced Engine

```bash
./bin/rvp youtube.apk -e revanced \
  --config examples/advanced-revanced-config.json
```

Combines ReVanced patches with debloating.

---

## Contributing

Have new debloat patterns? Submit them via PR:

1. Add pattern to `rvp/config.py`
2. Document in this file (category + impact)
3. Test on 3+ different APKs
4. Include before/after size measurements

---

## References

- [Android App Bundle Documentation](https://developer.android.com/guide/app-bundle)
- [APKTool Documentation](https://ibotpeaches.github.io/Apktool/)
- [DTL-X Repository](https://github.com/Gameye98/DTL-X)
- [ReVanced Documentation](https://github.com/revanced/revanced-cli)

---

_Last updated: 2025-12-09_
