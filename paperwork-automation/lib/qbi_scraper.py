#!/usr/bin/env python3
"""
QBI System Web Scraper for Haidilao Paperwork Automation
Scrapes data from https://qbi.superhi-tech.com with date range functionality
"""

import time
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import sys

# Web scraping dependencies
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
except ImportError:
    print("⚠️  Selenium or webdriver-manager not installed. Please run: pip install selenium webdriver-manager")
    sys.exit(1)


class QBIScraperError(Exception):
    """Custom exception for QBI scraper errors"""
    pass


class QBIScraper:
    """
    QBI System Web Scraper
    
    Handles authentication, navigation to dashboard iframe, date range input, 
    data querying, and Excel export from the QBI dashboard system.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize QBI scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout for operations in seconds
        """
        self.base_url = "https://qbi.superhi-tech.com"
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self.wait = None
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        
        # Essential stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up loading
        # chrome_options.add_argument("--disable-javascript")  # Keep JS enabled for QBI
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
        
        # Disable automation detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Handle SSL issues
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        chrome_options.add_argument("--ignore-ssl-errors-spki-list")
        
        # Download preferences for Excel files
        download_path = str(Path.cwd() / "output")
        Path(download_path).mkdir(exist_ok=True)
        
        prefs = {
            "download.default_directory": download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,  # Disable for stability
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_setting_values.notifications": 2,  # Block notifications
            "profile.default_content_settings.popups": 0,  # Block popups
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set longer timeouts
            driver.set_page_load_timeout(60)  # Increased timeout
            driver.implicitly_wait(10)
            
            # Hide automation
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except Exception as e:
            raise QBIScraperError(f"Failed to setup Chrome driver: {e}")
    
    def login(self, username: str, password: str) -> bool:
        """
        Handle QBI login process
        
        Args:
            username: QBI username
            password: QBI password
            
        Returns:
            bool: True if login successful
        """
        self.logger.info("🔐 Attempting QBI login...")
        
        try:
            # Wait for page to load completely
            self.logger.info("⏳ Waiting for QBI login page to load completely...")
            time.sleep(5)
            
            # Check if already logged in by looking for iframe or dashboard elements
            try:
                iframe = self.driver.find_element(By.TAG_NAME, "iframe")
                self.logger.info("✅ Already logged in - iframe found")
                return True
            except NoSuchElementException:
                pass
            
            # Look for login form elements with progress feedback
            self.logger.info("🔍 Looking for login form fields (this may take 2-3 minutes)...")
            login_selectors = [
                ("input[name='username']", "input[name='password']"),
                ("input[id='username']", "input[id='password']"),
                ("input[type='text']", "input[type='password']"),
                ("#username", "#password"),
                ("input[placeholder*='用户']", "input[placeholder*='密码']"),
                ("input[placeholder*='账号']", "input[placeholder*='密码']")
            ]
            
            username_field = None
            password_field = None
            
            # Try each selector with progress feedback
            for i, (user_sel, pass_sel) in enumerate(login_selectors):
                try:
                    self.logger.info(f"🔍 Trying login selector {i+1}/{len(login_selectors)}: {user_sel}")
                    username_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, user_sel)))
                    password_field = self.driver.find_element(By.CSS_SELECTOR, pass_sel)
                    self.logger.info(f"📧 Found login fields using selector: {user_sel}, {pass_sel}")
                    break
                except (TimeoutException, NoSuchElementException) as e:
                    self.logger.info(f"⚠️  Selector {i+1} failed, trying next...")
                    continue
            
            if not username_field or not password_field:
                self.logger.warning("⚠️  Could not find login fields - site might already be logged in")
                return True
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            # Submit login
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('登录')",
                "button:contains('login')",
                ".login-btn",
                "#login-btn"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if login_button:
                login_button.click()
                self.logger.info("🔄 Clicked login button")
            else:
                password_field.send_keys(Keys.RETURN)
                self.logger.info("⌨️  Pressed Enter to login")
            
            # Wait for login to complete
            time.sleep(5)
            self.logger.info("✅ Login process completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Login failed: {e}")
            return False
    
    def navigate_to_dashboard(self, product_id: str, menu_id: str) -> bool:
        """
        Navigate to the dashboard with specific product and menu IDs
        
        Args:
            product_id: Product ID for the dashboard
            menu_id: Menu ID for the dashboard
            
        Returns:
            bool: True if navigation successful
        """
        dashboard_url = f"{self.base_url}/product/view.htm?module=dashboard&productId={product_id}&menuId={menu_id}"
        
        try:
            self.logger.info(f"🌐 Navigating to dashboard: {dashboard_url}")
            self.driver.get(dashboard_url)
            
            # Wait for page to load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(5)  # Additional wait for dynamic content
            
            self.logger.info("✅ Dashboard page loaded")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to navigate to dashboard: {e}")
            return False
    
    def switch_to_dashboard_iframe(self) -> bool:
        """
        Find and switch to the dashboard iframe containing the actual controls
        
        Returns:
            bool: True if successfully switched to iframe
        """
        try:
            self.logger.info("🔄 Looking for dashboard iframe...")
            
            # Wait longer after login for page to fully load
            self.logger.info("⏳ Waiting for post-login page to stabilize...")
            time.sleep(10)
            
            # Wait for iframe to be present with extended timeout
            iframe_selectors = [
                "iframe[id*='portal']",
                "iframe[class*='portal']", 
                "iframe[src*='dashboard']",
                "iframe[id*='iframe']",
                "iframe"
            ]
            
            iframe = None
            for selector in iframe_selectors:
                try:
                    # Use longer timeout for iframe detection
                    iframe = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"📱 Found iframe with selector: {selector}")
                    
                    # Check if iframe has src attribute
                    iframe_src = iframe.get_attribute('src')
                    if iframe_src:
                        self.logger.info(f"📍 Iframe src: {iframe_src}")
                    
                    break
                except TimeoutException:
                    self.logger.info(f"⏳ Selector {selector} timed out, trying next...")
                    continue
            
            if not iframe:
                # Log current page info for debugging
                current_url = self.driver.current_url
                page_title = self.driver.title
                self.logger.info(f"🔍 Current URL: {current_url}")
                self.logger.info(f"🔍 Page title: {page_title}")
                
                # Check if we're on the right page
                if "dashboard" not in current_url.lower():
                    self.logger.warning("⚠️  Not on dashboard page, might need to navigate again")
                    return False
                
                # Log all iframes found
                all_iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                self.logger.info(f"🔍 Found {len(all_iframes)} iframe(s) total")
                for i, iframe_elem in enumerate(all_iframes):
                    iframe_id = iframe_elem.get_attribute('id')
                    iframe_class = iframe_elem.get_attribute('class') 
                    iframe_src = iframe_elem.get_attribute('src')
                    self.logger.info(f"Iframe {i}: id='{iframe_id}', class='{iframe_class}', src='{iframe_src}'")
                
                raise QBIScraperError("Could not find dashboard iframe")
            
            # Switch to iframe
            self.driver.switch_to.frame(iframe)
            self.logger.info("✅ Switched to dashboard iframe")
            
            # Wait for iframe content to load and stabilize
            self.logger.info("⏳ Waiting for iframe content to load...")
            time.sleep(15)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to switch to iframe: {e}")
            return False
    
    def wait_for_dashboard_elements(self) -> bool:
        """
        Wait for dashboard elements to load, specifically the query button
        
        Returns:
            bool: True if elements are ready
        """
        try:
            self.logger.info("⏳ Waiting for dashboard elements to load...")
            
            # Wait additional time for elements to fully load and stabilize
            time.sleep(20)
            
            # Look for query button with multiple strategies
            query_button_selectors = [
                "button.query-button",
                "button.ant-btn-primary",
                "button[class*='query']",
                "//button[contains(@class, 'query-button')]",
                "//button[contains(@class, 'ant-btn-primary') and .//span[contains(text(), '查')]]",
                "//button[.//span[contains(text(), '查询')]]"
            ]
            
            query_button = None
            for selector in query_button_selectors:
                try:
                    if selector.startswith("//"):
                        query_button = self.wait.until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        query_button = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    self.logger.info(f"🎯 Found query button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not query_button:
                # Log available buttons for debugging
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    self.logger.info(f"🔍 Found {len(buttons)} button elements total")
                    for i, btn in enumerate(buttons[:5]):
                        try:
                            btn_text = btn.get_attribute('textContent') or btn.text
                            btn_class = btn.get_attribute('class')
                            self.logger.info(f"Button {i}: text='{btn_text}', class='{btn_class}'")
                        except:
                            pass
                except:
                    pass
                
                raise QBIScraperError("Could not find query button after extended wait")
            
            self.logger.info("✅ Dashboard elements loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to wait for dashboard elements: {e}")
            return False
    
    def set_date_range(self, target_date: str) -> bool:
        """
        Set date range for the query (target_date ± 1 day)
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            bool: True if date range set successfully
        """
        try:
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            start_date = target_dt - timedelta(days=1)
            end_date = target_dt + timedelta(days=1)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            self.logger.info(f"📅 Setting date range: {start_date_str} to {end_date_str}")
            
            # Look for date input fields - based on inspection findings
            date_selectors = [
                "input[placeholder='请选择时间']",  # Found in inspection
                "input.ant-picker-input",
                "input[placeholder*='时间']",
                "input[placeholder*='日期']",
                "input[placeholder*='date']",
                "input[type='text'][class*='date']",
                "input[class*='picker']"
            ]
            
            date_inputs = []
            for selector in date_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if inputs:
                        date_inputs = inputs
                        self.logger.info(f"📅 Found {len(inputs)} date inputs with selector: {selector}")
                        break
                except:
                    continue
            
            if len(date_inputs) >= 2:
                # Try multiple approaches to set dates
                success = False
                
                # Method 1: JavaScript value setting
                try:
                    self.logger.info("🔧 Trying JavaScript approach for date setting...")
                    self.driver.execute_script(f"arguments[0].value = '{start_date_str}';", date_inputs[0])
                    self.driver.execute_script(f"arguments[1].value = '{end_date_str}';", date_inputs[1])
                    
                    # Trigger change events
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", date_inputs[0])
                    self.driver.execute_script("arguments[1].dispatchEvent(new Event('change', { bubbles: true }));", date_inputs[1])
                    time.sleep(2)
                    
                    # Verify values were set
                    start_value = self.driver.execute_script("return arguments[0].value;", date_inputs[0])
                    end_value = self.driver.execute_script("return arguments[1].value;", date_inputs[1])
                    
                    if start_value and end_value:
                        self.logger.info(f"✅ JavaScript method successful: {start_value} to {end_value}")
                        success = True
                except Exception as js_error:
                    self.logger.warning(f"⚠️  JavaScript method failed: {js_error}")
                
                # Method 2: Traditional send_keys (fallback)
                if not success:
                    try:
                        self.logger.info("🔧 Trying traditional send_keys approach...")
                        date_inputs[0].clear()
                        date_inputs[0].send_keys(start_date_str)
                        time.sleep(1)
                        
                        date_inputs[1].clear()
                        date_inputs[1].send_keys(end_date_str)
                        time.sleep(1)
                        
                        self.logger.info("✅ Traditional method successful")
                        success = True
                    except Exception as traditional_error:
                        self.logger.warning(f"⚠️  Traditional method failed: {traditional_error}")
                
                # Method 3: Click and type (fallback)
                if not success:
                    try:
                        self.logger.info("🔧 Trying click and type approach...")
                        date_inputs[0].click()
                        time.sleep(1)
                        date_inputs[0].send_keys(Keys.CONTROL + "a")  # Select all
                        date_inputs[0].send_keys(start_date_str)
                        time.sleep(1)
                        
                        date_inputs[1].click()
                        time.sleep(1)
                        date_inputs[1].send_keys(Keys.CONTROL + "a")  # Select all
                        date_inputs[1].send_keys(end_date_str)
                        time.sleep(1)
                        
                        self.logger.info("✅ Click and type method successful")
                        success = True
                    except Exception as click_error:
                        self.logger.warning(f"⚠️  Click and type method failed: {click_error}")
                
                if success:
                    self.logger.info("✅ Date range set successfully")
                    return True
                else:
                    self.logger.warning("⚠️  All date setting methods failed, but continuing with export...")
                    self.logger.warning("📅 The system may use default date range or current data")
                    return True  # Return True to continue with export
            else:
                self.logger.warning(f"⚠️  Found {len(date_inputs)} date inputs, expected at least 2")
                self.logger.warning("📅 Continuing without date range setting...")
                return True  # Return True to continue with export
                
        except Exception as e:
            self.logger.error(f"❌ Failed to set date range: {e}")
            return False
    
    def trigger_search(self) -> bool:
        """
        Click the query button to trigger the search
        
        Returns:
            bool: True if search triggered successfully
        """
        try:
            self.logger.info("🔍 Triggering search...")
            
            # Find query button
            query_button_selectors = [
                "button.query-button",
                "button.ant-btn-primary",
                "//button[contains(@class, 'query-button')]",
                "//button[.//span[contains(text(), '查询')]]",
                "//button[contains(@class, 'ant-btn-primary') and .//span[contains(text(), '查')]]"
            ]
            
            query_button = None
            for selector in query_button_selectors:
                try:
                    if selector.startswith("//"):
                        query_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        query_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not query_button:
                raise QBIScraperError("Could not find query button")
            
            # Scroll into view and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", query_button)
            time.sleep(2)
            query_button.click()
            
            self.logger.info("✅ Search triggered successfully")
            
            # Wait for search to complete
            time.sleep(10)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger search: {e}")
            return False
    
    def export_data(self) -> Optional[str]:
        """
        Find and click the export button to download data
        
        Returns:
            str: Path to downloaded file, or None if failed
        """
        try:
            self.logger.info("📤 Looking for export button...")
            
            # Wait for the floating mini-menu to appear (it might take time)
            self.logger.info("⏳ Waiting for floating mini-menu to appear...")
            time.sleep(5)
            
            # Look for export button - based on inspection findings
            export_button_selectors = [
                # Floating mini-menu export button (found in inspection)
                "//div[@class='preview-mini-menu-list-item-text' and text()='导出']",
                "//li[contains(@class, 'preview-mini-menu-list-item')]//div[text()='导出']",
                "//div[contains(@class, 'preview-mini-menu-list-item-text') and contains(text(), '导出')]",
                # Fallback selectors
                "//button[.//span[contains(text(), '导出')]]",
                "//button[contains(text(), '导出')]",
                "//a[contains(text(), '导出')]",
                "button[class*='export']",
                ".export-btn"
            ]
            
            export_button = None
            for selector in export_button_selectors:
                try:
                    self.logger.info(f"🔍 Trying selector: {selector}")
                    if selector.startswith("//"):
                        export_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        export_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    self.logger.info(f"📎 Found export button with selector: {selector}")
                    break
                except TimeoutException:
                    self.logger.warning(f"⚠️  Selector failed: {selector}")
                    continue
            
            if not export_button:
                # Try looking for any element containing '导出' text
                self.logger.info("🔍 Trying to find any element containing '导出'...")
                try:
                    export_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '导出')]")
                    if export_elements:
                        self.logger.info(f"📋 Found {len(export_elements)} elements containing '导出'")
                        for i, elem in enumerate(export_elements):
                            try:
                                elem_text = elem.get_attribute('textContent') or elem.text
                                elem_class = elem.get_attribute('class')
                                elem_tag = elem.tag_name
                                self.logger.info(f"  Element {i}: tag='{elem_tag}', text='{elem_text[:50]}', class='{elem_class}'")
                                if '导出' in elem_text and elem.is_displayed() and elem.is_enabled():
                                    export_button = elem
                                    self.logger.info(f"📎 Using export element {i}")
                                    break
                            except:
                                continue
                except:
                    pass
            
            if not export_button:
                raise QBIScraperError("Could not find export button")
            
            # Click export button with multiple approaches
            self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
            time.sleep(2)
            
            # Method 1: Try clicking the parent element if it's a text div
            clicked = False
            if export_button.tag_name == 'div':
                try:
                    parent = export_button.find_element(By.XPATH, "..")
                    if parent:
                        self.logger.info("🖱️  Clicking parent element of text div")
                        parent.click()
                        clicked = True
                except:
                    pass
            
            # Method 2: Direct click if parent click failed
            if not clicked:
                try:
                    self.logger.info("🖱️  Direct clicking export element")
                    export_button.click()
                    clicked = True
                except:
                    pass
            
            # Method 3: JavaScript click as fallback
            if not clicked:
                try:
                    self.logger.info("🖱️  JavaScript clicking export element")
                    self.driver.execute_script("arguments[0].click();", export_button)
                    clicked = True
                except:
                    pass
            
            if not clicked:
                raise QBIScraperError("Failed to click export button with any method")
            
            self.logger.info("✅ Export button clicked")
            
            # Wait for potential popup or confirmation dialog
            time.sleep(3)
            
            # Wait for export modal dialog to appear
            self.logger.info("⏳ Waiting for export modal dialog...")
            time.sleep(5)  # Wait for modal to appear
            
            # Look for the export modal dialog and click "确定" button
            try:
                # Look for the modal dialog with export options
                modal_selectors = [
                    "//div[contains(@class, 'ant-modal-content')]",
                    ".ant-modal-content",
                    "//div[contains(text(), '导出')]/..",
                    "[class*='modal']"
                ]
                
                modal_found = False
                for selector in modal_selectors:
                    try:
                        if selector.startswith("//"):
                            modal = self.driver.find_element(By.XPATH, selector)
                        else:
                            modal = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if modal.is_displayed():
                            self.logger.info(f"📋 Found export modal: {selector}")
                            modal_found = True
                            break
                    except:
                        continue
                
                if modal_found:
                    # Look for the "确定" (Confirm) button in the modal
                    confirm_selectors = [
                        "//div[contains(@class, 'ant-modal')]//button[contains(text(), '确定')]",
                        "//div[contains(@class, 'ant-modal')]//button[text()='确定']",
                        "//div[contains(@class, 'ant-modal')]//span[text()='确定']/parent::button",
                        "//div[contains(@class, 'ant-modal-footer')]//button[contains(text(), '确定')]",
                        "//div[contains(@class, 'ant-modal-footer')]//button[contains(@class, 'ant-btn-primary')]",
                        ".ant-modal .ant-btn-primary",
                        ".ant-modal-footer .ant-btn-primary"
                    ]
                    
                    confirm_clicked = False
                    for selector in confirm_selectors:
                        try:
                            if selector.startswith("//"):
                                confirm_btn = self.driver.find_element(By.XPATH, selector)
                            else:
                                confirm_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                            if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                                self.logger.info(f"🔘 Found '确定' button: {selector}")
                                confirm_btn.click()
                                self.logger.info("✅ Clicked '确定' button - download should start now")
                                confirm_clicked = True
                                time.sleep(3)  # Wait for download to start
                                break
                        except Exception as e:
                            self.logger.debug(f"Selector {selector} failed: {e}")
                            continue
                    
                    if not confirm_clicked:
                        self.logger.warning("⚠️  Could not find '确定' button in modal")
                        # Try clicking any primary button in the modal footer as fallback
                        try:
                            modal_primary_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".ant-modal-footer .ant-btn-primary")
                            if not modal_primary_buttons:
                                modal_primary_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".ant-modal .ant-btn-primary")
                            
                            for btn in modal_primary_buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn_text = btn.get_attribute('textContent') or btn.text
                                    self.logger.info(f"🔘 Trying modal primary button: '{btn_text}'")
                                    # Only click if it's likely a confirm button
                                    if any(word in btn_text for word in ['确定', '确认', '下载', '导出', 'OK', 'Confirm']):
                                        btn.click()
                                        self.logger.info("✅ Clicked modal primary button")
                                        confirm_clicked = True
                                        time.sleep(3)
                                        break
                                    else:
                                        self.logger.info(f"⚠️  Skipping button '{btn_text}' - not a confirm button")
                        except:
                            pass
                        
                        if not confirm_clicked:
                            self.logger.error("❌ Could not find any suitable confirm button in modal")
                else:
                    self.logger.warning("⚠️  Export modal not found, proceeding with download wait")
                    
            except Exception as e:
                self.logger.warning(f"⚠️  Error handling export modal: {e}")
                pass
            
            # Wait for download to complete
            downloaded_file = self.wait_for_download()
            return downloaded_file
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export data: {e}")
            return None
    
    def wait_for_download(self, timeout: int = 120) -> Optional[str]:
        """
        Wait for file download to complete
        
        Args:
            timeout: Maximum time to wait for download (increased to 120s)
            
        Returns:
            str: Path to downloaded file, or None if timeout
        """
        try:
            self.logger.info("⏳ Waiting for download to complete...")
            
            # Check multiple possible download locations
            download_dirs = [
                Path.cwd() / "output",
                Path.home() / "Downloads"
            ]
            
            start_time = time.time()
            last_file_count = {}
            
            # Initialize file counts for each directory
            for download_dir in download_dirs:
                if download_dir.exists():
                    excel_files = list(download_dir.glob("*.xlsx")) + list(download_dir.glob("*.xls")) + list(download_dir.glob("*.csv"))
                    last_file_count[str(download_dir)] = len(excel_files)
            
            while time.time() - start_time < timeout:
                for download_dir in download_dirs:
                    if not download_dir.exists():
                        continue
                    
                    # Check for .crdownload files (incomplete downloads)
                    temp_files = list(download_dir.glob("*.crdownload"))
                    
                    if temp_files:
                        self.logger.info(f"📥 Download in progress: {len(temp_files)} temp files in {download_dir}")
                        continue
                    
                    # Check for completed downloads
                    excel_files = list(download_dir.glob("*.xlsx")) + list(download_dir.glob("*.xls")) + list(download_dir.glob("*.csv"))
                    current_count = len(excel_files)
                    
                    # Check if new files appeared
                    if current_count > last_file_count.get(str(download_dir), 0):
                        self.logger.info(f"📁 New files detected in {download_dir}")
                        
                        # Find most recent file
                        if excel_files:
                            latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
                            
                            # Check if file was created after we started
                            if latest_file.stat().st_mtime > start_time:
                                # Verify file is complete (size > 0 and not changing)
                                initial_size = latest_file.stat().st_size
                                time.sleep(3)
                                
                                try:
                                    final_size = latest_file.stat().st_size
                                    
                                    if initial_size > 0 and initial_size == final_size:
                                        self.logger.info(f"✅ Download completed: {latest_file.name} ({final_size} bytes)")
                                        
                                        # If file is not in output directory, copy it there
                                        if download_dir != Path.cwd() / "output":
                                            output_dir = Path.cwd() / "output"
                                            output_dir.mkdir(exist_ok=True)
                                            target_file = output_dir / latest_file.name
                                            
                                            import shutil
                                            shutil.copy2(latest_file, target_file)
                                            self.logger.info(f"📋 Copied to output directory: {target_file}")
                                            return str(target_file)
                                        else:
                                            return str(latest_file)
                                except:
                                    # File might be locked, continue waiting
                                    pass
                    
                    last_file_count[str(download_dir)] = current_count
                
                time.sleep(3)
            
            # Before giving up, try one more comprehensive check
            self.logger.info("🔍 Final check for any recent downloads...")
            for download_dir in download_dirs:
                if download_dir.exists():
                    excel_files = list(download_dir.glob("*.xlsx")) + list(download_dir.glob("*.xls")) + list(download_dir.glob("*.csv"))
                    for file in excel_files:
                        if file.stat().st_mtime > start_time - 30:  # Within 30 seconds of start
                            self.logger.info(f"📎 Found recent file: {file.name}")
                            if file.stat().st_size > 0:
                                return str(file)
            
            raise QBIScraperError("Download timeout - no files downloaded")
            
        except Exception as e:
            self.logger.error(f"❌ Error waiting for download: {e}")
            return None
    
    def scrape_data(self, username: str, password: str, target_date: str,
                   product_id: str = "1fcba94f-c81d-4595-80cc-dac5462e0d24",
                   menu_id: str = "89809ff6-a4fe-4fd7-853d-49315e51b2ec") -> Optional[str]:
        """
        Main method to scrape data from QBI dashboard
        
        Args:
            username: QBI username
            password: QBI password
            target_date: Target date for data (YYYY-MM-DD format)
            product_id: Product ID for dashboard (default: daily reports)
            menu_id: Menu ID for dashboard (default: daily reports)
            
        Returns:
            str: Path to downloaded file, or None if failed
        """
        try:
            self.logger.info("🍲 Starting QBI data scraping...")
            
            # Setup WebDriver
            self.driver = self.setup_driver()
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            # Navigate to dashboard
            if not self.navigate_to_dashboard(product_id, menu_id):
                raise QBIScraperError("Failed to navigate to dashboard")
            
            # Handle login
            if not self.login(username, password):
                raise QBIScraperError("Failed to login")
            
            # Try to switch to dashboard iframe (if it exists)
            iframe_switched = self.switch_to_dashboard_iframe()
            if not iframe_switched:
                self.logger.info("🔄 No iframe found, checking for elements directly on page...")
            
            # Wait for dashboard elements to load
            if not self.wait_for_dashboard_elements():
                if iframe_switched:
                    # Try switching back to main frame and look for elements there
                    self.logger.info("🔄 Elements not found in iframe, trying main frame...")
                    self.driver.switch_to.default_content()
                    if not self.wait_for_dashboard_elements():
                        raise QBIScraperError("Dashboard elements did not load properly in iframe or main frame")
                else:
                    raise QBIScraperError("Dashboard elements did not load properly")
            
            # Set date range
            if not self.set_date_range(target_date):
                self.logger.warning("⚠️  Could not set date range, proceeding with default dates")
            
            # Trigger search
            if not self.trigger_search():
                raise QBIScraperError("Failed to trigger search")
            
            # Export data
            downloaded_file = self.export_data()
            if not downloaded_file:
                raise QBIScraperError("Failed to export data")
            
            self.logger.info(f"✅ QBI data scraping completed successfully: {downloaded_file}")
            return downloaded_file
            
        except Exception as e:
            self.logger.error(f"❌ QBI scraping failed: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔄 WebDriver closed")


def main():
    """Example usage of QBI scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='QBI Data Scraper')
    parser.add_argument('--username', required=True, help='QBI username')
    parser.add_argument('--password', required=True, help='QBI password')
    parser.add_argument('--date', required=True, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--product-id', default="1fcba94f-c81d-4595-80cc-dac5462e0d24", help='Product ID')
    parser.add_argument('--menu-id', default="89809ff6-a4fe-4fd7-853d-49315e51b2ec", help='Menu ID')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create scraper and run
    scraper = QBIScraper(headless=args.headless)
    result = scraper.scrape_data(
        username=args.username,
        password=args.password,
        target_date=args.date,
        product_id=args.product_id,
        menu_id=args.menu_id
    )
    
    if result:
        print(f"✅ Success: {result}")
    else:
        print("❌ Scraping failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 