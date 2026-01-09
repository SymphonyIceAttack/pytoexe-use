import socket
import tkinter as tk
from urllib.parse import urlparse
import re

def fetch_http(url):
    parsed = urlparse(url)

    if parsed.scheme != "http":
        return "❌ ERROR! Only HTTP"

    host = parsed.hostname
    path = parsed.path if parsed.path else "/"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, 80))

        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        s.send(request.encode())

        response = b""
        while True:
            data = s.recv(4096)
            if not data:
                break
            response += data

        s.close()

        body = response.split(b"\r\n\r\n", 1)[1]
        return body.decode(errors="ignore")

    except Exception as e:
        return f"ERROR: {e}"

def render_text(html):
    html = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.S)
    html = re.sub(r"<style.*?>.*?</style>", "", html, flags=re.S)

    html = re.sub(r"</p>|<br>|<br/>", "\n", html)
    html = re.sub(r"<h[1-3]>", "\n\n", html)
    html = re.sub(r"</h[1-3]>", "\n\n", html)

    text = re.sub(r"<.*?>", "", html)
    return text.strip()

def load_page():
    url = entry.get()
    html = fetch_http(url)
    text = render_text(html)
    text_box.delete("1.0", tk.END)
    text_box.insert(tk.END, text)

# --- GUI ---
root = tk.Tk()
root.title("SearchWeb")
root.geometry("800x600")

entry = tk.Entry(root)
entry.pack(fill=tk.X, padx=5, pady=5)
entry.insert(0, "http://")

button = tk.Button(root, text="Open", command=load_page)
button.pack()

text_box = tk.Text(root, wrap=tk.WORD)
text_box.pack(fill=tk.BOTH, expand=True)

root.mainloop()
