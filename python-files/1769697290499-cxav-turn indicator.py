import tkinter as tk
from tkinter import ttk
import math
import time


class TurnIndicator:
  """محاكاة مؤشر الانعطاف (Turn Indicator / Turn Coordinator)"""
  
  def __init__(self, root):
    self.root = root
    self.root.title("مؤشر الانعطاف - Turn Indicator")
    self.root.geometry("600x700")
    
    # متغيرات المحاكاة
    self.turn_rate = 0.0  # معدل الانعطاف (درجة/ثانية)
    self.bank_angle = 0.0  # زاوية الميلان (درجة)
    self.slip_ball = 0.0  # موضع كرة الانزلاق (-1 إلى +1)
    self.heading = 0.0  # الاتجاه (درجة)
    
    # محاكاة الطيران
    self.roll_rate = 0.0  # معدل الدوران حول المحور الطولي
    self.yaw_rate = 0.0  # معدل الانعراج
    self.is_coordinated = True  # هل الانعطاف منسق؟
    
    # إنشاء الواجهة
    self.create_widgets()
    
    # بدء المحاكاة
    self.last_update = time.time()
    self.update_simulation()
  
  def create_widgets(self):
    # العنوان
    title = tk.Label(self.root, text="مؤشر الانعطاف (Turn Indicator)",
            font=("Arial", 16, "bold"))
    title.pack(pady=10)
    
    # إطار المؤشر الرئيسي
    self.gauge_frame = tk.Frame(self.root, bg="black")
    self.gauge_frame.pack(pady=10)
    
    # لوحة المؤشر
    self.canvas = tk.Canvas(self.gauge_frame, width=400, height=400,
                bg="black", highlightthickness=0)
    self.canvas.pack()
    
    # مؤشر رقمي
    self.turn_display = tk.Label(self.root, text="0.0°/sec",
                  font=("Digital-7", 32, "bold"),
                  fg="cyan", bg="black")
    self.turn_display.pack(pady=5)
    
    # إطار التحكم
    control_frame = tk.LabelFrame(self.root, text="التحكم في المحاكاة",
                   padx=10, pady=10)
    control_frame.pack(pady=10, padx=20, fill="x")
    
    # التحكم في معدل الانعطاف
    tk.Label(control_frame, text="معدل الانعطاف (°/sec):").grid(row=0, column=0, sticky="w", pady=5)
    self.turn_slider = tk.Scale(control_frame, from_=-30.0, to=30.0,
                  resolution=0.5, orient="horizontal", length=300)
    self.turn_slider.set(0.0)
    self.turn_slider.grid(row=0, column=1, pady=5)
    
    # التحكم في زاوية الميلان
    tk.Label(control_frame, text="زاوية الميلان (°):").grid(row=1, column=0, sticky="w", pady=5)
    self.bank_slider = tk.Scale(control_frame, from_=-60.0, to=60.0,
                  resolution=1.0, orient="horizontal", length=300)
    self.bank_slider.set(0.0)
    self.bank_slider.grid(row=1, column=1, pady=5)
    
    # التحكم في كرة الانزلاق
    tk.Label(control_frame, text="كرة الانزلاق:").grid(row=2, column=0, sticky="w", pady=5)
    self.slip_slider = tk.Scale(control_frame, from_=-1.0, to=1.0,
                  resolution=0.1, orient="horizontal", length=300)
    self.slip_slider.set(0.0)
    self.slip_slider.grid(row=2, column=1, pady=5)
    
    # أزرار أوضاع الطيران المحددة
    tk.Label(control_frame, text="أوضاع طيران سريعة:").grid(row=3, column=0, sticky="w", pady=10)
    
    flight_modes_frame = tk.Frame(control_frame)
    flight_modes_frame.grid(row=3, column=1, pady=10)
    
    modes = [
      (" طيران مستقيم", self.straight_flight),
      ("↪ انعطاف يسار قياسي", lambda: self.standard_turn(-3.0)),
      ("↩ انعطاف يمين قياسي", lambda: self.standard_turn(3.0)),
      (" انعطاف حاد يسار", lambda: self.sharp_turn(-6.0)),
      (" انعطاف حاد يمين", lambda: self.sharp_turn(6.0)),
      ("⚠ انعطاف غير منسق", self.uncoordinated_turn),
      (" انزلاق بالكرة", self.slip_only)
    ]
    
    for i, (text, command) in enumerate(modes):
      btn = tk.Button(flight_modes_frame, text=text, width=20,
              command=command)
      btn.grid(row=i//2, column=i%2, padx=2, pady=2)
    
    # معلومات إضافية
    info_frame = tk.Frame(self.root)
    info_frame.pack(pady=10)
    
    self.info_label = tk.Label(info_frame,
                 text="معدل الانعطاف القياسي: 3°/sec (انعطاف كامل في دقيقتين)",
                 font=("Arial", 10))
    self.info_label.pack()
    
    # رسم المؤشر للمرة الأولى
    self.draw_turn_indicator()
  
  def draw_turn_indicator(self):
    """رسم مؤشر الانعطاف"""
    self.canvas.delete("all")
    
    width = 400
    height = 400
    center_x = width // 2
    center_y = height // 2
    
    # تقسيم الرسم إلى جزئين: الأعلى للمؤشر الدائري، الأسفل لكرة الانزلاق
    indicator_height = 300
    
    # رسم المؤشر الدائري (الجزء العلوي)
    self.draw_turn_dial(center_x, center_y - 50, indicator_height)
    
    # رسم كرة الانزلاق (الجزء السفلي)
    self.draw_slip_ball(center_x, center_y + 100, 200)
    
    # إضافة تسميات
    self.canvas.create_text(center_x, 20, text="TURN INDICATOR",
                fill="white", font=("Arial", 12, "bold"))
  
  def draw_turn_dial(self, cx, cy, height):
    """رسم القرص الدائري لمؤشر الانعطاف"""
    radius = height // 2 - 20
    
    # رسم الدائرة الخارجية
    self.canvas.create_oval(cx - radius, cy - radius,
                cx + radius, cy + radius,
                outline="white", width=3)
    
    # رسم الطائرة الصغيرة في المنتصف
    self.draw_airplane_symbol(cx, cy)
    
    # رسم علامات معدل الانعطاف
    self.draw_turn_marks(cx, cy, radius)
    
    # رسم الإبرة المؤشرة
    self.draw_turn_needle(cx, cy, radius)
  
  def draw_airplane_symbol(self, cx, cy):
    """رسم رمز الطائرة الصغير"""
    # جسم الطائرة
    self.canvas.create_line(cx - 40, cy, cx + 40, cy,
                fill="white", width=3)
    
    # الجناح الأيمن
    self.canvas.create_line(cx + 10, cy, cx + 20, cy - 15,
                fill="white", width=2)
    
    # الجناح الأيسر
    self.canvas.create_line(cx - 10, cy, cx - 20, cy - 15,
                fill="white", width=2)
    
    # الذيل
    self.canvas.create_line(cx - 30, cy, cx - 40, cy - 10,
                fill="white", width=2)
    
    # إضافة تأثير الميلان
    self.draw_bank_indicator(cx, cy)
  
  def draw_bank_indicator(self, cx, cy):
    """رسم مؤشر الميلان"""
    # تحويل زاوية الميلان إلى راديان
    bank_rad = math.radians(self.bank_angle)
    
    # خط الأفق مع الميلان
    length = 50
    x1 = cx - length * math.cos(bank_rad)
    y1 = cy - length * math.sin(bank_rad)
    x2 = cx + length * math.cos(bank_rad)
    y2 = cy + length * math.sin(bank_rad)
    
    self.canvas.create_line(x1, y1, x2, y2,
                fill="white", width=2)
    
    # إضافة خطوط صغيرة للإشارة للميلان
    for offset in [-30, -15, 0, 15, 30]:
      dx = offset * math.cos(bank_rad)
      dy = offset * math.sin(bank_rad)
      
      perp_dx = 10 * math.sin(bank_rad)
      perp_dy = -10 * math.cos(bank_rad)
      
      self.canvas.create_line(cx + dx - perp_dx, cy + dy - perp_dy,
                  cx + dx + perp_dx, cy + dy + perp_dy,
                  fill="white", width=1)
  
  def draw_turn_marks(self, cx, cy, radius):
    """رسم علامات معدل الانعطاف"""
    # معدل الانعطاف القياسي (Standard Rate Turn): 3°/sec
    # في المؤشر الحقيقي، عندما تكون الإبرة على علامة "L" أو "R"
    # فهذا يعني انعطافاً قياسياً (3°/sec أو 360° في دقيقتين)
    
    # رسم علامة L (يسار)
    self.canvas.create_text(cx - radius + 30, cy - 20, text="L",
                fill="white", font=("Arial", 14, "bold"))
    
    # رسم علامة R (يمين)
    self.canvas.create_text(cx + radius - 30, cy - 20, text="R",
                fill="white", font=("Arial", 14, "bold"))
    
    # رسم النقاط الصغيرة بين L و R
    for x_offset in range(-60, 61, 20):
      if x_offset == 0:
        # نقطة المنتصف (لا انعطاف)
        self.canvas.create_oval(cx - 3, cy - 25, cx + 3, cy - 19,
                    fill="white", outline="white")
      else:
        # النقاط الجانبية
        self.canvas.create_oval(cx + x_offset - 2, cy - 22,
                    cx + x_offset + 2, cy - 18,
                    fill="white", outline="white")
    
    # إضافة خطوط تشير لزوايا الميلان
    self.draw_bank_marks(cx, cy, radius)
  
  def draw_bank_marks(self, cx, cy, radius):
    """رسم علامات زوايا الميلان"""
    # زوايا الميلان الشائعة: 10°, 20°, 30°, 45°, 60°
    bank_angles = [10, 20, 30, 45, 60]
    
    for angle in bank_angles:
      # للجانبين الأيمن والأيسر
      for side in [-1, 1]:
        actual_angle = angle * side
        angle_rad = math.radians(actual_angle)
        
        # حساب موضع العلامة على محيط الدائرة
        mark_radius = radius - 40
        x = cx + mark_radius * math.sin(angle_rad)
        y = cy - mark_radius * math.cos(angle_rad)
        
        # رسم خط قصير
        inner_x = cx + (mark_radius - 10) * math.sin(angle_rad)
        inner_y = cy - (mark_radius - 10) * math.cos(angle_rad)
        
        self.canvas.create_line(inner_x, inner_y, x, y,
                    fill="white", width=1)
        
        # إضافة النص لزوايا كبيرة
        if angle >= 30:
          text_x = cx + (mark_radius - 25) * math.sin(angle_rad)
          text_y = cy - (mark_radius - 25) * math.cos(angle_rad)
          self.canvas.create_text(text_x, text_y, text=str(angle),
                      fill="white", font=("Arial", 8))
  
  def draw_turn_needle(self, cx, cy, radius):
    """رسم إبرة مؤشر الانعطاف"""
    # تحويل معدل الانعطاف إلى موضع
    # نطاق الانعطاف: ±30°/sec يتحول إلى ±60 بكسل
    turn_range = 30.0  # درجة/ثانية
    max_offset = 60  # بكسل
    
    offset = (self.turn_rate / turn_range) * max_offset
    offset = max(-max_offset, min(max_offset, offset))
    
    # رسم الإبرة (مثلث صغير)
    needle_y = cy - 30  # ارتفاع ثابت للإبرة
    
    # قاعدة المثلث
    base_width = 8
    tip_x = cx + offset
    tip_y = needle_y - 15
    
    # رسم المثلث
    self.canvas.create_polygon(
      tip_x, tip_y,  # رأس المثلث
      tip_x - base_width, needle_y,  # قاعدة يسار
      tip_x + base_width, needle_y,  # قاعدة يمين
      fill="red", outline="white"
    )
    
    # خط دليل للإبرة
    self.canvas.create_line(cx, needle_y, tip_x, tip_y,
                fill="cyan", width=1, dash=(2, 2))
  
  def draw_slip_ball(self, cx, y_pos, width):
    """رسم كرة الانزلاق (Slip/Skid Indicator)"""
    # رسم الأنبوب الأفقي
    tube_width = 100
    tube_height = 15
    
    self.canvas.create_rectangle(cx - tube_width//2, y_pos - tube_height//2,
                  cx + tube_width//2, y_pos + tube_height//2,
                  fill="black", outline="white", width=2)
    
    # رسم كرة الانزلاق
    ball_radius = 10
    ball_x = cx + (self.slip_ball * (tube_width//2 - ball_radius))
    ball_x = max(cx - tube_width//2 + ball_radius,
          min(cx + tube_width//2 - ball_radius, ball_x))
    
    self.canvas.create_oval(ball_x - ball_radius, y_pos - ball_radius,
                ball_x + ball_radius, y_pos + ball_radius,
                fill="yellow", outline="black", width=2)
    
    # إضافة تسمية
    self.canvas.create_text(cx, y_pos + 25, text="SLIP/SKID",
                fill="white", font=("Arial", 10))
    
    # إضافة خطوط التقسيم
    for offset in [-25, 0, 25]:
      self.canvas.create_line(cx + offset, y_pos - 10,
                  cx + offset, y_pos + 10,
                  fill="white", width=1)
  
  def update_simulation(self):
    """تحديث المحاكاة"""
    # قراءة القيم من عناصر التحكم
    self.turn_rate = self.turn_slider.get()
    self.bank_angle = self.bank_slider.get()
    self.slip_ball = self.slip_slider.get()
    
    # في الطيران الحقيقي، هناك علاقة بين معدل الانعطاف وزاوية الميلان
    # معادلة بسيطة: معدل الانعطاف ≈ (السرعة * tan(الميلان)) / نصف قطر الدوران
    # لكننا سنبقيها بسيطة للمحاكاة
    
    # تحديث العرض
    self.update_display()
    
    # الاستمرار في المحاكاة
    self.root.after(50, self.update_simulation)
  
  def update_display(self):
    """تحديث واجهة المستخدم"""
    # إعادة رسم المؤشر
    self.draw_turn_indicator()
    
    # تحديث العداد الرقمي
    self.turn_display.config(text=f"{self.turn_rate:+.1f}°/sec")
    
    # تغيير اللون بناءً على معدل الانعطاف
    if abs(self.turn_rate) > 6.0:
      color = "red"
    elif abs(self.turn_rate) > 3.0:
      color = "yellow"
    elif abs(self.turn_rate) > 0.5:
      color = "green"
    else:
      color = "cyan"
    
    self.turn_display.config(fg=color)
    
    # تحديث معلومات إضافية
    turn_time = 360 / abs(self.turn_rate) if self.turn_rate != 0 else 0
    turn_info = f"وقت الدوران الكامل: {turn_time:.1f} ثانية" if self.turn_rate != 0 else "طيران مستقيم"
    
    slip_status = "انزلاق يسار" if self.slip_ball < -0.3 else \
           "انزلاق يمين" if self.slip_ball > 0.3 else \
           "انعطاف منسق"
    
    self.info_label.config(
      text=f"معدل الانعطاف: {self.turn_rate:+.1f}°/sec | زاوية الميلان: {self.bank_angle:+.0f}° | {slip_status}"
    )
  
  def straight_flight(self):
    """طيران مستقيم"""
    self.turn_slider.set(0.0)
    self.bank_slider.set(0.0)
    self.slip_slider.set(0.0)
  
  def standard_turn(self, rate):
    """انعطاف قياسي (3°/sec)"""
    self.turn_slider.set(rate)
    self.bank_slider.set(15.0 if rate > 0 else -15.0)
    self.slip_slider.set(0.0)
  
  def sharp_turn(self, rate):
    """انعطاف حاد"""
    self.turn_slider.set(rate)
    self.bank_slider.set(30.0 if rate > 0 else -30.0)
    self.slip_slider.set(0.0)
  
  def uncoordinated_turn(self):
    """انعطاف غير منسق"""
    self.turn_slider.set(3.0)
    self.bank_slider.set(20.0)
    self.slip_slider.set(0.7)
  
  def slip_only(self):
    """انزلاق بالكرة فقط"""
    self.turn_slider.set(0.0)
    self.bank_slider.set(0.0)
    self.slip_slider.set(0.8)


# تشغيل المحاكاة
if __name__ == "__main__":
  root = tk.Tk()
  app = TurnIndicator(root)
  root.mainloop()