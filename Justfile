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
