import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt

# ---------------------------
# قاعدة البيانات
# ---------------------------
DB_NAME = "database.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    con = get_connection()
    cur = con.cursor()
    # جدول الممتلكات
    cur.execute("""
        CREATE TABLE IF NOT EXISTS الممتلكات (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            الاسم TEXT,
            الفئة TEXT,
            القيمة REAL
        )
    """)
    # سجل الاستخدام
    cur.execute("""
        CREATE TABLE IF NOT EXISTS سجل_الاستخدام (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            عنصر_id INTEGER,
            تاريخ TEXT,
            FOREIGN KEY (عنصر_id) REFERENCES الممتلكات(id)
        )
    """)
    # المهام والمواعيد
    cur.execute("""
        CREATE TABLE IF NOT EXISTS المهام (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            العنوان TEXT,
            الوصف TEXT,
            التاريخ TEXT,
            النوع TEXT,
            الحالة TEXT,
            الاولوية INTEGER
        )
    """)
    con.commit()
    con.close()

# ---------------------------
# شاشة Dashboard
# ---------------------------
class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.total_items_label = QLabel()
        self.unused_items_label = QLabel()
        self.tasks_today_label = QLabel()
        self.overdue_tasks_label = QLabel()
        self.suggestion_label = QLabel()
        self.weekly_report_label = QLabel()

        layout.addWidget(self.total_items_label)
        layout.addWidget(self.unused_items_label)
        layout.addWidget(self.tasks_today_label)
        layout.addWidget(self.overdue_tasks_label)
        layout.addWidget(self.suggestion_label)
        layout.addWidget(self.weekly_report_label)

        self.update_dashboard()

    def update_dashboard(self):
        con = get_connection()
        cur = con.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # إجمالي العناصر
        cur.execute("SELECT COUNT(*) FROM الممتلكات")
        total_items = cur.fetchone()[0]
        self.total_items_label.setText(f"إجمالي العناصر: {total_items}")

        # العناصر غير المستخدمة
        cur.execute("""
            SELECT COUNT(*) FROM الممتلكات m
            LEFT JOIN سجل_الاستخدام u ON m.id = u.عنصر_id AND u.تاريخ >= ?
            GROUP BY m.id
            HAVING COUNT(u.id) = 0
        """, (thirty_days_ago,))
        unused_count = len(cur.fetchall())
        self.unused_items_label.setText(f"العناصر غير المستخدمة خلال آخر 30 يوم: {unused_count}")

        # مهام اليوم
        cur.execute("SELECT COUNT(*) FROM المهام WHERE التاريخ = ?", (today,))
        tasks_today = cur.fetchone()[0]
        self.tasks_today_label.setText(f"مهام اليوم: {tasks_today}")

        # المهام المتأخرة
        cur.execute("SELECT COUNT(*) FROM المهام WHERE التاريخ < ? AND الحالة != 'منجز'", (today,))
        overdue_tasks = cur.fetchone()[0]
        self.overdue_tasks_label.setText(f"المهام المتأخرة: {overdue_tasks}")

        # اقتراح
        if overdue_tasks > 0:
            suggestion = "ابدأ بالمهام المتأخرة أولًا!"
        elif tasks_today > 0:
            suggestion = "ابدأ بالمهمة الأعلى أولوية اليوم."
        else:
            suggestion = "راجع العناصر غير المستخدمة أو أضف مهام جديدة."
        self.suggestion_label.setText(f"اقتراح: {suggestion}")

        # تقرير أسبوعي
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cur.execute("SELECT COUNT(*) FROM المهام WHERE التاريخ >= ?", (week_ago,))
        tasks_week = cur.fetchone()[0]
        self.weekly_report_label.setText(f"عدد المهام خلال الأسبوع الماضي: {tasks_week}")

        # ألوان تنبيه
        self.overdue_tasks_label.setStyleSheet("color: red;" if overdue_tasks>0 else "color: green;")
        con.close()

# ---------------------------
# شاشة Inventory
# ---------------------------
class InventoryScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.update_inventory()

    def update_inventory(self):
        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, الاسم, الفئة, القيمة FROM الممتلكات")
        rows = cur.fetchall()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['ID', 'الاسم', 'الفئة', 'القيمة'])
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i,j,QTableWidgetItem(str(val)))
        con.close()

# ---------------------------
# شاشة Tasks
# ---------------------------
class TasksScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.update_tasks()

    def update_tasks(self):
        con = get_connection()
        cur = con.cursor()
        cur.execute("SELECT id, العنوان, الوصف, التاريخ, النوع, الحالة, الاولوية FROM المهام")
        rows = cur.fetchall()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['ID','العنوان','الوصف','التاريخ','النوع','الحالة','الأولوية'])
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i,j,QTableWidgetItem(str(val)))
        con.close()

# ---------------------------
# شاشة AI Chat
# ---------------------------
class AIChatScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("مساعد ذكي: يمكنك كتابة استفساراتك هنا لاحقًا")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

# ---------------------------
# Main Window
# ---------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مدير الموارد الشخصية")
        self.resize(1000, 650)
        main_layout = QHBoxLayout(self)

        sidebar_layout = QVBoxLayout()
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFixedWidth(220)

        self.btn_dashboard = QPushButton("🏠 لوحة التحكم")
        self.btn_inventory = QPushButton("📦 الممتلكات")
        self.btn_tasks = QPushButton("✅ المهام")
        self.btn_ai = QPushButton("🤖 المساعد الذكي")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_inventory)
        sidebar_layout.addWidget(self.btn_tasks)
        sidebar_layout.addWidget(self.btn_ai)
        sidebar_layout.addStretch()

        self.stack = QStackedWidget()
        self.dashboard_screen = DashboardScreen()
        self.inventory_screen = InventoryScreen()
        self.tasks_screen = TasksScreen()
        self.ai_screen = AIChatScreen()

        self.stack.addWidget(self.dashboard_screen)
        self.stack.addWidget(self.inventory_screen)
        self.stack.addWidget(self.tasks_screen)
        self.stack.addWidget(self.ai_screen)

        self.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_screen))
        self.btn_inventory.clicked.connect(lambda: self.stack.setCurrentWidget(self.inventory_screen))
        self.btn_tasks.clicked.connect(lambda: self.stack.setCurrentWidget(self.tasks_screen))
        self.btn_ai.clicked.connect(lambda: self.stack.setCurrentWidget(self.ai_screen))

        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.stack)
        self.stack.setCurrentWidget(self.dashboard_screen)

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
