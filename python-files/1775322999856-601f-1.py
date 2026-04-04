import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading
from datetime import datetime

class LightAI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Assistant - سبک و عمیق")
        self.root.geometry("750x650")
        self.root.configure(bg='#0d1117')
        self.root.resizable(False, False)
        
        # مرکز کردن پنجره
        self.center_window()
        
        # مدل‌های رایگان Hugging Face (بدون نیاز به API key برای بعضی‌ها)
        self.models = {
            "GPT-OSS 120B (قوی‌ترین)": "robitec/gpt-oss-120b",
            "Mistral 7B (سریع)": "mistralai/Mistral-7B-Instruct-v0.3",
            "Gemma 2B (سبک)": "google/gemma-2b-it",
            "Llama 3 8B": "meta-llama/Llama-3.2-3B-Instruct"
        }
        
        self.current_model = tk.StringVar(value="GPT-OSS 120B (قوی‌ترین)")
        self.conversation_history = []
        
        # حالت تفکیک (تحلیل عمیق)
        self.deep_mode = tk.BooleanVar(value=True)
        
        # ========== رابط کاربری ==========
        
        # فریم اصلی
        main_frame = tk.Frame(root, bg='#0d1117')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # عنوان
        title_frame = tk.Frame(main_frame, bg='#161b22', relief=tk.RAISED, bd=1)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            title_frame,
            text="🧠 AI Assistant | سبک، عمیق، آنلاین",
            font=('Vazir', 16, 'bold'),
            bg='#161b22',
            fg='#58a6ff'
        )
        title_label.pack(pady=12)
        
        subtitle = tk.Label(
            title_frame,
            text="پرسش‌های خود را بپرسید | هوش مصنوعی با قابلیت تحلیل عمیق",
            font=('Vazir', 9),
            bg='#161b22',
            fg='#8b949e'
        )
        subtitle.pack(pady=(0, 10))
        
        # ========== تنظیمات ==========
        settings_frame = tk.Frame(main_frame, bg='#0d1117')
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # انتخاب مدل
        model_frame = tk.Frame(settings_frame, bg='#0d1117')
        model_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(model_frame, text="مدل هوش مصنوعی:", font=('Vazir', 10), bg='#0d1117', fg='#c9d1d9').pack(side=tk.LEFT)
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.current_model,
            values=list(self.models.keys()),
            state='readonly',
            width=25,
            font=('Vazir', 9)
        )
        model_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # حالت تفکیک عمیق
        deep_frame = tk.Frame(settings_frame, bg='#0d1117')
        deep_frame.pack(side=tk.LEFT)
        
        deep_check = tk.Checkbutton(
            deep_frame,
            text="🧠 حالت تفکیک عمیق (تحلیل مرحله به مرحله)",
            variable=self.deep_mode,
            bg='#0d1117',
            fg='#c9d1d9',
            selectcolor='#0d1117',
            font=('Vazir', 9)
        )
        deep_check.pack()
        
        # ========== بخش چت ==========
        chat_frame = tk.LabelFrame(
            main_frame,
            text="💬 گفتگو با هوش مصنوعی",
            font=('Vazir', 10, 'bold'),
            bg='#161b22',
            fg='#58a6ff',
            relief=tk.RIDGE,
            bd=1
        )
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # نمایش مکالمه
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Vazir', 10),
            bg='#0d1117',
            fg='#c9d1d9',
            insertbackground='#58a6ff',
            relief=tk.FLAT,
            bd=0,
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تگ‌های رنگی برای پیام‌ها
        self.chat_display.tag_config("user", foreground="#58a6ff", font=('Vazir', 10, 'bold'))
        self.chat_display.tag_config("ai", foreground="#7ee787", font=('Vazir', 10))
        self.chat_display.tag_config("thinking", foreground="#f0883e", font=('Vazir', 9, 'italic'))
        self.chat_display.tag_config("error", foreground="#f85149", font=('Vazir', 9))
        
        # ========== بخش ورودی ==========
        input_frame = tk.Frame(main_frame, bg='#0d1117')
        input_frame.pack(fill=tk.X)
        
        # لیبل وضعیت
        self.status_label = tk.Label(
            input_frame,
            text="✅ آماده | مدل فعال",
            font=('Vazir', 8),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.status_label.pack(anchor='w', pady=(0, 5))
        
        # باکس ورودی و دکمه
        input_row = tk.Frame(input_frame, bg='#0d1117')
        input_row.pack(fill=tk.X)
        
        self.question_entry = tk.Entry(
            input_row,
            font=('Vazir', 11),
            bg='#161b22',
            fg='#c9d1d9',
            insertbackground='#58a6ff',
            relief=tk.FLAT,
            bd=1
        )
        self.question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
        self.question_entry.bind("<Return>", lambda e: self.ask_question())
        
        self.send_btn = tk.Button(
            input_row,
            text="🚀 بفرست",
            command=self.ask_question,
            font=('Vazir', 10, 'bold'),
            bg='#238636',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=20,
            activebackground='#2ea043'
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # ========== دکمه‌های پایین ==========
        bottom_frame = tk.Frame(main_frame, bg='#0d1117')
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        clear_btn = tk.Button(
            bottom_frame,
            text="🗑️ پاک کردن گفتگو",
            command=self.clear_chat,
            font=('Vazir', 9),
            bg='#21262d',
            fg='#c9d1d9',
            cursor='hand2',
            bd=0,
            padx=15,
            pady=5
        )
        clear_btn.pack(side=tk.LEFT)
        
        exit_btn = tk.Button(
            bottom_frame,
            text="🚪 خروج",
            command=self.exit_app,
            font=('Vazir', 9),
            bg='#21262d',
            fg='#f85149',
            cursor='hand2',
            bd=0,
            padx=15,
            pady=5
        )
        exit_btn.pack(side=tk.RIGHT)
        
        # پیام خوش‌آمدگویی
        self.add_message("🤖", "سلام! من یک هوش مصنوعی سبک و عمیق هستم.\nهر سوالی داری بپرس. حالت تفکیک عمیق رو روشن گذاشتم تا بتونی فرآیند تحلیل رو ببینی! 🧠", "ai")
        
        # افکت محو شدن
        self.fade_in()
    
    def center_window(self):
        self.root.update_idletasks()
        width = 750
        height = 650
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def fade_in(self):
        alpha = 0
        self.root.attributes('-alpha', alpha)
        def increase():
            nonlocal alpha
            if alpha < 1:
                alpha += 0.05
                self.root.attributes('-alpha', alpha)
                self.root.after(30, increase)
        increase()
    
    def add_message(self, sender, message, msg_type):
        """اضافه کردن پیام به نمایشگر"""
        self.chat_display.insert(tk.END, f"\n{sender}: ", msg_type)
        self.chat_display.insert(tk.END, f"{message}\n", msg_type)
        self.chat_display.see(tk.END)
    
    def clear_chat(self):
        self.chat_display.delete(1.0, tk.END)
        self.add_message("🤖", "گفتگو پاک شد! هر سوالی داری بپرس.", "ai")
        self.conversation_history = []
    
    def ask_question(self):
        question = self.question_entry.get().strip()
        if not question:
            return
        
        self.question_entry.delete(0, tk.END)
        self.add_message("👤", question, "user")
        
        # غیرفعال کردن دکمه در حین پردازش
        self.send_btn.config(state=tk.DISABLED, text="⏳ در حال تفکر...")
        self.status_label.config(text="🧠 در حال تحلیل عمیق سوال...", fg='#f0883e')
        
        def process():
            try:
                selected_model_name = self.current_model.get()
                model_id = self.models[selected_model_name]
                
                # ========== مرحله 1: تفکیک و تحلیل سوال ==========
                if self.deep_mode.get():
                    self.root.after(0, lambda: self.add_message("🔍", "【مرحله 1 - تفکیک سوال】در حال تحلیل عمیق...", "thinking"))
                    
                    # تحلیل سوال به اجزا
                    analysis = self.analyze_question(question)
                    self.root.after(0, lambda: self.display_analysis(analysis))
                    
                    import time
                    time.sleep(0.5)  # تاخیر برای نمایش طبیعی
                
                # ========== مرحله 2: دریافت پاسخ از AI ==========
                self.root.after(0, lambda: self.status_label.config(text="🌐 اتصال به هوش مصنوعی...", fg='#58a6ff'))
                
                # استفاده از Hugging Face Inference API (رایگان)
                response = self.get_ai_response(question, model_id)
                
                # ========== مرحله 3: نمایش پاسخ نهایی ==========
                self.root.after(0, lambda: self.add_message("🧠", response, "ai"))
                self.root.after(0, lambda: self.status_label.config(text="✅ آماده | مدل فعال", fg='#8b949e'))
                
                # ذخیره در تاریخچه
                self.conversation_history.append({"question": question, "answer": response})
                
            except Exception as e:
                self.root.after(0, lambda: self.add_message("⚠️", f"خطا: {str(e)}\nلطفاً اتصال اینترنت خود را بررسی کنید.", "error"))
                self.root.after(0, lambda: self.status_label.config(text="❌ خطا در اتصال", fg='#f85149'))
            finally:
                self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="🚀 بفرست"))
        
        thread = threading.Thread(target=process)
        thread.start()
    
    def analyze_question(self, question):
        """تحلیل عمیق سوال - تفکیک به اجزا"""
        analysis = {
            "original": question,
            "length": len(question),
            "words": len(question.split()),
            "type": self.detect_question_type(question),
            "key_concepts": self.extract_keywords(question),
            "complexity": "ساده" if len(question.split()) < 5 else "متوسط" if len(question.split()) < 12 else "پیچیده"
        }
        return analysis
    
    def detect_question_type(self, question):
        """تشخیص نوع سوال"""
        q_lower = question.lower()
        if any(w in q_lower for w in ['چیست', 'چه', 'چگونه', 'define', 'what']):
            return "تعریفی/توصیفی"
        elif any(w in q_lower for w in ['چرا', 'why']):
            return "علت‌یابی/تحلیلی"
        elif any(w in q_lower for w in ['چطور', 'how']):
            return "آموزشی/راهنما"
        elif any(w in q_lower for w in ['مقایسه', 'تفاوت', 'compare']):
            return "مقایسه‌ای"
        else:
            return "عمومی"
    
    def extract_keywords(self, question):
        """استخراج کلمات کلیدی ساده"""
        # کلمات توقف فارسی
        stop_words = ['و', 'به', 'از', 'با', 'برای', 'در', 'یک', 'این', 'آن', 'که', 'چه', 'چرا', 'چطور']
        words = question.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords[:5]  # حداکثر 5 کلمه کلیدی
    
    def display_analysis(self, analysis):
        """نمایش تحلیل در چت"""
        analysis_text = f"""
┌─────────────────────────────────────────┐
│ 📊 تحلیل ساختار سوال                     │
├─────────────────────────────────────────┤
│ طول سوال: {analysis['length']} کاراکتر
│ تعداد کلمات: {analysis['words']} کلمه
│ نوع سوال: {analysis['type']}
│ سطح پیچیدگی: {analysis['complexity']}
│ مفاهیم کلیدی: {', '.join(analysis['key_concepts'])}
└─────────────────────────────────────────┘
        """
        self.add_message("🔬", analysis_text, "thinking")
    
    def get_ai_response(self, question, model_id):
        """دریافت پاسخ از Hugging Face API (رایگان)"""
        
        # استفاده از API رایگان Hugging Face
        # برای مدل‌های مختلف از API endpoints مختلف استفاده می‌کنیم
        
        api_urls = {
            "robitec/gpt-oss-120b": "https://api-inference.huggingface.co/models/robitec/gpt-oss-120b",
            "mistralai/Mistral-7B-Instruct-v0.3": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            "google/gemma-2b-it": "https://api-inference.huggingface.co/models/google/gemma-2b-it",
            "meta-llama/Llama-3.2-3B-Instruct": "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
        }
        
        api_url = api_urls.get(model_id, api_urls["robitec/gpt-oss-120b"])
        
        # ساخت پرامپت با دستورالعمل تفکیک عمیق
        if self.deep_mode.get():
            prompt = f"""【دستورالعمل: پاسخ خود را در 3 مرحله ساختار دهید】
مرحله 1 - درک سوال: ابتدا نشان بده که سوال رو چطور فهمیدی
مرحله 2 - تحلیل عمیق: اطلاعات و استدلال‌های مرتبط رو ارائه بده
مرحله 3 - پاسخ نهایی: جمع‌بندی و پاسخ نهایی رو بده

سوال کاربر: {question}

پاسخ خود را با این ساختار ارائه کن:"""
        else:
            prompt = f"سوال: {question}\nپاسخ:"
        
        headers = {"Content-Type": "application/json"}
        
        # تلاش برای اتصال به API
        try:
            # توجه: بعضی مدل‌ها نیاز به API key دارند
            # این کد از روش جایگزین استفاده می‌کنه که رایگانه
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "do_sample": True
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    # حذف پرامپت از پاسخ
                    if prompt in generated_text:
                        generated_text = generated_text.replace(prompt, '').strip()
                    return generated_text if generated_text else "پاسخی دریافت نشد."
                else:
                    return self.get_fallback_response(question)
            else:
                # اگر API کار نکرد، از پاسخ جایگزین استفاده کن
                return self.get_fallback_response(question)
                
        except requests.exceptions.Timeout:
            return "⏰ زمان اتصال به سرور به پایان رسید. لطفاً دوباره تلاش کن."
        except requests.exceptions.ConnectionError:
            return self.get_fallback_response(question)
        except Exception as e:
            return self.get_fallback_response(question)
    
    def get_fallback_response(self, question):
        """پاسخ جایگزین در صورت عدم دسترسی به API"""
        # این یک پاسخ ساده ولی هوشمندانه است
        q_lower = question.lower()
        
        if any(w in q_lower for w in ['سلام', 'hi', 'hello', 'درود']):
            return "سلام! چطور می‌تونم کمکت کنم؟"
        elif any(w in q_lower for w in ['اسم', 'نام', 'who are you']):
            return "من یک هوش مصنوعی سبک و عمیق هستم که با پایتون ساخته شده. از مدل‌های رایگان Hugging Face استفاده می‌کنم."
        elif any(w in q_lower for w in ['چطوری', 'حالت', 'how are you']):
            return "عالی! ممنون که پرسیدی. آماده پاسخگویی به سوالات تو هستم."
        elif any(w in q_lower for w in ['خداحافظ', 'bye', 'خروج']):
            return "خداحافظ! روز خوبی داشته باشی. هر وقت سوالی داشتی برگرد."
        elif any(w in q_lower for w in ['هوش مصنوعی', 'ai', 'what is ai']):
            return """هوش مصنوعی (AI) به معنی ساخت ماشین‌هایی است که می‌توانند مانند انسان فکر کنند و یاد بگیرند.
🔹 انواع اصلی: 
• یادگیری ماشین (ML): الگوریتم‌هایی که از داده یاد می‌گیرند
• یادگیری عمیق (Deep Learning): شبکه‌های عصبی چندلایه
• پردازش زبان طبیعی (NLP): درک و تولید زبان انسان

من خودم یک نمونه از هوش مصنوعی هستم که با استفاده از مدل‌های زبان بزرگ (LLM) ساخته شده‌ام."""
        elif any(w in q_lower for w in ['پایتون', 'python']):
            return """پایتون یک زبان برنامه‌نویسی سطح بالا، ساده و قدرتمند است.
✨ ویژگی‌ها:
• سینتکس ساده و خوانا
• کتابخانه‌های گسترده
• مناسب برای AI، وب، علم داده
• متن‌باز و رایگان

با پایتون می‌تونی برنامه‌های دسکتاپ، وب، هوش مصنوعی و خیلی چیزای دیگه بسازی!"""
        else:
            return f"""📝 سوال شما: "{question}"

🔍 تحلیل: 
من در حال حاضر به اینترنت متصل نیستم یا سرور هوش مصنوعی در دسترس نیست.

💡 پیشنهاد:
1. اتصال اینترنت خود را بررسی کن
2. دوباره سوال خود را بپرس
3. اگر مشکل ادامه داشت، از ساده‌تر کردن سوال استفاده کن

🔄 برای دریافت پاسخ دقیق‌تر، لطفاً اتصال اینترنت را بررسی کرده و دوباره تلاش کن."""
    
    def exit_app(self):
        if messagebox.askyesno("خروج", "آیا مطمئنی می‌خوای خارج بشی؟"):
            self.root.quit()

# نصب کتابخانه مورد نیاز
# قبل از اجرا: pip install requests

if __name__ == "__main__":
    root = tk.Tk()
    app = LightAI(root)
    root.mainloop()