#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网文件互传工具 - 增强版
新增功能：上传/下载实时进度条显示
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
                    <h3>📱 手机扫码访问</h3>
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
            # 修改：增加下载按钮的调用逻辑
            file_list_html += f'''
            <div class="file-item" id="file-{hash(name)}">
                <span class="file-name">{name}</span>
                <div class="action-area">
                    <div class="progress-container" id="dl-progress-{hash(name)}">
                        <div class="progress-bar" style="width: 0%"></div>
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
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                       max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f7; }}
                .container {{ background: white; border-radius: 20px; padding: 30px; 
                             box-shadow: 0 10px 40px rgba(0,0,0,0.1); margin-top: 20px; }}
                h1 {{ text-align: center; color: #333; margin: 0 0 10px 0; font-size: 26px; }}
                .subtitle {{ text-align: center; color: #999; margin-bottom: 30px; font-size: 14px; }}
                
                /* 通用进度条样式 */
                .progress-container {{ 
                    display: none; height: 24px; background: #e9ecef; border-radius: 12px; 
                    overflow: hidden; position: relative; margin-right: 10px; flex-grow: 1; 
                }}
                .progress-bar {{ height: 100%; background: linear-gradient(90deg, #007aff, #34c759); 
                               width: 0%; transition: width 0.2s; }}
                .progress-text {{ 
                    position: absolute; width: 100%; text-align: center; 
                    top: 2px; font-size: 12px; color: #333; font-weight: bold; 
                }}
                
                /* 上传区域 */
                .upload-card {{ background: #f8f9fa; padding: 25px; border-radius: 16px; margin-bottom: 25px; }}
                h2 {{ font-size: 18px; margin: 0 0 15px 0; color: #333; }}
                .upload-area {{ border: 2px dashed #d1d5db; padding: 40px 20px; text-align: center; 
                              border-radius: 12px; position: relative; cursor: pointer; transition: all 0.3s; }}
                .upload-area:hover {{ border-color: #007aff; background: #f0f7ff; }}
                .upload-icon {{ font-size: 40px; margin-bottom: 10px; }}
                .btn {{ background: #007aff; color: white; border: none; padding: 12px; 
                       border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 15px; width: 100%; }}
                .btn:disabled {{ background: #ccc; cursor: not-allowed; }}
                
                /* 二维码区域 */
                .qr-section {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 16px; margin-bottom: 25px; }}
                .qr-box {{ background: white; display: inline-block; padding: 15px; border-radius: 8px; border: 1px solid #eee; }}
                .qr-box svg {{ width: 160px; height: 160px; }}
                .url-text {{ font-family: monospace; color: #666; font-size: 13px; margin-top: 10px; background: white; padding: 5px 10px; border-radius: 4px; }}
                
                /* 文件列表 */
                .file-item {{ display: flex; flex-direction: column; padding: 12px; 
                             background: #f8f9fa; margin-bottom: 8px; border-radius: 8px; }}
                .file-info {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }}
                .file-name {{ font-size: 14px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 10px; }}
                .action-area {{ display: flex; align-items: center; width: 100%; margin-top: 5px; }}
                .btn-download {{ 
                    text-decoration: none; background: #34c759; color: white; padding: 6px 16px; 
                    border-radius: 6px; font-size: 13px; white-space: nowrap; border: none; cursor: pointer; min-width: 60px; text-align: center;
                }}
                .empty {{ text-align: center; color: #999; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 局域网文件互传</h1>
                <p class="subtitle">电脑与手机之间快速传输文件</p>
                
                {qr_svg_html}

                <div class="upload-card">
                    <h2>⬆️ 上传文件到电脑</h2>
                    <form id="uploadForm">
                        <div class="upload-area" id="dropArea">
                            <div class="upload-icon">📂</div>
                            <div id="fileLabel">点击选择或拖拽文件</div>
                            <input type="file" name="file" id="fileInput" style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;">
                        </div>
                        <!-- 上传进度条 -->
                        <div class="progress-container" id="uploadProgress" style="margin-top: 15px; display: none;">
                            <div class="progress-bar" id="uploadBar"></div>
                            <span class="progress-text" id="uploadText">0%</span>
                        </div>
                        <button type="submit" class="btn" id="uploadBtn">开始上传</button>
                    </form>
                </div>

                <div class="upload-card">
                    <h2>⬇️ 从电脑下载文件</h2>
                    {file_list_html}
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
                
                // 1. 文件选择显示名称
                fileInput.addEventListener('change', function() {{
                    if (this.files[0]) {{
                        fileLabel.innerHTML = '📄 ' + this.files[0].name;
                        fileLabel.style.color = '#007aff';
                    }}
                }});

                // 2. 上传逻辑 (AJAX)
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
                            uploadText.innerText = '完成!';
                            setTimeout(() => {{ location.reload(); }}, 500);
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

                // 3. 下载逻辑 (AJAX Blob)
                function downloadFile(url, filename, id) {{
                    const container = document.getElementById('dl-progress-' + id);
                    const bar = container.querySelector('.progress-bar');
                    const text = container.querySelector('.progress-text');
                    
                    const xhr = new XMLHttpRequest();
                    xhr.open('GET', url, true);
                    xhr.responseType = 'blob';
                    
                    container.style.display = 'block';
                    
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
                            
                            text.innerText = '完成!';
                            setTimeout(() => {{ container.style.display = 'none'; }}, 2000);
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
