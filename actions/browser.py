from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

# This would be in config.py
URLS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "stackoverflow": "https://stackoverflow.com",
}

class BrowserController:
    def __init__(self):
        self.driver: webdriver.Chrome = None
        main_logger.info("BrowserController initialized.")

    def start(self):
        """
        Starts the Chrome browser if it's not already running.
        """
        if self.driver:
            main_logger.info("Browser is already running.")
            return

        main_logger.info("Starting browser...")
        try:
            # Using webdriver_manager to automatically handle chromedriver
            driver_path = ChromeDriverManager().install()
            service = Service(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service)
            main_logger.info("Browser started successfully.")
        except ValueError as e:
            error_logger.critical(f"There was an issue installing or starting ChromeDriver: {e}", exc_info=True)
            error_logger.critical("Please ensure you have a stable internet connection and that Chrome is installed.")
            raise
        except WebDriverException as e:
            error_logger.critical(f"WebDriver error: {e}", exc_info=True)
            error_logger.critical("This may be due to a mismatch between your Chrome browser and ChromeDriver.")
            raise

    def open_url(self, name_or_url: str):
        """
        Opens a URL in the browser. Starts the browser if it's not running.
        """
        if not self.driver:
            main_logger.info("Browser not running. Starting it now to open URL.")
            self.start()
        
        # If start() fails, self.driver will still be None
        if not self.driver:
            error_logger.error("Cannot open URL because browser failed to start.")
            return False

        url = URLS.get(name_or_url.lower(), name_or_url)
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        main_logger.info(f"Navigating to URL: {url}")
        try:
            self.driver.get(url)
            return True
        except WebDriverException as e:
            error_logger.error(f"Failed to navigate to URL: {url}", exc_info=True)
            return False

    def find_element(self, by, value):
        """
        Finds an element on the page.
        """
        if not self.driver:
            error_logger.warning("Attempted to find element, but browser is not running.")
            return None
        try:
            return self.driver.find_element(by, value)
        except WebDriverException as e:
            error_logger.warning(f"Could not find element with selector '{by}={value}'.", exc_info=True)
            return None

    def click_element(self, element):
        """
        Clicks an element.
        """
        if not element:
            error_logger.warning("Attempted to click a null element.")
            return
        
        try:
            main_logger.debug(f"Clicking element: {element.tag_name} ({element.text[:30]}...)")
            element.click()
        except WebDriverException as e:
            error_logger.warning("Failed to click element.", exc_info=True)

    def execute_script(self, script: str):
        """
        Executes JavaScript in the browser.
        """
        if not self.driver:
            error_logger.warning("Attempted to execute script, but browser is not running.")
            return None
        
        main_logger.debug(f"Executing script: {script[:100]}...")
        try:
            return self.driver.execute_script(script)
        except WebDriverException as e:
            error_logger.error("Failed to execute JavaScript.", exc_info=True)
            return None

    def close(self):
        """
        Closes the browser window and quits the driver service.
        """
        if self.driver:
            main_logger.info("Closing browser.")
            try:
                self.driver.quit()
            except Exception as e:
                # This can sometimes happen if the browser was closed manually
                error_logger.warning("Error while quitting the browser, it might have been closed already.", exc_info=True)
            finally:
                self.driver = None
                main_logger.info("Browser closed and driver reset.")
        else:
            main_logger.info("Browser was not running, no need to close.")
