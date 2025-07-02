#!/usr/bin/env python3
"""
Interactive CLI Menu for Haidilao Paperwork Automation System
Streamlined workflow-focused interface for complete automation.
"""

import os
import sys
import subprocess
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

            # Special handling for inventory_checking_result (has store subfolders)
            if "inventory_checking_result" in str(path):
                # Check for store subfolders (1, 2, 7, etc.)
                store_folders = [d for d in path.iterdir(
                ) if d.is_dir() and d.name.isdigit()]
                if not store_folders:
                    missing_files.append(f"{path} (no store subfolders found)")
                    continue

                # Check if at least one store folder has files
                has_files = False
                for store_folder in store_folders:
                    store_files = list(store_folder.glob("*.xls*"))
                    if store_files:
                        has_files = True
                        break

                if not has_files:
                    missing_files.append(
                        f"{path} (no Excel files found in store subfolders)")
            else:
                # Check if folder has files
                files = list(path.glob("*.xls*"))
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
        daily_files = list(daily_store_path.glob("*.xls*"))
        # Filter out temporary Excel files (starting with ~$)
        daily_files = [f for f in daily_files if not f.name.startswith("~$")]
        if daily_files:
            daily_file = daily_files[0]
            command = f'{self.python_cmd} -m scripts.extract-all "{daily_file}" --daily-only --direct-db'
            if not self.run_command(command, "Daily Store Report Extraction"):
                return

        # Step 2: Extract time segment reports (separate file)
        time_segment_path = self.input_folder / \
            "daily_report" / "time_segment_store_report"
        time_files = list(time_segment_path.glob("*.xls*"))
        # Filter out temporary Excel files (starting with ~$)
        time_files = [f for f in time_files if not f.name.startswith("~$")]
        if time_files:
            time_file = time_files[0]
            command = f'{self.python_cmd} -m scripts.extract-all "{time_file}" --time-only --direct-db'
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
        dish_files = list(monthly_dish_path.glob("*.xls*"))
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
            dish_material_files = list(dish_material_path.glob("*.xls*"))
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
        print("📋 Generate material variance analysis report")
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

        # First, run database migration to ensure loss_rate column exists
        print("🔧 Running database migration for loss_rate column...")
        migration_command = f'{self.python_cmd} -m scripts.migrate_add_loss_rate'
        migration_success = self.run_command(
            migration_command, "Database Migration for Loss Rate")

        if not migration_success:
            print("❌ Database migration failed. Continuing with automation anyway...")
            print("💡 Note: Loss rate calculations may use default values")

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
                ("8", "Dishes Master Data (File → Database)", "dishes"),
                ("9", "Dish Price History (File → Database)", "price_history"),
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
                self.extract_dishes()
            elif choice == '9':
                self.extract_with_file_selection(
                    "price_history", "Dish Price History")
            else:
                print("❌ Invalid choice. Please try again.")
                input("Press Enter to continue...")

    def extract_with_file_selection(self, extraction_type: str, description: str):
        """Extract data with file selection"""
        excel_file = self.get_excel_file()
        if not excel_file:
            return

        commands = {
            'daily_store': f'{self.python_cmd} -m scripts.extract-all "{excel_file}" --daily-only --direct-db',
            'time_segment': f'{self.python_cmd} -m scripts.extract-all "{excel_file}" --time-only --direct-db',
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
                # ("1", "Store 6 Data Conversion (New Logic)", "store6_conversion"),  # Disabled - no longer needed
                ("2", "Legacy Format Conversion", "legacy_conversion"),
                ("b", "← Back to Main Menu", "back")
            ]

            self.print_menu_section("Select conversion type", options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == 'b':
                break
            # elif choice == '1':
            #     self.convert_store6_data()  # Disabled - no longer needed
            elif choice == '2':
                self.convert_legacy_format()
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
                ("3", "Migrate: Add Loss Rate Column", "migrate_loss_rate"),
                ("4", "Insert Constant Data", "insert_const"),
                ("5", "Insert Monthly Targets", "insert_targets"),
                ("6", "Verify Database Structure", "verify_structure"),
                ("7", "Show Database Status", "show_status"),
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
                self.run_loss_rate_migration()
            elif choice == '4':
                self.insert_constant_data()
            elif choice == '5':
                self.insert_monthly_targets()
            elif choice == '6':
                self.verify_database_structure()
            elif choice == '7':
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
                ("1", "🌅 Complete Daily Automation", "daily_automation"),
                ("2", "📅 Complete Monthly Automation", "monthly_automation"),
            ]
            self.print_menu_section(
                "🚀 COMPLETE AUTOMATION WORKFLOWS", workflow_options)

            # Single operation options
            single_options = [
                ("3", "📤 Single Extraction", "single_extraction"),
                ("4", "📊 Single Report Generation", "single_generate"),
                ("5", "🔄 Single Conversion", "single_conversion"),
                ("6", "🕷️  Single Web Scraping", "single_scraping"),
            ]
            self.print_menu_section("🔧 SINGLE OPERATIONS", single_options)

            # System options
            system_options = [
                ("7", "🧪 Testing", "testing"),
                ("8", "🗄️  Database Management", "database"),
                ("9", "⚙️  System", "system"),
                ("q", "🚪 Quit", "quit")
            ]
            self.print_menu_section("🛠️  SYSTEM & MAINTENANCE", system_options)

            choice = input("Enter your choice: ").lower().strip()

            if choice == '1':
                self.run_complete_daily_automation()
            elif choice == '2':
                self.run_complete_monthly_automation()
            elif choice == '3':
                self.show_single_extraction_menu()
            elif choice == '4':
                self.show_single_generate_menu()
            elif choice == '5':
                self.show_single_conversion_menu()
            elif choice == '6':
                self.show_single_web_scraping_menu()
            elif choice == '7':
                self.show_testing_menu()
            elif choice == '8':
                self.show_database_management_menu()
            elif choice == '9':
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
        print("   3. 分时段-上报 (Time Segment Report)")
        print("   4. 营业透视 (Business Insight)")
        print("   5. 门店日-加拿大 (Daily Store Tracking)")

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

    def run_loss_rate_migration(self):
        """Run database migration to add loss_rate column"""
        print("🔧 DATABASE MIGRATION: Add Loss Rate Column")
        print("=" * 50)
        print("This will add the loss_rate column to the dish_material table.")
        print("This is required for proper material variance calculations.")
        print()

        confirm = input("Run migration? (y/N): ").lower()
        if confirm != 'y':
            return

        command = f'{self.python_cmd} -m scripts.migrate_add_loss_rate'
        self.run_command(command, "Add Loss Rate Column Migration")

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

    def extract_dishes(self):
        """Extract dishes from Excel file"""
        excel_file = self.get_excel_file()
        if excel_file:
            command = f'{self.python_cmd} -m scripts.extract-dishes "{excel_file}" --direct-db'
            self.run_command(command, "Extract Dishes to Database")

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
