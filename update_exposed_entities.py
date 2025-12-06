#!/usr/bin/env python3
"""
Update entity registry to set conversation exposure based on exposed_entities.yaml.

This script:
1. Reads exposed_entities.yaml to get the list of entities to expose
2. Downloads core.entity_registry from HA server
3. Sets should_expose=true for listed entities, false for all others in auto-exposed domains
4. Uploads the modified registry back to the server

Usage:
    python update_exposed_entities.py [--dry-run]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Domains that HA auto-exposes by default (from exposed_entities.py source)
DEFAULT_EXPOSED_DOMAINS = {
    "climate",
    "cover",
    "fan",
    "humidifier",
    "light",
    "media_player",
    "scene",
    "switch",
    "todo",
    "vacuum",
    "water_heater",
}

# Additional domains that might have exposed entities
ADDITIONAL_DOMAINS = {
    "binary_sensor",
    "script",
    "sensor",
    "assist_satellite",
}

ALL_MANAGED_DOMAINS = DEFAULT_EXPOSED_DOMAINS | ADDITIONAL_DOMAINS


def load_exposed_config(config_path: Path) -> set[str]:
    """Load the exposed_entities.yaml and return set of entity_ids to expose."""
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # Return entity_ids where value is True
    return {entity_id for entity_id, expose in data.items() if expose is True}


def run_ssh(cmd: str) -> str:
    """Run SSH command and return output."""
    server = os.environ.get("HA_SERVER", "root@homeassistant")
    result = subprocess.run(
        ["ssh", server, cmd],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def download_registry(server: str) -> dict:
    """Download entity registry from HA server."""
    result = subprocess.run(
        ["ssh", server, "cat /config/.storage/core.entity_registry"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def upload_registry(server: str, registry: dict) -> None:
    """Upload entity registry to HA server."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(registry, f, indent=2)
        temp_path = f.name

    try:
        subprocess.run(
            ["scp", temp_path, f"{server}:/config/.storage/core.entity_registry"],
            check=True,
        )
    finally:
        os.unlink(temp_path)


def update_registry(
    registry: dict, expose_entities: set[str], dry_run: bool = False
) -> dict:
    """Update entity registry with exposure settings."""
    entities = registry["data"]["entities"]

    stats = {"exposed": 0, "hidden": 0, "unchanged": 0, "not_in_domain": 0}
    changes = []

    for entity in entities:
        entity_id = entity["entity_id"]
        domain = entity_id.split(".")[0]

        # Only manage entities in auto-exposed domains
        if domain not in ALL_MANAGED_DOMAINS:
            stats["not_in_domain"] += 1
            continue

        # Determine desired exposure
        should_expose = entity_id in expose_entities

        # Get current options
        options = entity.get("options", {})
        conv_options = options.get("conversation", {})
        current_expose = conv_options.get("should_expose")

        # Check if change needed
        if current_expose == should_expose:
            stats["unchanged"] += 1
            continue

        # Update options
        if "options" not in entity:
            entity["options"] = {}
        if "conversation" not in entity["options"]:
            entity["options"]["conversation"] = {}

        entity["options"]["conversation"]["should_expose"] = should_expose

        if should_expose:
            stats["exposed"] += 1
            changes.append(f"  + {entity_id}")
        else:
            stats["hidden"] += 1
            changes.append(f"  - {entity_id}")

    # Print summary
    print(f"\nChanges {'(dry run)' if dry_run else ''}:")
    if changes:
        for change in sorted(changes):
            print(change)
    else:
        print("  No changes needed")

    print(f"\nSummary:")
    print(f"  Exposed: {stats['exposed']}")
    print(f"  Hidden: {stats['hidden']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Not in managed domains: {stats['not_in_domain']}")

    return registry


def main():
    parser = argparse.ArgumentParser(description="Update HA entity exposure settings")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying"
    )
    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    config_path = script_dir / "config" / "exposed_entities.yaml"

    if not config_path.exists():
        print(f"Error: {config_path} not found")
        sys.exit(1)

    # Load config
    print(f"Loading exposed entities from {config_path}")
    expose_entities = load_exposed_config(config_path)
    print(f"Found {len(expose_entities)} entities to expose")

    # Get server from env
    server = os.environ.get("HA_SERVER", "root@homeassistant")
    print(f"Connecting to {server}...")

    # Download registry
    print("Downloading entity registry...")
    registry = download_registry(server)
    print(f"Found {len(registry['data']['entities'])} entities in registry")

    # Update registry
    updated_registry = update_registry(registry, expose_entities, dry_run=args.dry_run)

    if args.dry_run:
        print("\nDry run - no changes made")
        return

    # Upload registry
    print("\nUploading entity registry...")
    upload_registry(server, updated_registry)
    print("Done! Restart HA for changes to take effect: just config::restart")


if __name__ == "__main__":
    main()
