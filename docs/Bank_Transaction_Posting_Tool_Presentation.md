# Bank Transaction Posting Tool
## Presentation Guide

---

# SLIDE 1: Title Slide

## Bank Transaction Posting Tool

**Automating Bank Statement Processing**

*Harshwal Consulting Services*

Version 2.2.0 | December 2025

---

# SLIDE 2: Problem Statement

## The Challenge

### Manual Bank Statement Processing is:

- ⏰ **Time-Consuming**: Hours of manual data entry
- ❌ **Error-Prone**: Human mistakes in GL code assignment
- 📄 **Repetitive**: Same tasks for every bank statement
- 🔄 **Inconsistent**: Different people, different approaches

### Impact on Organizations:
- Delayed month-end closing
- Reconciliation errors
- Audit findings
- Staff frustration

---

# SLIDE 3: Our Solution

## Bank Transaction Posting Tool

### What It Does:

| Step | Manual Process | Automated |
|------|---------------|-----------|
| **Upload** | Manually open files | Drag & drop multiple files |
| **Extract** | Copy-paste transactions | Automatic parsing |
| **Classify** | Look up GL codes | Smart classification |
| **Generate** | Create journal entries | Auto-generated Excel |
| **Review** | Check each entry | Confidence-based review |

### Result: Hours → Minutes

---

# SLIDE 4: Key Features

## Feature Highlights

### 📁 Multi-Format Support
- PDF (digital + scanned)
- Excel (.xlsx, .xls)
- CSV files

### 🏦 Multiple Banks
- Farmers Bank
- Truist Bank
- PNC Bank
- CrossFirst Bank
- Sovereign Bank
- Generic fallback

### 🎯 Smart Classification
- 500+ keyword rules
- Vendor matching
- Customer/Grant identification
- Confidence scoring

### 📊 Three Modules
- Cash Receipts (CR)
- Cash Disbursements (CD)
- Journal Vouchers (JV)

---

# SLIDE 5: How It Works

## Processing Flow

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  1. UPLOAD          2. PARSE           3. CLASSIFY      │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐      │
│  │   PDF   │   →    │  Smart  │   →    │ Keyword │      │
│  │  Excel  │        │ Parser  │        │ Matching│      │
│  │   CSV   │        │   OCR   │        │  500+   │      │
│  └─────────┘        └─────────┘        └─────────┘      │
│                                               │          │
│  6. DOWNLOAD        5. REVIEW          4. ROUTE         │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐      │
│  │  Excel  │   ←    │  User   │   ←    │  CR/CD  │      │
│  │  Files  │        │ Review  │        │   /JV   │      │
│  │   ZIP   │        │  Edit   │        │         │      │
│  └─────────┘        └─────────┘        └─────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

# SLIDE 6: Upload Interface

## Multiple File Upload

### Features:
- **Drag & Drop**: Simply drag files onto the upload zone
- **Multiple Selection**: Hold Ctrl to select multiple files
- **Add More**: Click "Add More" to include additional files
- **File Preview**: See all selected files before processing
- **Remove Files**: Remove individual files from the list

### Supported Formats:
| Format | Icon | Extensions |
|--------|------|------------|
| PDF | 📕 | .pdf |
| Excel | 📗 | .xlsx, .xls |
| CSV | 📘 | .csv |

---

# SLIDE 7: Bank Detection

## Smart Bank Detection

### Automatic Recognition:

The tool automatically identifies the bank from statement content:

| Bank | Identifiers |
|------|-------------|
| Farmers Bank | "Farmers Bank", "farmers-bank.com" |
| Truist | "Truist", "truist.com" |
| PNC | "PNC Bank", "pnc.com" |
| CrossFirst | "CrossFirst Bank", "crossfirstbank.com" |
| Sovereign | "Sovereign Bank" |

### Benefits:
- No manual bank selection needed
- Correct parsing rules applied automatically
- Fallback parser for unknown formats

---

# SLIDE 8: Transaction Extraction

## OCR-Powered Extraction

### For Scanned PDFs:

```
┌───────────────────────────────────────┐
│          Scanned PDF Image            │
│                                       │
│  12/15  ACH DEPOSIT HUD     5,000.00  │
│  12/16  CHECK #1234         1,250.00  │
│  12/17  SERVICE FEE            25.00  │
│                                       │
└───────────────────────────────────────┘
                    │
                    ▼ OCR Processing

┌───────────────────────────────────────┐
│         Extracted Transactions        │
│                                       │
│  Date: 12/15  Desc: ACH DEPOSIT HUD   │
│  Amount: $5,000.00  Type: Deposit     │
│                                       │
│  Date: 12/16  Desc: CHECK #1234       │
│  Amount: $1,250.00  Type: Withdrawal  │
│                                       │
└───────────────────────────────────────┘
```

### Performance:
- First-time: ~100 seconds (23 pages)
- Cached: <1 second (2000x faster!)

---

# SLIDE 9: Classification System

## Intelligent Classification

### Multi-Layer Matching:

```
Transaction: "HUD TREAS NAHASDA GRANT 303"
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
┌─────────┐   ┌──────────┐   ┌─────────┐
│ Keyword │   │  Vendor  │   │ Customer│
│ Matching│   │ Matching │   │ Matching│
└────┬────┘   └────┬─────┘   └────┬────┘
     │              │              │
     ▼              ▼              ▼
  HUD: CR       Not Found      NAHASDA
  GL: 3001                     Fund: 1000
     │              │              │
     └──────────────┼──────────────┘
                    ▼
           ┌───────────────┐
           │ Final Result  │
           │ GL: 3001      │
           │ Module: CR    │
           │ Confidence:95%│
           └───────────────┘
```

---

# SLIDE 10: Confidence Scoring

## Confidence-Based Review

### Four Confidence Levels:

| Level | Range | Badge | Action |
|-------|-------|-------|--------|
| **High** | 85-100% | 🟢 Green | Auto-approved |
| **Medium** | 60-84% | 🟡 Yellow | Quick review |
| **Low** | 0-59% | 🔴 Red | Manual review |
| **None** | N/A | ⚪ Gray | Must classify |

### Filter by Confidence:
- Click column header dropdown
- Click any confidence badge
- Quickly focus on items needing attention

---

# SLIDE 11: Review Interface

## Transaction Review

### Features:

| Feature | Description |
|---------|-------------|
| **Module Tabs** | All, CR, CD, JV, Unknown |
| **Statistics** | Total, Deposits, Withdrawals |
| **Confidence Filter** | Click header or badges |
| **Edit Button** | Modify any transaction |
| **Bulk Edit** | Edit multiple low-confidence items |
| **Balance Display** | Shows credits vs debits |

### Workflow:
1. Filter by low confidence
2. Review and correct
3. Generate output files
4. Download results

---

# SLIDE 12: Module Routing

## Three Accounting Modules

### Cash Receipts (CR)
- **GL Range**: 4000-4999
- **Examples**:
  - Grant deposits (HUD, DOE)
  - Customer payments
  - Interest income

### Cash Disbursements (CD)
- **GL Range**: 6000-7999
- **Examples**:
  - Check payments
  - Payroll
  - Service fees
  - Taxes

### Journal Vouchers (JV)
- **Types**: Multi-line, corrections
- **Examples**:
  - Bank fee allocations
  - Error corrections

---

# SLIDE 13: Learning System

## ChromaDB Learning

### How It Works:

```
┌─────────────────────────────────────────┐
│     User corrects transaction           │
│     "ACH DEPOSIT HUD" → GL 3001         │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│     Pattern stored as vector embedding  │
│     in ChromaDB local database          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│     Future "HUD TREASURY" transactions  │
│     automatically matched → 95% conf    │
└─────────────────────────────────────────┘
```

### Benefits:
- 100% local (no cloud APIs)
- Learns from corrections
- Improves over time
- Bank-specific patterns

---

# SLIDE 14: Output Generation

## Excel Output Files

### Generated Files:

| File | Contents |
|------|----------|
| **CR_entries.xlsx** | Cash Receipt journal entries |
| **CD_entries.xlsx** | Cash Disbursement entries |
| **JV_entries.xlsx** | Journal Voucher entries |
| **All_transactions.xlsx** | Complete transaction list |

### Download Options:
- Individual file download
- "Download All as ZIP" button

### Import Ready:
Files formatted for direct import into accounting systems

---

# SLIDE 15: Performance

## Speed & Efficiency

### Processing Times:

| Scenario | Time |
|----------|------|
| First PDF upload (23 pages) | ~100-120 sec |
| Same PDF (cached) | <1 second |
| Simple PDF (3-5 pages) | ~15-30 sec |
| Excel/CSV files | 1-2 seconds |

### Optimization Features:
- OCR caching (file-hash based)
- Reduced DPI (350 vs 500)
- Single-pass processing
- Smart page classification

### ROI:
- **Manual**: 2-3 hours per statement
- **Automated**: 5-10 minutes (including review)
- **Savings**: 90%+ time reduction

---

# SLIDE 16: Architecture

## Technology Stack

### Backend:
| Component | Technology |
|-----------|------------|
| Framework | Python Flask |
| Database | MongoDB (optional) |
| OCR Engine | Tesseract OCR |
| PDF Processing | pdfplumber, pdf2image |
| Learning | ChromaDB |

### Frontend:
| Component | Technology |
|-----------|------------|
| UI Framework | Bootstrap 5 |
| Styling | HTML5, CSS3 |
| Interactivity | JavaScript |

### Data Processing:
- pandas for data manipulation
- openpyxl for Excel generation

---

# SLIDE 17: Security

## Security Features

### Data Protection:
- Local processing (no cloud uploads)
- MongoDB authentication support
- Session encryption (SECRET_KEY)
- No external API calls

### Access Control:
- Configurable via environment variables
- HTTPS support via reverse proxy
- Localhost by default

### Audit Trail:
- Transaction logging
- User action history
- Change tracking

---

# SLIDE 18: Recent Enhancements

## Version 2.2.0 Updates

### UI Improvements:
- ✅ Multiple file upload support
- ✅ Confidence filter in column header
- ✅ Clickable confidence badges
- ✅ Active filter indicator
- ✅ CDN optimization (Cloudflare)

### Performance:
- ✅ OCR caching (2000x faster)
- ✅ Reduced DPI processing

### Parser Fixes:
- ✅ CrossFirst Bank date extraction
- ✅ Multi-year statement handling
- ✅ Vendor extraction validation

---

# SLIDE 19: Demo Workflow

## Live Demo Steps

### 1. Upload
- Navigate to Upload page
- Drag & drop bank statement PDF
- Click "Process All Files"

### 2. Review
- View extracted transactions
- Filter by confidence level
- Edit low-confidence items
- Correct GL codes if needed

### 3. Generate
- Click "Generate Output"
- View generated files

### 4. Download
- Download individual files
- Or "Download All as ZIP"

---

# SLIDE 20: Summary

## Key Takeaways

### Benefits:
| Benefit | Description |
|---------|-------------|
| **Time Savings** | 90%+ reduction in processing time |
| **Accuracy** | Template-based = 100% extraction |
| **Learning** | Gets smarter with corrections |
| **Flexibility** | Multiple banks, multiple formats |
| **Production Ready** | MongoDB, concurrent users |

### ROI:
- Immediate time savings
- Reduced errors
- Faster month-end close
- Improved audit readiness

---

# SLIDE 21: Contact

## Get Started

### Harshwal Consulting Services

**Email**: support@harshwalconsulting.com

**Documentation**: See `/docs` folder

**Repository**: github.com/harshwaladvisory

---

# Appendix: Slide Design Notes

## For PowerPoint Conversion:

1. **Title Slide**: Blue gradient background, company logo
2. **Section Slides**: Darker blue with white text
3. **Content Slides**: White background, blue accents
4. **Icons**: Use Bootstrap Icons or similar
5. **Code Blocks**: Light gray background, monospace font
6. **Tables**: Alternating row colors, header in blue
7. **Flow Diagrams**: Use SmartArt or shapes

## Font Recommendations:
- **Titles**: Calibri Bold, 32-40pt
- **Body**: Calibri, 18-24pt
- **Code**: Consolas, 14-16pt

## Color Scheme:
- Primary: #0d6efd (Bootstrap Blue)
- Success: #28a745 (Green)
- Warning: #ffc107 (Yellow)
- Danger: #dc3545 (Red)
- Background: White
- Text: #212529 (Dark Gray)
