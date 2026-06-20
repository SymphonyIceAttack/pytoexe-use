import itertools
from random import randrange
import tkinter as tk
from tkinter import messagebox, font

canvas_width = 800
canvas_height = 400
root = tk.Tk()
root.title("Eierfangen Spiel")
c = tk.Canvas(root, width=canvas_width, height=canvas_height, background='deep sky blue')
c.pack()
c.create_rectangle(-5, canvas_height - 100, canvas_width + 5, canvas_height + 5, fill='sea green', width=0)
c.create_oval(-80, -80, 120, 120, fill='orange', width=0)
farb_zyklus = itertools.cycle(['light blue', 'light green', 'light pink', 'light yellow', 'light cyan'])
ei_width = 45
ei_height = 55
ei_punktzahl = 10
ei_tempo = 500
ei_intervall = 4000
schwierigkeit = 0.95
korb_color = 'blue'
korb_width = 100
korb_height = 100
korb_start_x = canvas_width / 2 - korb_width / 2
korb_start_y = canvas_height - korb_height - 20
korb_start_x2 = korb_start_x + korb_width
korb_start_y2 = korb_start_y + korb_height
korb = c.create_arc(korb_start_x, korb_start_y, korb_start_x2, korb_start_y2, start=200, extent=140, style='arc', outline=korb_color, width=3)
game_font = font.nametofont('TkFixedFont')
game_font.config(size=18)
punktzahl = 0
punktzahl_text = c.create_text(10, 10, anchor='nw', font=game_font, fill='darkblue', text='Punktzahl: ' + str(punktzahl))
verbleibende_leben = 3
leben_text = c.create_text(canvas_width - 10, 10, anchor='ne', font=game_font, fill='darkblue', text='Leben: ' + str(verbleibende_leben))
eier = []
def create_ei():
    x = randrange(10, canvas_width - ei_width - 10)
    y = 40
    neues_ei = c.create_oval(x, y, x + ei_width, y + ei_height, fill=next(farb_zyklus), width=0)
    eier.append(neues_ei)
    root.after(ei_intervall, create_ei)
def move_eier():
    for ei in eier:
        ei_x, ei_y, ei_x2, ei_y2 = c.coords(ei)
        c.move(ei, 0, 10)
        if ei_y2 > canvas_height:
            ei_gefallen(ei)
    root.after(ei_tempo, move_eier)
def ei_gefallen(ei):
    if ei in eier:
        eier.remove(ei)
        c.delete(ei)
        verliere_ein_leben()
        if verbleibende_leben == 0:
            messagebox.showinfo('Game Over!', 'Endpunktzahl: ' + str(punktzahl))
            root.destroy()
def verliere_ein_leben():
    global verbleibende_leben
    verbleibende_leben -= 1
    c.itemconfigure(leben_text, text='Leben: ' + str(verbleibende_leben))
def check_fang():
    korb_x1, korb_y1, korb_x2, korb_y2 = c.coords(korb)
    for ei in eier:
        ei_x1, ei_y1, ei_x2, ei_y2 = c.coords(ei)
        if korb_x1 < ei_x1 and ei_x2 < korb_x2 and korb_y2 - ei_y2 < 40:
            eier.remove(ei)
            c.delete(ei)
            erhoehe_punktzahl(ei_punktzahl)
    root.after(100, check_fang)
def erhoehe_punktzahl(points):
    global punktzahl, ei_tempo, ei_intervall
    punktzahl += points
    ei_tempo = int(ei_tempo * schwierigkeit)
    ei_intervall = int(ei_intervall * schwierigkeit)
    c.itemconfigure(punktzahl_text, text='Punktzahl: ' + str(punktzahl))
def move_left(event):
    x1, y1, x2, y2 = c.coords(korb)
    if x1 > 0:
        c.move(korb, -20, 0)
def move_right(event):
    x1, y1, x2, y2 = c.coords(korb)
    if x2 < canvas_width:
        c.move(korb, 20, 0)
c.bind('<Left>', move_left)
c.bind('<Right>', move_right)
c.focus_set()
root.after(1000, create_ei)
root.after(1000, move_eier)
root.after(1000, check_fang)
root.mainloop()
