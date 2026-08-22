import socket
import threading
import asyncio
import json
import os
import time
import random
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import logging
import aiohttp

# ==================== CONFIG ====================
BOT_TOKEN = "8627116125:AAHPgb1t3TgP8h31e7NOy8SxTKw2iAKH6QM"
CHANNEL_ID = "@tntservercrack"
ADMIN_ID = 8401873347

# ✅ تنظیمات سرعت فوق‌العاده بالا
MAX_CONCURRENT_SCANS = 3  # تعداد کشورهای همزمان
SCAN_TIMEOUT = 1         # تایم‌اوت اتصال (بسیار سریع)
BATCH_SIZE = 399           # تعداد IP در هر بسته پردازشی

TARGET_PORTS = [80, 443, 3389, 22, 2053]

STATE_FILE = "scan_state.json"
MONITOR_UPDATE_INTERVAL = 5
CACHE_DIR = "ip_ranges_cache"
CACHE_EXPIRY_HOURS = 24

# ✅ لیست منابع با سیستم Fallback
IP_RANGE_SOURCES = [
    lambda code: f"https://www.ipdeny.com/ipblocks/data/countries/{code}.zone",
    lambda code: f"https://ipverse.net/ipblocks/data/countries/{code}.zone",
    lambda code: f"https://raw.githubusercontent.com/maaaaz/country-ip-blocks/main/{code}.txt",
    lambda code: f"https://raw.githubusercontent.com/FirexAngel/country-ip-blocks/main/{code}.txt",
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==================== COUNTRIES ====================
ALL_COUNTRIES = {
    "no": ("Norway", "🇳🇴"), "vn": ("Vietnam", "🇻🇳"), "us": ("United States", "🇺🇸"),
    "cn": ("China", "🇨🇳"), "jp": ("Japan", "🇯🇵"), "au": ("Australia", "🇦🇺"),
    "pt": ("Portugal", "🇵🇹"), "mx": ("Mexico", "🇲🇽"), "br": ("Brazil", "🇧🇷"),
    "in": ("India", "🇮🇳"), "nl": ("Netherlands", "🇳🇱"), "ir": ("Iran", "🇮🇷"),
    "tr": ("Turkey", "🇹🇷"), "pk": ("Pakistan", "🇵🇰"), "it": ("Italy", "🇮🇹"),
    "eg": ("Egypt", "🇪🇬"), "hk": ("Hong Kong", "🇭🇰"), "es": ("Spain", "🇪🇸"),
    "fr": ("France", "🇫🇷"), "ru": ("Russia", "🇷🇺"), "ua": ("Ukraine", "🇺🇦"),
    "kr": ("South Korea", "🇰🇷"), "de": ("Germany", "🇩🇪"), "gb": ("United Kingdom", "🇬🇧"),
    "il": ("Israel", "🇮🇱"), "my": ("Malaysia", "🇲🇾"), "id": ("Indonesia", "🇮🇩"),
    "bd": ("Bangladesh", "🇧🇩"), "co": ("Colombia", "🇨🇴"), "cl": ("Chile", "🇨🇱"),
    "by": ("Belarus", "🇧🇾"), "bg": ("Bulgaria", "🇧🇬"), "bh": ("Bahrain", "🇧🇭"),
    "sa": ("Saudi Arabia", "🇸🇦"), "ae": ("United Arab Emirates", "🇦🇪"),
    "sg": ("Singapore", "🇸🇬"), "tw": ("Taiwan", "🇹🇼"), "py": ("Paraguay", "🇵🇾"),
    "be": ("Belgium", "🇧🇪"), "cz": ("Czech Republic", "🇨🇿"),
    "se": ("Sweden", "🇸🇪"), "ro": ("Romania", "🇷🇴")
}

DEFAULT_SPLIT_COUNTRIES = {'us', 'cn', 'kr', 'de', 'gb', 'hk', 'ru', 'in', 'br'}

bot = AsyncTeleBot(BOT_TOKEN)
scan_control = {'stop_all': False, 'lock': threading.Lock()}
split_countries = set(DEFAULT_SPLIT_COUNTRIES)
current_pages = {}
status_message_id = {}

main_loop = None
skipped_countries = set()
skipped_countries_lock = threading.Lock()

# ==================== LIVE MONITOR ====================
class LiveMonitor:
    def __init__(self):
        self.active_jobs = {}
        self.lock = threading.Lock()
        self.monitor_msg_id = None
        self.chat_id = None
        self.task = None
        self.status_text = "در انتظار..."

    def add_job(self, job):
        with self.lock:
            job_id = f"{job.country_code}_{job.chunk_id if job.is_split else 'full'}"
            self.active_jobs[job_id] = job

    def remove_job(self, job):
        with self.lock:
            job_id = f"{job.country_code}_{job.chunk_id if job.is_split else 'full'}"
            self.active_jobs.pop(job_id, None)

    def get_job_by_country(self, country_code):
        with self.lock:
            for job_id, job in self.active_jobs.items():
                if job.country_code == country_code:
                    return job
        return None

    def set_status(self, text):
        self.status_text = text

    async def start_monitoring(self, chat_id):
        self.chat_id = chat_id
        try:
            msg = await bot.send_message(chat_id, "📊 **مانیتورینگ زنده**\nدر حال شروع...", parse_mode="Markdown")
            self.monitor_msg_id = msg.message_id
        except:
            pass
        self.task = asyncio.create_task(self._update_loop())

    async def stop_monitoring(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except:
                pass

    def _get_control_buttons(self):
        buttons = []
        with self.lock:
            # محدود کردن نمایش به 4 شغل آخر برای جلوگیری از شلوغی
            jobs_list = list(self.active_jobs.items())[-4:] 
            for job_id, job in jobs_list:
                flag = ALL_COUNTRIES.get(job.country_code, ("Unknown", "🌍"))[1]
                # ✅ دکمه‌های جدید: رد کردن، توقف، لغو، ارسال فوری
                row = [
                    types.InlineKeyboardButton(f"⏭️ Skip {flag}", callback_data=f"skip:{job.country_code}"),
                    types.InlineKeyboardButton(f"⏸️ Pause {flag}", callback_data=f"pause:{job.country_code}"),
                ]
                row.append(types.InlineKeyboardButton(f"⏹️ Cancel {flag}", callback_data=f"stop_country:{job.country_code}"))
                row.append(types.InlineKeyboardButton(f"📤 Send Now {flag}", callback_data=f"send_now:{job.country_code}"))
                buttons.append(row)
        return buttons

    async def _update_loop(self):
        while True:
            try:
                await asyncio.sleep(MONITOR_UPDATE_INTERVAL)
                with self.lock:
                    lines = ["📊 **مانیتورینگ زنده اسکن (Ultra Fast)**\n"]
                    lines.append(f"📌 وضعیت کلی: {self.status_text}\n")
                    if self.active_jobs:
                        # نمایش فقط 5 شغل فعال برای خوانایی بهتر
                        displayed_jobs = list(self.active_jobs.items())[:5]
                        for job_id, job in displayed_jobs:
                            flag = ALL_COUNTRIES.get(job.country_code, ("Unknown", "🌍"))[1]
                            status = f"بخش {job.chunk_id}" if job.is_split else "کامل"
                            pause_mark = "⏸️" if job.pause_flag else ""
                            
                            # ✅ نمایش پورت‌های هدف
                            ports_str = ", ".join(map(str, TARGET_PORTS))
                            
                            lines.append(f"{flag} **{job.country_name}** ({status}) {pause_mark}")
                            lines.append(f"   🔓 Found: `{len(job.open_ips)}` | 📡 Scanned: `{job.scanned_count}`")
                            lines.append(f"   🎯 Ports: `{ports_str}`")
                    text = "\n".join(lines)
                
                control_buttons = self._get_control_buttons()
                
                try:
                    if self.monitor_msg_id:
                        if control_buttons:
                            markup = types.InlineKeyboardMarkup(control_buttons)
                            await bot.edit_message_text(text, self.chat_id, self.monitor_msg_id, parse_mode="Markdown", reply_markup=markup)
                        else:
                            await bot.edit_message_text(text, self.chat_id, self.monitor_msg_id, parse_mode="Markdown")
                except Exception as e:
                    if "message is not modified" not in str(e):
                        logging.warning(f"Monitor update error: {e}")
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

monitor = LiveMonitor()

# ==================== STATE MANAGEMENT ====================
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_country_progress(country_code):
    state = load_state()
    if country_code not in state:
        state[country_code] = {"next_chunk": 1, "last_ip": None}
        save_state(state)
    return state[country_code]

def save_country_progress(country_code, last_ip=None):
    state = load_state()
    if country_code not in state:
        state[country_code] = {}
    state[country_code]["next_chunk"] = state[country_code].get("next_chunk", 1) + 1
    if last_ip:
        state[country_code]["last_ip"] = last_ip
    save_state(state)

def reset_state(country_code=None):
    state = load_state()
    if country_code:
        state.pop(country_code, None)
    else:
        state = {}
    save_state(state)

# ==================== UTILITIES ====================
def is_admin(user_id):
    return user_id == ADMIN_ID

# ✅ اسکنر غیرهمگام (Async) بسیار سریع
async def scan_ip_async(ip, port):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), 
            timeout=SCAN_TIMEOUT
        )
        writer.close()
        await writer.wait_closed()
        return f"{ip}:{port}"
    except:
        return None

class ScanJob:
    def __init__(self, country_code, country_name, ranges, is_split=False, chunk_id=0, start_from=None):
        self.country_code = country_code
        self.country_name = country_name
        self.ranges = ranges
        self.is_split = is_split
        self.chunk_id = chunk_id
        self.open_ips = []
        self.scanned_count = 0
        self.stop_flag = False
        self.pause_flag = False
        self.completed = False
        self.lock = threading.Lock()
        self.start_from = start_from

# ==================== DOWNLOAD WITH FALLBACK ====================
async def download_single_country(code, session):
    for source_func in IP_RANGE_SOURCES:
        url = source_func(code)
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    ranges = []
                    for line in text.strip().split('\n'):
                        line = line.strip()
                        if not line or line.startswith('#') or line.startswith('//'):
                            continue
                        if '/' in line:
                            try:
                                net = IPv4Network(line, strict=False)
                                ranges.append((int(net.network_address), int(net.broadcast_address)))
                            except:
                                continue
                    if ranges:
                        return ranges
        except:
            continue
    return []

async def download_all_country_ranges():
    os.makedirs(CACHE_DIR, exist_ok=True)
    country_ranges = {}
    timeout = aiohttp.ClientTimeout(total=20)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for code in ALL_COUNTRIES.keys():
            cache_file = os.path.join(CACHE_DIR, f"{code}.json")
            if os.path.exists(cache_file):
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < CACHE_EXPIRY_HOURS * 3600:
                    try:
                        with open(cache_file, 'r') as f:
                            ranges = json.load(f)
                            country_ranges[code] = ranges
                            continue
                    except:
                        pass
            tasks.append((code, download_single_country(code, session)))
        
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        
        for i, (code, _) in enumerate(tasks):
            if not isinstance(results[i], Exception) and results[i]:
                country_ranges[code] = results[i]
                try:
                    with open(os.path.join(CACHE_DIR, f"{code}.json"), 'w') as f:
                        json.dump(results[i], f)
                except:
                    pass
    
    return country_ranges

# ==================== SCAN & SEND ====================

# ✅ تابع اصلی اسکن با Asyncio Semaphores برای کنترل همزمانی
async def scan_worker_async(job, semaphore):
    global main_loop
    monitor.add_job(job)
    
    # تبدیل رنج‌ها به لیست flat اگر کوچک هستند، یا پیمایش هوشمند
    all_ips = []
    for start, end in job.ranges:
        current_start = start
        if job.start_from and IPv4Address(job.start_from) > IPv4Address(start):
            current_start = int(IPv4Address(job.start_from))
        
        # برای جلوگیری از مصرف رم زیاد، آی‌پی‌ها را دسته‌بندی می‌کنیم
        step = 1
        for ip_int in range(current_start, end + 1, step):
            if job.stop_flag or scan_control['stop_all']:
                break
            while job.pause_flag:
                await asyncio.sleep(1)
            
            ip_str = str(IPv4Address(ip_int))
            # ✅ انتخاب پورت رندوم
            port = random.choice(TARGET_PORTS)
            
            async with semaphore:
                result = await scan_ip_async(ip_str, port)
            
            if result:
                with job.lock:
                    job.open_ips.append(result)
                    # اگر به سقف رسید، ارسال کن
                    if job.is_split and len(job.open_ips) >= 1000: # سقف پایین‌تر برای ارسال سریع‌تر
                        last_ip = ip_str
                        if main_loop:
                            asyncio.run_coroutine_threadsafe(
                                send_result_to_channel(job, last_ip), 
                                main_loop
                            )
                        with job.lock:
                            job.open_ips.clear() # پاک کردن بعد از ارسال
            
            with job.lock:
                job.scanned_count += 1

    job.completed = True
    if job.open_ips:
        if main_loop:
            asyncio.run_coroutine_threadsafe(send_result_to_channel(job, None), main_loop)
    
    monitor.remove_job(job)


async def send_result_to_channel(job, last_ip=None):
    with job.lock:
        if not job.open_ips:
            return
        ips_to_send = list(job.open_ips)
        # نکته: اینجا لیست را پاک نمی‌کنیم مگر اینکه ارسال موفق باشد یا دستور خاصی باشد
        # اما برای جلوگیری از تکرار در ارسال‌های خودکار، بهتر است مدیریت شود.
        # در اینجا فرض می‌کنیم caller مسئول پاک کردن است یا ما پاک می‌کنیم.
        
    if not ips_to_send:
        return

    base_name = job.country_name.replace(' ', '_')
    filename = f"{base_name}_Part{job.chunk_id}_{CHANNEL_ID}.txt"
    temp_path = f"temp_{filename}"

    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            for ip_port in ips_to_send:
                f.write(ip_port + "\n")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        caption = (
            f"📥 لیست آی‌پی‌ها (Ultra Fast)\n"
            f"🌍 لوکیشن: {job.country_name}\n"
            f"🔓 تعداد: {len(ips_to_send)}\n"
            f"🎯 پورت‌ها: {', '.join(map(str, TARGET_PORTS))}\n"
            f"🕗 {timestamp}\n"
            f"📢 {CHANNEL_ID}"
        )

        with open(temp_path, 'rb') as doc:
            await bot.send_document(CHANNEL_ID, doc, caption=caption, visible_file_name=filename)

        if last_ip:
            save_country_progress(job.country_code, last_ip)
        
        # ✅ پاک کردن لیست بعد از ارسال موفق
        with job.lock:
            # فقط آی‌پی‌هایی که فرستادیم را حذف می‌کنیم
            # چون ممکن است در حین ارسال آی‌پی جدید اضافه شده باشد، بهتر است کل لیست را ریست کنیم
            # اگر last_ip داریم یعنی اسکن ادامه دارد، پس باید لیست فعلی را خالی کنیم
            job.open_ips.clear()

    except Exception as e:
        logging.error(f"Send error: {e}")
    finally:
        try:
            os.remove(temp_path)
        except:
            pass

# ==================== ADMIN PANEL ====================
def get_admin_panel_markup(page=0):
    markup = types.InlineKeyboardMarkup(row_width=2)
    country_list = list(ALL_COUNTRIES.items())
    total_pages = (len(country_list) + 20 - 1) // 20
    start = page * 20
    end = start + 20

    for code, (name, flag) in country_list[start:end]:
        mark = "❌" if code in split_countries else "✅"
        markup.add(types.InlineKeyboardButton(f"{mark} {flag} {name}", callback_data=f"toggle:{code}"))

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ قبلی", callback_data=f"page:{page-1}"))
    if page < total_pages - 1:
        nav.append(types.InlineKeyboardButton("بعدی ➡️", callback_data=f"page:{page+1}"))
    if nav:
        markup.row(*nav)

    markup.row(types.InlineKeyboardButton("🚀 START ULTRA SCAN", callback_data="start_scan"))
    markup.row(types.InlineKeyboardButton("🔄 Reset All State", callback_data="reset_all"))
    markup.row(types.InlineKeyboardButton("⏹ Stop Current Scan", callback_data="stop_scan"))
    return markup

# ==================== CALLBACKS ====================
@bot.message_handler(commands=['start', 'help', 'panel'])
async def cmd_start(message):
    if not is_admin(message.from_user.id):
        await bot.reply_to(message, "⛔️ Access Denied.")
        return
    current_pages[message.chat.id] = 0
    markup = get_admin_panel_markup(0)
    text = "🎛 **Admin Control Panel (Ultra Fast Mode)**\n\nپورت‌های هدف: 80, 443, 3389, 22, 2053"
    await bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(call):
    if not is_admin(call.from_user.id):
        await bot.answer_callback_query(call.id, "⛔️ Access Denied", show_alert=True)
        return
    data = call.data
    
    if data.startswith("skip:"):
        country_code = data.split(":")[1]
        job = monitor.get_job_by_country(country_code)
        if job:
            job.stop_flag = True
            with skipped_countries_lock:
                skipped_countries.add(country_code)
            await bot.answer_callback_query(call.id, f"⏭️ {ALL_COUNTRIES[country_code][0]} رد شد", show_alert=True)
        else:
            await bot.answer_callback_query(call.id, "❌ Job یافت نشد", show_alert=True)
        return
    
    elif data.startswith("pause:"):
        country_code = data.split(":")[1]
        job = monitor.get_job_by_country(country_code)
        if job:
            job.pause_flag = not job.pause_flag
            status = "⏸️ متوقف شد" if job.pause_flag else "▶️ ادامه یافت"
            await bot.answer_callback_query(call.id, f"{status} - {ALL_COUNTRIES[country_code][0]}", show_alert=True)
        else:
            await bot.answer_callback_query(call.id, "❌ Job یافت نشد", show_alert=True)
        return
    
    elif data.startswith("stop_country:"):
        country_code = data.split(":")[1]
        job = monitor.get_job_by_country(country_code)
        if job:
            job.stop_flag = True
            reset_state(country_code)
            await bot.answer_callback_query(call.id, f"⏹️ {ALL_COUNTRIES[country_code][0]} لغو و ریست شد", show_alert=True)
        else:
            await bot.answer_callback_query(call.id, "❌ Job یافت نشد", show_alert=True)
        return

    # ✅ هندلر جدید برای ارسال فوری
    elif data.startswith("send_now:"):
        country_code = data.split(":")[1]
        job = monitor.get_job_by_country(country_code)
        if job:
            await bot.answer_callback_query(call.id, f"📤 در حال ارسال داده‌های {ALL_COUNTRIES[country_code][0]}...", show_alert=False)
            if main_loop:
                asyncio.run_coroutine_threadsafe(send_result_to_channel(job, None), main_loop)
            else:
                await bot.answer_callback_query(call.id, "❌ خطا در دسترسی به لوپ اصلی", show_alert=True)
        else:
            await bot.answer_callback_query(call.id, "❌ Job یافت نشد", show_alert=True)
        return
    
    if data.startswith("toggle:"):
        code = data.split(":")[1]
        if code in split_countries:
            split_countries.remove(code)
            text = f"✅ {ALL_COUNTRIES[code][0]} - اسکن کامل"
        else:
            split_countries.add(code)
            text = f"❌ {ALL_COUNTRIES[code][0]} - تقسیم‌بندی"
        await bot.answer_callback_query(call.id, text, show_alert=True)
        page = current_pages.get(call.message.chat.id, 0)
        try:
            await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_markup(page))
        except:
            pass
    elif data.startswith("page:"):
        page = int(data.split(":")[1])
        current_pages[call.message.chat.id] = page
        try:
            await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_markup(page))
        except:
            pass
        await bot.answer_callback_query(call.id)
    elif data == "start_scan":
        await bot.answer_callback_query(call.id, "🚀 شروع اسکن فوق سریع")
        status_msg = await bot.send_message(call.message.chat.id, "🔄 در حال آماده‌سازی اسکن...", parse_mode="Markdown")
        status_message_id[call.message.chat.id] = status_msg.message_id
        asyncio.create_task(run_infinite_scan_loop(call.message.chat.id, status_msg.message_id))
    elif data == "reset_all":
        reset_state()
        await bot.answer_callback_query(call.id, "State Reset شد", show_alert=True)
    elif data == "stop_scan":
        scan_control['stop_all'] = True
        await bot.answer_callback_query(call.id, "⏹ Stop شد", show_alert=True)

# ==================== MAIN LOOP ====================
async def run_infinite_scan_loop(chat_id, status_msg_id):
    global scan_control, main_loop
    scan_control = {'stop_all': False, 'lock': threading.Lock()}
    main_loop = asyncio.get_event_loop()

    await monitor.start_monitoring(chat_id)
    monitor.set_status("📥 در حال دانلود رنج آی‌پی کشورها...")

    country_ranges = await download_all_country_ranges()

    if not country_ranges:
        await bot.edit_message_text("❌ هیچ رنج آی‌پی دانلود نشد.", chat_id, status_msg_id)
        await monitor.stop_monitoring()
        return

    await bot.edit_message_text(f"✅ دانلود کامل شد ({len(country_ranges)} کشور)", chat_id, status_msg_id)
    await asyncio.sleep(2)

    cycle_number = 1

    while not scan_control['stop_all']:
        with skipped_countries_lock:
            skipped_countries.clear()
        
        jobs = []
        
        for code, ranges in country_ranges.items():
            with skipped_countries_lock:
                if code in skipped_countries:
                    continue
            
            name = ALL_COUNTRIES[code][0]
            progress = get_country_progress(code)
            chunk_id = progress.get("next_chunk", 1)
            start_from = progress.get("last_ip")
            
            if start_from:
                last_range_end = ranges[-1][1]
                if IPv4Address(start_from) > IPv4Address(last_range_end):
                    reset_state(code)
                    progress = get_country_progress(code)
                    chunk_id = 1
                    start_from = None
            
            if code in split_countries:
                job = ScanJob(code, name, ranges, True, chunk_id, start_from)
            else:
                if chunk_id == 1:
                    job = ScanJob(code, name, ranges, False, 0, None)
                else:
                    continue
            
            jobs.append(job)

        if not jobs:
            cycle_number += 1
            await bot.send_message(chat_id, f"🔄 **سیکل {cycle_number} شروع شد!**", parse_mode="Markdown")
            for code in country_ranges.keys():
                reset_state(code)
            await asyncio.sleep(5)
            continue

        # ✅ ایجاد Semaphore برای کنترل تعداد اتصالات همزمان (مثلاً 2000 اتصال همزمان)
        semaphore = asyncio.Semaphore(2000)
        
        tasks = []
        for job in jobs:
            task = asyncio.create_task(scan_worker_async(job, semaphore))
            tasks.append(task)

        await bot.edit_message_text(
            f"🔄 **سیکل {cycle_number}** — اسکن {len(jobs)} کشور (Ultra Fast)", 
            chat_id, status_msg_id, parse_mode="Markdown"
        )

        # منتظر ماندن برای اتمام همه تسک‌ها
        await asyncio.gather(*tasks, return_exceptions=True)
        
        cycle_number += 1
        await bot.send_message(chat_id, f"✅ سیکل {cycle_number-1} تمام شد. شروع سیکل بعدی...", parse_mode="Markdown")
        await asyncio.sleep(3)

    await monitor.stop_monitoring()
    await bot.send_message(chat_id, "⏹ اسکن متوقف شد.")

if __name__ == "__main__":
    print("🤖 Bot is running (Ultra Fast Mode)...")
    asyncio.run(bot.polling(non_stop=True, timeout=60))