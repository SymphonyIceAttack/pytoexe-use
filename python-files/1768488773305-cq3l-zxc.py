import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import subprocess
import os
import datetime
import threading


# ---------- UTILS ----------

def reg_val(key, name):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except:
        return "Tapylmady"


def last_access(path):
    try:
        return datetime.datetime.fromtimestamp(
            os.path.getatime(path)
        ).strftime("%d.%m.%Y")
    except:
        return "Tapylmady"


def get_installed_programs():
    programs = []
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for root, path in reg_paths:
        try:
            key = winreg.OpenKey(root, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
                    name = reg_val(sub, "DisplayName")
                    if name == "Tapylmady":
                        continue

                    date = reg_val(sub, "InstallDate")
                    if len(date) == 8:
                        date = f"{date[6:8]}.{date[4:6]}.{date[:4]}"
                    else:
                        date = "Tapylmady"

                    path_loc = reg_val(sub, "InstallLocation")
                    access = last_access(path_loc) if path_loc != "Tapylmady" else "Tapylmady"
                    uninstall = reg_val(sub, "UninstallString")

                    programs.append((name, date, path_loc, access, uninstall))
                except:
                    pass
        except:
            pass
    return programs


# ---------- APP ----------

class App:
    def __init__(self, root):
        root.title("Programma Dolandyryjy")
        root.geometry("1100x600")

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        self.tab_programs()
        self.tab_files()

    # ---------- TAB 1: PROGRAMS ----------

    def tab_programs(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="programma dolandyryjy")

        self.programs = get_installed_programs()
        self.current_uninstall = None

        search = tk.StringVar()
        search.trace_add("write", lambda *_: self.update_programs(search))

        tk.Entry(tab, textvariable=search, font=("Arial", 12)).pack(fill="x", padx=40, pady=10)

        cols = ("name", "date", "path", "last")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings")

        self.tree.heading("name", text="Ady")
        self.tree.heading("date", text="Gurnama Senesi")
        self.tree.heading("path", text="Gurnama Ýoly")
        self.tree.heading("last", text="Soňky Giriş Senesi")

        self.tree.column("name", width=250)
        self.tree.column("date", width=120)
        self.tree.column("path", width=450)
        self.tree.column("last", width=150)

        self.tree.bind("<<TreeviewSelect>>", self.on_program_select)

        sb = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0))
        sb.pack(side="right", fill="y")

        # ПКМ меню
        self.prog_menu = tk.Menu(tab, tearoff=0)
        self.prog_menu.add_command(label="Açmak", command=self.open_program)
        self.prog_menu.add_command(label="Pozmak", command=self.uninstall_program)
        self.tree.bind("<Button-3>", self.show_program_menu)

        # Кнопка Pozmak
        self.btn_delete = tk.Button(
            tab,
            text="Pozmak",
            font=("Arial", 14, "bold"),
            bg="#ff8a7a",
            state="disabled",
            command=self.uninstall_program
        )
        self.btn_delete.pack(fill="x", padx=350, pady=15)

        self.update_programs(search)

    def update_programs(self, var):
        self.tree.delete(*self.tree.get_children())
        q = var.get().lower()
        for p in self.programs:
            if q in p[0].lower():
                self.tree.insert("", "end", values=p[:4])
        self.btn_delete.config(state="disabled")

    def on_program_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0])["values"][0]
        for p in self.programs:
            if p[0] == name:
                self.current_uninstall = p[4]
                self.btn_delete.config(state="normal")
                break

    def show_program_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.on_program_select(None)
            self.prog_menu.tk_popup(event.x_root, event.y_root)

    def open_program(self):
        sel = self.tree.selection()
        if not sel:
            return
        name = self.tree.item(sel[0])["values"][0]
        for p in self.programs:
            if p[0] == name and p[2] != "Tapylmady":
                if os.path.exists(p[2]):
                    os.startfile(p[2])
                else:
                    messagebox.showwarning("Duýduryş", "Programma ýoly tapylmady")
                break

    def uninstall_program(self):
        if not self.current_uninstall:
            return
        if messagebox.askyesno("Tassyklama", "Programmany pozmak isleýärsiňizmi?"):
            subprocess.Popen(self.current_uninstall, shell=True)

    # ---------- TAB 2: FILE SEARCH ----------

    def tab_files(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="faýl gözlegi")

        top = ttk.Frame(tab)
        top.pack(fill="x", pady=10)

        self.disk = tk.StringVar(value="C:")
        ttk.Combobox(top, values=["C:", "D:"], width=5, textvariable=self.disk).pack(side="left", padx=10)

        self.file_search = tk.Entry(top, font=("Arial", 12))
        self.file_search.pack(side="left", fill="x", expand=True, padx=10)

        tk.Button(top, text="Gözle", command=self.start_search).pack(side="left", padx=10)

        self.file_tree = ttk.Treeview(tab, columns=("name", "path"), show="headings")
        self.file_tree.heading("name", text="Faýlyň ady")
        self.file_tree.heading("path", text="Ýoly")
        self.file_tree.column("name", width=300)
        self.file_tree.column("path", width=700)
        self.file_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # ПКМ меню
        self.file_menu = tk.Menu(tab, tearoff=0)
        self.file_menu.add_command(label="Açmak", command=self.open_file)
        self.file_menu.add_command(label="Pozmak", command=self.delete_file)
        self.file_tree.bind("<Button-3>", self.show_file_menu)

    def start_search(self):
        self.file_tree.delete(*self.file_tree.get_children())
        threading.Thread(target=self.search_files, daemon=True).start()

    def search_files(self):
        q = self.file_search.get().lower()
        root_path = self.disk.get() + "\\"
        for root, _, files in os.walk(root_path):
            for f in files:
                if q in f.lower():
                    self.file_tree.insert("", "end", values=(f, os.path.join(root, f)))

    def show_file_menu(self, event):
        iid = self.file_tree.identify_row(event.y)
        if iid:
            self.file_tree.selection_set(iid)
            self.file_menu.tk_popup(event.x_root, event.y_root)

    def open_file(self):
        sel = self.file_tree.selection()
        if sel:
            os.startfile(self.file_tree.item(sel[0])["values"][1])

    def delete_file(self):
        sel = self.file_tree.selection()
        if not sel:
            return
        path = self.file_tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Tassyklama", "Faýly pozmak isleýärsiňizmi?"):
            try:
                os.remove(path)
                self.file_tree.delete(sel[0])
            except Exception as e:
                messagebox.showerror("Ýalňyşlyk", str(e))


# ---------- RUN ----------

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
