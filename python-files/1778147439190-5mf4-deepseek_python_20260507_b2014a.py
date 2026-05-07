"""
蓝牙心率监测器 - 实时接收BLE心率广播并显示在置顶小窗
支持Windows/macOS/Linux
"""

import asyncio
import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# 蓝牙标准心率服务和特征UUID
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"


class HeartRateMonitor:
    """心率监测器主类 - 管理BLE连接和UI显示"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("心率监测器")
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes("-topmost", True)  # 置顶
        self.root.attributes("-alpha", 0.92)  # 轻微透明
        
        # 窗口拖拽相关变量
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # 蓝牙相关变量
        self.client = None
        self.current_heart_rate = 0
        self.is_monitoring = False
        self.device_address = None
        
        self.setup_ui()
        self.setup_drag()
        
    def setup_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = tk.Frame(self.root, bg="#1a1a2e", padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏（用于拖拽和关闭）
        title_frame = tk.Frame(main_frame, bg="#16213e")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame, text="❤️ 心率监测", 
            bg="#16213e", fg="#e94560", 
            font=("微软雅黑", 10, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=8, pady=5)
        
        # 关闭按钮
        close_btn = tk.Button(
            title_frame, text="✕", command=self.quit_app,
            bg="#16213e", fg="#888888", bd=0,
            font=("Arial", 10, "bold"),
            activebackground="#16213e", activeforeground="#e94560"
        )
        close_btn.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 心率显示区域
        hr_frame = tk.Frame(main_frame, bg="#0f3460", relief=tk.RAISED, bd=2)
        hr_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.hr_label = tk.Label(
            hr_frame, text="--", 
            bg="#0f3460", fg="#e94560",
            font=("DS-Digital", 48, "bold")
        )
        self.hr_label.pack(expand=True, pady=20)
        
        hr_unit = tk.Label(
            hr_frame, text="BPM", 
            bg="#0f3460", fg="#ffffff",
            font=("微软雅黑", 14)
        )
        hr_unit.pack(pady=(0, 20))
        
        # 状态和连接区域
        info_frame = tk.Frame(main_frame, bg="#1a1a2e")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(
            info_frame, text="⚡ 扫描中...", 
            bg="#1a1a2e", fg="#ffffff",
            font=("微软雅黑", 9)
        )
        self.status_label.pack()
        
        # 设备下拉框
        device_frame = tk.Frame(main_frame, bg="#1a1a2e")
        device_frame.pack(fill=tk.X, pady=(10, 5))
        
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            device_frame, textvariable=self.device_var,
            state="readonly", font=("微软雅黑", 9),
            width=18
        )
        self.device_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # 刷新按钮
        self.refresh_btn = tk.Button(
            device_frame, text="🔄", command=self.refresh_devices,
            bg="#0f3460", fg="#ffffff", bd=0,
            font=("Arial", 10),
            activebackground="#16213e", activeforeground="#e94560",
            width=3
        )
        self.refresh_btn.pack(side=tk.LEFT)
        
        # 连接/断开按钮
        self.connect_btn = tk.Button(
            main_frame, text="🔗 连接", command=self.toggle_connection,
            bg="#e94560", fg="#ffffff", bd=0,
            font=("微软雅黑", 10, "bold"),
            activebackground="#c73e54", activeforeground="#ffffff",
            cursor="hand2", pady=5
        )
        self.connect_btn.pack(fill=tk.X, pady=(10, 0))
        
        # 设备列表
        self.devices = []
        
        # 启动设备扫描线程
        self.start_scanning()
        
    def setup_drag(self):
        """设置窗口拖拽功能"""
        def on_drag_start(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
        def on_drag_motion(event):
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
            
        # 绑定到标题栏区域
        self.root.bind("<Button-1>", on_drag_start)
        self.root.bind("<B1-Motion>", on_drag_motion)
        
    def start_scanning(self):
        """启动后台扫描线程"""
        self.is_scanning = True
        self.scan_thread = threading.Thread(target=self.run_async_scan, daemon=True)
        self.scan_thread.start()
        
    def run_async_scan(self):
        """在独立线程中运行异步扫描"""
        asyncio.run(self.scan_devices())
        
    async def scan_devices(self):
        """扫描BLE心率设备"""
        self.update_status("🔍 扫描心率设备...")
        
        def detection_callback(device: BLEDevice, adv_data: AdvertisementData):
            if device not in self.devices:
                # 检查设备是否广播心率服务
                if HEART_RATE_SERVICE_UUID.lower() in [uuid.lower() for uuid in adv_data.service_uuids]:
                    self.devices.append(device)
                    self.update_device_list()
                    self.update_status(f"✅ 发现设备: {device.name or device.address[:8]}")
        
        scanner = BleakScanner(detection_callback)
        await scanner.start()
        
        # 扫描15秒
        await asyncio.sleep(15)
        await scanner.stop()
        
        if not self.devices:
            self.update_status("⚠️ 未找到设备，请确保设备已开启心率广播")
        else:
            self.update_status(f"📱 发现 {len(self.devices)} 个设备")
            
        self.is_scanning = False
        
    def update_device_list(self):
        """更新设备下拉列表"""
        device_names = []
        self.device_dict = {}
        
        for device in self.devices:
            name = device.name or f"未知设备-{device.address[-6:]}"
            display_name = f"{name[:20]}"
            device_names.append(display_name)
            self.device_dict[display_name] = device.address
            
        # 在主线程更新UI
        self.root.after(0, lambda: self.device_combo.configure(values=device_names))
        if device_names:
            self.root.after(0, lambda: self.device_combo.set(device_names[0]))
            
    def refresh_devices(self):
        """刷新设备列表"""
        self.devices = []
        self.update_device_list()
        if hasattr(self, 'is_scanning') and not self.is_scanning:
            self.start_scanning()
            
    def toggle_connection(self):
        """切换连接状态"""
        if self.is_monitoring:
            self.disconnect_device()
        else:
            self.connect_device()
            
    def connect_device(self):
        """连接选中的设备"""
        selected = self.device_var.get()
        if not selected or selected not in self.device_dict:
            self.update_status("⚠️ 请先选择设备")
            return
            
        self.device_address = self.device_dict[selected]
        self.connect_btn.config(state="disabled", text="⏳ 连接中...")
        self.update_status(f"🔄 连接设备...")
        
        # 启动连接线程
        self.connect_thread = threading.Thread(target=self.run_async_connect, daemon=True)
        self.connect_thread.start()
        
    def run_async_connect(self):
        """运行异步连接"""
        asyncio.run(self.connect_and_monitor())
        
    async def connect_and_monitor(self):
        """建立BLE连接并开启心率通知"""
        try:
            # 查找设备
            device = await BleakScanner.find_device_by_address(self.device_address, timeout=10.0)
            if not device:
                self.update_status("❌ 未找到设备")
                self.reset_connect_btn()
                return
                
            # 建立连接
            self.client = BleakClient(device)
            await self.client.connect()
            
            if not self.client.is_connected:
                self.update_status("❌ 连接失败")
                self.reset_connect_btn()
                return
                
            self.update_status("✅ 已连接，订阅心率数据...")
            
            # 开启心率通知
            await self.client.start_notify(
                HEART_RATE_MEASUREMENT_CHAR_UUID,
                self.handle_heart_rate
            )
            
            self.is_monitoring = True
            self.update_connect_btn_state(True)
            self.update_status("💓 正在接收心率数据")
            
        except Exception as e:
            self.update_status(f"❌ 连接错误: {str(e)[:30]}")
            self.reset_connect_btn()
            
    def handle_heart_rate(self, sender, data: bytearray):
        """处理接收到的心率数据"""
        try:
            flags = data[0]
            hr_format_is_uint16 = (flags & 0x01)
            
            # 解析心率值
            if hr_format_is_uint16:
                heart_rate = int.from_bytes(data[1:3], byteorder='little')
            else:
                heart_rate = data[1]
                
            self.current_heart_rate = heart_rate
            
            # 更新UI显示
            self.root.after(0, self.update_heart_rate_display, heart_rate)
            
        except Exception as e:
            print(f"解析心率数据错误: {e}")
            
    def update_heart_rate_display(self, heart_rate):
        """更新心率显示"""
        self.hr_label.config(text=str(heart_rate))
        
        # 根据心率范围改变颜色
        if heart_rate < 60:
            color = "#4ECDC4"  # 青色 - 较低
        elif heart_rate < 100:
            color = "#2ECC71"  # 绿色 - 正常
        elif heart_rate < 130:
            color = "#F39C12"  # 橙色 - 偏高
        elif heart_rate < 160:
            color = "#E67E22"  # 橙色 - 高
        else:
            color = "#E94560"  # 红色 - 很高
            
        self.hr_label.config(fg=color)
        
        # 动态心跳效果
        self.animate_heartbeat()
        
    def animate_heartbeat(self):
        """心跳动画效果"""
        current_size = self.hr_label.cget("font")[-1]
        if current_size != 48:
            self.hr_label.config(font=("DS-Digital", 48, "bold"))
            self.root.after(200, lambda: self.hr_label.config(font=("DS-Digital", 48, "bold")))
            
    def disconnect_device(self):
        """断开设备连接"""
        self.update_status("🔌 断开连接...")
        
        async def disconnect():
            if self.client and self.client.is_connected:
                try:
                    await self.client.stop_notify(HEART_RATE_MEASUREMENT_CHAR_UUID)
                    await self.client.disconnect()
                except:
                    pass
            self.is_monitoring = False
            self.reset_connect_btn()
            self.update_status("⚡ 已断开连接")
            self.current_heart_rate = 0
            self.root.after(0, lambda: self.hr_label.config(text="--", fg="#e94560"))
            
        asyncio.run_coroutine_threadsafe(disconnect(), asyncio.new_event_loop())
        
    def reset_connect_btn(self):
        """重置连接按钮状态"""
        self.root.after(0, lambda: self.connect_btn.config(state="normal", text="🔗 连接"))
        
    def update_connect_btn_state(self, is_connected):
        """更新连接按钮状态"""
        self.root.after(0, lambda: self.connect_btn.config(
            text="🔌 断开", 
            bg="#c73e54" if is_connected else "#e94560"
        ))
        
    def update_status(self, message):
        """更新状态栏消息"""
        self.root.after(0, lambda: self.status_label.config(text=message))
        
    def quit_app(self):
        """退出应用程序"""
        self.is_monitoring = False
        
        # 断开蓝牙连接
        if self.client and self.client.is_connected:
            async def cleanup():
                try:
                    await self.client.stop_notify(HEART_RATE_MEASUREMENT_CHAR_UUID)
                    await self.client.disconnect()
                except:
                    pass
            try:
                asyncio.run(cleanup())
            except:
                pass
                
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """启动应用程序主循环"""
        # 设置窗口大小和位置
        self.root.geometry("280x320")
        
        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (280 // 2)
        y = (self.root.winfo_screenheight() // 2) - (320 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.root.mainloop()


def main():
    """程序入口"""
    app = HeartRateMonitor()
    app.run()


if __name__ == "__main__":
    main()