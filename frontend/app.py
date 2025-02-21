import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

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
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    num_mcqs = st.slider("Number of MCQs", min_value=0, max_value=10, value=2)
    num_subjective = st.slider("Number of Subjective Questions", min_value=0, max_value=10, value=1)

    if pdf_file and st.button("Generate Test"):
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
            st.error(f"Failed to generate questions: {response.text}")

# Section 2: Generate Test from Keyword
elif st.session_state.mode == "from_keyword":
    st.header("Generate Test from Keyword")
    keyword = st.text_input("Enter a Keyword")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    num_mcqs = st.slider("Number of MCQs", min_value=0, max_value=10, value=2)
    num_subjective = st.slider("Number of Subjective Questions", min_value=0, max_value=10, value=1)

    if keyword and st.button("Generate Questions from Keyword"):
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
            st.error(f"Failed to generate questions: {response.text}")

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
                for fb in result["feedback"]:
                    st.write(fb)
            else:
                st.error(f"Evaluation failed: {response.text}")