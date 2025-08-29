from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models import EvaluationRequest, KeywordRequest
from ..services.question_service import call_openai_api, generate_questions_from_text
from ..utils.utils import extract_text_from_pdf, normalize_options
from ..services.evaluation_service import evaluate_answers
from ..services.pdf_service import generate_pdf_report
from ..prompts import get_keyword_prompt

router = APIRouter()

def process_generated_questions(response):
    if "error" in response:
        raise HTTPException(status_code=400, detail=response["error"])
    for q in response["questions"]:
        if q["type"] == "mcq":
            q["options"] = normalize_options(q["options"])
            q["correct_answer"] = normalize_options([q["correct_answer"]])[0]
    return response

@router.post("/generate-test")
async def generate_test_endpoint(pdf: UploadFile = File(None), difficulty: str = "medium", num_mcqs: int = 2, num_subjective: int = 1):
    if not pdf:
        raise HTTPException(400, "Upload a PDF file")

    text = extract_text_from_pdf(pdf.file)
    questions = generate_questions_from_text(text, num_mcqs, num_subjective, difficulty)
    return process_generated_questions(questions)

@router.post("/generate-from-keyword")
async def generate_from_keyword_endpoint(request: KeywordRequest):
    keyword = request.keyword.strip()
    num_mcqs = request.num_mcqs
    num_subjective = request.num_subjective
    difficulty = request.difficulty

    if num_mcqs + num_subjective > 10:
        raise HTTPException(status_code=400, detail="Maximum total number of questions allowed is 10.")

    if difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="Invalid difficulty level. Must be 'easy', 'medium', or 'hard'.")

    prompt = get_keyword_prompt(num_mcqs, num_subjective, difficulty, keyword)

    response = call_openai_api(prompt)
    return process_generated_questions(response)

@router.post("/evaluate-answers")
async def evaluate_answers_endpoint(request: EvaluationRequest):
    evaluation_result = evaluate_answers(request.questions, request.user_answers)
    score = evaluation_result["score"]
    feedback = evaluation_result["feedback"]
    pdf_content, pdf_stream = generate_pdf_report(request.questions, request.user_answers, score, feedback)
    return {"score": round(score, 2), "feedback": feedback, "pdf_report": pdf_content.decode('latin-1')}
