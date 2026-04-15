import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from scipy import stats


class DataAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()

        # -------------------- ОКНО --------------------
        self.setWindowTitle("Анализ экспериментальных данных")
        self.setGeometry(100, 100, 1250, 750)

        # -------------------- СТИЛЬ --------------------
        self.setStyleSheet("""
        QWidget {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #e3f2fd,
                stop:1 #fce4ec
            );
            font-family: "Segoe UI";
            font-size: 14px;
        }

        QLabel {
            font-weight: bold;
            color: #0d47a1;
        }

        QTextEdit {
            background-color: white;
            border: 2px solid #64b5f6;
            border-radius: 8px;
            padding: 8px;
        }

        QPushButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #42a5f5,
                stop:1 #ab47bc
            );
            color: white;
            font-size: 15px;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px 22px;
        }

        QPushButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #1e88e5,
                stop:1 #8e24aa
            );
        }

        QTabWidget::pane {
            border: 2px solid #90caf9;
            border-radius: 10px;
            background: white;
        }

        QTabBar::tab {
            background: #bbdefb;
            padding: 10px 22px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin-right: 4px;
        }

        QTabBar::tab:selected {
            background: #ffffff;
            font-weight: bold;
            color: #6a1b9a;
        }

        QTableWidget {
            background-color: white;
            border: 2px solid #ce93d8;
            border-radius: 8px;
            gridline-color: #e1bee7;
        }

        QHeaderView::section {
            background-color: #ce93d8;
            color: white;
            padding: 8px;
            font-weight: bold;
            border: none;
        }

        QTableWidget::item:selected {
            background-color: #f8bbd0;
            color: black;
        }
        """)

        # -------------------- LAYOUT --------------------
        main_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        self.label = QLabel("Введите экспериментальные значения:")
        self.label.setMinimumWidth(340)

        self.input_text = QTextEdit()
        self.input_text.setFixedHeight(55)
        self.input_text.setPlaceholderText(
            "Пример: 5.1 -2.7 1.1 1.7 -1.5 0 2.8 0.9"
        )

        input_layout.addWidget(self.label)
        input_layout.addWidget(self.input_text)
        main_layout.addLayout(input_layout)

        self.button = QPushButton("АНАЛИЗИРОВАТЬ")
        self.button.clicked.connect(self.analyze_data)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.button)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ===== Таблицы =====
        self.tab_table = QWidget()
        table_layout = QVBoxLayout()

        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setFixedHeight(210)

        table_layout.addWidget(self.table_widget)
        table_layout.addWidget(self.text_output)

        self.tab_table.setLayout(table_layout)
        self.tabs.addTab(self.tab_table, "📊 Таблицы и расчёты")

        # ===== Графики =====
        self.tab_graphs = QWidget()
        graph_layout = QVBoxLayout()

        self.canvas = FigureCanvas(plt.Figure(figsize=(11, 5)))
        graph_layout.addWidget(self.canvas)

        self.tab_graphs.setLayout(graph_layout)
        self.tabs.addTab(self.tab_graphs, "📈 Графики")

        # ===== Проверка =====
        self.tab_tests = QWidget()
        test_layout = QVBoxLayout()

        self.test_output = QTextEdit()
        self.test_output.setReadOnly(True)

        test_layout.addWidget(self.test_output)
        self.tab_tests.setLayout(test_layout)

        self.tabs.addTab(self.tab_tests, "🧪 Проверка")

        self.setLayout(main_layout)

    # ==================================================
    def analyze_data(self):
        try:
            data = [float(x) for x in self.input_text.toPlainText().split()]
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите числа через пробел!")
            return

        if len(data) < 2:
            QMessageBox.warning(self, "Ошибка", "Минимум два значения!")
            return

        sorted_data = np.sort(data)
        n = len(data)
        k = 7

        freq, bins = np.histogram(data, bins=k)
        h = bins[1] - bins[0]

        intervals = [f"[{bins[i]:.2f}; {bins[i+1]:.2f})" for i in range(k)]
        density = freq / (n * h)

        mean = np.mean(data)
        var = np.var(data, ddof=1)
        sigma = np.sqrt(var)

        # доверительный интервал
        alpha = 0.01
        z = stats.norm.ppf(1 - alpha / 2)
        ci = (mean - z * sigma / np.sqrt(n),
              mean + z * sigma / np.sqrt(n))

        # ---------- χ² ----------
        expected = [
            n * (stats.norm.cdf(bins[i+1], mean, sigma) -
                 stats.norm.cdf(bins[i], mean, sigma))
            for i in range(k)
        ]

        chi2 = np.sum((freq - expected) ** 2 / expected)
        df = k - 1 - 2
        p = 1 - stats.chi2.cdf(chi2, df)

        chi_warning = any(e < 5 for e in expected)

        # ---------- Доп тесты ----------
        ks_stat, ks_p = stats.kstest(data, 'norm', args=(mean, sigma))
        shapiro_stat, shapiro_p = stats.shapiro(data)
        anderson = stats.anderson(data, dist='norm')

        # ---------- Таблица ----------
        self.table_widget.clear()
        self.table_widget.setRowCount(k)
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(
            ["Интервал", "Частота", "Эмпирическая плотность"]
        )

        for i in range(k):
            for j, val in enumerate([intervals[i], freq[i], f"{density[i]:.4f}"]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(i, j, item)

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # ---------- Основной вывод ----------
        self.text_output.setText(
            f"Вариационный ряд:\n{sorted_data}\n\n"
            f"Среднее: {mean:.4f}\n"
            f"Дисперсия: {var:.4f}\n"
            f"σ: {sigma:.4f}\n\n"
            f"Доверительный интервал (γ=0.99):\n"
            f"[{ci[0]:.4f}; {ci[1]:.4f}]\n\n"
            f"χ² = {chi2:.4f}\n"
            f"p-value = {p:.4f}\n\n"
            f"Результат: {'Отвергаем H₀' if p < 0.05 else 'Не отвергаем H₀'}"
        )

        # ---------- ПРОВЕРКА ----------
        alpha_test = 0.05

        chi_decision = p > alpha_test
        ks_decision = ks_p > alpha_test
        shapiro_decision = shapiro_p > alpha_test
        anderson_decision = anderson.statistic < anderson.critical_values[2]

        decisions = [chi_decision, ks_decision, shapiro_decision, anderson_decision]
        accept_count = sum(decisions)

        final_decision = "НЕ ОТВЕРГАЕМ H₀ (данные нормальные)" \
            if accept_count >= 3 else \
            "ОТВЕРГАЕМ H₀ (данные НЕ нормальные)"

        warning = ""
        if chi_warning:
            warning = "\n⚠ Есть интервалы с expected < 5 (χ² неточен)\n"

        self.test_output.setText(
            "══════════════════════════════════════\n"
            "        ПРОВЕРКА ГИПОТЕЗЫ H₀\n"
            "   H₀: данные имеют нормальное распределение\n"
            "   α = 0.05\n"
            "══════════════════════════════════════\n\n"

            "1. χ² критерий\n"
            f"   p = {p:.4f}\n"
            f"   {'✔ НЕ отвергаем H₀' if chi_decision else '✖ ОТВЕРГАЕМ H₀'}\n\n"

            "2. Колмогоров–Смирнов\n"
            f"   p = {ks_p:.4f}\n"
            f"   {'✔ НЕ отвергаем H₀' if ks_decision else '✖ ОТВЕРГАЕМ H₀'}\n\n"

            "3. Шапиро–Уилк\n"
            f"   p = {shapiro_p:.4f}\n"
            f"   {'✔ НЕ отвергаем H₀' if shapiro_decision else '✖ ОТВЕРГАЕМ H₀'}\n\n"

            "4. Андерсон–Дарлинг\n"
            f"   Статистика = {anderson.statistic:.4f}\n"
            f"   Критическое (5%) = {anderson.critical_values[2]:.4f}\n"
            f"   {'✔ НЕ отвергаем H₀' if anderson_decision else '✖ ОТВЕРГАЕМ H₀'}\n\n"

            "──────────────────────────────────────\n"
            f"📊 Итог:\n{final_decision}\n"
            "──────────────────────────────────────\n"
            f"{warning}"
        )

        # ---------- Графики ----------
        plt.style.use("seaborn-v0_8-whitegrid")
        self.canvas.figure.clf()

        ax1 = self.canvas.figure.add_subplot(121)
        ax2 = self.canvas.figure.add_subplot(122)

        ax1.hist(sorted_data, bins=k, edgecolor="black", alpha=0.85)
        centers = (bins[:-1] + bins[1:]) / 2
        ax1.plot(centers, freq, marker="o", linewidth=2)
        ax1.set_title("Гистограмма и полигон")

        ecdf = np.arange(1, n + 1) / n
        ax2.step(sorted_data, ecdf, where="post", linewidth=2)
        ax2.set_title("Эмпирическая функция")

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())