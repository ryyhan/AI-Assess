# AI-Assess: AI-Powered Test Generator

AI Assess is an AI-powered tool designed to generate tests (MCQs and subjective questions) from uploaded PDF files or keywords. It also evaluates user answers and provides feedback. The application leverages OpenAI's GPT-4o model for generating questions and evaluating responses.

## Features

1. **Dynamic Question Generation**:
   - Generate questions dynamically based on user input.
   - Supports both **PDF uploads** and **keyword-based generation**.

2. **Mutually Exclusive Modes**:
   - Users can either upload a PDF or enter a keyword to generate questions, ensuring a clean and focused interface.

3. **Evaluation System**:
   - Automatically evaluates MCQs and subjective questions.
   - Provides detailed feedback and scores for submitted answers.

4. **User-Friendly Interface**:
   - Built using Streamlit for a clean and interactive frontend.
   - Easy-to-use sliders, radio buttons, and text inputs.

5. **Error Handling**:
   - Handles invalid inputs, API errors, and empty responses gracefully.

---

## Demo
- [Click here](https://youtu.be/cdadwiiSF9E)


[![AI Assess](https://img.youtube.com/vi/cdadwiiSF9E/0.jpg)]("https://youtu.be/cdadwiiSF9E")

## Installation and Setup

### Steps to Set Up

1. Clone the repository:
   ```bash
   git clone https://github.com/ryyhan/AI-Assess.git
   
   cd testforge
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Run the FastAPI backend:
   ```bash
   uvicorn main:app --reload
   ```

5. Run the Streamlit frontend:
   ```bash
   streamlit run frontend.py
   ```

6. Access the app:
   Open your browser and navigate to `http://localhost:8501`.

---

## Usage Guide

### Step 1: Choose a Mode
- Use the **radio button** at the top of the page to select between:
  - **Generate from PDF**: Upload a PDF file and specify the difficulty level and number of questions.
  - **Generate from Keyword**: Enter a keyword and specify the number of questions.

### Step 2: Generate Questions
- After selecting a mode, follow the instructions:
  - For **PDF Upload**: Upload a PDF file, choose difficulty, and set the number of questions.
  - For **Keyword Input**: Enter a keyword and set the number of questions.
- Click the "Generate" button to fetch questions.

### Step 3: Answer the Questions
- Once the questions are generated, answer them:
  - For **MCQs**, select the correct option from the radio buttons.
  - For **subjective questions**, type your answer in the text area.

### Step 4: Submit and Evaluate
- Click the "Submit Test" button to evaluate your answers.
- The app will display your score and detailed feedback for each question.

---

## Backend Endpoints

### 1. Generate Test from PDF
- **Endpoint**: `POST /generate-test`
- **Parameters**:
  - `pdf`: Uploaded PDF file.
  - `difficulty`: Difficulty level (`easy`, `medium`, `hard`).
  - `num_questions`: Number of questions to generate (max 10).
- **Response**:
  ```json
  {
      "questions": [
          {
              "type": "mcq",
              "question": "...",
              "options": ["A", "B", "C", "D"],
              "correct_answer": "A"
          },
          {
              "type": "subjective",
              "question": "...",
              "correct_answer": "..."
          }
      ]
  }
  ```

### 2. Generate Test from Keyword
- **Endpoint**: `POST /generate-from-keyword`
- **Parameters**:
  - `keyword`: Keyword to generate questions from.
  - `num_questions`: Number of questions to generate (max 10).
- **Response**:
  ```json
  {
      "questions": [
          {
              "type": "mcq",
              "question": "...",
              "options": ["A", "B", "C", "D"],
              "correct_answer": "A"
          },
          {
              "type": "subjective",
              "question": "...",
              "correct_answer": "..."
          }
      ]
  }
  ```

### 3. Evaluate Answers
- **Endpoint**: `POST /evaluate-answers`
- **Parameters**:
  - `questions`: List of generated questions.
  - `user_answers`: List of user-provided answers.
- **Response**:
  ```json
  {
      "score": 7.5,
      "feedback": [
          "Q1: Correct!",
          "Q2: Wrong. Correct: B",
          "Q3: Scored 0.80/1"
      ]
  }
  ```

---

## Technologies Used

- **Backend**:
  - FastAPI: For building the RESTful API.
  - OpenAI API: For generating questions and evaluating answers.
  - PyPDF2: For extracting text from PDF files.

- **Frontend**:
  - Streamlit: For creating an interactive web interface.

- **Other Libraries**:
  - `langchain`: For text splitting and preprocessing.
  - `requests`: For making API calls from the frontend.

---

## Future Enhancements

1. **Support for More File Formats**:
   - Extend support to other file formats like Word documents or plain text files.

2. **Advanced Evaluation Metrics**:
   - Implement more sophisticated scoring mechanisms for subjective questions.

3. **Customizable Question Types**:
   - Allow users to choose specific types of questions (e.g., only MCQs or only subjective).

4. **Export Results**:
   - Add functionality to export test results as a PDF or CSV file.

5. **Multi-Language Support**:
   - Enable question generation and evaluation in multiple languages.
