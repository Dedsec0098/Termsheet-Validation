import os
import pandas as pd
import docx
import PyPDF2
from typing import Dict, Any, Tuple, BinaryIO, Optional
import tempfile
import mimetypes
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def detect_file_type(file_obj: BinaryIO) -> str:
    """Detect the file type from the file extension, content type, or content."""
    # Debug the file object
    logger.debug(f"File object details: {dir(file_obj)}")
    logger.debug(f"File name: {getattr(file_obj, 'filename', None) or getattr(file_obj, 'name', 'Unknown')}")
    
    # Try to get filename from the file object (handle different attributes)
    filename = None
    if hasattr(file_obj, 'filename') and file_obj.filename:
        filename = file_obj.filename
    elif hasattr(file_obj, 'name') and file_obj.name:
        filename = file_obj.name
    
    logger.debug(f"Detected filename: {filename}")
    
    # Get content type if available
    content_type = getattr(file_obj, 'content_type', None)
    logger.debug(f"Content type: {content_type}")
    
    # If we have a filename with extension, use that first
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        logger.debug(f"File extension: {ext}")
        
        if ext:
            if ext == '.pdf':
                return 'pdf'
            elif ext in ['.doc', '.docx']:
                return 'word'
            elif ext in ['.xls', '.xlsx', '.csv']:
                return 'excel'
            elif ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']:
                return 'image'
    
    # If content type is available, use that
    if content_type:
        if 'pdf' in content_type:
            return 'pdf'
        elif 'word' in content_type or 'document' in content_type:
            return 'word'
        elif 'excel' in content_type or 'spreadsheet' in content_type or 'csv' in content_type:
            return 'excel'
        elif 'image' in content_type:
            return 'image'
    
    # Try to identify the file type from its content
    try:
        # Save the current position
        current_position = file_obj.tell()
        # Read the first few bytes to determine file type
        header = file_obj.read(8)
        file_obj.seek(current_position)  # Reset position
        
        logger.debug(f"File header bytes: {header[:8]}")
        
        # Check common file signatures
        if header.startswith(b'%PDF'):
            return 'pdf'
        elif header.startswith(b'\x89PNG'):
            return 'image'
        elif header.startswith(b'\xFF\xD8'):
            return 'image'  # JPEG
        elif b'PK\x03\x04' in header:  # ZIP-based formats like DOCX, XLSX
            # Look deeper into the file for Office formats
            if filename:
                if '.docx' in filename.lower():
                    return 'word'
                elif '.xlsx' in filename.lower():
                    return 'excel'
            # Default to Excel for zip-based formats if not specified
            return 'excel'
        
    except Exception as e:
        logger.error(f"Error identifying file type from content: {e}")
    
    # If we get here and still have a filename, make a guess based on mime type
    if filename:
        mime_type, _ = mimetypes.guess_type(filename)
        logger.debug(f"Guessed mime type: {mime_type}")
        
        if mime_type:
            if 'pdf' in mime_type:
                return 'pdf'
            elif 'word' in mime_type or 'document' in mime_type:
                return 'word'
            elif 'excel' in mime_type or 'spreadsheet' in mime_type or 'csv' in mime_type:
                return 'excel'
            elif 'image' in mime_type:
                return 'image'
    
    # If we have filename but couldn't determine type, try a simple extension check again
    if filename:
        lower_filename = filename.lower()
        if '.pdf' in lower_filename:
            return 'pdf'
        elif '.doc' in lower_filename or '.docx' in lower_filename:
            return 'word'
        elif '.xls' in lower_filename or '.xlsx' in lower_filename or '.csv' in lower_filename:
            return 'excel'
        elif any(img_ext in lower_filename for img_ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']):
            return 'image'
    
    # Last resort - return a default type if we can't determine
    logger.warning("Could not determine file type, defaulting to 'excel'")
    return 'excel'  # Default to excel as most master sheets are likely excel files

def save_uploaded_file(file_obj: BinaryIO) -> str:
    """Save an uploaded file to a temporary location and return the path."""
    # Get filename, with fallbacks
    filename = getattr(file_obj, 'filename', None) or getattr(file_obj, 'name', 'unknown_file')
    
    # Ensure the filename has an extension
    if '.' not in filename:
        # Try to determine an appropriate extension
        extension = '.dat'  # Default binary data
        mimetype = getattr(file_obj, 'content_type', '')
        
        if mimetype:
            if 'pdf' in mimetype:
                extension = '.pdf'
            elif 'spreadsheet' in mimetype or 'excel' in mimetype:
                extension = '.xlsx'
            elif 'document' in mimetype:
                extension = '.docx'
            elif 'image' in mimetype:
                extension = '.jpg'
        
        filename += extension
    
    # Create a temporary file with the determined filename
    base_name = os.path.basename(filename)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(base_name)[1])
    
    # Read and write the file content
    temp_file.write(file_obj.read())
    temp_file.close()
    
    logger.debug(f"Saved file to {temp_file.name}")
    return temp_file.name

def handle_input_files(term_sheet: BinaryIO, master_sheet: BinaryIO) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process uploaded term sheet and master sheet files.
    Returns metadata about each file including the path and file type.
    """
    # Log file information for debugging
    term_sheet_filename = getattr(term_sheet, 'filename', None) or getattr(term_sheet, 'name', 'Unknown')
    master_sheet_filename = getattr(master_sheet, 'filename', None) or getattr(master_sheet, 'name', 'Unknown')
    
    logger.debug(f"Processing term sheet: {term_sheet_filename}")
    logger.debug(f"Processing master sheet: {master_sheet_filename}")
    
    # Save files first, then detect type (more reliable)
    term_sheet_path = save_uploaded_file(term_sheet)
    term_sheet.seek(0)  # Reset file position for type detection
    
    master_sheet_path = save_uploaded_file(master_sheet)
    master_sheet.seek(0)  # Reset file position for type detection
    
    term_sheet_info = {
        'type': detect_file_type(term_sheet),
        'path': term_sheet_path,
        'filename': term_sheet_filename
    }
    
    master_sheet_info = {
        'type': detect_file_type(master_sheet),
        'path': master_sheet_path,
        'filename': master_sheet_filename
    }
    
    logger.debug(f"Term sheet info: {term_sheet_info}")
    logger.debug(f"Master sheet info: {master_sheet_info}")
    
    return term_sheet_info, master_sheet_info

def cleanup_temp_files(file_paths: list) -> None:
    """Remove temporary files after processing."""
    for path in file_paths:
        try:
            os.unlink(path)
        except Exception as e:
            logger.error(f"Error removing temporary file {path}: {e}")