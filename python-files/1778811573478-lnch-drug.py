import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QTextEdit, QLineEdit, QGroupBox, QFormLayout,
                             QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logging.basicConfig(filename='上传日志.log', level=logging.INFO,
                    encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s')

class UploadThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, config, file_path):
        super().__init__()
        self.config = config
        self.file_path = file_path
        self.is_running = True

    def run(self):
        try:
            self.log_signal.emit("📥 正在读取Excel文件...")
            df = pd.read_excel(self.file_path)
            
            if '追溯码' not in df.columns:
                self.error_signal.emit("Excel缺少【追溯码】列！")
                return

            df = df.dropna(subset=['追溯码'])
            total = len(df)
            if total == 0:
                self.error_signal.emit("文件中无有效追溯码数据")
                return
            self.log_signal.emit(f"✅ 读取完成，共 {total} 条追溯码")

            success_list = []
            fail_list = []

            for index, row in df.iterrows():
                if not self.is_running:
                    self.log_signal.emit("⏹️  上传已手动停止")
                    break

                trace_code = str(row['追溯码']).strip()
                self.log_signal.emit(f"🔹 正在上传第 {index+1}/{total} 条：{trace_code}")

                payload = {
                    "entInfo": {
                        "entCode": self.config['ent_code'],
                        "entName": self.config['ent_name'],
                        "uploadTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "drugList": [{
                        "traceCode": trace_code,
                        "batchNo": row.get('批号', ''),
                        "expireDate": row.get('有效期', ''),
                        "prodDate": row.get('生产日期', '')
                    }]
                }

                try:
                    response = requests.post(
                        url=self.config['api_url'],
                        json=payload,
                        headers={"Content-Type": "application/json;charset=utf-8"},
                        timeout=10
                    )
                    res_data = response.json()

                    if res_data.get('code') == '00000':
                        success_list.append({"追溯码": trace_code, "状态": "上传成功", "响应": json.dumps(res_data, ensure_ascii=False)})
                        self.log_signal.emit(f"✅ 上传成功：{trace_code}")
                    else:
                        fail_list.append({"追溯码": trace_code, "状态": "上传失败", "响应": json.dumps(res_data, ensure_ascii=False)})
                        self.log_signal.emit(f"❌ 上传失败：{trace_code} | {res_data.get('msg', '未知错误')}")

                except Exception as e:
                    err_msg = str(e)
                    fail_list.append({"追溯码": trace_code, "状态": "请求异常", "响应": err_msg})
                    self.log_signal.emit(f"⚠️  请求失败：{trace_code} | {err_msg}")

                progress = int((index + 1) / total * 100)
                self.progress_signal.emit(progress)
                time.sleep(0.2)

            self.export_report(success_list, fail_list)
            self.log_signal.emit("🎉 所有任务执行完成！")
            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"程序异常：{str(e)}")

    def export_report(self, success, fail):
        try:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            with pd.ExcelWriter(f'上传结果_{now}.xlsx') as writer:
                if success:
                    pd.DataFrame(success).to_excel(writer, sheet_name='上传成功', index=False)
                if fail:
                    pd.DataFrame(fail).to_excel(writer, sheet_name='上传失败', index=False)
            self.log_signal.emit(f"📊 结果报表已保存：上传结果_{now}.xlsx")
        except Exception as e:
            self.log_signal.emit(f"导出报表失败：{str(e)}")

    def stop(self):
        self.is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("医保药品追溯码上传软件")
        self.setFixedSize(800, 600)
        self.upload_thread = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        config_group = QGroupBox("医保接口配置")
        form_layout = QFormLayout(config_group)
        self.api_url = QLineEdit("https://ybj.xxx.gov.cn/upload")
        self.ent_code = QLineEdit("")
        self.ent_name = QLineEdit("")
        form_layout.addRow("接口地址：", self.api_url)
        form_layout.addRow("商户编码：", self.ent_code)
        form_layout.addRow("商户名称：", self.ent_name)
        layout.addWidget(config_group)

        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_btn = QPushButton("选择Excel")
        self.file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_btn)
        layout.addLayout(file_layout)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始上传")
        self.stop_btn = QPushButton("停止上传")
        self.start_btn.clicked.connect(self.start_upload)
        self.stop_btn.clicked.connect(self.stop_upload)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        layout.addWidget(QLabel("进度："))
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("日志："))
        layout.addWidget(self.log_text)
        self.file_path = None

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(filter="Excel (*.xlsx)")
        if path:
            self.file_path = path
            self.file_label.setText(Path(path).name)

    def start_upload(self):
        if not self.file_path:
            QMessageBox.warning(self, "提示", "请选择文件")
            return
        config = {
            "api_url": self.api_url.text().strip(),
            "ent_code": self.ent_code.text().strip(),
            "ent_name": self.ent_name.text().strip()
        }
        if not all(config.values()):
            QMessageBox.warning(self, "提示", "请完善配置")
            return
        self.start_btn.setEnabled(False)
        self.upload_thread = UploadThread(config, self.file_path)
        self.upload_thread.log_signal.connect(self.log_text.append)
        self.upload_thread.progress_signal.connect(self.progress_bar.setValue)
        self.upload_thread.finished_signal.connect(lambda: self.start_btn.setEnabled(True))
        self.upload_thread.error_signal.connect(lambda m: QMessageBox.critical(self,"错误",m))
        self.upload_thread.start()

    def stop_upload(self):
        if self.upload_thread:
            self.upload_thread.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())