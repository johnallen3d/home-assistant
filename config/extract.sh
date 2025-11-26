#!/bin/bash

# Extract Home Assistant YAML configuration files
# This script downloads YAML files from the HA server that have actual content
# For automations and scenes, splits them into individual files for better git tracking

set -uo pipefail

# Use environment variable from .env (loaded by justfile)
HA_HOST="${HA_SERVER}"
# Extract to current directory (config/)
CONFIG_DIR="."
TEMP_DIR=$(mktemp -d)

echo "📥 Extracting Home Assistant configuration files..."

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Cleanup temp directory on exit
trap "rm -rf $TEMP_DIR" EXIT

# List of YAML files to check (excluding secrets.yaml)
YAML_FILES=(
  "automations.yaml"
  "scenes.yaml"
  "configuration.yaml"
  "scripts.yaml"
)

# Files that will be split into directories
SPLIT_FILES=(
  "automations.yaml"
  "scenes.yaml"
)

# Function to check if file has content and download it
download_if_has_content() {
  local file=$1
  local remote_path="/config/$file"
  local local_path="$CONFIG_DIR/$file"

  echo "🔍 Checking $file..."

  # Check if file exists and get its size
  file_size=$(ssh "$HA_HOST" "[ -f '$remote_path' ] && wc -c < '$remote_path' 2>/dev/null || echo 0")

  if [ "$file_size" -gt 0 ]; then
    echo "  ✅ Downloading $file ($file_size bytes)"
    scp -q "$HA_HOST:$remote_path" "$local_path"
  else
    echo "  ⏭️  Skipping $file (empty or missing)"
    # Remove local copy if it exists but remote is empty
    if [ -f "$local_path" ]; then
      rm "$local_path"
    fi
  fi
}

# Function to split already-downloaded YAML list file into individual files
split_yaml_file() {
  local file=$1
  local source_file="$CONFIG_DIR/$file"
  local base_name="${file%.yaml}"
  local output_dir="$CONFIG_DIR/$base_name"

  if [ ! -f "$source_file" ]; then
    echo "  ⏭️  Skipping split of $file (not downloaded)"
    return
  fi

  echo "  📂 Splitting $file into individual files..."

  # Remove old split directory and create fresh one
  rm -rf "$output_dir"
  mkdir -p "$output_dir"

  # Get the count of entries
  entry_count=$(yq eval 'length' "$source_file")

  if [ "$entry_count" -gt 0 ]; then
    # Split each entry into its own file
    for i in $(seq 0 $((entry_count - 1))); do
      # Get the alias/name for the filename
      if [ "$base_name" = "automations" ]; then
        name=$(yq eval ".[$i].alias" "$source_file")
      else
        name=$(yq eval ".[$i].name" "$source_file")
      fi

      # Sanitize filename (lowercase, replace spaces with underscores, remove special chars)
      # Use iconv to handle UTF-8 and remove invalid characters safely
      filename=$(echo "$name" | iconv -c -t ASCII//TRANSLIT 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd '[:alnum:]_-')

      # Create filename: name.yaml
      output_file="$output_dir/${filename}.yaml"

      # Handle duplicates by appending a counter
      counter=1
      while [ -f "$output_file" ]; do
        output_file="$output_dir/${filename}_${counter}.yaml"
        counter=$((counter + 1))
      done

      # Extract the entry and write to file
      yq eval ".[$i]" "$source_file" > "$output_file"
    done

    echo "  ✅ Split into $entry_count files in $base_name/"
  else
    echo "  ⚠️  No entries found in $file"
  fi
}

# Download all YAML files
for file in "${YAML_FILES[@]}"; do
  download_if_has_content "$file"
done

echo ""
echo "📂 Splitting automations and scenes into individual files..."

# Split downloaded files
for file in "${SPLIT_FILES[@]}"; do
  split_yaml_file "$file"
done

echo ""
echo "🗑️  Removing source files that were split..."
# Remove the source files after splitting
for file in "${SPLIT_FILES[@]}"; do
  source_file="$CONFIG_DIR/$file"
  if [ -f "$source_file" ]; then
    rm "$source_file"
    echo "  ✅ Removed $file"
  fi
done

echo ""
echo "📊 Summary of extracted files:"
echo "Regular files:"
ls -lh "$CONFIG_DIR"/*.yaml 2>/dev/null || echo "  No YAML files found"
echo ""
echo "Split directories:"
for dir in "$CONFIG_DIR"/automations "$CONFIG_DIR"/scenes; do
  if [ -d "$dir" ]; then
    count=$(find "$dir" -name "*.yaml" | wc -l | tr -d ' ')
    echo "  $(basename "$dir")/: $count files"
  fi
done

echo ""
echo "✅ Configuration extraction complete!"
