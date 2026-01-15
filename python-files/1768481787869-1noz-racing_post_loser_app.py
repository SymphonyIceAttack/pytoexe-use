Python 3.14.2 (tags/v3.14.2:df79316, Dec  5 2025, 17:18:21) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> import tkinter as tk
... from tkinter import ttk, filedialog, messagebox
... import pandas as pd
... 
... def calculate_score(row):
...     score = 0
...     form = str(row['Form'])
...     if all(c in ['0', '9', '-'] for c in form):
...         score += 2
...     if float(row['Odds']) >= 20:
...         score += 2
...     if int(row['DaysSinceLastRun']) >= 120:
...         score += 1
...     if float(row['WinRate']) < 10:
...         score += 2
...     return score
... 
... root = tk.Tk()
... root.title("Loser Identifier")
... root.geometry("700x500")
... 
... columns = ('Horse', 'Form', 'Odds', 'DaysSinceLastRun', 'WinRate', 'Score', 'Result')
... tree = ttk.Treeview(root, columns=columns, show='headings')
... for col in columns:
...     tree.heading(col, text=col)
...     tree.column(col, width=90)
... tree.pack(fill='both', expand=True)
... 
... def load_csv():
...     file_path = filedialog.askopenfilename(filetypes=[('CSV Files', '*.csv')])
...     if not file_path:
...         return
...     try:
...         df = pd.read_csv(file_path)
...         df['Score'] = df.apply(calculate_score, axis=1)
...         df['Result'] = df['Score'].apply(lambda s: 'Likely Loser' if s >= 4 else 'Not Clear Loser')

        for i in tree.get_children():
            tree.delete(i)

        for _, row in df.iterrows():
            tree.insert('', 'end', values=(row['Horse'], row['Form'], row['Odds'],
                                           row['DaysSinceLastRun'], row['WinRate'],
                                           row['Score'], row['Result']))
        for child in tree.get_children():
            if tree.item(child)['values'][6] == 'Likely Loser':
                tree.item(child, tags=('loser',))
        tree.tag_configure('loser', background='salmon')
    except Exception as e:
        messagebox.showerror('Error', str(e))

def save_csv():
    file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV Files', '*.csv')])
    if not file_path:
        return
    try:
        rows = [tree.item(child)['values'] for child in tree.get_children()]
        df = pd.DataFrame(rows, columns=columns)
        df.to_csv(file_path, index=False)
        messagebox.showinfo('Saved', f'Results saved to {file_path}')
    except Exception as e:
        messagebox.showerror('Error', str(e))

frame = tk.Frame(root)
frame.pack(pady=10)
tk.Button(frame, text="Load CSV", command=load_csv).pack(side='left', padx=5)
tk.Button(frame, text="Save CSV", command=save_csv).pack(side='left', padx=5)

root.mainloop()
