import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Extract text from uploaded PDF
def extract_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

# Get Gemini response
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2}
    )
    return response.text

# Try to parse Gemini response as JSON
def try_parse_json(response_text):
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None

# Prompt template
prompt_template = """
You are an ATS (Applicant Tracking System) evaluator with expertise in the tech job market.

Compare the following RESUME with the JOB DESCRIPTION and return only a **valid JSON** object using this format:

{{
  "JD Match": "85%",
  "Missing Keywords": ["keyword1", "keyword2", ...],
  "Profile Summary": "Summarize the resume in 4-5 sentences and offer specific suggestions to improve it."
}}

⚠️ Do NOT add anything outside this JSON. No explanations, greetings, or formatting.

RESUME:
{text}

JOB DESCRIPTION:
{jd}
"""

# ------------------------- Streamlit UI -------------------------
st.set_page_config(page_title="ResumeBoost", page_icon="resumeboost.png", layout="centered")

# Custom CSS for light blue theme
st.markdown("""
    <style>
        .stApp {
            background-color: #e6f0fa;  /* very light blue background */
        }
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
            color: #1a237e; /* dark blue text */
        }
        h1 {
            color: #0d47a1;  /* strong blue */
        }
        .subtitle {
            color: #1976d2;  /* medium blue */
            font-size: 1rem;
            margin-top: -10px;
            font-style: italic;
        }
        .stTextInput, .stTextArea, .stFileUploader {
            background-color: white;
            border-radius: 10px;
            padding: 5px;
            border: 1px solid #90caf9; /* light blue border */
        }
        .stButton > button {
            background-color: #2196f3; /* bright blue */
            color: white;
            font-weight: bold;
            border-radius: 12px;
            padding: 10px 26px;
            font-size: 16px;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background-color: #1565c0; /* darker blue on hover */
        }
        .metric {
            font-size: 1.3rem !important;
            color: #0d47a1 !important; /* dark blue */
        }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div style="text-align:center; margin-top: -20px;">
            <h1 style="margin-bottom: 0;">ResumeBoost</h1>
            <p class="subtitle" style="margin-top: -8px;">by Hirize</p>
            <p style="font-size:1.05rem; color:gray; margin-top: -5px;">
                Boost your resume's chances using smart AI matching
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Job Description Input
with st.container():
    st.markdown("### 📋 Job Description")
    jd = st.text_area(
        "Paste the job description you're targeting:",
        height=180,
        placeholder="Example: Seeking a backend engineer with Python, SQL, Docker, and AWS experience..."
    )

# Resume Upload
with st.container():
    st.markdown("### 📎 Upload Your Resume")
    uploaded_file = st.file_uploader(
        "Only PDF files are supported",
        type="pdf",
        help="Your resume will be parsed securely"
    )

# Submit Button in Center
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submit = st.button("Analyze Resume", use_container_width=True)

# Output Section
if submit:
    if uploaded_file and jd.strip():
        with st.spinner("🔍 Matching your resume with the job description..."):
            resume_text = extract_pdf_text(uploaded_file)
            prompt = prompt_template.format(text=resume_text, jd=jd)
            response_text = get_gemini_response(prompt)
            result = try_parse_json(response_text)

        st.markdown("---")

        if result:
            st.success("✅ Analysis Complete")
            st.metric("📊 JD Match", result.get("JD Match", "N/A"))

            with st.expander("🧩 Missing Keywords"):
                keywords = result.get("Missing Keywords", [])
                if keywords:
                    st.markdown("These are the important keywords your resume might be missing:")
                    st.write(keywords)
                else:
                    st.write("✅ No major keywords missing!")

            with st.expander("🧠 Profile Summary & Suggestions"):
                summary = result.get("Profile Summary", "No summary found.")
                st.info(summary)

        else:
            st.error("⚠️ We couldn't parse Gemini's response properly.")
            st.markdown("### 🔍 Raw Output from Gemini:")
            st.code(response_text)

    else:
        st.warning("🚫 Please upload a resume and enter a job description before submitting.")
