#!/usr/bin/env python3
"""
Preview the first 15 keywords that would be processed by generate_seeds_pages.py
"""

import pandas as pd
from pathlib import Path
from slugify import slugify

def load_keywords_preview():
    """Load and preview keywords from CSV files"""
    csv_files = ['./keyword_clusters.csv', './keyword_clusters_expanded.csv']
    
    all_keywords = []
    seen_keywords = set()
    
    for csv_file in csv_files:
        if not Path(csv_file).exists():
            print(f"WARNING: CSV file not found: {csv_file}")
            continue
            
        try:
            df = pd.read_csv(csv_file)
            print(f"Loaded {len(df)} rows from {csv_file}")
            
            for _, row in df.iterrows():
                # Require 'keyword' column
                if 'keyword' not in row or pd.isna(row['keyword']):
                    continue
                    
                keyword = str(row['keyword']).strip()
                if not keyword or keyword.lower() in seen_keywords:
                    continue
                    
                seen_keywords.add(keyword.lower())
                
                # Extract optional fields
                item = {
                    'keyword': keyword,
                    'cluster': str(row.get('cluster', '')).strip() if not pd.isna(row.get('cluster')) else '',
                    'intent': str(row.get('intent', '')).strip() if not pd.isna(row.get('intent')) else '',
                    'notes': str(row.get('notes', '')).strip() if not pd.isna(row.get('notes')) else ''
                }
                all_keywords.append(item)
                
        except Exception as e:
            print(f"ERROR: Failed to load {csv_file}: {e}")
            continue
    
    print(f"SUCCESS: Total unique keywords loaded: {len(all_keywords)}")
    
    # Sort by keyword (same as script with --order keyword)
    all_keywords.sort(key=lambda x: x['keyword'])
    
    return all_keywords

def create_slug(keyword: str, slug_prefix: str = "") -> str:
    """Create a clean slug from keyword"""
    base_slug = slugify(keyword)
    if slug_prefix:
        return f"{slug_prefix}{base_slug}"
    return base_slug

def generate_title(keyword: str) -> str:
    """Generate a proper title from keyword"""
    words = keyword.split()
    title_words = []
    
    for word in words:
        if word.lower() in ['and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with']:
            title_words.append(word.lower())
        else:
            title_words.append(word.capitalize())
    
    # Capitalize first word
    if title_words:
        title_words[0] = title_words[0].capitalize()
    
    return ' '.join(title_words)

def preview_first_15():
    """Preview the first 15 keywords that would be processed"""
    keywords = load_keywords_preview()
    
    if not keywords:
        print("ERROR: No keywords found to preview")
        return
    
    # Show first 15 (batch size from command)
    preview_keywords = keywords[:15]
    
    print(f"\nPREVIEW: First 15 keywords that would be processed:")
    print("=" * 80)
    
    for i, kw in enumerate(preview_keywords, 1):
        keyword = kw['keyword']
        cluster = kw['cluster']
        slug = create_slug(keyword)
        title = generate_title(keyword)
        file_path = f"./site/content/guides/{slug}.md"
        
        print(f"\n{i:2d}. KEYWORD: {keyword}")
        print(f"    CLUSTER: {cluster if cluster else '(none)'}")
        print(f"    SLUG: {slug}")
        print(f"    TITLE: {title}")
        print(f"    FILE: {file_path}")
        
        # Check if file would exist
        if Path(file_path).exists():
            print(f"    STATUS: WARNING - File exists (would skip unless --overwrite)")
        else:
            print(f"    STATUS: Ready to create")
    
    print(f"\nSUMMARY:")
    print(f"Total keywords available: {len(keywords)}")
    print(f"Previewing first: {len(preview_keywords)}")
    print(f"Remaining in queue: {max(0, len(keywords) - 15)}")
    
    print(f"\nWHAT WOULD HAPPEN NEXT:")
    print(f"1. Load {len(keywords)} unique keywords from CSV files")
    print(f"2. Load Seeds songs from ./assets/seeds_songs.json")
    print(f"3. Build TF-IDF vectors for song matching")
    print(f"4. For each keyword, find top-5 matching songs (min score: 0.18)")
    print(f"5. Generate 700-900 word articles using Claude API")
    print(f"6. Create Hugo markdown files with YAML frontmatter")
    print(f"7. Save to ./site/content/guides/ directory")
    print(f"8. Update state file for resume functionality")

if __name__ == "__main__":
    preview_first_15()