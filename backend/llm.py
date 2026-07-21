import requests

with open("context.txt", "r") as f:
    context = f.read()

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"  # Change to whatever model you've pulled

def ask_bot(user_input):
    prompt = (
        "You are a helpful college club help desk assistant. "
        "Your answers are concise.\n\n"
        f"Context:\n{context}\n\n"
        f"User Question: {user_input}\n\n"
        "Answer:"
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            }
        )

        response.raise_for_status()
        data = response.json()
        return data["response"].strip()

    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return "I have encountered an error."


if __name__ == '__main__':
    print("HelpDesk Bot (type 'exit' to quit)")

    while True:
        user = input("You: ")
        if user.lower() == "exit":
            break
        reply = ask_bot(user)
        if reply:
            print("\nBot:", reply + "\n")