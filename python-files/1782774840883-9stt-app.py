import tkinter as tk 
okno_resulta = None
def calculate():
        if razmer >= 20:
            result = "Ого какой большой!!"
        else:
            result = "Неважно, какого размера твой клинок, важно лишь то, как ты с ним управляешься!"
def podschet_rezultatov():
    global okno_resulta
    if okno_resulta is not None:
        okno_resulta.destroy()
    try:
        razmer = float(davai_vvedi_razmer_chelna.get())
        if razmer >= 20:
            result = "Ого какой большой!!"
        else:
            result = "Неважно, какого размера твой клинок, важно лишь то, как ты с ним управляешься!"
        okno_resulta = tk.Toplevel(root)
        okno_resulta.title("Ваш результат:")
        okno_resulta.geometry("600x400")
        resulta_okno = tk.Label(okno_resulta, text = result, wraplength=200)
        resulta_okno.pack(pady = 20)
        zakrit_knopka = tk.Button(okno_resulta, text = "Закрыть окно с результатом", command=okno_resulta.destroy)
        zakrit_knopka.pack( pady = 20)
    except ValueError:
        balli_OGE.config(text = "Ты че еблан???")
    davai_vvedi_razmer_chelna.delete(0, tk.END)
root = tk.Tk()
root.geometry("1000x1000")
root.title("Магический калькулятор размера челна!")
mesto_dlya_Vvoda_razmera = tk.Label(root, text = "Введите размер вашего джунжурика!")
mesto_dlya_Vvoda_razmera.pack(pady = 20)
davai_vvedi_razmer_chelna = tk.Entry(root, width = 20)
davai_vvedi_razmer_chelna.pack(pady = 20)
podtverdid = tk.Button(root, text = "Ввести размер челна", command=podschet_rezultatov)
podtverdid.pack( pady = 20)
balli_OGE = tk.Label(root, text = "")
balli_OGE.pack(pady =  20)
knopka_zakrit = tk.Button(root, text = "Закрыть Магический вычислитель размера челна.", command = root.destroy)
knopka_zakrit.pack(pady = 20)


root.mainloop()