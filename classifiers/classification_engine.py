"""
Classification Engine - Orchestrates all classifiers to determine transaction type
Main brain of the Bank Transaction Posting Tool

ACCOUNTING PRINCIPLES (CA Standards):
1. Double-Entry System: Every transaction affects at least two accounts
2. Cash Receipts (CR): Debit Bank (Asset+), Credit Revenue (Revenue+)
3. Cash Disbursements (CD): Debit Expense (Expense+), Credit Bank (Asset-)
4. Journal Vouchers (JV): For corrections, transfers, fees, accruals

GL CODE STRUCTURE:
- 1000-1999: Assets (1070 = Bank Account)
- 2000-2999: Liabilities
- 3000-3999: Equity/Fund Balance
- 4000-4999: Revenue/Income
- 5000-5999: Cost of Goods Sold
- 6000-6999: Operating Expenses
- 7000-7999: Other Expenses
- 8000-8999: Other Income/Expenses
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
                    DEFAULT_BANK_GL, DEFAULT_FUND_CODE)

from .keyword_classifier import KeywordClassifier
from .vendor_matcher import VendorMatcher
from .customer_matcher import CustomerMatcher
from .history_matcher import HistoryMatcher


# Comprehensive GL Code Mapping based on CA Standards
GL_CODE_MAPPING = {
    # Revenue Accounts (4000-4999)
    'grant_revenue': {'gl': '4100', 'name': 'Grant Revenue', 'module': 'CR'},
    'hud_grant': {'gl': '4110', 'name': 'HUD Grant Revenue', 'module': 'CR'},
    'doe_grant': {'gl': '4120', 'name': 'DOE Grant Revenue', 'module': 'CR'},
    'hhs_grant': {'gl': '4130', 'name': 'HHS Grant Revenue', 'module': 'CR'},
    'state_grant': {'gl': '4140', 'name': 'State Grant Revenue', 'module': 'CR'},
    'rental_income': {'gl': '4200', 'name': 'Rental Income', 'module': 'CR'},
    'service_revenue': {'gl': '4300', 'name': 'Service Revenue', 'module': 'CR'},
    'donation': {'gl': '4400', 'name': 'Donations & Contributions', 'module': 'CR'},
    'membership_dues': {'gl': '4500', 'name': 'Membership Dues', 'module': 'CR'},
    'interest_income': {'gl': '4600', 'name': 'Interest Income', 'module': 'JV'},
    'dividend_income': {'gl': '4650', 'name': 'Dividend Income', 'module': 'CR'},
    'other_income': {'gl': '4900', 'name': 'Other Income', 'module': 'CR'},
    'refund_income': {'gl': '4950', 'name': 'Refunds Received', 'module': 'CR'},

    # Expense Accounts (6000-7999)
    'payroll': {'gl': '6100', 'name': 'Salaries & Wages', 'module': 'CD'},
    'payroll_taxes': {'gl': '6200', 'name': 'Payroll Taxes', 'module': 'CD'},
    'benefits': {'gl': '6300', 'name': 'Employee Benefits', 'module': 'CD'},
    'rent_expense': {'gl': '6400', 'name': 'Rent Expense', 'module': 'CD'},
    'utilities': {'gl': '6500', 'name': 'Utilities', 'module': 'CD'},
    'insurance': {'gl': '6600', 'name': 'Insurance', 'module': 'CD'},
    'professional_fees': {'gl': '6700', 'name': 'Professional Fees', 'module': 'CD'},
    'office_supplies': {'gl': '6800', 'name': 'Office Supplies', 'module': 'CD'},
    'repairs_maintenance': {'gl': '6900', 'name': 'Repairs & Maintenance', 'module': 'CD'},
    'travel': {'gl': '7000', 'name': 'Travel & Transportation', 'module': 'CD'},
    'telecommunications': {'gl': '7100', 'name': 'Telecommunications', 'module': 'CD'},
    'taxes': {'gl': '7200', 'name': 'Taxes (IRS/State)', 'module': 'CD'},
    'vendor_payment': {'gl': '7300', 'name': 'Vendor Payments', 'module': 'CD'},
    'bank_fees': {'gl': '6100', 'name': 'Bank Fees & Charges', 'module': 'CD'},
    'interest_expense': {'gl': '7600', 'name': 'Interest Expense', 'module': 'JV'},
    'miscellaneous': {'gl': '7900', 'name': 'Miscellaneous Expense', 'module': 'CD'},
}

# Keyword to GL Code mapping
KEYWORD_GL_MAPPING = {
    # Grants
    'hud': 'hud_grant', 'nahasda': 'hud_grant', 'cdbg': 'hud_grant', 'home': 'hud_grant',
    'section 8': 'hud_grant', 'housing': 'hud_grant',
    'doe': 'doe_grant', 'weatherization': 'doe_grant', 'liheap': 'doe_grant', 'energy': 'doe_grant',
    'hhs': 'hhs_grant', 'head start': 'hhs_grant', 'tanf': 'hhs_grant', 'csbg': 'hhs_grant',
    'grant': 'grant_revenue', 'award': 'grant_revenue', 'drawdown': 'grant_revenue',

    # Revenue - Rental Income (received, not paid)
    'rent received': 'rental_income', 'rental income': 'rental_income', 'tenant': 'rental_income',
    'tenant payment': 'rental_income', 'tenant rent': 'rental_income',
    'donation': 'donation', 'contribution': 'donation', 'gift': 'donation',
    'dues': 'membership_dues', 'membership': 'membership_dues',
    'interest credit': 'interest_income', 'interest earned': 'interest_income',
    'dividend': 'dividend_income',
    'refund': 'refund_income', 'rebate': 'refund_income', 'reimbursement': 'refund_income',

    # Payroll & Benefits
    'payroll': 'payroll', 'salary': 'payroll', 'adp': 'payroll', 'paychex': 'payroll',
    'gusto': 'payroll', 'intuit payroll': 'payroll', 'wage': 'payroll',
    'fica': 'payroll_taxes', 'social security': 'payroll_taxes', 'medicare': 'payroll_taxes',
    'futa': 'payroll_taxes', 'suta': 'payroll_taxes',
    '401k': 'benefits', 'health insurance': 'benefits', 'dental': 'benefits',

    # Taxes
    'irs': 'taxes', 'eftps': 'taxes', 'federal tax': 'taxes', 'state tax': 'taxes',
    'estimated tax': 'taxes', 'quarterly tax': 'taxes',

    # Utilities & Operations
    'electric': 'utilities', 'water': 'utilities', 'gas': 'utilities', 'utility': 'utilities',
    'phone': 'telecommunications', 'internet': 'telecommunications', 'mobile': 'telecommunications',
    'rent expense': 'rent_expense', 'lease payment': 'rent_expense', 'office rent': 'rent_expense',
    'rent paid': 'rent_expense', 'rent payment': 'rent_expense',
    'insurance': 'insurance', 'premium': 'insurance', 'policy': 'insurance',

    # Professional Services
    'legal': 'professional_fees', 'attorney': 'professional_fees', 'accounting': 'professional_fees',
    'audit': 'professional_fees', 'consulting': 'professional_fees', 'professional': 'professional_fees',

    # Office & Supplies
    'office': 'office_supplies', 'supplies': 'office_supplies', 'staples': 'office_supplies',
    'amazon': 'office_supplies', 'walmart': 'office_supplies',

    # Bank & Fees
    'bank fee': 'bank_fees', 'service charge': 'bank_fees', 'monthly fee': 'bank_fees',
    'maintenance fee': 'bank_fees', 'nsf': 'bank_fees', 'overdraft': 'bank_fees',
    'wire fee': 'bank_fees', 'analysis charge': 'bank_fees',
    'service fee': 'bank_fees',  # Bank service fees
    'interest charge': 'interest_expense', 'finance charge': 'interest_expense',
}


class ClassificationEngine:
    """
    Main classification engine that combines:
    1. Keyword-based classification
    2. Vendor matching
    3. Customer/Grant matching
    4. Historical pattern matching

    Returns the best classification with confidence scores and proper GL codes
    """

    def __init__(self):
        self.keyword_classifier = KeywordClassifier()
        self.vendor_matcher = VendorMatcher()
        self.customer_matcher = CustomerMatcher()
        self.history_matcher = HistoryMatcher()

    def classify(self, description: str, amount: float = 0,
                 date: str = None, check_number: str = None,
                 is_deposit: bool = None, module_hint: str = None) -> Dict:
        """
        Classify a transaction and return comprehensive result

        Args:
            description: Transaction description/narration
            amount: Transaction amount (positive=credit/deposit, negative=debit/withdrawal)
            date: Transaction date
            check_number: Check number if applicable
            is_deposit: Hint from parser if this is a deposit
            module_hint: Hint from parser for module type

        Returns:
            Dictionary with classification results including GL codes
        """
        results = {
            'description': description,
            'amount': amount,
            'date': date,
            'check_number': check_number,
            'classifications': []
        }

        # Determine transaction direction
        if is_deposit is not None:
            transaction_is_deposit = is_deposit
        else:
            transaction_is_deposit = amount > 0

        desc_lower = description.lower() if description else ''

        # 0. CRITICAL: DEBIT keyword detection - HIGHEST PRIORITY
        # "ACH CORP DEBIT", "DEBIT" in description = ALWAYS Cash Disbursement
        # This overrides all other classification rules because DEBIT explicitly means money OUT
        if 'debit' in desc_lower:
            debit_result = {
                'module': 'CD',
                'confidence': 0.99,  # Highest confidence
                'classifier': 'debit_keyword',
                'priority': 0,  # Highest priority (lower number = higher priority)
                'gl_code': '7200' if 'payroll' in desc_lower else '7900',
                'category': 'ACH Debit Payment'
            }
            results['classifications'].append(debit_result)
            # Override transaction direction - DEBIT is ALWAYS a withdrawal
            transaction_is_deposit = False

        # 1. Check for check number - always CD
        if check_number or 'check #' in desc_lower or 'check no' in desc_lower:
            check_result = {
                'module': 'CD',
                'confidence': 0.95,
                'classifier': 'check_detection',
                'priority': 1,
                'gl_code': '7300',  # Vendor payments default
                'category': 'Check Payment'
            }
            results['classifications'].append(check_result)

        # 1.5. High-confidence bank-generated transaction detection
        # These transactions are unambiguous - they come directly from the bank
        HIGH_CONFIDENCE_BANK_KEYWORDS = {
            'interest': {'module': 'CR', 'gl_code': '4600', 'category': 'Interest Income'},
            'interest credit': {'module': 'CR', 'gl_code': '4600', 'category': 'Interest Income'},
            'interest earned': {'module': 'CR', 'gl_code': '4600', 'category': 'Interest Income'},
            'interest paid': {'module': 'CR', 'gl_code': '4600', 'category': 'Interest Income'},
            'service fee': {'module': 'CD', 'gl_code': '6100', 'category': 'Bank Service Fee'},
            'service charge': {'module': 'CD', 'gl_code': '6100', 'category': 'Bank Service Charge'},
            'monthly fee': {'module': 'CD', 'gl_code': '6100', 'category': 'Bank Monthly Fee'},
            'maintenance fee': {'module': 'CD', 'gl_code': '6100', 'category': 'Bank Maintenance Fee'},
            'nsf fee': {'module': 'CD', 'gl_code': '6100', 'category': 'NSF Fee'},
            'overdraft fee': {'module': 'CD', 'gl_code': '6100', 'category': 'Overdraft Fee'},
            'wire transfer fee': {'module': 'CD', 'gl_code': '6100', 'category': 'Wire Transfer Fee'},
            'wire fee': {'module': 'CD', 'gl_code': '6100', 'category': 'Wire Fee'},
        }

        for keyword, info in HIGH_CONFIDENCE_BANK_KEYWORDS.items():
            if keyword in desc_lower:
                bank_txn_result = {
                    'module': info['module'],
                    'confidence': 0.95,  # High confidence - bank-generated
                    'classifier': 'bank_transaction',
                    'priority': 1,
                    'gl_code': info['gl_code'],
                    'category': info['category']
                }
                results['classifications'].append(bank_txn_result)
                break  # Only match first keyword

        # 2. Check learned patterns first (highest priority for non-checks)
        history_result = self.history_matcher.match(description, amount)
        if history_result and history_result['confidence'] > CONFIDENCE_HIGH:
            history_result['classifier'] = 'history'
            history_result['priority'] = 1
            results['classifications'].append(history_result)

        # 3. Check for refunds/credits (vendor refunds go to CR, not CD)
        is_refund = any(keyword in desc_lower for keyword in
                       ['refund', 'credit memo', 'return', 'reversal', 'credited', 'rebate'])

        # 4. Vendor matching (for expenses)
        if amount < 0 or (not transaction_is_deposit and not is_refund):
            vendor_result = self.vendor_matcher.match(description)
            if vendor_result:
                vendor_result['classifier'] = 'vendor'
                vendor_result['priority'] = 2
                vendor_result['module'] = 'CD'
                results['classifications'].append(vendor_result)

        # 5. Customer/Grant matching (for revenue)
        if amount > 0 or transaction_is_deposit or is_refund:
            customer_result = self.customer_matcher.match(description)
            if customer_result:
                customer_result['classifier'] = 'customer'
                customer_result['priority'] = 2
                customer_result['module'] = 'CR'
                results['classifications'].append(customer_result)

        # 6. Keyword classification with GL code lookup
        keyword_result = self.keyword_classifier.classify(description, amount)
        if keyword_result['module'] != 'UNKNOWN':
            # Enhance with specific GL code
            gl_info = self._get_gl_code_from_keywords(description, amount)
            if gl_info:
                keyword_result['gl_code'] = gl_info.get('gl')
                keyword_result['gl_name'] = gl_info.get('name')
            keyword_result['classifier'] = 'keyword'
            keyword_result['priority'] = 3
            results['classifications'].append(keyword_result)

        # 7. History matching (lower confidence)
        if history_result and history_result['confidence'] <= CONFIDENCE_HIGH:
            history_result['classifier'] = 'history'
            history_result['priority'] = 4
            results['classifications'].append(history_result)

        # 8. Apply module hint from parser if no strong classification
        if module_hint and module_hint in ['CR', 'CD', 'JV']:
            hint_result = {
                'module': module_hint,
                'confidence': 0.5,
                'classifier': 'parser_hint',
                'priority': 5,
                'category': 'Parser Detection'
            }
            results['classifications'].append(hint_result)

        # Determine best classification
        best = self._select_best_classification(results['classifications'], amount, transaction_is_deposit)

        if best:
            results['module'] = best.get('module', 'UNKNOWN')
            results['gl_code'] = best.get('gl_code') or self._suggest_gl_code(best, description, amount)
            results['fund_code'] = best.get('fund_code') or DEFAULT_FUND_CODE
            results['confidence'] = best.get('confidence', 0)
            results['confidence_level'] = self._get_confidence_level(best.get('confidence', 0))
            results['matched_by'] = best.get('classifier', 'unknown')
            results['category'] = best.get('category')
            results['payee'] = best.get('vendor_name') or best.get('name') or best.get('payee')
            results['gl_name'] = best.get('gl_name', '')
        else:
            # No classification - mark as unknown
            results['module'] = 'UNKNOWN'
            results['gl_code'] = None
            results['fund_code'] = None
            results['confidence'] = 0
            results['confidence_level'] = 'none'
            results['matched_by'] = None
            results['category'] = None
            results['payee'] = None

        # Add bank GL
        results['bank_gl'] = DEFAULT_BANK_GL

        # Build proper journal entry
        results['entry'] = self._build_entry(results)

        # Add validation
        results['is_balanced'] = self._validate_entry(results['entry'])

        return results

    def _get_gl_code_from_keywords(self, description: str, amount: float) -> Optional[Dict]:
        """Get specific GL code based on keywords in description"""
        if not description:
            return None

        desc_lower = description.lower()

        # Check each keyword mapping
        for keyword, gl_key in KEYWORD_GL_MAPPING.items():
            if keyword in desc_lower:
                if gl_key in GL_CODE_MAPPING:
                    return GL_CODE_MAPPING[gl_key]

        return None

    def _select_best_classification(self, classifications: List[Dict],
                                    amount: float, is_deposit: bool) -> Optional[Dict]:
        """Select the best classification considering amount direction"""
        if not classifications:
            return None

        # CRITICAL: For deposits (positive amounts), ONLY allow CR or JV, never CD
        # For withdrawals (negative amounts), ONLY allow CD or JV, never CR
        valid_classifications = []

        for c in classifications:
            module = c.get('module', 'UNKNOWN')

            # Strict validation based on transaction direction
            if is_deposit or amount > 0:
                # DEPOSIT: Only CR or JV allowed
                if module in ['CR', 'JV']:
                    valid_classifications.append(c)
            else:
                # WITHDRAWAL: Only CD or JV allowed
                if module in ['CD', 'JV']:
                    valid_classifications.append(c)

            # Always include UNKNOWN for fallback
            if module == 'UNKNOWN':
                valid_classifications.append(c)

        # If no valid classifications found, create a default based on amount
        if not valid_classifications:
            if is_deposit or amount > 0:
                # Default to CR for deposits
                return {
                    'module': 'CR',
                    'confidence': 0.3,
                    'classifier': 'amount_direction',
                    'priority': 10,
                    'category': 'Deposit',
                    'gl_code': '4000'
                }
            else:
                # Default to CD for withdrawals
                return {
                    'module': 'CD',
                    'confidence': 0.3,
                    'classifier': 'amount_direction',
                    'priority': 10,
                    'category': 'Payment',
                    'gl_code': '7000'
                }

        # Sort by confidence (desc), then priority (asc)
        sorted_classifications = sorted(
            valid_classifications,
            key=lambda x: (-x.get('confidence', 0), x.get('priority', 99))
        )

        return sorted_classifications[0] if sorted_classifications else None

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level"""
        if confidence >= CONFIDENCE_HIGH:
            return 'high'
        elif confidence >= CONFIDENCE_MEDIUM:
            return 'medium'
        elif confidence >= CONFIDENCE_LOW:
            return 'low'
        return 'none'

    def _suggest_gl_code(self, classification: Dict, description: str, amount: float) -> str:
        """Suggest GL code based on classification and description"""
        # First try keyword-based GL lookup
        gl_info = self._get_gl_code_from_keywords(description, amount)
        if gl_info:
            return gl_info.get('gl')

        # Use GL suggestion from keyword classifier
        gl_suggestion = classification.get('gl_suggestion')
        if gl_suggestion and gl_suggestion.get('gl'):
            return gl_suggestion['gl']

        # Default GL codes by module
        module = classification.get('module', 'UNKNOWN')
        category = classification.get('category', '').lower() if classification.get('category') else ''

        if module == 'CR':
            if 'grant' in category:
                return '4100'  # Grant Revenue
            elif 'rent' in category:
                return '4200'  # Rental Income
            elif 'donation' in category:
                return '4400'  # Donations
            return '4000'  # General Revenue

        elif module == 'CD':
            if 'payroll' in category:
                return '6100'  # Salaries & Wages
            elif 'tax' in category:
                return '7200'  # Taxes
            elif 'utility' in category:
                return '6500'  # Utilities
            elif 'insurance' in category:
                return '6600'  # Insurance
            return '7300'  # General Vendor Payment

        elif module == 'JV':
            if 'fee' in category or 'charge' in category:
                return '7500'  # Bank Fees
            elif 'interest' in category:
                if amount > 0:
                    return '4600'  # Interest Income
                else:
                    return '7600'  # Interest Expense
            return '7500'  # Default JV

        return None

    def _build_entry(self, result: Dict) -> Dict:
        """
        Build proper double-entry journal entry based on CA principles

        ACCOUNTING RULES:
        - CR: Debit Bank (1070), Credit Revenue (4xxx)
        - CD: Debit Expense (6xxx/7xxx), Credit Bank (1070)
        - JV: Depends on transaction type
        """
        module = result.get('module', 'UNKNOWN')
        amount = abs(result.get('amount', 0))
        gl_code = result.get('gl_code')
        fund_code = result.get('fund_code', DEFAULT_FUND_CODE)
        bank_gl = result.get('bank_gl', DEFAULT_BANK_GL)
        description = result.get('description', '')[:50]

        entry = {'lines': [], 'is_balanced': True}

        if module == 'CR':
            # Cash Receipt: Debit Bank (Asset increases), Credit Revenue (Revenue increases)
            entry['lines'] = [
                {
                    'line': 1,
                    'gl_code': bank_gl,
                    'gl_name': 'Bank Account',
                    'fund_code': fund_code,
                    'debit': amount,
                    'credit': 0,
                    'type': 'Asset',
                    'description': f"Deposit - {description}"
                },
                {
                    'line': 2,
                    'gl_code': gl_code or '4000',
                    'gl_name': result.get('gl_name', 'Revenue'),
                    'fund_code': fund_code,
                    'debit': 0,
                    'credit': amount,
                    'type': 'Revenue',
                    'description': description
                }
            ]

        elif module == 'CD':
            # Cash Disbursement: Debit Expense (Expense increases), Credit Bank (Asset decreases)
            entry['lines'] = [
                {
                    'line': 1,
                    'gl_code': gl_code or '7000',
                    'gl_name': result.get('gl_name', 'Expense'),
                    'fund_code': fund_code,
                    'debit': amount,
                    'credit': 0,
                    'type': 'Expense',
                    'description': description
                },
                {
                    'line': 2,
                    'gl_code': bank_gl,
                    'gl_name': 'Bank Account',
                    'fund_code': fund_code,
                    'debit': 0,
                    'credit': amount,
                    'type': 'Asset',
                    'description': f"Payment - {description}"
                }
            ]

        elif module == 'JV':
            # Journal Voucher: Direction depends on transaction type
            original_amount = result.get('amount', 0)

            if original_amount > 0:
                # Credit to company (e.g., interest income)
                entry['lines'] = [
                    {
                        'line': 1,
                        'gl_code': bank_gl,
                        'gl_name': 'Bank Account',
                        'fund_code': fund_code,
                        'debit': amount,
                        'credit': 0,
                        'type': 'Asset',
                        'description': f"Bank Credit - {description}"
                    },
                    {
                        'line': 2,
                        'gl_code': gl_code or '4600',
                        'gl_name': result.get('gl_name', 'Interest Income'),
                        'fund_code': fund_code,
                        'debit': 0,
                        'credit': amount,
                        'type': 'Income',
                        'description': description
                    }
                ]
            else:
                # Debit from company (e.g., bank fees)
                entry['lines'] = [
                    {
                        'line': 1,
                        'gl_code': gl_code or '7500',
                        'gl_name': result.get('gl_name', 'Bank Fees'),
                        'fund_code': fund_code,
                        'debit': amount,
                        'credit': 0,
                        'type': 'Expense',
                        'description': description
                    },
                    {
                        'line': 2,
                        'gl_code': bank_gl,
                        'gl_name': 'Bank Account',
                        'fund_code': fund_code,
                        'debit': 0,
                        'credit': amount,
                        'type': 'Asset',
                        'description': f"Bank Debit - {description}"
                    }
                ]

        return entry

    def _validate_entry(self, entry: Dict) -> bool:
        """Validate that entry is balanced (Debits = Credits)"""
        lines = entry.get('lines', [])
        total_debits = sum(line.get('debit', 0) for line in lines)
        total_credits = sum(line.get('credit', 0) for line in lines)

        # Allow 1 cent variance for rounding
        return abs(total_debits - total_credits) < 0.01

    def classify_batch(self, transactions: List[Dict]) -> List[Dict]:
        """
        Classify a batch of transactions

        Args:
            transactions: List of transaction dictionaries

        Returns:
            List of classification results with proper GL codes
        """
        results = []

        for txn in transactions:
            result = self.classify(
                description=txn.get('description', ''),
                amount=txn.get('amount', 0),
                date=txn.get('date'),
                check_number=txn.get('check_number'),
                is_deposit=txn.get('is_deposit'),
                module_hint=txn.get('module')
            )
            results.append(result)

        return results

    def learn_from_correction(self, description: str, amount: float,
                              module: str, gl_code: str, fund_code: str,
                              category: str = None, payee: str = None):
        """Learn from a manual correction for future matching"""
        self.history_matcher.learn_from_correction(
            description=description,
            amount=amount,
            module=module,
            gl_code=gl_code,
            fund_code=fund_code,
            category=category,
            payee=payee
        )

    def add_to_history(self, transaction: Dict):
        """Add a classified transaction to history"""
        self.history_matcher.add_to_history(transaction)

    def get_summary(self, results: List[Dict]) -> Dict:
        """Get summary statistics for classified transactions"""
        summary = {
            'total': len(results),
            'by_module': {'CR': 0, 'CD': 0, 'JV': 0, 'UNKNOWN': 0},
            'by_confidence': {'high': 0, 'medium': 0, 'low': 0, 'none': 0},
            'by_classifier': {},
            'total_debits': 0,
            'total_credits': 0,
            'balanced_entries': 0,
            'unbalanced_entries': 0
        }

        for result in results:
            # Count by module
            module = result.get('module', 'UNKNOWN')
            summary['by_module'][module] = summary['by_module'].get(module, 0) + 1

            # Count by confidence
            conf_level = result.get('confidence_level', 'none')
            summary['by_confidence'][conf_level] = summary['by_confidence'].get(conf_level, 0) + 1

            # Count by classifier
            classifier = result.get('matched_by', 'none')
            summary['by_classifier'][classifier] = summary['by_classifier'].get(classifier, 0) + 1

            # Sum amounts
            amount = result.get('amount', 0)
            if amount > 0:
                summary['total_credits'] += amount
            else:
                summary['total_debits'] += abs(amount)

            # Count balanced entries
            if result.get('is_balanced', True):
                summary['balanced_entries'] += 1
            else:
                summary['unbalanced_entries'] += 1

        return summary

    def load_reference_data(self, vendors_file: str = None, customers_file: str = None,
                           grants_file: str = None, gl_history_file: str = None):
        """Load reference data from files"""
        if vendors_file:
            self.vendor_matcher.load_from_file(vendors_file)
        if customers_file:
            self.customer_matcher.load_customers_from_file(customers_file)
        if grants_file:
            self.customer_matcher.load_grants_from_file(grants_file)
        if gl_history_file:
            self.history_matcher.load_history_from_gl(gl_history_file)


# Standalone test
if __name__ == "__main__":
    engine = ClassificationEngine()

    test_transactions = [
        {"description": "ACH Credit HUD CDBG Drawdown #12345", "amount": 50000.00, "date": "12/01/2024", "is_deposit": True},
        {"description": "ADP Payroll Transfer 925735495357", "amount": -15000.00, "date": "12/01/2024", "is_deposit": False},
        {"description": "IRS EFTPS Payment REF# 99345", "amount": -3000.00, "date": "12/01/2024", "is_deposit": False},
        {"description": "Monthly Service Charge", "amount": -25.00, "date": "12/01/2024", "is_deposit": False},
        {"description": "Interest Credit", "amount": 125.50, "date": "12/01/2024", "is_deposit": True},
        {"description": "Wire Transfer to ABC Vendor", "amount": -8500.00, "date": "12/01/2024", "is_deposit": False},
        {"description": "Check #1234", "amount": -250.00, "date": "12/01/2024", "check_number": "1234", "is_deposit": False},
        {"description": "Tenant Rent Payment - Unit 101", "amount": 1500.00, "date": "12/01/2024", "is_deposit": True},
        {"description": "Unknown Transaction XYZ123", "amount": -100.00, "date": "12/01/2024"}
    ]

    print(f"\n{'='*100}")
    print("Classification Engine Test Results (CA Standards)")
    print(f"{'='*100}")

    results = engine.classify_batch(test_transactions)

    for result in results:
        print(f"\n{'-'*100}")
        print(f"Description: {result['description']}")
        print(f"Amount: ${result['amount']:,.2f}")
        print(f"Module: {result['module']} | Confidence: {result['confidence_level']} ({result['confidence']:.0%})")
        print(f"GL Code: {result['gl_code']} ({result.get('gl_name', '')}) | Fund: {result['fund_code']}")
        print(f"Matched By: {result['matched_by']} | Category: {result.get('category')}")
        if result.get('payee'):
            print(f"Payee: {result['payee']}")
        if result.get('entry', {}).get('lines'):
            print("Journal Entry:")
            for line in result['entry']['lines']:
                dr = f"${line['debit']:,.2f}" if line['debit'] else ""
                cr = f"${line['credit']:,.2f}" if line['credit'] else ""
                print(f"  {line['gl_code']:6} {line['gl_name'][:20]:20} | Dr {dr:>12} | Cr {cr:>12}")
            print(f"  Entry Balanced: {result.get('is_balanced', 'N/A')}")

    print(f"\n{'='*100}")
    print("Summary:")
    print(f"{'='*100}")
    summary = engine.get_summary(results)
    print(f"Total Transactions: {summary['total']}")
    print(f"By Module: CR={summary['by_module']['CR']}, CD={summary['by_module']['CD']}, JV={summary['by_module']['JV']}, UNKNOWN={summary['by_module']['UNKNOWN']}")
    print(f"By Confidence: High={summary['by_confidence']['high']}, Medium={summary['by_confidence']['medium']}, Low={summary['by_confidence']['low']}")
    print(f"Total Credits: ${summary['total_credits']:,.2f}")
    print(f"Total Debits: ${summary['total_debits']:,.2f}")
    print(f"Balanced Entries: {summary['balanced_entries']}/{summary['total']}")
