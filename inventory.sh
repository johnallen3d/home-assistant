#!/bin/bash

# Home Assistant Inventory Script
# This script connects to your Home Assistant instance and extracts information about integrations, devices, and entities

HA_HOST="homeassistant"
OUTPUT_DIR="./inventory"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🏠 Home Assistant Inventory Script"
echo "=================================="
echo "Connecting to Home Assistant at: $HA_HOST"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Function to fetch data from Home Assistant
fetch_ha_data() {
    local file_path=$1
    local description=$2
    echo "📥 Fetching $description..."
    ssh root@$HA_HOST "cat /config/.storage/$file_path" > "$OUTPUT_DIR/$(basename "$file_path").json"
    if [ $? -eq 0 ]; then
        echo "✅ Successfully fetched $description"
    else
        echo "❌ Failed to fetch $description"
        return 1
    fi
}

# Function to get HA info
get_ha_info() {
    echo "📋 Getting Home Assistant system info..."
    ssh root@$HA_HOST "ha info" > "$OUTPUT_DIR/ha_info.txt"
    if [ $? -eq 0 ]; then
        echo "✅ Successfully fetched system info"
    else
        echo "❌ Failed to fetch system info"
        return 1
    fi
}

# Fetch all the data
get_ha_info
fetch_ha_data "core.config_entries" "Integrations Configuration"
fetch_ha_data "core.device_registry" "Device Registry"
fetch_ha_data "core.entity_registry" "Entity Registry"
fetch_ha_data "core.area_registry" "Area Registry"

echo ""
echo "🔍 Processing data..."

# Extract integrations summary
echo "📊 Generating integrations summary..."
python3 - << 'EOF' > "$OUTPUT_DIR/integrations_summary.md"
import json
import sys
from datetime import datetime

# Load integrations data
try:
    with open('./inventory/core.config_entries.json', 'r') as f:
        config_data = json.load(f)
except FileNotFoundError:
    print("❌ Could not find core.config_entries.json")
    sys.exit(1)

entries = config_data.get('data', {}).get('entries', [])

# Group integrations by domain
domains = {}
for entry in entries:
    domain = entry.get('domain', 'unknown')
    if domain not in domains:
        domains[domain] = []
    domains[domain].append(entry)

print("# Home Assistant Integrations")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")
print(f"Total Integrations: {len(entries)}")
print("")

for domain, items in sorted(domains.items()):
    print(f"## {domain.title()} ({len(items)})")
    print("")

    for item in items:
        title = item.get('title', 'Unknown')
        source = item.get('source', 'unknown')
        created = item.get('created_at', '')[:10]
        disabled = item.get('disabled_by')

        status = "✅ Enabled" if disabled is None else f"❌ Disabled by {disabled}"
        print(f"- **{title}** ({status})")
        print(f"  - Source: {source}")
        print(f"  - Created: {created}")
        if item.get('unique_id'):
            print(f"  - ID: {item.get('unique_id')}")
        print("")
EOF

# Extract devices summary
echo "📱 Generating devices summary..."
python3 - << 'EOF' > "$OUTPUT_DIR/devices_summary.md"
import json
import sys
from datetime import datetime

# Load devices data
try:
    with open('./inventory/core.device_registry.json', 'r') as f:
        device_data = json.load(f)
except FileNotFoundError:
    print("❌ Could not find core.device_registry.json")
    sys.exit(1)

devices = device_data.get('data', {}).get('devices', [])

# Group devices by area
areas = {}
unassigned = []

for device in devices:
    area_id = device.get('area_id')
    if area_id:
        if area_id not in areas:
            areas[area_id] = []
        areas[area_id].append(device)
    else:
        unassigned.append(device)

print("# Home Assistant Devices")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")
print(f"Total Devices: {len(devices)}")
print("")

# Print devices by area
for area_id, area_devices in sorted(areas.items()):
    print(f"## Area: {area_id.replace('_', ' ').title()} ({len(area_devices)})")
    print("")

    for device in area_devices:
        name = device.get('name', 'Unknown')
        manufacturer = device.get('manufacturer', 'Unknown')
        model = device.get('model', 'Unknown')
        connections = device.get('connections', [])

        print(f"- **{name}**")
        print(f"  - Manufacturer: {manufacturer}")
        print(f"  - Model: {model}")
        if connections:
            print(f"  - Connections: {', '.join([f'{k}:{v}' for k, v in connections])}")
        print("")

# Print unassigned devices
if unassigned:
    print("## Unassigned Devices")
    print("")

    for device in unassigned:
        name = device.get('name', 'Unknown')
        manufacturer = device.get('manufacturer', 'Unknown')
        model = device.get('model', 'Unknown')

        print(f"- **{name}**")
        print(f"  - Manufacturer: {manufacturer}")
        print(f"  - Model: {model}")
        print("")
EOF

# Extract entities summary
echo "🔗 Generating entities summary..."
python3 - << 'EOF' > "$OUTPUT_DIR/entities_summary.md"
import json
import sys
from datetime import datetime

# Load entities data
try:
    with open('./inventory/core.entity_registry.json', 'r') as f:
        entity_data = json.load(f)
except FileNotFoundError:
    print("❌ Could not find core.entity_registry.json")
    sys.exit(1)

entities = entity_data.get('data', {}).get('entities', [])

# Group entities by domain
domains = {}
for entity in entities:
    domain = entity.get('entity_id', '').split('.')[0]
    if domain not in domains:
        domains[domain] = []
    domains[domain].append(entity)

print("# Home Assistant Entities")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("")
print(f"Total Entities: {len(entities)}")
print("")

for domain, items in sorted(domains.items()):
    print(f"## {domain.title()} ({len(items)})")
    print("")

    for item in items[:10]:  # Limit to first 10 to avoid too long output
        entity_id = item.get('entity_id', 'unknown')
        name = item.get('name') or item.get('original_name', 'Unnamed')
        disabled = item.get('disabled_by')
        hidden = item.get('hidden_by')

        status = "✅ Active"
        if disabled:
            status = f"❌ Disabled by {disabled}"
        elif hidden:
            status = f"👻 Hidden by {hidden}"

        print(f"- **{entity_id}** - {name} ({status})")

    if len(items) > 10:
        print(f"  ... and {len(items) - 10} more {domain} entities")
    print("")
EOF

# Generate main summary
echo "📄 Generating main summary..."
cat > "$OUTPUT_DIR/README.md" << EOF
# Home Assistant Inventory Report

Generated on: $(date)

## Overview

This report contains a complete inventory of your Home Assistant setup, including:

- **System Information**: Home Assistant version, hardware details, etc.
- **Integrations**: All configured integrations and their status
- **Devices**: Physical and virtual devices connected to your system
- **Entities**: All available entities (sensors, switches, etc.)

## Files

- \`ha_info.txt\` - Raw system information
- \`core.config_entries.json\` - Raw integrations configuration
- \`core.device_registry.json\` - Raw device registry
- \`core.entity_registry.json\` - Raw entity registry
- \`integrations_summary.md\` - Human-readable integrations summary
- \`devices_summary.md\` - Human-readable devices summary
- \`entities_summary.md\` - Human-readable entities summary

## Quick Stats

EOF

# Add quick stats
python3 - << 'EOF' >> "$OUTPUT_DIR/README.md"
import json

# Load data
with open('./ha_inventory/core.config_entries.json', 'r') as f:
    config_data = json.load(f)
with open('./ha_inventory/core.device_registry.json', 'r') as f:
    device_data = json.load(f)
with open('./ha_inventory/core.entity_registry.json', 'r') as f:
    entity_data = json.load(f)

entries = config_data.get('data', {}).get('entries', [])
devices = device_data.get('data', {}).get('devices', [])
entities = entity_data.get('data', {}).get('entities', [])

# Count unique domains
integration_domains = set(entry.get('domain') for entry in entries)
device_domains = set()
for device in devices:
    for ident in device.get('identifiers', []):
        if len(ident) > 1:
            device_domains.add(ident[0])
entity_domains = set(entity.get('entity_id', '').split('.')[0] for entity in entities)

print(f"- **Integrations**: {len(entries)} total across {len(integration_domains)} domains")
print(f"- **Devices**: {len(devices)} total across {len(device_domains)} types")
print(f"- **Entities**: {len(entities)} total across {len(entity_domains)} domains")
print("")
print("## Integration Domains")
for domain in sorted(integration_domains):
    count = sum(1 for entry in entries if entry.get('domain') == domain)
    print(f"- {domain}: {count}")
print("")
print("## Device Types")
for device_type in sorted(device_domains):
    count = sum(1 for device in devices if any(ident[0] == device_type for ident in device.get('identifiers', [])))
    print(f"- {device_type}: {count}")
print("")
print("## Entity Domains")
for domain in sorted(entity_domains):
    count = sum(1 for entity in entities if entity.get('entity_id', '').startswith(domain + '.'))
    print(f"- {domain}: {count}")
EOF

echo ""
echo "✅ Inventory collection complete!"
echo ""
echo "📁 Generated files in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR"
echo ""
echo "📖 Start with: $OUTPUT_DIR/README.md"
echo ""
echo "🔄 To update this inventory, run this script again."