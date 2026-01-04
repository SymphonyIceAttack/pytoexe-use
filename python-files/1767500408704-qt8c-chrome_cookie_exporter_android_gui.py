#!/usr/bin/env python3
"""
Chrome DevTools Cookie Exporter (Android対応GUI版)
Windows PCとAndroidデバイスの両方に対応
"""

import json
import requests
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import threading
import subprocess

class DeviceManager:
    """デバイス（PC Chrome / Android）の管理"""
    
    @staticmethod
    def check_adb_available():
        """ADBが利用可能かチェック"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_android_devices():
        """接続されているAndroidデバイスを取得"""
        try:
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode != 0:
                return []
            
            lines = result.stdout.strip().split('\n')[1:]
            devices = []
            for line in lines:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            return devices
        except:
            return []
    
    @staticmethod
    def setup_port_forwarding(device_id, remote_port=9222, local_port=9223):
        """Androidデバイスのポートフォワーディングを設定"""
        try:
            subprocess.run(['adb', '-s', device_id, 'forward', '--remove-all'],
                         capture_output=True, timeout=5)
            
            result = subprocess.run(
                ['adb', '-s', device_id, 'forward', 
                 f'tcp:{local_port}', f'localabstract:chrome_devtools_remote'],
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

class CookieExporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome Cookie Exporter (Android対応)")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # スタイル設定
        style = ttk.Style()
        style.theme_use('clam')
        
        # メインフレーム
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="Chrome Cookie Exporter (Android対応)", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # 説明フレーム
        info_frame = ttk.LabelFrame(main_frame, text="セットアップ情報", padding="5")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        info_text = ("【PC Chrome】chrome.exe --remote-debugging-port=9222\n"
                     "【Android】USBデバッグを有効化 + ADBインストール + USB接続")
        info_label = ttk.Label(info_frame, text=info_text, 
                               foreground='blue', font=('Arial', 9))
        info_label.pack()
        
        # デバイス情報フレーム
        device_frame = ttk.LabelFrame(main_frame, text="接続デバイス情報", padding="5")
        device_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        device_frame.columnconfigure(0, weight=1)
        
        self.device_info_text = scrolledtext.ScrolledText(device_frame, height=4, 
                                                          font=('Consolas', 8))
        self.device_info_text.pack(fill=tk.BOTH, expand=True)
        
        # リストボックスフレーム
        list_frame = ttk.LabelFrame(main_frame, text="利用可能なページ", padding="5")
        list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # スクロールバー付きリストボックス
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.page_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        height=12, font=('Consolas', 9))
        self.page_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.page_listbox.yview)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=(0, 10))
        
        self.refresh_button = ttk.Button(button_frame, text="デバイスとページをスキャン", 
                                         command=self.refresh_all)
        self.refresh_button.grid(row=0, column=0, padx=5)
        
        self.export_button = ttk.Button(button_frame, text="Cookieをエクスポート", 
                                        command=self.export_cookies)
        self.export_button.grid(row=0, column=1, padx=5)
        
        self.help_button = ttk.Button(button_frame, text="ヘルプ", 
                                      command=self.show_help)
        self.help_button.grid(row=0, column=2, padx=5)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        # データ保持
        self.all_sources = []
        self.device_manager = DeviceManager()
        
        # 初回読み込み
        self.refresh_all()
    
    def show_help(self):
        """ヘルプを表示"""
        help_text = """
【PC Chromeの場合】
1. Chromeを以下のコマンドで起動:
   chrome.exe --remote-debugging-port=9222

2. Cookieを取得したいページを開く

【Androidの場合】
1. Androidデバイスで「開発者向けオプション」を有効化
2. 「USBデバッグ」を有効化
3. PCにADBをインストール（Android SDKに含まれる）
4. USBケーブルでPCとAndroidを接続
5. Androidで「USBデバッグを許可」をタップ
6. Androidの Chrome でページを開く
7. PC の Chrome で chrome://inspect を開く
8. 「Discover USB devices」にチェック

【ADBのインストール】
- Android Studio をインストール、または
- Platform Tools のみをダウンロード:
  https://developer.android.com/studio/releases/platform-tools

【使い方】
1. 「デバイスとページをスキャン」をクリック
2. リストからページを選択
3. 「Cookieをエクスポート」をクリック
4. 保存先を選択
"""
        messagebox.showinfo("ヘルプ", help_text)
    
    def get_targets_from_port(self, port):
        """指定されたポートからターゲットを取得"""
        try:
            response = requests.get(f"http://localhost:{port}/json", timeout=3)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def refresh_all(self):
        """全てのデバイスとページをスキャン"""
        self.status_var.set("スキャン中...")
        self.refresh_button.config(state='disabled')
        self.export_button.config(state='disabled')
        
        def scan():
            self.all_sources = []
            device_info_lines = []
            
            # PC Chromeをチェック
            device_info_lines.append("【PC Chrome】")
            pc_targets = self.get_targets_from_port(9222)
            if pc_targets:
                device_info_lines.append(f"  ✓ ポート 9222: {len(pc_targets)} ページ検出")
                for target in pc_targets:
                    self.all_sources.append({
                        'source_type': 'PC Chrome',
                        'port': 9222,
                        'target': target
                    })
            else:
                device_info_lines.append("  ✗ ポート 9222: 接続なし")
            
            # Androidデバイスをチェック
            device_info_lines.append("\n【Android デバイス】")
            if self.device_manager.check_adb_available():
                device_info_lines.append("  ✓ ADB 利用可能")
                android_devices = self.device_manager.get_android_devices()
                
                if android_devices:
                    device_info_lines.append(f"  ✓ {len(android_devices)} 台のデバイスが接続中")
                    
                    for i, device_id in enumerate(android_devices):
                        local_port = 9223 + i
                        device_info_lines.append(f"    → {device_id} (ポート {local_port})")
                        
                        if self.device_manager.setup_port_forwarding(device_id, local_port=local_port):
                            time.sleep(1)
                            android_targets = self.get_targets_from_port(local_port)
                            
                            if android_targets:
                                device_info_lines.append(f"      ✓ {len(android_targets)} ページ検出")
                                for target in android_targets:
                                    self.all_sources.append({
                                        'source_type': f'Android ({device_id[:8]}...)',
                                        'port': local_port,
                                        'device_id': device_id,
                                        'target': target
                                    })
                            else:
                                device_info_lines.append(f"      ✗ ページなし")
                        else:
                            device_info_lines.append(f"      ✗ ポートフォワーディング失敗")
                else:
                    device_info_lines.append("  ✗ デバイスが見つかりません")
            else:
                device_info_lines.append("  ✗ ADB がインストールされていません")
            
            # 結果を反映
            device_info = "\n".join(device_info_lines)
            self.root.after(0, lambda: self.update_ui(device_info))
        
        thread = threading.Thread(target=scan)
        thread.daemon = True
        thread.start()
    
    def update_ui(self, device_info):
        """UIを更新"""
        # デバイス情報を更新
        self.device_info_text.delete(1.0, tk.END)
        self.device_info_text.insert(1.0, device_info)
        
        # リストボックスを更新
        self.page_listbox.delete(0, tk.END)
        
        if not self.all_sources:
            self.page_listbox.insert(tk.END, "ページが見つかりません")
            self.page_listbox.insert(tk.END, "")
            self.page_listbox.insert(tk.END, "「ヘルプ」ボタンでセットアップ方法を確認してください")
            self.status_var.set("ページが見つかりません")
        else:
            for i, source in enumerate(self.all_sources):
                target = source['target']
                source_type = source['source_type']
                title = target.get('title', 'No Title')
                url = target.get('url', 'No URL')
                
                display_text = f"[{i+1}] [{source_type}] {title} | {url}"
                if len(display_text) > 120:
                    display_text = display_text[:117] + "..."
                
                self.page_listbox.insert(tk.END, display_text)
            
            self.status_var.set(f"{len(self.all_sources)} ページが見つかりました")
        
        self.refresh_button.config(state='normal')
        self.export_button.config(state='normal')
    
    def get_cookies(self, ws_url):
        """全てのCookieを取得"""
        import websocket
        
        ws = websocket.create_connection(ws_url, timeout=10)
        
        command = {
            "id": 1,
            "method": "Network.getAllCookies",
            "params": {}
        }
        
        ws.send(json.dumps(command))
        response = json.loads(ws.recv())
        ws.close()
        
        if "result" in response and "cookies" in response["result"]:
            return response["result"]["cookies"]
        return []
    
    def convert_to_netscape_format(self, cookies):
        """CookieをNetscape形式に変換"""
        lines = [
            "# Netscape HTTP Cookie File",
            "# This is a generated file! Do not edit.",
            ""
        ]
        
        for cookie in cookies:
            domain = cookie.get('domain', '')
            include_subdomains = "TRUE" if domain.startswith('.') else "FALSE"
            path = cookie.get('path', '/')
            secure = "TRUE" if cookie.get('secure', False) else "FALSE"
            
            expires = cookie.get('expires', time.time() + 31536000)
            if expires == -1:
                expires = 0
            else:
                expires = int(expires)
            
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def export_cookies(self):
        """Cookieをエクスポート"""
        # websocketモジュールをチェック
        try:
            import websocket
        except ImportError:
            messagebox.showerror("エラー", 
                "websocket-clientモジュールがインストールされていません\n\n"
                "以下のコマンドでインストールしてください:\n"
                "pip install websocket-client")
            return
        
        # 選択されているアイテムを取得
        selection = self.page_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "ページを選択してください")
            return
        
        if not self.all_sources:
            messagebox.showerror("エラー", "ページが見つかりません")
            return
        
        index = selection[0]
        if index >= len(self.all_sources):
            messagebox.showerror("エラー", "無効な選択です")
            return
        
        selected_source = self.all_sources[index]
        target = selected_source['target']
        source_type = selected_source['source_type']
        
        ws_url = target.get('webSocketDebuggerUrl')
        
        if not ws_url:
            messagebox.showerror("エラー", "WebSocketのURLが取得できません")
            return
        
        # 保存先を選択
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="cookies.txt"
        )
        
        if not file_path:
            return
        
        self.status_var.set("Cookieを取得中...")
        self.export_button.config(state='disabled')
        
        def export():
            try:
                # Cookieを取得
                cookies = self.get_cookies(ws_url)
                
                if not cookies:
                    self.root.after(0, lambda: messagebox.showinfo("情報", "Cookieが見つかりませんでした"))
                    self.root.after(0, lambda: self.status_var.set("Cookieが見つかりませんでした"))
                    return
                
                # Netscape形式に変換
                netscape_content = self.convert_to_netscape_format(cookies)
                
                # ファイルに保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(netscape_content)
                
                # 成功メッセージ
                message = (f"✓ {len(cookies)} 個のCookieを保存しました\n\n"
                          f"ソース: {source_type}\n"
                          f"URL: {target.get('url', '')[:60]}...\n"
                          f"保存先: {file_path}")
                self.root.after(0, lambda: messagebox.showinfo("成功", message))
                self.root.after(0, lambda: self.status_var.set(f"{len(cookies)} 個のCookieを保存しました"))
                
            except Exception as e:
                error_msg = f"エラーが発生しました:\n{str(e)}"
                self.root.after(0, lambda: messagebox.showerror("エラー", error_msg))
                self.root.after(0, lambda: self.status_var.set("エラーが発生しました"))
            finally:
                self.root.after(0, lambda: self.export_button.config(state='normal'))
        
        thread = threading.Thread(target=export)
        thread.daemon = True
        thread.start()

def main():
    root = tk.Tk()
    app = CookieExporterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
