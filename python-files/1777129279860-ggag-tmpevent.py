import tkinter as tk
from tkinter import ttk
from datetime import datetime
import time

def to_unix_timestamp(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return int(time.mktime(dt.timetuple()))
    except:
        return None

def generate():
    meetup_time = meetup_entry.get()
    departure_time = departure_entry.get()

    city_meet = city_meet_entry.get()
    company_meet = company_meet_entry.get()

    city_dest = city_dest_entry.get()
    company_dest = company_dest_entry.get()

    distance = distance_entry.get()
    server = server_entry.get()
    dlc = dlc_var.get()

    meetup_unix = to_unix_timestamp(meetup_time)
    departure_unix = to_unix_timestamp(departure_time)

    if not meetup_unix or not departure_unix:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "❌ Falsches Datum Format! YYYY-MM-DD HH:MM")
        return

    meetup_loc = f"{city_meet} ({company_meet})" if company_meet else city_meet
    dest_loc = f"{city_dest} ({company_dest})" if company_dest else city_dest

    result = f"""🕐 Meetup Time: <t:{meetup_unix}:t>
🚚 Departure Time: <t:{departure_unix}:t>
📍 Meetup: {meetup_loc}
🏁 Destination: {dest_loc}
📏 Distance: {distance} km
🌍 DLC Req: {dlc}
🛰️ Server: {server}"""

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, result)

def copy():
    root.clipboard_clear()
    root.clipboard_append(output_text.get("1.0", tk.END))
    root.update()

root = tk.Tk()
root.title("RSL Event Generator")
root.geometry("900x600")

left = tk.Frame(root)
left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

right = tk.Frame(root)
right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

def add(label, row):
    tk.Label(left, text=label).grid(row=row, column=0, sticky="w")
    e = tk.Entry(left, width=40)
    e.grid(row=row, column=1)
    return e

meetup_entry = add("Meetup Time (YYYY-MM-DD HH:MM)", 0)
departure_entry = add("Departure Time (YYYY-MM-DD HH:MM)", 1)

city_meet_entry = add("Meetup City", 2)
company_meet_entry = add("Meetup Company", 3)

city_dest_entry = add("Destination City", 4)
company_dest_entry = add("Destination Company", 5)

distance_entry = add("Distance (km)", 6)
server_entry = add("Server", 7)

# --- DLC Dropdown ---
tk.Label(left, text="DLC Required").grid(row=8, column=0, sticky="w")
dlc_var = tk.StringVar()
dlc_dropdown = ttk.Combobox(left, textvariable=dlc_var, width=37)
dlc_dropdown["values"] = (
    "None",
    "Going East!",
    "Scandinavia",
    "Vive la France!",
    "Italia",
    "Beyond the Baltic Sea",
    "Road to the Black Sea",
    "Iberia",
    "West Balkans",
    "Greece",
    "Nordic Horizons",
    "ProMods"
)
dlc_dropdown.current(0)
dlc_dropdown.grid(row=8, column=1)

tk.Button(left, text="Generate", command=generate).grid(row=9, column=0, pady=10)

output_text = tk.Text(right, wrap="word")
output_text.pack(fill="both", expand=True)

tk.Button(right, text="Discord kopieren", command=copy).pack(pady=10)

root.mainloop()