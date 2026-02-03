import webbrowser
import tkinter as tk
from tkinter import messagebox

# List of all links to open
links = [
    # Wikipedia pages
    "https://en.wikipedia.org/wiki/Israel",
    "https://en.wikipedia.org/wiki/Agartha",
    "https://en.wikipedia.org/wiki/Coin_edge",
    
    # YouTube video
    "https://www.youtube.com/watch?v=vHSNZK4Je-Y",
    
    # Image searches
    "https://stock.adobe.com/search?k=israel",
    "https://search.brave.com/images?q=aipac+logo&context=W3sic3JjIjoiaHR0cHM6Ly9jb250ZW50LmVuZXJnYWdlLmNvbS9jb21wYW55LWltYWdlcy9TRTY1OTEzL1NFNjU5MTNfbG9nb19vcmlnLnBuZyIsInRleHQiOiJBSVBBQyBDb21wYW55IExvZ28iLCJwYWdlX3VybCI6Imh0dHBzOi8vdG9wd29ya3BsYWNlcy5jb20vY29tcGFueS9hbWVyaWNhbi1pc3JhZWwtcHVibGljLWEvIn1d&sig=3785a5fe626fcaeaa93983a34d07b18c1a103e43869e0a48338f190d7dd013e7&nonce=1a52ce8669ff16d09d706dbb5ea531ae",
    "https://www.trackaipac.com/trump",
    "https://www.tiktok.com/@aipac/video/7582831655048580365"
]

# Optional: show a message first
root = tk.Tk()
root.withdraw()
messagebox.showinfo("Opening Links", "This program will open all the websites, images, and the YouTube video at once in your browser.")
root.destroy()

# Open all links without delay
for link in links:
    webbrowser.open(link)
