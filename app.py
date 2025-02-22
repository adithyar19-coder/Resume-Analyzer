import gradio as gr
import os
from groq import Groq
from pdfminer.high_level import extract_text

# Set API key (ensure this is securely managed in production)
api_key = ""
client = Groq(api_key=api_key)

# Function to extract text from PDF
def extract_resume_text(pdf_file):
    text = extract_text(pdf_file)
    return text if text else "No text found in the PDF."

# Function to analyze resume using Groq API
def analyze_resume(pdf_file, job_title):
    if not pdf_file:
        return "Please upload a resume."

    # Extract text from the PDF
    resume_text = extract_resume_text(pdf_file.name)

    # Generate a prompt for Llama 3 to compare the resume with the job title
    prompt = f"""
    Given the following resume text, evaluate how well it matches the job title: {job_title}. 
    Identify missing skills, required improvements, and calculate an ATS score (0-100).
    
    Resume Text:
    {resume_text}
    
    Provide a structured response with missing skills and ATS score.
    """

    # Call Groq API (Llama 3 model)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract response
    return response.choices[0].message.content

# Build the Gradio UI
with gr.Blocks() as app:
    gr.Markdown("# 📄 Resume Analyzer (ATS Check)")
    with gr.Row():
        resume_input = gr.File(label="Upload Your Resume (PDF)")
        job_title_input = gr.Textbox(label="Enter Job Title", placeholder="Software Engineer")

    analyze_button = gr.Button("Analyze Resume")
    result_output = gr.Textbox(label="Analysis Result", interactive=False)

    analyze_button.click(analyze_resume, inputs=[resume_input, job_title_input], outputs=result_output)

# Run the Gradio web app
if __name__ == "__main__":
    app.launch()
