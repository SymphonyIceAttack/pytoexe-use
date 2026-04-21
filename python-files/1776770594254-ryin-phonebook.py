import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import shutil
from datetime import datetime
import threading
import time
from collections import defaultdict
import csv

class PhoneBookPro:
    def __init__(self):
        self.db_filename = "phonebook.json"
        self.load_database()
        
        self.window = tk.Tk()
        self.window.title("دفترچه تلفن")
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 1400
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2 - 30
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.bg_dark = "#0a1628"
        self.bg_main = "#0f1f3a"
        self.bg_light = "#162a4a"
        self.bg_card = "#1a2f52"
        self.text_primary = "#ffffff"
        self.text_secondary = "#c4d4f0"
        self.accent_glow = "#7fff5f"
        self.accent_dim = "#5fbf3f"
        self.border_light = "#3a3a3a"
        self.danger = "#ff6b6b"
        self.success = "#2ecc71"
        self.search_bg = "#1a1a2e"
        
        self.window.configure(bg=self.bg_main)
        
        try:
            available_fonts = []
            for font_name in ["Vazir", "IRANSans", "Shabnam", "Tahoma"]:
                try:
                    test_font = tk.font.Font(family=font_name, size=10)
                    available_fonts.append(font_name)
                except:
                    pass
            
            if "Vazir" in available_fonts:
                self.font_title = ("Vazir", 20, "bold")
                self.font_heading = ("Vazir", 14, "bold")
                self.font_normal = ("Vazir", 12)
                self.font_small = ("Vazir", 11)
            elif "IRANSans" in available_fonts:
                self.font_title = ("IRANSans", 20, "bold")
                self.font_heading = ("IRANSans", 14, "bold")
                self.font_normal = ("IRANSans", 12)
                self.font_small = ("IRANSans", 11)
            elif "Shabnam" in available_fonts:
                self.font_title = ("Shabnam", 20, "bold")
                self.font_heading = ("Shabnam", 14, "bold")
                self.font_normal = ("Shabnam", 12)
                self.font_small = ("Shabnam", 11)
            else:
                self.font_title = ("Tahoma", 20, "bold")
                self.font_heading = ("Tahoma", 14, "bold")
                self.font_normal = ("Tahoma", 12)
                self.font_small = ("Tahoma", 11)
        except:
            self.font_title = ("Tahoma", 20, "bold")
            self.font_heading = ("Tahoma", 14, "bold")
            self.font_normal = ("Tahoma", 12)
            self.font_small = ("Tahoma", 11)
        
        self.font_english = ("Segoe UI", 11)
        
        self.columns_per_row = 3
        
        self.start_auto_backup()
        self.setup_ui()
        self.load_organized_view()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_database(self):
        if os.path.exists(self.db_filename):
            try:
                with open(self.db_filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {"contacts": []}
        else:
            self.data = {"contacts": []}
    
    def save_database(self):
        with open(self.db_filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
    
    def start_auto_backup(self):
        def backup_loop():
            while True:
                time.sleep(900)
                self.save_database()
                self.status_bar.config(text=f"💾 ذخیره خودکار در {datetime.now().strftime('%H:%M:%S')}")
                self.window.after(2000, lambda: self.status_bar.config(text="✅ آماده"))
        threading.Thread(target=backup_loop, daemon=True).start()
    
    def setup_ui(self):
        header = tk.Frame(self.window, bg=self.bg_dark, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        top_glow = tk.Frame(header, bg=self.accent_glow, height=3)
        top_glow.pack(fill="x")
        
        title_frame = tk.Frame(header, bg=self.bg_dark)
        title_frame.pack(expand=True)
        
        title_label = tk.Label(title_frame, text="📞 دفترچه تلفن", 
                               font=self.font_title, fg=self.text_primary, bg=self.bg_dark)
        title_label.pack(pady=25)
        
        bottom_glow = tk.Frame(header, bg=self.accent_glow, height=2)
        bottom_glow.pack(fill="x", side="bottom")
        
        main_container = tk.Frame(self.window, bg=self.bg_main)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)
        
        toolbar = tk.Frame(main_container, bg=self.bg_card, relief=tk.RAISED, bd=1, 
                          highlightbackground=self.border_light, highlightthickness=1)
        toolbar.pack(fill="x", pady=(0, 15))
        
        toolbar_inner = tk.Frame(toolbar, bg=self.bg_card, padx=20, pady=12)
        toolbar_inner.pack(fill="x")
        
        buttons_frame = tk.Frame(toolbar_inner, bg=self.bg_card)
        buttons_frame.pack(side="right", padx=(0, 10))
        
        add_frame = tk.Frame(buttons_frame, bg=self.success, relief=tk.RAISED, bd=1,
                            highlightbackground=self.border_light, highlightthickness=1)
        add_frame.pack(side="right", padx=5)
        add_btn = tk.Button(add_frame, text="➕ افزودن", command=self.add_contact_dialog, 
                           bg=self.success, fg=self.text_primary, font=self.font_normal,
                           padx=12, pady=5, cursor='hand2', bd=0,
                           activebackground=self.accent_glow, activeforeground=self.bg_dark)
        add_btn.pack(side="right", padx=5)
        
        merge_frame = tk.Frame(buttons_frame, bg=self.bg_light, relief=tk.RAISED, bd=1,
                              highlightbackground=self.border_light, highlightthickness=1)
        merge_frame.pack(side="right", padx=5)
        merge_btn = tk.Button(merge_frame, text="🔄 ادغام", command=self.merge_database_dialog,
                             bg=self.bg_light, fg=self.text_primary, font=self.font_normal,
                             padx=12, pady=5, cursor='hand2', bd=0,
                             activebackground=self.accent_glow, activeforeground=self.bg_dark)
        merge_btn.pack(side="right", padx=5)
        
        import_frame = tk.Frame(buttons_frame, bg=self.bg_light, relief=tk.RAISED, bd=1,
                               highlightbackground=self.border_light, highlightthickness=1)
        import_frame.pack(side="right", padx=5)
        import_btn = tk.Button(import_frame, text="📥 ورود", command=self.import_from_file,
                              bg=self.bg_light, fg=self.text_primary, font=self.font_normal,
                              padx=12, pady=5, cursor='hand2', bd=0,
                              activebackground=self.accent_glow, activeforeground=self.bg_dark)
        import_btn.pack(side="right", padx=5)
        
        backup_frame = tk.Frame(buttons_frame, bg=self.bg_light, relief=tk.RAISED, bd=1,
                               highlightbackground=self.border_light, highlightthickness=1)
        backup_frame.pack(side="right", padx=5)
        backup_btn = tk.Button(backup_frame, text="💾 ذخیره", command=self.manual_backup,
                              bg=self.bg_light, fg=self.text_primary, font=self.font_normal,
                              padx=12, pady=5, cursor='hand2', bd=0,
                              activebackground=self.accent_glow, activeforeground=self.bg_dark)
        backup_btn.pack(side="right", padx=5)
        
        export_frame = tk.Frame(buttons_frame, bg=self.bg_light, relief=tk.RAISED, bd=1,
                               highlightbackground=self.border_light, highlightthickness=1)
        export_frame.pack(side="right", padx=5)
        export_btn = tk.Button(export_frame, text="📤 خروجی", command=self.export_csv,
                              bg=self.bg_light, fg=self.text_primary, font=self.font_normal,
                              padx=12, pady=5, cursor='hand2', bd=0,
                              activebackground=self.accent_glow, activeforeground=self.bg_dark)
        export_btn.pack(side="right", padx=5)
        
        search_frame = tk.Frame(toolbar_inner, bg=self.bg_card)
        search_frame.pack(side="left")
        
        self.search_entry = tk.Entry(search_frame, width=45, font=self.font_english,
                                     bg=self.search_bg, fg=self.text_primary,
                                     relief=tk.SOLID, bd=1, insertbackground=self.text_primary,
                                     justify="right")
        self.search_entry.pack(side="left", padx=5, pady=3)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        search_icon = tk.Label(search_frame, text="🔍", font=("Segoe UI", 14), 
                               fg=self.danger, bg=self.bg_card)
        search_icon.pack(side="left", padx=(0, 10))
        
        stats_card = tk.Frame(main_container, bg=self.bg_card, relief=tk.RAISED, bd=1, 
                             highlightbackground=self.border_light, highlightthickness=1)
        stats_card.pack(fill="x", pady=(0, 15))
        
        stats_inner = tk.Frame(stats_card, bg=self.bg_card, padx=20, pady=12)
        stats_inner.pack(fill="x")
        
        self.stats_labels = {}
        stats_texts = [
            ("total", "📊 تعداد کل: 0"),
            ("orgs", "🏢 سازمان‌ها: 0"),
            ("active", "⭐ شماره‌های فعال: 0"),
            ("backup", "💾 ذخیره: هر ۱۵ دقیقه")
        ]
        
        for key, text in stats_texts:
            label = tk.Label(stats_inner, text=text, font=self.font_normal,
                            fg=self.text_primary, bg=self.bg_card)
            label.pack(side="right", padx=25)
            self.stats_labels[key] = label
        
        self.tree_container = tk.Frame(main_container, bg=self.bg_main)
        self.tree_container.pack(fill="both", expand=True)
        
        self.status_bar = tk.Label(self.window, text="✅ آماده", font=self.font_small,
                                   bg=self.bg_dark, fg=self.text_secondary, anchor="e",
                                   padx=15, pady=8)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_organized_view(self, search_keyword=""):
        if not hasattr(self, 'tree_container'):
            return
        
        for widget in self.tree_container.winfo_children():
            widget.destroy()
        
        canvas = tk.Canvas(self.tree_container, bg=self.bg_main, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.tree_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_main)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        filtered_contacts = []
        if search_keyword:
            for contact in self.data["contacts"]:
                if (search_keyword in contact.get("name", "").lower() or 
                    search_keyword in contact.get("organization", "").lower()):
                    filtered_contacts.append(contact)
        else:
            filtered_contacts = self.data["contacts"].copy()
        
        org_dict = defaultdict(list)
        no_org = []
        for contact in filtered_contacts:
            org = contact.get("organization", "").strip()
            if org:
                org_dict[org].append(contact)
            else:
                no_org.append(contact)
        
        current_row = 0
        
        for org_name, members in sorted(org_dict.items()):
            org_card = tk.Frame(scrollable_frame, bg=self.bg_card, relief=tk.RAISED, bd=1,
                               highlightbackground=self.border_light, highlightthickness=1)
            org_card.grid(row=current_row, column=0, columnspan=self.columns_per_row, 
                         sticky="ew", padx=10, pady=8)
            org_card.grid_columnconfigure(0, weight=1)
            
            org_header = tk.Frame(org_card, bg=self.bg_dark, height=50)
            org_header.pack(fill="x")
            org_header.pack_propagate(False)
            
            org_glow = tk.Frame(org_header, bg=self.accent_glow, height=2)
            org_glow.pack(fill="x", side="bottom")
            
            org_count = tk.Label(org_header, text=f"👥 {len(members)} نفر", 
                                font=self.font_normal, fg=self.text_secondary, bg=self.bg_dark)
            org_count.place(x=20, rely=0.5, anchor="w")
            
            org_icon = tk.Label(org_header, text=f"🏢 {org_name}", 
                               font=self.font_heading, fg=self.text_primary, bg=self.bg_dark)
            org_icon.place(relx=1, x=-20, rely=0.5, anchor="e")
            
            current_row += 1
            
            for i, contact in enumerate(members):
                col = i % self.columns_per_row
                if col == 0 and i > 0:
                    current_row += 1
                
                self.create_contact_card(scrollable_frame, contact, current_row, col)
            
            current_row += 1
        
        if no_org:
            no_org_card = tk.Frame(scrollable_frame, bg=self.bg_card, relief=tk.RAISED, bd=1,
                                  highlightbackground=self.border_light, highlightthickness=1)
            no_org_card.grid(row=current_row, column=0, columnspan=self.columns_per_row,
                            sticky="ew", padx=10, pady=8)
            no_org_card.grid_columnconfigure(0, weight=1)
            
            no_org_header = tk.Frame(no_org_card, bg=self.bg_dark, height=50)
            no_org_header.pack(fill="x")
            no_org_header.pack_propagate(False)
            
            no_org_count = tk.Label(no_org_header, text=f"👥 {len(no_org)} نفر", 
                                   font=self.font_normal, fg=self.text_secondary, bg=self.bg_dark)
            no_org_count.place(x=20, rely=0.5, anchor="w")
            
            no_org_title = tk.Label(no_org_header, text="📋 بدون سازمان", 
                                   font=self.font_heading, fg=self.text_primary, bg=self.bg_dark)
            no_org_title.place(relx=1, x=-20, rely=0.5, anchor="e")
            
            current_row += 1
            
            for i, contact in enumerate(no_org):
                col = i % self.columns_per_row
                if col == 0 and i > 0:
                    current_row += 1
                
                self.create_contact_card(scrollable_frame, contact, current_row, col)
            
            current_row += 1
        
        for col in range(self.columns_per_row):
            scrollable_frame.grid_columnconfigure(col, weight=1)
        
        self.update_statistics()
    
    def create_contact_card(self, parent, contact, row, col):
        card_width = 380
        
        card = tk.Frame(parent, bg=self.bg_light, relief=tk.FLAT, bd=1,
                       highlightbackground=self.border_light, highlightthickness=1,
                       width=card_width)
        card.grid(row=row, column=col, padx=8, pady=5, sticky="nsew")
        card.grid_propagate(False)
        card.config(width=card_width, height=250)
        
        display_name = contact.get('name', 'بدون نام')
        name_label = tk.Label(card, text=f"👤 {display_name}", 
                              font=self.font_heading, fg=self.text_primary, 
                              bg=self.bg_light, wraplength=350, justify="right")
        name_label.pack(pady=(10, 5))
        
        sep1 = tk.Frame(card, bg=self.accent_dim, height=1)
        sep1.pack(fill="x", padx=10, pady=5)
        
        phones_frame = tk.Frame(card, bg=self.bg_light)
        phones_frame.pack(fill="x", padx=155, pady=5)
        
        for phone in contact.get("phones", []):
            color = self.accent_glow if phone.get("is_active") else self.danger
            status = "✅" if phone.get("is_active") else "❌"
            phone_text = f"{phone['number']} {status}"
            
            phone_btn = tk.Button(phones_frame, text=phone_text, font=self.font_english,
                                 fg=color, bg=self.bg_light, bd=0, cursor='hand2',
                                 activebackground=self.bg_light,
                                 command=lambda num=phone['number']: self.copy_to_clipboard(num))
            phone_btn.pack(anchor="center", pady=2)
        
        sep2 = tk.Frame(card, bg=self.accent_dim, height=1)
        sep2.pack(fill="x", padx=10, pady=5)
        
        btn_frame = tk.Frame(card, bg=self.bg_light)
        btn_frame.pack(fill="x", padx=155, pady=8)
        
        edit_btn = tk.Button(btn_frame, text="✏️", font=self.font_small,
                            bg=self.bg_card, fg=self.text_primary, width=3,
                            cursor='hand2', bd=0,
                            command=lambda: self.edit_contact_dialog(contact))
        edit_btn.pack(side="left", padx=3)
        
        active_btn = tk.Button(btn_frame, text="⭐", font=self.font_small,
                              bg=self.bg_card, fg=self.accent_glow, width=3,
                              cursor='hand2', bd=0,
                              command=lambda: self.set_active_phones(contact))
        active_btn.pack(side="left", padx=3)
        
        delete_btn = tk.Button(btn_frame, text="🗑️", font=self.font_small,
                              bg=self.bg_card, fg=self.danger, width=3,
                              cursor='hand2', bd=0,
                              command=lambda: self.delete_contact(contact))
        delete_btn.pack(side="left", padx=3)
    
    def copy_to_clipboard(self, number):
        self.window.clipboard_clear()
        self.window.clipboard_append(number)
        self.status_bar.config(text=f"📋 شماره {number} کپی شد!")
        self.window.after(2000, lambda: self.status_bar.config(text="✅ آماده"))
    
    def update_statistics(self):
        total = len(self.data["contacts"])
        orgs = len(set(c.get("organization", "") for c in self.data["contacts"] if c.get("organization")))
        active = sum(1 for c in self.data["contacts"] for p in c.get("phones", []) if p.get("is_active"))
        
        if hasattr(self, 'stats_labels'):
            self.stats_labels["total"].config(text=f"📊 تعداد کل: {total}")
            self.stats_labels["orgs"].config(text=f"🏢 سازمان‌ها: {orgs}")
            self.stats_labels["active"].config(text=f"⭐ شماره‌های فعال: {active}")
    
    def on_search(self, event):
        keyword = self.search_entry.get().strip().lower()
        self.load_organized_view(keyword)
    
    def add_phone_field(self, parent, phones_list, frame, number="", is_active=False):
        phone_frame = tk.Frame(frame, bg=self.bg_main)
        phone_frame.pack(fill="x", pady=5)
        
        phone_entry = tk.Entry(phone_frame, width=30, font=self.font_english,
                               bg=self.bg_light, fg=self.text_primary, 
                               relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                               justify="right")
        phone_entry.insert(0, number)
        phone_entry.pack(side="right", padx=10)
        
        active_var = tk.BooleanVar(value=is_active)
        active_check = tk.Checkbutton(phone_frame, text="فعال", variable=active_var,
                                      font=self.font_normal, fg=self.text_primary,
                                      bg=self.bg_main, selectcolor=self.bg_main)
        active_check.pack(side="right", padx=10)
        
        def remove():
            phone_frame.destroy()
            phones_list.remove((phone_frame, phone_entry, active_var))
        
        remove_btn = tk.Button(phone_frame, text="✖", command=remove,
                               bg=self.bg_card, fg=self.danger, width=3,
                               cursor='hand2', relief=tk.FLAT, font=("Segoe UI", 12, "bold"))
        remove_btn.pack(side="left", padx=5)
        
        def add_new():
            self.add_phone_field(parent, phones_list, frame)
        
        add_btn = tk.Button(phone_frame, text="▼", command=add_new,
                           bg=self.bg_card, fg=self.success, width=3,
                           cursor='hand2', relief=tk.FLAT, font=("Segoe UI", 12, "bold"))
        add_btn.pack(side="left", padx=5)
        
        phones_list.append((phone_frame, phone_entry, active_var))
    
    def add_contact_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("➕ افزودن شماره تماس جدید")
        dialog.geometry("650x550")
        dialog.configure(bg=self.bg_main)
        dialog.transient(self.window)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 650) // 2
        y = (dialog.winfo_screenheight() - 550) // 2
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=self.bg_main, padx=30, pady=25)
        main_frame.pack(fill="both", expand=True)
        
        title = tk.Label(main_frame, text="➕ افزودن شماره تماس جدید", 
                         font=self.font_title, fg=self.text_primary, bg=self.bg_main)
        title.pack(pady=(0, 25))
        
        tk.Label(main_frame, text="🏢 نام سازمان:", font=self.font_heading, 
                 fg=self.text_primary, bg=self.bg_main).pack(anchor="e", pady=(10, 5))
        org_entry = tk.Entry(main_frame, width=50, font=self.font_english,
                             bg=self.bg_light, fg=self.text_primary, 
                             relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                             justify="right")
        org_entry.pack(fill="x", pady=(0, 15))
        
        tk.Label(main_frame, text="👤 نام و نام خانوادگی:", font=self.font_heading, 
                 fg=self.text_primary, bg=self.bg_main).pack(anchor="e", pady=(5, 5))
        name_entry = tk.Entry(main_frame, width=50, font=self.font_english,
                              bg=self.bg_light, fg=self.text_primary, 
                              relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                              justify="right")
        name_entry.pack(fill="x", pady=(0, 15))
        
        tk.Label(main_frame, text="📞 شماره‌های تلفن:", font=self.font_heading,
                 fg=self.text_primary, bg=self.bg_main).pack(anchor="e", pady=(5, 5))
        
        phones_frame = tk.Frame(main_frame, bg=self.bg_main)
        phones_frame.pack(fill="both", expand=True)
        
        phones = []
        self.add_phone_field(main_frame, phones, phones_frame)
        
        def save():
            name = name_entry.get().strip()
            org = org_entry.get().strip()
            
            if not name and not org:
                messagebox.showerror("خطا", "حداقل یکی از فیلدها را پر کنید!")
                return
            
            phones_list = []
            for _, phone_entry, active_var in phones:
                number = phone_entry.get().strip()
                if number:
                    if len(number) < 4 or len(number) > 11:
                        messagebox.showerror("خطا", f"شماره {number} باید بین ۴ تا ۱۱ رقم باشد")
                        return
                    if not number.isdigit():
                        messagebox.showerror("خطا", f"شماره {number} باید فقط شامل اعداد باشد")
                        return
                    phones_list.append({"number": number, "is_active": active_var.get()})
            
            if not phones_list:
                messagebox.showerror("خطا", "حداقل یک شماره تلفن وارد کنید!")
                return
            
            new_id = max([c["id"] for c in self.data["contacts"]], default=0) + 1
            self.data["contacts"].append({
                "id": new_id,
                "name": name,
                "organization": org,
                "phones": phones_list,
                "created_at": datetime.now().isoformat()
            })
            self.save_database()
            self.load_organized_view()
            dialog.destroy()
            messagebox.showinfo("موفق", "✅ شماره تماس با موفقیت اضافه شد!")
        
        save_btn = tk.Button(main_frame, text="💾 ذخیره شماره تماس", command=save,
                            bg=self.success, fg=self.text_primary, font=self.font_heading,
                            cursor='hand2', padx=30, pady=10, relief=tk.RAISED, bd=1)
        save_btn.pack(pady=20)
    
    def import_from_file(self):
        filename = filedialog.askopenfilename(
            title="انتخاب فایل",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return
        
        try:
            imported_count = 0
            if filename.endswith('.csv'):
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) >= 2:
                            person_name = row[0].strip() if row[0] else ""
                            phone_numbers = row[1].strip() if len(row) > 1 else ""
                            org_name = row[2].strip() if len(row) > 2 else ""
                            
                            if (person_name or org_name) and phone_numbers:
                                phones_list = [{"number": num.strip(), "is_active": (i == 0)} 
                                              for i, num in enumerate(phone_numbers.split(','))]
                                
                                new_id = max([c["id"] for c in self.data["contacts"]], default=0) + 1
                                self.data["contacts"].append({
                                    "id": new_id,
                                    "name": person_name,
                                    "organization": org_name,
                                    "phones": phones_list,
                                    "created_at": datetime.now().isoformat()
                                })
                                imported_count += 1
            else:
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split(',')
                        if len(parts) >= 2:
                            person_name = parts[0].strip()
                            phone_numbers = parts[1].strip()
                            org_name = parts[2].strip() if len(parts) > 2 else ""
                            
                            if (person_name or org_name) and phone_numbers:
                                phones_list = [{"number": num.strip(), "is_active": (i == 0)} 
                                              for i, num in enumerate(phone_numbers.split('|'))]
                                
                                new_id = max([c["id"] for c in self.data["contacts"]], default=0) + 1
                                self.data["contacts"].append({
                                    "id": new_id,
                                    "name": person_name,
                                    "organization": org_name,
                                    "phones": phones_list,
                                    "created_at": datetime.now().isoformat()
                                })
                                imported_count += 1
            
            self.save_database()
            self.load_organized_view()
            messagebox.showinfo("موفق", f"✅ {imported_count} شماره تماس با موفقیت وارد شد!")
            
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در خواندن فایل: {str(e)}")
    
    def edit_contact_dialog(self, contact):
        dialog = tk.Toplevel(self.window)
        dialog.title("✏️ ویرایش شماره تماس")
        dialog.geometry("650x600")
        dialog.configure(bg=self.bg_main)
        dialog.transient(self.window)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 650) // 2
        y = (dialog.winfo_screenheight() - 600) // 2
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=self.bg_main, padx=30, pady=25)
        main_frame.pack(fill="both", expand=True)
        
        title = tk.Label(main_frame, text="✏️ ویرایش شماره تماس", 
                         font=self.font_title, fg=self.text_primary, bg=self.bg_main)
        title.pack(pady=(0, 25))
        
        tk.Label(main_frame, text="🏢 نام سازمان:", font=self.font_heading,
                 fg=self.text_primary, bg=self.bg_main).pack(anchor="e", pady=(10, 5))
        org_entry = tk.Entry(main_frame, width=50, font=self.font_english,
                             bg=self.bg_light, fg=self.text_primary, 
                             relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                             justify="right")
        org_entry.insert(0, contact.get("organization", ""))
        org_entry.pack(fill="x", pady=(0, 15))
        
        tk.Label(main_frame, text="👤 نام و نام خانوادگی:", font=self.font_heading,
                 fg=self.text_primary, bg=self.bg_main).pack(anchor="e", pady=(5, 5))
        name_entry = tk.Entry(main_frame, width=50, font=self.font_english,
                              bg=self.bg_light, fg=self.text_primary, 
                              relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                              justify="right")
        name_entry.insert(0, contact["name"])
        name_entry.pack(fill="x", pady=(0, 15))
        
        tk.Label(main_frame, text="📞 شماره‌های تلفن:", font=self.font_heading,
                 fg=self.text_primary, bg=self.bg_main).pack(anchor="e", pady=(5, 5))
        
        phones_frame = tk.Frame(main_frame, bg=self.bg_main)
        phones_frame.pack(fill="both", expand=True)
        
        phones_widgets = []
        
        def add_new_phone():
            phone_frame = tk.Frame(phones_frame, bg=self.bg_main)
            phone_frame.pack(fill="x", pady=5)
            
            phone_entry = tk.Entry(phone_frame, width=30, font=self.font_english,
                                   bg=self.bg_light, fg=self.text_primary, 
                                   relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                                   justify="right")
            phone_entry.pack(side="right", padx=10)
            
            active_var = tk.BooleanVar(value=False)
            active_check = tk.Checkbutton(phone_frame, text="فعال", variable=active_var,
                                          font=self.font_normal, fg=self.text_primary,
                                          bg=self.bg_main, selectcolor=self.bg_main)
            active_check.pack(side="right", padx=10)
            
            def remove_this():
                phone_frame.destroy()
                phones_widgets.remove((phone_frame, phone_entry, active_var))
            
            remove_btn = tk.Button(phone_frame, text="✖", command=remove_this,
                                   bg=self.bg_card, fg=self.danger, width=3,
                                   cursor='hand2', relief=tk.FLAT, font=("Segoe UI", 12, "bold"))
            remove_btn.pack(side="left", padx=5)
            
            add_btn = tk.Button(phone_frame, text="▼", command=add_new_phone,
                               bg=self.bg_card, fg=self.success, width=3,
                               cursor='hand2', relief=tk.FLAT, font=("Segoe UI", 12, "bold"))
            add_btn.pack(side="left", padx=5)
            
            phones_widgets.append((phone_frame, phone_entry, active_var))
        
        def refresh_phones():
            for widget in phones_widgets:
                for w in widget:
                    w.destroy()
            phones_widgets.clear()
            
            for idx, phone in enumerate(contact["phones"]):
                phone_frame = tk.Frame(phones_frame, bg=self.bg_main)
                phone_frame.pack(fill="x", pady=5)
                
                phone_entry = tk.Entry(phone_frame, width=30, font=self.font_english,
                                       bg=self.bg_light, fg=self.text_primary, 
                                       relief=tk.FLAT, bd=0, insertbackground=self.text_primary,
                                       justify="right")
                phone_entry.insert(0, phone["number"])
                phone_entry.pack(side="right", padx=10)
                
                active_var = tk.BooleanVar(value=phone.get("is_active", False))
                active_check = tk.Checkbutton(phone_frame, text="فعال", variable=active_var,
                                              font=self.font_normal, fg=self.text_primary,
                                              bg=self.bg_main, selectcolor=self.bg_main)
                active_check.pack(side="right", padx=10)
                
                def remove_this(i=idx):
                    contact["phones"].pop(i)
                    refresh_phones()
                
                remove_btn = tk.Button(phone_frame, text="✖", command=remove_this,
                                       bg=self.bg_card, fg=self.danger, width=3,
                                       cursor='hand2', relief=tk.FLAT, font=("Segoe UI", 12, "bold"))
                remove_btn.pack(side="left", padx=5)
                
                def add_new():
                    add_new_phone()
                
                add_btn = tk.Button(phone_frame, text="▼", command=add_new,
                                   bg=self.bg_card, fg=self.success, width=3,
                                   cursor='hand2', relief=tk.FLAT, font=("Segoe UI", 12, "bold"))
                add_btn.pack(side="left", padx=5)
                
                phones_widgets.append((phone_frame, phone_entry, active_var))
        
        refresh_phones()
        
        def save():
            contact["name"] = name_entry.get().strip()
            contact["organization"] = org_entry.get().strip()
            
            new_phones = []
            for _, phone_entry, active_var in phones_widgets:
                number = phone_entry.get().strip()
                if number:
                    if len(number) < 4 or len(number) > 11:
                        messagebox.showerror("خطا", f"شماره {number} باید بین ۴ تا ۱۱ رقم باشد")
                        return
                    if not number.isdigit():
                        messagebox.showerror("خطا", f"شماره {number} باید فقط شامل اعداد باشد")
                        return
                    new_phones.append({"number": number, "is_active": active_var.get()})
            
            if not new_phones:
                messagebox.showerror("خطا", "حداقل یک شماره تلفن باید وجود داشته باشد!")
                return
            
            contact["phones"] = new_phones
            self.save_database()
            self.load_organized_view()
            dialog.destroy()
            messagebox.showinfo("موفق", "✅ شماره تماس با موفقیت ویرایش شد!")
        
        save_btn = tk.Button(main_frame, text="💾 ذخیره تغییرات", command=save,
                            bg=self.success, fg=self.text_primary, font=self.font_heading,
                            cursor='hand2', padx=30, pady=10, relief=tk.RAISED, bd=1)
        save_btn.pack(pady=20)
    
    def delete_contact(self, contact):
        if messagebox.askyesno("تأیید حذف", f"❓ آیا از حذف این شماره تماس مطمئن هستید؟"):
            self.data["contacts"] = [c for c in self.data["contacts"] if c["id"] != contact["id"]]
            self.save_database()
            self.load_organized_view()
            messagebox.showinfo("موفق", "🗑️ شماره تماس با موفقیت حذف شد!")
    
    def set_active_phones(self, contact):
        if not contact.get("phones"):
            messagebox.showwarning("خطا", "این شماره تماس هیچ شماره‌ای ندارد!")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("⭐ تنظیم وضعیت شماره‌ها")
        dialog.geometry("500x500")
        dialog.configure(bg=self.bg_main)
        dialog.transient(self.window)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 500) // 2
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg=self.bg_main, padx=25, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        title = tk.Label(main_frame, text="⭐ وضعیت شماره‌ها را انتخاب کنید:", 
                         font=self.font_heading, fg=self.text_primary, bg=self.bg_main)
        title.pack(pady=(0, 20))
        
        phone_vars = []
        
        for phone in contact["phones"]:
            var = tk.BooleanVar(value=phone.get("is_active", False))
            phone_vars.append((phone["number"], var))
            
            frame = tk.Frame(main_frame, bg=self.bg_main)
            frame.pack(fill="x", pady=8, padx=20)
            
            cb = tk.Checkbutton(frame, text=phone["number"], variable=var,
                               font=self.font_english, fg=self.text_primary,
                               bg=self.bg_main, selectcolor=self.bg_main,
                               activebackground=self.bg_main)
            cb.pack(side="right", anchor="e")
        
        btn_frame = tk.Frame(main_frame, bg=self.bg_main)
        btn_frame.pack(pady=20)
        
        def activate_all():
            for _, var in phone_vars:
                var.set(True)
        
        def deactivate_all():
            for _, var in phone_vars:
                var.set(False)
        
        btn_all_active = tk.Button(btn_frame, text="✅ فعال کردن همه", command=activate_all,
                                  bg=self.success, fg=self.text_primary, font=self.font_small,
                                  cursor='hand2', padx=15, pady=5, relief=tk.RAISED, bd=1)
        btn_all_active.pack(side="right", padx=10)
        
        btn_all_inactive = tk.Button(btn_frame, text="❌ غیرفعال کردن همه", command=deactivate_all,
                                    bg=self.danger, fg=self.text_primary, font=self.font_small,
                                    cursor='hand2', padx=15, pady=5, relief=tk.RAISED, bd=1)
        btn_all_inactive.pack(side="right", padx=10)
        
        def save_active():
            for i, (_, var) in enumerate(phone_vars):
                contact["phones"][i]["is_active"] = var.get()
            
            self.save_database()
            self.load_organized_view()
            dialog.destroy()
            
            active_count = sum(1 for _, var in phone_vars if var.get())
            messagebox.showinfo("موفق", f"⭐ {active_count} شماره با موفقیت تنظیم شد!")
        
        save_btn = tk.Button(main_frame, text="💾 ذخیره", command=save_active,
                            bg=self.success, fg=self.text_primary, font=self.font_heading,
                            cursor='hand2', padx=25, pady=8, relief=tk.RAISED, bd=1)
        save_btn.pack(pady=25)
    
    def merge_database_dialog(self):
        filename = filedialog.askopenfilename(title="انتخاب فایل دیتابیس", 
                                              filetypes=[("JSON files", "*.json")])
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                other_data = json.load(f)
            
            current_ids = [c["id"] for c in self.data["contacts"]]
            max_id = max(current_ids) if current_ids else 0
            
            for contact in other_data.get("contacts", []):
                max_id += 1
                contact["id"] = max_id
                self.data["contacts"].append(contact)
            
            self.save_database()
            self.load_organized_view()
            messagebox.showinfo("موفق", f"🔄 {len(other_data.get('contacts', []))} شماره تماس جدید اضافه شد!")
        except Exception as e:
            messagebox.showerror("خطا", f"❌ خطا در ادغام: {str(e)}")
    
    def export_csv(self):
        if not self.data["contacts"]:
            messagebox.showwarning("خطا", "هیچ شماره تماسی برای خروجی وجود ندارد!")
            return
        
        filename = f"phonebook_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['🏢 سازمان', '👤 نام و نام خانوادگی', '📞 شماره‌های تلفن', '⭐ شماره فعال', '📅 تاریخ ثبت'])
            
            for contact in self.data["contacts"]:
                phones_str = " | ".join([f"{p['number']}({'✅' if p.get('is_active') else '❌'})" 
                                        for p in contact.get("phones", [])])
                active_phone = next((p["number"] for p in contact.get("phones", []) 
                                    if p.get("is_active")), "ندارد")
                
                writer.writerow([
                    contact.get("organization", ""),
                    contact.get("name", ""),
                    phones_str,
                    active_phone,
                    contact.get("created_at", "")
                ])
        
        messagebox.showinfo("موفق", f"📤 خروجی در فایل {filename} ذخیره شد!")
    
    def manual_backup(self):
        self.save_database()
        self.status_bar.config(text="💾 ذخیره شد!")
        self.window.after(2000, lambda: self.status_bar.config(text="✅ آماده"))
        messagebox.showinfo("موفق", "💾 دیتابیس با موفقیت ذخیره شد!")
    
    def on_closing(self):
        self.save_database()
        self.window.destroy()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = PhoneBookPro()
    app.run()