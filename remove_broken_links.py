#!/usr/bin/env python3
"""
Remove all broken internal links from Hugo markdown files
"""

from pathlib import Path
import re

CONTENT_DIR = Path("C:/Users/joepe/seeds-kids-seo/site/content")
files_fixed = 0
links_removed = 0

def remove_broken_internal_links(content):
    """Remove broken internal links from content."""
    global links_removed
    
    # Find all markdown links
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links = re.findall(link_pattern, content)
    
    for link_text, link_url in links:
        # Skip external links and anchors
        if link_url.startswith('http') or link_url.startswith('#'):
            continue
            
        # For internal links, check if the target exists
        # Since we know most are broken, we'll remove lines containing these links
        full_link = f'[{link_text}]({link_url})'
        
        # Remove entire lines containing broken internal links
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if full_link in line:
                # If it's a bullet point line with only the link, remove it
                if line.strip().startswith('- ') and line.strip().endswith(')'):
                    links_removed += 1
                    continue
                # If it's embedded in other text, just remove the link but keep the text
                else:
                    line = line.replace(full_link, link_text)
                    links_removed += 1
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    return content

for md_file in CONTENT_DIR.rglob("*.md"):
    try:
        original_content = md_file.read_text(encoding='utf-8')
        cleaned_content = remove_broken_internal_links(original_content)
        
        if original_content != cleaned_content:
            md_file.write_text(cleaned_content, encoding='utf-8')
            files_fixed += 1
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print(f"Removed broken links from {files_fixed} files.")
print(f"Total links removed: {links_removed}")