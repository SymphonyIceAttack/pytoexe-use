#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🎬 批量视频转换压缩工具 v3.2
功能：批量转换 · 视频压缩 · 50+格式支持 · Web远程控制 · 文件下载
纯Python自带库，无需安装任何依赖
"""

import subprocess
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import shutil
import socket
import http.server
import socketserver
import webbrowser
import random
import json
import urllib.parse

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WebHandler(http.server.SimpleHTTPRequestHandler):
    app = None
    
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        
        if path == "/":
            self.send_html(self.get_index_html())
        elif path == "/api/status":
            self.send_json(self.get_status())
        elif path == "/api/download_list":
            self.send_json(self.get_download_list())
        elif path.startswith("/api/download/"):
            self.download_file(path.replace("/api/download/", ""))
        elif path.startswith("/api/delete/"):
            self.delete_file(path.replace("/api/delete/", ""))
        else:
            self.send_error(404)
    
    def do_POST(self):
        if urllib.parse.urlparse(self.path).path == "/api/convert":
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))
            if self.app:
                self.app.start_web_convert(data)
                self.send_json({"success": True})
            else:
                self.send_json({"success": False, "error": "应用未就绪"})
        else:
            self.send_error(404)
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def get_download_list(self):
        if not self.app:
            return []
        output_dir = self.app.output_dir.get()
        if not os.path.exists(output_dir):
            return []
        files = []
        valid_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
                     '.mpg', '.mpeg', '.3gp', '.ogv', '.ts', '.mp3', '.wav', '.aac', 
                     '.flac', '.m4a', '.ogg', '.wma', '.opus'}
        for f in os.listdir(output_dir):
            filepath = os.path.join(output_dir, f)
            if os.path.isfile(filepath) and os.path.splitext(f)[1].lower() in valid_exts:
                files.append({"name": f, "size": os.path.getsize(filepath), "time": os.path.getmtime(filepath)})
        files.sort(key=lambda x: x['time'], reverse=True)
        return files
    
    def download_file(self, filename):
        filepath = os.path.join(self.app.output_dir.get(), filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def delete_file(self, filename):
        filepath = os.path.join(self.app.output_dir.get(), filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                self.send_json({"success": True})
            except:
                self.send_json({"success": False})
        else:
            self.send_json({"success": False})
    
    def get_status(self):
        if self.app:
            return {
                "running": self.app.is_running,
                "progress": self.app.get_progress(),
                "current_file": self.app.get_current_file()
            }
        return {"running": False, "progress": 0, "current_file": ""}
    
    def get_index_html(self):
        return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎬 视频转换工具</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft YaHei',sans-serif;background:#1a1a2e;color:#e0e0e0;padding:16px}
.container{max-width:900px;margin:0 auto}
.header{text-align:center;padding:20px 0}
.header h1{font-size:28px;color:#e94560}
.header p{color:#8899aa;font-size:13px}
.card{background:#16213e;border-radius:10px;padding:16px;margin-bottom:16px;border:1px solid #0f3460}
.card-title{font-size:15px;font-weight:bold;margin-bottom:12px;color:#e94560}
.upload-area{border:2px dashed #0f3460;border-radius:8px;padding:30px;text-align:center;cursor:pointer;transition:.3s}
.upload-area:hover{border-color:#e94560;background:#1a1a2e}
.upload-area input{display:none}
.file-list{max-height:200px;overflow-y:auto}
.file-item{display:flex;justify-content:space-between;padding:6px 10px;background:#1a1a2e;border-radius:4px;margin-bottom:3px;font-size:13px}
.file-item .name{color:#00ff88;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.file-item .size{color:#8899aa;margin:0 8px}
.file-item .del{color:#ff6b6b;cursor:pointer}
.empty-text{color:#667788;text-align:center;padding:15px;font-size:13px}
.settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.settings-group{display:flex;flex-direction:column;gap:4px}
.settings-group label{font-size:12px;color:#8899aa}
select,input[type=text]{padding:6px 10px;background:#1a1a2e;color:#e0e0e0;border:1px solid #0f3460;border-radius:6px;font-size:13px;outline:none}
select:focus,input:focus{border-color:#e94560}
.quality-group{display:flex;gap:10px;flex-wrap:wrap}
.quality-group label{font-size:13px;cursor:pointer;display:flex;align-items:center;gap:4px}
.btn{padding:12px;border:none;border-radius:8px;font-size:15px;font-weight:bold;cursor:pointer;width:100%;transition:.3s}
.btn-primary{background:#e94560;color:#fff}
.btn-primary:hover{background:#ff6b6b}
.btn-primary:disabled{background:#555;cursor:not-allowed}
.btn-success{background:#00c853;color:#fff;width:auto;padding:4px 12px;font-size:12px}
.btn-success:hover{background:#00e676}
.progress-container{margin-top:10px}
.progress-bar{width:100%;height:6px;background:#1a1a2e;border-radius:3px;overflow:hidden}
.progress-bar .fill{height:100%;background:linear-gradient(90deg,#e94560,#ff6b6b);width:0%;transition:.3s}
.progress-text{display:flex;justify-content:space-between;margin-top:3px;font-size:12px;color:#8899aa}
.log-area{background:#0a0a1a;border-radius:6px;padding:10px;max-height:150px;overflow-y:auto;font-family:Consolas,monospace;font-size:12px;color:#00ff88;white-space:pre-wrap;word-break:break-all}
.download-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:6px}
.download-item{background:#1a1a2e;border-radius:6px;padding:8px 10px;display:flex;justify-content:space-between;align-items:center}
.download-item .name{font-size:12px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-right:6px}
.download-item .dl{color:#00ff88;cursor:pointer;padding:2px 6px;border-radius:3px;background:#0f3460;font-size:12px;text-decoration:none}
.download-item .dl:hover{background:#e94560}
.download-item .del{color:#ff6b6b;cursor:pointer;padding:2px 6px;font-size:12px}
.download-item .del:hover{background:#d32f2f;color:#fff;border-radius:3px}
.tab-bar{display:flex;gap:4px;margin-bottom:12px;border-bottom:1px solid #0f3460}
.tab{padding:8px 16px;cursor:pointer;border-radius:6px 6px 0 0;font-size:13px;color:#8899aa;transition:.3s}
.tab:hover{color:#e0e0e0;background:#1a1a2e}
.tab.active{color:#e94560;background:#1a1a2e;border-bottom:2px solid #e94560}
.tab-content{display:none}
.tab-content.active{display:block}
.status-bar{background:#16213e;border-radius:10px;padding:10px 14px;margin-bottom:16px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;border:1px solid #0f3460}
.status-item{display:flex;align-items:center;gap:6px;font-size:13px}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.status-dot.green{background:#00ff88}
.status-dot.yellow{background:#ffd93d}
@media(max-width:600px){.settings-grid{grid-template-columns:1fr}.status-bar{flex-direction:column}}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>🎬 视频转换工具</h1><p>上传 · 转换 · 下载</p></div>
<div class="status-bar">
<div class="status-item"><span class="status-dot green" id="statusDot"></span><span id="statusText">就绪</span></div>
<div class="status-item"><span id="fileCount">0 个文件</span></div>
<div class="status-item"><span id="convertStatus">空闲</span></div>
</div>
<div class="tab-bar"><div class="tab active" data-tab="tab1" onclick="switchTab('tab1')">📤 转换</div><div class="tab" data-tab="tab2" onclick="switchTab('tab2')">📥 下载</div></div>
<div id="tab1" class="tab-content active">
<div class="card"><div class="card-title">📁 上传文件</div>
<div class="upload-area" id="uploadArea"><div>📤 点击或拖拽上传</div><div style="font-size:11px;color:#667788;margin-top:4px;">MP4, AVI, MKV, MOV, WMV, FLV, WEBM, M4V, MPG, 3GP, OGV, TS</div><input type="file" id="fileInput" multiple accept=".mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v,.mpg,.mpeg,.3gp,.ogv,.ts"></div>
<div class="file-list" id="fileList"><div class="empty-text">暂无文件</div></div></div>
<div class="card"><div class="card-title">⚙️ 设置</div>
<div class="settings-grid">
<div class="settings-group"><label>输出格式</label><select id="formatSelect"><option value=".mp4">MP4</option><option value=".avi">AVI</option><option value=".mkv">MKV</option><option value=".mov">MOV</option><option value=".wmv">WMV</option><option value=".flv">FLV</option><option value=".webm">WEBM</option><option value=".mp3">MP3</option><option value=".wav">WAV</option><option value=".aac">AAC</option></select></div>
<div class="settings-group"><label>质量</label><div class="quality-group"><label><input type="radio" name="q" value="low">极速</label><label><input type="radio" name="q" value="medium" checked>平衡</label><label><input type="radio" name="q" value="high">极致</label></div></div>
<div class="settings-group"><label>压缩</label><label style="font-size:13px;"><input type="checkbox" id="compressCheck" checked>启用</label></div>
<div class="settings-group"><label>输出目录</label><input type="text" id="outputDir" value="~/Videos" readonly></div>
</div></div>
<div class="card"><button class="btn btn-primary" id="convertBtn" onclick="startConvert()">🚀 开始转换</button>
<div class="progress-container" id="progressContainer" style="display:none;"><div class="progress-bar"><div class="fill" id="progressFill"></div></div><div class="progress-text"><span id="progressPercent">0%</span><span id="progressFile">处理中...</span></div></div></div>
<div class="card"><div class="card-title">📝 日志</div><div class="log-area" id="logArea">等待开始...</div></div>
</div>
<div id="tab2" class="tab-content"><div class="card"><div class="card-title" style="display:flex;justify-content:space-between;align-items:center;"><span>📥 已转换文件</span><button class="btn btn-success" onclick="refreshDownloads()">🔄 刷新</button></div><div id="downloadList"><div class="empty-text">暂无文件</div></div></div></div>
</div>
<script>
let files=[],isConverting=!1,logLines=[],currentTab='tab1';
const fileInput=document.getElementById('fileInput'),fileList=document.getElementById('fileList'),uploadArea=document.getElementById('uploadArea'),formatSelect=document.getElementById('formatSelect'),compressCheck=document.getElementById('compressCheck'),convertBtn=document.getElementById('convertBtn'),progressFill=document.getElementById('progressFill'),progressPercent=document.getElementById('progressPercent'),progressFile=document.getElementById('progressFile'),progressContainer=document.getElementById('progressContainer'),logArea=document.getElementById('logArea'),fileCount=document.getElementById('fileCount'),statusText=document.getElementById('statusText'),statusDot=document.getElementById('statusDot'),convertStatus=document.getElementById('convertStatus'),downloadList=document.getElementById('downloadList');
function switchTab(id){document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelector(`[data-tab="${id}"]`).classList.add('active');currentTab=id;if(id==='tab2')refreshDownloads()}
uploadArea.onclick=()=>fileInput.click();
fileInput.onchange=()=>{Array.from(fileInput.files).forEach(f=>{if(!files.find(x=>x.name===f.name))files.push({name:f.name,size:f.size})});renderFiles();updateCount();fileInput.value=''};
uploadArea.ondragover=e=>{e.preventDefault();uploadArea.style.borderColor='#e94560'};
uploadArea.ondragleave=()=>{uploadArea.style.borderColor='#0f3460'};
uploadArea.ondrop=e=>{e.preventDefault();uploadArea.style.borderColor='#0f3460';Array.from(e.dataTransfer.files).forEach(f=>{if(!files.find(x=>x.name===f.name))files.push({name:f.name,size:f.size})});renderFiles();updateCount()};
function renderFiles(){if(!files.length){fileList.innerHTML='<div class="empty-text">暂无文件</div>';return}fileList.innerHTML=files.map((f,i)=>`<div class="file-item"><span class="name">🎬 ${f.name}</span><span class="size">${formatSize(f.size)}</span><span class="del" onclick="removeFile(${i})">✕</span></div>`).join('')}
function removeFile(i){files.splice(i,1);renderFiles();updateCount()}
function formatSize(b){if(b<1024)return b+'B';if(b<1048576)return(b/1024).toFixed(1)+'KB';if(b<1073741824)return(b/1048576).toFixed(1)+'MB';return(b/1073741824).toFixed(2)+'GB'}
function updateCount(){fileCount.textContent=files.length+' 个文件'}
function addLog(m){logLines.push(m);if(logLines.length>200)logLines=logLines.slice(-200);logArea.textContent=logLines.join('\\n');logArea.scrollTop=logArea.scrollHeight}
function startConvert(){if(isConverting||!files.length)return;isConverting=!0;convertBtn.disabled=!0;convertBtn.textContent='⏳ 转换中...';progressContainer.style.display='block';progressFill.style.width='0%';progressPercent.textContent='0%';logLines=[];addLog('🎬 开始转换...');addLog('📁 共 '+files.length+' 个文件');const q=document.querySelector('input[name="q"]:checked').value,f=formatSelect.value,c=compressCheck.checked;fetch('/api/convert',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({files:files.map(x=>x.name),format:f,quality:q,compress:c})}).then(r=>r.json()).then(d=>{if(d.success)addLog('✅ 转换任务已提交')}).catch(e=>addLog('❌ '+e.message))}
function refreshDownloads(){fetch('/api/download_list').then(r=>r.json()).then(data=>{if(!data.length){downloadList.innerHTML='<div class="empty-text">暂无文件</div>';return}downloadList.innerHTML='<div class="download-grid">'+data.map(f=>`<div class="download-item"><span class="name">${f.name}</span><a href="/api/download/${encodeURIComponent(f.name)}" class="dl">⬇</a><span class="del" onclick="deleteFile('${f.name}')">✕</span></div>`).join('')+'</div>'}).catch(()=>{})}
function deleteFile(name){if(!confirm('确定删除 "'+name+'" 吗？'))return;fetch('/api/delete/'+encodeURIComponent(name)).then(r=>r.json()).then(d=>{if(d.success)refreshDownloads()})}
setInterval(()=>{fetch('/api/status').then(r=>r.json()).then(d=>{if(d.running){statusDot.className='status-dot yellow';statusText.textContent='转换中...';convertStatus.textContent='处理中 '+d.progress+'%';progressFill.style.width=d.progress+'%';progressPercent.textContent=d.progress+'%';if(d.current_file)progressFile.textContent=d.current_file}else{statusDot.className='status-dot green';statusText.textContent='就绪';convertStatus.textContent='空闲';if(d.progress===100){progressFill.style.width='100%';progressPercent.textContent='100%';progressFile.textContent='完成!';setTimeout(()=>{progressContainer.style.display='none';convertBtn.disabled=!1;convertBtn.textContent='🚀 开始转换';isConverting=!1},2000)}}})},1500);
setInterval(()=>{if(currentTab==='tab2')refreshDownloads()},5000);
addLog('🌐 已连接');addLog('💡 上传文件后点击转换');
</script></body></html>'''

class FFmpegGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 批量视频转换工具")
        self.root.geometry("950x800")
        self.root.minsize(850, 700)
        self.root.configure(bg='#1a1a2e')
        
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.input_files = []
        self.output_dir = tk.StringVar(value=os.path.expanduser("~/Videos"))
        self.quality = tk.StringVar(value="medium")
        self.selected_format = tk.StringVar(value=".mp4")
        self.compress_mode = tk.BooleanVar(value=True)
        
        self.share_enabled = tk.BooleanVar(value=False)
        self.share_port = tk.StringVar(value="")
        self.share_server = None
        self.share_url = ""
        
        self.is_running = False
        self.current_progress = 0
        self.current_file = ""
        self.process = None
        
        self.file_count_label = tk.StringVar(value="共 0 个文件")
        
        self.format_categories = {
            "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv", ".ts"],
            "音频": [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg", ".wma", ".opus"],
            "设备": [".mp4_手机", ".mp4_平板", ".mp4_电视", ".mp4_网页", ".mp4_微信", ".mp4_抖音"],
            "压缩": [".mp4_高压缩", ".mp4_中压缩", ".mp4_低压缩"]
        }
        
        WebHandler.app = self
        
        self.create_widgets()
        self.check_ffmpeg()
        self.find_available_port()
    
    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            for p in [os.path.join(os.path.dirname(sys.executable), 'ffmpeg.exe'), resource_path('ffmpeg.exe')]:
                if os.path.exists(p):
                    return p
        return 'ffmpeg.exe' if os.path.exists('ffmpeg.exe') else ('ffmpeg' if shutil.which('ffmpeg') else 'ffmpeg')
    
    def check_ffmpeg(self):
        try:
            subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, timeout=3)
            self.status_label.config(text="✅ FFmpeg 已就绪", fg='#00ff88')
            return True
        except:
            self.status_label.config(text="❌ FFmpeg 未找到", fg='#ff6b6b')
            return False
    
    def find_available_port(self):
        for port in random.sample(range(8000, 9000), 100):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', port))
                sock.close()
                self.share_port.set(str(port))
                return port
            except:
                continue
        self.share_port.set("0")
        return 0
    
    def create_widgets(self):
        main = tk.Frame(self.root, bg='#1a1a2e')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # 标题
        tk.Label(main, text="🎬 批量视频转换工具", font=('微软雅黑', 20, 'bold'), fg='#e94560', bg='#1a1a2e').pack(pady=(0,5))
        tk.Label(main, text="批量转换 · 压缩 · Web远程控制", font=('微软雅黑', 10), fg='#8899aa', bg='#1a1a2e').pack(pady=(0,15))
        
        # 状态
        status_frame = tk.Frame(main, bg='#1a1a2e')
        status_frame.pack(fill=tk.X, pady=(0,10))
        self.status_label = tk.Label(status_frame, text="🔍 检测FFmpeg...", font=('微软雅黑', 10), fg='#ffd93d', bg='#1a1a2e')
        self.status_label.pack(side=tk.LEFT)
        
        # 文件区域
        file_frame = tk.Frame(main, bg='#1a1a2e')
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        header = tk.Frame(file_frame, bg='#1a1a2e')
        header.pack(fill=tk.X, pady=(0,5))
        tk.Label(header, text="📁 文件列表:", font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e').pack(side=tk.LEFT)
        tk.Label(header, textvariable=self.file_count_label, font=('微软雅黑', 9), fg='#8899aa', bg='#1a1a2e').pack(side=tk.LEFT, padx=(10,0))
        
        btn_frame = tk.Frame(header, bg='#1a1a2e')
        btn_frame.pack(side=tk.RIGHT)
        for t, c in [("➕ 添加", self.add_files), ("📂 文件夹", self.add_folder), ("🗑️ 清空", self.clear_files)]:
            tk.Button(btn_frame, text=t, font=('微软雅黑', 9), bg='#0f3460', fg='white', relief=tk.FLAT, padx=12, pady=4, cursor='hand2', command=c).pack(side=tk.LEFT, padx=(0,5))
        
        list_frame = tk.Frame(file_frame, bg='#0a0a1a')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox = tk.Listbox(list_frame, font=('Consolas', 9), bg='#0a0a1a', fg='#00ff88', selectmode=tk.EXTENDED, yscrollcommand=scroll.set, relief=tk.FLAT, highlightthickness=0, height=8)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.file_listbox.yview)
        
        # 右键菜单
        menu = tk.Menu(self.root, tearoff=0, bg='#1a1a2e', fg='#e0e0e0')
        menu.add_command(label="移除选中", command=self.remove_selected)
        menu.add_command(label="清空列表", command=self.clear_files)
        self.file_listbox.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))
        
        # 设置
        settings = tk.Frame(main, bg='#1a1a2e')
        settings.pack(fill=tk.X, pady=8)
        
        row1 = tk.Frame(settings, bg='#1a1a2e')
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="格式:", font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e').pack(side=tk.LEFT, padx=(0,8))
        self.format_combo = ttk.Combobox(row1, textvariable=self.selected_format, values=self.format_categories["视频"], font=('微软雅黑', 9), state='readonly', width=12)
        self.format_combo.pack(side=tk.LEFT, padx=(0,10))
        for cat in ["视频", "音频", "设备", "压缩"]:
            tk.Button(row1, text=cat, font=('微软雅黑', 8), bg='#0f3460', fg='#8899aa', relief=tk.FLAT, padx=8, pady=2, cursor='hand2', command=lambda c=cat: self.switch_category(c)).pack(side=tk.LEFT, padx=2)
        
        tk.Label(row1, text="质量:", font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e').pack(side=tk.LEFT, padx=(15,8))
        for t, v in [("极速","low"), ("平衡","medium"), ("极致","high")]:
            tk.Radiobutton(row1, text=t, variable=self.quality, value=v, font=('微软雅黑', 9), fg='#e0e0e0', bg='#1a1a2e', selectcolor='#1a1a2e', relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=(0,8))
        
        row2 = tk.Frame(settings, bg='#1a1a2e')
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="输出:", font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e').pack(side=tk.LEFT, padx=(0,8))
        tk.Entry(row2, textvariable=self.output_dir, font=('微软雅黑', 9), bg='#16213e', fg='#e0e0e0', relief=tk.FLAT, highlightthickness=1, highlightcolor='#e94560', highlightbackground='#0f3460', width=35).pack(side=tk.LEFT, padx=(0,8), ipady=3)
        tk.Button(row2, text="浏览", font=('微软雅黑', 9), bg='#0f3460', fg='white', relief=tk.FLAT, padx=12, pady=3, cursor='hand2', command=self.select_output_dir).pack(side=tk.LEFT, padx=(0,15))
        tk.Checkbutton(row2, text="📦 压缩", variable=self.compress_mode, font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e', selectcolor='#1a1a2e', cursor='hand2').pack(side=tk.LEFT)
        
        row3 = tk.Frame(settings, bg='#1a1a2e')
        row3.pack(fill=tk.X, pady=3)
        tk.Checkbutton(row3, text="🌐 Web远程控制", variable=self.share_enabled, font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e', selectcolor='#1a1a2e', cursor='hand2', command=self.toggle_share).pack(side=tk.LEFT, padx=(0,8))
        tk.Label(row3, text="端口:", font=('微软雅黑', 9), fg='#8899aa', bg='#1a1a2e').pack(side=tk.LEFT, padx=(0,5))
        tk.Entry(row3, textvariable=self.share_port, font=('微软雅黑', 9), bg='#16213e', fg='#e0e0e0', relief=tk.FLAT, width=8, highlightthickness=1, highlightcolor='#e94560', highlightbackground='#0f3460', state='readonly').pack(side=tk.LEFT, padx=(0,10))
        self.share_status_label = tk.Label(row3, text="⏸️ 已关闭", font=('微软雅黑', 9), fg='#8899aa', bg='#1a1a2e')
        self.share_status_label.pack(side=tk.LEFT)
        self.share_url_label = tk.Label(row3, text="", font=('微软雅黑', 9), fg='#00ff88', bg='#1a1a2e', cursor='hand2')
        self.share_url_label.pack(side=tk.LEFT, padx=(10,0))
        self.share_url_label.bind("<Button-1>", lambda e: webbrowser.open(self.share_url) if self.share_url else None)
        
        # 转换按钮
        self.convert_btn = tk.Button(main, text="🚀 开始批量转换", font=('微软雅黑', 13, 'bold'), bg='#e94560', fg='white', relief=tk.FLAT, pady=12, cursor='hand2', command=self.convert_files)
        self.convert_btn.pack(fill=tk.X, pady=10)
        
        # 进度
        prog_frame = tk.Frame(main, bg='#1a1a2e')
        prog_frame.pack(fill=tk.X, pady=3)
        self.progress_bar = ttk.Progressbar(prog_frame, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X)
        info = tk.Frame(prog_frame, bg='#1a1a2e')
        info.pack(fill=tk.X, pady=2)
        self.progress_label = tk.Label(info, text="0%", font=('微软雅黑', 9), fg='#00ff88', bg='#1a1a2e')
        self.progress_label.pack(side=tk.LEFT)
        self.file_progress_label = tk.Label(info, text="等待开始...", font=('微软雅黑', 9), fg='#8899aa', bg='#1a1a2e')
        self.file_progress_label.pack(side=tk.RIGHT)
        
        # 日志
        log_frame = tk.Frame(main, bg='#1a1a2e')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        log_header = tk.Frame(log_frame, bg='#1a1a2e')
        log_header.pack(fill=tk.X, pady=(0,3))
        tk.Label(log_header, text="📝 日志:", font=('微软雅黑', 10, 'bold'), fg='#e0e0e0', bg='#1a1a2e').pack(side=tk.LEFT)
        tk.Button(log_header, text="清空", font=('微软雅黑', 8), bg='#0f3460', fg='white', relief=tk.FLAT, padx=10, pady=2, cursor='hand2', command=self.clear_log).pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9), bg='#0a0a1a', fg='#00ff88', relief=tk.FLAT, highlightthickness=1, highlightcolor='#0f3460', highlightbackground='#0f3460', height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state='disabled')
        
        self.update_file_count()
        self.log("🎯 就绪，添加文件后点击转换")
        self.log(f"🌐 Web端口: {self.share_port.get()} (默认关闭)")
    
    def switch_category(self, cat):
        self.format_combo['values'] = self.format_categories[cat]
        if self.format_categories[cat]:
            self.selected_format.set(self.format_categories[cat][0])
    
    def add_files(self):
        files = filedialog.askopenfilenames(title="选择视频", filetypes=[("视频", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.3gp *.ogv *.ts")])
        for f in files:
            if f not in self.input_files:
                self.input_files.append(f)
                self.file_listbox.insert(tk.END, os.path.basename(f))
        self.update_file_count()
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            exts = {'.mp4','.avi','.mkv','.mov','.wmv','.flv','.webm','.m4v','.mpg','.mpeg','.3gp','.ogv','.ts'}
            count = 0
            for root, _, files in os.walk(folder):
                for f in files:
                    if os.path.splitext(f)[1].lower() in exts:
                        path = os.path.join(root, f)
                        if path not in self.input_files:
                            self.input_files.append(path)
                            self.file_listbox.insert(tk.END, f)
                            count += 1
            self.update_file_count()
            self.log(f"📂 添加了 {count} 个文件")
    
    def remove_selected(self):
        for i in reversed(self.file_listbox.curselection()):
            del self.input_files[i]
            self.file_listbox.delete(i)
        self.update_file_count()
    
    def clear_files(self):
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.update_file_count()
    
    def update_file_count(self):
        self.file_count_label.set(f"共 {len(self.input_files)} 个文件")
    
    def select_output_dir(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.output_dir.set(d)
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def toggle_share(self):
        if self.share_enabled.get():
            self.start_share()
        else:
            self.stop_share()
    
    def start_share(self):
        try:
            port = int(self.share_port.get()) or self.find_available_port()
            self.share_port.set(str(port))
            ip = socket.gethostbyname(socket.gethostname())
            
            out_dir = self.output_dir.get()
            os.makedirs(out_dir, exist_ok=True)
            os.chdir(out_dir)
            
            self.share_server = socketserver.TCPServer(("", port), WebHandler)
            self.share_server.allow_reuse_address = True
            self.share_url = f"http://{ip}:{port}"
            self.share_status_label.config(text="🟢 运行中", fg='#00ff88')
            self.share_url_label.config(text=f"🌐 {self.share_url}")
            self.log(f"🌐 Web已启动: {self.share_url}")
            
            t = threading.Thread(target=self.share_server.serve_forever)
            t.daemon = True
            t.start()
        except Exception as e:
            self.log(f"❌ 启动失败: {e}")
            self.share_enabled.set(False)
            self.share_status_label.config(text="❌ 失败", fg='#ff6b6b')
    
    def stop_share(self):
        try:
            if self.share_server:
                self.share_server.shutdown()
                self.share_server.server_close()
                self.share_server = None
            self.share_status_label.config(text="⏸️ 已关闭", fg='#8899aa')
            self.share_url_label.config(text="")
            self.log("🌐 Web已关闭")
        except:
            pass
    
    def get_progress(self):
        return self.current_progress
    
    def get_current_file(self):
        return self.current_file
    
    def start_web_convert(self, data):
        self.log("🌐 收到Web转换请求")
        self.convert_files()
    
    def get_format_params(self, fmt):
        base = {
            ".mp4": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4"},
            ".avi": {"vcodec": "mpeg4", "acodec": "mp3", "ext": ".avi"},
            ".mkv": {"vcodec": "libx264", "acodec": "aac", "ext": ".mkv"},
            ".mov": {"vcodec": "libx264", "acodec": "aac", "ext": ".mov"},
            ".wmv": {"vcodec": "wmv2", "acodec": "wmav2", "ext": ".wmv"},
            ".flv": {"vcodec": "flv", "acodec": "mp3", "ext": ".flv"},
            ".webm": {"vcodec": "libvpx", "acodec": "libvorbis", "ext": ".webm"},
            ".m4v": {"vcodec": "libx264", "acodec": "aac", "ext": ".m4v"},
            ".mpg": {"vcodec": "mpeg2video", "acodec": "mp2", "ext": ".mpg"},
            ".mpeg": {"vcodec": "mpeg2video", "acodec": "mp2", "ext": ".mpeg"},
            ".3gp": {"vcodec": "h263", "acodec": "aac", "ext": ".3gp"},
            ".ogv": {"vcodec": "libtheora", "acodec": "libvorbis", "ext": ".ogv"},
            ".ts": {"vcodec": "libx264", "acodec": "aac", "ext": ".ts"},
            ".mp3": {"vcodec": None, "acodec": "libmp3lame", "ext": ".mp3"},
            ".wav": {"vcodec": None, "acodec": "pcm_s16le", "ext": ".wav"},
            ".aac": {"vcodec": None, "acodec": "aac", "ext": ".aac"},
            ".flac": {"vcodec": None, "acodec": "flac", "ext": ".flac"},
            ".m4a": {"vcodec": None, "acodec": "aac", "ext": ".m4a"},
            ".ogg": {"vcodec": None, "acodec": "libvorbis", "ext": ".ogg"},
            ".wma": {"vcodec": None, "acodec": "wmav2", "ext": ".wma"},
            ".opus": {"vcodec": None, "acodec": "libopus", "ext": ".opus"},
            ".mp4_手机": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "720x1280"},
            ".mp4_平板": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "1080x1920"},
            ".mp4_电视": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "1920x1080"},
            ".mp4_网页": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "preset": "fast"},
            ".mp4_微信": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "640x360", "bitrate": "500k"},
            ".mp4_抖音": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "1080x1920", "fps": "30"},
            ".mp4_高压缩": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "crf": "28"},
            ".mp4_中压缩": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "crf": "23"},
            ".mp4_低压缩": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "crf": "18"},
        }
        return base.get(fmt, base[".mp4"])
    
    def convert_files(self):
        if not self.input_files:
            messagebox.showerror("错误", "请先添加文件")
            return
        if not self.check_ffmpeg():
            messagebox.showerror("错误", "FFmpeg未找到")
            return
        if self.is_running:
            return
        
        self.convert_btn.config(state='disabled', text='⏳ 转换中...')
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")
        self.is_running = True
        self.current_progress = 0
        self.total_files = len(self.input_files)
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        threading.Thread(target=self._convert_thread, daemon=True).start()
    
    def _convert_thread(self):
        quality_map = {"low": "28", "medium": "23", "high": "18"}
        qv = quality_map.get(self.quality.get(), "23")
        total = len(self.input_files)
        
        for idx, infile in enumerate(self.input_files):
            self.current_file = os.path.basename(infile)
            prog = int((idx / total) * 100)
            self.current_progress = prog
            self.root.after(0, lambda p=prog: self.progress_bar.config(value=p))
            self.root.after(0, lambda p=prog: self.progress_label.config(text=f"{p}%"))
            self.root.after(0, lambda i=idx, t=total: self.file_progress_label.config(text=f"{i+1}/{t} - {self.current_file}"))
            
            self.log(f"\n🎬 [{idx+1}/{total}] {self.current_file}")
            
            fmt = self.selected_format.get()
            params = self.get_format_params(fmt)
            outfile = os.path.join(self.output_dir.get(), f"{os.path.splitext(self.current_file)[0]}_转换{params['ext']}")
            
            cmd = [self.ffmpeg_path, "-i", infile]
            
            if params.get("vcodec"):
                cmd.extend(["-c:v", params["vcodec"]])
                if fmt in [".mp4_高压缩"]: cmd.extend(["-crf", "28"])
                elif fmt in [".mp4_中压缩"]: cmd.extend(["-crf", "23"])
                elif fmt in [".mp4_低压缩"]: cmd.extend(["-crf", "18"])
                elif self.compress_mode.get(): cmd.extend(["-crf", qv])
                if params.get("preset"): cmd.extend(["-preset", params["preset"]])
                if params.get("scale"): cmd.extend(["-vf", f"scale={params['scale']}"])
                if params.get("bitrate"): cmd.extend(["-b:v", params["bitrate"]])
                if params.get("fps"): cmd.extend(["-r", params["fps"]])
            
            if params.get("acodec"):
                cmd.extend(["-c:a", params["acodec"]])
            
            cmd.extend(["-y", outfile])
            self.log(f"📤 {outfile}")
            
            try:
                p = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                for line in p.stderr:
                    if "frame=" in line or "size=" in line or "time=" in line:
                        self.log(line.strip())
                p.wait()
                if p.returncode == 0:
                    self.log(f"✅ 成功! 大小: {self.get_file_size(outfile)}")
                else:
                    self.log(f"❌ 失败")
            except Exception as e:
                self.log(f"❌ 错误: {e}")
        
        self.root.after(0, self.conversion_complete)
    
    def conversion_complete(self):
        self.progress_bar['value'] = 100
        self.progress_label.config(text="100%")
        self.current_progress = 100
        self.is_running = False
        self.convert_btn.config(state='normal', text='🚀 开始批量转换')
        self.file_progress_label.config(text="完成!")
        self.log(f"\n🎉 完成! 共 {len(self.input_files)} 个文件")
        messagebox.showinfo("完成", f"转换完成!\n{len(self.input_files)} 个文件\n输出: {self.output_dir.get()}")
    
    def get_file_size(self, path):
        try:
            s = os.path.getsize(path)
            for unit in ['B','KB','MB','GB']:
                if s < 1024:
                    return f"{s:.1f}{unit}"
                s /= 1024
            return f"{s:.1f}TB"
        except:
            return "未知"

def main():
    root = tk.Tk()
    FFmpegGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()