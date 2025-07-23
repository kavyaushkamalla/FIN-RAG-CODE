import PyPDF2

def extract_text_from_pdf(uploaded_file):
    from PyPDF2 import PdfReader
    reader = PdfReader(uploaded_file)
    full_text = ""
    seen_pages = set()

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text not in seen_pages:
            full_text += text + "\n"
            seen_pages.add(text)
    return full_text

'''
import pdfplumber
def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])
'''
