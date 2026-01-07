"""
Bank Transaction Posting Tool - Configuration
Harshwal Consulting Services
"""

import os
from datetime import datetime

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# NOTE: No OUTPUT_DIR - all files are generated in-memory and stored in MongoDB
# No local file storage for inputs or outputs

# Ensure directories exist (only essential ones for data files)
for d in [DATA_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

# Date format as per SOP
DATE_FORMAT = "%m/%d/%Y"
DATE_FORMATS_TO_TRY = [
    "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%Y",
    "%m/%d/%y", "%d-%m-%Y", "%Y/%m/%d", "%b %d, %Y",
    "%B %d, %Y", "%d %b %Y", "%d %B %Y"
]

# Current year for session IDs
CURRENT_YEAR = datetime.now().year

# Session ID prefixes as per SOP
SESSION_ID_PREFIX = {
    'CR': f'GP_CR_{CURRENT_YEAR}',
    'CD': f'GP_CD_{CURRENT_YEAR}',
    'JV': f'GP_JV_{CURRENT_YEAR}'
}

# Default GL codes
DEFAULT_BANK_GL = '1070'
DEFAULT_FUND_CODE = '1000'

# Module types
MODULE_TYPES = ['CR', 'CD', 'JV']

# Classification confidence thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60
CONFIDENCE_LOW = 0.40

# Output file names
OUTPUT_FILES = {
    'CR': 'Cash_Receipts_Import.xlsx',
    'CD': 'Cash_Disbursements_Import.xlsx',
    'JV': 'Journal_Voucher_Import.xlsx',
    'UNIDENTIFIED': 'Unidentified.xlsx'
}

# Supported file extensions
SUPPORTED_BANK_EXTENSIONS = ['.pdf', '.xlsx', '.xls', '.csv']
SUPPORTED_GL_EXTENSIONS = ['.xlsx', '.xls', '.csv', '.txt']

# OCR settings - configurable via environment variables
def _find_tesseract():
    """Find Tesseract executable, checking common installation paths."""
    if os.environ.get('TESSERACT_CMD'):
        return os.environ.get('TESSERACT_CMD')

    # Common Windows installation paths
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    # Fallback to PATH (works on Linux/Mac or if added to Windows PATH)
    return 'tesseract'

def _find_poppler():
    """Find Poppler bin directory, checking common installation paths."""
    if os.environ.get('POPPLER_PATH'):
        return os.environ.get('POPPLER_PATH')

    # Common Windows installation paths
    common_paths = [
        # Bundled with project (preferred for deployment)
        os.path.join(BASE_DIR, 'poppler', 'Library', 'bin'),
        r'C:\Program Files\poppler\Library\bin',
        r'C:\Program Files (x86)\poppler\Library\bin',
        os.path.expandvars(r'%USERPROFILE%\poppler\Library\bin'),
        r'C:\poppler\Library\bin',
        r'C:\poppler\bin',
        # Chocolatey installation
        r'C:\ProgramData\chocolatey\lib\poppler\tools\Library\bin',
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    # Return None - pdf2image will use PATH or show appropriate error
    return None

TESSERACT_CMD = _find_tesseract()
POPPLER_PATH = _find_poppler()

# Flask settings
FLASK_HOST = '0.0.0.0'  # Listen on all interfaces for deployment
FLASK_PORT = int(os.environ.get('PORT', 6002))  # Default to 8587, configurable via environment
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'  # Enable auto-reload

# Logging settings
LOG_FILE = os.path.join(LOG_DIR, 'audit_trail.json')