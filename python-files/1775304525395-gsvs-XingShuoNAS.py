import os
import json
import threading
import sys
import shutil
import uuid
from tkinter import Tk, ttk, messagebox
from flask import Flask, render_template_string, request, send_file, redirect, session, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
from flask_cors import CORS

try:
    from pystray import Icon, Menu, MenuItem
except ImportError:
    Icon = None

# ==================== 基础配置 ====================
CONFIG_FILE = "nas_config.json"
DEFAULT_CONFIG = {
    "site_name": "星硕NAS",
    "share_path": r"D:\NAS_Share",
    "port": 8683,
    "users": {
        "admin": "123456",
        "user": "Wa1.8"
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

config = load_config()
os.makedirs(config["share_path"], exist_ok=True)

# 自动创建临时目录，不报错
TEMP_CHUNK_DIR = r"D:\NAS_Temp_Chunks"
os.makedirs(TEMP_CHUNK_DIR, exist_ok=True)

flask_app = Flask(__name__)
flask_app.secret_key = "cloud_disk_2026_secure"
CORS(flask_app)

# ==================== 工具函数：文件大小格式化 ====================
def fmt_size(byte_num):
    if byte_num < 1024:
        return f"{byte_num} B"
    elif byte_num < 1048576:
        return f"{byte_num/1024:.2f} KB"
    elif byte_num < 1073741824:
        return f"{byte_num/1048576:.2f} MB"
    else:
        return f"{byte_num/1073741824:.2f} GB"

def get_file_info(full_path, is_dir):
    if is_dir:
        return ""
    try:
        size = os.path.getsize(full_path)
        return fmt_size(size)
    except:
        return "未知大小"

def get_type(n):
    e = n.lower().split(".")[-1] if "." in n else ""
    img = ["jpg","jpeg","png","gif","webp","bmp"]
    txt = ["txt","md","py","json","html","css","log"]
    vid = ["mp4","mov","webm"]
    if e in img: return "image"
    if e in txt: return "text"
    if e in vid: return "video"
    if e == "pdf": return "pdf"
    return "other"

def safe_p(rel):
    if not rel: rel = ""
    full = os.path.abspath(os.path.join(config["share_path"], rel.replace("/", os.sep)))
    base = os.path.abspath(config["share_path"])
    if not full.startswith(base):
        return None
    return full

# 切片合并
def merge_chunks(file_id, filename, target_dir):
    temp_dir = os.path.join(TEMP_CHUNK_DIR, file_id)
    final = os.path.join(target_dir, secure_filename(filename))
    try:
        chunks = sorted(os.listdir(temp_dir), key=lambda x: int(x.split("_")[-1]))
        with open(final, "wb") as f_out:
            for c in chunks:
                p = os.path.join(temp_dir, c)
                with open(p, "rb") as f_in:
                    f_out.write(f_in.read())
                os.remove(p)
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass

# ==================== 前端HTML模板 ====================
login_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{site_name}} - 登录</title>
<style>
* {margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft Yahei",system-ui;}
body {background:linear-gradient(135deg,#6366f1,#8b5cf6);min-height:100vh;display:flex;align-items:center;justify-content:center;}
.login-card {background:#fff;border-radius:20px;padding:40px 30px;width:90%;max-width:420px;box-shadow:0 10px 40px rgba(0,0,0,0.15);}
.title {font-size:28px;color:#6366f1;text-align:center;margin-bottom:30px;font-weight:bold;}
.input-item {margin-bottom:20px;}
.input-item input {width:100%;padding:14px 18px;border:1px solid #e5e7eb;border-radius:12px;font-size:16px;transition:0.3s;}
.input-item input:focus {outline:none;border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,0.2);}
.login-btn {width:100%;padding:14px;background:#6366f1;color:#fff;border:none;border-radius:12px;font-size:17px;cursor:pointer;transition:0.3s;}
.login-btn:hover {background:#4f46e5;}
.error-tip {color:#ef4444;text-align:center;margin:10px 0;height:20px;}
</style>
</head>
<body>
<div class="login-card">
    <div class="title">{{site_name}}</div>
    <form method="post">
        <div class="input-item">
            <input name="user" placeholder="请输入用户名" required>
        </div>
        <div class="input-item">
            <input name="passwd" type="password" placeholder="请输入密码" required>
        </div>
        <div class="error-tip">{{error}}</div>
        <button class="login-btn">立即登录</button>
    </form>
</div>
</body>
</html>
"""

main_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{site_name}}</title>
<style>
* {margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft Yahei",system-ui;}
body {background:#f3f4f6;color:#1f2937;}
.header {background:#6366f1;color:#fff;padding:16px 24px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
.header h2 {font-size:20px;}
.header-user {display:flex;gap:20px;align-items:center;}
.header-user a {color:#fff;text-decoration:none;opacity:0.9;transition:0.2s;}
.header-user a:hover{opacity:1;}
.container{max-width:1200px;margin:20px auto;padding:0 20px;}
.card{background:#fff;border-radius:16px;padding:20px;margin-bottom:20px;box-shadow:0 4px 15px rgba(0,0,0,0.05);}
.btn{display:inline-block;padding:9px 18px;border-radius:10px;text-decoration:none;font-size:14px;border:none;cursor:pointer;transition:0.3s;}
.btn-primary{background:#6366f1;color:#fff;}
.btn-primary:hover{background:#4f46e5;}
.btn-danger{background:#ef4444;color:#fff;}
.btn-danger:hover:not(:disabled){background:#dc2626;}
.btn-danger:disabled{background:#cccccc;cursor:not-allowed;opacity:0.7;}
.btn-green{background:#10b981;color:#fff;}
.file-list{margin-top:10px;}
.file-item{display:flex;justify-content:space-between;align-items:center;padding:14px 10px;border-bottom:1px solid #f3f4f6;border-radius:8px;transition:0.2s;}
.file-item:hover{background:#f9fafb;}
.file-name{font-size:15px;display:flex;align-items:center;gap:8px;}
.file-size{color:#888;font-size:13px;margin-left:12px;}
.file-ops{display:flex;gap:8px;flex-wrap:wrap;}
.form-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px;}
.form-row input{padding:10px;border:1px solid #e5e7eb;border-radius:10px;font-size:14px;flex:1;min-width:180px;}
.del-modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:none;align-items:center;justify-content:center;z-index:999;}
.del-box{background:#fff;padding:25px;border-radius:16px;width:320px;text-align:center;}
.del-box p{margin-bottom:20px;font-size:15px;}
.del-btns{display:flex;gap:12px;justify-content:center;}
</style>
</head>
<body>
<div class="header">
    <h2>{{site_name}}</h2>
    <div class="header-user">
        <span>欢迎：{{user}}</span>
        <a href="/logout">退出登录</a>
    </div>
</div>
<div class="container">
    <div class="card">
        <a href="/" class="btn btn-primary">返回根目录</a>
        {% if is_admin %}<a href="/admin" class="btn btn-primary">👤 用户管理</a>{% endif %}
    </div>
    <div class="card">
        <h3 style="margin-bottom:12px;font-size:16px;">📁 新建文件夹</h3>
        <form class="form-row" method="post" action="/mkdir">
            <input name="name" placeholder="输入文件夹名称" required>
            <input type="hidden" name="cur" value="{{current_path}}">
            <button class="btn btn-primary">创建</button>
        </form>
    </div>
    <div class="card">
        <h3 style="margin-bottom:12px;font-size:16px;">上传(大文件会卡)</h3>
        <form class="form-row" method="post" action="/upload" enctype="multipart/form-data">
            <input type="file" name="upfile" required>
            <input type="hidden" name="cur" value="{{current_path}}">
            <button class="btn btn-primary">确认上传</button>
        </form>
    </div>
    <div class="card file-list">
        {% if current_path != "" %}
        <div class="file-item">
            <div class="file-name"><a href="/?path={{parent_path}}" style="color:#6366f1;text-decoration:none;">⬅ 返回上一级</a></div>
            <div></div>
        </div>
        {% endif %}
        {% for name,isdir,size_text in items %}
        <div class="file-item">
            <div class="file-name">
                {% if isdir %}
                    {% set newp = current_path + '/' + name if current_path else name %}
                    <a href="/?path={{newp}}" style="color:#1f2937;text-decoration:none;">📂 {{name}}</a>
                {% else %}
                    {% set fp = current_path + '/' + name if current_path else name %}
                    📄 {{name}} <span class="file-size">{{size_text}}</span>
                {% endif %}
            </div>
            <div class="file-ops">
                {% if not isdir %}
                    <a href="/preview?path={{fp}}" class="btn btn-primary">预览</a>
                    <a href="/download?path={{fp}}" class="btn btn-primary">下载</a>
                {% endif %}
                <button class="btn btn-danger" onclick="openDelPop('{{fp if not isdir else newp}}','{{name}}')">🗑️ 删除</button>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
<div class="del-modal" id="delModal">
    <div class="del-box">
        <p>确定要删除 <span id="delFileName"></span> 吗？会消失的！</p>
        <div class="del-btns">
            <button class="btn" onclick="closeDelPop()">取消</button>
            <form id="delForm" action="/del" method="post" style="margin:0;display:inline;">
                <input type="hidden" name="target" id="delTarget">
                <button type="submit" class="btn btn-danger" id="sureDelBtn" disabled>请冷静3秒</button>
            </form>
        </div>
    </div>
</div>
<script>
let delTimer = null;
function openDelPop(target, fname){
    const modal = document.getElementById('delModal');
    const targetInp = document.getElementById('delTarget');
    const nameText = document.getElementById('delFileName');
    const sureBtn = document.getElementById('sureDelBtn');
    clearInterval(delTimer);
    modal.style.display = 'flex';
    targetInp.value = target;
    nameText.innerText = fname;
    sureBtn.disabled = true;
    let sec = 3;
    sureBtn.innerText = `冷静${sec}s后删除`;
    delTimer = setInterval(()=>{
        sec--;
        sureBtn.innerText = `冷静${sec}s后删除`;
        if(sec <= 0){
            clearInterval(delTimer);
            sureBtn.disabled = false;
            sureBtn.innerText = '确认永久删除';
        }
    },1000);
}
function closeDelPop(){
    clearInterval(delTimer);
    document.getElementById('delModal').style.display = 'none';
}
function startUpload(){
    const files = document.getElementById("bigFile").files;
    if(files.length === 0){ alert("请选择文件"); return; }
    const arr = [];
    for(let i=0;i<files.length;i++){
        arr.push(files[i]);
    }
    sessionStorage.setItem("uploadTasks", JSON.stringify(arr));
    window.location.href = "/upload-progress?cur={{current_path}}";
}
</script>
</body>
</html>
"""

preview_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>预览 - {{name}}</title>
<style>
* {margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft Yahei",system-ui;}
body {background:#f3f4f6;padding:20px;}
.preview-box {max-width:1100px;margin:0 auto;background:#fff;border-radius:20px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.08);}
.operate {margin-bottom:20px;display:flex;gap:12px;flex-wrap:wrap;}
.btn {padding:10px 20px;border-radius:10px;text-decoration:none;font-size:15px;border:none;}
.btn-back {background:#6b7280;color:#fff;}
.btn-download {background:#6366f1;color:#fff;}
h3 {margin-bottom:20px;color:#1f2937;}
.img-view {max-width:100%;border-radius:12px;}
.txt-view {background:#f9fafb;padding:20px;border-radius:12px;white-space:pre-wrap;max-height:70vh;overflow:auto;border:1px solid #e5e7eb;}
video,iframe {width:100%;border-radius:12px;min-height:60vh;}
</style>
</head>
<body>
<div class="preview-box">
    <div class="operate">
        <a href="{{back}}" class="btn btn-back">← 返回列表</a>
        <a href="/download?path={{path}}" class="btn btn-download">下载文件</a>
    </div>
    <h3>{{name}}</h3>
    {% if t=='image' %}
        <img src="/raw?path={{path}}" class="img-view">
    {% elif t=='text' %}
        <div class="txt-view">{{content}}</div>
    {% elif t=='video' %}
        <video controls><source src="/raw?path={{path}}"></video>
    {% elif t=='pdf' %}
        <iframe src="/raw?path={{path}}"></iframe>
    {% else %}
        <p style="color:#6b7280;">当前文件不支持在线预览，请点击下载查看</p>
    {% endif %}
</div>
</body>
</html>
"""

admin_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>用户管理</title>
<style>
* {margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft Yahei",system-ui;}
body {background:#f3f4f6;}
.header {background:#6366f1;color:#fff;padding:16px 24px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
.header a {color:#fff;text-decoration:none;margin-left:20px;}
.container {max-width:900px;margin:20px auto;padding:0 20px;}
.card {background:#fff;border-radius:16px;padding:20px;margin-bottom:20px;box-shadow:0 4px 15px rgba(0,0,0,0.05);}
.form-row {display:flex;gap:10px;flex-wrap:wrap;}
.form-row input {padding:10px;border:1px solid #e5e7eb;border-radius:10px;flex:1;min-width:160px;}
.btn {padding:9px 18px;border-radius:10px;border:none;cursor:pointer;}
.btn-primary {background:#6366f1;color:#fff;}
.btn-danger {background:#ef4444;color:#fff;}
.user-item {padding:12px 0;border-bottom:1px solid #f3f4f6;display:flex;justify-content:space-between;align-items:center;}
</style>
</head>
<body>
<div class="header">
    <h2>后台用户管理 <a href="/">返回云盘</a></h2>
</div>
<div class="container">
    <div class="card">
        <h3 style="margin-bottom:15px;">新增/修改账号</h3>
        <form class="form-row" method="post" action="/adduser">
            <input name="u" placeholder="用户名">
            <input name="p" placeholder="密码">
            <button class="btn btn-primary">保存</button>
        </form>
    </div>
    <div class="card">
        {% for u,p in users.items() %}
        <div class="user-item">
            <span>{{ u }} ｜ 密码：{{ p }}</span>
            {% if u!='admin' %}
            <form action="/deluser" method="post">
                <input name="u" value="{{u}}" type="hidden">
                <button class="btn btn-danger">删除</button>
            </form>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>
</body>
</html>
"""

# ==================== 大文件上传API ====================
@flask_app.route("/api/chunk", methods=["POST"])
def api_chunk():
    if "user" not in session: return jsonify({"code":403})
    file_id = request.form.get("fileId")
    index = request.form.get("index")
    chunk = request.files.get("chunk")
    d = os.path.join(TEMP_CHUNK_DIR, file_id)
    os.makedirs(d, exist_ok=True)
    chunk.save(os.path.join(d, f"chunk_{index}"))
    return jsonify({"code":200})

@flask_app.route("/api/merge", methods=["POST"])
def api_merge():
    if "user" not in session: return jsonify({"code":403})
    data = request.json
    file_id = data.get("fileId")
    name = data.get("name")
    cur = data.get("cur")
    target = safe_p(cur)
    merge_chunks(file_id, name, target)
    return jsonify({"code":200})
'''
@flask_app.route("/upload-progress")
def page_upload_progress():
    if "user" not in session: return redirect("/login")
    cur = request.args.get("cur","")
    return render_template_string(upload_progress_html, cur=cur)
'''
# ==================== Flask路由 ====================
@flask_app.route("/login", methods=["GET", "POST"])
def login():
    err = ""
    if request.method == "POST":
        u = request.form.get("user","")
        p = request.form.get("passwd","")
        if u in config["users"] and config["users"][u] == p:
            session["user"] = u
            return redirect("/")
        err = "用户名或密码错误"
    return render_template_string(login_html, site_name=config["site_name"], error=err)

@flask_app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@flask_app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    cur = request.args.get("path","")
    full = safe_p(cur)
    if not full or not os.path.isdir(full):
        full = config["share_path"]
        cur = ""
    items = []
    for n in os.listdir(full):
        item_full = os.path.join(full, n)
        isdir = os.path.isdir(item_full)
        size_text = get_file_info(item_full, isdir)
        items.append((n, isdir, size_text))
    items.sort(key=lambda x:not x[1])
    parent = os.path.dirname(cur).replace("\\","/") if cur else ""
    if cur and parent == ".":
        parent = ""
    return render_template_string(main_html,
        site_name=config["site_name"], user=session["user"],
        is_admin=session["user"]=="admin",
        current_path=cur, items=items, parent_path=parent)

@flask_app.route("/mkdir", methods=["POST"])
def mkdir():
    if "user" not in session: return redirect("/login")
    n = secure_filename(request.form.get("name",""))
    cur = request.form.get("cur","")
    full = safe_p(os.path.join(cur, n))
    if full: os.makedirs(full, exist_ok=True)
    return redirect(f"/?path={cur}")

@flask_app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session: return redirect("/login")
    f = request.files.get("upfile")
    cur = request.form.get("cur","")
    full = safe_p(cur)
    if f and full:
        f.save(os.path.join(full, secure_filename(f.filename)))
    return redirect(f"/?path={cur}")

@flask_app.route("/download")
def download():
    if "user" not in session: return redirect("/login")
    p = request.args.get("path","")
    f = safe_p(p)
    if f and os.path.isfile(f):
        return send_file(f, as_attachment=True)
    return redirect("/")

@flask_app.route("/del", methods=["POST"])
def del_file():
    if "user" not in session: return redirect("/login")
    t = request.form.get("target","")
    f = safe_p(t)
    if f:
        if os.path.isdir(f):
            shutil.rmtree(f, ignore_errors=True)
        if os.path.isfile(f):
            os.remove(f)
    return redirect("/")

@flask_app.route("/preview")
def preview():
    if "user" not in session: return redirect("/login")
    p = request.args.get("path","")
    f = safe_p(p)
    if not f or not os.path.isfile(f): return redirect("/")
    n = os.path.basename(f)
    t = get_type(n)
    content = ""
    if t == "text":
        try:
            with open(f, "r", encoding="utf-8") as fp:
                content = fp.read()
        except:
            content = "文件编码不支持，无法预览"
    back = "/?path=" + os.path.dirname(p).replace("\\","/")
    return render_template_string(preview_html, name=n, path=p, t=t, content=content, back=back)

@flask_app.route("/raw")
def raw():
    if "user" not in session: return redirect("/login")
    f = safe_p(request.args.get("path",""))
    if f and os.path.isfile(f):
        return send_file(f, as_attachment=False)
    return "文件不存在",404

@flask_app.route("/admin")
def admin():
    if session.get("user")!="admin": return redirect("/")
    return render_template_string(admin_html, users=config["users"])

@flask_app.route("/adduser", methods=["POST"])
def adduser():
    if session.get("user")!="admin": return redirect("/")
    u = request.form.get("u","").strip()
    p = request.form.get("p","").strip()
    if u and p:
        config["users"][u] = p
        save_config(config)
    return redirect("/admin")

@flask_app.route("/deluser", methods=["POST"])
def deluser():
    if session.get("user")!="admin": return redirect("/")
    u = request.form.get("u","")
    if u in config["users"] and u!="admin":
        del config["users"][u]
        save_config(config)
    return redirect("/admin")

# ==================== 托盘 & GUI ====================
def run_flask():
    flask_app.run(host="::", port=config["port"], debug=False, threaded=True)

def get_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",8))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def create_tray_icon():
    img = Image.new('RGB', (32,32), color=(99, 102, 241))
    d = ImageDraw.Draw(img)
    d.ellipse((8,8,24,24), fill=(255,255,255))
    return img

class CloudGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("星硕NAS服务端v1.3.5")
        self.root.geometry("450x240")
        self.root.resizable(False,False)
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        ip = get_ip()
        ttk.Label(root, text="星硕NAS服务端", font=("微软雅黑",18)).pack(pady=15)
        ttk.Label(root, text=f"🌐 访问地址：http://{ip}:{config['port']}", font=("微软雅黑",11)).pack(pady=5)
        self.status = ttk.Label(root, text="🔴 状态：服务未启动", foreground="#ef4444", font=("微软雅黑",10))
        self.status.pack(pady=5)
        ttk.Button(root, text="启动服务", command=self.start).pack(pady=15)
        self.th = None
        self.tray_icon = None

    def start(self):
        if not self.th or not self.th.is_alive():
            self.th = threading.Thread(target=run_flask, daemon=True)
            self.th.start()
            self.status.config(text="🟢 状态：运行中", foreground="#10b981")

    def minimize_to_tray(self):
        if not Icon:
            messagebox.showwarning("提示","未安装pystray，无法托盘运行")
            self.root.destroy()
            return
        self.root.withdraw()
        if not self.tray_icon:
            self.tray_icon = Icon(
                "星硕NAS",
                create_tray_icon(),
                "星硕NAS - 运行中",
                menu=Menu(
                    MenuItem("显示窗口", self.show_window),
                    MenuItem("退出程序", self.quit_app)
                )
            )
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.deiconify()

    def quit_app(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    tk = Tk()
    app = CloudGUI(tk)
    tk.mainloop()
