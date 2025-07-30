#!/usr/bin/env python3
"""
Restore proper tags from original content to Hugo markdown files
"""

from pathlib import Path
import re

SOURCE_DIR = Path("C:/Users/joepe/seeds-kids-seo/content")
HUGO_DIR = Path("C:/Users/joepe/seeds-kids-seo/site/content")
files_updated = 0

def extract_tags_from_original(original_content):
    """Extract tags from original frontmatter."""
    lines = original_content.split('\n')
    
    if not lines or lines[0] != '---':
        return []
    
    # Find the end of frontmatter
    frontmatter_end = -1
    for i, line in enumerate(lines[1:], 1):
        if line == '---':
            frontmatter_end = i
            break
    
    if frontmatter_end == -1:
        return []
    
    # Extract tags
    tags = []
    in_tags_section = False
    
    for line in lines[1:frontmatter_end]:
        if line.strip() == 'tags:':
            in_tags_section = True
            continue
        
        if in_tags_section:
            if line.startswith('- '):
                tag = line.strip()[2:].strip('"\'')
                if tag:
                    tags.append(tag)
            elif line.strip() and not line.startswith(' ') and not line.startswith('-'):
                # End of tags section
                break
    
    return tags

def update_hugo_file_tags(hugo_file_path, tags):
    """Update Hugo file with proper tags."""
    content = hugo_file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    if not lines or lines[0] != '---':
        return False
    
    # Find the end of frontmatter
    frontmatter_end = -1
    for i, line in enumerate(lines[1:], 1):
        if line == '---':
            frontmatter_end = i
            break
    
    if frontmatter_end == -1:
        return False
    
    # Build new frontmatter with tags
    new_frontmatter = []
    
    for line in lines[1:frontmatter_end]:
        if line.strip() == 'tags:':
            new_frontmatter.append('tags:')
            for tag in tags:
                new_frontmatter.append(f'- "{tag}"')
        elif not line.startswith('- ') or 'tags:' not in '\n'.join(lines[1:frontmatter_end]):
            new_frontmatter.append(line)
    
    # If no tags section existed, add it
    if 'tags:' not in '\n'.join(new_frontmatter):
        new_frontmatter.append('tags:')
        for tag in tags:
            new_frontmatter.append(f'- "{tag}"')
    
    # Reconstruct content
    new_content = ['---'] + new_frontmatter + ['---'] + lines[frontmatter_end + 1:]
    hugo_file_path.write_text('\n'.join(new_content), encoding='utf-8')
    return True

# Process all files
for source_file in SOURCE_DIR.rglob("index.md"):
    relative_path = source_file.relative_to(SOURCE_DIR)
    category = relative_path.parts[0]
    slug = relative_path.parts[1]
    
    hugo_file = HUGO_DIR / category / f"{slug}.md"
    
    if hugo_file.exists():
        try:
            # Extract tags from original file
            original_content = source_file.read_text(encoding='utf-8')
            tags = extract_tags_from_original(original_content)
            
            if tags:
                if update_hugo_file_tags(hugo_file, tags):
                    files_updated += 1
        except Exception as e:
            print(f"Error processing {hugo_file}: {e}")

print(f"Restored tags in {files_updated} Hugo markdown files.")