#!/usr/bin/env python3
"""
Fix the remaining 22 files that still have template descriptions
"""

import re
from pathlib import Path

def extract_keyword_from_title(title):
    """Extract keyword from title by removing brand and common words."""
    if not title:
        return ""
    title = title.replace("| Seeds Kids Worship", "").strip()
    title = title.replace("Seeds Kids Worship", "").strip()
    return title

def generate_better_description(keyword):
    """Generate better descriptions for the remaining files."""
    keyword_lower = keyword.lower()
    
    if 'bible story songs' in keyword_lower:
        return f"Learn {keyword.lower()} that bring Scripture to life through music. Biblical storytelling resources for children's worship and education."
    elif 'choir songs' in keyword_lower:
        return f"Beautiful {keyword.lower()} perfect for children's ministry and church performances. Inspiring choral music for young voices."
    elif 'church songs' in keyword_lower:
        return f"Uplifting {keyword.lower()} for children's worship services and ministry. Church music resources for kids and families."
    elif 'ministry music' in keyword_lower:
        return f"Essential {keyword.lower()} for effective children's ministry. Professional worship resources and teaching tools."
    elif 'playlist' in keyword_lower:
        return f"Curated {keyword.lower()} featuring the best Christian music for children. Ready-made worship collections for families."
    elif 'devotional songs' in keyword_lower:
        return f"Meaningful {keyword.lower()} for daily faith building and family worship. Spiritual music resources for children."
    elif 'faith songs' in keyword_lower:
        return f"Inspiring {keyword.lower()} that build strong spiritual foundations. Faith-building music for children and families."
    elif 'gospel music' in keyword_lower:
        return f"Joyful {keyword.lower()} celebrating God's love and grace. Gospel worship resources for children and ministry."
    elif 'memory verse songs' in keyword_lower:
        return f"Catchy {keyword.lower()} that make Scripture memorization fun and easy. Bible learning through music for kids."
    elif 'praise songs' in keyword_lower:
        return f"Energetic {keyword.lower()} for celebrating God's goodness. Praise and worship music for children's ministry."
    elif 'spiritual songs' in keyword_lower:
        return f"Deep {keyword.lower()} that nurture children's relationship with God. Spiritual growth through music and worship."
    elif 'worship music' in keyword_lower:
        return f"Powerful {keyword.lower()} for connecting children with God. Worship resources for families and ministry leaders."
    elif 'preschool' in keyword_lower:
        return f"Age-appropriate {keyword.lower()} designed for young children. Early faith development through music and movement."
    elif 'scripture songs' in keyword_lower:
        return f"Educational {keyword.lower()} that teach Bible verses through melody. Scripture learning made fun and memorable."
    elif 'toddler' in keyword_lower:
        return f"Gentle {keyword.lower()} perfect for little ones. Early Christian education through simple, engaging melodies."
    elif 'vacation bible school' in keyword_lower or 'vbs' in keyword_lower:
        return f"Fun {keyword.lower()} for summer ministry programs. VBS music resources that energize and teach children."
    else:
        return f"Discover inspiring {keyword.lower()} for children's worship and spiritual growth. Quality Christian music resources for families."

def update_description(filepath, new_description):
    """Update the description field in the frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
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
    """Fix the remaining files with template descriptions."""
    
    # List of files that still need fixing
    flagged_files = [
        "content/songs/bible-story-songs-with-lyrics/index.md",
        "content/songs/children-s-choir-songs-with-lyrics/index.md",
        "content/songs/children-s-church-songs-with-lyrics/index.md",
        "content/songs/children-s-church-songs-with-lyrics-and-actions/index.md",
        "content/songs/children-s-ministry-music-with-lyrics/index.md",
        "content/songs/christian-kids-playlist-with-lyrics/index.md",
        "content/songs/christian-songs-for-kids-with-lyrics-and-action/index.md",
        "content/songs/christian-songs-with-motions-with-lyrics/index.md",
        "content/songs/kids-christian-music-with-lyrics/index.md",
        "content/songs/kids-church-music-with-lyrics/index.md",
        "content/songs/kids-devotional-songs-with-lyrics/index.md",
        "content/songs/kids-faith-songs-with-lyrics/index.md",
        "content/songs/kids-gospel-music-with-lyrics/index.md",
        "content/songs/kids-memory-verse-songs-with-lyrics/index.md",
        "content/songs/kids-praise-songs-with-lyrics/index.md",
        "content/songs/kids-spiritual-songs-with-lyrics/index.md",
        "content/songs/kids-worship-music-with-lyrics/index.md",
        "content/songs/preschool-christian-songs-with-lyrics/index.md",
        "content/songs/scripture-songs-with-lyrics/index.md",
        "content/songs/toddler-worship-songs-with-lyrics/index.md",
        "content/songs/worship-songs-for-toddlers-with-lyrics/index.md",
        "content/activities/vacation-bible-school-songs-with-lyrics/index.md"
    ]
    
    updated = 0
    errors = 0
    
    print(f"Fixing {len(flagged_files)} remaining files with template descriptions...")
    
    for filepath_str in flagged_files:
        filepath = Path(filepath_str)
        
        if not filepath.exists():
            print(f"File not found: {filepath}")
            errors += 1
            continue
        
        try:
            # Extract title to get keyword
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find title in frontmatter
            lines = content.split('\n')
            title = ""
            for line in lines:
                if line.strip().startswith('title:'):
                    title = line.split(':', 1)[1].strip().strip('"\'')
                    break
            
            keyword = extract_keyword_from_title(title)
            new_description = generate_better_description(keyword)
            
            if update_description(filepath, new_description):
                print(f"Updated: {filepath} -> {new_description}")
                updated += 1
            else:
                errors += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            errors += 1
    
    print(f"\nCompleted! Updated: {updated}, Errors: {errors}")

if __name__ == "__main__":
    main()