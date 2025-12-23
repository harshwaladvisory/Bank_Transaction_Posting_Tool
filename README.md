# Bank Transaction Posting Tool

**Harshwal Consulting Services**

Enterprise-grade bank statement processing and journal entry generation for accounting systems.

---

## Overview

Automates the complete workflow from bank statement upload to accounting system-ready journal entries:

- **Multi-format parsing**: PDF (digital + OCR), Excel, CSV
- **Template-based classification**: 100% accuracy with regex patterns for supported banks
- **Three accounting modules**: Cash Receipts (CR), Cash Disbursements (CD), Journal Vouchers (JV)
- **Production-ready**: Duplicate detection, balance validation, concurrent users, MongoDB-backed
- **Performance optimized**: OCR caching for instant repeat processing

---

## Features

### Smart Parser Architecture

The tool uses a **template-based regex parser** that achieves 100% accuracy for supported banks:

| Component | Description |
|-----------|-------------|
| **SmartParser** | Primary parser using bank-specific templates |
| **Bank Templates** | JSON-configurable patterns for each bank format |
| **OCR Processing** | Tesseract OCR with smart page classification |
| **OCR Caching** | File-hash based caching for instant repeat processing |
| **Vendor Extraction** | Extracts payee names from check images (with validation) |

### Data Ingestion

| Feature | Description |
|---------|-------------|
| **PDF Support** | Digital PDFs and scanned documents (via OCR) |
| **Excel Support** | .xlsx, .xls files with auto-column detection |
| **CSV Support** | Comma-separated files with flexible formatting |
| **Smart Detection** | Auto-detects bank formats from statement content |

### Classification Engine

| Feature | Description |
|---------|-------------|
| **Keyword Matching** | 500+ terms for payroll, taxes, grants, utilities |
| **High-Confidence Detection** | SERVICE FEE, INTEREST, CHECK automatically classified |
| **Vendor Matching** | Fuzzy matching against vendor master list |
| **Customer/Grant Matching** | Identifies government grants (HUD, DOE, HHS) |
| **Confidence Scoring** | High (>85%), Medium (60-85%), Low (<60%) |

### Module Routing

| Module | GL Range | Description | Examples |
|--------|----------|-------------|----------|
| **CR** | 4000-4999 | Cash Receipts | Grants, deposits, customer payments, interest |
| **CD** | 6000-7999 | Cash Disbursements | Checks, payroll, taxes, service fees |
| **JV** | Various | Journal Vouchers | Bank fees, corrections, transfers |

### Supported Banks

| Bank | Format | OCR Support | Template Status |
|------|--------|-------------|-----------------|
| **Farmers Bank** | PDF | Yes | Full support with multi-year handling |
| **Truist** | PDF | Yes | Full support |
| **PNC** | PDF | Yes | Full support |
| **CrossFirst** | PDF | Yes | Full support |
| **Sovereign** | PDF | Yes | Full support |
| **Generic** | PDF/Excel/CSV | Yes | Fallback parser |

---

## Performance

### OCR Optimization

The tool includes several performance optimizations for PDF processing:

| Optimization | Improvement |
|--------------|-------------|
| **OCR Caching** | 2000x+ faster on repeat processing |
| **Reduced DPI** | 350 DPI (30% faster than 500 DPI) |
| **Single-pass OCR** | Eliminates redundant PDF conversions |
| **Page Classification** | Skips boilerplate pages |

### Typical Processing Times

| Scenario | Time |
|----------|------|
| **First upload (23-page PDF)** | ~100-120 seconds |
| **Cached upload (same PDF)** | ~0.2 seconds |
| **Simple PDF (3-5 pages)** | ~15-30 seconds |
| **Excel/CSV files** | ~1-2 seconds |

---

## Quick Start

### Prerequisites

- **Python 3.8+**
- **MongoDB 4.0+** (optional, for data persistence)
- **Tesseract OCR** (required for scanned PDFs)
- **Poppler** (required for PDF processing)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/harshwaladvisory/Bank_Transaction_Posting_Tool.git
   cd Bank_Transaction_Posting_Tool
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install OCR dependencies:**

   **Windows:**
   - Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - Download and extract [Poppler](https://github.com/oschwartz10612/poppler-windows/releases)
   - Update paths in `config.py`:
     ```python
     TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     POPPLER_PATH = r'C:\path\to\poppler\bin'
     ```

4. **Set environment variables** (production):
   ```bash
   export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
   export MONGODB_URI="mongodb://localhost:27017/"
   export MONGODB_DATABASE="bank_posting_tool"
   export PORT=8590
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Open in browser:**
   ```
   http://localhost:8590
   ```

---

## Project Structure

```
Bank_Transaction_Posting_Tool/
├── app.py                      # Flask web interface
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── parsers/                    # Bank statement parsing
│   ├── universal_parser.py     # Auto-detect and route
│   ├── smart_parser.py         # Template-based parser (primary)
│   ├── ai_parser.py            # Enhanced regex fallback
│   ├── llm_parser.py           # LLM parser (optional, disabled)
│   ├── pdf_parser.py           # PDF extraction
│   └── excel_parser.py         # Excel/CSV parsing
│
├── classifiers/                # Transaction classification
│   ├── classification_engine.py # Main orchestrator
│   ├── keyword_classifier.py    # Keyword rules
│   ├── vendor_matcher.py        # Vendor matching
│   └── customer_matcher.py      # Customer/Grant matching
│
├── processors/                 # Entry generation
│   ├── module_router.py        # Route to CR/CD/JV
│   ├── entry_builder.py        # Build journal entries
│   └── output_generator.py     # Generate Excel files
│
├── config/                     # Bank templates
│   └── bank_templates.json     # Bank-specific parsing rules
│
├── data/                       # Data files
│   ├── keywords.json           # Classification rules
│   ├── vendors.json            # Vendor master list
│   ├── customers.json          # Customer list
│   └── ocr_cache/              # Cached OCR results
│
└── logs/                       # Audit trail logs
```

---

## Bank Templates

Add new bank support by editing `config/bank_templates.json`:

```json
{
  "banks": {
    "NewBank": {
      "identifiers": ["New Bank", "newbank.com"],
      "requires_ocr": true,
      "transaction_patterns": [
        {
          "name": "standard",
          "pattern": "^(\\d{1,2}/\\d{1,2})\\s+(.+?)\\s+([\\d,]+\\.\\d{2})$",
          "groups": {"date": 1, "description": 2, "amount": 3},
          "type": "auto"
        }
      ],
      "deposit_keywords": ["DEPOSIT", "CREDIT"],
      "withdrawal_keywords": ["CHECK", "DEBIT", "FEE"]
    }
  }
}
```

---

## GL Code Assignments

### Automatic High-Confidence Assignments

| Transaction Type | GL Code | Confidence |
|-----------------|---------|------------|
| SERVICE FEE | 6100 | High (95%) |
| INTEREST | 4600 | High (98%) |
| CHECK #XXXX | 7300 | High (95%) |
| DEPOSIT | 7900 | Medium |

### Default GL Mappings

Configured in `config/bank_templates.json` under `default_gl_mappings`:

```json
{
  "deposits": {
    "HUD": {"gl": "3001", "fund": "NAHASDA"},
    "INTEREST": {"gl": "9010", "fund": "General"}
  },
  "withdrawals": {
    "PAYROLL": {"gl": "6600", "fund": "General"},
    "SERVICE FEE": {"gl": "6100", "fund": "General"}
  }
}
```

---

## API Endpoints

### Health & Status
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Health check + MongoDB status |

### Transactions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/transactions` | GET | List all transactions |
| `/api/transactions` | POST | Create transaction |
| `/api/transactions/<id>` | PUT | Update transaction |
| `/api/transactions/<id>` | DELETE | Delete transaction |

### Output Files
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/output-files` | GET | List generated files |
| `/download/<filename>` | GET | Download single file |
| `/download_all_zip` | GET | Download all as ZIP |

---

## Troubleshooting

### "Processing takes too long"

**First-time PDF processing** requires OCR which takes ~100 seconds for a 23-page PDF. Subsequent uploads of the same file use cached OCR results and complete in <1 second.

To clear the cache:
```bash
rm -rf data/ocr_cache/*
```

### "No transactions found"

1. Check file format (.pdf, .xlsx, .xls, .csv)
2. Verify the bank is supported (check console for detected bank)
3. For scanned PDFs, ensure Tesseract and Poppler are installed
4. Check `config.py` for correct OCR paths

### "OCR not working"

1. Install Tesseract OCR
2. Install Poppler
3. Update paths in `config.py`:
   ```python
   TESSERACT_CMD = r'C:\path\to\tesseract.exe'
   POPPLER_PATH = r'C:\path\to\poppler\bin'
   ```

### "Garbage vendor names on checks"

The tool validates vendor names extracted from check images. If OCR quality is poor, vendor names are omitted rather than showing garbage text. This is intentional behavior.

### "MongoDB not available"

MongoDB is optional. The tool works without it but won't persist data across restarts.

To use MongoDB:
1. Install and start MongoDB: `mongod`
2. Set environment variable: `export MONGODB_URI="mongodb://localhost:27017/"`

---

## Configuration

### config.py Settings

```python
# Date format
DATE_FORMAT = "%m/%d/%Y"

# Default GL codes
DEFAULT_BANK_GL = '1070'
DEFAULT_FUND_CODE = '1000'

# Confidence thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.40

# OCR paths (customize for your system)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\path\to\poppler\bin'
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Production | Auto-generated | Flask session secret |
| `MONGODB_URI` | No | localhost:27017 | MongoDB connection |
| `PORT` | No | 8590 | Server port |
| `FLASK_DEBUG` | No | True | Debug mode |

---

## Version History

### v2.2.0 (December 2025)
- **Performance Optimizations**
  - OCR caching with file-hash based storage (2000x faster on repeat)
  - Reduced DPI from 500 to 350 (30% faster)
  - Single-pass OCR processing
  - Smart page classification
- **Vendor Extraction Improvements**
  - Added vendor name validation to filter OCR garbage
  - Clean "CHECK #XXXX" format when vendor cannot be extracted
  - Known vendor pattern matching
- **Parser Improvements**
  - Multi-year statement handling for Farmers Bank
  - Statement period extraction for all banks
  - Improved duplicate detection
- **Classification Enhancements**
  - High-confidence bank transaction detection (SERVICE FEE, INTEREST)
  - INTEREST at 98% confidence with GL 4600
  - SERVICE FEE at 95% confidence with GL 6100

### v2.1.0 (December 2025)
- Smart parser with bank templates
- ChromaDB learning module
- Multiple bank format support
- Fixed DEPOSIT/WITHDRAWAL classification

### v2.0.0 (December 2025)
- Duplicate transaction detection
- MongoDB integration
- Concurrent user support
- Security hardening

---

## Security

### Best Practices

1. **Secret Key**: Set `SECRET_KEY` environment variable in production
2. **MongoDB**: Use authentication in production
3. **HTTPS**: Use reverse proxy (Nginx/Apache) for SSL
4. **Firewall**: Restrict MongoDB port to localhost

---

## Technologies

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MongoDB](https://www.mongodb.com/) - Database (optional)
- [pandas](https://pandas.pydata.org/) - Data processing
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF parsing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [pdf2image](https://github.com/Belval/pdf2image) - PDF to image conversion

---

## Support

**Email**: support@harshwalconsulting.com

When reporting issues, include:
1. Python version (`python --version`)
2. Error message (full stack trace)
3. Steps to reproduce
4. Sample file (redact sensitive data)

---

## License

**Proprietary** - Harshwal Consulting Services

All rights reserved.

---

**Version:** 2.2.0
**Python Required:** 3.8+
**Default Port:** 8590

Made by Harshwal Consulting Services
