import random
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango

class BusinessRandomizerApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Рандомайзер")
        
        # Загрузка данных
        self.maps = self.get_list('maps.txt')
        self.times = self.get_list('time.txt')
        self.weather = self.get_list('weather.txt')
        
        self.set_default_size(360, 220)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        self.set_border_width(0)
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background: #f5f5f5;
            }
            button {
                background: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 5px 14px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 5px;
            }
            button:hover {
                background: #e8e8e8;
                border-color: #999999;
                border-radius: 5px;
            }
            button:active {
                background: #d0d0d0;
                border-color: #666666;
            }
            label {
                color: #333333;
                font-size: 14px;
            }
            .header-label {
                color: #666666;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
            .value-label {
                color: #000000;
                font-size: 14px;
                font-weight: 400;
                padding: 2px 0;
            }
            .value-label-empty {
                color: #aaaaaa;
                font-size: 14px;
                font-weight: 300;
                padding: 2px 0;
                font-style: italic;
            }
            .separator {
                background: #e0e0e0;
                min-height: 1px;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(25)
        main_box.set_margin_end(25)
        self.add(main_box)
        
        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.results_box.set_halign(Gtk.Align.FILL)
        main_box.pack_start(self.results_box, True, True, 0)
        
        self.show_empty_results()
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(8)
        
        self.button = Gtk.Button(label="Сгенерировать")
        self.button.connect("clicked", self.on_button_clicked)
        self.button.set_size_request(120, 30)
        button_box.pack_start(self.button, False, False, 0)
        
        main_box.pack_start(button_box, False, False, 0)
        
        self.connect("key-press-event", self.on_key_press)
    
    def get_list(self, file_name: str) -> list[str]:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                return [line.rstrip('\n') for line in f if line.strip()]
        except FileNotFoundError:
            return ["Файл не найден"]
    
    def show_empty_results(self):
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        items = [
            ("Карта", "—"),
            ("Время", "—"),
            ("Погода", "—")
        ]
        
        for label_text, placeholder in items:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row_box.set_halign(Gtk.Align.FILL)
            
            label = Gtk.Label()
            label.set_markup(f"<span weight='600'>{label_text}</span>")
            label.set_halign(Gtk.Align.START)
            label.set_size_request(60, -1)
            label.get_style_context().add_class('header-label')
            
            value_label = Gtk.Label()
            value_label.set_text(placeholder)
            value_label.set_halign(Gtk.Align.START)
            value_label.get_style_context().add_class('value-label-empty')
            
            row_box.pack_start(label, False, False, 0)
            row_box.pack_start(value_label, True, True, 0)
            
            self.results_box.pack_start(row_box, False, False, 0)
        
        self.results_box.show_all()
    
    def update_results(self):
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        map_value = random.choice(self.maps) if self.maps else "Нет данных"
        time_value = random.choice(self.times) if self.times else "Нет данных"
        weather_value = random.choice(self.weather) if self.weather else "Нет данных"
        
        items = [
            ("Карта", map_value),
            ("Время", time_value),
            ("Погода", weather_value)
        ]
        
        for label_text, value in items:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row_box.set_halign(Gtk.Align.FILL)
            
            label = Gtk.Label()
            label.set_markup(f"<span weight='600'>{label_text}</span>")
            label.set_halign(Gtk.Align.START)
            label.set_size_request(60, -1)
            label.get_style_context().add_class('header-label')
            
            value_label = Gtk.Label()
            value_label.set_text(value)
            value_label.set_halign(Gtk.Align.START)
            value_label.set_ellipsize(Pango.EllipsizeMode.END)
            value_label.get_style_context().add_class('value-label')
            
            row_box.pack_start(label, False, False, 0)
            row_box.pack_start(value_label, True, True, 0)
            
            self.results_box.pack_start(row_box, False, False, 0)
        
        self.results_box.show_all()
    
    def on_button_clicked(self, widget):
        self.update_results()
    
    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Return or event.keyval == Gdk.KEY_KP_Enter:
            self.update_results()

def main():
    win = BusinessRandomizerApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()