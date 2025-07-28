#!/usr/bin/env python3
import os
import sys
import logging
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return None

def check_chrome_installation():
    """Check if Chrome is installed and return its version."""
    # Check common Chrome binary locations
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser"
    ]
    
    installed_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            installed_path = path
            break
    
    if not installed_path:
        return False, "Chrome/Chromium not found in standard locations"
    
    # Try to get version
    try:
        version = run_command(f"{installed_path} --version")
        return True, f"Found at {installed_path}: {version}"
    except Exception as e:
        return False, f"Error getting Chrome version: {str(e)}"

def check_chromedriver_installation():
    """Check if ChromeDriver is installed and return its version."""
    # Check common ChromeDriver locations
    chromedriver_paths = [
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/lib/chromium-browser/chromedriver"
    ]
    
    installed_path = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            installed_path = path
            break
    
    if not installed_path:
        return False, "ChromeDriver not found in standard locations"
    
    # Try to get version
    try:
        version = run_command(f"{installed_path} --version")
        return True, f"Found at {installed_path}: {version}"
    except Exception as e:
        return False, f"Error getting ChromeDriver version: {str(e)}"

def check_selenium():
    """Check if Selenium can initialize a WebDriver."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Try with Chrome first
        try:
            service = ChromeService(executable_path="/usr/local/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            driver.quit()
            return True, "Successfully initialized Chrome WebDriver"
        except Exception as e:
            return False, f"Failed to initialize Chrome WebDriver: {str(e)}"
            
    except ImportError:
        return False, "Selenium is not installed"
    except Exception as e:
        return False, f"Error checking Selenium: {str(e)}"

def check_environment():
    """Check the environment variables and system configuration."""
    logger.info("=== Environment Check ===")
    
    # Check environment variables
    env_vars = [
        'CHROME_BIN', 'CHROMEDRIVER_PATH', 'DISPLAY', 
        'GOOGLE_CHROME_SHIM', 'PATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        logger.info(f"{var}: {value}")
    
    # Check Chrome installation
    chrome_ok, chrome_msg = check_chrome_installation()
    logger.info(f"Chrome check: {'OK' if chrome_ok else 'FAILED'}")
    logger.info(f"Chrome details: {chrome_msg}")
    
    # Check ChromeDriver installation
    chromedriver_ok, chromedriver_msg = check_chromedriver_installation()
    logger.info(f"ChromeDriver check: {'OK' if chromedriver_ok else 'FAILED'}")
    logger.info(f"ChromeDriver details: {chromedriver_msg}")
    
    # Check Selenium
    selenium_ok, selenium_msg = check_selenium()
    logger.info(f"Selenium check: {'OK' if selenium_ok else 'FAILED'}")
    logger.info(f"Selenium details: {selenium_msg}")
    
    # Check directory structure
    logger.info("\n=== Directory Structure ===")
    for root, dirs, files in os.walk('.'):
        level = root.replace(os.path.sep, '/').count('/')
        indent = ' ' * 4 * level
        logger.info(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logger.info(f"{subindent}{f}")
    
    return all([chrome_ok, chromedriver_ok, selenium_ok])

if __name__ == "__main__":
    logger.info("Starting Chrome environment check...")
    success = check_environment()
    
    if success:
        logger.info("\n✅ All checks passed! Your environment is ready for Selenium.")
        sys.exit(0)
    else:
        logger.error("\n❌ Some checks failed. Please review the logs above.")
        sys.exit(1)
