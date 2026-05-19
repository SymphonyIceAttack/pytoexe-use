import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os

class ShareToolApp:
    def __init__(self, root):
        self.root = root
        self.check_dependencies()
        self.root.title("Easy Share Tool (Printer & Folder)")
        self.root.geometry("600x400")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Tabs
        self.server_folder_tab = ttk.Frame(self.notebook)
        self.server_printer_tab = ttk.Frame(self.notebook)
        self.client_folder_tab = ttk.Frame(self.notebook)
        self.client_printer_tab = ttk.Frame(self.notebook)
        self.error_fixes_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.server_folder_tab, text='Server: Folder')
        self.notebook.add(self.server_printer_tab, text='Server: Printer')
        self.notebook.add(self.client_folder_tab, text='Client: Folder')
        self.notebook.add(self.client_printer_tab, text='Client: Printer')
        self.notebook.add(self.error_fixes_tab, text='Error Fixes')

        self.setup_server_folder_tab()
        self.setup_server_printer_tab()
        self.setup_client_folder_tab()
        self.setup_client_printer_tab()
        self.setup_error_fixes_tab()

    def setup_server_folder_tab(self):
        ttk.Label(self.server_folder_tab, text="Server Folder Sharing", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(self.server_folder_tab)
        frame.pack(pady=10, padx=20, fill='x')

        ttk.Label(frame, text="Select Folder:").pack(side='left')
        self.folder_path_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.folder_path_var).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_folder).pack(side='left')

        ttk.Button(self.server_folder_tab, text="Share without Restrictions", command=self.share_folder).pack(pady=20)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path_var.set(path)

    def share_folder(self):
        folder_path = self.folder_path_var.get().strip()
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        
        # Additional validation: avoid sharing system root or home directly
        if folder_path in ["/", "/home", "/etc", "/var"]:
             if not messagebox.askyesno("Warning", f"You are about to share a sensitive system directory: {folder_path}. Are you sure?"):
                 return

        share_name = os.path.basename(folder_path)
        if not share_name:
            share_name = "shared_drive"

        # 1. Update permissions
        try:
            subprocess.run(['sudo', 'chmod', '-R', '777', folder_path], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set permissions: {e}")
            return

        # 2. Add to Samba config
        samba_config = f"\n[{share_name}]\n   path = {folder_path}\n   browseable = yes\n   writable = yes\n   guest ok = yes\n   create mask = 0777\n   directory mask = 0777\n   public = yes\n"
        
        try:
            # Check if share already exists in smb.conf to avoid duplicates
            with open('/etc/samba/smb.conf', 'r') as f:
                content = f.read()
                if f"[{share_name}]" in content:
                    messagebox.showinfo("Info", "Share already exists in Samba config.")
                else:
                    # Fix: Avoid 'bash -c' with interpolation. Use pipe and 'tee -a'
                    subprocess.run(['sudo', 'tee', '-a', '/etc/samba/smb.conf'], input=samba_config, text=True, check=True, capture_output=True)
            
            subprocess.run(['sudo', 'systemctl', 'restart', 'smbd'], check=True)
            messagebox.showinfo("Success", f"Folder '{share_name}' shared successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Samba config: {e}")

    def setup_server_printer_tab(self):
        ttk.Label(self.server_printer_tab, text="Server Printer Sharing", font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Label(self.server_printer_tab, text="Local Printers:").pack()
        self.printer_listbox = tk.Listbox(self.server_printer_tab, height=10)
        self.printer_listbox.pack(pady=10, padx=20, fill='both', expand=True)

        btn_frame = ttk.Frame(self.server_printer_tab)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Refresh List", command=self.refresh_printers).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Share Selected Printer", command=self.share_printer).pack(side='left', padx=5)

        self.refresh_printers()

    def refresh_printers(self):
        self.printer_listbox.delete(0, tk.END)
        try:
            result = subprocess.run(['lpstat', '-e'], capture_output=True, text=True)
            printers = result.stdout.splitlines()
            for p in printers:
                self.printer_listbox.insert(tk.END, p)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list printers: {e}")

    def share_printer(self):
        selection = self.printer_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a printer from the list.")
            return
        
        printer_name = self.printer_listbox.get(selection[0])
        
        try:
            # 1. Enable global printer sharing in CUPS
            subprocess.run(['sudo', 'cupsctl', '--share-printers'], check=True)
            
            # 2. Specifically share the selected printer
            subprocess.run(['sudo', 'lpadmin', '-p', printer_name, '-o', 'printer-is-shared=true'], check=True)
            
            # 3. Allow access from everywhere (simple tool approach)
            subprocess.run(['sudo', 'cupsctl', '--remote-any'], check=True)
            
            messagebox.showinfo("Success", f"Printer '{printer_name}' shared successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to share printer: {e}")

    def setup_client_folder_tab(self):
        ttk.Label(self.client_folder_tab, text="Client Folder Discovery", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(self.client_folder_tab)
        frame.pack(pady=10, padx=20, fill='x')

        ttk.Label(frame, text="Server IP/Hostname:").pack(side='left')
        self.server_ip_var = tk.StringVar(value="localhost")
        ttk.Entry(frame, textvariable=self.server_ip_var).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(frame, text="Scan Shares", command=self.scan_folder_shares).pack(side='left')

        self.folder_shares_listbox = tk.Listbox(self.client_folder_tab, height=10)
        self.folder_shares_listbox.pack(pady=10, padx=20, fill='both', expand=True)

    def scan_folder_shares(self):
        server_ip = self.server_ip_var.get().strip()
        if not server_ip:
            messagebox.showerror("Error", "Please enter a server IP or hostname.")
            return
            
        # Basic validation for IP/Hostname
        if not all(c.isalnum() or c in '.-' for c in server_ip):
            messagebox.showerror("Error", "Invalid IP or hostname format.")
            return

        self.folder_shares_listbox.delete(0, tk.END)
        try:
            # Use smbclient to list shares. -N for no password (guest)
            result = subprocess.run(['smbclient', '-L', server_ip, '-N'], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            
            start_parsing = False
            for line in lines:
                if 'Sharename' in line and 'Type' in line:
                    start_parsing = True
                    continue
                if start_parsing:
                    if not line.strip() or line.startswith('---') or 'Reconnecting' in line:
                        if line.startswith('SMB1'): continue # skip some junk
                        if not line.strip(): continue
                    
                    # Usually formatted as "Sharename       Type      Comment"
                    parts = line.split()
                    if parts and parts[1] == 'Disk':
                        self.folder_shares_listbox.insert(tk.END, f"{parts[0]} (at {server_ip})")
            
            if self.folder_shares_listbox.size() == 0:
                 self.folder_shares_listbox.insert(tk.END, "No disk shares found or server unreachable.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan shares: {e}")

    def setup_client_printer_tab(self):
        ttk.Label(self.client_printer_tab, text="Client Printer Discovery", font=('Arial', 12, 'bold')).pack(pady=10)
        
        btn_frame = ttk.Frame(self.client_printer_tab)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Scan Network Printers", command=self.scan_network_printers).pack(side='left', padx=5)

        self.network_printers_listbox = tk.Listbox(self.client_printer_tab, height=10)
        self.network_printers_listbox.pack(pady=10, padx=20, fill='both', expand=True)

    def scan_network_printers(self):
        self.network_printers_listbox.delete(0, tk.END)
        try:
            # lpstat -v shows all known devices, including remote ones found via browsing
            result = subprocess.run(['lpstat', '-v'], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if 'device for' in line:
                    # Format: "device for PRINTER_NAME: ipp://..."
                    parts = line.split(':')
                    printer_info = parts[0].replace('device for ', '').strip()
                    uri = parts[1].strip() if len(parts) > 1 else "Unknown URI"
                    self.network_printers_listbox.insert(tk.END, f"{printer_info} ({uri})")
            
            if self.network_printers_listbox.size() == 0:
                self.network_printers_listbox.insert(tk.END, "No network printers discovered. Ensure CUPS browsing is enabled.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan network printers: {e}")

    def setup_error_fixes_tab(self):
        ttk.Label(self.error_fixes_tab, text="Common Fixes for Sharing Errors", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(self.error_fixes_tab)
        frame.pack(pady=10, padx=20, fill='both', expand=True)

        # Printer Fixes
        ttk.Label(frame, text="Printer Fixes:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        ttk.Button(frame, text="Restart CUPS Service", command=lambda: self.run_fix(["sudo", "systemctl", "restart", "cups"], "CUPS restarted")).pack(fill='x', pady=2)
        ttk.Button(frame, text="Clear All Print Queues", command=lambda: self.run_fix(["sudo", "cancel", "-a"], "All print queues cleared")).pack(fill='x', pady=2)
        ttk.Button(frame, text="Enable Remote Admin", command=lambda: self.run_fix(["sudo", "cupsctl", "--remote-admin", "--remote-any"], "Remote administration enabled")).pack(fill='x', pady=2)

        # Folder Fixes
        ttk.Label(frame, text="Folder Fixes:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=15)
        ttk.Button(frame, text="Restart Samba Service", command=lambda: self.run_fix(["sudo", "systemctl", "restart", "smbd"], "Samba restarted")).pack(fill='x', pady=2)
        ttk.Button(frame, text="Test Samba Config", command=self.test_samba_config).pack(fill='x', pady=2)

    def run_fix(self, command, success_msg):
        try:
            subprocess.run(command, check=True)
            messagebox.showinfo("Success", success_msg)
        except Exception as e:
            messagebox.showerror("Error", f"Action failed: {e}")

    def test_samba_config(self):
        try:
            result = subprocess.run(['testparm', '-s'], capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Samba Config OK", "Configuration is valid.")
            else:
                messagebox.showerror("Samba Config Error", result.stderr)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test config: {e}")

    def check_dependencies(self):
        deps = ['samba', 'cupsd', 'smbclient', 'lpstat']
        missing = []
        for d in deps:
            if subprocess.run(['which', d], capture_output=True).returncode != 0:
                # 'samba' binary might not exist, but 'smbd' should
                if d == 'samba':
                    if subprocess.run(['which', 'smbd'], capture_output=True).returncode != 0:
                         missing.append(d)
                else:
                    missing.append(d)
        
        if missing:
            messagebox.showwarning("Missing Dependencies", f"The following tools might be missing: {', '.join(missing)}. Some features may not work.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ShareToolApp(root)
    root.mainloop()
