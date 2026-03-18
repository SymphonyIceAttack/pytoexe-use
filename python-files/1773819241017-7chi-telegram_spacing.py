import pyperclip
import tkinter as tk
from tkinter import messagebox

# Grab text from clipboard
text = pyperclip.paste()

# Add double line spacing (change \n\n to \n\n\n for more spacing)
formatted_text = text.replace('\n', '\n\n')

# Copy back to clipboard
pyperclip.copy(formatted_text)

# Show confirmation popup
root = tk.Tk()
root.withdraw()
messagebox.showinfo("Done!", "Text formatted and copied to clipboard.\nPaste it in Telegram!")