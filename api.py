from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import time
import os
import json
from datetime import datetime
import tempfile
from dotenv import load_dotenv
from getHashtags import get_top_hashtags
from generate_using_web import generate_posts_from_web
app = FastAPI(title="LinkedIn Post Automation API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class CookiesRequest(BaseModel):
    cookies: str
    users: Optional[List[str]] = None
    numUsers: Optional[int] = None
    postsPerUser: Optional[int] = None
    minLikes: Optional[int] = None
    useOnlyInputProfiles: Optional[bool] = False
    customInstructions: Optional[str] = None

class TestResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    generated_posts: str

def save_cookies(cookies_content: str) -> str:
    """Save cookies to a temporary file and return its path."""
    temp_dir = tempfile.gettempdir()
    cookies_path = os.path.join(temp_dir, 'linkedin_cookies_netscape.txt')
    
    with open(cookies_path, 'w') as f:
        f.write(cookies_content)
    
    return cookies_path

def save_users(users: List[str]) -> str:
    """Save users to a temporary file and return its path."""
    temp_dir = tempfile.gettempdir()
    users_path = os.path.join(temp_dir, 'famousguys.json')
    
    with open(users_path, 'w') as f:
        json.dump(users, f, indent=2)
    
    return users_path

def convertToUsername(users: List[str]) -> List[str]:
    """Convert users to usernames."""
    for user in users:
        user.replace('https://www.linkedin.com/in/', '')
        #remove slug
        user = user.split('/')[0]
        user = user.split('?')[0]
        return user
    return users


def run_script(script_name: str | list) -> bool:
    """Run a Python script and return True if successful."""
    try:
        if isinstance(script_name, list):
            # If script_name is a list, use it directly as the command
            subprocess.run(script_name, check=True)
        else:
            # If script_name is a string, prepend 'python' to it
            subprocess.run(['python', script_name], check=True)
        return True
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error running {script_name}: {str(e)}")

def get_latest_generated_posts() -> str:
    """Get the content of the latest generated posts file."""
    try:
        generated_posts_dir = 'generated_posts'
        if not os.path.exists(generated_posts_dir):
            os.makedirs(generated_posts_dir)
            raise HTTPException(status_code=404, detail="No generated posts found. The posts directory was empty.")
        
        files = os.listdir(generated_posts_dir)
        if not files:
            raise HTTPException(status_code=404, detail="No generated posts found in the directory.")
        
        # Filter for .txt files only
        txt_files = [f for f in files if f.endswith('.txt')]
        if not txt_files:
            raise HTTPException(status_code=404, detail="No text files found in the generated posts directory.")
        
        latest_file = max(txt_files, key=lambda x: os.path.getctime(os.path.join(generated_posts_dir, x)))
        latest_file_path = os.path.join(generated_posts_dir, latest_file)
        
        with open(latest_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                raise HTTPException(status_code=404, detail="The generated posts file is empty.")
            return content
            
    except Exception as e:
        print(f"Error in get_latest_generated_posts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving generated posts: {str(e)}")

def get_default_users() -> List[str]:
    """Load users from the default famousguys.json file."""
    try:
        with open('famousguys.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Default users file (famousguys.json) not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing famousguys.json")

@app.post("/run-full-process")
async def run_full_process(request: CookiesRequest):
    """Run the full process (scrape + filter + generate) with provided cookies and users."""
    try:
        # Save cookies to temporary file
        cookies_path = save_cookies(request.cookies)
        
        # Use provided users or load from default file
        users = request.users if request.users is not None else get_default_users()
        users_path = save_users(users)
        
        # Set environment variables for the scripts
        os.environ['COOKIES_FILE'] = cookies_path
        os.environ['USERS_FILE'] = users_path
        
        # Run the full process
        if not run_script('scrape-all-categories.py'):
            raise HTTPException(status_code=500, detail="Scraping failed")
        
        time.sleep(2)
        
        if not run_script(['python', 'filter-posts.py', '--mode', 'category']):
            raise HTTPException(status_code=500, detail="Filtering failed")
        
        time.sleep(2)
        
        if not run_script('generate-posts-using-trending.py'):
            raise HTTPException(status_code=500, detail="Post generation failed")
        
        # Get the generated posts
        generated_posts = get_latest_generated_posts()
        
        return {"status": "success", "generated_posts": generated_posts}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-from-existing")
async def generate_from_existing():
    """Generate posts from existing filtered_posts.csv."""
    try:
        if not run_script('generate-posts-using-trending.py'):
            raise HTTPException(status_code=500, detail="Post generation failed")
        
        generated_posts = get_latest_generated_posts()
        return {"status": "success", "generated_posts": generated_posts}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-user-posts")
async def scrape_user_posts(request: CookiesRequest):
    """Scrape posts from specific users with provided cookies and users."""
    try:
        # Save cookies to temporary file
        cookies_path = save_cookies(request.cookies)
        
        useOnlyInputProfiles = request.useOnlyInputProfiles or False

        num_users = request.numUsers

        posts_per_user = request.postsPerUser

        likes_filter = 100 if (num_users * posts_per_user) < 200 else 400

        custom_instructions = request.customInstructions

        num_posts = request.numPosts if request.numPosts else 10
        
        default_users = get_default_users()

        # Use provided users or load from default file
        if(useOnlyInputProfiles):
            users = request.users
        else:
            users = [*request.users, *default_users]

        users = convertToUsername(users)

        users_path = save_users(users)
        
        # Set environment variables for the scripts
        os.environ['COOKIES_FILE'] = cookies_path
        os.environ['USERS_FILE'] = users_path
        
        print("Starting user scraping process...")
        # Run user scraping process with arguments
        if not run_script(['python', 'scrape-user-posts.py', str(num_users), str(posts_per_user)]):
            raise HTTPException(status_code=500, detail="User scraping failed")
        
        print("User scraping completed, starting filtering...")
        time.sleep(2)
        
        # Run filter-posts.py with mode argument
        if not run_script(['python', 'filter-posts.py', '--mode', 'user', '--likes_filter', str(likes_filter)]):
            raise HTTPException(status_code=500, detail="Filtering failed")
        
        print("Filtering completed, starting post generation...")
        time.sleep(2)
        
        # Run generate-posts-using-trending.py with custom instructions
        # if custom_instructions:
        #     # Escape any quotes in the custom instructions
        #     escaped_instructions = custom_instructions.replace('"', '\\"')
        #     if not run_script(['python', 'generate-posts-using-trending.py', f'--custom_instructions={escaped_instructions}']):
        #         raise HTTPException(status_code=500, detail="Post generation failed")
        # else:
        #     if not run_script('generate-posts-using-trending.py'):
        #         raise HTTPException(status_code=500, detail="Post generation failed")

        trending_content = ""
        with open("filtered_user_posts.csv", "r", encoding="utf-8") as f:
            trending_content = f.read()
        
        posts = generate_posts_from_web(
        trending_content,
        custom_instructions=custom_instructions,
        num_posts=num_posts
        )

        print(posts)

        # save posts to txt
        with open("generated_posts.txt", "w") as f:
            for post in posts:
                f.write(f"Topic: {post.topic}\n\n")
                f.write(post.content + "\n")
                f.write("--------------------------------\n")
        
        print("Post generation completed, retrieving results...")
        # Get the generated posts
        try:
            generated_posts = get_latest_generated_posts()
            # Get top hashtags
            top_hashtags = get_top_hashtags()
            
            return {
                "status": "success", 
                "generated_posts": generated_posts,
                "top_hashtags": top_hashtags
            }
        except HTTPException as e:
            print(f"Error retrieving generated posts: {str(e)}")
            return {"status": "partial_success", "message": "Posts were scraped but generation failed", "error": str(e)}
    
    except Exception as e:
        print(f"Error in scrape_user_posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API functionality."""
    return TestResponse(
        status="success",
        message="API is working correctly",
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        generated_posts= "Post 1 - Topic: The upcoming VishvaTech 3.0 event, scheduled from March 17-19, aims to foster innovation and networking among industry leaders and experts.\n================\n\nHave you ever found yourself in a room filled with visionaries, innovators \n\n============\n\nPost 2 - Topic: The Kectil Regional Conference in Zambia highlighted the power of in-person connections among young changemakers.\n================" 
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 