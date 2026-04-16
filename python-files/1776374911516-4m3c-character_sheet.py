import tkinter as tk
from tkinter import ttk, messagebox
import json
import random

class CharacterCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Создание листа персонажа D&D 5e")
        self.root.geometry("1000x950")
        self.root.resizable(True, True)
        
        # --- Системы характеристик и генерации ---
        self.max_points = 27
        
        self.str_var = tk.IntVar(value=10)
        self.dex_var = tk.IntVar(value=10)
        self.con_var = tk.IntVar(value=10)
        self.int_var = tk.IntVar(value=10)
        self.wis_var = tk.IntVar(value=10)
        self.cha_var = tk.IntVar(value=10)
        
        self.abilities = {
            "Сила": self.str_var,
            "Ловкость": self.dex_var,
            "Телосложение": self.con_var,
            "Интеллект": self.int_var,
            "Мудрость": self.wis_var,
            "Харизма": self.cha_var
        }
        
        self.base_abilities = {
            "Сила": 10, "Ловкость": 10, "Телосложение": 10,
            "Интеллект": 10, "Мудрость": 10, "Харизма": 10
        }
        
        # Расовые бонусы
        self.race_bonuses = {
            "Человек": {"Сила": 1, "Ловкость": 1, "Телосложение": 1, "Интеллект": 1, "Мудрость": 1, "Харизма": 1},
            "Эльф (Высший)": {"Ловкость": 2, "Интеллект": 1},
            "Эльф (Лесной)": {"Ловкость": 2, "Мудрость": 1},
            "Эльф (Темный - Дроу)": {"Ловкость": 2, "Харизма": 1},
            "Дварф (Холмовой)": {"Телосложение": 2, "Мудрость": 1},
            "Дварф (Горный)": {"Телосложение": 2, "Сила": 2},
            "Полурослик (Легконогий)": {"Ловкость": 2, "Харизма": 1},
            "Полурослик (Крепыш)": {"Ловкость": 2, "Телосложение": 1},
            "Драконорожденный": {"Сила": 2, "Харизма": 1},
            "Гном (Лесной)": {"Интеллект": 2, "Ловкость": 1},
            "Гном (Скальный)": {"Интеллект": 2, "Телосложение": 1},
            "Полуэльф": {"Харизма": 2},
            "Полуорк": {"Сила": 2, "Телосложение": 1},
            "Тифлинг": {"Интеллект": 1, "Харизма": 2}
        }
        
        # Требования классов
        self.class_requirements = {
            "Варвар": {"Сила": 13},
            "Бард": {"Харизма": 13},
            "Жрец": {"Мудрость": 13},
            "Друид": {"Мудрость": 13},
            "Воин": {"Сила": 13, "Ловкость": 13},
            "Монах": {"Ловкость": 13, "Мудрость": 13},
            "Паладин": {"Сила": 13, "Харизма": 13},
            "Следопыт": {"Ловкость": 13, "Мудрость": 13},
            "Плут": {"Ловкость": 13},
            "Чародей": {"Харизма": 13},
            "Колдун": {"Харизма": 13},
            "Волшебник": {"Интеллект": 13}
        }
        
        self.class_primary_ability = {
            "Варвар": "Сила", "Бард": "Харизма", "Жрец": "Мудрость",
            "Друид": "Мудрость", "Воин": "Сила", "Монах": "Ловкость",
            "Паладин": "Сила", "Следопыт": "Ловкость", "Плут": "Ловкость",
            "Чародей": "Харизма", "Колдун": "Харизма", "Волшебник": "Интеллект"
        }
        
        # Спасброски по классам
        self.class_saving_throws = {
            "Варвар": ["Сила", "Телосложение"],
            "Бард": ["Ловкость", "Харизма"],
            "Жрец": ["Мудрость", "Харизма"],
            "Друид": ["Интеллект", "Мудрость"],
            "Воин": ["Сила", "Телосложение"],
            "Монах": ["Сила", "Ловкость"],
            "Паладин": ["Мудрость", "Харизма"],
            "Следопыт": ["Сила", "Ловкость"],
            "Плут": ["Ловкость", "Интеллект"],
            "Чародей": ["Телосложение", "Харизма"],
            "Колдун": ["Мудрость", "Харизма"],
            "Волшебник": ["Интеллект", "Мудрость"]
        }
        
        # Навыки по характеристикам
        self.skills_by_ability = {
            "Сила": ["Атлетика"],
            "Ловкость": ["Акробатика", "Ловкость рук", "Скрытность"],
            "Телосложение": [],
            "Интеллект": ["Анализ", "История", "Магия", "Природа", "Религия"],
            "Мудрость": ["Внимательность", "Выживание", "Медицина", "Проницательность", "Уход за животными"],
            "Харизма": ["Выступление", "Запугивание", "Обман", "Убеждение"]
        }
        
        # Полный список навыков
        self.all_skills = []
        for skills in self.skills_by_ability.values():
            self.all_skills.extend(skills)
        
        # Навыки по классам
        self.class_skill_choices = {
            "Варвар": ["Атлетика", "Внимательность", "Выживание", "Запугивание", "Природа", "Уход за животными"],
            "Бард": ["Акробатика", "Анализ", "Атлетика", "Внимательность", "Выживание", "Выступление", 
                     "Запугивание", "История", "Ловкость рук", "Магия", "Медицина", "Обман", "Природа", 
                     "Проницательность", "Религия", "Скрытность", "Убеждение", "Уход за животными"],
            "Жрец": ["История", "Медицина", "Проницательность", "Религия", "Убеждение"],
            "Друид": ["Магия", "Внимательность", "Выживание", "Медицина", "Природа", "Проницательность", 
                      "Религия", "Уход за животными"],
            "Воин": ["Акробатика", "Анализ", "Атлетика", "Внимательность", "Выживание", "Запугивание", 
                     "История", "Проницательность", "Уход за животными"],
            "Монах": ["Акробатика", "Атлетика", "История", "Проницательность", "Религия", "Скрытность"],
            "Паладин": ["Атлетика", "Запугивание", "Медицина", "Проницательность", "Религия", "Убеждение"],
            "Следопыт": ["Атлетика", "Внимательность", "Выживание", "Природа", "Проницательность", 
                         "Скрытность", "Уход за животными"],
            "Плут": ["Акробатика", "Анализ", "Атлетика", "Внимательность", "Выступление", "Запугивание", 
                     "История", "Ловкость рук", "Обман", "Проницательность", "Скрытность", "Убеждение"],
            "Чародей": ["Магия", "Запугивание", "Обман", "Проницательность", "Религия", "Убеждение"],
            "Колдун": ["Магия", "Запугивание", "История", "Обман", "Природа", "Религия", "Убеждение"],
            "Волшебник": ["Анализ", "История", "Магия", "Медицина", "Религия"]
        }
        
        self.class_skill_count = {
            "Варвар": 2, "Бард": 3, "Жрец": 2, "Друид": 2, "Воин": 2,
            "Монах": 2, "Паладин": 2, "Следопыт": 3, "Плут": 4,
            "Чародей": 2, "Колдун": 2, "Волшебник": 2
        }
        
        # Предыстории
        self.backgrounds = {
            "Благородный": {"skills": ["История", "Убеждение"], "tools": ["Набор для игры в карты"], 
                           "languages": 1, "trait": "Привилегированное положение", "equipment": "Парадная одежда, перстень с печаткой"},
            "Моряк": {"skills": ["Атлетика", "Внимательность"], "tools": ["Инструменты навигатора", "Водный транспорт"], 
                     "languages": 0, "trait": "Крепкие морские ноги", "equipment": "Веревка (50 футов), шёлковый платок"},
            "Мудрец": {"skills": ["Магия", "История"], "tools": [], "languages": 2, 
                      "trait": "Исследователь", "equipment": "Чернила, перо, книга"},
            "Народный герой": {"skills": ["Уход за животными", "Выживание"], "tools": ["Инструменты ремесленника"], 
                              "languages": 0, "trait": "Гостеприимство простолюдинов", "equipment": "Лопата, железный котелок"},
            "Отшельник": {"skills": ["Медицина", "Религия"], "tools": ["Набор травника"], 
                         "languages": 1, "trait": "Открытие", "equipment": "Спальник, одеяло, травы"},
            "Преступник": {"skills": ["Скрытность", "Обман"], "tools": ["Воровские инструменты", "Набор для фальсификации"], 
                          "languages": 0, "trait": "Криминальные связи", "equipment": "Ломик, тёмная одежда с капюшоном"},
            "Странник": {"skills": ["Выступление", "Ловкость рук"], "tools": ["Маскировочный набор", "Музыкальный инструмент"], 
                        "languages": 0, "trait": "Фокусник", "equipment": "Костюм, колода карт"},
            "Чужеземец": {"skills": ["Атлетика", "Выживание"], "tools": ["Музыкальный инструмент"], 
                         "languages": 1, "trait": "Странник", "equipment": "Посох, карта местности"},
            "Шарлатан": {"skills": ["Обман", "Ловкость рук"], "tools": ["Набор для фальсификации"], 
                        "languages": 0, "trait": "Фальшивая личность", "equipment": "Поддельные документы, набор грима"},
            "Беспризорник": {"skills": ["Ловкость рук", "Скрытность"], "tools": ["Воровские инструменты", "Набор для грима"], 
                            "languages": 0, "trait": "Городские тайны", "equipment": "Маленький нож, карта города"},
            "Гильдейский ремесленник": {"skills": ["Анализ", "Убеждение"], "tools": ["Инструменты ремесленника"], 
                                       "languages": 1, "trait": "Член гильдии", "equipment": "Набор инструментов, письмо от гильдии"},
            "Солдат": {"skills": ["Атлетика", "Запугивание"], "tools": ["Игровой набор", "Транспорт (сухопутный)"], 
                      "languages": 0, "trait": "Воинское звание", "equipment": "Знак отличия, трофей с поля боя"}
        }
        
        self.races = list(self.race_bonuses.keys())
        self.classes = list(self.class_requirements.keys())
        self.background_names = list(self.backgrounds.keys())
        
        self.weapons = [
            "Боевой посох", "Булава", "Дубинка", "Кинжал", "Копье", 
            "Легкий арбалет", "Метательное копье", "Праща", "Ручной топор", "Серп",
            "Алебарда", "Боевой молот", "Боевой топор", "Двуручный меч", 
            "Длинный лук", "Длинный меч", "Короткий меч", "Рапира", "Тяжелый арбалет", "Ятаган"
        ]
        
        # Переменные для хранения выбора
        self.name_var = tk.StringVar(value="")
        self.race_var = tk.StringVar()
        self.class_var = tk.StringVar()
        self.background_var = tk.StringVar()
        self.weapon_var = tk.StringVar()
        
        self.level_var = tk.StringVar(value="1")
        self.alignment_var = tk.StringVar(value="Нейтральный")
        
        # Боевые показатели
        self.hp_var = tk.StringVar(value="10")
        self.ac_var = tk.StringVar(value="10")
        self.initiative_var = tk.StringVar(value="+0")
        self.speed_var = tk.StringVar(value="30 футов")
        
        # Поля для инвентаря
        self.equipment_text = tk.StringVar()
        self.proficiencies_text = tk.StringVar()
        self.languages_text = tk.StringVar()
        self.trait_text = tk.StringVar()
        
        # Состояние навыков (используем словарь bool вместо BooleanVar для контроля)
        self.skill_states = {skill: False for skill in self.all_skills}
        
        # Установка значений по умолчанию
        self.race_var.set(self.races[0])
        self.class_var.set(self.classes[0])
        self.background_var.set(self.background_names[0])
        self.weapon_var.set(self.weapons[0])
        
        self.remaining_points = tk.IntVar(value=self.max_points)
        self.ability_mode = tk.StringVar(value="pointbuy")
        self.selected_skills_count = 0
        self.max_skills = self.class_skill_count[self.classes[0]]
        
        # Отслеживание изменений
        self.race_var.trace_add("write", self.on_race_changed)
        self.class_var.trace_add("write", self.on_class_changed)
        self.background_var.trace_add("write", self.on_background_changed)
        self.level_var.trace_add("write", self.on_level_changed)
        
        self.create_widgets()
        self.apply_race_bonuses()
        self.update_all_modifiers()
        self.update_skill_list()
        self.update_proficiency_bonus()
        self.update_combat_stats()
        self.on_background_changed()
        self.update_saving_throws_display()
        
    # ================== МЕТОДЫ НАВЫКОВ (ИСПРАВЛЕННЫЕ) ==================
    def toggle_skill(self, skill_name):
        """Переключение галочки навыка с проверкой лимита"""
        if not self.skill_states[skill_name]:
            # Пытаемся ВКЛЮЧИТЬ навык
            if self.selected_skills_count >= self.max_skills:
                messagebox.showinfo("Ограничение", 
                    f"Вы уже выбрали максимум навыков для этого класса ({self.max_skills})")
                return
            self.skill_states[skill_name] = True
            self.selected_skills_count += 1
        else:
            # Выключаем навык
            self.skill_states[skill_name] = False
            self.selected_skills_count -= 1
        
        # Обновляем счетчик
        self.skill_count_label.config(text=f"{self.selected_skills_count}/{self.max_skills}")
        self.update_skill_bonuses()
        self.update_passive_perception()
    
    def update_skill_list(self):
        """Обновление списка доступных навыков при смене класса"""
        class_name = self.class_var.get()
        available_skills = self.class_skill_choices.get(class_name, [])
        
        # Сбрасываем все галочки
        for skill in self.all_skills:
            self.skill_states[skill] = False
        self.selected_skills_count = 0
        self.max_skills = self.class_skill_count.get(class_name, 2)
        
        # Обновляем чекбоксы
        for skill, cb in self.skill_checkboxes.items():
            if skill in available_skills:
                cb.config(state="normal")
            else:
                cb.config(state="disabled")
            # Снимаем выделение
            cb.deselect()
        
        # Обновляем счетчик
        self.skill_count_label.config(text=f"0/{self.max_skills}")
        self.update_skill_bonuses()
        self.update_passive_perception()
    
    def update_skill_bonuses(self):
        """Обновление бонусов навыков"""
        prof_bonus = self.get_proficiency_bonus()
        for skill in self.all_skills:
            if skill in self.skill_labels:
                for ability, skills in self.skills_by_ability.items():
                    if skill in skills:
                        ability_mod = self.calculate_modifier(self.abilities[ability].get())
                        total = ability_mod
                        if self.skill_states[skill]:
                            total += prof_bonus
                        sign = "+" if total >= 0 else ""
                        self.skill_labels[skill].config(text=f"{sign}{total}")
                        break
    
    # ================== ОСТАЛЬНЫЕ МЕТОДЫ ==================
    def on_race_changed(self, *args):
        self.apply_race_bonuses()
        self.update_combat_stats()
    
    def on_class_changed(self, *args):
        class_name = self.class_var.get()
        self.max_skills = self.class_skill_count.get(class_name, 2)
        self.update_skill_list()
        self.update_class_info()
        self.update_combat_stats()
        self.update_saving_throws_display()
    
    def on_background_changed(self, *args):
        bg = self.backgrounds[self.background_var.get()]
        self.trait_text.set(f"{bg['trait']}\nСнаряжение: {bg['equipment']}")
        tools_str = ", ".join(bg['tools']) if bg['tools'] else "Нет"
        self.proficiencies_text.set(f"Инструменты: {tools_str}")
        if bg['languages'] > 0:
            self.languages_text.set(f"+{bg['languages']} языка(ов) на выбор")
        else:
            self.languages_text.set("")
    
    def on_level_changed(self, *args):
        self.update_proficiency_bonus()
        self.update_combat_stats()
        self.update_saving_throws_display()
    
    def calculate_proficiency_bonus(self, level):
        if level < 5: return 2
        elif level < 9: return 3
        elif level < 13: return 4
        elif level < 17: return 5
        else: return 6
    
    def update_proficiency_bonus(self, *args):
        try:
            level = int(self.level_var.get())
            prof_bonus = self.calculate_proficiency_bonus(level)
            self.prof_bonus_label.config(text=f"+{prof_bonus}")
            self.update_skill_bonuses()
            self.update_saving_throws_display()
            self.update_passive_perception()
        except ValueError:
            pass
    
    def get_proficiency_bonus(self):
        try:
            return self.calculate_proficiency_bonus(int(self.level_var.get()))
        except:
            return 2
    
    def apply_race_bonuses(self):
        race = self.race_var.get()
        bonuses = self.race_bonuses.get(race, {})
        
        for ability in self.abilities:
            base = self.base_abilities.get(ability, 10)
            bonus = bonuses.get(ability, 0)
            self.abilities[ability].set(base + bonus)
        
        self.update_all_modifiers()
        self.update_skill_bonuses()
        self.update_saving_throws_display()
        self.update_passive_perception()
    
    def check_class_requirements(self):
        class_name = self.class_var.get()
        requirements = self.class_requirements.get(class_name, {})
        
        if class_name == "Воин":
            str_value = self.abilities["Сила"].get()
            dex_value = self.abilities["Ловкость"].get()
            if str_value >= 13 or dex_value >= 13:
                return True, []
            else:
                return False, [("Сила или Ловкость", 13)]
        
        unmet = []
        for ability, min_value in requirements.items():
            current = self.abilities[ability].get()
            if current < min_value:
                unmet.append((ability, min_value))
        
        return len(unmet) == 0, unmet
    
    def calculate_modifier(self, value):
        return (value - 10) // 2
    
    def roll_4d6_drop_lowest(self):
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls.sort(reverse=True)
        return sum(rolls[:3])
    
    def generate_rolled_stats(self):
        stats = []
        for _ in range(6):
            stats.append(self.roll_4d6_drop_lowest())
        stats.sort(reverse=True)
        return stats
    
    def apply_rolled_stats(self):
        stats = self.generate_rolled_stats()
        abilities_list = list(self.abilities.keys())
        for i, ability in enumerate(abilities_list):
            self.base_abilities[ability] = stats[i]
        self.apply_race_bonuses()
        self.update_remaining_points()
        self.update_all_modifiers()
        self.update_skill_bonuses()
        self.update_combat_stats()
        self.update_saving_throws_display()
    
    def calculate_point_cost(self, value):
        if value <= 8: return 0
        elif value == 9: return 1
        elif value == 10: return 2
        elif value == 11: return 3
        elif value == 12: return 4
        elif value == 13: return 5
        elif value == 14: return 7
        elif value == 15: return 9
        else: return 9 + (value - 15) * 2
    
    def update_remaining_points(self):
        total_cost = sum(self.calculate_point_cost(self.base_abilities[a]) for a in self.base_abilities)
        self.remaining_points.set(self.max_points - total_cost)
    
    def can_increase_ability(self, ability_name):
        if self.ability_mode.get() != "pointbuy":
            return True
        current_base = self.base_abilities.get(ability_name, 10)
        if current_base >= 15:
            return False
        new_cost = self.calculate_point_cost(current_base + 1)
        current_cost = self.calculate_point_cost(current_base)
        return self.remaining_points.get() >= (new_cost - current_cost)
    
    def can_decrease_ability(self, ability_name):
        if self.ability_mode.get() != "pointbuy":
            return True
        return self.base_abilities.get(ability_name, 10) > 8
    
    def increase_ability(self, ability_name):
        if self.ability_mode.get() == "pointbuy" and not self.can_increase_ability(ability_name):
            return
        self.base_abilities[ability_name] += 1
        self.apply_race_bonuses()
        self.update_remaining_points()
        self.update_all_modifiers()
        self.update_skill_bonuses()
        self.update_combat_stats()
        self.update_saving_throws_display()
    
    def decrease_ability(self, ability_name):
        if self.ability_mode.get() == "pointbuy" and not self.can_decrease_ability(ability_name):
            return
        self.base_abilities[ability_name] -= 1
        self.apply_race_bonuses()
        self.update_remaining_points()
        self.update_all_modifiers()
        self.update_skill_bonuses()
        self.update_combat_stats()
        self.update_saving_throws_display()
    
    def switch_ability_mode(self):
        if self.ability_mode.get() == "rolled":
            self.roll_button.config(state="normal")
            for btn in self.increase_buttons.values():
                btn.config(state="disabled")
            for btn in self.decrease_buttons.values():
                btn.config(state="disabled")
        else:
            self.roll_button.config(state="disabled")
            for btn in self.increase_buttons.values():
                btn.config(state="normal")
            for btn in self.decrease_buttons.values():
                btn.config(state="normal")
            for ability in self.base_abilities:
                self.base_abilities[ability] = 10
            self.apply_race_bonuses()
            self.update_remaining_points()
            self.update_all_modifiers()
            self.update_skill_bonuses()
            self.update_combat_stats()
    
    def update_modifier_label(self, ability_name):
        value = self.abilities[ability_name].get()
        modifier = self.calculate_modifier(value)
        sign = "+" if modifier >= 0 else ""
        self.modifier_labels[ability_name].config(text=f"{sign}{modifier}")
    
    def update_all_modifiers(self):
        for ability in self.abilities:
            self.update_modifier_label(ability)
    
    def update_race_info(self, *args):
        race = self.race_var.get()
        bonuses = self.race_bonuses.get(race, {})
        if bonuses:
            bonus_text = "Бонусы: " + ", ".join([f"{k} +{v}" for k, v in bonuses.items()])
            self.race_bonus_label.config(text=bonus_text)
        else:
            self.race_bonus_label.config(text="")
    
    def update_class_info(self, *args):
        class_name = self.class_var.get()
        requirements = self.class_requirements.get(class_name, {})
        primary = self.class_primary_ability.get(class_name, "")
        skill_count = self.class_skill_count.get(class_name, 2)
        
        if class_name == "Воин":
            req_text = f"Требования: Сила 13 ИЛИ Ловкость 13 | Навыки: {skill_count}"
        elif requirements:
            req_text = "Требования: " + ", ".join([f"{k} {v}" for k, v in requirements.items()])
            req_text += f" | Навыки: {skill_count}"
        else:
            req_text = f"Навыки: {skill_count}"
        
        if primary:
            req_text += f" | Осн: {primary}"
        
        self.class_req_label.config(text=req_text)
    
    def update_combat_stats(self):
        dex_mod = self.calculate_modifier(self.abilities["Ловкость"].get())
        con_mod = self.calculate_modifier(self.abilities["Телосложение"].get())
        
        self.ac_var.set(str(10 + dex_mod))
        self.initiative_var.set(f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod))
        
        # Расчет хитов
        hit_dice = 6
        class_name = self.class_var.get()
        if class_name in ["Варвар"]:
            hit_dice = 12
        elif class_name in ["Воин", "Паладин", "Следопыт"]:
            hit_dice = 10
        elif class_name in ["Бард", "Жрец", "Друид", "Монах", "Плут", "Колдун"]:
            hit_dice = 8
        
        try:
            level = int(self.level_var.get())
            hp = hit_dice + con_mod + (hit_dice // 2 + 1 + con_mod) * (level - 1)
            self.hp_var.set(str(max(hp, 1)))
        except:
            self.hp_var.set(str(hit_dice + con_mod))
        
        # Скорость
        race = self.race_var.get()
        if race in ["Дварф (Холмовой)", "Дварф (Горный)", "Гном (Лесной)", "Гном (Скальный)", 
                    "Полурослик (Легконогий)", "Полурослик (Крепыш)"]:
            speed = 25
        else:
            speed = 30
        self.speed_var.set(f"{speed} футов")
    
    def update_saving_throws_display(self):
        class_name = self.class_var.get()
        proficient_throws = self.class_saving_throws.get(class_name, [])
        prof_bonus = self.get_proficiency_bonus()
        
        for ability, frame in self.saving_throw_frames.items():
            ability_mod = self.calculate_modifier(self.abilities[ability].get())
            is_proficient = ability in proficient_throws
            total = ability_mod + (prof_bonus if is_proficient else 0)
            sign = "+" if total >= 0 else ""
            
            self.saving_throw_labels[ability].config(text=f"{sign}{total}")
            
            if is_proficient:
                self.saving_throw_checkboxes[ability].select()
            else:
                self.saving_throw_checkboxes[ability].deselect()
    
    def update_passive_perception(self):
        wis_mod = self.calculate_modifier(self.abilities["Мудрость"].get())
        prof_bonus = self.get_proficiency_bonus()
        has_prof = self.skill_states.get("Внимательность", False)
        passive = 10 + wis_mod + (prof_bonus if has_prof else 0)
        self.passive_perception_label.config(text=str(passive))
    
    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root, text="СОЗДАЙ СВОЕГО ГЕРОЯ", font=("Arial", 16, "bold"))
        title_label.pack(pady=5)
        
        # Основной контейнер с прокруткой
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        main_canvas.pack(side="left", fill="both", expand=True, padx=(10,0))
        scrollbar.pack(side="right", fill="y", padx=(0,10))
        
        # Основная форма
        form_frame = tk.Frame(scrollable_frame)
        form_frame.pack(pady=5, padx=10, fill="x")
        
        row = 0
        
        # === ОСНОВНАЯ ИНФОРМАЦИЯ ===
        info_frame = tk.LabelFrame(form_frame, text="Основная информация", font=("Arial", 10, "bold"))
        info_frame.grid(row=row, column=0, columnspan=4, pady=5, sticky="ew")
        
        tk.Label(info_frame, text="Имя:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        tk.Entry(info_frame, textvariable=self.name_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(info_frame, text="Уровень:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Spinbox(info_frame, from_=1, to=20, textvariable=self.level_var, width=5).grid(row=0, column=3, padx=5, pady=2)
        
        tk.Label(info_frame, text="Мировоззрение:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        alignments = ["Законно-добрый", "Нейтрально-добрый", "Хаотично-добрый", 
                     "Законно-нейтральный", "Нейтральный", "Хаотично-нейтральный",
                     "Законно-злой", "Нейтрально-злой", "Хаотично-злой"]
        ttk.Combobox(info_frame, textvariable=self.alignment_var, values=alignments, state="readonly", width=18).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(info_frame, text="Бонус мастерства:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.prof_bonus_label = tk.Label(info_frame, text="+2", font=("Arial", 11, "bold"), fg="#2980b9")
        self.prof_bonus_label.grid(row=1, column=3, padx=5, pady=2, sticky="w")
        
        row += 1
        
        # === БОЕВЫЕ ПОКАЗАТЕЛИ ===
        combat_frame = tk.LabelFrame(form_frame, text="Боевые показатели", font=("Arial", 10, "bold"), fg="#c0392b")
        combat_frame.grid(row=row, column=0, columnspan=4, pady=5, sticky="ew")
        
        tk.Label(combat_frame, text="КД:").grid(row=0, column=0, padx=5, pady=2)
        tk.Entry(combat_frame, textvariable=self.ac_var, width=5, state="readonly").grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(combat_frame, text="Хиты:").grid(row=0, column=2, padx=5, pady=2)
        tk.Entry(combat_frame, textvariable=self.hp_var, width=6, state="readonly").grid(row=0, column=3, padx=5, pady=2)
        
        tk.Label(combat_frame, text="Инициатива:").grid(row=1, column=0, padx=5, pady=2)
        tk.Entry(combat_frame, textvariable=self.initiative_var, width=5, state="readonly").grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(combat_frame, text="Скорость:").grid(row=1, column=2, padx=5, pady=2)
        tk.Entry(combat_frame, textvariable=self.speed_var, width=10, state="readonly").grid(row=1, column=3, padx=5, pady=2)
        
        tk.Label(combat_frame, text="Пассивная Внимательность:").grid(row=2, column=0, padx=5, pady=2)
        self.passive_perception_label = tk.Label(combat_frame, text="10", font=("Arial", 10, "bold"), fg="#27ae60")
        self.passive_perception_label.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
        row += 1
        
        # === ХАРАКТЕРИСТИКИ ===
        tk.Label(form_frame, text="ХАРАКТЕРИСТИКИ", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=4, pady=5)
        row += 1
        
        mode_frame = tk.Frame(form_frame)
        mode_frame.grid(row=row, column=0, columnspan=4, pady=3)
        
        tk.Radiobutton(mode_frame, text="Закуп (Point Buy)", variable=self.ability_mode, 
                       value="pointbuy", command=self.switch_ability_mode, font=("Arial", 10)).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Броски 4d6 drop lowest", variable=self.ability_mode, 
                       value="rolled", command=self.switch_ability_mode, font=("Arial", 10)).pack(side="left", padx=10)
        
        self.roll_button = tk.Button(mode_frame, text="🎲 Бросить", command=self.apply_rolled_stats, 
                                      bg="#3498db", fg="white", font=("Arial", 9))
        self.roll_button.pack(side="left", padx=20)
        self.roll_button.config(state="disabled")
        
        self.points_label = tk.Label(mode_frame, textvariable=self.remaining_points, 
                                      font=("Arial", 11, "bold"), fg="#e67e22")
        self.points_label.pack(side="left", padx=5)
        tk.Label(mode_frame, text="очков", font=("Arial", 9)).pack(side="left")
        row += 1
        
        # Заголовки таблицы характеристик
        headers = ["Характеристика", "Значение", "Модификатор", "Управление"]
        for col, header in enumerate(headers):
            tk.Label(form_frame, text=header, font=("Arial", 10, "bold"), 
                    bg="#34495e", fg="white", width=15 if col == 0 else 10).grid(
                    row=row, column=col, padx=1, pady=2)
        row += 1
        
        # Строки характеристик
        self.increase_buttons = {}
        self.decrease_buttons = {}
        self.modifier_labels = {}
        
        abilities_order = ["Сила", "Ловкость", "Телосложение", "Интеллект", "Мудрость", "Харизма"]
        
        for ability in abilities_order:
            var = self.abilities[ability]
            
            tk.Label(form_frame, text=ability, font=("Arial", 10)).grid(
                row=row, column=0, pady=2)
            
            tk.Label(form_frame, textvariable=var, font=("Arial", 11, "bold"), width=8).grid(
                row=row, column=1, pady=2)
            
            mod_label = tk.Label(form_frame, text="+0", font=("Arial", 11), fg="#27ae60", width=8)
            mod_label.grid(row=row, column=2, pady=2)
            self.modifier_labels[ability] = mod_label
            
            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=row, column=3, pady=2)
            
            dec_btn = tk.Button(btn_frame, text="-", width=2,
                               command=self.make_decrease_command(ability))
            dec_btn.pack(side="left", padx=2)
            self.decrease_buttons[ability] = dec_btn
            
            inc_btn = tk.Button(btn_frame, text="+", width=2,
                               command=self.make_increase_command(ability))
            inc_btn.pack(side="left", padx=2)
            self.increase_buttons[ability] = inc_btn
            
            row += 1
        
        # === СПАСБРОСКИ ===
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1
        
        tk.Label(form_frame, text="СПАСБРОСКИ", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=4, pady=5)
        row += 1
        
        saves_frame = tk.Frame(form_frame)
        saves_frame.grid(row=row, column=0, columnspan=4, pady=5)
        
        self.saving_throw_frames = {}
        self.saving_throw_labels = {}
        self.saving_throw_checkboxes = {}
        
        for i, ability in enumerate(abilities_order):
            frame = tk.Frame(saves_frame)
            frame.pack(side="left", padx=15, pady=5)
            self.saving_throw_frames[ability] = frame
            
            tk.Label(frame, text=ability, font=("Arial", 10, "bold")).pack()
            
            cb = tk.Checkbutton(frame, text="Владение", state="disabled")
            cb.pack()
            self.saving_throw_checkboxes[ability] = cb
            
            label = tk.Label(frame, text="+0", font=("Arial", 11, "bold"), fg="#8e44ad")
            label.pack()
            self.saving_throw_labels[ability] = label
        
        row += 1
        
        # === РАСА И КЛАСС ===
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1
        
        tk.Label(form_frame, text="Раса:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        race_combo = ttk.Combobox(form_frame, textvariable=self.race_var, 
                                  values=self.races, state="readonly", width=27)
        race_combo.grid(row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        self.race_bonus_label = tk.Label(form_frame, text="", font=("Arial", 9, "italic"), fg="#3498db")
        self.race_bonus_label.grid(row=row, column=1, columnspan=3, pady=2, padx=10, sticky="w")
        row += 1
        
        tk.Label(form_frame, text="Класс:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        class_combo = ttk.Combobox(form_frame, textvariable=self.class_var, 
                                   values=self.classes, state="readonly", width=27)
        class_combo.grid(row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        self.class_req_label = tk.Label(form_frame, text="", font=("Arial", 9, "italic"), fg="#e67e22")
        self.class_req_label.grid(row=row, column=1, columnspan=3, pady=2, padx=10, sticky="w")
        row += 1
        
        self.race_var.trace_add("write", self.update_race_info)
        self.class_var.trace_add("write", self.update_class_info)
        
        # === ПРЕДЫСТОРИЯ ===
        tk.Label(form_frame, text="Предыстория:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        bg_combo = ttk.Combobox(form_frame, textvariable=self.background_var, 
                                values=self.background_names, state="readonly", width=27)
        bg_combo.grid(row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        tk.Label(form_frame, text="Умение предыстории:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        tk.Entry(form_frame, textvariable=self.trait_text, width=60, state="readonly").grid(
            row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        # === НАВЫКИ ===
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1
        
        skills_header = tk.Frame(form_frame)
        skills_header.grid(row=row, column=0, columnspan=4, pady=5)
        tk.Label(skills_header, text="НАВЫКИ", font=("Arial", 12, "bold")).pack(side="left")
        
        self.skill_count_label = tk.Label(skills_header, text="0/2", font=("Arial", 11, "bold"), fg="#8e44ad")
        self.skill_count_label.pack(side="left", padx=20)
        tk.Label(skills_header, text="(отметьте владение)", font=("Arial", 9, "italic")).pack(side="left")
        row += 1
        
        self.skill_checkboxes = {}
        self.skill_labels = {}
        
        skills_container = tk.Frame(form_frame)
        skills_container.grid(row=row, column=0, columnspan=4, pady=5, sticky="w")
        
        col = 0
        for ability, skills in self.skills_by_ability.items():
            if not skills:
                continue
            
            ability_frame = tk.LabelFrame(skills_container, text=ability, font=("Arial", 9, "bold"), 
                                          fg="#2c3e50", padx=5, pady=5)
            ability_frame.grid(row=0, column=col, padx=5, pady=5, sticky="n")
            
            for skill in skills:
                skill_frame = tk.Frame(ability_frame)
                skill_frame.pack(anchor="w", pady=1)
                
                # Создаем чекбокс БЕЗ variable, только command
                cb = tk.Checkbutton(skill_frame, text=skill,
                                   command=lambda s=skill: self.toggle_skill(s),
                                   font=("Arial", 9), width=18, anchor="w")
                cb.pack(side="left")
                self.skill_checkboxes[skill] = cb
                
                bonus_label = tk.Label(skill_frame, text="+0", font=("Arial", 9, "bold"), 
                                       fg="#2980b9", width=4)
                bonus_label.pack(side="right")
                self.skill_labels[skill] = bonus_label
            
            col += 1
        
        row += 1
        
        # === ОРУЖИЕ ===
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1
        
        tk.Label(form_frame, text="Оружие:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        weapon_combo = ttk.Combobox(form_frame, textvariable=self.weapon_var, 
                                    values=self.weapons, state="readonly", width=27)
        weapon_combo.grid(row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        # === СНАРЯЖЕНИЕ И ВЛАДЕНИЯ ===
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=5)
        row += 1
        
        tk.Label(form_frame, text="Снаряжение и инвентарь:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        tk.Entry(form_frame, textvariable=self.equipment_text, width=60).grid(
            row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        tk.Label(form_frame, text="Владения:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        tk.Entry(form_frame, textvariable=self.proficiencies_text, width=60).grid(
            row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        tk.Label(form_frame, text="Языки:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=3)
        tk.Entry(form_frame, textvariable=self.languages_text, width=60).grid(
            row=row, column=1, columnspan=3, pady=3, padx=10, sticky="w")
        row += 1
        
        # === КНОПКИ ===
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=4, sticky="ew", pady=10)
        row += 1
        
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=4, pady=5)
        
        tk.Button(button_frame, text="📜 Создать лист", command=self.show_character_sheet, 
                 bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), padx=20, pady=5).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="💾 Сохранить в JSON", command=self.save_to_json, 
                 bg="#2196F3", fg="white", font=("Arial", 11, "bold"), padx=20, pady=5).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="🔄 Сбросить", command=self.reset_form, 
                 bg="#f44336", fg="white", font=("Arial", 10), padx=20, pady=5).pack(side="left", padx=5)
        
        self.update_race_info()
        self.update_class_info()
        self.update_skill_bonuses()
    
    def make_increase_command(self, ability_name):
        return lambda: self.increase_ability(ability_name)
    
    def make_decrease_command(self, ability_name):
        return lambda: self.decrease_ability(ability_name)
    
    def get_selected_skills(self):
        return [skill for skill, state in self.skill_states.items() if state]
    
    def show_character_sheet(self):
        if not self.name_var.get().strip():
            messagebox.showwarning("Внимание", "Пожалуйста, введите имя персонажа!")
            return
        
        meets_req, unmet = self.check_class_requirements()
        if not meets_req:
            if self.class_var.get() == "Воин":
                req_text = "Сила 13 ИЛИ Ловкость 13"
            else:
                req_text = ", ".join([f"{ability} {value}" for ability, value in unmet])
            
            response = messagebox.askyesno(
                "Требования класса не выполнены",
                f"Ваш персонаж не соответствует требованиям класса {self.class_var.get()}!\n"
                f"Необходимо: {req_text}\n\nВсё равно продолжить?"
            )
            if not response:
                return
        
        selected = self.get_selected_skills()
        if len(selected) < self.max_skills:
            response = messagebox.askyesno(
                "Не все навыки выбраны",
                f"Вы выбрали {len(selected)} из {self.max_skills} навыков.\n"
                f"Всё равно продолжить?"
            )
            if not response:
                return
        
        sheet_window = tk.Toplevel(self.root)
        sheet_window.title(f"Лист персонажа: {self.name_var.get()}")
        sheet_window.geometry("550x800")
        sheet_window.resizable(False, False)
        
        main_frame = tk.Frame(sheet_window, bg="#2c3e50")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="ЛИСТ ПЕРСОНАЖА", font=("Arial", 16, "bold"), 
                bg="#2c3e50", fg="#ecf0f1").pack(pady=15)
        
        info_frame = tk.Frame(main_frame, bg="#34495e")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        def create_info_row(parent, label_text, value_text, color="#3498db"):
            frame = tk.Frame(parent, bg="#34495e")
            frame.pack(fill="x", pady=3, padx=20)
            tk.Label(frame, text=label_text, font=("Arial", 11, "bold"), 
                    bg="#34495e", fg=color, width=16, anchor="w").pack(side="left")
            tk.Label(frame, text=value_text, font=("Arial", 11), 
                    bg="#34495e", fg="#ecf0f1", anchor="w", wraplength=300).pack(side="left", padx=10)
        
        prof_bonus = self.get_proficiency_bonus()
        create_info_row(info_frame, "Имя:", self.name_var.get())
        create_info_row(info_frame, "Уровень:", f"{self.level_var.get()} (бонус +{prof_bonus})")
        create_info_row(info_frame, "Мировоззрение:", self.alignment_var.get())
        create_info_row(info_frame, "Раса:", self.race_var.get())
        create_info_row(info_frame, "Класс:", self.class_var.get())
        create_info_row(info_frame, "Предыстория:", self.background_var.get())
        create_info_row(info_frame, "КД/Хиты:", f"{self.ac_var.get()} / {self.hp_var.get()}")
        create_info_row(info_frame, "Иниц./Скорость:", f"{self.initiative_var.get()} / {self.speed_var.get()}")
        create_info_row(info_frame, "Пасс. Внимательность:", self.passive_perception_label.cget("text"))
        create_info_row(info_frame, "Оружие:", self.weapon_var.get())
        
        ttk.Separator(info_frame, orient='horizontal').pack(fill='x', padx=20, pady=5)
        
        tk.Label(info_frame, text="Характеристики:", font=("Arial", 12, "bold"), 
                bg="#34495e", fg="#f39c12").pack(pady=5)
        
        for ability, var in self.abilities.items():
            value = var.get()
            modifier = self.calculate_modifier(value)
            sign = "+" if modifier >= 0 else ""
            create_info_row(info_frame, f"{ability}:", f"{value} ({sign}{modifier})", "#e67e22")
        
        ttk.Separator(info_frame, orient='horizontal').pack(fill='x', padx=20, pady=5)
        
        tk.Label(info_frame, text="Навыки (владение):", font=("Arial", 12, "bold"), 
                bg="#34495e", fg="#f39c12").pack(pady=5)
        
        selected = self.get_selected_skills()
        if selected:
            skills_text = ", ".join(selected)
        else:
            skills_text = "нет"
        create_info_row(info_frame, "Владение:", skills_text, "#8e44ad")
        
        tk.Label(info_frame, text="Снаряжение:", font=("Arial", 12, "bold"), 
                bg="#34495e", fg="#f39c12").pack(pady=5)
        create_info_row(info_frame, "Снаряжение:", self.equipment_text.get() or "нет", "#1abc9c")
        
        tk.Label(info_frame, text="Владения и языки:", font=("Arial", 12, "bold"), 
                bg="#34495e", fg="#f39c12").pack(pady=5)
        create_info_row(info_frame, "Владения:", self.proficiencies_text.get() or "нет", "#1abc9c")
        create_info_row(info_frame, "Языки:", self.languages_text.get() or "нет", "#1abc9c")
        
        btn_frame = tk.Frame(main_frame, bg="#2c3e50")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Закрыть", command=sheet_window.destroy, 
                 bg="#95a5a6", fg="white", font=("Arial", 10), padx=10, pady=3).pack()
    
    def save_to_json(self):
        if not self.name_var.get().strip():
            messagebox.showwarning("Внимание", "Пожалуйста, введите имя персонажа!")
            return
            
        ability_data = {}
        for ability, var in self.abilities.items():
            ability_data[ability] = {
                "value": var.get(),
                "modifier": self.calculate_modifier(var.get())
            }
        
        character_data = {
            "name": self.name_var.get(),
            "level": self.level_var.get(),
            "proficiency_bonus": self.get_proficiency_bonus(),
            "alignment": self.alignment_var.get(),
            "race": self.race_var.get(),
            "class": self.class_var.get(),
            "background": self.background_var.get(),
            "weapon": self.weapon_var.get(),
            "ac": self.ac_var.get(),
            "hp": self.hp_var.get(),
            "initiative": self.initiative_var.get(),
            "speed": self.speed_var.get(),
            "passive_perception": self.passive_perception_label.cget("text"),
            "abilities": ability_data,
            "skills": self.get_selected_skills(),
            "equipment": self.equipment_text.get(),
            "proficiencies": self.proficiencies_text.get(),
            "languages": self.languages_text.get(),
            "trait": self.trait_text.get()
        }
        
        try:
            filename = f"{self.name_var.get().replace(' ', '_')}_character.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(character_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успех", f"Персонаж сохранен в файл:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def reset_form(self):
        self.name_var.set("")
        self.level_var.set("1")
        self.alignment_var.set("Нейтральный")
        self.race_var.set(self.races[0])
        self.class_var.set(self.classes[0])
        self.background_var.set(self.background_names[0])
        self.weapon_var.set(self.weapons[0])
        
        for ability in self.base_abilities:
            self.base_abilities[ability] = 10
        
        for skill in self.all_skills:
            self.skill_states[skill] = False
        self.selected_skills_count = 0
        
        self.equipment_text.set("")
        self.languages_text.set("")
        
        self.apply_race_bonuses()
        self.update_remaining_points()
        self.update_all_modifiers()
        self.update_skill_list()
        self.update_proficiency_bonus()
        self.update_combat_stats()
        self.on_background_changed()
        self.update_saving_throws_display()
        self.skill_count_label.config(text=f"0/{self.max_skills}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterCreator(root)
    root.mainloop()