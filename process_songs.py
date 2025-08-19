#!/usr/bin/env python3
"""
Process SEEDS songs CSV file and convert to JSON with validation and normalization.
"""
import argparse
import json
import re
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
from dateutil.parser import parse as dateparse
from slugify import slugify


def validate_url(url_str):
    """Validate URL with basic scheme/domain check."""
    if not url_str or pd.isna(url_str) or str(url_str).strip() == '':
        return ""
    
    url_str = str(url_str).strip()
    try:
        parsed = urlparse(url_str)
        if parsed.scheme in ('http', 'https') and parsed.netloc:
            return url_str
    except Exception:
        pass
    return ""


def normalize_date(date_str):
    """Parse and normalize date to YYYY-MM-DD format."""
    if not date_str or pd.isna(date_str) or str(date_str).strip() == '':
        return ""
    
    date_str = str(date_str).strip()
    try:
        parsed_date = dateparse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except Exception:
        return ""


def safe_int(value):
    """Convert value to int, return None if invalid."""
    if pd.isna(value) or str(value).strip() == '':
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def safe_str(value):
    """Convert value to string, handle NaN/None."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def process_songs_csv(input_path, output_path):
    """Process the SEEDS songs CSV file."""
    
    # Read CSV
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    print(f"Input rows: {len(df)}")
    
    # Check for required Song Title column
    if 'Song Title' not in df.columns:
        print("Error: 'Song Title' column not found in CSV")
        return
    
    # Report missing titles
    missing_titles = df['Song Title'].isna() | (df['Song Title'].str.strip() == '')
    missing_count = missing_titles.sum()
    if missing_count > 0:
        print(f"Warning: {missing_count} rows missing Song Title")
    
    # Remove rows with missing titles
    df = df[~missing_titles].copy()
    
    # Create canonical slugs for deduplication
    df['canonical_slug'] = df['Song Title'].apply(lambda x: slugify(safe_str(x).lower()) if not pd.isna(x) else '')
    
    # Remove rows with empty slugs
    df = df[df['canonical_slug'] != ''].copy()
    
    # Remove duplicates by canonical slug (case-insensitive)
    df_deduped = df.drop_duplicates(subset=['canonical_slug'], keep='first')
    
    print(f"After deduplication: {len(df_deduped)} rows")
    
    # Process each row
    songs = []
    invalid_webpage_count = 0
    invalid_spotify_count = 0
    
    for _, row in df_deduped.iterrows():
        # Validate URLs
        webpage_url = validate_url(row.get('Webpage URL'))
        spotify_url = validate_url(row.get('Spotify Link'))
        
        if row.get('Webpage URL') and not webpage_url:
            invalid_webpage_count += 1
        if row.get('Spotify Link') and not spotify_url:
            invalid_spotify_count += 1
        
        # Create song record
        song = {
            "title": safe_str(row['Song Title']),
            "slug": slugify(safe_str(row['Song Title'])),
            "album": safe_str(row.get('Album', '')),
            "year": safe_int(row.get('Year')),
            "scripture": safe_str(row.get('Scripture Reference', '')),
            "webpage_url": webpage_url,
            "spotify_url": spotify_url,
            "description": safe_str(row.get('Description', '')),
            "publication_date": normalize_date(row.get('Publication Date')),
            "duration": safe_str(row.get('Duration', '')),
            "target_age": safe_str(row.get('Target Age Group', '')),
            "style": safe_str(row.get('Musical Style', '')),
            "lyrics": safe_str(row.get('Lyrics', ''))
        }
        
        songs.append(song)
    
    # Write JSON output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(songs, f, indent=2, ensure_ascii=False)
        print(f"Output written to: {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        return
    
    # Print statistics
    print(f"Final song count: {len(songs)}")
    if invalid_webpage_count > 0:
        print(f"Invalid webpage URLs: {invalid_webpage_count}")
    if invalid_spotify_count > 0:
        print(f"Invalid Spotify URLs: {invalid_spotify_count}")


def main():
    parser = argparse.ArgumentParser(description='Process SEEDS songs CSV to JSON')
    parser.add_argument('--csv', default='./assets/seeds_songs.csv',
                        help='Input CSV file path (default: ./assets/seeds_songs.csv)')
    
    args = parser.parse_args()
    
    input_path = args.csv
    output_path = './assets/seeds_songs.json'
    
    process_songs_csv(input_path, output_path)


if __name__ == '__main__':
    main()