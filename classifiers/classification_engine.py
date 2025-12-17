"""
Classification Engine - Orchestrates all classifiers to determine transaction type
Main brain of the Bank Transaction Posting Tool
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

class ClassificationEngine:
    """
    Main classification engine that combines:
    1. Keyword-based classification
    2. Vendor matching
    3. Customer/Grant matching
    4. Historical pattern matching
    
    Returns the best classification with confidence scores
    """
    
    def __init__(self):
        self.keyword_classifier = KeywordClassifier()
        self.vendor_matcher = VendorMatcher()
        self.customer_matcher = CustomerMatcher()
        self.history_matcher = HistoryMatcher()
        
    def classify(self, description: str, amount: float = 0, 
                 date: str = None, check_number: str = None) -> Dict:
        """
        Classify a transaction and return comprehensive result
        
        Args:
            description: Transaction description/narration
            amount: Transaction amount (positive=credit, negative=debit)
            date: Transaction date
            check_number: Check number if applicable
            
        Returns:
            Dictionary with classification results
        """
        results = {
            'description': description,
            'amount': amount,
            'date': date,
            'check_number': check_number,
            'classifications': []
        }
        
        # 1. Check learned patterns first (highest priority)
        history_result = self.history_matcher.match(description, amount)
        if history_result and history_result['confidence'] > CONFIDENCE_HIGH:
            history_result['classifier'] = 'history'
            history_result['priority'] = 1
            results['classifications'].append(history_result)

        # 2. Check for refunds/credits (CRITICAL FIX for vendor refunds)
        is_refund = any(keyword in description.lower() for keyword in ['refund', 'credit memo', 'return', 'reversal', 'credited'])

        # 3. Vendor matching (for expenses AND refunds)
        if amount < 0 or is_refund:  # Debit/Expense OR Refund
            vendor_result = self.vendor_matcher.match(description)
            if vendor_result:
                vendor_result['classifier'] = 'vendor'
                vendor_result['priority'] = 2
                vendor_result['module'] = 'CD'  # Cash Disbursement (negative for refunds)

                # If it's a refund, make amount negative for CD
                if is_refund and amount > 0:
                    vendor_result['is_refund'] = True
                    vendor_result['original_amount'] = amount
                    vendor_result['adjusted_amount'] = -amount  # Make negative for CD

                results['classifications'].append(vendor_result)

        # 4. Customer/Grant matching (for revenue, but not if it's a vendor refund)
        if amount > 0 and not is_refund:  # Credit/Revenue (excluding refunds)
            customer_result = self.customer_matcher.match(description)
            if customer_result:
                customer_result['classifier'] = 'customer'
                customer_result['priority'] = 2
                customer_result['module'] = 'CR'  # Cash Receipt
                results['classifications'].append(customer_result)
        
        # 4. Keyword classification
        keyword_result = self.keyword_classifier.classify(description, amount)
        if keyword_result['module'] != 'UNKNOWN':
            keyword_result['classifier'] = 'keyword'
            keyword_result['priority'] = 3
            results['classifications'].append(keyword_result)
        
        # 5. History matching (lower confidence)
        if history_result and history_result['confidence'] <= CONFIDENCE_HIGH:
            history_result['classifier'] = 'history'
            history_result['priority'] = 4
            results['classifications'].append(history_result)
        
        # Determine best classification
        best = self._select_best_classification(results['classifications'], amount)
        
        if best:
            results['module'] = best.get('module', 'UNKNOWN')
            results['gl_code'] = best.get('gl_code') or self._suggest_gl_code(best, description, amount)
            results['fund_code'] = best.get('fund_code') or DEFAULT_FUND_CODE
            results['confidence'] = best.get('confidence', 0)
            results['confidence_level'] = self._get_confidence_level(best.get('confidence', 0))
            results['matched_by'] = best.get('classifier', 'unknown')
            results['category'] = best.get('category')
            results['payee'] = best.get('vendor_name') or best.get('name') or best.get('payee')
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
        
        # Determine debit/credit based on module and amount
        results['entry'] = self._build_entry(results)
        
        return results
    
    def _select_best_classification(self, classifications: List[Dict], amount: float) -> Optional[Dict]:
        """Select the best classification from all results"""
        if not classifications:
            return None
        
        # Sort by confidence (desc), then priority (asc)
        sorted_classifications = sorted(
            classifications,
            key=lambda x: (-x.get('confidence', 0), x.get('priority', 99))
        )
        
        # Return best match
        return sorted_classifications[0]
    
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
        """Suggest GL code based on classification"""
        # Use GL suggestion from keyword classifier
        gl_suggestion = classification.get('gl_suggestion')
        if gl_suggestion and gl_suggestion.get('gl'):
            return gl_suggestion['gl']
        
        # Default GL codes by module
        module = classification.get('module', 'UNKNOWN')
        
        if module == 'CR':
            return '4000'  # Revenue
        elif module == 'CD':
            return '7000'  # Expense
        elif module == 'JV':
            return '7500'  # Bank fees default
        
        return None
    
    def _build_entry(self, result: Dict) -> Dict:
        """Build debit/credit entry based on classification"""
        module = result.get('module', 'UNKNOWN')
        amount = abs(result.get('amount', 0))
        gl_code = result.get('gl_code')
        fund_code = result.get('fund_code', DEFAULT_FUND_CODE)
        bank_gl = result.get('bank_gl', DEFAULT_BANK_GL)
        
        entry = {
            'lines': []
        }
        
        if module == 'CR':
            # Cash Receipt: Debit Bank, Credit Revenue
            entry['lines'] = [
                {'gl_code': bank_gl, 'fund_code': fund_code, 'debit': amount, 'credit': 0, 'type': 'Bank'},
                {'gl_code': gl_code, 'fund_code': fund_code, 'debit': 0, 'credit': amount, 'type': 'Revenue'}
            ]
        elif module == 'CD':
            # Cash Disbursement: Debit Expense, Credit Bank
            entry['lines'] = [
                {'gl_code': gl_code, 'fund_code': fund_code, 'debit': amount, 'credit': 0, 'type': 'Expense'},
                {'gl_code': bank_gl, 'fund_code': fund_code, 'debit': 0, 'credit': amount, 'type': 'Bank'}
            ]
        elif module == 'JV':
            # Journal Voucher: Varies by type
            if result.get('amount', 0) > 0:
                # Credit to bank (e.g., interest income)
                entry['lines'] = [
                    {'gl_code': bank_gl, 'fund_code': fund_code, 'debit': amount, 'credit': 0, 'type': 'Bank'},
                    {'gl_code': gl_code, 'fund_code': fund_code, 'debit': 0, 'credit': amount, 'type': 'Income'}
                ]
            else:
                # Debit to bank (e.g., bank fees)
                entry['lines'] = [
                    {'gl_code': gl_code, 'fund_code': fund_code, 'debit': amount, 'credit': 0, 'type': 'Expense'},
                    {'gl_code': bank_gl, 'fund_code': fund_code, 'debit': 0, 'credit': amount, 'type': 'Bank'}
                ]
        
        return entry
    
    def classify_batch(self, transactions: List[Dict]) -> List[Dict]:
        """
        Classify a batch of transactions
        
        Args:
            transactions: List of transaction dictionaries with keys:
                         description, amount, date, check_number (optional)
                         
        Returns:
            List of classification results
        """
        results = []
        
        for txn in transactions:
            result = self.classify(
                description=txn.get('description', ''),
                amount=txn.get('amount', 0),
                date=txn.get('date'),
                check_number=txn.get('check_number')
            )
            results.append(result)
        
        return results
    
    def learn_from_correction(self, description: str, amount: float,
                              module: str, gl_code: str, fund_code: str,
                              category: str = None, payee: str = None):
        """
        Learn from a manual correction
        Updates the history matcher with new pattern
        """
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
            'total_credits': 0
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
        {"description": "ACH Credit HUD CDBG Drawdown #12345", "amount": 50000.00, "date": "12/01/2024"},
        {"description": "ADP Payroll Transfer 925735495357", "amount": -15000.00, "date": "12/01/2024"},
        {"description": "IRS EFTPS Payment REF# 99345", "amount": -3000.00, "date": "12/01/2024"},
        {"description": "Monthly Service Charge", "amount": -25.00, "date": "12/01/2024"},
        {"description": "Interest Credit", "amount": 125.50, "date": "12/01/2024"},
        {"description": "Wire Transfer to ABC Vendor", "amount": -8500.00, "date": "12/01/2024"},
        {"description": "Check #1234 - Staples Office Supplies", "amount": -250.00, "date": "12/01/2024", "check_number": "1234"},
        {"description": "Customer Payment - Invoice #5678", "amount": 1500.00, "date": "12/01/2024"},
        {"description": "Unknown Transaction XYZ123", "amount": -100.00, "date": "12/01/2024"}
    ]
    
    print(f"\n{'='*90}")
    print("Classification Engine Test Results")
    print(f"{'='*90}")
    
    results = engine.classify_batch(test_transactions)
    
    for result in results:
        print(f"\n{'-'*90}")
        print(f"Description: {result['description']}")
        print(f"Amount: ${result['amount']:,.2f}")
        print(f"Module: {result['module']} | Confidence: {result['confidence_level']}")
        print(f"GL Code: {result['gl_code']} | Fund: {result['fund_code']}")
        print(f"Matched By: {result['matched_by']}")
        if result.get('payee'):
            print(f"Payee: {result['payee']}")
        if result.get('entry', {}).get('lines'):
            print("Entry:")
            for line in result['entry']['lines']:
                dr = f"${line['debit']:,.2f}" if line['debit'] else ""
                cr = f"${line['credit']:,.2f}" if line['credit'] else ""
                print(f"  {line['gl_code']} ({line['type']}): Dr {dr:>12} | Cr {cr:>12}")
    
    print(f"\n{'='*90}")
    print("Summary:")
    print(f"{'='*90}")
    summary = engine.get_summary(results)
    print(f"Total Transactions: {summary['total']}")
    print(f"By Module: {summary['by_module']}")
    print(f"By Confidence: {summary['by_confidence']}")
    print(f"Total Credits: ${summary['total_credits']:,.2f}")
    print(f"Total Debits: ${summary['total_debits']:,.2f}")
