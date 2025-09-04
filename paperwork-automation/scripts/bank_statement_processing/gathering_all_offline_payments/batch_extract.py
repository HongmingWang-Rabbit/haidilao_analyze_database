#!/usr/bin/env python3
"""
Batch extraction script for offline payments from multiple bank statement files.

This script processes all Excel files in a specified directory or pattern
and extracts offline payments that need confirmation.
"""

import sys
from pathlib import Path
import argparse
import logging
from datetime import datetime
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from extract_offline_payments import OfflinePaymentExtractorV2 as OfflinePaymentExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_excel_files(path: Path, pattern: str = "*.xlsx") -> List[Path]:
    """
    Find all Excel files matching the pattern.
    
    Args:
        path: Directory path or file path
        pattern: Glob pattern for file matching
        
    Returns:
        List of Excel file paths
    """
    if path.is_file():
        return [path] if path.suffix in ['.xlsx', '.xls'] else []
    
    if path.is_dir():
        # Find all Excel files in directory and subdirectories
        excel_files = list(path.glob(f"**/{pattern}"))
        # Filter out temporary files
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]
        return sorted(excel_files)
    
    return []


def main():
    """Main function for batch extraction."""
    parser = argparse.ArgumentParser(
        description='Batch extract offline payments from bank statements'
    )
    parser.add_argument(
        'input_path',
        help='Directory containing bank statement files or single file path'
    )
    parser.add_argument(
        '--pattern',
        default='*.xlsx',
        help='File pattern to match (default: *.xlsx)'
    )
    parser.add_argument(
        '--template',
        default='sheet-templates/offline-payment-sheet.xlsx',
        help='Path to offline payment template'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: auto-generated with timestamp)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search subdirectories recursively'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert paths
    input_path = Path(args.input_path)
    template_path = project_root / args.template
    output_path = Path(args.output) if args.output else None
    
    # Validate inputs
    if not input_path.exists():
        logger.error(f"Input path not found: {input_path}")
        sys.exit(1)
    
    if not template_path.exists():
        logger.error(f"Template file not found: {template_path}")
        sys.exit(1)
    
    # Find Excel files
    logger.info(f"Searching for Excel files in: {input_path}")
    pattern = f"**/{args.pattern}" if args.recursive else args.pattern
    excel_files = find_excel_files(input_path, args.pattern)
    
    if not excel_files:
        logger.warning(f"No Excel files found matching pattern: {pattern}")
        sys.exit(0)
    
    logger.info(f"Found {len(excel_files)} Excel file(s) to process")
    
    # Create extractor
    extractor = OfflinePaymentExtractor(template_path, output_path)
    
    # Process each file
    total_extracted = 0
    processed_files = 0
    
    for file_path in excel_files:
        logger.info(f"\nProcessing file {processed_files + 1}/{len(excel_files)}: {file_path.name}")
        
        try:
            extracted = extractor.extract_from_file(file_path)
            total_extracted += extracted
            processed_files += 1
            
            if extracted > 0:
                logger.info(f"  ✓ Extracted {extracted} record(s)")
            else:
                logger.info(f"  - No pending confirmations found")
                
        except Exception as e:
            logger.error(f"  ✗ Error processing {file_path.name}: {e}")
    
    # Save results
    if total_extracted > 0:
        extractor.save_to_template()
        
        # Print summary
        summary = extractor.get_summary()
        print("\n" + "="*60)
        print("BATCH EXTRACTION SUMMARY")
        print("="*60)
        print(f"Files processed: {processed_files}/{len(excel_files)}")
        print(f"Total records extracted: {summary['total_records']}")
        print(f"Total CAD amount: ${summary['total_amount_cad']:,.2f}")
        print(f"Total USD amount: ${summary['total_amount_usd']:,.2f}")
        
        print("\nRecords by department:")
        for dept, count in sorted(summary['by_department'].items()):
            print(f"  - {dept}: {count} records")
        
        print(f"\n✓ Output saved to: {extractor.output_path}")
    else:
        print("\n" + "="*60)
        print("BATCH EXTRACTION COMPLETE")
        print("="*60)
        print(f"Files processed: {processed_files}/{len(excel_files)}")
        print("No records with '待确认' status found in any files.")


if __name__ == '__main__':
    main()