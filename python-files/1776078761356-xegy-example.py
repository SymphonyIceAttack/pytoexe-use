import tkinter as tk 
import math 

class AngleMeter: 
    def __init__(self): 
        self.root = tk.Tk() 
        self.root.title("台球测角器") 
        self.root.attributes('-topmost', True) 
        self.root.attributes('-alpha', 0.7)  # 半透明 
        self.root.geometry("400x300+100+100") 
        
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0) 
        self.canvas.pack(fill=tk.BOTH, expand=True) 
        
        self.line1 = None 
        self.line2 = None 
        self.start_x = None 
        self.start_y = None 
        self.drawing_line = 1  # 1: 第一条线, 2: 第二条线 
        
        self.angle_label = tk.Label(self.root, text="角度: --°", fg="white", bg="black", font=("Arial", 14)) 
        self.angle_label.place(relx=0.5, rely=0.1, anchor=tk.CENTER) 
        
        self.status_label = tk.Label(self.root, text="拖动鼠标画第一条线", fg="cyan", bg="black", font=("Arial", 10)) 
        self.status_label.place(relx=0.5, rely=0.9, anchor=tk.CENTER) 
        
        self.canvas.bind("<ButtonPress-1>", self.on_press) 
        self.canvas.bind("<B1-Motion>", self.on_drag) 
        self.canvas.bind("<ButtonRelease-1>", self.on_release) 
        self.canvas.bind("<Button-3>", self.reset)  # 右键重置 
        
        self.root.mainloop() 
    
    def on_press(self, event): 
        self.start_x = event.x 
        self.start_y = event.y 
    
    def on_drag(self, event): 
        if self.start_x is None or self.start_y is None: 
            return 
        if self.drawing_line == 1: 
            if self.line1: 
                self.canvas.delete(self.line1) 
            self.line1 = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, fill="red", width=2) 
        elif self.drawing_line == 2: 
            if self.line2: 
                self.canvas.delete(self.line2) 
            self.line2 = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, fill="lime", width=2) 
    
    def on_release(self, event): 
        if self.start_x is None or self.start_y is None: 
            return 
        if self.drawing_line == 1: 
            self.drawing_line = 2 
            self.status_label.config(text="拖动鼠标画第二条线 (右键重置)") 
        elif self.drawing_line == 2: 
            self.drawing_line = 1  # 重置状态 
            self.status_label.config(text="已完成测量 (右键重置)") 
            self.calculate_angle() 
        self.start_x = None 
        self.start_y = None 
    
    def calculate_angle(self): 
        if not self.line1 or not self.line2: 
            return 
        # 获取第一条线的坐标 
        coords1 = self.canvas.coords(self.line1) 
        x1, y1, x2, y2 = coords1 
        v1 = (x2 - x1, y2 - y1) 
        # 获取第二条线的坐标 
        coords2 = self.canvas.coords(self.line2) 
        x3, y3, x4, y4 = coords2 
        v2 = (x4 - x3, y4 - y3) 
        
        # 计算夹角 
        dot = v1[0]*v2[0] + v1[1]*v2[1] 
        mag1 = math.hypot(v1[0], v1[1]) 
        mag2 = math.hypot(v2[0], v2[1]) 
        if mag1 == 0 or mag2 == 0: 
            angle = 0 
        else: 
            cos_val = dot / (mag1 * mag2) 
            cos_val = max(-1.0, min(1.0, cos_val))  # 限制范围 
            angle = math.degrees(math.acos(cos_val)) 
        
        self.angle_label.config(text=f"角度: {angle:.1f}°") 
    
    def reset(self, event=None): 
        self.canvas.delete("all") 
        self.line1 = None 
        self.line2 = None 
        self.drawing_line = 1 
        self.angle_label.config(text="角度: --°") 
        self.status_label.config(text="拖动鼠标画第一条线") 

if __name__ == "__main__": 
    AngleMeter()