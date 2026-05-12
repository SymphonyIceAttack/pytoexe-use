import http.server
import socketserver
import webbrowser
import threading
import os
import sys

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
PORT = 0
HOST = "localhost"
MAP_FOLDER = "mapdata"
START_PAGE = "buffering_deckgl_map.html"


# ---------------------------------------------------------
# GET BASE PATH (critical fix)
# ---------------------------------------------------------
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as EXE
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------
# CUSTOM HANDLER (serve from mapdata WITHOUT chdir)
# ---------------------------------------------------------
class MapDataHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        pass  # silence logs (optional)


# ---------------------------------------------------------
# OPEN BROWSER
# ---------------------------------------------------------
def open_browser(port):
    url = f"http://{HOST}:{port}/{START_PAGE}"
    webbrowser.open(url)
    print(f"🚀 Opening browser at: {url}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":

    base_path = get_base_path()
    map_path = os.path.join(base_path, MAP_FOLDER)

    print(f"Base path: {base_path}")
    print(f"Map path: {map_path}")

    if not os.path.exists(map_path):
        print(f"❌ ERROR: '{MAP_FOLDER}' folder not found.")
        input("Press Enter to exit...")
        sys.exit(1)

    # ✅ DO NOT CHDIR — serve from directory directly
    Handler = lambda *args, **kwargs: MapDataHandler(*args, directory=map_path, **kwargs)

    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:

            actual_port = httpd.server_address[1]

            print(f"✅ Server running at http://{HOST}:{actual_port}")
            print(f"📂 Serving: {map_path}")
            print("Press Ctrl+C to stop.\n")

            threading.Timer(1.0, open_browser, args=(actual_port,)).start()

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
