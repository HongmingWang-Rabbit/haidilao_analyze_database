#!/usr/bin/env python3
"""
Interactive CLI Menu for Haidilao Paperwork Automation System
Streamlined workflow-focused interface for complete automation.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


class AutomationMenu:
    """Interactive menu for automation system"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        os.chdir(self.project_root)
        # Auto-detect Python command based on OS
        self.python_cmd = self.get_python_command()
        self.input_folder = self.project_root / "Input"
        self.output_folder = self.project_root / "output"

    def get_python_command(self):
        """Auto-detect appropriate Python command based on OS"""
        if os.name == 'nt':  # Windows
            return 'py'
        else:  # macOS, Linux
            return 'python3'

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print menu header"""
        print("🍲" + "=" * 60 + "🍲")
        print("    HAIDILAO PAPERWORK AUTOMATION SYSTEM")
        print("         Streamlined Workflow Interface")
        print("🍲" + "=" * 60 + "🍲")
        print()

    def print_menu_section(self, title: str, options: List[Tuple[str, str, str]]):
        """Print a menu section with options"""
        print(f"📋 {title}")
        print("-" * (len(title) + 4))
        for key, description, _ in options:
            print(f"  {key}) {description}")
        print()

    def run_command(self, command: str, description: str) -> bool:
        """Run a command and return success status with detailed error logging"""
        print(f"🔄 Running: {description}...")
        print(f"Command: {command}")
        print("-" * 60)

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            if result.returncode == 0:
                # Show success message and any important output
                print("✅ Finished successfully")
                if result.stdout.strip():
                    print("Output:")
                    print(result.stdout.strip())
                return True
            else:
                # Show detailed error information
                print(f"❌ ERROR: {description} failed")
                print(f"Exit code: {result.returncode}")

                if result.stdout.strip():
                    print("\n📋 STDOUT:")
                    print("-" * 40)
                    print(result.stdout.strip())

                if result.stderr.strip():
                    print("\n🚨 STDERR:")
                    print("-" * 40)
                    print(result.stderr.strip())

                print("\n" + "=" * 60)
                print("⚠️  Command failed. Please review the error details above.")
                print("💡 Common solutions:")
                print("   - Check if the input file exists and is not corrupted")
                print("   - Verify the file path contains no special characters")
                print("   - Ensure the database connection is working")
                print("   - Check for missing dependencies or modules")
                print("=" * 60)

                # Wait for user to review the error
                input("Press Enter to continue...")
                return False

        except Exception as e:
            print(f"❌ EXCEPTION: {description} failed - {str(e)}")
            print("=" * 60)
            print("⚠️  An unexpected error occurred while running the command.")
            print("💡 This might indicate a system-level issue or missing dependencies.")
            print("=" * 60)
            input("Press Enter to continue...")
            return False

    def run_command_with_details(self, command: str, description: str) -> dict:
        """Run a command and return detailed results including output parsing"""
        try:
            # Set environment to handle Unicode properly
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                encoding='utf-8', errors='replace', env=env)

            # Parse output for extraction statistics
            output = result.stdout + result.stderr

            details = {
                'success': result.returncode == 0,
                'description': description,
                'output': output,
                'error_log': None,
                'percentage': None,
                'stats': None
            }

            # Parse dish-material extraction results
            if 'dish-material' in description.lower():
                import re
                # Look for success/failure stats in the ASCII format
                inserted_match = re.search(
                    r'\[INFO\] Inserted:\s*(\d+)', output)
                updated_match = re.search(r'\[INFO\] Updated:\s*(\d+)', output)
                errors_match = re.search(r'\[ERROR\] Errors:\s*(\d+)', output)

                if inserted_match and updated_match:
                    inserted = int(inserted_match.group(1))
                    updated = int(updated_match.group(1))
                    errors = int(errors_match.group(1)) if errors_match else 0

                    total_processed = inserted + updated + errors
                    successful = inserted + updated

                    if total_processed > 0:
                        details['percentage'] = round(
                            (successful / total_processed) * 100, 1)
                        details['stats'] = f"{successful}/{total_processed}"

                # Look for failure analysis file
                failure_analysis_match = re.search(
                    r'Failure analysis:\s*([^\n]+)', output)
                if failure_analysis_match:
                    details['error_log'] = failure_analysis_match.group(
                        1).strip()

            # Parse monthly performance extraction results
            elif any(keyword in description.lower() for keyword in ['monthly dish sales performance', 'monthly material usage performance']):
                import re
                # Look for database insertion stats like dish-material script
                inserted_match = re.search(
                    r'\[INFO\] Inserted:\s*(\d+)', output)
                updated_match = re.search(r'\[INFO\] Updated:\s*(\d+)', output)
                errors_match = re.search(r'\[ERROR\] Errors:\s*(\d+)', output)

                if inserted_match or updated_match:
                    inserted = int(inserted_match.group(1)
                                   ) if inserted_match else 0
                    updated = int(updated_match.group(
                        1)) if updated_match else 0
                    errors = int(errors_match.group(1)) if errors_match else 0

                    total_processed = inserted + updated + errors
                    successful = inserted + updated

                    if total_processed > 0:
                        details['percentage'] = round(
                            (successful / total_processed) * 100, 1)
                        details['stats'] = f"{successful}/{total_processed}"
                    elif successful > 0:
                        # If we have successful records but no errors reported
                        details['percentage'] = 100.0
                        details['stats'] = f"{successful} records"

                # Also look for alternative patterns like "Processed X records"
                if details['percentage'] is None:
                    processed_match = re.search(
                        r'Processed\s+(\d+)\s+(?:records|dishes|materials)', output, re.IGNORECASE)
                    if processed_match:
                        processed_count = int(processed_match.group(1))
                        details['stats'] = f"{processed_count} records"
                        details['percentage'] = 100.0

                # Check for partial success messages
                if details['percentage'] is None and 'some errors but most data processed' in output.lower():
                    # Assume 85% success for partial completions
                    details['percentage'] = 85.0
                    details['stats'] = "Partial success"

            # Parse other extraction results (dishes master data, materials master data)
            elif any(keyword in description.lower() for keyword in ['dish sales', 'material usage']) and 'performance' not in description.lower():
                import re
                # Look for dishes processing stats
                if 'dish sales' in description.lower():
                    # Look for "Processed X unique dishes" and total records
                    dishes_match = re.search(
                        r'Processed\s+(\d+)\s+unique\s+dishes', output)
                    total_match = re.search(
                        r'Total\s+processed:\s+(\d+)\s+records', output)
                    if dishes_match and total_match:
                        dishes_count = int(dishes_match.group(1))
                        total_count = int(total_match.group(1))
                        details['stats'] = f"{total_count} records"
                        details['percentage'] = 100.0

                # Look for materials processing stats
                elif 'material usage' in description.lower():
                    # Look for materials processing patterns
                    materials_match = re.search(
                        r'(\d+)\s+materials?\s+processed', output, re.IGNORECASE)
                    if materials_match:
                        materials_count = int(materials_match.group(1))
                        details['stats'] = f"{materials_count} materials"
                        details['percentage'] = 100.0

            # Parse report generation results
            elif 'report generation' in description.lower():
                import re
                # Look for successful report generation indicators
                if 'report saved' in output.lower() or 'generated successfully' in output.lower():
                    details['percentage'] = 100.0
                    details['stats'] = "Report generated"
                # Look for worksheet counts
                worksheet_match = re.search(
                    r'(\d+)\s+worksheets?\s+generated', output, re.IGNORECASE)
                if worksheet_match:
                    worksheet_count = int(worksheet_match.group(1))
                    details['stats'] = f"{worksheet_count} worksheets"

            if details['success']:
                print("Finished")
            else:
                if details['percentage'] is not None and details['percentage'] > 0:
                    print(f"Partial success ({details['percentage']}%)")
                else:
                    print(f"ERROR: {description} failed")

            return details

        except Exception as e:
            return {
                'success': False,
                'description': description,
                'output': str(e),
                'error_log': None,
                'percentage': None,
                'stats': None
            }

    def check_input_files(self, report_type: str) -> bool:
        """Check if required input files exist for the report type"""
        print(f"🔍 Checking {report_type} input files...")

        if report_type == "daily":
            required_paths = [
                self.input_folder / "daily_report" / "daily_store_report",
                self.input_folder / "daily_report" / "time_segment_store_report"
                # Store 6 conversion file no longer required - legacy feature disabled
            ]
        elif report_type == "monthly":
            required_paths = [
                self.input_folder / "monthly_report" / "monthly_dish_sale",
                self.input_folder / "monthly_report" / "material_detail",
                self.input_folder / "monthly_report" / "inventory_checking_result",
                self.input_folder / "monthly_report" / "calculated_dish_material_usage"
            ]
        else:
            return False

        missing_files = []
        for path in required_paths:
            if not path.exists():
                missing_files.append(str(path))
                continue

            # Special handling for folders with store subfolders
            if "inventory_checking_result" in str(path) or "material_detail" in str(path):
                # Check for store subfolders (1, 2, 7, etc.)
                store_folders = [d for d in path.iterdir(
                ) if d.is_dir() and d.name.isdigit()]
                if not store_folders:
                    missing_files.append(f"{path} (no store subfolders found)")
                    continue

                # Check if at least one store folder has files
                has_files = False
                for store_folder in store_folders:
                    store_files = list(store_folder.glob(
                        "*.xls*")) + list(store_folder.glob("*.XLS*"))
                    if store_files:
                        has_files = True
                        break

                if not has_files:
                    missing_files.append(
                        f"{path} (no Excel files found in store subfolders)")
            else:
                # Check if folder has files (handle both uppercase and lowercase extensions)
                files = list(path.glob("*.xls*")) + list(path.glob("*.XLS*"))
                if not files:
                    missing_files.append(f"{path} (no Excel files found)")

        if missing_files:
            print("❌ Missing required files:")
            for file in missing_files:
                print(f"   - {file}")
            print("\nPlease ensure all required files are in the Input folder.")
            input("Press Enter to continue...")
            return False

        print("✅ All required input files found!")
        return True

    def show_bank_processing_menu(self):
        """Show bank processing submenu with options for transactions and offline payments"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🏦 BANK PROCESSING MENU")
            print("=" * 40)

            options = [
                ("1", "📈 Daily Bank Transaction Processing", "transactions"),
                ("2", "💳 Extract Offline Payments (待确认)", "offline_payments"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select bank processing operation", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.run_bank_processing()
            elif choice == '2':
                self.extract_offline_payments()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def extract_offline_payments(self):
        """Extract offline payments with 待确认 status from bank statements"""
        print("💳 OFFLINE PAYMENT EXTRACTION")
        print("=" * 40)
        print("This will extract all transactions with '待确认' status")
        print("from the bank statement files and generate a summary report.")
        print()
        
        # Get target date from user
        print("📅 Enter target date (YYYY-MM-DD format):")
        print("Example: 2025-09-02")
        print()
        
        date_input = input("Enter date: ").strip()
        
        # Validate date format
        if not date_input:
            print("❌ No date provided")
            input("Press Enter to continue...")
            return
        
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_input, '%Y-%m-%d')
            year_month = target_date.strftime('%Y-%m')
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD format.")
            input("Press Enter to continue...")
            return
        
        # Build the path to the bank daily report folder
        bank_report_dir = self.project_root / "history_files" / "bank_daily_report" / year_month
        
        if not bank_report_dir.exists():
            print(f"❌ Directory not found: {bank_report_dir}")
            print(f"   Please ensure bank statements for {year_month} are available.")
            input("Press Enter to continue...")
            return
        
        # Find all Excel files in the directory
        excel_files = list(bank_report_dir.glob("*.xlsx")) + list(bank_report_dir.glob("*.xls"))
        
        if not excel_files:
            print(f"❌ No Excel files found in: {bank_report_dir}")
            input("Press Enter to continue...")
            return
        
        print(f"\n📂 Found {len(excel_files)} Excel file(s) in {year_month}:")
        for file in excel_files[:5]:  # Show first 5 files
            print(f"   - {file.name}")
        if len(excel_files) > 5:
            print(f"   ... and {len(excel_files) - 5} more")
        
        # Confirm extraction
        print(f"\n🔍 This will extract offline payments from all files in {year_month}")
        confirm = input("Proceed with extraction? (y/N): ").lower()
        
        if confirm != 'y':
            return
        
        # Run the extraction script
        print("\n" + "="*60)
        
        # Build file list as space-separated quoted paths
        file_list = ' '.join([f'"{file}"' for file in excel_files])
        
        # Run extraction command
        command = f'{self.python_cmd} scripts/bank_statement_processing/gathering_all_offline_payments/extract_offline_payments.py {file_list}'
        
        success = self.run_command(command, "Extract Offline Payments")
        
        if success:
            print("\n✅ Extraction completed successfully!")
            print("📁 Output file saved to: output/offline_payments/")
        else:
            print("\n❌ Extraction failed. Please check the error messages above.")
        
        input("\nPress Enter to continue...")

    def run_bank_processing(self):
        """Run daily bank transaction processing using new update system"""
        print("🏦 DAILY BANK STATEMENT UPDATE PROCESSING")
        print("=" * 50)
        print("This will update the CA全部7家店明细.xlsx workbook with new transactions")
        print("and automatically classify them according to our transaction rules.")
        print()

        # Get target date from user
        print("📅 Enter target date for processing:")
        print("Format: YYYY-MM-DD (e.g., 2025-08-15)")
        print("Press Enter for today's date")
        print("Note: Processes entire month regardless of day")

        date_input = input("\nTarget date: ").strip()

        if not date_input:
            from datetime import datetime
            target_date = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                from datetime import datetime
                datetime.strptime(date_input, '%Y-%m-%d')
                target_date = date_input
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")
                input("Press Enter to continue...")
                return

        print(f"📅 Processing bank transactions for: {target_date}")
        
        # Parse month/year for checking files
        from datetime import datetime
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        month_folder = target_dt.strftime('%Y-%m')
        
        # Quick check if required files exist
        from pathlib import Path
        bank_folder = Path("history_files/bank_daily_report") / month_folder
        if not bank_folder.exists():
            print(f"\n❌ Bank folder not found: {bank_folder}")
            print("Please ensure bank files are placed in the correct directory.")
            input("Press Enter to continue...")
            return

        ca_file = bank_folder / "CA全部7家店明细.xlsx"
        if not ca_file.exists():
            print(f"\n❌ Workbook not found: CA全部7家店明细.xlsx")
            print(f"   Expected location: {ca_file}")
            print("This file is required for the update process.")
            input("Press Enter to continue...")
            return

        print(f"\n✅ Found required files in {month_folder}/")

        # Confirm before processing
        confirm = input("\nStart bank statement update processing? (y/N): ").lower()
        if confirm != 'y':
            print("❌ Processing cancelled.")
            input("Press Enter to continue...")
            return

        # Run the bank processing command
        command = f'{self.python_cmd} -m scripts.process_bank_updates --target-date {target_date}'
        print(f"🚀 Running: {command}")

        result = self.run_command(command, "Bank Statement Update Processing")

        if result:
            print("\n✅ Bank statement processing completed successfully!")
            print(f"📁 Check output/bank_statements/{month_folder}/ for Updated_CA全部7家店明细.xlsx")
            print("\n✨ The updated file includes:")
            print("   • New transactions appended to each bank sheet")
            print("   • Auto-classified transaction categories (品名)")
            print("   • Payment details (付款详情) filled in")
            print("   • Items needing review marked as '待确认'")
        else:
            print("\n❌ Bank statement processing failed.")

        input("\nPress Enter to continue...")
    
    def run_hi_bowl_daily_processing(self):
        """Run Hi-Bowl daily report processing"""
        print("🍜 HI-BOWL DAILY REPORT PROCESSING")
        print("=" * 50)
        print("This will process Hi-Bowl daily transaction data and generate")
        print("the overseas business reporting template (海外新业态管报数据).")
        print()
        
        # Check for Hi-Bowl input files
        hi_bowl_daily_path = self.input_folder / "daily_report" / "hi-bowl-report" / "daily-data"
        if not hi_bowl_daily_path.exists():
            print("❌ Hi-Bowl daily data folder not found!")
            print(f"   Expected path: {hi_bowl_daily_path}")
            print("\n📁 Please create the folder structure and place your Hi-Bowl Excel files there.")
            input("Press Enter to continue...")
            return
            
        # List available files
        hi_bowl_files = list(hi_bowl_daily_path.glob("*.xls*"))
        hi_bowl_files = [f for f in hi_bowl_files if not f.name.startswith("~$")]  # Filter temp files
        
        # Remove duplicates (in case of case-insensitive filesystems)
        seen_files = set()
        unique_files = []
        for f in hi_bowl_files:
            if f.name.lower() not in seen_files:
                seen_files.add(f.name.lower())
                unique_files.append(f)
        hi_bowl_files = unique_files
        
        if not hi_bowl_files:
            print("❌ No Excel files found in Hi-Bowl daily data folder!")
            print(f"   Path: {hi_bowl_daily_path}")
            input("Press Enter to continue...")
            return
            
        print("📁 Available Hi-Bowl files:")
        for i, file in enumerate(hi_bowl_files, 1):
            print(f"   {i}. {file.name}")
        print()
        
        # Let user select file
        if len(hi_bowl_files) == 1:
            selected_file = hi_bowl_files[0]
            print(f"📄 Using file: {selected_file.name}")
        else:
            while True:
                try:
                    choice = input(f"Select file (1-{len(hi_bowl_files)}): ").strip()
                    idx = int(choice) - 1
                    if 0 <= idx < len(hi_bowl_files):
                        selected_file = hi_bowl_files[idx]
                        break
                    else:
                        print("❌ Invalid selection. Please try again.")
                except ValueError:
                    print("❌ Please enter a number.")
        
        # Get target month
        print("\n📅 Enter target month for processing:")
        print("Format: YYYY-MM (e.g., 2025-07)")
        print("Press Enter to auto-detect from filename")
        
        month_input = input("\nTarget month: ").strip()
        
        if not month_input:
            # Try to detect from filename
            import re
            match = re.search(r'(\d{4})-(\d{1,2})', selected_file.name)
            if match:
                year = match.group(1)
                month = match.group(2).zfill(2)
                target_month = f"{year}{month}"
                print(f"📅 Auto-detected month: {year}-{month}")
            else:
                print("❌ Could not auto-detect month from filename.")
                input("Press Enter to continue...")
                return
        else:
            try:
                from datetime import datetime
                dt = datetime.strptime(month_input, '%Y-%m')
                target_month = dt.strftime('%Y%m')
                print(f"📅 Using month: {month_input}")
            except ValueError:
                print("❌ Invalid month format. Please use YYYY-MM format.")
                input("Press Enter to continue...")
                return
        
        # Generate output filename
        output_filename = f"hi_bowl_report_{target_month}.xlsx"
        output_path = self.project_root / "output" / "hi-bowl" / output_filename
        
        print(f"\n📤 Output will be saved to: {output_path}")
        
        # Confirm before processing
        confirm = input("\nStart Hi-Bowl report processing? (y/N): ").lower()
        if confirm != 'y':
            print("❌ Processing cancelled.")
            input("Press Enter to continue...")
            return
        
        # Run the Hi-Bowl processing command
        command = f'{self.python_cmd} scripts/process_hi_bowl_daily.py --input-file "{selected_file}" --output-file "{output_path}" --target-month {target_month}'
        print(f"🚀 Running Hi-Bowl processor...")
        
        result = self.run_command(command, "Hi-Bowl Daily Report Processing")
        
        if result:
            print("\n✅ Hi-Bowl report processing completed successfully!")
            print(f"📊 Report saved to: {output_path}")
            print("\n📋 The report includes:")
            print("   • 收入(含税) - Revenue with tax")
            print("   • 收入(不含税) - Revenue without tax")
            print("   • 优惠总金额 - Total discount amounts")
            print("   • 营业天数 - Operating days statistics")
            print("   • 就餐人数 - Guest counts by weekday/weekend")
            print("   • 订单数量 - Order counts analysis")
        else:
            print("\n❌ Hi-Bowl report processing failed.")
            print("Please check the error messages above.")
        
        input("\nPress Enter to continue...")

    def run_complete_daily_automation(self):
        """Run complete daily automation workflow"""
        from datetime import datetime

        if not self.check_input_files("daily"):
            return

        confirm = input("Start complete daily automation? (y/N): ").lower()
        if confirm != 'y':
            return

        print("Starting complete daily automation...")

        # Step 1: Extract daily store reports
        daily_store_path = self.input_folder / "daily_report" / "daily_store_report"
        daily_files = list(daily_store_path.glob("*.xls*")) + \
            list(daily_store_path.glob("*.XLS*"))
        # Filter out temporary Excel files (starting with ~$)
        daily_files = [f for f in daily_files if not f.name.startswith("~$")]
        if daily_files:
            daily_file = daily_files[0]
            command = f'{self.python_cmd} scripts/extract_all.py "{daily_file}" --daily-only --direct-db'
            if not self.run_command(command, "Daily Store Report Extraction"):
                return

        # Step 2: Extract time segment reports (separate file)
        time_segment_path = self.input_folder / \
            "daily_report" / "time_segment_store_report"
        time_files = list(time_segment_path.glob("*.xls*")) + \
            list(time_segment_path.glob("*.XLS*"))
        # Filter out temporary Excel files (starting with ~$)
        time_files = [f for f in time_files if not f.name.startswith("~$")]
        if time_files:
            time_file = time_files[0]
            command = f'{self.python_cmd} scripts/extract_all.py "{time_file}" --time-only --direct-db'
            if not self.run_command(command, "Time Segment Report Extraction"):
                return

        # Step 3: Get target date from user and generate daily report
        print("\n📅 Enter target date for daily report generation:")
        print("Format options:")
        print("  - YYYY-MM-DD (e.g., 2025-06-30)")
        print("  - Press Enter for today's date")

        date_input = input("\nEnter target date: ").strip()

        # Parse and validate the date
        if not date_input:
            target_date = datetime.now().strftime('%Y-%m-%d')
            print(f"📅 Using today's date: {target_date}")
        else:
            try:
                datetime.strptime(date_input, '%Y-%m-%d')
                target_date = date_input
                print(f"📅 Using specified date: {target_date}")
            except ValueError:
                print("❌ Invalid date format. Using today's date instead.")
                target_date = datetime.now().strftime('%Y-%m-%d')
                print(f"📅 Using today's date: {target_date}")

        print(f"\nGenerating report for {target_date}...")
        command = f'{self.python_cmd} -m scripts.generate_database_report --date {target_date}'
        if not self.run_command(command, "Daily Report Generation"):
            return

        print("Complete daily automation finished")

        # Final confirmation step - show results and wait for user review
        print()
        print("=" * 60)
        print("📊 DAILY AUTOMATION RESULTS SUMMARY")
        print("=" * 60)
        print("✅ Daily store reports extraction: Completed")
        print("✅ Time segment reports extraction: Completed")
        print(f"✅ Daily report generation for {target_date}: Completed")
        print("📝 All data has been processed and report generated")
        print("📋 Report includes 6 worksheets:")
        print("   • 对比上月表 (Monthly Comparison)")
        print("   • 同比数据 (Yearly Comparison)")
        print("   • 对比上年表 (Year-over-Year Comparison)")
        print("   • 分时段-上报 (Time Segment Report)")
        print("   • 营业透视 (Business Insight)")
        print("   • 门店日-加拿大 (Daily Store Tracking)")
        print()
        print("🎉 Daily automation workflow completed successfully!")
        print("=" * 60)

        # Wait for user confirmation before clearing console
        input("Press Enter to continue...")

    def extract_month_year_from_filename(self, file_path: str) -> tuple:
        """Extract month and year from filename"""
        from datetime import datetime
        import re

        filename = Path(file_path).name

        # Try different patterns
        # Pattern 1: YYYYMM format
        pattern1 = re.search(r'(\d{4})(\d{2})', filename)
        if pattern1:
            year, month = int(pattern1.group(1)), int(pattern1.group(2))
            if 1 <= month <= 12:
                return month, year

        # Pattern 2: YYYY-MM format
        pattern2 = re.search(r'(\d{4})-(\d{1,2})', filename)
        if pattern2:
            year, month = int(pattern2.group(1)), int(pattern2.group(2))
            if 1 <= month <= 12:
                return month, year

        # Pattern 3: Current date as fallback
        now = datetime.now()
        print(
            f"⚠️  Could not extract date from filename, using current date: {now.year}-{now.month:02d}")
        return now.month, now.year

    def extract_target_date_from_files(self):
        """Extract and validate target date from monthly input files"""
        print("🔍 Extracting target date from input files...")

        # Use local date extraction function

        # Find monthly dish sales file (primary date source)
        monthly_dish_path = self.input_folder / "monthly_report" / "monthly_dish_sale"
        dish_files = list(monthly_dish_path.glob("*.xls*")) + \
            list(monthly_dish_path.glob("*.XLS*"))
        dish_files = [f for f in dish_files if not f.name.startswith("~$")]

        if not dish_files:
            print("❌ No monthly dish sales file found for date extraction")
            return None

        dish_file = dish_files[0]

        try:
            month, year = self.extract_month_year_from_filename(str(dish_file))
            target_date = f"{year}-{month:02d}-01"  # Use first day of month
            target_period = f"{year}-{month:02d}"

            print(f"📅 Target Period: {target_period} (from {dish_file.name})")

            # Validate date consistency with other files
            date_warnings = []

            # Check calculated dish material file
            dish_material_path = self.input_folder / \
                "monthly_report" / "calculated_dish_material_usage"
            dish_material_files = list(dish_material_path.glob(
                "*.xls*")) + list(dish_material_path.glob("*.XLS*"))
            if dish_material_files:
                calc_file = dish_material_files[0]
                # Simple check for YYMM pattern in filename
                if "2505" in calc_file.name and target_period == "2025-06":
                    date_warnings.append(
                        f"⚠️  Calculated dish materials appear to be from May (2025-05) while dish sales are from June (2025-06)")
                elif "2504" in calc_file.name and target_period == "2025-06":
                    date_warnings.append(
                        f"⚠️  Calculated dish materials appear to be from April (2025-04) while dish sales are from June (2025-06)")

            if date_warnings:
                print("\n⚠️  Date consistency warnings:")
                for warning in date_warnings:
                    print(f"   {warning}")
                print("   This may indicate mixed data from different periods.")

                proceed = input("\nProceed anyway? (y/N): ").lower()
                if proceed != 'y':
                    return None

            return target_date, target_period

        except Exception as e:
            print(f"❌ Error extracting date: {e}")
            return None

    def run_complete_monthly_automation(self):
        """Run complete monthly automation workflow - NEW WORKFLOW

        This performs a comprehensive monthly data processing with new approach:
        1. Extract from monthly_dish_sale: dish_type, dish_child_type, dish, dish_price_history, dish_monthly_sale
        2. Extract from material_detail: material, material_price_history  
        3. Extract from inventory_checking_result: inventory_count, material_price_history
        4. Extract from calculated_dish_material_usage: dish_material relationships
        5. Generate material variance analysis report
        """
        if not self.check_input_files("monthly"):
            return

        print("\n🍲 COMPLETE MONTHLY AUTOMATION - NEW WORKFLOW")
        print("=" * 60)
        print(
            "This will process ALL monthly data files in the Input/monthly_report folder:")
        print("📊 Monthly dish sales → dish types, dishes, price history, sales data")
        print("📦 Material details → materials, material price history")
        print("🏪 Inventory checking results → inventory counts by store")
        print("🔗 Calculated dish-material usage → dish-material relationships")
        print("📋 Generate reports:")
        print("   • Material variance analysis report")
        print("   • Beverage variance analysis report")
        print("   • Monthly gross margin analysis report (毛利相关分析指标)")
        print()

        # Get target date - either from files or user input
        print("📅 Detecting target date from current files...")

        # Try to extract date from files first
        file_date_result = self.extract_target_date_from_files()

        if file_date_result:
            suggested_date, period_info = file_date_result
            print(f"✅ Detected date from files: {period_info}")
            print("\nOptions:")
            print(f"  1. Use detected date: {suggested_date}")
            print("  2. Enter different date (YYYY-MM-DD)")

            choice = input("\nEnter choice (1/2): ").strip()

            if choice == "2":
                date_input = input("Enter target date (YYYY-MM-DD): ").strip()
                try:
                    from datetime import datetime
                    datetime.strptime(date_input, '%Y-%m-%d')
                    target_date = date_input
                except ValueError:
                    print(
                        f"❌ Invalid format. Using detected date: {suggested_date}")
                    target_date = suggested_date
            else:
                target_date = suggested_date
        else:
            # Fallback to manual input
            print("⚠️ Could not detect date from files.")
            print("📅 Enter target date manually:")
            print("Format: YYYY-MM-DD (e.g., 2025-06-30)")

            date_input = input("\nEnter date: ").strip()

            if not date_input:
                target_date = "2025-06-30"  # Fallback default
            else:
                try:
                    from datetime import datetime
                    datetime.strptime(date_input, '%Y-%m-%d')
                    target_date = date_input
                except ValueError:
                    print("❌ Invalid date format. Using fallback date 2025-06-30.")
                    target_date = "2025-06-30"

        print(f"📅 Using target date: {target_date}")

        # Get inventory count date separately
        print("\n📦 Enter inventory count date:")
        print("This is the actual date when physical inventory counting was performed.")
        print("Format: YYYY-MM-DD (e.g., 2025-06-28)")
        print(f"Press Enter to use target date ({target_date})")

        inventory_date_input = input("\nEnter inventory count date: ").strip()

        if not inventory_date_input:
            inventory_count_date = target_date
        else:
            try:
                from datetime import datetime
                datetime.strptime(inventory_date_input, '%Y-%m-%d')
                inventory_count_date = inventory_date_input
            except ValueError:
                print(
                    f"❌ Invalid date format. Using target date: {target_date}")
                inventory_count_date = target_date

        print(f"📦 Using inventory count date: {inventory_count_date}")

        confirm = input(
            "\nStart complete monthly automation with new workflow? (y/N): ").lower()
        if confirm != 'y':
            return

        print("\n🚀 Starting complete monthly automation...")

        # Note: Database migrations are one-time operations and should be run manually
        # if needed from the Database Management menu

        # Run the new monthly automation script
        command = f'{self.python_cmd} -m scripts.complete_monthly_automation_new --date {target_date} --inventory-count-date {inventory_count_date}'
        success = self.run_command(
            command, "Complete Monthly Automation - New Workflow")

        if success:
            print("\n" + "=" * 70)
            print("🎉 COMPLETE MONTHLY AUTOMATION FINISHED SUCCESSFULLY!")
            print("=" * 70)
            print("✅ All monthly data has been processed and imported")
            print("✅ Material variance analysis report has been generated")
            print("✅ Beverage variance analysis report has been generated")
            print("✅ Monthly gross margin analysis report has been generated")
            print("📁 Check the output/ folder for generated reports")
            print("📊 Database has been updated with all monthly data")
        else:
            print("\n" + "=" * 70)
            print("⚠️  COMPLETE MONTHLY AUTOMATION FINISHED WITH ISSUES")
            print("=" * 70)
            print("❌ Some steps may have encountered errors")
            print("📋 Check the logs above for details")
            print("💡 Partial success is normal due to data inconsistencies")

        print("=" * 70)

        # Wait for user confirmation before clearing console
        input("Press Enter to continue...")

    def show_single_extraction_menu(self):
        """Show single extraction submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("📤 SINGLE EXTRACTION")
            print("=" * 30)

            options = [
                ("1", "Daily Store Report (File → Database)", "daily_store"),
                ("2", "Time Segment Report (File → Database)", "time_segment"),
                # ("3", "Store 6 Conversion (New Logic)", "store6"),  # Disabled - no longer needed
                ("4", "Monthly Dish Sales (File → Database)", "monthly_dish"),
                ("5", "Monthly Material Usage (File → Database)", "monthly_material"),
                ("6", "Calculated Dish Materials (File → Database)", "dish_materials"),
                ("7", "Materials Master Data (File → Database)", "materials"),
                ("8", "Material Detail with Types (File → Database)",
                 "material_detail_types"),
                ("9", "Dishes Master Data (File → Database)", "dishes"),
                ("0", "Dish Price History (File → Database)", "price_history"),
                ("p", "Material Prices by Store (File → Database)",
                 "material_prices_store"),
                ("z", "Batch Extract Material Prices (All Stores)",
                 "batch_material_prices"),
                ("h", "Historical Data Extraction (All Months)",
                 "historical_data"),
                ("i", "📊 Inventory Calculation Data (All Months)",
                 "inventory_calculation"),
                ("t", "🏦 Bank Transaction Processing (Daily)", "bank_transactions"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select extraction type", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.extract_with_file_selection(
                    "daily_store", "Daily Store Report")
            elif choice == '2':
                self.extract_with_file_selection(
                    "time_segment", "Time Segment Report")
            # elif choice == '3':
            #     self.extract_with_file_selection(
            #         "store6", "Store 6 Conversion")  # Disabled - no longer needed
            elif choice == '4':
                self.extract_with_file_selection(
                    "monthly_dish", "Monthly Dish Sales")
            elif choice == '5':
                self.extract_with_file_selection(
                    "monthly_material", "Monthly Material Usage")
            elif choice == '6':
                self.extract_with_file_selection(
                    "dish_materials", "Calculated Dish Materials")
            elif choice == '7':
                self.extract_materials()
            elif choice == '8':
                self.extract_material_detail_with_types()
            elif choice == '9':
                self.extract_dishes()
            elif choice == '0':
                self.extract_with_file_selection(
                    "price_history", "Dish Price History")
            elif choice == 'p':
                self.extract_material_prices_by_store()
            elif choice == 'z':
                self.extract_material_prices_batch()
            elif choice == 'h':
                self.extract_historical_data()
            elif choice == 'i':
                self.extract_inventory_calculation_data()
            elif choice == 't':
                self.process_bank_transactions()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def extract_with_file_selection(self, extraction_type: str, description: str):
        """Extract data with file selection"""
        excel_file = self.get_excel_file()
        if not excel_file:
            return

        commands = {
            'daily_store': f'{self.python_cmd} scripts/extract_all.py "{excel_file}" --daily-only --direct-db',
            'time_segment': f'{self.python_cmd} scripts/extract_all.py "{excel_file}" --time-only --direct-db',
            # 'store6': f'{self.python_cmd} -m scripts.convert_other_source "{excel_file}"',  # Disabled - no longer needed
            'monthly_dish': f'{self.python_cmd} scripts/extract_dish_monthly_sales.py "{excel_file}" --direct-db',
            'monthly_material': f'{self.python_cmd} scripts/extract_material_monthly_usage.py "{excel_file}" --direct-db',
            'dish_materials': f'{self.python_cmd} -m scripts.extract-dish-materials "{excel_file}" --direct-db',
            'price_history': f'{self.python_cmd} scripts/extract_dish_price_history.py "{excel_file}" --direct-db'
        }

        if extraction_type in commands:
            self.run_command(commands[extraction_type],
                             f"Extract {description}")

    def show_single_generate_menu(self):
        """Show single report generation submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("📊 SINGLE REPORT GENERATION")
            print("=" * 40)

            options = [
                ("1", "Database Report (6 Worksheets)", "database_report"),
                ("2", "Monthly Comparison Report", "monthly_comparison"),
                ("3", "Yearly Comparison Report", "yearly_comparison"),
                ("4", "Time Segment Report", "time_segment_report"),
                ("5", "Business Insight Report", "business_insight"),
                ("6", "Monthly Dishes Report", "monthly_dishes"),
                ("7", "Daily Store Tracking Report", "daily_tracking"),
                ("8", "Monthly Material Report with Usage Summary",
                 "monthly_material_usage"),
                ("9", "Monthly Material Report with Detailed Spending",
                    "monthly_detailed_spending"),
                ("g", "Gross Margin Report (毛利报表)", "gross_margin_report"),
                ("v", "Monthly Beverage Report", "monthly_beverage_report"),
                ("r", "Monthly Store Revenue & Turnover Compare", "monthly_revenue_compare"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select report type", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.generate_database_report()
            elif choice == '2':
                self.generate_specific_report("monthly_comparison")
            elif choice == '3':
                self.generate_specific_report("yearly_comparison")
            elif choice == '4':
                self.generate_specific_report("time_segment")
            elif choice == '5':
                self.generate_specific_report("business_insight")
            elif choice == '6':
                self.generate_monthly_dishes_report()
            elif choice == '7':
                self.generate_daily_tracking_report()
            elif choice == '8':
                self.generate_monthly_material_usage_report()
            elif choice == '9':
                self.generate_monthly_detailed_spending_report()
            elif choice == 'g':
                self.generate_gross_margin_report()
            elif choice == 'v':
                self.generate_monthly_beverage_report()
            elif choice == 'r':
                self.generate_monthly_revenue_compare_report()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def show_single_conversion_menu(self):
        """Show single conversion submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🔄 SINGLE CONVERSION")
            print("=" * 30)

            options = [
                # Disabled - no longer needed
                ("1", "Snappy to BI Format Conversion", "store6_conversion"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select conversion type", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.convert_store6_data()  # Disabled - no longer needed

            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def show_single_web_scraping_menu(self):
        """Show single web scraping submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🕷️  SINGLE WEB SCRAPING")
            print("=" * 35)

            options = [
                ("1", "QBI System Scraping", "qbi_scraping"),
                ("2", "Daily Reports Scraping", "daily_scraping"),
                ("3", "Monthly Reports Scraping", "monthly_scraping"),
                ("4", "Debug QBI Connection", "qbi_debug"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select scraping type", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.run_qbi_scraping()
            elif choice == '2':
                print("⚠️  Daily reports scraping not yet implemented")
                input("Press Enter to continue...")
            elif choice == '3':
                print("⚠️  Monthly reports scraping not yet implemented")
                input("Press Enter to continue...")
            elif choice == '4':
                self.debug_qbi_connection()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def show_testing_menu(self):
        """Show testing submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🧪 TESTING")
            print("=" * 20)

            options = [
                ("1", "Run Comprehensive Tests", "comprehensive"),
                ("2", "Run Specific Test Module", "specific"),
                ("3", "Test Database Connection", "db_test"),
                ("4", "Validate Test Data", "validate"),
                ("5", "Test Analysis & Coverage", "analysis"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select test type", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.run_comprehensive_tests()
            elif choice == '2':
                self.run_specific_test()
            elif choice == '3':
                self.test_database_connection()
            elif choice == '4':
                self.validate_test_data()
            elif choice == '5':
                self.run_test_analysis()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def show_database_management_menu(self):
        """Show database management submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🗄️  DATABASE MANAGEMENT")
            print("=" * 35)

            options = [
                ("1", "Reset Database (Full)", "reset_full"),
                ("2", "Reset Test Database", "reset_test"),
                ("3", "Reset Materials Only (Development)", "reset_materials_only"),
                ("4", "Migrate: Add Loss Rate Column", "migrate_loss_rate"),
                ("5", "Migrate: Add Material Type Tables", "migrate_material_types"),
                ("6", "Migrate: Add Combo Tables", "migrate_combo_tables"),
                ("7", "Migrate: Add Unit Conversion Rate Column",
                 "migrate_unit_conversion_rate"),
                ("8", "Insert Constant Data", "insert_const"),
                ("9", "Insert Monthly Targets", "insert_targets"),
                ("a", "Verify Database Structure", "verify_structure"),
                ("0", "Show Database Status", "show_status"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select database operation", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.reset_database(test_only=False)
            elif choice == '2':
                self.reset_database(test_only=True)
            elif choice == '3':
                self.reset_materials_only()
            elif choice == '4':
                self.run_loss_rate_migration()
            elif choice == '5':
                self.run_material_type_migration()
            elif choice == '6':
                self.run_combo_tables_migration()
            elif choice == '7':
                self.run_unit_conversion_rate_migration()
            elif choice == '8':
                self.insert_constant_data()
            elif choice == '9':
                self.insert_monthly_targets()
            elif choice == 'a':
                self.verify_database_structure()
            elif choice == '0':
                self.show_database_status()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def show_system_menu(self):
        """Show system submenu"""
        while True:
            self.clear_screen()
            self.print_header()
            print("⚙️  SYSTEM")
            print("=" * 20)

            options = [
                ("1", "Show System Status", "status"),
                ("2", "Show Help & Documentation", "help"),
                ("3", "Check Dependencies", "dependencies"),
                ("4", "Show Input Folder Structure", "input_structure"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select system operation", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            elif choice == '1':
                self.show_status()
            elif choice == '2':
                self.show_help()
            elif choice == '3':
                self.check_dependencies()
            elif choice == '4':
                self.show_input_structure()
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def show_input_structure(self):
        """Show Input folder structure"""
        print("📁 INPUT FOLDER STRUCTURE")
        print("=" * 40)
        print(f"Root: {self.input_folder}")
        print()

        if not self.input_folder.exists():
            print("❌ Input folder does not exist!")
            input("Press Enter to continue...")
            return

        def print_tree(path: Path, prefix: str = "", is_last: bool = True):
            """Print directory tree structure"""
            if path.is_dir():
                print(f"{prefix}{'└── ' if is_last else '├── '}{path.name}/")
                items = sorted(path.iterdir())
                for i, item in enumerate(items):
                    is_last_item = i == len(items) - 1
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    if item.is_dir():
                        print_tree(item, new_prefix, is_last_item)
                    else:
                        print(
                            f"{new_prefix}{'└── ' if is_last_item else '├── '}{item.name}")

        print_tree(self.input_folder)
        print()
        input("Press Enter to continue...")

    def show_main_menu(self):
        """Display main menu and handle user input"""
        while True:
            self.clear_screen()
            self.print_header()

            # Main workflow options
            workflow_options = [
                ("1", "🏦 Bank Processing (Transactions & Offline Payments)", "bank_menu"),
                ("2", "🍜 Hi-Bowl Daily Report Processing", "hi_bowl_processing"),
                ("3", "🌅 Complete Daily Automation", "daily_automation"),
                ("4", "📅 Complete Monthly Automation", "monthly_automation"),
            ]
            self.print_menu_section(
                "🚀 COMPLETE AUTOMATION WORKFLOWS", workflow_options)

            # Single operation options
            single_options = [
                ("5", "📤 Single Extraction", "single_extraction"),
                ("6", "📊 Single Report Generation", "single_generate"),
                ("7", "🔄 Single Conversion", "single_conversion"),
                ("8", "🕷️  Single Web Scraping", "single_scraping"),
            ]
            self.print_menu_section("🔧 SINGLE OPERATIONS", single_options)

            # System options
            system_options = [
                ("9", "🧪 Testing", "testing"),
                ("10", "🗄️  Database Management", "database"),
                ("11", "⚙️  System", "system"),
                ("q", "🚪 Quit", "quit")
            ]
            self.print_menu_section("🛠️  SYSTEM & MAINTENANCE", system_options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == '1':
                self.show_bank_processing_menu()
            elif choice == '2':
                self.run_hi_bowl_daily_processing()
            elif choice == '3':
                self.run_complete_daily_automation()
            elif choice == '4':
                self.run_complete_monthly_automation()
            elif choice == '5':
                self.show_single_extraction_menu()
            elif choice == '6':
                self.show_single_generate_menu()
            elif choice == '7':
                self.show_single_conversion_menu()
            elif choice == '8':
                self.show_single_web_scraping_menu()
            elif choice == '9':
                self.show_testing_menu()
            elif choice == '10':
                self.show_database_management_menu()
            elif choice == '11':
                self.show_system_menu()
            elif choice == 'q':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    # Helper methods (preserve existing functionality)
    def get_excel_file(self) -> Optional[str]:
        """Get Excel file path from user"""
        print("📁 SELECT EXCEL FILE")
        print("=" * 30)
        print("Please enter the path to your Excel file:")
        print("(You can drag and drop the file here, or type the full path)")
        print()

        file_path = input("Excel file path: ").strip().strip('"').strip("'")

        if not file_path:
            print("❌ No file path provided")
            return None

        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return None

        if not file_path.lower().endswith(('.xlsx', '.xls')):
            print(f"❌ File must be an Excel file (.xlsx or .xls)")
            return None

        return file_path

    def generate_database_report(self):
        """Generate comprehensive database report"""
        print("📊 Generating comprehensive database report (6 worksheets)...")
        print("This will create a complete Excel report with all business analysis worksheets.")

        # Get target date from user
        print("\n📅 Enter target date for the report:")
        print("Format options:")
        print("  - YYYY-MM-DD (e.g., 2025-06-28)")
        print("  - Press Enter for today's date")

        date_input = input("\nEnter date: ").strip()

        # Parse and validate the date
        if not date_input:
            from datetime import datetime
            target_date = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                from datetime import datetime
                datetime.strptime(date_input, '%Y-%m-%d')
                target_date = date_input
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")
                input("Press Enter to continue...")
                return

        print(f"📅 Using target date: {target_date}")
        print("📋 Report will include:")
        print("   1. 对比上月表 (Monthly Comparison)")
        print("   2. 同比数据 (Yearly Comparison)")
        print("   3. 对比上年表 (Year-over-Year Comparison)")
        print("   4. 分时段-上报 (Time Segment Report)")
        print("   5. 营业透视 (Business Insight)")
        print("   6. 门店日-加拿大 (Daily Store Tracking)")

        confirm = input(
            "\nGenerate database report with this date? (y/N): ").lower()
        if confirm != 'y':
            return

        command = f'{self.python_cmd} -m scripts.generate_database_report --date {target_date}'
        self.run_command(command, "Generate Database Report")

    def generate_monthly_dishes_report(self):
        """Generate standalone monthly dishes report"""
        print("Generating monthly dishes report...")
        print(
            "This will create a standalone Excel file with dish-material relationship data.")

        # Get target date from user
        print("\n📅 Enter target date for the report:")
        print("Format options:")
        print("  - YYYY-MM (e.g., 2025-06)")
        print("  - YYYY-MM-DD (e.g., 2025-06-15)")
        print("  - Press Enter for current month")

        date_input = input("\nEnter date: ").strip()

        # Parse and validate the date
        target_date = self.parse_date_input(date_input)
        if not target_date:
            print("❌ Invalid date format")
            input("Press Enter to continue...")
            return

        print(f"📅 Using target date: {target_date}")
        confirm = input("Generate report with this date? (y/N): ").lower()
        if confirm != 'y':
            return

        # Create a temporary script to generate the monthly dishes report with both worksheets
        temp_script = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from lib.monthly_dishes_worksheet import MonthlyDishesWorksheetGenerator
    from lib.database_queries import ReportDataProvider
    from utils.database import DatabaseConfig, DatabaseManager
    from openpyxl import Workbook
    from datetime import datetime

    # Initialize database connection
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    data_provider = ReportDataProvider(db_manager)

    # Store mapping
    store_names = {{
        1: "加拿大一店", 2: "加拿大二店", 3: "加拿大三店", 4: "加拿大四店",
        5: "加拿大五店", 6: "加拿大六店", 7: "加拿大七店"
    }}

    # Use target date from user input
    target_date = "{target_date}"

    print(f"📊 Generating monthly dishes report for {{target_date}}")

    # Create workbook and generator
    wb = Workbook()
    if wb.active:
        wb.remove(wb.active)

    generator = MonthlyDishesWorksheetGenerator(store_names, target_date)

    # Generate material variance analysis worksheet
    print("📈 Generating material usage variance analysis worksheet...")
    try:
        variance_ws = generator.generate_material_variance_worksheet(wb, data_provider)
        print(f"✅ Variance worksheet created: {{variance_ws.title if variance_ws else 'None'}}")
    except Exception as e:
        print(f"❌ Error generating variance worksheet: {{e}}")
        import traceback
        traceback.print_exc()

    print(f"📋 Total worksheets in workbook: {{len(wb.worksheets)}}")
    for i, ws in enumerate(wb.worksheets, 1):
        print(f"   {{i}}. {{ws.title}}")

    if not wb.worksheets:
        print("❌ ERROR: No worksheets generated")
        sys.exit(1)

    # Save report
    output_path = f"output/monthly_dishes_report_{{target_date.replace('-', '_')}}.xlsx"
    wb.save(output_path)
    print(f"✅ Monthly dishes report saved: {{output_path}}")
    print(f"📋 Report includes:")
    for i, ws in enumerate(wb.worksheets, 1):
        print(f"   {{i}}. {{ws.title}}")

except Exception as e:
    print(f"❌ FATAL ERROR: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        # Write temporary script and execute
        from pathlib import Path
        temp_file = Path("temp_monthly_dishes_script.py")

        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(temp_script)

            command = f'{self.python_cmd} {temp_file}'
            success = self.run_command(
                command, "Generate Monthly Dishes Report")

            if success:
                print("📊 Monthly dishes report generated successfully!")

        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()

    def generate_daily_tracking_report(self):
        """Generate standalone daily store tracking report"""
        print("🏪 Generating daily store tracking report...")
        print("This will create a standalone Excel file with daily store performance tracking.")

        # Get target date from user
        print("\n📅 Enter target date for the report:")
        print("Format options:")
        print("  - YYYY-MM-DD (e.g., 2025-06-28)")
        print("  - Press Enter for today's date")

        date_input = input("\nEnter date: ").strip()

        # Parse and validate the date
        if not date_input:
            from datetime import datetime
            target_date = datetime.now().strftime('%Y-%m-%d')
        else:
            try:
                from datetime import datetime
                datetime.strptime(date_input, '%Y-%m-%d')
                target_date = date_input
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")
                input("Press Enter to continue...")
                return

        print(f"📅 Using target date: {target_date}")
        confirm = input(
            "Generate daily tracking report with this date? (y/N): ").lower()
        if confirm != 'y':
            return

        # Create a temporary script to generate the daily tracking report
        temp_script = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from lib.daily_store_tracking_worksheet import DailyStoreTrackingGenerator
    from lib.database_queries import ReportDataProvider
    from utils.database import DatabaseConfig, DatabaseManager
    from openpyxl import Workbook

    # Initialize database connection
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    data_provider = ReportDataProvider(db_manager)

    # Use target date from user input
    target_date = "{target_date}"

    print(f"🏪 Generating daily store tracking report for {{target_date}}")

    # Create workbook and generator
    wb = Workbook()
    if wb.active:
        wb.remove(wb.active)

    generator = DailyStoreTrackingGenerator(data_provider)

    # Generate daily tracking worksheet
    print("📊 Generating daily store tracking worksheet...")
    generator.generate_worksheet(wb, target_date)
    
    print(f"📋 Total worksheets in workbook: {{len(wb.worksheets)}}")
    for i, ws in enumerate(wb.worksheets, 1):
        print(f"   {{i}}. {{ws.title}}")

    if not wb.worksheets:
        print("❌ ERROR: No worksheets generated")
        sys.exit(1)

    # Save report
    output_path = f"output/daily_store_tracking_{{target_date.replace('-', '_')}}.xlsx"
    wb.save(output_path)
    print(f"✅ Daily store tracking report saved: {{output_path}}")

except Exception as e:
    print(f"❌ FATAL ERROR: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        # Write temporary script and execute
        from pathlib import Path
        temp_file = Path("temp_daily_tracking_script.py")

        try:
            temp_file.write_text(temp_script)
            command = f'{self.python_cmd} {temp_file}'
            result = self.run_command(
                command, "Daily Store Tracking Report Generation")
            if result:
                print("✅ Daily store tracking report generated successfully!")
            else:
                print("❌ Failed to generate daily store tracking report")

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
            input("Press Enter to continue...")

    def generate_monthly_material_usage_report(self):
        """Generate monthly report with material usage summary"""
        print("📊 Generating monthly report with material usage summary...")
        print("This will create a monthly report with material usage summary by store and material type.")

        # Get target date from user
        print("\n📅 Enter target date for the report:")
        print("Format options:")
        print("  - YYYY-MM (e.g., 2025-06)")
        print("  - YYYY-MM-DD (e.g., 2025-06-15)")
        print("  - Press Enter for current month")

        date_input = input("\nEnter date: ").strip()

        # Parse and validate the date
        target_date = self.parse_date_input(date_input)
        if not target_date:
            print("❌ Invalid date format")
            input("Press Enter to continue...")
            return

        print(f"📅 Using target date: {target_date}")
        confirm = input(
            "Generate monthly report with this date? (y/N): ").lower()
        if confirm != 'y':
            return

        # Create command to run monthly material report generation
        command = f'{self.python_cmd} -m scripts.generate_monthly_material_report --date {target_date}'
        success = self.run_command(
            command, "Generate Monthly Material Report with Usage Summary")

        if success:
            print("📊 Monthly report with material usage summary generated successfully!")
            print("📋 The report includes:")
            print("   1. 月度统计概览 (Monthly Statistics Overview)")
            print("   2. 物料差异分析 (Material Variance Analysis)")
            print("   3. 物料使用汇总 (Material Usage Summary)")
        else:
            print("❌ Failed to generate monthly report")

        input("Press Enter to continue...")

    def generate_monthly_detailed_spending_report(self):
        """Generate monthly report with detailed material spending worksheets for each store"""
        print("📊 GENERATE MONTHLY REPORT WITH DETAILED MATERIAL SPENDING")
        print("=" * 65)
        print("This will generate a comprehensive monthly report including:")
        print("✅ 月度统计概览 (Monthly Statistics Overview)")
        print("✅ 物料差异分析 (Material Variance Analysis)")
        print("✅ 物料使用汇总 (Material Usage Summary)")
        print("✅ 物料明细-[门店名] (Detailed Material Spending per Store)")
        print()
        print("Each store will get its own detailed worksheet showing:")
        print("   📋 Individual material usage with amounts")
        print("   🏷️  Material classifications and categories")
        print("   💰 Usage quantities, unit prices, and totals")
        print("   📊 Subtotals by material type and grand totals")
        print()

        # Get target date
        date_input = input(
            "Enter target date (YYYY-MM-DD) or press Enter for current month: ").strip()
        target_date = self.parse_date_input(date_input)

        if not target_date:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
            input("Press Enter to continue...")
            return

        print(f"📅 Target date: {target_date}")
        confirm = input(
            "Generate detailed monthly report? (y/N): ").lower()
        if confirm != 'y':
            return

        # Create command to run monthly material report generation
        command = f'{self.python_cmd} -m scripts.generate_monthly_material_report --date {target_date}'
        success = self.run_command(
            command, "Generate Monthly Material Report with Detailed Spending")

        if success:
            print(
                "📊 Monthly report with detailed material spending generated successfully!")
            print("📋 The report includes:")
            print("   1. 月度统计概览 (Monthly Statistics Overview)")
            print("   2. 物料差异分析 (Material Variance Analysis)")
            print("   3. 物料使用汇总 (Material Usage Summary)")
            print("   4. 物料明细-[门店名] (Detailed Spending for each Store)")
            print()
            print("💡 Each store worksheet shows individual material consumption")
            print("   with detailed breakdowns by material type and category.")
        else:
            print("❌ Failed to generate detailed monthly report")

        input("Press Enter to continue...")

    def generate_monthly_beverage_report(self):
        """Generate monthly beverage report with variance analysis"""
        print("🍺 GENERATE MONTHLY BEVERAGE REPORT")
        print("=" * 45)
        print("This will generate a comprehensive monthly beverage report including:")
        print("✅ 酒水统计概览 (Beverage Statistics Overview)")
        print("✅ 酒水汇总表 (Beverage Summary by Store)")
        print("✅ 酒水差异明细表 (Beverage Variance Details)")
        print()
        print("The report compares system sales data with inventory counts for:")
        print("   🍺 Alcoholic beverages (含酒精饮料)")
        print("   🥤 Non-alcoholic beverages (无酒精饮料)")
        print("   💧 Water and other beverages (水及其他饮品)")
        print()

        # Get target date
        date_input = input(
            "Enter target date (YYYY-MM-DD) or press Enter for current month: ").strip()
        target_date = self.parse_date_input(date_input)

        if not target_date:
            print("❌ Invalid date format. Please use YYYY-MM-DD")
            input("Press Enter to continue...")
            return

        print(f"📅 Target date: {target_date}")
        confirm = input(
            "Generate monthly beverage report? (y/N): ").lower()
        if confirm != 'y':
            return

        # Create command to run monthly beverage report generation
        command = f'{self.python_cmd} -m scripts.generate_monthly_beverage_report --date {target_date}'
        success = self.run_command(
            command, "Generate Monthly Beverage Report")

        if success:
            print(
                "🍺 Monthly beverage report generated successfully!")
            print("📋 The report includes:")
            print("   1. 酒水统计概览 (Beverage Statistics Overview)")
            print("   2. 酒水汇总表 (Beverage Summary by Store)")
            print("   3. 酒水差异明细表 (Beverage Variance Details)")
            print()
            print("💡 The report shows variance between system sales and inventory counts")
            print("   for all beverage-related items across all stores.")
        else:
            print("❌ Failed to generate monthly beverage report")

        input("Press Enter to continue...")

    def generate_monthly_revenue_compare_report(self):
        """Generate monthly store revenue and turnover rate comparison report"""
        print("📊 MONTHLY STORE REVENUE & TURNOVER COMPARISON")
        print("=" * 50)
        print("This will generate a monthly comparison report showing:")
        print("✅ Revenue comparison for all 7 Canadian stores")
        print("✅ Turnover rate comparison for all stores")
        print("✅ Year-over-year percentage changes")
        print()

        # Get year and month
        print("📅 Enter the target year and month:")
        year_input = input("Year (e.g., 2025): ").strip()
        month_input = input("Month (1-12): ").strip()

        try:
            year = int(year_input)
            month = int(month_input)
            
            if year < 2020 or year > 2030:
                print("❌ Invalid year. Please enter a year between 2020 and 2030.")
                input("Press Enter to continue...")
                return
            
            if month < 1 or month > 12:
                print("❌ Invalid month. Please enter a month between 1 and 12.")
                input("Press Enter to continue...")
                return
                
        except ValueError:
            print("❌ Invalid input. Please enter numeric values.")
            input("Press Enter to continue...")
            return

        print(f"\n📅 Target period: {year}-{month:02d}")
        print(f"📊 Will compare with: {year-1}-{month:02d}")
        
        # Define output path
        output_filename = f"monthly_revenue_compare_{year}{month:02d}.xlsx"
        output_path = self.output_folder / "monthly-revenue-compare" / output_filename
        
        print(f"📁 Output will be saved to: {output_path}")
        
        confirm = input("\nGenerate monthly revenue comparison report? (y/N): ").lower()
        if confirm != 'y':
            return

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Import and run the generator
        try:
            import sys
            import os
            # Add parent directory to path for imports
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from utils.database import DatabaseManager, DatabaseConfig
            from lib.monthly_store_revenue_compare_worksheet import MonthlyStoreRevenueCompareWorksheet
            
            # Create database manager
            config = DatabaseConfig()
            db_manager = DatabaseManager(config)
            
            # Create generator
            generator = MonthlyStoreRevenueCompareWorksheet(db_manager)
            
            # Generate report
            print("\n🔄 Generating report...")
            success = generator.generate_report(year, month, str(output_path))
            
            if success:
                print("✅ Monthly revenue comparison report generated successfully!")
                print(f"📁 Report saved to: {output_path}")
                print("\n📋 The report includes:")
                print("   • Revenue data for all 7 Canadian stores")
                print("   • Turnover rate data for all stores")
                print("   • Year-over-year comparison percentages")
                print("   • Monthly totals and averages")
            else:
                print("❌ Failed to generate monthly revenue comparison report")
                
        except Exception as e:
            print(f"❌ Error generating report: {str(e)}")
            import traceback
            traceback.print_exc()

        input("\nPress Enter to continue...")

    def parse_date_input(self, date_input: str) -> str:
        """Parse user date input and return formatted date string"""
        from datetime import datetime

        if not date_input:
            # Use current month
            return datetime.now().strftime('%Y-%m-%d')

        try:
            # Try YYYY-MM format
            if len(date_input) == 7 and '-' in date_input:
                year, month = date_input.split('-')
                year, month = int(year), int(month)
                if 1 <= month <= 12 and 2020 <= year <= 2030:
                    return f"{year}-{month:02d}-01"

            # Try YYYY-MM-DD format
            elif len(date_input) == 10 and date_input.count('-') == 2:
                parts = date_input.split('-')
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if 1 <= month <= 12 and 1 <= day <= 31 and 2020 <= year <= 2030:
                    return f"{year}-{month:02d}-{day:02d}"

            # Try parsing as date object
            else:
                parsed_date = datetime.strptime(date_input, '%Y-%m-%d')
                return parsed_date.strftime('%Y-%m-%d')

        except (ValueError, IndexError):
            pass

        return None

    def generate_gross_margin_report(self):
        """Generate gross margin report (毛利报表)"""
        print("📊 Generating gross margin report (毛利报表)...")
        print("This will create a comprehensive gross margin analysis report.")

        # Get target date from user
        print("\n📅 Enter target date for the report:")
        print("Format options:")
        print("  - YYYY-MM-DD (e.g., 2025-06-30)")
        print("  - Press Enter for current month end")

        date_input = input("\nEnter date: ").strip()

        # Parse and validate the date
        if not date_input:
            from datetime import datetime
            today = datetime.now()
            # Use last day of current month
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            target_date = f"{today.year}-{today.month:02d}-{last_day:02d}"
        else:
            try:
                from datetime import datetime
                datetime.strptime(date_input, '%Y-%m-%d')
                target_date = date_input
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")
                input("Press Enter to continue...")
                return

        print(f"📅 Using target date: {target_date}")
        print("📋 Report will include:")
        print("   1. 菜品价格变动及菜品损耗表 (Detailed Revenue Data)")
        print("   2. 原材料成本变动表 (Material Cost Analysis)")
        print("   3. 打折优惠表 (Discount Analysis)")
        print("   4. 各店毛利率分析 (Store Gross Profit Analysis)")

        confirm = input(
            "\nGenerate gross margin report with this date? (y/N): ").lower()
        if confirm != 'y':
            return

        command = f'{self.python_cmd} -m scripts.generate_gross_margin_report --target-date {target_date}'
        success = self.run_command(command, "Generate Gross Margin Report")

        if success:
            print("✅ Gross margin report generated successfully!")
            print("📋 The report includes:")
            print("   1. 菜品价格变动及菜品损耗表 (Detailed Revenue Data)")
            print("   2. 原材料成本变动表 (Material Cost Analysis)")
            print("   3. 打折优惠表 (Discount Analysis)")
            print("   4. 各店毛利率分析 (Store Gross Profit Analysis)")
        else:
            print("❌ Failed to generate gross margin report")

        input("Press Enter to continue...")

    def generate_specific_report(self, report_type: str):
        """Generate specific report type"""
        # Implementation for specific report generation
        print(f"⚠️  {report_type} report generation not yet implemented")
        input("Press Enter to continue...")

    def convert_store6_data(self):
        """Convert Store 6 data"""
        excel_file = self.get_excel_file()
        if excel_file:
            command = f'{self.python_cmd} -m scripts.convert_other_source "{excel_file}"'
            self.run_command(command, "Convert Store 6 Data")

    def convert_legacy_format(self):
        """Convert legacy format data"""
        print("⚠️  Legacy format conversion not yet implemented")
        input("Press Enter to continue...")

    def run_qbi_scraping(self):
        """Run QBI scraping"""
        command = f'{self.python_cmd} scripts/qbi_scraper_cli.py'
        self.run_command(command, "QBI System Scraping")

    def debug_qbi_connection(self):
        """Debug QBI connection"""
        command = f'{self.python_cmd} scripts/qbi_debug_test.py'
        self.run_command(command, "Debug QBI Connection")

    def run_comprehensive_tests(self):
        """Run comprehensive tests"""
        command = f'{self.python_cmd} -m unittest tests.test_* -v'
        self.run_command(command, "Comprehensive Test Suite")

    def run_specific_test(self):
        """Run specific test module"""
        print("🧪 AVAILABLE TEST MODULES")
        print("=" * 35)
        test_modules = [
            "test_business_insight_worksheet",
            "test_yearly_comparison_worksheet",
            "test_time_segment_worksheet",
            "test_extract_all",
            "test_validation_against_actual_data"
        ]

        for i, module in enumerate(test_modules, 1):
            print(f"  {i}) {module}")

        try:
            choice = int(input("\nSelect test module (number): "))
            if 1 <= choice <= len(test_modules):
                module = test_modules[choice - 1]
                command = f'{self.python_cmd} -m unittest tests.{module} -v'
                self.run_command(command, f"Test Module: {module}")
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")
        except ValueError:
            print("❌ Please enter a valid number")
            input("Press Enter to continue...")

    def test_database_connection(self):
        """Test database connection"""
        print("🗄️  TESTING DATABASE CONNECTIONS")
        print("=" * 40)

        try:
            from utils.database import verify_database_connection

            print("Testing production database...")
            prod_result = verify_database_connection(is_test=False)
            print(
                f"Production: {'✅ Connected' if prod_result else '❌ Failed'}")

            print("Testing test database...")
            test_result = verify_database_connection(is_test=True)
            print(f"Test: {'✅ Connected' if test_result else '❌ Failed'}")

        except Exception as e:
            print(f"❌ Error testing connections: {e}")

        input("\nPress Enter to continue...")

    def validate_test_data(self):
        """Validate test data"""
        command = f'{self.python_cmd} tests/test_validation_against_actual_data.py'
        self.run_command(command, "Validate Test Data")

    def run_test_analysis(self):
        """Run test analysis"""
        command = f'{self.python_cmd} tests/run_comprehensive_tests.py'
        self.run_command(command, "Test Analysis & Coverage")

    def reset_database(self, test_only: bool = False):
        """Reset database"""
        db_type = "test" if test_only else "production"
        confirm = input(
            f"⚠️  Reset {db_type} database? This will delete all data! (y/N): ").lower()

        if confirm == 'y':
            reset_script = self.project_root / "haidilao-database-querys" / "reset-db.sql"
            if reset_script.exists():
                # Implementation depends on database reset script
                print(f"🔄 Resetting {db_type} database...")
                print("⚠️  Database reset implementation needed")
                input("Press Enter to continue...")
            else:
                print("❌ Reset script not found")
                input("Press Enter to continue...")

    def reset_materials_only(self):
        """Reset material tables only using the development reset script"""
        print("🧪 RESET MATERIALS ONLY (DEVELOPMENT)")
        print("=" * 50)
        print("This will reset ONLY material-related tables:")
        print("🔄 DROP: material_monthly_usage, inventory_count, material_price_history")
        print("🔄 DROP: dish_material, material, material_child_type, material_type")
        print("✅ RECREATE: All material tables with correct schema")
        print("✅ INSERT: Default material types and child types")
        print()
        print("⚠️  WARNING: This will delete all material data but preserve:")
        print("   ✅ Stores, dishes, and dish sales data")
        print("   ✅ All other non-material tables")
        print()
        print("📄 Reset script: tests/reset_materials_only.sql")

        # Ask for database choice
        print("\n🗄️  Database Selection:")
        print("1. Test database (recommended)")
        print("2. Production database")

        db_choice = input("Enter choice (1/2): ").strip()
        use_test_db = db_choice != '2'
        db_name = "test" if use_test_db else "production"

        print(f"\n📊 Target database: {db_name}")
        confirm = input(
            f"Reset materials in {db_name} database? (y/N): ").lower()

        if confirm != 'y':
            return

        reset_script = self.project_root / "tests" / "reset_materials_only.sql"
        if not reset_script.exists():
            print("❌ Reset script not found: tests/reset_materials_only.sql")
            input("Press Enter to continue...")
            return

        # Run the reset using Python database helper
        command = f'{self.python_cmd} -m tests.test_material_reset'
        if not use_test_db:
            command += " --production-db"

        success = self.run_command(
            command, f"Reset Materials Only ({db_name} database)")

        if success:
            print("✅ Material tables reset completed successfully!")
            print("📊 All material tables have been recreated with proper schema")
            print("📝 Default material types and child types have been inserted")
            print()
            print("💡 You can now run material extraction to populate the tables")
        else:
            print("❌ Material reset failed. Check the error messages above.")

        input("Press Enter to continue...")

    def run_loss_rate_migration(self):
        """Run database migration to add loss_rate column"""
        print("🔧 DATABASE MIGRATION: Add Loss Rate Column")
        print("=" * 50)
        print("This will add the loss_rate column to the dish_material table.")
        print("This is required for proper material variance calculations.")
        print()
        print("⚠️  Note: This is a one-time migration. If already applied, this will fail.")
        print("📄 Migration file: haidilao-database-querys/add_loss_rate_column.sql")
        print()

        # Check if migration file exists
        migration_file = Path(
            "haidilao-database-querys/add_loss_rate_column.sql")
        if not migration_file.exists():
            print(
                "ℹ️  Migration file not found - this migration was likely already applied.")
            print("📋 Loss rate column should already exist in dish_material table.")
            print("🔍 Use Database Status to verify the current database structure.")
            input("Press Enter to continue...")
            return

        confirm = input("Run migration? (y/N): ").lower()
        if confirm != 'y':
            return

        command = f'{self.python_cmd} -m scripts.migrate_add_loss_rate'
        self.run_command(command, "Add Loss Rate Column Migration")

    def run_material_type_migration(self):
        """Run database migration to add material type tables"""
        print("🔧 DATABASE MIGRATION: Add Material Type Tables")
        print("=" * 50)
        print("This will add material classification tables similar to dish types:")
        print("✅ Create material_type table (11 types)")
        print("✅ Create material_child_type table (6 child types)")
        print("✅ Add material_type_id column to material table")
        print("✅ Add material_child_type_id column to material table")
        print("✅ Create appropriate indexes and triggers")
        print("✅ Insert initial material type data")
        print()

        confirm = input("Run migration? (y/N): ").lower()
        if confirm != 'y':
            return

        command = f'{self.python_cmd} -m scripts.migrate_add_material_types_simple'
        self.run_command(command, "Add Material Type Tables Migration")

    def run_combo_tables_migration(self):
        """Run database migration to add combo tables"""
        print("🔧 DATABASE MIGRATION: Add Combo Tables")
        print("=" * 50)
        print("This will add combo support to the database:")
        print("✅ Create combo table (套餐基础信息)")
        print("✅ Create monthly_combo_dish_sale table (套餐菜品销售数据)")
        print("✅ Add appropriate indexes and triggers")
        print("✅ Enable combo usage in material calculations")
        print()
        print("⚠️  This migration is safe and will not affect existing data.")
        print("    Tables will only be created if they don't already exist.")
        print()

        confirm = input("Run migration? (y/N): ").lower()
        if confirm != 'y':
            return

        command = f'{self.python_cmd} -m scripts.migrate_add_combo_tables'
        self.run_command(command, "Add Combo Tables Migration")

    def run_unit_conversion_rate_migration(self):
        """Run database migration to add unit_conversion_rate column to dish_material table"""
        print("🔧 DATABASE MIGRATION: Add Unit Conversion Rate Column")
        print("=" * 60)
        print("This will add unit conversion rate support to the dish_material table:")
        print("✅ Add unit_conversion_rate column to dish_material table")
        print("✅ Set default value of 1.0 for existing records")
        print("✅ Update extraction scripts to capture unit conversion from '物料单位' field")
        print("✅ Update material report calculations to apply conversion")
        print()
        print("📋 Example usage:")
        print("   - Dish 1060062 with material 1500882 has conversion rate 0.354")
        print("   - 理论用量 and 套餐用量 will be divided by conversion rate")
        print("   - If '物料单位' is blank, defaults to 1.0 (no conversion)")
        print()
        print("⚠️  This migration is safe and will not affect existing data.")
        print("    Existing records will get default conversion rate of 1.0.")
        print()

        confirm = input("Run migration? (y/N): ").lower()
        if confirm != 'y':
            return

        # Run the migration SQL script directly
        migration_file = self.project_root / "haidilao-database-querys" / \
            "add_unit_conversion_rate_column.sql"

        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            input("Press Enter to continue...")
            return

        # Use psql command to run the migration
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'hongming')
        db_password = os.getenv('DB_PASSWORD', '8894')
        db_name = os.getenv('DB_NAME', 'haidilao-paperwork')

        command = f'PGPASSWORD={db_password} psql -h {db_host} -U {db_user} -d {db_name} -f "{migration_file}"'

        success = self.run_command(
            command, "Add Unit Conversion Rate Column Migration")

        if success:
            print()
            print("✅ Migration completed successfully!")
            print("💡 Next steps:")
            print("   1. Run dish-material extraction to populate unit conversion rates")
            print("   2. Generate material reports to see conversion applied")
            print(
                "   3. Run tests to verify functionality: python3 -m unittest tests.test_unit_conversion_rate")
        else:
            print("❌ Migration failed. Please check the error output above.")

        input("Press Enter to continue...")

    def insert_constant_data(self):
        """Insert constant data"""
        command = f'{self.python_cmd} -c "exec(open(\'haidilao-database-querys/insert_const_data.sql\').read())"'
        self.run_command(command, "Insert Constant Data")

    def insert_monthly_targets(self):
        """Insert monthly targets"""
        command = f'{self.python_cmd} -c "exec(open(\'haidilao-database-querys/insert_monthly_target.sql\').read())"'
        self.run_command(command, "Insert Monthly Targets")

    def verify_database_structure(self):
        """Verify database structure"""
        print("🔍 VERIFYING DATABASE STRUCTURE")
        print("=" * 40)
        print("⚠️  Database structure verification not yet implemented")
        input("Press Enter to continue...")

    def show_database_status(self):
        """Show database status"""
        self.show_status()

    def extract_materials(self):
        """Extract materials from Excel file"""
        excel_file = self.get_excel_file()
        if excel_file:
            command = f'{self.python_cmd} -m scripts.extract-materials "{excel_file}" --direct-db'
            self.run_command(command, "Extract Materials to Database")

    def extract_material_detail_with_types(self):
        """Extract material detail with type classifications from Excel file"""
        excel_file = self.get_excel_file()
        if excel_file:
            command = f'{self.python_cmd} -m scripts.extract_material_detail_with_types "{excel_file}" --direct-db'
            self.run_command(
                command, "Extract Material Detail with Types to Database")

    def extract_dishes(self):
        """Extract dishes from Excel file"""
        excel_file = self.get_excel_file()
        if excel_file:
            command = f'{self.python_cmd} -m scripts.extract-dishes "{excel_file}" --direct-db'
            self.run_command(command, "Extract Dishes to Database")

    def extract_material_prices_by_store(self):
        """Extract material prices by store from Excel file"""
        excel_file = self.get_excel_file()
        if not excel_file:
            return

        # Ask for store ID (optional, can be auto-detected)
        print("🏪 Store ID Detection:")
        print("1. Auto-detect from filename/file content")
        print("2. Manually specify store ID")

        choice = input("Enter your choice (1 or 2): ").strip()

        command = f'{self.python_cmd} scripts/extract_material_prices_by_store.py --input "{excel_file}"'

        if choice == '2':
            store_id = input("Enter store ID (1-8): ").strip()
            try:
                store_id = int(store_id)
                if 1 <= store_id <= 8:
                    command += f' --store-id {store_id}'
                else:
                    print("❌ Invalid store ID. Using auto-detection.")
            except ValueError:
                print("❌ Invalid store ID. Using auto-detection.")

        self.run_command(command, "Extract Material Prices by Store")

    def extract_material_prices_batch(self):
        """Batch extract material prices from all store folders"""
        print("🏪 Batch Material Price Extraction")
        print("This will process all store folders in material_detail directory")
        print("📁 Expected structure:")
        print("   Input/monthly_report/material_detail/")
        print("   ├── 1/ (store 1 files)")
        print("   ├── 2/ (store 2 files)")
        print("   ├── 3/ (store 3 files)")
        print("   └── ... (other stores)")

        # Ask for custom path (optional)
        print("\n🗂️ Material Detail Path")
        print("Default: Input/monthly_report/material_detail")
        custom_path = input(
            "Enter custom path or press Enter for default: ").strip()

        if custom_path:
            if not Path(custom_path).exists():
                print(f"❌ Path not found: {custom_path}")
                return
            command = f'{self.python_cmd} -m scripts.extract_material_detail_prices_by_store_batch --material-detail-path "{custom_path}"'
        else:
            command = f'{self.python_cmd} -m scripts.extract_material_detail_prices_by_store_batch'

        # Ask for debug mode
        debug = input("Enable debug mode? (y/n): ").strip().lower()
        if debug in ['y', 'yes']:
            command += " --debug"

        self.run_command(command, "Batch Extract Material Prices (All Stores)")

    def extract_historical_data(self):
        """Extract all historical data from history_files/monthly_report_inputs"""
        print("🍲 HISTORICAL DATA EXTRACTION")
        print("=" * 40)
        print("📋 This will extract ALL historical data from:")
        print("   history_files/monthly_report_inputs/")
        print("   • Dishes and dish types from monthly_dish_sale/")
        print("   • Dish price history from monthly_dish_sale/")
        print("   • Materials from monthly_material_usage/")
        print("   • Material prices from material_detail/ store folders")
        print("   • Skips empty calculated_dish_material_usage & inventory_checking_result")
        print()
        print("⚠️  This is a COMPREHENSIVE extraction that will take significant time!")
        print("💡 Processes all months from 2024-05 to 2025-06")
        print("🔧 Uses critical material dtype={'物料': str} fix")
        print()

        # Get optional date range from user
        start_month = input(
            "Enter start month (YYYY-MM, or press Enter for all months): ").strip()
        if start_month and not re.match(r'^\d{4}-\d{2}$', start_month):
            print("❌ Invalid format. Please use YYYY-MM format.")
            input("Press Enter to continue...")
            return

        end_month = input(
            "Enter end month (YYYY-MM, or press Enter for all months): ").strip()
        if end_month and not re.match(r'^\d{4}-\d{2}$', end_month):
            print("❌ Invalid format. Please use YYYY-MM format.")
            input("Press Enter to continue...")
            return

        print()
        print("📊 Processing Options:")
        print("   • Start month:",
              start_month if start_month else "All months (2024-05)")
        print("   • End month:", end_month if end_month else "All months (2025-06)")
        print()

        # Final confirmation
        if input("🚀 Start historical data extraction? (y/n): ").lower() != 'y':
            print("Operation cancelled.")
            return

        # Build command
        command = f'{self.python_cmd} -m scripts.extract_historical_data_batch'

        # Add date range if specified
        if start_month:
            command += f' --start-month {start_month}'
        if end_month:
            command += f' --end-month {end_month}'

        # Ask if user wants debug output
        if input("Enable debug output? (y/n): ").lower() == 'y':
            command += ' --debug'

        # Ask if user wants to use test database
        if input("Use test database? (y/n): ").lower() == 'y':
            command += ' --test'

        print()
        print("🔄 Starting historical data extraction...")
        print("⏱️  This may take 30-60 minutes depending on data volume.")
        print()

        success = self.run_command(command, "Historical Data Extraction")
        if success:
            print("🎉 Historical data extraction completed successfully!")
            print("📊 Check the output summary for detailed statistics.")
        else:
            print("❌ Historical data extraction failed. Please check the logs.")

        input("Press Enter to continue...")

    def extract_inventory_calculation_data(self):
        """Extract inventory calculation data from all historical months"""
        print("📊 INVENTORY CALCULATION DATA EXTRACTION")
        print("=" * 50)
        print("📋 This will extract dish material usage data from:")
        print("   • Current month inventory files")
        print("   • ALL historical inventory files with 计算 sheets")
        print("   • Includes corrected portion size mapping")
        print()
        print("⚠️  This extracts thousands of records and may take several minutes!")
        print("🔧 Uses corrected column mapping to avoid unreasonable portion sizes")
        print()

        confirm = input(
            "Do you want to proceed with inventory calculation extraction? (y/N): ").lower().strip()
        if confirm != 'y':
            print("❌ Operation cancelled.")
            input("Press Enter to continue...")
            return

        print()
        print("🔄 Starting inventory calculation data extraction...")
        print("⏱️  This may take 5-10 minutes depending on data volume.")
        print()

        command = f'{self.python_cmd} scripts/extract_inventory_calculation_data.py'
        success = self.run_command(
            command, "Inventory Calculation Data Extraction")

        if success:
            print("🎉 Inventory calculation data extraction completed successfully!")
            print(
                "📊 Check the output file for thousands of records with corrected portion sizes.")
        else:
            print(
                "❌ Inventory calculation data extraction failed. Please check the logs.")

        input("Press Enter to continue...")

    def process_bank_transactions(self):
        """Process daily bank transactions from multiple banks using new update system"""
        print("🏦 BANK STATEMENT UPDATE PROCESSING")
        print("=" * 40)
        print("📋 This will process bank statements and update the workbook:")
        print()
        print("📂 Source files location:")
        print("   history_files/bank_daily_report/YYYY-MM/")
        print("   • BMO ReconciliationReport files (.xls)")
        print("   • RBC Business Bank Account files (.csv)")
        print("   • CIBC TransactionDetail files (.csv)")
        print("   • CA全部7家店明细.xlsx (existing workbook)")
        print()
        print("🎯 Features:")
        print("   • Extracts transactions from bank files")
        print("   • Updates CA全部7家店明细.xlsx workbook")
        print("   • Auto-classifies transactions (品名, 付款详情)")
        print("   • Marks items needing review as '待确认'")
        print("   • Formats dates per bank standards")
        print("   • Preserves existing data, only adds new records")
        print()

        # Get target date from user
        print("📅 Enter target date (processes entire month):")
        print("   Format: YYYY-MM-DD (e.g., 2025-08-15)")
        print("   Note: Day doesn't matter - processes entire month")
        print()

        date_input = input("Target date: ").strip()
        if not date_input:
            from datetime import datetime
            target_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Using today's date: {target_date}")
        else:
            try:
                from datetime import datetime
                datetime.strptime(date_input, '%Y-%m-%d')
                target_date = date_input
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")
                input("Press Enter to continue...")
                return

        print(f"\n📅 Processing transactions for: {target_date}")

        # Parse month/year for checking files
        from datetime import datetime
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        month_folder = target_dt.strftime('%Y-%m')
        
        # Check if bank files exist
        bank_folder = Path("history_files/bank_daily_report") / month_folder
        if not bank_folder.exists():
            print(f"❌ Bank folder not found: {bank_folder}")
            print("Please ensure bank files are placed in the correct directory.")
            input("Press Enter to continue...")
            return

        # Check for CA全部7家店明细.xlsx
        ca_file = bank_folder / "CA全部7家店明细.xlsx"
        if not ca_file.exists():
            print(f"❌ Workbook not found: CA全部7家店明细.xlsx")
            print(f"   Expected location: {ca_file}")
            print("This file is required for the update process.")
            input("Press Enter to continue...")
            return

        # List available bank files
        print(f"\n📁 Files in {bank_folder.name}:")
        bank_files = list(bank_folder.glob("*"))
        for file in bank_files[:10]:  # Show first 10 files
            print(f"   • {file.name}")
        if len(bank_files) > 10:
            print(f"   ... and {len(bank_files) - 10} more files")

        print()

        # Confirm processing
        confirm = input("🚀 Process bank statements? (y/n): ").lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return

        # Ask if user wants debug output
        debug_flag = ""
        if input("Enable debug output? (y/n): ").lower() == 'y':
            debug_flag = " --debug"

        # Build command
        command = f'{self.python_cmd} -m scripts.process_bank_updates --target-date {target_date}{debug_flag}'

        print()
        print("🔄 Starting bank statement update processing...")
        print("⏱️  This will:")
        print("   1. Read existing CA全部7家店明细.xlsx")
        print("   2. Extract new transactions from bank files")
        print("   3. Compare and identify new records")
        print("   4. Append new records with classifications")
        print()

        success = self.run_command(command, "Bank Statement Update Processing")
        if success:
            print()
            print("🎉 Bank statement update completed successfully!")
            print(f"📄 Check output/bank_statements/{month_folder}/ for Updated_CA全部7家店明细.xlsx")
            print()
            print("✨ New features in the updated file:")
            print("   • New transactions appended to each sheet")
            print("   • Transaction categories auto-filled")
            print("   • Items needing confirmation marked as '待确认'")
        else:
            print("❌ Bank statement processing failed. Please check the logs.")

        input("Press Enter to continue...")

    def show_status(self):
        """Show system status"""
        print("📊 SYSTEM STATUS")
        print("=" * 40)

        # Check environment variables
        env_vars = ['PG_HOST', 'PG_PASSWORD', 'TEST_PG_PASSWORD']
        print("🔑 Environment Variables:")
        for var in env_vars:
            status = "✅" if os.getenv(var) else "❌"
            print(f"  {status} {var}")

        print()

        # Check database connections
        print("🗄️  Database Connections:")
        try:
            from utils.database import verify_database_connection
            prod_status = "✅" if verify_database_connection(
                is_test=False) else "❌"
            test_status = "✅" if verify_database_connection(
                is_test=True) else "❌"
            print(f"  {prod_status} Production Database")
            print(f"  {test_status} Test Database")
        except Exception as e:
            print(f"  ❌ Database check failed: {e}")

        print()

        # Check Input folder
        print("📁 Input Folder Status:")
        input_status = "✅" if self.input_folder.exists() else "❌"
        print(f"  {input_status} Input folder exists: {self.input_folder}")

        if self.input_folder.exists():
            daily_path = self.input_folder / "daily_report"
            monthly_path = self.input_folder / "monthly_report"
            daily_status = "✅" if daily_path.exists() else "❌"
            monthly_status = "✅" if monthly_path.exists() else "❌"
            print(f"  {daily_status} Daily report folder")
            print(f"  {monthly_status} Monthly report folder")

        print()
        input("Press Enter to continue...")

    def show_help(self):
        """Show help documentation"""
        print("📖 HELP & DOCUMENTATION")
        print("=" * 35)
        print()
        print("🍲 HAIDILAO PAPERWORK AUTOMATION SYSTEM")
        print("=" * 50)
        print()
        print("This system automates the processing of Haidilao restaurant data")
        print("and generates comprehensive database reports.")
        print()
        print("📁 INPUT FOLDER STRUCTURE:")
        print("Input/")
        print("├── daily_report/")
        print("│   ├── daily_store_report/        # 海外门店经营日报数据")
        print("│   ├── time_segment_store_report/ # 海外分时段报表")
        print("│   └── store_6_convertion_file(temporary)/ # Store 6 conversion (DISABLED - no longer required)")
        print("└── monthly_report/")
        print("    ├── monthly_dish_sale/         # 海外菜品销售报表")
        print("    ├── material_detail/           # Material detail export")
        print("    ├── inventory_checking_result/ # 盘点结果 (subfolders: 1,2,7...)")
        print("    └── calculated_dish_material_usage/ # 计算 sheet with dish-material relationships")
        print()
        print("🚀 WORKFLOW:")
        print("1. Place your Excel files in the appropriate Input subfolders")
        print("2. Run Complete Daily/Monthly Automation for one-click processing")
        print("3. Or use Single Operations for granular control")
        print()
        print("📊 GENERATED REPORTS:")
        print("- 对比上月表 (Monthly Comparison)")
        print("- 同比数据 (Yearly Comparison)")
        print("- 分时段-上报 (Time Segment Report)")
        print("- 营业透视 (Business Insight)")
        print()
        print("🔧 REQUIREMENTS:")
        print("- Python 3.8+")
        print("- PostgreSQL database")
        print("- Required environment variables (PG_HOST, PG_PASSWORD, etc.)")
        print()
        input("Press Enter to continue...")

    def check_dependencies(self):
        """Check system dependencies"""
        print("🔍 CHECKING DEPENDENCIES")
        print("=" * 35)

        # Check Python version
        python_version = sys.version_info
        print(
            f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        if python_version >= (3, 8):
            print("✅ Python version OK")
        else:
            print("❌ Python 3.8+ required")

        print()

        # Check required packages
        required_packages = [
            'pandas', 'openpyxl', 'psycopg2', 'python-dotenv',
            'selenium', 'requests', 'beautifulsoup4'
        ]

        print("📦 Required packages:")
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} (not installed)")

        print()
        input("Press Enter to continue...")


def main():
    """Main entry point"""
    try:
        menu = AutomationMenu()
        menu.show_main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Automation menu interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your environment and try again.")


if __name__ == "__main__":
    main()
