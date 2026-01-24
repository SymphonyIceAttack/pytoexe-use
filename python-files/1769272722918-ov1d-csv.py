def clean_csv(self):
    if not self.file_path:
        messagebox.showwarning("No File", "Please select a CSV file first.")
        return

    try:
        # Read original CSV
        cleaned_rows = []
        with open(self.file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                # Fix barcode column (strip spaces, force text)
                if "BARCODE" in row:
                    row["BARCODE"] = str(row["BARCODE"]).strip()
                cleaned_rows.append(row)

        # Ask where to save
        save_file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files","*.csv")],
            initialfile="cleaned_" + os.path.basename(self.file_path)
        )
        if not save_file:
            return

        # Ensure absolute path
        save_file = os.path.abspath(save_file)

        # Write cleaned CSV
        with open(save_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(cleaned_rows)

        messagebox.showinfo("Success", f"CSV cleaned and saved as:\n{save_file}")

    except PermissionError:
        messagebox.showerror("Error", "Cannot save file. Please close the file if it's open in Excel or choose another location.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
