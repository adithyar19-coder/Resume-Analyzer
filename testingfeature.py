import streamlit as st
import os
from openai import OpenAI
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Get OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OpenAI API Key is missing! Please check your .env file.")
    st.stop()

# Initialize OpenAI Client
client = OpenAI(api_key=api_key)

def extract_resume_text(pdf_file):
    try:
        text = extract_text(pdf_file)
        return text[:5000] if text else "No text found in PDF."
    except Exception as e:
        return f"PDF Error: {str(e)}"

def calculate_ats_score(resume_text, job_title):
    try:
        ats_prompt = f"""
        Analyze this resume for ATS compatibility specifically for a {job_title} position.
        Consider these factors with weights:
        
        [SCORING CRITERIA]
        1. Keyword Match (35%): Presence of job-specific keywords and skills
        2. Formatting (25%): Proper headers, clean structure, ATS-friendly formatting
        3. Experience Relevance (20%): Relevant job experience duration and achievements
        4. Education/Certifications (10%): Relevant degrees/certifications
        5. Customization (10%): Resume tailored to target job
        
        Provide ONLY this response format:
        ATS_SCORE|XX| (replace XX with 0-100 score)
        KEYWORDS_MISSING|comma,separated,keywords|
        FORMAT_ISSUES|bullet points of formatting issues|
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an ATS scanner analyzer. Calculate precise compatibility scores."},
                {"role": "user", "content": f"Resume Content:\n{resume_text}\n\n{ats_prompt}"}
            ],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content
    
    except Exception as e:
        return f"ERROR|{str(e)}"

def parse_ats_response(response):
    try:
        score_match = re.search(r'ATS_SCORE\|(\d{1,3})\|', response)
        keywords_match = re.search(r'KEYWORDS_MISSING\|([^|]+)\|', response)
        format_match = re.search(r'FORMAT_ISSUES\|([^|]+)\|', response)

        return {
            'score': int(score_match.group(1)) if score_match else 0,
            'missing_keywords': keywords_match.group(1).split(',') if keywords_match else [],
            'format_issues': format_match.group(1).split('; ') if format_match else []
        }
    except Exception as e:
        return {'error': f"Parsing error: {str(e)}"}

def analyze_resume(pdf_file, job_title):
    try:
        resume_text = extract_resume_text(pdf_file)
        if "Error" in resume_text:
            return None, resume_text
        
        # Get ATS Analysis
        ats_response = calculate_ats_score(resume_text, job_title)
        ats_data = parse_ats_response(ats_response)
        
        if 'error' in ats_data:
            return None, ats_data['error']
        
        # Get General Feedback
        feedback_prompt = f"""
        Based on this ATS analysis:
        {ats_response}
        
        Provide detailed feedback with:
        1. Top 3 strengths
        2. Top 3 improvements needed
        3. Summary of ATS optimization tips
        """
        
        feedback_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Convert ATS analysis into actionable feedback"},
                {"role": "user", "content": feedback_prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        return ats_data, feedback_response.choices[0].message.content
    
    except Exception as e:
        return None, f"Analysis error: {str(e)}"

# Streamlit UI
st.set_page_config(page_title="ATS Resume Analyzer", layout="wide")

# Sidebar
with st.sidebar:
    st.title("🔍 ATS Scanner")
    uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
    job_title = st.text_input("🎯 Target Job Title", placeholder="e.g., Data Analyst")
    analyze_btn = st.button("Scan Resume")

# Main Interface
st.title("📄 ATS Compatibility Analyzer")

if analyze_btn:
    if not uploaded_file or not job_title:
        st.warning("⚠️ Please upload a resume and enter a job title")
    else:
        with st.spinner("🔍 Scanning resume through ATS..."):
            ats_data, feedback = analyze_resume(uploaded_file, job_title)

        if not ats_data:
            st.error(f"Error: {feedback}")
        else:
            # Display ATS Score
            st.subheader("📊 ATS Compatibility Score")
            score = ats_data['score']
            progress = score/100
            color = "red" if score < 50 else "orange" if score < 75 else "green"
            
            st.markdown(f"""
            <div style="background-color: {color}; 
                        padding: 20px; 
                        border-radius: 10px;
                        text-align: center;
                        color: white;">
                <h1 style="margin: 0;">{score}/100</h1>
                <p style="margin: 0;">ATS Compatibility</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed Analysis
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("❌ Missing Keywords")
                if ats_data['missing_keywords']:
                    for kw in ats_data['missing_keywords'][:5]:
                        st.error(f"- {kw.strip()}")
                else:
                    st.success("✅ All key keywords present!")
                
                st.subheader("📝 Formatting Issues")
                if ats_data['format_issues']:
                    for issue in ats_data['format_issues'][:3]:
                        st.warning(f"- {issue.strip()}")
                else:
                    st.success("✅ Good ATS formatting!")
            
            with col2:
                st.subheader("📋 Optimization Feedback")
                st.info(feedback)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center;'>🔹 Powered by OpenAI GPT-3.5 Turbo 🔹</div>", unsafe_allow_html=True)