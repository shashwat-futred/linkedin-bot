import pandas as pd
import os
from dotenv import load_dotenv
# from generate_posts_using_trending import generate_post_for_topic, GeneratedPost, Summary
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
import asyncio
import json
from datetime import datetime
from generate_using_web import generate_posts_from_web, generate_post_from_search
from openai import OpenAI


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    

    # posts = generate_posts_from_web(
    # trending_content="potato farming, f1 racing, plastic bottles",
    # )


    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    search_terms = []
    generated_posts = []
    for search_term in search_terms:
      print(f"Generating post for search term: {search_term['post_idea']}")
      post = generate_post_from_search(client, search_term)
      generated_posts.append(post)

    with open("generated_posts.txt", "w", encoding="utf-8") as f:
        for post in generated_posts:
            f.write(f"Topic: {post.topic}\n\n")
            f.write(post.content + "\n")
            f.write("--------------------------------\n")
        
    
