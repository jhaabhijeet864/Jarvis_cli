from actions.apps import AppLauncher
from actions.browser import BrowserController
from actions.search import SearchController
from actions.media import MediaController
import time

# Test app launcher
launcher = AppLauncher()
print("Opening Notepad...")
launcher.open("notepad")
input("Notepad should be open. Press Enter to continue tests...")

# Test browser
browser = BrowserController()
print("Starting browser...")
browser.start()
time.sleep(2) # Give browser time to open
print("Browser started.")

# Test search
print("Opening YouTube and searching for 'lofi music'...")
search = SearchController(browser)
search.search("lofi music", platform="youtube")
input("Search results for 'lofi music' should show. Press Enter to continue tests...")

# Test media
print("Searching for 'never gonna give you up' on YouTube and testing media controls...")
search.search_and_play("never gonna give you up")
time.sleep(5) # Let the video load

media = MediaController(browser)

input("Video should be playing. Press Enter to pause...")
media.pause()

input("Video should be paused. Press Enter to play...")
media.play()

input("Video should be playing. Press Enter to toggle (pause)...")
media.toggle()

input("Video should be paused. Press Enter to close browser...")
browser.close()
print("Browser closed.")

print("All STREAM 2 tests completed successfully!")