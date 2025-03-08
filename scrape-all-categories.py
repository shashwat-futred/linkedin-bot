import json
import os
from dotenv import load_dotenv
import subprocess
import pandas as pd
import random
import time
from datetime import datetime
from tqdm import tqdm
from scrape import initialize_browser, scrape_search_results, save_to_csv

def load_categories():
    with open('top-100-categories-linkedin.json', 'r') as f:
        return json.load(f)

def scrape_category(browser, category, posts_per_category):
    try:
        # Use the scrape_search_results function directly instead of running scrape.py
        posts_data = scrape_search_results(browser, category, posts_per_category)
        
        # Save to temporary CSV
        save_to_csv(posts_data, 'search_results.csv')
        
        # Read the generated CSV file
        df = pd.read_csv('search_results.csv')
        df['Category'] = category
        df['Scraped_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete the temporary CSV file
        os.remove('search_results.csv')
        
        return df
    except Exception as e:
        print(f"\nError scraping category '{category}': {str(e)}")
        return None

def main():
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    num_categories = int(os.getenv('NUM_CATEGORIES', 100))
    posts_per_category = int(os.getenv('POSTS_PER_CATEGORY', 20))
    output_file = os.getenv('OUTPUT_FILE', 'all_categories_posts.csv')
    
    # Load categories
    all_categories = load_categories()
    random.shuffle(all_categories)
    categories_to_scrape = all_categories[:num_categories]
    
    # Initialize browser once
    print("Initializing browser...")
    browser = initialize_browser()
    if not browser:
        print("Failed to initialize browser. Exiting...")
        return
    
    try:
        # Initialize empty DataFrame to store all results
        all_posts_df = pd.DataFrame()
        
        # Scrape each category with progress bar
        for category in tqdm(categories_to_scrape, desc="Scraping categories"):
            df = scrape_category(browser, category, posts_per_category)
            
            if df is not None:
                all_posts_df = pd.concat([all_posts_df, df], ignore_index=True)
            
            # Add a small delay between categories to avoid rate limiting
            time.sleep(3)
        
        # Save all results to CSV
        all_posts_df.to_csv(output_file, index=False)
        print(f"\nScraping completed! Results saved to {output_file}")
        print(f"Total posts scraped: {len(all_posts_df)}")
        
    finally:
        browser.quit()

if __name__ == "__main__":
    main() 