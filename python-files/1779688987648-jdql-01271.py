import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab, Image, ImageTk
import os, json

# ---------- 基本資料 ----------
LEFT_ITEMS = [
    "缺牙", "阻生齒", "植牙", "殘根",
    "牙冠牙橋", "曾根管治療", "齲齒", "根尖病灶"
]

TEETH = {
    "18-11": list(range(18, 10, -1)),
    "21-28": list(range(21, 29)),
    "48-41": list(range(48, 40, -1)),
    "31-38": list(range(31, 39)),
}

# ---------- 主視窗 ----------
root = tk.Tk()
root.title("牙科病灶快速紀錄")
screen_w = root.winfo_screenwidth()
root.geometry(f"{screen_w}x600")

current_item = tk.StringVar(value="")
temp_data = {item: set() for item in LEFT_ITEMS}

# ---------- 左側欄 ----------
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

tk.Label(left_frame, text="病灶項目", font=("Arial", 12, "bold")).pack()
for item in LEFT_ITEMS:
    tk.Radiobutton(left_frame, text=item, value=item, variable=current_item).pack(anchor="w")

# ---------- 中間區 ----------
right_frame = tk.Frame(root)
right_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

# ---------- 牙位按鈕 ----------
tooth_frame = tk.Frame(right_frame)
tooth_frame.pack(pady=5)

def toggle_tooth(item, tooth):
    if not item:
        messagebox.showwarning("提醒", "請先選擇左側項目")
        return
    if tooth in temp_data[item]:
        temp_data[item].remove(tooth)
    else:
        temp_data[item].add(tooth)
    refresh_temp()

for row, (label, teeth) in enumerate(TEETH.items()):
    f = tk.Frame(tooth_frame)
    f.grid(row=row//2, column=row%2, padx=5, pady=5)
    tk.Label(f, text=label).pack()
    for t in teeth:
        tk.Button(f, text=str(t), width=4, command=lambda t=t: toggle_tooth(current_item.get(), t)).pack(side=tk.LEFT)

# ---------- 暫存區 ----------
tk.Label(right_frame, text="暫存區", font=("Arial", 11, "bold")).pack()
temp_box = tk.Text(right_frame, height=6)
temp_box.pack(fill=tk.X, padx=10)

def refresh_temp():
    temp_box.delete("1.0", tk.END)
    for k, v in temp_data.items():
        if v:
            temp_box.insert(tk.END, f"{k}: {', '.join(map(str, sorted(v)))}\n")

# ---------- 操作按鈕 ----------
btn_frame = tk.Frame(right_frame)
btn_frame.pack(pady=5)

final_box = tk.Text(right_frame, height=8)
final_box.pack(fill=tk.BOTH, expand=True, padx=10)

def add_temp():
    final_box.insert(tk.END, temp_box.get("1.0", tk.END))
    clear_temp()

def clear_temp():
    for k in temp_data:
        temp_data[k].clear()
    refresh_temp()

tk.Button(btn_frame, text="加入暫存", command=add_temp).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="清除暫存", command=clear_temp).pack(side=tk.LEFT, padx=5)

# ---------- 截圖顯示區 ----------
screenshot_frame = tk.Frame(root)
screenshot_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

screenshot_label = tk.Label(screenshot_frame, text="尚未擷取截圖")
screenshot_label.pack()

save_dir = r"C:\Users\Ray\Desktop\PANO"
os.makedirs(save_dir, exist_ok=True)

# name.txt 控制編號
name_file = os.path.join(save_dir, "name.txt")
if not os.path.exists(name_file):
    with open(name_file, "w") as f:
        f.write("1")

with open(name_file, "r") as f:
    current_idx = int(f.read().strip())

def capture_pano():
    global current_idx
    img = ImageGrab.grabclipboard()
    if isinstance(img, Image.Image):
        target_w = screen_w // 3
        w, h = img.size
        target_h = int(h * (target_w / w))
        img_resized = img.resize((target_w, target_h))

        tk_img = ImageTk.PhotoImage(img_resized)
        screenshot_label.config(image=tk_img)
        screenshot_label.image = tk_img

        filename = f"{current_idx}.jpg"
        img.save(os.path.join(save_dir, filename), "JPEG")
    else:
        messagebox.showwarning("提醒", "剪貼簿沒有影像")

# 啟動時提示並擷取一次
messagebox.showinfo("提示", "請先擷取 pano 片至剪貼簿")
capture_pano()

# ---------- 單選詢問視窗 ----------
def ask_conditions():
    dialog = tk.Toplevel(root)
    dialog.title("牙周與鼻竇狀況")

    perio_var = tk.StringVar(value="健康")
    sinus_var = tk.StringVar(value="無異常")

    tk.Label(dialog, text="牙周健康狀況", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=5)
    for option in ["健康", "牙齦炎", "牙周病"]:
        tk.Radiobutton(dialog, text=option, variable=perio_var, value=option).pack(anchor="w", padx=20)

    tk.Label(dialog, text="鼻竇病灶", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=5)
    for option in ["無異常", "左側", "右側"]:
        tk.Radiobutton(dialog, text=option, variable=sinus_var, value=option).pack(anchor="w", padx=20)

    def confirm():
        dialog.destroy()

    tk.Button(dialog, text="確定", command=confirm).pack(pady=10)

    dialog.grab_set()
    root.wait_window(dialog)

    return perio_var.get(), sinus_var.get()

# ---------- 完成與剪貼簿 ----------
def finish():
    global current_idx
    perio, sinus = ask_conditions()
    if not perio or not sinus:
        return

    result = []
    idx = 1
    for line in final_box.get("1.0", tk.END).strip().splitlines():
        if line.strip():
            result.append(f"{idx}. {line}")
            idx += 1

    result.append(f"{idx}. 牙周狀況：{perio}")
    result.append(f"{idx+1}. 鼻竇狀況：{sinus}")

    final_text = "\n".join(result)

    root.clipboard_clear()
    root.clipboard_append(final_text)
    root.update()

    json_data = {"result": result}
    filename = f"{current_idx}.txt"
    with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 更新 name.txt 數值 +1
    with open(name_file, "w") as f:
        f.write(str(current_idx + 1))

    messagebox.showinfo("完成", "資料已複製到剪貼簿並輸出 JSON")

def clear_all():
    final_box.delete("1.0", tk.END)
    clear_temp()

final_btn_frame = tk.Frame(right_frame)
final_btn_frame.pack(pady=5)

tk.Button(final_btn_frame, text="確定完成", command=finish).pack(side=tk.LEFT, padx=5)
tk.Button(final_btn_frame, text="清除資料", command=clear_all).pack(side=tk.LEFT, padx=5)

root.mainloop()
