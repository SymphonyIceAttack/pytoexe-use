import os, re, json, threading, time
import tkinter as tk
from tkinter import ttk, messagebox

import tgbot as bot  

APP_VERSION = "1.0.5.3 beta"

# =========================
# Локальные настройки
# =========================
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "scanner_settings.json")

def _default_settings():
    return {
        "theme": "dark",  # dark|light
        "com_port": "COM3",
        "baudrate": 115200,
        "paths": {
            "FBO": r"G:\Мой диск\Склад",
            "WB": getattr(bot, "WB_PATH", ""),
            "OZON": getattr(bot, "OZON_PATH", ""),
        },
        "printers": {
            "market": "wb",
            "fbo": "wb",
            "boxes": getattr(bot, "BOXES_PRINTER", "wb"),
            "material": getattr(bot, "MATERIAL_PRINTER", "wb"),
            "ink": "wb",
        },
    }

def load_settings():
    s = _default_settings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            u = json.load(f)
        if isinstance(u, dict):
            for k in ("theme","com_port","baudrate"):
                if k in u: s[k] = u[k]
            if isinstance(u.get("paths"), dict):
                s["paths"].update(u["paths"])
            if isinstance(u.get("printers"), dict):
                s["printers"].update(u["printers"])
    except Exception:
        pass
    return s

def save_settings(s):
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_FILE)

SET = load_settings()


try:
    import serial
    import serial.tools.list_ports
except Exception:
    serial = None  



# FBO (склад) этикетки лежат отдельно. Важно: при скане сначала пытаемся найти файл тут,
# чтобы не печатать похожие этикетки из WB/OZON.
FBO_PATH = SET["paths"]["FBO"]

def _decode_com_bytes(data: bytes) -> str:
    if not data:
        return ""
    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            s = data.decode(enc)
            if enc == "utf-8" and ("�" in s):
                continue
            return s
        except Exception:
            continue
    try:
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return ''

def _normpath(p: str) -> str:
    try:
        return os.path.normcase(os.path.abspath(p))
    except Exception:
        return str(p)

# ----------------- Помощник -----------------

def _pc_username() -> str:
    for k in ("USERNAME", "USER", "LOGNAME"):
        v = os.environ.get(k)
        if v:
            return v
    try:
        return os.getlogin()
    except Exception:
        return "PC"

def _safe_strip_prefix(s: str) -> str:
    s = (s or "").strip()
    return s[1:].strip() if s.startswith("#") else s


def _split_sku_uid(raw: str) -> tuple[str, str|None]:
    """Разбираем строку со складской этикетки: 'SKU | UID'.
    Возвращает (sku, uid_or_None). Если разделителя нет — sku=raw, uid=None.
    Допускаем разделители: '|', '｜' (полный), '¦'.
    """
    s = (raw or "").strip()
    if not s:
        return "", None
    # нормализуем разделитель
    for sep in ("|", "｜", "¦"):
        if sep in s:
            left, right = s.split(sep, 1)
            sku = left.strip()
            uid = right.strip()
            uid = uid if uid else None
            return sku, uid
    return s, None

def _normalize_sku_for_match(sku: str) -> str:
    """Нормализуем SKU склада (убираем пробелы, приводим 'х/×' к 'x', нижний регистр)."""
    s = (sku or "").strip().lower()
    s = s.replace("×", "x").replace("х", "x").replace(" ", "")
    s = s.replace("__", "_")
    return s
def _looks_like_uid(s: str) -> bool:
    s = (s or "").strip()
    return s.isdigit() and 3 <= len(s) <= 10

def _extract_uid_from_any(raw: str) -> str|None:
    s = (raw or "").strip()
    if not s:
        return None
    if s.isdigit():
        return s
    nums = re.findall(r"\b(\d{3,10})\b", s)
    return nums[-1] if nums else None

def _parse_json_kind(raw: str) -> tuple[str|None, dict|None]:
    raw = (raw or "").strip()
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                kind = (data.get("kind") or "").lower()
                return kind or None, data
        except Exception:
            return None, None
    return None, None

def _score_path(path: str, uid: str|None) -> tuple:
    """Меньше — лучше."""
    name = os.path.basename(path).lower()
    score = 0
    if uid:
        if re.search(rf"(?:^|[_\-\s]){re.escape(uid)}(?:[_\-\s\.]|$)", name):
            score -= 100
        if f"_{uid}." in name:
            score -= 80
        if uid in name:
            score -= 30
        else:
            score += 200
    score += min(len(name), 200)/200.0
    if name.startswith("самовыкуп"):
        score -= 5
    return (score, len(name), name)

def _best_single_match(paths: list[str], uid: str|None) -> str|None:
    if not paths:
        return None
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        return None
    paths.sort(key=lambda p: _score_path(p, uid))
    return paths[0]


def _file_tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[ _\.\-]+", (name or "").lower()) if t]

def _find_matches_in_dir(directory: str, barcode: str, prefer_full: bool) -> list[str]:
    if not os.path.isdir(directory):
        return []
    raw = (barcode or "").strip()
    if not raw:
        return []

    raw_l = raw.lower().replace(" ", "")
    base = raw_l.split("-")[0] if "-" in raw_l else raw_l

    strong = set()
    strong.add(raw_l)
    for seg in re.findall(r"\d+-\d+", raw_l):
        strong.add(seg)

    weak = set([base]) if base else set()

    scored: list[tuple[int, str]] = []
    for root, _dirs, files in os.walk(directory):
        for fname in files:
            full = os.path.join(root, fname)
            if not os.path.isfile(full):
                continue
            low = fname.lower().replace(" ", "")

            parts = set(_file_tokens(low))
            score = 0
            if raw_l and (raw_l in parts or raw_l in low):
                score += 100
            if any(t in parts or t in low for t in strong if t):
                score += 60
            if any(t in parts for t in weak if t):
                score += 10

            if score > 0:
                scored.append((score, full))

    scored.sort(key=lambda x: (-x[0], len(os.path.basename(x[1]))))
    return [p for _s, p in scored]

def find_sticker_files_pc(barcode: str) -> tuple[list[str], str|None]:

    # 1) Сначала Склад (FBO) — строгий матч (без split('-')[0])
    fbo_matches = _find_matches_in_dir(FBO_PATH, barcode, prefer_full=True)
    if fbo_matches:
        prn = None
        try:
            # принтер из маппинга бота (если там прописан)
            prn = bot.PRINTER_PATH_MAP.get(FBO_PATH) or bot.PRINTER_PATH_MAP.get(_normpath(FBO_PATH))
        except Exception:
            prn = None
        return fbo_matches, prn or "wb"

    # 2) Иначе — как в боте (WB/OZON/прочее)
    return bot.find_sticker_files(barcode)




# ----------------- Скан склада (без протыкивания WB/OZON) -----------------

_SIZE_X_RE = re.compile(r"(\d)\s*[xх×]\s*(\d)", re.IGNORECASE)

def _norm_sku(s: str) -> str:
    """
    Нормализуем строку SKU/ярлыка для сопоставления:
    - убираем пробелы
    - приводим '312 x 270' / '312×270' / '312х270' -> '312x270'
    - lower()
    """
    s = (s or "").strip()
    if not s:
        return ""
    s = _SIZE_X_RE.sub(r"\1x\2", s)
    s = s.replace(" ", "")
    return s.lower()

def _warehouse_pick_best(cands: list[tuple[str, str, bool, str]]) -> tuple[str, str, bool, str] | None:
    """
    candidates: [(dir, filename, is_selfbuy, article), ...]
    Выбираем лучший:
    1) самовыкуп выше расхода
    2) короче имя файла
    3) более ранний по алфавиту
    """
    if not cands:
        return None
    def key(t):
        directory, fname, is_selfbuy, article = t
        low = fname.lower()
        return (
            0 if is_selfbuy else 1,
            len(low),
            low,
            _normpath(os.path.join(directory, fname)),
        )
    return sorted(cands, key=key)[0]

def warehouse_try_print_by_sku(raw: str, log) -> bool:
    """
    Сканируем СКЛАДСКУЮ этикетку/QR (SKU макета) и печатаем без выбора складов:
    - ищем в WB_PATH и OZON_PATH одновременно
    - находит файл(ы) расход_/самовыкуп_ с этим SKU
    - печатает 1 лучший и делает всё как warehouse_print_one()
    Возвращает True если что-то напечатали.
    """
    sku_raw = (raw or "").strip()
    if not sku_raw:
        return False

    sku_n = _norm_sku(sku_raw)

    # Быстро отсекаем числовые UID — это не складской SKU, пусть идёт в обычный print_by_scan()
    if _looks_like_uid(sku_raw):
        return False

    candidates: list[tuple[str, str, bool, str]] = []

    for directory in (SET["paths"].get("WB",""), SET["paths"].get("OZON","")):
        if not directory or not os.path.isdir(directory):
            continue

        # как и раньше по аналогии: самовыкуп имеет приоритет, чистим конфликты
        try:
            bot.purge_selfbuy_precedence(directory)
        except Exception:
            pass

        for fname in bot.get_active_files(directory):
            try:
                article = bot.extract_article_from_filename(fname)
            except Exception:
                continue

            if _norm_sku(article) == sku_n:
                is_selfbuy = fname.lower().startswith("самовыкуп")
                candidates.append((directory, fname, is_selfbuy, article))

    best = _warehouse_pick_best(candidates)
    if not best:
        return False

    directory, fname, is_selfbuy, article = best
    printer = "wb"
    warehouse_print_one(directory, printer, fname, is_selfbuy, article, log)
    return True


def _sheet_strict(barcode: str, source: str, log):
    payload = {
        "user": _pc_username(),
        "barcode": barcode,
        "source": source,
        "ts": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }
    ok, err = bot._post_to_google_sheet_strict(payload, timeout=20)
    if not ok:
        log("❌ Таблица не подтвердила запись. Печати не будет.")
        if err:
            log(f"   Детали: {err[:200]}")
        return False
    return True

def print_by_scan(code_raw: str, log):
    """
    Аналог scan_barcode() вне awaiting:
    - строгая запись в таблицу
    - поиск файлов
    - печать
    """
    code_raw = (code_raw or "").strip()
    if not code_raw:
        return

    kind, _data = _parse_json_kind(code_raw)
    if kind == "box":
        boxes_writeoff_by_qr(code_raw, log)
        return
    if kind in ("material", "ink"):
        log("ℹ️ Это служебный QR (материал/чернила). Используйте раздел «🏬 Склад» для привязки к ячейке.")
        return

    if not _sheet_strict(code_raw, "osnova", log):
        return

    log("✅ Таблица подтвердила запись. Ищу файлы…")
    matched, printer = find_sticker_files_pc(code_raw)

    if not matched:
        log("✅ Записано в таблицу, но файлы для печати не найдены.")
        return

    uid = _extract_uid_from_any(code_raw)

    # SAFETY: печатаем один лучший файл. Если совпадений много и uid не распознан — просим выбрать.
    best = _best_single_match(matched, uid)
    if not best:
        log("⚠️ Файлы найдены, но лучший матч не определён.")
        return

    # Если matched > 1 и uid есть — всё равно печатаем best.
    # Если matched > 1 и uid НЕТ — чтобы не печатать пачкой, просим выбрать.
    if len(matched) > 1 and not uid:
        log(f"⚠️ Найдено {len(matched)} файлов. Чтобы не напечатать лишнее — выберите в окне «Выбор файла» ниже.")
        return ("need_pick", matched, printer)

    log(f"🖨️ Печать: {os.path.basename(best)} → {printer}")
    ok = bot.print_file(best, printer)
    if ok:
        log("✅ Напечатано: 1")
        try:
            directory = os.path.dirname(best)
            fname = os.path.basename(best)
            key = bot._file_order_key_from_name(fname)
            bot._printed_index_add(key, directory, fname)
        except Exception:
            pass
    else:
        log("❌ Ошибка печати.")
    return None


def warehouse_list_rows(directory: str):
    # как handle_generic_warehouse: purge, get_active_files, extract_article_from_filename
    try:
        bot.purge_selfbuy_precedence(directory)
    except Exception:
        pass
    files = bot.get_active_files(directory)
    rows = []
    for f in files:
        is_selfbuy = f.lower().startswith("самовыкуп")
        art = bot.extract_article_from_filename(f)
        rows.append((art, f, "самовыкуп" if is_selfbuy else "расход", is_selfbuy))
    rows.sort(key=lambda x: (x[0].lower(), x[1].lower()))
    return rows

def warehouse_print_one(directory: str, printer: str, filename: str, is_selfbuy: bool, article: str, log):
    full_path = os.path.join(directory, filename)
    barcode_val = bot.extract_barcode_from_filename(filename)

    if not _sheet_strict(barcode_val, "osnova", log):
        return

    log("✅ Таблица подтвердила запись. Печатаю…")
    ok = bot.print_file(full_path, printer)
    if not ok:
        log("❌ Ошибка печати.")
        return

    if not is_selfbuy:
        try:
            import asyncio
            asyncio.run(bot.decrement_balance(article))
        except Exception:
            pass

    # переименование как в handle_item_selection()
    try:
        key = bot._file_order_key_from_name(filename)
        if is_selfbuy:
            dst = filename.replace("самовыкуп", "напечатано_самовыкуп")
        else:
            dst = filename.replace("расход", "напечатано")
        os.rename(full_path, os.path.join(directory, dst))
        bot._printed_index_add(key, directory, dst)
    except Exception as e:
        log(f"⚠️ Напечатано, но не смог переименовать файл: {e}")

    log(f"✅ {article}{' (САМОВЫКУП)' if is_selfbuy else ''} напечатан.")


# ----------------- (🏬 Склад) -----------------

class StorageBinder:
    """
    Состояние как в scan_barcode awaiting:
    - stage 'item_qr' → ждём QR товара или материала
    - stage 'cell_qr' → ждём QR ячейки
    """
    def __init__(self):
        self.stage = "item_qr"
        self.mode = None       
        self.tmp_item_qr = None
        self.tmp_material_id = None
        self.tmp_ink_id = None
        self.tmp_ink_id = None
        self.tmp_ink_id = None

    def reset(self):
        self.stage = "item_qr"
        self.mode = None
        self.tmp_item_qr = None
        self.tmp_material_id = None

    def accept_scan(self, raw: str, log):
        raw = (raw or "").strip()
        if not raw:
            return

        if self.stage == "item_qr":
            kind, data = _parse_json_kind(raw)
            if kind == "material" and isinstance(data, dict) and "id" in data:
                self.mode = "material"
                self.tmp_material_id = str(data["id"])
                self.stage = "cell_qr"
                log("👌 Материал принят. Теперь — QR ячейки.")
                return
            if kind == "ink" and isinstance(data, dict) and "id" in data:
                self.mode = "ink"
                self.tmp_ink_id = str(data["id"])
                self.stage = "cell_qr"
                log("👌 Чернила приняты. Теперь — QR ячейки.")
                return
            # обычный товар: extract_item_code как в боте (до |)
            self.mode = "item"
            self.tmp_item_qr = bot.extract_item_code(raw)
            self.stage = "cell_qr"
            log("👌 Товар принят. Теперь — QR ячейки.")
            return

        if self.stage == "cell_qr":
            cell_qr = raw
            if self.mode == "material" and self.tmp_material_id:
                mid = self.tmp_material_id
                try:
                    import asyncio
                    asyncio.run(bot.mat_set_location(mid, cell_qr))
                    log(f"✅ Материал ID {mid} привязан к ячейке {cell_qr}.")
                except Exception as e:
                    log(f"❌ Ошибка привязки материала: {e}")
                self.reset()
                return

            if self.mode == "ink" and self.tmp_ink_id:
                iid = self.tmp_ink_id
                try:
                    ok = inks_set_location(iid, cell_qr)
                    if ok:
                        log(f"✅ Чернила ID {iid} привязаны к ячейке {cell_qr}.")
                    else:
                        log(f"❌ Чернила ID {iid} не найдены в базе.")
                except Exception as e:
                    log(f"❌ Ошибка привязки чернил: {e}")
                self.reset()
                return

            if self.mode == "item" and self.tmp_item_qr:
                item = self.tmp_item_qr
                try:
                    import asyncio
                    asyncio.run(bot.add_record(item, cell_qr))
                    log(f"✅ Пара «{item} ↔ {cell_qr}» сохранена.")
                except Exception as e:
                    log(f"❌ Ошибка сохранения пары: {e}")
                self.reset()
                return

            log("⚠️ Ошибка последовательности. Начните заново.")
            self.reset()
            return


# ----------------- (QR) -----------------
def boxes_receive_packs(box_type: str, count: int, log):
    """Приемка пачек коробок + печать QR этикеток на каждую пачку."""
    box_type = (box_type or "").strip()
    if not box_type:
        raise ValueError("box_type")
    if count <= 0:
        raise ValueError("count")

    # добавляем пачки в учёт бота
    new_total = bot.boxes_add_packs(box_type, count)
    log(f"✅ Оприходовано: {box_type} ×{count}. Остаток: {new_total} пач.")

    printed = 0
    for _ in range(count):
        ok = False
        try:
            ok = bool(bot.print_box_label(box_type))
        except Exception:
            # fallback если в боте иначе
            try:
                png = bot.generate_box_qr_png(box_type, dpi=300)
                ok = bool(bot.print_file(png, SET["printers"]["boxes"]))
            except Exception:
                ok = False
        if ok:
            printed += 1
    log(f"🖨️ Этикеток коробок напечатано: {printed}/{count}")


def boxes_writeoff_by_qr(raw: str, log):
    kind, data = _parse_json_kind(raw)
    if kind != "box" or not isinstance(data, dict):
        log("❌ Это не QR пачки коробок (ожидался JSON kind=box).")
        return
    bt = data.get("box_type") or "короб"
    try:
        res = bot.boxes_mark_used(str(bt))
        if res == "ok":
            left = bot.boxes_summary().get(str(bt), 0)
            log(f"✅ Пачка «{bt}» списана. Осталось: {left} пач.")
        elif res == "empty":
            log(f"⚠️ Для «{bt}» остаток 0. Списывать нечего.")
        else:
            log("❌ Не удалось списать пачку.")
    except Exception as e:
        log(f"⛔ Ошибка списания коробок: {e}")



# ----------------- (🖋️ Чернила) -----------------
# Отдельный учёт чернил + QR этикетки + привязка к ячейке.
# Не парсится в бота

try:
    import qrcode  # type: ignore
except Exception:
    qrcode = None  # type: ignore

from datetime import datetime as _dt
from uuid import uuid4 as _uuid4

INK_COLORS = ["Magenta", "Yellow", "Cyan", "Black"]
INKS_PRINTER = "wb"  

def _inks_db_path() -> str:
    base = getattr(bot, "QUEUE_DIR", os.path.dirname(__file__))
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        base = os.path.dirname(__file__)
    return os.path.join(base, "inks_stock.json")

def _load_inks_db() -> dict:
    path = _inks_db_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"packs": []}
        if "packs" not in data or not isinstance(data["packs"], list):
            data["packs"] = []
        return data
    except FileNotFoundError:
        return {"packs": []}
    except Exception:
        return {"packs": []}

def _save_inks_db(db: dict) -> None:
    path = _inks_db_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def inks_summary() -> dict[str, int]:
    db = _load_inks_db()
    res = {c: 0 for c in INK_COLORS}
    for p in db.get("packs", []):
        if (p.get("status") or "in_stock") != "in_stock":
            continue
        c = p.get("color")
        if c in res:
            res[c] += 1
        else:
            res[c] = res.get(c, 0) + 1
    return res

def inks_add_packs(color: str, count: int) -> list[dict]:
    color = (color or "").strip()
    if color not in INK_COLORS:
        raise ValueError("Неверный цвет чернил")
    if count <= 0:
        raise ValueError("count должен быть > 0")

    db = _load_inks_db()
    packs = db.get("packs", [])
    created = []
    for _ in range(count):
        pid = _uuid4().hex[:10]
        rec = {
            "id": pid,
            "kind": "ink",
            "color": color,
            "cell_qr": "",
            "status": "in_stock",
            "created_at": _dt.now().isoformat(timespec="seconds"),
            "used_at": "",
        }
        packs.append(rec)
        created.append(rec)
    db["packs"] = packs
    _save_inks_db(db)
    return created

def inks_set_location(pack_id: str, cell_qr: str) -> bool:
    db = _load_inks_db()
    packs = db.get("packs", [])
    for p in packs:
        if str(p.get("id")) == str(pack_id):
            p["cell_qr"] = str(cell_qr)
            _save_inks_db(db)
            return True
    return False

def inks_mark_used(pack_id: str) -> str:
    db = _load_inks_db()
    packs = db.get("packs", [])
    for p in packs:
        if str(p.get("id")) == str(pack_id):
            if (p.get("status") or "in_stock") != "in_stock":
                return "already"
            p["status"] = "used"
            p["used_at"] = _dt.now().isoformat(timespec="seconds")
            _save_inks_db(db)
            return "ok"
    return "not_found"

def _generate_qr_png(payload: dict, caption: str, out_path: str, dpi: int = 300) -> str:
    # Наши дефолт этикетки 56x40 мм
    mm_w, mm_h = 56, 40
    px_w = int(round(dpi * (mm_w / 25.4)))
    px_h = int(round(dpi * (mm_h / 25.4)))
    margin = int(round(dpi * (3 / 25.4)))
    text_h = int(round(dpi * (12 / 25.4)))
    qr_side = min(px_w - 2*margin, px_h - 2*margin - text_h)

    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (px_w, px_h), "white")
    draw = ImageDraw.Draw(img)

    payload_json = json.dumps(payload, ensure_ascii=False)

    if qrcode:
        qr = qrcode.QRCode(border=1, box_size=10)
        qr.add_data(payload_json)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((qr_side, qr_side), Image.NEAREST)
    else:
        qr_img = Image.new("RGB", (qr_side, qr_side), "white")
        ImageDraw.Draw(qr_img).rectangle((0, 0, qr_side-1, qr_side-1), outline="black")

    qr_x = (px_w - qr_side) // 2
    qr_y = margin
    img.paste(qr_img, (qr_x, qr_y))

    try:
        font = ImageFont.truetype("arial.ttf", max(22, int(qr_side * 0.12)))
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.multiline_textbbox((0, 0), caption, font=font, align="center")
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    tx = (px_w - tw) // 2
    ty = qr_y + qr_side + max(0, (text_h - th)//2)
    draw.multiline_text((tx, ty), caption, font=font, fill="black", align="center")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    return out_path

def print_ink_label(pack: dict) -> bool:
    # печатаем одну этикетку упаковки чернил
    base = getattr(bot, "QUEUE_DIR", os.path.dirname(__file__))
    labels_dir = os.path.join(base, "_ink_labels")
    pid = str(pack.get("id"))
    color = str(pack.get("color"))
    payload = {"kind": "ink", "id": pid, "color": color}
    caption = f"COLOR INK: {color}\nID: {pid}"
    png_path = os.path.join(labels_dir, f"ink_{color}_{pid}.png")
    _generate_qr_png(payload, caption, png_path, dpi=300)
    try:
        return bool(bot.print_file(png_path, INKS_PRINTER))
    except Exception:
        try:
            return bool(bot.print_file(png_path, "wb"))
        except Exception:
            return False

# ----------------- Темы -----------------

def apply_theme_ttk(app: tk.Tk, theme: str):
    style = ttk.Style(app)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    if theme == "dark":
        bg = "#0f172a"; fg="#e5e7eb"; card="#111c34"; muted="#94a3b8"; accent="#38bdf8"
        entry="#0b1224"; sel="#1d4ed8"
    else:
        bg = "#f6f7fb"; fg="#0f172a"; card="#ffffff"; muted="#475569"; accent="#2563eb"
        entry="#ffffff"; sel="#c7d2fe"
    app.configure(bg=bg)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("Muted.TLabel", background=bg, foreground=muted)
    style.configure("Header.TLabel", background=bg, foreground=fg, font=("Segoe UI", 11, "bold"))
    style.configure("TButton", padding=7)
    style.configure("Accent.TButton", padding=7)
    style.map("Accent.TButton", background=[("active", accent)])
    style.configure("TEntry", fieldbackground=entry)
    style.configure("TCombobox", fieldbackground=entry)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure("Treeview", background=entry, fieldbackground=entry, foreground=fg)
    style.map("Treeview", background=[("selected", sel)], foreground=[("selected", fg)])


# ----------------- GUI -----------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        apply_theme_ttk(self, SET.get('theme','dark'))
        try:
            style = ttk.Style(self)
            # более современная тема
            if "clam" in style.theme_names():
                style.theme_use("clam")
            style.configure("TButton", padding=6)
            style.configure("TLabel", padding=2)
            style.configure("TLabelframe", padding=6)
        except Exception:
            pass

        self.title(f"Exponenta Scanner {APP_VERSION}")
        self.geometry("1040x720")

        self.binder = StorageBinder()

        self._last_scan = None
        self._last_scan_ts = 0.0

        self._com_thread = None
        self._com_stop = threading.Event()

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        # основное меню
        left = ttk.Frame(root, width=220)
        left.pack(side="left", fill="y", padx=(10,5), pady=10)

        ttk.Label(left, text="Меню", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,8))

        self.btn_scan = ttk.Button(left, text="📸 Сканер", command=lambda: self._show("scan"))
        self.btn_scan.pack(fill="x", pady=3)

        self.btn_wb = ttk.Button(left, text="🏢 Склад WB", command=lambda: self._show("wb"))
        self.btn_wb.pack(fill="x", pady=3)

        self.btn_oz = ttk.Button(left, text="🏢 Склад OZON", command=lambda: self._show("ozon"))
        self.btn_oz.pack(fill="x", pady=3)

        self.btn_bind = ttk.Button(left, text="🏬 Склад", command=lambda: self._show("bind"))
        self.btn_bind.pack(fill="x", pady=3)

        self.btn_boxes = ttk.Button(left, text="📦 Коробки", command=lambda: self._show("boxes"))
        self.btn_boxes.pack(fill="x", pady=3)

        self.btn_material = ttk.Button(left, text="🧵 Материал", command=lambda: self._show("material"))
        self.btn_material.pack(fill="x", pady=3)

        self.btn_ink = ttk.Button(left, text="🖋️ Чернила", command=lambda: self._show("ink"))
        self.btn_ink.pack(fill="x", pady=3)


        self.btn_settings = ttk.Button(left, text="⚙️ Настройки", command=lambda: self._show("settings"))
        self.btn_settings.pack(fill="x", pady=3)

        self.btn_help = ttk.Button(left, text="📘 Инструкция", command=lambda: self._show("help"))
        self.btn_help.pack(fill="x", pady=3)


        ttk.Separator(left).pack(fill="x", pady=10)

        ttk.Label(left, text="Активация сканера", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        comrow = ttk.Frame(left)
        comrow.pack(fill="x", pady=(6,3))
        self.com_ports = ttk.Combobox(comrow, width=10, state="readonly")
        self.com_ports.pack(side="left")
        self.btn_ports = ttk.Button(comrow, text="🔄", width=3, command=self._refresh_ports)
        self.btn_ports.pack(side="left", padx=6)

        self.btn_com = ttk.Button(left, text="▶ Соединить", command=self._toggle_com)
        self.btn_com.pack(fill="x", pady=3)

        self.com_status = ttk.Label(left, text="статус: остановлен", font=("Segoe UI", 9))
        self.com_status.pack(anchor="w", pady=(4,0))

        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True, padx=(5,10), pady=10)

        # Верхний статус (режим/ошибки/что делать)
        self.top_status = ttk.Label(right, text="Готов к скану", font=("Segoe UI", 10, "bold"))
        self.top_status.pack(anchor="w", pady=(0,6))

        self.container = ttk.Frame(right)
        self.container.pack(fill="both", expand=True)

        log_frame = ttk.Frame(right)
        log_frame.pack(fill="both", expand=False, pady=(10,0))
        ttk.Label(log_frame, text="Лог:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.log_box = tk.Text(log_frame, height=16, state="disabled", font=("Consolas", 10))
        self.log_box.pack(fill="both", expand=False)

        self.status_bar = ttk.Label(right, text=f"Версия: {APP_VERSION}", style="Muted.TLabel")
        self.status_bar.pack(anchor="e", pady=(6,0))

        self.screens = {}
        self._build_screen_scan()
        self._build_screen_warehouse("wb", bot.WB_PATH, "wb", title="🏢 Склад WB")
        self._build_screen_warehouse("ozon", bot.OZON_PATH, "wb", title="🏢 Склад OZON")
        self._build_screen_bind()
        self._build_screen_boxes()
        self._build_screen_material()
        self._build_screen_ink()
        self._build_screen_settings()
        self._build_screen_help()

        self._refresh_ports()
        self._show("scan")

    def log(self, msg: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _show(self, key: str):
        for k, fr in self.screens.items():
            fr.pack_forget()
        self.screens[key].pack(fill="both", expand=True)

    def _should_process(self, raw: str) -> bool:
        now = time.time()
        raw = (raw or "").strip()
        if not raw:
            return False
        if self._last_scan == raw and (now - self._last_scan_ts) < 1.5:
            return False
        self._last_scan = raw
        self._last_scan_ts = now
        return True

    # -------- Вкладка Сканер --------
    def _build_screen_scan(self):
        fr = ttk.Frame(self.container)
        self.screens["scan"] = fr

        ttk.Label(fr, text="📸 Сканер:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,10))

        row = ttk.Frame(fr)
        row.pack(fill="x", pady=5)

        ttk.Label(row, text="Ввод:").pack(side="left")
        self.scan_entry = ttk.Entry(row, font=("Consolas", 16))
        self.scan_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.scan_entry.bind("<Return>", lambda e: self._do_scan_print())

        ttk.Button(row, text="Печать", command=self._do_scan_print).pack(side="left")
        ttk.Button(row, text="Очистить", command=lambda: self.scan_entry.delete(0,"end")).pack(side="left", padx=6)

        self.pick_frame = ttk.LabelFrame(fr, text="Выбор файла (если найдено несколько)")
        self.pick_list = tk.Listbox(self.pick_frame, height=6)
        self.pick_list.pack(fill="both", expand=True, padx=8, pady=6)
        btnp = ttk.Frame(self.pick_frame)
        btnp.pack(fill="x", padx=8, pady=(0,8))
        ttk.Button(btnp, text="Печатать выбранный", command=self._print_picked).pack(side="left")
        ttk.Button(btnp, text="Скрыть", command=lambda: self.pick_frame.pack_forget()).pack(side="left", padx=8)

        self._pick_paths = []
        self._pick_printer = None

        hint = ttk.Label(fr, text="Совет: иногда проверяйте напечатанные этикетки и логи. Для всего остального есть вкладка Инструкция или пишите в чат с проблемами", font=("Segoe UI", 9))
        hint.pack(anchor="w", pady=(10,0))

    def _do_scan_print(self):
        raw0 = _safe_strip_prefix(self.scan_entry.get())
        self.scan_entry.delete(0,"end")
        if not raw0:
            return

        # Если включен режим списания чернил — пытаемся списать по QR JSON kind=ink
        if getattr(self, "_ink_writeoff_mode", False):
            if self._ink_try_writeoff(raw0):
                return


        # Если включен режим списания коробок — списываем по QR JSON kind=box (1 пачка)
        if getattr(self, "_boxes_writeoff_mode", False):
            kind, _d = _parse_json_kind(raw0)
            if kind == "box":
                boxes_writeoff_by_qr(raw0, self.log)
                try:
                    self._boxes_refresh()
                except Exception:
                    pass
                return

        # Если включен режим списания материала — списываем рулон по QR JSON kind=material
        if getattr(self, "_mat_writeoff_mode", False):
            kind, _d = _parse_json_kind(raw0)
            if kind == "material":
                try:
                    self._mat_writeoff_by_qr(raw0)
                except Exception as e:
                    self.log(f"⛔ Материал: ошибка списания по QR: {e}")
                return


        # Складская этикетка может быть вида: 'SKU | UID'
        sku, uid = _split_sku_uid(raw0)

        # 1) Попытка печати со складов WB/OZON по SKU (без выбора складов)
        if sku and warehouse_try_print_by_sku(sku, self.log):
            return

        # 2) Иначе — обычная печать по штрихкоду/UID (если UID есть справа от '|', используем его)
        raw = uid or raw0

        res = print_by_scan(raw, self.log)
        if isinstance(res, tuple) and res and res[0] == "need_pick":
            _, paths, prn = res
            self._pick_paths = paths
            self._pick_printer = prn
            self.pick_list.delete(0,"end")
            for p in paths[:200]:
                self.pick_list.insert("end", os.path.basename(p))
            self.pick_frame.pack(fill="both", expand=False, pady=(10,0))

    def _print_picked(self):
        sel = self.pick_list.curselection()
        if not sel:
            messagebox.showinfo("Выбор", "Выбери файл в списке.")
            return
        idx = sel[0]
        path = self._pick_paths[idx]
        prn = self._pick_printer
        self.log(f"🖨️ Печать выбранного: {os.path.basename(path)} → {prn}")
        ok = bot.print_file(path, prn)
        if ok:
            self.log("✅ Напечатано: 1")
        else:
            self.log("❌ Ошибка печати.")

    # -------- Вкладки Склады МП --------
    def _build_screen_warehouse(self, key: str, directory: str, printer: str, title: str):
        fr = ttk.Frame(self.container)
        self.screens[key] = fr

        ttk.Label(fr, text=title, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(fr, text=f"Папка: {directory}", font=("Segoe UI", 9)).pack(anchor="w")

        ctrl = ttk.Frame(fr)
        ctrl.pack(fill="x", pady=8)
        ttk.Button(ctrl, text="🔄 Обновить", command=lambda: self._refresh_wh(key)).pack(side="left")
        ttk.Button(ctrl, text="🖨️ Печать выбранного", command=lambda: self._print_wh_selected(key)).pack(side="left", padx=8)
        ttk.Label(ctrl, text="Поиск:").pack(side="left", padx=(18,6))
        ent = ttk.Entry(ctrl)
        ent.pack(side="left", fill="x", expand=True)
        ent.bind("<KeyRelease>", lambda e: self._apply_wh_filter(key, ent.get().strip()))
        setattr(self, f"_wh_search_{key}", ent)

        cols = ("article","file","type")
        tree = ttk.Treeview(fr, columns=cols, show="headings", height=16)
        tree.heading("article", text="SKU")
        tree.heading("file", text="Файл")
        tree.heading("type", text="Тип")
        tree.column("article", width=240)
        tree.column("file", width=560)
        tree.column("type", width=120, anchor="center")
        tree.pack(fill="both", expand=True, pady=(6,0))
        tree.bind("<Double-1>", lambda e: self._print_wh_selected(key))

        setattr(self, f"_wh_tree_{key}", tree)
        setattr(self, f"_wh_dir_{key}", directory)
        setattr(self, f"_wh_prn_{key}", printer)
        setattr(self, f"_wh_rows_{key}", [])

        self._refresh_wh(key)

    def _refresh_wh(self, key: str):
        tree: ttk.Treeview = getattr(self, f"_wh_tree_{key}")
        directory: str = getattr(self, f"_wh_dir_{key}")

        if not os.path.isdir(directory):
            self.log(f"⚠️ Папка не найдена: {directory}")
            return

        rows = warehouse_list_rows(directory)
        setattr(self, f"_wh_rows_{key}", rows)
        search: ttk.Entry = getattr(self, f"_wh_search_{key}")
        self._apply_wh_filter(key, search.get().strip())

    def _apply_wh_filter(self, key: str, q: str):
        tree: ttk.Treeview = getattr(self, f"_wh_tree_{key}")
        rows = getattr(self, f"_wh_rows_{key}", [])
        tree.delete(*tree.get_children())
        ql = (q or "").lower().strip()
        for art, fname, typ, is_selfbuy in rows:
            if ql and ql not in art.lower() and ql not in fname.lower():
                continue
            tree.insert("", "end", values=(art, fname, typ))

    def _print_wh_selected(self, key: str):
        tree: ttk.Treeview = getattr(self, f"_wh_tree_{key}")
        directory: str = getattr(self, f"_wh_dir_{key}")
        printer: str = getattr(self, f"_wh_prn_{key}")
        rows = getattr(self, f"_wh_rows_{key}", [])

        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Печать", "Выбери строку в списке.")
            return
        vals = tree.item(sel[0])["values"]
        if not vals:
            return
        art, fname, typ = vals
        is_selfbuy = (typ == "самовыкуп")
        warehouse_print_one(directory, printer, fname, is_selfbuy, art, self.log)
        # автообновление списка
        self._refresh_wh(key)

    # -------- Вкладка Склад --------
    def _build_screen_bind(self):
        fr = ttk.Frame(self.container)
        self.screens["bind"] = fr

        ttk.Label(fr, text="🏬 Склад (привязка товара к ячейкам)", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(fr, text="Цикл: 1) QR товара/материала/чернил/коробок → 2) QR ячейки", font=("Segoe UI", 9)).pack(anchor="w")

        st = ttk.Label(fr, text="Статус: ждём QR товара/материала/чернил/коробок", font=("Segoe UI", 10, "bold"))
        st.pack(anchor="w", pady=(10,6))
        self.bind_status = st

        row = ttk.Frame(fr)
        row.pack(fill="x", pady=6)
        ttk.Label(row, text="Ввод:").pack(side="left")
        self.bind_entry = ttk.Entry(row, font=("Consolas", 14))
        self.bind_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.bind_entry.bind("<Return>", lambda e: self._bind_accept())
        ttk.Button(row, text="Принять", command=self._bind_accept).pack(side="left")
        ttk.Button(row, text="Сброс", command=self._bind_reset).pack(side="left", padx=6)

    def _bind_accept(self):
        raw = _safe_strip_prefix(self.bind_entry.get())
        self.bind_entry.delete(0,"end")
        if not raw:
            return
        self.binder.accept_scan(raw, self.log)
        self.bind_status.configure(text="Статус: ждём QR ячейки" if self.binder.stage=="cell_qr" else "Статус: ждём QR товара/материала/чернил/коробок")

    def _bind_reset(self):
        self.binder.reset()
        self.bind_status.configure(text=("Статус: ждём QR ячейки" if self.binder.stage=="cell_qr" else "Статус: ждём QR товара/материала/чернил/коробок"))
        self.log("🔄 Привязка сброшена.")

    # -------- Вкладка Коробки --------

    def _build_screen_boxes(self):
        fr = ttk.Frame(self.container)
        self.screens["boxes"] = fr

        ttk.Label(fr, text="📦 Коробки", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(fr, text="Приемка пачек и списание по QR.", style="Muted.TLabel").pack(anchor="w")

        # --- Приемка ---
        add = ttk.LabelFrame(fr, text="➕ Приемка пачек коробок")
        add.pack(fill="x", pady=(10,8))
        ar = ttk.Frame(add); ar.pack(fill="x", padx=8, pady=8)

        ttk.Label(ar, text="Тип:").pack(side="left")
        self.box_add_type = tk.StringVar(value=(getattr(bot, "BOX_TYPES", ["короб"])[0]))
        self.box_add_cb = ttk.Combobox(ar, textvariable=self.box_add_type, state="readonly",
                                       values=list(getattr(bot, "BOX_TYPES", ["короб"])), width=24)
        self.box_add_cb.pack(side="left", padx=8)

        ttk.Label(ar, text="Пачек:").pack(side="left", padx=(10,4))
        self.box_add_cnt = ttk.Entry(ar, width=8)
        self.box_add_cnt.insert(0, "1")
        self.box_add_cnt.pack(side="left")

        ttk.Button(ar, text="Добавить + печать QR", command=self._boxes_add_and_print).pack(side="left", padx=10)

        # --- Списание по QR ---
        wd = ttk.LabelFrame(fr, text="➖ Списание по QR (1 пачка)")
        wd.pack(fill="x", pady=(0,8))
        row = ttk.Frame(wd)
        row.pack(fill="x", padx=8, pady=8)
        ttk.Label(row, text="QR:").pack(side="left")
        self.box_entry = ttk.Entry(row, font=("Consolas", 12))
        self.box_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.box_entry.bind("<Return>", lambda e: self._box_accept())
        ttk.Button(row, text="Списать 1 пачку", command=self._box_accept).pack(side="left", padx=(0,8))

        # --- Остатки склада ---
        stock = ttk.LabelFrame(fr, text="📊 Остатки на складе")
        stock.pack(fill="both", expand=True, pady=(0,8))
        self.box_stock_text = tk.Text(stock, height=10, font=("Consolas", 10))
        self.box_stock_text.pack(fill="both", expand=True, padx=8, pady=8)

        btns = ttk.Frame(fr)
        btns.pack(fill="x")
        ttk.Button(btns, text="🔄 Обновить остатки", command=self._boxes_refresh).pack(side="left")
        ttk.Button(btns, text="🗑️ Списать по QR", command=self._boxes_start_writeoff).pack(side="left", padx=8)

        self._boxes_writeoff_mode = False
        self._boxes_refresh()

    def _box_accept(self):

        raw = _safe_strip_prefix(self.box_entry.get())
        self.box_entry.delete(0,"end")
        if not raw:
            return
        boxes_writeoff_by_qr(raw, self.log)


    # -------- Вкладка --------
    def _boxes_add_and_print(self):
        """Оприходовать пачки коробок + напечатать QR-этикетки на каждую пачку.
        Это PC-функция, бот не трогаем: используем bot.boxes_add_packs + bot.print_box_label.
        """
        box_type = (self.box_add_type.get() or "").strip()
        if not box_type:
            messagebox.showinfo("Коробки", "Выберите тип коробок.")
            return
        try:
            cnt = int((self.box_add_cnt.get() or "0").strip())
        except Exception:
            cnt = 0
        if cnt <= 0:
            messagebox.showinfo("Коробки", "Укажи количество пачек (целое число > 0).")
            return

        def worker():
            try:
                try:
                    new_total = bot.boxes_add_packs(box_type, cnt)
                except Exception as e:
                    self.log(f"⛔ Ошибка оприходования коробок: {e}")
                    return

                printed = 0
                for i in range(cnt):
                    try:
                        ok = bot.print_box_label(box_type)
                        if ok:
                            printed += 1
                    except Exception as e:
                        self.log(f"⚠️ Печать коробок: ошибка на {i+1}/{cnt}: {e}")

                self.log(f"✅ Коробки оприходованы: «{box_type}» +{cnt} пач. Остаток: {new_total}. Напечатано этикеток: {printed}.")
            except Exception as e:
                self.log(f"⛔ Коробки: непредвиденная ошибка: {e}")

        threading.Thread(target=worker, daemon=True).start()



    def _boxes_refresh(self):
        """Обновить виджет остатков коробок."""
        try:
            summ = bot.boxes_summary()
        except Exception:
            summ = {}
        lines = []
        try:
            types = list(getattr(bot, "BOX_TYPES", []))
        except Exception:
            types = []
        seen = set()
        for bt in types:
            seen.add(bt)
            lines.append(f"{bt}: {int(summ.get(bt, 0) or 0)} пач.")
        for bt, n in sorted((summ or {}).items(), key=lambda x: str(x[0]).lower()):
            if bt in seen:
                continue
            lines.append(f"{bt}: {int(n or 0)} пач.")
        if not lines:
            lines = ["(пока пусто)"]
        if hasattr(self, "box_stock_text"):
            self.box_stock_text.delete("1.0", "end")
            self.box_stock_text.insert("end", "\n".join(lines))

    def _boxes_start_writeoff(self):
        """Включение режима: если включён — сканы коробок списывают 1 пачку по QR."""
        self._boxes_writeoff_mode = not getattr(self, "_boxes_writeoff_mode", False)
        if self._boxes_writeoff_mode:
            self.top_status.configure(text="📦 Коробки: СКАНИРУЙ QR коробок для списания")
            self.log("📦 Коробки: включён режим списания по QR.")
        else:
            self.top_status.configure(text="Готов к скану")
            self.log("📦 Коробки: режим списания выключен.")


    def _build_screen_material(self):
        fr = ttk.Frame(self.container)
        self.screens["material"] = fr

        ttk.Label(fr, text="🧵 Материал", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(fr, text="Приемка рулонов (печать QR), списание по полосам и списание по QR рулона.", style="Muted.TLabel").pack(anchor="w")

        # --- приемка материала ---
        add = ttk.LabelFrame(fr, text="➕ Приемка рулонов")
        add.pack(fill="x", pady=(10,8))

        row1 = ttk.Frame(add); row1.pack(fill="x", padx=8, pady=6)
        ttk.Label(row1, text="Тип:").pack(side="left")
        self.mat_type = tk.StringVar(value=(bot.MATERIAL_TYPES[0] if getattr(bot, "MATERIAL_TYPES", None) else "ОБОИ"))
        self.mat_type_cb = ttk.Combobox(row1, textvariable=self.mat_type, state="readonly",
                                        values=list(getattr(bot, "MATERIAL_TYPES", ["ФРЕСКА","холст","песок","ОБОИ","другое"])), width=22)
        self.mat_type_cb.pack(side="left", padx=8)

        ttk.Label(row1, text="Длина (м):").pack(side="left", padx=(12,4))
        self.mat_len = ttk.Entry(row1, width=12); self.mat_len.pack(side="left")
        ttk.Button(row1, text="Добавить + печать", command=self._mat_add_roll).pack(side="left", padx=10)

        # --- списание по полосам ---
        wd = ttk.LabelFrame(fr, text="➖ Списание по полосам (план)")
        wd.pack(fill="x", pady=(0,8))

        row2 = ttk.Frame(wd); row2.pack(fill="x", padx=8, pady=6)
        ttk.Label(row2, text="Тип:").pack(side="left")
        self.mat_wd_type = tk.StringVar(value=self.mat_type.get())
        self.mat_wd_type_cb = ttk.Combobox(row2, textvariable=self.mat_wd_type, state="readonly",
                                           values=list(getattr(bot, "MATERIAL_TYPES", ["ФРЕСКА","холст","песок","ОБОИ","другое"])), width=22)
        self.mat_wd_type_cb.pack(side="left", padx=8)

        ttk.Label(row2, text="Полос:").pack(side="left", padx=(12,4))
        self.mat_wd_cnt = ttk.Entry(row2, width=8); self.mat_wd_cnt.insert(0, "1"); self.mat_wd_cnt.pack(side="left")

        ttk.Label(row2, text="Длина 1 полосы (м):").pack(side="left", padx=(12,4))
        self.mat_wd_len = ttk.Entry(row2, width=10); self.mat_wd_len.insert(0, "2.83"); self.mat_wd_len.pack(side="left")

        ttk.Button(row2, text="Собрать план", command=self._mat_build_plan).pack(side="left", padx=10)
        ttk.Button(row2, text="✅ Подтвердить списание", command=self._mat_apply_plan).pack(side="left", padx=6)

        self.mat_plan_text = tk.Text(wd, height=6, font=("Consolas", 10))
        self.mat_plan_text.pack(fill="x", padx=8, pady=(0,8))

        # --- Остатки склада ---
        stock = ttk.LabelFrame(fr, text="📊 Остатки на складе")
        stock.pack(fill="both", expand=True, pady=(0,8))
        self.mat_stock_text = tk.Text(stock, height=10, font=("Consolas", 10))
        self.mat_stock_text.pack(fill="both", expand=True, padx=8, pady=8)

        btns = ttk.Frame(fr); btns.pack(fill="x")
        ttk.Button(btns, text="🔄 Обновить остатки", command=self._mat_refresh).pack(side="left")
        ttk.Button(btns, text="🗑️ Режим списания по QR", command=self._mat_start_writeoff).pack(side="left", padx=8)

        self._mat_writeoff_mode = False
        self._mat_refresh()

    def _mat_add_roll(self):

        mt = (self.mat_type.get() or "").strip()
        try:
            ln = float((self.mat_len.get() or "").replace(",", "."))
            if ln <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Материал", "Неверная длина. Пример: 27.5")
            return

        def work():
            try:
                import asyncio
                roll = asyncio.run(bot.mat_add_roll(mt, ln))
                ok = False
                try:
                    ok = asyncio.run(asyncio.to_thread(bot.print_material_label, roll))
                except Exception:
                    # если в боте нет print_material_label как coroutine wrapper
                    try:
                        ok = bool(bot.print_material_label(roll))
                    except Exception:
                        ok = False
                self.log(f"✅ Рулон добавлен: {mt}, {ln} м. Этикетка: {'OK' if ok else 'ошибка печати'}")
                self.log("➡️ Теперь привяжите рулон: «🏬 Склад» → QR материала → QR ячейки.")
            except Exception as e:
                self.log(f"❌ Ошибка добавления материала: {e}")

        threading.Thread(target=work, daemon=True).start()

    def _mat_build_plan(self):
        mt = (self.mat_wd_type.get() or "").strip()
        try:
            cnt = int((self.mat_wd_cnt.get() or "0").strip())
            if cnt <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Материал", "Полос должно быть целым числом > 0")
            return
        try:
            stripe_len = float((self.mat_wd_len.get() or "").replace(",", "."))
            if stripe_len <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Материал", "Длина полосы должна быть числом > 0")
            return

        def work():
            try:
                import asyncio
                rolls = asyncio.run(bot.mat_list())
                rolls = [r for r in rolls if (r.get("status") or "in_stock").lower() == "in_stock" and (r.get("mat_type") or "") == mt]
                if not rolls:
                    self.log(f"⚠️ Нет рулонов типа {mt} на складе.")
                    return
                plan, total_stripes, total_take_m = bot.plan_stripes_by_rolls(rolls, cnt, stripe_len)
                self._mat_plan_apply = [(rid, L) for (rid, _take, L, _cell, _rem) in plan]
                lines = []
                lines.append(f"План: {mt} — {cnt} пол. × {stripe_len:.3f} м")
                lines.append(f"Нарезать можно: {total_stripes} полос; к списанию рулонов: {total_take_m:g} м")
                lines.append("")
                for rid, take, L, cell, remainder in plan:
                    lines.append(f"• ID {rid}: рулон {L:g} м (ячейка {cell or '—'}) → полос {take}; остаток ~ {remainder:g} м (добавить как новый рулон)")
                self.mat_plan_text.delete("1.0", "end")
                self.mat_plan_text.insert("end", "\n".join(lines))
                self.log("✅ План сформирован. Нажмите «✅ Подтвердить списание» чтобы списать рулоны целиком.")
            except Exception as e:
                self.log(f"❌ Ошибка построения плана: {e}")

        threading.Thread(target=work, daemon=True).start()

    def _mat_apply_plan(self):
        if not self._mat_plan_apply:
            messagebox.showinfo("Материал", "Сначала соберите план.")
            return

        def work():
            try:
                import asyncio
                taken = asyncio.run(bot.mat_apply_withdraw(self._mat_plan_apply))
                # taken: [(id, use, cell)]
                self.log("✅ Списано (рулоны целиком):")
                for rid, use, cell in taken:
                    self.log(f"  • ID {rid}: {use} м (ячейка {cell or '—'})")
                self._mat_plan_apply = None
            except Exception as e:
                self.log(f"❌ Ошибка списания материала: {e}")

        threading.Thread(target=work, daemon=True).start()

    def _mat_refresh(self):
        """Показать остатки материалов (по типам и по рулонам)."""
        try:
            import asyncio
            rolls = asyncio.run(bot.mat_list())
        except Exception as e:
            self.log(f"⛔ Материал: не смог получить список рулонов: {e}")
            rolls = []
        in_stock = []
        for r in rolls or []:
            try:
                if (r.get("status") or "in_stock").lower() != "in_stock":
                    continue
            except Exception:
                continue
            in_stock.append(r)

        totals = {}
        for r in in_stock:
            mt = r.get("mat_type") or "?"
            try:
                ln = float(r.get("length_m") or 0)
            except Exception:
                ln = 0.0
            totals[mt] = totals.get(mt, 0.0) + ln

        lines = ["=== ИТОГО ПО ТИПАМ ==="]
        for mt in sorted(totals.keys(), key=lambda x: str(x).lower()):
            lines.append(f"{mt}: {totals[mt]:.2f} м")
        if len(lines) == 1:
            lines.append("(нет материалов на складе)")

        lines.append("")
        lines.append("=== РУЛОНЫ (in_stock) ===")
        for r in sorted(in_stock, key=lambda rr: (str(rr.get("mat_type") or ""), float(rr.get("length_m") or 0))):
            rid = r.get("id")
            mt = r.get("mat_type") or "?"
            cell = r.get("cell_qr") or "—"
            try:
                ln = float(r.get("length_m") or 0)
            except Exception:
                ln = 0.0
            lines.append(f"ID {rid}: {mt} {ln:.2f} м | ячейка: {cell}")

        if hasattr(self, "mat_stock_text"):
            self.mat_stock_text.delete("1.0", "end")
            self.mat_stock_text.insert("end", "\n".join(lines))

    def _mat_start_writeoff(self):
        """Включение режима: если включён — сканы QR материала списывает рулон целиком."""
        self._mat_writeoff_mode = not getattr(self, "_mat_writeoff_mode", False)
        if self._mat_writeoff_mode:
            self.top_status.configure(text="🧵 Материал: СКАНИРУЙ QR РУЛОНА для списания")
            self.log("🧵 Материал: включён режим списания по QR.")
        else:
            self.top_status.configure(text="Готов к скану")
            self.log("🧵 Материал: режим списания выключен.")

    def _mat_writeoff_by_qr(self, raw: str):
        """Списание рулона по QR (JSON kind=material, id=...). Списывает рулон целиком."""
        kind, data = _parse_json_kind(raw)
        if kind != "material" or not isinstance(data, dict) or "id" not in data:
            self.log("❌ Материал: это не QR материала (ожидался JSON kind=material).")
            return
        mid = str(data.get("id"))
        try:
            import asyncio
            rolls = asyncio.run(bot.mat_list())
            roll = next((r for r in (rolls or []) if str(r.get("id")) == mid), None)
            if not roll:
                self.log(f"⚠️ Материал: рулон ID {mid} не найден.")
                return
            if (roll.get("status") or "in_stock").lower() != "in_stock":
                self.log(f"⚠️ Материал: рулон ID {mid} уже не in_stock.")
                return
            ln = float(roll.get("length_m") or 0)
            if ln <= 0:
                self.log(f"⚠️ Материал: у рулона ID {mid} нулевая длина.")
                return
            asyncio.run(bot.mat_apply_withdraw([(mid, ln)]))
            self.log(f"✅ Материал: рулон ID {mid} списан ({ln:.2f} м).")
        except Exception as e:
            self.log(f"⛔ Материал: ошибка списания рулона: {e}")
        self._mat_refresh()

    # -------- Вкладка Чернила --------

    def _build_screen_ink(self):
        fr = ttk.Frame(self.container)
        self.screens["ink"] = fr

        ttk.Label(fr, text="🖋️ Чернила", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(fr, text="Оприходование: выбрать цвет → напечатать QR на упаковку → затем привязать к ячейке через «🏬 Склад».",
                  font=("Segoe UI", 9)).pack(anchor="w")

        add = ttk.LabelFrame(fr, text="➕ Приемка упаковок чернил")
        add.pack(fill="x", pady=(10,8))

        row = ttk.Frame(add)
        row.pack(fill="x", padx=8, pady=8)

        ttk.Label(row, text="Цвет:").pack(side="left")
        self.ink_color = tk.StringVar(value=INK_COLORS[0])
        self.ink_color_cb = ttk.Combobox(row, textvariable=self.ink_color, state="readonly", values=INK_COLORS, width=16)
        self.ink_color_cb.pack(side="left", padx=8)

        ttk.Label(row, text="Кол-во упаковок:").pack(side="left", padx=(12,4))
        self.ink_cnt = ttk.Entry(row, width=8)
        self.ink_cnt.insert(0, "1")
        self.ink_cnt.pack(side="left")

        ttk.Button(row, text="Добавить + печать QR", command=self._ink_add_and_print).pack(side="left", padx=10)

        ttk.Label(add, text="После печати: «🏬 Склад» → скан QR чернил → QR ячейки.",
                  font=("Segoe UI", 9)).pack(anchor="w", padx=8, pady=(0,8))

        stock = ttk.LabelFrame(fr, text="📊 Остатки на складе")
        stock.pack(fill="both", expand=True, pady=(0,8))

        self.ink_stock_text = tk.Text(stock, height=12, font=("Consolas", 10))
        self.ink_stock_text.pack(fill="both", expand=True, padx=8, pady=8)

        btns = ttk.Frame(fr)
        btns.pack(fill="x")
        ttk.Button(btns, text="🔄 Обновить остатки", command=self._ink_refresh).pack(side="left")
        ttk.Button(btns, text="🗑️ Списать по QR", command=lambda: self._ink_start_writeoff()).pack(side="left", padx=8)

        self._ink_writeoff_mode = False
        self._ink_refresh()

    def _ink_refresh(self):
        summ = inks_summary()
        lines = ["Остатки чернил (упаковки):"]
        for c in INK_COLORS:
            lines.append(f"• {c}: {summ.get(c, 0)}")
        self.ink_stock_text.delete("1.0", "end")
        self.ink_stock_text.insert("end", "\n".join(lines))

    def _ink_add_and_print(self):
        color = (self.ink_color.get() or "").strip()
        try:
            cnt = int((self.ink_cnt.get() or "0").strip())
            if cnt <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Чернила", "Кол-во должно быть целым числом > 0")
            return

        def work():
            try:
                packs = inks_add_packs(color, cnt)
                ok = 0
                for p in packs:
                    if print_ink_label(p):
                        ok += 1
                self.log(f"✅ Чернила оприходованы: {color} ×{cnt}. Этикеток напечатано: {ok}.")
                self.log("➡️ Теперь привяжите упаковку: «🏬 Склад» → скан QR чернил → QR ячейки.")
                self._ink_refresh()
            except Exception as e:
                self.log(f"❌ Ошибка оприходования чернил: {e}")

        threading.Thread(target=work, daemon=True).start()

    def _ink_start_writeoff(self):
        self._ink_writeoff_mode = True
        messagebox.showinfo("Чернила", "Режим списания чернил включен.\nСканируйте QR  чернил в любом месте — будет списана 1 упаковка.")

    def _ink_try_writeoff(self, raw: str) -> bool:
        kind, data = _parse_json_kind(raw)
        if kind != "ink" or not isinstance(data, dict) or "id" not in data:
            return False
        pid = str(data.get("id"))
        res = inks_mark_used(pid)
        if res == "ok":
            self.log(f"✅ Чернила ID {pid} списаны (used).")
        elif res == "already":
            self.log(f"⚠️ Чернила ID {pid} уже списаны ранее.")
        else:
            self.log(f"❌ Чернила ID {pid} не найдены в базе.")
        self._ink_refresh()
        return True

    # -------- Вкладка Настройки --------
    def _build_screen_settings(self):
        fr = ttk.Frame(self.container)
        self.screens["settings"] = fr

        ttk.Label(fr, text="⚙️ Настройки", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        ttk.Label(fr, text="Настройки локального ПО", style="Muted.TLabel").pack(anchor="w")

        # Темы
        box_theme = ttk.LabelFrame(fr, text="Вид")
        box_theme.pack(fill="x", pady=(10,8))
        row = ttk.Frame(box_theme); row.pack(fill="x", padx=8, pady=8)
        ttk.Label(row, text="Тема:").pack(side="left")
        self.set_theme = tk.StringVar(value=SET.get("theme","dark"))
        ttk.Radiobutton(row, text="Тёмная", value="dark", variable=self.set_theme).pack(side="left", padx=8)
        ttk.Radiobutton(row, text="Светлая", value="light", variable=self.set_theme).pack(side="left", padx=8)

        # Порты, принтеры и тп
        box_conn = ttk.LabelFrame(fr, text="Виртуальные порты и принтеры")
        box_conn.pack(fill="x", pady=(0,8))
        r2 = ttk.Frame(box_conn); r2.pack(fill="x", padx=8, pady=8)
        ttk.Label(r2, text="COM порт:").pack(side="left")
        self.set_com_port = ttk.Entry(r2, width=10)
        self.set_com_port.insert(0, SET.get("com_port","COM3"))
        self.set_com_port.pack(side="left", padx=8)

        ttk.Label(r2, text="Baudrate:").pack(side="left", padx=(10,4))
        self.set_baud = ttk.Entry(r2, width=10)
        self.set_baud.insert(0, str(SET.get("baudrate",115200)))
        self.set_baud.pack(side="left", padx=8)

        ttk.Label(r2, text="Принтер этикеток:").pack(side="left", padx=(10,4))
        self.set_prn_market = ttk.Entry(r2, width=16)
        self.set_prn_market.insert(0, SET["printers"].get("market","wb"))
        self.set_prn_market.pack(side="left", padx=8)

        # Папки
        box_paths = ttk.LabelFrame(fr, text="Папки этикеток")
        box_paths.pack(fill="x", pady=(0,8))

        self._path_entries = {}
        def add_path_row(lbl, key):
            rr = ttk.Frame(box_paths); rr.pack(fill="x", padx=8, pady=6)
            ttk.Label(rr, text=lbl, width=14).pack(side="left")
            e = ttk.Entry(rr)
            e.pack(side="left", fill="x", expand=True, padx=8)
            e.insert(0, SET["paths"].get(key,""))
            ttk.Button(rr, text="…", width=3, command=lambda: self._pick_dir(e)).pack(side="left")
            self._path_entries[key] = e

        add_path_row("FBO", "FBO")
        add_path_row("WB", "WB")
        add_path_row("OZON", "OZON")

        btn = ttk.Frame(fr); btn.pack(fill="x", pady=(6,0))
        ttk.Button(btn, text="💾 Сохранить", style="Accent.TButton", command=self._save_settings).pack(side="left")
        ttk.Button(btn, text="Применить тему", command=self._apply_theme_only).pack(side="left", padx=8)

    def _pick_dir(self, entry: ttk.Entry):
        p = filedialog.askdirectory()
        if p:
            entry.delete(0,"end"); entry.insert(0,p)

    def _apply_theme_only(self):
        SET["theme"] = self.set_theme.get()
        apply_theme_ttk(self, SET["theme"])

    def _save_settings(self):

        SET["theme"] = self.set_theme.get()

        SET["com_port"] = (self.set_com_port.get() or "").strip()
        try:
            SET["baudrate"] = int((self.set_baud.get() or "115200").strip())
        except Exception:
            SET["baudrate"] = 115200

        SET["printers"]["market"] = (self.set_prn_market.get() or "wb").strip()


        for k, e in self._path_entries.items():
            SET["paths"][k] = (e.get() or "").strip()

        global FBO_PATH
        FBO_PATH = SET["paths"]["FBO"]
        try:
            setattr(bot, "WB_PATH", SET["paths"]["WB"])
            setattr(bot, "OZON_PATH", SET["paths"]["OZON"])
        except Exception:
            pass

        save_settings(SET)
        self._apply_theme_only()
        self._refresh_ports()
        try:
            self.status_bar.configure(text=f"Версия: {APP_VERSION}  •  Настройки сохранены")
        except Exception:
            pass
        self.log("✅ Настройки сохранены.")

    # -------- Вкладка Инструкция --------
    def _build_screen_help(self):
        fr = ttk.Frame(self.container)
        self.screens["help"] = fr

        ttk.Label(fr, text="📘 Инструкция", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0,8))
        t = tk.Text(fr, font=("Segoe UI", 11), wrap="word")
        t.pack(fill="both", expand=True)

        t.insert("1.0", f"""📘 ИНСТРУКЦИЯ (Scanner {APP_VERSION})

Главное

Работаем СКАНЕРОМ, а не кнопками

1 скан = 1 действие

Что происходит — всегда видно в логе

📸 Сканер (основная работа)

Печать макетов
Отсканируй UID или штрихкод макета (пример: 5654-1)
Этикетка напечатается автоматически
Печать со склада
Отсканируй складскую наклейку типа:

ЛОФ_04_312x270 | 5454
                 
Программа сама найдёт и напечатает этикетку WB/OZON
Выбор складов не нужен

🧵 Материал
                 
Приемка рулонов
Нажми «Оприходовать рулон»
Выбери тип и длину → наклей QR
Привязать к ячейке
«Склад» → QR рулона → QR ячейки
Списать
«Списать по QR (режим)» → скан QR рулона

📦 Коробки

Приемка
«Добавить + печать QR»
Выбери тип и количество → наклей QR
Списать
«Списать по QR (режим)»
Скан QR пачки = −1 пачка

🖋️ Чернила

Приемка
Выбери цвет → количество → наклей QR
Привязать / списать
Привязка: «Склад» → QR → QR ячейки
Списание: «Списать по QR» → QR упаковки

🏬 Склад (привязка)

Скан предмета → скан ячейки
Работает для материала, коробок и чернил

⚙️ Настройки
Сканер, принтеры, папки, тема
""")
        t.configure(state="disabled")


    # -------- Порты --------
    def _refresh_ports(self):
        ports = []
        if serial is not None:
            try:
                ports = [p.device for p in serial.tools.list_ports.comports()]
            except Exception:
                ports = []
        self.com_ports["values"] = ports
        if ports and not self.com_ports.get():
            pref = (SET.get("com_port") or "").strip()
            if pref and pref in ports:
                self.com_ports.set(pref)
            elif "COM3" in ports:
                self.com_ports.set("COM3")
            else:
                self.com_ports.set(ports[0])

    def _toggle_com(self):
        if self._com_thread and self._com_thread.is_alive():
            self._com_stop.set()
            self.btn_com.configure(text="▶ Старт COM")
            self.com_status.configure(text="статус: остановлен")
            return

        if serial is None:
            messagebox.showerror("COM", "Не установлен pyserial. Установи: pip install pyserial")
            return

        port = (self.com_ports.get() or "").strip()
        if not port:
            messagebox.showinfo("COM", "Выбери COM-порт.")
            return

        self._com_stop.clear()
        self.btn_com.configure(text="■ Стоп COM")
        self.com_status.configure(text=f"статус: синхронизированно {port}")

        def loop():
            buf = ""
            try:
                baud = int(SET.get("baudrate",115200) or 115200)
                with serial.Serial(port, baudrate=baud, timeout=0.3) as ser:
                    while not self._com_stop.is_set():
                        data = ser.read(256)
                        if not data:
                            continue
                        txt = _decode_com_bytes(data)
                        if not txt:
                            continue
                        buf += txt
                        while True:
                            m = re.search(r"[\r\n]", buf)
                            if not m:
                                break
                            line = buf[:m.start()].strip()
                            buf = buf[m.end():]
                            if not line:
                                continue
                            line = _safe_strip_prefix(line)
                            if not self._should_process(line):
                                continue
                            self.log(f"📥 Scanner: {line}")

                            # Роутинг как "точь-в-точь по смыслу":
                            # - если открыт экран привязки — отдаём туда
                            # - если открыт экран коробок и это kind=box — списываем
                            # - иначе — обычный скан/печать
                            current = None
                            for k, fr in self.screens.items():
                                if fr.winfo_ismapped():
                                    current = k
                                    break

                            if current == "bind":
                                self.binder.accept_scan(line, self.log)
                                self.after(0, lambda: self.bind_status.configure(
                                    text="Статус: ждём QR ячейки" if self.binder.stage=="cell_qr" else "Статус: ждём QR товара/материала/чернил/коробок"
                                ))
                                continue

                            # режим списания чернил: если включен — списываем по QR kind=ink
                            if getattr(self, "_ink_writeoff_mode", False):
                                if self._ink_try_writeoff(line):
                                    continue

                            
                            # режим списания коробок (COM): если включен и мы на вкладке «Коробки», списываем по QR kind=box
                            if current == "boxes" and getattr(self, "_boxes_writeoff_mode", False):
                                kind2, _d2 = _parse_json_kind(line)
                                if kind2 == "box":
                                    boxes_writeoff_by_qr(line, self.log)
                                    try:
                                        self._boxes_refresh()
                                    except Exception:
                                        pass
                                    continue

                            # режим списания материала (COM): если включен и мы на вкладке «Материал», списываем рулон по QR kind=material
                            if current == "material" and getattr(self, "_mat_writeoff_mode", False):
                                kind3, _d3 = _parse_json_kind(line)
                                if kind3 == "material":
                                    try:
                                        self._mat_writeoff_by_qr(line)
                                    except Exception as e:
                                        self.log(f"⛔ Материал: ошибка списания по QR: {e}")
                                    continue

                            kind, _ = _parse_json_kind(line)
                            if kind == "box":
                                boxes_writeoff_by_qr(line, self.log)
                                continue

                            # дефолт: сначала пробуем складской SKU (расход/самовыкуп) без выбора складов
                            sku, uid = _split_sku_uid(line)
                            if sku and warehouse_try_print_by_sku(sku, self.log):
                                continue

                            # иначе — обычная печать (макеты/FBO/маркет)
                            res = print_by_scan(uid or line, self.log)
                            if isinstance(res, tuple) and res and res[0] == "need_pick":
                                # показать выбор на UI
                                _, paths, prn = res
                                def show_pick():
                                    self._show("scan")
                                    self._pick_paths = paths
                                    self._pick_printer = prn
                                    self.pick_list.delete(0,"end")
                                    for p in paths[:200]:
                                        self.pick_list.insert("end", os.path.basename(p))
                                    self.pick_frame.pack(fill="both", expand=False, pady=(10,0))
                                self.after(0, show_pick)

            except Exception as e:
                self.log(f"⛔ COM ошибка: {e}")
            finally:
                self.after(0, lambda: self.btn_com.configure(text="▶ Старт COM"))
                self.after(0, lambda: self.com_status.configure(text="статус: остановлен"))

        self._com_thread = threading.Thread(target=loop, daemon=True)
        self._com_thread.start()


if __name__ == "__main__":
    App().mainloop()
