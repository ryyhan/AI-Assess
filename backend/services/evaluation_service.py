import os
from fastapi import HTTPException
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_answers(questions: list, user_answers: list):
    score = 0
    feedback = []
    
    for idx, (q, ans) in enumerate(zip(questions, user_answers)):
        if q["type"] == "mcq":
            user_answer = str(ans).strip()
            correct_answer = str(q["correct_answer"]).strip()
            
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
                    model=os.getenv("OPENAI_MODEL", "gpt-4o"),  # Use environment variable for model
                    messages=[{"role": "user", "content": prompt}]
                )
                points = float(response.choices[0].message.content.strip())
                score += points
                feedback.append(f"Q{idx+1}: Scored {points:.2f}/1")
            except Exception as e:
                feedback.append(f"Q{idx+1}: Evaluation failed - {str(e)}")
    
    return {"score": round(score, 2), "feedback": feedback}