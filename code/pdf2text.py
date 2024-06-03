from pdfminer.high_level import extract_text
import os

def extract_text_from_pdf(pdf_path):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(base_dir, pdf_path)
        print('Extracting text from PDF file:', pdf_path)
        return extract_text(pdf_path)
    except Exception as e:
        print('Error extracting text from PDF file:', e)
        return "no result found"


if __name__ == '__main__':
    print(extract_text_from_pdf(r'C:\Users\Namita\OneDrive\Desktop\major_project\code\static\upload\Teacher_Resume_Samples_.pdf'))