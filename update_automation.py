#!/usr/bin/env python3
"""
Generic script to update Home Assistant automations.yaml
Workflow: Pull from server → Edit locally → Push back

Usage:
  # Update from a local split file
  python update_automation.py automations/bathroom_presence.yaml

  # Update multiple files
  python update_automation.py automations/*.yaml
"""

import yaml
import sys
import subprocess
from pathlib import Path

SERVER = "root@homeassistant"
SERVER_PATH = "/config/automations.yaml"
LOCAL_TEMP = "/tmp/automations.yaml"


def download_automations():
    """Download current automations.yaml from server"""
    print("📥 Downloading current automations from server...")
    result = subprocess.run(
        ["scp", f"{SERVER}:{SERVER_PATH}", LOCAL_TEMP], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to download: {result.stderr}")
        sys.exit(1)
    print("✅ Downloaded")


def upload_automations():
    """Upload modified automations.yaml back to server"""
    print("📤 Uploading updated automations to server...")
    result = subprocess.run(
        ["scp", LOCAL_TEMP, f"{SERVER}:{SERVER_PATH}"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to upload: {result.stderr}")
        sys.exit(1)
    print("✅ Uploaded")


def update_automation_from_file(local_file):
    """
    Update an automation in the server file using a local split file as source

    Args:
        local_file: Path to local split automation file (e.g., automations/bathroom_presence.yaml)
    """
    local_path = Path(local_file)
    if not local_path.exists():
        print(f"❌ Local file not found: {local_file}")
        return False

    # Read the local automation file (single automation)
    with open(local_path) as f:
        local_auto = yaml.safe_load(f)

    if not local_auto or "id" not in local_auto:
        print(f"❌ Invalid automation file (missing id): {local_file}")
        return False

    automation_id = local_auto["id"]
    automation_alias = local_auto.get("alias", "Unknown")

    # Read server automations (list of automations)
    with open(LOCAL_TEMP) as f:
        server_autos = yaml.safe_load(f)

    if not isinstance(server_autos, list):
        print("❌ Server automations.yaml is not a list")
        return False

    # Find and replace the automation by ID
    found = False
    for i, auto in enumerate(server_autos):
        if auto.get("id") == automation_id:
            print(f"✏️  Updating: {automation_alias} (id: {automation_id})")
            server_autos[i] = local_auto
            found = True
            break

    if not found:
        print(
            f"❌ Automation not found on server: {automation_alias} (id: {automation_id})"
        )
        return False

    # Write back to temp file
    with open(LOCAL_TEMP, "w") as f:
        yaml.dump(
            server_autos,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    print(f"✅ Updated: {automation_alias}")
    return True


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python update_automation.py <automation_file> [<automation_file2> ...]"
        )
        print("Example: python update_automation.py automations/bathroom_presence.yaml")
        sys.exit(1)

    # Download current automations from server
    download_automations()

    # Process each file
    updated_count = 0
    for file_path in sys.argv[1:]:
        if update_automation_from_file(file_path):
            updated_count += 1

    if updated_count > 0:
        # Upload modified automations back to server
        upload_automations()
        print(f"✅ Successfully updated {updated_count} automation(s)")
    else:
        print("❌ No automations were updated")
        sys.exit(1)


if __name__ == "__main__":
    main()
