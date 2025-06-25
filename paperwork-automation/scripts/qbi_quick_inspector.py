#!/usr/bin/env python3
"""
Quick QBI Inspector - Simplified version for specific element detection
"""

import time
import sys
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import getpass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_credentials():
    """Get QBI credentials"""
    username = os.getenv('QBI_USERNAME')
    password = os.getenv('QBI_PASSWORD')
    
    if not username:
        username = input("QBI Username: ").strip()
    
    if not password:
        password = getpass.getpass("QBI Password: ")
    
    return username, password

def setup_driver(headless=False):
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Handle SSL issues
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"❌ Failed to setup Chrome driver: {e}")
        return None

def find_ant_design_elements(driver):
    """Find specific Ant Design elements based on user's findings"""
    print("\n🔍 Looking for Ant Design elements...")
    
    elements_found = {}
    
    # Look for the search button
    search_selectors = [
        "button.ant-btn.ant-btn-primary.query-area-button.query-button",
        "button[class*='query-button']",
        "button[class*='ant-btn-primary']",
        ".query-button",
        "button:contains('查询')",
        "//button[contains(@class, 'query-button')]",
        "//button[contains(@class, 'ant-btn-primary')]//span[contains(text(), '查')]"
    ]
    
    print("🔍 Searching for 查询 button...")
    for selector in search_selectors:
        try:
            if selector.startswith("//"):
                # XPath selector
                elements = driver.find_elements(By.XPATH, selector)
            elif ":contains(" in selector:
                # Convert CSS :contains to XPath
                text = selector.split(":contains(")[1].split(")")[0].strip("'\"")
                elements = driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
            else:
                # CSS selector
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            if elements:
                for i, elem in enumerate(elements):
                    if elem.is_displayed():
                        print(f"✅ Found search button [{i+1}]: {selector}")
                        print(f"   Text: '{elem.text}'")
                        print(f"   Class: '{elem.get_attribute('class')}'")
                        print(f"   ID: '{elem.get_attribute('id')}'")
                        elements_found['search_button'] = elem
                        break
        except Exception as e:
            print(f"⚠️  Error with selector {selector}: {e}")
    
    # Look for date inputs (common patterns in Ant Design)
    date_selectors = [
        "input.ant-picker-input",
        ".ant-picker input",
        "input[placeholder*='日期']",
        "input[placeholder*='时间']",
        "input[placeholder*='date']",
        ".ant-date-picker input",
        "input[class*='picker']"
    ]
    
    print("\n📅 Searching for date inputs...")
    date_inputs = []
    for selector in date_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if elem.is_displayed():
                    date_inputs.append(elem)
                    print(f"✅ Found date input: {selector}")
                    print(f"   Placeholder: '{elem.get_attribute('placeholder')}'")
                    print(f"   Class: '{elem.get_attribute('class')}'")
                    print(f"   Name: '{elem.get_attribute('name')}'")
        except Exception as e:
            print(f"⚠️  Error with selector {selector}: {e}")
    
    elements_found['date_inputs'] = date_inputs
    
    # Look for export/download buttons
    export_selectors = [
        "button[class*='export']",
        "button[class*='download']",
        "button:contains('导出')",
        "button:contains('下载')",
        ".ant-btn:contains('导出')",
        "//button[contains(@class, 'ant-btn')]//span[contains(text(), '导出')]",
        "//button[contains(@class, 'ant-btn')]//span[contains(text(), '下载')]"
    ]
    
    print("\n📊 Searching for export/download buttons...")
    for selector in export_selectors:
        try:
            if selector.startswith("//"):
                elements = driver.find_elements(By.XPATH, selector)
            elif ":contains(" in selector:
                text = selector.split(":contains(")[1].split(")")[0].strip("'\"")
                elements = driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            if elements:
                for i, elem in enumerate(elements):
                    if elem.is_displayed():
                        print(f"✅ Found export button [{i+1}]: {selector}")
                        print(f"   Text: '{elem.text}'")
                        print(f"   Class: '{elem.get_attribute('class')}'")
                        elements_found['export_button'] = elem
                        break
        except Exception as e:
            print(f"⚠️  Error with selector {selector}: {e}")
    
    return elements_found

def wait_for_button_and_stabilize(driver, timeout=30):
    """Wait for the search button to appear and then wait for page to stabilize"""
    print("⏳ Waiting for 查询 button to appear...")
    
    # Wait for the specific button to appear
    button_selectors = [
        "button.ant-btn.ant-btn-primary.query-area-button.query-button",
        "//button[contains(@class, 'query-button')]",
        "//button[contains(@class, 'ant-btn-primary')]//span[contains(text(), '查')]"
    ]
    
    button_found = False
    for selector in button_selectors:
        try:
            if selector.startswith("//"):
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            else:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            
            if element.is_displayed():
                print(f"✅ Found 查询 button: {selector}")
                button_found = True
                break
        except TimeoutException:
            continue
    
    if button_found:
        print("⏳ Button found! Waiting additional 20 seconds for page to stabilize...")
        time.sleep(20)  # Wait for page to fully load after button appears
        print("✅ Page should now be fully loaded")
    else:
        print("⚠️  查询 button not found, continuing anyway...")
    
    return button_found

def quick_inspect(target_url):
    """Quick inspection of QBI site"""
    print("🚀 Quick QBI Site Inspection")
    print("=" * 50)
    
    driver = setup_driver(headless=False)  # Use GUI mode for inspection
    if not driver:
        return
    
    try:
        # Get credentials
        username, password = get_credentials()
        
        # Navigate to target URL
        print(f"🌐 Navigating to: {target_url}")
        driver.get(target_url)
        time.sleep(3)
        
        # Take initial screenshot
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        driver.save_screenshot(str(output_dir / "qbi_quick_initial.png"))
        print("📸 Initial screenshot saved")
        
        # Handle login if needed
        try:
            username_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            print("🔑 Logging in...")
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
            
            driver.save_screenshot(str(output_dir / "qbi_quick_after_login.png"))
            print("📸 After login screenshot saved")
        except:
            print("⚠️  Login not required or already authenticated")
        
        # Wait specifically for the button to appear and page to stabilize
        wait_for_button_and_stabilize(driver)
        
        # Take screenshot after proper loading
        driver.save_screenshot(str(output_dir / "qbi_quick_loaded.png"))
        print("📸 Loaded page screenshot saved")
        
        # Find elements
        elements = find_ant_design_elements(driver)
        
        # Test clicking the search button if found
        if 'search_button' in elements:
            print("\n🧪 Testing search button click...")
            try:
                search_btn = elements['search_button']
                print(f"Button text before click: '{search_btn.text}'")
                search_btn.click()
                time.sleep(5)  # Wait after clicking
                driver.save_screenshot(str(output_dir / "qbi_quick_after_search.png"))
                print("📸 After search click screenshot saved")
                print("✅ Search button clicked successfully!")
            except Exception as e:
                print(f"❌ Search button click failed: {e}")
        
        # Look for any newly appeared elements after search
        print("\n🔍 Looking for elements that appeared after search...")
        time.sleep(5)
        
        # Look for export buttons again
        export_elements = find_ant_design_elements(driver)
        
        # Save final screenshot
        driver.save_screenshot(str(output_dir / "qbi_quick_final.png"))
        print("📸 Final screenshot saved")
        
        # Save page source
        with open(output_dir / "qbi_quick_page_source.html", 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("📄 Page source saved")
        
        print("\n✅ Quick inspection completed!")
        print("📁 Check the 'output' folder for screenshots and page source")
        print("\n📋 Summary of elements found:")
        for key, value in elements.items():
            if value:
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} elements found")
                else:
                    print(f"  {key}: Found")
            else:
                print(f"  {key}: Not found")
        
        # Keep browser open for manual inspection
        input("\n⏸️  Press Enter to close browser...")
        
    except Exception as e:
        print(f"❌ Inspection failed: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick QBI Site Inspector')
    parser.add_argument('--url', required=True, help='Target QBI URL to inspect')
    
    args = parser.parse_args()
    quick_inspect(args.url) 