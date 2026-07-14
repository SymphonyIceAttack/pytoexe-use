import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime

TARGET_DRIVE = "Z:"
TARGET_ROOT = os.path.join(TARGET_DRIVE, "Windows")

WINDOWS_7_FOLDERS = [
    "System32", "System32\config", "System32\drivers", "System32\spool",
    "System32\spool\drivers", "System32\spool\PRINTERS", "System32\winevt",
    "System32\winevt\Logs", "System32\wbem", "System32\migration",
    "System32\en-US", "System32\ru-RU", "System32\zh-CN",
    "System32\CodeIntegrity", "System32\com", "System32\Dism",
    "System32\DriverStore", "System32\DriverStore\FileRepository",
    "System32\drivers\en-US", "System32\drivers\ru-RU",
    "System32\drivers\umdf", "System32\drivers\kmdf",
    "System", "System\en-US", "System\ru-RU",
    "SysWOW64", "SysWOW64\config", "SysWOW64\drivers",
    "SysWOW64\en-US", "SysWOW64\ru-RU", "SysWOW64\wbem",
    "SysWOW64\migration", "SysWOW64\spool",
    "SysWOW64\DriverStore", "SysWOW64\DriverStore\FileRepository",
    "Program Files", "Program Files\Common Files",
    "Program Files\Common Files\Microsoft Shared",
    "Program Files\Internet Explorer", "Program Files\Windows Media Player",
    "Program Files\Windows NT", "Program Files\Windows NT\Accessories",
    "Program Files\Movie Maker", "Program Files\Windows Sidebar",
    "Program Files\Windows Sidebar\Gadgets",
    "Program Files\Windows Defender",
    "Program Files (x86)", "Program Files (x86)\Common Files",
    "Program Files (x86)\Internet Explorer",
    "Program Files (x86)\Windows Media Player",
    "Program Files (x86)\Windows NT",
    "Program Files (x86)\Movie Maker",
    "Program Files (x86)\Windows Sidebar",
    "Users", "Users\Default", "Users\Default\Desktop",
    "Users\Default\Documents", "Users\Default\Downloads",
    "Users\Default\Music", "Users\Default\Pictures",
    "Users\Default\Videos", "Users\Default\Favorites",
    "Users\Default\AppData", "Users\Default\AppData\Local",
    "Users\Default\AppData\Roaming", "Users\Default\AppData\LocalLow",
    "Users\Default\AppData\Local\Temp",
    "Users\Default\AppData\Roaming\Microsoft",
    "Users\Public", "Users\Public\Desktop", "Users\Public\Documents",
    "Users\Public\Downloads", "Users\Public\Music", "Users\Public\Pictures",
    "Users\Public\Videos", "Users\Public\Favorites",
    "Fonts", "Help", "Help\mui", "Help\Windows", "Help\Windows\en-US",
    "Media", "Media\Sounds", "Media\Sounds\Windows",
    "Resources", "Resources\Themes", "Resources\Themes\Aero",
    "Resources\Themes\Aero\en-US", "Resources\Themes\Aero\ru-RU",
    "Resources\Themes\Classic", "Resources\Themes\Classic\en-US",
    "Resources\Themes\Classic\ru-RU",
    "Resources\Themes\en-US", "Resources\Themes\ru-RU",
    "Microsoft.NET", "Microsoft.NET\Framework",
    "Microsoft.NET\Framework\v2.0.50727",
    "Microsoft.NET\Framework\v3.5", "Microsoft.NET\Framework\v4.0.30319",
    "Microsoft.NET\Framework64", "Microsoft.NET\Framework64\v2.0.50727",
    "Microsoft.NET\Framework64\v3.5", "Microsoft.NET\Framework64\v4.0.30319",
    "Installer", "Installer\$PatchCache$",
    "Installer\MSI", "Installer\MSI\en-US",
    "winsxs", "winsxs\Manifests", "winsxs\Backup",
    "winsxs\Catalogs", "winsxs\Temp",
    "servicing", "servicing\Packages", "servicing\Sessions",
    "servicing\Cbs", "servicing\Cbs\Temp",
    "ADAM", "ADAM\ADAM", "ADAM\ADAM\en-US",
    "AppCompat", "AppCompat\Programs", "AppCompat\Programs\Install",
    "Bits", "Bits\Backup", "CSC", "CSC\v2.0.6",
    "CSC\v2.0.6\namespace", "CSC\v2.0.6\schema",
    "Cursors", "Debug", "Debug\WPD", "Debug\UserMode",
    "diagnostics", "diagnostics\system", "diagnostics\system\AERO",
    "diagnostics\system\Audio", "diagnostics\system\Display",
    "diagnostics\system\Networking", "diagnostics\system\Performance",
    "Downloaded Program Files",
    "ehome", "Globalization", "Globalization\Sorting",
    "IdentityCRL", "IdentityCRL\CRL",
    "ImmersiveControlPanel", "ImmersiveControlPanel\en-US",
    "LiveKernelReports", "LiveKernelReports\Watchdog",
    "MediaViewer", "MediaViewer\en-US",
    "MUI", "MUI\Fallback",
    "PolicyDefinitions", "PolicyDefinitions\en-US",
    "PolicyDefinitions\ru-RU", "ServiceProfiles",
    "ServiceProfiles\LocalService", "ServiceProfiles\NetworkService",
    "ServiceState", "ServiceState\EventLog",
    "system", "system\en-US", "system\ru-RU",
    "TAPI", "Tasks", "Tasks\Microsoft",
    "Tasks\Microsoft\Windows", "Tasks\Microsoft\Windows\Application Experience",
    "Tasks\Microsoft\Windows\Customer Experience Improvement Program",
    "Tasks\Microsoft\Windows\DiskDiagnostic",
    "Tasks\Microsoft\Windows\MobilePC",
    "Tasks\Microsoft\Windows\Registry",
    "Tasks\Microsoft\Windows\SystemRestore",
    "Tasks\Microsoft\Windows\Windows Update",
    "Tasks\Microsoft\Windows\Windows Media Center",
    "Temp", "Temp\Install", "temp",
    "tracing", "tracing\en-US", "tracing\ru-RU",
    "Web", "Web\Wallpaper", "Web\Wallpaper\Windows",
    "Web\Screen", "Web\Screen\en-US",
    "WindowsUpdate", "WindowsUpdate\en-US",
    "WinStore", "WinStore\en-US",
    "Write", "Write\en-US",
    "assembly", "assembly\GAC", "assembly\GAC_32", "assembly\GAC_64",
    "assembly\GAC_MSIL", "assembly\NativeImages_v2.0.50727_32",
    "assembly\NativeImages_v2.0.50727_64",
    "assembly\NativeImages_v4.0.30319_32",
    "assembly\NativeImages_v4.0.30319_64",
    "assembly\temp",
    "Branding", "Branding\BaseBrd", "Branding\BaseBrd\en-US",
    "Branding\BaseBrd\ru-RU", "Branding\ShellBrd",
    "Branding\ShellBrd\en-US", "Branding\ShellBrd\ru-RU",
]

def get_files_for_folder(folder):
    files = []
    
    if folder == "" or folder == "Windows":
        files.extend([
            ("explorer.exe", 2846720),
            ("winlogon.exe", 400896),
            ("csrss.exe", 9216),
            ("smss.exe", 70144),
            ("services.exe", 356352),
            ("lsass.exe", 35840),
            ("svchost.exe", 26112),
            ("taskhost.exe", 50944),
            ("regedit.exe", 398848),
            ("notepad.exe", 184320),
            ("calc.exe", 183296),
            ("mspaint.exe", 697856),
            ("snippingtool.exe", 229376),
            ("StikyNot.exe", 425984),
            ("write.exe", 276480),
            ("cmd.exe", 311296),
            ("control.exe", 132096),
            ("msconfig.exe", 240640),
            ("taskmgr.exe", 379392),
            ("winhelp.exe", 13312),
            ("winhlp32.exe", 26624),
            ("notepad.exe", 184320),
            ("regedt32.exe", 13312),
            ("system.ini", 219),
            ("win.ini", 92),
            ("boot.ini", 30),
            ("desktop.ini", 49),
        ])
    
    elif folder == "System32":
        files.extend([
            ("ntdll.dll", 1778688),
            ("kernel32.dll", 1167360),
            ("user32.dll", 838144),
            ("gdi32.dll", 320512),
            ("advapi32.dll", 873472),
            ("shell32.dll", 12887040),
            ("ole32.dll", 1419264),
            ("oleaut32.dll", 882688),
            ("comctl32.dll", 1680896),
            ("msvcrt.dll", 694272),
            ("ws2_32.dll", 215552),
            ("shlwapi.dll", 451584),
            ("winmm.dll", 195584),
            ("version.dll", 29696),
            ("secur32.dll", 72960),
            ("netapi32.dll", 574464),
            ("userenv.dll", 113664),
            ("iphlpapi.dll", 120320),
            ("winsock.dll", 23040),
            ("wsock32.dll", 19456),
            ("dnsapi.dll", 273920),
            ("dhcpcsvc.dll", 70144),
            ("dhcpcsvc6.dll", 45056),
            ("winrnr.dll", 23040),
            ("wshnetbs.dll", 10752),
            ("wship6.dll", 10752),
            ("cmd.exe", 311296),
            ("attrib.exe", 18944),
            ("chkdsk.exe", 154624),
            ("chkntfs.exe", 31232),
            ("compact.exe", 41984),
            ("convert.exe", 70144),
            ("diskpart.exe", 70656),
            ("diskperf.exe", 37376),
            ("driverquery.exe", 24576),
            ("fc.exe", 38912),
            ("find.exe", 15872),
            ("findstr.exe", 32256),
            ("format.com", 31232),
            ("fsutil.exe", 41472),
            ("help.exe", 28160),
            ("icacls.exe", 41472),
            ("ipconfig.exe", 80384),
            ("logoff.exe", 9728),
            ("mode.com", 24064),
            ("more.com", 26624),
            ("net.exe", 124416),
            ("net1.exe", 144384),
            ("netsh.exe", 395776),
            ("netstat.exe", 40448),
            ("nslookup.exe", 220160),
            ("pathping.exe", 60416),
            ("ping.exe", 50176),
            ("powercfg.exe", 93440),
            ("qprocess.exe", 18944),
            ("reg.exe", 58880),
            ("regedt32.exe", 13312),
            ("regsvr32.exe", 20992),
            ("replace.exe", 21504),
            ("route.exe", 27648),
            ("runas.exe", 23552),
            ("sc.exe", 102400),
            ("schtasks.exe", 215040),
            ("sfc.exe", 17408),
            ("shutdown.exe", 33280),
            ("sort.exe", 31232),
            ("subst.exe", 19456),
            ("systeminfo.exe", 46080),
            ("taskkill.exe", 37888),
            ("tasklist.exe", 77312),
            ("timeout.exe", 11264),
            ("tracert.exe", 34816),
            ("tree.com", 13312),
            ("tzutil.exe", 28160),
            ("verifier.exe", 198656),
            ("where.exe", 21504),
            ("whoami.exe", 23552),
            ("wmic.exe", 218112),
            ("xcopy.exe", 50688),
        ])
    
    elif folder.startswith("System32\drivers"):
        files.extend([
            ("ntfs.sys", 1656192),
            ("ntfs.sys", 1656192),
            ("ntoskrnl.exe", 5532544),
            ("hal.dll", 309248),
            ("kdcom.dll", 25600),
            ("pshed.dll", 16896),
            ("bootvid.dll", 29696),
            ("ci.dll", 384512),
            ("clfs.sys", 270336),
            ("pci.sys", 177664),
            ("acpi.sys", 368128),
            ("isapnp.sys", 53248),
            ("mountmgr.sys", 93184),
            ("fvevol.sys", 311808),
            ("volmgr.sys", 60416),
            ("volmgrx.sys", 349184),
            ("volsnap.sys", 305664),
            ("vdrvroot.sys", 39936),
            ("disk.sys", 46592),
            ("partmgr.sys", 74240),
            ("classpnp.sys", 176128),
            ("atapi.sys", 22016),
            ("ataport.sys", 155136),
            ("msahci.sys", 31232),
            ("pciide.sys", 14848),
            ("pciidex.sys", 50688),
            ("usbuhci.sys", 29184),
            ("usbehci.sys", 53760),
            ("usbhub.sys", 275968),
            ("usbport.sys", 286720),
            ("usbccgp.sys", 78848),
            ("usbstor.sys", 76288),
            ("hidusb.sys", 28160),
            ("kbdclass.sys", 44544),
            ("kbdhid.sys", 26112),
            ("mouclass.sys", 43520),
            ("mouhid.sys", 24576),
        ])
    
    elif folder == "Fonts":
        files.extend([
            ("arial.ttf", 733604),
            ("arialbd.ttf", 732188),
            ("arialbi.ttf", 730792),
            ("ariali.ttf", 730880),
            ("calibri.ttf", 901628),
            ("calibrib.ttf", 902100),
            ("calibrii.ttf", 902292),
            ("calibriz.ttf", 902012),
            ("cambria.ttf", 1002560),
            ("cambriab.ttf", 1002240),
            ("cambriai.ttf", 1002240),
            ("cambriaz.ttf", 1002240),
            ("candara.ttf", 964916),
            ("candarab.ttf", 964840),
            ("candarai.ttf", 964820),
            ("candaraz.ttf", 964816),
            ("comic.ttf", 221508),
            ("comicbd.ttf", 218680),
            ("consola.ttf", 231812),
            ("consolab.ttf", 231260),
            ("consolai.ttf", 231752),
            ("consolaz.ttf", 231048),
            ("constantia.ttf", 820368),
            ("constantinab.ttf", 820724),
            ("constantinaz.ttf", 820592),
            ("corbel.ttf", 818420),
            ("corbelb.ttf", 819680),
            ("corbeli.ttf", 819836),
            ("corbelz.ttf", 819920),
            ("cour.ttf", 253812),
            ("courbd.ttf", 252960),
            ("courbi.ttf", 253080),
            ("couri.ttf", 253640),
            ("georgia.ttf", 253812),
            ("georgiab.ttf", 252960),
            ("georgiai.ttf", 253080),
            ("georgiaz.ttf", 253640),
            ("impact.ttf", 221508),
            ("lucon.ttf", 218680),
            ("l_10646.ttf", 174548),
            ("msyh.ttf", 933268),
            ("msyhbd.ttf", 932932),
            ("segoeui.ttf", 903400),
            ("segoeuib.ttf", 903332),
            ("segoeuii.ttf", 903276),
            ("segoeuiz.ttf", 903264),
            ("simsun.ttc", 5072788),
            ("tahoma.ttf", 437916),
            ("tahomabd.ttf", 437820),
            ("times.ttf", 253812),
            ("timesbd.ttf", 252960),
            ("timesbi.ttf", 253080),
            ("timesi.ttf", 253640),
            ("trebuc.ttf", 253812),
            ("trebucbd.ttf", 252960),
            ("trebucbi.ttf", 253080),
            ("trebucit.ttf", 253640),
            ("verdana.ttf", 253812),
            ("verdanab.ttf", 252960),
            ("verdanai.ttf", 253080),
            ("verdanaz.ttf", 253640),
            ("webdings.ttf", 221508),
            ("wingding.ttf", 218680),
        ])
    
    elif folder.startswith("Resources\Themes"):
        files.extend([
            ("aero.theme", 2767),
            ("classic.theme", 564),
            ("desktop.ini", 49),
            ("themeui.dll", 204288),
        ])
    
    elif folder.startswith("Media"):
        files.extend([
            ("Windows Background.wav", 386528),
            ("Windows Balloon.wav", 25876),
            ("Windows Battery Critical.wav", 25876),
            ("Windows Battery Low.wav", 25876),
            ("Windows Critical Stop.wav", 31768),
            ("Windows Default.wav", 25876),
            ("Windows Ding.wav", 25876),
            ("Windows Error.wav", 25876),
            ("Windows Exclamation.wav", 25876),
            ("Windows Feed Discovered.wav", 25876),
            ("Windows Hardware Fail.wav", 25876),
            ("Windows Hardware Insert.wav", 25876),
            ("Windows Hardware Remove.wav", 25876),
            ("Windows Information Bar.wav", 25876),
            ("Windows Logoff Sound.wav", 25876),
            ("Windows Logon Sound.wav", 25876),
            ("Windows Mail Beep.wav", 25876),
            ("Windows Maximize.wav", 25876),
            ("Windows Menu Command.wav", 25876),
            ("Windows Minimize.wav", 25876),
            ("Windows Notification.wav", 25876),
            ("Windows Pop-up Blocked.wav", 25876),
            ("Windows Print complete.wav", 25876),
            ("Windows Program Close.wav", 25876),
            ("Windows Program Open.wav", 25876),
            ("Windows Restore.wav", 25876),
            ("Windows Ring.wav", 25876),
            ("Windows Ring Tone.wav", 25876),
            ("Windows Startup.wav", 25876),
            ("Windows User Account Control.wav", 25876),
            ("Windows Windows Update.wav", 25876),
        ])
    
    elif folder.startswith("Microsoft.NET"):
        files.extend([
            ("mscorlib.dll", 4079616),
            ("mscorpe.dll", 104448),
            ("mscorsec.dll", 28672),
            ("mscorsn.dll", 42496),
            ("mscorwks.dll", 5611520),
            ("ngen.exe", 29184),
            ("regsvcs.exe", 11264),
            ("vbc.exe", 83968),
            ("csc.exe", 27136),
            ("clr.dll", 500480),
            ("clrjit.dll", 312832),
            ("microsoft.jscript.dll", 118784),
            ("microsoft.visualbasic.dll", 1499136),
            ("microsoft.visualc.dll", 25600),
            ("msvcm80.dll", 547328),
            ("msvcp80.dll", 547328),
            ("msvcr80.dll", 547328),
            ("system.dll", 3538944),
            ("system.data.dll", 2949120),
            ("system.drawing.dll", 548864),
            ("system.enterpriseservices.dll", 262144),
            ("system.web.dll", 4980736),
            ("system.windows.forms.dll", 4976640),
            ("system.xml.dll", 2048000),
        ])
    
    elif folder.startswith("assembly"):
        files.extend([
            ("NativeImages.exe", 16384),
            ("vsvars32.dll", 32768),
            ("RegSvcs.exe", 11264),
            ("System.EnterpriseServices.dll", 262144),
            ("System.EnterpriseServices.Wrapper.dll", 40960),
        ])
    
    elif folder == "Cursors":
        files.extend([
            ("aero_arrow.cur", 4284),
            ("aero_busy.ani", 7222),
            ("aero_cross.cur", 1102),
            ("aero_help.cur", 1054),
            ("aero_i beam.cur", 1150),
            ("aero_link.cur", 1102),
            ("aero_nsew.cur", 1606),
            ("aero_ns.cur", 1102),
            ("aero_pen.cur", 4254),
            ("aero_person.cur", 4254),
            ("aero_pin.cur", 4254),
            ("aero_unavail.cur", 2438),
            ("aero_up.cur", 1102),
            ("aero_ew.cur", 1102),
            ("aero_nesw.cur", 1606),
            ("aero_move.cur", 1606),
            ("arrow_r.cur", 4284),
            ("beam_r.cur", 1150),
            ("busy_r.ani", 7222),
            ("cross_r.cur", 1102),
            ("help_r.cur", 1054),
            ("hlink_r.cur", 1102),
            ("move_r.cur", 1606),
            ("nsew_r.cur", 1606),
            ("pen_r.cur", 4254),
            ("person_r.cur", 4254),
            ("pin_r.cur", 4254),
            ("unavail_r.cur", 2438),
            ("up_r.cur", 1102),
            ("wait_r.ani", 7222),
        ])
    
    elif folder == "Help":
        files.extend([
            ("windows.hlp", 123456),
            ("windows.chm", 234567),
            ("winhelp.hlp", 78901),
            ("hh.exe", 12345),
            ("hhctrl.ocx", 345678),
            ("helppane.exe", 45678),
            ("helpman.exe", 34567),
        ])
    
    elif folder == "Web\Wallpaper\Windows":
        files.extend([
            ("img0.jpg", 345678),
            ("img1.jpg", 456789),
            ("img2.jpg", 567890),
            ("img3.jpg", 678901),
            ("img4.jpg", 789012),
            ("img5.jpg", 890123),
            ("img6.jpg", 901234),
            ("img7.jpg", 123456),
            ("img8.jpg", 234567),
            ("img9.jpg", 345678),
        ])
    
    elif folder.startswith("Program Files"):
        if "Internet Explorer" in folder:
            files.extend([
                ("iexplore.exe", 678912),
                ("ieproxy.dll", 234567),
                ("iedkcs32.dll", 345678),
                ("ieui.dll", 456789),
                ("mshtml.dll", 5678901),
                ("mshtml.tlb", 123456),
            ])
        elif "Windows Media Player" in folder:
            files.extend([
                ("wmplayer.exe", 234567),
                ("wmp.dll", 3456789),
                ("wmploc.dll", 4567890),
                ("wmpmde.dll", 234567),
                ("wmpdxm.dll", 345678),
            ])
        elif "Movie Maker" in folder:
            files.extend([
                ("moviemk.exe", 345678),
                ("movieMaker.dll", 456789),
                ("mmres.dll", 234567),
            ])
    
    if not files:
        files.extend([
            ("desktop.ini", 49),
            (f"folder_{random.randint(1,999)}.dll", random.randint(1024, 102400)),
            (f"system_{random.randint(1,999)}.ini", random.randint(512, 5120)),
        ])
    
    return files

def create_virtual_drive():
    temp_dir = os.environ.get('TEMP', 'C:\\Temp')
    drive_path = os.path.join(temp_dir, 'VirtualWin7')
    
    os.makedirs(drive_path, exist_ok=True)
    os.system(f"subst {TARGET_DRIVE} {drive_path}")
    print(f"[OK] Диск {TARGET_DRIVE} создан (путь: {drive_path})")

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 Б"
    units = ['Б', 'КБ', 'МБ', 'ГБ']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {units[i]}"

def print_progress(current, total, start_time, desc="Прогресс"):
    percent = current / total * 100
    bar_len = 40
    filled = int(bar_len * current / total)
    bar = '█' * filled + '░' * (bar_len - filled)
    
    elapsed = time.time() - start_time
    speed = current / elapsed if elapsed > 0 else 0
    
    sys.stdout.write('\r')
    sys.stdout.write(f"{desc}: |{bar}| {percent:5.1f}%  {current:,}/{total:,}  {speed:.1f} шт/с")
    sys.stdout.flush()

def main():
    print("=" * 70)
    print("   🏗️  ГЕНЕРАТОР ПОЛНОЙ СТРУКТУРЫ WINDOWS 7")
    print("   Создаёт диск Z: и генерирует ВСЕ файлы с нуля")
    print("=" * 70)
    
    try:
        test_path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'test_admin.txt')
        with open(test_path, 'w') as f:
            f.write('test')
        os.remove(test_path)
    except:
        print("\n❌ ОШИБКА: Запустите от имени АДМИНИСТРАТОРА!")
        input("\nНажмите Enter для выхода...")
        return
    
    print("\n[1/3] Создание виртуального диска Z:...")
    create_virtual_drive()
    
    target = Path(TARGET_ROOT)
    target.mkdir(parents=True, exist_ok=True)
    
    print("\n[2/3] Генерация структуры...")
    all_files = []
    total_size = 0
    
    for folder in WINDOWS_7_FOLDERS:
        folder_path = target / folder
        os.makedirs(folder_path, exist_ok=True)
        
        files = get_files_for_folder(folder)
        for fname, fsize in files:
            all_files.append((folder, fname, fsize))
            total_size += fsize
    
    print(f"   Создано папок: {len(WINDOWS_7_FOLDERS):,}")
    print(f"   Файлов для создания: {len(all_files):,}")
    print(f"   Общий вес: {format_size(total_size)}")
    
    response = input("\nПродолжить создание файлов? (y/n): ")
    if response.lower() != 'y':
        print("❌ Отмена")
        input("\nНажмите Enter для выхода...")
        return
    
    print("\n[3/3] Создание файлов...")
    created = 0
    start_time = time.time()
    
    for folder, fname, fsize in all_files:
        file_path = target / folder / fname
        
        try:
            with open(file_path, 'wb') as f:
                if fsize > 0:
                    chunk_size = 8192
                    remaining = fsize
                    while remaining > 0:
                        chunk = min(chunk_size, remaining)
                        f.write(os.urandom(chunk))
                        remaining -= chunk
                else:
                    f.write(b'')
            created += 1
        except Exception as e:
            print(f"\nОшибка создания {file_path}: {e}")
        
        if created % 10 == 0:
            print_progress(created, len(all_files), start_time, "Файлы")
    
    print()
    
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    print("\n" + "=" * 70)
    print(" Test...")
    print(f"   ����Диск: {TARGET_DRIVE}")
    print(f"   ����Путь: {target}")
    print(f"   ����оздано файлов: {created:,}")
    print(f"    Папок: {len(WINDOWS_7_FOLDERS):,}")
    print(f"   System: {format_size(total_size)}")
    print(f"   Время: {minutes} мин {seconds} сек")
    print("=" * 70)
    print("\n Для отключения диска: subst Z: /D")

if __name__ == "__main__":
    try:
        main()
        input("\nНажмите Enter для выхода...")
    except KeyboardInterrupt:
        print("\n\nПРЕРВАНО!")
        input("\nНажмите Enter для выхода...")
    except Exception as e:
        print(f"\n ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")