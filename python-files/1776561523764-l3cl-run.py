import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def load_config():
    with open("More Inventory-JSON.json", "r", encoding="utf-8") as f:
        return json.load(f)

def patch_file(game_file_path, offset, original_hex, patched_hex):
    try:
        original = bytes.fromhex(original_hex)
        patched = bytes.fromhex(patched_hex)
        offset_int = int(offset)
        with open(game_file_path, "rb+") as f:
            f.seek(offset_int)
            current = f.read(len(original))
            if current != original:
                messagebox.showwarning("警告", f"偏移{offset}原始值不匹配！")
                return False
            f.seek(offset_int)
            f.write(patched)
        return True
    except:
        messagebox.showerror("错误", "补丁失败")
        return False

def apply_patch(selected_option):
    config = load_config()
    changes = config["patches"][0]["changes"]
    target = None
    for c in changes:
        if c["label"] == selected_option:
            target = c
            break
    if not target:
        messagebox.showerror("错误", "未找到配置")
        return
    game_file = filedialog.askopenfilename(filetypes=[("PABGB", "*.pabgb"), ("所有", "*.*")])
    if not game_file:
        return
    if patch_file(game_file, target["offset"], target["original"], target["patched"]):
        messagebox.showinfo("成功", "补丁完成！")

def main():
    root = tk.Tk()
    root.title("库存修改工具")
    root.geometry("400x200")
    config = load_config()
    options = [c["label"] for c in config["patches"][0]["changes"]]
    ttk.Label(root, text="选择库存档位：").pack(pady=20)
    var = tk.StringVar()
    combo = ttk.Combobox(root, textvariable=var, values=options, state="readonly")
    combo.pack(pady=10)
    combo.current(0)
    ttk.Button(root, text="应用补丁", command=lambda: apply_patch(var.get())).pack(pady=20)
    root.mainloop()

if __name__ == "__main__":
    if not os.path.exists("More Inventory-JSON.json"):
        messagebox.showerror("错误", "请把JSON和工具放一起！")
    else:
        main()