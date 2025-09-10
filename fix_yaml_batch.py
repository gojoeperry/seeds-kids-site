#!/usr/bin/env python3
"""
Fix YAML frontmatter syntax errors in recovered content files
"""
import os
import re
from pathlib import Path

def fix_yaml_file(file_path):
    """Fix common YAML syntax errors in a markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into frontmatter and body
        parts = content.split('---', 2)
        if len(parts) < 3:
            return False
        
        frontmatter = parts[1].strip()
        body = parts[2]
        
        # Fix common issues
        lines = frontmatter.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Fix orphaned list items
            if line.startswith('- "') and line.endswith('"') and ':' not in line:
                # This looks like a stray tag, skip it for now
                continue
                
            # Fix missing colons for fields
            if not ':' in line and not line.startswith('-'):
                continue
                
            fixed_lines.append(line)
        
        # Reconstruct the file
        fixed_frontmatter = '\n'.join(fixed_lines)
        fixed_content = f"---\n{fixed_frontmatter}\n---{body}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return True
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    site_dir = Path("site/content")
    fixed_count = 0
    
    for md_file in site_dir.rglob("*.md"):
        if fix_yaml_file(md_file):
            fixed_count += 1
    
    print(f"Fixed YAML in {fixed_count} files")

if __name__ == "__main__":
    main()