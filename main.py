import os
import tkinter as tk
from tkinter import filedialog
from dotenv import load_dotenv
from groq import Groq
from pdfminer.high_level import extract_text

# Load API key from .env file
api_key = "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"
client = Groq(api_key=api_key)


def choose_pdf():
    """Opens a file picker to select a PDF file."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select a Resume PDF",
        filetypes=[("PDF files", "*.pdf")]
    )
    return file_path

def analyze_resume(pdf_path, job_title):
    """Extracts text from PDF and checks match for a given job title."""
    
    # Extract text from PDF
    resume_text = extract_text(pdf_path)
    
    # Send to Groq API
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are an expert ATS analyzer."},
            {"role": "user", "content": f"Analyze this resume for a {job_title} job:\n{resume_text}"}
        ]
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    print("📂 Select a resume PDF file...")
    resume_path = choose_pdf()
    
    if not resume_path:
        print("❌ No file selected. Exiting.")
        exit()

    job_title = input("Enter the job title: ")
    
    print("\n⏳ Analyzing resume... Please wait.\n")
    result = analyze_resume(resume_path, job_title)
    
    print("\n📊 Resume Analysis Result:\n", result)

