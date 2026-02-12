import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from db import AddressBookDB


def _not_empty(value: str) -> bool:
    return bool(value and value.strip())


class AddressBookApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Address Book (SQLite)")
        self.geometry("1100x600")
        self.minsize(1000, 560)

        self.db = AddressBookDB("address_book.db")
        self.selected_contact_id: Optional[int] = None

        self._build_ui()
        self._load_all_contacts()

    def _build_ui(self) -> None:
        # Top: Search
        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Find by ID:").pack(side=tk.LEFT)
        self.find_id_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.find_id_var, width=10).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(top, text="Find ID", command=self.on_find_by_id).pack(side=tk.LEFT)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)

        ttk.Label(top, text="Find by Name/Surname:").pack(side=tk.LEFT)
        self.find_name_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.find_name_var, width=25).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(top, text="Search", command=self.on_search_by_name).pack(side=tk.LEFT)
        ttk.Button(top, text="Show All", command=self._load_all_contacts).pack(side=tk.LEFT, padx=(10, 0))

        # Main split: left list (scrolling) + right form
        main = ttk.Frame(self, padding=(10, 0, 10, 10))
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(main, padding=(10, 0, 0, 0))
        right.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview (scrolling menu/list)
        columns = ("id", "name", "surname", "address", "region", "phone", "passport")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("surname", text="Surname")
        self.tree.heading("address", text="Address")
        self.tree.heading("region", text="Region")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("passport", text="Passport")

        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("name", width=120)
        self.tree.column("surname", width=140)
        self.tree.column("address", width=260)
        self.tree.column("region", width=120)
        self.tree.column("phone", width=140)
        self.tree.column("passport", width=140)

        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(left, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Right: form
        ttk.Label(right, text="Contact details", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        form = ttk.Frame(right)
        form.pack(fill=tk.Y)

        self.name_var = tk.StringVar()
        self.surname_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.region_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.passport_var = tk.StringVar()

        self._add_labeled_entry(form, "Name", self.name_var, 0)
        self._add_labeled_entry(form, "Surname", self.surname_var, 1)
        self._add_labeled_entry(form, "Address", self.address_var, 2)
        self._add_labeled_entry(form, "Region", self.region_var, 3)
        self._add_labeled_entry(form, "Phone", self.phone_var, 4)
        self._add_labeled_entry(form, "Passport", self.passport_var, 5)

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, pady=(12, 0))

        ttk.Button(btns, text="New", command=self.on_new).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btns, text="Add", command=self.on_add).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(btns, text="Update", command=self.on_update).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btns, text="Delete", command=self.on_delete).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(10, 6))
        status.pack(side=tk.BOTTOM, fill=tk.X)

    def _add_labeled_entry(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky="w", pady=4)
        e = ttk.Entry(parent, textvariable=var, width=34)
        e.grid(row=row, column=1, sticky="we", pady=4, padx=(8, 0))
        parent.grid_columnconfigure(1, weight=1)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _clear_form(self) -> None:
        self.selected_contact_id = None
        self.name_var.set("")
        self.surname_var.set("")
        self.address_var.set("")
        self.region_var.set("")
        self.phone_var.set("")
        self.passport_var.set("")

    def _validate_form(self) -> Optional[str]:
        if not _not_empty(self.name_var.get()):
            return "Name is required."
        if not _not_empty(self.surname_var.get()):
            return "Surname is required."
        if not _not_empty(self.address_var.get()):
            return "Address is required."
        if not _not_empty(self.region_var.get()):
            return "Region is required."
        if not _not_empty(self.phone_var.get()):
            return "Phone is required."
        if not _not_empty(self.passport_var.get()):
            return "Passport is required."
        return None

    def _populate_tree(self, rows: list[Dict[str, Any]]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            self.tree.insert(
                "",
                tk.END,
                values=(r["id"], r["name"], r["surname"], r["address"], r["region"], r["phone"], r["passport"]),
            )
        self._set_status(f"Loaded {len(rows)} contact(s).")

    def _load_all_contacts(self) -> None:
        rows = self.db.list_contacts(limit=5000, offset=0)
        self._populate_tree(rows)
        self._clear_form()

    def on_tree_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return
        contact_id = int(values[0])
        contact = self.db.get_contact_by_id(contact_id)
        if not contact:
            return

        self.selected_contact_id = contact_id
        self.name_var.set(contact["name"])
        self.surname_var.set(contact["surname"])
        self.address_var.set(contact["address"])
        self.region_var.set(contact["region"])
        self.phone_var.set(contact["phone"])
        self.passport_var.set(contact["passport"])
        self._set_status(f"Selected ID {contact_id}")

    def on_new(self) -> None:
        self._clear_form()
        self.tree.selection_remove(self.tree.selection())
        self._set_status("New contact (form cleared).")

    def on_add(self) -> None:
        err = self._validate_form()
        if err:
            messagebox.showerror("Validation error", err)
            return

        new_id = self.db.add_contact(
            self.name_var.get(),
            self.surname_var.get(),
            self.address_var.get(),
            self.region_var.get(),
            self.phone_var.get(),
            self.passport_var.get(),
        )
        self._load_all_contacts()
        self._set_status(f"Added contact ID {new_id}")

    def on_update(self) -> None:
        if self.selected_contact_id is None:
            messagebox.showwarning("No selection", "Select a contact to update.")
            return

        err = self._validate_form()
        if err:
            messagebox.showerror("Validation error", err)
            return

        self.db.update_contact(
            self.selected_contact_id,
            self.name_var.get(),
            self.surname_var.get(),
            self.address_var.get(),
            self.region_var.get(),
            self.phone_var.get(),
            self.passport_var.get(),
        )
        self._load_all_contacts()
        self._set_status(f"Updated contact ID {self.selected_contact_id}")

    def on_delete(self) -> None:
        if self.selected_contact_id is None:
            messagebox.showwarning("No selection", "Select a contact to delete.")
            return

        cid = self.selected_contact_id
        if not messagebox.askyesno("Confirm delete", f"Delete contact ID {cid}?"):
            return

        self.db.delete_contact(cid)
        self._load_all_contacts()
        self._set_status(f"Deleted contact ID {cid}")

    def on_find_by_id(self) -> None:
        raw = self.find_id_var.get().strip()
        if not raw:
            messagebox.showinfo("Find by ID", "Enter an ID.")
            return
        try:
            cid = int(raw)
        except ValueError:
            messagebox.showerror("Invalid ID", "ID must be a number.")
            return

        contact = self.db.get_contact_by_id(cid)
        if not contact:
            messagebox.showinfo("Not found", f"No contact with ID {cid}.")
            return

        self._populate_tree([contact])
        self._set_status(f"Found contact ID {cid}")

    def on_search_by_name(self) -> None:
        q = self.find_name_var.get().strip()
        if not q:
            messagebox.showinfo("Search", "Enter a name or surname.")
            return
        rows = self.db.search_by_name(q, limit=5000)
        self._populate_tree(rows)
        self._clear_form()
        self._set_status(f"Search results for '{q}': {len(rows)} contact(s).")


if __name__ == "__main__":
    app = AddressBookApp()
    app.mainloop()
