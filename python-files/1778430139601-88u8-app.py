import tkinter as tk
from plyer import notification as system_notification
import random
def create_windows():
    root = tk.Tk()
    root.withdraw() 

    system_notification.notify(
        title='System Antivires',
        message="there is a risk in your system",
        timeout=2
    )

    for i in range(50):
        top = tk.Toplevel(root)
        top.title("HACKING...")
        x = random.randint(0, root.winfo_screenwidth() - 300)
        y = random.randint(0, root.winfo_screenheight() - 100)
        top.geometry(f"300x100+{x}+{y}")
        top.attributes("-topmost", True) 
        
        tk.Label(top, text="Error.. Error..", padx=20, pady=20).pack()
        
        tk.Button(top, text="OK", command=top.destroy, width=10).pack()
    for i in range(50):
        top = tk.Toplevel(root)
        top.title("HACKING...")
        # x = random.randint(0, root.winfo_screenwidth() - 300)
        # y = random.randint(0, root.winfo_screenheight() - 100)
        top.geometry(f"300x100+{100+(i*10)}+{100+(i*10)}")
        top.attributes("-topmost", True) 
        
        tk.Label(top, text="Error.. Error..", padx=20, pady=20).pack()
        
        tk.Button(top, text="OK", command=top.destroy, width=10).pack()

    root.mainloop()

if __name__ == "__main__":
    create_windows()