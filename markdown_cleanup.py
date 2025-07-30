#!/usr/bin/env python3
"""
Comprehensive Markdown Cleanup Script for Seeds Kids SEO Content
Cleans up all Markdown files according to specified requirements.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
import yaml


class MarkdownCleaner:
    def __init__(self, content_dir: str):
        self.content_dir = Path(content_dir)
        self.stats = {
            'total_files': 0,
            'files_processed': 0,
            'files_with_errors': 0,
            'frontmatter_fixes': 0,
            'placeholder_removals': 0,
            'formatting_fixes': 0,
            'title_capitalizations': 0,
            'spacing_fixes': 0,
            'markdown_syntax_fixes': 0
        }
        self.error_files = []
        self.detailed_changes = {}
        
        # Placeholder patterns to remove
        self.placeholder_patterns = [
            r'\[Insert content here\]',
            r'\[Claude generating\.\.\.\]',
            r'\[Content coming soon\]',
            r'placeholder',
            r'\[placeholder\]',
            r'\[Placeholder text\]',
            r'\[Add content here\]',
            r'\[TODO:.*?\]',
            r'\[Coming soon\]'
        ]
        
    def clean_frontmatter(self, frontmatter_content: str) -> Tuple[str, List[str]]:
        """Clean and normalize YAML frontmatter."""
        changes = []
        
        # Simple regex-based approach for better performance
        lines = frontmatter_content.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
                
            # Handle title capitalization and quoting
            if line.startswith('title:'):
                title_part = line[6:].strip()
                title_clean = title_part.strip('"\'')
                
                # Capitalize first letter if needed
                if title_clean and not title_clean[0].isupper():
                    title_clean = title_clean[0].upper() + title_clean[1:]
                    changes.append(f"Capitalized title")
                
                # Ensure quoted
                if not title_part.startswith('"') and not title_part.startswith("'"):
                    cleaned_lines.append(f'title: "{title_clean}"')
                    changes.append("Added quotes to title")
                else:
                    cleaned_lines.append(f'title: "{title_clean}"')
                    
            # Handle description quoting
            elif line.startswith('description:'):
                desc_part = line[12:].strip()
                desc_clean = desc_part.strip('"\'')
                if not desc_part.startswith('"') and not desc_part.startswith("'"):
                    cleaned_lines.append(f'description: "{desc_clean}"')
                    changes.append("Added quotes to description")
                else:
                    cleaned_lines.append(f'description: "{desc_clean}"')
                    
            # Handle slug quoting
            elif line.startswith('slug:'):
                slug_part = line[5:].strip()
                slug_clean = slug_part.strip('"\'')
                if not slug_part.startswith('"') and not slug_part.startswith("'"):
                    cleaned_lines.append(f'slug: "{slug_clean}"')
                    changes.append("Added quotes to slug")
                else:
                    cleaned_lines.append(f'slug: "{slug_clean}"')
                    
            # Handle tags (ensure they're quoted)
            elif line.startswith('- ') and not line.startswith('- "') and not line.startswith("- '"):
                tag_clean = line[2:].strip().strip('"\'')
                cleaned_lines.append(f'- "{tag_clean}"')
                if not any("quotes to tags" in change for change in changes):
                    changes.append("Added quotes to tags")
            else:
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines), changes
    
    def remove_placeholders(self, content: str) -> Tuple[str, List[str]]:
        """Remove placeholder content from the markdown."""
        changes = []
        original_content = content
        
        for pattern in self.placeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
                changes.extend([f"Removed placeholder: {match}" for match in matches])
        
        # Remove lines that are just whitespace after placeholder removal
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():  # Keep non-empty lines
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1].strip():  # Keep one empty line after content
                cleaned_lines.append(line)
        
        if len(cleaned_lines) != len(lines):
            changes.append("Removed empty lines after placeholder removal")
            
        return '\n'.join(cleaned_lines), changes
    
    def fix_markdown_formatting(self, content: str) -> Tuple[str, List[str]]:
        """Fix malformed Markdown formatting."""
        changes = []
        original_content = content
        
        # Fix malformed bold/italic formatting
        # Fix incomplete bold (**text -> **text**)
        content = re.sub(r'\*\*([^*]+)(?<!\*\*)$', r'**\1**', content, flags=re.MULTILINE)
        
        # Fix incomplete italic (*text -> *text*)
        content = re.sub(r'(?<!\*)\*([^*]+)(?<!\*)$', r'*\1*', content, flags=re.MULTILINE)
        
        # Fix incomplete underline (__text -> __text__)
        content = re.sub(r'__([^_]+)(?<!__)$', r'__\1__', content, flags=re.MULTILINE)
        
        # Fix header spacing - ensure exactly one blank line after headers
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            fixed_lines.append(line)
            
            # Check if current line is a header
            if re.match(r'^#{1,6}\s+', line):
                # Look ahead to see what follows
                j = i + 1
                empty_lines = 0
                
                # Count consecutive empty lines
                while j < len(lines) and not lines[j].strip():
                    empty_lines += 1
                    j += 1
                
                # Ensure exactly one empty line after header (if there's content after)
                if j < len(lines):  # There's content after the header
                    if empty_lines != 1:
                        changes.append(f"Fixed spacing after header: '{line.strip()}'")
                        # Remove extra empty lines we're about to skip
                        i += empty_lines
                        # Add exactly one empty line
                        fixed_lines.append('')
                    else:
                        i += 1  # Skip the existing single empty line
                else:
                    i += empty_lines  # Skip to end if no content follows
            else:
                i += 1
        
        content = '\n'.join(fixed_lines)
        
        # Remove extra blank lines (more than 2 consecutive)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        if content != original_content:
            if not any("Fixed spacing after header" in change for change in changes):
                changes.append("Fixed Markdown formatting issues")
        
        return content, changes
    
    def fix_header_consistency(self, content: str) -> Tuple[str, List[str]]:
        """Ensure headers use consistent # syntax."""
        changes = []
        original_content = content
        
        # This regex finds potential headers that might be using inconsistent formatting
        # Most files already seem to use # syntax, but we'll double-check
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Check for underline-style headers (not common in this dataset but good to check)
            if re.match(r'^=+$', line) and fixed_lines:
                # Previous line becomes h1
                fixed_lines[-1] = f"# {fixed_lines[-1]}"
                changes.append(f"Converted underline header to #: {fixed_lines[-1]}")
                continue
            elif re.match(r'^-+$', line) and fixed_lines:
                # Previous line becomes h2
                fixed_lines[-1] = f"## {fixed_lines[-1]}"
                changes.append(f"Converted underline header to ##: {fixed_lines[-1]}")
                continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        return content, changes
    
    def process_file(self, file_path: Path) -> Dict[str, any]:
        """Process a single Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content
            all_changes = []
            
            # Split frontmatter and content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    main_content = parts[2]
                    
                    # Clean frontmatter
                    cleaned_frontmatter, fm_changes = self.clean_frontmatter(frontmatter)
                    all_changes.extend(fm_changes)
                    
                    # Clean main content
                    main_content, placeholder_changes = self.remove_placeholders(main_content)
                    all_changes.extend(placeholder_changes)
                    
                    main_content, format_changes = self.fix_markdown_formatting(main_content)
                    all_changes.extend(format_changes)
                    
                    main_content, header_changes = self.fix_header_consistency(main_content)
                    all_changes.extend(header_changes)
                    
                    # Reconstruct file
                    content = f"---\n{cleaned_frontmatter}\n---{main_content}"
                else:
                    # No proper frontmatter, just clean content
                    content, placeholder_changes = self.remove_placeholders(content)
                    all_changes.extend(placeholder_changes)
                    
                    content, format_changes = self.fix_markdown_formatting(content)
                    all_changes.extend(format_changes)
            else:
                # No frontmatter, just clean content
                content, placeholder_changes = self.remove_placeholders(content)
                all_changes.extend(placeholder_changes)
                
                content, format_changes = self.fix_markdown_formatting(content)
                all_changes.extend(format_changes)
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Update statistics
                self.stats['files_processed'] += 1
                if any('frontmatter' in change.lower() or 'title' in change.lower() or 'quotes' in change.lower() for change in all_changes):
                    self.stats['frontmatter_fixes'] += 1
                if any('placeholder' in change.lower() for change in all_changes):
                    self.stats['placeholder_removals'] += 1
                if any('format' in change.lower() or 'spacing' in change.lower() for change in all_changes):
                    self.stats['formatting_fixes'] += 1
                if any('capital' in change.lower() for change in all_changes):
                    self.stats['title_capitalizations'] += 1
                if any('spacing' in change.lower() for change in all_changes):
                    self.stats['spacing_fixes'] += 1
                if any('markdown' in change.lower() or 'header' in change.lower() for change in all_changes):
                    self.stats['markdown_syntax_fixes'] += 1
            
            return {
                'file': str(file_path),
                'changes': all_changes,
                'success': True
            }
            
        except Exception as e:
            self.stats['files_with_errors'] += 1
            self.error_files.append(str(file_path))
            return {
                'file': str(file_path),
                'error': str(e),
                'success': False
            }
    
    def process_all_files(self) -> Dict[str, any]:
        """Process all Markdown files in the content directory."""
        activities_dir = self.content_dir / 'activities'
        songs_dir = self.content_dir / 'songs'
        
        all_files = []
        if activities_dir.exists():
            all_files.extend(list(activities_dir.glob('*.md')))
        if songs_dir.exists():
            all_files.extend(list(songs_dir.glob('*.md')))
        
        self.stats['total_files'] = len(all_files)
        
        results = []
        for i, file_path in enumerate(all_files):
            if i % 50 == 0:  # Progress update every 50 files
                print(f"Processing {i+1}/{len(all_files)}: {file_path.name}")
            result = self.process_file(file_path)
            results.append(result)
            
            if result['success'] and result['changes']:
                self.detailed_changes[str(file_path)] = result['changes']
        
        return {
            'stats': self.stats,
            'error_files': self.error_files,
            'detailed_changes': self.detailed_changes,
            'results': results
        }
    
    def generate_report(self, results: Dict[str, any]) -> str:
        """Generate a comprehensive report of all changes made."""
        report = []
        report.append("# Markdown Cleanup Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        report.append("## Summary Statistics")
        report.append(f"Total files found: {self.stats['total_files']}")
        report.append(f"Files processed (with changes): {self.stats['files_processed']}")
        report.append(f"Files with errors: {self.stats['files_with_errors']}")
        report.append(f"Success rate: {((self.stats['total_files'] - self.stats['files_with_errors']) / self.stats['total_files'] * 100):.1f}%")
        report.append("")
        
        # Issue breakdown
        report.append("## Issues Found and Fixed")
        report.append(f"Frontmatter normalization fixes: {self.stats['frontmatter_fixes']}")
        report.append(f"Placeholder content removed: {self.stats['placeholder_removals']}")
        report.append(f"Markdown formatting corrections: {self.stats['formatting_fixes']}")
        report.append(f"Title capitalization fixes: {self.stats['title_capitalizations']}")
        report.append(f"Spacing fixes: {self.stats['spacing_fixes']}")
        report.append(f"Markdown syntax fixes: {self.stats['markdown_syntax_fixes']}")
        report.append("")
        
        # Error files
        if self.error_files:
            report.append("## Files with Errors")
            for error_file in self.error_files:
                report.append(f"- {error_file}")
            report.append("")
        
        # Detailed changes (first 10 files as examples)
        if self.detailed_changes:
            report.append("## Sample Detailed Changes")
            count = 0
            for file_path, changes in self.detailed_changes.items():
                if count >= 10:  # Limit to first 10 for readability
                    break
                report.append(f"### {Path(file_path).name}")
                for change in changes:
                    report.append(f"  - {change}")
                report.append("")
                count += 1
            
            if len(self.detailed_changes) > 10:
                report.append(f"... and {len(self.detailed_changes) - 10} more files with changes")
                report.append("")
        
        return '\n'.join(report)


def main():
    """Main execution function."""
    content_dir = r"C:\Users\joepe\seeds-kids-seo\content"
    
    print("Starting comprehensive Markdown cleanup...")
    print(f"Processing directory: {content_dir}")
    print("=" * 60)
    
    cleaner = MarkdownCleaner(content_dir)
    results = cleaner.process_all_files()
    
    print("\n" + "=" * 60)
    print("Cleanup completed!")
    
    # Generate and display report
    report = cleaner.generate_report(results)
    print("\n" + report)
    
    # Save detailed report to file
    report_file = Path(content_dir).parent / "cleanup_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return results


if __name__ == "__main__":
    main()