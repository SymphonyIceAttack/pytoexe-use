import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def process_file(input_file, output_folder):
    try:
        data = pd.read_csv(input_file)
        final_rows = []

        for idx, row in data.iterrows():
            sku = row['SKU']
            pov = row['POverview']
            lines = [line.strip() for line in pov.splitlines() if line.strip()]

            if lines and lines[0].startswith("| Product Overview"):
                lines.pop(0)

            product_desc = lines[0] if lines else ""
            attr_dict = {'SKU': sku, 'Product Description': product_desc}

            for l in lines[1:]:
                if ":" in l:
                    key, value = l.split(":", 1)
                    attr_dict[key.strip()] = value.strip()
            final_rows.append(attr_dict)

        final_df = pd.DataFrame(final_rows)

        output_file = os.path.join(output_folder, "organized_data.xlsx")
        final_df.to_excel(output_file, index=False)
        messagebox.showinfo("Success", f"Organized Excel created:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI
root = tk.Tk()
root.title("SKU Organizer Tool")
root.geometry("400x200")

input_file_path = tk.StringVar()
output_folder_path = tk.StringVar()

def select_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files","*.csv")])
    if file_path:
        input_file_path.set(file_path)

def select_output_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        output_folder_path.set(folder_path)

def run_tool():
    if not input_file_path.get() or not output_folder_path.get():
        messagebox.showwarning("Missing Info", "Please select input file and output folder")
        return
    process_file(input_file_path.get(), output_folder_path.get())

tk.Label(root, text="SKU Organizer Tool", font=("Arial",14)).pack(pady=10)

tk.Button(root, text="Select Input CSV File", command=select_input_file).pack(pady=5)
tk.Entry(root, textvariable=input_file_path, width=50).pack()

tk.Button(root, text="Select Output Folder", command=select_output_folder).pack(pady=5)
tk.Entry(root, textvariable=output_folder_path, width=50).pack()

tk.Button(root, text="Run", command=run_tool, bg="green", fg="white").pack(pady=15)

root.mainloop()