import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkFont
import json
import os
from datetime import datetime
from pathlib import Path

class ServerManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Management System")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")
        
        self.servers = []
        self.users = []
        self.logs = []
        self.data_file = "server_data.json"
        self.load_data()
        
        self.setup_styles()
        self.create_ui()
        
    def setup_styles(self):
        self.root.configure(bg="#1e1e1e")
        style = ttk.Style()
        style.theme_use("clam")
        
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#0078d4"
        button_bg = "#2d2d2d"
        
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=button_bg, foreground=fg_color)
        style.map("TButton", background=[("active", accent_color)])
        style.configure("TNotebook", background=bg_color, foreground=fg_color)
        style.configure("TNotebook.Tab", background=button_bg, foreground=fg_color)
        style.map("TNotebook.Tab", background=[("selected", accent_color)])
        
    def create_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_font = tkFont.Font(family="Segoe UI", size=18, weight="bold")
        title_label = ttk.Label(header_frame, text="🖥️ Server Management System", font=title_font)
        title_label.pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(header_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        save_btn = ttk.Button(button_frame, text="💾 Save All", command=self.save_data)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(button_frame, text="📤 Export Data", command=self.export_data)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        servers_frame = ttk.Frame(notebook)
        notebook.add(servers_frame, text="🖥️  Server Management")
        self.create_servers_tab(servers_frame)
        
        users_frame = ttk.Frame(notebook)
        notebook.add(users_frame, text="👥 User Management")
        self.create_users_tab(users_frame)
        
        terminal_frame = ttk.Frame(notebook)
        notebook.add(terminal_frame, text="⚙️  Server Management Terminal")
        self.create_terminal_tab(terminal_frame)
        
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📋 System Logs")
        self.create_logs_tab(logs_frame)
        
    def create_servers_tab(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header = ttk.Label(content_frame, text="Add New Server", font=("Segoe UI", 12, "bold"))
        header.pack(anchor=tk.W, pady=(0, 10))
        
        form_frame = ttk.LabelFrame(content_frame, text="Server Configuration", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(form_frame, text="Server Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.server_name_var, width=40).grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="IP Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.server_ip_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.server_ip_var, width=40).grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.server_port_var = tk.StringVar(value="8080")
        ttk.Entry(form_frame, textvariable=self.server_port_var, width=40).grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="OS Type:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.server_os_var = tk.StringVar()
        os_combo = ttk.Combobox(form_frame, textvariable=self.server_os_var, values=["Windows", "Linux", "macOS"], width=37)
        os_combo.grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.server_status_var = tk.StringVar()
        status_combo = ttk.Combobox(form_frame, textvariable=self.server_status_var, values=["Online", "Offline", "Maintenance"], width=37)
        status_combo.grid(row=4, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Description:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.server_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.server_desc_var, width=40).grid(row=5, column=1, sticky=tk.EW, padx=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15, sticky=tk.EW)
        
        ttk.Button(button_frame, text="➕ Add Server", command=self.add_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Clear Form", command=self.clear_server_form).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(content_frame, text="Server List", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.servers_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg="#2d2d2d", fg="#ffffff", height=15)
        self.servers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.servers_listbox.yview)
        
        self.servers_listbox.bind('<Double-Button-1>', self.edit_server)
        
        action_frame = ttk.Frame(content_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(action_frame, text="✏️  Edit Server", command=self.show_edit_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️  Delete Server", command=self.delete_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🔌 Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🔄 Refresh", command=self.refresh_servers_list).pack(side=tk.LEFT, padx=5)
        
        self.refresh_servers_list()
        
    def create_users_tab(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header = ttk.Label(content_frame, text="User Management", font=("Segoe UI", 12, "bold"))
        header.pack(anchor=tk.W, pady=(0, 10))
        
        form_frame = ttk.LabelFrame(content_frame, text="Add New User", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.user_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.user_name_var, width=40).grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.user_email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.user_email_var, width=40).grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.user_pass_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.user_pass_var, width=40, show="*").grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Role:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.user_role_var = tk.StringVar()
        role_combo = ttk.Combobox(form_frame, textvariable=self.user_role_var, values=["Admin", "User", "Guest", "Operator"], width=37)
        role_combo.grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Permissions:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.user_perms_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.user_perms_var, width=40).grid(row=4, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(form_frame, text="Status:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.user_status_var = tk.StringVar(value="Active")
        status_combo = ttk.Combobox(form_frame, textvariable=self.user_status_var, values=["Active", "Inactive", "Suspended"], width=37)
        status_combo.grid(row=5, column=1, sticky=tk.EW, padx=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15, sticky=tk.EW)
        
        ttk.Button(button_frame, text="➕ Add User", command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Clear Form", command=self.clear_user_form).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(content_frame, text="User List", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.users_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg="#2d2d2d", fg="#ffffff", height=15)
        self.users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.users_listbox.yview)
        
        action_frame = ttk.Frame(content_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(action_frame, text="✏️  Edit User", command=self.show_edit_user_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️  Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🔐 Reset Password", command=self.reset_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🔄 Refresh", command=self.refresh_users_list).pack(side=tk.LEFT, padx=5)
        
        self.refresh_users_list()
        
    def create_terminal_tab(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header = ttk.Label(content_frame, text="Server Management Terminal", font=("Segoe UI", 12, "bold"))
        header.pack(anchor=tk.W, pady=(0, 10))
        
        control_frame = ttk.LabelFrame(content_frame, text="Terminal Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Select Server:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.terminal_server_var = tk.StringVar()
        self.terminal_server_combo = ttk.Combobox(control_frame, textvariable=self.terminal_server_var, width=50)
        self.terminal_server_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(control_frame, text="Command:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.terminal_cmd_var = tk.StringVar()
        cmd_entry = ttk.Entry(control_frame, textvariable=self.terminal_cmd_var, width=50)
        cmd_entry.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        control_frame.columnconfigure(1, weight=1)
        
        cmd_button_frame = ttk.Frame(control_frame)
        cmd_button_frame.grid(row=2, column=0, columnspan=2, pady=15, sticky=tk.EW)
        
        ttk.Button(cmd_button_frame, text="▶️  Execute", command=self.execute_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(cmd_button_frame, text="⏹️  Stop", command=self.stop_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(cmd_button_frame, text="🗑️  Clear Output", command=self.clear_terminal).pack(side=tk.LEFT, padx=5)
        
        quick_cmd_frame = ttk.LabelFrame(control_frame, text="Quick Commands", padding=10)
        quick_cmd_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        quick_buttons = [
            ("📊 CPU Usage", "get_cpu_usage"),
            ("💾 Memory", "get_memory"),
            ("🔄 Restart", "restart_service"),
            ("🛑 Stop Service", "stop_service"),
            ("▶️  Start Service", "start_service"),
            ("📁 Disk Space", "get_disk_space"),
            ("📡 Network Stats", "get_network_stats"),
            ("🔍 Process List", "list_processes"),
        ]
        
        for i, (label, cmd) in enumerate(quick_buttons):
            ttk.Button(quick_cmd_frame, text=label, command=lambda c=cmd: self.execute_quick_cmd(c)).grid(row=i//4, column=i%4, padx=5, pady=5)
        
        ttk.Label(content_frame, text="Terminal Output", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        terminal_frame = ttk.Frame(content_frame)
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(terminal_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.terminal_output = tk.Text(terminal_frame, bg="#000000", fg="#00ff00", font=("Courier", 9), yscrollcommand=scrollbar.set, height=20)
        self.terminal_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.terminal_output.yview)
        
        self.update_terminal_servers()
        
    def create_logs_tab(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header = ttk.Label(content_frame, text="System Activity Logs", font=("Segoe UI", 12, "bold"))
        header.pack(anchor=tk.W, pady=(0, 10))
        
        filter_frame = ttk.LabelFrame(content_frame, text="Log Filters", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Type:").pack(side=tk.LEFT, padx=5)
        self.log_filter_var = tk.StringVar()
        log_filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_filter_var, values=["All", "Server", "User", "Terminal", "System"], width=20)
        log_filter_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="🔍 Apply Filter", command=self.apply_log_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="🗑️  Clear All Logs", command=self.clear_all_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="💾 Export Logs", command=self.export_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(content_frame, text="Log Entries", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        logs_frame = ttk.Frame(content_frame)
        logs_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(logs_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.logs_text = tk.Text(logs_frame, bg="#2d2d2d", fg="#ffffff", font=("Courier", 9), yscrollcommand=scrollbar.set, height=20)
        self.logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.logs_text.yview)
        
        self.refresh_logs()
        
    def add_server(self):
        name = self.server_name_var.get()
        ip = self.server_ip_var.get()
        port = self.server_port_var.get()
        os_type = self.server_os_var.get()
        status = self.server_status_var.get()
        desc = self.server_desc_var.get()
        
        if not name or not ip or not port or not os_type or not status:
            messagebox.showerror("Error", "Please fill all required fields")
            return
        
        server = {
            "name": name,
            "ip": ip,
            "port": port,
            "os": os_type,
            "status": status,
            "description": desc,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.servers.append(server)
        self.add_log("SERVER", f"Server '{name}' added successfully")
        messagebox.showinfo("Success", f"Server '{name}' added successfully")
        self.clear_server_form()
        self.refresh_servers_list()
        self.save_data()
        self.update_terminal_servers()
        
    def delete_server(self):
        selection = self.servers_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a server to delete")
            return
        
        index = selection[0]
        server = self.servers[index]
        
        if messagebox.askyesno("Confirm", f"Delete server '{server['name']}'?"):
            self.servers.pop(index)
            self.add_log("SERVER", f"Server '{server['name']}' deleted")
            self.refresh_servers_list()
            self.save_data()
            self.update_terminal_servers()
        
    def show_edit_dialog(self):
        selection = self.servers_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a server to edit")
            return
        
        index = selection[0]
        server = self.servers[index]
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Server - {server['name']}")
        edit_window.geometry("500x400")
        edit_window.configure(bg="#1e1e1e")
        
        frame = ttk.Frame(edit_window, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Server Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=server['name'])
        ttk.Entry(frame, textvariable=name_var, width=40).grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="IP Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ip_var = tk.StringVar(value=server['ip'])
        ttk.Entry(frame, textvariable=ip_var, width=40).grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        port_var = tk.StringVar(value=server['port'])
        ttk.Entry(frame, textvariable=port_var, width=40).grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="OS Type:").grid(row=3, column=0, sticky=tk.W, pady=5)
        os_var = tk.StringVar(value=server['os'])
        ttk.Combobox(frame, textvariable=os_var, values=["Windows", "Linux", "macOS"], width=37).grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=5)
        status_var = tk.StringVar(value=server['status'])
        ttk.Combobox(frame, textvariable=status_var, values=["Online", "Offline", "Maintenance"], width=37).grid(row=4, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Description:").grid(row=5, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=server['description'])
        ttk.Entry(frame, textvariable=desc_var, width=40).grid(row=5, column=1, sticky=tk.EW, padx=5)
        
        frame.columnconfigure(1, weight=1)
        
        def save_changes():
            self.servers[index]['name'] = name_var.get()
            self.servers[index]['ip'] = ip_var.get()
            self.servers[index]['port'] = port_var.get()
            self.servers[index]['os'] = os_var.get()
            self.servers[index]['status'] = status_var.get()
            self.servers[index]['description'] = desc_var.get()
            self.add_log("SERVER", f"Server '{name_var.get()}' updated")
            self.refresh_servers_list()
            self.save_data()
            self.update_terminal_servers()
            edit_window.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15, sticky=tk.EW)
        ttk.Button(button_frame, text="💾 Save", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
        
    def edit_server(self, event):
        self.show_edit_dialog()
        
    def test_connection(self):
        selection = self.servers_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a server")
            return
        
        server = self.servers[selection[0]]
        self.terminal_output.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] Testing connection to {server['name']} ({server['ip']}:{server['port']})...\n")
        self.add_log("SYSTEM", f"Connection test to {server['name']}")
        
        self.terminal_output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Connection successful\n")
        self.terminal_output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Response time: 45ms\n")
        self.terminal_output.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] Status: Online\n")
        self.terminal_output.see(tk.END)
        
    def refresh_servers_list(self):
        self.servers_listbox.delete(0, tk.END)
        for server in self.servers:
            status_icon = "🟢" if server['status'] == "Online" else "🔴" if server['status'] == "Offline" else "🟡"
            display_text = f"{status_icon} {server['name']} ({server['ip']}:{server['port']}) - {server['os']}"
            self.servers_listbox.insert(tk.END, display_text)
    
    def clear_server_form(self):
        self.server_name_var.set("")
        self.server_ip_var.set("")
        self.server_port_var.set("8080")
        self.server_os_var.set("")
        self.server_status_var.set("")
        self.server_desc_var.set("")
        
    def add_user(self):
        username = self.user_name_var.get()
        email = self.user_email_var.get()
        password = self.user_pass_var.get()
        role = self.user_role_var.get()
        permissions = self.user_perms_var.get()
        status = self.user_status_var.get()
        
        if not username or not email or not password or not role or not status:
            messagebox.showerror("Error", "Please fill all required fields")
            return
        
        user = {
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "permissions": permissions,
            "status": status,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": None
        }
        
        self.users.append(user)
        self.add_log("USER", f"User '{username}' created with role '{role}'")
        messagebox.showinfo("Success", f"User '{username}' added successfully")
        self.clear_user_form()
        self.refresh_users_list()
        self.save_data()
        
    def delete_user(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user to delete")
            return
        
        index = selection[0]
        user = self.users[index]
        
        if messagebox.askyesno("Confirm", f"Delete user '{user['username']}'?"):
            self.users.pop(index)
            self.add_log("USER", f"User '{user['username']}' deleted")
            self.refresh_users_list()
            self.save_data()
        
    def show_edit_user_dialog(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user to edit")
            return
        
        index = selection[0]
        user = self.users[index]
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit User - {user['username']}")
        edit_window.geometry("500x500")
        edit_window.configure(bg="#1e1e1e")
        
        frame = ttk.Frame(edit_window, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_var = tk.StringVar(value=user['username'])
        ttk.Entry(frame, textvariable=username_var, width=40).grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=user['email'])
        ttk.Entry(frame, textvariable=email_var, width=40).grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Role:").grid(row=2, column=0, sticky=tk.W, pady=5)
        role_var = tk.StringVar(value=user['role'])
        ttk.Combobox(frame, textvariable=role_var, values=["Admin", "User", "Guest", "Operator"], width=37).grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Permissions:").grid(row=3, column=0, sticky=tk.W, pady=5)
        perms_var = tk.StringVar(value=user['permissions'])
        ttk.Entry(frame, textvariable=perms_var, width=40).grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=5)
        status_var = tk.StringVar(value=user['status'])
        ttk.Combobox(frame, textvariable=status_var, values=["Active", "Inactive", "Suspended"], width=37).grid(row=4, column=1, sticky=tk.EW, padx=5)
        
        frame.columnconfigure(1, weight=1)
        
        def save_changes():
            self.users[index]['username'] = username_var.get()
            self.users[index]['email'] = email_var.get()
            self.users[index]['role'] = role_var.get()
            self.users[index]['permissions'] = perms_var.get()
            self.users[index]['status'] = status_var.get()
            self.add_log("USER", f"User '{username_var.get()}' updated")
            self.refresh_users_list()
            self.save_data()
            edit_window.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15, sticky=tk.EW)
        ttk.Button(button_frame, text="💾 Save", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
        
    def reset_password(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
        
        user = self.users[selection[0]]
        
        reset_window = tk.Toplevel(self.root)
        reset_window.title(f"Reset Password - {user['username']}")
        reset_window.geometry("400x200")
        reset_window.configure(bg="#1e1e1e")
        
        frame = ttk.Frame(reset_window, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"Reset password for: {user['username']}").pack(pady=10)
        ttk.Label(frame, text="New Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        new_pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=new_pass_var, show="*", width=40).grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(frame, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        confirm_pass_var = tk.StringVar()
        ttk.Entry(frame, textvariable=confirm_pass_var, show="*", width=40).grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        frame.columnconfigure(1, weight=1)
        
        def apply_reset():
            if new_pass_var.get() != confirm_pass_var.get():
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            self.users[selection[0]]['password'] = new_pass_var.get()
            self.add_log("USER", f"Password reset for user '{user['username']}'")
            messagebox.showinfo("Success", "Password reset successfully")
            self.save_data()
            reset_window.destroy()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15, sticky=tk.EW)
        ttk.Button(button_frame, text="🔄 Reset", command=apply_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancel", command=reset_window.destroy).pack(side=tk.LEFT, padx=5)
        
    def refresh_users_list(self):
        self.users_listbox.delete(0, tk.END)
        for user in self.users:
            status_icon = "🟢" if user['status'] == "Active" else "🔴" if user['status'] == "Inactive" else "🟠"
            role_colors = {"Admin": "👑", "User": "👤", "Guest": "👁️", "Operator": "⚙️"}
            role_icon = role_colors.get(user['role'], "•")
            display_text = f"{status_icon} {role_icon} {user['username']} ({user['email']}) - {user['role']}"
            self.users_listbox.insert(tk.END, display_text)
    
    def clear_user_form(self):
        self.user_name_var.set("")
        self.user_email_var.set("")
        self.user_pass_var.set("")
        self.user_role_var.set("")
        self.user_perms_var.set("")
        self.user_status_var.set("Active")
        
    def execute_command(self):
        server_name = self.terminal_server_var.get()
        command = self.terminal_cmd_var.get()
        
        if not server_name or not command:
            messagebox.showerror("Error", "Please select a server and enter a command")
            return
        
        self.terminal_output.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] $ {command}\n")
        self.add_log("TERMINAL", f"Command executed: {command}")
        
        outputs = {
            "ls": "file1.txt  file2.pdf  folder1/  folder2/",
            "pwd": "/home/user/server",
            "whoami": "admin",
            "date": datetime.now().strftime("%a %b %d %H:%M:%S %Y"),
            "uptime": "23 days, 5 hours, 42 minutes",
            "disk usage": "Disk   Used  Available  Use%\n/dev/sda1  450G  150G      60%\n/dev/sda2  200G  50G       80%",
        }
        
        output = next((v for k, v in outputs.items() if k in command.lower()), f"Executing: {command}\n✓ Command completed successfully")
        self.terminal_output.insert(tk.END, f"{output}\n")
        self.terminal_output.see(tk.END)
        
    def execute_quick_cmd(self, cmd):
        self.terminal_cmd_var.set(cmd)
        server_name = self.terminal_server_var.get()
        
        if not server_name:
            messagebox.showerror("Error", "Please select a server first")
            return
        
        self.terminal_output.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] Executing: {cmd}\n")
        self.add_log("TERMINAL", f"Quick command: {cmd}")
        
        cmd_outputs = {
            "get_cpu_usage": "CPU Usage: 45.2%\nUser: 28.3%\nSystem: 16.9%\nProcesses: 156",
            "get_memory": "Memory Usage:\nTotal: 16GB\nUsed: 9.5GB (59.4%)\nFree: 6.5GB\nBuffers: 512MB",
            "restart_service": "Restarting service...\n✓ Service restarted successfully",
            "stop_service": "Stopping service...\n✓ Service stopped",
            "start_service": "Starting service...\n✓ Service started",
            "get_disk_space": "Disk Space:\n/: 450GB total, 300GB used, 150GB free (67% usage)",
            "get_network_stats": "Network Statistics:\nBytes sent: 2.5GB\nBytes received: 1.8GB\nPackets sent: 1,245,632\nPackets received: 987,421",
            "list_processes": "PID    Name               Memory   CPU\n1234   nginx              242MB   1.2%\n5678   mysql              856MB   3.5%\n9012   python             128MB   0.8%",
        }
        
        output = cmd_outputs.get(cmd, f"Command {cmd} executed\n✓ Success")
        self.terminal_output.insert(tk.END, f"{output}\n")
        self.terminal_output.see(tk.END)
        
    def stop_command(self):
        self.terminal_output.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] Command stopped by user\n")
        
    def clear_terminal(self):
        self.terminal_output.delete(1.0, tk.END)
        
    def update_terminal_servers(self):
        server_names = [s['name'] for s in self.servers]
        self.terminal_server_combo['values'] = server_names
        
    def add_log(self, log_type, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": log_type,
            "message": message
        }
        self.logs.append(log_entry)
        
    def refresh_logs(self):
        self.logs_text.delete(1.0, tk.END)
        for log in self.logs:
            log_display = f"[{log['timestamp']}] {log['type']:10} | {log['message']}\n"
            self.logs_text.insert(tk.END, log_display)
        self.logs_text.see(tk.END)
        
    def apply_log_filter(self):
        filter_type = self.log_filter_var.get()
        self.logs_text.delete(1.0, tk.END)
        
        filtered_logs = self.logs if filter_type == "All" else [l for l in self.logs if l['type'] == filter_type]
        
        for log in filtered_logs:
            log_display = f"[{log['timestamp']}] {log['type']:10} | {log['message']}\n"
            self.logs_text.insert(tk.END, log_display)
            
    def clear_all_logs(self):
        if messagebox.askyesno("Confirm", "Clear all logs? This cannot be undone."):
            self.logs.clear()
            self.refresh_logs()
            self.save_data()
            
    def export_logs(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write("Timestamp,Type,Message\n")
                for log in self.logs:
                    f.write(f"{log['timestamp']},{log['type']},{log['message']}\n")
            messagebox.showinfo("Success", "Logs exported successfully")
            
    def save_data(self):
        data = {
            "servers": self.servers,
            "users": self.users,
            "logs": self.logs
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        self.add_log("SYSTEM", "Data saved to file")
        
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.servers = data.get("servers", [])
                    self.users = data.get("users", [])
                    self.logs = data.get("logs", [])
            except:
                pass
                
    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            data = {
                "servers": self.servers,
                "users": self.users,
                "logs": self.logs
            }
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Success", "Data exported successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerManagementApp(root)
    root.mainloop()