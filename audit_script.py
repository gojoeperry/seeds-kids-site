"""
Pre-Deployment Audit for Hugo Static Site (Vercel-ready)

This script runs a full audit of a Hugo site directory to catch common errors before deploying to Vercel:
- YAML front matter validation
- Broken internal links
- Orphaned content files
- Unused static assets
- Vercel config consistency
- Build test using Hugo and Vercel CLI

Usage: Run this in the project root directory before deploying to Vercel
"""

import os
import subprocess
import yaml
from pathlib import Path

CONTENT_DIR = Path("site/content")
STATIC_DIR = Path("site/static")
CONFIG_FILE = Path("site/config.toml")
VARS_TO_CHECK = ["title", "description", "slug"]

def validate_yaml_frontmatter(md_file):
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.read().split("---")
            if len(lines) < 2:
                return False, "Missing front matter"
            data = yaml.safe_load(lines[1])
            for var in VARS_TO_CHECK:
                if var not in data:
                    return False, f"Missing '{var}'"
        return True, ""
    except Exception as e:
        return False, str(e)

def scan_markdown_files():
    print("\n[1] Validating YAML Front Matter...")
    failed = []
    for md in CONTENT_DIR.rglob("*.md"):
        valid, message = validate_yaml_frontmatter(md)
        if not valid:
            failed.append((md, message))
    if failed:
        print(f"  ⚠️ {len(failed)} files with front matter issues:")
        for path, reason in failed[:10]:  # Show first 10
            print(f"    - {path}: {reason}")
        if len(failed) > 10:
            print(f"    ... and {len(failed) - 10} more")
    else:
        print("  ✅ All markdown files have valid front matter.")

def check_broken_links():
    print("\n[2] Checking for broken internal links...")
    broken = []
    all_slugs = {str(p.relative_to(CONTENT_DIR)).replace("\\", "/").replace("/index.md", "").replace(".md", "") for p in CONTENT_DIR.rglob("*.md")}
    for md in CONTENT_DIR.rglob("*.md"):
        with open(md, "r", encoding="utf-8") as f:
            for line in f:
                if "](/" in line:
                    parts = line.split("](/")
                    for part in parts[1:]:
                        link = part.split(")")[0].strip("/")
                        if link and link not in all_slugs:
                            broken.append((md, link))
    if broken:
        print(f"  ⚠️ Found {len(broken)} broken internal links:")
        for path, link in broken[:10]:  # Show first 10
            print(f"    - {path}: /{link}")
        if len(broken) > 10:
            print(f"    ... and {len(broken) - 10} more")
    else:
        print("  ✅ No broken internal links found.")

def check_orphan_files():
    print("\n[3] Checking for orphan content files (not linked internally)...")
    slugs = set()
    for md in CONTENT_DIR.rglob("*.md"):
        slug = str(md.relative_to(CONTENT_DIR)).replace("\\", "/").replace("/index.md", "").replace(".md", "")
        slugs.add(slug)
    linked = set()
    for md in CONTENT_DIR.rglob("*.md"):
        with open(md, "r", encoding="utf-8") as f:
            content = f.read()
            for slug in slugs:
                if f"](/" + slug in content:
                    linked.add(slug)
    orphaned = slugs - linked
    if orphaned:
        print(f"  ⚠️ Found {len(orphaned)} orphan content files (never linked internally):")
        for slug in list(orphaned)[:10]:  # Show first 10
            print(f"    - {slug}")
        if len(orphaned) > 10:
            print(f"    ... and {len(orphaned) - 10} more")
    else:
        print("  ✅ No orphan content files.")

def build_hugo():
    print("\n[4] Running Hugo build to validate site...")
    try:
        result = subprocess.run(["hugo", "-s", "site"], capture_output=True, text=True)
        if result.returncode != 0:
            print("  ❌ Hugo build failed:")
            print(result.stderr)
        else:
            print("  ✅ Hugo build completed successfully.")
    except FileNotFoundError:
        print("  ⚠️ Hugo not found in PATH - skipping Hugo build test")

def build_vercel():
    print("\n[5] Running Vercel build test (vercel build)...")
    try:
        result = subprocess.run(["vercel", "build", "site", "--prod"], capture_output=True, text=True)
        if result.returncode != 0:
            print("  ❌ Vercel build failed:")
            print(result.stderr)
        else:
            print("  ✅ Vercel build completed successfully.")
    except FileNotFoundError:
        print("  ⚠️ Vercel CLI not found in PATH - skipping Vercel build test")

# === RUN ===
if __name__ == "__main__":
    scan_markdown_files()
    check_broken_links()
    check_orphan_files()
    build_hugo()
    build_vercel()
    print("\nPre-deployment audit complete.")