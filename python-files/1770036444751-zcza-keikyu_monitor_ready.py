#!/usr/bin/env python3
"""
京急モーニング・ウィング号 空席監視プログラム (Discord専用版)
Webhook URL設定済み - すぐに使えます
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, time as dt_time
import sys

# ===== 設定項目 =====

# Discord Webhook URL（設定済み）
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1467837927298957312/XWF6mIjvAlLF7h3CYh7EqWxSsS8L31hnCX2lVr39724OmDomMqqvXC-vlPO4echS1OGf'

# 監視設定
CHECK_INTERVAL = 60  # チェック間隔（秒） ※30秒以上を推奨
TARGET_STATION = "横須賀中央"
TARGET_TIME = "06:26"
TARGET_TRAIN = "3号"
TARGET_URL = "https://kquick.keikyu.co.jp/pc/ticket/stock/mwpass"


class KeikuMonitor:
    def __init__(self):
        """初期化"""
        # 統計情報
        self.stats = {
            'start_time': None,
            'total_checks': 0,
            'success_checks': 0,
            'failed_checks': 0,
            'last_status': None,
            'status_changes': 0,
            'notifications_sent': 0,
            'consecutive_errors': 0,
        }
        
        # 定時通知の送信済みフラグ
        self.daily_reports_sent = {
            'morning': None,  # 送信した日付を記録
            'evening': None,
        }
        
        self.is_running = True
    
    def send_discord(self, notification_type, **kwargs):
        """Discord通知を送信"""
        try:
            # 通知タイプに応じてメッセージを構築
            if notification_type == 'startup':
                embed = {
                    'title': '🚀 監視プログラムを起動しました',
                    'description': f'{TARGET_STATION}駅 {TARGET_TIME}発の空席監視を開始します',
                    'color': 3447003,  # 青色
                    'fields': [
                        {'name': '🚉 乗車駅', 'value': TARGET_STATION, 'inline': True},
                        {'name': '⏰ 発車時刻', 'value': TARGET_TIME, 'inline': True},
                        {'name': '🚄 列車番号', 'value': TARGET_TRAIN, 'inline': True},
                        {'name': '⏱️ チェック間隔', 'value': f'{CHECK_INTERVAL}秒ごと', 'inline': True},
                        {'name': '📊 定時レポート', 'value': '朝7時・夜9時', 'inline': True},
                        {'name': '🕐 開始時刻', 'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'inline': False},
                    ],
                    'footer': {'text': '空席を発見したら即座に通知します！'},
                    'timestamp': datetime.now().isoformat()
                }
                
            elif notification_type == 'seat_available':
                status = kwargs.get('status')
                embed = {
                    'title': '🎉 空席を発見しました！',
                    'description': f'**{TARGET_STATION}駅 {TARGET_TIME}発 ({TARGET_TRAIN})** に空席があります',
                    'color': 5763719,  # 緑色
                    'fields': [
                        {'name': '空席状況', 'value': f'**{status}**', 'inline': True},
                        {'name': '検出時刻', 'value': datetime.now().strftime('%H:%M:%S'), 'inline': True},
                        {'name': '予約リンク', 'value': f'[今すぐ予約する]({TARGET_URL})', 'inline': False},
                    ],
                    'footer': {'text': 'お早めにご予約ください！'},
                    'timestamp': datetime.now().isoformat()
                }
                
            elif notification_type == 'daily_report':
                report_time = kwargs.get('report_time', 'morning')
                uptime_minutes = int((datetime.now() - self.stats['start_time']).total_seconds() / 60)
                success_rate = (self.stats['success_checks'] / self.stats['total_checks'] * 100) if self.stats['total_checks'] > 0 else 0
                
                time_emoji = '🌅' if report_time == 'morning' else '🌙'
                time_label = '朝の' if report_time == 'morning' else '夜の'
                report_color = 16776960 if report_time == 'morning' else 8388736  # 黄色/紫色
                
                embed = {
                    'title': f'{time_emoji} {time_label}定時レポート',
                    'description': '✅ **プログラムは正常に動作しています**',
                    'color': report_color,
                    'fields': [
                        {'name': '📋 監視対象', 'value': f'{TARGET_STATION}駅 {TARGET_TIME}発 ({TARGET_TRAIN})', 'inline': False},
                        {'name': '⏱️ 稼働時間', 'value': f'{uptime_minutes // 60}時間{uptime_minutes % 60}分', 'inline': True},
                        {'name': '🔍 総チェック回数', 'value': f'{self.stats["total_checks"]}回', 'inline': True},
                        {'name': '✅ 成功率', 'value': f'{success_rate:.1f}%', 'inline': True},
                        {'name': '📊 成功/失敗', 'value': f'{self.stats["success_checks"]}回 / {self.stats["failed_checks"]}回', 'inline': True},
                        {'name': '🎫 最新の空席状況', 'value': self.stats['last_status'] or '未取得', 'inline': True},
                        {'name': '🔔 送信した通知数', 'value': f'{self.stats["notifications_sent"]}回', 'inline': True},
                    ],
                    'footer': {'text': 'プログラムは継続して監視を行っています'},
                    'timestamp': datetime.now().isoformat()
                }
                
            elif notification_type == 'error_alert':
                error_count = kwargs.get('error_count', 0)
                embed = {
                    'title': '⚠️ 警告: 連続エラーを検知しました',
                    'description': f'**{error_count}回**連続でエラーが発生しています',
                    'color': 15158332,  # 赤色
                    'fields': [
                        {'name': '考えられる原因', 'value': 
                         '• インターネット接続の問題\n'
                         '• KQuickサイトのメンテナンス\n'
                         '• サイト構造の変更', 'inline': False},
                        {'name': '対応', 'value': 
                         'プログラムは継続して監視を試みますが、\n'
                         '状況を確認することをお勧めします。', 'inline': False},
                    ],
                    'footer': {'text': '問題が解決すると自動的に通知が止まります'},
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                return False
            
            # Discordに送信
            data = {'embeds': [embed]}
            response = requests.post(
                DISCORD_WEBHOOK_URL,
                json=data,
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"      ❌ Discord通知エラー: {e}")
            return False
    
    def check_daily_reports(self):
        """定時レポートの送信チェック"""
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()
        
        # 朝7時のレポート（7:00-7:05の間）
        if (dt_time(7, 0) <= current_time <= dt_time(7, 5) and 
            self.daily_reports_sent['morning'] != current_date):
            
            print()
            print("    📊 朝の定時レポートを送信します...")
            if self.send_discord('daily_report', report_time='morning'):
                self.daily_reports_sent['morning'] = current_date
                self.stats['notifications_sent'] += 1
                print("    ✅ 朝のレポート送信完了")
            print()
        
        # 夜9時のレポート（21:00-21:05の間）
        if (dt_time(21, 0) <= current_time <= dt_time(21, 5) and 
            self.daily_reports_sent['evening'] != current_date):
            
            print()
            print("    📊 夜の定時レポートを送信します...")
            if self.send_discord('daily_report', report_time='evening'):
                self.daily_reports_sent['evening'] = current_date
                self.stats['notifications_sent'] += 1
                print("    ✅ 夜のレポート送信完了")
            print()
    
    def check_seat_availability(self):
        """空席状況をチェック"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(TARGET_URL, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) > 0:
                    station_cell = cells[0].get_text(strip=True)
                    
                    if TARGET_STATION in station_cell:
                        for i, cell in enumerate(cells):
                            text = cell.get_text(strip=True)
                            
                            if TARGET_TIME in text and "発" in text:
                                if i + 1 < len(cells):
                                    status_cell = cells[i + 1]
                                    status = status_cell.get_text(strip=True)
                                    
                                    # 統計更新
                                    self.stats['success_checks'] += 1
                                    self.stats['consecutive_errors'] = 0
                                    
                                    return {
                                        'status': status,
                                        'available': status in ['○', '△']
                                    }
            
            # 見つからなかった場合
            self.stats['success_checks'] += 1
            self.stats['consecutive_errors'] = 0
            
            return {
                'status': '不明',
                'available': False
            }
            
        except Exception as e:
            print(f"      ❌ チェックエラー: {e}")
            self.stats['failed_checks'] += 1
            self.stats['consecutive_errors'] += 1
            
            # 連続10回エラーで警告通知
            if self.stats['consecutive_errors'] == 10:
                print()
                print("    ⚠️  連続エラーを検知。警告通知を送信します...")
                if self.send_discord('error_alert', error_count=10):
                    self.stats['notifications_sent'] += 1
                print()
            
            return None
    
    def stop(self):
        """監視を停止"""
        self.is_running = False
    
    def run(self):
        """監視メインループ"""
        print("=" * 70)
        print("京急モーニング・ウィング号 空席監視プログラム")
        print("(Discord専用版)")
        print("=" * 70)
        print(f"監視対象: {TARGET_STATION}駅 {TARGET_TIME}発 ({TARGET_TRAIN})")
        print(f"チェック間隔: {CHECK_INTERVAL}秒ごと")
        print(f"定時レポート: 朝7時・夜9時")
        print(f"通知先: Discord Webhook")
        print("=" * 70)
        print()
        
        # 統計情報初期化
        self.stats['start_time'] = datetime.now()
        
        # 起動通知を送信
        print("📢 起動通知を送信します...")
        if self.send_discord('startup'):
            print("✅ 起動通知を送信しました")
            self.stats['notifications_sent'] += 1
        else:
            print("❌ 起動通知の送信に失敗しました")
        
        print()
        print("監視を開始します... (Ctrl+C で停止)")
        print()
        
        previous_status = None
        seat_notification_sent = False
        
        try:
            while self.is_running:
                self.stats['total_checks'] += 1
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"[{self.stats['total_checks']}] {current_time}", end=" ")
                
                result = self.check_seat_availability()
                
                if result is None:
                    print("→ ❌ チェック失敗")
                else:
                    status = result['status']
                    available = result['available']
                    
                    print(f"→ {status}", end="")
                    
                    if status != previous_status:
                        print(f" (変化: {previous_status or '初回'} → {status})")
                        self.stats['status_changes'] += 1
                    else:
                        print()
                    
                    # 統計更新
                    self.stats['last_status'] = status
                    previous_status = status
                    
                    # 空席発見時の通知
                    if available and not seat_notification_sent:
                        print()
                        print("    🎉" * 15)
                        print("    ✨ 空席を発見しました！")
                        print("    🎉" * 15)
                        print()
                        
                        if self.send_discord('seat_available', status=status):
                            seat_notification_sent = True
                            self.stats['notifications_sent'] += 1
                            print("    📱 Discord通知を送信しました")
                        else:
                            print("    ❌ Discord通知の送信に失敗しました")
                        
                        print()
                    
                    # 満席に戻った時
                    elif not available and seat_notification_sent:
                        seat_notification_sent = False
                        print("    ℹ️  再び満席になりました（次回空席時に再通知）")
                
                # 定時レポートのチェック
                self.check_daily_reports()
                
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            print()
            print()
            print("=" * 70)
            print("監視を停止しました")
            print()
            
            uptime_minutes = int((datetime.now() - self.stats['start_time']).total_seconds() / 60)
            success_rate = (self.stats['success_checks'] / self.stats['total_checks'] * 100) if self.stats['total_checks'] > 0 else 0
            
            print("【動作統計】")
            print(f"稼働時間: {uptime_minutes}分 ({uptime_minutes // 60}時間{uptime_minutes % 60}分)")
            print(f"総チェック回数: {self.stats['total_checks']}回")
            print(f"成功: {self.stats['success_checks']}回")
            print(f"失敗: {self.stats['failed_checks']}回")
            print(f"成功率: {success_rate:.1f}%")
            print(f"送信した通知数: {self.stats['notifications_sent']}回")
            print("=" * 70)


def main():
    """エントリーポイント"""
    monitor = KeikuMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
