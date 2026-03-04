import pymem
import pymem.process
import win32gui
import win32con
import glfw
from imgui_bundle import imgui
from imgui_bundle.imgui import GlfwRenderer
import OpenGL.GL as gl
import numpy as np
import math
import time
import threading
import keyboard
import pyautogui
import ctypes
from ctypes import wintypes

class BloxStrikeCheat:
    def __init__(self):
        # ===== FRESH OFFSETS FROM GITHUB (4 days old) =====
        self.OFFSETS = {
            'local_player': 0x130,        # LocalPlayer pointer
            'entity_list': 0x70,          # Children (player list)
            'health': 0x194,               # Health value
            'x_pos': 0xE4,                  # Position X
            'y_pos': 0xE8,                  # Position Y  
            'z_pos': 0xEC,                  # Position Z
            'team': 0x290,                  # Team
            'view_matrix': 0x120,          # View matrix for ESP
            'name': 0xB0,                   # Player name
            'camera': 0x460,                # Camera
            'camera_pos': 0x11C,            # Camera position
            'workspace': 0x178,             # Workspace pointer
            'visual_engine': 0x7A36CD8,     # Visual engine pointer
            'data_model': 0x7E83170,        # Data model pointer
            'children_end': 0x8,            # End of children list
            'velocity': 0xF0,                # Velocity for prediction
        }
        
        # Connect to Roblox
        self.pm = None
        self.connected = False
        self.base_addr = 0
        self.roblox_hwnd = None
        self.connect_to_roblox()
        
        # ESP settings
        self.esp_enabled = True
        self.box_color = [0, 1, 0, 1]  # Green
        self.enemy_color = [1, 0, 0, 1]  # Red for enemies
        self.show_names = True
        self.show_health = True
        self.show_distance = True
        
        # Aimbot settings
        self.aimbot_enabled = True
        self.aim_on_rmb = True
        self.aim_fov = 90
        self.aim_smoothness = 5
        self.target_bone = "head"
        self.predict_movement = True
        
        # No Recoil settings
        self.no_recoil_enabled = True
        self.recoil_strength = 2
        
        # GUI settings
        self.show_menu = True
        self.menu_key = 'insert'
        
        # Player data
        self.local_pos = (0, 0, 0)
        self.local_health = 100
        self.players = []
        
        # Window dimensions
        self.screen_width = 1920
        self.screen_height = 1080
        
        # Setup overlay if connected
        if self.connected and self.roblox_hwnd:
            self.setup_overlay()
            
            # Start aimbot thread
            self.aimbot_running = True
            self.aimbot_thread = threading.Thread(target=self.aimbot_loop)
            self.aimbot_thread.daemon = True
            self.aimbot_thread.start()
            
            # Start no recoil thread
            self.recoil_thread = threading.Thread(target=self.no_recoil_loop)
            self.recoil_thread.daemon = True
            self.recoil_thread.start()
            
            # Hotkey for hiding
            keyboard.add_hotkey('f9', self.toggle_visibility)
        else:
            print("❌ Could not setup overlay - Roblox not found")
    
    def connect_to_roblox(self):
        """Connect to Roblox process"""
        try:
            # Find Roblox window
            self.roblox_hwnd = win32gui.FindWindow(None, "Roblox")
            if not self.roblox_hwnd:
                print("❌ Roblox not found - make sure it's running")
                return False
            
            # Get window dimensions
            rect = win32gui.GetWindowRect(self.roblox_hwnd)
            self.screen_width = rect[2] - rect[0]
            self.screen_height = rect[3] - rect[1]
            
            # Connect with pymem
            self.pm = pymem.Pymem("RobloxPlayerBeta.exe")
            
            # Get base address
            self.base_addr = pymem.process.module_from_name(
                self.pm.process_handle, 
                "RobloxPlayerBeta.exe"
            ).lpBaseOfDll
            
            self.connected = True
            print(f"✅ Connected to Roblox")
            print(f"✅ Base address: 0x{self.base_addr:X}")
            print(f"✅ Window: {self.screen_width}x{self.screen_height}")
            
            # Test offsets
            self.test_offsets()
            
            return True
        except pymem.exception.ProcessNotFound:
            print("❌ Roblox process not found - is Roblox running?")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def test_offsets(self):
        """Test if our offsets are working"""
        try:
            # Try to read local player
            local_addr = self.pm.read_longlong(self.base_addr + self.OFFSETS['local_player'])
            if local_addr:
                # Try to read health
                health = self.pm.read_int(local_addr + self.OFFSETS['health'])
                
                # Try to read position
                x = self.pm.read_float(local_addr + self.OFFSETS['x_pos'])
                y = self.pm.read_float(local_addr + self.OFFSETS['y_pos'])
                z = self.pm.read_float(local_addr + self.OFFSETS['z_pos'])
                
                print(f"✅ Offsets test passed!")
                print(f"  - Local player: 0x{local_addr:X}")
                print(f"  - Health: {health}")
                print(f"  - Position: ({x:.2f}, {y:.2f}, {z:.2f})")
                
                if abs(x) < 0.1 and abs(y) < 0.1 and abs(z) < 0.1:
                    print("⚠️  Position is zero - might be in menu or loading")
                else:
                    print("✅ Offsets look good!")
            else:
                print("❌ Couldn't find local player - offsets might be wrong")
        except Exception as e:
            print(f"❌ Offset test failed: {e}")
    
    def setup_overlay(self):
        """Create transparent overlay for ESP"""
        if not glfw.init():
            print("❌ Failed to initialize GLFW")
            return
        
        # Get Roblox window position
        rect = win32gui.GetWindowRect(self.roblox_hwnd)
        
        # Create overlay window
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.FLOATING, glfw.TRUE)
        glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        
        self.window = glfw.create_window(
            self.screen_width, self.screen_height,
            "BloxStrike External", None, None
        )
        
        if not self.window:
            print("❌ Failed to create overlay window")
            return
        
        glfw.set_window_pos(self.window, rect[0], rect[1])
        glfw.make_context_current(self.window)
        
        # Make overlay click-through
        self.overlay_hwnd = glfw.get_win32_window(self.window)
        ex_style = win32gui.GetWindowLong(self.overlay_hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.overlay_hwnd, win32con.GWL_EXSTYLE, 
                               ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        
        # Setup ImGui
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)
        
        # Set ImGui style
        self.setup_imgui_style()
        
        print("✅ Overlay created successfully")
        
        # Start render loop
        self.render_loop()
    
    def setup_imgui_style(self):
        """Make GUI look like Undetek"""
        style = imgui.get_style()
        style.window_rounding = 5.0
        style.frame_rounding = 3.0
        style.grab_rounding = 3.0
        
        # Dark purple theme
        imgui.style_colors_dark()
        
        # Custom colors
        style.colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.11, 0.11, 0.17, 0.94)
        style.colors[imgui.COLOR_TITLE_BACKGROUND] = (0.15, 0.15, 0.25, 1.0)
        style.colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = (0.25, 0.25, 0.35, 1.0)
        style.colors[imgui.COLOR_FRAME_BACKGROUND] = (0.18, 0.18, 0.27, 1.0)
        style.colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.25, 0.25, 0.35, 1.0)
        style.colors[imgui.COLOR_CHECK_MARK] = (0.45, 0.35, 0.85, 1.0)
        style.colors[imgui.COLOR_SLIDER_GRAB] = (0.45, 0.35, 0.85, 1.0)
        style.colors[imgui.COLOR_BUTTON] = (0.25, 0.25, 0.35, 1.0)
        style.colors[imgui.COLOR_BUTTON_HOVERED] = (0.35, 0.35, 0.45, 1.0)
    
    def read_player_data(self):
        """Read all player data from memory using offsets"""
        if not self.connected or not self.pm:
            return []
        
        players = []
        try:
            # Read local player
            local_addr = self.pm.read_longlong(self.base_addr + self.OFFSETS['local_player'])
            if not local_addr:
                return []
            
            # Get local player position and health
            self.local_pos = (
                self.pm.read_float(local_addr + self.OFFSETS['x_pos']),
                self.pm.read_float(local_addr + self.OFFSETS['y_pos']),
                self.pm.read_float(local_addr + self.OFFSETS['z_pos'])
            )
            self.local_health = self.pm.read_int(local_addr + self.OFFSETS['health'])
            
            # Get workspace
            workspace = self.pm.read_longlong(self.base_addr + self.OFFSETS['workspace'])
            if not workspace:
                return []
            
            # Get children list
            children = self.pm.read_longlong(workspace + self.OFFSETS['entity_list'])
            if not children:
                return []
            
            # Iterate through children
            current = children
            for i in range(100):  # Max players
                try:
                    player_addr = self.pm.read_longlong(current)
                    if player_addr and player_addr != local_addr:
                        # Check if it's a player (has health)
                        health = self.pm.read_int(player_addr + self.OFFSETS['health'])
                        if 0 < health <= 100:
                            # Get position
                            x = self.pm.read_float(player_addr + self.OFFSETS['x_pos'])
                            y = self.pm.read_float(player_addr + self.OFFSETS['y_pos'])
                            z = self.pm.read_float(player_addr + self.OFFSETS['z_pos'])
                            
                            # Get team
                            team = 0
                            try:
                                team = self.pm.read_int(player_addr + self.OFFSETS['team'])
                            except:
                                pass
                            
                            # Get name
                            name = "Player"
                            try:
                                name_ptr = self.pm.read_longlong(player_addr + self.OFFSETS['name'])
                                if name_ptr:
                                    name = self.pm.read_string(name_ptr)
                            except:
                                pass
                            
                            # Get velocity for prediction
                            vel_x = vel_y = vel_z = 0
                            if self.predict_movement:
                                try:
                                    vel_x = self.pm.read_float(player_addr + self.OFFSETS['velocity'])
                                    vel_y = self.pm.read_float(player_addr + self.OFFSETS['velocity'] + 4)
                                    vel_z = self.pm.read_float(player_addr + self.OFFSETS['velocity'] + 8)
                                except:
                                    pass
                            
                            players.append({
                                'address': player_addr,
                                'health': health,
                                'x': x,
                                'y': y,
                                'z': z,
                                'team': team,
                                'name': name,
                                'vel_x': vel_x,
                                'vel_y': vel_y,
                                'vel_z': vel_z
                            })
                    
                    # Move to next in linked list
                    current = self.pm.read_longlong(current + 0x8)
                    if not current:
                        break
                        
                except:
                    break
                    
        except Exception as e:
            pass
        
        return players
    
    def world_to_screen(self, x, y, z):
        """Convert 3D world position to 2D screen position"""
        try:
            # Get view matrix
            view_matrix = self.pm.read_longlong(self.base_addr + self.OFFSETS['view_matrix'])
            if not view_matrix:
                return None
            
            # Read matrix (4x4)
            matrix = []
            for i in range(16):
                matrix.append(self.pm.read_float(view_matrix + (i * 4)))
            
            # Transform point
            w = (matrix[3] * x) + (matrix[7] * y) + (matrix[11] * z) + matrix[15]
            if w < 0.01:
                return None
            
            inv_w = 1.0 / w
            screen_x = (matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12]) * inv_w
            screen_y = (matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13]) * inv_w
            
            # Convert to screen coordinates
            screen_x = (self.screen_width / 2) + (screen_x * self.screen_width / 2)
            screen_y = (self.screen_height / 2) - (screen_y * self.screen_height / 2)
            
            if 0 <= screen_x <= self.screen_width and 0 <= screen_y <= self.screen_height:
                return (screen_x, screen_y)
            
        except:
            pass
        return None
    
    def draw_esp(self):
        """Draw ESP boxes for all players"""
        if not self.esp_enabled or not hasattr(imgui, 'get_window_draw_list'):
            return
        
        draw_list = imgui.get_window_draw_list()
        
        for player in self.players:
            # World to screen conversion
            screen_pos = self.world_to_screen(player['x'], player['y'], player['z'])
            
            if screen_pos:
                x, y = screen_pos
                
                # Calculate distance
                dist = math.sqrt(
                    (player['x'] - self.local_pos[0])**2 +
                    (player['y'] - self.local_pos[1])**2 +
                    (player['z'] - self.local_pos[2])**2
                )
                
                # Box size based on distance
                box_height = 6000 / max(dist, 1)
                box_width = box_height * 0.6
                
                # Choose color (red for enemies, green for teammates)
                color = self.enemy_color if player['team'] != 0 else self.box_color
                
                # Draw box
                draw_list.add_rect(
                    x - box_width/2, y - box_height,
                    x + box_width/2, y,
                    imgui.get_color_u32_rgba(color[0], color[1], color[2], color[3]),
                    thickness=2.0
                )
                
                # Draw health bar
                if self.show_health:
                    health_height = (player['health'] / 100) * box_height
                    draw_list.add_rect_filled(
                        x - box_width/2 - 5, y - health_height,
                        x - box_width/2 - 2, y,
                        imgui.get_color_u32_rgba(0, 1, 0, 1)
                    )
                
                # Draw name
                if self.show_names:
                    draw_list.add_text(
                        x - box_width/2, y - box_height - 15,
                        imgui.get_color_u32_rgba(1, 1, 1, 1),
                        f"{player['name']}"
                    )
                
                # Draw distance
                if self.show_distance:
                    draw_list.add_text(
                        x - box_width/2, y + 5,
                        imgui.get_color_u32_rgba(1, 1, 1, 1),
                        f"{int(dist)}m"
                    )
    
    def aimbot_loop(self):
        """Main aimbot logic"""
        while self.aimbot_running:
            if self.aimbot_enabled and self.connected and self.players:
                # Check if RMB is pressed
                if self.aim_on_rmb and not pyautogui.mouse.pressed()[1]:
                    time.sleep(0.01)
                    continue
                
                # Find best target
                target = self.get_best_target()
                
                if target:
                    # Predict movement if enabled
                    target_x, target_y, target_z = target['x'], target['y'], target['z']
                    
                    if self.predict_movement:
                        # Simple prediction (lead target)
                        target_x += target['vel_x'] * 0.1
                        target_y += target['vel_y'] * 0.1
                        target_z += target['vel_z'] * 0.1
                    
                    screen_pos = self.world_to_screen(target_x, target_y, target_z)
                    
                    if screen_pos:
                        target_x, target_y = screen_pos
                        center_x, center_y = self.screen_width/2, self.screen_height/2
                        
                        # Calculate distance from crosshair
                        dist = math.sqrt(
                            (target_x - center_x)**2 + 
                            (target_y - center_y)**2
                        )
                        
                        # Check FOV
                        if dist < self.aim_fov * 5:
                            # Smooth aim
                            move_x = (target_x - center_x) / self.aim_smoothness
                            move_y = (target_y - center_y) / self.aim_smoothness
                            
                            pyautogui.moveRel(move_x, move_y)
            
            time.sleep(0.001)
    
    def no_recoil_loop(self):
        """No recoil thread"""
        bullet_count = 0
        while self.aimbot_running:
            if self.no_recoil_enabled and self.connected:
                if pyautogui.mouse.pressed()[0]:  # Left click held
                    # Pull mouse down based on bullet count
                    pull = self.recoil_strength * (1 + bullet_count * 0.1)
                    pyautogui.moveRel(0, pull, duration=0.005)
                    bullet_count += 1
                    time.sleep(0.05)
                else:
                    bullet_count = 0
            time.sleep(0.01)
    
    def get_best_target(self):
        """Find best target for aimbot"""
        if not self.players:
            return None
        
        best_target = None
        best_dist = float('inf')
        best_health = 0
        center_x, center_y = self.screen_width/2, self.screen_height/2
        
        for player in self.players:
            # Skip teammates if team check is enabled
            if player['team'] != 0:  # If not enemy
                continue
                
            screen_pos = self.world_to_screen(player['x'], player['y'], player['z'])
            if screen_pos:
                dist = math.sqrt(
                    (screen_pos[0] - center_x)**2 + 
                    (screen_pos[1] - center_y)**2
                )
                
                # Prioritize closer enemies with low health
                score = dist - (100 - player['health']) * 10
                
                if score < best_dist:
                    best_dist = score
                    best_target = player
        
        return best_target if best_dist < self.aim_fov * 10 else None
    
    def render_menu(self):
        """Render the Undetek-style menu"""
        if not self.show_menu:
            return
        
        imgui.set_next_window_size(500, 400, imgui.ONCE)
        imgui.begin("BLOXSTRIKE EXTERNAL", True)
        
        # Header
        imgui.text_colored("BLOXSTRIKE EXTERNAL v2.0", 0.45, 0.35, 0.85, 1)
        imgui.separator()
        
        # Status bar
        if self.connected:
            imgui.text_colored(f"Connected | Players: {len(self.players)} | Health: {self.local_health}", 0, 1, 0, 1)
        else:
            imgui.text_colored("Disconnected - Start Roblox", 1, 0, 0, 1)
        imgui.separator()
        
        # Tabs
        if imgui.begin_tab_bar("MainTabs"):
            # AIMBOT TAB
            if imgui.begin_tab_item("AIMBOT")[0]:
                imgui.spacing()
                _, self.aimbot_enabled = imgui.checkbox("Enable Aimbot", self.aimbot_enabled)
                imgui.same_line()
                _, self.aim_on_rmb = imgui.checkbox("On RMB Only", self.aim_on_rmb)
                
                imgui.spacing()
                imgui.text("Aimbot Settings")
                imgui.separator()
                
                _, self.aim_fov = imgui.slider_int("FOV", self.aim_fov, 1, 180)
                _, self.aim_smoothness = imgui.slider_int("Smoothness", self.aim_smoothness, 1, 20)
                _, self.predict_movement = imgui.checkbox("Predict Movement", self.predict_movement)
                
                # Bone selection
                imgui.text("Target Bone:")
                if imgui.radio_button("Head", self.target_bone == "head"):
                    self.target_bone = "head"
                imgui.same_line()
                if imgui.radio_button("Chest", self.target_bone == "chest"):
                    self.target_bone = "chest"
                imgui.same_line()
                if imgui.radio_button("Body", self.target_bone == "body"):
                    self.target_bone = "body"
                
                imgui.end_tab_item()
            
            # ESP TAB
            if imgui.begin_tab_item("ESP")[0]:
                imgui.spacing()
                _, self.esp_enabled = imgui.checkbox("Enable ESP", self.esp_enabled)
                
                imgui.spacing()
                imgui.text("ESP Elements")
                imgui.separator()
                _, self.show_names = imgui.checkbox("Show Names", self.show_names)
                _, self.show_health = imgui.checkbox("Show Health Bars", self.show_health)
                _, self.show_distance = imgui.checkbox("Show Distance", self.show_distance)
                
                imgui.spacing()
                imgui.text("ESP Colors")
                imgui.separator()
                _, self.box_color = imgui.color_edit4("Box Color", *self.box_color)
                _, self.enemy_color = imgui.color_edit4("Enemy Color", *self.enemy_color)
                
                imgui.end_tab_item()
            
            # MISC TAB
            if imgui.begin_tab_item("MISC")[0]:
                imgui.spacing()
                _, self.no_recoil_enabled = imgui.checkbox("Enable No Recoil", self.no_recoil_enabled)
                _, self.recoil_strength = imgui.slider_int("Recoil Strength", self.recoil_strength, 1, 10)
                
                imgui.spacing()
                imgui.text("Hotkeys")
                imgui.separator()
                imgui.text("INSERT - Toggle Menu")
                imgui.text("F9 - Hide/Show Overlay")
                imgui.text("RMB - Activate Aimbot")
                
                imgui.end_tab_item()
            
            imgui.end_tab_bar()
        
        # Footer
        imgui.separator()
        imgui.text_colored(f"Offsets Updated: 4 days ago | Build 2.0", 0.5, 0.5, 0.5, 1)
        
        imgui.end()
    
    def render_loop(self):
        """Main render loop"""
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.impl.process_inputs()
            
            # Toggle menu with INSERT
            if keyboard.is_pressed('insert'):
                self.show_menu = not self.show_menu
                time.sleep(0.2)
            
            # Update player data
            self.players = self.read_player_data()
            
            # Start ImGui frame
            imgui.new_frame()
            
            # Render menu
            self.render_menu()
            
            # Render ESP (only if window not hidden)
            if self.esp_enabled and glfw.get_window_attrib(self.window, glfw.VISIBLE):
                self.draw_esp()
            
            # Render ImGui
            imgui.render()
            
            # Clear and draw
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)
        
        self.cleanup()
    
    def toggle_visibility(self):
        """Hide/show overlay with F9"""
        if hasattr(self, 'window') and self.window:
            if glfw.get_window_attrib(self.window, glfw.VISIBLE):
                glfw.hide_window(self.window)
                print("🔴 Overlay hidden")
            else:
                glfw.show_window(self.window)
                print("🟢 Overlay shown")
    
    def cleanup(self):
        """Clean up resources"""
        self.aimbot_running = False
        if hasattr(self, 'impl'):
            self.impl.shutdown()
        if hasattr(self, 'window'):
            glfw.terminate()
        print("👋 Cheat stopped")

# Run the cheat
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════╗
    ║   BLOXSTRIKE EXTERNAL v2.0       ║
    ║      Undetek Edition              ║
    ╚══════════════════════════════════╝
    """)
    
    print("[*] Starting cheat...")
    print("[*] Make sure Roblox is running!")
    print("[*] Press INSERT for menu")
    print("[*] Press F9 to hide/show overlay")
    print("[*] Hold RMB for aimbot")
    print("[*] Hold left click for no recoil")
    print("\n" + "="*50)
    
    try:
        cheat = BloxStrikeCheat()
    except KeyboardInterrupt:
        print("\n👋 Cheat stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")