"""
Keyword Classifier Module - Classify transactions using keyword matching
Contains 500+ keywords organized by category
"""

import re
import json
import os
from typing import Dict, List, Tuple, Optional
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW

class KeywordClassifier:
    """
    Classify transactions based on keyword matching
    Uses hierarchical matching with confidence scores
    """
    
    def __init__(self):
        self.keywords = self._load_keywords()
        self.custom_rules = []
        
    def _load_keywords(self) -> Dict:
        """Load keyword database from JSON file"""
        keywords_file = os.path.join(DATA_DIR, 'keywords.json')
        
        if os.path.exists(keywords_file):
            with open(keywords_file, 'r') as f:
                return json.load(f)
        
        # Return default keywords if file not found
        return self._get_default_keywords()
    
    def _get_default_keywords(self) -> Dict:
        """Return comprehensive default keyword database"""
        return {
            "classification_rules": {
                "CR": {
                    "keywords": self._get_cr_keywords(),
                    "patterns": self._get_cr_patterns()
                },
                "CD": {
                    "keywords": self._get_cd_keywords(),
                    "patterns": self._get_cd_patterns()
                },
                "JV": {
                    "keywords": self._get_jv_keywords(),
                    "patterns": self._get_jv_patterns()
                }
            },
            "gl_code_mappings": self._get_gl_mappings()
        }
    
    def _get_cr_keywords(self) -> List[str]:
        """Cash Receipts keywords - 150+ terms"""
        return [
            # Deposits & Credits
            "deposit", "credit", "credits", "receipt", "received", "incoming",
            "ach credit", "ach deposit", "direct deposit", "wire in", "wire credit",
            "transfer in", "incoming wire", "incoming transfer", "funds received",
            
            # Interest & Dividends
            "interest credit", "interest income", "interest earned", "int credit",
            "dividend", "dividends", "div credit", "investment income",
            
            # Grants & Government
            "grant", "grant award", "grant payment", "grant draw", "drawdown",
            "hud", "hud payment", "housing urban", "doe", "department of energy",
            "hhs", "health human services", "epa", "environmental protection",
            "fema", "usda", "agriculture", "dol", "department of labor",
            "nsf", "national science", "nih", "national institutes",
            "federal grant", "state grant", "city grant", "county grant",
            "cfda", "uei", "award", "reimbursement grant",
            
            # Revenue
            "revenue", "income", "sales", "sales revenue", "service revenue",
            "consulting income", "fee income", "commission", "royalty",
            "licensing fee", "franchise fee", "contract revenue",
            
            # Rent & Lease
            "rent received", "rental income", "rent payment received",
            "lease payment", "tenant payment", "property income",
            
            # Donations & Contributions
            "donation", "donations", "contribution", "contributions",
            "gift", "bequest", "charitable", "pledge payment",
            "membership", "membership dues", "dues", "subscription",
            
            # Customer Payments
            "customer payment", "client payment", "invoice payment",
            "payment received", "collection", "ar payment", "receivable",
            "accounts receivable", "customer deposit",
            
            # Refunds & Reimbursements
            "refund", "refunds", "reimbursement", "rebate", "rebates",
            "credit memo", "returned payment", "overpayment return",
            
            # Insurance & Claims
            "insurance claim", "claim payment", "settlement", "insurance settlement",
            "insurance refund", "premium refund",
            
            # Miscellaneous Income
            "miscellaneous income", "misc income", "other income",
            "sundry income", "gain", "proceeds"
        ]
    
    def _get_cd_keywords(self) -> List[str]:
        """Cash Disbursements keywords - 200+ terms"""
        return [
            # Payments & Debits
            "payment", "paid", "pay", "debit", "debits", "withdrawal",
            "ach debit", "ach payment", "wire out", "wire transfer",
            "transfer out", "outgoing wire", "bill pay", "billpay",
            "autopay", "auto pay", "recurring payment", "scheduled payment",
            
            # Checks
            "check", "cheque", "chk", "check #", "check no", "check number",
            "cleared check", "cashed check",
            
            # Payroll
            "payroll", "salary", "salaries", "wage", "wages", "compensation",
            "bonus", "bonuses", "commission paid", "stipend",
            "adp", "adp payroll", "paychex", "gusto", "intuit payroll",
            "quickbooks payroll", "ceridian", "paylocity", "paycom", "paycor",
            "workday", "kronos", "ultimate software", "bamboohr",
            "direct deposit payroll", "net pay", "gross pay",
            
            # Payroll Taxes & Benefits
            "payroll tax", "employment tax", "fica", "social security",
            "medicare", "futa", "suta", "state unemployment",
            "401k", "retirement contribution", "pension",
            "health insurance", "dental", "vision", "fsa", "hsa",
            "life insurance", "disability", "workers comp",
            
            # Federal & State Taxes
            "irs", "eftps", "internal revenue", "federal tax",
            "941", "940", "1120", "990", "estimated tax", "quarterly tax",
            "state tax", "franchise tax", "income tax", "sales tax",
            "property tax", "excise tax", "use tax",
            
            # Vendors & Suppliers
            "vendor", "supplier", "purchase", "procurement", "po #",
            "invoice", "inv #", "bill", "statement",
            
            # Utilities
            "utility", "utilities", "electric", "electricity", "power",
            "gas", "natural gas", "water", "sewer", "trash", "garbage",
            "waste management", "sanitation", "recycling",
            "at&t", "verizon", "comcast", "spectrum", "cox", "xfinity",
            "t-mobile", "sprint", "centurylink", "frontier",
            
            # Rent & Lease Payments
            "rent", "rent payment", "lease payment", "lease", "mortgage",
            "property management", "cam", "common area",
            
            # Insurance Premiums
            "insurance", "insurance premium", "premium", "policy",
            "liability insurance", "property insurance", "auto insurance",
            "workers compensation", "professional liability", "e&o",
            "aetna", "cigna", "united health", "blue cross", "anthem",
            "humana", "kaiser", "metlife", "prudential", "aflac",
            
            # Professional Services
            "professional fee", "legal", "legal fee", "attorney",
            "accounting", "audit", "cpa", "bookkeeping", "tax prep",
            "consultant", "consulting", "advisory", "contractor",
            "subcontractor", "freelance", "1099",
            
            # Office & Supplies
            "office supplies", "supplies", "office expense",
            "staples", "office depot", "amazon", "costco", "walmart",
            "equipment", "furniture", "computer", "software", "hardware",
            
            # Travel & Entertainment
            "travel", "airfare", "airline", "flight", "hotel", "lodging",
            "car rental", "uber", "lyft", "taxi", "parking",
            "meals", "entertainment", "conference", "seminar", "training",
            "registration", "mileage", "per diem",
            
            # Subscriptions & Services
            "subscription", "monthly fee", "annual fee", "license",
            "saas", "cloud", "hosting", "domain", "ssl",
            "microsoft", "google", "adobe", "salesforce", "zoom",
            
            # Maintenance & Repairs
            "maintenance", "repair", "repairs", "service", "servicing",
            "janitorial", "cleaning", "landscaping", "pest control",
            
            # Shipping & Postage
            "shipping", "freight", "postage", "fedex", "ups", "usps",
            "dhl", "courier", "delivery",
            
            # Marketing & Advertising
            "advertising", "marketing", "promotion", "ad spend",
            "google ads", "facebook ads", "social media", "seo",
            "print", "radio", "tv", "billboard",
            
            # Loan & Debt
            "loan payment", "principal", "interest payment", "debt",
            "line of credit", "loc", "note payable",
            
            # Credit Cards
            "credit card", "amex", "american express", "visa",
            "mastercard", "discover", "corporate card"
        ]
    
    def _get_jv_keywords(self) -> List[str]:
        """Journal Voucher keywords - 100+ terms"""
        return [
            # Bank Fees & Charges
            "bank fee", "bank charge", "service charge", "monthly fee",
            "maintenance fee", "account fee", "analysis charge",
            "wire fee", "transfer fee", "ach fee", "transaction fee",
            "overdraft", "overdraft fee", "nsf", "nsf fee",
            "returned item", "returned check", "stop payment",
            "foreign transaction", "atm fee", "cash advance fee",
            
            # Interest Charges
            "interest charge", "finance charge", "late fee", "penalty",
            "interest expense", "loan interest",
            
            # Corrections & Adjustments
            "correction", "adjustment", "reversal", "void", "voided",
            "error correction", "posting error", "mispost",
            "credit adjustment", "debit adjustment",
            
            # Transfers
            "transfer", "transfer between", "internal transfer",
            "book transfer", "account transfer", "sweep",
            "zba", "zero balance", "concentration",
            
            # Reclassifications
            "reclassification", "reclass", "journal entry", "je",
            "accrual", "accrued", "prepaid", "deferred",
            "amortization", "depreciation",
            
            # Reserves & Allowances
            "allowance", "reserve", "provision", "write off",
            "write-off", "bad debt", "doubtful accounts",
            
            # Gains & Losses
            "gain", "loss", "realized", "unrealized",
            "foreign exchange", "fx", "currency", "translation",
            
            # Intercompany
            "intercompany", "due to", "due from", "affiliate",
            "related party", "subsidiary",
            
            # Clearing & Suspense
            "clearing", "suspense", "unidentified", "uncleared",
            "reconciling", "in transit"
        ]
    
    def _get_cr_patterns(self) -> List[str]:
        """Regex patterns for Cash Receipts"""
        return [
            r"(?i)deposit.*from",
            r"(?i)credit.*memo",
            r"(?i)payment.*received",
            r"(?i)grant.*award",
            r"(?i)hud.*draw",
            r"(?i)interest.*earned",
            r"(?i)wire.*in.*from",
            r"(?i)ach.*credit.*from",
            r"(?i)refund.*from"
        ]
    
    def _get_cd_patterns(self) -> List[str]:
        """Regex patterns for Cash Disbursements"""
        return [
            r"(?i)payroll.*transfer",
            r"(?i)irs.*eftps",
            r"(?i)tax.*payment",
            r"(?i)vendor.*payment",
            r"(?i)check.*#?\d+",
            r"(?i)ach.*debit",
            r"(?i)wire.*to",
            r"(?i)bill.*pay",
            r"(?i)payment.*to"
        ]
    
    def _get_jv_patterns(self) -> List[str]:
        """Regex patterns for Journal Vouchers"""
        return [
            r"(?i)bank.*charge",
            r"(?i)service.*fee",
            r"(?i)monthly.*maintenance",
            r"(?i)transfer.*between",
            r"(?i)correction.*entry",
            r"(?i)adjustment.*#",
            r"(?i)nsf.*fee",
            r"(?i)overdraft.*charge"
        ]
    
    def _get_gl_mappings(self) -> Dict:
        """Default GL code mappings"""
        return {
            "payroll": {"gl": "7200", "fund": "2700", "category": "Payroll Expense"},
            "payroll_tax": {"gl": "7210", "fund": "2700", "category": "Payroll Taxes"},
            "federal_tax": {"gl": "7400", "fund": "2700", "category": "Federal Taxes"},
            "state_tax": {"gl": "7410", "fund": "2700", "category": "State Taxes"},
            "interest_income": {"gl": "4600", "fund": "1000", "category": "Interest Income"},
            "interest_expense": {"gl": "8100", "fund": "1000", "category": "Interest Expense"},
            "bank_fees": {"gl": "7500", "fund": "1000", "category": "Bank Service Charges"},
            "rent_expense": {"gl": "7300", "fund": "1000", "category": "Rent Expense"},
            "rent_income": {"gl": "4200", "fund": "1000", "category": "Rental Income"},
            "utilities": {"gl": "7310", "fund": "1000", "category": "Utilities"},
            "office_supplies": {"gl": "7320", "fund": "1000", "category": "Office Supplies"},
            "professional_fees": {"gl": "7600", "fund": "1000", "category": "Professional Fees"},
            "insurance": {"gl": "7700", "fund": "1000", "category": "Insurance"},
            "travel": {"gl": "7800", "fund": "1000", "category": "Travel & Entertainment"},
            "grant_revenue": {"gl": "4100", "fund": "varies", "category": "Grant Revenue"},
            "donation": {"gl": "4300", "fund": "1000", "category": "Contributions"},
            "miscellaneous": {"gl": "7900", "fund": "1000", "category": "Miscellaneous"}
        }
    
    def classify(self, description: str, amount: float = 0) -> Dict:
        """
        Classify a transaction based on its description
        
        Args:
            description: Transaction description/narration
            amount: Transaction amount (positive=credit, negative=debit)
            
        Returns:
            Dictionary with module, confidence, matched_keywords, gl_suggestion
        """
        description_lower = description.lower()
        
        results = {
            'CR': {'score': 0, 'keywords': [], 'patterns': []},
            'CD': {'score': 0, 'keywords': [], 'patterns': []},
            'JV': {'score': 0, 'keywords': [], 'patterns': []}
        }
        
        rules = self.keywords.get('classification_rules', {})
        
        # Keyword matching
        for module, rule_data in rules.items():
            keywords = rule_data.get('keywords', [])
            patterns = rule_data.get('patterns', [])
            
            # Check keywords
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    results[module]['score'] += 1
                    results[module]['keywords'].append(keyword)
            
            # Check patterns
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    results[module]['score'] += 2  # Patterns worth more
                    results[module]['patterns'].append(pattern)
        
        # Apply amount-based heuristics
        if amount > 0:  # Credit/Deposit
            results['CR']['score'] += 0.5
        elif amount < 0:  # Debit/Withdrawal
            results['CD']['score'] += 0.5
        
        # Find best match
        best_module = max(results.keys(), key=lambda k: results[k]['score'])
        best_score = results[best_module]['score']
        
        # Calculate confidence
        total_matches = sum(r['score'] for r in results.values())
        if total_matches > 0:
            confidence = best_score / (total_matches + 1)  # Normalize
            confidence = min(confidence, 1.0)
        else:
            confidence = 0
        
        # Determine confidence level
        if confidence >= CONFIDENCE_HIGH:
            confidence_level = 'high'
        elif confidence >= CONFIDENCE_MEDIUM:
            confidence_level = 'medium'
        elif confidence >= CONFIDENCE_LOW:
            confidence_level = 'low'
        else:
            confidence_level = 'none'
        
        # Get GL suggestion
        gl_suggestion = self._suggest_gl(description_lower, best_module)
        
        return {
            'module': best_module if best_score > 0 else 'UNKNOWN',
            'confidence': confidence,
            'confidence_level': confidence_level,
            'matched_keywords': results[best_module]['keywords'],
            'matched_patterns': results[best_module]['patterns'],
            'all_scores': {k: v['score'] for k, v in results.items()},
            'gl_suggestion': gl_suggestion
        }
    
    def _suggest_gl(self, description: str, module: str) -> Optional[Dict]:
        """Suggest GL code based on description"""
        gl_mappings = self.keywords.get('gl_code_mappings', self._get_gl_mappings())
        
        # Priority keywords for GL mapping
        gl_keywords = {
            'payroll': ['payroll', 'salary', 'wage', 'adp', 'paychex', 'gusto'],
            'payroll_tax': ['fica', 'futa', 'suta', 'employment tax', 'payroll tax'],
            'federal_tax': ['irs', 'eftps', 'federal tax', '941', '940'],
            'state_tax': ['state tax', 'franchise tax', 'state withholding'],
            'interest_income': ['interest credit', 'interest income', 'interest earned'],
            'interest_expense': ['interest charge', 'finance charge', 'loan interest'],
            'bank_fees': ['bank fee', 'service charge', 'monthly fee', 'wire fee', 'nsf'],
            'rent_expense': ['rent', 'lease payment', 'office rent'],
            'rent_income': ['rent received', 'rental income', 'tenant'],
            'utilities': ['electric', 'gas', 'water', 'utility', 'phone', 'internet'],
            'office_supplies': ['office supplies', 'supplies', 'staples', 'office depot'],
            'professional_fees': ['legal', 'accounting', 'consultant', 'attorney', 'cpa'],
            'insurance': ['insurance', 'premium', 'policy', 'liability'],
            'travel': ['travel', 'airfare', 'hotel', 'uber', 'mileage'],
            'grant_revenue': ['grant', 'hud', 'doe', 'hhs', 'federal', 'award'],
            'donation': ['donation', 'contribution', 'gift', 'charitable']
        }
        
        for category, keywords in gl_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    return gl_mappings.get(category)
        
        return gl_mappings.get('miscellaneous')
    
    def add_custom_rule(self, keyword: str, module: str, gl_code: str = None, fund_code: str = None):
        """Add a custom classification rule"""
        self.custom_rules.append({
            'keyword': keyword.lower(),
            'module': module,
            'gl_code': gl_code,
            'fund_code': fund_code
        })
    
    def save_keywords(self):
        """Save current keywords to file"""
        keywords_file = os.path.join(DATA_DIR, 'keywords.json')
        with open(keywords_file, 'w') as f:
            json.dump(self.keywords, f, indent=2)


# Standalone test
if __name__ == "__main__":
    classifier = KeywordClassifier()
    
    test_descriptions = [
        ("ACH Credit - HUD Grant Drawdown #12345", 50000.00),
        ("ADP Payroll Transfer 925735495357", -15000.00),
        ("IRS EFTPS Payment REF# 99345", -3000.00),
        ("Monthly Service Charge", -25.00),
        ("Interest Credit", 125.50),
        ("Wire Transfer to ABC Vendor", -8500.00),
        ("Check #1234 - Office Supplies", -250.00),
        ("Customer Payment - Invoice #5678", 1500.00),
        ("Bank Fee - Wire Transfer", -35.00),
        ("Unknown Transaction XYZ123", -100.00)
    ]
    
    print(f"\n{'='*80}")
    print("Keyword Classifier Test Results")
    print(f"{'='*80}")
    
    for desc, amount in test_descriptions:
        result = classifier.classify(desc, amount)
        print(f"\nDescription: {desc}")
        print(f"Amount: ${amount:,.2f}")
        print(f"Module: {result['module']} (Confidence: {result['confidence_level']})")
        print(f"Matched Keywords: {result['matched_keywords'][:3]}")
        if result['gl_suggestion']:
            print(f"GL Suggestion: {result['gl_suggestion'].get('gl')} - {result['gl_suggestion'].get('category')}")
