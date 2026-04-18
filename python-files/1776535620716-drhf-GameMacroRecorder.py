import json
import time
import threading
from pynput import keyboard, mouse
import tkinter as tk
from tkinter import messagebox, ttk

# متغيرات التسجيل
recorded = []
recording = False
start_time = 0
play_key = 'f1'  # الزر الافتراضي لتشغيل الماكرو

# وظائف التسجيل
def on_press(key):
    if recording:
        recorded.append(('key_press', str(key), time.time()))

def on_release(key):
    if recording:
        recorded.append(('key_release', str(key), time.time()))

def on_click(x, y, button, pressed):
    if recording:
        recorded.append(('mouse', x, y, str(button), pressed, time.time()))

# بدء التسجيل
def start_recording():
    global recording, recorded, start_time
    recorded.clear()
    recording = True
    start_time = time.time()
    status_label.config(text="✅ التسجيل جارٍ... اضغط Ctrl+Shift+R لإيقافه")

# إيقاف التسجيل
def stop_recording():
    global recording
    recording = False
    status_label.config(text="⏸️ التسجيل متوقف. اضغط 'حفظ' لحفظ الماكرو.")

# تشغيل الماكرو
def play_macro():
    if not recorded:
        messagebox.showwarning("تحذير", "لا يوجد ماكرو مسجل!")
        return

    def play():
        first_time = recorded
        for event in recorded:
            if event == 'key_press':
                key = eval(event) if 'Key.' in event else event.strip("'")
                keyboard.Controller().press(key)
            elif event == 'key_release':
                key = eval(event) if 'Key.' in event else event.strip("'")
                keyboard.Controller().release(key)
            elif event == 'mouse':
                x, y, button, pressed, t = event, event, event, event, event
                mouse.Controller().position = (x, y)
                if pressed:
                    mouse.Controller().press(eval(button))
                else:
                    mouse.Controller().release(eval(button))
            # تأخير
            time.sleep(max(0, event - first_time))
            first_time = event

    thread = threading.Thread(target=play)
    thread.start()

# تشغيل الماكرو عند الضغط على الزر المحدد
def on_global_press(key):
    try:
        if str(key).lower() == f"'{play_key.lower()}'" or str(key) == f'Key.{play_key.lower()}':
            play_macro()
    except:
        pass

# حفظ الماكرو
def save_macro():
    if not recorded:
        messagebox.showwarning("تحذير", "لا يوجد ماكرو لحفظه!")
        return
    try:
        with open("macro.json", "w", encoding="utf-8") as f:
            json.dump(recorded, f, indent=2)
        messagebox.showinfo("تم", "تم حفظ الماكرو بنجاح في ملف macro.json")
    except Exception as e:
        messagebox.showerror("خطأ", f"فشل الحفظ: {e}")

# تحميل الماكرو
def load_macro():
    global recorded
    try:
        with open("macro.json", "r", encoding="utf-8") as f:
            recorded = json.load(f)
        messagebox.showinfo("تم", "تم تحميل الماكرو من macro.json")
    except FileNotFoundError:
        messagebox.showerror("خطأ", "لم يتم العثور على ملف macro.json")
    except Exception as e:
        messagebox.showerror("خطأ", f"فشل التحميل: {e}")

# تغيير زر التشغيل
def change_play_key():
    global play_key
    new_key = key_entry.get().strip().lower()
    if new_key:
        play_key = new_key
        messagebox.showinfo("تم", f"تم تغيير زر التشغيل إلى: {play_key}")
    else:
        messagebox.showwarning("تحذير", "أدخل زراً صالحاً (مثل: f1, a, ctrl)")

# واجهة المستخدم
root = tk.Tk()
root.title("GameMacroRecorder - بدون إنترنت")
root.geometry("400x350")
root.resizable(False, False)

tk.Label(root, text="GameMacroRecorder", font=("Arial", 16, "bold")).pack(pady=10)

status_label = tk.Label(root, text="⚠️ اضغط 'بدء التسجيل' لبدء تسجيل ماكرو", fg="blue")
status_label.pack(pady=5)

btn_start = tk.Button(root, text="🟢 بدء التسجيل", command=start_recording, width=20)
btn_start.pack(pady=5)

btn_stop = tk.Button(root, text="🔴 إيقاف التسجيل", command=stop_recording, width=20)
btn_stop.pack(pady=5)

btn_save = tk.Button(root, text="💾 حفظ الماكرو", command=save_macro, width=20)
btn_save.pack(pady=5)

btn_load = tk.Button(root, text="📂 تحميل الماكرو", command=load_macro, width=20)
btn_load.pack(pady=5)

btn_play = tk.Button(root, text="▶️ تشغيل الماكرو", command=play_macro, width=20)
btn_play.pack(pady=5)

tk.Label(root, text=f"زر التشغيل الحالي: {play_key.upper()}").pack(pady=5)
key_entry = tk.Entry(root, width=10)
key_entry.insert(0, play_key)
key_entry.pack()
btn_change_key = tk.Button(root, text="🔄 تغيير زر التشغيل", command=change_play_key, width=20)
btn_change_key.pack(pady=5)

# بدء الاستماع
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener = mouse.Listener(on_click=on_click)
global_listener = keyboard.Listener(on_press=on_global_press)

keyboard_listener.start()
mouse_listener.start()
global_listener.start()

root.mainloop()