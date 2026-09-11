import json
import re

from ollama import chat


# ==================================================
# CONFIGURATION
# ==================================================

MODEL = "qwen2.5:7b-instruct-q3_K_M"


# ==================================================
# CLEAN JSON RESPONSE
# ==================================================

def clean_json_response(text):

    text = text.strip()

    # Remove markdown code fences if Qwen adds them
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


# ==================================================
# PARSE USER INTENT
# ==================================================

def parse_user_intent(user_text):
    """
    Convert natural language into a list of safe,
    structured actions.

    Qwen only understands the request.
    It does not execute anything.
    """

    prompt = f"""
You are Jarvis's intent parser.

Analyze the user's message and return ONLY valid JSON.

The user may contain MULTIPLE requests in one sentence.

Allowed action types:

1. chat
2. launch_app
3. open_url
4. none

Return this exact structure:

{{
    "actions": [
        {{
            "type": "chat",
            "text": "question or conversational part"
        }},
        {{
            "type": "launch_app",
            "apps": ["signal", "discord"]
        }},
        {{
            "type": "open_url",
            "url": "https://www.youtube.com"
        }}
    ]
}}

Rules:

- Detect ALL meaningful requests in the user's message.
- Preserve the order in which the user requested them.
- Multiple applications must be returned in one launch_app action.
- Ignore conversational filler such as:
  "ok", "okay", "hey", "hi", "hello",
  "please", "pls", "for me", "real quick",
  "right now", "just", "now".
- Understand natural language.
- "open", "start", "launch", "run", "fire up"
  can indicate an application request.
- Do NOT invent application names.
- Do NOT return executable paths.
- Do NOT return shell commands.
- Do NOT return PowerShell commands.
- Do NOT return Python code.
- Qwen only identifies intent. Jarvis will perform the action.
- If the message is only a normal question or conversation,
  use a "chat" action.
- If the message contains an app request AND a question,
  return both actions.
- YouTube, Gmail, Google and ChatGPT are websites.
- If the user says "open YouTube", use open_url.
- If the user asks "are you smarter than Qwen?", this is a chat action.
- Do not treat model names as applications unless the user explicitly
  asks to launch an installed application with that name.

Examples:

User:
"open signal"

Return:
{{
    "actions": [
        {{
            "type": "launch_app",
            "apps": ["signal"]
        }}
    ]
}}

User:
"start signal and discord"

Return:
{{
    "actions": [
        {{
            "type": "launch_app",
            "apps": ["signal", "discord"]
        }}
    ]
}}

User:
"can you launch vscode and open youtube"

Return:
{{
    "actions": [
        {{
            "type": "launch_app",
            "apps": ["vscode"]
        }},
        {{
            "type": "open_url",
            "url": "https://www.youtube.com"
        }}
    ]
}}

User:
"are you smarter than qwen2.5:7b-instruct-q3_K_M and open signal"

Return:
{{
    "actions": [
        {{
            "type": "chat",
            "text": "Are you smarter than qwen2.5:7b-instruct-q3_K_M?"
        }},
        {{
            "type": "launch_app",
            "apps": ["signal"]
        }}
    ]
}}

User:
"what is Docker and launch vscode"

Return:
{{
    "actions": [
        {{
            "type": "chat",
            "text": "What is Docker?"
        }},
        {{
            "type": "launch_app",
            "apps": ["vscode"]
        }}
    ]
}}

User:
"hello jarvis"

Return:
{{
    "actions": [
        {{
            "type": "chat",
            "text": "hello jarvis"
        }}
    ]
}}

User message:
{user_text}
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
        ]

        content = clean_json_response(
            content
        )

        data = json.loads(
            content
        )

        if not isinstance(
            data,
            dict
        ):
            return None

        actions = data.get(
            "actions",
            []
        )

        if not isinstance(
            actions,
            list
        ):
            return None

        return {
            "actions": actions
        }

    except Exception as e:

        print(
            f"Intent parser error: {e}"
        )

        return None


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    print("=" * 60)
    print("JARVIS MULTI-INTENT PARSER TEST")
    print("=" * 60)
    print()

    tests = [
        "open signal",
        "start signal and discord",
        "can you launch vscode and open youtube",
        "are you smarter than qwen2.5:7b-instruct-q3_K_M and open signal",
        "what is Docker and launch vscode",
    ]

    for text in tests:

        print(
            f"USER: {text}"
        )

        result = parse_user_intent(
            text
        )

        print(
            json.dumps(
                result,
                indent=4
            )
        )

        print("-" * 60)