#!/usr/bin/env python3
"""
Script to delete scenes from Home Assistant scenes.yaml by name.
Workflow: Pull from server → Delete matching scenes → Push back

Usage:
  # Delete by name
  python delete_scene.py "Daytime potty"

  # Delete multiple scenes
  python delete_scene.py "Daytime potty" "Nighttime potty" "TV Time"
"""

import yaml
import sys
import subprocess
import os

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


def delete_scenes_by_name(names_to_delete: list[str]) -> int:
    """
    Delete scenes from the server file by name.

    Args:
        names_to_delete: List of scene names to delete

    Returns:
        Number of scenes deleted
    """
    # Read server scenes
    with open(LOCAL_TEMP) as f:
        scenes = yaml.safe_load(f)

    if not isinstance(scenes, list):
        print("❌ Server scenes.yaml is not a list")
        sys.exit(1)

    original_count = len(scenes)
    names_set = set(names_to_delete)

    # Filter out scenes to delete
    remaining_scenes = []
    deleted_names = []
    for scene in scenes:
        name = scene.get("name", "")
        if name in names_set:
            deleted_names.append(name)
            print(f"🗑️  Deleting: {name}")
        else:
            remaining_scenes.append(scene)

    deleted_count = original_count - len(remaining_scenes)

    if deleted_count == 0:
        print(f"⚠️  No matching scenes found for: {names_to_delete}")
        return 0

    # Report any names that weren't found
    not_found = names_set - set(deleted_names)
    for name in not_found:
        print(f"⚠️  Scene not found: {name}")

    # Write back
    with open(LOCAL_TEMP, "w") as f:
        yaml.dump(
            remaining_scenes,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return deleted_count


def main():
    if len(sys.argv) < 2:
        print("Usage: python delete_scene.py <scene_name> [<scene_name2> ...]")
        print('Example: python delete_scene.py "Daytime potty" "Nighttime potty"')
        sys.exit(1)

    scene_names = sys.argv[1:]

    # Download current scenes from server
    download_scenes()

    # Delete scenes
    deleted_count = delete_scenes_by_name(scene_names)

    if deleted_count > 0:
        upload_scenes()
        print(f"✅ Successfully deleted {deleted_count} scene(s)")
    else:
        print("❌ No scenes were deleted")
        sys.exit(1)


if __name__ == "__main__":
    main()
