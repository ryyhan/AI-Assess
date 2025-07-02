from fpdf import FPDF
from starlette.responses import StreamingResponse
from io import BytesIO

def generate_pdf_report(questions: list, user_answers: list, score: float, feedback: list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="AI-Assess Test Report", ln=True, align="C")
    pdf.ln(10)

    for idx, (q, ans) in enumerate(zip(questions, user_answers)):
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 10, f"Q{idx+1}: {q['question']}")
        pdf.set_font("Arial", size=10)
        
        if q["type"] == "mcq":
            pdf.multi_cell(0, 10, f"Correct Answer: {q['correct_answer']}")
            pdf.multi_cell(0, 10, f"Your Answer: {ans}")
            if "Correct" in feedback[idx]:
                pdf.set_text_color(0, 128, 0) # Green
                pdf.multi_cell(0, 10, "Status: Correct")
            else:
                pdf.set_text_color(255, 0, 0) # Red
                pdf.multi_cell(0, 10, "Status: Incorrect")
            pdf.set_text_color(0, 0, 0) # Black
        else:
            pdf.multi_cell(0, 10, f"Correct Answer: {q['correct_answer']}")
            pdf.multi_cell(0, 10, f"Your Answer: {ans}")
            # For subjective questions, we don't have direct score here, so we'll just show the answers
            # The actual scoring is done in evaluate_answers endpoint
            pdf.set_text_color(0, 0, 0) # Black

        pdf.ln(5)

    # Add overall score and feedback from the evaluation request
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Overall Score: {score}/{len(questions)}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt="Feedback:", ln=True)
    pdf.set_font("Arial", size=10)
    for fb in feedback:
        pdf.multi_cell(0, 10, fb)
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    return StreamingResponse(BytesIO(pdf_output), media_type="application/pdf", headers={'Content-Disposition': 'attachment;filename="test_report.pdf"'})