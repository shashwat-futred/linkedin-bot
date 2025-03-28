import subprocess
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from generate_using_web import generate_posts_from_web

def run_script(script_name):
    print(f"\n{'='*50}")
    print(f"Running {script_name if isinstance(script_name, str) else ' '.join(script_name)}...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        if isinstance(script_name, str):
            subprocess.run(['python', script_name], check=True)
        else:
            subprocess.run(script_name, check=True)
        print(f"\n{script_name if isinstance(script_name, str) else ' '.join(script_name)} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running {script_name if isinstance(script_name, str) else ' '.join(script_name)}: {str(e)}")
        return False

def run_full_process():
    # Run scraping script
    if not run_script('scrape-all-categories.py'):
        print("Scraping failed. Stopping process.")
        return False
    
    # Add a small delay between scripts
    time.sleep(2)
    
    # Run filtering script with category mode
    if not run_script(['python', 'filter-posts.py', '--mode', 'category']):
        print("Filtering failed.")
        return False
    
    # Add a small delay before generating posts
    time.sleep(2)
    
    # Run post generation script
    if not run_script('generate-posts-using-trending.py'):
        print("Post generation failed.")
        return False
    
    return True

def run_user_scraping():
    # Run user scraping script
    if not run_script('scrape-user-posts.py'):
        print("User scraping failed. Stopping process.")
        return False
    
    # Add a small delay between scripts
    time.sleep(2)
    
    # Run filtering script with user posts mode
    if not run_script(['python', 'filter-posts.py', '--mode', 'user']):
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
    trending_content = ""
    with open("filtered_user_posts.csv", "r", encoding="utf-8") as f:
        trending_content = f.read()
        
    posts = generate_posts_from_web(
    trending_content,
    )

    print(posts)

        # save posts to txt
    with open("generated_posts.txt", "w") as f:
        for post in posts:
            f.write(f"Topic: {post.topic}\n\n")
            f.write(post.content + "\n")
            f.write("--------------------------------\n")

    return True
    
    # Check if filtered posts file exists
    # if not os.path.exists(filtered_file):
    #     print(f"\nError: {filtered_file} not found!")
    #     print("Please run the full process first to generate filtered posts.")
    #     return False
    
    # Run post generation script
    # return run_script('generate-posts-using-trending.py')

def main():
    print("\nLinkedIn Post Automation")
    print("1. Run full process (scrape + filter + generate)")
    print("2. Generate posts from existing filtered_posts.csv")
    print("3. Scrape posts from specific users")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1, 2, or 3): "))
            if choice in [1, 2, 3]:
                break
            print("Please enter 1, 2, or 3")
        except ValueError:
            print("Please enter a valid number")
    
    if choice == 1:
        print("\nRunning full process...")
        success = run_full_process()
    elif choice == 2:
        print("\nRunning post generation only...")
        success = run_post_generation()
    else:
        print("\nRunning user post scraping...")
        success = run_user_scraping()
    
    if success:
        print("\nAll processes completed successfully!")
    else:
        print("\nProcess completed with errors.")

if __name__ == "__main__":
    main() 