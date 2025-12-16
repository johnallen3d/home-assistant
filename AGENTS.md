# AGENTS.md

## Todo List

Use `/todo` command for todo list queries. This queries `todo.ha_enhancements` (not the internal `todoread`/`todowrite` tools).

## Core Tenets

1. **Make changes locally** - Edit files in this repo, not in HA UI
2. **Push local changes to HA** - Use `just` commands or scp
3. **Reload HA when necessary** - Use MCP `ha_call_service` for reloads, or `just config::restart`
4. **Never make changes in HA UI** - For things managed here (automations, scripts, scenes, configuration.yaml)

## What We Manage Locally

| Type | Local File(s) | Deploy Command | Reload Command |
|------|---------------|----------------|----------------|
| Automations | `config/automations/*.yaml` | `just config::update-automation <file>` | auto |
| Scenes | `config/scenes/*.yaml` | `just config::update-scene <file>` | auto |
| Scripts | `config/scripts.yaml` | `just config::deploy-scripts` | `ha_call_service("script", "reload")` |
| Configuration | `config/configuration.yaml` | `just config::deploy` | restart required |
| Blueprints | `config/blueprints/` | `just config::upload-blueprint <file>` | `ha_call_service("automation", "reload")` |
| Dashboards | `config/.storage/lovelace.*` | `just config::deploy-dashboard <name>` | restart required |
| Exposed entities (voice) | `config/exposed_entities.yaml` | `just config::deploy-exposed` | restart required |
| Exposed entities (HomeKit) | `config/homekit_exposed.yaml` | `just config::deploy-homekit` | restart required |

**Defined in `configuration.yaml`** (deploy via `just config::deploy`):
- Light groups (`light:` section)
- Entity groups (`group:` section)  
- Input helpers (`input_number:`, `input_datetime:`, etc.)
- Template sensors (`template:` section)

**NOT managed locally** (OK to edit in HA UI):
- Integrations, devices, entities
- Areas, floors, labels
- Users, persons, zones
- HACS repositories

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
   - `just config::deploy` - Upload configuration.yaml and restart
   - `just config::restart` - Restart HA core

**Decision guide:**
- Query/modify entities, automations, dashboards → Use MCP tools
- Check config validity, view logs, rapid file deployment → Use skill (SSH/scp)
- Routine tasks with established patterns → Use `just` commands

### Known Issues

**`just config::update-automation` only updates existing automations.**  
For NEW automations, use MCP `ha_config_set_automation()` to create them first, then update the local YAML file with the generated `id` from the response. The `update-automation` command downloads the server's automation list and merges changes - it won't add automations that don't already exist on the server.

**`ha core reload-scripts` via SSH doesn't reliably reload new scripts.**  
After uploading scripts.yaml, use MCP `ha_call_service("script", "reload")` instead of SSH `ha core reload-scripts`. The SSH command may silently fail to pick up new script definitions.

### Renaming Scripts/Scenes/Entities Checklist

When renaming any script, scene, or entity that may be exposed to voice assistants or HomeKit:

1. **Update the entity definition** (e.g., `scripts.yaml`, `scenes/*.yaml`)
2. **Update all references** in automations that call the entity
3. **Update exposure configs** - these reference entities by ID:
   - `config/exposed_entities.yaml` - voice assistant (Assist)
   - `config/homekit_exposed.yaml` - HomeKit/Siri
4. **Deploy all changes** - scripts, automations, AND exposure configs

**The exposure configs are the primary reason for renaming** - they control what voice assistants can access. Forgetting to update them defeats the purpose of the rename.

### Automation/Script Update Checklist

After modifying automations that respond to physical triggers (buttons, sensors), **always verify**:

1. **Check the automation exists and is enabled:**
   ```
   ha_get_state("automation.xxx") → state should be "on"
   ```

2. **Test the script/action directly first:**
   ```
   ha_call_service("script", "turn_on", entity_id="script.xxx")
   ```
   Verify the expected state change occurred.

3. **Trigger a test event and check traces:**
   - Ask user to press the button
   - Check `ha_get_automation_traces()` for the new run
   - Verify `execution: finished` and no errors

4. **If automation fails silently:** The MCP `ha_config_set_automation` may mangle config. 
   Re-push and reload, or compare with a known-working automation.

**Do NOT mark an automation change as "done" until step 3 confirms it works end-to-end.**

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

### HomeKit Bridge Exposed Entities
- **Config file**: `config/homekit_exposed.yaml` - domain-based filter config
- **Script**: `update_homekit_entities.py` - applies YAML config to HomeKit config entry
- **Critical**: HA must be **stopped** before modifying `core.config_entries`
- **Model**: Unlike voice assistant (per-entity), HomeKit uses domain includes + entity excludes
- **Commands**:
  - `just config::deploy-homekit` - Apply settings and restart HA
  - `just config::check-homekit` - Dry run, show what would change
  - `just config::list-homekit-server` - Show current filter on server
- **Config structure**:
  ```yaml
  include_domains: [light, lock]  # expose all entities in these domains
  include_entities: [scene.x, script.y]  # add specific entities from other domains
  exclude_entities: [light.atom_echo_led]  # hide specific entities from included domains
  ```

### Adaptive Lighting System

**Location**: `config/configuration.yaml` (template sensors section)

**Key entities**:
- `sensor.adaptive_brightness` - brightness % based on sun elevation and time
- `sensor.adaptive_color_temp` - color temperature (K) based on sun elevation and time

**Brightness curve** (update this table if values change):

| Condition | Brightness |
|-----------|------------|
| Night (11pm-6am) | 20% |
| Sun below horizon (dusk/dawn) | 32% |
| Sun 0-15° elevation | 32% + (elevation × 1.6), so 32-56% |
| Sun above 15° | 56% + cloud boost (up to 80%) |

**Color temp curve**:

| Condition | Color Temp |
|-----------|------------|
| Night (11pm-6am) | 2200K |
| Sun below horizon | 2400K |
| Sun 0-15° elevation | 2400K + (elevation × 80), so 2400-3600K |
| Sun above 15° | 3600K-4500K |

**Usage**: Most lighting scripts call `script.lights` which reads these sensors.
Presence automations (kitchen, living room) also use these values.

**Tuning tips**:
- If lights feel too dim at dusk, increase the `sun_elev < 0` baseline
- If night mode is too dim, increase the `hour >= 23 or hour < 6` value
- The ramp multiplier (currently `× 2`) controls how quickly brightness increases with sun elevation
