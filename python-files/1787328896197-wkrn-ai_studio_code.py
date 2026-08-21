# ==============================================================================
# PC SMART REMOTE - PYTHON TCP SERVER
# ==============================================================================
import socket
import pyautogui

# Disable PyAutoGUI delay for real-time mouse response
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.001

HOST = "0.0.0.0"  # Listen on all network interfaces
PORT = 5000       # Port number

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def handle_command(cmd_line):
    cmd_line = cmd_line.strip()
    if not cmd_line:
        return

    parts = cmd_line.split(" ")
    action = parts[0].upper()

    try:
        if action == "MOVE" and len(parts) >= 3:
            dx = float(parts[1])
            dy = float(parts[2])
            pyautogui.moveRel(dx, dy, _pause=False)

        elif action == "CLICK":
            pyautogui.click(button="left")

        elif action == "RIGHT_CLICK":
            pyautogui.click(button="right")

        elif action == "SCROLL" and len(parts) >= 2:
            dy = int(parts[1])
            # Multiply scroll step for smooth scrolling
            pyautogui.scroll(dy * 20)

        elif action == "KEY" and len(parts) >= 2:
            key = parts[1]
            if key == "SPACE":
                pyautogui.press("space")
            elif key == "BACKSPACE":
                pyautogui.press("backspace")
            elif key == "ENTER":
                pyautogui.press("enter")
            elif len(key) == 1:
                pyautogui.write(key)
            else:
                pyautogui.press(key.lower())

    except Exception as e:
        print(f"Error handling '{cmd_line}': {e}")

def start_server():
    server_ip = get_local_ip()
    print("=" * 60)
    print("   PC SMART REMOTE SERVER IS ACTIVE")
    print(f"   PC IP Address: {server_ip}")
    print(f"   Listening on Port: {PORT}")
    print("=" * 60)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    while True:
        print(f"\n[+] Waiting for connection on {server_ip}:{PORT}...")
        client_sock, addr = server_socket.accept()
        client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print(f"[✓] Connected to phone: {addr[0]}:{addr[1]}")

        buffer = ""
        try:
            while True:
                data = client_sock.recv(1024).decode("utf-8")
                if not data:
                    print("[-] Phone disconnected.")
                    break

                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    handle_command(line)

        except ConnectionResetError:
            print("[-] Connection reset.")
        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            client_sock.close()

if __name__ == "__main__":
    start_server()