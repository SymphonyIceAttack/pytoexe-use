import cv2
import numpy as np
import pyautogui
import math
import win32gui
import win32con

WHITE_LOW  = np.array([0, 0, 210])
WHITE_HIGH = np.array([180, 35, 255])
BALL_LOW   = np.array([0, 70, 100])
BALL_HIGH  = np.array([180, 255, 255])

LINE_COLOR = (0, 255, 0)
LINE_WIDTH = 2
EXTEND_LEN = 2000
SHOW_LINE  = True

def set_topmost(hwnd):
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0, win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)

def find_ball(frame, low, high):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, low, high)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((4,4),np.uint8))
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    best = None
    for c in cnts:
        area = cv2.contourArea(c)
        if 40 < area < 850:
            peri = cv2.arcLength(c,True)
            if peri==0: continue
            cir = 4*math.pi*area/(peri**2)
            if cir>0.65:
                M = cv2.moments(c)
                x = int(M["m10"]/M["m00"])
                y = int(M["m01"]/M["m00"])
                best = (x,y)
    return best

def draw_aim_line(frame, white, target):
    if not SHOW_LINE or not white or not target:
        return frame
    dx = target[0]-white[0]
    dy = target[1]-white[1]
    dis = math.hypot(dx,dy)
    if dis<5: return frame
    ex = int(target[0] + dx/dis*EXTEND_LEN)
    ey = int(target[1] + dy/dis*EXTEND_LEN)
    cv2.line(frame, white, (ex,ey), LINE_COLOR, LINE_WIDTH)
    cv2.circle(frame, white, 7, (255,255,255), -1)
    cv2.circle(frame, target, 7, (0,0,255), -1)
    return frame

def main():
    global SHOW_LINE
    cv2.namedWindow("腾讯桌球瞄准器", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("腾讯桌球瞄准器", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    hwnd = win32gui.FindWindow(None,"腾讯桌球瞄准器")
    set_topmost(hwnd)
    while True:
        screen = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        white_pos = find_ball(frame, WHITE_LOW, WHITE_HIGH)
        ball_pos  = find_ball(frame, BALL_LOW, BALL_HIGH)
        frame = draw_aim_line(frame, white_pos, ball_pos)
        cv2.imshow("腾讯桌球瞄准器", frame)
        k = cv2.waitKey(1)&0xFF
        if k == 27: break
        if k == 112: SHOW_LINE = not SHOW_LINE
    cv2.destroyAllWindows()

if __name__=="__main__":
    main()