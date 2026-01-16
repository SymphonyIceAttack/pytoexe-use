import time, random
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key, Listener

# Controller globali
mouse = MouseController()
keyboard = KeyboardController()


# ===== Mouse =====
def move_mouse(x: int, y: int):
    """Sposta il mouse alle coordinate (x, y)"""
    mouse.position = (x, y)


def left_click(x: int = None, y: int = None):
    """Click sinistro del mouse, opzionalmente spostando prima il cursore"""
    if x is not None and y is not None:
        move_mouse(x, y)
    mouse.click(Button.left)


def right_click(x: int = None, y: int = None):
    """Click destro del mouse, opzionalmente spostando prima il cursore"""
    if x is not None and y is not None:
        move_mouse(x, y)
    mouse.click(Button.right)


def get_mouse_position():
    """Ritorna la posizione corrente del mouse come tuple (x, y)"""
    return mouse.position


# ===== Tastiera =====
def keyboard_input(text: str):
    """Scrive testo tramite tastiera"""
    keyboard.type(text)


def press_key(key: str):
    """Premi un singolo tasto"""
    keyboard.press(key)
    keyboard.release(key)


# Funzione base per leggere un singolo tasto
def read_single_key():
    """
    Blocca l'esecuzione finché non viene premuto un tasto.
    Ritorna il tasto premuto.
    """
    key_pressed = None

    def on_press(key):
        nonlocal key_pressed
        key_pressed = key
        return False  # ferma il listener

    with Listener(on_press=on_press) as listener:
        listener.join()

    return key_pressed


def message1():
    print("Non deselezionare questa finestra.")
    print("Posiziona il cursore sopra all'icona di Teams.")
    print("Una volta fatto, premi un tasto della tastiera.")

def message2():
    print('Non deselezionare questa finestra.')
    print('Muovi il cursore dove comparirebbe la voce "Disponibile" (come se cliccassi tasto detro su Teams).')
    print('Una volta fatto, premi un tasto della tastiera.')

def message3():
    print('Per arrestare il processo, premere Ctrl-C o chiudere la finestra. ')
   
def start():
    message1()
    k = read_single_key()
    teams_x, teams_y = get_mouse_position()
    message2()
    k = read_single_key()
    disp_x, disp_y = get_mouse_position()
    min_ = float(input('Ogni quanti minuti aggiornare la presenza? '))
    message3()
    input('Premere Invio per avviare il programma.')
    return teams_x, teams_y, disp_x, disp_y, min_

def script(teams_x, teams_y, disp_x, disp_y):
    move_mouse(teams_x, teams_y)
    time.sleep(0.2)
    
    right_click()
    time.sleep(0.4)
    
    move_mouse(disp_x, disp_y)
    time.sleep(0.2)
    
    left_click()

teams_x, teams_y, disp_x, disp_y, min_ = start()
t0 = time.time()

while True:
    dt = time.time()-t0
    if dt > min_*60+random.uniform(-30, 30):
        script(teams_x, teams_y, disp_x, disp_y)
        print('Presenza aggiornata alle', time.strftime("%H:%M:%S"))
        t0 = time.time()

