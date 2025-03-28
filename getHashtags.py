import pandas as pd
import re
from collections import Counter

def extract_hashtags(text):
    """Extract hashtags from text using regex."""
    hashtags = re.findall(r'#\w+', text)
    return hashtags

def get_top_hashtags(csv_file='filtered_user_posts.csv', top_n=10):
    """Get top N most recurring hashtags from the CSV file."""
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Extract hashtags from all posts
        all_hashtags = []
        for content in df['Content']:
            hashtags = extract_hashtags(content)
            all_hashtags.extend(hashtags)
        
        # Count hashtag frequencies
        hashtag_counts = Counter(all_hashtags)
        
        # Get top N hashtags
        top_hashtags = hashtag_counts.most_common(top_n)
        
        # Format hashtags as a single string
        hashtag_string = ' '.join([tag for tag, _ in top_hashtags])

        #write to generated_posts/top_hashtags.txt
        with open('generated_posts/top_hashtags.txt', 'w') as f:
            f.write(hashtag_string)
        
        return hashtag_string
        
    except Exception as e:
        print(f"Error processing hashtags: {str(e)}")
        return "" 