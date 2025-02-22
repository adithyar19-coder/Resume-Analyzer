import gradio as gr
import os
from groq import Groq
from pdfminer.high_level import extract_text
from pathlib import Path

# Set API key (replace with your actual API key)
api_key = ""
client = Groq(api_key=api_key)

# Function to extract text from PDF
def extract_resume_text(pdf_file):
    text = extract_text(pdf_file)
    return text if text else "No text found in the PDF."

# Function to analyze resume using Groq API
def analyze_resume(pdf_file, job_title):
    if not pdf_file:
        return "Please upload a resume.", "", 0

    # Extract text from the PDF
    resume_text = extract_resume_text(pdf_file.name)

    # Generate a prompt for Llama 3 to compare the resume with the job title
    prompt = f"""
    Analyze this resume for a {job_title} position. Provide:
    1. Missing technical skills (comma-separated)
    2. Improvement recommendations (bulleted list)
    3. ATS compatibility score (0-100 number only)
    
    Resume: {resume_text}
    
    Format response as:
    Missing Skills: [skills]
    Recommendations: [bullets]
    ATS Score: [number]
    """

    # Call Groq API (Llama 3 model)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract response
    result = response.choices[0].message.content
    return parse_response(result)

# Function to parse the API response
def parse_response(response):
    skills = ""
    recommendations = ""
    score = 0
    
    try:
        parts = response.split("Recommendations:")
        skills_part = parts[0].split("Missing Skills:")[1].strip()
        skills = ", ".join([s.strip() for s in skills_part.split(",")])
        
        rec_part = parts[1].split("ATS Score:")[0].strip()
        recommendations = "\n".join([f"• {r.strip()}" for r in rec_part.split("•") if r.strip()])
        
        score = int(parts[1].split("ATS Score:")[1].strip())
    except:
        return "Error parsing response", "", 0
    
    return skills, recommendations, score

# Custom CSS for styling
custom_css = """
#title {text-align: center; color: #2B6CB0;}
.section {padding: 20px; border-radius: 10px; background: #f8f9fa; margin: 10px 0;}
.score-container {background: white; padding: 15px; border-radius: 10px; text-align: center;}
.score-number {font-size: 48px; font-weight: bold; color: #2B6CB0;}
"""

# Build the Gradio UI
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as app:
    gr.Markdown("""<h1 id="title">📄 Smart Resume Analyzer</h1>""")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📌 Upload Resume")
            resume_input = gr.File(label="PDF Only", file_types=[".pdf"])
            job_title_input = gr.Textbox(label="🔍 Target Job Title", placeholder="e.g., Software Engineer")
            analyze_btn = gr.Button("Analyze Now →", variant="primary")

        with gr.Column(scale=2):
            gr.Markdown("## 📊 Analysis Results")
            with gr.Tab("Missing Skills"):
                skills_output = gr.Textbox(label="🔎 Key Skills to Add", interactive=False)
            with gr.Tab("Improvements"):
                recommendations_output = gr.Textbox(label="💡 Optimization Tips", interactive=False, lines=6)
            
            with gr.Group():
                gr.Markdown("### 🎯 ATS Compatibility Score")
                with gr.Row():
                    score_output = gr.Number(label="Score", elem_classes="score-number")
                    gr.BarPlot(label="Score Breakdown", 
                              x=["ATS Score"], 
                              y=[0], 
                              color=["#2B6CB0"],
                              height=200,
                              width=100)

    # Interactive examples (fixed to avoid file errors)
    gr.Examples(
        examples=[
            [None, "Data Scientist"],
            [None, "Product Manager"],
            [None, "UX Designer"]
        ],
        inputs=[resume_input, job_title_input],
        label="💡 Try Example Job Titles",
        examples_per_page=3
    )

    # Connect the button to the function
    analyze_btn.click(
        fn=analyze_resume,
        inputs=[resume_input, job_title_input],
        outputs=[skills_output, recommendations_output, score_output]
    )

# Run the Gradio web app
if __name__ == "__main__":
    app.launch(share=True)