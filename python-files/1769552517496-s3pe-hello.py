import time
import os
import pie 

def say(text, delay=1.2):
    print(text)
    time.sleep(delay)

# Set console title
os.system("title Windows Update")

# Fake update messages
say("Installing critical system update...")
say("Do not turn off your computer.")
say("Update 1 of 1")
time.sleep(2)

# Countdown message
for i in range(5, 0, -1):
    print(f"Shutting down in {i}...")
    time.sleep(1)

# Start shutdown (10 second delay)
os.system("shutdown /s /t 10")
