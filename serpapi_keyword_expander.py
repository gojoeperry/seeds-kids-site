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
from typing import List, Dict, Set
from urllib.parse import quote_plus
from slugify import slugify
import re

class SerpAPIKeywordExpander:
    def __init__(self, api_key: str = None):
        """Initialize with SerpAPI key"""
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is required. Set environment variable or pass as parameter.")
        
        self.base_url = "https://serpapi.com/search"
        self.all_keywords = set()
        self.keyword_data = []
        
    def load_seed_keywords(self, filename: str = "seed_keywords.txt") -> List[str]:
        """Load seed keywords from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                seeds = [line.strip() for line in f if line.strip()]
            print(f"[OK] Loaded {len(seeds)} seed keywords from {filename}")
            return seeds
        except FileNotFoundError:
            print(f"[ERROR] {filename} not found")
            return []
    
    def get_autocomplete_suggestions(self, query: str) -> List[str]:
        """Get Google Autocomplete suggestions via SerpAPI"""
        params = {
            'engine': 'google_autocomplete',
            'q': query,
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            suggestions = []
            if 'suggestions' in data:
                for suggestion in data['suggestions']:
                    if 'value' in suggestion:
                        suggestions.append(suggestion['value'])
            
            print(f"   📝 Autocomplete: {len(suggestions)} suggestions for '{query}'")
            return suggestions
            
        except Exception as e:
            print(f"   ❌ Autocomplete error for '{query}': {e}")
            return []
    
    def get_people_also_ask(self, query: str) -> List[Dict]:
        """Get People Also Ask questions via SerpAPI"""
        params = {
            'engine': 'google',
            'q': query,
            'api_key': self.api_key,
            'num': 10
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            paa_questions = []
            if 'related_questions' in data:
                for question in data['related_questions']:
                    paa_data = {
                        'question': question.get('question', ''),
                        'snippet': question.get('snippet', ''),
                        'title': question.get('title', ''),
                        'link': question.get('link', '')
                    }
                    paa_questions.append(paa_data)
            
            print(f"   🤔 People Also Ask: {len(paa_questions)} questions for '{query}'")
            return paa_questions
            
        except Exception as e:
            print(f"   ❌ People Also Ask error for '{query}': {e}")
            return []
    
    def get_related_searches(self, query: str) -> List[str]:
        """Get related searches via SerpAPI"""
        params = {
            'engine': 'google',
            'q': query,
            'api_key': self.api_key,
            'num': 10
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            related = []
            if 'related_searches' in data:
                for search in data['related_searches']:
                    if 'query' in search:
                        related.append(search['query'])
            
            print(f"   🔗 Related searches: {len(related)} for '{query}'")
            return related
            
        except Exception as e:
            print(f"   ❌ Related searches error for '{query}': {e}")
            return []
    
    def generate_manual_variations(self, seed: str) -> List[str]:
        """Generate manual keyword variations"""
        variations = []
        base = seed.lower()
        
        # Age group variations
        age_groups = ["for toddlers", "for preschoolers", "for kids", "for children", 
                     "for babies", "for elementary", "for young children"]
        
        # Format variations  
        formats = ["youtube", "videos", "playlist", "cd", "app", "free download", 
                  "with lyrics", "instrumental", "acapella"]
        
        # Context variations
        contexts = ["for church", "for sunday school", "for home", "for car", 
                   "for bedtime", "for worship", "for vbs"]
        
        # Action variations
        actions = ["with motions", "with actions", "with dancing", "interactive", 
                  "with clapping", "with sign language"]
        
        # Theme variations
        themes = ["christmas", "easter", "thanksgiving", "creation", "jesus", 
                 "bible stories", "praise", "worship"]
        
        # Quality variations
        qualities = ["easy", "simple", "fun", "energetic", "peaceful", "joyful", 
                    "uplifting", "contemporary", "traditional"]
        
        # Generate combinations
        for age in age_groups:
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
    
    def determine_cluster(self, keyword: str) -> str:
        """Determine semantic cluster for keyword"""
        keyword_lower = keyword.lower()
        
        if any(x in keyword_lower for x in ['app', 'download', 'android', 'ios', 'mobile']):
            return 'apps'
        elif any(x in keyword_lower for x in ['christmas', 'nativity', 'xmas']):
            return 'christmas'
        elif any(x in keyword_lower for x in ['easter', 'resurrection', 'palm sunday']):
            return 'easter'
        elif any(x in keyword_lower for x in ['scripture', 'bible verse', 'memory verse']):
            return 'scripture_memory'
        elif any(x in keyword_lower for x in ['worship', 'praise']):
            return 'worship'
        elif any(x in keyword_lower for x in ['sunday school', 'sunday morning']):
            return 'sunday_school'
        elif any(x in keyword_lower for x in ['vbs', 'vacation bible school']):
            return 'vbs'
        elif any(x in keyword_lower for x in ['preschool', 'pre-k']):
            return 'preschool'
        elif any(x in keyword_lower for x in ['toddler', '2 year', '3 year']):
            return 'toddler'
        elif any(x in keyword_lower for x in ['choir', 'harmony', 'anthem']):
            return 'choir'
        elif any(x in keyword_lower for x in ['lullaby', 'bedtime', 'sleep', 'naptime']):
            return 'lullabies'
        elif any(x in keyword_lower for x in ['bible story', 'noah', 'david', 'jonah', 'moses']):
            return 'bible_stories'
        elif any(x in keyword_lower for x in ['motion', 'action', 'movement', 'dance', 'clap']):
            return 'motions'
        else:
            return 'general'
    
    def create_url_slug(self, keyword: str, cluster: str) -> str:
        """Create SEO-friendly URL slug"""
        slug = slugify(keyword, max_length=60)
        
        # Determine URL category based on cluster
        if cluster in ['christmas', 'easter', 'sunday_school', 'vbs']:
            category = 'activities'
        else:
            category = 'songs'
            
        return f"/{category}/{slug}"
    
    def determine_search_intent(self, keyword: str) -> str:
        """Determine search intent"""
        keyword_lower = keyword.lower()
        
        if any(x in keyword_lower for x in ['buy', 'download', 'cd', 'app', 'store', 'purchase']):
            return 'commercial'
        elif any(x in keyword_lower for x in ['how to', 'what is', 'why', 'review', 'best']):
            return 'informational'
        elif any(x in keyword_lower for x in ['youtube', 'watch', 'video', 'listen']):
            return 'navigational'
        else:
            return 'informational'
    
    def estimate_difficulty(self, keyword: str) -> str:
        """Estimate SEO difficulty"""
        word_count = len(keyword.split())
        
        if word_count >= 5:
            return 'low'
        elif word_count >= 3:
            return 'medium'
        else:
            return 'high'
    
    def process_seed_keyword(self, seed: str) -> List[Dict]:
        """Process a single seed keyword through all SerpAPI endpoints"""
        print(f"\n🔍 Processing seed: '{seed}'")
        
        keyword_variations = []
        processed_keywords = set()
        
        # Get autocomplete suggestions
        autocomplete = self.get_autocomplete_suggestions(seed)
        time.sleep(1)  # Rate limiting
        
        # Get People Also Ask
        paa_data = self.get_people_also_ask(seed)
        time.sleep(1)  # Rate limiting
        
        # Get related searches
        related_searches = self.get_related_searches(seed)
        time.sleep(1)  # Rate limiting
        
        # Get manual variations
        manual_variations = self.generate_manual_variations(seed)
        
        # Combine all keyword sources
        all_keywords = set()
        all_keywords.update(autocomplete)
        all_keywords.update(related_searches)
        all_keywords.update(manual_variations)
        
        # Extract keywords from PAA questions
        for paa in paa_data:
            question = paa['question'].lower()
            # Extract keyword-like phrases from questions
            if 'kids' in question or 'children' in question:
                all_keywords.add(question)
        
        # Process each keyword
        for keyword in all_keywords:
            keyword = keyword.strip()
            if len(keyword) < 10 or len(keyword) > 100:  # Filter length
                continue
                
            if keyword.lower() in processed_keywords:
                continue
                
            processed_keywords.add(keyword.lower())
            
            cluster = self.determine_cluster(keyword)
            url = self.create_url_slug(keyword, cluster)
            search_intent = self.determine_search_intent(keyword)
            difficulty = self.estimate_difficulty(keyword)
            
            # Create comprehensive metadata
            keyword_data = {
                'keyword': keyword,
                'seed': seed,
                'cluster': cluster,
                'url': url,
                'search_intent': search_intent,
                'difficulty': difficulty,
                'title': f"{keyword.title()} | Seeds Kids Worship",
                'meta_description': f"Explore '{keyword}' with lyrics, devotional, and video content for children.",
                'h1': keyword.title(),
                'source': 'mixed'  # combination of sources
            }
            
            keyword_variations.append(keyword_data)
        
        print(f"   ✅ Generated {len(keyword_variations)} keyword variations")
        return keyword_variations
    
    def expand_keywords(self) -> Dict:
        """Main method to expand all seed keywords"""
        print("🚀 Starting SerpAPI Keyword Expansion...")
        
        # Load seed keywords
        seeds = self.load_seed_keywords()
        if not seeds:
            print("❌ No seed keywords found. Exiting.")
            return {}
        
        all_keyword_data = []
        
        # Process each seed
        for i, seed in enumerate(seeds, 1):
            print(f"\n📊 Progress: {i}/{len(seeds)}")
            
            try:
                keyword_variations = self.process_seed_keyword(seed)
                all_keyword_data.extend(keyword_variations)
                
                # Rate limiting between seeds
                if i < len(seeds):
                    print("   ⏱️  Waiting 3 seconds...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"   ❌ Error processing '{seed}': {e}")
                continue
        
        # Remove duplicates based on keyword
        seen_keywords = set()
        unique_data = []
        
        for item in all_keyword_data:
            keyword_lower = item['keyword'].lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                unique_data.append(item)
        
        print(f"\n📈 Summary:")
        print(f"   • Total seed keywords: {len(seeds)}")
        print(f"   • Total variations generated: {len(all_keyword_data)}")
        print(f"   • Unique keywords after deduplication: {len(unique_data)}")
        
        return {
            'seeds_processed': len(seeds),
            'total_generated': len(all_keyword_data),
            'unique_keywords': len(unique_data),
            'data': unique_data
        }
    
    def save_results(self, results: Dict) -> None:
        """Save results to multiple output formats"""
        data = results['data']
        
        # Save raw JSON
        with open('all_keywords_raw.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save CSV
        csv_headers = ['keyword', 'cluster', 'url', 'search_intent', 'difficulty', 
                      'title', 'meta_description', 'h1', 'seed', 'source']
        
        with open('keyword_clusters.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(data)
        
        # Save URL metadata for content generation
        url_metadata = []
        for item in data:
            metadata = {
                'url': item['url'],
                'keyword': item['keyword'],
                'title': item['title'],
                'h1': item['h1'],
                'meta_description': item['meta_description'],
                'cluster': item['cluster']
            }
            url_metadata.append(metadata)
        
        with open('url_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(url_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved:")
        print(f"   • all_keywords_raw.json ({len(data)} keywords)")
        print(f"   • keyword_clusters.csv ({len(data)} rows)")
        print(f"   • url_metadata.json ({len(url_metadata)} URLs)")
    
    def run(self) -> None:
        """Run the complete keyword expansion process"""
        try:
            results = self.expand_keywords()
            if results and results['data']:
                self.save_results(results)
                print(f"\n🎉 Success! Generated {results['unique_keywords']} unique keywords using SerpAPI")
            else:
                print("❌ No keywords were generated")
                
        except Exception as e:
            print(f"❌ Fatal error: {e}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("SerpAPI Keyword Expander for Seeds Kids Worship")
    print("=" * 60)
    
    try:
        # Initialize expander
        expander = SerpAPIKeywordExpander()
        
        # Run expansion process
        expander.run()
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 To fix this:")
        print("   1. Get SerpAPI key from https://serpapi.com/")
        print("   2. Set environment variable: set SERPAPI_API_KEY=your_key_here")
        print("   3. Re-run this script")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()