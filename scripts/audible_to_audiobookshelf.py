#!/usr/bin/env python3
"""
Sync Audible library progress to Audiobookshelf.

Usage:
    # First time: authenticate with Audible
    python audible_to_audiobookshelf.py auth

    # Extract Audible library (saves to audible_library.json)
    python audible_to_audiobookshelf.py extract

    # Compare with Audiobookshelf (requires ABS_URL and ABS_TOKEN env vars)
    python audible_to_audiobookshelf.py compare

    # Sync progress to Audiobookshelf
    python audible_to_audiobookshelf.py sync
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import audible
import requests
from dotenv import load_dotenv

load_dotenv()

# Paths
SCRIPT_DIR = Path(__file__).parent
AUTH_FILE = SCRIPT_DIR / "audible_auth.json"
LIBRARY_FILE = SCRIPT_DIR / "audible_library.json"

# Audiobookshelf config
ABS_URL = os.getenv("ABS_URL", "").rstrip("/")
ABS_TOKEN = os.getenv("ABS_TOKEN", "")


def authenticate():
    """Interactive authentication with Audible using external browser."""
    print("Starting Audible authentication...")
    print("A browser window will open for you to log in to Amazon.\n")

    auth = audible.Authenticator.from_login_external(locale="us")

    # Save credentials
    auth.to_file(AUTH_FILE)
    print(f"\nAuthentication successful! Credentials saved to {AUTH_FILE}")
    return auth


def get_auth():
    """Load existing authentication or create new."""
    if AUTH_FILE.exists():
        try:
            auth = audible.Authenticator.from_file(AUTH_FILE)
            print(f"Loaded existing auth from {AUTH_FILE}")
            return auth
        except Exception as e:
            print(f"Failed to load auth: {e}")
            print("Re-authenticating...")

    return authenticate()


def extract_library():
    """Extract library directly from Audible API with full progress data."""
    auth = audible.Authenticator.from_file(Path.home() / ".audible" / "audible.json")

    with audible.Client(auth=auth) as client:
        print("Fetching library from Audible API...")
        library = client.get(
            "1.0/library",
            num_results=1000,
            response_groups="listening_status,is_finished,product_desc",
        )

        items = library.get("items", [])
        print(f"Found {len(items)} items")

        # Process and categorize
        processed = []
        stats = {"finished": 0, "in_progress": 0, "not_started": 0}

        for item in items:
            ls = item.get("listening_status") or {}
            pct = ls.get("percent_complete", 0) or 0
            is_finished = item.get("is_finished", False)

            if is_finished:
                state = "finished"
                stats["finished"] += 1
            elif pct > 0:
                state = "in_progress"
                stats["in_progress"] += 1
            else:
                state = "not_started"
                stats["not_started"] += 1

            processed.append({
                "asin": item.get("asin", ""),
                "title": item.get("title", "Unknown"),
                "is_finished": is_finished,
                "percent_complete": pct,
                "state": state,
            })

        # Save to file
        output = {
            "extracted_at": datetime.now().isoformat(),
            "total_items": len(processed),
            "stats": stats,
            "items": processed,
        }

        with open(LIBRARY_FILE, "w") as f:
            json.dump(output, f, indent=2)

        print(f"\nLibrary saved to {LIBRARY_FILE}")
        print(f"\nStats:")
        print(f"  Finished:    {stats['finished']}")
        print(f"  In progress: {stats['in_progress']}")
        print(f"  Not started: {stats['not_started']}")
        print(f"  Total:       {len(processed)}")

        return output


def get_audiobookshelf_library():
    """Fetch library from Audiobookshelf with user progress."""
    if not ABS_URL or not ABS_TOKEN:
        print("Error: ABS_URL and ABS_TOKEN environment variables required")
        print("Set them in .env or environment")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {ABS_TOKEN}"}

    # Get user's media progress
    resp = requests.get(f"{ABS_URL}/api/me", headers=headers)
    resp.raise_for_status()
    user_data = resp.json()

    # Build progress lookup by libraryItemId
    progress_by_item = {}
    for p in user_data.get("mediaProgress", []):
        progress_by_item[p["libraryItemId"]] = {
            "is_finished": p.get("isFinished", False),
            "progress": p.get("progress", 0),
            "current_time": p.get("currentTime", 0),
        }

    # Get all libraries
    resp = requests.get(f"{ABS_URL}/api/libraries", headers=headers)
    resp.raise_for_status()
    libraries = resp.json().get("libraries", [])

    all_items = []

    for lib in libraries:
        lib_id = lib["id"]
        lib_name = lib["name"]
        print(f"Fetching library: {lib_name}")

        # Get all items in this library
        resp = requests.get(
            f"{ABS_URL}/api/libraries/{lib_id}/items",
            headers=headers,
            params={"limit": 0},
        )
        resp.raise_for_status()

        items = resp.json().get("results", [])
        print(f"  Found {len(items)} items")

        for item in items:
            item_id = item["id"]
            progress = progress_by_item.get(item_id, {"is_finished": False, "progress": 0, "current_time": 0})

            all_items.append({
                "id": item_id,
                "library_id": lib_id,
                "library_name": lib_name,
                "title": item.get("media", {}).get("metadata", {}).get("title", ""),
                "authors": [a.get("name", "") for a in item.get("media", {}).get("metadata", {}).get("authors", [])],
                "asin": item.get("media", {}).get("metadata", {}).get("asin", ""),
                "is_finished": progress["is_finished"],
                "progress": progress["progress"],
                "current_time": progress["current_time"],
            })

    return all_items


def compare():
    """Compare Audible library with Audiobookshelf."""
    # Load Audible data
    if not LIBRARY_FILE.exists():
        print(f"No library file found at {LIBRARY_FILE}")
        print("Run 'extract' command first")
        sys.exit(1)

    with open(LIBRARY_FILE) as f:
        data = json.load(f)

    # Handle both old flat format and new wrapped format
    if isinstance(data, list):
        audible_items = data
        aud_stats = None
    else:
        audible_items = data.get("items", [])
        aud_stats = data.get("stats")

    # Count stats if not available
    if not aud_stats:
        aud_stats = {"finished": 0, "in_progress": 0, "not_started": 0}
        for item in audible_items:
            if item.get("is_finished", False):
                aud_stats["finished"] += 1
            elif item.get("percent_complete", 0) > 0:
                aud_stats["in_progress"] += 1
            else:
                aud_stats["not_started"] += 1

    print(f"Audible: {len(audible_items)} items")
    print(f"  Finished: {aud_stats['finished']}, In progress: {aud_stats.get('in_progress', 0)}, Not started: {aud_stats.get('not_started', 0)}")

    # Fetch Audiobookshelf
    abs_items = get_audiobookshelf_library()
    print(f"\nAudiobookshelf: {len(abs_items)} items")

    # Stats for Audiobookshelf
    abs_stats = {"finished": 0, "has_progress": 0, "no_progress": 0}
    for item in abs_items:
        if item["is_finished"]:
            abs_stats["finished"] += 1
        elif item["progress"] > 0 or item["current_time"] > 0:
            abs_stats["has_progress"] += 1
        else:
            abs_stats["no_progress"] += 1

    print(f"  Finished: {abs_stats['finished']}, Has progress: {abs_stats['has_progress']}, No progress: {abs_stats['no_progress']}")

    # Try to match by ASIN
    abs_by_asin = {item["asin"]: item for item in abs_items if item["asin"]}

    matched = 0
    unmatched_audible = []
    needs_update = []

    for aud_item in audible_items:
        asin = aud_item.get("asin", "")
        if asin in abs_by_asin:
            matched += 1
            abs_item = abs_by_asin[asin]

            aud_finished = aud_item.get("is_finished", False)
            aud_pct = aud_item.get("percent_complete", 0) or 0
            abs_finished = abs_item["is_finished"]
            abs_progress = abs_item["progress"]
            abs_current_time = abs_item["current_time"]

            # Check if update needed
            if aud_finished and not abs_finished:
                needs_update.append({
                    "title": aud_item.get("title", "Unknown"),
                    "asin": asin,
                    "abs_id": abs_item["id"],
                    "action": "mark_finished",
                    "aud_pct": aud_pct,
                })
            elif aud_pct > 0 and not abs_finished and abs_progress == 0 and abs_current_time == 0:
                # Has progress in Audible but none in ABS
                needs_update.append({
                    "title": aud_item.get("title", "Unknown"),
                    "asin": asin,
                    "abs_id": abs_item["id"],
                    "action": "set_progress",
                    "aud_pct": aud_pct,
                })
        else:
            unmatched_audible.append(aud_item)

    # Categorize updates
    to_finish = [u for u in needs_update if u["action"] == "mark_finished"]
    to_progress = [u for u in needs_update if u["action"] == "set_progress"]

    print(f"\nMatching:")
    print(f"  Matched by ASIN: {matched}")
    print(f"  Unmatched Audible items: {len(unmatched_audible)}")
    print(f"\nUpdates needed:")
    print(f"  Mark as finished: {len(to_finish)}")
    print(f"  Set progress: {len(to_progress)}")

    if unmatched_audible:
        print(f"\nFirst 5 unmatched (no ASIN match in ABS):")
        for item in unmatched_audible[:5]:
            print(f"  - {item.get('title', 'Unknown')[:60]} (ASIN: {item.get('asin', 'N/A')})")

    return {
        "audible_stats": aud_stats,
        "abs_stats": abs_stats,
        "matched": matched,
        "unmatched": len(unmatched_audible),
        "needs_update": needs_update,
    }


def sync(dry_run=False):
    """Sync Audible progress to Audiobookshelf."""
    # Run compare to get what needs updating
    result = compare()
    needs_update = result["needs_update"]

    if not needs_update:
        print("\nNothing to sync - all matched items are already correct!")
        return

    # Categorize
    to_finish = [u for u in needs_update if u["action"] == "mark_finished"]
    to_progress = [u for u in needs_update if u["action"] == "set_progress"]

    print(f"\n{'DRY RUN - ' if dry_run else ''}Sync plan:")
    print(f"  Mark finished: {len(to_finish)}")
    print(f"  Set progress: {len(to_progress)}")

    if dry_run:
        if to_finish:
            print("\nWould mark as finished:")
            for item in to_finish[:10]:
                print(f"  - {item['title'][:60]}")
            if len(to_finish) > 10:
                print(f"  ... and {len(to_finish) - 10} more")

        if to_progress:
            print("\nWould set progress:")
            for item in sorted(to_progress, key=lambda x: -x["aud_pct"])[:10]:
                print(f"  - {item['aud_pct']:5.1f}% {item['title'][:55]}")
            if len(to_progress) > 10:
                print(f"  ... and {len(to_progress) - 10} more")
        return

    headers = {"Authorization": f"Bearer {ABS_TOKEN}"}

    updated = 0
    errors = 0

    # Process finished items
    for item in to_finish:
        try:
            resp = requests.patch(
                f"{ABS_URL}/api/me/progress/{item['abs_id']}",
                headers=headers,
                json={"isFinished": True},
            )
            resp.raise_for_status()
            updated += 1
            print(f"  ✓ [finished] {item['title'][:55]}")
        except Exception as e:
            errors += 1
            print(f"  ✗ {item['title'][:40]}: {e}")

    # Process in-progress items
    for item in to_progress:
        try:
            pct = item["aud_pct"]
            progress = pct / 100.0

            # Get item duration for currentTime calculation
            item_resp = requests.get(
                f"{ABS_URL}/api/items/{item['abs_id']}",
                headers=headers,
            )
            duration = 0
            if item_resp.ok:
                media = item_resp.json().get("media", {})
                # Try direct duration first, then sum from audio files
                duration = media.get("duration", 0)
                if not duration:
                    audio_files = media.get("audioFiles", [])
                    duration = sum(f.get("duration", 0) for f in audio_files)

            current_time = duration * progress

            # Treat >95% as finished
            if pct > 95:
                resp = requests.patch(
                    f"{ABS_URL}/api/me/progress/{item['abs_id']}",
                    headers=headers,
                    json={"progress": 1.0, "currentTime": duration, "isFinished": True},
                )
                resp.raise_for_status()
                updated += 1
                print(f"  ✓ [{pct:5.1f}% → finished] {item['title'][:50]}")
            else:
                resp = requests.patch(
                    f"{ABS_URL}/api/me/progress/{item['abs_id']}",
                    headers=headers,
                    json={"progress": progress, "currentTime": current_time, "isFinished": False},
                )
                resp.raise_for_status()
                updated += 1
                print(f"  ✓ [{pct:5.1f}%] {item['title'][:55]}")
        except Exception as e:
            errors += 1
            print(f"  ✗ {item['title'][:40]}: {e}")

    print(f"\nSync complete:")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")


def main():
    parser = argparse.ArgumentParser(description="Sync Audible to Audiobookshelf")
    parser.add_argument(
        "command",
        choices=["auth", "extract", "compare", "sync"],
        help="Command to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )

    args = parser.parse_args()

    if args.command == "auth":
        authenticate()
    elif args.command == "extract":
        extract_library()
    elif args.command == "compare":
        compare()
    elif args.command == "sync":
        sync(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
