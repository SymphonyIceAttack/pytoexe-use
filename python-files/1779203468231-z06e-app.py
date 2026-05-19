import tkinter as tk
from tkinter import scrolledtext, messagebox
import io
import requests
import json
from PIL import ImageGrab
import threading
import os

# Configuration
DEEPSEEK_API_KEY = ""  # Laisse vide pour copier-coller manuellement

class ScreenCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Capture + IA - COD/COI")
        self.root.geometry("750x650")
        
        self.captured_image = None
        self.selection_window = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Interface
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=85, height=22, font=("Courier", 10))
        self.text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        
        self.btn_capture = tk.Button(btn_frame, text="✂️ Sélectionner une zone", command=self.start_selection, bg="#4CAF50", fg="white", padx=15, pady=5)
        self.btn_capture.pack(side=tk.LEFT, padx=5)
        
        self.btn_ocr = tk.Button(btn_frame, text="🔍 Lire le texte (OCR)", command=self.ocr_image, bg="#2196F3", fg="white", padx=15, pady=5, state=tk.DISABLED)
        self.btn_ocr.pack(side=tk.LEFT, padx=5)
        
        self.btn_manual = tk.Button(btn_frame, text="📋 Générer pour DeepSeek", command=self.generate_for_deepseek, bg="#FF9800", fg="white", padx=15, pady=5, state=tk.DISABLED)
        self.btn_manual.pack(side=tk.LEFT, padx=5)
        
        self.btn_copy = tk.Button(btn_frame, text="📋 Copier tout", command=self.copy_all, bg="#9C27B0", fg="white", padx=15, pady=5)
        self.btn_copy.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(root, text="✅ Prêt - Clique sur 'Sélectionner une zone'", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.ocr_text = ""
    
    def start_selection(self):
        self.root.iconify()
        threading.Timer(0.3, self.create_selection_window).start()
    
    def create_selection_window(self):
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.title("Sélectionne une zone - Clique et glisse")
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.configure(bg='black')
        
        self.canvas = tk.Canvas(self.selection_window, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.selection_window.bind("<Escape>", lambda e: self.cancel_selection())
    
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
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        self.selection_window.destroy()
        self.capture_area(x1, y1, x2, y2)
    
    def cancel_selection(self):
        if self.selection_window:
            self.selection_window.destroy()
        self.root.deiconify()
        self.status_label.config(text="❌ Sélection annulée")
    
    def capture_area(self, x1, y1, x2, y2):
        try:
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.captured_image = screenshot
            
            self.text_area.insert(tk.END, "📸 CAPTURE EFFECTUÉE\n")
            self.text_area.insert(tk.END, f"Zone: {x2-x1} x {y2-y1} pixels\n\n")
            self.text_area.yview(tk.END)
            
            self.btn_ocr.config(state=tk.NORMAL)
            self.status_label.config(text="✅ Capture réussie ! Clique sur 'Lire le texte'")
            self.root.deiconify()
            
        except Exception as e:
            self.status_label.config(text=f"❌ Erreur: {str(e)[:50]}")
            self.root.deiconify()
    
    def ocr_image(self):
        if not self.captured_image:
            messagebox.showwarning("Attention", "Capture d'abord une zone")
            return
        
        self.status_label.config(text="🔍 OCR en cours...")
        self.btn_ocr.config(state=tk.DISABLED)
        
        def do_ocr():
            try:
                img_bytes = io.BytesIO()
                self.captured_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
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
                        self.text_area.insert(tk.END, "🔍 TEXTE EXTRAIT:\n")
                        self.text_area.insert(tk.END, "="*60 + "\n")
                        self.text_area.insert(tk.END, self.ocr_text + "\n")
                        self.text_area.insert(tk.END, "="*60 + "\n\n")
                        self.text_area.yview(tk.END)
                        
                        self.btn_manual.config(state=tk.NORMAL)
                        self.status_label.config(text="✅ OCR terminé ! Clique sur 'Générer pour DeepSeek'")
                    else:
                        self.status_label.config(text="❌ Aucun texte détecté")
                else:
                    self.status_label.config(text="❌ Erreur OCR")
                    
            except Exception as e:
                self.status_label.config(text=f"❌ Erreur: {str(e)[:50]}")
            finally:
                self.btn_ocr.config(state=tk.NORMAL)
        
        threading.Thread(target=do_ocr, daemon=True).start()
    
    def generate_for_deepseek(self):
        if not self.ocr_text:
            return
        
        prompt = f"""Consigne: Pour chaque phrase, réponds uniquement "COD" ou "COI" (un par ligne).

Texte:
{self.ocr_text}

Réponses:"""
        
        self.text_area.insert(tk.END, "🤖 À COPIER-COLLER DANS DeepSeek (https://chat.deepseek.com):\n")
        self.text_area.insert(tk.END, "="*60 + "\n")
        self.text_area.insert(tk.END, prompt + "\n")
        self.text_area.insert(tk.END, "="*60 + "\n\n")
        self.text_area.yview(tk.END)
        
        self.status_label.config(text="✅ Prompt généré ! Copie-le et va sur chat.deepseek.com")
    
    def copy_all(self):
        text = self.text_area.get("1.0", tk.END)
        if text.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_label.config(text="✅ Tout le texte copié !")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenCaptureApp(root)
    root.mainloop()