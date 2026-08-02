import sys
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
import math
import time

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QMessageBox, QDialog, QListWidget, QLabel,
    QFileDialog, QCheckBox, QTextEdit
)
from PySide6.QtWebEngineWidgets import QWebEngineView

# ==============================================================================
# 🔍 NATIVE NO-AI SEARCH ENGINE ENGINE ("Crust Search Engine")
# ==============================================================================

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.text_parts = []
        self.in_title = False
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'title':
            self.in_title = True
        elif tag.lower() in ['script', 'style']:
            self.in_script = True

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False
        elif tag.lower() in ['script', 'style']:
            self.in_script = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.in_script:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

class CrustSearchEngine:
    """An independent full-text indexing search engine (No Google, No AI)."""
    def __init__(self):
        self.index = {}  # token -> {url: score}
        self.docs = {}   # url -> {title, snippet, domain}
        self.seed_default_index()

    def seed_default_index(self):
        """Pre-populate the search index with non-AI web links."""
        seeds = [
            {
                "url": "https://en.wikipedia.org/wiki/Pie",
                "title": "Pie - Wikipedia Encyclopedia",
                "snippet": "A pie is a baked dish which is usually made of a pastry dough casing that contains a filling of various sweet or savoury ingredients.",
                "tokens": ["pie", "pastry", "baked", "filling", "crust", "cooking", "bakery", "recipe", "encyclopedia"]
            },
            {
                "url": "https://python.org",
                "title": "Welcome to Python.org",
                "snippet": "Python is a programming language that lets you work quickly and integrate systems more effectively.",
                "tokens": ["python", "programming", "code", "language", "software", "developer", "script"]
            },
            {
                "url": "https://news.ycombinator.com",
                "title": "Hacker News - Indie Web Tech & Discussions",
                "snippet": "A community started by Y Combinator dedicated to technology, hacking, indie programming, and startup news.",
                "tokens": ["hacker", "news", "tech", "technology", "programming", "startup", "discussion", "indie", "web"]
            },
            {
                "url": "https://archive.org",
                "title": "Internet Archive: Digital Library of Free & Open Web",
                "snippet": "Internet Archive is a non-profit library of millions of free books, movies, software, music, websites, and more.",
                "tokens": ["archive", "internet", "library", "books", "free", "history", "web", "digital"]
            },
            {
                "url": "https://w3schools.com",
                "title": "W3Schools Online Web Tutorials",
                "snippet": "Learn web development with free tutorials on HTML, CSS, JavaScript, Python, SQL, and Web Design.",
                "tokens": ["html", "css", "javascript", "web", "development", "coding", "tutorial", "learning"]
            }
        ]
        for item in seeds:
            url = item["url"]
            domain = urllib.parse.urlparse(url).netloc
            self.docs[url] = {
                "title": item["title"],
                "snippet": item["snippet"],
                "domain": domain
            }
            for token in item["tokens"]:
                token = token.lower()
                if token not in self.index:
                    self.index[token] = {}
                self.index[token][url] = self.index[token].get(url, 0) + 3

    def crawl_and_index(self, url):
        """Index any live URL visited by the user into Crust Search!"""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PieBrowser/2.0 CrustCrawler'})
            with urllib.request.urlopen(req, timeout=4) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
                
            parser = HTMLTextExtractor()
            parser.feed(html_content)
            
            title = parser.title.strip() or url
            full_text = " ".join(parser.text_parts)
            snippet = (full_text[:180] + "...") if len(full_text) > 180 else full_text
            domain = urllib.parse.urlparse(url).netloc

            self.docs[url] = {"title": title, "snippet": snippet, "domain": domain}
            
            # Tokenize & index words
            words = re.findall(r'\w+', (title + " " + full_text).lower())
            for word in words:
                if len(word) > 2:
                    if word not in self.index:
                        self.index[word] = {}
                    self.index[word][url] = self.index[word].get(url, 0) + 1
            return True, f"Successfully indexed: {title}"
        except Exception as e:
            return False, f"Indexing failed: {str(e)}"

    def search(self, query):
        """Search algorithm returning pure, ranked links."""
        tokens = [t.lower() for t in re.findall(r'\w+', query)]
        scores = {}
        
        for token in tokens:
            if token in self.index:
                for url, score in self.index[token].items():
                    scores[url] = scores.get(url, 0) + score
        
        # Sort URLs by relevance score
        ranked_urls = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for url, score in ranked_urls:
            doc = self.docs.get(url, {})
            results.append({
                "url": url,
                "title": doc.get("title", url),
                "snippet": doc.get("snippet", "No snippet available."),
                "domain": doc.get("domain", url),
                "score": score
            })
        return results

    def render_results_html(self, query, results):
        """Generates clean HTML search results with zero AI bloat."""
        results_html = ""
        if not results:
            results_html = f"""
            <div class="no-results">
                <h3>No Slices found in Crust Search for "{query}"</h3>
                <p>Try indexing websites by clicking the <b>🕸️ Index Page</b> button on any page you visit!</p>
            </div>
            """
        else:
            for item in results:
                results_html += f"""
                <div class="result-card">
                    <span class="domain">🥧 {item['domain']}</span>
                    <a class="title" href="{item['url']}">{item['title']}</a>
                    <p class="snippet">{item['snippet']}</p>
                    <span class="relevance">Relevance Score: {item['score']}</span>
                </div>
                """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, sans-serif;
                    background-color: #FDFBF7;
                    color: #333;
                    margin: 0;
                    padding: 40px;
                }}
                .header {{
                    border-bottom: 2px solid #D2691E;
                    padding-bottom: 15px;
                    margin-bottom: 25px;
                }}
                .logo {{
                    color: #8B4513;
                    font-size: 28px;
                    font-weight: bold;
                    text-decoration: none;
                }}
                .tagline {{
                    font-size: 13px;
                    color: #D2691E;
                    font-weight: bold;
                    margin-left: 10px;
                }}
                .stats {{
                    font-size: 12px;
                    color: #777;
                    margin-top: 5px;
                }}
                .result-card {{
                    background: white;
                    border: 1px solid #EFE6D5;
                    border-left: 4px solid #D2691E;
                    border-radius: 6px;
                    padding: 15px 20px;
                    margin-bottom: 18px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
                }}
                .domain {{
                    font-size: 12px;
                    color: #8B4513;
                    font-weight: bold;
                    display: block;
                    margin-bottom: 4px;
                }}
                .title {{
                    font-size: 18px;
                    color: #1A0DAB;
                    text-decoration: none;
                    font-weight: 600;
                }}
                .title:hover {{ text-decoration: underline; color: #D2691E; }}
                .snippet {{
                    font-size: 14px;
                    color: #444;
                    margin: 8px 0;
                    line-height: 1.4;
                }}
                .relevance {{
                    font-size: 11px;
                    color: #999;
                    background: #F5EBE0;
                    padding: 2px 6px;
                    border-radius: 4px;
                }}
                .no-results {{
                    background: #FFF3E0;
                    border: 1px solid #FFE0B2;
                    padding: 20px;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <span class="logo">🥧 Crust Search</span>
                <span class="tagline">Independent Engine • Zero AI • Pure Web</span>
                <div class="stats">Found {len(results)} native web results for "{query}"</div>
            </div>
            {results_html}
        </body>
        </html>
        """

# Global Crust Search Instance
crust_engine = CrustSearchEngine()

# ==============================================================================
# 🥧 MAIN BROWSER UI APPLICATION
# ==============================================================================

class PieBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pie Browser v2.0 - Independent Engine Edition")
        self.setGeometry(100, 100, 1280, 850)

        # Storage
        self.pantry_links = []  # Bookmarks
        self.crumbs_list = []   # History

        # Styling (Bakery Palette)
        self.setStyleSheet("""
            QMainWindow { background-color: #FDFBF7; }
            QTabWidget::pane { border: 2px solid #D2B48C; background: white; }
            QTabBar::tab {
                background: #EFE6D5; color: #5C4033;
                border: 1px solid #D2B48C; border-top-left-radius: 8px; border-top-right-radius: 8px;
                padding: 8px 16px; font-weight: bold; font-family: 'Segoe UI', sans-serif;
            }
            QTabBar::tab:selected { background: #D2691E; color: white; }
            QLineEdit {
                border: 2px solid #D2691E; border-radius: 15px; padding: 6px 15px;
                background-color: #FFFDF9; font-size: 13px; color: #333;
            }
            QPushButton {
                background-color: #8B4513; color: white; border: none; border-radius: 6px;
                padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #A0522D; }
            QPushButton#nav_btn {
                background-color: #EFE6D5; color: #5C4033; border: 1px solid #D2B48C;
                border-radius: 12px; font-size: 13px;
            }
            QPushButton#nav_btn:hover { background-color: #D2691E; color: white; }
            QPushButton#secret_btn { background-color: #4A2E19; color: #FFD700; }
        """)

        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Nav Bar Layout
        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton("◀", id="nav_btn")
        self.back_btn.clicked.connect(self.navigate_back)
        self.forward_btn = QPushButton("▶", id="nav_btn")
        self.forward_btn.clicked.connect(self.navigate_forward)
        self.reload_btn = QPushButton("🔄", id="nav_btn")
        self.reload_btn.clicked.connect(self.reload_page)

        # The Dish (Address Bar)
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Search Crust Engine or type URL... 🥧")
        self.address_bar.returnPressed.connect(self.load_from_address_bar)

        # Action Buttons
        self.index_page_btn = QPushButton("🕸️ Index Page", id="nav_btn")
        self.index_page_btn.setToolTip("Add current web page to your custom Crust Search engine!")
        self.index_page_btn.clicked.connect(self.index_current_page)

        self.add_pantry_btn = QPushButton("⭐ Save")
        self.add_pantry_btn.clicked.connect(self.save_to_pantry)

        self.pantry_btn = QPushButton("🧺 Pantry")
        self.pantry_btn.clicked.connect(self.open_pantry_manager)

        self.crumbs_btn = QPushButton("🧹 Crumbs")
        self.crumbs_btn.clicked.connect(self.open_crumbs_manager)

        self.secret_slice_btn = QPushButton("🤫 Secret Slice", id="secret_btn")
        self.secret_slice_btn.clicked.connect(lambda: self.add_new_slice(is_secret=True))

        self.new_slice_btn = QPushButton("+ Cut Slice 🥧")
        self.new_slice_btn.clicked.connect(lambda: self.add_new_slice())

        # Assemble Controls
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.reload_btn)
        nav_layout.addWidget(self.address_bar)
        nav_layout.addWidget(self.index_page_btn)
        nav_layout.addWidget(self.add_pantry_btn)
        nav_layout.addWidget(self.pantry_btn)
        nav_layout.addWidget(self.crumbs_btn)
        nav_layout.addWidget(self.secret_slice_btn)
        nav_layout.addWidget(self.new_slice_btn)

        layout.addLayout(nav_layout)

        # Slices Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_slice)
        self.tabs.currentChanged.connect(self.slice_changed)
        layout.addWidget(self.tabs)

        # Initial Search Startup Page
        self.add_new_slice(query="pie", label="Slice 1 🥧")

    # --- SLICES (TABS) ENGINE ---
    def add_new_slice(self, url=None, query=None, label="New Slice 🥧", is_secret=False):
        browser = QWebEngineView()
        browser.setProperty("is_secret", is_secret)

        index = self.tabs.addTab(browser, f"🤫 {label}" if is_secret else label)
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(lambda qurl, b=browser: self.update_url(qurl, b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_title(title, b))

        if query:
            self.execute_crust_search(query, browser)
        elif url:
            browser.setUrl(QUrl(url))
        else:
            self.execute_crust_search("pie", browser)

    def close_slice(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            QMessageBox.information(self, "Pie Browser", "You must keep at least one Slice open!")

    def slice_changed(self, index):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            self.address_bar.setText(current_browser.url().toString())

    # --- CRUST SEARCH ENGINE EXECUTION ---
    def execute_crust_search(self, query, browser):
        """Runs the native non-Google Crust Engine and renders HTML directly."""
        results = crust_engine.search(query)
        html_content = crust_engine.render_results_html(query, results)
        browser.setHtml(html_content, QUrl(f"pie://crust-search?q={urllib.parse.quote(query)}"))

    def load_from_address_bar(self):
        text = self.address_bar.text().strip()
        if not text:
            return

        current_browser = self.tabs.currentWidget()
        if not current_browser:
            return

        # Check if direct URL vs Crust Search query
        if text.startswith("http://") or text.startswith("https://"):
            current_browser.setUrl(QUrl(text))
        elif "." in text and " " not in text:
            current_browser.setUrl(QUrl("https://" + text))
        else:
            # Route through native Crust Search Engine
            self.execute_crust_search(text, current_browser)

    def index_current_page(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            url = current_browser.url().toString()
            if url.startswith("http"):
                success, msg = crust_engine.crawl_and_index(url)
                if success:
                    QMessageBox.information(self, "Crust Engine Indexer", msg)
                else:
                    QMessageBox.warning(self, "Crust Engine Indexer", msg)
            else:
                QMessageBox.warning(self, "Crust Engine", "Cannot index local pie:// search pages.")

    def update_url(self, qurl, browser):
        url_str = qurl.toString()
        if browser == self.tabs.currentWidget():
            self.address_bar.setText(url_str)

        # Log to Crumbs history unless it's a Secret Slice
        is_secret = browser.property("is_secret")
        if not is_secret and url_str and url_str not in self.crumbs_list and not url_str.startswith("pie://"):
            self.crumbs_list.append(url_str)

    def update_title(self, title, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            is_secret = browser.property("is_secret")
            prefix = "🤫 " if is_secret else "🥧 "
            short_title = (title[:14] + '...') if len(title) > 14 else title
            self.tabs.setTabText(index, f"{prefix}{short_title}")

    def navigate_back(self):
        current = self.tabs.currentWidget()
        if current: current.back()

    def navigate_forward(self):
        current = self.tabs.currentWidget()
        if current: current.forward()

    def reload_page(self):
        current = self.tabs.currentWidget()
        if current: current.reload()

    # --- PANTRY MANAGER (BOOKMARK IMPORT/EXPORT) ---
    def save_to_pantry(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            url = current_browser.url().toString()
            if url and url not in self.pantry_links:
                self.pantry_links.append(url)
                QMessageBox.information(self, "Pantry", f"Saved page to Pantry:\n{url}")

    def open_pantry_manager(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("🧺 The Pantry (Bookmarks)")
        dialog.setGeometry(200, 200, 480, 380)
        vbox = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for link in self.pantry_links:
            list_widget.addItem(link)

        list_widget.itemDoubleClicked.connect(lambda item: (dialog.accept(), self.add_new_slice(url=item.text())))

        btn_layout = QHBoxLayout()
        import_btn = QPushButton("📥 Import Pantry")
        import_btn.clicked.connect(lambda: self.import_pantry(list_widget))

        export_btn = QPushButton("📤 Export Pantry")
        export_btn.clicked.connect(self.export_pantry)

        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(export_btn)

        vbox.addWidget(QLabel("Double click to open bookmark:"))
        vbox.addWidget(list_widget)
        vbox.addLayout(btn_layout)
        dialog.exec()

    def import_pantry(self, list_widget):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Pantry Bookmarks", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.pantry_links = list(set(self.pantry_links + data))
                        list_widget.clear()
                        for link in self.pantry_links:
                            list_widget.addItem(link)
                        QMessageBox.information(self, "Pantry", "Imported bookmarks successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import: {str(e)}")

    def export_pantry(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Pantry Bookmarks", "pantry_bookmarks.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.pantry_links, f, indent=4)
                QMessageBox.information(self, "Pantry", "Exported bookmarks successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")

    # --- CRUMBS MANAGER (HISTORY IMPORT/EXPORT) ---
    def open_crumbs_manager(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("🧹 Crumbs (Browsing History)")
        dialog.setGeometry(200, 200, 500, 380)
        vbox = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for crumb in reversed(self.crumbs_list):
            list_widget.addItem(crumb)

        list_widget.itemDoubleClicked.connect(lambda item: (dialog.accept(), self.add_new_slice(url=item.text())))

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Sweep Crumbs (Clear)")
        clear_btn.clicked.connect(lambda: (self.crumbs_list.clear(), list_widget.clear()))

        export_btn = QPushButton("Export History")
        export_btn.clicked.connect(self.export_crumbs)

        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(export_btn)

        vbox.addWidget(QLabel("Double click a crumb to visit:"))
        vbox.addWidget(list_widget)
        vbox.addLayout(btn_layout)
        dialog.exec()

    def export_crumbs(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export History", "crumbs_history.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.crumbs_list, f, indent=4)
                QMessageBox.information(self, "Crumbs", "Exported browsing history!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export history: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = PieBrowser()
    browser.show()
    sys.exit(app.exec())