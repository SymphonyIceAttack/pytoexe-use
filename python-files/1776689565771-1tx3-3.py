# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import font
import datetime
import random

class RudeClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Часы с характером")
        self.root.geometry("650x450")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)

        # Fonts
        self.clock_font = font.Font(family="Courier New", size=48, weight="bold")
        self.text_font = font.Font(family="Arial", size=13)

        # Clock label
        self.clock_frame = tk.Frame(root, bg="#1e1e1e")
        self.clock_frame.pack(pady=30)

        self.clock_label = tk.Label(
            self.clock_frame,
            text="",
            font=self.clock_font,
            fg="#00ff00",
            bg="#1e1e1e"
        )
        self.clock_label.pack()

        # Text area for insults
        self.text_frame = tk.Frame(root, bg="#1e1e1e")
        self.text_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.insult_text = tk.Text(
            self.text_frame,
            height=5,
            font=self.text_font,
            fg="#ff8888",
            bg="#2d2d2d",
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=15
        )
        self.insult_text.pack(fill="both", expand=True)
        self.insult_text.insert("1.0", "Нажми кнопку, чтобы услышать правду...")
        self.insult_text.configure(state="disabled")

        # Button frame
        self.button_frame = tk.Frame(root, bg="#1e1e1e")
        self.button_frame.pack(pady=20)

        self.rude_button = tk.Button(
            self.button_frame,
            text="⏰ КОТОРЫЙ ЧАС?! ⏰",
            font=("Arial", 14, "bold"),
            bg="#ff3333",
            fg="white",
            activebackground="#990000",
            activeforeground="white",
            relief="raised",
            borderwidth=3,
            padx=20,
            pady=10,
            command=self.insult_user
        )
        self.rude_button.pack()

        # Start clock update
        self.update_clock()

    def get_rude_time(self):
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        # Словарь часов с «завуалированной» бранью
        hour_insults = {
            0: "полночь-полуночница, чтоб тебе ни дна ни покрышки",
            1: "час быка, когда бесы хвосты чешут, а ты дрыхнешь, язви тя в корень",
            2: "второй час, глухая темень, волки воют, а твой храп их пугает",
            3: "три ночи, самое времечко удавиться, да ты и так уж полутруп",
            4: "четыре утра, петух трижды пропел, а ты всё не отпел, падаль сонная",
            5: "пять, заря занимается, а тебе хоть бы хны, лодырь стоеросовый",
            6: "шесть, роса умыла землю, но не твою немытую рожу, б*я",
            7: "семь, добры люди уж в поле, а ты всё как пень трухлявый",
            8: "восемь, солнце встало, тебя не спросило, и правильно, х*ли с тебя взять",
            9: "девять, блоха тебя укуси — подохнет от скуки, бездельник ты",
            10: "десять, самый расцвет тунеядства, едрёна вошь",
            11: "одиннадцать, обед близко, а ты не евши уже духом нищ, х*ли толку",
            12: "полдень, чёрт полуденный, разрази тебя гром среди ясного неба",
            13: "час пополудни, сонная одурь, мухи дохнут, глядя на твоё прозябание",
            14: "два, жара макушку печёт, а ты в тени как гнилой гриб, ё* твою медь",
            15: "три, время чай гонять, а ты слюни пускаешь, тля ты этакая",
            16: "четыре, день к закату, а ты ни с места, истукан неповоротливый",
            17: "пять, вечерняя зорька, а ты всё тот же охламон, ч*рт бы тебя побрал",
            18: "шесть, комарьё вьётся, а ты и не чешешься, бревно с глазами",
            19: "семь, сумерки сгущаются, как твоё невежество, ё-моё",
            20: "восемь, филин ухает, предрекая тебе пустую жизнь, х*ли ты тут забыл",
            21: "девять, ночь грядёт, а ты как был балбесом, так и остался",
            22: "десять, звёзды смеются над твоей бесполезностью, распронафиг",
            23: "одиннадцать, перед полночью самое время подумать о душе, но ты ж бездушный п*здюк"
        }

        # Минуты
        if minute == 0:
            minute_part = "— ровно, как топором отрубило, без затей"
        elif minute == 30:
            minute_part = "— половина, будто жизнь твоя надвое расколота"
        elif minute == 15:
            minute_part = "— четверть, пшик в масштабах вечности"
        elif minute == 45:
            minute_part = "— без четверти, почти уже ч*рт лапу наложил"
        else:
            minute_part = f"— и ещё {minute} минут, да чтоб они тебе поперёк горла встали"

        time_phrase = hour_insults.get(hour, f"{hour} часов, прости господи, неведомая х*рня")
        full_time = f"{time_phrase} {minute_part}".strip()

        # Оскорбления
        insults = [
            "Восстань из гроба лености, труп ходячий, е*аный в рот комар!",
            "Протри зенки бесстыжие, образина сонная, х*ли ты разлёгся, как падишах на минном поле?!",
            "Очнись, диванный выползень, жертва собственной беспомощности, ё* твою душу в три господа!",
            "Поднимай свой бренный остов, мешок с дерьмом космическим, б*я буду!",
            "Вставай, лежень заплесневелый, пуп земли дырявый, чтоб тебя е*и волами!",
            "Глянь на стрелки, чучело гороховое, с*ка ты эдакая, время-то тикает, пока ты тут бока отлёживаешь!",
            "Пробудись, убожество ходячее, п*здоглазое создание, ирод племенной!",
            "Шевелись, падаль малахольная, гнилушка человеческая, х*ли ты как сыч надулся?!",
            "Отлипни от перины, слизняк прямоходящий, едри твою в коромысло!",
            "Восстань, ленивое отребье, бесполезный нарост на теле человечества, ядрён-батон!",
            "Проснись, мумия недоделанная, кладбищенский упырь, х*ли ты тут забыл среди живых?!",
            "Встряхнись, гнида неповоротливая, б*я буду, ударю по ушам — не прочухаешься!",
            "Очнись, баклан залётный, п*зда тебе от жизни за такое лежание!",
            "Подъём, чмо болотное, с*ка ты ленивая, солнце уж в ж*пу светит, а ты всё дрыхнешь!"
        ]

        rude_greeting = random.choice(insults)
        return f"{rude_greeting} Сейчас-то у нас {full_time}!"

    def update_clock(self):
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.clock_label.config(text=time_str)
        self.root.after(1000, self.update_clock)

    def insult_user(self):
        message = self.get_rude_time()
        self.insult_text.configure(state="normal")
        self.insult_text.delete("1.0", tk.END)
        self.insult_text.insert("1.0", message)
        self.insult_text.configure(state="disabled")


if __name__ == "__main__":
    try:
        window = tk.Tk()
        app = RudeClock(window)
        window.mainloop()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        input("Нажмите Enter для выхода...")
