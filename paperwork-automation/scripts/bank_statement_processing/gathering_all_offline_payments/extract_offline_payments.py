#!/usr/bin/env python3
"""
Extract offline payments that need confirmation from bank statements (Version 2).
Uses bank-specific extractors to handle different column structures.

This script:
1. Reads bank statement files with multiple sheets
2. Uses appropriate extractor based on bank type
3. Extracts rows where '是否登记线下付款表' is '待确认'
4. Appends all extracted data to a copy of the offline payment template
"""

import pandas as pd
import sys
import warnings
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import argparse
import logging
from openpyxl import load_workbook

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.bank_statement.processing_sheet import BankWorkSheetOfflinePaymentInfo, current_cad_to_usd_rate
from lib.excel_utils import suppress_excel_warnings
from bank_extractors.factory import BankExtractorFactory

# Suppress warnings
suppress_excel_warnings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OfflinePaymentExtractorV2:
    """Extract offline payments using bank-specific extractors."""
    
    def __init__(self, template_path: Path, output_path: Optional[Path] = None):
        """
        Initialize the extractor.
        
        Args:
            template_path: Path to the offline payment template
            output_path: Path for output file (default: generated with timestamp)
        """
        self.template_path = template_path
        self.output_path = output_path or self._generate_output_path()
        self.extracted_data: List[Dict[str, Any]] = []
        self.extraction_stats = {
            'by_bank': {},
            'by_department': {},
            'total_records': 0,
            'sheets_processed': 0,
            'sheets_with_data': 0
        }
        
    def _generate_output_path(self) -> Path:
        """Generate output path with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = project_root / 'output' / 'offline_payments'
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f'offline_payments_{timestamp}.xlsx'
    
    def extract_from_file(self, file_path: Path) -> int:
        """
        Extract offline payments from a bank statement file.
        
        Args:
            file_path: Path to the bank statement Excel file
            
        Returns:
            Number of records extracted
        """
        logger.info(f"Processing file: {file_path.name}")
        
        try:
            # Get all sheet names
            xlsx = pd.ExcelFile(file_path, engine='openpyxl')
            total_extracted = 0
            
            for sheet_name in xlsx.sheet_names:
                # Skip sheets not in our configuration
                if sheet_name not in BankWorkSheetOfflinePaymentInfo:
                    logger.debug(f"Skipping unconfigured sheet: {sheet_name}")
                    continue
                
                self.extraction_stats['sheets_processed'] += 1
                
                # Get bank-specific extractor
                extractor = BankExtractorFactory.create_extractor(sheet_name)
                
                if not extractor:
                    logger.warning(f"No extractor available for sheet: {sheet_name}")
                    continue
                
                # Get payment info
                payment_info = BankWorkSheetOfflinePaymentInfo[sheet_name]
                
                # Extract using bank-specific extractor
                records = extractor.extract_from_sheet(file_path, sheet_name, payment_info)
                
                if records:
                    self.extracted_data.extend(records)
                    total_extracted += len(records)
                    self.extraction_stats['sheets_with_data'] += 1
                    
                    # Update stats by bank
                    bank_type = BankExtractorFactory.get_bank_type(sheet_name)
                    if bank_type:
                        self.extraction_stats['by_bank'][bank_type] = \
                            self.extraction_stats['by_bank'].get(bank_type, 0) + len(records)
                    
                    # Update stats by department
                    dept = payment_info['department_name']
                    self.extraction_stats['by_department'][dept] = \
                        self.extraction_stats['by_department'].get(dept, 0) + len(records)
                
            self.extraction_stats['total_records'] += total_extracted
            logger.info(f"Extracted {total_extracted} records from {file_path.name}")
            return total_extracted
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return 0
    
    def save_to_template(self):
        """Save extracted data to a copy of the template."""
        if not self.extracted_data:
            logger.warning("No data to save")
            return
        
        logger.info(f"Saving {len(self.extracted_data)} records to {self.output_path}")
        
        try:
            # Read the template
            template_df = pd.read_excel(self.template_path, engine='openpyxl')
            
            # Remove the Unnamed column if it exists
            template_df = template_df.loc[:, ~template_df.columns.str.contains('^Unnamed')]
            
            # Create DataFrame from extracted data
            new_data_df = pd.DataFrame(self.extracted_data)
            
            # Get template columns (no longer handling '来源' since it's removed)
            template_columns = [col for col in template_df.columns if not col.startswith('Unnamed')]
            
            # Reorder new_data_df columns to match template
            ordered_columns = [col for col in template_columns if col in new_data_df.columns]
            new_data_df = new_data_df[ordered_columns]
            
            # Always skip the first row of template (example row) and use only new data
            final_df = new_data_df
            
            # Calculate 折算美金 if CAD currency
            if '付款币种' in final_df.columns and '付款金额（$）' in final_df.columns:
                # For CAD amounts, calculate USD equivalent
                final_df.loc[final_df['付款币种'] == 'CAD', '折算美金'] = (
                    final_df.loc[final_df['付款币种'] == 'CAD', '付款金额（$）'] * current_cad_to_usd_rate
                ).round(2)
                # For USD amounts, copy the amount directly
                final_df.loc[final_df['付款币种'] == 'USD', '折算美金'] = final_df.loc[final_df['付款币种'] == 'USD', '付款金额（$）']
            
            # Save to Excel
            with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Sheet1')
                
                # Get the worksheet to apply formatting
                worksheet = writer.sheets['Sheet1']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Successfully saved to {self.output_path}")
            
        except Exception as e:
            logger.error(f"Error saving to template: {e}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get enhanced summary of extracted data."""
        if not self.extracted_data:
            return self.extraction_stats
        
        df = pd.DataFrame(self.extracted_data)
        
        summary = {
            'total_records': len(df),
            'sheets_processed': self.extraction_stats['sheets_processed'],
            'sheets_with_data': self.extraction_stats['sheets_with_data'],
            'total_amount_cad': df[df['付款币种'] == 'CAD']['付款金额（$）'].sum() if '付款币种' in df.columns else 0,
            'total_amount_usd': df[df['付款币种'] == 'USD']['付款金额（$）'].sum() if '付款币种' in df.columns else 0,
            'by_department': self.extraction_stats['by_department'],
            'by_bank': self.extraction_stats['by_bank']
        }
        
        return summary


def main():
    """Main function to run the extraction."""
    parser = argparse.ArgumentParser(
        description='Extract offline payments using bank-specific extractors (V2)'
    )
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Path(s) to bank statement Excel files'
    )
    parser.add_argument(
        '--template',
        default='sheet-templates/offline-payment-sheet.xlsx',
        help='Path to offline payment template (default: sheet-templates/offline-payment-sheet.xlsx)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: auto-generated with timestamp)'
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
    template_path = project_root / args.template
    output_path = Path(args.output) if args.output else None
    
    # Validate template exists
    if not template_path.exists():
        logger.error(f"Template file not found: {template_path}")
        sys.exit(1)
    
    # Create extractor
    extractor = OfflinePaymentExtractorV2(template_path, output_path)
    
    # Process each input file
    total_extracted = 0
    for input_file in args.input_files:
        file_path = Path(input_file)
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
        
        extracted = extractor.extract_from_file(file_path)
        total_extracted += extracted
    
    # Save to template if we have data
    if total_extracted > 0:
        extractor.save_to_template()
        
        # Print summary
        summary = extractor.get_summary()
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY (V2 - Bank-Specific)")
        print("="*60)
        print(f"Sheets processed: {summary['sheets_processed']}")
        print(f"Sheets with data: {summary['sheets_with_data']}")
        print(f"Total records extracted: {summary['total_records']}")
        print(f"Total CAD amount: ${summary['total_amount_cad']:,.2f}")
        print(f"Total USD amount: ${summary['total_amount_usd']:,.2f}")
        print(f"Exchange rate (CAD to USD): {current_cad_to_usd_rate}")
        
        if summary['by_bank']:
            print("\nRecords by bank:")
            for bank, count in sorted(summary['by_bank'].items()):
                print(f"  - {bank}: {count} records")
        
        if summary['by_department']:
            print("\nRecords by department:")
            for dept, count in sorted(summary['by_department'].items()):
                print(f"  - {dept}: {count} records")
        
        print(f"\nOutput saved to: {extractor.output_path}")
    else:
        print("\nNo records with '待确认' status found in the provided files.")


if __name__ == '__main__':
    main()