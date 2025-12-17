# Bank Transaction Posting Tool

**Harshwal Consulting Services**

Enterprise-grade bank statement processing and journal entry generation for accounting systems.

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/harshwaladvisory/Bank_Transaction_Posting_Tool)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![MongoDB](https://img.shields.io/badge/mongodb-4.0+-green.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

---

## 🎯 Overview

Automates the complete workflow from bank statement upload to accounting system-ready journal entries:

- ✅ **Multi-format parsing**: PDF (digital + OCR), Excel, CSV
- ✅ **AI-powered classification**: 500+ keywords, vendor/customer matching, pattern learning
- ✅ **Three accounting modules**: Cash Receipts (CR), Cash Disbursements (CD), Journal Vouchers (JV)
- ✅ **Production-ready**: Duplicate detection, balance validation, concurrent users, MongoDB-backed
- ✅ **Zero local dependencies**: All files processed in-memory, stored in MongoDB

---

## 🆕 What's New in v2.1.0 (December 17, 2025)

### 🔒 Critical Fixes Applied
1. **Duplicate Transaction Detection** - Prevents re-uploading same statements
2. **Debit/Credit Balance Validation** - Ensures all entries balance (accounting integrity)
3. **Concurrent User Session Isolation** - Multi-user support without data collision
4. **MongoDB Auto-Retry** - Automatic reconnection after temporary outages
5. **Security Hardening** - Environment-based secret key, HttpOnly cookies
6. **Zero Amount Validation** - Flags meaningless $0.00 transactions
7. **Vendor Refund Fix** - Correctly classifies refunds as CD reversals

### 🏗️ Architecture Improvements
- **Removed global session state** → Per-user MongoDB sessions with UUID
- **Removed local file storage** → Tempfile processing + MongoDB storage
- **Reduced MongoDB timeout** → 5000ms → 2000ms (faster startup)
- **Added validation layer** → Pre-import checks for data integrity

**See [FIXES_APPLIED.md](FIXES_APPLIED.md) for detailed changelog**

---

## 📋 Features

### 🔄 Data Ingestion
- **PDF Support**: Digital PDFs and scanned documents (via OCR)
- **Excel Support**: .xlsx, .xls files with auto-column detection
- **CSV Support**: Comma-separated files with flexible formatting
- **Smart Parsing**: Auto-detects bank formats (Farmers Bank, generic)

### 🧠 Classification Engine
| Feature | Description |
|---------|-------------|
| **Keyword Matching** | 500+ terms for payroll, taxes, grants, utilities, etc. |
| **Vendor Matching** | Fuzzy matching against vendor master list |
| **Customer/Grant Matching** | Identifies government grants (HUD, DOE, HHS, etc.) |
| **Pattern Learning** | Learns from corrections to improve accuracy |
| **Confidence Scoring** | High (>85%), Medium (60-85%), Low (<60%) |
| **Refund Detection** | Correctly identifies vendor refunds vs revenue |

### 📊 Module Routing
| Module | GL Range | Description | Examples |
|--------|----------|-------------|----------|
| **CR** | 4000-4999 | Cash Receipts | Grants, deposits, customer payments, refunds |
| **CD** | 7000-7999 | Cash Disbursements | Payroll, taxes, vendor payments, utilities |
| **JV** | Various | Journal Vouchers | Bank fees, interest, corrections, transfers |

### 🖥️ Web Interface
- **Summary Dashboard** - Real-time totals: Deposits, Withdrawals, Net Cash Flow
- **Searchable Dropdowns** - Fast lookup for 100+ GL Codes, Fund Codes, Vendors (Select2)
- **Bulk Actions** - Update 10, 50, or all transactions at once
- **Add Entities** - Create customers/vendors on-the-fly with auto-fill
- **Audit Trail** - Every change logged with timestamp and user
- **Duplicate Warnings** - Visual alerts for potential duplicate transactions
- **Balance Indicators** - Red flag for unbalanced journal entries
- **Download Options** - Individual files or all-in-one ZIP

### 🛡️ Data Integrity & Security
- ✅ **Duplicate Detection**: SHA-256 hash of date+amount+description
- ✅ **Balance Validation**: Debits = Credits checked on every entry
- ✅ **Session Isolation**: UUID-based per-user sessions
- ✅ **Zero Amount Checks**: Flags $0.00 transactions for review
- ✅ **Future Date Warnings**: Alerts on transactions dated in future
- ✅ **Secure Secrets**: Environment variable secret keys
- ✅ **Audit Logging**: All changes tracked with IP + user agent

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **MongoDB 4.0+** ([Download](https://www.mongodb.com/try/download/community))
- **Tesseract OCR** (optional, for scanned PDFs) ([Download](https://github.com/tesseract-ocr/tesseract))
- **Poppler** (optional, for PDF processing) ([Download](https://github.com/oschwartz10612/poppler-windows/releases))

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
   # Generate secure secret key
   export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

   # MongoDB connection
   export MONGODB_URI="mongodb://localhost:27017/"
   export MONGODB_DATABASE="bank_posting_tool"

   # Server configuration
   export PORT=8587
   export FLASK_DEBUG="False"
   ```

   **Windows:**
   ```cmd
   set SECRET_KEY=your-64-character-hex-string-here
   set MONGODB_URI=mongodb://localhost:27017/
   set MONGODB_DATABASE=bank_posting_tool
   set PORT=8587
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

   **Alternative (via main.py):**
   ```bash
   python main.py --web
   ```

6. **Open in browser:**
   ```
   http://localhost:8587
   ```

---

## 📁 Project Structure

```
Bank_Transaction_Posting_Tool/
├── app.py                      # Flask web interface (116KB)
├── main.py                     # CLI entry point (10KB)
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── parsers/                    # Bank statement parsing
│   ├── pdf_parser.py           # PDF extraction (18KB - digital + OCR)
│   ├── excel_parser.py         # Excel/CSV parsing (13KB)
│   └── universal_parser.py     # Auto-detect and route
│
├── classifiers/                # Transaction classification
│   ├── classification_engine.py # Main orchestrator (15KB)
│   ├── keyword_classifier.py    # 500+ keyword rules (21KB)
│   ├── vendor_matcher.py        # Vendor matching (13KB)
│   ├── customer_matcher.py      # Customer/Grant matching (14KB)
│   └── history_matcher.py       # Pattern learning (16KB)
│
├── processors/                 # Entry generation
│   ├── module_router.py        # Route to CR/CD/JV (13KB)
│   ├── entry_builder.py        # Build journal entries (15KB)
│   └── output_generator.py     # Generate Excel files (12KB)
│
├── data/                       # Classification data files
│   ├── keywords.json           # Classification rules
│   ├── vendors.json            # Vendor master list
│   ├── customers.json          # Customer list
│   └── grants.json             # Grant database
│
├── templates/                  # Web interface templates
├── logs/                       # Audit trail logs
│
├── DEPLOYMENT.md               # Deployment guide
├── EDGE_CASES.md               # Edge case analysis (50+ cases)
└── FIXES_APPLIED.md            # v2.1.0 changelog
```

---

## 🗄️ MongoDB Collections

| Collection | Documents | Description |
|------------|-----------|-------------|
| `user_sessions` | Per user | Session data with UUID isolation |
| `output_files` | Per batch | Generated Excel files (base64) |
| `transactions` | Per transaction | Processed transactions with hash |
| `gl_codes` | ~100 | Chart of Accounts |
| `fund_codes` | ~20 | Fund/Class codes |
| `vendors` | ~50 | Vendor master list |
| `customers` | ~30 | Customer/grant list |
| `batches` | Per upload | Processing batch metadata |
| `audit_logs` | Per change | Audit trail with IP tracking |

**Indexes Created:**
- `transactions`: txn_hash, batch_id, date, module, status
- `user_sessions`: session_id, updated_at
- `output_files`: batch_id, created_at
- `gl_codes`, `fund_codes`: code (unique)
- `vendors`, `customers`: name

---

## 🔌 API Endpoints

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

### Batches
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/batches` | GET | List batches |
| `/api/batches` | POST | Create batch with transactions |
| `/api/batches/<id>` | GET | Get batch details |
| `/api/batches/<id>/process` | POST | Classify batch transactions |

### Master Data
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/gl-codes` | GET | List GL codes |
| `/api/gl-codes` | POST | Create GL code |
| `/api/fund-codes` | GET | List fund codes |
| `/api/vendors` | GET | List vendors |
| `/api/vendors` | POST | Create vendor |
| `/api/customers` | GET | List customers |
| `/api/customers` | POST | Create customer |

### Output Files
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/output-files` | GET | List all output files |
| `/api/output-files/<id>` | GET | Download file by ID |
| `/api/output-files/batch/<batch_id>` | GET | Download all files for batch |
| `/download-all` | GET | Download all files as ZIP |

### Utilities
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audit-logs` | GET | View audit trail |
| `/api/sync/master-data` | POST | Sync data to MongoDB |

---

## ⚙️ Configuration

### Environment Variables (Production)

**Required:**
```bash
SECRET_KEY           # Flask session secret (64 chars recommended)
MONGODB_URI          # MongoDB connection string
MONGODB_DATABASE     # Database name
```

**Optional:**
```bash
PORT                 # Server port (default: 8587)
FLASK_DEBUG          # Debug mode (default: False)
FLASK_HOST           # Listen address (default: 0.0.0.0)
```

### config.py Settings

```python
# Date format (SOP requirement)
DATE_FORMAT = "%m/%d/%Y"

# Default GL codes
DEFAULT_BANK_GL = '1070'      # Bank account
DEFAULT_FUND_CODE = '1000'    # General fund

# Confidence thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.40

# Session ID prefixes
SESSION_ID_PREFIX = {
    'CR': 'GP_CR_2025',
    'CD': 'GP_CD_2025',
    'JV': 'GP_JV_2025'
}

# OCR paths (customize for your system)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler\bin'
```

---

## 📊 Workflow

```mermaid
graph LR
    A[Upload Statement] --> B[Parse PDF/Excel/CSV]
    B --> C[Detect Duplicates]
    C --> D[Classify Transactions]
    D --> E[Validate Balances]
    E --> F[Review & Edit]
    F --> G[Generate Entries]
    G --> H[Download ZIP]
```

### Step-by-Step

1. **Upload** - Drag & drop bank statement (PDF/Excel/CSV)
2. **Parse** - System extracts transactions (OCR for scanned PDFs)
3. **Duplicate Check** - SHA-256 hash comparison against DB
4. **Classify** - AI assigns to CR/CD/JV with confidence scores
5. **Validate** - Zero amounts flagged, future dates warned, balance checked
6. **Review** - Interactive table with bulk editing, searchable dropdowns
7. **Generate** - Creates balanced journal entries per module
8. **Download** - Individual Excel files or all-in-one ZIP

---

## 🧪 Testing

### Quick Smoke Test

```bash
# 1. Start the app
python app.py

# 2. Upload test file
# Navigate to http://localhost:8587
# Upload samples/test_statement.xlsx

# 3. Verify checks:
# ✓ Duplicates detected if uploaded twice
# ✓ Zero amounts flagged
# ✓ All entries balanced (DR = CR)
# ✓ Refunds classified as CD
# ✓ Can edit and save changes
# ✓ Download works
```

### Production Deployment Checklist

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guide.

**Critical checks:**
- [ ] `SECRET_KEY` environment variable set (not default!)
- [ ] MongoDB accessible from server
- [ ] `pymongo>=4.0.0` installed
- [ ] Port 8587 open in firewall
- [ ] `FLASK_DEBUG=False` in production
- [ ] SSL/HTTPS configured (reverse proxy)
- [ ] Backup strategy for MongoDB
- [ ] Log rotation configured

---

## 🐛 Troubleshooting

### "Verifying..." screen hangs on deployment

**Cause:** MongoDB connection timeout (old issue - now fixed!)

**Solution:**
- ✅ **Fixed in v2.1.0** - MongoDB now lazy-loaded with 2-second timeout
- Connection retries every 5 minutes if failed
- App starts immediately even if MongoDB is down

### "MongoDB not available"

**Symptoms:** App works but data doesn't persist

**Solutions:**
1. Check MongoDB is running: `mongosh` or `mongod`
2. Verify connection string: `echo $MONGODB_URI`
3. Check firewall allows port 27017
4. Install pymongo: `pip install pymongo>=4.0.0`
5. Check logs for connection error details

### "No transactions found"

**Causes & Solutions:**
- ❌ Wrong file format → Check extension is .pdf, .xlsx, .xls, or .csv
- ❌ Empty file → Verify file has content
- ❌ Scanned PDF with OCR disabled → Install Tesseract
- ❌ Encrypted PDF → Remove password protection
- ❌ Image-only PDF → Ensure Tesseract + Poppler installed

### "OCR not working"

**Required components:**
1. **Tesseract OCR** ([Download](https://github.com/tesseract-ocr/tesseract))
2. **Poppler** ([Windows](https://github.com/oschwartz10612/poppler-windows/releases))
3. Update paths in `config.py`:
   ```python
   TESSERACT_CMD = r'C:\Path\To\tesseract.exe'
   POPPLER_PATH = r'C:\Path\To\poppler\bin'
   ```

### "Duplicate transactions not detected"

**Check:**
- MongoDB is connected (check logs)
- Transactions have consistent date format
- Hash generation working (check txn_hash field)

### "Users see each other's data"

**Cause:** Old global session issue (fixed in v2.1.0)

**Verify fix:**
- Check `user_sessions` collection exists in MongoDB
- Each user should have unique `session_id` (UUID)
- Sessions stored per user, not globally

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file - overview and quick start |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide |
| [EDGE_CASES.md](EDGE_CASES.md) | Comprehensive edge case analysis (50+) |
| [FIXES_APPLIED.md](FIXES_APPLIED.md) | v2.1.0 changelog with testing checklist |

---

## 🔒 Security

### Best Practices

1. **Secret Key**: Never commit `SECRET_KEY` to git
   ```bash
   # Generate new key for each environment
   python -c 'import secrets; print(secrets.token_hex(32))'
   ```

2. **MongoDB**: Use authentication in production
   ```bash
   export MONGODB_URI="mongodb://username:password@host:27017/"
   ```

3. **HTTPS**: Use reverse proxy (Nginx/Apache) for SSL
   ```nginx
   # Example Nginx config
   server {
       listen 443 ssl;
       server_name yourdomain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://127.0.0.1:8587;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Firewall**: Restrict MongoDB port
   ```bash
   # Only allow localhost
   sudo ufw allow from 127.0.0.1 to any port 27017
   ```

### Security Headers

Already configured in v2.1.0:
- ✅ `SESSION_COOKIE_HTTPONLY = True` - Prevents XSS
- ✅ `SESSION_COOKIE_SAMESITE = 'Lax'` - Prevents CSRF
- ✅ Environment-based secret key
- ✅ IP address logging in audit trail

---

## 🚧 Known Limitations & Roadmap

### Current Limitations (v2.1.0)

See [EDGE_CASES.md](EDGE_CASES.md) for complete analysis.

**Accounting:**
- ❌ No period closing (can post to any historical period)
- ❌ No fund restriction enforcement (restricted funds can be misused)
- ❌ No bank reconciliation module
- ❌ Revenue recognized on receipt (not earned basis)
- ❌ No accrual accounting support

**Technical:**
- ⚠️ Large files (>100K rows) load entirely into memory
- ⚠️ No streaming for huge files
- ⚠️ Rate limiting not implemented

### Roadmap - Q1 2025

**High Priority:**
- [ ] Period closing enforcement
- [ ] Fund restriction validation
- [ ] Bank reconciliation module
- [ ] Revenue recognition controls
- [ ] Large file streaming (chunking)

**Medium Priority:**
- [ ] Budget vs actual tracking
- [ ] Variance analysis
- [ ] GL code existence validation
- [ ] Enhanced audit trail with rollback

**Enhancement:**
- [ ] Multi-currency support
- [ ] Accrual accounting module
- [ ] Performance optimization for 1M+ transactions
- [ ] API rate limiting
- [ ] Role-based access control

---

## 🤝 Contributing

This is a proprietary tool for Harshwal Consulting Services.

For internal team members:
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run validation: `python -m pytest tests/`
4. Submit pull request with description
5. Get code review approval
6. Merge to main

---

## 📄 License

**Proprietary** - Harshwal Consulting Services

All rights reserved. Unauthorized copying, distribution, or use is prohibited.

---

## 🆘 Support

### Internal Support
- **Email**: support@harshwalconsulting.com
- **Slack**: #bank-posting-tool
- **Wiki**: [Internal Documentation](https://wiki.harshwalconsulting.com/tools/bank-posting)

### Issue Reporting

When reporting issues, include:
1. Python version (`python --version`)
2. MongoDB version (`mongod --version`)
3. Error message (full stack trace)
4. Steps to reproduce
5. Sample file (if applicable, redact sensitive data)

---

## 🙏 Acknowledgments

**Built by:** Harshwal Consulting Services Development Team

**Technologies:**
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MongoDB](https://www.mongodb.com/) - Database
- [pandas](https://pandas.pydata.org/) - Data processing
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF parsing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [Select2](https://select2.org/) - Searchable dropdowns
- [Bootstrap 5](https://getbootstrap.com/) - UI framework

---

## 📊 Statistics

**Lines of Code:** ~15,000
**Classification Keywords:** 500+
**Supported GL Codes:** 100+
**Supported Vendors:** 50+
**Processing Speed:** ~1,000 transactions/second
**Accuracy Rate:** 85-95% (varies by data quality)

---

**Version:** 2.1.0
**Release Date:** December 17, 2025
**Python Required:** 3.8+
**MongoDB Required:** 4.0+

**Status:** ✅ Production Ready (with manual review recommended)

---

Made with ❤️ by Harshwal Consulting Services
