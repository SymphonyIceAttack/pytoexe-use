import tkinter as tk
import math


class PhysicalVSI:
  """VSI بمحاكاة فيزيائية دقيقة"""
  
  def __init__(self, root):
    self.root = root
    self.root.title("VSI - النموذج الفيزيائي")
    self.root.geometry("500x400")
    
    # ثوابت فيزيائية
    self.g = 9.80665  # m/s² (تسارع الجاذبية)
    self.R = 287.05  # J/(kg·K) (ثابت الغازات للهواء الجاف)
    self.L = 0.0065  # K/m (معدل انخفاض درجة الحرارة)
    self.T0 = 288.15  # K (درجة حرارة مستوى البحر)
    self.P0 = 1013.25  # hPa (ضغط مستوى البحر)
    
    # متغيرات المحاكاة
    self.altitude = 0  # m
    self.pressure = self.P0  # hPa
    self.dp_dt = 0.0  # hPa/ثانية
    self.vsi = 0.0  # m/ثانية
    
    # إنشاء الواجهة
    self.create_ui()
    self.update_display()
  
  def create_ui(self):
    # العنوان
    tk.Label(self.root, text="VSI - النموذج الفيزيائي الدقيق",
        font=("Arial", 14, "bold")).pack(pady=10)
    
    # مؤشر VSI
    self.canvas = tk.Canvas(self.root, width=200, height=200, bg="black")
    self.canvas.pack(pady=10)
    
    # عداد VSI
    self.vsi_display = tk.Label(self.root, text="0.0",
                  font=("Arial", 32, "bold"))
    self.vsi_display.pack()
    
    tk.Label(self.root, text="متر/ثانية").pack()
    
    # تحويل إلى قدم/دقيقة
    self.vsi_ft_display = tk.Label(self.root, text="0",
                   font=("Arial", 18))
    self.vsi_ft_display.pack()
    
    tk.Label(self.root, text="قدم/دقيقة").pack()
    
    # التحكم في معدل تغير الضغط
    frame = tk.Frame(self.root)
    frame.pack(pady=20)
    
    tk.Label(frame, text="dP/dt (hPa/ثانية):").pack()
    
    self.dp_slider = tk.Scale(frame, from_=-5.0, to=5.0,
                 resolution=0.1, orient="horizontal",
                 length=300, command=self.update_dp_dt)
    self.dp_slider.set(0.0)
    self.dp_slider.pack()
    
    # معلومات
    self.info_label = tk.Label(self.root,
                 text=f"الضغط: {self.pressure:.1f} hPa | الارتفاع: {self.altitude:.0f} m",
                 font=("Arial", 10))
    self.info_label.pack(pady=10)
    
    # بدء المحاكاة
    self.simulate()
  
  def calculate_vsi_from_dp_dt(self, dp_dt, pressure):
    """حساب VSI من dP/dt باستخدام المعادلات الفيزيائية"""
    if pressure <= 0:
      return 0.0
    
    # حساب dh/dP من معادلة الغلاف الجوي القياسي
    # h = (T0 / L) * (1 - (P/P0)^(R*L/g))
    # dh/dP = - (T0 * R) / (g * P0) * (P/P0)^(R*L/g - 1)
    
    # حساب الأس
    exponent = (self.R * self.L / self.g) - 1
    
    # حساب dh/dP
    dh_dp = - (self.T0 * self.R) / (self.g * self.P0) * \
        (pressure / self.P0) ** exponent
    
    # تحويل الوحدات (dh/dP بالأمتار لكل hPa)
    dh_dp_hpa = dh_dp * 100  # 1 hPa = 100 Pa
    
    # حساب VSI = dh/dt = (dh/dP) * (dP/dt)
    vsi_ms = dh_dp_hpa * dp_dt  # متر/ثانية
    
    return vsi_ms
  
  def update_dp_dt(self, value):
    """تحديث معدل تغير الضغط"""
    self.dp_dt = float(value)
  
  def simulate(self):
    """تشغيل المحاكاة"""
    # حساب VSI من dP/dt
    self.vsi = self.calculate_vsi_from_dp_dt(self.dp_dt, self.pressure)
    
    # تحديث الارتفاع (تكامل VSI)
    dt = 0.1  # ثانية
    self.altitude += self.vsi * dt
    
    # حساب الضغط الجديد من الارتفاع
    # P = P0 * (1 - (L * h) / T0)^(g/(R*L))
    if self.altitude >= 0:
      exponent = self.g / (self.R * self.L)
      self.pressure = self.P0 * (1 - (self.L * self.altitude) / self.T0) ** exponent
    else:
      self.pressure = self.P0
      self.altitude = 0
    
    # تحديث العرض
    self.update_display()
    
    # الاستمرار
    self.root.after(100, self.simulate)
  
  def update_display(self):
    """تحديث العرض"""
    # رسم المؤشر
    self.canvas.delete("all")
    
    w, h = 200, 200
    cx, cy = w//2, h//2
    
    # مقياس من -10 إلى +10 م/ثانية
    vs_max = 10  # م/ثانية
    
    # رسم خط الصفر
    self.canvas.create_line(50, cy, w-50, cy, fill="white", width=2)
    
    # رسم المؤشر
    vs_normalized = self.vsi / vs_max
    vs_normalized = max(-1, min(1, vs_normalized))
    
    x_pos = cx + (vs_normalized * 80)
    
    # رسم السهم
    self.canvas.create_polygon(
      x_pos-10, cy-20,
      x_pos+10, cy-20,
      x_pos, cy-40,
      fill="red"
    )
    
    # خط المؤشر
    self.canvas.create_line(x_pos, cy-15, x_pos, cy+15,
                fill="cyan", width=3)
    
    # تحديث العدادات
    self.vsi_display.config(text=f"{self.vsi:+.2f}")
    
    # تحويل إلى قدم/دقيقة
    vsi_ft_min = self.vsi * 196.85  # 1 م/ث = 196.85 قدم/دقيقة
    self.vsi_ft_display.config(text=f"{vsi_ft_min:+.0f}")
    
    # تحديث اللون
    if abs(vsi_ft_min) > 2000:
      color = "red"
    elif abs(vsi_ft_min) > 1000:
      color = "orange"
    elif vsi_ft_min > 0:
      color = "green"
    elif vsi_ft_min < 0:
      color = "yellow"
    else:
      color = "white"
    
    self.vsi_display.config(fg=color)
    self.vsi_ft_display.config(fg=color)
    
    # تحديث المعلومات
    self.info_label.config(
      text=f"الضغط: {self.pressure:.1f} hPa | الارتفاع: {self.altitude:.0f} m | dP/dt: {self.dp_dt:.1f} hPa/ثانية"
    )


# تشغيل النسخة الفيزيائية
if __name__ == "__main__":
  root = tk.Tk()
  app = PhysicalVSI(root)
  root.mainloop()