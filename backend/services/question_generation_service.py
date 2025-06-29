from fastapi import HTTPException
from langchain.text_splitter import CharacterTextSplitter
from ..services.openai_service import call_openai_api
from ..utils.question_utils import normalize_options

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