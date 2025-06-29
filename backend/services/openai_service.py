import os
import json
from openai import OpenAI
from fastapi import HTTPException

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_openai_api(prompt: str):
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),  # Use environment variable for model
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_response = response.choices[0].message.content
        
        # Strip Markdown-style backticks if present
        if raw_response.startswith("```json") and raw_response.endswith("```"):
            raw_response = raw_response[len("```json"):].strip()[:-3].strip()
        
        if not raw_response.strip():
            raise HTTPException(status_code=500, detail="Empty response from OpenAI API. The AI might not have generated a response or the response was not in the expected format.")
        
        try:
            parsed_response = json.loads(raw_response)
            return parsed_response
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to parse API response as JSON. Error: {e}. Raw response: {raw_response[:200]}...")
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI API: {e}")