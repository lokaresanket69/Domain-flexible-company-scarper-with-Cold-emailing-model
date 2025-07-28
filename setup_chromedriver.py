#!/usr/bin/env python3
import os
import sys
import logging
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

def setup_chromedriver():
    """Set up ChromeDriver with appropriate settings for Render."""
    try:
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Set Chrome options
        options = webdriver.ChromeOptions()
        
        # Headless configuration
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--window-size=1920,1080')
        
        # Set up ChromeDriver
        try:
            # Try to use the system Chrome first
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("Successfully set up ChromeDriver with Chrome")
            return driver
        except Exception as e:
            logger.warning(f"Failed to set up Chrome, trying Chromium: {e}")
            try:
                # Fall back to Chromium
                service = ChromeService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                driver = webdriver.Chrome(service=service, options=options)
                logger.info("Successfully set up ChromeDriver with Chromium")
                return driver
            except Exception as e:
                logger.error(f"Failed to set up ChromeDriver with Chromium: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to set up ChromeDriver: {e}")
        sys.exit(1)

if __name__ == "__main__":
    driver = setup_chromedriver()
    if driver:
        print("ChromeDriver set up successfully!")
        driver.quit()
