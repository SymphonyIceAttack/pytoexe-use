import time
import random
import os

# ----------------------------
# Fake Cleaner Data
# ----------------------------
cleaning_items = {
"Temporary Files": 1247,
"Browser Cache": 543,
"Download Cache": 89,
"Recycle Bin": 156,
"Thumbnails": 2891,
"Log Files": 234
}

def clear_screen():
os.system("cls" if os.name == "nt" else "clear")

def progress_bar(prefix, current, total):
bar_length = 30
filled = int(bar_length * current // total)
bar = "█" * filled + "-" * (bar_length - filled)
percent = int(current / total * 100)
print(f"{prefix} |{bar}| {percent}%")

def scan_system():
clear_screen()
print("=== QuickHawk Fake Cleaner ===\n")
print("🔍 Scanning system for junk files...\n")

total_steps = 100
for i in range(total_steps + 1):
progress_bar("Scanning", i, total_steps)
time.sleep(0.03)

total_items = sum(cleaning_items.values())
print("\n✅ Scan complete!")
print(f"Found {total_items} junk items.\n")

for name, count in cleaning_items.items():
size_mb = count * random.randint(1, 3)
print(f"[✓] {name} — {count} items (~{size_mb} MB)")

def clean_system():
print("\n🧹 Cleaning selected items...\n")

total_steps = 100
for i in range(total_steps + 1):
progress_bar("Cleaning", i, total_steps)
time.sleep(0.03)

freed_size = sum([count * random.randint(1, 3) for count in cleaning_items.values()])
print("\n✅ Cleaning complete!")
print(f"Freed ~{freed_size} MB of space.\n")

def main():
scan_system()

confirm = input("\nDo you want to clean these items? (y/n): ").lower()
if confirm != "y":
print("❌ Cleaning cancelled. Exiting.")
return

backup = input("Create backup before cleaning? (y/n): ").lower()
if backup == "y":
print("\n💾 Creating backup...")
time.sleep(1)
print("💾 Backup completed successfully!")

clean_system()
print("🎉 Your system is optimized! Thank you for using QuickHawk.")

if __name__ == "__main__":
main()
