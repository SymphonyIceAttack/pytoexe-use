#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trial Reset for Kaspersky (KSOS) – GUI Edition
Full license reset without IObitUnlocker.
Requires Administrator privileges.
"""

import os
import sys
import subprocess
import ctypes
import shutil
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from pathlib import Path

# ==================== Helper Functions ====================

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-launch the script with administrator privileges."""
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
    except Exception as e:
        messagebox.showerror("Error", f"Failed to elevate privileges: {e}")
    sys.exit()

def run_cmd(command, capture=False):
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            subprocess.run(command, shell=True, check=False)
            return "", "", 0
    except Exception as e:
        return "", str(e), -1

def grant_permissions(path, sid="*S-1-5-32-544"):
    """Grant full control to Administrators (SID) on a file/folder."""
    run_cmd(f'icacls "{path}" /grant {sid}:(F,WDAC) /t /q')

# ==================== Core Reset Logic ====================

def get_product_info():
    """Determine product type (AVP or KES) and version folder."""
    program_data = os.environ.get("ProgramData", "C:\\ProgramData")
    base = os.path.join(program_data, "Kaspersky Lab")
    if not os.path.exists(base):
        return None, None, None, None

    avp_folders = [d for d in os.listdir(base) if d.startswith("AVP")]
    kes_folders = [d for d in os.listdir(base) if d.startswith("KES")]

    type_av = None
    folder = None
    if avp_folders:
        type_av = "AVP"
        folder = avp_folders[0]
    elif kes_folders:
        type_av = "KES"
        folder = kes_folders[0]
    else:
        return None, None, None, None

    if type_av == "AVP":
        reg_path = f"HKLM\\SOFTWARE\\WOW6432Node\\KasperskyLab\\{folder}"
    else:
        reg_path = f"HKLM\\SOFTWARE\\WOW6432Node\\KasperskyLab\\protected\\{folder}"
    data_path = os.path.join(base, folder)
    return type_av, folder, reg_path, data_path

def remove_klobjdb(drive, log_callback=None):
    """Locate and delete all klobjdb.dat files."""
    svi = os.path.join(drive, "System Volume Information")
    if not os.path.exists(svi):
        if log_callback:
            log_callback("System Volume Information not found.")
        return False

    # Grant permissions
    grant_permissions(svi)
    for item in os.listdir(svi):
        if item.startswith("K"):
            subfolder = os.path.join(svi, item)
            if os.path.isdir(subfolder):
                grant_permissions(subfolder)

    deleted = False
    for root, dirs, files in os.walk(svi):
        for file in files:
            if file.lower() == "klobjdb.dat":
                full_path = os.path.join(root, file)
                if log_callback:
                    log_callback(f"Found: {full_path}")
                # Take ownership
                run_cmd(f'takeown /f "{full_path}"')
                run_cmd(f'icacls "{full_path}" /grant {os.environ["USERNAME"]}:F')
                run_cmd(f'icacls "{full_path}" /grant *S-1-5-32-544:(F)')
                run_cmd(f'attrib -r -s -h "{full_path}"')
                try:
                    os.remove(full_path)
                    if log_callback:
                        log_callback(f"Deleted: {full_path}")
                    deleted = True
                except Exception as e:
                    if log_callback:
                        log_callback(f"Failed to delete {full_path}: {e}")
    # Revoke permissions
    run_cmd(f'icacls "{svi}" /remove *S-1-5-32-544 /t /c /q')
    return deleted

def delete_data_files(data_path, log_callback=None):
    """Delete license-related data files."""
    data_folder = os.path.join(data_path, "Data")
    if not os.path.exists(data_folder):
        if log_callback:
            log_callback("Data folder not found.")
        return
    patterns = ["*.bin", "cat_engine*", "certdb_v2.*.idx"]
    for pattern in patterns:
        for file in Path(data_folder).glob(pattern):
            try:
                os.remove(file)
                if log_callback:
                    log_callback(f"Deleted: {file}")
            except Exception as e:
                if log_callback:
                    log_callback(f"Failed to delete {file}: {e}")

def delete_registry_keys(reg_path, log_callback=None):
    """Delete license-related registry keys."""
    keys = [
        f"{reg_path}\\Data\\LicCache",
        f"{reg_path}\\Data\\LicensingActivationErrorStorageLogic",
        f"HKLM\\SOFTWARE\\WOW6432Node\\KasperskyLab\\LicStrg",
        f"{reg_path}\\Data\\UPAO",
        "HKLM\\SOFTWARE\\Microsoft\\SystemCertificates\\SPC",
    ]
    for key in keys:
        out, err, code = run_cmd(f'reg delete "{key}" /f', capture=True)
        if log_callback:
            if code == 0:
                log_callback(f"Deleted registry key: {key}")
            else:
                log_callback(f"Failed to delete {key}: {err or 'key not found'}")

def set_reset_registry(reg_path, self_protection_value=0, log_callback=None):
    """Set registry values for reset."""
    settings_path = f"{reg_path}\\settings"
    env_path = f"{reg_path}\\environment"
    data_upao = f"{reg_path}\\Data\\UPAO"
    commands = [
        f'reg add "{settings_path}" /v EnableSelfProtection /t REG_DWORD /d {self_protection_value} /f',
        f'reg add "{settings_path}" /v Ins_InitMode /t REG_DWORD /d 1 /f',
        f'reg add "{data_upao}" /v UpaoState /t REG_DWORD /d 1 /f',
        f'reg add "{env_path}" /v UpaoState /t REG_SZ /d 1 /f',
        f'reg add "HKLM\\SOFTWARE\\WOW6432Node\\KasperskyLab\\LicStrg" /f',
    ]
    for cmd in commands:
        out, err, code = run_cmd(cmd, capture=True)
        if log_callback:
            if code == 0:
                log_callback(f"Set registry: {cmd}")
            else:
                log_callback(f"Failed: {cmd} -> {err}")

def reboot_system(log_callback=None):
    """Reboot the system."""
    if log_callback:
        log_callback("Rebooting system in 5 seconds...")
    time.sleep(5)
    run_cmd("shutdown /r /t 0")

# ==================== GUI Application ====================

class TrialResetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kaspersky Trial Reset (KSOS)")
        self.root.geometry("720x550")
        self.root.resizable(False, False)

        # Product info
        self.type_av = None
        self.folder = None
        self.reg_path = None
        self.data_path = None
        self.product_name = "Unknown"

        # UI elements
        self.create_widgets()
        self.check_product()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Kaspersky Trial Reset", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Product info frame
        info_frame = ttk.LabelFrame(main_frame, text="Product Information", padding="5")
        info_frame.pack(fill=tk.X, pady=5)

        self.info_text = tk.StringVar(value="Detecting...")
        info_label = ttk.Label(info_frame, textvariable=self.info_text, font=("Helvetica", 10))
        info_label.pack(anchor=tk.W, pady=2)

        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.pack(fill=tk.X, pady=5)

        self.self_protect_var = tk.IntVar(value=0)
        self.self_protect_check = ttk.Checkbutton(
            options_frame,
            text="Enable Self-Protection after reset (recommended)",
            variable=self.self_protect_var
        )
        self.self_protect_check.pack(anchor=tk.W, pady=2)

        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.reset_btn = ttk.Button(btn_frame, text="Start Reset", command=self.start_reset)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        self.exit_btn = ttk.Button(btn_frame, text="Exit", command=self.root.quit)
        self.exit_btn.pack(side=tk.RIGHT, padx=5)

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def check_product(self):
        """Detect product and update UI."""
        self.type_av, self.folder, self.reg_path, self.data_path = get_product_info()
        if self.type_av:
            # Try to read ProductName from registry
            try:
                key_path = f"{self.reg_path}\\environment"
                # Use reg query to get ProductName
                out, err, code = run_cmd(f'reg query "{key_path}" /v ProductName', capture=True)
                if code == 0:
                    lines = out.splitlines()
                    for line in lines:
                        if "ProductName" in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                self.product_name = parts[2]
                                break
                else:
                    self.product_name = f"{self.type_av} ({self.folder})"
            except:
                self.product_name = f"{self.type_av} ({self.folder})"
            self.info_text.set(f"Product: {self.product_name}\nVersion: {self.folder}\nType: {self.type_av}")
            self.log("Product detected successfully.")
        else:
            self.info_text.set("No Kaspersky product found!")
            self.reset_btn.config(state=tk.DISABLED)
            self.log("ERROR: No supported Kaspersky product found in ProgramData.")
            messagebox.showerror("Error", "No supported Kaspersky product found.\nMake sure Kaspersky is installed.")

    def log(self, message):
        """Append message to log area."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_reset(self):
        """Start reset process in a separate thread."""
        if not self.type_av:
            messagebox.showerror("Error", "No product detected. Cannot proceed.")
            return

        self.reset_btn.config(state=tk.DISABLED, text="Working...")
        self.log("=" * 50)
        self.log("Starting reset process...")

        # Run in thread to keep UI responsive
        thread = threading.Thread(target=self.reset_process, daemon=True)
        thread.start()

    def reset_process(self):
        """Perform the actual reset steps."""
        try:
            drive = os.environ.get("SystemDrive", "C:")
            self_protection = self.self_protect_var.get()

            # Step 1: Remove klobjdb.dat
            self.log("Removing klobjdb.dat...")
            remove_klobjdb(drive, self.log)

            # Step 2: Delete data files
            self.log("Removing Kaspersky data files...")
            delete_data_files(self.data_path, self.log)

            # Step 3: Delete registry keys
            self.log("Removing license registry keys...")
            delete_registry_keys(self.reg_path, self.log)

            # Step 4: Set reset registry values
            self.log("Configuring reset registry settings...")
            set_reset_registry(self.reg_path, self_protection, self.log)

            self.log("Reset completed successfully!")
            self.log("Rebooting system...")
            # Reboot after a short delay
            self.root.after(2000, self.finish_reset)

        except Exception as e:
            self.log(f"ERROR: {e}")
            self.reset_btn.config(state=tk.NORMAL, text="Start Reset")
            messagebox.showerror("Error", f"Reset failed: {e}")

    def finish_reset(self):
        """Reboot system and close GUI."""
        # Ask user confirmation for reboot
        if messagebox.askyesno("Reboot", "Reset completed. Reboot now to apply changes?"):
            self.log("Rebooting...")
            reboot_system(self.log)
        else:
            self.log("Reboot cancelled. You must restart manually for changes to take effect.")
            self.reset_btn.config(state=tk.NORMAL, text="Start Reset")

# ==================== Entry Point ====================

def main():
    # Check admin rights
    if not is_admin():
        # Re-launch as admin
        run_as_admin()
        return

    # Start GUI
    root = tk.Tk()
    app = TrialResetApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()