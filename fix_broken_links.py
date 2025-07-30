#!/usr/bin/env python3
"""
Fix broken internal markdown links and malformed syntax
Addresses both missing links and double-bracket formatting issues
"""

import re
from pathlib import Path

def fix_markdown_links():
    """Fix all markdown link issues in content files."""
    content_dir = Path('content')
    md_files = list(content_dir.rglob('index.md'))
    
    # Build a mapping of all available slugs
    all_slugs = {}
    for md_file in md_files:
        slug = str(md_file.parent.relative_to(content_dir)).lower()
        all_slugs[slug] = md_file
    
    total_files = len(md_files)
    files_fixed = 0
    broken_links_fixed = 0
    malformed_links_fixed = 0
    
    print(f"Processing {total_files} markdown files...")
    
    for i, file_path in enumerate(md_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix 1: Remove malformed double-bracket links like [[text](url)](url)
            # Pattern: [[text](url)](url) -> [text](url)
            double_bracket_pattern = r'\[\[([^\]]*)\]\(([^\)]*)\)\]\([^\)]*\)'
            matches = re.findall(double_bracket_pattern, content)
            if matches:
                for text, url in matches:
                    malformed = f'[[{text}]({url})]({url})'
                    fixed = f'[{text}]({url})'
                    content = content.replace(malformed, fixed)
                    malformed_links_fixed += 1
            
            # Fix 2: Remove broken internal links entirely (since they don't exist)
            # Find all internal links and remove ones that don't have corresponding files
            internal_link_pattern = r'- "\[([^\]]+)\]\((\/[a-zA-Z0-9\-/]+)\/\)"'
            matches = re.findall(internal_link_pattern, content)
            
            for link_text, link_url in matches:
                rel_path = link_url.strip('/').lower()
                if rel_path not in all_slugs:
                    # Remove the entire line with the broken link
                    broken_line = f'- "[{link_text}]({link_url}/)"'
                    content = content.replace(broken_line, '')
                    broken_links_fixed += 1
            
            # Fix 3: Clean up any extra empty lines created by removing links
            content = re.sub(r'\n\n\n+', '\n\n', content)
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_fixed += 1
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        
        # Progress update
        if (i + 1) % 100 == 0 or (i + 1) == total_files:
            progress = (i + 1) / total_files * 100
            print(f"Progress: {progress:.1f}% ({i + 1}/{total_files})")
    
    print(f"\n" + "="*60)
    print("LINK FIXING COMPLETED!")
    print("="*60)
    print(f"Files processed: {total_files}")
    print(f"Files modified: {files_fixed}")
    print(f"Broken links removed: {broken_links_fixed}")
    print(f"Malformed links fixed: {malformed_links_fixed}")
    print(f"Total fixes: {broken_links_fixed + malformed_links_fixed}")

if __name__ == "__main__":
    fix_markdown_links()