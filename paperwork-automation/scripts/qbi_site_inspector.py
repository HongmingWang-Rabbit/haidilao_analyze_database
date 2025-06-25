#!/usr/bin/env python3
"""
QBI Site Inspector
Inspect the QBI dashboard structure to understand elements for scraping
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

class QBIInspector:
    """QBI Site Inspector for understanding page structure"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
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
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
            return True
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return False
    
    def get_credentials(self):
        """Get QBI credentials"""
        username = os.getenv('QBI_USERNAME')
        password = os.getenv('QBI_PASSWORD')
        
        if not username:
            username = input("QBI Username: ").strip()
        
        if not password:
            password = getpass.getpass("QBI Password: ")
        
        return username, password
    
    def inspect_page_elements(self, element_type="all"):
        """Inspect page elements and return their details"""
        print(f"\n🔍 Inspecting {element_type} elements...")
        
        elements_found = []
        
        if element_type in ["all", "inputs"]:
            # Find all input elements
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"📝 Found {len(inputs)} input elements:")
            for i, input_el in enumerate(inputs):
                try:
                    input_info = {
                        'tag': 'input',
                        'type': input_el.get_attribute('type'),
                        'name': input_el.get_attribute('name'),
                        'id': input_el.get_attribute('id'),
                        'class': input_el.get_attribute('class'),
                        'placeholder': input_el.get_attribute('placeholder'),
                        'value': input_el.get_attribute('value'),
                        'visible': input_el.is_displayed()
                    }
                    elements_found.append(input_info)
                    
                    if input_info['visible']:
                        print(f"  [{i+1}] Type: {input_info['type']}, Name: {input_info['name']}, "
                              f"ID: {input_info['id']}, Placeholder: {input_info['placeholder']}")
                except Exception as e:
                    print(f"  [{i+1}] Error reading input: {e}")
        
        if element_type in ["all", "buttons"]:
            # Find all button elements
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"\n🔘 Found {len(buttons)} button elements:")
            for i, button in enumerate(buttons):
                try:
                    button_info = {
                        'tag': 'button',
                        'type': button.get_attribute('type'),
                        'name': button.get_attribute('name'),
                        'id': button.get_attribute('id'),
                        'class': button.get_attribute('class'),
                        'text': button.text.strip(),
                        'title': button.get_attribute('title'),
                        'visible': button.is_displayed()
                    }
                    elements_found.append(button_info)
                    
                    if button_info['visible'] and button_info['text']:
                        print(f"  [{i+1}] Text: '{button_info['text']}', Type: {button_info['type']}, "
                              f"ID: {button_info['id']}, Class: {button_info['class']}")
                except Exception as e:
                    print(f"  [{i+1}] Error reading button: {e}")
        
        if element_type in ["all", "links"]:
            # Find all link elements with relevant text
            links = self.driver.find_elements(By.TAG_NAME, "a")
            relevant_links = []
            for link in links:
                try:
                    text = link.text.strip()
                    if any(keyword in text.lower() for keyword in ['导出', '下载', 'export', 'download', '查询', '搜索']):
                        link_info = {
                            'tag': 'a',
                            'text': text,
                            'href': link.get_attribute('href'),
                            'id': link.get_attribute('id'),
                            'class': link.get_attribute('class'),
                            'visible': link.is_displayed()
                        }
                        relevant_links.append(link_info)
                        elements_found.append(link_info)
                except:
                    continue
            
            print(f"\n🔗 Found {len(relevant_links)} relevant link elements:")
            for i, link_info in enumerate(relevant_links):
                if link_info['visible']:
                    print(f"  [{i+1}] Text: '{link_info['text']}', ID: {link_info['id']}, "
                          f"Class: {link_info['class']}")
        
        return elements_found
    
    def save_page_source(self, filename="qbi_page_source.html"):
        """Save current page source for analysis"""
        try:
            page_source = self.driver.page_source
            output_path = Path("output") / filename
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"📄 Page source saved to: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"❌ Failed to save page source: {e}")
            return None
    
    def take_screenshot(self, filename="qbi_screenshot.png"):
        """Take screenshot of current page"""
        try:
            output_path = Path("output") / filename
            output_path.parent.mkdir(exist_ok=True)
            
            self.driver.save_screenshot(str(output_path))
            print(f"📸 Screenshot saved to: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"❌ Failed to take screenshot: {e}")
            return None
    
    def wait_for_page_load(self, timeout=30):
        """Wait for key page elements to load"""
        print("⏳ Waiting for page elements to load...")
        
        # Wait for common indicators that the page is fully loaded
        wait_indicators = [
            "//button[contains(text(), '查询')]",  # Search button
            "//button[contains(text(), '导出')]",  # Export button
            "//input[@type='date']",              # Date inputs
            "//input[contains(@placeholder, '日期')]",  # Date placeholder
            "//div[@class and contains(@class, 'dashboard')]",  # Dashboard container
            "//div[@class and contains(@class, 'content')]"     # Content container
        ]
        
        # Try to wait for any of these elements
        for i, xpath in enumerate(wait_indicators):
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                print(f"✅ Found loading indicator {i+1}: {xpath}")
                break
            except TimeoutException:
                continue
        
        # Additional wait for JavaScript to complete
        print("⏳ Waiting for JavaScript to complete...")
        time.sleep(5)
        
        # Wait for any AJAX/dynamic content
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return jQuery.active == 0") if driver.execute_script("return typeof jQuery !== 'undefined'") else True
            )
            print("✅ jQuery requests completed")
        except:
            pass
        
        # Final wait to ensure everything is stable
        time.sleep(3)
        print("✅ Page loading wait completed")

    def wait_for_search_button(self, timeout=30):
        """Specifically wait for the 查询 button to appear"""
        print("🔍 Waiting for 查询 (search) button to appear...")
        
        search_button_xpaths = [
            "//button[contains(text(), '查询')]",
            "//input[@value='查询']",
            "//a[contains(text(), '查询')]",
            "//button[contains(@title, '查询')]",
            "//button[contains(@class, 'search')]",
            "//button[contains(@class, 'query')]"
        ]
        
        for xpath in search_button_xpaths:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                print(f"✅ Found search button: {xpath}")
                return element
            except TimeoutException:
                continue
        
        print("⚠️  Search button not found after waiting")
        return None

    def inspect_qbi_site(self, target_url, username, password):
        """Complete QBI site inspection workflow"""
        print("🚀 Starting QBI Site Inspection")
        print("=" * 50)
        
        try:
            # Navigate to target URL
            print(f"🌐 Navigating to: {target_url}")
            self.driver.get(target_url)
            time.sleep(3)
            
            # Take initial screenshot
            self.take_screenshot("qbi_initial_page.png")
            
            # Check if we need to login
            print("\n🔐 Checking for login requirements...")
            
            # Look for login elements
            login_indicators = [
                "input[type='password']",
                "input[name*='password']",
                "input[placeholder*='密码']",
                ".login",
                "#login"
            ]
            
            needs_login = False
            for indicator in login_indicators:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, indicator)
                    needs_login = True
                    break
                except NoSuchElementException:
                    continue
            
            if needs_login:
                print("🔑 Login required - attempting authentication...")
                
                # Try to find username field
                username_selectors = [
                    "input[name='username']",
                    "input[type='text']",
                    "input[id='username']",
                    "input[placeholder*='用户']",
                    "input[placeholder*='账号']"
                ]
                
                username_field = None
                for selector in username_selectors:
                    try:
                        username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"📧 Found username field: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                # Try to find password field
                password_field = None
                password_selectors = [
                    "input[type='password']",
                    "input[name='password']",
                    "input[placeholder*='密码']"
                ]
                
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"🔒 Found password field: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                if username_field and password_field:
                    # Enter credentials
                    username_field.clear()
                    username_field.send_keys(username)
                    password_field.clear()
                    password_field.send_keys(password)
                    
                    # Try to submit
                    password_field.send_keys(Keys.RETURN)
                    time.sleep(5)
                    
                    print("✅ Login attempt completed")
                    self.take_screenshot("qbi_after_login.png")
                else:
                    print("⚠️  Could not find login fields")
            else:
                print("✅ No login required or already authenticated")
            
            # Wait for page to fully load
            print("\n⏳ Waiting for dashboard to fully load...")
            self.wait_for_page_load()
            
            # Wait specifically for search button
            search_button = self.wait_for_search_button()
            
            # Take screenshot after page is loaded
            self.take_screenshot("qbi_after_page_load.png")
            
            # Inspect current page
            print("\n🔍 Analyzing page structure...")
            
            # Get page title and URL
            print(f"📋 Page Title: {self.driver.title}")
            print(f"🔗 Current URL: {self.driver.current_url}")
            
            # Inspect elements
            elements = self.inspect_page_elements("all")
            
            # Save page source
            self.save_page_source("qbi_dashboard.html")
            
            # Look for date-related elements specifically
            print("\n📅 Looking for date input elements...")
            date_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='date'], input[placeholder*='日期'], input[name*='date'], input[id*='date'], input[class*='date']")
            
            if date_inputs:
                print(f"📅 Found {len(date_inputs)} date input elements:")
                for i, date_input in enumerate(date_inputs):
                    print(f"  [{i+1}] Type: {date_input.get_attribute('type')}, "
                          f"Name: {date_input.get_attribute('name')}, "
                          f"ID: {date_input.get_attribute('id')}, "
                          f"Class: {date_input.get_attribute('class')}, "
                          f"Placeholder: {date_input.get_attribute('placeholder')}")
            else:
                print("⚠️  No obvious date input elements found")
            
            # Look for search/query buttons with more detail
            print("\n🔍 Looking for search/query buttons...")
            search_buttons = []
            search_texts = ['查询', '搜索', 'search', 'query', '确认', '提交']
            
            for text in search_texts:
                try:
                    # Look in buttons
                    buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    for btn in buttons:
                        search_buttons.append({
                            'element': btn,
                            'type': 'button',
                            'text': btn.text,
                            'id': btn.get_attribute('id'),
                            'class': btn.get_attribute('class'),
                            'visible': btn.is_displayed()
                        })
                    
                    # Look in inputs
                    inputs = self.driver.find_elements(By.XPATH, f"//input[@value='{text}']")
                    for inp in inputs:
                        search_buttons.append({
                            'element': inp,
                            'type': 'input',
                            'value': inp.get_attribute('value'),
                            'id': inp.get_attribute('id'),
                            'class': inp.get_attribute('class'),
                            'visible': inp.is_displayed()
                        })
                except:
                    pass
            
            if search_buttons:
                print(f"🔍 Found {len(search_buttons)} search/query elements:")
                for i, btn_info in enumerate(search_buttons):
                    if btn_info['visible']:
                        print(f"  [{i+1}] Type: {btn_info['type']}, Text/Value: '{btn_info.get('text', btn_info.get('value', ''))}', "
                              f"ID: {btn_info['id']}, Class: {btn_info['class']}")
            else:
                print("⚠️  No obvious search buttons found")
            
            # Look for export/download buttons with more detail
            print("\n📊 Looking for export/download buttons...")
            export_buttons = []
            export_texts = ['导出', '下载', 'export', 'download', '输出', '保存']
            
            for text in export_texts:
                try:
                    # Look in buttons and links
                    elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')] | //a[contains(text(), '{text}')] | //input[@value='{text}']")
                    for elem in elements:
                        export_buttons.append({
                            'element': elem,
                            'tag': elem.tag_name,
                            'text': elem.text or elem.get_attribute('value'),
                            'id': elem.get_attribute('id'),
                            'class': elem.get_attribute('class'),
                            'href': elem.get_attribute('href') if elem.tag_name == 'a' else None,
                            'visible': elem.is_displayed()
                        })
                except:
                    pass
            
            if export_buttons:
                print(f"📊 Found {len(export_buttons)} export/download elements:")
                for i, btn_info in enumerate(export_buttons):
                    if btn_info['visible']:
                        print(f"  [{i+1}] Tag: {btn_info['tag']}, Text: '{btn_info['text']}', "
                              f"ID: {btn_info['id']}, Class: {btn_info['class']}")
            else:
                print("⚠️  No obvious export buttons found")
            
            # Look for any form elements
            print("\n📋 Looking for form elements...")
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                print(f"📋 Found {len(forms)} form elements:")
                for i, form in enumerate(forms):
                    print(f"  [{i+1}] ID: {form.get_attribute('id')}, "
                          f"Class: {form.get_attribute('class')}, "
                          f"Action: {form.get_attribute('action')}")
            
            # Final screenshot
            self.take_screenshot("qbi_final_analysis.png")
            
            print("\n✅ QBI site inspection completed!")
            print(f"📁 Check the 'output' folder for screenshots and page source")
            
            # Keep browser open for manual inspection if not headless
            if not self.headless:
                input("\n⏸️  Press Enter to close browser and continue...")
            
        except Exception as e:
            print(f"❌ Inspection failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()


def main():
    """Main inspection function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='QBI Site Inspector')
    parser.add_argument('--url', required=True, help='Target QBI URL to inspect')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--username', help='QBI username')
    parser.add_argument('--password', help='QBI password')
    
    args = parser.parse_args()
    
    inspector = QBIInspector(headless=args.headless)
    
    try:
        if not inspector.setup_driver():
            sys.exit(1)
        
        # Get credentials
        if args.username and args.password:
            username, password = args.username, args.password
        else:
            username, password = inspector.get_credentials()
        
        # Run inspection
        inspector.inspect_qbi_site(args.url, username, password)
        
    except KeyboardInterrupt:
        print("\n🛑 Inspection cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        inspector.cleanup()


if __name__ == "__main__":
    main() 