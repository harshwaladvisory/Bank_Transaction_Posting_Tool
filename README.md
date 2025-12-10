# Bank Transaction Posting Tool

**Harshwal Consulting Services**

Automates bank statement processing and journal entry generation for accounting systems.

## 🎯 Overview

This tool processes bank statements (PDF, Excel, CSV) and automatically:
- Extracts transactions using OCR (for scanned PDFs) or direct parsing
- Classifies transactions using 500+ keywords, vendor matching, and pattern recognition
- Routes transactions to appropriate accounting modules (Cash Receipts, Cash Disbursements, Journal Vouchers)
- Generates formatted import files for MIP, QuickBooks Desktop, and other systems
- Learns from manual corrections to improve future accuracy

## 📋 Features

### Data Ingestion
- **PDF Support**: Digital PDFs and scanned documents (via OCR)
- **Excel Support**: .xlsx, .xls files with auto-column detection
- **CSV Support**: Comma-separated files with flexible formatting

### Classification Engine
- **Keyword Matching**: 500+ terms for payroll, taxes, grants, utilities, etc.
- **Vendor Matching**: Match against vendor master list
- **Customer/Grant Matching**: Identify grant drawdowns (HUD, DOE, HHS, etc.)
- **Historical Pattern Recognition**: Learn from past transactions
- **Confidence Scoring**: High/Medium/Low confidence for review prioritization

### Module Routing
| Module | Description | Examples |
|--------|-------------|----------|
| **CR** | Cash Receipts | Grants, deposits, customer payments, refunds |
| **CD** | Cash Disbursements | Payroll, taxes, vendor payments, utilities |
| **JV** | Journal Vouchers | Bank fees, interest, corrections, transfers |

### Output Files
- Cash_Receipts_Import.xlsx
- Cash_Disbursements_Import.xlsx
- Journal_Vouchers_Import.xlsx
- Unidentified.xlsx (for manual review)
- Processing_Summary.xlsx

## 🚀 Quick Start

### Installation

1. **Clone/Extract the tool:**
```bash
cd bank_posting_tool
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **For PDF/OCR support (optional):**
   - Windows: Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and [Poppler](https://github.com/osborne/poppler-windows)
   - Update paths in `config.py` if needed

### Usage

#### Command Line Interface
```bash
# Process a bank statement
python main.py statement.pdf

# Specify output directory
python main.py statement.xlsx --output ./my_output

# Target QuickBooks Desktop format
python main.py statement.csv --system QBD

# Launch web interface
python main.py --web
```

#### Web Interface
```bash
python app.py
# Open http://127.0.0.1:5000 in your browser
```

## 📁 Project Structure

```
bank_posting_tool/
├── main.py                 # CLI entry point
├── app.py                  # Flask web interface
├── config.py               # Configuration settings
│
├── parsers/                # Bank statement parsing
│   ├── pdf_parser.py       # PDF extraction (digital + OCR)
│   ├── excel_parser.py     # Excel/CSV parsing
│   └── universal_parser.py # Auto-detect and route
│
├── classifiers/            # Transaction classification
│   ├── keyword_classifier.py    # 500+ keyword rules
│   ├── vendor_matcher.py        # Vendor matching
│   ├── customer_matcher.py      # Customer/Grant matching
│   ├── history_matcher.py       # Historical patterns
│   └── classification_engine.py # Main orchestrator
│
├── processors/             # Entry generation
│   ├── module_router.py    # Route to CR/CD/JV
│   ├── entry_builder.py    # Build journal entries
│   └── output_generator.py # Generate Excel files
│
├── data/                   # Data files
│   ├── keywords.json       # Classification keywords
│   ├── vendors.json        # Vendor master list
│   ├── customers.json      # Customer list
│   ├── grants.json         # Grant programs
│   └── learned_patterns.json # Learned corrections
│
├── templates/              # Flask HTML templates
├── outputs/                # Generated files
├── logs/                   # Audit trail
└── uploads/                # Uploaded files (web)
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Date format (SOP requirement)
DATE_FORMAT = "%m/%d/%Y"

# Default GL codes
DEFAULT_BANK_GL = '1070'
DEFAULT_FUND_CODE = '1000'

# Confidence thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.40

# OCR paths (Windows)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler\bin'
```

## 📊 Classification Rules

### Cash Receipts (CR)
- Keywords: deposit, credit, grant, HUD, DOE, interest income, refund, customer payment
- Patterns: `(?i)deposit.*from`, `(?i)grant.*award`

### Cash Disbursements (CD)
- Keywords: payroll, ADP, IRS, EFTPS, check, vendor, utility, insurance
- Patterns: `(?i)payroll.*transfer`, `(?i)irs.*eftps`

### Journal Vouchers (JV)
- Keywords: bank fee, service charge, interest charge, correction, transfer
- Patterns: `(?i)bank.*charge`, `(?i)monthly.*maintenance`

## 🔧 Extending the Tool

### Add Custom Keywords
Edit `data/keywords.json`:
```json
{
  "classification_rules": {
    "CR": {
      "keywords": ["your_keyword", ...]
    }
  }
}
```

### Add Vendors
Edit `data/vendors.json` or load from Excel:
```python
from classifiers import VendorMatcher
matcher = VendorMatcher()
matcher.load_from_file('vendor_list.xlsx')
matcher.save_vendors()
```

### Add Grants
Edit `data/grants.json`:
```json
{
  "name": "New Grant Program",
  "aliases": ["ngp", "new grant"],
  "agency": "HUD",
  "cfda": "14.XXX",
  "gl_code": "4100",
  "fund_code": "2700"
}
```

## 📝 Entry Structure (Per SOP)

### Cash Receipt Entry
| Field | Value |
|-------|-------|
| Session ID | GP_CR_YYYY |
| Doc Number | GP_MMDD_SEQ |
| Debit | Bank GL (1070) |
| Credit | Revenue GL |

### Cash Disbursement Entry
| Field | Value |
|-------|-------|
| Session ID | GP_CD_YYYY |
| Doc Number | GP_MMDD_SEQ |
| Debit | Expense GL |
| Credit | Bank GL (1070) |

### Journal Voucher Entry
| Field | Value |
|-------|-------|
| Session ID | GP_JV_YYYY |
| Doc Number | GP_MMDD_SEQ |
| Debit/Credit | Depends on type |

## 🐛 Troubleshooting

### "No transactions found"
- Check file format is correct
- For PDFs, ensure text is selectable (not image-only)
- For scanned PDFs, verify Tesseract is installed

### "OCR not working"
- Install Tesseract: `pip install pytesseract`
- Install Poppler for PDF conversion
- Update paths in `config.py`

### "Module classification incorrect"
1. Review the transaction in web interface
2. Correct the module/GL code
3. The tool learns from corrections automatically

## 📄 License

Proprietary - Harshwal Consulting Services

## 🤝 Support

For questions or issues, contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: December 2024
