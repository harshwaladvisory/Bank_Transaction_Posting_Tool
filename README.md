# Bank Transaction Posting Tool

**Harshwal Consulting Services**

Enterprise-grade bank statement processing and journal entry generation for accounting systems.

---

## Overview

Automates the complete workflow from bank statement upload to accounting system-ready journal entries:

- **Multi-format parsing**: PDF (digital + OCR), Excel, CSV
- **AI-powered classification**: 500+ keywords, vendor/customer matching, pattern learning
- **Three accounting modules**: Cash Receipts (CR), Cash Disbursements (CD), Journal Vouchers (JV)
- **Production-ready**: Duplicate detection, balance validation, concurrent users, MongoDB-backed
- **Zero local dependencies**: All files processed in-memory, stored in MongoDB

---

## Features

### Data Ingestion
- **PDF Support**: Digital PDFs and scanned documents (via OCR)
- **Excel Support**: .xlsx, .xls files with auto-column detection
- **CSV Support**: Comma-separated files with flexible formatting
- **Smart Parsing**: Auto-detects bank formats (Truist, PNC, CrossFirst, Sovereign, Farmers, etc.)

### Classification Engine
| Feature | Description |
|---------|-------------|
| **Keyword Matching** | 500+ terms for payroll, taxes, grants, utilities, etc. |
| **Vendor Matching** | Fuzzy matching against vendor master list |
| **Customer/Grant Matching** | Identifies government grants (HUD, DOE, HHS, etc.) |
| **Pattern Learning** | ChromaDB-based learning from corrections |
| **Confidence Scoring** | High (>85%), Medium (60-85%), Low (<60%) |
| **Refund Detection** | Correctly identifies vendor refunds vs revenue |

### Module Routing
| Module | GL Range | Description | Examples |
|--------|----------|-------------|----------|
| **CR** | 4000-4999 | Cash Receipts | Grants, deposits, customer payments, refunds |
| **CD** | 7000-7999 | Cash Disbursements | Payroll, taxes, vendor payments, utilities |
| **JV** | Various | Journal Vouchers | Bank fees, interest, corrections, transfers |

### Web Interface
- **Summary Dashboard** - Real-time totals: Deposits, Withdrawals, Net Cash Flow
- **Searchable Dropdowns** - Fast lookup for 100+ GL Codes, Fund Codes, Vendors
- **Bulk Actions** - Update 10, 50, or all transactions at once
- **Add Entities** - Create customers/vendors on-the-fly with auto-fill
- **Audit Trail** - Every change logged with timestamp and user
- **Download Options** - Individual files or all-in-one ZIP

---

## Quick Start

### Prerequisites
- **Python 3.8+**
- **MongoDB 4.0+**
- **Tesseract OCR** (optional, for scanned PDFs)
- **Poppler** (optional, for PDF processing)

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

3. **Set environment variables** (production):
   ```bash
   export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
   export MONGODB_URI="mongodb://localhost:27017/"
   export MONGODB_DATABASE="bank_posting_tool"
   export PORT=8590
   export FLASK_DEBUG="False"
   ```

   **Windows:**
   ```cmd
   set SECRET_KEY=your-64-character-hex-string-here
   set MONGODB_URI=mongodb://localhost:27017/
   set MONGODB_DATABASE=bank_posting_tool
   set PORT=8590
   set FLASK_DEBUG=False
   ```

4. **Start MongoDB** (if not running):
   ```bash
   mongod
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
├── main.py                     # CLI entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── parsers/                    # Bank statement parsing
│   ├── pdf_parser.py           # PDF extraction (digital + OCR)
│   ├── excel_parser.py         # Excel/CSV parsing
│   ├── universal_parser.py     # Auto-detect and route
│   ├── smart_parser.py         # Smart parser with templates
│   ├── template_parser.py      # Template-based parsing
│   └── ai_parser.py            # AI-powered parsing
│
├── classifiers/                # Transaction classification
│   ├── classification_engine.py # Main orchestrator
│   ├── keyword_classifier.py    # 500+ keyword rules
│   ├── vendor_matcher.py        # Vendor matching
│   ├── customer_matcher.py      # Customer/Grant matching
│   └── history_matcher.py       # Pattern learning
│
├── processors/                 # Entry generation
│   ├── module_router.py        # Route to CR/CD/JV
│   ├── entry_builder.py        # Build journal entries
│   └── output_generator.py     # Generate Excel files
│
├── learning/                   # ChromaDB learning module
│   └── chroma_learner.py       # GL code suggestions
│
├── data/                       # Classification data files
│   ├── keywords.json           # Classification rules
│   ├── vendors.json            # Vendor master list
│   ├── customers.json          # Customer list
│   └── grants.json             # Grant database
│
├── config/                     # Bank templates
│   └── bank_templates.json     # Bank-specific parsing rules
│
└── logs/                       # Audit trail logs
```

---

## API Endpoints

### Health & Status
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Health check + MongoDB connection status |
| `/api/stats` | GET | Dashboard statistics |

### Transactions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/transactions` | GET | List all transactions |
| `/api/transactions` | POST | Create transaction |
| `/api/transactions/<id>` | GET | Get transaction by ID |
| `/api/transactions/<id>` | PUT | Update transaction |
| `/api/transactions/<id>` | DELETE | Delete transaction |

### Master Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/gl-codes` | GET | List GL codes |
| `/api/gl-codes` | POST | Create GL code |
| `/api/fund-codes` | GET | List fund codes |
| `/api/vendors` | GET | List vendors |
| `/api/customers` | GET | List customers |

---

## Configuration

### Environment Variables

**Required:**
```bash
SECRET_KEY           # Flask session secret (64 chars recommended)
MONGODB_URI          # MongoDB connection string
MONGODB_DATABASE     # Database name
```

**Optional:**
```bash
PORT                 # Server port (default: 8590)
FLASK_DEBUG          # Debug mode (default: False)
FLASK_HOST           # Listen address (default: 0.0.0.0)
```

### config.py Settings

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

# OCR paths (customize for your system)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler\bin'
```

---

## Supported Banks

The tool supports the following bank statement formats:

| Bank | Format | OCR Support |
|------|--------|-------------|
| Truist | PDF | Yes |
| PNC | PDF | Yes |
| CrossFirst | PDF | Yes |
| Sovereign | PDF | Yes |
| Farmers | PDF | Yes |
| Generic | PDF/Excel/CSV | Yes |

---

## Troubleshooting

### "MongoDB not available"
1. Check MongoDB is running: `mongod`
2. Verify connection string: `echo $MONGODB_URI`
3. Check firewall allows port 27017

### "No transactions found"
- Check file format is .pdf, .xlsx, .xls, or .csv
- Verify file has content
- For scanned PDFs, ensure Tesseract is installed

### "OCR not working"
1. Install Tesseract OCR
2. Install Poppler
3. Update paths in `config.py`

### "Port already in use"
```bash
# Change port via environment variable
export PORT=8591

# Or find and kill existing process
netstat -ano | findstr :8590
taskkill /PID <PID> /F
```

---

## Security

### Best Practices

1. **Secret Key**: Never commit `SECRET_KEY` to git
   ```bash
   python -c 'import secrets; print(secrets.token_hex(32))'
   ```

2. **MongoDB**: Use authentication in production
   ```bash
   export MONGODB_URI="mongodb://username:password@host:27017/"
   ```

3. **HTTPS**: Use reverse proxy (Nginx/Apache) for SSL

4. **Firewall**: Restrict MongoDB port to localhost only

---

## Version History

### v2.1.0 (December 2025)
- Fixed session_data error in results route
- Added word boundary matching for transaction classification
- Added smart_parser, template_parser, and ai_parser modules
- Added ChromaDB learning module for GL code suggestions
- Changed default port to 8590
- Fixed DEPOSIT/WITHDRAWAL misclassification
- Added support for multiple bank formats

### v2.0.0 (December 2025)
- Duplicate transaction detection
- Debit/Credit balance validation
- Concurrent user session isolation
- MongoDB auto-retry mechanism
- Security hardening
- Zero amount validation
- Vendor refund fix

---

## Support

### Internal Support
- **Email**: support@harshwalconsulting.com

### Issue Reporting
When reporting issues, include:
1. Python version (`python --version`)
2. MongoDB version (`mongod --version`)
3. Error message (full stack trace)
4. Steps to reproduce
5. Sample file (if applicable, redact sensitive data)

---

## License

**Proprietary** - Harshwal Consulting Services

All rights reserved. Unauthorized copying, distribution, or use is prohibited.

---

## Technologies

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MongoDB](https://www.mongodb.com/) - Database
- [pandas](https://pandas.pydata.org/) - Data processing
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF parsing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [ChromaDB](https://www.trychroma.com/) - Vector database for learning

---

**Version:** 2.1.0
**Python Required:** 3.8+
**MongoDB Required:** 4.0+
**Default Port:** 8590

Made by Harshwal Consulting Services
