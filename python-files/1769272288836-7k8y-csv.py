import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import os

APP_NAME = "Barcode Cleaner - DIP MANAGE Helper"

class BarcodeCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("500x250")
        
        tk.Label(root, text=APP_NAME, font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(root, text="Select CSV exported from Excel with barcode issues", font=("Arial", 10)).pack(pady=5)
        
        tk.Button(root, text="Select CSV File", width=20, command=self.select_file).pack(pady=10)
        tk.Button(root, text="Clean & Save CSV", width=20, command=self.clean_csv).pack(pady=10)
        
        self.file_path_label = tk.Label(root, text="No file selected", fg="blue")
        self.file_path_label.pack(pady=5)
        
        self.file_path = None

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("CSV Files","*.csv")])
        if file:
            self.file_path = file
            self.file_path_label.config(text=os.path.basename(file))

    def clean_csv(self):
        if not self.file_path:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return
        
        try:
            # Read original CSV
            cleaned_rows = []
            with open(self.file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    # Fix barcode column (strip spaces, force text)
                    if "BARCODE" in row:
                        row["BARCODE"] = str(row["BARCODE"]).strip()
                    cleaned_rows.append(row)
            
            # Ask where to save
            save_file = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                     filetypes=[("CSV Files","*.csv")],
                                                     initialfile="cleaned_" + os.path.basename(self.file_path))
            if not save_file:
                return
            
            # Write cleaned CSV
            with open(save_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(cleaned_rows)
            
            messagebox.showinfo("Success", f"CSV cleaned and saved as:\n{save_file}")
        
        except Exception as e:
            messagebox.showerror("Error", str(e))

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = BarcodeCleanerApp(root)
    root.mainloop()
