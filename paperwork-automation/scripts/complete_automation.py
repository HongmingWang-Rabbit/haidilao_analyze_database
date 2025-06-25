#!/usr/bin/env python3
"""
Complete Haidilao Automation Workflow
Handles entire process: QBI scraping → data processing → database insertion → report generation
"""

import sys
import os
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from scripts.qbi_scraper_cli import scrape_qbi_data
from lib.qbi_scraper import QBIScraperError

class AutomationWorkflowError(Exception):
    """Custom exception for automation workflow errors"""
    pass

class CompleteAutomationWorkflow:
    """
    Complete automation workflow manager
    
    Orchestrates the entire process from QBI data scraping to final report generation
    """
    
    def __init__(self, target_date: str, working_dir: str = None):
        """
        Initialize automation workflow
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            working_dir: Working directory (default: current directory)
        """
        self.target_date = target_date
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.output_dir = self.working_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Workflow tracking
        self.scraped_file = None
        self.processed_data = None
        self.database_inserted = False
        self.report_generated = None
        
        print("🍲 HAIDILAO COMPLETE AUTOMATION WORKFLOW")
        print("=" * 60)
        print(f"📅 Target Date: {target_date}")
        print(f"📁 Working Directory: {self.working_dir}")
        print(f"📂 Output Directory: {self.output_dir}")
        print()
    
    def step_1_scrape_qbi_data(self, username: str = None, password: str = None,
                              product_id: str = None, menu_id: str = None, 
                              headless: bool = True) -> str:
        """
        Step 1: Scrape data from QBI system
        
        Args:
            username: QBI username
            password: QBI password  
            product_id: Product ID from QBI URL
            menu_id: Menu ID from QBI URL
            headless: Run browser in headless mode
            
        Returns:
            str: Path to scraped Excel file
        """
        print("🚀 STEP 1: QBI DATA SCRAPING")
        print("-" * 40)
        
        try:
            # Change to working directory for scraping
            original_cwd = os.getcwd()
            os.chdir(self.working_dir)
            
            self.scraped_file = scrape_qbi_data(
                target_date=self.target_date,
                username=username,
                password=password,
                product_id=product_id,
                menu_id=menu_id,
                headless=headless
            )
            
            print(f"✅ Step 1 Complete: QBI data scraped to {self.scraped_file}")
            return self.scraped_file
            
        except Exception as e:
            raise AutomationWorkflowError(f"Step 1 (QBI Scraping) failed: {e}")
        finally:
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
    
    def step_2_process_data(self, mode: str = "enhanced") -> bool:
        """
        Step 2: Process scraped data using extract-all.py
        
        Args:
            mode: Processing mode (enhanced, all, daily, time)
            
        Returns:
            bool: True if processing successful
        """
        print("\n🔄 STEP 2: DATA PROCESSING")
        print("-" * 40)
        
        if not self.scraped_file:
            raise AutomationWorkflowError("Step 2 failed: No scraped file available")
        
        try:
            # Determine command based on mode
            mode_commands = {
                'enhanced': f'python3 scripts/extract-all.py "{self.scraped_file}" --enhanced --direct-db',
                'all': f'python3 scripts/extract-all.py "{self.scraped_file}" --direct-db',
                'daily': f'python3 scripts/extract-all.py "{self.scraped_file}" --daily-only --direct-db',
                'time': f'python3 scripts/extract-time-segments.py "{self.scraped_file}" --direct-db'
            }
            
            if mode not in mode_commands:
                raise AutomationWorkflowError(f"Invalid processing mode: {mode}")
            
            command = mode_commands[mode]
            print(f"🖥️  Running: {command}")
            
            # Change to project root for processing
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            # Run processing command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Step 2 Complete: Data processing successful")
                self.database_inserted = True
                return True
            else:
                print(f"❌ Processing command failed with exit code {result.returncode}")
                print(f"Error output: {result.stderr}")
                raise AutomationWorkflowError("Data processing failed")
                
        except Exception as e:
            raise AutomationWorkflowError(f"Step 2 (Data Processing) failed: {e}")
        finally:
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
    
    def step_3_generate_report(self) -> str:
        """
        Step 3: Generate database report
        
        Returns:
            str: Path to generated report
        """
        print("\n📊 STEP 3: REPORT GENERATION")
        print("-" * 40)
        
        if not self.database_inserted:
            raise AutomationWorkflowError("Step 3 failed: Database not populated")
        
        try:
            # Change to project root for report generation
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            # Run report generation
            command = f'python3 scripts/generate_database_report.py --target-date {self.target_date}'
            print(f"🖥️  Running: {command}")
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Find generated report file
                report_files = list(self.output_dir.glob(f"database_report_*.xlsx"))
                if report_files:
                    # Get the most recent report file
                    self.report_generated = str(max(report_files, key=os.path.getctime))
                    print(f"✅ Step 3 Complete: Report generated at {self.report_generated}")
                    return self.report_generated
                else:
                    raise AutomationWorkflowError("Report file not found after generation")
            else:
                print(f"❌ Report generation failed with exit code {result.returncode}")
                print(f"Error output: {result.stderr}")
                raise AutomationWorkflowError("Report generation failed")
                
        except Exception as e:
            raise AutomationWorkflowError(f"Step 3 (Report Generation) failed: {e}")
        finally:
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
    
    def step_4_cleanup_and_organize(self) -> None:
        """
        Step 4: Cleanup and organize output files
        """
        print("\n🧹 STEP 4: CLEANUP AND ORGANIZATION")
        print("-" * 40)
        
        try:
            # Create organized output structure
            date_dir = self.output_dir / f"automation_{self.target_date.replace('-', '_')}"
            date_dir.mkdir(exist_ok=True)
            
            # Move files to organized structure
            if self.scraped_file and Path(self.scraped_file).exists():
                scraped_dest = date_dir / f"01_scraped_qbi_data_{Path(self.scraped_file).name}"
                shutil.copy2(self.scraped_file, scraped_dest)
                print(f"📁 Organized scraped data: {scraped_dest}")
            
            if self.report_generated and Path(self.report_generated).exists():
                report_dest = date_dir / f"02_final_report_{Path(self.report_generated).name}"
                shutil.copy2(self.report_generated, report_dest)
                print(f"📁 Organized final report: {report_dest}")
            
            # Create workflow summary
            summary_file = date_dir / "workflow_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Haidilao Automation Workflow Summary\n")
                f.write(f"=====================================\n\n")
                f.write(f"Target Date: {self.target_date}\n")
                f.write(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Files Generated:\n")
                f.write(f"- Scraped QBI Data: {self.scraped_file}\n")
                f.write(f"- Final Report: {self.report_generated}\n\n")
                f.write(f"Database Status: {'✅ Updated' if self.database_inserted else '❌ Not Updated'}\n")
                f.write(f"Workflow Status: ✅ Complete\n")
            
            print(f"📄 Workflow summary: {summary_file}")
            print(f"✅ Step 4 Complete: Files organized in {date_dir}")
            
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")
            # Non-critical error, don't raise exception
    
    def run_complete_workflow(self, username: str = None, password: str = None,
                             product_id: str = None, menu_id: str = None,
                             processing_mode: str = "enhanced", headless: bool = True) -> dict:
        """
        Run the complete automation workflow
        
        Args:
            username: QBI username
            password: QBI password
            product_id: Product ID from QBI URL
            menu_id: Menu ID from QBI URL  
            processing_mode: Data processing mode
            headless: Run browser in headless mode
            
        Returns:
            dict: Workflow results summary
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape QBI data
            self.step_1_scrape_qbi_data(
                username=username,
                password=password,
                product_id=product_id,
                menu_id=menu_id,
                headless=headless
            )
            
            # Step 2: Process data
            self.step_2_process_data(mode=processing_mode)
            
            # Step 3: Generate report
            self.step_3_generate_report()
            
            # Step 4: Cleanup and organize
            self.step_4_cleanup_and_organize()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            results = {
                'success': True,
                'target_date': self.target_date,
                'scraped_file': self.scraped_file,
                'report_file': self.report_generated,
                'database_updated': self.database_inserted,
                'duration': str(duration),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            print("\n🎉 COMPLETE AUTOMATION WORKFLOW FINISHED!")
            print("=" * 60)
            print(f"⏱️  Total Duration: {duration}")
            print(f"📁 Scraped File: {self.scraped_file}")
            print(f"📊 Final Report: {self.report_generated}")
            print(f"🗄️  Database: {'✅ Updated' if self.database_inserted else '❌ Not Updated'}")
            print("🍲 Have a great day!")
            
            return results
            
        except Exception as e:
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n❌ AUTOMATION WORKFLOW FAILED!")
            print("=" * 60)
            print(f"⏱️  Duration before failure: {duration}")
            print(f"🚨 Error: {e}")
            
            return {
                'success': False,
                'target_date': self.target_date,
                'error': str(e),
                'duration': str(duration),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Complete Haidilao Automation Workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script runs the complete automation workflow:
1. Scrape data from QBI system
2. Process and insert data into database  
3. Generate comprehensive Excel report
4. Cleanup and organize output files

Examples:
  # Run complete workflow for specific date
  python3 scripts/complete_automation.py --target-date 2025-06-21
  
  # Run with specific QBI parameters
  python3 scripts/complete_automation.py --target-date 2025-06-21 \
    --product-id "1fcba94f-c81d-4595-80cc-dac5462e0d24" \
    --menu-id "89809ff6-a4fe-4fd7-853d-49315e51b2ec"
  
  # Run with enhanced processing mode
  python3 scripts/complete_automation.py --target-date 2025-06-21 --mode enhanced

Environment Variables:
  QBI_USERNAME    - QBI system username  
  QBI_PASSWORD    - QBI system password
        """
    )
    
    parser.add_argument(
        '--target-date',
        required=True,
        help='Target date for automation workflow (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--username',
        help='QBI username (will prompt if not provided)'
    )
    
    parser.add_argument(
        '--password', 
        help='QBI password (will prompt if not provided)'
    )
    
    parser.add_argument(
        '--product-id',
        help='Product ID from QBI URL (optional)'
    )
    
    parser.add_argument(
        '--menu-id',
        help='Menu ID from QBI URL (optional)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['enhanced', 'all', 'daily', 'time'],
        default='enhanced',
        help='Data processing mode (default: enhanced)'
    )
    
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser with GUI (for debugging)'
    )
    
    parser.add_argument(
        '--working-dir',
        help='Working directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.target_date, "%Y-%m-%d")
    except ValueError:
        print("❌ Error: Invalid date format. Please use YYYY-MM-DD")
        sys.exit(1)
    
    try:
        # Initialize workflow
        workflow = CompleteAutomationWorkflow(
            target_date=args.target_date,
            working_dir=args.working_dir
        )
        
        # Run complete workflow
        results = workflow.run_complete_workflow(
            username=args.username,
            password=args.password,
            product_id=args.product_id,
            menu_id=args.menu_id,
            processing_mode=args.mode,
            headless=not args.no_headless
        )
        
        # Exit with appropriate code
        sys.exit(0 if results['success'] else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Workflow cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 