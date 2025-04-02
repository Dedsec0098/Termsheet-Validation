from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import tempfile
import pandas as pd
import json
import traceback
from werkzeug.utils import secure_filename

# Import your existing modules
from input_handler import handle_input_files, cleanup_temp_files
from ocr_extractor import DocumentExtractor
from data_structurer import DataStructurer
from validator import TermValidator
from reporter import ValidationReporter

REACT_BUILD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'build')

app = Flask(__name__, static_folder=REACT_BUILD_FOLDER)

# Configure CORS properly with specific origins and options
CORS(app, origins="*", supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())
    
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
    
@app.route('/api/validate', methods=['POST'])
def validate_termsheet():
    try:
        # Check if both files are present in the request
        if 'termsheet' not in request.files or 'mastersheet' not in request.files:
            app.logger.error("Missing required files")
            return jsonify({'error': 'Both term sheet and master sheet files are required'}), 400
        
        term_sheet = request.files['termsheet']
        master_sheet = request.files['mastersheet']
        
        # Check if files are empty
        if term_sheet.filename == '' or master_sheet.filename == '':
            app.logger.error("Empty filenames")
            return jsonify({'error': 'File names cannot be empty'}), 400
        
        # Log file info for debugging
        app.logger.info(f"Received term sheet: {term_sheet.filename}, Content-Type: {term_sheet.content_type}")
        app.logger.info(f"Received master sheet: {master_sheet.filename}, Content-Type: {master_sheet.content_type}")
        
        # Process the uploaded files
        try:
            term_sheet_info, master_sheet_info = handle_input_files(term_sheet, master_sheet)
            app.logger.debug(f"File processing successful: {term_sheet_info}, {master_sheet_info}")
        except ValueError as e:
            app.logger.error(f"Error processing files: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Unexpected error processing files: {str(e)}")
            return jsonify({'error': f"Error processing files: {str(e)}"}), 500
        
        # Process the uploaded files
        term_sheet_info, master_sheet_info = handle_input_files(term_sheet, master_sheet)
        
        # Extract text from the documents
        doc_extractor = DocumentExtractor()
        term_sheet_text = doc_extractor.extract_text(term_sheet_info)
        master_df = doc_extractor.extract_master_sheet_structure(master_sheet_info)
        
        # Structure the extracted term sheet data
        data_structurer = DataStructurer()
        extracted_terms = data_structurer.structure_data(term_sheet_text)
        
        # Normalize terms to match master sheet terminology
        normalized_terms = data_structurer.normalize_terms(extracted_terms, master_df)
        
        # Validate terms against master sheet
        validator = TermValidator()
        validation_results = validator.validate_terms(normalized_terms, master_df)
        
        # Convert DataFrame to JSON
        master_sheet_json = master_df.to_dict(orient='records')
        validation_results_json = validation_results.to_dict(orient='records')
        
        # Generate reports
        reporter = ValidationReporter()
        
        # HTML report
        html_report = reporter.generate_html_report(validation_results, term_sheet_info, master_sheet_info)
        
        # Generate PDF and Excel reports
        pdf_path = reporter.generate_pdf_report(validation_results, term_sheet_info, master_sheet_info)
        excel_path = reporter.generate_excel_report(validation_results, term_sheet_info, master_sheet_info)

        # Calculate summary statistics
        total_terms = len(validation_results)
        valid_terms = len(validation_results[validation_results['Status'] == '✅'])
        invalid_terms = len(validation_results[validation_results['Status'] == '❌'])
        unknown_terms = len(validation_results[validation_results['Status'] == '❓'])
        
        # Return results
        response = {
            'success': True,
            'masterSheetData': master_sheet_json,
            'extractedTerms': extracted_terms,
            'validationResults': validation_results_json,
            'summary': {
                'totalTerms': total_terms,
                'validTerms': valid_terms,
                'invalidTerms': invalid_terms,
                'unknownTerms': unknown_terms,
                'validPercent': (valid_terms/total_terms*100) if total_terms > 0 else 0,
                'invalidPercent': (invalid_terms/total_terms*100) if total_terms > 0 else 0,
                'unknownPercent': (unknown_terms/total_terms*100) if total_terms > 0 else 0
            },
            'extractedText': term_sheet_text[:5000] + ("..." if len(term_sheet_text) > 5000 else ""),
            'pdfReport': os.path.basename(pdf_path),
            'excelReport': os.path.basename(excel_path),
            'htmlReport': html_report
        }
        
        # Store file paths for download endpoints
        app.config['REPORT_FILES'] = {
            'pdf': pdf_path,
            'excel': excel_path
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/download/<report_type>', methods=['GET'])
def download_report(report_type):
    try:
        if report_type not in ['pdf', 'excel']:
            return jsonify({'error': 'Invalid report type'}), 400
            
        if 'REPORT_FILES' not in app.config or report_type not in app.config['REPORT_FILES']:
            return jsonify({'error': 'Report not found'}), 404
            
        report_path = app.config['REPORT_FILES'][report_type]
        
        if not os.path.exists(report_path):
            return jsonify({'error': 'Report file not found'}), 404
            
        # Set correct MIME type
        mime_type = 'application/pdf' if report_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Return the file
        return send_file(
            report_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"term_sheet_validation.{'pdf' if report_type == 'pdf' else 'xlsx'}"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)