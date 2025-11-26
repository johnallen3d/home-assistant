# AGENT.md

## Build/Test/Lint Commands
This is a Home Assistant inventory repository - no traditional build/test commands needed.
- Run inventory script: `./ha_inventory.sh`
- Verify script syntax: `bash -n ha_inventory.sh`
- Test SSH connectivity: `ssh root@homeassistant "ha info"`

## Code Style Guidelines
- Use bash for shell scripts with proper error handling
- Follow standard bash conventions: 2-space indentation, quoted variables
- Use descriptive function names and comments for complex operations
- Prefer emoji indicators for user feedback (✅❌📥📊)
- Use Python 3 for data processing with json library
- Generate markdown documentation with proper headers and formatting
- Handle SSH connection errors gracefully with appropriate exit codes
- Use absolute paths for file operations to ensure reliability

## Home Assistant Configuration Management
- Configuration files location: `/config/` on Home Assistant server
- Server uses single-file configuration: `/config/automations.yaml`, `/config/scenes.yaml`
- Local repo uses split files: `config/automations/*.yaml`, `config/scenes/*.yaml`
- Extract script automatically splits into individual files for better git tracking
- This is a READ-ONLY backup repository - never push changes back to server
- Edit automations/scenes via Home Assistant UI only (server is source of truth)
- Use SCP to transfer files: `scp local/file root@homeassistant:/config/file`
- Use SSH to execute HA CLI commands: `ssh root@homeassistant "ha [command]"`
- To reload after manual edits: `ha core restart` (no direct reload command)
- YAML uses 2-space indentation and follows Home Assistant entity structure

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
