import os
import subprocess
import webbrowser

from app_detector import find_app


# ==================================================
# JARVIS SAFE TOOLS
# ==================================================

def launch_app(app_name):
    """
    Launch an approved application using app_detector.py.
    """

    path = find_app(app_name)

    if not path:
        return False, f"Application not found: {app_name}"

    try:
        # Use the application's folder as the working directory.
        # This is important for applications like OBS that
        # need to locate files such as en-US.ini.
        working_dir = os.path.dirname(path)

        subprocess.Popen(
            [path],
            cwd=working_dir,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

        return True, f"Started {app_name}"

    except Exception as e:
        return False, f"Failed to start {app_name}: {e}"


def open_url(url):
    """
    Open a URL in the default browser.
    """

    try:
        webbrowser.open(url)
        return True, f"Opened {url}"

    except Exception as e:
        return False, f"Failed to open URL: {e}"


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("JARVIS TOOLS TEST")
    print("=" * 50)

    # Test OBS
    success, message = launch_app("obs")
    print(message)

    # Test Brave
    success, message = launch_app("brave")
    print(message)

    # Test URL
    success, message = open_url("https://www.youtube.com")
    print(message)

    print("=" * 50)