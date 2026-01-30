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
    """
    Extract text from Word documents, handling two-column layouts.
    For resumes with left sidebar (credentials) and right main content (experience),
    we extract columns separately to preserve structure for AI parsing.
    """
    try:
        doc = Document(io.BytesIO(file_content))
        
        # First, check if document uses tables for layout (common for two-column resumes)
        has_layout_table = False
        layout_table = None
        
        for table in doc.tables:
            # Check if this looks like a layout table (typically 2 columns, spanning document)
            if len(table.columns) == 2:
                has_layout_table = True
                layout_table = table
                break
        
        if has_layout_table and layout_table:
            # Extract two-column layout with clear section markers
            left_column_text = []
            right_column_text = []
            
            for row in layout_table.rows:
                cells = row.cells
                if len(cells) >= 2:
                    # Left column - usually credentials
                    left_text = cells[0].text.strip()
                    if left_text:
                        left_column_text.append(left_text)
                    
                    # Right column - usually bio and experience
                    right_text = cells[1].text.strip()
                    if right_text:
                        right_column_text.append(right_text)
                elif len(cells) == 1:
                    # Single cell spanning - add to right
                    text = cells[0].text.strip()
                    if text:
                        right_column_text.append(text)
            
            # Also get any paragraphs outside the table (headers, footers)
            header_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    header_text.append(para.text.strip())
            
            # Combine with clear section markers to help AI understand structure
            result_parts = []
            
            if header_text:
                result_parts.append("=== DOCUMENT HEADER ===")
                result_parts.extend(header_text)
            
            if left_column_text:
                result_parts.append("\n=== LEFT COLUMN (CREDENTIALS/QUALIFICATIONS) ===")
                result_parts.append("\n".join(left_column_text))
            
            if right_column_text:
                result_parts.append("\n=== RIGHT COLUMN (BIO AND EXPERIENCE) ===")
                result_parts.append("\n".join(right_column_text))
            
            return "\n".join(result_parts)
        
        else:
            # Standard document without layout table - extract in order
            text_parts = []
            
            # Interleave paragraphs and tables in document order
            body = doc.element.body
            for child in body:
                if child.tag.endswith('p'):  # Paragraph
                    for para in doc.paragraphs:
                        if para._element == child:
                            if para.text.strip():
                                text_parts.append(para.text.strip())
                            break
                elif child.tag.endswith('tbl'):  # Table
                    for table in doc.tables:
                        if table._tbl == child:
                            for row in table.rows:
                                row_text = []
                                for cell in row.cells:
                                    if cell.text.strip():
                                        row_text.append(cell.text.strip())
                                if row_text:
                                    text_parts.append(" | ".join(row_text))
                            break
            
            # Fallback if element-based extraction didn't work
            if not text_parts:
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
