MODEL = "qwen2.5:7b-instruct-q3_K_M"

import json
import re

from ollama import chat
from commands import execute_command, create_file


# =========================================================
# SETTINGS
# =========================================================

SAFE_FOLDER = r"C:\AI_Assistant\test_prompt"


# =========================================================
# CONVERSATION MEMORY
# =========================================================

conversation = []

USER_NAME = None


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are Jarvis, a helpful PC assistant.

Your name is Jarvis.

Answer normal questions naturally.

You should remember information the user tells you during this
conversation.

If the user tells you their name, remember it and use it when
appropriate.

Do NOT create files for normal questions.

Do NOT create files for:
- greetings
- normal conversation
- math questions
- general questions

A file should only be created when the user explicitly asks to:
- create a file
- make a file
- write code/file content into a file
- save something to a file
- create a script
- write something into a filename such as test.py

You are running as a PC assistant.
"""


# =========================================================
# FILE EXTENSIONS
# =========================================================

FILE_EXTENSIONS = (
    "py|txt|json|html|htm|css|js|jsx|ts|tsx|cpp|c|h|"
    "java|md|csv|xml|yaml|yml|sql|sh|bat|ps1"
)


# =========================================================
# DETECT FILE REQUEST
# =========================================================

def user_wants_file(user_input):
    text = user_input.lower().strip()

    # Explicit file actions
    file_actions = [
        "create a file",
        "create an file",
        "create file",
        "make a file",
        "make an file",
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
    ]

    for phrase in file_actions:
        if phrase in text:
            return True

    # Detect filenames such as:
    # test.py
    # calculator.py
    # hello.txt
    # index.html
    filename_pattern = (
        rf"\b[\w\-. ]+\.({FILE_EXTENSIONS})\b"
    )

    has_filename = bool(
        re.search(filename_pattern, text, re.IGNORECASE)
    )

    if not has_filename:
        return False

    # If a filename is explicitly mentioned with an action,
    # treat it as a file request.
    action_words = [
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
    ]

    return any(word in text for word in action_words)


# =========================================================
# DETECT OBS
# =========================================================

def user_wants_obs(user_input):
    text = user_input.lower().strip()

    return (
        "open obs" in text
        or "launch obs" in text
        or "start obs" in text
        or "open obs studio" in text
    )


# =========================================================
# DETECT BRAVE
# =========================================================

def user_wants_brave(user_input):
    text = user_input.lower().strip()

    return (
        "open brave" in text
        or "launch brave" in text
        or "start brave" in text
    )


# =========================================================
# EXTRACT USER NAME
# =========================================================

def detect_user_name(user_input):
    global USER_NAME

    text = user_input.strip()

    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z0-9 _-]{0,40})",
        r"\bcall me ([A-Za-z][A-Za-z0-9 _-]{0,40})",
        r"\bi am ([A-Za-z][A-Za-z0-9 _-]{0,40})",
        r"\bi'm ([A-Za-z][A-Za-z0-9 _-]{0,40})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            name = match.group(1).strip()

            # Avoid accidentally treating common sentences
            # as names.
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

    # Add previous conversation
    messages.extend(conversation)

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    response = chat(
        model=MODEL,
        messages=messages
    )

    answer = response.message.content.strip()

    # Save conversation
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

    return answer


# =========================================================
# FILE AI
# =========================================================

def ask_file_ai(user_input):

    file_system_prompt = f"""
You are Jarvis's file creation assistant.

The user explicitly wants a file created or modified.

Your job is to determine:

1. The filename
2. The COMPLETE contents of the file

You MUST return a create_file function call whenever possible.

The safe folder is:

{SAFE_FOLDER}

IMPORTANT:

filename:
- Must be only the filename.
- Example: test.py
- Do not include the folder path.

content:
- Must contain the COMPLETE actual file contents.
- content MUST be a plain string.
- Do NOT put JSON schema inside content.
- Do NOT put tool definitions inside content.
- Do NOT explain how to create the file.
- Do NOT use markdown fences around the code.
- Do NOT return an explanation instead of the file.

For example:

User:
write a hello world program in test.py

The file content should be:

print("Hello World")

Another example:

User:
write a simple calculator code in calculator.py

The content should be actual Python code such as:

def add(a, b):
    return a + b

...

Use the create_file tool.
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": file_system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": (
                        "Create a file inside "
                        f"{SAFE_FOLDER}"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": (
                                    "Filename only, such as "
                                    "test.py"
                                )
                            },
                            "content": {
                                "type": "string",
                                "description": (
                                    "Complete actual file "
                                    "contents as a plain string."
                                )
                            }
                        },
                        "required": [
                            "filename",
                            "content"
                        ]
                    }
                }
            }
        ]
    )

    return response


# =========================================================
# CLEAN FILENAME
# =========================================================

def clean_filename(filename):

    if not isinstance(filename, str):
        return None

    filename = filename.strip()

    filename = filename.strip('"')
    filename = filename.strip("'")

    # Convert Windows paths into just the filename.
    filename = filename.replace("\\", "/")

    if "/" in filename:
        filename = filename.split("/")[-1]

    return filename.strip()


# =========================================================
# CLEAN CONTENT
# =========================================================

def clean_content(content):

    if not isinstance(content, str):
        return None

    content = content.strip()

    # Remove accidental markdown fences.
    if content.startswith("```"):

        lines = content.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    # Reject obvious schema output.
    bad_patterns = [
        '"type": "string"',
        '"description":',
        '"properties":',
        '"required":',
    ]

    if all(pattern in content for pattern in bad_patterns[:2]):
        return None

    return content


# =========================================================
# CREATE FILE FROM ARGUMENTS
# =========================================================

def create_file_from_arguments(arguments):

    if not isinstance(arguments, dict):
        print("AI: Invalid file arguments.")
        return True

    filename = clean_filename(
        arguments.get("filename")
    )

    content = clean_content(
        arguments.get("content")
    )

    if not filename:
        print("AI: I couldn't determine the filename.")
        return True

    if content is None:
        print(
            "AI: The model did not provide valid file content."
        )
        return True

    # Extra safety:
    # only allow normal filenames, not paths.
    if (
        ".." in filename
        or "/" in filename
        or "\\" in filename
    ):
        print("AI: Invalid filename.")
        return True

    success = create_file(
        filename,
        content
    )

    if success:
        print(
            f"AI: Done. Created {filename} in "
            f"{SAFE_FOLDER}"
        )
    else:
        print("AI: I couldn't create the file.")

    return True


# =========================================================
# FIND JSON TOOL CALL IN TEXT
# =========================================================

def find_create_file_json(text):

    text = text.strip()

    # First try normal JSON.
    try:
        data = json.loads(text)

        if isinstance(data, dict):
            if data.get("name") == "create_file":
                return data

            if data.get("function") == "create_file":
                return data

    except json.JSONDecodeError:
        pass

    # Try to locate a JSON object inside surrounding text.
    start_positions = [
        m.start()
        for m in re.finditer(r"\{", text)
    ]

    for start in start_positions:

        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):

            char = text[i]

            if escape:
                escape = False
                continue

            if char == "\\" and in_string:
                escape = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1

            elif char == "}":
                depth -= 1

                if depth == 0:

                    candidate = text[start:i + 1]

                    try:
                        data = json.loads(candidate)

                        if isinstance(data, dict):

                            if data.get("name") == "create_file":
                                return data

                            if (
                                isinstance(
                                    data.get("function"),
                                    dict
                                )
                                and
                                data["function"].get("name")
                                == "create_file"
                            ):
                                return data

                    except json.JSONDecodeError:
                        pass

                    break

    return None


# =========================================================
# EXECUTE FILE REQUEST
# =========================================================

def execute_file_request(response):

    message = response.message

    # -----------------------------------------------------
    # Native Ollama tool call
    # -----------------------------------------------------

    tool_calls = getattr(
        message,
        "tool_calls",
        None
    )

    if tool_calls:

        for tool_call in tool_calls:

            function = getattr(
                tool_call,
                "function",
                None
            )

            if not function:
                continue

            function_name = getattr(
                function,
                "name",
                None
            )

            if function_name != "create_file":
                continue

            arguments = getattr(
                function,
                "arguments",
                {}
            )

            if isinstance(arguments, str):

                try:
                    arguments = json.loads(arguments)

                except json.JSONDecodeError:
                    print("AI: Invalid tool arguments.")
                    return True

            return create_file_from_arguments(
                arguments
            )

    # -----------------------------------------------------
    # JSON returned as text
    # -----------------------------------------------------

    text = getattr(
        message,
        "content",
        ""
    )

    if not text:
        return False

    text = text.strip()

    data = find_create_file_json(text)

    if not data:
        return False

    # Format:
    #
    # {
    #   "name": "create_file",
    #   "arguments": {...}
    # }

    arguments = data.get(
        "arguments",
        {}
    )

    if isinstance(arguments, str):

        try:
            arguments = json.loads(arguments)

        except json.JSONDecodeError:
            print("AI: Invalid file arguments.")
            return True

    return create_file_from_arguments(
        arguments
    )


# =========================================================
# MAIN JARVIS LOOP
# =========================================================

while True:

    try:
        user_input = input("\nYou: ").strip()

    except KeyboardInterrupt:
        print("\nGoodbye!")
        break

    except EOFError:
        print("\nGoodbye!")
        break

    if not user_input:
        continue

    # -----------------------------------------------------
    # EXIT
    # -----------------------------------------------------

    if user_input.lower() in [
        "exit",
        "quit",
        "bye"
    ]:

        print("Goodbye!")
        break

    # -----------------------------------------------------
    # REMEMBER USER NAME
    # -----------------------------------------------------

    detected_name = detect_user_name(
        user_input
    )

    if detected_name:

        print(
            f"AI: Nice to meet you, {detected_name}!"
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
                "content": (
                    f"Nice to meet you, "
                    f"{detected_name}!"
                )
            }
        )

        continue

    # -----------------------------------------------------
    # WHAT IS MY NAME?
    # -----------------------------------------------------

    if re.search(
        r"\bwhat('?s| is) my name\b",
        user_input.lower()
    ):

        if USER_NAME:

            print(
                f"AI: Your name is {USER_NAME}."
            )

        else:

            print(
                "AI: I don't know your name yet. "
                "Tell me by saying 'my name is ...'."
            )

        continue

    # -----------------------------------------------------
    # WHAT IS YOUR NAME?
    # -----------------------------------------------------

    if re.search(
        r"\bwhat('?s| is) your name\b",
        user_input.lower()
    ):

        print(
            "AI: My name is Jarvis."
        )

        continue

    # -----------------------------------------------------
    # OBS
    # -----------------------------------------------------

    if user_wants_obs(user_input):

        execute_command("open obs")

        print("AI: Done.")
        continue

    # -----------------------------------------------------
    # BRAVE
    # -----------------------------------------------------

    if user_wants_brave(user_input):

        execute_command("open brave")

        print("AI: Done.")
        continue

    # -----------------------------------------------------
    # FILE CREATION
    # -----------------------------------------------------

    if user_wants_file(user_input):

        response = ask_file_ai(
            user_input
        )

        handled = execute_file_request(
            response
        )

        if not handled:

            text = getattr(
                response.message,
                "content",
                ""
            ).strip()

            if text:

                # One last attempt to detect JSON.
                data = find_create_file_json(
                    text
                )

                if data:

                    arguments = data.get(
                        "arguments",
                        {}
                    )

                    if isinstance(
                        arguments,
                        str
                    ):
                        try:
                            arguments = json.loads(
                                arguments
                            )
                        except json.JSONDecodeError:
                            arguments = {}

                    create_file_from_arguments(
                        arguments
                    )

                else:

                    print(
                        "AI:",
                        text
                    )

            else:

                print(
                    "AI: I couldn't create the file."
                )

        continue

    # -----------------------------------------------------
    # NORMAL CONVERSATION
    # -----------------------------------------------------

    result = ask_normal_ai(
        user_input
    )

    print(
        "AI:",
        result
    )