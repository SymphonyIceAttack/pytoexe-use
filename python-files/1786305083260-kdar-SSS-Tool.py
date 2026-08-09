import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import base64
import os
import secrets
import hashlib
import struct

# --- 1. Pure Python Shamir's Secret Sharing & Crypto ---

class ShamirSSS:
    """
    Implements Shamir's Secret Sharing over a finite field.
    """
    # Large Prime (256-bit) for security
    PRIME = 2**256 - 189

    @staticmethod
    def _extended_gcd(a, b):
        x, last_x = 0, 1
        y, last_y = 1, 0
        while b != 0:
            quot = a // b
            a, b = b, a % b
            x, last_x = last_x - quot * x, x
            y, last_y = last_y - quot * y, y
        return last_x, last_y

    @staticmethod
    def _divmod(num, den, p):
        """Compute num / den modulo p."""
        inv, _ = ShamirSSS._extended_gcd(den, p)
        return (num * inv) % p

    @staticmethod
    def split_secret(secret_int, n, k):
        """Splits an integer secret into N shares with threshold K."""
        if k > n:
            raise ValueError("K cannot be greater than N")
        
        # Coefficients: [secret, rand1, rand2, ..., rand(k-1)]
        coeffs = [secret_int] + [secrets.randbelow(ShamirSSS.PRIME) for _ in range(k - 1)]
        
        shares = []
        for x in range(1, n + 1):
            # Evaluate polynomial at x
            y = 0
            for coeff in reversed(coeffs):
                y = (y * x + coeff) % ShamirSSS.PRIME
            shares.append((x, y))
        return shares

    @staticmethod
    def recover_secret(shares):
        """Recovers the integer secret using Lagrange Interpolation."""
        if not shares:
            return 0
            
        k = len(shares)
        x_s, y_s = zip(*shares)
        secret = 0
        
        for i in range(k):
            numerator = 1
            denominator = 1
            for j in range(k):
                if i == j: 
                    continue
                numerator = (numerator * (0 - x_s[j])) % ShamirSSS.PRIME
                denominator = (denominator * (x_s[i] - x_s[j])) % ShamirSSS.PRIME
            
            lagrange = ShamirSSS._divmod(numerator, denominator, ShamirSSS.PRIME)
            term = (y_s[i] * lagrange) % ShamirSSS.PRIME
            secret = (secret + term) % ShamirSSS.PRIME
            
        return secret

class NativeCrypto:
    """
    Implements a Stream Cipher using SHA-256 (Standard Library Only).
    """
    # Encryption strength presets
    STRENGTH_PRESETS = {
        "Low (128-bit)": 16,
        "Medium (256-bit)": 32,
        "High (512-bit)": 64
    }

    @staticmethod
    def generate_keystream(seed_bytes, length):
        """
        Expands a seed into a keystream of 'length' bytes 
        using SHA-256 in counter mode.
        """
        keystream = bytearray()
        counter = 0
        while len(keystream) < length:
            # Hash(Seed + Counter)
            counter_bytes = struct.pack(">Q", counter) # 8-byte big endian counter
            block = hashlib.sha256(seed_bytes + counter_bytes).digest()
            keystream.extend(block)
            counter += 1
        return keystream[:length]

    @staticmethod
    def xor_bytes(data, key):
        """XORs two byte arrays."""
        return bytes(a ^ b for a, b in zip(data, key))

    @staticmethod
    def encrypt_payload(filename, file_bytes, n, k, seed_length=32):
        # 1. Create Payload (JSON -> Bytes)
        file_b64 = base64.b64encode(file_bytes).decode('ascii')
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        payload_dict = {
            "filename": filename,
            "content": file_b64,
            "hash": file_hash
        }
        payload_json = json.dumps(payload_dict).encode('utf-8')
        
        # 2. Generate Random Seed (The Secret) - variable length based on encryption strength
        seed = secrets.token_bytes(seed_length)
        
        # 3. Encrypt Payload using Stream Cipher
        keystream = NativeCrypto.generate_keystream(seed, len(payload_json))
        encrypted_data = NativeCrypto.xor_bytes(payload_json, keystream)
        
        # 4. Split the Seed using SSS
        seed_int = int.from_bytes(seed, 'big')
        shares = ShamirSSS.split_secret(seed_int, n, k)
        
        # 5. Prepare Output
        output_shares = []
        encrypted_b64 = base64.b64encode(encrypted_data).decode('ascii')
        
        # Unique ID for this encryption session to prevent mixing shares
        session_id = secrets.token_hex(4) 
        
        for x, y in shares:
            output_shares.append({
                "share_id": x,
                "share_val_hex": hex(y),
                "threshold": k,
                "session_id": session_id,
                "encrypted_data": encrypted_b64,
                "encryption_strength": seed_length
            })
            
        return output_shares

    @staticmethod
    def decrypt_payload(share_list):
        # 1. Extract Info
        first = share_list[0]
        k = first['threshold']
        enc_b64 = first['encrypted_data']
        seed_length = first.get('encryption_strength', 32)  # Default to 32 for backward compatibility
        encrypted_data = base64.b64decode(enc_b64)
        
        # 2. Recover Seed
        sss_points = []
        for s in share_list:
            sss_points.append((s['share_id'], int(s['share_val_hex'], 16)))
            
        recovered_int = ShamirSSS.recover_secret(sss_points)
        
        # Convert int back to bytes (variable length based on encryption strength)
        try:
            seed = recovered_int.to_bytes(seed_length, 'big')
        except OverflowError:
            raise ValueError("Recovered secret is invalid (math error).")
            
        # 3. Decrypt
        keystream = NativeCrypto.generate_keystream(seed, len(encrypted_data))
        decrypted_bytes = NativeCrypto.xor_bytes(encrypted_data, keystream)
        
        # 4. Parse & Verify
        try:
            payload = json.loads(decrypted_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError("Decryption failed. Key is incorrect or shares are corrupted.")

        # Check Hash
        try:
            content_bytes = base64.b64decode(payload['content'])
        except Exception:
            raise ValueError("Failed to decode file content from payload.")
            
        calc_hash = hashlib.sha256(content_bytes).hexdigest()
        
        if calc_hash != payload['hash']:
            raise ValueError("Integrity Check Failed: Content does not match original.")
            
        return payload['filename'], content_bytes

# --- 2. GUI Application ---

class SecretApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shamir's Secret Sharing Tool")
        self.root.geometry("800x700")
        
        style = ttk.Style()
        style.theme_use('alt')
        
        # Create menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # About menu
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="License", command=self.show_license)
        about_menu.add_command(label="Acknowledgements", command=self.show_acknowledgements)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.frame_decode = ttk.Frame(self.notebook)
        self.frame_encode = ttk.Frame(self.notebook)
        
        self.notebook.add(self.frame_decode, text='  Reveal Secret  ')
        self.notebook.add(self.frame_encode, text='  Create Shares  ')
        
        self.shares_store = []
        
        self.init_decode_tab()
        self.init_encode_tab()

    def show_license(self):
        """Display the license dialog."""
        license_window = tk.Toplevel(self.root)
        license_window.title("License - Shamir's Secret Sharing Tool")
        license_window.geometry("680x680")
        license_window.resizable(False, False)
        
        # Create a frame to hold content with proper padding
        content_frame = tk.Frame(license_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(content_frame, text="Shamir's Secret Sharing Tool", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 5))
        
        # Subtitle with copyright
        copyright_label = tk.Label(content_frame, text="Copyright © David Weijzen", font=("Arial", 10))
        copyright_label.pack(pady=(0, 15))
        
        # Text content using Label with 10pt font and wrapping
        license_text = ("This program is free software: you can redistribute it and/or modify it "
                       "under the terms of the GNU General Public License as published by the Free "
                       "Software Foundation, either version 3 of the License, or (at your option) "
                       "any later version.\n\n"
                       "This program is distributed in the hope that it will be useful, but "
                       "WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY "
                       "or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License "
                       "for more details.\n\n"
                       "You should have received a copy of the GNU General Public License along "
                       "with this program. If not, see <https://www.gnu.org/licenses/>")
        
        text_label = tk.Label(content_frame, text=license_text, font=("Arial", 10), justify=tk.LEFT, 
                             wraplength=640, relief=tk.FLAT, bg=content_frame.cget('bg'))
        text_label.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Close button
        close_btn = ttk.Button(license_window, text="Close", command=license_window.destroy)
        close_btn.pack(pady=(0, 15))

    def show_acknowledgements(self):
        """Display the acknowledgements dialog."""
        ack_window = tk.Toplevel(self.root)
        ack_window.title("Acknowledgements - Shamir's Secret Sharing Tool")
        ack_window.geometry("680x800")
        ack_window.resizable(False, False)
        
        # Create a frame to hold content with proper padding
        content_frame = tk.Frame(ack_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(content_frame, text="Acknowledgements", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Text content using Label with 10pt font and wrapping
        ack_text = ("This project utilizes the following Python standard libraries:\n\n"
                   "• tkinter - GUI framework for creating the user interface\n"
                   "• json - JSON encoder and decoder\n"
                   "• base64 - Base64 data encodings\n"
                   "• os - Miscellaneous operating system interfaces\n"
                   "• secrets - Generate cryptographically strong random numbers\n"
                   "• hashlib - Secure hashing and message digests\n"
                   "• struct - Interpret bytes as packed binary data\n"
                   "All standard library modules are part of Python and are licensed under the "
                   "Python Software Foundation License (PSFL), which is compatible with the "
                   "GNU General Public License v3.\n\n"
                   "  Copyright © 2001 Python Software Foundation; All Rights Reserved")
        
        text_label = tk.Label(content_frame, text=ack_text, font=("Arial", 10), justify=tk.LEFT, 
                             wraplength=640, relief=tk.FLAT, bg=content_frame.cget('bg'))
        text_label.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Close button
        close_btn = ttk.Button(ack_window, text="Close", command=ack_window.destroy)
        close_btn.pack(pady=(0, 15))

    # --- ENCODE TAB ---
    def init_encode_tab(self):
        f = self.frame_encode
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        
        # Create main container that fills the tab
        main_container = ttk.Frame(f)
        main_container.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        main_container.columnconfigure(0, weight=1)
        
        # File Section
        ttk.Label(main_container, text="Select File to Encode", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky='w', pady=(0, 10))
        
        self.var_filepath = tk.StringVar()
        file_row = ttk.Frame(main_container)
        file_row.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        file_row.columnconfigure(0, weight=1)
        
        entry = ttk.Entry(file_row, textvariable=self.var_filepath, state='readonly')
        entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        ttk.Button(file_row, text="Browse", command=self.browse_file).grid(row=0, column=1)
        
        # Config Section
        ttk.Label(main_container, text="Configuration", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky='w', pady=(0, 10))
        
        cfg_row = ttk.Frame(main_container)
        cfg_row.grid(row=3, column=0, sticky='w', pady=(0, 30))
        
        ttk.Label(cfg_row, text="Total Shares (N):").grid(row=0, column=0, padx=5, pady=5)
        self.var_n = tk.IntVar(value=5)
        sp_n = ttk.Spinbox(cfg_row, from_=2, to=20, textvariable=self.var_n, width=5, command=self.update_spinners)
        sp_n.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(cfg_row, text="Required to Reveal (K):").grid(row=0, column=2, padx=5, pady=5)
        self.var_k = tk.IntVar(value=3)
        self.sp_k = ttk.Spinbox(cfg_row, from_=2, to=5, textvariable=self.var_k, width=5)
        self.sp_k.grid(row=0, column=3, padx=5, pady=5)
        
        # Encryption Strength Row
        strength_row = ttk.Frame(main_container)
        strength_row.grid(row=4, column=0, sticky='w', pady=(0, 30))
        
        ttk.Label(strength_row, text="Encryption Strength:").grid(row=0, column=0, padx=5, pady=5)
        self.var_strength = tk.StringVar(value="Medium (256-bit)")
        self.strength_combo = ttk.Combobox(
            strength_row,
            textvariable=self.var_strength,
            values=list(NativeCrypto.STRENGTH_PRESETS.keys()),
            state='readonly',
            width=20
        )
        self.strength_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Separator
        ttk.Separator(main_container, orient='horizontal').grid(row=5, column=0, sticky='ew', pady=20)
        
        # Execute button
        self.btn_create = ttk.Button(main_container, text="GENERATE SHARES", command=self.do_encode)
        self.btn_create.grid(row=6, column=0, sticky='ew', ipady=10, pady=20)

    def update_spinners(self):
        n = self.var_n.get()
        self.sp_k.config(to=n)
        if self.var_k.get() > n:
            self.var_k.set(n)

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.var_filepath.set(path)

    def do_encode(self):
        path = self.var_filepath.get()
        if not path:
            messagebox.showwarning("Missing Info", "Please select a file.")
            return
            
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            n = self.var_n.get()
            k = self.var_k.get()
            fname = os.path.basename(path)
            
            # Get encryption strength
            strength_label = self.var_strength.get()
            seed_length = NativeCrypto.STRENGTH_PRESETS[strength_label]
            
            shares = NativeCrypto.encrypt_payload(fname, data, n, k, seed_length)
            
            save_dir = filedialog.askdirectory(title="Select Folder to Save Shares")
            if save_dir:
                base = os.path.splitext(fname)[0]
                for s in shares:
                    name = f"{base}_share_{s['share_id']}.share"
                    with open(os.path.join(save_dir, name), 'w') as f:
                        json.dump(s, f, indent=4)
                
                messagebox.showinfo("Success", f"Created {n} shares in:\n{save_dir}")
                self.var_filepath.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --- DECODE TAB ---
    def init_decode_tab(self):
        f = self.frame_decode
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        
        # Title
        lbl = ttk.Label(f, text="Load share files (.share) to unlock the secret", font=("Arial", 10))
        lbl.grid(row=0, column=0, pady=(20, 10), sticky='w', padx=20)
        
        # Listbox container with proper expansion
        list_container = ttk.Frame(f)
        list_container.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        self.lst_shares = tk.Listbox(list_container, width=70, height=12)
        self.lst_shares.grid(row=0, column=0, sticky='nsew')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.lst_shares.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.lst_shares.config(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_row = ttk.Frame(f)
        btn_row.grid(row=2, column=0, pady=10)
        ttk.Button(btn_row, text="+ Add Share File", command=self.add_share).pack(side='left', padx=5)
        ttk.Button(btn_row, text="Clear All", command=self.clear_shares).pack(side='left', padx=5)
        
        # Status Label
        self.lbl_status = ttk.Label(f, text="Status: Waiting for shares...", font=("Arial", 11, "bold"), foreground="#666")
        self.lbl_status.grid(row=3, column=0, pady=10, sticky='ew', padx=20)
        
        # Decode Button
        self.btn_decode = ttk.Button(f, text="REVEAL SECRET", command=self.do_decode, state='disabled')
        self.btn_decode.grid(row=4, column=0, pady=(0, 20), ipady=10, sticky='ew', padx=20)

    def add_share(self):
        paths = filedialog.askopenfilenames(filetypes=[("Shares", "*.share")])
        if not paths: return
        
        for p in paths:
            try:
                with open(p, 'r') as f:
                    data = json.load(f)
                
                # Validation
                req = ['share_id', 'threshold', 'session_id', 'encrypted_data']
                if not all(k in data for k in req):
                    print(f"Skipping {p}: Invalid format")
                    continue
                
                # Duplicate Check
                if any(s['share_id'] == data['share_id'] for s in self.shares_store):
                    continue
                
                # Consistency Check (Session ID)
                if self.shares_store:
                    if self.shares_store[0]['session_id'] != data['session_id']:
                        messagebox.showwarning("Mismatch", f"File '{os.path.basename(p)}' belongs to a different secret!")
                        continue
                        
                self.shares_store.append(data)
                self.lst_shares.insert(tk.END, os.path.basename(p))
                
            except Exception as e:
                pass
        
        self.update_status()

    def clear_shares(self):
        self.shares_store = []
        self.lst_shares.delete(0, tk.END)
        self.update_status()

    def update_status(self):
        if not self.shares_store:
            self.lbl_status.config(text="Status: Waiting for shares...", foreground="#666")
            self.btn_decode.config(state='disabled')
            return
            
        k = self.shares_store[0]['threshold']
        curr = len(self.shares_store)
        
        if curr >= k:
            self.lbl_status.config(text=f"Status: {curr}/{k} Shares collected. READY.", foreground="green")
            self.btn_decode.config(state='normal')
        else:
            needed = k - curr
            self.lbl_status.config(text=f"Status: Need {needed} more share(s) to reveal.", foreground="red")
            self.btn_decode.config(state='disabled')

    def do_decode(self):
        try:
            fname, content = NativeCrypto.decrypt_payload(self.shares_store)
            
            save_path = filedialog.asksaveasfilename(initialfile=fname, title="Save Revealed File")
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(content)
                messagebox.showinfo("Success", "File revealed and verified successfully!")
                self.clear_shares()
                
        except Exception as e:
            messagebox.showerror("Failed", f"Could not decode: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SecretApp(root)
    root.mainloop()
