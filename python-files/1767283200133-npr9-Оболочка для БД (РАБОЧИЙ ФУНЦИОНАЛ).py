import psycopg2 as ps2
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter.messagebox import showinfo, showerror, showwarning
from tkinter import filedialog
import csv
conn=()# пустой параметр подключения к БД (изменяется нажатием кнопки  "Connect to DB")
login=()
passcode=()
table=()
class Application(Frame):
    '''GUI-приложение'''
    def __init__(self, master):
        '''Инициализация рамки'''
        super(Application, self).__init__(master)
        self.grid()
        self.create_widget()
    def create_widget(self):
        '''Создает кнопки, текстовые поля и области'''
        #метка-инструкция
        self.inst_lbl=Label(self, text='Программа чтения данных "Радиосредства"',font=('Times New Roman', 18, 'bold'))
        self.inst_lbl.grid(row=0, column=0, columnspan=5, sticky=N)
        #поля ввода данных
        Label(self, text='Введите логин').grid(row=1, column=1, sticky=W)
        self.login_ent=Entry(self)
        self.login_ent.grid(row=1, column=2, sticky=W)
        Label(self, text='Введите пароль').grid(row=2, column=1, sticky=W)
        self.passcode_ent=Entry(self, show='*')
        self.passcode_ent.grid(row=2, column=2, sticky=W)
        Label(self, text='Поиск по заданному значению', font=('Times New Roman', 13, 'bold')).grid(row=8, column=2, sticky=W)
        self.search_ent=Entry(self)
        self.search_ent.grid(row=9, column=2, columnspan=10, sticky=W)        
        #кнопки
        self.connect_bttn=Button(self, text='Connect to DB', command=self.connect, bd=3, bg='green', fg='white')
        self.connect_bttn.grid(row=3, column=1, sticky=W)
        self.disconnect_bttn=Button(self, text='Disconnect from DB', command=self.disconnect, bd=3, bg='red', fg='black')
        self.disconnect_bttn.grid(row=4, column=1, sticky=W)
        self.read_bttn=Button(self, text='Прочитать данные', font=('Arial', 12), command=self.read_data, bd=3)
        self.read_bttn.grid(row=5, column=2, sticky=W)
        self.search_bttn=Button(self, text='Поиск', font=('Arial', 12), command=self.search_data, bd=3)
        self.search_bttn.grid(row=9, column=1, sticky=W)
        #self.search_bttn.place(x=20, y=620)
        self.save_bttn=Button(self, text='Сохранить в файл', command=self.save_dialog, bd=3)
        self.save_bttn.grid(row=15, column=1, sticky=W)
        #создание текстовой области для отображения статусов подключения и чтения, вывода данных
        self.connection_status_txt=Text(self, width=30, height=2, wrap=WORD, bg='cyan', bd=3)
        self.connection_status_txt.grid(row=3, column=2, sticky=N)
        self.data_read_status_txt=Text(self, width=30, height=1, wrap=WORD, bg='magenta', fg='white', bd=3)
        self.data_read_status_txt.grid(row=6, column=2, sticky=W)
        self.result_txt=Text(self, width=50, height=25, wrap=WORD, bg='lightgreen', bd=3)
        self.result_txt.grid(row=7, column=2, sticky=W)
        #выбор параметра поиска
        Label(self,text='Выберите параметр поиска:').grid(row=10, column=1, sticky = W)
        #переменная для хранения сведений о выборе
        self.parameter=StringVar()
        self.parameter.set(None)
        parameters=['модель', 'класс', 'id (полностью)', 'зав. номер', 'фамилия']
        row=10
        for parameter in parameters:
            Radiobutton(self,
                        text=parameter,
                        variable=self.parameter,
                        value=parameter).grid(row=row, column=2, sticky=W)
            row+=1        
    def connect(self):
        try:
            global conn
            global login
            global passcode
            login=self.login_ent.get()
            passcode=self.passcode_ent.get()
            conn=ps2.connect(dbname='radiobase',
                             host='127.0.0.1',
                             user=login,
                             password=passcode,
                             port='5432')
            message='Соединение с БД установлено.'
            showinfo(title='Connection Status', message=message)
        except:
            message='Не удалось установить соединение с БД.'
            showwarning(title='Connection Status', message=message)
        self.connection_status_txt.delete(0.0, END)
        self.connection_status_txt.insert(0.0, message)
    def disconnect(self):
        global conn
        global login
        global passcode        
        conn.close()
        conn=()
        login=()
        passcode=()
        message='Соединение с БД закрыто.'
        showinfo(title='Connection Status', message=message)
        self.connection_status_txt.delete(0.0, END)
        self.connection_status_txt.insert(0.0, message)
    def read_data(self):
        try:
            global conn
            global table
            conn.autocommit=True
            cursor=conn.cursor()
            cursor.execute('SELECT * FROM models ORDER BY id ASC;')
            result=cursor.fetchall()
            message='Данные прочитаны успешно.'
            showinfo(title='Data Reading Status', message=message)
        except:
             message='Ошибка чтения данных.'
             showerror(title='Data Reading Status', message=message)
        self.data_read_status_txt.delete(0.0, END)
        self.data_read_status_txt.insert(0.0, message)
        self.result_txt.delete(0.0, END)
        self.result_txt.insert(0.0, result)
        #создание окна для отображения данных по запросу
        window=Tk()
        window.title('Результаты запроса')
        window.geometry('800x600')
        frametable=tk.Frame(window, bg='blue')
        frametable.pack(expand=True, anchor='nw', fill=Y)#fill растягивает рамку для таблицы в window
        #представление данных в виде таблицы
        global table
        heads=('№ п/п', 'Производитель', 'Модель', 'Номенклатура' , 'Диапазон',
               'МАХ мощность', 'Тип', 'Класс устройсва' , 'Нижняя частота', 'Верхняя частота') #названия столбцов
        table=ttk.Treeview(frametable, columns=heads, show='headings') #если нужно отобразить корневой столбец, то tree_headings 
        table['displaycolumns']=['№ п/п', 'Производитель', 'Модель', 'Номенклатура' , 'Диапазон',
                                 'МАХ мощность', 'Тип', 'Класс устройсва' , 'Нижняя частота', 'Верхняя частота'] #порядок отображения столбцов
        #table.grid(row=0, column=0, sticky='ns') #nswe растягивает таблицу на все стороны;
                                                  #не используется, т.к. далее к scrollbar применяется pack
        for header in heads:
            table.heading(header, text=header, anchor='center')
            table.column(header, anchor='center')
        for item in result:
            table.insert('', END, values=item)
        #параметры каждого столбца
        table.column('#1', width=60, minwidth=60, anchor='center') #значения anchor - S, N, W, E, NE, NW, SE, SW, 'center', 's', 'n' и т.п.
        table.column('#2', width=100, minwidth=100, anchor='center')
        table.column('#3', width=100, minwidth=100, anchor='center')
        table.column('#4', width=250, minwidth=250, anchor='center')
        table.column('#5', width=150, minwidth=150, anchor='center')
        table.column('#6', width=100, minwidth=100, anchor='center')
        table.column('#7', width=100, minwidth=100, anchor='center')
        table.column('#8', width=100, minwidth=100, anchor='center')
        table.column('#9', width=150, minwidth=150, anchor='center')
        table.column('#10', width=150, minwidth=150, anchor='center')
        #поля прокрутки таблицы
        scrolly=ttk.Scrollbar(frametable, command=table.yview)
        table.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx=ttk.Scrollbar(frametable, orient=HORIZONTAL, command=table.xview)
        table.configure(xscrollcommand=scrollx.set)
        scrollx.pack(side=BOTTOM, fill=X)
        table.pack(expand=True, fill=tk.BOTH)
    def search_data(self):
        search=self.search_ent.get()
        choice=self.parameter.get()
        try:
            global conn
            global table
            conn.autocommit=True
            cursor=conn.cursor()
            if choice=='модель':
                choice='"Модель"'
                cursor.execute ("SELECT * FROM gupsit WHERE " + choice +" LIKE '%" + search + "%' ORDER BY id ASC;")
            elif choice=='класс':
                choice='"РЭС или ВЧУ"'
                cursor.execute("SELECT * FROM gupsit WHERE " + choice +" LIKE '%" + search + "%' ORDER BY id ASC;")
            elif choice=='id (полностью)':
                choice='id'
                cursor.execute('SELECT * FROM gupsit WHERE ' + choice + '=' + search)
            elif choice=='зав. номер':
                choice='"Заводской номер"'
                cursor.execute("SELECT * FROM gupsit WHERE " + choice +" LIKE '%" + search + "%' ORDER BY id ASC;")
            elif choice=='фамилия':
                choice='"Фамилия ответственного"'
                cursor.execute("SELECT * FROM gupsit WHERE " + choice +" LIKE '%" + search + "%' ORDER BY id ASC;")
            result=cursor.fetchall()
            message='Данные прочитаны успешно.'
            showinfo(title='Data Reading Status', message=message)
        except:
             message='Ошибка чтения данных.'
             showerror(title='Data Reading Status', message=message)
        self.data_read_status_txt.delete(0.0, END)
        self.data_read_status_txt.insert(0.0, message)
        self.result_txt.delete(0.0, END)
        self.result_txt.insert(0.0, result)
        #создание окна для отображения данных по запросу
        window=Tk()
        window.title('Результаты запроса')
        window.geometry('800x600')
        frametable=tk.Frame(window, bg='blue')
        frametable.pack(expand=True, anchor='nw', fill=Y)#fill растягивает рамку для таблицы на весь размер window
        #представление данных в виде таблицы
        global table
        heads=('№ п/п', 'Производитель', 'Модель', 'Номенклатура' , 'Диапазон',
               'МАХ мощность', 'Тип', 'Класс устройсва' , 'Нижняя частота', 'Верхняя частота') #названия столбцов
        table=ttk.Treeview(frametable, columns=heads, show='headings') #если нужно отобразить корневой столбец, то tree_headings 
        table['displaycolumns']=['№ п/п', 'Производитель', 'Модель', 'Номенклатура' , 'Диапазон',
                                 'МАХ мощность', 'Тип', 'Класс устройсва' , 'Нижняя частота', 'Верхняя частота'] #порядок отображения столбцов
        #table.grid(row=0, column=3, sticky='ns') #nswe растягивает таблицу на все стороны 
        for header in heads:
            table.heading(header, text=header, anchor='center')
            table.column(header, anchor='center')
        for item in result:
            table.insert('', END, values=item)
        #параметры каждого столбца
        table.column('#1', width=60, minwidth=60, anchor='center') #значения anchor - S, N, W, E, NE, NW, SE, SW, 'center', 's', 'n' и т.п.
        table.column('#2', width=100, minwidth=100, anchor='center')
        table.column('#3', width=100, minwidth=100, anchor='center')
        table.column('#4', width=250, minwidth=250, anchor='center')
        table.column('#5', width=150, minwidth=150, anchor='center')
        table.column('#6', width=100, minwidth=100, anchor='center')
        table.column('#7', width=100, minwidth=100, anchor='center')
        table.column('#8', width=100, minwidth=100, anchor='center')
        table.column('#9', width=150, minwidth=150, anchor='center')
        table.column('#10', width=150, minwidth=150, anchor='center')
        #поля прокрутки таблицы
        scrolly=ttk.Scrollbar(frametable, command=table.yview)
        table.configure(yscrollcommand=scrolly.set)
        scrolly.pack(side=RIGHT, fill=Y)
        scrollx=ttk.Scrollbar(frametable, orient=HORIZONTAL, command=table.xview)
        table.configure(xscrollcommand=scrollx.set)
        scrollx.pack(side=BOTTOM, fill=X)
        table.pack(expand=True, fill=BOTH)
    def save(self, table, filename): #сохраняет данные в csv
        with open(filename, 'w+', newline='') as file: #при указании encoding='utf-8' некорректно отбражается кириллица!!!
            writer=csv.writer(file)
            writer.writerow(table['columns'])
            for item in table.get_children():
                writer.writerow(table.item(item, 'values')) #table.item(item, 'values') возвращает кортеж значений из ячеек
    def save_dialog(self): #открывает диалоговое окно сохранения
        filepath=filedialog.asksaveasfilename(title='Сохранение данных в файл',
                                              initialdir='C://Users/User/Desktop',
                                              defaultextension='.csv',
                                              filetypes=[('Таблица Excel (.csv)', '*.csv'), ('All files (.*)', '*.*')],
                                              initialfile='Table.csv')
        if filepath:
            self.save(table, filepath)
root=Tk()#создание окна
root.title('Клент БД "Радиосредства"') #заголовок окна
root.geometry('600x600') #размер окна
app=Application(root)
root.mainloop #запуск событийного цикла




