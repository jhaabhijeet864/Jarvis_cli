from actions.browser import BrowserController

class MediaController:
    def __init__(self, browser_controller: BrowserController):
        self.browser = browser_controller

    def _execute_video_script(self, script):
        """
        Executes a script on the current video element.
        """
        full_script = f"document.querySelector('video').{script};"
        return self.browser.execute_script(full_script)

    def play(self):
        """
        Plays the video.
        """
        self._execute_video_script("play()")

    def pause(self):
        """
        Pauses the video.
        """
        self._execute_video_script("pause()")

    def toggle(self):
        """
        Toggles play/pause on the video.
        """
        is_paused = self.browser.execute_script("return document.querySelector('video').paused;")
        if is_paused:
            self.play()
        else:
            self.pause()

if __name__ == '__main__':
    from actions.search import SearchController
    import time

    browser = BrowserController()
    browser.start()
    search = SearchController(browser)
    search.search_and_play("never gonna give you up")
    time.sleep(5) # Let the video load

    media = MediaController(browser)

    input("Video should be playing. Press Enter to pause...")
    media.pause()

    input("Video should be paused. Press Enter to play...")
    media.play()

    input("Video should be playing. Press Enter to toggle (pause)...")
    media.toggle()

    input("Video should be paused. Press Enter to close...")
    browser.close()
