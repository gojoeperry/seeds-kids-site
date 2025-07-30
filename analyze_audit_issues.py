#!/usr/bin/env python3
"""
Analyze and categorize audit issues to understand what needs fixing
"""

from pathlib import Path
import re
import yaml

CONTENT_DIR = Path("C:/Users/joepe/seeds-kids-seo/site/content")
issues = {
    'yaml_errors': [],
    'missing_keys': [],
    'broken_links': []
}

# Count all files
all_files = list(CONTENT_DIR.rglob("*.md"))
print(f"Total files: {len(all_files)}")

# Categorize issues
for md_file in CONTENT_DIR.rglob("*.md"):
    try:
        rel_path = str(md_file.relative_to(CONTENT_DIR))
        
        # Check YAML
        text = md_file.read_text(encoding='utf-8')
        if "---" not in text:
            issues['missing_keys'].append((rel_path, "Missing front matter block"))
            continue
            
        try:
            front = text.split("---", 2)[1]
            data = yaml.safe_load(front)
            
            # Check required keys
            REQUIRED_KEYS = {"title", "description", "slug", "tags"}
            if not isinstance(data, dict):
                issues['missing_keys'].append((rel_path, "Front matter is not a dictionary"))
            else:
                missing = REQUIRED_KEYS - data.keys()
                if missing:
                    issues['missing_keys'].append((rel_path, f"Missing keys: {missing}"))
        except yaml.YAMLError as e:
            issues['yaml_errors'].append((rel_path, str(e)))
        
        # Count broken links
        links = re.findall(r'\[.*?\]\((.*?)\)', text)
        broken_count = 0
        for link in links:
            if not link.startswith("http") and not link.startswith("#"):
                broken_count += 1
        
        if broken_count > 0:
            issues['broken_links'].append((rel_path, broken_count))
            
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

# Report summary
print(f"\nIssue Summary:")
print(f"- YAML Errors: {len(issues['yaml_errors'])}")
print(f"- Missing Keys: {len(issues['missing_keys'])}")
print(f"- Files with Broken Links: {len(issues['broken_links'])}")

# Show examples
if issues['missing_keys']:
    print(f"\nMissing Keys Examples:")
    for path, issue in issues['missing_keys'][:5]:
        print(f"  - {path}: {issue}")

if issues['broken_links']:
    print(f"\nBroken Links Examples:")
    total_broken = sum(count for _, count in issues['broken_links'])
    print(f"  Total broken links: {total_broken}")
    for path, count in issues['broken_links'][:5]:
        print(f"  - {path}: {count} broken links")