import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time

CONFIG_FILE = "settings.json"
LOG_FILE = r"C:\search\123.txt"  # Укажите путь к вашему блокноту здесь

class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("КПП Ингур. Поиск Ориентировок")
        self.phrases = self.load_phrases()
        self.found_phrases = set()  # Множество для исключения повторных уведомлений

        # Интерфейс
        self.label = tk.Label(root, text="Введите номер документа (через запятую):")
        self.label.pack(pady=5)

        self.entry = tk.Entry(root, width=50)
        self.entry.insert(0, ", ".join(self.phrases))
        self.entry.pack(pady=5)

        self.btn = tk.Button(root, text="Поехали", command=self.start_search)
        self.btn.pack(pady=5)

        self.btn_reset = tk.Button(root, text="Сбросить историю находок", command=self.reset_search)
        self.btn_reset.pack(pady=5)

        self.running = False

    def load_phrases(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return []

    def save_phrases(self):
        phrases = [p.strip() for p in self.entry.get().split(",") if p.strip()]
        with open(CONFIG_FILE, "w") as f:
            json.dump(phrases, f)
        return phrases

    def reset_search(self):
        self.found_phrases.clear()
        messagebox.showinfo("Сброс", "История найденных фраз очищена.")

    def start_search(self):
        self.phrases = self.save_phrases()
        if not self.running:
            self.running = True
            threading.Thread(target=self.search_loop, daemon=True).start()

    def search_loop(self):
        while self.running:
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        lines = f.readlines()[-30:]

                    for phrase in self.phrases:
                        # Проверяем, не находили ли мы эту фразу ранее
                        if phrase not in self.found_phrases:
                            for line in lines:
                                if phrase in line:
                                    self.found_phrases.add(phrase)
                                    # Вызываем уведомление в основном потоке
                                    self.root.after(0, self.notify, phrase)
                                    break
            except Exception as e:
                print(f"Ошибка чтения файла: {e}")

            time.sleep(4)

    def notify(self, phrase):
        top = tk.Toplevel(self.root)
        top.attributes("-topmost", True)
        top.title("Найдено совпадение!")
        tk.Label(top, text=f"Найдена фраза:\n{phrase}", padx=20, pady=20).pack()
        tk.Button(top, text="ОК", command=top.destroy).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = SearchApp(root)
    root.mainloop()