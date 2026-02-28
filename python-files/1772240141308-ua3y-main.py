import streamlit as st
from datetime import datetime
import time
from auth import Authentication
from database import Database
from helpers import load_css
from modules.products import products_module
from modules.purchase import purchase_module
from modules.sales import sales_module
from modules.customers import customers_module
from modules.warehouse import warehouse_module
from modules.employees import employees_module
from modules.expenses import expenses_module
from modules.users import users_module
from modules.reports import reports_module

# نسخه سیستم
VERSION = "1.0.0.0"

def show_login_page(auth):
    """نمایش صفحه لاگین"""
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #1e3a8a; font-size: 36px;">🧼 سیستم مدیریت کارخانه مواد شوینده</h1>
        <p style="color: #666; font-size: 16px;">نسخه {VERSION} | آخرین به‌روزرسانی: {datetime.now().strftime('%Y/%m/%d')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # استفاده از سه ستون برای قرار دادن فرم در وسط
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                color: white;
                margin-bottom: 20px;
            ">
                <h2 style="text-align: center; margin-bottom: 10px;">🔐 ورود به سیستم</h2>
                <p style="text-align: center; opacity: 0.9;">لطفا اطلاعات حساب کاربری خود را وارد نمایید</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    username = st.text_input("👤 نام کاربری", 
                                           placeholder="نام کاربری",
                                           help="نام کاربری خود را وارد کنید")
                with col_b:
                    password = st.text_input("🔒 رمز عبور", 
                                           type="password",
                                           placeholder="••••••••",
                                           help="رمز عبور خود را وارد کنید")
                
                # دکمه‌های فرم
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_btn = st.form_submit_button("🚪 ورود به سیستم", 
                                                    type="primary",
                                                    use_container_width=True)
                with col_btn2:
                    reset_btn = st.form_submit_button("🔄 بازنشانی", 
                                                    type="secondary",
                                                    use_container_width=True)
                
                if login_btn:
                    if not username or not password:
                        st.error("❌ لطفاً نام کاربری و رمز عبور را وارد کنید")
                    else:
                        with st.spinner("در حال احراز هویت..."):
                            time.sleep(0.5)
                            user = auth.authenticate(username, password)
                            if user:
                                st.session_state.logged_in = True
                                st.session_state.user_id = user[0]
                                st.session_state.username = user[1]
                                st.session_state.role = user[2]
                                st.session_state.full_name = user[3]
                                st.success(f"✅ ورود موفقیت‌آمیز! خوش آمدید {user[3]}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ نام کاربری یا رمز عبور اشتباه است")
                
                if reset_btn:
                    st.rerun()
    
    # اطلاعات تماس در فوتر
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 15px;
        text-align: center;
        font-size: 14px;
    ">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div>
                <strong>📞 پشتیبانی فنی:</strong> 0774616327(+93)
            </div>
            <div>
                <strong>📧 ایمیل:</strong> ajoya028@gmail.com
            </div>
            <div>
                <strong>🕒 ساعات کاری:</strong> ۸:۰۰ صبح تا ۴:۰۰ عصر
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_main_dashboard(db):
    """نمایش داشبورد اصلی با آمار و نمودارها"""
    cursor = db.conn.cursor()
    
    # ردیف اول: کارت‌های آماری
    st.markdown("### 📈 آمار کلی سیستم")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        product_count = cursor.fetchone()[0]
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 10px;">
            <div style="font-size: 14px; color: #666;">🏷️ محصولات فعال</div>
            <div style="font-size: 32px; font-weight: bold; color: #1e3a8a;">{product_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_active = 1")
        customer_count = cursor.fetchone()[0]
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #10b981; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 10px;">
            <div style="font-size: 14px; color: #666;">👥 مشتریان فعال</div>
            <div style="font-size: 32px; font-weight: bold; color: #1e3a8a;">{customer_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        cursor.execute("SELECT SUM(quantity_in_stock) FROM products WHERE is_active = 1")
        total_stock = cursor.fetchone()[0] or 0
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #f59e0b; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 10px;">
            <div style="font-size: 14px; color: #666;">📦 موجودی کل</div>
            <div style="font-size: 32px; font-weight: bold; color: #1e3a8a;">{total_stock:,.0f}</div>
            <div style="font-size: 12px; color: #28a745;">واحد</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        cursor.execute("SELECT SUM(total_price) FROM sales WHERE DATE(sale_date) = DATE('now')")
        today_sales = cursor.fetchone()[0] or 0
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #ef4444; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 10px;">
            <div style="font-size: 14px; color: #666;">💰 فروش امروز</div>
            <div style="font-size: 32px; font-weight: bold; color: #1e3a8a;">{today_sales:,.0f}</div>
            <div style="font-size: 12px; color: #28a745;">افغانی</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ردیف دوم: هشدارها و اعلان‌ها
    st.markdown("### ⚠️ هشدارها و اعلان‌ها")
    col_alert1, col_alert2 = st.columns(2)
    
    with col_alert1:
        cursor.execute('''
            SELECT name, quantity_in_stock, min_stock_level 
            FROM products 
            WHERE quantity_in_stock < min_stock_level AND is_active = 1
            ORDER BY (quantity_in_stock * 100.0 / min_stock_level)
            LIMIT 5
        ''')
        low_stock = cursor.fetchall()
        
        if low_stock:
            st.markdown('<div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 10px; padding: 15px; margin: 10px 0;">', unsafe_allow_html=True)
            st.markdown("**📦 محصولات با موجودی کم:**")
            for product in low_stock:
                name, stock, min_stock = product
                percentage = (stock / min_stock) * 100 if min_stock > 0 else 0
                st.progress(int(percentage), text=f"{name}: {stock} از {min_stock}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background: #d4edda; border: 1px solid #28a745; border-radius: 10px; padding: 15px; margin: 10px 0;">', unsafe_allow_html=True)
            st.markdown("✅ تمام موجودی‌ها در سطح مناسب هستند")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col_alert2:
        cursor.execute('''
            SELECT COUNT(*) FROM sales 
            WHERE DATE(sale_date) = DATE('now', '-1 day')
        ''')
        yesterday_sales_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM sales 
            WHERE DATE(sale_date) = DATE('now')
        ''')
        today_sales_count = cursor.fetchone()[0]
        
        st.markdown('<div style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">', unsafe_allow_html=True)
        st.markdown("**📊 فعالیت روزانه:**")
        st.markdown(f"- دیروز: {yesterday_sales_count} تراکنش")
        st.markdown(f"- امروز: {today_sales_count} تراکنش")
        
        if today_sales_count > yesterday_sales_count:
            st.success(f"📈 رشد: +{today_sales_count - yesterday_sales_count}")
        elif today_sales_count < yesterday_sales_count:
            st.warning(f"📉 کاهش: {yesterday_sales_count - today_sales_count}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ردیف سوم: آخرین تراکنش‌ها
    st.markdown("### 🔄 آخرین فعالیت‌ها")
    tab1, tab2, tab3 = st.tabs(["🛒 آخرین فروش‌ها", "📦 آخرین خریدها", "📝 آخرین مصارف"])
    
    with tab1:
        try:
            # ابتدا سعی می‌کنیم با ستون payment_status کوئری بزنیم
            cursor.execute('''
                SELECT s.id, s.sale_date, c.name as customer_name, 
                       s.product_name, s.quantity, s.total_price,
                       s.payment_type, s.payment_status
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                ORDER BY s.sale_date DESC 
                LIMIT 10
            ''')
            recent_sales = cursor.fetchall()
        except Exception as e:
            # اگر ستون payment_status وجود نداشت، بدون آن کوئری می‌زنیم
            try:
                cursor.execute('''
                    SELECT s.id, s.sale_date, c.name as customer_name, 
                           s.product_name, s.quantity, s.total_price,
                           s.payment_type
                    FROM sales s
                    LEFT JOIN customers c ON s.customer_id = c.id
                    ORDER BY s.sale_date DESC 
                    LIMIT 10
                ''')
                recent_sales = cursor.fetchall()
                
                # تبدیل به فرمت یکسان
                new_recent_sales = []
                for sale in recent_sales:
                    new_recent_sales.append(list(sale) + [''])
                recent_sales = new_recent_sales
            except Exception as e2:
                # اگر مشکل دیگری بود، ساده‌ترین کوئری را اجرا می‌کنیم
                cursor.execute('''
                    SELECT id, sale_date, 'مشتری' as customer_name, 
                           product_name, quantity, total_price,
                           'نقدی' as payment_type, 'پرداخت شده' as payment_status
                    FROM sales 
                    ORDER BY sale_date DESC 
                    LIMIT 10
                ''')
                recent_sales = cursor.fetchall()
        
        if recent_sales:
            sales_data = []
            for sale in recent_sales:
                # بررسی طول لیست sale
                if len(sale) >= 8:
                    sales_data.append({
                        "شناسه": sale[0],
                        "تاریخ": sale[1],
                        "مشتری": sale[2] if sale[2] else "بدون نام",
                        "محصول": sale[3],
                        "تعداد": sale[4],
                        "مبلغ": f"{sale[5]:,.0f}" if sale[5] else "0",
                        "نوع پرداخت": sale[6] if len(sale) > 6 else "نقدی",
                        "وضعیت": sale[7] if len(sale) > 7 else "پرداخت شده"
                    })
                elif len(sale) >= 7:
                    sales_data.append({
                        "شناسه": sale[0],
                        "تاریخ": sale[1],
                        "مشتری": sale[2] if sale[2] else "بدون نام",
                        "محصول": sale[3],
                        "تعداد": sale[4],
                        "مبلغ": f"{sale[5]:,.0f}" if sale[5] else "0",
                        "نوع پرداخت": sale[6] if len(sale) > 6 else "نقدی",
                        "وضعیت": "پرداخت شده"
                    })
                else:
                    # حداقل اطلاعات را نمایش می‌دهیم
                    sales_data.append({
                        "شناسه": sale[0] if len(sale) > 0 else "-",
                        "تاریخ": sale[1] if len(sale) > 1 else "-",
                        "مشتری": sale[2] if len(sale) > 2 else "بدون نام",
                        "محصول": sale[3] if len(sale) > 3 else "-",
                        "تعداد": sale[4] if len(sale) > 4 else "0",
                        "مبلغ": f"{sale[5]:,.0f}" if len(sale) > 5 and sale[5] else "0",
                        "نوع پرداخت": "نقدی",
                        "وضعیت": "پرداخت شده"
                    })
            st.dataframe(sales_data, use_container_width=True)
        else:
            st.info("هیچ فروشی ثبت نشده است")
    
    with tab2:
        try:
            cursor.execute('''
                SELECT id, purchase_date, supplier, material_name, 
                       quantity, total_price, status
                FROM purchases 
                ORDER BY purchase_date DESC 
                LIMIT 10
            ''')
        except:
            cursor.execute('''
                SELECT id, purchase_date, supplier, material_name, 
                       quantity, total_price, 'ثبت شده' as status
                FROM purchases 
                ORDER BY purchase_date DESC 
                LIMIT 10
            ''')
        
        recent_purchases = cursor.fetchall()
        
        if recent_purchases:
            purchase_data = []
            for purchase in recent_purchases:
                purchase_data.append({
                    "شناسه": purchase[0],
                    "تاریخ": purchase[1],
                    "تأمین‌کننده": purchase[2],
                    "مواد": purchase[3],
                    "تعداد": purchase[4],
                    "مبلغ": f"{purchase[5]:,.0f}",
                    "وضعیت": purchase[6] if len(purchase) > 6 else "ثبت شده"
                })
            st.dataframe(purchase_data, use_container_width=True)
        else:
            st.info("هیچ خریدی ثبت نشده است")
    
    with tab3:
        try:
            cursor.execute('''
                SELECT id, expense_date, expense_type, description, 
                       amount, category, payment_method
                FROM expenses 
                ORDER BY expense_date DESC 
                LIMIT 10
            ''')
        except:
            cursor.execute('''
                SELECT id, expense_date, expense_type, description, 
                       amount, category, 'نقدی' as payment_method
                FROM expenses 
                ORDER BY expense_date DESC 
                LIMIT 10
            ''')
        
        recent_expenses = cursor.fetchall()
        
        if recent_expenses:
            expense_data = []
            for expense in recent_expenses:
                expense_data.append({
                    "شناسه": expense[0],
                    "تاریخ": expense[1],
                    "نوع": expense[2],
                    "شرح": expense[3],
                    "مبلغ": f"{expense[4]:,.0f}",
                    "دسته": expense[5] if len(expense) > 5 else "عمومی",
                    "روش پرداخت": expense[6] if len(expense) > 6 else "نقدی"
                })
            st.dataframe(expense_data, use_container_width=True)
        else:
            st.info("هیچ مصرفی ثبت نشده است")
    
    # ردیف چهارم: ابزارهای سریع
    st.markdown("### ⚡ ابزارهای سریع")
    col_tool1, col_tool2, col_tool3, col_tool4 = st.columns(4)
    
    with col_tool1:
        if st.button("📊 گزارش اکسل", use_container_width=True, icon="📊"):
            from helpers import generate_excel_report
            # تولید گزارش اکسل
            report_data = [
                ['گزارش سیستم مدیریت کارخانه مواد شوینده', ''],
                ['تاریخ تولید', datetime.now().strftime('%Y/%m/%d %H:%M:%S')],
                ['تولید شده توسط', st.session_state.full_name],
                ['', ''],
                ['آمار کلی', ''],
                ['تعداد محصولات', product_count],
                ['تعداد مشتریان', customer_count],
                ['موجودی کل', total_stock],
                ['فروش امروز', today_sales],
                ['', ''],
                ['محصولات با موجودی کم', '']
            ]
            
            # اضافه کردن محصولات با موجودی کم
            for product in low_stock:
                report_data.append([product[0], f"{product[1]} از {product[2]}"])
            
            generate_excel_report(report_data, ['عنوان', 'مقدار'], f'گزارش_سیستم_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            st.success("گزارش اکسل با موفقیت تولید شد!")
    
    with col_tool2:
        if st.button("🖨️ فاکتور نمونه", use_container_width=True, icon="🖨️"):
            from helpers import create_invoice_html
            # ایجاد فاکتور نمونه برای چاپ
            invoice_items = [
                {
                    'name': 'مایع ظرفشویی 1 لیتری',
                    'unit': 'عدد',
                    'quantity': 10,
                    'unit_price': 150,
                    'total': 1500
                },
                {
                    'name': 'پودر لباسشویی 2 کیلویی',
                    'unit': 'بسته',
                    'quantity': 5,
                    'unit_price': 300,
                    'total': 1500
                },
                {
                    'name': 'مایع سفید کننده',
                    'unit': 'لیتر',
                    'quantity': 3,
                    'unit_price': 200,
                    'total': 600
                }
            ]
            
            invoice_data = {
                'invoice_number': f'INV-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'date': datetime.now().strftime('%Y/%m/%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'customer_name': 'مشتری نمونه',
                'customer_phone': '0770000000',
                'customer_address': 'آدرس نمونه',
                'payment_type': 'نقدی',
                'payment_status': 'پرداخت شده',
                'subtotal': 3600,
                'tax': 0,
                'discount': 0,
                'total': 3600,
                'notes': 'فاکتور نمونه برای تست سیستم چاپ',
                'cashier': st.session_state.full_name
            }
            
            # ایجاد HTML فاکتور
            invoice_html = create_invoice_html('فاکتور فروش', invoice_data, invoice_items)
            
            # نمایش فاکتور
            st.markdown("### 🧾 پیش‌نمایش فاکتور")
            st.components.v1.html(invoice_html, height=800, scrolling=True)
            
            # دکمه چاپ
            if st.button("🖨️ چاپ فاکتور", key="print_invoice"):
                st.markdown("""
                <script>
                window.print();
                </script>
                """, unsafe_allow_html=True)

def dashboard_module(db, auth):
    """ماژول داشبورد اصلی"""
    # هدر اصلی
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h1>🧼 مدیریت کارخانه مواد شوینده</h1>
        <p>نسخه {VERSION} | کاربر: {st.session_state.full_name} | نقش: {st.session_state.role}</p>
        <p style="font-size: 14px; opacity: 0.9;">آخرین به‌روزرسانی: {datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # نمایش اطلاعات کاربر در سایدبار
    with st.sidebar:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h4>👤 پروفایل کاربر</h4>
            <p style="margin: 5px 0;"><strong>نام:</strong> {st.session_state.full_name}</p>
            <p style="margin: 5px 0;"><strong>نقش:</strong> {st.session_state.role}</p>
            <p style="margin: 5px 0;"><strong>کاربری:</strong> {st.session_state.username}</p>
            <p style="margin: 5px 0; font-size: 12px;">🕒 آخرین ورود: {datetime.now().strftime('%H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # منوی اصلی
        st.markdown("### 📋 منوی اصلی")
        
        # منو بر اساس نقش کاربر
        menu_items = []
        
        if st.session_state.role == "ادمین":
            menu_items = [
                "📊 داشبورد",
                "🏷️ مدیریت محصولات",
                "📦 خرید مواد اولیه", 
                "💰 مدیریت فروش",
                "👥 مدیریت مشتریان",
                "📦 مدیریت انبار",
                "👥 مدیریت کارمندان",
                "💰 مدیریت مصارف",
                "📊 گزارشات و آمار",
                "👑 مدیریت کاربران"
            ]
        elif st.session_state.role == "حسابدار":
            menu_items = [
                "📊 داشبورد",
                "💰 مدیریت فروش",
                "📦 خرید مواد اولیه",
                "💰 مدیریت مصارف",
                "📊 گزارشات و آمار",
                "👥 مدیریت مشتریان"
            ]
        elif st.session_state.role == "انباردار":
            menu_items = [
                "📊 داشبورد",
                "🏷️ مدیریت محصولات",
                "📦 مدیریت انبار",
                "📦 خرید مواد اولیه"
            ]
        else:
            menu_items = [
                "📊 داشبورد",
                "💰 مدیریت فروش",
                "👥 مدیریت مشتریان"
            ]
        
        selected_menu = st.selectbox("انتخاب بخش", menu_items)
        
        # بخش جستجوی سریع
        st.markdown("---")
        st.markdown("### 🔍 جستجوی سریع")
        search_type = st.selectbox("نوع جستجو", ["مشتری", "محصول", "فاکتور", "خرید"])
        search_query = st.text_input("عبارت جستجو")
        if st.button("🔍 اجرای جستجو", use_container_width=True):
            st.info(f"جستجوی {search_type} برای '{search_query}'")
        
        # دکمه خروج
        st.markdown("---")
        if st.button("🚪 خروج از سیستم", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("با موفقیت از سیستم خارج شدید!")
            time.sleep(1)
            st.rerun()
    
    # محتوای اصلی بر اساس منوی انتخاب شده
    if selected_menu == "📊 داشبورد":
        show_main_dashboard(db)
    elif selected_menu == "🏷️ مدیریت محصولات":
        products_module(db)
    elif selected_menu == "📦 خرید مواد اولیه":
        purchase_module(db)
    elif selected_menu == "💰 مدیریت فروش":
        sales_module(db)
    elif selected_menu == "👥 مدیریت مشتریان":
        customers_module(db)
    elif selected_menu == "📦 مدیریت انبار":
        warehouse_module(db)
    elif selected_menu == "👥 مدیریت کارمندان":
        employees_module(db)
    elif selected_menu == "💰 مدیریت مصارف":
        expenses_module(db)
    elif selected_menu == "📊 گزارشات و آمار":
        reports_module(db)
    elif selected_menu == "👑 مدیریت کاربران":
        users_module(db, auth)

def main():
    """تابع اصلی اجرای برنامه"""
    # بارگذاری استایل‌های CSS
    load_css()
    
    # اضافه کردن استایل‌های اضافی
    st.markdown("""
    <style>
    /* استایل‌های عمومی */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* استایل‌های تب‌ها */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f8f9fa;
        padding: 5px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    /* استایل‌های جداول */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .dataframe th {
        background: #1e3a8a !important;
        color: white !important;
        font-weight: 600;
    }
    
    /* استایل‌های فرم */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 10px;
    }
    
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # تنظیمات صفحه
    st.set_page_config(
        page_title="🧼 سیستم مدیریت کارخانه مواد شوینده",
        page_icon="🧼",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/detergent-factory-system',
            'Report a bug': "mailto:ajoya028@gmail.com",
            'About': f"سیستم مدیریت کارخانه مواد شوینده v{VERSION}"
        }
    )
    
    # مقداردهی اولیه session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # ایجاد اتصال به دیتابیس و سیستم احراز هویت
    db = Database()
    auth = Authentication(db)
    
    # نمایش صفحه مناسب بر اساس وضعیت لاگین
    if not st.session_state.logged_in:
        show_login_page(auth)
    else:
        dashboard_module(db, auth)

if __name__ == "__main__":
    main()
