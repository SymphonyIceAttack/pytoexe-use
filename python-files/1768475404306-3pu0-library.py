import csv 
 
filename = "library.csv" 
 
def add_book(): 
    with open(filename, "a", newline='') as f: 
        writer = csv.writer(f) 
        book_id = input("Enter Book ID: ") 
        title = input("Enter Title: ") 
        author = input("Enter Author: ") 
        price = input("Enter Price: ") 
        status = "Available" 
        writer.writerow([book_id, title, author, price, status]) 
        print("Book added successfully!\n") 
 
def display_books(): 
    with open(filename, "r") as f: 
        reader = csv.reader(f) 
        for row in reader: 
            print(row) 
 
def search_book(): 
    key = input("Enter Book ID or Title to search: ") 
    found = False 
    with open(filename, "r") as f: 
        reader = csv.reader(f) 
        for row in reader: 
            if key in row: 
                print("Book found:", row) 
                found = True 
    if not found: 
        print("Book not found.\n") 
 
def issue_book(): 
    temp = [] 
    book_id = input("Enter Book ID to issue: ") 
    with open(filename, "r") as f: 
        reader = csv.reader(f) 
        for row in reader: 
            if row[0] == book_id and row[4] == "Available": 
                row[4] = "Issued" 
                print("Book issued successfully!") 
            temp.append(row) 
    with open(filename, "w", newline='') as f: 
        writer = csv.writer(f) 
        writer.writerows(temp) 
 
def return_book(): 
    temp = [] 
    book_id = input("Enter Book ID to return: ") 
    with open(filename, "r") as f: 
        reader = csv.reader(f) 
        for row in reader: 
            if row[0] == book_id and row[4] == "Issued": 
                row[4] = "Available" 
                print("Book returned successfully!") 
            temp.append(row) 
    with open(filename, "w", newline='') as f: 
        writer = csv.writer(f) 
        writer.writerows(temp) 
 
def main(): 
    while True: 
        print("\n--- Library Management System ---") 
        print("1. Add Book") 
        print("2. Display Books") 
        print("3. Search Book") 
        print("4. Issue Book") 
        print("5. Return Book") 
        print("6. Exit") 
 
        ch = input("Enter your choice: ") 
        if ch == '1': 
            add_book() 
        elif ch == '2': 
            display_books() 
        elif ch == '3': 
            search_book() 
        elif ch == '4': 
            issue_book() 
        elif ch == '5': 
            return_book() 
        elif ch == '6': 
            print("Exiting...") 
            break 
        else: 
            print("Invalid choice!") 
 
main() 
 
