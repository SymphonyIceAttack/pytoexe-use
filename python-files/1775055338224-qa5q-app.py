"""
PDF Processor — Desktop App
Обработка PDF через Docling + авто-заголовок через Claude API
SQLite база данных + CSV экспорт
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import sqlite3
import os
import csv
import json
import datetime
import anthropic
from pathlib import Path

# ── Docling импорт (с fallback если не установлен) ──────────────────────────
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# ── Настройка темы ───────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DB_PATH = os.path.join(os.path.expanduser("~"), "pdf_processor.db")


# ── База данных ──────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filepath TEXT,
            suggested_title TEXT,
            extracted_text TEXT,
            page_count INTEGER,
            processed_at TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_to_db(filename, filepath, title, text, pages, status="ok"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO documents (filename, filepath, suggested_title, extracted_text, page_count, processed_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (filename, filepath, title, text[:5000], pages,
          datetime.datetime.now().isoformat(), status))
    conn.commit()
    conn.close()


def load_all_records():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, suggested_title, page_count, processed_at, status FROM documents ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def export_csv(path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, filepath, suggested_title, page_count, processed_at, status FROM documents")
    rows = c.fetchall()
    conn.close()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Файл", "Путь", "Заголовок", "Страниц", "Обработан", "Статус"])
        writer.writerows(rows)


# ── ИИ заголовок ─────────────────────────────────────────────────────────────
def get_ai_title(text: str, api_key: str) -> str:
    """Запрашивает Claude предложить заголовок по тексту документа."""
    if not api_key or not text.strip():
        # Fallback: первые значимые слова
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
        return lines[0][:80] if lines else "Без названия"
    try:
        client = anthropic.Anthropic(api_key=api_key)
        snippet = text[:1500]
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": f"Предложи краткий информативный заголовок (до 10 слов) для этого документа. Ответь ТОЛЬКО заголовком, без пояснений.\n\nТекст:\n{snippet}"
            }]
        )
        return msg.content[0].text.strip().strip('"').strip("'")
    except Exception as e:
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
        return lines[0][:80] if lines else "Без названия"


# ── Обработка PDF ─────────────────────────────────────────────────────────────
def process_pdf(filepath: str, api_key: str) -> dict:
    filename = os.path.basename(filepath)
    try:
        if DOCLING_AVAILABLE:
            converter = DocumentConverter()
            result = converter.convert(filepath)
            text = result.document.export_to_markdown()
            pages = getattr(result.document, 'num_pages', 1) or 1
        else:
            # Fallback: PyMuPDF если есть
            try:
                import fitz
                doc = fitz.open(filepath)
                text = "\n".join(page.get_text() for page in doc)
                pages = doc.page_count
                doc.close()
            except ImportError:
                text = f"[Docling не установлен. Установите: pip install docling]\nФайл: {filepath}"
                pages = 0

        title = get_ai_title(text, api_key)
        save_to_db(filename, filepath, title, text, pages, "ok")
        return {"status": "ok", "filename": filename, "title": title, "pages": pages}
    except Exception as e:
        save_to_db(filename, filepath, "Ошибка обработки", str(e), 0, "error")
        return {"status": "error", "filename": filename, "error": str(e)}


# ── Главное окно ──────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        init_db()

        self.title("PDF Processor  ·  Docling + Claude AI")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color="#0f1117")

        self._build_ui()
        self._refresh_table()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Заголовок
        header = ctk.CTkFrame(self, fg_color="#161b27", corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⬡  PDF Processor",
                     font=ctk.CTkFont("Courier New", 22, "bold"),
                     text_color="#4fc3f7").pack(side="left", padx=24, pady=16)
        ctk.CTkLabel(header, text="Docling · Claude AI · SQLite",
                     font=ctk.CTkFont("Courier New", 11),
                     text_color="#4a5568").pack(side="left", padx=4)

        # Основной контейнер
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=16)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # ── Левая панель ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(main, fg_color="#161b27", corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(left, text="НАСТРОЙКИ", font=ctk.CTkFont("Courier New", 10, "bold"),
                     text_color="#4a5568").pack(anchor="w", padx=20, pady=(20, 4))

        # API ключ
        ctk.CTkLabel(left, text="Claude API Key",
                     font=ctk.CTkFont(size=12), text_color="#a0aec0").pack(anchor="w", padx=20)
        self.api_key_var = ctk.StringVar(value=os.environ.get("ANTHROPIC_API_KEY", ""))
        api_entry = ctk.CTkEntry(left, textvariable=self.api_key_var,
                                  show="•", placeholder_text="sk-ant-...",
                                  fg_color="#0f1117", border_color="#2d3748",
                                  font=ctk.CTkFont("Courier New", 11))
        api_entry.pack(fill="x", padx=20, pady=(4, 16))

        ctk.CTkLabel(left, text="ИСТОЧНИК ФАЙЛОВ", font=ctk.CTkFont("Courier New", 10, "bold"),
                     text_color="#4a5568").pack(anchor="w", padx=20, pady=(8, 4))

        # Кнопка выбора файлов
        self.btn_files = ctk.CTkButton(
            left, text="📄  Выбрать PDF-файлы",
            fg_color="#1a2744", hover_color="#1e3a5f",
            border_color="#2b4c7e", border_width=1,
            font=ctk.CTkFont(size=13),
            command=self._pick_files)
        self.btn_files.pack(fill="x", padx=20, pady=4)

        # Кнопка выбора папки
        self.btn_folder = ctk.CTkButton(
            left, text="📁  Выбрать папку",
            fg_color="#1a2744", hover_color="#1e3a5f",
            border_color="#2b4c7e", border_width=1,
            font=ctk.CTkFont(size=13),
            command=self._pick_folder)
        self.btn_folder.pack(fill="x", padx=20, pady=4)

        # Список выбранных файлов
        ctk.CTkLabel(left, text="Выбрано файлов:", font=ctk.CTkFont(size=11),
                     text_color="#718096").pack(anchor="w", padx=20, pady=(12, 2))
        self.files_box = ctk.CTkTextbox(left, height=140, fg_color="#0f1117",
                                         border_color="#2d3748",
                                         font=ctk.CTkFont("Courier New", 10),
                                         text_color="#68d391")
        self.files_box.pack(fill="x", padx=20)
        self.selected_files = []

        # Кнопка запуска
        self.btn_run = ctk.CTkButton(
            left, text="▶  Запустить обработку",
            fg_color="#0e4f2f", hover_color="#0a6b3c",
            border_color="#38a169", border_width=1,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            command=self._start_processing)
        self.btn_run.pack(fill="x", padx=20, pady=(16, 8))

        # Прогресс
        self.progress = ctk.CTkProgressBar(left, fg_color="#1a1f2e",
                                            progress_color="#38a169")
        self.progress.set(0)
        self.progress.pack(fill="x", padx=20, pady=4)

        self.status_label = ctk.CTkLabel(left, text="Готов к работе",
                                          font=ctk.CTkFont("Courier New", 10),
                                          text_color="#4a5568")
        self.status_label.pack(anchor="w", padx=20, pady=4)

        # Экспорт
        ctk.CTkLabel(left, text="ЭКСПОРТ", font=ctk.CTkFont("Courier New", 10, "bold"),
                     text_color="#4a5568").pack(anchor="w", padx=20, pady=(16, 4))

        self.btn_csv = ctk.CTkButton(
            left, text="💾  Экспорт в CSV",
            fg_color="#2d1b4e", hover_color="#3d2560",
            border_color="#553c9a", border_width=1,
            font=ctk.CTkFont(size=13),
            command=self._export_csv)
        self.btn_csv.pack(fill="x", padx=20, pady=4)

        self.btn_clear = ctk.CTkButton(
            left, text="🗑  Очистить базу",
            fg_color="#2d1515", hover_color="#3d1a1a",
            border_color="#742a2a", border_width=1,
            font=ctk.CTkFont(size=12),
            command=self._clear_db)
        self.btn_clear.pack(fill="x", padx=20, pady=(4, 20))

        # ── Правая панель ─────────────────────────────────────────────────────
        right = ctk.CTkFrame(main, fg_color="#161b27", corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew")

        top_bar = ctk.CTkFrame(right, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(top_bar, text="БАЗА ДАННЫХ",
                     font=ctk.CTkFont("Courier New", 10, "bold"),
                     text_color="#4a5568").pack(side="left")
        self.count_label = ctk.CTkLabel(top_bar, text="",
                                         font=ctk.CTkFont("Courier New", 10),
                                         text_color="#4fc3f7")
        self.count_label.pack(side="right")

        # Таблица (через текстовое поле с форматированием)
        cols_frame = ctk.CTkFrame(right, fg_color="#0f1117", corner_radius=6)
        cols_frame.pack(fill="x", padx=20)
        for col, w in [("ID", 40), ("Файл", 200), ("Заголовок AI", 280), ("Стр.", 50), ("Дата", 140), ("Статус", 70)]:
            ctk.CTkLabel(cols_frame, text=col,
                         font=ctk.CTkFont("Courier New", 10, "bold"),
                         text_color="#4fc3f7", width=w, anchor="w").pack(side="left", padx=4, pady=6)

        self.table = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.table.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        # Превью текста
        ctk.CTkLabel(right, text="ПРЕДПРОСМОТР ТЕКСТА",
                     font=ctk.CTkFont("Courier New", 10, "bold"),
                     text_color="#4a5568").pack(anchor="w", padx=20)
        self.preview = ctk.CTkTextbox(right, height=140, fg_color="#0f1117",
                                       border_color="#2d3748",
                                       font=ctk.CTkFont("Courier New", 10),
                                       text_color="#a0aec0")
        self.preview.pack(fill="x", padx=20, pady=(4, 20))

    # ── Выбор файлов ─────────────────────────────────────────────────────────
    def _pick_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        if files:
            self.selected_files = list(files)
            self._update_files_box()

    def _pick_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_files = [
                str(p) for p in Path(folder).rglob("*.pdf")
            ]
            self._update_files_box()

    def _update_files_box(self):
        self.files_box.delete("1.0", "end")
        for f in self.selected_files:
            self.files_box.insert("end", os.path.basename(f) + "\n")
        self.status_label.configure(text=f"Выбрано: {len(self.selected_files)} файлов")

    # ── Обработка ─────────────────────────────────────────────────────────────
    def _start_processing(self):
        if not self.selected_files:
            messagebox.showwarning("Нет файлов", "Выберите PDF-файлы или папку.")
            return
        self.btn_run.configure(state="disabled", text="⏳  Обрабатываю...")
        threading.Thread(target=self._run_processing, daemon=True).start()

    def _run_processing(self):
        total = len(self.selected_files)
        api_key = self.api_key_var.get().strip()
        for i, fp in enumerate(self.selected_files):
            self.after(0, self.status_label.configure,
                       {"text": f"[{i+1}/{total}] {os.path.basename(fp)}"})
            self.after(0, self.progress.set, (i + 0.5) / total)
            result = process_pdf(fp, api_key)
            self.after(0, self.progress.set, (i + 1) / total)

        self.after(0, self._on_done)

    def _on_done(self):
        self.btn_run.configure(state="normal", text="▶  Запустить обработку")
        self.progress.set(1.0)
        self.status_label.configure(text="✅  Готово!")
        self._refresh_table()

    # ── Таблица ───────────────────────────────────────────────────────────────
    def _refresh_table(self):
        for w in self.table.winfo_children():
            w.destroy()

        rows = load_all_records()
        self.count_label.configure(text=f"{len(rows)} записей")

        for row in rows:
            rid, fname, title, pages, date, status = row
            color = "#68d391" if status == "ok" else "#fc8181"
            date_short = date[:16] if date else ""

            frame = ctk.CTkFrame(self.table, fg_color="#1a1f2e", corner_radius=6)
            frame.pack(fill="x", pady=2)
            frame.bind("<Button-1>", lambda e, r=row: self._show_preview(r))

            for val, w in [(str(rid), 40), (fname[:28], 200),
                            (title[:40] if title else "", 280),
                            (str(pages or ""), 50), (date_short, 140), (status, 70)]:
                lbl = ctk.CTkLabel(frame, text=val,
                                    font=ctk.CTkFont("Courier New", 10),
                                    text_color=color if val == status else "#cbd5e0",
                                    width=w, anchor="w")
                lbl.pack(side="left", padx=4, pady=5)
                lbl.bind("<Button-1>", lambda e, r=row: self._show_preview(r))

    def _show_preview(self, row):
        rid = row[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT filename, suggested_title, extracted_text FROM documents WHERE id=?", (rid,))
        rec = c.fetchone()
        conn.close()
        if rec:
            fname, title, text = rec
            self.preview.delete("1.0", "end")
            self.preview.insert("end", f"📄 {fname}\n🏷  {title}\n\n{text or ''}")

    # ── Экспорт / очистка ─────────────────────────────────────────────────────
    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV", "*.csv")],
                                             initialfile="pdf_database.csv")
        if path:
            export_csv(path)
            messagebox.showinfo("Готово", f"CSV сохранён:\n{path}")

    def _clear_db(self):
        if messagebox.askyesno("Очистить базу?", "Удалить все записи из базы данных?"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM documents")
            conn.commit()
            conn.close()
            self._refresh_table()
            self.status_label.configure(text="База очищена")


if __name__ == "__main__":
    app = App()
    app.mainloop()
