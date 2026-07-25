import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import os

class ControlDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SysController & Puzzle Manager v1.0")
        self.geometry("600x450")
        self.configure(bg="#1e1e1e")

        # Style configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#333333", foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=1)
        style.map("TButton", background=[("active", "#555555")])

        # Title Label
        title_lbl = tk.Label(self, text="REMOTE BATCH & PROCESS CONTROLLER", font=("Segoe UI", 14, "bold"), fg="#00ffcc", bg="#1e1e1e")
        title_lbl.pack(pady=15)

        # Status frame
        status_frame = tk.Frame(self, bg="#252526", bd=2, relief="groove")
        status_frame.pack(fill="x", padx=20, pady=10)

        self.status_lbl = tk.Label(status_frame, text="Status: Ready / Waiting for action", font=("Segoe UI", 10), fg="#cccccc", bg="#252526")
        self.status_lbl.pack(anchor="w", padx=10, pady=10)

        # Control Buttons Frame
        btn_frame = tk.Frame(self, bg="#1e1e1e")
        btn_frame.pack(pady=20)

        # Row 1: Execution & Screenshots
        btn_run = ttk.Button(btn_frame, text="🚀 Launch Puzzle Script", command=self.launch_script)
        btn_run.grid(row=0, column=0, padx=10, pady=10, ipadx=10, ipady=8)

        btn_shot = ttk.Button(btn_frame, text="📸 Trigger Remote Screenshot", command=self.trigger_screenshot)
        btn_shot.grid(row=0, column=1, padx=10, pady=10, ipadx=10, ipady=8)

        # Row 2: Window Management & Process Termination
        btn_close_win = ttk.Button(btn_frame, text="🪟 Close Target Windows", command=self.close_windows)
        btn_close_win.grid(row=1, column=0, padx=10, pady=10, ipadx=10, ipady=8)

        btn_kill = ttk.Button(btn_frame, text="🛑 Kill Batch / PowerShell Processes", command=self.kill_processes)
        btn_kill.grid(row=1, column=1, padx=10, pady=10, ipadx=10, ipady=8)

        # Row 3: Utility / Open Explorer
        btn_open = ttk.Button(btn_frame, text="📂 Open Temp Directory", command=self.open_temp)
        btn_open.grid(row=2, column=0, columnspan=2, padx=10, pady=10, ipadx=50, ipady=8)

    def launch_script(self):
        try:
            # Launch the puzzle script or target batch file
            subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", "puzzle.bat"])
            self.status_lbl.config(text="Status: Puzzle script launched successfully.", fg="#00ff00")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch: {e}")

    def trigger_screenshot(self):
        # Quick PowerShell command to take and save screenshot locally
        cmd = 'powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $b = [Windows.Forms.Screen]::PrimaryScreen.Bounds; $bmp = New-Object Drawing.Bitmap $b.Width, $b.Height; $g = [Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.Location, [Drawing.Point]::Empty, $b.Size); $bmp.Save('$env:TEMP\remote_snap.png'); $g.Dispose(); $bmp.Dispose()"'
        try:
            subprocess.Popen(cmd, shell=True)
            self.status_lbl.config(text="Status: Screenshot captured to %TEMP%\remote_snap.png", fg="#00ff00")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def close_windows(self):
        # Close active command prompt windows running batch tasks
        try:
            subprocess.run(["taskkill", "/f", "/im", "cmd.exe"], capture_output=True)
            self.status_lbl.config(text="Status: All CMD windows terminated.", fg="#ffaa00")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def kill_processes(self):
        # Terminate active powershell instances handling background reports/scripts
        try:
            subprocess.run(["taskkill", "/f", "/im", "powershell.exe"], capture_output=True)
            self.status_lbl.config(text="Status: All PowerShell background processes killed.", fg="#ff5555")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_temp(self):
        temp_dir = os.path.expandvars("%TEMP%")
        os.startfile(temp_dir)
        self.status_lbl.config(text="Status: Opened TEMP directory in Explorer.", fg="#00ffcc")

if __name__ == "__main__":
    app = ControlDashboard()
    app.mainloop()
