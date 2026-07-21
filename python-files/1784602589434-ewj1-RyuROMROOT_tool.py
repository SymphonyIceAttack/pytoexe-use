import subprocess
import hashlib
import os

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QTextEdit,
    QFileDialog,
)

ADB_PATH = r"C:\Users\shiaw\Downloads\platform-tools-latest-windows\platform-tools\adb.exe"
FASTBOOT_PATH = r"C:\Users\shiaw\Downloads\platform-tools-latest-windows\platform-tools\fastboot.exe"

app = QApplication([])

window = QWidget()
window.setWindowTitle("📱 RyuROM Tool")
window.resize(600, 900)

title = QLabel("📱 RyuROM Tool")
status = QLabel("🔌 接続状態: 未接続")
model_label = QLabel("📱 機種名: -")
manufacturer_label = QLabel("🏭 メーカー: -")
android_label = QLabel("🤖 Android: -")
rom_label = QLabel("📦 ROM: 未選択")

rom_path = ""

button = QPushButton("📱 接続確認")
fastboot_button = QPushButton("⚡ Fastboot再起動")
recovery_button = QPushButton("🛠 Recovery再起動")
apk_button = QPushButton("📦 APKインストール")
bootloader_button = QPushButton("🔓 Bootloader確認")
fastboot_info_button = QPushButton("🔍 Fastboot情報取得")
rom_button = QPushButton("📦 ROM選択")
rom_check_button = QPushButton("🔍 ROM情報確認")

log = QTextEdit()
log.setReadOnly(True)


def write_log(text):
    log.append(str(text))


def adb(cmd):
    result = subprocess.run(
        [ADB_PATH] + cmd,
        capture_output=True,
        text=True
    )

    if result.stdout:
        write_log(result.stdout)

    if result.stderr:
        write_log("ERROR: " + result.stderr)

    return result.stdout.strip()


def check_device():
    write_log("ADB接続確認中...")

    result = subprocess.run(
        [ADB_PATH, "devices"],
        capture_output=True,
        text=True
    )

    if "\tdevice" not in result.stdout:
        status.setText("🔌 接続状態: 未接続")
        QMessageBox.warning(window, "未接続", "Android端末が接続されていません")
        return

    status.setText("🔌 接続状態: 接続済み")
    write_log("接続成功")

    model = adb(["shell", "getprop", "ro.product.model"])
    manufacturer = adb(["shell", "getprop", "ro.product.manufacturer"])
    android = adb(["shell", "getprop", "ro.build.version.release"])

    model_label.setText(f"📱 機種名: {model}")
    manufacturer_label.setText(f"🏭 メーカー: {manufacturer}")
    android_label.setText(f"🤖 Android: {android}")


def fastboot():
    write_log("Fastbootへ移行")
    adb(["reboot", "bootloader"])


def recovery():
    write_log("Recoveryへ移行")
    adb(["reboot", "recovery"])


def install_apk():
    file, _ = QFileDialog.getOpenFileName(
        window,
        "APK選択",
        "",
        "APK Files (*.apk)"
    )

    if file:
        write_log("APKインストール開始")

        result = subprocess.run(
            [ADB_PATH, "install", file],
            capture_output=True,
            text=True
        )

        write_log(result.stdout)
        write_log(result.stderr)


def check_bootloader():
    write_log("Bootloader確認中...")

    result = subprocess.run(
        [FASTBOOT_PATH, "devices"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        write_log("Fastboot接続OK")
        write_log(result.stdout)
    else:
        write_log("Fastboot端末なし")


def fastboot_info():
    write_log("Fastboot情報取得")

    result = subprocess.run(
        [FASTBOOT_PATH, "getvar", "product"],
        capture_output=True,
        text=True
    )

    write_log(result.stdout)
    write_log(result.stderr)


def select_rom():
    global rom_path

    file, _ = QFileDialog.getOpenFileName(
        window,
        "ROM選択",
        "",
        "ROM Files (*.zip *.img)"
    )

    if file:
        rom_path = file
        rom_label.setText(f"📦 ROM: {file}")
        write_log("ROM選択:")
        write_log(file)


def check_rom():
    if rom_path == "":
        QMessageBox.warning(window, "未選択", "ROMが選択されていません")
        return

    size = os.path.getsize(rom_path)
    mb = size / 1024 / 1024

    write_log(f"容量: {mb:.2f}MB")

    sha = hashlib.sha256()

    with open(rom_path, "rb") as f:
        while True:
            data = f.read(1024 * 1024)

            if not data:
                break

            sha.update(data)

    write_log("SHA256:")
    write_log(sha.hexdigest())

    QMessageBox.information(window, "完了", "ROM情報取得完了")


button.clicked.connect(check_device)
fastboot_button.clicked.connect(fastboot)
recovery_button.clicked.connect(recovery)
apk_button.clicked.connect(install_apk)
bootloader_button.clicked.connect(check_bootloader)
fastboot_info_button.clicked.connect(fastboot_info)
rom_button.clicked.connect(select_rom)
rom_check_button.clicked.connect(check_rom)

layout = QVBoxLayout()

layout.addWidget(title)
layout.addWidget(status)
layout.addWidget(model_label)
layout.addWidget(manufacturer_label)
layout.addWidget(android_label)

layout.addWidget(button)
layout.addWidget(fastboot_button)
layout.addWidget(recovery_button)
layout.addWidget(apk_button)
layout.addWidget(bootloader_button)
layout.addWidget(fastboot_info_button)

layout.addWidget(rom_button)
layout.addWidget(rom_label)
layout.addWidget(rom_check_button)

layout.addWidget(QLabel("📜 ログ"))
layout.addWidget(log)

window.setLayout(layout)
window.show()

app.exec()