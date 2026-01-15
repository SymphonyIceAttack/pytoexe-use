import tkinter as tk

def save_name():
    name = entry.get()
    with open("names.txt", "w", encoding="utf-8") as file:
        file.write(name)
    label_result.config(text="تم حفظ الاسم بنجاح ✅")

window = tk.Tk()
window.title("حفظ اسم")
window.geometry("300x200")

label = tk.Label(window, text="اكتب الاسم:")
label.pack(pady=5)

entry = tk.Entry(window, width=25)
entry.pack(pady=5)

button = tk.Button(window, text="حفظ", command=save_name)
button.pack(pady=10)

label_result = tk.Label(window, text="")
label_result.pack(pady=5)

window.mainloop()