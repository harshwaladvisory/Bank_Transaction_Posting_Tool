"""
Vendor Matcher Module - Match transactions against vendor master list
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR

class VendorMatcher:
    """Match transaction descriptions against vendor master list"""
    
    def __init__(self):
        self.vendors = self._load_vendors()
        self.vendor_aliases = self._build_aliases()
        
    def _load_vendors(self) -> List[Dict]:
        """Load vendor master list from file"""
        vendors_file = os.path.join(DATA_DIR, 'vendors.json')
        
        if os.path.exists(vendors_file):
            with open(vendors_file, 'r') as f:
                return json.load(f)
        
        # Return sample vendors if file not found
        return self._get_sample_vendors()
    
    def _get_sample_vendors(self) -> List[Dict]:
        """Sample vendor data for demonstration"""
        return [
            # Payroll Vendors
            {"name": "ADP", "aliases": ["adp payroll", "adp fees", "adp tax"], "category": "payroll", "gl_code": "7200", "fund_code": "2700"},
            {"name": "Paychex", "aliases": ["paychex payroll", "paychex fees"], "category": "payroll", "gl_code": "7200", "fund_code": "2700"},
            {"name": "Gusto", "aliases": ["gusto payroll", "gusto fees"], "category": "payroll", "gl_code": "7200", "fund_code": "2700"},
            {"name": "Intuit Payroll", "aliases": ["intuit", "quickbooks payroll"], "category": "payroll", "gl_code": "7200", "fund_code": "2700"},
            
            # Tax Agencies
            {"name": "IRS", "aliases": ["irs eftps", "internal revenue", "federal tax"], "category": "tax", "gl_code": "7400", "fund_code": "2700"},
            {"name": "State Tax Board", "aliases": ["state tax", "franchise tax", "edd"], "category": "tax", "gl_code": "7410", "fund_code": "2700"},
            
            # Utilities
            {"name": "Electric Company", "aliases": ["electric", "power", "energy", "edison", "pge", "duke energy"], "category": "utilities", "gl_code": "7310", "fund_code": "1000"},
            {"name": "Gas Company", "aliases": ["gas", "natural gas", "socal gas"], "category": "utilities", "gl_code": "7310", "fund_code": "1000"},
            {"name": "Water District", "aliases": ["water", "water district", "sewer"], "category": "utilities", "gl_code": "7310", "fund_code": "1000"},
            {"name": "AT&T", "aliases": ["at&t", "att", "at and t"], "category": "utilities", "gl_code": "7310", "fund_code": "1000"},
            {"name": "Verizon", "aliases": ["verizon", "vzw"], "category": "utilities", "gl_code": "7310", "fund_code": "1000"},
            {"name": "Comcast", "aliases": ["comcast", "xfinity"], "category": "utilities", "gl_code": "7310", "fund_code": "1000"},
            
            # Insurance
            {"name": "Aetna", "aliases": ["aetna", "aetna health"], "category": "insurance", "gl_code": "7700", "fund_code": "1000"},
            {"name": "Blue Cross", "aliases": ["blue cross", "bcbs", "anthem"], "category": "insurance", "gl_code": "7700", "fund_code": "1000"},
            {"name": "United Healthcare", "aliases": ["united health", "uhc", "optum"], "category": "insurance", "gl_code": "7700", "fund_code": "1000"},
            {"name": "State Farm", "aliases": ["state farm"], "category": "insurance", "gl_code": "7700", "fund_code": "1000"},
            
            # Office Supplies
            {"name": "Staples", "aliases": ["staples"], "category": "office_supplies", "gl_code": "7320", "fund_code": "1000"},
            {"name": "Office Depot", "aliases": ["office depot", "officemax"], "category": "office_supplies", "gl_code": "7320", "fund_code": "1000"},
            {"name": "Amazon", "aliases": ["amazon", "amzn", "aws"], "category": "office_supplies", "gl_code": "7320", "fund_code": "1000"},
            
            # Professional Services
            {"name": "Legal Services", "aliases": ["law firm", "attorney", "legal", "llp", "pllc"], "category": "professional_fees", "gl_code": "7600", "fund_code": "1000"},
            {"name": "Accounting Services", "aliases": ["cpa", "accountant", "accounting", "audit"], "category": "professional_fees", "gl_code": "7600", "fund_code": "1000"},
            
            # Software/Subscriptions
            {"name": "Microsoft", "aliases": ["microsoft", "msft", "office 365", "azure"], "category": "software", "gl_code": "7320", "fund_code": "1000"},
            {"name": "Google", "aliases": ["google", "google workspace", "gcp"], "category": "software", "gl_code": "7320", "fund_code": "1000"},
            {"name": "Adobe", "aliases": ["adobe", "creative cloud"], "category": "software", "gl_code": "7320", "fund_code": "1000"},
            {"name": "Salesforce", "aliases": ["salesforce", "sfdc"], "category": "software", "gl_code": "7320", "fund_code": "1000"},
            {"name": "Zoom", "aliases": ["zoom", "zoom video"], "category": "software", "gl_code": "7320", "fund_code": "1000"},
            
            # Travel
            {"name": "Airlines", "aliases": ["airline", "united", "delta", "american", "southwest", "jetblue"], "category": "travel", "gl_code": "7800", "fund_code": "1000"},
            {"name": "Hotels", "aliases": ["marriott", "hilton", "hyatt", "hotel", "lodging"], "category": "travel", "gl_code": "7800", "fund_code": "1000"},
            {"name": "Uber", "aliases": ["uber"], "category": "travel", "gl_code": "7800", "fund_code": "1000"},
            {"name": "Lyft", "aliases": ["lyft"], "category": "travel", "gl_code": "7800", "fund_code": "1000"},
            
            # Shipping
            {"name": "FedEx", "aliases": ["fedex", "federal express"], "category": "shipping", "gl_code": "7330", "fund_code": "1000"},
            {"name": "UPS", "aliases": ["ups", "united parcel"], "category": "shipping", "gl_code": "7330", "fund_code": "1000"},
            {"name": "USPS", "aliases": ["usps", "postal service", "postage"], "category": "shipping", "gl_code": "7330", "fund_code": "1000"},
            
            # Banks
            {"name": "Bank of America", "aliases": ["bank of america", "bofa", "boa"], "category": "bank", "gl_code": "7500", "fund_code": "1000"},
            {"name": "Wells Fargo", "aliases": ["wells fargo", "wf"], "category": "bank", "gl_code": "7500", "fund_code": "1000"},
            {"name": "Chase", "aliases": ["chase", "jpmorgan"], "category": "bank", "gl_code": "7500", "fund_code": "1000"},
            {"name": "PNC", "aliases": ["pnc", "pnc bank"], "category": "bank", "gl_code": "7500", "fund_code": "1000"}
        ]
    
    def _build_aliases(self) -> Dict[str, Dict]:
        """Build a lookup dictionary from aliases to vendor info"""
        aliases = {}
        for vendor in self.vendors:
            # Add main name
            aliases[vendor['name'].lower()] = vendor
            # Add all aliases
            for alias in vendor.get('aliases', []):
                aliases[alias.lower()] = vendor
        return aliases
    
    def match(self, description: str) -> Optional[Dict]:
        """
        Match a transaction description to a vendor
        
        Args:
            description: Transaction description
            
        Returns:
            Matched vendor info or None
        """
        description_lower = description.lower()
        
        # First try exact alias match
        for alias, vendor in self.vendor_aliases.items():
            if alias in description_lower:
                return {
                    'vendor_name': vendor['name'],
                    'category': vendor['category'],
                    'gl_code': vendor.get('gl_code'),
                    'fund_code': vendor.get('fund_code'),
                    'match_type': 'exact',
                    'confidence': 0.95
                }
        
        # Try fuzzy matching
        best_match = None
        best_score = 0
        
        for vendor in self.vendors:
            # Check against vendor name
            score = self._fuzzy_match(description_lower, vendor['name'].lower())
            if score > best_score and score > 0.7:
                best_score = score
                best_match = vendor
            
            # Check against aliases
            for alias in vendor.get('aliases', []):
                score = self._fuzzy_match(description_lower, alias.lower())
                if score > best_score and score > 0.7:
                    best_score = score
                    best_match = vendor
        
        if best_match:
            return {
                'vendor_name': best_match['name'],
                'category': best_match['category'],
                'gl_code': best_match.get('gl_code'),
                'fund_code': best_match.get('fund_code'),
                'match_type': 'fuzzy',
                'confidence': best_score
            }
        
        return None
    
    def _fuzzy_match(self, text: str, pattern: str) -> float:
        """Calculate fuzzy match score between text and pattern"""
        # Check if pattern is contained in text
        if pattern in text:
            return 0.9
        
        # Check word-by-word
        pattern_words = pattern.split()
        text_words = text.split()
        
        matches = 0
        for pw in pattern_words:
            for tw in text_words:
                if SequenceMatcher(None, pw, tw).ratio() > 0.8:
                    matches += 1
                    break
        
        if pattern_words:
            return matches / len(pattern_words)
        return 0
    
    def add_vendor(self, name: str, aliases: List[str] = None, category: str = None,
                   gl_code: str = None, fund_code: str = None):
        """Add a new vendor to the list"""
        vendor = {
            'name': name,
            'aliases': aliases or [],
            'category': category or 'other',
            'gl_code': gl_code,
            'fund_code': fund_code
        }
        self.vendors.append(vendor)
        self._build_aliases()
    
    def load_from_file(self, file_path: str):
        """Load vendors from an external file (Excel/CSV)"""
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Expected columns: name, aliases (comma-separated), category, gl_code, fund_code
            for _, row in df.iterrows():
                aliases = []
                if 'aliases' in row and pd.notna(row['aliases']):
                    aliases = [a.strip() for a in str(row['aliases']).split(',')]
                
                self.add_vendor(
                    name=row.get('name', ''),
                    aliases=aliases,
                    category=row.get('category', 'other'),
                    gl_code=str(row.get('gl_code', '')) if pd.notna(row.get('gl_code')) else None,
                    fund_code=str(row.get('fund_code', '')) if pd.notna(row.get('fund_code')) else None
                )
                
        except Exception as e:
            print(f"Error loading vendors from file: {e}")
    
    def save_vendors(self):
        """Save vendors to JSON file"""
        vendors_file = os.path.join(DATA_DIR, 'vendors.json')
        with open(vendors_file, 'w') as f:
            json.dump(self.vendors, f, indent=2)
    
    def get_all_vendors(self) -> List[Dict]:
        """Get all vendors"""
        return self.vendors


# Standalone test
if __name__ == "__main__":
    matcher = VendorMatcher()
    
    test_descriptions = [
        "ACH Debit ADP Payroll Fees 925735495357",
        "Wire to Staples Office Supplies",
        "Check #1234 - AT&T Monthly Service",
        "IRS EFTPS Tax Payment Q4",
        "Amazon Web Services Invoice",
        "United Airlines Ticket Purchase",
        "Unknown Vendor Payment XYZ"
    ]
    
    print(f"\n{'='*70}")
    print("Vendor Matcher Test Results")
    print(f"{'='*70}")
    
    for desc in test_descriptions:
        result = matcher.match(desc)
        print(f"\nDescription: {desc}")
        if result:
            print(f"  Vendor: {result['vendor_name']}")
            print(f"  Category: {result['category']}")
            print(f"  GL Code: {result['gl_code']}")
            print(f"  Match Type: {result['match_type']} ({result['confidence']:.0%})")
        else:
            print("  No vendor match found")
