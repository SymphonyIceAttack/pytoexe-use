# MetaGold Margin Calculator
# Place metag.png next to this file.
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

RED="#C00000";WHITE="#FFFFFF";LIGHT_RED="#FCE4E4";GRAY="#555555"

symbols={
"EURUSD":100000,"GBPUSD":100000,"USDJPY":100000,"AUDUSD":100000,
"AUDUSD":100000,"NZDUSD":100000,"USDCAD":100000,"USDCHF":100000,
"XAUUSD":100,"XAGUSD":5000,"US30":10,"NAS100":1,"SPX500":1,"GER40":1,"UK100":1,"JP225":1}

def update_contract(e=None):
    contract_label.config(text=f"Contract Size : {symbols[symbol_box.get()]:,}")

def calculate_margin():
    try:
        symbol=symbol_box.get()
        price=float(price_entry.get())
        lot=float(lot_entry.get())
        lev=int(leverage_box.get())
        c=symbols[symbol]
        notional=c*lot*price
        margin=notional/lev
        result_label.config(text=f"Symbol : {symbol}\n\nLot Size : {lot}\nLeverage : 1:{lev}\nContract Size : {c:,}\n\nNotional Value : {notional:,.2f} USD\nRequired Margin : {margin:,.2f} USD")
    except:
        messagebox.showerror("Error","Please enter valid numbers")

def reset():
    price_entry.delete(0,tk.END);lot_entry.delete(0,tk.END);result_label.config(text="")
def copy_result():
    root.clipboard_clear();root.clipboard_append(result_label.cget("text"));root.update()

root=tk.Tk()
root.title("MetaGold - Margin Calculator")
root.geometry("450x650");root.configure(bg=WHITE);root.resizable(False,False)
try:
    root.iconphoto(True, tk.PhotoImage(file="metag.png"))
except: pass

header=tk.Frame(root,bg=RED,height=90);header.pack(fill="x");header.pack_propagate(False)
try:
    img=Image.open("metag.png").resize((48,48),Image.LANCZOS)
    logo=ImageTk.PhotoImage(img)
    l=tk.Label(header,image=logo,bg=RED);l.image=logo;l.pack(side="left",padx=18)
except: pass
tf=tk.Frame(header,bg=RED);tf.pack(side="left")
tk.Label(tf,text="MetaGold",font=("Segoe UI",20,"bold"),fg="white",bg=RED).pack(anchor="w")
tk.Label(tf,text="Margin Calculator",font=("Segoe UI",10),fg="white",bg=RED).pack(anchor="w")

tk.Label(root,text="Symbol",bg=WHITE).pack(pady=5)
symbol_box=ttk.Combobox(root,values=list(symbols.keys()),state="readonly");symbol_box.pack();symbol_box.current(0);symbol_box.bind("<<ComboboxSelected>>",update_contract)
contract_label=tk.Label(root,text="Contract Size : 100,000",bg=WHITE,fg=GRAY);contract_label.pack(pady=5)
tk.Label(root,text="Current Price",bg=WHITE).pack();price_entry=tk.Entry(root,width=25);price_entry.pack()
tk.Label(root,text="Lot Size",bg=WHITE).pack();lot_entry=tk.Entry(root,width=25);lot_entry.pack()
tk.Label(root,text="Leverage",bg=WHITE).pack(pady=5)
leverage_box=ttk.Combobox(root,values=[100,200,300,400],state="readonly");leverage_box.pack();leverage_box.current(0)
bf=tk.Frame(root,bg=WHITE);bf.pack(pady=20)
tk.Button(bf,text="Calculate",bg=RED,fg="white",width=12,command=calculate_margin).grid(row=0,column=0,padx=5)
tk.Button(bf,text="Reset",bg=RED,fg="white",width=12,command=reset).grid(row=0,column=1,padx=5)
tk.Button(bf,text="Copy",bg=RED,fg="white",width=12,command=copy_result).grid(row=0,column=2,padx=5)
result_label=tk.Label(root,text="",font=("Segoe UI",11,"bold"),fg=RED,bg=LIGHT_RED,width=40,height=10,justify="left")
result_label.pack(pady=20)
root.mainloop()
