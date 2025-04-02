import os
import pytesseract
from PIL import Image
import pandas as pd
import docx
import PyPDF2
import pdfplumber
import io
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DocumentExtractor:
    def __init__(self):
    # Initialize OCR engine
        try:
            # Try with default path
            pytesseract.pytesseract.tesseract_cmd = r'tesseract'
        except:
            # Try common Mac installation paths
            for path in ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def extract_text(self, file_info: Dict[str, Any]) -> str:
        """Extract text from various file formats."""
        file_type = file_info['type']
        file_path = file_info['path']
        
        if file_type == 'pdf':
            return self._extract_from_pdf(file_path)
        elif file_type == 'word':
            return self._extract_from_word(file_path)
        elif file_type == 'excel':
            return self._extract_from_excel(file_path)
        elif file_type == 'image':
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files."""
        try:
            # First try to extract text directly (for digital PDFs)
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                # If no text was extracted, the PDF might be scanned
                if not text.strip():
                    return self._ocr_pdf(file_path)
                return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            # Fall back to OCR
            return self._ocr_pdf(file_path)
    
    def _ocr_pdf(self, file_path: str) -> str:
        """Perform OCR on PDF pages."""
        from pdf2image import convert_from_path
        
        pages = convert_from_path(file_path, 300)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
        return text
    
    def _extract_from_word(self, file_path: str) -> str:
        """Extract text from Word documents."""
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    def _extract_from_excel(self, file_path: str) -> str:
        """Extract text from Excel files."""
        df = pd.read_excel(file_path)
        # Convert DataFrame to string representation
        return df.to_string()
    
    def _extract_from_image(self, file_path: str) -> str:
        """Perform OCR on image files."""
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)
    
    def extract_master_sheet_structure(self, file_info: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract structured data from the master sheet.
        Returns a DataFrame with terms, expected values, and allowed ranges.
        """
        file_type = file_info['type']
        file_path = file_info['path']
        
        if file_type == 'excel':
            return pd.read_excel(file_path)
        elif file_type == 'csv':
            return pd.read_csv(file_path)
        else:
            # For other formats, we'll need to parse the extracted text
            text = self.extract_text(file_info)
            # This is a simplified approach - in reality, you'd need more sophisticated parsing
            # depending on the structure of your master sheet
            return self._parse_text_to_dataframe(text)
    
    def _parse_text_to_dataframe(self, text: str) -> pd.DataFrame:
        """
        Parse extracted text into a DataFrame structure.
        This is a placeholder implementation.
        """
        # In a real implementation, you would use regex or other parsing techniques
        # to extract structured data from the text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        data = []
        
        # Simple parsing of "Term: Value" format
        for line in lines:
            if ':' in line:
                term, value = line.split(':', 1)
                data.append({
                    'Term': term.strip(),
                    'Expected Value': value.strip(),
                    'Allowed Range': ''  # This would need more sophisticated parsing
                })
        
        return pd.DataFrame(data)