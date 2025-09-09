#!/usr/bin/env python3
"""
Comprehensive Seeds Content Rewriter with Claude API
Rewrites all content using the full 186-song Seeds database with Claude API for high-quality content
"""

import json
import os
import re
from pathlib import Path
import yaml
from typing import Dict, List, Any
import logging
from datetime import datetime
import random
import anthropic
from dotenv import load_dotenv
from hook_variations import HookGenerator
from content_variations import ContentBlocks, SectionVariations

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveSeedsRewriter:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        self.base_dir = Path(".")
        self.site_dir = self.base_dir / "site"
        self.content_dir = self.site_dir / "content"
        self.activities_dir = self.content_dir / "activities"
        self.songs_dir = self.content_dir / "songs"
        
        # Progress tracking file
        self.progress_file = self.base_dir / "rewrite_progress.json"
        
        # Initialize Claude API client
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Load Seeds data
        self.seeds_songs = self.load_seeds_songs()
        self.style_guide = self.load_style_guide()
        
        # Initialize content variation generators
        self.content_blocks = ContentBlocks()
        self.section_variations = SectionVariations()
        
        # Create directories if they don't exist
        self.songs_dir.mkdir(exist_ok=True)
        
        # Song categorization
        self.songs_by_category = self.categorize_songs()
        
        # Load progress tracking
        self.processed_files = self.load_progress()
        
    def load_seeds_songs(self) -> List[Dict]:
        """Load the full Seeds songs database"""
        try:
            songs_path = self.base_dir / "assets" / "seeds_songs.json"
            with open(songs_path, 'r', encoding='utf-8') as f:
                songs = json.load(f)
            logger.info(f"Loaded {len(songs)} Songs from Seeds database")
            return songs
        except Exception as e:
            logger.error(f"Failed to load Seeds songs: {e}")
            return []
    
    def load_style_guide(self) -> str:
        """Load the Seeds style guide"""
        try:
            style_path = self.base_dir / "seeds_style_guide.txt"
            with open(style_path, 'r', encoding='utf-8') as f:
                guide = f.read()
            logger.info("Loaded Seeds style guide")
            return guide
        except Exception as e:
            logger.error(f"Failed to load style guide: {e}")
            return ""
    
    def load_progress(self) -> set:
        """Load the set of already processed files"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed = set(data.get('processed_files', []))
                    logger.info(f"Loaded progress: {len(processed)} files already processed")
                    return processed
            else:
                logger.info("No progress file found, starting fresh")
                return set()
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return set()
    
    def save_progress(self):
        """Save the current progress to file"""
        try:
            data = {
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Progress saved: {len(self.processed_files)} files processed")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def mark_file_processed(self, file_path: Path):
        """Mark a file as processed"""
        relative_path = str(file_path.relative_to(self.base_dir))
        self.processed_files.add(relative_path)
        self.save_progress()
    
    def categorize_songs(self) -> Dict[str, List[Dict]]:
        """Categorize songs by themes and characteristics using comprehensive analysis"""
        categories = {
            'christmas': [],
            'easter': [],
            'worship': [],
            'praise': [],
            'courage': [],
            'forgiveness': [],
            'scripture_memory': [],
            'action_songs': [],
            'lullabies': [],
            'toddlers': [],
            'preschool': [],
            'all_ages': [],
            'faith_building': [],
            'gospel_songs': [],
            'bible_stories': [],
            'character_building': [],
            'sunday_school': [],
            'vbs_songs': []
        }
        
        for song in self.seeds_songs:
            title_lower = song.get('title', '').lower()
            description_lower = song.get('description', '').lower()
            style_lower = song.get('style', '').lower()
            scripture_lower = song.get('scripture', '').lower()
            
            # Comprehensive categorization
            # Christmas/Holiday themes
            if any(word in title_lower + description_lower for word in ['christmas', 'bethlehem', 'mary', 'nativity', 'manger', 'wise men', 'star']):
                categories['christmas'].append(song)
            
            # Easter themes
            if any(word in title_lower + description_lower for word in ['easter', 'resurrection', 'cross', 'tomb', 'alive', 'risen']):
                categories['easter'].append(song)
            
            # Worship/Praise themes
            if any(word in style_lower + description_lower for word in ['worship', 'praise', 'adoration', 'reverent', 'holy']):
                categories['worship'].append(song)
                categories['praise'].append(song)
            
            # Action/Movement songs
            if any(word in style_lower + description_lower for word in ['energetic', 'action', 'movement', 'dance', 'active', 'upbeat']):
                categories['action_songs'].append(song)
                
            # Lullabies/Calm songs
            if any(word in style_lower + description_lower for word in ['lullaby', 'peaceful', 'gentle', 'calm', 'quiet', 'bedtime']):
                categories['lullabies'].append(song)
                
            # Character building
            if any(word in description_lower for word in ['character', 'obedience', 'kindness', 'love', 'patience', 'forgiveness', 'courage', 'strength']):
                categories['character_building'].append(song)
                
            # Gospel/Salvation themes
            if any(word in description_lower + scripture_lower for word in ['salvation', 'gospel', 'sin', 'grace', 'cross', 'jesus', 'savior']):
                categories['gospel_songs'].append(song)
                
            # Bible story themes
            if any(word in description_lower for word in ['story', 'david', 'moses', 'noah', 'abraham', 'creation', 'genesis', 'psalm']):
                categories['bible_stories'].append(song)
                
            # Scripture memory
            if any(word in description_lower for word in ['memory', 'memorize', 'verse', 'scripture', 'bible']):
                categories['scripture_memory'].append(song)
                
            # Age categorization
            target_age = song.get('target_age', '').lower()
            if 'toddler' in target_age:
                categories['toddlers'].append(song)
            elif 'preschool' in target_age:
                categories['preschool'].append(song)
            else:
                categories['all_ages'].append(song)
                
            # Default categories for comprehensive coverage
            categories['faith_building'].append(song)
            categories['sunday_school'].append(song)
            if len(categories['vbs_songs']) < 50:  # Limit VBS songs
                categories['vbs_songs'].append(song)
        
        return categories
    
    def generate_content_with_claude(self, prompt: str, max_tokens: int = 8192) -> str:
        """Generate content using Claude API"""
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return ""
    
    def count_words(self, content: str) -> int:
        """Count words in content, excluding frontmatter and schema markup"""
        # Remove frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]
        
        # Remove schema markup
        import re
        content = re.sub(r'<script type="application/ld\+json">.*?</script>', '', content, flags=re.DOTALL)
        
        # Count words
        words = content.split()
        return len(words)
    
    def generate_content_with_word_limit_validation(self, prompt: str, filename: str) -> str:
        """Generate content with strict word limit validation and regeneration if needed"""
        MAX_ATTEMPTS = 3
        MIN_WORDS = 1200
        MAX_WORDS = 1800
        
        for attempt in range(MAX_ATTEMPTS):
            logger.info(f"Generating content for {filename}, attempt {attempt + 1}/{MAX_ATTEMPTS}")
            
            # Make the prompt even stricter on subsequent attempts
            if attempt > 0:
                strict_prompt = prompt.replace(
                    "CRITICAL LENGTH REQUIREMENTS:\n- ABSOLUTE WORD COUNT: 1200-1800 words (will be verified automatically)\n- NO EXCEPTIONS: Content over 1800 words will be rejected and regenerated\n- WRITE CONCISELY: Focus on quality over quantity\n- TARGET: Aim for 1400-1600 words for optimal engagement\n- STRICT ENFORCEMENT: This limit is non-negotiable",
                    f"CRITICAL WORD LIMIT ENFORCEMENT - ATTEMPT {attempt + 1}:\n"
                    f"- ABSOLUTE MAXIMUM: 1800 words (you will be penalized for exceeding this)\n"
                    f"- TARGET RANGE: 1200-1800 words ONLY\n"
                    f"- This is attempt {attempt + 1} - previous attempts were TOO LONG\n"
                    f"- Write CONCISELY and stay within limits\n"
                    f"- Cut unnecessary content to fit the limit\n"
                    f"- DO NOT exceed 1800 words under ANY circumstances"
                )
                content = self.generate_content_with_claude(strict_prompt)
            else:
                content = self.generate_content_with_claude(prompt)
            
            if not content:
                logger.error(f"No content generated for {filename} on attempt {attempt + 1}")
                continue
            
            word_count = self.count_words(content)
            logger.info(f"{filename} generated {word_count} words on attempt {attempt + 1}")
            
            if MIN_WORDS <= word_count <= MAX_WORDS:
                logger.info(f"✓ {filename} meets word count requirements: {word_count} words")
                return content
            elif word_count < MIN_WORDS:
                logger.warning(f"⚠ {filename} too short: {word_count} words (min: {MIN_WORDS})")
                continue
            else:
                logger.warning(f"⚠ {filename} too long: {word_count} words (max: {MAX_WORDS})")
                continue
        
        # If all attempts failed, use the last generated content anyway but log a warning
        logger.error(f"❌ Failed to generate content within word limits for {filename} after {MAX_ATTEMPTS} attempts. Using last attempt with {self.count_words(content) if content else 0} words.")
        return content
    
    def generate_compelling_meta_description(self, filename: str, content: str) -> str:
        """Generate compelling, click-worthy meta descriptions based on content and topic"""
        title = filename.replace('-', ' ').title()
        title_lower = title.lower()
        
        # Extract key benefits and compelling elements from content
        if 'grade 1' in title_lower or 'first grade' in title_lower:
            return f"Transform your Grade 1 classroom with expert-backed strategies for using {title.lower()}. Discover proven techniques that boost engagement, support motor development, and help 6-7 year olds learn through movement. Get practical tips from education professionals!"
        
        elif 'preschool' in title_lower or 'preschooler' in title_lower:
            return f"Unlock the secret to preschooler engagement with {title.lower()} that support brain development. Expert insights on ages 3-5 learning, emotional regulation, and school readiness. Proven strategies parents and teachers love!"
            
        elif 'toddler' in title_lower:
            return f"Master toddler music activities with {title.lower()} designed for ages 18mo-3yrs. Expert guidance on language development, motor skills, and managing high energy. Transform challenging toddler behaviors into joyful learning!"
            
        elif 'nursery school' in title_lower:
            return f"Elevate your nursery school program with {title.lower()} that build socialization and school readiness. Professional strategies for ages 3-4, separation anxiety solutions, and parent engagement ideas that work!"
            
        elif 'action songs' in title_lower:
            return f"Supercharge child development with {title.lower()} that boost motor skills, coordination, and brain function. Science-backed benefits of movement + music, plus expert tips for kinesthetic learners. Transform learning through movement!"
            
        elif 'sunday school' in title_lower:
            return f"Revolutionize your Sunday school with {title.lower()} that actually work. Expert teaching strategies, age-appropriate activities, and proven methods that help children memorize Scripture joyfully. See dramatic engagement improvements!"
            
        elif 'lullabies' in title_lower or 'bedtime' in title_lower:
            return f"Solve bedtime battles with {title.lower()} backed by sleep science. Expert guidance on bedtime routines, calming techniques, and how music affects children's nervous systems. Peaceful nights await!"
            
        elif 'christmas' in title_lower or 'holiday' in title_lower:
            return f"Create magical Christmas memories with {title.lower()} that teach the true meaning of the season. Expert ideas for family traditions, church programs, and balancing secular/spiritual celebrations. Make this Christmas unforgettable!"
            
        elif 'worship' in title_lower:
            return f"Transform children's spiritual development with {title.lower()} designed for different ages and stages. Expert insights on reverent worship, family practices, and creating meaningful spiritual experiences that last a lifetime."
            
        elif 'bible songs' in title_lower or 'scripture' in title_lower:
            return f"Unlock powerful Scripture memorization with {title.lower()} that make Bible learning effortless. Research-backed techniques, age-appropriate methods, and expert strategies that help children hide God's Word in their hearts permanently."
            
        elif 'playlist' in title_lower:
            return f"Build the perfect {title.lower()} with expert curation strategies and child development insights. Proven techniques for age-appropriate selection, engagement optimization, and family worship integration. Create playlists kids actually want to hear!"
            
        elif 'ministry' in title_lower:
            return f"Elevate your children's ministry with {title.lower()} strategies from industry professionals. Proven programming techniques, volunteer training insights, and engagement methods that transform Sunday school and church programs."
            
        else:
            # Generic compelling description
            return f"Discover expert strategies for {title.lower()} that actually work. Research-backed insights, proven techniques, and professional tips that transform how children learn and engage. See immediate results with these game-changing methods!"
    
    def add_schema_markup(self, filename: str, content: str, relevant_songs: List[Dict]) -> str:
        """Add JSON-LD schema markup for better SEO"""
        import json
        from datetime import datetime
        
        title = filename.replace('-', ' ').title()
        
        # Extract FAQ section if it exists
        faq_data = self.extract_faq_data(content)
        
        # Create Article schema
        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "author": {
                "@type": "Organization",
                "name": "Seeds Kids Worship"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Seeds Kids Worship",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://seedskidsworship.com/logo.png"
                }
            },
            "datePublished": datetime.now().isoformat(),
            "dateModified": datetime.now().isoformat(),
            "description": self.generate_compelling_meta_description(filename, content)[:160],
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"https://seedskidsworship.com/activities/{filename}/"
            }
        }
        
        # Create FAQPage schema if FAQs exist
        faq_schema = None
        if faq_data:
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": faq_data
            }
        
        # Create Product schema for featured songs
        products_schema = []
        for song in relevant_songs[:5]:  # Limit to 5 products
            if song.get('title') and song.get('webpage_url'):
                product_schema = {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": song['title'],
                    "description": song.get('description', ''),
                    "url": song.get('webpage_url', ''),
                    "brand": {
                        "@type": "Brand",
                        "name": "Seeds Kids Worship"
                    },
                    "category": "Children's Christian Music"
                }
                if song.get('album'):
                    product_schema["album"] = song['album']
                products_schema.append(product_schema)
        
        # Build schema markup HTML
        schema_html = '\n<script type="application/ld+json">\n' + json.dumps(article_schema, indent=2) + '\n</script>\n'
        
        if faq_schema:
            schema_html += '\n<script type="application/ld+json">\n' + json.dumps(faq_schema, indent=2) + '\n</script>\n'
        
        for product_schema in products_schema:
            schema_html += '\n<script type="application/ld+json">\n' + json.dumps(product_schema, indent=2) + '\n</script>\n'
        
        # Add schema markup at the end of the content
        return content + schema_html
    
    def extract_faq_data(self, content: str) -> List[Dict]:
        """Extract FAQ questions and answers from content for schema markup"""
        import re
        
        faq_data = []
        
        # Find FAQ section
        faq_match = re.search(r'## Frequently Asked Questions(.*?)(?=##|$)', content, re.DOTALL)
        if not faq_match:
            return faq_data
        
        faq_section = faq_match.group(1)
        
        # Extract individual Q&A pairs
        qa_pattern = r'### (.+?)\n\n(.+?)(?=\n### |\n\n##|\Z)'
        qa_matches = re.findall(qa_pattern, faq_section, re.DOTALL)
        
        for question, answer in qa_matches[:5]:  # Limit to 5 FAQs
            faq_item = {
                "@type": "Question",
                "name": question.strip(),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer.strip()
                }
            }
            faq_data.append(faq_item)
        
        return faq_data
    
    def create_topic_specific_guidance(self, title: str) -> str:
        """Create rich, topic-specific content guidance based on the blog title"""
        title_lower = title.lower()
        
        # Age-specific content guidance
        if 'grade 1' in title_lower or 'first grade' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include extensive information about Grade 1 children's developmental characteristics (ages 6-7)
- Explain Grade 1 attention spans, physical development, and learning styles
- Detail how Grade 1 children learn best through movement, repetition, and visual cues
- Discuss Grade 1 social-emotional development and need for structure vs. creativity
- Address common Grade 1 challenges: reading development, following directions, peer interaction
- Provide specific classroom management techniques that work for Grade 1 teachers
- Include seasonal considerations for Grade 1 attention and energy levels
- Add parent-teacher collaboration strategies for reinforcing learning at home
"""
        elif 'preschool' in title_lower or 'preschooler' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include comprehensive information about preschooler development (ages 3-5)
- Explain preschooler brain development and how music impacts neural pathways
- Detail preschooler attention spans, memory formation, and learning preferences
- Discuss emotional regulation challenges and how music helps preschoolers cope
- Address common preschooler behaviors: tantrums, separation anxiety, social development
- Provide specific strategies for engaging reluctant or shy preschoolers
- Include toilet training, nap time, and daily routine integration strategies
- Add guidance for parents navigating the transition to formal education
"""
        elif 'toddler' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include detailed information about toddler development (ages 18 months - 3 years)
- Explain toddler language development and how music accelerates vocabulary growth
- Detail toddler motor skill development and how movement songs support gross motor skills
- Discuss toddler independence challenges and how music provides positive structure
- Address common toddler issues: sleep disruptions, eating challenges, communication delays
- Provide strategies for managing toddler attention spans and high energy levels
- Include safety considerations for toddler music activities and props
- Add guidance for parents dealing with typical toddler resistance and testing behaviors
"""
        elif 'nursery school' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include information about nursery school age children (typically 3-4 years old)
- Explain nursery school program goals: socialization, independence, school readiness
- Detail how nursery school children learn through play, exploration, and peer interaction
- Discuss nursery school daily routines and how music supports transitions
- Address separation anxiety, sharing challenges, and early friendship development
- Provide strategies for nursery school teachers managing diverse developmental levels
- Include parent involvement opportunities and home extension activities
- Add guidance for preparing children for the transition to formal preschool or kindergarten
"""
        elif 'action songs' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include comprehensive information about the benefits of movement and music for child development
- Explain how action songs support gross motor development, coordination, and spatial awareness
- Detail the connection between movement and brain development in children
- Discuss how action songs help with sensory integration and self-regulation
- Address different learning styles and how kinesthetic learners especially benefit from action songs
- Provide specific movement activities and choreography suggestions for different ages
- Include classroom management techniques for action song activities
- Add guidance for accommodating children with special needs or mobility limitations
- Explain how action songs build confidence and reduce anxiety in children
- Detail seasonal and weather considerations for indoor vs. outdoor action song activities
"""
        elif 'lullabies' in title_lower or 'bedtime' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include comprehensive information about children's sleep development and bedtime routines
- Explain how music affects children's nervous system and promotes relaxation
- Detail age-appropriate bedtime routines from infancy through elementary years
- Discuss common sleep challenges: bedtime resistance, night fears, sleep disruptions
- Address the science of how lullabies affect heart rate, breathing, and brain waves
- Provide strategies for creating calming bedtime environments
- Include guidance for parents dealing with sleep regressions and developmental changes
- Add information about co-sleeping considerations and independent sleep skills
- Explain cultural traditions around lullabies and their psychological benefits
"""
        elif 'christmas' in title_lower or 'holiday' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include rich information about Christmas traditions and their spiritual significance
- Explain how Christmas music helps children understand the nativity story
- Detail age-appropriate ways to teach children about Jesus' birth and its meaning
- Discuss family Christmas traditions and how music creates lasting memories
- Address the balance between secular and spiritual Christmas celebrations
- Provide ideas for Christmas pageants, family celebrations, and church programs
- Include guidance for families navigating different faith backgrounds during holidays
- Add suggestions for Advent activities and countdown traditions using music
- Explain how Christmas songs teach children about anticipation, celebration, and worship
"""
        elif 'worship' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include comprehensive information about children's spiritual development and worship understanding
- Explain how children at different ages understand and participate in worship
- Detail the components of meaningful children's worship: praise, prayer, Scripture, response
- Discuss creating reverent yet age-appropriate worship experiences for children
- Address common challenges: short attention spans, distractions, varying spiritual backgrounds
- Provide strategies for teaching children about reverence, respect, and genuine worship
- Include guidance for family worship practices and making worship meaningful at home
- Add information about children's worship in different church contexts and traditions
"""
        elif 'bible songs' in title_lower or 'scripture' in title_lower:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include extensive information about Scripture memorization and its lifelong benefits
- Explain how music-based Scripture learning affects memory retention and recall
- Detail age-appropriate Bible teaching methods and how songs enhance understanding
- Discuss the importance of accurate biblical content in children's music
- Address different learning styles and how musical Scripture learning accommodates various needs
- Provide strategies for helping children understand and apply biblical concepts
- Include guidance for parents who feel uncertain about teaching the Bible to children
- Add information about child-friendly Bible translations and their musical adaptations
"""
        else:
            return """
TOPIC-SPECIFIC CONTENT REQUIREMENTS:
- Include comprehensive information about the specific topic addressed in the blog title
- Explain the developmental, educational, or spiritual benefits related to this topic
- Detail practical applications and real-world usage scenarios
- Discuss common challenges parents and educators face with this topic
- Address different approaches and methodologies related to the subject
- Provide expert insights and research-backed information where applicable
- Include troubleshooting guidance for common issues
- Add age-appropriate considerations and adaptation strategies
"""
        
    def create_blog_prompt(self, existing_file_path: Path, relevant_songs: List[Dict]) -> str:
        """Create a comprehensive prompt for Claude to rewrite blog content with rich topic-specific content"""
        
        # Read existing content
        try:
            with open(existing_file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except:
            existing_content = ""
        
        # Extract title from filename or existing content
        filename = existing_file_path.stem
        title = filename.replace('-', ' ').title()
        
        # Create topic-specific content guidance based on the blog title
        topic_guidance = self.create_topic_specific_guidance(title)
        
        # Extract number from title ONLY if it promises a specific count (e.g., "40 Popular Songs" -> 40)
        import re
        # Only look for numbers at the beginning of titles that promise specific counts
        title_match = re.search(r'^(\d+)\s+', title)
        target_song_count = int(title_match.group(1)) if title_match else None
        
        # Only create numbered lists if there's a specific number at the start of the title
        # Don't force numbered lists just because of words like "best" or "top" without numbers
        if not title_match:
            target_song_count = None
        
        # Handle numbered list creation only if title promises specific count
        if target_song_count:
            # Ensure we have enough songs to match the title
            if len(relevant_songs) < target_song_count:
                # Fill with additional songs from other categories
                all_other_songs = [s for s in self.seeds_songs if s not in relevant_songs]
                needed_count = target_song_count - len(relevant_songs)
                relevant_songs.extend(all_other_songs[:needed_count])
            
            # Create comprehensive numbered song list with rich details
            song_descriptions = []
            for i, song in enumerate(relevant_songs[:target_song_count], 1):
                # Build rich song description with all available details
                song_info = f"{i}. **[{song['title']}]({song.get('webpage_url', '#')})** ({song['scripture']}): {song['description']}"
                
                # Add rich metadata
                if song.get('album'):
                    song_info += f" - Album: {song['album']}"
                if song.get('duration'):
                    song_info += f" - Duration: {song['duration']}"
                if song.get('year'):
                    song_info += f" - Year: {song['year']}"
                if song.get('style'):
                    song_info += f" - Style: {song['style']}"
                    
                song_descriptions.append(song_info)
            
            songs_section = "\n".join(song_descriptions)
        else:
            # Create featured songs section with rich details instead of numbered list
            featured_songs = relevant_songs[:8]  # Showcase more featured songs
            song_descriptions = []
            for song in featured_songs:
                # Build rich featured song description
                song_info = f"**[{song['title']}]({song.get('webpage_url', '#')})** ({song['scripture']}): {song['description']}"
                
                # Add rich metadata
                if song.get('album'):
                    song_info += f" - Album: {song['album']}"
                if song.get('duration'):
                    song_info += f" - Duration: {song['duration']}"
                if song.get('year'):
                    song_info += f" - Year: {song['year']}"
                if song.get('style'):
                    song_info += f" - Style: {song['style']}"
                    
                song_descriptions.append(song_info)
            
            songs_section = "\n".join(song_descriptions)
        
        # Create content requirements based on whether numbered list is needed
        if target_song_count:
            requirements = f"""
SEO & CONTENT REQUIREMENTS:
1. Write an engaging, comprehensive blog post that delivers on the title's promise with rich, valuable content
2. Include the target keyword naturally throughout (derived from title)
3. Use H1, H2, H3 headings with keyword variations for SEO structure
4. ABSOLUTE PRIORITY: Include a complete numbered list of ALL {target_song_count} songs mentioned in the title
5. Organize the numbered song list into logical, thematic categories with descriptive subheadings
6. Create FOCUSED, ENGAGING content that readers will genuinely enjoy and find valuable
7. Include practical applications, real-world examples, and specific usage scenarios
8. Add information about how each song category serves different family needs
9. Include age-specific recommendations with explanations for each age group
10. Provide worship ideas, activity suggestions, and creative implementation strategies
11. Add character-building insights explaining how specific songs develop Christian virtues
12. Include seasonal and situational usage recommendations (holidays, celebrations)
13. Integrate key information from the Seeds Songs database (albums, Scripture connections)
14. Add practical elements about how families use these songs in real worship scenarios
15. Include troubleshooting tips for common challenges families face with children's worship
16. Provide Scripture integration strategies showing how songs connect to Bible study
17. Add FAQ section with helpful answers to genuine parent concerns
18. Follow the Seeds style guide exactly (warm, encouraging, Scripture-focused tone)
19. Include relevant Bible verses naturally throughout with explanation of their significance
20. End with compelling, specific call-to-action encouraging families to start using Seeds songs

CONTENT STRUCTURE:
1. Engaging Hook with Real Family Scenario
2. Biblical Foundation for Worship Music (with Scripture explanation)
3. Why These Songs Matter for Children's Faith (with examples)
4. Practical Applications for Families (real-world usage ideas)
5. Age-Appropriate Usage Guidelines (recommendations for each age)
6. Character Building Through Scripture Songs (virtue development)
7. Seasonal Usage Recommendations (holidays, celebrations)
8. Complete Numbered Song List (ALL {target_song_count} songs with thematic grouping)
9. Worship Ideas and Implementation Strategies
10. Common Family Worship Challenges
11. FAQ Section with Helpful Answers
12. Call-to-Action with Next Steps

NUMBERED SONG LIST:
Include ALL {target_song_count} songs in a section titled "Complete List of {target_song_count} [Type] Songs":

{songs_section}

CRITICAL INSTRUCTIONS:
- The numbered list is the ABSOLUTE PRIORITY - it must reach the FULL number promised in the title
- Do not stop at 30 or 35 - continue to {target_song_count}
- If you need to choose between rich content and a complete numbered list, choose the complete numbered list
- Structure the content to prioritize completing the full numbered list first
- Keep introductory content concise to allow maximum tokens for the complete numbered list
"""
        else:
            requirements = f"""
SEO & CONTENT REQUIREMENTS:
1. Write an engaging blog post with FOCUSED, VALUABLE content that readers will love
2. Include the target keyword naturally throughout (derived from title)
3. Use H1, H2, H3 headings with keyword variations for optimal SEO structure
4. Create featured songs sections with practical usage ideas
5. Organize content thematically with explanations of how each theme serves families
6. Include practical applications with real-world examples and specific scenarios
7. Add character-building insights showing how songs develop Christian virtues
8. Provide age-appropriate recommendations with explanations
9. Include seasonal and situational usage recommendations (holidays, family events)
10. Integrate key information from Seeds Songs database (Scripture connections, albums)
11. Add practical elements about how real families use these songs successfully
12. Include troubleshooting tips for common challenges in family worship with children
13. Provide specific Scripture integration strategies connecting songs to Bible study
14. Add creative worship ideas, activity suggestions, and implementation strategies
15. Include ministry applications for churches, Sunday schools, and children's programs
16. Add parent education content about child development and music-based learning
17. Provide comparison and selection guidance to help parents choose appropriate songs
18. Include FAQ section with comprehensive, genuinely helpful answers
19. Follow the Seeds style guide exactly (warm, encouraging, Scripture-focused tone)
20. Include relevant Bible verses naturally throughout with detailed explanations
21. Reference actual Seeds songs extensively throughout the content with clickable links
22. End with compelling, specific call-to-action with clear next steps for families

CONTENT STRUCTURE:
1. Engaging Hook with Real Family Scenario
2. Biblical Foundation for Worship Music (with detailed Scripture explanation)
3. Why These Songs Matter for Children's Faith (with specific developmental benefits)
4. Comprehensive Practical Applications for Families (extensive real-world usage scenarios)
5. Detailed Age-Appropriate Usage Guidelines (specific recommendations for each stage)
6. Character Building Through Scripture Songs (specific virtue development strategies)
7. Seasonal and Situational Usage Recommendations (holidays, challenges, celebrations)
8. Featured Scripture Songs Section (rich descriptions with practical applications)
9. Ministry and Church Applications (Sunday school, VBS, family services)
10. Advanced Worship Ideas and Creative Implementation Strategies
11. Troubleshooting Common Family Worship Challenges (practical solutions)
12. Scripture Integration and Bible Study Connection Ideas
13. Parent Education: Child Development and Music Learning
14. Song Selection and Comparison Guidance
15. Comprehensive FAQ Section with Detailed, Helpful Answers
16. Strong Call-to-Action with Specific, Actionable Next Steps

FEATURED SONGS TO REFERENCE:
{songs_section}
"""
        
        prompt = f"""
You are a professional content writer specializing in Christian children's music and family worship. You need to completely rewrite a blog post with RICH, TOPIC-FOCUSED content plus Seeds Kids Worship integration.

STYLE GUIDE:
{self.style_guide}

EXISTING BLOG TITLE/TOPIC: {title}

{topic_guidance}

CURRENT CONTENT (for reference only - DO NOT copy):
{existing_content[:1000]}...

{requirements}

CRITICAL REQUIREMENTS FOR FOCUSED, ENGAGING CONTENT:
- Do NOT include any frontmatter (---) or metadata
- Write ONLY the blog content itself
- STRICT WORD LIMIT: Keep total article between 1200-1800 words maximum
- Be concise and actionable - avoid unnecessary elaboration
- AVOID REPETITIVE OPENINGS: Do NOT start with "Picture this" - use varied, engaging openings like "Imagine," "Consider," "Have you ever wondered," "What if," "Envision," etc.
- VARY YOUR LANGUAGE: Avoid repetitive phrases throughout the article. Use diverse vocabulary and sentence structures
- AVOID OVERUSED PHRASES: Do not repeatedly use phrases like "hide God's Word in their hearts," "building a foundation of faith," "biblically grounded and engaging for young hearts," or "transform your family worship time"
- USE DIVERSE EXPRESSIONS: Instead of repetitive patterns, vary your language for Scripture memorization, faith building, and family worship concepts

CONTENT BALANCE PRIORITY:
1. PRIMARY FOCUS: Create focused, educational content about the BLOG TOPIC ITSELF (70% of content)
2. SECONDARY INTEGRATION: Weave in Seeds songs naturally as supporting examples (30% of content)
3. The blog should be valuable and concise - then Seeds songs enhance the value

TOPIC-FOCUSED CONTENT REQUIREMENTS:
- STRICT WORD LIMIT: Keep total article between 1200-1800 words maximum
- Do NOT exceed 2000 words under any circumstances
- CREATE VALUABLE EDUCATIONAL CONTENT about the blog topic that parents and educators will bookmark
- Include key information about child development, education techniques, or spiritual growth related to the topic
- Add research-backed insights and professional best practices related to the subject
- Provide practical troubleshooting for common challenges specific to the topic
- Include practical scenarios with implementation guidance
- Add story-telling elements that help readers visualize successful topic implementation
- Provide seasonal adaptations for the topic area
- Include expert tips from child development, education, or ministry perspectives

SEEDS INTEGRATION REQUIREMENTS:
- Reference specific Seeds songs naturally within the topic-focused content
- Show how Seeds songs ENHANCE and SUPPORT the main topic rather than replace topic content
- Include clickable links to Seeds website URLs when mentioning songs
- Connect songs to specific aspects of the topic (e.g., how action songs support Grade 1 motor development)
- Use Songs as EXAMPLES within broader topic discussions, not as the main content

CRITICAL LENGTH REQUIREMENTS:
- ABSOLUTE WORD COUNT: 1200-1800 words (will be verified automatically)
- NO EXCEPTIONS: Content over 1800 words will be rejected and regenerated
- WRITE CONCISELY: Focus on quality over quantity
- TARGET: Aim for 1400-1600 words for optimal engagement
- STRICT ENFORCEMENT: This limit is non-negotiable

Please write the complete, rich, engaging blog post now:
"""
        
        return prompt
    
    def generate_song_page(self, song: Dict) -> str:
        """Generate individual song page content"""
        title = song.get('title', '')
        scripture = song.get('scripture', '')
        description = song.get('description', '')
        album = song.get('album', '')
        year = song.get('year', '')
        duration = song.get('duration', '')
        style = song.get('style', '')
        webpage_url = song.get('webpage_url', '')
        spotify_url = song.get('spotify_url', '')
        
        # Create varied hook using HookGenerator
        hook_generator = HookGenerator()
        context = "song"
        if "christmas" in title.lower():
            context = "christmas"
        elif "easter" in title.lower():
            context = "easter"
        elif "action" in title.lower():
            context = "action"
        elif "worship" in title.lower():
            context = "worship"
        
        hook = hook_generator.generate_hook(title, context)
        
        # Generate varied content sections
        biblical_header = self.section_variations.get_biblical_header()
        foundation_intro = self.content_blocks.get_foundation_intro(title, scripture, description)
        learning_block = self.content_blocks.get_learning_block(title)
        
        content = f"""# {title}: Scripture Song from {scripture}

{hook}

## {biblical_header}

{foundation_intro}

{learning_block}

## Song Details

- **Scripture Reference**: {scripture}
- **Album**: {album}
- **Duration**: {duration}
- **Musical Style**: {style}
- **Target Age**: All Ages
- **Year Released**: {year}

## {self.section_variations.get_usage_header()}

### Daily Worship Integration

Start your morning routine with "{title}" to set a worship tone for the day. When children hear the same biblical truth from {scripture} set to music repeatedly, it naturally moves from their minds to their hearts.

### Creating Sacred Moments

Use this song during car rides to church, turning travel time into worship time. The combination of music and Scripture creates perfect opportunities for family discipleship conversations about {scripture}.

### Sunday School and Church Applications

"{title}" works beautifully in both home and church settings, providing consistency between family worship and corporate worship experiences. Teachers can use this song to reinforce the biblical truth of {scripture} in their lessons.

## {self.section_variations.get_power_header()}

### Scripture Memorization Made Joyful

When biblical truth like {scripture} is set to music, children naturally memorize Scripture without the struggle often associated with rote memorization. "{title}" becomes a tool the Holy Spirit can bring to mind during difficult moments.

### Building Long-Term Faith

Music creates emotional connections that help children develop positive feelings toward Scripture and worship. Instead of seeing Bible reading as a chore, children who grow up with songs like "{title}" often develop genuine excitement about God's Word.

## {self.section_variations.get_cta_header()}

{self.content_blocks.get_cta_block(title, "song")}

**Listen Now**: Experience "{title}" and let this Scripture song transform your family worship time.

<!-- featured-songs:start -->
## Listen to "{title}"
- [{title}]({webpage_url}) — {description}
<!-- featured-songs:end -->

<!-- resources:start -->
<div class="resources">
  <p><a href="{spotify_url}">Listen on Spotify</a></p>
  <p><small>Sing God's Word with your family.</small></p>
</div>
<!-- resources:end -->

**Want to bring this biblical foundation into your home or church? Listen now and let "{title}" help your family hide {scripture} in their hearts through worship!**
"""
        
        return content.strip()
    
    def generate_collection_page(self, keyword: str, songs: List[Dict], title: str) -> str:
        """Generate collection pages for grouped songs"""
        
        # Select featured songs (up to 6)
        featured_songs = songs[:6] if len(songs) > 6 else songs
        
        # Create varied contextual hook
        hook_generator = HookGenerator()
        if "christmas" in keyword.lower():
            hook = hook_generator.generate_hook(title, "christmas")
            scripture_focus = "Luke 2:14, Isaiah 9:6"
        elif "easter" in keyword.lower():
            hook = hook_generator.generate_hook(title, "easter")
            scripture_focus = "1 Corinthians 15:20, Romans 6:9"
        elif "action" in keyword.lower():
            hook = hook_generator.generate_hook(title, "action")
            scripture_focus = "Psalm 150:4, 2 Samuel 6:14"
        elif "worship" in keyword.lower():
            hook = hook_generator.generate_hook(title, "worship")
            scripture_focus = "Psalm 96:1, Colossians 3:16"
        elif "toddler" in keyword.lower():
            hook = hook_generator.generate_hook(title, "toddler")
            scripture_focus = "Psalm 8:2, Matthew 19:14"
        elif "preschool" in keyword.lower():
            hook = hook_generator.generate_hook(title, "preschool")
            scripture_focus = "Deuteronomy 6:7, Proverbs 22:6"
        else:
            hook = hook_generator.generate_hook(title, "general")
            scripture_focus = "Psalm 96:1, Colossians 3:16"
        
        # Generate featured songs section
        featured_section = ""
        if featured_songs:
            featured_section = "## Featured Scripture Songs\n\n"
            for song in featured_songs:
                featured_section += f"- [{song['title']}]({song.get('webpage_url', '#')}) — {song.get('description', '')[:100]}...\n"
        
        content = f"""# {title}

{hook}

## {self.section_variations.get_biblical_header()}

As {scripture_focus.split(',')[0]} reminds us, we're called to sing new songs to the Lord. When families sing God's Word together through {keyword}, we follow the pattern Scripture gives us for passing faith to the next generation.

These Scripture songs serve as powerful tools for family discipleship because they transform Bible verses into memorable melodies that children carry with them long after the music stops. Each song creates positive associations with God's Word while engaging children's natural love for rhythm and repetition.

## How These {keyword.title()} Help Children Learn Biblical Truth

### Building a Foundation of Faith Through Music

{self.content_blocks.get_learning_block(f"{keyword} songs")}

These {keyword} create opportunities for children to:
- **{self.content_blocks.content_variations.get_scripture_phrase().title()}** through repetitive, joyful singing
- **Develop a love for worship** that extends beyond Sunday morning
- **Connect biblical truth** to their daily experiences and emotions
- **Experience God's presence** through music and worship

### Age-Appropriate Spiritual Development

Scripture songs naturally meet children where they are developmentally while introducing them to deep spiritual truths. Simple, repetitive melodies help younger children participate fully, while older kids can explore the biblical meaning behind each song.

## {self.section_variations.get_usage_header()}

### Daily Worship Integration

Start your morning routine with one Scripture song to set a worship tone for the day. When children hear the same biblical truth set to music repeatedly, it naturally moves from their minds to their hearts.

### Creating Sacred Moments

Transform bedtime into sacred worship with gentle Scripture-based songs. Music has a unique ability to prepare hearts for prayer and worship, making it the perfect bridge between daily activities and spiritual connection.

### Church and Sunday School Applications

These songs work beautifully in both home and church settings, providing consistency between family worship and corporate worship experiences. Teachers love using Scripture songs to reinforce biblical truth in their lessons.

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

## {self.section_variations.get_cta_header()}

{self.content_blocks.get_cta_block(f"{keyword} songs", "collection")}

{featured_section}

**Want to bring this biblical foundation into your home or church? Listen now and let these Scripture songs transform your family worship time!**
"""
        
        return content.strip()
    
    def create_frontmatter(self, title: str, description: str, song_slugs: List[str] = None) -> Dict:
        """Create frontmatter for pages"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        frontmatter = {
            'date': today,
            'title': title,
            'description': description,
            'meta_description': f"{description[:150]}..." if len(description) > 150 else description,
            'tags': ['seeds-kids-worship', 'scripture-songs', 'family-worship', 'kids'],
            'layout': 'single'
        }
        
        if song_slugs:
            frontmatter['seed_songs'] = song_slugs
            
        return frontmatter
    
    def write_page(self, file_path: Path, frontmatter: Dict, content: str):
        """Write a page with frontmatter and content"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(frontmatter, f, default_flow_style=False)
                f.write("---\n")
                f.write(content)
                
            logger.info(f"Created: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return False
    
    def update_todo_progress(self, task_id: str, status: str):
        """Update todo list progress"""
        # This is a placeholder - the actual TodoWrite would be called from the main thread
        pass
    
    def create_individual_song_pages(self) -> int:
        """Create individual pages for each song"""
        count = 0
        
        for song in self.seeds_songs:
            slug = song.get('slug', '')
            title = song.get('title', '')
            description = song.get('description', '')
            
            if not slug or not title:
                continue
                
            # Create frontmatter
            frontmatter = self.create_frontmatter(
                title=f"{title} - Scripture Song",
                description=f"Learn {title}, a Scripture song from {song.get('scripture', '')} that helps children hide God's Word in their hearts.",
                song_slugs=[slug]
            )
            
            # Generate content
            content = self.generate_song_page(song)
            
            # Write file
            file_path = self.songs_dir / f"{slug}.md"
            if self.write_page(file_path, frontmatter, content):
                count += 1
        
        return count
    
    def create_collection_pages(self) -> int:
        """Create collection pages for song categories"""
        count = 0
        
        collections = [
            ("action-songs-for-kids", "Action Songs for Kids", "action_songs"),
            ("scripture-memory-songs", "Scripture Memory Songs", "scripture_memory"),
            ("worship-songs-for-children", "Worship Songs for Children", "worship"),
            ("praise-songs-for-kids", "Praise Songs for Kids", "praise"),
            ("courage-songs-for-children", "Courage Songs for Children", "courage"),
            ("forgiveness-songs-for-kids", "Forgiveness Songs for Kids", "forgiveness"),
            ("christmas-songs-for-kids", "Christmas Songs for Kids", "christmas"),
            ("easter-songs-for-children", "Easter Songs for Children", "easter"),
            ("toddler-worship-songs", "Toddler Worship Songs", "toddlers"),
            ("preschool-christian-songs", "Preschool Christian Songs", "preschool")
        ]
        
        for slug, title, category in collections:
            songs = self.songs_by_category.get(category, [])
            if not songs:
                songs = self.seeds_songs[:10]  # Use first 10 if category is empty
            
            # Create frontmatter
            song_slugs = [song.get('slug', '') for song in songs[:10]]
            frontmatter = self.create_frontmatter(
                title=title,
                description=f"Discover {title.lower()} that help children hide God's Word in their hearts through joyful worship.",
                song_slugs=song_slugs
            )
            
            # Generate content
            content = self.generate_collection_page(slug, songs, title)
            
            # Write file
            file_path = self.songs_dir / f"{slug}.md"
            if self.write_page(file_path, frontmatter, content):
                count += 1
        
        return count
    
    def update_existing_activities(self) -> int:
        """Update existing activity pages with Seeds song integration"""
        count = 0
        
        if not self.activities_dir.exists():
            logger.warning("Activities directory not found")
            return 0
            
        for activity_file in self.activities_dir.glob("*.md"):
            try:
                # Read existing file
                with open(activity_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        
                        # Add random Seeds songs to frontmatter
                        if 'seed_songs' not in frontmatter or not frontmatter['seed_songs']:
                            random_songs = random.sample(self.seeds_songs, min(3, len(self.seeds_songs)))
                            frontmatter['seed_songs'] = [song.get('slug', '') for song in random_songs]
                        
                        # Update descriptions to include Seeds branding
                        if 'description' in frontmatter:
                            desc = frontmatter['description']
                            if 'seeds' not in desc.lower():
                                frontmatter['description'] = f"{desc} Discover Scripture-based songs from Seeds Kids Worship."
                        
                        # Write updated file
                        new_content = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n" + parts[2]
                        
                        with open(activity_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        count += 1
                        logger.info(f"Updated: {activity_file}")
                        
            except Exception as e:
                logger.error(f"Failed to update {activity_file}: {e}")
        
        return count
    
    def rewrite_existing_blogs_with_claude(self, max_blogs: int = 50) -> int:
        """Rewrite existing blog posts using Claude API with full Seeds song integration"""
        count = 0
        
        # Get all existing blog files - prioritize activities directory
        all_blog_files = []
        
        # First, get activities files
        activities_files = list(self.content_dir.glob("activities/*.md"))
        all_blog_files.extend(activities_files)
        
        # Add songs files
        songs_files = list(self.content_dir.glob("songs/*.md"))
        all_blog_files.extend(songs_files)
        
        # Filter out already processed files
        unprocessed_files = []
        for blog_file in all_blog_files:
            relative_path = str(blog_file.relative_to(self.base_dir))
            if relative_path not in self.processed_files:
                unprocessed_files.append(blog_file)
        
        logger.info(f"Found {len(unprocessed_files)} unprocessed files out of {len(all_blog_files)} total files")
        
        # Limit to max_blogs for this run
        blog_files = unprocessed_files[:max_blogs]
        
        if not blog_files:
            logger.info("No unprocessed files found!")
            return 0
        
        logger.info(f"Processing {len(blog_files)} files in this batch")
        
        for blog_file in blog_files:
            try:
                logger.info(f"Rewriting {blog_file.name}...")
                
                # Determine relevant songs based on filename/content keywords
                filename_lower = blog_file.stem.lower()
                relevant_songs = []
                
                # Enhanced song selection with randomization and diversity
                primary_songs = []
                secondary_songs = []
                
                if "christmas" in filename_lower:
                    christmas_songs = list(self.songs_by_category.get('christmas', []))
                    random.shuffle(christmas_songs)
                    primary_songs.extend(christmas_songs[:random.randint(4, 7)])
                    
                    worship_songs = list(self.songs_by_category.get('worship', []))
                    random.shuffle(worship_songs)
                    secondary_songs.extend(worship_songs[:random.randint(2, 4)])
                    
                elif "easter" in filename_lower:
                    easter_songs = list(self.songs_by_category.get('easter', []))
                    random.shuffle(easter_songs)
                    primary_songs.extend(easter_songs[:random.randint(4, 6)])
                    
                    gospel_songs = list(self.songs_by_category.get('gospel_songs', []))
                    random.shuffle(gospel_songs)
                    secondary_songs.extend(gospel_songs[:random.randint(2, 4)])
                    
                elif "action" in filename_lower:
                    action_songs = list(self.songs_by_category.get('action_songs', []))
                    random.shuffle(action_songs)
                    primary_songs.extend(action_songs[:random.randint(3, 6)])
                    
                    praise_songs = list(self.songs_by_category.get('praise', []))
                    random.shuffle(praise_songs)
                    secondary_songs.extend(praise_songs[:random.randint(2, 3)])
                    
                elif "worship" in filename_lower:
                    worship_songs = list(self.songs_by_category.get('worship', []))
                    random.shuffle(worship_songs)
                    primary_songs.extend(worship_songs[:random.randint(4, 6)])
                    
                    praise_songs = list(self.songs_by_category.get('praise', []))
                    random.shuffle(praise_songs)
                    secondary_songs.extend(praise_songs[:random.randint(2, 4)])
                    
                elif "praise" in filename_lower:
                    praise_songs = list(self.songs_by_category.get('praise', []))
                    random.shuffle(praise_songs)
                    primary_songs.extend(praise_songs[:random.randint(4, 6)])
                    
                    worship_songs = list(self.songs_by_category.get('worship', []))
                    random.shuffle(worship_songs)
                    secondary_songs.extend(worship_songs[:random.randint(2, 4)])
                    
                elif "toddler" in filename_lower:
                    toddler_songs = list(self.songs_by_category.get('toddlers', []))
                    random.shuffle(toddler_songs)
                    primary_songs.extend(toddler_songs[:random.randint(3, 5)])
                    
                    lullaby_songs = list(self.songs_by_category.get('lullabies', []))
                    random.shuffle(lullaby_songs)
                    secondary_songs.extend(lullaby_songs[:random.randint(1, 3)])
                    
                elif "preschool" in filename_lower:
                    preschool_songs = list(self.songs_by_category.get('preschool', []))
                    random.shuffle(preschool_songs)
                    primary_songs.extend(preschool_songs[:random.randint(3, 5)])
                    
                    character_songs = list(self.songs_by_category.get('character_building', []))
                    random.shuffle(character_songs)
                    secondary_songs.extend(character_songs[:random.randint(2, 4)])
                    
                elif "sunday-school" in filename_lower:
                    ss_songs = list(self.songs_by_category.get('sunday_school', []))
                    random.shuffle(ss_songs)
                    primary_songs.extend(ss_songs[:random.randint(5, 8)])
                    
                    gospel_songs = list(self.songs_by_category.get('gospel_songs', []))
                    random.shuffle(gospel_songs)
                    secondary_songs.extend(gospel_songs[:random.randint(2, 4)])
                    
                elif "vbs" in filename_lower or "vacation" in filename_lower:
                    vbs_songs = list(self.songs_by_category.get('vbs_songs', []))
                    random.shuffle(vbs_songs)
                    primary_songs.extend(vbs_songs[:random.randint(4, 6)])
                    
                    action_songs = list(self.songs_by_category.get('action_songs', []))
                    random.shuffle(action_songs)
                    secondary_songs.extend(action_songs[:random.randint(2, 4)])
                    
                elif "bible" in filename_lower:
                    bible_songs = list(self.songs_by_category.get('bible_stories', []))
                    random.shuffle(bible_songs)
                    primary_songs.extend(bible_songs[:random.randint(3, 5)])
                    
                    memory_songs = list(self.songs_by_category.get('scripture_memory', []))
                    random.shuffle(memory_songs)
                    secondary_songs.extend(memory_songs[:random.randint(2, 4)])
                    
                elif "lullaby" in filename_lower:
                    lullaby_songs = list(self.songs_by_category.get('lullabies', []))
                    random.shuffle(lullaby_songs)
                    primary_songs.extend(lullaby_songs[:random.randint(3, 5)])
                    
                    worship_songs = list(self.songs_by_category.get('worship', []))
                    random.shuffle(worship_songs)
                    secondary_songs.extend(worship_songs[:random.randint(1, 3)])
                    
                else:
                    # Use a diverse mix of songs for general topics with randomization
                    categories_to_mix = ['sunday_school', 'worship', 'character_building', 'gospel_songs', 'faith_building', 'praise']
                    random.shuffle(categories_to_mix)
                    
                    for i, category in enumerate(categories_to_mix[:4]):  # Use 4 random categories
                        category_songs = list(self.songs_by_category.get(category, []))
                        if category_songs:
                            random.shuffle(category_songs)
                            count = random.randint(1, 3) if i > 0 else random.randint(2, 4)  # First category gets more songs
                            primary_songs.extend(category_songs[:count])
                
                # Combine primary and secondary songs
                relevant_songs = primary_songs + secondary_songs
                
                # Remove duplicates while preserving order
                seen = set()
                relevant_songs = [song for song in relevant_songs if not (song.get('slug', '') in seen or seen.add(song.get('slug', '')))]
                
                # Add random songs if we don't have enough variety
                if len(relevant_songs) < 8:
                    remaining_songs = [s for s in self.seeds_songs if s not in relevant_songs]
                    random.shuffle(remaining_songs)
                    relevant_songs.extend(remaining_songs[:random.randint(2, 4)])
                
                # Final shuffle for more variety
                random.shuffle(relevant_songs)
                
                # Create prompt and generate content with word count validation
                prompt = self.create_blog_prompt(blog_file, relevant_songs)
                new_content = self.generate_content_with_word_limit_validation(prompt, blog_file.name)
                
                if new_content:
                    # Read existing frontmatter
                    existing_frontmatter = {}
                    try:
                        with open(blog_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if content.startswith('---'):
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                existing_frontmatter = yaml.safe_load(parts[1]) or {}
                    except:
                        pass
                    
                    # Update frontmatter with variable number of Seeds songs (3-8)
                    num_songs = random.randint(3, 8)
                    song_slugs = [song.get('slug', '') for song in relevant_songs[:num_songs] if song.get('slug')]
                    if song_slugs:
                        existing_frontmatter['seed_songs'] = song_slugs
                        logger.info(f"Selected {len(song_slugs)} Seeds songs for {blog_file.name}: {song_slugs[:3]}..." + ("" if len(song_slugs) <= 3 else f" (and {len(song_slugs)-3} more)"))
                    
                    # Create compelling meta description based on content and title
                    meta_description = self.generate_compelling_meta_description(blog_file.stem, new_content)
                    existing_frontmatter['description'] = meta_description
                    existing_frontmatter['meta_description'] = meta_description
                    
                    # Add schema markup to content
                    new_content_with_schema = self.add_schema_markup(blog_file.stem, new_content, relevant_songs)
                    
                    # Write updated file
                    self.write_page(blog_file, existing_frontmatter, new_content_with_schema)
                    
                    # Mark file as processed
                    self.mark_file_processed(blog_file)
                    
                    count += 1
                    logger.info(f"Successfully rewrote {blog_file.name}")
                else:
                    logger.error(f"Failed to generate content for {blog_file.name}")
                    
            except Exception as e:
                logger.error(f"Error rewriting {blog_file}: {e}")
        
        return count
    
    def run(self, max_blogs: int = None):
        """Main execution method"""
        logger.info("Starting comprehensive Seeds content rewriting with Claude API...")
        logger.info(f"Seeds songs loaded: {len(self.seeds_songs)}")
        
        results = {
            'rewritten_blogs': 0,
            'individual_songs': 0,
            'collection_pages': 0,
            'updated_activities': 0
        }
        
        # Rewrite existing blogs with Claude API (priority task)
        if max_blogs:
            logger.info(f"Rewriting {max_blogs} existing blogs with Claude API...")
            results['rewritten_blogs'] = self.rewrite_existing_blogs_with_claude(max_blogs)
        else:
            # Create individual song pages
            logger.info("Creating individual song pages...")
            results['individual_songs'] = self.create_individual_song_pages()
            
            # Create collection pages
            logger.info("Creating collection pages...")
            results['collection_pages'] = self.create_collection_pages()
            
            # Update existing activities
            logger.info("Updating existing activity pages...")
            results['updated_activities'] = self.update_existing_activities()
        
        logger.info("Content rewriting complete!")
        if max_blogs:
            logger.info(f"Blogs rewritten with Claude API: {results['rewritten_blogs']}")
        else:
            logger.info(f"Individual song pages: {results['individual_songs']}")
            logger.info(f"Collection pages: {results['collection_pages']}")
            logger.info(f"Updated activities: {results['updated_activities']}")
        
        return results

if __name__ == "__main__":
    rewriter = ComprehensiveSeedsRewriter()
    # Rewrite 50 blogs with enhanced song variation and word count controls
    rewriter.run(max_blogs=50)