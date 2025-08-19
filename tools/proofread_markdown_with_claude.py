#!/usr/bin/env python3
"""
Proofread Markdown files using the Anthropic API (Claude) while preserving structure.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import tempfile
import difflib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

try:
    import yaml
    import anthropic
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install anthropic pyyaml", file=sys.stderr)
    sys.exit(1)


PROTECTED_BLOCKS = [
    (r'<!-- featured-songs:start -->', r'<!-- featured-songs:end -->'),
    (r'<!-- related-seeds:start -->', r'<!-- related-seeds:end -->'),
    (r'<!-- resources:start -->', r'<!-- resources:end -->'),
    (r'<!-- related:start -->', r'<!-- related:end -->')
]


def resolve_api_key(api_key_arg: Optional[str], debug_auth: bool) -> str:
    """Resolve API key from arguments or environment."""
    key = None
    source = None
    
    if api_key_arg:
        key = api_key_arg
        source = "command line argument"
    elif os.getenv('CLAUDE_API_KEY'):
        key = os.getenv('CLAUDE_API_KEY')
        source = "CLAUDE_API_KEY environment variable"
    elif os.getenv('ANTHROPIC_API_KEY'):
        key = os.getenv('ANTHROPIC_API_KEY')
        source = "ANTHROPIC_API_KEY environment variable"
    
    if not key:
        raise ValueError("No API key found. Set CLAUDE_API_KEY or ANTHROPIC_API_KEY environment variable, or use --api-key")
    
    if debug_auth:
        masked_key = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
        print(f"Using API key from {source}: {masked_key}")
    
    return key


def extract_front_matter(content: str) -> Tuple[Optional[str], str]:
    """Extract YAML front matter and body."""
    if not content.startswith('---\n'):
        return None, content
    
    end_match = re.search(r'\n---\n', content[4:])
    if not end_match:
        return None, content
    
    yaml_section = content[:4 + end_match.end()]
    body = content[4 + end_match.end():]
    
    return yaml_section, body


def protect_blocks(content: str) -> Tuple[str, Dict[str, str]]:
    """Replace protected blocks with placeholders."""
    protected_content = content
    placeholders = {}
    
    for i, (start_pattern, end_pattern) in enumerate(PROTECTED_BLOCKS):
        pattern = f'{re.escape(start_pattern)}(.*?){re.escape(end_pattern)}'
        matches = re.finditer(pattern, protected_content, re.DOTALL)
        
        for j, match in enumerate(matches):
            placeholder = f"__PROTECTED_BLOCK_{i}_{j}__"
            placeholders[placeholder] = match.group(0)
            protected_content = protected_content.replace(match.group(0), placeholder, 1)
    
    return protected_content, placeholders


def restore_blocks(content: str, placeholders: Dict[str, str]) -> str:
    """Restore protected blocks from placeholders."""
    restored_content = content
    for placeholder, original_content in placeholders.items():
        restored_content = restored_content.replace(placeholder, original_content)
    
    return restored_content


def chunk_content(content: str, max_chars: int) -> List[str]:
    """Split content into chunks at paragraph boundaries."""
    if len(content) <= max_chars:
        return [content]
    
    chunks = []
    current_chunk = ""
    
    # Split by double newlines (paragraphs)
    paragraphs = content.split('\n\n')
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed limit
        if len(current_chunk) + len(paragraph) + 2 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = paragraph
            else:
                # Single paragraph is too long, split on whitespace
                words = paragraph.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 > max_chars:
                        if temp_chunk:
                            chunks.append(temp_chunk.rstrip())
                            temp_chunk = word
                        else:
                            # Single word too long, force split
                            chunks.append(word[:max_chars])
                            temp_chunk = word[max_chars:]
                    else:
                        temp_chunk += (" " if temp_chunk else "") + word
                if temp_chunk:
                    current_chunk = temp_chunk
        else:
            current_chunk += ("\n\n" if current_chunk else "") + paragraph
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    return chunks


def proofread_chunk(client: anthropic.Anthropic, chunk: str, model: str, 
                   temperature: float, max_tokens: int) -> Optional[str]:
    """Proofread a single chunk using Claude."""
    system_prompt = ("You are a meticulous copy editor. Fix spelling, grammar, punctuation, and minor formatting issues in Markdown. "
                    "Preserve meaning, tone, structure, headings, links, and references. "
                    "Do not add or remove sections. Do not invent facts or change Scripture references. "
                    "Keep Markdown syntax valid. No emojis.")
    
    user_prompt = f"""You will receive a Markdown excerpt from a larger page. 
Constraints:
- Output only the corrected Markdown for this excerpt.
- Do not change YAML front matter (it is not included here).
- Maintain headings, lists, links, code fences, and inline formatting.
- Keep URLs unchanged.
- Preserve Scripture references exactly (spelling and punctuation fixes allowed, but do not change the reference itself).
- Keep line breaks logically intact (paragraphs stay paragraphs).
- Avoid altering templating shortcodes if present.

EXCERPT START
{chunk}
EXCERPT END"""
    
    for attempt in range(5):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            return response.content[0].text.strip()
            
        except anthropic.AuthenticationError as e:
            print(f"Authentication error: {e}", file=sys.stderr)
            return None
        except anthropic.RateLimitError as e:
            if attempt < 4:
                wait_time = 5 * (attempt + 1)
                print(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/5")
                time.sleep(wait_time)
                continue
            print(f"Rate limit exceeded after 5 attempts: {e}", file=sys.stderr)
            return None
        except Exception as e:
            if attempt < 4:
                wait_time = 5 * (attempt + 1)
                print(f"API error (attempt {attempt + 1}/5): {e}")
                time.sleep(wait_time)
                continue
            print(f"API error after 5 attempts: {e}", file=sys.stderr)
            return None
    
    return None


def load_state(state_path: Path) -> Dict:
    """Load processing state from file."""
    if not state_path.exists():
        return {"completed": []}
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"completed": []}


def save_state(state_path: Path, state: Dict):
    """Atomically save processing state to file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                    dir=state_path.parent, delete=False) as f:
        json.dump(state, f, indent=2)
        temp_path = Path(f.name)
    
    temp_path.replace(state_path)


def discover_files(content_dirs: List[str], include: str, exclude: str, 
                  order: str, limit: int) -> List[Path]:
    """Discover markdown files from content directories."""
    all_files = []
    
    for content_dir in content_dirs:
        content_path = Path(content_dir)
        if not content_path.exists():
            print(f"Warning: Content directory {content_dir} does not exist")
            continue
        
        files = list(content_path.glob(include))
        
        # Apply exclusions
        if exclude:
            exclude_files = set(content_path.glob(exclude))
            files = [f for f in files if f not in exclude_files]
        
        all_files.extend(files)
    
    # Sort files
    if order == 'mtime':
        all_files.sort(key=lambda f: f.stat().st_mtime)
    else:
        all_files.sort(key=lambda f: str(f).lower())
    
    # Apply limit
    if limit > 0:
        all_files = all_files[:limit]
    
    return all_files


def show_preview(original: str, updated: str, filepath: Path):
    """Show unified diff preview."""
    original_lines = original.splitlines(keepends=True)
    updated_lines = updated.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        original_lines[:120], updated_lines[:120],
        fromfile=f"a/{filepath.name}", tofile=f"b/{filepath.name}",
        lineterm=""
    ))
    
    if diff:
        print(f"\n--- Preview changes for {filepath} ---")
        for line in diff[:50]:  # Limit diff output
            print(line.rstrip())
        if len(diff) > 50:
            print("... (diff truncated)")


def process_file(filepath: Path, client: anthropic.Anthropic, args, 
                project_root: Path) -> Dict[str, Any]:
    """Process a single markdown file."""
    rel_path = filepath.resolve().relative_to(project_root).as_posix()
    
    result = {
        'relpath': rel_path,
        'action': 'skipped_no_changes',
        'chunks': 0,
        'changes_chars': 0,
        'notes': ''
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Extract front matter
        yaml_section, body = extract_front_matter(original_content)
        
        if yaml_section:
            # Validate YAML
            try:
                yaml_content = yaml_section[4:-5]  # Remove --- fences
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                result['action'] = 'yaml_error'
                result['notes'] = str(e)[:160]
                return result
        
        if not body.strip():
            return result
        
        # Protect blocks if enabled
        protected_body = body
        placeholders = {}
        if args.protect_blocks:
            protected_body, placeholders = protect_blocks(body)
        
        # Chunk content
        chunks = chunk_content(protected_body, args.chunk_chars)
        result['chunks'] = len(chunks)
        
        # Process chunks
        corrected_chunks = []
        api_errors = 0
        
        for chunk in chunks:
            if not chunk.strip():
                corrected_chunks.append(chunk)
                continue
            
            corrected_chunk = proofread_chunk(
                client, chunk, args.model, args.temperature, args.max_tokens
            )
            
            if corrected_chunk is None:
                corrected_chunks.append(chunk)
                api_errors += 1
            else:
                corrected_chunks.append(corrected_chunk)
        
        # Reassemble
        new_body = '\n\n'.join(corrected_chunks)
        
        # Restore protected blocks
        if placeholders:
            new_body = restore_blocks(new_body, placeholders)
        
        # Check for changes
        if new_body != body:
            result['action'] = 'updated'
            result['changes_chars'] = abs(len(new_body) - len(body))
            
            if args.preview_n > 0:
                show_preview(body, new_body, filepath)
            
            if not args.dry_run:
                # Write updated content
                new_content = (yaml_section if yaml_section else '') + new_body
                if not new_content.endswith('\n'):
                    new_content += '\n'
                
                with open(filepath, 'w', encoding='utf-8', newline='') as f:
                    f.write(new_content)
        
        if api_errors > 0:
            if result['action'] == 'skipped_no_changes':
                result['action'] = 'api_error'
            result['notes'] = f'api_fallback_{api_errors}_chunks'
        
    except Exception as e:
        result['action'] = 'api_error'
        result['notes'] = str(e)[:160]
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Proofread Markdown files with Claude API')
    parser.add_argument('--content-dir', action='append', required=True,
                       help='Content directory to scan (repeatable)')
    parser.add_argument('--include', default='**/*.md',
                       help='Include pattern for files')
    parser.add_argument('--exclude', default='**/_index.md',
                       help='Exclude pattern for files')
    parser.add_argument('--protect-blocks', action='store_true', default=True,
                       help='Protect auto-generated blocks from edits')
    parser.add_argument('--model', default='claude-sonnet-4-20250514',
                       help='Claude model to use')
    parser.add_argument('--temperature', type=float, default=0.2,
                       help='Temperature for API calls')
    parser.add_argument('--max-tokens', type=int, default=1200,
                       help='Maximum tokens per API call')
    parser.add_argument('--chunk-chars', type=int, default=8000,
                       help='Maximum characters per chunk')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Batch size for processing')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous run')
    parser.add_argument('--state-path', default='./tmp/proofread_state.json',
                       help='Path to state file for resume')
    parser.add_argument('--order', choices=['path', 'mtime'], default='path',
                       help='File processing order')
    parser.add_argument('--limit', type=int, default=0,
                       help='Limit number of files (0 = all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without writing')
    parser.add_argument('--preview-n', type=int, default=3,
                       help='Show diffs for first N changed files')
    parser.add_argument('--report', default='./tmp/proofread_report.csv',
                       help='CSV report file path')
    parser.add_argument('--api-key', help='Anthropic API key')
    parser.add_argument('--debug-auth', action='store_true',
                       help='Show API key source and preview')
    
    args = parser.parse_args()
    
    # Resolve API key
    try:
        api_key = resolve_api_key(args.api_key, args.debug_auth)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Initialize client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Discover files
    files = discover_files(args.content_dir, args.include, args.exclude, 
                          args.order, args.limit)
    
    if not files:
        print("No files found to process")
        return 0
    
    # Load state for resume
    state_path = Path(args.state_path)
    state = {"completed": []}
    if args.resume:
        state = load_state(state_path)
    
    project_root = Path.cwd()
    completed_set = set(state["completed"])
    
    # Filter out completed files
    files_to_process = []
    for filepath in files:
        rel_path = filepath.resolve().relative_to(project_root).as_posix()
        if rel_path not in completed_set:
            files_to_process.append(filepath)
    
    print(f"Found {len(files)} total files, {len(files_to_process)} to process")
    
    if args.dry_run:
        print("DRY RUN MODE: No files will be modified")
    
    # Prepare report
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Statistics
    stats = {
        'seen': 0,
        'updated': 0,
        'skipped_no_changes': 0,
        'yaml_error': 0,
        'api_error': 0
    }
    
    previews_shown = 0
    
    # Process files in batches
    with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['relpath', 'action', 'chunks', 'changes_chars', 'notes'])
        
        for i, filepath in enumerate(files_to_process):
            print(f"Processing {i+1}/{len(files_to_process)}: {filepath.name}")
            
            # Show preview for first N files
            original_preview_n = args.preview_n
            if previews_shown >= args.preview_n:
                args.preview_n = 0
            
            result = process_file(filepath, client, args, project_root)
            stats['seen'] += 1
            stats[result['action']] = stats.get(result['action'], 0) + 1
            
            if result['action'] == 'updated' and previews_shown < original_preview_n:
                previews_shown += 1
            
            # Restore preview setting
            args.preview_n = original_preview_n
            
            # Write to report
            writer.writerow([
                result['relpath'],
                result['action'],
                result['chunks'],
                result['changes_chars'],
                result['notes']
            ])
            csvfile.flush()
            
            # Update state
            state["completed"].append(result['relpath'])
            save_state(state_path, state)
            
            # Batch delay
            if (i + 1) % args.batch_size == 0 and i < len(files_to_process) - 1:
                print(f"Completed batch {(i + 1) // args.batch_size}, pausing 2s...")
                time.sleep(2)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Files processed: {stats['seen']}")
    print(f"  Updated: {stats['updated']}")
    print(f"  No changes: {stats['skipped_no_changes']}")
    print(f"  YAML errors: {stats['yaml_error']}")
    print(f"  API errors: {stats['api_error']}")
    print(f"  Report written to: {report_path}")
    
    if args.dry_run:
        print("  (DRY RUN - no files were modified)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())