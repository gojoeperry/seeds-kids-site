#!/usr/bin/env python3
"""
Complete Content Rewriter for Seeds Kids Worship
Rewrites all content using the style guide and songs database
"""

import json
import os
import re
from pathlib import Path
import yaml
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SeedsContentRewriter:
    def __init__(self):
        self.base_dir = Path(".")
        self.content_dir = self.base_dir / "content" / "activities"
        self.style_guide_path = self.base_dir / "seeds_style_guide.txt"
        self.songs_db_path = self.base_dir / "seed_content_raw.json"
        
        # Load style guide and songs database
        self.style_guide = self.load_style_guide()
        self.songs_db = self.load_songs_database()
        
    def load_style_guide(self) -> str:
        """Load the style guide"""
        try:
            with open(self.style_guide_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load style guide: {e}")
            return ""
    
    def load_songs_database(self) -> List[Dict]:
        """Load the songs database"""
        try:
            with open(self.songs_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load songs database: {e}")
            return []
    
    def get_all_article_files(self) -> List[Path]:
        """Get all article index.md files"""
        article_files = []
        for item in self.content_dir.glob("*/index.md"):
            article_files.append(item)
        return sorted(article_files)
    
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
            logger.error(f"Failed to parse frontmatter: {e}")
            return {}, content
    
    def extract_keyword_from_slug(self, slug: str) -> str:
        """Extract the main keyword from slug"""
        # Remove leading slash and activities path
        keyword = slug.replace('/activities/', '').replace('/', '')
        # Convert dashes to spaces and clean up
        keyword = keyword.replace('-', ' ')
        return keyword
    
    def generate_content_for_keyword(self, keyword: str, title: str) -> str:
        """Generate new content following the style guide"""
        
        # Create hook based on keyword
        hook_variations = [
            f"Let's explore how {keyword} can transform your family's worship time.",
            f"Picture this: your children singing Scripture with joy through {keyword}.",
            f"Have you ever wondered how {keyword} can help children memorize God's Word?",
            f"When it comes to teaching kids about faith, nothing beats the power of {keyword}."
        ]
        
        # Select hook based on keyword characteristics
        if "christmas" in keyword.lower():
            hook = f"Picture this: your children celebrating Christ's birth through {keyword} that hide God's Word in their hearts."
        elif "easter" in keyword.lower():
            hook = f"Let's explore how {keyword} can help families celebrate the resurrection with Scripture-based worship."
        elif "sunday school" in keyword.lower():
            hook = f"Have you ever wondered how to make Sunday school more engaging with {keyword} rooted in biblical truth?"
        else:
            hook = hook_variations[hash(keyword) % len(hook_variations)]
        
        # Scripture verses based on keyword theme
        scripture_options = [
            ("Psalm 96:1", "sing to the Lord a new song"),
            ("Colossians 3:16", "teach and admonish one another with psalms, hymns, and spiritual songs"),
            ("Deuteronomy 6:6-7", "teach God's Word diligently to our children"),
            ("Psalm 150:6", "let everything that has breath praise the Lord"),
            ("Ephesians 5:19", "speaking to one another with psalms, hymns, and songs from the Spirit")
        ]
        
        primary_scripture = scripture_options[hash(keyword) % len(scripture_options)]
        
        # Generate application ideas
        applications = [
            "Start your morning routine with one Scripture song to set a worship tone for the day",
            "Use these songs during car rides to church, turning travel time into worship time",
            "Create family devotional moments by pairing songs with Bible reading",
            "Transform bedtime into sacred worship with gentle Scripture-based lullabies",
            "Incorporate songs into Sunday school lessons to reinforce biblical truth",
            "Use interactive elements like hand motions and instruments to engage young worshippers"
        ]
        
        # Featured songs from database
        featured_songs_section = ""
        if self.songs_db:
            featured_songs_section = "\n## Featured Songs\n"
            for song in self.songs_db[:4]:  # Use first 4 songs
                featured_songs_section += f"- [{song['title']}]({song['url']}) — {song['body'][:100]}...\n"
        
        # Generate the complete article
        content = f"""# {title}

{hook}

## The Biblical Foundation for Scripture Songs

As {primary_scripture[0]} reminds us, we're called to "{primary_scripture[1]}." When families sing God's Word together, we follow the pattern Scripture gives us for passing faith to the next generation. Music provides a natural, joyful way to hide His Word in children's hearts through worship.

Scripture songs serve as powerful tools for family discipleship because they transform Bible verses into memorable melodies that children carry with them long after the music stops. These songs create positive associations with God's Word while engaging children's natural love for rhythm and repetition.

## How These Scripture Songs Help Children Learn Biblical Truth

### Building a Foundation of Faith Through Music

When children sing Scripture-based songs, they're not just learning melodies—they're building a foundation of biblical truth that will serve them throughout their lives. Each song becomes a prayer, a declaration of faith, and a tool for memorizing God's Word.

These {keyword} create opportunities for children to:
- **Hide Scripture in their hearts** through repetitive, joyful singing
- **Develop a love for worship** that extends beyond Sunday morning
- **Connect biblical truth** to their daily experiences and emotions
- **Experience God's presence** through music and worship

### Age-Appropriate Spiritual Development

Scripture songs naturally meet children where they are developmentally while introducing them to deep spiritual truths. Simple, repetitive melodies help younger children participate fully, while older kids can explore the biblical meaning behind each song.

## Practical Ways to Use Scripture Songs in Family Worship

### Daily Worship Integration

{applications[0]}. When children hear the same biblical truth set to music repeatedly, it naturally moves from their minds to their hearts. Choose songs that match your family's current season or spiritual focus.

### Creating Sacred Moments

{applications[3]}. Music has a unique ability to prepare hearts for prayer and worship, making it the perfect bridge between daily activities and spiritual connection.

### Church and Sunday School Applications

{applications[4]}. These songs work beautifully in both home and church settings, providing consistency between family worship and corporate worship experiences.

### Interactive Worship Ideas

- Add simple hand motions to engage kinesthetic learners
- Use rhythm instruments like shakers, tambourines, or drums
- Create call-and-response patterns with different family members
- Let children choose which songs to sing during worship time
- Incorporate dancing and movement for high-energy worship

## Building Long-Term Faith Through Music

### Scripture Memorization Made Joyful

When biblical truth is set to music, children naturally memorize Scripture without the struggle often associated with rote memorization. These songs become tools the Holy Spirit can bring to mind during difficult moments, providing comfort, guidance, and strength.

### Creating Positive Associations with God's Word

Music creates emotional connections that help children develop positive feelings toward Scripture and worship. Instead of seeing Bible reading as a chore, children who grow up with Scripture songs often develop genuine excitement about God's Word.

## Frequently Asked Questions

### How do I choose the right Scripture songs for my children's ages?

Start with simple, repetitive melodies that match your child's developmental stage. Focus on clear biblical truth rather than complex theology, and let your children's interest guide which songs become family favorites. Remember that children can often handle deeper spiritual concepts than we expect when they're presented through music.

### What if my child doesn't seem interested in worship music at first?

Make it playful and pressure-free. Let children choose which song to sing, add simple hand motions, or use instruments. Remember that seeds planted through consistent, joyful exposure to God's Word often take time to grow. Trust the Holy Spirit to work through the music even when you don't see immediate results.

### How can I help my children understand the Scripture behind each song?

Take time to read the Bible passage that inspired each song before or after singing. Explain difficult words in simple terms and connect the Scripture to your child's daily experiences. Help them see how the biblical truth applies to their own lives and relationships.

## Transform Your Family's Worship Time Today

Ready to hide God's Word in your children's hearts through joy-filled worship? These Scripture-based {keyword} provide the perfect foundation for family worship that's both biblically grounded and engaging for young hearts. Start with one song this week and watch as your family's worship time transforms into something truly special.

{featured_songs_section}

**Want to bring this biblical foundation into your home or church? Listen now and let these Scripture songs transform your family worship time!**
"""
        
        return content.strip()
    
    def rewrite_article(self, file_path: Path) -> bool:
        """Rewrite a single article"""
        try:
            # Read existing file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Parse frontmatter
            frontmatter, _ = self.parse_frontmatter(original_content)
            
            # Extract keyword from slug
            slug = frontmatter.get('slug', str(file_path.parent.name))
            keyword = self.extract_keyword_from_slug(slug)
            title = frontmatter.get('title', f"{keyword.title()} | Seeds Kids Worship")
            
            # Generate new content
            new_content = self.generate_content_for_keyword(keyword, title)
            
            # Update meta description based on new content
            meta_description = f"{title[:100]}... Hide God's Word in your children's hearts through Scripture-based worship songs."
            frontmatter['meta_description'] = meta_description
            
            # Update description
            frontmatter['description'] = f"Scripture-based {keyword} that help children memorize God's Word through joyful worship. Biblical foundation for family faith."
            
            # Write new file
            new_file_content = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n" + new_content
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
            
            logger.info(f"Successfully rewrote: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rewrite {file_path}: {e}")
            return False
    
    def rewrite_all_articles(self) -> Dict[str, int]:
        """Rewrite all articles"""
        results = {"success": 0, "failed": 0}
        
        article_files = self.get_all_article_files()
        logger.info(f"Found {len(article_files)} articles to rewrite")
        
        for file_path in article_files:
            if self.rewrite_article(file_path):
                results["success"] += 1
            else:
                results["failed"] += 1
                
        return results
    
    def run(self):
        """Main execution method"""
        logger.info("Starting complete content rewrite...")
        logger.info(f"Style guide loaded: {len(self.style_guide)} characters")
        logger.info(f"Songs database loaded: {len(self.songs_db)} songs")
        
        results = self.rewrite_all_articles()
        
        logger.info("Content rewrite complete!")
        logger.info(f"Successfully rewrote: {results['success']} articles")
        logger.info(f"Failed to rewrite: {results['failed']} articles")
        
        return results

if __name__ == "__main__":
    rewriter = SeedsContentRewriter()
    rewriter.run()