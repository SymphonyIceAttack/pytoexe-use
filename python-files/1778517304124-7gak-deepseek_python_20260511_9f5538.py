import subprocess
import sys
import os
import json
import time
import base64
from urllib.parse import unquote

try:
    import customtkinter as ctk
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    import customtkinter as ctk

class VLESSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("VLESS Client")
        self.geometry("500x400")
        self.xray_process = None
        
        # Заголовок
        ctk.CTkLabel(self, text="VLESS Client", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Поле для ссылки
        self.link_entry = ctk.CTkEntry(self, width=400, placeholder_text="Вставьте vless:// ссылку...")
        self.link_entry.pack(pady=10)
        
        # Информация
        self.info_text = ctk.CTkTextbox(self, width=400, height=100)
        self.info_text.pack(pady=10)
        self.info_text.insert("1.0", "Готов к подключению...")
        self.info_text.configure(state="disabled")
        
        # Кнопка
        self.btn = ctk.CTkButton(self, text="Подключить", command=self.toggle_connection, width=200, height=40)
        self.btn.pack(pady=10)
        
        # Статус
        self.status = ctk.CTkLabel(self, text="● Не подключено", text_color="red", font=("Arial", 14))
        self.status.pack(pady=20)
    
    def parse_vless(self, link):
        """Правильный парсер VLESS ссылки"""
        try:
            # Убираем vless://
            if link.startswith("vless://"):
                link = link[8:]
            
            # Разделяем UUID и остальное
            if "@" not in link:
                return None
            
            uuid, rest = link.split("@", 1)
            
            # Разделяем адрес и параметры
            if "?" in rest:
                address_part, params_part = rest.split("?", 1)
            else:
                address_part = rest
                params_part = ""
            
            # Парсим адрес:порт
            if ":" in address_part:
                address, port = address_part.rsplit(":", 1)
            else:
                address = address_part
                port = "443"
            
            # Убираем все после # (имя конфига)
            if "#" in params_part:
                params_part = params_part.split("#")[0]
            
            # Парсим параметры
            params = {}
            if params_part:
                for param in params_part.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        params[unquote(key)] = unquote(value)
            
            result = {
                "uuid": uuid,
                "address": address,
                "port": int(port),
                "params": params
            }
            
            return result
            
        except Exception as e:
            print(f"Ошибка парсинга: {e}")
            return None
    
    def create_config(self, parsed):
        """Создание конфига для Xray"""
        config = {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "tag": "socks",
                    "port": 1080,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "settings": {
                        "udp": True
                    }
                },
                {
                    "tag": "http",
                    "port": 1081,
                    "listen": "127.0.0.1",
                    "protocol": "http"
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [{
                            "address": parsed["address"],
                            "port": parsed["port"],
                            "users": [{
                                "id": parsed["uuid"],
                                "encryption": "none",
                                "flow": parsed["params"].get("flow", "")
                            }]
                        }]
                    },
                    "streamSettings": {
                        "network": parsed["params"].get("type", "tcp"),
                        "security": parsed["params"].get("security", "none")
                    }
                }
            ]
        }
        
        # Добавляем настройки транспорта
        network = parsed["params"].get("type", "tcp")
        stream = config["outbounds"][0]["streamSettings"]
        
        if network == "ws":
            stream["wsSettings"] = {
                "path": parsed["params"].get("path", "/"),
                "headers": {
                    "Host": parsed["params"].get("host", parsed["address"])
                }
            }
        elif network == "grpc":
            stream["grpcSettings"] = {
                "serviceName": parsed["params"].get("serviceName", "")
            }
        elif network == "kcp":
            stream["kcpSettings"] = {
                "header": {
                    "type": parsed["params"].get("headerType", "none")
                }
            }
        
        # Если есть TLS
        if parsed["params"].get("security") == "tls":
            stream["security"] = "tls"
            stream["tlsSettings"] = {
                "serverName": parsed["params"].get("sni", parsed["address"]),
                "allowInsecure": parsed["params"].get("allowInsecure", "0") == "1"
            }
        
        return config
    
    def toggle_connection(self):
        if self.xray_process:
            # Отключаем
            self.disconnect()
        else:
            # Подключаем
            self.connect()
    
    def connect(self):
        link = self.link_entry.get().strip()
        
        if not link:
            self.update_info("Ошибка: Введите ссылку")
            return
        
        # Парсим ссылку
        parsed = self.parse_vless(link)
        
        if not parsed:
            self.update_info("Ошибка: Неверный формат ссылки")
            return
        
        # Создаем конфиг
        config = self.create_config(parsed)
        
        # Сохраняем конфиг
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        # Показываем информацию
        info = f"Сервер: {parsed['address']}:{parsed['port']}\n"
        info += f"UUID: {parsed['uuid'][:16]}...\n"
        info += f"Протокол: {parsed['params'].get('type', 'tcp')}\n"
        info += f"TLS: {parsed['params'].get('security', 'none')}\n"
        info += f"Прокси: 127.0.0.1:1080 (SOCKS5)"
        self.update_info(info)
        
        # Запускаем Xray
        try:
            xray_path = "xray.exe" if sys.platform == "win32" else "xray"
            
            if not os.path.exists(xray_path):
                self.update_info("Ошибка: xray не найден\nСкачайте с github.com/XTLS/Xray-core")
                return
            
            self.xray_process = subprocess.Popen(
                [xray_path, "-c", "config.json"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(2)
            
            if self.xray_process.poll() is None:
                self.status.configure(text="● Подключено", text_color="green")
                self.btn.configure(text="Отключить")
                self.link_entry.configure(state="disabled")
            else:
                self.update_info("Ошибка: Не удалось запустить Xray")
                self.xray_process = None
                
        except Exception as e:
            self.update_info(f"Ошибка: {str(e)}")
            self.xray_process = None
    
    def disconnect(self):
        if self.xray_process:
            self.xray_process.terminate()
            time.sleep(1)
            if self.xray_process.poll() is None:
                self.xray_process.kill()
            self.xray_process = None
        
        self.status.configure(text="● Не подключено", text_color="red")
        self.btn.configure(text="Подключить")
        self.link_entry.configure(state="normal")
    
    def update_info(self, text):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", text)
        self.info_text.configure(state="disabled")

if __name__ == "__main__":
    app = VLESSApp()
    app.mainloop()