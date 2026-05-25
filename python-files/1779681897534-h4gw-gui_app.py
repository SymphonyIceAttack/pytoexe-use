import platform
import plistlib
import traceback
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QLocale
import qdarktheme
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux

import resources_rc
from Sparserestore.restore import restore_files, FileToRestore
from devicemanagement.constants import Device

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.device = None

        locale = QLocale.system().name()
        self.language = "zh" if locale.startswith("zh") else "en"

        if self.language == "zh":
            self.verify_user_agreement()

        self.thermalmonitord = False
        self.disable_ota = False
        self.disable_usage_tracking_agent = False
        self.skip_setup = True

        self.language_pack = {
            "en": {
                "title": "thermalmonitordDisabler",
                "modified_by": "Modified by rponeawa from LeminLimez's Nugget.\nFree tool. If you purchased it, please report the seller.\n（免费工具，若您是购买而来，请举报卖家。）",
                "backup_warning": "Please back up your device before using!",
                "connect_prompt": "Please connect your device and try again!",
                "connected": "Connected to",
                "ios_version": "iOS",
                "apply_changes": "Applying changes to disabled.plist...",
                "applying_changes": "Applying changes...",
                "success": "Changes applied successfully!",
                "error": "An error occurred while applying changes to disabled.plist:",
                "error_connecting": "Error connecting to device",
                "goodbye": "Goodbye!",
                "input_prompt": "Enter a number: ",
                "menu_options": [
                    "Disable thermalmonitord",
                    "Disable OTA",
                    "Disable UsageTrackingAgent",
                    "Apply changes",
                    "Refresh",
                    "Skip Setup"
                ],
                "skip_setup_description": "Uncheck to prevent MDM configuration profiles from being removed. If you do not know what this option does, please keep it checked."
            },
            "zh": {
                "title": "温控禁用工具",
                "modified_by": "由 rponeawa 基于 LeminLimez 的 Nugget 修改。\n免费工具，若您是购买而来，请举报卖家。",
                "backup_warning": "使用前请备份您的设备！",
                "connect_prompt": "请连接设备并重试！",
                "connected": "已连接到",
                "ios_version": "iOS",
                "apply_changes": "正在应用更改到 disabled.plist...",
                "applying_changes": "正在应用修改...",
                "success": "更改已成功应用！",
                "error": "应用更改时发生错误：",
                "error_connecting": "连接设备时发生错误",
                "goodbye": "再见！",
                "input_prompt": "请输入选项: ",
                "menu_options": [
                    "禁用温控",
                    "禁用系统更新",
                    "禁用使用情况日志",
                    "应用更改",
                    "刷新",
                    "跳过向导"
                ],
                "skip_setup_description": "取消勾选以防止 MDM 配置文件被移除。若你不知道该选项的作用，请保持其被勾选。"
            }
        }

        self.init_ui()
        self.get_device_info()

    def verify_user_agreement(self):
        required_text = "我未为本工具或相关代操作服务付费，也未通过营销号和视频等途径获知，或从非官方渠道如限速网盘下载本工具"
        user_input, ok = QtWidgets.QInputDialog.getText(
            self,
            "验证声明",
            "请准确输入以下内容以继续使用本工具：\n\n" + required_text,
            QtWidgets.QLineEdit.Normal
        )
        if not ok or user_input != required_text:
            QtWidgets.QMessageBox.critical(
                self, "验证失败", "输入内容不匹配，程序将退出。"
            )
            sys.exit()

    def set_font(self):
        if platform.system() == "Windows":
            font = QtGui.QFont("Microsoft YaHei")
            QtWidgets.QApplication.setFont(font)

    def init_ui(self):
        self.setWindowTitle(self.language_pack[self.language]["title"])

        self.set_font()
        
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(10)

        self.modified_by_label = QtWidgets.QLabel(self.language_pack[self.language]["modified_by"])
        self.layout.addWidget(self.modified_by_label)

        self.icon_layout = QtWidgets.QHBoxLayout()
        self.icon_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.icon_layout.setSpacing(10)

        self.github_icon = QSvgWidget(":/brand-github.svg")
        self.github_icon.setFixedSize(24, 24)
        self.github_icon.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.github_icon.mouseReleaseEvent = lambda event: self.open_link("https://github.com/rponeawa/thermalmonitordDisabler")

        self.bilibili_icon = QSvgWidget(":/brand-bilibili.svg")
        self.bilibili_icon.setFixedSize(24, 24)
        self.bilibili_icon.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.bilibili_icon.mouseReleaseEvent = lambda event: self.open_link("https://space.bilibili.com/332095459")

        self.icon_layout.addWidget(self.github_icon)
        self.icon_layout.addWidget(self.bilibili_icon)

        self.layout.addLayout(self.icon_layout)

        self.device_info = QtWidgets.QLabel(self.language_pack[self.language]["backup_warning"])
        self.layout.addWidget(self.device_info)

        self.thermalmonitord_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][0])
        self.thermalmonitord_checkbox.setChecked(self.thermalmonitord)
        self.layout.addWidget(self.thermalmonitord_checkbox)

        self.disable_ota_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][1])
        self.disable_ota_checkbox.setChecked(self.disable_ota)
        self.layout.addWidget(self.disable_ota_checkbox)

        self.disable_usage_tracking_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][2])
        self.disable_usage_tracking_checkbox.setChecked(self.disable_usage_tracking_agent)
        self.layout.addWidget(self.disable_usage_tracking_checkbox)

        self.skip_setup_layout = QtWidgets.QVBoxLayout()
        self.skip_setup_layout.setSpacing(2)

        self.skip_setup_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][5])
        self.skip_setup_checkbox.setChecked(self.skip_setup)
        self.skip_setup_checkbox.stateChanged.connect(self.toggle_skip_setup)
        self.skip_setup_layout.addWidget(self.skip_setup_checkbox)

        self.skip_setup_description_label = QtWidgets.QLabel(self.language_pack[self.language]["skip_setup_description"])
        self.skip_setup_description_label.setWordWrap(True)

        font = self.skip_setup_description_label.font()
        font.setPointSize(10)
        self.skip_setup_description_label.setFont(font)
        self.skip_setup_description_label.setStyleSheet("color: gray;")
        self.skip_setup_layout.addWidget(self.skip_setup_description_label)

        self.layout.addLayout(self.skip_setup_layout)

        self.apply_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][3])
        self.apply_button.clicked.connect(self.apply_changes)
        self.layout.addWidget(self.apply_button)

        self.refresh_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][4])
        self.refresh_button.clicked.connect(self.get_device_info)
        self.layout.addWidget(self.refresh_button)

        self.setLayout(self.layout)
        self.show()

    def toggle_skip_setup(self, state):
        self.skip_setup = state == QtCore.Qt.Checked

    def open_link(self, url):
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        except Exception as e:
            print(f"Error opening link {url}: {str(e)}")

    def get_device_info(self):
        connected_devices = usbmux.list_devices()

        if not connected_devices:
            self.device = None
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            self.disable_controls(True)
            return
        
        for current_device in connected_devices:
            if current_device.is_usb:
                try:
                    ld = create_using_usbmux(serial=current_device.serial)
                    vals = ld.all_values
                    print(vals)
                    self.device = Device(
                        uuid=current_device.serial,
                        name=vals['DeviceName'],
                        version=vals['ProductVersion'],
                        build=vals['BuildVersion'],
                        model=vals['ProductType'],
                        locale=ld.locale,
                        ld=ld
                    )
                    self.update_device_info()
                    self.disable_controls(False)
                    return
                except Exception as e:
                    self.device_info.setText(self.language_pack[self.language]["error_connecting"] + str(e))
                    print(traceback.format_exc())
                    return

        self.device = None
        self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
        self.disable_controls(True)

    def disable_controls(self, disable):
        self.thermalmonitord_checkbox.setEnabled(not disable)
        self.disable_ota_checkbox.setEnabled(not disable)
        self.disable_usage_tracking_checkbox.setEnabled(not disable)
        self.skip_setup_checkbox.setEnabled(not disable)
        self.apply_button.setEnabled(not disable)

    def update_device_info(self):
        if self.device:
            self.device_info.setText(f"{self.language_pack[self.language]['connected']} {self.device.name}\n{self.language_pack[self.language]['ios_version']} {self.device.version}")
        else:
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            self.disable_controls(True)

    def modify_disabled_plist(self):
        default_disabled_plist = {
            "com.apple.magicswitchd.companion": True,
            "com.apple.security.otpaird": True,
            "com.apple.dhcp6d": True,
            "com.apple.bootpd": True,
            "com.apple.ftp-proxy-embedded": False,
            "com.apple.relevanced": True
        }

        plist = default_disabled_plist.copy()

        if self.thermalmonitord_checkbox.isChecked():
            plist["com.apple.thermalmonitord"] = True
        else:
            plist.pop("com.apple.thermalmonitord", None)

        if self.disable_ota_checkbox.isChecked():
            plist["com.apple.mobile.softwareupdated"] = True
            plist["com.apple.OTATaskingAgent"] = True
            plist["com.apple.softwareupdateservicesd"] = True
        else:
            plist.pop("com.apple.mobile.softwareupdated", None)
            plist.pop("com.apple.OTATaskingAgent", None)
            plist.pop("com.apple.softwareupdateservicesd", None)

        if self.disable_usage_tracking_checkbox.isChecked():
            plist["com.apple.UsageTrackingAgent"] = True
        else:
            plist.pop("com.apple.UsageTrackingAgent", None)

        return plistlib.dumps(plist, fmt=plistlib.FMT_XML)

    def apply_changes(self):
        self.apply_button.setText(self.language_pack[self.language]["applying_changes"])
        self.apply_button.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        QtCore.QTimer.singleShot(100, self._execute_changes)

    def add_skip_setup(self, files_to_restore):
        if self.skip_setup:
            cloud_config_plist: dict = {
                "SkipSetup": ["WiFi", "Location", "Restore", "SIMSetup", "Android", "AppleID", "IntendedUser", "TOS", "Siri", "ScreenTime", "Diagnostics", "SoftwareUpdate", "Passcode", "Biometric", "Payment", "Zoom", "DisplayTone", "MessagingActivationUsingPhoneNumber", "HomeButtonSensitivity", "CloudStorage", "ScreenSaver", "TapToSetup", "Keyboard", "PreferredLanguage", "SpokenLanguage", "WatchMigration", "OnBoarding", "TVProviderSignIn", "TVHomeScreenSync", "Privacy", "TVRoom", "iMessageAndFaceTime", "AppStore", "Safety", "Multitasking", "ActionButton", "TermsOfAddress", "AccessibilityAppearance", "Welcome", "Appearance", "RestoreCompleted", "UpdateCompleted"],
                "AllowPairing": True,
                "ConfigurationWasApplied": True,
                "CloudConfigurationUIComplete": True,
                "ConfigurationSource": 0,
                "PostSetupProfileWasInstalled": True,
                "IsSupervised": False,
            }
            files_to_restore.append(FileToRestore(
                contents=plistlib.dumps(cloud_config_plist),
                restore_path="systemgroup.com.apple.configurationprofiles/Library/ConfigurationProfiles/CloudConfigurationDetails.plist",
                domain="SysSharedContainerDomain-."
            ))
            purplebuddy_plist = {
                "SetupDone": True,
                "SetupFinishedAllSteps": True,
                "UserChoseLanguage": True
            }
            files_to_restore.append(FileToRestore(
                contents=plistlib.dumps(purplebuddy_plist),
                restore_path="mobile/com.apple.purplebuddy.plist",
                domain="ManagedPreferencesDomain"
            ))

    def _execute_changes(self):
        try:
            files_to_restore = []
            print("\n" + self.language_pack[self.language]["apply_changes"])
            plist_data = self.modify_disabled_plist()

            files_to_restore.append(FileToRestore(
                contents=plist_data,
                restore_path="com.apple.xpc.launchd/disabled.plist",
                domain="DatabaseDomain",
                owner=0,
                group=0
            ))

            self.add_skip_setup(files_to_restore)

            print(files_to_restore)
            
            restore_files(files=files_to_restore, reboot=True, lockdown_client=self.device.ld)

            QtWidgets.QMessageBox.information(self, "Success", self.language_pack[self.language]["success"])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", self.language_pack[self.language]["error"] + str(e))
            print(traceback.format_exc())
        finally:
            self.apply_button.setText(self.language_pack[self.language]["menu_options"][3])
            self.apply_button.setEnabled(True)

if __name__ == "__main__":
    qdarktheme.enable_hi_dpi()
    app = QtWidgets.QApplication(sys.argv)
    qdarktheme.setup_theme()

    gui = App()
    sys.exit(app.exec_())