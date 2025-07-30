import os
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re

def load_api_key():
    """Load SerpApi API key from environment variable."""
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        raise ValueError("SERPAPI_API_KEY environment variable not found")
    return api_key

def get_autocomplete_suggestions(query, api_key):
    """Fetch Google Autocomplete suggestions using SerpApi."""
    url = "https://serpapi.com/search"
    params = {
        'engine': 'google_autocomplete',
        'q': query,
        'api_key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        suggestions = []
        if 'suggestions' in data:
            for suggestion in data['suggestions']:
                if 'value' in suggestion:
                    suggestions.append(suggestion['value'])
        
        return suggestions
    except requests.RequestException as e:
        print(f"Error fetching autocomplete for '{query}': {e}")
        return []

def get_people_also_ask(query, api_key):
    """Fetch People Also Ask questions using SerpApi."""
    url = "https://serpapi.com/search"
    params = {
        'engine': 'google',
        'q': query,
        'api_key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        questions = []
        if 'related_questions' in data:
            for question in data['related_questions']:
                if 'question' in question:
                    questions.append(question['question'])
        
        return questions
    except requests.RequestException as e:
        print(f"Error fetching People Also Ask for '{query}': {e}")
        return []

def clean_keyword(keyword):
    """Clean and normalize keyword text."""
    # Remove extra whitespace and convert to lowercase
    keyword = re.sub(r'\s+', ' ', keyword.strip().lower())
    # Remove special characters but keep alphanumeric and spaces
    keyword = re.sub(r'[^\w\s]', '', keyword)
    return keyword

def cluster_keywords(keywords, n_clusters=10):
    """Cluster keywords using TF-IDF and KMeans."""
    if len(keywords) < n_clusters:
        n_clusters = len(keywords)
    
    # Vectorize keywords using TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 3)
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(keywords)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)
        
        # Group keywords by cluster
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(keywords[i])
        
        return clusters
    except Exception as e:
        print(f"Error clustering keywords: {e}")
        return {}

def get_cluster_representative(cluster_keywords):
    """Select the shortest keyword as the cluster representative."""
    return min(cluster_keywords, key=len)

def main():
    # Seed keywords
    seed_keywords = [
        "Bible songs for kids",
        "scripture songs",
        "kids worship music",
        "Easter worship songs children",
        "Christmas Bible songs preschool",
        "worship music for Sunday School"
    ]
    
    try:
        # Load API key
        api_key = load_api_key()
        print("API key loaded successfully")
        
        all_keywords = set()
        
        # Fetch data for each seed keyword
        for seed in seed_keywords:
            print(f"\nProcessing seed keyword: '{seed}'")
            
            # Get autocomplete suggestions
            suggestions = get_autocomplete_suggestions(seed, api_key)
            print(f"  Found {len(suggestions)} autocomplete suggestions")
            
            # Get People Also Ask questions
            questions = get_people_also_ask(seed, api_key)
            print(f"  Found {len(questions)} People Also Ask questions")
            
            # Add to our collection
            for item in suggestions + questions:
                cleaned = clean_keyword(item)
                if cleaned and len(cleaned) > 3:  # Filter out very short keywords
                    all_keywords.add(cleaned)
        
        print(f"\nTotal unique keywords found: {len(all_keywords)}")
        
        if not all_keywords:
            print("No keywords found. Exiting.")
            return
        
        # Convert to list for clustering
        keyword_list = list(all_keywords)
        
        # Cluster keywords
        print("Clustering keywords...")
        clusters = cluster_keywords(keyword_list, n_clusters=10)
        
        if not clusters:
            print("Clustering failed. Exiting.")
            return
        
        print(f"Created {len(clusters)} clusters")
        
        # Prepare data for CSV
        csv_data = []
        for cluster_id, kw_list in clusters.items():
            representative = get_cluster_representative(kw_list)
            keywords_str = "; ".join(sorted(kw_list))
            csv_data.append({
                'Cluster_Topic': representative,
                'Keywords': keywords_str
            })
        
        # Sort by cluster topic for consistent output
        csv_data.sort(key=lambda x: x['Cluster_Topic'])
        
        # Save to CSV
        df = pd.DataFrame(csv_data)
        df.to_csv('keyword_clusters.csv', index=False)
        print(f"\nResults saved to 'keyword_clusters.csv'")
        print(f"Total clusters: {len(csv_data)}")
        
        # Display summary
        for i, row in enumerate(csv_data, 1):
            keyword_count = len(row['Keywords'].split('; '))
            print(f"Cluster {i}: '{row['Cluster_Topic']}' ({keyword_count} keywords)")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()