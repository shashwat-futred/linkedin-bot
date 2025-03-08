import os
from dotenv import load_dotenv
import pandas as pd
import random
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class Topic(BaseModel):
    topic: str = Field(description="A specific topic extracted from the trending content")
    description: str = Field(description="Brief description of why this topic is trending")

class TopicsList(BaseModel):
    topics: List[Topic] = Field(description="List of topics extracted from the trending content")

class GeneratedPost(BaseModel):
    content: str = Field(description="The generated post content")
    hashtags: List[str] = Field(description="List of relevant hashtags for the post")
    topic: str = Field(description="The topic this post is about")

def load_trending_content():
    # Load environment variables
    load_dotenv()
    filtered_file = os.getenv('FILTERED_POSTS', 'filtered_posts.csv')
    
    # Read the CSV file
    df = pd.read_csv(filtered_file)

    # Convert the 'Content' column to a list and shuffle it
    content_list = df['Content'].tolist()
    random.shuffle(content_list)

    # Combine shuffled content into a single string
    trending_content = "\n\n".join(content_list)
    
    # Combine all post contents into a single string
    trending_content = "\n\n".join(df['Content'].tolist())
    
    return trending_content

def extract_topics(model, trending_content):
    # Initialize the output parser for topics
    parser = PydanticOutputParser(pydantic_object=TopicsList)
    
    # Create the prompt template for topic extraction
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional linkedin content analyst. 
        Analyze the following trending posts and identify the top 10 most recurring and engaging topics and the latest thing or sentiment that is being talked about that topic.
        The topic will be a sentence that captures the essence of the conversation, but not too generic.
        If a relevant topic involves a trending product, service, person, or company, include that in the topic.
        For each topic, provide a brief description of why it's trending.
        
        {format_instructions}"""),
        ("user", "Here are the trending posts to analyze:\n\n{trending_content}")
    ])
    
    # Format the prompt
    formatted_prompt = prompt.format_messages(
        trending_content=trending_content,
        format_instructions=parser.get_format_instructions()
    )
    
    # Generate the response
    response = model.invoke(formatted_prompt)
    
    # Parse the response
    topics_list = parser.parse(response.content)
    
    return topics_list.topics

def generate_post_for_topic(model, topic, parser):
    # Create the prompt template for post generation
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional LinkedIn content creator. 
        Create an engaging LinkedIn post about the following topic that:
        1. Is valuable to the professional community
        2. Includes relevant hashtags
        3. Maintains a professional tone
        4. Is optimized for LinkedIn's algorithm
        
        {format_instructions}"""),
        ("user", "Create a LinkedIn post about this topic:\n\nTopic: {topic}\nDescription: {description}")
    ])
    
    # Format the prompt
    formatted_prompt = prompt.format_messages(
        topic=topic.topic,
        description=topic.description,
        format_instructions=parser.get_format_instructions()
    )
    
    # Generate the response
    response = model.invoke(formatted_prompt)
    
    # Parse the response
    generated_post = parser.parse(response.content)
    generated_post.topic = topic.topic  # Add the topic to the post
    
    return generated_post

def save_generated_posts(posts):
    # Create output directory if it doesn't exist
    os.makedirs('generated_posts', exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'generated_posts/posts_{timestamp}.txt'
    
    # Save all posts
    with open(filename, 'w', encoding='utf-8') as f:
        for i, post in enumerate(posts, 1):
            f.write(f"Post {i} - Topic: {post.topic}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"{post.content}\n\n")
            f.write("Hashtags:\n")
            for hashtag in post.hashtags:
                f.write(f"{hashtag} ")
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    print(f"\nGenerated posts saved to: {filename}")

def main():
    try:
        # Load trending content
        print("Loading trending content...")
        trending_content = load_trending_content()
        
        # Load environment variables
        load_dotenv()
        
        # Initialize the OpenAI model
        model = ChatOpenAI(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.7)),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize the output parsers
        topic_parser = PydanticOutputParser(pydantic_object=Topic)
        post_parser = PydanticOutputParser(pydantic_object=GeneratedPost)
        
        # Extract topics
        print("Extracting topics from trending content...")
        topics = extract_topics(model, trending_content)
        
        # Generate posts for each topic
        print("Generating posts for each topic...")
        generated_posts = []
        for topic in topics:
            print(f"Generating post for topic: {topic.topic}")
            post = generate_post_for_topic(model, topic, post_parser)
            generated_posts.append(post)
        
        # Save all generated posts
        save_generated_posts(generated_posts)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main() 