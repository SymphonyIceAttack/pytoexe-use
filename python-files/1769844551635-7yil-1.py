import os
import json
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# 配置
PORT = 8080
BASE_DIR = os.getcwd()  # 程序运行目录
WIOP_DIR = os.path.join(BASE_DIR, "wiop")  # wiop文件夹路径

# 确保wiop目录存在
if not os.path.exists(WIOP_DIR):
    os.makedirs(WIOP_DIR)


class FileManagerHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # 返回主页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 获取wiop目录中的文件列表
            files = []
            if os.path.exists(WIOP_DIR):
                for f in os.listdir(WIOP_DIR):
                    file_path = os.path.join(WIOP_DIR, f)
                    if os.path.isfile(file_path):
                        files.append({
                            'name': f,
                            'size': os.path.getsize(file_path),
                            'modified': time.ctime(os.path.getmtime(file_path))
                        })
            
            html = self.generate_html(files)
            self.wfile.write(html.encode('utf-8'))
            
        elif parsed_path.path == '/list':
            # 返回文件列表JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            files = []
            if os.path.exists(WIOP_DIR):
                for f in os.listdir(WIOP_DIR):
                    file_path = os.path.join(WIOP_DIR, f)
                    if os.path.isfile(file_path):
                        files.append({
                            'name': f,
                            'size': os.path.getsize(file_path),
                            'modified': time.ctime(os.path.getmtime(file_path))
                        })
            
            self.wfile.write(json.dumps(files).encode('utf-8'))
            
        else:
            # 默认处理静态文件
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/delete':
            # 删除所有文件
            self.delete_all_files()
            
        elif parsed_path.path == '/add':
            # 添加文件
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            filename = params.get('filename', ['new_file.txt'])[0]
            content = params.get('content', [''])[0]
            
            self.add_text_file(filename, content)
            
        else:
            self.send_error(404, "Not found")
    
    def delete_all_files(self):
        """删除wiop目录中的所有文件"""
        try:
            deleted_files = []
            if os.path.exists(WIOP_DIR):
                for f in os.listdir(WIOP_DIR):
                    file_path = os.path.join(WIOP_DIR, f)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_files.append(f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'success': True,
                'message': f'成功删除 {len(deleted_files)} 个文件',
                'deleted': deleted_files
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"删除文件时出错: {str(e)}")
    
    def add_text_file(self, filename, content=""):
        """添加文本文件到wiop目录"""
        try:
            # 确保文件名以.txt结尾
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            # 防止路径穿越
            filename = os.path.basename(filename)
            file_path = os.path.join(WIOP_DIR, filename)
            
            # 如果文件已存在，添加时间戳
            if os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(time.time())}{ext}"
                file_path = os.path.join(WIOP_DIR, filename)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content if content else f"这是一个自动创建的文本文件\n创建时间: {time.ctime()}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'success': True,
                'message': f'文件 {filename} 创建成功',
                'filename': filename,
                'path': file_path
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"创建文件时出错: {str(e)}")
    
    def generate_html(self, files):
        """生成HTML页面"""
        files_html = ""
        if files:
            for file in files:
                files_html += f"""
                <div class="file-item">
                    <div class="file-name">{file['name']}</div>
                    <div class="file-size">{file['size']} bytes</div>
                    <div class="file-modified">{file['modified']}</div>
                </div>
                """
        else:
            files_html = "<div class='empty'>wiop目录中没有文件</div>"
        
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件管理器 - wiop目录</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .path-info {{
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            font-family: monospace;
            color: #495057;
        }}
        
        .controls {{
            padding: 25px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            border-bottom: 1px solid #e9ecef;
            background: #f8f9fa;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .btn-delete {{
            background: #dc3545;
            color: white;
        }}
        
        .btn-delete:hover {{
            background: #c82333;
            transform: translateY(-2px);
        }}
        
        .btn-add {{
            background: #28a745;
            color: white;
        }}
        
        .btn-add:hover {{
            background: #218838;
            transform: translateY(-2px);
        }}
        
        .btn-refresh {{
            background: #17a2b8;
            color: white;
        }}
        
        .btn-refresh:hover {{
            background: #138496;
            transform: translateY(-2px);
        }}
        
        .file-form {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .form-group {{
            margin-bottom: 15px;
        }}
        
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #495057;
        }}
        
        input, textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        textarea {{
            min-height: 100px;
            resize: vertical;
            font-family: monospace;
        }}
        
        .files-container {{
            padding: 25px;
        }}
        
        .files-header {{
            display: grid;
            grid-template-columns: 2fr 1fr 2fr;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            font-weight: 600;
            color: #495057;
            margin-bottom: 10px;
        }}
        
        .file-item {{
            display: grid;
            grid-template-columns: 2fr 1fr 2fr;
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            transition: background 0.2s;
        }}
        
        .file-item:hover {{
            background: #f8f9fa;
        }}
        
        .empty {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-style: italic;
        }}
        
        .status {{
            padding: 15px;
            margin: 15px 25px;
            border-radius: 6px;
            display: none;
        }}
        
        .status.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            display: block;
        }}
        
        .status.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            display: block;
        }}
        
        .status.info {{
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
            display: block;
        }}
        
        @media (max-width: 768px) {{
            .controls {{
                flex-direction: column;
            }}
            
            .btn {{
                width: 100%;
                justify-content: center;
            }}
            
            .files-header, .file-item {{
                grid-template-columns: 1fr;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📁 文件管理器</h1>
            <p class="subtitle">管理 wiop 目录中的文件</p>
        </header>
        
        <div class="path-info">
            当前目录: {WIOP_DIR}
        </div>
        
        <div class="controls">
            <button class="btn btn-delete" onclick="deleteAllFiles()">
                🗑️ 删除所有文件
            </button>
            <button class="btn btn-add" onclick="showAddForm()">
                ➕ 添加文本文件
            </button>
            <button class="btn btn-refresh" onclick="loadFiles()">
                🔄 刷新列表
            </button>
        </div>
        
        <div id="status" class="status"></div>
        
        <div id="fileForm" class="file-form" style="display: none;">
            <div class="form-group">
                <label for="filename">文件名:</label>
                <input type="text" id="filename" placeholder="例如: myfile.txt" value="new_file_{int(time.time())}.txt">
            </div>
            <div class="form-group">
                <label for="content">文件内容:</label>
                <textarea id="content" placeholder="输入文件内容..."></textarea>
            </div>
            <button class="btn btn-add" onclick="addFile()">
                💾 创建文件
            </button>
            <button class="btn" onclick="hideAddForm()" style="background: #6c757d; color: white; margin-left: 10px;">
                取消
            </button>
        </div>
        
        <div class="files-container">
            <h2>wiop目录中的文件 (共 {len(files)} 个)</h2>
            <div class="files-header">
                <div>文件名</div>
                <div>大小</div>
                <div>修改时间</div>
            </div>
            <div id="filesList">
                {files_html}
            </div>
        </div>
    </div>
    
    <script>
        function showStatus(message, type = 'info') {{
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
            setTimeout(() => {{
                statusEl.style.display = 'none';
            }}, 5000);
        }}
        
        async function deleteAllFiles() {{
            if (!confirm('确定要删除wiop目录中的所有文件吗？此操作不可恢复！')) {{
                return;
            }}
            
            try {{
                const response = await fetch('/delete', {{
                    method: 'POST'
                }});
                const result = await response.json();
                
                if (result.success) {{
                    showStatus(result.message, 'success');
                    loadFiles();
                }} else {{
                    showStatus('删除失败: ' + result.message, 'error');
                }}
            }} catch (error) {{
                showStatus('删除失败: ' + error.message, 'error');
            }}
        }}
        
        function showAddForm() {{
            document.getElementById('fileForm').style.display = 'block';
        }}
        
        function hideAddForm() {{
            document.getElementById('fileForm').style.display = 'none';
        }}
        
        async function addFile() {{
            const filename = document.getElementById('filename').value;
            const content = document.getElementById('content').value;
            
            if (!filename) {{
                showStatus('请输入文件名', 'error');
                return;
            }}
            
            try {{
                const formData = new URLSearchParams();
                formData.append('filename', filename);
                formData.append('content', content);
                
                const response = await fetch('/add', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }},
                    body: formData
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showStatus(result.message, 'success');
                    hideAddForm();
                    loadFiles();
                    
                    // 清空表单
                    document.getElementById('filename').value = '';
                    document.getElementById('content').value = '';
                }} else {{
                    showStatus('创建失败: ' + result.message, 'error');
                }}
            }} catch (error) {{
                showStatus('创建失败: ' + error.message, 'error');
            }}
        }}
        
        async function loadFiles() {{
            try {{
                const response = await fetch('/list');
                const files = await response.json();
                
                let filesHtml = '';
                if (files.length > 0) {{
                    files.forEach(file => {{
                        filesHtml += `
                        <div class="file-item">
                            <div class="file-name">${{file.name}}</div>
                            <div class="file-size">${{file.size}} bytes</div>
                            <div class="file-modified">${{file.modified}}</div>
                        </div>
                        `;
                    }});
                }} else {{
                    filesHtml = '<div class="empty">wiop目录中没有文件</div>';
                }}
                
                document.getElementById('filesList').innerHTML = filesHtml;
                
                // 更新标题中的文件计数
                const h2 = document.querySelector('.files-container h2');
                h2.textContent = `wiop目录中的文件 (共 ${{files.length}} 个)`;
                
            }} catch (error) {{
                showStatus('加载文件列表失败: ' + error.message, 'error');
            }}
        }}
        
        // 页面加载时显示当前文件列表
        document.addEventListener('DOMContentLoaded', () => {{
            console.log('文件管理器已启动，访问 http://localhost:{PORT}');
        }});
    </script>
</body>
</html>
"""


def start_server():
    """启动HTTP服务器"""
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, FileManagerHandler)
    
    print("=" * 60)
    print(f"📁 文件管理器服务器已启动!")
    print(f"🌐 访问地址: http://localhost:{PORT}")
    print(f"📂 文件目录: {WIOP_DIR}")
    print("=" * 60)
    print("\n操作说明:")
    print("1. 点击 '删除所有文件' 按钮清空wiop目录")
    print("2. 点击 '添加文本文件' 按钮创建新文件")
    print("3. 点击 '刷新列表' 按钮更新文件列表")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.server_close()


def open_browser():
    """在默认浏览器中打开页面"""
    import webbrowser
    import time
    
    # 等待服务器启动
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    # 可选：在新线程中打开浏览器
    # threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动服务器
    start_server()