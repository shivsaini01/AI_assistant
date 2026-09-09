import json
import os
import subprocess
import sys


# =========================================================
# FOLDERS
# =========================================================

BASE_DIR = r"C:\AI_Assistant"

SKILLS_FOLDER = os.path.join(
    BASE_DIR,
    "skills"
)

CREATE_FOLDER = os.path.join(
    SKILLS_FOLDER,
    "test_prompt"
)

REGISTRY_FILE = os.path.join(
    BASE_DIR,
    "skills.json"
)


# =========================================================
# SETUP
# =========================================================

def ensure_folders():
    os.makedirs(SKILLS_FOLDER, exist_ok=True)
    os.makedirs(CREATE_FOLDER, exist_ok=True)


ensure_folders()


# =========================================================
# REGISTRY
# =========================================================

def load_registry():
    if not os.path.isfile(REGISTRY_FILE):
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
        print(
            f"Warning: couldn't read skills registry: {e}"
        )

    return {}


def save_registry(registry):
    try:
        with open(
            REGISTRY_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                registry,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception as e:
        print(
            f"Error saving skills registry: {e}"
        )

        return False


# =========================================================
# SAFE FILENAME
# =========================================================

def clean_filename(filename):
    if not isinstance(filename, str):
        return None

    filename = filename.strip()
    filename = filename.strip('"')
    filename = filename.strip("'")

    # Keep only the filename.
    filename = os.path.basename(filename)

    if not filename:
        return None

    if filename in {".", ".."}:
        return None

    # Prevent path traversal.
    if ".." in filename:
        return None

    return filename


# =========================================================
# CREATE / REPLACE FILE
# =========================================================

def create_file(filename, content):
    """
    Create or replace a file inside:

        C:\\AI_Assistant\\skills\\test_prompt

    If the same filename already exists, its contents
    are replaced with the new contents.

    This is intentional.

    Example:

        yt.py
        delete yt.py
        create another yt.py

    The new yt.py becomes the active script.
    """

    filename = clean_filename(filename)

    if not filename:
        print("Error: invalid filename.")
        return False

    try:
        os.makedirs(
            CREATE_FOLDER,
            exist_ok=True
        )

        file_path = os.path.join(
            CREATE_FOLDER,
            filename
        )

        # "w" means:
        #
        #   file doesn't exist -> create it
        #   file exists        -> replace contents
        #
        with open(
            file_path,
            "w",
            encoding="utf-8",
            newline="\n"
        ) as file:
            file.write(str(content))

        print(
            f"File created: {file_path}"
        )

        return True

    except Exception as e:
        print(
            f"Error creating file: {e}"
        )

        return False


# =========================================================
# SKILL FILE PATH
# =========================================================

def get_skill_path(filename):
    filename = clean_filename(filename)

    if not filename:
        return None

    path = os.path.abspath(
        os.path.join(
            CREATE_FOLDER,
            filename
        )
    )

    allowed_folder = os.path.abspath(
        CREATE_FOLDER
    )

    # Security check.
    if not path.startswith(
        allowed_folder + os.sep
    ):
        return None

    return path


# =========================================================
# REGISTER / UPDATE SKILL
# =========================================================

def register_skill(
    name,
    filename,
    triggers,
    description=""
):
    """
    Register or update a skill.

    The skill remembers the filename and triggers,
    NOT what the Python code does.

    Example:

        YouTube -> yt.py

    If yt.py is deleted and a new yt.py is created,
    the registration remains valid.
    """

    name = str(name).strip()

    filename = clean_filename(
        filename
    )

    if not name or not filename:
        return False

    if not isinstance(
        triggers,
        list
    ):
        triggers = []

    clean_triggers = []

    for trigger in triggers:

        if not isinstance(
            trigger,
            str
        ):
            continue

        trigger = trigger.strip().lower()

        if (
            trigger
            and trigger not in clean_triggers
        ):
            clean_triggers.append(trigger)

    registry = load_registry()

    key = name.lower()

    # -----------------------------------------------------
    # UPDATE EXISTING SKILL
    # -----------------------------------------------------
    #
    # This is important.
    #
    # If:
    #
    #     YouTube -> yt.py
    #
    # already exists and you create another yt.py,
    # we don't create another skill.
    #
    # We simply keep/update the same skill.
    #

    old_skill = registry.get(key)

    if old_skill:

        old_triggers = old_skill.get(
            "triggers",
            []
        )

        if isinstance(
            old_triggers,
            list
        ):
            for trigger in old_triggers:

                if (
                    isinstance(trigger, str)
                    and trigger.strip().lower()
                    not in clean_triggers
                ):
                    clean_triggers.append(
                        trigger.strip().lower()
                    )

    registry[key] = {
        "name": name,
        "filename": filename,
        "triggers": clean_triggers,
        "description": str(
            description
        ).strip()
    }

    return save_registry(
        registry
    )


# =========================================================
# FIND SKILL
# =========================================================

def find_skill(command):
    """
    Find a registered skill.

    IMPORTANT:
    A missing file does NOT remove the skill.

    Examples:

        youtube
        open youtube
        run youtube

        yt.py
        run yt.py

        signal
        open signal
    """

    command = str(
        command
    ).strip().lower()

    if not command:
        return None

    # IMPORTANT:
    # Always load the registry directly.
    #
    # We do NOT remove "stale" skills.
    #
    registry = load_registry()

    # =====================================================
    # EXACT SKILL NAME
    # =====================================================

    if command in registry:

        return registry[command]

    # =====================================================
    # FILENAME MATCHING
    # =====================================================

    for skill in registry.values():

        filename = str(
            skill.get(
                "filename",
                ""
            )
        ).strip().lower()

        if not filename:
            continue

        possible_commands = {
            filename,
            f"open {filename}",
            f"run {filename}",
            f"launch {filename}",
            f"start {filename}",
            f"execute {filename}"
        }

        if command in possible_commands:

            return skill

    # =====================================================
    # EXACT TRIGGER
    # =====================================================

    for skill in registry.values():

        triggers = skill.get(
            "triggers",
            []
        )

        if not isinstance(
            triggers,
            list
        ):
            continue

        for trigger in triggers:

            if not isinstance(
                trigger,
                str
            ):
                continue

            trigger = trigger.strip().lower()

            if command == trigger:

                return skill

    # =====================================================
    # NATURAL SENTENCE MATCHING
    # =====================================================

    for skill in registry.values():

        triggers = skill.get(
            "triggers",
            []
        )

        if not isinstance(
            triggers,
            list
        ):
            continue

        for trigger in triggers:

            if not isinstance(
                trigger,
                str
            ):
                continue

            trigger = trigger.strip().lower()

            if (
                trigger
                and trigger in command
            ):
                return skill

    return None


# =========================================================
# RUN SKILL
# =========================================================

def run_skill(skill):
    """
    Run the CURRENT contents of the registered Python file.

    The registry does not care what the file does.

    Example:

        YouTube -> yt.py

    Whatever code is currently inside yt.py is executed.
    """

    if not isinstance(
        skill,
        dict
    ):
        return False

    filename = clean_filename(
        skill.get("filename")
    )

    if not filename:
        return False

    script_path = get_skill_path(
        filename
    )

    if not script_path:
        print(
            "Error: skill path is outside "
            "the allowed folder."
        )

        return False

    # =====================================================
    # FILE MUST EXIST WHEN WE TRY TO RUN IT
    # =====================================================

    if not os.path.isfile(
        script_path
    ):
        print(
            f"Error: skill file not found: "
            f"{script_path}"
        )

        return False

    # =====================================================
    # PYTHON ONLY
    # =====================================================

    if not filename.lower().endswith(
        ".py"
    ):
        print(
            "Error: only Python skills "
            "are allowed."
        )

        return False

    # =====================================================
    # RUN CURRENT SCRIPT
    # =====================================================

    try:

        subprocess.Popen(
            [
                sys.executable,
                script_path
            ],
            cwd=CREATE_FOLDER,
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
            )
        )

        return True

    except Exception as e:

        print(
            f"Error running skill: {e}"
        )

        return False


# =========================================================
# EXECUTE COMMAND
# =========================================================

def execute_command(command):
    """
    Execute a registered Jarvis skill and return its details.
    """

    skill = find_skill(command)

    if not skill:
        return None

    success = run_skill(skill)

    if success:
        return {
            "success": True,
            "name": skill.get("name", "Skill"),
            "filename": skill.get("filename", "")
        }

    return {
        "success": False,
        "name": skill.get("name", "Skill"),
        "filename": skill.get("filename", "")
    }


# =========================================================
# LIST SKILLS
# =========================================================

def list_skills():

    registry = load_registry()

    return list(
        registry.values()
    )


# =========================================================
# REMOVE SKILL
# =========================================================

def remove_skill(name):

    name = str(
        name
    ).strip().lower()

    registry = load_registry()

    if name not in registry:
        return False

    del registry[name]

    return save_registry(
        registry
    )