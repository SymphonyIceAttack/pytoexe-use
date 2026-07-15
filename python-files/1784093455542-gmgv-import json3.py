import json
import zipfile
import tempfile
import shutil
import re
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


# =========================
# توابع کد اول (پاک کننده)
# =========================

def cleaner_remove_number(title):

    if not title:
        return ""

    title = title.strip()

    if re.fullmatch(r'\d+(?:\.\d+)+', title):
        return title.split(".")[-1]

    title = re.sub(
        r'^\d+(?:\.\d+)*\s*',
        '',
        title
    )

    return title.strip()


def cleaner_rebuild(topic):

    children = topic.get("children", {})
    attached = children.get("attached", [])

    for child in attached:

        text = cleaner_remove_number(
            child.get("title", "")
        )

        child["title"] = text

        cleaner_rebuild(child)


def process_cleaner(input_file, output_file):

    temp_dir = tempfile.mkdtemp()

    try:

        with zipfile.ZipFile(input_file, "r") as z:
            z.extractall(temp_dir)

        content_json = Path(temp_dir) / "content.json"

        if not content_json.exists():
            raise Exception(
                "این فایل از content.json پشتیبانی نمی‌کند."
            )

        with open(
            content_json,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        for sheet in data:

            root_topic = sheet.get("rootTopic")

            if root_topic:
                cleaner_rebuild(root_topic)

        with open(
            content_json,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        with zipfile.ZipFile(
            output_file,
            "w",
            zipfile.ZIP_DEFLATED
        ) as z:

            for file in Path(temp_dir).rglob("*"):

                if file.is_file():

                    z.write(
                        file,
                        file.relative_to(temp_dir)
                    )

    finally:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )


# =========================
# توابع کد دوم (شماره گذار)
# =========================

def renumber_remove_number(title):

    if not title:
        return ""

    return re.sub(
        r'^\d+(?:\.\d+)*\s+',
        '',
        title
    ).strip()


def renumber_rebuild(topic, parent_code):

    children = topic.get("children", {})
    attached = children.get("attached", [])

    for idx, child in enumerate(attached, start=1):

        text = renumber_remove_number(
            child.get("title", "")
        )

        code = f"{parent_code}.{idx}"

        child["title"] = f"{code} {text}"

        renumber_rebuild(
            child,
            code
        )


def process_renumber(input_file, output_file):

    temp_dir = tempfile.mkdtemp()

    try:

        with zipfile.ZipFile(input_file, "r") as z:
            z.extractall(temp_dir)

        content_json = Path(temp_dir) / "content.json"

        if not content_json.exists():
            raise Exception(
                "فایل content.json پیدا نشد."
            )

        with open(
            content_json,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        for sheet in data:

            root_topic = sheet.get("rootTopic")

            if not root_topic:
                continue

            try:

                refinery = root_topic

                process_units = (
                    refinery
                    .get("children", {})
                    .get("attached", [])[0]
                )

                vacuum_unit = (
                    process_units
                    .get("children", {})
                    .get("attached", [])[0]
                )

                systems = (
                    vacuum_unit
                    .get("children", {})
                    .get("attached", [])
                )

                for idx, system in enumerate(
                    systems,
                    start=1
                ):

                    text = renumber_remove_number(
                        system.get("title", "")
                    )

                    system["title"] = (
                        f"{idx} {text}"
                    )

                    renumber_rebuild(
                        system,
                        str(idx)
                    )

            except Exception as e:

                print(
                    "خطا در ساختار فایل:",
                    e
                )

        with open(
            content_json,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        with zipfile.ZipFile(
            output_file,
            "w",
            zipfile.ZIP_DEFLATED
        ) as z:

            for file in Path(temp_dir).rglob("*"):

                if file.is_file():

                    z.write(
                        file,
                        file.relative_to(temp_dir)
                    )

    finally:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )


# =========================
# رابط گرافیکی
# =========================

def run_cleaner():

    input_file = filedialog.askopenfilename(
        title="انتخاب فایل XMind",
        filetypes=[("XMind Files", "*.xmind")]
    )

    if not input_file:
        return

    output_file = filedialog.asksaveasfilename(
        title="ذخیره فایل خروجی",
        defaultextension=".xmind",
        initialfile="Cleaned.xmind",
        filetypes=[("XMind Files", "*.xmind")]
    )

    if not output_file:
        return

    try:

        process_cleaner(
            input_file,
            output_file
        )

        messagebox.showinfo(
            "موفق",
            "عملیات پاک‌سازی انجام شد."
        )

    except Exception as e:

        messagebox.showerror(
            "خطا",
            str(e)
        )


def run_renumber():

    input_file = filedialog.askopenfilename(
        title="انتخاب فایل XMind",
        filetypes=[("XMind Files", "*.xmind")]
    )

    if not input_file:
        return

    output_file = filedialog.asksaveasfilename(
        title="ذخیره فایل خروجی",
        defaultextension=".xmind",
        initialfile="Renumbered.xmind",
        filetypes=[("XMind Files", "*.xmind")]
    )

    if not output_file:
        return

    try:

        process_renumber(
            input_file,
            output_file
        )

        messagebox.showinfo(
            "موفق",
            "شماره‌گذاری انجام شد."
        )

    except Exception as e:

        messagebox.showerror(
            "خطا",
            str(e)
        )


# =========================
# ساخت پنجره
# =========================

root = tk.Tk()

root.title("XMind Tools")
root.geometry("400x250")
root.resizable(False, False)

title_label = tk.Label(
    root,
    text="ابزار مدیریت فایل‌های XMind",
    font=("Tahoma", 14, "bold")
)
title_label.pack(pady=20)

btn_clean = tk.Button(
    root,
    text="پاک کننده",
    width=20,
    height=2,
    font=("Tahoma", 11),
    command=run_cleaner
)
btn_clean.pack(pady=10)

btn_number = tk.Button(
    root,
    text="شماره گذار",
    width=20,
    height=2,
    font=("Tahoma", 11),
    command=run_renumber
)
btn_number.pack(pady=10)

developer_label = tk.Label(
    root,
    text="Developer : ebit navid",
    font=("Tahoma", 9)
)
developer_label.pack(side="bottom", pady=15)

root.mainloop()