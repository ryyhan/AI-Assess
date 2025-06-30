import os
import json
import re
from openai import OpenAI
from fastapi import HTTPException
from langchain.text_splitter import CharacterTextSplitter

# Initialize OpenAI client
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

def generate_questions_from_text(text: str, num_mcqs: int, num_subjective: int, difficulty: str = "medium"):
    if num_mcqs + num_subjective > 10:
        raise HTTPException(status_code=400, detail="Maximum total number of questions allowed is 10.")

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)

    prompt = f"""
    Generate {num_mcqs} multiple-choice questions and {num_subjective} subjective questions from the text below.
    Difficulty: {difficulty}
    Text: {chunks[0]}

    IMPORTANT: Return the response strictly as valid JSON in the following format:
    {{
        "questions": [
            {{
                "type": "mcq",
                "question": "...",
                "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
                "correct_answer": "A. Option 1"
            }},
            {{
                "type": "subjective",
                "question": "...",
                "correct_answer": "..."
            }}
        ]
    }}
    """

    parsed_response = call_openai_api(prompt)
    # Normalize options for MCQs
    for q in parsed_response["questions"]:
        if q["type"] == "mcq":
            q["options"] = normalize_options(q["options"])
            q["correct_answer"] = normalize_options([q["correct_answer"]])[0]
    return parsed_response

def normalize_options(options):
    # Normalize options to a consistent format (e.g., "A. Option 1")
    normalized_options = []
    for option in options:
        # Extract the letter (A, B, C, D) and append a period
        match = re.match(r"([A-Za-z])[).:-]?\s*(.*)", option)
        if match:
            letter, text = match.groups()
            normalized_options.append(f"{letter.upper()}. {text.strip()}")
    return normalized_options