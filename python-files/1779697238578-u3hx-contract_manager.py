import sys
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
                             QPushButton, QDateEdit, QComboBox, QDialog, QFormLayout,
                             QMessageBox, QFileDialog, QLabel, QGroupBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont


def init_db():
    # 确保附件目录存在
    if not os.path.exists('attachments'):
        os.makedirs('attachments')
    # 连接数据库
    conn = sqlite3.connect('contracts.db')
    c = conn.cursor()
    # 创建合同表
    c.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            party_b TEXT NOT NULL,
            amount REAL,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT '履行中',
            notes TEXT,
            attachment TEXT
        )
    ''')
    conn.commit()
    conn.close()


class AddContractDialog(QDialog):
    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self.edit_data = edit_data
        self.attachment_path = None
        self.setWindowTitle("新增合同" if edit_data is None else "编辑合同")
        self.setFixedSize(500, 450)
        self.init_ui()
        if edit_data:
            self.fill_data()

    def init_ui(self):
        layout = QFormLayout()
        layout.setSpacing(15)

        # 合同编号
        self.contract_no = QLineEdit()
        layout.addRow("合同编号:", self.contract_no)

        # 合同名称
        self.name = QLineEdit()
        layout.addRow("合同名称:", self.name)

        # 对方单位
        self.party_b = QLineEdit()
        layout.addRow("对方单位:", self.party_b)

        # 合同金额
        self.amount = QLineEdit()
        layout.addRow("合同金额:", self.amount)

        # 生效日期
        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        layout.addRow("生效日期:", self.start_date)

        # 到期日期
        self.end_date = QDateEdit(QDate.currentDate().addMonths(12))
        self.end_date.setCalendarPopup(True)
        layout.addRow("到期日期:", self.end_date)

        # 状态
        self.status = QComboBox()
        self.status.addItems(["待履行", "履行中", "已到期", "已终止"])
        layout.addRow("合同状态:", self.status)

        # 备注
        self.notes = QLineEdit()
        layout.addRow("备注:", self.notes)

        # 附件
        self.attach_btn = QPushButton("选择附件")
        self.attach_btn.clicked.connect(self.select_attachment)
        self.attach_label = QLabel("未选择附件")
        attach_layout = QHBoxLayout()
        attach_layout.addWidget(self.attach_btn)
        attach_layout.addWidget(self.attach_label)
        layout.addRow("合同附件:", attach_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_contract)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def fill_data(self):
        # 编辑的时候填充数据
        self.contract_no.setText(self.edit_data[1])
        self.name.setText(self.edit_data[2])
        self.party_b.setText(self.edit_data[3])
        self.amount.setText(str(self.edit_data[4]) if self.edit_data[4] else "")
        if self.edit_data[5]:
            self.start_date.setDate(QDate.fromString(self.edit_data[5], "yyyy-MM-dd"))
        if self.edit_data[6]:
            self.end_date.setDate(QDate.fromString(self.edit_data[6], "yyyy-MM-dd"))
        self.status.setCurrentText(self.edit_data[7])
        self.notes.setText(self.edit_data[8] if self.edit_data[8] else "")
        if self.edit_data[9]:
            self.attachment_path = self.edit_data[9]
            self.attach_label.setText(os.path.basename(self.edit_data[9]))

    def select_attachment(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择合同文件", "", "所有文件 (*.*);;Word文档 (*.docx);;PDF文件 (*.pdf)")
        if file_path:
            self.attachment_path = file_path
            self.attach_label.setText(os.path.basename(file_path))

    def save_contract(self):
        # 获取数据
        contract_no = self.contract_no.text().strip()
        name = self.name.text().strip()
        party_b = self.party_b.text().strip()
        amount_text = self.amount.text().strip()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        status = self.status.currentText()
        notes = self.notes.text().strip()

        # 验证
        if not contract_no or not name or not party_b:
            QMessageBox.warning(self, "输入错误", "合同编号、名称、对方单位不能为空！")
            return
        try:
            amount = float(amount_text) if amount_text else None
        except:
            QMessageBox.warning(self, "输入错误", "合同金额必须是数字！")
            return

        # 处理附件
        attachment = None
        if self.attachment_path:
            # 如果是新的附件，复制到本地目录
            filename = os.path.basename(self.attachment_path)
            new_path = os.path.join('attachments', filename)
            # 如果文件不存在才复制，避免重复复制
            if not os.path.exists(new_path):
                shutil.copy2(self.attachment_path, new_path)
            attachment = new_path

        # 保存到数据库
        conn = sqlite3.connect('contracts.db')
        c = conn.cursor()
        try:
            if self.edit_data is None:
                # 新增
                c.execute('''
                    INSERT INTO contracts (contract_no, name, party_b, amount, start_date, end_date, status, notes, attachment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (contract_no, name, party_b, amount, start_date, end_date, status, notes, attachment))
            else:
                # 编辑
                c.execute('''
                    UPDATE contracts SET contract_no=?, name=?, party_b=?, amount=?, start_date=?, end_date=?, status=?, notes=?, attachment=?
                    WHERE id=?
                ''', (contract_no, name, party_b, amount, start_date, end_date, status, notes, attachment, self.edit_data[0]))
            conn.commit()
            QMessageBox.information(self, "成功", "合同保存成功！")
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "错误", "合同编号已存在，请修改！")
        finally:
            conn.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("本地合同管理系统")
        self.setGeometry(100, 100, 1200, 700)
        self.init_ui()
        self.check_reminder()

    def init_ui(self):
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部搜索栏
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索合同名称/对方单位/合同编号...")
        self.search_input.textChanged.connect(self.load_contracts)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.load_contracts)
        add_btn = QPushButton("新增合同")
        add_btn.clicked.connect(self.add_contract)
        backup_btn = QPushButton("备份数据")
        backup_btn.clicked.connect(self.backup_db)
        restore_btn = QPushButton("恢复数据")
        restore_btn.clicked.connect(self.restore_db)

        top_layout.addWidget(QLabel("搜索:"))
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(search_btn)
        top_layout.addStretch()
        top_layout.addWidget(add_btn)
        top_layout.addWidget(backup_btn)
        top_layout.addWidget(restore_btn)
        main_layout.addLayout(top_layout)

        # 合同表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "合同编号", "合同名称", "对方单位", "金额", "生效日期", "到期日期", "状态", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)

        # 加载数据
        self.load_contracts()

    def load_contracts(self):
        # 加载合同数据
        search_text = self.search_input.text().strip()
        conn = sqlite3.connect('contracts.db')
        c = conn.cursor()
        if search_text:
            c.execute('''
                SELECT * FROM contracts 
                WHERE name LIKE ? OR party_b LIKE ? OR contract_no LIKE ?
                ORDER BY end_date DESC
            ''', (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
        else:
            c.execute('SELECT * FROM contracts ORDER BY end_date DESC')
        contracts = c.fetchall()
        conn.close()

        self.table.setRowCount(len(contracts))
        for row, contract in enumerate(contracts):
            # contract: id, contract_no, name, party_b, amount, start_date, end_date, status, notes, attachment
            self.table.setItem(row, 0, QTableWidgetItem(str(contract[0])))
            self.table.setItem(row, 1, QTableWidgetItem(contract[1]))
            self.table.setItem(row, 2, QTableWidgetItem(contract[2]))
            self.table.setItem(row, 3, QTableWidgetItem(contract[3]))
            self.table.setItem(row, 4, QTableWidgetItem(f"{contract[4]:.2f}" if contract[4] else ""))
            self.table.setItem(row, 5, QTableWidgetItem(contract[5]))
            self.table.setItem(row, 6, QTableWidgetItem(contract[6]))
            # 状态，不同状态不同颜色
            status_item = QTableWidgetItem(contract[7])
            if contract[7] == "已到期":
                status_item.setForeground(Qt.red)
            elif contract[7] == "待履行":
                status_item.setForeground(Qt.blue)
            self.table.setItem(row, 7, status_item)

            # 操作按钮
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(2,2,2,2)
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda _, c=contract: self.edit_contract(c))
            del_btn = QPushButton("删除")
            del_btn.clicked.connect(lambda _, c=contract: self.delete_contract(c))
            if contract[9]:
                open_btn = QPushButton("打开附件")
                open_btn.clicked.connect(lambda _, p=contract[9]: self.open_attachment(p))
                layout.addWidget(open_btn)
            layout.addWidget(edit_btn)
            layout.addWidget(del_btn)
            self.table.setCellWidget(row, 8, widget)

    def add_contract(self):
        dialog = AddContractDialog(self)
        if dialog.exec_():
            self.load_contracts()

    def edit_contract(self, contract):
        dialog = AddContractDialog(self, edit_data=contract)
        if dialog.exec_():
            self.load_contracts()

    def delete_contract(self, contract):
        reply = QMessageBox.question(self, "确认删除", f"确定要删除合同【{contract[2]}】吗？此操作不可恢复！", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect('contracts.db')
            c = conn.cursor()
            c.execute('DELETE FROM contracts WHERE id=?', (contract[0],))
            conn.commit()
            conn.close()
            self.load_contracts()
            QMessageBox.information(self, "成功", "合同已删除！")

    def open_attachment(self, path):
        if os.path.exists(path):
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", path], check=True)
                else:
                    subprocess.run(["xdg-open", path], check=True)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"打开附件失败：{str(e)}")
        else:
            QMessageBox.warning(self, "错误", "附件文件不存在，可能已被移动或删除！")

    def check_reminder(self):
        # 检查到期提醒
        today = datetime.now().date()
        soon = today + timedelta(days=30)
        conn = sqlite3.connect('contracts.db')
        c = conn.cursor()
        c.execute('''
            SELECT name, end_date FROM contracts 
            WHERE end_date <= ? AND status != '已终止' AND status != '已到期'
            ORDER BY end_date
        ''', (soon.strftime("%Y-%m-%d"),))
        reminders = c.fetchall()
        conn.close()
        if reminders:
            msg = "以下合同即将在30天内到期，请及时处理：\n\n"
            for name, end_date in reminders:
                days = (datetime.strptime(end_date, "%Y-%m-%d").date() - today).days
                msg += f"【{name}】 到期日期: {end_date} (剩余{days}天)\n"
            QMessageBox.warning(self, "到期提醒", msg)

    def backup_db(self):
        # 备份数据库
        file_path, _ = QFileDialog.getSaveFileName(self, "备份数据", f"contracts_backup_{datetime.now().strftime('%Y%m%d')}.db", "数据库文件 (*.db)")
        if file_path:
            try:
                shutil.copy2('contracts.db', file_path)
                QMessageBox.information(self, "成功", f"数据已备份到：{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"备份失败：{str(e)}")

    def restore_db(self):
        # 恢复数据
        file_path, _ = QFileDialog.getOpenFileName(self, "恢复数据", "", "数据库文件 (*.db)")
        if file_path:
            reply = QMessageBox.question(self, "确认恢复", "恢复数据将覆盖当前所有数据，是否继续？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    shutil.copy2(file_path, 'contracts.db')
                    self.load_contracts()
                    QMessageBox.information(self, "成功", "数据恢复成功！")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"恢复失败：{str(e)}")


if __name__ == "__main__":
    # 初始化数据库
    init_db()
    app = QApplication(sys.argv)
    # 设置字体，支持中文
    font = QFont()
    font.setFamily("Microsoft YaHei" if sys.platform == "win32" else "WenQuanYi Micro Hei")
    font.setPointSize(9)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
