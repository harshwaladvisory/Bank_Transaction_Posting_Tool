# 🏦 Bank Transaction Posting Tool

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-brightgreen.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

**Automated Bank Statement Processing & Classification System**

Transform hours of manual accounting work into minutes with AI-powered transaction classification.

![Time Savings](https://img.shields.io/badge/Time%20Savings-85%25-success)
![GL Codes](https://img.shields.io/badge/GL%20Codes-210-blue)
![API Endpoints](https://img.shields.io/badge/API%20Endpoints-25+-purple)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

### The Problem

Accountants spend **2-4 hours** per bank statement manually:
- Typing transactions from PDF into Excel
- Looking up vendors/customers
- Determining GL codes from memory
- Assigning Fund/Class codes
- Formatting for MIP import

### The Solution

This tool automates the entire process:
- **Upload** bank statement (PDF, Excel, or CSV)
- **AI classifies** transactions automatically using 500+ keywords
- **Review** with color-coded confidence levels
- **Export** MIP-ready files in minutes

**Result: 85-90% time savings**

---

## ✨ Features

### Core Features

| Feature | Description |
|---------|-------------|
| 📄 **Multi-Format Parsing** | PDF, Excel (.xlsx, .xls), CSV support |
| 🔍 **OCR Support** | Tesseract OCR for scanned documents |
| 🧠 **AI Classification** | 500+ keywords for auto-categorization |
| 📊 **210 GL Codes** | Complete Chart of Accounts pre-configured |
| 🏷️ **45 Fund Codes** | All programs (NAHASDA, BGCA, BCBS, etc.) |
| 👥 **Auto-Fill** | Vendor/Customer selection auto-fills GL & Fund |
| 📝 **Audit Trail** | Track all changes with timestamps |
| 🍃 **MongoDB Storage** | Persistent data storage |
| 🔌 **REST API** | 25+ endpoints for integration |
| 📥 **MIP Export** | Generate CR, CD, JV import files |

### Classification Modules

- **CR (Cash Receipts)**: Deposits, incoming payments
- **CD (Cash Disbursements)**: Checks, withdrawals, payments
- **JV (Journal Vouchers)**: Bank fees, transfers, adjustments

### Supported Banks

- PNC Bank
- Wells Fargo
- Bank of America
- Truist
- Farmers Bank
- And more...

---

## 🛠️ Technology Stack

### Backend

| Technology | Purpose | Why We Chose It |
|------------|---------|-----------------|
| **Python 3.8+** | Primary language | Best for data processing, excellent libraries |
| **Flask** | Web framework | Lightweight, perfect for internal tools |
| **MongoDB** | Database | Flexible schema for varying transaction formats |
| **pymongo** | MongoDB driver | Official Python driver |

### PDF & Data Processing

| Technology | Purpose | Why We Chose It |
|------------|---------|-----------------|
| **pdfplumber** | PDF text extraction | Preserves layout, handles tables |
| **Tesseract OCR** | Scanned document OCR | Industry-standard, free |
| **openpyxl** | Excel read/write | Full formatting support |
| **pandas** | Data manipulation | Powerful data processing |

### Frontend

| Technology | Purpose | Why We Chose It |
|------------|---------|-----------------|
| **Bootstrap 5** | UI framework | Professional components, responsive |
| **Bootstrap Icons** | Icon library | 1,800+ free icons |
| **Jinja2** | Templating | Built into Flask, dynamic HTML |

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/harshwaladvisory/Bank_Transaction_Posting_Tool.git
cd Bank_Transaction_Posting_Tool
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install MongoDB

Download from [mongodb.com](https://www.mongodb.com/try/download/community) and install with default settings.

### Step 5: Start MongoDB

```bash
# Windows (as service)
net start MongoDB

# Or manually
mongod --dbpath C:\data\db
```

### Step 6: Run Application

```bash
python app.py
```

### Step 7: Access the Tool

- **Web Interface**: http://127.0.0.1:5000
- **API Status**: http://127.0.0.1:5000/api/status

### Step 8: Sync Master Data (First Time)

```bash
# PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/sync/master-data" -Method POST

# Or curl
curl -X POST http://127.0.0.1:5000/api/sync/master-data
```

---

## 🚀 Usage

### Web Interface

1. **Open** http://127.0.0.1:5000 in your browser
2. **Upload** bank statement (PDF, Excel, or CSV)
3. **Review** transactions with color-coded confidence:
   - 🟢 Green = High confidence (auto-classified)
   - 🟡 Yellow = Medium confidence (may need review)
   - 🔴 Red = Low confidence (needs manual input)
4. **Edit** transactions if needed (click row to edit)
5. **Generate** MIP import files
6. **Download** CR, CD, JV files

### Command Line Interface

```bash
python main.py --file statement.pdf --bank PNC
```

### API Usage

```bash
# Check status
curl http://127.0.0.1:5000/api/status

# Get GL codes
curl http://127.0.0.1:5000/api/gl-codes

# Create transaction
curl -X POST http://127.0.0.1:5000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"date":"2024-12-10","description":"Test Payment","amount":-100.00}'
```

---

## 📁 Project Structure

```
Bank_Transaction_Posting_Tool/
│
├── app.py                      # Main Flask application (1873 lines)
├── main.py                     # CLI interface
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
│
├── classifiers/                # AI Classification Modules
│   ├── __init__.py
│   ├── classification_engine.py   # Main orchestrator
│   ├── keyword_classifier.py      # 500+ keyword rules
│   ├── vendor_matcher.py          # Vendor matching
│   ├── customer_matcher.py        # Customer matching
│   └── history_matcher.py         # Pattern learning
│
├── parsers/                    # File Parsing Modules
│   ├── __init__.py
│   ├── universal_parser.py        # Smart router
│   ├── pdf_parser.py              # PDF + OCR parsing
│   └── excel_parser.py            # Excel/CSV parsing
│
├── processors/                 # Data Processing Modules
│   ├── __init__.py
│   ├── module_router.py           # CR/CD/JV routing
│   ├── entry_builder.py           # Accounting entry builder
│   └── output_generator.py        # Excel file generator
│
├── data/                       # JSON Data Files
│   ├── keywords.json              # Classification keywords
│   ├── vendors.json               # Vendor master data
│   ├── customers.json             # Customer master data
│   ├── grants.json                # Grant information
│   └── learned_patterns.json      # ML patterns
│
├── templates/                  # HTML Templates (Jinja2)
│   ├── base.html                  # Base layout
│   ├── index.html                 # Upload page
│   ├── review.html                # Transaction review
│   └── results.html               # Download page
│
├── uploads/                    # Uploaded files (temporary)
│
└── outputs/                    # Generated Excel files
```

---

## 🔌 API Documentation

### Base URL

```
http://127.0.0.1:5000/api
```

### Endpoints

#### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Health check & MongoDB status |
| GET | `/stats` | Dashboard statistics |

#### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | List all transactions |
| POST | `/transactions` | Create new transaction |
| GET | `/transactions/<id>` | Get single transaction |
| PUT | `/transactions/<id>` | Update transaction |
| DELETE | `/transactions/<id>` | Delete transaction |

#### Batches

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/batches` | List all batches |
| POST | `/batches` | Create batch with transactions |
| GET | `/batches/<id>` | Get batch with transactions |
| POST | `/batches/<id>/process` | Classify batch |

#### Master Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/gl-codes` | List GL codes (210) |
| POST | `/gl-codes` | Create GL code |
| GET | `/fund-codes` | List fund codes (45) |
| GET | `/vendors` | List vendors (12) |
| POST | `/vendors` | Create vendor |
| GET | `/customers` | List customers (34) |
| POST | `/customers` | Create customer |

#### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit-logs` | View audit logs |
| POST | `/sync/master-data` | Sync to MongoDB |

### Example Responses

#### GET /api/status
```json
{
  "status": "ok",
  "mongodb": "connected",
  "database": "bank_posting_tool",
  "timestamp": "2024-12-10T12:30:00.000000"
}
```

#### GET /api/stats
```json
{
  "transactions": {
    "total": 150,
    "by_status": {"classified": 145, "pending": 5},
    "by_module": {"CR": 50, "CD": 85, "JV": 15}
  },
  "batches": {"total": 10},
  "timestamp": "2024-12-10T12:30:00.000000"
}
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017/` | MongoDB connection |
| `MONGODB_DATABASE` | `bank_posting_tool` | Database name |
| `FLASK_SECRET_KEY` | `bank_posting_tool_secret_key_2024` | Flask secret |
| `FLASK_DEBUG` | `True` | Debug mode |

### OCR Configuration (Optional)

For scanned PDF support:

```python
# config.py
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\bin'
```

---

## 📊 Master Data

### GL Codes (210 total)

| Range | Category |
|-------|----------|
| 10000-10999 | Bank Accounts |
| 11000-13999 | Assets |
| 20000-28000 | Liabilities |
| 3001-4999 | Revenue |
| 5000-6999 | Expenses |
| 9000-9999 | Other |

### Fund Codes (45 total)

- General Admin
- NAHASDA Programs (4)
- Boys and Girls Club (12)
- BCBS Programs (3)
- Events & Cultural (8)
- Properties & Community (3)
- Grants & Foundations (5)
- Tribal Programs (3)

### Keywords (500+)

Categories include:
- Payroll (ADP, WAGES, SALARY)
- Taxes (IRS, EFTPS, WITHHOLDING)
- Utilities (ELECTRIC, WATER, GAS)
- Grants (NAHASDA, HUD, BGCA)
- Insurance (BCBS, DELTA DENTAL)

---

## 🗄️ Database Schema

### MongoDB Collections

```javascript
// transactions
{
  _id: ObjectId,
  batch_id: String,
  date: String,
  description: String,
  amount: Number,
  module: "CR" | "CD" | "JV",
  gl_code: String,
  fund_code: String,
  confidence: Number,
  status: "pending" | "classified" | "processed"
}

// batches
{
  _id: ObjectId,
  name: String,
  source_file: String,
  transaction_count: Number,
  status: String,
  created_at: DateTime
}

// gl_codes, fund_codes, vendors, customers, audit_logs
```

---

## 🔧 Troubleshooting

### MongoDB Not Connecting

```bash
# Check if running
net start MongoDB

# Or start manually
mongod --dbpath C:\data\db
```

### Module Not Found Errors

```bash
pip install flask pymongo openpyxl pandas pdfplumber
```

### Port 5000 Already in Use

```bash
# Find process
netstat -ano | findstr :5000

# Kill process
taskkill /PID <pid> /F
```

### PDF Parsing Fails

1. Install Tesseract OCR for scanned documents
2. Check PDF isn't password protected
3. Try converting to Excel first

---

## 📈 Statistics

| Metric | Value |
|--------|-------|
| Lines of Code | 7,372 |
| Files | 30 |
| GL Codes | 210 |
| Fund Codes | 45 |
| Customers | 34 |
| Vendors | 12 |
| Keywords | 500+ |
| API Endpoints | 25+ |
| Time Savings | 85-90% |

---

## 🗺️ Roadmap

- [ ] Machine Learning classification improvements
- [ ] Multi-bank API integration (Plaid)
- [ ] Email notifications
- [ ] Dashboard analytics
- [ ] User authentication
- [ ] Mobile app

---

## 👥 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

Proprietary - Harshwal Consulting Services

---

## 📞 Support

For issues or questions:
- Create an [Issue](https://github.com/harshwaladvisory/Bank_Transaction_Posting_Tool/issues)
- Contact the development team

---

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MongoDB](https://www.mongodb.com/) - Database
- [Bootstrap](https://getbootstrap.com/) - UI framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF parsing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/harshwaladvisory">Harshwal Consulting Services</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/December-2024-orange.svg" alt="Date">
</p>
