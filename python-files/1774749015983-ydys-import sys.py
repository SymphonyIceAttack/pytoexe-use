import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox
from flask import Flask, request, send_from_directory, render_template_string
import shutil
import webbrowser
from datetime import datetime
import re

# ===================== 配置 =====================
SHARE_FOLDER = "shared_files"
HOST = "192.168.2.3"
PORT = 8080
os.makedirs(SHARE_FOLDER, exist_ok=True)

app = Flask(__name__)
connected_devices = {}

# ===================== 穿透配置 =====================
CUSTOM_DOMAIN = ""  # 你本机内网穿透的域名/地址


# ===================== 你原来的设备识别（完全没动） =====================
def parse_device(ua):
    ua = ua.lower()
    model = "未知设备"

    if "iphone" in ua:
        model = "iPhone"
    elif "mi" in ua or "xiaomi" in ua:
        match = re.search(r"mi\s+[\d+a-z]+|redmi\s+[\d+a-z]+", ua)
        if match:
            model = match.group(0).strip().title()
        else:
            model = "小米手机"
    elif "huawei" in ua or "honor" in ua:
        match = re.search(r"huawei\s+[\w-]+|honor\s+[\w-]+|nova\s+[\w-]+|mate\s+[\w-]+|p\s+[\w-]+", ua)
        if match:
            model = match.group(0).strip().title()
        else:
            model = "华为/荣耀手机"
    elif "oppo" in ua or "realme" in ua:
        match = re.search(r"oppo\s+[\w-]+|realme\s+[\w-]+", ua)
        if match:
            model = match.group(0).strip().title()
        else:
            model = "OPPO/Realme手机"
    elif "vivo" in ua or "iqoo" in ua:
        match = re.search(r"vivo\s+[\w-]+|iqoo\s+[\w-]+", ua)
        if match:
            model = match.group(0).strip().upper()
        else:
            model = "vivo/iQOO手机"
    elif "samsung" in ua:
        model = "三星手机"
    elif "windows" in ua:
        model = "Windows 电脑"
    elif "mac os" in ua:
        model = "Mac 电脑"
    elif "linux" in ua:
        model = "Linux 电脑"
    elif "android" in ua:
        model = "安卓手机"
    return model


# ===================== 网页端（完全没动） =====================
@app.route('/')
def index():
    client_ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    device_model = parse_device(ua)

    connected_devices[client_ip] = {
        "model": device_model,
        "ua": ua,
        "time": datetime.now().strftime("%H:%M:%S")
    }

    files = os.listdir(SHARE_FOLDER)
    return render_template_string('''
<!DOCTYPE html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>局域网文件传输</title>
<style>
    *{box-sizing:border-box}
    body{background:#f5f7fa;font-family:Arial;padding:20px;margin:0}
    .box{max-width:500px;margin:auto;background:white;padding:22px;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.08)}
    h2{text-align:center;color:#222;margin-top:0}
    .upload-area{background:#007AFF;color:white;padding:16px;border-radius:12px;margin:16px 0;text-align:center}
    input,button{width:100%;padding:12px;margin:6px 0;border-radius:10px;border:none;font-size:15px}
    button{background:#007AFF;color:white;font-weight:bold}
    .file-item{background:#f1f3f5;padding:16px;margin:10px 0;border-radius:12px}
    a{color:#007AFF;text-decoration:none;font-size:15px}
    #preview{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);
            display:none;justify-content:center;align-items:center}
    .close{position:absolute;top:24px;right:24px;background:#ff3b30;color:white;padding:10px 16px;border-radius:8px}
    .dl-btn{background:#007AFF;color:white;padding:10px 16px;border-radius:8px;margin-top:16px}
    img,video{max-width:90%;max-height:80vh;border-radius:8px}
</style>

<div class="box">
    <h2>📂 局域网文件传输</h2>
    <div class="upload-area">
        <form method="post" enctype="multipart/form-data" action="/upload">
            <input type="file" name="file" required>
            <button type="submit">⬆️ 上传文件</button>
        </form>
    </div>

    <h3 style="margin-bottom:10px">📥 文件列表</h3>
    {% for f in files %}
        <div class="file-item">
            {% set ext = f.lower().split('.')[-1] %}
            {% if ext in ['jpg','jpeg','png','gif','bmp','webp'] %}
                <a href="javascript:viewImg('/dl/{{f}}')">{{f}}</a>
            {% elif ext in ['mp4','mov','avi','mkv','flv','webm'] %}
                <a href="javascript:viewVideo('/dl/{{f}}')">{{f}}</a>
            {% else %}
                <a href="/dl/{{f}}" download>{{f}}</a>
            {% endif %}
        </div>
    {% else %}
        <p style="text-align:center;color:#999">暂无文件</p>
    {% endfor %}
</div>

<div id="preview">
    <div style="text-align:center">
        <img id="prevImg" style="display:none">
        <video id="prevVideo" controls style="display:none"></video>
        <br>
        <button class="dl-btn" onclick="startDownload()">下载文件</button>
        <button class="close" onclick="closeView()">关闭预览</button>
    </div>
</div>

<script>
    let currentFile = ""
    function viewImg(url){
        currentFile = url
        document.getElementById("prevImg").src = url
        document.getElementById("prevImg").style.display = "block"
        document.getElementById("prevVideo").style.display = "none"
        document.getElementById("preview").style.display = "flex"
    }
    function viewVideo(url){
        currentFile = url
        document.getElementById("prevVideo").src = url
        document.getElementById("prevVideo").style.display = "block"
        document.getElementById("prevImg").style.display = "none"
        document.getElementById("preview").style.display = "flex"
    }
    function closeView(){
        document.getElementById("preview").style.display = "none"
    }
    function startDownload(){
        let a = document.createElement("a")
        a.href = currentFile
        a.download = ""
        a.click()
    }
</script>
''', files=files)

# 上传（完全没动）
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file:
        save_path = os.path.join(SHARE_FOLDER, file.filename)
        file.save(save_path)
    return '<script>alert("上传成功");location.href="/"</script>'

# 下载（完全没动）
@app.route('/dl/<filename>')
def download_file(filename):
    return send_from_directory(os.path.abspath(SHARE_FOLDER), filename, as_attachment=True)

# 启动服务（完全没动）
def run_server():
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


# ===================== UI界面：完整集合你所有需求 =====================
class FileServerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("局域网文件传输 · 完整版")
        self.root.geometry("480x650")
        self.root.resizable(False, False)

        tk.Label(root, text="✅ 服务已启动", font=("Arial", 16, "bold")).pack(pady=10)
        self.url = f"http://{HOST}:{PORT}"
        tk.Label(root, text=self.url, fg="red", font=("Arial", 14, "bold")).pack(pady=5)

        # ========== 适配你这种纯IP穿透地址，预填你的IP ==========
        tk.Label(root, text="本机内网穿透地址（纯IP）", font=("Arial", 11)).pack(pady=3)
        self.tunnel_entry = ttk.Entry(root, width=40, font=("Arial", 11))
        self.tunnel_entry.pack(pady=2)
        self.tunnel_entry.insert(0, "26.103.244.158")  # 预填你这个穿透IP
        self.tunnel_btn = ttk.Button(root, text="应用穿透地址", command=self.apply_tunnel)
        self.tunnel_btn.pack(pady=3)

        self.tunnel_show = tk.Label(root, text="未设置穿透", fg="gray", font=("Arial", 11))
        self.tunnel_show.pack(pady=2)
        # ======================================================

        # 功能按钮（原样）
        ttk.Button(root, text="📤 电脑本地上传", command=self.upload_local).pack(pady=4, fill=tk.X, padx=20)
        ttk.Button(root, text="📂 打开共享文件夹", command=self.open_folder).pack(pady=4, fill=tk.X, padx=20)

        # 设备列表（原样）
        tk.Label(root, text="📡 已连接设备（双击查询详情）", font=("Arial", 12, "bold")).pack(pady=8)
        self.device_box = Listbox(root, width=55, height=9, font=("Consolas", 11))
        self.device_box.pack(padx=20, pady=4, fill=tk.BOTH, expand=True)
        self.device_box.bind("<Double-Button-1>", self.search_device)

        ttk.Button(root, text="🔄 刷新设备列表", command=self.refresh_devices).pack(pady=6)
        tk.Label(root, text="关闭窗口即停止服务", fg="#666").pack(pady=4)

        self.refresh_devices()

    def apply_tunnel(self):
        global CUSTOM_DOMAIN
        domain = self.tunnel_entry.get().strip()
        if domain:
            CUSTOM_DOMAIN = f"http://{domain}"  # 自动补http://
            self.tunnel_show.config(text=f"已启用：{CUSTOM_DOMAIN}", fg="green")
            messagebox.showinfo("成功", f"内网穿透地址已应用！\n外部访问请使用：{CUSTOM_DOMAIN}")
        else:
            CUSTOM_DOMAIN = ""
            self.tunnel_show.config(text="已清除穿透", fg="gray")

    def upload_local(self):
        path = filedialog.askopenfilename()
        if path:
            name = os.path.basename(path)
            shutil.copy(path, os.path.join(SHARE_FOLDER, name))
            messagebox.showinfo("成功", f"已共享：{name}")

    def open_folder(self):
        os.startfile(SHARE_FOLDER)

    def refresh_devices(self):
        self.device_box.delete(0, tk.END)
        for ip, info in connected_devices.items():
            line = f"{ip:15s} | {info['time']} | {info['model']}"
            self.device_box.insert(tk.END, line)

    def search_device(self, event):
        try:
            idx = self.device_box.curselection()[0]
            line = self.device_box.get(idx)
            model = line.split("|")[-1].strip()
            keyword = f"{model} 价格 性价比 参数 评测"
            webbrowser.open(f"https://www.bing.com/search?q={keyword}")
        except Exception:
            messagebox.showwarning("提示", "无法获取设备信息")


# ===================== 启动 =====================
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    root = tk.Tk()
    FileServerUI(root)
    root.mainloop()