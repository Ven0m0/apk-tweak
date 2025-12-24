# Pipeline Configuration Files

Ready-to-use pipeline configurations for different use cases.

## Available Configurations

### simple_pipeline.json

Basic single-engine configuration for quick ReVanced patching.

**Usage:**

```bash
./bin/rvp youtube.apk --config config/simple_pipeline.json
```

### full_pipeline.json

Complete production pipeline with multiple engines and plugins.

**Features:**

- Pre-analysis with DTL-X
- Media optimization
- ReVanced patching
- Optional LSPatch/Magisk
- Logging and metrics

**Usage:**

```bash
./bin/rvp youtube.apk --config config/full_pipeline.json -o output/
```

### development_pipeline.json

Development/testing configuration with verbose logging and no cleanup.

**Usage:**

```bash
./bin/rvp test.apk --config config/development_pipeline.json
```

## Configuration Structure

### Top-Level Fields

```json
{
  "version": "1.0",           // Config format version
  "description": "...",       // Human-readable description
  "input": null,              // Default input (null = from CLI)
  "output_dir": "output",     // Default output directory
  "engines": [...],           // Engine configuration array
  "plugins": [...],           // Plugin names to load
  "global_options": {...},    // Pipeline-wide settings
  "hooks": {...},             // Custom hook scripts (optional)
  "notifications": {...}      // Notification settings (optional)
}
```

### Engine Configuration

```json
{
  "name": "revanced",         // Engine identifier
  "enabled": true,            // Enable/disable without removing
  "options": {                // Engine-specific options
    "patches": ["all"],
    "integrations": true,
    ...
  }
}
```

### Global Options

```json
{
  "verbose": true, // Verbose output
  "debug": false, // Debug mode
  "cleanup": true, // Remove temp files
  "cleanup_on_error": false, // Cleanup even on failure
  "temp_dir": "/tmp/rvp", // Temporary working directory
  "parallel_processing": false, // Run engines in parallel (experimental)
  "timeout": 3600, // Max execution time (seconds)
  "retry_on_failure": true, // Retry failed engines
  "max_retries": 3 // Maximum retry attempts
}
```

## Customization

Copy and modify any configuration:

```bash
cp config/full_pipeline.json config/my_custom.json
${EDITOR} config/my_custom.json
./bin/rvp input.apk --config config/my_custom.json
```

### Engine Options

```json
{
  "engines": [
    {
      "name": "revanced",
      "enabled": true,
      "options": {
        // Only patch ads, no other modifications
        "patches": ["video-ads", "general-ads"],
        "exclude_patches": [],
        "integrations": true,

        // Use custom patch files
        "patches_path": "/path/to/custom-patches.jar",

        // Custom keystore for signing
        "keystore": "~/.android/release.keystore"
      }
    }
  ]
}
```

### Enable/Disable Engines

```json
{
  "engines": [
    {"name": "dtlx", "enabled": true, ...},        // ✓ Will run
    {"name": "revanced", "enabled": true, ...},    // ✓ Will run
    {"name": "lspatch", "enabled": false, ...},    // ✗ Will skip
    {"name": "magisk", "enabled": false, ...}      // ✗ Will skip
  ]
}
```

### Add Plugins

```json
{
  "plugins": [
    "logging", // Comprehensive logging
    "metrics", // Performance metrics
    "validation", // Input/output validation
    "notification" // Build notifications
  ]
}
```

### Configure Notifications

```json
{
  "notifications": {
    "enabled": true,
    "telegram": {
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID"
    },
    "webhook": {
      "url": "https://your-webhook.com/endpoint",
      "method": "POST"
    }
  }
}
```

## Environment Variable Substitution

Configuration files support environment variable substitution:

```json
{
  "engines": [
    {
      "name": "revanced",
      "options": {
        "cli_path": "${REVANCED_CLI_PATH}",
        "keystore": "${ANDROID_KEYSTORE}"
      }
    }
  ],
  "global_options": {
    "temp_dir": "${TMPDIR:-/tmp/rvp}"
  }
}
```

Set variables before running:

```bash
export REVANCED_CLI_PATH=/opt/revanced/cli.jar
export ANDROID_KEYSTORE=~/.android/release.keystore

./bin/rvp app.apk --config config/my_pipeline.json
```

## Validation

Validate configuration before running:

```bash
# Using Python module directly
python3 -m rvp.cli --validate-config config/my_pipeline.json

# Using wrapper script
./bin/rvp --validate-config config/my_pipeline.json
```

## Best Practices

1. **Version Control**: Keep configurations in git
2. **Naming Convention**: Use descriptive names (e.g., `youtube_minimal.json`)
3. **Comments**: Use `description` field for documentation
4. **Secrets**: Never commit tokens/passwords; use environment variables
5. **Testing**: Test new configurations with `development_pipeline.json` first
6. **Backups**: Keep working configurations as templates
7. **Validation**: Always validate before production use

## Troubleshooting

### Configuration Not Loading

```bash
# Check JSON syntax
jq . config/my_pipeline.json

# Validate against schema
./bin/rvp --validate-config config/my_pipeline.json
```

### Engine Not Running

- Check `"enabled": true` is set
- Verify engine name matches registered engines
- Check engine-specific options are valid

### Options Not Applied

- Ensure options are in correct engine block
- Check option names match engine expectations
- Verify paths exist and are accessible

## See Also

- [CLAUDE.md](../CLAUDE.md) - Full development guide
