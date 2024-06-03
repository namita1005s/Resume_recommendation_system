import docx2txt
import os 

def extract_text_from_docx(docx_path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docx_path = os.path.join(base_dir, docx_path)
    txt = docx2txt.process(docx_path)
    if txt:
        return txt.replace('\t', ' ')
    return None


if __name__ == '__main__':
    print(extract_text_from_docx('./resume.docx'))  # noqa: T001