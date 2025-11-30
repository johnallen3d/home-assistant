# AGENTS.md

## ⛔️ CRITICAL: GIT OPERATIONS ARE STRICTLY FORBIDDEN ⛔️
**NEVER EVER run ANY git commands. NEVER EVER make commits. NEVER EVER stage files with git add.**
**This includes but is not limited to:**
- `git commit` (NEVER)
- `git add` (NEVER)
- `git push` (NEVER)
- `git rebase` (NEVER)
- `git merge` (NEVER)
- `git stash` (NEVER)
- `git tag` (NEVER)
- `git branch` (NEVER - except to READ current branch name)
- `git checkout` (NEVER - except to READ or discard local changes if explicitly requested)
- `git reset` (NEVER - except to discard local changes if explicitly requested)

**ONLY ALLOWED git commands (READ-ONLY):**
- `git status` - to check working directory state
- `git diff` - to view changes
- `git log` - to view history
- `git show` - to view commit details
- `git branch` (no arguments) - to view current branch

**User is responsible for ALL git operations including commits, staging, and pushing.**
**If you run ANY write operation with git, you have FAILED.**

## Project-Specific Details

### Connection Info
- **HA Server**: `root@homeassistant` (or `root@homeassistant.local`)
- **Server config path**: `/config/`
- **This repo**: READ-ONLY backup, never push changes back to server

### ESPHome Development
- Local ESPHome setup: `esphome/` directory with uv package manager
- Use `just` task runner for common commands (see `esphome/Justfile`)
- Validate config: `cd esphome && just validate`
- Compile firmware: `cd esphome && just compile`
- Upload via OTA: `cd esphome && just upload` (device IP: 192.168.0.87)
- View logs: `cd esphome && just logs`
- Clean build: `rm -rf esphome/.esphome/build/tiny-button && cd esphome && just compile`

### Just Recipes for Home Assistant Config
- **Sync all**: `just sync` - Run inventory and extract config
- **Extract config**: `just config::extract` or `just config::pull` - Download config from server and split into files
- **Upload config.yaml**: `just config::upload-config` - Upload configuration.yaml and re-sync
- **Update automation**: `just config::update-automation config/automations/FILE.yaml` - Update specific automation on server
- **Update multiple**: `just config::update-automations "config/automations/FILE1.yaml config/automations/FILE2.yaml"` - Update multiple automations
- **Create helper**: `just config::create-helper NAME "Display Name" MIN MAX STEP UNIT INITIAL` - Add input_number helper to config
  - Example: `just config::create-helper laundry_delay "Laundry Delay" 1 60 1 seconds 5`
  - IMPORTANT: After creating/modifying helpers in configuration.yaml, you MUST restart HA with `just config::restart`
- **Restart HA**: `just config::restart` - Restart Home Assistant core (30s wait)
- **Deploy config**: `just config::deploy` - Upload config and restart (use this for configuration.yaml changes)
- **Check status**: `just config::status` - Show HA server info
- **View logs**: `just config::logs` - Stream HA core logs
- **Backup**: `just config::backup` - Backup automations.yaml on server
- **Show info**: `just config::info` - Display config paths and file counts

### Important Notes on Configuration Changes
- **Automations/Scenes**: Can be updated without restart using `update-automation` (reloads automatically)
- **configuration.yaml changes** (helpers, integrations, etc.): Require full restart with `just config::restart` or `just config::deploy`
- **Best practice**: Use `just config::deploy` when making configuration.yaml changes to ensure restart happens

### Blueprint Management
- **Init blueprints**: `just config::init-blueprints` - Create local blueprints/automation directory
- **Upload blueprint**: `just config::upload-blueprint blueprints/automation/FILE.yaml` - Upload blueprint to server
- **Pull blueprints**: `just config::pull-blueprints` - Download all custom blueprints from server
- **Location**: Local blueprints stored in `config/blueprints/automation/`
- **Custom blueprint**: `multi_click_button_controller.yaml` - Handles single/double/long press for smart buttons
  - Used by: Dad's bedroom button, kitchen button, living room Atom S3 button
  - Supports both Zigbee event buttons and ESPHome buttons

## ESPHome Device: M5Stack Atom S3 (tiny-button)
- **Device**: M5Stack Atom S3 with 128x128 LCD display (GC9107 chip, st7789v driver)
- **Location**: 192.168.0.87
- **Config**: `esphome/tiny-button.yaml`
- **Features**:
  - Multi-click button (GPIO41): single, double, long press
  - 128x128 LCD display showing time, date, and temperatures
  - Pulls bathroom temperature from `sensor.bathroom_presence_sensor_temperature`
  - Pulls outdoor temperature from `weather.forecast_home` attribute
  - Sends button events to HA as `esphome.button_pressed` with `click_type` data
- **Display troubleshooting**:
  - Must use `arduino` framework (not `esp-idf`)
  - Board: `m5stack-atoms3` (not `esp32-s3-devkitc-1`)
  - Platform: `st7789v` with `CUSTOM` model
  - Offsets required: `offset_height: 3`, `offset_width: 1`
  - When adding new sensor types, do clean build: `rm -rf .esphome/build/tiny-button`
  - Pin configuration: CLK=GPIO17, MOSI=GPIO21, CS=GPIO15, DC=GPIO33, RST=GPIO34, BL=GPIO16

## Category Management via Browser Automation
- Categories are assigned via UI menu, not in YAML files
- Category assignment is available in the three-dot menu ("Assign category")
- Use Playwright browser automation to assign categories at scale
- Key workflow:
  1. Navigate to entity dashboard (`/config/automation/dashboard` or `/config/scene/dashboard`)
  2. Click entity to open it
  3. Click menu button (`button[aria-label="Menu"]`)
  4. Click "Assign category" menu item
  5. Interact with `ha-category-picker` element in dialog
  6. Select category from dropdown
  7. Click Save button in dialog (`ha-button:has-text("Save")` within dialog)
- IMPORTANT: Use `force=True` for clicks as `<ha-svg-icon>` often intercepts pointer events
- IMPORTANT: Find Save button within dialog element to avoid viewport issues
- Categories are stored in `/config/.storage/core.category_registry` (DO NOT EDIT DIRECTLY)
- Editing registry files directly will break Home Assistant - always use UI/API
