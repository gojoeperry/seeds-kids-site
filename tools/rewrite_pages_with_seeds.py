#!/usr/bin/env python3
"""
Rewrite Hugo Markdown pages to focus on Seeds Kids Worship content using TF-IDF similarity matching.
"""
import argparse
import csv
import json
import os
import re
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import warnings

import pandas as pd
import yaml
from anthropic import Anthropic
from markdown_it import MarkdownIt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning)


class SeedsPageRewriter:
    def __init__(self, args):
        self.args = args
        self.anthropic = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.md_parser = MarkdownIt()
        
        # Load data
        self.songs = self._load_songs()
        self.style_guide = self._load_style_guide()
        
        # Build TF-IDF index
        self.vectorizer, self.song_vectors = self._build_song_index()
        
        # Logging
        self.report_data = []
        
        # Stats
        self.stats = {
            'pages_scanned': 0,
            'pages_rewritten': 0,
            'pages_skipped_no_match': 0,
            'pages_stubbed': 0,
            'total_songs_selected': 0,
            'total_seen': 0,
            'already_done': 0,
            'processed_this_run': 0,
            'remaining': 0
        }
        
        # State management
        self.state_file = Path(args.state_path)
        self.state = self._load_state() if args.resume else None
    
    def _load_songs(self) -> List[Dict]:
        """Load songs from JSON file."""
        try:
            with open(self.args.songs_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading songs JSON: {e}")
            return []
    
    def _load_style_guide(self) -> str:
        """Load style guide text."""
        try:
            with open(self.args.style_guide, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error loading style guide: {e}")
            return ""
    
    def _load_state(self) -> Optional[Dict]:
        """Load state from JSON file for resume functionality."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    print(f"Loaded state with {len(state.get('completed', []))} completed files")
                    return state
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
        return None
    
    def _save_state(self, completed_files: List[str]) -> None:
        """Save state to JSON file atomically."""
        if self.args.dry_run:
            return
        
        # Ensure directory exists
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Prepare state data
        state = {
            'model': self.args.model,
            'temperature': self.args.temperature,
            'max_tokens': self.args.max_tokens,
            'completed': completed_files
        }
        
        # Atomic write via temp file
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8',
                dir=self.state_file.parent,
                delete=False,
                suffix='.tmp'
            ) as temp_f:
                json.dump(state, temp_f, indent=2)
                temp_path = temp_f.name
            
            # Rename temp file to actual state file
            Path(temp_path).replace(self.state_file)
            
        except Exception as e:
            print(f"Warning: Could not save state file: {e}")
            # Clean up temp file if it exists
            if 'temp_path' in locals() and Path(temp_path).exists():
                Path(temp_path).unlink()
    
    def _build_song_index(self) -> Tuple[TfidfVectorizer, np.ndarray]:
        """Build TF-IDF index for song similarity matching."""
        if not self.songs:
            print("No songs loaded, creating empty index")
            vectorizer = TfidfVectorizer()
            return vectorizer, np.array([])
        
        # Build text representation for each song
        song_texts = []
        for song in self.songs:
            text_parts = [
                song.get('title', ''),
                song.get('scripture', ''),
                song.get('album', ''),
                song.get('description', ''),
                song.get('target_age', ''),
                song.get('style', ''),
                # Extract keywords from title and scripture
                self._extract_keywords(song.get('title', '')),
                self._extract_keywords(song.get('scripture', ''))
            ]
            song_texts.append(' '.join(filter(None, text_parts)))
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=10000,
            lowercase=True
        )
        
        try:
            song_vectors = vectorizer.fit_transform(song_texts)
            return vectorizer, song_vectors
        except Exception as e:
            print(f"Error building TF-IDF index: {e}")
            return vectorizer, np.array([])
    
    def _extract_keywords(self, text: str) -> str:
        """Extract meaningful keywords from text."""
        if not text:
            return ""
        
        # Simple keyword extraction - split on common delimiters
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words and short words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        return ' '.join(keywords)
    
    def _discover_markdown_files(self) -> List[Path]:
        """Discover markdown files matching include/exclude patterns with deterministic ordering."""
        all_files = []
        
        for content_dir in self.args.content_dir:
            content_path = Path(content_dir)
            if not content_path.exists():
                print(f"Warning: Content directory not found: {content_dir}")
                continue
            
            # Find files matching include pattern
            if self.args.include:
                files = list(content_path.glob(self.args.include))
            else:
                files = list(content_path.rglob("*.md"))
            
            # Filter out excluded files
            if self.args.exclude:
                exclude_pattern = self.args.exclude
                files = [f for f in files if not f.match(exclude_pattern)]
            
            all_files.extend(files)
        
        # Deterministic ordering
        if self.args.order == 'path':
            # Sort by normalized absolute path (case-insensitive)
            all_files.sort(key=lambda f: str(f.resolve()).lower())
        elif self.args.order == 'mtime':
            # Sort by last modified time ascending
            all_files.sort(key=lambda f: f.stat().st_mtime)
        
        return all_files
    
    def _parse_front_matter(self, content: str) -> Tuple[Dict, str, str]:
        """Parse YAML front matter from markdown content."""
        # Detect original line endings
        if '\r\n' in content:
            original_newlines = '\r\n'
        elif '\r' in content:
            original_newlines = '\r'
        else:
            original_newlines = '\n'
        
        # Normalize to \n for processing
        normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        if not normalized_content.startswith('---\n'):
            return {}, normalized_content, original_newlines
        
        try:
            # Find end of front matter
            end_match = re.search(r'\n---\n', normalized_content[4:])
            if not end_match:
                return {}, normalized_content, original_newlines
            
            end_pos = end_match.start() + 4
            front_matter_str = normalized_content[4:end_pos]
            body = normalized_content[end_pos + 4:]
            
            # Parse YAML
            front_matter = yaml.safe_load(front_matter_str) or {}
            
            return front_matter, body, original_newlines
            
        except yaml.YAMLError as e:
            print(f"YAML parsing error: {e}")
            return {}, normalized_content, original_newlines
    
    def _markdown_to_text(self, markdown_text: str) -> str:
        """Convert markdown to plain text for analysis."""
        try:
            # Parse markdown and extract text
            tokens = self.md_parser.parse(markdown_text)
            text_parts = []
            
            for token in tokens:
                if token.type == 'paragraph_open':
                    continue
                elif token.type == 'heading_open':
                    continue
                elif token.type == 'inline' and token.content:
                    # Remove markdown formatting
                    clean_text = re.sub(r'[*_`\[\]()#]', '', token.content)
                    text_parts.append(clean_text)
            
            return ' '.join(text_parts)
        except Exception:
            # Fallback: simple regex-based markdown stripping
            text = re.sub(r'[*_`#]', '', markdown_text)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
            text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)  # Images
            return text
    
    def _build_query_text(self, front_matter: Dict, body: str) -> str:
        """Build query text from page content."""
        parts = []
        
        # Front matter title
        if 'title' in front_matter:
            parts.append(front_matter['title'])
        
        # Description/meta
        for key in ['description', 'meta_description']:
            if key in front_matter:
                parts.append(str(front_matter[key]))
        
        # Extract headings and first ~200 words from body
        body_text = self._markdown_to_text(body)
        
        # Get headings
        heading_matches = re.findall(r'^#+\s+(.+)$', body, re.MULTILINE)
        parts.extend(heading_matches)
        
        # Get first ~200 words from body
        words = body_text.split()[:200]
        parts.append(' '.join(words))
        
        return ' '.join(filter(None, parts))
    
    def _calculate_similarity_scores(self, query_text: str) -> List[Tuple[int, float]]:
        """Calculate similarity scores between query and all songs."""
        if self.song_vectors.shape[0] == 0:
            return []
        
        try:
            # Vectorize query
            query_vector = self.vectorizer.transform([query_text])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_vector, self.song_vectors).flatten()
            
            # Return list of (song_index, score) tuples
            return [(i, float(score)) for i, score in enumerate(similarities)]
            
        except Exception as e:
            print(f"Error calculating similarities: {e}")
            return []
    
    def _apply_score_adjustments(self, scores: List[Tuple[int, float]], page_title: str, page_body: str) -> List[Tuple[int, float]]:
        """Apply rule-based score adjustments."""
        adjusted_scores = []
        page_title_lower = page_title.lower()
        page_body_lower = page_body.lower()
        
        for song_idx, base_score in scores:
            song = self.songs[song_idx]
            adjusted_score = base_score
            
            # Scripture/album match bonus
            scripture = song.get('scripture', '').lower()
            album = song.get('album', '').lower()
            
            if scripture and any(word in page_title_lower for word in scripture.split()):
                adjusted_score += 0.05
            if album and any(word in page_title_lower for word in album.split()):
                adjusted_score += 0.05
            
            # Age group match bonus
            target_age = song.get('target_age', '').lower()
            age_keywords = ['preschool', 'kids', 'children', 'family', 'toddler', 'baby', 'adult']
            if target_age:
                for keyword in age_keywords:
                    if keyword in target_age and (keyword in page_title_lower or keyword in page_body_lower):
                        adjusted_score += 0.05
                        break
            
            # Seasonal match bonus
            seasonal_keywords = ['christmas', 'easter', 'vbs', 'vacation bible school']
            song_text = f"{song.get('title', '')} {song.get('description', '')} {song.get('album', '')}".lower()
            
            for keyword in seasonal_keywords:
                if keyword in page_title_lower and keyword in song_text:
                    adjusted_score += 0.06
                    break
            
            adjusted_scores.append((song_idx, adjusted_score))
        
        return adjusted_scores
    
    def _select_top_songs(self, scores: List[Tuple[int, float]]) -> List[Dict]:
        """Select top-k songs above minimum score threshold."""
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by minimum score and take top-k
        selected = []
        for song_idx, score in scores:
            if score >= self.args.min_score and len(selected) < self.args.top_k:
                song = self.songs[song_idx]
                selected.append({
                    'title': song.get('title', ''),
                    'slug': song.get('slug', ''),
                    'scripture': song.get('scripture', ''),
                    'description': song.get('description', ''),
                    'webpage_url': song.get('webpage_url', ''),
                    'spotify_url': song.get('spotify_url', ''),
                    'album': song.get('album', ''),
                    'target_age': song.get('target_age', ''),
                    'score': score
                })
        
        return selected
    
    def _call_anthropic_with_retry(self, system_prompt: str, user_content: str) -> Optional[str]:
        """Call Anthropic API with retry logic."""
        backoff_delays = [5, 10, 15, 20, 25]  # seconds
        
        for attempt in range(5):
            try:
                response = self.anthropic.messages.create(
                    model=self.args.model,
                    max_tokens=self.args.max_tokens,
                    temperature=self.args.temperature,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_content
                    }]
                )
                
                return response.content[0].text if response.content else None
                
            except Exception as e:
                print(f"Anthropic API call attempt {attempt + 1} failed: {e}")
                if attempt < 4:  # Don't sleep on last attempt
                    time.sleep(backoff_delays[attempt])
                continue
        
        return None
    
    def _create_anthropic_prompt(self, front_matter: Dict, body: str, selected_songs: List[Dict]) -> Tuple[str, str]:
        """Create system and user prompts for Anthropic."""
        system_prompt = (
            "You are a careful, biblically faithful editor for Seeds Kids Worship. "
            "Write parent-friendly, web-ready pages in a warm, encouraging tone. "
            "Follow the style guide strictly. Do not include full song lyrics."
        )
        
        # Build user content
        user_parts = [
            "# STYLE GUIDE",
            self.style_guide,
            "",
            "# PAGE SNAPSHOT",
            "## Current Front Matter (YAML)",
            yaml.dump(front_matter, default_flow_style=False),
            "",
            "## Current Body (Markdown)",
            body,
            "",
            "# SELECTED SONGS",
            json.dumps(selected_songs, indent=2),
            "",
            "# REWRITE CONSTRAINTS",
            "- Replace generic content with a focused guide that highlights the selected Seeds songs (by title and scripture).",
            "- Length target: ~700–900 words.",
            "- Structure:",
            "  1) Intro that frames the page topic and mentions Seeds songs by name.",
            "  2) Scripture integration (accurate, short references only).",
            "  3) How these songs help kids learn (themes), with 2–3 simple family applications.",
            "  4) Short FAQ (2–3 Q&As) relevant to the topic and songs.",
            "  5) Closing call-to-action consistent with the brand voice.",
            "- Include inline links for each featured song using its webpage_url when present; otherwise leave the song name without a link.",
            "- Do not reproduce full lyrics; paraphrase themes or use brief quotes only if necessary.",
            "- Keep headings and lists in clean Markdown. Do not include JSON, YAML, or templating tags in the body.",
            "- No emojis.",
            "",
            "Please rewrite the page body (markdown only, no front matter) following these constraints:"
        ]
        
        return system_prompt, '\n'.join(user_parts)
    
    def _create_fallback_content(self, selected_songs: List[Dict], original_title: str) -> str:
        """Create fallback content when API call fails."""
        content_parts = [
            f"# {original_title}",
            "",
            "Discover how Seeds Kids Worship songs can help your family grow in faith through music and Scripture.",
            ""
        ]
        
        if selected_songs:
            content_parts.extend([
                "## Featured Songs from Seeds Kids Worship",
                ""
            ])
            
            for song in selected_songs:
                title = song['title']
                scripture = song['scripture']
                description = song['description'][:100] + "..." if len(song['description']) > 100 else song['description']
                
                if song['webpage_url']:
                    content_parts.append(f"### [{title}]({song['webpage_url']})")
                else:
                    content_parts.append(f"### {title}")
                
                if scripture:
                    content_parts.append(f"**Scripture:** {scripture}")
                
                if description:
                    content_parts.append(f"{description}")
                
                content_parts.append("")
        
        content_parts.extend([
            "## How to Use These Songs",
            "",
            "These carefully selected songs from Seeds Kids Worship help children:",
            "- Learn Scripture through memorable melodies",
            "- Develop a heart for worship",
            "- Build biblical foundations for life",
            "",
            "## Getting Started",
            "",
            "Start by listening to these songs with your family and discussing the Bible verses they're based on. "
            "Seeds Kids Worship makes it easy to bring biblical truth into your daily routine through music.",
        ])
        
        return '\n'.join(content_parts)
    
    def _generate_featured_songs_section(self, selected_songs: List[Dict]) -> str:
        """Generate the featured songs section."""
        if not selected_songs:
            return ""
        
        lines = [
            "<!-- featured-songs:start -->",
            "## Featured Songs"
        ]
        
        for song in selected_songs:
            title = song['title']
            webpage_url = song['webpage_url']
            description = song['description']
            
            # Truncate description to ~120 chars
            if len(description) > 120:
                description = description[:117] + "..."
            
            if webpage_url:
                lines.append(f"- [{title}]({webpage_url}) — {description}")
            else:
                lines.append(f"- {title} — {description}")
        
        lines.append("<!-- featured-songs:end -->")
        return '\n'.join(lines)
    
    def _generate_resources_section(self, selected_songs: List[Dict]) -> str:
        """Generate the resources section."""
        lines = [
            "<!-- resources:start -->",
            '<div class="resources">'
        ]
        
        # Find first song with Spotify URL
        spotify_url = None
        for song in selected_songs:
            if song.get('spotify_url'):
                spotify_url = song['spotify_url']
                break
        
        if spotify_url:
            lines.append(f'  <p><a href="{spotify_url}">Listen on Spotify</a></p>')
        
        lines.extend([
            '  <p><small>Sing God\'s Word with your family.</small></p>',
            '</div>',
            '<!-- resources:end -->'
        ])
        
        return '\n'.join(lines)
    
    def _update_meta_description(self, front_matter: Dict, new_body: str) -> None:
        """Update meta description if missing or too long."""
        current_meta = front_matter.get('meta_description', '')
        
        if not current_meta or len(current_meta) > 160:
            # Extract first sentence or paragraph from new body
            body_text = self._markdown_to_text(new_body)
            sentences = re.split(r'[.!?]+', body_text)
            
            if sentences:
                new_meta = sentences[0].strip()
                if len(new_meta) > 160:
                    # Truncate at word boundary
                    words = new_meta.split()
                    truncated = []
                    length = 0
                    
                    for word in words:
                        if length + len(word) + 1 > 157:  # +1 for space, 3 for ellipsis
                            break
                        truncated.append(word)
                        length += len(word) + 1
                    
                    new_meta = ' '.join(truncated) + "..."
                
                front_matter['meta_description'] = new_meta
    
    def _replace_idempotent_blocks(self, body: str, featured_songs_section: str, resources_section: str) -> str:
        """Replace existing featured songs and resources blocks."""
        # Remove existing blocks
        body = re.sub(r'<!-- featured-songs:start -->.*?<!-- featured-songs:end -->', '', body, flags=re.DOTALL)
        body = re.sub(r'<!-- resources:start -->.*?<!-- resources:end -->', '', body, flags=re.DOTALL)
        
        # Clean up extra whitespace
        body = body.rstrip()
        
        # Append new blocks
        if featured_songs_section:
            body += '\n\n' + featured_songs_section
        
        if resources_section:
            body += '\n\n' + resources_section
        
        return body + '\n'
    
    def _process_file(self, file_path: Path) -> bool:
        """Process a single markdown file. Returns True if successfully processed."""
        self.stats['pages_scanned'] += 1
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Parse front matter and body
            front_matter, body, original_newlines = self._parse_front_matter(original_content)
            
            # Build query text
            page_title = front_matter.get('title', file_path.stem)
            query_text = self._build_query_text(front_matter, body)
            
            # Calculate similarities
            scores = self._calculate_similarity_scores(query_text)
            
            if not scores:
                self._log_result(file_path, [], [], 'skipped_no_songs', 0, 'No songs loaded')
                return False
            
            # Apply adjustments
            adjusted_scores = self._apply_score_adjustments(scores, page_title, body)
            
            # Select top songs
            selected_songs = self._select_top_songs(adjusted_scores)
            
            if not selected_songs:
                self._log_result(file_path, [], [], 'skipped_no_match', 0, f'No songs above threshold {self.args.min_score}')
                self.stats['pages_skipped_no_match'] += 1
                return False
            
            # Track stats
            self.stats['total_songs_selected'] += len(selected_songs)
            
            if self.args.dry_run:
                song_titles = [s['title'] for s in selected_songs]
                song_scores = [f"{s['score']:.3f}" for s in selected_songs]
                self._log_result(file_path, song_titles, song_scores, 'dry_run', 0, f'Would rewrite with {len(selected_songs)} songs')
                return True  # Dry run counts as success
            
            # Call Anthropic API
            system_prompt, user_content = self._create_anthropic_prompt(front_matter, body, selected_songs)
            new_body = self._call_anthropic_with_retry(system_prompt, user_content)
            
            if not new_body:
                # Fallback to stub content
                new_body = self._create_fallback_content(selected_songs, page_title)
                action = 'stub'
                self.stats['pages_stubbed'] += 1
            else:
                action = 'rewritten'
                self.stats['pages_rewritten'] += 1
            
            # Update meta description
            self._update_meta_description(front_matter, new_body)
            
            # Generate sections
            featured_songs_section = self._generate_featured_songs_section(selected_songs)
            resources_section = self._generate_resources_section(selected_songs)
            
            # Replace idempotent blocks
            final_body = self._replace_idempotent_blocks(new_body, featured_songs_section, resources_section)
            
            # Serialize updated content
            fm_yaml = yaml.dump(front_matter, default_flow_style=False, sort_keys=False)
            updated_content = f"---\n{fm_yaml}---\n{final_body}"
            
            # Restore original line endings
            if original_newlines != '\n':
                updated_content = updated_content.replace('\n', original_newlines)
            
            # Ensure trailing newline
            if not updated_content.endswith(('\n', '\r\n', '\r')):
                updated_content += original_newlines
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            # Log success
            song_titles = [s['title'] for s in selected_songs]
            song_scores = [f"{s['score']:.3f}" for s in selected_songs]
            tokens_out = len(new_body.split()) if new_body else 0
            
            self._log_result(file_path, song_titles, song_scores, action, tokens_out, f'Success with {len(selected_songs)} songs')
            
            print(f"{'[DRY RUN] ' if self.args.dry_run else ''}Processed: {file_path.name} ({len(selected_songs)} songs selected)")
            return True
            
        except Exception as e:
            self._log_result(file_path, [], [], 'error', 0, str(e))
            print(f"Error processing {file_path}: {e}")
            return False
    
    def _log_result(self, file_path: Path, song_titles: List[str], scores: List[str], action: str, tokens_out: int, notes: str):
        """Log processing result."""
        self.report_data.append({
            'file': str(file_path),
            'selected_songs': '|'.join(song_titles),
            'scores': '|'.join(scores),
            'action': action,
            'tokens_out': tokens_out,
            'notes': notes
        })
    
    def _save_report(self):
        """Save processing report."""
        report_path = Path('./tmp/rewrite_with_seeds.csv')
        report_path.parent.mkdir(exist_ok=True)
        
        df = pd.DataFrame(self.report_data)
        df.to_csv(report_path, index=False)
        print(f"Report saved to: {report_path}")
    
    def run(self):
        """Run the page rewriting process with batch processing and resume support."""
        print(f"Loading {len(self.songs)} songs...")
        
        if not self.songs:
            print("No songs loaded. Exiting.")
            return
        
        # Discover all files deterministically
        all_files = self._discover_markdown_files()
        self.stats['total_seen'] = len(all_files)
        print(f"Found {len(all_files)} markdown files total...")
        
        # Convert to relative paths for consistent state tracking
        # Use the parent of the working directory as the base for relative paths
        base_dir = Path.cwd().parent if Path.cwd().name == 'tools' else Path.cwd()
        all_files_relative = []
        for f in all_files:
            try:
                rel_path = str(f.resolve().relative_to(base_dir))
                all_files_relative.append((rel_path, f))
            except ValueError:
                # File outside of base directory, use absolute path
                rel_path = str(f.resolve())
                all_files_relative.append((rel_path, f))
        
        # Get completed files from state
        completed_files = set()
        if self.state:
            completed_files = set(self.state.get('completed', []))
            self.stats['already_done'] = len(completed_files)
            print(f"Resuming: {len(completed_files)} files already completed")
        
        # Filter out completed files and apply legacy limit if specified
        files_to_process = []
        for rel_path, file_path in all_files_relative:
            if rel_path not in completed_files:
                files_to_process.append((rel_path, file_path))
        
        # Apply legacy limit if specified and not resuming
        if self.args.limit > 0 and not self.args.resume:
            files_to_process = files_to_process[:self.args.limit]
            
        # Apply batch size limit
        batch_files = files_to_process[:self.args.batch_size]
        self.stats['remaining'] = len(files_to_process) - len(batch_files)
        
        if self.args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            print(f"Would process {len(batch_files)} files this batch")
            if self.stats['remaining'] > 0:
                print(f"Would leave {self.stats['remaining']} files for future batches")
        else:
            print(f"Processing {len(batch_files)} files this batch")
            if self.stats['remaining'] > 0:
                print(f"Will leave {self.stats['remaining']} files for future batches")
        
        # Process files in batch
        newly_completed = list(completed_files)  # Start with existing completed files
        
        for rel_path, file_path in batch_files:
            success = self._process_file(file_path)
            
            if success:
                self.stats['processed_this_run'] += 1
                newly_completed.append(rel_path)
                # Save state after each successful file (atomic)
                self._save_state(newly_completed)
        
        # Save report
        self._save_report()
        
        # Print summary
        avg_songs = (self.stats['total_songs_selected'] / max(1, self.stats['pages_rewritten'] + self.stats['pages_stubbed']))
        
        print(f"\nSummary:")
        print(f"Total files seen: {self.stats['total_seen']}")
        print(f"Already completed: {self.stats['already_done']}")
        print(f"Processed this run: {self.stats['processed_this_run']}")
        print(f"Remaining for future batches: {self.stats['remaining']}")
        print(f"Pages scanned: {self.stats['pages_scanned']}")
        print(f"Pages rewritten: {self.stats['pages_rewritten']}")
        print(f"Pages stubbed: {self.stats['pages_stubbed']}")
        print(f"Pages skipped (no match): {self.stats['pages_skipped_no_match']}")
        if self.stats['pages_rewritten'] + self.stats['pages_stubbed'] > 0:
            print(f"Average songs selected per page: {avg_songs:.1f}")
        
        # Progress info - only count files actually in the current scope
        total_in_scope_completed = len([rel_path for rel_path, _ in all_files_relative if rel_path in completed_files]) + self.stats['processed_this_run']
        if self.stats['total_seen'] > 0:
            progress = (total_in_scope_completed / self.stats['total_seen']) * 100
            print(f"Overall progress: {total_in_scope_completed}/{self.stats['total_seen']} ({progress:.1f}%)")
        
        if self.stats['remaining'] > 0:
            print(f"\nTo continue: add --resume to process the remaining {self.stats['remaining']} files")


def main():
    parser = argparse.ArgumentParser(description='Rewrite Hugo pages with Seeds Kids Worship content')
    
    # Input/output paths
    parser.add_argument('--content-dir', action='append', default=[],
                        help='Content directories to scan (can specify multiple)')
    parser.add_argument('--songs-json', default='./assets/seeds_songs.json',
                        help='Path to songs JSON file')
    parser.add_argument('--style-guide', default='./style/seeds_style_guide.txt',
                        help='Path to style guide file')
    
    # Processing options
    parser.add_argument('--top-k', type=int, default=5,
                        help='Number of songs to feature per page')
    parser.add_argument('--min-score', type=float, default=0.18,
                        help='Minimum similarity score to consider')
    parser.add_argument('--include', default='**/*.md',
                        help='Glob pattern for files to include')
    parser.add_argument('--exclude', default='**/_index.md',
                        help='Glob pattern for files to exclude')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of files to process (0 = all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate changes without writing files')
    
    # Pagination and resume options
    parser.add_argument('--batch-size', type=int, default=20,
                        help='Number of files to process per batch (default: 20)')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='Resume from previous run using saved state')
    parser.add_argument('--state-path', default='./tmp/rewrite_state.json',
                        help='Path to state file for resume functionality')
    parser.add_argument('--order', choices=['path', 'mtime'], default='path',
                        help='File ordering: path (alphabetical) or mtime (modification time)')
    
    # API options
    parser.add_argument('--model', default='claude-sonnet-4-20250514',
                        help='Anthropic model to use for rewriting')
    parser.add_argument('--temperature', type=float, default=0.6,
                        help='Generation temperature: lower = more focused, higher = more creative (default: 0.6)')
    parser.add_argument('--max-tokens', type=int, default=1400,
                        help='Maximum number of tokens in model output (default: 1400)')
    
    args = parser.parse_args()
    
    # Set default content dir if none specified
    if not args.content_dir:
        args.content_dir = ['./site/content/songs']
    
    # Check API key
    if not os.getenv('CLAUDE_API_KEY'):
        print("Error: CLAUDE_API_KEY environment variable not set")
        return
    
    # Run the rewriter
    rewriter = SeedsPageRewriter(args)
    rewriter.run()


if __name__ == '__main__':
    main()