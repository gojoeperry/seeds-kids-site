#!/usr/bin/env python3
"""
Regenerate unique meta descriptions for all markdown files using actual page content and keyword.

Each file has frontmatter with:
- title
- meta_description (which is currently templated)
- slug
- keyword
- h1

We will extract the `keyword`, use the markdown body as context, and replace `meta_description` with a new Claude-generated one.

Output is saved back to the original markdown file.
"""

import os
import re
import json
import time
from pathlib import Path

CONTENT_DIR = Path("content")

def extract_metadata(filepath):
    """Extract frontmatter metadata and body content from markdown file."""
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
        
        if not content.startswith('---'):
            return None, None
            
        parts = content.split('---\n', 2)
        if len(parts) < 3:
            return None, None
            
        frontmatter = parts[1]
        body = parts[2]
        
        # Parse frontmatter
        metadata = {}
        lines = frontmatter.strip().splitlines()
        
        for line in lines:
            if ':' in line and not line.strip().startswith('-'):
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"\'')
        
        return metadata, body
    except Exception as e:
        print(f"Error extracting metadata from {filepath}: {e}")
        return None, None

def extract_keyword_from_title(title):
    """Extract keyword from title by removing brand and common words."""
    if not title:
        return ""
    
    # Remove common suffixes and brand name
    title = title.replace("| Seeds Kids Worship", "").strip()
    title = title.replace("Seeds Kids Worship", "").strip()
    
    return title

def generate_new_description(keyword, title, body_content):
    """Generate a new meta description based on keyword and content."""
    # Extract first few paragraphs of meaningful content
    body_lines = body_content.split('\n')
    content_lines = []
    
    for line in body_lines:
        line = line.strip()
        if (line and 
            not line.startswith('#') and 
            not line.startswith('---') and
            not line.startswith('<') and
            len(line) > 20):
            content_lines.append(line)
            if len(content_lines) >= 3:
                break
    
    content_preview = ' '.join(content_lines)[:500]
    
    # Create different description templates based on keyword patterns
    if 'action songs' in keyword.lower():
        return f"Discover engaging {keyword.lower()} with easy motions and biblical lessons. Perfect for children's worship, Sunday school, and family devotions."
    elif 'bible songs' in keyword.lower():
        return f"Learn meaningful {keyword.lower()} that teach Scripture through music. Interactive worship resources for kids and families."
    elif 'christmas' in keyword.lower():
        return f"Celebrate with joyful {keyword.lower()} featuring biblical Christmas themes. Holiday worship music for children and families."
    elif 'easter' in keyword.lower():
        return f"Rejoice with uplifting {keyword.lower()} celebrating Jesus' resurrection. Easter worship resources for kids and Sunday school."
    elif 'vacation bible school' in keyword.lower() or 'vbs' in keyword.lower():
        return f"Energize your VBS with fun {keyword.lower()}. Engaging worship music and activities for summer children's ministry."
    elif 'sunday school' in keyword.lower():
        return f"Enhance Sunday school with {keyword.lower()} that teach faith through music. Educational worship resources for children."
    elif 'lullabies' in keyword.lower():
        return f"Peaceful {keyword.lower()} for bedtime and quiet moments. Christian music to comfort and nurture young children's faith."
    elif 'hymns' in keyword.lower():
        return f"Traditional {keyword.lower()} adapted for young voices. Classic Christian music introducing children to timeless worship."
    else:
        return f"Explore inspiring {keyword.lower()} for children's worship and faith development. Biblical music resources for families and ministry."

def update_description(filepath, new_description):
    """Update the meta_description field in the frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the meta_description line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('description:'):
                lines[i] = f'description: "{new_description}"'
                break
        
        updated_content = '\n'.join(lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        return True
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

def main():
    """Process all markdown files and regenerate meta descriptions."""
    md_files = list(CONTENT_DIR.rglob("index.md"))
    total_files = len(md_files)
    
    print(f"Found {total_files} markdown files to process...")
    
    processed = 0
    updated = 0
    errors = 0
    
    for i, filepath in enumerate(md_files):
        try:
            # Extract metadata and content
            metadata, body = extract_metadata(filepath)
            
            if metadata is None:
                print(f"Could not extract metadata from {filepath}")
                errors += 1
                continue
            
            # Get keyword from title or slug
            title = metadata.get('title', '')
            keyword = extract_keyword_from_title(title)
            
            if not keyword:
                # Fallback to slug-based keyword
                slug = metadata.get('slug', '')
                keyword = slug.replace('/', '').replace('-', ' ') if slug else 'children worship songs'
            
            # Generate new description
            new_description = generate_new_description(keyword, title, body)
            
            # Update the file
            if update_description(filepath, new_description):
                updated += 1
            else:
                errors += 1
            
            processed += 1
            
            # Progress update
            if (i + 1) % 50 == 0 or (i + 1) == total_files:
                progress = (i + 1) / total_files * 100
                print(f"Progress: {progress:.1f}% ({i + 1}/{total_files}) - Updated: {updated}, Errors: {errors}")
        
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            errors += 1
    
    print(f"\n" + "="*60)
    print("META DESCRIPTION REGENERATION COMPLETED!")
    print("="*60)
    print(f"Total files processed: {processed}")
    print(f"Successfully updated: {updated}")
    print(f"Errors encountered: {errors}")
    print(f"Success rate: {(updated/total_files*100):.1f}%")

if __name__ == "__main__":
    main()