import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import hashlib
import os
import threading

class PCAntiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Anti - Professional Protection")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")

        # Fiktive Datenbank
        self.virus_db = ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]

        # Design-Elemente (UI)
        self.label_title = tk.Label(root, text="PC ANTI", font=("Arial", 24, "bold"), fg="#2c3e50", bg="#f0f0f0")
        self.label_title.pack(pady=20)

        self.status_label = tk.Label(root, text="System geschützt", font=("Arial", 12), fg="green", bg="#f0f0f0")
        self.status_label.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

        self.log_box = tk.Text(root, height=8, width=55, state="disabled", font=("Consolas", 9))
        self.log_box.pack(pady=10)

        self.scan_btn = tk.Button(root, text="Ordner scannen", command=self.start_scan_thread, 
                                  bg="#3498db", fg="white", font=("Arial", 10, "bold"), padx=20, pady=10)
        self.scan_btn.pack(pady=10)

    def log(self, message):
        """Schreibt Nachrichten in das Textfeld."""
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def calculate_hash(self, file_path):
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except:
            return None

    def start_scan_thread(self):
        """Startet den Scan in einem eigenen Thread, damit die App nicht einfriert."""
        folder = filedialog.askdirectory()
        if folder:
            self.scan_btn.config(state="disabled")
            self.status_label.config(text="Scan läuft...", fg="orange")
            threading.Thread(target=self.run_scan, args=(folder,), daemon=True).start()

    def run_scan(self, folder):
        files_to_scan = []
        for root, _, files in os.walk(folder):
            for f in files:
                files_to_scan.append(os.path.join(root, f))

        total = len(files_to_scan)
        found = 0

        for i, file_path in enumerate(files_to_scan):
            self.log(f"Prüfe: {os.path.basename(file_path)}")
            h = self.calculate_hash(file_path)
            if h in self.virus_db:
                self.log(f"🚨 GEFAHR: {file_path}")
                found += 1
            
            # Update Fortschrittsbalken
            percent = int(((i + 1) / total) * 100)
            self.progress["value"] = percent
            self.root.update_idletasks()

        self.scan_btn.config(state="normal")
        if found > 0:
            self.status_label.config(text=f"Warnung: {found} Bedrohungen!", fg="red")
            messagebox.showwarning("Scan beendet", f"Es wurden {found} Bedrohungen gefunden!")
        else:
            self.status_label.config(text="System sauber", fg="green")
            messagebox.showinfo("Scan beendet", "Keine Bedrohungen gefunden.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PCAntiApp(root)
    root.mainloop()