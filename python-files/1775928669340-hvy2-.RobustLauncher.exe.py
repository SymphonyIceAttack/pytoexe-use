import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import ctypes
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# =============================================================
#  مسار ثابت دائم — AppData بغض النظر عن مكان تشغيل البرنامج
# =============================================================
def get_app_dir():
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        base = os.path.expanduser('~/.config')
    folder = os.path.join(base, 'RobustLauncher')
    os.makedirs(folder, exist_ok=True)
    return folder

APP_DIR    = get_app_dir()
DATA_FILE  = os.path.join(APP_DIR, "safe_launch.json")
TRASH_FILE = os.path.join(APP_DIR, "trash_bin.json")
BACKUP     = os.path.join(APP_DIR, "safe_launch_backup.json")
ADMIN_FLAG = os.path.join(APP_DIR, ".admin_choice")   # 'yes' | 'no'

# =============================================================
#  صلاحيات المسؤول — السؤال مرة واحدة فقط في العمر
# =============================================================
def is_admin():
    try:
        if sys.platform == 'win32':
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.geteuid() == 0
    except:
        return False

def _relaunch_as_admin():
    try:
        params = ' '.join(f'"{a}"' for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
    except:
        pass
    sys.exit()

def handle_admin():
    """
    - مسؤول بالفعل  → لا شيء
    - قرار محفوظ 'no'  → لا شيء
    - قرار محفوظ 'yes' → أعد التشغيل بصمت
    - لا يوجد قرار     → اسأل مرة واحدة واحفظ الإجابة
    """
    if sys.platform != 'win32':
        return
    if is_admin():
        return

    if os.path.exists(ADMIN_FLAG):
        with open(ADMIN_FLAG, 'r') as f:
            choice = f.read().strip()
        if choice == 'no':
            return
        if choice == 'yes':
            _relaunch_as_admin()
        return   # قيمة غير معروفة → تجاهل

    # السؤال لأول مرة فقط
    r = tk.Tk(); r.withdraw()
    ans = messagebox.askyesno(
        "Robust Launcher — صلاحيات",
        "هل تريد تشغيل البرنامج بصلاحيات المسؤول؟\n\n"
        "• نعم  ← صلاحيات كاملة وحفظ في أي مكان\n"
        "• لا   ← تشغيل عادي\n\n"
        "لن يُسأل هذا السؤال مرة أخرى.\n"
        "يمكنك تغييره لاحقاً من نافذة الإعدادات."
    )
    r.destroy()

    with open(ADMIN_FLAG, 'w') as f:
        f.write('yes' if ans else 'no')

    if ans:
        _relaunch_as_admin()

if __name__ == "__main__":
    handle_admin()

# إخفاء نافذة الكونسول
if sys.platform == 'win32':
    try:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# =============================================================
#  الثوابت
# =============================================================
SLOTS         = 12
DEFAULT_COLOR = "#3b82f6"
EMPTY_BG      = "#1e293b"
BG_DARK       = "#0f172a"
BG_MID        = "#1e293b"
BG_BORDER     = "#334155"
TEXT_PRIMARY  = "#f1f5f9"
TEXT_MUTED    = "#64748b"
ACCENT        = "#3b82f6"


# =============================================================
#  الكلاس الرئيسي
# =============================================================
class RobustLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Robust Launcher")
        self.root.overrideredirect(True)
        self.root.configure(bg=BG_DARK)

        self._drag_x = self._drag_y = 0
        self._rsz    = None
        self._sts_id = None

        self.apps  = self._load_json(DATA_FILE,  [None] * SLOTS)
        self.trash = self._load_json(TRASH_FILE, [])

        if not isinstance(self.apps, list) or len(self.apps) != SLOTS:
            self.apps = [None] * SLOTS

        self._ensure_backup()
        self.center_window(460, 680)
        self._build_ui()
        self.root.mainloop()

    # ----------------------------------------------------------
    #  حفظ / تحميل
    # ----------------------------------------------------------
    def _load_json(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default

    def _save_json(self, path, data):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def save_apps(self):
        ok = self._save_json(DATA_FILE, self.apps)
        if ok:
            try: shutil.copy2(DATA_FILE, BACKUP)
            except: pass
            self.set_status("✔  تم الحفظ", "#22c55e", 2500)
        else:
            self.set_status("✘  فشل الحفظ!", "#ef4444")
        return ok

    def save_trash(self):
        self._save_json(TRASH_FILE, self.trash)

    def _ensure_backup(self):
        if not os.path.exists(BACKUP):
            try: shutil.copy2(DATA_FILE, BACKUP)
            except: pass

    # ----------------------------------------------------------
    #  بناء الواجهة
    # ----------------------------------------------------------
    def _build_ui(self):
        self.frame = tk.Frame(self.root, bg=BG_DARK,
                              highlightthickness=2,
                              highlightbackground=BG_BORDER)
        self.frame.pack(fill="both", expand=True)

        self._build_header()
        tk.Frame(self.frame, bg=ACCENT, height=2).pack(fill="x")
        self._build_search()
        self._build_buttons()
        self._build_statusbar()
        self._build_context_menu()
        self._add_resize_grip()
        self._bind_hotkeys()

    # --- هيدر ---
    def _build_header(self):
        hdr = tk.Frame(self.frame, bg=BG_MID, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ico = tk.Frame(hdr, bg=ACCENT, width=30, height=30)
        ico.place(x=14, y=11); ico.pack_propagate(False)
        tk.Label(ico, text="🚀", bg=ACCENT, font=("Arial", 14)
                 ).place(relx=.5, rely=.5, anchor="center")

        tf = tk.Frame(hdr, bg=BG_MID)
        tf.place(x=52, y=8)
        tk.Label(tf, text="ROBUST LAUNCHER", fg=TEXT_PRIMARY,
                 bg=BG_MID, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        adm_txt   = "● ADMIN" if is_admin() else "● USER"
        adm_color = "#22c55e" if is_admin() else "#94a3b8"
        tk.Label(tf, text=adm_txt, fg=adm_color,
                 bg=BG_MID, font=("Segoe UI", 7)).pack(anchor="w")

        btn_data = [
            ("🗑", "#94a3b8", self.show_trash),
            ("⚙", "#94a3b8", self.show_settings),
            ("─", "#94a3b8", self.root.iconify),
            ("✕", "#ef4444", self.on_close),
        ]
        for txt, fg, cmd in reversed(btn_data):
            b = tk.Label(hdr, text=txt, fg=fg, bg=BG_MID,
                         font=("Segoe UI", 12), cursor="hand2", padx=7)
            b.pack(side="right", pady=10)
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>",    lambda e, w=b: w.config(bg="#334155"))
            b.bind("<Leave>",    lambda e, w=b: w.config(bg=BG_MID))

        for w in (hdr, tf, ico):
            w.bind("<Button-1>",  self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

    # --- بحث ---
    def _build_search(self):
        wrap = tk.Frame(self.frame, bg=BG_DARK, pady=8)
        wrap.pack(fill="x", padx=14)
        box = tk.Frame(wrap, bg=BG_MID,
                       highlightthickness=1, highlightbackground=BG_BORDER)
        box.pack(fill="x")

        tk.Label(box, text="🔍", fg="#475569", bg=BG_MID,
                 font=("Arial", 10)).pack(side="left", padx=(8, 2))

        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self._filter())

        self._search = tk.Entry(box, textvariable=self._sv,
                                bg=BG_MID, fg="#cbd5e1",
                                insertbackground=ACCENT,
                                font=("Segoe UI", 10),
                                relief="flat", highlightthickness=0)
        self._search.pack(side="left", fill="x", expand=True, pady=7)
        self._ph = "ابحث عن برنامج..."
        self._search.insert(0, self._ph)
        self._search.config(fg="#475569")

        def fi(e):
            if self._search.get() == self._ph:
                self._search.delete(0, tk.END)
                self._search.config(fg="#cbd5e1")
            box.config(highlightbackground=ACCENT)
        def fo(e):
            if not self._search.get():
                self._search.insert(0, self._ph)
                self._search.config(fg="#475569")
            box.config(highlightbackground=BG_BORDER)

        self._search.bind("<FocusIn>",  fi)
        self._search.bind("<FocusOut>", fo)

        clr = tk.Label(box, text="✖", fg="#475569", bg=BG_MID,
                       cursor="hand2", font=("Arial", 9))
        clr.pack(side="right", padx=8)
        clr.bind("<Button-1>", lambda e: self._sv.set(""))
        clr.bind("<Enter>",    lambda e: clr.config(fg="#ef4444"))
        clr.bind("<Leave>",    lambda e: clr.config(fg="#475569"))

    # --- أزرار التطبيقات ---
    def _build_buttons(self):
        outer = tk.Frame(self.frame, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        self._canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical",
                          command=self._canvas.yview,
                          width=5, bg=BG_MID,
                          troughcolor=BG_DARK, relief="flat")
        self._sf = tk.Frame(self._canvas, bg=BG_DARK)

        self._sf.bind("<Configure>", lambda e:
            self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._cw = self._canvas.create_window(
            (0, 0), window=self._sf, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._cw, width=e.width))

        self._sf.bind("<Enter>",
            lambda e: self._canvas.bind_all("<MouseWheel>", self._scroll))
        self._sf.bind("<Leave>",
            lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._btns    = []
        self._bframes = []
        for i in range(SLOTS):
            self._make_btn(i)

    def _make_btn(self, idx):
        fr = tk.Frame(self._sf, bg=BG_DARK, pady=2)
        fr.pack(fill="x")
        btn = tk.Button(fr, text="", relief="flat", cursor="hand2",
                        font=("Segoe UI", 10, "bold"),
                        height=2, anchor="w", padx=16, bd=0,
                        command=lambda i=idx: self.run_app(i))
        btn.pack(fill="x", expand=True)
        btn.bind("<Button-3>",       lambda e, i=idx: self._ctx_menu(e, i))
        btn.bind("<Double-Button-1>",lambda e, i=idx: self.edit_slot(i))
        self._btns.append(btn)
        self._bframes.append(fr)
        self._refresh_btn(idx)

    @staticmethod
    def _icon(name):
        n = name.lower()
        m = {'game':'🎮','steam':'🎮','epic':'🎮',
             'chrome':'🌐','firefox':'🌐','edge':'🌐',
             'code':'💻','studio':'💻','python':'💻','vscode':'💻',
             'discord':'💬','telegram':'💬','whatsapp':'💬',
             'photo':'🖼','paint':'🖼','photoshop':'🖼',
             'music':'🎵','spotify':'🎵','vlc':'🎵',
             'word':'📄','excel':'📊','office':'📄',
             'folder':'📁','explorer':'📁'}
        for k, v in m.items():
            if k in n: return v
        return '⚡'

    def _refresh_btn(self, idx):
        btn  = self._btns[idx]
        app  = self.apps[idx] if idx < SLOTS else None

        if app:
            alive = os.path.exists(app.get('path', ''))
            name  = app['name'][:24]
            ico   = self._icon(app['name'])
            if alive:
                color = app.get('color', DEFAULT_COLOR)
                btn.config(text=f"  {ico}  {name}",
                           bg=color, fg="white",
                           activebackground=color, activeforeground="white")
                def _enter(e, c=color):
                    r, g, b = (self.root.winfo_rgb(c)[i]//257 for i in range(3))
                    btn.config(bg=f'#{min(255,r+25):02x}{min(255,g+25):02x}{min(255,b+25):02x}')
                def _leave(e, c=color): btn.config(bg=c)
                btn.bind("<Enter>", _enter)
                btn.bind("<Leave>", _leave)
            else:
                btn.config(text=f"  ⚠  {name}  (ملف مفقود)",
                           bg="#431407", fg="#fb923c",
                           activebackground="#431407", activeforeground="#fb923c")
                btn.unbind("<Enter>"); btn.unbind("<Leave>")
        else:
            btn.config(text=f"  ＋  خانة {idx+1}",
                       bg=EMPTY_BG, fg="#334155",
                       activebackground="#253347", activeforeground="#475569")
            btn.bind("<Enter>", lambda e: btn.config(bg="#253347", fg="#475569"))
            btn.bind("<Leave>", lambda e: btn.config(bg=EMPTY_BG, fg="#334155"))

    def _filter(self):
        q = self._sv.get().lower()
        for i, fr in enumerate(self._bframes):
            app = self.apps[i] if i < SLOTS else None
            if not q or q == self._ph.lower():
                fr.pack(fill="x")
            elif app and q in app.get('name', '').lower():
                fr.pack(fill="x")
            else:
                fr.pack_forget()

    # --- شريط الحالة ---
    def _build_statusbar(self):
        bar = tk.Frame(self.frame, bg=BG_MID, height=36)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status = tk.Label(bar, text="جاهز", fg=TEXT_MUTED,
                                bg=BG_MID, font=("Segoe UI", 9))
        self._status.pack(side="left", padx=12)

        self._counter = tk.Label(bar, text="", fg=ACCENT,
                                 bg=BG_MID, font=("Segoe UI", 9, "bold"))
        self._counter.pack(side="right", padx=10)

        rb = tk.Label(bar, text="↺ استعادة", fg="#475569", bg=BG_MID,
                      font=("Segoe UI", 8), cursor="hand2")
        rb.pack(side="right", padx=6)
        rb.bind("<Button-1>", lambda e: self.restore_backup())
        rb.bind("<Enter>",    lambda e: rb.config(fg=ACCENT))
        rb.bind("<Leave>",    lambda e: rb.config(fg="#475569"))

        self._update_counter()

    # --- قائمة السياق ---
    def _build_context_menu(self):
        self._menu = tk.Menu(self.root, tearoff=0,
                             bg=BG_MID, fg="#e2e8f0",
                             activebackground=ACCENT, activeforeground="white",
                             font=("Segoe UI", 9), relief="flat", bd=0)
        self._menu.add_command(label="  ✏  تعديل")
        self._menu.add_command(label="  📂  فتح المجلد")
        self._menu.add_command(label="  📋  نسخ المسار")
        self._menu.add_separator()
        self._menu.add_command(label="  🗑  حذف")

    def _ctx_menu(self, event, idx):
        self._menu.entryconfig(0, command=lambda: self.edit_slot(idx))
        self._menu.entryconfig(1, command=lambda: self.open_folder(idx))
        self._menu.entryconfig(2, command=lambda: self.copy_path(idx))
        self._menu.entryconfig(4, command=lambda: self.move_to_trash(idx))
        self._menu.post(event.x_root, event.y_root)

    # --- مقبض تغيير الحجم ---
    def _add_resize_grip(self):
        g = tk.Label(self.frame, text="◢", fg="#334155", bg=BG_DARK,
                     cursor="size_nw_se", font=("Arial", 10))
        g.place(relx=1, rely=1, anchor="se", x=-2, y=-2)
        g.bind("<Button-1>",  self._rsz_start)
        g.bind("<B1-Motion>", self._rsz_drag)

    def _rsz_start(self, e):
        self._rsz = (e.x_root, e.y_root,
                     self.root.winfo_width(), self.root.winfo_height())
    def _rsz_drag(self, e):
        if not self._rsz: return
        sx, sy, sw, sh = self._rsz
        nw = max(380, sw + e.x_root - sx)
        nh = max(400, sh + e.y_root - sy)
        self.root.geometry(f"{nw}x{nh}")

    # ----------------------------------------------------------
    #  تعديل خانة
    # ----------------------------------------------------------
    def edit_slot(self, idx):
        dlg = tk.Toplevel(self.root)
        dlg.overrideredirect(True)
        dlg.configure(bg=BG_DARK)
        dlg.grab_set()

        W, H = 430, 410
        x = self.root.winfo_x() + (self.root.winfo_width()  - W) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - H) // 2
        dlg.geometry(f"{W}x{H}+{x}+{y}")

        dh = tk.Frame(dlg, bg=BG_MID, height=42)
        dh.pack(fill="x"); dh.pack_propagate(False)
        tk.Label(dh, text=f"✏  تعديل الخانة {idx+1}",
                 fg=TEXT_PRIMARY, bg=BG_MID,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=14, pady=10)
        xb = tk.Label(dh, text="✕", fg="#94a3b8", bg=BG_MID,
                      font=("Segoe UI", 13), cursor="hand2")
        xb.pack(side="right", padx=10)
        xb.bind("<Button-1>", lambda e: dlg.destroy())
        xb.bind("<Enter>",    lambda e: xb.config(fg="#ef4444"))
        xb.bind("<Leave>",    lambda e: xb.config(fg="#94a3b8"))

        body = tk.Frame(dlg, bg=BG_DARK, padx=18, pady=10)
        body.pack(fill="both", expand=True)

        def lbl(txt):
            tk.Label(body, text=txt, fg=TEXT_MUTED, bg=BG_DARK,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))

        def entry_box():
            f = tk.Frame(body, bg=BG_MID,
                         highlightthickness=1, highlightbackground=BG_BORDER)
            f.pack(fill="x")
            e = tk.Entry(f, bg=BG_MID, fg="#e2e8f0",
                         insertbackground=ACCENT,
                         font=("Segoe UI", 10), relief="flat",
                         highlightthickness=0)
            e.pack(fill="x", padx=10, pady=7)
            e.bind("<FocusIn>",  lambda _: f.config(highlightbackground=ACCENT))
            e.bind("<FocusOut>", lambda _: f.config(highlightbackground=BG_BORDER))
            return e

        lbl("اسم البرنامج:")
        name_e = entry_box()

        lbl("مسار الملف التنفيذي:")
        pf = tk.Frame(body, bg=BG_MID,
                      highlightthickness=1, highlightbackground=BG_BORDER)
        pf.pack(fill="x")
        path_e = tk.Entry(pf, bg=BG_MID, fg="#e2e8f0",
                          insertbackground=ACCENT,
                          font=("Segoe UI", 10), relief="flat",
                          highlightthickness=0)
        path_e.pack(side="left", fill="x", expand=True, padx=10, pady=7)
        path_e.bind("<FocusIn>",  lambda _: pf.config(highlightbackground=ACCENT))
        path_e.bind("<FocusOut>", lambda _: pf.config(highlightbackground=BG_BORDER))

        def browse():
            p = filedialog.askopenfilename(
                parent=dlg, title="اختر البرنامج",
                filetypes=[("تطبيقات", "*.exe *.bat *.cmd *.lnk"),
                           ("كل الملفات", "*.*")])
            if p:
                path_e.delete(0, tk.END); path_e.insert(0, p)
                if not name_e.get():
                    name_e.insert(0, Path(p).stem)

        brow = tk.Label(pf, text="📂", fg="#94a3b8", bg=BG_MID,
                        cursor="hand2", font=("Arial", 12), padx=8)
        brow.pack(side="right")
        brow.bind("<Button-1>", lambda e: browse())
        brow.bind("<Enter>",    lambda e: brow.config(fg=ACCENT))
        brow.bind("<Leave>",    lambda e: brow.config(fg="#94a3b8"))

        lbl("لون الزر:")
        color_row = tk.Frame(body, bg=BG_DARK)
        color_row.pack(fill="x")

        cf = tk.Frame(color_row, bg=BG_MID,
                      highlightthickness=1, highlightbackground=BG_BORDER)
        cf.pack(side="left", fill="x", expand=True)
        color_e = tk.Entry(cf, bg=BG_MID, fg="#e2e8f0",
                           insertbackground=ACCENT,
                           font=("Segoe UI", 10), relief="flat",
                           highlightthickness=0, width=10)
        color_e.pack(padx=10, pady=7)
        color_e.insert(0, DEFAULT_COLOR)

        prev = tk.Frame(color_row, bg=DEFAULT_COLOR, width=44, height=36)
        prev.pack(side="left", padx=(8, 0)); prev.pack_propagate(False)

        def upd_prev(*_):
            c = color_e.get()
            if len(c) == 7 and c.startswith('#'):
                try: int(c[1:], 16); prev.config(bg=c)
                except: pass
        color_e.bind("<KeyRelease>", upd_prev)

        prow = tk.Frame(body, bg=BG_DARK)
        prow.pack(fill="x", pady=(6, 0))
        for c in ["#3b82f6","#8b5cf6","#ec4899","#f97316",
                  "#22c55e","#14b8a6","#ef4444","#eab308"]:
            cb = tk.Frame(prow, bg=c, width=26, height=26, cursor="hand2")
            cb.pack(side="left", padx=2)
            cb.bind("<Button-1>", lambda e, col=c: (
                color_e.delete(0, tk.END), color_e.insert(0, col),
                prev.config(bg=col)
            ))

        def do_save():
            name  = name_e.get().strip()
            path  = path_e.get().strip()
            color = color_e.get().strip()

            if not name or not path:
                messagebox.showwarning("تنبيه", "أدخل الاسم والمسار!", parent=dlg)
                return
            try:
                if not (len(color) == 7 and color.startswith('#')):
                    raise ValueError
                int(color[1:], 16)
            except:
                color = DEFAULT_COLOR

            self.apps[idx] = {"name": name, "path": path, "color": color}
            if self.save_apps():
                self._refresh_btn(idx)
                self._update_counter()
                dlg.destroy()

        tk.Button(body, text="💾  حفظ",
                  command=do_save,
                  bg=ACCENT, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=9, cursor="hand2",
                  activebackground="#2563eb",
                  activeforeground="white").pack(fill="x", pady=(14, 0))

        if self.apps[idx]:
            cur = self.apps[idx]
            name_e.insert(0, cur.get('name', ''))
            path_e.insert(0, cur.get('path', ''))
            c = cur.get('color', DEFAULT_COLOR)
            color_e.delete(0, tk.END); color_e.insert(0, c)
            prev.config(bg=c)

    # ----------------------------------------------------------
    #  تشغيل، فتح مجلد، حذف، نسخ
    # ----------------------------------------------------------
    def run_app(self, idx):
        app = self.apps[idx] if idx < SLOTS else None
        if not app:
            self.edit_slot(idx); return
        p = app.get('path', '')
        if not os.path.exists(p):
            if messagebox.askyesno("ملف مفقود",
                                    f"'{app['name']}' غير موجود.\nهل تريد إعادة تعيينه؟"):
                self.move_to_trash(idx)
                self.edit_slot(idx)
            return
        try:
            if sys.platform == 'win32': os.startfile(p)
            elif sys.platform == 'darwin': subprocess.Popen(['open', p])
            else: subprocess.Popen(['xdg-open', p])
            self.set_status(f"▶  {app['name']}", "#22c55e", 3000)
        except Exception as ex:
            messagebox.showerror("خطأ", f"فشل التشغيل:\n{ex}")

    def open_folder(self, idx):
        app = self.apps[idx] if idx < SLOTS else None
        if not app: return
        folder = os.path.dirname(app.get('path', ''))
        if os.path.isdir(folder):
            if sys.platform == 'win32': os.startfile(folder)
            elif sys.platform == 'darwin': subprocess.Popen(['open', folder])
            else: subprocess.Popen(['xdg-open', folder])
            self.set_status("📂  فتح المجلد", ACCENT, 2000)

    def move_to_trash(self, idx):
        app = self.apps[idx] if idx < SLOTS else None
        if not app: return
        item = {**app,
                'deleted_date':  datetime.now().strftime("%Y-%m-%d %H:%M"),
                'original_slot': idx}
        self.trash.append(item)
        self.save_trash()
        self.apps[idx] = None
        self.save_apps()
        self._refresh_btn(idx)
        self._update_counter()
        self.set_status(f"🗑  {app['name']} → السلة", "#f59e0b", 3000)

    def copy_path(self, idx):
        app = self.apps[idx] if idx < SLOTS else None
        if app and app.get('path'):
            self.root.clipboard_clear()
            self.root.clipboard_append(app['path'])
            self.set_status("📋  تم نسخ المسار", "#a78bfa", 2000)

    # ----------------------------------------------------------
    #  سلة المحذوفات
    # ----------------------------------------------------------
    def show_trash(self):
        win = self._popup(500, 440, f"🗑  السلة  ({len(self.trash)})")
        body = tk.Frame(win, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        if not self.trash:
            tk.Label(body, text="السلة فارغة", fg="#334155",
                     bg=BG_DARK, font=("Segoe UI", 14)
                     ).place(relx=.5, rely=.5, anchor="center")
        else:
            cv = tk.Canvas(body, bg=BG_DARK, highlightthickness=0)
            sb = tk.Scrollbar(body, orient="vertical", command=cv.yview, width=5)
            sf = tk.Frame(cv, bg=BG_DARK)
            sf.bind("<Configure>", lambda e:
                cv.configure(scrollregion=cv.bbox("all")))
            cw = cv.create_window((0, 0), window=sf, anchor="nw")
            cv.configure(yscrollcommand=sb.set)
            cv.bind("<Configure>", lambda e: cv.itemconfig(cw, width=e.width))
            cv.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")

            def rebuild(): win.destroy(); self.show_trash()

            for i, item in enumerate(self.trash):
                ifrm = tk.Frame(sf, bg=BG_MID,
                                highlightthickness=1, highlightbackground=BG_BORDER)
                ifrm.pack(fill="x", pady=3)
                lf = tk.Frame(ifrm, bg=BG_MID)
                lf.pack(side="left", fill="x", expand=True, padx=12, pady=8)
                n = item.get('name', '؟')
                tk.Label(lf, text=f"{self._icon(n)}  {n}",
                         fg="#e2e8f0", bg=BG_MID,
                         font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w")
                tk.Label(lf, text=f"حُذف: {item.get('deleted_date','---')}",
                         fg=TEXT_MUTED, bg=BG_MID,
                         font=("Segoe UI", 8), anchor="w").pack(anchor="w")

                rf = tk.Frame(ifrm, bg=BG_MID)
                rf.pack(side="right", padx=8)

                def restore(i2=i, nm=n):
                    for s in range(SLOTS):
                        if self.apps[s] is None:
                            obj = self.trash.pop(i2)
                            obj.pop('deleted_date', None)
                            obj.pop('original_slot', None)
                            self.apps[s] = obj
                            self.save_apps()
                            self.save_trash()
                            self._refresh_btn(s)
                            self._update_counter()
                            win.destroy()
                            self.set_status(f"↩  {nm} استُعيد", "#22c55e", 3000)
                            return
                    messagebox.showwarning("ممتلئ","جميع الخانات ممتلئة!",parent=win)

                def perm_del(i2=i, nm=n):
                    if messagebox.askyesno("حذف نهائي",
                                            f"حذف '{nm}' نهائياً؟", parent=win):
                        self.trash.pop(i2); self.save_trash(); rebuild()

                tk.Button(rf, text="↩ استعادة", command=restore,
                          bg="#064e3b", fg="#22c55e", relief="flat",
                          padx=10, pady=4, font=("Segoe UI", 8),
                          cursor="hand2").pack(side="left", padx=3)
                tk.Button(rf, text="✕ حذف", command=perm_del,
                          bg="#450a0a", fg="#ef4444", relief="flat",
                          padx=10, pady=4, font=("Segoe UI", 8),
                          cursor="hand2").pack(side="left", padx=3)

            tk.Button(win, text="🗑  تفريغ السلة",
                      command=lambda: self._empty_trash(win),
                      bg="#450a0a", fg="#ef4444",
                      font=("Segoe UI", 9, "bold"),
                      relief="flat", pady=8, cursor="hand2"
                      ).pack(fill="x", padx=12, pady=(4, 10))

    def _empty_trash(self, win):
        if messagebox.askyesno("تحذير","حذف الكل نهائياً؟",parent=win):
            self.trash.clear(); self.save_trash()
            win.destroy()
            self.set_status("🗑  تم تفريغ السلة", "#f59e0b", 3000)

    # ----------------------------------------------------------
    #  الإعدادات
    # ----------------------------------------------------------
    def show_settings(self):
        win = self._popup(380, 330, "⚙  الإعدادات")
        body = tk.Frame(win, bg=BG_DARK, padx=18, pady=12)
        body.pack(fill="both", expand=True)

        alive   = sum(1 for a in self.apps if a and os.path.exists(a.get('path','')))
        missing = sum(1 for a in self.apps if a and not os.path.exists(a.get('path','')))

        info_f = tk.Frame(body, bg=BG_MID,
                           highlightthickness=1, highlightbackground=BG_BORDER)
        info_f.pack(fill="x", pady=(0, 12))
        disp_dir = APP_DIR if len(APP_DIR) <= 42 else "…" + APP_DIR[-40:]
        rows = [("مجلد البيانات", disp_dir),
                ("برامج محملة",   f"{alive}/{SLOTS}"),
                ("ملفات مفقودة",  str(missing)),
                ("في السلة",      str(len(self.trash))),
                ("الصلاحيات",     "مسؤول ✔" if is_admin() else "مستخدم عادي")]
        for k, v in rows:
            r = tk.Frame(info_f, bg=BG_MID)
            r.pack(fill="x", padx=14, pady=4)
            tk.Label(r, text=k, fg=TEXT_MUTED, bg=BG_MID,
                     font=("Segoe UI", 9)).pack(side="left")
            tk.Label(r, text=v, fg=TEXT_PRIMARY, bg=BG_MID,
                     font=("Segoe UI", 9, "bold")).pack(side="right")

        def _btn(txt, bg, fg, cmd):
            b = tk.Button(body, text=txt, command=cmd,
                          bg=bg, fg=fg, relief="flat",
                          pady=8, font=("Segoe UI", 9), cursor="hand2")
            b.pack(fill="x", pady=3)

        _btn("↺  استعادة نسخة احتياطية",
             BG_MID, "#94a3b8",
             lambda: (win.destroy(), self.restore_backup()))

        if os.path.exists(ADMIN_FLAG) and not is_admin():
            def reset_adm():
                try: os.remove(ADMIN_FLAG)
                except: pass
                messagebox.showinfo("تم",
                    "سيُطلب منك قرار الصلاحيات في المرة القادمة.", parent=win)
                win.destroy()
            _btn("🔑  تغيير قرار صلاحيات المسؤول",
                 "#1e3a5f", "#60a5fa", reset_adm)

        if is_admin():
            def revoke_adm():
                with open(ADMIN_FLAG, 'w') as f: f.write('no')
                messagebox.showinfo("تم",
                    "سيُشغَّل البرنامج بدون صلاحيات مسؤول في المرة القادمة.",
                    parent=win)
                win.destroy()
            _btn("🔒  التراجع عن صلاحيات المسؤول",
                 "#1c1917", "#a3a3a3", revoke_adm)

    # ----------------------------------------------------------
    #  نسخ احتياطية
    # ----------------------------------------------------------
    def restore_backup(self):
        if messagebox.askyesno("استعادة","استعادة آخر نسخة احتياطية؟"):
            data = self._load_json(BACKUP, None)
            if isinstance(data, list) and len(data) == SLOTS:
                self.apps = data
                self.save_apps()
                self._refresh_all()
                self.set_status("↺  تم الاستعادة", "#22c55e", 3000)
            else:
                messagebox.showwarning("غير موجود","لا توجد نسخة احتياطية صالحة")

    def _refresh_all(self):
        for i in range(SLOTS): self._refresh_btn(i)
        self._update_counter()

    def _update_counter(self):
        alive   = sum(1 for a in self.apps if a and os.path.exists(a.get('path','')))
        missing = sum(1 for a in self.apps if a and not os.path.exists(a.get('path','')))
        txt = f"● {alive}/{SLOTS}"
        if missing: txt += f"  ⚠{missing}"
        self._counter.config(text=txt)

    def set_status(self, msg, color=TEXT_MUTED, clear_after=0):
        if self._sts_id:
            try: self.root.after_cancel(self._sts_id)
            except: pass
            self._sts_id = None
        self._status.config(text=msg, fg=color)
        if clear_after:
            self._sts_id = self.root.after(
                clear_after,
                lambda: self._status.config(text="جاهز", fg=TEXT_MUTED))

    # ----------------------------------------------------------
    #  مفاتيح الاختصار
    # ----------------------------------------------------------
    def _bind_hotkeys(self):
        self.root.bind('<Escape>',    lambda e: self.on_close())
        self.root.bind('<Control-s>', lambda e: self.save_apps())
        self.root.bind('<Control-f>', lambda e: (
            self._search.focus(),
            self._search.select_range(0, tk.END)))
        self.root.bind('<F5>',        lambda e: self._refresh_all())
        for i in range(1, min(10, SLOTS+1)):
            self.root.bind(f'<Control-Key-{i}>',
                           lambda e, n=i-1: self.run_app(n))

    # ----------------------------------------------------------
    #  مساعدات النافذة
    # ----------------------------------------------------------
    def _popup(self, w, h, title=""):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.configure(bg=BG_DARK)
        win.grab_set()
        x = self.root.winfo_x() + (self.root.winfo_width()  - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")
        hdr = tk.Frame(win, bg=BG_MID, height=42)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=title, fg=TEXT_PRIMARY, bg=BG_MID,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=14, pady=10)
        xb = tk.Label(hdr, text="✕", fg="#94a3b8", bg=BG_MID,
                      font=("Segoe UI", 13), cursor="hand2")
        xb.pack(side="right", padx=10)
        xb.bind("<Button-1>", lambda e: win.destroy())
        xb.bind("<Enter>",    lambda e: xb.config(fg="#ef4444"))
        xb.bind("<Leave>",    lambda e: xb.config(fg="#94a3b8"))
        return win

    def center_window(self, w, h):
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _drag_start(self, e): self._drag_x, self._drag_y = e.x, e.y
    def _drag_move(self, e):
        self.root.geometry(
            f"+{self.root.winfo_x()+e.x-self._drag_x}"
            f"+{self.root.winfo_y()+e.y-self._drag_y}")

    def _scroll(self, e):
        self._canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def on_close(self):
        if messagebox.askyesno("خروج","هل تريد الخروج؟"):
            self.save_apps()
            self.root.destroy()


# =============================================================
if __name__ == "__main__":
    RobustLauncher()
