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
import argparse

class Summary(BaseModel):
    summary: str = Field(description="Something that is being talked about in the trending content along with relevant examples")

class SummaryList(BaseModel):
    summaries: List[Summary] = Field(description="List of summaries extracted from the trending content")

class GeneratedPost(BaseModel):
    content: str = Field(description="The generated post content")
    hashtags: List[str] = Field(description="List of relevant hashtags for the post")
    topic: str = Field(description="The topic/news this post is about")
    summary: str = Field(description="The original summary/topic this post was generated from")

def load_trending_content():
    # Load environment variables
    load_dotenv()
    filtered_file = os.getenv('FILTERED_USER_POSTS', 'filtered_user_posts.csv')
    
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

def extract_topics(model, trending_content, custom_instructions=""):
    # Initialize the output parser for topics
    parser = PydanticOutputParser(pydantic_object=SummaryList)

    print(custom_instructions)
    
    # Create the prompt template for topic extraction
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional linkedin content analyst. 
        Analyze the following trending posts and identify the top 10 most recurring topics or the latest news or event that is being talked about.
        Write summary of each of those 10.
        Summary HAS TO INCLUDE THE SPECIFICS FROM THE POST(s) FROM WHICH IT IS EXTRACTED.
        The summary has to be about specific recent events, news, or trends.
        Choose topics that is trending right now, not something generic which can be posted on any day. Name the people, products, services, companies or events involved.
        If an example is given in the trending posts, you have to use that example to illustrate your point.
        If a relevant topic involves a trending product, service, person, or company, include that in the summary.
        We are from the edtech sector, so we are more interested in topics relevant to education, tech, business, students.
        We want to include the latest events and news that are being talked about in the trending posts.
        In each summary, provide a relevant and engaging example to illustrate the point.
        Keep some variation in the types of posts. All posts not to be of similar type.
        
        VERY IMPORTANT: {custom_instructions}
         
        Dont write the post right now, just write the required summaries.
        
        IMPORTANT: Provide your response in clean JSON format without any markdown formatting or code block markers.
        The response should be a valid JSON object that can be parsed directly.
        
        {format_instructions}"""),
        ("user", "Here are the trending posts to analyze:\n\n{trending_content}")
    ])

    
    # Format the prompt
    formatted_prompt = prompt.format_messages(
        trending_content=trending_content,
        format_instructions=parser.get_format_instructions(),
        custom_instructions=custom_instructions
    )

    print(formatted_prompt)
    
    try:
        # Generate the response
        response = model.invoke(formatted_prompt)
        
        # Clean the response content by removing any markdown formatting
        cleaned_content = response.content.strip()
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()
        
        # Parse the response
        summary_list = parser.parse(cleaned_content)
        return summary_list.summaries
    except Exception as e:
        print(f"Error parsing topics: {str(e)}")
        print("Raw response:", response.content)
        raise

def generate_post_for_topic(model, summary, parser, custom_instructions=""):
    # Create the prompt template for post generation
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional LinkedIn content creator. 
        Create an engaging LinkedIn post about the following topic that:
        1. Is valuable to the professional community
        2. Includes relevant hashtags
        3. Maintains a professional tone
        4. Is optimized for LinkedIn's algorithm
        5. Is relevant to current time, not just generic
        6. Uses the example to illustrate the point in an engaging way
         
        You are creating content for Futred, which is a platform for stuents to learn tech, ai, business and other skills and get work oppotunities.
        You do not neccessarily have to mention the brand in the post, but keep it relevant to the brand.
        
        You have to use the following 6 elements to create the post:

        1. Hook (49 characters)
Grabs attention immediately—short, punchy, and intriguing. Use curiosity, bold statements, or emotional appeal to stop the scroll.
Examples: "I made a huge mistake today." "This post format is going viral."

2. Re-Hook (51 characters)
Builds on the hook and tells readers what value they'll get. Use numbers, results, or outcomes to spark interest and credibility.
Example: "12 posts got 38K likes, 11K comments, 3K reposts."

3. Body Text (953 characters)
Delivers the promised value with structure—bullets, short sentences, and clear flow. Use real stories, examples, data, or tips to inform and engage.

4. End of Body Text (132 characters)
Wraps up with a persuasive, engaging message. Reinforce the value or takeaway, often with a casual or personal tone to set up the CTA.
Example: "Now, off to the comments…"

5. CTA (72 characters)
Prompts immediate action—comment, click, download, or engage. Make it direct and compelling.
Example: "Are you ready to try this on your next post?"

6. Second CTA (63 characters)
Gently reminds readers to share. Keep it friendly and subtle, often with emojis for added visibility.
Example: "Don't forget to repost ♻️ this for others."
         
        It is not neccessary to use all the 6 elements, or stick to the exact character count. But try to follow the structure as closely as possible.
         
        ---

        VERY IMPORTANT: {custom_instructions}
         
        ---

        IMPORTANT: Provide your response in clean JSON format without any markdown formatting or code block markers.
        The response should be a valid JSON object that can be parsed directly.
        
        {format_instructions}"""),
        ("user", "Create a LinkedIn post about this topic:\n\nTopic: {summary}")
    ])
    
    # Format the prompt
    formatted_prompt = prompt.format_messages(
        summary=summary.summary,
        format_instructions=parser.get_format_instructions(),
        custom_instructions=custom_instructions
    )
    
    try:
        # Generate the response
        response = model.invoke(formatted_prompt)
        
        # Clean the response content by removing any markdown formatting
        cleaned_content = response.content.strip()
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()
        
        # Parse the response
        generated_post = parser.parse(cleaned_content)
        generated_post.summary = summary.summary  # Add the original summary
        
        return generated_post
    except Exception as e:
        print(f"Error generating post: {str(e)}")
        print("Raw response:", response.content)
        raise

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

def main(custom_instructions=""):
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

        modelBig = ChatOpenAI(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.7)),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize the output parsers
        topic_parser = PydanticOutputParser(pydantic_object=Summary)
        post_parser = PydanticOutputParser(pydantic_object=GeneratedPost)
        
        # Extract topics
        print("Extracting topics from trending content...")
        summaries = extract_topics(model, trending_content, custom_instructions)
        
        # Generate posts for each topic
        print("Generating posts for each topic...")
        generated_posts = []
        for summary in summaries:
            print(f"Generating post for topic: {summary.summary}")
            post = generate_post_for_topic(modelBig, summary, post_parser, custom_instructions)
            generated_posts.append(post)
        
        # Save all generated posts
        save_generated_posts(generated_posts)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate posts from trending content')
    parser.add_argument('--custom_instructions', type=str, help='Custom instructions for content generation')
    args = parser.parse_args()
    
    main(args.custom_instructions if args.custom_instructions else "") 