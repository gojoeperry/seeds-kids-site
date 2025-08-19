#!/usr/bin/env python3
"""
Rebuild the state file with all existing guide files
"""

import json
from pathlib import Path

# Get all existing guide files
guides_dir = Path("site/content/guides")
existing_files = []

if guides_dir.exists():
    for md_file in guides_dir.glob("*.md"):
        # Extract slug from filename
        slug = md_file.stem
        existing_files.append(slug)

# Sort for consistency
existing_files.sort()

# Create state file
state_data = {
    "completed": existing_files
}

# Write state file
state_path = Path("tmp/generate_state.json")
state_path.parent.mkdir(exist_ok=True)

with open(state_path, 'w') as f:
    json.dump(state_data, f, indent=2)

print(f"Rebuilt state file with {len(existing_files)} completed items:")
for slug in existing_files:
    print(f"  - {slug}")
print(f"State saved to: {state_path}")