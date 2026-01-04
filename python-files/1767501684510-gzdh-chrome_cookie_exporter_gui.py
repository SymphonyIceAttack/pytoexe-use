#!/usr/bin/env python3
"""
Chrome DevTools Cookie Exporter (GUI版)
chrome://inspect/#devices からCookieをNetscape形式でエクスポート
"""

import json
import requests
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading

class CookieExporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome Cookie Exporter")
        self.root.geometry("800x600")
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
        main_frame.rowconfigure(2, weight=1)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="Chrome Cookie Exporter", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # 説明
        info_text = ("Chromeをデバッグモードで起動してください:\n"
                     'chrome.exe --remote-debugging-port=9222')
        info_label = ttk.Label(main_frame, text=info_text, 
                               foreground='blue', font=('Arial', 9))
        info_label.grid(row=1, column=0, pady=(0, 10))
        
        # リストボックスフレーム
        list_frame = ttk.LabelFrame(main_frame, text="開いているページ", padding="5")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # スクロールバー付きリストボックス
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.page_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        height=15, font=('Consolas', 9))
        self.page_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.page_listbox.yview)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(0, 10))
        
        self.refresh_button = ttk.Button(button_frame, text="ページ一覧を更新", 
                                         command=self.refresh_targets)
        self.refresh_button.grid(row=0, column=0, padx=5)
        
        self.export_button = ttk.Button(button_frame, text="Cookieをエクスポート", 
                                        command=self.export_cookies)
        self.export_button.grid(row=0, column=1, padx=5)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        # データ保持
        self.targets = []
        
        # 初回読み込み
        self.refresh_targets()
    
    def get_available_targets(self):
        """利用可能なChromeのデバッグターゲットを取得"""
        try:
            response = requests.get("http://localhost:9222/json", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            return []
    
    def refresh_targets(self):
        """ターゲット一覧を更新"""
        self.status_var.set("ページ一覧を取得中...")
        self.refresh_button.config(state='disabled')
        
        def fetch():
            self.targets = self.get_available_targets()
            self.root.after(0, self.update_listbox)
        
        thread = threading.Thread(target=fetch)
        thread.daemon = True
        thread.start()
    
    def update_listbox(self):
        """リストボックスを更新"""
        self.page_listbox.delete(0, tk.END)
        
        if not self.targets:
            self.page_listbox.insert(tk.END, "ページが見つかりません")
            self.page_listbox.insert(tk.END, "")
            self.page_listbox.insert(tk.END, "Chromeをデバッグモードで起動してください:")
            self.page_listbox.insert(tk.END, "chrome.exe --remote-debugging-port=9222")
            self.status_var.set("エラー: ページが見つかりません")
            self.refresh_button.config(state='normal')
            return
        
        for i, target in enumerate(self.targets):
            target_type = target.get('type', 'unknown')
            title = target.get('title', 'No Title')
            url = target.get('url', 'No URL')
            
            # タイトルとURLを表示
            display_text = f"[{i+1}] {title} | {url}"
            if len(display_text) > 100:
                display_text = display_text[:97] + "..."
            
            self.page_listbox.insert(tk.END, display_text)
        
        self.status_var.set(f"{len(self.targets)} ページが見つかりました")
        self.refresh_button.config(state='normal')
    
    def get_cookies(self, ws_url):
        """全てのCookieを取得"""
        import websocket
        
        ws = websocket.create_connection(ws_url)
        
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
        
        if not self.targets:
            messagebox.showerror("エラー", "ページが見つかりません")
            return
        
        index = selection[0]
        if index >= len(self.targets):
            messagebox.showerror("エラー", "無効な選択です")
            return
        
        selected_target = self.targets[index]
        ws_url = selected_target.get('webSocketDebuggerUrl')
        
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
