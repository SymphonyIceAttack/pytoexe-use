from tkinter import *
from tkinter import ttk
from PIL import Image,ImageTk
import glob
import os
#  основное  окно программы
root = Tk()  # создаем корневой объект - окно
root.title("Физический калькулятор")  # устанавливаем заголовок окна
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
w = w // 2  # середина экрана
h = h // 2
w = w - 200  # смещение от середины
h = h - 200
root.geometry(f'500x500+{w}+{h}')
root.resizable(False, False)


#  список  тем.  Список  каталогов из  папки  data

physics_topics = os.listdir("data")
#  Listbox  со  списком  тем
physics_topics_var = Variable(value=physics_topics)

physics_topics_listbox = Listbox(listvariable=physics_topics_var)


#  Label
label_name_tema =ttk.Label(text = "Список тем")
label_name_tema.place(relx=0.01, rely=0.00,relwidth=0.29, relheight=0.05)

#  Label
label_name_var =ttk.Label(text = "Список переменных")
label_name_var.place(relx=0.3, rely=0.00,relwidth=0.29, relheight=0.05)

#  Label
label_form =ttk.Label(text = "Список формул")
label_form.place(relx=0.3, rely=0.54,relwidth=0.29, relheight=0.05)

#  Frame
frame_formul = ttk.Frame(borderwidth=1, relief=SOLID)
frame_formul.place(relx=0.3, rely=0.58,relwidth=0.29, relheight=0.41)

#  Listbox  со  списком  переменных из  файлв  var   в  выбранной  папке
name_variable_listbox = Listbox()
name_variable_listbox.place(relx=0.3, rely=0.05, relwidth=0.29, relheight=0.49)




#  обработчик нажатия  в  списке  тем. Заполнение списка  переменных
def Click_physics_topics(event):
    try:
        selected_indices = physics_topics_listbox.curselection()
        dir_tema = "data/" + physics_topics_listbox.get(selected_indices) + "/"
        file_name_var=dir_tema + "var"
        if    os.path.exists(file_name_var):
            file_var = open(file_name_var, "r", encoding="utf8")
            var_topics = file_var.readlines()
            file_var.close()
            name_variable_listbox.delete(0,END)
            for tmp_var in var_topics:
                name_variable_listbox.insert(0,tmp_var)
    except:
        selected_indices = 0
    list_obj = frame_formul.winfo_children()
    for object_name in list_obj:
        object_name.destroy()
    files = glob.glob(dir_tema  + '*.png')
    for file_image  in files:
        img_formul = Image.open(file_image)
        img_formul = ImageTk.PhotoImage(img_formul)
        if "formula1.png" in file_image:
    btn_formul = ttk.Button(frame_formul, image=img_formul, compound=CENTER, command=open_formula1)
else:
    btn_formul = ttk.Button(frame_formul, image=img_formul, compound=CENTER)
        btn_formul.image=img_formul
        btn_formul.place(relx=0.01, rely=0.01, relwidth=0.90, relheight=0.2)





physics_topics_listbox.place(relx=0.01, rely=0.05,relwidth=0.29, relheight=0.95)
physics_topics_listbox.bind("<<ListboxSelect>>", Click_physics_topics)

def open_formula1():

    win = Toplevel()
    win.title("x = x0 + vt")
    win.geometry("250x220")

    Label(win, text="x0").pack()
    entry_x0 = Entry(win)
    entry_x0.pack()

    Label(win, text="v").pack()
    entry_v = Entry(win)
    entry_v.pack()

    Label(win, text="t").pack()
    entry_t = Entry(win)
    entry_t.pack()

    result = Label(win, text="")
    result.pack()

    def calc():
        x0 = float(entry_x0.get())
        v = float(entry_v.get())
        t = float(entry_t.get())

        x = x0 + v * t
        result.config(text=f"x = {x}")

    Button(win, text="Рассчитать", command=calc).pack()
    
root.mainloop()
