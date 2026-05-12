"""
52-й Медицинский Корпус — Датапад v3.0
Desktop приложение | Захват клавиатуры | NGG/МК стиль
"""
import sys, os, time, threading, csv, io
import requests
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    import keyboard
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False

SHEET_URL  = "https://docs.google.com/spreadsheets/d/1XTUm3Je3QfrrOusMAF21qV9yrRGHKuo4KGEyjGMGv2s/export?format=csv&gid=1534723792"
HOTKEY     = "F7"
STEP_DELAY = 2.8

BG    = "#0a0b14"; BG2   = "#0f1020"; CARD  = "#12152a"; CARD2 = "#171b35"
BORD  = "#1e2444"; BORD2 = "#262d52"
N1    = "#3b6ff5"; N2    = "#8b3af5"; N3    = "#f53b9a"
TEXT  = "#e8ecf8"; TXT2  = "#8a9ac8"; TXT3  = "#4a5580"
OK    = "#22c87a"; WARN  = "#f5a623"; ERR   = "#f54b4b"

TCOL = {"Блок A":ERR,"Блок B":WARN,"Блок C":OK,"Раны":N2,"Стационар":N1}
TABS = ["Блок A","Блок B","Блок C","Раны","Стационар"]

ACTIONS = [
    {"tab":"Блок A","tag":"A-1","label":"Отсутствие дыхания","steps":[
        "надевает медицинские перчатки, снимает шлем с пострадавшего",
        "запрокидывает голову, применяет маневр «челюстной подъём» — выдвигает нижнюю челюсть вперёд",
        "открывает рот, аккуратно вытягивает язык, проверяет дыхательные пути",
        "проверяет наличие дыхания и пульса",
        "при отсутствии пульса — начинает непрямой массаж сердца, 30 компрессий",
        "делает 2 вдоха ИВЛ, зажав нос, продолжает цикл 30:2",
        "вводит Морферум внутривенно после восстановления пульса",
    ]},
    {"tab":"Блок A","tag":"A-1b","label":"Блокировка ВДП (рвота / инородное тело)","steps":[
        "поворачивает пострадавшего на бок, снимает шлем, открывает рот",
        "надевает перчатки, берёт салфетки, очищает ВДП от рвотных масс",
        "при инородном теле — встаёт сзади, обхватывает чуть ниже солнечного сплетения",
        "выполняет 5 резких нажатий на живот (приём Геймлиха)",
        "просит наклониться вперёд, постукивает между лопатками",
        "проверяет наличие дыхания, вводит Морферум в/в при необходимости",
    ]},
    {"tab":"Блок A","tag":"A-2","label":"Контузия","steps":[
        "снимает шлем с пострадавшего, освобождает шею — закатывает ворот ЧНК",
        "вводит Морферум внутривенно в шею, Антишок внутримышечно",
        "накладывает холодный компресс на голову на 5-7 минут с перерывами",
        "следит за речью — при невнятной кладёт на зубы что-то мягкое",
        "не поднимает бойца в вертикальное положение",
        "при необходимости фиксирует шею воротником",
    ]},
    {"tab":"Блок A","tag":"A-2b","label":"Ушибы","steps":[
        "снимает шлем и бронепластины с поражённой области",
        "освобождает шею — закатывает ворот ЧНК",
        "вводит Морферум внутривенно в шею для обезболивания",
        "разрезает одежду в области ушиба для доступа",
        "наносит слой Бакты на ушиб",
        "накладывает холодный компресс на поражённую область",
        "перебинтовывает область ушиба бинтами, закрепляет повязку",
    ]},
    {"tab":"Блок A","tag":"A-3","label":"Обморок","steps":[
        "убеждается в отсутствии других ранений прежде чем приводить в сознание",
        "снимает шлем с пострадавшего",
        "достаёт Квиквейк — разламывает палочку",
        "аккуратно подносит к носу бойца, чтобы тот вдохнул пары",
        "после прихода в сознание — даёт попить воды",
        "при травматическом шоке — вводит Морферум в/в, Антишок в/м",
    ]},
    {"tab":"Блок B","tag":"B-1a","label":"Капиллярное кровотечение","steps":[
        "снимает бронепластины, освобождает область от одежды (закатывает ЧНК)",
        "определяет тип ранения и тип кровотечения",
        "обрабатывает рану антисептиком Веромин",
        "наносит Бакту на рану",
        "накладывает и закрепляет асептическую повязку",
    ]},
    {"tab":"Блок B","tag":"B-1b","label":"Венозное / Артериальное (конечность)","steps":[
        "снимает шлем, освобождает шею (закатывает ЧНК)",
        "вводит Морферум внутривенно в шею для обезболивания",
        "снимает бронепластины, разрезает одежду поперёк в месте ранения",
        "определяет тип ранения, проверяет на инородные тела — при наличии извлекает пинцетом",
        "при венозном — накладывает жгут НИЖЕ места ранения",
        "при артериальном/смешанном — накладывает жгут ВЫШЕ места ранения",
        "обрабатывает рану Веромином, наносит Бакту",
        "накладывает и закрепляет асептическую повязку",
        "при большой кровопотере — устанавливает капельницу с Раствором Рингера",
    ]},
    {"tab":"Блок B","tag":"B-1c","label":"Кровотечение (шея / туловище)","steps":[
        "снимает шлем, разрезает ЧНК на шее в области ранения",
        "вводит Морферум внутривенно в шею для обезболивания",
        "обрабатывает рану Веромином, наносит Бакту",
        "зашивает рану с помощью УДСР",
        "вводит 1 шприц Транексамовой кислоты внутривенно",
        "перебинтовывает Бакта-бинтом, сверху — асептической повязкой",
        "на шею: накладывает давящую повязку, затягивает под подмышку",
        "устанавливает капельницу с Раствором Рингера при большой кровопотере",
    ]},
    {"tab":"Блок B","tag":"B-1d","label":"Внутреннее кровотечение","steps":[
        "вводит 1 шприц Транексамовой кислоты внутривенно",
        "устанавливает капельницу с Раствором Рингера",
        "накладывает холодный компресс или намазывает Эйсом",
        "транспортирует бойца в стационар для дальнейшего лечения",
    ]},
    {"tab":"Блок B","tag":"B-2a","label":"Ожог I степени","steps":[
        "снимает шлем, все бронепластины и верхнюю одежду (ЧНК)",
        "вводит Морферум внутривенно в шею для обезболивания",
        "обрабатывает область ожога Веромином и Бактой",
        "наносит Эйс на место ожога",
        "накладывает и закрепляет асептическую повязку",
    ]},
    {"tab":"Блок B","tag":"B-2b","label":"Ожог II степени","steps":[
        "вводит Морферум внутривенно в шею для обезболивания",
        "осторожно удаляет снаряжение в области ожога, не затрагивая пузыри",
        "аккуратно обрабатывает кожу вокруг ожога Веромином",
        "наносит Бакту и Эйс на место ожога",
        "вводит Хлоропирамин внутримышечно",
        "накладывает и закрепляет асептическую повязку",
    ]},
    {"tab":"Блок B","tag":"B-2c","label":"Ожог III-IV (стабилизация)","steps":[
        "НЕ пытается снять/разрезать одежду с места ожога",
        "вводит Морферум внутривенно для обезболивания",
        "стабилизирует состояние бойца",
        "транспортирует в ВПГ или МБ — лечение III+ только в стационаре",
    ]},
    {"tab":"Блок B","tag":"B-3a","label":"Обморожение I-II степени","steps":[
        "вводит Морферум внутривенно, Антишок для стабилизации",
        "снимает шлем, бронепластины и верхнюю одежду (ЧНК) для доступа",
        "наносит слой Бакты на обмороженные участки",
        "накладывает тёплый (не горячий) компресс на обмороженную область",
        "даёт пострадавшему выпить тёплой воды",
        "НЕ растирает обмороженные участки — это ведёт к доп. повреждениям",
    ]},
    {"tab":"Блок B","tag":"B-3b","label":"Обморожение III-IV (стабилизация)","steps":[
        "вводит Морферум внутривенно для обезболивания",
        "снимает броню, подворачивает ЧНК на месте обморожения",
        "обрабатывает поражённую область Нунибамидом",
        "НЕ взаимодействует с местами обморожения — не разрезает, не трогает",
        "транспортирует в ВПГ или МБ — лечение III+ только в стационаре",
    ]},
    {"tab":"Блок C","tag":"C-1a","label":"Закрытый перелом конечности","steps":[
        "снимает шлем с пострадавшего",
        "снимает бронепластины с повреждённой конечности, закатывает ЧНК",
        "вводит Морферум внутривенно в шею",
        "достаёт шину, подкладывает под неё ткань",
        "накладывает шину, захватывая два сустава — выше и ниже места перелома",
        "надёжно фиксирует шину",
        "НЕ наносит Бакту если перелом сильно деформирован",
    ]},
    {"tab":"Блок C","tag":"C-1b","label":"Открытый перелом конечности","steps":[
        "снимает шлем и бронепластины с повреждённой конечности, закатывает ЧНК",
        "вводит Морферум внутривенно",
        "разрезает ЧНК поперёк в области перелома для доступа к ране",
        "определяет тип кровотечения, накладывает жгут",
        "обрабатывает пинцет Веромином, удаляет видимые осколки",
        "обрабатывает рану Веромином",
        "накладывает шину, надёжно фиксирует",
    ]},
    {"tab":"Блок C","tag":"C-1c","label":"Перелом рёбер / позвоночника","steps":[
        "вводит Морферум внутривенно",
        "обрабатывает место перелома Веромином",
        "обрабатывает Крайном, вводит Хромостринг в место перелома",
        "устанавливает Костный стабилизатор наружного применения (КСНП)",
        "при переломе позвоночника — надевает медицинский корсет/воротник",
        "фиксирует устройство, через время снимает",
    ]},
    {"tab":"Блок C","tag":"C-2","label":"Растяжение","steps":[
        "снимает бронепластины, освобождает область от одежды (закатывает ЧНК)",
        "наносит слой Бакты на место растяжения",
        "накладывает холодный компресс для уменьшения отёка и боли",
    ]},
    {"tab":"Блок C","tag":"C-3","label":"Вывих","steps":[
        "снимает шлем, освобождает шею (закатывает ЧНК)",
        "вводит Морферум внутривенно в шею для обезболивания",
        "снимает все бронепластины, освобождает область вывиха от одежды",
        "наносит Нунибамид на область сустава",
        "аккуратно вправляет сустав в правильное анатомическое положение",
        "накладывает эластичный бинт, пропитанный Бактой, фиксирует повязку",
    ]},
    {"tab":"Блок C","tag":"C-4","label":"Пневмоторакс","steps":[
        "снимает все бронепластины и шлем с пострадавшего",
        "обрабатывает место ранения антисептиком Веромин",
        "вводит иглу аппарата УОП, выкачивает воздух/газ из плевральной полости",
        "при гидротораксе — выкачивает жидкость",
        "вводит Бакту в место ранения",
        "накладывает окклюзионную (герметизирующую) повязку",
        "перебинтовывает асептической повязкой",
        "подключает бойца к аппарату ИВЛ",
    ]},
    {"tab":"Блок C","tag":"C-5a","label":"ЧМТ закрытая","steps":[
        "вводит Морферум внутривенно",
        "оценивает состояние — уровень сознания, реакция зрачков",
        "стабилизирует шею и голову — горизонтальное положение, воротник",
        "вводит Хромостринг",
        "вводит Бакту инъекцией в артерию на шее",
        "наносит Эйс и Бакту на марлевую повязку, перевязывает голову",
        "вводит Нейростабилекс внутривенно",
    ]},
    {"tab":"Блок C","tag":"C-5b","label":"ЧМТ открытая","steps":[
        "вводит Морферум внутривенно",
        "оценивает состояние",
        "стабилизирует шею и голову — горизонтальное положение, воротник",
        "вводит Хромостринг",
        "обрабатывает гемостатическую губку AnBS и Веромином, прикладывает к ране",
        "вводит Бакту инъекцией в артерию на шее",
        "вводит Нейростабилекс внутривенно",
        "убирает губку, накладывает Кожный герметик",
        "наносит Эйс и Бакту на марлевую повязку, перевязывает голову",
    ]},
    {"tab":"Раны","tag":"Р-1","label":"Колотая рана","steps":[
        "вводит Морферум внутривенно",
        "останавливает кровотечение",
        "избавляется от всех инородных тел в ране",
        "обрабатывает рану Веромином",
        "накладывает Кожный герметик",
        "перебинтовывает место ранения Бакта-бинтом",
    ]},
    {"tab":"Раны","tag":"Р-2","label":"Резаная рана","steps":[
        "вводит Морферум внутривенно",
        "останавливает кровотечение",
        "избавляется от всех инородных тел в ране",
        "обрабатывает ранение Веромином и Бактой",
        "перебинтовывает место ранения",
    ]},
    {"tab":"Раны","tag":"Р-3","label":"Укушенная / рваная рана","steps":[
        "вводит Морферум внутривенно",
        "останавливает кровотечение",
        "избавляется от всех инородных тел в ране",
        "обрабатывает ранение Веромином и Бактой",
        "вводит Антиядин или Карбоксим и Хлоропирамин для профилактики отравления",
        "перебинтовывает место ранения",
        "при большой потере кожного покрова — применяет Синтеплоть",
    ]},
    {"tab":"Стационар","tag":"СТА","label":"Первичный осмотр","steps":[
        "помещает пострадавшего на койку",
        "сканирует бойца СУА — оценивает состояние здоровья",
        "проверяет основные жизненные показатели: дыхание, сознание",
        "проводит противошоковые мероприятия: вводит Морферум в/в",
        "при травматическом шоке — вводит Антишок или Хлорпромазин в/в",
        "восстанавливает кровообращение, останавливает кровотечения",
        "при необходимости устанавливает аппарат ИВЛ",
        "оказывает лечение остальных ранений по степени тяжести",
    ]},
    {"tab":"Стационар","tag":"СТА","label":"Очистка ВДП","steps":[
        "снимает шлем с бойца",
        "надевает медицинские перчатки",
        "приподнимает голову бойца, открывает ротовую полость",
        "достаёт из ВДП инородный предмет или рвотные массы",
        "отодвигает язык бойца, поворачивает голову на бок",
    ]},
    {"tab":"Стационар","tag":"СТА","label":"Медицинская комиссия","steps":[
        "приглашает бойца в смотровую, просит снять шлем, бронепластины и ЧНК",
        "направляет фонарик на глаза бойца — проверяет реакцию зрачков на свет",
        "определяет цвет глаз (норма — карие)",
        "измеряет артериальное давление (норма/отклонение)",
        "осматривает кожный покров (в норме/не в норме)",
        "проверяет ротовую полость (в норме/не в норме)",
        "проверяет наличие протезов/имплантов (более 3 — признак дефектности)",
        "задаёт устные вопросы: фобии, беспокойства, общее самочувствие",
        "пересчитывает пальцы на обеих руках и ногах",
        "заполняет бланк медкомиссии, выносит заключение",
    ]},
    {"tab":"Стационар","tag":"СТА","label":"Отравление","steps":[
        "вызывает у бойца рвотный рефлекс",
        "вводит Антиядин и Карбоксим",
        "вводит внутримышечно Витамин B1",
        "даёт таблетку Блистера и ложку Меруна с водой",
    ]},
]


class RosterLoader(QThread):
    done = pyqtSignal(list, bool, str)
    def run(self):
        try:
            r = requests.get(SHEET_URL, timeout=8); r.encoding = 'utf-8'
            users = []
            for row in csv.reader(io.StringIO(r.text)):
                if len(row) < 3: continue
                steam,num,cs = row[0].strip(),row[1].strip(),row[2].strip()
                rank = row[4].strip() if len(row)>4 else ""
                if not num or not cs or num=="Номер" or cs=="Позывной": continue
                if any(x in steam for x in ["Испытательный","Осуждённые","Бойцы","Общее"]): continue
                users.append({"callsign":cs,"num":num,"rank":rank or "Сотрудник МК"})
            self.done.emit(users, True, f"{len(users)} сотрудников")
        except Exception as e:
            self.done.emit([], False, str(e))


class GModSender(QObject):
    status_sig = pyqtSignal(str, str)
    def __init__(self):
        super().__init__(); self.busy = False
    def send(self, steps):
        if self.busy: self.status_sig.emit("Ожидайте...", WARN); return
        self.busy = True
        threading.Thread(target=self._worker, args=(steps,), daemon=True).start()
    def _worker(self, steps):
        for i, step in enumerate(steps):
            self._type(f"/me {step}")
            self.status_sig.emit(f"[{i+1}/{len(steps)}] {step[:60]}", N1)
            if i < len(steps)-1: time.sleep(STEP_DELAY)
        self.busy = False
        self.status_sig.emit("Готово!", OK)
    def _type(self, text):
        if not HAS_KEYBOARD: return
        try:
            keyboard.press_and_release('t'); time.sleep(0.18)
            QApplication.clipboard().setText(text)
            time.sleep(0.05)
            keyboard.press_and_release('ctrl+a')
            time.sleep(0.03)
            keyboard.press_and_release('ctrl+v')
            time.sleep(0.05)
            keyboard.press_and_release('enter')
        except: pass


class LoginScreen(QWidget):
    ok = pyqtSignal(dict)
    def __init__(self, p=None):
        super().__init__(p); self.users = []; self._ui()
        self._rl = RosterLoader(); self._rl.done.connect(self._loaded); self._rl.start()

    def _ui(self):
        v = QVBoxLayout(self); v.setContentsMargins(44,36,44,36); v.setSpacing(0)

        logo = QLabel("52-й МЕДИЦИНСКИЙ КОРПУС")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            font-size:17px; font-weight:700; font-family:'Segoe UI';
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {N1},stop:0.5 {N2},stop:1 {N3});
            -webkit-background-clip:text; color:{N1};
        """)
        v.addWidget(logo)

        sub = QLabel("ДАТАПАД  //  ПОЛЕВОЙ ДОСТУП")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color:{TXT3}; font-size:10px; letter-spacing:2px; margin-bottom:8px; font-family:'Segoe UI';")
        v.addWidget(sub)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"border-color:{BORD}; margin-bottom:20px;"); v.addWidget(line)

        card = QFrame(); card.setStyleSheet(f"background:{CARD}; border:1px solid {BORD}; border-radius:10px;")
        cl = QVBoxLayout(card); cl.setContentsMargins(22,20,22,20); cl.setSpacing(10)

        def lbl(t):
            l=QLabel(t); l.setStyleSheet(f"color:{TXT3}; font-size:10px; letter-spacing:1px; font-weight:700; font-family:'Segoe UI'; background:transparent; border:none;"); return l
        def inp(ph):
            e=QLineEdit(); e.setPlaceholderText(ph); e.setFixedHeight(34)
            e.setStyleSheet(f"background:{CARD2}; color:{TEXT}; border:1px solid {BORD2}; border-radius:6px; padding:0 10px; font-family:'Segoe UI'; font-size:12px;")
            return e

        cl.addWidget(lbl("ПОЗЫВНОЙ")); self.ics = inp("Введите позывной..."); cl.addWidget(self.ics)
        cl.addWidget(lbl("ЛИЧНЫЙ НОМЕР")); self.inum = inp("Введите номер..."); cl.addWidget(self.inum)

        self.errl = QLabel(""); self.errl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.errl.setStyleSheet(f"color:{ERR}; font-size:11px; font-family:'Segoe UI'; background:transparent; border:none;")
        cl.addWidget(self.errl)

        btn = QPushButton("ВОЙТИ В СИСТЕМУ"); btn.setFixedHeight(38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {N1}25,stop:0.5 {N2}25,stop:1 {N3}25);
                color:{N1}; border:1px solid {N1}55; border-radius:6px;
                font-size:13px; font-weight:700; letter-spacing:1.5px; font-family:'Segoe UI';}}
            QPushButton:hover {{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {N1}45,stop:0.5 {N2}45,stop:1 {N3}45); border-color:{N1}99;}}
        """)
        btn.clicked.connect(self._login); cl.addWidget(btn)
        v.addWidget(card); v.addSpacing(14)

        self.syncl = QLabel("Загрузка состава...")
        self.syncl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.syncl.setStyleSheet(f"color:{WARN}; font-size:10px; font-family:'Segoe UI';")
        v.addWidget(self.syncl); v.addStretch()

        self.inum.returnPressed.connect(self._login)
        self.ics.returnPressed.connect(lambda: self.inum.setFocus())

    def _loaded(self, users, ok, msg):
        self.users = users
        self.syncl.setText(f"Состав синхронизирован — {msg}" if ok else f"Ошибка: {msg}")
        self.syncl.setStyleSheet(f"color:{OK if ok else ERR}; font-size:10px; font-family:'Segoe UI';")

    def _login(self):
        cs=self.ics.text().strip(); num=self.inum.text().strip()
        if not cs or not num: self.errl.setText("Заполните все поля"); return
        for u in self.users:
            if u["callsign"].lower()==cs.lower() and u["num"]==num:
                self.ok.emit(u); return
        self.errl.setText("Неверные данные. Доступ запрещён.")


class MainScreen(QWidget):
    logout = pyqtSignal()
    def __init__(self, user, sender, p=None):
        super().__init__(p); self.user=user; self.sender=sender; self.tab=TABS[0]
        self._ui(); sender.status_sig.connect(self._status)

    def _ui(self):
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); v.setSpacing(0)

        # Шапка
        hdr=QFrame(); hdr.setFixedHeight(50)
        hdr.setStyleSheet(f"background:{CARD}; border-bottom:1px solid {BORD};")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(0,0,10,0); hl.setSpacing(0)

        bar=QFrame(); bar.setFixedSize(4,50)
        bar.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {N1},stop:0.5 {N2},stop:1 {N3});")
        hl.addWidget(bar); hl.addSpacing(12)

        il=QVBoxLayout(); il.setSpacing(1)
        t1=QLabel("МК-52  //  ДАТАПАД"); t1.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:700; font-family:'Segoe UI';")
        t2=QLabel(f"{self.user['rank']}  ·  {self.user['callsign']}  #{self.user['num']}")
        t2.setStyleSheet(f"color:{TXT2}; font-size:11px; font-family:'Segoe UI';")
        il.addWidget(t1); il.addWidget(t2); hl.addLayout(il); hl.addStretch()

        def hbtn(txt,col,fn):
            b=QPushButton(txt); b.setFixedSize(76,30); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"QPushButton{{background:transparent;color:{col};border:1px solid {col}44;border-radius:5px;font-size:11px;font-weight:600;font-family:'Segoe UI';}}QPushButton:hover{{background:{col}18;border-color:{col}88;}}")
            b.clicked.connect(fn); hl.addWidget(b); hl.addSpacing(4)

        hbtn("⟳ СИНХР.", OK, self._sync)
        hbtn("ВЫЙТИ", ERR, self.logout.emit)
        v.addWidget(hdr)

        # Поле пациента
        pr=QFrame(); pr.setFixedHeight(36)
        pr.setStyleSheet(f"background:{BG}; border-bottom:1px solid {BORD};")
        pl=QHBoxLayout(pr); pl.setContentsMargins(12,0,12,0)
        pl.addWidget(QLabel("Пациент:").__class__("Пациент:"))
        # fix: proper label
        plab=QLabel("Пациент:")
        plab.setStyleSheet(f"color:{TXT3}; font-size:11px; font-weight:600; font-family:'Segoe UI';")
        self.pat=QLineEdit(); self.pat.setPlaceholderText("Имя / позывной пациента"); self.pat.setFixedHeight(26)
        self.pat.setStyleSheet(f"background:{CARD2}; color:{TEXT}; border:1px solid {BORD2}; border-radius:5px; padding:0 8px; font-family:'Segoe UI'; font-size:12px;")
        pl=QHBoxLayout(pr); pl.setContentsMargins(12,0,12,0)
        pl.addWidget(plab); pl.addSpacing(8); pl.addWidget(self.pat,1)
        v.addWidget(pr)

        # Вкладки
        tf=QFrame(); tf.setFixedHeight(32)
        tf.setStyleSheet(f"background:{CARD}; border-bottom:1px solid {BORD};")
        tl=QHBoxLayout(tf); tl.setContentsMargins(0,0,0,0); tl.setSpacing(0)
        self.tbtn={}
        for t in TABS:
            b=QPushButton(t); b.setFixedHeight(32); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _,tn=t: self._settab(tn))
            self.tbtn[t]=b; tl.addWidget(b)
        self._styletabs(); v.addWidget(tf)

        # Список
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"QScrollArea{{border:none;background:{BG};}}QScrollBar:vertical{{background:{CARD};width:4px;border-radius:2px;}}QScrollBar::handle:vertical{{background:{BORD2};border-radius:2px;}}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self.lw=QWidget(); self.lw.setStyleSheet(f"background:{BG};")
        self.ll=QVBoxLayout(self.lw); self.ll.setContentsMargins(8,8,8,8); self.ll.setSpacing(0); self.ll.addStretch()
        self.scroll.setWidget(self.lw); v.addWidget(self.scroll,1)

        # Статусбар
        self.stbar=QLabel(f"ЛКМ — один шаг  ·  ПКМ или кнопка ▶ — все шаги  ·  Горячая клавиша: {HOTKEY}")
        self.stbar.setFixedHeight(22); self.stbar.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.stbar.setStyleSheet(f"background:{CARD};color:{TXT3};font-size:10px;font-family:'Segoe UI';padding-left:12px;border-top:1px solid {BORD};")
        v.addWidget(self.stbar)

        self._refresh()

    def _styletabs(self):
        for name,btn in self.tbtn.items():
            c=TCOL.get(name,N1); active=(name==self.tab)
            if active:
                btn.setStyleSheet(f"QPushButton{{background:{CARD2};color:{c};border:none;border-bottom:2px solid {c};font-size:11px;font-weight:700;font-family:'Segoe UI';padding:0 12px;}}")
            else:
                btn.setStyleSheet(f"QPushButton{{background:{CARD};color:{TXT3};border:none;border-bottom:2px solid transparent;border-right:1px solid {BORD};font-size:11px;font-family:'Segoe UI';padding:0 12px;}}QPushButton:hover{{background:{CARD2};color:{TXT2};}}")

    def _settab(self, name):
        self.tab=name; self._styletabs(); self._refresh()

    def _refresh(self):
        while self.ll.count()>1:
            item=self.ll.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for act in ACTIONS:
            if act["tab"]!=self.tab: continue
            c=TCOL.get(self.tab,N1)

            # Заголовок
            grp=QFrame(); grp.setFixedHeight(30)
            grp.setStyleSheet(f"background:{CARD};border-left:3px solid {c};margin-top:4px;margin-bottom:2px;")
            gl=QHBoxLayout(grp); gl.setContentsMargins(10,0,10,0)
            lb=QLabel(act["label"]); lb.setStyleSheet(f"color:{TEXT};font-size:12px;font-weight:700;font-family:'Segoe UI';background:transparent;")
            tg=QLabel(act["tag"]); tg.setStyleSheet(f"color:{TXT3};font-size:10px;font-family:'Segoe UI';background:transparent;")
            gl.addWidget(lb); gl.addStretch(); gl.addWidget(tg)
            self.ll.insertWidget(self.ll.count()-1, grp)

            # Шаги
            for i,step in enumerate(act["steps"]):
                row=QFrame(); row.setFixedHeight(28)
                row.setStyleSheet(f"background:{BG};border:none;")
                rl=QHBoxLayout(row); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)

                btn=QPushButton(); btn.setFixedHeight(28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip("ЛКМ — отправить этот шаг\nПКМ — отправить ВСЕ шаги")

                inner=QHBoxLayout(btn); inner.setContentsMargins(8,0,8,0); inner.setSpacing(6)
                num=QLabel(str(i+1)); num.setFixedWidth(16); num.setAlignment(Qt.AlignmentFlag.AlignCenter)
                num.setStyleSheet(f"color:{TXT3};font-size:10px;font-weight:600;font-family:'Segoe UI';")
                txt=QLabel(step); txt.setStyleSheet(f"color:{TXT2};font-size:12px;font-family:'Segoe UI';")
                inner.addWidget(num); inner.addWidget(txt,1)

                btn.setStyleSheet(f"QPushButton{{background:{BG};border:none;border-left:2px solid {BORD};text-align:left;}}QPushButton:hover{{background:{CARD2};border-left:2px solid {c};}}")

                all_steps=act["steps"]
                btn.clicked.connect(lambda _,s=step: self._one(s))

                class RClickBtn(QPushButton):
                    rclicked=pyqtSignal()
                    def mousePressEvent(self, e):
                        if e.button()==Qt.MouseButton.RightButton: self.rclicked.emit()
                        else: super().mousePressEvent(e)

                # Проще — сделаем нормально через eventFilter
                rl.addWidget(btn); self.ll.insertWidget(self.ll.count()-1, row)

            # Кнопка все шаги
            ab=QPushButton(f"  Все шаги: {act['label']}"); ab.setFixedHeight(26)
            ab.setCursor(Qt.CursorShape.PointingHandCursor)
            all_s=act["steps"]
            ab.clicked.connect(lambda _,s=all_s: self._all(s))
            ab.setStyleSheet(f"QPushButton{{background:transparent;color:{TXT3};border:1px solid {BORD};border-radius:4px;font-size:10px;font-weight:600;font-family:'Segoe UI';margin:2px 0 6px 0;text-align:left;padding-left:8px;}}QPushButton:hover{{background:{c}12;color:{c};border-color:{c}44;}}")
            self.ll.insertWidget(self.ll.count()-1, ab)

            div=QFrame(); div.setFrameShape(QFrame.Shape.HLine)
            div.setStyleSheet(f"border-color:{BORD};margin:0 4px;")
            self.ll.insertWidget(self.ll.count()-1, div)

    def _one(self, step): self.sender.send([step])
    def _all(self, steps): self.sender.send(steps)
    def _status(self, t, c):
        self.stbar.setText(t)
        self.stbar.setStyleSheet(f"background:{CARD};color:{c};font-size:10px;font-family:'Segoe UI';padding-left:12px;border-top:1px solid {BORD};")
    def _sync(self):
        self._status("Синхронизация...", WARN)
        rl=RosterLoader(); rl.done.connect(lambda u,ok,m: self._status(f"Обновлено: {m}" if ok else f"Ошибка: {m}", OK if ok else ERR)); rl.start()


class App(QMainWindow):
    tog=pyqtSignal()
    def __init__(self):
        super().__init__(); self.sender=GModSender()
        self.setWindowTitle("МК-52 Датапад"); self.setMinimumSize(580,660); self.resize(620,700)
        self.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.WindowStaysOnTopHint)
        screen=QApplication.primaryScreen().availableGeometry()
        self.move(screen.width()-640, 30)
        self.setStyleSheet(f"QMainWindow{{background:{BG};}}QWidget{{background:{BG};color:{TEXT};}}")
        self._icon()
        self._tray()
        self._login()
        if HAS_KEYBOARD:
            try: keyboard.add_hotkey(HOTKEY, lambda: self.tog.emit(), suppress=False)
            except: pass
        self.tog.connect(self._toggle)

    def _icon(self):
        px=QPixmap(32,32); px.fill(Qt.GlobalColor.transparent)
        p=QPainter(px); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g=QLinearGradient(0,0,32,32)
        g.setColorAt(0,QColor(N1)); g.setColorAt(0.5,QColor(N2)); g.setColorAt(1,QColor(N3))
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(2,2,28,28,6,6)
        p.setPen(QColor(TEXT)); p.setFont(QFont("Arial",10,QFont.Weight.Bold))
        p.drawText(QRect(0,0,32,32),Qt.AlignmentFlag.AlignCenter,"МК")
        p.end(); self.ico=QIcon(px); self.setWindowIcon(self.ico)

    def _tray(self):
        self.tray=QSystemTrayIcon(self.ico,self)
        m=QMenu(); m.setStyleSheet(f"QMenu{{background:{CARD};color:{TEXT};border:1px solid {BORD};}}QMenu::item:selected{{background:{CARD2};color:{N1};}}")
        m.addAction("Показать/Скрыть").triggered.connect(self._toggle)
        m.addSeparator(); m.addAction("Выход").triggered.connect(QApplication.quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(lambda r: self._toggle() if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.setToolTip(f"МК-52 Датапад [{HOTKEY}]"); self.tray.show()

    def _toggle(self):
        if self.isVisible() and not self.isMinimized(): self.hide()
        else: self.show(); self.raise_(); self.activateWindow()

    def _login(self):
        w=LoginScreen(); w.ok.connect(self._main); self.setCentralWidget(w)

    def _main(self, user):
        w=MainScreen(user, self.sender); w.logout.connect(self._login); self.setCentralWidget(w)

    def closeEvent(self, e):
        e.ignore(); self.hide()
        self.tray.showMessage("МК-52 Датапад",f"В трее. {HOTKEY} — открыть.",QSystemTrayIcon.MessageIcon.Information,2000)

    def paintEvent(self, e):
        super().paintEvent(e)
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g=QLinearGradient(0,0,self.width(),0)
        g.setColorAt(0,QColor(N1)); g.setColorAt(0.5,QColor(N2)); g.setColorAt(1,QColor(N3))
        p.setPen(QPen(QBrush(g),2)); p.drawLine(0,0,self.width(),0)


def main():
    app=QApplication(sys.argv)
    app.setApplicationName("МК-52 Датапад")
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Segoe UI",10))
    w=App(); w.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
