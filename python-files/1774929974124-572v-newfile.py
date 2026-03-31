import customtkinter as ctk

app = ctk.CTk()
app.geometry("300x200")

btn = ctk.CTkButton(app, text="Hello")
btn.pack(pady=20)

app.mainloop()