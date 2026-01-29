import tkinter as tk
import math


class PitotStaticAirspeed:
  """نظام Pitot-Static الكامل مع حسابات فيزيائية دقيقة"""
  
  def __init__(self, root):
    self.root = root
    self.root.title("Pitot-Static Airspeed System")
    self.root.geometry("700x800")
    
    # ثوابت فيزيائية
    self.gamma = 1.4    # نسبة السعات الحرارية
    self.R = 287.05    # J/(kg·K)
    self.P0 = 101325    # Pa (ضغط مستوى البحر)
    self.T0 = 288.15    # K (حرارة مستوى البحر)
    self.RHO0 = 1.225   # kg/m³ (كثافة مستوى البحر)
    
    # متغيرات النظام
    self.P_total = 101325  # Pa
    self.P_static = 101325  # Pa
    self.altitude = 0    # m
    self.temperature = 15  # °C
    
    # إنشاء الواجهة
    self.setup_ui()
    self.update_airspeed()
  
  def setup_ui(self):
    """إعداد واجهة المستخدم"""
    # العنوان
    tk.Label(self.root, text="PITOT-STATIC AIRSPEED SYSTEM",
        font=("Arial", 16, "bold")).pack(pady=10)
    
    tk.Label(self.root, text="نظام قياس سرعة الهواء بالضغط",
        font=("Arial", 12)).pack()
    
    # إطار المؤشر
    self.canvas = tk.Canvas(self.root, width=500, height=300, bg="black")
    self.canvas.pack(pady=20)
    
    # إطار التحكم في الضغط
    self.setup_pressure_controls()
    
    # إطار النتائج
    self.setup_results_display()
    
    # معلومات النظام
    self.setup_system_diagram()
  
  def setup_pressure_controls(self):
    """إعداد أدوات التحكم في الضغط"""
    frame = tk.LabelFrame(self.root, text="Pressure Controls", padx=10, pady=10)
    frame.pack(pady=10, padx=20, fill="x")
    
    # شريط الضغط الكلي
    tk.Label(frame, text="Total Pressure (Pitot):").grid(row=0, column=0, sticky="w")
    self.p_total_slider = tk.Scale(frame, from_=90000, to=110000,
                   orient="horizontal", length=300)
    self.p_total_slider.set(101325)
    self.p_total_slider.grid(row=0, column=1)
    tk.Label(frame, text="Pa").grid(row=0, column=2)
    
    # شريط الضغط الساكن
    tk.Label(frame, text="Static Pressure:").grid(row=1, column=0, sticky="w", pady=10)
    self.p_static_slider = tk.Scale(frame, from_=70000, to=101325,
                    orient="horizontal", length=300)
    self.p_static_slider.set(101325)
    self.p_static_slider.grid(row=1, column=1, pady=10)
    tk.Label(frame, text="Pa").grid(row=1, column=2)
    
    # أزرار أوضاع الطيران
    modes_frame = tk.Frame(frame)
    modes_frame.grid(row=2, column=0, columnspan=3, pady=10)
    
    modes = [
      ("Parked (V=0)", 101325, 101325),
      ("Taxi (V=30)", 101350, 101325),
      ("Takeoff (V=80)", 101600, 101300),
      ("Climb (V=120)", 102000, 100000),
      ("Cruise (V=250)", 104000, 90000)
    ]
    
    for text, p_total, p_static in modes:
      btn = tk.Button(modes_frame, text=text, width=15,
              command=lambda pt=p_total, ps=p_static: self.set_pressures(pt, ps))
      btn.pack(side="left", padx=2)
  
  def setup_results_display(self):
    """إعداد عرض النتائج"""
    frame = tk.LabelFrame(self.root, text="Airspeed Results", padx=10, pady=10)
    frame.pack(pady=10, padx=20, fill="x")
    
    # سرعات متنوعة
    self.results = {}
    labels = [
      ("Indicated Airspeed (IAS):", "IAS", "knots"),
      ("True Airspeed (TAS):", "TAS", "knots"),
      ("Calibrated Airspeed (CAS):", "CAS", "knots"),
      ("Mach Number:", "Mach", ""),
      ("Dynamic Pressure (q):", "q", "Pa")
    ]
    
    for i, (label, key, unit) in enumerate(labels):
      tk.Label(frame, text=label, font=("Arial", 9)).grid(row=i, column=0, sticky="w", pady=5)
      
      value_label = tk.Label(frame, text="0", font=("Arial", 10, "bold"), fg="blue")
      value_label.grid(row=i, column=1, padx=10, pady=5)
      
      if unit:
        tk.Label(frame, text=unit).grid(row=i, column=2, padx=5)
      
      self.results[key] = value_label
  
  def setup_system_diagram(self):
    """إعداد رسم تخطيطي للنظام"""
    frame = tk.LabelFrame(self.root, text="Pitot-Static System Diagram", padx=10, pady=10)
    frame.pack(pady=10, padx=20, fill="x")
    
    # رسم تخطيطي مبسط
    diagram_canvas = tk.Canvas(frame, width=600, height=150, bg="white")
    diagram_canvas.pack()
    
    # رسم أنبوب Pitot
    diagram_canvas.create_rectangle(50, 50, 80, 100, fill="gray")  # أنبوب
    diagram_canvas.create_oval(45, 45, 85, 55, fill="gray")  # فتحة
    
    # رسم أنبوب Static
    diagram_canvas.create_rectangle(150, 50, 180, 100, fill="lightblue")
    
    # توصيلات إلى ASI
    diagram_canvas.create_line(80, 75, 200, 75, fill="red", width=2)  # Pitot
    diagram_canvas.create_line(150, 75, 200, 75, fill="blue", width=2)  # Static
    
    # ASI
    diagram_canvas.create_rectangle(200, 40, 280, 110, fill="black", outline="gray")
    diagram_canvas.create_text(240, 75, text="ASI", fill="white", font=("Arial", 10, "bold"))
    
    # تسميات
    diagram_canvas.create_text(65, 30, text="Pitot Tube", font=("Arial", 8))
    diagram_canvas.create_text(165, 30, text="Static Port", font=("Arial", 8))
    diagram_canvas.create_text(240, 120, text="Airspeed Indicator", font=("Arial", 8))
    
    # معادلة
    diagram_canvas.create_text(400, 75, text="V = √(2(P\u2091 - P\u209B)/ρ)",
                 font=("Arial", 12, "bold"))
  
  def calculate_airspeed(self):
    """حساب سرعة الهواء من الضغط"""
    P_total = self.P_total
    P_static = self.P_static
    
    # حساب فرق الضغط
    q = P_total - P_static  # Dynamic pressure
    
    if q <= 0:
      return 0, 0, 0, 0, q
    
    # حساب كثافة الهواء (ISA نموذج مبسط)
    altitude = self.altitude
    T = self.temperature + 273.15
    rho = self.RHO0 * (P_static / self.P0) * (self.T0 / T)
    
    # للمسرعات دون الصوتية
    V_ms = math.sqrt(2 * q / rho)
    
    # تحويل الوحدات
    V_knots = V_ms * 1.94384
    
    # حساب رقم ماخ
    a = math.sqrt(self.gamma * self.R * T)  # سرعة الصوت
    mach = V_ms / a if a > 0 else 0
    
    # محاكاة IAS, TAS, CAS
    IAS = V_knots
    TAS = V_knots * math.sqrt(self.RHO0 / rho)
    CAS = IAS  # تبسيط
    
    return IAS, TAS, CAS, mach, q
  
  def update_airspeed(self):
    """تحديث حساب وعرض سرعة الهواء"""
    # قراءة القيم من أشرطة التمرير
    self.P_total = self.p_total_slider.get()
    self.P_static = self.p_static_slider.get()
    
    # الحساب
    IAS, TAS, CAS, mach, q = self.calculate_airspeed()
    
    # تحديث النتائج
    self.results["IAS"].config(text=f"{IAS:.1f}")
    self.results["TAS"].config(text=f"{TAS:.1f}")
    self.results["CAS"].config(text=f"{CAS:.1f}")
    self.results["Mach"].config(text=f"{mach:.3f}")
    self.results["q"].config(text=f"{q:.0f}")
    
    # رسم المؤشر
    self.draw_airspeed_indicator(IAS)
    
    # تحديث بعد 100ms
    self.root.after(100, self.update_airspeed)
  
  def draw_airspeed_indicator(self, speed):
    """رسم مؤشر سرعة الهواء"""
    self.canvas.delete("all")
    
    w, h = 500, 300
    cx, cy = w//2, h//2
    radius = 120
    
    # خلفية القرص
    self.canvas.create_oval(cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill="#111111", outline="white", width=2)
    
    # علامات السرعة
    for s in range(0, 401, 20):
      angle = (s / 400) * 300  # 300 درجة
      angle_rad = math.radians(angle)
      
      # طول العلامة
      if s % 40 == 0:
        inner = radius - 20
        outer = radius - 5
        
        # النص
        text_radius = radius - 30
        x = cx + text_radius * math.sin(angle_rad)
        y = cy - text_radius * math.cos(angle_rad)
        self.canvas.create_text(x, y, text=str(s), fill="white", font=("Arial", 8))
      else:
        inner = radius - 15
        outer = radius - 5
      
      # رسم العلامة
      x1 = cx + inner * math.sin(angle_rad)
      y1 = cy - inner * math.cos(angle_rad)
      x2 = cx + outer * math.sin(angle_rad)
      y2 = cy - outer * math.cos(angle_rad)
      self.canvas.create_line(x1, y1, x2, y2, fill="white", width=1)
    
    # إبرة السرعة
    speed = min(speed, 400)
    angle = (speed / 400) * 300
    angle_rad = math.radians(angle)
    
    end_x = cx + (radius - 25) * math.sin(angle_rad)
    end_y = cy - (radius - 25) * math.cos(angle_rad)
    
    self.canvas.create_line(cx, cy, end_x, end_y, fill="red", width=3)
    
    # نقطة المركز
    self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8,
                fill="black", outline="white", width=2)
    
    # عرض رقمي
    self.canvas.create_text(cx, cy + radius + 20,
                text=f"{speed:.0f} KNOTS",
                font=("Arial", 14, "bold"),
                fill="#00ff00")
    
    # معلومات الضغط
    q = self.P_total - self.P_static
    self.canvas.create_text(cx, cy + radius + 40,
                text=f"ΔP = {q:.0f} Pa",
                font=("Arial", 10),
                fill="#ffff00")
  
  def set_pressures(self, p_total, p_static):
    """تعيين قيم ضغط محددة"""
    self.p_total_slider.set(p_total)
    self.p_static_slider.set(p_static)


# تشغيل المحاكاة
if __name__ == "__main__":
  root = tk.Tk()
  app = PitotStaticAirspeed(root)
  root.mainloop()