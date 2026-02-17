import json
import sys
import os
from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        # Try to add a Unicode font (Arial is standard on Windows)
        try:
            self.add_font("Arial", "", "c:/windows/fonts/arial.ttf", uni=True)
            self.add_font("Arial", "B", "c:/windows/fonts/arialbd.ttf", uni=True)
            self.add_font("Arial", "I", "c:/windows/fonts/ariali.ttf", uni=True)
            self.default_font = "Arial"
        except Exception as e:
            print(f"Warning: Could not load Arial font: {e}. Fallback to default (may fail with Unicode).")
            self.default_font = "Helvetica"

    def header(self):
        self.set_font(self.default_font, 'B', 15)
        self.cell(0, 10, 'LLM Council Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.default_font, 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font(self.default_font, 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, label, 0, 1, 'L', True)
        self.ln(4)

    def chapter_body(self, text):
        self.set_font(self.default_font, '', 11)
        # simplistic markdown clean up for now
        cleaned_text = text.replace('**', '').replace('##', '').replace('###', '')
        self.multi_cell(0, 5, cleaned_text)
        self.ln()

def generate_pdf(json_path, output_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON at {json_path}")
        return

    pdf = PDFReport()
    pdf.add_page()
    
    # Title and Meta
    pdf.set_font(pdf.default_font, 'B', 16)
    pdf.cell(0, 10, data.get('title', 'Untitled Conversation'), 0, 1, 'L')
    pdf.set_font(pdf.default_font, '', 10)
    pdf.cell(0, 10, f"ID: {data.get('id', 'N/A')}", 0, 1, 'L')
    pdf.cell(0, 10, f"Date: {data.get('created_at', 'N/A')}", 0, 1, 'L')
    pdf.ln(10)

    # Process Messages
    messages = data.get('messages', [])
    
    # 1. User Query
    user_msgs = [m for m in messages if m.get('role') == 'user']
    if user_msgs:
        pdf.chapter_title("User Query")
        for msg in user_msgs:
             pdf.chapter_body(msg.get('content', ''))
    
    # 2. Final Synthesis (Stage 3)
    assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
    
    for msg in assistant_msgs:
        # Stage 3 - Final Response
        if 'stage3' in msg and msg['stage3']:
            pdf.chapter_title("Final Council Response")
            stage3 = msg['stage3']
            if isinstance(stage3, dict):
                 pdf.chapter_body(stage3.get('response', ''))
            else:
                 # fallback if structure differs
                 pdf.chapter_body(str(stage3))

        # Stage 1 - Individual Responses (Appendix)
        if 'stage1' in msg and msg['stage1']:
            pdf.add_page()
            pdf.chapter_title("Appendix: Individual Model Responses")
            for resp in msg['stage1']:
                model_name = resp.get('model', 'Unknown Model')
                pdf.set_font(pdf.default_font, 'B', 10)
                pdf.cell(0, 6, f"Model: {model_name}", 0, 1)
                pdf.chapter_body(resp.get('response', ''))
                pdf.ln(5)

    try:
        pdf.output(output_path)
        print(f"Successfully generated PDF at: {output_path}")
    except Exception as e:
        print(f"Error saving PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <path_to_json> [output_path]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Default output name
        base_name = os.path.basename(input_file).replace('.json', '.pdf')
        output_file = os.path.join(os.path.dirname(input_file), base_name)
    
    generate_pdf(input_file, output_file)
