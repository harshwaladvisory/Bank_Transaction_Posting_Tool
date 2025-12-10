"""
Customer/Grant Matcher Module - Match transactions against customer and grant lists
Used for Cash Receipts classification
"""

import json
import os
import re
from typing import Dict, List, Optional
from difflib import SequenceMatcher
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR

class CustomerMatcher:
    """Match transaction descriptions against customer and grant lists"""
    
    def __init__(self):
        self.customers = self._load_customers()
        self.grants = self._load_grants()
        
    def _load_customers(self) -> List[Dict]:
        """Load customer list from file"""
        customers_file = os.path.join(DATA_DIR, 'customers.json')
        
        if os.path.exists(customers_file):
            with open(customers_file, 'r') as f:
                return json.load(f)
        
        return self._get_sample_customers()
    
    def _load_grants(self) -> List[Dict]:
        """Load grant list from file"""
        grants_file = os.path.join(DATA_DIR, 'grants.json')
        
        if os.path.exists(grants_file):
            with open(grants_file, 'r') as f:
                return json.load(f)
        
        return self._get_sample_grants()
    
    def _get_sample_customers(self) -> List[Dict]:
        """Sample customer data"""
        return [
            {"name": "ABC Corporation", "aliases": ["abc corp", "abc"], "type": "customer", "gl_code": "4000", "fund_code": "1000"},
            {"name": "XYZ Industries", "aliases": ["xyz ind", "xyz"], "type": "customer", "gl_code": "4000", "fund_code": "1000"},
            {"name": "Smith & Associates", "aliases": ["smith assoc", "smith"], "type": "customer", "gl_code": "4000", "fund_code": "1000"},
            {"name": "Johnson Holdings", "aliases": ["johnson", "jh"], "type": "customer", "gl_code": "4000", "fund_code": "1000"},
            {"name": "Metro Properties", "aliases": ["metro prop", "metro"], "type": "tenant", "gl_code": "4200", "fund_code": "1000"},
            {"name": "Downtown Retail", "aliases": ["downtown", "dtr"], "type": "tenant", "gl_code": "4200", "fund_code": "1000"}
        ]
    
    def _get_sample_grants(self) -> List[Dict]:
        """Sample grant data - Federal agencies and grant programs"""
        return [
            # HUD Programs
            {"name": "HUD CDBG", "aliases": ["hud", "cdbg", "community development", "block grant"], 
             "agency": "HUD", "cfda": "14.218", "gl_code": "4100", "fund_code": "2700"},
            {"name": "HUD HOME", "aliases": ["home program", "home investment"], 
             "agency": "HUD", "cfda": "14.239", "gl_code": "4100", "fund_code": "2710"},
            {"name": "HUD Section 8", "aliases": ["section 8", "housing choice", "hcv"], 
             "agency": "HUD", "cfda": "14.871", "gl_code": "4100", "fund_code": "2720"},
            {"name": "HUD CoC", "aliases": ["continuum of care", "coc", "homeless"], 
             "agency": "HUD", "cfda": "14.267", "gl_code": "4100", "fund_code": "2730"},
            
            # DOE Programs
            {"name": "DOE Weatherization", "aliases": ["doe", "weatherization", "wap", "energy"], 
             "agency": "DOE", "cfda": "81.042", "gl_code": "4100", "fund_code": "2800"},
            {"name": "DOE LIHEAP", "aliases": ["liheap", "heating assistance", "energy assistance"], 
             "agency": "DOE", "cfda": "93.568", "gl_code": "4100", "fund_code": "2810"},
            
            # HHS Programs
            {"name": "HHS Head Start", "aliases": ["head start", "early head start", "hhs"], 
             "agency": "HHS", "cfda": "93.600", "gl_code": "4100", "fund_code": "2900"},
            {"name": "HHS TANF", "aliases": ["tanf", "temporary assistance", "welfare"], 
             "agency": "HHS", "cfda": "93.558", "gl_code": "4100", "fund_code": "2910"},
            {"name": "HHS CSBG", "aliases": ["csbg", "community services"], 
             "agency": "HHS", "cfda": "93.569", "gl_code": "4100", "fund_code": "2920"},
            
            # FEMA Programs
            {"name": "FEMA Emergency Management", "aliases": ["fema", "emergency management", "empg"], 
             "agency": "FEMA", "cfda": "97.042", "gl_code": "4100", "fund_code": "3000"},
            
            # USDA Programs
            {"name": "USDA SNAP", "aliases": ["snap", "food stamps", "usda"], 
             "agency": "USDA", "cfda": "10.551", "gl_code": "4100", "fund_code": "3100"},
            
            # DOL Programs
            {"name": "DOL WIOA", "aliases": ["wioa", "workforce", "job training", "dol"], 
             "agency": "DOL", "cfda": "17.258", "gl_code": "4100", "fund_code": "3200"},
            
            # EPA Programs
            {"name": "EPA Clean Water", "aliases": ["epa", "clean water", "cwsrf"], 
             "agency": "EPA", "cfda": "66.458", "gl_code": "4100", "fund_code": "3300"},
            
            # Treasury
            {"name": "Treasury ARPA", "aliases": ["arpa", "american rescue", "slfrf", "treasury"], 
             "agency": "Treasury", "cfda": "21.027", "gl_code": "4100", "fund_code": "3400"},
            
            # State Programs
            {"name": "State Grant", "aliases": ["state", "state grant", "state funding"], 
             "agency": "State", "gl_code": "4100", "fund_code": "4000"},
            
            # Local Programs
            {"name": "City Grant", "aliases": ["city", "municipal", "local"], 
             "agency": "Local", "gl_code": "4100", "fund_code": "4100"},
            {"name": "County Grant", "aliases": ["county", "county grant"], 
             "agency": "Local", "gl_code": "4100", "fund_code": "4100"}
        ]
    
    def match_customer(self, description: str) -> Optional[Dict]:
        """Match description against customer list"""
        description_lower = description.lower()
        
        for customer in self.customers:
            # Check main name
            if customer['name'].lower() in description_lower:
                return {
                    'name': customer['name'],
                    'type': customer.get('type', 'customer'),
                    'gl_code': customer.get('gl_code'),
                    'fund_code': customer.get('fund_code'),
                    'match_type': 'exact',
                    'confidence': 0.95
                }
            
            # Check aliases
            for alias in customer.get('aliases', []):
                if alias.lower() in description_lower:
                    return {
                        'name': customer['name'],
                        'type': customer.get('type', 'customer'),
                        'gl_code': customer.get('gl_code'),
                        'fund_code': customer.get('fund_code'),
                        'match_type': 'alias',
                        'confidence': 0.90
                    }
        
        return None
    
    def match_grant(self, description: str) -> Optional[Dict]:
        """Match description against grant list"""
        description_lower = description.lower()
        
        for grant in self.grants:
            # Check main name
            if grant['name'].lower() in description_lower:
                return {
                    'name': grant['name'],
                    'agency': grant.get('agency'),
                    'cfda': grant.get('cfda'),
                    'gl_code': grant.get('gl_code'),
                    'fund_code': grant.get('fund_code'),
                    'match_type': 'exact',
                    'confidence': 0.95
                }
            
            # Check aliases
            for alias in grant.get('aliases', []):
                if alias.lower() in description_lower:
                    return {
                        'name': grant['name'],
                        'agency': grant.get('agency'),
                        'cfda': grant.get('cfda'),
                        'gl_code': grant.get('gl_code'),
                        'fund_code': grant.get('fund_code'),
                        'match_type': 'alias',
                        'confidence': 0.90
                    }
        
        return None
    
    def match(self, description: str) -> Optional[Dict]:
        """
        Match description against both customer and grant lists
        Returns the best match
        """
        # Try grant match first (usually more specific)
        grant_match = self.match_grant(description)
        if grant_match:
            grant_match['source'] = 'grant'
            return grant_match
        
        # Try customer match
        customer_match = self.match_customer(description)
        if customer_match:
            customer_match['source'] = 'customer'
            return customer_match
        
        return None
    
    def add_customer(self, name: str, aliases: List[str] = None, 
                     customer_type: str = 'customer', gl_code: str = None, fund_code: str = None):
        """Add a new customer"""
        customer = {
            'name': name,
            'aliases': aliases or [],
            'type': customer_type,
            'gl_code': gl_code,
            'fund_code': fund_code
        }
        self.customers.append(customer)
    
    def add_grant(self, name: str, aliases: List[str] = None, agency: str = None,
                  cfda: str = None, gl_code: str = None, fund_code: str = None):
        """Add a new grant"""
        grant = {
            'name': name,
            'aliases': aliases or [],
            'agency': agency,
            'cfda': cfda,
            'gl_code': gl_code,
            'fund_code': fund_code
        }
        self.grants.append(grant)
    
    def load_customers_from_file(self, file_path: str):
        """Load customers from Excel/CSV file"""
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            for _, row in df.iterrows():
                aliases = []
                if 'aliases' in row and pd.notna(row['aliases']):
                    aliases = [a.strip() for a in str(row['aliases']).split(',')]
                
                self.add_customer(
                    name=str(row.get('name', '')),
                    aliases=aliases,
                    customer_type=str(row.get('type', 'customer')),
                    gl_code=str(row.get('gl_code', '')) if pd.notna(row.get('gl_code')) else None,
                    fund_code=str(row.get('fund_code', '')) if pd.notna(row.get('fund_code')) else None
                )
        except Exception as e:
            print(f"Error loading customers: {e}")
    
    def load_grants_from_file(self, file_path: str):
        """Load grants from Excel/CSV file"""
        try:
            import pandas as pd
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            for _, row in df.iterrows():
                aliases = []
                if 'aliases' in row and pd.notna(row['aliases']):
                    aliases = [a.strip() for a in str(row['aliases']).split(',')]
                
                self.add_grant(
                    name=str(row.get('name', '')),
                    aliases=aliases,
                    agency=str(row.get('agency', '')) if pd.notna(row.get('agency')) else None,
                    cfda=str(row.get('cfda', '')) if pd.notna(row.get('cfda')) else None,
                    gl_code=str(row.get('gl_code', '')) if pd.notna(row.get('gl_code')) else None,
                    fund_code=str(row.get('fund_code', '')) if pd.notna(row.get('fund_code')) else None
                )
        except Exception as e:
            print(f"Error loading grants: {e}")
    
    def save_data(self):
        """Save customers and grants to JSON files"""
        customers_file = os.path.join(DATA_DIR, 'customers.json')
        grants_file = os.path.join(DATA_DIR, 'grants.json')
        
        with open(customers_file, 'w') as f:
            json.dump(self.customers, f, indent=2)
        
        with open(grants_file, 'w') as f:
            json.dump(self.grants, f, indent=2)


# Standalone test
if __name__ == "__main__":
    matcher = CustomerMatcher()
    
    test_descriptions = [
        "ACH Credit HUD CDBG Drawdown #12345",
        "Wire from ABC Corporation - Invoice Payment",
        "DOE Weatherization Grant Payment",
        "Treasury ARPA SLFRF Reimbursement",
        "Metro Properties Rent Payment",
        "State Grant Award FY2024",
        "Unknown Customer Payment"
    ]
    
    print(f"\n{'='*70}")
    print("Customer/Grant Matcher Test Results")
    print(f"{'='*70}")
    
    for desc in test_descriptions:
        result = matcher.match(desc)
        print(f"\nDescription: {desc}")
        if result:
            print(f"  Match: {result['name']}")
            print(f"  Source: {result['source']}")
            if result.get('agency'):
                print(f"  Agency: {result['agency']}")
            if result.get('cfda'):
                print(f"  CFDA: {result['cfda']}")
            print(f"  GL Code: {result.get('gl_code')}")
            print(f"  Fund Code: {result.get('fund_code')}")
            print(f"  Confidence: {result['confidence']:.0%}")
        else:
            print("  No match found")
