global REMAINING_TIME
import os
import sys
import ctypes
def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
def request_admin():
    """请求管理员权限"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)
        sys.exit()
if getattr(sys, 'frozen', False):
    if not is_admin():
        request_admin()
def setup_playwright_path():
    """设置 Playwright 浏览器路径 - 支持打包后的 exe"""
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    browsers_path = os.path.join(application_path, 'playwright_browsers')
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        temp_browsers = os.path.join(sys._MEIPASS, 'playwright_browsers')
        if temp_browsers and os.path.exists(temp_browsers):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = temp_browsers
            print(f'使用内置浏览器: {temp_browsers}')
            return None
    if os.path.exists(browsers_path):
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
        print(f'使用本地浏览器: {browsers_path}')
        return None
    else:
        if os.environ.get('PLAYWRIGHT_BROWSERS_PATH'):
            print(f"使用环境变量指定的浏览器路径: {os.environ['PLAYWRIGHT_BROWSERS_PATH']}")
        else:
            user_browsers = os.path.expanduser('~\\.cache\\ms-playwright')
            if os.path.exists(user_browsers):
                print(f'使用用户缓存浏览器: {user_browsers}')
            else:
                print('提示: 未找到浏览器，程序将自动下载（约120MB）')
setup_playwright_path()
from playwright.sync_api import sync_playwright
import time
import random
import string
import requests
import re
import urllib3
import pathlib
import threading
import hashlib
import datetime
import uuid
import platform
import subprocess
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit, QSpinBox, QHBoxLayout, QComboBox, QDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
urllib3.disable_warnings()
def get_app_path():
    """获取应用程序路径（支持打包后的 exe）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
def get_extension_path():
    """获取扩展路径（支持打包后相对路径）"""
    app_path = get_app_path()
    possible_paths = [os.path.join(app_path, 'google_pro_1.4.1'), os.path.join(app_path, 'extensions', 'google_pro_1.4.1'), 'C:\\Users\\Administrator\\Desktop\\SteamTool - 副本\\google_pro_1.4.1']
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            possible_paths.insert(0, os.path.join(sys._MEIPASS, 'google_pro_1.4.1'))
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return possible_paths[0]
def get_user_data_dir():
    """获取用户数据目录（支持打包后）- 使用固定路径，不会每次变化"""
    app_path = get_app_path()
    user_data_dir = os.path.join(app_path, 'SteamBrowserData')
    try:
        os.makedirs(user_data_dir, exist_ok=True)
        return user_data_dir
    except:
        docs_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'SteamRegister_BrowserData')
        os.makedirs(docs_dir, exist_ok=True)
        return docs_dir
SERVER_URL = 'https://www.keyt.cn/kami/w971131370/check.php'
APP_NAME = 'zidong'
SIGN_KEY = 'DreamX'
TIMESTAMP_MAX_DIFF = 120
APP_DATA_DIR = get_app_path()
CARD_PATH = os.path.join(APP_DATA_DIR, 'steam_save_card.txt')
LICENSE_CHECK_INTERVAL = 50
RETRY_CHECK_INTERVAL = 20
MAX_RETRY_FAILED = 5
NETWORK_RETRY_MIN_COUNT = 2
NETWORK_RETRY_MIN_DURATION = 30
DUCKMAIL_API_URL = 'https://api.dreamw.fun'
DUCKMAIL_MAIL_URL = 'https://mail.dreamw.fun'
DUCKMAIL_ADMIN_PASSWORD = '5201314@'
DUCKMAIL_DOMAIN = 'dreamw.fun'
EXTENSION_PATH = get_extension_path()
BASE_USER_DATA_DIR = get_user_data_dir()
TIANQI_API_URL = '1'
TIANQI_SECRET = '199t2st9wp8awx3w'
TIANQI_SIGN = '543d0c2cad76ff96446bdd4b72121cec'
REMAINING_TIME = '长期'
def fetch_tianqi_proxy():
    """从天启HTTP提取一个代理IP（每次注册账号调用一次）"""
    try:
        params = {
            'secret': TIANQI_SECRET,
            'num': 1,
            'type': 'txt',
            'port': 1,
            'time': 3,
            'mr': 1,
            'sign': TIANQI_SIGN,
            'region': '440000,460000,130000,320000,360000,210000,420000,410000'
        }
        resp = requests.get(TIANQI_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        proxy = resp.text.strip()
        if proxy:
            return {'server': f'http://{proxy}'}
    except Exception as e:
        print(f'提取代理失败: {e}')
    return None
def create_duckmail_email():
    """创建 DuckMail 邮箱（永不过期）"""
    try:
        url = f'{DUCKMAIL_API_URL}/admin/new_address'
        name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        payload = {'enablePrefix': True, 'name': name, 'domain': DUCKMAIL_DOMAIN, 'expiresIn': 0}
        headers = {'x-admin-auth': DUCKMAIL_ADMIN_PASSWORD, 'Content-Type': 'application/json'}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return {'success': True, 'email': data.get('address'), 'jwt': data.get('jwt'), 'address_id': data.get('address_id')}
        else:
            print(f'创建 DuckMail 邮箱失败: {resp.text}')
            return {'success': False}
    except Exception as e:
        print(f'创建 DuckMail 邮箱异常: {e}')
        return {'success': False}
def change_email_password(address_id, new_password, jwt=None):
    """修改邮箱密码"""
    if not jwt:
        return {'success': False, 'error': '需要传入 jwt'}
    try:
        url = f'{DUCKMAIL_API_URL}/api/address_change_password'
        sha256_password = hashlib.sha256(new_password.encode()).hexdigest()
        payload = {'new_password': sha256_password}
        headers = {'Authorization': f'Bearer {jwt}', 'Content-Type': 'application/json'}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            return {'success': True}
        return {'success': False, 'error': resp.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}
def delete_duckmail_email(address_id):
    """删除 DuckMail 邮箱"""
    try:
        url = f'{DUCKMAIL_API_URL}/admin/delete_address/{address_id}'
        headers = {'x-admin-auth': DUCKMAIL_ADMIN_PASSWORD, 'Content-Type': 'application/json'}
        resp = requests.delete(url, headers=headers, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        print(f'删除邮箱异常: {e}')
        return False
def check_duckmail_mails(email, log_func=None):
    """检查 DuckMail 邮箱的邮件列表"""
    try:
        url = f'{DUCKMAIL_API_URL}/admin/mails'
        headers = {'x-admin-auth': DUCKMAIL_ADMIN_PASSWORD}
        params = {'limit': 20, 'offset': 0, 'address': email}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('results', [])
        else:
            if log_func:
                log_func(f'检查邮件失败: {resp.status_code}')
            return []
    except Exception as e:
        if log_func:
            log_func(f'检查邮件异常: {e}')
        return []
def extract_verification_link_from_raw(raw_content):
    """从邮件原始内容中提取 Steam 验证链接"""
    cleaned = re.sub('=\\s*\\n', '', raw_content)
    cleaned = cleaned.replace('=3D', '=')
    pattern = 'https?://store\\.steampowered\\.com/account/newaccountverification\\?stoken=[a-f0-9]+&creationid=\\d+'
    match = re.search(pattern, cleaned)
    if match:
        return match.group(0)
def extract_disable_link_from_raw(raw_content):
    """从邮件原始内容中提取 Steam 禁用令牌链接"""
    cleaned = re.sub('=\\s*\\n', '', raw_content)
    cleaned = cleaned.replace('=3D', '=')
    pattern = 'https?://store\\.steampowered\\.com/account/steamguarddisableverification\\?stoken=[a-f0-9]+&steamid=\\d+'
    match = re.search(pattern, cleaned)
    if match:
        return match.group(0)
def wait_for_verification_email(email, log_func, max_attempts=3):
    """等待验证邮件并返回验证链接（最多等待3次）"""
    log_func(f'等待验证邮件... (邮箱: {email})')
    for i in range(max_attempts):
        if i > 0:
            time.sleep(3)
        log_func(f'  第{i + 1}次检查邮箱...')
        mails = check_duckmail_mails(email, log_func)
        if not mails:
            continue
        else:
            for mail in mails:
                raw = mail.get('raw', '')
                link = extract_verification_link_from_raw(raw)
                if link:
                    log_func('  ✓ 提取到验证链接')
                    return link
    log_func('  ✗ 等待超时，未收到验证邮件')
def wait_for_disable_email(email, log_func, max_attempts=25):
    """等待禁用确认邮件并返回确认链接"""
    log_func(f'等待禁用确认邮件... (邮箱: {email})')
    for i in range(max_attempts):
        if i > 0:
            time.sleep(3)
        log_func(f'  第{i + 1}次检查邮箱...')
        mails = check_duckmail_mails(email, log_func)
        if not mails:
            continue
        else:
            for mail in mails:
                raw = mail.get('raw', '')
                link = extract_disable_link_from_raw(raw)
                if link:
                    log_func('  ✓ 提取到确认链接')
                    return link
def md5_string(data_str):
    return hashlib.md5(data_str.encode('utf-8')).hexdigest().lower()
def calc_sign(data):
    key_len = len(SIGN_KEY)
    res = ''
    for i in range(len(data)):
        v = (ord(data[i]) + ord(SIGN_KEY[i % key_len])) % 256
        res += f'{v:02x}'
    return res.lower()
def verify_response(raw, xsign2):
    if '|sign=' not in raw:
        return ''
    else:
        body, sign = raw.split('|sign=', 1)
        local_sign = ''
        if xsign2 and len(xsign2) == 32:
            local_sign = md5_string(body + SIGN_KEY)
            if local_sign!= xsign2.lower():
                return ''
        else:
            if len(sign) == 32:
                local_sign = md5_string(body + SIGN_KEY)
            else:
                local_sign = calc_sign(body)
        if local_sign.lower()!= sign.lower() and (not xsign2 or local_sign.lower()!= xsign2.lower()):
                return ''
        if '|' not in body:
            return ''
        else:
            last_pipe = body.rfind('|')
            ts_str = body[last_pipe + 1:]
            if not ts_str.isdigit() or abs(int(time.time()) - int(ts_str)) > TIMESTAMP_MAX_DIFF:
                return ''
            else:
                return body[:last_pipe]
def trans_msg_and_get_action(code):
    mapping = {'already_online': ('该卡密已在线（多设备上限可能已满）', False), 'online_limit_reached': ('在线设备数已满', False), 'activate': ('激活成功', True), 'valid': ('验证通过', True), 'permanent': ('终身有效', True), 'heartbeat': ('心跳正常', True), 'bypass': ('验证已关闭', True), 'unbind_ok': ('解绑成功', True), 'invalid_card': ('卡密无效', False), 'expired': ('卡密已过期', False), 'banned': ('卡密已被禁用', False), 'device_mismatch': ('设备不匹配', False), 'missing_params': ('参数不完整', False)}
    if code in mapping:
        return mapping[code]
    else:
        return (code, False)
def get_hardware_id() -> str:
    try:
        node_name = platform.node()
        if platform.system() == 'Windows':
            cpu_id = ''
            try:
                cpu_output = subprocess.check_output('wmic cpu get ProcessorId', shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL).decode(errors='ignore').split('\n')
                cpu_id = next((line.strip() for line in cpu_output if line.strip() and 'ProcessorId' not in line), '')
            except:
                pass
            base_str = (cpu_id + node_name).encode()
        else:
            mac_address = hex(uuid.getnode())
            base_str = (node_name + mac_address).encode()
        return hashlib.md5(base_str).hexdigest()[:16].upper() + 'MAC'
    except:
        return 'HWID' + os.urandom(4).hex().upper() + 'MAC'
def save_license_key(key: str) -> None:
    dir_path = os.path.dirname(CARD_PATH)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    with open(CARD_PATH, 'w', encoding='utf-8') as f:
        f.write(key)
def load_license_key() -> str:
    if not os.path.isfile(CARD_PATH):
        return ''
    with open(CARD_PATH, 'r', encoding='utf-8') as f:
        return f.read().strip()
def check_card_core(card, mac, is_heartbeat=False):
    global REMAINING_TIME
    try:
        t_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        url = f'{SERVER_URL}?card={card}&mac={mac}&app={APP_NAME}&t={t_str}'
        if is_heartbeat:
            url += '&heart=1'
        response = requests.get(url, headers={'Cache-Control': 'no-cache'}, timeout=10)
        ret = response.text
        xsign2 = response.headers.get('X-Sign2', '')
        body = ret.split('|sign=')[0] if '|sign=' in ret else ret
        biz = ''
        if xsign2 and md5_string(body + SIGN_KEY) == xsign2.lower() and '|' in body:
            last_pipe = body.rfind('|')
            ts_str = body[last_pipe + 1:]
            if ts_str.isdigit() and abs(int(time.time()) - int(ts_str)) <= TIMESTAMP_MAX_DIFF:
                biz = body[:last_pipe]
        if not biz:
            biz = verify_response(ret, xsign2)
        if not biz:
            return 'error|签名校验失败或时间戳过期'

        if biz.startswith('error|'):
            raw_code = biz.split('|', 1)[1]
            msg, is_ok = trans_msg_and_get_action(raw_code)
            return '{}|{}'.format('ok' if is_ok else 'error', msg)

        arr = biz.split('|')
        status_code = arr[0]
        days = arr[1] if len(arr) > 1 else ''
        if is_heartbeat:
            msg, _ = trans_msg_and_get_action('heartbeat')
        else:
            msg, _ = trans_msg_and_get_action('valid')
        if days.isdigit():
            if len(arr) >= 4:
                total_mins = int(arr[3])
                REMAINING_TIME = f'{total_mins // 1440}天{total_mins % 1440 // 60}小时{total_mins % 60}分钟'
            else:
                REMAINING_TIME = f'{days}天'
        else:
            if days.lower() == 'permanent':
                msg, _ = trans_msg_and_get_action('permanent')
                REMAINING_TIME = msg
            else:
                REMAINING_TIME = days
        return f'ok|{msg}'
    except requests.exceptions.Timeout:
        return 'network|验证接口请求超时'
    except requests.exceptions.ConnectionError:
        return 'network|网络连接失败，请检查网络'
    except Exception as e:
        return f'error|验证异常: {str(e)}\n{traceback.format_exc()}'

def verify_license_key(key: str, hwid: str, is_heartbeat=False) -> dict:
    result = check_card_core(key, hwid, is_heartbeat=is_heartbeat)
    if isinstance(result, str):
        if result.startswith('ok|'):
            msg = result.split('|', 1)[1]
            return {'ok': True, 'expire': REMAINING_TIME, 'msg': msg}
        elif result.startswith('network|'):
            return {'ok': False, 'expire': '', 'msg': result.split('|', 1)[1]}
        else:
            return {'ok': False, 'expire': '', 'msg': result.split('|', 1)[1] if '|' in result else result}
    return {'ok': False, 'expire': '', 'msg': '验证结果异常'}

def license_background_check(key: str, hwid: str) -> None:
    while True:
        time.sleep(LICENSE_CHECK_INTERVAL)
        verify_license_key(key, hwid, is_heartbeat=True)

class LicenseDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('软件激活')
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)
        title = QLabel('Steam 账号批量自动注册工具')
        title.setFont(QFont('微软雅黑', 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        line = QLabel('==================================================')
        line.setAlignment(Qt.AlignCenter)
        layout.addWidget(line)
        tip = QLabel('请输入您的卡密进行激活:')
        tip.setFont(QFont('微软雅黑', 10))
        tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(tip)
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText('请输入卡密')
        self.license_input.setFont(QFont('Consolas', 11))
        layout.addWidget(self.license_input)
        self.verify_btn = QPushButton('验证并激活')
        self.verify_btn.clicked.connect(self.verify_license)
        layout.addWidget(self.verify_btn)
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        hint = QLabel('提示：激活后会自动保存，下次启动免输入')
        hint.setFont(QFont('微软雅黑', 9))
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)
        self.license_key = None
    def verify_license(self):
        key = self.license_input.text().strip()
        if not key:
            QMessageBox.warning(self, '提示', '请输入卡密！')
            return None
        else:
            self.verify_btn.setEnabled(False)
            self.verify_btn.setText('验证中...')
            self.status_label.setText('正在验证，请稍候...')
            def verify_task():
                hwid = get_hardware_id()
                result = verify_license_key(key, hwid)
                if result.get('ok', False):
                    save_license_key(key)
                    self.license_key = key
                    self.accept()
                else:
                    error_msg = result.get('msg', '验证失败')
                    self.status_label.setText(f'验证失败: {error_msg}')
                    self.verify_btn.setEnabled(True)
                    self.verify_btn.setText('验证并激活')
            threading.Thread(target=verify_task, daemon=True).start()
def generate_username():
    prefix = ['Cool', 'Happy', 'Fast', 'Smart', 'Dark', 'Light', 'Super', 'Mega']
    suffix = ['Gamer', 'Player', 'Warrior', 'Knight', 'Wolf', 'Hunter', 'Ninja']
    return random.choice(prefix) + random.choice(suffix) + ''.join((random.choice('0123456789') for _ in range(4)))
def generate_password():
    letter_count = random.randint(6, 10)
    letters = []
    for _ in range(letter_count):
        if random.choice([True, False]):
            letters.append(chr(random.randint(65, 90)))
        else:
            letters.append(chr(random.randint(97, 122)))
    num_count = random.randint(2, 6)
    numbers = ''.join((str(random.randint(0, 9)) for _ in range(num_count)))
    symbol = random.choice(['@', '!'])
    end_char = random.choice(list('abcdefghijklmnopqrstuvwxyz#'))
    return ''.join(letters) + numbers + symbol + end_char
def generate_email():
    """创建 DuckMail 邮箱（永不过期）"""
    result = create_duckmail_email()
    if result.get('success'):
        return result['email']
    else:
        prefix = ''.join((random.choice(string.ascii_lowercase) for _ in range(10)))
        return prefix + '@ddker.com'
def get_email_jwt(email):
    """获取邮箱的 JWT（用于保存）"""
    return None
def check_email(email):
    """检查邮件（使用 DuckMail）"""
    return check_duckmail_mails(email, None)
def get_email_detail(email_id):
    """获取邮件详情（DuckMail 不需要单独获取详情，已在列表中包含 raw）"""
    return {'text_body': ''}
def extract_verification_link(body):
    pattern = 'https?://store\\.steampowered\\.com/account/newaccountverification\\?stoken=[a-f0-9]+&creationid=\\d+'
    match = re.search(pattern, body)
    if match:
        return match.group(0)
def extract_disable_link(body):
    pattern = 'https?://store\\.steampowered\\.com/account/steamguarddisableverification\\?stoken=[a-f0-9]+&steamid=\\d+'
    match = re.search(pattern, body)
    if match:
        return match.group(0)
def wait_for_verification_email(email, log_func, max_attempts=3):
    """等待验证邮件并返回验证链接（最多等待3次）"""
    log_func(f'等待验证邮件... (邮箱: {email})')
    for i in range(max_attempts):
        if i > 0:
            time.sleep(3)
        log_func(f'  第{i + 1}次检查邮箱...')
        mails = check_duckmail_mails(email, log_func)
        if not mails:
            continue
        else:
            for mail in mails:
                raw = mail.get('raw', '')
                link = extract_verification_link_from_raw(raw)
                if link:
                    log_func('  ✓ 提取到验证链接')
                    return link
    log_func('  ✗ 等待超时，未收到验证邮件')
def wait_for_disable_email(email, log_func, max_attempts=25):
    """等待禁用确认邮件并返回确认链接"""
    log_func(f'等待禁用确认邮件... (邮箱: {email})')
    for i in range(max_attempts):
        if i > 0:
            time.sleep(3)
        log_func(f'  第{i + 1}次检查邮箱...')
        mails = check_duckmail_mails(email, log_func)
        if not mails:
            continue
        else:
            for mail in mails:
                raw = mail.get('raw', '')
                link = extract_disable_link_from_raw(raw)
                if link:
                    log_func('  ✓ 提取到确认链接')
                    return link
def check_captcha_error(page, log_func):
    """检查页面是否出现CAPTCHA错误"""
    try:
        error_selectors = ['text=您对 CAPTCHA 的响应似乎无效', 'text=CAPTCHA 响应无效', 'text=请重新验证您不是机器人', '.error_msg', '.alert_error', '.captcha_error']
        for selector in error_selectors:
            error_element = page.locator(selector)
            if error_element.count() > 0:
                error_text = error_element.first.inner_text()
                log_func(f'  ⚠ 检测到CAPTCHA错误: {error_text[:50]}...')
                return True
    except Exception as e:
        return False
    else:
        return False
class BatchRegisterThread(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    progress_signal = pyqtSignal(int, int)
    def __init__(self, count, delay):
        super().__init__()
        self.count = count
        self.delay = delay
    def log(self, msg):
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] {msg}")
    def wait_for_yescaptcha_complete(self, page):
        """等待 YesCaptcha 扩展完成验证"""
        self.log('等待 YesCaptcha 扩展完成验证...')
        for i in range(60):
            result = page.evaluate('\n                () => {\n                    const iframe = document.querySelector(\'iframe[title*=\"hCaptcha 安全挑战复选框\"]\');\n                    let checkboxChecked = false;\n                    if (iframe) {\n                        try {\n                            const doc = iframe.contentDocument;\n                            const checkbox = doc && doc.querySelector(\'#checkbox\');\n                            if (checkbox && checkbox.getAttribute(\'aria-checked\') === \'true\') {\n                                checkboxChecked = true;\n                            }\n                        } catch(e) {}\n                    }\n                    \n                    const responseInput = document.querySelector(\'[name=\"h-captcha-response\"]\');\n                    const hasToken = responseInput && responseInput.value && responseInput.value.length > 50;\n                    \n                    return {\n                        completed: checkboxChecked || hasToken\n                    };\n                }\n            ')
            if result.get('completed'):
                self.log('✓ YesCaptcha 验证完成')
                return True
            else:
                if i % 10 == 0 and i > 0:
                        self.log(f'  等待中... ({i}秒)')
                time.sleep(1)
        self.log('⚠ 等待超时')
        return True
    def simulate_human_click(self, element):
        """模拟人工点击"""
        element.scroll_into_view_if_needed()
        time.sleep(random.uniform(0.3, 0.6))
        element.hover()
        time.sleep(random.uniform(0.1, 0.3))
        element.click(delay=random.randint(50, 120))
    def type_with_delay(self, element, text, delay_range=(50, 120)):
        """逐字输入"""
        for char in text:
            element.type(char, delay=random.randint(delay_range[0], delay_range[1]))
    def safe_goto_with_retry(self, page, url, max_retries=3):
        """安全访问URL，遇到超时自动刷新重试（但Steam注册页面不自动刷新）"""
        is_steam_join = 'store.steampowered.com/join' in url
        for attempt in range(max_retries):
            try:
                if attempt > 0 and not is_steam_join:
                    self.log(f'正在重试访问: {url} (尝试 {attempt + 1}/{max_retries})')
                else:
                    self.log(f'正在访问: {url}')
                page.goto(url, timeout=30000)
                return True
            except Exception as e:
                error_msg = str(e)
                if 'Timeout' in error_msg or 'timeout' in error_msg:
                    if is_steam_join:
                        self.log('✗ Steam注册页面访问超时，不进行刷新重试')
                        return False
                    self.log(f'⚠ 访问超时，尝试刷新页面 (第 {attempt + 1} 次)')
                    try:
                        page.reload(timeout=30000)
                        self.log('✓ 页面刷新成功')
                        return True
                    except Exception:
                        self.log('✗ 刷新失败，将重试')
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                self.log(f'✗ 访问失败: {error_msg}')
                return False
        return False
    def register_one_account(self, context, account_num):
        """注册单个账号（返回True表示成功，False表示失败需要跳过）"""
        email_result = create_duckmail_email()
        if not email_result.get('success'):
            self.log('✗ 创建邮箱失败，跳过此账号')
            return False
        else:
            email = email_result['email']
            email_address_id = email_result['address_id']
            email_jwt = email_result['jwt']
            email_password = generate_password()
            try:
                sha256_password = hashlib.sha256(email_password.encode()).hexdigest()
                change_pwd_url = f'{DUCKMAIL_API_URL}/api/address_change_password'
                change_pwd_headers = {'Authorization': f'Bearer {email_jwt}', 'Content-Type': 'application/json'}
                change_pwd_payload = {'new_password': sha256_password}
                resp = requests.post(change_pwd_url, json=change_pwd_payload, headers=change_pwd_headers, timeout=30)
                if resp.status_code == 200:
                    self.log('✓ 邮箱密码设置成功')
                else:
                    self.log(f'⚠ 邮箱密码设置失败: {resp.text}')
            except Exception as e:
                self.log(f'⚠ 设置邮箱密码异常: {e}')
            username = generate_username()
            password = generate_password()
            self.log(f"\n{'=================================================='}")
            self.log(f'开始注册第 {account_num} 个账号')
            self.log(f'邮箱: {email}')
            self.log(f'用户名: {username}')
            self.log(f'Steam密码: {password}')
            self.log(f'邮箱密码: {email_password}')
            self.log(f"{'=================================================='}")
            page = context.pages[0] if context.pages else context.new_page()
            self.log('打开 Steam 注册页...')
            if not self.safe_goto_with_retry(page, 'https://store.steampowered.com/join/'):
                self.log('✗ 无法访问 Steam 注册页面')
                delete_duckmail_email(email_address_id)
                self.log('已删除对应的邮箱')
                return False
            else:
                time.sleep(5)
                if not self.wait_for_yescaptcha_complete(page):
                    self.log('⚠ 扩展验证未完成，但继续尝试...')
                time.sleep(2)
                self.log('逐字输入邮箱...')
                email_input = page.locator('#email')
                email_input.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.3, 0.6))
                email_input.click()
                time.sleep(random.uniform(0.1, 0.3))
                self.type_with_delay(email_input, email)
                time.sleep(random.uniform(0.2, 0.5))
                reenter_input = page.locator('#reenter_email')
                reenter_input.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.3, 0.6))
                reenter_input.click()
                time.sleep(random.uniform(0.1, 0.3))
                self.type_with_delay(reenter_input, email)
                time.sleep(random.uniform(0.2, 0.5))
                self.log('选择国家/地区: 中国（大陆）')
                page.select_option('#country', index=9)
                time.sleep(0.5)
                self.log('勾选协议...')
                agree_checkbox = page.locator('#i_agree_check')
                self.simulate_human_click(agree_checkbox)
                time.sleep(random.uniform(0.3, 0.6))
                self.log('点击继续按钮，Steam将发送验证邮件...')
                continue_btn = page.locator('#createAccountButton')
                self.simulate_human_click(continue_btn)
                time.sleep(3)
                if check_captcha_error(page, self.log):
                    self.log('⚠ CAPTCHA验证失败，跳过此账号')
                    delete_duckmail_email(email_address_id)
                    self.log('已删除对应的邮箱')
                    return False
                else:
                    verification_link = wait_for_verification_email(email, self.log, max_attempts=3)
                    if not verification_link:
                        self.log('✗ 未收到验证邮件，跳过此账号')
                        delete_duckmail_email(email_address_id)
                        self.log('已删除对应的邮箱')
                        return False
                    else:
                        self.log('✓ 获取到验证链接，正在激活账号...')
                        new_page = context.new_page()
                        if not self.safe_goto_with_retry(new_page, verification_link):
                            self.log('✗ 无法访问验证链接')
                            new_page.close()
                            delete_duckmail_email(email_address_id)
                            self.log('已删除对应的邮箱')
                            return False
                        else:
                            time.sleep(5)
                            new_page.close()
                            self.log('✓ 邮箱验证成功！')
                            self.log('等待跳转到用户名密码页面...')
                            time.sleep(5)
                            if 'completesignup' not in page.url:
                                for pg in context.pages:
                                    if 'completesignup' in pg.url:
                                        page = pg
                                        break
                            self.log(f'当前页面: {page.title()}')
                            self.log('逐字输入用户名和密码...')
                            page.wait_for_selector('#accountname', timeout=30000)
                            username_input = page.locator('#accountname')
                            username_input.scroll_into_view_if_needed()
                            time.sleep(random.uniform(0.2, 0.5))
                            username_input.click()
                            time.sleep(random.uniform(0.1, 0.3))
                            username_input.fill('')
                            self.type_with_delay(username_input, username)
                            password_input = page.locator('#password')
                            password_input.scroll_into_view_if_needed()
                            time.sleep(random.uniform(0.2, 0.5))
                            password_input.click()
                            time.sleep(random.uniform(0.1, 0.3))
                            password_input.fill('')
                            self.type_with_delay(password_input, password)
                            confirm_input = page.locator('#reenter_password')
                            confirm_input.scroll_into_view_if_needed()
                            time.sleep(random.uniform(0.2, 0.5))
                            confirm_input.click()
                            time.sleep(random.uniform(0.1, 0.3))
                            confirm_input.fill('')
                            self.type_with_delay(confirm_input, password)
                            self.log('  ✓ 用户名密码填写完成')
                            self.log('正在点击完成按钮...')
                            complete_btn = page.locator('#createAccountButton')
                            self.simulate_human_click(complete_btn)
                            self.log('  ✓ 已点击「完成」按钮')
                            account_file = os.path.join(get_app_path(), '账号数据.txt')
                            with open(account_file, 'a', encoding='utf-8') as f:
                                f.write(f'账号：{username}密码：{password}邮箱：{email}邮箱密码：{email_password}邮箱地址：{DUCKMAIL_MAIL_URL}\n')
                            self.log(f'✓ 账号已保存到 {account_file}')
                            self.log('等待5秒后开始禁用令牌...')
                            time.sleep(5)
                            self.disable_steam_guard(page, context, email)
                            return True
    def disable_steam_guard(self, page, context, email):
        """禁用 Steam 令牌"""
        self.log('==================================================')
        self.log('开始自动禁用 Steam 令牌...')
        self.log('==================================================')
        try:
            if not self.safe_goto_with_retry(page, 'https://store.steampowered.com/twofactor/manage'):
                self.log('✗ 无法访问令牌管理页面')
                return
            else:
                time.sleep(5)
                self.log('点击「通过电子邮件获取 Steam 令牌验证码」...')
                page.click('#email_authenticator_check')
                time.sleep(2)
                self.log('点击「关闭 Steam 令牌」...')
                page.click('#none_authenticator_check')
                time.sleep(5)
                self.log('点击「禁用 Steam 令牌」...')
                page.click('text=\'禁用 Steam 令牌\'')
                self.log('  ✓ 已点击禁用链接')
                time.sleep(3)
                disable_link = wait_for_disable_email(email, self.log)
                if not disable_link:
                    self.log('✗ 未收到确认邮件')
                    return
                else:
                    self.log('✓ 获取到确认链接，正在完成禁用...')
                    if not self.safe_goto_with_retry(page, disable_link):
                        self.log('✗ 无法访问禁用确认链接')
                        return
                    else:
                        time.sleep(5)
                        self.log('✅ Steam 令牌已成功禁用！')
        except Exception as e:
            self.log(f'自动禁用令牌时发生错误: {e}')
    def run(self):
        try:
            self.log('==================================================')
            self.log(f'开始批量注册 {self.count} 个账号')
            self.log(f'账号间隔: {self.delay} 秒')
            self.log(f'扩展路径: {EXTENSION_PATH}')
            self.log(f'数据目录: {BASE_USER_DATA_DIR}')
            self.log('==================================================')
            if not os.path.exists(EXTENSION_PATH):
                self.log('❌ 错误：找不到扩展文件夹！')
                self.log(f'请确保扩展文件夹存在: {EXTENSION_PATH}')
                self.finished.emit(False, '扩展文件夹不存在')
                return
            else:
                if not os.path.exists(BASE_USER_DATA_DIR):
                    pathlib.Path(BASE_USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
                    self.log(f'✓ 创建固定浏览器数据目录: {BASE_USER_DATA_DIR}')
                success_count = 0
                fixed_user_data_dir = BASE_USER_DATA_DIR
                self.log(f'浏览器固定数据目录: {fixed_user_data_dir}')
                self.log('提示：此目录为固定路径，关闭程序后不会删除，下次启动继续使用')
                for i in range(self.count):
                    self.progress_signal.emit(i + 1, self.count)
                    self.log(f'正在从天启HTTP提取代理IP (第{i + 1}个账号)...')
                    proxy_config = fetch_tianqi_proxy()
                    if not proxy_config:
                        self.log('⚠ 提取代理失败，等待3秒后重试...')
                        time.sleep(3)
                        proxy_config = fetch_tianqi_proxy()
                        if not proxy_config:
                            self.log('✗ 提取代理失败，跳过本次注册')
                            continue
                    self.log(f"使用代理: {proxy_config['server']}")
                    self.log(f'\n启动第 {i + 1} 个浏览器...')
                    with sync_playwright() as p:
                        context = p.chromium.launch_persistent_context(user_data_dir=fixed_user_data_dir, channel='chromium', headless=False, proxy=proxy_config, args=[f'--disable-extensions-except={EXTENSION_PATH}', f'--load-extension={EXTENSION_PATH}', '--disable-blink-features=AutomationControlled', '--ignore-certificate-errors'], viewport={'width': 1280, 'height': 720}, ignore_default_args=['--disable-extensions'])
                        time.sleep(3)
                        result = self.register_one_account(context, i + 1)
                        if result:
                            success_count += 1
                        self.log('关闭浏览器...')
                        context.close()
                        time.sleep(2)
                    if i < self.count - 1:
                        self.log(f'\n等待 {self.delay} 秒后开始下一个账号...')
                        time.sleep(self.delay)
                self.log(f"\n{'=================================================='}")
                self.log(f'批量注册完成！成功: {success_count}/{self.count}')
                self.log(f"{'=================================================='}")
                self.finished.emit(True, f'完成 {success_count}/{self.count} 个账号')
        except Exception as e:
            self.log(f'错误: {e}')
            self.finished.emit(False, str(e))
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Steam 账号批量自动注册工具')
        self.setFixedSize(650, 550)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 650) // 2
        y = (screen.height() - 550) // 2
        self.setGeometry(x, y, 650, 550)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        title = QLabel('Steam 账号批量自动注册工具')
        title.setFont(QFont('微软雅黑', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        settings_frame = QWidget()
        settings_frame.setStyleSheet('background-color: #ecf0f1; border-radius: 8px; padding: 10px;')
        settings_layout = QVBoxLayout(settings_frame)
        count_layout = QHBoxLayout()
        count_label = QLabel('注册数量:')
        count_label.setFont(QFont('微软雅黑', 10))
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(100)
        self.count_spin.setValue(1)
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_spin)
        count_layout.addStretch()
        delay_layout = QHBoxLayout()
        delay_label = QLabel('账号间隔(秒):')
        delay_label.setFont(QFont('微软雅黑', 10))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(5)
        self.delay_spin.setMaximum(60)
        self.delay_spin.setValue(10)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch()
        settings_layout.addLayout(count_layout)
        settings_layout.addLayout(delay_layout)
        layout.addWidget(settings_frame)
        self.progress_label = QLabel('等待开始...')
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        self.start_btn = QPushButton('▶ 开始批量注册')
        self.start_btn.setStyleSheet('\n            QPushButton {\n                background-color: #2980b9;\n                color: white;\n                border: none;\n                border-radius: 8px;\n                padding: 12px;\n                font-size: 12px;\n            }\n            QPushButton:hover { background-color: #3498db; }\n            QPushButton:disabled { background-color: #bdc3c7; }\n        ')
        self.start_btn.clicked.connect(self.start_registration)
        layout.addWidget(self.start_btn)
        log_label = QLabel('📋 运行日志:')
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('background-color: #2c3e50; color: #ecf0f1; border-radius: 5px;')
        layout.addWidget(self.log_text)
        self.status_label = QLabel('✅ 就绪')
        layout.addWidget(self.status_label)
        self.thread = None
    def start_registration(self):
        count = self.count_spin.value()
        delay = self.delay_spin.value()
        self.start_btn.setEnabled(False)
        self.log_text.clear()
        self.status_label.setText(f'⏳ 正在执行... (0/{count})')
        self.progress_label.setText(f'进度: 0/{count}')
        self.thread = BatchRegisterThread(count, delay)
        self.thread.log_signal.connect(self.append_log)
        self.thread.finished.connect(self.on_finished)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.start()
    def update_progress(self, current, total):
        self.progress_label.setText(f'进度: {current}/{total}')
        self.status_label.setText(f'⏳ 正在执行... ({current}/{total})')
    def on_finished(self, success, message):
        self.start_btn.setEnabled(True)
        if success:
            self.status_label.setText('✅ 完成！')
        else:
            self.status_label.setText('❌ 失败')
        self.append_log(f"{('✅' if success else '❌')} {message}")
    def append_log(self, msg):
        self.log_text.append(msg)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
def check_license_and_run():
    """检查卡密并运行主程序"""
    hwid = get_hardware_id()
    saved_license = load_license_key()
    if saved_license:
        result = verify_license_key(saved_license, hwid)
        if result.get('ok', False):
            heartbeat_thread = threading.Thread(target=license_background_check, args=(saved_license, hwid), daemon=True)
            heartbeat_thread.start()
            return True
    dialog = LicenseDialog()
    if dialog.exec_() == QDialog.Accepted:
        license_key = dialog.license_key
        if license_key:
            heartbeat_thread = threading.Thread(target=license_background_check, args=(license_key, hwid), daemon=True)
            heartbeat_thread.start()
            return True
    return False
def main():
    app = QApplication(sys.argv)
    if not check_license_and_run():
        QMessageBox.critical(None, '验证失败', '卡密验证失败，程序将退出！')
        sys.exit(1)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()