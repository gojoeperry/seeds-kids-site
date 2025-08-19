#!/usr/bin/env python3
"""
Generate new Hugo Markdown pages from keyword CSVs using the Anthropic API.
Creates brand-new pages with Seeds Kids Worship content.
"""

import argparse
import csv
import json
import logging
import os
import random
import re
import unicodedata
from datetime import date
from pathlib import Path
from textwrap import dedent
from time import sleep
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml
from anthropic import Anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from slugify import slugify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SeedsPageGenerator:
    def __init__(self, args):
        self.args = args
        self.client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.tfidf_vectorizer = None
        self.song_vectors = None
        self.songs_data = []
        self.style_guide = ""
        self.state_data = {"completed": []}
        self.log_entries = []
        
        # Ensure output directory exists
        Path(args.out_dir).mkdir(parents=True, exist_ok=True)
        Path("tmp").mkdir(exist_ok=True)
    
    def load_keywords(self) -> List[Dict]:
        """Load and unify keywords from CSV files"""
        logger.info(f"Loading keywords from {len(self.args.csv)} CSV files...")
        
        all_keywords = []
        seen_keywords = set()
        
        for csv_file in self.args.csv:
            if not Path(csv_file).exists():
                logger.warning(f"CSV file not found: {csv_file}")
                continue
                
            try:
                df = pd.read_csv(csv_file)
                logger.info(f"Loaded {len(df)} rows from {csv_file}")
                
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
                logger.error(f"Failed to load {csv_file}: {e}")
                continue
        
        logger.info(f"Total unique keywords loaded: {len(all_keywords)}")
        return all_keywords
    
    def load_songs(self) -> List[Dict]:
        """Load Seeds songs JSON data"""
        if not Path(self.args.songs_json).exists():
            logger.warning(f"Songs JSON not found: {self.args.songs_json}")
            return []
            
        try:
            with open(self.args.songs_json, 'r', encoding='utf-8') as f:
                songs = json.load(f)
            logger.info(f"Loaded {len(songs)} songs from {self.args.songs_json}")
            return songs
        except Exception as e:
            logger.error(f"Failed to load songs: {e}")
            return []
    
    def load_style_guide(self) -> str:
        """Load style guide if available"""
        if not self.args.style_guide or not Path(self.args.style_guide).exists():
            logger.info("No style guide provided or file not found")
            return ""
            
        try:
            with open(self.args.style_guide, 'r', encoding='utf-8') as f:
                guide = f.read()
            logger.info(f"Loaded style guide: {len(guide)} characters")
            return guide
        except Exception as e:
            logger.error(f"Failed to load style guide: {e}")
            return ""
    
    def prepare_tfidf(self, songs: List[Dict]):
        """Prepare TF-IDF vectors for song matching"""
        if not songs:
            logger.warning("No songs available for TF-IDF preparation")
            return
            
        # Build text corpus from songs
        song_texts = []
        for song in songs:
            text_parts = [
                song.get('title', ''),
                song.get('scripture', ''),
                song.get('album', ''),
                song.get('description', ''),
                song.get('target_age', ''),
                song.get('style', '')
            ]
            combined_text = ' '.join(filter(None, text_parts))
            song_texts.append(combined_text)
        
        # Create TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=5000,
            lowercase=True
        )
        
        # Fit and transform
        self.song_vectors = self.tfidf_vectorizer.fit_transform(song_texts)
        self.songs_data = songs
        
        logger.info(f"Prepared TF-IDF vectors for {len(songs)} songs")
    
    def match_songs_to_keyword(self, keyword: str) -> List[Tuple[Dict, float]]:
        """Match songs to keyword using TF-IDF similarity with adjustments"""
        if not self.tfidf_vectorizer or not self.songs_data:
            return []
        
        # Vectorize the keyword
        keyword_vector = self.tfidf_vectorizer.transform([keyword])
        
        # Calculate similarities
        similarities = cosine_similarity(keyword_vector, self.song_vectors)[0]
        
        # Apply adjustments
        adjusted_scores = []
        keyword_lower = keyword.lower()
        
        for i, (song, base_score) in enumerate(zip(self.songs_data, similarities)):
            adjusted_score = base_score
            
            # Scripture reference bonus
            scripture = song.get('scripture', '').lower()
            if scripture and any(ref in keyword_lower for ref in scripture.split()):
                adjusted_score += 0.05
            
            # Seasonal bonus
            seasonal_tokens = ['christmas', 'easter', 'vbs']
            if any(token in keyword_lower for token in seasonal_tokens):
                adjusted_score += 0.04
            
            # Age group bonus
            age_tokens = ['toddler', 'preschool', 'kids', 'family']
            if any(token in keyword_lower for token in age_tokens):
                adjusted_score += 0.03
            
            adjusted_scores.append((song, adjusted_score))
        
        # Filter by minimum score and sort
        filtered_songs = [(song, score) for song, score in adjusted_scores if score >= self.args.min_score]
        filtered_songs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return filtered_songs[:self.args.top_k]
    
    def create_slug(self, keyword: str) -> str:
        """Create a clean slug from keyword"""
        base_slug = slugify(keyword)
        if self.args.slug_prefix:
            return f"{self.args.slug_prefix}{base_slug}"
        return base_slug
    
    def generate_title(self, keyword: str) -> str:
        """Generate a proper title from keyword"""
        # Simple title case with some adjustments
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
    
    def extract_tags(self, keyword: str, cluster: str) -> List[str]:
        """Extract relevant tags from keyword and cluster"""
        tags = ['seeds-kids-worship']
        
        if cluster:
            tags.append(slugify(cluster))
        
        keyword_lower = keyword.lower()
        
        # Common tag patterns
        tag_patterns = {
            'kids': ['kid', 'children'],
            'family': ['family', 'parent'],
            'worship': ['worship', 'praise'],
            'christmas': ['christmas', 'xmas'],
            'easter': ['easter', 'resurrection'],
            'sunday-school': ['sunday school'],
            'vbs': ['vbs', 'vacation bible school'],
            'toddler': ['toddler', 'baby'],
            'preschool': ['preschool', 'pre-k']
        }
        
        for tag, patterns in tag_patterns.items():
            if any(pattern in keyword_lower for pattern in patterns):
                if tag not in tags:
                    tags.append(tag)
        
        return tags
    
    def generate_content_with_api(self, keyword: str, cluster: str, intent: str, notes: str, selected_songs: List[Dict]) -> str:
        """Generate article content using Anthropic API"""
        
        # Build the prompt
        system_prompt = dedent("""
            You are a careful, biblically faithful editor for Seeds Kids Worship. 
            Write parent-friendly, web-ready pages in a warm, encouraging tone. 
            Follow the style guide strictly. Do not include full song lyrics.
        """).strip()
        
        # Prepare context
        context_parts = []
        
        if self.style_guide:
            context_parts.append(f"STYLE GUIDE:\n{self.style_guide}")
        
        context_parts.append(f"KEYWORD: {keyword}")
        if cluster:
            context_parts.append(f"CLUSTER: {cluster}")
        if intent:
            context_parts.append(f"INTENT: {intent}")
        if notes:
            context_parts.append(f"NOTES: {notes}")
        
        if selected_songs:
            songs_context = "SELECTED SEEDS SONGS:\n"
            for song in selected_songs:
                songs_context += f"- {song.get('title', 'Untitled')}"
                if song.get('scripture'):
                    songs_context += f" (Scripture: {song['scripture']})"
                if song.get('description'):
                    songs_context += f" - {song['description'][:100]}..."
                if song.get('webpage_url'):
                    songs_context += f" [Link: {song['webpage_url']}]"
                songs_context += "\n"
            context_parts.append(songs_context)
        
        constraints = dedent("""
            OUTPUT CONSTRAINTS:
            - Length target: ~700–900 words
            - Structure:
              (a) Hook/intro framing the keyword and audience (parents/church leaders)
              (b) Accurate Scripture tie-ins; brief references only
              (c) How featured Seeds songs help kids learn this topic; 2–3 family applications
              (d) Short FAQ (2–3 Q&As) matched to the keyword
              (e) Call-to-action consistent with brand voice
            - Inline link song titles to webpage_url when present
            - Avoid full lyrics; paraphrase themes or brief lines only if necessary
            - Plain Markdown only; no templates or YAML
            - No emojis
        """).strip()
        
        context_parts.append(constraints)
        
        user_content = "\n\n".join(context_parts)
        
        # Make API call with retries
        retry_delays = [5, 10, 15, 20, 25]
        
        for attempt, delay in enumerate(retry_delays, 1):
            try:
                response = self.client.messages.create(
                    model=self.args.model,
                    max_tokens=self.args.max_tokens,
                    temperature=self.args.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_content}
                    ]
                )
                
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    logger.warning(f"Empty response from API for keyword: {keyword}")
                    break
                    
            except Exception as e:
                logger.warning(f"API attempt {attempt} failed for '{keyword}': {e}")
                if attempt < len(retry_delays):
                    logger.info(f"Retrying in {delay} seconds...")
                    sleep(delay)
                else:
                    logger.error(f"All API retries failed for '{keyword}'")
                    break
        
        # Fallback content
        logger.info(f"Creating fallback content for '{keyword}'")
        fallback_content = self.create_fallback_content(keyword, selected_songs)
        return fallback_content
    
    def create_fallback_content(self, keyword: str, selected_songs: List[Dict]) -> str:
        """Create minimal stub content when API fails"""
        title = self.generate_title(keyword)
        
        content = f"# {title}\n\n"
        content += f"Explore the wonderful world of {keyword} with Seeds Kids Worship. "
        content += "Our Scripture-based songs help families sing God's Word together.\n\n"
        
        if selected_songs:
            content += "## Featured Songs\n\n"
            for song in selected_songs:
                song_title = song.get('title', 'Untitled')
                if song.get('webpage_url'):
                    content += f"- [{song_title}]({song['webpage_url']})\n"
                else:
                    content += f"- {song_title}\n"
        
        content += "\n## Transform Your Family's Worship Time\n\n"
        content += "Ready to hide God's Word in your children's hearts? "
        content += "Start with these Scripture songs and watch your family's worship time transform.\n"
        
        return content
    
    def create_featured_songs_block(self, songs: List[Dict]) -> str:
        """Create the featured songs HTML block"""
        if not songs:
            return ""
        
        block = "<!-- featured-songs:start -->\n## Featured Songs\n"
        for song in songs:
            title = song.get('title', 'Untitled')
            url = song.get('webpage_url', '')
            description = song.get('description', '')
            
            if description and len(description) > 120:
                description = description[:120].rsplit(' ', 1)[0] + '...'
            
            if url:
                block += f"- [{title}]({url})"
            else:
                block += f"- {title}"
            
            if description:
                block += f" — {description}"
            block += "\n"
        
        block += "<!-- featured-songs:end -->\n"
        return block
    
    def create_resources_block(self, songs: List[Dict]) -> str:
        """Create the resources HTML block"""
        spotify_urls = [song.get('spotify_url') for song in songs if song.get('spotify_url')]
        
        block = "<!-- resources:start -->\n<div class=\"resources\">\n"
        
        if spotify_urls:
            block += f'  <p><a href="{spotify_urls[0]}">Listen on Spotify</a></p>\n'
        
        block += '  <p><small>Sing God\'s Word with your family.</small></p>\n'
        block += "</div>\n<!-- resources:end -->\n"
        
        return block
    
    def create_frontmatter(self, keyword: str, cluster: str, selected_songs: List[Dict], content: str) -> Dict:
        """Create YAML frontmatter"""
        title = self.generate_title(keyword)
        slug = self.create_slug(keyword)
        tags = self.extract_tags(keyword, cluster)
        
        # Extract description from content (first paragraph or generate)
        content_lines = content.split('\n')
        description = ""
        for line in content_lines[2:]:  # Skip title and empty line
            if line.strip() and not line.startswith('#'):
                description = line.strip()[:200]
                if len(description) > 150:
                    description = description[:150].rsplit(' ', 1)[0] + '...'
                break
        
        if not description:
            description = f"Discover how {keyword} can transform your family's worship time with Scripture-based songs from Seeds Kids Worship."
        
        # Meta description (<=160 chars)
        meta_description = description
        if len(meta_description) > 160:
            meta_description = meta_description[:160].rsplit(' ', 1)[0] + '...'
        
        # Song slugs
        seed_songs = [slugify(song.get('title', '')) for song in selected_songs if song.get('title')]
        
        frontmatter = {
            'title': title,
            'slug': slug,
            'description': description,
            'meta_description': meta_description,
            'tags': tags,
            'seed_songs': seed_songs,
            'date': date.today().isoformat()
        }
        
        return frontmatter
    
    def write_page(self, keyword: str, cluster: str, intent: str, notes: str) -> Tuple[str, str, str]:
        """Write a single page"""
        slug = self.create_slug(keyword)
        file_path = Path(self.args.out_dir) / f"{slug}.md"
        
        # Check if file exists
        if file_path.exists() and not self.args.overwrite:
            return slug, "exists", str(file_path)
        
        # Match songs
        matched_songs = self.match_songs_to_keyword(keyword)
        selected_songs = [song for song, score in matched_songs]
        
        if self.args.dry_run:
            logger.info(f"[DRY RUN] Would create: {file_path}")
            logger.info(f"[DRY RUN] Matched {len(selected_songs)} songs")
            return slug, "dry_run", str(file_path)
        
        # Generate content
        try:
            content = self.generate_content_with_api(keyword, cluster, intent, notes, selected_songs)
            action_note = ""
        except Exception as e:
            logger.error(f"Content generation failed for '{keyword}': {e}")
            content = self.create_fallback_content(keyword, selected_songs)
            action_note = "api_fallback"
        
        # Create frontmatter
        frontmatter = self.create_frontmatter(keyword, cluster, selected_songs, content)
        
        # Add footer blocks
        content += "\n\n"
        content += self.create_featured_songs_block(selected_songs)
        content += "\n"
        content += self.create_resources_block(selected_songs)
        
        # Ensure content ends with newline
        if not content.endswith('\n'):
            content += '\n'
        
        # Write file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
                f.write("---\n")
                f.write(content)
            
            action = "overwritten" if file_path.exists() else "created"
            return slug, action, str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return slug, "failed", str(file_path)
    
    def load_state(self):
        """Load resume state if available"""
        if not self.args.resume or not Path(self.args.state_path).exists():
            return
        
        try:
            with open(self.args.state_path, 'r') as f:
                self.state_data = json.load(f)
            logger.info(f"Loaded state: {len(self.state_data.get('completed', []))} completed items")
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
            self.state_data = {"completed": []}
    
    def save_state(self):
        """Save current state"""
        if self.args.dry_run:
            return
        
        try:
            # Ensure parent directory exists
            Path(self.args.state_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write atomically
            temp_path = Path(str(self.args.state_path) + '.tmp')
            with open(temp_path, 'w') as f:
                json.dump(self.state_data, f, indent=2)
            temp_path.rename(self.args.state_path)
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def save_log(self):
        """Save processing log"""
        if not self.log_entries:
            return
        
        log_path = Path("tmp/generate_pages.csv")
        log_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['slug', 'keyword', 'cluster', 'selected_songs', 'action', 'action_note', 'path'])
                writer.writerows(self.log_entries)
            
            logger.info(f"Saved processing log to {log_path}")
        except Exception as e:
            logger.error(f"Failed to save log: {e}")
    
    def run(self):
        """Main execution"""
        logger.info("Starting Seeds page generation...")
        
        # Load data
        keywords = self.load_keywords()
        if not keywords:
            logger.error("No keywords loaded, exiting")
            return
        
        self.songs_data = self.load_songs()
        self.style_guide = self.load_style_guide()
        
        # Prepare TF-IDF
        self.prepare_tfidf(self.songs_data)
        
        # Load state for resume
        self.load_state()
        completed_slugs = set(self.state_data.get("completed", []))
        
        # Apply limit
        if self.args.limit > 0:
            keywords = keywords[:self.args.limit]
        
        # Order keywords
        if self.args.order == "random":
            random.seed(42)  # For reproducibility
            random.shuffle(keywords)
        else:
            keywords.sort(key=lambda x: x['keyword'])
        
        # Filter out completed items
        if self.args.resume:
            original_count = len(keywords)
            keywords = [kw for kw in keywords if self.create_slug(kw['keyword']) not in completed_slugs]
            logger.info(f"Resume: skipped {original_count - len(keywords)} completed items")
        
        # Process in batches
        batch_keywords = keywords[:self.args.batch_size]
        logger.info(f"Processing batch of {len(batch_keywords)} keywords")
        
        # Stats
        stats = {
            "seen": 0,
            "created": 0,
            "overwritten": 0,
            "exists": 0,
            "dry_run": 0,
            "failed": 0
        }
        
        # Process each keyword
        for i, kw in enumerate(batch_keywords, 1):
            keyword = kw['keyword']
            cluster = kw['cluster']
            intent = kw['intent']
            notes = kw['notes']
            
            logger.info(f"[{i}/{len(batch_keywords)}] Processing: {keyword}")
            
            slug, action, file_path = self.write_page(keyword, cluster, intent, notes)
            
            # Update stats
            stats["seen"] += 1
            stats[action] = stats.get(action, 0) + 1
            
            # Log entry
            selected_songs_titles = ""
            if not self.args.dry_run:
                matched_songs = self.match_songs_to_keyword(keyword)
                selected_songs_titles = " | ".join([song.get('title', '') for song, _ in matched_songs])
            
            self.log_entries.append([
                slug, keyword, cluster, selected_songs_titles, action, "", file_path
            ])
            
            # Update state for all processed items (not just created/overwritten)
            if not self.args.dry_run:
                if slug not in self.state_data["completed"]:
                    self.state_data["completed"].append(slug)
                self.save_state()
        
        # Save log
        self.save_log()
        
        # Print summary
        logger.info("=== PROCESSING SUMMARY ===")
        for key, value in stats.items():
            if value > 0:
                logger.info(f"{key.upper()}: {value}")
        
        logger.info("Generation complete!")

def main():
    parser = argparse.ArgumentParser(description="Generate Seeds Kids Worship pages from keyword CSVs")
    
    # Input files
    parser.add_argument('--csv', action='append', required=True,
                       help='CSV files containing keywords (can specify multiple)')
    parser.add_argument('--songs-json', default='./assets/seeds_songs.json',
                       help='Seeds songs JSON file')
    parser.add_argument('--style-guide', default='./style/seeds_style_guide.txt',
                       help='Style guide file')
    
    # Output options
    parser.add_argument('--out-dir', default='./site/content/guides',
                       help='Output directory for generated pages')
    parser.add_argument('--slug-prefix', default='',
                       help='Optional prefix for slugs')
    
    # Song matching
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of songs to feature')
    parser.add_argument('--min-score', type=float, default=0.18,
                       help='Minimum similarity score for song selection')
    
    # Processing options
    parser.add_argument('--batch-size', type=int, default=15,
                       help='Number of items to process per run')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from state file if present')
    parser.add_argument('--state-path', default='./tmp/generate_state.json',
                       help='State file path for resume functionality')
    parser.add_argument('--order', choices=['keyword', 'random'], default='keyword',
                       help='Processing order')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit number of items to process (0 = all)')
    parser.add_argument('--overwrite', action='store_true',
                       help='Overwrite existing files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run - do not write files')
    
    # API options
    parser.add_argument('--model', default='claude-sonnet-4-20250514',
                       help='Anthropic model to use')
    parser.add_argument('--temperature', type=float, default=0.6,
                       help='Temperature for content generation')
    parser.add_argument('--max-tokens', type=int, default=1400,
                       help='Maximum tokens for API response')
    
    args = parser.parse_args()
    
    # Validate API key
    if not os.getenv('CLAUDE_API_KEY'):
        logger.error("CLAUDE_API_KEY environment variable not set")
        return 1
    
    # Run generator
    try:
        generator = SeedsPageGenerator(args)
        generator.run()
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())