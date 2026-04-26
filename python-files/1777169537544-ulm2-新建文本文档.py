import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox


class CalculatorApp(QWidget):
    def __init__(self):
        super().__init__()

        # 初始化窗口
        self.setWindowTitle("药剂兑水计算器")
        self.setGeometry(100, 100, 400, 300)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 创建输入框
        self.dose_label = QLabel("药剂量 (g/kg/ml/l):")
        self.dose_entry = QLineEdit()

        self.water_label = QLabel("兑水量或兑水倍数:")
        self.water_entry = QLineEdit()

        self.calculate_button = QPushButton("计算")
        self.calculate_button.clicked.connect(self.calculate)

        layout.addWidget(self.dose_label)
        layout.addWidget(self.dose_entry)
        layout.addWidget(self.water_label)
        layout.addWidget(self.water_entry)
        layout.addWidget(self.calculate_button)

        self.setLayout(layout)

    def calculate(self):
        try:
            # 获取用户输入的药剂量和兑水量/兑水倍数
            dose = float(self.dose_entry.text())
            water = float(self.water_entry.text())

            # 判断输入的是兑水量还是兑水倍数
            if water <= 1:  # 兑水量
                amount_per_kg = dose / water
                self.show_message(f"每斤水需要药剂：{amount_per_kg:.2f} 单位")
            else:  # 兑水倍数
                total_water = dose * water
                self.show_message(f"药剂可兑水总量：{total_water:.2f} 单位")
                self.create_calculation_panel(dose, water)

        except ValueError:
            self.show_message("输入错误，请确保输入的是有效的数字", error=True)

    def show_message(self, message, error=False):
        """显示消息框"""
        msg_box = QMessageBox()
        msg_box.setText(message)
        if error:
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()

    def create_calculation_panel(self, dose, water):
        """创建计算面板"""
        self.dose_amount_label = QLabel("药剂量 (单位):")
        self.dose_amount_entry = QLineEdit()

        self.water_amount_label = QLabel("需要的水量 (斤):")
        self.water_amount_entry = QLineEdit()

        self.calculate_final_button = QPushButton("计算")
        self.calculate_final_button.clicked.connect(lambda: self.final_calculate(dose, water))

        layout = self.layout()
        layout.addWidget(self.dose_amount_label)
        layout.addWidget(self.dose_amount_entry)
        layout.addWidget(self.water_amount_label)
        layout.addWidget(self.water_amount_entry)
        layout.addWidget(self.calculate_final_button)

    def final_calculate(self, dose, water):
        try:
            water_amount = float(self.water_amount_entry.text())
            dose_amount = float(self.dose_amount_entry.text())

            if water_amount:
                result = dose * water_amount / dose_amount
                self.show_message(f"所需药剂量：{result:.2f} 单位")
            else:
                result = dose * dose_amount / water_amount
                self.show_message(f"所需兑水量：{result:.2f} 单位")

        except ValueError:
            self.show_message("输入错误，请确保输入的是有效的数字", error=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = CalculatorApp()
    calculator.show()
    sys.exit(app.exec_())