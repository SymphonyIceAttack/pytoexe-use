import tkinter as tk
from tkinter import filedialog, messagebox
import os

def apply_patch():
    file_path = entry_path.get().strip().replace('"', '')
    
    if not file_path:
        messagebox.showerror("خطأ", "الرجاء تحديد مسار ملف BIO4.EXE أولاً.")
        return
        
    if not os.path.exists(file_path):
        messagebox.showerror("خطأ", "الملف المحدد غير موجود.")
        return

    if os.path.basename(file_path).upper() != "BIO4.EXE":
        messagebox.showerror("تنبيه", "اسم الملف ليس BIO4.EXE، تأكد من اختيار الملف الصحيح.")
        return

    try:
        offset = 0x1BD1D0
        byte_data = b'\xC3'
        
        with open(file_path, "r+b") as f:
            f.seek(offset)
            f.write(byte_data)
            
        messagebox.showinfo("نجاح", "تم تطبيق التعديل بنجاح.")
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ أثناء تعديل الملف:\n{str(e)}")

def browse_file():
    path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)

# إعداد النافذة الرئيسية
root = tk.Tk()
root.title("BIO4 Patcher")
root.geometry("500x180")
root.configure(bg="black")
root.resizable(False, False)

# الأنماط العامة
bg_color = "black"
fg_color = "white"
entry_bg = "#222222"
btn_bg = "#333333"
btn_active_bg = "#444444"

# العناصر الواجهة
label_title = tk.Label(root, text="BIO4.EXE Offset Modifier", bg=bg_color, fg=fg_color, font=("Arial", 12, "bold"))
label_title.pack(pady=10)

frame_input = tk.Frame(root, bg=bg_color)
frame_input.pack(pady=10, fill=tk.X, px=20)

entry_path = tk.Entry(frame_input, bg=entry_bg, fg=fg_color, insertbackground=fg_color, font=("Arial", 10))
entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, px=(0, 5))

btn_browse = tk.Button(frame_input, text="...", bg=btn_bg, fg=fg_color, activebackground=btn_active_bg, activeforeground=fg_color, width=5, command=browse_file, relief=tk.FLAT)
btn_browse.pack(side=tk.RIGHT)

btn_apply = tk.Button(root, text="Apply", bg=btn_bg, fg=fg_color, activebackground=btn_active_bg, activeforeground=fg_color, font=("Arial", 11, "bold"), width=15, command=apply_patch, relief=tk.FLAT)
btn_apply.pack(pady=15)

root.mainloop()
