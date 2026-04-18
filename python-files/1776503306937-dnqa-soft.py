import requests
import tkinter as tk
from tkinter import filedialog, messagebox

# 🔗 apna server URL yaha daalo
UPLOAD_URL = "https://apnadigital.byethost13.com/upload.php"
SECRET_KEY = "12345"

def upload_file():
    file_path = filedialog.askopenfilename()

    if not file_path:
        return

    try:
        files = {'file': open(file_path, 'rb')}
        data = {'key': SECRET_KEY}

        res = requests.post(UPLOAD_URL, files=files, data=data)

        messagebox.showinfo("Server Response", res.text)

    except Exception as e:
        messagebox.showerror("Error", str(e))


# GUI
root = tk.Tk()
root.title("File Uploader")
root.geometry("300x150")

btn = tk.Button(root, text="Select File & Upload", command=upload_file, height=2)
btn.pack(pady=40)

root.mainloop()