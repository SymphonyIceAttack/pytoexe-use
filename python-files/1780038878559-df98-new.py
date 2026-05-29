
import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import mm

class PackagingProFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("Packaging Designer - Board Size & Actual Structure")
        self.root.geometry("1250x750")
        self.root.configure(bg="#121212")

        # Side Panel (Inputs)
        self.side = tk.Frame(root, bg="#1e1e1e", width=350, padx=35)
        self.side.pack(side="left", fill="y")

        tk.Label(self.side, text="BOX INPUTS", font=("Impact", 28), bg="#1e1e1e", fg="#00e676").pack(pady=40)
        self.entry_l = self.create_field("LENGTH (mm)")
        self.entry_w = self.create_field("WIDTH (mm)")
        self.entry_h = self.create_field("HIGHT (mm)")

        tk.Button(self.side, text="CALCULATE & VIEW", command=self.update_ui, bg="#00e676", font=("Arial", 10, "bold"), pady=12).pack(fill="x", pady=20)
        tk.Button(self.side, text="EXPORT 1:1 PDF", command=self.save_pdf, bg="#2196f3", fg="white", font=("Arial", 11, "bold"), pady=12).pack(fill="x")

        # Board Size පෙන්වන කොටස
        self.res_frame = tk.Frame(self.side, bg="#2d2d2d", padx=15, pady=15)
        self.res_frame.pack(fill="x", pady=30)
        self.lbl_bl = tk.Label(self.res_frame, text="Board Length: -", bg="#2d2d2d", fg="#00ff88", font=("Arial", 10, "bold"))
        self.lbl_bl.pack(anchor="w")
        self.lbl_bw = tk.Label(self.res_frame, text="Board Width: -", bg="#2d2d2d", fg="#00ff88", font=("Arial", 10, "bold"))
        self.lbl_bw.pack(anchor="w", pady=(5,0))

        # Canvas
        self.canvas = tk.Canvas(root, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(side="right", expand=True, fill="both", padx=30, pady=30)

    def create_field(self, label):
        tk.Label(self.side, text=label, bg="#1e1e1e", fg="#888888", font=("Arial", 9, "bold")).pack(anchor="w")
        e = tk.Entry(self.side, font=("Arial", 13), bg="#333333", fg="white", bd=0); e.pack(fill="x", pady=(5, 15), ipady=8)
        return e

    def get_data(self):
        try:
            l, w, h = float(self.entry_l.get()), float(self.entry_w.get()), float(self.entry_h.get())
            gf, gap, fh = 35, 6, (w / 2) + 0.25 # මූලාශ්‍රයේ දත්ත සහ සූත්‍රය [1]
            bl, bw = gf + (l * 2) + (w * 2), (fh * 2) + h
            return l, w, h, gf, gap, fh, bl, bw
        except: return None

    def update_ui(self):
        d = self.get_data()
        if not d: return
        l, w, h, gf, gap, fh, bl, bw = d
        
        # Board Size යාවත්කාලීන කිරීම
        self.lbl_bl.config(text=f"Board Length: {bl:.2f} mm")
        self.lbl_bw.config(text=f"Board Width: {bw:.2f} mm")

        self.canvas.delete("all")
        scale = min((self.canvas.winfo_width()-100)/bl, (self.canvas.winfo_height()-150)/bw)
        x, y = 50, self.canvas.winfo_height()/2
        ph, pfh, pgf = h * scale, fh * scale, gf * scale

        # 1. Glue Flap (Angle Cut) - කළු රේඛා [1]
        points = [x, y-ph/2+5, x+pgf, y-ph/2, x+pgf, y+ph/2, x, y+ph/2-5]
        self.canvas.create_polygon(points, outline="black", fill="", width=1)
        
        # 2. Main Panels සහ Flaps
        curr_x = x + pgf
        for i, val in enumerate([l, w, l, w]):
            pw = val * scale
            # මැද පැනල් - රතු රේඛා [1]
            self.canvas.create_rectangle(curr_x, y-ph/2, curr_x+pw, y+ph/2, outline="red", width=2)
            
            # පියන් (Flaps) - කළු රේඛා [1]
            if i == 3: # අවසාන පැනලයේ පියන සම්පූර්ණ පළලටම
                f_pw, f_x = pw, curr_x
            else:
                f_pw, f_x = pw - (gap * scale), curr_x + (gap/2 * scale)
            
            self.canvas.create_rectangle(f_x, y-ph/2-pfh, f_x+f_pw, y-ph/2, outline="black")
            self.canvas.create_rectangle(f_x, y+ph/2, f_x+f_pw, y+ph/2+pfh, outline="black")
            curr_x += pw

    def save_pdf(self):
        d = self.get_data()
        if not d: return
        l, w, h, gf, gap, fh, bl, bw = d
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not path: return

        m = 10 # Safety Margin for CorelDRAW
        c = pdf_canvas.Canvas(path, pagesize=((bl+m*2)*mm, (bw+m*2)*mm))
        sx, sy = m*mm, (m+fh)*mm

        # Glue Flap
        c.setStrokeColorRGB(0, 0, 0)
        p = c.beginPath()
        p.moveTo(sx, sy + 2*mm); p.lineTo(sx + gf*mm, sy); p.lineTo(sx + gf*mm, sy + h*mm)
        p.lineTo(sx, sy + h*mm - 2*mm); p.close(); c.drawPath(p)

        # Panels & Flaps
        curr_x = sx + (gf*mm)
        for i, val in enumerate([l, w, l, w]):
            c.setStrokeColorRGB(1, 0, 0) # Red
            c.rect(curr_x, sy, val*mm, h*mm)
            c.setStrokeColorRGB(0, 0, 0) # Black
            if i == 3: f_w, f_sx = val, curr_x
            else: f_w, f_sx = val - gap, curr_x + (gap/2 * mm)
            c.rect(f_sx, sy + h*mm, f_w*mm, fh*mm)
            c.rect(f_sx, sy - fh*mm, f_w*mm, fh*mm)
            curr_x += (val*mm)

        c.save()
        messagebox.showinfo("Success", f"PDF එක සූදානම්!\nBoard Size: {bl} x {bw} mm")

if __name__ == "__main__":
    root = tk.Tk()
    app = PackagingProFinal(root)
    root.mainloop()