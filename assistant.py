import json
import os
import re

from ollama import chat
from commands import (
    execute_command,
    create_file,
    register_skill,
)


# =========================================================
# SETTINGS
# =========================================================

MODEL = "qwen2.5:7b-instruct-q3_K_M"

BASE_DIR = r"C:\AI_Assistant"

SAFE_FOLDER = os.path.join(
    BASE_DIR,
    "skills",
    "test_prompt"
)

MAX_HISTORY_MESSAGES = 12

conversation = []

USER_NAME = None


# =========================================================
# LOCAL AI SETTINGS
# =========================================================

CHAT_OPTIONS = {
    "temperature": 0.3,
    "num_ctx": 4096,
    "num_predict": 512,
    "keep_alive": "10m",
}


# =========================================================
# NORMAL AI SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are Jarvis, a fast local PC assistant.

Your name is Jarvis.

Answer normal questions naturally and directly.

Do not claim you performed a computer action unless Python
actually performed it.

Do not invent PC capabilities.

Keep normal answers concise unless the user asks for detail.

Approved PC skills are handled by Python before this prompt
is called.

If the user asks for code, answer normally unless they
explicitly ask you to create/write/save the code into a file.
"""


# =========================================================
# FAST ACTION DETECTION
# =========================================================

ACTION_WORDS = (
    "open",
    "launch",
    "start",
    "run",
    "fire up",
    "bring up",
    "get up",
    "load",
    "turn on",
)

NEGATIVE_WORDS = (
    "what is",
    "what's",
    "who is",
    "tell me about",
    "explain",
    "how does",
    "meaning of",
    "about",
)


def has_action_intent(text):
    text = text.lower().strip()

    if any(
        phrase in text
        for phrase in NEGATIVE_WORDS
    ):
        return False

    return any(
        word in text
        for word in ACTION_WORDS
    )


def detect_actions(user_input):
    """
    Detect registered/approved applications quickly.

    IMPORTANT:
    This function should NOT run for file-creation requests.
    File requests are handled first in the main loop.
    """

    text = re.sub(
        r"\s+",
        " ",
        user_input.lower().strip()
    )

    if not has_action_intent(text):
        return []

    found = []

    # -----------------------------------------------------
    # OBS
    # -----------------------------------------------------

    obs_targets = (
        "obs",
        "obs studio",
        "streaming setup",
        "streaming software",
        "recording setup",
        "stream setup",
    )

    if any(
        target in text
        for target in obs_targets
    ):
        found.append("open_obs")

    # -----------------------------------------------------
    # BRAVE
    # -----------------------------------------------------

    brave_targets = (
        "brave",
        "brave browser",
        "my browser",
        "the browser",
        "browser",
    )

    if any(
        target in text
        for target in brave_targets
    ):
        found.append("open_brave")

    # -----------------------------------------------------
    # THE LAST OF US
    # -----------------------------------------------------

    tlou_targets = (
        "the last of us",
        "last of us",
        "tlou",
        "the game",
        "my game",
    )

    if any(
        target in text
        for target in tlou_targets
    ):
        found.append("open_last_of_us")

    # -----------------------------------------------------
    # DYNAMIC SKILLS
    # -----------------------------------------------------
    #
    # Example:
    #
    # YouTube -> yt.py
    #
    # Signal -> signal.py
    #
    # These are resolved by commands.py.
    #

    if not found:
        skill = None

        try:
            from commands import find_skill

            skill = find_skill(text)

        except Exception:
            skill = None

        if skill:
            found.append(
                skill
                .get("name", "")
                .strip()
                .lower()
            )

    return list(
        dict.fromkeys(found)
    )


# =========================================================
# ACTION MESSAGES
# =========================================================

ACTION_MESSAGES = {
    "open_obs": "OBS is open.",
    "open_brave": "Brave is open.",
    "open_last_of_us": "The Last of Us is opening.",
}


def perform_actions(actions):
    for action in actions:
        result = execute_command(action)

        if result and result.get("success"):
            filename = result.get("filename", "")
            name = result.get("name", "Skill")

            if filename:
                print(f"AI: Running {filename} — Opening {name}...")
            else:
                print(f"AI: Opening {name}...")

        elif result:
            filename = result.get("filename", "")
            name = result.get("name", "skill")

            if filename:
                print(f"AI: Couldn't run {filename}.")
            else:
                print(f"AI: Couldn't open {name}.")

        else:
            print(f"AI: I couldn't find a skill for {action}.")


# =========================================================
# FILE REQUEST DETECTION
# =========================================================

FILE_EXTENSIONS = (
    "py|txt|json|html|htm|css|js|jsx|ts|tsx|"
    "cpp|c|h|java|md|csv|xml|yaml|yml|sql|sh|bat|ps1"
)


FILE_ACTIONS = (
    "create a file",
    "create file",
    "make a file",
    "make file",
    "write a file",
    "save a file",
    "create a python file",
    "make a python file",
    "create a text file",
    "make a text file",
    "create a script",
    "make a script",
    "write code in",
    "write code into",
    "write code to",
    "put code in",
    "put code into",
    "save code in",
    "save code to",
)


def user_wants_file(text):
    """
    Detect explicit file-generation requests.

    This MUST run before action detection.
    """

    text = text.lower().strip()

    # Strong explicit file request.
    if any(
        phrase in text
        for phrase in FILE_ACTIONS
    ):
        return True

    # Filename such as:
    #
    # yt.py
    # signal.py
    # calculator.py
    #

    filename_pattern = (
        rf"\b[\w\-. ]+\.({FILE_EXTENSIONS})\b"
    )

    if not re.search(
        filename_pattern,
        text,
        re.IGNORECASE
    ):
        return False

    action_words = (
        "create",
        "make",
        "write",
        "save",
        "put",
        "add",
        "generate",
        "edit",
        "modify",
        "update",
    )

    return any(
        word in text
        for word in action_words
    )


# =========================================================
# NAME MEMORY
# =========================================================

def detect_user_name(user_input):
    global USER_NAME

    patterns = (
        r"\bmy name is ([A-Za-z][A-Za-z0-9 _-]{0,40})",
        r"\bcall me ([A-Za-z][A-Za-z0-9 _-]{0,40})",
        r"\bi am ([A-Za-z][A-Za-z0-9 _-]{0,40})",
        r"\bi'm ([A-Za-z][A-Za-z0-9 _-]{0,40})",
    )

    blocked = {
        "a",
        "an",
        "the",
        "going",
        "fine",
        "good",
        "okay",
        "ok",
        "here",
        "looking",
        "trying",
        "using",
    }

    for pattern in patterns:

        match = re.search(
            pattern,
            user_input.strip(),
            re.IGNORECASE
        )

        if match:

            name = match.group(1).strip()

            if name.lower() in blocked:
                return None

            USER_NAME = name

            return name

    return None


# =========================================================
# NORMAL AI
# =========================================================

def ask_normal_ai(user_input):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(
        conversation[
            -MAX_HISTORY_MESSAGES:
        ]
    )

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    response = chat(
        model=MODEL,
        messages=messages,
        options=CHAT_OPTIONS,
    )

    answer = (
        response.message.content
        .strip()
    )

    conversation.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    conversation.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    if len(conversation) > MAX_HISTORY_MESSAGES:
        del conversation[
            :-MAX_HISTORY_MESSAGES
        ]

    return answer


# =========================================================
# FILE AI
# =========================================================

def ask_file_ai(user_input):

    """
    Generate a complete file using JSON mode.

    Qwen returns:

    {
        "filename": "yt.py",
        "content": "..."
    }
    """

    prompt = f"""
You are Jarvis's file creation engine.

The user explicitly wants a file created.

Return ONLY valid JSON.

Required format:

{{
    "filename": "example.py",
    "content": "complete file contents",
    "skill_name": "Example",
    "triggers": [
        "example",
        "open example",
        "run example"
    ],
    "description": "Short description"
}}

RULES:

1. filename must be ONLY the filename.
2. Never put a path in filename.
3. content must contain the COMPLETE actual code/text.
4. Do NOT use markdown code fences.
5. Do NOT explain anything outside the JSON.
6. skill_name should describe what the script does.
7. triggers should contain natural commands the user
   could say to Jarvis to run this skill.
8. Keep triggers short and useful.
9. The generated Python file must be directly executable.
10. If the user asks to open a website/app, generate code
    that actually opens it instead of calling an API unless
    the user explicitly asks for an API.
11. The file will be saved inside:

{SAFE_FOLDER}

USER REQUEST:

{user_input}
"""

    return chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json",
        options={
            "temperature": 0.1,
            "num_ctx": 4096,
            "num_predict": 2048,
            "keep_alive": "10m",
        },
    )


# =========================================================
# CLEAN FILENAME
# =========================================================

def clean_filename(filename):

    if not isinstance(
        filename,
        str
    ):
        return None

    filename = (
        filename
        .strip()
        .strip('"')
        .strip("'")
    )

    filename = os.path.basename(
        filename
    )

    if not filename:
        return None

    if filename in {
        ".",
        ".."
    }:
        return None

    if ".." in filename:
        return None

    return filename


# =========================================================
# CLEAN CONTENT
# =========================================================

def clean_content(content):

    if not isinstance(
        content,
        str
    ):
        return None

    content = content.strip()

    # Remove accidental markdown fences.
    if content.startswith("```"):

        lines = content.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        content = "\n".join(
            lines
        ).strip()

    return content


# =========================================================
# CREATE FILE + REGISTER SKILL
# =========================================================

def create_file_from_response(response):

    try:

        text = (
            response.message.content
            .strip()
        )

        data = json.loads(text)

    except Exception as e:

        print(
            "AI: I couldn't generate "
            "valid file data."
        )

        return

    if not isinstance(
        data,
        dict
    ):
        print(
            "AI: Invalid file data."
        )

        return

    # -----------------------------------------------------
    # FILE
    # -----------------------------------------------------

    filename = clean_filename(
        data.get("filename")
    )

    content = clean_content(
        data.get("content")
    )

    if not filename:

        print(
            "AI: I couldn't determine "
            "a safe filename."
        )

        return

    if content is None:

        print(
            "AI: I couldn't generate "
            "valid file content."
        )

        return

    # -----------------------------------------------------
    # CREATE / REPLACE FILE
    # -----------------------------------------------------

    if not create_file(
        filename,
        content
    ):
        print(
            "AI: I couldn't create the file."
        )

        return

    # -----------------------------------------------------
    # REGISTER SKILL
    # -----------------------------------------------------

    skill_name = data.get(
        "skill_name"
    )

    if not isinstance(
        skill_name,
        str
    ) or not skill_name.strip():

        # Fallback:
        # yt.py -> Yt
        skill_name = os.path.splitext(
            filename
        )[0].replace(
            "_",
            " "
        ).replace(
            "-",
            " "
        ).title()

    triggers = data.get(
        "triggers",
        []
    )

    if not isinstance(
        triggers,
        list
    ):
        triggers = []

    # Always make filename itself usable.
    if filename.lower() not in [
        str(x).lower()
        for x in triggers
        if isinstance(x, str)
    ]:
        triggers.append(
            filename.lower()
        )

    description = data.get(
        "description",
        ""
    )

    registered = register_skill(
        skill_name,
        filename,
        triggers,
        description
    )

    if registered:

        print(
            f"AI: Created {filename} "
            f"and registered "
            f"'{skill_name}' as a skill."
        )

    else:

        print(
            f"AI: Created {filename}, "
            f"but couldn't register "
            f"the skill."
        )


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        user_input = input(
            "\nYou: "
        ).strip()

    except (
        KeyboardInterrupt,
        EOFError
    ):

        print(
            "\nGoodbye!"
        )

        break

    if not user_input:
        continue

    lower = user_input.lower()


    # =====================================================
    # EXIT
    # =====================================================

    if lower in {
        "exit",
        "quit",
        "bye"
    }:

        print(
            "Goodbye!"
        )

        break


    # =====================================================
    # NAME MEMORY
    # =====================================================

    detected_name = detect_user_name(
        user_input
    )

    if detected_name:

        answer = (
            f"Nice to meet you, "
            f"{detected_name}!"
        )

        print(
            "AI:",
            answer
        )

        conversation.extend(
            [
                {
                    "role": "user",
                    "content": user_input
                },
                {
                    "role": "assistant",
                    "content": answer
                },
            ]
        )

        continue


    # =====================================================
    # NAME QUESTIONS
    # =====================================================

    if re.search(
        r"\bwhat('?s| is) my name\b",
        lower
    ):

        if USER_NAME:

            print(
                f"AI: Your name is "
                f"{USER_NAME}."
            )

        else:

            print(
                "AI: I don't know your "
                "name yet."
            )

        continue


    if re.search(
        r"\bwhat('?s| is) your name\b",
        lower
    ):

        print(
            "AI: My name is Jarvis."
        )

        continue


    # =====================================================
    # IMPORTANT:
    # FILE CREATION MUST COME FIRST
    # =====================================================
    #
    # This fixes:
    #
    # "write a code to open youtube in yt.py"
    #
    # We create/update yt.py instead of trying to
    # execute an old/missing yt.py.
    #

    if user_wants_file(
        user_input
    ):

        response = ask_file_ai(
            user_input
        )

        create_file_from_response(
            response
        )

        continue


    # =====================================================
    # FAST PC / SKILL ACTIONS
    # =====================================================
    #
    # These do NOT use Qwen.
    #

    actions = detect_actions(
        user_input
    )

    if actions:

        perform_actions(
            actions
        )

        continue


    # =====================================================
    # NORMAL LOCAL AI
    # =====================================================

    print(
        "AI:",
        ask_normal_ai(
            user_input
        )
    )