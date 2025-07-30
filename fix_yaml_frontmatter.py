#!/usr/bin/env python3
"""
Fix malformed YAML frontmatter in Hugo markdown files
Removes orphaned category lines and ensures proper structure
"""

from pathlib import Path
import re

CONTENT_DIR = Path("C:/Users/joepe/seeds-kids-seo/site/content")
files_fixed = 0

def fix_frontmatter(content):
    """Fix malformed YAML frontmatter."""
    lines = content.split('\n')
    
    if not lines or lines[0] != '---':
        return content
    
    # Find the end of frontmatter
    frontmatter_end = -1
    for i, line in enumerate(lines[1:], 1):
        if line == '---':
            frontmatter_end = i
            break
    
    if frontmatter_end == -1:
        return content
    
    # Process frontmatter lines
    frontmatter_lines = lines[1:frontmatter_end]
    fixed_frontmatter = []
    
    for line in frontmatter_lines:
        # Skip orphaned category lines like: - "songs", - "activities"
        if re.match(r'^- "[^"]*"$', line.strip()) and line.strip() not in ['- "kids"', '- "songs"', '- "worship"', '- "activities"', '- "praise"', '- "learning"', '- "memory"', '- "performance"', '- "devotional"', '- "gospel"', '- "actions"', '- "scripture"', '- "sunday-school"']:
            continue
        
        # Skip lines that are just category names without proper YAML structure
        if line.strip() in ['"songs"', '"activities"']:
            continue
            
        fixed_frontmatter.append(line)
    
    # Reconstruct the content
    fixed_content = ['---'] + fixed_frontmatter + ['---'] + lines[frontmatter_end + 1:]
    return '\n'.join(fixed_content)

for md_file in CONTENT_DIR.rglob("*.md"):
    try:
        original_content = md_file.read_text(encoding="utf-8")
        fixed_content = fix_frontmatter(original_content)
        
        if original_content != fixed_content:
            md_file.write_text(fixed_content, encoding="utf-8")
            files_fixed += 1
            print(f"Fixed: {md_file.relative_to(CONTENT_DIR)}")
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print(f"\nFixed YAML frontmatter in {files_fixed} markdown files.")