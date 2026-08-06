#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🎬 批量视频转换压缩工具 v3.1
功能：批量转换 · 视频压缩 · 50+格式支持 · Web远程控制 · 文件下载
纯Python自带库，无需安装任何依赖
"""

import subprocess
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import shutil
import socket
import http.server
import socketserver
import webbrowser
import random
import json
import urllib.parse
import time

def resource_path(relative_path):
    """获取资源文件路径（支持打包后运行）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WebHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP处理器，提供Web界面"""
    
    app = None
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == "/":
            self.send_html(self.get_index_html())
        elif path == "/api/status":
            self.send_json(self.get_status())
        elif path == "/api/files":
            self.send_json(self.get_files())
        elif path == "/api/download_list":
            self.send_json(self.get_download_list())
        elif path.startswith("/api/download/"):
            filename = path.replace("/api/download/", "")
            self.download_file(filename)
        elif path.startswith("/api/delete/"):
            filename = path.replace("/api/delete/", "")
            self.delete_file(filename)
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == "/api/convert":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            self.handle_convert(data)
        else:
            self.send_error(404, "Not Found")
    
    def send_html(self, html):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def get_download_list(self):
        """获取可下载文件列表"""
        if self.app:
            output_dir = self.app.output_dir.get()
            files = []
            if os.path.exists(output_dir):
                for f in os.listdir(output_dir):
                    filepath = os.path.join(output_dir, f)
                    if os.path.isfile(filepath):
                        ext = os.path.splitext(f)[1].lower()
                        # 只显示视频/音频文件
                        if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
                                   '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv', '.ts',
                                   '.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg', '.wma', '.opus']:
                            files.append({
                                "name": f,
                                "size": os.path.getsize(filepath),
                                "time": os.path.getmtime(filepath)
                            })
            files.sort(key=lambda x: x['time'], reverse=True)
            return files
        return []
    
    def download_file(self, filename):
        """下载文件"""
        if self.app:
            filepath = os.path.join(self.app.output_dir.get(), filename)
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                return
        self.send_error(404, "File not found")
    
    def delete_file(self, filename):
        """删除文件"""
        if self.app:
            filepath = os.path.join(self.app.output_dir.get(), filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    self.send_json({"success": True, "message": f"已删除: {filename}"})
                    return
                except Exception as e:
                    self.send_json({"success": False, "error": str(e)})
                    return
        self.send_json({"success": False, "error": "文件不存在"})
    
    def get_status(self):
        """获取状态"""
        if self.app:
            return {
                "running": self.app.is_running,
                "progress": self.app.get_progress(),
                "current_file": self.app.get_current_file(),
                "total_files": len(self.app.input_files)
            }
        return {"running": False, "progress": 0, "current_file": "", "total_files": 0}
    
    def get_files(self):
        """获取文件列表"""
        if self.app:
            return [{"name": os.path.basename(f), "size": os.path.getsize(f)} for f in self.app.input_files]
        return []
    
    def handle_convert(self, data):
        """处理转换请求"""
        if self.app:
            self.app.start_web_convert(data)
            self.send_json({"success": True, "message": "转换已开始"})
        else:
            self.send_json({"success": False, "error": "应用未就绪"})
    
    def get_index_html(self):
        """获取主页HTML"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 批量视频转换工具 - Web控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', 'PingFang SC', -apple-system, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 16px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { text-align: center; padding: 20px 0 16px; }
        .header h1 { font-size: 28px; color: #e94560; margin-bottom: 6px; }
        .header p { color: #8899aa; font-size: 13px; }
        
        .status-bar {
            background: #16213e;
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            border: 1px solid #0f3460;
        }
        .status-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .status-dot.green { background: #00ff88; }
        .status-dot.red { background: #ff6b6b; }
        .status-dot.yellow { background: #ffd93d; }
        
        .card {
            background: #16213e;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid #0f3460;
        }
        .card-title { font-size: 15px; font-weight: bold; margin-bottom: 12px; color: #e94560; }
        
        .upload-area {
            border: 2px dashed #0f3460;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover { border-color: #e94560; background: #1a1a2e; }
        .upload-area input { display: none; }
        .upload-area .icon { font-size: 36px; }
        .upload-area .text { margin-top: 8px; color: #8899aa; }
        
        .file-list { max-height: 250px; overflow-y: auto; }
        .file-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 8px 12px; background: #1a1a2e; border-radius: 6px;
            margin-bottom: 4px; font-size: 13px;
        }
        .file-item:hover { background: #0f3460; }
        .file-item .name { flex: 1; color: #00ff88; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .file-item .size { color: #8899aa; margin: 0 10px; font-size: 12px; }
        .file-item .remove { color: #ff6b6b; cursor: pointer; padding: 0 4px; font-size: 16px; }
        .file-item .remove:hover { color: #ff4444; }
        
        .empty-text { color: #667788; text-align: center; padding: 20px; font-size: 14px; }
        
        .settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .settings-group { display: flex; flex-direction: column; gap: 5px; }
        .settings-group label { font-size: 12px; color: #8899aa; }
        select, input[type="text"] {
            padding: 8px 10px; background: #1a1a2e; color: #e0e0e0;
            border: 1px solid #0f3460; border-radius: 6px; font-size: 13px; outline: none;
        }
        select:focus, input[type="text"]:focus { border-color: #e94560; }
        
        .quality-group { display: flex; gap: 12px; flex-wrap: wrap; }
        .quality-group label { display: flex; align-items: center; gap: 4px; font-size: 13px; cursor: pointer; }
        
        .btn {
            padding: 12px 20px; border: none; border-radius: 8px;
            font-size: 15px; font-weight: bold; cursor: pointer;
            transition: all 0.3s; width: 100%;
        }
        .btn-primary { background: #e94560; color: white; }
        .btn-primary:hover { background: #ff6b6b; transform: translateY(-2px); }
        .btn-primary:disabled { background: #555; cursor: not-allowed; transform: none; }
        .btn-success { background: #00c853; color: white; }
        .btn-success:hover { background: #00e676; }
        .btn-danger { background: #d32f2f; color: white; }
        .btn-danger:hover { background: #f44336; }
        
        .progress-container { margin-top: 12px; }
        .progress-bar { width: 100%; height: 6px; background: #1a1a2e; border-radius: 3px; overflow: hidden; }
        .progress-bar .fill { height: 100%; background: linear-gradient(90deg, #e94560, #ff6b6b); transition: width 0.3s; width: 0%; }
        .progress-text { display: flex; justify-content: space-between; margin-top: 4px; font-size: 12px; color: #8899aa; }
        
        .log-area {
            background: #0a0a1a; border-radius: 6px; padding: 12px;
            max-height: 200px; overflow-y: auto;
            font-family: 'Consolas', monospace; font-size: 12px;
            color: #00ff88; white-space: pre-wrap; word-break: break-all;
        }
        .log-area::-webkit-scrollbar { width: 4px; }
        .log-area::-webkit-scrollbar-track { background: #0a0a1a; }
        .log-area::-webkit-scrollbar-thumb { background: #0f3460; border-radius: 2px; }
        
        .download-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }
        .download-item {
            background: #1a1a2e; border-radius: 6px; padding: 10px 12px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .download-item .name { 
            font-size: 12px; color: #e0e0e0; 
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap; 
            flex: 1; margin-right: 8px;
        }
        .download-item .actions { display: flex; gap: 4px; }
        .download-item .actions a, .download-item .actions span {
            text-decoration: none; padding: 2px 8px; border-radius: 4px;
            font-size: 12px; cursor: pointer;
        }
        .download-item .actions .dl { background: #0f3460; color: #00ff88; }
        .download-item .actions .dl:hover { background: #e94560; }
        .download-item .actions .del { background: #2d2d44; color: #ff6b6b; }
        .download-item .actions .del:hover { background: #d32f2f; color: white; }
        .download-empty { color: #667788; text-align: center; padding: 20px; }
        
        .tab-bar {
            display: flex; gap: 4px; margin-bottom: 12px;
            border-bottom: 1px solid #0f3460;
        }
        .tab {
            padding: 8px 16px; cursor: pointer; border-radius: 6px 6px 0 0;
            font-size: 13px; color: #8899aa; transition: all 0.3s;
        }
        .tab:hover { color: #e0e0e0; background: #1a1a2e; }
        .tab.active { color: #e94560; background: #1a1a2e; border-bottom: 2px solid #e94560; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        @media (max-width: 768px) {
            .settings-grid { grid-template-columns: 1fr; }
            .status-bar { flex-direction: column; align-items: stretch; gap: 4px; }
            .header h1 { font-size: 22px; }
            .download-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 批量视频转换工具</h1>
            <p>Web 远程控制台 · 上传 · 转换 · 下载</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot green" id="statusDot"></span>
                <span id="statusText">已连接</span>
            </div>
            <div class="status-item">
                <span id="fileCount">共 0 个文件</span>
            </div>
            <div class="status-item">
                <span id="convertStatus">就绪</span>
            </div>
        </div>
        
        <!-- 标签页 -->
        <div class="tab-bar">
            <div class="tab active" data-tab="tab-convert" onclick="switchTab('tab-convert')">📤 转换</div>
            <div class="tab" data-tab="tab-download" onclick="switchTab('tab-download')">📥 下载</div>
        </div>
        
        <!-- 转换标签页 -->
        <div id="tab-convert" class="tab-content active">
            <div class="card">
                <div class="card-title">📁 上传文件</div>
                <div class="upload-area" id="uploadArea">
                    <div class="icon">📤</div>
                    <div class="text">点击或拖拽上传视频文件</div>
                    <div style="font-size:11px;color:#667788;margin-top:4px;">MP4, AVI, MKV, MOV, WMV, FLV, WEBM, M4V, MPG, 3GP, OGV, TS</div>
                    <input type="file" id="fileInput" multiple accept=".mp4,.avi,.mkv,.mov,.wmv,.flv,.webm,.m4v,.mpg,.mpeg,.3gp,.ogv,.ts">
                </div>
                <div class="file-list" id="fileList">
                    <div class="empty-text">暂无文件，请上传</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">⚙️ 转换设置</div>
                <div class="settings-grid">
                    <div class="settings-group">
                        <label>输出格式</label>
                        <select id="formatSelect">
                            <option value=".mp4">MP4</option>
                            <option value=".avi">AVI</option>
                            <option value=".mkv">MKV</option>
                            <option value=".mov">MOV</option>
                            <option value=".wmv">WMV</option>
                            <option value=".flv">FLV</option>
                            <option value=".webm">WEBM</option>
                            <option value=".mp3">MP3 (音频)</option>
                            <option value=".wav">WAV (音频)</option>
                            <option value=".aac">AAC (音频)</option>
                        </select>
                    </div>
                    <div class="settings-group">
                        <label>转换质量</label>
                        <div class="quality-group">
                            <label><input type="radio" name="quality" value="low"> 极速</label>
                            <label><input type="radio" name="quality" value="medium" checked> 平衡</label>
                            <label><input type="radio" name="quality" value="high"> 极致</label>
                        </div>
                    </div>
                    <div class="settings-group">
                        <label>压缩视频</label>
                        <label style="font-size:13px;"><input type="checkbox" id="compressCheck" checked> 启用压缩</label>
                    </div>
                    <div class="settings-group">
                        <label>输出目录</label>
                        <input type="text" id="outputDir" value="~/Videos" readonly>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <button class="btn btn-primary" id="convertBtn" onclick="startConvert()">🚀 开始批量转换</button>
                <div class="progress-container" id="progressContainer" style="display:none;">
                    <div class="progress-bar"><div class="fill" id="progressFill"></div></div>
                    <div class="progress-text">
                        <span id="progressPercent">0%</span>
                        <span id="progressFile">处理中...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">📝 转换日志</div>
                <div class="log-area" id="logArea">等待开始转换...</div>
            </div>
        </div>
        
        <!-- 下载标签页 -->
        <div id="tab-download" class="tab-content">
            <div class="card">
                <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;">
                    <span>📥 已转换文件</span>
                    <button class="btn btn-success" style="width:auto;padding:4px 12px;font-size:12px;" onclick="refreshDownloads()">🔄 刷新</button>
                </div>
                <div id="downloadList">
                    <div class="download-empty">暂无文件，转换完成后会显示在这里</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let files = [];
        let isConverting = false;
        let logLines = [];
        let currentTab = 'tab-convert';
        
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const uploadArea = document.getElementById('uploadArea');
        const formatSelect = document.getElementById('formatSelect');
        const compressCheck = document.getElementById('compressCheck');
        const convertBtn = document.getElementById('convertBtn');
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressFile = document.getElementById('progressFile');
        const progressContainer = document.getElementById('progressContainer');
        const logArea = document.getElementById('logArea');
        const fileCount = document.getElementById('fileCount');
        const statusText = document.getElementById('statusText');
        const statusDot = document.getElementById('statusDot');
        const convertStatus = document.getElementById('convertStatus');
        const downloadList = document.getElementById('downloadList');
        
        // 标签切换
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
            currentTab = tabId;
            if (tabId === 'tab-download') {
                refreshDownloads();
            }
        }
        
        // 上传
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            const newFiles = Array.from(e.target.files);
            newFiles.forEach(f => {
                if (!files.find(item => item.name === f.name)) {
                    files.push({ name: f.name, size: f.size, path: f.name });
                }
            });
            renderFileList();
            updateFileCount();
            fileInput.value = '';
        });
        
        uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.style.borderColor = '#e94560'; });
        uploadArea.addEventListener('dragleave', () => { uploadArea.style.borderColor = '#0f3460'; });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#0f3460';
            Array.from(e.dataTransfer.files).forEach(f => {
                if (!files.find(item => item.name === f.name)) {
                    files.push({ name: f.name, size: f.size, path: f.name });
                }
            });
            renderFileList();
            updateFileCount();
        });
        
        function renderFileList() {
            if (files.length === 0) {
                fileList.innerHTML = '<div class="empty-text">暂无文件，请上传</div>';
                return;
            }
            fileList.innerHTML = files.map((f, i) => `
                <div class="file-item">
                    <span class="name">🎬 ${f.name}</span>
                    <span class="size">${formatSize(f.size)}</span>
                    <span class="remove" onclick="removeFile(${i})">✕</span>
                </div>
            `).join('');
        }
        
        function removeFile(index) {
            files.splice(index, 1);
            renderFileList();
            updateFileCount();
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            if (bytes < 1024 * 1024 * 1024) return (bytes / (1024*1024)).toFixed(1) + ' MB';
            return (bytes / (1024*1024*1024)).toFixed(2) + ' GB';
        }
        
        function updateFileCount() {
            fileCount.textContent = `共 ${files.length} 个文件`;
        }
        
        function addLog(message) {
            logLines.push(message);
            if (logLines.length > 200) logLines = logLines.slice(-200);
            logArea.textContent = logLines.join('\\n');
            logArea.scrollTop = logArea.scrollHeight;
        }
        
        function startConvert() {
            if (isConverting) return;
            if (files.length === 0) { alert('请先添加要转换的文件'); return; }
            
            isConverting = true;
            convertBtn.disabled = true;
            convertBtn.textContent = '⏳ 转换中...';
            progressContainer.style.display = 'block';
            progressFill.style.width = '0%';
            progressPercent.textContent = '0%';
            logLines = [];
            addLog('🎬 开始批量转换...');
            addLog(`📁 共 ${files.length} 个文件`);
            
            const quality = document.querySelector('input[name="quality"]:checked').value;
            const format = formatSelect.value;
            const compress = compressCheck.checked;
            
            fetch('/api/convert', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ files: files.map(f => f.name), format, quality, compress })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    addLog('✅ 转换任务已提交');
                } else {
                    addLog('❌ 提交失败: ' + data.error);
                }
            })
            .catch(err => addLog('❌ 请求失败: ' + err.message));
        }
        
        function refreshDownloads() {
            fetch('/api/download_list')
                .then(r => r.json())
                .then(data => {
                    if (data.length === 0) {
                        downloadList.innerHTML = '<div class="download-empty">暂无文件，转换完成后会显示在这里</div>';
                        return;
                    }
                    downloadList.innerHTML = `
                        <div class="download-grid">
                            ${data.map(f => `
                                <div class="download-item">
                                    <span class="name" title="${f.name}">${f.name}</span>
                                    <span style="font-size:11px;color:#667788;margin-right:6px;">${formatSize(f.size)}</span>
                                    <div class="actions">
                                        <a href="/api/download/${encodeURIComponent(f.name)}" class="dl" download>⬇</a>
                                        <span class="del" onclick="deleteFile('${f.name}')">✕</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                })
                .catch(() => {});
        }
        
        function deleteFile(filename) {
            if (!confirm(`确定要删除 "${filename}" 吗？`)) return;
            fetch(`/api/delete/${encodeURIComponent(filename)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        refreshDownloads();
                    } else {
                        alert('删除失败: ' + data.error);
                    }
                });
        }
        
        // 状态轮询
        setInterval(() => {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    if (data.running) {
                        statusDot.className = 'status-dot yellow';
                        statusText.textContent = '转换中...';
                        convertStatus.textContent = `处理中 ${data.progress}%`;
                        progressFill.style.width = data.progress + '%';
                        progressPercent.textContent = data.progress + '%';
                        if (data.current_file) {
                            progressFile.textContent = data.current_file;
                        }
                    } else {
                        statusDot.className = 'status-dot green';
                        statusText.textContent = '就绪';
                        convertStatus.textContent = '空闲';
                        if (data.progress === 100) {
                            progressFill.style.width = '100%';
                            progressPercent.textContent = '100%';
                            progressFile.textContent = '完成!';
                            setTimeout(() => {
                                progressContainer.style.display = 'none';
                                convertBtn.disabled = false;
                                convertBtn.textContent = '🚀 开始批量转换';
                                isConverting = false;
                            }, 2000);
                        }
                    }
                })
                .catch(() => {});
        }, 1500);
        
        // 定期刷新下载列表
        setInterval(() => {
            if (currentTab === 'tab-download') {
                refreshDownloads();
            }
        }, 5000);
        
        // 初始
        addLog('🌐 Web 控制台已连接');
        addLog('💡 上传文件后点击「开始批量转换」');
    </script>
</body>
</html>
        '''


class FFmpegGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 批量视频转换压缩工具 v3.1")
        self.root.geometry("1000x850")
        self.root.minsize(900, 750)
        self.root.configure(bg='#1a1a2e')
        
        # 变量
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.input_files = []
        self.output_dir = tk.StringVar(value=os.path.expanduser("~/Videos"))
        self.quality = tk.StringVar(value="medium")
        self.output_format = tk.StringVar(value=".mp4")
        self.compress_mode = tk.BooleanVar(value=True)
        
        # 共享相关
        self.share_enabled = tk.BooleanVar(value=False)
        self.share_port = tk.StringVar(value="")
        self.share_server = None
        self.share_thread = None
        self.share_url = ""
        
        # 转换状态
        self.is_running = False
        self.current_progress = 0
        self.current_file = ""
        
        # 格式分类
        self.format_categories = {
            "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", 
                    ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".m2ts", ".divx", ".xvid"],
            "音频": [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg", ".wma", ".opus", 
                    ".amr", ".ac3", ".dts", ".aiff", ".alac", ".ape"],
            "设备": [".mp4_手机", ".mp4_平板", ".mp4_电视", ".mp4_网页", ".mp4_微信", 
                    ".mp4_抖音", ".mp4_B站", ".mp4_YouTube"],
            "压缩": [".mp4_高压缩", ".mp4_中压缩", ".mp4_低压缩", ".hevc_高压缩"]
        }
        
        self.selected_format = tk.StringVar(value=".mp4")
        self.process = None
        
        WebHandler.app = self
        
        self.create_widgets()
        self.check_ffmpeg()
        self.find_available_port()
    
    def get_ffmpeg_path(self):
        """获取 FFmpeg 路径"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            ffmpeg_paths = [
                os.path.join(exe_dir, 'ffmpeg.exe'),
                os.path.join(exe_dir, 'bin', 'ffmpeg.exe'),
                resource_path('ffmpeg.exe'),
            ]
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    return path
        
        if os.path.exists('ffmpeg.exe'):
            return 'ffmpeg.exe'
        
        if shutil.which('ffmpeg'):
            return 'ffmpeg'
        
        return 'ffmpeg'
    
    def check_ffmpeg(self):
        """检查 ffmpeg 是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                self.status_label.config(text="✅ FFmpeg 已就绪", fg='#00ff88')
                return True
        except:
            pass
        
        self.status_label.config(text="❌ FFmpeg 未找到，请安装", fg='#ff6b6b')
        return False
    
    def find_available_port(self):
        """查找可用端口"""
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
        """创建界面"""
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # 标题
        title = tk.Label(
            main_frame,
            text="🎬 批量视频转换压缩工具 v3.1",
            font=('微软雅黑', 20, 'bold'),
            fg='#e94560',
            bg='#1a1a2e'
        )
        title.pack(pady=(0, 5))
        
        subtitle = tk.Label(
            main_frame,
            text="支持 50+ 格式 · 批量转换 · Web远程控制 · 文件下载",
            font=('微软雅黑', 10),
            fg='#8899aa',
            bg='#1a1a2e'
        )
        subtitle.pack(pady=(0, 15))
        
        # 状态栏
        status_frame = tk.Frame(main_frame, bg='#1a1a2e')
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_label = tk.Label(
            status_frame,
            text="🔍 检测 FFmpeg...",
            font=('微软雅黑', 10),
            fg='#ffd93d',
            bg='#1a1a2e'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 文件列表
        file_frame = tk.Frame(main_frame, bg='#1a1a2e')
        file_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        file_header = tk.Frame(file_frame, bg='#1a1a2e')
        file_header.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(
            file_header,
            text="📁 文件列表:",
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT)
        
        tk.Label(
            file_header,
            textvariable=self.file_count_label,
            font=('微软雅黑', 9),
            fg='#8899aa',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        btn_group = tk.Frame(file_header, bg='#1a1a2e')
        btn_group.pack(side=tk.RIGHT)
        
        for text, cmd in [("➕ 添加文件", self.add_files), 
                          ("📂 添加文件夹", self.add_folder),
                          ("🗑️ 清空列表", self.clear_files)]:
            tk.Button(
                btn_group,
                text=text,
                font=('微软雅黑', 9),
                bg='#0f3460',
                fg='white',
                relief=tk.FLAT,
                padx=15,
                pady=5,
                cursor='hand2',
                command=cmd
            ).pack(side=tk.LEFT, padx=(0, 5))
        
        list_frame = tk.Frame(file_frame, bg='#0a0a1a')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 9),
            bg='#0a0a1a',
            fg='#00ff88',
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            highlightthickness=0,
            height=8
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        self.create_context_menu()
        
        # 设置区域
        settings_frame = tk.Frame(main_frame, bg='#1a1a2e')
        settings_frame.pack(fill=tk.X, pady=10)
        
        # 第一行：格式 + 质量
        row1 = tk.Frame(settings_frame, bg='#1a1a2e')
        row1.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row1,
            text="📝 输出格式:",
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_combo = ttk.Combobox(
            row1,
            textvariable=self.selected_format,
            values=self.format_categories["视频"],
            font=('微软雅黑', 9),
            state='readonly',
            width=15
        )
        self.format_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        for cat in ["视频", "音频", "设备", "压缩"]:
            tk.Button(
                row1,
                text=cat,
                font=('微软雅黑', 8),
                bg='#0f3460',
                fg='#8899aa',
                relief=tk.FLAT,
                padx=10,
                pady=3,
                cursor='hand2',
                command=lambda c=cat: self.switch_category(c)
            ).pack(side=tk.LEFT, padx=2)
        
        tk.Label(
            row1,
            text="⚙️ 质量:",
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT, padx=(20, 10))
        
        for text, value in [("极速", "low"), ("平衡", "medium"), ("极致", "high")]:
            tk.Radiobutton(
                row1,
                text=text,
                variable=self.quality,
                value=value,
                font=('微软雅黑', 9),
                fg='#e0e0e0',
                bg='#1a1a2e',
                selectcolor='#1a1a2e',
                relief=tk.FLAT,
                cursor='hand2'
            ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 第二行：输出目录 + 压缩
        row2 = tk.Frame(settings_frame, bg='#1a1a2e')
        row2.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row2,
            text="💾 输出目录:",
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_entry = tk.Entry(
            row2,
            textvariable=self.output_dir,
            font=('微软雅黑', 9),
            bg='#16213e',
            fg='#e0e0e0',
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor='#e94560',
            highlightbackground='#0f3460',
            width=30
        )
        self.output_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        
        tk.Button(
            row2,
            text="浏览",
            font=('微软雅黑', 9),
            bg='#0f3460',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.select_output_dir
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Checkbutton(
            row2,
            text="📦 压缩视频",
            variable=self.compress_mode,
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e',
            selectcolor='#1a1a2e',
            cursor='hand2'
        ).pack(side=tk.LEFT)
        
        # 第三行：局域网共享
        row3 = tk.Frame(settings_frame, bg='#1a1a2e')
        row3.pack(fill=tk.X, pady=5)
        
        self.share_check = tk.Checkbutton(
            row3,
            text="🌐 开启Web远程控制",
            variable=self.share_enabled,
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e',
            selectcolor='#1a1a2e',
            cursor='hand2',
            command=self.toggle_share
        )
        self.share_check.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            row3,
            text="端口:",
            font=('微软雅黑', 9),
            fg='#8899aa',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.port_entry = tk.Entry(
            row3,
            textvariable=self.share_port,
            font=('微软雅黑', 9),
            bg='#16213e',
            fg='#e0e0e0',
            relief=tk.FLAT,
            width=8,
            highlightthickness=1,
            highlightcolor='#e94560',
            highlightbackground='#0f3460',
            state='readonly'
        )
        self.port_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        self.share_status_label = tk.Label(
            row3,
            text="⏸️ 已关闭",
            font=('微软雅黑', 9),
            fg='#8899aa',
            bg='#1a1a2e'
        )
        self.share_status_label.pack(side=tk.LEFT)
        
        self.share_url_label = tk.Label(
            row3,
            text="",
            font=('微软雅黑', 9),
            fg='#00ff88',
            bg='#1a1a2e',
            cursor='hand2'
        )
        self.share_url_label.pack(side=tk.LEFT, padx=(10, 0))
        self.share_url_label.bind("<Button-1>", lambda e: self.open_share_url())
        
        # 转换按钮
        btn_frame = tk.Frame(main_frame, bg='#1a1a2e')
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.convert_btn = tk.Button(
            btn_frame,
            text="🚀 开始批量转换",
            font=('微软雅黑', 13, 'bold'),
            bg='#e94560',
            fg='white',
            relief=tk.FLAT,
            pady=14,
            cursor='hand2',
            command=self.convert_files
        )
        self.convert_btn.pack(fill=tk.X)
        
        # 进度
        progress_frame = tk.Frame(main_frame, bg='#1a1a2e')
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X)
        
        progress_info = tk.Frame(progress_frame, bg='#1a1a2e')
        progress_info.pack(fill=tk.X, pady=3)
        
        self.progress_label = tk.Label(
            progress_info, text="0%", font=('微软雅黑', 9),
            fg='#00ff88', bg='#1a1a2e'
        )
        self.progress_label.pack(side=tk.LEFT)
        
        self.file_progress_label = tk.Label(
            progress_info, text="等待开始...",
            font=('微软雅黑', 9), fg='#8899aa', bg='#1a1a2e'
        )
        self.file_progress_label.pack(side=tk.RIGHT)
        
        # 日志
        log_frame = tk.Frame(main_frame, bg='#1a1a2e')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        log_header = tk.Frame(log_frame, bg='#1a1a2e')
        log_header.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(
            log_header,
            text="📝 转换日志:",
            font=('微软雅黑', 10, 'bold'),
            fg='#e0e0e0',
            bg='#1a1a2e'
        ).pack(side=tk.LEFT)
        
        tk.Button(
            log_header,
            text="清空日志",
            font=('微软雅黑', 8),
            bg='#0f3460',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=3,
            cursor='hand2',
            command=self.clear_log
        ).pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Consolas', 9),
            bg='#0a0a1a',
            fg='#00ff88',
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor='#0f3460',
            highlightbackground='#0f3460',
            height=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state='disabled')
        
        # 初始化
        self.file_count_label = tk.StringVar(value="共 0 个文件")
        self.update_file_count()
        
        self.log("🎯 批量视频转换压缩工具 v3.1")
        self.log("📌 支持 50+ 种格式转换")
        self.log("💡 添加文件后点击「开始批量转换」")
        self.log(f"🌐 Web远程控制端口: {self.share_port.get()} (默认关闭)")
    
    def create_context_menu(self):
        """右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='#1a1a2e', fg='#e0e0e0')
        self.context_menu.add_command(label="移除选中", command=self.remove_selected)
        self.context_menu.add_command(label="清空列表", command=self.clear_files)
        self.file_listbox.bind("<Button-3>", lambda e: self.context_menu.post(e.x_root, e.y_root))
    
    def switch_category(self, category):
        """切换格式分类"""
        self.format_combo['values'] = self.format_categories[category]
        if self.format_categories[category]:
            self.selected_format.set(self.format_categories[category][0])
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.3gp *.ogv *.ts")]
        )
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
        self.update_file_count()
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            video_exts = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
                         '.mpg', '.mpeg', '.3gp', '.ogv', '.ts', '.m2ts'}
            count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in video_exts:
                        file_path = os.path.join(root, file)
                        if file_path not in self.input_files:
                            self.input_files.append(file_path)
                            self.file_listbox.insert(tk.END, file)
                            count += 1
            self.update_file_count()
            self.log(f"📂 从文件夹添加了 {count} 个文件")
    
    def remove_selected(self):
        selected = self.file_listbox.curselection()
        for index in reversed(selected):
            del self.input_files[index]
            self.file_listbox.delete(index)
        self.update_file_count()
    
    def clear_files(self):
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.update_file_count()
    
    def update_file_count(self):
        self.file_count_label.set(f"共 {len(self.input_files)} 个文件")
    
    def select_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def toggle_share(self):
        if self.share_enabled.get():
            self.start_share()
        else:
            self.stop_share()
    
    def start_share(self):
        try:
            port = int(self.share_port.get())
            if port == 0:
                port = self.find_available_port()
                self.share_port.set(str(port))
            
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            
            share_dir = self.output_dir.get()
            if not os.path.exists(share_dir):
                os.makedirs(share_dir)
            os.chdir(share_dir)
            
            self.share_server = socketserver.TCPServer(("", port), WebHandler)
            self.share_server.allow_reuse_address = True
            
            self.share_url = f"http://{ip}:{port}"
            self.share_status_label.config(text="🟢 运行中", fg='#00ff88')
            self.share_url_label.config(text=f"🌐 {self.share_url}")
            
            self.log(f"🌐 Web远程控制已启动: {self.share_url}")
            self.log(f"📂 共享目录: {share_dir}")
            self.log("📱 手机/平板在浏览器打开上述地址即可控制")
            self.log("📥 转换完成后可在「下载」标签页下载文件")
            
            self.share_thread = threading.Thread(target=self._run_share_server)
            self.share_thread.daemon = True
            self.share_thread.start()
            
        except Exception as e:
            self.log(f"❌ 启动Web服务失败: {str(e)}")
            self.share_enabled.set(False)
            self.share_status_label.config(text="❌ 启动失败", fg='#ff6b6b')
            messagebox.showerror("错误", f"启动Web服务失败:\n{str(e)}")
    
    def _run_share_server(self):
        try:
            self.share_server.serve_forever()
        except:
            pass
    
    def stop_share(self):
        try:
            if self.share_server:
                self.share_server.shutdown()
                self.share_server.server_close()
                self.share_server = None
            self.share_status_label.config(text="⏸️ 已关闭", fg='#8899aa')
            self.share_url_label.config(text="")
            self.log("🌐 Web远程控制已关闭")
        except Exception as e:
            self.log(f"⚠️ 关闭服务出错: {str(e)}")
    
    def open_share_url(self):
        if self.share_url:
            webbrowser.open(self.share_url)
    
    def get_progress(self):
        return self.current_progress
    
    def get_current_file(self):
        return self.current_file
    
    def start_web_convert(self, data):
        self.log(f"🌐 收到Web转换请求")
        self.convert_files()
    
    def get_format_params(self, format_str):
        params = {
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
            ".divx": {"vcodec": "mpeg4", "acodec": "mp3", "ext": ".divx"},
            ".xvid": {"vcodec": "libxvid", "acodec": "mp3", "ext": ".xvid"},
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
            ".mp4_B站": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "1920x1080", "bitrate": "2000k"},
            ".mp4_YouTube": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "scale": "1920x1080", "bitrate": "4000k"},
            ".mp4_高压缩": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "crf": "28"},
            ".mp4_中压缩": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "crf": "23"},
            ".mp4_低压缩": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4", "crf": "18"},
            ".hevc_高压缩": {"vcodec": "libx265", "acodec": "aac", "ext": ".mp4", "crf": "28"},
        }
        return params.get(format_str, params[".mp4"])
    
    def convert_files(self):
        if not self.input_files:
            messagebox.showerror("错误", "请先添加要转换的文件")
            return
        
        if not os.path.exists(self.output_dir.get()):
            try:
                os.makedirs(self.output_dir.get())
            except:
                messagebox.showerror("错误", "无法创建输出目录")
                return
        
        if not self.check_ffmpeg():
            messagebox.showerror("错误", "FFmpeg 未找到，请安装后重试")
            return
        
        if self.is_running:
            return
        
        self.convert_btn.config(state='disabled', text='⏳ 转换中...')
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")
        self.is_running = True
        self.current_progress = 0
        self.current_file_index = 0
        self.total_files = len(self.input_files)
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        thread = threading.Thread(target=self._convert_thread)
        thread.daemon = True
        thread.start()
    
    def _convert_thread(self):
        quality_settings = {"low": "28", "medium": "23", "high": "18"}
        quality_value = quality_settings.get(self.quality.get(), "23")
        total = len(self.input_files)
        
        for idx, input_file in enumerate(self.input_files):
            self.current_file_index = idx
            file_name = os.path.basename(input_file)
            self.current_file = file_name
            
            progress = int((idx / total) * 100)
            self.current_progress = progress
            self.root.after(0, lambda p=progress: self.progress_bar.config(value=p))
            self.root.after(0, lambda p=progress: self.progress_label.config(text=f"{p}%"))
            self.root.after(0, lambda i=idx, t=total, n=file_name: 
                          self.file_progress_label.config(text=f"处理: {i+1}/{t} - {n}"))
            
            self.log(f"\n🎬 [{idx+1}/{total}] 开始转换: {file_name}")
            
            format_str = self.selected_format.get()
            params = self.get_format_params(format_str)
            
            base_name = os.path.splitext(file_name)[0]
            output_file = os.path.join(
                self.output_dir.get(),
                f"{base_name}_转换{params['ext']}"
            )
            
            cmd = [self.ffmpeg_path, "-i", input_file]
            
            if params.get("vcodec"):
                cmd.extend(["-c:v", params["vcodec"]])
                
                if format_str in [".mp4_高压缩", ".hevc_高压缩"]:
                    cmd.extend(["-crf", "28"])
                elif format_str in [".mp4_中压缩"]:
                    cmd.extend(["-crf", "23"])
                elif format_str in [".mp4_低压缩"]:
                    cmd.extend(["-crf", "18"])
                elif self.compress_mode.get():
                    cmd.extend(["-crf", quality_value])
                
                if params.get("preset"):
                    cmd.extend(["-preset", params["preset"]])
                if params.get("scale"):
                    cmd.extend(["-vf", f"scale={params['scale']}"])
                if params.get("bitrate"):
                    cmd.extend(["-b:v", params["bitrate"]])
                if params.get("fps"):
                    cmd.extend(["-r", params["fps"]])
            
            if params.get("acodec"):
                cmd.extend(["-c:a", params["acodec"]])
            
            cmd.extend(["-y", output_file])
            
            self.log(f"📤 输出: {output_file}")
            
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                while True:
                    output = self.process.stderr.readline()
                    if not output:
                        break
                    if "frame=" in output or "size=" in output or "time=" in output:
                        self.log(output.strip())
                
                self.process.wait()
                
                if self.process.returncode == 0:
                    size = self.get_file_size(output_file)
                    self.log(f"✅ 转换成功! 大小: {size}")
                else:
                    self.log(f"❌ 转换失败: {file_name}")
                    
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
        
        self.root.after(0, self.conversion_complete)
    
    def conversion_complete(self):
        self.progress_bar['value'] = 100
        self.progress_label.config(text="100%")
        self.current_progress = 100
        self.is_running = False
        self.convert_btn.config(state='normal', text='🚀 开始批量转换')
        self.file_progress_label.config(text="完成!")
        self.current_file = ""
        
        self.log("\n🎉 所有文件转换完成！")
        self.log(f"📊 共处理 {len(self.input_files)} 个文件")
        self.log("📥 可在Web界面的「下载」标签页下载文件")
        
        messagebox.showinfo(
            "🎉 转换完成",
            f"批量转换完成！\n\n"
            f"📊 处理文件: {len(self.input_files)} 个\n"
            f"💾 输出目录: {self.output_dir.get()}\n\n"
            f"📥 Web界面可下载转换后的文件"
        )
    
    def get_file_size(self, file_path):
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.2f} GB"
        except:
            return "未知"


def main():
    root = tk.Tk()
    app = FFmpegGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()