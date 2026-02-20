import sys
import sqlite3
import os
import shutil
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QStackedWidget, QDateEdit, QFormLayout,
    QScrollArea, QFrame, QFileDialog, QCompleter
)
from PyQt6.QtCore import Qt, QDate, QSize, QStringListModel
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor, QPalette
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import cm

# Configurações de Cores
COLOR_BACKGROUND = "#000000"
COLOR_TITLE = "#00FF00"  # Verde
COLOR_BUTTON = "#0000FF" # Azul
COLOR_TEXT = "#FFFFFF"
COLOR_FRAME = "#1E1E1E"
COLOR_ACCENT = "#2e7d32" # Verde escuro para destaque

class Database:
    def __init__(self):
        self.db_path = "lt_ingenieria.db"
        self.conn = None
        self.connect()
        self.create_table()
        self.migrate_db()

    def connect(self):
        if self.conn:
            self.conn.close()
        self.conn = sqlite3.connect(self.db_path)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                cliente TEXT,
                direcao TEXT,
                quantidade INTEGER,
                descricao TEXT,
                formula TEXT,
                valor_unitario REAL DEFAULT 0.0,
                total REAL DEFAULT 0.0,
                marca TEXT DEFAULT ''
            )
        """)
        self.conn.commit()

    def migrate_db(self):
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(vendas)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'marca' not in columns:
            cursor.execute("ALTER TABLE vendas ADD COLUMN marca TEXT DEFAULT ''")
            self.conn.commit()

    def salvar_venda(self, data, cliente, direcao, quantidade, descricao, formula, marca, valor_unitario=0.0):
        total = float(quantidade) * float(valor_unitario)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO vendas (data, cliente, direcao, quantidade, descricao, formula, marca, valor_unitario, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data, cliente, direcao, quantidade, descricao, formula, marca, valor_unitario, total))
        self.conn.commit()

    def buscar_por_cliente(self, nome):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vendas WHERE cliente LIKE ? ORDER BY data ASC", (f"%{nome}%",))
        return cursor.fetchall()

    def filtrar_vendas(self, cliente=None, data_inicio=None, data_fim=None):
        query = "SELECT * FROM vendas WHERE 1=1"
        params = []
        if cliente:
            query += " AND cliente LIKE ?"
            params.append(f"%{cliente}%")
        if data_inicio and data_fim:
            query += " AND data BETWEEN ? AND ?"
            params.extend([data_inicio, data_fim])
        elif data_inicio:
            query += " AND data = ?"
            params.append(data_inicio)
        
        query += " ORDER BY data ASC"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_autocomplete_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT cliente FROM vendas")
        clientes = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT descricao FROM vendas")
        descricoes = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT marca FROM vendas")
        marcas = [row[0] for row in cursor.fetchall() if row[0]]
        return clientes, descricoes, marcas

    def get_ultima_venda_cliente(self, cliente):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vendas WHERE cliente = ? ORDER BY id DESC LIMIT 1", (cliente,))
        return cursor.fetchone()

    def get_stats_mes_atual(self):
        hoje = date.today()
        inicio_mes = f"{hoje.year}-{hoje.month:02d}-01"
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(total), COUNT(id) FROM vendas WHERE data >= ?", (inicio_mes,))
        res = cursor.fetchone()
        return res if res[0] else (0.0, 0)

    def get_cliente_top(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT cliente, COUNT(id) as total FROM vendas GROUP BY cliente ORDER BY total DESC LIMIT 1")
        return cursor.fetchone()

    def fazer_backup(self):
        if os.path.exists(self.db_path):
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(self.db_path, f"{backup_dir}/backup_lt_{timestamp}.db")

    def restaurar_backup(self, file_path):
        try:
            if self.conn:
                self.conn.close()
            shutil.copy2(file_path, self.db_path)
            self.connect()
            return True
        except Exception as e:
            print(f"Erro ao restaurar: {e}")
            self.connect()
            return False

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LT Ingeniería - Login")
        self.setFixedSize(400, 500)
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND}; color: {COLOR_TEXT};")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label = QLabel()
        if os.path.exists("logo.jpg"):
            pixmap = QPixmap("logo.jpg")
            self.logo_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.logo_label.setText("LT Ingeniería")
            self.logo_label.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 24px; font-weight: bold;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)
        layout.addSpacing(30)
        title = QLabel("CONTROLE DE TINTAS")
        title.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(20)
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuário")
        self.user_input.setFixedSize(250, 40)
        self.user_input.setStyleSheet("padding: 5px; border: 1px solid #555; border-radius: 5px;")
        layout.addWidget(self.user_input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Senha")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setFixedSize(250, 40)
        self.pass_input.setStyleSheet("padding: 5px; border: 1px solid #555; border-radius: 5px;")
        layout.addWidget(self.pass_input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        login_btn = QPushButton("ENTRAR")
        login_btn.setFixedSize(250, 45)
        login_btn.setStyleSheet(f"background-color: {COLOR_BUTTON}; color: white; font-weight: bold; border-radius: 5px;")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def handle_login(self):
        if self.user_input.text() == "Berti" and self.pass_input.text() == "123":
            self.on_login_success()
        else:
            QMessageBox.warning(self, "Erro", "Usuário ou senha incorretos!")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LT Ingeniería - Controle de Tintas V4")
        self.setMinimumSize(1100, 750)
        self.setStyleSheet(f"background-color: {COLOR_BACKGROUND}; color: {COLOR_TEXT};")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.create_sidebar()
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)
        self.create_home_screen()
        self.create_venda_screen()
        self.create_historico_screen()
        self.create_relatorio_screen()
        self.create_config_screen()
        self.content_stack.setCurrentIndex(0)
        self.atualizar_dashboard()

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background-color: {COLOR_FRAME}; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        logo_small = QLabel()
        if os.path.exists("logo.jpg"):
            pixmap = QPixmap("logo.jpg")
            logo_small.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio))
        logo_small.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo_small)
        sidebar_layout.addSpacing(20)
        btn_style = f"""
            QPushButton {{ background-color: transparent; color: {COLOR_TEXT}; text-align: left; padding: 12px; font-size: 14px; border: none; border-radius: 5px; }}
            QPushButton:hover {{ background-color: #333; color: {COLOR_TITLE}; }}
        """
        btn_home = QPushButton("🏠 Início / Dashboard")
        btn_home.setStyleSheet(btn_style)
        btn_home.clicked.connect(lambda: [self.content_stack.setCurrentIndex(0), self.atualizar_dashboard()])
        sidebar_layout.addWidget(btn_home)
        btn_venda = QPushButton("📝 Nova Venda")
        btn_venda.setStyleSheet(btn_style)
        btn_venda.clicked.connect(lambda: [self.content_stack.setCurrentIndex(1), self.atualizar_autocomplete()])
        sidebar_layout.addWidget(btn_venda)
        btn_hist = QPushButton("📜 Histórico / Busca")
        btn_hist.setStyleSheet(btn_style)
        btn_hist.clicked.connect(lambda: [self.content_stack.setCurrentIndex(2), self.atualizar_tabela_historico()])
        sidebar_layout.addWidget(btn_hist)
        btn_rel = QPushButton("📄 Relatórios PDF")
        btn_rel.setStyleSheet(btn_style)
        btn_rel.clicked.connect(lambda: self.content_stack.setCurrentIndex(3))
        sidebar_layout.addWidget(btn_rel)
        btn_config = QPushButton("⚙️ Configurações / Backup")
        btn_config.setStyleSheet(btn_style)
        btn_config.clicked.connect(lambda: self.content_stack.setCurrentIndex(4))
        sidebar_layout.addWidget(btn_config)
        sidebar_layout.addStretch()
        logout_btn = QPushButton("🚪 Sair")
        logout_btn.setStyleSheet(btn_style)
        logout_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(logout_btn)
        self.main_layout.addWidget(sidebar)

    def create_home_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        title = QLabel("BEM-VINDO, BERTI")
        title.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        cards_layout = QHBoxLayout()
        self.card_vendas_mes = self.create_card("VENDAS NO MÊS", "gs 0,000", "#1565c0")
        self.card_qtd_vendas = self.create_card("TOTAL DE PEDIDOS", "0", "#2e7d32")
        self.card_top_cliente = self.create_card("CLIENTE TOP", "Nenhum", "#c62828")
        cards_layout.addWidget(self.card_vendas_mes)
        cards_layout.addWidget(self.card_qtd_vendas)
        cards_layout.addWidget(self.card_top_cliente)
        layout.addLayout(cards_layout)
        layout.addSpacing(40)
        layout.addWidget(QLabel("ATALHOS RÁPIDOS"))
        btn_row = QHBoxLayout()
        btn_venda_rapida = QPushButton("Nova Venda")
        btn_venda_rapida.setFixedSize(200, 60)
        btn_venda_rapida.setStyleSheet(f"background-color: {COLOR_BUTTON}; color: white; font-weight: bold; border-radius: 10px;")
        btn_venda_rapida.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))
        btn_rel_rapido = QPushButton("Relatório Mensal")
        btn_rel_rapido.setFixedSize(200, 60)
        btn_rel_rapido.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; font-weight: bold; border-radius: 10px;")
        btn_rel_rapido.clicked.connect(self.gerar_relatorio_mensal)
        btn_row.addWidget(btn_venda_rapida)
        btn_row.addWidget(btn_rel_rapido)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()
        self.content_stack.addWidget(screen)

    def create_card(self, title, value, color):
        card = QFrame()
        card.setFixedSize(250, 150)
        card.setStyleSheet(f"background-color: {COLOR_FRAME}; border-left: 5px solid {color}; border-radius: 10px;")
        layout = QVBoxLayout(card)
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #aaa; font-size: 12px; font-weight: bold;")
        v_label = QLabel(value)
        v_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        v_label.setWordWrap(True)
        layout.addWidget(t_label)
        layout.addWidget(v_label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.value_label = v_label
        return card

    def create_venda_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        title = QLabel("CADASTRO DE VENDA")
        title.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        form_frame = QFrame()
        form_frame.setStyleSheet(f"background-color: {COLOR_FRAME}; border-radius: 10px; padding: 20px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        self.venda_data = QDateEdit(QDate.currentDate())
        self.venda_data.setCalendarPopup(True)
        self.venda_data.setStyleSheet("padding: 5px; color: white;")
        self.venda_cliente = QLineEdit()
        self.venda_direcao = QLineEdit()
        self.venda_quantidade = QLineEdit()
        self.venda_valor = QLineEdit("0.0")
        self.venda_marca = QLineEdit()
        self.venda_descricao = QLineEdit()
        self.venda_formula = QLineEdit()
        self.completer_cliente = QCompleter()
        self.venda_cliente.setCompleter(self.completer_cliente)
        self.completer_desc = QCompleter()
        self.venda_descricao.setCompleter(self.completer_desc)
        self.completer_marca = QCompleter()
        self.venda_marca.setCompleter(self.completer_marca)
        input_style = "padding: 8px; background-color: #2b2b2b; border: 1px solid #444; color: white; border-radius: 3px;"
        for widget in [self.venda_cliente, self.venda_direcao, self.venda_quantidade, self.venda_valor, self.venda_marca, self.venda_descricao, self.venda_formula]:
            widget.setStyleSheet(input_style)
        btn_repetir = QPushButton("🔄 Repetir Última Fórmula")
        btn_repetir.setStyleSheet(f"background-color: #444; color: {COLOR_TITLE}; padding: 5px; border-radius: 3px;")
        btn_repetir.clicked.connect(self.repetir_ultima_venda)
        form_layout.addRow("Data:", self.venda_data)
        form_layout.addRow("Cliente:", self.venda_cliente)
        form_layout.addRow("", btn_repetir)
        form_layout.addRow("Direção:", self.venda_direcao)
        form_layout.addRow("Quantidade:", self.venda_quantidade)
        form_layout.addRow("Valor Unitário:", self.venda_valor)
        form_layout.addRow("Marca da Tinta:", self.venda_marca)
        form_layout.addRow("Descrição da Tinta:", self.venda_descricao)
        form_layout.addRow("Fórmula da Tinta:", self.venda_formula)
        layout.addWidget(form_frame)
        save_btn = QPushButton("SALVAR VENDA")
        save_btn.setFixedSize(200, 50)
        save_btn.setStyleSheet(f"background-color: {COLOR_BUTTON}; color: white; font-weight: bold; border-radius: 5px; margin-top: 20px;")
        save_btn.clicked.connect(self.salvar_venda)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self.content_stack.addWidget(screen)

    def create_historico_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        title = QLabel("HISTÓRICO E BUSCA")
        title.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por cliente...")
        self.search_input.setStyleSheet("padding: 8px; background-color: #2b2b2b; color: white;")
        self.search_input.textChanged.connect(self.atualizar_tabela_historico)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Data", "Cliente", "Direção", "Qtd", "Marca", "Descrição", "Fórmula", "V. Unit", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e1e1e; color: white; gridline-color: #333; border: none; }
            QHeaderView::section { background-color: #333; color: #00FF00; padding: 5px; border: 1px solid #111; }
        """)
        layout.addWidget(self.table)
        self.content_stack.addWidget(screen)

    def create_relatorio_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        title = QLabel("GERAR RELATÓRIOS PDF")
        title.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        rel_frame = QFrame()
        rel_frame.setStyleSheet(f"background-color: {COLOR_FRAME}; border-radius: 10px; padding: 20px;")
        rel_layout = QVBoxLayout(rel_frame)
        rel_layout.addWidget(QLabel("Relatório por Período:"))
        periodo_layout = QHBoxLayout()
        self.rel_inicio = QDateEdit(QDate.currentDate().addMonths(-1))
        self.rel_inicio.setCalendarPopup(True)
        self.rel_fim = QDateEdit(QDate.currentDate())
        self.rel_fim.setCalendarPopup(True)
        periodo_layout.addWidget(QLabel("De:"))
        periodo_layout.addWidget(self.rel_inicio)
        periodo_layout.addWidget(QLabel("Até:"))
        periodo_layout.addWidget(self.rel_fim)
        rel_layout.addLayout(periodo_layout)
        btn_periodo = QPushButton("Gerar Relatório por Período")
        btn_periodo.setStyleSheet(f"background-color: {COLOR_BUTTON}; color: white; padding: 10px; margin-top: 10px;")
        btn_periodo.clicked.connect(self.gerar_relatorio_periodo)
        rel_layout.addWidget(btn_periodo)
        rel_layout.addSpacing(30)
        rel_layout.addWidget(QLabel("Relatórios Rápidos:"))
        btn_mensal = QPushButton("Gerar Relatório do Mês Atual")
        btn_mensal.setStyleSheet(f"background-color: #2e7d32; color: white; padding: 10px;")
        btn_mensal.clicked.connect(self.gerar_relatorio_mensal)
        rel_layout.addWidget(btn_mensal)
        btn_anual = QPushButton("Gerar Relatório do Ano Atual")
        btn_anual.setStyleSheet(f"background-color: #1565c0; color: white; padding: 10px; margin-top: 5px;")
        btn_anual.clicked.connect(self.gerar_relatorio_anual)
        rel_layout.addWidget(btn_anual)
        layout.addWidget(rel_frame)
        layout.addStretch()
        self.content_stack.addWidget(screen)

    def create_config_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        title = QLabel("CONFIGURAÇÕES E BACKUP")
        title.setStyleSheet(f"color: {COLOR_TITLE}; font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        config_frame = QFrame()
        config_frame.setStyleSheet(f"background-color: {COLOR_FRAME}; border-radius: 10px; padding: 20px;")
        config_layout = QVBoxLayout(config_frame)
        
        config_layout.addWidget(QLabel("Gerenciamento de Dados:"))
        config_layout.addSpacing(10)
        
        btn_backup = QPushButton("💾 Criar Backup Manual Agora")
        btn_backup.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; padding: 15px; font-weight: bold; border-radius: 5px;")
        btn_backup.clicked.connect(self.manual_backup)
        config_layout.addWidget(btn_backup)
        
        config_layout.addSpacing(20)
        
        btn_restore = QPushButton("📂 Restaurar Banco de Dados (Carregar Backup)")
        btn_restore.setStyleSheet(f"background-color: #c62828; color: white; padding: 15px; font-weight: bold; border-radius: 5px;")
        btn_restore.clicked.connect(self.restore_backup_dialog)
        config_layout.addWidget(btn_restore)
        
        config_layout.addSpacing(20)
        config_layout.addWidget(QLabel("ℹ️ Ao restaurar um backup, os dados atuais serão substituídos."))
        config_layout.addWidget(QLabel("ℹ️ O sistema faz backup automático toda vez que é fechado."))
        
        layout.addWidget(config_frame)
        layout.addStretch()
        self.content_stack.addWidget(screen)

    def manual_backup(self):
        self.db.fazer_backup()
        QMessageBox.information(self, "Sucesso", "Backup criado com sucesso na pasta 'backups'!")

    def restore_backup_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Backup", "backups", "SQLite Database (*.db)")
        if file_path:
            confirm = QMessageBox.question(self, "Confirmar Restauração", 
                                         "Você tem certeza que deseja restaurar este backup?\nTodos os dados atuais serão substituídos!",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                if self.db.restaurar_backup(file_path):
                    QMessageBox.information(self, "Sucesso", "Banco de dados restaurado com sucesso!")
                    self.atualizar_dashboard()
                    self.content_stack.setCurrentIndex(0)
                else:
                    QMessageBox.critical(self, "Erro", "Falha ao restaurar o banco de dados.")

    def atualizar_dashboard(self):
        total_mes, qtd_mes = self.db.get_stats_mes_atual()
        self.card_vendas_mes.value_label.setText(f"Gs {total_mes:,.2f}")
        self.card_qtd_vendas.value_label.setText(str(qtd_mes))
        top_cliente = self.db.get_cliente_top()
        if top_cliente:
            self.card_top_cliente.value_label.setText(f"{top_cliente[0]} ({top_cliente[1]})")
        else:
            self.card_top_cliente.value_label.setText("Nenhum")

    def atualizar_autocomplete(self):
        clientes, descricoes, marcas = self.db.get_autocomplete_data()
        self.completer_cliente.setModel(QStringListModel(clientes))
        self.completer_desc.setModel(QStringListModel(descricoes))
        self.completer_marca.setModel(QStringListModel(marcas))

    def repetir_ultima_venda(self):
        cliente = self.venda_cliente.text()
        if not cliente:
            QMessageBox.warning(self, "Aviso", "Digite o nome do cliente primeiro.")
            return
        venda = self.db.get_ultima_venda_cliente(cliente)
        if venda:
            self.venda_direcao.setText(venda[3])
            self.venda_descricao.setText(venda[5])
            self.venda_formula.setText(venda[6])
            self.venda_valor.setText(str(venda[7]))
            if len(venda) > 9:
                self.venda_marca.setText(venda[9])
        else:
            QMessageBox.information(self, "Aviso", "Nenhuma venda anterior encontrada para este cliente.")

    def salvar_venda(self):
        try:
            data = self.venda_data.date().toString("yyyy-MM-dd")
            cliente = self.venda_cliente.text()
            direcao = self.venda_direcao.text()
            quantidade = self.venda_quantidade.text()
            descricao = self.venda_descricao.text()
            formula = self.venda_formula.text()
            marca = self.venda_marca.text()
            valor = self.venda_valor.text()
            if not all([cliente, direcao, quantidade, descricao, formula]):
                QMessageBox.warning(self, "Erro", "Preencha todos os campos obrigatórios!")
                return
            self.db.salvar_venda(data, cliente, direcao, int(quantidade), descricao, formula, marca, float(valor))
            QMessageBox.information(self, "Sucesso", "Venda salva com sucesso!")
            self.venda_cliente.clear()
            self.venda_direcao.clear()
            self.venda_quantidade.clear()
            self.venda_valor.setText("0.0")
            self.venda_marca.clear()
            self.venda_descricao.clear()
            self.venda_formula.clear()
            self.atualizar_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    def atualizar_tabela_historico(self):
        nome = self.search_input.text()
        vendas = self.db.buscar_por_cliente(nome)
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(vendas):
            self.table.insertRow(row_idx)
            display_indices = [1, 2, 3, 4, 9, 5, 6, 7, 8]
            for col_idx, db_idx in enumerate(display_indices):
                if db_idx < len(row_data):
                    val = row_data[db_idx]
                    item = QTableWidgetItem(str(val))
                    item.setForeground(QColor("white"))
                    self.table.setItem(row_idx, col_idx, item)

    def gerar_relatorio_periodo(self):
        d_inicio = self.rel_inicio.date().toString("yyyy-MM-dd")
        d_fim = self.rel_fim.date().toString("yyyy-MM-dd")
        vendas = self.db.filtrar_vendas(data_inicio=d_inicio, data_fim=d_fim)
        self.exportar_pdf(vendas, d_inicio, d_fim)

    def gerar_relatorio_mensal(self):
        hoje = date.today()
        d_inicio = f"{hoje.year}-{hoje.month:02d}-01"
        d_fim = hoje.strftime("%Y-%m-%d")
        vendas = self.db.filtrar_vendas(data_inicio=d_inicio, data_fim=d_fim)
        self.exportar_pdf(vendas, d_inicio, d_fim, "Mensal")

    def gerar_relatorio_anual(self):
        hoje = date.today()
        d_inicio = f"{hoje.year}-01-01"
        d_fim = hoje.strftime("%Y-%m-%d")
        vendas = self.db.filtrar_vendas(data_inicio=d_inicio, data_fim=d_fim)
        self.exportar_pdf(vendas, d_inicio, d_fim, "Anual")

    def exportar_pdf(self, vendas, d_inicio, d_fim, tipo="Periodo"):
        if not vendas:
            QMessageBox.warning(self, "Aviso", "Nenhuma venda encontrada no período.")
            return
        filename = f"Relatorio_LT_{d_inicio}_a_{d_fim}.pdf"
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            if os.path.exists("logo.jpg"):
                img = Image("logo.jpg", 2*cm, 2*cm)
                elements.append(img)
            title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.green)
            elements.append(Paragraph("LT Ingeniería - Controle de Tintas", title_style))
            elements.append(Paragraph(f"Relatório {tipo}: {d_inicio} até {d_fim}", styles['Normal']))
            elements.append(Paragraph(f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 12))
            data = [["Data", "Cliente", "Qtd", "Marca", "Descrição", "Fórmula", "Total"]]
            total_qtd = 0
            total_valor = 0
            for v in vendas:
                marca = v[9] if len(v) > 9 else ""
                data.append([v[1], v[2], str(v[4]), marca, v[5], v[6], f"Gs {v[8]:,.000f}"])
                total_qtd += v[4]
                total_valor += v[8]
            t = Table(data, colWidths=[2.2*cm, 3.5*cm, 1.2*cm, 2.5*cm, 3.5*cm, 3.5*cm, 2.2*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Total de Registros: {len(vendas)}", styles['Normal']))
            elements.append(Paragraph(f"Quantidade Total Vendida: {total_qtd}", styles['Normal']))
            elements.append(Paragraph(f"Valor Total Geral: Gs {total_valor:.2f}", styles['Normal']))
            doc.build(elements)
            QMessageBox.information(self, "Sucesso", f"Relatório gerado: {filename}")
            if sys.platform == "win32": os.startfile(filename)
            elif sys.platform == "darwin": os.system(f"open {filename}")
            else: os.system(f"xdg-open {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar PDF: {str(e)}")

    def closeEvent(self, event):
        self.db.fazer_backup()
        event.accept()

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow(self.show_main)
        self.main_window = None

    def run(self):
        self.login_window.show()
        sys.exit(self.app.exec())

    def show_main(self):
        self.main_window = MainWindow()
        self.main_window.show()
        self.login_window.close()

if __name__ == "__main__":
    controller = AppController()
    controller.run()
