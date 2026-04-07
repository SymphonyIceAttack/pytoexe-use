import http.server
import socketserver
import struct
import subprocess
import threading
import time
import os

def get_wav_header():
    return struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 0xFFFFFFFF, b'WAVE', b'fmt ', 16, 1, 2, 
        44100, 176400, 4, 16, b'data', 0xFFFFFFFF)

class VacuumHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'audio/wav')
        self.end_headers()
        self.wfile.write(get_wav_header())
        try:
            while True:
                self.wfile.write(b'\x00' * 8192)
                time.sleep(0.01)
        except: pass

def run_server():
    with socketserver.TCPServer(("127.0.0.1", 8888), VacuumHandler) as httpd:
        httpd.handle_request()

def launch_player():
    portal_url = "http://127.0.0.1:8888/emptiness 1.wav"

    os.system(f"start wmplayer {portal_url}")
    
    # vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
    
    # if os.path.exists(vlc_path):
    #     subprocess.Popen([vlc_path, portal_url, "--loop"])
    # else:
    #     # This usually triggers Windows Media Player or Groove Music
        

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    launch_player()
    
    while True:
        time.sleep(1)