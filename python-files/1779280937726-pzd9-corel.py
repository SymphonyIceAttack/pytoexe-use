import tkinter as tk
from tkinter import messagebox

def calculate():
    try:
      
        l = float(entry_l.get())
        w = float(entry_w.get())
        h = float(entry_h.get())
   
        glue_flap = 35 
       
        board_length = (l * 2) + (w * 2) + glue_flap
        
       
        flap_height = (w / 2) + 0.25
        board_width = (flap_height * 2) + h
        
       
        lbl_res_l.config(text=f"Board Length: {board_length:.2f} mm", fg="#ffffff")
        lbl_res_w.config(text=f"Board Width: {board_width:.2f} mm", fg="#ffffff")
        lbl_flap.config(text=f"Flap Height: {flap_height:.2f} mm", fg="#a0a0a0")
        
    except ValueError:
        messagebox.showerror("වැරදියි", "කරුණාකර අංක පමණක් නිවැරදිව ඇතුළත් කරන්න.")


root = tk.Tk()
root.title("KSPA-BOX CUL")
root.geometry("400x500")
root.configure(bg="#2c3e50") 

# Header
header = tk.Label(root, text="BOARD CALCULATOR", font=("Helvetica", 18, "bold"), bg="#2c3e50", fg="#ecf0f1")
header.pack(pady=20)

# Input Style Helper
def create_label_entry(text):
    lbl = tk.Label(root, text=text, font=("Helvetica", 10), bg="#2c3e50", fg="#bdc3c7")
    lbl.pack()
    entry = tk.Entry(root, font=("Helvetica", 12), justify='center', bd=0, highlightthickness=2)
    entry.config(highlightbackground="#34495e", highlightcolor="#3498db")
    entry.pack(pady=5, ipady=3)
    return entry

entry_l = create_label_entry("Box Length (mm)")
entry_w = create_label_entry("Box Width (mm)")
entry_h = create_label_entry("Box Height (mm)")

# Calculate Button
btn = tk.Button(root, text="CALCULATE NOW", command=calculate, font=("Helvetica", 11, "bold"), 
                bg="#3498db", fg="white", bd=0, cursor="hand2", activebackground="#2980b9")
btn.pack(pady=25, ipadx=20, ipady=5)

# Results Section
result_frame = tk.Frame(root, bg="#34495e", padx=20, pady=20)
result_frame.pack(fill="x", padx=30)

lbl_res_l = tk.Label(result_frame, text="Board Length: -", font=("Helvetica", 12, "bold"), bg="#34495e", fg="#95a5a6")
lbl_res_l.pack()

lbl_res_w = tk.Label(result_frame, text="Board Width: -", font =("Helvetica", 12, "bold"), bg="#34495e", fg="#95a5a6")
lbl_res_w.pack(pady=5)

lbl_flap = tk.Label(result_frame, text="Flap Height: -", font=("Helvetica", 10), bg="#34495e", fg="#7f8c8d")
lbl_flap.pack()

# Footer
footer = tk.Label(root, text="Glue Flap: 35mm Included"     " By Malith Balasooriya", font=("Helvetica", 8, "italic"), bg="#2c3e50", fg="#7f8c8d")
footer.pack(side="bottom", pady=10)

root.mainloop()