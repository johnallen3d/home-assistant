# Home Assistant Management Commands

mod esphome
mod config

# List all available commands
default:
    @just --list

# Run inventory script to fetch HA device/entity data
inventory:
    @echo "📊 Running Home Assistant inventory..."
    @./inventory/extract.sh

# Run both inventory and config extraction in sequence
sync: inventory config::extract
    @echo "✅ Sync complete!"
