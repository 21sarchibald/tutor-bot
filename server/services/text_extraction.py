from flask import Flask, request, jsonify 
from PyPDF2 import PdfReader


app = Flask(__name__)


@app.route('/api/extract', methods=['POST'])
def extract():
    # Get file from frontend request
    file = request.files['file']
    file_type = request.form['file_type']  # 'pdf' or 'docx', tbd
    
    # PLACEHOLDER: i need to call extraction function
    extracted_text = extract_text(file, file_type)
    
    #this goes back to frontend
    return jsonify({'text': extracted_text})

def extract_text(file, file_type):
    if file_type == 'pdf':
        return extract_text_from_pdf(file)
    elif file_type == 'docx':
        return extract_text_from_docx(file)

def extract_text_from_pdf(file):
    pdf_text = []
    reader = PyPDF2.PdfReader(file, strict=False)
    for page in reader.pages:
        content = page.extract_text()
        pdf_text.append(content)
    return pdf_text

def extract_text_from_docx(file):
    # in progress
    pass