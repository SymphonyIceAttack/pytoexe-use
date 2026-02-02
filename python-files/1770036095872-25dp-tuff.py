import random
import time
import sys

fake_files = [
    "Accessing mainframe...",
    "Bypassing firewall...",
    "Decrypting password hash...",
    "Establishing secure tunnel...",
    "Uploading payload...",
    "Extracting data packets...",
    "Compiling exploit...",
    "Injection successful.",
    "Covering tracks...",
    "Operation complete."
]

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"

def type_effect(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

print("\nINITIALIZING SYSTEM...\n")
time.sleep(1)

for _ in range(40):
    line = "".join(random.choice(chars) for _ in range(random.randint(40, 70)))
    print(line)
    time.sleep(0.05)

print("\n")

for step in fake_files:
    type_effect(step)
    for i in range(0, 101, random.randint(5, 20)):
        sys.stdout.write(f"\r[{('=' * (i//5)).ljust(20)}] {i}%")
        sys.stdout.flush()
        time.sleep(0.1)
    print("\n")

print(">>> ACCESS GRANTED <<<")
print(">>> WELCOME, ADMIN <<<")
