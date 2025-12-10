"""
Excel Parser Module - Extract transactions from bank statement Excel/CSV files
"""

import re
import os
from datetime import datetime
from typing import List, Dict, Optional
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATE_FORMATS_TO_TRY

class ExcelParser:
    """Parse bank statement Excel/CSV files to extract transactions"""
    
    def __init__(self):
        self.transactions = []
        self.bank_name = None
        self.account_number = None
        self.column_mapping = {}
        
    def parse(self, file_path: str) -> List[Dict]:
        """
        Main entry point - detect file type and parse accordingly
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            transactions = self._parse_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            transactions = self._parse_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        self.transactions = transactions
        return transactions
    
    def _parse_excel(self, file_path: str) -> List[Dict]:
        """Parse Excel file using pandas"""
        try:
            import pandas as pd
        except ImportError:
            print("Warning: pandas not installed. Run: pip install pandas openpyxl")
            return []
        
        transactions = []
        
        try:
            # Try to read all sheets
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty:
                    continue
                
                # Auto-detect columns
                self._detect_columns(df)
                
                # Parse transactions
                sheet_transactions = self._parse_dataframe(df)
                transactions.extend(sheet_transactions)
                
                if transactions:
                    break  # Use first sheet with transactions
                    
        except Exception as e:
            print(f"Error parsing Excel file: {e}")
            
        return transactions
    
    def _parse_csv(self, file_path: str) -> List[Dict]:
        """Parse CSV file using pandas"""
        try:
            import pandas as pd
        except ImportError:
            print("Warning: pandas not installed. Run: pip install pandas")
            return []
        
        transactions = []
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"Could not decode CSV file")
                return []
            
            # Auto-detect columns
            self._detect_columns(df)
            
            # Parse transactions
            transactions = self._parse_dataframe(df)
            
        except Exception as e:
            print(f"Error parsing CSV file: {e}")
            
        return transactions
    
    def _detect_columns(self, df) -> Dict:
        """Auto-detect column mappings based on column names"""
        import pandas as pd
        
        columns = {col: col.lower().strip() for col in df.columns}
        mapping = {}
        
        # Date column detection
        date_keywords = ['date', 'trans date', 'transaction date', 'posting date', 'post date', 'value date']
        for col, col_lower in columns.items():
            if any(kw in col_lower for kw in date_keywords):
                mapping['date'] = col
                break
        
        # Description column detection
        desc_keywords = ['description', 'narration', 'narrative', 'details', 'particulars', 
                        'transaction description', 'memo', 'reference', 'payee']
        for col, col_lower in columns.items():
            if any(kw in col_lower for kw in desc_keywords):
                mapping['description'] = col
                break
        
        # Amount column detection (single column)
        amount_keywords = ['amount', 'transaction amount', 'trans amount']
        for col, col_lower in columns.items():
            if any(kw == col_lower for kw in amount_keywords):
                mapping['amount'] = col
                break
        
        # Debit/Credit separate columns
        debit_keywords = ['debit', 'withdrawal', 'withdrawals', 'dr', 'debit amount', 'money out']
        credit_keywords = ['credit', 'deposit', 'deposits', 'cr', 'credit amount', 'money in']
        
        for col, col_lower in columns.items():
            if any(kw in col_lower for kw in debit_keywords):
                mapping['debit'] = col
            if any(kw in col_lower for kw in credit_keywords):
                mapping['credit'] = col
        
        # Balance column
        balance_keywords = ['balance', 'running balance', 'closing balance', 'available balance']
        for col, col_lower in columns.items():
            if any(kw in col_lower for kw in balance_keywords):
                mapping['balance'] = col
                break
        
        # Check number
        check_keywords = ['check', 'cheque', 'check no', 'check number', 'cheque no']
        for col, col_lower in columns.items():
            if any(kw in col_lower for kw in check_keywords):
                mapping['check_number'] = col
                break
        
        self.column_mapping = mapping
        return mapping
    
    def _parse_dataframe(self, df) -> List[Dict]:
        """Parse pandas DataFrame into transactions"""
        import pandas as pd
        
        transactions = []
        mapping = self.column_mapping
        
        # Need at least date and description
        if 'date' not in mapping:
            # Try first column as date
            mapping['date'] = df.columns[0]
        
        if 'description' not in mapping:
            # Try to find longest text column
            for col in df.columns:
                if df[col].dtype == 'object':
                    avg_len = df[col].astype(str).str.len().mean()
                    if avg_len > 10:
                        mapping['description'] = col
                        break
        
        for idx, row in df.iterrows():
            try:
                # Parse date
                date_val = row.get(mapping.get('date', ''))
                date = self._parse_date(date_val)
                if not date:
                    continue
                
                # Parse description
                description = str(row.get(mapping.get('description', ''), '')).strip()
                if not description or description == 'nan':
                    continue
                
                # Parse amount
                amount = None
                
                # Single amount column
                if 'amount' in mapping:
                    amount = self._parse_amount(row.get(mapping['amount']))
                
                # Separate debit/credit columns
                elif 'debit' in mapping or 'credit' in mapping:
                    debit = self._parse_amount(row.get(mapping.get('debit', ''))) or 0
                    credit = self._parse_amount(row.get(mapping.get('credit', ''))) or 0
                    
                    if debit and not credit:
                        amount = -abs(debit)  # Debits are negative (money out)
                    elif credit and not debit:
                        amount = abs(credit)  # Credits are positive (money in)
                    elif debit and credit:
                        amount = credit - debit
                
                if amount is None:
                    continue
                
                # Parse balance
                balance = None
                if 'balance' in mapping:
                    balance = self._parse_amount(row.get(mapping['balance']))
                
                # Parse check number
                check_number = None
                if 'check_number' in mapping:
                    check_number = str(row.get(mapping['check_number'], '')).strip()
                    if check_number == 'nan' or not check_number:
                        check_number = None
                
                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'balance': balance,
                    'check_number': check_number,
                    'raw_data': row.to_dict()
                })
                
            except Exception as e:
                continue
        
        return transactions
    
    def _parse_date(self, date_val) -> Optional[str]:
        """Parse various date formats and return MM/DD/YYYY"""
        import pandas as pd
        
        if date_val is None or (isinstance(date_val, float) and pd.isna(date_val)):
            return None
        
        # Handle pandas Timestamp
        if isinstance(date_val, pd.Timestamp):
            return date_val.strftime("%m/%d/%Y")
        
        # Handle datetime
        if isinstance(date_val, datetime):
            return date_val.strftime("%m/%d/%Y")
        
        # Handle string
        date_str = str(date_val).strip()
        if not date_str or date_str == 'nan':
            return None
        
        current_year = datetime.now().year
        
        for fmt in DATE_FORMATS_TO_TRY:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.year < 100:
                    dt = dt.replace(year=dt.year + 2000)
                return dt.strftime("%m/%d/%Y")
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_val) -> Optional[float]:
        """Parse amount value to float"""
        import pandas as pd
        
        if amount_val is None or (isinstance(amount_val, float) and pd.isna(amount_val)):
            return None
        
        # Already a number
        if isinstance(amount_val, (int, float)):
            return float(amount_val) if not pd.isna(amount_val) else None
        
        # Handle string
        amount_str = str(amount_val).strip()
        if not amount_str or amount_str == 'nan':
            return None
        
        # Remove currency symbols and commas
        amount_str = re.sub(r'[$€£₹,]', '', amount_str)
        
        # Handle parentheses for negative
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        # Handle CR/DR suffixes
        if amount_str.upper().endswith('CR'):
            amount_str = amount_str[:-2].strip()
        elif amount_str.upper().endswith('DR'):
            amount_str = '-' + amount_str[:-2].strip()
        
        try:
            return float(amount_str)
        except ValueError:
            return None
    
    def get_summary(self) -> Dict:
        """Get parsing summary"""
        if not self.transactions:
            return {'status': 'no_transactions', 'count': 0}
        
        total_deposits = sum(t['amount'] for t in self.transactions if t['amount'] > 0)
        total_withdrawals = sum(t['amount'] for t in self.transactions if t['amount'] < 0)
        
        return {
            'status': 'success',
            'count': len(self.transactions),
            'column_mapping': self.column_mapping,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'net_change': total_deposits + total_withdrawals
        }


# Standalone test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        parser = ExcelParser()
        transactions = parser.parse(sys.argv[1])
        
        print(f"\n{'='*60}")
        print(f"Excel Parsing Results")
        print(f"{'='*60}")
        
        summary = parser.get_summary()
        print(f"Transactions found: {summary['count']}")
        print(f"Column Mapping: {summary.get('column_mapping', {})}")
        print(f"Total Deposits: ${summary.get('total_deposits', 0):,.2f}")
        print(f"Total Withdrawals: ${abs(summary.get('total_withdrawals', 0)):,.2f}")
        
        print(f"\n{'='*60}")
        print("Sample Transactions:")
        print(f"{'='*60}")
        
        for txn in transactions[:10]:
            print(f"{txn['date']} | {txn['description'][:40]:<40} | ${txn['amount']:>12,.2f}")
    else:
        print("Usage: python excel_parser.py <path_to_file>")
