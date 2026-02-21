# Remove Adaptive Lighting Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the custom adaptive lighting system (two template sensors + all callsites) and replace with fixed per-scenario brightness/color temp values.

**Architecture:** The adaptive lighting system consists of two template sensors in `configuration.yaml` (`sensor.adaptive_brightness`, `sensor.adaptive_color_temp`) that compute values from sun elevation and cloud cover. Six callsites read these sensors at runtime. We replace each callsite with hardcoded fixed values, then delete the sensors.

**Tech Stack:** Home Assistant YAML config, `mise run automation-update`, `mise run config deploy`

---

### Task 1: Replace adaptive values in `script.lights`

**Files:**
- Modify: `config/scripts.yaml` (around line 259-308)

The default path in `script.lights` reads both sensors. Replace the variable declarations and usage with fixed values. Also update the description.

**Step 1: Edit `config/scripts.yaml`**

Replace:
```yaml
  description: "Apply adaptive brightness and color temperature based on time/weather"
```
With:
```yaml
  description: "Apply standard brightness and color temperature"
```

Replace the variables block and default sequence (lines ~259-308):
```yaml
    - variables:
        brightness: "{{ states('sensor.adaptive_brightness') | int(50) }}"
        color_temp: "{{ states('sensor.adaptive_color_temp') | int(3000) }}"
        hour: "{{ now().hour }}"
        is_night: "{{ hour >= 23 or hour < 6 }}"
        mode: "{{ night_mode | default('adaptive') }}"
        rgb: "{{ night_rgb | default([255, 159, 242]) }}"
        night_pct: "{{ night_brightness | default(10) }}"
        # Use night_lights if provided, otherwise use all lights
        night_targets: "{{ night_lights | default(lights) }}"
```
With:
```yaml
    - variables:
        brightness: 60
        color_temp: 2700
        hour: "{{ now().hour }}"
        is_night: "{{ hour >= 23 or hour < 6 }}"
        mode: "{{ night_mode | default('adaptive') }}"
        rgb: "{{ night_rgb | default([255, 159, 242]) }}"
        night_pct: "{{ night_brightness | default(10) }}"
        # Use night_lights if provided, otherwise use all lights
        night_targets: "{{ night_lights | default(lights) }}"
```

**Step 2: Deploy scripts**

```bash
mise run config deploy-scripts
```

Expected: scripts upload successfully, no errors.

**Step 3: Verify via MCP**

Call `ha_call_service("script", "reload")` to reload scripts.

**Step 4: Commit**

```bash
git add config/scripts.yaml
git commit -m "fix: replace adaptive values in script.lights with fixed 60%/2700K"
```

---

### Task 2: Replace adaptive values in `script.kitchen_chill`

**Files:**
- Modify: `config/scripts.yaml` (around line 582-620)

**Step 1: Edit `config/scripts.yaml`**

Replace the variables block:
```yaml
    - variables:
        adaptive_brightness: "{{ states('sensor.adaptive_brightness') | int(50) }}"
        adaptive_color_temp: "{{ states('sensor.adaptive_color_temp') | int(3000) }}"
        hour: "{{ now().hour }}"
        is_night: "{{ hour >= 23 or hour < 6 }}"
        # Use full adaptive brightness (no cap)
        chill_brightness: "{{ adaptive_brightness }}"
        # Cap color temp at 3000K (warmer = more chill)
        chill_color_temp: "{{ [adaptive_color_temp, 3000] | min }}"
```
With:
```yaml
    - variables:
        chill_brightness: 50
        chill_color_temp: 2700
        hour: "{{ now().hour }}"
        is_night: "{{ hour >= 23 or hour < 6 }}"
```

**Step 2: Deploy and reload** (same as Task 1 Step 2-3)

**Step 3: Commit**

```bash
git add config/scripts.yaml
git commit -m "fix: replace adaptive values in script.kitchen_chill with fixed 50%/2700K"
```

---

### Task 3: Replace adaptive values in `script.winding_down`

**Files:**
- Modify: `config/scripts.yaml` (around line 806-809)

**Step 1: Edit `config/scripts.yaml`**

Replace:
```yaml
    - variables:
        adaptive_brightness: "{{ states('sensor.adaptive_brightness') | int(25) }}"
        # Cap brightness at 35% for winding down
        capped_brightness: "{{ [adaptive_brightness, 35] | min }}"
        # Very warm color temp, capped at 2200K
        color_temp: 2200
```
With:
```yaml
    - variables:
        capped_brightness: 35
        color_temp: 2200
```

**Step 2: Deploy and reload** (same as Task 1 Step 2-3)

**Step 3: Commit**

```bash
git add config/scripts.yaml
git commit -m "fix: replace adaptive values in script.winding_down with fixed 35%/2200K"
```

---

### Task 4: Replace adaptive values in `script.arriving_home`

**Files:**
- Modify: `config/scripts.yaml` (around line 884-929)

Only the evening (default) path uses adaptive values. The daytime (25%/3000K) and late-night paths are already hardcoded — leave those alone.

**Step 1: Edit `config/scripts.yaml`**

Replace the variables block:
```yaml
    - variables:
        sun_elevation: "{{ state_attr('sun.sun', 'elevation') | float(0) }}"
        adaptive_brightness: "{{ states('sensor.adaptive_brightness') | int(50) }}"
        adaptive_color_temp: "{{ states('sensor.adaptive_color_temp') | int(3000) }}"
        hour: "{{ now().hour }}"
        # Daytime: sun is high enough for natural light
        is_daytime: "{{ sun_elevation > 5 }}"
        # Late night: after 11pm or before 6am
        is_late_night: "{{ hour >= 23 or hour < 6 }}"
        # Cap brightness at 60% for chill vibe
        chill_brightness: "{{ [adaptive_brightness, 60] | min }}"
        # Cap color temp at 3000K (warmer = more welcoming)
        chill_color_temp: "{{ [adaptive_color_temp, 3000] | min }}"
```
With:
```yaml
    - variables:
        sun_elevation: "{{ state_attr('sun.sun', 'elevation') | float(0) }}"
        hour: "{{ now().hour }}"
        is_daytime: "{{ sun_elevation > 5 }}"
        is_late_night: "{{ hour >= 23 or hour < 6 }}"
        chill_brightness: 50
        chill_color_temp: 2700
```

**Step 2: Deploy and reload** (same as Task 1 Step 2-3)

**Step 3: Commit**

```bash
git add config/scripts.yaml
git commit -m "fix: replace adaptive values in script.arriving_home with fixed 50%/2700K"
```

---

### Task 5: Replace adaptive values in `script.charlie_eating`

**Files:**
- Modify: `config/scripts.yaml` (around line 1076-1082)

**Step 1: Edit `config/scripts.yaml`**

Replace:
```yaml
    - variables:
        adaptive_brightness: "{{ states('sensor.adaptive_brightness') | int(50) }}"
        color_temp: "{{ states('sensor.adaptive_color_temp') | int(3000) }}"
        hour: "{{ now().hour }}"
        is_night: "{{ hour >= 23 or hour < 6 }}"
        # Minimum 50% brightness for task lighting
        brightness: "{{ [adaptive_brightness, 50] | max }}"
```
With:
```yaml
    - variables:
        brightness: 60
        color_temp: 2700
        hour: "{{ now().hour }}"
        is_night: "{{ hour >= 23 or hour < 6 }}"
```

**Step 2: Deploy and reload** (same as Task 1 Step 2-3)

**Step 3: Commit**

```bash
git add config/scripts.yaml
git commit -m "fix: replace adaptive values in script.charlie_eating with fixed 60%/2700K"
```

---

### Task 6: Replace adaptive values in `living_room_presence_lighting.yaml`

**Files:**
- Modify: `config/automations/living_room_presence_lighting.yaml`

Only the default (non-night, non-alarm) presence-on branch uses adaptive values. Night (15%/2200K) and alarm (10%/pink) branches are already hardcoded.

**Step 1: Edit the automation**

Remove the `overhead_brightness` variable reference (already removed in a prior session). Replace the remaining adaptive variable declarations:

```yaml
              - variables:
                  brightness: "{{ states('sensor.adaptive_brightness') | int(50) }}"
                  color_temp: "{{ states('sensor.adaptive_color_temp') | int(3000) }}"
                  hour: "{{ now().hour }}"
                  is_night: "{{ hour >= 23 or hour < 6 }}"
                  night_brightness: 15
```
With:
```yaml
              - variables:
                  brightness: 60
                  color_temp: 2700
                  hour: "{{ now().hour }}"
                  is_night: "{{ hour >= 23 or hour < 6 }}"
                  night_brightness: 15
```

**Step 2: Deploy the automation**

```bash
mise run automation-update config/automations/living_room_presence_lighting.yaml
```

Expected: `✅ Updated: Living Room Presence Lighting`

**Step 3: Commit**

```bash
git add config/automations/living_room_presence_lighting.yaml
git commit -m "fix: replace adaptive values in living room presence with fixed 60%/2700K"
```

---

### Task 7: Remove adaptive sensor definitions from `configuration.yaml`

**Files:**
- Modify: `config/configuration.yaml` (around line 146-181)

This is the final step — only do this after all callsites are replaced (Tasks 1-6 complete).

**Step 1: Edit `configuration.yaml`**

Remove the entire `template:` block containing both sensors (lines ~146-182):
```yaml
template:
  - sensor:
      - name: "Adaptive Color Temp"
        ...
      - name: "Adaptive Brightness"
        ...
```

If there are other entries in the `template:` block (non-adaptive sensors), keep those and only remove the two adaptive sensor definitions. If these are the only entries under `template:`, remove the `template:` key too.

**Step 2: Deploy configuration**

```bash
mise run config deploy
```

This uploads `configuration.yaml` and restarts HA. Wait for HA to come back up (~60 seconds).

**Step 3: Verify sensors are gone**

After restart, confirm `sensor.adaptive_brightness` and `sensor.adaptive_color_temp` no longer exist. Use MCP `ha_get_state("sensor.adaptive_brightness")` — should return unavailable or not found.

**Step 4: Commit**

```bash
git add config/configuration.yaml
git commit -m "feat: remove adaptive lighting sensors (brightness + color temp)"
```

---

### Task 8: Update beads issue

Close `home-assistant-28p` (the adaptive lighting investigation issue) since the concept has been removed rather than investigated.

```bash
bd close home-assistant-28p --reason="Removed adaptive lighting entirely rather than investigating - replaced with fixed per-scenario values"
```
