    self.grabando = False
    self.reproduciendo = False
    self.clicks = []
    self.tecla_pausa = "q"
    self.bucle_continuo = tk.BooleanVar(value=True)
    
    self.ui()
    threading.Thread(target=self.detectar_pausa, daemon=True).start()

def ui(self):
    # Título
    tk.Label(self.root, text="🔴 OPTI_RED MACRO PRO", font=("Arial", 14, "bold"), fg="#00ff00", bg="#121212").pack(pady=10)
    
    # Estado
    self.lbl_status = tk.Label(self.root, text="Estado: Listo", font=("Arial", 10), fg="#ffffff", bg="#121212")
    self.lbl_status.pack(pady=5)

    # Botones Principales
    f_btns = tk.Frame(self.root, bg="#121212")
    f_btns.pack(pady=10)
    
    self.btn_rec = tk.Button(f_btns, text="REC", font=("Arial", 10, "bold"), bg="#ff3333", fg="white", width=10, command=self.acciones_rec)
    self.btn_rec.grid(row=0, column=0, padx=5)
    
    self.btn_play = tk.Button(f_btns, text="PLAY", font=("Arial", 10, "bold"), bg="#33cc33", fg="white", width=10, command=self.reproducir)
    self.btn_play.grid(row=0, column=1, padx=5)

    # Botones de Archivo
    f_files = tk.Frame(self.root, bg="#121212")
    f_files.pack(pady=5)
    
    tk.Button(f_files, text="Save", bg="#333333", fg="white", width=10, command=self.guardar).grid(row=0, column=0, padx=5)
    tk.Button(f_files, text="Open", bg="#333333", fg="white", width=10, command=self.cargar).grid(row=0, column=1, padx=5)

    # Ajustes
    f_ajustes = tk.LabelFrame(self.root, text=" Ajustes ", fg="#00ff00", bg="#121212", padx=10, pady=10)
    f_ajustes.pack(pady=15, fill="x", padx=20)

    tk.Checkbutton(f_ajustes, text="Continuous Playback (Bucle)", variable=self.bucle_continuo, fg="white", bg="#121212", selectcolor="#121212").pack(anchor="w")
    
    f_tecla = tk.Frame(f_ajustes, bg="#121212")
    f_tecla.pack(anchor="w", pady=5)
    tk.Label(f_tecla, text="Tecla para Pausar:", fg="white", bg="#121212").grid(row=0, column=0)
    self.txt_tecla = tk.Entry(f_tecla, width=5, justify="center")
    self.txt_tecla.insert(0, self.tecla_pausa)
    self.txt_tecla.grid(row=0, column=1, padx=5)

def acciones_rec(self):
    if not self.grabando:
        self.grabando = True
        self.clicks = []
        self.btn_rec.config(text="STOP", bg="#555555")
        self.lbl_status.config(text="¡GRABANDO! Pulsa 'CTRL' en tu juego para marcar clicks.", fg="#ff3333")
        threading.Thread(target=self.bucle_grabar, daemon=True).start()
    else:
        self.grabando = False
        self.btn_rec.config(text="REC", bg="#ff3333")
        self.lbl_status.config(text=f"Macro guardada con {len(self.clicks)} pasos.", fg="#00ff00")

def bucle_grabar(self):
    while self.grabando:
        if keyboard.is_pressed('ctrl'):
            x, y = pyautogui.position()
            self.clicks.append({'x': x, 'y': y})
            self.lbl_status.config(text=f"Punto registrado: X={x}, Y={y}")
            time.sleep(0.3)  # Evita registrar doble por dejar la tecla presionada
        time.sleep(0.05)

def reproducir(self):
    if not self.clicks:
        messagebox.showwarning("Aviso", "Graba o abre una macro primero.")
        return
    if self.reproduciendo: return
    
    self.reproduciendo = True
    self.tecla_pausa = self.txt_tecla.get().strip().lower() or "q"
    self.lbl_status.config(text=f"Reproduciendo... Deja pisada la [{self.tecla_pausa.upper()}] para parar.", fg="#33cc33")
    threading.Thread(target=self.bucle_play, daemon=True).start()

def bucle_play(self):
    while self.reproduciendo:
        for p in self.clicks:
            if not self.reproduciendo: break
            pyautogui.moveTo(p['x'], p['y'], duration=0.1)
            pyautogui.click()
            time.sleep(0.3)
        if not self.bucle_continuo.get(): break
    self.reproduciendo = False
    self.lbl_status.config(text="Estado: Listo", fg="#ffffff")

def detectar_pausa(self):
    while True:
        if self.reproduciendo and keyboard.is_pressed(self.tecla_pausa):
            self.reproduciendo = False
        time.sleep(0.1)

def guardar(self):
    if not self.clicks: return
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Macro", "*.json")])
    if path:
        with open(path, 'w') as f: json.dump(self.clicks, f)

def cargar(self):
    path = filedialog.askopenfilename(filetypes=[("Macro", "*.json")])
    if path:
        with open(path, 'r') as f: self.clicks = json.load(f)
        self.lbl_status.config(text=f"Macro cargada: {len(self.clicks)} puntos.", fg="#00ff00")