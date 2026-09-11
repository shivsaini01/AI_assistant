import json
import os
import re

from ollama import chat

from commands import (
    create_file,
    register_skill,
    find_skill,
    execute_command,
)

from jarvis_tools import (
    launch_app,
    open_url,
)

from intent_parser import (
    parse_user_intent,
)


# ==================================================
# CONFIGURATION
# ==================================================

MODEL = "qwen2.5:7b-instruct-q3_K_M"

BASE_DIR = r"C:\AI_Assistant"

SAFE_FOLDER = os.path.join(
    BASE_DIR,
    "skills"
)


# ==================================================
# FILE REQUEST DETECTION
# ==================================================

FILE_ACTIONS = [
    "create a file",
    "create file",
    "make a file",
    "make file",
    "write a file",
    "write file",
    "save a file",
    "save file",
    "generate a file",
    "generate file",
]


def is_file_request(text):

    text_lower = text.lower()

    return any(
        phrase in text_lower
        for phrase in FILE_ACTIONS
    )


# ==================================================
# KNOWN WEBSITE FALLBACK
# ==================================================

def detect_known_website(text):

    text_lower = text.lower()

    if "youtube" in text_lower:

        return "https://www.youtube.com"

    if "chatgpt" in text_lower:

        return "https://chatgpt.com"

    if "gmail" in text_lower:

        return "https://mail.google.com"

    if (
        "google" in text_lower
        and "chrome" not in text_lower
    ):

        return "https://www.google.com"

    return None


# ==================================================
# VALIDATE APP NAME
# ==================================================

def is_safe_app_name(app_name):

    if not isinstance(
        app_name,
        str
    ):
        return False

    app_name = app_name.strip()

    if not app_name:

        return False

    # Prevent paths / command injection
    forbidden = [
        "\\",
        "/",
        ":",
        ";",
        "|",
        "&",
        ">",
        "<",
        '"',
        "'",
    ]

    return not any(
        char in app_name
        for char in forbidden
    )


# ==================================================
# VALIDATE URL
# ==================================================

def is_safe_url(url):

    if not isinstance(
        url,
        str
    ):
        return False

    url = url.strip()

    return (
        url.startswith(
            "https://"
        )
        or
        url.startswith(
            "http://"
        )
    )


# ==================================================
# HANDLE CHAT ACTION
# ==================================================

def handle_chat(text):

    if not text:

        return

    answer = ask_ai(
        text
    )

    print(
        f"Jarvis: {answer}"
    )


# ==================================================
# HANDLE APP ACTION
# ==================================================

def handle_launch_apps(apps):

    if not isinstance(
        apps,
        list
    ):
        return

    for app_name in apps:

        if not is_safe_app_name(
            app_name
        ):

            print(
                f"Jarvis: I couldn't use that application name."
            )

            continue

        app_name = app_name.strip()

        print(
            f"Jarvis: 🔍 Looking for {app_name.title()}..."
        )

        success, message = launch_app(
            app_name
        )

        if success:

            print(
                f"Jarvis: ✅ {message}"
            )

        else:

            print(
                f"Jarvis: ❌ {message}"
            )


# ==================================================
# HANDLE URL
# ==================================================

def handle_open_url(url):

    if not is_safe_url(
        url
    ):

        print(
            "Jarvis: ❌ Invalid website address."
        )

        return

    success, message = open_url(
        url
    )

    if success:

        print(
            f"Jarvis: ✅ {message}"
        )

    else:

        print(
            f"Jarvis: ❌ {message}"
        )


# ==================================================
# HANDLE SKILL
# ==================================================

def handle_skill(skill_name):

    if not skill_name:

        return False

    skill = find_skill(
        skill_name
    )

    if not skill:

        return False

    return execute_command(
        skill.get(
            "filename"
        )
    )


# ==================================================
# PROCESS MULTIPLE ACTIONS
# ==================================================

def process_actions(result):

    if not result:

        return False

    actions = result.get(
        "actions",
        []
    )

    if not isinstance(
        actions,
        list
    ):
        return False

    processed = False

    for action in actions:

        if not isinstance(
            action,
            dict
        ):
            continue

        action_type = action.get(
            "type"
        )

        # ------------------------------------------
        # CHAT
        # ------------------------------------------

        if action_type == "chat":

            text = action.get(
                "text",
                ""
            )

            if text:

                handle_chat(
                    text
                )

                processed = True

        # ------------------------------------------
        # LAUNCH APP
        # ------------------------------------------

        elif action_type == "launch_app":

            apps = action.get(
                "apps",
                []
            )

            if apps:

                handle_launch_apps(
                    apps
                )

                processed = True

        # ------------------------------------------
        # OPEN URL
        # ------------------------------------------

        elif action_type == "open_url":

            url = action.get(
                "url",
                ""
            )

            if url:

                handle_open_url(
                    url
                )

                processed = True

        # ------------------------------------------
        # NONE
        # ------------------------------------------

        elif action_type == "none":

            continue

    return processed


# ==================================================
# FILE AI
# ==================================================

def ask_file_ai(user_text):

    prompt = f"""
You are Jarvis's file-generation assistant.

The user wants to create a file.

User request:

{user_text}

The file will be saved directly inside:

{SAFE_FOLDER}

Return ONLY valid JSON.

Format:

{{
    "filename": "example.py",
    "content": "complete file content here",
    "skill_name": "Example Skill",
    "triggers": ["example", "run example"],
    "description": "What this skill does"
}}

Rules:

1. Return valid JSON only.
2. Do not use markdown code fences.
3. Do not include explanations outside JSON.
4. filename must be a simple filename.
5. Do not include folder paths.
6. Do not use ".." in the filename.
7. If this is a Python skill, provide complete runnable Python code.
"""

    try:

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response[
            "message"
        ][
            "content"
        ].strip()

        content = re.sub(
            r"^```json\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        content = re.sub(
            r"^```\s*",
            "",
            content
        )

        content = re.sub(
            r"\s*```$",
            "",
            content
        )

        return json.loads(
            content
        )

    except Exception as e:

        print(
            f"File AI error: {e}"
        )

        return None


# ==================================================
# CLEAN FILENAME
# ==================================================

def clean_filename(filename):

    if not filename:

        return None

    filename = os.path.basename(
        str(filename)
    ).strip()

    if ".." in filename:

        return None

    return filename


# ==================================================
# CREATE FILE
# ==================================================

def create_file_from_response(data):

    if not isinstance(
        data,
        dict
    ):

        print(
            "Jarvis: ❌ Invalid AI file response."
        )

        return False

    filename = clean_filename(
        data.get(
            "filename"
        )
    )

    content = data.get(
        "content",
        ""
    )

    skill_name = data.get(
        "skill_name"
    )

    triggers = data.get(
        "triggers",
        []
    )

    description = data.get(
        "description",
        ""
    )

    if not filename:

        print(
            "Jarvis: ❌ Invalid filename."
        )

        return False

    if not content:

        print(
            "Jarvis: ❌ File content is empty."
        )

        return False

    success, result = create_file(
        filename,
        content
    )

    if not success:

        print(
            f"Jarvis: ❌ {result}"
        )

        return False

    print(
        f"Jarvis: ✅ File created: {result}"
    )

    if filename.lower().endswith(
        ".py"
    ):

        if not skill_name:

            skill_name = os.path.splitext(
                filename
            )[0]

        register_skill(
            skill_name=skill_name,
            filename=filename,
            triggers=triggers,
            description=description
        )

        print(
            f"Jarvis: ✅ Skill registered: {skill_name}"
        )

    return True


# ==================================================
# NORMAL AI
# ==================================================

def ask_ai(user_text):

    try:

        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )

        return response[
            "message"
        ][
            "content"
        ]

    except Exception as e:

        return f"AI error: {e}"


# ==================================================
# MAIN
# ==================================================

def main():

    print("=" * 60)
    print("JARVIS SMART AI ASSISTANT")
    print("=" * 60)

    print(
        "Type 'exit' to quit."
    )

    print()

    while True:

        try:

            user_text = input(
                "You: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\nJarvis: Goodbye."
            )

            break

        if not user_text:

            continue

        # ------------------------------------------
        # EXIT
        # ------------------------------------------

        if user_text.lower() in {
            "exit",
            "quit",
            "bye"
        }:

            print(
                "Jarvis: Goodbye."
            )

            break

        # ------------------------------------------
        # NAME
        # ------------------------------------------

        if user_text.lower().startswith(
            "my name is "
        ):

            name = user_text[
                11:
            ].strip()

            if name:

                print(
                    f"Jarvis: Nice to meet you, {name}."
                )

            continue

        # ------------------------------------------
        # FILE CREATION
        # ------------------------------------------

        if is_file_request(
            user_text
        ):

            print(
                "Jarvis: 🛠️ Creating the file..."
            )

            data = ask_file_ai(
                user_text
            )

            if data:

                create_file_from_response(
                    data
                )

            else:

                print(
                    "Jarvis: ❌ I couldn't generate the file."
                )

            continue

        # ------------------------------------------
        # MULTI-INTENT PARSER
        # ------------------------------------------

        result = parse_user_intent(
            user_text
        )

        # ------------------------------------------
        # Fallback for known websites
        # ------------------------------------------

        if not result:

            website = detect_known_website(
                user_text
            )

            if website:

                handle_open_url(
                    website
                )

                continue

        # ------------------------------------------
        # PROCESS ALL ACTIONS
        # ------------------------------------------

        if result:

            handled = process_actions(
                result
            )

            if handled:

                continue

        # ------------------------------------------
        # NORMAL AI FALLBACK
        # ------------------------------------------

        answer = ask_ai(
            user_text
        )

        print(
            f"Jarvis: {answer}"
        )


# ==================================================
# START JARVIS
# ==================================================

if __name__ == "__main__":

    main()