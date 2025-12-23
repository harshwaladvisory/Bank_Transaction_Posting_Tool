"""
LLM-Based PDF Parser - Uses Local LLM (LM Studio or Ollama) to extract transactions

================================================================================
STATUS: OPTIONAL - NOT CURRENTLY USED
================================================================================
The regex/template-based SmartParser achieves 100% accuracy for all supported
banks (Farmers, PNC, Truist, Sovereign, CrossFirst). LLM is kept as optional
fallback for future unsupported bank formats.

To enable: Set use_llm=True in UniversalParser (app.py line 797)

================================================================================
HYBRID PARSER ARCHITECTURE
================================================================================
1. Primary: Fast regex parser (SmartParser) - RECOMMENDED
2. Fallback: LLM parser when regex fails validation - OPTIONAL

LLM Options:
- LM Studio: http://localhost:1234/v1 (OpenAI-compatible)
- Ollama: http://localhost:11434 (llama3.1:8b recommended)

This approach handles:
1. Messy OCR text with garbled characters
2. Multiple bank statement formats automatically
3. Intelligent amount extraction (ignores reference numbers)
4. Proper date parsing and validation
5. Validation against bank's stated totals
"""

import os
import re
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional


# LLM Server settings
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"  # Using 3B model (8B requires more RAM)


class LLMParser:
    """Parse bank statements using Local LLM (LM Studio or Ollama) for intelligent extraction"""

    def __init__(self, base_url: str = None, prefer_ollama: bool = True):
        """
        Initialize LLM Parser

        Args:
            base_url: LM Studio server URL (default: http://localhost:1234/v1)
            prefer_ollama: Try Ollama first before LM Studio (default: True)
        """
        self.base_url = base_url or "http://localhost:1234/v1"
        self.chat_url = f"{self.base_url}/chat/completions"
        self.prefer_ollama = prefer_ollama
        self.bank_name = None
        self.statement_year = datetime.now().year
        self.transactions = []
        self._server_available = None
        self._use_ollama = False

    def is_available(self) -> bool:
        """Check if any LLM server is running - tries Ollama first, then LM Studio"""
        # Try Ollama first if preferred
        if self.prefer_ollama:
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    self._server_available = True
                    self._use_ollama = True
                    print("[INFO] Ollama server is running", flush=True)
                    return True
            except:
                pass

        # Try LM Studio
        try:
            response = requests.get(f"{self.base_url}/models", timeout=5)
            self._server_available = response.status_code == 200
            self._use_ollama = False
            if self._server_available:
                print("[INFO] LM Studio server is running", flush=True)
            return self._server_available
        except Exception as e:
            self._server_available = False
            print(f"[INFO] No LLM server available: {e}", flush=True)
            return False

    def parse(self, file_path: str) -> List[Dict]:
        """Parse PDF using local LLM"""
        import sys
        print(f"[DEBUG] LLM Parser starting for: {file_path}", flush=True)

        if not self.is_available():
            print("[ERROR] LM Studio not available. Please start the local server.", flush=True)
            return []

        # Extract text from PDF
        print("[DEBUG] Extracting text from PDF...", flush=True)
        text = self._extract_text(file_path)
        if not text:
            print("[ERROR] Could not extract text from PDF", flush=True)
            return []

        print(f"[INFO] Extracted {len(text)} characters from PDF", flush=True)
        print(f"[DEBUG] First 500 chars of text: {text[:500]}", flush=True)
        sys.stdout.flush()

        # Use LLM to extract transactions
        transactions = self._extract_with_llm(text)
        print(f"[DEBUG] LLM returned {len(transactions) if transactions else 0} raw transactions", flush=True)

        # Validate and clean
        transactions = self._validate_transactions(transactions)

        self.transactions = transactions
        print(f"[INFO] LLM extracted {len(transactions)} valid transactions", flush=True)
        sys.stdout.flush()

        return transactions

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber or OCR"""
        text = ""

        # Try pdfplumber first
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"[WARNING] pdfplumber failed: {e}")

        # If no text, try OCR
        if not text or len(text.strip()) < 100:
            text = self._extract_with_ocr(file_path)

        return text

    def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR"""
        try:
            from pdf2image import convert_from_path
            import pytesseract

            # Get paths from config
            try:
                from config import TESSERACT_CMD, POPPLER_PATH
                if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
                    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
                poppler = POPPLER_PATH if POPPLER_PATH and os.path.exists(POPPLER_PATH) else None
            except:
                poppler = None

            print("[INFO] Converting PDF to images for OCR...")
            if poppler:
                images = convert_from_path(file_path, dpi=300, poppler_path=poppler)
            else:
                images = convert_from_path(file_path, dpi=300)

            text = ""
            for i, image in enumerate(images):
                print(f"[INFO] OCR processing page {i+1}/{len(images)}...")
                page_text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
                text += page_text + "\n"

            return text

        except Exception as e:
            print(f"[ERROR] OCR failed: {e}")
            return ""

    def _extract_with_llm(self, text: str) -> List[Dict]:
        """Use local LLM to extract transactions from text"""

        # Truncate if too long (local LLMs have smaller context and are slow)
        max_chars = 6000  # Increased for better context
        if len(text) > max_chars:
            text = text[:max_chars]
            print(f"[WARNING] Text truncated to {max_chars} characters for faster processing", flush=True)

        prompt = f"""You are a bank statement parser. Extract ALL transactions from this bank statement text.

IMPORTANT RULES:
1. Extract the ACTUAL transaction amount, NOT reference numbers or customer IDs
2. Reference numbers are long digit strings (8+ digits) WITHOUT decimal points - IGNORE these
3. Transaction amounts ALWAYS have a decimal point with 2 digits (e.g., 251.91, 13,300.00)
4. Checks are WITHDRAWALS (negative amounts)
5. ACH DEBIT, PAYROLL, TAX PAYMENT are WITHDRAWALS (negative amounts)
6. DEPOSIT, ACH CREDIT, GRANT are DEPOSITS (positive amounts)

For each transaction, extract:
- date: in MM/DD/YYYY format
- description: clean description without reference numbers
- amount: positive for deposits, negative for withdrawals
- type: "deposit" or "withdrawal"
- check_number: if it's a check, include the check number

BANK STATEMENT TEXT:
{text}

Return ONLY a valid JSON array of transactions. Example format:
[
  {{"date": "10/06/2024", "description": "CHECK #20101", "amount": -13300.00, "type": "withdrawal", "check_number": "20101"}},
  {{"date": "09/26/2024", "description": "ACH CORP DEBIT PAYROLL INTUIT", "amount": -251.91, "type": "withdrawal"}},
  {{"date": "10/01/2024", "description": "ACH CREDIT HUD NAHASDA DRAWDOWN", "amount": 50000.00, "type": "deposit"}}
]

Extract ALL transactions. Return ONLY the JSON array, no explanations."""

        try:
            # Use Ollama if available, otherwise LM Studio
            if self._use_ollama:
                return self._call_ollama(prompt)
            else:
                return self._call_lm_studio(prompt)

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM response as JSON: {e}", flush=True)
            return []
        except requests.exceptions.Timeout:
            print("[ERROR] LLM request timed out.", flush=True)
            return []
        except Exception as e:
            print(f"[ERROR] LLM extraction failed: {e}", flush=True)
            return []

    def _call_ollama(self, prompt: str) -> List[Dict]:
        """Call Ollama API to extract transactions"""
        print(f"[INFO] Calling Ollama ({OLLAMA_MODEL}) to extract transactions...", flush=True)

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4000
                }
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"[ERROR] Ollama request failed: {response.status_code}", flush=True)
            return []

        result = response.json()
        content = result.get("response", "").strip()

        return self._parse_llm_response(content)

    def _call_lm_studio(self, prompt: str) -> List[Dict]:
        """Call LM Studio API to extract transactions"""
        print(f"[INFO] Calling LM Studio to extract transactions...", flush=True)
        print(f"[DEBUG] Sending request to: {self.chat_url}", flush=True)

        response = requests.post(
            self.chat_url,
            json={
                "model": "meta-llama-3.1-8b-instruct",
                "messages": [
                    {"role": "system", "content": "You are a precise bank statement parser. Extract transactions accurately and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
                "stream": False
            },
            timeout=300
        )

        print(f"[DEBUG] Response status: {response.status_code}", flush=True)

        if response.status_code != 200:
            print(f"[ERROR] LM Studio request failed: {response.status_code}", flush=True)
            return []

        result = response.json()
        content = result['choices'][0]['message']['content'].strip()

        return self._parse_llm_response(content)

    def _parse_llm_response(self, content: str) -> List[Dict]:
        """Parse JSON from LLM response"""
        print(f"[DEBUG] LLM response (first 500 chars): {content[:500]}", flush=True)

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r'^```json?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)

        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            content = json_match.group(0)

        transactions = json.loads(content)
        print(f"[INFO] LLM extracted {len(transactions)} transactions", flush=True)

        return transactions

    def _old_extract_with_llm(self, text: str) -> List[Dict]:
        """DEPRECATED: Old implementation kept for reference"""
        try:
            print("[INFO] Calling local LLM to extract transactions...", flush=True)
            print(f"[DEBUG] Sending request to: {self.chat_url}", flush=True)

            response = requests.post(
                self.chat_url,
                json={
                    "model": "meta-llama-3.1-8b-instruct",  # Specify model
                    "messages": [
                        {"role": "system", "content": "You are a precise bank statement parser. Extract transactions accurately and return only valid JSON."},
                        {"role": "user", "content": "Extract transactions"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "stream": False
                },
                timeout=300  # 5 minutes - local LLMs can be very slow
            )

            print(f"[DEBUG] Response status: {response.status_code}", flush=True)

            if response.status_code != 200:
                print(f"[ERROR] LLM request failed: {response.status_code}", flush=True)
                print(f"[DEBUG] Response: {response.text[:500]}", flush=True)
                return []

            result = response.json()
            print(f"[DEBUG] Got LLM response", flush=True)
            content = result['choices'][0]['message']['content'].strip()
            print(f"[DEBUG] LLM response content (first 1000 chars): {content[:1000]}", flush=True)

            # Try to parse JSON
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```json?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)

            # Try to find JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                content = json_match.group(0)

            transactions = json.loads(content)
            print(f"[INFO] LLM extracted {len(transactions)} transactions", flush=True)

            return transactions

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM response as JSON: {e}", flush=True)
            return []
        except requests.exceptions.Timeout:
            print("[ERROR] LLM request timed out. The model might be too slow.", flush=True)
            return []
        except Exception as e:
            print(f"[ERROR] LLM extraction failed: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return []

    def _validate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Validate and clean extracted transactions"""
        valid = []
        seen = set()

        for txn in transactions:
            # Must have date
            date = txn.get('date')
            if not date:
                continue

            # Standardize date format
            date = self._format_date(date)
            if not date:
                continue

            # Must have amount
            amount = txn.get('amount')
            if amount is None:
                continue

            try:
                amount = float(amount)
            except:
                continue

            # Skip zero amounts
            if abs(amount) < 0.01:
                continue

            # Skip impossibly large amounts (over $1M)
            if abs(amount) > 1000000:
                print(f"[REJECTED] Amount too large: ${abs(amount):,.2f}")
                continue

            # Get description
            description = txn.get('description', 'Unknown Transaction')
            description = self._clean_description(description)

            # Determine module
            is_deposit = amount > 0 or txn.get('type') == 'deposit'
            module = 'CR' if is_deposit else 'CD'

            # Check number
            check_number = txn.get('check_number')
            if check_number:
                check_number = str(check_number)

            # Deduplication
            key = (date, description[:20], round(amount, 2), check_number)
            if key in seen:
                continue
            seen.add(key)

            valid.append({
                'date': date,
                'description': description,
                'amount': amount,
                'is_deposit': is_deposit,
                'module': module,
                'check_number': check_number
            })

        return valid

    def _format_date(self, date_str: str) -> Optional[str]:
        """Format date to MM/DD/YYYY"""
        if not date_str:
            return None

        date_str = str(date_str).strip()

        # Try various formats
        formats = [
            '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d',
            '%m-%d-%Y', '%m-%d-%y', '%d/%m/%Y'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%m/%d/%Y')
            except:
                continue

        # Try to extract from string
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
        if match:
            month, day, year = match.groups()
            if len(year) == 2:
                year = '20' + year
            try:
                return f"{int(month):02d}/{int(day):02d}/{year}"
            except:
                pass

        return None

    def _clean_description(self, desc: str) -> str:
        """Clean description"""
        if not desc:
            return ''

        desc = str(desc)

        # Remove long numbers (reference IDs)
        desc = re.sub(r'\b\d{8,}\b', '', desc)

        # Remove CUSTOMER ID patterns
        desc = re.sub(r'CUSTOMER\s*ID\s*\d+', '', desc, flags=re.IGNORECASE)

        # Clean up spaces
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Truncate
        if len(desc) > 60:
            desc = desc[:60]

        return desc

    def get_summary(self) -> Dict:
        """Get parsing summary"""
        if not self.transactions:
            return {'count': 0, 'total_deposits': 0, 'total_withdrawals': 0}

        deposits = sum(t['amount'] for t in self.transactions if t['amount'] > 0)
        withdrawals = sum(t['amount'] for t in self.transactions if t['amount'] < 0)

        return {
            'count': len(self.transactions),
            'total_deposits': deposits,
            'total_withdrawals': withdrawals,
            'net_change': deposits + withdrawals,
            'bank_name': self.bank_name
        }


# =============================================================================
# HYBRID PARSER - Uses regex first, falls back to LLM
# =============================================================================

class HybridParser:
    """
    Hybrid parser that uses fast regex parsing first,
    then falls back to LLM when validation fails.

    This gives you:
    - Speed: Regex is instant, LLM is slow
    - Accuracy: LLM handles edge cases regex misses
    - Cost: Only uses LLM when needed (saves API costs/compute)
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.llm_parser = LLMParser(prefer_ollama=True)
        self._llm_available = None

    def is_llm_available(self) -> bool:
        """Check if LLM fallback is available"""
        if self._llm_available is None:
            self._llm_available = self.llm_parser.is_available()
        return self._llm_available

    def should_use_llm(self, parsed_total: float, expected_total: float,
                       tolerance_pct: float = 0.02) -> bool:
        """
        Determine if we should fall back to LLM parsing.

        Args:
            parsed_total: What regex parser found
            expected_total: What bank statement says
            tolerance_pct: Acceptable discrepancy (default 2%)

        Returns:
            True if LLM fallback is needed
        """
        if expected_total == 0:
            return False

        discrepancy = abs(parsed_total - expected_total)
        tolerance = max(expected_total * tolerance_pct, 10)  # At least $10 tolerance

        if discrepancy > tolerance:
            if self.debug:
                print(f"[HYBRID] Discrepancy ${discrepancy:,.2f} exceeds tolerance ${tolerance:,.2f}")
            return True

        return False

    def validate_and_fallback(self, regex_transactions: List[Dict],
                              expected_deposits: float,
                              expected_withdrawals: float,
                              raw_text: str = None,
                              file_path: str = None) -> Dict:
        """
        Validate regex results and fall back to LLM if needed.

        Args:
            regex_transactions: Transactions from regex parser
            expected_deposits: Bank's stated deposit total
            expected_withdrawals: Bank's stated withdrawal total
            raw_text: Raw text for LLM parsing (optional)
            file_path: PDF path for LLM parsing (optional)

        Returns:
            Dict with 'transactions', 'source', 'validation' info
        """
        # Calculate regex totals
        regex_deposits = sum(t.get('amount', 0) for t in regex_transactions
                            if t.get('amount', 0) > 0 or t.get('is_deposit', False))
        regex_withdrawals = abs(sum(t.get('amount', 0) for t in regex_transactions
                                   if t.get('amount', 0) < 0 or not t.get('is_deposit', True)))

        if self.debug:
            print(f"[HYBRID] Regex results:")
            print(f"  Deposits: ${regex_deposits:,.2f} (expected: ${expected_deposits:,.2f})")
            print(f"  Withdrawals: ${regex_withdrawals:,.2f} (expected: ${expected_withdrawals:,.2f})")

        # Check if regex is good enough
        deposits_ok = not self.should_use_llm(regex_deposits, expected_deposits)
        withdrawals_ok = not self.should_use_llm(regex_withdrawals, expected_withdrawals)

        if deposits_ok and withdrawals_ok:
            if self.debug:
                print("[HYBRID] Regex validation PASSED - using regex results")
            return {
                'transactions': regex_transactions,
                'source': 'regex',
                'validated': True,
                'deposit_discrepancy': abs(regex_deposits - expected_deposits),
                'withdrawal_discrepancy': abs(regex_withdrawals - expected_withdrawals)
            }

        # Try LLM fallback
        if not self.is_llm_available():
            if self.debug:
                print("[HYBRID] LLM not available - using regex results with warning")
            return {
                'transactions': regex_transactions,
                'source': 'regex',
                'validated': False,
                'warning': 'Validation failed but LLM not available',
                'deposit_discrepancy': abs(regex_deposits - expected_deposits),
                'withdrawal_discrepancy': abs(regex_withdrawals - expected_withdrawals)
            }

        if self.debug:
            print("[HYBRID] Validation failed - trying LLM fallback...")

        # Try LLM parsing
        llm_transactions = []
        if file_path:
            llm_transactions = self.llm_parser.parse(file_path)
        elif raw_text:
            llm_transactions = self.llm_parser._extract_with_llm(raw_text)
            llm_transactions = self.llm_parser._validate_transactions(llm_transactions)

        if not llm_transactions:
            if self.debug:
                print("[HYBRID] LLM returned no results - using regex results")
            return {
                'transactions': regex_transactions,
                'source': 'regex',
                'validated': False,
                'warning': 'LLM fallback returned no results'
            }

        # Calculate LLM totals
        llm_deposits = sum(t.get('amount', 0) for t in llm_transactions
                          if t.get('amount', 0) > 0)
        llm_withdrawals = abs(sum(t.get('amount', 0) for t in llm_transactions
                                 if t.get('amount', 0) < 0))

        if self.debug:
            print(f"[HYBRID] LLM results:")
            print(f"  Deposits: ${llm_deposits:,.2f}")
            print(f"  Withdrawals: ${llm_withdrawals:,.2f}")

        # Compare which is closer
        regex_deposit_diff = abs(regex_deposits - expected_deposits)
        regex_withdrawal_diff = abs(regex_withdrawals - expected_withdrawals)
        llm_deposit_diff = abs(llm_deposits - expected_deposits)
        llm_withdrawal_diff = abs(llm_withdrawals - expected_withdrawals)

        regex_score = regex_deposit_diff + regex_withdrawal_diff
        llm_score = llm_deposit_diff + llm_withdrawal_diff

        if llm_score < regex_score:
            if self.debug:
                print(f"[HYBRID] Using LLM results (score: {llm_score:.2f} vs regex: {regex_score:.2f})")
            return {
                'transactions': llm_transactions,
                'source': 'llm',
                'validated': llm_deposit_diff < 10 and llm_withdrawal_diff < 10,
                'deposit_discrepancy': llm_deposit_diff,
                'withdrawal_discrepancy': llm_withdrawal_diff
            }
        else:
            if self.debug:
                print(f"[HYBRID] Keeping regex results (score: {regex_score:.2f} vs llm: {llm_score:.2f})")
            return {
                'transactions': regex_transactions,
                'source': 'regex',
                'validated': False,
                'deposit_discrepancy': regex_deposit_diff,
                'withdrawal_discrepancy': regex_withdrawal_diff
            }


# Test
if __name__ == "__main__":
    import sys

    print("="*60)
    print("HYBRID PARSER - Regex + LLM Fallback")
    print("="*60)

    parser = LLMParser()

    print("\nChecking LLM availability...")
    if parser.is_available():
        if parser._use_ollama:
            print("  Ollama is available (preferred)")
        else:
            print("  LM Studio is available")
    else:
        print("  No LLM server available")
        print("\nTo enable LLM fallback, install one of:")
        print("\n  Option 1: Ollama (recommended)")
        print("    1. Download from https://ollama.ai")
        print("    2. Run: ollama pull llama3.1:8b")
        print("    3. Ollama runs automatically on port 11434")
        print("\n  Option 2: LM Studio")
        print("    1. Download from https://lmstudio.ai")
        print("    2. Load a model (Llama 3, Mistral recommended)")
        print("    3. Go to 'Local Server' tab")
        print("    4. Click 'Start Server' (port 1234)")

    if len(sys.argv) > 1:
        print(f"\nParsing: {sys.argv[1]}")
        txns = parser.parse(sys.argv[1])

        print(f"\n{'='*70}")
        print("LLM Parser Results")
        print(f"{'='*70}")

        for t in txns[:20]:
            sign = '+' if t['amount'] > 0 else ''
            print(f"{t['date']} | {t['description'][:35]:35} | {sign}${t['amount']:>10,.2f}")

        print(f"\n{'='*70}")
        s = parser.get_summary()
        print(f"Total: {s['count']} transactions")
        print(f"Deposits: ${s['total_deposits']:,.2f}")
        print(f"Withdrawals: ${abs(s['total_withdrawals']):,.2f}")
    else:
        print("\nUsage: python llm_parser.py <path_to_pdf>")
        print("\nMake sure LM Studio server is running first!")
