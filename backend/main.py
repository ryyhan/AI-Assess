from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import json
import re

from dotenv import load_dotenv

from .models import EvaluationRequest, KeywordRequest
from .services.question_service import call_openai_api, generate_questions_from_text
from .utils.utils import extract_text_from_pdf, normalize_options
from .services.evaluation_service import evaluate_answers
from .services.pdf_service import generate_pdf_report

load_dotenv()

app = FastAPI()

def process_generated_questions(response):
    if "error" in response:
        raise HTTPException(status_code=400, detail=response["error"])
    for q in response["questions"]:
        if q["type"] == "mcq":
            q["options"] = normalize_options(q["options"])
            q["correct_answer"] = normalize_options([q["correct_answer"]])[0]
    return response

@app.post("/generate-test")
async def generate_test_endpoint(pdf: UploadFile = File(None), difficulty: str = "medium", num_mcqs: int = 2, num_subjective: int = 1):
    if not pdf:
        raise HTTPException(400, "Upload a PDF file")

    text = extract_text_from_pdf(pdf.file)
    questions = generate_questions_from_text(text, num_mcqs, num_subjective, difficulty)
    return process_generated_questions(questions)

@app.post("/generate-from-keyword")
async def generate_from_keyword_endpoint(request: KeywordRequest):
    keyword = request.keyword.strip()
    num_mcqs = request.num_mcqs
    num_subjective = request.num_subjective
    difficulty = request.difficulty

    if num_mcqs + num_subjective > 10:
        raise HTTPException(status_code=400, detail="Maximum total number of questions allowed is 10.")

    if difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="Invalid difficulty level. Must be 'easy', 'medium', or 'hard'.")

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

    response = call_openai_api(prompt)
    return process_generated_questions(response)

@app.post("/evaluate-answers")
async def evaluate_answers_endpoint(request: EvaluationRequest):
    score, feedback = evaluate_answers(request.questions, request.user_answers)
    pdf_report = generate_pdf_report(request.questions, request.user_answers, score, feedback)
    return {"score": round(score, 2), "feedback": feedback, "pdf_report": pdf_report.body.decode('latin-1')}

