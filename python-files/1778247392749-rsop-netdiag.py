import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import zipfile
import socket
import os


COMMANDS = {
    "DNS Lookup": lambda host, port: f"nslookup {host}",
    "TCP Port Check": lambda host, port: f"powershell Test-NetConnection {host} -Port {port}",
    "Ping IPv4": lambda host, port: f"ping -4 {host}",
    "Ping IPv6": lambda host, port: f"ping -6 {host}",
    "Trace Route IPv4": lambda host, port: f"tracert -4 {host}",
    "Trace Route IPv6": lambda host, port: f"tracert -6 {host}",
    "IP Config": lambda host, port: "ipconfig /all",
    "Routing Table": lambda host, port: "route print",
    "ARP Table": lambda host, port: "arp -a",
    "Netstat": lambda host, port: "netstat -ano",
}


class NetDiagApp:

    def __init__(self, root):

        self.root = root
        self.root.title("NETDIAG")
        self.root.geometry("900x650")
        self.root.configure(bg="#101312")

        self.create_ui()

    def create_ui(self):

        top = tk.Frame(self.root, bg="#101312")
        top.pack(fill="x", padx=20, pady=20)

        title = tk.Label(
            top,
            text="NETDIAG",
            fg="#00ff88",
            bg="#101312",
            font=("Consolas", 24, "bold")
        )
        title.pack(anchor="w")

        form = tk.Frame(self.root, bg="#101312")
        form.pack(fill="x", padx=20)

        tk.Label(
            form,
            text="HOST / IP",
            fg="#cccccc",
            bg="#101312",
            font=("Consolas", 11)
        ).pack(anchor="w")

        self.host_entry = tk.Entry(
            form,
            font=("Consolas", 12),
            bg="#1b1f1d",
            fg="#ffffff",
            insertbackground="white"
        )
        self.host_entry.pack(fill="x", pady=(4, 12))
        self.host_entry.insert(0, "example.com")
    root.mainloop()