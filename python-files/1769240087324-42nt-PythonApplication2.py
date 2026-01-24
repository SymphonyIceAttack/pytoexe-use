import tkinter as tk
from tkinter import messagebox

class MenedzherZadach:
    def __init__(self, okno):
        self.okno = okno
        self.okno.title("Матрица Эйзенхауэра")
        self.okno.geometry("900x600")

        ramka_verh = tk.Frame(self.okno, pady=10)
        ramka_verh.pack(fill=tk.X)

        nadpis_vvod = tk.Label(ramka_verh, text="Текст задачи:")
        nadpis_vvod.pack(side=tk.LEFT, padx=5)

        self.pole_vvoda = tk.Entry(ramka_verh, width=30)
        self.pole_vvoda.pack(side=tk.LEFT, padx=5)

        self.peremennaya_srochno = tk.BooleanVar()
        self.peremennaya_vazhno = tk.BooleanVar()

        galochka_srochno = tk.Checkbutton(ramka_verh, text="Срочно", variable=self.peremennaya_srochno)
        galochka_srochno.pack(side=tk.LEFT, padx=5)

        galochka_vazhno = tk.Checkbutton(ramka_verh, text="Важно", variable=self.peremennaya_vazhno)
        galochka_vazhno.pack(side=tk.LEFT, padx=5)

        knopka_dobavit = tk.Button(ramka_verh, text="Добавить", command=self.dobavit_zadachu, bg="#4CAF50", fg="white")
        knopka_dobavit.pack(side=tk.LEFT, padx=10)

        ramka_matritsy = tk.Frame(self.okno)
        ramka_matritsy.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ramka_matritsy.columnconfigure(0, weight=1)
        ramka_matritsy.columnconfigure(1, weight=1)
        ramka_matritsy.rowconfigure(0, weight=1)
        ramka_matritsy.rowconfigure(1, weight=1)

        self.spisok_srochno_vazhno = self.sozdat_kvadrat(ramka_matritsy, 0, 0, "СРОЧНО и ВАЖНО", "#ffcccc")
        self.spisok_ne_srochno_vazhno = self.sozdat_kvadrat(ramka_matritsy, 0, 1, "НЕ СРОЧНО но ВАЖНО", "#ccffcc")
        self.spisok_srochno_ne_vazhno = self.sozdat_kvadrat(ramka_matritsy, 1, 0, "СРОЧНО но НЕ ВАЖНО", "#fff4cc")
        self.spisok_ne_srochno_ne_vazhno = self.sozdat_kvadrat(ramka_matritsy, 1, 1, "НЕ СРОЧНО и НЕ ВАЖНО", "#e0e0e0")

        self.tekushiy_spisok = None
        
        self.menu_deistviy = tk.Menu(self.okno, tearoff=0)
        self.menu_deistviy.add_command(label="Отметить выполненным", command=self.sdelat_vypolnennym)
        self.menu_deistviy.add_separator()
        self.menu_deistviy.add_command(label="Удалить задачу", command=self.udalit_zadachu)

    def sozdat_kvadrat(self, roditel, ryad, kolonka, zagolovok, cvet_fona):
        ramka = tk.Frame(roditel, bd=2, relief=tk.GROOVE)
        ramka.grid(row=ryad, column=kolonka, sticky="nsew", padx=2, pady=2)

        nadpis = tk.Label(ramka, text=zagolovok, font=("Arial", 10, "bold"), bg=cvet_fona)
        nadpis.pack(fill=tk.X)

        spisok = tk.Listbox(ramka, bg=cvet_fona, selectmode=tk.SINGLE, font=("Arial", 12))
        spisok.pack(fill=tk.BOTH, expand=True)

        spisok.bind("<Button-3>", lambda sobytie, s=spisok: self.pokazat_menu(sobytie, s))
        
        return spisok

    def dobavit_zadachu(self):
        tekst_zadachi = self.pole_vvoda.get()
        if not tekst_zadachi:
            messagebox.showwarning("Внимание", "Напишите текст задачи!")
            return

        srochno = self.peremennaya_srochno.get()
        vazhno = self.peremennaya_vazhno.get()

        if srochno and vazhno:
            self.spisok_srochno_vazhno.insert(tk.END, tekst_zadachi)
        elif srochno and not vazhno:
            self.spisok_srochno_ne_vazhno.insert(tk.END, tekst_zadachi)
        elif not srochno and vazhno:
            self.spisok_ne_srochno_vazhno.insert(tk.END, tekst_zadachi)
        else:
            self.spisok_ne_srochno_ne_vazhno.insert(tk.END, tekst_zadachi)

        self.pole_vvoda.delete(0, tk.END)

    def pokazat_menu(self, sobytie, spisok):
        try:
            spisok.selection_clear(0, tk.END)
            spisok.selection_set(spisok.nearest(sobytie.y))
            spisok.activate(spisok.nearest(sobytie.y))
            
            self.tekushiy_spisok = spisok
            self.menu_deistviy.tk_popup(sobytie.x_root, sobytie.y_root)
        except:
            pass

    def udalit_zadachu(self):
        if self.tekushiy_spisok:
            vydelennoe = self.tekushiy_spisok.curselection()
            if vydelennoe:
                self.tekushiy_spisok.delete(vydelennoe)

    def sdelat_vypolnennym(self):
        if self.tekushiy_spisok:
            vydelennoe = self.tekushiy_spisok.curselection()
            if vydelennoe:
                indeks = vydelennoe[0]
                tekst = self.tekushiy_spisok.get(indeks)
                
                if tekst.startswith("✅ "):
                    noviy_tekst = tekst[2:]
                    self.tekushiy_spisok.itemconfig(indeks, fg="black")
                else:
                    noviy_tekst = "✅ " + tekst
                    self.tekushiy_spisok.itemconfig(indeks, fg="gray50")
                
                self.tekushiy_spisok.delete(indeks)
                self.tekushiy_spisok.insert(indeks, noviy_tekst)

if __name__ == "__main__":
    glavnoe_okno = tk.Tk()
    prilozhenie = MenedzherZadach(glavnoe_okno)
    glavnoe_okno.mainloop()