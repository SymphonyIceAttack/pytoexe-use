import sys
import time
import json
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu,
                             QAction, QVBoxLayout, QDialog, QFormLayout,
                             QLineEdit, QPushButton, QSystemTrayIcon, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QIcon
import os

# ========== 配置 ==========
CONFIG_PATH = "weather_config.json"
API_URL = "http://coapi.moji.com/whapi/v2/weather"

# 常用城市 ID（无需手动查）
COMMON_CITIES = {
    "北京": "2",
    "上海": "4",
    "广州": "8",
    "深圳": "9",
    "杭州": "45",
    "成都": "46",
    "南京": "42",
    "武汉": "38",
    "西安": "11",
    "重庆": "48",
    "天津": "3",
    "苏州": "29",
    "青岛": "12",
    "大连": "15",
    "厦门": "37",
    "长沙": "40",
    "郑州": "14",
    "沈阳": "5",
    "哈尔滨": "6",
    "昆明": "56",
    "福州": "39",
    "济南": "17",
    "合肥": "41",
    "南昌": "43",
    "南宁": "34",
    "贵阳": "57",
    "太原": "26",
    "兰州": "20",
    "乌鲁木齐": "25",
    "拉萨": "61",
    "呼和浩特": "21",
    "银川": "22",
    "西宁": "62",
    "石家庄": "19",
    "海口": "36",
    "三亚": "32",
    "香港": "31",
    "澳门": "33",
}

LANG_OPTIONS = {
    "简体中文": "zh-CN",
    "繁体中文": "zh-TW",
    "英文": "en-US",
    "日文": "ja-JP",
    "韩文": "ko-KR",
}

# ========== 配置管理 ==========
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            cfg.pop("token", None)
            cfg.pop("password", None)
            return cfg
    except FileNotFoundError:
        return {"cityName": "", "cityId": "", "lang": "zh-CN", "autoStart": False}

def save_config(cfg):
    clean = {
        "cityName": cfg.get("cityName", "").strip(),
        "cityId": cfg.get("cityId", "").strip(),
        "lang": cfg.get("lang", "zh-CN").strip() or "zh-CN",
        "autoStart": bool(cfg.get("autoStart", False))
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)

def get_city_id_by_name(name):
    """通过城市名快速获取 cityId"""
    name = name.strip()
    if name in COMMON_CITIES:
        return COMMON_CITIES[name]
    # 尝试模糊匹配
    for key, cid in COMMON_CITIES.items():
        if name in key or key in name:
            return cid
    return ""

# ========== 天气获取 ==========
def get_weather(cfg):
    """获取天气数据，返回 (data, msg)"""
    ts = int(time.time() * 1000)
    cid = cfg.get("cityId", "").strip()
    lang = cfg.get("lang", "zh-CN").strip()
    
    if not cid:
        return None, "请右键打开配置，选择或输入城市"
    
    params = {
        "timestamp": ts,
        "cityId": cid,
        "language": lang
    }
    
    try:
        resp = requests.get(API_URL, params=params, timeout=12)
        resp.raise_for_status()
        res = resp.json()
        code = res.get("code", -1)
        if code != 0:
            msg = res.get("msg", "服务异常")
            return None, f"接口错误(code={code}): {msg}"
        return res.get("data"), "ok"
    except requests.exceptions.Timeout:
        return None, "请求超时，请检查网络"
    except requests.exceptions.ConnectionError:
        return None, "网络连接失败，请检查网络"
    except Exception as e:
        return None, f"请求异常: {str(e)}"

# ========== 配置对话框 ==========
class ConfigDialog(QDialog):
    def __init__(self, parent, cfg):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 天气配置")
        self.resize(480, 320)
        self.cfg = cfg
        self.parent_ref = parent
        
        layout = QFormLayout()
        layout.setSpacing(12)
        
        # 城市选择
        self.combo_city = QComboBox()
        self.combo_city.addItem("— 选择城市 —", "")
        for name in sorted(COMMON_CITIES.keys()):
            self.combo_city.addItem(name, COMMON_CITIES[name])
        self.combo_city.currentIndexChanged.connect(self.on_city_selected)
        layout.addRow("快捷选择城市：", self.combo_city)
        
        # 自定义城市名
        self.edit_city_name = QLineEdit(cfg.get("cityName", ""))
        layout.addRow("显示城市名称：", self.edit_city_name)
        
        # CityId
        self.edit_city_id = QLineEdit(cfg.get("cityId", ""))
        self.edit_city_id.setPlaceholderText("输入城市ID，如 2=北京")
        layout.addRow("城市CityId：", self.edit_city_id)
        
        # 语言选择
        self.combo_lang = QComboBox()
        for label, code in LANG_OPTIONS.items():
            self.combo_lang.addItem(label, code)
        self.combo_lang.setCurrentText("简体中文")
        layout.addRow("语言：", self.combo_lang)
        
        # 自动刷新
        self.edit_interval = QLineEdit("5")
        self.edit_interval.setPlaceholderText("分钟，最小1")
        layout.addRow("刷新间隔(分钟)：", self.edit_interval)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow("", btn_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                background: #2c3e50;
                color: #ecf0f1;
                border-radius: 12px;
            }
            QLabel { color: #ecf0f1; font-size: 13px; }
            QLineEdit, QComboBox {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #46627f;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover { background: #2980b9; }
        """)
    
    def on_city_selected(self, index):
        cid = self.combo_city.itemData(index)
        if cid:
            self.edit_city_id.setText(cid)
            name = self.combo_city.itemText(index)
            if not self.edit_city_name.text():
                self.edit_city_name.setText(name)
    
    def save(self):
        city_name = self.edit_city_name.text().strip()
        city_id = self.edit_city_id.text().strip()
        
        # 如果选择了快捷城市但手动改了ID，以手动为准
        # 自动补全城市名
        if not city_name and city_id:
            for name, cid in COMMON_CITIES.items():
                if cid == city_id:
                    city_name = name
                    break
        
        self.cfg["cityName"] = city_name
        self.cfg["cityId"] = city_id
        self.cfg["lang"] = self.combo_lang.currentData()
        
        try:
            interval = int(self.edit_interval.text())
            interval = max(1, min(120, interval))
        except:
            interval = 5
        self.cfg["interval"] = interval
        
        save_config(self.cfg)
        
        # 更新父窗口的刷新间隔
        if self.parent_ref and hasattr(self.parent_ref, "timer"):
            self.parent_ref.timer.setInterval(interval * 60 * 1000)
        
        self.accept()

# ========== 主窗口 ==========
class FloatWeather(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.top_flag = True
        self.drag_point = QPoint()
        self.status = "loading"  # loading, ok, error
        
        self.init_window()
        self.init_ui()
        self.init_timer()
        self.refresh()
    
    def init_window(self):
        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(330, 220)
        # 默认放在右下角附近
        self.move(self.get_default_pos())
    
    def get_default_pos(self):
        try:
            desktop = QApplication.desktop()
            w = desktop.screenGeometry().width()
            h = desktop.screenGeometry().height()
            return QPoint(w - 370, 100)
        except:
            return QPoint(1120, 90)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(8)
        
        font_big = QFont("Microsoft YaHei", 18, QFont.Bold)
        font_mid = QFont("Microsoft YaHei", 10)
        font_small = QFont("Microsoft YaHei", 9)
        font_tiny = QFont("Microsoft YaHei", 8)
        
        self.lb_city = QLabel("等待配置...")
        self.lb_city.setFont(font_big)
        self.lb_city.setStyleSheet("color:#ffffff;")
        
        self.lb_weather = QLabel("")
        self.lb_weather.setFont(font_mid)
        self.lb_weather.setStyleSheet("color:#e8e8e8;")
        
        self.lb_detail = QLabel("")
        self.lb_detail.setFont(font_small)
        self.lb_detail.setStyleSheet("color:#cccccc;")
        self.lb_detail.setWordWrap(True)
        
        self.lb_tip = QLabel("右键窗口 → 打开配置")
        self.lb_tip.setFont(font_tiny)
        self.lb_tip.setStyleSheet("color:#aaaaaa;")
        
        layout.addWidget(self.lb_city)
        layout.addWidget(self.lb_weather)
        layout.addWidget(self.lb_detail)
        layout.addStretch(1)
        layout.addWidget(self.lb_tip)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background: rgba(30, 40, 60, 0.85);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.1);
            }
        """)
    
    def init_timer(self):
        interval = self.cfg.get("interval", 5)
        self.timer = QTimer()
        self.timer.setInterval(max(1, interval) * 60 * 1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
    
    def refresh(self):
        data, msg = get_weather(self.cfg)
        if data is None:
            self.status = "error"
            self.lb_city.setText("⚠️ 获取失败")
            self.lb_weather.setText("")
            self.lb_detail.setText(msg or "请检查配置")
            self.lb_tip.setText("右键 → 城市配置")
            return
        
        self.status = "ok"
        city = data.get("city", {})
        curr = data.get("current", {})
        
        city_name = self.cfg.get("cityName") or city.get("name", "未知")
        temp = curr.get("temp", "--")
        weather = curr.get("weather", "--")
        feel = curr.get("real_feel", "--")
        hum = curr.get("humidity", "--")
        wind_dir = curr.get("wind_dir", "")
        wind_level = curr.get("wind_level", "--")
        uvi = curr.get("uvi", "--")
        rain1h = curr.get("precip_1h", "0")
        tip = curr.get("tips", "")
        
        self.lb_city.setText(f"{city_name}  {temp}°C")
        self.lb_weather.setText(f"{weather}")
        
        wind_str = f"{wind_dir}{wind_level}级" if wind_dir else f"{wind_level}级"
        detail = f"体感 {feel}°C | 湿度 {hum}%\n{wind_str} | 紫外线 {uvi} | 降水 {rain1h}mm"
        self.lb_detail.setText(detail)
        
        if tip:
            self.lb_tip.setText(f"💡 {tip}")
        else:
            self.lb_tip.setText("双击刷新 · 右键菜单")
    
    # ===== 拖动 =====
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_point = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()
    
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self.drag_point)
            e.accept()
    
    def mouseDoubleClickEvent(self, e):
        self.refresh()
    
    # ===== 右键菜单 =====
    def contextMenuEvent(self, e):
        menu = QMenu()
        act_ref = QAction("🔄 立即刷新")
        act_set = QAction("⚙️ 城市配置")
        act_top = QAction("🚫 取消置顶" if self.top_flag else "📌 开启置顶")
        act_about = QAction("ℹ️ 关于")
        act_exit = QAction("🚪 退出")
        
        act_ref.triggered.connect(self.refresh)
        act_set.triggered.connect(self.open_set)
        act_top.triggered.connect(self.switch_top)
        act_about.triggered.connect(self.show_about)
        act_exit.triggered.connect(self.quit_app)
        
        menu.addAction(act_ref)
        menu.addAction(act_set)
        menu.addAction(act_top)
        menu.addSeparator()
        menu.addAction(act_about)
        menu.addSeparator()
        menu.addAction(act_exit)
        
        menu.setStyleSheet("""
            QMenu {
                background: rgba(30, 40, 60, 0.95);
                color: #ecf0f1;
                border-radius: 8px;
                padding: 6px;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(52, 152, 219, 0.8);
            }
        """)
        menu.exec_(e.globalPos())
    
    def open_set(self):
        dlg = ConfigDialog(self, self.cfg)
        if dlg.exec():
            self.cfg = load_config()
            self.refresh()
    
    def switch_top(self):
        self.top_flag = not self.top_flag
        flag = Qt.FramelessWindowHint | Qt.Tool
        if self.top_flag:
            flag |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flag)
        self.show()
    
    def show_about(self):
        QMessageBox.information(self, "关于", 
            "🌤️ 悬浮天气桌面应用\n\n"
            "• 双击窗口：立即刷新\n"
            "• 拖动窗口：移动位置\n"
            "• 右键窗口：打开菜单\n\n"
            "数据来源：墨迹天气开放接口")
    
    def quit_app(self):
        self.timer.stop()
        QApplication.quit()

# ========== 启动入口 ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 防止误关
    
    win = FloatWeather()
    win.show()
    
    # 检查配置，如果没有城市则提示
    if not win.cfg.get("cityId"):
        QMessageBox.information(win, "首次使用", 
            "欢迎使用悬浮天气应用！\n\n请右键点击窗口，选择「城市配置」来设置您的城市。")
    
    sys.exit(app.exec_())
