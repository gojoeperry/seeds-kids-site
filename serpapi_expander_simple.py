#!/usr/bin/env python3
"""
SerpAPI Keyword Expander for Seeds Kids Worship
Generates 300+ scalable long-tail keywords using SerpAPI data
"""

import os
import json
import csv
import time
import requests
from slugify import slugify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SerpAPIExpander:
    def __init__(self):
        self.api_key = os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable not found")
        self.base_url = "https://serpapi.com/search"
        
    def load_seeds(self):
        """Load seed keywords"""
        with open('seed_keywords.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def get_autocomplete(self, query):
        """Get autocomplete suggestions"""
        params = {
            'engine': 'google_autocomplete',
            'q': query,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            suggestions = []
            if 'suggestions' in data:
                for suggestion in data['suggestions']:
                    if 'value' in suggestion:
                        suggestions.append(suggestion['value'])
            
            print(f"   Autocomplete: {len(suggestions)} suggestions for '{query}'")
            return suggestions
            
        except Exception as e:
            print(f"   Error with autocomplete for '{query}': {str(e)}")
            return []
    
    def get_people_also_ask(self, query):
        """Get People Also Ask questions"""
        params = {
            'engine': 'google',
            'q': query,
            'api_key': self.api_key,
            'num': 10
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            questions = []
            if 'related_questions' in data:
                for q in data['related_questions']:
                    questions.append({
                        'question': q.get('question', ''),
                        'snippet': q.get('snippet', ''),
                        'title': q.get('title', ''),
                        'link': q.get('link', '')
                    })
            
            print(f"   People Also Ask: {len(questions)} questions for '{query}'")
            return questions
            
        except Exception as e:
            print(f"   Error with PAA for '{query}': {str(e)}")
            return []
    
    def get_related_searches(self, query):
        """Get related searches"""
        params = {
            'engine': 'google',
            'q': query,
            'api_key': self.api_key,
            'num': 10
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            related = []
            if 'related_searches' in data:
                for search in data['related_searches']:
                    if 'query' in search:
                        related.append(search['query'])
            
            print(f"   Related searches: {len(related)} for '{query}'")
            return related
            
        except Exception as e:
            print(f"   Error with related searches for '{query}': {str(e)}")
            return []
    
    def generate_variations(self, seed):
        """Generate manual variations"""
        variations = []
        base = seed.lower()
        
        # Age groups
        ages = ["for toddlers", "for preschoolers", "for kids", "for children", "for babies"]
        
        # Formats
        formats = ["youtube", "videos", "cd", "app", "playlist", "with lyrics"]
        
        # Contexts
        contexts = ["for church", "for sunday school", "for home", "for worship"]
        
        # Actions
        actions = ["with motions", "with actions", "interactive"]
        
        # Themes
        themes = ["christmas", "easter", "praise", "worship"]
        
        # Qualities
        qualities = ["easy", "simple", "fun", "peaceful"]
        
        for age in ages:
            variations.append(f"{base} {age}")
        
        for fmt in formats:
            variations.append(f"{base} {fmt}")
            
        for context in contexts:
            variations.append(f"{base} {context}")
            
        for action in actions:
            variations.append(f"{base} {action}")
            
        for theme in themes:
            variations.append(f"{theme} {base}")
            
        for quality in qualities:
            variations.append(f"{quality} {base}")
        
        return variations
    
    def determine_cluster(self, keyword):
        """Determine semantic cluster"""
        k = keyword.lower()
        
        if any(x in k for x in ['christmas', 'nativity']):
            return 'christmas'
        elif any(x in k for x in ['easter', 'resurrection']):
            return 'easter'
        elif any(x in k for x in ['scripture', 'bible verse']):
            return 'scripture_memory'
        elif any(x in k for x in ['worship', 'praise']):
            return 'worship'
        elif any(x in k for x in ['sunday school']):
            return 'sunday_school'
        elif any(x in k for x in ['vbs', 'vacation bible']):
            return 'vbs'
        elif any(x in k for x in ['preschool']):
            return 'preschool'
        elif any(x in k for x in ['toddler']):
            return 'toddler'
        elif any(x in k for x in ['choir']):
            return 'choir'
        elif any(x in k for x in ['lullaby', 'bedtime']):
            return 'lullabies'
        elif any(x in k for x in ['app', 'download']):
            return 'apps'
        else:
            return 'general'
    
    def create_url(self, keyword, cluster):
        """Create URL slug"""
        slug = slugify(keyword, max_length=60)
        
        if cluster in ['christmas', 'easter', 'sunday_school', 'vbs']:
            category = 'activities'
        else:
            category = 'songs'
            
        return f"/{category}/{slug}"
    
    def process_seed(self, seed):
        """Process single seed keyword"""
        print(f"\nProcessing: '{seed}'")
        
        all_keywords = set()
        
        # Get SerpAPI data
        autocomplete = self.get_autocomplete(seed)
        time.sleep(1)
        
        paa_data = self.get_people_also_ask(seed)
        time.sleep(1)
        
        related = self.get_related_searches(seed)
        time.sleep(1)
        
        # Get manual variations
        variations = self.generate_variations(seed)
        
        # Combine all sources
        all_keywords.update(autocomplete)
        all_keywords.update(related)
        all_keywords.update(variations)
        
        # Extract from PAA questions
        for paa in paa_data:
            question = paa['question'].lower()
            if 'kids' in question or 'children' in question:
                all_keywords.add(question)
        
        # Process keywords
        results = []
        for keyword in all_keywords:
            keyword = keyword.strip()
            if len(keyword) < 10 or len(keyword) > 100:
                continue
                
            cluster = self.determine_cluster(keyword)
            url = self.create_url(keyword, cluster)
            
            data = {
                'keyword': keyword,
                'seed': seed,
                'cluster': cluster,
                'url': url,
                'title': f"{keyword.title()} | Seeds Kids Worship",
                'meta_description': f"Explore '{keyword}' with lyrics, devotional, and video content for children.",
                'h1': keyword.title()
            }
            results.append(data)
        
        print(f"   Generated: {len(results)} variations")
        return results
    
    def run(self):
        """Main execution"""
        print("=" * 50)
        print("SerpAPI Keyword Expander")
        print("=" * 50)
        
        seeds = self.load_seeds()
        print(f"Loaded {len(seeds)} seed keywords")
        
        all_data = []
        for i, seed in enumerate(seeds, 1):
            print(f"\nProgress: {i}/{len(seeds)}")
            
            try:
                results = self.process_seed(seed)
                all_data.extend(results)
                
                if i < len(seeds):
                    print("   Waiting 3 seconds...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"   Error processing '{seed}': {str(e)}")
                continue
        
        # Remove duplicates
        seen = set()
        unique_data = []
        for item in all_data:
            key = item['keyword'].lower()
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        print(f"\nSummary:")
        print(f"  Seeds processed: {len(seeds)}")
        print(f"  Total generated: {len(all_data)}")
        print(f"  Unique keywords: {len(unique_data)}")
        
        # Save results
        self.save_results(unique_data)
        
    def save_results(self, data):
        """Save all output files"""
        # Raw JSON
        with open('all_keywords_raw.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # CSV
        headers = ['keyword', 'cluster', 'url', 'title', 'meta_description', 'h1', 'seed']
        with open('keyword_clusters.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        # URL metadata
        url_data = []
        for item in data:
            url_item = {
                'url': item['url'],
                'keyword': item['keyword'],
                'title': item['title'],
                'h1': item['h1'],
                'meta_description': item['meta_description'],
                'cluster': item['cluster']
            }
            url_data.append(url_item)
        
        with open('url_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(url_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nFiles saved:")
        print(f"  all_keywords_raw.json ({len(data)} keywords)")
        print(f"  keyword_clusters.csv ({len(data)} rows)")
        print(f"  url_metadata.json ({len(url_data)} URLs)")

def main():
    try:
        expander = SerpAPIExpander()
        expander.run()
        print("\nSuccess! Keywords generated using SerpAPI data.")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nTo fix:")
        print("1. Get SerpAPI key from https://serpapi.com/")
        print("2. Set environment variable: set SERPAPI_API_KEY=your_key")
        print("3. Re-run this script")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()