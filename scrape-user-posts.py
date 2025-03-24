import json
import os
from dotenv import load_dotenv
import pandas as pd
import random
import time
from datetime import datetime
from tqdm import tqdm
from scrape import initialize_browser, scrape_profile_posts, save_to_csv
from urllib.parse import urlparse

def load_users():
    with open('famousguys.json', 'r') as f:
        return json.load(f)

def get_username_from_url(url):
    return url #url is currently same as username

def scrape_user(browser, profile_url, posts_per_user):
    try:
        # Get username from profile URL
        username = get_username_from_url(profile_url)
        if not username:
            print(f"\nError: Could not extract username from URL: {profile_url}")
            return None

        # Construct the activity URL
        activity_url = f"https://www.linkedin.com/in/{username}/recent-activity/all/"
        
        # Check if page exists (not 404)
        browser.get(activity_url)
        time.sleep(2)  # Wait for page to load
        
        # Check for 404 message
        try:
            error_message = browser.find_element("css selector", "p.artdeco-empty-state__message")
            if error_message and "Please check your URL" in error_message.text:
                print(f"\nSkipping user {username}: Profile not found (404)")
                return None
        except:
            pass  # No 404 message found, continue with scraping
        
        # Use the scrape_profile_posts function to get posts
        posts_data = scrape_profile_posts(browser, activity_url, posts_per_user)
        
        # Save to temporary CSV
        save_to_csv(posts_data, 'profile_posts.csv')
        
        # Read the generated CSV file
        df = pd.read_csv('profile_posts.csv')
        df['Username'] = username
        df['Profile_URL'] = profile_url
        df['Scraped_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete the temporary CSV file
        os.remove('profile_posts.csv')
        
        return df
    except Exception as e:
        print(f"\nError scraping user '{profile_url}': {str(e)}")
        return None

def main(num_users=None, posts_per_user=None):
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    num_users = int(os.getenv('NUM_USERS')) if num_users is None else num_users
    posts_per_user = int(os.getenv('POSTS_PER_USER')) if posts_per_user is None else posts_per_user
    output_file = os.getenv('USER_POSTS_OUTPUT_FILE', 'user_posts.csv')
    
    # Load users
    all_users = load_users()
    random.shuffle(all_users)
    users_to_scrape = all_users[:num_users]
    
    # Initialize browser once
    print("Initializing browser...")
    browser = initialize_browser()
    if not browser:
        print("Failed to initialize browser. Exiting...")
        return
    
    try:
        # Initialize empty DataFrame to store all results
        all_posts_df = pd.DataFrame()
        
        # Scrape each user with progress bar
        for user_url in tqdm(users_to_scrape, desc="Scraping users"):
            df = scrape_user(browser, user_url, posts_per_user)
            
            if df is not None:
                all_posts_df = pd.concat([all_posts_df, df], ignore_index=True)
            
            # Add a small delay between users to avoid rate limiting
            time.sleep(2)
        
        # Save all results to CSV
        all_posts_df.to_csv(output_file, index=False)
        print(f"\nScraping completed! Results saved to {output_file}")
        print(f"Total posts scraped: {len(all_posts_df)}")
        
    finally:
        browser.quit()

if __name__ == "__main__":
    import sys
    # Get command line arguments if provided
    num_users = int(sys.argv[1]) if len(sys.argv) > 1 else None
    posts_per_user = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(num_users, posts_per_user) 