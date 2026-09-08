import subprocess

OBS = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
OBS_DIR = r"C:\Program Files\obs-studio\bin\64bit"

BRAVE = r"C:\Users\shivp\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"


def open_obs():
    subprocess.Popen([OBS], cwd=OBS_DIR)
    print("OBS opened.")


def open_brave():
    subprocess.Popen([BRAVE])
    print("Brave opened.")


def execute_command(command):
    command = command.lower().strip()

    if "open obs" in command:
        open_obs()
        return True

    if "open brave" in command:
        open_brave()
        return True

    return False
