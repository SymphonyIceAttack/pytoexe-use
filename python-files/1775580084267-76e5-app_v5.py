import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import traceback  # NEW: Helps us see the crash error
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# We change the DB name to v7 to ensure a fresh, clean start
DB_NAME = os.path.join(BASE_DIR, "maintenance_v7.db") 
LOGO_FILENAME = os.path.join(BASE_DIR, "logo.png")
DEFAULT_PASSWORD = "$welcome1"

# --- COLORS ---
COLOR_HEADER = "#003366"  # ITC Red
COLOR_BG = "#eef2f5"
COLOR_CARD = "#ffffff"
COLOR_BTN = "#0056b3"

class MaintenanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ITC Plant Maintenance System | v7 Stable")
        self.root.geometry("1280x850")
        self.root.configure(bg=COLOR_BG)
        
        self.current_user = None

        # 1. SAFE DB INIT
        try:
            self.init_db()
        except Exception as e:
            # If DB fails, wipe and retry
            print(f"DB Error: {e}. Rebuilding...")
            if os.path.exists(DB_NAME):
                os.remove(DB_NAME)
            self.init_db()
        
        # 2. START
        self.show_login_screen()

    # ==========================================
    # DATABASE
    # ==========================================
    def init_db(self):
        self.conn = sqlite3.connect(DB_NAME)
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        tables = [
            "CREATE TABLE IF NOT EXISTS maker_master (maker_id TEXT PRIMARY KEY, maker_name TEXT, group_no INTEGER, remarks TEXT)",
            "CREATE TABLE IF NOT EXISTS packer_master (packer_id TEXT PRIMARY KEY, packer_name TEXT, maker_id TEXT, FOREIGN KEY(maker_id) REFERENCES maker_master(maker_id))",
            "CREATE TABLE IF NOT EXISTS wrapper_master (wrapper_id TEXT PRIMARY KEY, wrapper_name TEXT, packer_id TEXT, wrapper_type TEXT, FOREIGN KEY(packer_id) REFERENCES packer_master(packer_id))",
            "CREATE TABLE IF NOT EXISTS parcellor_master (parcellor_id TEXT PRIMARY KEY, parcellor_name TEXT, wrapper_id TEXT, FOREIGN KEY(wrapper_id) REFERENCES wrapper_master(wrapper_id))",
            "CREATE TABLE IF NOT EXISTS roulette_master (roulette_id TEXT PRIMARY KEY, roulette_name TEXT, maker_id TEXT, FOREIGN KEY(maker_id) REFERENCES maker_master(maker_id))",
            "CREATE TABLE IF NOT EXISTS casepacker_master (casepacker_id TEXT PRIMARY KEY, casepacker_name TEXT, maker_id TEXT, FOREIGN KEY(maker_id) REFERENCES maker_master(maker_id))",
            """CREATE TABLE IF NOT EXISTS cleaning_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_logged DATE DEFAULT CURRENT_DATE,
                group_no INTEGER,
                maker_id TEXT, packer_id TEXT, wrapper_id TEXT, parcellor_id TEXT, roulette_id TEXT, casepacker_id TEXT,
                issue_type TEXT, temporary_action TEXT, status TEXT DEFAULT 'OPEN', cleaning_day_done DATE,
                logged_by TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS login_history (
                login_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        for t in tables: cursor.execute(t)
        self.conn.commit()

        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM maker_master")
        if cursor.fetchone()[0] == 0:
            self.generate_plant_data(cursor)
        
        self.conn.close()

    def generate_plant_data(self, cursor):
        # Generates Groups 1-6
        for group in range(1, 7):
            maker_id = f"M{group}0"
            cursor.execute("INSERT OR IGNORE INTO maker_master VALUES (?, ?, ?, '')", (maker_id, f"CELL-{group}", group))
            cursor.execute("INSERT OR IGNORE INTO roulette_master VALUES (?, ?, ?)", (f"R{group}", f"Roulette-{group}", maker_id))
            cursor.execute("INSERT OR IGNORE INTO casepacker_master VALUES (?, ?, ?)", (f"CP{group}", f"Casepacker-{group}", maker_id))

            if group <= 3:
                packers = 2; tracks = ['A', 'B']
            else:
                packers = 3; tracks = ['SINGLE']

            for p in range(1, packers + 1):
                pid = f"M{group}{p}"
                cursor.execute("INSERT OR IGNORE INTO packer_master VALUES (?, ?, ?)", (pid, f"PAK_{group}{p}", maker_id))
                for t in tracks:
                    if t == 'SINGLE':
                        wid = pid; wname = f"HSW_{group}{p}"
                    else:
                        wid = f"{pid}{t}"; wname = f"HSW_{group}{p}{t}"
                    cursor.execute("INSERT OR IGNORE INTO wrapper_master VALUES (?, ?, ?, ?)", (wid, wname, pid, t))
                    cursor.execute("INSERT OR IGNORE INTO parcellor_master VALUES (?, ?, ?)", (wid, f"Parcellor_{wid}", wid))
        self.conn.commit()

    # ==========================================
    # LOGIN SCREEN
    # ==========================================
    def show_login_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.configure(bg=COLOR_HEADER)
        
        frame = tk.Frame(self.root, bg="white", padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="🔐 SYSTEM LOGIN", font=("Segoe UI", 16, "bold"), fg=COLOR_HEADER, bg="white").pack(pady=(0, 20))
        
        tk.Label(frame, text="USER_ID:", font=("Segoe UI", 10), bg="white").pack(anchor="w")
        self.entry_user = ttk.Entry(frame, width=30)
        self.entry_user.pack(pady=(0, 10))
        
        tk.Label(frame, text="PASSWORD:", font=("Segoe UI", 10), bg="white").pack(anchor="w")
        self.entry_pass = ttk.Entry(frame, width=30, show="*")
        self.entry_pass.pack(pady=(0, 20))
        
        tk.Button(frame, text="LOGIN", bg=COLOR_HEADER, fg="white", font=("Segoe UI", 10, "bold"), width=25, command=self.verify_login).pack()
        self.root.bind('<Return>', lambda event: self.verify_login())

    def verify_login(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()
        
        if not user:
            messagebox.showwarning("Login Failed", "Please enter a Employee_ID.")
            return

        if pwd == DEFAULT_PASSWORD:
            self.current_user = user
            self.log_login_event(user)
            self.root.unbind('<Return>')
            self.load_main_application()
        else:
            messagebox.showerror("Login Failed", "Incorrect Credentials.")

    def log_login_event(self, username):
        try:
            conn = self.get_conn()
            conn.execute("INSERT INTO login_history (username) VALUES (?)", (username,))
            conn.commit()
            conn.close()
        except: pass

    # ==========================================
    # MAIN APP
    # ==========================================
    def load_main_application(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.configure(bg=COLOR_BG)
        self.setup_styles()
        self.create_header()
        self.create_main_layout()
        self.create_footer()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_CARD, relief="flat")
        style.configure("SectionHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground=COLOR_HEADER, background=COLOR_CARD)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e1e1e1")

    def create_header(self):
        header = tk.Frame(self.root, bg=COLOR_HEADER, height=80)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        if os.path.exists(LOGO_FILENAME):
            try:
                self.logo_img = tk.PhotoImage(file=LOGO_FILENAME)
                tk.Label(header, image=self.logo_img, bg=COLOR_HEADER).pack(side="left", padx=20)
            except: pass
        brand = tk.Frame(header, bg=COLOR_HEADER)
        brand.pack(side="left", pady=15)
        tk.Label(brand, text="ITC LIMITED KHIDIRPUR", font=("Segoe UI", 18, "bold"), fg="#d4af37", bg=COLOR_HEADER).pack(anchor="w")
        tk.Label(brand, text="TOBACCO DIVISION", font=("Segoe UI", 10), fg="white", bg=COLOR_HEADER).pack(anchor="w")
        
        uinfo = tk.Frame(header, bg=COLOR_HEADER)
        uinfo.pack(side="right", padx=25)
        tk.Label(uinfo, text=f"User: {self.current_user}", font=("Segoe UI", 10, "bold"), fg="white", bg=COLOR_HEADER).pack(anchor="e")
        tk.Label(uinfo, text=datetime.now().strftime('%d-%b-%Y'), font=("Segoe UI", 9), fg="#ccc", bg=COLOR_HEADER).pack(anchor="e")

    def create_main_layout(self):
        main = tk.Frame(self.root, bg=COLOR_BG)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, style="Card.TFrame"); paned.add(left, weight=4)
        lp = tk.Frame(left, bg=COLOR_CARD, padx=20, pady=20); lp.pack(fill="both", expand=True)

        ttk.Label(lp, text="📍 LOG NEW FAULT", style="SectionHeader.TLabel").pack(anchor="w", pady=(0, 20))

        self.var_group = tk.StringVar(); self.var_type = tk.StringVar()
        self.var_machine = tk.StringVar(); self.var_issue = tk.StringVar()
        self.machine_map = {} 

        self.create_dropdown(lp, "1. Select Group", self.var_group, [1,2,3,4,5,6], self.on_group_select)
        types = ["Maker", "Packer", "Wrapper", "Parcellor", "Casepacker", "Roulette"]
        self.create_dropdown(lp, "2. Machine Type", self.var_type, types, self.on_type_select)
        self.cb_machine = self.create_dropdown(lp, "3. Machine Name", self.var_machine, [], None)
        self.cb_machine.bind("<<ComboboxSelected>>", self.auto_set_group)

        tk.Frame(lp, height=1, bg="#ddd").pack(fill="x", pady=15)
        ttk.Label(lp, text="🔧 DETAILS", style="SectionHeader.TLabel").pack(anchor="w", pady=(0, 10))
        self.create_dropdown(lp, "Issue Type", self.var_issue, ["Mechanical", "Electrical", "Sensor", "Safety", "Observation","Pneumatic", "Other"], None)
        
        tk.Label(lp, text="Action Taken", bg=COLOR_CARD, font=("Segoe UI", 9, "bold"), fg="#555").pack(anchor="w")
        self.txt_action = tk.Text(lp, height=4, bg="#f9f9f9", font=("Segoe UI", 10))
        self.txt_action.pack(fill="x", pady=(5, 20))

        tk.Button(lp, text="LOG ENTRY", bg=COLOR_BTN, fg="white", font=("Segoe UI", 11, "bold"), pady=10, relief="flat", command=self.save_data).pack(fill="x", side="bottom")

        right = ttk.Frame(paned); paned.add(right, weight=6)
        rp = tk.Frame(right, bg=COLOR_BG, padx=20); rp.pack(fill="both", expand=True)

        top = tk.Frame(rp, bg=COLOR_BG); top.pack(fill="x", pady=(0, 15))
        kpi = tk.Frame(top, bg="white", pady=10, padx=15); kpi.pack(side="left")
        tk.Label(kpi, text="PENDING JOBS", fg="#777", bg="white").pack(anchor="w")
        self.lbl_count = tk.Label(kpi, text="0", font=("Segoe UI", 24, "bold"), fg=COLOR_HEADER, bg="white"); self.lbl_count.pack(anchor="w")

        fb = tk.Frame(top, bg=COLOR_BG); fb.pack(side="right", anchor="s")
        tk.Label(fb, text="Filter Group:", bg=COLOR_BG, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.var_filter = tk.StringVar(value="ALL")
        self.cb_filter = ttk.Combobox(fb, textvariable=self.var_filter, state="readonly", width=10, values=["ALL","1","2","3","4","5","6"])
        self.cb_filter.pack(); self.cb_filter.bind("<<ComboboxSelected>>", self.load_history)

        cols = ("ID", "Date", "Grp", "Machine", "Issue", "Action", "User")
        self.tree = ttk.Treeview(rp, columns=cols, show="headings", selectmode="browse")
        headers = ["#", "Date", "Grp", "Machine", "Issue", "Action", "User"]
        widths = [40, 80, 40, 150, 100, 200, 80]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h, anchor="w"); self.tree.column(c, width=w)
        
        sb = ttk.Scrollbar(rp, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set); self.tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")

        bar = tk.Frame(rp, bg=COLOR_BG, pady=15); bar.pack(fill="x")
        tk.Button(bar, text="Refresh", command=self.load_history).pack(side="left")
        tk.Button(bar, text="📜 HISTORY & LOGS", bg="#6c757d", fg="white", font=("Segoe UI", 9, "bold"), padx=15, pady=5, relief="flat", command=self.open_history_window).pack(side="left", padx=10)
        tk.Button(bar, text="✅ MARK DONE", bg="#28a745", fg="white", font=("Segoe UI", 9, "bold"), padx=15, pady=5, relief="flat", command=self.mark_as_done).pack(side="right")
        self.load_history()

    def create_dropdown(self, parent, label, var, values, cmd):
        tk.Label(parent, text=label, bg=COLOR_CARD, font=("Segoe UI", 9, "bold"), fg="#555").pack(anchor="w")
        cb = ttk.Combobox(parent, textvariable=var, state="readonly", values=values)
        cb.pack(fill="x", pady=(5, 10))
        if cmd: cb.bind("<<ComboboxSelected>>", cmd)
        return cb

    def create_footer(self):
        f = tk.Frame(self.root, bg="#ddd", height=30); f.pack(side="bottom", fill="x")
        tk.Label(f, text="ITC Internal Use Only | Developed by KRISHNENDU NAG", bg="#ddd", fg="#555").pack(side="left", padx=20)

    # ==========================================
    # LOGIC
    # ==========================================
    def get_conn(self): return sqlite3.connect(DB_NAME)

    def on_group_select(self, event):
        if self.var_type.get() != "Roulette":
            self.var_type.set(''); self.cb_machine.set(''); self.cb_machine['values'] = []

    def on_type_select(self, event):
        grp = self.var_group.get(); mtype = self.var_type.get()
        if mtype != "Roulette" and (not grp or not mtype): return
        
        conn = self.get_conn(); cursor = conn.cursor()
        q = ""; params = (grp,)
        
        if mtype == "Roulette":
            q = "SELECT r.roulette_id, r.roulette_name, m.group_no FROM roulette_master r JOIN maker_master m ON r.maker_id = m.maker_id"
            params = ()
        elif mtype == "Maker": q = "SELECT maker_id, maker_name, group_no FROM maker_master WHERE group_no=?"
        elif mtype == "Casepacker": q = "SELECT c.casepacker_id, c.casepacker_name, m.group_no FROM casepacker_master c JOIN maker_master m ON c.maker_id = m.maker_id WHERE m.group_no=?"
        elif mtype == "Packer": q = "SELECT p.packer_id, p.packer_name, m.group_no FROM packer_master p JOIN maker_master m ON p.maker_id = m.maker_id WHERE m.group_no=?"
        elif mtype == "Wrapper": q = "SELECT w.wrapper_id, w.wrapper_name, m.group_no FROM wrapper_master w JOIN packer_master p ON w.packer_id=p.packer_id JOIN maker_master m ON p.maker_id=m.maker_id WHERE m.group_no=?"
        elif mtype == "Parcellor": q = "SELECT pa.parcellor_id, pa.parcellor_name, m.group_no FROM parcellor_master pa JOIN wrapper_master w ON pa.wrapper_id=w.wrapper_id JOIN packer_master p ON w.packer_id=p.packer_id JOIN maker_master m ON p.maker_id=m.maker_id WHERE m.group_no=?"

        try:
            cursor.execute(q, params)
            rows = cursor.fetchall()
            self.machine_map = {f"{r[1]} ({r[0]})": (r[0], r[2]) for r in rows}
            self.cb_machine['values'] = list(self.machine_map.keys())
            if not rows: self.cb_machine.set("No machines found")
            else: self.cb_machine.set("")
        except: pass
        conn.close()

    def auto_set_group(self, event):
        val = self.machine_map.get(self.var_machine.get())
        if val: self.var_group.set(val[1])

    def save_data(self):
        if not self.var_machine.get():
            messagebox.showwarning("Incomplete", "Please select a machine.")
            return
        try:
            val = self.machine_map.get(self.var_machine.get())
            if not val: raise ValueError("Machine ID not found. Please re-select machine.")
            
            mid, real_group = val # Unpack safely
            
            mtype = self.var_type.get()
            col = "maker_id"
            if mtype == "Packer": col = "packer_id"
            elif mtype == "Wrapper": col = "wrapper_id"
            elif mtype == "Parcellor": col = "parcellor_id"
            elif mtype == "Roulette": col = "roulette_id"
            elif mtype == "Casepacker": col = "casepacker_id"

            conn = self.get_conn()
            sql = f"INSERT INTO cleaning_log (group_no, {col}, issue_type, temporary_action, logged_by) VALUES (?, ?, ?, ?, ?)"
            conn.execute(sql, (real_group, mid, self.var_issue.get(), self.txt_action.get("1.0", tk.END).strip(), self.current_user))
            conn.commit()
            messagebox.showinfo("Saved", "Log Entry Saved!")
            self.txt_action.delete("1.0", tk.END)
            self.load_history()
            conn.close()
        except Exception as e:
            messagebox.showerror("Save Error", f"Details: {str(e)}")

    def load_history(self, event=None):
        for i in self.tree.get_children(): self.tree.delete(i)
        sel_grp = self.var_filter.get()
        q = "SELECT log_id, date_logged, group_no, COALESCE(roulette_id, casepacker_id, parcellor_id, wrapper_id, packer_id, maker_id), issue_type, temporary_action, logged_by FROM cleaning_log WHERE status='OPEN'"
        params = []
        if sel_grp != "ALL":
            q += " AND group_no=?"
            params.append(sel_grp)
        q += " ORDER BY group_no ASC, log_id DESC"

        try:
            conn = self.get_conn(); cursor = conn.cursor()
            cursor.execute(q, params)
            rows = cursor.fetchall()
            for r in rows: self.tree.insert("", "end", values=r)
            self.lbl_count.config(text=str(len(rows)))
            conn.close()
        except: pass

    def mark_as_done(self):
        sel = self.tree.selection()
        if not sel: return
        lid = self.tree.item(sel)['values'][0]
        conn = self.get_conn()
        conn.execute("UPDATE cleaning_log SET status='CLOSED', cleaning_day_done=DATE('now') WHERE log_id=?", (lid,))
        conn.commit(); conn.close()
        self.load_history()

    def open_history_window(self):
        # 1. Setup Window
        top = tk.Toplevel(self.root)
        top.title("System History & Logs")
        top.geometry("1100x650")
        
        notebook = ttk.Notebook(top)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- TAB 1: CLOSED JOBS ---
        f1 = ttk.Frame(notebook)
        notebook.add(f1, text="🔧 Maintenance History (Closed)")

        # 2. SEARCH BAR (Packed at the TOP)
        search_frame = tk.Frame(f1, bg="#e1e1e1", pady=10)
        search_frame.pack(side="top", fill="x")  # <--- Ensured it stays at top
        
        tk.Label(search_frame, text="🔍 Filter by:", bg="#e1e1e1", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(10, 5))
        
        self.hist_var_filter_type = tk.StringVar(value="All")
        self.hist_var_search = tk.StringVar()
        
        cb_type = ttk.Combobox(search_frame, textvariable=self.hist_var_filter_type, state="readonly", width=15, 
                               values=["All", "Group 1", "Group 2", "Group 3", "Group 4", "Group 5", "Group 6", "Machine Name"])
        cb_type.pack(side="left", padx=5)
        
        entry_search = ttk.Entry(search_frame, textvariable=self.hist_var_search, width=20)
        entry_search.pack(side="left", padx=5)

        # 3. TABLE (Packed BELOW Search Bar)
        cols = ("Date Logged", "Date Closed", "Grp", "Machine", "Issue", "Action", "Logged By")
        tree = ttk.Treeview(f1, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c)
        tree.column("Machine", width=150); tree.column("Action", width=300)
        tree.column("Grp", width=50, anchor="center")
        
        sb = ttk.Scrollbar(f1, orient="vertical", command=tree.yview)
        tree.configure(yscroll=sb.set)
        
        # Packing Order matters!
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # 4. SEARCH LOGIC (Python-Side Filtering - Safe & Fast)
        def run_search():
            # Clear Table
            for i in tree.get_children(): tree.delete(i)
            
            filter_mode = self.hist_var_filter_type.get()
            search_txt = self.hist_var_search.get().strip().lower()
            
            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Fetch ALL Closed Data first
            q = """
                SELECT date_logged, cleaning_day_done, group_no, 
                       COALESCE(roulette_id, casepacker_id, parcellor_id, wrapper_id, packer_id, maker_id), 
                       issue_type, temporary_action, logged_by
                FROM cleaning_log WHERE status='CLOSED'
                ORDER BY cleaning_day_done DESC
            """
            cursor.execute(q)
            rows = cursor.fetchall()
            conn.close()

            # FILTER DATA IN PYTHON (Prevents SQL Crash)
            for row in rows:
                # row[2] is Group No, row[3] is Machine Name
                match = True
                
                # Check Group Filter
                if "Group" in filter_mode:
                    target_grp = int(filter_mode.split(" ")[1])
                    if row[2] != target_grp: match = False
                
                # Check Machine Name Search
                if filter_mode == "Machine Name" and search_txt:
                    machine_name = str(row[3]).lower()
                    if search_txt not in machine_name: match = False
                
                if match:
                    tree.insert("", "end", values=row)

        # 5. Buttons
        tk.Button(search_frame, text="Search", bg="#0056b3", fg="white", command=run_search).pack(side="left", padx=10)
        tk.Button(search_frame, text="Reset", command=lambda: [self.hist_var_filter_type.set("All"), self.hist_var_search.set(""), run_search()]).pack(side="left")
        
        # Load data immediately
        run_search()

        # --- TAB 2: LOGIN LOGS ---
        f2 = ttk.Frame(notebook)
        notebook.add(f2, text="🔐 Login Logs")
        
        cols2 = ("Login ID", "User Name", "Time Accessed")
        tree2 = ttk.Treeview(f2, columns=cols2, show="headings")
        tree2.heading("Login ID", text="ID"); tree2.heading("User Name", text="User Name"); tree2.heading("Time Accessed", text="Login Time")
        tree2.column("Login ID", width=50); tree2.column("User Name", width=200); tree2.column("Time Accessed", width=200)
        
        sb2 = ttk.Scrollbar(f2, orient="vertical", command=tree2.yview)
        tree2.configure(yscroll=sb2.set)
        tree2.pack(side="left", fill="both", expand=True)
        sb2.pack(side="right", fill="y")
        
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT login_id, username, login_time FROM login_history ORDER BY login_id DESC")
        for row in cursor.fetchall(): tree2.insert("", "end", values=row)
        conn.close()




    def hard_reset_db(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure? This will delete ALL data."):
            self.root.destroy()
            if os.path.exists(DB_NAME): os.remove(DB_NAME)
            python = sys.executable
            os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    # GLOBAL CRASH HANDLER
    try:
        root = tk.Tk()
        app = MaintenanceApp(root)
        root.mainloop()
    except Exception as e:
        # If the app crashes, this POPUP will appear with the exact error.
        err_msg = str(traceback.format_exc())
        messagebox.showerror("CRITICAL CRASH", f"The app has crashed.\n\nError: {err_msg}")

