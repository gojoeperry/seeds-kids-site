#!/usr/bin/env python3
"""
Check progress of SEO page generation
Shows statistics on completed vs remaining pages
"""

import json
import os
from pathlib import Path

INPUT_FILE = "url_metadata.json"
OUTPUT_DIR = "content"

def file_exists(url):
    """Check if output file exists"""
    clean_url = url.strip("/")
    path_parts = clean_url.split("/")
    
    output_path = Path(OUTPUT_DIR)
    for part in path_parts:
        output_path = output_path / part
    
    # Check for index.md file in the directory (current structure)
    index_file = output_path / "index.md"
    if index_file.exists():
        return True
    
    # Also check for direct .md file (legacy structure)
    return output_path.with_suffix(".md").exists()

def main():
    # Load metadata
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    total_keywords = len(metadata)
    completed = 0
    remaining = []
    
    for item in metadata:
        if file_exists(item["url"]):
            completed += 1
        else:
            remaining.append(item["keyword"])
    
    # Statistics
    progress_percent = (completed / total_keywords) * 100
    
    print("=" * 60)
    print("SEO PAGE GENERATION PROGRESS REPORT")
    print("=" * 60)
    print(f"Total Keywords:      {total_keywords:,}")
    print(f"Pages Generated:     {completed:,}")
    print(f"Pages Remaining:     {len(remaining):,}")
    print(f"Progress:           {progress_percent:.1f}%")
    print(f"Output Directory:   {Path(OUTPUT_DIR).absolute()}")
    
    # Show next few to be generated
    if remaining:
        print(f"\nNext 10 keywords to generate:")
        for i, keyword in enumerate(remaining[:10], 1):
            print(f"  {i}. {keyword}")
        
        if len(remaining) > 10:
            print(f"  ... and {len(remaining) - 10} more")
    else:
        print("\nALL PAGES GENERATED!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()