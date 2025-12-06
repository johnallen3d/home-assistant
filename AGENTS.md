# AGENTS.md

## Available Tools

This project has three layers of Home Assistant tooling:

1. **Home Assistant MCP** (`home-assistant_ha_*`) - Direct API access to HA
   - CRUD for automations, scripts, scenes, dashboards, helpers
   - Entity state queries and service calls
   - History, statistics, and logbook access
   - Preferred for most read/write operations

2. **`home-assistant-manager` skill** - SSH/scp workflows and deployment patterns
   - Use for: config validation (`ha core check`), log analysis, rapid scp iteration
   - Covers: reload vs restart decisions, dashboard JSON debugging, template testing

3. **`just` commands** - Convenience wrappers (see `just --list`)
   - `just sync` - Extract full config from server
   - `just config::deploy` - Upload configuration.yaml and restart
   - `just config::restart` - Restart HA core

**Decision guide:**
- Query/modify entities, automations, dashboards → Use MCP tools
- Check config validity, view logs, rapid file deployment → Use skill (SSH/scp)
- Routine tasks with established patterns → Use `just` commands

## Floorplan

**Orientation:** All directions assume you're standing at the **front door facing in**.
- **Left** = Charlie's side
- **Right** = Dad's side  
- **Forward** = toward living room + balcony

### Layout

**Central Area (straight ahead):**
- **Entry** → **Kitchen** (island facing living room) → **Dining** → **Living Room** → **Balcony**

**Charlie's Side (left):**
- Charlie's Bedroom (with closet) + ensuite Bathroom
- Laundry between kitchen and Charlie's bathroom
- Mechanical/utility closet next to laundry

**Dad's Side (right):**
- Dad's Bedroom (primary, larger, big closet) + ensuite Bathroom (double vanity)

**Connectivity:**
- Entry → Kitchen → Dining → Living → Balcony (central spine)
- Kitchen → Laundry → Charlie's Bathroom → Charlie's Bedroom
- Dining/Living → Dad's Bedroom → Dad's Bathroom
- No shared bathrooms; Charlie's and Dad's suites do not connect to each other

### Lighting Context
- **TV location**: Living room, wall adjacent to Charlie's room (left wall)
- **Dad's chair**: Faces TV, adjacent to Dad's bedroom (right side)
- **Windows**: Large sliding glass door to the right of Dad's chair (balcony access)
- **Couch**: Divides living room from dining area, faces the glass doors (not the TV)
- **TV viewing preferences**: Living room light causes glare (to Dad's right); kitchen lights don't cause glare

## Project-Specific Details

### Connection Info
- **HA Server**: `root@homeassistant` (NOT `.local` - causes auth failures)
- **Server config path**: `/config/`
- **This repo**: READ-ONLY backup, never push changes back to server

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

### Custom Blueprints
- **Location**: `config/blueprints/automation/`
- **multi_click_button_controller.yaml**: Handles single/double/long press
  - Used by: Dad's bedroom button, kitchen button, living room Atom S3 button
  - Supports: Zigbee event buttons and ESPHome buttons

### Voice Assistant Exposed Entities
- **Config file**: `config/exposed_entities.yaml` - simple YAML list of entities to expose
- **Script**: `update_exposed_entities.py` - applies YAML config to entity registry
- **Critical**: HA must be **stopped** before modifying `core.entity_registry`
- **Commands**:
  - `just config::deploy-exposed` - Apply settings and restart HA
  - `just config::check-exposed` - Dry run, show what would change
- **Note**: Light groups may need `homeassistant.exposed_entities` for legacy handling
