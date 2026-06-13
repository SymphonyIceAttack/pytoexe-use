import shutil
from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from tkinter.ttk import Notebook
from PIL import Image, ImageFilter, ImageEnhance
import os
import pyperclip
import json
from copy import deepcopy

from sklearn.cluster import KMeans
import numpy as np

import cv2

from PIL import Image
import rembg

from image_info import ImageInfo
from enhance_slider_window import EnhanceSliderWindow


CONFIG_FILE = "config.json"


class PyPhotoEditor:
    def __init__(self):
        self.root = Tk()
        self.image_tabs = Notebook(self.root)
        self.opened_images = []
        self.last_viewed_images = []

        self.init()

        self.open_recent_menu = None

        


    def init(self):
        self.root.title("Фоторедактор")
        self.root.iconphoto(True, PhotoImage(file="resources/icon.png"))
        self.image_tabs.enable_traversal()

        self.root.bind("<Escape>", self._close)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"opened_images": [], "last_viewed_images": []}, f)

        else:
            self.load_images_from_config()


    def run(self):
        self.draw_menu()
        self.draw_widgets()

        self.root.mainloop()


    def draw_menu(self):
        menu_bar = Menu(self.root)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Открыть", command=self.open_new_images)

        self.open_recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Открыть недавние изображения", menu=self.open_recent_menu)
        for path in self.last_viewed_images:
            self.open_recent_menu.add_command(label=path, command=lambda x=path: self.add_new_image(x))

        file_menu.add_separator()
        file_menu.add_command(label="Сохранить", command=self.save_current_image)
        file_menu.add_command(label="Сохранить как", command=self.save_image_as)
        file_menu.add_command(label="Сохранить все", command=self.save_all_changes)
        file_menu.add_separator()
        file_menu.add_command(label="Закрыть изображение", command=self.close_current_image)
        file_menu.add_separator()
        file_menu.add_command(label="Удалить изображение", command=self.delete_current_image)
        file_menu.add_command(label="Переместить изображение", command=self.move_current_image)
        file_menu.add_separator()

        clipboard_menu = Menu(file_menu, tearoff=0)
        clipboard_menu.add_command(label="Добавить имя изображения в буфер обмена", command=lambda: self.save_to_clipboard("name"))
        clipboard_menu.add_command(label="Добавить путь к папке с изображением в буфер обмена", command=lambda: self.save_to_clipboard("dir"))
        clipboard_menu.add_command(label="Добавить полный путь до изображения в буфер обмена", command=lambda: self.save_to_clipboard("path"))
        file_menu.add_cascade(label="Буфер обмена", menu=clipboard_menu)

        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._close)
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = Menu(menu_bar, tearoff=0)
        
        rotate_menu = Menu(edit_menu, tearoff=0)
        rotate_menu.add_command(label="Повернуть влево на 90", command=lambda: self.rotate_current_image(90))
        rotate_menu.add_command(label="Повернуть вправо на 90", command=lambda: self.rotate_current_image(-90))
        rotate_menu.add_command(label="Повернуть влево на 180", command=lambda: self.rotate_current_image(180))
        rotate_menu.add_command(label="Повернуть вправо на 180", command=lambda: self.rotate_current_image(-180))

        flip_menu = Menu(edit_menu, tearoff=0)
        flip_menu.add_command(label="Горизонтально", command=lambda: self.flip_current_image(Image.FLIP_LEFT_RIGHT))
        flip_menu.add_command(label="Вертикально", command=lambda: self.flip_current_image(Image.FLIP_TOP_BOTTOM))

        resize_menu = Menu(edit_menu, tearoff=0)
        resize_menu.add_command(label="25% от первоначального размера", command=lambda: self.resize_current_image(25))
        resize_menu.add_command(label="50% от первоначального размера", command=lambda: self.resize_current_image(50))
        resize_menu.add_command(label="75% от первоначального размера", command=lambda: self.resize_current_image(75))
        resize_menu.add_command(label="125% от первоначального размера", command=lambda: self.resize_current_image(125))
        resize_menu.add_command(label="150% от первоначального размера", command=lambda: self.resize_current_image(150))
        resize_menu.add_command(label="200% от первоначального размера", command=lambda: self.resize_current_image(200))

        filter_menu = Menu(edit_menu, tearoff=0)
        filter_menu.add_command(label="Блюр", command=lambda:self.apply_filter_current_image(ImageFilter.BLUR))
        filter_menu.add_command(label="Резкость", command=lambda:self.apply_filter_current_image(ImageFilter.SHARPEN))
        filter_menu.add_command(label="Контур", command=lambda:self.apply_filter_current_image(ImageFilter.CONTOUR))
        filter_menu.add_command(label="Детализированность", command=lambda:self.apply_filter_current_image(ImageFilter.DETAIL))
        filter_menu.add_command(label="Сглаживание", command=lambda:self.apply_filter_current_image(ImageFilter.SMOOTH))

        crop_menu = Menu(edit_menu, tearoff=0)
        crop_menu.add_command(label="Начать выделение", command=self.start_crop_selection_of_current_image)
        crop_menu.add_command(label="Обрезать изображение", command=self.crop_selection_of_current_image)
        crop_menu.add_command(label="Отмена", command=self.cancel_selection_of_current_image)

        convert_menu = Menu(edit_menu, tearoff=0)
        convert_menu.add_command(label="Ч/Б", command=lambda: self.convert_current_image("1"))
        convert_menu.add_command(label="Оттенки серого", command=lambda: self.convert_current_image("L"))
        convert_menu.add_command(label="RGB", command=lambda: self.convert_current_image("RGB"))
        convert_menu.add_command(label="RGBA", command=lambda: self.convert_current_image("RGBA"))
        convert_menu.add_command(label="CMYK", command=lambda: self.convert_current_image("CMYK"))
        convert_menu.add_command(label="LAB", command=lambda: self.convert_current_image("LAB"))
        convert_menu.add_command(label="HSV", command=lambda: self.convert_current_image("HSV"))
        convert_menu.add_command(label="Прокрутка RGB цветов", command=lambda: self.convert_current_image("roll"))
        convert_menu.add_command(label="Красный", command=lambda: self.convert_current_image("R"))
        convert_menu.add_command(label="Зеленый", command=lambda: self.convert_current_image("G"))
        convert_menu.add_command(label="Синий", command=lambda: self.convert_current_image("B"))


        enhance_menu = Menu(edit_menu, tearoff=0)
        enhance_menu.add_command(label="Насыщенность", command=lambda: self.enhance_current_image("Насыщенность", ImageEnhance.Color))
        enhance_menu.add_command(label="Контрастность", command=lambda: self.enhance_current_image("Контрастность", ImageEnhance.Contrast))
        enhance_menu.add_command(label="Яркость", command=lambda: self.enhance_current_image("Яркость", ImageEnhance.Brightness))
        enhance_menu.add_command(label="Размытие", command=lambda: self.enhance_current_image("Размытие", ImageEnhance.Sharpness))

        edit_menu.add_cascade(label="Повернуть", menu=rotate_menu)
        edit_menu.add_cascade(label="Отзеркалить", menu=flip_menu)
        edit_menu.add_cascade(label="Изменить размер", menu=resize_menu)
        edit_menu.add_separator()
        edit_menu.add_cascade(label="Фильтр", menu=filter_menu)
        edit_menu.add_cascade(label="Конвертировать", menu=convert_menu)
        edit_menu.add_cascade(label="Улучшить", menu=enhance_menu)
        edit_menu.add_separator()
        edit_menu.add_cascade(label="Обрезать", menu=crop_menu)

        menu_bar.add_cascade(label="Редактировать", menu=edit_menu)

        special_menu = Menu(menu_bar, tearoff=0)
        special_menu.add_command(label="Реставрация фото", command=self.restore_old_photo)
        special_menu.add_command(label="Генерация палитры", command=self.generate_color_palette)
        special_menu.add_command(label="Удалить фон", command=self.remove_bg_current_image)
        menu_bar.add_cascade(label="Особые действия", menu=special_menu)

        self.root.configure(menu=menu_bar)


    def update_open_recent_menu(self):
        if self.open_recent_menu is None:
            return

        self.open_recent_menu.delete(0, "end")
        for path in self.last_viewed_images:
            self.open_recent_menu.add_command(label=path, command=lambda x=path: self.add_new_image(x))


    def draw_widgets(self):
        self.image_tabs.pack(fill="both", expand=1)


    def load_images_from_config(self):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        self.last_viewed_images = config["last_viewed_images"]
        paths = config["opened_images"]
        for path in paths:
            self.add_new_image(path)


    def open_new_images(self):
        image_paths = fd.askopenfilenames(filetypes=(("Images", "*.jpeg;*.jpg;*.png"), ))
        for image_path in image_paths:
            self.add_new_image(image_path)

            if image_path not in self.last_viewed_images:
                self.last_viewed_images.append(image_path)
            else:
                self.last_viewed_images.remove(image_path)
                self.last_viewed_images.append(image_path)
            
            if len(self.last_viewed_images) > 5:
                del self.last_viewed_images[0]

        self.update_open_recent_menu()


    def add_new_image(self, image_path):
        if not os.path.isfile(image_path):
            if image_path in self.last_viewed_images:
                self.last_viewed_images.remove(image_path)
                self.update_open_recent_menu()
            return

        opened_images = [info.path for info in self.opened_images]
        if image_path in opened_images:
            index = opened_images.index(image_path)
            self.image_tabs.select(index)
            return

        image = Image.open(image_path)
        image_tab = Frame(self.image_tabs)

        image_info = ImageInfo(image, image_path, image_tab)
        self.opened_images.append(image_info)

        image_tab.rowconfigure(0, weight=1)
        image_tab.columnconfigure(0, weight=1)

        canvas = Canvas(image_tab, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky='nsew')
        canvas.update()

        image_info.set_canvas(canvas)

        self.image_tabs.add(image_tab, text=image_info.filename())
        self.image_tabs.select(image_tab)

        
    def current_image(self):
        current_tab = self.image_tabs.select()
        if not current_tab:
            return None
        tab_number = self.image_tabs.index(current_tab)

        return self.opened_images[tab_number]


    def save_current_image(self):
        image = self.current_image()
        if not image:
            return
        if not image.unsaved:
            return

        image.save()
        self.image_tabs.add(image.tab, text=image.filename())


    def save_image_as(self):
        image = self.current_image()
        if not image:
            return
        
        try:
            image.save_as()
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Ошибка сохранения", str(e))


    def save_all_changes(self):
        for image_info in self.opened_images:
            if not image_info.unsaved:
                continue
            image_info.save()
            self.image_tabs.tab(image_info.tab, text=image_info.filename())


    def close_current_image(self):
        image = self.current_image()
        if not image:
            return
        
        if image.unsaved:
            if not mb.askyesno("У вас есть несохранённые изменения", "Сохранить перед закрытием?"):
                return
            
        image.close()
        self.image_tabs.forget(image.tab)
        self.opened_images.remove(image)


    def delete_current_image(self):
        image = self.current_image()
        if not image:
            return
        
        if not mb.askokcancel("Удаление изображения", "Вы уверены что хотите удалить изображение? \nЭту операцию нельзя отменить!"):
            return

        image.delete()
        self.image_tabs.forget(image.tab)
        self.opened_images.remove(image)


    def move_current_image(self):
        image = self.current_image()
        if not image:
           return
        image.move()
        self.update_image_inside_app(image)


    def update_image_inside_app(self, image_info):
        image_info.update_image_on_canvas()
        self.image_tabs.tab(image_info.tab, text = image_info.filename())


    def rotate_current_image(self, degrees):
        image = self.current_image()
        if not image:
            return

        image.rotate(degrees)
        image.unsaved = True
        self.update_image_inside_app(image)


    def flip_current_image(self, mode):
        image = self.current_image()
        if not image:
            return

        image.flip(mode)
        image.unsaved = True
        self.update_image_inside_app(image)


    def resize_current_image(self, percents):
        image = self.current_image()
        if not image:
            return

        image.resize(percents)
        image.unsaved = True
        self.update_image_inside_app(image)


    def apply_filter_current_image(self, filter_type):
       image = self.current_image()
       if not image:
            return

       image.filter(filter_type)
       image.unsaved = True
       self.update_image_inside_app(image)


    def start_crop_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return
        
        image.start_crop_selection()


    def crop_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return
        
        try:
            image.crop_selected_area()
            image.unsaved = True
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Ошибка обрезания", str(e))


    def cancel_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return
        
        try:
            image.cancel_crop_selection()
        except ValueError as e:
            mb.showerror("Ошибка обрезания", str(e))


    def convert_current_image(self, mode):
        image = self.current_image()
        if not image:
            return
        
        try:
            image.convert(mode)
            image.unsaved = True
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Ошибка преобразования", str(e))


    def enhance_current_image(self, name, enhance):
        image = self.current_image()
        if not image:
            return

        EnhanceSliderWindow(self.root, name, enhance, image, self.update_image_inside_app)


    def save_to_clipboard(self, mode):
        image = self.current_image()
        if not image:
          return
        
        if mode == "name":
            pyperclip.copy(image.filename(no_star=True))
        elif mode == "dir":
            pyperclip.copy(image.directory(no_star=True))
        elif mode == "path":
            pyperclip.copy(image.full_path(no_star=True))


    def unsaved_images(self):
        for info in self.opened_images:
            if info.unsaved:
                return True
        return False
    

    def save_images_to_config(self):
        paths = [info.full_path(no_star = True) for info in self.opened_images]
        images = {"opened_images": paths, "last_viewed_images": self.last_viewed_images}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(images, f, indent=4)



    def _close(self, event=None):
        if self.unsaved_images():
            if not mb.askyesno("Несохраненные изменения", "У вас есть несохраненные изменения! Закрыть программу?"):
                return
            
        self.save_images_to_config()
            
        self.root.quit()

    def generate_color_palette(self):
        image_info = self.current_image()
        if not image_info:
            mb.showerror("Ошибка", "Сначала откройте изображение!")
            return

        try:
            small_img = image_info.image.copy()
            small_img.thumbnail((200, 200))

            pixels = np.array(small_img).reshape(-1, 3)

            kmeans = KMeans(n_clusters=5, random_state=42)
            kmeans.fit(pixels)

            main_colors_hex = []
            for center in kmeans.cluster_centers_:
                r, g, b = map(int, center)
                hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                main_colors_hex.append(hex_color)

            self._show_palette_window(main_colors_hex)

        except Exception as e:
            mb.showerror("Ошибка анализа", f"Не удалось сгенерировать палитру:\n{str(e)}")

    def _show_palette_window(self, colors_hex):
        """Отображает окно с цветовыми плашками."""
        palette_win = Toplevel(self.root)
        palette_win.title("Цветовая палитра")

        frame = Frame(palette_win, padx=15, pady=15)
        frame.pack()

        for i, color in enumerate(colors_hex):
            color_box = Label(frame, text=f"{color}", bg=color, fg='white' if self._is_dark(color) else 'black')
            color_box.config(width=15, height=2, relief="ridge", bd=2)
            color_box.grid(row=0, column=i, padx=5, pady=10)
            
            row = i // 5
            col = i % 5
            color_box.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")

            frame.grid_columnconfigure(col, weight=1)
            frame.grid_rowconfigure(row, weight=1)

        palette_win.update_idletasks()
        
        required_width = frame.winfo_reqwidth()
        required_height = frame.winfo_reqheight()
        
        palette_win.minsize(required_width, required_height)
        
        frame.grid_propagate(False) 

    @staticmethod
    def _is_dark(hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 125
    
    def restore_old_photo(self):
        image_info = self.current_image()
        if not image_info:
            mb.showerror("Ошибка", "Сначала откройте изображение!")
            return

        try:
            self.root.config(cursor="wait")
            
            img_pil = image_info.image

            img_cv = np.array(img_pil)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

            denoised_cv = cv2.fastNlMeansDenoisingColored(
                src=img_cv,
                h=10,                
                hColor=10,          
                templateWindowSize=7,
                searchWindowSize=21 
            )

            sharpened_cv = cv2.addWeighted(denoised_cv, 1.5, denoised_cv, 0, -3) 

            sharpened_rgb = cv2.cvtColor(sharpened_cv, cv2.COLOR_BGR2RGB)
            new_img_pil = Image.fromarray(sharpened_rgb)

            image_info.set_image(new_img_pil)
            image_info.unsaved = True
            self.update_image_inside_app(image_info)

        except Exception as e:
            mb.showerror("Ошибка обработки", f"Не удалось улучшить фото:\n{str(e)}")
        finally:
            self.root.config(cursor="")

    def _remove_background(self, pil_image):
        import io
        import rembg
        from PIL import Image

        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
    
        output = rembg.remove(buffered.getvalue())
    
        return Image.open(io.BytesIO(output))


    def remove_bg_current_image(self):
        image = self.current_image()
        if not image:
            return 

        image._save_state_to_history()

        try:
            new_image = self._remove_background(image.image)
        
            image.set_image(new_image)
        
            image.unsaved = True
            self.update_image_inside_app(image)
        
            print("Фон успешно удален!")

        except Exception as e:
            mb.showerror("Ошибка", f"Не удалось удалить фон: {str(e)}")

if __name__ == "__main__":
    PyPhotoEditor().run()