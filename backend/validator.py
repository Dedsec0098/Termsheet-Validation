import pandas as pd
import re
import dateparser
from typing import Dict, Any, List, Tuple
from dateutil.parser import parse as date_parse
import numpy as np

class TermValidator:
    def __init__(self):
        pass
    
    def validate_terms(self, extracted_terms: Dict[str, Any], master_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate extracted terms against the master sheet rules.
        Returns a DataFrame with validation results.
        """
        results = []
        
        # Convert master_df to dictionary for easier access
        master_dict = {}
        for _, row in master_df.iterrows():
            term = row['Term']
            master_dict[term] = {
                'Expected Value': row['Expected Value'] if 'Expected Value' in row else None,
                'Allowed Range': row['Allowed Range'] if 'Allowed Range' in row else None
            }
        
        # Validate each extracted term
        for term, extracted_value in extracted_terms.items():
            result = {
                'Term': term,
                'Extracted Value': extracted_value,
                'Status': '❓',  # Default unknown
                'Expected Value': 'N/A',
                'Allowed Range': 'N/A',
                'Notes': ''
            }
            
            # Check if term exists in master sheet
            if term in master_dict:
                result['Expected Value'] = master_dict[term]['Expected Value']
                result['Allowed Range'] = master_dict[term]['Allowed Range']
                
                # Validate the term
                is_valid, notes = self._validate_value(
                    extracted_value, 
                    master_dict[term]['Expected Value'],
                    master_dict[term]['Allowed Range']
                )
                
                result['Status'] = '✅' if is_valid else '❌'
                result['Notes'] = notes
            else:
                result['Notes'] = 'Term not found in master sheet'
                
            results.append(result)
        
        # Check for missing terms from master sheet
        for term in master_dict:
            if term not in extracted_terms:
                results.append({
                    'Term': term,
                    'Extracted Value': 'Missing',
                    'Status': '❌',
                    'Expected Value': master_dict[term]['Expected Value'],
                    'Allowed Range': master_dict[term]['Allowed Range'],
                    'Notes': 'Term not found in document'
                })
        
        return pd.DataFrame(results)
    
    def _validate_value(self, extracted_value: str, expected_value: Any, allowed_range: Any) -> Tuple[bool, str]:
        """
        Validate a single value against expected value and allowed range.
        Returns (is_valid, notes).
        """
        if pd.isna(expected_value) and pd.isna(allowed_range):
            return True, "No validation rules specified"
        
        # Convert values to strings for consistent handling
        extracted_str = str(extracted_value).strip()
        
        # Try to determine if we're dealing with a date, number, or text
        value_type = self._determine_value_type(extracted_str)
        
        if value_type == 'date':
            return self._validate_date(extracted_str, expected_value, allowed_range)
        elif value_type == 'number':
            return self._validate_number(extracted_str, expected_value, allowed_range)
        else:  # text
            return self._validate_text(extracted_str, expected_value, allowed_range)
    
    def _determine_value_type(self, value_str: str) -> str:
        """Determine if a value is a date, number, or text."""
        # Check if it's a date
        try:
            date_parse(value_str)
            return 'date'
        except:
            pass
        
        # Check if it's a number (possibly with % or currency symbols)
        numeric_str = re.sub(r'[%$£€,]', '', value_str)
        try:
            float(numeric_str)
            return 'number'
        except:
            pass
        
        # Default to text
        return 'text'
    
    def _validate_date(self, extracted_str: str, expected_value: Any, allowed_range: Any) -> Tuple[bool, str]:
        """Validate a date value."""
        try:
            extracted_date = dateparser.parse(extracted_str)
            
            if pd.notna(expected_value):
                expected_date = dateparser.parse(str(expected_value))
                if extracted_date == expected_date:
                    return True, "Date matches expected value"
                
            if pd.notna(allowed_range):
                # Handle date range patterns like "≥2024-01-01"
                range_str = str(allowed_range)
                if range_str.startswith('≥'):
                    min_date = dateparser.parse(range_str[1:])
                    if extracted_date >= min_date:
                        return True, f"Date is after minimum {min_date.strftime('%Y-%m-%d')}"
                    else:
                        return False, f"Date is before minimum {min_date.strftime('%Y-%m-%d')}"
                elif range_str.startswith('≤'):
                    max_date = dateparser.parse(range_str[1:])
                    if extracted_date <= max_date:
                        return True, f"Date is before maximum {max_date.strftime('%Y-%m-%d')}"
                    else:
                        return False, f"Date is after maximum {max_date.strftime('%Y-%m-%d')}"
                elif '–' in range_str or '-' in range_str:
                    # Handle date ranges like "2023-01-01 – 2025-12-31"
                    delimiter = '–' if '–' in range_str else '-'
                    parts = range_str.split(delimiter)
                    if len(parts) == 2:
                        min_date = dateparser.parse(parts[0].strip())
                        max_date = dateparser.parse(parts[1].strip())
                        if min_date <= extracted_date <= max_date:
                            return True, f"Date is within range {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
                        else:
                            return False, f"Date is outside range {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
            
            # If we got here with no validation rules that passed
            if pd.notna(expected_value):
                return False, f"Date {extracted_date.strftime('%Y-%m-%d')} doesn't match expected {expected_value}"
            
            return True, "No specific date validation rules"
            
        except Exception as e:
            return False, f"Date validation error: {e}"
    
    def _validate_number(self, extracted_str: str, expected_value: Any, allowed_range: Any) -> Tuple[bool, str]:
        """Validate a numeric value."""
        try:
            # Remove any non-numeric characters except decimal point
            numeric_str = re.sub(r'[^0-9\.]', '', extracted_str.replace(',', ''))
            extracted_num = float(numeric_str)
            
            # Handle percentage values (if % symbol is present)
            is_percentage = '%' in extracted_str
            
            if pd.notna(expected_value):
                # Clean expected value if it's a string
                if isinstance(expected_value, str):
                    expected_str = re.sub(r'[^0-9\.]', '', expected_value.replace(',', ''))
                    expected_num = float(expected_str)
                else:
                    expected_num = float(expected_value)
                
                if np.isclose(extracted_num, expected_num, rtol=1e-5):
                    return True, "Number matches expected value"
            
            if pd.notna(allowed_range):
                range_str = str(allowed_range)
                if range_str.startswith('≥'):
                    min_val = float(re.sub(r'[^0-9\.]', '', range_str[1:].replace(',', '')))
                    if extracted_num >= min_val:
                        return True, f"Number is greater than or equal to minimum {min_val}"
                    else:
                        return False, f"Number is below minimum {min_val}"
                elif range_str.startswith('≤'):
                    max_val = float(re.sub(r'[^0-9\.]', '', range_str[1:].replace(',', '')))
                    if extracted_num <= max_val:
                        return True, f"Number is less than or equal to maximum {max_val}"
                    else:
                        return False, f"Number is above maximum {max_val}"
                elif '–' in range_str or '-' in range_str:
                    # Handle ranges like "4.5%–6.0%" or "100-200"
                    delimiter = '–' if '–' in range_str else '-'
                    parts = range_str.split(delimiter)
                    if len(parts) == 2:
                        min_val = float(re.sub(r'[^0-9\.]', '', parts[0].replace(',', '')))
                        max_val = float(re.sub(r'[^0-9\.]', '', parts[1].replace(',', '')))
                        if min_val <= extracted_num <= max_val:
                            return True, f"Number is within range {min_val} to {max_val}"
                        else:
                            return False, f"Number is outside range {min_val} to {max_val}"
            
            # If we got here with no validation rules that passed
            if pd.notna(expected_value):
                return False, f"Number {extracted_num} doesn't match expected {expected_value}"
            
            return True, "No specific numeric validation rules"
            
        except Exception as e:
            return False, f"Numeric validation error: {e}"
    
    def _validate_text(self, extracted_str: str, expected_value: Any, allowed_range: Any) -> Tuple[bool, str]:
        """Validate a text value."""
        if pd.notna(expected_value):
            expected_str = str(expected_value).strip()
            
            # Exact match
            if extracted_str.lower() == expected_str.lower():
                return True, "Text matches expected value"
            
            # Fuzzy match
            from fuzzywuzzy import fuzz
            similarity = fuzz.ratio(extracted_str.lower(), expected_str.lower())
            if similarity >= 90:  # 90% similarity threshold
                return True, f"Text matches expected value with {similarity}% similarity"
            else:
                return False, f"Text doesn't match expected value (similarity: {similarity}%)"
        
        if pd.notna(allowed_range):
            # For text, allowed_range could be a pipe-separated list of valid values
            range_str = str(allowed_range)
            if '|' in range_str:
                valid_values = [v.strip() for v in range_str.split('|')]
                if extracted_str in valid_values or any(extracted_str.lower() == v.lower() for v in valid_values):
                    return True, "Text is in list of allowed values"
                else:
                    return False, f"Text is not in list of allowed values: {', '.join(valid_values)}"
        
        # If no validation rules specified
        return True, "No specific text validation rules"