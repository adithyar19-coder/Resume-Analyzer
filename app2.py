import gradio as gr
import os
import time
from groq import Groq
from pdfminer.high_level import extract_text

# Set API key - REPLACE WITH YOUR ACTUAL KEY
api_key = "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"  # Add your Groq API key here
client = Groq(api_key=api_key)

def extract_resume_text(pdf_file):
    try:
        text = extract_text(pdf_file)
        if text:
            print("Extracted text length:", len(text))
            return text[:3000]
        else:
            return "No text found in PDF."
    except Exception as e:
        err = f"PDF Error: {str(e)}"
        print(err)
        return err

def analyze_resume(pdf_file, job_title):
    try:
        start_time = time.time()
        print("Starting analysis...")

        if not pdf_file:
            raise ValueError("Please upload a resume PDF")

        # Step 1: PDF Extraction
        resume_text = extract_resume_text(pdf_file.name)
        if "Error" in resume_text:
            raise ValueError(resume_text)
        print("Resume text extracted.")

        # Step 2: Create Prompt
        prompt = f"""
        Analyze this resume for a {job_title} position. Provide:
        1. Missing skills with explanations (formatted as bullet points)
        2. Improvement recommendations
        3. ATS score breakdown
        
        Resume Content: {resume_text}
        
        Format response STRICTLY as:
        ### Missing Skills:
        - [Skill 1]: [Reason]
        
        ### Recommendations:
        - [Recommendation 1]
        
        ### ATS Breakdown:
        Technical: [score]/25
        Experience: [score]/30
        Education: [score]/20
        Keywords: [score]/15
        Formatting: [score]/10
        Total: [total]/100
        """
        print("Prompt created.")

        # Step 3: API Call with Timeout
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            timeout=30  # 30 seconds timeout
        )
        print("API call returned.")

        # Step 4: Parse Response
        result = response.choices[0].message.content
        print("API response content received.")
        parsed = parse_response(result)
        processing_time = time.time() - start_time
        # Append processing time to debug info (5th output)
        debug_info = f"Debug Info:\nProcessing Time: {processing_time:.1f}s"
        # Combine any existing debug message from parse_response with our info
        if parsed[4]:
            debug_info += "\n" + parsed[4]
        print("Parsed output:", parsed)
        # Return exactly 5 outputs
        return parsed[0], parsed[1], parsed[2], parsed[3], debug_info

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        # Return error message for all outputs
        return error_msg, error_msg, 0, {}, error_msg

def parse_response(response):
    try:
        # Parse Missing Skills
        skills_section = response.split("### Missing Skills:")[1].split("### Recommendations:")[0]
        skills = "\n".join([line.strip() for line in skills_section.split("\n") if line.strip().startswith('-')])
        
        # Parse Recommendations
        rec_section = response.split("### Recommendations:")[1].split("### ATS Breakdown:")[0]
        recommendations = "\n".join([line.strip() for line in rec_section.split("\n") if line.strip().startswith('-')])
        
        # Parse ATS Breakdown Scores
        breakdown = {}
        score_section = response.split("### ATS Breakdown:")[1]
        for line in score_section.split("\n"):
            if ":" in line and "/" in line:
                key, value = line.split(":")
                key = key.strip()
                value = value.split("/")[0].strip()
                try:
                    breakdown[key] = int(value)
                except ValueError:
                    breakdown[key] = 0
        total = breakdown.get("Total", 0)
        
        return (
            skills, 
            recommendations, 
            total,
            {
                "categories": list(breakdown.keys()),
                "scores": list(breakdown.values())
            },
            ""  # No additional debug message
        )
        
    except Exception as e:
        err = f"Parsing Error: {str(e)}"
        print(err)
        return (
            "Failed to parse results", 
            "Analysis format error", 
            0, 
            {},
            err
        )

# Custom CSS for better visual feedback
custom_css = """
.processing {color: #4a5568; padding: 20px; border-radius: 8px;}
.error {color: #e53e3e; background: #fff5f5; padding: 15px; border-radius: 8px;}
.success {color: #38a169; background: #f0fff4; padding: 15px; border-radius: 8px;}
"""

with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as app:
    gr.Markdown("""<h1 style="text-align: center">📄 Resume Analyzer</h1>""")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📌 Input Section")
            resume_input = gr.File(label="Upload PDF Resume", file_types=[".pdf"])
            job_title_input = gr.Textbox(label="Target Job Title", placeholder="e.g., Software Engineer")
            analyze_btn = gr.Button("Analyze Resume", variant="primary")

        with gr.Column(scale=2):
            status = gr.Textbox(label="Status", interactive=False, elem_classes="processing")
            
            with gr.Tab("🔍 Missing Skills"):
                skills_output = gr.Textbox(label="Required Skills", lines=6)
                
            with gr.Tab("📈 Improvements"):
                recommendations_output = gr.Textbox(label="Optimization Tips", lines=6)
            
            with gr.Group():
                gr.Markdown("### 📊 ATS Score Analysis")
                with gr.Row():
                    score_output = gr.Number(label="Total Score")
                    breakdown_plot = gr.BarPlot()
            
            debug_output = gr.Textbox(label="Debug Info", visible=True)  # For debugging; hide in production

    analyze_btn.click(
        fn=analyze_resume,
        inputs=[resume_input, job_title_input],
        outputs=[skills_output, recommendations_output, score_output, breakdown_plot, debug_output],
        api_name="analyze"
    )

if __name__ == "__main__":
    app.launch(debug=True, share=True)
