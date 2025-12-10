"""
Module Router - Route classified transactions to appropriate accounting modules
CR (Cash Receipts), CD (Cash Disbursements), JV (Journal Vouchers)
"""

import os
import sys
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SESSION_ID_PREFIX, CURRENT_YEAR

class ModuleRouter:
    """
    Route transactions to appropriate accounting modules based on classification
    Generates module-specific entry structures
    """
    
    def __init__(self):
        self.counters = {
            'CR': 0,
            'CD': 0,
            'JV': 0
        }
        self.routed_transactions = {
            'CR': [],
            'CD': [],
            'JV': [],
            'UNIDENTIFIED': []
        }
        
    def route(self, classified_transaction: Dict) -> Dict:
        """
        Route a single classified transaction to the appropriate module
        
        Args:
            classified_transaction: Output from ClassificationEngine.classify()
            
        Returns:
            Transaction with routing information added
        """
        module = classified_transaction.get('module', 'UNKNOWN')
        
        if module == 'UNKNOWN' or classified_transaction.get('confidence_level') == 'none':
            # Route to unidentified
            classified_transaction['routed_to'] = 'UNIDENTIFIED'
            classified_transaction['needs_review'] = True
            self.routed_transactions['UNIDENTIFIED'].append(classified_transaction)
            return classified_transaction
        
        # Increment counter and generate document number
        self.counters[module] += 1
        doc_number = self._generate_doc_number(module, classified_transaction)
        session_id = SESSION_ID_PREFIX.get(module, f'GP_{module}_{CURRENT_YEAR}')
        
        # Add routing information
        classified_transaction['routed_to'] = module
        classified_transaction['session_id'] = session_id
        classified_transaction['doc_number'] = doc_number
        classified_transaction['sequence'] = self.counters[module]
        classified_transaction['needs_review'] = classified_transaction.get('confidence_level') in ['low', 'medium']
        
        # Add module-specific fields
        if module == 'CR':
            classified_transaction = self._prepare_cash_receipt(classified_transaction)
        elif module == 'CD':
            classified_transaction = self._prepare_cash_disbursement(classified_transaction)
        elif module == 'JV':
            classified_transaction = self._prepare_journal_voucher(classified_transaction)
        
        self.routed_transactions[module].append(classified_transaction)
        return classified_transaction
    
    def _generate_doc_number(self, module: str, transaction: Dict) -> str:
        """Generate document number based on SOP format"""
        date = transaction.get('date', '')
        
        # Try to parse date for document number
        if date:
            try:
                if '/' in date:
                    dt = datetime.strptime(date, '%m/%d/%Y')
                else:
                    dt = datetime.strptime(date, '%Y-%m-%d')
                date_part = dt.strftime('%m%d')
            except:
                date_part = datetime.now().strftime('%m%d')
        else:
            date_part = datetime.now().strftime('%m%d')
        
        # Format: GP_MMDD_SEQ (e.g., GP_1201_001)
        return f"GP_{date_part}_{self.counters[module]:03d}"
    
    def _prepare_cash_receipt(self, transaction: Dict) -> Dict:
        """Prepare Cash Receipt specific fields"""
        transaction['module_type'] = 'Cash Receipt'
        transaction['receipt_type'] = self._determine_receipt_type(transaction)
        
        # Customer/Payer information
        transaction['payer'] = transaction.get('payee') or 'Unknown Payer'
        
        # Entry structure for CR
        # Debit: Bank GL
        # Credit: Revenue GL
        amount = abs(transaction.get('amount', 0))
        transaction['debit_account'] = transaction.get('bank_gl', '1070')
        transaction['credit_account'] = transaction.get('gl_code', '4000')
        transaction['debit_amount'] = amount
        transaction['credit_amount'] = amount
        
        return transaction
    
    def _prepare_cash_disbursement(self, transaction: Dict) -> Dict:
        """Prepare Cash Disbursement specific fields"""
        transaction['module_type'] = 'Cash Disbursement'
        transaction['disbursement_type'] = self._determine_disbursement_type(transaction)
        
        # Vendor/Payee information
        transaction['vendor'] = transaction.get('payee') or 'Unknown Vendor'
        
        # Check information
        if transaction.get('check_number'):
            transaction['payment_method'] = 'Check'
            transaction['reference'] = f"Check #{transaction['check_number']}"
        else:
            transaction['payment_method'] = 'ACH/Wire'
            transaction['reference'] = transaction.get('description', '')[:30]
        
        # Entry structure for CD
        # Debit: Expense GL
        # Credit: Bank GL
        amount = abs(transaction.get('amount', 0))
        transaction['debit_account'] = transaction.get('gl_code', '7000')
        transaction['credit_account'] = transaction.get('bank_gl', '1070')
        transaction['debit_amount'] = amount
        transaction['credit_amount'] = amount
        
        return transaction
    
    def _prepare_journal_voucher(self, transaction: Dict) -> Dict:
        """Prepare Journal Voucher specific fields"""
        transaction['module_type'] = 'Journal Voucher'
        transaction['jv_type'] = self._determine_jv_type(transaction)
        
        # Entry structure for JV depends on transaction type
        amount = abs(transaction.get('amount', 0))
        
        if transaction.get('amount', 0) > 0:
            # Credit to company (e.g., interest income)
            transaction['debit_account'] = transaction.get('bank_gl', '1070')
            transaction['credit_account'] = transaction.get('gl_code', '4600')
        else:
            # Debit from company (e.g., bank fees)
            transaction['debit_account'] = transaction.get('gl_code', '7500')
            transaction['credit_account'] = transaction.get('bank_gl', '1070')
        
        transaction['debit_amount'] = amount
        transaction['credit_amount'] = amount
        transaction['reference'] = transaction.get('description', '')[:50]
        
        return transaction
    
    def _determine_receipt_type(self, transaction: Dict) -> str:
        """Determine the type of cash receipt"""
        description = transaction.get('description', '').lower()
        category = transaction.get('category', '').lower() if transaction.get('category') else ''
        
        if any(kw in description for kw in ['grant', 'hud', 'doe', 'hhs', 'federal']):
            return 'Grant Receipt'
        elif any(kw in description for kw in ['rent', 'lease', 'tenant']):
            return 'Rental Income'
        elif any(kw in description for kw in ['interest', 'dividend']):
            return 'Investment Income'
        elif any(kw in description for kw in ['donation', 'contribution', 'gift']):
            return 'Donation'
        elif any(kw in description for kw in ['refund', 'reimbursement', 'rebate']):
            return 'Refund/Reimbursement'
        else:
            return 'Customer Receipt'
    
    def _determine_disbursement_type(self, transaction: Dict) -> str:
        """Determine the type of cash disbursement"""
        description = transaction.get('description', '').lower()
        
        if any(kw in description for kw in ['payroll', 'salary', 'adp', 'paychex', 'gusto']):
            return 'Payroll'
        elif any(kw in description for kw in ['irs', 'eftps', 'tax']):
            return 'Tax Payment'
        elif any(kw in description for kw in ['rent', 'lease', 'mortgage']):
            return 'Rent/Lease'
        elif any(kw in description for kw in ['utility', 'electric', 'gas', 'water', 'phone']):
            return 'Utilities'
        elif any(kw in description for kw in ['insurance', 'premium']):
            return 'Insurance'
        else:
            return 'Vendor Payment'
    
    def _determine_jv_type(self, transaction: Dict) -> str:
        """Determine the type of journal voucher"""
        description = transaction.get('description', '').lower()
        
        if any(kw in description for kw in ['fee', 'charge', 'service']):
            return 'Bank Fee'
        elif any(kw in description for kw in ['interest']):
            if transaction.get('amount', 0) > 0:
                return 'Interest Income'
            else:
                return 'Interest Expense'
        elif any(kw in description for kw in ['transfer', 'xfer']):
            return 'Transfer'
        elif any(kw in description for kw in ['correction', 'adjustment', 'reversal']):
            return 'Correction'
        else:
            return 'Miscellaneous'
    
    def route_batch(self, classified_transactions: List[Dict]) -> Dict:
        """
        Route a batch of classified transactions
        
        Args:
            classified_transactions: List of classified transactions
            
        Returns:
            Dictionary with routed transactions by module
        """
        for txn in classified_transactions:
            self.route(txn)
        
        return self.routed_transactions
    
    def get_summary(self) -> Dict:
        """Get routing summary"""
        return {
            'total_routed': sum(len(v) for v in self.routed_transactions.values()),
            'by_module': {
                'CR': len(self.routed_transactions['CR']),
                'CD': len(self.routed_transactions['CD']),
                'JV': len(self.routed_transactions['JV']),
                'UNIDENTIFIED': len(self.routed_transactions['UNIDENTIFIED'])
            },
            'needs_review': sum(
                1 for module in ['CR', 'CD', 'JV']
                for txn in self.routed_transactions[module]
                if txn.get('needs_review')
            )
        }
    
    def get_transactions_by_module(self, module: str) -> List[Dict]:
        """Get all transactions routed to a specific module"""
        return self.routed_transactions.get(module, [])
    
    def reset(self):
        """Reset the router for a new batch"""
        self.counters = {'CR': 0, 'CD': 0, 'JV': 0}
        self.routed_transactions = {
            'CR': [],
            'CD': [],
            'JV': [],
            'UNIDENTIFIED': []
        }


# Standalone test
if __name__ == "__main__":
    router = ModuleRouter()
    
    # Sample classified transactions
    test_transactions = [
        {
            'description': 'HUD Grant Drawdown',
            'amount': 50000.00,
            'date': '12/01/2024',
            'module': 'CR',
            'confidence_level': 'high',
            'gl_code': '4100',
            'fund_code': '2700',
            'bank_gl': '1070',
            'payee': 'HUD'
        },
        {
            'description': 'ADP Payroll',
            'amount': -15000.00,
            'date': '12/01/2024',
            'module': 'CD',
            'confidence_level': 'high',
            'gl_code': '7200',
            'fund_code': '2700',
            'bank_gl': '1070',
            'payee': 'ADP'
        },
        {
            'description': 'Monthly Service Fee',
            'amount': -25.00,
            'date': '12/01/2024',
            'module': 'JV',
            'confidence_level': 'high',
            'gl_code': '7500',
            'fund_code': '1000',
            'bank_gl': '1070'
        },
        {
            'description': 'Unknown Transaction',
            'amount': -100.00,
            'date': '12/01/2024',
            'module': 'UNKNOWN',
            'confidence_level': 'none'
        }
    ]
    
    print(f"\n{'='*70}")
    print("Module Router Test Results")
    print(f"{'='*70}")
    
    for txn in test_transactions:
        result = router.route(txn)
        print(f"\n{'-'*70}")
        print(f"Description: {result['description']}")
        print(f"Routed To: {result['routed_to']}")
        if result['routed_to'] != 'UNIDENTIFIED':
            print(f"Session ID: {result.get('session_id')}")
            print(f"Doc Number: {result.get('doc_number')}")
            print(f"Module Type: {result.get('module_type')}")
            print(f"Debit: {result.get('debit_account')} ${result.get('debit_amount', 0):,.2f}")
            print(f"Credit: {result.get('credit_account')} ${result.get('credit_amount', 0):,.2f}")
        print(f"Needs Review: {result.get('needs_review')}")
    
    print(f"\n{'='*70}")
    print("Summary:")
    print(router.get_summary())
