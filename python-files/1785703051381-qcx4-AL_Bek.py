import tkinter as tk

# Create the main window
window = tk.Tk()
window.title("Simple Tkinter App")
window.geometry("300x200")

# Label
label = tk.Label(window, text="Hello, Tkinter!", font=("Arial", 14))
label.pack(pady=20)

# Button function
def change_text():
    label.config(text="Button Clicked!")

# Button
button = tk.Button(window, text="Click Me", command=change_text)
button.pack()

# Run the app
window.mainloop()