import tkinter as tk
from tkinter import messagebox
import requests
import csv
import os
from datetime import datetime

WEBHOOK_URL = "https://discord.com/api/webhooks/1469293960110542992/8rN1y2FxHL__pabXKEMuxhPe1vYDyF0yMqcyG2rxGRU7kwft_bPf6p0mdF__KPr4GO8C"  # Optional (leave empty "" to disable)


class LegitGiveawayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Roblox Giveaway Entry")
        self.root.geometry("500x520")
        self.root.configure(bg="#1e1f26")

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self.root,
            text="ROBLOX GIVEAWAY ENTRY",
            bg="#1e1f26",
            fg="#f0b323",
            font=("Arial", 18, "bold")
        ).pack(pady=20)

        tk.Label(
            self.root,
            text="This is a MANUAL giveaway.\nNo Robux is generated automatically.",
            bg="#1e1f26",
            fg="white",
            font=("Arial", 11),
            justify="center"
        ).pack(pady=10)

        # Username
        tk.Label(self.root, text="Roblox Username", bg="#1e1f26", fg="white").pack(pady=(20, 5))
        self.username_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.username_var, width=30).pack()

        # Discord
        tk.Label(self.root, text="Discord Username", bg="#1e1f26", fg="white").pack(pady=(20, 5))
        self.discord_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.discord_var, width=30).pack()

        # Consent checkbox
        self.consent_var = tk.BooleanVar()
        tk.Checkbutton(
            self.root,
            text="I understand this is manually reviewed and\nmy entry will be stored.",
            variable=self.consent_var,
            bg="#1e1f26",
            fg="white",
            selectcolor="#1e1f26",
            activebackground="#1e1f26"
        ).pack(pady=20)

        tk.Button(
            self.root,
            text="Submit Entry",
            bg="#f0b323",
            fg="black",
            font=("Arial", 14, "bold"),
            command=self.submit_entry
        ).pack(pady=20)

    def submit_entry(self):
        username = self.username_var.get().strip()
        discord = self.discord_var.get().strip()

        if not username or not discord:
            messagebox.showwarning("Missing Info", "Please fill all fields.")
            return

        if not self.consent_var.get():
            messagebox.showwarning("Consent Required", "You must agree before submitting.")
            return

        # Save locally
        file_exists = os.path.isfile("entries.csv")

        with open("entries.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Roblox Username", "Discord Username"])
            writer.writerow([datetime.now(), username, discord])

        # Optional webhook notification
        if WEBHOOK_URL:
            try:
                requests.post(WEBHOOK_URL, json={
                    "content": f"🎉 New Giveaway Entry\nRoblox: {username}\nDiscord: {discord}"
                })
            except:
                pass

        messagebox.showinfo("Success", "Your entry has been submitted!")

        self.username_var.set("")
        self.discord_var.set("")
        self.consent_var.set(False)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LegitGiveawayApp()
    app.run()
