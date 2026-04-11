import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import random
import json
import os
from pynput.keyboard import Key, Controller, Listener

class AutoKeyTool:
    def __init__(self, root):
        self.root = root
        self.root.title("按鍵模擬控制工具 - 專業版")
        self.root.geometry("600x550")
        self.root.resizable(False, False)

        self.running = False
        self.thread = None
        self.keyboard = Controller()
        self.hotkey_listener = None

        # 設定檔儲存路徑
        self.config_dir = "key_configs"
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        # 預設設定
        self.current_config_name = "預設設定"
        self.configs = {
            "預設設定": {
                "left_key": "a",
                "right_key": "d",
                "action_key": "space",
                "min_walk": 0.5,
                "max_walk": 2.5,
                "attack_prob": 0.5,
                "attack_wait": 0.5
            }
        }

        self.setup_ui()
        self.load_config_to_ui("預設設定")
        self.start_hotkey_listener()

    def setup_ui(self):
        # 標題
        title = tk.Label(self.root, text="按鍵模擬控制工具", font=("Arial", 18, "bold"))
        title.pack(pady=10)

        # ===== 設定管理區 =====
        frame_config = tk.LabelFrame(self.root, text="設定管理", padx=10, pady=10)
        frame_config.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_config, text="目前設定:").grid(row=0, column=0, sticky="w")
        self.config_combo = ttk.Combobox(frame_config, values=list(self.configs.keys()), width=15)
        self.config_combo.grid(row=0, column=1, padx=5)
        self.config_combo.bind("<<ComboboxSelected>>", self.on_config_selected)

        tk.Button(frame_config, text="載入", command=self.load_selected_config, width=8).grid(row=0, column=2, padx=2)
        tk.Button(frame_config, text="儲存", command=self.save_current_config, width=8).grid(row=0, column=3, padx=2)
        tk.Button(frame_config, text="另存新檔", command=self.save_as_config, width=10).grid(row=0, column=4, padx=2)
        tk.Button(frame_config, text="刪除", command=self.delete_config, width=8).grid(row=0, column=5, padx=2)

        # ===== 按鍵設定區 =====
        frame_keys = tk.LabelFrame(self.root, text="按鍵設定", padx=10, pady=10)
        frame_keys.pack(fill="x", padx=20, pady=5)

        # 左走
        tk.Label(frame_keys, text="向左走路鍵:").grid(row=0, column=0, sticky="w", pady=5)
        self.left_entry = tk.Entry(frame_keys, width=10)
        self.left_entry.grid(row=0, column=1, padx=5)
        tk.Label(frame_keys, text="(小寫字母)").grid(row=0, column=2, sticky="w")

        # 右走
        tk.Label(frame_keys, text="向右走路鍵:").grid(row=1, column=0, sticky="w", pady=5)
        self.right_entry = tk.Entry(frame_keys, width=10)
        self.right_entry.grid(row=1, column=1, padx=5)
        tk.Label(frame_keys, text="(小寫字母)").grid(row=1, column=2, sticky="w")

        # 攻擊鍵
        tk.Label(frame_keys, text="攻擊按鈕:").grid(row=2, column=0, sticky="w", pady=5)
        self.action_entry = tk.Entry(frame_keys, width=10)
        self.action_entry.grid(row=2, column=1, padx=5)
        tk.Label(frame_keys, text="space / ctrl / shift / 字母").grid(row=2, column=2, sticky="w")

        # ===== 時間與機率設定區 =====
        frame_time = tk.LabelFrame(self.root, text="時間與機率設定", padx=10, pady=10)
        frame_time.pack(fill="x", padx=20, pady=5)

        # 走路間隔
        tk.Label(frame_time, text="走路間隔 (秒):").grid(row=0, column=0, sticky="w", pady=5)
        self.min_walk = tk.DoubleVar(value=0.5)
        self.max_walk = tk.DoubleVar(value=2.5)
        tk.Scale(frame_time, from_=0.2, to=3.0, resolution=0.1, variable=self.min_walk, orient="horizontal", length=150).grid(row=0, column=1, padx=5)
        tk.Label(frame_time, text="~").grid(row=0, column=2)
        tk.Scale(frame_time, from_=0.5, to=5.0, resolution=0.1, variable=self.max_walk, orient="horizontal", length=150).grid(row=0, column=3, padx=5)

        # 攻擊機率與等待
        tk.Label(frame_time, text="攻擊機率 (0~1):").grid(row=1, column=0, sticky="w", pady=5)
        self.attack_prob = tk.DoubleVar(value=0.5)
        tk.Scale(frame_time, from_=0.0, to=1.0, resolution=0.05, variable=self.attack_prob, orient="horizontal", length=200).grid(row=1, column=1, columnspan=2, padx=5)

        tk.Label(frame_time, text="攻擊後等待:").grid(row=1, column=3, sticky="w", pady=5)
        self.attack_wait = tk.DoubleVar(value=0.5)
        tk.Scale(frame_time, from_=0.2, to=2.0, resolution=0.1, variable=self.attack_wait, orient="horizontal", length=150).grid(row=1, column=4, padx=5)

        # ===== 控制區 =====
        frame_control = tk.Frame(self.root)
        frame_control.pack(pady=15)

        self.start_btn = tk.Button(frame_control, text="▶ 開始", command=self.start_auto, bg="lightgreen", width=12, font=("Arial", 10))
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = tk.Button(frame_control, text="⏹ 停止", command=self.stop_auto, bg="lightcoral", width=12, font=("Arial", 10), state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        self.status_label = tk.Label(self.root, text="狀態: 停止", fg="gray", font=("Arial", 10))
        self.status_label.pack(pady=5)

        # ===== 熱鍵提示 =====
        hotkey_frame = tk.Frame(self.root, bg="lightyellow", relief="ridge", bd=1)
        hotkey_frame.pack(fill="x", padx=20, pady=10)
        hotkey_label = tk.Label(hotkey_frame, text="🔥 熱鍵: 按 F6 立即停止", font=("Arial", 10, "bold"), fg="red", bg="lightyellow")
        hotkey_label.pack(pady=5)

        # ===== 說明文字 =====
        info = tk.Label(self.root, text="※ 啟動前請點擊目標視窗（如記事本）\n※ 按 F6 或點擊停止按鈕可中斷", fg="blue", font=("Arial", 9))
        info.pack(pady=5)

    def parse_action_key(self, key_str):
        """將字串轉換成 pynput 按鍵物件"""
        key_str = key_str.lower().strip()
        if key_str == "space":
            return Key.space
        elif key_str == "ctrl":
            return Key.ctrl_l
        elif key_str == "shift":
            return Key.shift_l
        elif key_str == "enter":
            return Key.enter
        elif len(key_str) == 1 and key_str.isalpha():
            return key_str
        else:
            raise ValueError(f"不支援的按鍵: {key_str}")

    def press_key(self, key):
        """按下並放開一個按鍵"""
        self.keyboard.press(key)
        time.sleep(0.05)
        self.keyboard.release(key)

    def auto_loop(self):
        while self.running:
            try:
                left = self.left_entry.get().strip().lower()
                right = self.right_entry.get().strip().lower()
                action_str = self.action_entry.get().strip().lower()

                min_wait = self.min_walk.get()
                max_wait = self.max_walk.get()
                prob = self.attack_prob.get()
                attack_delay = self.attack_wait.get()

                direction = random.choice(['left', 'right'])
                key_to_press = left if direction == 'left' else right
                self.press_key(key_to_press)

                time.sleep(random.uniform(min_wait, max_wait))

                if random.random() < prob:
                    action_key = self.parse_action_key(action_str)
                    self.press_key(action_key)
                    time.sleep(attack_delay)

            except Exception as e:
                print("錯誤:", e)
                self.stop_auto()
                break

    def start_auto(self):
        if self.running:
            return
        try:
            self.parse_action_key(self.action_entry.get().strip().lower())
        except Exception as e:
            messagebox.showerror("錯誤", f"攻擊鍵設定無效:\n{e}")
            return

        self.running = True
        self.thread = threading.Thread(target=self.auto_loop, daemon=True)
        self.thread.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="狀態: 執行中 (按 F6 停止)", fg="green")

    def stop_auto(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="狀態: 停止", fg="gray")

    def start_hotkey_listener(self):
        """啟動熱鍵監聽 (F6 停止)"""
        def on_press(key):
            try:
                if key == Key.f6:
                    print("偵測到 F6，停止動作")
                    self.stop_auto()
            except Exception:
                pass

        self.hotkey_listener = Listener(on_press=on_press, daemon=True)
        self.hotkey_listener.start()

    # ===== 設定管理功能 =====
    def on_config_selected(self, event):
        """選擇設定檔時自動載入"""
        self.load_config_to_ui(self.config_combo.get())

    def load_config_to_ui(self, config_name):
        """將設定載入到 UI"""
        if config_name not in self.configs:
            return
        cfg = self.configs[config_name]
        self.left_entry.delete(0, tk.END)
        self.left_entry.insert(0, cfg["left_key"])
        self.right_entry.delete(0, tk.END)
        self.right_entry.insert(0, cfg["right_key"])
        self.action_entry.delete(0, tk.END)
        self.action_entry.insert(0, cfg["action_key"])
        self.min_walk.set(cfg["min_walk"])
        self.max_walk.set(cfg["max_walk"])
        self.attack_prob.set(cfg["attack_prob"])
        self.attack_wait.set(cfg["attack_wait"])
        self.current_config_name = config_name

    def save_current_config(self):
        """儲存到當前設定檔"""
        cfg = self.get_current_config()
        self.configs[self.current_config_name] = cfg
        self.save_configs_to_file()
        self.update_config_list()
        messagebox.showinfo("成功", f"已儲存設定: {self.current_config_name}")

    def save_as_config(self):
        """另存新檔"""
        name = tk.simpledialog.askstring("另存新檔", "請輸入設定名稱:")
        if name and name.strip():
            name = name.strip()
            cfg = self.get_current_config()
            self.configs[name] = cfg
            self.current_config_name = name
            self.save_configs_to_file()
            self.update_config_list()
            messagebox.showinfo("成功", f"已儲存為: {name}")

    def delete_config(self):
        """刪除目前設定檔（不能刪除預設設定）"""
        if self.current_config_name == "預設設定":
            messagebox.showwarning("警告", "不能刪除預設設定")
            return
        if messagebox.askyesno("確認", f"確定要刪除設定「{self.current_config_name}」嗎？"):
            del self.configs[self.current_config_name]
            self.current_config_name = "預設設定"
            self.save_configs_to_file()
            self.update_config_list()
            self.load_config_to_ui("預設設定")
            messagebox.showinfo("成功", "已刪除")

    def load_selected_config(self):
        """載入選擇的設定"""
        name = self.config_combo.get()
        if name in self.configs:
            self.load_config_to_ui(name)
            messagebox.showinfo("成功", f"已載入設定: {name}")

    def get_current_config(self):
        """從 UI 取得目前設定"""
        return {
            "left_key": self.left_entry.get().strip().lower(),
            "right_key": self.right_entry.get().strip().lower(),
            "action_key": self.action_entry.get().strip().lower(),
            "min_walk": self.min_walk.get(),
            "max_walk": self.max_walk.get(),
            "attack_prob": self.attack_prob.get(),
            "attack_wait": self.attack_wait.get()
        }

    def update_config_list(self):
        """更新下拉選單"""
        self.config_combo['values'] = list(self.configs.keys())
        self.config_combo.set(self.current_config_name)

    def save_configs_to_file(self):
        """儲存所有設定到 JSON 檔案"""
        config_file = os.path.join(self.config_dir, "key_configs.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.configs, f, indent=4, ensure_ascii=False)

    def load_configs_from_file(self):
        """從 JSON 檔案載入設定"""
        config_file = os.path.join(self.config_dir, "key_configs.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if "預設設定" not in loaded:
                        loaded["預設設定"] = self.configs["預設設定"]
                    self.configs = loaded
            except Exception as e:
                print("載入設定失敗:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoKeyTool(root)
    app.load_configs_from_file()
    app.update_config_list()
    root.mainloop()