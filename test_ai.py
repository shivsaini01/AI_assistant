from ollama import chat

response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": "What is 2 + 2?"
        }
    ]
)

print(response.message.content)