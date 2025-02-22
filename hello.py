import streamlit as st
import os
from openai import OpenAI
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OpenAI API Key is missing! Please check your .env file.")
    st.stop()  # Stop execution if API key is missing

# Initialize OpenAI Client
client = OpenAI(api_key=api_key)

# Function to extract text from the uploaded PDF
def extract_resume_text(pdf_file):
    try:
        text = extract_text(pdf_file)
        return text[:3000] if text else "No text found in PDF."
    except Exception as e:
        return f"PDF Error: {str(e)}"

# Function to analyze resume using OpenAI GPT-4o
def analyze_resume(pdf_file, job_title):
    try:
        if not pdf_file:
            return "", "", "", "", "", "Please upload a resume PDF."

        resume_text = extract_resume_text(pdf_file)
        if "Error" in resume_text:
            return "", "", "", "", "", resume_text

        prompt = f"""
Analyze this resume for a {job_title} position. Provide analysis in EXACT format:

**STRENGTHS**
- [Strength 1]
- [Strength 2]

**WEAKNESSES**
- [Weakness 1]
- [Weakness 2]

**REQUIRED IMPROVEMENTS**
1. [Improvement 1]
2. [Improvement 2]

**ATS SCORE**
[XX]/100

**REASONING**
- [Reason 1]
- [Reason 2]

Resume Content: {resume_text}
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )

        result = response.choices[0].message.content
        return parse_response(result)

    except Exception as e:
        return "", "", "", "", "", f"API Error: {str(e)}"

# Function to parse API response
def parse_response(response):
    try:
        sections = {
            "strengths": "",
            "weaknesses": "",
            "required improvements": "",
            "ats score": "",
            "reasoning": ""
        }

        current_section = None
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            if line.lower().startswith("**") and line.lower().endswith("**"):
                section_name = line.strip("*").strip().lower()
                if section_name in sections:
                    current_section = section_name
                continue

            if current_section and line and not line.startswith("**"):
                sections[current_section] += f"{line}\n"

        return (
            sections["strengths"].strip(),
            sections["weaknesses"].strip(),
            sections["required improvements"].strip(),
            sections["ats score"].split("/")[0].strip(),
            sections["reasoning"].strip(),
            ""
        )

    except Exception as e:
        return "", "", "", "", "", f"Parsing Error: {str(e)}\n\nRaw Response:\n{response}"

# Streamlit UI
st.set_page_config(page_title="Cyber Resume Analyzer", layout="wide")

# Sidebar for file upload and job title input
with st.sidebar:
    st.title("📄 Resume Analyzer")
    st.subheader("Upload your resume and enter job title")

    uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
    job_title = st.text_input("🎯 Target Job Title", placeholder="e.g., Data Scientist")
    analyze_btn = st.button("Analyze Resume")

# Main content area
st.title("⚡ AI powered Resume Analyzer ")

if analyze_btn and uploaded_file and job_title:
    with st.spinner("Analyzing your resume... 🚀"):
        strengths, weaknesses, improvements, ats_score, reasoning, error_msg = analyze_resume(uploaded_file, job_title)

    if error_msg:
        st.error(error_msg)
    else:
        # Display strengths
        st.subheader("🔷 Key Strengths")
        st.success(strengths)

        # Display weaknesses
        st.subheader("🔶 Critical Weaknesses")
        st.warning(weaknesses)

        # Display required improvements
        st.subheader("⚙️ Required Optimizations")
        st.info(improvements)

        # Display ATS Score
        st.subheader("📊 ATS Compatibility Score")
        ats_score = int(ats_score) if ats_score.isdigit() else 0
        st.progress(ats_score / 100)
        st.markdown(f"### Score: **{ats_score}/100**")

        # Display reasoning
        st.subheader("🛠️ Conclusion")
        st.text_area("Reasoning", reasoning, height=200)

elif not uploaded_file or not job_title:
    st.warning("Please upload a resume and enter a job title to proceed.")

# Footer
st.markdown("---")
st.markdown("<center>🔹 Built with ❤️ using Streamlit 🔹</center>", unsafe_allow_html=True)
