#!/usr/bin/env python3
"""
Reprocess the 56 files that were processed with bad batch scripts
These files got forced 8-song treatment and need proper comprehensive rewriting
"""

from comprehensive_seeds_rewriter import ComprehensiveSeedsRewriter
from pathlib import Path
import logging
import sys
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of 56 files that need reprocessing (from find command results)
BAD_FILES = [
    "site/content/activities/christmas-songs-for-kids-for-preschoolers.md",
    "site/content/activities/christmas-songs-for-kids-for-sunday-school.md", 
    "site/content/activities/christmas-songs-for-kids-for-toddlers.md",
    "site/content/activities/christmas-songs-for-kids-for-worship.md",
    "site/content/activities/christmas-songs-for-kids-in-english.md",
    "site/content/activities/christmas-songs-for-kids-interactive.md",
    "site/content/activities/christmas-songs-for-kids-jingle-bells.md",
    "site/content/activities/christmas-songs-for-kids-list.md",
    "site/content/activities/christmas-songs-for-kids-lyrics.md",
    "site/content/activities/christmas-songs-for-kids-mp3-download.md",
    "site/content/activities/christmas-songs-for-kids-playlist.md",
    "site/content/activities/christmas-songs-for-kids-to-perform.md",
    "site/content/activities/christmas-songs-for-kids-videos.md",
    "site/content/activities/christmas-songs-for-kids-with-actions.md",
    "site/content/activities/christmas-songs-for-kids-with-dance.md",
    "site/content/activities/christmas-worship-songs-for-toddlers.md",
    "site/content/activities/church-easter-songs-for-kids.md",
    "site/content/activities/contemporary-easter-songs-for-kids.md",
    "site/content/activities/easter-action-songs-for-kids.md",
    "site/content/activities/easter-bible-songs-for-kids.md",
    "site/content/activities/easter-bible-songs-for-preschoolers.md",
    "site/content/activities/easter-bible-story-songs.md",
    "site/content/activities/easter-children-s-choir-songs.md",
    "site/content/activities/easter-children-s-church-songs.md",
    "site/content/activities/easter-children-s-ministry-music.md",
    "site/content/activities/easter-christian-kids-playlist.md",
    "site/content/activities/easter-christian-lullabies-for-kids.md",
    "site/content/activities/easter-christian-songs-with-motions.md",
    "site/content/activities/easter-christmas-songs-for-kids.md",
    "site/content/activities/easter-easter-songs-for-kids.md",
    "site/content/activities/easter-kids-christian-music.md",
    "site/content/activities/easter-kids-church-music.md",
    "site/content/activities/easter-kids-devotional-songs.md",
    "site/content/activities/easter-kids-faith-songs.md",
    "site/content/activities/easter-kids-gospel-music.md",
    "site/content/activities/easter-kids-hymns.md",
    "site/content/activities/easter-kids-memory-verse-songs.md",
    "site/content/activities/easter-kids-praise-songs.md",
    "site/content/activities/easter-kids-spiritual-songs.md",
    "site/content/activities/easter-kids-worship-music.md",
    "site/content/activities/easter-preschool-christian-songs.md",
    "site/content/activities/easter-scripture-songs.md",
    "site/content/activities/easter-songs-for-kids-app.md",
    "site/content/activities/easter-songs-for-kids-bunny.md",
    "site/content/activities/easter-songs-for-kids-cd.md",
    "site/content/activities/easter-songs-for-kids-choir.md",
    "site/content/activities/easter-songs-for-kids-christian.md",
    "site/content/activities/easter-songs-for-kids-church.md",
    "site/content/activities/easter-songs-for-kids-church-lyrics.md",
    "site/content/activities/easter-songs-for-kids-download.md",
    "site/content/activities/easter-songs-for-kids-for-babies.md",
    "site/content/activities/easter-songs-for-kids-for-children.md",
    "site/content/activities/easter-songs-for-kids-for-church.md",
    "site/content/guides/40-popular-sunday-school-songs.md"
]

def process_bad_files_batch(batch_size=10):
    """Process the bad files in batches using comprehensive rewriter"""
    logger.info(f"Starting reprocessing of {len(BAD_FILES)} bad files...")
    
    # Initialize comprehensive rewriter
    rewriter = ComprehensiveSeedsRewriter()
    
    # Convert string paths to Path objects and verify they exist
    valid_files = []
    for file_path_str in BAD_FILES:
        file_path = Path(file_path_str)
        if file_path.exists():
            valid_files.append(file_path)
        else:
            logger.warning(f"File not found: {file_path}")
    
    logger.info(f"Found {len(valid_files)} valid files to reprocess")
    
    # Process in batches
    total_processed = 0
    batch_num = 1
    
    for i in range(0, len(valid_files), batch_size):
        batch_files = valid_files[i:i+batch_size]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"PROCESSING BATCH {batch_num}: {len(batch_files)} files")
        logger.info(f"Files {i+1}-{min(i+batch_size, len(valid_files))} of {len(valid_files)}")
        logger.info(f"{'='*80}")
        
        batch_start_time = time.time()
        batch_success = 0
        
        for j, file_path in enumerate(batch_files):
            file_start_time = time.time()
            current_num = i + j + 1
            
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
                elif "sunday-school" in filename_lower:
                    relevant_songs.extend(rewriter.songs_by_category.get('sunday_school', [])[:8])
                    relevant_songs.extend(rewriter.songs_by_category.get('gospel_songs', [])[:4])
                elif "vbs" in filename_lower or "vacation" in filename_lower:
                    relevant_songs.extend(rewriter.songs_by_category.get('vbs_songs', []))
                    relevant_songs.extend(rewriter.songs_by_category.get('action_songs', [])[:3])
                elif "bible" in filename_lower:
                    relevant_songs.extend(rewriter.songs_by_category.get('bible_stories', []))
                    relevant_songs.extend(rewriter.songs_by_category.get('scripture_memory', [])[:3])
                elif "lullaby" in filename_lower:
                    relevant_songs.extend(rewriter.songs_by_category.get('lullabies', []))
                    relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:2])
                else:
                    # Use a diverse mix for general topics
                    relevant_songs.extend(rewriter.songs_by_category.get('sunday_school', [])[:4])
                    relevant_songs.extend(rewriter.songs_by_category.get('worship', [])[:3])
                    relevant_songs.extend(rewriter.songs_by_category.get('character_building', [])[:2])
                    relevant_songs.extend(rewriter.songs_by_category.get('gospel_songs', [])[:2])
                    relevant_songs.extend(rewriter.songs_by_category.get('faith_building', [])[:2])
                
                # Ensure we have enough songs for numbered lists if needed
                if len(relevant_songs) < 10:
                    remaining_songs = [s for s in rewriter.seeds_songs if s not in relevant_songs]
                    import random
                    relevant_songs.extend(random.sample(remaining_songs, min(10 - len(relevant_songs), len(remaining_songs))))
                
                logger.info(f"  Selected {len(relevant_songs)} relevant songs")
                
                # Create prompt and generate content using comprehensive rewriter
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
                    
                    # Update frontmatter with Seeds songs
                    song_slugs = [song.get('slug', '') for song in relevant_songs[:6] if song.get('slug')]
                    if song_slugs:
                        existing_frontmatter['seed_songs'] = song_slugs
                    
                    # Create compelling meta description
                    meta_description = rewriter.generate_compelling_meta_description(file_path.stem, new_content)
                    existing_frontmatter['description'] = meta_description
                    existing_frontmatter['meta_description'] = meta_description
                    
                    # Add schema markup
                    new_content_with_schema = rewriter.add_schema_markup(file_path.stem, new_content, relevant_songs)
                    
                    # Write updated file
                    rewriter.write_page(file_path, existing_frontmatter, new_content_with_schema)
                    
                    file_time = time.time() - file_start_time
                    logger.info(f"  ✅ SUCCESS: {file_path.name} ({file_time/60:.1f} min)")
                    batch_success += 1
                    total_processed += 1
                    
                else:
                    file_time = time.time() - file_start_time
                    logger.error(f"  ❌ FAILED: {file_path.name} - No content generated ({file_time/60:.1f} min)")
                    
            except Exception as e:
                file_time = time.time() - file_start_time
                logger.error(f"  ❌ ERROR: {file_path.name} - {str(e)} ({file_time/60:.1f} min)")
        
        # Batch summary
        batch_time = time.time() - batch_start_time
        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH {batch_num} COMPLETE:")
        logger.info(f"  Success: {batch_success}/{len(batch_files)} files")
        logger.info(f"  Time: {batch_time/60:.1f} minutes")
        logger.info(f"  Total Progress: {total_processed}/{len(valid_files)} files")
        logger.info(f"{'='*80}\n")
        
        batch_num += 1
        
        # Brief pause between batches
        if i + batch_size < len(valid_files):
            time.sleep(2)
    
    # Final summary
    logger.info(f"REPROCESSING COMPLETE!")
    logger.info(f"Successfully processed: {total_processed}/{len(valid_files)} files")
    logger.info(f"Files with bad 8-song treatment have been rewritten with comprehensive rewriter")
    
    return total_processed

if __name__ == "__main__":
    # Check if we should process all files or just a batch
    import sys
    
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
            logger.info(f"Using batch size: {batch_size}")
        except:
            batch_size = 10
            logger.info("Invalid batch size, using default: 10")
    else:
        batch_size = 10
        logger.info("Using default batch size: 10")
    
    processed_count = process_bad_files_batch(batch_size)
    logger.info(f"Reprocessing completed: {processed_count} files processed")