"""
Advanced Market News Telegram Bot
---------------------------------
المهام:
1. متابعة الأخبار الاقتصادية والسياسية المهمة فور صدورها
2. تحليل تأثير كل خبر على الأسواق المالية (فوركس، ذهب، فضة، كريبتو)
3. تصنيف قوة التأثير: High, Medium, Low
4. إرسالها مباشرة إلى قناة أو حساب Telegram
"""

import requests
from bs4 import BeautifulSoup
from telegram import Bot
import schedule
import time

# ===== إعداد البوت =====
TOKEN = "8472807467:AAG08lbPY5kH2Kwp8Bg2y80LszeCB-UvPaU"
CHAT_ID = "@Alawade555"  # @MyChannel أو ID شخصي
bot = Bot(token=TOKEN)

# ===== دالة جلب الأخبار من Investing.com =====
def get_economic_news():
    url = "https://www.investing.com/economic-calendar/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    events = []
    rows = soup.find_all("tr", {"class": "js-event-item"})
    for row in rows[:15]:  # أول 15 خبر
        time_event = row.find("td", {"class": "first left"}).text.strip()
        currency = row.find("td", {"class": "left flagCur"}).text.strip()
        event_name = row.find("td", {"class": "event"}).text.strip()
        impact = row.find("td", {"class": "sentiment"}).text.strip()

        # تحليل التأثير المتقدم
        market_impact = analyze_impact(event_name, impact)

        events.append({
            "time": time_event,
            "currency": currency,
            "event": event_name,
            "impact": impact,
            "market_analysis": market_impact
        })
    return events

# ===== تحليل التأثير على الأسواق =====
def analyze_impact(event_name, impact_level):
    """تقدير التأثير على الأسواق المالية حسب نوع الحدث وقوته"""
    impact_map = {"High": "قوي", "Medium": "متوسط", "Low": "ضعيف"}
    impact_text = impact_map.get(impact_level, "غير معروف")

    if any(word in event_name for word in ["Fed", "FOMC"]):
        return f"USD/الذهب/الكريبتو: تحركات {impact_text} متوقعة"
    elif any(word in event_name for word in ["CPI", "Inflation", "Employment"]):
        return f"الدولار/الذهب/العملات: تحركات {impact_text} محتملة حسب البيانات"
    else:
        return f"تأثير {impact_text} على الأسواق المالية"

# ===== إرسال الأخبار للبوت =====
def send_news():
    news_list = get_economic_news()
    for news in news_list:
        message = (
            f"⏰ الوقت: {news['time']}\n"
            f"💱 العملة/السوق: {news['currency']}\n"
            f"📌 الحدث: {news['event']}\n"
            f"⚡ قوة التأثير: {news['impact']}\n"
            f"🧠 التحليل: {news['market_analysis']}"
        )
        bot.send_message(chat_id=CHAT_ID, text=message)

# ===== جدولة التحقق المستمر =====
# التحقق كل 5 دقائق للحصول على الأخبار فور صدورها
schedule.every(5).minutes.do(send_news)

print("البوت الذكي يعمل الآن... 🟢")

while True:
    schedule.run_pending()
    time.sleep(60)
