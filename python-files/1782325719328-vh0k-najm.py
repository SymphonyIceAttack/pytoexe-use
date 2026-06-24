import sys
import enum
import os
from datetime import datetime, timedelta
from typing import List, Optional
from passlib.context import CryptContext
from sqlalchemy import create_engine, String, Integer, DateTime, Float, ForeignKey, Enum as SAEnum, Text, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QFrame,
                              QStackedWidget, QTableWidget, QTableWidgetItem, QDialog, QHeaderView,
                              QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QGridLayout, QGroupBox,
                              QScrollArea, QSizePolicy, QFileDialog, QTabWidget, QCheckBox, QProgressBar)
from PyQt6.QtCore import Qt, QDate, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QLinearGradient, QPalette, QBrush, QIcon, QPixmap

# ==========================================
# 1. Enums للحالات والأدوار
# ==========================================
class UserRole(enum.Enum):
    ADMIN = "مدير النظام"
    MANAGER = "مدير الصيانة"
    SUPERVISOR = "مشرف"
    TECHNICIAN = "فني"
    REQUESTER = "مقدم طلب"

class AssetStatus(enum.Enum):
    OPERATIONAL = "يعمل بكفاءة"
    NEEDS_MAINTENANCE = "يحتاج صيانة"
    DOWN = "متوقف عن العمل"
    UNDER_REPAIR = "قيد الإصلاح"
    RETIRED = "خارج الخدمة"

class WorkOrderStatus(enum.Enum):
    NEW = "جديد"
    ASSIGNED = "تم الإسناد"
    IN_PROGRESS = "قيد التنفيذ"
    WAITING_PARTS = "بانتظار قطع غيار"
    COMPLETED = "مكتمل"
    CLOSED = "مغلق"
    CANCELLED = "ملغي"

class Priority(enum.Enum):
    CRITICAL = "حرج"
    HIGH = "عالي"
    MEDIUM = "متوسط"
    LOW = "منخفض"
    ROUTINE = "روتيني"

class WorkType(enum.Enum):    EMERGENCY = "طوارئ"
    URGENT = "عاجل"
    PLANNED = "مخطط"
    PREVENTIVE = "وقائي"
    PREDICTIVE = "تنبؤي"
    CORRECTIVE = "تصحيحي"
    INSPECTION = "فحص"

class FrequencyType(enum.Enum):
    DAILY = "يومي"
    WEEKLY = "أسبوعي"
    MONTHLY = "شهري"
    QUARTERLY = "ربع سنوي"
    YEARLY = "سنوي"
    HOURS = "حسب الساعات"
    CYCLES = "حسب الدورات"

# ==========================================
# 2. Base & Engine
# ==========================================
class Base(DeclarativeBase):
    pass

engine = create_engine('sqlite:///cmms_benhamawi.db', echo=False)

# ==========================================
# 3. Models (الجداول)
# ==========================================
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    assigned_work_orders: Mapped[List["WorkOrder"]] = relationship(
        back_populates="assigned_tech", 
        foreign_keys="WorkOrder.assigned_tech_id"
    )

class Asset(Base):
    __tablename__ = "assets"    id: Mapped[int] = mapped_column(primary_key=True)
    asset_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[AssetStatus] = mapped_column(SAEnum(AssetStatus), default=AssetStatus.OPERATIONAL)
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    purchase_cost: Mapped[float] = mapped_column(Float, default=0.0)
    warranty_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    criticality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    work_orders: Mapped[List["WorkOrder"]] = relationship(back_populates="asset")
    maintenance_schedules: Mapped[List["MaintenanceSchedule"]] = relationship(back_populates="asset")

class WorkOrder(Base):
    __tablename__ = "work_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_type: Mapped[WorkType] = mapped_column(SAEnum(WorkType), default=WorkType.PLANNED)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.MEDIUM)
    status: Mapped[WorkOrderStatus] = mapped_column(SAEnum(WorkOrderStatus), default=WorkOrderStatus.NEW)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    labor_hours: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    failure_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_tech_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="work_orders")
    requester: Mapped["User"] = relationship(foreign_keys=[requester_id])
    assigned_tech: Mapped[Optional["User"]] = relationship(
        back_populates="assigned_work_orders", 
        foreign_keys=[assigned_tech_id]
    )

class SparePart(Base):
    __tablename__ = "spare_parts"
    id: Mapped[int] = mapped_column(primary_key=True)    part_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quantity_in_stock: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=5)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    supplier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    schedule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frequency_type: Mapped[FrequencyType] = mapped_column(SAEnum(FrequencyType), nullable=False)
    frequency_value: Mapped[int] = mapped_column(Integer, default=1)
    last_performed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_due: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    checklist: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    asset: Mapped["Asset"] = relationship(back_populates="maintenance_schedules")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# ==========================================
# 4. دوال قاعدة البيانات
# ==========================================
def init_db():
    Base.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

# ==========================================
# 5. خدمة المصادقة
# ==========================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def authenticate(username: str, password: str):
        with get_session() as session:
            user = session.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if user and AuthService.verify_password(password, user.password_hash):
                user.last_login = datetime.utcnow()
                session.commit()
                return user
            return None
    
    @staticmethod
    def log_action(user_id: int, action: str, table_name: str, record_id: int = None, details: str = None):
        with get_session() as session:
            log = AuditLog(
                user_id=user_id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                details=details
            )
            session.add(log)
            session.commit()

def create_default_admin():
    with get_session() as session:
        admin = session.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=AuthService.hash_password("admin123"),
                full_name="مدير النظام",
                role=UserRole.ADMIN,
                email="admin@benhamawi.com",
                is_active=True
            )
            session.add(admin)
            session.commit()
# ==========================================
# 6. الثيم والألوان
# ==========================================
THEME = {
    "primary": "#1e3a8a",
    "secondary": "#3b82f6",
    "accent": "#f59e0b",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "info": "#06b6d4",
    "dark": "#1f2937",
    "light": "#f9fafb",
    "gray": "#6b7280",
    "white": "#ffffff",
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {THEME['light']};
}}
QLabel {{
    color: {THEME['dark']};
    font-size: 13px;
}}
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {{
    padding: 8px;
    border: 2px solid #e5e7eb;
    border-radius: 6px;
    font-size: 13px;
    background-color: white;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border: 2px solid {THEME['secondary']};
}}
QTableWidget {{
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    gridline-color: #e5e7eb;
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 8px;
}}
QTableWidget::item:selected {{
    background-color: {THEME['secondary']};
    color: white;
}}
QHeaderView::section {{    background-color: {THEME['primary']};
    color: white;
    padding: 10px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}}
QPushButton {{
    background-color: {THEME['secondary']};
    color: white;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    border: none;
}}
QPushButton:hover {{
    background-color: {THEME['primary']};
}}
QPushButton:pressed {{
    background-color: #1e40af;
}}
QGroupBox {{
    font-weight: bold;
    font-size: 14px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}
QTabWidget::pane {{
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: white;
}}
QTabBar::tab {{
    background-color: #e5e7eb;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background-color: {THEME['secondary']};
    color: white;    font-weight: bold;
}}
QProgressBar {{
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    text-align: center;
    font-weight: bold;
}}
QProgressBar::chunk {{
    background-color: {THEME['success']};
    border-radius: 5px;
}}
"""

# ==========================================
# 7. نافذة تسجيل الدخول
# ==========================================
class LoginWindow(QMainWindow):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("شركة بن الحموي - نظام إدارة الصيانة")
        self.setFixedSize(500, 600)
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {THEME['primary']}, stop:1 {THEME['secondary']});
            }}
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # شعار الشركة
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        logo_layout = QVBoxLayout(logo_frame)
                logo_title = QLabel("🏢")
        logo_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_title.setFont(QFont("Arial", 48))
        logo_layout.addWidget(logo_title)
        
        company_name = QLabel("شركة بن الحموي")
        company_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        company_name.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        company_name.setStyleSheet(f"color: {THEME['primary']};")
        logo_layout.addWidget(company_name)
        
        subtitle = QLabel("نظام إدارة الصيانة المتكامل")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet(f"color: {THEME['gray']};")
        logo_layout.addWidget(subtitle)
        
        layout.addWidget(logo_frame)
        layout.addSpacing(20)
        
        # نموذج تسجيل الدخول
        login_frame = QFrame()
        login_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        login_layout = QVBoxLayout(login_frame)
        login_layout.setSpacing(15)
        
        login_layout.addWidget(QLabel("👤 اسم المستخدم:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        login_layout.addWidget(self.username_input)
        
        login_layout.addWidget(QLabel("🔒 كلمة المرور:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        login_layout.addWidget(self.password_input)
        
        login_btn = QPushButton("🚀 تسجيل الدخول")
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['primary']};
                color: white;
                padding: 15px;
                border-radius: 8px;                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME['secondary']};
            }}
        """)
        login_btn.clicked.connect(self.handle_login)
        login_layout.addWidget(login_btn)
        
        layout.addWidget(login_frame)
        
        # معلومات
        info_label = QLabel("المستخدم الافتراضي: admin / admin123")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: white; font-size: 12px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # توقيع المطور
        developer_label = QLabel("مطور البرنامج: محمد نجم الخطيب الحسني")
        developer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        developer_label.setStyleSheet("color: white; font-size: 11px; font-weight: bold;")
        layout.addWidget(developer_label)
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return
        
        user = AuthService.authenticate(username, password)
        
        if user:
            QMessageBox.information(self, "نجاح", f"مرحباً {user.full_name}!")
            self.on_login_success(user)
        else:
            QMessageBox.critical(self, "فشل", "اسم المستخدم أو كلمة المرور غير صحيحة")

# ==========================================
# 8. لوحة التحكم
# ==========================================
class DashboardWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # العنوان
        title = QLabel("📊 لوحة التحكم")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {THEME['primary']};")
        layout.addWidget(title)
        
        # بطاقات الإحصائيات
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        self.stats_cards = {}
        stats = [
            ("total_assets", "🔧 إجمالي المعدات", "#3b82f6"),
            ("active_orders", "📋 أوامر العمل النشطة", "#f59e0b"),
            ("down_assets", "⚠️ معدات متوقفة", "#ef4444"),
            ("low_stock", "📦 مخزون منخفض", "#8b5cf6"),
            ("total_users", "👥 المستخدمين", "#10b981"),
            ("completed_today", "✅ مكتملة اليوم", "#06b6d4"),
        ]
        
        for i, (key, title, color) in enumerate(stats):
            card = self.create_stat_card(key, title, color)
            row = i // 3
            col = i % 3
            stats_layout.addWidget(card, row, col)
        
        layout.addLayout(stats_layout)
        
        # مؤشرات الأداء
        kpi_group = QGroupBox("📈 مؤشرات الأداء الرئيسية (KPIs)")
        kpi_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;            }
        """)
        kpi_layout = QVBoxLayout(kpi_group)
        
        kpis = [
            ("MTBF - متوسط الوقت بين الأعطال", 85, "#10b981"),
            ("MTTR - متوسط وقت الإصلاح", 72, "#f59e0b"),
            ("OEE - فعالية المعدات", 78, "#3b82f6"),
            ("نسبة الصيانة المخططة", 65, "#8b5cf6"),
        ]
        
        for label, value, color in kpis:
            kpi_item = QHBoxLayout()
            kpi_label = QLabel(label)
            kpi_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            kpi_item.addWidget(kpi_label)
            
            progress = QProgressBar()
            progress.setValue(value)
            progress.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            kpi_item.addWidget(progress)
            
            value_label = QLabel(f"{value}%")
            value_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
            kpi_item.addWidget(value_label)
            
            kpi_layout.addLayout(kpi_item)
        
        layout.addWidget(kpi_group)
        layout.addStretch()
    
    def create_stat_card(self, key, title, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {color}dd);
                border-radius: 15px;
                padding: 20px;
            }}
        """)
        card.setMinimumHeight(150)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
                title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel("0")
        value_label.setStyleSheet("color: white; font-size: 42px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        self.stats_cards[key] = value_label
        
        return card
    
    def load_data(self):
        with get_session() as session:
            total_assets = session.query(func.count(Asset.id)).scalar()
            self.stats_cards["total_assets"].setText(str(total_assets))
            
            active_orders = session.query(func.count(WorkOrder.id)).filter(
                WorkOrder.status.in_([
                    WorkOrderStatus.NEW, WorkOrderStatus.ASSIGNED, 
                    WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.WAITING_PARTS
                ])
            ).scalar()
            self.stats_cards["active_orders"].setText(str(active_orders))
            
            down_assets = session.query(func.count(Asset.id)).filter(
                Asset.status == AssetStatus.DOWN
            ).scalar()
            self.stats_cards["down_assets"].setText(str(down_assets))
            
            low_stock = session.query(func.count(SparePart.id)).filter(
                SparePart.quantity_in_stock <= SparePart.min_stock_level
            ).scalar()
            self.stats_cards["low_stock"].setText(str(low_stock))
            
            total_users = session.query(func.count(User.id)).filter(
                User.is_active == True
            ).scalar()
            self.stats_cards["total_users"].setText(str(total_users))
            
            today = datetime.now().date()
            completed_today = session.query(func.count(WorkOrder.id)).filter(
                func.date(WorkOrder.completed_at) == today
            ).scalar()
            self.stats_cards["completed_today"].setText(str(completed_today))

# ==========================================
# 9. إدارة المعدات
# ==========================================class AssetsWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.load_assets()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("🔧 إدارة المعدات")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME['primary']};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ إضافة معدة جديدة")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['success']};
                color: white;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        add_btn.clicked.connect(self.add_asset)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "الكود", "الاسم", "الفئة", "الموقع", "الحالة", "المصنع", "الموديل", "الأولوية", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
    
    def load_assets(self):
        with get_session() as session:
            assets = session.query(Asset).all()
            self.table.setRowCount(len(assets))
                        for row, asset in enumerate(assets):
                self.table.setItem(row, 0, QTableWidgetItem(asset.asset_code))
                self.table.setItem(row, 1, QTableWidgetItem(asset.name))
                self.table.setItem(row, 2, QTableWidgetItem(asset.category or "-"))
                self.table.setItem(row, 3, QTableWidgetItem(asset.location or "-"))
                self.table.setItem(row, 4, QTableWidgetItem(asset.status.value))
                self.table.setItem(row, 5, QTableWidgetItem(asset.manufacturer or "-"))
                self.table.setItem(row, 6, QTableWidgetItem(asset.model or "-"))
                self.table.setItem(row, 7, QTableWidgetItem(asset.criticality or "-"))
                
                edit_btn = QPushButton("✏️ تعديل")
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME['secondary']};
                        padding: 6px 12px;
                        font-size: 12px;
                    }}
                """)
                edit_btn.clicked.connect(lambda checked, a=asset: self.edit_asset(a))
                self.table.setCellWidget(row, 8, edit_btn)
    
    def add_asset(self):
        dialog = AssetDialog(self)
        if dialog.exec():
            self.load_assets()
    
    def edit_asset(self, asset):
        dialog = AssetDialog(self, asset)
        if dialog.exec():
            self.load_assets()

class AssetDialog(QDialog):
    def __init__(self, parent, asset=None):
        super().__init__(parent)
        self.asset = asset
        self.setWindowTitle("إضافة/تعديل معدة")
        self.setFixedSize(600, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        fields = [
            ("asset_code", "كود المعدة*", QLineEdit),
            ("name", "اسم المعدة*", QLineEdit),            ("category", "الفئة", QComboBox, ["كهربائي", "ميكانيكي", "هيدروليكي", "إلكتروني", "أخرى"]),
            ("location", "الموقع", QLineEdit),
            ("manufacturer", "المصنع", QLineEdit),
            ("model", "الموديل", QLineEdit),
            ("serial_number", "الرقم التسلسلي", QLineEdit),
            ("status", "الحالة", QComboBox, [s.value for s in AssetStatus]),
            ("criticality", "الأولوية", QComboBox, ["حرج", "عالي", "متوسط", "منخفض"]),
        ]
        
        self.inputs = {}
        
        for field in fields:
            label = QLabel(field[1])
            label.setStyleSheet("font-weight: bold; font-size: 13px;")
            scroll_layout.addWidget(label)
            
            if field[2] == QLineEdit:
                input_widget = QLineEdit()
            else:
                input_widget = QComboBox()
                input_widget.addItems(field[3])
            
            self.inputs[field[0]] = input_widget
            scroll_layout.addWidget(input_widget)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet(f"background-color: {THEME['success']}; color: white; padding: 12px;")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet(f"background-color: {THEME['gray']}; color: white; padding: 12px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if self.asset:
            self.inputs["asset_code"].setText(self.asset.asset_code)
            self.inputs["name"].setText(self.asset.name)
            self.inputs["category"].setCurrentText(self.asset.category or "")
            self.inputs["location"].setText(self.asset.location or "")
            self.inputs["manufacturer"].setText(self.asset.manufacturer or "")
            self.inputs["model"].setText(self.asset.model or "")
            self.inputs["serial_number"].setText(self.asset.serial_number or "")            self.inputs["status"].setCurrentText(self.asset.status.value)
            self.inputs["criticality"].setCurrentText(self.asset.criticality or "متوسط")
    
    def save(self):
        with get_session() as session:
            if self.asset:
                asset = session.query(Asset).get(self.asset.id)
            else:
                asset = Asset()
                session.add(asset)
            
            asset.asset_code = self.inputs["asset_code"].text()
            asset.name = self.inputs["name"].text()
            asset.category = self.inputs["category"].currentText()
            asset.location = self.inputs["location"].text()
            asset.manufacturer = self.inputs["manufacturer"].text()
            asset.model = self.inputs["model"].text()
            asset.serial_number = self.inputs["serial_number"].text()
            asset.status = AssetStatus(self.inputs["status"].currentText())
            asset.criticality = self.inputs["criticality"].currentText()
            
            session.commit()
            
            AuthService.log_action(
                self.parent().current_user.id,
                "update" if self.asset else "create",
                "assets",
                asset.id
            )
        
        QMessageBox.information(self, "نجاح", "تم حفظ المعدة بنجاح!")
        self.accept()

# ==========================================
# 10. إدارة أوامر العمل
# ==========================================
class WorkOrdersWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.load_work_orders()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("📋 إدارة أوامر العمل")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME['primary']};")        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ إنشاء أمر عمل")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['success']};
                color: white;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        add_btn.clicked.connect(self.add_work_order)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "رقم الأمر", "العنوان", "المعدة", "النوع", "الأولوية", "الحالة", 
            "مقدم الطلب", "الفني", "التاريخ", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_work_orders(self):
        with get_session() as session:
            orders = session.query(WorkOrder).all()
            self.table.setRowCount(len(orders))
            
            for row, order in enumerate(orders):
                self.table.setItem(row, 0, QTableWidgetItem(order.order_number))
                self.table.setItem(row, 1, QTableWidgetItem(order.title))
                self.table.setItem(row, 2, QTableWidgetItem(order.asset.name))
                self.table.setItem(row, 3, QTableWidgetItem(order.work_type.value))
                self.table.setItem(row, 4, QTableWidgetItem(order.priority.value))
                self.table.setItem(row, 5, QTableWidgetItem(order.status.value))
                self.table.setItem(row, 6, QTableWidgetItem(order.requester.full_name))
                self.table.setItem(row, 7, QTableWidgetItem(order.assigned_tech.full_name if order.assigned_tech else "-"))
                self.table.setItem(row, 8, QTableWidgetItem(order.reported_at.strftime("%Y-%m-%d")))
                
                edit_btn = QPushButton("✏️ تعديل")
                edit_btn.setStyleSheet(f"""
                    QPushButton {{                        background-color: {THEME['secondary']};
                        padding: 6px 12px;
                        font-size: 12px;
                    }}
                """)
                edit_btn.clicked.connect(lambda checked, o=order: self.edit_work_order(o))
                self.table.setCellWidget(row, 9, edit_btn)
    
    def add_work_order(self):
        dialog = WorkOrderDialog(self)
        if dialog.exec():
            self.load_work_orders()
    
    def edit_work_order(self, order):
        dialog = WorkOrderDialog(self, order)
        if dialog.exec():
            self.load_work_orders()

class WorkOrderDialog(QDialog):
    def __init__(self, parent, order=None):
        super().__init__(parent)
        self.order = order
        self.setWindowTitle("إنشاء/تعديل أمر عمل")
        self.setFixedSize(700, 800)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        scroll_layout.addWidget(QLabel("رقم الأمر*:"))
        self.order_number = QLineEdit()
        scroll_layout.addWidget(self.order_number)
        
        scroll_layout.addWidget(QLabel("العنوان*:"))
        self.title = QLineEdit()
        scroll_layout.addWidget(self.title)
        
        scroll_layout.addWidget(QLabel("الوصف:"))
        self.description = QTextEdit()
        self.description.setMaximumHeight(100)
        scroll_layout.addWidget(self.description)
        
        scroll_layout.addWidget(QLabel("المعدة*:"))
        self.asset_combo = QComboBox()
        with get_session() as session:            assets = session.query(Asset).all()
            for asset in assets:
                self.asset_combo.addItem(f"{asset.asset_code} - {asset.name}", asset.id)
        scroll_layout.addWidget(self.asset_combo)
        
        scroll_layout.addWidget(QLabel("نوع العمل:"))
        self.work_type_combo = QComboBox()
        for wt in WorkType:
            self.work_type_combo.addItem(wt.value, wt)
        scroll_layout.addWidget(self.work_type_combo)
        
        scroll_layout.addWidget(QLabel("الأولوية:"))
        self.priority_combo = QComboBox()
        for p in Priority:
            self.priority_combo.addItem(p.value, p)
        scroll_layout.addWidget(self.priority_combo)
        
        scroll_layout.addWidget(QLabel("الفني المسؤول:"))
        self.tech_combo = QComboBox()
        self.tech_combo.addItem("- غير محدد -", None)
        with get_session() as session:
            techs = session.query(User).filter(User.role == UserRole.TECHNICIAN).all()
            for tech in techs:
                self.tech_combo.addItem(tech.full_name, tech.id)
        scroll_layout.addWidget(self.tech_combo)
        
        scroll_layout.addWidget(QLabel("سبب العطل:"))
        self.failure_cause = QTextEdit()
        self.failure_cause.setMaximumHeight(80)
        scroll_layout.addWidget(self.failure_cause)
        
        scroll_layout.addWidget(QLabel("السبب الجذري (RCA):"))
        self.root_cause = QTextEdit()
        self.root_cause.setMaximumHeight(80)
        scroll_layout.addWidget(self.root_cause)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet(f"background-color: {THEME['success']}; color: white; padding: 12px;")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet(f"background-color: {THEME['gray']}; color: white; padding: 12px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
                layout.addLayout(btn_layout)
        
        if self.order:
            self.order_number.setText(self.order.order_number)
            self.title.setText(self.order.title)
            self.description.setPlainText(self.order.description or "")
            self.failure_cause.setPlainText(self.order.failure_cause or "")
            self.root_cause.setPlainText(self.order.root_cause or "")
    
    def save(self):
        with get_session() as session:
            if self.order:
                wo = session.query(WorkOrder).get(self.order.id)
            else:
                wo = WorkOrder()
                session.add(wo)
            
            wo.order_number = self.order_number.text()
            wo.title = self.title.text()
            wo.description = self.description.toPlainText()
            wo.asset_id = self.asset_combo.currentData()
            wo.work_type = self.work_type_combo.currentData()
            wo.priority = self.priority_combo.currentData()
            wo.requester_id = self.parent().current_user.id
            wo.assigned_tech_id = self.tech_combo.currentData()
            wo.failure_cause = self.failure_cause.toPlainText()
            wo.root_cause = self.root_cause.toPlainText()
            
            session.commit()
        
        QMessageBox.information(self, "نجاح", "تم حفظ أمر العمل!")
        self.accept()

# ==========================================
# 11. إدارة المستخدمين
# ==========================================
class UsersWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("👥 إدارة المستخدمين")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME['primary']};")        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ إضافة مستخدم")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['success']};
                color: white;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        add_btn.clicked.connect(self.add_user)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "اسم المستخدم", "الاسم الكامل", "البريد", "الهاتف", "الدور", "القسم", "المهارات", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_users(self):
        with get_session() as session:
            users = session.query(User).all()
            self.table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(user.username))
                self.table.setItem(row, 1, QTableWidgetItem(user.full_name))
                self.table.setItem(row, 2, QTableWidgetItem(user.email or "-"))
                self.table.setItem(row, 3, QTableWidgetItem(user.phone or "-"))
                self.table.setItem(row, 4, QTableWidgetItem(user.role.value))
                self.table.setItem(row, 5, QTableWidgetItem(user.department or "-"))
                self.table.setItem(row, 6, QTableWidgetItem(user.skills or "-"))
                
                edit_btn = QPushButton("✏️ تعديل")
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME['secondary']};
                        padding: 6px 12px;
                        font-size: 12px;                    }}
                """)
                edit_btn.clicked.connect(lambda checked, u=user: self.edit_user(u))
                self.table.setCellWidget(row, 7, edit_btn)
    
    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec():
            self.load_users()
    
    def edit_user(self, user):
        dialog = UserDialog(self, user)
        if dialog.exec():
            self.load_users()

class UserDialog(QDialog):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("إضافة/تعديل مستخدم")
        self.setFixedSize(600, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        scroll_layout.addWidget(QLabel("اسم المستخدم*:"))
        self.username = QLineEdit()
        scroll_layout.addWidget(self.username)
        
        scroll_layout.addWidget(QLabel("كلمة المرور*:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        scroll_layout.addWidget(self.password)
        
        scroll_layout.addWidget(QLabel("الاسم الكامل*:"))
        self.full_name = QLineEdit()
        scroll_layout.addWidget(self.full_name)
        
        scroll_layout.addWidget(QLabel("البريد الإلكتروني:"))
        self.email = QLineEdit()
        scroll_layout.addWidget(self.email)
        
        scroll_layout.addWidget(QLabel("الهاتف:"))
        self.phone = QLineEdit()        scroll_layout.addWidget(self.phone)
        
        scroll_layout.addWidget(QLabel("الدور*:"))
        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value, role)
        scroll_layout.addWidget(self.role_combo)
        
        scroll_layout.addWidget(QLabel("القسم:"))
        self.department = QLineEdit()
        scroll_layout.addWidget(self.department)
        
        scroll_layout.addWidget(QLabel("المهارات:"))
        self.skills = QTextEdit()
        self.skills.setMaximumHeight(80)
        scroll_layout.addWidget(self.skills)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet(f"background-color: {THEME['success']}; color: white; padding: 12px;")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet(f"background-color: {THEME['gray']}; color: white; padding: 12px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if self.user:
            self.username.setText(self.user.username)
            self.full_name.setText(self.user.full_name)
            self.email.setText(self.user.email or "")
            self.phone.setText(self.user.phone or "")
            self.role_combo.setCurrentText(self.user.role.value)
            self.department.setText(self.user.department or "")
            self.skills.setPlainText(self.user.skills or "")
    
    def save(self):
        with get_session() as session:
            if self.user:
                u = session.query(User).get(self.user.id)
            else:
                u = User()
                session.add(u)
                        u.username = self.username.text()
            if self.password.text():
                u.password_hash = AuthService.hash_password(self.password.text())
            u.full_name = self.full_name.text()
            u.email = self.email.text()
            u.phone = self.phone.text()
            u.role = self.role_combo.currentData()
            u.department = self.department.text()
            u.skills = self.skills.toPlainText()
            
            session.commit()
        
        QMessageBox.information(self, "نجاح", "تم حفظ المستخدم!")
        self.accept()

# ==========================================
# 12. إدارة المخزون
# ==========================================
class InventoryWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.load_inventory()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("📦 إدارة المخزون")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME['primary']};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ إضافة قطعة غيار")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['success']};
                color: white;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        add_btn.clicked.connect(self.add_part)        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "الكود", "الاسم", "الفئة", "الكمية", "الحد الأدنى", "السعر", "المورد", "الموقع", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_inventory(self):
        with get_session() as session:
            parts = session.query(SparePart).all()
            self.table.setRowCount(len(parts))
            
            for row, part in enumerate(parts):
                self.table.setItem(row, 0, QTableWidgetItem(part.part_code))
                self.table.setItem(row, 1, QTableWidgetItem(part.name))
                self.table.setItem(row, 2, QTableWidgetItem(part.category or "-"))
                self.table.setItem(row, 3, QTableWidgetItem(str(part.quantity_in_stock)))
                self.table.setItem(row, 4, QTableWidgetItem(str(part.min_stock_level)))
                self.table.setItem(row, 5, QTableWidgetItem(f"{part.unit_price:.2f}"))
                self.table.setItem(row, 6, QTableWidgetItem(part.supplier or "-"))
                self.table.setItem(row, 7, QTableWidgetItem(part.location or "-"))
                
                edit_btn = QPushButton("✏️ تعديل")
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME['secondary']};
                        padding: 6px 12px;
                        font-size: 12px;
                    }}
                """)
                edit_btn.clicked.connect(lambda checked, p=part: self.edit_part(p))
                self.table.setCellWidget(row, 8, edit_btn)
    
    def add_part(self):
        dialog = SparePartDialog(self)
        if dialog.exec():
            self.load_inventory()
    
    def edit_part(self, part):
        dialog = SparePartDialog(self, part)
        if dialog.exec():
            self.load_inventory()

class SparePartDialog(QDialog):
    def __init__(self, parent, part=None):        super().__init__(parent)
        self.part = part
        self.setWindowTitle("إضافة/تعديل قطعة غيار")
        self.setFixedSize(600, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        scroll_layout.addWidget(QLabel("كود القطعة*:"))
        self.part_code = QLineEdit()
        scroll_layout.addWidget(self.part_code)
        
        scroll_layout.addWidget(QLabel("الاسم*:"))
        self.name = QLineEdit()
        scroll_layout.addWidget(self.name)
        
        scroll_layout.addWidget(QLabel("الفئة:"))
        self.category = QLineEdit()
        scroll_layout.addWidget(self.category)
        
        scroll_layout.addWidget(QLabel("الكمية في المخزون:"))
        self.quantity = QSpinBox()
        self.quantity.setMaximum(999999)
        scroll_layout.addWidget(self.quantity)
        
        scroll_layout.addWidget(QLabel("الحد الأدنى للمخزون:"))
        self.min_stock = QSpinBox()
        self.min_stock.setMaximum(999999)
        scroll_layout.addWidget(self.min_stock)
        
        scroll_layout.addWidget(QLabel("سعر الوحدة:"))
        self.unit_price = QDoubleSpinBox()
        self.unit_price.setMaximum(999999.99)
        self.unit_price.setDecimals(2)
        scroll_layout.addWidget(self.unit_price)
        
        scroll_layout.addWidget(QLabel("المورد:"))
        self.supplier = QLineEdit()
        scroll_layout.addWidget(self.supplier)
        
        scroll_layout.addWidget(QLabel("موقع التخزين:"))
        self.location = QLineEdit()
        scroll_layout.addWidget(self.location)
                scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet(f"background-color: {THEME['success']}; color: white; padding: 12px;")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet(f"background-color: {THEME['gray']}; color: white; padding: 12px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        if self.part:
            self.part_code.setText(self.part.part_code)
            self.name.setText(self.part.name)
            self.category.setText(self.part.category or "")
            self.quantity.setValue(self.part.quantity_in_stock)
            self.min_stock.setValue(self.part.min_stock_level)
            self.unit_price.setValue(self.part.unit_price)
            self.supplier.setText(self.part.supplier or "")
            self.location.setText(self.part.location or "")
    
    def save(self):
        with get_session() as session:
            if self.part:
                p = session.query(SparePart).get(self.part.id)
            else:
                p = SparePart()
                session.add(p)
            
            p.part_code = self.part_code.text()
            p.name = self.name.text()
            p.category = self.category.text()
            p.quantity_in_stock = self.quantity.value()
            p.min_stock_level = self.min_stock.value()
            p.unit_price = self.unit_price.value()
            p.supplier = self.supplier.text()
            p.location = self.location.text()
            
            session.commit()
        
        QMessageBox.information(self, "نجاح", "تم حفظ قطعة الغيار!")
        self.accept()

# ==========================================
# 13. الصيانة الدورية# ==========================================
class MaintenanceScheduleWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
        self.load_schedules()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("📅 الصيانة الدورية")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME['primary']};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ إضافة جدول صيانة")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['success']};
                color: white;
                padding: 12px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        add_btn.clicked.connect(self.add_schedule)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "المعدة", "اسم الجدول", "التكرار", "القيمة", "آخر تنفيذ", "التالي", "الحالة", "الإجراءات"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
    
    def load_schedules(self):
        with get_session() as session:
            schedules = session.query(MaintenanceSchedule).all()
            self.table.setRowCount(len(schedules))
                        for row, schedule in enumerate(schedules):
                self.table.setItem(row, 0, QTableWidgetItem(schedule.asset.name))
                self.table.setItem(row, 1, QTableWidgetItem(schedule.schedule_name))
                self.table.setItem(row, 2, QTableWidgetItem(schedule.frequency_type.value))
                self.table.setItem(row, 3, QTableWidgetItem(str(schedule.frequency_value)))
                self.table.setItem(row, 4, QTableWidgetItem(schedule.last_performed.strftime("%Y-%m-%d") if schedule.last_performed else "-"))
                self.table.setItem(row, 5, QTableWidgetItem(schedule.next_due.strftime("%Y-%m-%d") if schedule.next_due else "-"))
                self.table.setItem(row, 6, QTableWidgetItem("نشط" if schedule.is_active else "غير نشط"))
                
                edit_btn = QPushButton("✏️ تعديل")
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {THEME['secondary']};
                        padding: 6px 12px;
                        font-size: 12px;
                    }}
                """)
                edit_btn.clicked.connect(lambda checked, s=schedule: self.edit_schedule(s))
                self.table.setCellWidget(row, 7, edit_btn)
    
    def add_schedule(self):
        dialog = ScheduleDialog(self)
        if dialog.exec():
            self.load_schedules()
    
    def edit_schedule(self, schedule):
        dialog = ScheduleDialog(self, schedule)
        if dialog.exec():
            self.load_schedules()

class ScheduleDialog(QDialog):
    def __init__(self, parent, schedule=None):
        super().__init__(parent)
        self.schedule = schedule
        self.setWindowTitle("إضافة/تعديل جدول صيانة")
        self.setFixedSize(600, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        scroll_layout.addWidget(QLabel("المعدة*:"))
        self.asset_combo = QComboBox()
        with get_session() as session:
            assets = session.query(Asset).all()            for asset in assets:
                self.asset_combo.addItem(f"{asset.asset_code} - {asset.name}", asset.id)
        scroll_layout.addWidget(self.asset_combo)
        
        scroll_layout.addWidget(QLabel("اسم الجدول*:"))
        self.schedule_name = QLineEdit()
        scroll_layout.addWidget(self.schedule_name)
        
        scroll_layout.addWidget(QLabel("الوصف:"))
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        scroll_layout.addWidget(self.description)
        
        scroll_layout.addWidget(QLabel("نوع التكرار*:"))
        self.frequency_type = QComboBox()
        for ft in FrequencyType:
            self.frequency_type.addItem(ft.value, ft)
        scroll_layout.addWidget(self.frequency_type)
        
        scroll_layout.addWidget(QLabel("القيمة (كل كم):"))
        self.frequency_value = QSpinBox()
        self.frequency_value.setMinimum(1)
        self.frequency_value.setMaximum(365)
        scroll_layout.addWidget(self.frequency_value)
        
        scroll_layout.addWidget(QLabel("قائمة الفحص (Checklist):"))
        self.checklist = QTextEdit()
        self.checklist.setMaximumHeight(100)
        self.checklist.setPlaceholderText("اكتب مهام الفحص هنا...")
        scroll_layout.addWidget(self.checklist)
        
        self.is_active = QCheckBox("نشط")
        self.is_active.setChecked(True)
        scroll_layout.addWidget(self.is_active)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 حفظ")
        save_btn.setStyleSheet(f"background-color: {THEME['success']}; color: white; padding: 12px;")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setStyleSheet(f"background-color: {THEME['gray']}; color: white; padding: 12px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)        
        if self.schedule:
            self.schedule_name.setText(self.schedule.schedule_name)
            self.description.setPlainText(self.schedule.description or "")
            self.frequency_value.setValue(self.schedule.frequency_value)
            self.checklist.setPlainText(self.schedule.checklist or "")
            self.is_active.setChecked(self.schedule.is_active)
    
    def save(self):
        with get_session() as session:
            if self.schedule:
                s = session.query(MaintenanceSchedule).get(self.schedule.id)
            else:
                s = MaintenanceSchedule()
                session.add(s)
            
            s.asset_id = self.asset_combo.currentData()
            s.schedule_name = self.schedule_name.text()
            s.description = self.description.toPlainText()
            s.frequency_type = self.frequency_type.currentData()
            s.frequency_value = self.frequency_value.value()
            s.checklist = self.checklist.toPlainText()
            s.is_active = self.is_active.isChecked()
            
            if not self.schedule:
                s.next_due = datetime.now() + timedelta(days=self.frequency_value.value())
            
            session.commit()
        
        QMessageBox.information(self, "نجاح", "تم حفظ جدول الصيانة!")
        self.accept()

# ==========================================
# 14. التقارير
# ==========================================
class ReportsWidget(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("📈 التقارير والتحليلات")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME['primary']};")
        layout.addWidget(title)
        
        tabs = QTabWidget()        
        # تبويب KPIs
        kpi_tab = QWidget()
        kpi_layout = QVBoxLayout(kpi_tab)
        
        kpis = [
            ("MTBF - متوسط الوقت بين الأعطال", 85, "#10b981"),
            ("MTTR - متوسط وقت الإصلاح", 72, "#f59e0b"),
            ("OEE - فعالية المعدات", 78, "#3b82f6"),
            ("نسبة الصيانة المخططة", 65, "#8b5cf6"),
            ("نسبة الجاهزية", 92, "#06b6d4"),
        ]
        
        for label, value, color in kpis:
            kpi_item = QHBoxLayout()
            kpi_label = QLabel(label)
            kpi_label.setStyleSheet("font-size: 15px; font-weight: bold;")
            kpi_item.addWidget(kpi_label)
            
            progress = QProgressBar()
            progress.setValue(value)
            progress.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            kpi_item.addWidget(progress)
            
            value_label = QLabel(f"{value}%")
            value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
            kpi_item.addWidget(value_label)
            
            kpi_layout.addLayout(kpi_item)
        
        kpi_layout.addStretch()
        tabs.addTab(kpi_tab, "📊 مؤشرات الأداء")
        
        # تبويب التكاليف
        cost_tab = QWidget()
        cost_layout = QVBoxLayout(cost_tab)
        
        costs = [
            ("قطع الغيار", 45000, "#3b82f6"),
            ("العمالة", 32000, "#10b981"),
            ("العقود الخارجية", 18000, "#f59e0b"),
            ("التوقف عن العمل", 25000, "#ef4444"),
        ]
        
        total = sum(c[1] for c in costs)
                for label, value, color in costs:
            cost_item = QHBoxLayout()
            cost_label = QLabel(label)
            cost_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            cost_item.addWidget(cost_label)
            
            progress = QProgressBar()
            progress.setMaximum(total)
            progress.setValue(value)
            progress.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            cost_item.addWidget(progress)
            
            value_label = QLabel(f"{value:,} ر.س")
            value_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color};")
            cost_item.addWidget(value_label)
            
            cost_layout.addLayout(cost_item)
        
        total_label = QLabel(f"💰 الإجمالي: {total:,} ر.س")
        total_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {THEME['primary']}; margin-top: 20px;")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cost_layout.addWidget(total_label)
        
        cost_layout.addStretch()
        tabs.addTab(cost_tab, "💰 التكاليف")
        
        # تبويب الأعطال
        failures_tab = QWidget()
        failures_layout = QVBoxLayout(failures_tab)
        
        failures = [
            ("أعطال كهربائية", 35),
            ("أعطال ميكانيكية", 28),
            ("أعطال هيدروليكية", 18),
            ("أعطال إلكترونية", 12),
            ("أخرى", 7),
        ]
        
        for label, value in failures:
            failure_item = QHBoxLayout()
            failure_label = QLabel(label)
            failure_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            failure_item.addWidget(failure_label)
            
            progress = QProgressBar()
            progress.setValue(value)            progress.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #ef4444;
                }
            """)
            failure_item.addWidget(progress)
            
            value_label = QLabel(f"{value}%")
            value_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #ef4444;")
            failure_item.addWidget(value_label)
            
            failures_layout.addLayout(failure_item)
        
        failures_layout.addStretch()
        tabs.addTab(failures_tab, "⚠️ تحليل الأعطال")
        
        layout.addWidget(tabs)

# ==========================================
# 15. النافذة الرئيسية
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self, current_user: User):
        super().__init__()
        self.current_user = current_user
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"شركة بن الحموي - نظام إدارة الصيانة")
        self.setGeometry(100, 100, 1500, 900)
        self.setStyleSheet(STYLESHEET)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # الشريط الجانبي
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {THEME['primary']}, stop:1 {THEME['dark']});
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)        
        # شعار الشركة
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                margin: 10px;
                padding: 15px;
            }
        """)
        logo_layout = QVBoxLayout(logo_frame)
        
        logo_icon = QLabel("🏢")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setFont(QFont("Arial", 36))
        logo_layout.addWidget(logo_icon)
        
        company_name = QLabel("شركة بن الحموي")
        company_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        company_name.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        company_name.setStyleSheet("color: white;")
        logo_layout.addWidget(company_name)
        
        sidebar_layout.addWidget(logo_frame)
        
        # معلومات المستخدم
        user_info = QFrame()
        user_info.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                margin: 10px;
                padding: 15px;
            }
        """)
        user_layout = QVBoxLayout(user_info)
        
        user_label = QLabel(f"👤 {self.current_user.full_name}")
        user_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(user_label)
        
        role_label = QLabel(f"🔑 {self.current_user.role.value}")
        role_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(role_label)
        
        sidebar_layout.addWidget(user_info)
                sidebar_layout.addSpacing(20)
        
        # أزرار القائمة
        self.menu_buttons = []
        menu_items = [
            ("📊 لوحة التحكم", "dashboard"),
            ("🔧 المعدات", "assets"),
            ("📋 أوامر العمل", "work_orders"),
            ("📅 الصيانة الدورية", "schedules"),
            ("📦 المخزون", "inventory"),
            ("👥 المستخدمين", "users"),
            ("📈 التقارير", "reports"),
        ]
        
        for text, key in menu_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: white;
                    text-align: left;
                    padding: 15px 25px;
                    border: none;
                    border-radius: 8px;
                    font-size: 15px;
                    margin: 5px 15px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                }}
                QPushButton:checked {{
                    background-color: {THEME['secondary']};
                }}
            """)
            btn.clicked.connect(lambda checked, k=key: self.show_page(k))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)
        
        sidebar_layout.addStretch()
        
        # زر تسجيل الخروج
        logout_btn = QPushButton("🚪 تسجيل الخروج")
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['danger']};
                color: white;
                padding: 12px;
                margin: 15px;                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)
        
        main_layout.addWidget(sidebar)
        
        # منطقة المحتوى
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # شريط العنوان
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {THEME['primary']}, stop:1 {THEME['secondary']});
                padding: 20px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        
        title = QLabel("شركة بن الحموي")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        date_label = QLabel(datetime.now().strftime("%Y-%m-%d"))
        date_label.setStyleSheet("color: white; font-size: 14px;")
        header_layout.addWidget(date_label)
        
        content_layout.addWidget(header)
        
        # منطقة الصفحات
        self.content_stack = QStackedWidget()
        
        self.pages = {
            "dashboard": DashboardWidget(self.current_user),
            "assets": AssetsWidget(self.current_user),
            "work_orders": WorkOrdersWidget(self.current_user),            "schedules": MaintenanceScheduleWidget(self.current_user),
            "inventory": InventoryWidget(self.current_user),
            "users": UsersWidget(self.current_user),
            "reports": ReportsWidget(self.current_user),
        }
        
        for page in self.pages.values():
            self.content_stack.addWidget(page)
        
        content_layout.addWidget(self.content_stack)
        
        # توقيع المطور
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['dark']};
                padding: 10px;
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        
        developer_label = QLabel("مطور البرنامج: محمد نجم الخطيب الحسني")
        developer_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        developer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(developer_label)
        
        content_layout.addWidget(footer)
        
        main_layout.addWidget(content_widget)
        
        self.show_page("dashboard")
    
    def show_page(self, page_key):
        for btn in self.menu_buttons:
            btn.setChecked(False)
        
        page_keys = list(self.pages.keys())
        if page_key in page_keys:
            index = page_keys.index(page_key)
            self.menu_buttons[index].setChecked(True)
            self.content_stack.setCurrentIndex(index)
    
    def logout(self):
        reply = QMessageBox.question(
            self, "تأكيد", "هل تريد تسجيل الخروج؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
# ==========================================
# 16. نقطة البداية
# ==========================================
class CMMSApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")
        
        init_db()
        create_default_admin()
        
        self.login_window = LoginWindow(self.on_login_success)
        self.login_window.show()
    
    def on_login_success(self, user):
        self.login_window.close()
        self.main_window = MainWindow(user)
        self.main_window.show()
    
    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = CMMSApp()
    app.run()