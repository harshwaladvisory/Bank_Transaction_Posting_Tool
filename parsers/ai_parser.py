"""
AI-Powered Parser for Unknown Bank Formats

Uses Claude API or local LLM (Ollama/LM Studio) as fallback
when no template exists for a bank.
"""

import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime


class AIParser:
    """
    AI fallback parser for unknown bank statement formats.

    SECURITY: Uses ONLY local LLM (Ollama) - NO external API calls.
    Banking data never leaves your machine.
    """

    def __init__(self, use_local: bool = True, local_url: str = None):
        """
        Initialize AI parser

        Args:
            use_local: Always True - external APIs disabled for security.
            local_url: URL for local LLM API (default: Ollama)
        """
        self.use_local = True  # ALWAYS local for security
        self.local_url = local_url or "http://localhost:11434/api/generate"
        self.api_key = None  # DISABLED - no external API for banking data
        self._available = None

    def is_available(self) -> bool:
        """Check if AI parsing is available"""
        if self._available is not None:
            return self._available

        if self.use_local:
            self._available = self._check_local_llm()
        else:
            self._available = False  # External APIs disabled

        return self._available

    def _check_local_llm(self) -> bool:
        """Check if local LLM (Ollama) is running"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                # Check if a model is available
                models = response.json().get('models', [])
                if models:
                    print(f"[INFO] Ollama available with models: {[m['name'] for m in models]}")
                    return True
            return False
        except:
            return False

    def parse(self, text: str, max_chars: int = 15000) -> List[Dict]:
        """
        Use AI to extract transactions from bank statement text

        Args:
            text: Extracted text from PDF
            max_chars: Maximum characters to send to AI

        Returns:
            List of transaction dictionaries
        """
        if not self.is_available():
            print("[WARNING] AI parser not available. Using regex fallback.")
            return self._regex_fallback(text)

        # Truncate text if too long
        text_truncated = text[:max_chars] if len(text) > max_chars else text

        prompt = self._build_prompt(text_truncated)

        try:
            if self.use_local:
                response = self._call_local_llm(prompt)
            else:
                response = self._call_claude_api(prompt)

            transactions = self._parse_json_response(response)
            print(f"[INFO] AI parser extracted {len(transactions)} transactions")
            return transactions

        except Exception as e:
            print(f"[ERROR] AI parsing failed: {e}")
            return self._regex_fallback(text)

    def _build_prompt(self, text: str) -> str:
        """Build the prompt for AI extraction"""
        return f"""You are a bank statement parser. Extract ALL transactions from this statement.

For each transaction, identify:
1. Date (format as MM/DD/YYYY)
2. Description (clean text, remove OCR garbage like |, =, _, ~)
3. Amount (as a positive number, no $ or commas)
4. Type: "deposit" or "withdrawal"

Rules:
- Deposits/Credits = money IN (positive for customer)
- Withdrawals/Debits/Checks = money OUT (negative for customer)
- INTEREST is a deposit
- CHECK is a withdrawal
- Skip daily balances, summaries, headers, page numbers
- Include ALL actual transactions, don't skip any
- If unsure about type, use context clues from description

Return ONLY a valid JSON array, no other text or explanation:
[
  {{"date": "MM/DD/YYYY", "description": "...", "amount": 123.45, "type": "deposit"}},
  {{"date": "MM/DD/YYYY", "description": "...", "amount": 456.78, "type": "withdrawal"}}
]

BANK STATEMENT TEXT:
{text}
"""

    def _call_local_llm(self, prompt: str) -> str:
        """Call Ollama or compatible local LLM"""
        import requests

        try:
            response = requests.post(
                self.local_url,
                json={
                    "model": "llama3.2:latest",  # Your installed model
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent output
                        "num_predict": 4000
                    }
                },
                timeout=300  # 5 minutes for large PDFs
            )

            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                raise Exception(f"Local LLM returned status {response.status_code}")

        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to local LLM. Is Ollama running?")

    def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API for high accuracy parsing"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except ImportError:
            raise Exception("anthropic package not installed. Run: pip install anthropic")

    def _parse_json_response(self, response: str) -> List[Dict]:
        """Parse AI response into transaction list"""
        transactions = []

        # Try to extract JSON array from response
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
        if not json_match:
            print("[WARNING] No JSON array found in AI response")
            return []

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return []

        # Convert to standard format
        for item in data:
            try:
                date_str = item.get('date', '')
                description = item.get('description', '')
                amount = float(item.get('amount', 0))
                txn_type = item.get('type', 'withdrawal').lower()

                # Format date
                date = self._format_date(date_str)
                if not date:
                    continue

                # Set amount sign based on type
                if txn_type == 'withdrawal':
                    amount = -abs(amount)
                else:
                    amount = abs(amount)

                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'is_deposit': amount > 0,
                    'module': 'CR' if amount > 0 else 'CD',
                    'confidence_score': 75,  # AI confidence
                    'confidence_level': 'medium',
                    'parsed_by': 'ai'
                })

            except Exception as e:
                print(f"[DEBUG] Failed to process AI transaction: {e}")
                continue

        return transactions

    def _format_date(self, date_str: str) -> Optional[str]:
        """Format date string to YYYY-MM-DD"""
        if not date_str:
            return None

        # Try various formats
        formats = [
            '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d',
            '%m-%d-%Y', '%m-%d-%y', '%d/%m/%Y'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    def _regex_fallback(self, text: str) -> List[Dict]:
        """
        Enhanced universal regex parser - handles most bank formats without AI.

        This is the PRIMARY parsing method for unknown banks.
        No data leaves your machine - fully local and secure.
        """
        transactions = []
        lines = text.split('\n')
        year = datetime.now().year

        # Extract year from statement date (more reliable than first year found)
        # Look for patterns like "08/30/2024", "07/31/25", "Statement Date 08/30/24"
        statement_date_patterns = [
            r'Statement\s*Date[:\s]+(\d{1,2}/\d{1,2}/(\d{4}))',  # Statement Date: 08/30/2024
            r'(\d{1,2}/\d{1,2}/(\d{4}))',  # 08/30/2024
            r'(\d{1,2}/\d{1,2}/(\d{2}))\b',  # 08/30/24 (2-digit year)
        ]
        for pattern in statement_date_patterns:
            year_match = re.search(pattern, text)
            if year_match:
                year_str = year_match.group(2)
                if len(year_str) == 2:
                    year = 2000 + int(year_str)
                else:
                    year = int(year_str)
                break

        # Track line numbers for better deduplication (allow same transactions on different lines)
        line_counter = 0

        # Comprehensive deposit/withdrawal keywords
        # NOTE: Order matters - more specific keywords should come first
        deposit_keywords = [
            'DEPOSIT', 'INTEREST', 'CREDIT', 'ACH CREDIT', 'WIRE IN',
            'TRANSFER IN', 'DIRECT DEP', 'PAYROLL', 'TAX REFUND',
            'DIVIDEND', 'REFUND', 'REIMBURSE', 'GRANT', 'HUD', 'NAHASDA',
            'CAPITALIZATION', 'INCOMING', 'RECEIVED'
        ]

        withdrawal_keywords = [
            'CHECK', 'WITHDRAWAL', 'DEBIT', 'FEE', 'SERVICE CHARGE',
            'ACH DEBIT', 'WIRE OUT', 'TRANSFER OUT', 'PAYMENT', 'PAYROLL TAX',
            'IRS', 'EFTPS', 'INSURANCE', 'UTILITY', 'ELECTRIC', 'WATER',
            'PHONE', 'INTERNET', 'RENT', 'LEASE', 'PURCHASE', 'POS PURCHASE',
            'POS DEBIT', 'ATM', 'CARD', 'OUTGOING', 'SENT'
        ]

        def match_keyword(text, keywords):
            """Match keywords using word boundaries to avoid false positives.
            E.g., 'POS' should not match inside 'DEPOSIT'."""
            text_upper = text.upper()
            for kw in keywords:
                # Use word boundary matching
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_upper):
                    return kw
            return None

        # Skip patterns - lines that look like transactions but aren't
        skip_patterns = [
            'balance', 'summary', 'total', 'page', 'statement', 'account',
            'date', 'description', 'amount', 'opening', 'ending', 'closing',
            'beginning', 'previous', 'member fdic', 'routing', 'customer'
        ]

        # Universal transaction patterns covering most US banks
        patterns = [
            # Pattern 1: MM/DD/YYYY Description Amount (most common)
            (r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+\$?([\d,]+\.\d{2})\s*$', 'date_desc_amt'),

            # Pattern 2: MM/DD/YYYY Description (Amount) Balance - withdrawal in parens
            (r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s*\(\s*\$?([\d,]+\.\d{2})\s*\)', 'date_desc_withdrawal'),

            # Pattern 3: MM/DD/YYYY Description Amount Balance
            (r'^(\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s+[\d,]+\.\d{2}', 'date_desc_amt_bal'),

            # Pattern 4: MM/DD Description Amount (2-digit year or no year)
            (r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})\s*$', 'short_date_desc_amt'),

            # Pattern 5: MM/DD Amount Description (amount before desc)
            (r'^(\d{1,2}/\d{1,2})\s+([\d,]+\.\d{2})\s+(.+)', 'short_date_amt_desc'),

            # Pattern 6: MM-DD-YYYY Description Amount (dash separator)
            (r'^(\d{1,2}-\d{1,2}-\d{4})\s+(.+?)\s+\$?([\d,]+\.\d{2})', 'dash_date'),

            # Pattern 7: YYYY-MM-DD Description Amount (ISO format)
            (r'^(\d{4}-\d{1,2}-\d{1,2})\s+(.+?)\s+\$?([\d,]+\.\d{2})', 'iso_date'),

            # Pattern 8: Check #XXXX Amount (check payments)
            (r'^(?:CHECK|CHK|CK)\s*#?\s*(\d+)\s+(.+?)?\s*\$?([\d,]+\.\d{2})', 'check'),

            # Pattern 9: Description MM/DD Amount (desc before date)
            (r'^(.{10,50}?)\s+(\d{1,2}/\d{1,2})\s+([\d,]+\.\d{2})', 'desc_date_amt'),

            # Pattern 10: NUMBERED CHECKS section - CheckNum MM/DD Amount (Farmers Bank)
            # Matches: 1493 08/14 2,301.24
            (r'^(\d{4})\s+(\d{1,2}/\d{1,2})\s+([\d,]+\.\d{2})\s*$', 'numbered_check'),
        ]

        seen = {}  # Track counts for smart deduplication

        # Track section context (some banks have Deposits/Withdrawals sections)
        current_section = None
        for line in lines:
            line_lower = line.lower().strip()
            if 'deposit' in line_lower and ('addition' in line_lower or 'credit' in line_lower):
                current_section = 'deposits'
            elif 'withdrawal' in line_lower or 'deduction' in line_lower or 'debit' in line_lower:
                current_section = 'withdrawals'
            elif 'check' in line_lower and ('paid' in line_lower or 'cleared' in line_lower):
                current_section = 'withdrawals'

        for line_num, line in enumerate(lines):
            line = line.strip()
            if len(line) < 10:
                continue

            # Skip header/summary lines
            line_lower = line.lower()
            if any(skip in line_lower for skip in skip_patterns):
                # Update section tracking
                if 'deposit' in line_lower:
                    current_section = 'deposits'
                elif 'withdrawal' in line_lower or 'deduction' in line_lower:
                    current_section = 'withdrawals'
                continue

            for pattern, pattern_type in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()

                    try:
                        if pattern_type == 'check':
                            # Check pattern: check_num, desc (optional), amount
                            check_num = groups[0]
                            description = f"CHECK #{check_num}" + (f" {groups[1]}" if groups[1] else "")
                            amount_str = groups[2]
                            date_str = None  # Need to find date elsewhere
                        elif pattern_type == 'numbered_check':
                            # NUMBERED CHECKS section: check_num, date, amount
                            # Example: 1493 08/14 2,301.24
                            check_num = groups[0]
                            date_str = groups[1]
                            amount_str = groups[2]
                            description = f"CHECK #{check_num}"
                        elif pattern_type in ['short_date_amt_desc']:
                            date_str = groups[0]
                            amount_str = groups[1]
                            description = groups[2]
                        elif pattern_type == 'desc_date_amt':
                            description = groups[0]
                            date_str = groups[1]
                            amount_str = groups[2]
                        else:
                            date_str = groups[0]
                            description = groups[1] if len(groups) > 1 else ''
                            amount_str = groups[2] if len(groups) > 2 else groups[1]

                        # Parse amount
                        amount = float(amount_str.replace(',', '').replace('$', ''))

                        # Skip unreasonably large amounts (likely account numbers)
                        if amount > 10000000:
                            continue

                        # Skip very small amounts that might be noise
                        if amount < 0.01:
                            continue

                        # Format date
                        if date_str:
                            # Handle various date formats
                            date_str = date_str.replace('-', '/')
                            if '/' in date_str and len(date_str.split('/')) == 2:
                                date_str = f"{date_str}/{year}"
                            date = self._format_date(date_str)
                            if not date:
                                continue
                        else:
                            # For checks without dates, use current year
                            date = datetime.now().strftime('%Y-%m-%d')

                        # Clean description
                        description = self._clean_description_universal(description)
                        if not description:
                            description = "TRANSACTION"

                        # Filter garbage transactions - descriptions that are clearly not real
                        # Example: "415.00 08/29" is garbage (amount followed by date)
                        # Example: "1497 07/25 684.00 1498" is garbage (check numbers and amounts mixed)
                        if re.match(r'^[\d,]+\.\d{2}\s+\d{1,2}/\d{1,2}', description):
                            continue
                        # Filter: starts with check number, date, amount pattern
                        if re.match(r'^\d{4}\s+\d{1,2}/\d{1,2}\s+[\d,]+\.\d{2}', description):
                            continue
                        # Filter: date followed by amount (not a real description)
                        if re.match(r'^\d{1,2}/\d{1,2}\s+[\d,]+\.\d{2}', description):
                            continue

                        # Determine transaction type
                        desc_upper = description.upper()

                        # Priority order for determining deposit vs withdrawal:
                        # 1. Explicit pattern (parentheses = withdrawal)
                        # 2. Keywords in description (most reliable)
                        # 3. Section context (fallback)
                        # 4. Default to withdrawal

                        # Explicit withdrawal pattern (parens)
                        if pattern_type == 'date_desc_withdrawal':
                            is_deposit = False
                            amount = -abs(amount)
                        # Check DEPOSIT keywords FIRST (higher priority than withdrawal)
                        # This ensures "DEPOSIT" is recognized even if it contains "POS"
                        elif match_keyword(description, deposit_keywords):
                            is_deposit = True
                            amount = abs(amount)
                        # Then check withdrawal keywords
                        elif match_keyword(description, withdrawal_keywords):
                            is_deposit = False
                            amount = -abs(amount)
                        elif 'CHECK' in pattern_type.upper() or pattern_type == 'numbered_check':
                            is_deposit = False
                            amount = -abs(amount)
                        # Then check section context as fallback
                        elif current_section == 'deposits':
                            is_deposit = True
                            amount = abs(amount)
                        elif current_section == 'withdrawals':
                            is_deposit = False
                            amount = -abs(amount)
                        else:
                            # Default to withdrawal (safer assumption)
                            is_deposit = False
                            amount = -abs(amount)

                        # Smart dedup - allow up to 2 identical transactions
                        # Some banks have legitimate duplicates (e.g., 2 identical deposits same day)
                        # Use 2 as a reasonable limit that catches most statement duplicates
                        MAX_DUPLICATES = 2
                        key = (date, description[:30], round(abs(amount), 2))
                        current_count = seen.get(key, 0)
                        if current_count >= MAX_DUPLICATES:
                            continue
                        seen[key] = current_count + 1

                        transactions.append({
                            'date': date,
                            'description': description.strip(),
                            'amount': amount,
                            'is_deposit': is_deposit,
                            'module': 'CR' if is_deposit else 'CD',
                            'confidence_score': 70,
                            'confidence_level': 'medium',
                            'parsed_by': 'universal_regex'
                        })
                        break  # Found a match, move to next line

                    except (ValueError, IndexError) as e:
                        continue

        print(f"[INFO] Universal regex found {len(transactions)} transactions")
        return transactions

    def _clean_description_universal(self, desc: str) -> str:
        """Clean transaction description - remove OCR artifacts and noise."""
        if not desc:
            return ''

        # Remove common OCR garbage
        desc = re.sub(r'[|=_~`]+', ' ', desc)
        desc = re.sub(r'\b(ccm|cain|END|xxx+)\b', '', desc, flags=re.IGNORECASE)

        # Remove long number sequences (likely reference IDs)
        desc = re.sub(r'\b\d{10,}\b', '', desc)

        # Remove extra whitespace
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Truncate
        if len(desc) > 80:
            desc = desc[:80]

        return desc
