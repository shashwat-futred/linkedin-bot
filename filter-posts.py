import json
import os
from dotenv import load_dotenv
import pandas as pd
import re

def truncate_post(text, max_words=200):
    """Truncate text to a maximum number of words."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'

def load_hiring_indicators():
    with open('hiring-post-indicator-words.json', 'r') as f:
        return json.load(f)

def remove_hiring_posts():
    # Load environment variables
    load_dotenv()
    
    # Get input and output file paths
    input_file = os.getenv('OUTPUT_FILE', 'all_categories_posts.csv')
    output_file = os.getenv('FILTERED_POSTS', 'filtered_posts.csv')
    
    # Load hiring indicator words
    hiring_indicators = load_hiring_indicators()
    
    # Create a regex pattern that matches any of the hiring indicators
    pattern = '|'.join(map(re.escape, hiring_indicators))
    
    print(f"Loading posts from {input_file}...")
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # Filter out posts containing any hiring indicators (case insensitive)
    df = df[~df['Content'].str.contains(pattern, case=False, na=False)]

    # Truncate the post content to 200 words
    df['Content'] = df['Content'].astype(str).apply(truncate_post)

    # Remove duplicates based on 'Content'
    df = df.drop_duplicates(subset='Content', keep='first')

    # reset the index after removing duplicates
    df.reset_index(drop=True, inplace=True)
    
    # Save filtered posts
    df.to_csv(output_file, index=False)
    removed_count = initial_count - len(df)
    
    print(f"\nHiring posts filtering completed!")
    print(f"Initial posts: {initial_count}")
    print(f"Posts removed: {removed_count}")
    print(f"Remaining posts: {len(df)}")
    print(f"Filtered posts saved to: {output_file}")
    
    return output_file

def likes_filter(input_file):
    # Load environment variables
    load_dotenv()
    
    # Get minimum likes threshold
    min_likes = int(os.getenv('LIKES_FILTER', 10))
    
    print(f"\nFiltering posts with less than {min_likes} likes...")
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # Filter posts based on likes count
    df = df[df['Reactions'] >= min_likes]
    
    # Save filtered posts
    df.to_csv(input_file, index=False)
    removed_count = initial_count - len(df)
    
    print(f"\nLikes filtering completed!")
    print(f"Initial posts: {initial_count}")
    print(f"Posts removed: {removed_count}")
    print(f"Remaining posts: {len(df)}")
    print(f"Final filtered posts saved to: {input_file}")

def main():
    # First remove hiring posts
    filtered_file = remove_hiring_posts()
    
    # Then filter by likes
    likes_filter(filtered_file)

if __name__ == "__main__":
    main() 