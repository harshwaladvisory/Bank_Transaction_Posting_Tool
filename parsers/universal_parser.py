"""
Universal Parser Module - Auto-detect file type and route to appropriate parser
Now with LLM support for better accuracy!
"""

import os
from typing import List, Dict
from .pdf_parser import PDFParser
from .excel_parser import ExcelParser

# Try to import LLM parser
try:
    from .llm_parser import LLMParser
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class UniversalParser:
    """Universal parser that auto-detects and routes to appropriate parser"""

    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.csv': 'excel'
    }

    def __init__(self, use_llm: bool = True):
        """
        Initialize parser

        Args:
            use_llm: If True and OpenAI is available, use LLM for PDF parsing
        """
        self.pdf_parser = PDFParser()
        self.excel_parser = ExcelParser()
        self.llm_parser = None
        self.last_parser = None
        self.file_type = None
        self.use_llm = use_llm

        # Initialize LLM parser if available and requested
        if use_llm and LLM_AVAILABLE:
            self.llm_parser = LLMParser()
            if self.llm_parser.is_available():
                print("[INFO] LLM parser enabled (GPT-4)")
            else:
                print("[INFO] LLM parser not available (no API key). Using regex parser.")
                self.llm_parser = None

    def parse(self, file_path: str) -> List[Dict]:
        """
        Auto-detect file type and parse accordingly

        Args:
            file_path: Path to bank statement file

        Returns:
            List of transaction dictionaries
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}. Supported: {list(self.SUPPORTED_EXTENSIONS.keys())}")

        self.file_type = self.SUPPORTED_EXTENSIONS[ext]

        if self.file_type == 'pdf':
            # Try LLM parser first if available
            if self.llm_parser and self.llm_parser.is_available():
                print("[INFO] Using LLM parser for PDF...")
                self.last_parser = self.llm_parser
                transactions = self.llm_parser.parse(file_path)

                # If LLM fails or returns no results, fall back to regex
                if not transactions:
                    print("[WARNING] LLM parser returned no results. Falling back to regex parser.")
                    self.last_parser = self.pdf_parser
                    transactions = self.pdf_parser.parse(file_path)

                return transactions
            else:
                # Use regex parser
                print("[INFO] Using regex parser for PDF...")
                self.last_parser = self.pdf_parser
                return self.pdf_parser.parse(file_path)
        else:
            self.last_parser = self.excel_parser
            return self.excel_parser.parse(file_path)

    def get_summary(self) -> Dict:
        """Get parsing summary from last used parser"""
        if self.last_parser:
            summary = self.last_parser.get_summary()
            summary['file_type'] = self.file_type
            summary['parser_type'] = 'llm' if self.last_parser == self.llm_parser else 'regex'
            return summary
        return {'status': 'no_file_parsed'}

    def get_metadata(self) -> Dict:
        """Get metadata from last parsed file"""
        if isinstance(self.last_parser, PDFParser):
            return {
                'bank_name': self.last_parser.bank_name,
                'account_number': self.last_parser.account_number,
                'statement_period': self.last_parser.statement_period
            }
        elif isinstance(self.last_parser, ExcelParser):
            return {
                'column_mapping': self.last_parser.column_mapping
            }
        return {}

    def get_parsing_metadata(self) -> Dict:
        """Get detailed parsing metadata including validation warnings"""
        if isinstance(self.last_parser, PDFParser):
            return self.last_parser.get_parsing_metadata()
        return {}


def parse_bank_statement(file_path: str, use_llm: bool = True) -> tuple:
    """
    Convenience function to parse a bank statement

    Args:
        file_path: Path to bank statement file
        use_llm: If True, use LLM parser for PDFs

    Returns:
        Tuple of (transactions list, summary dict)
    """
    parser = UniversalParser(use_llm=use_llm)
    transactions = parser.parse(file_path)
    summary = parser.get_summary()
    return transactions, summary


# Standalone test
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        transactions, summary = parse_bank_statement(sys.argv[1])

        print(f"\n{'='*60}")
        print(f"Universal Parser Results")
        print(f"{'='*60}")
        print(f"File Type: {summary.get('file_type', 'Unknown')}")
        print(f"Parser Type: {summary.get('parser_type', 'Unknown')}")
        print(f"Transactions found: {summary['count']}")
        print(f"Total Deposits: ${summary.get('total_deposits', 0):,.2f}")
        print(f"Total Withdrawals: ${abs(summary.get('total_withdrawals', 0)):,.2f}")

        print(f"\n{'='*60}")
        print("Sample Transactions:")
        print(f"{'='*60}")

        for txn in transactions[:10]:
            print(f"{txn['date']} | {txn['description'][:40]:<40} | ${txn['amount']:>12,.2f}")
    else:
        print("Usage: python universal_parser.py <path_to_file>")
