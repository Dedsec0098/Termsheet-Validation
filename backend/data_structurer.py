import spacy
import re
from typing import Dict, Any, List, Optional
import pandas as pd
import dateparser
from fuzzywuzzy import fuzz

class DataStructurer:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # Download the model if not present
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Expanded list of financial terms for pattern matching
        self.financial_terms = [
            "interest rate", "maturity date", "principal", "coupon", 
            "governing law", "counterparty", "collateral", "amortization",
            "default rate", "prepayment penalty", "term", "closing date",
            "loan amount", "borrower", "lender", "facility", "commitment",
            "pricing", "margin", "fee", "documentation", "security", "covenant",
            "debt", "equity", "currency", "payment date", "repayment", "default"
        ]
        
        # Enhanced regex patterns with more flexibility
        self.patterns = {
            'interest_rate': re.compile(r'interest\s*rate\s*[:=\-]?\s*([\d\.]+)\s*%', re.IGNORECASE),
            'maturity_date': re.compile(r'maturity\s*date\s*[:=\-]?\s*([a-zA-Z0-9\s\-\.,/]+)', re.IGNORECASE),
            'principal': re.compile(r'principal\s*[:=\-]?\s*[$£€]?\s*([\d,\.]+)', re.IGNORECASE),
            'counterparty': re.compile(r'(?:counterparty|counter[\/\- ]?party|counter-party)\s*[:=\-]?\s*([a-zA-Z0-9\s\-\.,&]+)', re.IGNORECASE),
            'governing_law': re.compile(r'governing\s*law\s*[:=\-]?\s*([a-zA-Z\s]+)', re.IGNORECASE),
            'loan_amount': re.compile(r'(?:loan|facility)\s*amount\s*[:=\-]?\s*[$£€]?\s*([\d,\.]+\s*(?:million|billion|m|b)?)', re.IGNORECASE),
            'borrower': re.compile(r'borrower\s*[:=\-]?\s*([a-zA-Z0-9\s\-\.,&]+)', re.IGNORECASE),
            'lender': re.compile(r'lender\s*[:=\-]?\s*([a-zA-Z0-9\s\-\.,&]+)', re.IGNORECASE),
        }
    
    def structure_data(self, text: str) -> Dict[str, Any]:
        """
        Process extracted text and structure it into a dictionary of terms.
        Uses regex pattern matching, NLP techniques, and line-by-line analysis.
        """
        terms = {}
        
        # Apply regex pattern matching
        for key, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            for match in matches:  # Get all matches, not just the first one
                if key not in terms:  # Only keep the first match per key
                    terms[key] = match.group(1).strip()
        
        # Apply NLP processing
        doc = self.nlp(text[:100000])  # Limit text size to prevent memory issues
        
        # Extract dates that weren't caught by regex
        if 'maturity_date' not in terms:
            for ent in doc.ents:
                if ent.label_ == "DATE" and any(date_term in text[max(0, ent.start_char-40):ent.start_char].lower() 
                                             for date_term in ["maturity", "matures", "due"]):
                    date_str = ent.text
                    parsed_date = dateparser.parse(date_str)
                    if parsed_date:
                        terms['maturity_date'] = parsed_date.strftime('%Y-%m-%d')
                    else:
                        terms['maturity_date'] = date_str
                    break
        
        # Extract percentages that weren't caught by regex
        if 'interest_rate' not in terms:
            for ent in doc.ents:
                if ent.label_ == "PERCENT" and any(rate_term in text[max(0, ent.start_char-40):ent.start_char].lower() 
                                                for rate_term in ["interest", "rate", "coupon"]):
                    terms['interest_rate'] = ent.text
                    break
        
        # Extract organizations as potential counterparties
        if 'counterparty' not in terms:
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    terms['counterparty'] = ent.text
                    break
                    
        # Extract money amounts that weren't caught
        if 'principal' not in terms and 'loan_amount' not in terms:
            for ent in doc.ents:
                if ent.label_ == "MONEY":
                    if any(principal_term in text[max(0, ent.start_char-30):ent.start_char].lower() 
                          for principal_term in ["principal", "amount"]):
                        terms['principal'] = ent.text
                    break
        
        # Look for terms based on line-by-line analysis (more aggressive approach)
        lines = text.split('\n')
        for line in lines:
            # Check for "Term: Value" or "Term - Value" or "Term = Value" patterns
            for separator in [':', '-', '=']:
                if separator in line:
                    parts = line.split(separator, 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        
                        if not value:  # Skip if value is empty
                            continue
                            
                        # Direct match with financial terms
                        if any(term == key for term in self.financial_terms):
                            normalized_term = key.replace(' ', '_')
                            terms[normalized_term] = value
                            continue
                            
                        # Fuzzy match with lower threshold to catch more terms
                        for term in self.financial_terms:
                            if fuzz.ratio(key, term) > 65:  # Lower threshold (was 80)
                                normalized_term = term.replace(' ', '_')
                                terms[normalized_term] = value
                                break
        
        print(f"Extracted {len(terms)} terms: {list(terms.keys())}")
        return terms
    
    def normalize_terms(self, terms: Dict[str, Any], master_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Normalize extracted terms to match the master sheet terminology.
        Uses fuzzy matching to handle variations in terminology.
        """
        normalized_terms = {}
        
        # Ensure we have a Term column
        if 'Term' not in master_df.columns:
            print("WARNING: Master sheet does not have a 'Term' column. Available columns:", master_df.columns.tolist())
            # Try to guess which column might contain terms
            potential_term_columns = [col for col in master_df.columns if 'term' in col.lower()]
            if potential_term_columns:
                master_terms = master_df[potential_term_columns[0]].astype(str).str.lower().tolist()
                print(f"Using '{potential_term_columns[0]}' as Term column")
            else:
                # Just use the first column as a fallback
                master_terms = master_df.iloc[:, 0].astype(str).str.lower().tolist()
                print(f"Using first column '{master_df.columns[0]}' as Term column")
        else:
            master_terms = master_df['Term'].astype(str).str.lower().tolist()
        
        print(f"Master sheet terms: {master_terms}")
        
        for key, value in terms.items():
            # Convert snake_case to spaces for matching
            display_key = key.replace('_', ' ')
            
            # Try exact match first (case insensitive)
            if display_key.lower() in master_terms:
                # Get the original case from master_df
                original_case_term = master_df[master_df['Term'].str.lower() == display_key.lower()]['Term'].iloc[0]
                normalized_terms[original_case_term] = value
                continue
            
            # Then try fuzzy matching with a lower threshold
            best_match = None
            best_score = 0
            
            for master_term in master_terms:
                score = fuzz.ratio(display_key.lower(), master_term.lower())
                if score > best_score and score > 60:  # Lower threshold (was 70)
                    best_score = score
                    best_match = master_term
            
            if best_match:
                # Get the original case from master_df
                original_case_terms = master_df[master_df['Term'].str.lower() == best_match]['Term']
                if not original_case_terms.empty:
                    original_case_term = original_case_terms.iloc[0]
                    normalized_terms[original_case_term] = value
                    print(f"Matched '{display_key}' to '{original_case_term}' with score {best_score}")
                else:
                    normalized_terms[best_match.title()] = value
                    print(f"Matched '{display_key}' to '{best_match.title()}' with score {best_score}")
            else:
                # Keep the original term if no good match
                normalized_terms[display_key.title()] = value
                print(f"No match found for '{display_key}', keeping as is")
                
        print(f"Normalized {len(normalized_terms)} terms: {list(normalized_terms.keys())}")
        return normalized_terms