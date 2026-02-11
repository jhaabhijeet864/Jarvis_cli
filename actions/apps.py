import subprocess
import pyautogui
import platform
import os
import logging

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

# This would be in config.py
APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": "chrome.exe",
    "vscode": "code.exe",
}

class AppLauncher:
    def open(self, app_name):
        """
        Opens an application.
        """
        app_name = app_name.lower()
        main_logger.info(f"Attempting to open application: '{app_name}'")

        if platform.system() == "Windows":
            if app_name in APP_PATHS:
                try:
                    main_logger.debug(f"Opening '{app_name}' using direct path: {APP_PATHS[app_name]}")
                    subprocess.Popen([APP_PATHS[app_name]])
                    return True
                except FileNotFoundError:
                    error_logger.warning(f"File not found for '{app_name}' at path '{APP_PATHS[app_name]}'. Falling back to pyautogui.")
                    return self._open_with_pyautogui(app_name)
            else:
                main_logger.info(f"'{app_name}' not in predefined paths. Attempting to open with pyautogui.")
                return self._open_with_pyautogui(app_name)
        else:
            # For other OS, you might need different logic
            main_logger.info(f"Opening '{app_name}' on non-Windows OS.")
            try:
                subprocess.Popen([app_name])
                return True
            except FileNotFoundError:
                error_logger.error(f"Could not find application '{app_name}' on this system.")
                return False

    def _open_with_pyautogui(self, app_name):
        """
        Fallback to open an application using pyautogui.
        This simulates pressing the Windows key, typing the app name, and pressing Enter.
        """
        main_logger.info(f"Using pyautogui fallback to open '{app_name}'.")
        try:
            pyautogui.press("win")
            pyautogui.sleep(0.5) # Wait for start menu
            pyautogui.write(app_name, interval=0.05)
            pyautogui.sleep(0.5) # Wait for search results
            pyautogui.press("enter")
            main_logger.info(f"Successfully sent commands to open '{app_name}' via pyautogui.")
            return True
        except Exception as e:
            error_logger.exception(f"An error occurred while trying to open '{app_name}' with pyautogui.")
            return False
