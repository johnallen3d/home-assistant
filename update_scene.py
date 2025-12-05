#!/usr/bin/env python3
"""
Script to update Home Assistant scenes.yaml
Workflow: Pull from server → Update from local file → Push back

Usage:
  # Update from a local split file
  python update_scene.py scenes/alarm.yaml

  # Update multiple files
  python update_scene.py scenes/*.yaml
"""

import yaml
import sys
import subprocess
import os
from pathlib import Path

# Use environment variables from .env (loaded by justfile)
SERVER = os.environ["HA_SERVER"]
CONFIG_PATH = os.environ["HA_CONFIG_PATH"]
SERVER_PATH = f"{CONFIG_PATH}/scenes.yaml"
LOCAL_TEMP = "/tmp/scenes.yaml"


def download_scenes():
    """Download current scenes.yaml from server"""
    print("📥 Downloading current scenes from server...")
    result = subprocess.run(
        ["scp", f"{SERVER}:{SERVER_PATH}", LOCAL_TEMP], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to download: {result.stderr}")
        sys.exit(1)
    print("✅ Downloaded")


def upload_scenes():
    """Upload modified scenes.yaml back to server"""
    print("📤 Uploading updated scenes to server...")
    result = subprocess.run(
        ["scp", LOCAL_TEMP, f"{SERVER}:{SERVER_PATH}"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to upload: {result.stderr}")
        sys.exit(1)
    print("✅ Uploaded")


def update_scene_from_file(local_file):
    """
    Update a scene in the server file using a local split file as source

    Args:
        local_file: Path to local split scene file (e.g., scenes/alarm.yaml)
    """
    local_path = Path(local_file)
    if not local_path.exists():
        print(f"❌ Local file not found: {local_file}")
        return False

    # Read the local scene file (single scene)
    with open(local_path) as f:
        local_scene = yaml.safe_load(f)

    if not local_scene or "id" not in local_scene:
        print(f"❌ Invalid scene file (missing id): {local_file}")
        return False

    scene_id = local_scene["id"]
    scene_name = local_scene.get("name", "Unknown")

    # Read server scenes (list of scenes)
    with open(LOCAL_TEMP) as f:
        server_scenes = yaml.safe_load(f)

    if not isinstance(server_scenes, list):
        print("❌ Server scenes.yaml is not a list")
        return False

    # Find and replace the scene by ID
    found = False
    for i, scene in enumerate(server_scenes):
        if scene.get("id") == scene_id:
            print(f"✏️  Updating: {scene_name} (id: {scene_id})")
            server_scenes[i] = local_scene
            found = True
            break

    if not found:
        print(f"❌ Scene not found on server: {scene_name} (id: {scene_id})")
        return False

    # Write back to temp file
    with open(LOCAL_TEMP, "w") as f:
        yaml.dump(
            server_scenes,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    print(f"✅ Updated: {scene_name}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_scene.py <scene_file> [<scene_file2> ...]")
        print("Example: python update_scene.py scenes/alarm.yaml")
        sys.exit(1)

    # Download current scenes from server
    download_scenes()

    # Process each file
    updated_count = 0
    for file_path in sys.argv[1:]:
        if update_scene_from_file(file_path):
            updated_count += 1

    if updated_count > 0:
        # Upload modified scenes back to server
        upload_scenes()
        print(f"✅ Successfully updated {updated_count} scene(s)")
    else:
        print("❌ No scenes were updated")
        sys.exit(1)


if __name__ == "__main__":
    main()
