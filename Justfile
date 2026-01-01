# Home Assistant Management Commands

# Load configuration from .env file
set dotenv-load

mod esphome
mod config

# List all available commands
default:
    @just --list

# Extract config from server
sync: config::extract
    @echo "✅ Sync complete!"

# Sync HA devices to Homebox inventory
# Usage: just homebox-sync [--dry-run] [--force-update]
homebox-sync *args:
    uv run src/integrations/homebox_sync.py {{args}}
