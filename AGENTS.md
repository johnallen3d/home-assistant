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
