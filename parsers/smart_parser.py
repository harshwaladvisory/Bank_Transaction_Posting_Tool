# -*- coding: utf-8 -*-
"""
Smart Bank Statement Parser - Template-based + AI Fallback

Architecture:
1. Load bank templates from JSON config
2. Auto-detect bank using template identifiers
3. Parse using template patterns (regex-based, fast)
4. If no template matches OR parsing fails, use AI fallback
5. AI can use local LLM (Ollama) or Claude API

This approach is scalable - add new banks via JSON config, no code changes needed!
"""

import re
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# OCR and PDF libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# AI Parser for fallback
try:
    from .ai_parser import AIParser
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Config paths
try:
    from config import TESSERACT_CMD, POPPLER_PATH
except ImportError:
    TESSERACT_CMD = None
    POPPLER_PATH = None


class SmartParser:
    """
    Smart bank statement parser using templates + AI fallback.

    Usage:
        parser = SmartParser()
        transactions = parser.parse("statement.pdf")
        summary = parser.get_summary()
    """

    # Maximum transaction amount (configurable via templates)
    DEFAULT_MAX_AMOUNT = 10000000.00  # $10 million

    def __init__(self, templates_path: str = None, use_ai_fallback: bool = True):
        """
        Initialize smart parser.

        Args:
            templates_path: Path to bank_templates.json (auto-detected if None)
            use_ai_fallback: Enable AI fallback for unknown banks
        """
        # Auto-detect templates path
        if templates_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            templates_path = os.path.join(base_dir, 'config', 'bank_templates.json')

        self.templates = self._load_templates(templates_path)
        self.use_ai_fallback = use_ai_fallback
        # Always create AIParser for enhanced regex fallback, even if AI (LLM) is disabled
        self.ai_parser = AIParser() if AI_AVAILABLE else None

        # State
        self.transactions = []
        self.bank_name = None
        self.bank_template = None
        self.statement_year = datetime.now().year
        self.raw_text = None
        self.parsing_method = None  # 'template' or 'ai'
        self.debug = True

        # Metadata storage
        self._expected_deposits = None
        self._expected_withdrawals = None
        self._ocr_used = False
        self._ocr_fixes = []

    def _load_templates(self, path: str) -> Dict:
        """Load bank templates from JSON file."""
        if not os.path.exists(path):
            print(f"[WARNING] Templates file not found: {path}")
            return {"banks": {}, "default_gl_mappings": {}}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load templates: {e}")
            return {"banks": {}, "default_gl_mappings": {}}

    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse bank statement using smart detection.

        Flow:
        1. Extract text (pdfplumber -> OCR fallback)
        2. Detect bank using template identifiers
        3. If template found: parse with template
        4. If no template OR template fails: use AI fallback
        5. Apply validation and cleanup
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"[INFO] SmartParser: Parsing {file_path}", flush=True)

        # Step 1: Extract text
        text = self._extract_text(file_path)
        if not text or len(text.strip()) < 100:
            print("[ERROR] Could not extract text from PDF", flush=True)
            return []

        self.raw_text = text

        # Step 2: Detect bank
        self.bank_name, self.bank_template = self._detect_bank(text)
        print(f"[INFO] Detected Bank: {self.bank_name}", flush=True)

        # Step 3: Extract year
        self._extract_year(text)

        # Step 4: Parse transactions
        transactions = []

        if self.bank_template:
            # Try template-based parsing
            print(f"[INFO] Using template for: {self.bank_name}", flush=True)
            transactions = self._parse_with_template(text, self.bank_template)
            self.parsing_method = 'template'

            # Validate template results
            if not self._validate_parsing(transactions, text):
                print("[WARNING] Template parsing may be incomplete, trying AI...", flush=True)
                if self.ai_parser and self.ai_parser.is_available():
                    ai_transactions = self.ai_parser.parse(text)
                    if len(ai_transactions) > len(transactions):
                        transactions = ai_transactions
                        self.parsing_method = 'ai'
        else:
            # No template - use AI or enhanced regex fallback
            print(f"[INFO] No template for '{self.bank_name}', using fallback parser...", flush=True)
            if self.use_ai_fallback and self.ai_parser and self.ai_parser.is_available():
                # Use LLM for parsing (if enabled and available)
                transactions = self.ai_parser.parse(text)
                self.parsing_method = 'ai'
            elif self.ai_parser:
                # Use enhanced regex fallback from ai_parser (more comprehensive than generic)
                print("[INFO] Using enhanced universal regex parser...", flush=True)
                transactions = self.ai_parser._regex_fallback(text)
                self.parsing_method = 'universal_regex'
            else:
                # Last resort: basic generic regex parsing
                print("[WARNING] AI parser not loaded, using basic generic parser...", flush=True)
                transactions = self._generic_parse(text)
                self.parsing_method = 'generic'

        # Step 5: Final validation
        transactions = self._final_validation(transactions)
        self.transactions = transactions

        print(f"[INFO] Parsed {len(transactions)} transactions using {self.parsing_method}", flush=True)

        # Store metadata
        self._store_metadata(transactions, text)

        return transactions

    def _extract_text(self, file_path: str) -> str:
        """Extract text using pdfplumber, fallback to OCR."""
        text = ""

        # Try pdfplumber first
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"[WARNING] pdfplumber failed: {e}")

        # If text is too short, use OCR
        if len(text.strip()) < 100 and OCR_AVAILABLE:
            print("[INFO] Using OCR for text extraction...", flush=True)
            self._ocr_used = True
            text = self._extract_with_ocr(file_path)

        # Clean text
        text = self._clean_text(text)

        return text

    def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR."""
        try:
            if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

            print("[INFO] Converting PDF to images...", flush=True)

            if POPPLER_PATH and os.path.exists(POPPLER_PATH):
                images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
            else:
                images = convert_from_path(file_path, dpi=300)

            print(f"[INFO] OCR processing {len(images)} pages...", flush=True)

            all_text = ""
            for i, image in enumerate(images):
                custom_config = r'--oem 3 --psm 6'
                page_text = pytesseract.image_to_string(image, config=custom_config)
                if page_text:
                    all_text += page_text + "\n"

            return all_text

        except Exception as e:
            print(f"[ERROR] OCR failed: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Clean OCR artifacts from text."""
        if not text:
            return ""

        # Remove common OCR garbage
        text = re.sub(r'^[\|\=\_\~\-\—\–]+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*[\|\=\_\~\—\–]+\s*', ' ', text)
        text = re.sub(r' +', ' ', text)

        return text

    def _detect_bank(self, text: str) -> Tuple[str, Optional[Dict]]:
        """
        Detect bank using template identifiers.

        Returns:
            Tuple of (bank_name, template_dict or None)
        """
        text_lower = text.lower()

        for bank_name, template in self.templates.get('banks', {}).items():
            identifiers = template.get('identifiers', [])
            for identifier in identifiers:
                if identifier.lower() in text_lower:
                    print(f"[DEBUG] Matched '{identifier}' -> {bank_name}", flush=True)
                    return bank_name, template

        # No template match - return generic
        return "Unknown Bank", None

    def _extract_year(self, text: str):
        """Extract statement year from text."""
        # Look for full date first
        match = re.search(r'\d{1,2}/\d{1,2}/(20\d{2})', text)
        if match:
            self.statement_year = int(match.group(1))
            return

        # Look for year alone
        match = re.search(r'(202[0-9])', text)
        if match:
            self.statement_year = int(match.group(1))

    def _parse_with_template(self, text: str, template: Dict) -> List[Dict]:
        """
        Parse statement using bank-specific template.

        Supports two template formats:
        1. Single pattern: transaction_pattern (legacy)
        2. Multiple patterns: transaction_patterns array (new - recommended)

        Template structure:
        - transaction_patterns: array of pattern objects with name, pattern, groups, type
        - sections: deposit/withdrawal section markers (optional)
        - date_format: MM/DD or MM/DD/YYYY
        - deposit_keywords: words indicating deposits
        - withdrawal_keywords: words indicating withdrawals
        - skip_patterns: lines to skip
        - ocr_fixes: OCR error corrections to apply
        """
        transactions = []
        seen = set()

        # Get template config
        date_format = template.get('date_format', 'MM/DD')
        deposit_kw = template.get('deposit_keywords', ['DEPOSIT', 'INTEREST', 'CREDIT'])
        withdrawal_kw = template.get('withdrawal_keywords', ['CHECK', 'DEBIT', 'WITHDRAWAL', 'FEE'])
        skip_patterns = template.get('skip_patterns', template.get('skip_sections', []))
        ocr_fixes = template.get('ocr_fixes', {})

        # Extract expected totals for validation
        self._extract_expected_totals(text, template)

        # Check for new multi-pattern format
        multi_patterns = template.get('transaction_patterns', [])

        if multi_patterns:
            # New format: multiple transaction patterns
            transactions = self._parse_with_multi_patterns(text, template, multi_patterns)
        elif template.get('sections'):
            # Section-based parsing
            transactions = self._parse_sections(text, template)
        else:
            # Legacy single pattern
            txn_pattern = template.get('transaction_pattern', r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$')
            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                if len(line) < 10:
                    continue

                # Skip unwanted patterns
                if any(skip.lower() in line.lower() for skip in skip_patterns):
                    continue

                match = re.match(txn_pattern, line)
                if match:
                    txn = self._parse_match(match, line, date_format, deposit_kw, withdrawal_kw)
                    if txn:
                        key = (txn['date'], txn['description'][:30], abs(txn['amount']))
                        if key not in seen:
                            seen.add(key)
                            transactions.append(txn)

        return transactions

    def _parse_with_multi_patterns(self, text: str, template: Dict, patterns: List[Dict]) -> List[Dict]:
        """
        Parse using multiple transaction patterns.

        Each pattern object has:
        - name: pattern identifier
        - pattern: regex pattern
        - groups: dict mapping field names to group numbers
        - type: 'withdrawal', 'deposit', or 'auto'
        """
        transactions = []
        seen = set()
        lines = text.split('\n')

        date_format = template.get('date_format', 'MM/DD')
        deposit_kw = template.get('deposit_keywords', ['DEPOSIT', 'INTEREST', 'CREDIT'])
        withdrawal_kw = template.get('withdrawal_keywords', ['CHECK', 'DEBIT', 'WITHDRAWAL', 'FEE'])
        skip_patterns = template.get('skip_patterns', [])
        ocr_fixes = template.get('ocr_fixes', {})

        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue

            # Skip unwanted patterns
            if any(skip.lower() in line.lower() for skip in skip_patterns):
                continue

            # Try each pattern
            for pattern_config in patterns:
                regex = pattern_config.get('pattern')
                groups = pattern_config.get('groups', {})
                txn_type = pattern_config.get('type', 'auto')

                match = re.match(regex, line)
                if match:
                    try:
                        # Extract fields using group mapping
                        date_str = match.group(groups.get('date', 1))
                        description = match.group(groups.get('description', 2))
                        amount_str = match.group(groups.get('amount', 3))

                        # Apply OCR fixes
                        if ocr_fixes.get('date_day_90_offset'):
                            date_str = self._fix_ocr_date(date_str)

                        # Clean description
                        description = self._clean_description(description)

                        # Parse amount
                        amount = float(amount_str.replace(',', '').replace(' ', ''))

                        # Format date
                        date = self._format_date(date_str, date_format)
                        if not date:
                            continue

                        # Determine transaction type
                        if txn_type == 'withdrawal':
                            amount = -abs(amount)
                            is_deposit = False
                        elif txn_type == 'deposit':
                            amount = abs(amount)
                            is_deposit = True
                        else:  # auto
                            desc_upper = description.upper()
                            is_deposit = any(kw.upper() in desc_upper for kw in deposit_kw)
                            is_withdrawal = any(kw.upper() in desc_upper for kw in withdrawal_kw)

                            if is_withdrawal:
                                amount = -abs(amount)
                                is_deposit = False
                            elif is_deposit:
                                amount = abs(amount)
                            else:
                                amount = -abs(amount)
                                is_deposit = False

                        # Dedup
                        key = (date, abs(amount), description[:20])
                        if key in seen:
                            continue
                        seen.add(key)

                        transactions.append({
                            'date': date,
                            'description': description if description else ('DEPOSIT' if is_deposit else 'WITHDRAWAL'),
                            'amount': amount,
                            'is_deposit': is_deposit,
                            'module': 'CR' if is_deposit else 'CD',
                            'confidence_score': 85,
                            'confidence_level': 'high',
                            'parsed_by': 'template',
                            'pattern_used': pattern_config.get('name', 'unknown')
                        })

                        if self.debug:
                            txn_label = 'deposit' if is_deposit else 'withdrawal'
                            print(f"[DEBUG] {self.bank_name} {txn_label}: {date} ${abs(amount):.2f}", flush=True)

                        break  # Stop trying other patterns for this line

                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG] Pattern '{pattern_config.get('name')}' failed: {e}", flush=True)
                        continue

        return transactions

    def _fix_ocr_date(self, date_str: str) -> str:
        """Fix common OCR errors in dates (e.g., 04/97 -> 04/07)."""
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
        if not match:
            return date_str

        month, day, year = match.groups()
        month = int(month)
        day = int(day)

        # Fix day > 31 (OCR error: 0 misread as 9)
        if day > 31:
            if day >= 90:
                day = day - 90
            elif day >= 60:
                day = day - 60
            elif day >= 30:
                day = day - 30
            if day == 0:
                day = 10

        # Fix month > 12
        if month > 12:
            if month >= 90:
                month = month - 90
            elif month >= 10:
                month = month % 10
            if month == 0:
                month = 10

        return f"{month:02d}/{day:02d}/{year}"

    def _clean_description(self, desc: str) -> str:
        """Clean transaction description."""
        if not desc:
            return ''

        # Remove common OCR garbage
        desc = re.sub(r'\b(ccm|cain|END)\b', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s+', ' ', desc).strip()

        # If mostly empty, return empty
        if len(desc) < 3 or not re.search(r'[a-zA-Z]{2,}', desc):
            return ''

        return desc[:100]

    def _parse_sections(self, text: str, template: Dict) -> List[Dict]:
        """Parse by tracking deposit/withdrawal sections."""
        transactions = []
        seen = set()
        lines = text.split('\n')

        sections_config = template.get('sections', {})
        deposit_markers = sections_config.get('deposits', {}).get('start_markers', [])
        deposit_end = sections_config.get('deposits', {}).get('end_markers', [])
        withdrawal_markers = sections_config.get('withdrawals', {}).get('start_markers', [])
        withdrawal_end = sections_config.get('withdrawals', {}).get('end_markers', [])

        txn_pattern = template.get('transaction_pattern', r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$')
        date_format = template.get('date_format', 'MM/DD')
        skip_sections = template.get('skip_sections', [])

        current_section = None  # 'deposit', 'withdrawal', or None

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            if len(line_stripped) < 5:
                continue

            # Check for section markers
            for marker in deposit_markers:
                if marker.lower() in line_lower:
                    current_section = 'deposit'
                    break

            for marker in withdrawal_markers:
                if marker.lower() in line_lower:
                    current_section = 'withdrawal'
                    break

            # Check for section end
            for marker in deposit_end + withdrawal_end:
                if marker.lower() in line_lower:
                    if marker.lower() in [m.lower() for m in skip_sections]:
                        current_section = None

            # Skip if not in transaction section
            if current_section is None:
                continue

            # Skip unwanted content
            if any(skip.lower() in line_lower for skip in skip_sections):
                continue

            # Try to match transaction
            match = re.match(txn_pattern, line_stripped)
            if match:
                txn = self._parse_match_with_section(match, line_stripped, date_format, current_section)
                if txn:
                    key = (txn['date'], abs(txn['amount']))
                    if key not in seen:
                        seen.add(key)
                        transactions.append(txn)

        return transactions

    def _parse_match(self, match, line: str, date_format: str, deposit_kw: List, withdrawal_kw: List) -> Optional[Dict]:
        """Parse a regex match into a transaction."""
        try:
            groups = match.groups()

            # Extract based on pattern (typically: date, description/amount, amount)
            date_str = groups[0]

            # Handle different group orders
            if len(groups) >= 3:
                # Pattern: date, amount, description OR date, description, amount
                if re.match(r'^[\d,]+\.\d{2}$', groups[1]):
                    amount_str = groups[1]
                    description = groups[2] if len(groups) > 2 else ''
                else:
                    description = groups[1]
                    amount_str = groups[2] if len(groups) > 2 else groups[-1]
            else:
                description = ''
                amount_str = groups[-1]

            # Parse amount
            amount = float(amount_str.replace(',', '').replace(' ', ''))

            # Format date
            date = self._format_date(date_str, date_format)
            if not date:
                return None

            # Determine transaction type
            desc_upper = description.upper()
            is_deposit = any(kw.upper() in desc_upper for kw in deposit_kw)
            is_withdrawal = any(kw.upper() in desc_upper for kw in withdrawal_kw)

            if is_withdrawal:
                amount = -abs(amount)
            elif is_deposit:
                amount = abs(amount)
            else:
                # Default based on context
                amount = -abs(amount)  # Conservative: assume withdrawal

            return {
                'date': date,
                'description': description.strip()[:100],
                'amount': amount,
                'is_deposit': amount > 0,
                'module': 'CR' if amount > 0 else 'CD',
                'confidence_score': 80,
                'confidence_level': 'high',
                'parsed_by': 'template'
            }

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Failed to parse match: {e}")
            return None

    def _parse_match_with_section(self, match, line: str, date_format: str, section: str) -> Optional[Dict]:
        """Parse match using section context for transaction type."""
        try:
            groups = match.groups()
            date_str = groups[0]

            # Handle different group orders
            if len(groups) >= 3:
                if re.match(r'^[\d,]+\.\d{2}$', groups[1]):
                    amount_str = groups[1]
                    description = groups[2] if len(groups) > 2 else ''
                else:
                    description = groups[1]
                    amount_str = groups[2] if len(groups) > 2 else groups[-1]
            else:
                description = ''
                amount_str = groups[-1]

            amount = float(amount_str.replace(',', '').replace(' ', ''))
            date = self._format_date(date_str, date_format)
            if not date:
                return None

            # Use section to determine type
            is_deposit = (section == 'deposit')
            if not is_deposit:
                amount = -abs(amount)
            else:
                amount = abs(amount)

            return {
                'date': date,
                'description': description.strip()[:100],
                'amount': amount,
                'is_deposit': is_deposit,
                'module': 'CR' if is_deposit else 'CD',
                'confidence_score': 85,
                'confidence_level': 'high',
                'parsed_by': 'template'
            }

        except Exception as e:
            return None

    def _format_date(self, date_str: str, date_format: str) -> Optional[str]:
        """Format date string to MM/DD/YYYY."""
        try:
            date_str = date_str.strip()

            if date_format == 'MM/DD':
                # Add year
                match = re.match(r'^(\d{1,2})/(\d{1,2})$', date_str)
                if match:
                    month, day = int(match.group(1)), int(match.group(2))
                    if 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{month:02d}/{day:02d}/{self.statement_year}"

            elif date_format == 'MM/DD/YYYY':
                match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_str)
                if match:
                    month, day, year = match.groups()
                    if len(year) == 2:
                        year = '20' + year
                    return f"{int(month):02d}/{int(day):02d}/{year}"

            # Fallback: try to parse any date format
            for fmt in ['%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%m/%d/%Y')
                except ValueError:
                    continue

        except Exception:
            pass

        return None

    def _extract_expected_totals(self, text: str, template: Dict):
        """Extract expected totals from bank summary."""
        summary_patterns = template.get('summary_patterns', {})

        # Extract deposits total
        dep_pattern = summary_patterns.get('total_deposits')
        if dep_pattern:
            matches = re.findall(dep_pattern, text, re.IGNORECASE)
            if matches:
                total = 0
                for match in matches:
                    amt_str = match[-1] if isinstance(match, tuple) else match
                    try:
                        total += float(amt_str.replace(',', ''))
                    except:
                        pass
                self._expected_deposits = total

        # Extract withdrawals total
        wd_pattern = summary_patterns.get('total_withdrawals')
        if wd_pattern:
            matches = re.findall(wd_pattern, text, re.IGNORECASE)
            if matches:
                total = 0
                for match in matches:
                    amt_str = match[-1] if isinstance(match, tuple) else match
                    try:
                        total += float(amt_str.replace(',', ''))
                    except:
                        pass
                self._expected_withdrawals = total

    def _generic_parse(self, text: str) -> List[Dict]:
        """Generic fallback parser for unknown formats."""
        transactions = []
        seen = set()
        lines = text.split('\n')

        # Common transaction patterns
        patterns = [
            r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            r'^(\d{1,2}/\d{1,2})\s+([\d,]+\.\d{2})\s+(.+)',
        ]

        deposit_keywords = ['deposit', 'interest', 'credit', 'transfer in']
        withdrawal_keywords = ['check', 'withdrawal', 'debit', 'fee', 'payment', 'transfer out']

        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue

            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    date_str = groups[0]

                    # Determine which group is amount vs description
                    if re.match(r'^[\d,]+\.\d{2}$', groups[1]):
                        amount_str = groups[1]
                        description = groups[2] if len(groups) > 2 else ''
                    else:
                        description = groups[1]
                        amount_str = groups[2] if len(groups) > 2 else groups[-1]

                    try:
                        amount = float(amount_str.replace(',', ''))
                    except:
                        continue

                    # Determine type
                    desc_lower = description.lower()
                    is_deposit = any(kw in desc_lower for kw in deposit_keywords)
                    is_withdrawal = any(kw in desc_lower for kw in withdrawal_keywords)

                    if is_withdrawal:
                        amount = -abs(amount)
                    elif is_deposit:
                        amount = abs(amount)
                    else:
                        amount = -abs(amount)

                    # Format date
                    date = self._format_date(date_str, 'MM/DD/YYYY' if '/' in date_str and len(date_str) > 5 else 'MM/DD')
                    if not date:
                        continue

                    key = (date, abs(amount))
                    if key not in seen:
                        seen.add(key)
                        transactions.append({
                            'date': date,
                            'description': description[:100],
                            'amount': amount,
                            'is_deposit': amount > 0,
                            'module': 'CR' if amount > 0 else 'CD',
                            'confidence_score': 60,
                            'confidence_level': 'low',
                            'parsed_by': 'generic'
                        })
                    break

        return transactions

    def _validate_parsing(self, transactions: List[Dict], text: str) -> bool:
        """Validate parsing results against expected totals."""
        if not transactions:
            return False

        # If we have expected totals, compare
        if self._expected_deposits:
            parsed_dep = sum(t['amount'] for t in transactions if t['amount'] > 0)
            diff_pct = abs(parsed_dep - self._expected_deposits) / self._expected_deposits * 100
            if diff_pct > 20:
                return False

        if self._expected_withdrawals:
            parsed_wd = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
            diff_pct = abs(parsed_wd - self._expected_withdrawals) / self._expected_withdrawals * 100
            if diff_pct > 20:
                return False

        return True

    def _final_validation(self, transactions: List[Dict]) -> List[Dict]:
        """Final validation and smart deduplication.

        Allows multiple transactions with same date/description/amount up to a limit.
        This handles banks that have multiple identical deposits on the same date
        (e.g., multiple $720 DEPOSIT entries on 07/25).

        Also detects and removes repeated statement sections (entire statement duplicates).
        """
        max_amount = self.templates.get('max_transaction_amount', self.DEFAULT_MAX_AMOUNT)
        seen_counts = {}  # Track how many times we've seen each key
        MAX_DUPLICATES = 2  # Allow up to 2 identical transactions (catches statement duplicates)
        valid = []

        for txn in transactions:
            # Must have date and amount
            if not txn.get('date') or txn.get('amount') is None:
                continue

            # Check amount bounds
            if abs(txn['amount']) > max_amount or abs(txn['amount']) < 0.01:
                continue

            # Smart dedup - allow up to MAX_DUPLICATES of same transaction
            key = (txn['date'], txn.get('description', '')[:50], round(abs(txn['amount']), 2))
            current_count = seen_counts.get(key, 0)

            if current_count < MAX_DUPLICATES:
                seen_counts[key] = current_count + 1
                valid.append(txn)
            # else: skip - likely duplicate from repeated statement section

        return valid

    def _store_metadata(self, transactions: List[Dict], text: str):
        """Store parsing metadata."""
        deposits = [t for t in transactions if t.get('amount', 0) > 0]
        withdrawals = [t for t in transactions if t.get('amount', 0) < 0]

        self.parsing_metadata = {
            'bank_name': self.bank_name,
            'parsing_method': self.parsing_method,
            'template_used': self.bank_template is not None,
            'ocr_used': self._ocr_used,
            'statement_year': self.statement_year,
            'total_transactions': len(transactions),
            'deposit_count': len(deposits),
            'withdrawal_count': len(withdrawals),
            'parsed_deposits': sum(t['amount'] for t in deposits),
            'parsed_withdrawals': sum(abs(t['amount']) for t in withdrawals),
            'expected_deposits': self._expected_deposits,
            'expected_withdrawals': self._expected_withdrawals,
            'warnings': []
        }

        # Add validation warnings
        if self._expected_deposits and self.parsing_metadata['parsed_deposits']:
            diff = abs(self.parsing_metadata['parsed_deposits'] - self._expected_deposits)
            if diff > 1:
                pct = diff / self._expected_deposits * 100
                self.parsing_metadata['warnings'].append({
                    'type': 'deposit_mismatch',
                    'message': f"Deposit mismatch: ${self.parsing_metadata['parsed_deposits']:,.2f} vs expected ${self._expected_deposits:,.2f} ({pct:.1f}%)",
                    'severity': 'high' if pct > 5 else 'medium'
                })

    def get_summary(self) -> Dict:
        """Get parsing summary."""
        if not self.transactions:
            return {'count': 0, 'total_deposits': 0, 'total_withdrawals': 0}

        deposits = sum(t['amount'] for t in self.transactions if t['amount'] > 0)
        withdrawals = sum(t['amount'] for t in self.transactions if t['amount'] < 0)

        return {
            'count': len(self.transactions),
            'total_deposits': deposits,
            'total_withdrawals': withdrawals,
            'net_change': deposits + withdrawals,
            'bank_name': self.bank_name,
            'parsing_method': self.parsing_method
        }

    def get_parsing_metadata(self) -> Dict:
        """Get detailed parsing metadata."""
        return getattr(self, 'parsing_metadata', {})

    def add_bank_template(self, bank_name: str, template: Dict):
        """Add a new bank template at runtime."""
        self.templates['banks'][bank_name] = template
        print(f"[INFO] Added template for: {bank_name}")


# Convenience function
def smart_parse(file_path: str, use_ai: bool = True) -> Tuple[List[Dict], Dict]:
    """
    Parse a bank statement using smart detection.

    Returns:
        Tuple of (transactions, summary)
    """
    parser = SmartParser(use_ai_fallback=use_ai)
    transactions = parser.parse(file_path)
    summary = parser.get_summary()
    return transactions, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        transactions, summary = smart_parse(sys.argv[1])

        print(f"\n{'='*60}")
        print(f"Smart Parser Results")
        print(f"{'='*60}")
        print(f"Bank: {summary['bank_name']}")
        print(f"Method: {summary['parsing_method']}")
        print(f"Transactions: {summary['count']}")
        print(f"Deposits: ${summary['total_deposits']:,.2f}")
        print(f"Withdrawals: ${abs(summary['total_withdrawals']):,.2f}")

        print(f"\n{'='*60}")
        print("Transactions:")
        for t in transactions[:10]:
            print(f"  {t['date']} | {t['description'][:40]:40} | ${t['amount']:>10,.2f}")
    else:
        print("Usage: python smart_parser.py <path_to_pdf>")
