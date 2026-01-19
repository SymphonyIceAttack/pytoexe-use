import time
import random

cleaning_items = {
"Temporary Files": 1247,
"Browser Cache": 543,
"Download Cache": 89,
"Recycle Bin": 156,
"Thumbnails": 2891,
"Log Files": 234
}

def progress(prefix, total_steps=100):
for i in range(total_steps + 1):
percent = int(i / total_steps * 100)
bar = "#" * (percent // 2) + "-" * (50 - (percent // 2))
print(f"{prefix} |{bar}| {percent}%")
time.sleep(0.03)

def scan_system():
print("=== QuickHawk Fake Cleaner ===")
print("Scanning system...")
progress("Scanning")

total_items = sum(cleaning_items.values())
print("Scan complete!")
print(f"Found {total_items} junk items.")
for name, count in cleaning_items.items():
print(f"- {name}: {count} items")

def clean_system():
print("Cleaning selected items...")
progress("Cleaning")
freed = sum([count * random.randint(1, 3) for count in cleaning_items.values()])
print("Cleaning complete!")
print(f"Freed ~{freed} MB.")

def main():
scan_system()

confirm = input("Do you want to clean these items? (y/n): ").lower()
if confirm != "y":
print("Cleaning cancelled.")
return

backup = input("Create backup before cleaning? (y/n): ").lower()
if backup == "y":
print("Creating backup...")
time.sleep(1)
print("Backup completed!")

clean_system()
print("Done. Thank you for using QuickHawk.")

if __name__ == "__main__":
main()
