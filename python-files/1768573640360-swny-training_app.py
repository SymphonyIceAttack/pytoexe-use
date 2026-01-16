import tkinter as tk
from tkinter import messagebox

# ---------------------------
# بيانات التمارين
# ---------------------------
exercises = [
    ("تمرين السرعة (بدون كرة)", "الجري في المكان بسرعة لمدة 30 ثانية"),
    ("تمرين الرشاقة", "قفز يمين - يسار 20 مرة"),
    ("تمرين التوازن", "الوقوف على رجل واحدة 30 ثانية"),
    ("تمرين القوة", "سكوات 15 مرة"),
    ("تمرين المرونة", "لمس القدمين 20 مرة"),
    ("تمرين التحمل", "قفز بالحبل (بدون حبل) 40 ثانية"),
    ("تمرين الكارديو", "نط متقطع 30 ثانية"),
    ("تمرين الانفجار", "قفزة عالية 10 مرات"),
    ("تمرين الجاهزية", "Sprint صغير داخل المنزل 20 ثانية"),
]

# ---------------------------
# تهيئة التطبيق
# ---------------------------
root = tk.Tk()
root.title("تطبيق تمارين الجناح الأيسر")
root.geometry("480x450")
root.resizable(False, False)

# ---------------------------
# دالة لحفظ التقييم بعد التمرين
# ---------------------------
def save_result(ex_name, result):
    with open("progress.txt", "a", encoding="utf-8") as file:
        file.write(f"{ex_name} — النتيجة: {result}\n")

    messagebox.showinfo("تم الحفظ", "تم تسجيل نتيجتك بنجاح!")

# ---------------------------
# عرض التمرين المختار
# ---------------------------
def show_exercise(index):
    name, desc = exercises[index]

    top = tk.Toplevel()
    top.title(name)
    top.geometry("450x300")

    tk.Label(top, text=name, font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(top, text=desc, font=("Arial", 12)).pack(pady=10)

    tk.Label(top, text="أدخل تقييمك بعد إنهاء التمرين:", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(top, width=20)
    entry.pack(pady=5)

    def save():
        result = entry.get()
        if not result.strip():
            messagebox.showwarning("خطأ", "الرجاء إدخال التقييم!")
            return
        save_result(name, result)
        top.destroy()

    tk.Button(top, text="حفظ النتيجة", command=save, bg="#4CAF50", fg="white").pack(pady=20)

# ---------------------------
# عرض قائمة التمارين
# ---------------------------
tk.Label(root, text="قائمة التمارين", font=("Arial", 20, "bold")).pack(pady=10)

for idx, ex in enumerate(exercises):
    tk.Button(root, text=ex[0], width=40, command=lambda i=idx: show_exercise(i)).pack(pady=5)

# ---------------------------
# تشغيل التطبيق
# ---------------------------
root.mainloop()
