import customtkinter as ctk
import ollama
import threading

# Настройка внешнего вида
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

class AIChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Meta llama 3b realized by wanna")
        self.attributes('-fullscreen', True) 

        self.history = [
            {'role': 'system', 'content': 'Ты — русскоязычный помощник. Общайся со мной на русском, но сохраняй технические названия и бренды на английском. Не переходи на другие языки.'}
        ]

        self.setup_ui()
        self.append_to_chat("Бурмалда", "Hello, World!\n")

    def setup_ui(self):
        
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=10, padx=20, fill="x")
        
        self.title_label = ctk.CTkLabel(self.top_frame, text="Meta llama 3b realized by wanna", font=("Arial", 24, "bold"))
        self.title_label.pack(side="left")

        
        self.exit_btn = ctk.CTkButton(self.top_frame, text="❌ Hello, World!", width=120, fg_color="#d9534f", hover_color="#c9302c", command=self.destroy)
        self.exit_btn.pack(side="right")

        
        self.chat_box = ctk.CTkTextbox(self, font=("Arial", 16), wrap="word", state="disabled")
        self.chat_box.pack(pady=10, padx=20, fill="both", expand=True)

        
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=(0, 20), padx=20, fill="x")

        self.entry = ctk.CTkEntry(self.bottom_frame, placeholder_text="import tkinter as tk", font=("Arial", 16), height=50)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = ctk.CTkButton(self.bottom_frame, text="➤ HelloWorld(print)", font=("Arial", 16, "bold"), height=50, width=150, command=self.send_message)
        self.send_btn.pack(side="right")

    def append_to_chat(self, sender, text):
        """Добавляет текст в окно чата и прокручивает вниз"""
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{sender}:\n{text}\n\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled") 

    def send_message(self, event=None):
        user_text = self.entry.get().strip()
        if not user_text:
            return

        
        self.entry.delete(0, "end")
        self.send_btn.configure(state="disabled")
        self.entry.configure(state="disabled")

        
        self.append_to_chat("Ты", user_text)
        self.history.append({'role': 'user', 'content': user_text})

        
        threading.Thread(target=self.generate_response, daemon=True).start()

    def generate_response(self):
        try:
            
            response = ollama.chat(
                model='llama3.2:1b',
                messages=self.history,
                options={'temperature': 0.7}
            )
            answer = response['message']['content']
            
            
            self.history.append({'role': 'assistant', 'content': answer})
            
           
            self.after(0, self.append_to_chat, "AI", answer)
        except Exception as e:
            self.after(0, self.append_to_chat, "terminal", f"Ошибка связи с ИИ: {e}")
        finally:
           
            self.after(0, self.enable_input)

    def enable_input(self):
        """Возвращает активность полю ввода после ответа"""
        self.send_btn.configure(state="normal")
        self.entry.configure(state="normal")
        self.entry.focus() 

if __name__ == "__main__":
    app = AIChatApp()
    app.mainloop()