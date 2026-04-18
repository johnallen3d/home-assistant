# AGENTS.md

## Development Preferences

- **Use `uv`** for Python package management, not pip

## Project Structure

```
mise/tasks/              # All executable tasks (mise run <task>)
├── automation-update    # Update automations on HA server from local files
├── scene-update         # Update scenes on HA server from local files
├── scene-delete         # Delete scenes from HA server by name
├── exposure-voice       # Update voice assistant entity exposure
├── exposure-homekit     # Update HomeKit Bridge entity exposure
├── homebox-sync         # Sync HA devices to Homebox inventory
├── sync                 # Extract config from HA server
├── config               # HA config management (deploy, restart, etc.)
├── esphome              # ESPHome device management
└── esphome-secrets      # Generate esphome/secrets.yaml from Doppler

config/                  # Local HA configuration files
├── automations/         # Individual automation YAML files
├── scenes/              # Individual scene YAML files
├── configuration.yaml   # Main HA config
├── scripts.yaml         # Scripts
└── .storage/            # Dashboard JSON files
```

All scripts are invoked via `mise run <task>` commands. Secrets are managed via **Doppler** (not .envrc).

**Tools managed by mise**: `uv`, `doppler`, `yq`

## Todo List

Use `/todo` command for todo list queries. This queries `todo.ha_enhancements` (not the internal `todoread`/`todowrite` tools).

## Core Tenets

1. **Make changes locally FIRST** - Edit files in this repo via `read` + `edit`, never in HA UI
2. **Push local changes to HA** - Use `mise run <task>` commands for deployment
3. **Validate via SSH** - Use `ssh root@homeassistant` for config validation, entity inspection, and log analysis
4. **Never make changes in HA UI** - For things managed here (automations, scripts, scenes, configuration.yaml)

## ⛔ LOCAL-FIRST WORKFLOW - READ THIS ⛔

**For anything in the "What We Manage Locally" table below, NEVER edit via HA UI or make direct server changes.**

This means: Do NOT edit automations, scripts, dashboards, etc. in the HA UI directly.

**Correct workflow:**
1. Edit the local file (e.g., `config/automations/sexy_time_mode.yaml`) using `read` + `edit`
2. Deploy via `mise` command (e.g., `mise run automation-update config/automations/sexy_time_mode.yaml`)

**Wrong workflow:**
1. ~~Edit automations in the HA UI~~
2. ~~Then try to update local files~~

UI edits bypass local files and create drift between repo and server. Local-first keeps everything in sync.

## What We Manage Locally

| Type | Local File(s) | Deploy Command | Reload Command |
|------|---------------|----------------|----------------|
| Automations | `config/automations/*.yaml` | `mise run automation-update <file>` | auto |
| Scenes | `config/scenes/*.yaml` | `mise run scene-update <file>` | auto |
| Scripts | `config/scripts.yaml` | `mise run config deploy-scripts` | `ha_call_service("script", "reload")` |
| Configuration | `config/configuration.yaml` | `mise run config deploy` | restart required |
| Blueprints | `config/blueprints/` | `mise run config upload-blueprint <file>` | `ha_call_service("automation", "reload")` |
| Dashboards | `config/.storage/lovelace.*` | `mise run config deploy-dashboard <name>` | restart required |
| Exposed entities (voice) | `config/exposed_entities.yaml` | `mise run exposure-voice` | restart required |
| Exposed entities (HomeKit) | `config/homekit_exposed.yaml` | `mise run exposure-homekit` | restart required |

**Defined in `configuration.yaml`** (deploy via `mise run config deploy`):
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

This project has two primary tools for agents:

1. **`mise` tasks** - Deployment automation (see `mise tasks`)
   - `mise run automation-update <file>` - Deploy automation YAML to HA
   - `mise run scene-update <file>` - Deploy scene YAML to HA
   - `mise run config deploy` - Upload configuration.yaml and restart
   - `mise run config restart` - Restart HA core
   - `mise run esphome <cmd>` - ESPHome device management
   - Secrets loaded on-demand from **Doppler** (no .envrc needed)

2. **SSH + File Inspection** - Remote validation and entity inspection
   - SSH to `root@homeassistant` for config validation (`ha core check`), logs, and entity registry queries
   - Query `.storage/core.entity_registry` and `.storage/core.device_registry` for entity IDs and device mappings
   - Useful for debugging service call issues and verifying entity targeting

**Workflow:**
- Edit files locally with `read` + `edit` tools
- Deploy via `mise run` commands
- Validate via SSH when needed (entity registry inspection, config checks)

### Known Issues

**`mise run automation-update` only updates existing automations.**
The `update-automation` task downloads the server's automation list and merges changes. It won't add automations that don't already exist on the server. For new automations, create them in the HA UI first, then download the `id` and add to your local YAML.

**Service call syntax varies by integration.**  
Some integrations (like Music Assistant) don't accept standard HA `target: entity_id:` syntax. Use SSH to query entity registry for entity IDs and test service calls locally in YAML before deploying. Example: `music_assistant.play_media` requires `data: entity_id:` not `target:`.

### Renaming Scripts/Scenes/Entities Checklist

When renaming any script, scene, or entity that may be exposed to voice assistants or HomeKit:

1. **Update the entity definition** (e.g., `scripts.yaml`, `scenes/*.yaml`)
2. **Update all references** in automations that call the entity
3. **Update exposure configs** - these reference entities by ID:
   - `config/exposed_entities.yaml` - voice assistant (Assist)
   - `config/homekit_exposed.yaml` - HomeKit/Siri
4. **Deploy all changes** - scripts, automations, AND exposure configs

**The exposure configs are the primary reason for renaming** - they control what voice assistants can access. Forgetting to update them defeats the purpose of the rename.

### Adding a New Mode Checklist

When adding a new mode (like babysitter_mode, cleaning_mode, etc.), ALL of these must be done:

1. **`input_boolean`** in `configuration.yaml`
2. **Scene** (if applicable) in `config/scenes/`
3. **Automation handler** in `config/automations/` (ON/OFF logic)
4. **Mode conflict matrix** — add to every other mode that should clear this one (automation sandwich: disable automation → turn off boolean → re-enable)
5. **`reset_all_modes` script** — add to all 3 steps (disable, turn off, re-enable)
6. **`departing` automation** — add condition to protect mode from departure lights-off (if mode should survive leaving home)
7. **`mode_light_watchers` automation** — add to relevant light-off triggers so mode clears when its lights are manually turned off. **This prevents stale mode state.**
8. **Dashboard** — add toggle button to mobile dashboard
9. **Other scripts that control the same lights** (e.g., `tv_time`) — add guards to skip light changes when mode is active

### Automation/Script Update Checklist

After modifying automations that respond to physical triggers (buttons, sensors), **always verify**:

1. **Deploy the local YAML:**
   ```bash
   mise run automation-update config/automations/your_automation.yaml
   ```
   Verify success message.

2. **Query entity state via SSH:**
   ```bash
   ssh root@homeassistant "ha shell -c 'print(hass.states.get(\"automation.xxx\"))'"
   ```
   State should be "on" and not showing errors.

3. **Trigger a test event and verify:**
   - Ask user to press the button / trigger the sensor
   - Check HA's automation traces in the UI (Automations → tap automation → "Traces" tab)
   - Verify the most recent execution shows `finished` state and no errors

4. **If automation fails silently:**
   - Check entity registry: `ssh root@homeassistant "cat /config/.storage/core.entity_registry | jq '.data.entities[] | select(.entity_id == \"automation.xxx\")'`
   - Verify service call syntax in YAML (some integrations have non-standard `target:` vs `data:` requirements)
   - Re-deploy and check traces again

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
  `mise run esphome clean && mise run esphome compile`
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
- **Task**: `mise run exposure-voice` - applies YAML config to entity registry
- **Critical**: HA must be **stopped** before modifying `core.entity_registry`
- **Commands**:
  - `mise run exposure-voice` - Apply settings (requires HA stopped)
  - `mise run exposure-voice --dry-run` - Dry run, show what would change
- **Note**: Light groups may need `homeassistant.exposed_entities` for legacy handling

### HomeKit Bridge Exposed Entities
- **Config file**: `config/homekit_exposed.yaml` - domain-based filter config
- **Task**: `mise run exposure-homekit` - applies YAML config to HomeKit config entry
- **Critical**: HA must be **stopped** before modifying `core.config_entries`
- **Model**: Unlike voice assistant (per-entity), HomeKit uses domain includes + entity excludes
- **Commands**:
  - `mise run exposure-homekit` - Apply settings (requires HA stopped)
  - `mise run exposure-homekit --dry-run` - Dry run, show what would change
  - `mise run config list-homekit-server` - Show current filter on server
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

## External Network Monitoring (pi-01)

The pi-cielo project on pi-01 runs a network outage detector that monitors connectivity to key network infrastructure. This can be useful for correlating Home Assistant device availability issues with network outages.

### Outage Detector Service

**Location**: pi-01 (`ssh pi@pi-01.local`)

| Command | Description |
|---------|-------------|
| `ssh pi@pi-01.local "systemctl status outage-detector"` | Service status |
| `ssh pi@pi-01.local "journalctl -u outage-detector -f"` | Live logs |
| `ssh pi@pi-01.local "journalctl -u outage-detector --since '1 hour ago'"` | Recent history |

**Script**: `/opt/outage-detector/outage_detector.py`
**Data**: `/var/lib/outage-detector/`

### Monitored Endpoints

| Endpoint | IP | Purpose |
|----------|-----|---------|
| tplink_router | 192.168.0.1 | Primary router |
| att_gateway | 192.168.1.254 | ISP gateway |
| internet | 8.8.8.8 | External connectivity |

The detector pings each endpoint every 5 seconds and logs when connectivity is lost/restored, including outage duration.

### Correlation with Home Assistant

When investigating device unavailability in HA:
1. Note the timestamp of unavailable states
2. Check outage detector logs for the same window
3. If all three endpoints were down, it's a network issue (not device-specific)
4. TP-Link router outages may cause brief HA device disconnections

**Related project**: `~/dev/src/playground/pi-cielo/` (see `docs/network-outage-*.md` for investigation examples)

---

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Prepare commit** - Stage changes and prepare commit message
5. **ASK USER FOR CONFIRMATION** - Show staged files and commit message, wait for approval
6. **After user approves commit** - Commit and sync beads
7. **ASK USER FOR PUSH CONFIRMATION** - Ask "Ready to push to remote?"
8. **After user approves push** - Push to remote

## ⛔ GIT SAFETY - READ THIS ⛔

**NEVER commit or push without user approval.** But recognize what approval looks like.

**These phrases ARE approval - just do it, don't ask again:**
- "commit the changes", "commit it", "please commit"
- "push it", "push to remote", "go ahead and push"
- "yes", "do it", "go ahead", "ship it"

**Only ask for confirmation when:**
- You're about to commit/push and the user hasn't requested it
- The user asked a question (not gave an instruction)

**Agent co-author convention:**
- When agent co-author credit is required, use `Co-Authored-By: Shitty Coding Agent <noreply@shittycodingagent.ai>`

**Commands that push (be aware):**
- `git push`
- `bd sync` ← THIS PUSHES! It runs `git push` internally!

**Do NOT run `bd sync` without approval.** Use `bd close` to close issues,
then wait for push approval before running `bd sync`.

## Agent Methods & Patterns

### File Operations
- **`read` tool**: Load YAML/JSON files for inspection before editing
- **`edit` tool**: Make precise text replacements with `oldText` + `newText` (no overlapping edits)
- **`bash` tool**: File operations (`ls`, `find`, `grep`) only; avoid large output

### Entity & Device Inspection
- **SSH entity registry**: `ssh root@homeassistant "cat /config/.storage/core.entity_registry | jq ..."` to query entity IDs by name/platform
- **SSH device registry**: `ssh root@homeassistant "cat /config/.storage/core.device_registry | jq ..."` to map devices to names/models
- Useful for verifying service call targeting and debugging integration-specific naming

### Deployment
- **`mise run` tasks**: All deployments go through mise (automation-update, config deploy, etc.)
- Always verify task succeeds before considering work done

### Issue Tracking
- **`bd` commands**: All work tracked via beads (create, close, list)
- Use `--json` flag for programmatic output
- Create issue → do work → close issue → commit → push

### Git & Commits
- **Conventional Commits**: `type(scope): subject` format
- Example: `fix(automations): use data param for music_assistant play_media`
- Use `authoring-commits` skill when creating commit messages

<!-- bv-agent-instructions-v1 -->

---

## Beads Workflow Integration

This project uses [beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) for issue tracking. Issues are stored in `.beads/` and tracked in git.

### Essential Commands

```bash
# View issues (launches TUI - avoid in automated sessions)
bv

# CLI commands for agents (use these instead)
bd ready              # Show issues ready to work (no blockers)
bd list --status=open # All open issues
bd show <id>          # Full issue details with dependencies
bd create --title="..." --type=task --priority=2
bd update <id> --status=in_progress
bd close <id> --reason="Completed"
bd close <id1> <id2>  # Close multiple issues at once
bd sync               # ⚠️ PUSHES TO REMOTE - requires user approval first!
```

### Workflow Pattern

1. **Start**: Run `bd ready` to find actionable work
2. **Claim**: Use `bd update <id> --status=in_progress`
3. **Work**: Implement the task
4. **Complete**: Use `bd close <id>`
5. **Ask before sync**: `bd sync` pushes to remote - get user approval first!

### Key Concepts

- **Dependencies**: Issues can block other issues. `bd ready` shows only unblocked work.
- **Priority**: P0=critical, P1=high, P2=medium, P3=low, P4=backlog (use numbers, not words)
- **Types**: task, bug, feature, epic, question, docs
- **Blocking**: `bd dep add <issue> <depends-on>` to add dependencies

### Session Protocol

**Before ending any session, run this checklist:**

```bash
git status              # Check what changed
git add <files>         # Stage code changes
git commit -m "..."     # Commit code
# ⛔ STOP HERE - ASK USER: "Ready to push to remote?"
# Only after approval:
bd sync                 # Syncs beads AND pushes to remote
```

**IMPORTANT:**
- Always `git commit` before `bd sync` (sync pulls, which fails with staged changes)
- **NEVER run `bd sync` or `git push` without explicit user approval**

### Best Practices

- Check `bd ready` at session start to find available work
- Update status as you work (in_progress → closed)
- Create new issues with `bd create` when you discover tasks
- Use descriptive titles and set appropriate priority/type
- Ask user before running `bd sync` (it pushes to remote)

<!-- end-bv-agent-instructions -->

## Notes for Pi Agents Working Without HA MCP

This project **intentionally does not provide HA MCP access** to agents. Instead, agents should:

1. **Edit locally** - Use `read` + `edit` to modify config files
2. **Deploy via mise** - All deployment goes through `mise run` tasks
3. **Validate via SSH** - Query entity registry, inspect device mappings, check logs over SSH
4. **Reference AGENTS.md** - This file documents all entity naming, device locations, and known issues

This approach keeps all config in git and prevents drift between repo and server state. If something isn't documented here or in the code, query the HA server via SSH to discover it.

Common SSH patterns:
```bash
# List all automations
grep -r "alias:" /config/automations/*.yaml | head -20

# Find entity by name
ssh root@homeassistant "cat /config/.storage/core.entity_registry | jq '.data.entities[] | select(.entity_id | contains(\"keyword\"))'"

# Check automation state
ssh root@homeassistant "curl -s http://localhost:8123/api/states/automation.xxx \
  -H \"Authorization: Bearer TOKEN\" | jq .state"

# View recent logs
ssh root@homeassistant "ha core logs | tail -50"
```

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Dolt-powered version control with native sync
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs via Dolt:

- Each write auto-commits to Dolt history
- Use `bd dolt push`/`bd dolt pull` for remote sync
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->

# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any shell command containing `curl` or `wget` will be intercepted and blocked by the context-mode plugin. Do NOT retry.
Instead use:
- `context-mode_ctx_fetch_and_index(url, source)` to fetch and index web pages
- `context-mode_ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any shell command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` will be intercepted and blocked. Do NOT retry with shell.
Instead use:
- `context-mode_ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### Direct web fetching — BLOCKED
Do NOT use any direct URL fetching tool. Use the sandbox equivalent.
Instead use:
- `context-mode_ctx_fetch_and_index(url, source)` then `context-mode_ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Shell (>20 lines output)
Shell is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `context-mode_ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `context-mode_ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### File reading (for analysis)
If you are reading a file to **edit** it → reading is correct (edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `context-mode_ctx_execute_file(path, language, code)` instead. Only your printed summary enters context.

### grep / search (large results)
Search results can flood context. Use `context-mode_ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `context-mode_ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `context-mode_ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `context-mode_ctx_execute(language, code)` | `context-mode_ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `context-mode_ctx_fetch_and_index(url, source)` then `context-mode_ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `context-mode_ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.
