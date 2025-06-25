#!/usr/bin/env python3
"""
QBI Iframe Inspector - Inspect elements inside the dashboard iframe after login
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

def inspect_iframe_elements():
    """Inspect elements inside the QBI dashboard iframe"""
    driver = None
    try:
        logger.info("🚀 Starting QBI iframe inspection...")
        
        # Setup driver
        driver = setup_driver()
        wait = WebDriverWait(driver, 60)
        
        # Get credentials
        username = os.getenv('QBI_USERNAME')
        password = os.getenv('QBI_PASSWORD')
        
        if not username or not password:
            logger.error("❌ QBI credentials not found in environment")
            return
        
        # Navigate to dashboard
        url = "https://qbi.superhi-tech.com/product/view.htm?module=dashboard&productId=1fcba94f-c81d-4595-80cc-dac5462e0d24&menuId=89809ff6-a4fe-4fd7-853d-49315e51b2ec"
        logger.info(f"🌐 Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Login
        logger.info("🔐 Logging in...")
        username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        time.sleep(5)
        
        # Wait for iframe and switch
        logger.info("📱 Finding and switching to iframe...")
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id*='portal']")))
        driver.switch_to.frame(iframe)
        time.sleep(15)  # Wait for iframe content to load
        
        # Wait for query button to appear
        logger.info("⏳ Waiting for query button...")
        query_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.query-button")))
        logger.info("✅ Query button found!")
        
        # Inspect all input elements
        logger.info("🔍 Inspecting all input elements...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"📝 Found {len(inputs)} input elements:")
        
        for i, inp in enumerate(inputs):
            try:
                inp_type = inp.get_attribute('type')
                inp_class = inp.get_attribute('class')
                inp_placeholder = inp.get_attribute('placeholder')
                inp_name = inp.get_attribute('name')
                inp_id = inp.get_attribute('id')
                logger.info(f"Input {i}: type='{inp_type}', class='{inp_class}', placeholder='{inp_placeholder}', name='{inp_name}', id='{inp_id}'")
            except:
                pass
        
        # Look specifically for date-related inputs
        logger.info("\n🗓️ Looking for date-related inputs...")
        date_selectors = [
            "input[class*='picker']",
            "input[class*='date']",
            "input[placeholder*='日期']",
            "input[placeholder*='date']",
            "input[type='text'][class*='ant-picker']"
        ]
        
        for selector in date_selectors:
            try:
                date_inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                if date_inputs:
                    logger.info(f"📅 Found {len(date_inputs)} elements with selector: {selector}")
                    for j, inp in enumerate(date_inputs):
                        inp_class = inp.get_attribute('class')
                        inp_placeholder = inp.get_attribute('placeholder')
                        logger.info(f"  Date input {j}: class='{inp_class}', placeholder='{inp_placeholder}'")
            except:
                pass
        
        # Inspect all button elements
        logger.info("\n🔘 Inspecting all button elements...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"🔘 Found {len(buttons)} button elements:")
        
        for i, btn in enumerate(buttons):
            try:
                btn_text = btn.get_attribute('textContent') or btn.text
                btn_class = btn.get_attribute('class')
                btn_title = btn.get_attribute('title')
                logger.info(f"Button {i}: text='{btn_text[:30]}', class='{btn_class}', title='{btn_title}'")
            except:
                pass
        
        # Look specifically for export-related buttons
        logger.info("\n📤 Looking for export-related elements...")
        export_selectors = [
            "//button[contains(text(), '导出')]",
            "//button[contains(text(), '下载')]",
            "//button[contains(text(), 'export')]",
            "//button[contains(text(), 'download')]",
            "//a[contains(text(), '导出')]",
            "//a[contains(text(), '下载')]",
            "button[class*='export']",
            "button[title*='导出']",
            "button[title*='下载']"
        ]
        
        for selector in export_selectors:
            try:
                if selector.startswith("//"):
                    export_elements = driver.find_elements(By.XPATH, selector)
                else:
                    export_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if export_elements:
                    logger.info(f"📎 Found {len(export_elements)} elements with selector: {selector}")
                    for j, elem in enumerate(export_elements):
                        elem_text = elem.get_attribute('textContent') or elem.text
                        elem_class = elem.get_attribute('class')
                        logger.info(f"  Export element {j}: text='{elem_text}', class='{elem_class}'")
            except:
                pass
        
        # Look for any elements with Chinese export text
        logger.info("\n🔍 Looking for elements containing export-related Chinese text...")
        chinese_export_texts = ["导出", "下载", "Export", "Download"]
        
        for text in chinese_export_texts:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                if elements:
                    logger.info(f"📋 Found {len(elements)} elements containing '{text}':")
                    for j, elem in enumerate(elements):
                        elem_tag = elem.tag_name
                        elem_text = elem.get_attribute('textContent') or elem.text
                        elem_class = elem.get_attribute('class')
                        logger.info(f"  {text} element {j}: tag='{elem_tag}', text='{elem_text[:50]}', class='{elem_class}'")
            except:
                pass
        
        # Take a screenshot for visual inspection
        logger.info("\n📸 Taking screenshot...")
        driver.save_screenshot("output/qbi_iframe_inspection.png")
        logger.info("✅ Screenshot saved to output/qbi_iframe_inspection.png")
        
        # Save page source
        logger.info("💾 Saving iframe page source...")
        with open("output/qbi_iframe_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("✅ Page source saved to output/qbi_iframe_source.html")
        
        logger.info("✅ Iframe inspection completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during inspection: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("🔄 Driver closed")

if __name__ == "__main__":
    inspect_iframe_elements() 