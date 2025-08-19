#!/usr/bin/env python3
"""
Build internal links between content pages using TF-IDF similarity.
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import unicodedata
from collections import defaultdict, Counter

try:
    import yaml
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install pyyaml scikit-learn numpy", file=sys.stderr)
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
    
    # Remove HTML comments (like our block markers)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
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


def extract_scripture_tokens(scripture_text: str) -> set:
    """Extract normalized tokens from scripture references."""
    if not scripture_text:
        return set()
    
    # Extract book names, chapter/verse numbers
    tokens = set()
    
    # Common book abbreviations and full names
    books = re.findall(r'\b(?:psalm|psalms|matthew|mark|luke|john|romans|corinthians|ephesians|philippians|colossians|thessalonians|timothy|titus|hebrews|james|peter|jude|revelation|genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|samuel|kings|chronicles|ezra|nehemiah|esther|job|proverbs|ecclesiastes|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|acts|galatians)\b', scripture_text.lower())
    tokens.update(books)
    
    # Extract chapter:verse patterns
    verses = re.findall(r'\b\d+:\d+(?:-\d+)?\b', scripture_text)
    tokens.update(verses)
    
    return tokens


def build_query_text(front_matter: Dict, body: str) -> Tuple[str, str, set]:
    """Build query text components for TF-IDF."""
    title = front_matter.get('title', '')
    
    # Extract scripture references
    scripture = front_matter.get('scripture', '')
    scripture_tokens = extract_scripture_tokens(scripture)
    
    # Get first 200 words from body
    plain_text = markdown_to_text(body)
    words = plain_text.split()[:200]
    body_text = ' '.join(words) if words else ''
    
    # Combine components
    query_parts = []
    if title:
        query_parts.append(title)
    if scripture:
        query_parts.append(scripture)
    if body_text:
        query_parts.append(body_text)
    
    query_text = normalize_text(' '.join(query_parts))
    
    return query_text, title, scripture_tokens


def get_rare_title_tokens(titles: List[str], min_freq: int = 2) -> set:
    """Identify rare tokens across all titles."""
    all_tokens = []
    for title in titles:
        tokens = re.findall(r'\b\w+\b', normalize_text(title))
        all_tokens.extend(tokens)
    
    token_counts = Counter(all_tokens)
    rare_tokens = {token for token, count in token_counts.items() 
                   if count < min_freq and len(token) > 3}
    
    return rare_tokens


def calculate_adjusted_score(raw_score: float, source_page: Dict, target_page: Dict, 
                           rare_tokens: set) -> float:
    """Calculate adjusted similarity score with biases."""
    adjusted = raw_score
    
    # Same section bias (+0.05)
    if source_page.get('section') == target_page.get('section'):
        adjusted += 0.05
    
    # Scripture overlap bias (+0.08)
    source_scripture = source_page.get('scripture_tokens', set())
    target_scripture = target_page.get('scripture_tokens', set())
    if source_scripture and target_scripture and source_scripture.intersection(target_scripture):
        adjusted += 0.08
    
    # Rare title tokens bias (+0.03)
    source_title_tokens = set(re.findall(r'\b\w+\b', normalize_text(source_page.get('title', ''))))
    target_title_tokens = set(re.findall(r'\b\w+\b', normalize_text(target_page.get('title', ''))))
    
    if source_title_tokens.intersection(target_title_tokens).intersection(rare_tokens):
        adjusted += 0.03
    
    return min(adjusted, 1.0)


def create_related_block(links: List[Tuple[str, str]]) -> str:
    """Create a Related Content block."""
    if not links:
        return ""
    
    lines = ["<!-- related:start -->", "## Related Content"]
    
    for title, path in links:
        lines.append(f"- [{title}]({path})")
    
    lines.append("<!-- related:end -->")
    return '\n'.join(lines)


def update_related_block(content: str, new_block: str) -> Tuple[str, bool]:
    """Update or insert the related content block."""
    pattern = r'<!--\s*related:start\s*-->.*?<!--\s*related:end\s*-->'
    
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


def discover_pages(root_dir: Path, sections: List[str], include_pattern: str, 
                  exclude_pattern: str) -> List[Dict]:
    """Discover and parse content pages."""
    pages = []
    
    for section in sections:
        section_dir = root_dir / section
        if not section_dir.exists():
            continue
        
        # Find markdown files
        files = list(section_dir.glob(include_pattern))
        
        # Apply exclusions
        if exclude_pattern:
            exclude_files = set(section_dir.glob(exclude_pattern))
            files = [f for f in files if f not in exclude_files]
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                front_matter, body = extract_front_matter(content)
                if front_matter is None:
                    continue  # Skip files with invalid YAML
                
                query_text, title, scripture_tokens = build_query_text(front_matter, body)
                
                # Generate URL path
                rel_path = filepath.relative_to(root_dir)
                if rel_path.name == 'index.md':
                    url_path = '/' + '/'.join(rel_path.parts[:-1]) + '/'
                else:
                    url_path = '/' + str(rel_path.with_suffix('')) + '/'
                
                page = {
                    'filepath': filepath,
                    'section': section,
                    'title': title or filepath.stem.replace('-', ' ').title(),
                    'url_path': url_path,
                    'query_text': query_text,
                    'scripture_tokens': scripture_tokens,
                    'original_content': content
                }
                
                pages.append(page)
                
            except Exception as e:
                print(f"Warning: Failed to process {filepath}: {e}", file=sys.stderr)
                continue
    
    return pages


def build_internal_links(pages: List[Dict], max_links: int, min_score: float) -> List[Dict]:
    """Build internal links using TF-IDF similarity."""
    if len(pages) < 2:
        return []
    
    # Build TF-IDF vectors
    query_texts = [page['query_text'] for page in pages]
    
    try:
        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        vectors = vectorizer.fit_transform(query_texts)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(vectors)
        
        # Get rare tokens for bias calculation
        titles = [page['title'] for page in pages]
        rare_tokens = get_rare_title_tokens(titles)
        
        results = []
        
        for i, source_page in enumerate(pages):
            similarities = similarity_matrix[i]
            
            # Calculate adjusted scores and create candidate list
            candidates = []
            for j, target_page in enumerate(pages):
                if i == j:  # Skip self-links
                    continue
                
                raw_score = similarities[j]
                adjusted_score = calculate_adjusted_score(
                    raw_score, source_page, target_page, rare_tokens
                )
                
                if adjusted_score >= min_score:
                    candidates.append((j, adjusted_score, raw_score))
            
            # Sort by adjusted score and take top links
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = candidates[:max_links]
            
            # Build links for this page
            links = []
            for j, adjusted_score, raw_score in top_candidates:
                target_page = pages[j]
                links.append((target_page['title'], target_page['url_path']))
                
                # Log the relationship
                results.append({
                    'source': source_page['title'],
                    'source_path': source_page['url_path'],
                    'target': target_page['title'], 
                    'target_path': target_page['url_path'],
                    'raw_score': round(raw_score, 4),
                    'adjusted_score': round(adjusted_score, 4)
                })
            
            source_page['related_links'] = links
        
        return results
        
    except Exception as e:
        print(f"Error in TF-IDF processing: {e}", file=sys.stderr)
        return []


def process_pages(pages: List[Dict], dry_run: bool) -> Dict[str, int]:
    """Process pages to add/update related content blocks."""
    stats = {'processed': 0, 'updated': 0, 'errors': 0}
    
    for page in pages:
        try:
            stats['processed'] += 1
            
            links = page.get('related_links', [])
            if not links:
                continue
            
            # Create related block
            related_block = create_related_block(links)
            if not related_block:
                continue
            
            # Update content
            original_content = page['original_content']
            updated_content, modified = update_related_block(original_content, related_block)
            
            if modified:
                stats['updated'] += 1
                
                if not dry_run:
                    # Ensure trailing newline
                    if not updated_content.endswith('\n'):
                        updated_content += '\n'
                    
                    # Write updated content
                    with open(page['filepath'], 'w', encoding='utf-8', newline='') as f:
                        f.write(updated_content)
        
        except Exception as e:
            stats['errors'] += 1
            print(f"Error processing {page['filepath']}: {e}", file=sys.stderr)
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Build internal links between content pages')
    parser.add_argument('--root', default='./site/content', 
                       help='Root content directory (default: ./site/content)')
    parser.add_argument('--sections', default='songs,activities,bible-verses,guides',
                       help='Comma-separated list of sections to process')
    parser.add_argument('--max-links', type=int, default=5,
                       help='Maximum links per page (default: 5)')
    parser.add_argument('--min-score', type=float, default=0.18,
                       help='Minimum similarity score for links (default: 0.18)')
    parser.add_argument('--include', default='**/*.md',
                       help='Include pattern for files (default: **/*.md)')
    parser.add_argument('--exclude', default='**/_index.md',
                       help='Exclude pattern for files (default: **/_index.md)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--log', default='./tmp/internal_links.csv',
                       help='CSV log file path (default: ./tmp/internal_links.csv)')
    
    args = parser.parse_args()
    
    # Parse sections
    sections = [s.strip() for s in args.sections.split(',') if s.strip()]
    if not sections:
        print("Error: No sections specified", file=sys.stderr)
        return 1
    
    root_dir = Path(args.root)
    if not root_dir.exists():
        print(f"Error: Root directory {root_dir} does not exist", file=sys.stderr)
        return 1
    
    print(f"Discovering pages in sections: {', '.join(sections)}")
    
    # Discover pages
    pages = discover_pages(root_dir, sections, args.include, args.exclude)
    if not pages:
        print("Error: No pages found to process", file=sys.stderr)
        return 1
    
    print(f"Found {len(pages)} pages to process")
    
    # Build internal links
    print("Building TF-IDF similarity matrix...")
    link_results = build_internal_links(pages, args.max_links, args.min_score)
    
    print(f"Generated {len(link_results)} internal link relationships")
    
    # Create log directory
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV log
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['source', 'source_path', 'target', 'target_path', 'raw_score', 'adjusted_score']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(link_results)
    
    # Process pages to add links
    if args.dry_run:
        print("DRY RUN: Would update pages with related content blocks")
        # Count pages that would be updated
        pages_to_update = sum(1 for page in pages if page.get('related_links'))
        print(f"Would update {pages_to_update} pages with related links")
    else:
        print("Updating pages with related content blocks...")
        stats = process_pages(pages, dry_run=False)
        print(f"Processed: {stats['processed']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
    
    print(f"Link relationships logged to: {log_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())