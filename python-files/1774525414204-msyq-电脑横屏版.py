#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网文件互传工具 - 增强版
新增功能：上传/下载实时进度条显示、左右分栏布局
"""

import http.server
import socketserver
import socket
import os
import sys
import re
import urllib.parse
import io

# 尝试导入二维码库
try:
    import qrcode
    from qrcode.image import svg
    QR_SUPPORT = True
except ImportError:
    QR_SUPPORT = False
    print("⚠️ 警示: 未检测到 'qrcode' 库，网页将不显示二维码。")
    print("   请运行 'pip install qrcode' 安装以启用此功能。")

# ================== 配置区 ==================
PORT = 8000
WORK_DIR = os.getcwd()
# ===========================================

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

class FileTransferHandler(http.server.SimpleHTTPRequestHandler):
    """文件传输HTTP处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self._generate_html_page().encode('utf-8'))
        else:
            # 其他请求（文件下载）交给父类处理
            super().do_GET()
    
    def do_POST(self):
        """处理文件上传"""
        try:
            content_length = int(self.headers['Content-Length'])
            content_type = self.headers['Content-Type']
            
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Bad Request")
                return
            
            boundary = content_type.split("=")[1].encode()
            remaining_bytes = content_length
            
            # 优化：使用 bytearray 避免大文件拼接时的内存复制开销
            body = bytearray()
            
            # 读取上传数据
            while remaining_bytes > 0:
                chunk = self.rfile.read(min(4096, remaining_bytes))
                if not chunk: break
                body.extend(chunk)
                remaining_bytes -= len(chunk)
            
            # 解析文件数据
            parts = body.split(b'\r\n\r\n', 1)
            if len(parts) < 2:
                self.send_error(400, "Invalid format")
                return
            
            header_part = parts[0]
            file_data_with_end = parts[1]
            
            # 提取文件名
            header_str = header_part.decode('utf-8', errors='ignore')
            filename_match = re.search(r'filename="(.+?)"', header_str)
            if not filename_match:
                self.send_error(400, "Filename not found")
                return
            
            filename = filename_match.group(1)
            
            # 去除末尾的boundary
            end_boundary = b'\r\n--' + boundary + b'--'
            if file_data_with_end.endswith(end_boundary):
                file_data = file_data_with_end[:-len(end_boundary)]
            else:
                file_data = file_data_with_end
            
            # 安全处理：去除路径，只保留文件名
            filename = os.path.basename(filename)
            filepath = os.path.join(WORK_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            print(f"✅ 文件已接收: {filename} ({len(file_data)} bytes)")
            
            # 返回JSON响应（便于前端AJAX处理）
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = f'{{"status": "success", "filename": "{filename}"}}'
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            print(f"❌ 上传错误: {e}")
            self.send_error(500, f"Upload failed: {str(e)}")
    
    def _generate_html_page(self):
        """生成主页HTML"""
        local_ip = get_local_ip()
        url = f"http://{local_ip}:{PORT}"
        
        # 生成二维码SVG
        qr_svg_html = ""
        if QR_SUPPORT:
            try:
                img = qrcode.make(url, image_factory=svg.SvgPathImage)
                stream = io.BytesIO()
                img.save(stream)
                svg_str = stream.getvalue().decode('utf-8')
                qr_svg_html = f"""
                <div class="qr-section">
                    <h3>📱 扫码访问</h3>
                    <div class="qr-box">{svg_str}</div>
                    <p class="url-text">{url}</p>
                </div>
                """
            except Exception as e:
                print(f"生成二维码失败: {e}")
        
        # 获取文件列表
        files = []
        try:
            for item in os.listdir(WORK_DIR):
                item_path = os.path.join(WORK_DIR, item)
                if os.path.isfile(item_path):
                    files.append(item)
        except:
            pass
        
        file_list_html = ""
        for name in files:
            encoded_name = urllib.parse.quote(name)
            file_list_html += f'''
            <div class="file-item" id="file-{hash(name)}">
                <div class="file-info">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{name}</span>
                </div>
                <div class="action-area">
                    <div class="progress-container" id="dl-progress-{hash(name)}">
                        <div class="progress-bar"></div>
                        <span class="progress-text">0%</span>
                    </div>
                    <button class="btn-download" onclick="downloadFile('{encoded_name}', '{name}', '{hash(name)}')">下载</button>
                </div>
            </div>
            '''
        
        if not files:
            file_list_html = '<p class="empty">当前目录暂无文件</p>'

        return f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>局域网文件传输</title>
            <style>
                * {{ box-sizing: border-box; }}
                
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                    margin: 0; padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                
                /* 主容器 */
                .main-container {{ 
                    max-width: 1400px; 
                    margin: 0 auto; 
                }}
                
                /* 标题区域 */
                .header {{ 
                    text-align: center; 
                    padding: 30px 20px; 
                    margin-bottom: 25px;
                }}
                .header h1 {{ color: white; margin: 0 0 10px 0; font-size: 32px; text-shadow: 0 2px 10px rgba(0,0,0,0.2); }}
                .header .subtitle {{ color: rgba(255,255,255,0.9); margin: 0; font-size: 15px; }}
                
                /* 左右分栏容器 */
                .content-wrapper {{ 
                    display: flex; 
                    gap: 25px; 
                    align-items: flex-start;
                }}
                
                /* 左侧栏 */
                .left-panel {{ 
                    flex: 0 0 380px; 
                    display: flex; 
                    flex-direction: column; 
                    gap: 20px;
                }}
                
                /* 右侧栏 */
                .right-panel {{ 
                    flex: 1; 
                    min-width: 0;
                }}
                
                /* 卡片通用样式 */
                .card {{ 
                    background: white; 
                    border-radius: 20px; 
                    padding: 25px; 
                    box-shadow: 0 10px 40px rgba(0,0,0,0.15); 
                }}
                
                h2 {{ font-size: 18px; margin: 0 0 20px 0; color: #333; display: flex; align-items: center; gap: 8px; }}
                
                /* 二维码区域 */
                .qr-section {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 16px; }}
                .qr-section h3 {{ margin: 0 0 15px 0; font-size: 16px; color: #555; }}
                .qr-box {{ background: white; display: inline-block; padding: 15px; border-radius: 12px; border: 1px solid #eee; }}
                .qr-box svg {{ width: 140px; height: 140px; }}
                .url-text {{ font-family: monospace; color: #666; font-size: 12px; margin-top: 12px; background: white; padding: 6px 12px; border-radius: 6px; display: inline-block; }}
                
                /* 上传区域 */
                .upload-area {{ 
                    border: 2px dashed #d1d5db; 
                    padding: 35px 20px; 
                    text-align: center; 
                    border-radius: 16px; 
                    position: relative; 
                    cursor: pointer; 
                    transition: all 0.3s;
                    background: #fafbfc;
                }}
                .upload-area:hover {{ border-color: #007aff; background: #f0f7ff; }}
                .upload-icon {{ font-size: 48px; margin-bottom: 10px; display: block; }}
                .upload-text {{ color: #666; font-size: 14px; }}
                .btn {{ 
                    background: linear-gradient(135deg, #007aff 0%, #5856d6 100%); 
                    color: white; 
                    border: none; 
                    padding: 14px; 
                    border-radius: 12px; 
                    font-size: 16px; 
                    font-weight: 600; 
                    cursor: pointer; 
                    margin-top: 20px; 
                    width: 100%;
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                .btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,122,255,0.3); }}
                .btn:disabled {{ background: #ccc; cursor: not-allowed; transform: none; box-shadow: none; }}
                
                /* 文件列表区域 */
                .file-list-header {{ 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center;
                    margin-bottom: 15px;
                }}
                .file-count {{ 
                    background: #007aff; 
                    color: white; 
                    padding: 4px 12px; 
                    border-radius: 20px; 
                    font-size: 13px; 
                    font-weight: 600;
                }}
                
                /* 文件列表滚动区域 */
                .file-list-container {{ 
                    max-height: calc(100vh - 300px); 
                    overflow-y: auto; 
                    padding-right: 5px;
                }}
                .file-list-container::-webkit-scrollbar {{ width: 6px; }}
                .file-list-container::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 10px; }}
                .file-list-container::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 10px; }}
                .file-list-container::-webkit-scrollbar-thumb:hover {{ background: #aaa; }}
                
                .file-item {{ 
                    padding: 15px; 
                    background: #f8f9fa; 
                    margin-bottom: 10px; 
                    border-radius: 12px; 
                    transition: all 0.2s;
                    border: 1px solid transparent;
                }}
                .file-item:hover {{ background: #f0f4f8; border-color: #e0e5eb; }}
                
                .file-info {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
                .file-icon {{ font-size: 20px; }}
                .file-name {{ 
                    font-size: 14px; 
                    color: #333; 
                    overflow: hidden; 
                    text-overflow: ellipsis; 
                    white-space: nowrap; 
                    flex: 1; 
                    font-weight: 500;
                }}
                
                .action-area {{ display: flex; align-items: center; gap: 10px; }}
                
                .btn-download {{ 
                    background: linear-gradient(135deg, #34c759 0%, #30d158 100%); 
                    color: white; 
                    padding: 8px 20px; 
                    border-radius: 8px; 
                    font-size: 13px; 
                    white-space: nowrap; 
                    border: none; 
                    cursor: pointer; 
                    min-width: 70px; 
                    text-align: center;
                    font-weight: 600;
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                .btn-download:hover {{ transform: translateY(-2px); box-shadow: 0 3px 15px rgba(52,199,89,0.3); }}
                
                /* 进度条 */
                .progress-container {{ 
                    display: none; 
                    height: 28px; 
                    background: #e9ecef; 
                    border-radius: 14px; 
                    overflow: hidden; 
                    position: relative; 
                    flex: 1;
                }}
                .progress-bar {{ 
                    height: 100%; 
                    background: linear-gradient(90deg, #007aff, #34c759); 
                    width: 0%; 
                    transition: width 0.3s ease; 
                }}
                .progress-text {{ 
                    position: absolute; 
                    width: 100%; 
                    text-align: center; 
                    top: 5px; 
                    font-size: 12px; 
                    color: #333; 
                    font-weight: bold; 
                }}
                
                .empty {{ text-align: center; color: #999; padding: 40px 20px; font-size: 14px; }}
                
                /* 响应式布局 - 小屏幕时变为上下布局 */
                @media (max-width: 900px) {{
                    .content-wrapper {{ flex-direction: column; }}
                    .left-panel {{ flex: none; width: 100%; }}
                    .file-list-container {{ max-height: 400px; }}
                }}
            </style>
        </head>
        <body>
            <div class="main-container">
                <!-- 标题 -->
                <div class="header">
                    <h1>📁 局域网文件互传</h1>
                    <p class="subtitle">电脑与手机之间快速传输文件</p>
                </div>
                
                <!-- 左右分栏 -->
                <div class="content-wrapper">
                    <!-- 左侧：上传和二维码 -->
                    <div class="left-panel">
                        {qr_svg_html}
                        
                        <div class="card">
                            <h2>⬆️ 上传文件</h2>
                            <form id="uploadForm">
                                <div class="upload-area" id="dropArea">
                                    <span class="upload-icon">📂</span>
                                    <div class="upload-text" id="fileLabel">点击选择或拖拽文件</div>
                                    <input type="file" name="file" id="fileInput" style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;">
                                </div>
                                <!-- 上传进度条 -->
                                <div class="progress-container" id="uploadProgress" style="margin-top: 15px;">
                                    <div class="progress-bar" id="uploadBar"></div>
                                    <span class="progress-text" id="uploadText">0%</span>
                                </div>
                                <button type="submit" class="btn" id="uploadBtn">开始上传</button>
                            </form>
                        </div>
                    </div>
                    
                    <!-- 右侧：文件列表 -->
                    <div class="right-panel">
                        <div class="card">
                            <div class="file-list-header">
                                <h2>⬇️ 文件列表</h2>
                                <span class="file-count">{len(files)} 个文件</span>
                            </div>
                            <div class="file-list-container">
                                {file_list_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                const fileInput = document.getElementById('fileInput');
                const fileLabel = document.getElementById('fileLabel');
                const uploadForm = document.getElementById('uploadForm');
                const uploadProgress = document.getElementById('uploadProgress');
                const uploadBar = document.getElementById('uploadBar');
                const uploadText = document.getElementById('uploadText');
                const uploadBtn = document.getElementById('uploadBtn');
                
                // 文件选择显示名称
                fileInput.addEventListener('change', function() {{
                    if (this.files[0]) {{
                        fileLabel.innerHTML = '📄 ' + this.files[0].name;
                        fileLabel.style.color = '#007aff';
                        fileLabel.style.fontWeight = '600';
                    }}
                }});

                // 拖拽上传支持
                const dropArea = document.getElementById('dropArea');
                
                dropArea.addEventListener('dragover', function(e) {{
                    e.preventDefault();
                    dropArea.style.borderColor = '#007aff';
                    dropArea.style.background = '#f0f7ff';
                }});
                
                dropArea.addEventListener('dragleave', function(e) {{
                    e.preventDefault();
                    dropArea.style.borderColor = '#d1d5db';
                    dropArea.style.background = '#fafbfc';
                }});
                
                dropArea.addEventListener('drop', function(e) {{
                    e.preventDefault();
                    dropArea.style.borderColor = '#d1d5db';
                    dropArea.style.background = '#fafbfc';
                    
                    if (e.dataTransfer.files.length > 0) {{
                        fileInput.files = e.dataTransfer.files;
                        const event = new Event('change');
                        fileInput.dispatchEvent(event);
                    }}
                }});

                // 上传逻辑 (AJAX)
                uploadForm.addEventListener('submit', function(e) {{
                    e.preventDefault();
                    if (!fileInput.files[0]) {{
                        alert("请先选择一个文件");
                        return;
                    }}
                    
                    const file = fileInput.files[0];
                    const xhr = new XMLHttpRequest();
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    // 显示进度条
                    uploadProgress.style.display = 'block';
                    uploadBtn.disabled = true;
                    uploadBtn.innerText = '上传中...';
                    
                    xhr.upload.onprogress = function(e) {{
                        if (e.lengthComputable) {{
                            const percent = Math.round((e.loaded / e.total) * 100);
                            uploadBar.style.width = percent + '%';
                            uploadText.innerText = percent + '%';
                        }}
                    }};
                    
                    xhr.onload = function() {{
                        if (xhr.status === 200) {{
                            uploadBar.style.width = '100%';
                            uploadText.innerText = '✓ 完成!';
                            setTimeout(() => {{ location.reload(); }}, 800);
                        }} else {{
                            alert('上传失败: ' + xhr.statusText);
                            resetUploadUI();
                        }}
                    }};
                    
                    xhr.onerror = function() {{
                        alert('网络错误');
                        resetUploadUI();
                    }};
                    
                    xhr.open('POST', '/');
                    xhr.send(formData);
                }});
                
                function resetUploadUI() {{
                    uploadProgress.style.display = 'none';
                    uploadBtn.disabled = false;
                    uploadBtn.innerText = '开始上传';
                }}

                // 下载逻辑 (AJAX Blob)
                function downloadFile(url, filename, id) {{
                    const container = document.getElementById('dl-progress-' + id);
                    const bar = container.querySelector('.progress-bar');
                    const text = container.querySelector('.progress-text');
                    const btn = container.parentElement.querySelector('.btn-download');
                    
                    const xhr = new XMLHttpRequest();
                    xhr.open('GET', url, true);
                    xhr.responseType = 'blob';
                    
                    container.style.display = 'block';
                    btn.style.display = 'none';
                    
                    xhr.onprogress = function(e) {{
                        if (e.lengthComputable) {{
                            const percent = Math.round((e.loaded / e.total) * 100);
                            bar.style.width = percent + '%';
                            text.innerText = percent + '%';
                        }}
                    }};
                    
                    xhr.onload = function() {{
                        if (this.status === 200) {{
                            const blob = this.response;
                            const link = document.createElement('a');
                            link.href = window.URL.createObjectURL(blob);
                            link.download = filename;
                            link.click();
                            
                            text.innerText = '✓ 完成!';
                            setTimeout(() => {{ 
                                container.style.display = 'none';
                                btn.style.display = 'block';
                                btn.innerText = '下载';
                            }}, 1500);
                        }}
                    }};
                    
                    xhr.send();
                }}
            </script>
        </body>
        </html>
        '''

    def log_message(self, format, *args):
        """静默日志，避免控制台刷屏"""
        if '/favicon.ico' not in args[0]:
            print(f"[请求] {args[0]}")


def print_banner(ip, port):
    url = f"http://{ip}:{port}"
    print("\n" + "="*60)
    print(f"🚀 服务已启动！")
    print(f"📂 共享目录: {WORK_DIR}")
    print("-"*60)
    print(f"📱 请在手机或电脑浏览器打开:")
    print(f"   {url}")
    print("-"*60)
    print("💡 提示: 按 Ctrl + C 停止服务")
    print("="*60 + "\n")


if __name__ == "__main__":
    os.chdir(WORK_DIR)
    
    try:
        with socketserver.TCPServer(("", PORT), FileTransferHandler) as httpd:
            httpd.allow_reuse_address = True
            local_ip = get_local_ip()
            print_banner(local_ip, PORT)
            httpd.serve_forever()
            
    except OSError as e:
        print(f"❌ 启动失败: 端口 {PORT} 可能被占用，请修改代码中的 PORT 变量。")
    except KeyboardInterrupt:
        print("\n🛑 服务已停止。")
