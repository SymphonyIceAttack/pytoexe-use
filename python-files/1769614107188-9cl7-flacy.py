import win32gui
import win32con
import win32api

x, y = 50, 50
dx, dy = 5, 5
ICON_SIZE = 32
timer_id = 1

def wndproc(hwnd, msg, wparam, lparam):
    global x, y, dx, dy

    if msg == win32con.WM_CREATE:
        win32gui.SetTimer(hwnd, timer_id, 30, 0)
        return 0

    elif msg == win32con.WM_TIMER:
        rect = win32gui.GetClientRect(hwnd)
        width = rect[2]
        height = rect[3]

        x += dx
        y += dy

        if x <= 0 or x + ICON_SIZE >= width:
            dx = -dx
        if y <= 0 or y + ICON_SIZE >= height:
            dy = -dy

        win32gui.InvalidateRect(hwnd, None, True)
        return 0

    elif msg == win32con.WM_PAINT:
        hdc, ps = win32gui.BeginPaint(hwnd)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_WINDOW)
        win32gui.FillRect(hdc, ps[2], brush)

        hicon = win32gui.LoadIcon(0, win32con.IDI_QUESTION)
        win32gui.DrawIcon(hdc, x, y, hicon)

        win32gui.EndPaint(hwnd, ps)
        return 0

    elif msg == win32con.WM_DESTROY:
        win32gui.KillTimer(hwnd, timer_id)
        win32gui.PostQuitMessage(0)
        return 0

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# Register window class
wc = win32gui.WNDCLASS()
wc.lpfnWndProc = wndproc
wc.lpszClassName = "PythonBouncyIcon"
wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)

class_atom = win32gui.RegisterClass(wc)

# Create window
hwnd = win32gui.CreateWindow(
    class_atom,
    "Bouncy Question Mark (Python GDI)",
    win32con.WS_OVERLAPPEDWINDOW,
    win32con.CW_USEDEFAULT,
    win32con.CW_USEDEFAULT,
    500,
    400,
    0,
    0,
    0,
    None
)

win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
win32gui.UpdateWindow(hwnd)

# Message loop
while True:
    msg = win32gui.GetMessage(None, 0, 0)
    if not msg:
        break
    win32gui.TranslateMessage(msg)
    win32gui.DispatchMessage(msg)
