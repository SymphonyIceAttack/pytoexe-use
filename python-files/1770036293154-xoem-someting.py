import random
import time
import sys
import platform
import os
import shutil

# ANSI green color
GREEN = "\033[92m"
RESET = "\033[0m"

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+=-"

def green_print(text, delay=0.02):
    for c in text:
        sys.stdout.write(GREEN + c + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def random_code_line():
    return "".join(random.choice(chars) for _ in range(random.randint(50, 80)))

# Fake hacking intro
print(GREEN + "\nINITIALIZING TERMINAL...\n" + RESET)
time.sleep(1)

for _ in range(35):
    print(GREEN + random_code_line() + RESET)
    time.sleep(0.04)

steps = [
    "Connecting to remote node...",
    "Bypassing firewall...",
    "Decrypting secure packets...",
    "Accessing system kernel...",
    "Extracting system data..."
]

print()
for step in steps:
    green_print(step)
    for i in range(0, 101, random.randint(10, 25)):
        bar = "=" * (i // 5)
        sys.stdout.write(GREEN + f"\r[{bar.ljust(20)}] {i}%" + RESET)
        sys.stdout.flush()
        time.sleep(0.08)
    print("\n")

# REAL SYSTEM INFO
green_print("ACCESS GRANTED\n")
time.sleep(1)
green_print("=== SYSTEM SPECS ===\n")

print(GREEN + f"OS: {platform.system()} {platform.release()}" + RESET)
print(GREEN + f"Machine: {platform.machine()}" + RESET)
print(GREEN + f"Processor: {platform.processor()}" + RESET)
print(GREEN + f"Python Version: {platform.python_version()}" + RESET)

# Disk info
total, used, free = shutil.disk_usage(os.getcwd())
print(GREEN + f"Disk Total: {total // (2**30)} GB" + RESET)
print(GREEN + f"Disk Used: {used // (2**30)} GB" + RESET)
print(GREEN + f"Disk Free: {free // (2**30)} GB" + RESET)

green_print("\nOPERATION COMPLETE.")
green_print("SESSION TERMINATED.")
