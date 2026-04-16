import os
import json
import ctypes
import time
from art import tprint
from colorama import init
from colorama import Fore, Back, Style
from datetime import datetime, timezone

init()

# Строковый ID оператора -> русское название
allOp = {
    "recruita": "Р-Штурмовик", "recruitg": "Р-Поддержка", "recruitm": "Р-Медик", "recruits": "Р-Снайпер",
    "fsb2004a": "Волк", "fsb2004g": "Алмаз", "fsb2004m": "Дед", "fsb2004s": "Стрелок",
    "fsb2016a": "Перун", "fsb2016g": "Сварог", "fsb2016m": "Травник", "fsb2016s": "Сокол",
    "sso2013a": "Ворон", "sso2013g": "Спутник", "sso2013m": "Бард", "sso2013s": "Комар",
    "22spn2016a": "Плут", "22spn2016g": "Кит", "22spn2016m": "Каравай", "22spn2016s": "Тень",
    "grom2014a": "Кошмар", "grom2014g": "Пророк", "grom2014m": "Микола", "grom2014s": "Стилет",
    "ksk2011a": "Рейн", "ksk2011g": "Штерн", "ksk2011m": "Шатц", "ksk2011s": "Курт",
    "seal2014a": "Корсар", "seal2014g": "Бурбон", "seal2014m": "Монк", "seal2014s": "Скаут",
    "tfb2008a": "Стерлинг", "tfb2008g": "Бишоп", "tfb2008m": "Ватсон", "tfb2008s": "Арчер",
    "raid2017a": "Авангард", "raid2017g": "Бастион", "raid2017m": "Велюр", "raid2017s": "Вагабонд",
    "nesher2015a": "Афела", "nesher2015g": "Хагана", "nesher2015m": "Шаршерет", "nesher2015s": "Эйма",
    "ezapaca": "Фаро", "ezapacg": "Матадор", "ezapacm": "Мигель", "ezapacs": "Диабло",
    "arystana": "Мустанг", "arystang": "Тибет", "arystanm": "Багги", "arystans": "Султан",
    "belssoa": "Лазутчик", "belssog": "Зубр", "belssom": "Каваль", "belssos": "Бусел",
    "amfa": "Старкад", "amfg": "Один", "amfm": "Фрейр", "amfs": "Видар",
    "jiaolonga": "Шаовэй", "jiaolongg": "Инчжоу", "jiaolongm": "Яован", "jiaolongs": "Цанлун",
    "csta": "Слай", "cstg": "Фортресс", "cstm": "Боунс", "csts": "Аваланш",
    "bopea": "Мартелу", "bopeg": "Баррейра", "bopem": "Асаи", "bopes": "Касадор",
    # --- Новые операторы ---
    "sass": "SAS-Штурмовик", "sasm": "SAS-Медик",
    "sek2015g": "SEK-Поддержка", "sek2015s": "SEK-Снайпер",
    "pohm": "POH-Медик",
}

# Числовой ID оператора (ключ "0" в карточке) -> строковый ID
operNumToStr = {
    0: "recruita", 3: "recruitm",
    4: "fsb2004a", 8: "fsb2016s", 9: "sso2013a",
    10: "22spn2016g", 11: "grom2014g", 13: "22spn2016m",
    16: "grom2014g", 18: "sso2013m", 19: "cstg",
    20: "grom2014g", 21: "seal2014m", 23: "belssom",
    25: "22spn2016m", 30: "grom2014s", 31: "grom2014m",
    39: "tfb2008s", 41: "tfb2008m", 44: "22spn2016g",
    49: "arystanm", 50: "arystanm", 52: "belssog",
    53: "sso2013g", 56: "belssom", 58: "jiaolongs",
    61: "jiaolongs", 62: "cstm", 64: "jiaolonga",
    70: "bopea", 75: "sass", 77: "sasm",
    80: "sek2015g", 81: "sek2015g", 82: "sek2015s",
}

# Строковый ID навыка -> русское название
abilityNames = {
    "adaptive_armor": "Адапт. броня",
    "adrenaline_rush": "Прилив адреналина",
    "advanced_training": "Выс. подготовка",
    "altitude_training": "Угл. тренировка",
    "ambush": "Засада",
    "armament": "Вооруж. забег",
    "armor_piercing_rounds": "Бб. патроны",
    "barrel_cutting": "Обр. цевья",
    "battle_hardening": "Б. закалка",
    "blood_rage": "Кровавая ярость",
    "booster_pouch": "Доп. подсумки",
    "buffhunter": "Охота за г.",
    "chock_a_block": "Расчетливость",
    "cold_blood": "Хладнокровие",
    "cold_math": "Холодный расчет",
    "collective_syringe": "Общий мед пакет",
    "combined_armor": "Комб. броня",
    "consumables_pouch": "Доп. подсумки",
    "counter_attack": "Контратака",
    "dead_silence": "Скрыт перемещение",
    "die_hard": "Крепкий орешек",
    "direct_acting_shutter": "Мод. зат. мех.",
    "effective_reload": "Быстр. магазины",
    "enhanced_armor": "Ус. защита",
    "expansive_bullets": "Экспанс. пули",
    "extra_layer": "Противооскол. слой",
    "fast_revive": "Скорая помощь",
    "feedback_armor": "Реген. материалы",
    "field_medicine": "Фактор лечения",
    "fireres_materials": "Герм. материалы",
    "first_blood": "Первая кровь",
    "flatness": "Настильность",
    "forend_processing": "Обр. цевья",
    "fresh_forces": "Свежие силы",
    "head_hunter": "Охота за г.",
    "head_protection": "Защ. головы",
    "healing_factor": "Фактор лечения",
    "healing_touch": "Беспощадность",
    "heavy_ammunition": "Тяж. боеприпасы",
    "heavy_barrel": "Тяж. ствол",
    "heavyweight_marathon": "Вооруж. забег",
    "hemoglobin_serum": "Сыв.гемоглобина",
    "improved_formula": "Ул. формула",
    "in_the_crosshairs": "Под прицелом",
    "inner_strength": "Внутр. резерв",
    "lightweight_armor": "Облегч. разгрузка",
    "lightweight_equipment": "Обл. разгрузка",
    "lone_wolf": "Одинокий волк",
    "merciless": "Беспощадность",
    "neurosurgery": "Стим. медикаменты",
    "own_priorities": "Свои приоритеты",
    "priority_target": "Приоритетная цель",
    "prudence": "Расчетливость",
    "quick_release_magazines": "Быстр. магазины",
    "regenerative_materials": "Реген. материалы",
    "retaliation": "Возмездие",
    "robotic_calibrations": "Калибровка техники",
    "second_wind": "Вт. дыхание",
    "self_healing": "Самолечение",
    "shield_breaker": "Щитолом",
    "shoulder_to_shoulder": "Плечом к плечу",
    "shrapnel_layer": "Противооскол. слой",
    "sixth_sense": "Крепкие нервы",
    "spare_syringe": "Зап. шприц",
    "stay_frosty": "Хороший отдых",
    "stealth_warrior": "Скрытый воин",
    "stim_medpacks": "Стим. медикаменты",
    "strong_armor": "Адапт. броня",
    "strong_nerves": "Крепкие нервы",
    "strong_stim": "Усил. стим.",
    "subdermal_meldonium": "Суб. мельдоний",
    "subdermal_morphine": "Суб. морфин",
    "super_sensitive_trigger": "Чувств. спуск. к.",
    "take_aim": "Стрелк. позиция",
    "team_medpacks": "Общий мед пакет",
    "thermal_imager": "Тепловизор",
    "tight_fit": "Пл. прилегание",
    "tungsten_coating": "Вольфрам. покрытие",
    "well_rested": "Хороший отдых",
    "will_to_live": "Тяга к жизни",
}

# Расходники
consumableNames = {
    "HealthPack": "Мед. пакет",
    "ArmorPack": "Пластина",
    "AmmoPack": "Патроны",
    "StaminaRegenBooster": "Стимулятор",
    "TeamAmmoBox": "Ящик",
}

groups = {
    0: Back.GREEN, 1: Back.CYAN, 2: Back.WHITE, 3: Back.YELLOW
}

allRegimes = {
    "polygon": 1, "pvehard": 4, "pve": 4,
    "onslaughtnormal": 4, "onslaughthard": 4,
    "pvpdestruction": 8, "pvpve": 8, "pvp": 8,
    "hacking": 8, "pvpve2": 8,
}


def get_op_name(op_str):
    """Получить русское имя оператора по строковому ID."""
    return allOp.get(op_str, op_str)


def get_ability_name(ab):
    """Получить русское имя навыка (строка или None)."""
    if ab is None:
        return "-"
    return abilityNames.get(ab, ab)


def get_consumable_name(c):
    """Получить русское имя расходника."""
    if c is None:
        return "-"
    return consumableNames.get(c, c)


print(Fore.RED)
try:
    tprint("VXRGXS", "speed")
except Exception:
    tprint("VXRGXS")

ctypes.windll.kernel32.SetConsoleTitleA(b"MMR")
print(Style.BRIGHT)

work = True
name = os.environ["UserName"]
replays_path = f"C:\\Users\\{name}\\AppData\\LocalLow\\1CGS\\Caliber\\Replays"
log_path = f"C:\\Users\\{name}\\AppData\\LocalLow\\1CGS\\Caliber\\Player.log"

while work:
    try:
        content = os.listdir(replays_path)
    except FileNotFoundError:
        print(Fore.RED + f"Папка реплеев не найдена: {replays_path}")
        break

    content.sort(
        key=lambda x: os.path.getmtime(os.path.join(replays_path, x)),
        reverse=True
    )

    for i, file in enumerate(content):
        print(Fore.BLUE + str(i) + " " + Fore.GREEN + content[i])

    number = input(
        Fore.GREEN + "Введите" + Fore.BLUE + " НОМЕР " + Fore.GREEN + "реплея или" +
        Fore.BLUE + " b (battle) " + Fore.GREEN + "чтобы посмотреть игроков в текущем поиске\n" +
        Fore.BLUE
    )
    os.system('CLS')

    # ── Режим battle (текущий поиск) ──────────────────────────────────────────
    if number.lower() in ("b", "battle"):
        bufTime = 0.0
        workBattle = True
        while workBattle:
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    textBattle = f.readlines()
            except FileNotFoundError:
                print(Fore.RED + f"Файл лога не найден: {log_path}")
                workBattle = False
                break

            for i in range(len(textBattle)):
                textLine = str(textBattle[len(textBattle) - i - 1])
                if textLine[100:160].find("battlepreparation/me") != -1:
                    battleLine = textBattle[len(textBattle) - i]
                    if len(battleLine) < 100:
                        continue
                    timeLine = textLine[1:textLine.find("]")]
                    timeLine = datetime.fromisoformat(timeLine)
                    currentTime = datetime.now(timezone.utc)
                    if bufTime == timeLine.timestamp():
                        if (currentTime.timestamp() - timeLine.timestamp()) > 21:
                            print(
                                Fore.RED + "Выведена информация о последнем поиске боя."
                                           " Подготовка к раунду закончилась больше 20 сек. назад.")
                            input("Нажмите" + Fore.GREEN + " ENTER " + Fore.RED + "чтобы продолжить")
                            workBattle = False
                            break
                        print("\r", end="")
                        print(Fore.MAGENTA + "Последняя информация получена " + Fore.RED +
                              str(int(currentTime.timestamp() - timeLine.timestamp())) +
                              Fore.MAGENTA + " сек. назад.", end="")
                        time.sleep(0.5)
                        break
                    bufTime = timeLine.timestamp()
                    print()
                    os.system('CLS')

                    try:
                        battleJson = json.loads(battleLine)
                    except json.JSONDecodeError:
                        print(Fore.RED + "Ошибка чтения JSON из лога")
                        workBattle = False
                        break

                    print(Fore.MAGENTA, battleJson["b"]["Mission"]["SelectedMission"]["MissionId"], "\n")
                    print(Fore.MAGENTA,
                          battleJson["b"]["Stages"][battleJson["b"]["CurrentStage"]["Index"]]["stage_type"])

                    for plCount in range(len(battleJson["b"]["Teams"])):
                        label = Fore.BLUE + f"\nКоманда #{plCount + 1}"
                        print(label)

                        battlePlayersGr = [
                            battleJson["b"]["Teams"][plCount]["Users"][p]
                            for p in range(len(battleJson["b"]["Teams"][plCount]["Users"]))
                        ]
                        battlePlayersGr.sort(key=lambda x: x["Role"])

                        for pl in battlePlayersGr:
                            abil = "| "
                            consumables = "| "
                            picked = pl.get("PickedCard")
                            if picked is not None:
                                card = picked["Card"]
                                for t in range(2):
                                    c = card.get("14", [None, None])[t]
                                    consumables += "{0:^14}".format(get_consumable_name(c)) + "|"
                                for l in range(4):
                                    ab_list = card.get("15", [None] * 4)
                                    ab = ab_list[l] if l < len(ab_list) else None
                                    abil += "{0:^20}".format(get_ability_name(ab)) + "|"

                            op_str = picked["Card"].get("1", "") if picked else ""
                            op_name = get_op_name(op_str) if op_str else "Не выбран"

                            print(
                                f"{Fore.MAGENTA}{'+'if pl['IsReady'] else '-'} "
                                f"{Fore.RED}{'{0:<22}'.format(pl['Nickname'])}"
                                f"{Fore.MAGENTA}Роль: {Fore.RED}{'{0:<8}'.format(pl['Role'])}"
                                f"{Fore.MAGENTA}Опер: {Fore.RED}{'{0:<12}'.format(op_name)}"
                                f"{Fore.MAGENTA} Ур:{Fore.RED}{'{0:^4}'.format(picked['Card'].get('18','?') if picked else '?')}"
                                f"{Fore.MAGENTA} Расх:{Fore.RED}{consumables}"
                            )
                            print(f"{Fore.GREEN}{abil}")
                    break
                elif i == len(textBattle) - 1:
                    print(Fore.RED, "Игра не найдена. Введите b во время старта боя")
                    workBattle = False
                    break

    # ── Просмотр реплея ───────────────────────────────────────────────────────
    elif number.isdigit() and int(number) < len(content):
        number = int(number)
        if not content[number].endswith(".bytes"):
            print(Fore.RED + "Нельзя открыть этот файл")
            continue

        replay_file = os.path.join(replays_path, content[number])
        try:
            with open(replay_file, "rb") as f:
                text = f.readline()
        except FileNotFoundError:
            print(Fore.RED + "Файл реплея не найден")
            continue

        text = str(text)
        text = text[text.find("{"):text.rfind("}") + 2]
        sub_text = text[:text.find('"Log"')]
        sub_text1 = sub_text[:sub_text.rfind("]}") + 2]

        if len(sub_text1) < 2:
            print(Fore.RED, "Не удается открыть реплей")
            continue

        try:
            block1 = json.loads(sub_text1)
        except json.JSONDecodeError:
            print(Fore.RED, "Ошибка разбора JSON реплея")
            continue

        players = block1["7"]
        regime = block1["4"]
        player_count = int(allRegimes.get(regime, len(players)))

        print(
            Fore.MAGENTA + "ID реплея: ", Fore.RED, block1["0"],
            Fore.MAGENTA, "\tКарта: ", Fore.RED, block1["2"],
            Fore.MAGENTA, "\tРежим: ", Fore.RED, block1["4"],
            Fore.MAGENTA, "\tРегион: ", Fore.RED, block1["6"]
        )

        gr = [players[i]["1"] for i in range(player_count)]
        gr2 = {}
        grCount = 0
        for i in range(player_count):
            if gr.count(players[i]["1"]) > 1 and players[i]["1"] not in gr2:
                gr2[players[i]["1"]] = grCount
                grCount += 1

        for i in range(player_count):
            color = " "
            if i == 0:
                print(Fore.BLUE + "\nКоманда #1")
            elif i == 4:
                print(Fore.BLUE + "\nКоманда #2")
            if players[i]["1"] in gr2:
                color = groups[gr2.get(players[i]["1"])] + " "
                if players[i]["1"] == players[i]["0"]:
                    color = groups[gr2.get(players[i]["1"])] + Fore.BLACK + Style.NORMAL + "!"

            op_str = players[i]["8"].get("1", "")
            op_name = get_op_name(op_str) if op_str else "?"

            print(
                f"{color}{Back.RESET + Style.BRIGHT + Fore.RED}"
                f"{'{0:<22}'.format(players[i]['2'])}"
                f"{Fore.MAGENTA}ID игрока: {Fore.RED}{'{0:<10}'.format(players[i]['0'])}"
                f"{Fore.MAGENTA}Опер: {Fore.RED}{'{0:<14}'.format(op_name)}"
                f"{Fore.MAGENTA}Уровень: {Fore.RED}{'{0:<4}'.format(players[i]['3'])}"
                f"{Fore.MAGENTA}"
            )

        # Дополнительная информация
        while True:
            word = input(
                f"{Fore.BLUE}\ni (info){Fore.GREEN} - Дополнительная информация об игроках\n"
                f"{Fore.BLUE}r (replays){Fore.GREEN} - к списку реплеев\n"
                f"{Fore.BLUE}e (exit){Fore.GREEN} - выход\n{Fore.BLUE}"
            ).lower()

            if word in ("info", "i"):
                for i in range(player_count):
                    print(Fore.BLUE, i, Fore.GREEN, players[i]["2"], Fore.BLUE)
                    if i == 3:
                        print("")

                numberPlayer = input("\n*********************\nВведите номер игрока:\n")
                if numberPlayer.isdigit() and int(numberPlayer) < player_count:
                    p = players[int(numberPlayer)]
                    card = p["8"]
                    op_str = card.get("1", "")

                    # Навыки
                    abilities_raw = card.get("15", [])
                    abilities_str = ", ".join(get_ability_name(a) for a in abilities_raw)

                    # Расходники
                    consumables_raw = card.get("14", [])
                    consumables_str = ", ".join(get_consumable_name(c) for c in consumables_raw)

                    # Навыки аккаунта
                    acc_skills = p.get("20", {})
                    if isinstance(acc_skills, dict):
                        acc_str = ", ".join(
                            f"{get_ability_name(k)}(ур.{v})" for k, v in acc_skills.items()
                        )
                    else:
                        acc_str = str(acc_skills)

                    print(f"""{Fore.RED}{p["2"]}

{Fore.MAGENTA}Оперативник:            {Fore.RED}{get_op_name(op_str)}
{Fore.MAGENTA}Расходники:             {Fore.RED}{consumables_str}
{Fore.MAGENTA}Установленные навыки:   {Fore.RED}{abilities_str}
{Fore.MAGENTA}Уровень оперативника:   {Fore.RED}{card.get("18", "?")}
{Fore.MAGENTA}Престиж оперативника:   {Fore.RED}{card.get("19", "?")}
{Fore.MAGENTA}Опыт оперативника:      {Fore.RED}{card.get("4", "?")}

{Fore.MAGENTA}Навыки аккаунта:
{Fore.RED}{acc_str}
""")
                else:
                    print(Fore.RED, "\n***Введен неверный номер***")
                    break

            elif word in ("exit", "e"):
                work = False
                break
            elif word in ("replays", "r"):
                os.system('CLS')
                break
            else:
                print(Fore.RED, "\nОшибка")
                continue

    else:
        os.system('CLS')
        print(Fore.RED, "\n***Введен неверный номер***")
