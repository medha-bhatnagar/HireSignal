#format the input  
from groq import AsyncGroq
import json
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
import os
load_dotenv()
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY")
)

async def generate_summary(data: dict):
    chat_completion = await client.chat.completions.create(
        messages=[
    
        {"role": "system",
         "content": 
        """ 
        You are an AI recruiter assistant.
        Evaluate developers based on GitHub data.
        Give concise flowing paragraph(s) summary.
        Focus on experience level, technical strengths, primary technologies
        Do not use any markdown formatting — no asterisks, no bullet points, 
        no bold text, no headers, and no line breaks. Just plain prose sentences.
        """},
        {
        "role": "user",
         "content": 
        f"""
        Developer profile data: {data}
        """}
         
        ],
        model = "openai/gpt-oss-120b"
    )
    return chat_completion.choices[0].message.content



async def generate_job_match(profile_data: dict, job_requirements: str):
    chat_completion = await client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": """
            You are an AI recruiter assistant.
            Compare a developer's GitHub profile
            against a job description.
            Return the match percentage, matching skills, missing skills, hiring recommendation.
            Do not use any markdown formatting — no asterisks, no bullet points, 
            no bold text, no headers, and no line breaks. Just plain prose sentences.

                """
        },{
            "role":"user",
            "content":f"""
            Developer profile: {profile_data}
            Job Description: {job_requirements}
                """
        }
    ], model="openai/gpt-oss-120b"
    )
#  Use exactly this structure:\n"
#             '{"match_label": "Strong" | "Moderate" | "Weak", '
#             '"explanation": "a single flowing paragraph, no markdown, no line breaks"
    return chat_completion.choices[0].message.content
#send data to functions
#return text