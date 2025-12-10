"""
History Matcher Module - Learn from historical GL entries
Implements pattern recognition based on past transactions
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR

class HistoryMatcher:
    """
    Match transactions based on historical patterns
    Learns from past GL entries and manual corrections
    """
    
    def __init__(self):
        self.history = self._load_history()
        self.learned_patterns = self._load_learned_patterns()
        
    def _load_history(self) -> List[Dict]:
        """Load historical transactions"""
        history_file = os.path.join(DATA_DIR, 'transaction_history.json')
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        
        return []
    
    def _load_learned_patterns(self) -> Dict:
        """Load patterns learned from manual corrections"""
        patterns_file = os.path.join(DATA_DIR, 'learned_patterns.json')
        
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r') as f:
                return json.load(f)
        
        return {
            'description_patterns': {},  # description -> {module, gl, fund}
            'amount_patterns': {},  # amount range -> {module, gl, fund}
            'recurring_transactions': []  # List of recurring transaction patterns
        }
    
    def match(self, description: str, amount: float = None) -> Optional[Dict]:
        """
        Find matching historical transaction
        
        Args:
            description: Transaction description
            amount: Transaction amount
            
        Returns:
            Match result with module, gl_code, fund_code, confidence
        """
        # First check learned patterns (highest priority - manual corrections)
        learned_match = self._match_learned_patterns(description, amount)
        if learned_match and learned_match['confidence'] > 0.8:
            return learned_match
        
        # Then check historical transactions
        history_match = self._match_history(description, amount)
        if history_match:
            return history_match
        
        # Check recurring patterns
        recurring_match = self._match_recurring(description, amount)
        if recurring_match:
            return recurring_match
        
        return None
    
    def _match_learned_patterns(self, description: str, amount: float = None) -> Optional[Dict]:
        """Match against manually learned patterns"""
        description_lower = description.lower()
        patterns = self.learned_patterns.get('description_patterns', {})
        
        best_match = None
        best_score = 0
        
        for pattern, mapping in patterns.items():
            # Calculate similarity
            score = self._calculate_similarity(description_lower, pattern.lower())
            
            if score > best_score and score > 0.7:
                best_score = score
                best_match = mapping
        
        if best_match:
            return {
                'module': best_match.get('module'),
                'gl_code': best_match.get('gl_code'),
                'fund_code': best_match.get('fund_code'),
                'category': best_match.get('category'),
                'match_type': 'learned_pattern',
                'confidence': best_score,
                'source': 'manual_correction'
            }
        
        return None
    
    def _match_history(self, description: str, amount: float = None) -> Optional[Dict]:
        """Match against historical transactions"""
        if not self.history:
            return None
        
        description_lower = description.lower()
        matches = []
        
        for hist in self.history:
            hist_desc = hist.get('description', '').lower()
            
            # Calculate description similarity
            desc_score = self._calculate_similarity(description_lower, hist_desc)
            
            # Calculate amount similarity if provided
            amount_score = 0
            if amount is not None and hist.get('amount'):
                amount_score = self._calculate_amount_similarity(amount, hist['amount'])
            
            # Combined score
            if amount is not None:
                combined_score = (desc_score * 0.7) + (amount_score * 0.3)
            else:
                combined_score = desc_score
            
            if combined_score > 0.6:
                matches.append({
                    'history': hist,
                    'score': combined_score
                })
        
        if matches:
            # Get best match
            best = max(matches, key=lambda x: x['score'])
            hist = best['history']
            
            return {
                'module': hist.get('module'),
                'gl_code': hist.get('gl_code'),
                'fund_code': hist.get('fund_code'),
                'category': hist.get('category'),
                'payee': hist.get('payee'),
                'match_type': 'historical',
                'confidence': best['score'],
                'matched_description': hist.get('description'),
                'source': 'history'
            }
        
        return None
    
    def _match_recurring(self, description: str, amount: float = None) -> Optional[Dict]:
        """Match against recurring transaction patterns"""
        recurring = self.learned_patterns.get('recurring_transactions', [])
        
        for pattern in recurring:
            # Check description pattern
            if pattern.get('description_pattern'):
                if re.search(pattern['description_pattern'], description, re.IGNORECASE):
                    # Check amount range if specified
                    if amount is not None and pattern.get('amount_range'):
                        min_amt, max_amt = pattern['amount_range']
                        if not (min_amt <= abs(amount) <= max_amt):
                            continue
                    
                    return {
                        'module': pattern.get('module'),
                        'gl_code': pattern.get('gl_code'),
                        'fund_code': pattern.get('fund_code'),
                        'category': pattern.get('category'),
                        'match_type': 'recurring',
                        'confidence': 0.85,
                        'pattern_name': pattern.get('name'),
                        'source': 'recurring_pattern'
                    }
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using multiple methods"""
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Contains match
        if text1 in text2 or text2 in text1:
            return 0.9
        
        # Word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if words1 and words2:
            overlap = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = overlap / union if union > 0 else 0
            
            # Sequence matching
            seq_ratio = SequenceMatcher(None, text1, text2).ratio()
            
            # Combined score
            return (jaccard * 0.4) + (seq_ratio * 0.6)
        
        return 0
    
    def _calculate_amount_similarity(self, amount1: float, amount2: float) -> float:
        """Calculate how similar two amounts are"""
        if amount1 == amount2:
            return 1.0
        
        # Handle sign differences
        if (amount1 > 0) != (amount2 > 0):
            return 0
        
        # Calculate percentage difference
        avg = (abs(amount1) + abs(amount2)) / 2
        if avg == 0:
            return 1.0
        
        diff_pct = abs(abs(amount1) - abs(amount2)) / avg
        
        # Convert to similarity score
        if diff_pct == 0:
            return 1.0
        elif diff_pct <= 0.01:  # Within 1%
            return 0.95
        elif diff_pct <= 0.05:  # Within 5%
            return 0.85
        elif diff_pct <= 0.10:  # Within 10%
            return 0.70
        elif diff_pct <= 0.25:  # Within 25%
            return 0.50
        else:
            return 0
    
    def learn_from_correction(self, description: str, amount: float,
                              module: str, gl_code: str, fund_code: str,
                              category: str = None, payee: str = None):
        """
        Learn from a manual correction
        Stores the pattern for future matching
        """
        # Add to description patterns
        patterns = self.learned_patterns.setdefault('description_patterns', {})
        
        # Normalize description for pattern
        pattern_key = self._normalize_description(description)
        
        patterns[pattern_key] = {
            'module': module,
            'gl_code': gl_code,
            'fund_code': fund_code,
            'category': category,
            'payee': payee,
            'original_description': description,
            'amount': amount,
            'learned_at': datetime.now().isoformat(),
            'times_matched': 0
        }
        
        # Save patterns
        self._save_learned_patterns()
    
    def add_to_history(self, transaction: Dict):
        """Add a processed transaction to history"""
        self.history.append({
            'description': transaction.get('description'),
            'amount': transaction.get('amount'),
            'date': transaction.get('date'),
            'module': transaction.get('module'),
            'gl_code': transaction.get('gl_code'),
            'fund_code': transaction.get('fund_code'),
            'category': transaction.get('category'),
            'payee': transaction.get('payee'),
            'added_at': datetime.now().isoformat()
        })
        
        # Keep history manageable (last 10000 entries)
        if len(self.history) > 10000:
            self.history = self.history[-10000:]
        
        self._save_history()
    
    def add_recurring_pattern(self, name: str, description_pattern: str,
                              module: str, gl_code: str, fund_code: str,
                              amount_range: Tuple[float, float] = None,
                              category: str = None):
        """Add a recurring transaction pattern"""
        recurring = self.learned_patterns.setdefault('recurring_transactions', [])
        
        recurring.append({
            'name': name,
            'description_pattern': description_pattern,
            'module': module,
            'gl_code': gl_code,
            'fund_code': fund_code,
            'amount_range': amount_range,
            'category': category,
            'added_at': datetime.now().isoformat()
        })
        
        self._save_learned_patterns()
    
    def _normalize_description(self, description: str) -> str:
        """Normalize description for pattern matching"""
        # Remove numbers that might be reference numbers
        normalized = re.sub(r'\d{6,}', '', description)
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        return normalized.lower().strip()
    
    def _save_learned_patterns(self):
        """Save learned patterns to file"""
        patterns_file = os.path.join(DATA_DIR, 'learned_patterns.json')
        with open(patterns_file, 'w') as f:
            json.dump(self.learned_patterns, f, indent=2)
    
    def _save_history(self):
        """Save history to file"""
        history_file = os.path.join(DATA_DIR, 'transaction_history.json')
        with open(history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def load_history_from_gl(self, file_path: str):
        """
        Load historical data from a GL export file
        Used to bootstrap the learning system
        """
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Expected columns: Date, Description, Amount, GL Code, Fund Code
            # Map common column names
            column_map = {
                'date': ['date', 'trans date', 'transaction date', 'posting date'],
                'description': ['description', 'narration', 'memo', 'details'],
                'amount': ['amount', 'debit', 'credit'],
                'gl_code': ['gl code', 'gl', 'account', 'account code', 'acct'],
                'fund_code': ['fund code', 'fund', 'fund no']
            }
            
            # Find actual columns
            actual_cols = {}
            for target, options in column_map.items():
                for col in df.columns:
                    if col.lower().strip() in options:
                        actual_cols[target] = col
                        break
            
            for _, row in df.iterrows():
                if 'description' in actual_cols and 'gl_code' in actual_cols:
                    self.add_to_history({
                        'description': str(row.get(actual_cols.get('description', ''), '')),
                        'amount': float(row.get(actual_cols.get('amount', ''), 0) or 0),
                        'date': str(row.get(actual_cols.get('date', ''), '')),
                        'gl_code': str(row.get(actual_cols.get('gl_code', ''), '')),
                        'fund_code': str(row.get(actual_cols.get('fund_code', ''), ''))
                    })
            
            print(f"Loaded {len(self.history)} historical transactions")
            
        except Exception as e:
            print(f"Error loading GL history: {e}")
    
    def get_statistics(self) -> Dict:
        """Get statistics about learned patterns"""
        return {
            'total_history': len(self.history),
            'learned_patterns': len(self.learned_patterns.get('description_patterns', {})),
            'recurring_patterns': len(self.learned_patterns.get('recurring_transactions', []))
        }


# Standalone test
if __name__ == "__main__":
    matcher = HistoryMatcher()
    
    # Add some sample patterns
    matcher.learn_from_correction(
        description="ADP Payroll Fees 925735495357",
        amount=-133.00,
        module="CD",
        gl_code="7200",
        fund_code="2700",
        category="Payroll Fees"
    )
    
    matcher.add_recurring_pattern(
        name="Monthly Bank Fee",
        description_pattern=r"monthly.*service.*charge|service.*fee",
        module="JV",
        gl_code="7500",
        fund_code="1000",
        amount_range=(10, 100),
        category="Bank Fees"
    )
    
    # Test matching
    test_descriptions = [
        ("ADP Payroll Fees 123456789", -133.00),
        ("Monthly Service Charge", -25.00),
        ("Unknown Transaction", -500.00)
    ]
    
    print(f"\n{'='*70}")
    print("History Matcher Test Results")
    print(f"{'='*70}")
    
    for desc, amount in test_descriptions:
        result = matcher.match(desc, amount)
        print(f"\nDescription: {desc}")
        print(f"Amount: ${amount:,.2f}")
        if result:
            print(f"  Module: {result['module']}")
            print(f"  GL Code: {result['gl_code']}")
            print(f"  Match Type: {result['match_type']}")
            print(f"  Confidence: {result['confidence']:.0%}")
        else:
            print("  No match found")
    
    print(f"\n{'='*70}")
    print("Statistics:")
    print(matcher.get_statistics())
