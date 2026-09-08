import subprocess
import os

OBS = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
OBS_DIR = r"C:\Program Files\obs-studio\bin\64bit"

BRAVE = r"C:\Users\shivp\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"

# Folder where Jarvis is allowed to create files
CREATE_FOLDER = r"C:\AI_Assistant\test_prompt"


def open_obs():
    subprocess.Popen([OBS], cwd=OBS_DIR)
    print("OBS opened.")
    return True


def open_brave():
    subprocess.Popen([BRAVE])
    print("Brave opened.")
    return True


def create_file(filename, content):
    """
    Create a file only inside CREATE_FOLDER.
    """

    # Remove accidental quotes/spaces
    filename = filename.strip().strip('"').strip("'")

    # Prevent paths such as ../file.py or C:\something\file.py
    filename = os.path.basename(filename)

    if not filename:
        print("Error: filename is empty.")
        return False

    os.makedirs(CREATE_FOLDER, exist_ok=True)

    file_path = os.path.join(CREATE_FOLDER, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        print(f"File created: {file_path}")
        return True

    except Exception as e:
        print(f"Error creating file: {e}")
        return False


def execute_command(command):
    """
    Handles simple direct commands.

    Tool-style file creation will be handled by assistant.py.
    """

    command = command.lower().strip()

    if "open obs" in command:
        return open_obs()

    if "open brave" in command:
        return open_brave()

    return False