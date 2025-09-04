# Offline Payment Extraction Scripts

This directory contains scripts for extracting offline payments that need confirmation from bank statement files.

## Overview

These scripts process bank statement Excel files and extract all rows where the `是否登记线下付款表` column contains `"待确认"` (pending confirmation). The extracted data is then formatted and appended to the offline payment template for further processing.

The system uses **bank-specific extractors** to handle different column structures and formats for BMO, CIBC, and RBC bank statements.

## Scripts

### Core Scripts

#### 1. `extract_offline_payments.py`
Main extraction script with bank-specific processing logic.

**Features:**
- **Bank-specific extractors** for BMO, CIBC, and RBC
- Handles different column names and date formats per bank
- Preserves mixed data types (text and numbers) in status column
- Detailed extraction statistics by bank and department
- Maps sheet names to company codes and department names
- Automatically calculates USD equivalents using configured exchange rate
- Formats dates as YYYY-MM-DD
- Generates timestamped output files

#### 2. `batch_extract.py`
Batch processing script for handling multiple files at once.

**Features:**
- Process entire directories of bank statements
- Recursive directory search option
- Pattern matching for file selection
- Consolidated output with summary statistics


### Bank-Specific Extractors (`bank_extractors/`)

The system includes specialized extractors for each bank type:

#### `bmo_extractor.py`
- Header at row 2 (index 1)
- Date column: `Date`
- Amount columns: `Debit`, `Credit`
- Description: `Transaction Description`

#### `cibc_extractor.py`
- Header at row 2 (index 1)
- Date column: `Date`
- Amount columns: `Debit`, `Credit`
- Description: `Transaction details`

#### `rbc_extractor.py`
- Header at row 2 (index 1)
- Date column: `Effective Date`
- Amount columns: `Debits`, `Credits` (plural)
- Description: `Description`

## Usage

### Single File Processing

```bash
# Process a single bank statement file with bank-specific logic
python scripts/bank_statement_processing/gathering_all_offline_payments/extract_offline_payments.py "history_files/bank_daily_report/2025-08/CA全部7家店明细.xlsx"

# Process multiple specific files
python scripts/bank_statement_processing/gathering_all_offline_payments/extract_offline_payments.py file1.xlsx file2.xlsx file3.xlsx

# Specify custom output path
python scripts/bank_statement_processing/gathering_all_offline_payments/extract_offline_payments.py input.xlsx --output "output/my_offline_payments.xlsx"

# Enable verbose logging to see bank-specific processing
python scripts/bank_statement_processing/gathering_all_offline_payments/extract_offline_payments.py input.xlsx --verbose
```

### Batch Processing

```bash
# Process all Excel files in a directory
python scripts/bank_statement_processing/gathering_all_offline_payments/batch_extract.py "history_files/bank_daily_report/2025-09"

# Process recursively through subdirectories
python scripts/bank_statement_processing/gathering_all_offline_payments/batch_extract.py "history_files/bank_daily_report" --recursive

# Process only files matching a specific pattern
python scripts/bank_statement_processing/gathering_all_offline_payments/batch_extract.py "history_files/bank_daily_report" --pattern "CA*.xlsx"

# Specify custom template and output
python scripts/bank_statement_processing/gathering_all_offline_payments/batch_extract.py input_dir --template "my_template.xlsx" --output "output/results.xlsx"
```

## Input File Requirements

Bank statement Excel files must have:
1. Sheet names matching those defined in `BankWorkSheetOfflinePaymentInfo`
2. Header row at row 2 (1-indexed)
3. Required columns:
   - `是否登记线下付款表` (status column)
   - `Date` (transaction date)
   - `Debit` or `Credit` (amount)
   - `品名` (item name)
   - `付款详情` or `Transaction Description`
   - `单据号` (document number, optional)

## Output Format

The output Excel file contains the following columns:
- `公司代码`: Company code (from configuration)
- `付款日期`: Payment date (YYYYMMDD format)
- `申请部门`: Department name (from configuration)
- `品名`: Item name
- `付款说明`: Payment description
- `付款币种`: Currency (CAD or USD)
- `付款金额（$）`: Payment amount
- `兑换人民币汇率`: Exchange rate (to be filled manually)
- `折算美金`: USD equivalent (to be filled manually)
- `来源`: Source (sheet name and document number)

## Configuration

The script uses the `BankWorkSheetOfflinePaymentInfo` dictionary from `configs/bank_statement/processing_sheet.py` to map sheet names to:
- Company codes
- Department names

Currently configured sheets:
- CA1D-3817 → 加拿大一店
- CA2D-6027 → 加拿大二店
- CA3D-1680 → 加拿大三店
- CA4D-1699 → 加拿大四店
- CA5D-6333 → 加拿大五店
- CA6D-6317 → 加拿大六店
- CA7D-CIBC 0401 → 加拿大七店
- RBC accounts → RBC
- Hi Bowl accounts → 加拿大Hi-Bowl一店
- BMO USD account → BMO

## Template File

The template file should be located at:
```
sheet-templates/offline-payment-sheet.xlsx
```

This template defines the column structure and formatting for the output file.

## Output Location

By default, output files are saved to:
```
output/offline_payments/offline_payments_YYYYMMDD_HHMMSS.xlsx
```

## Example Workflow

1. **Gather all bank statements for the month:**
   ```bash
   # Copy all bank statements to a working directory
   cp history_files/bank_daily_report/2025-09/*.xlsx working_dir/
   ```

2. **Run batch extraction:**
   ```bash
   python scripts/bank_statement_processing/gathering_all_offline_payments/batch_extract.py working_dir/
   ```

3. **Review the summary:**
   The script will display:
   - Total records extracted
   - Total amounts by currency
   - Breakdown by department
   - Output file location

4. **Open the output file:**
   The extracted data will be in the generated Excel file, ready for:
   - Manual review
   - Adding exchange rates
   - Further processing

## Error Handling

The scripts include robust error handling:
- Invalid file formats are skipped with warnings
- Missing columns are handled gracefully
- Sheets without the status column are skipped
- Detailed logging available with `--verbose` flag

## Troubleshooting

1. **No data extracted:**
   - Check if files contain "待确认" in the `是否登记线下付款表` column
   - Verify sheet names match configuration
   - Use `--verbose` flag for detailed logging

2. **File not found errors:**
   - Ensure file paths are correct
   - Check file permissions
   - Verify template file exists

3. **Column not found errors:**
   - Verify header is at row 2
   - Check column names match expected values
   - Some sheets may not have all columns (handled automatically)