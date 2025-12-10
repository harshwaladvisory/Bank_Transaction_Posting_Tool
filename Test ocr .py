"""
OCR Installation Test Script
Tests if Tesseract and Poppler are properly installed
"""

import os
import sys

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def test_tesseract():
    """Test Tesseract OCR installation"""
    print_header("Testing Tesseract OCR")
    
    try:
        import pytesseract
        print("✓ pytesseract module imported successfully")
        
        # Try to get tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract version: {version}")
            return True
        except Exception as e:
            print(f"✗ Tesseract not found or not in PATH")
            print(f"  Error: {e}")
            print("\n  SOLUTION:")
            print("  1. Download Tesseract from:")
            print("     https://github.com/UB-Mannheim/tesseract/wiki")
            print("  2. Install it (remember the installation path)")
            print("  3. Add to PATH or set in config.py:")
            print("     TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
            return False
            
    except ImportError:
        print("✗ pytesseract module not installed")
        print("  Run: pip install pytesseract")
        return False

def test_poppler():
    """Test Poppler installation (needed for pdf2image)"""
    print_header("Testing Poppler (pdf2image)")
    
    try:
        from pdf2image import convert_from_path
        print("✓ pdf2image module imported successfully")
        
        # Try to check if poppler is available
        try:
            from pdf2image.exceptions import PDFInfoNotInstalledError
            # Create a minimal test - just check if pdftoppm exists
            import shutil
            
            # Check common locations
            poppler_paths = [
                r'C:\Program Files\poppler\bin',
                r'C:\Program Files\poppler-24.08.0\Library\bin',
                r'C:\poppler\bin',
                r'C:\Program Files (x86)\poppler\bin',
            ]
            
            pdftoppm_found = shutil.which('pdftoppm')
            
            if pdftoppm_found:
                print(f"✓ Poppler found: {pdftoppm_found}")
                return True
            else:
                # Check manual paths
                for path in poppler_paths:
                    if os.path.exists(os.path.join(path, 'pdftoppm.exe')):
                        print(f"✓ Poppler found at: {path}")
                        print(f"  NOTE: Add this to your PATH environment variable")
                        return True
                
                print("✗ Poppler (pdftoppm) not found in PATH")
                print("\n  SOLUTION:")
                print("  1. Download Poppler from:")
                print("     https://github.com/oschwartz10612/poppler-windows/releases")
                print("  2. Extract to C:\\Program Files\\poppler")
                print("  3. Add to PATH: C:\\Program Files\\poppler\\Library\\bin")
                print("  4. Or set in config.py:")
                print("     POPPLER_PATH = r'C:\\Program Files\\poppler\\Library\\bin'")
                return False
                
        except Exception as e:
            print(f"✗ Error checking Poppler: {e}")
            return False
            
    except ImportError:
        print("✗ pdf2image module not installed")
        print("  Run: pip install pdf2image")
        return False

def test_pdfplumber():
    """Test pdfplumber for digital PDFs"""
    print_header("Testing pdfplumber (Digital PDFs)")
    
    try:
        import pdfplumber
        print("✓ pdfplumber module imported successfully")
        print("  (This handles digital/text-based PDFs without OCR)")
        return True
    except ImportError:
        print("✗ pdfplumber module not installed")
        print("  Run: pip install pdfplumber")
        return False

def test_with_sample_pdf(pdf_path=None):
    """Test OCR with an actual PDF file"""
    if not pdf_path:
        print_header("Testing with Sample PDF")
        print("  No PDF file provided for testing")
        print("  Usage: python test_ocr.py <path_to_pdf>")
        return
    
    print_header(f"Testing with: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        print(f"✗ File not found: {pdf_path}")
        return
    
    # Test 1: Try pdfplumber (digital PDF)
    print("\n[1] Trying pdfplumber (for digital PDFs)...")
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                if text and len(text.strip()) > 50:
                    print(f"✓ Digital PDF - Extracted {len(text)} characters")
                    print(f"  Preview: {text[:200]}...")
                    return
                else:
                    print("  No text found - might be scanned/image PDF")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 2: Try OCR (scanned PDF)
    print("\n[2] Trying OCR (for scanned PDFs)...")
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        # Convert first page to image
        print("  Converting PDF to image...")
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
        
        if images:
            print("  Running OCR...")
            text = pytesseract.image_to_string(images[0])
            
            if text and len(text.strip()) > 20:
                print(f"✓ OCR Success - Extracted {len(text)} characters")
                print(f"  Preview: {text[:200]}...")
            else:
                print("✗ OCR returned no/little text")
                print("  The PDF might be empty or very low quality")
        else:
            print("✗ Could not convert PDF to image")
            
    except Exception as e:
        print(f"✗ OCR Error: {e}")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         OCR INSTALLATION TEST                                 ║
║                   Bank Transaction Posting Tool                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # Run tests
    results['pdfplumber'] = test_pdfplumber()
    results['tesseract'] = test_tesseract()
    results['poppler'] = test_poppler()
    
    # Summary
    print_header("SUMMARY")
    
    all_passed = all(results.values())
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
    
    if all_passed:
        print("\n✓ All components installed correctly!")
        print("  Your system is ready to process PDF bank statements.")
    else:
        print("\n✗ Some components are missing.")
        print("  Please install the missing components listed above.")
    
    # Test with actual PDF if provided
    if len(sys.argv) > 1:
        test_with_sample_pdf(sys.argv[1])
    else:
        print("\n" + "="*60)
        print("  TIP: Test with an actual PDF file:")
        print("  python test_ocr.py your_bank_statement.pdf")
        print("="*60)

if __name__ == "__main__":
    main()