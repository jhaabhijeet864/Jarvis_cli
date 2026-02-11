from actions.browser import BrowserController
import logging

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

class MediaController:
    def __init__(self, browser_controller: BrowserController):
        self.browser = browser_controller
        main_logger.info("MediaController initialized.")

    def _execute_video_script(self, script: str):
        """
        Executes a script on the current video element.
        """
        if not self.browser or not self.browser.driver:
            error_logger.warning("Browser not active. Cannot execute video script.")
            return None
        
        full_script = f"document.querySelector('video').{script};"
        main_logger.debug(f"Executing video script: {full_script}")
        try:
            return self.browser.execute_script(full_script)
        except Exception as e:
            error_logger.exception(f"Error executing video script: {script}")
            return None

    def play(self):
        """
        Plays the video.
        """
        main_logger.info("Attempting to play media.")
        self._execute_video_script("play()")

    def pause(self):
        """
        Pauses the video.
        """
        main_logger.info("Attempting to pause media.")
        self._execute_video_script("pause()")

    def toggle(self):
        """
        Toggles play/pause on the video.
        """
        main_logger.info("Attempting to toggle media play/pause.")
        is_paused = self._execute_video_script("return document.querySelector('video').paused;")
        if is_paused is not None: # Ensure script execution was successful
            if is_paused:
                self.play()
                main_logger.info("Media toggled to play.")
            else:
                self.pause()
                main_logger.info("Media toggled to pause.")
        else:
            error_logger.warning("Could not determine media state to toggle.")
