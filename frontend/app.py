import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.title("AI Test Generator")

# Test generation section
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])

if pdf_file and st.button("Generate Test"):
    response = requests.post(
        f"{BACKEND_URL}/generate-test",
        files={"pdf": pdf_file.getvalue()},
        data={"difficulty": difficulty}
    )
    
    if response.status_code == 200:
        st.session_state.questions = response.json()["questions"]
    else:
        st.error(f"Failed to generate questions: {response.text}")

# Test display and evaluation
if "questions" in st.session_state:
    st.subheader("Test")
    user_answers = []
    
    for idx, q in enumerate(st.session_state.questions):
        st.markdown(f"**Q{idx+1}**: {q['question']}")
        
        if q["type"] == "mcq":
            answer = st.radio(
                "Options", 
                q["options"], 
                key=f"q{idx}",
                index=None  # Force user to select an option
            )
        else:
            answer = st.text_area("Your Answer", key=f"q{idx}")
        
        user_answers.append(answer)
    
    if st.button("Submit Test"):
        if None in user_answers or "" in user_answers:
            st.error("Please answer all questions before submitting")
        else:
            response = requests.post(
                f"{BACKEND_URL}/evaluate-answers",
                json={
                    "questions": st.session_state.questions,
                    "user_answers": user_answers
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"Score: {result['score']}/3")
                for fb in result["feedback"]:
                    st.write(fb)
            else:
                st.error(f"Evaluation failed: {response.text}")