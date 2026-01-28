import io
import os
from typing import Optional
from docx import Document
from pypdf import PdfReader
from openpyxl import load_workbook


def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_content))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_content))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    text_parts.append(" | ".join(row_text))
        
        return "\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {str(e)}")


def extract_text_from_excel(file_content: bytes) -> str:
    try:
        wb = load_workbook(io.BytesIO(file_content), data_only=True)
        text_parts = []
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            text_parts.append(f"=== Sheet: {sheet_name} ===")
            
            for row in sheet.iter_rows(values_only=True):
                row_values = [str(cell) if cell is not None else "" for cell in row]
                if any(v.strip() for v in row_values):
                    text_parts.append(" | ".join(row_values))
        
        return "\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to parse Excel: {str(e)}")


def extract_text_from_file(filename: str, file_content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_content)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_content)
    elif ext in ['.xlsx', '.xls']:
        return extract_text_from_excel(file_content)
    elif ext == '.txt':
        return file_content.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file format: {ext}")
