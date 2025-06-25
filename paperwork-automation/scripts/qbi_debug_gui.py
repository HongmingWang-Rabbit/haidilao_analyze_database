#!/usr/bin/env python3
"""
QBI Debug GUI - Run with visible browser to debug login issues
"""

import sys
import os
import time
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from qbi_scraper import QBIScraper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_qbi_login():
    """Debug QBI login with visible browser"""
    
    # Get credentials
    username = os.getenv('QBI_USERNAME')
    password = os.getenv('QBI_PASSWORD')
    
    if not username or not password:
        print("❌ QBI credentials not found in environment variables")
        return False
    
    print("🚀 QBI Login Debug (GUI Mode)")
    print("=" * 40)
    print(f"👤 Username: {username}")
    print(f"🔐 Password: {'*' * len(password)}")
    print("🖥️  Running with visible browser")
    print()
    
    try:
        # Create scraper with GUI mode and longer timeout
        print("📦 Creating QBI scraper (GUI mode)...")
        scraper = QBIScraper(headless=False, timeout=60)
        
        print("🔧 Setting up WebDriver...")
        scraper.driver = scraper.setup_driver()
        from selenium.webdriver.support.ui import WebDriverWait
        scraper.wait = WebDriverWait(scraper.driver, scraper.timeout)
        
        print("🌐 Navigating to QBI dashboard...")
        success = scraper.navigate_to_dashboard(
            product_id="1fcba94f-c81d-4595-80cc-dac5462e0d24",
            menu_id="89809ff6-a4fe-4fd7-853d-49315e51b2ec"
        )
        
        if not success:
            print("❌ Failed to navigate to dashboard")
            return False
        
        print("✅ Dashboard navigation successful")
        print("🔐 Now attempting login...")
        print("👀 Watch the browser window to see what happens")
        
        # Try login with detailed feedback
        login_success = scraper.login(username, password)
        
        if login_success:
            print("✅ Login successful!")
            
            # Try to proceed with iframe switching
            print("🔄 Attempting iframe switch...")
            iframe_success = scraper.switch_to_dashboard_iframe()
            
            if iframe_success:
                print("✅ Iframe switch successful!")
                print("🎯 QBI scraper is working correctly!")
            else:
                print("⚠️  Iframe switch failed, but login worked")
                
        else:
            print("❌ Login failed")
            
        print("\n🔍 Browser will stay open for inspection")
        input("Press Enter to close browser...")
        
        return login_success
        
    except KeyboardInterrupt:
        print("\n🛑 Debug interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False
    finally:
        if 'scraper' in locals() and scraper.driver:
            scraper.driver.quit()
            print("🔄 Browser closed")

if __name__ == "__main__":
    debug_qbi_login() 