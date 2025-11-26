# Home Assistant Management Commands

mod esphome

# List all available commands
default:
    @just --list

# Run inventory script to fetch HA device/entity data
inventory:
    @echo "📊 Running Home Assistant inventory..."
    @./inventory/extract.sh

# Extract config files from HA server and split into individual files
config:
    @echo "📥 Extracting configuration from Home Assistant..."
    @./config/extract.sh

# Run both inventory and config extraction in sequence
sync: inventory config
    @echo "✅ Sync complete!"
