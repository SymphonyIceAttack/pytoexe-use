#!/usr/bin/env python3
"""
Chrome DevTools Cookie Exporter
chrome://inspect/#devices からCookieをNetscape形式でエクスポート
"""

import json
import requests
import sys
import time
from datetime import datetime
from pathlib import Path

def get_available_targets():
    """利用可能なChromeのデバッグターゲットを取得"""
    try:
        response = requests.get("http://localhost:9222/json", timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"エラー: Chromeのデバッグポートに接続できません: {e}")
        print("\nChromeを以下のコマンドで起動してください:")
        print('chrome.exe --remote-debugging-port=9222')
        return []

def list_targets(targets):
    """ターゲット一覧を表示"""
    print("\n利用可能なページ:")
    print("-" * 80)
    for i, target in enumerate(targets):
        target_type = target.get('type', 'unknown')
        title = target.get('title', 'No Title')
        url = target.get('url', 'No URL')
        print(f"{i + 1}. [{target_type}] {title}")
        print(f"   URL: {url}")
        print()

def send_devtools_command(ws_url, method, params=None):
    """DevTools Protocolコマンドを送信"""
    import websocket
    
    ws = websocket.create_connection(ws_url)
    
    command = {
        "id": 1,
        "method": method,
        "params": params or {}
    }
    
    ws.send(json.dumps(command))
    response = json.loads(ws.recv())
    ws.close()
    
    return response

def get_cookies(ws_url):
    """全てのCookieを取得"""
    import websocket
    
    ws = websocket.create_connection(ws_url)
    
    # Cookieを取得
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

def convert_to_netscape_format(cookies):
    """CookieをNetscape形式に変換"""
    lines = [
        "# Netscape HTTP Cookie File",
        "# This is a generated file! Do not edit.",
        ""
    ]
    
    for cookie in cookies:
        domain = cookie.get('domain', '')
        
        # ドメインが . で始まる場合はTRUE、そうでない場合はFALSE
        include_subdomains = "TRUE" if domain.startswith('.') else "FALSE"
        
        # . で始まらない場合は追加
        if not domain.startswith('.'):
            domain = domain
        
        path = cookie.get('path', '/')
        secure = "TRUE" if cookie.get('secure', False) else "FALSE"
        
        # expiresがない場合は、現在時刻から1年後を設定
        expires = cookie.get('expires', time.time() + 31536000)
        if expires == -1:
            expires = 0
        else:
            expires = int(expires)
        
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        
        # Netscape形式: domain flag path secure expiration name value
        line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
        lines.append(line)
    
    return "\n".join(lines)

def main():
    print("=" * 80)
    print("Chrome DevTools Cookie Exporter")
    print("=" * 80)
    
    # websocketモジュールをチェック
    try:
        import websocket
    except ImportError:
        print("\nエラー: websocket-clientモジュールがインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install websocket-client")
        sys.exit(1)
    
    # ターゲット一覧を取得
    targets = get_available_targets()
    
    if not targets:
        print("\nターゲットが見つかりません。")
        print("\n【セットアップ手順】")
        print("1. Chromeを以下のコマンドで起動してください:")
        print("   chrome.exe --remote-debugging-port=9222")
        print("\n2. または、ショートカットのプロパティで以下を追加:")
        print('   リンク先: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
        sys.exit(1)
    
    # ページ一覧を表示
    list_targets(targets)
    
    # ユーザーに選択させる
    try:
        choice = input("Cookieを取得するページの番号を入力してください (1-{}): ".format(len(targets)))
        choice = int(choice) - 1
        
        if choice < 0 or choice >= len(targets):
            print("無効な選択です")
            sys.exit(1)
        
        selected_target = targets[choice]
        ws_url = selected_target.get('webSocketDebuggerUrl')
        
        if not ws_url:
            print("エラー: WebSocketのURLが取得できません")
            sys.exit(1)
        
        print(f"\nページに接続中: {selected_target.get('title')}")
        print(f"URL: {selected_target.get('url')}")
        
        # Cookieを取得
        print("\nCookieを取得中...")
        cookies = get_cookies(ws_url)
        
        print(f"取得したCookie数: {len(cookies)}")
        
        if not cookies:
            print("Cookieが見つかりませんでした")
            sys.exit(0)
        
        # Netscape形式に変換
        netscape_content = convert_to_netscape_format(cookies)
        
        # ファイルに保存
        output_file = "cookies.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(netscape_content)
        
        print(f"\n✓ Cookieを '{output_file}' に保存しました")
        print(f"  保存場所: {Path(output_file).absolute()}")
        
        # サンプルを表示
        print("\n【保存されたCookieの例】")
        for i, cookie in enumerate(cookies[:5]):
            print(f"  - {cookie.get('name')}: {cookie.get('value')[:50]}...")
        
        if len(cookies) > 5:
            print(f"  ... 他 {len(cookies) - 5} 個")
        
    except ValueError:
        print("エラー: 数値を入力してください")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nキャンセルされました")
        sys.exit(0)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
