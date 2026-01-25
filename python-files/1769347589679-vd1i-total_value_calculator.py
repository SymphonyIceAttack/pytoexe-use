import tkinter as tk

PRICES = {
    "CAN": 387.83,
    "Sting": 424.74,
    "33CL": 424.74,
    "1L": 472.68,
    "2L": 757.50
}

def calculate():
    grand_total = 0
    for item in PRICES:
        try:
            qty = float(entries[item].get())
        except ValueError:
            qty = 0

        total = qty * PRICES[item]
        results[item].config(text=f"{total:.2f}")
        grand_total += total

    grand_total_label.config(text=f"{grand_total:.2f}")

root = tk.Tk()
root.title("Total Value Calculator")
root.geometry("420x320")
root.resizable(False, False)

entries = {}
results = {}

row = 0
for item, price in PRICES.items():
    tk.Label(root, text=f"{item} ({price})").grid(row=row, column=0, padx=10, pady=5, sticky="w")
    entry = tk.Entry(root, width=10)
    entry.grid(row=row, column=1)
    entries[item] = entry
    result = tk.Label(root, text="0.00", width=12)
    result.grid(row=row, column=2)
    results[item] = result
    row += 1

tk.Button(root, text="Calculate", command=calculate).grid(row=row, column=1, pady=10)

tk.Label(root, text="Grand Total:", font=("Arial", 10, "bold")).grid(row=row+1, column=0, pady=10)
grand_total_label = tk.Label(root, text="0.00", font=("Arial", 10, "bold"))
grand_total_label.grid(row=row+1, column=2)

root.mainloop()
