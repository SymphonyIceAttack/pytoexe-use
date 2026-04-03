import tkinter as tk
from tkinter import scrolledtext
import keyboard
import threading
import re

# ===================== БАЗА ДАННЫХ =====================
articles = []

def add_article(code, aid, title, text, keywords=None):
    terms = [aid.lower(), title.lower(), code.lower()]
    if keywords:
        terms.extend([k.lower() for k in keywords])
    articles.append({
        "code": code,
        "id": aid,
        "title": title,
        "text": text,
        "terms": terms
    })

# ===================== УГОЛОВНЫЙ КОДЕКС =====================
# Глава I
add_article("УК", "1.1", "Понятие преступления", "1.1 Преступление — виновно совершенное общественно опасное деяние, запрещенное под угрозой наказания.", ["преступление"])
add_article("УК", "1.4", "Покушение", "1.4 Покушение — умышленные действия, направленные на преступление, не доведённое до конца по независящим причинам.", ["покушение"])

# Глава VI
add_article("УК", "6.1", "Телесные повреждения", "6.1* Нанесение телесных повреждений — от 2 до 4 месяцев ЛС. Залог $1500", ["побои"])
add_article("УК", "6.2", "Убийство", "6.2** Убийство — 1 год ЛС.", ["убийство", "смерть"])

# Глава X
add_article("УК", "10.1", "Кража до $10000", "10.1* Кража до $10000 — до 4 месяцев ЛС. Залог $4000", ["кража"])
add_article("УК", "10.2", "Кража от $10001", "10.2* Кража от $10001 — до 8 месяцев ЛС. Залог $4000", ["кража"])
add_article("УК", "10.4", "Мошенничество", "10.4* Мошенничество — до 5 месяцев. Залог $3000", ["мошенничество"])
add_article("УК", "10.5", "Грабеж", "10.5** Грабеж — до 5 месяцев. Залог $3000", ["грабеж"])
add_article("УК", "10.6", "Разбой", "10.6** Разбой — до 5 месяцев. Залог $5000", ["разбой"])
add_article("УК", "10.7", "Угон", "10.7* Угон авто — до 4 месяцев. Залог $2000", ["угон"])

# Глава XV
add_article("УК", "15.4", "Получение взятки", "15.4** Получение взятки — от 3 до 4 лет ЛС.", ["взятка"])
add_article("УК", "15.4.1", "Дача взятки", "15.4.1** Дача взятки — от 1 до 2 лет ЛС.", ["взятка"])

# Глава XVII
add_article("УК", "17.1", "Посягательство на жизнь сотрудника", "17.1**** Посягательство на жизнь сотрудника госорганизации или их близких — 1 год ЛС.", ["посягательство", "сотрудник"])
add_article("УК", "17.2", "Насилие над сотрудником", "17.2* Применение насилия к сотруднику — 8 месяцев. Залог $5000", ["насилие"])
add_article("УК", "17.3", "Оскорбление сотрудника", "17.3 Оскорбление сотрудника — до 4 месяцев. Залог $2000", ["оскорбление"])
add_article("УК", "17.6", "Неповиновение", "17.6* Неповиновение сотруднику LSPD/LSSD/FIB — до 5 месяцев. Залог $5000", ["неповиновение"])
add_article("УК", "17.7", "Отказ от штрафа", "17.7* Отказ от оплаты штрафа — до 8 месяцев ЛС.", ["штраф"])

# ===================== АДМИНИСТРАТИВНЫЙ КОДЕКС =====================
# Глава 6
add_article("АК", "6.1", "Нарушение порядка проведения публичного мероприятия", "6.1 Штраф до $25.000", ["митинг", "собрание", "демонстрация", "пикетирование"])
add_article("АК", "6.2", "Наркотики (1-10 грамм)", "6.2 Незаконное хранение наркотиков до 10г — штраф до $20.000", ["наркотики"])
add_article("АК", "6.3", "Ложный вызов спецслужб", "6.3 Заведомо ложный вызов — штраф до $10.000", ["ложный вызов"])
add_article("АК", "6.4", "Введение в заблуждение госслужащих", "6.4 Попытка обмана сотрудников — штраф до $15.000", ["обман"])
add_article("АК", "6.5", "Воспрепятствование задержанию (гражданский)", "6.5 Вмешательство в процесс задержания — штраф до $20.000", ["вмешательство", "задержание"])
add_article("АК", "6.6", "Воспрепятствование задержанию (госслужащий)", "6.6 Штраф до $30.000", [])
add_article("АК", "6.7", "Сокрытие личности (маска)", "6.7 Ношение маски без причины — штраф до $15.000", ["маска", "балаклава"])
add_article("АК", "6.8", "Мелкое хулиганство", "6.8 Нарушение общественного порядка, нецензурная брань, драка, шум в госучреждениях — штраф до $15.000", ["хулиганство", "драка", "шум", "нецензурная брань"])
add_article("АК", "6.9", "Неприемлемый вид в общественных местах", "6.9 Нахождение без одежды, в белье или в состоянии опьянения — штраф до $15.000", ["голый", "опьянение", "алкоголь"])
add_article("АК", "6.10", "Нарушение закона об оружии (госслужащие)", "6.10 Штраф до $25.000", ["оружие"])
add_article("АК", "6.11", "Подделка документов на грузоперевозку", "6.11 Штраф $30.000", ["подделка", "груз"])

# Глава 7
add_article("АК", "7.1", "Оскорбление", "7.1 Унижение чести и достоинства — штраф до $10.000", ["оскорбление"])
add_article("АК", "7.2", "Публичное оскорбление", "7.2 Штраф до $10.000", [])
add_article("АК", "7.3", "Дискриминация", "7.3 Штраф до $15.000", ["дискриминация", "расизм"])
add_article("АК", "7.4", "Нарушение неприкосновенности частной жизни", "7.4 Телефонный терроризм, преследование — штраф до $30.000", ["частная жизнь", "преследование", "терроризм"])
add_article("АК", "7.5", "Повреждение чужого имущества", "7.5 Штраф до $10.000 + возмещение ущерба до $5.000", ["повреждение", "имущество"])
add_article("АК", "7.6", "Клевета с обвинением в преступлении", "7.6 Штраф до $10.000 + возмещение до $7.000", ["клевета"])
add_article("АК", "7.7", "Клевета", "7.7 Штраф до $10.000 + возмещение до $7.000", ["клевета"])

# Глава 8
add_article("АК", "8.1", "Превышение нормы вылова/охоты", "8.1 Штраф $5.000 за 1 кг сверх нормы (макс $100.000)", ["рыбалка", "охота", "вылов"])

# Глава 9
add_article("АК", "9.1", "Отсутствие медсправки (госслужащий)", "9.1 Штраф до $10.000", ["медсправка", "медицинская справка"])
add_article("АК", "9.2", "Отсутствие категорий в медсправке", "9.2 Штраф до $5.000", [])
add_article("АК", "9.3", "Воспрепятствование оказанию медпомощи", "9.3 Штраф до $20.000", ["медпомощь", "скорая"])

# Глава 10
add_article("АК", "10.1", "Халатность должностного лица", "10.1 Неисполнение обязанностей — штраф до $30.000", ["халатность", "должностное лицо"])

def search(query):
    q = query.strip().lower()
    if not q:
        return []
    exact = [a for a in articles if a["id"].lower() == q]
    if exact:
        return exact
    by_id = [a for a in articles if a["id"].lower().startswith(q)]
    if by_id and re.match(r'^\d+(\.\d+)?$', q):
        return by_id
    results = []
    for a in articles:
        if (q in a["id"].lower() or 
            q in a["title"].lower() or 
            q in a["text"].lower() or
            any(q in term for term in a["terms"])):
            results.append(a)
    return results

class SearchApp:
    def __init__(self):
        self.root = None
        self.setup_window()
        self.setup_hotkey()
    
    def setup_window(self):
        self.root = tk.Tk()
        self.root.title("⚖️ УК + АК Поиск — Сан-Андреас")
        self.root.geometry("1440x1080")
        self.root.configure(bg="#0a0e1a")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Заголовок
        title = tk.Label(self.root, text="УК + АК ПОИСК", font=("Segoe UI", 26, "bold"), fg="#ffd966", bg="#0a0e1a")
        title.pack(pady=20)
        
        sub = tk.Label(self.root, text="Введите номер (6.8, 17.1) или слово (хулиганство, кража, маска)", font=("Segoe UI", 12), fg="#8a92b0", bg="#0a0e1a")
        sub.pack()
        
        # Поле поиска
        frame = tk.Frame(self.root, bg="#141a2a")
        frame.pack(pady=20, padx=30, fill="x")
        
        self.entry = tk.Entry(frame, font=("Segoe UI", 16), bg="#1e2638", fg="white", insertbackground="white", relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", lambda e: self.do_search())
        
        btn = tk.Button(frame, text="🔍 НАЙТИ", font=("Segoe UI", 13, "bold"), bg="#2a6f5c", fg="white", relief="flat", cursor="hand2", command=self.do_search)
        btn.pack(side="right", padx=10, pady=10)
        
        # Результаты
        self.results = scrolledtext.ScrolledText(self.root, font=("Segoe UI", 12), bg="#101624", fg="#e0e4f0", wrap="word", relief="flat", padx=20, pady=20)
        self.results.pack(fill="both", expand=True, padx=30, pady=15)
        self.results.tag_configure("uk_title", font=("Segoe UI", 15, "bold"), foreground="#ff6666")
        self.results.tag_configure("ak_title", font=("Segoe UI", 15, "bold"), foreground="#66ff66")
        self.results.tag_configure("normal", font=("Segoe UI", 12), foreground="#e0e4f0")
        
        # Подсказки
        hint_frame = tk.Frame(self.root, bg="#0a0e1a")
        hint_frame.pack(pady=10)
        for word in ["17.1", "6.8", "покушение", "кража", "хулиганство", "маска", "клевета", "наркотики"]:
            b = tk.Button(hint_frame, text=word, font=("Segoe UI", 10), bg="#1a2235", fg="#b8c4e0", relief="flat", cursor="hand2", command=lambda w=word: self.set_search(w))
            b.pack(side="left", padx=6)
        
        self.status = tk.Label(self.root, text="Нажмите Alt+X для быстрого открытия", font=("Segoe UI", 10), fg="#4a5270", bg="#0a0e1a")
        self.status.pack(pady=8)
        
        # Центрирование
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1440 // 2)
        y = (self.root.winfo_screenheight() // 2) - (1080 // 2)
        self.root.geometry(f"1440x1080+{x}+{y}")
    
    def set_search(self, word):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, word)
        self.do_search()
    
    def do_search(self):
        query = self.entry.get()
        results = search(query)
        self.results.delete(1.0, tk.END)
        if not results:
            self.results.insert(tk.END, "❌ Ничего не найдено.\n\nПопробуйте: 17.1, 6.8, хулиганство, кража, маска", "normal")
            self.status.config(text="Ничего не найдено", fg="#cc5555")
            return
        self.status.config(text=f"Найдено: {len(results)}", fg="#55cc55")
        for r in results:
            tag = "uk_title" if r["code"] == "УК" else "ak_title"
            self.results.insert(tk.END, f"[{r['code']}] {r['id']} — {r['title']}\n", tag)
            self.results.insert(tk.END, f"{'─'*60}\n", "normal")
            self.results.insert(tk.END, f"{r['text']}\n\n", "normal")
    
    def show_window(self):
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.entry.focus()
    
    def hide_window(self):
        if self.root:
            self.root.withdraw()
    
    def setup_hotkey(self):
        def on_hotkey():
            if self.root:
                self.root.after(0, self.show_window)
        keyboard.add_hotkey("alt+x", on_hotkey)
    
    def run(self):
        if self.root:
            self.root.withdraw()
            self.root.mainloop()

if __name__ == "__main__":
    app = SearchApp()
    app.run()