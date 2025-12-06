#!/usr/bin/env python3
"""
Update HomeKit Bridge config entry to set exposed entities based on homekit_exposed.yaml.

This script:
1. Reads homekit_exposed.yaml to get include_domains, include_entities, exclude_entities
2. Downloads core.config_entries from HA server
3. Updates the HomeKit Bridge entry's options.filter section
4. Uploads the modified config entries back to the server

Usage:
    python update_homekit_entities.py [--dry-run]

Note: Unlike voice assistant exposure (entity registry), HomeKit uses the
config entry's filter options. This requires HA to be stopped before modification.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# The HomeKit Bridge entry we want to modify (not the accessory mode entry)
HOMEKIT_BRIDGE_TITLE_PATTERN = "HASS Bridge"


def load_homekit_config(config_path: Path) -> dict:
    """Load homekit_exposed.yaml and return the filter configuration."""
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return {
        "include_domains": data.get("include_domains", []),
        "include_entities": data.get("include_entities", []),
        "exclude_domains": data.get("exclude_domains", []),
        "exclude_entities": data.get("exclude_entities", []),
    }


def download_config_entries(server: str) -> dict:
    """Download config entries from HA server."""
    result = subprocess.run(
        ["ssh", server, "cat /config/.storage/core.config_entries"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def upload_config_entries(server: str, config_entries: dict) -> None:
    """Upload config entries to HA server."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_entries, f, indent=2)
        temp_path = f.name

    try:
        subprocess.run(
            ["scp", temp_path, f"{server}:/config/.storage/core.config_entries"],
            check=True,
        )
    finally:
        os.unlink(temp_path)


def find_homekit_bridge_entry(config_entries: dict) -> dict | None:
    """Find the HomeKit Bridge config entry (not accessory mode)."""
    for entry in config_entries["data"]["entries"]:
        if entry.get("domain") == "homekit":
            # Look for bridge mode, not accessory mode
            if entry.get("options", {}).get("mode") == "bridge":
                return entry
            # Fallback: check title pattern
            if HOMEKIT_BRIDGE_TITLE_PATTERN in entry.get("title", ""):
                return entry
    return None


def update_homekit_filter(
    config_entries: dict, filter_config: dict, dry_run: bool = False
) -> tuple[dict, dict]:
    """Update HomeKit Bridge filter configuration."""
    entry = find_homekit_bridge_entry(config_entries)

    if not entry:
        print("Error: HomeKit Bridge config entry not found")
        print("Available homekit entries:")
        for e in config_entries["data"]["entries"]:
            if e.get("domain") == "homekit":
                print(
                    f"  - {e.get('title')} (mode: {e.get('options', {}).get('mode', 'unknown')})"
                )
        sys.exit(1)

    # Get current filter
    current_options = entry.get("options", {})
    current_filter = current_options.get("filter", {})

    # Build new filter
    new_filter = {
        "include_domains": filter_config["include_domains"],
        "include_entities": filter_config["include_entities"],
        "exclude_domains": filter_config["exclude_domains"],
        "exclude_entities": filter_config["exclude_entities"],
    }

    # Calculate changes
    changes = {
        "include_domains": {
            "added": set(new_filter["include_domains"])
            - set(current_filter.get("include_domains", [])),
            "removed": set(current_filter.get("include_domains", []))
            - set(new_filter["include_domains"]),
        },
        "include_entities": {
            "added": set(new_filter["include_entities"])
            - set(current_filter.get("include_entities", [])),
            "removed": set(current_filter.get("include_entities", []))
            - set(new_filter["include_entities"]),
        },
        "exclude_domains": {
            "added": set(new_filter["exclude_domains"])
            - set(current_filter.get("exclude_domains", [])),
            "removed": set(current_filter.get("exclude_domains", []))
            - set(new_filter["exclude_domains"]),
        },
        "exclude_entities": {
            "added": set(new_filter["exclude_entities"])
            - set(current_filter.get("exclude_entities", [])),
            "removed": set(current_filter.get("exclude_entities", []))
            - set(new_filter["exclude_entities"]),
        },
    }

    # Print changes
    has_changes = False
    print(
        f"\nChanges to HomeKit Bridge '{entry.get('title')}' {'(dry run)' if dry_run else ''}:"
    )

    for section, diffs in changes.items():
        if diffs["added"] or diffs["removed"]:
            has_changes = True
            print(f"\n  {section}:")
            for item in sorted(diffs["added"]):
                print(f"    + {item}")
            for item in sorted(diffs["removed"]):
                print(f"    - {item}")

    if not has_changes:
        print("  No changes needed")

    # Apply changes if not dry run
    if not dry_run and has_changes:
        entry["options"]["filter"] = new_filter

    # Summary
    print(f"\nFinal configuration:")
    print(f"  include_domains: {len(new_filter['include_domains'])} domains")
    print(f"  include_entities: {len(new_filter['include_entities'])} entities")
    print(f"  exclude_domains: {len(new_filter['exclude_domains'])} domains")
    print(f"  exclude_entities: {len(new_filter['exclude_entities'])} entities")

    return config_entries, {"has_changes": has_changes}


def main():
    parser = argparse.ArgumentParser(
        description="Update HomeKit Bridge exposure settings"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying"
    )
    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    config_path = script_dir / "config" / "homekit_exposed.yaml"

    if not config_path.exists():
        print(f"Error: {config_path} not found")
        sys.exit(1)

    # Load config
    print(f"Loading HomeKit config from {config_path}")
    filter_config = load_homekit_config(config_path)
    print(f"  include_domains: {filter_config['include_domains']}")
    print(f"  include_entities: {len(filter_config['include_entities'])} entities")
    print(f"  exclude_entities: {len(filter_config['exclude_entities'])} entities")

    # Get server from env
    server = os.environ.get("HA_SERVER", "root@homeassistant")
    print(f"\nConnecting to {server}...")

    # Download config entries
    print("Downloading config entries...")
    config_entries = download_config_entries(server)

    # Update HomeKit filter
    updated_entries, result = update_homekit_filter(
        config_entries, filter_config, dry_run=args.dry_run
    )

    if args.dry_run:
        print("\nDry run - no changes made")
        return

    if not result["has_changes"]:
        print("\nNo changes to apply")
        return

    # Upload config entries
    print("\nUploading config entries...")
    upload_config_entries(server, updated_entries)
    print("Done! Restart HA for changes to take effect: just config::restart")


if __name__ == "__main__":
    main()
