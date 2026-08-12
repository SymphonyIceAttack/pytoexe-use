import pymem
import pymem.process
import win32gui
import win32con
import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw
import OpenGL.GL as gl
 
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
 
dwLocalPlayer = 0xDEF97C
dwEntityList = 0x4E051DC
dwViewMatrix = 0x4DF6024
m_iHealth = 0x100
m_iTeamNum = 0xF4
m_bDormant = 0xED
m_vecOrigin = 0x138
m_dwBoneMatrix = 0x26A8
 
print("CSGO LEGACY ESP CODE BY AGIGATORX ENJOY :)")
 
pm = None
client = None
 
def connect():
    global pm, client
    try:
        pm = pymem.Pymem("csgo.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        return True
    except:
        return False
 
def read_int(addr):
    try:
        return pm.read_int(addr)
    except:
        return 0
 
def read_float(addr):
    try:
        return pm.read_float(addr)
    except:
        return 0.0
 
def w2s(pos, width, height):
    view_matrix = []
    for i in range(16):
        view_matrix.append(read_float(client + dwViewMatrix + i * 4))
    
    w = (view_matrix[12] * pos[0]) + (view_matrix[13] * pos[1]) + (view_matrix[14] * pos[2]) + view_matrix[15]
    if w < 0.001:
        return None
    
    x = (view_matrix[0] * pos[0]) + (view_matrix[1] * pos[1]) + (view_matrix[2] * pos[2]) + view_matrix[3]
    y = (view_matrix[4] * pos[0]) + (view_matrix[5] * pos[1]) + (view_matrix[6] * pos[2]) + view_matrix[7]
    
    return [(width / 2) * (1 + x / w), (height / 2) * (1 - y / w)]
 
def main():
    if not connect():
        input("Press Enter to exit...")
        return
    
    if not glfw.init():
        return
    
    glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "AGIGATORX", None, None)
    if not window:
        glfw.terminate()
        return
    
    hwnd = glfw.get_win32_window(window)
    
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
    
    ex_style = win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, -2, -2, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
    
    glfw.make_context_current(window)
    imgui.create_context()
    impl = GlfwRenderer(window)
    
    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        
        imgui.new_frame()
        
        imgui.set_next_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        imgui.set_next_window_position(0, 0)
        
        imgui.begin("overlay", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | 
                    imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BACKGROUND)
        
        draw = imgui.get_window_draw_list()
        
        local = read_int(client + dwLocalPlayer)
        if local:
            local_team = read_int(local + m_iTeamNum)
            
            for i in range(1, 64):
                entity = read_int(client + dwEntityList + (i * 0x10))
                if not entity or entity < 0x10000:
                    continue
                
                health = read_int(entity + m_iHealth)
                team = read_int(entity + m_iTeamNum)
                dormant = read_int(entity + m_bDormant)
                
                if health <= 0 or dormant or team == local_team:
                    continue
                
                bone = read_int(entity + m_dwBoneMatrix)
                if bone < 0x10000:
                    continue
                
                head = [read_float(bone + 0x30 * 8 + 0x0C), read_float(bone + 0x30 * 8 + 0x1C), read_float(bone + 0x30 * 8 + 0x2C)]
                foot = [read_float(entity + m_vecOrigin), read_float(entity + m_vecOrigin + 4), read_float(entity + m_vecOrigin + 8)]
                
                head_s = w2s(head, WINDOW_WIDTH, WINDOW_HEIGHT)
                foot_s = w2s(foot, WINDOW_WIDTH, WINDOW_HEIGHT)
                
                if not head_s or not foot_s:
                    continue
                
                height = foot_s[1] - head_s[1]
                width = height * 0.3
                x = head_s[0] - width / 2
                y = head_s[1]
                
                color = imgui.get_color_u32_rgba(1, 0, 0, 1)
                
                draw.add_line(x, y, x + width, y, color, 2.0)
                draw.add_line(x + width, y, x + width, y + height, color, 2.0)
                draw.add_line(x + width, y + height, x, y + height, color, 2.0)
                draw.add_line(x, y + height, x, y, color, 2.0)
                
                hp_height = (health / 100.0) * height
                draw.add_rect_filled(x - 6, y + height - hp_height, x - 2, y + height, imgui.get_color_u32_rgba(0, 1, 0, 1))
                draw.add_rect(x - 6, y, x - 2, y + height, imgui.get_color_u32_rgba(0, 0, 0, 0.5), 1.0)
        
        imgui.end()
        imgui.end_frame()
        
        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        
        glfw.swap_buffers(window)
        
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            break
    
    impl.shutdown()
    glfw.terminate()
 
if __name__ == '__main__':
    main()