#!/usr/bin/env python3
"""
Final fix for YAML frontmatter - remove all orphaned category lines
"""

from pathlib import Path
import re

CONTENT_DIR = Path("C:/Users/joepe/seeds-kids-seo/site/content")
files_fixed = 0

def fix_frontmatter_final(content):
    """Remove orphaned category lines from YAML frontmatter."""
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
        # Remove any orphaned lines that are just: - "category"
        if re.match(r'^- "[^"]*"$', line.strip()):
            # Skip this line - it's an orphaned category
            continue
            
        fixed_frontmatter.append(line)
    
    # Reconstruct the content
    fixed_content = ['---'] + fixed_frontmatter + ['---'] + lines[frontmatter_end + 1:]
    return '\n'.join(fixed_content)

for md_file in CONTENT_DIR.rglob("*.md"):
    try:
        original_content = md_file.read_text(encoding="utf-8")
        fixed_content = fix_frontmatter_final(original_content)
        
        if original_content != fixed_content:
            md_file.write_text(fixed_content, encoding="utf-8")
            files_fixed += 1
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print(f"Removed orphaned category lines from {files_fixed} markdown files.")