import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

# إنشاء نافذة البرنامج
root = tk.Tk()
root.title("برنامج فرز الملفات الذكي")
root.geometry("400x150")

def sort_files():
    # اختيار المجلد من المستخدم
    path = filedialog.askdirectory(title="اختر المجلد للفرز")
    if not path:  # إذا ما اختار شيء
        return
    
    # أنواع الملفات
    file_types = {
        "صور": [".jpg", ".png", ".jpeg", ".gif"],
        "فيديو": [".mp4", ".mkv", ".avi"],
        "مستندات": [".pdf", ".docx", ".txt", ".xlsx"],
        "صوتيات": [".mp3", ".wav", ".aac"],
        "برامج": [".exe", ".msi"],
        "ضغط": [".zip", ".rar", ".7z"]
    }

    # فرز الملفات
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            for folder, exts in file_types.items():
                if ext in exts:
                    folder_path = os.path.join(path, folder)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                    shutil.move(file_path, os.path.join(folder_path, file))

    messagebox.showinfo("تم", "تم فرز الملفات بنجاح! 🚀")

# زر لاختيار المجلد وبدء الفرز
btn = tk.Button(root, text="اختر مجلد وابدأ الفرز", command=sort_files, width=30, height=2)
btn.pack(expand=True)

root.mainloop()