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
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
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

css = """
:root {
    --neon-cyan: #00f3ff;
    --neon-purple: #b362ff;
    --dark-bg: #0a0a0a;
    --section-bg: #1a1a1a;
}

body {
    background: var(--dark-bg) !important;
    color: white !important;
    font-family: 'Courier New', monospace;
}

.cyber-section {
    border: 2px solid var(--neon-cyan);
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
    background: var(--section-bg);
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.3);
    min-height: 300px;
    max-height: 400px;
    overflow-y: auto;
}

.analysis-section {
    min-height: 380px;
    max-height: 380px;
}

.cyber-title {
    color: var(--neon-cyan) !important;
    border-bottom: 2px solid var(--neon-purple);
    padding-bottom: 10px;
    margin-bottom: 15px;
    font-size: 1.2em;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.ats-score {
    font-size: 2.5em;
    color: var(--neon-purple);
    text-shadow: 0 0 10px rgba(179, 98, 255, 0.5);
    text-align: center;
    padding: 20px;
    margin: 15px 0;
}

.cyber-button {
    background: linear-gradient(45deg, var(--neon-cyan), var(--neon-purple)) !important;
    border: none !important;
    color: black !important;
    font-weight: bold !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: 0.3s !important;
}

.error-box {
    color: #ff006e !important;
    border: 2px solid #ff006e !important;
    background: rgba(255, 0, 110, 0.1) !important;
    padding: 15px !important;
    border-radius: 8px !important;
    margin-top: 20px !important;
}

.equal-columns {
    flex: 1;
    min-width: 0;
}
"""

with gr.Blocks(css=css, theme=gr.themes.Default()) as app:
    gr.Markdown("# <center>⚡ RESUME ANALYZER </center>")
    
    with gr.Row():
        with gr.Column(scale=1):
            pdf_input = gr.File(label="📁 UPLOAD RESUME", file_types=[".pdf"])
            job_input = gr.Textbox(label="🎯 TARGET POSITION", placeholder="e.g., ML Engineer")
            analyze_btn = gr.Button("ANALYZE NOW", variant="primary", elem_classes="cyber-button")

    with gr.Row():
        with gr.Column(elem_classes="equal-columns"):
            with gr.Group(elem_classes="cyber-section"):
                gr.Markdown("## 🔷 KEY STRENGTHS", elem_classes="cyber-title")
                strengths = gr.Markdown()
        
        with gr.Column(elem_classes="equal-columns"):
            with gr.Group(elem_classes="cyber-section"):
                gr.Markdown("## 🔶 CRITICAL WEAKNESSES", elem_classes="cyber-title")
                weaknesses = gr.Markdown()

    with gr.Row(equal_height=True):
        with gr.Column(elem_classes="equal-columns"):
            with gr.Group(elem_classes="cyber-section"):
                gr.Markdown("## ⚙️ REQUIRED OPTIMIZATIONS", elem_classes="cyber-title")
                improvements = gr.Markdown()
        
        with gr.Column(elem_classes="equal-columns"):
            with gr.Group(elem_classes=["cyber-section", "analysis-section"]):
                gr.Markdown("## 📊 FINAL VERDICT", elem_classes="cyber-title")
                gr.Markdown("### ATS COMPATIBILITY SCORE", elem_classes="cyber-title")
                score = gr.Markdown(elem_classes="ats-score")
                gr.Markdown("### PROCESSOR LOGS", elem_classes="cyber-title")
                reasoning = gr.Markdown()

    error = gr.Textbox(label="🚨 SYSTEM ERRORS", visible=True, elem_classes="error-box")

    analyze_btn.click(
        fn=analyze_resume,
        inputs=[pdf_input, job_input],
        outputs=[strengths, weaknesses, improvements, score, reasoning, error]
    )

if __name__ == "__main__":
    app.launch(share=True)