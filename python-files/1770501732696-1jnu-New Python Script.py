import psutil
import threading
import time
import tkinter as tk
from tkinter import ttk

# ===========================
# المتغيرات الأساسية
# ===========================
monitoring = False
base_pids = set()
process_log = {}

# ===========================
# دالة المراقبة
# ===========================
def monitor_processes():
    global monitoring, base_pids, process_log
    while monitoring:
        current_pids = set()
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            pid = proc.info['pid']
            current_pids.add(pid)

            # فقط العمليات الجديدة
            if pid not in base_pids and pid not in process_log:
                process_log[pid] = {
                    "name": proc.info['name'],
                    "start": time.strftime("%H:%M:%S", time.localtime(proc.info['create_time'])),
                    "end": "",
                    "status": "new"  # جديدة
                }

        # تحديث العمليات المتوقفة
        for pid in list(process_log.keys()):
            if pid not in current_pids and process_log[pid]["end"] == "":
                process_log[pid]["end"] = time.strftime("%H:%M:%S")
                process_log[pid]["status"] = "stopped"  # توقفت
            elif process_log[pid]["end"] == "":
                process_log[pid]["status"] = "running"  # لا تزال تعمل

        update_table()
        time.sleep(1)

# ===========================
# دوال الأزرار
# ===========================
def start_monitoring(event=None):
    global monitoring, base_pids, process_log
    if not monitoring:
        base_pids = {p.pid for p in psutil.process_iter()}
        process_log = {}
        monitoring = True
        threading.Thread(target=monitor_processes, daemon=True).start()
        status_label.config(text="🟢 المراقبة تعمل الآن...")

def stop_monitoring(event=None):
    global monitoring
    monitoring = False
    status_label.config(text="🔴 تم إيقاف المراقبة")
    # تحديث الجدول النهائي
    for pid in process_log:
        if process_log[pid]["end"] == "":
            process_log[pid]["status"] = "running"
    update_table()

# ===========================
# تحديث الجدول مع الألوان
# ===========================
def update_table():
    for row in tree.get_children():
        tree.delete(row)
    for pid, p in process_log.items():
        item = tree.insert("", "end", values=(p['name'], p['start'], p['end'] or "ما زالت تعمل"))
        # تعيين الألوان
        if p["status"] == "new":
            tree.item(item, tags=("new",))
        elif p["status"] == "running":
            tree.item(item, tags=("running",))
        elif p["status"] == "stopped":
            tree.item(item, tags=("stopped",))
    # إعداد الأنماط
    tree.tag_configure("new", foreground="green")
    tree.tag_configure("running", foreground="green")
    tree.tag_configure("stopped", foreground="red")

# ===========================
# واجهة المستخدم
# ===========================
root = tk.Tk()
root.title("مراقبة العمليات الجديدة")
root.geometry("600x400")

# أزرار التشغيل والإيقاف
btn_start = tk.Button(root, text="تشغيل (F1)", command=start_monitoring, bg="#4CAF50", fg="white", font=("Arial", 12))
btn_start.pack(pady=5)

btn_stop = tk.Button(root, text="إيقاف (F2)", command=stop_monitoring, bg="#F44336", fg="white", font=("Arial", 12))
btn_stop.pack(pady=5)

# حالة المراقبة
status_label = tk.Label(root, text="🔴 المراقبة متوقفة", font=("Arial", 12))
status_label.pack(pady=5)

# جدول عرض البيانات
columns = ("اسم العملية", "وقت البدء", "وقت الإيقاف")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=180, anchor="center")
tree.pack(expand=True, fill="both", pady=10)

# ===========================
# اختصارات لوحة المفاتيح
# ===========================
root.bind("<F1>", start_monitoring)
root.bind("<F2>", stop_monitoring)

# ===========================
# تشغيل البرنامج
# ===========================
root.mainloop()
