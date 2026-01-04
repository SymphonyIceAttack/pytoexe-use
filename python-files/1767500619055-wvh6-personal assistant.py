import pyttsx3
import speech_recognition as sr
import webbrowser
import datetime

engine = pyttsx3.init()
engine.setProperty('rate', 170)

def speak(text):
    engine.say(text)
    engine.runAndWait()

user_name = None

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source, phrase_time_limit=5)
        try:
            command = r.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except:
            return ""

# Predefined answers
answers = {
    "how are you": "I am fine, thank you!",
    "tell me a joke": "Why did the computer go to the doctor? Because it caught a virus!",
    "what is your name": "I am your personal assistant."
}

def assistant():
    global user_name
    while True:
        command = listen()
        if command == "":
            continue
        if "exit" in command or "quit" in command:
            speak("Goodbye!")
            break
        
        if "my name is" in command:
            user_name = command.replace("my name is", "").strip()
            speak(f"Nice to meet you, {user_name}!")
            continue
        elif "what is my name" in command:
            if user_name:
                speak(f"Your name is {user_name}")
            else:
                speak("I don't know your name yet.")
            continue

        elif "time" in command:
            time = datetime.datetime.now().strftime("%H:%M")
            speak(f"The time is {time}")
            continue

        # Web search fallback
        if "search for" in command:
            query = command.replace("search for", "").strip()
            speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            continue

        # Predefined answers
        response_found = False
        for question, answer in answers.items():
            if question in command:
                speak(answer)
                response_found = True
                break

        if not response_found:
            speak("I don't know that. But you can search for it!")
            webbrowser.open(f"https://www.google.com/search?q={command}")

# Run assistant
speak("Hello! I am your assistant. You can tell me your name.")
assistant()
