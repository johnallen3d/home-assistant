# AGENTS.md

## Project-Specific Details

### Connection Info
- **HA Server**: `root@homeassistant` (NOT `.local` - causes auth failures)
- **Server config path**: `/config/`
- **This repo**: READ-ONLY backup, never push changes back to server

### Just Task Runner Shortcuts
This project uses `just` as a task runner wrapper around SSH/scp commands.
See `Justfile` for all available commands. Common ones:

- `just sync` - Extract full config from server
- `just config::update-automation FILE.yaml` - Update single automation
- `just config::deploy` - Upload configuration.yaml and restart
- `just config::restart` - Restart HA core (required for helpers/integrations)
- `just --list` - Show all available commands

**Note:** `home-assistant-manager` skill covers the underlying SSH/scp patterns.
These `just` commands are convenience wrappers.

### ESPHome Device: M5Stack Atom S3 (tiny-button)
- **Location**: 192.168.0.87
- **Config**: `esphome/tiny-button.yaml`
- **Display**: 128x128 LCD (GC9107 chip, st7789v driver)
- **Button**: GPIO41 (single/double/long press detection)
- **Hardware requirements**:
  - Framework: `arduino` (not `esp-idf`)
  - Board: `m5stack-atoms3`
  - Display platform: `st7789v` with `CUSTOM` model
  - Display offsets: `offset_height: 3`, `offset_width: 1`
  - Pins: CLK=GPIO17, MOSI=GPIO21, CS=GPIO15, DC=GPIO33, RST=GPIO34, BL=GPIO16
- **Troubleshooting**: When adding new sensor types, do clean build:
  `rm -rf esphome/.esphome/build/tiny-button && cd esphome && just compile`
- **Features**:
  - Displays time, date, bathroom temp, outdoor temp
  - Sends button events to HA: `esphome.button_pressed` with `click_type` data

### Lovelace Dashboard Deployment
- **Dashboard files**: `config/.storage/lovelace.dashboard_*`
- **Dashboard registry**: `config/.storage/lovelace_dashboards`
- **Deploy command**: `scp ./config/.storage/lovelace.dashboard_<name> root@homeassistant:/config/.storage/`
- **After deploying changes**: Requires HA restart (`just config::restart`) - browser refresh alone is NOT sufficient
- **After registering new dashboard**: Also requires HA restart

### Custom Blueprints
- **Location**: `config/blueprints/automation/`
- **multi_click_button_controller.yaml**: Handles single/double/long press
  - Used by: Dad's bedroom button, kitchen button, living room Atom S3 button
  - Supports: Zigbee event buttons and ESPHome buttons
