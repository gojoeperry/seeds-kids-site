#!/usr/bin/env python3
"""
Reprocess the 10 files that failed during network interruption
"""

from comprehensive_seeds_rewriter import ComprehensiveSeedsRewriter
from pathlib import Path
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The 10 failed files that need reprocessing
FAILED_FILES = [
    "site/content/activities/easter-bible-songs-for-kids.md",
    "site/content/activities/easter-bible-songs-for-preschoolers.md", 
    "site/content/activities/easter-bible-story-songs.md",
    "site/content/activities/easter-children-s-choir-songs.md",
    "site/content/activities/easter-children-s-church-songs.md",
    "site/content/activities/easter-children-s-ministry-music.md",
    "site/content/activities/easter-christian-kids-playlist.md",
    "site/content/activities/easter-christian-lullabies-for-kids.md",
    "site/content/activities/easter-christian-songs-with-motions.md",
    "site/content/activities/easter-christmas-songs-for-kids.md"
]

def process_failed_files():
    """Process the failed files using comprehensive rewriter"""
    logger.info(f"Starting reprocessing of {len(FAILED_FILES)} failed files...")
    
    # Initialize comprehensive rewriter
    rewriter = ComprehensiveSeedsRewriter()
    
    # Convert string paths to Path objects and verify they exist
    valid_files = []
    for file_path_str in FAILED_FILES:
        file_path = Path(file_path_str)
        if file_path.exists():
            valid_files.append(file_path)
        else:
            logger.warning(f"File not found: {file_path}")
    
    logger.info(f"Found {len(valid_files)} valid files to reprocess")
    
    if not valid_files:
        logger.error("No valid files found!")
        return 0
    
    total_processed = 0
    batch_start_time = time.time()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"PROCESSING FAILED FILES: {len(valid_files)} files")
    logger.info(f"{'='*80}")
    
    for i, file_path in enumerate(valid_files):
        file_start_time = time.time()
        current_num = i + 1
        
        logger.info(f"[{current_num}/{len(valid_files)}] Processing: {file_path.name}")
        
        try:
            # Determine relevant songs based on filename
            filename_lower = file_path.stem.lower()
            relevant_songs = []
            
            # Enhanced song selection (same logic as comprehensive rewriter)
            if "christmas" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('christmas', []))
                relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:3])
            elif "easter" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('easter', []))
                relevant_songs.extend(rewriter.songs_by_category.get('gospel_songs', [])[:3])
            elif "action" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('action_songs', []))
                relevant_songs.extend(rewriter.songs_by_category.get('praise', [])[:3])
            elif "worship" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('worship', []))
                relevant_songs.extend(rewriter.songs_by_category.get('praise', [])[:3])
            elif "praise" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('praise', []))
                relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:3])
            elif "toddler" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('toddlers', []))
                relevant_songs.extend(rewriter.songs_by_category.get('lullabies', [])[:2])
            elif "preschool" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('preschool', []))
                relevant_songs.extend(rewriter.songs_by_category.get('character_building', [])[:3])
            elif "bible" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('bible_stories', []))
                relevant_songs.extend(rewriter.songs_by_category.get('scripture', [])[:3])
            elif "choir" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('traditional_hymns', []))
                relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:3])
            elif "church" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('worship', []))
                relevant_songs.extend(rewriter.songs_by_category.get('gospel_songs', [])[:3])
            elif "lullabies" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('lullabies', []))
                relevant_songs.extend(rewriter.songs_by_category.get('peaceful', [])[:2])
            elif "devotional" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('devotional', []))
                relevant_songs.extend(rewriter.songs_by_category.get('scripture', [])[:3])
            elif "faith" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('character_building', []))
                relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:3])
            elif "gospel" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('gospel_songs', []))
                relevant_songs.extend(rewriter.songs_by_category.get('praise', [])[:3])
            elif "hymns" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('traditional_hymns', []))
                relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:3])
            elif "memory" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('scripture', []))
                relevant_songs.extend(rewriter.songs_by_category.get('character_building', [])[:3])
            elif "spiritual" in filename_lower:
                relevant_songs.extend(rewriter.songs_by_category.get('worship', []))
                relevant_songs.extend(rewriter.songs_by_category.get('devotional', [])[:3])
            else:
                # General mix for uncategorized files
                relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:5])
                relevant_songs.extend(rewriter.songs_by_category.get('praise', [])[:3])
                relevant_songs.extend(rewriter.songs_by_category.get('character_building', [])[:2])
            
            # Ensure we have some songs
            if len(relevant_songs) < 5:
                remaining_songs = [s for s in rewriter.seeds_songs if s not in relevant_songs]
                relevant_songs.extend(remaining_songs[:5-len(relevant_songs)])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_songs = []
            for song in relevant_songs:
                if song['slug'] not in seen:
                    unique_songs.append(song)
                    seen.add(song['slug'])
            
            relevant_songs = unique_songs
            logger.info(f"  Selected {len(relevant_songs)} relevant songs")
            
            # Generate prompt and content
            prompt = rewriter.create_blog_prompt(file_path, relevant_songs)
            new_content = rewriter.generate_content_with_claude(prompt)
            
            if new_content:
                # Read existing frontmatter
                existing_frontmatter = {}
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            import yaml
                            existing_frontmatter = yaml.safe_load(parts[1]) or {}
                except:
                    pass
                
                # Update frontmatter
                song_slugs = [song.get('slug', '') for song in relevant_songs[:6] if song.get('slug')]
                if song_slugs:
                    existing_frontmatter['seed_songs'] = song_slugs
                
                meta_description = rewriter.generate_compelling_meta_description(file_path.stem, new_content)
                existing_frontmatter['description'] = meta_description
                existing_frontmatter['meta_description'] = meta_description
                
                # Add schema markup
                new_content_with_schema = rewriter.add_schema_markup(file_path.stem, new_content, relevant_songs)
                
                # Write updated file
                rewriter.write_page(file_path, existing_frontmatter, new_content_with_schema)
                
                file_time = time.time() - file_start_time
                logger.info(f"  ✅ SUCCESS: {file_path.name} ({file_time/60:.1f} min)")
                total_processed += 1
                
            else:
                file_time = time.time() - file_start_time
                logger.error(f"  ❌ FAILED: {file_path.name} - No content generated ({file_time/60:.1f} min)")
                
        except Exception as e:
            file_time = time.time() - file_start_time
            logger.error(f"  ❌ ERROR: {file_path.name} - {str(e)} ({file_time/60:.1f} min)")
    
    # Final summary
    batch_time = time.time() - batch_start_time
    logger.info(f"\n{'='*80}")
    logger.info(f"FAILED FILES PROCESSING COMPLETE:")
    logger.info(f"  Success: {total_processed}/{len(valid_files)} files")
    logger.info(f"  Time: {batch_time/60:.1f} minutes")
    logger.info(f"{'='*80}")
    
    logger.info(f"REPROCESSING COMPLETE!")
    logger.info(f"Successfully processed: {total_processed}/{len(valid_files)} files")
    
    return total_processed

if __name__ == "__main__":
    processed_count = process_failed_files()
    logger.info(f"Failed files reprocessing completed: {processed_count} files processed")