import csv
import json
import re
from slugify import slugify

def infer_category(topic):
    """Infer URL category based on topic keywords."""
    topic_lower = topic.lower()
    
    # Bible verses/lyrics category
    if any(word in topic_lower for word in ['lyrics', 'verse', 'bible', 'scripture']):
        if any(ref in topic_lower for ref in ['john', 'matthew', 'psalm', 'genesis', 'exodus']):
            return '/bible-verses/'
    
    # Holiday activities category
    if any(holiday in topic_lower for holiday in ['christmas', 'easter']):
        return '/activities/'
    
    # Default to songs category
    return '/songs/'

def generate_title(topic):
    """Generate SEO-friendly title with brand suffix."""
    title = f"{topic} | Seeds Kids Worship"
    
    # Truncate if too long (keeping brand intact)
    if len(title) > 60:
        max_topic_length = 60 - len(" | Seeds Kids Worship")
        truncated_topic = topic[:max_topic_length].strip()
        title = f"{truncated_topic} | Seeds Kids Worship"
    
    return title

def generate_meta_description(topic):
    """Generate meta description under 160 characters."""
    base_desc = f"Explore '{topic}' with lyrics, devotional, and video for children."
    
    if len(base_desc) <= 160:
        return base_desc
    
    # Truncate topic if description is too long
    max_topic_length = 160 - len("Explore '' with lyrics, devotional, and video for children.")
    truncated_topic = topic[:max_topic_length].strip()
    return f"Explore '{truncated_topic}' with lyrics, devotional, and video for children."

def process_keyword_clusters(input_file, output_file):
    """Process CSV file and generate URL metadata."""
    results = []
    
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            cluster_topic = row['Cluster_Topic'].strip()
            
            # Skip empty rows
            if not cluster_topic:
                continue
            
            # Generate slug from cluster topic
            slug = slugify(cluster_topic)
            
            # Infer category
            category = infer_category(cluster_topic)
            
            # Generate full URL
            url = f"{category}{slug}"
            
            # Generate metadata
            metadata = {
                'url': url,
                'keyword': cluster_topic,
                'title': generate_title(cluster_topic),
                'h1': cluster_topic,
                'meta_description': generate_meta_description(cluster_topic)
            }
            
            results.append(metadata)
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(results, jsonfile, indent=2, ensure_ascii=False)
    
    return len(results)

if __name__ == "__main__":
    input_file = "keyword_clusters.csv"
    output_file = "url_metadata.json"
    
    try:
        rows_processed = process_keyword_clusters(input_file, output_file)
        print(f"Successfully processed {rows_processed} rows from {input_file}")
        print(f"Results saved to {output_file}")
    except FileNotFoundError:
        print(f"Error: {input_file} not found in current directory")
    except Exception as e:
        print(f"Error processing file: {str(e)}")