"""
Scrapes posts from linkedin. input: profile url or search keyword.
commands: 
python scrape.py --mode search --keyword "your search term" --max-posts 20
python scrape.py --mode profile --url "https://www.linkedin.com/in/username/recent-activity/all/" --max-posts 50
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from bs4 import BeautifulSoup as bs
import csv
import argparse
from urllib.parse import quote

# Function to load cookies from a Netscape format cookies.txt file
def load_cookies(browser, file_path):
    with open(file_path, 'r') as file:
        for line in file:
            if not line.startswith('#') and line.strip():
                fields = line.strip().split('\t')
                if len(fields) == 7:
                    domain = fields[0]
                    # Remove leading dot from domain if present
                    if domain.startswith('.'):
                        domain = domain[1:]
                    
                    cookie = {
                        'name': fields[5],
                        'value': fields[6],
                        'domain': domain,
                        'path': fields[2],
                        'secure': fields[3].lower() == 'true',
                        'expiry': int(fields[4]) if fields[4] and fields[4].isdigit() else None
                    }
                    
                    try:
                        browser.add_cookie(cookie)
                    except Exception as e:
                        print(f"Failed to add cookie {cookie['name']}: {str(e)}")

def initialize_browser():
    # Initialize Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    
    # Initialize the Chrome driver
    print("Initializing the Chrome driver...")
    browser = webdriver.Chrome(options=chrome_options)
    browser.set_window_size(1920, 1080)
    
    # Open LinkedIn login page
    print("Opening LinkedIn login page...")
    browser.get('https://www.linkedin.com/')
    
    # Load cookies from the file
    print("Loading cookies...")
    load_cookies(browser, 'linkedin_cookies_netscape.txt')
    
    # Refresh the page to apply cookies
    browser.refresh()
    
    # Wait for the main navigation bar to be visible
    print("Waiting for the main navigation bar after applying cookies...")
    try:
        WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#global-nav .global-nav__me')))
        print("Navigation bar found. Proceeding with scraping...")
    except TimeoutException:
        print("TimeoutException: Navigation bar not found after applying cookies. Check if the cookies are correct.")
        return None
    
    return browser

def scrape_profile_posts(browser, user_profile_url, max_posts=50):
    print(f"Navigating to the user's recent activity page: {user_profile_url}...")
    browser.get(user_profile_url)
    
    # Wait for the page to load completely
    print("Waiting for the user's recent activity page to load completely...")
    time.sleep(5)
    
    posts_data = []
    post_count = 0
    no_new_posts_count = 0
    max_no_new_posts = 3  # Maximum number of consecutive scrolls without new posts
    
    while post_count < max_posts:
        # Parse the page source with BeautifulSoup
        user_page = browser.page_source
        linkedin_soup = bs(user_page.encode("utf-8"), "html.parser")
        
        # Extract post containers from the HTML
        containers = linkedin_soup.find_all("div", {"class": "social-details-social-counts"})
        current_post_count = len(posts_data)
        
        # Process each container
        for container in containers:
            if post_count >= max_posts:
                break
                
            try:
                post_content_container = container.find_previous("div", {"class": "update-components-text"})
                post_content = post_content_container.text.strip() if post_content_container else "No content"
            except Exception as e:
                print(e)
                post_content = "No content"
                
            try:
                post_reactions = container.find("li", {"class": "social-details-social-counts__reactions"}).find("button")["aria-label"].split(" ")[0].replace(',', '')
            except:
                post_reactions = "0"
            try:
                post_comments = container.find("li", {"class": "social-details-social-counts__comments"}).find("button")["aria-label"].split(" ")[0].replace(',', '')
            except:
                post_comments = "0"
                
            # Convert reactions and comments to numeric values
            post_reactions_numeric = convert_abbreviated_to_number(post_reactions)
            post_comments_numeric = convert_abbreviated_to_number(post_comments)
            
            posts_data.append({
                'Content': post_content,
                'Reactions': post_reactions_numeric,
                'Comments': post_comments_numeric,
            })
            
            post_count += 1
            print(f"Post {post_count} saved.")
            
        # Check if we found any new posts after this scroll
        if len(posts_data) == current_post_count:
            no_new_posts_count += 1
            print(f"No new posts found after scroll. Attempt {no_new_posts_count}/{max_no_new_posts}")
            if no_new_posts_count >= max_no_new_posts:
                print("Stopping scroll as no new posts are being found.")
                break
        else:
            no_new_posts_count = 0  # Reset counter if we found new posts
            
        # Only scroll if we haven't reached max_posts
        if post_count < max_posts:
            print("Scrolling down to load more posts...")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
    
    return posts_data

def scrape_search_results(browser, search_keyword, max_posts=20):
    encoded_keyword = quote(search_keyword)
    search_url = f"https://www.linkedin.com/search/results/content/?datePosted=\"past-week\"&keywords={encoded_keyword}&origin=SWITCH_SEARCH_VERTICAL"
    print(f"Navigating to search results page: {search_url}...")
    browser.get(search_url)
    
    # Wait for the page to load completely
    print("Waiting for search results page to load completely...")
    time.sleep(5)
    
    posts_data = []
    post_count = 0
    no_new_posts_count = 0
    max_no_new_posts = 3  # Maximum number of consecutive scrolls without new posts
    
    while post_count < max_posts:
        # Parse the page source with BeautifulSoup
        search_page = browser.page_source
        linkedin_soup = bs(search_page.encode("utf-8"), "html.parser")
        
        # Extract post containers from the HTML
        post_containers = linkedin_soup.find_all("div", {"class": "update-components-text"})
        current_post_count = len(posts_data)
        
        # Process each container
        for container in post_containers:
            if post_count >= max_posts:
                break
                
            try:
                # Get post content
                post_content = container.text.strip()
                
                # Find the reactions count
                reactions_element = container.find_next("span", {"class": "social-details-social-counts__reactions-count"})
                reactions = reactions_element.text.strip() if reactions_element else "0"
                
                # Convert reactions to numeric value
                reactions_numeric = convert_abbreviated_to_number(reactions)
                
                posts_data.append({
                    'Content': post_content,
                    'Reactions': reactions_numeric,
                    'Comments': 0  # Search results don't show comments count
                })
                
                post_count += 1
                print(f"Post {post_count} saved.")
                
            except Exception as e:
                print(f"Error processing post: {str(e)}")
                continue
        
        # Check if we found any new posts after this scroll
        if len(posts_data) == current_post_count:
            no_new_posts_count += 1
            print(f"No new posts found after scroll. Attempt {no_new_posts_count}/{max_no_new_posts}")
            if no_new_posts_count >= max_no_new_posts:
                print("Stopping scroll as no new posts are being found.")
                break
        else:
            no_new_posts_count = 0  # Reset counter if we found new posts
            
        # Only scroll if we haven't reached max_posts
        if post_count < max_posts:
            print("Scrolling down to load more posts...")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(10)
    
    return posts_data

def convert_abbreviated_to_number(s):
    if 'K' in s:
        return int(float(s.replace('K', '')) * 1000)
    elif 'M' in s:
        return int(float(s.replace('M', '')) * 1000000)
    else:
        return int(s)

def save_to_csv(posts_data, filename):
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Content', 'Reactions', 'Comments'])
        for post in posts_data:
            writer.writerow([post['Content'], post['Reactions'], post['Comments']])

def main():
    parser = argparse.ArgumentParser(description='LinkedIn Post Scraper')
    parser.add_argument('--mode', choices=['profile', 'search'], required=True, help='Scraping mode: profile or search')
    parser.add_argument('--url', help='Profile URL for profile mode')
    parser.add_argument('--keyword', help='Search keyword for search mode')
    parser.add_argument('--max-posts', type=int, default=20, help='Maximum number of posts to scrape')
    args = parser.parse_args()
    
    # Initialize browser
    browser = initialize_browser()
    if not browser:
        return
    
    try:
        # Scrape based on mode
        if args.mode == 'profile':
            if not args.url:
                print("Error: Profile URL is required for profile mode")
                return
            posts_data = scrape_profile_posts(browser, args.url, args.max_posts)
            output_file = "profile_posts.csv"
        else:  # search mode
            if not args.keyword:
                print("Error: Search keyword is required for search mode")
                return
            posts_data = scrape_search_results(browser, args.keyword, args.max_posts)
            output_file = "search_results.csv"
        
        # Save results to CSV
        save_to_csv(posts_data, output_file)
        print(f"Data exported to {output_file}")
        
    finally:
        browser.quit()

if __name__ == "__main__":
    main()
