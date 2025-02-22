import gradio as gr
import os
import time
from groq import Groq
from pdfminer.high_level import extract_text

# Set API key - REPLACE WITH YOUR ACTUAL KEY
api_key = ""
client = Groq(api_key=api_key)

def extract_resume_text(pdf_file):
    try:
        text = extract_text(pdf_file)
        return text[:3000] if text else "No text found in PDF."
    except Exception as e:
        return f"PDF Error: {str(e)}"

def analyze_resume(pdf_file, job_title):
    try:
        if not pdf_file:
            return "", "", "", "", "", "Please upload a resume PDF."

        resume_text = extract_resume_text(pdf_file.name)
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
            model="llama3-70b-8192",  # Corrected model name
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        print("API Response:\n", result)  # Debug print
        return parse_response(result)
    
    except Exception as e:
        return "", "", "", "", "", f"API Error: {str(e)}"

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
            # Detect section headers (case-insensitive)
            if line.lower().startswith("**") and line.lower().endswith("**"):
                section_name = line.strip("*").strip().lower()
                if section_name in sections:
                    current_section = section_name
                continue
                
            # Add content to current section
            if current_section and line and not line.startswith("**"):
                sections[current_section] += f"{line}\n"
        
        # Verify required sections
        if not sections["ats score"]:
            raise ValueError("ATS Score section missing")
            
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

css = """
.section {
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 8px;
    min-height: 200px;
    background: #f8f9fa;
    border-left: 4px solid #2B6CB0;
}
.section h2 { color: #2B6CB0; }
.score { 
    font-size: 32px; 
    font-weight: bold; 
    color: #2B6CB0;
    text-align: center;
    margin: 20px 0;
}
.error { 
    color: #e53e3e; 
    padding: 15px;
    background: #fff5f5;
    border-radius: 8px;
}
"""

with gr.Blocks(css=css) as app:
    gr.Markdown("# Professional Resume Analyzer")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
        job_input = gr.Textbox(label="Target Job Title", placeholder="e.g., Machine Learning Engineer")
    
    analyze_btn = gr.Button("Analyze Resume", variant="primary")
    
    with gr.Column():
        with gr.Row():
            with gr.Column():
                with gr.Group(elem_classes="section"):
                    gr.Markdown("## Strengths")
                    strengths = gr.Markdown()
            with gr.Column():
                with gr.Group(elem_classes="section"):
                    gr.Markdown("## Weaknesses")
                    weaknesses = gr.Markdown()
        
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group(elem_classes="section"):
                    gr.Markdown("## Required Improvements")
                    improvements = gr.Markdown()
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("## ATS Score")
                    score = gr.Markdown(elem_classes="score")
                    gr.Markdown("## Reasoning")
                    reasoning = gr.Markdown()
        
        error = gr.Markdown(elem_classes="error")

    analyze_btn.click(
        fn=analyze_resume,
        inputs=[pdf_input, job_input],
        outputs=[strengths, weaknesses, improvements, score, reasoning, error]
    )

if __name__ == "__main__":
    app.launch(share=True)