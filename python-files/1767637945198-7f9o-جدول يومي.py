import os

FILE_NAME = "expenses.txt"

# Load data from file
def load_data():
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        return [line.strip().split(",") for line in f if line.strip()]

# Save data to file
def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        for item in data:
            f.write(",".join(item) + "\n")

# Add new entry (income or expense)
def add_entry(data):
    kind = input("Type (Income/Expense): ").strip()
    amount = input("Amount: ").strip()
    note = input("Note: ").strip()
    data.append([kind, amount, note])
    save_data(data)
    print("✅ Entry added successfully.")

# Show all entries
def list_entries(data):
    if not data:
        print("No entries yet.")
        return
    print("\nYour entries:")
    for i, (kind, amount, note) in enumerate(data, start=1):
        print(f"{i}. {kind} - {amount} EGP - {note}")
    print()

# Show current balance
def balance(data):
    total = 0
    for kind, amount, _ in data:
        if kind.lower() == "income":
            total += float(amount)
        elif kind.lower() == "expense":
            total -= float(amount)
    print(f"💰 Current balance: {total} EGP")

# Main menu
def main():
    data = load_data()
    menu = """
Choose an option:
1) Add Income/Expense
2) Show Entries
3) Show Balance
4) Exit
"""
    while True:
        print(menu)
        choice = input("Your choice: ").strip()
        if choice == "1":
            add_entry(data)
        elif choice == "2":
            list_entries(data)
        elif choice == "3":
            balance(data)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("⚠️ Invalid choice, try again.")

if __name__ == "__main__":
    main()