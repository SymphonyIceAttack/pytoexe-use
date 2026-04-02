import pyautogui
import time
import cv2
import numpy as np

# ===================== ����������Ĭ�ϣ�=====================
pyautogui.FAILSAFE = True
SLEEP_FAST = 0.3
SLEEP_NOR = 0.8
SLEEP_LONG = 1.5

# ���ð�ťRGB
COLOR_SIGN = (255, 200, 0)       # ǩ���ư�ť
COLOR_MAIL = (20, 180, 255)      # �ʼ�����
COLOR_FIGHT = (255, 80, 80)      # ��ս�찴ť
COLOR_REWARD = (255, 220, 30)    # ��ȡ����
COLOR_NEXT = (70, 210, 255)      # ��һ��

# ��ͼʶ��
def get_screen():
    img = pyautogui.screenshot()
    return cv2.cvtColor(np.array(img), cv2.RGB2BGR)

# ����ɫ���
def find_and_click(img, target_rgb, region, tol=0.12):
    x1,y1,w,h = region
    crop = img[y1:y1+h, x1:x1+w]
    t = np.array(target_rgb, dtype=np.uint8)
    low = t * (1-tol)
    high = t * (1+tol)
    mask = cv2.inRange(crop, low, high)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        m = cv2.moments(max(cnts, key=cv2.contourArea))
        if m["m00"] == 0:
            return False
        cx = int(m["m10"]/m["m00"]) + x1
        cy = int(m["m01"]/m["m00"]) + y1
        pyautogui.moveTo(cx, cy, duration=SLEEP_FAST)
        pyautogui.click()
        time.sleep(SLEEP_NOR)
        return True
    return False

# 1.�Զ�ǩ��
def auto_sign(img):
    print("[����] ���ǩ��...")
    return find_and_click(img, COLOR_SIGN, (0,0,300,300))

# 2.�Զ����ʼ�����
def auto_mail(img):
    print("[����] ����ʼ�����...")
    if find_and_click(img, COLOR_MAIL, (800,0,160,200)):
        time.sleep(SLEEP_LONG)
        find_and_click(get_screen(), COLOR_REWARD, (0,0,960,540))
    return True

# 3.�Զ�ˢ����Ԯ�������һ���
def auto_rescue(img):
    print("[����] ����Ԯ�һ�...")
    # �ҿ�ս
    if find_and_click(img, COLOR_FIGHT, (350,250,260,200)):
        time.sleep(SLEEP_LONG*2)
        # ѭ���콱����һ��
        for _ in range(5):
            s = get_screen()
            find_and_click(s, COLOR_REWARD, (0,0,960,540))
            find_and_click(s, COLOR_NEXT, (0,0,960,540))
            time.sleep(SLEEP_NOR)
    return True

# ��ѭ����������
def main():
    print("===== ��ʬ���� ȫ�Զ����ų��� =====")
    print("1.ģ�����ֱ��ʣ�960��540")
    print("2.������Ϸǰ̨����Ҫ�����")
    print("3.�ر�ֱ�Ӳ�����ڼ���ֹͣ")
    time.sleep(3)

    while True:
        frame = get_screen()
        auto_sign(frame)
        auto_mail(frame)
        auto_rescue(frame)
        print("һ��������ɣ��ȴ���һ��...")
        time.sleep(8)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n�������ֶ�ֹͣ")