# cook your dish here
# cook your dish here
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.basemap import Basemap
import tkinter as tk
from tkinter import Frame, Button

# Задаём координаты (широта, долгота) точки
coordinates = [    (37.7749, -122.4194),  # San Francisco    (34.0522, -118.2437),  # Los Angeles    (36.1699, -115.1398),  # Las Vegas    (40.7128, -74.0060),   # New York City    (41.8781, -87.6298)    # Chicago]

# Разделяем широту и долготу
latitudes = [coord[0] for coord in coordinates]
longitudes = [coord[1] for coord in coordinates]

# Функция для настройки графика
def setup_map(lats, lons):
    fig, ax = plt.subplots(figsize=(8, 8))
    m = Basemap(projection='lcc', resolution='h',
                lat_0=np.mean(lats), lon_0=np.mean(lons),
                width=5E6, height=3E6)
    
    m.shadedrelief()
    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary(fill_color='aqua')
    m.fillcontinents(color='lightgreen', lake_color='aqua')

    return fig, ax, m  # Исправлено: заменено "]" на "}"

# Инициализация графика
fig, ax, m = setup_map(latitudes, longitudes)
point, = ax.plot([], [], 'bo')  # 'bo' - синий круг

# Настройка анимации
def init():
    point.set_data([], [])
    return point,

def update(frame):
    x, y = m(longitudes[frame], latitudes[frame])
    point.set_data(x, y)
    return point,

# Функция для запуска анимации
def start_animation():
    ani = animation.FuncAnimation(fig, update, frames=len(coordinates), init_func=init, blit=True, repeat=False)
    plt.xlabel('Долгота')
    plt.ylabel('Широта')
    plt.title('Движение цели по координатам')
    plt.grid()
    plt.show()

# Создание пользовательского интерфейса
root = tk.Tk()
root.title("Анимация движения по координатам")

frame = Frame(root)
frame.pack()

start_button = Button(frame, text="Начать анимацию", command=start_animation)
start_button.pack()

root.mainloop()
