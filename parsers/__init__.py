"""
Parsers Package - Bank statement parsing modules

Architecture:
1. SmartParser (smart_parser.py) - RECOMMENDED: Template-based + AI fallback
2. PDFParser (pdf_parser.py) - Legacy regex-based parser with OCR support
3. TemplateParser (template_parser.py) - JSON template-based parsing
4. AIParser (ai_parser.py) - AI fallback for unknown banks
5. UniversalParser (universal_parser.py) - Multi-bank format support
6. LLMParser (llm_parser.py) - AI-powered parser using Ollama or LM Studio
7. HybridParser (llm_parser.py) - Best of both: regex first, LLM fallback

To add a new bank:
1. Edit config/bank_templates.json
2. Add identifiers, transaction_patterns, and keywords
3. No code changes needed!
"""

# Primary parser (recommended)
from .smart_parser import SmartParser, smart_parse

# Legacy parsers
from .pdf_parser import PDFParser
from .excel_parser import ExcelParser
from .universal_parser import UniversalParser, parse_bank_statement

# Template-based parser
try:
    from .template_parser import TemplateParser
except ImportError:
    TemplateParser = None

# AI fallback parser
try:
    from .ai_parser import AIParser
except ImportError:
    AIParser = None

# Try to import LLM parser and HybridParser
try:
    from .llm_parser import LLMParser, HybridParser
    __all__ = ['SmartParser', 'smart_parse', 'PDFParser', 'ExcelParser',
               'UniversalParser', 'LLMParser', 'HybridParser', 'TemplateParser',
               'AIParser', 'parse_bank_statement']
except ImportError:
    __all__ = ['SmartParser', 'smart_parse', 'PDFParser', 'ExcelParser',
               'UniversalParser', 'TemplateParser', 'AIParser', 'parse_bank_statement']
