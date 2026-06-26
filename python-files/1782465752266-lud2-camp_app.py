import customtkinter as ctk
from tkinter import messagebox, simpledialog
import json
import sys
import os
from datetime import datetime

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class CampApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏕️ Приложение для лагеря")
        self.root.geometry("1400x800")
        
        self.squad_counter = 0
        self.children_data = {}
        self.editing_entry = None
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        self.patriot_row_widgets = {}
        self.patriot_all_days = []
        
        # Определяем путь к файлу данных (для .exe и для скрипта)
        if getattr(sys, 'frozen', False):
            self.data_file = os.path.join(os.path.dirname(sys.executable), "camp_data.json")
        else:
            self.data_file = os.path.join(os.path.dirname(__file__), "camp_data.json")
        
        self.tabview = ctk.CTkTabview(root)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        self.tabview.add("📋 Отряды")
        self.tabview.add("🏆 Патриоты")
        
        self._setup_squads_tab()
        self._setup_patriot_tab()
        
        # Загружаем данные при старте
        self.root.after(100, self._load_or_create_data)

    # ---------- ЗАГРУЗКА / СОХРАНЕНИЕ ДАННЫХ ----------
    def _load_or_create_data(self):
        """Загружает данные из JSON, если файл существует, иначе создаёт тестовые"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.children_data = loaded
                    self.squad_counter = len(self.children_data)
                    self._rebuild_all_from_data()
                    messagebox.showinfo("Загрузка", f"✅ Загружено {len(self.children_data)} отрядов")
                    return
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
        
        # Если файла нет или он повреждён – создаём тестовые
        self._create_test_data()

    def _create_test_data(self):
        """Создаёт тестовые отряды"""
        for i in range(2):
            self._add_squad()
        messagebox.showinfo("Новые данные", "Созданы тестовые отряды")

    def _rebuild_all_from_data(self):
        """Перестраивает все карточки отрядов из загруженных данных"""
        # Очищаем контейнер
        for widget in self.squads_container.winfo_children():
            widget.destroy()
        
        # Для каждого отряда в данных создаём карточку
        for squad_name, data in self.children_data.items():
            self._add_squad(squad_name, from_data=True)

    def _save_data(self):
        """Сохраняет данные в JSON"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.children_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Сохранено", f"✅ Сохранено {len(self.children_data)} отрядов")
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Не удалось сохранить: {e}")

    # ---------- ПРОКРУТКА ----------
    def _bind_scroll_events(self, widget, orientation="vertical"):
        if sys.platform == "darwin":
            widget.bind("<MouseWheel>", lambda e: self._on_mac_scroll(e, widget, orientation))
        else:
            widget.bind("<MouseWheel>", lambda e: self._on_scroll(e, widget, orientation))
            widget.bind("<Button-4>", lambda e: self._on_linux_scroll(e, widget, orientation, -1))
            widget.bind("<Button-5>", lambda e: self._on_linux_scroll(e, widget, orientation, 1))

    def _on_scroll(self, event, widget, orientation):
        delta = -1 if event.delta > 0 else 1
        if orientation == "vertical":
            widget._parent_canvas.yview_scroll(delta, "units")
        else:
            widget._parent_canvas.xview_scroll(delta, "units")
        return "break"

    def _on_mac_scroll(self, event, widget, orientation):
        delta = -1 if event.delta > 0 else 1
        if orientation == "vertical":
            widget._parent_canvas.yview_scroll(delta, "units")
        else:
            widget._parent_canvas.xview_scroll(delta, "units")
        return "break"

    def _on_linux_scroll(self, event, widget, orientation, direction):
        if orientation == "vertical":
            widget._parent_canvas.yview_scroll(direction, "units")
        else:
            widget._parent_canvas.xview_scroll(direction, "units")
        return "break"

    # ---------- ВКЛАДКА ОТРЯДЫ ----------
    def _setup_squads_tab(self):
        tab = self.tabview.tab("📋 Отряды")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(
            main_frame,
            orientation="horizontal",
            fg_color="transparent",
            scrollbar_button_color="#b0bec5",
            scrollbar_button_hover_color="#90a4ae"
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        
        self._bind_scroll_events(self.scrollable_frame, orientation="horizontal")
        
        self.squads_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.squads_container.pack(side="left", fill="both", expand=True, padx=5)
        
        control_frame = ctk.CTkFrame(tab, fg_color="transparent", height=60)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        control_frame.grid_columnconfigure(0, weight=1)
        
        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.pack()
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Добавить отряд",
            command=self._add_squad,
            corner_radius=10,
            fg_color="#4CAF50",
            hover_color="#66bb6a"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить данные",
            command=self._save_data,
            corner_radius=10,
            fg_color="#2196F3",
            hover_color="#42a5f5"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            control_frame,
            text="↔ Скролл вправо для просмотра всех отрядов",
            text_color="#78909c",
            font=("Segoe UI", 12)
        ).pack(side="right", padx=10)

    def _add_squad(self, squad_name=None, from_data=False):
        """Добавляет новый отряд. Если from_data=True, то использует данные из self.children_data"""
        if not from_data:
            self.squad_counter += 1
            if not squad_name:
                squad_name = f"Отряд №{self.squad_counter}"
            self.children_data[squad_name] = {
                "educators": [],
                "counselors": [],
                "junior_counselors": [],
                "children": []
            }
        else:
            # При загрузке из данных squad_name уже передан, и данные есть в self.children_data
            pass
        
        squad_data = self.children_data[squad_name]
        
        card = ctk.CTkFrame(
            self.squads_container,
            fg_color="#ffffff",
            corner_radius=15,
            border_width=2,
            border_color="#e0e0e0",
            width=580,
            height=700
        )
        card.pack(side="left", padx=15, pady=15, fill="both", expand=False)
        card.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            card,
            text=f"🌟 {squad_name}",
            font=("Segoe UI", 16, "bold"),
            text_color="#2c3e50"
        )
        title_label.pack(pady=(10, 5))
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=5)
        
        btn_frame = ctk.CTkFrame(inner, fg_color="#f8f9fa", corner_radius=8, height=45)
        btn_frame.pack(fill="x", pady=(0, 8))
        btn_frame.pack_propagate(False)
        
        btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_inner.pack(expand=True)
        
        buttons = [
            ("👶 Добавить ребёнка", "#FF9800", lambda: self._add_child(card)),
            ("👨‍🏫 Добавить вожатого", "#9C27B0", lambda: self._add_counselor(card)),
            ("👨‍🏫 Добавить воспитателя", "#E65100", lambda: self._add_educator(card)),
            ("🧑‍🤝‍🧑 Добавить мл.вожатого", "#00838F", lambda: self._add_junior(card)),
            ("✏️ Переименовать", "#78909c", lambda: self._rename_squad(card)),
            ("🗑️ Удалить", "#ef5350", lambda: self._delete_squad(card)),
        ]
        for text, color, cmd in buttons:
            ctk.CTkButton(
                btn_inner,
                text=text,
                command=cmd,
                fg_color=color,
                hover_color=self._get_hover_color(color),
                corner_radius=8,
                font=("Segoe UI", 8, "bold"),
                height=28,
                width=90
            ).pack(side="left", padx=3)
        
        # ----- Воспитатели -----
        edu_table = ctk.CTkFrame(inner, fg_color="#ffe0b2", corner_radius=6)
        edu_table.pack(fill="x", pady=(0, 4))
        edu_header = ctk.CTkFrame(edu_table, fg_color="#e65100", corner_radius=6)
        edu_header.pack(fill="x")
        ctk.CTkLabel(edu_header, text="👨‍🏫 ВОСПИТАТЕЛИ", text_color="white", font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=5)
        edu_rows = ctk.CTkFrame(edu_table, fg_color="#fff3e0")
        edu_rows.pack(fill="x")
        card.edu_rows = edu_rows
        
        # ----- Вожатые -----
        counselor_table = ctk.CTkFrame(inner, fg_color="#ce93d8", corner_radius=6)
        counselor_table.pack(fill="x", pady=(0, 4))
        counselor_header = ctk.CTkFrame(counselor_table, fg_color="#7b1fa2", corner_radius=6)
        counselor_header.pack(fill="x")
        ctk.CTkLabel(counselor_header, text="👨‍🏫 ВОЖАТЫЕ", text_color="white", font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=5)
        counselor_rows = ctk.CTkFrame(counselor_table, fg_color="#f3e5f5")
        counselor_rows.pack(fill="x")
        card.counselor_rows = counselor_rows
        
        # ----- Младшие вожатые -----
        junior_table = ctk.CTkFrame(inner, fg_color="#80deea", corner_radius=6)
        junior_table.pack(fill="x", pady=(0, 4))
        junior_header = ctk.CTkFrame(junior_table, fg_color="#00838F", corner_radius=6)
        junior_header.pack(fill="x")
        ctk.CTkLabel(junior_header, text="🧑‍🤝‍🧑 МЛАДШИЕ ВОЖАТЫЕ", text_color="white", font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=5)
        junior_rows = ctk.CTkFrame(junior_table, fg_color="#e0f7fa")
        junior_rows.pack(fill="x")
        card.junior_rows = junior_rows
        
        # ----- Дети -----
        children_table = ctk.CTkFrame(inner, fg_color="#cfd8dc", corner_radius=6)
        children_table.pack(fill="both", expand=True)
        children_header = ctk.CTkFrame(children_table, fg_color="#eceff1", corner_radius=6)
        children_header.pack(fill="x")
        ctk.CTkLabel(children_header, text="№", width=40, text_color="#37474f", font=("Segoe UI", 8, "bold")).pack(side="left", padx=3)
        ctk.CTkLabel(children_header, text="ФИО", text_color="#37474f", font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=3)
        ctk.CTkLabel(children_header, text="Дата рождения", width=100, text_color="#37474f", font=("Segoe UI", 8, "bold")).pack(side="left", padx=3)
        ctk.CTkLabel(children_header, text="", width=30).pack(side="left")
        
        children_scroll = ctk.CTkScrollableFrame(children_table, fg_color="transparent")
        children_scroll.pack(fill="both", expand=True, pady=4)
        self._bind_scroll_events(children_scroll, orientation="vertical")
        
        card.children_scroll = children_scroll
        card.squad_name = squad_name
        
        # Заполняем секции данными из squad_data
        # Воспитатели
        for e in squad_data["educators"]:
            self._add_educator(card, e["name"], from_data=True)
        # Вожатые
        for c in squad_data["counselors"]:
            self._add_counselor(card, c["name"], from_data=True)
        # Младшие вожатые
        for j in squad_data["junior_counselors"]:
            self._add_junior(card, j["name"], from_data=True)
        # Дети
        for child in squad_data["children"]:
            self._add_child(card, child["name"], child["birth"], from_data=True, number=child["number"], score_entries=child.get("score_entries", []))
        
        # Если это создание нового отряда (не из данных), добавляем тестовые данные
        if not from_data:
            self._add_test_data_to_card(card, squad_name)
        
        self.root.after(100, lambda: self._update_card_height(card))

    def _add_test_data_to_card(self, card, squad_name):
        """Добавляет тестовые данные в новый отряд"""
        # Тестовые данные уже добавлены в squad_data, но мы можем их перезаписать?
        # Лучше не перезаписывать, а просто если отряд новый, добавить.
        # Но в нашей логике новый отряд уже создан с пустыми списками, поэтому добавим тестовые.
        # Воспитатель
        test_educators = ["Светлана Ивановна Петрова"]
        for e in test_educators:
            self._add_educator(card, e)
        # Вожатый
        test_counselors = ["Анна Сергеевна Смирнова"]
        for c in test_counselors:
            self._add_counselor(card, c)
        # Младшие вожатые
        test_juniors = ["Дмитрий Алексеевич Иванов", "Екатерина Павловна Соколова"]
        for j in test_juniors:
            self._add_junior(card, j)
        # Дети
        test_names = [
            "Иванов Иван Иванович", "Петров Петр Петрович", "Сидоров Сидор Сидорович",
            "Кузнецова Анна Михайловна", "Смирнов Алексей Владимирович", "Попова Елена Дмитриевна",
            "Васильев Дмитрий Николаевич", "Михайлова Ольга Александровна"
        ]
        for i, name in enumerate(test_names, start=1):
            birth = f"{i:02d}.{i+5:02d}.2015"
            self._add_child(card, name, birth)

    def _update_card_height(self, card):
        # Не используется, так как высота фиксирована 700
        pass

    # ---------- МЕТОДЫ ДЛЯ ВОСПИТАТЕЛЕЙ ----------
    def _add_educator(self, card, name=None, from_data=False):
        if not from_data:
            if name is None:
                name = simpledialog.askstring("Добавить воспитателя", "Введите ФИО воспитателя:")
                if not name:
                    return
            squad_name = card.squad_name
            educators = self.children_data[squad_name]["educators"]
            if len(educators) >= 1:
                messagebox.showwarning("Ограничение", "Может быть только один воспитатель")
                return
            educators.append({"number": len(educators)+1, "name": name})
        self._update_educators_display(card)

    def _update_educators_display(self, card):
        for w in card.edu_rows.winfo_children():
            w.destroy()
        squad_name = card.squad_name
        for e in self.children_data[squad_name]["educators"]:
            row = ctk.CTkFrame(card.edu_rows, fg_color="#fff3e0")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=str(e["number"]), width=30, text_color="#e65100", font=("Segoe UI", 8)).pack(side="left", padx=3)
            lbl = ctk.CTkLabel(row, text=e["name"], text_color="#bf360c", font=("Segoe UI", 8, "bold"), anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=3)
            lbl.bind("<Button-1>", lambda ev, r=row, e=e: self._edit_educator(card, r, e))
            ctk.CTkButton(row, text="✕", width=24, height=20, fg_color="#e53935", hover_color="#c62828", corner_radius=4,
                         command=lambda e=e: self._delete_educator(card, e["number"])).pack(side="right", padx=3)

    def _edit_educator(self, card, row, educator):
        new = simpledialog.askstring("Редактирование", "Введите новое ФИО воспитателя:", initialvalue=educator["name"])
        if new:
            educator["name"] = new
            self._update_educators_display(card)

    def _delete_educator(self, card, number):
        squad_name = card.squad_name
        self.children_data[squad_name]["educators"] = [e for e in self.children_data[squad_name]["educators"] if e["number"] != number]
        self._renumber_educators(card)
        self._update_educators_display(card)

    def _renumber_educators(self, card):
        for idx, e in enumerate(self.children_data[card.squad_name]["educators"], start=1):
            e["number"] = idx

    # ---------- МЕТОДЫ ДЛЯ ВОЖАТЫХ ----------
    def _add_counselor(self, card, name=None, from_data=False):
        if not from_data:
            if name is None:
                name = simpledialog.askstring("Добавить вожатого", "Введите ФИО вожатого:")
                if not name:
                    return
            squad_name = card.squad_name
            counselors = self.children_data[squad_name]["counselors"]
            if len(counselors) >= 1:
                messagebox.showwarning("Ограничение", "Может быть только один вожатый")
                return
            counselors.append({"number": len(counselors)+1, "name": name})
        self._update_counselors_display(card)

    def _update_counselors_display(self, card):
        for w in card.counselor_rows.winfo_children():
            w.destroy()
        squad_name = card.squad_name
        for c in self.children_data[squad_name]["counselors"]:
            row = ctk.CTkFrame(card.counselor_rows, fg_color="#f3e5f5")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=str(c["number"]), width=30, text_color="#4a148c", font=("Segoe UI", 8)).pack(side="left", padx=3)
            lbl = ctk.CTkLabel(row, text=c["name"], text_color="#4a148c", font=("Segoe UI", 8, "bold"), anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=3)
            lbl.bind("<Button-1>", lambda ev, r=row, c=c: self._edit_counselor(card, r, c))
            ctk.CTkButton(row, text="✕", width=24, height=20, fg_color="#e53935", hover_color="#c62828", corner_radius=4,
                         command=lambda c=c: self._delete_counselor(card, c["number"])).pack(side="right", padx=3)

    def _edit_counselor(self, card, row, counselor):
        new = simpledialog.askstring("Редактирование", "Введите новое ФИО вожатого:", initialvalue=counselor["name"])
        if new:
            counselor["name"] = new
            self._update_counselors_display(card)

    def _delete_counselor(self, card, number):
        squad_name = card.squad_name
        self.children_data[squad_name]["counselors"] = [c for c in self.children_data[squad_name]["counselors"] if c["number"] != number]
        self._renumber_counselors(card)
        self._update_counselors_display(card)

    def _renumber_counselors(self, card):
        for idx, c in enumerate(self.children_data[card.squad_name]["counselors"], start=1):
            c["number"] = idx

    # ---------- МЕТОДЫ ДЛЯ МЛАДШИХ ВОЖАТЫХ ----------
    def _add_junior(self, card, name=None, from_data=False):
        if not from_data:
            if name is None:
                name = simpledialog.askstring("Добавить младшего вожатого", "Введите ФИО младшего вожатого:")
                if not name:
                    return
            squad_name = card.squad_name
            juniors = self.children_data[squad_name]["junior_counselors"]
            if len(juniors) >= 2:
                messagebox.showwarning("Ограничение", "Может быть не более двух младших вожатых")
                return
            juniors.append({"number": len(juniors)+1, "name": name})
        self._update_juniors_display(card)

    def _update_juniors_display(self, card):
        for w in card.junior_rows.winfo_children():
            w.destroy()
        squad_name = card.squad_name
        for j in self.children_data[squad_name]["junior_counselors"]:
            row = ctk.CTkFrame(card.junior_rows, fg_color="#e0f7fa")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=str(j["number"]), width=30, text_color="#00695c", font=("Segoe UI", 8)).pack(side="left", padx=3)
            lbl = ctk.CTkLabel(row, text=j["name"], text_color="#004d40", font=("Segoe UI", 8, "bold"), anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=3)
            lbl.bind("<Button-1>", lambda ev, r=row, j=j: self._edit_junior(card, r, j))
            ctk.CTkButton(row, text="✕", width=24, height=20, fg_color="#e53935", hover_color="#c62828", corner_radius=4,
                         command=lambda j=j: self._delete_junior(card, j["number"])).pack(side="right", padx=3)

    def _edit_junior(self, card, row, junior):
        new = simpledialog.askstring("Редактирование", "Введите новое ФИО младшего вожатого:", initialvalue=junior["name"])
        if new:
            junior["name"] = new
            self._update_juniors_display(card)

    def _delete_junior(self, card, number):
        squad_name = card.squad_name
        self.children_data[squad_name]["junior_counselors"] = [j for j in self.children_data[squad_name]["junior_counselors"] if j["number"] != number]
        self._renumber_juniors(card)
        self._update_juniors_display(card)

    def _renumber_juniors(self, card):
        for idx, j in enumerate(self.children_data[card.squad_name]["junior_counselors"], start=1):
            j["number"] = idx

    # ---------- МЕТОДЫ ДЛЯ ДЕТЕЙ ----------
    def _add_child(self, card, name=None, birth=None, from_data=False, number=None, score_entries=None):
        squad_name = card.squad_name
        children = self.children_data[squad_name]["children"]
        
        if not from_data:
            if name is None:
                name = "Новый ребёнок"
            if birth is None:
                birth = "01.01.2015"
            number = len(children) + 1
            children.append({
                "number": number,
                "name": name,
                "birth": birth,
                "score_entries": []
            })
        else:
            # при загрузке данные уже есть, просто используем их
            pass
        
        # Если передан number, значит это загрузка, ищем ребёнка по номеру
        if from_data and number is not None:
            child_data = next((c for c in children if c["number"] == number), None)
            if not child_data:
                return
            name = child_data["name"]
            birth = child_data["birth"]
            score_entries = child_data.get("score_entries", [])
        else:
            child_data = children[-1]  # только что добавленный
        
        # Создаём строку в интерфейсе
        row = ctk.CTkFrame(card.children_scroll, fg_color="transparent")
        row.pack(fill="x", pady=1)
        bg = "#f5f7fa" if (number-1)%2 else "#ffffff"
        row.configure(fg_color=bg)
        
        ctk.CTkLabel(row, text=str(number), width=40, text_color="#37474f", font=("Segoe UI", 8)).pack(side="left", padx=3)
        
        lbl_name = ctk.CTkLabel(row, text=name, text_color="#2c3e50", font=("Segoe UI", 8), anchor="w", cursor="hand2")
        lbl_name.pack(side="left", fill="x", expand=True, padx=3)
        lbl_name.bind("<Button-1>", lambda e, r=row, field="name": self._edit_child(card, r, field))
        lbl_name.bind("<Enter>", lambda e, l=lbl_name: l.configure(text_color="#1976d2"))
        lbl_name.bind("<Leave>", lambda e, l=lbl_name: l.configure(text_color="#2c3e50"))
        
        lbl_birth = ctk.CTkLabel(row, text=birth, width=100, text_color="#2c3e50", font=("Segoe UI", 8), cursor="hand2")
        lbl_birth.pack(side="left", padx=3)
        lbl_birth.bind("<Button-1>", lambda e, r=row, field="birth": self._edit_child(card, r, field))
        lbl_birth.bind("<Enter>", lambda e, l=lbl_birth: l.configure(text_color="#1976d2"))
        lbl_birth.bind("<Leave>", lambda e, l=lbl_birth: l.configure(text_color="#2c3e50"))
        
        ctk.CTkButton(row, text="✕", width=24, height=20, fg_color="#ef5350", hover_color="#c62828", corner_radius=4,
                     command=lambda: self._delete_child(card, row, number)).pack(side="right", padx=3)
        
        row.name_label = lbl_name
        row.birth_label = lbl_birth
        row.child_number = number

    def _edit_child(self, card, row, field):
        if field == "name":
            current = row.name_label.cget("text")
            new = simpledialog.askstring("Редактирование", "Введите новое ФИО:", initialvalue=current)
            if new and new.strip():
                new = new.strip()
                row.name_label.configure(text=new)
                squad_name = card.squad_name
                child_num = row.child_number
                for child in self.children_data[squad_name]["children"]:
                    if child["number"] == child_num:
                        child["name"] = new
                        break
        else:
            current = row.birth_label.cget("text")
            new = simpledialog.askstring("Редактирование", "Введите новую дату рождения (ДД.ММ.ГГГГ):", initialvalue=current)
            if new and new.strip():
                new = new.strip()
                row.birth_label.configure(text=new)
                squad_name = card.squad_name
                child_num = row.child_number
                for child in self.children_data[squad_name]["children"]:
                    if child["number"] == child_num:
                        child["birth"] = new
                        break

    def _delete_child(self, card, row, number):
        if messagebox.askyesno("Удаление", f"Удалить ребёнка №{number}?"):
            squad_name = card.squad_name
            self.children_data[squad_name]["children"] = [c for c in self.children_data[squad_name]["children"] if c["number"] != number]
            row.destroy()
            self._renumber_children(card)

    def _renumber_children(self, card):
        children = self.children_data[card.squad_name]["children"]
        children.sort(key=lambda x: x["number"])
        for idx, child in enumerate(children, start=1):
            child["number"] = idx
        for idx, row in enumerate(card.children_scroll.winfo_children(), start=1):
            for w in row.winfo_children():
                if isinstance(w, ctk.CTkLabel) and w.cget("width") == 40:
                    w.configure(text=str(idx))
                    break
            row.child_number = idx

    # ---------- ОБЩИЕ ДЕЙСТВИЯ ----------
    def _rename_squad(self, card):
        new = simpledialog.askstring("Переименование", "Введите новое название:", initialvalue=card.squad_name)
        if new:
            old = card.squad_name
            if old in self.children_data:
                self.children_data[new] = self.children_data.pop(old)
            card.squad_name = new
            for child in card.winfo_children():
                if isinstance(child, ctk.CTkLabel) and child.cget("font") == ("Segoe UI", 16, "bold"):
                    child.configure(text=f"🌟 {new}")
                    break

    def _delete_squad(self, card):
        squad_name = card.squad_name
        if messagebox.askyesno("Удаление", f"Удалить отряд «{squad_name}»?"):
            if squad_name in self.children_data:
                del self.children_data[squad_name]
            card.destroy()

    # ---------- ВКЛАДКА ПАТРИОТЫ ----------
    def _setup_patriot_tab(self):
        tab = self.tabview.tab("🏆 Патриоты")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=0)
        tab.grid_rowconfigure(1, weight=1)
        
        top_frame = ctk.CTkFrame(tab, fg_color="transparent", height=50)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        top_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkButton(
            top_frame,
            text="📊 Подвести итоги",
            command=self._refresh_patriot_table,
            corner_radius=10,
            fg_color="#4CAF50",
            hover_color="#66bb6a",
            width=150
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            top_frame,
            text="📈 ИТОГИ",
            command=self._open_summary_window,
            corner_radius=10,
            fg_color="#E65100",
            hover_color="#ef6c00",
            width=120
        ).pack(side="right", padx=5)
        
        self.patriot_table_frame = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        self.patriot_table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self._show_placeholder()

    def _show_placeholder(self):
        for widget in self.patriot_table_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.patriot_table_frame,
            text="👆 Нажмите «Подвести итоги» для отображения рейтинга",
            font=("Segoe UI", 16, "bold"),
            text_color="#78909c"
        ).pack(expand=True, fill="both", pady=100)

    # ---------- МЕТОДЫ ДЛЯ РАБОТЫ С БАЛЛАМИ ----------
    def _get_all_participants(self):
        participants = []
        for squad_name, data in self.children_data.items():
            for child in data["children"]:
                participants.append({
                    "name": child["name"],
                    "squad": squad_name,
                    "role": "Ребёнок",
                    "data_ref": child,
                    "is_junior": False
                })
            for junior in data["junior_counselors"]:
                participants.append({
                    "name": junior["name"],
                    "squad": squad_name,
                    "role": "Мл.вожатый",
                    "data_ref": junior,
                    "is_junior": True
                })
        return participants

    def _add_score_row(self, participant, category, points, day=None):
        if day is None:
            day = self.today
        if "score_entries" not in participant["data_ref"]:
            participant["data_ref"]["score_entries"] = []
        participant["data_ref"]["score_entries"].append({
            "day": day,
            "category": category,
            "points": points
        })
        self._update_participant_row(participant)

    def _update_participant_row(self, participant):
        key = (participant["name"], participant["squad"])
        widgets = self.patriot_row_widgets.get(key)
        if not widgets:
            self._refresh_patriot_table()
            return
        
        sport = 0
        intellect = 0
        work = 0
        total = 0
        for entry in participant["data_ref"].get("score_entries", []):
            if entry["category"] == "спорт":
                sport += entry["points"]
            elif entry["category"] == "интеллект":
                intellect += entry["points"]
            elif entry["category"] == "работа":
                work += entry["points"]
            total += entry["points"]
        
        widgets["sport_label"].configure(text=str(sport))
        widgets["intellect_label"].configure(text=str(intellect))
        widgets["work_label"].configure(text=str(work))
        widgets["total_label"].configure(text=str(total))
        
        if "day_labels" in widgets:
            day_labels = widgets["day_labels"]
            if len(day_labels) != len(self.patriot_all_days):
                self._refresh_patriot_table()
                return
            day_sums = {day: 0 for day in self.patriot_all_days}
            for entry in participant["data_ref"].get("score_entries", []):
                if entry["day"] in day_sums:
                    day_sums[entry["day"]] += entry["points"]
            for i, day in enumerate(self.patriot_all_days):
                day_labels[i].configure(text=str(day_sums[day]) if day_sums[day] else "")

    def _refresh_patriot_table(self):
        for widget in self.patriot_table_frame.winfo_children():
            widget.destroy()
        self.patriot_row_widgets.clear()
        
        participants = self._get_all_participants()
        if not participants:
            ctk.CTkLabel(self.patriot_table_frame, text="Нет участников для отображения", 
                         font=("Segoe UI", 14), text_color="#78909c").pack(expand=True, fill="both", pady=50)
            return
        
        all_days = set()
        for p in participants:
            for entry in p["data_ref"].get("score_entries", []):
                all_days.add(entry["day"])
        self.patriot_all_days = sorted(all_days)
        
        header = ctk.CTkFrame(self.patriot_table_frame, fg_color="#eceff1", corner_radius=8)
        header.pack(fill="x", pady=(0, 5))
        col_idx = 0
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=1); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        for _ in self.patriot_all_days:
            header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        header.grid_columnconfigure(col_idx, weight=0); col_idx += 1
        
        row_h = 0
        col = 0
        ctk.CTkLabel(header, text="№", width=40, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="ФИО", font=("Segoe UI", 8, "bold"), anchor="w").grid(row=row_h, column=col, sticky="ew", padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Отряд", width=100, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        for day in self.patriot_all_days:
            ctk.CTkLabel(header, text=day, width=80, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Спорт", width=50, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Интеллект", width=50, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Работа", width=50, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Сумма", width=60, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Действие", width=180, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        
        for p in participants:
            sport = 0
            intellect = 0
            work = 0
            total = 0
            for entry in p["data_ref"].get("score_entries", []):
                if entry["category"] == "спорт":
                    sport += entry["points"]
                elif entry["category"] == "интеллект":
                    intellect += entry["points"]
                elif entry["category"] == "работа":
                    work += entry["points"]
                total += entry["points"]
            p["sport"] = sport
            p["intellect"] = intellect
            p["work"] = work
            p["total"] = total
        
        participants.sort(key=lambda x: x["total"], reverse=True)
        
        for idx, p in enumerate(participants, start=1):
            row = ctk.CTkFrame(self.patriot_table_frame, fg_color="#f5f7fa" if idx % 2 == 0 else "white")
            row.pack(fill="x", pady=1)
            col_idx = 0
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=1); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            for _ in self.patriot_all_days:
                row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            row.grid_columnconfigure(col_idx, weight=0); col_idx += 1
            
            col = 0
            ctk.CTkLabel(row, text=str(idx), width=40, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=p["name"], font=("Segoe UI", 8), anchor="w").grid(row=0, column=col, sticky="ew", padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=p["squad"], width=100, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            
            day_sums = {day: 0 for day in self.patriot_all_days}
            for entry in p["data_ref"].get("score_entries", []):
                if entry["day"] in day_sums:
                    day_sums[entry["day"]] += entry["points"]
            day_labels = []
            for day in self.patriot_all_days:
                lbl = ctk.CTkLabel(row, text=str(day_sums[day]) if day_sums[day] else "", 
                                   width=80, font=("Segoe UI", 8))
                lbl.grid(row=0, column=col, padx=3, pady=2)
                day_labels.append(lbl)
                col += 1
            
            sport_lbl = ctk.CTkLabel(row, text=str(p["sport"]), width=50, font=("Segoe UI", 8))
            sport_lbl.grid(row=0, column=col, padx=3, pady=2); col += 1
            intellect_lbl = ctk.CTkLabel(row, text=str(p["intellect"]), width=50, font=("Segoe UI", 8))
            intellect_lbl.grid(row=0, column=col, padx=3, pady=2); col += 1
            work_lbl = ctk.CTkLabel(row, text=str(p["work"]), width=50, font=("Segoe UI", 8))
            work_lbl.grid(row=0, column=col, padx=3, pady=2); col += 1
            total_lbl = ctk.CTkLabel(row, text=str(p["total"]), width=60, font=("Segoe UI", 8, "bold"),
                                     text_color="#1976d2")
            total_lbl.grid(row=0, column=col, padx=3, pady=2); col += 1
            
            action_frame = ctk.CTkFrame(row, fg_color="transparent")
            action_frame.grid(row=0, column=col, padx=3, pady=2, sticky="w")
            col += 1
            
            cat_var = ctk.StringVar(value="спорт")
            cat_menu = ctk.CTkOptionMenu(action_frame, variable=cat_var, values=["спорт", "интеллект", "работа"],
                                         width=80, font=("Segoe UI", 8))
            cat_menu.pack(side="left", padx=2)
            
            points_var = ctk.StringVar(value="1")
            points_menu = ctk.CTkOptionMenu(action_frame, variable=points_var, values=["1", "2", "3"],
                                            width=50, font=("Segoe UI", 8))
            points_menu.pack(side="left", padx=2)
            
            add_btn = ctk.CTkButton(
                action_frame,
                text="➕",
                width=30,
                height=25,
                fg_color="#4CAF50",
                hover_color="#66bb6a",
                corner_radius=6,
                command=lambda p=p, cat_var=cat_var, points_var=points_var: 
                    self._add_score_row(p, cat_var.get(), int(points_var.get()), self.today)
            )
            add_btn.pack(side="left", padx=2)
            
            key = (p["name"], p["squad"])
            self.patriot_row_widgets[key] = {
                "sport_label": sport_lbl,
                "intellect_label": intellect_lbl,
                "work_label": work_lbl,
                "total_label": total_lbl,
                "day_labels": day_labels
            }

    # ---------- ОКНО ИТОГОВ ----------
    def _open_summary_window(self):
        summary_window = ctk.CTkToplevel(self.root)
        summary_window.title("📈 Итоги по категориям")
        summary_window.geometry("800x600")
        summary_window.resizable(True, True)
        summary_window.transient(self.root)
        summary_window.grab_set()
        
        main_frame = ctk.CTkScrollableFrame(summary_window, fg_color="white", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        header = ctk.CTkFrame(main_frame, fg_color="#eceff1", corner_radius=8)
        header.pack(fill="x", pady=(0, 5))
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)
        header.grid_columnconfigure(3, weight=0)
        header.grid_columnconfigure(4, weight=0)
        header.grid_columnconfigure(5, weight=0)
        
        row_h = 0
        col = 0
        ctk.CTkLabel(header, text="№", width=40, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="ФИО", font=("Segoe UI", 8, "bold"), anchor="w").grid(row=row_h, column=col, sticky="ew", padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Отряд", width=100, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Спорт", width=60, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Интеллект", width=60, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Работа", width=60, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        ctk.CTkLabel(header, text="Сумма", width=60, font=("Segoe UI", 8, "bold")).grid(row=row_h, column=col, padx=3, pady=3); col += 1
        
        participants = self._get_all_participants()
        if not participants:
            ctk.CTkLabel(main_frame, text="Нет данных для отображения", font=("Segoe UI", 14)).pack(pady=50)
            return
        
        summary_data = []
        for p in participants:
            sport = 0
            intellect = 0
            work = 0
            total = 0
            for entry in p["data_ref"].get("score_entries", []):
                if entry["category"] == "спорт":
                    sport += entry["points"]
                elif entry["category"] == "интеллект":
                    intellect += entry["points"]
                elif entry["category"] == "работа":
                    work += entry["points"]
                total += entry["points"]
            summary_data.append({
                "name": p["name"],
                "squad": p["squad"],
                "sport": sport,
                "intellect": intellect,
                "work": work,
                "total": total
            })
        summary_data.sort(key=lambda x: x["total"], reverse=True)
        
        for idx, row_data in enumerate(summary_data, start=1):
            row = ctk.CTkFrame(main_frame, fg_color="#f5f7fa" if idx % 2 == 0 else "white")
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0)
            row.grid_columnconfigure(3, weight=0)
            row.grid_columnconfigure(4, weight=0)
            row.grid_columnconfigure(5, weight=0)
            row.grid_columnconfigure(6, weight=0)
            
            col = 0
            ctk.CTkLabel(row, text=str(idx), width=40, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=row_data["name"], font=("Segoe UI", 8), anchor="w").grid(row=0, column=col, sticky="ew", padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=row_data["squad"], width=100, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=str(row_data["sport"]), width=60, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=str(row_data["intellect"]), width=60, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=str(row_data["work"]), width=60, font=("Segoe UI", 8)).grid(row=0, column=col, padx=3, pady=2); col += 1
            ctk.CTkLabel(row, text=str(row_data["total"]), width=60, font=("Segoe UI", 8, "bold"),
                         text_color="#1976d2").grid(row=0, column=col, padx=3, pady=2); col += 1
        
        ctk.CTkButton(
            summary_window,
            text="Закрыть",
            command=summary_window.destroy,
            corner_radius=10,
            fg_color="#ef5350",
            hover_color="#e57373",
            width=100
        ).pack(pady=10)

    # ---------- ДОПОЛНИТЕЛЬНО ----------
    @staticmethod
    def _get_hover_color(color):
        hover_map = {
            "#4CAF50": "#66bb6a",
            "#2196F3": "#42a5f5",
            "#FF9800": "#ffa726",
            "#9C27B0": "#ab47bc",
            "#E65100": "#ef6c00",
            "#00838F": "#0097a7",
            "#78909c": "#90a4ae",
            "#ef5350": "#e57373"
        }
        return hover_map.get(color, color)

if __name__ == "__main__":
    root = ctk.CTk()
    app = CampApp(root)
    root.mainloop()