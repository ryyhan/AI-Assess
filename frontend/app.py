import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Initialize session state variables
if "mode" not in st.session_state:
    st.session_state.mode = "pdf"  # Default mode: Generate from PDF
if "questions" not in st.session_state:
    st.session_state.questions = []

st.title("TestForge: AI-Powered Test Generator")

# Mode selection
st.subheader("Choose Generation Mode")
mode = st.radio(
    "Select how you want to generate questions:",
    ["From PDF", "From Keyword"],
    index=0 if st.session_state.mode == "pdf" else 1,
    key="mode_selector"
)

# Update session state based on mode selection
st.session_state.mode = mode.lower().replace(" ", "_")

# Section 1: Generate Test from PDF
if st.session_state.mode == "from_pdf":
    st.header("Generate Test from PDF")
    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key="pdf_difficulty")
    num_mcqs = st.slider("Number of MCQs", min_value=0, max_value=10, value=2, key="pdf_num_mcqs")
    num_subjective = st.slider("Number of Subjective Questions", min_value=0, max_value=10, value=1, key="pdf_num_subjective")

    if pdf_file and st.button("Generate Test"):
        with st.spinner("Generating questions from PDF..."): # Loading indicator
            response = requests.post(
                f"{BACKEND_URL}/generate-test",
                files={"pdf": pdf_file.getvalue()},
                data={
                    "difficulty": difficulty,
                    "num_mcqs": num_mcqs,
                    "num_subjective": num_subjective
                }
            )
            
            if response.status_code == 200:
                st.session_state.questions = response.json()["questions"]
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Failed to generate questions: {error_detail}") # Improved error message

# Section 2: Generate Test from Keyword
elif st.session_state.mode == "from_keyword":
    st.header("Generate Test from Keyword")
    keyword = st.text_input("Enter a Keyword")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key="keyword_difficulty")
    num_mcqs = st.slider("Number of MCQs", min_value=0, max_value=10, value=2, key="keyword_num_mcqs")
    num_subjective = st.slider("Number of Subjective Questions", min_value=0, max_value=10, value=1, key="keyword_num_subjective")

    if keyword and st.button("Generate Questions from Keyword"):
        with st.spinner("Generating questions from keyword..."): # Loading indicator
            response = requests.post(
                f"{BACKEND_URL}/generate-from-keyword",
                json={
                    "keyword": keyword,
                    "num_mcqs": num_mcqs,
                    "num_subjective": num_subjective,
                    "difficulty": difficulty
                }
            )
            
            if response.status_code == 200:
                st.session_state.questions = response.json()["questions"]
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Failed to generate questions: {error_detail}") # Improved error message

# Section 3: Display and Evaluate Test
if st.session_state.questions:
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

    st.subheader("Copy Questions")
    questions_text = "\n\n".join([f"Q{i+1}: {q['question']}\nOptions: {', '.join(q['options']) if q['type'] == 'mcq' else ''}" for i, q in enumerate(st.session_state.questions)])
    st.text_area("Generated Questions (Copyable)", questions_text, height=300)
    
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
                st.success(f"Score: {result['score']}/{len(st.session_state.questions)}")
                for fb in result['feedback']:
                    st.write(fb)

                # Download Report Button
                st.download_button(
                    label="Download Report",
                    data=requests.post(
                        f"{BACKEND_URL}/generate-pdf-report",
                        json={
                            "questions": st.session_state.questions,
                            "user_answers": user_answers,
                            "score": result['score'],
                            "feedback": result['feedback']
                        }
                    ).content,
                    file_name="test_report.pdf",
                    mime="application/pdf"
                )
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Evaluation failed: {error_detail}")