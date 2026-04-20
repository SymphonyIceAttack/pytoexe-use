import os, sys, json, time
import requests
import matplotlib
matplotlib.use('TkAgg')  # Обязательно до импорта pyplot
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(get_app_dir(), "config.json")
DEFAULT_IP = "192.168.1.100"

def load_ip():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get("esp_ip", DEFAULT_IP)
    return DEFAULT_IP

ESP_IP = load_ip()
URL = f"http://{ESP_IP}/api"

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()
x_data, y_flow, y_total = [], [], []

line_flow, = ax1.plot([], [], 'b-o', label='Расход (л/мин)', markersize=4)
line_total, = ax2.plot([], [], 'r--s', label='Всего (л)', markersize=3)

ax1.set_ylim(0, 4)
ax1.set_ylabel('Расход, л/мин', color='b')
ax1.legend(loc='upper left')
ax2.set_ylabel('Объём, л', color='r')
ax2.legend(loc='upper right')
plt.title('💧 Мониторинг расхода воды')
plt.grid(True, alpha=0.3)

def init():
    line_flow.set_data([], [])
    line_total.set_data([], [])
    return line_flow, line_total

def update(frame):
    try:
        resp = requests.get(URL, timeout=2).json()
        now = time.time()
        x_data.append(now)
        y_flow.append(resp['flow'])
        y_total.append(resp['total'])

        if len(x_data) > 120:
            x_data.pop(0); y_flow.pop(0); y_total.pop(0)

        line_flow.set_data(x_data, y_flow)
        line_total.set_data(x_data, y_total)
        ax1.set_xlim(x_data[0], x_data[-1] + 0.5)
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    return line_flow, line_total

ani = FuncAnimation(fig, update, init_func=init, interval=1000, blit=False, cache_frame_data=False)
plt.tight_layout()
plt.show()