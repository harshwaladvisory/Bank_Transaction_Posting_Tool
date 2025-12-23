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

# OCR settings
TESSERACT_CMD = r'C:\Users\sanjana.thakur\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'  # Windows default
POPPLER_PATH = r'C:\Users\sanjana.thakur\poppler\Library\bin'  # Windows default

# Flask settings
FLASK_HOST = '0.0.0.0'  # Listen on all interfaces for deployment
FLASK_PORT = int(os.environ.get('PORT', 8590))  # Default to 8590, configurable via environment
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'  # Enable auto-reload

# Logging settings
LOG_FILE = os.path.join(LOG_DIR, 'audit_trail.json')