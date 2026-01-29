import tkinter as tk
from tkinter import messagebox

# Assuming 'root', 'cur', and 'conn' are already defined in your main script

def manage_items():
    manage_win = tk.Toplevel(root)
    manage_win.title("Manage Items")
    manage_win.geometry("800x500")

    # This list will keep track of the Database IDs in the same order as the Listbox
    displayed_ids = []

    # --- Search UI ---
    search_frame = tk.Frame(manage_win)
    search_frame.pack(pady=5, fill="x")
    tk.Label(search_frame, text="Search:").pack(side="left", padx=5)
    
    search_entry = tk.Entry(search_frame)
    search_entry.pack(side="left", fill="x", expand=True, padx=5)

    # --- Item Listbox ---
    item_list = tk.Listbox(manage_win, font=("Arial", 12))
    item_list.pack(fill="both", expand=True, padx=10, pady=5)

    MIN_STOCK = 5

    # --- Logic: Load Data ---
    def load_items(query=""):
        item_list.delete(0, tk.END)
        displayed_ids.clear()  # Clear the ID mapping
        
        # We fetch the 'id' but don't show it in the string display
        cur.execute("""SELECT id, item_name, barcode, quantity 
                       FROM items 
                       WHERE item_name LIKE ? OR barcode LIKE ? OR item_code LIKE ? 
                       ORDER BY item_name""",
                    (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        for row in cur.fetchall():
            db_id, name, barcode, qty = row
            display_text = f"{name} | Barcode: {barcode} | Qty: {qty}"
            
            if qty <= MIN_STOCK:
                display_text += " ⚠ LOW STOCK"
            
            item_list.insert(tk.END, display_text)
            displayed_ids.append(db_id)  # Sync the database ID with the listbox index

    # --- Logic: Search ---
    def search_items(event=None):
        load_items(search_entry.get())
    
    search_entry.bind("<KeyRelease>", search_items)

    # --- Logic: Edit ---
    def edit_item():
        selection = item_list.curselection()
        if not selection:
            messagebox.showwarning("Select Item", "Please select an item from the list first.")
            return
        
        index = selection[0]
        item_db_id = displayed_ids[index] # Get the real ID from our hidden list

        cur.execute("SELECT item_name, item_code, barcode, quantity FROM items WHERE id=?", (item_db_id,))
        item_data = cur.fetchone()

        edit_win = tk.Toplevel(manage_win)
        edit_win.title("Edit Item")
        edit_win.geometry("400x350")

        # Entry fields
        labels = ["Item Name", "Item Code", "Barcode", "Quantity"]
        entries = []
        for i, label_text in enumerate(labels):
            tk.Label(edit_win, text=label_text).pack(pady=(5, 0))
            entry = tk.Entry(edit_win)
            entry.pack(pady=2)
            entry.insert(0, str(item_data[i]))
            entries.append(entry)

        def save_item():
            try:
                # We update by ID so we can safely change the Barcode text if needed
                cur.execute("""UPDATE items 
                               SET item_name=?, item_code=?, barcode=?, quantity=? 
                               WHERE id=?""",
                            (entries[0].get(), entries[1].get(), entries[2].get(), int(entries[3].get()), item_db_id))
                conn.commit()
                messagebox.showinfo("Success", "Item updated successfully!")
                edit_win.destroy()
                load_items(search_entry.get()) # Refresh the list
            except Exception as e:
                messagebox.showerror("Error", f"Update failed: {e}")

        tk.Button(edit_win, text="Save Changes", command=save_item, bg="green", fg="white").pack(pady=20)

    # --- Logic: Delete ---
    def delete_item():
        selection = item_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        item_db_id = displayed_ids[index]
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            cur.execute("DELETE FROM items WHERE id=?", (item_db_id,))
            conn.commit()
            load_items(search_entry.get())
            messagebox.showinfo("Deleted", "Item removed from inventory.")

    # --- Action Buttons ---
    btn_frame = tk.Frame(manage_win)
    btn_frame.pack(pady=10)
    
    tk.Button(btn_frame, text="Edit Item", command=edit_item, bg="blue", fg="white", width=15).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete Item", command=delete_item, bg="red", fg="white", width=15).pack(side="left", padx=5)

    # Initial load of data
    load_items()