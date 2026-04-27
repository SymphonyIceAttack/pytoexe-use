import sys
import serial
import serial.tools.list_ports
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal

def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')

class SerialReadThread(QThread):
    received = pyqtSignal(bytes)
    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True
    def run(self):
        while self.running and self.ser.is_open:
            try:
                buf = self.ser.read(128)
                if buf:
                    self.received.emit(buf)
            except:
                break
    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.thread = None
        self.setWindowTitle("众惠智能 - 步进电机控制器")
        self.setGeometry(100, 100, 700, 650)
        self.init_ui()

    def init_ui(self):
        w = QWidget()
        self.setCentralWidget(w)
        lay = QVBoxLayout(w)

        g1 = QGroupBox("串口设置")
        l1 = QHBoxLayout()
        self.cb_com = QComboBox()
        self.cb_baud = QComboBox()
        self.cb_baud.addItems(["9600","19200","38400","115200"])
        self.cb_baud.setCurrentText("9600")
        self.btn_ref = QPushButton("刷新")
        self.btn_conn = QPushButton("连接")
        self.btn_ref.clicked.connect(self.refresh)
        self.btn_conn.clicked.connect(self.conn)
        l1.addWidget(QLabel("COM"))
        l1.addWidget(self.cb_com)
        l1.addWidget(QLabel("波特率"))
        l1.addWidget(self.cb_baud)
        l1.addWidget(self.btn_ref)
        l1.addWidget(self.btn_conn)
        g1.setLayout(l1)
        lay.addWidget(g1)
        self.refresh()

        g2 = QGroupBox("参数设置")
        l2 = QFormLayout()
        self.addr = QLineEdit("1")
        self.speed = QLineEdit("60")
        self.acc = QLineEdit("100")
        self.dec = QLineEdit("100")
        self.start_spd = QLineEdit("10")
        self.pulse = QLineEdit("1000")
        l2.addRow("从机地址", self.addr)
        l2.addRow("最大速度(r/min)", self.speed)
        l2.addRow("加速时间(ms)", self.acc)
        l2.addRow("减速时间(ms)", self.dec)
        l2.addRow("起始速度", self.start_spd)
        l2.addRow("总脉冲数", self.pulse)
        g2.setLayout(l2)
        lay.addWidget(g2)

        g3 = QGroupBox("运动控制")
        l3 = QGridLayout()
        self.btn_write_all = QPushButton("写入全部参数")
        self.btn_fwd = QPushButton("正转(速度模式)")
        self.btn_rev = QPushButton("反转(速度模式)")
        self.btn_pos_fwd = QPushButton("位置模式正转")
        self.btn_pos_rev = QPushButton("位置模式反转")
        self.btn_stop = QPushButton("正常停止")
        self.btn_emg = QPushButton("急停")
        self.btn_home = QPushButton("回原点")
        self.btn_read_spd = QPushButton("读最大速度")
        self.btn_read_pos = QPushButton("读位置参数")

        self.btn_write_all.clicked.connect(self.write_all)
        self.btn_fwd.clicked.connect(lambda: self.run_speed(1))
        self.btn_rev.clicked.connect(lambda: self.run_speed(-1))
        self.btn_pos_fwd.clicked.connect(lambda: self.run_pos(1))
        self.btn_pos_rev.clicked.connect(lambda: self.run_pos(-1))
        self.btn_stop.clicked.connect(self.stop)
        self.btn_emg.clicked.connect(self.emg)
        self.btn_home.clicked.connect(self.home)
        self.btn_read_spd.clicked.connect(self.read_speed)
        self.btn_read_pos.clicked.connect(self.read_pos)

        l3.addWidget(self.btn_write_all,0,0,1,2)
        l3.addWidget(self.btn_fwd,1,0)
        l3.addWidget(self.btn_rev,1,1)
        l3.addWidget(self.btn_pos_fwd,2,0)
        l3.addWidget(self.btn_pos_rev,2,1)
        l3.addWidget(self.btn_stop,3,0)
        l3.addWidget(self.btn_emg,3,1)
        l3.addWidget(self.btn_home,4,0)
        l3.addWidget(self.btn_read_spd,4,1)
        l3.addWidget(self.btn_read_pos,5,0,1,2)
        g3.setLayout(l3)
        lay.addWidget(g3)

        g4 = QGroupBox("通讯日志")
        l4 = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        l4.addWidget(self.log)
        g4.setLayout(l4)
        lay.addWidget(g4)

    def log_print(self, s):
        t = time.strftime("%H:%M:%S")
        self.log.append(f"[{t}] {s}")

    def refresh(self):
        self.cb_com.clear()
        for p in serial.tools.list_ports.comports():
            self.cb_com.addItem(p.device)

    def conn(self):
        if self.ser and self.ser.is_open:
            self.thread.stop()
            self.thread.wait()
            self.ser.close()
            self.ser = None
            self.btn_conn.setText("连接")
            self.log_print("断开连接")
            return
        try:
            port = self.cb_com.currentText()
            baud = int(self.cb_baud.currentText())
            self.ser = serial.Serial(port, baud, timeout=0.5)
            self.thread = SerialReadThread(self.ser)
            self.thread.received.connect(self.on_recv)
            self.thread.start()
            self.btn_conn.setText("断开")
            self.log_print("连接成功")
        except Exception as e:
            QMessageBox.critical(self,"错误",str(e))

    def on_recv(self, b):
        self.log_print(f"接收: {b.hex().upper()}")

    def send(self, cmd):
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self,"提示","未连接串口")
            return
        self.ser.write(cmd)
        self.log_print(f"发送: {cmd.hex().upper()}")

    def write_all(self):
        a = int(self.addr.text())
        spd = int(self.speed.text())
        acc = int(self.acc.text())
        dec = int(self.dec.text())
        st = int(self.start_spd.text())
        self.send(bytes([a,6,0,0x20])+st.to_bytes(2,'big')+crc16(bytes([a,6,0,0x20])+st.to_bytes(2,'big')))
        time.sleep(0.1)
        self.send(bytes([a,6,0,0x21])+acc.to_bytes(2,'big')+crc16(bytes([a,6,0,0x21])+acc.to_bytes(2,'big')))
        time.sleep(0.1)
        self.send(bytes([a,6,0,0x22])+dec.to_bytes(2,'big')+crc16(bytes([a,6,0,0x22])+dec.to_bytes(2,'big')))
        time.sleep(0.1)
        self.send(bytes([a,6,0,0x23])+spd.to_bytes(2,'big')+crc16(bytes([a,6,0,0x23])+spd.to_bytes(2,'big')))

    def run_speed(self, d):
        a = int(self.addr.text())
        v = int(self.speed.text()) * d
        self.send(bytes([a,6,0,0x23])+v.to_bytes(2,'big',signed=True)+crc16(bytes([a,6,0,0x23])+v.to_bytes(2,'big',signed=True)))
        time.sleep(0.1)
        self.send(bytes([a,6,0,0x27,0,2])+crc16(bytes([a,6,0,0x27,0,2])))

    def run_pos(self, d):
        a = int(self.addr.text())
        p = int(self.pulse.text()) * d
        self.send(bytes([a,6,0,0x25])+p.to_bytes(2,'big',signed=True)+crc16(bytes([a,6,0,0x25])+p.to_bytes(2,'big',signed=True)))
        time.sleep(0.1)
        self.send(bytes([a,6,0,0x27,0,1])+crc16(bytes([a,6,0,0x27,0,1])))

    def stop(self):
        a = int(self.addr.text())
        self.send(bytes([a,6,0,0x28,0,0])+crc16(bytes([a,6,0,0x28,0,0])))

    def emg(self):
        a = int(self.addr.text())
        self.send(bytes([a,6,0,0x28,0,1])+crc16(bytes([a,6,0,0x28,0,1])))

    def home(self):
        a = int(self.addr.text())
        self.send(bytes([a,6,0,0x30,0,1])+crc16(bytes([a,6,0,0x30,0,1])))

    def read_speed(self):
        a = int(self.addr.text())
        self.send(bytes([a,3,0,0x23,0,1])+crc16(bytes([a,3,0,0x23,0,1])))

    def read_pos(self):
        a = int(self.addr.text())
        self.send(bytes([a,3,0,0x20,0,4])+crc16(bytes([a,3,0,0x20,0,4])))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
