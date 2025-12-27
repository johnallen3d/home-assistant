# Home Assistant

## Access

### Network

via tailscale, hostname: `homeassistant`
via ip address, `192.168.0.182`
port: `8123`

### SSH

```bash
ssh root@homeassistant
```

### CLI

accessible via SSH

```bash
ssh root@homeassistant "ha --help"
```

## Commands

This repository uses [just](https://github.com/casey/just) as a command runner.

### Home Assistant

- `just config::extract` - Download YAML config files (automations, scenes, configuration)
- `just sync` - Alias for config extraction

### ESPHome

- `just esphome validate` - Validate YAML configuration
- `just esphome compile` - Compile firmware
- `just esphome upload` - Upload firmware via OTA
- `just esphome run` - Compile, upload, and stream logs
- `just esphome logs` - Stream logs from device
- `just esphome clean` - Clean build artifacts
- `just esphome info` - Show device info

Running `just` with no arguments lists all available commands. You can also run `just esphome` to list ESPHome-specific commands.

## Scripts

Scripts are organized in their respective directories:

- `./config/extract.sh` - Downloads YAML config files from HA server
