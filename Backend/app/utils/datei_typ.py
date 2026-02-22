from pdfminer.high_level import extract_text
from docx import Document
import xlrd


def extract_text_from_pdf(file_path):
    try:
        return extract_text(file_path)
    except Exception as e:
        return f"Fehler beim Extrahieren von PDF: {str(e)}"

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Fehler beim Extrahieren von DOCX: {str(e)}"

def extract_text_from_xlsx(file_path):
    try:
        workbook = xlrd.open_workbook(file_path)
        sheet = workbook.sheet_by_index(0)
        return "\n".join(["\t".join(map(str, sheet.row_values(row))) for row in range(sheet.nrows)])
    except Exception as e:
        return f"Fehler beim Extrahieren von XLSX: {str(e)}"