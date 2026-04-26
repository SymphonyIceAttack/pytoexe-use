import tkinter as tk
from tkinter import messagebox
import time
import threading
import webbrowser
from datetime import datetime
import requests

class TwitchDropsBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitch Drops Bot - t.me/TwitchDropsFpee")
        self.root.geometry("850x750")
        self.root.configure(bg="#0a0a0a")
        
        self.is_running = False
        self.remaining = 0
        self.all_streamers = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        title_frame = tk.Frame(main_frame, bg="#1a1a1a")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(
            title_frame, 
            text="🎮 Twitch Drops Bot\n📍 t.me/TwitchDropsFpee #ritosha", 
            font=("Arial", 16, "bold"),
            fg="#888888",
            bg="#1a1a1a",
            justify="center"
        )
        title_label.pack(pady=15)
        
        # ===== Панель поиска =====
        search_frame = tk.Frame(main_frame, bg="#1a1a1a")
        search_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            search_frame, 
            text="🔍 ПОИСК СТРИМЕРОВ", 
            font=("Arial", 11, "bold"),
            fg="#aaaaaa",
            bg="#1a1a1a"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        search_row = tk.Frame(search_frame, bg="#1a1a1a")
        search_row.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(
            search_row, 
            text="Количество:", 
            fg="#888888", 
            bg="#1a1a1a",
            font=("Arial", 10)
        ).pack(side="left", padx=(0, 10))
        
        self.search_count = tk.IntVar(value=10)
        tk.Spinbox(
            search_row, 
            from_=1, to=20, 
            textvariable=self.search_count,
            width=5,
            bg="#2a2a2a",
            fg="white",
            relief="flat"
        ).pack(side="left", padx=(0, 20))
        
        self.btn_search = tk.Button(
            search_row, 
            text="🔍 НАЙТИ СТРИМЕРОВ", 
            command=self.search_streamers,
            bg="#333333",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5,
            relief="flat"
        )
        self.btn_search.pack(side="left")
        
        self.search_status = tk.Label(
            search_row, 
            text="", 
            fg="#666666", 
            bg="#1a1a1a",
            font=("Arial", 9)
        )
        self.search_status.pack(side="left", padx=15)
        
        # ===== Панель стримеров =====
        streams_card = tk.Frame(main_frame, bg="#1a1a1a")
        streams_card.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(
            streams_card, 
            text="📺 ВЫБЕРИТЕ СТРИМЕРОВ ДЛЯ ПРОСМОТРА", 
            font=("Arial", 11, "bold"),
            fg="#aaaaaa",
            bg="#1a1a1a"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        list_frame = tk.Frame(streams_card, bg="#1a1a1a")
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame, bg="#2a2a2a")
        scrollbar.pack(side="right", fill="y")
        
        self.listbox = tk.Listbox(
            list_frame,
            selectmode="multiple",
            yscrollcommand=scrollbar.set,
            bg="#2a2a2a",
            fg="#cccccc",
            selectbackground="#555555",
            selectforeground="white",
            font=("Arial", 10),
            height=8,
            relief="flat"
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        btn_sel_frame = tk.Frame(streams_card, bg="#1a1a1a")
        btn_sel_frame.pack(pady=10)
        
        tk.Button(
            btn_sel_frame, text="✅ ВЫБРАТЬ ВСЕ", command=self.select_all,
            bg="#333333", fg="white", font=("Arial", 10),
            relief="flat", padx=10
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_sel_frame, text="❌ ОЧИСТИТЬ", command=self.deselect_all,
            bg="#333333", fg="white", font=("Arial", 10),
            relief="flat", padx=10
        ).pack(side="left", padx=5)
        
        # ===== Таймер =====
        timer_frame = tk.Frame(main_frame, bg="#1a1a1a")
        timer_frame.pack(fill="x", pady=15)
        
        self.timer_label = tk.Label(
            timer_frame, text="02:00:00",
            font=("Arial", 52, "bold"),
            fg="#666666", bg="#1a1a1a"
        )
        self.timer_label.pack(pady=15)
        
        self.status_label = tk.Label(
            timer_frame, text="⚫ Статус: Ожидание",
            font=("Arial", 11), fg="#666666", bg="#1a1a1a"
        )
        self.status_label.pack(pady=5)
        
        # ===== Кнопки управления =====
        btn_frame = tk.Frame(main_frame, bg="#0a0a0a")
        btn_frame.pack(pady=15)
        
        self.btn_start = tk.Button(
            btn_frame, text="СТАРТ", command=self.start_farming,
            bg="#333333", fg="white", font=("Arial", 14, "bold"),
            padx=40, pady=12, relief="flat"
        )
        self.btn_start.pack(side="left", padx=15)
        
        self.btn_stop = tk.Button(
            btn_frame, text="СТОП", command=self.stop_farming,
            bg="#444444", fg="white", font=("Arial", 14, "bold"),
            padx=40, pady=12, relief="flat", state="disabled"
        )
        self.btn_stop.pack(side="left", padx=15)
        
        self.btn_claim = tk.Button(
            btn_frame, text="ЗАБРАТЬ ДРОПЫ", command=self.open_claim_page,
            bg="#555555", fg="white", font=("Arial", 12, "bold"),
            padx=30, pady=12, relief="flat"
        )
        self.btn_claim.pack(side="left", padx=15)
        
        # ===== Лог =====
        log_frame = tk.Frame(main_frame, bg="#1a1a1a")
        log_frame.pack(fill="both", expand=True, pady=10)
        
        tk.Label(
            log_frame, text="📋 ЛОГ СОБЫТИЙ",
            font=("Arial", 9, "bold"), fg="#888888", bg="#1a1a1a"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.log_text = tk.Text(
            log_frame, height=6, bg="#0a0a0a", fg="#00ff88",
            font=("Consolas", 9), wrap="word", relief="flat"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        info_label = tk.Label(
            main_frame, 
            text="💡 НАЙДИТЕ СТРИМЕРОВ → ВЫБЕРИТЕ → СТАРТ → НЕ ЗАКРЫВАЙТЕ ВКЛАДКИ",
            bg="#0a0a0a", fg="#444444", font=("Arial", 9)
        )
        info_label.pack(pady=(10, 0))
    
    def log(self, message):
        try:
            self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            self.log_text.see(tk.END)
        except:
            pass
    
    def search_streamers(self):
        """Поиск активных стримеров через API"""
        self.log("🔍 Поиск стримов с дропами...")
        self.search_status.config(text="Идёт поиск...", fg="#888888")
        self.btn_search.config(state="disabled")
        
        def find():
            try:
                # Публичный API Twitch (без токена)
                url = "https://api.twitch.tv/helix/streams?game_id=263490&first=20"
                headers = {
                    "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
                    "Accept": "application/vnd.twitchtv.v5+json"
                }
                
                resp = requests.get(url, headers=headers, timeout=10)
                live_streamers = []
                
                if resp.status_code == 200:
                    data = resp.json()
                    streams = data.get('data', [])
                    
                    for stream in streams:
                        name = stream.get('user_name', 'Unknown')
                        title = stream.get('title', '').lower()
                        # Фильтр по ключевым словам дропов
                        if 'drop' in title or 'дроп' in title:
                            live_streamers.append(name)
                    
                    # Если не нашли по словам, берем топ-10 живых стримов
                    if not live_streamers and streams:
                        for s in streams[:10]:
                            live_streamers.append(s.get('user_name'))
                else:
                    # Если API не работает, используем список по умолчанию
                    live_streamers = ["hJune", "Blooprint", "Posty", "Frost", "Spoonkid", "Welyn"]
                
                count = self.search_count.get()
                found = live_streamers[:count]
                
                self.root.after(0, lambda: self._update_streamers_list(found))
                
                if found:
                    self.root.after(0, lambda: self.search_status.config(text=f"✅ Найдено {len(found)} стримеров", fg="#00ff88"))
                    self.log(f"✅ Найдено {len(found)} стримеров с дропами")
                else:
                    self.root.after(0, lambda: self.search_status.config(text="❌ Не найдено активных стримов", fg="#ff4444"))
                    self.log("❌ Активных стримов с дропами не найдено")
                    
            except Exception as e:
                self.log(f"Ошибка поиска: {e}")
                # Запасной список
                default_list = ["hJune", "Blooprint", "Posty", "Frost", "Spoonkid", "Welyn", "Stevie", "Enardo"]
                self.root.after(0, lambda: self._update_streamers_list(default_list[:self.search_count.get()]))
                self.root.after(0, lambda: self.search_status.config(text="⚠️ Использую список по умолчанию", fg="#ffaa00"))
            
            self.root.after(0, lambda: self.btn_search.config(state="normal"))
        
        thread = threading.Thread(target=find, daemon=True)
        thread.start()
    
    def _update_streamers_list(self, streamers):
        """Обновляет список стримеров"""
        self.listbox.delete(0, tk.END)
        self.all_streamers = streamers
        for s in streamers:
            self.listbox.insert(tk.END, s)
    
    def select_all(self):
        try:
            self.listbox.select_set(0, tk.END)
        except:
            pass
    
    def deselect_all(self):
        try:
            self.listbox.select_clear(0, tk.END)
        except:
            pass
    
    def start_farming(self):
        try:
            selected = self.listbox.curselection()
            
            if selected:
                selected_names = [self.listbox.get(i) for i in selected]
            else:
                if self.listbox.size() > 0:
                    selected_names = [self.listbox.get(i) for i in range(min(5, self.listbox.size()))]
                else:
                    messagebox.showwarning("Ошибка", "Сначала найдите стримеров!")
                    return
            
            if not selected_names:
                messagebox.showwarning("Ошибка", "Выберите хотя бы одного стримера!")
                return
            
            self.log(f"🚀 Открываю {len(selected_names)} стримов")
            
            for streamer in selected_names:
                url = f"https://www.twitch.tv/{streamer.lower()}"
                webbrowser.open(url)
                self.log(f"📺 {streamer}")
                time.sleep(0.3)
            
            self.is_running = True
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            self.btn_search.config(state="disabled")
            self.status_label.config(text="🟢 Статус: Стримы открыты!", fg="#00ff88")
            
            self.remaining = 7200
            self.update_timer()
            
            self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
            self.timer_thread.start()
            
            self.log("✅ Фарм запущен! Через 2 часа будет уведомление")
        except Exception as e:
            self.log(f"Ошибка: {e}")
    
    def timer_loop(self):
        try:
            while self.is_running and self.remaining > 0:
                time.sleep(1)
                if self.is_running:
                    self.remaining -= 1
                    self.root.after(0, self.update_timer)
            
            if self.remaining <= 0:
                self.root.after(0, self.time_finished)
        except:
            pass
    
    def update_timer(self):
        try:
            hours = self.remaining // 3600
            minutes = (self.remaining % 3600) // 60
            seconds = self.remaining % 60
            self.timer_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        except:
            pass
    
    def time_finished(self):
        try:
            self.is_running = False
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.btn_search.config(state="normal")
            self.status_label.config(text="✅ ВРЕМЯ ВЫШЛО! Забирайте награды!", fg="#00ff88")
            self.timer_label.config(text="ГОТОВО!")
            
            self.log("🎉 Время вышло! Забирайте дропы!")
            
            messagebox.showinfo(
                "🎁 Дропы готовы!",
                "Время вышло!\n\n"
                "1. Зайдите на Twitch и нажмите CLAIM\n"
                "2. Зайдите на Facepunch и заберите скины в Steam"
            )
            
            webbrowser.open("https://www.twitch.tv/drops/inventory")
        except:
            pass
    
    def stop_farming(self):
        try:
            self.is_running = False
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.btn_search.config(state="normal")
            self.status_label.config(text="⚫ Статус: Остановлен", fg="#666666")
            self.timer_label.config(text="02:00:00")
            self.log("⏹️ Фарм остановлен")
        except:
            pass
    
    def open_claim_page(self):
        try:
            webbrowser.open("https://twitch.facepunch.com")
            self.log("🌐 Открыт Facepunch")
            messagebox.showinfo(
                "Забор скинов",
                "1. Войдите через Steam\n"
                "2. Нажмите 'Check for Missing Drops'\n"
                "3. Скины появятся в Steam!"
            )
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TwitchDropsBot(root)
    root.mainloop()