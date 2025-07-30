#!/usr/bin/env python3
"""
Fix remaining malformed double-bracket links
Handles the specific pattern: [[text](url/)](url)
"""

import re
from pathlib import Path

def fix_remaining_malformed_links():
    """Fix remaining malformed double-bracket link patterns."""
    content_dir = Path('content')
    md_files = list(content_dir.rglob('index.md'))
    
    total_files = len(md_files)
    files_fixed = 0
    links_fixed = 0
    
    print(f"Processing {total_files} markdown files for remaining malformed links...")
    
    for i, file_path in enumerate(md_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix pattern: [[text](url/)](url) -> [text](url/)
            # More specific pattern for the remaining issues
            pattern = r'\[\[([^\]]+)\]\(([^\)]+/)\)\]\([^\)]*\)'
            matches = re.findall(pattern, content)
            
            if matches:
                for text, url in matches:
                    # Find the full malformed link
                    malformed_pattern = rf'\[\[{re.escape(text)}\]\({re.escape(url)}\)\]\([^\)]*\)'
                    fixed = f'[{text}]({url})'
                    content = re.sub(malformed_pattern, fixed, content)
                    links_fixed += 1
                
                # Write the fixed content
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
    print("REMAINING LINK FIXES COMPLETED!")
    print("="*60)
    print(f"Files processed: {total_files}")
    print(f"Files modified: {files_fixed}")
    print(f"Malformed links fixed: {links_fixed}")

if __name__ == "__main__":
    fix_remaining_malformed_links()