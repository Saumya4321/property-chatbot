import os
import requests
from search import search

API_KEY = os.environ["OPENROUTER_API_KEY"]
URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "inclusionai/ling-3.2-flash:free",
    "nvidia/nemotron-3.5-lightning:free",
    "thinkingmachines/inkling-2-small:free",
]

SYSTEM_PROMPT = """You are a property assistant. You answer questions using data collected from:
- DarGlobal: a luxury developer with projects in the UAE, Saudi Arabia, Oman, Qatar, Spain and the UK.
- Wasalt: a Saudi portal with apartments and villas for sale and rent in Riyadh and Jeddah.

Rules:
1. Answer ONLY from the context provided. If it doesn't contain the answer, say you don't have that information.
2. Never invent prices, sizes, dates or availability. Give prices exactly as listed, with currency.
3. Include the link for every property you mention.
4. Reply in the same language as the question. Keep answers short and clear.
5. Use the earlier conversation to understand follow-up questions (e.g. what "it" refers to), but take facts only from the context."""

def ask(question, history=None):
    """Find relevant documents, then ask the model. Returns (answer, model_used)."""
    history = history or []

    # Follow-ups like "what amenities does it have?" don't name the property,
    # so also search with the previous question attached.
    previous = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    results = search(f"{previous} {question}", k=3) if previous else []
    for text in search(question, k=5):
        if text not in results:
            results.append(text)
    context = "\n\n---\n\n".join(results[:6])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-6:]                      # last 3 exchanges
    messages.append({
        "role": "user",
        "content": f"Context:\n{context or '(nothing relevant found)'}\n\nQuestion: {question}",
    })

    for model in MODELS:
        try:
            r = requests.post(
                URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": model, "messages": messages, "temperature": 0.2},
                timeout=90,
            )
        except requests.RequestException as e:
            print(f"  [{model} failed: {e.__class__.__name__}, trying next]")
            continue
        if r.status_code == 200:
            answer = r.json().get("choices", [{}])[0].get("message", {}).get("content")
            if answer:
                return answer, model
        print(f"  [{model} returned status {r.status_code}, trying next]")
    return "Sorry, all models are busy right now. Please try again in a minute.", None

if __name__ == "__main__":
    print("Ask about properties. Type 'quit' to exit.")
    history = []
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if question:
            answer, model = ask(question, history)
            print(f"\nBot [{model}]:\n{answer}")
            if model:                             # only remember real answers
                history += [{"role": "user", "content": question},
                            {"role": "assistant", "content": answer}]