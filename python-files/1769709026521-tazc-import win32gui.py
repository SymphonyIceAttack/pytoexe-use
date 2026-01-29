import win32gui
import win32con

def draw_rectangle():
    hwnd = win32gui.GetDesktopWindow()
    hdc = win32gui.GetWindowDC(hwnd)
    pen = win32gui.CreatePen(win32con.PS_SOLID, 5, 0x0000FF)  # Blue pen
    old_pen = win32gui.SelectObject(hdc, pen)
    win32gui.Rectangle(hdc, 100, 100, 300, 300)
    win32gui.SelectObject(hdc, old_pen)
    win32gui.DeleteObject(pen)
    win32gui.ReleaseDC(hwnd, hdc)

draw_rectangle()