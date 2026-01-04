#!/usr/bin/env python3
"""
Chrome DevTools Cookie Exporter (Android対応版)
Windows PCとAndroidデバイスの両方に対応
"""

import json
import requests
import sys
import time
import subprocess
import re
from datetime import datetime
from pathlib import Path

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
            
            lines = result.stdout.strip().split('\n')[1:]  # "List of devices attached"をスキップ
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
            # 既存のフォワーディングをクリア
            subprocess.run(['adb', '-s', device_id, 'forward', '--remove-all'],
                         capture_output=True, timeout=5)
            
            # 新しいフォワーディングを設定
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
    
    @staticmethod
    def get_available_ports():
        """利用可能なポートをスキャン"""
        ports_to_check = [9222, 9223, 9224, 9225, 9226]
        available_ports = []
        
        for port in ports_to_check:
            try:
                response = requests.get(f"http://localhost:{port}/json", timeout=2)
                if response.status_code == 200:
                    targets = response.json()
                    if targets:  # ターゲットが存在する
                        available_ports.append({
                            'port': port,
                            'targets': targets,
                            'count': len(targets)
                        })
            except:
                continue
        
        return available_ports

def get_targets_from_port(port):
    """指定されたポートからターゲットを取得"""
    try:
        response = requests.get(f"http://localhost:{port}/json", timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        return []

def list_all_sources(device_manager):
    """全てのソース（PC + Android）を一覧表示"""
    print("\n" + "=" * 80)
    print("接続可能なデバイスとページを検索中...")
    print("=" * 80)
    
    all_sources = []
    source_index = 0
    
    # PCのChromeをチェック（ポート9222）
    pc_targets = get_targets_from_port(9222)
    if pc_targets:
        print(f"\n[PC Chrome] ポート 9222 ({len(pc_targets)} ページ)")
        print("-" * 80)
        for target in pc_targets:
            source_index += 1
            target_type = target.get('type', 'unknown')
            title = target.get('title', 'No Title')
            url = target.get('url', 'No URL')
            
            print(f"{source_index}. [{target_type}] {title}")
            print(f"   URL: {url}")
            print()
            
            all_sources.append({
                'index': source_index,
                'source_type': 'PC Chrome',
                'port': 9222,
                'target': target
            })
    
    # Androidデバイスをチェック
    if device_manager.check_adb_available():
        android_devices = device_manager.get_android_devices()
        
        if android_devices:
            print(f"\n✓ {len(android_devices)} 台のAndroidデバイスが見つかりました")
            
            for i, device_id in enumerate(android_devices):
                local_port = 9223 + i
                
                # ポートフォワーディングを設定
                print(f"  → デバイス {device_id} をポート {local_port} に設定中...")
                if device_manager.setup_port_forwarding(device_id, local_port=local_port):
                    time.sleep(1)  # 少し待機
                    
                    # ターゲットを取得
                    android_targets = get_targets_from_port(local_port)
                    if android_targets:
                        print(f"\n[Android: {device_id}] ポート {local_port} ({len(android_targets)} ページ)")
                        print("-" * 80)
                        
                        for target in android_targets:
                            source_index += 1
                            target_type = target.get('type', 'unknown')
                            title = target.get('title', 'No Title')
                            url = target.get('url', 'No URL')
                            
                            print(f"{source_index}. [{target_type}] {title}")
                            print(f"   URL: {url}")
                            print()
                            
                            all_sources.append({
                                'index': source_index,
                                'source_type': f'Android ({device_id})',
                                'port': local_port,
                                'device_id': device_id,
                                'target': target
                            })
    else:
        print("\n[情報] ADBが見つかりません（Android対応にはADBが必要です）")
    
    # その他のポートもスキャン
    print("\n他のポートをスキャン中...")
    available_ports = device_manager.get_available_ports()
    for port_info in available_ports:
        port = port_info['port']
        if port == 9222:  # 既にチェック済み
            continue
        
        # 既にAndroidデバイスとして登録済みか確認
        already_registered = any(s['port'] == port for s in all_sources)
        if already_registered:
            continue
        
        targets = port_info['targets']
        print(f"\n[その他] ポート {port} ({len(targets)} ページ)")
        print("-" * 80)
        
        for target in targets:
            source_index += 1
            target_type = target.get('type', 'unknown')
            title = target.get('title', 'No Title')
            url = target.get('url', 'No URL')
            
            print(f"{source_index}. [{target_type}] {title}")
            print(f"   URL: {url}")
            print()
            
            all_sources.append({
                'index': source_index,
                'source_type': f'リモート (ポート {port})',
                'port': port,
                'target': target
            })
    
    return all_sources

def get_cookies(ws_url):
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

def convert_to_netscape_format(cookies):
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

def main():
    print("=" * 80)
    print("Chrome Cookie Exporter (Android対応版)")
    print("=" * 80)
    
    # websocketモジュールをチェック
    try:
        import websocket
    except ImportError:
        print("\nエラー: websocket-clientモジュールがインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install websocket-client")
        sys.exit(1)
    
    # デバイスマネージャーを初期化
    device_manager = DeviceManager()
    
    # 全てのソースを一覧表示
    all_sources = list_all_sources(device_manager)
    
    if not all_sources:
        print("\n❌ ページが見つかりません\n")
        print("【PC Chromeの場合】")
        print("  chrome.exe --remote-debugging-port=9222 で起動してください\n")
        print("【Androidの場合】")
        print("  1. USB デバッグを有効にする")
        print("  2. Chrome で chrome://inspect を開く")
        print("  3. 「Discover USB devices」にチェック")
        print("  4. Android デバイスを USB 接続")
        print("  5. ADB がインストールされていることを確認\n")
        sys.exit(1)
    
    # ユーザーに選択させる
    try:
        choice = input(f"\nCookieを取得するページの番号を入力してください (1-{len(all_sources)}): ")
        choice = int(choice)
        
        if choice < 1 or choice > len(all_sources):
            print("無効な選択です")
            sys.exit(1)
        
        # 選択されたソースを取得
        selected_source = next(s for s in all_sources if s['index'] == choice)
        target = selected_source['target']
        source_type = selected_source['source_type']
        
        ws_url = target.get('webSocketDebuggerUrl')
        
        if not ws_url:
            print("エラー: WebSocketのURLが取得できません")
            sys.exit(1)
        
        print(f"\n接続中...")
        print(f"  ソース: {source_type}")
        print(f"  タイトル: {target.get('title')}")
        print(f"  URL: {target.get('url')}")
        
        # Cookieを取得
        print("\nCookieを取得中...")
        cookies = get_cookies(ws_url)
        
        print(f"✓ 取得したCookie数: {len(cookies)}")
        
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
            domain = cookie.get('domain', '')
            name = cookie.get('name', '')
            value = cookie.get('value', '')[:30]
            print(f"  - [{domain}] {name}: {value}...")
        
        if len(cookies) > 5:
            print(f"  ... 他 {len(cookies) - 5} 個")
        
        print(f"\n✓ 完了しました！")
        
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
