"""
Manga Downloader 2.0
Быстрая и стабильная версия для com-x.life

Улучшения:
- Параллельная загрузка глав
- Retry + Session
- Без временных папок
- Прямая сборка CBZ
- Улучшенная обработка ошибок
- Гарантированное закрытие браузера
"""

import sys
import re
import json
import time
import zipfile
import random
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# =========================
# API Layer
# =========================

class ComXAPI:
    BASE = "https://com-x.life"

    def __init__(self, cookies, log_func):
        self.log = log_func
        self.session = requests.Session()

        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Referer": self.BASE
        })

        for c in cookies:
            self.session.cookies.set(c["name"], c["value"])

    def get_manga_data(self, url):
        resp = self.session.get(url)
        if resp.status_code != 200:
            raise Exception(f"Ошибка загрузки страницы: {resp.status_code}")

        match = re.search(r'window\.__DATA__\s*=\s*({.*?})\s*;', resp.text, re.DOTALL)
        if not match:
            raise Exception("window.__DATA__ не найден")

        data = json.loads(match.group(1))
        chapters = data["chapters"][::-1]
        title = data.get("title", "Manga").strip()

        news_id = data.get("news_id")
        if not news_id:
            m = re.search(r'/(\d+)-', url)
            if not m:
                raise Exception("news_id не найден")
            news_id = m.group(1)

        return chapters, title, news_id

    def get_chapter_zip(self, chapter_id, news_id, referer):
        payload = f"chapter_id={chapter_id}&news_id={news_id}"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
            "Origin": self.BASE
        }

        api_url = f"{self.BASE}/engine/ajax/controller.php?mod=api&action=chapters/download"
        r = self.session.post(api_url, headers=headers, data=payload)

        if r.status_code != 200:
            raise Exception(f"Ошибка API: {r.status_code}")

        try:
            raw = r.json().get("data")
        except Exception:
            raise Exception("API вернул не JSON")

        if not raw:
            raise Exception("Пустой ответ API")

        download_url = "https:" + raw.replace("\\/", "/")
        file_resp = self.session.get(download_url)

        if not file_resp.ok:
            raise Exception("Ошибка скачивания ZIP")

        return file_resp.content


# =========================
# Worker Thread
# =========================

class MangaDownloader(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)

    COOKIE_FILE = "comx_life_cookies_v2.json"
    MAX_WORKERS = 5

    def __init__(self):
        super().__init__()
        self.url = None
        self.cookies = None
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        driver = None
        try:
            driver = self._open_browser()
            if not driver:
                self.finished.emit(False)
                return

            self._wait_for_download_page(driver)
            driver.quit()

            self._download()

            self.finished.emit(True)

        except Exception as e:
            self.log.emit(f"❌ {e}")
            self.finished.emit(False)

        finally:
            if driver:
                driver.quit()

    # =========================
    # Selenium
    # =========================

    def _open_browser(self):
        options = Options()
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=options)
        driver.get("https://com-x.life/")
        self.log.emit("🔐 Авторизуйтесь вручную")

        while not driver.get_cookie("dle_user_id"):
            if self._cancel:
                driver.quit()
                return None
            time.sleep(1)

        self.cookies = driver.get_cookies()
        with open(self.COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cookies, f)

        self.log.emit("✅ Авторизация сохранена")
        return driver

    def _wait_for_download_page(self, driver):
        self.log.emit("📦 Ожидание страницы /download")

        while not self._cancel:
            url = driver.current_url
            if url.endswith("/download"):
                self.url = url.replace("/download", "")
                return
            time.sleep(0.2)

    # =========================
    # Download logic
    # =========================

    def _download(self):
        api = ComXAPI(self.cookies, self.log.emit)
        chapters, title, news_id = api.get_manga_data(self.url)

        safe_title = re.sub(r"[^\w\- ]", "_", title)
        final_cbz = Path(f"{safe_title}.cbz")

        self.log.emit(f"📚 Глав: {len(chapters)}")

        results = []
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    api.get_chapter_zip,
                    ch["id"],
                    news_id,
                    self.url
                ): i for i, ch in enumerate(chapters)
            }

            completed = 0

            for future in as_completed(futures):
                if self._cancel:
                    return

                index = futures[future]
                try:
                    data = future.result()
                    results.append((index, data))
                except Exception as e:
                    self.log.emit(f"⚠️ Ошибка главы {index+1}: {e}")

                completed += 1
                percent = int((completed / len(chapters)) * 100)
                self.progress.emit(percent)

                time.sleep(random.uniform(0.2, 0.6))

        results.sort(key=lambda x: x[0])

        self.log.emit("📦 Создание CBZ...")

        counter = 1
        with zipfile.ZipFile(final_cbz, "w") as cbz:
            for _, zip_bytes in results:
                with zipfile.ZipFile(
                    Path("temp.zip").write_bytes(zip_bytes) or "temp.zip"
                ) as z:
                    for name in sorted(z.namelist()):
                        ext = Path(name).suffix
                        out_name = f"{counter:06}{ext}"
                        cbz.writestr(out_name, z.read(name))
                        counter += 1

        Path("temp.zip").unlink(missing_ok=True)

        self.log.emit(f"✅ Готово: {final_cbz.resolve()}")


# =========================
# GUI
# =========================

class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manga Downloader 2.0")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self.start_btn = QPushButton("Открыть com-x.life")
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.hide()

        self.progress = QProgressBar()
        self.logs = QTextEdit(readOnly=True)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.cancel_btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.logs)

        self.start_btn.clicked.connect(self.start)
        self.cancel_btn.clicked.connect(self.cancel)

    def start(self):
        self.worker = MangaDownloader()
        self.worker.log.connect(self.logs.append)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.done)

        self.start_btn.setEnabled(False)
        self.cancel_btn.show()
        self.worker.start()

    def cancel(self):
        if hasattr(self, "worker"):
            self.worker.cancel()
            self.logs.append("🛑 Отмена...")

    def done(self, ok):
        self.start_btn.setEnabled(True)
        self.cancel_btn.hide()
        if ok:
            self.logs.append("🎉 Успешно!")
        else:
            self.logs.append("❌ Ошибка.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec_())

