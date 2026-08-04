import random
import time

print("Loading...")

for i in range(5):
    time.sleep(0.5)
    print(f"Step {i + 1}/5")

print("\nDone!")
print(f"Random Number: {random.randint(1000, 9999)}")
input("Press Enter to exit...")
