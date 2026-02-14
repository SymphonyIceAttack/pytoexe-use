import PyPDF2
import os
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import threading

class PDFSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Splitter Tool")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Set icon (optional - you can add an .ico file)
        # self.root.iconbitmap('icon.ico')
        
        # Variables
        self.input_pdf = StringVar()
        self.output_folder = StringVar()
        
        # Title
        title_label = Label(root, text="PDF Splitter", font=("Arial", 20, "bold"))
        title_label.pack(pady=10)
        
        # Subtitle
        subtitle_label = Label(root, text="Split multi-page PDF into individual pages", font=("Arial", 10))
        subtitle_label.pack()
        
        # Frame for file selection
        file_frame = LabelFrame(root, text="Select PDF File", padx=10, pady=10)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        self.file_entry = Entry(file_frame, textvariable=self.input_pdf, width=50)
        self.file_entry.pack(side=LEFT, padx=5)
        
        browse_btn = Button(file_frame, text="Browse", command=self.browse_file, bg="#4CAF50", fg="white")
        browse_btn.pack(side=LEFT)
        
        # Frame for output folder
        folder_frame = LabelFrame(root, text="Select Output Folder", padx=10, pady=10)
        folder_frame.pack(pady=10, padx=20, fill="x")
        
        self.folder_entry = Entry(folder_frame, textvariable=self.output_folder, width=50)
        self.folder_entry.pack(side=LEFT, padx=5)
        
        folder_btn = Button(folder_frame, text="Browse", command=self.browse_folder, bg="#2196F3", fg="white")
        folder_btn.pack(side=LEFT)
        
        # Split button
        self.split_btn = Button(root, text="Split PDF", command=self.start_split, 
                                bg="#FF5722", fg="white", font=("Arial", 12, "bold"),
                                height=2, width=20)
        self.split_btn.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.progress.pack(pady=10)
        
        # Status label
        self.status_label = Label(root, text="Ready to split", font=("Arial", 9))
        self.status_label.pack()
        
        # Information label
        self.info_label = Label(root, text="", font=("Arial", 9), fg="blue")
        self.info_label.pack()
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.input_pdf.set(filename)
            self.status_label.config(text=f"Selected: {os.path.basename(filename)}")
            
            # Check page count
            try:
                with open(filename, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pages = len(pdf_reader.pages)
                    self.info_label.config(text=f"PDF has {pages} pages")
            except:
                self.info_label.config(text="Could not read PDF")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
    
    def start_split(self):
        # Disable button during processing
        self.split_btn.config(state=DISABLED)
        
        # Start splitting in a separate thread
        thread = threading.Thread(target=self.split_pdf)
        thread.start()
    
    def split_pdf(self):
        input_file = self.input_pdf.get()
        output_dir = self.output_folder.get()
        
        if not input_file or not output_dir:
            messagebox.showerror("Error", "Please select both input file and output folder")
            self.split_btn.config(state=NORMAL)
            return
        
        if not input_file.lower().endswith('.pdf'):
            messagebox.showerror("Error", "Selected file is not a PDF")
            self.split_btn.config(state=NORMAL)
            return
        
        try:
            # Update status
            self.root.after(0, self.update_status, "Opening PDF...")
            
            with open(input_file, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # Setup progress bar
                self.root.after(0, self.setup_progress, total_pages)
                
                base_name = os.path.splitext(os.path.basename(input_file))[0]
                
                for page_num in range(total_pages):
                    pdf_writer = PyPDF2.PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                    
                    # Create output filename
                    output_filename = f"{output_dir}/{base_name}_Page_{page_num+1:03d}.pdf"
                    
                    # Save page
                    with open(output_filename, 'wb') as output_file:
                        pdf_writer.write(output_file)
                    
                    # Update progress
                    self.root.after(0, self.update_progress, page_num + 1, total_pages)
                
                # Complete
                self.root.after(0, self.split_complete, total_pages, output_dir)
                
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            self.root.after(0, self.enable_button)
    
    def setup_progress(self, total):
        self.progress['maximum'] = total
        self.progress['value'] = 0
        self.status_label.config(text=f"Splitting {total} pages...")
    
    def update_progress(self, current, total):
        self.progress['value'] = current
        self.status_label.config(text=f"Processing page {current} of {total}")
        self.root.update_idletasks()
    
    def update_status(self, text):
        self.status_label.config(text=text)
    
    def split_complete(self, total, output_dir):
        self.progress['value'] = 0
        messagebox.showinfo("Success", f"Successfully split {total} pages!\n\nSaved to:\n{output_dir}")
        self.status_label.config(text="Split complete!")
        
        # Ask to open folder
        if messagebox.askyesno("Open Folder", "Do you want to open the output folder?"):
            os.startfile(output_dir)
    
    def show_error(self, error):
        messagebox.showerror("Error", f"An error occurred:\n{error}")
        self.status_label.config(text="Error occurred")
    
    def enable_button(self):
        self.split_btn.config(state=NORMAL)

# Create the application
if __name__ == "__main__":
    root = Tk()
    app = PDFSplitterApp(root)
    root.mainloop()