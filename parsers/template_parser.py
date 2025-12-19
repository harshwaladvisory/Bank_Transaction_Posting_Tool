"""
Template-Based Bank Statement Parser

Uses JSON templates from config/bank_templates.json to parse any configured bank.
Falls back to AI for unknown banks.
"""

import json
import os
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class TemplateParser:
    """Parse bank statements using JSON-configured templates"""

    def __init__(self, templates_path: str = None):
        """
        Initialize with templates from JSON config

        Args:
            templates_path: Path to bank_templates.json (auto-detected if None)
        """
        if templates_path is None:
            # Auto-detect templates path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            templates_path = os.path.join(base_dir, 'config', 'bank_templates.json')

        self.templates_path = templates_path
        self.templates = self._load_templates()
        self.current_bank = None
        self.current_template = None

    def _load_templates(self) -> Dict:
        """Load bank templates from JSON file"""
        if not os.path.exists(self.templates_path):
            print(f"[WARNING] Templates file not found: {self.templates_path}")
            return {"banks": {}, "default_gl_mappings": {}}

        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load templates: {e}")
            return {"banks": {}, "default_gl_mappings": {}}

    def detect_bank(self, text: str) -> Optional[str]:
        """
        Auto-detect bank from PDF text using template identifiers

        Args:
            text: Extracted text from PDF

        Returns:
            Bank name if detected, None if unknown
        """
        text_lower = text.lower()

        for bank_name, config in self.templates.get('banks', {}).items():
            identifiers = config.get('identifiers', [])
            for identifier in identifiers:
                if identifier.lower() in text_lower:
                    print(f"[INFO] Detected bank: {bank_name} (matched: '{identifier}')")
                    self.current_bank = bank_name
                    self.current_template = config
                    return bank_name

        print("[INFO] Bank not detected - will use AI fallback")
        return None

    def requires_ocr(self, bank_name: str) -> bool:
        """Check if bank requires OCR for text extraction"""
        config = self.templates.get('banks', {}).get(bank_name, {})
        return config.get('requires_ocr', False)

    def get_template(self, bank_name: str) -> Optional[Dict]:
        """Get template configuration for a bank"""
        return self.templates.get('banks', {}).get(bank_name)

    def parse_with_template(self, text: str, bank_name: str) -> List[Dict]:
        """
        Parse statement using bank-specific template

        Args:
            text: Extracted text from PDF
            bank_name: Detected bank name

        Returns:
            List of transaction dictionaries
        """
        template = self.get_template(bank_name)
        if not template:
            print(f"[ERROR] No template found for bank: {bank_name}")
            return []

        self.current_template = template
        transactions = []

        # Get deposit and withdrawal keywords
        deposit_keywords = template.get('deposit_keywords', ['DEPOSIT', 'INTEREST', 'CREDIT'])
        withdrawal_keywords = template.get('withdrawal_keywords', ['CHECK', 'DEBIT', 'WITHDRAWAL', 'FEE'])

        # Get transaction pattern
        txn_pattern = template.get('transaction_pattern', r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$')

        # Get year from text or use default
        year = self._extract_year(text)

        # Parse line by line
        lines = text.split('\n')
        seen = set()

        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue

            # Skip header/summary lines
            skip_sections = template.get('skip_sections', [])
            if any(skip.lower() in line.lower() for skip in skip_sections):
                continue

            # Try to match transaction pattern
            match = re.match(txn_pattern, line)
            if match:
                txn = self._parse_transaction_match(match, line, template, year,
                                                    deposit_keywords, withdrawal_keywords)
                if txn:
                    # Deduplication
                    key = (txn['date'], txn['description'][:30], abs(txn['amount']))
                    if key not in seen:
                        seen.add(key)
                        transactions.append(txn)

        print(f"[INFO] Template parser found {len(transactions)} transactions")
        return transactions

    def _parse_transaction_match(self, match, line: str, template: Dict,
                                  year: int, deposit_kw: List, withdrawal_kw: List) -> Optional[Dict]:
        """Parse a regex match into a transaction dictionary"""
        try:
            groups = match.groups()

            # Different templates have different group orders
            date_format = template.get('date_format', 'MM/DD')

            if date_format == 'MM/DD/YYYY':
                # Full date in first group
                date_str = groups[0]
                description = groups[1] if len(groups) > 1 else ''
                amount_str = groups[2] if len(groups) > 2 else groups[1]
            else:
                # MM/DD format - need to add year
                date_str = f"{groups[0]}/{year}"
                description = groups[1] if len(groups) > 1 else ''
                amount_str = groups[2] if len(groups) > 2 else groups[-1]

            # Clean amount
            amount_str = amount_str.replace(',', '').replace(' ', '')
            amount = float(amount_str)

            # Determine type based on keywords
            desc_upper = description.upper()
            is_deposit = any(kw.upper() in desc_upper for kw in deposit_kw)
            is_withdrawal = any(kw.upper() in desc_upper for kw in withdrawal_kw)

            # Default based on section if keywords don't match
            if not is_deposit and not is_withdrawal:
                # Check if line contains deposit/withdrawal indicators
                if 'DEPOSIT' in line.upper() or 'INTEREST' in line.upper() or 'CREDIT' in line.upper():
                    is_deposit = True
                else:
                    is_withdrawal = True

            if is_withdrawal:
                amount = -abs(amount)
            else:
                amount = abs(amount)

            # Format date
            date = self._format_date(date_str, year)
            if not date:
                return None

            return {
                'date': date,
                'description': description.strip(),
                'amount': amount,
                'is_deposit': amount > 0,
                'module': 'CR' if amount > 0 else 'CD',
                'confidence_score': 85,
                'confidence_level': 'high'
            }

        except Exception as e:
            print(f"[DEBUG] Failed to parse transaction: {e}")
            return None

    def _extract_year(self, text: str) -> int:
        """Extract statement year from text"""
        # Look for full date pattern
        match = re.search(r'\d{1,2}/\d{1,2}/(20\d{2})', text)
        if match:
            return int(match.group(1))

        # Look for year alone
        match = re.search(r'(202[0-9])', text)
        if match:
            return int(match.group(1))

        return datetime.now().year

    def _format_date(self, date_str: str, default_year: int) -> Optional[str]:
        """Format date string to YYYY-MM-DD"""
        try:
            # Try different formats
            for fmt in ['%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            # Try MM/DD format with default year
            match = re.match(r'(\d{1,2})/(\d{1,2})', date_str)
            if match:
                month, day = int(match.group(1)), int(match.group(2))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return f"{default_year}-{month:02d}-{day:02d}"

        except Exception as e:
            print(f"[DEBUG] Date format error: {e}")

        return None

    def extract_expected_totals(self, text: str, bank_name: str) -> Dict:
        """
        Extract expected totals from bank summary using template patterns

        Args:
            text: Extracted PDF text
            bank_name: Bank name

        Returns:
            Dict with expected_deposits and expected_withdrawals
        """
        template = self.get_template(bank_name)
        if not template:
            return {}

        summary_patterns = template.get('summary_patterns', {})
        result = {}

        # Extract deposits total
        deposit_pattern = summary_patterns.get('total_deposits')
        if deposit_pattern:
            matches = re.findall(deposit_pattern, text, re.IGNORECASE)
            if matches:
                # Handle patterns that return tuples (count, amount)
                total = 0
                for match in matches:
                    if isinstance(match, tuple):
                        amt_str = match[-1]  # Last group is usually the amount
                    else:
                        amt_str = match
                    try:
                        total += float(amt_str.replace(',', ''))
                    except:
                        pass
                result['expected_deposits'] = total

        # Extract withdrawals total
        withdrawal_pattern = summary_patterns.get('total_withdrawals')
        if withdrawal_pattern:
            matches = re.findall(withdrawal_pattern, text, re.IGNORECASE)
            if matches:
                total = 0
                for match in matches:
                    if isinstance(match, tuple):
                        amt_str = match[-1]
                    else:
                        amt_str = match
                    try:
                        total += float(amt_str.replace(',', ''))
                    except:
                        pass
                result['expected_withdrawals'] = total

        return result

    def assign_gl_codes(self, transactions: List[Dict]) -> List[Dict]:
        """
        Assign GL codes to transactions based on template mappings

        Args:
            transactions: List of parsed transactions

        Returns:
            Transactions with gl_code and fund_code assigned
        """
        gl_mappings = self.templates.get('default_gl_mappings', {})
        deposit_mappings = gl_mappings.get('deposits', {})
        withdrawal_mappings = gl_mappings.get('withdrawals', {})

        for txn in transactions:
            desc_upper = txn.get('description', '').upper()
            is_deposit = txn.get('amount', 0) > 0

            mappings = deposit_mappings if is_deposit else withdrawal_mappings
            best_match = None
            best_confidence = 'low'

            # Find best matching GL code
            for keyword, mapping in mappings.items():
                if keyword.upper() in desc_upper:
                    if best_match is None or self._compare_confidence(mapping['confidence'], best_confidence) > 0:
                        best_match = mapping
                        best_confidence = mapping['confidence']

            if best_match:
                txn['gl_code'] = best_match.get('gl', '')
                txn['fund_code'] = best_match.get('fund', 'General')
                txn['gl_confidence'] = best_confidence

        return transactions

    def _compare_confidence(self, a: str, b: str) -> int:
        """Compare confidence levels: high > medium > low"""
        levels = {'high': 3, 'medium': 2, 'low': 1}
        return levels.get(a, 0) - levels.get(b, 0)

    def get_supported_banks(self) -> List[str]:
        """Get list of banks with templates"""
        return list(self.templates.get('banks', {}).keys())

    def add_bank_template(self, bank_name: str, template: Dict) -> bool:
        """
        Add a new bank template (runtime only, doesn't persist)

        Args:
            bank_name: Name of the bank
            template: Template configuration

        Returns:
            True if added successfully
        """
        self.templates['banks'][bank_name] = template
        print(f"[INFO] Added template for bank: {bank_name}")
        return True
