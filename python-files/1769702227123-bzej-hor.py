import tkinter as tk
import math


class SimpleArtificialHorizon:
  """مؤشر أفق صناعي مبسط مع حركة سلسة"""
  
  def __init__(self, root):
    self.root = root
    self.root.title("Simple Artificial Horizon")
    self.root.geometry("600x700")
    
    # قيم المحاكاة
    self.pitch = 0  # degrees
    self.roll = 0  # degrees
    
    # ألوان
    self.sky_color = "#87CEEB"
    self.ground_color = "#8B4513"
    self.horizon_color = "#FFFF00"
    self.aircraft_color = "#FFFFFF"
    self.text_color = "#00FF00"
    
    # إنشاء الواجهة
    self.setup_ui()
    self.animate()
  
  def setup_ui(self):
    """إعداد واجهة المستخدم"""
    self.root.configure(bg="black")
    
    # العنوان
    tk.Label(self.root, text="ARTIFICIAL HORIZON",
        font=("Arial", 16, "bold"),
        fg="white", bg="black").pack(pady=10)
    
    # المؤشر
    self.canvas = tk.Canvas(self.root, width=500, height=500, bg="black")
    self.canvas.pack(pady=10)
    
    # أدوات التحكم
    self.setup_controls()
    
    # معلومات
    self.info_label = tk.Label(self.root,
                 text="Pitch: 0° | Roll: 0° | Level Flight",
                 font=("Arial", 12, "bold"),
                 fg=self.text_color, bg="black")
    self.info_label.pack(pady=10)
  
  def setup_controls(self):
    """إعداد أدوات التحكم"""
    control_frame = tk.Frame(self.root, bg="gray")
    control_frame.pack(pady=10)
    
    # التحكم في الميل الأمامي/الخلفي
    tk.Label(control_frame, text="Pitch:", bg="gray").pack()
    self.pitch_slider = tk.Scale(control_frame, from_=-30, to=30,
                  orient="horizontal", length=300)
    self.pitch_slider.set(0)
    self.pitch_slider.pack()
    
    # التحكم في الميل الجانبي
    tk.Label(control_frame, text="Roll:", bg="gray").pack(pady=10)
    self.roll_slider = tk.Scale(control_frame, from_=-60, to=60,
                  orient="horizontal", length=300)
    self.roll_slider.set(0)
    self.roll_slider.pack()
    
    # أزرار أوضاع الطيران
    btn_frame = tk.Frame(control_frame, bg="gray")
    btn_frame.pack(pady=10)
    
    modes = [
      ("Level", (0, 0)),
      ("Climb", (10, 0)),
      ("Descend", (-10, 0)),
      ("Bank Left", (0, -30)),
      ("Bank Right", (0, 30)),
      ("Climb & Bank", (15, 25))
    ]
    
    for text, values in modes:
      btn = tk.Button(btn_frame, text=text, width=10,
              command=lambda v=values: self.set_attitude(v))
      btn.pack(side="left", padx=2)
  
  def draw_horizon(self):
    """رسم الأفق الصناعي"""
    self.canvas.delete("all")
    
    w, h = 500, 500
    cx, cy = w//2, h//2
    
    # تحويل القيم
    pitch = self.pitch
    roll = math.radians(self.roll)
    
    # حساب إزاحة الأفق بناءً على الميل
    horizon_offset = pitch * 3  # 3 بكسل لكل درجة
    
    # رسم السماء (مع الميل الجانبي)
    sky_points = []
    for x in range(-250, 251, 50):
      # النقاط الأصلية
      y_original = -horizon_offset
      
      # تطبيق الدوران حول المركز
      x_rot = cx + x * math.cos(roll) - y_original * math.sin(roll)
      y_rot = cy + x * math.sin(roll) + y_original * math.cos(roll)
      
      sky_points.extend([x_rot, y_rot])
    
    # إكمال المضلع
    if sky_points:
      sky_points.extend([w, 0, 0, 0])
      self.canvas.create_polygon(sky_points, fill=self.sky_color, outline="")
    
    # رسم الأرض (مع الميل الجانبي)
    ground_points = []
    for x in range(-250, 251, 50):
      # النقاط الأصلية
      y_original = -horizon_offset
      
      # تطبيق الدوران حول المركز
      x_rot = cx + x * math.cos(roll) - y_original * math.sin(roll)
      y_rot = cy + x * math.sin(roll) + y_original * math.cos(roll)
      
      ground_points.extend([x_rot, y_rot])
    
    # إكمال المضلع
    if ground_points:
      ground_points.extend([w, h, 0, h])
      self.canvas.create_polygon(ground_points, fill=self.ground_color, outline="")
    
    # خط الأفق (مع الميل الجانبي)
    length = 250
    x1 = cx - length
    y1 = cy - horizon_offset
    x2 = cx + length
    y2 = cy - horizon_offset
    
    x1_rot = cx + (x1 - cx) * math.cos(roll) - (y1 - cy) * math.sin(roll)
    y1_rot = cy + (x1 - cx) * math.sin(roll) + (y1 - cy) * math.cos(roll)
    x2_rot = cx + (x2 - cx) * math.cos(roll) - (y2 - cy) * math.sin(roll)
    y2_rot = cy + (x2 - cx) * math.sin(roll) + (y2 - cy) * math.cos(roll)
    
    self.canvas.create_line(x1_rot, y1_rot, x2_rot, y2_rot,
                fill=self.horizon_color, width=3)
    
    # رسم رمز الطائرة (ثابت في المركز)
    self.draw_aircraft_symbol(cx, cy)
    
    # رسم سلم الميل
    self.draw_pitch_ladder(cx, cy, horizon_offset, roll)
    
    # رسم مؤشر الميل الجانبي
    self.draw_roll_indicator(cx, cy)
  
  def draw_aircraft_symbol(self, cx, cy):
    """رسم رمز الطائرة"""
    # مثلث علوي
    self.canvas.create_polygon(
      cx - 15, cy - 30,
      cx, cy - 50,
      cx + 15, cy - 30,
      fill=self.aircraft_color, outline="black"
    )
    
    # جسم الطائرة
    self.canvas.create_line(cx - 60, cy, cx + 60, cy,
                fill=self.aircraft_color, width=3)
    
    # أجنحة
    self.canvas.create_line(cx - 60, cy, cx - 60, cy + 15,
                fill=self.aircraft_color, width=2)
    self.canvas.create_line(cx + 60, cy, cx + 60, cy + 15,
                fill=self.aircraft_color, width=2)
  
  def draw_pitch_ladder(self, cx, cy, offset, roll):
    """رسم سلم الميل"""
    # خطوط الميل
    for pitch in range(-20, 21, 5):
      if pitch == 0:
        continue
      
      y_pos = cy - offset + (pitch * 3)
      
      # تطبيق الدوران
      x1 = cx - 30
      y1 = y_pos
      x2 = cx + 30
      y2 = y_pos
      
      x1_rot = cx + (x1 - cx) * math.cos(roll) - (y1 - cy) * math.sin(roll)
      y1_rot = cy + (x1 - cx) * math.sin(roll) + (y1 - cy) * math.cos(roll)
      x2_rot = cx + (x2 - cx) * math.cos(roll) - (y2 - cy) * math.sin(roll)
      y2_rot = cy + (x2 - cx) * math.sin(roll) + (y2 - cy) * math.cos(roll)
      
      # اللون بناءً على الاتجاه
      color = "green" if pitch > 0 else "red"
      
      self.canvas.create_line(x1_rot, y1_rot, x2_rot, y2_rot,
                  fill=color, width=2)
      
      # النص
      text_x = cx - 40 if pitch > 0 else cx + 40
      text_y = y_pos
      
      text_x_rot = cx + (text_x - cx) * math.cos(roll) - (text_y - cy) * math.sin(roll)
      text_y_rot = cy + (text_x - cx) * math.sin(roll) + (text_y - cy) * math.cos(roll)
      
      self.canvas.create_text(text_x_rot, text_y_rot,
                  text=str(abs(pitch)),
                  font=("Arial", 8, "bold"),
                  fill=color,
                  angle=math.degrees(-roll))
  
  def draw_roll_indicator(self, cx, cy):
    """رسم مؤشر الميل الجانبي"""
    radius = 150
    
    # دائرة الميل
    self.canvas.create_oval(cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline="white", width=1)
    
    # علامات الميل
    for angle in [10, 20, 30, 45, 60]:
      for side in [-1, 1]:
        actual_angle = angle * side
        angle_rad = math.radians(actual_angle)
        
        # طول العلامة
        inner = radius - 20 if angle <= 30 else radius - 25
        outer = radius - 5 if angle <= 30 else radius - 10
        
        x1 = cx + inner * math.sin(angle_rad)
        y1 = cy - inner * math.cos(angle_rad)
        x2 = cx + outer * math.sin(angle_rad)
        y2 = cy - outer * math.cos(angle_rad)
        
        color = "white" if angle <= 30 else "red"
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
    
    # المؤشر العلوي
    self.canvas.create_polygon(
      cx, cy - radius + 10,
      cx - 10, cy - radius + 25,
      cx + 10, cy - radius + 25,
      fill="yellow", outline="white"
    )
  
  def set_attitude(self, values):
    """تعيين وضع طيران محدد"""
    pitch, roll = values
    self.pitch_slider.set(pitch)
    self.roll_slider.set(roll)
  
  def animate(self):
    """تحديث الرسوم المتحركة"""
    # قراءة القيم من أشرطة التمرير
    self.pitch = self.pitch_slider.get()
    self.roll = self.roll_slider.get()
    
    # رسم الأفق
    self.draw_horizon()
    
    # تحديث المعلومات
    status = "LEVEL"
    if abs(self.pitch) > 5:
      status = "CLIMBING" if self.pitch > 0 else "DESCENDING"
    if abs(self.roll) > 10:
      status += " & BANKING"
    
    self.info_label.config(
      text=f"Pitch: {self.pitch:+03d}° | Roll: {self.roll:+03d}° | {status}"
    )
    
    # إضافة معلومات إضافية على المؤشر
    w, h = 500, 500
    cx, cy = w//2, h//2
    
    self.canvas.create_text(cx, 30, text="ARTIFICIAL HORIZON",
                font=("Arial", 12, "bold"),
                fill="white")
    
    # تحذير إذا كان الميل كبيراً
    if abs(self.pitch) > 25:
      self.canvas.create_text(cx, h - 30,
                  text="PITCH WARNING!",
                  font=("Arial", 14, "bold"),
                  fill="red")
    
    if abs(self.roll) > 45:
      self.canvas.create_text(cx, h - 50,
                  text="BANK ANGLE WARNING!",
                  font=("Arial", 14, "bold"),
                  fill="red")
    
    # الاستمرار
    self.root.after(50, self.animate)


# تشغيل النسخة المبسطة
if __name__ == "__main__":
  root = tk.Tk()
  app = SimpleArtificialHorizon(root)
  root.mainloop()
