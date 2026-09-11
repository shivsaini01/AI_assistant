import json
import os

from jarvis_tools import launch_app, open_url


# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = r"C:\AI_Assistant"

SKILLS_FOLDER = os.path.join(
    BASE_DIR,
    "skills"
)

CREATE_FOLDER = SKILLS_FOLDER

REGISTRY_FILE = os.path.join(
    BASE_DIR,
    "skills.json"
)


# ==================================================
# FOLDER SETUP
# ==================================================

def ensure_folders():

    os.makedirs(
        SKILLS_FOLDER,
        exist_ok=True
    )


# ==================================================
# SKILL REGISTRY
# ==================================================

def load_registry():

    ensure_folders()

    if not os.path.exists(REGISTRY_FILE):
        return {}

    try:

        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except Exception as e:

        print(f"Registry error: {e}")

    return {}


def save_registry(registry):

    ensure_folders()

    try:

        with open(
            REGISTRY_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                registry,
                file,
                indent=4
            )

        return True

    except Exception as e:

        print(f"Failed to save registry: {e}")

        return False


# ==================================================
# CLEAN FILENAME
# ==================================================

def clean_filename(filename):

    if not filename:
        return None

    filename = os.path.basename(
        str(filename)
    ).strip()

    if not filename:
        return None

    if ".." in filename:
        return None

    return filename


# ==================================================
# CREATE FILE
# ==================================================

def create_file(filename, content):

    ensure_folders()

    filename = clean_filename(filename)

    if not filename:
        return False, "Invalid filename."

    file_path = os.path.join(
        CREATE_FOLDER,
        filename
    )

    try:

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(content)

        return True, file_path

    except Exception as e:

        return False, f"Failed to create file: {e}"


# ==================================================
# GET SKILL PATH
# ==================================================

def get_skill_path(filename):

    filename = clean_filename(filename)

    if not filename:
        return None

    if not filename.lower().endswith(".py"):
        filename += ".py"

    return os.path.join(
        SKILLS_FOLDER,
        filename
    )


# ==================================================
# REGISTER SKILL
# ==================================================

def register_skill(
    skill_name,
    filename,
    triggers=None,
    description=""
):

    ensure_folders()

    if triggers is None:
        triggers = []

    filename = clean_filename(filename)

    if not filename:
        return False

    if not filename.lower().endswith(".py"):
        filename += ".py"

    registry = load_registry()

    registry[skill_name] = {
        "filename": filename,
        "triggers": triggers,
        "description": description
    }

    return save_registry(registry)


# ==================================================
# FIND SKILL
# ==================================================

def find_skill(text):

    if not text:
        return None

    text_lower = text.lower().strip()

    registry = load_registry()

    for skill_name, skill_data in registry.items():

        # Check skill name
        if skill_name.lower() == text_lower:
            return skill_data

        # Check filename
        filename = skill_data.get(
            "filename",
            ""
        )

        filename_without_ext = os.path.splitext(
            filename
        )[0].lower()

        if filename_without_ext == text_lower:
            return skill_data

        # Check triggers
        triggers = skill_data.get(
            "triggers",
            []
        )

        for trigger in triggers:

            if trigger.lower() in text_lower:
                return skill_data

    return None


# ==================================================
# RUN SKILL
# ==================================================

def run_skill(skill_name):

    skill = find_skill(skill_name)

    if not skill:

        print(
            f"Skill not found: {skill_name}"
        )

        return False

    filename = skill.get(
        "filename"
    )

    skill_path = get_skill_path(
        filename
    )

    if not skill_path:

        print("Invalid skill path.")

        return False

    if not os.path.exists(skill_path):

        print(
            f"Skill file not found: {filename}"
        )

        return False

    try:

        # Import and execute the registered
        # Python skill.
        import subprocess

        result = subprocess.run(
            [
                "python",
                skill_path
            ],
            cwd=SKILLS_FOLDER,
            capture_output=True,
            text=True
        )

        if result.stdout:
            print(result.stdout.strip())

        if result.stderr:
            print(result.stderr.strip())

        if result.returncode == 0:
            return True

        return False

    except Exception as e:

        print(
            f"Failed to run skill: {e}"
        )

        return False


# ==================================================
# EXECUTE APPROVED COMMAND
# ==================================================

def execute_command(command):

    if not command:
        return False

    command = command.strip()

    # ----------------------------------------------
    # OPEN BRAVE
    # ----------------------------------------------

    if command == "open_brave":

        success, message = launch_app(
            "brave"
        )

        print(message)

        return success

    # ----------------------------------------------
    # OPEN OBS
    # ----------------------------------------------

    if command == "open_obs":

        success, message = launch_app(
            "obs"
        )

        print(message)

        return success

    # ----------------------------------------------
    # OPEN URL
    # ----------------------------------------------

    if command.startswith("open_url:"):

        url = command[
            len("open_url:"):
        ].strip()

        if not url:

            print("URL is empty.")

            return False

        success, message = open_url(
            url
        )

        print(message)

        return success

    # ----------------------------------------------
    # REGISTERED SKILL
    # ----------------------------------------------

    skill = find_skill(command)

    if skill:

        return run_skill(command)

    # ----------------------------------------------
    # UNKNOWN COMMAND
    # ----------------------------------------------

    print(
        f"Unknown command: {command}"
    )

    return False


# ==================================================
# LIST SKILLS
# ==================================================

def list_skills():

    registry = load_registry()

    if not registry:

        print("No skills registered.")

        return []

    for name, data in registry.items():

        print(
            f"- {name}: "
            f"{data.get('filename', '')}"
        )

    return registry


# ==================================================
# REMOVE SKILL
# ==================================================

def remove_skill(skill_name):

    registry = load_registry()

    skill = find_skill(
        skill_name
    )

    if not skill:

        print(
            f"Skill not found: {skill_name}"
        )

        return False

    skill_to_remove = None

    for name, data in registry.items():

        if data == skill:
            skill_to_remove = name
            break

    if not skill_to_remove:
        return False

    filename = skill.get(
        "filename"
    )

    skill_path = get_skill_path(
        filename
    )

    # Remove registry entry
    del registry[skill_to_remove]

    save_registry(registry)

    # Remove Python file
    if skill_path and os.path.exists(skill_path):

        try:

            os.remove(skill_path)

        except Exception as e:

            print(
                f"Could not delete skill file: {e}"
            )

    print(
        f"Removed skill: {skill_to_remove}"
    )

    return True


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("JARVIS COMMANDS TEST")
    print("=" * 50)

    print()

    print("Testing OBS...")

    execute_command(
        "open_obs"
    )

    print()

    print("Testing Brave...")

    execute_command(
        "open_brave"
    )

    print()

    print("Testing YouTube...")

    execute_command(
        "open_url:https://www.youtube.com"
    )

    print()

    print("=" * 50)
