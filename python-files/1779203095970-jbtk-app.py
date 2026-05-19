import tkinter as tk
from tkinter import scrolledtext, messagebox
import pyautogui
import io
import requests
import json
from PIL import ImageGrab
import threading

# Configuration - Si tu as une clé DeepSeek, mets-la ici
# Sinon, l'appli te donnera le texte à coller toi-même
DEEPSEEK_API_KEY = ""  # Optionnel - laisse vide pour utiliser le mode "copier-coller"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class ScreenCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Capture + IA - COD/COI")
        self.root.geometry("750x650")
        
        # Variables
        self.selection_start = None
        self.selection_rect = None
        self.captured_image = None
        
        # Interface
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=85, height=20, font=("Courier", 10))
        self.text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Frame des boutons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        
        self.btn_capture = tk.Button(btn_frame, text="✂️ Sélectionner une zone", command=self.start_selection, bg="#4CAF50", fg="white", padx=15, pady=5)
        self.btn_capture.pack(side=tk.LEFT, padx=5)
        
        self.btn_ocr = tk.Button(btn_frame, text="🔍 Lire le texte (OCR)", command=self.ocr_image, bg="#2196F3", fg="white", padx=15, pady=5, state=tk.DISABLED)
        self.btn_ocr.pack(side=tk.LEFT, padx=5)
        
        self.btn_ask = tk.Button(btn_frame, text="🤖 Demander à DeepSeek", command=self.ask_deepseek, bg="#FF9800", fg="white", padx=15, pady=5, state=tk.DISABLED)
        self.btn_ask.pack(side=tk.LEFT, padx=5)
        
        self.btn_copy = tk.Button(btn_frame, text="📋 Copier la réponse", command=self.copy_response, bg="#9C27B0", fg="white", padx=15, pady=5)
        self.btn_copy.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(root, text="✅ Prêt - Clique sur 'Sélectionner une zone'", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.ocr_text = ""
        self.ai_response = ""
    
    def start_selection(self):
        """Ferme la fenêtre principale et lance la sélection de zone"""
        self.root.iconify()  # Minimiser la fenêtre
        threading.Timer(0.5, self.create_selection_window).start()
    
    def create_selection_window(self):
        """Crée une fenêtre transparente pour sélectionner une zone"""
        self.selection_root = tk.Tk()
        self.selection_root.title("Sélectionne une zone")
        self.selection_root.attributes('-fullscreen', True)
        self.selection_root.attributes('-alpha', 0.3)
        self.selection_root.configure(bg='black')
        
        # Canvas pour dessiner
        self.canvas = tk.Canvas(self.selection_root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Variables
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Événements souris
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Touche Échap pour annuler
        self.selection_root.bind("<Escape>", lambda e: self.cancel_selection())
        
        self.selection_root.mainloop()
    
    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
    
    def on_mouse_move(self, event):
        if self.start_x and self.start_y:
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=3, fill='blue', stipple='gray50'
            )
    
    def on_mouse_up(self, event):
        end_x, end_y = event.x, event.y
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)
        
        self.selection_root.destroy()
        
        # Capturer la zone sélectionnée
        self.capture_area(x1, y1, x2, y2)
    
    def cancel_selection(self):
        self.selection_root.destroy()
        self.root.deiconify()
        self.status_label.config(text="❌ Sélection annulée")
    
    def capture_area(self, x1, y1, x2, y2):
        """Capture la zone sélectionnée"""
        try:
            # Prendre la capture
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.captured_image = screenshot
            
            # Sauvegarder temporairement
            self.captured_image.save("temp_capture.png")
            
            # Afficher dans la zone de texte
            self.text_area.insert(tk.END, "📸 CAPTURE EFFECTUÉE\n")
            self.text_area.insert(tk.END, f"Zone: ({x1},{y1}) à ({x2},{y2})\n")
            self.text_area.insert(tk.END, f"Taille: {x2-x1} x {y2-y1} pixels\n\n")
            self.text_area.yview(tk.END)
            
            # Activer le bouton OCR
            self.btn_ocr.config(state=tk.NORMAL)
            self.status_label.config(text="✅ Capture réussie ! Clique sur 'Lire le texte'")
            
            # Réafficher la fenêtre principale
            self.root.deiconify()
            
        except Exception as e:
            self.status_label.config(text=f"❌ Erreur capture: {str(e)}")
            self.root.deiconify()
    
    def ocr_image(self):
        """Envoie l'image à OCR.space (gratuit, sans installation)"""
        if not self.captured_image:
            messagebox.showwarning("Attention", "Capture d'abord une zone")
            return
        
        self.status_label.config(text="🔍 OCR en cours...")
        self.btn_ocr.config(state=tk.DISABLED)
        
        def do_ocr():
            try:
                # Convertir l'image en bytes
                img_bytes = io.BytesIO()
                self.captured_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Appeler API OCR.space gratuite
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': ('capture.png', img_bytes, 'image/png')},
                    data={'language': 'fre', 'isOverlayRequired': False},
                    timeout=30
                )
                
                result = response.json()
                if result.get('ParsedResults'):
                    text = result['ParsedResults'][0]['ParsedText'].strip()
                    if text:
                        self.ocr_text = text
                        self.text_area.insert(tk.END, "🔍 TEXTE EXTRAIT (OCR):\n")
                        self.text_area.insert(tk.END, "-" * 50 + "\n")
                        self.text_area.insert(tk.END, self.ocr_text + "\n")
                        self.text_area.insert(tk.END, "-" * 50 + "\n\n")
                        self.text_area.yview(tk.END)
                        
                        self.btn_ask.config(state=tk.NORMAL)
                        self.status_label.config(text="✅ OCR terminé ! Clique sur 'Demander à DeepSeek'")
                    else:
                        self.status_label.config(text="❌ Aucun texte détecté")
                else:
                    self.status_label.config(text="❌ Erreur OCR - essaie une zone plus nette")
                    
            except Exception as e:
                self.status_label.config(text=f"❌ Erreur: {str(e)[:50]}")
        
        threading.Thread(target=do_ocr, daemon=True).start()
    
    def ask_deepseek(self):
        """Envoie le texte à DeepSeek ou donne les instructions"""
        if not self.ocr_text:
            messagebox.showwarning("Attention", "Fais d'abord l'OCR")
            return
        
        if not DEEPSEEK_API_KEY:
            # Mode sans clé API
            self.text_area.insert(tk.END, "🤖 MODE MANUEL:\n")
            self.text_area.insert(tk.END, "Va sur https://chat.deepseek.com et colle ce texte:\n\n")
            self.text_area.insert(tk.END, f"CONSIGNE: Donne-moi juste les réponses COD/COI pour chaque phrase\n\n")
            self.text_area.insert(tk.END, f"TEXTE:\n{self.ocr_text}\n\n")
            self.ai_response = "➡️ Copie le texte ci-dessus et va sur chat.deepseek.com"
            self.status_label.config(text="📋 Texte prêt à être copié-collé dans DeepSeek")
            return
        
        # Mode avec clé API
        self.status_label.config(text="🤖 Envoi à DeepSeek...")
        self.btn_ask.config(state=tk.DISABLED)
        
        def call_api():
            try:
                prompt = f"""Voici le texte d'un exercice de français (COD/COI).
Réponds UNIQUEMENT avec les réponses, une par ligne (juste "COD" ou "COI").

Texte:
{self.ocr_text}

RÉPONSES:"""
                
                headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
                payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
                
                response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    self.ai_response = response.json()["choices"][0]["message"]["content"]
                    self.text_area.insert(tk.END, "🤖 RÉPONSE DE DeepSeek:\n")
                    self.text_area.insert(tk.END, "-" * 50 + "\n")
                    self.text_area.insert(tk.END, self.ai_response + "\n")
                    self.text_area.insert(tk.END, "-" * 50 + "\n")
                    self.status_label.config(text="✅ Réponse reçue !")
                else:
                    self.text_area.insert(tk.END, f"❌ Erreur API: {response.status_code}\n")
            except Exception as e:
                self.text_area.insert(tk.END, f"❌ Erreur: {str(e)}\n")
            finally:
                self.btn_ask.config(state=tk.NORMAL)
        
        threading.Thread(target=call_api, daemon=True).start()
    
    def copy_response(self):
        if self.ai_response:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.ai_response)
            self.status_label.config(text="✅ Réponse copiée !")
        else:
            messagebox.showinfo("Info", "Rien à copier - fais d'abord l'OCR et demande à DeepSeek")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()