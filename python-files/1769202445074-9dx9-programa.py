import sys
import os
import zipfile
import ctypes
import webbrowser
import colorsys

# --- SISTEMA DE PROTEÇÃO DE BIBLIOTECAS ---
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageChops, ImageEnhance
    import numpy as np
    import imageio.v3 as iio
except ImportError:
    print("Erro: Bibliotecas faltando. Instale Pillow, numpy e imageio.")
    sys.exit()

# --- AJUSTE DE RESOLUÇÃO WINDOWS ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# --- DICIONÁRIO DE IDIOMAS ---
LANGS = {
    "PT": {
        "cfg": "CONFIGURAÇÃO", "font": "📁 PASTA DE FONTES", "fx": "Efeito Mobitec:", 
        "vel": "Velocidade:", "update": "🔄 ATUALIZAR LETREIRO", "final": "MODELO DOS ÔNIBUS",
        "led": "Cor do LED:", "export": "📦 EXPORTAR MOD (.SCS)", "success": "Mod criado com sucesso!",
        "theme": "TEMA DO LAYOUT:", "site": "Site Oficial", "compat": "Mods compatível com os jogos"
    },
    "EN": {
        "cfg": "SETTINGS", "font": "📁 FONT FOLDER", "fx": "Mobitec Effect:", 
        "vel": "Scroll Speed:", "update": "🔄 UPDATE DISPLAY", "final": "BUS MODELS",
        "led": "LED Color:", "export": "📦 EXPORT MOD (.SCS)", "success": "Mod created successfully!",
        "theme": "LAYOUT THEME:", "site": "Official Site", "compat": "Mods compatible with games"
    },
    "ES": {
        "cfg": "CONFIGURACIÓN", "font": "📁 CARPETA DE FUENTES", "fx": "Efecto Mobitec:", 
        "vel": "Velocidad:", "update": "🔄 ACTUALIZAR LETRERO", "final": "MODELO DE AUTOBUSES",
        "led": "Color del LED:", "export": "📦 EXPORTAR MOD (.SCS)", "success": "¡Mod criado con éxito!",
        "theme": "TEMA DEL DISEÑO:", "site": "Sitio Oficial", "compat": "Mods compatible con juegos"
    }
}

# --- DEFINIÇÃO DE TEMAS ---
TEMAS = {
    "Preto":      {"bg": "#050505", "panel": "#121212", "text": "white"},
    "Branco":     {"bg": "#F0F0F0", "panel": "#FFFFFF", "text": "#333"},
    "Cinza":      {"bg": "#2B2B2B", "panel": "#3C3F41", "text": "#EEE"},
    "Azul Claro": {"bg": "#E3F2FD", "panel": "#BBDEFB", "text": "#0D47A1"}
}

C_BLUE, C_GREEN, C_BRIGHT, C_GOLD = "#0078D7", "#21A366", "#2ECC71", "#FFD700"

MODELOS_ONIBUS = {
    "Busscar 400": {"path": "jp3d/bussc400/upgrade/mobitec/texture/", "file": "Busscar Vissta Buss 400.png"},
    "Comil": {"path": "jp3d/comil/upgrade/mobitec/texture/", "file": "Comil invictus.jpg"},
    "Comil HD": {"path": "jp3d/comilhd/upgrade/mobitec/texture/", "file": "Comil Invictus HD.jpg"},
    "Modasa": {"path": "jp3d/modasa/upgrade/mobitec/texture/", "file": "modasa.png"}
}

MAPA_CORES = {"Ciano": "#00FFFF", "Laranja": "#FF8000", "Amarelo": "#FFCC00", "Branco": "#FFFFFF", "Verde": "#00FF00", "Vermelho": "#FF0000"}
MAPA_VEL = {"Lento": 3, "Normal": 7, "Rápido": 12, "Turbo": 22}
MAPA_FX = ["Rolar", "Fixo (Central)", "Piscar", "Subir"]

class JP3D_V208_CLEAN_GLOW:
    def __init__(self, root):
        self.root = root
        self.root.title("JP3D MODS - LETREIRO EDIT | BR SKINS")
        self.root.geometry("1600x900")

        self.pos_x, self.pos_y = 0, 36
        self.flash_count = 0
        self.flash_visible = True
        self.pasta_fontes = ""
        self.bus_frames = []
        self.pulse = True
        self.lang_atual = "PT"
        
        # Variáveis do Ciclo RGB da Logo Principal
        self.logo_base = None
        self.logo_hue = 0.0

        # Variáveis do Glow das Logos Laterais (ATS/ETS2)
        self.ats_base = None
        self.ets2_base = None
        self.glow_val = 1.0
        self.glow_dir = 0.03

        self.selecao_mods = {nome: tk.BooleanVar(value=True) for nome in MODELOS_ONIBUS.keys()}

        self.root.columnconfigure(0, weight=0, minsize=360)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0, minsize=360)
        self.root.rowconfigure(0, weight=1)

        self.montar_ui()
        self.mudar_tema("Preto") 
        self.root.after(800, self.iniciar_motores)

    def montar_ui(self):
        # --- COLUNA ESQUERDA (EDIÇÃO) ---
        self.f_esq = tk.Frame(self.root, width=360, padx=20)
        self.f_esq.grid(row=0, column=0, sticky="nsew"); self.f_esq.grid_propagate(False)

        self.lbl_cfg = tk.Label(self.f_esq, text="CONFIGURAÇÃO", font=("bold", 11), fg=C_BLUE)
        self.lbl_cfg.pack(pady=(30, 10))
        
        self.btn_f_sel = tk.Button(self.f_esq, text="📁 PASTA DE FONTES", bg=C_BLUE, fg="white", command=self.abrir_fontes, relief="flat")
        self.btn_f_sel.pack(fill="x", pady=5)
        self.cb_font = ttk.Combobox(self.f_esq, state="readonly"); self.cb_font.pack(fill="x", pady=5)
        
        self.lbl_fx_t = tk.Label(self.f_esq, text="Efeito Mobitec:"); self.lbl_fx_t.pack(anchor="w", pady=(10,0))
        self.cb_fx = ttk.Combobox(self.f_esq, values=MAPA_FX, state="readonly"); self.cb_fx.set("Rolar"); self.cb_fx.pack(fill="x")

        self.lbl_vel_t = tk.Label(self.f_esq, text="Velocidade:"); self.lbl_vel_t.pack(anchor="w", pady=(10,0))
        self.cb_vel = ttk.Combobox(self.f_esq, values=list(MAPA_VEL.keys()), state="readonly"); self.cb_vel.set("Normal"); self.cb_vel.pack(fill="x")

        self.entradas = [tk.Entry(self.f_esq, bg="#1A1A1A", fg="white", bd=0, insertbackground="white", font=("Arial", 11)) for _ in range(5)]
        for e in self.entradas: e.pack(fill="x", pady=2, ipady=8)
        self.entradas[0].insert(0, "BR SKINS")

        self.btn_upd = tk.Button(self.f_esq, text="🔄 ATUALIZAR LETREIRO", bg=C_GREEN, fg="white", font=("bold", 10), command=self.reset_pos, relief="flat")
        self.btn_upd.pack(fill="x", pady=15, ipady=12)

        # --- LOGO PRINCIPAL (Sem quadro azul) ---
        # O fundo será ajustado pelo tema dinamicamente
        self.lbl_logo = tk.Label(self.f_esq, height=95, text="LOGO JP3D", fg="#333", font=("bold", 10))
        self.lbl_logo.pack(fill="x", pady=(25, 10))

        self.lbl_site = tk.Label(self.f_esq, text="http://br.jp3dmods.com", font=("Arial", 9, "underline"), cursor="hand2")
        self.lbl_site.pack(pady=2); self.lbl_site.bind("<Button-1>", lambda e: webbrowser.open_new("http://br.jp3dmods.com"))

        # --- COLUNA CENTRAL ---
        self.f_mid = tk.Frame(self.root, padx=10)
        self.f_mid.grid(row=0, column=1, sticky="nsew")
        self.visor = tk.Label(self.f_mid, bg="black", bd=1, highlightthickness=1, highlightbackground=C_BLUE)
        self.visor.pack(expand=True, fill="both", pady=(40, 0))
        self.sc_z = ttk.Scale(self.f_mid, from_=100, to=500, orient="horizontal"); self.sc_z.set(100); self.sc_z.pack(fill="x", pady=20)

        # --- COLUNA DIREITA ---
        self.f_dir = tk.Frame(self.root, width=360, padx=20)
        self.f_dir.grid(row=0, column=2, sticky="nsew"); self.f_dir.grid_propagate(False)

        self.lbl_lang_t = tk.Label(self.f_dir, text="LANGUAGE / IDIOMA", font=("Arial", 7, "bold"))
        self.lbl_lang_t.pack(pady=(20, 5))
        f_l = tk.Frame(self.f_dir); f_l.pack(fill="x", pady=5)
        self.btn_pt = tk.Button(f_l, text="PT", width=8, command=lambda: self.mudar_idioma("PT"), relief="flat")
        self.btn_pt.pack(side="left", expand=True, padx=2)
        self.btn_en = tk.Button(f_l, text="EN", width=8, command=lambda: self.mudar_idioma("EN"), relief="flat")
        self.btn_en.pack(side="left", expand=True, padx=2)
        self.btn_es = tk.Button(f_l, text="ES", width=8, command=lambda: self.mudar_idioma("ES"), relief="flat")
        self.btn_es.pack(side="left", expand=True, padx=2)

        self.lbl_tema_txt = tk.Label(self.f_dir, text="TEMA DO LAYOUT:", font=("Arial", 8, "bold"))
        self.lbl_tema_txt.pack(pady=(15, 2))
        self.cb_tema = ttk.Combobox(self.f_dir, values=list(TEMAS.keys()), state="readonly")
        self.cb_tema.set("Preto"); self.cb_tema.pack(fill="x", pady=5)
        self.cb_tema.bind("<<ComboboxSelected>>", lambda e: self.mudar_tema(self.cb_tema.get()))

        self.lbl_fin = tk.Label(self.f_dir, text="MODELO DOS ÔNIBUS", fg=C_GOLD, font=("bold", 12))
        self.lbl_fin.pack(pady=(25, 10))
        
        self.f_chk = tk.Frame(self.f_dir); self.f_chk.pack(fill="x", pady=5)
        self.chk_btns = []
        for nome in MODELOS_ONIBUS.keys():
            cb = tk.Checkbutton(self.f_chk, text=nome, variable=self.selecao_mods[nome], font=("Arial", 10))
            cb.pack(anchor="w"); self.chk_btns.append(cb)

        self.lbl_led_c = tk.Label(self.f_dir, text="Cor do LED:"); self.lbl_led_c.pack(anchor="w", pady=(15, 0))
        self.cb_cor = ttk.Combobox(self.f_dir, values=list(MAPA_CORES.keys()), state="readonly"); self.cb_cor.current(0); self.cb_cor.pack(fill="x", pady=5)

        self.lbl_compat = tk.Label(self.f_dir, text="Mods compátivel com os jogos", font=("Arial", 8, "bold"))
        self.lbl_compat.pack(pady=(20, 5))
        self.f_games = tk.Frame(self.f_dir); self.f_games.pack(fill="x", pady=5)
        self.lbl_ats = tk.Label(self.f_games); self.lbl_ats.pack(side="left", expand=True, fill="both", padx=2)
        self.lbl_ets2 = tk.Label(self.f_games); self.lbl_ets2.pack(side="left", expand=True, fill="both", padx=2)

        self.f_spacer = tk.Frame(self.f_dir); self.f_spacer.pack(expand=True, fill="both")
        self.f_anim = tk.Frame(self.f_dir, height=60); self.f_anim.pack(fill="x")
        self.lbl_g8 = tk.Label(self.f_anim); self.lbl_g8.place(x=-150, y=0)

        self.bar = ttk.Progressbar(self.f_dir, mode='determinate', length=280); self.bar.pack(pady=5)
        self.btn_exp = tk.Button(self.f_dir, text="📦 EXPORTAR MOD (.SCS)", bg=C_GREEN, fg="white", font=("bold", 12), command=self.exportar, relief="flat")
        self.btn_exp.pack(fill="x", pady=(5, 40), ipady=15)

    def mudar_tema(self, nome_tema):
        t = TEMAS[nome_tema]
        self.root.configure(bg=t["bg"])
        for f in [self.f_esq, self.f_mid, self.f_dir, self.f_chk, self.f_anim, self.btn_pt.master, self.f_games, self.f_spacer]:
            f.configure(bg=t["panel"])
        # Adicionado lbl_logo para mudar o fundo junto com o painel
        for lbl in [self.lbl_tema_txt, self.lbl_cfg, self.lbl_fx_t, self.lbl_vel_t, self.lbl_site, self.lbl_fin, self.lbl_led_c, self.lbl_lang_t, self.lbl_ats, self.lbl_ets2, self.lbl_compat, self.lbl_logo]:
            lbl.configure(bg=t["panel"], fg=t["text"] if lbl not in [self.lbl_cfg, self.lbl_site, self.lbl_fin] else lbl.cget("fg"))
        for cb in self.chk_btns:
            cb.configure(bg=t["panel"], fg=t["text"], selectcolor=t["panel"], activebackground=t["panel"], activeforeground=C_GOLD)
        self.mudar_idioma(self.lang_atual)

    def loop_logo_rgb(self):
        if self.logo_base:
            self.logo_hue = (self.logo_hue + 0.01) % 1.0
            rgb = colorsys.hsv_to_rgb(self.logo_hue, 0.7, 1.0)
            cor_tint = tuple(int(c * 255) for c in rgb)
            overlay = Image.new("RGB", self.logo_base.size, cor_tint)
            img_tinted = ImageChops.multiply(self.logo_base.convert("RGB"), overlay)
            if self.logo_base.mode == "RGBA":
                img_tinted.putalpha(self.logo_base.split()[-1])
            self.logo_tk = ImageTk.PhotoImage(img_tinted)
            self.lbl_logo.config(image=self.logo_tk)
        self.root.after(100, self.loop_logo_rgb)

    # NOVO: Loop de brilho para as logos dos jogos
    def loop_games_glow(self):
        self.glow_val += self.glow_dir
        if self.glow_val >= 1.2 or self.glow_val <= 0.8:
            self.glow_dir *= -1
        
        enhancer = ImageEnhance.Brightness
        if self.ats_base:
            img_ats = enhancer(self.ats_base).enhance(self.glow_val)
            self.ats_tk = ImageTk.PhotoImage(img_ats)
            self.lbl_ats.config(image=self.ats_tk)
        if self.ets2_base:
            img_ets = enhancer(self.ets2_base).enhance(self.glow_val)
            self.ets2_tk = ImageTk.PhotoImage(img_ets)
            self.lbl_ets2.config(image=self.ets2_tk)
            
        self.root.after(50, self.loop_games_glow)

    def mudar_idioma(self, lang):
        self.lang_atual = lang; L = LANGS[lang]
        self.lbl_tema_txt.config(text=L["theme"]); self.lbl_cfg.config(text=L["cfg"])
        self.btn_f_sel.config(text=L["font"]); self.lbl_fx_t.config(text=L["fx"])
        self.lbl_vel_t.config(text=L["vel"]); self.btn_upd.config(text=L["update"])
        self.lbl_fin.config(text=L["final"]); self.lbl_led_c.config(text=L["led"])
        self.btn_exp.config(text=L["export"]); self.lbl_compat.config(text=L["compat"])
        self.btn_pt.config(bg=C_BLUE if lang == "PT" else "#333", fg="white")
        self.btn_en.config(bg=C_BLUE if lang == "EN" else "#333", fg="white")
        self.btn_es.config(bg=C_BLUE if lang == "ES" else "#333", fg="white")

    def iniciar_motores(self):
        self.carregar_recursos(); self.loop_principal(); self.animar_botao(); 
        self.loop_logo_rgb(); self.loop_games_glow() # Inicia os dois efeitos

    def loop_principal(self):
        self.root.after(45, self.loop_principal)
        dw = self.visor.winfo_width()
        if dw < 30: return 
        fx, vel = self.cb_fx.get(), MAPA_VEL.get(self.cb_vel.get(), 7)
        if fx == "Rolar":
            self.pos_x -= vel; self.pos_y, self.flash_visible = 36, True
            if self.pos_x < -12000: self.pos_x = 4096
        elif fx == "Fixo (Central)":
            self.pos_y, self.pos_x, self.flash_visible = 36, 0, True
        elif fx == "Piscar":
            self.flash_count += 1; self.flash_visible = (self.flash_count // 10) % 2 == 0
        elif fx == "Subir":
            self.pos_y -= 2; self.pos_x, self.flash_visible = 0, True
            if self.pos_y < -50: self.pos_y = 128
        try:
            frame = self.renderizar(self.pos_x, self.pos_y, self.flash_visible)
            dh, cw = self.visor.winfo_height(), max(10, int(dw / (self.sc_z.get() / 100.0)))
            tk_img = ImageTk.PhotoImage(frame.crop((0,0,min(4096, cw), 128)).resize((dw,dh), Image.NEAREST))
            self.visor.config(image=tk_img); self.visor.image = tk_img
        except: pass

    def renderizar(self, ox, oy, flash):
        img = Image.new("RGB", (4096, 128), (0, 0, 0))
        if not flash: return img
        draw = ImageDraw.Draw(img)
        try: fnt = ImageFont.truetype(os.path.join(self.pasta_fontes, self.cb_font.get()), 52)
        except: fnt = ImageFont.load_default()
        c_l, txts = MAPA_CORES.get(self.cb_cor.get(), "#00FFFF"), [e.get().strip() for e in self.entradas if e.get().strip()]
        cx = (4096 - (sum(draw.textlength(t, font=fnt) + 400 for t in txts) - 400)) // 2 if self.cb_fx.get() == "Fixo (Central)" else ox
        for t in txts:
            draw.text((cx, oy), t, font=fnt, fill=c_l)
            cx += int(draw.textlength(t, font=fnt)) + 400
        return img

    def carregar_recursos(self):
        p_f = os.path.join(os.getcwd(), "Fontes_JP3D")
        if os.path.exists(p_f):
            lista = [f for f in os.listdir(p_f) if f.lower().endswith(('.ttf', '.otf'))]
            if lista: self.pasta_fontes = p_f; self.cb_font['values'] = lista; self.cb_font.current(0)
        
        logo_path = "LOGO JP3DMODS 2025.png"
        if os.path.exists(logo_path):
            self.logo_base = Image.open(logo_path).resize((320, 95), Image.LANCZOS)
        
        # Carrega as bases para o efeito Glow
        if os.path.exists("american.png"):
            self.ats_base = Image.open("american.png").resize((170, 50), Image.LANCZOS)
        if os.path.exists("ets2.png"):
            self.ets2_base = Image.open("ets2.png").resize((170, 50), Image.LANCZOS)

        p_a = "bus_anim_brskins"
        if os.path.exists(p_a):
            for i in range(4):
                path = os.path.join(p_a, f"frame_{i}.png")
                if os.path.exists(path): self.bus_frames.append(ImageTk.PhotoImage(Image.open(path).resize((100, 50))))

    def exportar(self):
        marcados = [nome for nome, var in self.selecao_mods.items() if var.get()]
        if not marcados: return
        path = filedialog.asksaveasfilename(defaultextension=".scs", initialfile="Letreiro_Mods_JP3D Mods")
        if path:
            def run(s):
                if s <= 100:
                    self.bar['value'] = s
                    if self.bus_frames:
                        self.lbl_g8.config(image=self.bus_frames[(s // 5) % 4]); self.lbl_g8.place(x=int((s / 100) * 240) - 30, y=0)
                    self.root.update(); self.root.after(15, lambda: run(s + 2))
                else: self.lbl_g8.place(x=-150, y=0); self.finalizar(path, marcados)
            run(0)

    def finalizar(self, path, marcados):
        try:
            render = np.array(self.renderizar(self.pos_x, self.pos_y, True)); iio.imwrite("temp_render.dds", render, extension=".dds")
            mat_c = 'effect : "eut2.dif.anim.flipsheet.add.rfx" {\n\tadditional_ambient : 50\n\tdiffuse : { 0.8 , 0.8 , 0.8 }\n\treflection: 0.0\n\tshininess : 100\n\tspecular : { 0.01 , 0.01 , 0.01 }\n\tluminance_night : 50\n\tluminance_output : 800\n\tanimsheet_cfg_fps : 60\n\tanimsheet_cfg_frames_row : 6000\n\tanimsheet_cfg_frames_total : 6000\n\tanimsheet_frame_width : 0.00025\n\tanimsheet_frame_height : 1\n\ttexture : "texture_base" {\n\t\tsource : "/vehicle/bus/shared/letreiro/letreiro_00.tobj"\n\t}\n}\n//Generated by JP3D Mods'
            tobj_c = "眕                                    ,       /vehicle/bus/shared/letreiro/letreiro_00.dds"
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as scs:
                for n in marcados:
                    b = MODELOS_ONIBUS[n]["path"]
                    scs.write("temp_render.dds", arcname=os.path.join(b, "letreiro_00.dds"))
                    scs.writestr(os.path.join(b, "letreiro_00.mat"), mat_c); scs.writestr(os.path.join(b, "letreiro_00.tobj"), tobj_c)
                scs.writestr("manifest.sii", 'SiiNunit\n{\nmod_package : .package {\n\tdisplay_name: "JP3D Mods - Pack Personalizado"\n\tauthor: "JP3D MODS"\n}\n}')
            if os.path.exists("temp_render.dds"): os.remove("temp_render.dds")
            messagebox.showinfo("Sucesso", LANGS[self.lang_atual]["success"])
        except Exception as e: messagebox.showerror("Erro", str(e))

    def animar_botao(self):
        self.btn_upd.config(bg=C_BRIGHT if self.pulse else C_GREEN); self.pulse = not self.pulse; self.root.after(800, self.animar_botao)

    def reset_pos(self): self.pos_x, self.pos_y = 0, 36

    def abrir_fontes(self):
        p = filedialog.askdirectory()
        if p:
            self.pasta_fontes = p; self.cb_font['values'] = [f for f in os.listdir(p) if f.lower().endswith(('.ttf', '.otf'))]
            if self.cb_font['values']: self.cb_font.current(0)

if __name__ == "__main__":
    app_root = tk.Tk(); app = JP3D_V208_CLEAN_GLOW(app_root); app_root.mainloop()
