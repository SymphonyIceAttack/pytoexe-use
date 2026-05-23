import tkinter as tk
from tkinter import messagebox, filedialog
import os
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import mm

class PackagingWeightFix:
    def __init__(self, root):
        self.root = root
        self.root.title("Packaging Designer - Weight & Board Size Display")
        self.root.geometry("1300x850")
        self.root.configure(bg="#121212")

        # Side Panel
        self.side = tk.Frame(root, bg="#1e1e1e", width=350, padx=35)
        self.side.pack(side="left", fill="y")

        tk.Label(self.side, text="BOX INPUTS", font=("Impact", 28), bg="#1e1e1e", fg="#00e676").pack(pady=40)
        self.entry_l = self.create_field("LENGTH (mm)")
        self.entry_w = self.create_field("WIDTH (mm)")
        self.entry_h = self.create_field("HIGHT (mm)")
        self.entry_gsm = self.create_field("PAPER GSM") # බර සෙවීමට මෙය අත්‍යවශ්‍යයි

        # Calculate Button
        tk.Button(self.side, text="CALCULATE", command=self.update_ui, bg="#00e676", font=("Arial", 10, "bold"), pady=12).pack(fill="x", pady=20)
        tk.Button(self.side, text="EXPORT 1:1 PDF", command=self.save_pdf, bg="#2196f3", fg="white", font=("Arial", 11, "bold"), pady=12).pack(fill="x")

        # Results Display (මෙම කොටසින් බර පෙන්වයි)
        self.res_frame = tk.Frame(self.side, bg="#2d2d2d", padx=15, pady=15)
        self.res_frame.pack(fill="x", pady=30)
        self.lbl_bl = tk.Label(self.res_frame, text="Board Size: -", bg="#2d2d2d", fg="#00ff88", font=("Arial", 10, "bold"))
        self.lbl_bl.pack(anchor="w")
        self.lbl_weight = tk.Label(self.res_frame, text="Carton Weight: - g", bg="#2d2d2d", fg="#ffeb3b", font=("Arial", 11, "bold"))
        self.lbl_weight.pack(anchor="w", pady=(10,0))

        self.canvas = tk.Canvas(root, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(side="right", expand=True, fill="both", padx=30, pady=30)

    def create_field(self, label):
        tk.Label(self.side, text=label, bg="#1e1e1e", fg="#888888", font=("Arial", 9, "bold")).pack(anchor="w")
        e = tk.Entry(self.side, font=("Arial", 13), bg="#333333", fg="white", bd=0); e.pack(fill="x", pady=(5, 10), ipady=8); return e

    def get_data(self):
        try:
            l, w, h = float(self.entry_l.get()), float(self.entry_w.get()), float(self.entry_h.get())
            gsm = float(self.entry_gsm.get() or 0)
            gf, fh = 35, (w / 2) + 2.5 # [2] Screenshot (104) specifications
            bl, bw = gf + (l * 2) + (w * 2), (fh * 2) + h
            # බර ගණනය කිරීමේ සූත්‍රය
            weight = (bl * bw * gsm) / 1000000 
            return l, w, h, gf, fh, bl, bw, weight
        except: return None

    def update_ui(self):
        d = self.get_data()
        if not d: return
        l, w, h, gf, fh, bl, bw, weight = d
        # UI එක යාවත්කාලීන කිරීම
        self.lbl_bl.config(text=f"Board: {bl:.1f} x {bw:.1f} mm")
        self.lbl_weight.config(text=f"Carton Weight: {weight:.2f} g")
        
        self.canvas.delete("all")
        scale = min((self.canvas.winfo_width()-80)/bl, (self.canvas.winfo_height()-80)/bw)
        x_off = (self.canvas.winfo_width() - bl * scale) / 2
        y_off = (self.canvas.winfo_height() - bw * scale) / 2
        ph, pfh, pgf = h * scale, fh * scale, gf * scale

        # Glue Flap
        self.canvas.create_polygon([x_off, y_off+pfh+5, x_off+pgf, y_off+pfh, x_off+pgf, y_off+pfh+ph, x_off, y_off+pfh+ph-5], outline="black", width=1)
        
        curr_x = x_off + pgf
        for i, val in enumerate([l, w, l, w]):
            pw = val * scale
            self.canvas.create_rectangle(curr_x, y_off+pfh, curr_x+pw, y_off+pfh+ph, outline="red", width=1)
            f_x = curr_x + (3 * scale); f_pw = (pw - 3 * scale) if i == 3 else (pw - 6 * scale)
            self.canvas.create_rectangle(f_x, y_off, f_x+f_pw, y_off+pfh, outline="black")
            self.canvas.create_rectangle(f_x, y_off+pfh+ph, f_x+f_pw, y_off+bw*scale, outline="black")
            curr_x += pw
        self.canvas.create_line(curr_x, y_off+pfh, curr_x, y_off+pfh+ph, fill="black")

    def save_pdf(self):
        d = self.get_data()
        if not d: return
        l, w, h, gf, fh, bl, bw, weight = d
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not path: return
        c = pdf_canvas.Canvas(path, pagesize=((bl+20)*mm, (bw+20)*mm))
        c.setLineWidth(0.2 * mm); sx, sy = 10*mm, (10+fh)*mm
        c.setStrokeColorRGB(1, 0, 0)
        curr_x = sx + (gf*mm)
        for val in [l, w, l, w]:
            c.rect(curr_x, sy, val*mm, h*mm); curr_x += (val*mm)
        c.setStrokeColorRGB(0, 0, 0)
        p = c.beginPath(); p.moveTo(sx, sy+2*mm); p.lineTo(sx+gf*mm, sy); p.lineTo(sx+gf*mm, sy+h*mm); p.lineTo(sx, sy+h*mm-2*mm); p.close(); c.drawPath(p)
        curr_x = sx + (gf*mm)
        for i, val in enumerate([l, w, l, w]):
            f_sx = curr_x + (3 * mm); f_w = (val-3) if i == 3 else (val-6)
            c.rect(f_sx, sy+h*mm, f_w*mm, fh*mm); c.rect(f_sx, sy-fh*mm, f_w*mm, fh*mm)
            curr_x += (val*mm)
        c.line(curr_x, sy, curr_x, sy + h*mm); c.save()
        messagebox.showinfo("Success", "PDF Saved!")

if __name__ == "__main__":
    root = tk.Tk(); app = PackagingWeightFix(root); root.mainloop()