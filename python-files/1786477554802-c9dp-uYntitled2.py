import tkinter as tk
from tkinter import ttk, messagebox
import math


# =========================
# تنظیمات اصلی
# =========================

root = tk.Tk()
root.title("ماشین حساب هندسی حرفه‌ای")
root.geometry("850x650")
root.resizable(False, False)
root.configure(bg="#151922")

history = []


# =========================
# توابع کمکی
# =========================

def clear_inputs():
    for entry in entries:
        entry.delete(0, tk.END)

    result_area.config(text="مساحت: ---")
    result_perimeter.config(text="محیط: ---")
    result_volume.config(text="حجم: ---")


def clear_history():
    history.clear()
    history_list.delete(0, tk.END)


def save_history():
    if not history:
        messagebox.showinfo("تاریخچه", "تاریخچه‌ای برای ذخیره وجود ندارد.")
        return

    try:
        with open("history.txt", "w", encoding="utf-8") as file:
            for item in history:
                file.write(item + "\n")

        messagebox.showinfo(
            "ذخیره شد",
            "تاریخچه با موفقیت در فایل history.txt ذخیره شد."
        )

    except Exception as error:
        messagebox.showerror("خطا", str(error))


def add_history(text):
    history.append(text)
    history_list.insert(tk.END, text)


# =========================
# تغییر نوع محاسبه
# =========================

def change_shape(event=None):

    for widget in input_frame.winfo_children():
        widget.destroy()

    entries.clear()

    shape = shape_var.get()

    fields = {

        "مربع": [
            "ضلع"
        ],

        "مستطیل": [
            "طول",
            "عرض"
        ],

        "مثلث": [
            "قاعده",
            "ارتفاع",
            "ضلع اول",
            "ضلع دوم"
        ],

        "دایره": [
            "شعاع"
        ],

        "ذوزنقه": [
            "قاعده اول",
            "قاعده دوم",
            "ارتفاع",
            "ضلع اول",
            "ضلع دوم"
        ],

        "مکعب": [
            "ضلع"
        ],

        "مکعب‌مستطیل": [
            "طول",
            "عرض",
            "ارتفاع"
        ]
    }

    for name in fields[shape]:

        row = tk.Frame(
            input_frame,
            bg="#202633"
        )

        row.pack(
            fill="x",
            padx=20,
            pady=5
        )

        label = tk.Label(
            row,
            text=name,
            width=15,
            anchor="e",
            bg="#202633",
            fg="white",
            font=("Tahoma", 11)
        )

        label.pack(side="right")

        entry = tk.Entry(
            row,
            justify="center",
            font=("Tahoma", 11),
            width=20
        )

        entry.pack(
            side="left",
            padx=15
        )

        entries.append(entry)


# =========================
# محاسبه
# =========================

def calculate():

    shape = shape_var.get()

    try:

        values = []

        for entry in entries:

            value = float(entry.get())

            if value <= 0:
                raise ValueError

            values.append(value)


        # -----------------
        # مربع
        # -----------------

        if shape == "مربع":

            side = values[0]

            area = side ** 2
            perimeter = 4 * side

            result_area.config(
                text=f"مساحت: {area:.2f}"
            )

            result_perimeter.config(
                text=f"محیط: {perimeter:.2f}"
            )

            result_volume.config(
                text="حجم: ---"
            )

            text = (
                f"مربع | ضلع={side} | "
                f"مساحت={area:.2f} | "
                f"محیط={perimeter:.2f}"
            )


        # -----------------
        # مستطیل
        # -----------------

        elif shape == "مستطیل":

            length = values[0]
            width = values[1]

            area = length * width
            perimeter = 2 * (length + width)

            result_area.config(
                text=f"مساحت: {area:.2f}"
            )

            result_perimeter.config(
                text=f"محیط: {perimeter:.2f}"
            )

            result_volume.config(
                text="حجم: ---"
            )

            text = (
                f"مستطیل | "
                f"طول={length} | عرض={width} | "
                f"مساحت={area:.2f} | "
                f"محیط={perimeter:.2f}"
            )


        # -----------------
        # مثلث
        # -----------------

        elif shape == "مثلث":

            base = values[0]
            height = values[1]
            side1 = values[2]
            side2 = values[3]

            area = (base * height) / 2
            perimeter = base + side1 + side2

            result_area.config(
                text=f"مساحت: {area:.2f}"
            )

            result_perimeter.config(
                text=f"محیط: {perimeter:.2f}"
            )

            result_volume.config(
                text="حجم: ---"
            )

            text = (
                f"مثلث | قاعده={base} | "
                f"ارتفاع={height} | "
                f"مساحت={area:.2f} | "
                f"محیط={perimeter:.2f}"
            )


        # -----------------
        # دایره
        # -----------------

        elif shape == "دایره":

            radius = values[0]

            area = math.pi * radius ** 2
            perimeter = 2 * math.pi * radius

            result_area.config(
                text=f"مساحت: {area:.2f}"
            )

            result_perimeter.config(
                text=f"محیط: {perimeter:.2f}"
            )

            result_volume.config(
                text="حجم: ---"
            )

            text = (
                f"دایره | شعاع={radius} | "
                f"مساحت={area:.2f} | "
                f"محیط={perimeter:.2f}"
            )


        # -----------------
        # ذوزنقه
        # -----------------

        elif shape == "ذوزنقه":

            base1 = values[0]
            base2 = values[1]
            height = values[2]
            side1 = values[3]
            side2 = values[4]

            area = ((base1 + base2) * height) / 2
            perimeter = base1 + base2 + side1 + side2

            result_area.config(
                text=f"مساحت: {area:.2f}"
            )

            result_perimeter.config(
                text=f"محیط: {perimeter:.2f}"
            )

            result_volume.config(
                text="حجم: ---"
            )

            text = (
                f"ذوزنقه | "
                f"مساحت={area:.2f} | "
                f"محیط={perimeter:.2f}"
            )


        # -----------------
        # مکعب
        # -----------------

        elif shape == "مکعب":

            side = values[0]

            area = 6 * side ** 2
            volume = side ** 3

            result_area.config(
                text=f"مساحت سطح: {area:.2f}"
            )

            result_perimeter.config(
                text="محیط: ---"
            )

            result_volume.config(
                text=f"حجم: {volume:.2f}"
            )

            text = (
                f"مکعب | ضلع={side} | "
                f"مساحت سطح={area:.2f} | "
                f"حجم={volume:.2f}"
            )


        # -----------------
        # مکعب مستطیل
        # -----------------

        elif shape == "مکعب‌مستطیل":

            length = values[0]
            width = values[1]
            height = values[2]

            area = 2 * (
                length * width +
                length * height +
                width * height
            )

            volume = length * width * height

            result_area.config(
                text=f"مساحت سطح: {area:.2f}"
            )

            result_perimeter.config(
                text="محیط: ---"
            )

            result_volume.config(
                text=f"حجم: {volume:.2f}"
            )

            text = (
                f"مکعب‌مستطیل | "
                f"حجم={volume:.2f} | "
                f"مساحت سطح={area:.2f}"
            )


        add_history(text)

    except (ValueError, IndexError):

        messagebox.showerror(
            "خطای ورودی",
            "لطفاً همه قسمت‌ها را با عدد مثبت پر کنید."
        )


# =========================
# عنوان
# =========================

title = tk.Label(
    root,
    text="ماشین حساب هندسی حرفه‌ای",
    font=("Tahoma", 24, "bold"),
    bg="#151922",
    fg="#00d9ff"
)

title.pack(pady=20)


subtitle = tk.Label(
    root,
    text="محاسبه مساحت، محیط و حجم",
    font=("Tahoma", 11),
    bg="#151922",
    fg="#aaaaaa"
)

subtitle.pack()


# =========================
# انتخاب شکل
# =========================

shape_var = tk.StringVar()
shape_var.set("مربع")

shape_box = ttk.Combobox(
    root,
    textvariable=shape_var,
    values=[
        "مربع",
        "مستطیل",
        "مثلث",
        "دایره",
        "ذوزنقه",
        "مکعب",
        "مکعب‌مستطیل"
    ],
    state="readonly",
    justify="center",
    font=("Tahoma", 11),
    width=25
)

shape_box.pack(pady=15)

shape_box.bind(
    "<<ComboboxSelected>>",
    change_shape
)


# =========================
# بخش اصلی
# =========================

main_frame = tk.Frame(
    root,
    bg="#151922"
)

main_frame.pack(
    fill="both",
    expand=True
)


# =========================
# بخش ورودی
# =========================

left_frame = tk.Frame(
    main_frame,
    bg="#202633"
)

left_frame.pack(
    side="left",
    padx=20,
    pady=10,
    fill="both",
    expand=True
)


input_title = tk.Label(
    left_frame,
    text="ورودی‌ها",
    font=("Tahoma", 14, "bold"),
    bg="#202633",
    fg="white"
)

input_title.pack(pady=10)


input_frame = tk.Frame(
    left_frame,
    bg="#202633"
)

input_frame.pack(
    fill="x"
)

entries = []

change_shape()


# =========================
# دکمه‌ها
# =========================

button_frame = tk.Frame(
    left_frame,
    bg="#202633"
)

button_frame.pack(pady=20)


calculate_button = tk.Button(
    button_frame,
    text="محاسبه",
    command=calculate,
    font=("Tahoma", 12, "bold"),
    bg="#00a8cc",
    fg="white",
    relief="flat",
    padx=35,
    pady=8
)

calculate_button.pack(
    side="left",
    padx=5
)


clear_button = tk.Button(
    button_frame,
    text="پاک کردن",
    command=clear_inputs,
    font=("Tahoma", 11),
    bg="#444b5a",
    fg="white",
    relief="flat",
    padx=20,
    pady=8
)

clear_button.pack(
    side="left",
    padx=5
)


# =========================
# نتایج
# =========================

result_area = tk.Label(
    left_frame,
    text="مساحت: ---",
    font=("Tahoma", 14, "bold"),
    bg="#202633",
    fg="#00ff9d"
)

result_area.pack(pady=5)


result_perimeter = tk.Label(
    left_frame,
    text="محیط: ---",
    font=("Tahoma", 14, "bold"),
    bg="#202633",
    fg="#00ff9d"
)

result_perimeter.pack(pady=5)


result_volume = tk.Label(
    left_frame,
    text="حجم: ---",
    font=("Tahoma", 14, "bold"),
    bg="#202633",
    fg="#00ff9d"
)

result_volume.pack(pady=5)


# =========================
# تاریخچه
# =========================

right_frame = tk.Frame(
    main_frame,
    bg="#202633"
)

right_frame.pack(
    side="right",
    padx=20,
    pady=10,
    fill="both",
    expand=True
)


history_title = tk.Label(
    right_frame,
    text="تاریخچه محاسبات",
    font=("Tahoma", 14, "bold"),
    bg="#202633",
    fg="white"
)

history_title.pack(pady=10)


history_list = tk.Listbox(
    right_frame,
    width=45,
    height=18,
    font=("Tahoma", 9),
    bg="#11151c",
    fg="white"
)

history_list.pack(
    padx=10,
    pady=5,
    fill="both",
    expand=True
)


history_buttons = tk.Frame(
    right_frame,
    bg="#202633"
)

history_buttons.pack(pady=10)


delete_history_button = tk.Button(
    history_buttons,
    text="پاک کردن تاریخچه",
    command=clear_history,
    bg="#444b5a",
    fg="white",
    relief="flat",
    padx=10,
    pady=6
)

delete_history_button.pack(
    side="left",
    padx=5
)


save_history_button = tk.Button(
    history_buttons,
    text="ذخیره تاریخچه",
    command=save_history,
    bg="#008c72",
    fg="white",
    relief="flat",
    padx=10,
    pady=6
)

save_history_button.pack(
    side="left",
    padx=5
)


# =========================
# خروج
# =========================

exit_button = tk.Button(
    root,
    text="خروج از برنامه",
    command=root.destroy,
    font=("Tahoma", 10),
    bg="#8f3030",
    fg="white",
    relief="flat",
    padx=30,
    pady=7
)

exit_button.pack(pady=12)


# =========================
# اجرای برنامه
# =========================

root.mainloop()