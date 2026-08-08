import json
import os
import re
import urllib.error
import urllib.request

# Dynamic paths to Downloads directory
downloads_path = os.path.expanduser("~/Downloads")
brain_file = os.path.join(downloads_path, "brain.txt")
config_file = os.path.join(downloads_path, "user_config.json")


def clean_text(text):
    """Normalize user input by lowering case and removing punctuation."""
    text = text.lower().strip()
    return re.sub(r"[^\w\s]", "", text)


def load_config():
    """Asks the user for their API key on first run and saves it locally."""
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as file:
                config = json.load(file)
                if config.get("api_key"):
                    return config
        except Exception:
            pass

    print("--- First-Time Setup ---")
    api_key = input("🔑 Please enter your Groq/API key: ").strip()

    # Pre-configured endpoint for Groq keys (gsk_)
    config = {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key": api_key,
        "model": "llama-3.1-8b-instant",
    }

    try:
        with open(config_file, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        print(f" Saved config to: {config_file}\n")
    except Exception as e:
        print(f"Warning: Could not save configuration locally: {e}")

    return config


def load_brain():
    """Reads saved offline memory from brain.txt."""
    if os.path.exists(brain_file):
        try:
            with open(brain_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            pass

    return {
        "hello": "Hi there! How can I help you?",
        "hi": "Hey! What's up?",
    }


def save_brain(brain):
    """Saves updated response pairs into brain.txt."""
    with open(brain_file, "w", encoding="utf-8") as file:
        json.dump(brain, file, indent=4)


def fetch_ai_response(prompt, config):
    """Queries the AI provider using urllib with a standard User-Agent header."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    data = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}],
    }

    req = urllib.request.Request(
        config["url"],
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"].strip()
    except Exception:
        # Returns None on failure or if offline
        return None


def start_chat():
    config = load_config()
    brain = load_brain()

    print("🤖 AI Chatbot Loaded!")
    print(f"📁 Brain File: {brain_file}")
    print("Type 'quit' to exit the chat.\n")

    while True:
        try:
            user_input = input("You: ")
        except (KeyboardInterrupt, EOFError):
            break

        cleaned_input = clean_text(user_input)

        if cleaned_input == "quit":
            print("Bot: Goodbye!")
            break

        if not cleaned_input:
            continue

        ai_reply = fetch_ai_response(user_input, config)

        if ai_reply:
            print(f"Bot (AI): {ai_reply}\n")
            brain[cleaned_input] = ai_reply
            save_brain(brain)
        else:
            if cleaned_input in brain:
                print(f"Bot (Offline Memory): {brain[cleaned_input]}\n")
            else:
                print(
                    "Bot: Connection failed or offline. No local response saved for that question yet.\n"
                )


if __name__ == "__main__":
    start_chat()