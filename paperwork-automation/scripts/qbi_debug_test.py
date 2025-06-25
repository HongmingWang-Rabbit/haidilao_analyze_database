#!/usr/bin/env python3
"""
QBI Debug Test - Run scraper with GUI and detailed logging
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from qbi_scraper import QBIScraper
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_qbi_scraper():
    """Run QBI scraper in debug mode with GUI"""
    
    # Configure detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('qbi_debug.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Get credentials
    username = os.getenv('QBI_USERNAME')
    password = os.getenv('QBI_PASSWORD')
    
    if not username or not password:
        print("❌ QBI credentials not found in environment variables")
        return
    
    print("🚀 Starting QBI Debug Test")
    print("=" * 50)
    print(f"👤 Username: {username}")
    print(f"🔐 Password: {'*' * len(password)}")
    print("🖥️  Running in GUI mode (not headless)")
    print("📝 Detailed logging enabled")
    print()
    
    # Create scraper with GUI mode and extended timeout
    scraper = QBIScraper(headless=False, timeout=60)
    
    try:
        # Setup WebDriver
        logger.info("Setting up WebDriver...")
        scraper.driver = scraper.setup_driver()
        from selenium.webdriver.support.ui import WebDriverWait
        scraper.wait = WebDriverWait(scraper.driver, scraper.timeout)
        
        # Navigate to dashboard
        logger.info("Navigating to dashboard...")
        if not scraper.navigate_to_dashboard(
            product_id="1fcba94f-c81d-4595-80cc-dac5462e0d24",
            menu_id="89809ff6-a4fe-4fd7-853d-49315e51b2ec"
        ):
            raise Exception("Failed to navigate to dashboard")
        
        # Handle login
        logger.info("Handling login...")
        if not scraper.login(username, password):
            raise Exception("Failed to login")
        
        # Switch to iframe
        logger.info("Switching to iframe...")
        if not scraper.switch_to_dashboard_iframe():
            logger.warning("No iframe found")
        
        # Wait for elements
        logger.info("Waiting for dashboard elements...")
        if not scraper.wait_for_dashboard_elements():
            raise Exception("Dashboard elements not found")
        
        # Set date range (optional)
        logger.info("Setting date range...")
        scraper.set_date_range("2025-01-15")
        
        # Trigger search
        logger.info("Triggering search...")
        if not scraper.trigger_search():
            raise Exception("Failed to trigger search")
        
        # Now let's manually debug the export process
        logger.info("🔍 Starting export debugging...")
        
        # Wait for floating menu
        time.sleep(5)
        
        # Look for export button
        export_selectors = [
            "//div[@class='preview-mini-menu-list-item-text' and text()='导出']",
            "//li[contains(@class, 'preview-mini-menu-list-item')]//div[text()='导出']"
        ]
        
        export_button = None
        for selector in export_selectors:
            try:
                export_button = scraper.driver.find_element("xpath", selector)
                logger.info(f"✅ Found export button: {selector}")
                break
            except:
                continue
        
        if not export_button:
            logger.error("❌ Export button not found")
            return
        
        # Click export button
        logger.info("🖱️  Clicking export button...")
        parent = export_button.find_element("xpath", "..")
        parent.click()
        
        # Wait and look for confirmation
        time.sleep(3)
        
        # Look for confirmation buttons
        confirmation_selectors = [
            ".ant-btn-primary",
            "//button[contains(text(), '确认')]",
            "//button[contains(text(), '下载')]"
        ]
        
        for selector in confirmation_selectors:
            try:
                if selector.startswith("//"):
                    buttons = scraper.driver.find_elements("xpath", selector)
                else:
                    buttons = scraper.driver.find_elements("css selector", selector)
                
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button_text = button.get_attribute('textContent') or button.text
                        logger.info(f"🔘 Found confirmation button: {selector} - Text: '{button_text}'")
                        
                        # Click it
                        button.click()
                        logger.info(f"✅ Clicked confirmation button")
                        time.sleep(2)
                        break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
        
        # Now wait and monitor for downloads
        logger.info("⏳ Monitoring for downloads...")
        print("\n🔍 Manual monitoring - watch the browser and Downloads folder")
        print("Press Ctrl+C when you see download complete or want to stop")
        
        try:
            # Keep browser open for manual observation
            while True:
                time.sleep(5)
                
                # Check Downloads folder
                downloads_dir = Path.home() / "Downloads"
                recent_files = []
                
                for pattern in ["*.xlsx", "*.xls", "*.csv"]:
                    files = list(downloads_dir.glob(pattern))
                    for file in files:
                        if file.stat().st_mtime > time.time() - 300:  # Last 5 minutes
                            recent_files.append(file)
                
                if recent_files:
                    logger.info(f"📥 Recent downloads found: {[f.name for f in recent_files]}")
                    break
                    
        except KeyboardInterrupt:
            logger.info("🛑 Manual monitoring stopped")
        
    except Exception as e:
        logger.error(f"❌ Debug test failed: {e}")
        
    finally:
        if scraper.driver:
            input("Press Enter to close browser...")
            scraper.driver.quit()


if __name__ == "__main__":
    debug_qbi_scraper() 