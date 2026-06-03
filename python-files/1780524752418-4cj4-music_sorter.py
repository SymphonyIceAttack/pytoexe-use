import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from mutagen import File

# لیست خوانندگان کردی (می‌توانید اینجا نام‌های بیشتری اضافه کنید)
KURDISH_ARTISTS = ["حسن زیرک", "ناصر رزازی", "آوات بوکانی", "سیوان گاگلی", "مظهر خالقی", "کارزان", "برزان"]
MIX_KEYWORDS = ["remix", "mix", "dj", "ریمیکس", "میکس"]

def sort_music(source_dir, dest_dir):
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.mp3', '.m4a', '.flac')):
                path = os.path.join(root, file)
                try:
                    audio = File(path, easy=True)
                    artist = (audio.get('artist', [''])[0]).lower()
                    title = (audio.get('title', [''])[0]).lower()
                    
                    is_kurdish = any(k in artist or k in title for k in [k.lower() for k in KURDISH_ARTISTS])
                    is_mix = any(m in artist or m in title for m in MIX_KEYWORDS)
                    
                    if is_kurdish:
                        folder = "Kurdish Mix" if is_mix else "Kurdish"
                    else:
                        folder = "Persian Mix" if is_mix else "Persian"
                    
                    target_path = os.path.join(dest_dir, folder)
                    os.makedirs(target_path, exist_ok=True)
                    shutil.copy2(path, os.path.join(target_path, file))
                except:
                    continue
    messagebox.showinfo("موفقیت", "دسته‌بندی با موفقیت انجام شد!")

# طراحی پنجره گرافیکی
root = tk.Tk()
root.title("مرتب‌ساز آهنگ")
def start():
    s = filedialog.askdirectory(title="پوشه آهنگ‌ها")
    d = filedialog.askdirectory(title="پوشه مقصد")
    if s and d: sort_music(s, d)

tk.Button(root, text="انتخاب پوشه و شروع", command=start, height=5, width=30).pack(pady=20)
root.mainloop()
