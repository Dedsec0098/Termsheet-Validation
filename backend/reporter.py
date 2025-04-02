import matplotlib
matplotlib.use('Agg') 

import pandas as pd
import matplotlib.pyplot as plt
import io
from typing import Dict, Any, List
import base64
from fpdf import FPDF
import os
from datetime import datetime

class ValidationReporter:
    def __init__(self):
        pass
    
    def generate_html_report(self, validation_results: pd.DataFrame, 
                           term_sheet_info: Dict[str, Any], 
                           master_sheet_info: Dict[str, Any]) -> str:
        """
        Generate an HTML validation report.
        """
        # Calculate summary statistics
        total_terms = len(validation_results)
        valid_terms = len(validation_results[validation_results['Status'] == '✅'])
        invalid_terms = len(validation_results[validation_results['Status'] == '❌'])
        unknown_terms = len(validation_results[validation_results['Status'] == '❓'])
        
        # Create summary chart
        plt.figure(figsize=(8, 5))
        labels = ['Valid', 'Invalid', 'Unknown']
        sizes = [valid_terms, invalid_terms, unknown_terms]
        colors = ['#4CAF50', '#F44336', '#FFC107']
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('Term Validation Results')
        
        # Save chart to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_img = base64.b64encode(buf.read()).decode('utf-8')
        plt.close('all')
        
        # Style the results table with colors based on status
        styled_results = validation_results.style.apply(
            lambda row: ['background-color: #E8F5E9' if cell == '✅' else
                         'background-color: #FFEBEE' if cell == '❌' else
                         'background-color: #FFF8E1' if cell == '❓' else ''
                         for cell in row], 
            axis=1, subset=['Status']
        )
        
        # Generate HTML report
        html = f"""
        <html>
        <head>
            <title>Term Sheet Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .file-info {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{background-color: #f5f5f5;}}
                .chart {{ text-align: center; margin-bottom: 20px; }}
                .valid {{ color: green; }}
                .invalid {{ color: red; }}
                .unknown {{ color: orange; }}
            </style>
        </head>
        <body>
            <h1>Term Sheet Validation Report</h1>
            <div class="file-info">
                <h3>Files Analyzed</h3>
                <p><strong>Term Sheet:</strong> {term_sheet_info.get('filename', 'Unknown')}</p>
                <p><strong>Master Sheet:</strong> {master_sheet_info.get('filename', 'Unknown')}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>Validation Summary</h2>
                <p><strong>Total Terms:</strong> {total_terms}</p>
                <p><strong>Valid Terms:</strong> <span class="valid">{valid_terms}</span> ({valid_terms/total_terms*100:.1f}%)</p>
                <p><strong>Invalid Terms:</strong> <span class="invalid">{invalid_terms}</span> ({invalid_terms/total_terms*100:.1f}%)</p>
                <p><strong>Unknown Terms:</strong> <span class="unknown">{unknown_terms}</span> ({unknown_terms/total_terms*100:.1f}%)</p>
            </div>
            
            <div class="chart">
                <h2>Validation Chart</h2>
                <img src="data:image/png;base64,{chart_img}" alt="Validation Results Chart">
            </div>
            
            <h2>Detailed Results</h2>
            {styled_results.to_html()}
        </body>
        </html>
        """
        
        return html
    
    def generate_pdf_report(self, validation_results: pd.DataFrame, 
                       term_sheet_info: Dict[str, Any], 
                       master_sheet_info: Dict[str, Any]) -> str:
        """
        Generate a PDF validation report and return the file path.
        """
        # Create a copy of validation results to avoid modifying the original
        pdf_results = validation_results.copy()
        
        # Replace Unicode symbols with ASCII alternatives
        pdf_results['Status'] = pdf_results['Status'].replace({
            '✅': 'PASS',
            '❌': 'FAIL',
            '❓': 'UNKNOWN'
        })
        
        # Create a PDF document
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Term Sheet Validation Report', 0, 1, 'C')
        
        # File information
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Term Sheet: {term_sheet_info.get('filename', 'Unknown')}", 0, 1)
        pdf.cell(0, 10, f"Master Sheet: {master_sheet_info.get('filename', 'Unknown')}", 0, 1)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        
        # Summary statistics
        total_terms = len(pdf_results)
        valid_terms = len(validation_results[validation_results['Status'] == '✅'])
        invalid_terms = len(validation_results[validation_results['Status'] == '❌'])
        unknown_terms = len(validation_results[validation_results['Status'] == '❓'])
        
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Validation Summary', 0, 1)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Total Terms: {total_terms}", 0, 1)
        pdf.cell(0, 10, f"Valid Terms: {valid_terms} ({valid_terms/total_terms*100:.1f}%)", 0, 1)
        pdf.cell(0, 10, f"Invalid Terms: {invalid_terms} ({invalid_terms/total_terms*100:.1f}%)", 0, 1)
        pdf.cell(0, 10, f"Unknown Terms: {unknown_terms} ({unknown_terms/total_terms*100:.1f}%)", 0, 1)
        
        # Add detailed results table
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Detailed Results', 0, 1)
        
        # Define table columns and widths
        columns = ['Term', 'Extracted Value', 'Status', 'Expected Value', 'Notes']
        col_widths = [40, 35, 15, 35, 65]
        
        # Create table header
        pdf.set_font('Arial', 'B', 10)
        for i, col in enumerate(columns):
            pdf.cell(col_widths[i], 10, col, 1)
        pdf.ln()
        
        # Add table data
        pdf.set_font('Arial', '', 8)
        for _, row in pdf_results.iterrows():
            pdf.cell(col_widths[0], 10, str(row['Term'])[:25], 1)
            pdf.cell(col_widths[1], 10, str(row['Extracted Value'])[:20], 1)
            pdf.cell(col_widths[2], 10, str(row['Status']), 1)
            pdf.cell(col_widths[3], 10, str(row['Expected Value'])[:20], 1)
            
            # Make sure notes don't contain Unicode characters
            notes = str(row['Notes'])[:40]
            notes = notes.encode('latin-1', errors='replace').decode('latin-1')
            pdf.cell(col_widths[4], 10, notes, 1)
            pdf.ln()
        
        # Save the PDF to a temporary file
        output_path = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(output_path)
        
        return output_path
    
   # Replace the generate_excel_report method

    def generate_excel_report(self, validation_results: pd.DataFrame, 
                            term_sheet_info: Dict[str, Any], 
                            master_sheet_info: Dict[str, Any]) -> str:
            """
            Generate an Excel validation report and return the file path.
            """
            # Create a copy of validation results with ASCII replacements for Excel
            excel_results = validation_results.copy()
            excel_results['Status'] = excel_results['Status'].replace({
                '✅': 'PASS',
                '❌': 'FAIL',
                '❓': 'UNKNOWN'
            })
            
            # Create a Pandas Excel writer
            output_path = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            try:
                writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
            except Exception as e:
                print(f"Error creating Excel writer: {e}")
                # Fallback to using openpyxl engine
                writer = pd.ExcelWriter(output_path, engine='openpyxl')
            
            # Write the validation results to the Excel file
            excel_results.to_excel(writer, sheet_name='Validation Results', index=False)
            
            try:
                # Access the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['Validation Results']
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#D9D9D9',
                    'border': 1
                })
                
                valid_format = workbook.add_format({
                    'bg_color': '#E8F5E9',
                    'border': 1
                })
                
                invalid_format = workbook.add_format({
                    'bg_color': '#FFEBEE',
                    'border': 1
                })
                
                unknown_format = workbook.add_format({
                    'bg_color': '#FFF8E1',
                    'border': 1
                })
                
                # Apply formats to the header row
                for col_num, value in enumerate(excel_results.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Apply conditional formatting based on Status
                status_col = excel_results.columns.get_loc('Status')
                for row_num in range(1, len(excel_results) + 1):
                    orig_status = validation_results.iloc[row_num - 1]['Status']
                    status = excel_results.iloc[row_num - 1]['Status']
                    if orig_status == '✅':
                        worksheet.write(row_num, status_col, status, valid_format)
                    elif orig_status == '❌':
                        worksheet.write(row_num, status_col, status, invalid_format)
                    elif orig_status == '❓':
                        worksheet.write(row_num, status_col, status, unknown_format)
            except Exception as e:
                print(f"Error formatting Excel worksheet: {e}")
            
            # Add a summary sheet
            summary_data = {
                'Metric': ['Total Terms', 'Valid Terms', 'Invalid Terms', 'Unknown Terms'],
                'Value': [
                    len(validation_results),
                    len(validation_results[validation_results['Status'] == '✅']),
                    len(validation_results[validation_results['Status'] == '❌']),
                    len(validation_results[validation_results['Status'] == '❓'])
                ]
            }
            
            # Add file information
            file_info = {
                'File': ['Term Sheet', 'Master Sheet', 'Generated'],
                'Value': [
                    term_sheet_info.get('filename', 'Unknown'),
                    master_sheet_info.get('filename', 'Unknown'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            # Write summary information
            pd.DataFrame(file_info).to_excel(writer, sheet_name='Summary', startrow=0, index=False)
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', startrow=5, index=False)
            
            # Save the Excel file
            try:
                writer.save()
            except Exception as e:
                print(f"Error saving Excel file: {e}")
                # If workbook can't be saved properly, create a simpler version
                with pd.ExcelWriter(output_path, engine='openpyxl') as simple_writer:
                    excel_results.to_excel(simple_writer, sheet_name='Results', index=False)
            
            return output_path