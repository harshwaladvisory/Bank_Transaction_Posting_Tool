# Bank Transaction Posting Tool
## Complete End-to-End Guide

---

**Version:** 2.2.0
**Organization:** Harshwal Consulting Services
**Date:** December 2025
**Document Type:** Shareable Guide

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [What Does This Tool Do?](#2-what-does-this-tool-do)
3. [Key Features](#3-key-features)
4. [How It Works](#4-how-it-works)
5. [User Guide](#5-user-guide)
6. [Supported Banks](#6-supported-banks)
7. [Understanding the Output](#7-understanding-the-output)
8. [Technical Overview](#8-technical-overview)
9. [Installation & Setup](#9-installation--setup)
10. [Frequently Asked Questions](#10-frequently-asked-questions)
11. [Version History](#11-version-history)
12. [Support & Contact](#12-support--contact)

---

## 1. Introduction

### What is the Bank Transaction Posting Tool?

The **Bank Transaction Posting Tool** is an enterprise-grade application that automates the process of converting bank statements into accounting journal entries. Instead of manually reading bank statements and entering each transaction into your accounting system, this tool does it automatically in minutes.

### Who Should Use This Tool?

- **Accountants & Bookkeepers** - Reduce manual data entry
- **Financial Controllers** - Faster month-end closing
- **Housing Authorities** - Process HUD and grant transactions
- **Government Agencies** - Handle multiple funding sources
- **Non-Profit Organizations** - Track grants and donations

### The Problem We Solve

| Manual Process | With This Tool |
|----------------|----------------|
| 2-3 hours per statement | 5-10 minutes |
| Prone to human errors | 100% accurate extraction |
| Inconsistent GL coding | Smart classification |
| No audit trail | Full logging & tracking |

---

## 2. What Does This Tool Do?

### Simple Explanation

1. **You upload** a bank statement (PDF, Excel, or CSV)
2. **The tool extracts** all transactions automatically
3. **It classifies** each transaction (payroll, grants, fees, etc.)
4. **It assigns** the correct GL codes
5. **It generates** Excel files ready for your accounting system

### The Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   STEP 1: UPLOAD                                                │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Drag & drop your bank statement files                   │  │
│   │  • PDF statements (scanned or digital)                   │  │
│   │  • Excel files (.xlsx, .xls)                             │  │
│   │  • CSV files                                             │  │
│   │  • Multiple files at once supported                      │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│   STEP 2: AUTOMATIC PROCESSING                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  The system automatically:                               │  │
│   │  • Detects which bank the statement is from              │  │
│   │  • Extracts all transactions (deposits & withdrawals)    │  │
│   │  • Reads scanned PDFs using OCR technology               │  │
│   │  • Identifies transaction types                          │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│   STEP 3: SMART CLASSIFICATION                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Each transaction is analyzed:                           │  │
│   │  • Matched against 500+ keyword rules                    │  │
│   │  • Compared to vendor master list                        │  │
│   │  • Checked against customer/grant database               │  │
│   │  • Assigned a confidence score                           │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│   STEP 4: REVIEW & ADJUST                                       │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  You review the results:                                 │  │
│   │  • High confidence items are ready to go                 │  │
│   │  • Low confidence items highlighted for review           │  │
│   │  • Easy editing for any corrections needed               │  │
│   │  • Filter by confidence level                            │  │
│   └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│   STEP 5: GENERATE & DOWNLOAD                                   │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Output files created:                                   │  │
│   │  • CR_entries.xlsx (Cash Receipts)                       │  │
│   │  • CD_entries.xlsx (Cash Disbursements)                  │  │
│   │  • JV_entries.xlsx (Journal Vouchers)                    │  │
│   │  • Download individually or as ZIP                       │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Features

### 3.1 Multiple File Upload

Upload several bank statements at once:

| Method | How To |
|--------|--------|
| **Drag & Drop** | Drag files from your folder onto the upload area |
| **File Picker** | Click "Browse" and hold Ctrl to select multiple files |
| **Add More** | Click "Add More" button to add additional files |

All files are processed together and combined into a single review.

### 3.2 Smart Bank Detection

The tool automatically recognizes which bank the statement is from:

- **Farmers Bank** - Full support with multi-year handling
- **Truist Bank** - Complete transaction extraction
- **PNC Bank** - With service charge recovery
- **CrossFirst Bank** - With date extraction fixes
- **Sovereign Bank** - Full format support
- **Other Banks** - Generic parser as fallback

### 3.3 OCR for Scanned PDFs

Many bank statements are scanned images. Our tool uses **Tesseract OCR** technology to read these:

| Feature | Benefit |
|---------|---------|
| **Automatic Detection** | Knows when OCR is needed |
| **High Accuracy** | Optimized for bank statement formats |
| **Caching** | Same PDF processes 2000x faster on repeat |

### 3.4 Confidence-Based Classification

Every transaction gets a confidence score:

| Level | Score | Badge | What It Means |
|-------|-------|-------|---------------|
| **High** | 85-100% | 🟢 Green | Reliable - ready to use |
| **Medium** | 60-84% | 🟡 Yellow | Good - quick review recommended |
| **Low** | 0-59% | 🔴 Red | Uncertain - needs manual review |
| **None** | N/A | ⚪ Gray | No match - must be classified |

### 3.5 Interactive Confidence Filter

On the review page, you can filter transactions by confidence:

- **Click the Confidence column header** - Dropdown menu appears
- **Click any confidence badge** - Filters to that level only
- **Clear filter** - Click X on the filter indicator

This helps you focus on items that need attention.

### 3.6 Three Accounting Modules

Transactions are routed to the appropriate module:

| Module | Code | GL Range | Examples |
|--------|------|----------|----------|
| **Cash Receipts** | CR | 4000-4999 | Deposits, grants, interest |
| **Cash Disbursements** | CD | 6000-7999 | Checks, payroll, fees |
| **Journal Vouchers** | JV | Various | Corrections, transfers |

### 3.7 Learning System

The tool gets smarter over time:

1. When you correct a classification, the system remembers
2. Similar transactions in the future are classified correctly
3. All learning stays local on your server (no cloud)

---

## 4. How It Works

### 4.1 Transaction Extraction

The tool uses **template-based parsing** for supported banks:

```
Bank Statement Text:
"12/15  ACH DEPOSIT HUD NAHASDA    5,000.00"

Extracted Data:
├── Date: 12/15
├── Description: ACH DEPOSIT HUD NAHASDA
├── Amount: $5,000.00
└── Type: Deposit (positive amount)
```

### 4.2 Classification Logic

Each transaction goes through multiple matching layers:

```
Transaction: "HUD TREAS NAHASDA GRANT"
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ KEYWORD │    │ VENDOR  │    │CUSTOMER │
│ MATCHER │    │ MATCHER │    │ MATCHER │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
  HUD=Grant     Not Found      NAHASDA
  GL: 3001                    Fund: 1000
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
           ┌───────────────┐
           │ FINAL RESULT  │
           │ GL: 3001      │
           │ Module: CR    │
           │ Confidence:95%│
           └───────────────┘
```

### 4.3 High-Confidence Auto-Classification

Some transactions are classified with very high confidence:

| Transaction Pattern | GL Code | Confidence | Module |
|--------------------|---------|------------|--------|
| SERVICE FEE / SERVICE CHARGE | 6100 | 95% | CD |
| INTEREST / INTEREST EARNED | 4600 | 98% | CR |
| CHECK #XXXX | 7300 | 95% | CD |
| HUD / NAHASDA | 3001 | 95% | CR |
| PAYROLL / SALARY | 6600 | 90% | CD |

---

## 5. User Guide

### 5.1 Accessing the Application

1. Open your web browser
2. Go to: `http://localhost:8590` (or your server URL)
3. You'll see the Upload page

### 5.2 Uploading Files

**Method 1: Drag & Drop**
1. Open your file explorer
2. Select your bank statement file(s)
3. Drag them onto the upload area
4. Files appear in the "Selected Files" list

**Method 2: File Picker**
1. Click the file input box
2. Navigate to your files
3. Hold **Ctrl** to select multiple files
4. Click "Open"

**Method 3: Add More Files**
1. Upload initial file(s)
2. Click "Add More" button
3. Select additional files
4. All files shown in list

### 5.3 Processing Files

1. Verify all files are in the list
2. Click **"Process All Files"**
3. Wait for processing (progress bar shown)
   - First-time PDFs: ~2 minutes per 20 pages
   - Cached PDFs: < 1 second
   - Excel/CSV: 1-2 seconds
4. Automatically redirected to Review page

### 5.4 Reviewing Transactions

**The Review Page Shows:**
- Summary statistics (total, deposits, withdrawals)
- All transactions in a table
- Confidence level for each transaction
- Module assignment (CR/CD/JV)
- GL code assignments

**Filtering Transactions:**
1. Click the **Confidence** column header
2. Select a filter (High, Medium, Low, None)
3. Only matching transactions shown
4. Click X on filter badge to clear

**Editing a Transaction:**
1. Click the **pencil icon** on any row
2. Modal opens with current values
3. Change Module, GL Code, or Fund Code
4. Click "Save Changes"

**Bulk Editing:**
1. Click "Bulk Edit Low Confidence" button
2. All low/no-confidence items shown
3. Edit multiple items at once
4. Save all changes

### 5.5 Generating Output

1. Review all transactions
2. Click **"Generate Output Files"**
3. System creates Excel files
4. Redirected to Results page

### 5.6 Downloading Results

**Individual Files:**
- Click file name to download

**All Files:**
- Click **"Download All as ZIP"**
- Single ZIP file with all outputs

---

## 6. Supported Banks

### Currently Supported

| Bank | PDF | Excel | CSV | OCR | Special Notes |
|------|-----|-------|-----|-----|---------------|
| **Farmers Bank** | ✅ | ✅ | ✅ | ✅ | Multi-year statement handling |
| **Truist Bank** | ✅ | ✅ | ✅ | ✅ | Full support |
| **PNC Bank** | ✅ | ✅ | ✅ | ✅ | Service charge recovery |
| **CrossFirst Bank** | ✅ | ✅ | ✅ | ✅ | Withdrawal date fixes |
| **Sovereign Bank** | ✅ | ✅ | ✅ | ✅ | Full support |
| **Other Banks** | ✅ | ✅ | ✅ | ✅ | Generic parser |

### Adding New Banks

New banks can be added by updating the configuration file. Contact support for assistance.

---

## 7. Understanding the Output

### 7.1 Output Files Generated

| File | Contents | Use |
|------|----------|-----|
| **CR_entries.xlsx** | Cash Receipt journal entries | Import to AR module |
| **CD_entries.xlsx** | Cash Disbursement entries | Import to AP module |
| **JV_entries.xlsx** | Journal Voucher entries | Import to GL module |
| **All_transactions.xlsx** | Complete transaction list | Reference/audit |

### 7.2 File Format

Each Excel file contains:

| Column | Description |
|--------|-------------|
| Date | Transaction date |
| Description | Original description from bank |
| Amount | Transaction amount |
| GL Code | Assigned general ledger code |
| Fund Code | Fund/department code |
| Module | CR, CD, or JV |
| Confidence | Classification confidence level |

### 7.3 GL Code Structure

| GL Range | Category | Examples |
|----------|----------|----------|
| 1000-1999 | Assets | Bank accounts |
| 3000-3999 | Fund Balance | Federal revenue |
| 4000-4999 | Revenue | Grants, interest |
| 6000-6999 | Operating Expenses | Salaries, utilities |
| 7000-7999 | Other Expenses | Taxes, vendors |

---

## 8. Technical Overview

### 8.1 Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.8+, Flask |
| **Frontend** | HTML5, Bootstrap 5, JavaScript |
| **Database** | MongoDB (optional) |
| **OCR Engine** | Tesseract OCR |
| **PDF Processing** | pdfplumber, pdf2image |
| **Machine Learning** | ChromaDB (vector embeddings) |

### 8.2 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      WEB BROWSER                            │
│                    (User Interface)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER                         │
│                      (app.py)                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   PARSERS   │  │ CLASSIFIERS  │  │   PROCESSORS    │    │
│  ├─────────────┤  ├──────────────┤  ├─────────────────┤    │
│  │SmartParser  │  │KeywordMatch  │  │ ModuleRouter    │    │
│  │PDFParser    │  │VendorMatch   │  │ EntryBuilder    │    │
│  │ExcelParser  │  │CustomerMatch │  │ OutputGenerator │    │
│  │OCR Engine   │  │HistoryMatch  │  │                 │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     DATA LAYER                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │  MongoDB    │  │  ChromaDB    │  │   JSON Files    │    │
│  │ (optional)  │  │  (Learning)  │  │  (Keywords)     │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Performance Metrics

| Scenario | Processing Time |
|----------|-----------------|
| First PDF upload (23 pages) | ~100-120 seconds |
| Same PDF (cached) | < 1 second |
| Simple PDF (3-5 pages) | ~15-30 seconds |
| Excel/CSV files | 1-2 seconds |

### 8.4 Security Features

| Feature | Description |
|---------|-------------|
| **Local Processing** | All data processed locally, no cloud uploads |
| **No External APIs** | Transaction data never leaves your server |
| **Session Encryption** | Flask sessions encrypted with SECRET_KEY |
| **Audit Logging** | All actions logged for compliance |

---

## 9. Installation & Setup

### 9.1 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.8+ | Application runtime |
| Tesseract OCR | Latest | Read scanned PDFs |
| Poppler | Latest | PDF processing |
| MongoDB | 4.0+ | Data persistence (optional) |

### 9.2 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/harshwaladvisory/Bank_Transaction_Posting_Tool.git
cd Bank_Transaction_Posting_Tool

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure OCR paths in config.py
# Edit TESSERACT_CMD and POPPLER_PATH

# 5. Run application
python app.py

# 6. Open browser
# http://localhost:8590
```

### 9.3 Configuration

Key settings in `config.py`:

```python
# OCR Settings (UPDATE FOR YOUR SYSTEM)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\poppler\bin'

# Server Settings
FLASK_PORT = 8590
FLASK_DEBUG = True  # Set False for production

# Classification Thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
```

### 9.4 Environment Variables (Production)

```bash
# Required
SECRET_KEY=your-secret-key-here

# Optional
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=bank_posting_tool
PORT=8590
FLASK_DEBUG=False
```

---

## 10. Frequently Asked Questions

### General Questions

**Q: How long does processing take?**
A: First-time PDFs take ~2 minutes per 20 pages due to OCR. The same file processes in under 1 second on subsequent uploads due to caching. Excel/CSV files process in 1-2 seconds.

**Q: Can I upload multiple bank statements at once?**
A: Yes! You can drag & drop multiple files, use Ctrl+click in the file picker, or use the "Add More" button. All files are processed together.

**Q: What if my bank isn't supported?**
A: The tool has a generic parser that works with most bank formats. For best results, contact support to add specific bank templates.

**Q: Is my data secure?**
A: Yes. All processing happens locally on your server. No data is sent to external services or cloud providers.

### Technical Questions

**Q: Why does the first PDF take so long?**
A: The first upload requires OCR processing to read the scanned document. Results are cached, so subsequent uploads of the same file are instant.

**Q: How do I clear the cache?**
A: Delete files in the `data/ocr_cache/` folder. This forces re-processing on next upload.

**Q: Does it work without MongoDB?**
A: Yes, but data won't persist across application restarts. MongoDB is recommended for production use.

**Q: Can I add custom keywords?**
A: Yes, edit `data/keywords.json` to add your own classification rules.

### Troubleshooting

**Q: "No transactions found" error**
A: Check that:
1. File format is supported (.pdf, .xlsx, .xls, .csv)
2. Tesseract OCR is installed (for PDFs)
3. Bank is supported or use generic format

**Q: OCR not working**
A: Verify:
1. Tesseract installed: `tesseract --version`
2. Poppler installed
3. Paths correct in config.py

**Q: Bootstrap/CSS not loading**
A: The app uses cdnjs.cloudflare.com. If blocked:
1. Disable tracking prevention for the site
2. Or add to browser exceptions

---

## 11. Version History

### Version 2.2.0 (December 2025) - Current

**UI Enhancements:**
- Multiple file upload support (drag & drop, file picker, "Add More")
- Confidence filter dropdown in review table column header
- Clickable confidence badges for quick filtering
- Active filter indicator with clear button
- CDN switched to cdnjs (Cloudflare) for better compatibility

**Performance Optimizations:**
- OCR caching with file-hash based storage (2000x faster on repeat)
- Reduced DPI from 500 to 350 (30% faster)
- Single-pass OCR processing
- Smart page classification

**Parser Improvements:**
- CrossFirst Bank withdrawal date extraction fixes
- Multi-year statement handling for Farmers Bank
- Vendor extraction validation
- Statement period extraction for all banks

**Classification Enhancements:**
- High-confidence bank transaction detection
- SERVICE FEE at 95% confidence with GL 6100
- INTEREST at 98% confidence with GL 4600

### Version 2.1.0 (December 2025)

- Smart parser with bank templates
- ChromaDB learning module
- Multiple bank format support

### Version 2.0.0 (December 2025)

- MongoDB integration
- Duplicate detection
- Concurrent user support
- Security hardening

### Version 1.0.0 (Initial Release)

- Basic PDF/Excel parsing
- Keyword classification
- CR/CD/JV routing

---

## 12. Support & Contact

### Harshwal Consulting Services

**Email:** support@harshwalconsulting.com

**When Reporting Issues, Please Include:**
1. Python version (`python --version`)
2. Operating system
3. Full error message
4. Steps to reproduce
5. Sample file (redact sensitive data)

### Documentation Files

| File | Description |
|------|-------------|
| `README.md` | Quick start guide |
| `docs/Bank_Transaction_Posting_Tool_Documentation.md` | Full technical documentation |
| `docs/Bank_Transaction_Posting_Tool_Presentation.md` | Presentation slides |
| `docs/SECURITY_AND_CONFIGURATION.txt` | Security & config reference |
| `docs/Bank_Transaction_Posting_Tool_Complete_Guide.md` | This document |

---

## Quick Reference Card

| Item | Value |
|------|-------|
| **Default URL** | http://localhost:8590 |
| **Supported Files** | PDF, XLSX, XLS, CSV |
| **Max File Size** | 50MB |
| **First PDF Processing** | ~2 min per 20 pages |
| **Cached PDF** | < 1 second |
| **Excel/CSV** | 1-2 seconds |

| Confidence | Score | Color | Action |
|------------|-------|-------|--------|
| High | 85%+ | Green | Ready |
| Medium | 60-84% | Yellow | Review |
| Low | <60% | Red | Manual |
| None | N/A | Gray | Classify |

| Module | Code | GL Range |
|--------|------|----------|
| Cash Receipts | CR | 4000-4999 |
| Cash Disbursements | CD | 6000-7999 |
| Journal Vouchers | JV | Various |

---

**Document Version:** 1.0
**Last Updated:** December 24, 2025
**Maintained By:** Harshwal Consulting Services

---

*This document may be shared with stakeholders, team members, and clients.*
