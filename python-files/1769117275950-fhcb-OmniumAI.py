import sys, os, re, json
import google.generativeai as genai
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextBrowser, QLineEdit, QPushButton, QListWidget, 
                             QListWidgetItem, QFrame, QFileDialog, QLabel)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextCursor

# --- CONFIGURATION ---
API_KEY = "AIzaSyC44OWBxcyLxmIxmujvwDaGf8ZhVQQf5jk"
HISTORY_DIR = "history"

if not os.path.exists(HISTORY_DIR): os.makedirs(HISTORY_DIR)

genai.configure(api_key=API_KEY)

class AIWorker(QThread):
    response_signal = Signal(str)
    
    def __init__(self, user_text, img_path=None):
        super().__init__()
        self.user_text = user_text
        self.img_path = img_path

    def run(self):
        try:
            # Используем самый стабильный алиас модели
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction="You are OmniumAI. Strictly professional tone. NEVER use informal words like 'Брат'. Answer in Russian."
            )
            
            content = []
            if self.img_path:
                with open(self.img_path, "rb") as f:
                    img_bytes = f.read()
                content.append({"mime_type": "image/jpeg", "data": img_bytes})
            
            content.append(self.user_text if self.user_text else "Проанализируй изображение.")

            response = model.generate_content(content)
            
            if response.text:
                ans = response.text
                # Принудительная очистка от нежелательных обращений
                ans = re.sub(r'\b(брат|Брат|brother|Brother)\b', '', ans).strip(",. ")
                self.response_signal.emit(ans)
            else:
                self.response_signal.emit(">> AI_CORE: Empty response (check safety filters).")
                
        except Exception as e:
            self.response_signal.emit(f">> SYSTEM_ERROR: {str(e)}")

class OmniumV36(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmniumAI // SYSTEM v36.0")
        self.resize(1100, 850)
        self.current_chat_id = None
        self.history = []
        self.current_img = None
        self.init_ui()
        self.load_chats()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #050505; color: #00FF41; font-family: 'Consolas', monospace; }
            #Sidebar { border-right: 2px solid #004411; background: #000; }
            QListWidget { border: none; color: #008F11; outline: none; }
            QListWidget::item:selected { background: #00FF41; color: #000; font-weight: bold; }
            QTextBrowser { border: none; font-size: 15px; }
            #InputBox { border-top: 2px solid #00FF41; padding: 15px; }
            QLineEdit { border: 1px solid #004411; color: #00FF41; padding: 10px; background: #080808; }
            #Btn { background: #00FF41; color: #000; font-weight: bold; border: none; padding: 10px 25px; }
        """)

        layout = QHBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        
        # Сайдбар
        side = QFrame(); side.setObjectName("Sidebar"); side.setFixedWidth(250)
        side_lay = QVBoxLayout(side)
        btn_new = QPushButton("[ INIT_SESSION ]"); btn_new.setObjectName("Btn")
        btn_new.clicked.connect(self.create_chat)
        side_lay.addWidget(btn_new)
        self.chat_list = QListWidget(); self.chat_list.itemClicked.connect(self.switch_chat)
        side_lay.addWidget(self.chat_list)
        layout.addWidget(side)

        # Консоль
        main_lay = QVBoxLayout()
        self.display = QTextBrowser()
        main_lay.addWidget(self.display)
        
        self.status = QLabel("STATUS: IDLE"); self.status.setStyleSheet("color: #58A6FF; margin-left: 10px;")
        main_lay.addWidget(self.status)

        in_frame = QFrame(); in_frame.setObjectName("InputBox")
        in_lay = QHBoxLayout(in_frame)
        btn_img = QPushButton("📎"); btn_img.setObjectName("Btn")
        btn_img.clicked.connect(self.attach)
        self.input = QLineEdit(); self.input.setPlaceholderText("Command...")
        self.input.returnPressed.connect(self.send)
        btn_run = QPushButton("RUN"); btn_run.setObjectName("Btn")
        btn_run.clicked.connect(self.send)
        
        in_lay.addWidget(btn_img); in_lay.addWidget(self.input); in_lay.addWidget(btn_run)
        main_lay.addWidget(in_frame)
        layout.addLayout(main_lay)

    def attach(self):
        path, _ = QFileDialog.getOpenFileName(self, "Image", "", "Images (*.jpg *.png *.jpeg)")
        if path:
            self.current_img = path
            self.status.setText(f"READY: {os.path.basename(path)}")

    def create_chat(self):
        self.current_chat_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.history = []; self.display.clear()
        self.display.append(">> OmniumAI v36.0 Online.")
        self.load_chats()

    def switch_chat(self, item):
        self.current_chat_id = item.data(Qt.UserRole)
        path = os.path.join(HISTORY_DIR, f"{self.current_chat_id}.json")
        try:
            with open(path, "r", encoding="utf-8") as f: self.history = json.load(f)
            self.display.clear()
            for m in self.history: self.render_msg(m['role'], m['content'])
        except: pass

    def load_chats(self):
        self.chat_list.clear()
        if os.path.exists(HISTORY_DIR):
            for f in sorted(os.listdir(HISTORY_DIR), reverse=True):
                if f.endswith(".json"):
                    cid = f.replace(".json", "")
                    it = QListWidgetItem(cid); it.setData(Qt.UserRole, cid); self.chat_list.addItem(it)

    def render_msg(self, role, text):
        tag = "[USER]:" if role == "user" else "[OmniumAI]:"
        color = "#58A6FF" if role == "user" else "#00FF41"
        self.display.append(f"<b style='color:{color};'>{tag}</b> {text}\n")
        self.display.moveCursor(QTextCursor.End)

    def send(self):
        txt = self.input.text().strip()
        if not txt and not self.current_img: return
        if not self.current_chat_id: self.create_chat()
        
        self.render_msg("user", txt + (" (DATA)" if self.current_img else ""))
        self.input.setEnabled(False); self.input.clear()
        
        self.worker = AIWorker(txt, self.current_img)
        self.worker.response_signal.connect(self.done); self.worker.start()

    def done(self, ans):
        self.history.append({"role": "user", "content": "Request" if not self.input.text() else self.input.text()})
        self.history.append({"role": "assistant", "content": ans})
        with open(os.path.join(HISTORY_DIR, f"{self.current_chat_id}.json"), "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False)
        self.render_msg("assistant", ans)
        self.current_img = None; self.status.setText("STATUS: IDLE"); self.input.setEnabled(True); self.input.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv); win = OmniumV36(); win.show(); sys.exit(app.exec())