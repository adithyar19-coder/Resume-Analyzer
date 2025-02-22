import gradio as gr
import os
import time
from groq import Groq
from pdfminer.high_level import extract_text

# Set API key - REPLACE WITH YOUR ACTUAL KEY
api_key = "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"
client = Groq(api_key=api_key)

def extract_resume_text(pdf_file):
    try:
        text = extract_text(pdf_file)
        return text[:3000] if text else "No text found in PDF."
    except Exception as e:
        return f"PDF Error: {str(e)}"

def analyze_resume(pdf_file, job_title):
    try:
        start_time = time.time()
        
        if not pdf_file:
            return "", "", "", "", "", "Please upload a resume PDF."

        resume_text = extract_resume_text(pdf_file.name)
        if "Error" in resume_text:
            return "", "", "", "", "", resume_text

        prompt = f"""
        Analyze this resume for a {job_title} position. Provide detailed analysis in EXACTLY this format:
        
        **Strengths:**
        - [Strength 1]
        - [Strength 2]
        
        **Weaknesses:**
        - [Weakness 1]
          + [Sub-point]
        - [Weakness 2]
        
        **Required Improvements:**
        1. [Improvement 1]
        2. [Improvement 2]
        
        **ATS Score:** [XX]/100
        
        **Reasoning:**
        - [Reason 1]
        - [Reason 2]
        
        **Suggested Improvements:**
        1. [Suggestion 1]
        2. [Suggestion 2]
        
        Resume Content: {resume_text}
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Using larger 70B model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        return parse_response(result)
    
    except Exception as e:
        return "", "", "", "", "", f"Error: {str(e)}"

def parse_response(response):
    try:
        strengths = ""
        weaknesses = ""
        improvements = ""
        score = ""
        reasoning = ""
        
        # Parse sections
        sections = response.split("**")
        for i, section in enumerate(sections):
            if "Strengths:" in section:
                strengths = "\n".join([line.strip() for line in sections[i+1].split("\n") if line.strip()])
            elif "Weaknesses:" in section:
                weaknesses = "\n".join([line.strip() for line in sections[i+1].split("\n") if line.strip()])
            elif "Required Improvements:" in section:
                improvements = "\n".join([line.strip() for line in sections[i+1].split("\n") if line.strip()])
            elif "ATS Score:" in section:
                score = sections[i+1].split("/")[0].strip()
            elif "Reasoning:" in section:
                reasoning = "\n".join([line.strip() for line in sections[i+1].split("\n") if line.strip()])
        
        return strengths, weaknesses, improvements, score, reasoning, ""

    except Exception as e:
        return "", "", "", "", "", f"Parsing Error: {str(e)}"

css = """
#main {padding: 20px;}
.section {margin-bottom: 20px; padding: 15px; border-radius: 8px;}
.strength {background: #f0fff4; border-left: 4px solid #38a169;}
.weakness {background: #fff5f5; border-left: 4px solid #e53e3e;}
.improvement {background: #fffaf0; border-left: 4px solid #dd6b20;}
.score {font-size: 24px; font-weight: bold; color: #2b6cb0;}
"""

with gr.Blocks(css=css) as app:
    gr.Markdown("# Professional Resume Analyzer")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
        job_input = gr.Textbox(label="Target Job Title", placeholder="e.g., Machine Learning Engineer")
    
    analyze_btn = gr.Button("Analyze Resume", variant="primary")
    
    with gr.Column(visible=True) as output_section:
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group(elem_classes="section strength"):
                    gr.Markdown("## Strengths")
                    strengths = gr.Markdown()
            with gr.Column(scale=1):
                with gr.Group(elem_classes="section weakness"):
                    gr.Markdown("## Weaknesses")
                    weaknesses = gr.Markdown()
        
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group(elem_classes="section improvement"):
                    gr.Markdown("## Required Improvements")
                    improvements = gr.Markdown()
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("## ATS Score")
                    score = gr.Markdown(elem_classes="score")
                    gr.Markdown("## Reasoning")
                    reasoning = gr.Markdown()
        
        error = gr.Textbox(label="Error Messages", visible=False)

    analyze_btn.click(
        fn=analyze_resume,
        inputs=[pdf_input, job_input],
        outputs=[strengths, weaknesses, improvements, score, reasoning, error]
    )

if __name__ == "__main__":
    app.launch(share=True)