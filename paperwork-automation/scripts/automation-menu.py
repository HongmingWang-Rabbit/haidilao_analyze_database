#!/usr/bin/env python3
"""
Interactive CLI Menu for Haidilao Paperwork Automation System
Provides a user-friendly interface to access all automation features.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AutomationMenu:
    """Interactive menu for automation system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        os.chdir(self.project_root)
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print menu header"""
        print("🍲" + "=" * 60 + "🍲")
        print("    HAIDILAO PAPERWORK AUTOMATION SYSTEM")
        print("         Interactive Control Menu")
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
        """Run a command and handle errors"""
        print(f"🚀 {description}")
        print(f"Running: {command}")
        print("-" * 50)
        
        try:
            if command.startswith('npm run'):
                result = subprocess.run(command.split(), capture_output=False, text=True)
            else:
                result = subprocess.run(command, shell=True, capture_output=False, text=True)
            
            print("-" * 50)
            if result.returncode == 0:
                print(f"✅ {description} completed successfully!")
            else:
                print(f"❌ {description} failed with exit code {result.returncode}")
            
            input("\nPress Enter to continue...")
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running command: {e}")
            input("\nPress Enter to continue...")
            return False
    
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
            prod_status = "✅" if verify_database_connection(is_test=False) else "❌"
            test_status = "✅" if verify_database_connection(is_test=True) else "❌"
            print(f"  {prod_status} Production Database")
            print(f"  {test_status} Test Database")
        except Exception as e:
            print(f"  ❌ Database check failed: {e}")
        
        print()
        
        # Check required files
        print("📁 Required Files:")
        required_files = [
            'haidilao-database-querys/reset-db.sql',
            'haidilao-database-querys/insert_const_data.sql',
            'haidilao-database-querys/insert_monthly_target.sql'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            status = "✅" if full_path.exists() else "❌"
            print(f"  {status} {file_path}")
        
        print()
        input("Press Enter to continue...")
    
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
    
    def process_excel_file(self, mode: str):
        """Process Excel file with specified mode"""
        excel_file = self.get_excel_file()
        if not excel_file:
            input("\nPress Enter to continue...")
            return
        
        commands = {
            'enhanced': f'ts-node scripts/extract-sql-enhanced.ts process "{excel_file}"',
            'all': f'python3 scripts/extract-all.py "{excel_file}"',
            'daily': f'python3 scripts/extract-all.py "{excel_file}" --daily-only',
            'time': f'python3 scripts/extract-time-segments.py "{excel_file}"',
            'db-all': f'python3 scripts/extract-all.py "{excel_file}" --direct-db',
            'db-daily': f'python3 scripts/extract-all.py "{excel_file}" --daily-only --direct-db',
            'db-time': f'python3 scripts/extract-time-segments.py "{excel_file}" --direct-db'
        }
        
        descriptions = {
            'enhanced': 'Enhanced TypeScript Processing',
            'all': 'Complete Python Processing (SQL Files)',
            'daily': 'Daily Reports Only (SQL Files)',
            'time': 'Time Segments Only (SQL Files)',
            'db-all': 'Complete Processing (Direct to Database)',
            'db-daily': 'Daily Reports Only (Direct to Database)',
            'db-time': 'Time Segments Only (Direct to Database)'
        }
        
        if mode in commands:
            self.run_command(commands[mode], descriptions[mode])
    
    def get_report_date(self) -> Optional[str]:
        """Get report date from user"""
        print("📅 SELECT REPORT DATE")
        print("=" * 30)
        print("Please enter the date for the report:")
        print("Format: YYYY-MM-DD (e.g., 2025-06-10)")
        print("Press Enter for default date (2025-06-10)")
        print()
        
        date_input = input("Report date: ").strip()
        
        if not date_input:
            return "2025-06-10"  # Default date
        
        # Basic date format validation
        try:
            from datetime import datetime
            datetime.strptime(date_input, '%Y-%m-%d')
            return date_input
        except ValueError:
            print(f"❌ Invalid date format: {date_input}")
            print("Please use YYYY-MM-DD format")
            return None
    
    def generate_report(self):
        """Generate comparison report"""
        report_date = self.get_report_date()
        if not report_date:
            input("\nPress Enter to continue...")
            return
        
        command = f'python3 scripts/generate_database_report.py --date {report_date}'
        description = f'Generating Comparison Report for {report_date}'
        self.run_command(command, description)
    
    def show_main_menu(self):
        """Show main menu and handle user input"""
        while True:
            self.clear_screen()
            self.print_header()
            
            # Processing Options
            processing_options = [
                ("1", "Enhanced TypeScript Processing", "enhanced"),
                ("2", "Complete Python Processing (SQL Files)", "all"),
                ("3", "Daily Reports Only (SQL Files)", "daily"),
                ("4", "Time Segments Only (SQL Files)", "time"),
            ]
            self.print_menu_section("📊 DATA PROCESSING", processing_options)
            
            # Database Options
            database_options = [
                ("5", "Complete Processing → Database", "db-all"),
                ("6", "Daily Reports → Database", "db-daily"),
                ("7", "Time Segments → Database", "db-time"),
            ]
            self.print_menu_section("🗄️  DATABASE OPERATIONS", database_options)
            
            # Report Generation
            report_options = [
                ("r", "Generate Comparison Report (对比上月表)", "report"),
            ]
            self.print_menu_section("📊 REPORT GENERATION", report_options)
            
            # Testing & Validation
            testing_options = [
                ("t", "Run All Tests (45+ tests)", "npm run test"),
                ("v", "Validate System", "npm run validate"),
                ("q", "Quick Test Suite", "npm run test:quick"),
            ]
            self.print_menu_section("🧪 TESTING & VALIDATION", testing_options)
            
            # Database Management
            db_management_options = [
                ("d", "Setup Test Database", "npm run db:setup"),
                ("c", "Check Database Connections", "npm run db:verify"),
                ("s", "Show System Status", "status"),
            ]
            self.print_menu_section("⚙️  DATABASE MANAGEMENT", db_management_options)
            
            # System Options
            system_options = [
                ("h", "Show Help & Documentation", "help"),
                ("x", "Exit Menu", "exit"),
            ]
            self.print_menu_section("🔧 SYSTEM", system_options)
            
            # Get user choice
            choice = input("Select an option: ").strip().lower()
            
            # Handle processing options (1-7)
            if choice in ['1', '2', '3', '4']:
                mode_map = {'1': 'enhanced', '2': 'all', '3': 'daily', '4': 'time'}
                self.process_excel_file(mode_map[choice])
            elif choice in ['5', '6', '7']:
                mode_map = {'5': 'db-all', '6': 'db-daily', '7': 'db-time'}
                self.process_excel_file(mode_map[choice])
            
            # Handle direct commands
            elif choice == 't':
                self.run_command("npm run test", "Running All Tests")
            elif choice == 'v':
                self.run_command("npm run validate", "System Validation")
            elif choice == 'q':
                self.run_command("npm run test:quick", "Quick Test Suite")
            elif choice == 'd':
                self.run_command("npm run db:setup", "Setting up Test Database")
            elif choice == 'c':
                self.run_command("npm run db:verify && npm run db:verify-test", "Checking Database Connections")
            elif choice == 's':
                self.clear_screen()
                self.print_header()
                self.show_status()
            elif choice == 'r':
                self.generate_report()
            elif choice == 'h':
                self.show_help()
            elif choice == 'x':
                print("\n👋 Thank you for using Haidilao Automation System!")
                print("🍲 Have a great day!")
                break
            else:
                print(f"\n❌ Invalid option: {choice}")
                input("Press Enter to continue...")
    
    def show_help(self):
        """Show help and documentation"""
        self.clear_screen()
        self.print_header()
        
        print("📖 HELP & DOCUMENTATION")
        print("=" * 50)
        print()
        
        print("🎯 SYSTEM OVERVIEW:")
        print("This automation system processes Haidilao restaurant data from Excel files")
        print("and can output SQL files or insert directly into the database.")
        print()
        
        print("📊 DATA PROCESSING MODES:")
        print("• Enhanced TypeScript: Advanced processing with validation")
        print("• Complete Python: Full processing of all data types")
        print("• Daily Reports: Process only daily summary data")
        print("• Time Segments: Process only time-based segment data")
        print()
        
        print("🗄️  DATABASE MODES:")
        print("• SQL Files: Generate .sql files for manual database import")
        print("• Direct Database: Insert data directly into PostgreSQL database")
        print()
        
        print("📊 REPORT GENERATION:")
        print("• Comparison Report: Generate Excel report (对比上月表) from database data")
        print("• Output saved to OUTPUT_DIR (./output by default)")
        print("• Filename format: report_YYYY_MM_DD.xlsx")
        print()
        
        print("📋 EXPECTED DATA FORMAT:")
        print("• Excel file with store data (加拿大一店 through 加拿大七店)")
        print("• Date format: YYYYMMDD (e.g., 20241201)")
        print("• Time segments: 早餐, 午餐, 下午茶, 晚餐")
        print()
        
        print("🔧 TROUBLESHOOTING:")
        print("• Use 'Show System Status' to check configuration")
        print("• Ensure .env file contains database credentials")
        print("• Run tests to verify system functionality")
        print()
        
        print("📞 SUPPORT:")
        print("• Check DATABASE_INTEGRATION.md for detailed documentation")
        print("• Run validation tests if you encounter issues")
        print("• Ensure Excel file follows expected format")
        print()
        
        input("Press Enter to return to main menu...")

def main():
    """Main entry point"""
    try:
        menu = AutomationMenu()
        menu.show_main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 