# -*- coding: utf-8 -*-
"""
Генератор постановлений об отмене постановления об отказе в ВУД
и сопроводительных писем.
Работает через подстановку в готовые .docx-шаблоны (XML-замена).
Прокуратура Карасунского административного округа г. Краснодара, каб. 14.

Структура папок рядом с программой:
  templates/
      otmena_KO.docx
      soprovod_s_otmenoy_v_KAO.docx
      otmena_GMR.docx
      soprovod_s_otmenoy_v_GMR.docx
  Отмены_КАО/
      ДД.ММ.ГГГГ/
          Постановление_КАО_КУСП_XXXXX.docx
          Сопровод_КАО_КУСП_XXXXX.docx
"""

import os, sys, json, copy, zipfile, shutil, datetime, tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ─────────────────────────────────────────────────────────────────────────────
# ПУТИ — определяем папку программы максимально надёжно
# ─────────────────────────────────────────────────────────────────────────────
def _get_app_dir():
    # 1) PyInstaller .exe
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # 2) Обычный .py — папка файла
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass
    # 3) Fallback — текущая рабочая директория
    return os.path.abspath(os.getcwd())

APP_DIR       = _get_app_dir()
TMPL_DIR      = os.path.join(APP_DIR, "templates")
OUT_ROOT      = os.path.join(APP_DIR, "Отмены_КАО")
SIGNERS_FILE  = os.path.join(APP_DIR, "otmena_signers.json")
SETTINGS_FILE = os.path.join(APP_DIR, "otmena_settings.json")

# Ключи шаблонов: dept_key -> (постановление, сопровод)
TMPL_KEYS = {
    "КАО": ("otmena_KO.docx",             "soprovod_s_otmenoy_v_KAO.docx"),
    "ГМР": ("otmena_GMR.docx",            "soprovod_s_otmenoy_v_GMR.docx"),
}

# ─────────────────────────────────────────────────────────────────────────────
# НАСТРОЙКИ ОТДЕЛОВ (редактируются в программе, сохраняются в JSON)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_DEPT = {
    "КАО": {
        "name_short":    "ОП (Карасунский округ)",
        "name_full":     "ОП (Карасунский округ) УМВД России по г. Краснодару",
        "sop_line2":     "(Карасунский округ)",
        "sop_line4":     "",
        "sop_line5":     "Бадалову А.Э.",
    },
    "ГМР": {
        "name_short":    "ОП (мкр. Гидростроителей)",
        "name_full":     "ОП (мкр. Гидростроителей) УМВД России по г. Краснодару",
        "sop_line2":     "(мкр. Гидростроителей)",
        "sop_line4":     "полковнику полиции",
        "sop_line5":     "Щербине А.Е.",
    },
}

def load_settings():
    s = {}
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
    except Exception:
        pass
    for dept, defaults in _DEFAULT_DEPT.items():
        if dept not in s:
            s[dept] = copy.deepcopy(defaults)
        else:
            for k, v in defaults.items():
                s[dept].setdefault(k, v)
    # Масштаб по умолчанию
    s.setdefault("ui_scale", 1.0)
    return s

def get_ui_scale():
    return float(DEPT.get("ui_scale", 1.0)) if "ui_scale" in DEPT else 1.0

def set_ui_scale(val):
    DEPT["ui_scale"] = float(val)
    save_settings(DEPT)

def save_settings(s):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

DEPT = load_settings()

# ─────────────────────────────────────────────────────────────────────────────
# ПОДПИСАНТЫ
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_SIGNERS = {
    "Иванов Д.С. (зам.)": {
        "post_doc":  "Заместитель прокурора Карасунского административного округа \nг. Краснодара советник юстиции",
        "fio_short": "Д.С. Иванов",
        "rank":      "советник юстиции",
        "post_sign": "Заместитель прокурора округа",
    },
    "Кириченко С.К. (прокурор)": {
        "post_doc":  "Прокурор Карасунского административного округа \nг. Краснодара старший советник юстиции",
        "fio_short": "С.К. Кириченко",
        "rank":      "старший советник юстиции",
        "post_sign": "Прокурор округа",
    },
    "Семенюта Г.К. (зам.)": {
        "post_doc":  "Заместитель прокурора Карасунского административного округа \nг. Краснодара советник юстиции",
        "fio_short": "Г.К. Семенюта",
        "rank":      "советник юстиции",
        "post_sign": "Заместитель прокурора округа",
    },
    "Сизо З.М. (зам.)": {
        "post_doc":  "Заместитель прокурора Карасунского административного округа \nг. Краснодара старший советник юстиции",
        "fio_short": "З.М. Сизо",
        "rank":      "старший советник юстиции",
        "post_sign": "Заместитель прокурора округа",
    },
    "Попов К.В. (и.о. зам.)": {
        "post_doc":  "И.о. заместителя прокурора Карасунского административного округа \nг. Краснодара младший советник юстиции",
        "fio_short": "К.В. Попов",
        "rank":      "младший советник юстиции",
        "post_sign": "И.о. заместителя прокурора округа",
    },
}
_BUILTIN_DEFAULT = "Иванов Д.С. (зам.)"

def load_signers():
    try:
        if os.path.exists(SIGNERS_FILE):
            with open(SIGNERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                raw  = data.get("list", {})
                dkey = data.get("default", "")
                if isinstance(raw, dict) and raw:
                    res = {}
                    for k, v in raw.items():
                        if isinstance(v, dict):
                            res[k] = v
                        elif isinstance(v, (list, tuple)) and len(v) >= 3:
                            res[k] = {"post_doc": str(v[0]), "fio_short": str(v[2]),
                                      "rank": str(v[1]), "post_sign": "Заместитель прокурора округа"}
                    if res:
                        if dkey not in res:
                            dkey = next(iter(res))
                        return res, dkey
    except Exception as e:
        print("load_signers:", e)
    return copy.deepcopy(_DEFAULT_SIGNERS), _BUILTIN_DEFAULT

def save_signers(signers, default_key):
    with open(SIGNERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"default": default_key, "list": signers}, f, ensure_ascii=False, indent=2)

SIGNERS, DEFAULT_SIGNER = load_signers()

# ─────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ
# ─────────────────────────────────────────────────────────────────────────────
_TOMA = {1:"в 1-м томе", 2:"в 2-х томах", 3:"в 3-х томах", 4:"в 4-х томах",
         5:"в 5-и томах", 6:"в 6-и томах", 7:"в 7-и томах", 8:"в 8-и томах",
         9:"в 9-и томах", 10:"в 10-и томах"}
def toma_phrase(n): return _TOMA.get(max(1, min(int(n), 10)), f"в {n} томах")

_MON = ["января","февраля","марта","апреля","мая","июня",
        "июля","августа","сентября","октября","ноября","декабря"]
def date_long(d):  return f"{d.day} {_MON[d.month-1]} {d.year} года"
def date_short(d): return d.strftime("%d.%m.%Y")


# ─────────────────────────────────────────────────────────────────────────────
# СКЛОНЕНИЕ ФИО
# ─────────────────────────────────────────────────────────────────────────────
def _decline_surname(s, case):
    """Склоняет фамилию. case: 'dat'|'gen'|'acc'"""
    last = s.lower()
    # Несклоняемые украинские окончания
    for suf in ('ко', 'чук', 'юк', 'як', 'ець', 'ич'):
        if last.endswith(suf): return s
    # -ский/-цкий
    for suf in ('ский', 'цкий', 'зкий', 'жский', 'чский', 'шский'):
        if last.endswith(suf):
            stem = s[:-2]
            if case == 'dat': return stem + 'ому'
            return stem + 'ого'
    # Адъективные
    if last.endswith('ой'):
        return (s[:-2] + 'ому') if case == 'dat' else (s[:-2] + 'ого')
    if last.endswith('ый'):
        return (s[:-2] + 'ому') if case == 'dat' else (s[:-2] + 'ого')
    if last.endswith('ий'):
        return (s[:-2] + 'ему') if case == 'dat' else (s[:-2] + 'его')
    # Женские на -ева/-ова/-ава
    for suf in ('ева', 'ова', 'ава'):
        if last.endswith(suf):
            if case == 'dat': return s[:-1] + 'ой'
            if case == 'gen': return s[:-1] + 'ой'
            return s[:-1] + 'у'
    # -ина/-ына (Щербина → Щербине)
    if last.endswith('ина') or last.endswith('ына'):
        if case == 'dat': return s[:-1] + 'е'
        if case == 'gen': return s[:-1] + 'ы'
        return s[:-1] + 'у'
    # -а/-я
    if last[-1] == 'а':
        stem = s[:-1]
        if case == 'dat': return stem + 'е'
        if case == 'gen': return stem + ('и' if last[-2] in 'жшщчгкх' else 'ы')
        return stem + 'у'
    if last[-1] == 'я':
        stem = s[:-1]
        if case == 'dat': return stem + 'е'
        if case == 'gen': return stem + 'и'
        return stem + 'ю'
    # Несклоняемые (гласная не а/я)
    if last[-1] in 'еёиоуыэюь': return s
    # Мужские на согласную
    if case == 'dat': return s + 'у'
    if case == 'gen': return s + 'а'
    return s + 'а'

def decline_fio(fio, case="dat"):
    """Склоняет строку 'Фамилия И.О.' в нужный падеж."""
    parts = fio.strip().split()
    if not parts: return fio
    rest = (" " + " ".join(parts[1:])) if len(parts) > 1 else ""
    return _decline_surname(parts[0], case) + rest


def safe(s):
    for c in r'\/:*?"<>|': s = s.replace(c, "_")
    return s.strip()

def nbsp(s):
    """
    Расставляет неразрывные пробелы \u00a0 в типичных юридических текстах,
    чтобы «г.», «ст.», «ч.», «п.», «УПК», «УК», «РФ» не оставались
    в одиночестве на новой строке.
    """
    import re as _re
    # г. Краснодар, г. Москва
    s = _re.sub(r'г\.\s+', 'г.\u00a0', s)
    # ст. 124, ч. 2, п. 6
    s = _re.sub(r'(ст|ч|п|пп|ул|д|кв|пр|мкр)\.(\s+)', lambda m: m.group(1)+'.\u00a0', s)
    # № 12345
    s = _re.sub(r'№\s+', '№\u00a0', s)
    # УПК РФ, УК РФ
    s = _re.sub(r'(УПК|УК)\s+(РФ)', '\\1\u00a0\\2', s)
    # 1 л. (приложение)
    s = _re.sub(r'(\d+)\s+л\.', '\\1\u00a0л.', s)
    return s

# ─────────────────────────────────────────────────────────────────────────────
# XML-ЗАМЕНА В DOCX (через lxml для корректного сохранения namespace)
# ─────────────────────────────────────────────────────────────────────────────
W_NS  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_TAG = f"{{{W_NS}}}"

try:
    from lxml import etree as _etree
    _USE_LXML = True
except ImportError:
    import xml.etree.ElementTree as _etree
    _USE_LXML = False
    # Регистрируем все namespace чтобы ET не переименовывал их
    for _p, _u in [
        ("wpc","http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"),
        ("cx","http://schemas.microsoft.com/office/drawing/2014/chartex"),
        ("mc","http://schemas.openxmlformats.org/markup-compatibility/2006"),
        ("o","urn:schemas-microsoft-com:office:office"),
        ("r","http://schemas.openxmlformats.org/officeDocument/2006/relationships"),
        ("m","http://schemas.openxmlformats.org/officeDocument/2006/math"),
        ("v","urn:schemas-microsoft-com:vml"),
        ("wp14","http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"),
        ("wp","http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
        ("w10","urn:schemas-microsoft-com:office:word"),
        ("w","http://schemas.openxmlformats.org/wordprocessingml/2006/main"),
        ("w14","http://schemas.microsoft.com/office/word/2010/wordml"),
        ("w15","http://schemas.microsoft.com/office/word/2012/wordml"),
        ("w16se","http://schemas.microsoft.com/office/word/2015/wordml/symex"),
        ("wpg","http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"),
        ("wpi","http://schemas.microsoft.com/office/word/2010/wordprocessingInk"),
        ("wne","http://schemas.microsoft.com/office/word/2006/wordml"),
        ("wps","http://schemas.microsoft.com/office/word/2010/wordprocessingShape"),
    ]:
        _etree.register_namespace(_p, _u)


def _xml_parse(path):
    """Парсит XML файл, возвращает (tree, root)."""
    if _USE_LXML:
        with open(path, "rb") as f:
            data = f.read()
        root = _etree.fromstring(data)
        return None, root
    else:
        tree = _etree.parse(path)
        return tree, tree.getroot()


def _xml_write(path, tree_or_none, root):
    """Сохраняет XML обратно в файл."""
    if _USE_LXML:
        data = _etree.tostring(root, xml_declaration=True,
                               encoding="UTF-8", standalone=True)
        with open(path, "wb") as f:
            f.write(data)
    else:
        tree_or_none.write(path, xml_declaration=True, encoding="UTF-8")


def _all_text(elem):
    """Собирает весь текст из всех w:t потомков."""
    return "".join((t.text or "") for t in elem.iter(f"{W_TAG}t"))


def _replace_text(para, new_text, apply_nbsp=True):
    """Заменяет текст параграфа, сохраняя форматирование первого run."""
    if apply_nbsp and new_text:
        new_text = nbsp(new_text)
    runs = list(para.findall(f"{W_TAG}r"))
    if not runs:
        return
    first = runs[0]
    for r in runs[1:]:
        para.remove(r)
    t_elems = list(first.findall(f"{W_TAG}t"))
    if t_elems:
        for t in t_elems[1:]:
            first.remove(t)
        t_elems[0].text = new_text
        if new_text and (new_text[0] == " " or new_text[-1] == " "):
            t_elems[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    else:
        t = _etree.SubElement(first, f"{W_TAG}t")
        t.text = new_text


def _normalize(s):
    """Нормализует строку: заменяет неразрывные пробелы/дефисы на обычные."""
    return s.replace("\u00a0"," ").replace("\u2011","-").replace("\u202f"," ")


def _find_para(root, search):
    """Ищет первый параграф во всём документе (включая таблицы), содержащий search."""
    for elem in root.iter(f"{W_TAG}p"):
        if search in _normalize(_all_text(elem)):
            return elem
    return None


def _find_para_body(body, search):
    """Ищет параграф только в прямых дочерних w:p тела документа."""
    paras = list(body.findall(f"{W_TAG}p"))
    for i, p in enumerate(paras):
        if search in _normalize(_all_text(p)):
            return i, p
    return -1, None


def _repack(tmp_dir, out_path):
    """Перепаковывает распакованную папку в docx."""
    tmp_zip = out_path + ".tmp"
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zout:
        for root_d, dirs, files in os.walk(tmp_dir):
            for fname in files:
                full = os.path.join(root_d, fname)
                arc  = os.path.relpath(full, tmp_dir).replace(os.sep, "/")
                zout.write(full, arc)
    os.replace(tmp_zip, out_path)

# ─────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ — ПОСТАНОВЛЕНИЕ
# ─────────────────────────────────────────────────────────────────────────────
def generate_postanovlenie(dept_key, doc_date, kusp_num, kusp_date,
                            otk_date, statya, actions, signer_key, out_path):
    import xml.etree.ElementTree as ET

    tmpl = os.path.join(TMPL_DIR, TMPL_KEYS[dept_key][0])
    if not os.path.exists(tmpl):
        raise FileNotFoundError(f"Шаблон не найден: {tmpl}")

    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    dept = DEPT[dept_key]

    post_doc  = sig["post_doc"]
    fio_short = sig["fio_short"]
    post_sign = sig["post_sign"]
    name_short = dept["name_short"]

    doc_str  = date_long(doc_date)
    kusp_str = date_short(kusp_date)
    otk_str  = date_short(otk_date)

    tmp = tempfile.mkdtemp(prefix="post_")
    try:
        with zipfile.ZipFile(tmpl, "r") as z:
            z.extractall(tmp)

        xml_path = os.path.join(tmp, "word", "document.xml")
        tree, root = _xml_parse(xml_path)
        body = root.find(f"{{{W_NS}}}body")
        paras = list(body.findall(f"{{{W_NS}}}p"))

        # ── P4: Город + дата ──
        # Шаблон: «г. Краснодар    ...    26 марта 2026 года»
        # Берём всё до даты (пробелы сохраняем) и меняем дату
        p4_orig = _all_text(paras[4])
        if "г. Краснодар" in p4_orig:
            # Находим позицию первой цифры после пробелов (начало старой даты)
            import re as _re
            m = _re.search(r'\d+\s+\w+\s+\d{4}\s+года', p4_orig)
            if m:
                new_p4 = p4_orig[:m.start()] + doc_str
            else:
                # Fallback: просто берём левую часть до большого пробела
                parts = p4_orig.split()
                # «г. Краснодар» это первые 2 слова, потом пробелы, потом дата
                left_end = p4_orig.index("Краснодар") + len("Краснодар")
                new_p4 = p4_orig[:left_end] + p4_orig[left_end:].rstrip()
                # Дописываем дату с теми же пробелами
                spaces = len(p4_orig) - len(p4_orig.rstrip()) - len(p4_orig.lstrip(p4_orig[:left_end]))
                new_p4 = p4_orig[:left_end] + " " * max(1, len(p4_orig) - left_end - len(doc_str)) + doc_str
            _replace_text(paras[4], new_p4)

        # ── P6: Преамбула ──
        new_p6 = (f"{post_doc} {fio_short} рассмотрев материалы проверки об отказе "
                  f"в возбуждении уголовного дела КУСП № {kusp_num} от {kusp_str},")
        _replace_text(paras[6], new_p6)

        # ── P10: Первый абзац УСТАНОВИЛ ──
        new_p10 = (f"{kusp_str} в КУСП {name_short} УМВД России "
                   f"по г. Краснодару зарегистрировано заявление о противоправных "
                   f"действиях (КУСП № {kusp_num} от {kusp_str}).")
        _replace_text(paras[10], new_p10)

        # ── P11: Второй абзац УСТАНОВИЛ ──
        new_p11 = (f"По данному сообщению проведена основная и дополнительная проверка, "
                   f"по результатам которой {otk_str} должностным лицом {name_short} "
                   f"УМВД России по г. Краснодару вынесено постановление об отказе "
                   f"в возбуждении уголовного дела в связи с отсутствием состава "
                   f"преступления, предусмотренного ст. {statya} УК РФ.")
        _replace_text(paras[11], new_p11)

        # ── P13: Незаконность ──
        new_p13 = (f"Изучением материалов проверки показало, что постановление об отказе "
                   f"в возбуждении уголовного дела от {otk_str} является незаконным "
                   f"и необоснованным, так как необходимые проверочные мероприятия "
                   f"в полном объёме не проведены, в связи с чем подлежит отмене.")
        _replace_text(paras[13], new_p13)

        # ── P15: Действия (первый пункт + клонирование) ──
        # P15 = первый пункт-шаблон, P16 = «- провести иные мероприятия...»
        action_tmpl = paras[15]
        fixed_last  = paras[16]
        clean_acts  = [a.strip() for a in actions if a.strip()]

        if clean_acts:
            _replace_text(action_tmpl, f"- {clean_acts[0]};")
            prev = action_tmpl
            for act in clean_acts[1:]:
                new_p = copy.deepcopy(action_tmpl)
                _replace_text(new_p, f"- {act};")
                children = list(body)
                idx = children.index(prev)
                body.insert(idx + 1, new_p)
                prev = new_p
        else:
            _replace_text(action_tmpl, "- ;")

        # Перечитываем параграфы после вставки
        paras = list(body.findall(f"{{{W_NS}}}p"))

        # ── ПОСТАНОВИЛ 1 ──
        i21, p21 = _find_para_body(body, "1. Постановление")
        if p21 is not None:
            new_p21 = (f"1. Постановление {name_short} УМВД России по "
                       f"г. Краснодару об отказе в возбуждении уголовного дела "
                       f"от {otk_str} по материалу проверки "
                       f"КУСП № {kusp_num} от {kusp_str} - отменить.")
            _replace_text(p21, new_p21)

        # ── ПОСТАНОВИЛ 2 ──
        i22, p22 = _find_para_body(body, "2. Материал проверки")
        if p22 is not None:
            new_p22 = (f"2. Материал проверки КУСП № {kusp_num} от {kusp_str} "
                       f"для организации дополнительной проверки направить начальнику "
                       f"{name_short} УМВД России по г. Краснодару.")
            _replace_text(p22, new_p22)

        # ── Строка подписи ──
        p_sign = None
        for marker in ["Заместитель прокурора округа", "Прокурор округа",
                       "И.о. заместителя прокурора округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig = _all_text(p_sign)
                # Сохраняем пробелы между должностью и ФИО
                after_post = orig[orig.index(marker) + len(marker):]
                spaces_cnt = len(after_post) - len(after_post.lstrip())
                new_sign   = post_sign + after_post[:spaces_cnt] + fio_short
                _replace_text(p_sign, new_sign)
                break

        _xml_write(xml_path, tree, root)
        _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ — СОПРОВОДИТЕЛЬНОЕ ПИСЬМО
# ─────────────────────────────────────────────────────────────────────────────
def generate_soprovod(dept_key, kusp_num, kusp_date, toma, signer_key, out_path):
    import xml.etree.ElementTree as ET

    tmpl = os.path.join(TMPL_DIR, TMPL_KEYS[dept_key][1])
    if not os.path.exists(tmpl):
        raise FileNotFoundError(f"Шаблон не найден: {tmpl}")

    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    dept = DEPT[dept_key]

    fio_short  = sig["fio_short"]
    post_sign  = sig["post_sign"]
    kusp_str   = date_short(kusp_date)
    toma_str   = toma_phrase(toma)

    tmp = tempfile.mkdtemp(prefix="sop_")
    try:
        with zipfile.ZipFile(tmpl, "r") as z:
            z.extractall(tmp)

        xml_path = os.path.join(tmp, "word", "document.xml")
        tree, root = _xml_parse(xml_path)

        # ── Адресат: строка 2 (округ) ──
        # КАО: «(Карасунский округ)»   ГМР: «(мкр. Гидростроителей)»
        for old in ["(Карасунский округ)", "(мкр. Гидростроителей)"]:
            p = _find_para(root, old)
            if p is not None:
                _replace_text(p, dept["sop_line2"])
                break

        # ── Адресат: строка 4 (звание, если есть) ──
        # В шаблоне КАО этой строки нет (пустая), в ГМР = «полковнику полиции»
        for old in ["полковнику полиции", "генерал-майору", "подполковнику"]:
            p = _find_para(root, old)
            if p is not None:
                _replace_text(p, dept["sop_line4"])
                break

        # ── Адресат: строка 5 (Фамилия И.О.) ──
        for old in ["Бадалову А.Э.", "Щербине А.Е."]:
            p = _find_para(root, old)
            if p is not None:
                _replace_text(p, dept["sop_line5"])
                break

        # ── Основной текст ──
        p_napr = _find_para(root, "Направляю для организации")
        if p_napr is not None:
            _replace_text(p_napr,
                          f"Направляю для организации дополнительной проверки материал   "
                          f"КУСП № {kusp_num} от {kusp_str}.")

        # ── Приложение ──
        p_pril = _find_para(root, "Приложение:")
        if p_pril is not None:
            _replace_text(p_pril,
                          f"Приложение: постановление об отмене постановления об отказе "
                          f"в возбуждении уголовного дела на 1\u00a0л., материл проверки "
                          f"КУСП № {kusp_num} от {kusp_str} {toma_str}.")

        # ── Подпись ──
        for marker in ["Заместитель прокурора округа", "Прокурор округа",
                       "И.о. заместителя прокурора округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig = _all_text(p_sign)
                after = orig[orig.index(marker) + len(marker):]
                spaces_cnt = len(after) - len(after.lstrip())
                _replace_text(p_sign, post_sign + after[:spaces_cnt] + fio_short, apply_nbsp=False)
                break

        _xml_write(xml_path, tree, root)
        _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# ВИДЖЕТ ДАТЫ
# ─────────────────────────────────────────────────────────────────────────────
class DateEntry(tk.Frame):
    def __init__(self, master, bg="#f4f1e8", initial_today=True, **kw):
        super().__init__(master, bg=bg)
        val = datetime.date.today().strftime("%d.%m.%Y") if initial_today else ""
        self._var = tk.StringVar(value=val)
        tk.Entry(self, textvariable=self._var, width=12,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Button(self, text="сегодня", font=("Segoe UI", 8),
                  command=self._today, padx=4, pady=0).pack(side="left", padx=3)

    def _today(self):
        self._var.set(datetime.date.today().strftime("%d.%m.%Y"))

    def get_date(self):
        v = self._var.get().strip()
        for fmt in ("%d.%m.%Y", "%d.%m.%y"):
            try:
                return datetime.datetime.strptime(v, fmt).date()
            except ValueError:
                pass
        return None

    def get(self): return self._var.get()
    def set(self, s): self._var.set(s)


# ─────────────────────────────────────────────────────────────────────────────
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Отмена постановления об отказе в ВУД — КАО")
        self.geometry("920x840")
        self.minsize(800, 640)
        self.configure(bg="#0b3d2e")
        self._check_templates()
        self._build_header()
        self._build_bottom_buttons()
        self._build_scroll_area()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # Применяем сохранённый масштаб
        try:
            sc = get_ui_scale()
            if sc != 1.0:
                self.tk.call("tk", "scaling", sc * 1.333)
        except Exception:
            pass

    # ── Шаблоны ──────────────────────────────────────────────────────────
    def _check_templates(self):
        global TMPL_DIR, APP_DIR
        os.makedirs(TMPL_DIR, exist_ok=True)
        missing = []
        for dept, (p, s) in TMPL_KEYS.items():
            for fn in (p, s):
                if not os.path.exists(os.path.join(TMPL_DIR, fn)):
                    missing.append(fn)
        if missing:
            msg = (
                f"Шаблоны не найдены в папке:\n{TMPL_DIR}\n\n"
                f"Убедитесь, что рядом с otmena_app.py есть папка templates/ "
                f"с файлами шаблонов.\n\n"
                f"Нужные файлы:\n" +
                "\n".join(f"  {f}" for f in missing) +
                "\n\nХотите вручную указать папку с шаблонами?"
            )
            if messagebox.askyesno("Шаблоны не найдены", msg):
                chosen = filedialog.askdirectory(
                    title="Выберите папку с шаблонами (templates/)",
                    initialdir=APP_DIR)
                if chosen:
                    TMPL_DIR = chosen
                    # Проверим ещё раз
                    still_missing = [
                        fn for dept, (p, s) in TMPL_KEYS.items()
                        for fn in (p, s)
                        if not os.path.exists(os.path.join(TMPL_DIR, fn))
                    ]
                    if still_missing:
                        messagebox.showwarning(
                            "Шаблоны",
                            f"В выбранной папке всё равно не найдены:\n" +
                            "\n".join(still_missing))
                    else:
                        messagebox.showinfo("Шаблоны", "Шаблоны найдены! ✅")

    # ── Шапка ────────────────────────────────────────────────────────────
    def _build_header(self):
        tk.Label(self, text="ПРОКУРАТУРА", bg="#0b3d2e", fg="#f5d77a",
                 font=("Times New Roman", 22, "bold")).pack(pady=(14, 2))
        tk.Label(self, bg="#0b3d2e", fg="white", font=("Segoe UI", 10), wraplength=880,
                 text="Генератор постановлений об отмене отказа в ВУД + сопроводительных писем"
                 ).pack()
        self._lbl_clk = tk.Label(self, text="", bg="#0b3d2e", fg="#d4af37",
                                  font=("Consolas", 11, "bold"))
        self._lbl_clk.pack(pady=(3, 0))
        self._tick()
        tk.Label(self, bg="#0b3d2e", fg="#8B6914", font=("Segoe UI", 7),
                 text="✦ ──────────────────────────────────────────────────────── ✦"
                 ).pack()

    def _tick(self):
        try:
            now = datetime.datetime.now()
            d   = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"][now.weekday()]
            self._lbl_clk.config(
                text=f"{d}  {now.strftime('%d.%m.%Y')}  {now.strftime('%H:%M:%S')}")
        except Exception: pass
        self.after(1000, self._tick)

    # ── Нижние кнопки ────────────────────────────────────────────────────
    def _build_bottom_buttons(self):
        tk.Label(self, bg="#0b3d2e", fg="#cfcfcf", font=("Segoe UI", 8, "italic"),
                 text="Разработано каб. 14 Прокуратуры КАО г. Краснодар"
                 ).pack(side="bottom", pady=3)
        btns = tk.Frame(self, bg="#0b3d2e")
        btns.pack(side="bottom", fill="x", pady=6)

        def b(t, cmd, bg="#fffef7", fg="#0b3d2e", bold=False):
            tk.Button(btns, text=t, command=cmd, bg=bg, fg=fg,
                      font=("Segoe UI", 10, "bold" if bold else "normal"),
                      padx=10, pady=5, cursor="hand2").pack(side="left", padx=4)

        b("📝 Создать документы",  self._generate,        bg="#f5d77a", bold=True)
        b("🔄 Предпросмотр",       self._preview_update,  bg="#2e5c8a", fg="white")
        b("✍ Подписанты",          self.open_signers,      bg="#d4af37")
        b("🏛 Настройки отделов",  self.open_dept_settings,bg="#d4af37")
        tk.Button(btns, text="🔍 Масштаб",
                  command=self._open_scale,
                  font=("Segoe UI", 9), padx=8, pady=5, cursor="hand2"
                  ).pack(side="left", padx=3)
        b("📂 Папка вывода",       self._open_out)
        b("🧹 Очистить форму",     self._clear)
        tk.Button(btns, text="📁 Жалобы",
                  command=self._open_zhaloba,
                  bg="#c0392b", fg="white",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=5, cursor="hand2"
                  ).pack(side="right", padx=10)

    # ── Прокрутка ─────────────────────────────────────────────────────────
    def _build_scroll_area(self):
        outer = tk.Frame(self, bg="#0b3d2e"); outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg="#0b3d2e", highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(cv, bg="#0b3d2e")
        win = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",   lambda e: cv.itemconfigure(win, width=e.width))
        cv.bind_all("<MouseWheel>", lambda e: cv.yview_scroll(-1*int(e.delta/120), "units"))
        self._build_form(inner)

    # ── Форма ─────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        BG = "#f4f1e8"
        frm = tk.Frame(parent, bg=BG, bd=2, relief="ridge")
        frm.pack(padx=18, pady=14, fill="both", expand=True)
        frm.columnconfigure(1, weight=1)
        R = 0

        def lbl(txt, r):
            tk.Label(frm, text=txt, bg=BG, font=("Segoe UI", 10, "bold"), anchor="w"
                     ).grid(row=r, column=0, sticky="nw", padx=8, pady=5)

        def sep():
            nonlocal R
            ttk.Separator(frm, orient="horizontal").grid(
                row=R, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
            R += 1

        # ① Подразделение
        lbl("① Подразделение (отдел полиции):", R)
        df = tk.Frame(frm, bg=BG); df.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        self._dept = tk.StringVar(value="КАО")
        for txt, val in [("ОП (Карасунский округ) — КАО", "КАО"),
                         ("ОП (мкр. Гидростроителей) — ГМР", "ГМР")]:
            tk.Radiobutton(df, text=txt, variable=self._dept, value=val,
                           bg=BG, font=("Segoe UI", 10), selectcolor=BG,
                           activebackground=BG).pack(side="left", padx=10)
        R += 1; sep()

        # ② Дата постановления
        lbl("② Дата постановления:", R)
        self._date_doc = DateEntry(frm, bg=BG)
        self._date_doc.grid(row=R, column=1, sticky="w", padx=6, pady=5); R += 1

        # ③ КУСП
        lbl("③ Номер КУСП:", R)
        kf = tk.Frame(frm, bg=BG); kf.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        tk.Label(kf, text="КУСП №", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._kusp_num = tk.Entry(kf, width=12, font=("Segoe UI", 10))
        self._kusp_num.pack(side="left", padx=4)
        tk.Label(kf, text="от", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._date_kusp = DateEntry(kf, bg=BG)
        self._date_kusp.pack(side="left", padx=4)
        R += 1

        # ④ Дата отказа
        lbl("④ Дата постановления об отказе:", R)
        self._date_otk = DateEntry(frm, bg=BG, initial_today=False)
        self._date_otk.grid(row=R, column=1, sticky="w", padx=6, pady=5); R += 1

        # ⑤ Статья
        lbl("⑤ Статья УК РФ:", R)
        sf = tk.Frame(frm, bg=BG); sf.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        tk.Label(sf, text="ст.", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._statya = tk.Entry(sf, width=14, font=("Segoe UI", 10))
        self._statya.insert(0, "327"); self._statya.pack(side="left", padx=4)
        tk.Label(sf, text="УК РФ", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        R += 1; sep()

        # ⑥ Действия
        lbl("⑥ Действия для доп. проверки:", R)
        tk.Label(frm, bg=BG, fg="#666", font=("Segoe UI", 8, "italic"),
                 text='(финальный пункт «провести иные мероприятия» добавляется автоматически)'
                 ).grid(row=R, column=1, sticky="w", padx=6); R += 1

        self._acts_frame = tk.Frame(frm, bg=BG)
        self._acts_frame.grid(row=R, column=0, columnspan=2, sticky="ew", padx=8); R += 1
        self._act_rows = []

        tk.Button(frm, text="+ добавить пункт",
                  font=("Segoe UI", 9), bg="#d4af37", fg="#0b3d2e",
                  padx=8, pady=2, cursor="hand2", command=self._add_act
                  ).grid(row=R, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        R += 1; sep()

        self._add_act("выполнить требования прокуратуры округа от")

        # ⑦ Томов
        lbl("⑦ Кол-во томов материала:", R)
        tf = tk.Frame(frm, bg=BG); tf.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        self._toma = tk.IntVar(value=1)
        ttk.Spinbox(tf, from_=1, to=10, textvariable=self._toma,
                    width=5, font=("Segoe UI", 10)).pack(side="left")
        self._lbl_toma = tk.Label(tf, text=toma_phrase(1), bg=BG, fg="#0b3d2e",
                                   font=("Segoe UI", 10, "italic"))
        self._lbl_toma.pack(side="left", padx=8)
        self._toma.trace_add("write", lambda *_: self._lbl_toma.config(
            text=toma_phrase(self._toma.get())))
        R += 1

        # ⑧ Подписант
        lbl("⑧ Подписант:", R)
        self._signer_var = tk.StringVar(value=DEFAULT_SIGNER)
        self._cmb_signer = ttk.Combobox(frm, textvariable=self._signer_var,
                                         values=list(SIGNERS.keys()),
                                         width=46, state="readonly")
        self._cmb_signer.grid(row=R, column=1, sticky="w", padx=6, pady=5); R += 1
        sep()

        # Предпросмотр
        tk.Label(frm, text="Предпросмотр текста:", bg=BG,
                 font=("Segoe UI", 10, "bold")).grid(
            row=R, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 2)); R += 1
        pf = tk.Frame(frm, bg=BG)
        pf.grid(row=R, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        pvsb = tk.Scrollbar(pf); pvsb.pack(side="right", fill="y")
        self._preview_txt = tk.Text(pf, height=13, wrap="word",
                                    font=("Times New Roman", 11),
                                    bg="#fffef7", fg="#0b3d2e",
                                    yscrollcommand=pvsb.set,
                                    state="disabled", relief="flat", bd=1,
                                    padx=8, pady=6)
        self._preview_txt.pack(fill="both", expand=True)
        pvsb.config(command=self._preview_txt.yview)

    # ── Пункты действий ───────────────────────────────────────────────────
    def _add_act(self, default=""):
        BG = "#f4f1e8"
        idx = len(self._act_rows) + 1
        rf  = tk.Frame(self._acts_frame, bg=BG); rf.pack(fill="x", pady=2)
        tk.Label(rf, text=f"{idx}.", bg=BG, font=("Segoe UI", 10), width=3).pack(side="left")
        var = tk.StringVar(value=default)
        tk.Entry(rf, textvariable=var, width=74, font=("Segoe UI", 10)).pack(side="left", padx=4)
        data = [rf, var]
        tk.Button(rf, text="×", fg="#aa0000", font=("Segoe UI", 9, "bold"), width=2,
                  command=lambda d=data: self._del_act(d)).pack(side="left")
        self._act_rows.append(data)
        self._renumber_acts()

    def _del_act(self, data):
        if data in self._act_rows: self._act_rows.remove(data)
        data[0].destroy(); self._renumber_acts()

    def _renumber_acts(self):
        for i, (rf, _) in enumerate(self._act_rows):
            ch = rf.winfo_children()
            if ch and isinstance(ch[0], tk.Label): ch[0].config(text=f"{i+1}.")

    # ── Сбор данных ───────────────────────────────────────────────────────
    def _collect(self):
        def err(msg): messagebox.showerror("Ошибка", msg); return None
        doc_d  = self._date_doc.get_date()
        if not doc_d:   return err("Некорректная дата постановления.")
        kusp_n = self._kusp_num.get().strip()
        if not kusp_n:  return err("Введите номер КУСП.")
        kusp_d = self._date_kusp.get_date()
        if not kusp_d:  return err("Некорректная дата КУСП.")
        otk_d  = self._date_otk.get_date()
        if not otk_d:   return err("Введите дату постановления об отказе.")
        st = self._statya.get().strip()
        if not st:      return err("Введите статью УК РФ.")
        acts = [v.get().strip() for _, v in self._act_rows if v.get().strip()]
        return dict(dept=self._dept.get(), doc_date=doc_d,
                    kusp_num=kusp_n, kusp_date=kusp_d, otk_date=otk_d,
                    statya=st, actions=acts, toma=self._toma.get(),
                    signer=self._signer_var.get())

    # ── Предпросмотр ──────────────────────────────────────────────────────
    def _preview_update(self):
        d = self._collect()
        if not d: return
        dep = DEPT[d["dept"]]
        sig = SIGNERS.get(d["signer"], list(SIGNERS.values())[0])
        ns  = dep["name_short"]
        ks  = date_short(d["kusp_date"])
        os_ = date_short(d["otk_date"])
        lines = [
            "ПОСТАНОВЛЕНИЕ",
            "об отмене постановления об отказе в возбуждении уголовного дела",
            "и направлении материала для дополнительной проверки", "",
            f"г. Краснодар                        {date_long(d['doc_date'])}", "",
            f"{sig['post_doc']} {sig['fio_short']} рассмотрев материалы проверки об отказе "
            f"в возбуждении уголовного дела КУСП № {d['kusp_num']} от {ks},", "",
            "УСТАНОВИЛ:", "",
            f"{ks} в КУСП {ns} УМВД России по г. Краснодару "
            f"зарегистрировано заявление о противоправных действиях "
            f"(КУСП № {d['kusp_num']} от {ks}).", "",
            f"По данному сообщению проведена основная и дополнительная проверка, "
            f"по результатам которой {os_} должностным лицом {ns} "
            f"УМВД России по г. Краснодару вынесено постановление об отказе "
            f"в возбуждении уголовного дела в связи с отсутствием состава "
            f"преступления, предусмотренного ст. {d['statya']} УК РФ.", "",
            "В ходе дополнительной проверки необходимо выполнить следующее:",
        ]
        for a in d["actions"]: lines.append(f"- {a};")
        lines += ["- провести иные мероприятия необходимость в которых возникает.", "",
                  "ПОСТАНОВИЛ:", "",
                  f"1. Постановление {ns} УМВД России по г. Краснодару "
                  f"об отказе в возбуждении уголовного дела от {os_} "
                  f"по материалу проверки КУСП № {d['kusp_num']} от {ks} - отменить.", "",
                  f"2. Материал проверки КУСП № {d['kusp_num']} от {ks} "
                  f"направить начальнику {ns} УМВД России по г. Краснодару.", "",
                  f"{sig['post_sign']}                    {sig['fio_short']}", "",
                  "─"*60, "СОПРОВОДИТЕЛЬНОЕ ПИСЬМО",
                  f"Направляю материал КУСП № {d['kusp_num']} от {ks}.",
                  f"Приложение: ... КУСП № {d['kusp_num']} от {ks} {toma_phrase(d['toma'])}."]
        self._preview_txt.config(state="normal")
        self._preview_txt.delete("1.0", "end")
        self._preview_txt.insert("1.0", "\n".join(lines))
        self._preview_txt.config(state="disabled")

    # ── Создание файлов ───────────────────────────────────────────────────
    def _generate(self):
        d = self._collect()
        if not d: return
        folder = os.path.join(OUT_ROOT, datetime.date.today().strftime("%d.%m.%Y"))
        os.makedirs(folder, exist_ok=True)
        ks = safe(d["kusp_num"])
        dk = safe(d["dept"])
        pname = f"Постановление_{dk}_КУСП_{ks}.docx"
        sname = f"Сопровод_{dk}_КУСП_{ks}.docx"
        ppath = os.path.join(folder, pname)
        spath = os.path.join(folder, sname)
        errs  = []
        try:
            generate_postanovlenie(d["dept"], d["doc_date"], d["kusp_num"],
                                   d["kusp_date"], d["otk_date"], d["statya"],
                                   d["actions"], d["signer"], ppath)
        except Exception as e: errs.append(f"Постановление: {e}")
        try:
            generate_soprovod(d["dept"], d["kusp_num"], d["kusp_date"],
                               d["toma"], d["signer"], spath)
        except Exception as e: errs.append(f"Сопровод: {e}")
        if errs:
            messagebox.showerror("Ошибки", "\n\n".join(errs)); return
        msg = f"✅ Документы созданы:\n\n📄 {pname}\n📄 {sname}\n\n📁 {folder}"
        if messagebox.askyesno("Готово", msg + "\n\nОткрыть папку?"):
            try:
                if sys.platform.startswith("win"): os.startfile(folder)
                else:
                    import subprocess; subprocess.Popen(["xdg-open", folder])
            except Exception: pass

    def _open_zhaloba(self):
        ZhalobaWindow(self)

    def _open_scale(self):
        global DEPT
        w = tk.Toplevel(self); w.title("Масштаб интерфейса")
        w.configure(bg="#f4f1e8"); w.geometry("340x180")
        w.transient(self); w.grab_set()
        tk.Label(w, text="🔍 Масштаб интерфейса",
                 bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        frm = tk.Frame(w, bg="#f4f1e8"); frm.pack(fill="both", expand=True, padx=16, pady=14)
        tk.Label(frm, text="Масштаб (%):", bg="#f4f1e8",
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="e", padx=6, pady=8)
        scale_var = tk.IntVar(value=int(get_ui_scale() * 100))
        scale_spin = ttk.Spinbox(frm, from_=70, to=200, increment=10,
                                  textvariable=scale_var, width=7,
                                  font=("Segoe UI", 10))
        scale_spin.grid(row=0, column=1, sticky="w", padx=6, pady=8)
        tk.Label(frm, text="(100 = стандарт, 120 = крупнее)",
                 bg="#f4f1e8", fg="#666",
                 font=("Segoe UI", 8, "italic")).grid(row=1, column=0, columnspan=2, pady=2)
        def do_apply():
            val = scale_var.get() / 100.0
            set_ui_scale(val)
            self._apply_scale(val)
            w.destroy()
        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=16, pady=6)
        tk.Button(bf, text="✅ Применить и перезапустить",
                  command=do_apply, bg="#f5d77a", fg="#0b3d2e",
                  font=("Segoe UI", 10, "bold"), padx=10, pady=4).pack(side="right")
        tk.Button(bf, text="Отмена", command=w.destroy,
                  padx=10, pady=4).pack(side="right", padx=4)

    def _apply_scale(self, scale):
        """Применяет масштаб — перезапускает приложение через os.execv."""
        try:
            import subprocess
            python = sys.executable
            script = os.path.abspath(__file__)
            self.destroy()
            os.execv(python, [python, script])
        except Exception as e:
            messagebox.showinfo("Масштаб", f"Настройки сохранены.\nПерезапустите программу вручную.\n{e}")

    def _open_out(self):
        os.makedirs(OUT_ROOT, exist_ok=True)
        try:
            if sys.platform.startswith("win"): os.startfile(OUT_ROOT)
            else:
                import subprocess; subprocess.Popen(["xdg-open", OUT_ROOT])
        except Exception as e: messagebox.showerror("Ошибка", str(e))

    def _clear(self):
        if not messagebox.askyesno("Очистить форму", "Сбросить все поля?"): return
        self._dept.set("КАО")
        self._date_doc.set(datetime.date.today().strftime("%d.%m.%Y"))
        self._kusp_num.delete(0, "end")
        self._date_kusp.set(datetime.date.today().strftime("%d.%m.%Y"))
        self._date_otk.set("")
        self._statya.delete(0, "end"); self._statya.insert(0, "327")
        for d in list(self._act_rows): d[0].destroy()
        self._act_rows.clear()
        self._add_act("выполнить требования прокуратуры округа от")
        self._toma.set(1)
        self._preview_txt.config(state="normal")
        self._preview_txt.delete("1.0", "end")
        self._preview_txt.config(state="disabled")

    # ─────────────────────────────────────────────────────────────────────
    # РЕДАКТОР ПОДПИСАНТОВ
    # ─────────────────────────────────────────────────────────────────────
    def open_signers(self):
        global SIGNERS, DEFAULT_SIGNER
        w = tk.Toplevel(self); w.title("Подписанты — управление")
        w.configure(bg="#f4f1e8"); w.geometry("800x520")
        w.transient(self); w.grab_set()

        tk.Label(w, text="Справочник подписантов", bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        tk.Label(w, text="★ — по умолчанию.  Двойной клик — изменить.",
                 bg="#f4f1e8", fg="#555", font=("Segoe UI", 9, "italic")
                 ).pack(anchor="w", padx=10, pady=(6, 2))

        body = tk.Frame(w, bg="#f4f1e8"); body.pack(fill="both", expand=True, padx=10, pady=4)
        lb   = tk.Listbox(body, font=("Segoe UI", 10), activestyle="dotbox", width=38)
        sb   = tk.Scrollbar(body, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True); sb.pack(side="left", fill="y")

        info = tk.Label(w, text="", bg="#f4f1e8", fg="#0b3d2e",
                        font=("Segoe UI", 9), justify="left", anchor="w", wraplength=760)
        info.pack(fill="x", padx=10, pady=(2, 4))

        def refresh(sel=None):
            lb.delete(0, "end")
            for k in SIGNERS:
                lb.insert("end", ("★ " if k == DEFAULT_SIGNER else "  ") + k)
            if sel and sel in list(SIGNERS.keys()):
                i = list(SIGNERS.keys()).index(sel)
                lb.selection_clear(0, "end"); lb.selection_set(i); lb.see(i); show(sel)
            elif SIGNERS:
                lb.selection_set(0); show(list(SIGNERS.keys())[0])
            self._refresh_cmb()

        def cur():
            s = lb.curselection()
            if not s: return None
            keys = list(SIGNERS.keys())
            return keys[s[0]] if 0 <= s[0] < len(keys) else None

        def show(k):
            if k and k in SIGNERS:
                sg = SIGNERS[k]
                info.config(text=f"В документе: {sg.get('post_doc','')}\n"
                                 f"Строка подписи: {sg.get('post_sign','')}   |   "
                                 f"ФИО: {sg.get('fio_short','')}")

        lb.bind("<<ListboxSelect>>", lambda e: show(cur()))

        def edit_dlg(ek=None):
            ed = tk.Toplevel(w); ed.title("Изменить" if ek else "Добавить")
            ed.configure(bg="#f4f1e8"); ed.transient(w); ed.grab_set()
            sg  = SIGNERS.get(ek, {}) if ek else {}
            fields = [
                ("Ключ (для выпадающего списка):",             ek or ""),
                ("Должность + звание в тексте документа:",     sg.get("post_doc", "")),
                ("Строка должности в подписи (кратко):",       sg.get("post_sign", "Заместитель прокурора округа")),
                ("Звание:",                                     sg.get("rank", "")),
                ("И.О. Фамилия (для строки подписи):",         sg.get("fio_short", "")),
            ]
            ents = []
            for r, (fl, fv) in enumerate(fields):
                tk.Label(ed, text=fl, bg="#f4f1e8", font=("Segoe UI", 9),
                         anchor="e", width=38).grid(row=r, column=0, sticky="e", padx=8, pady=6)
                ent = tk.Entry(ed, width=50, font=("Segoe UI", 10))
                ent.grid(row=r, column=1, sticky="w", padx=6, pady=6)
                ent.insert(0, fv); ents.append(ent)

            def do_save():
                global SIGNERS, DEFAULT_SIGNER
                k, pd, ps, rk, fi = [e.get().strip() for e in ents]
                if not k:  messagebox.showwarning("", "Укажите ключ.", parent=ed); return
                if not (pd and fi): messagebox.showwarning("", "Заполните все поля.", parent=ed); return
                if k != ek and k in SIGNERS:
                    messagebox.showwarning("", f"Ключ «{k}» существует.", parent=ed); return
                nv = {"post_doc": pd, "post_sign": ps, "rank": rk, "fio_short": fi}
                if ek and ek != k:
                    nm = {}
                    for ok, ov in SIGNERS.items(): nm[k if ok == ek else ok] = ov
                    nm[k] = nv; SIGNERS.clear(); SIGNERS.update(nm)
                    if DEFAULT_SIGNER == ek: DEFAULT_SIGNER = k
                else:
                    SIGNERS[k] = nv
                    if not DEFAULT_SIGNER or DEFAULT_SIGNER not in SIGNERS: DEFAULT_SIGNER = k
                save_signers(SIGNERS, DEFAULT_SIGNER); ed.destroy(); refresh(sel=k)

            bf = tk.Frame(ed, bg="#f4f1e8")
            bf.grid(row=len(fields), column=0, columnspan=2, sticky="e", padx=8, pady=8)
            tk.Button(bf, text="Сохранить", command=do_save, bg="#d4af37", fg="#0b3d2e",
                      font=("Segoe UI", 10, "bold"), padx=12, pady=3).pack(side="left", padx=4)
            tk.Button(bf, text="Отмена", command=ed.destroy,
                      padx=12, pady=3).pack(side="left", padx=4)
            ents[0].focus_set()

        def do_del():
            global DEFAULT_SIGNER
            k = cur()
            if not k: messagebox.showinfo("", "Выберите запись.", parent=w); return
            if len(SIGNERS) <= 1:
                messagebox.showwarning("", "Нельзя удалить последнего.", parent=w); return
            if not messagebox.askyesno("Удалить", f"Удалить «{k}»?", parent=w): return
            del SIGNERS[k]
            if DEFAULT_SIGNER == k: DEFAULT_SIGNER = next(iter(SIGNERS))
            save_signers(SIGNERS, DEFAULT_SIGNER); refresh()

        def do_def():
            global DEFAULT_SIGNER
            k = cur()
            if not k: messagebox.showinfo("", "Выберите запись.", parent=w); return
            DEFAULT_SIGNER = k; save_signers(SIGNERS, DEFAULT_SIGNER); refresh(sel=k)

        lb.bind("<Double-Button-1>", lambda e: edit_dlg(cur()))
        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=10, pady=(4, 10))
        for txt, cmd in [("➕ Добавить", lambda: edit_dlg(None)),
                         ("✎ Изменить",  lambda: edit_dlg(cur())),
                         ("🗑 Удалить",  do_del), ("★ По умолчанию", do_def)]:
            tk.Button(bf, text=txt, command=cmd, padx=10, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="Закрыть", command=w.destroy,
                  padx=10, pady=4).pack(side="right", padx=3)
        refresh()

    def _refresh_cmb(self):
        try:
            if hasattr(self, "_cmb_signer") and self._cmb_signer.winfo_exists():
                keys = list(SIGNERS.keys())
                self._cmb_signer["values"] = keys
                if self._signer_var.get() not in SIGNERS:
                    self._signer_var.set(DEFAULT_SIGNER if DEFAULT_SIGNER in SIGNERS
                                         else (keys[0] if keys else ""))
        except Exception: pass

    # ─────────────────────────────────────────────────────────────────────
    # РЕДАКТОР НАСТРОЕК ОТДЕЛОВ
    # ─────────────────────────────────────────────────────────────────────
    def open_dept_settings(self):
        global DEPT
        w = tk.Toplevel(self); w.title("Настройки отделов полиции")
        w.configure(bg="#f4f1e8"); w.geometry("780x560")
        w.transient(self); w.grab_set()

        tk.Label(w, text="⚙ Настройки отделов полиции",
                 bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        tk.Label(w, text="Данные подставляются в шаблоны при генерации документов.",
                 bg="#f4f1e8", fg="#555", font=("Segoe UI", 9, "italic")
                 ).pack(anchor="w", padx=10, pady=(4, 2))

        nb = ttk.Notebook(w); nb.pack(fill="both", expand=True, padx=10, pady=6)
        dept_ents = {}

        for dk, dv in DEPT.items():
            tab = tk.Frame(nb, bg="#f4f1e8"); nb.add(tab, text=f"  {dk}  ")
            fields = [
                ("name_short",  "Краткое название ОП (в тексте постановления):"),
                ("name_full",   "Полное название ОП:"),
                ("sop_line2",   "Адресат сопровода — строка 2 (округ/мкр):"),
                ("sop_line4",   "Адресат сопровода — строка 4 (звание, если есть):"),
                ("sop_line5",   "Адресат сопровода — строка 5 (Фамилия И.О.):"),
            ]
            ents = {}
            for r, (fk, fl) in enumerate(fields):
                tk.Label(tab, text=fl, bg="#f4f1e8", font=("Segoe UI", 9),
                         anchor="e", width=48
                         ).grid(row=r, column=0, sticky="e", padx=8, pady=6)
                ent = tk.Entry(tab, width=40, font=("Segoe UI", 10))
                ent.grid(row=r, column=1, sticky="w", padx=6, pady=6)
                ent.insert(0, dv.get(fk, "")); ents[fk] = ent
            dept_ents[dk] = ents

        def do_save():
            global DEPT
            for dk, ents in dept_ents.items():
                for fk, ent in ents.items():
                    DEPT[dk][fk] = ent.get().strip()
            save_settings(DEPT)
            messagebox.showinfo("Сохранено", "Настройки отделов сохранены.", parent=w)
            w.destroy()

        def do_reset():
            if not messagebox.askyesno("Сброс", "Сбросить к значениям по умолчанию?", parent=w):
                return
            for dk, ents in dept_ents.items():
                for fk, ent in ents.items():
                    ent.delete(0, "end"); ent.insert(0, _DEFAULT_DEPT.get(dk, {}).get(fk, ""))

        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=10, pady=(4, 10))
        tk.Button(bf, text="💾 Сохранить", command=do_save, bg="#f5d77a", fg="#0b3d2e",
                  font=("Segoe UI", 10, "bold"), padx=14, pady=5).pack(side="right", padx=4)
        tk.Button(bf, text="Отмена", command=w.destroy,
                  padx=14, pady=5).pack(side="right")
        tk.Button(bf, text="↺ Сбросить к умолчаниям", command=do_reset,
                  padx=10, pady=5).pack(side="left", padx=4)



# ═════════════════════════════════════════════════════════════════════════════
# МОДУЛЬ ЖАЛОБ — генерация 4 документов по жалобам на отказ в ВУД
# ═════════════════════════════════════════════════════════════════════════════

ZHALOBA_TMPLS = {
    # Вариант «отказ»
    "post":     "Postanovlenie_otkaz_v_ud_zhaloby.docx",
    "otvet":    "Otvet_otkaz_v_ud_zhaloby.docx",
    "prodlenka":"prodlenka_otkaz_v_ud_zhaloby.docx",
    "raport":   "raport_otkaz_v_ud_zhaloby.docx",
    # Вариант «удовлетворение»
    "post_ud":     "Postanovlenie_ud_zhaloby.docx",
    "otvet_ud":    "Otvet_ud_zhaloby.docx",
    "prodlenka_ud":"prodlenka_ud_zhaloby.docx",
    "raport_ud":   "raport_ud_zhaloby.docx",
}

ZHALOBA_LABELS = {
    "post":      "Постановление об отказе в жалобе",
    "otvet":     "Ответ заявителю",
    "prodlenka": "Продлёнка (уведомление о продлении)",
    "raport":    "Рапорт о продлении",
}

# ─── Настройки рапорта (сотрудник-исполнитель) ───────────────────────────────
RAPORT_FILE = os.path.join(APP_DIR, "otmena_raport_staff.json")
_DEFAULT_RAPORT_STAFF = {
    "post_line1": "Помощник прокурора",
    "post_line2": "Карасунского административного округа",
    "fio":        "Д.П. Лихачев",
}

def load_raport_staff():
    try:
        if os.path.exists(RAPORT_FILE):
            with open(RAPORT_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and "fio" in d:
                return d
    except Exception: pass
    return copy.deepcopy(_DEFAULT_RAPORT_STAFF)

def save_raport_staff(d):
    with open(RAPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

RAPORT_STAFF = load_raport_staff()

# ─── Шаблоны текстов «сути жалобы» ──────────────────────────────────────────
SUIT_TMPLS_FILE = os.path.join(APP_DIR, "otmena_suit_tmpls.json")
_DEFAULT_SUIT_TMPLS = [
    "о повреждении автомобиля",
    "о краже имущества",
    "о мошеннических действиях",
    "о причинении телесных повреждений",
    "о бездействии органа дознания",
]

def load_suit_tmpls():
    try:
        if os.path.exists(SUIT_TMPLS_FILE):
            with open(SUIT_TMPLS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, list): return d
    except Exception: pass
    return list(_DEFAULT_SUIT_TMPLS)

def save_suit_tmpls(lst):
    with open(SUIT_TMPLS_FILE, "w", encoding="utf-8") as f:
        json.dump(lst, f, ensure_ascii=False, indent=2)

SUIT_TMPLS = load_suit_tmpls()

# Шаблоны оснований отказа (фраза после «в связи с отсутствием»)
OSNOV_FILE = os.path.join(APP_DIR, "otmena_osnov_tmpls.json")
_DEFAULT_OSNOV = [
    "события преступления",
    "состава преступления",
    "в действиях лица состава преступления",
    "события и состава преступления",
]

def load_osnov_tmpls():
    try:
        if os.path.exists(OSNOV_FILE):
            with open(OSNOV_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, list) and d: return d
    except Exception: pass
    return list(_DEFAULT_OSNOV)

def save_osnov_tmpls(lst):
    with open(OSNOV_FILE, "w", encoding="utf-8") as f:
        json.dump(lst, f, ensure_ascii=False, indent=2)

OSNOV_TMPLS = load_osnov_tmpls()


# ─────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАТОРЫ ДОКУМЕНТОВ ЖАЛОБ
# ─────────────────────────────────────────────────────────────────────────────

def _zhaloba_tmpl(key):
    p = os.path.join(TMPL_DIR, ZHALOBA_TMPLS[key])
    if not os.path.exists(p):
        raise FileNotFoundError(f"Шаблон не найден: {p}")
    return p


def gen_post_zhaloba(dept_key, doc_date, kusp_num, kusp_date,
                     otk_date, zayavitel, suit_text, osnov,
                     pojt_date, signer_key, out_path):
    """Постановление об отказе в удовлетворении жалобы."""
    import re as _re
    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    dept = DEPT[dept_key]
    ns   = dept["name_short"]
    pd   = sig["post_doc"]; fi = sig["fio_short"]; ps = sig["post_sign"]
    ds   = date_long(doc_date)
    ks   = date_short(kusp_date)
    os_  = date_short(otk_date)
    pj   = date_short(pojt_date)   # дата поступления жалобы в прокуратуру

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("post")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)
        body  = root.find(f"{W_TAG}body")
        paras = list(body.findall(f"{W_TAG}p"))

        # P3: дата
        p3 = _all_text(paras[3])
        m = _re.search(r'\d+\s+\w+\s+\d{4}\s+года', p3)
        if m: _replace_text(paras[3], p3[:m.start()] + ds)

        # P5: подписант + КУСП
        _replace_text(paras[5],
            f"{pd} {fi}, рассмотрев в порядке ст. 124 УПК РФ "
            f"жалобу {zayavitel} о несогласии с постановлением об отказе "
            f"в возбуждении уголовного дела по материалу КУСП № {kusp_num} от {ks},")

        # P9: дата поступления жалобы
        _replace_text(paras[9],
            f"{pj} в прокуратуру Карасунского административного округа "
            f"г. Краснодара поступила жалоба {zayavitel} о несогласии с "
            f"постановлением об отказе в возбуждении уголовного дела по "
            f"материалу КУСП № {kusp_num} от {ks}.")

        # P10: суть + КУСП
        _replace_text(paras[10],
            f"В ходе рассмотрения жалобы установлено, что {ks} в {ns} "
            f"УМВД России по г. Краснодару зарегистрировано заявление "
            f"{zayavitel} {suit_text} (КУСП № {kusp_num} от {ks}).")

        # P11: дата отказа
        _replace_text(paras[11],
            f"{os_} по результатам проверки, в том числе дополнительной, "
            f"указанного сообщения о преступлении должностным лицом {ns} "
            f"УМВД России по г. Краснодару вынесено постановление об отказе "
            f"в возбуждении уголовного дела в связи с отсутствием {osnov}.")

        # P12: отменено
        _replace_text(paras[12],
            f"Изучение указанного постановления об отказе в возбуждении "
            f"уголовного дела в прокуратуре округа показало, что последнее "
            f"является незаконным, необоснованным и немотивированным, в связи "
            f"с чем отменено в порядке надзора, материал КУСП № {kusp_num} от {ks} "
            f"направлен для организации дополнительной проверки, о результатах "
            f"которой заинтересованные лица будут уведомлены в установленном "
            f"законом порядке.")

        # P18: ПОСТАНОВИЛ — отказать
        i18, p18 = _find_para_body(body, "В удовлетворении жалобы")
        if p18 is not None:
            _replace_text(p18,
                f"В удовлетворении жалобы {zayavitel} о несогласии с "
                f"постановлением об отказе в возбуждении уголовного дела "
                f"по материалу КУСП № {kusp_num} от {ks} – отказать.")

        # Подпись
        p_sign = _find_para(root, "Заместитель прокурора округа")
        if p_sign is None: p_sign = _find_para(root, "Прокурор округа")
        if p_sign is not None:
            orig  = _all_text(p_sign)
            marker = next((m for m in ["Заместитель прокурора округа",
                                        "Прокурор округа",
                                        "И.о. заместителя прокурора округа"]
                           if m in orig), None)
            if marker:
                after = orig[orig.index(marker)+len(marker):]
                sc = len(after)-len(after.lstrip())
                _replace_text(p_sign, ps + after[:sc] + fi, apply_nbsp=False)

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gen_otvet_zhaloba(doc_date, kusp_num, kusp_date,
                      vo_num, vo_date, zayavitel, kontakt,
                      signer_key, out_path):
    """Ответ заявителю об отказе в удовлетворении жалобы."""
    import re as _re
    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    fi   = sig["fio_short"]; ps = sig["post_sign"]
    ks   = date_short(kusp_date)
    vd   = date_short(vo_date)
    ds   = date_short(doc_date)   # дата вынесения постановления

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("otvet")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)

        # Адресат: ФИО (P15) и контакт/адрес (P17)
        zayav_lines = zayavitel.strip().split()
        # Дательный падеж не автоматизируем — подставляем как есть
        p15 = _find_para(root, "Соболеву А.А.")
        if p15 is not None: _replace_text(p15, zayavitel)

        p17 = _find_para(root, "пр. Монтажный")
        if p17 is not None: _replace_text(p17, kontakt)

        # P19: основной текст
        p19 = _find_para(root, "Прокуратурой округа рассмотрена")
        if p19 is not None:
            _replace_text(p19,
                f"Прокуратурой округа рассмотрена Ваша жалоба "
                f"({vo_num} от {vd}) на постановление об отказе в возбуждении "
                f"уголовного дела по материалу проверки КУСП № {kusp_num} от {ks}.")

        # P20: результат
        p20 = _find_para(root, "По результатам рассмотрения")
        if p20 is not None:
            _replace_text(p20,
                f"По результатам рассмотрения {ds} вынесено постановление "
                f"об отказе в удовлетворении жалобы.")

        # Подпись
        for marker in ["Заместитель прокурора округа", "Прокурор округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig  = _all_text(p_sign)
                after = orig[orig.index(marker)+len(marker):]
                sc    = len(after)-len(after.lstrip())
                _replace_text(p_sign, ps + after[:sc] + fi, apply_nbsp=False)
                break

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)



# ─────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАТОРЫ — УДОВЛЕТВОРЕНИЕ ЖАЛОБЫ
# ─────────────────────────────────────────────────────────────────────────────

def gen_post_ud(dept_key, doc_date, kusp_num, kusp_date,
                otk_date, zayavitel, suit_text, osnov,
                pojt_date, signer_key, out_path):
    """Постановление об удовлетворении жалобы."""
    import re as _re
    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    dept = DEPT[dept_key]
    ns   = dept["name_short"]
    pd   = sig["post_doc"]; fi = sig["fio_short"]; ps = sig["post_sign"]
    ds   = date_long(doc_date)
    ks   = date_short(kusp_date)
    os_  = date_short(otk_date)
    pj   = date_short(pojt_date)

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("post_ud")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)
        body  = root.find(f"{W_TAG}body")
        paras = list(body.findall(f"{W_TAG}p"))

        # P3: дата
        p3_txt = _all_text(paras[3])
        m = _re.search(r'\d+\s+\w+\s+\d{4}\s+года', p3_txt)
        if m: _replace_text(paras[3], p3_txt[:m.start()] + ds)

        # P4: подписант + жалоба
        _replace_text(paras[4],
            f"{pd} {fi}, рассмотрев в порядке ст. 124 УПК РФ "
            f"жалобу {zayavitel} на постановление об отказе в возбуждении "
            f"уголовного дела от {os_} по материалу проверки "
            f"КУСП № {kusp_num} от {ks},")

        # P8: дата поступления жалобы
        _replace_text(paras[8],
            f"В прокуратуру Карасунского административного округа "
            f"г. Краснодара {pj} поступила жалоба {zayavitel} "
            f"на постановление об отказе в возбуждении уголовного дела "
            f"от {os_} по материалу проверки КУСП № {kusp_num} от {ks}.")

        # P9: суть + КУСП
        _replace_text(paras[9],
            f"В ходе рассмотрения жалобы установлено, что {ks} в {ns} "
            f"УМВД России по г. Краснодару зарегистрировано заявление "
            f"{zayavitel} {suit_text} (КУСП № {kusp_num} от {ks}).")

        # P10: дата отказа
        _replace_text(paras[10],
            f"{os_} по результатам проверки, в том числе дополнительной, "
            f"указанного сообщения о преступлении должностным лицом {ns} "
            f"УМВД России по г. Краснодару вынесено постановление об отказе "
            f"в возбуждении уголовного дела в связи с отсутствием {osnov}.")

        # P11, P12, P13, P14 — «Кроме того» блоки убираем (оставляем пустыми если один КУСП)
        for pi in [11, 12, 13, 14]:
            if pi < len(paras):
                _replace_text(paras[pi], "")

        # P15: «подлежит отмене, жалоба удовлетворению»
        i15, p15 = _find_para_body(body, "подлежит отмене")
        if p15 is not None:
            _replace_text(p15,
                f"Изучение доводов, изложенных в жалобе {zayavitel}, "
                f"а также указанного постановления об отказе в возбуждении "
                f"уголовного дела показало, что последнее подлежит отмене, "
                f"а жалоба удовлетворению, так как проверочные мероприятия, "
                f"необходимые для принятия законного, обоснованного и "
                f"мотивированного решения проведены не были.")

        # ПОСТАНОВИЛ — «удовлетворить»
        i_ud, p_ud = _find_para_body(body, "удовлетворить")
        if p_ud is not None:
            _replace_text(p_ud,
                f"Жалобу {zayavitel} на постановление об отказе в возбуждении "
                f"уголовного дела от {os_} по материалу проверки "
                f"КУСП № {kusp_num} от {ks} — удовлетворить.")

        # ПОСТАНОВИЛ — «отменить»
        i_ot, p_ot = _find_para_body(body, "отменить")
        if p_ot is not None:
            _replace_text(p_ot,
                f"Постановление об отказе в возбуждении уголовного дела "
                f"от {os_} по материалу проверки "
                f"КУСП № {kusp_num} от {ks} — отменить.")

        # Подпись
        for marker in ["Заместитель прокурора округа", "Прокурор округа",
                       "И.о. заместителя прокурора округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig  = _all_text(p_sign)
                after = orig[orig.index(marker)+len(marker):]
                sc    = len(after)-len(after.lstrip())
                _replace_text(p_sign, ps + after[:sc] + fi, apply_nbsp=False)
                break

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gen_otvet_ud(doc_date, kusp_num, kusp_date,
                 vo_num, vo_date, otk_date, zayavitel, kontakt,
                 signer_key, out_path):
    """Ответ заявителю об удовлетворении жалобы."""
    import re as _re
    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    fi   = sig["fio_short"]; ps = sig["post_sign"]
    ks   = date_short(kusp_date)
    vd   = date_short(vo_date)
    os_  = date_short(otk_date)
    ds   = date_short(doc_date)

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("otvet_ud")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)

        # Адресат ФИО (P16)
        p_fio = _find_para(root, "Зинову В.А.")
        if p_fio is not None: _replace_text(p_fio, zayavitel)

        # Контакт (P18)
        p_cont = _find_para(root, "VZinov@vtb-leasing.com")
        if p_cont is not None: _replace_text(p_cont, kontakt)

        # Основной текст
        p_main = _find_para(root, "Прокуратурой округа рассмотрена")
        if p_main is not None:
            _replace_text(p_main,
                f"Прокуратурой округа рассмотрена Ваша жалоба "
                f"({vo_num} от {vd}) на постановление об отказе в возбуждении "
                f"уголовного дела от {os_} по материалу проверки "
                f"КУСП № {kusp_num} от {ks}.")

        # Результат
        p_res = _find_para(root, "По результатам рассмотрения")
        if p_res is not None:
            _replace_text(p_res,
                f"По результатам рассмотрения {ds} вынесено постановление "
                f"об удовлетворении жалобы по основаниям, изложенным "
                f"в постановлении об удовлетворении жалобы.")

        # Подпись
        for marker in ["Заместитель прокурора округа", "Прокурор округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig  = _all_text(p_sign)
                after = orig[orig.index(marker)+len(marker):]
                sc    = len(after)-len(after.lstrip())
                _replace_text(p_sign, ps + after[:sc] + fi, apply_nbsp=False)
                break

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gen_prodlenka_ud(vo_num, vo_date, zayavitel, kontakt,
                     pojt_date, signer_key, out_path):
    """Продлёнка (удовлетворение) — дата поступления в тексте."""
    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    fi   = sig["fio_short"]; ps = sig["post_sign"]
    vd   = date_short(vo_date)
    pj   = date_short(pojt_date)

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("prodlenka_ud")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)

        # Адресат ФИО
        p_fio = _find_para(root, "Шамаеву В.Е.")
        if p_fio is not None: _replace_text(p_fio, zayavitel)

        # Контакт
        p_cont = _find_para(root, "Veshin3371@rambler.ru")
        if p_cont is not None: _replace_text(p_cont, kontakt)

        # Основной текст — включает дату поступления и № жалобы
        p_main = _find_para(root, "Сообщаю, что срок рассмотрения")
        if p_main is not None:
            _replace_text(p_main,
                f"Сообщаю, что срок рассмотрения Вашей жалобы в порядке "
                f"ст. 124 УПК РФ, поступившей {pj} ({vo_num}) "
                f"в прокуратуру округа продлен до 10 суток.")

        # Подпись
        for marker in ["Заместитель прокурора округа", "Прокурор округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig  = _all_text(p_sign)
                after = orig[orig.index(marker)+len(marker):]
                sc    = len(after)-len(after.lstrip())
                _replace_text(p_sign, ps + after[:sc] + fi, apply_nbsp=False)
                break

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gen_raport_ud(dept_key, vo_num, vo_date, zayavitel,
                  suit_text, prodl_date, signer_key, raport_date, out_path):
    """Рапорт о продлении (удовлетворение) — индексы параграфов отличаются."""
    global RAPORT_STAFF
    sig   = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    fi_s  = sig["fio_short"]
    pd_s  = sig["post_doc"]
    rank  = sig.get("rank", "советник юстиции")
    dept  = DEPT[dept_key]
    ns    = dept["name_short"]
    vd    = date_short(vo_date)
    prd   = date_short(prodl_date)
    rdate = date_short(raport_date)

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("raport_ud")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)
        body  = root.find(f"{W_TAG}body")
        paras = list(body.findall(f"{W_TAG}p"))

        # P1: должность подписанта
        _replace_text(paras[1], pd_s.split("\n")[0].strip())

        # P3: звание
        _replace_text(paras[3], rank)

        # P5: ФИО — сохраняем пробелы
        orig5 = _all_text(paras[5])
        spaces = len(orig5) - len(orig5.lstrip())
        _replace_text(paras[5], " " * spaces + fi_s)

        # P7: дата «согласования»
        _replace_text(paras[7], f"{rdate} г.")

        # P12: основной текст рапорта
        _replace_text(paras[12],
            f"Мне на рассмотрение поступила жалоба {zayavitel}, "
            f"зарегистрированная в прокуратуре округа от {vd} {suit_text}.")

        # P13: просьба о продлении
        _replace_text(paras[13],
            f"В рамках проверки из {ns} УМВД России по г. Краснодару "
            f"запрошены материалы, в связи чем, прошу продлить срок "
            f"рассмотрения жалобы до 10 суток, а именно до {prd}.")

        # Исполнитель
        rs = RAPORT_STAFF
        p_r1 = _find_para(root, "Помощник прокурора")
        if p_r1 is not None: _replace_text(p_r1, rs.get("post_line1", "Помощник прокурора"))

        # ФИО исполнителя
        p_fio_r = _find_para(root, "Лихачев")
        if p_fio_r is not None:
            orig = _all_text(p_fio_r)
            if "г. Краснодара" in orig:
                after = orig[orig.index("г. Краснодара")+len("г. Краснодара"):]
                sc    = len(after)-len(after.lstrip())
                _replace_text(p_fio_r, "г. Краснодара" + after[:sc] + rs.get("fio","Д.П. Лихачев"))

        # Дата внизу
        p_date = _find_para(root, "29 декабря 2025")
        if p_date is None:
            for p in paras[-5:]:
                t = _normalize(_all_text(p)).strip()
                if t.endswith("г.") and any(c.isdigit() for c in t) and "Иванов" not in t:
                    _replace_text(p, f"{rdate} г."); break
        else:
            _replace_text(p_date, f"{rdate} г.")

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gen_prodlenka(vo_num, vo_date, zayavitel, kontakt,
                  signer_key, out_path):
    """Уведомление о продлении срока рассмотрения жалобы."""
    sig  = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    fi   = sig["fio_short"]; ps = sig["post_sign"]
    vd   = date_short(vo_date)

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("prodlenka")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)

        # Адресат ФИО
        p_fio = _find_para(root, "Ивахнову С.Н.")
        if p_fio is not None: _replace_text(p_fio, zayavitel)

        # Контакт (email или адрес)
        p_cont = _find_para(root, "alla.ivahnowa@yandex.ru")
        if p_cont is not None: _replace_text(p_cont, kontakt)

        # Основной текст
        p_main = _find_para(root, "Сообщаю, что срок рассмотрения")
        if p_main is not None:
            _replace_text(p_main,
                f"Сообщаю, что срок рассмотрения Вашей жалобы "
                f"({vo_num} от {vd}) в порядке ст. 124 УПК РФ, "
                f"поступившей в прокуратуру округа продлен до 10 суток.")

        # Подпись
        for marker in ["Заместитель прокурора округа", "Прокурор округа"]:
            p_sign = _find_para(root, marker)
            if p_sign is not None:
                orig  = _all_text(p_sign)
                after = orig[orig.index(marker)+len(marker):]
                sc    = len(after)-len(after.lstrip())
                _replace_text(p_sign, ps + after[:sc] + fi, apply_nbsp=False)
                break

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def gen_raport(dept_key, vo_num, vo_date, zayavitel,
               suit_text, prodl_date, signer_key, raport_date, out_path):
    """Рапорт о продлении срока рассмотрения жалобы."""
    global RAPORT_STAFF
    sig   = SIGNERS.get(signer_key, list(SIGNERS.values())[0])
    fi_s  = sig["fio_short"]
    pd_s  = sig["post_doc"]
    rank  = sig.get("rank", "советник юстиции")
    dept  = DEPT[dept_key]
    ns    = dept["name_short"]
    vd    = date_short(vo_date)
    prd   = date_short(prodl_date)
    rdate = date_short(raport_date)

    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(_zhaloba_tmpl("raport")) as z: z.extractall(tmp)
        xp = os.path.join(tmp, "word", "document.xml")
        _, root = _xml_parse(xp)
        body  = root.find(f"{W_TAG}body")
        paras = list(body.findall(f"{W_TAG}p"))

        # P1: должность подписанта (шапка «согласен»)
        _replace_text(paras[1], pd_s.split("\n")[0].strip())

        # P3: звание
        _replace_text(paras[3], rank)

        # P5: ФИО подписанта
        orig5 = _all_text(paras[5])
        spaces = len(orig5) - len(orig5.lstrip())
        _replace_text(paras[5], " " * spaces + fi_s)

        # P8: дата рапорта
        _replace_text(paras[8], f"{rdate} г.")

        # P13: основной текст рапорта
        _replace_text(paras[13],
            f"Мне на рассмотрение поступила жалоба {zayavitel}, "
            f"зарегистрированная в прокуратуре округа от {vd} {suit_text}.")

        # P14: просьба о продлении
        _replace_text(paras[14],
            f"В рамках проверки из {ns} УМВД России по г. Краснодару "
            f"запрошены материалы, в связи чем, прошу продлить срок "
            f"рассмотрения жалобы до 10 суток, а именно до {prd}.")

        # P17/P18/P19: исполнитель рапорта
        rs = RAPORT_STAFF
        p17 = _find_para(root, "Помощник прокурора")
        if p17 is not None: _replace_text(p17, rs.get("post_line1", "Помощник прокурора"))

        p18 = _find_para(root, "Карасунского административного округа")
        # Находим нужный параграф (не путаем с шапкой)
        for p in root.iter(f"{W_TAG}p"):
            t = _all_text(p)
            if "Карасунского административного округа" in t and "Лихачев" not in t and "Иванов" not in t:
                if "прокуратур" not in t:
                    _replace_text(p, rs.get("post_line2", "Карасунского административного округа"))
                    break

        p_fio_r = _find_para(root, "Лихачев")
        if p_fio_r is not None:
            orig = _all_text(p_fio_r)
            # Сохраняем пробелы
            spaces = len(orig) - len(orig.rstrip()) if not orig.endswith(rs.get("fio","")) else 0
            left_spaces = len(orig) - len(orig.lstrip())
            # Берём паттерн пробелов из оригинала
            after_city = orig[orig.find("г. Краснодара") + len("г. Краснодара"):] if "г. Краснодара" in orig else orig
            sc = len(after_city) - len(after_city.lstrip())
            new_line = "г. Краснодара" + after_city[:sc] + rs.get("fio", "Д.П. Лихачев")
            _replace_text(p_fio_r, new_line)

        # Дата рапорта (нижняя)
        p_date = _find_para(root, "23 мая 2025")
        if p_date is None:
            # Ищем строку с "г." в конце
            for p in root.iter(f"{W_TAG}p"):
                t = _all_text(p).strip()
                if t.endswith(" г.") and any(c.isdigit() for c in t):
                    if "Иванов" not in t and "Лихачев" not in t:
                        _replace_text(p, f"{rdate} г.")
                        break
        else:
            _replace_text(p_date, f"{rdate} г.")

        _xml_write(xp, None, root); _repack(tmp, out_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# ОКНО ЖАЛОБ
# ─────────────────────────────────────────────────────────────────────────────
class ZhalobaWindow(tk.Toplevel):
    """Отдельное окно для генерации документов по жалобам на отказ в ВУД."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Жалобы на отказ в ВУД")
        self.geometry("960x860")
        self.minsize(860, 700)
        self.configure(bg="#0b3d2e")
        self.transient(master)

        # Шапка
        tk.Label(self, text="Документы по жалобам на отказ в ВУД",
                 bg="#0b3d2e", fg="#f5d77a",
                 font=("Times New Roman", 16, "bold")).pack(pady=(12, 2))
        tk.Label(self, bg="#0b3d2e", fg="#cfcfcf", font=("Segoe UI", 9),
                 text="Выберите документы для создания, заполните поля, нажмите «Создать»"
                 ).pack()
        tk.Label(self, bg="#0b3d2e", fg="#8B6914", font=("Segoe UI", 7),
                 text="✦ ──────────────────────────────────────────────────────── ✦"
                 ).pack()

        self._build_bottom()
        self._build_scroll()

    # ── Нижние кнопки ────────────────────────────────────────────────────
    def _build_bottom(self):
        bf = tk.Frame(self, bg="#0b3d2e"); bf.pack(side="bottom", fill="x", pady=6)
        tk.Button(bf, text="📝 Создать выбранные документы",
                  command=self._generate, bg="#f5d77a", fg="#0b3d2e",
                  font=("Segoe UI", 11, "bold"), padx=14, pady=5, cursor="hand2"
                  ).pack(side="left", padx=10)
        tk.Button(bf, text="✍ Редактор рапорта",
                  command=self._edit_raport_staff, bg="#d4af37", fg="#0b3d2e",
                  font=("Segoe UI", 10), padx=10, pady=5, cursor="hand2"
                  ).pack(side="left", padx=4)
        tk.Button(bf, text="📋 Шаблоны сути",
                  command=self._edit_suit_tmpls, bg="#d4af37", fg="#0b3d2e",
                  font=("Segoe UI", 10), padx=10, pady=5, cursor="hand2"
                  ).pack(side="left", padx=4)
        tk.Button(bf, text="⚖ Основания",
                  command=self._edit_osnov_tmpls, bg="#d4af37", fg="#0b3d2e",
                  font=("Segoe UI", 10), padx=10, pady=5, cursor="hand2"
                  ).pack(side="left", padx=4)
        tk.Button(bf, text="📂 Папка вывода",
                  command=self._open_out, font=("Segoe UI", 10),
                  padx=10, pady=5, cursor="hand2"
                  ).pack(side="left", padx=4)
        tk.Button(bf, text="Закрыть", command=self.destroy,
                  font=("Segoe UI", 10), padx=10, pady=5
                  ).pack(side="right", padx=10)

    # ── Прокрутка ────────────────────────────────────────────────────────
    def _build_scroll(self):
        outer = tk.Frame(self, bg="#0b3d2e"); outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg="#0b3d2e", highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); cv.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(cv, bg="#0b3d2e")
        win = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",   lambda e: cv.itemconfigure(win, width=e.width))
        cv.bind_all("<MouseWheel>", lambda e: cv.yview_scroll(-1*int(e.delta/120), "units"))
        self._build_form(inner)

    # ── Форма ─────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        BG = "#f4f1e8"
        frm = tk.Frame(parent, bg=BG, bd=2, relief="ridge")
        frm.pack(padx=16, pady=12, fill="both", expand=True)
        frm.columnconfigure(1, weight=1)
        R = 0

        def lbl(txt, r):
            tk.Label(frm, text=txt, bg=BG, font=("Segoe UI", 10, "bold"),
                     anchor="w").grid(row=r, column=0, sticky="nw", padx=8, pady=5)

        def sep():
            nonlocal R
            ttk.Separator(frm, orient="horizontal").grid(
                row=R, column=0, columnspan=2, sticky="ew", padx=8, pady=3)
            R += 1

        # ── БЛОК 1: Галочки документов ────────────────────────────────────
        tk.Label(frm, text="Выберите документы для создания:",
                 bg=BG, font=("Segoe UI", 10, "bold")
                 ).grid(row=R, column=0, columnspan=2, sticky="w", padx=8, pady=(8,2))
        R += 1

        self._chk_vars = {}
        chk_frame = tk.Frame(frm, bg=BG)
        chk_frame.grid(row=R, column=0, columnspan=2, sticky="w", padx=16, pady=4)
        for key, label in ZHALOBA_LABELS.items():
            var = tk.BooleanVar(value=True)
            self._chk_vars[key] = var
            tk.Checkbutton(chk_frame, text=label, variable=var,
                           bg=BG, font=("Segoe UI", 10), selectcolor=BG,
                           activebackground=BG
                           ).pack(anchor="w", pady=1)
        R += 1; sep()

        # ── Результат жалобы ──────────────────────────────────────────────
        tk.Label(frm, text="Результат рассмотрения жалобы:",
                 bg=BG, font=("Segoe UI", 10, "bold")
                 ).grid(row=R, column=0, columnspan=2, sticky="w", padx=8, pady=(6,2))
        R += 1
        self._result_var = tk.StringVar(value="otkaz")
        rf = tk.Frame(frm, bg=BG); rf.grid(row=R, column=0, columnspan=2, sticky="w", padx=16, pady=4)
        tk.Radiobutton(rf, text="❌  Отказ в удовлетворении жалобы",
                       variable=self._result_var, value="otkaz",
                       bg=BG, font=("Segoe UI", 10, "bold"),
                       fg="#8B0000", selectcolor=BG, activebackground=BG
                       ).pack(side="left", padx=10)
        tk.Radiobutton(rf, text="✅  Удовлетворение жалобы",
                       variable=self._result_var, value="ud",
                       bg=BG, font=("Segoe UI", 10, "bold"),
                       fg="#006400", selectcolor=BG, activebackground=BG
                       ).pack(side="left", padx=10)
        R += 1; sep()

        # ── БЛОК 2: Подразделение ─────────────────────────────────────────
        lbl("① Подразделение:", R)
        df = tk.Frame(frm, bg=BG); df.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        self._dept = tk.StringVar(value="КАО")
        for txt, val in [("КАО", "КАО"), ("ГМР", "ГМР")]:
            tk.Radiobutton(df, text=txt, variable=self._dept, value=val,
                           bg=BG, font=("Segoe UI", 10), selectcolor=BG,
                           activebackground=BG).pack(side="left", padx=10)
        R += 1

        # ── БЛОК 3: Общие данные ──────────────────────────────────────────
        lbl("② КУСП (материал):", R)
        kf = tk.Frame(frm, bg=BG); kf.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        tk.Label(kf, text="КУСП №", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._kusp_num = tk.Entry(kf, width=12, font=("Segoe UI", 10))
        self._kusp_num.pack(side="left", padx=4)
        tk.Label(kf, text="от", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._date_kusp = DateEntry(kf, bg=BG)
        self._date_kusp.pack(side="left", padx=4)
        R += 1

        lbl("③ Дата отказа в ВУД:", R)
        self._date_otk = DateEntry(frm, bg=BG, initial_today=False)
        self._date_otk.grid(row=R, column=1, sticky="w", padx=6, pady=5); R += 1

        lbl("④ Заявитель (Фамилия И.О.):", R)
        tk.Label(frm, text="Введите в именительном падеже — программа склонит автоматически",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        zf = tk.Frame(frm, bg=BG); zf.grid(row=R, column=1, sticky="ew", padx=6, pady=(0,2))
        self._zayavitel = tk.Entry(zf, width=26, font=("Segoe UI", 10))
        self._zayavitel.pack(side="left")
        # Поля ручного исправления склонений
        decline_frm = tk.LabelFrame(frm, text="Склонения (авто, при необходимости — поправьте)",
                                    bg=BG, fg="#444", font=("Segoe UI", 8))
        decline_frm.grid(row=R+1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0,4))
        self._zayav_dat = tk.StringVar()  # дательный — кому (для ответа/продлёнки)
        self._zayav_rod = tk.StringVar()  # родительный — кого (для «жалобу X»)
        def _update_declines(*_):
            fio = self._zayavitel.get().strip()
            self._zayav_dat.set(decline_fio(fio, "dat") if fio else "")
            self._zayav_rod.set(decline_fio(fio, "gen") if fio else "")
        self._zayavitel.bind("<KeyRelease>", _update_declines)
        # Дательный
        df1 = tk.Frame(decline_frm, bg=BG); df1.pack(fill="x", padx=6, pady=2)
        tk.Label(df1, text="Кому (Дат.):", bg=BG, font=("Segoe UI", 8), width=14,
                 anchor="e").pack(side="left")
        tk.Entry(df1, textvariable=self._zayav_dat, width=28,
                 font=("Segoe UI", 10), bg="#fffff0").pack(side="left", padx=4)
        tk.Label(df1, text="← используется в шапке ответа/продлёнки",
                 bg=BG, fg="#888", font=("Segoe UI", 7)).pack(side="left")
        # Родительный
        df2 = tk.Frame(decline_frm, bg=BG); df2.pack(fill="x", padx=6, pady=2)
        tk.Label(df2, text="Кого (Род.):", bg=BG, font=("Segoe UI", 8), width=14,
                 anchor="e").pack(side="left")
        tk.Entry(df2, textvariable=self._zayav_rod, width=28,
                 font=("Segoe UI", 10), bg="#fffff0").pack(side="left", padx=4)
        tk.Label(df2, text="← используется в тексте «жалобу X»",
                 bg=BG, fg="#888", font=("Segoe UI", 7)).pack(side="left")
        R += 2

        lbl("⑤ Контакт заявителя:", R)
        tk.Label(frm, text="(адрес или email — подставляется в шапку ответа/продлёнки)",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        self._kontakt = tk.Entry(frm, width=52, font=("Segoe UI", 10))
        self._kontakt.grid(row=R, column=1, sticky="w", padx=6, pady=(0,5)); R += 1

        lbl("⑥ Суть жалобы:", R)
        tk.Label(frm, text="(свободный текст — напр. «о повреждении автомобиля»)",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        sf = tk.Frame(frm, bg=BG); sf.grid(row=R, column=1, sticky="ew", padx=6, pady=(0,5))
        sf.columnconfigure(0, weight=1)
        self._suit = tk.Entry(sf, width=52, font=("Segoe UI", 10))
        self._suit.pack(side="left", fill="x", expand=True)
        tk.Button(sf, text="▼ шаблоны", font=("Segoe UI", 8),
                  bg="#e8e0cc", padx=4, pady=1,
                  command=self._pick_suit).pack(side="left", padx=(4,0))
        R += 1

        lbl("⑥б Основание отказа:", R)
        tk.Label(frm, text="(после «в связи с отсутствием» — нужно для постановления)",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        of = tk.Frame(frm, bg=BG); of.grid(row=R, column=1, sticky="ew", padx=6, pady=(0,5))
        of.columnconfigure(0, weight=1)
        self._osnov = tk.Entry(of, width=52, font=("Segoe UI", 10))
        self._osnov.insert(0, OSNOV_TMPLS[0] if OSNOV_TMPLS else "события преступления")
        self._osnov.pack(side="left", fill="x", expand=True)
        tk.Button(of, text="▼ шаблоны", font=("Segoe UI", 8),
                  bg="#e8e0cc", padx=4, pady=1,
                  command=self._pick_osnov).pack(side="left", padx=(4,0))
        tk.Button(of, text="✎ ред.", font=("Segoe UI", 8),
                  bg="#d4af37", padx=4, pady=1,
                  command=self._edit_osnov_tmpls).pack(side="left", padx=(2,0))
        R += 1

        sep()

        # ── БЛОК 4: Номер жалобы (ВО-...) ────────────────────────────────
        lbl("⑦ Входящий № жалобы:", R)
        vf = tk.Frame(frm, bg=BG); vf.grid(row=R, column=1, sticky="w", padx=6, pady=5)
        self._vo_prefix = tk.Entry(vf, width=4, font=("Segoe UI", 10))
        self._vo_prefix.insert(0, "ВО-"); self._vo_prefix.pack(side="left")
        self._vo_num = tk.Entry(vf, width=10, font=("Segoe UI", 10))
        self._vo_num.pack(side="left", padx=2)
        tk.Label(vf, text="-", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._vo_year = tk.Entry(vf, width=4, font=("Segoe UI", 10))
        self._vo_year.insert(0, str(datetime.date.today().year)[-2:])
        self._vo_year.pack(side="left")
        tk.Label(vf, text="от", bg=BG, font=("Segoe UI", 10)).pack(side="left", padx=(6,0))
        self._date_vo = DateEntry(vf, bg=BG, initial_today=False)
        self._date_vo.pack(side="left", padx=4)
        R += 1

        # ── БЛОК 5: Поля для постановления/ответа ────────────────────────
        lbl("⑧ Дата постановления:", R)
        tk.Label(frm, text="(дата документа — постановления об отказе в жалобе и ответа)",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        self._date_doc = DateEntry(frm, bg=BG)
        self._date_doc.grid(row=R, column=1, sticky="w", padx=6, pady=(0,5)); R += 1

        lbl("⑨ Дата поступления жалобы:", R)
        tk.Label(frm, text="(когда жалоба поступила в прокуратуру округа)",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        self._date_pojt = DateEntry(frm, bg=BG, initial_today=False)
        self._date_pojt.grid(row=R, column=1, sticky="w", padx=6, pady=(0,5)); R += 1

        sep()

        # ── БЛОК 6: Поля для продлёнки/рапорта ───────────────────────────
        lbl("⑩ Дата — до которой продлить:", R)
        tk.Label(frm, text="(нужно для рапорта — «до 10 суток, а именно до ДД.ММ.ГГГГ»)",
                 bg=BG, fg="#666", font=("Segoe UI", 8, "italic")
                 ).grid(row=R, column=1, sticky="w", padx=6)
        R += 1
        self._date_prodl = DateEntry(frm, bg=BG, initial_today=False)
        self._date_prodl.grid(row=R, column=1, sticky="w", padx=6, pady=(0,5)); R += 1

        lbl("⑪ Дата рапорта:", R)
        self._date_raport = DateEntry(frm, bg=BG)
        self._date_raport.grid(row=R, column=1, sticky="w", padx=6, pady=5); R += 1

        sep()

        # ── Подписант ─────────────────────────────────────────────────────
        lbl("⑫ Подписант:", R)
        self._signer_var = tk.StringVar(value=DEFAULT_SIGNER)
        self._cmb = ttk.Combobox(frm, textvariable=self._signer_var,
                                  values=list(SIGNERS.keys()),
                                  width=46, state="readonly")
        self._cmb.grid(row=R, column=1, sticky="w", padx=6, pady=5); R += 1

    # ── Выбор шаблона сути ───────────────────────────────────────────────
    def _pick_suit(self):
        global SUIT_TMPLS
        SUIT_TMPLS = load_suit_tmpls()
        if not SUIT_TMPLS:
            messagebox.showinfo("Шаблоны", "Список шаблонов пуст. Добавьте через «Шаблоны сути».", parent=self)
            return
        menu = tk.Menu(self, tearoff=0)
        for tmpl in SUIT_TMPLS:
            menu.add_command(label=tmpl,
                             command=lambda t=tmpl: (self._suit.delete(0,"end"),
                                                      self._suit.insert(0, t)))
        try:
            menu.tk_popup(self._suit.winfo_rootx(),
                          self._suit.winfo_rooty() + self._suit.winfo_height())
        finally:
            menu.grab_release()


    # ── Выбор шаблона основания отказа ───────────────────────────────
    def _pick_osnov(self):
        global OSNOV_TMPLS
        OSNOV_TMPLS = load_osnov_tmpls()
        if not OSNOV_TMPLS:
            messagebox.showinfo("Основания", "Список пуст.", parent=self)
            return
        menu = tk.Menu(self, tearoff=0)
        for tmpl in OSNOV_TMPLS:
            menu.add_command(
                label=f"...отсутствием {tmpl}",
                command=lambda t=tmpl: (self._osnov.delete(0,"end"),
                                         self._osnov.insert(0, t)))
        try:
            menu.tk_popup(self._osnov.winfo_rootx(),
                          self._osnov.winfo_rooty() + self._osnov.winfo_height())
        finally:
            menu.grab_release()

    # ── Редактор шаблонов оснований ──────────────────────────────────
    def _edit_osnov_tmpls(self):
        global OSNOV_TMPLS
        w = tk.Toplevel(self); w.title("Основания отказа")
        w.configure(bg="#f4f1e8"); w.geometry("540x350")
        w.transient(self); w.grab_set()
        tk.Label(w, text="Основания отказа в ВУД",
                 bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        tk.Label(w,
                 text="Фраза подставляется после «в связи с отсутствием»\n"
                      "Двойной клик — выбрать и вставить в форму",
                 bg="#f4f1e8", fg="#555",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=10, pady=(4,2))
        body = tk.Frame(w, bg="#f4f1e8"); body.pack(fill="both", expand=True, padx=10, pady=4)
        lb = tk.Listbox(body, font=("Segoe UI", 10), activestyle="dotbox")
        sb = tk.Scrollbar(body, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True); sb.pack(side="left", fill="y")

        def refresh(sel=None):
            lb.delete(0, "end")
            for t in OSNOV_TMPLS:
                lb.insert("end", f"отсутствием {t}")
            if sel is not None and 0 <= sel < len(OSNOV_TMPLS):
                lb.selection_set(sel); lb.see(sel)

        def cur_idx():
            s = lb.curselection(); return s[0] if s else None

        def edit_dlg(idx=None):
            ed = tk.Toplevel(w); ed.configure(bg="#f4f1e8")
            ed.title("Изменить" if idx is not None else "Добавить")
            ed.transient(w); ed.grab_set(); ed.geometry("420x120")
            tk.Label(ed, text="в связи с отсутствием:",
                     bg="#f4f1e8", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(10,2))
            ent = tk.Entry(ed, width=50, font=("Segoe UI", 10))
            ent.pack(padx=10, pady=4)
            if idx is not None: ent.insert(0, OSNOV_TMPLS[idx])
            def do_s():
                global OSNOV_TMPLS
                val = ent.get().strip()
                if not val: return
                if idx is not None: OSNOV_TMPLS[idx] = val
                else: OSNOV_TMPLS.append(val)
                save_osnov_tmpls(OSNOV_TMPLS); ed.destroy()
                refresh(idx if idx is not None else len(OSNOV_TMPLS)-1)
            bf2 = tk.Frame(ed, bg="#f4f1e8"); bf2.pack(fill="x", padx=10, pady=6)
            tk.Button(bf2, text="Сохранить", command=do_s, bg="#d4af37", fg="#0b3d2e",
                      padx=10, pady=3).pack(side="left", padx=4)
            tk.Button(bf2, text="Отмена", command=ed.destroy, padx=10, pady=3).pack(side="left")
            ent.focus_set()

        def do_use():
            i = cur_idx()
            if i is None: return
            self._osnov.delete(0,"end"); self._osnov.insert(0, OSNOV_TMPLS[i])
            w.destroy()

        def do_del():
            global OSNOV_TMPLS
            i = cur_idx()
            if i is None: return
            if len(OSNOV_TMPLS) <= 1:
                messagebox.showwarning("", "Нельзя удалить последний.", parent=w); return
            if not messagebox.askyesno("Удалить",
                    f"Удалить «{OSNOV_TMPLS[i]}»?", parent=w): return
            OSNOV_TMPLS.pop(i); save_osnov_tmpls(OSNOV_TMPLS); refresh()

        lb.bind("<Double-Button-1>", lambda e: do_use())
        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=10, pady=(4,10))
        tk.Button(bf, text="✅ Использовать", command=do_use,
                  bg="#f5d77a", fg="#0b3d2e",
                  font=("Segoe UI", 10, "bold"), padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="➕ Добавить", command=lambda: edit_dlg(None), padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="✎ Изменить", command=lambda: edit_dlg(cur_idx()), padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="🗑 Удалить",  command=do_del, padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="Закрыть",    command=w.destroy, padx=8, pady=4).pack(side="right", padx=3)
        refresh()

    # ── Сбор и валидация данных ───────────────────────────────────────────
    def _get_vo_full(self):
        prefix = self._vo_prefix.get().strip()
        num    = self._vo_num.get().strip()
        year   = self._vo_year.get().strip()
        if not num: return ""
        return f"{prefix}{num}-{year}"

    def _collect(self):
        selected = [k for k, v in self._chk_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Жалобы", "Выберите хотя бы один документ.", parent=self)
            return None

        # Обязательные для всех
        required_all = {
            "kusp_num":   (self._kusp_num.get().strip(),   "② Номер КУСП"),
            "kusp_date":  (self._date_kusp.get_date(),      "② Дата КУСП"),
            "zayavitel":  (self._zayavitel.get().strip(),   "④ Заявитель"),
        }

        # Поля нужные только для конкретных документов
        required_by_doc = {
            "post":      [("otk_date",  self._date_otk.get_date(),    "③ Дата отказа в ВУД"),
                          ("suit_text", self._suit.get().strip(),      "⑥ Суть жалобы"),
                          ("pojt_date", self._date_pojt.get_date(),   "⑨ Дата поступления жалобы"),
                          ("doc_date",  self._date_doc.get_date(),    "⑧ Дата постановления")],
            "otvet":     [("vo_full",   self._get_vo_full(),          "⑦ Входящий № жалобы"),
                          ("vo_date",   self._date_vo.get_date(),     "⑦ Дата жалобы (ВО)"),
                          ("kontakt",   self._kontakt.get().strip(),  "⑤ Контакт заявителя"),
                          ("doc_date",  self._date_doc.get_date(),    "⑧ Дата постановления"),
                          ("otk_date",  self._date_otk.get_date(),   "③ Дата отказа в ВУД")],
            "prodlenka": [("vo_full",   self._get_vo_full(),          "⑦ Входящий № жалобы"),
                          ("vo_date",   self._date_vo.get_date(),     "⑦ Дата жалобы (ВО)"),
                          ("kontakt",   self._kontakt.get().strip(),  "⑤ Контакт заявителя")],
            "raport":    [("suit_text", self._suit.get().strip(),     "⑥ Суть жалобы"),
                          ("vo_date",   self._date_vo.get_date(),     "⑦ Дата жалобы (ВО)"),
                          ("prodl_date",self._date_prodl.get_date(),  "⑩ Дата — до которой продлить")],
        }

        # Проверяем обязательные для всех
        errors = []
        for fld, (val, label) in required_all.items():
            if not val:
                errors.append(label)

        # Проверяем поля нужные для выбранных документов
        for doc_key in selected:
            for fld, val, label in required_by_doc.get(doc_key, []):
                if not val:
                    lbl_with_doc = f"{label}  (нужно для: {ZHALOBA_LABELS[doc_key]})"
                    if lbl_with_doc not in errors and label not in errors:
                        errors.append(lbl_with_doc)

        if errors:
            messagebox.showwarning("Заполните поля",
                "Не заполнены обязательные поля:\n\n" +
                "\n".join(f"  • {e}" for e in errors),
                parent=self)
            return None

        zayavitel_nom = self._zayavitel.get().strip()
        zayav_dat = self._zayav_dat.get().strip() or decline_fio(zayavitel_nom, "dat")
        zayav_rod = self._zayav_rod.get().strip() or decline_fio(zayavitel_nom, "gen")

        return dict(
            selected   = selected,
            result     = self._result_var.get(),
            dept       = self._dept.get(),
            kusp_num   = self._kusp_num.get().strip(),
            kusp_date  = self._date_kusp.get_date(),
            otk_date   = self._date_otk.get_date(),
            zayavitel  = zayavitel_nom,
            zayav_dat  = zayav_dat,    # дательный: Иванову А.А.
            zayav_rod  = zayav_rod,    # родительный: Иванова А.А.
            kontakt    = self._kontakt.get().strip(),
            suit_text  = self._suit.get().strip(),
            osnov      = self._osnov.get().strip() or (OSNOV_TMPLS[0] if OSNOV_TMPLS else 'события преступления'),
            vo_full    = self._get_vo_full(),
            vo_date    = self._date_vo.get_date(),
            doc_date   = self._date_doc.get_date(),
            pojt_date  = self._date_pojt.get_date(),
            prodl_date = self._date_prodl.get_date(),
            raport_date= self._date_raport.get_date(),
            signer     = self._signer_var.get(),
        )

    # ── Генерация ─────────────────────────────────────────────────────────
    def _generate(self):
        d = self._collect()
        if not d: return

        folder = os.path.join(OUT_ROOT,
                              datetime.date.today().strftime("%d.%m.%Y"),
                              "Жалобы")
        os.makedirs(folder, exist_ok=True)
        ks = safe(d["kusp_num"])

        is_ud  = (d["result"] == "ud")
        suffix = "УД" if is_ud else "отказ"
        gen_map = {
            "post":     (f"Постановление_{suffix}_КУСП_{ks}.docx",
                         lambda out: (gen_post_ud if is_ud else gen_post_zhaloba)(
                             d["dept"], d["doc_date"], d["kusp_num"], d["kusp_date"],
                             d["otk_date"], d["zayav_rod"], d["suit_text"], d["osnov"],
                             d["pojt_date"], d["signer"], out)),
            "otvet":    (f"Ответ_{suffix}_КУСП_{ks}.docx",
                         lambda out: (gen_otvet_ud(
                             d["doc_date"], d["kusp_num"], d["kusp_date"],
                             d["vo_full"], d["vo_date"], d["otk_date"],
                             d["zayav_dat"], d["kontakt"], d["signer"], out)
                         if is_ud else gen_otvet_zhaloba(
                             d["doc_date"], d["kusp_num"], d["kusp_date"],
                             d["vo_full"], d["vo_date"], d["zayav_dat"],
                             d["kontakt"], d["signer"], out))),
            "prodlenka":(f"Продлёнка_{suffix}_КУСП_{ks}.docx",
                         lambda out: (gen_prodlenka_ud(
                             d["vo_full"], d["vo_date"], d["zayav_dat"],
                             d["kontakt"], d["pojt_date"], d["signer"], out)
                         if is_ud else gen_prodlenka(
                             d["vo_full"], d["vo_date"], d["zayav_dat"],
                             d["kontakt"], d["signer"], out))),
            "raport":   (f"Рапорт_{suffix}_КУСП_{ks}.docx",
                         lambda out: (gen_raport_ud if is_ud else gen_raport)(
                             d["dept"], d["vo_full"], d["vo_date"],
                             d["zayav_rod"], d["suit_text"], d["prodl_date"],
                             d["signer"], d["raport_date"], out)),
        }

        created = []; errors = []
        for key in d["selected"]:
            fname, gen_fn = gen_map[key]
            fpath = os.path.join(folder, fname)
            try:
                gen_fn(fpath); created.append(fname)
            except Exception as e:
                errors.append(f"{ZHALOBA_LABELS[key]}: {e}")

        if errors:
            messagebox.showerror("Ошибки", "\n\n".join(errors), parent=self)

        if created:
            msg = "✅ Создано:\n\n" + "\n".join(f"📄 {f}" for f in created)
            msg += f"\n\n📁 {folder}"
            if messagebox.askyesno("Готово", msg + "\n\nОткрыть папку?", parent=self):
                try:
                    if sys.platform.startswith("win"): os.startfile(folder)
                    else:
                        import subprocess; subprocess.Popen(["xdg-open", folder])
                except Exception: pass

    def _open_zhaloba(self):
        ZhalobaWindow(self)

    def _open_scale(self):
        global DEPT
        w = tk.Toplevel(self); w.title("Масштаб интерфейса")
        w.configure(bg="#f4f1e8"); w.geometry("340x180")
        w.transient(self); w.grab_set()
        tk.Label(w, text="🔍 Масштаб интерфейса",
                 bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        frm = tk.Frame(w, bg="#f4f1e8"); frm.pack(fill="both", expand=True, padx=16, pady=14)
        tk.Label(frm, text="Масштаб (%):", bg="#f4f1e8",
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="e", padx=6, pady=8)
        scale_var = tk.IntVar(value=int(get_ui_scale() * 100))
        scale_spin = ttk.Spinbox(frm, from_=70, to=200, increment=10,
                                  textvariable=scale_var, width=7,
                                  font=("Segoe UI", 10))
        scale_spin.grid(row=0, column=1, sticky="w", padx=6, pady=8)
        tk.Label(frm, text="(100 = стандарт, 120 = крупнее)",
                 bg="#f4f1e8", fg="#666",
                 font=("Segoe UI", 8, "italic")).grid(row=1, column=0, columnspan=2, pady=2)
        def do_apply():
            val = scale_var.get() / 100.0
            set_ui_scale(val)
            self._apply_scale(val)
            w.destroy()
        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=16, pady=6)
        tk.Button(bf, text="✅ Применить и перезапустить",
                  command=do_apply, bg="#f5d77a", fg="#0b3d2e",
                  font=("Segoe UI", 10, "bold"), padx=10, pady=4).pack(side="right")
        tk.Button(bf, text="Отмена", command=w.destroy,
                  padx=10, pady=4).pack(side="right", padx=4)

    def _apply_scale(self, scale):
        """Применяет масштаб — перезапускает приложение через os.execv."""
        try:
            import subprocess
            python = sys.executable
            script = os.path.abspath(__file__)
            self.destroy()
            os.execv(python, [python, script])
        except Exception as e:
            messagebox.showinfo("Масштаб", f"Настройки сохранены.\nПерезапустите программу вручную.\n{e}")

    def _open_out(self):
        folder = os.path.join(OUT_ROOT, datetime.date.today().strftime("%d.%m.%Y"), "Жалобы")
        os.makedirs(folder, exist_ok=True)
        try:
            if sys.platform.startswith("win"): os.startfile(folder)
            else:
                import subprocess; subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    # ── Редактор исполнителя рапорта ─────────────────────────────────────
    def _edit_raport_staff(self):
        global RAPORT_STAFF
        w = tk.Toplevel(self); w.title("Исполнитель рапорта")
        w.configure(bg="#f4f1e8"); w.geometry("520x260")
        w.transient(self); w.grab_set()
        tk.Label(w, text="Исполнитель рапорта о продлении",
                 bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        frm = tk.Frame(w, bg="#f4f1e8"); frm.pack(fill="both", expand=True, padx=16, pady=10)
        fields = [
            ("post_line1", "Должность (строка 1):"),
            ("post_line2", "Должность (строка 2):"),
            ("fio",        "И.О. Фамилия:"),
        ]
        ents = {}
        for r, (fk, fl) in enumerate(fields):
            tk.Label(frm, text=fl, bg="#f4f1e8", font=("Segoe UI", 9),
                     width=24, anchor="e").grid(row=r, column=0, sticky="e", padx=6, pady=6)
            ent = tk.Entry(frm, width=36, font=("Segoe UI", 10))
            ent.grid(row=r, column=1, sticky="w", padx=6, pady=6)
            ent.insert(0, RAPORT_STAFF.get(fk, "")); ents[fk] = ent

        def do_save():
            global RAPORT_STAFF
            RAPORT_STAFF = {fk: ent.get().strip() for fk, ent in ents.items()}
            save_raport_staff(RAPORT_STAFF)
            messagebox.showinfo("Сохранено", "Данные исполнителя сохранены.", parent=w)
            w.destroy()

        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=16, pady=6)
        tk.Button(bf, text="💾 Сохранить", command=do_save,
                  bg="#d4af37", fg="#0b3d2e", font=("Segoe UI", 10, "bold"),
                  padx=12, pady=4).pack(side="right", padx=4)
        tk.Button(bf, text="Отмена", command=w.destroy,
                  padx=12, pady=4).pack(side="right")

    # ── Редактор шаблонов сути ───────────────────────────────────────────
    def _edit_suit_tmpls(self):
        global SUIT_TMPLS
        w = tk.Toplevel(self); w.title("Шаблоны текста сути жалобы")
        w.configure(bg="#f4f1e8"); w.geometry("540x380")
        w.transient(self); w.grab_set()
        tk.Label(w, text="Шаблоны текста сути жалобы",
                 bg="#0b3d2e", fg="#d4af37",
                 font=("Segoe UI", 11, "bold"), pady=6).pack(fill="x")
        tk.Label(w, text="Двойной клик — редактировать. Появляются в меню «▼ шаблоны».",
                 bg="#f4f1e8", fg="#555",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=10, pady=(4,2))

        body = tk.Frame(w, bg="#f4f1e8"); body.pack(fill="both", expand=True, padx=10, pady=4)
        lb = tk.Listbox(body, font=("Segoe UI", 10), activestyle="dotbox")
        sb = tk.Scrollbar(body, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True); sb.pack(side="left", fill="y")

        def refresh(sel=None):
            lb.delete(0, "end")
            for t in SUIT_TMPLS: lb.insert("end", t)
            if sel is not None and 0 <= sel < len(SUIT_TMPLS):
                lb.selection_set(sel); lb.see(sel)

        def cur_idx():
            s = lb.curselection(); return s[0] if s else None

        def edit_dlg(idx=None):
            ed = tk.Toplevel(w); ed.configure(bg="#f4f1e8")
            ed.title("Изменить" if idx is not None else "Добавить")
            ed.transient(w); ed.grab_set()
            tk.Label(ed, text="Текст шаблона:", bg="#f4f1e8",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(10,2))
            ent = tk.Entry(ed, width=54, font=("Segoe UI", 10))
            ent.pack(padx=10, pady=4)
            if idx is not None: ent.insert(0, SUIT_TMPLS[idx])
            def do_s():
                global SUIT_TMPLS
                val = ent.get().strip()
                if not val: return
                if idx is not None: SUIT_TMPLS[idx] = val
                else: SUIT_TMPLS.append(val)
                save_suit_tmpls(SUIT_TMPLS); ed.destroy()
                refresh(idx if idx is not None else len(SUIT_TMPLS)-1)
            bf2 = tk.Frame(ed, bg="#f4f1e8"); bf2.pack(fill="x", padx=10, pady=6)
            tk.Button(bf2, text="Сохранить", command=do_s, bg="#d4af37", fg="#0b3d2e",
                      padx=10, pady=3).pack(side="left", padx=4)
            tk.Button(bf2, text="Отмена", command=ed.destroy, padx=10, pady=3).pack(side="left")
            ent.focus_set()

        def do_del():
            global SUIT_TMPLS
            i = cur_idx()
            if i is None: return
            if not messagebox.askyesno("Удалить", f"Удалить «{SUIT_TMPLS[i]}»?", parent=w): return
            SUIT_TMPLS.pop(i); save_suit_tmpls(SUIT_TMPLS); refresh()

        lb.bind("<Double-Button-1>", lambda e: edit_dlg(cur_idx()))
        bf = tk.Frame(w, bg="#f4f1e8"); bf.pack(fill="x", padx=10, pady=(4,10))
        tk.Button(bf, text="➕ Добавить", command=lambda: edit_dlg(None), padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="✎ Изменить", command=lambda: edit_dlg(cur_idx()), padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="🗑 Удалить",  command=do_del, padx=8, pady=4).pack(side="left", padx=3)
        tk.Button(bf, text="Закрыть",    command=w.destroy, padx=8, pady=4).pack(side="right", padx=3)
        refresh()

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
