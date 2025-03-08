import subprocess
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def run_script(script_name):
    print(f"\n{'='*50}")
    print(f"Running {script_name}...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        subprocess.run(['python', script_name], check=True)
        print(f"\n{script_name} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running {script_name}: {str(e)}")
        return False

def run_full_process():
    # Run scraping script
    if not run_script('scrape-all-categories.py'):
        print("Scraping failed. Stopping process.")
        return False
    
    # Add a small delay between scripts
    time.sleep(2)
    
    # Run filtering script
    if not run_script('filter-posts.py'):
        print("Filtering failed.")
        return False
    
    # Add a small delay before generating posts
    time.sleep(2)
    
    # Run post generation script
    if not run_script('generate-posts-using-trending.py'):
        print("Post generation failed.")
        return False
    
    return True

def run_post_generation():
    # Load environment variables
    load_dotenv()
    filtered_file = os.getenv('FILTERED_POSTS', 'filtered_posts.csv')
    
    # Check if filtered posts file exists
    if not os.path.exists(filtered_file):
        print(f"\nError: {filtered_file} not found!")
        print("Please run the full process first to generate filtered posts.")
        return False
    
    # Run post generation script
    return run_script('generate-posts-using-trending.py')

def main():
    print("\nLinkedIn Post Automation")
    print("1. Run full process (scrape + filter + generate)")
    print("2. Generate posts from existing filtered_posts.csv")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1 or 2): "))
            if choice in [1, 2]:
                break
            print("Please enter 1 or 2")
        except ValueError:
            print("Please enter a valid number")
    
    if choice == 1:
        print("\nRunning full process...")
        success = run_full_process()
    else:
        print("\nRunning post generation only...")
        success = run_post_generation()
    
    if success:
        print("\nAll processes completed successfully!")
    else:
        print("\nProcess completed with errors.")

if __name__ == "__main__":
    main() 