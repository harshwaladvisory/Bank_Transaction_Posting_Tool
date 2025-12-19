# -*- coding: utf-8 -*-
"""
GL Code Suggester

Combines ChromaDB learning with keyword fallback for intelligent GL code suggestions.

Layered approach:
1. ChromaDB (learned patterns) - most accurate, improves over time
2. Keyword matching (fallback rules) - reliable defaults
3. Default assignment - when no match found

All processing is LOCAL - no external API calls for banking data security.
"""

import os
import re
import json
from typing import Dict, List, Optional, Any

from .chroma_store import get_chroma_store, ChromaLearningStore


class GLSuggester:
    """
    Intelligent GL Code Suggester with learning capability.

    Combines vector similarity search (ChromaDB) with keyword matching
    for reliable GL code suggestions that improve over time.

    Usage:
        suggester = GLSuggester()

        # Get suggestion for a transaction
        result = suggester.suggest(
            description="HUD TREAS NAHASDA",
            transaction_type="deposit",
            bank="PNC"
        )
        # Returns: {
        #     'gl_code': '3001',
        #     'gl_name': 'Revenue - Federal',
        #     'confidence': 92.5,
        #     'confidence_level': 'high',
        #     'source': 'learned',
        #     'reason': 'Similar to: HUD TREASURY PAYMENT...'
        # }

        # Learn from user action
        suggester.learn_from_user(
            description="NEW VENDOR PAYMENT",
            gl_code="7300",
            transaction_type="withdrawal",
            module="CD",
            bank="PNC"
        )
    """

    # Confidence thresholds
    AUTO_ASSIGN_THRESHOLD = 85  # Auto-assign if >= 85% confident
    SUGGEST_THRESHOLD = 60      # Show suggestion if >= 60%

    def __init__(self, keywords_path: str = None):
        """
        Initialize GL Suggester.

        Args:
            keywords_path: Path to gl_keywords.json. Auto-detected if None.
        """
        # Initialize ChromaDB store
        self.chroma = get_chroma_store()

        # Load keyword fallback rules
        if keywords_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            keywords_path = os.path.join(base_dir, 'config', 'gl_keywords.json')

        self.keywords = self._load_keywords(keywords_path)
        self.keywords_path = keywords_path

    def _load_keywords(self, path: str) -> Dict:
        """Load keyword fallback rules from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                keywords = json.load(f)
                print(f"[INFO] Loaded GL keywords from {path}")
                return keywords
        except FileNotFoundError:
            print(f"[INFO] Keywords file not found, using defaults: {path}")
            return self._default_keywords()
        except Exception as e:
            print(f"[WARNING] Failed to load keywords: {e}")
            return self._default_keywords()

    def _default_keywords(self) -> Dict:
        """Default keyword rules as fallback."""
        return {
            "deposits": {
                # Federal/Government
                "HUD TREAS": {"gl": "3001", "name": "Revenue - Federal"},
                "HUD": {"gl": "3001", "name": "Revenue - Federal"},
                "NAHASDA": {"gl": "3001", "name": "Revenue - Federal"},
                "TREASURY": {"gl": "3001", "name": "Revenue - Federal"},

                # Insurance/Healthcare
                "BLUE CROSS": {"gl": "4080", "name": "Revenue - Contributions"},
                "BCBS": {"gl": "4080", "name": "Revenue - Contributions"},
                "HEALTH INSURANCE": {"gl": "4080", "name": "Revenue - Contributions"},

                # State/County
                "NC DEPT": {"gl": "3002", "name": "Revenue - State"},
                "NC DEPARTMENT": {"gl": "3002", "name": "Revenue - State"},
                "STATE OF": {"gl": "3002", "name": "Revenue - State"},
                "COUNTY": {"gl": "3003", "name": "Revenue - County"},

                # Merchant/Business
                "MERCHANT DEPOSIT": {"gl": "4380", "name": "Revenue - Tomahawk"},
                "WIXCOM": {"gl": "4380", "name": "Revenue - Tomahawk"},
                "SQUARE": {"gl": "4380", "name": "Revenue - Tomahawk"},
                "CLOVER": {"gl": "4380", "name": "Revenue - Tomahawk"},

                # Interest
                "INTEREST": {"gl": "4100", "name": "Interest Income"},
                "CAPITALIZATION": {"gl": "4100", "name": "Interest Income"},

                # Generic deposits
                "DEPOSIT": {"gl": "4100", "name": "Revenue - Fundraising"},
                "GRANT": {"gl": "3001", "name": "Revenue - Federal"},
                "TRANSFER IN": {"gl": "4200", "name": "Transfer In"}
            },
            "withdrawals": {
                # Payroll
                "PAYROLL": {"gl": "6601", "name": "Salaries"},
                "INTUIT": {"gl": "6601", "name": "Salaries"},
                "ADP": {"gl": "6601", "name": "Salaries"},
                "PAYCHEX": {"gl": "6601", "name": "Salaries"},

                # Taxes
                "IRS": {"gl": "7400", "name": "Taxes"},
                "TAX PYMT": {"gl": "7400", "name": "Taxes"},
                "EFTPS": {"gl": "7400", "name": "Taxes"},
                "TAX PAYMENT": {"gl": "7400", "name": "Taxes"},

                # Software/Technology
                "QBOOKS": {"gl": "5152", "name": "Software"},
                "QUICKBOOKS": {"gl": "5152", "name": "Software"},
                "MICROSOFT": {"gl": "5152", "name": "Software"},
                "ADOBE": {"gl": "5152", "name": "Software"},

                # Bank Fees
                "SERVICE CHARGE": {"gl": "5060", "name": "Bank Charges"},
                "SERVICE FEE": {"gl": "5060", "name": "Bank Charges"},
                "BANK FEE": {"gl": "5060", "name": "Bank Charges"},
                "FDMS": {"gl": "5060", "name": "Bank Charges"},
                "MERCHANT FEE": {"gl": "5060", "name": "Bank Charges"},
                "MERCHANT DISCOUNT": {"gl": "5060", "name": "Bank Charges"},

                # Contracted Services
                "BILL.COM": {"gl": "5110", "name": "Contracted Services"},
                "CONSULTING": {"gl": "5110", "name": "Contracted Services"},

                # Utilities
                "ELECTRIC": {"gl": "5200", "name": "Utilities"},
                "WATER": {"gl": "5200", "name": "Utilities"},
                "GAS": {"gl": "5200", "name": "Utilities"},
                "UTILITY": {"gl": "5200", "name": "Utilities"},

                # Insurance
                "INSURANCE": {"gl": "5300", "name": "Insurance"},

                # Generic/Default
                "CHECK": {"gl": "7300", "name": "Accounts Payable"},
                "TRANSFER OUT": {"gl": "7200", "name": "Transfer Out"},
                "WITHDRAWAL": {"gl": "7300", "name": "Accounts Payable"}
            }
        }

    def suggest(self, description: str, transaction_type: str,
                amount: float = None, bank: str = None) -> Dict[str, Any]:
        """
        Get GL code suggestion using layered approach.

        Layer 1: ChromaDB (learned patterns) - most accurate
        Layer 2: Keyword matching (fallback rules)
        Layer 3: Default assignment (when no match)

        Args:
            description: Transaction description
            transaction_type: 'deposit' or 'withdrawal'
            amount: Transaction amount (optional)
            bank: Bank name (optional)

        Returns:
            Dictionary with suggestion details:
            {
                'gl_code': str,
                'gl_name': str,
                'confidence': float (0-100),
                'confidence_level': 'high'|'medium'|'low'|'none',
                'source': 'learned'|'keyword'|'default',
                'reason': str,
                'suggestions': list (alternative suggestions)
            }
        """
        result = {
            'gl_code': None,
            'gl_name': None,
            'confidence': 0,
            'confidence_level': 'none',
            'source': None,
            'reason': None,
            'suggestions': []
        }

        # ═══════════════════════════════════════════════════════════
        # LAYER 1: ChromaDB learned patterns (most accurate)
        # ═══════════════════════════════════════════════════════════

        try:
            chroma_suggestions = self.chroma.suggest_gl_code(
                description=description,
                transaction_type=transaction_type,
                bank_name=bank,
                n_results=5
            )

            if chroma_suggestions:
                best = chroma_suggestions[0]
                result['suggestions'] = chroma_suggestions

                if best['confidence'] >= self.AUTO_ASSIGN_THRESHOLD:
                    # High confidence - auto assign
                    result['gl_code'] = best['gl_code']
                    result['gl_name'] = self._get_gl_name(best['gl_code'], transaction_type)
                    result['confidence'] = best['confidence']
                    result['confidence_level'] = 'high'
                    result['source'] = 'learned'
                    result['reason'] = f"Learned pattern: {best['matched_description'][:40]}..."
                    return result

                elif best['confidence'] >= self.SUGGEST_THRESHOLD:
                    # Medium confidence - suggest but check keywords too
                    result['gl_code'] = best['gl_code']
                    result['gl_name'] = self._get_gl_name(best['gl_code'], transaction_type)
                    result['confidence'] = best['confidence']
                    result['confidence_level'] = 'medium'
                    result['source'] = 'learned'
                    result['reason'] = f"Similar to: {best['matched_description'][:40]}..."
                    # Continue to check keywords for potentially better match

        except Exception as e:
            print(f"[WARNING] ChromaDB suggestion failed: {e}")

        # ═══════════════════════════════════════════════════════════
        # LAYER 2: Keyword matching (fallback rules)
        # ═══════════════════════════════════════════════════════════

        keyword_match = self._keyword_match(description, transaction_type)

        if keyword_match:
            # If no ChromaDB match, or keyword is more specific
            if result['gl_code'] is None or keyword_match['confidence'] > result['confidence']:
                result['gl_code'] = keyword_match['gl_code']
                result['gl_name'] = keyword_match['gl_name']
                result['confidence'] = keyword_match['confidence']
                result['confidence_level'] = keyword_match['confidence_level']
                result['source'] = 'keyword'
                result['reason'] = f"Matched keyword: {keyword_match['keyword']}"

        # ═══════════════════════════════════════════════════════════
        # LAYER 3: Default assignment (when no match found)
        # ═══════════════════════════════════════════════════════════

        if result['gl_code'] is None:
            result['confidence_level'] = 'none'
            result['source'] = 'default'
            result['reason'] = 'No pattern match - using default'

            # Assign default based on transaction type
            if transaction_type == 'deposit':
                result['gl_code'] = '4100'
                result['gl_name'] = 'Revenue - Fundraising'
            else:
                result['gl_code'] = '7300'
                result['gl_name'] = 'Accounts Payable'

            result['confidence'] = 20

        return result

    def _keyword_match(self, description: str, transaction_type: str) -> Optional[Dict]:
        """
        Match description against keyword rules.

        Args:
            description: Transaction description
            transaction_type: 'deposit' or 'withdrawal'

        Returns:
            Match dict or None
        """
        desc_upper = description.upper()

        # Select keyword set based on transaction type
        if transaction_type == 'deposit':
            keywords = self.keywords.get('deposits', {})
        else:
            keywords = self.keywords.get('withdrawals', {})

        # Check each keyword (longer matches first for specificity)
        sorted_keywords = sorted(keywords.keys(), key=len, reverse=True)

        for keyword in sorted_keywords:
            if keyword.upper() in desc_upper:
                rule = keywords[keyword]
                return {
                    'gl_code': rule.get('gl', ''),
                    'gl_name': rule.get('name', ''),
                    'keyword': keyword,
                    'confidence': 75,  # Keyword matches are 75% confident
                    'confidence_level': 'medium'
                }

        return None

    def _get_gl_name(self, gl_code: str, transaction_type: str) -> str:
        """Get GL account name from code."""
        # Check deposits keywords
        for keyword, rule in self.keywords.get('deposits', {}).items():
            if rule.get('gl') == gl_code:
                return rule.get('name', '')

        # Check withdrawals keywords
        for keyword, rule in self.keywords.get('withdrawals', {}).items():
            if rule.get('gl') == gl_code:
                return rule.get('name', '')

        return ''

    def learn_from_user(self, description: str, gl_code: str,
                       transaction_type: str, module: str,
                       bank: str, user_corrected: bool = False) -> str:
        """
        Learn from user's GL code assignment.
        Called when user approves or corrects a transaction.

        Args:
            description: Transaction description
            gl_code: Assigned GL code
            transaction_type: 'deposit' or 'withdrawal'
            module: 'CR', 'CD', or 'JV'
            bank: Bank name
            user_corrected: True if user changed the suggestion

        Returns:
            Document ID of learned pattern
        """
        doc_id = self.chroma.learn_transaction(
            description=description,
            gl_code=gl_code,
            transaction_type=transaction_type,
            module=module,
            bank_name=bank,
            user_corrected=user_corrected
        )

        return doc_id

    def learn_batch(self, transactions: List[Dict], bank: str) -> int:
        """
        Learn from multiple approved transactions.

        Args:
            transactions: List of transaction dicts with gl_code assigned
            bank: Bank name

        Returns:
            Number of patterns learned
        """
        patterns = []
        for txn in transactions:
            if txn.get('approved', False) or txn.get('gl_code'):
                patterns.append({
                    'description': txn.get('description', ''),
                    'gl_code': txn.get('gl_code', ''),
                    'type': 'deposit' if txn.get('amount', 0) > 0 else 'withdrawal',
                    'module': txn.get('module', 'CD'),
                    'bank': bank
                })

        return self.chroma.learn_batch(patterns)

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        return self.chroma.get_statistics()

    def export_patterns(self, filepath: str) -> int:
        """Export learned patterns to JSON file."""
        return self.chroma.export_patterns(filepath)

    def import_patterns(self, filepath: str) -> int:
        """Import patterns from JSON file."""
        return self.chroma.import_patterns(filepath)

    def save_keywords(self) -> bool:
        """Save current keywords to file."""
        try:
            os.makedirs(os.path.dirname(self.keywords_path), exist_ok=True)
            with open(self.keywords_path, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, indent=2)
            print(f"[INFO] Saved keywords to {self.keywords_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save keywords: {e}")
            return False

    def add_keyword_rule(self, keyword: str, gl_code: str,
                        gl_name: str, transaction_type: str) -> bool:
        """
        Add a new keyword rule.

        Args:
            keyword: Keyword to match (case-insensitive)
            gl_code: GL code to assign
            gl_name: GL account name
            transaction_type: 'deposit' or 'withdrawal'

        Returns:
            True if added successfully
        """
        section = 'deposits' if transaction_type == 'deposit' else 'withdrawals'

        if section not in self.keywords:
            self.keywords[section] = {}

        self.keywords[section][keyword.upper()] = {
            'gl': gl_code,
            'name': gl_name
        }

        return self.save_keywords()


# ═══════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════

_suggester_instance = None

def get_gl_suggester() -> GLSuggester:
    """
    Get singleton GL suggester instance.

    Returns:
        GLSuggester instance
    """
    global _suggester_instance
    if _suggester_instance is None:
        _suggester_instance = GLSuggester()
    return _suggester_instance


# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Testing GL Suggester")
    print("=" * 60)

    suggester = get_gl_suggester()

    # Check stats
    stats = suggester.get_learning_stats()
    print(f"\nLearning Statistics:")
    print(f"  Total patterns: {stats['total_patterns']}")

    # Test suggestions
    test_cases = [
        ("HUD TREAS NAHASDA GRANT", "deposit"),
        ("BLUE CROSS BCBS PREMIUM", "deposit"),
        ("INTUIT PAYROLL SERVICES", "withdrawal"),
        ("UNKNOWN VENDOR PAYMENT", "withdrawal"),
        ("SERVICE CHARGE FEE", "withdrawal"),
        ("INTEREST CAPITALIZATION", "deposit")
    ]

    print("\n" + "=" * 60)
    print("Testing Suggestions")
    print("=" * 60)

    for desc, txn_type in test_cases:
        result = suggester.suggest(desc, txn_type)
        print(f"\n'{desc}'")
        print(f"  -> GL {result['gl_code']} ({result['gl_name']})")
        print(f"     Confidence: {result['confidence']}% ({result['confidence_level']})")
        print(f"     Source: {result['source']}")
        print(f"     Reason: {result['reason']}")

    # Test learning
    print("\n" + "=" * 60)
    print("Testing Learning")
    print("=" * 60)

    suggester.learn_from_user(
        description="NEW VENDOR ABC COMPANY PAYMENT",
        gl_code="7350",
        transaction_type="withdrawal",
        module="CD",
        bank="TestBank"
    )

    # Now check if we can find it
    result = suggester.suggest("ABC COMPANY INVOICE PAYMENT", "withdrawal")
    print(f"\nAfter learning 'NEW VENDOR ABC COMPANY PAYMENT' -> GL 7350:")
    print(f"  Query: 'ABC COMPANY INVOICE PAYMENT'")
    print(f"  -> GL {result['gl_code']} ({result['confidence']}% confidence)")
    print(f"     Source: {result['source']}")
