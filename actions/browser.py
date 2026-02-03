from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# This would be in config.py
URLS = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
}

class BrowserController:
    def __init__(self):
        self.driver = None

    def start(self):
        """
        Starts the browser.
        """
        if not self.driver:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    def open_url(self, name_or_url):
        """
        Opens a URL in the browser.
        """
        if not self.driver:
            self.start()

        url = URLS.get(name_or_url.lower(), name_or_url)
        self.driver.get(url)

    def find_element(self, by, value):
        """
        Finds an element on the page.
        """
        if self.driver:
            return self.driver.find_element(by, value)
        return None

    def click_element(self, element):
        """
        Clicks an element.
        """
        if element:
            element.click()

    def execute_script(self, script):
        """
        Executes JavaScript in the browser.
        """
        if self.driver:
            return self.driver.execute_script(script)
        return None

    def close(self):
        """
        Closes the browser.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None

if __name__ == '__main__':
    browser = BrowserController()
    browser.start()
    browser.open_url("google")
    input("Google should be open. Press Enter to close...")
    browser.close()
