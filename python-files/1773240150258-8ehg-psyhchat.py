import tkinter as tk
from tkinter import messagebox
import random

# ----------------------------------------------------------------------
# БАЗА ВОПРОСОВ (ВНИМАНИЕ, ЭМОЦИИ, СМЕШАННЫЕ)
# ----------------------------------------------------------------------

questions_attention = [
    {
        "question": "Какой термин обозначает снижение внимания?",
        "options": ["Апрозексия", "Гипопрозексия", "Гиперпрозексия", "Парапрозексия"],
        "correct": "Гипопрозексия",
        "explanation": "Гипопрозексия — снижение внимания (приставка «гипо-»)."
    },
    {
        "question": "Какая приставка означает «отсутствие»?",
        "options": ["Гипо-", "Гипер-", "А-", "Пара-"],
        "correct": "А-",
        "explanation": "Приставка «а-» означает отрицание, отсутствие."
    },
    {
        "question": "Что такое гиперпрозексия?",
        "options": ["Отсутствие внимания", "Снижение внимания", "Усиление внимания", "Искажение внимания"],
        "correct": "Усиление внимания",
        "explanation": "Гиперпрозексия — усиление внимания."
    },
    {
        "question": "Как называется неспособность длительно сосредотачиваться?",
        "options": ["Рассеянность", "Истощаемость", "Гиперфиксация", "Апрозексия"],
        "correct": "Рассеянность",
        "explanation": "Рассеянность — неспособность длительно сосредотачиваться."
    },
    {
        "question": "С чем часто сочетается рассеянность?",
        "options": ["С усилением памяти", "С истощаемостью внимания", "С гиперпрозексией", "С абулией"],
        "correct": "С истощаемостью внимания",
        "explanation": "Рассеянность часто сочетается с истощаемостью внимания."
    },
    {
        "question": "Что происходит при истощаемости внимания?",
        "options": [
            "Не может начать деятельность",
            "В начале сосредоточен, потом фиксация снижается",
            "Внимание усиливается к концу",
            "Не обращает внимания на стимулы"
        ],
        "correct": "В начале сосредоточен, потом фиксация снижается",
        "explanation": "Истощаемость — падение концентрации со временем."
    },
    {
        "question": "Какой термин обозначает полное отсутствие внимания?",
        "options": ["Гипопрозексия", "Апрозексия", "Гиперпрозексия", "Дизпрозексия"],
        "correct": "Апрозексия",
        "explanation": "Апрозексия — полное отсутствие внимания."
    },
    {
        "question": "От какого слова образованы термины расстройств внимания?",
        "options": ["Phren", "Mneme", "Prosexis", "Thymos"],
        "correct": "Prosexis",
        "explanation": "Prosexis (греч.) — внимание."
    },
    {
        "question": "Какое расстройство проявляется в повышенной отвлекаемости?",
        "options": ["Гиперпрозексия", "Апрозексия", "Гипопрозексия", "Все"],
        "correct": "Гипопрозексия",
        "explanation": "При гипопрозексии ребёнок легко отвлекается."
    },
    {
        "question": "При каком расстройстве ребёнок чрезмерно сосредоточен?",
        "options": ["Гипопрозексия", "Апрозексия", "Гиперпрозексия", "Ни при одном"],
        "correct": "Гиперпрозексия",
        "explanation": "Гиперпрозексия — патологическая фиксация."
    },
    {
        "question": "Рассеянность — это проявление:",
        "options": ["Гиперпрозексии", "Гипопрозексии", "Апрозексии", "Парапрозексии"],
        "correct": "Гипопрозексии",
        "explanation": "Рассеянность — основной симптом гипопрозексии."
    },
    {
        "question": "Приставка «гипер-» переводится как:",
        "options": ["Снижение", "Отсутствие", "Усиление", "Искажение"],
        "correct": "Усиление",
        "explanation": "Гипер- — усиление."
    },
    {
        "question": "Приставка «а-» переводится как:",
        "options": ["Снижение", "Отсутствие", "Усиление", "Искажение"],
        "correct": "Отсутствие",
        "explanation": "А- — отрицание, отсутствие."
    },
    {
        "question": "К количественным нарушениям НЕ относится:",
        "options": ["Гипопрозексия", "Апрозексия", "Гиперпрозексия", "Парапрозексия"],
        "correct": "Парапрозексия",
        "explanation": "Пара- означает искажение."
    }
]

questions_emotion = [
    {
        "question": "Что такое эйфория?",
        "options": ["Повышенное беспечное настроение", "Угрюмое раздражение", "Отсутствие эмоций", "Тревога"],
        "correct": "Повышенное беспечное настроение",
        "explanation": "Эйфория — повышенное настроение с беспечностью."
    },
    {
        "question": "Что такое дисфория?",
        "options": ["Повышенное настроение", "Злобно-тоскливое настроение", "Отсутствие эмоций", "Страх"],
        "correct": "Злобно-тоскливое настроение",
        "explanation": "Дисфория — угрюмое, раздражительное настроение."
    },
    {
        "question": "Что такое апатия?",
        "options": ["Повышенное настроение", "Отсутствие эмоций", "Тревога", "Страх"],
        "correct": "Отсутствие эмоций",
        "explanation": "Апатия — полное безразличие."
    },
    {
        "question": "Что такое тревога?",
        "options": ["Неясное чувство опасности", "Реакция на угрозу", "Повышенное настроение", "Отсутствие эмоций"],
        "correct": "Неясное чувство опасности",
        "explanation": "Тревога — недифференцированное чувство угрозы."
    },
    {
        "question": "Что такое страх?",
        "options": ["Неясное чувство опасности", "Чувство напряжённости при угрозе", "Отсутствие эмоций", "Повышенное настроение"],
        "correct": "Чувство напряжённости при угрозе",
        "explanation": "Страх — реакция на конкретную угрозу."
    },
    {
        "question": "Что такое амбивалентность?",
        "options": ["Двойственное отношение", "Отсутствие эмоций", "Страх", "Повышенное настроение"],
        "correct": "Двойственное отношение",
        "explanation": "Амбивалентность — противоположные чувства одновременно."
    },
    {
        "question": "Как называется кратковременная бурная эмоция?",
        "options": ["Настроение", "Аффект", "Страсть", "Эйфория"],
        "correct": "Аффект",
        "explanation": "Аффект — интенсивная эмоциональная реакция."
    },
    {
        "question": "Чем отличается патологический аффект?",
        "options": ["Длится дольше", "С помрачением сознания", "Без причины", "Ничем"],
        "correct": "С помрачением сознания",
        "explanation": "Патологический аффект — с помрачением сознания."
    },
    {
        "question": "Что такое гипотимия?",
        "options": ["Сниженное настроение", "Повышенное настроение", "Отсутствие эмоций", "Двойственность"],
        "correct": "Сниженное настроение",
        "explanation": "Гипотимия — снижение настроения."
    },
    {
        "question": "Что такое гипертимия?",
        "options": ["Сниженное настроение", "Повышенное настроение", "Отсутствие эмоций", "Тревога"],
        "correct": "Повышенное настроение",
        "explanation": "Гипертимия — повышенное настроение."
    },
    {
        "question": "Что такое растерянность?",
        "options": ["Недоумение", "Страх", "Тревога", "Апатия"],
        "correct": "Недоумение",
        "explanation": "Растерянность — непонимание ситуации."
    },
    {
        "question": "Какая эмоция относится к высшим?",
        "options": ["Голод", "Жажда", "Эстетическое наслаждение", "Страх"],
        "correct": "Эстетическое наслаждение",
        "explanation": "Высшие эмоции связаны с духовными потребностями."
    },
    {
        "question": "Какая эмоция относится к низшим?",
        "options": ["Любовь к искусству", "Чувство голода", "Патриотизм", "Дружба"],
        "correct": "Чувство голода",
        "explanation": "Низшие эмоции связаны с физиологическими потребностями."
    },
    {
        "question": "Что такое эйтимия?",
        "options": ["Ровное настроение", "Повышенное", "Сниженное", "Отсутствие"],
        "correct": "Ровное настроение",
        "explanation": "Эйтимия — нормальное настроение."
    },
    {
        "question": "Что такое страсть?",
        "options": ["Кратковременная эмоция", "Сильное стойкое чувство", "Отсутствие эмоций", "Страх"],
        "correct": "Сильное стойкое чувство",
        "explanation": "Страсть — длительное интенсивное чувство."
    }
]

questions_mixed = [
    {
        "question": "Какой термин относится к вниманию?",
        "options": ["Апатия", "Гипопрозексия", "Эйфория", "Дисфория"],
        "correct": "Гипопрозексия",
        "explanation": "Гипопрозексия — снижение внимания."
    },
    {
        "question": "Какая приставка означает «отсутствие»?",
        "options": ["Гипо-", "Гипер-", "А-", "Пара-"],
        "correct": "А-",
        "explanation": "А- — отсутствие (апатия, апрозексия)."
    },
    {
        "question": "Что такое апатия?",
        "options": ["Снижение внимания", "Отсутствие эмоций", "Усиление внимания", "Повышенное настроение"],
        "correct": "Отсутствие эмоций",
        "explanation": "Апатия — отсутствие эмоций."
    },
    {
        "question": "Что такое апрозексия?",
        "options": ["Отсутствие эмоций", "Отсутствие внимания", "Снижение внимания", "Повышенное настроение"],
        "correct": "Отсутствие внимания",
        "explanation": "Апрозексия — отсутствие внимания."
    },
    {
        "question": "Что такое эйфория?",
        "options": ["Повышенное настроение", "Снижение внимания", "Усиление внимания", "Злобное настроение"],
        "correct": "Повышенное настроение",
        "explanation": "Эйфория — эмоциональное расстройство."
    },
    {
        "question": "Что такое дисфория?",
        "options": ["Повышенное настроение", "Злобно-тоскливое", "Рассеянность", "Истощаемость"],
        "correct": "Злобно-тоскливое",
        "explanation": "Дисфория — угрюмое настроение."
    },
    {
        "question": "Какая приставка означает «усиление»?",
        "options": ["Гипо-", "Гипер-", "А-", "Пара-"],
        "correct": "Гипер-",
        "explanation": "Гипер- — усиление."
    },
    {
        "question": "Что такое гипопрозексия?",
        "options": ["Снижение внимания", "Повышенное настроение", "Сниженное настроение", "Отсутствие эмоций"],
        "correct": "Снижение внимания",
        "explanation": "Гипопрозексия — расстройство внимания."
    },
    {
        "question": "Что такое гиперпрозексия?",
        "options": ["Усиление внимания", "Повышенное настроение", "Снижение внимания", "Отсутствие эмоций"],
        "correct": "Усиление внимания",
        "explanation": "Гиперпрозексия — усиление внимания."
    },
    {
        "question": "Что такое гипотимия?",
        "options": ["Снижение внимания", "Сниженное настроение", "Повышенное настроение", "Отсутствие эмоций"],
        "correct": "Сниженное настроение",
        "explanation": "Гипотимия — пониженное настроение."
    },
    {
        "question": "Что такое гипертимия?",
        "options": ["Усиление внимания", "Повышенное настроение", "Снижение внимания", "Отсутствие эмоций"],
        "correct": "Повышенное настроение",
        "explanation": "Гипертимия — повышенное настроение."
    },
    {
        "question": "Рассеянность — это симптом:",
        "options": ["Гипопрозексии", "Эйфории", "Дисфории", "Апатии"],
        "correct": "Гипопрозексии",
        "explanation": "Рассеянность — при гипопрозексии."
    },
    {
        "question": "Что такое амбивалентность?",
        "options": ["Двойственность эмоций", "Снижение внимания", "Усиление внимания", "Отсутствие эмоций"],
        "correct": "Двойственность эмоций",
        "explanation": "Амбивалентность — двойственность чувств."
    },
    {
        "question": "Что такое тревога?",
        "options": ["Чувство опасности", "Снижение внимания", "Рассеянность", "Отсутствие эмоций"],
        "correct": "Чувство опасности",
        "explanation": "Тревога — эмоциональное расстройство."
    },
    {
        "question": "Качественные нарушения обозначаются приставкой:",
        "options": ["Гипо-", "Гипер-", "А-", "Пара-"],
        "correct": "Пара-",
        "explanation": "Пара- — искажение."
    }
]

# ----------------------------------------------------------------------
# ПРОФИЛИ
# ----------------------------------------------------------------------

profile_attention = """
🧠 ПРОФИЛЬ: ВНИМАНИЕ

Количественные нарушения:
• Гипопрозексия — снижение внимания
• Апрозексия — отсутствие внимания
• Гиперпрозексия — усиление внимания

Проявления:
• Рассеянность
• Истощаемость
"""

profile_emotion = """
❤️ ПРОФИЛЬ: ЭМОЦИИ

Нарушения настроения:
• Гипертимия — повышенное
• Гипотимия — пониженное
• Эйфория — беспечное
• Дисфория — злобное

Другие:
• Апатия — отсутствие эмоций
• Тревога, страх
• Амбивалентность
• Аффект
"""

profile_mixed = """
👩🏻‍🦰 ПРОФИЛЬ: ЗОЯ

ВНИМАНИЕ:
• Гипопрозексия (снижение)
• Апрозексия (отсутствие)
• Гиперпрозексия (усиление)

ЭМОЦИИ:
• Гипертимия, гипотимия
• Эйфория, дисфория
• Апатия, тревога, страх
"""

# ----------------------------------------------------------------------
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# ----------------------------------------------------------------------

class TelegramApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PsychoChat 🌸")
        self.root.geometry("1400x900")
        self.root.configure(bg="#e6d9f2")
        
        # Основной контейнер
        main_container = tk.Frame(self.root, bg="#e6d9f2")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Левая панель (список подруг)
        left_panel = tk.Frame(main_container, bg="#ffffff", width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Заголовок
        header = tk.Frame(left_panel, bg="#f8f0ff", height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🌸 PsychChat", font=("Arial", 24, "bold"), 
                bg="#f8f0ff", fg="#7b4b9a").pack(pady=25)
        
        # Приветствие
        tk.Label(left_panel, text="👋 Привет, подружка!", font=("Arial", 16), 
                bg="#ffffff", fg="#a569bd", anchor="w").pack(fill=tk.X, padx=20, pady=15)
        
        # Список подруг (убраны темы)
        friends_list = tk.Frame(left_panel, bg="#ffffff")
        friends_list.pack(fill=tk.BOTH, expand=True, padx=15)
        
        self.friend_buttons = []
        
        # Аня (Внимание)
        btn1 = self.create_friend_button(friends_list, "👩🏻 Аня", "#FFB6C1")
        btn1.pack(fill=tk.X, pady=5)
        btn1.bind("<Button-1>", lambda e: self.open_chat("attention"))
        self.friend_buttons.append(btn1)
        
        # Лена (Эмоции)
        btn2 = self.create_friend_button(friends_list, "👩🏼 Лена", "#40E0D0")
        btn2.pack(fill=tk.X, pady=5)
        btn2.bind("<Button-1>", lambda e: self.open_chat("emotion"))
        self.friend_buttons.append(btn2)
        
        # Зоя (Внимание + Эмоции)
        btn3 = self.create_friend_button(friends_list, "👩🏻‍🦰 Зоя", "#D8BFD8")
        btn3.pack(fill=tk.X, pady=5)
        btn3.bind("<Button-1>", lambda e: self.open_chat("mixed"))
        self.friend_buttons.append(btn3)
        
        # Правая панель (чат с выбранной подругой)
        self.right_panel = tk.Frame(main_container, bg="#ffffff")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.show_welcome()
        
        self.current_chat_type = None
        self.root.mainloop()
    
    def create_friend_button(self, parent, name, color):
        frame = tk.Frame(parent, bg="#f9f9f9", height=90)
        frame.pack_propagate(False)
        
        # Аватар
        avatar = tk.Label(frame, text=name[0], font=("Arial", 24), bg=color, fg="white")
        avatar.place(x=15, y=15, width=60, height=60)
        
        # Только имя (без темы)
        tk.Label(frame, text=name, font=("Arial", 16, "bold"),
                bg="#f9f9f9", fg="#333").place(x=90, y=25)
        
        # Статус
        tk.Label(frame, text="онлайн 🌸", font=("Arial", 12),
                bg="#f9f9f9", fg="#888").place(x=90, y=55)
        
        return frame
    
    def show_welcome(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.right_panel, bg="#ffffff")
        frame.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(frame, text="🌸 Добро пожаловать в PsychChat!", 
                font=("Arial", 28, "bold"), bg="#ffffff", fg="#7b4b9a").pack(pady=100)
        tk.Label(frame, text="Выбери подружку слева, чтобы начать 💕", 
                font=("Arial", 18), bg="#ffffff", fg="#a569bd").pack()
    
    def open_chat(self, chat_type):
        # Подсветка выбранной подруги
        colors = ["#f9f9f9", "#f9f9f9", "#f9f9f9"]
        idx = ["attention", "emotion", "mixed"].index(chat_type)
        colors[idx] = "#e8d9f0"
        
        for i, btn in enumerate(self.friend_buttons):
            btn.config(bg=colors[i])
        
        # Очищаем правую панель
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # Создаём чат с выбранной подругой
        if chat_type == "attention":
            self.current_chat = ChatFrame(self.right_panel, "Аня", questions_attention, 
                                         profile_attention, "👩🏻", "#FFB6C1")
        elif chat_type == "emotion":
            self.current_chat = ChatFrame(self.right_panel, "Лена", questions_emotion, 
                                         profile_emotion, "👩🏼", "#40E0D0")
        else:
            self.current_chat = ChatFrame(self.right_panel, "Зоя", questions_mixed, 
                                         profile_mixed, "👩🏻‍🦰", "#D8BFD8")

# ----------------------------------------------------------------------
# ЧАТ С ПОДРУГОЙ
# ----------------------------------------------------------------------

class ChatFrame:
    def __init__(self, parent, name, questions, profile_text, avatar, color):
        self.parent = parent
        self.name = name
        self.questions = questions.copy()
        self.current_q = 0
        self.waiting = False
        self.avatar = avatar
        self.color = color
        self.profile_text = profile_text
        
        # Основной фрейм
        main = tk.Frame(parent, bg="#ffffff")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Шапка чата
        header = tk.Frame(main, bg="#f8f0ff", height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Аватар в шапке
        tk.Label(header, text=avatar, font=("Arial", 28), 
                bg=color, fg="white").place(x=20, y=15, width=60, height=60)
        
        # Имя в шапке
        tk.Label(header, text=name, font=("Arial", 20, "bold"),
                bg="#f8f0ff", fg="#7b4b9a").place(x=100, y=25)
        
        # Статус
        tk.Label(header, text="онлайн", font=("Arial", 12),
                bg="#f8f0ff", fg="#888").place(x=100, y=55)
        
        # Кнопка профиля
        tk.Button(header, text=f"📋 Профиль {name}",
                 font=("Arial", 14), bg="white", fg="#7b4b9a", 
                 relief=tk.FLAT, padx=20, pady=8,
                 command=self.show_profile).place(x=700, y=20)
        
        # Область сообщений с прокруткой
        self.messages_frame = tk.Frame(main, bg="#f5f0fa")
        self.messages_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.canvas = tk.Canvas(self.messages_frame, bg="#f5f0fa", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.messages_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg="#f5f0fa")
        
        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки с вариантами ответов
        self.options = tk.Frame(main, bg="#f0e6fa", height=120)
        self.options.pack(fill=tk.X, side=tk.BOTTOM)
        self.options.pack_propagate(False)
        
        # Начинаем общение
        self.add_message(f"Привет! Я {name} 🌸", "bot")
        self.add_message(f"Сейчас проверю твои знания ✨", "bot")
        self.parent.after(500, self.ask_question)
    
    def add_message(self, text, sender):
        frame = tk.Frame(self.scrollable, bg="#f5f0fa")
        frame.pack(fill=tk.X, padx=40, pady=8)
        
        if sender == "bot":
            # Сообщение подруги слева
            left_frame = tk.Frame(frame, bg="#f5f0fa")
            left_frame.pack(anchor="w")
            
            # Аватар
            tk.Label(left_frame, text=self.avatar, font=("Arial", 16), 
                    bg=self.color, fg="white").pack(side=tk.LEFT, padx=(0, 10))
            
            # Текст
            tk.Label(left_frame, text=text, bg="white", fg="#333",
                    font=("Arial", 14), wraplength=600, justify=tk.LEFT,
                    padx=20, pady=12).pack(side=tk.LEFT)
        else:
            # Моё сообщение справа
            tk.Label(frame, text=text, bg="#40E0D0", fg="black",
                    font=("Arial", 14), wraplength=600, justify=tk.RIGHT,
                    padx=20, pady=12).pack(anchor="e")
        
        self.canvas.yview_moveto(1)
        self.parent.update()
    
    def show_profile(self):
        win = tk.Toplevel(self.parent)
        win.title(f"Профиль {self.name}")
        win.geometry("500x500")
        win.configure(bg="white")
        
        text = tk.Text(win, wrap=tk.WORD, font=("Arial", 14), bg="white", padx=20, pady=20)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, self.profile_text)
        text.config(state=tk.DISABLED)
    
    def ask_question(self):
        if self.current_q >= len(self.questions):
            self.add_message("✨ Ты молодец! Справилась со всеми вопросами! ✨", "bot")
            self.add_message("Ой, действительно! Ты просто умничка! 🌸", "bot")
            self.add_message("💕 Надеюсь, скоро ещё поболтаем! Пока, зайка! 👋", "bot")
            return
        
        self.waiting = False
        q = self.questions[self.current_q]
        self.add_message(f"❓ {q['question']}", "bot")
        
        # Очищаем старые кнопки
        for widget in self.options.winfo_children():
            widget.destroy()
        
        # Создаём новые кнопки
        for opt in q['options']:
            btn = tk.Button(self.options, text=opt, font=("Arial", 14),
                          bg="white", fg="#7b4b9a", relief=tk.FLAT,
                          padx=20, pady=10,
                          command=lambda o=opt, q=q: self.check_answer(o, q))
            btn.pack(side=tk.LEFT, padx=8, pady=15, ipadx=15, ipady=8, expand=True, fill=tk.X)
    
    def check_answer(self, selected, q):
        if self.waiting:
            return
        
        self.waiting = True
        self.add_message(selected, "user")
        
        if selected == q['correct']:
            praise = random.choice(['Молодец!', 'Отлично!', 'Супер!', 'Умничка!'])
            self.add_message(f"✅ О, действительно! {praise} 🌸", "bot")
        else:
            self.add_message(f"❌ Неправильно.\n{q['explanation']}", "bot")
        
        self.current_q += 1
        self.parent.after(1500, self.ask_question)

# ----------------------------------------------------------------------
# ЗАПУСК
# ----------------------------------------------------------------------

if __name__ == "__main__":
    app = TelegramApp()