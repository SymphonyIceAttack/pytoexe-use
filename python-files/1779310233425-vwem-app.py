import os
import subprocess
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import threading

# Настраиваем внешний вид интерфейса
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class CookieExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Roblox Cookie Extractor (Fast Engine)")
        self.geometry("550x440")
        self.resizable(False, False)

        # Путь к Rar.exe
        self.rar_path = r"D:\Новая папка\Rar.exe"
        
        # Путь к выбранной папке
        self.selected_dir = ""
        
        # --- ИНТЕРФЕЙС ---
        self.label_title = ctk.CTkLabel(self, text="Сборщик кук из архивов и папок", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=20)

        # Выбор ПАПКИ
        self.frame_dir = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dir.pack(fill="x", padx=20, pady=5)
        
        self.entry_dir = ctk.CTkEntry(self.frame_dir, placeholder_text="Папка-источник не выбрана...", width=360)
        self.entry_dir.pack(side="left", padx=(0, 10))
        
        self.btn_browse = ctk.CTkButton(self.frame_dir, text="Выбрать папку", width=120, command=self.browse_directory)
        self.btn_browse.pack(side="left")

        # Ввод пароля
        self.label_pass = ctk.CTkLabel(self, text="Пароль от архивов (если собирается с нуля):")
        self.label_pass.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.frame_pass = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_pass.pack(fill="x", padx=20, pady=5)

        self.entry_pass = ctk.CTkEntry(self.frame_pass, width=380)
        self.entry_pass.insert(0, "https://t.me/AllLinksPrivate")
        self.entry_pass.pack(side="left", padx=(0, 10))

        self.entry_pass.bind("<Control-KeyPress>", self.handle_control_key)

        self.btn_clear_pass = ctk.CTkButton(self.frame_pass, text="Сбросить", width=100, fg_color="#c93b3b", hover_color="#a82e2e", command=self.clear_password_field)
        self.btn_clear_pass.pack(side="left")

        # Кнопка СТАРТ
        self.btn_start = ctk.CTkButton(self, text="СТАРТ", font=ctk.CTkFont(size=16, weight="bold"), width=500, height=40, command=self.start_processing_thread)
        self.btn_start.pack(padx=20, pady=15)

        # Консоль вывода (Лог)
        self.textbox_log = ctk.CTkTextbox(self, width=500, height=140)
        self.textbox_log.pack(padx=20, pady=10)
        self.log("Программа готова. Выберите папку и нажмите СТАРТ.")

    def handle_control_key(self, event):
        if event.keycode == 86:  # Ctrl + V
            try:
                cleaned_clipboard = self.clipboard_get().replace('\r', '').replace('\n', '')
                try:
                    if self.entry_pass.selection_get():
                        self.entry_pass.delete("sel.first", "sel.last")
                except:
                    pass
                self.entry_pass.insert(tk.INSERT, cleaned_clipboard)
            except:
                pass
            return "break"
        elif event.keycode == 67:  # Ctrl + C
            try:
                selected_text = self.entry_pass.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
            except:
                pass
            return "break"
        elif event.keycode == 65:  # Ctrl + A
            self.entry_pass.select_range(0, tk.END)
            self.entry_pass.icursor(tk.END)
            return "break"

    def log(self, message):
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.configure(state="disabled")
        self.textbox_log.see("end")
        self.update_idletasks()

    def clear_password_field(self):
        self.entry_pass.delete(0, tk.END)
        self.entry_pass.focus()

    def browse_directory(self):
        directory = filedialog.askdirectory(title="Выберите рабочую папку")
        if directory:
            self.selected_dir = os.path.normpath(directory)
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, self.selected_dir)
            self.log(f"[+] Выбрана папка: {self.selected_dir}")

    def start_processing_thread(self):
        if not self.selected_dir or not os.path.exists(self.selected_dir):
            self.log("[!] Ошибка: Сначала выберите корректную папку!")
            return

        self.btn_start.configure(state="disabled", text="ОБРАБОТКА...")
        self.btn_browse.configure(state="disabled")
        
        thread = threading.Thread(target=self.process_data, daemon=True)
        thread.start()

    def process_data(self):
        password = self.entry_pass.get()
        self.log("\n================ НАЧАЛО ОБРАБОТКИ ================")
        
        all_txt_path = os.path.join(self.selected_dir, "all.txt")
        output_file = os.path.join(self.selected_dir, "roblox_cookies.txt")

        # Если all.txt уже существует, пропускаем этап долгого поиска и сборки
        if os.path.exists(all_txt_path):
            self.log("[+] Найден готовый all.txt. Запуск моментальной фильтрации...")
        else:
            self.log("[!] Файл all.txt не найден. Собираю базу силами Windows...")
            
            # Быстрый консольный стриминг архивов через WinRAR одной строкой
            if os.path.exists(self.rar_path):
                # Находим все архивы в один проход командной строки и сливаем текстовики в all.txt
                rar_cmd = f'for /r "{self.selected_dir}" %i in (*.rar *.zip) do "{self.rar_path}" p -inul -p"{password}" "%i" *.txt >> "{all_txt_path}"'
                subprocess.run(rar_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Быстрое слияние обычных текстовиков из всех подпапок в один проход CMD
            combine_cmd = f'cd /d "{self.selected_dir}" && for /r %f in (*.txt) do ( if /i "%~nxf" neq "all.txt" if /i "%~nxf" neq "roblox_cookies.txt" type "%f" >> "all.txt" )'
            subprocess.run(combine_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Моментальный поиск кук через оригинальный findstr Windows (высокая скорость)
        if os.path.exists(all_txt_path) and os.path.getsize(all_txt_path) > 0:
            self.log("[+] Извлечение кук...")
            try:
                findstr_cmd = f'findstr /I "ROBLOSECURITY WARNING:-DO-NOT-SHARE-THIS" "{all_txt_path}" > "{output_file}"'
                subprocess.run(findstr_cmd, shell=True, stderr=subprocess.DEVNULL)
            except Exception as e:
                self.log(f"[!] Ошибка findstr: {e}")
        
        # Автоматическое удаление временного / исходного файла all.txt
        if os.path.exists(all_txt_path):
            self.log("[+] Очистка: удаление файла all.txt...")
            try:
                os.remove(all_txt_path)
            except Exception as e:
                self.log(f"[!] Не удалось автоматически удалить all.txt: {e}")

        # Проверка и вывод итоговых данных
        file_size_kb = 0
        if os.path.exists(output_file):
            file_size_kb = round(os.path.getsize(output_file) / 1024, 1)

        if file_size_kb > 0:
            self.log(f"\n[+] УСПЕШНО ЗАВЕРШЕНО!")
            self.log(f"[+] Вес файла кук: {file_size_kb} КБ")
            self.log(f"[+] Результат сохранен в: {output_file}")
        else:
            self.log("\n[X] Обработка завершена. Куки не найдены.")
            
        self.log("==================================================")
        self.restore_interface()

    def restore_interface(self):
        self.btn_start.configure(state="normal", text="СТАРТ")
        self.btn_browse.configure(state="normal")

if __name__ == "__main__":
    app = CookieExtractorApp()
    app.mainloop()