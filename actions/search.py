from actions.browser import BrowserController
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class SearchController:
    def __init__(self, browser_controller: BrowserController):
        self.browser = browser_controller

    def search(self, query, platform="google"):
        """
        Searches for a query on a given platform.
        """
        self.browser.open_url(platform)
        time.sleep(2)  # Wait for page to load

        if platform == "google":
            search_box = self.browser.find_element(By.NAME, "q")
        elif platform == "youtube":
            search_box = self.browser.find_element(By.NAME, "search_query")
        else:
            print(f"Platform {platform} not supported for search.")
            return

        if search_box:
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

    def search_and_play(self, query):
        """
        Searches for a query on YouTube and plays the first video.
        """
        self.search(query, platform="youtube")
        time.sleep(3)  # Wait for search results

        # Click the first video
        first_video = self.browser.find_element(By.ID, "video-title")
        if first_video:
            self.browser.click_element(first_video)

if __name__ == '__main__':
    browser = BrowserController()
    browser.start()
    search = SearchController(browser)
    search.search_and_play("lofi hip hop radio")
    input("YouTube should be playing a video. Press Enter to close...")
    browser.close()
