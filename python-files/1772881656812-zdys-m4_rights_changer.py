import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

class M4RightsChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("M4 Rights Changer Tool")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))

        # Main Frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # UI Elements
        self.label_title = ttk.Label(main_frame, text="M4 Rights Changer Tool", style="Title.TLabel")
        self.label_title.pack(pady=(0, 20))

        self.btn_select = ttk.Button(main_frame, text="Select Folder", command=self.select_folder)
        self.btn_select.pack(pady=10)

        self.label_path = ttk.Label(main_frame, text="No folder selected", wraplength=460, foreground="gray")
        self.label_path.pack(pady=5)

        self.btn_start = ttk.Button(main_frame, text="Start Processing", command=self.start_processing_thread, state=tk.DISABLED)
        self.btn_start.pack(pady=10)

        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=20)

        self.label_status = ttk.Label(main_frame, text="Ready", font=("Segoe UI", 9))
        self.label_status.pack(pady=5)
        
        self.stats_label = ttk.Label(main_frame, text="", font=("Segoe UI", 10, "bold"))
        self.stats_label.pack(pady=10)

        self.selected_path = ""
        self.extensions = ['.lua', '.js', '.json', '.cfg', '.html', '.css', '.txt', '.xml']
        self.copyright_text = "Copyright © M4 STORE\nDeveloper: Thamer Almutairy\nAll Rights Reserved"
        self.keywords = ['author', 'developer', 'created by', 'copyright', 'credits', 'discord']

    def get_comment_format(self, file_extension):
        if file_extension in ['.js', '.css', '.json']:
            return "/*\n * {}\n */"
        elif file_extension == '.lua':
            return "--[[\n{}\n--]]"
        elif file_extension in ['.xml', '.html']:
            return "<!--\n{}\n-->"
        else: # .txt, .cfg, etc.
            return "# {}\n#"

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.selected_path = path
            self.label_path.config(text=f"Selected: {self.selected_path}", foreground="black")
            self.btn_start.config(state=tk.NORMAL)
            self.label_status.config(text="Ready to process")
            self.stats_label.config(text="")
            self.progress['value'] = 0

    def start_processing_thread(self):
        self.btn_start.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.label_status.config(text="Scanning files...")
        threading.Thread(target=self.process_files, daemon=True).start()

    def process_files(self):
        all_files = []
        for root, _, files in os.walk(self.selected_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.extensions):
                    all_files.append(os.path.join(root, file))

        total_files = len(all_files)
        modified_files = 0

        if total_files == 0:
            self.root.after(0, lambda: messagebox.showinfo("No Files Found", "No supported files found in the selected directory."))
            self.root.after(0, self.reset_ui)
            return

        self.progress['maximum'] = total_files

        for i, file_path in enumerate(all_files):
            self.root.after(0, lambda i=i, total=total_files: self.label_status.config(text=f"Processing: {i+1}/{total}"))
            file_extension = os.path.splitext(file_path)[1].lower()
            
            comment_format = self.get_comment_format(file_extension)
            copyright_block = comment_format.format(self.copyright_text.replace('\n', '\n * '))

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Step 1: Remove lines containing keywords
                lines = content.splitlines()
                new_lines = []
                for line in lines:
                    if not any(keyword.lower() in line.lower() for keyword in self.keywords):
                        new_lines.append(line)
                
                # Step 2: Add copyright at the top
                final_content = copyright_block + "\n\n" + "\n".join(new_lines)

                # Write back if changed
                with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(final_content)
                
                modified_files += 1

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

            self.root.after(0, lambda i=i: self.progress.config(value=i + 1))

        self.root.after(0, lambda: self.show_completion(total_files, modified_files))

    def show_completion(self, total, modified):
        messagebox.showinfo("Done", f"Scan Complete!\nTotal Scanned: {total}\nTotal Modified: {modified}")
        self.stats_label.config(text=f"Total Scanned: {total} | Modified: {modified}")
        self.reset_ui()

    def reset_ui(self):
        self.btn_start.config(state=tk.NORMAL)
        self.label_status.config(text="Ready")

if __name__ == "__main__":
    root = tk.Tk()
    app = M4RightsChangerApp(root)
    root.mainloop()
