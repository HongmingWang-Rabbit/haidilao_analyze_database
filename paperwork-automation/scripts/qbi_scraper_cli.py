#!/usr/bin/env python3
"""
QBI Web Scraper CLI Script
Command-line interface for scraping data from QBI system
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from lib.qbi_scraper import QBIScraper, QBIScraperError

def get_qbi_credentials():
    """Get QBI credentials from environment or user input"""
    username = os.getenv('QBI_USERNAME')
    password = os.getenv('QBI_PASSWORD')
    
    if not username:
        username = input("QBI Username: ").strip()
    
    if not password:
        import getpass
        password = getpass.getpass("QBI Password: ")
    
    return username, password

def scrape_qbi_data(target_date: str, username: str = None, password: str = None, 
                   product_id: str = None, menu_id: str = None, headless: bool = True) -> str:
    """
    Scrape data from QBI system for specified date
    
    Args:
        target_date: Target date in YYYY-MM-DD format
        username: QBI username (optional, will prompt if not provided)
        password: QBI password (optional, will prompt if not provided)
        product_id: Product ID from URL (optional)
        menu_id: Menu ID from URL (optional)
        headless: Run browser in headless mode
        
    Returns:
        str: Path to downloaded Excel file
    """
    print("🚀 Starting QBI Data Scraping")
    print("=" * 50)
    
    # Get credentials if not provided
    if not username or not password:
        username, password = get_qbi_credentials()
    
    print(f"📅 Target Date: {target_date}")
    print(f"👤 Username: {username}")
    print(f"🔐 Password: {'*' * len(password)}")
    
    if product_id and menu_id:
        print(f"🎯 Product ID: {product_id}")
        print(f"📋 Menu ID: {menu_id}")
    else:
        print("📊 Using default Daily Reports configuration")
        product_id = "1fcba94f-c81d-4595-80cc-dac5462e0d24"
        menu_id = "89809ff6-a4fe-4fd7-853d-49315e51b2ec"
    
    print()
    print("⚠️  Note: Invalid credentials will cause the scraper to hang.")
    print("⚠️  Use Ctrl+C to interrupt if needed.")
    print()
    
    try:
        # Use shorter timeout to prevent hanging
        scraper = QBIScraper(headless=headless, timeout=60)
        downloaded_file = scraper.scrape_data(
            username=username,
            password=password,
            target_date=target_date,
            product_id=product_id,
            menu_id=menu_id
        )
        
        if downloaded_file:
            print(f"✅ Success! QBI data downloaded to: {downloaded_file}")
            return downloaded_file
        else:
            raise QBIScraperError("Failed to download QBI data file")
            
    except Exception as e:
        print(f"❌ QBI scraping failed: {e}")
        raise

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='QBI System Web Scraper for Haidilao Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape data for specific date
  python3 scripts/qbi_scraper_cli.py --target-date 2025-06-21
  
  # Scrape with specific QBI URL parameters
  python3 scripts/qbi_scraper_cli.py --target-date 2025-06-21 \
    --product-id "1fcba94f-c81d-4595-80cc-dac5462e0d24" \
    --menu-id "89809ff6-a4fe-4fd7-853d-49315e51b2ec"
  
  # Run with GUI (non-headless mode) for debugging
  python3 scripts/qbi_scraper_cli.py --target-date 2025-06-21 --no-headless

Environment Variables:
  QBI_USERNAME    - QBI system username
  QBI_PASSWORD    - QBI system password
        """
    )
    
    parser.add_argument(
        '--target-date', 
        required=True, 
        help='Target date for data scraping (YYYY-MM-DD format)'
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
        '--no-headless', 
        action='store_true',
        help='Run browser with GUI (for debugging)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for downloaded files (default: output)'
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.target_date, "%Y-%m-%d")
    except ValueError:
        print("❌ Error: Invalid date format. Please use YYYY-MM-DD")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Change to output directory
        original_cwd = os.getcwd()
        os.chdir(output_dir.parent)
        
        # Run scraper
        downloaded_file = scrape_qbi_data(
            target_date=args.target_date,
            username=args.username,
            password=args.password,
            product_id=args.product_id,
            menu_id=args.menu_id,
            headless=not args.no_headless
        )
        
        print()
        print("🎉 QBI Data Scraping Completed Successfully!")
        print(f"📁 Downloaded file: {downloaded_file}")
        
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        # Restore original working directory
        if 'original_cwd' in locals():
            os.chdir(original_cwd)

if __name__ == "__main__":
    main() 