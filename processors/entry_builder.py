"""
Entry Builder - Generate properly formatted journal entries for each module
Creates entries ready for import into accounting systems
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SESSION_ID_PREFIX, CURRENT_YEAR, DEFAULT_BANK_GL, DEFAULT_FUND_CODE

class EntryBuilder:
    """
    Build formatted journal entries for each module type
    Generates entries compatible with MIP, QuickBooks Desktop, and other systems
    """
    
    def __init__(self, target_system: str = 'MIP'):
        """
        Initialize entry builder
        
        Args:
            target_system: Target accounting system ('MIP', 'QBD', 'Generic')
        """
        self.target_system = target_system
        self.entries = {
            'CR': [],
            'CD': [],
            'JV': []
        }
        
    def validate_entry_balance(self, entry: Dict) -> Dict:
        """
        Validate that entry is balanced (debits = credits)

        Args:
            entry: Journal entry to validate

        Returns:
            Validation result dict with 'is_balanced', 'total_debits', 'total_credits', 'variance'
        """
        lines = entry.get('lines', [])
        total_debits = sum(line.get('debit', 0) for line in lines)
        total_credits = sum(line.get('credit', 0) for line in lines)
        variance = abs(total_debits - total_credits)

        # Allow 1 cent rounding difference
        is_balanced = variance < 0.01

        result = {
            'is_balanced': is_balanced,
            'total_debits': round(total_debits, 2),
            'total_credits': round(total_credits, 2),
            'variance': round(variance, 2)
        }

        if not is_balanced:
            entry['needs_review'] = True
            entry['review_reason'] = entry.get('review_reason', '') + f' | UNBALANCED: DR={total_debits:.2f} CR={total_credits:.2f}'
            entry['validation_error'] = f'Entry does not balance. Debits: ${total_debits:.2f}, Credits: ${total_credits:.2f}, Variance: ${variance:.2f}'

        entry['balance_check'] = result
        return result

    def build_entry(self, routed_transaction: Dict) -> Dict:
        """
        Build a formatted entry from a routed transaction

        Args:
            routed_transaction: Output from ModuleRouter.route()

        Returns:
            Formatted entry dictionary with balance validation
        """
        module = routed_transaction.get('routed_to')

        if module == 'UNIDENTIFIED':
            entry = self._build_unidentified_entry(routed_transaction)
        elif module == 'CR':
            entry = self._build_cash_receipt_entry(routed_transaction)
        elif module == 'CD':
            entry = self._build_cash_disbursement_entry(routed_transaction)
        elif module == 'JV':
            entry = self._build_journal_voucher_entry(routed_transaction)
        else:
            entry = routed_transaction

        # Validate balance for all entries with lines
        if 'lines' in entry and len(entry['lines']) > 0:
            self.validate_entry_balance(entry)

        return entry
    
    def _build_cash_receipt_entry(self, txn: Dict) -> Dict:
        """Build Cash Receipt entry as per SOP"""
        amount = abs(txn.get('amount', 0))
        
        entry = {
            # Header fields
            'entry_type': 'Cash Receipt',
            'session_id': txn.get('session_id', SESSION_ID_PREFIX.get('CR')),
            'doc_number': txn.get('doc_number'),
            'doc_date': txn.get('date'),
            'posting_date': txn.get('date'),
            
            # Payer information
            'payer_name': txn.get('payer') or txn.get('payee') or 'Unknown',
            'receipt_type': txn.get('receipt_type', 'Customer Receipt'),
            
            # Amount
            'amount': amount,
            
            # Description
            'description': txn.get('description', '')[:100],
            'memo': txn.get('description', ''),
            
            # Account distribution
            'lines': [
                {
                    'line_number': 1,
                    'gl_code': txn.get('bank_gl', DEFAULT_BANK_GL),
                    'fund_code': txn.get('fund_code', DEFAULT_FUND_CODE),
                    'debit': amount,
                    'credit': 0,
                    'description': f"Bank Deposit - {txn.get('description', '')[:50]}"
                },
                {
                    'line_number': 2,
                    'gl_code': txn.get('gl_code', '4000'),
                    'fund_code': txn.get('fund_code', DEFAULT_FUND_CODE),
                    'debit': 0,
                    'credit': amount,
                    'description': txn.get('description', '')[:50]
                }
            ],
            
            # Metadata
            'source_data': {
                'original_description': txn.get('description'),
                'original_amount': txn.get('amount'),
                'confidence': txn.get('confidence_level'),
                'matched_by': txn.get('matched_by')
            },
            
            'needs_review': txn.get('needs_review', False)
        }
        
        # Add system-specific fields
        if self.target_system == 'MIP':
            entry['batch_id'] = f"CR_{datetime.now().strftime('%Y%m%d')}"
        elif self.target_system == 'QBD':
            entry['txn_type'] = 'Deposit'
        
        self.entries['CR'].append(entry)
        return entry
    
    def _build_cash_disbursement_entry(self, txn: Dict) -> Dict:
        """Build Cash Disbursement entry as per SOP"""
        amount = abs(txn.get('amount', 0))
        
        entry = {
            # Header fields
            'entry_type': 'Cash Disbursement',
            'session_id': txn.get('session_id', SESSION_ID_PREFIX.get('CD')),
            'doc_number': txn.get('doc_number'),
            'doc_date': txn.get('date'),
            'posting_date': txn.get('date'),
            
            # Vendor information
            'vendor_name': txn.get('vendor') or txn.get('payee') or 'Unknown',
            'disbursement_type': txn.get('disbursement_type', 'Vendor Payment'),
            'payment_method': txn.get('payment_method', 'ACH'),
            'check_number': txn.get('check_number'),
            'reference': txn.get('reference', ''),
            
            # Amount
            'amount': amount,
            
            # Description
            'description': txn.get('description', '')[:100],
            'memo': txn.get('description', ''),
            
            # Account distribution
            'lines': [
                {
                    'line_number': 1,
                    'gl_code': txn.get('gl_code', '7000'),
                    'fund_code': txn.get('fund_code', DEFAULT_FUND_CODE),
                    'debit': amount,
                    'credit': 0,
                    'description': txn.get('description', '')[:50]
                },
                {
                    'line_number': 2,
                    'gl_code': txn.get('bank_gl', DEFAULT_BANK_GL),
                    'fund_code': txn.get('fund_code', DEFAULT_FUND_CODE),
                    'debit': 0,
                    'credit': amount,
                    'description': f"Bank Payment - {txn.get('vendor', 'Vendor')}"
                }
            ],
            
            # Metadata
            'source_data': {
                'original_description': txn.get('description'),
                'original_amount': txn.get('amount'),
                'confidence': txn.get('confidence_level'),
                'matched_by': txn.get('matched_by')
            },
            
            'needs_review': txn.get('needs_review', False)
        }
        
        # Add system-specific fields
        if self.target_system == 'MIP':
            entry['batch_id'] = f"CD_{datetime.now().strftime('%Y%m%d')}"
        elif self.target_system == 'QBD':
            if txn.get('check_number'):
                entry['txn_type'] = 'Check'
            else:
                entry['txn_type'] = 'Bill Payment'
        
        self.entries['CD'].append(entry)
        return entry
    
    def _build_journal_voucher_entry(self, txn: Dict) -> Dict:
        """Build Journal Voucher entry as per SOP"""
        amount = abs(txn.get('amount', 0))
        original_amount = txn.get('amount', 0)
        
        # Determine debit/credit based on transaction direction
        if original_amount > 0:
            # Credit to company (e.g., interest income)
            debit_gl = txn.get('bank_gl', DEFAULT_BANK_GL)
            credit_gl = txn.get('gl_code', '4600')
            debit_desc = 'Bank Credit'
            credit_desc = txn.get('jv_type', 'Income')
        else:
            # Debit from company (e.g., bank fees)
            debit_gl = txn.get('gl_code', '7500')
            credit_gl = txn.get('bank_gl', DEFAULT_BANK_GL)
            debit_desc = txn.get('jv_type', 'Expense')
            credit_desc = 'Bank Debit'
        
        entry = {
            # Header fields
            'entry_type': 'Journal Voucher',
            'session_id': txn.get('session_id', SESSION_ID_PREFIX.get('JV')),
            'doc_number': txn.get('doc_number'),
            'doc_date': txn.get('date'),
            'posting_date': txn.get('date'),
            
            # JV information
            'jv_type': txn.get('jv_type', 'Miscellaneous'),
            'reference': txn.get('reference', txn.get('description', '')[:50]),
            
            # Amount
            'amount': amount,
            
            # Description
            'description': txn.get('description', '')[:100],
            'memo': txn.get('description', ''),
            
            # Account distribution
            'lines': [
                {
                    'line_number': 1,
                    'gl_code': debit_gl,
                    'fund_code': txn.get('fund_code', DEFAULT_FUND_CODE),
                    'debit': amount,
                    'credit': 0,
                    'description': f"{debit_desc} - {txn.get('description', '')[:40]}"
                },
                {
                    'line_number': 2,
                    'gl_code': credit_gl,
                    'fund_code': txn.get('fund_code', DEFAULT_FUND_CODE),
                    'debit': 0,
                    'credit': amount,
                    'description': f"{credit_desc} - {txn.get('description', '')[:40]}"
                }
            ],
            
            # Metadata
            'source_data': {
                'original_description': txn.get('description'),
                'original_amount': txn.get('amount'),
                'confidence': txn.get('confidence_level'),
                'matched_by': txn.get('matched_by')
            },
            
            'needs_review': txn.get('needs_review', False)
        }
        
        # Add system-specific fields
        if self.target_system == 'MIP':
            entry['batch_id'] = f"JV_{datetime.now().strftime('%Y%m%d')}"
        elif self.target_system == 'QBD':
            entry['txn_type'] = 'Journal Entry'
        
        self.entries['JV'].append(entry)
        return entry
    
    def _build_unidentified_entry(self, txn: Dict) -> Dict:
        """Build entry for unidentified transactions"""
        return {
            'entry_type': 'Unidentified',
            'date': txn.get('date'),
            'description': txn.get('description'),
            'amount': txn.get('amount'),
            'original_data': txn,
            'needs_review': True,
            'review_reason': 'Unable to classify transaction'
        }
    
    def build_batch(self, routed_transactions: List[Dict]) -> Dict:
        """
        Build entries for a batch of routed transactions
        
        Args:
            routed_transactions: List of routed transactions
            
        Returns:
            Dictionary of entries by module
        """
        for txn in routed_transactions:
            self.build_entry(txn)
        
        return self.entries
    
    def get_entries_by_module(self, module: str) -> List[Dict]:
        """Get all entries for a specific module"""
        return self.entries.get(module, [])
    
    def get_all_entries(self) -> Dict:
        """Get all entries organized by module"""
        return self.entries
    
    def get_summary(self) -> Dict:
        """Get summary of built entries"""
        summary = {
            'total_entries': sum(len(v) for v in self.entries.values()),
            'by_module': {k: len(v) for k, v in self.entries.items()},
            'total_amount': {
                'CR': sum(e.get('amount', 0) for e in self.entries['CR']),
                'CD': sum(e.get('amount', 0) for e in self.entries['CD']),
                'JV': sum(e.get('amount', 0) for e in self.entries['JV'])
            },
            'needs_review': sum(
                1 for module in self.entries.values()
                for entry in module
                if entry.get('needs_review')
            )
        }
        return summary
    
    def reset(self):
        """Reset the builder for a new batch"""
        self.entries = {'CR': [], 'CD': [], 'JV': []}


# Standalone test
if __name__ == "__main__":
    builder = EntryBuilder(target_system='MIP')
    
    # Sample routed transactions
    test_transactions = [
        {
            'description': 'HUD Grant Drawdown #12345',
            'amount': 50000.00,
            'date': '12/01/2024',
            'routed_to': 'CR',
            'session_id': 'GP_CR_2024',
            'doc_number': 'GP_1201_001',
            'receipt_type': 'Grant Receipt',
            'payer': 'HUD',
            'gl_code': '4100',
            'fund_code': '2700',
            'bank_gl': '1070',
            'confidence_level': 'high',
            'matched_by': 'keyword',
            'needs_review': False
        },
        {
            'description': 'ADP Payroll Transfer',
            'amount': -15000.00,
            'date': '12/01/2024',
            'routed_to': 'CD',
            'session_id': 'GP_CD_2024',
            'doc_number': 'GP_1201_001',
            'disbursement_type': 'Payroll',
            'vendor': 'ADP',
            'payment_method': 'ACH',
            'gl_code': '7200',
            'fund_code': '2700',
            'bank_gl': '1070',
            'confidence_level': 'high',
            'matched_by': 'vendor',
            'needs_review': False
        },
        {
            'description': 'Monthly Service Charge',
            'amount': -25.00,
            'date': '12/01/2024',
            'routed_to': 'JV',
            'session_id': 'GP_JV_2024',
            'doc_number': 'GP_1201_001',
            'jv_type': 'Bank Fee',
            'gl_code': '7500',
            'fund_code': '1000',
            'bank_gl': '1070',
            'confidence_level': 'high',
            'matched_by': 'keyword',
            'needs_review': False
        }
    ]
    
    print(f"\n{'='*80}")
    print("Entry Builder Test Results")
    print(f"{'='*80}")
    
    for txn in test_transactions:
        entry = builder.build_entry(txn)
        print(f"\n{'-'*80}")
        print(f"Entry Type: {entry['entry_type']}")
        print(f"Doc Number: {entry['doc_number']}")
        print(f"Date: {entry['doc_date']}")
        print(f"Amount: ${entry['amount']:,.2f}")
        print(f"Description: {entry['description'][:60]}")
        print("\nAccount Distribution:")
        for line in entry['lines']:
            dr = f"${line['debit']:,.2f}" if line['debit'] else ""
            cr = f"${line['credit']:,.2f}" if line['credit'] else ""
            print(f"  Line {line['line_number']}: GL {line['gl_code']} Fund {line['fund_code']} | Dr: {dr:>12} | Cr: {cr:>12}")
    
    print(f"\n{'='*80}")
    print("Summary:")
    print(builder.get_summary())
