"""
Bank Transaction Posting Tool - Main Entry Point
Harshwal Consulting Services

Command Line Interface for processing bank statements
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR, SUPPORTED_BANK_EXTENSIONS
from parsers import UniversalParser, parse_bank_statement
from classifiers import ClassificationEngine
from processors import ModuleRouter, EntryBuilder, OutputGenerator


def print_banner():
    """Print application banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     BANK TRANSACTION POSTING TOOL                             ║
║                      Harshwal Consulting Services                             ║
║                                                                               ║
║  Automates bank statement processing and journal entry generation            ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


def process_bank_statement(file_path: str, output_dir: str = None, 
                          target_system: str = 'MIP', verbose: bool = True) -> Dict:
    """
    Process a bank statement file end-to-end
    
    Args:
        file_path: Path to bank statement file (PDF, Excel, CSV)
        output_dir: Output directory for generated files
        target_system: Target accounting system ('MIP', 'QBD', 'Generic')
        verbose: Print progress messages
        
    Returns:
        Dictionary with processing results and generated file paths
    """
    results = {
        'status': 'success',
        'input_file': file_path,
        'transactions_parsed': 0,
        'transactions_classified': 0,
        'generated_files': {},
        'summary': {}
    }
    
    try:
        # Step 1: Parse bank statement
        if verbose:
            print(f"\n[1/5] Parsing bank statement: {os.path.basename(file_path)}")
        
        parser = UniversalParser()
        transactions = parser.parse(file_path)
        parse_summary = parser.get_summary()
        
        results['transactions_parsed'] = len(transactions)
        results['parse_summary'] = parse_summary
        
        if verbose:
            print(f"      ✓ Found {len(transactions)} transactions")
            print(f"      ✓ Total Deposits: ${parse_summary.get('total_deposits', 0):,.2f}")
            print(f"      ✓ Total Withdrawals: ${abs(parse_summary.get('total_withdrawals', 0)):,.2f}")
        
        if not transactions:
            results['status'] = 'error'
            results['error'] = 'No transactions found in file'
            return results
        
        # Step 2: Classify transactions
        if verbose:
            print(f"\n[2/5] Classifying transactions...")
        
        classifier = ClassificationEngine()
        classified = classifier.classify_batch(transactions)
        classification_summary = classifier.get_summary(classified)
        
        results['transactions_classified'] = len(classified)
        results['classification_summary'] = classification_summary
        
        if verbose:
            print(f"      ✓ Classified {len(classified)} transactions")
            print(f"      ✓ By Module: CR={classification_summary['by_module'].get('CR', 0)}, "
                  f"CD={classification_summary['by_module'].get('CD', 0)}, "
                  f"JV={classification_summary['by_module'].get('JV', 0)}, "
                  f"Unknown={classification_summary['by_module'].get('UNKNOWN', 0)}")
        
        # Step 3: Route to modules
        if verbose:
            print(f"\n[3/5] Routing to accounting modules...")
        
        router = ModuleRouter()
        routed = router.route_batch(classified)
        routing_summary = router.get_summary()
        
        results['routing_summary'] = routing_summary
        
        if verbose:
            print(f"      ✓ CR: {routing_summary['by_module'].get('CR', 0)} entries")
            print(f"      ✓ CD: {routing_summary['by_module'].get('CD', 0)} entries")
            print(f"      ✓ JV: {routing_summary['by_module'].get('JV', 0)} entries")
            print(f"      ✓ Unidentified: {routing_summary['by_module'].get('UNIDENTIFIED', 0)} entries")
        
        # Step 4: Build entries
        if verbose:
            print(f"\n[4/5] Building journal entries...")
        
        builder = EntryBuilder(target_system=target_system)
        
        all_routed = []
        for module in ['CR', 'CD', 'JV']:
            all_routed.extend(router.get_transactions_by_module(module))
        
        entries = builder.build_batch(all_routed)
        entry_summary = builder.get_summary()
        
        results['entry_summary'] = entry_summary
        
        if verbose:
            print(f"      ✓ Built {entry_summary['total_entries']} entries")
        
        # Step 5: Generate output files
        if verbose:
            print(f"\n[5/5] Generating output files...")
        
        output_generator = OutputGenerator(output_dir=output_dir, target_system=target_system)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        generated_files = output_generator.generate_all(entries, timestamp)
        
        # Generate unidentified file if needed
        unidentified = router.get_transactions_by_module('UNIDENTIFIED')
        if unidentified:
            generated_files['UNIDENTIFIED'] = output_generator.generate_unidentified(unidentified, timestamp)
        
        # Generate summary report
        generated_files['SUMMARY'] = output_generator.generate_summary_report(
            entries, classification_summary, routing_summary, timestamp
        )
        
        results['generated_files'] = generated_files
        
        if verbose:
            print(f"      ✓ Generated files:")
            for name, path in generated_files.items():
                print(f"        - {name}: {os.path.basename(path)}")
        
        # Final summary
        results['summary'] = {
            'total_transactions': len(transactions),
            'successfully_classified': sum(1 for c in classified if c.get('module') != 'UNKNOWN'),
            'needs_review': routing_summary.get('needs_review', 0),
            'total_credits': classification_summary.get('total_credits', 0),
            'total_debits': classification_summary.get('total_debits', 0)
        }
        
        if verbose:
            print(f"\n{'='*70}")
            print("PROCESSING COMPLETE")
            print(f"{'='*70}")
            print(f"Total Transactions: {results['summary']['total_transactions']}")
            print(f"Successfully Classified: {results['summary']['successfully_classified']}")
            print(f"Needs Review: {results['summary']['needs_review']}")
            print(f"Total Credits: ${results['summary']['total_credits']:,.2f}")
            print(f"Total Debits: ${results['summary']['total_debits']:,.2f}")
            print(f"\nOutput Directory: {output_dir or OUTPUT_DIR}")
        
    except Exception as e:
        results['status'] = 'error'
        results['error'] = str(e)
        if verbose:
            print(f"\n✗ Error: {e}")
        raise
    
    return results


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Bank Transaction Posting Tool - Process bank statements and generate journal entries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py statement.pdf
  python main.py statement.xlsx --output ./output
  python main.py statement.csv --system QBD --verbose
        """
    )
    
    parser.add_argument('file', nargs='?', help='Bank statement file (PDF, Excel, or CSV)')
    parser.add_argument('--output', '-o', help='Output directory for generated files')
    parser.add_argument('--system', '-s', choices=['MIP', 'QBD', 'Generic'], default='MIP',
                       help='Target accounting system (default: MIP)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--web', '-w', action='store_true', help='Launch web interface')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.web:
        print("Starting web interface...")
        from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
        print(f"Open http://{FLASK_HOST}:{FLASK_PORT} in your browser")
        from app import app
        app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
        return
    
    if not args.file:
        parser.print_help()
        print("\n✗ Error: Please provide a bank statement file or use --web for web interface")
        sys.exit(1)
    
    if not os.path.exists(args.file):
        print(f"\n✗ Error: File not found: {args.file}")
        sys.exit(1)
    
    ext = os.path.splitext(args.file)[1].lower()
    if ext not in SUPPORTED_BANK_EXTENSIONS:
        print(f"\n✗ Error: Unsupported file format: {ext}")
        print(f"   Supported formats: {', '.join(SUPPORTED_BANK_EXTENSIONS)}")
        sys.exit(1)
    
    try:
        results = process_bank_statement(
            file_path=args.file,
            output_dir=args.output,
            target_system=args.system,
            verbose=True
        )
        
        if results['status'] == 'success':
            print("\n✓ Processing completed successfully!")
            sys.exit(0)
        else:
            print(f"\n✗ Processing failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()