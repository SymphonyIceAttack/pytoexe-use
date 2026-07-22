import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import json
import calendar

# --- Настройки ---
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), "CryptoAccounting", "settings.json")
ACHIEVEMENTS_FILE = os.path.join(os.path.expanduser("~"), "CryptoAccounting", "achievements.json")
DEFAULT_SETTINGS = {
    "daily_limit": 5,
    "weekly_limit": 200000,
    "night_start": 23,
    "night_end": 6,
    "tax_rate": 13,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def load_achievements():
    """Загружает сохраненные достижения"""
    if os.path.exists(ACHIEVEMENTS_FILE):
        with open(ACHIEVEMENTS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_achievements(achievements):
    """Сохраняет достижения"""
    os.makedirs(os.path.dirname(ACHIEVEMENTS_FILE), exist_ok=True)
    with open(ACHIEVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(achievements), f, ensure_ascii=False, indent=2)

# --- База данных ---
DB_FOLDER = os.path.join(os.path.expanduser("~"), "CryptoAccounting")
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
DB_NAME = os.path.join(DB_FOLDER, "crypto.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA table_info(deals)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'currency' not in columns:
        c.execute('''CREATE TABLE IF NOT EXISTS deals_new
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      type TEXT,
                      currency TEXT,
                      amount REAL,
                      rate_rub REAL,
                      fee REAL,
                      comment TEXT)''')
        c.execute("SELECT * FROM deals")
        old_data = c.fetchall()
        for row in old_data:
            if len(row) == 7:
                c.execute("INSERT INTO deals_new (id, date, type, currency, amount, rate_rub, fee, comment) VALUES (?,?,?,?,?,?,?,?)",
                         (row[0], row[1], row[2], 'USDT', row[3], row[4], row[5], row[6]))
        c.execute("DROP TABLE IF EXISTS deals")
        c.execute("ALTER TABLE deals_new RENAME TO deals")
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS deals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      type TEXT,
                      currency TEXT,
                      amount REAL,
                      rate_rub REAL,
                      fee REAL,
                      comment TEXT)''')
    conn.commit()
    conn.close()

def add_deal(date, type_, currency, amount, rate_rub, fee, comment=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO deals (date, type, currency, amount, rate_rub, fee, comment) VALUES (?,?,?,?,?,?,?)",
              (date, type_, currency, amount, rate_rub, fee, comment))
    conn.commit()
    conn.close()

def get_all_deals():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM deals ORDER BY date DESC")
    data = c.fetchall()
    conn.close()
    return data

def get_deals_by_date_range(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM deals WHERE date >= ? AND date <= ? ORDER BY date DESC", (start_date, end_date))
    data = c.fetchall()
    conn.close()
    return data

def clear_all_deals():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM deals")
    conn.commit()
    conn.close()

def delete_deal_by_id(deal_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
    conn.commit()
    conn.close()

def delete_deals_by_date_range(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM deals WHERE date >= ? AND date <= ?", (start_date, end_date))
    conn.commit()
    conn.close()

def calculate_stats(deals_filtered=None):
    if deals_filtered is None:
        deals = get_all_deals()
    else:
        deals = deals_filtered
    
    stats = {
        "profit": 0,
        "count": len(deals),
        "buy": 0,
        "sell": 0,
        "fee": 0,
        "buy_count": 0,
        "sell_count": 0,
        "avg_amount": 0,
        "max_amount": 0,
        "min_amount": 0
    }
    
    if not deals:
        return stats
    
    total_buy = 0
    total_sell = 0
    total_fee = 0
    buy_count = 0
    sell_count = 0
    amounts = []
    
    for d in deals:
        if len(d) == 8:
            _, _, type_, currency, amount, rate_rub, fee, _ = d
        else:
            _, _, type_, amount, rate_rub, fee, _ = d
            currency = "USDT"
        
        if currency == "USDT":
            amount_rub = amount * rate_rub
            fee_rub = fee * rate_rub
        else:
            amount_rub = amount
            fee_rub = fee
        
        total_fee += fee_rub
        amounts.append(amount_rub)
        
        if type_ == "Покупка":
            total_buy += amount_rub
            buy_count += 1
        else:
            total_sell += amount_rub
            sell_count += 1
    
    stats["profit"] = total_sell - total_buy - total_fee
    stats["buy"] = total_buy
    stats["sell"] = total_sell
    stats["fee"] = total_fee
    stats["buy_count"] = buy_count
    stats["sell_count"] = sell_count
    stats["avg_amount"] = sum(amounts) / len(amounts) if amounts else 0
    stats["max_amount"] = max(amounts) if amounts else 0
    stats["min_amount"] = min(amounts) if amounts else 0
    
    return stats

def analyze_risk(deals_filtered=None, settings=None):
    if settings is None:
        settings = load_settings()
    
    if deals_filtered is None:
        deals = get_all_deals()
    else:
        deals = deals_filtered
    
    if not deals:
        return "🟢", ["Нет данных для анализа"], 0, []
    
    today = dt.now().date()
    last_7_days = (today - datetime.timedelta(days=7)).isoformat()
    today_str = today.isoformat()
    
    recent_deals = [d for d in deals if d[1] >= last_7_days]
    today_deals = [d for d in deals if d[1] >= today_str]
    
    risk_score = 0
    warnings = []
    recommendations = []
    
    if not recent_deals:
        return "🟢", ["✅ За 7 дней сделок нет — риск минимальный"], 0, []
    
    daily_limit = settings.get("daily_limit", 5)
    if len(today_deals) >= daily_limit:
        risk_score += 2
        warnings.append(f"⚠️ Сегодня уже {len(today_deals)} сделок (лимит {daily_limit})")
        recommendations.append(f"💡 Сегодня больше не совершайте сделок — лимит {daily_limit} в день")
    
    weekly_total = 0
    for d in recent_deals:
        if len(d) == 8:
            _, _, _, currency, amount, rate_rub, _, _ = d
        else:
            _, _, _, amount, rate_rub, _, _ = d
            currency = "USDT"
        
        if currency == "USDT":
            weekly_total += amount * rate_rub
        else:
            weekly_total += amount
    
    weekly_limit = settings.get("weekly_limit", 200000)
    if weekly_total > weekly_limit:
        risk_score += 3
        warnings.append(f"⚠️ Оборот за неделю: {weekly_total:,.0f} RUB (лимит {weekly_limit:,} RUB)")
        recommendations.append(f"💡 Снизьте оборот до {weekly_limit:,} RUB в неделю")
    
    buy_count = sum(1 for d in recent_deals if d[2] == "Покупка")
    sell_count = sum(1 for d in recent_deals if d[2] == "Продажа")
    
    if buy_count > 0 and sell_count == 0 and len(recent_deals) > 3:
        risk_score += 2
        warnings.append("⚠️ Только покупки без продаж — выглядит подозрительно")
        recommendations.append("💡 Добавьте продажи, чтобы балансировать активность")
    
    night_deals = 0
    for d in recent_deals:
        try:
            date_str = d[1]
            if " " in date_str:
                time_str = date_str.split(" ")[1]
                hour = int(time_str.split(":")[0])
                if settings.get("night_start", 23) <= hour or hour <= settings.get("night_end", 6):
                    night_deals += 1
        except:
            pass
    
    if night_deals > 2:
        risk_score += 2
        warnings.append(f"⚠️ {night_deals} ночных транзакций ({settings.get('night_start', 23)}:00-{settings.get('night_end', 6)}:00)")
        recommendations.append(f"💡 Избегайте сделок ночью — это привлекает внимание банков")
    
    amounts = []
    for d in recent_deals:
        if len(d) == 8:
            _, _, _, currency, amount, rate_rub, _, _ = d
        else:
            _, _, _, amount, rate_rub, _, _ = d
            currency = "USDT"
        
        if currency == "USDT":
            amounts.append(amount * rate_rub)
        else:
            amounts.append(amount)
    
    if amounts:
        avg_amount = sum(amounts) / len(amounts)
        if avg_amount > 200000:
            risk_score += 1
            warnings.append(f"⚠️ Средняя сумма: {avg_amount:,.0f} RUB (выше 200 000)")
            recommendations.append("💡 Дробите крупные суммы на несколько сделок")
    
    if amounts and len(amounts) > 1:
        max_amount = max(amounts)
        min_amount = min(amounts)
        if max_amount > min_amount * 10:
            risk_score += 1
            warnings.append(f"⚠️ Большой разброс сумм: от {min_amount:,.0f} до {max_amount:,.0f} RUB")
            recommendations.append("💡 Старайтесь делать сделки схожих сумм")
    
    if len(recent_deals) > 10:
        risk_score += 1
        warnings.append(f"⚠️ {len(recent_deals)} сделок за неделю — слишком много")
        recommendations.append(f"💡 Уменьшите количество сделок до 5-7 в неделю")
    
    if risk_score == 0:
        status = "🟢"
        warnings.append("✅ Риск минимальный — всё хорошо!")
        if not recommendations:
            recommendations.append("✅ Продолжайте в том же духе")
    elif risk_score <= 3:
        status = "🟡"
        warnings.append("⚠️ Средний риск — будьте осторожнее")
        if not recommendations:
            recommendations.append("💡 Проверьте рекомендации ниже")
    else:
        status = "🔴"
        warnings.append("🔴 ВЫСОКИЙ РИСК! Карту могут заблокировать")
        if not recommendations:
            recommendations.append("🚨 СРОЧНО: примите меры!")
    
    return status, warnings, risk_score, recommendations

def calculate_tax(profit):
    tax_rate = load_settings()["tax_rate"] / 100
    tax = profit * tax_rate if profit > 0 else 0
    return {
        "profit": profit,
        "tax_rate": load_settings()["tax_rate"],
        "tax": tax,
        "net_profit": profit - tax
    }

def plot_profit_chart(frame, deals_filtered=None):
    if deals_filtered is None:
        deals = get_all_deals()
    else:
        deals = deals_filtered
    
    if not deals:
        label = tk.Label(frame, text="Нет данных для графика", font=("Segoe UI", 16), bg='#1a1a2e', fg='#888888')
        label.pack(expand=True)
        return
    
    dates = []
    cumulative = []
    current = 0
    
    for d in reversed(deals):
        if len(d) == 8:
            _, date, type_, currency, amount, rate_rub, fee, _ = d
        else:
            _, date, type_, amount, rate_rub, fee, _ = d
            currency = "USDT"
        
        if currency == "USDT":
            amount_rub = amount * rate_rub
            fee_rub = fee * rate_rub
        else:
            amount_rub = amount
            fee_rub = fee
        
        if type_ == "Покупка":
            current -= amount_rub
        else:
            current += amount_rub
        current -= fee_rub
        dates.append(date)
        cumulative.append(current)
    
    fig, ax = plt.subplots(figsize=(8, 4), facecolor='#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    ax.plot(dates, cumulative, marker='o', linewidth=2.5, 
            color='#00d4ff' if cumulative[-1] > 0 else '#ff6b6b',
            markersize=8, markerfacecolor='#1a1a2e', markeredgewidth=2)
    ax.axhline(y=0, color='#444444', linewidth=1, linestyle='--')
    ax.set_title("📈 Кумулятивная прибыль (RUB)", fontsize=14, fontweight='bold', color='white')
    ax.set_xlabel("Дата", color='#aaaaaa', fontsize=11)
    ax.set_ylabel("Прибыль (RUB)", color='#aaaaaa', fontsize=11)
    ax.grid(True, alpha=0.2, color='#444444')
    ax.tick_params(colors='#aaaaaa', labelsize=10)
    
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

# --- ДОСТИЖЕНИЯ ---
def calculate_achievements(deals):
    """Рассчитывает достижения и возвращает только новые"""
    all_achievements = []
    count = len(deals)
    
    if count == 0:
        return []
    
    if count >= 1:
        all_achievements.append({"name": "🥉 Новичок", "desc": "Первая сделка!", "icon": "🥉"})
    if count >= 10:
        all_achievements.append({"name": "🥈 Активный", "desc": "10 сделок — ты в деле!", "icon": "🥈"})
    if count >= 50:
        all_achievements.append({"name": "🥇 Трейдер", "desc": "50 сделок — профи!", "icon": "🥇"})
    if count >= 100:
        all_achievements.append({"name": "💎 Крипто-кит", "desc": "100 сделок — легенда!", "icon": "💎"})
    
    stats = calculate_stats(deals)
    profit = stats['profit']
    
    if profit >= 1000:
        all_achievements.append({"name": "💵 Первая прибыль", "desc": "Заработал 1000+ RUB!", "icon": "💵"})
    if profit >= 10000:
        all_achievements.append({"name": "💰 Заработок", "desc": "Заработал 10 000+ RUB!", "icon": "💰"})
    if profit >= 50000:
        all_achievements.append({"name": "🤑 Профит", "desc": "Заработал 50 000+ RUB!", "icon": "🤑"})
    if profit >= 100000:
        all_achievements.append({"name": "💎 Магнат", "desc": "Заработал 100 000+ RUB!", "icon": "💎"})
    
    buy_count = sum(1 for d in deals if d[2] == "Покупка")
    sell_count = sum(1 for d in deals if d[2] == "Продажа")
    
    if buy_count >= 10:
        all_achievements.append({"name": "🟢 Покупатель", "desc": "10+ покупок!", "icon": "🟢"})
    if sell_count >= 10:
        all_achievements.append({"name": "🔴 Продавец", "desc": "10+ продаж!", "icon": "🔴"})
    if buy_count > 0 and sell_count > 0 and abs(buy_count - sell_count) <= 1:
        all_achievements.append({"name": "⚖️ Баланс", "desc": "Покупок и продаж поровну!", "icon": "⚖️"})
    
    if deals:
        dates = sorted(set([d[1].split()[0] for d in deals]))
        if len(dates) >= 3:
            streak = 1
            max_streak = 1
            for i in range(1, len(dates)):
                try:
                    prev = dt.strptime(dates[i-1], "%Y-%m-%d")
                    curr = dt.strptime(dates[i], "%Y-%m-%d")
                    if (curr - prev).days == 1:
                        streak += 1
                        max_streak = max(max_streak, streak)
                    else:
                        streak = 1
                except:
                    pass
            
            if max_streak >= 3:
                all_achievements.append({"name": "🔥 Стрик 3", "desc": "3 дня подряд — держи ритм!", "icon": "🔥"})
            if max_streak >= 7:
                all_achievements.append({"name": "🔥 Стрик 7", "desc": "7 дней подряд — ты машина!", "icon": "🔥"})
            if max_streak >= 30:
                all_achievements.append({"name": "🔥 Стрик 30", "desc": "30 дней подряд — легенда!", "icon": "🔥"})
    
    # Убираем дубликаты
    unique = []
    seen = set()
    for a in all_achievements:
        if a["name"] not in seen:
            seen.add(a["name"])
            unique.append(a)
    
    return unique

# --- GUI ---
class CryptoApp:
    def __init__(self, root):
        self.root = root
        root.title("🚀 CryptoAccounting v3.0 — Учет криптовалютных сделок")
        root.geometry("1400x1000")
        root.configure(bg='#1a1a2e')
        root.minsize(1200, 800)
        
        self.settings = load_settings()
        self.setup_styles()
        
        # Загружаем сохраненные достижения
        self.unlocked_achievements = load_achievements()
        self.last_achievement_count = len(self.unlocked_achievements)
        
        self.main_container = tk.Frame(root, bg='#1a1a2e')
        self.main_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        self.create_header()
        
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, pady=15)
        
        self.tab_add = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_add, text="➕ Добавить сделку")
        self.build_add_tab()
        
        self.tab_history = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_history, text="📋 История сделок")
        self.build_history_tab()
        
        self.tab_stats = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_stats, text="📊 Статистика и риск")
        self.build_stats_tab()
        
        self.tab_analytics = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_analytics, text="📈 Расширенная аналитика")
        self.build_analytics_tab()
        
        self.tab_calendar = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_calendar, text="📆 Календарь активности")
        self.build_calendar_tab()
        
        self.tab_achievements = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_achievements, text="🏆 Достижения")
        self.build_achievements_tab()
        
        self.tab_tax = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_tax, text="💰 Налоговый калькулятор")
        self.build_tax_tab()
        
        self.tab_settings = tk.Frame(self.notebook, bg='#1a1a2e')
        self.notebook.add(self.tab_settings, text="⚙️ Настройки")
        self.build_settings_tab()
        
        init_db()
        self.refresh_history()
        self.refresh_stats()
        self.refresh_analytics()
        self.refresh_calendar()
        self.refresh_achievements()
        self.refresh_tax()
    
    def create_header(self):
        header = tk.Frame(self.main_container, bg='#16213e', relief='ridge', bd=2)
        header.pack(fill='x', pady=(0, 10))
        
        title = tk.Label(header, text="🚀 CryptoAccounting", 
                         font=("Segoe UI", 26, "bold"), 
                         bg='#16213e', fg='#00d4ff')
        title.pack(side='left', padx=20, pady=15)
        
        subtitle = tk.Label(header, text="📊 Умный учет криптовалютных сделок с анализом рисков", 
                            font=("Segoe UI", 12), bg='#16213e', fg='#888888')
        subtitle.pack(side='left', padx=20)
        
        self.status_label = tk.Label(header, text="✅ Система готова", 
                                     font=("Segoe UI", 11), bg='#16213e', fg='#00ff88')
        self.status_label.pack(side='right', padx=20)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TNotebook', background='#1a1a2e', borderwidth=0)
        style.configure('TNotebook.Tab', background='#16213e', foreground='#aaaaaa', 
                       padding=[20, 10], font=('Segoe UI', 11))
        style.map('TNotebook.Tab', background=[('selected', '#0f3460')], 
                 foreground=[('selected', '#ffffff')])
        
        style.configure('Treeview', background='#16213e', foreground='#ffffff', 
                       fieldbackground='#16213e', font=('Segoe UI', 10))
        style.configure('Treeview.Heading', background='#0f3460', foreground='#ffffff',
                       font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', '#1a4a7a')])
        
        style.configure('TButton', background='#0f3460', foreground='white',
                       font=('Segoe UI', 10), padding=8)
        style.map('TButton', background=[('active', '#1a4a7a')])
    
    def create_card(self, parent, title, **kwargs):
        frame = tk.Frame(parent, bg='#16213e', relief='ridge', bd=2)
        frame.pack(**kwargs)
        if title:
            header = tk.Label(frame, text=title, font=("Segoe UI", 15, "bold"), 
                             bg='#16213e', fg='#00d4ff')
            header.pack(pady=(12, 8), padx=10)
            tk.Frame(frame, bg='#0f3460', height=2).pack(fill='x', padx=10)
        return frame
    
    def build_add_tab(self):
        container = tk.Frame(self.tab_add, bg='#1a1a2e')
        container.pack(expand=True)
        
        card = self.create_card(container, "📝 Новая сделка", pady=25, padx=30, fill='x')
        
        f = tk.Frame(card, bg='#16213e')
        f.pack(padx=40, pady=20)
        
        left_col = tk.Frame(f, bg='#16213e')
        left_col.pack(side='left', fill='both', expand=True, padx=10)
        
        right_col = tk.Frame(f, bg='#16213e')
        right_col.pack(side='left', fill='both', expand=True, padx=10)
        
        tk.Label(left_col, text="📅 Дата и время:", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff').pack(anchor='w', pady=8)
        self.date_entry = tk.Entry(left_col, width=30, font=("Segoe UI", 12),
                                   bg='#2a2a4a', fg='white', insertbackground='white')
        self.date_entry.pack(anchor='w', pady=5)
        self.date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        tk.Label(left_col, text="🔄 Тип сделки:", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff').pack(anchor='w', pady=8)
        type_frame = tk.Frame(left_col, bg='#16213e')
        type_frame.pack(anchor='w', pady=5)
        
        self.type_var = tk.StringVar(value="Покупка")
        tk.Radiobutton(type_frame, text="🟢 Покупка", variable=self.type_var, 
                      value="Покупка", bg='#16213e', fg='#00ff88', 
                      selectcolor='#2a2a4a', font=("Segoe UI", 11)).pack(side='left', padx=10)
        tk.Radiobutton(type_frame, text="🔴 Продажа", variable=self.type_var, 
                      value="Продажа", bg='#16213e', fg='#ff6b6b',
                      selectcolor='#2a2a4a', font=("Segoe UI", 11)).pack(side='left', padx=10)
        
        tk.Label(left_col, text="💱 Валюта:", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff').pack(anchor='w', pady=8)
        currency_frame = tk.Frame(left_col, bg='#16213e')
        currency_frame.pack(anchor='w', pady=5)
        
        self.currency_var = tk.StringVar(value="USDT")
        tk.Radiobutton(currency_frame, text="🇺🇸 USDT", variable=self.currency_var, 
                      value="USDT", bg='#16213e', fg='#00d4ff',
                      selectcolor='#2a2a4a', font=("Segoe UI", 11)).pack(side='left', padx=10)
        tk.Radiobutton(currency_frame, text="🇷🇺 RUB", variable=self.currency_var, 
                      value="RUB", bg='#16213e', fg='#ffd93d',
                      selectcolor='#2a2a4a', font=("Segoe UI", 11)).pack(side='left', padx=10)
        
        tk.Label(right_col, text="💰 Сумма:", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff').pack(anchor='w', pady=8)
        self.amount_entry = tk.Entry(right_col, width=25, font=("Segoe UI", 12),
                                     bg='#2a2a4a', fg='white', insertbackground='white')
        self.amount_entry.pack(anchor='w', pady=5)
        
        self.rate_label = tk.Label(right_col, text="💱 Курс (RUB за 1 USDT):", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff')
        self.rate_label.pack(anchor='w', pady=8)
        self.rate_entry = tk.Entry(right_col, width=25, font=("Segoe UI", 12),
                                   bg='#2a2a4a', fg='white', insertbackground='white')
        self.rate_entry.pack(anchor='w', pady=5)
        
        self.fee_label = tk.Label(right_col, text="💸 Комиссия (USDT):", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff')
        self.fee_label.pack(anchor='w', pady=8)
        self.fee_entry = tk.Entry(right_col, width=25, font=("Segoe UI", 12),
                                  bg='#2a2a4a', fg='white', insertbackground='white')
        self.fee_entry.pack(anchor='w', pady=5)
        self.fee_entry.insert(0, "0")
        
        tk.Label(right_col, text="📝 Комментарий:", font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff').pack(anchor='w', pady=8)
        self.comment_entry = tk.Entry(right_col, width=35, font=("Segoe UI", 12),
                                      bg='#2a2a4a', fg='white', insertbackground='white')
        self.comment_entry.pack(anchor='w', pady=5)
        
        self.currency_var.trace_add('write', self.on_currency_change)
        
        btn_frame = tk.Frame(f, bg='#16213e')
        btn_frame.pack(side='bottom', pady=20)
        
        tk.Button(btn_frame, text="💾 Сохранить сделку", command=self.save_deal,
                 bg='#00d4ff', fg='black', font=("Segoe UI", 13, "bold"),
                 padx=40, pady=12, cursor='hand2').pack()
    
    def on_currency_change(self, *args):
        if self.currency_var.get() == "USDT":
            self.rate_label.config(text="💱 Курс (RUB за 1 USDT):")
            self.fee_label.config(text="💸 Комиссия (USDT):")
            self.rate_entry.config(state='normal', bg='#2a2a4a')
            self.rate_entry.delete(0, tk.END)
        else:
            self.rate_label.config(text="💱 Курс (не нужен для RUB):")
            self.fee_label.config(text="💸 Комиссия (RUB):")
            self.rate_entry.config(state='disabled', bg='#1a1a2e')
            self.rate_entry.delete(0, tk.END)
            self.rate_entry.insert(0, "1")
    
    def save_deal(self):
        try:
            date = self.date_entry.get()
            type_ = self.type_var.get()
            currency = self.currency_var.get()
            amount = float(self.amount_entry.get())
            rate = float(self.rate_entry.get()) if currency == "USDT" else 1
            fee = float(self.fee_entry.get())
            comment = self.comment_entry.get()
        except ValueError:
            messagebox.showerror("Ошибка", "⚠️ Введите корректные числа")
            return
        
        add_deal(date, type_, currency, amount, rate, fee, comment)
        messagebox.showinfo("Успех", "✅ Сделка добавлена!")
        self.status_label.config(text="✅ Сделка добавлена", fg='#00ff88')
        self.refresh_history()
        self.refresh_stats()
        self.refresh_analytics()
        self.refresh_calendar()
        self.refresh_achievements()
        self.refresh_tax()
    
    def build_history_tab(self):
        filter_frame = tk.Frame(self.tab_history, bg='#16213e', relief='ridge', bd=2)
        filter_frame.pack(fill='x', padx=15, pady=15)
        
        tk.Label(filter_frame, text="🔍 Фильтр по дате", font=("Segoe UI", 14, "bold"),
                bg='#16213e', fg='#00d4ff').pack(pady=(12, 8))
        
        f = tk.Frame(filter_frame, bg='#16213e')
        f.pack(padx=15, pady=12)
        
        tk.Label(f, text="От:", bg='#16213e', fg='#ffffff', font=("Segoe UI", 11)).pack(side='left', padx=8)
        self.filter_start = tk.Entry(f, width=15, font=("Segoe UI", 11),
                                     bg='#2a2a4a', fg='white', insertbackground='white')
        self.filter_start.pack(side='left', padx=5)
        self.filter_start.insert(0, (dt.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        
        tk.Label(f, text="До:", bg='#16213e', fg='#ffffff', font=("Segoe UI", 11)).pack(side='left', padx=8)
        self.filter_end = tk.Entry(f, width=15, font=("Segoe UI", 11),
                                   bg='#2a2a4a', fg='white', insertbackground='white')
        self.filter_end.pack(side='left', padx=5)
        self.filter_end.insert(0, dt.now().strftime("%Y-%m-%d"))
        
        btn_frame = tk.Frame(f, bg='#16213e')
        btn_frame.pack(side='left', padx=15)
        
        tk.Button(btn_frame, text="🔍 Применить", command=self.apply_filter,
                 bg='#00d4ff', fg='black', font=("Segoe UI", 10, "bold"),
                 padx=15, pady=5, cursor='hand2').pack(side='left', padx=5)
        tk.Button(btn_frame, text="📋 Сбросить", command=self.clear_filter,
                 bg='#0f3460', fg='white', font=("Segoe UI", 10),
                 padx=15, pady=5, cursor='hand2').pack(side='left', padx=5)
        
        table_frame = tk.Frame(self.tab_history, bg='#1a1a2e')
        table_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        columns = ("ID", "Дата", "Тип", "Валюта", "Сумма", "Курс", "Комиссия", "Коммент")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        widths = [50, 180, 100, 80, 120, 110, 120, 250]
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        btn_frame = tk.Frame(self.tab_history, bg='#1a1a2e')
        btn_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Button(btn_frame, text="🗑️ Удалить выбранную", command=self.delete_selected,
                 bg='#ff6b6b', fg='white', font=("Segoe UI", 10, "bold"),
                 padx=15, pady=8, cursor='hand2').pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Очистить всё", command=self.clear_all,
                 bg='#ff6b6b', fg='white', font=("Segoe UI", 10, "bold"),
                 padx=15, pady=8, cursor='hand2').pack(side='left', padx=5)
        
        self.count_label = tk.Label(btn_frame, text="Всего: 0 сделок", 
                                   font=("Segoe UI", 11), bg='#1a1a2e', fg='#888888')
        self.count_label.pack(side='right', padx=15)
    
    def apply_filter(self):
        start = self.filter_start.get()
        end = self.filter_end.get()
        deals = get_deals_by_date_range(start, end)
        
        for row in self.tree.get_children():
            self.tree.delete(row)
        for d in deals:
            if len(d) == 8:
                self.tree.insert("", "end", values=(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]))
            else:
                self.tree.insert("", "end", values=(d[0], d[1], d[2], "USDT", d[3], d[4], d[5], d[6]))
        
        self.count_label.config(text=f"Всего: {len(deals)} сделок")
        self.refresh_stats_with_filter(deals)
        messagebox.showinfo("Фильтр", f"📊 Показано {len(deals)} сделок")
    
    def clear_filter(self):
        self.filter_start.delete(0, tk.END)
        self.filter_end.delete(0, tk.END)
        self.refresh_history()
        self.refresh_stats()
    
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "⚠️ Выберите сделку")
            return
        deal_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить сделку #{deal_id}?"):
            delete_deal_by_id(deal_id)
            self.status_label.config(text=f"🗑️ Сделка #{deal_id} удалена", fg='#ff6b6b')
            self.refresh_history()
            self.refresh_stats()
            self.refresh_analytics()
            self.refresh_calendar()
            self.refresh_achievements()
            self.refresh_tax()
    
    def clear_all(self):
        if messagebox.askyesno("ВНИМАНИЕ!", "Удалить ВСЕ сделки безвозвратно?"):
            clear_all_deals()
            self.status_label.config(text="🗑️ Вся история очищена", fg='#ff6b6b')
            self.refresh_history()
            self.refresh_stats()
            self.refresh_analytics()
            self.refresh_calendar()
            self.refresh_achievements()
            self.refresh_tax()
    
    def refresh_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        deals = get_all_deals()
        for d in deals:
            if len(d) == 8:
                self.tree.insert("", "end", values=(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]))
            else:
                self.tree.insert("", "end", values=(d[0], d[1], d[2], "USDT", d[3], d[4], d[5], d[6]))
        self.count_label.config(text=f"Всего: {len(deals)} сделок")
    
    def build_stats_tab(self):
        stats_container = tk.Frame(self.tab_stats, bg='#1a1a2e')
        stats_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        top_frame = tk.Frame(stats_container, bg='#1a1a2e')
        top_frame.pack(fill='x', pady=(0, 15))
        
        risk_frame = self.create_card(top_frame, "🚦 Риск блокировки карты", 
                                      side='left', fill='x', expand=True, padx=(0, 10))
        
        self.risk_label = tk.Label(risk_frame, text="Анализируем...", 
                                   font=("Segoe UI", 26, "bold"), bg='#16213e', fg='#00d4ff')
        self.risk_label.pack(pady=15)
        
        self.risk_details = tk.Label(risk_frame, text="", font=("Segoe UI", 12),
                                     bg='#16213e', fg='#aaaaaa', justify='left')
        self.risk_details.pack(pady=10)
        
        stats_frame = self.create_card(top_frame, "📊 Общая статистика", 
                                       side='left', fill='x', expand=True, padx=(10, 0))
        
        self.stats_label = tk.Label(stats_frame, text="Загрузка...", 
                                    font=("Segoe UI", 13), bg='#16213e', fg='#ffffff', justify='left')
        self.stats_label.pack(pady=20, padx=15)
        
        chart_frame = self.create_card(stats_container, "📈 График прибыли", pady=5, fill='both', expand=True)
        
        self.chart_frame = tk.Frame(chart_frame, bg='#1a1a2e')
        self.chart_frame.pack(fill='both', expand=True, padx=15, pady=15)
    
    def refresh_stats(self):
        deals = get_all_deals()
        self.refresh_stats_with_filter(deals)
    
    def refresh_stats_with_filter(self, deals_filtered):
        stats = calculate_stats(deals_filtered)
        
        profit = stats['profit']
        profit_color = '#00ff88' if profit >= 0 else '#ff6b6b'
        profit_emoji = '📈' if profit >= 0 else '📉'
        
        text = (f"{profit_emoji} Прибыль: {profit:+.2f} RUB\n"
                f"📊 Сделок: {stats['count']} (покупок: {stats['buy_count']}, продаж: {stats['sell_count']})\n"
                f"📈 Покупок: {stats['buy']:,.2f} RUB\n"
                f"📉 Продаж: {stats['sell']:,.2f} RUB\n"
                f"💸 Комиссий: {stats['fee']:,.2f} RUB")
        
        self.stats_label.config(text=text, fg=profit_color)
        
        status, warnings, score, recommendations = analyze_risk(deals_filtered, self.settings)
        self.risk_label.config(text=f"{status} Риск: {score}/10")
        
        color = '#00ff88' if status == "🟢" else '#ffd93d' if status == "🟡" else '#ff6b6b'
        self.risk_label.config(fg=color)
        
        warning_text = "\n".join(warnings)
        
        if recommendations:
            recommendations_text = "\n\n📌 Рекомендации:\n" + "\n".join(recommendations)
            self.risk_details.config(text=warning_text + recommendations_text)
        else:
            self.risk_details.config(text=warning_text)
        
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        plot_profit_chart(self.chart_frame, deals_filtered)
    
    def build_analytics_tab(self):
        container = tk.Frame(self.tab_analytics, bg='#1a1a2e')
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        top_frame = tk.Frame(container, bg='#1a1a2e')
        top_frame.pack(fill='x', pady=5)
        
        self.avg_amount_label = self._create_metric_card(top_frame, "📊 Средняя сумма", '#00d4ff')
        self.best_rate_label = self._create_metric_card(top_frame, "💱 Лучший курс", '#00ff88')
        self.total_fee_label = self._create_metric_card(top_frame, "💸 Комиссий всего", '#ffd93d')
        self.avg_daily_label = self._create_metric_card(top_frame, "📆 Сделок в день", '#ff6b6b')
        
        bottom_frame = self.create_card(container, "📋 Детальная аналитика", pady=10, fill='both', expand=True)
        
        self.analytics_text = tk.Label(bottom_frame, text="", font=("Segoe UI", 12),
                                       bg='#16213e', fg='#ffffff', justify='left')
        self.analytics_text.pack(pady=15, padx=20, anchor='w')
    
    def _create_metric_card(self, parent, title, color):
        card = self.create_card(parent, title, side='left', fill='x', expand=True, padx=5)
        label = tk.Label(card, text="-", font=("Segoe UI", 20, "bold"),
                         bg='#16213e', fg=color)
        label.pack(pady=15)
        return label
    
    def refresh_analytics(self):
        deals = get_all_deals()
        if not deals:
            for label in [self.avg_amount_label, self.best_rate_label, self.total_fee_label, self.avg_daily_label]:
                label.config(text="Нет данных")
            self.analytics_text.config(text="Нет данных для анализа")
            return
        
        stats = calculate_stats(deals)
        
        avg_amount = stats['avg_amount']
        self.avg_amount_label.config(text=f"{avg_amount:,.0f} RUB")
        
        best_rate = 0
        for d in deals:
            if len(d) == 8 and d[3] == "USDT" and d[5] > best_rate:
                best_rate = d[5]
            elif len(d) == 7 and d[4] > best_rate:
                best_rate = d[4]
        self.best_rate_label.config(text=f"{best_rate:.2f} RUB")
        
        total_fee = stats['fee']
        self.total_fee_label.config(text=f"{total_fee:,.2f} RUB")
        
        dates = set([d[1].split()[0] for d in deals])
        avg_daily = len(deals) / len(dates) if dates else 0
        self.avg_daily_label.config(text=f"{avg_daily:.1f}")
        
        text = f"""
📈 Статистика сделок:
  • Всего сделок: {stats['count']}
    - Покупок: {stats['buy_count']} ({stats['buy_count']/stats['count']*100:.1f}%)
    - Продаж: {stats['sell_count']} ({stats['sell_count']/stats['count']*100:.1f}%)

💰 Финансовые показатели (в RUB):
  • Общая сумма покупок: {stats['buy']:,.2f} RUB
  • Общая сумма продаж: {stats['sell']:,.2f} RUB
  • Чистая прибыль: {stats['profit']:+.2f} RUB
  • Средняя прибыль на сделку: {stats['profit']/stats['count']:,.2f} RUB

📊 Анализ сумм (в RUB):
  • Минимальная сумма: {stats['min_amount']:,.2f} RUB
  • Максимальная сумма: {stats['max_amount']:,.2f} RUB
  • Средняя сумма: {stats['avg_amount']:,.2f} RUB

💸 Комиссии:
  • Всего комиссий: {stats['fee']:,.2f} RUB
  • Средняя комиссия: {stats['fee']/stats['count']:,.2f} RUB

📆 Активность:
  • Уникальных дней: {len(dates)}
  • В среднем сделок в день: {avg_daily:.1f}
"""
        self.analytics_text.config(text=text)
    
    # ==================== КАЛЕНДАРЬ ====================
    def build_calendar_tab(self):
        container = tk.Frame(self.tab_calendar, bg='#1a1a2e')
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        top_frame = tk.Frame(container, bg='#1a1a2e')
        top_frame.pack(fill='x', pady=(0, 15))
        
        nav_frame = tk.Frame(top_frame, bg='#16213e', relief='ridge', bd=2)
        nav_frame.pack(pady=10)
        
        tk.Button(nav_frame, text="◀", command=self.prev_month,
                 bg='#0f3460', fg='white', font=("Segoe UI", 14),
                 padx=15, cursor='hand2').pack(side='left', padx=10, pady=5)
        
        self.month_label = tk.Label(nav_frame, text="", font=("Segoe UI", 16, "bold"),
                                    bg='#16213e', fg='#00d4ff', width=20)
        self.month_label.pack(side='left', padx=20, pady=5)
        
        tk.Button(nav_frame, text="▶", command=self.next_month,
                 bg='#0f3460', fg='white', font=("Segoe UI", 14),
                 padx=15, cursor='hand2').pack(side='left', padx=10, pady=5)
        
        tk.Button(nav_frame, text="📅 Сегодня", command=self.go_today,
                 bg='#00d4ff', fg='black', font=("Segoe UI", 11, "bold"),
                 padx=15, pady=5, cursor='hand2').pack(side='left', padx=15, pady=5)
        
        legend_frame = tk.Frame(top_frame, bg='#16213e', relief='ridge', bd=2)
        legend_frame.pack(pady=5)
        
        tk.Label(legend_frame, text="Легенда:", font=("Segoe UI", 11, "bold"),
                bg='#16213e', fg='white').pack(side='left', padx=10, pady=5)
        
        colors = [
            ('#2a2a2a', 'Нет сделок'),
            ('#00ff88', '1-2 сделки'),
            ('#ffd93d', '3-5 сделок'),
            ('#ff6b6b', '6+ сделок'),
        ]
        
        for color, label_text in colors:
            frame = tk.Frame(legend_frame, bg='#16213e')
            frame.pack(side='left', padx=10, pady=5)
            
            square = tk.Frame(frame, bg=color, width=20, height=20, relief='ridge', bd=1)
            square.pack(side='left')
            
            tk.Label(frame, text=label_text, font=("Segoe UI", 10),
                    bg='#16213e', fg='white').pack(side='left', padx=5)
        
        self.calendar_frame = tk.Frame(container, bg='#16213e', relief='ridge', bd=2)
        self.calendar_frame.pack(fill='both', expand=True, pady=10)
        
        self.current_date = dt.now()
        self.draw_calendar()
    
    def draw_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        year = self.current_date.year
        month = self.current_date.month
        
        self.month_label.config(text=f"{calendar.month_name[month]} {year}")
        
        cal_frame = tk.Frame(self.calendar_frame, bg='#16213e')
        cal_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for i, day in enumerate(days):
            tk.Label(cal_frame, text=day, font=("Segoe UI", 12, "bold"),
                    bg='#16213e', fg='#00d4ff', width=10, height=2,
                    relief='ridge', bd=1).grid(row=0, column=i, padx=2, pady=2)
        
        activity = self.get_month_activity(year, month)
        
        first_day = datetime.date(year, month, 1)
        start_weekday = first_day.weekday()
        days_in_month = calendar.monthrange(year, month)[1]
        
        row = 1
        col = start_weekday
        today = dt.now().date()
        
        for day in range(1, days_in_month + 1):
            date_obj = datetime.date(year, month, day)
            date_str = date_obj.isoformat()
            
            count = activity.get(date_str, 0)
            
            if count == 0:
                color = '#2a2a2a'
            elif count <= 2:
                color = '#00ff88'
            elif count <= 5:
                color = '#ffd93d'
            else:
                color = '#ff6b6b'
            
            cell = tk.Frame(cal_frame, bg=color, width=80, height=50, relief='ridge', bd=2)
            cell.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
            
            day_label = tk.Label(cell, text=str(day), font=("Segoe UI", 12, "bold"),
                                 bg=color, fg='white' if count > 0 else '#666666')
            day_label.pack(pady=2)
            
            if count > 0:
                count_label = tk.Label(cell, text=f"{count} 🟢" if count <= 2 else f"{count} 🟡" if count <= 5 else f"{count} 🔴",
                                       font=("Segoe UI", 9), bg=color, fg='white')
                count_label.pack()
            
            if date_obj == today:
                tk.Frame(cell, bg='#00d4ff', height=3).pack(fill='x', side='bottom')
            
            col += 1
            if col > 6:
                col = 0
                row += 1
        
        total_deals = sum(activity.values())
        active_days = len([d for d in activity.values() if d > 0])
        
        info_frame = tk.Frame(self.calendar_frame, bg='#16213e')
        info_frame.pack(fill='x', pady=10, padx=20)
        
        info_text = f"📊 За месяц: {total_deals} сделок  |  Активных дней: {active_days}  |  Дней без сделок: {days_in_month - active_days}"
        tk.Label(info_frame, text=info_text, font=("Segoe UI", 12),
                bg='#16213e', fg='#ffffff').pack()
    
    def get_month_activity(self, year, month):
        deals = get_all_deals()
        activity = {}
        
        for d in deals:
            date_str = d[1].split()[0]
            try:
                d_date = dt.strptime(date_str, "%Y-%m-%d").date()
                if d_date.year == year and d_date.month == month:
                    activity[date_str] = activity.get(date_str, 0) + 1
            except:
                pass
        
        return activity
    
    def prev_month(self):
        year = self.current_date.year
        month = self.current_date.month
        if month == 1:
            self.current_date = datetime.date(year - 1, 12, 1)
        else:
            self.current_date = datetime.date(year, month - 1, 1)
        self.draw_calendar()
    
    def next_month(self):
        year = self.current_date.year
        month = self.current_date.month
        if month == 12:
            self.current_date = datetime.date(year + 1, 1, 1)
        else:
            self.current_date = datetime.date(year, month + 1, 1)
        self.draw_calendar()
    
    def go_today(self):
        self.current_date = dt.now()
        self.draw_calendar()
    
    def refresh_calendar(self):
        self.draw_calendar()
    
    # ==================== ДОСТИЖЕНИЯ ====================
    def build_achievements_tab(self):
        container = tk.Frame(self.tab_achievements, bg='#1a1a2e')
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        header = tk.Label(container, text="🏆 Твои достижения", 
                          font=("Segoe UI", 28, "bold"), bg='#1a1a2e', fg='#ffd93d')
        header.pack(pady=(0, 10))
        
        self.achievement_count_label = tk.Label(container, text="", 
                                                font=("Segoe UI", 14), bg='#1a1a2e', fg='#00d4ff')
        self.achievement_count_label.pack(pady=(0, 15))
        
        self.achievements_frame = tk.Frame(container, bg='#1a1a2e')
        self.achievements_frame.pack(fill='both', expand=True)
    
    def refresh_achievements(self):
        deals = get_all_deals()
        all_achievements = calculate_achievements(deals)
        
        # Находим новые достижения (которых еще нет в сохраненных)
        new_achievements = []
        for a in all_achievements:
            if a["name"] not in self.unlocked_achievements:
                new_achievements.append(a)
                self.unlocked_achievements.add(a["name"])
        
        # Если есть новые — показываем уведомление и сохраняем
        if new_achievements:
            msg = "🎉 НОВЫЕ ДОСТИЖЕНИЯ!\n\n"
            for a in new_achievements:
                msg += f"{a['icon']} {a['name']}\n   {a['desc']}\n\n"
            messagebox.showinfo("🏆 НОВЫЕ ДОСТИЖЕНИЯ!", msg)
            self.status_label.config(text=f"🏆 +{len(new_achievements)} новых достижений!", fg='#ffd93d')
            save_achievements(self.unlocked_achievements)
        
        # Обновляем отображение
        for widget in self.achievements_frame.winfo_children():
            widget.destroy()
        
        self.achievement_count_label.config(text=f"🏅 Получено достижений: {len(self.unlocked_achievements)}")
        
        if not self.unlocked_achievements:
            tk.Label(self.achievements_frame, text="🚀 Сделай первую сделку, чтобы получить достижения!", 
                    font=("Segoe UI", 18), bg='#1a1a2e', fg='#888888').pack(expand=True)
            return
        
        # Показываем все сохраненные достижения
        col = 0
        row = 0
        for achievement_name in sorted(self.unlocked_achievements):
            # Ищем полную информацию о достижении
            achievement = next((a for a in all_achievements if a["name"] == achievement_name), None)
            if achievement is None:
                continue
            
            card = tk.Frame(self.achievements_frame, bg='#16213e', relief='ridge', bd=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            icon = tk.Label(card, text=achievement["icon"], font=("Segoe UI", 40),
                            bg='#16213e', fg='#ffd93d')
            icon.pack(pady=(15, 5))
            
            name = tk.Label(card, text=achievement["name"], font=("Segoe UI", 14, "bold"),
                            bg='#16213e', fg='#ffffff')
            name.pack()
            
            desc = tk.Label(card, text=achievement["desc"], font=("Segoe UI", 11),
                            bg='#16213e', fg='#888888')
            desc.pack(pady=(0, 15))
            
            if "Стрик" in achievement["name"] or "Магнат" in achievement["name"] or "Крипто-кит" in achievement["name"]:
                tk.Frame(card, bg='#ffd93d', height=3).pack(fill='x', side='bottom')
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        for i in range(3):
            self.achievements_frame.grid_columnconfigure(i, weight=1)
    
    # ===================================================
    
    def build_tax_tab(self):
        container = tk.Frame(self.tab_tax, bg='#1a1a2e')
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        card = self.create_card(container, "💰 Налоговый калькулятор", pady=25, fill='x')
        
        f = tk.Frame(card, bg='#16213e')
        f.pack(padx=30, pady=20)
        
        self.tax_info = tk.Label(f, text="", font=("Segoe UI", 14), 
                                 bg='#16213e', fg='#ffffff', justify='left')
        self.tax_info.pack(pady=15)
        
        btn_frame = tk.Frame(f, bg='#16213e')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="📥 Сохранить отчет для ФНС", command=self.save_tax_report,
                 bg='#00d4ff', fg='black', font=("Segoe UI", 12, "bold"),
                 padx=30, pady=12, cursor='hand2').pack()
    
    def refresh_tax(self):
        deals = get_all_deals()
        stats = calculate_stats(deals)
        tax_data = calculate_tax(stats['profit'])
        
        text = f"""
📊 Прибыль: {tax_data['profit']:,.2f} RUB
📋 Налоговая ставка: {tax_data['tax_rate']}%
💰 Налог к уплате: {tax_data['tax']:,.2f} RUB
💎 Чистая прибыль после налога: {tax_data['net_profit']:,.2f} RUB

{'✅ Налог рассчитан по ставке 13%' if tax_data['profit'] > 0 else '⚠️ Прибыли нет — налог не начисляется'}
"""
        self.tax_info.config(text=text)
    
    def save_tax_report(self):
        deals = get_all_deals()
        stats = calculate_stats(deals)
        tax_data = calculate_tax(stats['profit'])
        
        if not deals:
            messagebox.showwarning("Нет данных", "Нет сделок для отчета")
            return
        
        report_data = []
        for d in deals:
            if len(d) == 8:
                _, date, type_, currency, amount, rate_rub, fee, comment = d
            else:
                _, date, type_, amount, rate_rub, fee, comment = d
                currency = "USDT"
            
            if currency == "USDT":
                amount_rub = amount * rate_rub
                fee_rub = fee * rate_rub
            else:
                amount_rub = amount
                fee_rub = fee
            
            report_data.append({
                "Дата": date,
                "Тип": type_,
                "Валюта": currency,
                "Сумма": amount,
                "Курс (RUB)": rate_rub if currency == "USDT" else "-",
                "Сумма (RUB)": amount_rub,
                "Комиссия": fee,
                "Комиссия (RUB)": fee_rub,
                "Комментарий": comment
            })
        
        df = pd.DataFrame(report_data)
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"Налоговый_отчет_{dt.now().strftime('%Y-%m-%d')}.xlsx"
        )
        
        if file_path:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Сделки', index=False)
                
                summary = pd.DataFrame({
                    "Показатель": ["Прибыль", "Налоговая ставка", "Налог к уплате", "Чистая прибыль"],
                    "Значение": [
                        f"{tax_data['profit']:,.2f} RUB",
                        f"{tax_data['tax_rate']}%",
                        f"{tax_data['tax']:,.2f} RUB",
                        f"{tax_data['net_profit']:,.2f} RUB"
                    ]
                })
                summary.to_excel(writer, sheet_name='Сводка', index=False)
            
            messagebox.showinfo("Успех", f"✅ Отчет сохранен!\nПрибыль: {tax_data['profit']:,.2f} RUB\nНалог: {tax_data['tax']:,.2f} RUB")
            self.status_label.config(text="📥 Отчет сохранен", fg='#00ff88')
    
    def build_settings_tab(self):
        container = tk.Frame(self.tab_settings, bg='#1a1a2e')
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        card = self.create_card(container, "⚙️ Настройки уведомлений и рисков", pady=25, fill='x')
        
        f = tk.Frame(card, bg='#16213e')
        f.pack(padx=40, pady=20)
        
        settings_fields = [
            ("📊 Максимум сделок в день:", "daily_limit", 10, 5),
            ("💵 Максимальный оборот за неделю (RUB):", "weekly_limit", 15, 200000),
            ("🌙 Ночное время (с):", "night_start", 5, 23),
            ("🌙 Ночное время (до):", "night_end", 5, 6),
            ("💰 Налоговая ставка (%):", "tax_rate", 5, 13),
        ]
        
        self.settings_entries = {}
        for i, (label_text, key, width, default) in enumerate(settings_fields):
            tk.Label(f, text=label_text, font=("Segoe UI", 12),
                    bg='#16213e', fg='#ffffff').grid(row=i, column=0, sticky='w', pady=10, padx=5)
            entry = tk.Entry(f, width=width, font=("Segoe UI", 12),
                             bg='#2a2a4a', fg='white', insertbackground='white')
            entry.grid(row=i, column=1, pady=10, padx=5, sticky='w')
            entry.insert(0, str(self.settings.get(key, default)))
            self.settings_entries[key] = entry
        
        btn_frame = tk.Frame(f, bg='#16213e')
        btn_frame.grid(row=len(settings_fields), column=0, columnspan=2, pady=25)
        
        tk.Button(btn_frame, text="💾 Сохранить настройки", command=self.save_settings,
                 bg='#00d4ff', fg='black', font=("Segoe UI", 12, "bold"),
                 padx=30, pady=10, cursor='hand2').pack()
    
    def save_settings(self):
        try:
            self.settings["daily_limit"] = int(self.settings_entries["daily_limit"].get())
            self.settings["weekly_limit"] = float(self.settings_entries["weekly_limit"].get())
            self.settings["night_start"] = int(self.settings_entries["night_start"].get())
            self.settings["night_end"] = int(self.settings_entries["night_end"].get())
            self.settings["tax_rate"] = float(self.settings_entries["tax_rate"].get())
        except ValueError:
            messagebox.showerror("Ошибка", "⚠️ Введите корректные числа")
            return
        
        save_settings(self.settings)
        messagebox.showinfo("Успех", "✅ Настройки сохранены!")
        self.status_label.config(text="⚙️ Настройки обновлены", fg='#00ff88')
        self.refresh_stats()

# --- Запуск ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoApp(root)
    root.mainloop()