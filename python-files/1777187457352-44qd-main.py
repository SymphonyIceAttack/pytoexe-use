import speech_recognition as sr
import pyttsx3
import webbrowser
import pyautogui
import os
from datetime import datetime
import subprocess

# -----------------
# VOICE ENGINE (FIXED)
# -----------------
engine = pyttsx3.init('sapi5')

engine.setProperty("rate", 180)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

def speak(text):
    print("Jarvis:", text)
    try:
        engine.stop()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("Voice Error:", e)

# -----------------
# RECOGNIZER
# -----------------
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.6

mic = sr.Microphone()

# CALIBRATION
with mic as source:
    print("Calibrating mic...")
    recognizer.adjust_for_ambient_noise(source, duration=1)

# -----------------
# LISTEN FUNCTION
# -----------------
def listen():
    with mic as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=4, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="en-IN").lower()
            print("You:", text)
            return text

        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            speak("Internet problem")
            return ""
        except Exception as e:
            print("Error:", e)
            return ""

# -----------------
# COMMANDS
# -----------------
def execute_command(command):

    if "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")

    elif "open google" in command:
        speak("Opening Google")
        webbrowser.open("https://google.com")

    elif "search" in command:
        query = command.replace("search", "").strip()
        speak("Searching " + query)
        webbrowser.open(f"https://www.google.com/search?q={query}")

    elif "open chrome" in command:
        subprocess.Popen("start chrome", shell=True)

    elif "open notepad" in command:
        subprocess.Popen("notepad", shell=True)

    elif "time" in command:
        speak(datetime.now().strftime("The time is %H:%M"))

    elif "type" in command:
        text = command.replace("type", "").strip()
        pyautogui.write(text, interval=0.03)

    elif "close window" in command:
        pyautogui.hotkey("alt", "f4")

    elif "volume up" in command:
        pyautogui.press("volumeup")

    elif "volume down" in command:
        pyautogui.press("volumedown")

    elif "mute" in command:
        pyautogui.press("volumemute")

    elif "shutdown" in command:
        speak("Shutting down")
        os.system("shutdown /s /t 1")

    elif "restart" in command:
        speak("Restarting")
        os.system("shutdown /r /t 1")

    elif "exit" in command or "stop jarvis" in command:
        speak("Goodbye")
        os._exit(0)

    else:
        speak("I heard " + command)

# -----------------
# START
# -----------------
speak("Jarvis is online")

# -----------------
# MAIN LOOP
# -----------------
while True:
    print("Waiting for wake word...")

    command = listen()

    if any(word in command for word in ["jarvis", "hey jarvis", "jervis, jar"]):
        speak("Yes sir")

        while True:
            command = listen()

            if not command:
                continue

            if "sleep" in command or "stop listening" in command:
                speak("Going to sleep")
                break

            execute_command(command)