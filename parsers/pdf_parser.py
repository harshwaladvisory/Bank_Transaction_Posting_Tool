"""
PDF Parser Module - Extract transactions from bank statement PDFs
Supports both digital PDFs and scanned PDFs (via OCR)
"""

import re
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATE_FORMATS_TO_TRY, TESSERACT_CMD, POPPLER_PATH

# Configure Tesseract path if available
try:
    import pytesseract
    if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
except ImportError:
    pass

class PDFParser:
    """Parse bank statement PDFs to extract transactions"""
    
    def __init__(self):
        self.transactions = []
        self.bank_name = None
        self.account_number = None
        self.statement_period = None
        
    def parse(self, file_path: str) -> List[Dict]:
        """
        Main entry point - detect PDF type and parse accordingly
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try digital PDF first
        transactions = self._parse_digital_pdf(file_path)
        
        # If no transactions found, try OCR
        if not transactions:
            transactions = self._parse_scanned_pdf(file_path)
        
        self.transactions = transactions
        return transactions
    
    def _parse_digital_pdf(self, file_path: str) -> List[Dict]:
        """Parse digital PDF using pdfplumber"""
        try:
            import pdfplumber
        except ImportError:
            print("Warning: pdfplumber not installed. Run: pip install pdfplumber")
            return []
        
        transactions = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = ""
                
                for page in pdf.pages:
                    # Extract text
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                    
                    # Also try table extraction
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            txn = self._parse_table_row(row)
                            if txn:
                                transactions.append(txn)
                
                # If no transactions from tables, try text parsing
                if not transactions and full_text:
                    transactions = self._parse_text_transactions(full_text)
                
                # Extract metadata
                if full_text:
                    self._extract_metadata(full_text)
                    
        except Exception as e:
            print(f"Error parsing digital PDF: {e}")
            
        return transactions
    
    def _parse_scanned_pdf(self, file_path: str) -> List[Dict]:
        """Parse scanned PDF using OCR (Tesseract)"""
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError:
            print("Warning: OCR libraries not installed. Run: pip install pytesseract pdf2image")
            return []
        
        transactions = []
        
        try:
            # Convert PDF to images (use poppler_path if configured)
            if POPPLER_PATH and os.path.exists(POPPLER_PATH):
                images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(file_path, dpi=300)
            
            full_text = ""
            for i, image in enumerate(images):
                # OCR each page
                text = pytesseract.image_to_string(image)
                full_text += text + "\n"
            
            # Parse transactions from OCR text
            transactions = self._parse_text_transactions(full_text)
            
            # Extract metadata
            self._extract_metadata(full_text)
            
        except Exception as e:
            print(f"Error parsing scanned PDF with OCR: {e}")
            
        return transactions
    
    def _parse_table_row(self, row: List) -> Optional[Dict]:
        """Parse a single table row into a transaction"""
        if not row or len(row) < 3:
            return None
        
        # Clean row data
        row = [str(cell).strip() if cell else "" for cell in row]
        
        # Skip header rows
        header_keywords = ['date', 'description', 'amount', 'balance', 'debit', 'credit']
        if any(kw in ' '.join(row).lower() for kw in header_keywords):
            return None
        
        # Try to identify columns
        date = None
        description = None
        amount = None
        balance = None
        
        for cell in row:
            if not cell:
                continue
                
            # Check if it's a date
            parsed_date = self._parse_date(cell)
            if parsed_date and not date:
                date = parsed_date
                continue
            
            # Check if it's an amount
            parsed_amount = self._parse_amount(cell)
            if parsed_amount is not None:
                if amount is None:
                    amount = parsed_amount
                elif balance is None:
                    balance = parsed_amount
                continue
            
            # Otherwise, it's probably description
            if not description and len(cell) > 3:
                description = cell
        
        if date and description and amount is not None:
            return {
                'date': date,
                'description': description,
                'amount': amount,
                'balance': balance,
                'raw_data': row
            }
        
        return None
    
    def _parse_text_transactions(self, text: str) -> List[Dict]:
        """Parse transactions from raw text - handles multiple bank formats"""
        transactions = []
        
        # Detect bank type and use appropriate parser
        text_lower = text.lower()
        
        if 'farmers bank' in text_lower:
            transactions = self._parse_farmers_bank(text)
        else:
            # Generic parsing
            transactions = self._parse_generic_statement(text)
        
        return transactions
    
    def _parse_farmers_bank(self, text: str) -> List[Dict]:
        """Parse Farmers Bank statement format"""
        transactions = []
        lines = text.split('\n')
        current_year = datetime.now().year
        
        # Track which section we're in
        in_deposits = False
        in_checks = False
        processed_checks = set()  # Track check numbers we've already processed
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            line_lower = line.lower()
            if 'debits / credits' in line_lower or ('date' in line_lower and 'description' in line_lower):
                in_deposits = True
                in_checks = False
                continue
            elif 'numbered checks' in line_lower:
                in_deposits = False
                in_checks = True
                continue
            elif 'daily balance' in line_lower:
                in_deposits = False
                in_checks = False
                continue
            
            # Parse deposit/credit lines
            # Format: 07/01 100,000.00 Red River Oper July KGC 978014 ACH DEPOSIT
            if in_deposits:
                # Pattern: MM/DD Amount Description
                match = re.match(r'^(\d{2}/\d{2})\s+([\d,]+\.\d{2})\s+(.+?)(?:\s+ACH\s+DEPOSIT|\s+DEPOSIT)?$', line, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    amount_str = match.group(2)
                    description = match.group(3).strip()
                    
                    # Clean description - remove trailing reference numbers
                    description = re.sub(r'\s+\d{6}$', '', description)
                    
                    date = self._parse_date(date_str)
                    amount = self._parse_amount(amount_str)
                    
                    if date and amount is not None:
                        transactions.append({
                            'date': date,
                            'description': description,
                            'amount': abs(amount),  # Deposits are positive
                            'type': 'deposit'
                        })
                        continue
            
            # Parse check lines - HANDLE MULTIPLE CHECKS ON ONE LINE
            # Format: "125 07/02 100,000.00    126 07/02 250,000.00    127 07/26 600,000.00"
            if in_checks:
                # Find ALL check patterns on this line
                # Pattern: Check# MM/DD Amount
                check_pattern = r'(\d{1,4})\s+(\d{2}/\d{2})\s+([\d,]+\.\d{2})'
                matches = re.findall(check_pattern, line)
                
                for check_match in matches:
                    check_num = check_match[0]
                    date_str = check_match[1]
                    amount_str = check_match[2]
                    
                    # Skip if we already processed this check
                    if check_num in processed_checks:
                        continue
                    
                    date = self._parse_date(date_str)
                    amount = self._parse_amount(amount_str)
                    
                    if date and amount is not None:
                        transactions.append({
                            'date': date,
                            'description': f'Check #{check_num}',
                            'amount': -abs(amount),  # Checks are negative (debits)
                            'type': 'check',
                            'check_number': check_num
                        })
                        processed_checks.add(check_num)
        
        return transactions
    
    def _parse_generic_statement(self, text: str) -> List[Dict]:
        """Generic bank statement parsing"""
        transactions = []
        lines = text.split('\n')
        
        # Common patterns for bank statement transactions
        patterns = [
            # Pattern 1: MM/DD/YYYY Description Amount
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)\s*$',
            # Pattern 2: MM/DD Description Amount Balance
            r'(\d{1,2}[/-]\d{1,2})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s*$',
            # Pattern 3: Date at start, amount at end
            r'^(\d{1,2}[/-]\d{1,2}[/-]?\d{0,4})\s+(.+?)\s+([-+]?\$?[\d,]+\.?\d*)',
        ]
        
        current_year = datetime.now().year
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    groups = match.groups()
                    
                    # Parse date
                    date_str = groups[0]
                    date = self._parse_date(date_str)
                    if not date:
                        continue
                    
                    # Parse description
                    description = groups[1].strip()
                    if len(description) < 3:
                        continue
                    
                    # Parse amount
                    amount = self._parse_amount(groups[2])
                    if amount is None:
                        continue
                    
                    # Determine if debit or credit based on keywords
                    desc_lower = description.lower()
                    if any(kw in desc_lower for kw in ['deposit', 'credit', 'transfer in', 'interest']):
                        amount = abs(amount)
                    elif any(kw in desc_lower for kw in ['withdrawal', 'debit', 'check', 'payment', 'fee']):
                        amount = -abs(amount)
                    
                    transactions.append({
                        'date': date,
                        'description': description,
                        'amount': amount,
                        'balance': self._parse_amount(groups[3]) if len(groups) > 3 else None
                    })
                    break
        
        return transactions
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats and return MM/DD/YYYY"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        current_year = datetime.now().year
        
        # Try various formats
        formats = [
            '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%m/%d', '%m-%d'  # Without year
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # If no year in format, use current year
                if '%Y' not in fmt and '%y' not in fmt:
                    dt = dt.replace(year=current_year)
                return dt.strftime('%m/%d/%Y')
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str:
            return None
        
        try:
            # Clean the string
            amount_str = str(amount_str).strip()
            
            # Remove currency symbols and spaces
            amount_str = amount_str.replace('$', '').replace(' ', '')
            
            # Handle parentheses for negative
            is_negative = False
            if '(' in amount_str and ')' in amount_str:
                is_negative = True
                amount_str = amount_str.replace('(', '').replace(')', '')
            
            # Handle CR/DR suffixes
            if amount_str.upper().endswith('CR'):
                amount_str = amount_str[:-2]
            elif amount_str.upper().endswith('DR'):
                is_negative = True
                amount_str = amount_str[:-2]
            
            # Handle negative sign
            if amount_str.startswith('-'):
                is_negative = True
                amount_str = amount_str[1:]
            
            # Remove commas
            amount_str = amount_str.replace(',', '')
            
            # Parse
            if amount_str:
                amount = float(amount_str)
                return -amount if is_negative else amount
                
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _extract_metadata(self, text: str):
        """Extract bank name, account number, statement period from text"""
        text_lower = text.lower()
        
        # Bank name detection
        bank_patterns = [
            (r'farmers bank', 'Farmers Bank'),
            (r'pnc bank', 'PNC Bank'),
            (r'bank of america', 'Bank of America'),
            (r'wells fargo', 'Wells Fargo'),
            (r'chase', 'Chase'),
            (r'banc of california', 'Banc of California'),
        ]
        
        for pattern, name in bank_patterns:
            if re.search(pattern, text_lower):
                self.bank_name = name
                break
        
        # Account number
        acct_match = re.search(r'account[:\s#]*(\d{4,})', text_lower)
        if acct_match:
            self.account_number = acct_match.group(1)
        
        # Statement period
        period_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|through|-)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text_lower)
        if period_match:
            self.statement_period = f"{period_match.group(1)} to {period_match.group(2)}"
    
    def get_summary(self) -> Dict:
        """Get summary of parsed transactions"""
        if not self.transactions:
            return {
                'total_transactions': 0,
                'total_deposits': 0,
                'total_withdrawals': 0,
                'bank_name': self.bank_name,
                'account_number': self.account_number
            }
        
        deposits = sum(t['amount'] for t in self.transactions if t.get('amount', 0) > 0)
        withdrawals = sum(t['amount'] for t in self.transactions if t.get('amount', 0) < 0)
        
        return {
            'total_transactions': len(self.transactions),
            'total_deposits': deposits,
            'total_withdrawals': withdrawals,
            'net_change': deposits + withdrawals,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'statement_period': self.statement_period
        }


# Standalone test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        parser = PDFParser()
        transactions = parser.parse(sys.argv[1])
        
        print(f"\n{'='*70}")
        print(f"PDF Parser Results - {parser.bank_name or 'Unknown Bank'}")
        print(f"{'='*70}")
        
        for txn in transactions:
            print(f"\nDate: {txn['date']}")
            print(f"Description: {txn['description']}")
            print(f"Amount: ${txn['amount']:,.2f}")
            if txn.get('check_number'):
                print(f"Check #: {txn['check_number']}")
        
        summary = parser.get_summary()
        print(f"\n{'='*70}")
        print("Summary:")
        print(f"  Total Transactions: {summary['total_transactions']}")
        print(f"  Total Deposits: ${summary['total_deposits']:,.2f}")
        print(f"  Total Withdrawals: ${summary['total_withdrawals']:,.2f}")
        print(f"  Net Change: ${summary['net_change']:,.2f}")
    else:
        print("Usage: python pdf_parser.py <path_to_pdf>")