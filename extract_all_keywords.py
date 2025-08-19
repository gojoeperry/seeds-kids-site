#!/usr/bin/env python3
"""
Extract all SEO keywords from the Seeds Kids project
"""

import os
import json
from pathlib import Path
import yaml
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeywordExtractor:
    def __init__(self):
        self.base_dir = Path(".")
        self.content_dir = self.base_dir / "content" / "activities"
        self.keywords = []
        
    def get_all_article_files(self) -> list:
        """Get all article index.md files"""
        article_files = []
        for item in self.content_dir.glob("*/index.md"):
            article_files.append(item)
        return sorted(article_files)
    
    def extract_keyword_from_path(self, file_path: Path) -> str:
        """Extract keyword from directory path"""
        # Get the directory name which should be the keyword
        keyword = file_path.parent.name
        # Convert dashes to spaces
        keyword = keyword.replace('-', ' ')
        return keyword
    
    def parse_frontmatter(self, content: str) -> tuple:
        """Parse frontmatter and content"""
        if not content.startswith('---'):
            return {}, content
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
            
        try:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return frontmatter, body
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            return {}, content
    
    def extract_keywords_from_file(self, file_path: Path) -> dict:
        """Extract keyword data from a single file"""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter
            frontmatter, body = self.parse_frontmatter(content)
            
            # Extract keyword from path
            keyword_from_path = self.extract_keyword_from_path(file_path)
            
            # Extract data
            keyword_data = {
                'file_path': str(file_path),
                'directory_name': file_path.parent.name,
                'keyword_from_path': keyword_from_path,
                'title': frontmatter.get('title', ''),
                'slug': frontmatter.get('slug', ''),
                'description': frontmatter.get('description', ''),
                'meta_description': frontmatter.get('meta_description', ''),
                'tags': frontmatter.get('tags', []),
                'categories': frontmatter.get('categories', [])
            }
            
            return keyword_data
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return None
    
    def extract_all_keywords(self):
        """Extract keywords from all files"""
        article_files = self.get_all_article_files()
        logger.info(f"Found {len(article_files)} article files")
        
        for file_path in article_files:
            keyword_data = self.extract_keywords_from_file(file_path)
            if keyword_data:
                self.keywords.append(keyword_data)
        
        logger.info(f"Extracted {len(self.keywords)} keywords")
        return self.keywords
    
    def save_keywords(self, output_file: str = "all_seo_keywords.json"):
        """Save all keywords to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.keywords)} keywords to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save keywords: {e}")
    
    def print_keyword_summary(self):
        """Print summary of keywords"""
        logger.info("=== KEYWORD SUMMARY ===")
        logger.info(f"Total keywords found: {len(self.keywords)}")
        
        # Group by keyword themes
        themes = {}
        for kw in self.keywords:
            keyword = kw['keyword_from_path'].lower()
            
            if 'christmas' in keyword:
                theme = 'Christmas'
            elif 'easter' in keyword:
                theme = 'Easter'
            elif 'sunday school' in keyword:
                theme = 'Sunday School'
            elif 'vbs' in keyword or 'vacation bible school' in keyword:
                theme = 'VBS'
            elif 'worship' in keyword:
                theme = 'Worship'
            elif 'action' in keyword or 'motions' in keyword:
                theme = 'Action Songs'
            elif 'bible' in keyword:
                theme = 'Bible Songs'
            elif 'christian' in keyword:
                theme = 'Christian Songs'
            elif 'children' in keyword or 'kids' in keyword:
                theme = 'Children\'s Songs'
            else:
                theme = 'Other'
                
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(keyword)
        
        for theme, keywords in themes.items():
            logger.info(f"{theme}: {len(keywords)} keywords")
        
        # Show first 10 keywords as examples
        logger.info("\n=== SAMPLE KEYWORDS ===")
        for i, kw in enumerate(self.keywords[:10]):
            logger.info(f"{i+1}. {kw['keyword_from_path']} -> {kw['title']}")
    
    def run(self):
        """Main execution"""
        logger.info("Starting keyword extraction...")
        self.extract_all_keywords()
        self.print_keyword_summary()
        self.save_keywords()
        logger.info("Keyword extraction complete!")

if __name__ == "__main__":
    extractor = KeywordExtractor()
    extractor.run()