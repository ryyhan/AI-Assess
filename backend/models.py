from pydantic import BaseModel

class EvaluationRequest(BaseModel):
    questions: list
    user_answers: list
    score: float = 0.0
    feedback: list = []

class KeywordRequest(BaseModel):
    keyword: str
    num_mcqs: int
    num_subjective: int
    difficulty: str
