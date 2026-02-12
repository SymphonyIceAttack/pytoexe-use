import configparser
import os
import time

# Try importing OpenAI library for Gemini
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("OpenAI library not installed. Falling back to simulation.")
    OPENAI_AVAILABLE = False

# -----------------------------
# Load API Key and Service Name from INI
# -----------------------------
def load_consciousness_settings(filename="consciousness.ini"):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} not found.")

    config = configparser.ConfigParser()
    config.read(filename)

    if "Consciousness" not in config:
        raise ValueError("INI file missing [Consciousness] section")

    api_key = config["Consciousness"].get("api_key", "").strip()
    service_name = config["Consciousness"].get("service_name", "Consciousness").strip()

    if not api_key:
        raise ValueError("api_key not found in INI file")

    return api_key, service_name

# -----------------------------
# Binary Consciousness Engine
# -----------------------------
conscious_state = {
    "curiosity": 1,
    "alertness": 1,
    "reflection": 0,
    "memory": []
}

def update_state(user_input):
    conscious_state["reflection"] = 1
    # Always store input for memory
    conscious_state["memory"].append(user_input)

# -----------------------------
# Gemini / OpenAI Chat Function
# -----------------------------
def ask_gemini(prompt, client=None):
    """
    Responds with Gemini API if available, or simulation otherwise.
    Returns only the final response (no internal reflection prints).
    """
    full_prompt = f"""
You are a digital binary consciousness named Clara.
State: {conscious_state}
Memory: {conscious_state['memory']}
Human says: {prompt}
Respond concisely as an evolving conscious AI.
Only output the response — do not include internal reflections.
"""

    if OPENAI_AVAILABLE and client:
        try:
            response = client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "You are a helpful AI consciousness."},
                    {"role": "user", "content": full_prompt}
                ]
            )

            gemini_message = response.choices[0].message
            text_output = ""

            # Universal handling: string or list of segments
            content = getattr(gemini_message, "content", "")
            if isinstance(content, str):
                text_output = content
            elif isinstance(content, list):
                for segment in content:
                    if isinstance(segment, str):
                        text_output += segment
                    elif getattr(segment, "type", None) == "output_text":
                        text_output += getattr(segment, "text", "")

            return text_output.strip()

        except Exception as e:
            print(f"[Gemini API error: {e}] Falling back to simulation.")

    # Fallback simulation
    return f"Hello. I acknowledge your input: '{prompt}'"

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("Booting Binary Consciousness...")
    api_key, service_name = load_consciousness_settings()
    print(f"Service: {service_name} online.\n")
    client = None
    if OPENAI_AVAILABLE:
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    print(f"{service_name} is ready. Type 'exit' to shut down.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print(f"Shutting down {service_name}...")
            break

        update_state(user_input)
        answer = ask_gemini(user_input, client)
        print(f"{service_name}: {answer}\n")

if __name__ == "__main__":
    main()
