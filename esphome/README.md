# ESPHome Local Development

## Setup Complete ✅

ESPHome CLI managed by uv with just recipes for common operations.

## Files

- `tiny-button.yaml` - Device configuration
- `secrets.yaml` - WiFi credentials (gitignored)
- `Justfile` - Task runner recipes
- `pyproject.toml` - Python dependencies managed by uv

## Quick Start

**1. Edit secrets.yaml** with your actual WiFi credentials:
```yaml
wifi_ssid: "YourActualSSID"
wifi_password: "YourActualPassword"
```

**2. See available commands:**
```bash
just
```

## Common Workflows

```bash
# Validate config
just validate

# Make changes, compile, and upload over WiFi
just run

# Just compile (check for errors)
just compile

# Upload without compiling
just upload

# View live logs
just logs

# Check device connectivity
just ping

# Clean build artifacts
just clean
```

## Typical Development Flow

1. Edit `tiny-button.yaml`
2. Run `just validate` to check syntax
3. Run `just run` to compile + upload + watch logs
4. Test your changes in Home Assistant

**No more web builder needed!** Everything happens locally over WiFi (OTA).

## Device Info

- Name: tiny-button
- IP: 192.168.0.87
- Board: ESP32-S3 (Atom S3)

## Python Environment

Dependencies are managed by uv:
```bash
# Install/update dependencies
just install

# Or manually
uv sync
```
