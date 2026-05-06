import tkinter as tk

from tkinter import ttk

 

class MandelbrotApp:

    def __init__(self, root):

        self.root = root

        self.root.title("Mandelbrot Set")

 

        self.canvas = tk.Canvas(self.root, width=800, height=800, bg="black")

        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.on_press)

        self.canvas.bind("<B1-Motion>", self.on_drag)

        self.canvas.bind("<ButtonRelease-1>", self.on_release)

 

        self.progress_var = tk.DoubleVar()

        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)

        self.progress_bar.pack(fill=tk.X)

 

        self.draw_button = tk.Button(self.root, text="dessiner Mandelbrot", command=self.draw_mandelbrot)

        self.draw_button.pack()

 

        self.x_min, self.x_max = -2.0, 1.0

        self.y_min, self.y_max = -1.5, 1.5

 

        self.rect = None

        self.start_x = None

        self.start_y = None

 

    def mandelbrot(self, c, max_iter):

        z = 0

        n = 0

        while abs(z) <= 2 and n < max_iter:

            z = z*z + c

            n += 1

        return n

 

    def draw_mandelbrot(self, x_min=None, x_max=None, y_min=None, y_max=None):

        if x_min is not None and x_max is not None and y_min is not None and y_max is not None:

            self.x_min, self.x_max = x_min, x_max

            self.y_min, self.y_max = y_min, y_max

 

        width, height = 800, 800

        max_iter = 100

 

        self.canvas.delete("all")

        image = tk.PhotoImage(width=width, height=height)

        self.canvas.create_image((width//2, height//2), image=image, state="normal")

 

        for x in range(width):

            for y in range(height):

                real = self.x_min + (x / width) * (self.x_max - self.x_min)

                imag = self.y_min + (y / height) * (self.y_max - self.y_min)

                c = complex(real, imag)

                color = self.mandelbrot(c, max_iter)

                if color == max_iter:

                    color_hex = "#000000"

                else:

                    color_val = int(color * 255 / max_iter)

                    if color_val < 85:

                        color_hex = f'#{color_val*3:02x}0000'

                    elif color_val < 170:

                        color_hex = f'#00{color_val*3%255:02x}00'

                    else:

                        color_hex = f'#0000{color_val*3%255:02x}'

                image.put(color_hex, (x, y))

            self.progress_var.set((x + 1) / width * 100)

            self.root.update_idletasks()

 

        self.canvas.image = image

 

    def on_press(self, event):

        self.start_x = event.x

        self.start_y = event.y

        if self.rect:

            self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="white")

 

    def on_drag(self, event):

        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

 

    def on_release(self, event):

        end_x, end_y = event.x, event.y

        if end_x < self.start_x:

            self.start_x, end_x = end_x, self.start_x

        if end_y < self.start_y:

            self.start_y, end_y = end_y, self.start_y

 

        x_min = self.x_min + (self.start_x / 800) * (self.x_max - self.x_min)

        x_max = self.x_min + (end_x / 800) * (self.x_max - self.x_min)

        y_min = self.y_min + (self.start_y / 800) * (self.y_max - self.y_min)

        y_max = self.y_min + (end_y / 800) * (self.y_max - self.y_min)

 

        self.draw_mandelbrot(x_min, x_max, y_min, y_max)

 

if __name__ == "__main__":

    root = tk.Tk()

    app = MandelbrotApp(root)

    root.mainloop()