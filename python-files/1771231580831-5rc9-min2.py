import tkinter as tk
from datetime import datetime, timedelta

def generate_table():
    output.delete("1.0", tk.END)

    start_time_str = entry_time.get().strip()

    try:
        current = datetime.strptime(start_time_str, "%H:%M:%S")
    except ValueError:
        output.insert(tk.END, "Invalid time format. Use HH:MM:SS")
        return

    end_time = current + timedelta(hours=1)

    while current < end_time:
        t0 = current.strftime("%H:%M:%S")
        t1 = (current + timedelta(seconds=30)).strftime("%H:%M:%S")
        t2 = (current + timedelta(seconds=60)).strftime("%H:%M:%S")

        output.insert(tk.END, f"{t0}\n")
        output.insert(tk.END, f"{t1} prepare trade\n")
        output.insert(tk.END, f"{t2} go trade\n\n")
        output.insert(tk.END, "New trade\n\n")

        current += timedelta(seconds=30)

# -------- UI --------
root = tk.Tk()
root.title("Trade Table Generator")
root.geometry("520x600")

tk.Label(root, text="Start Time (HH:MM:SS)").pack(pady=5)

entry_time = tk.Entry(root, justify="center", font=("Arial", 12))
entry_time.pack(pady=5)
entry_time.insert(0, "01:00:00")

tk.Button(root, text="Generate Table", command=generate_table).pack(pady=10)

output = tk.Text(root, font=("Consolas", 11))
output.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()
