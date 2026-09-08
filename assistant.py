MODEL = "qwen3:8b"
from ollama import chat
from commands import execute_command

SYSTEM_PROMPT = """
You are a helpful PC assistant.

You have two available PC actions:

open_obs
open_brave

If the user asks to open OBS, include the exact text: open_obs

If the user asks to open Brave or their browser, include the exact text: open_brave

If the user asks for both, include both.

For normal conversation and questions, simply answer normally.

Do not output action names unless the user actually asks you to perform that action.
"""


def ask_ai(user_input):
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    return response.message.content.strip()


while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    result = ask_ai(user_input)

    # Execute requested actions
    obs_requested = "open_obs" in result
    brave_requested = "open_brave" in result

    if obs_requested:
        execute_command("open obs")

    if brave_requested:
        execute_command("open brave")

    # Always show the AI's normal response
    if not obs_requested and not brave_requested:
        print("AI:", result)
    else:
        print("AI:", "Done.")
