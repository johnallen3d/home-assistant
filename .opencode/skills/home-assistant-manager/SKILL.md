---
name: home-assistant-manager
description: Expert-level Home Assistant configuration management with efficient deployment workflows (rapid scp iteration), MCP server integration, automation verification protocols, log analysis, reload vs restart optimization, and comprehensive Lovelace dashboard management for tablet-optimized UIs. Includes template patterns, card types, debugging strategies, and real-world examples. CRITICAL - Never use git write operations (commit/add/push).
---

# Home Assistant Manager

Expert-level Home Assistant configuration management with efficient workflows, MCP server integration, and verification protocols.

**⛔️ CRITICAL: Never use git write operations (commit, add, push, merge, rebase) - user handles all git operations.**

## Core Capabilities

- Remote Home Assistant instance management via SSH and MCP server
- Smart deployment workflows (git-based and rapid iteration)
- Configuration validation and safety checks
- Automation testing and verification
- Log analysis and error detection
- Reload vs restart optimization
- Lovelace dashboard development and optimization
- Template syntax patterns and debugging
- Tablet-optimized UI design

## Prerequisites

Before starting, verify the environment has:

1. SSH access to Home Assistant instance (`root@homeassistant.local`)
2. Home Assistant MCP server tools available
3. Git repository connected to HA `/config` directory
4. Context7 MCP server with Home Assistant docs (recommended)

**Note:** Projects may use task runners like `just` or `make` as wrappers around these SSH/scp commands. Check for `Justfile` or `Makefile` in the project root for convenience shortcuts.

## Remote Access Patterns

### Using MCP Server Tools

The skill uses Home Assistant MCP server tools for API operations:

```python
# Get entity state
ha_get_state(entity_id="sensor.temperature")

# Call services
ha_call_service(domain="automation", service="reload")
ha_call_service(domain="automation", service="trigger", entity_id="automation.name")

# List entities
ha_get_overview()
```

### Using SSH for HA Management

```bash
# Check configuration validity
ssh root@homeassistant.local "ha core check"

# Restart Home Assistant
ssh root@homeassistant.local "ha core restart"

# View logs
ssh root@homeassistant.local "ha core logs"

# Tail logs with grep
ssh root@homeassistant.local "ha core logs | grep -i error | tail -20"
```

## Deployment Workflows

### Standard Workflow (After User Commits)

After user commits and pushes to version control:

```bash
# 1. Make changes locally
# 2. Check validity
ssh root@homeassistant.local "ha core check"

# 3. USER commits and pushes (not agent)

# 4. CRITICAL: Pull to HA instance
ssh root@homeassistant.local "cd /config && git pull"

# 5. Reload or restart
ha_call_service(domain="automation", service="reload")  # if reload sufficient
# OR
ssh root@homeassistant.local "ha core restart"  # if restart needed

# 6. Verify
ha_get_state(entity_id="sensor.new_entity")
ssh root@homeassistant.local "ha core logs | grep -i error | tail -20"
```

### Rapid Development Workflow (Testing/Iteration)

Use `scp` for quick testing before user commits:

```bash
# 1. Make changes locally
# 2. Quick deploy
scp automations.yaml root@homeassistant.local:/config/

# 3. Reload/restart
ha_call_service(domain="automation", service="reload")

# 4. Test and iterate (repeat 1-3 as needed)

# 5. Once finalized, USER commits to git
```

**When to use scp:**

- 🚀 Rapid iteration and testing
- 🔄 Frequent small adjustments
- 🧪 Experimental changes
- 🎨 UI/Dashboard work

**After testing, user commits final versions**

## Reload vs Restart Decision Making

**ALWAYS assess if reload is sufficient before requiring a full restart.**

### Can be reloaded (fast, preferred)

- ✅ Automations: `ha_call_service(domain="automation", service="reload")`
- ✅ Scripts: `ha_call_service(domain="script", service="reload")`
- ✅ Scenes: `ha_call_service(domain="scene", service="reload")`
- ✅ Template entities: `ha_call_service(domain="template", service="reload")`
- ✅ Groups: `ha_call_service(domain="group", service="reload")`
- ✅ Themes: `ha_call_service(domain="frontend", service="reload_themes")`

### Require full restart

- ❌ Min/Max sensors and platform-based sensors
- ❌ New integrations in configuration.yaml
- ❌ Core configuration changes
- ❌ MQTT sensor/binary_sensor platforms

## Automation Verification Workflow

**ALWAYS verify automations after deployment:**

### Step 1: Deploy

```bash
# User commits changes, then agent pulls:
ssh root@homeassistant.local "cd /config && git pull"
```

### Step 2: Check Configuration

```bash
ssh root@homeassistant.local "ha core check"
```

### Step 3: Reload

```bash
ha_call_service(domain="automation", service="reload")
```

### Step 4: Manually Trigger

```bash
ha_call_service(domain="automation", service="trigger", entity_id="automation.name")
```

**Why trigger manually?**

- Instant feedback (don't wait for scheduled triggers)
- Verify logic before production
- Catch errors immediately

### Step 5: Check Logs

```bash
sleep 3
ssh root@homeassistant.local "ha core logs | grep -i 'automation_name' | tail -20"
```

**Success indicators:**

- `Initialized trigger AutomationName`
- `Running automation actions`
- `Executing step ...`
- No ERROR or WARNING messages

**Error indicators:**

- `Error executing script`
- `Invalid data for call_service`
- `TypeError`, `Template variable warning`

### Step 6: Verify Outcome

**For notifications:**

- Ask user if they received it
- Check logs for mobile_app messages

**For device control:**

```bash
ha_get_state(entity_id="switch.device_name")
```

**For sensors:**

```bash
ha_get_state(entity_id="sensor.new_sensor")
```

### Step 7: Fix and Re-test if Needed

If errors found:

1. Identify root cause from error messages
2. Fix the issue
3. Re-deploy (steps 1-2)
4. Re-verify (steps 3-6)

## Dashboard Management

### Dashboard Fundamentals

**What are Lovelace Dashboards?**

- JSON files in `.storage/` directory (e.g., `.storage/lovelace.control_center`)
- UI configuration for Home Assistant frontend
- Optimizable for different devices (mobile, tablet, wall panels)

**Critical Understanding:**

- Creating dashboard file is NOT enough - must register in `.storage/lovelace_dashboards`
- **Dashboard changes REQUIRE HA restart** - browser refresh alone is NOT sufficient
- Use panel view for full-screen content (maps, cameras)
- Use sections view for organized multi-card layouts

### Dashboard Development Workflow

**Rapid Iteration with scp (Recommended for dashboards):**

```bash
# 1. Make changes locally
vim .storage/lovelace.control_center

# 2. Deploy immediately (no git commit yet)
scp .storage/lovelace.control_center root@homeassistant.local:/config/.storage/

# 3. Restart HA (required for dashboard changes to take effect)
ssh root@homeassistant.local "ha core restart"

# 4. After restart, hard refresh browser (Ctrl+F5 or Cmd+Shift+R)

# 5. Iterate: Repeat 1-4 until perfect

# 6. When stable, USER commits to git
ssh root@homeassistant.local "cd /config && git pull"
```

**Why scp for dashboards:**

- Quick deploy without git commits
- Iterate on visual changes
- Commit only stable versions
- Note: Each change requires HA restart to take effect

### Creating New Dashboard

**Complete workflow:**

```bash
# Step 1: Create dashboard file
cp .storage/lovelace.my_home .storage/lovelace.new_dashboard

# Step 2: Register in lovelace_dashboards
# Edit .storage/lovelace_dashboards to add:
{
  "id": "new_dashboard",
  "show_in_sidebar": true,
  "icon": "mdi:tablet-dashboard",
  "title": "New Dashboard",
  "require_admin": false,
  "mode": "storage",
  "url_path": "new-dashboard"
}

# Step 3: Deploy both files
scp .storage/lovelace.new_dashboard root@homeassistant.local:/config/.storage/
scp .storage/lovelace_dashboards root@homeassistant.local:/config/.storage/

# Step 4: Restart HA (required for registry changes)
ssh root@homeassistant.local "ha core restart"
sleep 30

# Step 5: Verify appears in sidebar
```

**Update .gitignore to track:**

```gitignore
# Exclude .storage/ by default
.storage/

# Include dashboard files
!.storage/lovelace.new_dashboard
!.storage/lovelace_dashboards
```

### View Types Decision Matrix

**Use Panel View when:**

- Displaying full-screen map (vacuum, cameras)
- Single large card needs full width
- Want zero margins/padding
- Minimize scrolling

**Use Sections View when:**

- Organizing multiple cards
- Need responsive grid layout
- Building multi-section dashboards

**Layout Example:**

```json
// Panel view - full width, no margins
{
  "type": "panel",
  "title": "Vacuum Map",
  "path": "map",
  "cards": [
    {
      "type": "custom:xiaomi-vacuum-map-card",
      "entity": "vacuum.dusty"
    }
  ]
}

// Sections view - organized, has ~10% margins
{
  "type": "sections",
  "title": "Home",
  "sections": [
    {
      "type": "grid",
      "cards": [...]
    }
  ]
}
```

### Card Types Quick Reference

**Mushroom Cards (Modern, Touch-Optimized):**

```json
{
  "type": "custom:mushroom-light-card",
  "entity": "light.living_room",
  "use_light_color": true,
  "show_brightness_control": true,
  "collapsible_controls": true,
  "fill_container": true
}
```

- Best for tablets and touch screens
- Animated, colorful icons
- Built-in slider controls

**Mushroom Template Card (Dynamic Content):**

```json
{
  "type": "custom:mushroom-template-card",
  "primary": "All Doors",
  "secondary": "{% set sensors = ['binary_sensor.front_door'] %}\n{% set open = sensors | select('is_state', 'on') | list | length %}\n{{ open }} / {{ sensors | length }} open",
  "icon": "mdi:door",
  "icon_color": "{% if open > 0 %}red{% else %}green{% endif %}"
}
```

- Use Jinja2 templates for dynamic content
- Color-code status with icon_color
- Multi-line templates use `\n` in JSON

**Tile Card (Built-in, Modern):**

```json
{
  "type": "tile",
  "entity": "climate.thermostat",
  "features": [
    {
      "type": "climate-hvac-modes",
      "hvac_modes": ["heat", "cool", "fan_only", "off"]
    },
    { "type": "target-temperature" }
  ]
}
```

- No custom cards required
- Built-in features for controls

### Common Template Patterns

**Counting Open Doors:**

```jinja2
{% set door_sensors = [
  'binary_sensor.front_door',
  'binary_sensor.back_door'
] %}
{% set open = door_sensors | select('is_state', 'on') | list | length %}
{{ open }} / {{ door_sensors | length }} open
```

**Color-Coded Days Until:**

```jinja2
{% set days = state_attr('sensor.bin_collection', 'daysTo') | int %}
{% if days <= 1 %}red
{% elif days <= 3 %}amber
{% elif days <= 7 %}yellow
{% else %}grey
{% endif %}
```

**Conditional Display:**

```jinja2
{% set bins = [] %}
{% if days and days | int <= 7 %}
  {% set bins = bins + ['Recycling'] %}
{% endif %}
{% if bins %}This week: {{ bins | join(', ') }}{% else %}None this week{% endif %}
```

**IMPORTANT:** Always use `| int` or `| float` to avoid type errors when comparing

### Tablet Optimization

**Screen-specific layouts:**

- 11-inch tablets: 3-4 columns
- Touch targets: minimum 44x44px
- Minimize scrolling: Use panel view for full-screen
- Visual feedback: Color-coded status (red/green/amber)

**Grid Layout for Tablets:**

```json
{
  "type": "grid",
  "columns": 3,
  "square": false,
  "cards": [
    { "type": "custom:mushroom-light-card", "entity": "light.living_room" },
    { "type": "custom:mushroom-light-card", "entity": "light.bedroom" }
  ]
}
```

### Common Dashboard Pitfalls

**Problem 1: Dashboard Not in Sidebar**

- **Cause:** File created but not registered
- **Fix:** Add to `.storage/lovelace_dashboards` and restart HA

**Problem 2: "Configuration Error" in Card**

- **Cause:** Custom card not installed, wrong syntax, template error
- **Fix:**
  - Check HACS for card installation
  - Check browser console (F12) for details
  - Test templates in Developer Tools → Template

**Problem 3: Auto-Entities Fails**

- **Cause:** `card_param` not supported by card type
- **Fix:** Use cards that accept `entities` parameter:
  - ✅ Works: `entities`, `vertical-stack`, `horizontal-stack`
  - ❌ Doesn't work: `grid`, `glance` (without specific syntax)

**Problem 4: Vacuum Map Has Margins/Scrolling**

- **Cause:** Using sections view (has margins)
- **Fix:** Use panel view for full-width, no scrolling

**Problem 5: Template Type Errors**

- **Error:** `TypeError: '<' not supported between instances of 'str' and 'int'`
- **Fix:** Use type filters: `states('sensor.days') | int < 7`

### Dashboard Debugging

**1. Browser Console (F12):**

- Check for red errors when loading dashboard
- Common: "Custom element doesn't exist" → Card not installed

**2. Validate JSON Syntax:**

```bash
python3 -m json.tool .storage/lovelace.control_center > /dev/null
```

**3. Test Templates:**

```
Home Assistant → Developer Tools → Template
Paste template to test before adding to dashboard
```

**4. Verify Entities:**

```bash
ha_get_state(entity_id="binary_sensor.front_door")
```

**5. Clear Browser Cache:**

- Hard refresh: Ctrl+F5 or Cmd+Shift+R
- Try incognito window

## Real-World Examples

### Quick Controls Dashboard Section

```json
{
  "type": "grid",
  "title": "Quick Controls",
  "cards": [
    {
      "type": "custom:mushroom-template-card",
      "primary": "All Doors",
      "secondary": "{% set doors = ['binary_sensor.front_door', 'binary_sensor.back_door'] %}\n{% set open = doors | select('is_state', 'on') | list | length %}\n{{ open }} / {{ doors | length }} open",
      "icon": "mdi:door",
      "icon_color": "{% if open > 0 %}red{% else %}green{% endif %}"
    },
    {
      "type": "tile",
      "entity": "climate.thermostat",
      "features": [
        {
          "type": "climate-hvac-modes",
          "hvac_modes": ["heat", "cool", "fan_only", "off"]
        },
        { "type": "target-temperature" }
      ]
    }
  ]
}
```

### Individual Light Cards (Touch-Friendly)

```json
{
  "type": "grid",
  "title": "Lights",
  "columns": 3,
  "cards": [
    {
      "type": "custom:mushroom-light-card",
      "entity": "light.office_studio",
      "name": "Office",
      "use_light_color": true,
      "show_brightness_control": true,
      "collapsible_controls": true
    }
  ]
}
```

### Full-Screen Vacuum Map

```json
{
  "type": "panel",
  "title": "Vacuum",
  "path": "vacuum-map",
  "cards": [
    {
      "type": "custom:xiaomi-vacuum-map-card",
      "vacuum_platform": "Tasshack/dreame-vacuum",
      "entity": "vacuum.dusty"
    }
  ]
}
```

## Common Commands Quick Reference

```bash
# Configuration
ssh root@homeassistant.local "ha core check"
ssh root@homeassistant.local "ha core restart"

# Logs
ssh root@homeassistant.local "ha core logs | tail -50"
ssh root@homeassistant.local "ha core logs | grep -i error | tail -20"

# State/Services
ha_get_overview()
ha_get_state(entity_id="entity.name")
ha_call_service(domain="automation", service="reload")
ha_call_service(domain="automation", service="trigger", entity_id="automation.name")

# Deployment (after user commits)
ssh root@homeassistant.local "cd /config && git pull"
scp file.yaml root@homeassistant.local:/config/

# Dashboard deployment
scp .storage/lovelace.my_dashboard root@homeassistant.local:/config/.storage/
python3 -m json.tool .storage/lovelace.my_dashboard > /dev/null  # Validate JSON

# Quick test cycle
scp automations.yaml root@homeassistant.local:/config/
ha_call_service(domain="automation", service="reload")
ha_call_service(domain="automation", service="trigger", entity_id="automation.name")
ssh root@homeassistant.local "ha core logs | grep -i 'automation' | tail -10"
```

## ESPHome Device Integration

Home Assistant often integrates with ESPHome devices (custom firmware for ESP32/ESP8266). When working with ESPHome:

**Configuration:** ESPHome devices have YAML config files typically in an `esphome/` directory.

**Development workflow:**
1. Edit YAML config locally
2. Validate: `esphome config device.yaml`
3. Compile firmware: `esphome compile device.yaml`
4. Upload OTA: `esphome upload device.yaml --device [IP]`
5. Monitor logs: `esphome logs device.yaml`

**Integration with HA:**
- ESPHome devices auto-discovered by Home Assistant
- Entities automatically created
- Use these entities in automations and dashboards like any other HA entity

**Common patterns:**
- Multi-click buttons sending events to HA
- Custom displays showing HA state data
- Sensors reporting to HA entities

Check project docs for device-specific hardware requirements (display drivers, GPIO pins, frameworks).

## Best Practices Summary

1. **Always check configuration** before restart: `ha core check`
2. **Prefer reload over restart** when possible
3. **Test automations manually** after deployment
4. **Check logs** for errors after every change
5. **Use scp for rapid iteration**, git for final changes
6. **Verify outcomes** - don't assume it worked
7. **Use Context7** for current documentation
8. **Test templates in Dev Tools** before adding to dashboards
9. **Validate JSON syntax** before deploying dashboards
10. **Test on actual device** for tablet dashboards
11. **Color-code status** for visual feedback (red/green/amber)
12. **Test with scp first** - user commits stable versions

## Workflow Decision Tree

```
Configuration Change Needed
├─ Is this final/tested?
│  ├─ YES → User commits, agent pulls
│  └─ NO → Use scp workflow
├─ Check configuration valid
├─ Deploy (git pull or scp)
├─ Needs restart?
│  ├─ YES → ha core restart
│  └─ NO → Use appropriate reload
├─ Verify in logs
└─ Test outcome

Dashboard Change Needed
├─ Make changes locally
├─ Deploy via scp
├─ Restart HA (required)
├─ Hard refresh browser
├─ Test on target device
├─ Iterate until perfect
└─ User commits when stable
```

## Voice Assistant Exposed Entities

Control which entities are exposed to the Assist voice assistant (conversation integration).

### Key Concepts

**Storage locations:**
- **`core.entity_registry`** - Stores exposure settings for entities WITH a unique_id (most entities)
- **`homeassistant.exposed_entities`** - Only for legacy entities WITHOUT a unique_id (e.g., light groups)

**Default behavior:**
- HA auto-exposes entities in these domains: `climate`, `cover`, `fan`, `humidifier`, `light`, `media_player`, `scene`, `switch`, `todo`, `vacuum`, `water_heater`
- Plus certain `binary_sensor` and `sensor` device classes (temperature, humidity, motion, etc.)

### Critical: Modifying Entity Registry

**HA must be STOPPED before modifying `core.entity_registry`**, otherwise HA overwrites changes on restart (it keeps the registry in memory).

```bash
# Correct workflow
ssh root@homeassistant "ha core stop"
# ... modify core.entity_registry ...
ssh root@homeassistant "ha core start"
```

### Entity Registry Structure

Exposure settings are stored in each entity's `options.conversation.should_expose` field:

```json
{
  "data": {
    "entities": [
      {
        "entity_id": "light.kitchen",
        "options": {
          "conversation": {
            "should_expose": true
          }
        }
      }
    ]
  }
}
```

### Recommended Management Pattern

1. Create a simple YAML config file listing entities to expose:

```yaml
# exposed_entities.yaml
light.kitchen_lights: true
light.bedroom_lights: true
scene.tv_time: true
scene.good_morning: true
```

2. Create a Python script to apply settings to entity registry:
   - Download `core.entity_registry` from server
   - Set `should_expose: true` for listed entities
   - Set `should_expose: false` for all other entities in auto-exposed domains
   - Upload modified registry back to server

3. Deployment workflow:
   - Stop HA
   - Run script to apply settings
   - Start HA

### Checking Exposed Entities

```bash
# List entities currently exposed (from entity registry)
ssh root@homeassistant "cat /config/.storage/core.entity_registry" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  [print(e['entity_id']) for e in d['data']['entities'] \
  if e.get('options',{}).get('conversation',{}).get('should_expose')==True]"
```

### Light Groups and Legacy Entities

Light groups defined in `configuration.yaml` may not be in the entity registry. For these:
- They need entries in `homeassistant.exposed_entities` instead
- Check if entity exists in registry first before deciding which file to modify

---

This skill encapsulates efficient Home Assistant management workflows developed through iterative optimization and real-world dashboard development. Apply these patterns to any Home Assistant instance for reliable, fast, and safe configuration management.
