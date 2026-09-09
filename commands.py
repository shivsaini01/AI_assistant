import json
import os
import subprocess
import sys

from jarvis_tools import launch_app, open_url


# ==================================================
# PATHS
# ==================================================

BASE_DIR = r"C:\AI_Assistant"

# All generated skills are stored directly here.
SKILLS_FOLDER = os.path.join(BASE_DIR, "skills")

# Skills use this folder for creation and execution.
CREATE_FOLDER = SKILLS_FOLDER

# Skill registry
REGISTRY_FILE = os.path.join(BASE_DIR, "skills.json")


# ==================================================
# FOLDER SETUP
# ==================================================

def ensure_folders():
    """Create required folders if they don't exist."""

    os.makedirs(SKILLS_FOLDER, exist_ok=True)


ensure_folders()


# ==================================================
# SKILL REGISTRY
# ==================================================

def load_registry():
    """Load the skill registry."""

    if not os.path.exists(REGISTRY_FILE):
        return {}

    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_registry(registry):
    """Save the skill registry."""

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)


# ==================================================
# FILE CREATION
# ==================================================

def clean_filename(filename):
    """Clean and validate a filename."""

    filename = os.path.basename(filename).strip()

    if not filename:
        return None

    if ".." in filename:
        return None

    return filename


def create_file(filename, content):
    """
    Create a file directly inside the skills folder.
    """

    ensure_folders()

    filename = clean_filename(filename)

    if not filename:
        return False, "Invalid filename."

    file_path = os.path.abspath(
        os.path.join(CREATE_FOLDER, filename)
    )

    # Security check: make sure the file stays inside skills folder.
    skills_root = os.path.abspath(CREATE_FOLDER)

    if not file_path.startswith(skills_root + os.sep):
        return False, "File creation outside the skills folder is not allowed."

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, file_path

    except OSError as e:
        return False, f"Failed to create file: {e}"


# ==================================================
# SKILL PATH
# ==================================================

def get_skill_path(filename):
    """Return the full path of a skill inside the skills folder."""

    filename = clean_filename(filename)

    if not filename:
        return None

    skill_path = os.path.abspath(
        os.path.join(CREATE_FOLDER, filename)
    )

    skills_root = os.path.abspath(CREATE_FOLDER)

    if not skill_path.startswith(skills_root + os.sep):
        return None

    if not skill_path.lower().endswith(".py"):
        return None

    return skill_path


# ==================================================
# REGISTER SKILL
# ==================================================

def register_skill(
    skill_name,
    filename,
    triggers=None,
    description=""
):
    """Register a generated skill in skills.json."""

    registry = load_registry()

    if triggers is None:
        triggers = []

    registry[skill_name.lower()] = {
        "name": skill_name,
        "filename": filename,
        "triggers": triggers,
        "description": description
    }

    save_registry(registry)

    return True


# ==================================================
# FIND SKILL
# ==================================================

def find_skill(text):
    """
    Find a registered skill based on:
    - skill name
    - filename
    - trigger
    - natural language trigger
    """

    registry = load_registry()

    text_lower = text.lower().strip()

    # Exact skill name
    if text_lower in registry:
        return registry[text_lower]

    for skill_name, skill_data in registry.items():

        filename = skill_data.get("filename", "").lower()
        name = skill_data.get("name", "").lower()

        # Exact filename
        if text_lower == filename:
            return skill_data

        # Filename without .py
        if text_lower == filename.replace(".py", ""):
            return skill_data

        # Exact name
        if text_lower == name:
            return skill_data

        # Triggers
        for trigger in skill_data.get("triggers", []):
            trigger_lower = trigger.lower().strip()

            if text_lower == trigger_lower:
                return skill_data

            if trigger_lower and trigger_lower in text_lower:
                return skill_data

    return None


# ==================================================
# RUN SKILL
# ==================================================

def run_skill(skill):
    """
    Run a registered Python skill.

    Only registered .py files inside the skills folder
    are allowed to run.
    """

    if isinstance(skill, str):
        skill = find_skill(skill)

    if not skill:
        return False, "Skill not found."

    filename = skill.get("filename")

    if not filename:
        return False, "Skill filename is missing."

    script_path = get_skill_path(filename)

    if not script_path:
        return False, "Invalid skill path."

    if not os.path.exists(script_path):
        return False, f"Skill file not found: {filename}"

    try:
        subprocess.Popen(
            [
                sys.executable,
                script_path
            ],
            cwd=CREATE_FOLDER,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

        return True, f"Started skill: {skill.get('name', filename)}"

    except Exception as e:
        return False, f"Failed to run skill: {e}"


# ==================================================
# EXECUTE COMMAND
# ==================================================

def execute_command(command):
    """
    Execute an approved Jarvis command or registered skill.

    Supported built-in commands:
        open_brave
        open_obs
        open_url

    Registered skills are handled separately.
    """

    command_lower = command.lower().strip()

    # ----------------------------------------------
    # APPROVED APPLICATIONS
    # ----------------------------------------------

    if command_lower == "open_brave":
        success, message = launch_app("brave")
        print(message)
        return success

    if command_lower == "open_obs":
        success, message = launch_app("obs")
        print(message)
        return success

    # ----------------------------------------------
    # URL
    # ----------------------------------------------

    if command_lower.startswith("open_url:"):
        url = command.split(":", 1)[1].strip()

        if not url:
            print("URL is missing.")
            return False

        success, message = open_url(url)
        print(message)
        return success

    # ----------------------------------------------
    # REGISTERED SKILL
    # ----------------------------------------------

    skill = find_skill(command)

    if skill:
        success, message = run_skill(skill)
        print(message)
        return success

    print(f"Unknown command: {command}")
    return False


# ==================================================
# LIST SKILLS
# ==================================================

def list_skills():
    """Display all registered skills."""

    registry = load_registry()

    if not registry:
        print("No skills registered.")
        return

    print("\nRegistered Skills:")
    print("-" * 40)

    for skill_name, skill in registry.items():

        print(f"Name: {skill.get('name', skill_name)}")
        print(f"File: {skill.get('filename', '')}")
        print(f"Triggers: {', '.join(skill.get('triggers', []))}")

        description = skill.get("description", "")

        if description:
            print(f"Description: {description}")

        print("-" * 40)


# ==================================================
# REMOVE SKILL
# ==================================================

def remove_skill(skill_name):
    """Remove a skill from the registry and delete its file."""

    registry = load_registry()

    skill = registry.get(skill_name.lower())

    if not skill:
        return False, "Skill not found."

    filename = skill.get("filename")
    skill_path = get_skill_path(filename)

    # Remove the Python file
    if skill_path and os.path.exists(skill_path):

        try:
            os.remove(skill_path)

        except OSError as e:
            return False, f"Failed to remove skill file: {e}"

    # Remove from registry
    del registry[skill_name.lower()]
    save_registry(registry)

    return True, f"Removed skill: {skill_name}"


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("JARVIS COMMANDS TEST")
    print("=" * 50)

    print("\nTesting OBS...")
    execute_command("open_obs")

    print("\nTesting Brave...")
    execute_command("open_brave")

    print("=" * 50)