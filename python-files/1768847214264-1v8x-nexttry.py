import time
import random

# Items to “clean”
cleaning_items = {
"Temporary Files": 1247,
"Browser Cache": 543,
"Download Cache": 89,
"Recycle Bin": 156,
"Thumbnails": 2891,
"Log Files": 234
}

def format_size(count):
# Just for fun, simulate size
return f"{count * random.randint(1,3)} MB"

def scan_system():
print("🔍 Scanning system...")
total_items = sum(cleaning_items.values())
for i in range(0, 101, 5):
print(f"Scanning... {i}%")
time.sleep(0.1)
print(f"Scan complete! Found {total_items} items.\n")
for name, count in cleaning_items.items():
print(f"{name}: {count} items ({format_size(count)})")
print("\nSelect items to clean (all selected by default).")

def clean_system():
print("\n🧹 Cleaning selected items...")
for i in range(0, 101, 5):
print(f"Cleaning... {i}%")
time.sleep(0.1)
freed_size = sum([count * random.randint(1,3) for count in cleaning_items.values()])
print(f"\n✅ Cleaning complete! Freed ~{freed_size} MB.")

def main():
print("=== QuickHawk Fake Cleaner ===\n")
scan_system()

# Confirmation
confirm = input("\nDo you want to clean these items? (y/n): ").lower()
if confirm != 'y':
print("❌ Cleaning cancelled.")
return

# Backup option (simulated)
backup = input("Create backup before cleaning? (y/n): ").lower()
if backup == 'y':
print("💾 Creating backup... Done!")

clean_system()
print("\nThank you for using QuickHawk!")

if __name__ == "__main__":
main()
