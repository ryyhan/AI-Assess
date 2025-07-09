
def get_keyword_prompt(num_mcqs: int, num_subjective: int, difficulty: str, keyword: str) -> str:
    return f"""
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
