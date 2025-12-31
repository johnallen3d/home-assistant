#!/usr/bin/env python3
"""
Sync Home Assistant devices to Homebox inventory.

This script:
1. Fetches device and area data live from Home Assistant API
2. Creates/updates locations in Homebox from HA areas
3. Creates/updates inventory items in Homebox from HA devices
4. Filters out virtual devices (HA components, plugins, integrations)

Usage:
    # Set environment variables (or use .env file)
    export HOMEBOX_URL="https://homebox.example.com"
    export HOMEBOX_TOKEN="your-token"
    export HA_URL="http://homeassistant.local:8123"
    export HA_TOKEN="your-long-lived-access-token"

    # Dry run (show what would change)
    python ha_to_homebox.py --dry-run

    # Sync devices
    python ha_to_homebox.py

    # Force update all items (even if they exist)
    python ha_to_homebox.py --force-update
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import requests

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


# Patterns for filtering out virtual/system devices
EXCLUDE_PATTERNS = [
    # HA system components
    r"^Home Assistant",
    r"^HASS Bridge:",
    r"^Backup$",
    # HACS and plugins
    r"^HACS$",
    r"model.*plugin$",
    r"model.*theme$",
    r"model.*integration$",
    # Add-ons
    r"^(Tailscale|Studio Code Server|Terminal & SSH|Whisper|Piper|openWakeWord)$",
    r"^(Matter Server|Mosquitto broker|Music Assistant|ESPHome Device Builder)$",
    r"^(Claude Terminal|Beszel-Agent)$",
    # Virtual entities
    r"^Sun$",
    r"^Forecast$",
    # Mobile devices (phones, tablets, watches)
    r"iPhone",
    r"iPad",
    r"Watch",
    # Cryptic/auto-generated names
    r"^[A-Z0-9]{8,}",  # All caps/numbers like "WSBC018418804T 130A"
    r"^Nuki_[A-F0-9]+$",  # Nuki auto-names
    r"^hci\d",  # Bluetooth adapters
    r"\([0-9A-F]{2}:[0-9A-F]{2}:",  # MAC addresses in names
    # Hue rooms (we want bulbs, not room groups)
    r"^(Kitchen|Bathroom|Bedroom|Living Room)$",  # Bare room names from Hue
    # Duplicate LG entries (keep the one with manufacturer "LG")
    r"^\[LG\]",
    # Computers and network devices (not smart home)
    r"macbook",
    r"\.local$",
    r"-net$",  # Network names
    # Emoji-only names
    r"^[\U0001F300-\U0001F9FF]+$",  # Emoji only
    # eero profiles (not devices)
    r"^(eero|beltalowda)",
]

EXCLUDE_MANUFACTURERS = [
    # These are typically integration metadata, not physical devices
    "piitaya",  # Mushroom plugin
    "basnijholt",  # iOS themes
    "vasqued2",  # Team Tracker
    "Madelena",  # Metrology theme
    "Clooos",  # Bubble Card
    "krahabb",  # Meross LAN integration
    "sopelj",  # Ember Mug integration
    "AlexandrErohin",  # TP-Link Router integration
    "koush",  # Scrypted integration
    "schmittx",  # eero integration
    "andrew-codechimp",  # Battery Notes
    "PiotrMachowski",  # Xiaomi Cloud Map
    "homeassistant-extras",  # Pi-hole Card
    "NemesisRE",  # Kiosk Mode
    "Flight-Lab",  # Ember Mug Card
    "bauer-group",  # S3 Backup
]

# Models that indicate virtual/integration entities
EXCLUDE_MODELS = [
    "plugin",
    "theme",
    "integration",
    "Home Assistant Add-on",
]


@dataclass
class HomeboxConfig:
    url: str
    token: str

    @property
    def api_url(self) -> str:
        return f"{self.url.rstrip('/')}/api/v1"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


@dataclass
class HAConfig:
    url: str
    token: str

    @property
    def api_url(self) -> str:
        return f"{self.url.rstrip('/')}/api"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


class HomeboxClient:
    """Client for interacting with Homebox API."""

    def __init__(self, config: HomeboxConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)

    def _get(self, endpoint: str) -> dict:
        resp = self.session.get(f"{self.config.api_url}{endpoint}")
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint: str, data: dict) -> dict:
        resp = self.session.post(f"{self.config.api_url}{endpoint}", json=data)
        resp.raise_for_status()
        return resp.json()

    def _put(self, endpoint: str, data: dict) -> dict:
        resp = self.session.put(f"{self.config.api_url}{endpoint}", json=data)
        resp.raise_for_status()
        return resp.json()

    def get_locations(self) -> list[dict]:
        """Get all locations."""
        return self._get("/locations")

    def create_location(self, name: str, description: str = "") -> dict:
        """Create a new location."""
        return self._post("/locations", {"name": name, "description": description})

    def get_items(self) -> list[dict]:
        """Get all items."""
        response = self._get("/items")
        if isinstance(response, dict) and "items" in response:
            return response["items"]
        return response

    def create_item(
        self,
        name: str,
        location_id: Optional[str] = None,
        description: str = "",
        manufacturer: str = "",
        model: str = "",
        serial_number: str = "",
        notes: str = "",
        quantity: int = 1,
    ) -> dict:
        """Create a new inventory item."""
        item_data = {"name": name, "description": description, "quantity": quantity}
        if location_id:
            item_data["locationId"] = location_id

        item = self._post("/items", item_data)
        item_id = item["id"]

        update_data = {
            "id": item_id,
            "name": name,
            "description": description,
            "manufacturer": manufacturer or "",
            "modelNumber": model or "",
            "serialNumber": serial_number or "",
            "notes": notes or "",
            "quantity": quantity,
        }
        if location_id:
            update_data["locationId"] = location_id

        return self._put(f"/items/{item_id}", update_data)

    def update_item(
        self,
        item_id: str,
        name: str,
        location_id: Optional[str] = None,
        description: str = "",
        manufacturer: str = "",
        model: str = "",
        notes: str = "",
        quantity: int = 1,
    ) -> dict:
        """Update an existing item."""
        update_data = {
            "id": item_id,
            "name": name,
            "description": description,
            "manufacturer": manufacturer or "",
            "modelNumber": model or "",
            "notes": notes or "",
            "quantity": quantity,
        }
        if location_id:
            update_data["locationId"] = location_id

        return self._put(f"/items/{item_id}", update_data)


class HAClient:
    """Client for interacting with Home Assistant API."""

    def __init__(self, config: HAConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)

    def _ws_call(self, msg_type: str) -> dict:
        """Make a websocket-style call via REST API."""
        # HA exposes some websocket commands via REST
        resp = self.session.get(f"{self.config.api_url}/config")
        resp.raise_for_status()
        return resp.json()

    def get_devices(self) -> list[dict]:
        """Get all devices from device registry."""
        # Use the REST API endpoint for device registry
        resp = self.session.get(f"{self.config.api_url}/states")
        resp.raise_for_status()

        # Unfortunately, the simple REST API doesn't expose device registry directly
        # We need to use the websocket API via a different approach
        # Let's try the template API to get device info

        # Alternative: call the config API
        try:
            # Try the new REST API for device registry (HA 2023.3+)
            resp = self.session.get(
                f"{self.config.api_url}/config/device_registry",
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass

        # Fallback: Use websocket via REST proxy if available
        # This requires the HA instance to have the REST API properly configured
        raise NotImplementedError(
            "Device registry API not available. "
            "Please ensure your HA token has admin access."
        )

    def get_areas(self) -> list[dict]:
        """Get all areas from area registry."""
        try:
            resp = self.session.get(
                f"{self.config.api_url}/config/area_registry",
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass

        raise NotImplementedError("Area registry API not available.")


def fetch_ha_data_via_websocket(ha_url: str, ha_token: str) -> tuple[list[dict], list[dict]]:
    """
    Fetch HA data using websocket API.

    This is more reliable than REST API for registry access.
    """
    import websocket
    import json
    import ssl

    ws_url = ha_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url}/api/websocket"

    devices = []
    areas = []
    msg_id = 1

    def send_and_receive(ws, msg_type: str) -> dict:
        nonlocal msg_id
        ws.send(json.dumps({"id": msg_id, "type": msg_type}))
        while True:
            result = json.loads(ws.recv())
            if result.get("id") == msg_id:
                msg_id += 1
                return result

    try:
        ws = websocket.create_connection(
            ws_url,
            sslopt={"cert_reqs": ssl.CERT_NONE} if "wss://" in ws_url else {}
        )

        # Auth phase
        auth_msg = json.loads(ws.recv())
        if auth_msg["type"] == "auth_required":
            ws.send(json.dumps({"type": "auth", "access_token": ha_token}))
            auth_result = json.loads(ws.recv())
            if auth_result["type"] != "auth_ok":
                raise Exception(f"Auth failed: {auth_result}")

        # Get devices
        result = send_and_receive(ws, "config/device_registry/list")
        if result.get("success"):
            devices = result.get("result", [])

        # Get areas
        result = send_and_receive(ws, "config/area_registry/list")
        if result.get("success"):
            areas = result.get("result", [])

        ws.close()

    except ImportError:
        raise ImportError(
            "websocket-client package required. Install with: pip install websocket-client"
        )

    return devices, areas


def is_physical_device(device: dict) -> bool:
    """Check if a device is a physical device (not virtual/integration)."""
    name = device.get("name") or device.get("name_by_user") or ""
    manufacturer = device.get("manufacturer") or ""
    model = device.get("model") or ""

    # Check exclusion patterns for name
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return False

    # Check excluded manufacturers
    if manufacturer in EXCLUDE_MANUFACTURERS:
        return False

    # Check excluded models
    for excluded_model in EXCLUDE_MODELS:
        if excluded_model.lower() in (model or "").lower():
            return False

    # Exclude devices with no name
    if not name:
        return False

    # Exclude disabled devices
    if device.get("disabled_by"):
        return False

    return True


def sync_locations(
    client: HomeboxClient,
    areas: list[dict],
    dry_run: bool = False
) -> dict[str, str]:
    """Create Homebox locations from HA areas."""
    print("\n=== Syncing Locations ===")

    existing = {loc["name"]: loc["id"] for loc in client.get_locations()}
    print(f"Found {len(existing)} existing locations in Homebox")

    area_to_location = {}

    for area in areas:
        name = area.get("name", "")
        area_id = area.get("area_id", "")

        if not name:
            continue

        if name in existing:
            print(f"  [EXISTS] {name}")
            area_to_location[area_id] = existing[name]
        else:
            if dry_run:
                print(f"  [DRY-RUN] Would create: {name}")
                area_to_location[area_id] = f"dry-run-{area_id}"
            else:
                print(f"  [CREATE] {name}")
                location = client.create_location(
                    name, f"Imported from Home Assistant area: {area_id}"
                )
                area_to_location[area_id] = location["id"]

    return area_to_location


def sync_devices(
    client: HomeboxClient,
    devices: list[dict],
    area_to_location: dict[str, str],
    dry_run: bool = False,
    force_update: bool = False,
) -> None:
    """Create/update Homebox items from HA devices."""
    print("\n=== Syncing Devices ===")

    existing_items = client.get_items()
    existing_by_name = {item["name"]: item for item in existing_items}
    print(f"Found {len(existing_items)} existing items in Homebox")

    # Filter to physical devices only
    physical_devices = [d for d in devices if is_physical_device(d)]
    print(f"Processing {len(physical_devices)} physical devices (filtered from {len(devices)} total)")

    created = 0
    updated = 0
    skipped = 0

    for device in physical_devices:
        name = device.get("name_by_user") or device.get("name") or ""
        if not name:
            continue

        manufacturer = device.get("manufacturer") or ""
        model = device.get("model") or ""
        area_id = device.get("area_id")
        device_id = device.get("id") or device.get("device_id") or ""

        location_id = area_to_location.get(area_id) if area_id else None

        notes_parts = []
        if device_id:
            notes_parts.append(f"HA Device ID: {device_id}")
        labels = device.get("labels", [])
        if labels:
            notes_parts.append(f"HA Labels: {', '.join(labels)}")
        notes = "\n".join(notes_parts)

        description = f"{manufacturer} {model}".strip()

        if name in existing_by_name:
            existing = existing_by_name[name]
            existing_loc_id = existing.get("location", {}).get("id")
            existing_qty = existing.get("quantity", 0)

            # Check if update needed
            needs_update = (
                force_update
                or (location_id and existing_loc_id != location_id)
                or existing_qty == 0  # Fix items with quantity=0
            )

            if needs_update:
                if dry_run:
                    old_loc = existing.get("location", {}).get("name", "None")
                    new_loc = area_id or "None"
                    print(f"  [DRY-RUN] Would update: {name} ({old_loc} -> {new_loc})")
                else:
                    print(f"  [UPDATE] {name}")
                    try:
                        client.update_item(
                            item_id=existing["id"],
                            name=name,
                            location_id=location_id,
                            description=description,
                            manufacturer=manufacturer,
                            model=model,
                            notes=notes,
                        )
                        updated += 1
                    except requests.HTTPError as e:
                        print(f"    [ERROR] Failed to update {name}: {e}")
            else:
                print(f"  [EXISTS] {name}")
                skipped += 1
        else:
            if dry_run:
                loc_name = area_id or "None"
                print(f"  [DRY-RUN] Would create: {name} ({manufacturer}) -> {loc_name}")
            else:
                print(f"  [CREATE] {name}")
                try:
                    client.create_item(
                        name=name,
                        location_id=location_id,
                        description=description,
                        manufacturer=manufacturer,
                        model=model,
                        notes=notes,
                    )
                    created += 1
                except requests.HTTPError as e:
                    print(f"    [ERROR] Failed to create {name}: {e}")

    print(f"\nSummary: Created {created}, Updated {updated}, Skipped {skipped}")


def main():
    parser = argparse.ArgumentParser(
        description="Sync Home Assistant devices to Homebox inventory"
    )
    parser.add_argument(
        "--homebox-url",
        default=os.environ.get("HOMEBOX_URL"),
        help="Homebox server URL",
    )
    parser.add_argument(
        "--homebox-token",
        default=os.environ.get("HOMEBOX_TOKEN"),
        help="Homebox API token (without 'Bearer ' prefix)",
    )
    parser.add_argument(
        "--ha-url",
        default=os.environ.get("HA_URL", "http://homeassistant.local:8123"),
        help="Home Assistant URL",
    )
    parser.add_argument(
        "--ha-token",
        default=os.environ.get("HA_TOKEN") or os.environ.get("HOME_ASSISTANT_API_KEY"),
        help="Home Assistant Long-Lived Access Token",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Update all existing items (not just location changes)",
    )
    args = parser.parse_args()

    # Validate required args
    if not args.homebox_url:
        print("Error: --homebox-url or HOMEBOX_URL required")
        sys.exit(1)
    if not args.homebox_token:
        print("Error: --homebox-token or HOMEBOX_TOKEN required")
        sys.exit(1)
    if not args.ha_token:
        print("Error: --ha-token or HA_TOKEN required")
        print("\nTo create a Long-Lived Access Token:")
        print("  1. Go to your HA profile (click your name in sidebar)")
        print("  2. Scroll to 'Long-Lived Access Tokens'")
        print("  3. Click 'Create Token'")
        sys.exit(1)

    # Clean up tokens
    homebox_token = args.homebox_token
    if homebox_token.startswith("Bearer "):
        homebox_token = homebox_token[7:]

    # Connect to Homebox
    hb_config = HomeboxConfig(url=args.homebox_url, token=homebox_token)
    hb_client = HomeboxClient(hb_config)

    print(f"Connecting to Homebox at {hb_config.api_url}...")
    try:
        locations = hb_client.get_locations()
        print(f"Connected! Found {len(locations)} existing locations.")
    except requests.HTTPError as e:
        print(f"Error connecting to Homebox: {e}")
        sys.exit(1)

    # Fetch HA data
    print(f"\nFetching data from Home Assistant at {args.ha_url}...")
    try:
        devices, areas = fetch_ha_data_via_websocket(args.ha_url, args.ha_token)
        print(f"Loaded {len(devices)} devices and {len(areas)} areas from Home Assistant")
    except ImportError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching HA data: {e}")
        sys.exit(1)

    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***")

    # Sync
    area_to_location = sync_locations(hb_client, areas, dry_run=args.dry_run)
    sync_devices(
        hb_client, devices, area_to_location,
        dry_run=args.dry_run, force_update=args.force_update
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
