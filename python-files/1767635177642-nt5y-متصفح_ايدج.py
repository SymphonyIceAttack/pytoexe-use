import tkinter as tk
import webbrowser
import os

# مسار Microsoft Edge (غالبًا موجود كده عند الكل)
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# لو موجود، نسجله كمتصفح
if os.path.exists(edge_path):
    webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
    browser = webbrowser.get('edge')
else:
    browser = webbrowser  # لو مش موجود، يستخدم المتصفح الافتراضي

# الواجهة
root = tk.Tk()
root.title("متصفح Edge الرائع 🚀")
root.geometry("800x500")
root.configure(bg="#1a1a2e")

tk.Label(root, text="افتح أي موقع في Microsoft Edge", font=("Arial", 24, "bold"), fg="#00b7eb", bg="#1a1a2e").pack(pady=40)
tk.Label(root, text="اكتب الرابط أو ابحث (مثل: يوتيوب أو فيسبوك)", font=("Arial", 14), fg="#aaa", bg="#1a1a2e").pack(pady=10)

entry = tk.Entry(root, font=("Arial", 18), width=50, justify="center")
entry.pack(pady=30)
entry.focus()

def open_site():
    text = entry.get().strip()
    if not text:
        return
    
    if " " in text or "." not in text:
        url = "https://www.google.com/search?q=" + text.replace(" ", "+")
    else:
        url = "https://" + text if not text.startswith("http") else text
    
    browser.open_new_tab(url)
    entry.delete(0, tk.END)

tk.Button(root, text="اذهب!", command=open_site, font=("Arial", 20, "bold"), bg="#00b7eb", fg="white", width=15, height=2).pack(pady=20)

tk.Label(root, text="البرنامج شغال 100% بدون تثبيت أي حاجة إضافية 🌟", font=("Arial", 10), fg="#666", bg="#1a1a2e").pack(side="bottom", pady=20)

root.mainloop()