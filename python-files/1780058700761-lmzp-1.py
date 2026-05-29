"""
โปรแกรมแก้ไขปัญหา Print Spooler แบบ GUI
รองรับ Windows 7/8/10/11
พัฒนาโดยใช้ tkinter (ติดมากับ Python)
ต้องรันด้วยสิทธิ์ Administrator เท่านั้น
"""

import os
import subprocess
import winreg as reg
import sys
import ctypes
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from datetime import datetime

class PrintSpoolerFixerGUI:
    """คลาสหลักสำหรับ GUI ของโปรแกรมแก้ไข Print Spooler"""
    
    def __init__(self, root):
        """
        เริ่มต้น GUI และตั้งค่าต่างๆ
        root: หน้าต่างหลักของ tkinter
        """
        self.root = root
        self.root.title("โปรแกรมแก้ไขปัญหา Print Spooler")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # ตั้งค่าไอคอน (ถ้ามี)
        try:
            self.root.iconbitmap(default="icon.ico")
        except:
            pass
        
        # ตัวแปรสำหรับเก็บสถานะ
        self.is_admin = False
        self.fix_status = {
            "method1": False,
            "method2": False, 
            "method3": False
        }
        
        # สร้างส่วนประกอบต่างๆ ของ GUI
        self.setup_ui()
        
        # ตรวจสอบสิทธิ์ Admin เมื่อเริ่มโปรแกรม
        self.check_admin_status()
    
    def setup_ui(self):
        """สร้างและจัดวางส่วนประกอบต่างๆ ในหน้าต่าง GUI"""
        
        # สร้างสไตล์
        style = ttk.Style()
        style.theme_use('vista')  # ใช้ธีมแบบ Windows Vista/7/10
        
        # ===== ส่วนหัว (Header) =====
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(header_frame, text="🖨️ โปรแกรมแก้ไขปัญหา Print Spooler", 
                                font=('Tahoma', 16, 'bold'))
        title_label.pack()
        
        desc_label = ttk.Label(header_frame, 
                               text="แก้ไขปัญหาบริการจัดการงานพิมพ์ไม่ทำงาน, งานพิมพ์ค้าง, ติดตั้งเครื่องพิมพ์ไม่ได้",
                               font=('Tahoma', 9))
        desc_label.pack()
        
        # ===== ส่วนแสดงสถานะ Admin =====
        self.admin_frame = ttk.Frame(self.root, padding="5")
        self.admin_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.admin_status_label = ttk.Label(self.admin_frame, text="🔍 กำลังตรวจสอบสิทธิ์...", 
                                            font=('Tahoma', 10))
        self.admin_status_label.pack()
        
        # ===== Notebook (แท็บต่างๆ) =====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # แท็บที่ 1: การแก้ไขหลัก
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="🔧 แก้ไขปัญหา")
        
        # แท็บที่ 2: บันทึกการทำงาน (Log)
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="📋 บันทึกการทำงาน")
        
        # แท็บที่ 3: ข้อมูลระบบ
        self.info_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.info_tab, text="ℹ️ ข้อมูลระบบ")
        
        # ===== สร้างเนื้อหาในแท็บแก้ไขปัญหา =====
        self.setup_main_tab()
        
        # ===== สร้างเนื้อหาในแท็บบันทึกการทำงาน =====
        self.setup_log_tab()
        
        # ===== สร้างเนื้อหาในแท็บข้อมูลระบบ =====
        self.setup_info_tab()
        
        # ===== ส่วนท้าย (Footer) =====
        footer_frame = ttk.Frame(self.root, padding="10")
        footer_frame.pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(footer_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack()
        
        self.fix_all_btn = ttk.Button(button_frame, text="🔧 แก้ไขทั้งหมดอัตโนมัติ", 
                                      command=self.start_fix_all, width=20)
        self.fix_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.restart_btn = ttk.Button(button_frame, text="🔄 รีสตาร์ทคอมพิวเตอร์", 
                                      command=self.restart_computer, width=20)
        self.restart_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_log_btn = ttk.Button(button_frame, text="🗑️ ล้างบันทึก", 
                                        command=self.clear_log, width=15)
        self.clear_log_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_main_tab(self):
        """สร้างส่วนประกอบในแท็บแก้ไขปัญหา"""
        
        # กรอบสำหรับวิธีการแก้ไขทั้ง 3 วิธี
        methods_frame = ttk.Frame(self.main_tab, padding="10")
        methods_frame.pack(fill=tk.BOTH, expand=True)
        
        # วิธีที่ 1
        method1_frame = ttk.LabelFrame(methods_frame, text="วิธีที่ 1: รีเซ็ตค่าการขึ้นต่อกัน (Dependencies)", 
                                       padding="10")
        method1_frame.pack(fill=tk.X, pady=5)
        
        method1_desc = ttk.Label(method1_frame, 
                                 text="ตั้งค่าให้บริการ Spooler ขึ้นต่อกับ RPCSS เท่านั้น (วิธีที่เร็วที่สุด)",
                                 wraplength=600)
        method1_desc.pack(anchor=tk.W)
        
        self.method1_btn = ttk.Button(method1_frame, text="▶ ดำเนินการวิธีที่ 1", 
                                      command=self.method1_reset_dependencies)
        self.method1_btn.pack(anchor=tk.W, pady=5)
        
        self.method1_status = ttk.Label(method1_frame, text="⏳ ยังไม่ได้ดำเนินการ", foreground="gray")
        self.method1_status.pack(anchor=tk.W)
        
        # วิธีที่ 2
        method2_frame = ttk.LabelFrame(methods_frame, text="วิธีที่ 2: ล้างงานพิมพ์ค้างและรีสตาร์ทบริการ", 
                                       padding="10")
        method2_frame.pack(fill=tk.X, pady=5)
        
        method2_desc = ttk.Label(method2_frame, 
                                 text="หยุดบริการ → ลบไฟล์งานพิมพ์ที่ค้าง → ตั้งค่า Auto → เริ่มบริการใหม่",
                                 wraplength=600)
        method2_desc.pack(anchor=tk.W)
        
        self.method2_btn = ttk.Button(method2_frame, text="▶ ดำเนินการวิธีที่ 2", 
                                      command=self.method2_clear_jobs_and_restart)
        self.method2_btn.pack(anchor=tk.W, pady=5)
        
        self.method2_status = ttk.Label(method2_frame, text="⏳ ยังไม่ได้ดำเนินการ", foreground="gray")
        self.method2_status.pack(anchor=tk.W)
        
        # วิธีที่ 3
        method3_frame = ttk.LabelFrame(methods_frame, text="วิธีที่ 3: แก้ไข Registry (ใช้เมื่อวิธีก่อนหน้าไม่สำเร็จ)", 
                                       padding="10")
        method3_frame.pack(fill=tk.X, pady=5)
        
        method3_desc = ttk.Label(method3_frame, 
                                 text="แก้ไขค่า DependOnService ใน Registry โดยตรง (สำหรับกรณี Registry เสียหาย)",
                                 wraplength=600)
        method3_desc.pack(anchor=tk.W)
        
        self.method3_btn = ttk.Button(method3_frame, text="▶ ดำเนินการวิธีที่ 3", 
                                      command=self.method3_fix_registry)
        self.method3_btn.pack(anchor=tk.W, pady=5)
        
        self.method3_status = ttk.Label(method3_frame, text="⏳ ยังไม่ได้ดำเนินการ", foreground="gray")
        self.method3_status.pack(anchor=tk.W)
        
        # ปุ่มตรวจสอบสถานะบริการ
        check_frame = ttk.Frame(methods_frame)
        check_frame.pack(fill=tk.X, pady=10)
        
        self.check_service_btn = ttk.Button(check_frame, text="🔍 ตรวจสอบสถานะ Print Spooler", 
                                            command=self.check_spooler_status)
        self.check_service_btn.pack(side=tk.LEFT, padx=5)
        
        self.service_status_label = ttk.Label(check_frame, text="", font=('Tahoma', 10, 'bold'))
        self.service_status_label.pack(side=tk.LEFT, padx=10)
    
    def setup_log_tab(self):
        """สร้างส่วนประกอบในแท็บบันทึกการทำงาน"""
        
        log_frame = ttk.Frame(self.log_tab, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # สร้าง Text widget พร้อม Scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=25,
                                                   font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ตั้งค่า tag สำหรับสีต่างๆ
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("warning", foreground="orange")
        
        # เพิ่มบันทึกแรกเริ่ม
        self.add_log("โปรแกรมเริ่มทำงานแล้ว", "info")
        self.add_log("="*60, "info")
    
    def setup_info_tab(self):
        """สร้างส่วนประกอบในแท็บข้อมูลระบบ"""
        
        info_frame = ttk.Frame(self.info_tab, padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # ข้อมูล Windows
        windows_frame = ttk.LabelFrame(info_frame, text="ข้อมูล Windows", padding="10")
        windows_frame.pack(fill=tk.X, pady=5)
        
        self.windows_info = ttk.Label(windows_frame, text="กำลังโหลด...", wraplength=600)
        self.windows_info.pack(anchor=tk.W)
        
        # ข้อมูล Print Spooler
        spooler_frame = ttk.LabelFrame(info_frame, text="ข้อมูลบริการ Print Spooler", padding="10")
        spooler_frame.pack(fill=tk.X, pady=5)
        
        self.spooler_info = ttk.Label(spooler_frame, text="กำลังโหลด...", wraplength=600)
        self.spooler_info.pack(anchor=tk.W)
        
        # ปุ่มรีเฟรช
        refresh_btn = ttk.Button(info_frame, text="🔄 รีเฟรชข้อมูล", command=self.refresh_system_info)
        refresh_btn.pack(pady=10)
        
        # โหลดข้อมูลทันที
        self.refresh_system_info()
    
    def add_log(self, message, level="info"):
        """
        เพิ่มข้อความลงในบันทึกการทำงาน
        message: ข้อความที่จะเพิ่ม
        level: success, error, info, warning
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)  # เลื่อนไปที่บรรทัดล่าสุด
        self.root.update_idletasks()
    
    def check_admin_status(self):
        """ตรวจสอบว่าโปรแกรมรันด้วยสิทธิ์ Administrator หรือไม่"""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            self.is_admin = is_admin
            
            if is_admin:
                self.admin_status_label.config(text="✅ สถานะ: รันด้วยสิทธิ์ Administrator แล้ว", 
                                              foreground="green")
                self.add_log("ตรวจสอบสิทธิ์: รันด้วย Administrator แล้ว (ผ่าน)", "success")
            else:
                self.admin_status_label.config(text="⚠️ สถานะ: ยังไม่ได้รันด้วยสิทธิ์ Administrator (คลิกปุ่มด้านล่างเพื่อขอสิทธิ์)", 
                                              foreground="orange")
                self.add_log("ตรวจสอบสิทธิ์: ยังไม่ได้รันด้วย Administrator (ต้องขอสิทธิ์)", "warning")
                
                # เพิ่มปุ่มขอสิทธิ์ Admin
                request_admin_btn = ttk.Button(self.admin_frame, text="👑 ขอสิทธิ์ Administrator", 
                                               command=self.request_admin_rights)
                request_admin_btn.pack(pady=5)
        except:
            self.admin_status_label.config(text="❌ ไม่สามารถตรวจสอบสิทธิ์ได้", foreground="red")
            self.add_log("ตรวจสอบสิทธิ์: ไม่สามารถตรวจสอบได้", "error")
    
    def request_admin_rights(self):
        """ขอสิทธิ์ Administrator ใหม่"""
        self.add_log("กำลังขอสิทธิ์ Administrator ผ่าน UAC...", "info")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            self.root.quit()  # ปิดโปรแกรมตัวเดิม
        except Exception as e:
            self.add_log(f"ไม่สามารถขอสิทธิ์ได้: {e}", "error")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถขอสิทธิ์ Administrator ได้\n{e}")
    
    def run_command(self, command):
        """รันคำสั่งระบบและคืนผลลัพธ์"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def method1_reset_dependencies(self):
        """วิธีที่ 1: รีเซ็ตค่าการขึ้นต่อกัน"""
        if not self.is_admin:
            messagebox.showwarning("สิทธิ์ไม่เพียงพอ", "กรุณาขอสิทธิ์ Administrator ก่อนดำเนินการ")
            return
        
        self.add_log("เริ่มดำเนินการวิธีที่ 1: รีเซ็ตค่า dependencies", "info")
        self.method1_btn.config(state=tk.DISABLED)
        self.method1_status.config(text="🔄 กำลังดำเนินการ...", foreground="orange")
        
        def run():
            returncode, _, stderr = self.run_command("sc config spooler depend= RPCSS")
            
            if returncode == 0:
                self.fix_status["method1"] = True
                self.method1_status.config(text="✅ สำเร็จ: ตั้งค่า dependencies เรียบร้อย", foreground="green")
                self.add_log("วิธีที่ 1 สำเร็จ: ตั้งค่า Dependencies เป็น RPCSS", "success")
                messagebox.showinfo("สำเร็จ", "วิธีที่ 1 ดำเนินการสำเร็จ")
            else:
                self.method1_status.config(text=f"❌ ล้มเหลว: {stderr[:50]}", foreground="red")
                self.add_log(f"วิธีที่ 1 ล้มเหลว: {stderr}", "error")
            
            self.method1_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=run, daemon=True).start()
    
    def method2_clear_jobs_and_restart(self):
        """วิธีที่ 2: ล้างงานพิมพ์ค้างและรีสตาร์ทบริการ"""
        if not self.is_admin:
            messagebox.showwarning("สิทธิ์ไม่เพียงพอ", "กรุณาขอสิทธิ์ Administrator ก่อนดำเนินการ")
            return
        
        self.add_log("เริ่มดำเนินการวิธีที่ 2: ล้างงานพิมพ์ค้างและรีสตาร์ทบริการ", "info")
        self.method2_btn.config(state=tk.DISABLED)
        self.method2_status.config(text="🔄 กำลังดำเนินการ...", foreground="orange")
        
        def run():
            # หยุดบริการ
            self.add_log("กำลังหยุดบริการ Print Spooler...", "info")
            self.run_command("net stop spooler")
            
            # ลบไฟล์งานพิมพ์ค้าง
            spool_path = os.path.expandvars(r"%WINDIR%\system32\spool\PRINTERS")
            deleted_count = 0
            
            if os.path.exists(spool_path):
                self.add_log(f"กำลังลบไฟล์ใน {spool_path}", "info")
                for filename in os.listdir(spool_path):
                    file_path = os.path.join(spool_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            deleted_count += 1
                            self.add_log(f"  ลบไฟล์: {filename}", "info")
                    except Exception as e:
                        self.add_log(f"  ไม่สามารถลบ {filename}: {e}", "warning")
                
                self.add_log(f"ลบไฟล์ไปแล้ว {deleted_count} ไฟล์", "success" if deleted_count > 0 else "info")
            else:
                self.add_log(f"ไม่พบโฟลเดอร์: {spool_path}", "warning")
            
            # ตั้งค่า Auto และเริ่มบริการ
            self.add_log("ตั้งค่า Startup type เป็น Automatic...", "info")
            self.run_command("sc config spooler start= auto")
            
            self.add_log("กำลังเริ่มบริการ Print Spooler ใหม่...", "info")
            returncode, _, stderr = self.run_command("net start spooler")
            
            if returncode == 0:
                self.fix_status["method2"] = True
                self.method2_status.config(text="✅ สำเร็จ: บริการทำงานปกติ", foreground="green")
                self.add_log("วิธีที่ 2 สำเร็จ: บริการ Print Spooler เริ่มทำงานแล้ว", "success")
                messagebox.showinfo("สำเร็จ", "วิธีที่ 2 ดำเนินการสำเร็จ\nบริการ Print Spooler ทำงานปกติแล้ว")
            else:
                self.method2_status.config(text=f"❌ ล้มเหลว: {stderr[:50]}", foreground="red")
                self.add_log(f"วิธีที่ 2 ล้มเหลว: {stderr}", "error")
                messagebox.showerror("ล้มเหลว", f"ไม่สามารถเริ่มบริการได้\n{stderr}")
            
            self.method2_btn.config(state=tk.NORMAL)
            self.check_spooler_status()  # อัปเดตสถานะ
        
        threading.Thread(target=run, daemon=True).start()
    
    def method3_fix_registry(self):
        """วิธีที่ 3: แก้ไข Registry"""
        if not self.is_admin:
            messagebox.showwarning("สิทธิ์ไม่เพียงพอ", "กรุณาขอสิทธิ์ Administrator ก่อนดำเนินการ")
            return
        
        self.add_log("เริ่มดำเนินการวิธีที่ 3: แก้ไข Registry", "info")
        self.method3_btn.config(state=tk.DISABLED)
        self.method3_status.config(text="🔄 กำลังดำเนินการ...", foreground="orange")
        
        def run():
            try:
                registry_path = r"SYSTEM\CurrentControlSet\Services\Spooler"
                key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, registry_path, 0, reg.KEY_SET_VALUE)
                reg.SetValueEx(key, "DependOnService", 0, reg.REG_MULTI_SZ, ["RPCSS"])
                reg.CloseKey(key)
                
                self.fix_status["method3"] = True
                self.method3_status.config(text="✅ สำเร็จ: แก้ไข Registry เรียบร้อย", foreground="green")
                self.add_log("วิธีที่ 3 สำเร็จ: ตั้งค่า DependOnService = RPCSS", "success")
                messagebox.showinfo("สำเร็จ", "วิธีที่ 3 ดำเนินการสำเร็จ\nกรุณารีสตาร์ทเครื่องเพื่อให้มีผล")
                
            except Exception as e:
                self.method3_status.config(text=f"❌ ล้มเหลว: {str(e)[:50]}", foreground="red")
                self.add_log(f"วิธีที่ 3 ล้มเหลว: {e}", "error")
                messagebox.showerror("ล้มเหลว", f"ไม่สามารถแก้ไข Registry ได้\n{e}")
            
            self.method3_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=run, daemon=True).start()
    
    def check_spooler_status(self):
        """ตรวจสอบสถานะของบริการ Print Spooler"""
        self.add_log("กำลังตรวจสอบสถานะ Print Spooler...", "info")
        
        def run():
            returncode, stdout, _ = self.run_command("sc query spooler")
            
            if "RUNNING" in stdout.upper():
                self.service_status_label.config(text="✅ กำลังทำงาน", foreground="green")
                self.add_log("สถานะ Print Spooler: กำลังทำงาน", "success")
            elif "STOPPED" in stdout.upper():
                self.service_status_label.config(text="❌ หยุดทำงาน", foreground="red")
                self.add_log("สถานะ Print Spooler: หยุดทำงาน", "warning")
            else:
                self.service_status_label.config(text="⚠️ ไม่ทราบสถานะ", foreground="orange")
                self.add_log("สถานะ Print Spooler: ไม่ทราบสถานะ", "warning")
        
        threading.Thread(target=run, daemon=True).start()
    
    def refresh_system_info(self):
        """รีเฟรชข้อมูลระบบ"""
        self.add_log("กำลังโหลดข้อมูลระบบ...", "info")
        
        def run():
            # ข้อมูล Windows
            try:
                key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                product_name = reg.QueryValueEx(key, "ProductName")[0]
                current_version = reg.QueryValueEx(key, "CurrentVersion")[0]
                reg.CloseKey(key)
                
                windows_text = f"Windows: {product_name}\nรุ่น: {current_version}"
            except:
                windows_text = "ไม่สามารถอ่านข้อมูล Windows ได้"
            
            # ข้อมูล Print Spooler
            returncode, stdout, _ = self.run_command("sc query spooler")
            status = "RUNNING" if "RUNNING" in stdout.upper() else "STOPPED"
            
            spooler_text = f"สถานะ: {status}\n"
            
            # อัปเดต GUI
            self.windows_info.config(text=windows_text)
            self.spooler_info.config(text=spooler_text)
            self.add_log("โหลดข้อมูลระบบเรียบร้อย", "success")
        
        threading.Thread(target=run, daemon=True).start()
    
    def start_fix_all(self):
        """ดำเนินการแก้ไขทั้งหมดอัตโนมัติ (วิธีที่ 1 -> 2 -> 3)"""
        if not self.is_admin:
            messagebox.showwarning("สิทธิ์ไม่เพียงพอ", "กรุณาขอสิทธิ์ Administrator ก่อนดำเนินการ")
            return
        
        result = messagebox.askyesno("ยืนยัน", 
                                     "โปรแกรมจะดำเนินการแก้ไขทั้งหมดอัตโนมัติ:\n"
                                     "1. รีเซ็ตค่า Dependencies\n"
                                     "2. ล้างงานพิมพ์ค้างและรีสตาร์ทบริการ\n"
                                     "3. แก้ไข Registry (ถ้าจำเป็น)\n\n"
                                     "คุณต้องการดำเนินการต่อหรือไม่?")
        
        if not result:
            return
        
        self.add_log("="*60, "info")
        self.add_log("เริ่มดำเนินการแก้ไขทั้งหมดอัตโนมัติ", "info")
        
        # เริ่ม Progress Bar
        self.progress_bar.start()
        self.fix_all_btn.config(state=tk.DISABLED)
        
        def run_all():
            # วิธีที่ 1
            self.add_log("ขั้นตอนที่ 1/3: รีเซ็ต dependencies", "info")
            self.run_command("sc config spooler depend= RPCSS")
            
            # วิธีที่ 2
            self.add_log("ขั้นตอนที่ 2/3: ล้างงานพิมพ์ค้างและรีสตาร์ทบริการ", "info")
            self.run_command("net stop spooler")
            
            spool_path = os.path.expandvars(r"%WINDIR%\system32\spool\PRINTERS")
            if os.path.exists(spool_path):
                for filename in os.listdir(spool_path):
                    file_path = os.path.join(spool_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except:
                        pass
            
            self.run_command("sc config spooler start= auto")
            returncode, _, _ = self.run_command("net start spooler")
            
            # ถ้าวิธีที่ 2 ล้มเหลว ให้ทำวิธีที่ 3
            if returncode != 0:
                self.add_log("วิธีที่ 2 ล้มเหลว กำลังลองวิธีที่ 3...", "warning")
                try:
                    registry_path = r"SYSTEM\CurrentControlSet\Services\Spooler"
                    key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, registry_path, 0, reg.KEY_SET_VALUE)
                    reg.SetValueEx(key, "DependOnService", 0, reg.REG_MULTI_SZ, ["RPCSS"])
                    reg.CloseKey(key)
                    self.add_log("แก้ไข Registry เรียบร้อย", "success")
                    
                    # ลองเริ่มบริการอีกครั้ง
                    self.run_command("net start spooler")
                except Exception as e:
                    self.add_log(f"แก้ไข Registry ล้มเหลว: {e}", "error")
            
            # ตรวจสอบผลลัพธ์
            _, stdout, _ = self.run_command("sc query spooler")
            if "RUNNING" in stdout.upper():
                self.add_log("✅ แก้ไขสำเร็จ! Print Spooler ทำงานปกติ", "success")
                messagebox.showinfo("สำเร็จ", "แก้ไข Print Spooler สำเร็จ!\nบริการทำงานปกติแล้ว")
            else:
                self.add_log("❌ แก้ไขไม่สำเร็จ กรุณาตรวจสอบด้วยตนเอง", "error")
                messagebox.showerror("ไม่สำเร็จ", "ไม่สามารถแก้ไขปัญหาได้\nกรุณาตรวจสอบ Windows Event Viewer")
            
            # หยุด Progress Bar
            self.progress_bar.stop()
            self.fix_all_btn.config(state=tk.NORMAL)
            self.check_spooler_status()
        
        threading.Thread(target=run_all, daemon=True).start()
    
    def restart_computer(self):
        """รีสตาร์ทคอมพิวเตอร์"""
        result = messagebox.askyesno("ยืนยันการรีสตาร์ท", 
                                     "คุณต้องการรีสตาร์ทคอมพิวเตอร์ตอนนี้หรือไม่?\n\n"
                                     "ระบบจะรีสตาร์ทใน 10 วินาที (สามารถยกเลิกได้โดยพิมพ์ 'shutdown /a' ใน CMD)")
        
        if result:
            self.add_log("กำลังรีสตาร์ทคอมพิวเตอร์ใน 10 วินาที...", "warning")
            os.system("shutdown /r /t 10")
            messagebox.showinfo("รีสตาร์ท", "ระบบจะรีสตาร์ทใน 10 วินาที\nเปิด CMD แล้วพิมพ์ 'shutdown /a' เพื่อยกเลิก")
    
    def clear_log(self):
        """ล้างบันทึกการทำงาน"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("ล้างบันทึกการทำงานแล้ว", "info")


def main():
    """ฟังก์ชันหลักสำหรับเริ่มโปรแกรม"""
    root = tk.Tk()
    app = PrintSpoolerFixerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()