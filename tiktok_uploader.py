import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class TikTokUploader:
    def __init__(self, config):
        """Initialize TikTok uploader with configuration"""
        self.config = config
    
    def setup_chrome_driver(self):
        """Setup Chrome driver with persistent session"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Use persistent user data directory to maintain login session
        user_data_dir = os.path.join(os.getcwd(), "chrome_user_data")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Optional: uncomment for headless mode (not recommended for first-time login)
        # chrome_options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def login_tiktok_with_google(self, driver):
        """Login to TikTok using Google OAuth"""
        try:
            wait = WebDriverWait(driver, 30)
            
            # Navigate to TikTok login page
            driver.get("https://www.tiktok.com/login")
            time.sleep(3)
            
            # Look for Google login button
            try:
                # Try different possible selectors for Google login
                google_login_selectors = [
                    "//div[contains(text(), 'Continue with Google')]",
                    "//button[contains(text(), 'Continue with Google')]",
                    "//div[contains(@class, 'google')]//parent::div",
                    "//*[contains(text(), 'Google')]//ancestor::div[contains(@class, 'login')]"
                ]
                
                google_button = None
                for selector in google_login_selectors:
                    try:
                        google_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except:
                        continue
                
                if not google_button:
                    logger.error("Could not find Google login button")
                    return False
                
                # Click Google login button
                google_button.click()
                time.sleep(3)
                
                # Handle Google OAuth flow
                # Switch to Google login window if it opens in a new tab
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                
                # Check if we need to enter Google credentials
                try:
                    # Check if already logged in to Google
                    wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
                    
                    # Enter Google email
                    email_input = driver.find_element(By.ID, "identifierId")
                    email_input.send_keys(self.config['google']['email'])
                    
                    # Click Next
                    next_button = driver.find_element(By.ID, "identifierNext")
                    next_button.click()
                    time.sleep(3)
                    
                    # Enter password
                    password_input = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
                    password_input.send_keys(self.config['google']['password'])
                    
                    # Click Next
                    password_next = driver.find_element(By.ID, "passwordNext")
                    password_next.click()
                    time.sleep(5)
                    
                except:
                    # Might already be logged in to Google, continue
                    pass
                
                # Wait for redirect back to TikTok
                wait.until(lambda driver: "tiktok.com" in driver.current_url)
                
                # Switch back to main window if needed
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[0])
                
                # Verify login success
                time.sleep(5)
                
                # Check if we're logged in by looking for profile or upload elements
                try:
                    # Look for elements that indicate successful login
                    logged_in_indicators = [
                        "//div[contains(@class, 'avatar')]",
                        "//a[contains(@href, '/upload')]",
                        "//*[contains(text(), 'Upload')]"
                    ]
                    
                    for indicator in logged_in_indicators:
                        try:
                            driver.find_element(By.XPATH, indicator)
                            logger.info("Successfully logged in to TikTok with Google")
                            return True
                        except:
                            continue
                    
                    # If no indicators found, assume login failed
                    logger.warning("Login may have failed - no login indicators found")
                    return False
                    
                except Exception as e:
                    logger.error(f"Error verifying login: {str(e)}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error during Google login: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error in login_tiktok_with_google: {str(e)}")
            return False

    def check_login_status(self, driver):
        """Check if already logged in to TikTok"""
        try:
            # Navigate to TikTok homepage
            driver.get("https://www.tiktok.com")
            time.sleep(3)
            
            # Check for login indicators
            logged_in_indicators = [
                "//div[contains(@class, 'avatar')]",
                "//a[contains(@href, '/upload')]",
                "//*[contains(text(), 'Upload')]",
                "//div[contains(@class, 'user-info')]"
            ]
            
            for indicator in logged_in_indicators:
                try:
                    driver.find_element(By.XPATH, indicator)
                    logger.info("Already logged in to TikTok")
                    return True
                except:
                    continue
            
            logger.info("Not logged in to TikTok")
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False

    def upload_to_tiktok(self, video_path, metadata):
        """Upload video to TikTok using Selenium with Google OAuth"""
        driver = None
        try:
            # Setup Chrome driver
            driver = self.setup_chrome_driver()
            
            # Check if already logged in
            if not self.check_login_status(driver):
                # Attempt login with Google
                if not self.login_tiktok_with_google(driver):
                    logger.error("Failed to login to TikTok")
                    return False
            
            # Navigate to upload page
            driver.get("https://www.tiktok.com/upload")
            wait = WebDriverWait(driver, 30)
            time.sleep(5)
            
            # Upload video file
            try:
                # Look for file input
                file_input_selectors = [
                    "input[type='file']",
                    "input[accept*='video']",
                    ".upload-btn input[type='file']"
                ]
                
                file_input = None
                for selector in file_input_selectors:
                    try:
                        file_input = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if not file_input:
                    logger.error("Could not find file input element")
                    return False
                
                # Upload the video
                file_input.send_keys(os.path.abspath(video_path))
                logger.info("Video file uploaded, waiting for processing...")
                
                # Wait for video to upload and process
                time.sleep(15)
                
                # Add caption/description
                caption_selectors = [
                    "[data-contents='true']",
                    "div[contenteditable='true']",
                    ".notranslate[contenteditable='true']",
                    "div[role='textbox']"
                ]
                
                caption_field = None
                for selector in caption_selectors:
                    try:
                        caption_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if caption_field:
                    caption_text = f"{metadata['description']} {' '.join(metadata['hashtags'])}"
                    caption_field.clear()
                    caption_field.send_keys(caption_text)
                    logger.info("Caption added")
                else:
                    logger.warning("Could not find caption field")
                
                # Look for and click Post button
                time.sleep(3)
                post_button_selectors = [
                    "//div[contains(text(), 'Post')]",
                    "//button[contains(text(), 'Post')]",
                    "//div[contains(text(), 'Publish')]",
                    "//button[contains(text(), 'Publish')]"
                ]
                
                post_button = None
                for selector in post_button_selectors:
                    try:
                        post_button = driver.find_element(By.XPATH, selector)
                        if post_button.is_enabled():
                            break
                    except:
                        continue
                
                if post_button and post_button.is_enabled():
                    post_button.click()
                    logger.info("Post button clicked")
                    
                    # Wait for confirmation
                    time.sleep(10)
                    
                    logger.info(f"Successfully uploaded video: {metadata['title']}")
                    return True
                else:
                    logger.error("Could not find or click Post button")
                    return False
                
            except Exception as e:
                logger.error(f"Error during upload process: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading to TikTok: {str(e)}")
            return False
        finally:
            if driver:
                driver.quit() 