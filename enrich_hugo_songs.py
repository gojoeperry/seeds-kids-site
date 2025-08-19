#!/usr/bin/env python3
"""
Enrich Hugo Markdown content with Seeds song metadata.
"""
import argparse
import csv
import json
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml
from rapidfuzz import fuzz
from slugify import slugify


class HugoSongEnricher:
    def __init__(self, songs_json_path: str, content_dir: str, dry_run: bool = False):
        self.songs_json_path = Path(songs_json_path)
        self.content_dir = Path(content_dir)
        self.dry_run = dry_run
        self.report_data = []
        
        # Load songs data
        self.songs = self._load_songs()
        
        # Discover existing markdown files
        self.markdown_files = self._discover_markdown_files()
        
    def _load_songs(self) -> List[Dict]:
        """Load songs from JSON file."""
        try:
            with open(self.songs_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading songs JSON: {e}")
            return []
    
    def _discover_markdown_files(self) -> List[Path]:
        """Discover all markdown files in content directory."""
        if not self.content_dir.exists():
            print(f"Content directory not found: {self.content_dir}")
            return []
        return list(self.content_dir.glob("*.md"))
    
    def _parse_front_matter(self, content: str) -> Tuple[Dict, str, str]:
        """
        Parse YAML front matter from markdown content.
        Returns: (front_matter_dict, body, original_newlines)
        """
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
    
    def _serialize_front_matter(self, front_matter: Dict) -> str:
        """Serialize front matter to YAML string."""
        if not front_matter:
            return ""
        
        # Use default_flow_style=False to avoid inline formatting
        yaml_str = yaml.dump(front_matter, 
                           default_flow_style=False, 
                           allow_unicode=True,
                           sort_keys=False)
        return f"---\n{yaml_str}---\n"
    
    def _find_matching_file(self, song: Dict) -> Tuple[Optional[Path], float, str]:
        """
        Find matching markdown file for song.
        Returns: (file_path, match_score, match_method)
        """
        slug = song['slug']
        title = song['title']
        
        # Try exact slug match first
        exact_path = self.content_dir / f"{slug}.md"
        if exact_path.exists():
            return exact_path, 100.0, "exact_slug"
        
        # Fuzzy match against filenames and front matter titles
        best_match = None
        best_score = 0
        best_method = ""
        
        for md_file in self.markdown_files:
            # Match against filename stem
            filename_stem = md_file.stem
            score = fuzz.ratio(title.lower(), filename_stem.lower())
            if score > best_score and score >= 85:
                best_match = md_file
                best_score = score
                best_method = "filename_fuzzy"
            
            # Match against front matter title
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                front_matter, _, _ = self._parse_front_matter(content)
                
                if 'title' in front_matter:
                    fm_title = str(front_matter['title'])
                    score = fuzz.ratio(title.lower(), fm_title.lower())
                    if score > best_score and score >= 85:
                        best_match = md_file
                        best_score = score
                        best_method = "title_fuzzy"
                        
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
                continue
        
        return best_match, best_score, best_method
    
    def _generate_meta_description(self, description: str) -> str:
        """Generate meta description from description, max 160 chars."""
        if not description:
            return ""
        
        # Truncate without breaking words
        if len(description) <= 160:
            return description
        
        truncated = description[:157]
        last_space = truncated.rfind(' ')
        if last_space > 120:  # Don't truncate too aggressively
            return truncated[:last_space] + "..."
        return truncated + "..."
    
    def _generate_resources_block(self, song: Dict) -> str:
        """Generate resources HTML block."""
        lines = ["<!-- resources:start -->", "<div class=\"resources\">"]
        
        if song.get('spotify_url'):
            lines.append(f'  <p><a href="{song["spotify_url"]}">Listen on Spotify</a></p>')
        
        if song.get('webpage_url'):
            lines.append(f'  <p><a href="{song["webpage_url"]}">Song page (Seeds Kids Worship)</a></p>')
        
        lines.extend([
            "  <p><small>Sing God's Word with your family.</small></p>",
            "</div>",
            "<!-- resources:end -->"
        ])
        
        return '\n'.join(lines)
    
    def _update_content_body(self, body: str, resources_block: str) -> str:
        """Update content body with resources block."""
        # Remove existing resources block
        pattern = r'<!-- resources:start -->.*?<!-- resources:end -->'
        body_cleaned = re.sub(pattern, '', body, flags=re.DOTALL)
        
        # Clean up extra whitespace
        body_cleaned = body_cleaned.rstrip()
        
        # Append new resources block
        if body_cleaned:
            return f"{body_cleaned}\n\n{resources_block}\n"
        else:
            return f"{resources_block}\n"
    
    def _update_front_matter(self, front_matter: Dict, song: Dict) -> Tuple[Dict, List[str]]:
        """Update front matter with song metadata."""
        updated_fm = front_matter.copy()
        missing_fields = []
        
        # Map song fields to front matter
        field_mapping = {
            'title': 'title',
            'slug': 'slug',
            'scripture': 'scripture',
            'album': 'album',
            'year': 'year',
            'description': 'description',
            'publication_date': 'publication_date',
            'duration': 'duration',
            'target_age': 'target_age',
            'style': 'style',
            'webpage_url': 'webpage_url',
            'spotify_url': 'spotify_url',
            'lyrics': 'lyrics'
        }
        
        for fm_key, song_key in field_mapping.items():
            value = song.get(song_key)
            if value is not None and value != "":
                updated_fm[fm_key] = value
            elif fm_key not in updated_fm or not updated_fm[fm_key]:
                missing_fields.append(fm_key)
        
        # Handle meta_description
        if 'meta_description' not in updated_fm or not updated_fm['meta_description']:
            meta_desc = self._generate_meta_description(song.get('description', ''))
            if meta_desc:
                updated_fm['meta_description'] = meta_desc
            else:
                missing_fields.append('meta_description')
        
        return updated_fm, missing_fields
    
    def _process_song(self, song: Dict) -> None:
        """Process a single song."""
        title = song.get('title', 'Unknown')
        slug = song.get('slug', 'unknown')
        
        # Find matching file
        file_path, match_score, match_method = self._find_matching_file(song)
        
        if not file_path:
            self.report_data.append({
                'file': 'N/A',
                'action': 'not_found',
                'match_score': 0,
                'final_title': title,
                'final_slug': slug,
                'missing_fields': 'N/A'
            })
            print(f"No matching file found for: {title}")
            return
        
        try:
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Parse front matter and body
            front_matter, body, original_newlines = self._parse_front_matter(original_content)
            
            if front_matter is None:
                self.report_data.append({
                    'file': file_path.name,
                    'action': 'skipped',
                    'match_score': match_score,
                    'final_title': title,
                    'final_slug': slug,
                    'missing_fields': 'malformed_yaml'
                })
                print(f"Skipping {file_path.name} due to malformed YAML")
                return
            
            # Update front matter
            updated_fm, missing_fields = self._update_front_matter(front_matter, song)
            
            # Generate resources block
            resources_block = self._generate_resources_block(song)
            
            # Update body
            updated_body = self._update_content_body(body, resources_block)
            
            # Serialize updated content
            fm_yaml = self._serialize_front_matter(updated_fm)
            new_content = f"{fm_yaml}{updated_body}"
            
            # Restore original line endings
            if original_newlines != '\n':
                new_content = new_content.replace('\n', original_newlines)
            
            # Ensure file ends with newline
            if not new_content.endswith(('\n', '\r\n', '\r')):
                new_content += original_newlines
            
            # Write file (unless dry run)
            if not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            # Log action
            self.report_data.append({
                'file': file_path.name,
                'action': 'touched',
                'match_score': match_score,
                'final_title': updated_fm.get('title', title),
                'final_slug': updated_fm.get('slug', slug),
                'missing_fields': ','.join(missing_fields) if missing_fields else 'none'
            })
            
            action_verb = "Would update" if self.dry_run else "Updated"
            print(f"{action_verb} {file_path.name} (match: {match_score:.1f}%, method: {match_method})")
            
        except Exception as e:
            self.report_data.append({
                'file': file_path.name,
                'action': 'skipped',
                'match_score': match_score,
                'final_title': title,
                'final_slug': slug,
                'missing_fields': f'error: {str(e)}'
            })
            print(f"Error processing {file_path.name}: {e}")
    
    def _save_report(self) -> None:
        """Save processing report to CSV."""
        report_path = Path('./tmp/enrich_report.csv')
        report_path.parent.mkdir(exist_ok=True)
        
        df = pd.DataFrame(self.report_data)
        df.to_csv(report_path, index=False)
        print(f"Report saved to: {report_path}")
    
    def enrich_all(self) -> None:
        """Process all songs and enrich markdown files."""
        if not self.songs:
            print("No songs data found.")
            return
        
        if not self.markdown_files:
            print(f"No markdown files found in {self.content_dir}")
            return
        
        print(f"Processing {len(self.songs)} songs...")
        print(f"Found {len(self.markdown_files)} markdown files...")
        
        if self.dry_run:
            print("DRY RUN MODE - No files will be modified")
        
        for song in self.songs:
            self._process_song(song)
        
        # Save report
        self._save_report()
        
        # Print summary
        actions = [item['action'] for item in self.report_data]
        touched_count = actions.count('touched')
        skipped_count = actions.count('skipped')
        not_found_count = actions.count('not_found')
        
        print(f"\nSummary:")
        print(f"Files scanned: {len(self.markdown_files)}")
        print(f"Songs matched: {touched_count}")
        print(f"Songs skipped: {skipped_count}")
        print(f"Songs not found: {not_found_count}")


def main():
    parser = argparse.ArgumentParser(description='Enrich Hugo Markdown with Seeds song metadata')
    parser.add_argument('--songs-json', default='./assets/seeds_songs.json',
                        help='Path to songs JSON file')
    parser.add_argument('--content-dir', default='./site/content/songs',
                        help='Path to Hugo content directory')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate changes without writing files')
    
    args = parser.parse_args()
    
    enricher = HugoSongEnricher(
        songs_json_path=args.songs_json,
        content_dir=args.content_dir,
        dry_run=args.dry_run
    )
    
    enricher.enrich_all()


if __name__ == '__main__':
    main()