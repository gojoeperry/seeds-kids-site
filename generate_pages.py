#!/usr/bin/env python3
"""
Script to generate SEO pages for kids scripture songs from metadata.
"""

import json
import os
import time
from pathlib import Path
from jinja2 import Template
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_metadata():
    """Load page metadata from url_metadata.json and extract keywords from titles"""
    with open('url_metadata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract keywords from title field
    for item in data:
        # Extract keyword from title by removing "| Seeds Kids Worship" suffix
        if 'title' in item:
            keyword = item['title'].split(' | ')[0]
            item['keyword'] = keyword
    
    return data


def load_template():
    """Load the page template"""
    with open('page_template.md', 'r', encoding='utf-8') as f:
        return Template(f.read())


def call_claude_api(prompt):
    url = "https://api.anthropic.com/v1/messages"
    api_key = os.getenv("CLAUDE_API_KEY")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1200,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e.response.text}")
        return "Content generation failed."
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return "Content generation failed."


def generate_placeholder_content(keyword):
    """Generate placeholder content when API is not available"""
    return f"""# {keyword.title()} - Bible Songs for Kids | Seeds Kids Worship

## Introduction

Welcome to our collection of {keyword}! At Seeds Kids Worship, we believe that music is one of the most powerful ways to help children connect with God's love and learn His word. Whether you're a parent looking for meaningful songs for family worship time, a Sunday school teacher planning your next lesson, or a pastor seeking engaging content for children's ministry, our {keyword} collection provides the perfect blend of biblical truth and joyful melodies.

## Devotional: Growing in Faith Through Song

*"Let the message of Christ dwell among you richly as you teach and admonish one another with all wisdom through psalms, hymns, and songs from the Spirit, singing to God with gratitude in your hearts."* - Colossians 3:16

Music has always been central to worship and spiritual formation. When children sing {keyword}, they're not just learning melodies - they're hiding God's word in their hearts. These songs create lasting memories that will serve as spiritual anchors throughout their lives, reminding them of God's faithfulness, love, and promises.

## How This Song Helps Kids Learn Scripture

{keyword.title()} serves as a powerful educational tool that makes Bible learning engaging and memorable. Through repetition, rhythm, and melody, children naturally absorb biblical concepts and verses. The combination of music and movement helps accommodate different learning styles, ensuring that every child can participate and grow in their understanding of God's word.

## Scripture Reference

> "Sing to the LORD a new song; sing to the LORD, all the earth. Sing to the LORD, praise his name; proclaim his salvation day after day." - Psalm 96:1-2

## Call to Action

Ready to explore more inspiring songs for your children? Visit our complete collection at Seeds Kids Worship and discover hundreds of Bible-based songs that will nurture your child's faith journey. From worship anthems to scripture memory songs, we have everything you need to make God's word come alive through music.

## Frequently Asked Questions

**What age group is {keyword} appropriate for?**
{keyword.title()} is designed for children ages 3-12, with simple lyrics and engaging melodies that capture young attention while teaching important biblical truths.

**How can I use {keyword} in our family devotions?**
Incorporate {keyword} into your daily or weekly family worship time. Start with singing together, then discuss the biblical concepts presented in the lyrics, and end with prayer.

**Are there resources available to help teach {keyword}?**
Yes! Our website provides lyrics, sheet music, and teaching guides to help parents, teachers, and ministry leaders effectively use {keyword} in their educational and worship settings."""


def generate_claude_content(keyword):
    """
    Generate content using Claude API.
    Returns structured content ready for template injection.
    """
    # Claude API prompt template
    prompt_template = """You are a Christian educator and SEO content writer. Please generate a full 500-word Markdown page for the topic: "{keyword}".

Include:

- A warm, engaging introduction for Christian parents, teachers, or pastors
- A short devotional explaining a relevant Bible verse or theme
- A section on how this song helps kids learn Scripture
- A scripture reference block
- A call to action to explore more songs
- 3 FAQs with answers
- SEO title (max 60 characters)
- Meta description (max 160 characters)

Use clear markdown headings for each section."""

    prompt = prompt_template.format(keyword=keyword)
    
    # Get the full markdown content from Claude
    print(f"    [API Call] Generating content for: {keyword}")
    full_markdown = call_claude_api(prompt)
    
    if full_markdown is None:
        print(f"    Falling back to placeholder content for: {keyword}")
        # Return placeholder structured content
        return {
            'intro_paragraph': f"Welcome to our collection of {keyword}! At Seeds Kids Worship, we believe that music is one of the most powerful ways to help children connect with God's love and learn His word.",
            'scripture_ref': "Let the message of Christ dwell among you richly as you teach and admonish one another with all wisdom through psalms, hymns, and songs from the Spirit, singing to God with gratitude in your hearts. - Colossians 3:16",
            'lyrics_text': f"Explore our collection of {keyword} and discover the perfect songs for your children's spiritual growth.",
            'devotional_paragraph': f"Teaching children through {keyword} builds a strong foundation of faith and biblical understanding.",
            'faqs': [
                {"question": f"What age group is {keyword} appropriate for?", "answer": f"{keyword.title()} is designed for children ages 3-12, with simple lyrics and engaging melodies that capture young attention while teaching important biblical truths."},
                {"question": f"How can I use {keyword} in our family devotions?", "answer": f"Incorporate {keyword} into your daily or weekly family worship time. Start with singing together, then discuss the biblical concepts presented in the lyrics, and end with prayer."},
                {"question": f"Are there resources available to help teach {keyword}?", "answer": f"Yes! Our website provides lyrics, sheet music, and teaching guides to help parents, teachers, and ministry leaders effectively use {keyword} in their educational and worship settings."}
            ]
        }
    
    # For now, parse the markdown response and extract components
    # In a more sophisticated implementation, you might ask Claude to return JSON
    lines = full_markdown.split('\n')
    
    # Extract different sections
    intro_paragraph = ""
    scripture_ref = ""
    lyrics_text = f"Explore our collection of {keyword} and discover the perfect songs for your children's spiritual growth."
    devotional_paragraph = ""
    faqs = []
    
    current_section = ""
    current_faq_question = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith('## Introduction'):
            current_section = "intro"
        elif line.startswith('## Devotional'):
            current_section = "devotional"
        elif line.startswith('## Scripture Reference') or line.startswith('> '):
            current_section = "scripture"
            if line.startswith('> '):
                scripture_ref = line[2:]  # Remove "> " prefix
        elif line.startswith('## Frequently Asked Questions'):
            current_section = "faqs"
        elif line.startswith('**') and line.endswith('**') and current_section == "faqs":
            current_faq_question = line[2:-2]  # Remove ** markers
        elif current_faq_question and line and current_section == "faqs":
            faqs.append({
                "question": current_faq_question,
                "answer": line
            })
            current_faq_question = ""
        elif current_section == "intro" and line and not line.startswith('#'):
            intro_paragraph += line + " "
        elif current_section == "devotional" and line and not line.startswith('#') and not line.startswith('*'):
            devotional_paragraph += line + " "
    
    # Ensure we have at least 3 FAQs
    while len(faqs) < 3:
        faqs.append({
            "question": f"How can {keyword} benefit my child's spiritual growth?",
            "answer": f"{keyword.title()} helps children develop a love for worship while learning biblical truths through engaging melodies and meaningful lyrics."
        })
    
    return {
        'intro_paragraph': intro_paragraph.strip(),
        'scripture_ref': scripture_ref or f"Scripture references included in {keyword} help children learn God's word.",
        'lyrics_text': lyrics_text,
        'devotional_paragraph': devotional_paragraph.strip() or f"Teaching children through {keyword} builds a strong foundation of faith and biblical understanding.",
        'faqs': faqs[:3]  # Limit to 3 FAQs
    }


def create_output_directory(url):
    """Create the output directory structure based on URL"""
    # Remove leading slash and get directory path
    clean_url = url.lstrip('/')
    file_path = Path('content') / f"{clean_url}.md"
    
    # Create directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    return file_path


def generate_pages():
    """Main function to generate all pages"""
    print("Loading metadata and template...")
    
    # Load data
    metadata_list = load_metadata()
    template = load_template()
    
    # Create content directory
    Path('content').mkdir(exist_ok=True)
    
    generated_count = 0
    
    print(f"Generating {len(metadata_list)} pages...")
    
    for item in metadata_list:
        print(f"  Processing: {item['keyword']}")
        
        # Generate Claude content
        claude_content = generate_claude_content(item['keyword'])
        
        # Combine all template variables
        template_vars = {
            **item,  # url, title, h1, meta_description, keyword
            **claude_content,  # intro_paragraph, scripture_ref, lyrics_text, devotional_paragraph, faqs
            'video_embed_code': None  # No video embed by default
        }
        
        # Render template
        rendered_content = template.render(**template_vars)
        
        # Create output path and save file
        output_path = create_output_directory(item['url'])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)
        
        generated_count += 1
        print(f"    Saved: {output_path}")
        
        # Add 2-second delay between API calls to avoid rate limits
        if generated_count < len(metadata_list):
            print(f"    Waiting 2 seconds before next API call...")
            time.sleep(2)
    
    print(f"\nSuccessfully generated {generated_count} pages in the 'content/' folder")
    print(f"Files saved in: {Path('content').absolute()}")


if __name__ == "__main__":
    generate_pages()