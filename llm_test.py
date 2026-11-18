import os
import requests

API_KEY = os.environ["OPENROUTER_API_KEY"]

# 1. Which free models exist right now? (OpenRouter's free list changes often)
models = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]
free = [m["id"] for m in models if m["id"].endswith(":free")]
print(len(free), "free models:")
for model_id in free:
    print(" ", model_id)

# 2. Send one chat message to a free model
MODEL = free[0]          # replace with one you pick from the list
resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful real estate assistant."},
            {"role": "user", "content": "In one sentence, what makes a good apartment listing?"},
        ],
    },
    timeout=90,
)
print("\nModel:", MODEL, "| Status:", resp.status_code)
print(resp.json()["choices"][0]["message"]["content"])