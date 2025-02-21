from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain.text_splitter import CharacterTextSplitter
from PyPDF2 import PdfReader
from openai import OpenAI
from pydantic import BaseModel
import os
import json
import re

app = FastAPI()

# Initialize OpenAI client
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable not set!")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic model for evaluation request
class EvaluationRequest(BaseModel):
    questions: list
    user_answers: list

# Pydantic model for generating questions from a keyword
class KeywordRequest(BaseModel):
    keyword: str
    num_mcqs: int
    num_subjective: int
    difficulty: str

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Updated to gpt-4o
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_response = response.choices[0].message.content
        
        # Strip Markdown-style backticks if present
        if raw_response.startswith("```json") and raw_response.endswith("```"):
            raw_response = raw_response[len("```json"):].strip()[:-3].strip()
        
        # Check if the response is empty
        if not raw_response.strip():
            raise HTTPException(status_code=500, detail="Empty response from OpenAI API")
        
        # Attempt to parse the response as JSON
        try:
            parsed_response = json.loads(raw_response)
            # Normalize options for MCQs
            for q in parsed_response["questions"]:
                if q["type"] == "mcq":
                    q["options"] = normalize_options(q["options"])
                    q["correct_answer"] = normalize_options([q["correct_answer"]])[0]
            return parsed_response
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse API response")
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail="Error communicating with OpenAI API")

@app.post("/generate-test")
async def generate_test(pdf: UploadFile = File(None), difficulty: str = "medium", num_mcqs: int = 2, num_subjective: int = 1):
    if not pdf:
        raise HTTPException(400, "Upload a PDF file")
    
    text = extract_text_from_pdf(pdf.file)
    questions = generate_questions_from_text(text, num_mcqs, num_subjective, difficulty)
    return {"questions": questions["questions"]}

@app.post("/generate-from-keyword")
async def generate_from_keyword(request: KeywordRequest):
    keyword = request.keyword.strip()
    num_mcqs = request.num_mcqs
    num_subjective = request.num_subjective
    difficulty = request.difficulty
    
    if num_mcqs + num_subjective > 10:
        raise HTTPException(status_code=400, detail="Maximum total number of questions allowed is 10.")
    
    prompt = f"""
    Generate {num_mcqs} multiple-choice questions and {num_subjective} subjective questions based on the keyword: '{keyword}'.
    Difficulty: {difficulty}
    If the keyword does not provide enough context to generate meaningful questions, reply with:
    {{
        "error": "Not enough context to generate questions from this keyword."
    }}
    Otherwise, return the response strictly as valid JSON in the following format:
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
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Updated to gpt-4o
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_response = response.choices[0].message.content
        
        # Strip Markdown-style backticks if present
        if raw_response.startswith("```json") and raw_response.endswith("```"):
            raw_response = raw_response[len("```json"):].strip()[:-3].strip()
        
        # Check if the response is empty
        if not raw_response.strip():
            raise HTTPException(status_code=500, detail="Empty response from OpenAI API")
        
        # Attempt to parse the response as JSON
        try:
            parsed_response = json.loads(raw_response)
            if "error" in parsed_response:
                raise HTTPException(status_code=400, detail=parsed_response["error"])
            # Normalize options for MCQs
            for q in parsed_response["questions"]:
                if q["type"] == "mcq":
                    q["options"] = normalize_options(q["options"])
                    q["correct_answer"] = normalize_options([q["correct_answer"]])[0]
            return parsed_response
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse API response")
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail="Error communicating with OpenAI API")

@app.post("/evaluate-answers")
async def evaluate_answers(request: EvaluationRequest):
    score = 0
    feedback = []
    
    for idx, (q, ans) in enumerate(zip(request.questions, request.user_answers)):
        if q["type"] == "mcq":
            # Normalize user answer: Extract only the first letter (e.g., 'A', 'B', 'C') and append a period
            match_user = re.match(r"([A-Za-z])", str(ans).strip())
            user_answer = match_user.group(1).upper() + "." if match_user else None
            
            # Normalize correct answer: Extract only the first letter (e.g., 'A', 'B', 'C') and append a period
            match_correct = re.match(r"([A-Za-z])", str(q["correct_answer"]).strip())
            correct_answer = match_correct.group(1).upper() + "." if match_correct else None
            
            # Log the normalized values for debugging
            print(f"Debug - Q{idx+1}: Normalized User Answer: '{user_answer}', Normalized Correct Answer: '{correct_answer}'")
            
            if user_answer == correct_answer:
                score += 1
                feedback.append(f"Q{idx+1}: Correct!")
            else:
                feedback.append(f"Q{idx+1}: Wrong. Correct: {q['correct_answer']}")
        else:
            prompt = f"""
            Rate this answer from 0 to 1 (1=fully correct). Reply ONLY with the number.
            Question: {q['question']}
            Correct Answer: {q['correct_answer']}
            User Answer: {ans}
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",  # Updated to gpt-4o
                    messages=[{"role": "user", "content": prompt}]
                )
                points = float(response.choices[0].message.content.strip())
                score += points
                feedback.append(f"Q{idx+1}: Scored {points:.2f}/1")
            except Exception as e:
                feedback.append(f"Q{idx+1}: Evaluation failed - {str(e)}")
    
    return {"score": round(score, 2), "feedback": feedback}