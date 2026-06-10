import sys
import os
import webbrowser
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
)


# =========================
# 统计函数
# =========================

def reconstruct_group_data(n, mean, sd):
    """
    构造一组 synthetic / reconstructed 数据，
    使其样本均值和样本标准差与目标 mean、sd 一致。

    注意：
    本函数生成的是模拟/重建数据，不是真实原始实验数据。
    """
    if n < 2:
        raise ValueError("每组样本量 n 必须至少为 2")
    if sd < 0:
        raise ValueError("标准差 sd 不能为负")

    if sd == 0:
        return np.full(n, mean)

    base = np.linspace(-1, 1, n)
    base = base - np.mean(base)
    base = base / np.std(base, ddof=1)

    values = mean + sd * base
    return values


def generate_dataset(groups):
    """
    根据每组的 n、mean、sd 生成模拟/重建数据集。
    """
    records = []

    for group in groups:
        group_name = group["group"]
        n = int(group["n"])
        mean = float(group["mean"])
        sd = float(group["sd"])

        values = reconstruct_group_data(n, mean, sd)

        for i, value in enumerate(values, start=1):
            records.append({
                "subject_id": f"{group_name}_{i}",
                "group": group_name,
                "value": value,
                "data_type": "synthetic_reconstructed"
            })

    return pd.DataFrame(records)


def descriptive_stats(df):
    """
    各组描述性统计。
    """
    return (
        df.groupby("group")["value"]
        .agg(
            n="count",
            mean="mean",
            sd=lambda x: x.std(ddof=1),
            min="min",
            max="max"
        )
        .reset_index()
    )


def one_way_anova(df):
    """
    单因素 ANOVA。
    """
    group_values = [
        sub["value"].values
        for _, sub in df.groupby("group")
    ]

    f_stat, p_value = stats.f_oneway(*group_values)

    return pd.DataFrame([{
        "F": f_stat,
        "p": p_value
    }])


def fisher_lsd(df, alpha=0.05):
    """
    Fisher's LSD 两两比较。

    计算逻辑：
    1. 使用单因素 ANOVA 的组内均方误差 MSE
    2. 进行两两 t 检验
    3. 给出 LSD 临界差、置信区间和显著性判断
    """
    groups = list(df["group"].unique())
    k = len(groups)
    n_total = len(df)

    if k < 2:
        raise ValueError("至少需要两组才能进行 LSD 检验")

    sse = 0
    group_info = {}

    for g in groups:
        values = df[df["group"] == g]["value"].values
        n = len(values)
        mean = np.mean(values)
        sd = np.std(values, ddof=1)

        sse += np.sum((values - mean) ** 2)

        group_info[g] = {
            "n": n,
            "mean": mean,
            "sd": sd
        }

    df_error = n_total - k

    if df_error <= 0:
        raise ValueError("误差自由度不足，无法进行 LSD 检验")

    mse = sse / df_error
    results = []

    for g1, g2 in combinations(groups, 2):
        n1 = group_info[g1]["n"]
        n2 = group_info[g2]["n"]
        mean1 = group_info[g1]["mean"]
        mean2 = group_info[g2]["mean"]

        mean_diff = mean1 - mean2
        se = np.sqrt(mse * (1 / n1 + 1 / n2))

        if se == 0:
            t_value = np.nan
            p_value = np.nan
            lsd_value = 0
            ci_low = np.nan
            ci_high = np.nan
            significant = False
        else:
            t_value = mean_diff / se
            p_value = 2 * (1 - stats.t.cdf(abs(t_value), df_error))

            t_critical = stats.t.ppf(1 - alpha / 2, df_error)
            lsd_value = t_critical * se

            ci_low = mean_diff - lsd_value
            ci_high = mean_diff + lsd_value

            significant = p_value < alpha

        results.append({
            "group_1": g1,
            "group_2": g2,
            "n_1": n1,
            "n_2": n2,
            "mean_1": mean1,
            "mean_2": mean2,
            "mean_difference": mean_diff,
            "standard_error": se,
            "t": t_value,
            "df_error": df_error,
            "p": p_value,
            "LSD_critical_difference": lsd_value,
            "CI_low": ci_low,
            "CI_high": ci_high,
            "significant": significant
        })

    return pd.DataFrame(results)


# =========================
# GUI 主界面
# =========================

class SyntheticDataApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("科研模拟重建数据生成器（增强版）")
        self.resize(950, 720)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.info_label = QLabel(
            "输入各组参数：组名、样本量 n、均值 mean、标准差 sd。\n"
            "本软件生成 synthetic / reconstructed data，仅用于统计复现、教学演示或方法验证。"
        )
        self.layout.addWidget(self.info_label)

        self.table = QTableWidget(3, 4)
        self.table.setHorizontalHeaderLabels(["组名", "样本量 n", "均值 mean", "标准差 sd"])

        default_names = ["Control", "Treatment_A", "Treatment_B"]
        for i in range(3):
            self.table.setItem(i, 0, QTableWidgetItem(default_names[i]))
            self.table.setItem(i, 1, QTableWidgetItem("20"))
            self.table.setItem(i, 2, QTableWidgetItem(str(10 + 2 * i)))
            self.table.setItem(i, 3, QTableWidgetItem("2.0"))

        self.layout.addWidget(self.table)

        # 增删组按钮
        self.group_btn_layout = QHBoxLayout()

        self.add_row_btn = QPushButton("增加组")
        self.add_row_btn.clicked.connect(self.add_row)

        self.remove_row_btn = QPushButton("删除最后一组")
        self.remove_row_btn.clicked.connect(self.remove_row)

        self.group_btn_layout.addWidget(self.add_row_btn)
        self.group_btn_layout.addWidget(self.remove_row_btn)
        self.layout.addLayout(self.group_btn_layout)

        # alpha 输入
        self.alpha_layout = QHBoxLayout()

        self.alpha_label = QLabel("显著性水平 alpha：")
        self.alpha_input = QLineEdit("0.05")

        self.alpha_layout.addWidget(self.alpha_label)
        self.alpha_layout.addWidget(self.alpha_input)

        self.layout.addLayout(self.alpha_layout)

        # 生成按钮
        self.generate_btn = QPushButton("生成数据并导出 CSV")
        self.generate_btn.clicked.connect(self.generate_data)
        self.layout.addWidget(self.generate_btn)

        self.notice_label = QLabel(
            "导出文件包括：synthetic_reconstructed_data.csv、descriptive_statistics.csv、"
            "anova_results.csv、fisher_lsd_results.csv。"
        )
        self.layout.addWidget(self.notice_label)

    def add_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        self.table.setItem(row_count, 0, QTableWidgetItem(f"Group_{row_count + 1}"))
        self.table.setItem(row_count, 1, QTableWidgetItem("20"))
        self.table.setItem(row_count, 2, QTableWidgetItem("10.0"))
        self.table.setItem(row_count, 3, QTableWidgetItem("2.0"))

    def remove_row(self):
        row_count = self.table.rowCount()

        if row_count <= 2:
            QMessageBox.warning(self, "不能删除", "至少需要保留两组。")
            return

        self.table.removeRow(row_count - 1)

    def read_groups_from_table(self):
        groups = []

        for i in range(self.table.rowCount()):
            group_item = self.table.item(i, 0)
            n_item = self.table.item(i, 1)
            mean_item = self.table.item(i, 2)
            sd_item = self.table.item(i, 3)

            if group_item is None or n_item is None or mean_item is None or sd_item is None:
                raise ValueError(f"第 {i + 1} 行存在空白单元格，请填写完整。")

            group_name = group_item.text().strip()
            if not group_name:
                raise ValueError(f"第 {i + 1} 行组名不能为空。")

            n = int(n_item.text())
            mean = float(mean_item.text())
            sd = float(sd_item.text())

            if n < 2:
                raise ValueError(f"第 {i + 1} 行样本量 n 必须至少为 2。")
            if sd < 0:
                raise ValueError(f"第 {i + 1} 行标准差 sd 不能为负。")

            groups.append({
                "group": group_name,
                "n": n,
                "mean": mean,
                "sd": sd
            })

        group_names = [g["group"] for g in groups]
        if len(group_names) != len(set(group_names)):
            raise ValueError("组名不能重复，请修改后再生成。")

        return groups

    def generate_data(self):
        try:
            groups = self.read_groups_from_table()
            alpha = float(self.alpha_input.text())

            if not (0 < alpha < 1):
                raise ValueError("alpha 必须在 0 到 1 之间，例如 0.05。")

            df = generate_dataset(groups)
            desc = descriptive_stats(df)
            anova = one_way_anova(df)
            lsd = fisher_lsd(df, alpha)

            folder = QFileDialog.getExistingDirectory(self, "选择导出文件夹")

            if folder:
                df.to_csv(
                    os.path.join(folder, "synthetic_reconstructed_data.csv"),
                    index=False,
                    encoding="utf-8-sig"
                )
                desc.to_csv(
                    os.path.join(folder, "descriptive_statistics.csv"),
                    index=False,
                    encoding="utf-8-sig"
                )
                anova.to_csv(
                    os.path.join(folder, "anova_results.csv"),
                    index=False,
                    encoding="utf-8-sig"
                )
                lsd.to_csv(
                    os.path.join(folder, "fisher_lsd_results.csv"),
                    index=False,
                    encoding="utf-8-sig"
                )

                message = (
                    f"文件已导出到：\n{folder}\n\n"
                    "已生成：\n"
                    "1. synthetic_reconstructed_data.csv\n"
                    "2. descriptive_statistics.csv\n"
                    "3. anova_results.csv\n"
                    "4. fisher_lsd_results.csv\n\n"
                    "请在报告中注明：数据为 synthetic / reconstructed dataset，"
                    "仅用于统计复现、教学演示或方法验证。"
                )

                QMessageBox.information(self, "完成", message)

                try:
                    webbrowser.open(folder)
                except Exception:
                    pass

        except Exception as e:
            QMessageBox.warning(self, "出错", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SyntheticDataApp()
    window.show()
    sys.exit(app.exec())
