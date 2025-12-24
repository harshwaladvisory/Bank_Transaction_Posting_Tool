# Bank Transaction Posting Tool
## Complete Technical Documentation

**Version:** 2.2.0
**Organization:** Harshwal Consulting Services
**Date:** December 2025
**Author:** Development Team

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture](#3-architecture)
4. [Features](#4-features)
5. [Technical Components](#5-technical-components)
6. [User Interface](#6-user-interface)
7. [Supported Banks](#7-supported-banks)
8. [GL Code Structure](#8-gl-code-structure)
9. [Installation Guide](#9-installation-guide)
10. [Configuration](#10-configuration)
11. [API Reference](#11-api-reference)
12. [Performance](#12-performance)
13. [Troubleshooting](#13-troubleshooting)
14. [Version History](#14-version-history)

---

# 1. Executive Summary

The **Bank Transaction Posting Tool** is an enterprise-grade application designed to automate the complete workflow from bank statement upload to accounting system-ready journal entries. Built by Harshwal Consulting Services, this tool significantly reduces manual data entry, minimizes errors, and accelerates the bank reconciliation process.

## Key Benefits

| Benefit | Description |
|---------|-------------|
| **Time Savings** | Reduces manual entry from hours to minutes |
| **Accuracy** | 100% accuracy with template-based parsing for supported banks |
| **Multi-Format** | Supports PDF, Excel, and CSV bank statements |
| **Smart Learning** | ChromaDB-powered learning from user corrections |
| **Production Ready** | MongoDB integration, concurrent users, audit trails |

## Target Users

- Accountants and bookkeepers
- Financial controllers
- Housing authorities
- Government agencies
- Non-profit organizations

---

# 2. System Overview

## 2.1 What It Does

The tool processes bank statements and automatically:

1. **Extracts** all transactions (deposits and withdrawals)
2. **Classifies** each transaction by type and GL code
3. **Routes** to appropriate accounting module (CR/CD/JV)
4. **Generates** Excel import files for accounting systems
5. **Learns** from user corrections for future accuracy

## 2.2 Processing Flow

```
Bank Statement (PDF/Excel/CSV)
        |
        v
   [UPLOAD] --> File Detection & Validation
        |
        v
   [PARSE] --> SmartParser (Template-based)
        |           |
        |           v (if unknown bank)
        |       AIParser (Fallback)
        |
        v
   [CLASSIFY] --> Keyword + Vendor + Customer Matching
        |
        v
   [ROUTE] --> CR (Cash Receipts)
        |       CD (Cash Disbursements)
        |       JV (Journal Vouchers)
        |
        v
   [REVIEW] --> User Review & Corrections
        |
        v
   [GENERATE] --> Excel Import Files
        |
        v
   [DOWNLOAD] --> Ready for Accounting System
```

---

# 3. Architecture

## 3.1 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | HTML5, Bootstrap 5, JavaScript | User interface |
| **Backend** | Python 3.8+, Flask | Web application framework |
| **Database** | MongoDB (optional) | Data persistence |
| **OCR Engine** | Tesseract OCR | Scanned PDF processing |
| **PDF Processing** | pdfplumber, pdf2image | PDF extraction |
| **Data Processing** | pandas, openpyxl | Excel/CSV handling |
| **Learning** | ChromaDB, sentence-transformers | Vector embeddings for GL suggestions |

## 3.2 Directory Structure

```
Bank_Transaction_Posting_Tool/
|
├── app.py                      # Main Flask application (160KB)
├── main.py                     # CLI entry point (10.6KB)
├── config.py                   # Configuration settings (2.2KB)
├── requirements.txt            # Python dependencies
|
├── parsers/                    # Bank statement parsing modules
│   ├── __init__.py            # Package exports
│   ├── universal_parser.py    # Auto-detect file type (5.8KB)
│   ├── smart_parser.py        # Template-based parser (197KB) [PRIMARY]
│   ├── pdf_parser.py          # Legacy PDF parser (85KB)
│   ├── excel_parser.py        # Excel/CSV parser (14KB)
│   ├── template_parser.py     # JSON template support (13KB)
│   ├── ai_parser.py           # Regex fallback (22KB)
│   └── llm_parser.py          # LLM fallback (27KB)
|
├── classifiers/                # Transaction classification
│   ├── __init__.py            # Package exports
│   ├── classification_engine.py # Main orchestrator (34KB)
│   ├── keyword_classifier.py   # 500+ keyword rules (22KB)
│   ├── vendor_matcher.py       # Fuzzy vendor matching (13KB)
│   ├── customer_matcher.py     # Customer/grant matching (14KB)
│   └── history_matcher.py      # Historical pattern matching (16KB)
|
├── processors/                 # Journal entry generation
│   ├── __init__.py            # Package exports
│   ├── module_router.py       # Route to CR/CD/JV (13KB)
│   ├── entry_builder.py       # Build journal entries (17KB)
│   └── output_generator.py    # Generate Excel files (13KB)
|
├── learning/                   # Machine learning components
│   ├── __init__.py            # Package exports
│   ├── chroma_store.py        # ChromaDB vector store (23.8KB)
│   └── gl_suggester.py        # GL code suggestions (20.5KB)
|
├── templates/                  # HTML templates
│   ├── base.html              # Base template with Bootstrap
│   ├── index.html             # Upload interface
│   ├── review.html            # Transaction review
│   └── results.html           # Processing results
|
├── config/                     # Configuration files
│   └── bank_templates.json    # Bank-specific parsing rules
|
├── data/                       # Data storage
│   ├── keywords.json          # Classification keywords
│   ├── vendors.json           # Vendor master list
│   ├── customers.json         # Customer list
│   ├── grants.json            # Grant programs
│   ├── learned_patterns.json  # Learned patterns
│   ├── ocr_cache/             # Cached OCR results
│   └── chroma_db/             # Vector embeddings
|
└── logs/                       # Audit trail logs
```

## 3.3 Module Responsibilities

### Parsers

| Module | Responsibility |
|--------|----------------|
| **UniversalParser** | Detects file type and routes to appropriate parser |
| **SmartParser** | Template-based parsing with bank detection (PRIMARY) |
| **PDFParser** | Low-level PDF text extraction with OCR support |
| **ExcelParser** | Excel and CSV file parsing |
| **AIParser** | Regex-based fallback for unknown formats |
| **LLMParser** | AI-powered parsing (optional, for complex cases) |

### Classifiers

| Module | Responsibility |
|--------|----------------|
| **ClassificationEngine** | Orchestrates all classification methods |
| **KeywordClassifier** | Matches 500+ keywords to GL codes |
| **VendorMatcher** | Fuzzy matches against vendor master list |
| **CustomerMatcher** | Identifies customers and grant programs |
| **HistoryMatcher** | Learns from historical transactions |

### Processors

| Module | Responsibility |
|--------|----------------|
| **ModuleRouter** | Routes transactions to CR/CD/JV modules |
| **EntryBuilder** | Constructs balanced journal entries |
| **OutputGenerator** | Creates Excel import files |

---

# 4. Features

## 4.1 Multi-Format File Support

| Format | Extensions | Features |
|--------|------------|----------|
| **PDF** | .pdf | Digital text extraction + OCR for scanned |
| **Excel** | .xlsx, .xls | Auto-column detection |
| **CSV** | .csv | Flexible delimiter support |

## 4.2 Multiple File Upload

The application supports uploading multiple bank statements at once:

- **Drag & Drop**: Drag multiple files onto the upload zone
- **File Picker**: Hold Ctrl to select multiple files
- **Add More**: Click "Add More" button to add additional files
- **Combined Processing**: All files processed and merged into single review

## 4.3 Smart Bank Detection

The system automatically detects the bank from statement content:

```
Supported Banks:
- Farmers Bank (with multi-year handling)
- Truist Bank
- PNC Bank
- CrossFirst Bank
- Sovereign Bank
- Generic (fallback for unknown banks)
```

## 4.4 Confidence Scoring

Each classified transaction receives a confidence score:

| Level | Range | Indicator | Meaning |
|-------|-------|-----------|---------|
| **High** | 85-100% | Green badge | Reliable classification |
| **Medium** | 60-84% | Yellow badge | Review recommended |
| **Low** | 0-59% | Red badge | Manual review required |
| **None** | N/A | Gray badge | No match found |

## 4.5 Confidence Filter

The review page includes a clickable confidence filter:

- **Column Header Filter**: Click "Confidence" header dropdown
- **Badge Filter**: Click any confidence badge to filter
- **Clear Filter**: Click X on active filter badge
- **Options**: All Levels, High, Medium, Low, No Match

## 4.6 Transaction Classification

### Keyword-Based Classification

Over 500 keywords mapped to GL codes:

| Category | Example Keywords | GL Range |
|----------|-----------------|----------|
| **Grants** | HUD, DOE, NAHASDA | 3001-3999 |
| **Payroll** | PAYROLL, SALARY, WAGES | 6600 |
| **Taxes** | TAX, IRS, FICA | 7200 |
| **Utilities** | ELECTRIC, GAS, WATER | 6200 |
| **Insurance** | BCBS, HEALTH, INSURANCE | 6650 |
| **Bank Fees** | SERVICE FEE, FEE | 6100 |

### High-Confidence Auto-Classification

| Transaction Type | GL Code | Confidence |
|-----------------|---------|------------|
| SERVICE FEE | 6100 | 95% |
| INTEREST | 4600 | 98% |
| CHECK #XXXX | 7300 | 95% |

## 4.7 Module Routing

### Cash Receipts (CR)
- **GL Range**: 4000-4999
- **Types**: Deposits, grants, donations, interest income
- **Examples**: HUD grants, customer payments, bank interest

### Cash Disbursements (CD)
- **GL Range**: 6000-7999
- **Types**: Checks, payroll, taxes, service fees
- **Examples**: Vendor payments, employee salaries, utility bills

### Journal Vouchers (JV)
- **Types**: Multi-line entries, corrections, transfers
- **Examples**: Bank fee allocations, error corrections

## 4.8 Learning System

The ChromaDB-based learning system:

1. **Stores Patterns**: Saves transaction patterns as vector embeddings
2. **Suggests GL Codes**: Finds similar past transactions
3. **Learns from Corrections**: Updates when users change classifications
4. **100% Local**: No external API calls (data security)

## 4.9 Bulk Operations

| Feature | Description |
|---------|-------------|
| **Bulk Edit** | Edit multiple low-confidence transactions at once |
| **Bulk Download** | Download all output files as ZIP |
| **Batch Processing** | Process multiple statements in one upload |

---

# 5. Technical Components

## 5.1 SmartParser (Primary Parser)

The SmartParser is the core parsing engine with these capabilities:

### Bank Detection
```python
# Identifies bank from statement content
identifiers = ["Farmers Bank", "farmers-bank.com"]
bank_detected = "Farmers Bank"
```

### Transaction Extraction
```python
# Regex-based pattern matching
pattern = r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$'
# Extracts: date, description, amount
```

### OCR Processing
- **Engine**: Tesseract OCR
- **DPI**: 350 (optimized for speed)
- **Caching**: File-hash based (2000x faster on repeat)

## 5.2 Classification Engine

The ClassificationEngine orchestrates multiple matchers:

```python
# Classification pipeline
1. KeywordClassifier.match(description)  # 500+ keywords
2. VendorMatcher.match(description)      # Fuzzy vendor matching
3. CustomerMatcher.match(description)    # Customer/grant matching
4. HistoryMatcher.match(description)     # Historical patterns
5. ChromaStore.suggest(description)      # Vector similarity
```

## 5.3 ChromaDB Learning Store

Vector embedding-based learning:

```python
# Store a learned pattern
store.learn_transaction(
    description="HUD TREAS NAHASDA",
    gl_code="3001",
    transaction_type="deposit",
    module="CR",
    bank_name="PNC"
)

# Get suggestions for new transaction
suggestions = store.suggest_gl_code("HUD TREASURY PAYMENT")
# Returns: [{'gl_code': '3001', 'confidence': 92.5, ...}]
```

---

# 6. User Interface

## 6.1 Upload Page (index.html)

Features:
- Drag-and-drop file upload zone
- Visible file input with multiple selection
- "Multiple Bank Statements Supported" badge
- Selected files list with remove option
- "Add More" button for additional files
- Progress indicator during processing

## 6.2 Review Page (review.html)

Features:
- Module tabs: All, CR, CD, JV, Unknown
- Transaction statistics cards
- Confidence filter dropdown in column header
- Clickable confidence badges for filtering
- Edit button for each transaction
- Bulk edit for low confidence items
- Balance summary showing credits/debits

## 6.3 Results Page (results.html)

Features:
- Generated files list
- Individual file download
- "Download All as ZIP" button
- Processing summary

---

# 7. Supported Banks

| Bank | Template | OCR | Special Features |
|------|----------|-----|------------------|
| **Farmers Bank** | Full | Yes | Multi-year statement handling |
| **Truist Bank** | Full | Yes | Complete transaction extraction |
| **PNC Bank** | Full | Yes | Service charge recovery |
| **CrossFirst Bank** | Full | Yes | Withdrawal date extraction fixes |
| **Sovereign Bank** | Full | Yes | Full format support |
| **Generic** | Fallback | Yes | Handles unknown formats |

### Adding New Banks

Edit `config/bank_templates.json`:

```json
{
  "banks": {
    "NewBank": {
      "identifiers": ["New Bank Name", "newbank.com"],
      "requires_ocr": true,
      "transaction_patterns": [
        {
          "name": "standard",
          "pattern": "^(\\d{1,2}/\\d{1,2})\\s+(.+?)\\s+([\\d,]+\\.\\d{2})$",
          "groups": {"date": 1, "description": 2, "amount": 3},
          "type": "auto"
        }
      ],
      "deposit_keywords": ["DEPOSIT", "CREDIT", "TRANSFER IN"],
      "withdrawal_keywords": ["CHECK", "DEBIT", "FEE", "WITHDRAWAL"]
    }
  }
}
```

---

# 8. GL Code Structure

## 8.1 Standard Chart of Accounts

| Range | Category | Description |
|-------|----------|-------------|
| **1000-1999** | Assets | Bank accounts, receivables |
| **2000-2999** | Liabilities | Payables, accruals |
| **3000-3999** | Fund Balance/Equity | Federal revenue, retained earnings |
| **4000-4999** | Revenue | Grants, interest, donations |
| **5000-5999** | COGS | Cost of goods sold |
| **6000-6999** | Operating Expenses | Salaries, utilities, insurance |
| **7000-7999** | Other Expenses | Taxes, vendor payments |
| **8000-8999** | Other Income/Expense | Miscellaneous |

## 8.2 Common GL Codes

| GL Code | Description | Module |
|---------|-------------|--------|
| 1070 | Bank Account | - |
| 3001 | Federal Revenue | CR |
| 4100 | Grant Revenue | CR |
| 4600 | Interest Income | CR |
| 6100 | Bank Fees | CD |
| 6600 | Salaries & Wages | CD |
| 6650 | Insurance | CD |
| 7200 | Taxes | CD |
| 7300 | Vendor Payments | CD |

---

# 9. Installation Guide

## 9.1 Prerequisites

- **Python**: 3.8 or higher
- **MongoDB**: 4.0+ (optional, for persistence)
- **Tesseract OCR**: Required for scanned PDFs
- **Poppler**: Required for PDF processing

## 9.2 Step-by-Step Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/harshwaladvisory/Bank_Transaction_Posting_Tool.git
cd Bank_Transaction_Posting_Tool
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install Tesseract OCR (Windows)
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. Add to PATH or update `config.py`

### Step 5: Install Poppler (Windows)
1. Download from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to: `C:\poppler\`
3. Update path in `config.py`

### Step 6: Configure Paths
Edit `config.py`:
```python
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\bin'
```

### Step 7: Set Environment Variables (Production)
```bash
set SECRET_KEY=your-secret-key-here
set MONGODB_URI=mongodb://localhost:27017/
set MONGODB_DATABASE=bank_posting_tool
set PORT=8590
```

### Step 8: Run Application
```bash
python app.py
```

### Step 9: Access Web Interface
Open browser: `http://localhost:8590`

---

# 10. Configuration

## 10.1 config.py Settings

```python
# Date Formats
DATE_FORMAT = "%m/%d/%Y"
DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"]

# Default GL Codes
DEFAULT_BANK_GL = '1070'
DEFAULT_FUND_CODE = '1000'

# Confidence Thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.40

# OCR Settings
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\bin'
OCR_DPI = 350  # Optimized for speed

# Flask Settings
FLASK_DEBUG = True
FLASK_PORT = 8590
```

## 10.2 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Production | Auto-generated | Flask session encryption |
| `MONGODB_URI` | No | localhost:27017 | MongoDB connection string |
| `MONGODB_DATABASE` | No | bank_posting_tool | Database name |
| `PORT` | No | 8590 | Server port |
| `FLASK_DEBUG` | No | True | Debug mode |

---

# 11. API Reference

## 11.1 Health Check

```
GET /api/status
```

Response:
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "version": "2.2.0"
}
```

## 11.2 Transactions

### List Transactions
```
GET /api/transactions
```

### Create Transaction
```
POST /api/transactions
Content-Type: application/json

{
  "date": "12/24/2025",
  "description": "HUD GRANT PAYMENT",
  "amount": 50000.00,
  "type": "deposit"
}
```

### Update Transaction
```
PUT /api/transactions/<id>
Content-Type: application/json

{
  "gl_code": "3001",
  "module": "CR"
}
```

### Delete Transaction
```
DELETE /api/transactions/<id>
```

## 11.3 File Downloads

### Download Single File
```
GET /download/<filename>
```

### Download All as ZIP
```
GET /download_all_zip
```

## 11.4 Bulk Update
```
POST /bulk_update
Content-Type: application/json

{
  "updates": [
    {"index": 0, "module": "CR", "gl_code": "3001", "fund_code": "1000"},
    {"index": 1, "module": "CD", "gl_code": "6100", "fund_code": "1000"}
  ]
}
```

---

# 12. Performance

## 12.1 Processing Times

| Scenario | Time | Notes |
|----------|------|-------|
| First PDF (23 pages) | ~100-120s | Includes OCR processing |
| Cached PDF (same file) | ~0.2s | Uses OCR cache |
| Simple PDF (3-5 pages) | ~15-30s | First-time processing |
| Excel/CSV | ~1-2s | No OCR required |

## 12.2 Optimization Techniques

| Technique | Improvement |
|-----------|-------------|
| **OCR Caching** | 2000x faster on repeat files |
| **Reduced DPI** | 30% faster (350 vs 500 DPI) |
| **Single-pass OCR** | Eliminates redundant processing |
| **Page Classification** | Skips non-transaction pages |

## 12.3 Clearing Cache

```bash
# Clear OCR cache
rm -rf data/ocr_cache/*

# Clear learning data
rm -rf data/chroma_db/*
```

---

# 13. Troubleshooting

## 13.1 Common Issues

### "No transactions found"
1. Check file format (.pdf, .xlsx, .xls, .csv)
2. Verify bank is supported
3. Check OCR installation for scanned PDFs
4. Review console logs for bank detection

### "Processing takes too long"
- First-time OCR processing is slow (~100s for 23 pages)
- Subsequent uploads use cache (<1s)
- Clear cache if files have changed: `rm -rf data/ocr_cache/*`

### "OCR not working"
1. Verify Tesseract installation
2. Verify Poppler installation
3. Check paths in `config.py`
4. Test: `tesseract --version`

### "MongoDB connection failed"
- MongoDB is optional
- Tool works without it (no persistence)
- To enable: `mongod` and set `MONGODB_URI`

### "Tracking Prevention blocking CDN"
- Application uses cdnjs.cloudflare.com
- If blocked, disable tracking prevention for the site
- Or add localhost to exceptions

---

# 14. Version History

## v2.2.0 (December 2025)
- **UI Enhancements**
  - Multiple file upload support
  - Confidence filter in column header
  - Clickable confidence badges
  - Active filter indicator
  - CDN switched to cdnjs (Cloudflare)
- **Performance**
  - OCR caching (2000x improvement)
  - Reduced DPI for faster processing
- **Parser Improvements**
  - CrossFirst Bank withdrawal date fixes
  - Multi-year statement handling
  - Vendor extraction validation

## v2.1.0 (December 2025)
- Smart parser with bank templates
- ChromaDB learning module
- Multiple bank format support

## v2.0.0 (December 2025)
- MongoDB integration
- Duplicate detection
- Concurrent user support
- Security hardening

## v1.0.0 (Initial Release)
- Basic PDF/Excel parsing
- Keyword classification
- CR/CD/JV routing

---

# Appendix A: Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl + Click | Select multiple files |
| Shift + Click | Select file range |
| Ctrl + F5 | Hard refresh (clear cache) |

# Appendix B: File Format Requirements

## PDF Files
- Digital or scanned
- Single or multi-page
- Portrait or landscape orientation

## Excel Files
- .xlsx or .xls format
- First row should contain headers
- Date, Description, Amount columns required

## CSV Files
- Comma-separated values
- UTF-8 encoding preferred
- Header row recommended

---

**Document Version:** 1.0
**Last Updated:** December 24, 2025
**Maintained By:** Harshwal Consulting Services Development Team
