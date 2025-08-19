#!/usr/bin/env python3
"""
Audit and optionally enrich Hugo Markdown pages to ensure they are Seeds-focused and SEO-ready.
"""

import argparse
import json
import re
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import unicodedata
from collections import defaultdict

try:
    import yaml
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from slugify import slugify
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install pyyaml pandas scikit-learn python-slugify", file=sys.stderr)
    sys.exit(1)


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    # Unicode normalization and basic cleaning
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', text.lower().strip())


def markdown_to_text(markdown: str) -> str:
    """Convert markdown to plain text (simple approach)."""
    if not markdown:
        return ""
    
    # Remove code blocks
    text = re.sub(r'```.*?```', '', markdown, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove headers markers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove other markdown syntax
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # italic
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # lists
    
    return re.sub(r'\s+', ' ', text).strip()


def extract_front_matter(content: str) -> Tuple[Optional[Dict], str]:
    """Extract YAML front matter and body from markdown content."""
    if not content.startswith('---\n'):
        return None, content
    
    try:
        # Find closing fence
        end_match = re.search(r'\n---\n', content[4:])
        if not end_match:
            return None, content
        
        yaml_content = content[4:4 + end_match.start()]
        body = content[4 + end_match.end():]
        
        front_matter = yaml.safe_load(yaml_content) or {}
        return front_matter, body
    except yaml.YAMLError:
        return None, content


def build_query_text(title: str, front_matter: Dict, body: str) -> str:
    """Build normalized query text for similarity matching."""
    parts = []
    
    if title:
        parts.append(title)
    
    # Add description fields
    for key in ['description', 'meta_description', 'summary']:
        if front_matter.get(key):
            parts.append(str(front_matter[key]))
    
    # Extract headers and first ~200 words from body
    plain_text = markdown_to_text(body)
    words = plain_text.split()[:200]
    if words:
        parts.append(' '.join(words))
    
    return normalize_text(' '.join(parts))


def adjust_similarity_score(score: float, page_text: str, song: Dict) -> float:
    """Adjust similarity score based on contextual factors."""
    adjusted = score
    page_lower = page_text.lower()
    
    # Scripture reference bonus
    if song.get('scripture'):
        scripture_tokens = re.findall(r'\b\w+\b', normalize_text(song['scripture']))
        for token in scripture_tokens:
            if len(token) > 2 and token in page_lower:
                adjusted += 0.05
                break
    
    # Seasonal bonus
    seasonal_patterns = r'\b(christmas|easter|vbs|vacation\s+bible\s+school)\b'
    if re.search(seasonal_patterns, page_lower):
        adjusted += 0.04
    
    # Age group bonus
    age_patterns = r'\b(toddler|preschool|kids|family|children)\b'
    if re.search(age_patterns, page_lower):
        adjusted += 0.03
    
    return min(adjusted, 1.0)


def create_featured_block(songs: List[Dict]) -> str:
    """Create a Featured Songs block."""
    if not songs:
        return ""
    
    lines = ["<!-- featured-songs:start -->", "## Featured Songs"]
    
    for song in songs:
        if not song.get('webpage_url'):
            continue
        
        title = song.get('title', 'Untitled')
        url = song['webpage_url']
        description = song.get('description', '')
        
        # Truncate description to ~120 chars at word boundary
        if len(description) > 120:
            truncated = description[:120]
            last_space = truncated.rfind(' ')
            if last_space > 80:
                description = truncated[:last_space] + '...'
            else:
                description = truncated + '...'
        
        blurb = f" — {description}" if description else ""
        lines.append(f"- [{title}]({url}){blurb}")
    
    lines.append("<!-- featured-songs:end -->")
    return '\n'.join(lines)


def create_related_block(songs: List[Dict]) -> str:
    """Create a Related Seeds Songs block."""
    if not songs:
        return ""
    
    lines = ["<!-- related-seeds:start -->", "## Related Seeds Songs"]
    
    for song in songs:
        if not song.get('webpage_url'):
            continue
        
        title = song.get('title', 'Untitled')
        url = song['webpage_url']
        lines.append(f"- [{title}]({url})")
    
    lines.append("<!-- related-seeds:end -->")
    return '\n'.join(lines)


def create_resources_block(songs: List[Dict]) -> str:
    """Create a Resources block."""
    lines = ["<!-- resources:start -->", '<div class="resources">']
    
    # Find first Spotify URL
    spotify_url = None
    for song in songs:
        if song.get('spotify_url'):
            spotify_url = song['spotify_url']
            break
    
    if spotify_url:
        lines.append(f'<p><a href="{spotify_url}">Listen on Spotify</a></p>')
    
    lines.extend([
        '<p><small>Sing God\'s Word with your family.</small></p>',
        '</div>',
        '<!-- resources:end -->'
    ])
    
    return '\n'.join(lines)


def update_block_in_content(content: str, new_block: str, start_marker: str, end_marker: str) -> Tuple[str, bool]:
    """Update or insert a delimited block in content."""
    pattern = f'<!--\\s*{re.escape(start_marker[4:-4])}\\s*-->.*?<!--\\s*{re.escape(end_marker[4:-4])}\\s*-->'
    
    if re.search(pattern, content, re.DOTALL):
        # Replace existing block
        updated_content = re.sub(pattern, new_block, content, flags=re.DOTALL)
        return updated_content, True
    else:
        # Append new block
        if not content.endswith('\n'):
            content += '\n'
        content += '\n' + new_block + '\n'
        return content, True


def process_file(filepath: Path, songs_data: List[Dict], vectorizer, song_vectors,
                 args) -> Dict[str, Any]:
    """Process a single markdown file."""
    try:
        relpath = str(filepath.relative_to(Path.cwd()))
    except ValueError:
        # Handle case where file is not in current working directory
        relpath = str(filepath)
    
    result = {
        'relpath': relpath,
        'section': filepath.parts[-2] if len(filepath.parts) > 1 else '',
        'title': '',
        'slug': '',
        'issues': [],
        'actions': [],
        'meta_ok': True,
        'featured_ok': True,
        'related_ok': True,
        'resources_ok': True,
        'selected_songs': [],
        'selected_scores': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        original_content = content
        
        # Parse front matter
        front_matter, body = extract_front_matter(content)
        
        if front_matter is None:
            result['issues'].append('yaml_invalid')
            result['meta_ok'] = False
            return result
        
        # Get/fix title
        title = front_matter.get('title', '')
        if not title:
            # Derive from filename
            title = filepath.stem.replace('-', ' ').title()
            if args.fix_meta:
                front_matter['title'] = title
                result['actions'].append('added_title')
        
        result['title'] = title
        result['slug'] = front_matter.get('slug', filepath.stem)
        
        # Check slug vs filename
        if front_matter.get('slug') and front_matter['slug'] != filepath.stem:
            result['issues'].append('slug_filename_mismatch')
        
        # Fix metadata
        if args.fix_meta:
            # Meta description
            meta_desc = front_matter.get('meta_description', '')
            if not meta_desc or len(meta_desc) > 160:
                # Generate from first paragraph
                paragraphs = body.split('\n\n')
                first_para = markdown_to_text(paragraphs[0]) if paragraphs else ''
                if first_para:
                    if len(first_para) > 160:
                        truncated = first_para[:160]
                        last_space = truncated.rfind(' ')
                        if last_space > 100:
                            meta_desc = truncated[:last_space]
                        else:
                            meta_desc = truncated
                    else:
                        meta_desc = first_para
                    front_matter['meta_description'] = meta_desc
                    result['actions'].append('fixed_meta_description')
            
            # Tags
            tags = front_matter.get('tags', [])
            if not isinstance(tags, list):
                tags = []
            
            if 'seeds-kids-worship' not in tags:
                tags.append('seeds-kids-worship')
                result['actions'].append('added_seeds_tag')
            
            # Add section tag if appropriate
            section_tag = result['section']
            if section_tag in ['guides', 'songs', 'activities', 'bible-verses'] and section_tag not in tags:
                tags.append(section_tag)
                result['actions'].append(f'added_{section_tag}_tag')
            
            front_matter['tags'] = tags
        
        # Build query text and find related songs
        query_text = build_query_text(title, front_matter, body)
        
        if query_text and song_vectors is not None:
            try:
                query_vector = vectorizer.transform([query_text])
                similarities = cosine_similarity(query_vector, song_vectors)[0]
                
                # Adjust scores and select top songs
                adjusted_scores = []
                for i, score in enumerate(similarities):
                    adjusted = adjust_similarity_score(score, query_text, songs_data[i])
                    adjusted_scores.append((adjusted, i))
                
                # Sort by adjusted score and take top-k above threshold
                adjusted_scores.sort(reverse=True)
                selected = []
                for score, idx in adjusted_scores[:args.top_k_related]:
                    if score >= args.min_score:
                        selected.append((songs_data[idx], score))
                
                result['selected_songs'] = [song['title'] for song, _ in selected]
                result['selected_scores'] = [round(score, 3) for _, score in selected]
                selected_songs = [song for song, _ in selected]
                
            except Exception as e:
                if not args.quiet:
                    print(f"Warning: TF-IDF failed for {filepath}: {e}", file=sys.stderr)
                selected_songs = []
        else:
            selected_songs = []
        
        # Update blocks
        content_modified = False
        
        # Featured Songs block
        if args.fix_featured and selected_songs:
            featured_block = create_featured_block(selected_songs[:3])  # Top 3 for featured
            if featured_block:
                content, modified = update_block_in_content(
                    content, featured_block, 
                    '<!-- featured-songs:start -->', '<!-- featured-songs:end -->'
                )
                if modified:
                    content_modified = True
                    result['actions'].append('updated_featured')
        
        # Related Seeds Songs block
        if args.add_related and selected_songs:
            related_block = create_related_block(selected_songs)
            if related_block:
                content, modified = update_block_in_content(
                    content, related_block,
                    '<!-- related-seeds:start -->', '<!-- related-seeds:end -->'
                )
                if modified:
                    content_modified = True
                    result['actions'].append('updated_related')
        
        # Resources block
        if args.fix_resources and selected_songs:
            resources_block = create_resources_block(selected_songs)
            if resources_block:
                content, modified = update_block_in_content(
                    content, resources_block,
                    '<!-- resources:start -->', '<!-- resources:end -->'
                )
                if modified:
                    content_modified = True
                    result['actions'].append('updated_resources')
        
        # Rebuild content with updated front matter
        if args.fix_meta or content_modified:
            yaml_content = yaml.dump(front_matter, default_flow_style=False, allow_unicode=True)
            # Remove trailing newlines/whitespace from YAML
            yaml_content = yaml_content.rstrip()
            
            new_content = f"---\n{yaml_content}\n---\n{body}"
            
            # Apply block updates to new content
            if content_modified:
                # Re-apply block updates to the reconstructed content
                if args.fix_featured and selected_songs:
                    featured_block = create_featured_block(selected_songs[:3])
                    if featured_block:
                        new_content, _ = update_block_in_content(
                            new_content, featured_block,
                            '<!-- featured-songs:start -->', '<!-- featured-songs:end -->'
                        )
                
                if args.add_related and selected_songs:
                    related_block = create_related_block(selected_songs)
                    if related_block:
                        new_content, _ = update_block_in_content(
                            new_content, related_block,
                            '<!-- related-seeds:start -->', '<!-- related-seeds:end -->'
                        )
                
                if args.fix_resources and selected_songs:
                    resources_block = create_resources_block(selected_songs)
                    if resources_block:
                        new_content, _ = update_block_in_content(
                            new_content, resources_block,
                            '<!-- resources:start -->', '<!-- resources:end -->'
                        )
            
            content = new_content
        
        # Write changes if not dry run
        if not args.dry_run and content != original_content:
            # Ensure content ends with newline
            if not content.endswith('\n'):
                content += '\n'
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
    except Exception as e:
        result['issues'].append(f'processing_error: {str(e)[:160]}')
        result['meta_ok'] = False
        result['featured_ok'] = False
        result['related_ok'] = False
        result['resources_ok'] = False
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Audit and enrich Hugo Markdown pages for Seeds content')
    parser.add_argument('--content-dir', action='append', default=None,
                       help='Content directory to scan (repeatable, default: guides/songs/activities/bible-verses)')
    parser.add_argument('--songs-json', default='./assets/seeds_songs.json',
                       help='Path to seeds songs JSON file')
    parser.add_argument('--report', default='./tmp/audit_enrich_report.csv',
                       help='Output CSV report path')
    parser.add_argument('--include', default='**/*.md',
                       help='Include pattern for files')
    parser.add_argument('--exclude', default='**/_index.md',
                       help='Exclude pattern for files')
    parser.add_argument('--top-k-related', type=int, default=4,
                       help='Maximum number of related songs to select')
    parser.add_argument('--min-score', type=float, default=0.18,
                       help='Minimum similarity score for related songs')
    parser.add_argument('--fix-meta', action='store_true',
                       help='Fix metadata issues')
    parser.add_argument('--fix-featured', action='store_true',
                       help='Ensure Featured Songs block exists/refresh')
    parser.add_argument('--add-related', action='store_true',
                       help='Insert/update Related Seeds Songs block')
    parser.add_argument('--fix-resources', action='store_true',
                       help='Ensure Resources block exists')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit number of files to process (0 = all)')
    parser.add_argument('--order', choices=['path', 'mtime'], default='path',
                       help='Order files by path or modification time')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress non-essential output')
    
    args = parser.parse_args()
    
    # Set default content directories
    if args.content_dir is None:
        args.content_dir = ['./content/songs', './content/activities']
    
    # Load songs data
    try:
        with open(args.songs_json, 'r', encoding='utf-8') as f:
            songs_data = json.load(f)
        if not args.quiet:
            print(f"Loaded {len(songs_data)} songs from {args.songs_json}")
    except Exception as e:
        print(f"Error loading songs data: {e}", file=sys.stderr)
        return 1
    
    # Prepare TF-IDF if we need related songs
    vectorizer = None
    song_vectors = None
    
    if args.add_related or args.fix_featured or args.fix_resources:
        try:
            # Build song corpus
            song_texts = []
            for song in songs_data:
                parts = [
                    song.get('title', ''),
                    song.get('scripture', ''),
                    song.get('album', ''),
                    song.get('description', ''),
                    song.get('target_age', ''),
                    song.get('style', '')
                ]
                song_text = normalize_text(' '.join(str(p) for p in parts if p))
                song_texts.append(song_text)
            
            if song_texts:
                vectorizer = TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 2),
                    stop_words='english'
                )
                song_vectors = vectorizer.fit_transform(song_texts)
                if not args.quiet:
                    print(f"Built TF-IDF index for {len(song_texts)} songs")
        except Exception as e:
            if not args.quiet:
                print(f"Warning: TF-IDF setup failed: {e}", file=sys.stderr)
    
    # Discover files
    all_files = []
    for content_dir in args.content_dir:
        content_path = Path(content_dir)
        if not content_path.exists():
            if not args.quiet:
                print(f"Warning: Content directory {content_dir} does not exist")
            continue
        
        files = list(content_path.glob(args.include))
        
        # Apply exclusions
        if args.exclude:
            exclude_files = set(content_path.glob(args.exclude))
            files = [f for f in files if f not in exclude_files]
        
        all_files.extend(files)
    
    # Sort files
    if args.order == 'mtime':
        all_files.sort(key=lambda f: f.stat().st_mtime)
    else:
        all_files.sort()
    
    # Apply limit
    if args.limit > 0:
        all_files = all_files[:args.limit]
    
    if not args.quiet:
        print(f"Processing {len(all_files)} files...")
    
    # Process files
    results = []
    stats = defaultdict(int)
    
    for filepath in all_files:
        result = process_file(filepath, songs_data, vectorizer, song_vectors, args)
        results.append(result)
        
        # Update stats
        stats['files_scanned'] += 1
        if 'yaml_invalid' in result['issues']:
            stats['yaml_invalid'] += 1
        if any('added_' in action or 'fixed_' in action for action in result['actions']):
            stats['fixed_meta'] += 1
        if 'updated_featured' in result['actions']:
            stats['updated_featured'] += 1
        if 'updated_related' in result['actions']:
            stats['updated_related'] += 1
        if 'updated_resources' in result['actions']:
            stats['updated_resources'] += 1
    
    # Ensure report directory exists
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV report
    with open(args.report, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['relpath', 'section', 'title', 'slug', 'issues', 'actions', 
                     'meta_ok', 'featured_ok', 'related_ok', 'resources_ok',
                     'selected_songs', 'selected_scores']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Format lists as pipe-separated strings
            result['issues'] = '|'.join(result['issues'])
            result['actions'] = '|'.join(result['actions'])
            result['selected_songs'] = '|'.join(result['selected_songs'])
            result['selected_scores'] = '|'.join(map(str, result['selected_scores']))
            writer.writerow(result)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Files scanned: {stats['files_scanned']}")
    print(f"  YAML invalid: {stats['yaml_invalid']}")
    print(f"  Fixed metadata: {stats['fixed_meta']}")
    print(f"  Updated featured blocks: {stats['updated_featured']}")
    print(f"  Updated related blocks: {stats['updated_related']}")
    print(f"  Updated resources blocks: {stats['updated_resources']}")
    print(f"  Report written to: {args.report}")
    
    if args.dry_run:
        print("  (DRY RUN - no files were modified)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())