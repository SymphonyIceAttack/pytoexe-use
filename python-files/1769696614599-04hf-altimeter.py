import tkinter as tk
from tkinter import ttk
import math


class AltimeterSimulator:
  def __init__(self, root):
    self.root = root
    self.root.title("مقياس الارتفاع - Altimeter")
    self.root.geometry("600x500")
    
    # قيم المحاكاة
    self.altitude = 5000  # قدم
    self.pressure = 1013.25  # hPa (ضغط ساكن)
    self.kollsman_setting = 1013.25  # hPa (ضبط كولسمان)
    self.vertical_speed = 0  # ft/min
    
    # إنشاء الواجهة
    self.create_widgets()
    self.update_display()
  
  def create_widgets(self):
    # العنوان
    title = tk.Label(self.root, text="مقياس الارتفاع (Altimeter)",
            font=("Arial", 16, "bold"))
    title.pack(pady=10)
    
    # إطار المؤشر
    self.gauge_frame = tk.Frame(self.root)
    self.gauge_frame.pack(pady=10)
    
    # إنشاء مؤشر الارتفاع
    self.canvas = tk.Canvas(self.gauge_frame, width=400, height=300, bg="black")
    self.canvas.pack()
    
    # عداد رقمي كبير للارتفاع
    self.digital_altitude = tk.Label(self.root, text="05000",
                    font=("Digital-7", 48, "bold"),
                    fg="white", bg="black",
                    width=8, height=2)
    self.digital_altitude.pack(pady=5)
    
    # تسمية الوحدة
    tk.Label(self.root, text="قدم", font=("Arial", 12)).pack()
    
    # إطار التحكم
    control_frame = tk.LabelFrame(self.root, text="التحكم", padx=10, pady=10)
    control_frame.pack(pady=10, padx=20, fill="x")
    
    # التحكم في الضغط الساكن
    tk.Label(control_frame, text="الضغط الساكن (hPa):").grid(row=0, column=0, sticky="w", pady=5)
    self.pressure_scale = tk.Scale(control_frame, from_=800, to=1100,
                   orient="horizontal", length=200,
                   command=self.update_pressure)
    self.pressure_scale.set(int(self.pressure))
    self.pressure_scale.grid(row=0, column=1, pady=5)
    
    # ضبط كولسمان (لتصحيح الارتفاع)
    tk.Label(control_frame, text="ضبط كولسمان (hPa):").grid(row=1, column=0, sticky="w", pady=5)
    self.kollsman_scale = tk.Scale(control_frame, from_=950, to=1050,
                   orient="horizontal", length=200,
                   command=self.update_kollsman)
    self.kollsman_scale.set(int(self.kollsman_setting))
    self.kollsman_scale.grid(row=1, column=1, pady=5)
    
    # أزرار التحكم السريع
    alt_frame = tk.Frame(control_frame)
    alt_frame.grid(row=2, column=0, columnspan=2, pady=10)
    
    tk.Label(alt_frame, text="تغيير الارتفاع:").pack(side="left", padx=5)
    
    altitudes = [0, 1000, 3000, 5000, 10000, 15000]
    for alt in altitudes:
      btn = tk.Button(alt_frame, text=f"{alt}", width=6,
              command=lambda a=alt: self.set_altitude(a))
      btn.pack(side="left", padx=2)
    
    # إطار معلومات
    info_frame = tk.Frame(self.root)
    info_frame.pack(pady=10)
    
    self.info_label = tk.Label(info_frame,
                 text=f"الارتفاع: {self.altitude} قدم | الضغط: {self.pressure} hPa",
                 font=("Arial", 10))
    self.info_label.pack()
    
    # معلومات تقنية
    tech_frame = tk.LabelFrame(self.root, text="معلومات تقنية", padx=10, pady=10)
    tech_frame.pack(pady=10, padx=20, fill="x")
    
    info_text = """
    مقياس الارتفاع (Altimeter):
    • يقيس الارتفاع بناءً على الضغط الجوي
    • يعتمد على الضغط الساكن فقط
    • يستخدم معادلة الغلاف الجوي القياسي (ISA)
    • يحتوي على ضبط كولسمان لتصحيح قراءة الارتفاع
    • العلاقة: كلما قل الضغط، زاد الارتفاع
    """
    
    tech_label = tk.Label(tech_frame, text=info_text, justify="right")
    tech_label.pack()
  
  def create_altimeter_dial(self):
    """إنشاء مؤشر مقياس الارتفاع"""
    self.canvas.delete("all")
    
    width = 400
    height = 300
    center_x = width // 2
    center_y = height // 2 + 30
    radius = 120
    
    # رسم الدائرة الخارجية
    self.canvas.create_oval(center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline="white", width=3)
    
    # رسم علامات الآلاف
    for angle in range(0, 360, 36):  # كل 36 درجة = 1000 قدم
      angle_rad = math.radians(angle)
      
      # طول العلامة
      inner_radius = radius - 20
      outer_radius = radius - 10
      
      # حساب إحداثيات العلامة
      x1 = center_x + inner_radius * math.sin(angle_rad)
      y1 = center_y - inner_radius * math.cos(angle_rad)
      x2 = center_x + outer_radius * math.sin(angle_rad)
      y2 = center_y - outer_radius * math.cos(angle_rad)
      
      # رسم العلامة
      self.canvas.create_line(x1, y1, x2, y2, fill="white", width=2)
      
      # إضافة رقم (كل 1000 قدم)
      value = (angle // 36) * 1000  # 0, 1000, 2000, ..., 9000, 10000
      if value <= 10000:  # تحديد النطاق
        text_radius = radius - 35
        x_text = center_x + text_radius * math.sin(angle_rad)
        y_text = center_y - text_radius * math.cos(angle_rad)
        
        self.canvas.create_text(x_text, y_text, text=str(value//1000),
                    fill="white", font=("Arial", 10))
    
    # رسم المؤشر (إبرة)
    # تحويل الارتفاع إلى زاوية (كل 1000 قدم = 36 درجة)
    alt_normalized = self.altitude % 10000  # نطاق 0-10000 قدم
    angle = (alt_normalized / 10000) * 360  # درجات
    angle_rad = math.radians(angle)
    
    # طول المؤشر
    needle_length = radius - 25
    
    # حساب نهاية المؤشر
    end_x = center_x + needle_length * math.sin(angle_rad)
    end_y = center_y - needle_length * math.cos(angle_rad)
    
    # رسم المؤشر
    self.canvas.create_line(center_x, center_y, end_x, end_y,
                fill="red", width=3)
    
    # رسم نقطة المركز
    self.canvas.create_oval(center_x-10, center_y-10,
                center_x+10, center_y+10,
                fill="black", outline="white", width=2)
    
    # إضافة نوافذ صغيرة للآلاف والعشرات (محاكاة للaltimeter الحقيقي)
    self.draw_windows(center_x, center_y)
  
  def draw_windows(self, center_x, center_y):
    """رسم نوافذ الأرقام (للآلاف والعشرات)"""
    # نافذة الآلاف (أعلى)
    self.canvas.create_rectangle(center_x - 40, center_y - 130,
                  center_x + 40, center_y - 110,
                  fill="black", outline="white")
    
    # عرض قيمة الآلاف
    thousands = self.altitude // 1000
    self.canvas.create_text(center_x, center_y - 120,
                text=str(thousands).zfill(2),
                fill="white", font=("Arial", 12, "bold"))
    
    # نافذة العشرات (أسفل)
    self.canvas.create_rectangle(center_x - 60, center_y - 70,
                  center_x + 60, center_y - 30,
                  fill="black", outline="white")
    
    # عرض قيمة المئات والعشرات
    hundreds_tens = (self.altitude % 1000) // 10
    self.canvas.create_text(center_x, center_y - 50,
                text=str(hundreds_tens).zfill(2),
                fill="white", font=("Arial", 16, "bold"))
  
  def calculate_altitude_from_pressure(self, pressure, kollsman=1013.25):
    """حساب الارتفاع من الضغط باستخدام معادلة الغلاف الجوي القياسي"""
    # معادلة مبسطة: h = 44330 * (1 - (P/P0)^(1/5.255))
    # حيث h بالأمتار، ثم نحول للقدم
    
    P0 = kollsman  # الضغط المرجعي
    P = pressure  # الضغط المقاس
    
    if P <= 0:
      return 0
    
    # حساب الارتفاع بالأمتار
    altitude_m = 44330 * (1 - (P / P0) ** (1 / 5.255))
    
    # تحويل للقدم
    altitude_ft = altitude_m * 3.28084
    
    return altitude_ft
  
  def calculate_pressure_from_altitude(self, altitude_ft, kollsman=1013.25):
    """حساب الضغط من الارتفاع"""
    # تحويل القدم لمتر
    altitude_m = altitude_ft / 3.28084
    
    # معادلة عكسية: P = P0 * (1 - h/44330)^5.255
    P0 = kollsman
    P = P0 * (1 - altitude_m / 44330) ** 5.255
    
    return P
  
  def update_pressure(self, value):
    """تحديث عند تغيير الضغط"""
    self.pressure = float(value)
    # إعادة حساب الارتفاع بناءً على الضغط الجديد
    self.altitude = self.calculate_altitude_from_pressure(self.pressure, self.kollsman_setting)
    self.update_display()
  
  def update_kollsman(self, value):
    """تحديث ضبط كولسمان"""
    self.kollsman_setting = float(value)
    # إعادة حساب الارتفاع مع الضبط الجديد
    self.altitude = self.calculate_altitude_from_pressure(self.pressure, self.kollsman_setting)
    self.update_display()
  
  def set_altitude(self, altitude):
    """تعيين ارتفاع محدد"""
    self.altitude = altitude
    # حساب الضغط المقابل لهذا الارتفاع
    self.pressure = self.calculate_pressure_from_altitude(altitude, self.kollsman_setting)
    self.pressure_scale.set(int(self.pressure))
    self.update_display()
  
  def update_display(self):
    """تحديث جميع عناصر العرض"""
    # تحديث المؤشر
    self.create_altimeter_dial()
    
    # تحديث العداد الرقمي
    self.digital_altitude.config(text=str(int(self.altitude)).zfill(5))
    
    # تحديث المعلومات
    self.info_label.config(
      text=f"الارتفاع: {int(self.altitude)} قدم | الضغط: {self.pressure:.1f} hPa | كولسمان: {self.kollsman_setting} hPa"
    )
    
    # تغيير لون العداد بناءً على الارتفاع
    if self.altitude < 1000:
      color = "green"
    elif self.altitude < 5000:
      color = "white"
    elif self.altitude < 10000:
      color = "yellow"
    else:
      color = "red"
    
    self.digital_altitude.config(fg=color)


# تشغيل المحاكاة
if __name__ == "__main__":
  root = tk.Tk()
  app = AltimeterSimulator(root)
  root.mainloop()