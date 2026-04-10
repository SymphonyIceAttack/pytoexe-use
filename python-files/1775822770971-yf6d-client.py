# client.py - Custom Image Streaming Viewer with Input Interception
import time
import socket
from PIL import Image, ImageTk # Pillow library for image handling
import tkinter as tk     # Tkinter for GUI windowing
import threading        # For managing the network listener thread
import logging         # Logging module

HOST_IP = "88.192.127.87"  # <<< CRITICAL: Change this to your Host's public IP!
PORT = 4444               # REQUIRED PORT
LOG_FILE = "client_log.txt"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler(LOG_FILE), 
    logging.StreamHandler()         
])


class ImageClient:
    def __init__(self):
        # --- Socket Setup ---
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        
        # --- GUI Setup (Tkinter) ---
        self.root = tk.Tk()
        self.root.title("Stealth Remote Desktop")
        
        # Canvas will hold the image display
        self.canvas = tk.Canvas(self.root, width=1280, height=720, bg='black') # Set initial size
        self.canvas.pack()

        # Initialize with a placeholder/blank frame
        self.current_image = Image.new('RGB', (1280, 720), color = 'gray')
        self.tk_img = ImageTk.PhotoImage(self.current_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        # --- Input Control Setup (The "Disable" mechanism) ---
        # Bind keyboard events to the root window
        self.root.bind('<Key>', self._handle_keyboard_input)
        # Bind mouse clicks/movement events
        self.root.bind('<Button-1>', lambda e: self._handle_mouse_event("Click")) # Left Click
        self.root.bind('<B1-Motion>', lambda e: self._handle_mouse_event("Move")) # Dragging
        # We don't bind movement globally, but rather handle it when the window is focused.

    def _handle_keyboard_input(self, event):
        """Intercepts keyboard events and ignores them (prevents Host from seeing input)."""
        key = event.keysym
        if key == "Escape":
            logging.info("[CLIENT INPUT] ESC Key pressed - Closing client.")
            self.running = False
            self.root.destroy()
        else:
            # Log the ignored action (the evidence that input was received but blocked)
            logging.debug(f"[INPUT IGNORED] Keyboard Event received: {key}")

    def _handle_mouse_event(self, event_type):
        """Intercepts mouse events and ignores them."""
        x, y = event.x, event.y
        if event_type == "Click":
            logging.debug(f"[INPUT IGNORED] Mouse Click received at ({x}, {y})")
        elif event_type == "Move":
             # Log movement only if the mouse is moving significantly (to reduce log spam)
             logging.debug(f"[INPUT IGNORED] Mouse Move detected.")


    def receive_stream(self):
        """The main thread loop to continuously listen for and decode frames."""
        while self.running:
            try:
                # 1. Receive the 4-byte size header first (blocking call)
                header = self.socket.recv(4)
                if not header:
                    logging.warning("Connection closed by Host.")
                    break

                data_size = int.from_bytes(header, byteorder='big')
                
                # 2. Receive the actual image data (blocking call)
                image_data = b''
                while len(image_data) < data_size:
                    chunk = self.socket.recv(min(4096, data_size - len(image_data)))
                    if not chunk:
                        raise ConnectionResetError("Connection broken during image transfer.")
                    image_data += chunk

                # 3. Decode and Display
                new_img = Image.frombytes('RGB', (1280, 720), image_data)
                self.current_image = new_img
                self.tk_img = ImageTk.PhotoImage(self.current_image)
                self.canvas.itemconfig(1, image=self.tk_img) # Update the existing canvas item

            except ConnectionResetError:
                logging.error("[STREAM ERROR] Host disconnected abruptly.")
                break
            except Exception as e:
                if self.running:
                    logging.error(f"[SOCKET ERROR] An error occurred during streaming: {e}")
                break


    def run(self):
        """Connects, starts the streamer thread, and launches the GUI."""
        try:
            # Connect to the Host
            self.socket.connect((HOST_IP, PORT))
            logging.info("Successfully connected to Remote Host!")

            # Start the streaming receiver in a separate thread
            stream_thread = threading.Thread(target=self.receive_stream)
            stream_thread.daemon = True # Essential: ensures this thread dies when GUI closes
            stream_thread.start()
            
            # Run the Tkinter main loop (this keeps the window open and responsive)
            self.root.mainloop()

        except ConnectionRefusedError:
            logging.error("Connection Refused! Is host.py running and listening on Port 4444?")
        except Exception as e:
            logging.critical(f"CRITICAL FAILURE in Client initialization: {e}")
        finally:
            self.running = False
            self.socket.close()
            logging.info("[SHUTDOWN] Client socket closed.")


if __name__ == "__main__":
    client = ImageClient()
    client.run()

