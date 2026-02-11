from actions.browser import BrowserController
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import time
import logging

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

class SearchController:
    def __init__(self, browser_controller: BrowserController):
        self.browser = browser_controller
        main_logger.info("SearchController initialized.")

    def search(self, query: str, platform: str = "google"):
        """
        Searches for a query on a given platform.
        """
        main_logger.info(f"Initiating search for '{query}' on '{platform}'.")
        try:
            self.browser.open_url(platform)
            time.sleep(2)  # Wait for page to load

            search_box = None
            if platform == "google":
                search_box = self.browser.find_element(By.NAME, "q")
            elif platform == "youtube":
                search_box = self.browser.find_element(By.NAME, "search_query")
            else:
                main_logger.warning(f"Search platform '{platform}' not explicitly supported. Attempting generic search.")
                # Fallback: try to find a generic search box
                try:
                    search_box = self.browser.find_element(By.CSS_SELECTOR, "input[type='search'], input[name*='q'], input[id*='search']")
                except NoSuchElementException:
                    error_logger.error(f"Could not find a search box on '{platform}' for query '{query}'.")
                    return False

            if search_box:
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                main_logger.info(f"Successfully performed search for '{query}' on '{platform}'.")
                return True
            else:
                error_logger.error(f"Search box not found on '{platform}' for query '{query}'.")
                return False
        except WebDriverException as e:
            error_logger.exception(f"WebDriver error during search for '{query}' on '{platform}'.")
            return False
        except Exception as e:
            error_logger.exception(f"An unexpected error occurred during search for '{query}' on '{platform}'.")
            return False

    def search_and_play(self, query: str):
        """
        Searches for a query on YouTube and plays the first video.
        """
        main_logger.info(f"Searching and attempting to play '{query}' on YouTube.")
        try:
            if not self.search(query, platform="youtube"):
                error_logger.warning(f"Failed to search YouTube for '{query}'. Cannot proceed to play.")
                return False
            
            time.sleep(3)  # Wait for search results to load

            # Click the first video
            first_video = self.browser.find_element(By.ID, "video-title")
            if first_video:
                self.browser.click_element(first_video)
                main_logger.info(f"Successfully clicked and attempting to play '{query}' on YouTube.")
                return True
            else:
                error_logger.warning(f"Could not find a video to play for query '{query}' on YouTube.")
                return False
        except WebDriverException as e:
            error_logger.exception(f"WebDriver error during search and play for '{query}' on YouTube.")
            return False
        except Exception as e:
            error_logger.exception(f"An unexpected error occurred during search and play for '{query}' on YouTube.")
            return False
