# ==================================================
# TL COMMUNITY - SCRIPT COMPATÍVEL COM EXE
# ==================================================
import ctypes
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import sys

# ==================================================
# CONSTANTES
# ==================================================
VK_RBUTTON = 0x02
VK_DELETE = 0x2E
VK_Q = 0x51
VK_E = 0x45
VK_OEM_PLUS = 0xBB
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_MOVE = 0x0001

user32 = ctypes.windll.user32

# ==================================================
# CHAVE ÚNICA (1 HORA)
# ==================================================
CHAVE_VALIDA = "MCROPRIV-001-1h-kvlak"
TEMPO_EXPIRACAO = 3600

# ==================================================
# VARIÁVEIS GLOBAIS
# ==================================================
running = True
macro_enabled = True
litefoot_status = False
sessao_ativa = False
tempo_restante = TEMPO_EXPIRACAO

# Litefoot
tecla1 = "Q"
tecla2 = "E"
tecla3 = "Q"
tecla4 = "="
delay_litefoot = 20

# Correr
correr_ativo = False
delay_correr = 320

# Recoil
recoil_ativo = False
recoil_intensidade = 110
recoil_delay = 55

# Mira
mira_ativo = False
mira_estilo = "ponto"
mira_cor = "#00ff00"
mira_borda = "#000000"
mira_tamanho = 20
mira_x = 0
mira_y = 0
mira_window = None
mira_canvas = None

login_root = None
main_root = None
delay_litefoot_label = None
delay_correr_label = None
recoil_intensidade_label = None
recoil_delay_label = None
btn_tecla1 = None
btn_tecla2 = None
btn_tecla3 = None
btn_tecla4 = None
frame_litefoot = None
frame_correr = None
frame_recoil = None
frame_mira = None
correr_status_label = None
recoil_status_label = None
mira_status_label = None
btn_correr_toggle = None
btn_recoil_toggle = None
btn_litefoot_toggle = None
litefoot_status_label = None
btn_litefoot = None
btn_correr = None
btn_recoil = None
btn_mira = None
btn_cor_mira = None
btn_cor_borda = None
label_tamanho = None
combo_estilo = None
label_tempo = None

# ==================================================
# FUNÇÕES AUXILIARES (compatíveis com exe)
# ==================================================

def is_key_down(vk):
    try:
        return (user32.GetAsyncKeyState(vk) & 0x8000) != 0
    except:
        return False

def press_key(vk, hold_seconds=0.02):
    try:
        user32.keybd_event(vk, 0, 0, 0)
        if hold_seconds:
            time.sleep(hold_seconds)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    except:
        pass

def get_vk(tecla):
    vk_map = {
        'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
        'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
        'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
        'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
        'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
        'Z': 0x5A,
        '=': 0xBB,
    }
    return vk_map.get(tecla.upper(), 0)

def send_wheel_up():
    try:
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, 120, 0)
    except:
        pass

def move_mouse(dx, dy):
    try:
        user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
    except:
        pass

# ==================================================
# LITEFOOT
# ==================================================
def execute_litefoot():
    global macro_enabled, tecla1, tecla2, tecla3, tecla4, delay_litefoot, litefoot_status
    if not macro_enabled or not litefoot_status:
        return
    d = delay_litefoot / 1000
    vk1 = get_vk(tecla1)
    vk2 = get_vk(tecla2)
    vk3 = get_vk(tecla3)
    vk4 = get_vk(tecla4)
    press_key(vk1, hold_seconds=d)
    time.sleep(d)
    press_key(vk2, hold_seconds=d)
    time.sleep(d)
    press_key(vk3, hold_seconds=d)
    time.sleep(d)
    press_key(vk4, hold_seconds=d)

# ==================================================
# CORRER
# ==================================================
def loop_correr():
    global correr_ativo, running, delay_correr
    while correr_ativo and running:
        send_wheel_up()
        time.sleep(delay_correr / 1000)

def toggle_correr():
    global correr_ativo, correr_thread, running, btn_correr_toggle, correr_status_label
    if not correr_ativo:
        correr_ativo = True
        if btn_correr_toggle:
            btn_correr_toggle.config(text="⏹ DESATIVAR", bg="#c0392b")
        if correr_status_label:
            correr_status_label.config(text="● ATIVADO", fg="#27ae60")
        correr_thread = threading.Thread(target=loop_correr, daemon=True)
        correr_thread.start()
    else:
        correr_ativo = False
        if btn_correr_toggle:
            btn_correr_toggle.config(text="▶ ATIVAR", bg="#2c3e50")
        if correr_status_label:
            correr_status_label.config(text="● DESATIVADO", fg="#e74c3c")

# ==================================================
# RECOIL
# ==================================================
def execute_recoil():
    global recoil_ativo, recoil_intensidade, recoil_delay
    if not recoil_ativo:
        return
    move_mouse(0, recoil_intensidade)
    time.sleep(0.001)
    move_mouse(-recoil_intensidade, 0)

def check_recoil():
    prev_state = False
    global running, recoil_ativo, recoil_delay
    while running:
        try:
            cur = is_key_down(VK_RBUTTON)
            if not cur and prev_state:
                if recoil_ativo:
                    time.sleep(recoil_delay / 1000)
                    threading.Thread(target=execute_recoil, daemon=True).start()
            prev_state = cur
        except:
            pass
        time.sleep(0.001)

def toggle_recoil():
    global recoil_ativo, btn_recoil_toggle, recoil_status_label
    recoil_ativo = not recoil_ativo
    if recoil_ativo:
        if btn_recoil_toggle:
            btn_recoil_toggle.config(text="⏹ DESATIVAR", bg="#c0392b")
        if recoil_status_label:
            recoil_status_label.config(text="● ATIVADO", fg="#27ae60")
    else:
        if btn_recoil_toggle:
            btn_recoil_toggle.config(text="▶ ATIVAR", bg="#2c3e50")
        if recoil_status_label:
            recoil_status_label.config(text="● DESATIVADO", fg="#e74c3c")

def toggle_litefoot():
    global litefoot_status, macro_enabled, btn_litefoot_toggle, litefoot_status_label
    litefoot_status = not litefoot_status
    macro_enabled = litefoot_status
    if litefoot_status:
        if btn_litefoot_toggle:
            btn_litefoot_toggle.config(text="⏹ DESATIVAR", bg="#c0392b")
        if litefoot_status_label:
            litefoot_status_label.config(text="● ATIVADO", fg="#27ae60")
    else:
        if btn_litefoot_toggle:
            btn_litefoot_toggle.config(text="▶ ATIVAR", bg="#2c3e50")
        if litefoot_status_label:
            litefoot_status_label.config(text="● DESATIVADO", fg="#e74c3c")

# ==================================================
# MIRA
# ==================================================
def criar_janela_mira():
    global mira_window, mira_canvas, mira_ativo
    if mira_window:
        mira_window.destroy()
        mira_window = None
        mira_canvas = None
    if not mira_ativo or not main_root:
        return
    mira_window = tk.Toplevel(main_root)
    mira_window.title("Mira")
    mira_window.attributes('-transparentcolor', '#010101')
    mira_window.attributes('-topmost', True)
    mira_window.overrideredirect(True)
    mira_window.geometry(f"{main_root.winfo_screenwidth()}x{main_root.winfo_screenheight()}+0+0")
    mira_window.configure(bg='#010101')
    mira_canvas = tk.Canvas(
        mira_window,
        width=main_root.winfo_screenwidth(),
        height=main_root.winfo_screenheight(),
        bg='#010101',
        highlightthickness=0
    )
    mira_canvas.pack()
    desenhar_mira()

def desenhar_mira():
    global mira_canvas, mira_estilo, mira_cor, mira_borda, mira_tamanho, mira_x, mira_y
    if not mira_canvas:
        return
    mira_canvas.delete("all")
    cx = main_root.winfo_screenwidth() // 2 + mira_x
    cy = main_root.winfo_screenheight() // 2 + mira_y
    t = mira_tamanho
    if mira_estilo == "ponto":
        r = max(2, t // 4)
        mira_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=mira_cor, outline=mira_cor)
    elif mira_estilo == "ponto_borda":
        r = max(4, t // 3)
        mira_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=mira_borda, outline=mira_borda)
        r2 = max(2, r - 3)
        mira_canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, fill=mira_cor, outline=mira_cor)
    elif mira_estilo == "circulo":
        r = max(5, t // 2)
        mira_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=mira_cor, width=2)
    elif mira_estilo == "cruz_cs":
        gap = max(2, t // 6)
        length = max(6, t // 2)
        thickness = max(1, t // 12)
        mira_canvas.create_line(cx, cy-gap, cx, cy-gap-length, fill=mira_cor, width=thickness)
        mira_canvas.create_line(cx, cy+gap, cx, cy+gap+length, fill=mira_cor, width=thickness)
        mira_canvas.create_line(cx-gap, cy, cx-gap-length, cy, fill=mira_cor, width=thickness)
        mira_canvas.create_line(cx+gap, cy, cx+gap+length, cy, fill=mira_cor, width=thickness)
    elif mira_estilo == "ponto_cruz":
        gap = max(2, t // 8)
        length = max(5, t // 3)
        thickness = max(1, t // 14)
        mira_canvas.create_line(cx, cy-gap, cx, cy-gap-length, fill=mira_cor, width=thickness)
        mira_canvas.create_line(cx, cy+gap, cx, cy+gap+length, fill=mira_cor, width=thickness)
        mira_canvas.create_line(cx-gap, cy, cx-gap-length, cy, fill=mira_cor, width=thickness)
        mira_canvas.create_line(cx+gap, cy, cx+gap+length, cy, fill=mira_cor, width=thickness)
        r = max(2, t // 8)
        mira_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=mira_cor, outline=mira_cor)

def toggle_mira():
    global mira_ativo, btn_mira_toggle, mira_status_label
    mira_ativo = not mira_ativo
    if mira_ativo:
        if btn_mira_toggle:
            btn_mira_toggle.config(text="⏹ DESATIVAR", bg="#c0392b")
        if mira_status_label:
            mira_status_label.config(text="● ATIVADO", fg="#27ae60")
        criar_janela_mira()
        threading.Thread(target=listen_arrow_keys, daemon=True).start()
    else:
        if btn_mira_toggle:
            btn_mira_toggle.config(text="▶ ATIVAR", bg="#2c3e50")
        if mira_status_label:
            mira_status_label.config(text="● DESATIVADO", fg="#e74c3c")
        if mira_window:
            mira_window.destroy()

def listen_arrow_keys():
    global mira_x, mira_y, mira_ativo
    while mira_ativo and running:
        if is_key_down(0x26):
            mira_y -= 2
            desenhar_mira()
            time.sleep(0.02)
        elif is_key_down(0x28):
            mira_y += 2
            desenhar_mira()
            time.sleep(0.02)
        elif is_key_down(0x25):
            mira_x -= 2
            desenhar_mira()
            time.sleep(0.02)
        elif is_key_down(0x27):
            mira_x += 2
            desenhar_mira()
            time.sleep(0.02)
        else:
            time.sleep(0.01)

def escolher_cor_mira():
    global mira_cor
    cor = colorchooser.askcolor(title="Escolha a cor da mira", color=mira_cor)
    if cor:
        mira_cor = cor[1]
        btn_cor_mira.config(bg=mira_cor)
        if mira_ativo:
            desenhar_mira()

def escolher_cor_borda():
    global mira_borda
    cor = colorchooser.askcolor(title="Escolha a cor da borda", color=mira_borda)
    if cor:
        mira_borda = cor[1]
        btn_cor_borda.config(bg=mira_borda)
        if mira_ativo:
            desenhar_mira()

def atualizar_estilo_mira(valor):
    global mira_estilo
    estilos = {
        "Ponto": "ponto",
        "Ponto com Borda": "ponto_borda",
        "Círculo": "circulo",
        "Cruz CS 1.6": "cruz_cs",
        "Ponto + Cruz": "ponto_cruz"
    }
    mira_estilo = estilos.get(valor, "ponto")
    if mira_ativo:
        desenhar_mira()

def atualizar_tamanho_mira(valor):
    global mira_tamanho
    mira_tamanho = int(float(valor))
    if mira_tamanho < 5:
        mira_tamanho = 5
    label_tamanho.config(text=f"{mira_tamanho}px")
    if mira_ativo:
        desenhar_mira()

# ==================================================
# MONITORES
# ==================================================
def check_right_button():
    prev_state = False
    global running, macro_enabled, litefoot_status
    while running:
        try:
            cur = is_key_down(VK_RBUTTON)
            if not cur and prev_state:
                if macro_enabled and litefoot_status:
                    threading.Thread(target=execute_litefoot, daemon=True).start()
            prev_state = cur
        except:
            pass
        time.sleep(0.001)

def check_toggle_delete():
    prev_state = False
    global macro_enabled, running
    while running:
        try:
            cur = is_key_down(VK_DELETE)
            if cur and not prev_state:
                macro_enabled = not macro_enabled
                if not macro_enabled and litefoot_status:
                    if btn_litefoot_toggle:
                        btn_litefoot_toggle.config(text="▶ ATIVAR", bg="#2c3e50")
                    if litefoot_status_label:
                        litefoot_status_label.config(text="● DESATIVADO", fg="#e74c3c")
            prev_state = cur
        except:
            pass
        time.sleep(0.05)

# ==================================================
# LOGIN
# ==================================================
def fazer_login():
    key = entry_key.get().strip()
    if key == CHAVE_VALIDA:
        global sessao_ativa, tempo_restante, main_root
        sessao_ativa = True
        tempo_restante = TEMPO_EXPIRACAO
        login_root.destroy()
        threading.Thread(target=contador_expiracao, daemon=True).start()
        criar_interface_principal()
    else:
        messagebox.showerror("Erro", "❌ Chave inválida!\nUse: MCROPRIV-001-1h-kvlak")

def contador_expiracao():
    global tempo_restante, sessao_ativa, main_root
    while sessao_ativa and tempo_restante > 0:
        time.sleep(1)
        tempo_restante -= 1
        if label_tempo:
            minutos = tempo_restante // 60
            label_tempo.config(text=f"⏱ {minutos} min restantes")
    if sessao_ativa:
        sessao_ativa = False
        if main_root:
            main_root.after(0, lambda: [main_root.destroy(), mostrar_tela_login()])
        messagebox.showwarning("Sessão Expirada", "⏰ Sua sessão de 1 hora expirou!\nFaça login novamente.")

def mostrar_tela_login():
    global login_root, entry_key
    login_root = tk.Tk()
    login_root.title("🔐 LOGIN - TL COMMUNITY")
    login_root.geometry("400x300")
    login_root.configure(bg="#0a0a0f")
    login_root.resizable(False, False)
    login_root.eval('tk::PlaceWindow . center')
    tk.Label(login_root, text="TL COMMUNITY", font=("Segoe UI", 22, "bold"),
             bg="#0a0a0f", fg="#3498db").pack(pady=30)
    tk.Label(login_root, text="Insira sua chave de acesso:", font=("Segoe UI", 11),
             bg="#0a0a0f", fg="#7f8c8d").pack(pady=5)
    entry_key = tk.Entry(login_root, font=("Segoe UI", 12), bg="#1a1a2e", fg="#ecf0f1",
                         insertbackground="white", relief="flat", bd=0, width=30)
    entry_key.pack(pady=10)
    entry_key.focus()
    btn_login = tk.Button(login_root, text="ENTRAR", font=("Segoe UI", 11, "bold"),
                         bg="#3498db", fg="white", relief="flat", bd=0,
                         padx=30, pady=8, command=fazer_login)
    btn_login.pack(pady=5)
    tk.Label(login_root, text="Chave: MCROPRIV-001-1h-kvlak", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#555566").pack(pady=15)
    tk.Label(login_root, text="⏱ Válida por 1 hora", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#f39c12").pack()
    btn_sair = tk.Button(login_root, text="Sair", font=("Segoe UI", 9),
                        bg="#e74c3c", fg="white", relief="flat", bd=0,
                        padx=20, pady=4, command=lambda: sys.exit(0))
    btn_sair.pack(pady=15)
    login_root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    login_root.mainloop()

# ==================================================
# INTERFACE PRINCIPAL
# ==================================================
def criar_interface_principal():
    global main_root, delay_litefoot_label, delay_correr_label, recoil_intensidade_label, recoil_delay_label
    global btn_tecla1, btn_tecla2, btn_tecla3, btn_tecla4
    global frame_litefoot, frame_correr, frame_recoil, frame_mira
    global correr_status_label, recoil_status_label, litefoot_status_label, mira_status_label
    global btn_correr_toggle, btn_recoil_toggle, btn_litefoot_toggle, btn_mira_toggle
    global btn_litefoot, btn_correr, btn_recoil, btn_mira
    global btn_cor_mira, btn_cor_borda, label_tamanho, combo_estilo
    global label_tempo

    main_root = tk.Tk()
    main_root.title("TL COMMUNITY")
    main_root.geometry("650x520")
    main_root.minsize(600, 460)
    main_root.configure(bg="#0a0a0f")

    label_tempo = tk.Label(main_root, text="⏱ 60 min restantes", font=("Segoe UI", 9, "bold"),
                          bg="#0a0a0f", fg="#f39c12")
    label_tempo.place(relx=0.95, rely=0.02, anchor="ne")

    main_frame = tk.Frame(main_root, bg="#0a0a0f")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Menu
    menu_frame = tk.Frame(main_frame, bg="#12121a", width=180)
    menu_frame.pack(side=tk.LEFT, fill=tk.Y)
    menu_frame.pack_propagate(False)
    logo_frame = tk.Frame(menu_frame, bg="#12121a")
    logo_frame.pack(fill=tk.X, pady=(20, 15))
    tk.Label(logo_frame, text="TL", font=("Segoe UI", 18, "bold"),
             bg="#12121a", fg="#3498db").pack()
    tk.Label(logo_frame, text="COMMUNITY", font=("Segoe UI", 9, "bold"),
             bg="#12121a", fg="#666688").pack()
    ttk.Separator(menu_frame, orient='horizontal').pack(fill='x', padx=15, pady=10)
    btn_litefoot = tk.Button(menu_frame, text="⚡ Litefoot", font=("Segoe UI", 10),
                            bg="#2c3e50", fg="#ecf0f1", relief="flat", bd=0,
                            anchor="w", padx=20, pady=10,
                            command=lambda: mudar_aba("litefoot"))
    btn_litefoot.pack(fill=tk.X, padx=12, pady=3)
    btn_correr = tk.Button(menu_frame, text="🏃 Correr", font=("Segoe UI", 10),
                          bg="#1a1a2e", fg="#7f8c8d", relief="flat", bd=0,
                          anchor="w", padx=20, pady=10,
                          command=lambda: mudar_aba("correr"))
    btn_correr.pack(fill=tk.X, padx=12, pady=3)
    btn_recoil = tk.Button(menu_frame, text="🎯 Recoil", font=("Segoe UI", 10),
                          bg="#1a1a2e", fg="#7f8c8d", relief="flat", bd=0,
                          anchor="w", padx=20, pady=10,
                          command=lambda: mudar_aba("recoil"))
    btn_recoil.pack(fill=tk.X, padx=12, pady=3)
    btn_mira = tk.Button(menu_frame, text="🎯 Mira", font=("Segoe UI", 10),
                        bg="#1a1a2e", fg="#7f8c8d", relief="flat", bd=0,
                        anchor="w", padx=20, pady=10,
                        command=lambda: mudar_aba("mira"))
    btn_mira.pack(fill=tk.X, padx=12, pady=3)
    tk.Label(menu_frame, text="", bg="#12121a").pack(expand=True)

    content_frame = tk.Frame(main_frame, bg="#0a0a0f")
    content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # LITEFOOT
    frame_litefoot = tk.Frame(content_frame, bg="#0a0a0f")
    frame_litefoot.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
    tk.Label(frame_litefoot, text="LITEFOOT", font=("Segoe UI", 20, "bold"),
             bg="#0a0a0f", fg="#ecf0f1").pack(anchor="center", pady=(0, 5))
    tk.Label(frame_litefoot, text="Executa ao soltar o botão direito do mouse", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#666688").pack(anchor="center", pady=(0, 15))
    tk.Label(frame_litefoot, text="SEQUÊNCIA DE TECLAS", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center")
    teclas_frame = tk.Frame(frame_litefoot, bg="#0a0a0f")
    teclas_frame.pack(anchor="center", pady=8)
    btn_tecla1 = tk.Button(teclas_frame, text=tecla1, font=("Segoe UI", 14, "bold"),
                          bg="#1a1a2e", fg="#ecf0f1", relief="flat", bd=0,
                          width=5, height=1,
                          command=lambda: editar_tecla(tecla1, 1))
    btn_tecla1.grid(row=0, column=0, padx=3)
    tk.Label(teclas_frame, text="+", font=("Segoe UI", 14, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").grid(row=0, column=1, padx=5)
    btn_tecla2 = tk.Button(teclas_frame, text=tecla2, font=("Segoe UI", 14, "bold"),
                          bg="#1a1a2e", fg="#ecf0f1", relief="flat", bd=0,
                          width=5, height=1,
                          command=lambda: editar_tecla(tecla2, 2))
    btn_tecla2.grid(row=0, column=2, padx=3)
    tk.Label(teclas_frame, text="+", font=("Segoe UI", 14, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").grid(row=0, column=3, padx=5)
    btn_tecla3 = tk.Button(teclas_frame, text=tecla3, font=("Segoe UI", 14, "bold"),
                          bg="#1a1a2e", fg="#ecf0f1", relief="flat", bd=0,
                          width=5, height=1,
                          command=lambda: editar_tecla(tecla3, 3))
    btn_tecla3.grid(row=0, column=4, padx=3)
    tk.Label(teclas_frame, text="=", font=("Segoe UI", 14, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").grid(row=0, column=5, padx=5)
    btn_tecla4 = tk.Button(teclas_frame, text=tecla4, font=("Segoe UI", 14, "bold"),
                          bg="#1a1a2e", fg="#ecf0f1", relief="flat", bd=0,
                          width=5, height=1,
                          command=lambda: editar_tecla(tecla4, 4))
    btn_tecla4.grid(row=0, column=6, padx=3)

    tk.Label(frame_litefoot, text="ATRASO (ms)", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center", pady=(15, 5))
    slider_container = tk.Frame(frame_litefoot, bg="#0a0a0f")
    slider_container.pack(anchor="center", pady=4)
    slider = tk.Scale(
        slider_container,
        from_=1,
        to=100,
        orient=tk.HORIZONTAL,
        length=320,
        bg="#0a0a0f",
        fg="#3498db",
        highlightthickness=0,
        troughcolor="#1a1a2e",
        sliderlength=18,
        command=atualizar_delay_litefoot
    )
    slider.set(20)
    slider.pack(side=tk.LEFT)
    delay_litefoot_label = tk.Label(
        slider_container,
        text="20 ms",
        font=("Segoe UI", 12, "bold"),
        bg="#0a0a0f",
        fg="#ecf0f1"
    )
    delay_litefoot_label.pack(side=tk.LEFT, padx=(15, 0))
    btn_litefoot_toggle = tk.Button(frame_litefoot, text="▶ ATIVAR", font=("Segoe UI", 10, "bold"),
                                   bg="#2c3e50", fg="#ecf0f1", relief="flat", bd=0,
                                   padx=35, pady=10, command=toggle_litefoot)
    btn_litefoot_toggle.pack(anchor="center", pady=(15, 8))
    litefoot_status_label = tk.Label(frame_litefoot, text="● DESATIVADO", font=("Segoe UI", 10, "bold"),
                                    bg="#0a0a0f", fg="#e74c3c")
    litefoot_status_label.pack(anchor="center")

    # CORRER
    frame_correr = tk.Frame(content_frame, bg="#0a0a0f")
    frame_correr.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
    frame_correr.pack_forget()
    tk.Label(frame_correr, text="CORRER", font=("Segoe UI", 20, "bold"),
             bg="#0a0a0f", fg="#ecf0f1").pack(anchor="center", pady=(0, 5))
    tk.Label(frame_correr, text="Ativa scroll automático do mouse", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#666688").pack(anchor="center", pady=(0, 15))
    tk.Label(frame_correr, text="VELOCIDADE (ms)", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center")
    slider_correr_container = tk.Frame(frame_correr, bg="#0a0a0f")
    slider_correr_container.pack(anchor="center", pady=8)
    slider_correr = tk.Scale(
        slider_correr_container,
        from_=100,
        to=500,
        orient=tk.HORIZONTAL,
        length=320,
        bg="#0a0a0f",
        fg="#3498db",
        highlightthickness=0,
        troughcolor="#1a1a2e",
        sliderlength=18,
        command=atualizar_delay_correr
    )
    slider_correr.set(320)
    slider_correr.pack(side=tk.LEFT)
    delay_correr_label = tk.Label(
        slider_correr_container,
        text="320 ms",
        font=("Segoe UI", 12, "bold"),
        bg="#0a0a0f",
        fg="#ecf0f1"
    )
    delay_correr_label.pack(side=tk.LEFT, padx=(15, 0))
    btn_correr_toggle = tk.Button(frame_correr, text="▶ ATIVAR", font=("Segoe UI", 10, "bold"),
                                 bg="#2c3e50", fg="#ecf0f1", relief="flat", bd=0,
                                 padx=35, pady=10, command=toggle_correr)
    btn_correr_toggle.pack(anchor="center", pady=(15, 8))
    correr_status_label = tk.Label(frame_correr, text="● DESATIVADO", font=("Segoe UI", 10, "bold"),
                                  bg="#0a0a0f", fg="#e74c3c")
    correr_status_label.pack(anchor="center")

    # RECOIL
    frame_recoil = tk.Frame(content_frame, bg="#0a0a0f")
    frame_recoil.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
    frame_recoil.pack_forget()
    tk.Label(frame_recoil, text="RECOIL", font=("Segoe UI", 20, "bold"),
             bg="#0a0a0f", fg="#ecf0f1").pack(anchor="center", pady=(0, 5))
    tk.Label(frame_recoil, text="Compensa o recuo ao atirar", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#666688").pack(anchor="center", pady=(0, 15))
    tk.Label(frame_recoil, text="INTENSIDADE", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center")
    slider_int_container = tk.Frame(frame_recoil, bg="#0a0a0f")
    slider_int_container.pack(anchor="center", pady=5)
    slider_recoil_int = tk.Scale(
        slider_int_container,
        from_=1,
        to=200,
        orient=tk.HORIZONTAL,
        length=320,
        bg="#0a0a0f",
        fg="#3498db",
        highlightthickness=0,
        troughcolor="#1a1a2e",
        sliderlength=18,
        command=atualizar_recoil_intensidade
    )
    slider_recoil_int.set(110)
    slider_recoil_int.pack(side=tk.LEFT)
    recoil_intensidade_label = tk.Label(
        slider_int_container,
        text="110",
        font=("Segoe UI", 12, "bold"),
        bg="#0a0a0f",
        fg="#ecf0f1"
    )
    recoil_intensidade_label.pack(side=tk.LEFT, padx=(15, 0))
    tk.Label(frame_recoil, text="DELAY (ms)", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center", pady=(15, 5))
    slider_delay_container = tk.Frame(frame_recoil, bg="#0a0a0f")
    slider_delay_container.pack(anchor="center", pady=5)
    slider_recoil_delay = tk.Scale(
        slider_delay_container,
        from_=1,
        to=150,
        orient=tk.HORIZONTAL,
        length=320,
        bg="#0a0a0f",
        fg="#3498db",
        highlightthickness=0,
        troughcolor="#1a1a2e",
        sliderlength=18,
        command=atualizar_recoil_delay
    )
    slider_recoil_delay.set(55)
    slider_recoil_delay.pack(side=tk.LEFT)
    recoil_delay_label = tk.Label(
        slider_delay_container,
        text="55 ms",
        font=("Segoe UI", 12, "bold"),
        bg="#0a0a0f",
        fg="#ecf0f1"
    )
    recoil_delay_label.pack(side=tk.LEFT, padx=(15, 0))
    btn_recoil_toggle = tk.Button(frame_recoil, text="▶ ATIVAR", font=("Segoe UI", 10, "bold"),
                                 bg="#2c3e50", fg="#ecf0f1", relief="flat", bd=0,
                                 padx=35, pady=10, command=toggle_recoil)
    btn_recoil_toggle.pack(anchor="center", pady=(15, 8))
    recoil_status_label = tk.Label(frame_recoil, text="● DESATIVADO", font=("Segoe UI", 10, "bold"),
                                  bg="#0a0a0f", fg="#e74c3c")
    recoil_status_label.pack(anchor="center")

    # MIRA
    frame_mira = tk.Frame(content_frame, bg="#0a0a0f")
    frame_mira.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
    frame_mira.pack_forget()
    tk.Label(frame_mira, text="MIRA PERSONALIZADA", font=("Segoe UI", 20, "bold"),
             bg="#0a0a0f", fg="#ecf0f1").pack(anchor="center", pady=(0, 15))
    tk.Label(frame_mira, text="ESTILO DA MIRA:", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center")
    combo_estilo = ttk.Combobox(frame_mira, values=["Ponto", "Ponto com Borda", "Círculo", "Cruz CS 1.6", "Ponto + Cruz"],
                                font=("Segoe UI", 11), state="readonly")
    combo_estilo.set("Ponto")
    combo_estilo.pack(anchor="center", pady=5)
    combo_estilo.bind("<<ComboboxSelected>>", lambda e: atualizar_estilo_mira(combo_estilo.get()))
    frame_cores = tk.Frame(frame_mira, bg="#0a0a0f")
    frame_cores.pack(anchor="center", pady=10)
    tk.Label(frame_cores, text="COR DA MIRA:", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#7f8c8d").pack(side=tk.LEFT, padx=5)
    btn_cor_mira = tk.Button(frame_cores, width=3, height=1, bg="#00ff00",
                            relief="flat", bd=2, command=escolher_cor_mira)
    btn_cor_mira.pack(side=tk.LEFT, padx=5)
    tk.Label(frame_cores, text="COR DA BORDA:", font=("Segoe UI", 9),
             bg="#0a0a0f", fg="#7f8c8d").pack(side=tk.LEFT, padx=5)
    btn_cor_borda = tk.Button(frame_cores, width=3, height=1, bg="#000000",
                            relief="flat", bd=2, command=escolher_cor_borda)
    btn_cor_borda.pack(side=tk.LEFT, padx=5)
    tk.Label(frame_mira, text="TAMANHO:", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center", pady=(10, 2))
    slider_tamanho = tk.Scale(frame_mira, from_=5, to=80, orient=tk.HORIZONTAL,
                              length=250, bg="#0a0a0f", fg="#3498db",
                              highlightthickness=0, troughcolor="#1a1a2e",
                              sliderlength=18, command=atualizar_tamanho_mira)
    slider_tamanho.set(20)
    slider_tamanho.pack(anchor="center", pady=2)
    label_tamanho = tk.Label(frame_mira, text="20px", font=("Segoe UI", 10),
                            bg="#0a0a0f", fg="#ecf0f1")
    label_tamanho.pack(anchor="center")
    tk.Label(frame_mira, text="USE AS SETAS DO TECLADO PARA MOVER", font=("Segoe UI", 9, "bold"),
             bg="#0a0a0f", fg="#7f8c8d").pack(anchor="center", pady=(10, 5))
    tk.Label(frame_mira, text="⬆ ⬇ ⬅ ➡", font=("Segoe UI", 14),
             bg="#0a0a0f", fg="#666688").pack(anchor="center")
    btn_mira_toggle = tk.Button(frame_mira, text="▶ ATIVAR", font=("Segoe UI", 10, "bold"),
                               bg="#2c3e50", fg="#ecf0f1", relief="flat", bd=0,
                               padx=35, pady=10, command=toggle_mira)
    btn_mira_toggle.pack(anchor="center", pady=(15, 8))
    mira_status_label = tk.Label(frame_mira, text="● DESATIVADO", font=("Segoe UI", 10, "bold"),
                                bg="#0a0a0f", fg="#e74c3c")
    mira_status_label.pack(anchor="center")

    # INICIA MONITORES
    threading.Thread(target=check_right_button, daemon=True).start()
    threading.Thread(target=check_toggle_delete, daemon=True).start()
    threading.Thread(target=check_recoil, daemon=True).start()

    main_root.protocol("WM_DELETE_WINDOW", fechar)
    main_root.mainloop()

# ==================================================
# FUNÇÕES DE INTERFACE
# ==================================================
def atualizar_delay_litefoot(valor):
    global delay_litefoot, delay_litefoot_label
    delay_litefoot = int(float(valor))
    if delay_litefoot_label:
        delay_litefoot_label.config(text=f"{delay_litefoot} ms")

def atualizar_delay_correr(valor):
    global delay_correr, delay_correr_label
    delay_correr = int(float(valor))
    if delay_correr_label:
        delay_correr_label.config(text=f"{delay_correr} ms")

def atualizar_recoil_intensidade(valor):
    global recoil_intensidade, recoil_intensidade_label
    recoil_intensidade = int(float(valor))
    if recoil_intensidade_label:
        recoil_intensidade_label.config(text=f"{recoil_intensidade}")

def atualizar_recoil_delay(valor):
    global recoil_delay, recoil_delay_label
    recoil_delay = int(float(valor))
    if recoil_delay_label:
        recoil_delay_label.config(text=f"{recoil_delay} ms")

def editar_tecla(atual, posicao):
    janela = tk.Toplevel(main_root)
    janela.title(f"Editar Tecla {posicao}")
    janela.geometry("320x180")
    janela.configure(bg="#1a1a2e")
    janela.transient(main_root)
    janela.grab_set()
    tk.Label(janela, text=f"Tecla {posicao}: {atual}", font=("Segoe UI", 12),
             bg="#1a1a2e", fg="#ecf0f1").pack(pady=12)
    tk.Label(janela, text="Pressione a nova tecla:", font=("Segoe UI", 10),
             bg="#1a1a2e", fg="#7f8c8d").pack()
    nova = tk.StringVar()
    label = tk.Label(janela, text="Aguardando...", font=("Segoe UI", 11, "bold"),
                     bg="#1a1a2e", fg="#3498db")
    label.pack(pady=10)
    def capturar(event):
        nome = event.keysym
        if len(nome) == 1:
            nova.set(nome.upper())
        else:
            nova.set(nome)
        label.config(text=f"Tecla: {nova.get()}")
    janela.bind("<Key>", capturar)
    janela.focus_set()
    def salvar():
        if nova.get():
            atualizar_tecla(nova.get(), posicao)
            janela.destroy()
    def cancelar():
        janela.destroy()
    frame = tk.Frame(janela, bg="#1a1a2e")
    frame.pack(pady=15)
    tk.Button(frame, text="SALVAR", font=("Segoe UI", 10, "bold"),
              bg="#27ae60", fg="white", padx=25, pady=6, command=salvar).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="CANCELAR", font=("Segoe UI", 10, "bold"),
              bg="#e74c3c", fg="white", padx=25, pady=6, command=cancelar).pack(side=tk.LEFT, padx=5)

def atualizar_tecla(nova, posicao):
    global tecla1, tecla2, tecla3, tecla4, btn_tecla1, btn_tecla2, btn_tecla3, btn_tecla4
    if posicao == 1:
        tecla1 = nova
        if btn_tecla1:
            btn_tecla1.config(text=tecla1)
    elif posicao == 2:
        tecla2 = nova
        if btn_tecla2:
            btn_tecla2.config(text=tecla2)
    elif posicao == 3:
        tecla3 = nova
        if btn_tecla3:
            btn_tecla3.config(text=tecla3)
    elif posicao == 4:
        tecla4 = nova
        if btn_tecla4:
            btn_tecla4.config(text=tecla4)

def mudar_aba(opcao):
    global frame_litefoot, frame_correr, frame_recoil, frame_mira
    global btn_litefoot, btn_correr, btn_recoil, btn_mira
    btn_litefoot.config(bg="#1a1a2e", fg="#7f8c8d")
    btn_correr.config(bg="#1a1a2e", fg="#7f8c8d")
    btn_recoil.config(bg="#1a1a2e", fg="#7f8c8d")
    btn_mira.config(bg="#1a1a2e", fg="#7f8c8d")
    frame_litefoot.pack_forget()
    frame_correr.pack_forget()
    frame_recoil.pack_forget()
    frame_mira.pack_forget()
    if opcao == "litefoot":
        frame_litefoot.pack(fill=tk.BOTH, expand=True)
        btn_litefoot.config(bg="#2c3e50", fg="#ecf0f1")
    elif opcao == "correr":
        frame_correr.pack(fill=tk.BOTH, expand=True)
        btn_correr.config(bg="#2c3e50", fg="#ecf0f1")
    elif opcao == "recoil":
        frame_recoil.pack(fill=tk.BOTH, expand=True)
        btn_recoil.config(bg="#2c3e50", fg="#ecf0f1")
    elif opcao == "mira":
        frame_mira.pack(fill=tk.BOTH, expand=True)
        btn_mira.config(bg="#2c3e50", fg="#ecf0f1")

def fechar():
    global running, main_root, sessao_ativa
    running = False
    sessao_ativa = False
    if main_root:
        main_root.destroy()
    sys.exit(0)

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    mostrar_tela_login()