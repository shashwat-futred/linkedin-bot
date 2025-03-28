import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import json
from post_guidelines import guideline1, guideline2

class SearchTerm(BaseModel):
    idea: str = Field(description="A search term to find relevant information")
    search_term: str = Field(description="A search term to find relevant information")

class SearchTermList(BaseModel):
    ideas: List[SearchTerm] = Field(description="List of search terms and ideas")

class GeneratedPost(BaseModel):
    content: str = Field(description="The generated post content")
    topic: str = Field(description="The topic/news this post is about")
    # search_term: str = Field(description="The search term used to generate this post")

def extract_search_terms(client, trending_content, guideline=""):
    """Extract search terms from trending content using GPT-4"""
    prompt = f"""
    {guideline}
    -----

Your job is to extract 15 relevant ideas for posts, based on what is trending today, and our guidelines. Below is a list of trending posts. Extract relevant ideas which are not too generic. For each idea, Craft a detailed search term, using which we can find relevant latest articles to refer to in the post to make it more engaging.
search terms would help find detailed information about the topics.
Each search term should be specific and targeted to find recent, relevant information.
-----
    
    Here is the trending content to analyze:
    
    {trending_content}
    
    Provide your response as a JSON array of 15 objects with "idea" and "search_term" fields, like this:
    {{"ideas": [{{"idea": "idea 1", "search_term": "search term 1"}}, {{"idea": "idea 2", "search_term": "search term 2"}}, ...]}}"""
    
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[
                # {
                #     "type": "web_search_preview",
                #     "user_location": {
                #         "type": "approximate",
                #         "country": "IN",
                #         "region": "delhi"
                #     },
                #     "search_context_size": "medium"
                # }
            ],
            temperature=0.9,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # Extract the text content from the response
        response_text = response.output[0].content[0].text
        # Remove markdown code block markers if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse the response
        search_terms = SearchTermList.parse_raw(response_text)
        return search_terms.ideas
    except Exception as e:
        print(f"Error extracting search terms: {str(e)}")
        print("Raw response:", response_text)
        raise

def generate_post_from_search(client, search_term, guideline=guideline2):
    """Generate a post using web search capabilities"""
    prompt = f"""You are a professional LinkedIn content creator with web search capabilities.
    
    {guideline}

    -----

    Use the following idea and search the given search term to find relevant latest article and generate a post:
    
    Web Search Term and idea: {search_term}
    
    Provide your response as a JSON object with these fields: (no markdown. Return only the JSON object, nothing else.)
    - content: The post content (it must start with a crisp, engaging hook. And use short points.)
    - topic: The topic of the post (not to be displayed to audience, only for internal use)"""
    
    try:
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[
                {
                    "type": "web_search_preview",
                    "user_location": {
                        "type": "approximate",
                        "country": "IN",
                        "region": "delhi"
                    },
                    "search_context_size": "medium"
                }
            ],
            temperature=0.8,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # print(response)

        # Extract the text content from the response
        response_text = response.output[1].content[0].text

        print(response_text)

        # Remove markdown code block markers if present
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        if response_text.endswith('\n'):
            response_text = response_text[:-1]
        response_text = response_text.strip()

        print("--------------------------------")

        print(response_text)
        
        # Parse the response
        post_data = json.loads(response_text)
        generated_post = GeneratedPost(
            content=post_data["content"],
            topic=post_data["topic"],
            # search_term=search_term.term
        )
        return generated_post
    except Exception as e:
        print(f"Error generating post for search term '{search_term.search_term}': {str(e)}")
        print("Raw response:", response_text)
        raise

def generate_posts_from_web(trending_content: str) -> List[GeneratedPost]:
    """
    Generate posts using web search capabilities.
    
    Args:
        trending_content (str): The trending content to analyze
        
    Returns:
        List[GeneratedPost]: List of generated posts
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Extract search terms
        print("Extracting search terms from trending content...")
        search_terms = extract_search_terms(client, trending_content, guideline1)
        
        # Generate posts for each search term
        print("Generating posts for each search term...")
        generated_posts = []
        for search_term in search_terms:
            print(f"Generating post for search term: {search_term.idea}")
            post = generate_post_from_search(client, search_term, guideline2)
            generated_posts.append(post)
        
        return generated_posts
        
    except Exception as e:
        print(f"Error in generate_posts_from_web: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    test_content = """
    Recent developments in artificial intelligence and machine learning are transforming industries.
    Key trends include the rise of large language models, increased focus on AI ethics and regulation,
    and growing adoption of AI in healthcare and finance.
    """
    
    test_guideline = """
    Focus on practical applications and real-world examples.
    Include specific company names and products where relevant.
    """
    
    posts = ["test"]
    print(f"Generated {len(posts)} posts")