import tkinter as tk
import random
import threading
import time

class RealisticPrankVirus:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#001100")
        self.root.bind("<Escape>", lambda e: None)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Реалистичные имена файлов
        self.fake_files = [
            "Documents/private_passwords.txt", 
            "Desktop/bank_cards.xlsx",
            "Pictures/IMG_2958.jpg",
            "Downloads/tax_return_2025.pdf",
            "AppData/chrome_cookies.db",
            "Telegram/tdata/session.dat",
            ".ssh/id_rsa",
            "Desktop/private_photos.zip",
            "Documents/contract_signed.docx",
            "AppData/wallet.dat",
            "Pictures/vacation/IMG_4452.png",
            "Documents/company_secrets.xlsx",
            "AppData/signal_backup.sqlite",
            "Desktop/bitcoin_private.key",
            "Documents/passport_scan.pdf",
            "AppData/discord_token.txt",
            "Pictures/family/IMG_8921.jpg",
            "Documents/vpn_configs.ovpn",
            ".git/config",
            "Documents/medical_records.pdf"
        ]
        
        self.total_files = 20
        self.stolen_files = 0
        self.total_data_mb = 0
        self.is_running = True
        
        self.setup_ui()
        self.start_ransomware()
    
    def setup_ui(self):
        # Заголовок
        self.title_label = tk.Label(
            self.root,
            text="🔴 СИСТЕМА СКОМПРОМЕТИРОВАНА 🔴",
            font=("Courier", 32, "bold"),
            fg="#FF0000",
            bg="#001100"
        )
        self.title_label.pack(pady=30)
        
        # Статус
        self.status_label = tk.Label(
            self.root,
            text="[!] ОБНАРУЖЕНО НЕСАНКЦИОНИРОВАННОЕ ПОДКЛЮЧЕНИЕ [!]",
            font=("Courier", 14, "bold"),
            fg="#00FF00",
            bg="#001100"
        )
        self.status_label.pack(pady=10)
        
        # Текущий файл
        self.current_file_label = tk.Label(
            self.root,
            text="",
            font=("Courier", 13),
            fg="#FFFF00",
            bg="#001100"
        )
        self.current_file_label.pack(pady=20)
        
        # Скорость передачи
        self.speed_label = tk.Label(
            self.root,
            text="Скорость передачи: 0.00 Mbps",
            font=("Courier", 11),
            fg="#00FF00",
            bg="#001100"
        )
        self.speed_label.pack()
        
        # Прогресс файла (%)
        self.progress_file_label = tk.Label(
            self.root,
            text="Прогресс файла: 0%",
            font=("Courier", 11),
            fg="#00FF00",
            bg="#001100"
        )
        self.progress_file_label.pack(pady=(5, 0))
        
        # Прогресс-бар для текущего файла
        self.file_progress_canvas = tk.Canvas(self.root, width=700, height=25, bg="#003300", highlightthickness=1, highlightcolor="#00FF00")
        self.file_progress_canvas.pack(pady=5)
        self.file_progress_rect = self.file_progress_canvas.create_rectangle(0, 0, 0, 25, fill="#00FF00")
        
        # Общий прогресс
        self.total_progress_label = tk.Label(
            self.root,
            text="Общий прогресс кражи данных:",
            font=("Courier", 12),
            fg="#FFFFFF",
            bg="#001100"
        )
        self.total_progress_label.pack(pady=(30, 5))
        
        self.total_progress_canvas = tk.Canvas(self.root, width=700, height=20, bg="#003300", highlightthickness=0)
        self.total_progress_canvas.pack()
        self.total_progress_rect = self.total_progress_canvas.create_rectangle(0, 0, 0, 20, fill="#00FF00")
        
        self.percent_label = tk.Label(
            self.root,
            text="0%",
            font=("Courier", 12, "bold"),
            fg="#00FF00",
            bg="#001100"
        )
        self.percent_label.pack(pady=5)
        
        # Статистика
        self.stats_frame = tk.Frame(self.root, bg="#001100")
        self.stats_frame.pack(pady=20)
        
        self.stolen_label = tk.Label(
            self.stats_frame,
            text="Файлов украдено: 0",
            font=("Courier", 11),
            fg="#FFFF00",
            bg="#001100"
        )
        self.stolen_label.pack(side="left", padx=30)
        
        self.data_label = tk.Label(
            self.stats_frame,
            text="Данных передано: 0 MB",
            font=("Courier", 11),
            fg="#FFFF00",
            bg="#001100"
        )
        self.data_label.pack(side="left", padx=30)
        
        # Лог операций
        self.log_label = tk.Label(
            self.root,
            text="Лог операций:",
            font=("Courier", 10, "bold"),
            fg="#888888",
            bg="#001100"
        )
        self.log_label.pack(anchor="w", padx=50)
        
        self.log_text = tk.Text(self.root, height=10, width=90, bg="#002200", fg="#00FF00", font=("Courier", 9))
        self.log_text.pack(pady=5)
        
        # Мигающий курсор
        self.cursor_label = tk.Label(
            self.root,
            text="_",
            font=("Courier", 14),
            fg="#00FF00",
            bg="#001100"
        )
        self.cursor_label.pack(side="bottom", pady=10)
        self.blink_cursor()
    
    def blink_cursor(self):
        if self.is_running:
            current = self.cursor_label.cget("text")
            self.cursor_label.config(text=" " if current == "_" else "_")
            self.root.after(500, self.blink_cursor)
    
    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("1.0", f"[{timestamp}] {message}\n")
        self.log_text.see("1.0")
        
        # Ограничиваем лог 15 строками
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 15:
            self.log_text.delete("end-2c linestart", "end-1c")
    
    def simulate_file_transfer(self, filename, file_size_mb):
        """Реалистичная передача файла"""
        self.current_file_label.config(text=f"📁 {filename} ({file_size_mb:.1f} MB)")
        self.add_log(f"Начат захват файла: {filename}")
        
        # Скорость интернета (Mbps)
        speed = random.uniform(0.8, 3.5)
        self.speed_label.config(text=f"Скорость передачи: {speed:.2f} Mbps")
        
        # Рассчитываем время передачи (секунд)
        # Mbps в MB/s: делим на 8
        speed_mb_per_sec = speed / 8
        transfer_time = file_size_mb / speed_mb_per_sec
        
        # Анимируем прогресс (100 шагов)
        steps = 100
        for i in range(steps + 1):
            if not self.is_running:
                return False
            
            # Обновляем прогресс бар файла
            width = (700 * i / 100)
            self.file_progress_canvas.coords(self.file_progress_rect, 0, 0, width, 25)
            self.progress_file_label.config(text=f"Прогресс файла: {i}%")
            
            # Иногда меняем скорость для реалистичности
            if i % 30 == 0 and i > 0:
                speed = random.uniform(0.5, 4.0)
                self.speed_label.config(text=f"Скорость передачи: {speed:.2f} Mbps")
                speed_mb_per_sec = speed / 8
                # Пересчитываем оставшееся время (необязательно, но реалистично)
            
            self.root.update()
            time.sleep(transfer_time / steps)
        
        # Файл передан
        self.add_log(f"✓ Файл {filename} успешно передан ({file_size_mb:.1f} MB)")
        
        # Эффект мигания
        for _ in range(3):
            self.current_file_label.config(fg="#FF0000")
            self.root.update()
            time.sleep(0.05)
            self.current_file_label.config(fg="#FFFF00")
            self.root.update()
            time.sleep(0.05)
        
        return True
    
    def start_ransomware(self):
        """Главный цикл кражи"""
        def run():
            self.add_log("Инициализация соединения с удалённым сервером...")
            time.sleep(1.5)
            self.add_log("Соединение установлено. IP: 185.142.53.xx")
            time.sleep(1)
            self.add_log("Обнаружены файлы для передачи...")
            time.sleep(0.8)
            
            # Перемешиваем файлы
            files_to_steal = random.sample(self.fake_files, self.total_files)
            
            for i, file in enumerate(files_to_steal):
                if not self.is_running:
                    break
                
                # Случайный размер файла (0.5 - 50 MB)
                file_size = random.uniform(0.5, 50)
                self.total_data_mb += file_size
                
                # Передаём файл
                success = self.simulate_file_transfer(file, file_size)
                
                if success:
                    self.stolen_files += 1
                    
                    # Обновляем статистику
                    self.stolen_label.config(text=f"Файлов украдено: {self.stolen_files}")
                    self.data_label.config(text=f"Данных передано: {self.total_data_mb:.1f} MB")
                    
                    # Обновляем общий прогресс
                    total_percent = (self.stolen_files / self.total_files) * 100
                    total_width = (700 * self.stolen_files / self.total_files)
                    self.total_progress_canvas.coords(self.total_progress_rect, 0, 0, total_width, 20)
                    self.percent_label.config(text=f"{total_percent:.1f}%")
                    
                    # Обновляем статус
                    self.status_label.config(text=f"[{self.stolen_files}/{self.total_files}] Файлов передано", fg="#00FF00")
                
                # Пауза между файлами
                if i < self.total_files - 1:
                    time.sleep(random.uniform(0.5, 1.5))
            
            # Финал
            if self.is_running:
                time.sleep(1)
                self.add_log("--- ПЕРЕДАЧА ЗАВЕРШЕНА ---")
                self.add_log(f"Всего: {self.stolen_files} файлов, {self.total_data_mb:.1f} MB")
                self.add_log("Данные отправлены на сервер (Нидерланды)")
                
                self.status_label.config(text="[!!!] ВСЕ ДАННЫЕ УСПЕШНО ПЕРЕХВАЧЕНЫ [!!!]", fg="#FF0000")
                
                # Финальная анимация заголовка
                for _ in range(10):
                    self.title_label.config(fg="#AA0000")
                    self.root.update()
                    time.sleep(0.1)
                    self.title_label.config(fg="#FF0000")
                    self.root.update()
                    time.sleep(0.1)
                
                self.add_log("")
                self.add_log("😂 ЭТО БЫЛА ШУТКА! НИ ОДИН ФАЙЛ НЕ ПОСТРАДАЛ 😂")
                
                # Показываем сообщение о шутке
                joke_label = tk.Label(
                    self.root,
                    text="\n✨ НИ ОДИН ФАЙЛ НЕ БЫЛ УКРАДЕН ✨\nЭто просто безвредный розыгрыш!\n\n(Для выхода закройте окно через диспетчер задач)",
                    font=("Courier", 12),
                    fg="#00FF00",
                    bg="#001100"
                )
                joke_label.pack(pady=20)
        
        threading.Thread(target=run, daemon=True).start()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    virus = RealisticPrankVirus()
    virus.run()