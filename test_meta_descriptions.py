#!/usr/bin/env python3
"""
Test the meta description generation on a few sample files
"""

import os
import re
from pathlib import Path

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

def test_sample_files():
    """Test on a few sample files."""
    content_dir = Path("content")
    
    # Get first 5 files as samples
    sample_files = list(content_dir.rglob("index.md"))[:5]
    
    print("Testing meta description generation on sample files:")
    print("="*60)
    
    for filepath in sample_files:
        print(f"\nFile: {filepath}")
        
        metadata, body = extract_metadata(filepath)
        if metadata is None:
            print("  ERROR: Could not extract metadata")
            continue
        
        title = metadata.get('title', '')
        current_desc = metadata.get('description', '')
        keyword = extract_keyword_from_title(title)
        
        if not keyword:
            slug = metadata.get('slug', '')
            keyword = slug.replace('/', '').replace('-', ' ') if slug else 'children worship songs'
        
        new_description = generate_new_description(keyword, title, body)
        
        print(f"  Title: {title}")
        print(f"  Keyword: {keyword}")
        print(f"  Current: {current_desc}")
        print(f"  New: {new_description}")
        print(f"  Length: {len(new_description)} chars")

if __name__ == "__main__":
    test_sample_files()