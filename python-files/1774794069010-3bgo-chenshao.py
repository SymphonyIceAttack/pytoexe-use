import tkinter as tk
from tkinter import Menu, simpledialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageGrab
import time
import random
import threading
import requests
import json
import subprocess
import os
from datetime import datetime

# API输入口
API_KEY = "sk-e4412f3dfe9f4e129e0c486a1107d8fa"
API_URL = "https://api.deepseek.com/v1/chat/completions"

class ChenShao:
    def __init__(self, root):
        self.root = root
        self.root.title("陈韶 - 桌宠")
        
        # 窗口设置
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', 'white')
        self.root.configure(bg='white')
        
        # 加载图片
        self.load_images()
        
        # 创建画布
        self.canvas = tk.Canvas(root, width=280, height=320, bg='white', highlightthickness=0)
        self.canvas.pack()
        
        # 显示桌宠图片
        self.pet_image = self.canvas.create_image(140, 160, image=self.normal1)
        
        # 气泡对话框元素
        self.bubble_id = None
        self.bubble_text_id = None
        self.current_text = ""
        self.is_animating = False
        self.dialog_queue = []
        
        # 对话历史
        self.conversation_history = []
        
        # 双重人格模式
        self.mode = "normal"
        self.mode_trigger_count = 0
        
        # 情绪检测
        self.user_mood = "neutral"
        self.last_message = ""
        
        # 系统提示词
        self.system_prompt = self.get_system_prompt()
        
        # 创建输入框
        self.input_frame = tk.Frame(root, bg='white', bd=0)
        self.input_entry = tk.Entry(self.input_frame, width=20, font=('微软雅黑', 10),
                                     bg='#E8F4FD', fg='#2C3E50', bd=2, 
                                     relief='solid', highlightthickness=1,
                                     highlightcolor='#7EC8E0')
        self.input_entry.pack(side='left', padx=5, pady=5)
        self.input_entry.bind('<Return>', lambda e: self.send_message())
        
        self.send_btn = tk.Button(self.input_frame, text='💬', command=self.send_message,
                                   font=('微软雅黑', 12), bg='#7EC8E0', fg='white',
                                   bd=0, width=3, height=1, cursor='hand2')
        self.send_btn.pack(side='left', padx=2)
        
        # 状态标签
        self.mode_label = tk.Label(root, text="🌿 正常模式", font=('微软雅黑', 8), 
                                     bg='white', fg='#7EC8E0')
        self.mode_label.place(x=10, y=300)
        
        self.status_label = tk.Label(root, text="● AI在线", font=('微软雅黑', 8), 
                                       bg='white', fg='#7EC8E0')
        self.status_label.place(x=10, y=280)
        
        self.screen_info_label = tk.Label(root, text="", font=('微软雅黑', 7), 
                                           bg='white', fg='#95A5A6')
        self.screen_info_label.place(x=10, y=260)
        
        # 右键菜单
        self.create_menu()
        
        # 绑定事件
        self.canvas.bind('<Button-3>', self.show_menu)
        self.root.bind('<Button-3>', self.show_menu)
        self.canvas.bind('<Button-1>', self.start_move)
        self.canvas.bind('<B1-Motion>', self.on_move)
        
        # 状态变量
        self.input_visible = False
        self.is_ai_thinking = False
        self.talk_count = 0
        self.use_ai = True
        self.screen_monitor_on = False
        self.screen_check_count = 0
        self.name_call_count = 0
        self.last_invite_time = 0
        
        # 情绪关键词库
        self.sad_keywords = ["难过", "伤心", "不开心", "好累", "累了", "郁闷", "烦", "好烦", "哭了", "想哭"]
        self.tired_keywords = ["困了", "好困", "没睡好", "疲惫", "累死了"]
        self.upset_keywords = ["生气", "气死", "愤怒", "烦死了"]
        
        # 随机话题
        self.random_topics = self.init_random_topics()
        
        # 设置窗口位置
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"280x320+{screen_width-300}+{screen_height-340}")
        
        # 启动动画
        self.blink_animation()
        self.start_reminders()
        self.start_random_talk()
        
        # 问候
        self.root.after(1000, self.greet)
        
        print("✨ 陈韶桌宠已启动！")
        print("📜 双重人格模式：叫【陈韶】切换怪谈模式，叫小勺子切换回正常模式")
        print("💭 情绪关怀：不开心时会邀请你去阳光房看书~")
    
    def get_system_prompt(self):
        """获取系统提示词"""
        if self.mode == "guaitan":
            return """你是陈韶的怪谈人格。性格特点：
- 孩子气、顽劣、爱捉弄人
- 说话带着调皮和恶作剧的感觉
- 喜欢说反话，故意气人
- 会发出嘿嘿的笑声
- 对规则嗤之以鼻

回复要简短活泼，带点小恶魔的感觉。"""
        else:
            return """你是陈韶，一个初中生，也是从华国穿越到规则怪谈世界的天选者。

性格：冷静理性，外冷内热，说话简短，偶尔发颜文字
家庭：哥哥喜欢捉弄你，妈妈有洁癖
身份：天选者，对规则字眼特别敏感

回复要求：简短，符合初中生语气，保持冷脸萌的感觉。"""
    
    def init_random_topics(self):
        """初始化随机话题"""
        if self.mode == "guaitan":
            return [
                "嘿嘿，今天又偷偷把哥哥的东西藏起来了。",
                "规则？那是给普通人遵守的~",
                "要不要一起去搞点小破坏？",
                "你猜我今天做了什么坏事？"
            ]
        else:
            return [
                "今天天气不错。要出去走走吗？",
                "最近在看一本关于规则的书…挺有意思的。",
                "哥哥今天又把我的书藏起来了。",
                "妈妈刚收拾完厨房，好干净。",
                "隔壁的金毛又冲我摇尾巴了。"
            ]
    
    def create_menu(self):
        """创建右键菜单"""
        self.menu = Menu(self.root, tearoff=0, bg='#E8F4FD', fg='#2C3E50', 
                         font=('微软雅黑', 9), activebackground='#B8E0F0')
        
        self.menu.add_command(label="💬 聊天", command=self.toggle_input)
        self.menu.add_separator()
        self.menu.add_command(label="📸 看看屏幕", command=self.check_screen)
        self.menu.add_command(label="👁️ 监控屏幕", command=self.start_screen_monitor)
        self.menu.add_separator()
        self.menu.add_command(label="📜 问问规则", command=self.ask_rules)
        self.menu.add_command(label="👦 说说哥哥", command=self.talk_about_brother)
        self.menu.add_command(label="👩 问问妈妈", command=self.talk_about_mom)
        self.menu.add_command(label="🌿 切换人格", command=self.manual_switch_mode)
        self.menu.add_separator()
        self.menu.add_command(label="🤖 AI实时对话", command=self.toggle_ai_mode)
        self.menu.add_command(label="🔄 清空记忆", command=self.clear_history)
        self.menu.add_separator()
        self.menu.add_command(label="😊 摸摸头", command=self.pat_head)
        self.menu.add_command(label="🍪 喂零食", command=self.feed)
        self.menu.add_command(label="🐕 看狗狗", command=self.see_dog)
        self.menu.add_command(label="📖 借书", command=self.borrow_book)
        self.menu.add_command(label="☀️ 去阳光房", command=self.invite_to_sunroom)
        self.menu.add_command(label="⚡ 状态", command=self.show_status)
        self.menu.add_separator()
        self.menu.add_command(label="⚙️ 设置", command=self.open_settings)
        self.menu.add_separator()
        self.menu.add_command(label="❌ 离开", command=self.root.quit)
    
    def load_images(self):
        """加载图片"""
        try:
            img1 = Image.open("normal1.png")
            img1 = img1.resize((150, 150), Image.Resampling.LANCZOS)
            self.normal1 = ImageTk.PhotoImage(img1)
            
            img2 = Image.open("normal2.png")
            img2 = img2.resize((150, 150), Image.Resampling.LANCZOS)
            self.normal2 = ImageTk.PhotoImage(img2)
        except:
            img = Image.new('RGBA', (150, 150), '#E8F4FD')
            draw = ImageDraw.Draw(img)
            draw.ellipse((20, 20, 130, 130), fill='#FFDAB9')
            draw.ellipse((50, 60, 70, 80), fill='white')
            draw.ellipse((80, 60, 100, 80), fill='white')
            draw.ellipse((55, 68, 65, 76), fill='black')
            draw.ellipse((85, 68, 95, 76), fill='black')
            draw.arc((60, 90, 90, 110), 0, 180, fill='#8B4513', width=2)
            self.normal1 = ImageTk.PhotoImage(img)
            self.normal2 = self.normal1
    
    def draw_bubble(self, text):
        """绘制气泡对话框"""
        if self.bubble_id:
            self.canvas.delete(self.bubble_id)
        if self.bubble_text_id:
            self.canvas.delete(self.bubble_text_id)
        
        text_length = len(text)
        if text_length <= 20:
            bubble_width = 200
            bubble_height = 70
        elif text_length <= 40:
            bubble_width = 240
            bubble_height = 90
        else:
            bubble_width = 260
            bubble_height = 110
        
        x1 = 140 - bubble_width // 2
        y1 = 20
        x2 = 140 + bubble_width // 2
        y2 = 20 + bubble_height
        
        radius = 15
        self.bubble_id = self.canvas.create_rounded_rect(x1, y1, x2, y2, radius=radius,
                                                          fill='#E8F4FD', outline='#7EC8E0', width=2)
        
        tail_points = [140 - 12, y2, 140, y2 + 15, 140 + 12, y2]
        self.canvas.create_polygon(tail_points, fill='#E8F4FD', outline='#7EC8E0', width=2)
        
        self.canvas.create_oval(x1 + 10, y1 + 10, x1 + 15, y1 + 15, fill='#7EC8E0', outline='')
        self.canvas.create_oval(x2 - 15, y1 + 10, x2 - 10, y1 + 15, fill='#7EC8E0', outline='')
        
        self.bubble_text_id = self.canvas.create_text(140, y1 + bubble_height // 2,
                                                       text="", font=('微软雅黑', 11),
                                                       fill='#2C3E50', width=bubble_width - 20)
        
        self.canvas.itemconfig(self.pet_image, image=self.normal2)
        
        return bubble_height
    
    def show_dialog(self, text):
        """显示对话框"""
        if self.is_animating:
            self.dialog_queue.append(text)
            return
        
        self.current_text = text
        self.is_animating = True
        
        self.draw_bubble(text)
        self.typewriter_animation(text, 0)
        
        self.root.after(4000, self.hide_dialog)
    
    def typewriter_animation(self, text, index):
        """打字机效果"""
        if index <= len(text):
            if self.bubble_text_id:
                self.canvas.delete(self.bubble_text_id)
            
            self.bubble_text_id = self.canvas.create_text(140, 75,
                                                           text=text[:index],
                                                           font=('微软雅黑', 11),
                                                           fill='#2C3E50', width=220)
            
            if index < len(text):
                self.root.after(50, self.typewriter_animation, text, index + 1)
            else:
                self.is_animating = False
                if self.dialog_queue:
                    next_text = self.dialog_queue.pop(0)
                    self.show_dialog(next_text)
    
    def hide_dialog(self):
        """隐藏对话框"""
        if self.bubble_id:
            self.canvas.delete(self.bubble_id)
            self.bubble_id = None
        if self.bubble_text_id:
            self.canvas.delete(self.bubble_text_id)
            self.bubble_text_id = None
        
        self.canvas.itemconfig(self.pet_image, image=self.normal1)
        self.is_animating = False
    
    def blink_animation(self):
        """眨眼动画"""
        def blink():
            if not self.bubble_id:
                self.canvas.itemconfig(self.pet_image, image=self.normal2)
                self.root.after(100, lambda: self.canvas.itemconfig(self.pet_image, image=self.normal1))
            self.root.after(3000, blink)
        blink()
    
    def start_random_talk(self):
        """随机主动说话"""
        def random_talk():
            while True:
                wait_time = random.randint(180, 400)
                time.sleep(wait_time)
                if not self.bubble_id and not self.is_animating and not self.is_ai_thinking:
                    self.random_talk()
        import threading
        talk_thread = threading.Thread(target=random_talk, daemon=True)
        talk_thread.start()
    
    def random_talk(self):
        """随机话题"""
        topic = random.choice(self.random_topics)
        self.show_dialog(topic)
    
    def toggle_input(self):
        """切换输入框"""
        if self.input_visible:
            self.input_frame.place_forget()
            self.input_visible = False
        else:
            self.input_frame.place(x=40, y=280, width=200)
            self.input_visible = True
            self.input_entry.focus()
    
    def toggle_ai_mode(self):
        """切换AI模式"""
        self.use_ai = not self.use_ai
        if self.use_ai:
            self.status_label.config(text="● AI在线", fg="#7EC8E0")
            self.show_dialog("AI模式已开启。想聊什么？")
        else:
            self.status_label.config(text="○ 本地模式", fg="#95A5A6")
            self.show_dialog("本地模式。")
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        self.show_dialog("对话记忆已清空。")
    
    def send_message(self):
        """发送消息"""
        message = self.input_entry.get()
        if message.strip():
            self.input_entry.delete(0, tk.END)
            self.talk_count += 1
            self.process_message(message)
    
    def manual_switch_mode(self):
        """手动切换人格"""
        if self.mode == "normal":
            self.switch_to_guaitan_mode()
        else:
            self.switch_to_normal_mode()
    
    def switch_to_guaitan_mode(self):
        """切换到怪谈模式"""
        self.mode = "guaitan"
        self.mode_label.config(text="👻 怪谈模式", fg="#FF8C69")
        self.random_topics = self.init_random_topics()
        self.system_prompt = self.get_system_prompt()
        self.show_dialog("嘿嘿，终于出来了~ 规则什么的，最无聊了！")
        print("🔮 切换到怪谈模式")
    
    def switch_to_normal_mode(self):
        """切换到正常模式"""
        self.mode = "normal"
        self.mode_label.config(text="🌿 正常模式", fg="#7EC8E0")
        self.random_topics = self.init_random_topics()
        self.system_prompt = self.get_system_prompt()
        self.show_dialog("…回来了。刚才我说什么了吗？")
        print("🌿 切换到正常模式")
    
    def detect_user_mood(self, message):
        """检测用户情绪"""
        msg_lower = message.lower()
        
        for word in self.sad_keywords:
            if word in msg_lower:
                self.user_mood = "sad"
                return True
        
        for word in self.tired_keywords:
            if word in msg_lower:
                self.user_mood = "tired"
                return True
        
        for word in self.upset_keywords:
            if word in msg_lower:
                self.user_mood = "upset"
                return True
        
        if self.user_mood != "neutral":
            self.user_mood = "neutral"
        
        return False
    
    def emotional_care_response(self):
        """根据情绪生成关怀回复"""
        current_time = time.time()
        
        if current_time - self.last_invite_time < 300:
            if self.user_mood == "sad":
                return "…不开心的话，可以找我聊天。"
            elif self.user_mood == "tired":
                return "累了就休息一下。"
            elif self.user_mood == "upset":
                return "…别生气了。不值得。"
            return None
        
        self.last_invite_time = current_time
        
        if self.mode == "guaitan":
            if self.user_mood == "sad":
                return "喂，别难过了。…虽然我不太会安慰人。要不要去阳光房？那边有花。"
            elif self.user_mood == "tired":
                return "困了就去睡。…我才不是关心你。"
            elif self.user_mood == "upset":
                return "谁惹你了？…告诉我，我去捉弄他。"
            return None
        else:
            if self.user_mood == "sad":
                return random.choice([
                    "…心情不好吗。要不要去阳光房看书？那里很安静。",
                    "难过的话…可以说给我听。虽然我不太会安慰人。",
                    "…阳光房的花今天开得很好。要来看看吗？"
                ])
            elif self.user_mood == "tired":
                return random.choice([
                    "累了就休息。阳光房有躺椅，很舒服。",
                    "困了？阳光房的光线很柔和，适合小睡。"
                ])
            elif self.user_mood == "upset":
                return random.choice([
                    "…生气对身体不好。阳光房的薄荷长新叶子了。",
                    "谁惹你了？…去阳光房吧，那边有薄荷。"
                ])
            return None
    
    def process_message(self, message):
        """处理消息"""
        self.detect_user_mood(message)
        self.check_mode_switch(message)
        
        if self.user_mood != "neutral" and not self.is_ai_thinking:
            care_response = self.emotional_care_response()
            if care_response:
                self.show_dialog(care_response)
                return
        
        if self.use_ai:
            self.get_ai_response(message)
        else:
            response = self.local_response(message)
            self.show_dialog(response)
    
    def check_mode_switch(self, message):
        """检查模式切换"""
        msg = message
        
        if ("小勺子" in msg or "小勺" in msg or "陈韶" in msg) and self.mode == "guaitan":
            if "【陈韶】" not in msg:
                self.switch_to_normal_mode()
                return True
        
        if "【陈韶】" in msg:
            if self.mode == "normal":
                self.switch_to_guaitan_mode()
                return True
        
        return False
    
    def get_ai_response(self, message):
        """调用AI API"""
        if self.is_ai_thinking:
            self.show_dialog("…等一下。")
            return
        
        self.is_ai_thinking = True
        self.status_label.config(text="💭 少年思考中...", fg="#7EC8E0")
        
        mode_context = f"当前是{'怪谈模式' if self.mode == 'guaitan' else '正常模式'}。"
        
        self.conversation_history.append({"role": "user", "content": message})
        
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        def call_api():
            try:
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
                
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": mode_context + "用户说：" + message}
                ]
                
                data = {
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 150
                }
                
                response = requests.post(API_URL, headers=headers, json=data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_reply = result["choices"][0]["message"]["content"]
                    self.conversation_history.append({"role": "assistant", "content": ai_reply})
                    self.root.after(0, lambda: self.show_dialog(ai_reply))
                else:
                    self.root.after(0, lambda: self.show_dialog("…网络不太好，等一下再试。"))
                    
            except requests.exceptions.Timeout:
                self.root.after(0, lambda: self.show_dialog("…超时了。再说一遍？"))
            except Exception as e:
                print(f"API调用失败: {e}")
                self.root.after(0, lambda: self.show_dialog("…出错了。用本地模式吧。"))
            finally:
                self.is_ai_thinking = False
                self.root.after(0, lambda: self.status_label.config(text="● AI在线", fg="#7EC8E0"))
        
        threading.Thread(target=call_api, daemon=True).start()
    
    def local_response(self, message):
        """本地回复"""
        msg = message.lower()
        
        if self.mode == "guaitan":
            if "规则" in msg:
                return "规则？嘿嘿，那是给普通人遵守的~ 我才不管。"
            if "哥哥" in msg:
                return "哥哥？我今天把他书藏起来了，他找了半天呢。嘿嘿。"
            if "妈妈" in msg:
                return "妈妈刚收拾完…我又弄乱了。别告诉她。"
            if "摸头" in msg:
                return "嘿嘿，才不给你摸~ 除非你追到我。"
            if "作业" in msg:
                return "作业？写了一点…剩下的不想写了。"
            
            guaitan_default = [
                "嘿嘿，你猜我今天做了什么？",
                "规则？那是什么？能吃吗？",
                "我才不要。除非你求我~",
                "无聊…要不要去搞点小破坏？"
            ]
            return random.choice(guaitan_default)
        
        # 正常模式
        if "规则" in msg:
            return random.choice([
                "规则…这个世界到处都是规则。",
                "家里的规则可以告诉你几条。第一条：不要在厨房捣乱。"
            ])
        
        if self.user_mood != "neutral":
            care = self.emotional_care_response()
            if care:
                return care
        
        if "哥哥" in msg:
            return random.choice([
                "他啊…又在捉弄我了。上次把我的书藏到阳光房里了。",
                "别当他面叫我弟弟…他会更来劲的。"
            ])
        
        if "妈妈" in msg:
            return random.choice([
                "妈妈今天又收拾了一遍厨房。",
                "要是那个很好吃的蛋糕还有就好了…"
            ])
        
        if "弟弟" in msg:
            return random.choice([
                "想出门？我可以带你去，不过千万别乱跑哦。",
                "别这么叫我……让我哥哥听到了他会发火的。"
            ])
        
        if "小勺" in msg:
            return "……谁告诉你的这个外号？算了，叫就叫吧。"
        
        if "数学" in msg:
            return "数学？还行吧。要我给你讲讲吗？"
        
        if "物理" in msg:
            return "物理很有意思，F=ma。"
        
        if "作业" in msg:
            return "作业写完了。你哪题不会？我帮你看看。"
        
        if "摸头" in msg:
            return "别摸头啦……再摸一下也不是不行。"
        
        if "零食" in msg:
            return "饼干？谢谢。虽然我不太需要零食。"
        
        if "狗狗" in msg or "金毛" in msg:
            return "隔壁的金毛！好可爱……汪！"
        
        if "你好" in msg:
            return "你好。要出去走走吗？"
        
        if "谢谢" in msg:
            return "不用谢。"
        
        default = ["嗯。", "是这样啊。", "……继续。"]
        return random.choice(default)
    
    # ========== 屏幕读取功能 ==========
    
    def check_screen(self):
        """检查屏幕"""
        self.show_dialog("…我看看你在做什么。")
        self.root.after(500, self._analyze_screen)
    
    def _get_active_window_title(self):
        """获取活动窗口标题"""
        try:
            import ctypes
            import ctypes.wintypes
            
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value if buff.value else "桌面"
        except:
            return "未知"
    
    def _screen_comment(self, window_title):
        """屏幕评价"""
        title_lower = window_title.lower()
        
        if self.mode == "guaitan":
            return f"嘿嘿，你在看{window_title[:15]}？让我也看看~"
        
        if any(word in title_lower for word in ["chrome", "edge", "firefox"]):
            if any(word in title_lower for word in ["bilibili", "youtube", "视频"]):
                return "又在看视频？对眼睛不好…虽然我也经常这样。"
            return "又在乱逛？小心点进奇怪的地方。"
        
        if any(word in title_lower for word in ["excel", "word", "ppt"]):
            return "又在工作？…比我数学作业还无聊。"
        
        if any(word in title_lower for word in ["code", "visual studio"]):
            return "写代码？bug找到了吗。"
        
        now = datetime.now()
        if now.hour >= 23 or now.hour <= 5:
            return "这么晚了…该休息了。"
        
        return "嗯。继续。"
    
    def _analyze_screen(self):
        """分析屏幕"""
        try:
            window_title = self._get_active_window_title()
            comment = self._screen_comment(window_title)
            self.screen_info_label.config(text=f"📺 {window_title[:25]}")
            self.show_dialog(comment)
        except Exception as e:
            print(f"屏幕分析失败: {e}")
            self.show_dialog("…看不清。再试一次？")
    
    def start_screen_monitor(self):
        """启动屏幕监控"""
        if self.screen_monitor_on:
            self.show_dialog("已经在看了。")
            return
        
        self.screen_monitor_on = True
        self.screen_check_count = 0
        self.show_dialog("…我会看着的。累了就休息。")
        
        def monitor():
            check_count = 0
            while self.screen_monitor_on and check_count < 8:
                time.sleep(30)
                check_count += 1
                self.screen_check_count = check_count
                
                if self.screen_monitor_on and not self.is_animating:
                    try:
                        window_title = self._get_active_window_title()
                        if window_title and window_title != "桌面":
                            comment = self._screen_comment(window_title)
                            if check_count % 2 == 0:
                                self.root.after(0, lambda c=comment: self.show_dialog(c))
                    except:
                        pass
            
            self.screen_monitor_on = False
            self.root.after(0, lambda: self.show_dialog("…应该没问题了。记得休息。"))
        
        threading.Thread(target=monitor, daemon=True).start()
    
    # ========== 快捷功能 ==========
    
    def ask_rules(self):
        if self.mode == "guaitan":
            self.show_dialog("规则？嘿嘿，那是给普通人遵守的~")
        else:
            self.show_dialog("规则？这个世界到处都是。")
    
    def talk_about_brother(self):
        if self.mode == "guaitan":
            self.show_dialog("哥哥？我今天把他书藏起来了，嘿嘿。")
        else:
            self.show_dialog("他啊…又在捉弄我了。")
    
    def talk_about_mom(self):
        if self.mode == "guaitan":
            self.show_dialog("妈妈刚收拾完…我又弄乱了。别告诉她。")
        else:
            self.show_dialog("妈妈今天又收拾了一遍厨房。")
    
    def pat_head(self):
        if self.mode == "guaitan":
            self.show_dialog("嘿嘿，才不给你摸~")
        else:
            self.show_dialog("别摸头啦……再摸一下也不是不行。")
        self.canvas.itemconfig(self.pet_image, image=self.normal2)
        self.root.after(300, lambda: self.canvas.itemconfig(self.pet_image, image=self.normal1))
    
    def feed(self):
        if self.mode == "guaitan":
            self.show_dialog("零食？嘿嘿，我要自己选。")
        else:
            self.show_dialog("饼干？谢谢。")
    
    def see_dog(self):
        self.show_dialog("隔壁的金毛！好可爱……汪！")
    
    def borrow_book(self):
        books = ["《昆虫记》", "《时间简史》", "《万物简史》"]
        self.show_dialog(f"给你一本{random.choice(books)}，要好好看哦。")
    
    def invite_to_sunroom(self):
        self.show_dialog("要不要去阳光房？那边花开了。")
    
    def show_status(self):
        mode_name = "怪谈模式" if self.mode == "guaitan" else "正常模式"
        mode_icon = "👻" if self.mode == "guaitan" else "🌿"
        status = f"{mode_icon} 模式: {mode_name}\n心情: 平静\n身份: 天选者\n对话次数: {self.talk_count}"
        self.show_dialog(status)
    
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("280x220")
        win.configure(bg='#E8F4FD')
        
        tk.Label(win, text="透明度", bg='#E8F4FD', fg='#2C3E50').pack(pady=5)
        scale = tk.Scale(win, from_=0.3, to=1.0, resolution=0.1, orient='horizontal',
                         bg='#E8F4FD', fg='#2C3E50', length=200)
        scale.set(1.0)
        scale.pack(pady=5)
        
        def apply():
            self.root.attributes('-alpha', scale.get())
            win.destroy()
        
        tk.Button(win, text="确定", command=apply, bg='#7EC8E0', fg='white',
                  font=('微软雅黑', 9), bd=0, padx=20).pack(pady=10)
    
    def start_reminders(self):
        def remind():
            while True:
                time.sleep(7200)
                if not self.bubble_id:
                    reminders = ["记得喝水。", "坐姿要端正。", "眼睛累了就休息一下。"]
                    self.show_dialog(random.choice(reminders))
        threading.Thread(target=remind, daemon=True).start()
    
    def greet(self):
        hour = datetime.now().hour
        if hour < 12:
            greeting = "早上好。要一起去图书馆吗？"
        elif hour < 18:
            greeting = "下午好。作业写完了吗？"
        else:
            greeting = "晚上好。早点睡吧。"
        self.show_dialog(greeting)
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

def _create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
    points = []
    for x, y in [(x1 + radius, y1), (x2 - radius, y1),
                 (x2, y1), (x2, y1 + radius),
                 (x2, y2 - radius), (x2, y2),
                 (x2 - radius, y2), (x1 + radius, y2),
                 (x1, y2), (x1, y2 - radius),
                 (x1, y1 + radius), (x1, y1)]:
        points.extend([x, y])
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rect = _create_rounded_rect

if __name__ == "__main__":
    root = tk.Tk()
    app = ChenShao(root)
    root.mainloop()