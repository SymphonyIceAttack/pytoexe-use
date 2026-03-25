#!/usr/bin/env python3
"""
Text to Python Conversion
Generated: 2026-03-24T14:51:35.957Z
Total Lines: 82
"""

def process_text():
    """
    Process and analyze text data
    Returns: dictionary with text data and metadata
    """
    text_lines = [
    "import tkinter as tk",
    "import time",
    "import datetime",
    "import threading",
    "import socket",
    "# Final Okulları Teneffüs Saatleri (Ders Bitiş - Ders Başlangıç)",
    "TENEFFUSLER = [",
    "    (\"09:40\", \"09:50\"), (\"10:30\", \"10:40\"), (\"11:20\", \"11:30\"),",
    "    (\"12:10\", \"12:50\"), # 40 dakikalık öğle arası",
    "    (\"13:30\", \"13:40\"), (\"14:20\", \"14:30\"), (\"15:10\", \"15:20\")",
    "]",
    "class AkilliTahtaApp:",
    "    def __init__(self, root):",
    "        self.root = root",
    "        self.root.title(\"Final Okulları Akıllı Tahta Sistemi\")",
    "        self.root.attributes(\"-fullscreen\", True)",
    "        self.root.attributes(\"-topmost\", True)",
    "        self.root.config(cursor=\"none\") # Kilitliyken imleci gizle",
    "        self.kilit_aktif = True",
    "        # --- Kilit Ekranı Arayüzü ---",
    "        self.kilit_frame = tk.Frame(self.root, bg=\"#1a1a1a\")",
    "        self.ip_label = tk.Label(self.kilit_frame, text=f\"IP: {self.get_ip()}\", fg=\"gray\", bg=\"#1a1a1a\", font=(\"Arial\", 12))",
    "        self.ip_label.pack(side=\"top\", anchor=\"ne\", padx=20, pady=20)",
    "        tk.Label(self.kilit_frame, text=\"TENEFFÜS MODU\", font=(\"Arial\", 60, \"bold\"), fg=\"white\", bg=\"#1a1a1a\").pack(expand=True)",
    "        tk.Label(self.kilit_frame, text=\"Lütfen dersin başlamasını bekleyin...\", font=(\"Arial\", 20), fg=\"#cccccc\", bg=\"#1a1a1a\").pack(expand=True)",
    "        # --- Çizim (Fatih Kalem) Arayüzü ---",
    "        self.kalem_frame = tk.Frame(self.root, bg=\"white\")",
    "        self.canvas = tk.Canvas(self.kalem_frame, bg=\"white\", highlightthickness=0)",
    "        self.canvas.pack(fill=\"both\", expand=True)",
    "        self.canvas.bind(\"<B1-Motion>\", self.ciz)",
    "        # Kontrol Paneli",
    "        self.panel = tk.Frame(self.kalem_frame, bg=\"#333\", height=50)",
    "        self.panel.pack(side=\"top\", fill=\"x\")",
    "        tk.Button(self.panel, text=\"Temizle\", command=lambda: self.canvas.delete(\"all\"), bg=\"red\", fg=\"white\").pack(side=\"left\", padx=10)",
    "        tk.Button(self.panel, text=\"Kapat/Simge Durumu\", command=lambda: self.root.iconify()).pack(side=\"right\", padx=10)",
    "        self.ekrani_kilitle() # Başlangıçta kilitle",
    "        # Arka Plan Görevleri",
    "        threading.Thread(target=self.zaman_kontrol, daemon=True).start()",
    "        threading.Thread(target=self.ag_sunucusu, daemon=True).start()",
    "    def get_ip(self):",
    "        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)",
    "        try:",
    "            s.connect(('8.8.8.8', 1))",
    "            IP = s.getsockname()[0]",
    "        except: IP = '127.0.0.1'",
    "        finally: s.close()",
    "        return IP",
    "    def ciz(self, event):",
    "        x, y = event.x, event.y",
    "        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=\"black\", outline=\"black\")",
    "    def ekrani_kilitle(self):",
    "        self.kilit_aktif = True",
    "        self.root.attributes(\"-topmost\", True)",
    "        self.root.config(cursor=\"none\")",
    "        self.kalem_frame.pack_forget()",
    "        self.kilit_frame.pack(fill=\"both\", expand=True)",
    "    def kilidi_ac(self):",
    "        self.kilit_aktif = False",
    "        self.root.attributes(\"-topmost\", False)",
    "        self.root.config(cursor=\"arrow\")",
    "        self.kilit_frame.pack_forget()",
    "        self.kalem_frame.pack(fill=\"both\", expand=True)",
    "    def zaman_kontrol(self):",
    "        while True:",
    "            simdi = datetime.datetime.now().strftime(\"%H:%M\")",
    "            teneffus_vakti = any(bas <= simdi < bit for bas, bit in TENEFFUSLER)",
    "            if teneffus_vakti and not self.kilit_aktif:",
    "                self.ekrani_kilitle()",
    "            time.sleep(15)",
    "    def ag_sunucusu(self):",
    "        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:",
    "            s.bind((\"0.0.0.0\", 6060))",
    "            s.listen()",
    "            while True:",
    "                conn, _ = s.accept()",
    "                with conn:",
    "                    data = conn.recv(1024).decode()",
    "                    if data == \"OPEN\": self.kilidi_ac()",
    "if __name__ == \"__main__\":",
    "    root = tk.Tk()",
    "    app = AkilliTahtaApp(root)",
    "    root.mainloop()"
    ]
    
    # Calculate metadata
    metadata = {
        'total_lines': 82,
        'total_characters': 3865,
        'total_words': 284,
        'created_at': '2026-03-24T14:51:35.957Z',
        'version': '1.0'
    }
    
    # Calculate statistics
    line_lengths = [len(line) for line in text_lines]
    statistics = {
        'average_line_length': sum(line_lengths) // len(line_lengths) if line_lengths else 0,
        'longest_line': max(line_lengths) if line_lengths else 0,
        'shortest_line': min(line_lengths) if line_lengths else 0,
        'empty_lines': 16
    }
    
    return {
        'lines': text_lines,
        'metadata': metadata,
        'statistics': statistics
    }

def display_text(data):
    """Display text data with metadata"""
    print("Metadata:")
    for key, value in data['metadata'].items():
        print(f"  {key}: {value}")
    
    print("\nStatistics:")
    for key, value in data['statistics'].items():
        print(f"  {key}: {value}")
    
    print("\nText Lines:")
    for i, line in enumerate(data['lines'], 1):
        print(f"Line {i}: {line}")

if __name__ == "__main__":
    data = process_text()
    display_text(data)