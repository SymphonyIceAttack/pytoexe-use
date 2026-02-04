from tkinter import*
window = Tk()  
window.title("Преобразование данных")
window.geometry("500x500")

frame = Frame(window) #создаем фрейм, в котором будет размещено поле для ввода

class Group_Widgets(object):           #создаем класс с тремя объектами - entry, button, label
    def __init__(self):  #Конструктор с аргументами
        self.entry = Entry(frame, width = 30)      #Атрибуты (свойства) объекта
        self.button = Button(frame, bg = "yellow", fg = "black", text = "Преобразовать", font = "Arial 16") 
        self.label = Label(frame, bg = "red", fg = "black", text = "                          ", font = "Arial 16")
        self.entry.pack()
        self.button.pack()
        self.label.pack()
        
    def show_input_and_sort_up(self):  #метод отображения введенного списка в лэйбле с сортировкой по возрастанию (функция сортировки)
        numbers = self.entry.get()   #считывание введенных данных из поля данных Entry 
        sorted_numbers = sorted(numbers, reverse = False) #сортировка чисел по возрастанию
        self.label.config(text = f"{sorted_numbers}") #вставка чисел в лэйбл

    def setFunc(self, func):       #метод, связывающий кнопку с функцией сортировки (параметр command вынесен из свойств кнопки в отдельный метод - функцию,связанную с классом)
        self.button['command'] = eval('self.' + func)

button = Group_Widgets()  #связь кнопки с классом
button.setFunc('show_input_and_sort_up') #связь кнопки с функцией сортировки "show_input_and_sort_up" через связующий метод - функцию "setFunc" 

#Располагаем поле ввода
frame.pack()

#Цикл обработки событий окна
window.mainloop()
