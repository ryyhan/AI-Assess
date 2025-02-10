from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain.text_splitter import CharacterTextSplitter
from PyPDF2 import PdfReader
from openai import OpenAI
from pydantic import BaseModel
import os
import json

app = FastAPI()

# Initialize OpenAI client
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable not set!")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic model for evaluation request
class EvaluationRequest(BaseModel):
    questions: list
    user_answers: list

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def generate_questions(text: str, difficulty: str = "medium"):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    
    prompt = f"""
    Generate 2 multiple-choice questions and 1 subjective question from the text below.
    Difficulty: {difficulty}
    Text: {chunks[0]}
    
    IMPORTANT: Return the response strictly as valid JSON in the following format:
    {{
        "questions": [
            {{
                "type": "mcq",
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A"
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
        
        # Log the raw response for debugging
        print("Raw API Response:", raw_response)
        
        # Strip Markdown-style backticks if present
        if raw_response.startswith("```json") and raw_response.endswith("```"):
            raw_response = raw_response[len("```json"):].strip()[:-3].strip()
        
        # Check if the response is empty
        if not raw_response.strip():
            raise HTTPException(status_code=500, detail="Empty response from OpenAI API")
        
        # Attempt to parse the response as JSON
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse API response")
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail="Error communicating with OpenAI API")

@app.post("/generate-test")
async def generate_test(pdf: UploadFile = File(None), difficulty: str = "medium"):
    if not pdf:
        raise HTTPException(400, "Upload a PDF file")
    
    text = extract_text_from_pdf(pdf.file)
    questions = generate_questions(text, difficulty)
    return {"questions": questions["questions"]}

@app.post("/evaluate-answers")
async def evaluate_answers(request: EvaluationRequest):
    score = 0
    feedback = []
    
    for idx, (q, ans) in enumerate(zip(request.questions, request.user_answers)):
        if q["type"] == "mcq":
            # Extract only the first part of the user's answer (e.g., "B. Query Transformation" -> "B")
            user_answer = str(ans).strip().split(".")[0].lower()  # Extract the letter before the dot
            correct_answer = str(q["correct_answer"]).strip().lower()
            
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