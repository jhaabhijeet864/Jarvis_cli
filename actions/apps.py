import subprocess
import pyautogui
import platform
import os

# This would be in config.py
APP_PATHS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
}

class AppLauncher:
    def open(self, app_name):
        """
        Opens an application.
        """
        app_name = app_name.lower()
        if platform.system() == "Windows":
            if app_name in APP_PATHS:
                try:
                    subprocess.Popen([APP_PATHS[app_name]])
                    return True
                except FileNotFoundError:
                    return self._open_with_pyautogui(app_name)
            else:
                return self._open_with_pyautogui(app_name)
        else:
            # For other OS, you might need different logic
            try:
                subprocess.Popen([app_name])
                return True
            except FileNotFoundError:
                return False

    def _open_with_pyautogui(self, app_name):
        """
        Fallback to open an application using pyautogui.
        """
        try:
            pyautogui.press("win")
            pyautogui.sleep(1)
            pyautogui.write(app_name)
            pyautogui.sleep(1)
            pyautogui.press("enter")
            return True
        except Exception as e:
            print(f"Error opening with pyautogui: {e}")
            return False

if __name__ == '__main__':
    launcher = AppLauncher()
    launcher.open("notepad")
