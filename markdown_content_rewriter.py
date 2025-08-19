#!/usr/bin/env python3
"""
Seeds Kids Worship - Markdown Content Rewriter
Rewrites all 1200+ markdown files using Claude 3.5 Sonnet via Anthropic API
"""

import os
import re
import time
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import json

# === Configuration ===
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
MODEL = "claude-3-5-sonnet-20241022"
STYLE_GUIDE_PATH = "seeds_style_guide.txt"
CONTENT_DIR = "content"
BATCH_SIZE = 10  # Process in batches to manage API limits
TEST_MODE = True  # Set to True to process only first 10 files for review
TEST_LIMIT = 10  # Number of files to process in test mode
DELAY_BETWEEN_REQUESTS = 1.5  # Seconds to avoid rate limiting
RESUME_FILE = "rewrite_progress.json"

# === Load Style Guide ===
try:
    with open(STYLE_GUIDE_PATH, "r", encoding="utf-8") as f:
        STYLE_GUIDE = f.read()
    print(f"[SUCCESS] Loaded style guide from {STYLE_GUIDE_PATH}")
except FileNotFoundError:
    print(f"[ERROR] Style guide not found at {STYLE_GUIDE_PATH}")
    exit(1)

def extract_frontmatter_and_content(markdown_content):
    """Extract YAML frontmatter and body content from markdown file"""
    if markdown_content.startswith('---'):
        parts = markdown_content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].strip()
            return frontmatter, body
    return "", markdown_content.strip()

def reconstruct_markdown(frontmatter, new_body):
    """Reconstruct markdown file with original frontmatter and new body"""
    if frontmatter:
        return f"---\n{frontmatter}\n---\n\n{new_body}"
    return new_body

def load_progress():
    """Load progress from resume file"""
    if os.path.exists(RESUME_FILE):
        try:
            with open(RESUME_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"completed": [], "failed": [], "last_batch": 0}

def save_progress(progress):
    """Save progress to resume file"""
    with open(RESUME_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def rewrite_content(title, current_body, file_path):
    """Rewrite article content using Claude API"""
    prompt = f"""
You are a Christian copywriter for Seeds Kids Worship. Rewrite the following blog article with these goals:

- Make it biblically grounded and family-friendly
- Use clear, structured SEO content with H2s, H3s, and bullet points  
- Include Scripture references where relevant
- Add practical family worship ideas
- Include a call to action for families and churches
- Match the Seeds Kids Worship brand voice and style
- Aim for 800-1200 words for comprehensive coverage
- Use engaging, parent-focused language

STYLE GUIDE:
{STYLE_GUIDE}

CURRENT ARTICLE:
Title: {title}
File: {file_path}
Content:
{current_body}

Please provide the complete rewritten article body (without frontmatter):
"""
    
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            temperature=0.7,
            system="You are a blog writer creating polished, SEO-optimized content for Christian families. Focus on practical application and biblical truth.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[ERROR] API call failed for {file_path}: {e}")
        return None

def get_all_markdown_files():
    """Get all markdown files in content directory"""
    markdown_files = []
    content_path = Path(CONTENT_DIR)
    
    if not content_path.exists():
        print(f"Content directory '{CONTENT_DIR}' not found")
        return []
    
    # Find all .md files recursively
    for md_file in content_path.rglob("*.md"):
        markdown_files.append(md_file)
    
    return sorted(markdown_files)

def process_batch(files_batch, progress, batch_num):
    """Process a batch of markdown files"""
    print(f"\n=== Processing Batch {batch_num} ({len(files_batch)} files) ===")
    
    for file_path in tqdm(files_batch, desc=f"Batch {batch_num}"):
        file_str = str(file_path)
        
        # Skip if already completed
        if file_str in progress["completed"]:
            continue
            
        try:
            # Read current file
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Extract frontmatter and body
            frontmatter, body = extract_frontmatter_and_content(current_content)
            
            # Extract title from frontmatter or filename
            title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
            title = title_match.group(1).strip() if title_match else file_path.stem.replace('-', ' ').title()
            
            # Skip if body is too short (likely template/placeholder)
            if len(body.strip()) < 50:
                print(f"[SKIP] {file_str} - Content too short")
                progress["completed"].append(file_str)
                continue
            
            # Rewrite content
            print(f"[REWRITE] {title}")
            new_body = rewrite_content(title, body, file_str)
            
            if new_body:
                # Reconstruct and save file
                new_content = reconstruct_markdown(frontmatter, new_body)
                
                # Backup original file
                backup_path = file_path.with_suffix('.md.backup')
                if not backup_path.exists():
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(current_content)
                
                # Write new content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                progress["completed"].append(file_str)
                print(f"[SUCCESS] {file_str}")
            else:
                progress["failed"].append(file_str)
                print(f"[FAILED] {file_str}")
                
        except Exception as e:
            progress["failed"].append(file_str)
            print(f"[ERROR] {file_str}: {e}")
        
        # Save progress after each file
        save_progress(progress)
        
        # Rate limiting delay
        time.sleep(DELAY_BETWEEN_REQUESTS)

def main():
    """Main processing function"""
    print("Seeds Kids Worship - Markdown Content Rewriter")
    print("=" * 60)
    
    # Get all markdown files
    markdown_files = get_all_markdown_files()
    if not markdown_files:
        print("[ERROR] No markdown files found")
        return
    
    print(f"Found {len(markdown_files)} markdown files")
    
    # Load progress
    progress = load_progress()
    completed_count = len(progress["completed"])
    failed_count = len(progress["failed"])
    
    if completed_count > 0:
        print(f"Resume mode: {completed_count} completed, {failed_count} failed")
    
    # Calculate remaining files
    remaining_files = [f for f in markdown_files if str(f) not in progress["completed"]]
    
    # Apply test mode limit if enabled
    if TEST_MODE and len(remaining_files) > TEST_LIMIT:
        remaining_files = remaining_files[:TEST_LIMIT]
        print(f"TEST MODE: Processing first {TEST_LIMIT} files for review")
    
    print(f"{len(remaining_files)} files to process")
    
    if not remaining_files:
        print("All files already processed!")
        return
    
    # Confirm before proceeding
    response = input(f"\nProceed with rewriting {len(remaining_files)} files? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        return
    
    # Process in batches
    total_batches = (len(remaining_files) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(remaining_files), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = remaining_files[i:i + BATCH_SIZE]
        
        try:
            process_batch(batch, progress, batch_num)
            progress["last_batch"] = batch_num
            save_progress(progress)
            
            # Longer delay between batches
            if batch_num < total_batches:
                print(f"Batch {batch_num}/{total_batches} complete. Pausing 10 seconds...")
                time.sleep(10)
                
        except KeyboardInterrupt:
            print(f"\nInterrupted by user. Progress saved. Resume with: python {__file__}")
            save_progress(progress)
            return
        except Exception as e:
            print(f"Batch {batch_num} failed: {e}")
            continue
    
    # Final summary
    final_progress = load_progress()
    print("\n" + "=" * 60)
    print("CONTENT REWRITING COMPLETE!")
    print(f"Successfully processed: {len(final_progress['completed'])} files")
    print(f"Failed: {len(final_progress['failed'])} files")
    
    if final_progress["failed"]:
        print("\nFailed files:")
        for failed_file in final_progress["failed"][:10]:  # Show first 10
            print(f"   - {failed_file}")
        if len(final_progress["failed"]) > 10:
            print(f"   ... and {len(final_progress['failed']) - 10} more")

if __name__ == "__main__":
    main()