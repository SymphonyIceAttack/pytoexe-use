import cv2
import numpy as np
import pyautogui
import time
import keyboard
from mss import mss
import sys
import os

# ========== إعدادات ==========
RED_THRESHOLD_LOW = 80
MIN_AREA = 100
HEAD_OFFSET_Y = -30
SHOOT_DURATION = 1.5
FPS_TARGET = 5

print("=" * 60)
print("          🎯 Black Shot Auto Aim - مشروع التخرج")
print("=" * 60)
print()
print("📌 المفاتيح:")
print("   [F1]  تشغيل/إيقاف النظام")
print("   [F2]  إظهار/إخفاء نافذة الكشف")
print("   [ESC] إغلاق البرنامج")
print()
print("=" * 60)

try:
    sct = mss()
    monitor = sct.monitors[1]
except Exception as e:
    print(f"❌ خطأ في تصوير الشاشة: {e}")
    input("اضغط Enter للخروج...")
    sys.exit()

running = False
debug_mode = True
is_shooting = False
targets_found = 0

def shoot():
    """ضغط زر الماوس الأيسر لمدة محددة"""
    global is_shooting
    if is_shooting:
        return
    is_shooting = True
    try:
        pyautogui.mouseDown()
        time.sleep(SHOOT_DURATION)
        pyautogui.mouseUp()
    except Exception as e:
        print(f"⚠️ خطأ في الضغط: {e}")
    is_shooting = False

def find_red_targets(img):
    """
    البحث عن الأهداف الحمراء في الصورة
    """
    try:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    except Exception as e:
        return [], None
    
    # مدى اللون الأحمر (مضبوط للعبة Black Shot)
    lower_red1 = np.array([0, 80, RED_THRESHOLD_LOW])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 80, RED_THRESHOLD_LOW])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # تنظيف القناع
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # البحث عن الملامح
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    targets = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_AREA:
            continue
        
        x, y, w, h = cv2.boundingRect(contour)
        center_x = x + w // 2
        center_y = y + h // 2
        
        targets.append((center_x, center_y + HEAD_OFFSET_Y, w, h, area))
    
    return targets, mask

def process_frame():
    """معالجة الإطار الواحد"""
    global running, debug_mode, targets_found
    
    try:
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    except Exception as e:
        return
    
    targets, mask = find_red_targets(img_rgb)
    
    if targets:
        targets_found += 1
        # اختيار أقرب هدف إلى مركز الشاشة
        screen_center_x = monitor["width"] // 2
        screen_center_y = monitor["height"] // 2
        
        targets.sort(key=lambda t: abs(t[0] - screen_center_x) + abs(t[1] - screen_center_y))
        head_x, head_y, w, h, area = targets[0]
        
        # تحريك الماوس
        try:
            pyautogui.moveTo(head_x, head_y)
            print(f"🎯 تصويب على الرأس عند ({head_x}, {head_y}) - المساحة: {area}")
        except Exception as e:
            print(f"⚠️ خطأ في تحريك الماوس: {e}")
        
        # إطلاق نار
        shoot()
        
        if debug_mode:
            try:
                cv2.circle(img_rgb, (head_x, head_y), 10, (0, 255, 0), 2)
                cv2.putText(img_rgb, "HEAD", (head_x - 25, head_y - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(img_rgb, f"TARGETS: {targets_found}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            except:
                pass
    
    if debug_mode:
        try:
            img_resized = cv2.resize(img_rgb, (640, 360))
            cv2.imshow('Black Shot Auto Aim', img_resized)
            
            mask_resized = cv2.resize(mask, (640, 360))
            cv2.imshow('Red Mask', mask_resized)
        except:
            pass

def main_loop():
    """الحلقة الرئيسية"""
    global running, debug_mode
    
    frame_time = 1.0 / FPS_TARGET
    
    while True:
        start_time = time.time()
        
        # تشغيل/إيقاف
        if keyboard.is_pressed('f1'):
            running = not running
            print(f"{'▶️' if running else '⏸️'} النظام {'مفعل' if running else 'موقف'}")
            time.sleep(0.3)
        
        # إظهار/إخفاء الديباج
        if keyboard.is_pressed('f2'):
            debug_mode = not debug_mode
            print(f"{'👁️' if debug_mode else '🚫'} نافذة الديباج {'مفعلة' if debug_mode else 'مطفأة'}")
            if not debug_mode:
                try:
                    cv2.destroyAllWindows()
                except:
                    pass
            time.sleep(0.3)
        
        # خروج
        if keyboard.is_pressed('esc'):
            print("🛑 إيقاف البرنامج...")
            break
        
        # معالجة الإطار
        if running:
            process_frame()
        
        # التحكم في السرعة
        elapsed = time.time() - start_time
        sleep_time = max(0, frame_time - elapsed)
        time.sleep(sleep_time)
    
    try:
        cv2.destroyAllWindows()
    except:
        pass
    print(f"✅ تم إيقاف البرنامج. تم اكتشاف {targets_found} هدف.")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n🛑 تم الإيقاف بواسطة المستخدم")
        try:
            cv2.destroyAllWindows()
        except:
            pass
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        input("اضغط Enter للخروج...")