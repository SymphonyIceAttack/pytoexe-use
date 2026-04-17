import customtkinter as ctk
import json
import os

# ---------- إعداد ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATA_FILE = "database.json"


# ---------- البيانات ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ---------- تحقق الأرقام ----------
def limit_digits(entry, max_len):
    def on_write(*args):
        value = var.get()
        filtered = "".join(filter(str.isdigit, value))
        if len(filtered) > max_len:
            filtered = filtered[:max_len]
        if filtered != value:
            var.set(filtered)

    var = ctk.StringVar()
    var.trace_add("write", on_write)
    entry.configure(textvariable=var)
    return var


# ---------- التطبيق ----------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("نظام إدارة الأشخاص")
        self.geometry("1000x700")

        self.data = load_data()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main()

        self.show_dashboard()

    # ---------- Sidebar ----------
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(self.sidebar, text="القائمة", font=("Arial", 22)).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="🏠 الرئيسية", command=self.show_dashboard).pack(pady=10, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="➕ تسجيل", command=self.show_register).pack(pady=10, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="🔍 بحث", command=self.show_search).pack(pady=10, fill="x", padx=10)
        ctk.CTkButton(self.sidebar, text="⚙️ الإعدادات", command=self.show_settings).pack(pady=10, fill="x", padx=10)

    # ---------- Main ----------
    def create_main(self):
        self.main = ctk.CTkFrame(self)
        self.main.grid(row=0, column=1, sticky="nsew")

    def clear(self):
        for w in self.main.winfo_children():
            w.destroy()

    # ---------- Dashboard ----------
    def show_dashboard(self):
        self.clear()

        ctk.CTkLabel(self.main, text="لوحة التحكم", font=("Arial", 34)).pack(pady=40)

        ctk.CTkButton(self.main, text="تسجيل شخص", height=70, command=self.show_register).pack(pady=20, ipadx=80)
        ctk.CTkButton(self.main, text="البحث عن شخص", height=70, command=self.show_search).pack(pady=20, ipadx=80)

    # ---------- إنشاء حقل ----------
    def create_field(self, label, key, entries, max_len=None):
        box = ctk.CTkFrame(self.main, corner_radius=15)
        box.pack(fill="x", padx=120, pady=12)

        lbl = ctk.CTkLabel(box, text=label, font=("Arial", 16), anchor="e")
        lbl.pack(fill="x", padx=15, pady=(10, 0))

        entry = ctk.CTkEntry(box, height=45, font=("Arial", 16))
        entry.pack(fill="x", padx=15, pady=10)

        if max_len:
            limit_digits(entry, max_len)

        entries[key] = entry

    # ---------- تسجيل ----------
    def show_register(self, user=None):
        self.clear()

        entries = {}

        self.create_field("الاسم واللقب", "name", entries)
        self.create_field("رقم التعريف الوطني", "nid", entries, 18)
        self.create_field("رقم المستخدم", "uid", entries, 12)
        self.create_field("رقم الحساب البريدي", "acc", entries, 12)
        self.create_field("رقم الهاتف", "phone", entries, 10)

        if user:
            entries["name"].insert(0, user["name"])
            entries["nid"].insert(0, user["nid"])
            entries["uid"].insert(0, user["uid"])
            entries["acc"].insert(0, user["acc"])
            entries["phone"].insert(0, user["phone"])

        def ask_status(callback):
            popup = ctk.CTkToplevel(self)
            popup.geometry("320x200")

            ctk.CTkLabel(popup, text="هل حصل على موعد؟", font=("Arial", 18)).pack(pady=20)

            ctk.CTkButton(popup, text="نعم", command=lambda: [callback(True), popup.destroy()]).pack(pady=5)
            ctk.CTkButton(popup, text="لا", command=lambda: [callback(False), popup.destroy()]).pack(pady=5)

        def save_user():
            def after(status):
                new_user = {
                    "name": entries["name"].get(),
                    "nid": entries["nid"].get(),
                    "uid": entries["uid"].get(),
                    "acc": entries["acc"].get(),
                    "phone": entries["phone"].get(),
                    "status": status
                }

                if user:
                    self.data.remove(user)

                self.data.append(new_user)
                save_data(self.data)
                self.show_dashboard()

            ask_status(after)

        ctk.CTkButton(self.main, text="حفظ", height=55, command=save_user).pack(pady=30)

    # ---------- البحث ----------
    def show_search(self):
        self.clear()

        entry = ctk.CTkEntry(self.main, height=50, font=("Arial", 16))
        entry.pack(fill="x", padx=120, pady=20)

        results = ctk.CTkFrame(self.main)
        results.pack(fill="both", expand=True, padx=120)

        def do_search():
            for w in results.winfo_children():
                w.destroy()

            text = entry.get()

            for u in self.data:
                if text in u["name"]:
                    status = "حصل على موعد" if u["status"] else "لم يحصل على موعد"

                    btn = ctk.CTkButton(
                        results,
                        text=f"{u['name']}\n{status}",
                        height=60,
                        command=lambda user=u: self.show_register(user)
                    )
                    btn.pack(fill="x", pady=6)

        ctk.CTkButton(self.main, text="بحث", command=do_search).pack()

    # ---------- الإعدادات ----------
    def show_settings(self):
        self.clear()

        def toggle():
            mode = ctk.get_appearance_mode()
            ctk.set_appearance_mode("light" if mode == "dark" else "dark")

        ctk.CTkButton(self.main, text="تغيير الوضع", command=toggle).pack(pady=20)

        ctk.CTkLabel(
            self.main,
            text="تم صناعة البرنامج من قبل محمد عبد المجيد بن جاب الله",
            font=("Arial", 16)
        ).pack(pady=40)


# ---------- تشغيل ----------
if __name__ == "__main__":
    app = App()
    app.mainloop()