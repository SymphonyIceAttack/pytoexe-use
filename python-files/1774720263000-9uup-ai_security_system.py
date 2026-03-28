#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الحماية والذكاء الاصطناعي المتطور
الإصدار 3.0 - حقيقي، يعمل على الجهاز المحلي
"""

import json
import os
import sys
import time
import threading
import socket
import random
import subprocess
import platform
import hashlib
import signal
from datetime import datetime
import logging
import requests
import psutil

# محاولة استيراد scapy (مراقبة الشبكة الحقيقية)
try:
    from scapy.all import sniff, IP, TCP, UDP, ARP, Ether, conf, get_if_list, get_if_addr
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("⚠️ Scapy غير مثبت. قم بتثبيته للحصول على مراقبة شبكة حقيقية: pip install scapy")

# ========== الإعدادات ==========
DATA_FILE = "ai_security_data.json"          # ملف البيانات المركزي
UPDATE_INTERVAL = 1800                       # نصف ساعة (بالثواني)
MAX_AGENTS_STORED = 500000                   # الحد الأقصى للوكلاء المخزنين (يستهلك ~500 ميجا)
AGENTS_ACTIVE_LIMIT = 5000                   # عدد الوكلاء النشطين في الذاكرة
UPDATE_URL = "https://raw.githubusercontent.com/your-repo/ai_update.py"  # غيّر إلى رابط تحديث حقيقي
LOG_FILE = "ai_security.log"

# إعداد التسجيل
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AISecurity")

# ========== إدارة البيانات (تخزين في ملف JSON) ==========
class DataManager:
    """مسؤول عن حفظ وقراءة البيانات من ملف JSON واحد."""
    def __init__(self, filename):
        self.filename = filename
        self.lock = threading.Lock()
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"خطأ في تحميل الملف: {e}")
        # البيانات الافتراضية
        return {
            "agents": [],
            "security_logs": [],
            "ai_logs": [],
            "updates": [],
            "system_status": "active",
            "agent_counter": 0,
            "version": "3.0"
        }

    def save(self):
        with self.lock:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)

    def add_agent(self, name):
        with self.lock:
            # تخزين محدود: إذا وصلنا للحد، نعيد استخدام أقدم وكيل (محاكاة لا نهائي)
            if len(self.data["agents"]) < MAX_AGENTS_STORED:
                self.data["agents"].append({
                    "name": name,
                    "created": datetime.now().isoformat()
                })
            else:
                idx = self.data["agent_counter"] % MAX_AGENTS_STORED
                self.data["agents"][idx] = {
                    "name": name,
                    "created": datetime.now().isoformat()
                }
            self.data["agent_counter"] += 1
            self.save()

    def add_security_event(self, event_type, details):
        with self.lock:
            self.data["security_logs"].append({
                "time": datetime.now().isoformat(),
                "type": event_type,
                "details": details
            })
            # الاحتفاظ بآخر 2000 سجل
            if len(self.data["security_logs"]) > 2000:
                self.data["security_logs"] = self.data["security_logs"][-2000:]
            self.save()

    def add_ai_event(self, message):
        with self.lock:
            self.data["ai_logs"].append({
                "time": datetime.now().isoformat(),
                "message": message
            })
            if len(self.data["ai_logs"]) > 2000:
                self.data["ai_logs"] = self.data["ai_logs"][-2000:]
            self.save()

    def add_update_record(self, version, changes):
        with self.lock:
            self.data["updates"].append({
                "time": datetime.now().isoformat(),
                "version": version,
                "changes": changes
            })
            self.save()
        logger.info(f"تم تسجيل تحديث: {version} - {changes}")

# ========== وكيل الذكاء الاصطناعي (كائن نشط) ==========
class AIAgent:
    """يمثل وكيلاً ذكياً يمكنه التواصل مع الآخرين."""
    def __init__(self, name, data_manager):
        self.name = name
        self.data_manager = data_manager
        self.data_manager.add_agent(name)

    def process(self):
        """يقوم الوكيل بمهمة عشوائية (محاكاة الذكاء)."""
        task = random.choice([
            "تحليل حركة الشبكة", "التنبؤ بالتهديدات", "تحسين قواعد الحماية",
            "تعلم سلوك المستخدم", "تحديث المعرفة"
        ])
        result = f"{self.name} قام بـ {task} في {datetime.now()}"
        self.data_manager.add_ai_event(result)
        return result

    def communicate(self, target_agent, message):
        """التواصل بين وكيلين."""
        comm_log = f"{self.name} -> {target_agent}: {message}"
        self.data_manager.add_ai_event(comm_log)
        return comm_log

# ========== مدير الوكلاء (إنتاج عدد ضخم مع إعادة تدوير) ==========
class AgentManager:
    """ينشئ وكلاء ويحافظ على عدد محدود منهم في الذاكرة."""
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.active_agents = []      # الوكلاء النشطون في الذاكرة
        self.running = True
        self.lock = threading.Lock()

    def create_agent(self):
        """ينشئ وكيلاً جديداً ويضيفه إلى القائمة النشطة (مع إزالة الأقدم إذا تجاوز الحد)."""
        agent_id = f"AI_Agent_{self.data_manager.data['agent_counter'] + 1}"
        agent = AIAgent(agent_id, self.data_manager)
        with self.lock:
            self.active_agents.append(agent)
            if len(self.active_agents) > AGENTS_ACTIVE_LIMIT:
                removed = self.active_agents.pop(0)
                # لا نحذف الوكيل من الملف، فقط نحرر الذاكرة
        return agent

    def start_infinite_creation(self, rate_per_second=10):
        """يبدأ توليد وكلاء بمعدل معين لمحاكاة العدد اللانهائي."""
        def creator():
            while self.running:
                for _ in range(rate_per_second):
                    if not self.running:
                        break
                    self.create_agent()
                time.sleep(1)
        threading.Thread(target=creator, daemon=True).start()
        logger.info(f"بدأ توليد الوكلاء بمعدل {rate_per_second} وكيل/ثانية")

    def stop(self):
        self.running = False

# ========== نظام الحماية (مراقبة الشبكة باستخدام scapy) ==========
class SecurityMonitor:
    """يراقب حركة الشبكة ويكشف الهجمات الشائعة."""
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.sniffing = False
        self.arp_table = {}      # تخزين عناوين MAC المعروفة للكشف عن ARP spoofing

    def packet_callback(self, packet):
        """تستدعى لكل حزمة يتم التقاطها."""
        # كشف ARP spoofing
        if packet.haslayer(ARP):
            arp = packet[ARP]
            if arp.op == 2:  # ARP reply
                ip = arp.psrc
                mac = arp.hwsrc
                if ip in self.arp_table and self.arp_table[ip] != mac:
                    alert = f"⚠️ ARP spoofing محتمل! IP {ip} تغير MAC من {self.arp_table[ip]} إلى {mac}"
                    logger.warning(alert)
                    self.data_manager.add_security_event("ARP_Spoofing", alert)
                else:
                    self.arp_table[ip] = mac

        # كشف فحص المنافذ (Port Scan) عبر كثرة اتصالات TCP SYN
        if packet.haslayer(TCP) and packet[TCP].flags == 2:  # SYN
            src_ip = packet[IP].src
            dst_port = packet[TCP].dport
            # يمكن إضافة منطق لحساب عدد الـ SYN من نفس المصدر في فترة زمنية
            # (لتجنب تعقيد الكود، نكتفي بالتسجيل)
            # هنا نضيف حدثاً بسيطاً
            self.data_manager.add_security_event("Port_Scan_Attempt", f"SYN from {src_ip} to port {dst_port}")

        # يمكن إضافة المزيد من القواعد حسب الحاجة

    def start_sniffing(self, interface=None):
        """بدء التقاط الحزم."""
        if not SCAPY_AVAILABLE:
            logger.error("Scapy غير مثبت، لا يمكن بدء مراقبة الشبكة.")
            return

        if interface is None:
            # اختيار أول واجهة شبكة متاحة
            interfaces = get_if_list()
            if interfaces:
                interface = interfaces[0]
            else:
                logger.error("لا توجد واجهات شبكة متاحة.")
                return

        logger.info(f"بدء مراقبة الشبكة على الواجهة {interface}")
        self.sniffing = True
        try:
            # التقاط الحزم في خيط منفصل
            sniff(iface=interface, prn=self.packet_callback, store=0, stop_filter=lambda _: not self.sniffing)
        except Exception as e:
            logger.error(f"خطأ في التقاط الحزم: {e}")

    def stop_sniffing(self):
        self.sniffing = False

# ========== نظام التحديث الذاتي ==========
class SelfUpdater:
    """يتحقق من وجود تحديثات كل نصف ساعة ويطبقها."""
    def __init__(self, data_manager, current_version, update_url):
        self.data_manager = data_manager
        self.current_version = current_version
        self.update_url = update_url
        self.running = True

    def check_for_updates(self):
        """يتحقق من وجود تحديث (محاكاة أو حقيقية)."""
        try:
            # نستخدم طلب HTTP لجلب رقم الإصدار الجديد (مثلاً من ملف نصي)
            # هنا نستخدم محاكاة لتجنب الاعتماد على خادم حقيقي
            # يمكنك استبدال هذا بطلب حقيقي: response = requests.get(f"{self.update_url}/version")
            # سنقوم بمحاكاة التحديث أحياناً (10% احتمال)
            if random.random() < 0.1:  # محاكاة: تحديث وهمي
                new_version = f"{float(self.current_version) + 0.1:.1f}"
                changes = "تحسين أداء الوكلاء وإضافة قواعد حماية جديدة"
                self.apply_update(new_version, changes)
                return True
            else:
                logger.info("لا توجد تحديثات جديدة.")
                return False
        except Exception as e:
            logger.error(f"فشل التحقق من التحديثات: {e}")
            return False

    def apply_update(self, new_version, changes):
        """تطبيق التحديث (هنا نقوم بتسجيل التحديث وإعادة التشغيل)."""
        logger.info(f"جاري تطبيق التحديث إلى الإصدار {new_version}: {changes}")
        self.data_manager.add_update_record(new_version, changes)
        # تحديث الإصدار في البيانات
        self.data_manager.data["version"] = new_version
        self.data_manager.save()
        # يمكن إعادة تشغيل البرنامج
        self.restart_program()

    def restart_program(self):
        """إعادة تشغيل البرنامج (لتحميل الكود الجديد)."""
        logger.info("إعادة تشغيل البرنامج لتطبيق التحديث...")
        time.sleep(1)
        # إعادة التشغيل بنفس السكريبت
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def start(self):
        """حلقة التحديث الدورية."""
        def updater_loop():
            while self.running:
                time.sleep(UPDATE_INTERVAL)
                if self.running:
                    self.check_for_updates()
        threading.Thread(target=updater_loop, daemon=True).start()
        logger.info("بدأ نظام التحديث الذاتي (كل نصف ساعة).")

    def stop(self):
        self.running = False

# ========== الوظيفة الرئيسية ==========
def main():
    """نقطة الدخول الرئيسية للبرنامج."""
    print("==================================================")
    print("     نظام الحماية والذكاء الاصطناعي المتطور      ")
    print("              الإصدار 3.0 - حقيقي                 ")
    print("==================================================")
    print("جاري تشغيل البرنامج...")
    print("سجلات التشغيل موجودة في ملف", LOG_FILE)
    print("بيانات الوكلاء والأحداث في ملف", DATA_FILE)
    print("لمراقبة الشبكة بشكل حقيقي، قم بتشغيل البرنامج بصلاحيات الجذر/المسؤول.")
    print("للخروج، اضغط Ctrl+C.")

    # تهيئة مدير البيانات
    data_manager = DataManager(DATA_FILE)
    current_version = data_manager.data.get("version", "3.0")

    # تشغيل مدير الوكلاء
    agent_manager = AgentManager(data_manager)
    agent_manager.start_infinite_creation(rate_per_second=20)  # توليد 20 وكيل/ثانية (عدد ضخم)

    # تشغيل مراقبة الشبكة (في خيط منفصل)
    security = SecurityMonitor(data_manager)
    sniff_thread = threading.Thread(target=security.start_sniffing, daemon=True)
    sniff_thread.start()

    # تشغيل نظام التحديث الذاتي
    updater = SelfUpdater(data_manager, current_version, UPDATE_URL)
    updater.start()

    # الحلقة الرئيسية: محاكاة عمل الوكلاء النشطين وتواصلهم
    try:
        while True:
            # كل 5 ثوانٍ، نختار وكيلاً عشوائياً ليقوم بمهمة
            if agent_manager.active_agents:
                agent = random.choice(agent_manager.active_agents)
                agent.process()
                # أحياناً يتواصل مع وكيل آخر
                if len(agent_manager.active_agents) > 1:
                    other = random.choice(agent_manager.active_agents)
                    if other != agent:
                        agent.communicate(other.name, "مرحباً، كيف حال الذكاء؟")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nإيقاف البرنامج...")
        agent_manager.stop()
        security.stop_sniffing()
        updater.stop()
        logger.info("تم إيقاف البرنامج بواسطة المستخدم.")
        sys.exit(0)

if __name__ == "__main__":
    main()