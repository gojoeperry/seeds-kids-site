#!/usr/bin/env python3
"""
Test version of the Markdown cleanup script - processes just 5 files
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def clean_frontmatter(frontmatter_content: str) -> Tuple[str, List[str]]:
    """Clean and normalize YAML frontmatter."""
    changes = []
    
    # Simple regex-based approach for better performance
    lines = frontmatter_content.strip().split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append('')
            continue
            
        # Handle title capitalization and quoting
        if line.startswith('title:'):
            title_part = line[6:].strip()
            title_clean = title_part.strip('"\'')
            
            # Capitalize first letter if needed
            if title_clean and not title_clean[0].isupper():
                title_clean = title_clean[0].upper() + title_clean[1:]
                changes.append(f"Capitalized title")
            
            # Ensure quoted
            if not title_part.startswith('"') and not title_part.startswith("'"):
                cleaned_lines.append(f'title: "{title_clean}"')
                changes.append("Added quotes to title")
            else:
                cleaned_lines.append(f'title: "{title_clean}"')
                
        # Handle description quoting
        elif line.startswith('description:'):
            desc_part = line[12:].strip()
            desc_clean = desc_part.strip('"\'')
            if not desc_part.startswith('"') and not desc_part.startswith("'"):
                cleaned_lines.append(f'description: "{desc_clean}"')
                changes.append("Added quotes to description")
            else:
                cleaned_lines.append(f'description: "{desc_clean}"')
                
        # Handle slug quoting
        elif line.startswith('slug:'):
            slug_part = line[5:].strip()
            slug_clean = slug_part.strip('"\'')
            if not slug_part.startswith('"') and not slug_part.startswith("'"):
                cleaned_lines.append(f'slug: "{slug_clean}"')
                changes.append("Added quotes to slug")
            else:
                cleaned_lines.append(f'slug: "{slug_clean}"')
                
        # Handle tags (ensure they're quoted)
        elif line.startswith('- ') and not line.startswith('- "') and not line.startswith("- '"):
            tag_clean = line[2:].strip().strip('"\'')
            cleaned_lines.append(f'- "{tag_clean}"')
            if not any("quotes to tags" in change for change in changes):
                changes.append("Added quotes to tags")
        else:
            cleaned_lines.append(line)
            
    return '\n'.join(cleaned_lines), changes

def remove_placeholders(content: str) -> Tuple[str, List[str]]:
    """Remove placeholder content from the markdown."""
    changes = []
    placeholder_patterns = [
        r'\[Insert content here\]',
        r'\[Claude generating\.\.\.\]',
        r'\[Content coming soon\]',
        r'placeholder',
        r'\[placeholder\]',
        r'\[Placeholder text\]',
        r'\[Add content here\]',
        r'\[TODO:.*?\]',
        r'\[Coming soon\]'
    ]
    
    for pattern in placeholder_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            changes.extend([f"Removed placeholder: {match}" for match in matches])
    
    return content, changes

def fix_markdown_formatting(content: str) -> Tuple[str, List[str]]:
    """Fix malformed Markdown formatting."""
    changes = []
    original_content = content
    
    # Fix malformed bold/italic formatting
    content = re.sub(r'\*\*([^*]+)(?<!\*\*)$', r'**\1**', content, flags=re.MULTILINE)
    content = re.sub(r'(?<!\*)\*([^*]+)(?<!\*)$', r'*\1*', content, flags=re.MULTILINE)
    content = re.sub(r'__([^_]+)(?<!__)$', r'__\1__', content, flags=re.MULTILINE)
    
    # Fix header spacing - ensure exactly one blank line after headers
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if current line is a header
        if re.match(r'^#{1,6}\s+', line):
            # Look ahead to see what follows
            j = i + 1
            empty_lines = 0
            
            # Count consecutive empty lines
            while j < len(lines) and not lines[j].strip():
                empty_lines += 1
                j += 1
            
            # Ensure exactly one empty line after header (if there's content after)
            if j < len(lines):  # There's content after the header
                if empty_lines != 1:
                    changes.append(f"Fixed spacing after header")
                    # Remove extra empty lines we're about to skip
                    i += empty_lines
                    # Add exactly one empty line
                    fixed_lines.append('')
                else:
                    i += 1  # Skip the existing single empty line
            else:
                i += empty_lines  # Skip to end if no content follows
        else:
            i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Remove extra blank lines (more than 2 consecutive)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if content != original_content and not changes:
        changes.append("Fixed Markdown formatting issues")
    
    return content, changes

def process_file(file_path: Path):
    """Process a single Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        all_changes = []
        
        # Split frontmatter and content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                main_content = parts[2]
                
                # Clean frontmatter
                cleaned_frontmatter, fm_changes = clean_frontmatter(frontmatter)
                all_changes.extend(fm_changes)
                
                # Clean main content
                main_content, placeholder_changes = remove_placeholders(main_content)
                all_changes.extend(placeholder_changes)
                
                main_content, format_changes = fix_markdown_formatting(main_content)
                all_changes.extend(format_changes)
                
                # Reconstruct file
                content = f"---\n{cleaned_frontmatter}\n---{main_content}"
            else:
                # No proper frontmatter, just clean content
                content, placeholder_changes = remove_placeholders(content)
                all_changes.extend(placeholder_changes)
                
                content, format_changes = fix_markdown_formatting(content)
                all_changes.extend(format_changes)
        else:
            # No frontmatter, just clean content
            content, placeholder_changes = remove_placeholders(content)
            all_changes.extend(placeholder_changes)
            
            content, format_changes = fix_markdown_formatting(content)
            all_changes.extend(format_changes)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Processed {file_path.name} - {len(all_changes)} changes")
            for change in all_changes:
                print(f"  - {change}")
        else:
            print(f"- No changes needed for {file_path.name}")
        
        return True, all_changes
        
    except Exception as e:
        print(f"✗ Error processing {file_path.name}: {e}")
        return False, []

def main():
    """Test with first 5 files."""
    content_dir = Path(r"C:\Users\joepe\seeds-kids-seo\content")
    
    # Get first 5 files from activities
    activities_dir = content_dir / 'activities'
    test_files = list(activities_dir.glob('*.md'))[:5]
    
    print(f"Testing with {len(test_files)} files:")
    for file_path in test_files:
        print(f"  - {file_path.name}")
    print("-" * 50)
    
    total_processed = 0
    total_changes = 0
    
    for file_path in test_files:
        success, changes = process_file(file_path)
        if success:
            total_processed += 1
            total_changes += len(changes)
    
    print("-" * 50)
    print(f"Test completed: {total_processed}/{len(test_files)} files processed")
    print(f"Total changes made: {total_changes}")

if __name__ == "__main__":
    main()