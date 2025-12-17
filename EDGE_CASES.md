# Edge Cases Analysis - Bank Transaction Posting Tool

**Expert Analysis: Accounting + Development Perspective**
**Date:** December 17, 2025
**Version:** 2.0

---

## 🚨 CRITICAL ISSUES (Must Fix Before Production)

### 1. **No Duplicate Transaction Detection**
**Risk Level:** 🔴 CRITICAL

**Problem:**
- Re-uploading the same bank statement creates duplicate entries
- No check for same date + amount + description
- Multiple banks with same transfer creates double-posting

**Location:** Missing throughout, no dedup in `app.py` upload flow

**Accounting Impact:**
- Financial statements overstated
- Audit failures
- Reconciliation impossibilities

**Recommendation:**
```python
# Add to app.py before saving transactions
def check_duplicates(new_transactions, existing_batch_ids):
    for txn in new_transactions:
        hash_key = f"{txn['date']}_{txn['amount']}_{txn['description']}"
        if db.transactions.find_one({'hash': hash_key, 'batch_id': {'$in': existing_batch_ids}}):
            txn['is_duplicate'] = True
            txn['needs_review'] = True
```

---

### 2. **No Debit/Credit Balance Validation**
**Risk Level:** 🔴 CRITICAL

**Problem:**
- Journal entries never validated for balance (debits = credits)
- GL code lookup failures could create unbalanced entries
- No pre-import validation

**Location:** [entry_builder.py:171-210](entry_builder.py#L171-L210)

**Accounting Impact:**
- Violates fundamental accounting equation
- Trial balance won't balance
- Financial statements incorrect
- Audit failure

**Recommendation:**
```python
# Add to entry_builder.py
def validate_entry(entry):
    debits = sum(line['debit'] for line in entry['lines'])
    credits = sum(line['credit'] for line in entry['lines'])
    if abs(debits - credits) > 0.01:  # Allow 1 cent rounding
        raise ValueError(f"Unbalanced entry: DR={debits} CR={credits}")
```

---

### 3. **Global Session Data = Concurrent User Collision**
**Risk Level:** 🔴 CRITICAL

**Problem:**
- [app.py:46](app.py#L46): Single global `session_data` dictionary
- User A's upload overwrites User B's data
- No session isolation
- No multi-tenancy

**Technical Impact:**
- Data corruption
- User sees wrong transactions
- Lost work

**Recommendation:**
```python
# Use Flask session with unique IDs
from flask import session
import uuid

@app.route('/upload', methods=['POST'])
def upload():
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id

    # Store in MongoDB with session_id
    db.user_sessions.update_one(
        {'session_id': session_id},
        {'$set': {'transactions': transactions, 'updated_at': datetime.now()}},
        upsert=True
    )
```

---

### 4. **MongoDB Permanent Failure Flag**
**Risk Level:** 🔴 CRITICAL

**Problem:**
- [app.py:86](app.py#L86): `_mongo_connection_failed = True` is permanent
- If MongoDB goes down temporarily, app never retries
- Stuck in degraded mode forever until restart

**Technical Impact:**
- Requires manual restart after temporary DB outage
- Data not persisted even after DB recovers

**Recommendation:**
```python
# Add retry mechanism
def get_db():
    global _mongo_client, _mongo_db, _mongo_connection_failed

    # Retry connection every 5 minutes if previously failed
    if _mongo_connection_failed:
        if not hasattr(get_db, 'last_retry') or \
           (datetime.now() - get_db.last_retry).seconds > 300:
            get_db.last_retry = datetime.now()
            _mongo_connection_failed = False  # Allow retry
        else:
            return None

    # ... rest of connection logic
```

---

### 5. **No Period Closing / Historical Modification**
**Risk Level:** 🔴 CRITICAL

**Problem:**
- No fiscal period tracking
- Can post December 2024 transactions in July 2025
- Can modify closed periods
- No audit trail for period locks

**Accounting Impact:**
- Financial statements can change retroactively
- Violates GAAP/audit requirements
- Tax reporting errors
- SEC violations (if applicable)

**Recommendation:**
```python
# Add period closing to MongoDB
db.fiscal_periods.insert_one({
    'year': 2024,
    'period': 12,
    'status': 'closed',
    'closed_by': 'admin@example.com',
    'closed_at': datetime(2025, 1, 15)
})

# Validate before posting
def validate_period(transaction_date):
    period = db.fiscal_periods.find_one({
        'year': transaction_date.year,
        'period': transaction_date.month,
        'status': 'closed'
    })
    if period:
        raise ValueError(f"Period {transaction_date.month}/{transaction_date.year} is closed")
```

---

### 6. **Fund Accounting Not Enforced**
**Risk Level:** 🔴 CRITICAL (for non-profit/government entities)

**Problem:**
- [config.py:43](config.py#L43): All defaults to fund '1000' (general fund)
- No validation of restricted fund usage
- Grant revenue can be posted to unrestricted funds
- Expense GL + Fund combination not validated

**Accounting Impact:**
- Restricted funds misused
- Grant compliance violations
- Audit findings
- Legal liability

**Recommendation:**
```python
# Add fund restrictions table
FUND_RESTRICTIONS = {
    '2100': {  # HUD CDBG fund
        'allowed_gl_codes': ['4100', '7200', '7300'],  # Only housing expenses
        'required_gl_codes': [],
        'type': 'restricted'
    },
    '1000': {  # General fund
        'type': 'unrestricted'
    }
}

def validate_fund_gl_combination(gl_code, fund_code, amount):
    fund = FUND_RESTRICTIONS.get(fund_code)
    if fund and fund['type'] == 'restricted':
        if gl_code not in fund['allowed_gl_codes']:
            raise ValueError(f"GL {gl_code} not allowed in restricted fund {fund_code}")
```

---

## ⚠️ HIGH PRIORITY ISSUES

### 7. **Zero Amount Transactions**
**Risk Level:** 🟠 HIGH

**Problem:**
- [pdf_parser.py:369-410](parsers/pdf_parser.py#L369-L410): Parses and accepts $0.00
- Creates meaningless journal entries
- Clutters reports

**Recommendation:**
```python
# Add validation in classification_engine.py
if abs(transaction['amount']) < 0.01:
    transaction['module'] = 'UNIDENTIFIED'
    transaction['needs_review'] = True
    transaction['review_reason'] = 'Zero or near-zero amount'
```

---

### 8. **Missing Bank Reconciliation**
**Risk Level:** 🟠 HIGH

**Problem:**
- [pdf_parser.py:144,161](parsers/pdf_parser.py#L144): Balance field extracted but never used
- No validation: Beginning + Deposits - Withdrawals = Ending
- No outstanding check tracking
- No deposits in transit

**Accounting Impact:**
- Cannot detect bank errors
- Cannot detect missing transactions
- No reconciliation audit trail

**Recommendation:**
```python
# Add reconciliation module
class BankReconciliation:
    def reconcile(self, statement_balance, book_balance, outstanding_checks, deposits_in_transit):
        adjusted_book = book_balance + deposits_in_transit - outstanding_checks
        variance = statement_balance - adjusted_book
        if abs(variance) > 0.01:
            return {'status': 'unreconciled', 'variance': variance}
        return {'status': 'reconciled'}
```

---

### 9. **Revenue Recognition Timing**
**Risk Level:** 🟠 HIGH

**Problem:**
- Grant drawdowns recognized as revenue immediately
- Should be deferred until earned
- No accrual accounting
- Advance payments recognized immediately

**Accounting Impact:**
- Violates GAAP (ASC 606)
- Overstates revenue
- Tax implications
- Misleading financial statements

**Recommendation:**
```python
# Add deferred revenue logic
if 'grant drawdown' in description.lower():
    # DR: Cash (1010)
    # CR: Deferred Revenue - Grants (2300)
    gl_code = '2300'  # Liability account
    module = 'JV'  # Not revenue yet
```

---

### 10. **Vendor Refunds Misclassified**
**Risk Level:** 🟠 HIGH

**Problem:**
- [classification_engine.py:67-73](classifiers/classification_engine.py#L67-L73): Amount > 0 = customer match
- Vendor refunds (positive amount) skip vendor matching
- Classified as CR instead of CD reversal

**Accounting Impact:**
- Expense GL code wrong
- Vendor balance incorrect
- Budget tracking wrong

**Recommendation:**
```python
# Check keywords before amount-based routing
if 'refund' in description.lower() or 'credit memo' in description.lower():
    # Try vendor match regardless of amount sign
    vendor_result = self.vendor_matcher.match(transaction)
    if vendor_result['confidence'] > 0.7:
        result['module'] = 'CD'  # Negative CD = refund
        result['amount'] = -abs(result['amount'])  # Make negative
```

---

## ⚠️ MEDIUM PRIORITY ISSUES

### 11. **Date Parsing - Year Boundary Issues**
**Risk Level:** 🟡 MEDIUM

**Problem:**
- [pdf_parser.py:342-367](parsers/pdf_parser.py#L342-L367): Dates without year default to current year
- December 2024 statement uploaded in January 2025 → dates become 2025
- International date format confusion (DD/MM vs MM/DD)

**Recommendation:**
```python
def _parse_date_with_context(self, date_str, statement_date_range):
    parsed = self._parse_date(date_str)
    if parsed:
        # If parsed year is current but statement is from last year
        if parsed.year == datetime.now().year and \
           statement_date_range['start'].year == datetime.now().year - 1:
            parsed = parsed.replace(year=statement_date_range['start'].year)
    return parsed
```

---

### 12. **Ambiguous Keyword Conflicts**
**Risk Level:** 🟡 MEDIUM

**Problem:**
- [keyword_classifier.py:341-356](classifiers/keyword_classifier.py#L341-L356): "Transfer to IRS for Payroll" matches CR, CD, JV
- Ties return alphabetically (CR before CD) not by confidence
- Pattern overlaps: "wire in preparation to send" matches both incoming and outgoing

**Recommendation:**
```python
# Add keyword weights and tie-breaking
KEYWORD_WEIGHTS = {
    'payroll tax': 3.0,  # Highly specific
    'transfer': 0.5,     # Generic
    'payment': 1.0       # Moderate
}

# Tie-breaker: use GL code category
if scores['CR'] == scores['CD']:
    # Check if GL code is expense or revenue
    if gl_code.startswith('7'):  # Expense
        return 'CD'
    elif gl_code.startswith('4'):  # Revenue
        return 'CR'
```

---

### 13. **Large File Memory Issues**
**Risk Level:** 🟡 MEDIUM

**Problem:**
- [excel_parser.py:90](parsers/excel_parser.py#L90): Pandas reads entire file into memory
- 100K+ rows = memory exhaustion
- 50MB+ files silently rejected

**Recommendation:**
```python
# Add chunking for large files
def parse_large_excel(self, file_path):
    chunk_size = 10000
    all_transactions = []

    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        transactions = self._process_chunk(chunk)
        # Process and save to DB immediately
        db.transactions.insert_many(transactions)
        all_transactions.extend(transactions)

    return all_transactions
```

---

### 14. **OCR Path Hardcoded**
**Risk Level:** 🟡 MEDIUM

**Problem:**
- [config.py:66](config.py#L66): Tesseract path hardcoded for one user
- Linux deployments fail silently
- No error if Tesseract not installed

**Recommendation:**
```python
# Auto-detect or use environment variable
import shutil

TESSERACT_CMD = os.environ.get('TESSERACT_CMD') or \
                shutil.which('tesseract') or \
                r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Validate at startup
if not os.path.exists(TESSERACT_CMD):
    print(f"⚠️  Warning: Tesseract not found at {TESSERACT_CMD}")
    print("   OCR for scanned PDFs will not work")
```

---

### 15. **No Transaction Hash/Uniqueness**
**Risk Level:** 🟡 MEDIUM

**Problem:**
- No unique identifier for transactions
- Cannot detect if same transaction imported twice
- Cannot track transaction through workflow

**Recommendation:**
```python
import hashlib

def generate_transaction_hash(txn):
    """Generate unique hash for transaction"""
    key = f"{txn['date']}|{txn['amount']}|{txn['description']}|{txn.get('check_number', '')}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]

# Add to each transaction
transaction['txn_hash'] = generate_transaction_hash(transaction)
transaction['duplicate_check'] = db.transactions.count_documents({'txn_hash': transaction['txn_hash']}) > 0
```

---

## 📊 ACCOUNTING-SPECIFIC EDGE CASES

### 16. **Accrual vs Cash Basis**
**Problem:** System is pure cash basis
- Payroll dated 12/31 but deposited 1/2 posts to wrong fiscal year
- No accrual adjustments
- Prepaid expenses not deferred

**Impact:** Financial statements incorrect for accrual-basis entities

**Recommendation:**
- Add transaction type: 'cash' vs 'accrual'
- Add adjusting entries module
- Support both basis reporting

---

### 17. **Multi-Currency Not Supported**
**Problem:**
- All amounts assumed to be USD
- No exchange rate handling
- Foreign bank statements fail

**Impact:** International organizations cannot use tool

**Recommendation:**
```python
# Add currency field
transaction['currency'] = 'USD'
transaction['exchange_rate'] = 1.0
transaction['base_amount'] = amount * exchange_rate
```

---

### 18. **Rounding Errors Accumulate**
**Problem:**
- [amount parsing](parsers/pdf_parser.py#L369-L410): Float arithmetic
- No decimal precision standard
- Pennies lost over thousands of transactions

**Impact:** Trial balance off by several dollars

**Recommendation:**
```python
from decimal import Decimal, ROUND_HALF_UP

# Use Decimal for all amounts
amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

---

### 19. **Budget vs Actual Tracking Missing**
**Problem:**
- No budget upload or comparison
- No variance analysis
- GL codes used without budget control

**Impact:** Overspending not detected

**Recommendation:**
- Add budget table by GL code + Fund + Period
- Flag transactions that exceed budget
- Generate variance reports

---

### 20. **Audit Trail Incomplete**
**Problem:**
- [app.py:1694-1713](app.py#L1694-L1713): Audit log exists but:
  - No "before" snapshot
  - User ID may not be captured
  - No IP address tracking
  - No rollback capability

**Impact:** Cannot reconstruct who changed what when

**Recommendation:**
```python
def create_audit_log(action, entity_type, entity_id, old_value, new_value, user_id, ip_address):
    db.audit_logs.insert_one({
        'timestamp': datetime.now(),
        'action': action,  # 'create', 'update', 'delete'
        'entity_type': entity_type,
        'entity_id': entity_id,
        'old_value': old_value,  # Full JSON snapshot
        'new_value': new_value,  # Full JSON snapshot
        'user_id': user_id,
        'ip_address': ip_address,
        'reversible': True
    })
```

---

## 🔧 TECHNICAL EDGE CASES

### 21. **Silent Exception Swallowing**
**Risk Level:** 🟡 MEDIUM

**Locations:**
- [excel_parser.py:246](parsers/excel_parser.py#L246): `except Exception: continue`
- [pdf_parser.py:86](parsers/pdf_parser.py#L86): Generic print
- [app.py:589](app.py#L589): Generic flash message

**Problem:** Real errors hidden, debugging impossible

**Recommendation:**
```python
import logging

logger = logging.getLogger(__name__)

try:
    # ... code
except SpecificException as e:
    logger.error(f"Specific error in parsing: {e}", exc_info=True)
    raise
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    # Don't swallow - re-raise or handle properly
    raise
```

---

### 22. **Tempfile Cleanup Race Conditions**
**Problem:** [app.py:537-540](app.py#L537-L540)
```python
try:
    os.unlink(tmp_filepath)
except:
    pass  # Silently fails
```

**Issue:**
- File may still be open (Windows)
- Permissions error on Linux
- Temp directory fills up

**Recommendation:**
```python
import atexit

# Register cleanup handler
temp_files = []

def cleanup_temp_files():
    for f in temp_files:
        try:
            if os.path.exists(f):
                os.unlink(f)
        except Exception as e:
            logger.warning(f"Could not delete temp file {f}: {e}")

atexit.register(cleanup_temp_files)
```

---

### 23. **No Rate Limiting**
**Problem:**
- User can upload unlimited files rapidly
- No throttling on API endpoints
- DoS vulnerability

**Recommendation:**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload():
    # ...
```

---

### 24. **File Extension vs Content Validation**
**Problem:** [app.py:508](app.py#L508)
```python
def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS
```

**Issue:**
- Only checks extension, not actual content
- `malware.exe` renamed to `malware.pdf` passes
- No magic number validation

**Recommendation:**
```python
import magic

def validate_file_type(file_path, expected_type):
    mime = magic.from_file(file_path, mime=True)

    ALLOWED_MIMES = {
        'pdf': 'application/pdf',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv'
    }

    if mime != ALLOWED_MIMES.get(expected_type):
        raise ValueError(f"File content ({mime}) doesn't match extension")
```

---

### 25. **Hardcoded Secret Key**
**Risk Level:** 🔴 CRITICAL SECURITY

**Problem:** [app.py:37](app.py#L37)
```python
app.secret_key = 'bank_posting_tool_secret_key_2024'
```

**Issue:**
- Hardcoded in source code (committed to git!)
- Same across all deployments
- Session hijacking possible
- Flask session cookies can be forged

**Recommendation:**
```python
import secrets

app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# In deployment:
# export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

---

## 📋 COMPLETE EDGE CASE CHECKLIST

### Parsing Layer
- [ ] Mixed digital/scanned PDF pages
- [ ] Dates without year across year boundary
- [ ] International date formats (DD/MM/YYYY)
- [ ] Future-dated transactions
- [ ] Zero amount transactions
- [ ] Negative amounts in debit columns
- [ ] Amount format ambiguity (European vs US)
- [ ] Very large amounts (>$1M)
- [ ] OCR quality threshold
- [ ] Check number duplicates
- [ ] Multi-line descriptions
- [ ] Merged Excel cells
- [ ] CSV encoding issues
- [ ] Files >50MB
- [ ] Files >100K rows

### Classification Layer
- [ ] Keyword conflicts/ambiguity
- [ ] Vendor name aliases
- [ ] Vendor refunds (positive amount)
- [ ] Customer refunds (negative amount)
- [ ] Grant vs customer name collision
- [ ] Pattern learning from bad corrections
- [ ] Confidence score ties
- [ ] Missing GL code suggestions
- [ ] Historical pattern pollution

### Data Validation
- [ ] Duplicate transaction detection
- [ ] Debit = Credit validation
- [ ] GL code existence check
- [ ] Fund code restrictions
- [ ] GL + Fund combination validity
- [ ] Period closing enforcement
- [ ] Zero/null amount prevention
- [ ] Future date warnings
- [ ] Balance reconciliation

### Accounting Principles
- [ ] Double-entry balance
- [ ] Fund accounting restrictions
- [ ] Revenue recognition timing
- [ ] Accrual vs cash basis
- [ ] Period closing locks
- [ ] Bank reconciliation
- [ ] Budget vs actual
- [ ] Multi-currency support
- [ ] Rounding precision (Decimal)
- [ ] Audit trail completeness

### Technical
- [ ] Concurrent user isolation
- [ ] MongoDB retry mechanism
- [ ] Large file streaming
- [ ] Memory limits enforcement
- [ ] Rate limiting
- [ ] File content validation
- [ ] Secret key security
- [ ] Exception logging
- [ ] Tempfile cleanup
- [ ] Session timeout
- [ ] XSS/SQL injection prevention
- [ ] CSRF protection

---

## 🎯 RECOMMENDED PRIORITY ORDER

### Phase 1: Critical Fixes (Before Production Use)
1. Fix global session data → per-user sessions
2. Add duplicate transaction detection
3. Add debit/credit balance validation
4. Fix MongoDB retry mechanism
5. Change hardcoded secret key
6. Add period closing enforcement
7. Add fund accounting validation

### Phase 2: High Priority (First Month)
8. Add bank reconciliation module
9. Fix vendor refund classification
10. Add revenue recognition logic
11. Add zero amount validation
12. Implement proper exception logging
13. Add file content validation

### Phase 3: Medium Priority (Quarter 1)
14. Add large file streaming
15. Fix date parsing year boundary
16. Resolve keyword conflicts
17. Add budget tracking
18. Implement rate limiting
19. Add audit trail enhancements

### Phase 4: Enhancement (Quarter 2+)
20. Multi-currency support
21. Accrual accounting module
22. Advanced reconciliation
23. Variance analysis
24. Pattern learning improvements
25. Performance optimization

---

## 💡 GENERAL RECOMMENDATIONS

### 1. Add Comprehensive Testing
```python
# Unit tests for each classifier
def test_vendor_refund_classification():
    txn = {'description': 'VENDOR REFUND', 'amount': 50.00}
    result = classifier.classify(txn)
    assert result['module'] == 'CD'
    assert result['amount'] < 0  # Should be negative

# Integration tests
def test_duplicate_upload():
    upload_file('statement.pdf')
    result = upload_file('statement.pdf')  # Same file
    assert result['duplicates_found'] == len(transactions)
```

### 2. Add Configuration Validation
```python
# Validate on startup
def validate_configuration():
    errors = []

    if not os.path.exists(TESSERACT_CMD):
        errors.append(f"Tesseract not found at {TESSERACT_CMD}")

    if app.secret_key == 'bank_posting_tool_secret_key_2024':
        errors.append("SECURITY: Secret key is default/hardcoded!")

    if not MONGODB_AVAILABLE:
        errors.append("WARNING: pymongo not installed")

    # ... more checks

    if errors:
        for err in errors:
            logger.error(err)
        if any('SECURITY' in e for e in errors):
            raise RuntimeError("Cannot start with security issues")
```

### 3. Add User Warnings
```python
# Warn user of risky operations
@app.route('/process', methods=['POST'])
def process():
    warnings = []

    for txn in transactions:
        if txn['amount'] == 0:
            warnings.append(f"Line {txn['line']}: Zero amount transaction")

        if txn['date'] > datetime.now():
            warnings.append(f"Line {txn['line']}: Future-dated transaction")

        if not txn.get('gl_code'):
            warnings.append(f"Line {txn['line']}: No GL code assigned")

    return jsonify({'warnings': warnings, 'proceed': len(warnings) == 0})
```

---

**End of Edge Case Analysis**

This document should be reviewed quarterly and updated as:
- New edge cases are discovered
- Fixes are implemented
- New features are added
- Accounting rules change
