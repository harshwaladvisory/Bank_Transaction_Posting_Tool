# Bank Transaction Posting Tool

**Harshwal Consulting Services**

Automates bank statement processing and journal entry generation for accounting systems.

## 🎯 Overview

This tool processes bank statements (PDF, Excel, CSV) and automatically:
- Extracts transactions using OCR (for scanned PDFs) or direct parsing
- Classifies transactions using 500+ keywords, vendor matching, and pattern recognition
- Routes transactions to appropriate accounting modules (Cash Receipts, Cash Disbursements, Journal Vouchers)
- Generates formatted import files for MIP, QuickBooks Desktop, and other systems
- Stores output files in MongoDB (no local storage dependency)

## 📋 Features

### Data Ingestion
- **PDF Support**: Digital PDFs and scanned documents (via OCR)
- **Excel Support**: .xlsx, .xls files with auto-column detection
- **CSV Support**: Comma-separated files with flexible formatting

### Classification Engine
- **Keyword Matching**: 500+ terms for payroll, taxes, grants, utilities, etc.
- **Vendor Matching**: Match against vendor master list
- **Customer/Grant Matching**: Identify grant drawdowns (HUD, DOE, HHS, etc.)
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
- **Download All as ZIP** option available

### Web Interface Features
- **Summary Dashboard** - Total Deposits, Withdrawals, Net Cash Flow displayed at top
- **Searchable Dropdowns** - Quick search for GL Codes, Fund Codes, Customers/Vendors using Select2
- **Bulk Actions** - Update multiple transactions at once
- **Add Customer/Vendor** - Add new entities with searchable GL and Fund selection
- **Audit Trail** - Track all changes made during review
- **MongoDB Storage** - All output files stored in database (no local file dependency)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (running locally or remote)
- Tesseract OCR (optional, for scanned PDFs)
- Poppler (optional, for PDF processing)

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

3. **Start MongoDB** (if not running):
```bash
mongod
```

4. **Run the application:**
```bash
python app.py
```

5. **Open in browser:**
```
http://127.0.0.1:8587
```

## 📁 Project Structure

```
Bank_Transaction_Posting_Tool/
├── app.py                  # Flask web interface
├── main.py                 # CLI entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
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
│   └── customers.json      # Customer list
│
├── logs/                   # Audit trail
└── uploads/                # Uploaded files (web)
```

## 🗄️ MongoDB Collections

| Collection | Description |
|------------|-------------|
| `output_files` | Generated Excel files (stored as base64) |
| `transactions` | Processed transactions |
| `gl_codes` | Chart of Accounts |
| `fund_codes` | Fund/Class codes |
| `vendors` | Vendor master list |
| `customers` | Customer list |
| `batches` | Processing batches |
| `audit_logs` | Audit trail |

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Health check & MongoDB status |
| `/api/output-files` | GET | List all output files |
| `/api/output-files/<id>` | GET | Download file by ID |
| `/api/output-files/batch/<batch_id>` | GET | Get files by batch |
| `/api/transactions` | GET/POST | List or create transactions |
| `/api/gl-codes` | GET | List GL codes |
| `/api/fund-codes` | GET | List fund codes |
| `/api/vendors` | GET/POST | List or create vendors |
| `/api/customers` | GET/POST | List or create customers |

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

# MongoDB settings (via environment variables)
MONGODB_URI = 'mongodb://localhost:27017/'
MONGODB_DATABASE = 'bank_posting_tool'

# OCR paths (Windows)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler\bin'
```

## 📊 Workflow

1. **Upload** - Upload bank statement (PDF/Excel/CSV)
2. **Parse** - System extracts transactions automatically
3. **Classify** - AI classifies transactions into CR/CD/JV modules
4. **Review** - Review and edit classifications in web interface
5. **Generate** - Generate import files for accounting system
6. **Download** - Download individual files or all as ZIP

## 🐛 Troubleshooting

### "MongoDB not available"
- Ensure MongoDB is running: `mongod`
- Check connection string in config.py
- Install pymongo: `pip install pymongo`

### "No transactions found"
- Check file format is correct
- For PDFs, ensure text is selectable
- For scanned PDFs, verify Tesseract is installed

### "OCR not working"
- Install Tesseract OCR
- Install Poppler for PDF conversion
- Update paths in `config.py`

## 📄 License

Proprietary - Harshwal Consulting Services

## 🤝 Support

For questions or issues, contact the development team.

---

**Version**: 2.0.0  
**Last Updated**: December 2024
