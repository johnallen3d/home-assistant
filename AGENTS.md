# AGENTS.md

## Development Preferences
- Use `uv`, not `pip`.
- Run repo tasks via `mise run <task>`.
- Secrets come from **Doppler**, not `.envrc`.
- Tools managed by mise: `uv`, `doppler`, `yq`.

## Project Structure
```text
mise/tasks/              # executable tasks
config/                  # local HA config
├── automations/
├── scenes/
├── configuration.yaml
├── scripts.yaml
└── .storage/
```

Common tasks:
- `automation-update` - deploy automation YAML
- `scene-update` / `scene-delete`
- `exposure-voice` / `exposure-homekit`
- `homebox-sync`
- `sync`
- `config`
- `esphome`
- `esphome-secrets`

## Todo List
- Use `/todo` for todo queries.
- Query `todo.ha_enhancements`, not internal todo tools.

## Core Rules
1. **Local first.** Edit repo files with `read` + `edit`.
2. **Do not edit managed items in HA UI.** Avoid drift.
3. **Deploy via `mise run ...`.**
4. **Validate via SSH.** Use `ssh root@homeassistant`.

## Managed Locally
| Type | Local file(s) | Deploy |
|---|---|---|
| Automations | `config/automations/*.yaml` | `mise run automation-update <file>` |
| Scenes | `config/scenes/*.yaml` | `mise run scene-update <file>` |
| Scripts | `config/scripts.yaml` | `mise run config deploy-scripts` |
| Configuration | `config/configuration.yaml` | `mise run config deploy` |
| Blueprints | `config/blueprints/` | `mise run config upload-blueprint <file>` |
| Dashboards | `config/.storage/lovelace.*` | `mise run config deploy-dashboard <name>` |
| Voice exposure | `config/exposed_entities.yaml` | `mise run exposure-voice` |
| HomeKit exposure | `config/homekit_exposed.yaml` | `mise run exposure-homekit` |

Also managed in `configuration.yaml`:
- `light:` groups
- `group:` entity groups
- input helpers
- `template:` sensors

OK in HA UI:
- integrations, devices, entities
- areas, floors, labels
- users, persons, zones
- HACS repos

## Standard Workflow
1. Edit local file.
2. Deploy with `mise run ...`.
3. Validate with SSH.
4. Never "fix in UI later".

## Main Tools
### `mise`
- `mise run automation-update <file>`
- `mise run scene-update <file>`
- `mise run config deploy`
- `mise run config restart`
- `mise run esphome <cmd>`

### SSH
Use for:
- `ha core check`
- logs
- `.storage/core.entity_registry`
- `.storage/core.device_registry`

## Known Issues
- `mise run automation-update` updates existing automations only. New automation must exist in HA first so local YAML can include server `id`.
- Some integrations need nonstandard service syntax. Example: `music_assistant.play_media` uses `data: entity_id:`, not `target:`.
- Airversa AP2 1120 air purifier has never worked; its unavailable state is not a new incident.

## Renaming Checklist
When renaming script, scene, or entity:
1. Update definition.
2. Update all automation references.
3. Update exposure files:
   - `config/exposed_entities.yaml`
   - `config/homekit_exposed.yaml`
4. Deploy all affected files.

## New Mode Checklist
When adding mode (`babysitter_mode`, `cleaning_mode`, etc.):
1. Add `input_boolean` in `configuration.yaml`.
2. Add scene if needed.
3. Add automation handler.
4. Update conflict matrix in other modes.
5. Update `reset_all_modes`.
6. Update `departing` if mode should survive leaving.
7. Update `mode_light_watchers` so manual light-off clears stale mode.
8. Add dashboard toggle.
9. Add guards in other scripts touching same lights.

## Automation / Script Verification
After changing physical-trigger automation:
1. Deploy YAML.
2. Check automation state over SSH:
   ```bash
   ssh root@homeassistant "ha shell -c 'print(hass.states.get(\"automation.xxx\"))'"
   ```
3. Trigger real event.
4. Verify HA trace shows `finished` and no errors.

Do not mark done until real trigger works.

If it fails silently:
- inspect entity registry
- verify service-call syntax
- redeploy and recheck traces

## Floorplan
Orientation: standing at front door facing in.
- Left = Charlie side
- Right = Dad side
- Forward = living room + balcony

Layout:
- Entry → Kitchen → Dining → Living → Balcony
- Left wing: Charlie bedroom + bath, laundry, utility closet
- Right wing: Dad bedroom + bath

Lighting context:
- TV on wall near Charlie side
- Dad chair near Dad bedroom, faces TV
- Balcony doors right of Dad chair
- Couch faces glass doors, not TV
- Living room light causes TV glare; kitchen lights do not

## Connection Info
- HA server: `root@homeassistant` (`.local` fails auth)
- HA config path: `/config/`

## ESPHome: M5Stack Atom S3 (`tiny-button`)
- IP: `192.168.0.87`
- Config: `esphome/tiny-button.yaml`
- Button: GPIO41
- Display: 128x128 LCD, GC9107, `st7789v`
- Framework: `arduino`
- Board: `m5stack-atoms3`
- Display model: `CUSTOM`
- Offsets: `offset_height: 3`, `offset_width: 1`
- Pins: CLK=17 MOSI=21 CS=15 DC=33 RST=34 BL=16
- Clean build if sensor types change:
  ```bash
  mise run esphome clean && mise run esphome compile
  ```
- Emits HA event: `esphome.button_pressed` with `click_type`

## Blueprints
- Path: `config/blueprints/automation/`
- `multi_click_button_controller.yaml` handles single/double/long press for Zigbee and ESPHome buttons.

## Voice Exposure
- Config: `config/exposed_entities.yaml`
- Apply: `mise run exposure-voice`
- HA must be **stopped** before editing `core.entity_registry`
- Dry run: `mise run exposure-voice --dry-run`
- Light groups may need `homeassistant.exposed_entities`

## HomeKit Exposure
- Config: `config/homekit_exposed.yaml`; apply: `mise run exposure-homekit`.
- Read-only plan: `mise run exposure-homekit --dry-run`; tests: `mise run test-homekit`.
- Top-level include/exclude lists manage the existing bridge (HASS Bridge, 21064).
  `camera_accessories` manages standalone camera entries on stable names/ports.
  Cameras must not also match the bridge filter. Missing accessories are created;
  matching ones retain entry IDs and pairing state. Unlisted entries are not deleted.
- Charlie Cam: `camera.charlie_cam_2`, port 21065, linked to
  `binary_sensor.charlie_cam_person_occupancy`. Entry Nest: `camera.entry_nest`,
  port 21066, linked to `binary_sensor.entry_nest_person_occupancy`.
  Both copy H.264 without transcoding; audio is off. HomeKit Secure Video is unsupported.
- `frigate_rtsp` configures the Frigate RTSP URL template through its options API.
  Credentials are read at runtime from Doppler `pi-cielo/prod`, secret names
  `FRIGATE_RTSP_USER` / `FRIGATE_RTSP_PASSWORD`; never commit or print values.
  Streams use authenticated `192.168.5.20:8554/{{ name }}`. Never use the
  ONVIF/direct-Wyze entity: the camera must retain one RTSP client (Frigate).
- HomeKit options flows cannot express linked motion sensors or stable names/ports.
  The task holds `/config/.home-assistant-deploy.lock`, stops HA itself, re-reads
  flushed storage, creates a timestamped 0600 backup, atomically replaces
  `core.config_entries`, and starts HA even if writing fails. No manual stop needed.
  It skips stop/start for an unchanged plan and records source/hashes in
  `/config/.homekit-exposure-deployment.json` after checking integrations loaded.
  Other activation entry points must honor the same lock; never bypass its owner.
- Inspect bridge filter: `mise run config list-homekit-server`. Pair each new
  accessory separately using HA persistent notifications; enable camera activity
  notifications in the iPhone Home app. Verify live view, Apple TV PiP, and a real
  person-triggered snapshot notification before closing the camera task.

Camera config shape (alongside the existing bridge lists):
```yaml
camera_accessories:
  - name: Charlie Cam
    port: 21065
    entity_id: camera.charlie_cam_2
    linked_motion_sensor: binary_sensor.charlie_cam_person_occupancy
    video_codec: copy
    support_audio: false
```

## Adaptive Lighting
Location: `config/configuration.yaml` template sensors.

Key entities:
- `sensor.adaptive_brightness`
- `sensor.adaptive_color_temp`

Brightness:
| Condition | Brightness |
|---|---|
| Night (11pm-6am) | 20% |
| Sun below horizon | 32% |
| Sun 0-15° | `32 + elevation*1.6` → 32-56% |
| Sun above 15° | 56% + cloud boost, up to 80% |

Color temp:
| Condition | Temp |
|---|---|
| Night (11pm-6am) | 2200K |
| Sun below horizon | 2400K |
| Sun 0-15° | `2400 + elevation*80` → 2400-3600K |
| Sun above 15° | 3600-4500K |

Used by `script.lights` and presence automations.

Tuning:
- too dim at dusk → raise below-horizon baseline
- too dim at night → raise night value
- ramp speed set by multiplier

## External Network Monitoring (`pi-01`)
- Host: `ssh pi@pi-01.local`
- Service: `outage-detector`
- Script: `/opt/outage-detector/outage_detector.py`
- Data: `/var/lib/outage-detector/`

Useful commands:
```bash
ssh pi@pi-01.local "systemctl status outage-detector"
ssh pi@pi-01.local "journalctl -u outage-detector -f"
ssh pi@pi-01.local "journalctl -u outage-detector --since '1 hour ago'"
```

Endpoints:
- `tplink_router` - `192.168.0.1`
- `att_gateway` - `192.168.1.254`
- `internet` - `8.8.8.8`

Use outage logs to correlate HA device unavailability.

Related repo: `~/dev/src/playground/pi-cielo/`

## Git / Issue Tracking Rules
- Track work with **Fizzy**, not markdown TODOs. `.fizzy.yaml` selects the `home-assistant` board.
- Run via Doppler for `FIZZY_TOKEN`: `mise exec -- doppler run -- fizzy ...`.
- Cards use their **number**, not ID. Prefer `--jq` for compact output.
- Typical flow:
  1. `fizzy card list`
  2. `fizzy card show <number>`
  3. work; comment progress with `fizzy comment create --card <number> --body "..."`
  4. `fizzy card close <number>`
- Reference related cards by number (e.g. "pi-cielo #843") in descriptions/comments.
- `.beads/` is a historical archive of the old tracker. Do not create or update Beads issues.
- Never commit or push without user approval.
- Approval can be explicit short forms: "yes", "do it", "commit it", "push it", etc.

## Session Wrap-Up
Before ending session:
1. File follow-up issues.
2. Run quality checks if code changed.
3. Update issue status.
4. Stage changes and prepare commit message.
5. Ask user before commit.
6. After commit approval, commit.
7. Ask user before push.
8. After push approval, push.

Co-author trailer if needed:
`Co-Authored-By: Shitty Coding Agent <noreply@shittycodingagent.ai>`

## Common Commands
```bash
mise exec -- doppler run -- fizzy card list
mise exec -- doppler run -- fizzy card show <number>
mise exec -- doppler run -- fizzy card create --title "Title" --description "Context"
mise exec -- doppler run -- fizzy comment create --card <number> --body "Progress"
mise exec -- doppler run -- fizzy card close <number>
mise exec -- doppler run -- fizzy search "query"
```

SSH patterns:
```bash
grep -r "alias:" /config/automations/*.yaml | head -20
ssh root@homeassistant "cat /config/.storage/core.entity_registry | jq '.data.entities[] | select(.entity_id | contains(\"keyword\"))'"
ssh root@homeassistant "ha core logs | tail -50"
```

## Context-Mode Rules
Do not use blocked direct web fetch patterns.

Instead use context-mode tools:
- fetch/index: `context-mode_ctx_fetch_and_index(...)`
- command batches: `context-mode_ctx_batch_execute(...)`
- sandbox execution: `context-mode_ctx_execute(...)`
- indexed search: `context-mode_ctx_search(...)`

Shell is for short-output commands only. Use sandbox/context-mode for large output, grep-heavy analysis, file analysis, or web fetching.
