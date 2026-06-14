


import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import sys
import re
import os
from datetime import datetime


def get_downloads_path():
    """Возвращает путь к папке Загрузки на Windows"""
    if os.name == 'nt': 
        return os.path.join(os.environ['USERPROFILE'], 'Downloads')
    else:  
        return os.path.join(os.environ['HOME'], 'Downloads')

DOWNLOAD_FOLDER = get_downloads_path()

def generate_signal(expr: str, duration=1.0, fs=8000):

    expr = expr.strip().replace('\n', '').replace('\r', '')
    t = np.arange(0, duration, 1/fs)
    ns = {'np': np, 't': t, 'pi': np.pi, 'e': np.e}
    try:
        y = eval(expr, {"__builtins__": {}}, ns)
    except Exception as e:
        raise ValueError(f"Не удалось вычислить выражение: {e}")
    y = np.asarray(y, dtype=np.float64).flatten()
    return t, y

def plot_signal_and_spectrum(t, y, fs, expr, save_to_downloads=True):

    N = len(y)
    Y = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(N, 1/fs)
    amp = np.abs(Y) / N * 2
    if len(amp) > 0:
        amp[0] /= 2


    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(f"Сигнал: {expr}", fontsize=14, fontweight='bold')


    ax1.plot(t, y, linewidth=0.8, color='blue')
    ax1.set_xlabel("Время, с", fontsize=11)
    ax1.set_ylabel("Амплитуда", fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([t[0], t[-1]])
    ax1.set_title("Осциллограмма", fontsize=12)


    ax2.plot(freqs, amp, 'g-o', linewidth=1, markersize=3)
    ax2.set_xlabel("Частота, Гц", fontsize=11)
    ax2.set_ylabel("Амплитуда", fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, fs/2])
    ax2.set_title("Амплитудный спектр", fontsize=12)

    plt.tight_layout()
    

    if save_to_downloads:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(DOWNLOAD_FOLDER, f"signal_graph_{timestamp}.png")
        
        try:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"\n💾 График сохранён в файл: {save_path}")
        except Exception as e:
            print(f"\n⚠️ Не удалось сохранить график: {e}")
    

    plt.show()
    print("📊 График отображён на экране (закройте окно графика для продолжения)")

def save_wav(y, fs, filename="signal.wav"):
    """Сохраняет сигнал в WAV в папку Загрузки."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_without_ext = os.path.splitext(filename)[0]
    unique_filename = f"{name_without_ext}_{timestamp}.wav"
    full_path = os.path.join(DOWNLOAD_FOLDER, unique_filename)
    

    max_val = np.max(np.abs(y))
    if max_val > 0:
        y_norm = y / max_val * 0.9
    else:
        y_norm = y
    y_int16 = (y_norm * 32767).astype(np.int16)
    
    try:
        wavfile.write(full_path, fs, y_int16)
        print(f"\n💾 WAV-файл сохранён: {full_path}")
        return full_path
    except Exception as e:
        print(f"\n❌ Ошибка сохранения WAV: {e}")
        return None

def main():
    print("=" * 60)
    print("🎵 ВИРТУАЛЬНЫЙ ГЕНЕРАТОР СИГНАЛОВ v2.0 (Для Windows)")
    print("=" * 60)
    print("\nПоддерживаются функции numpy:")
    print("  • np.sin(), np.cos(), np.tan()  — тригонометрические")
    print("  • np.exp(), np.log(), np.sqrt() — экспонента и логарифмы")
    print("  • np.square(), np.abs()         — возведение в квадрат, модуль")
    print("\nПеременная времени: t")
    print("Константы: pi, e")
    print("\n📌 ПРИМЕРЫ формул:")
    print("  1. 0.5*np.sin(2*pi*100*t) + 0.3*np.sin(2*pi*1000*t)")
    print("  2. np.sin(2*pi*2*t) + np.sin(2*pi*1*t)  (восьмёрка)")
    print("  3. np.sin(2*pi*440*t) * np.exp(-3*t)    (затухание)")
    print("=" * 60)


    expr_input = input("\n🔧 Введите формулу сигнала: ").strip()
    expr = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', expr_input)
    
    if not expr:
        print("❌ Формула не введена, выход.")
        sys.exit(0)


    print("\n⚙️ ПАРАМЕТРЫ СИГНАЛА:")
    try:
        duration_input = input("  Длительность, с (по умолчанию 1.0): ").strip()
        duration = float(duration_input) if duration_input else 1.0
        
        fs_input = input("  Частота дискретизации, Гц (по умолчанию 8000): ").strip()
        fs = int(fs_input) if fs_input else 8000
    except ValueError:
        print("⚠️ Ошибка ввода чисел, используются значения по умолчанию.")
        duration, fs = 1.0, 8000

    print(f"\n📁 Все файлы будут сохранены в папку: {DOWNLOAD_FOLDER}")


    print("\n🔄 Генерация сигнала...")
    try:
        t, y = generate_signal(expr, duration, fs)
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"✅ Сгенерировано {len(y):,} отсчётов")
    print(f"   Длительность: {duration} с")
    print(f"   Частота дискретизации: {fs} Гц")


    print("\n📊 Построение графика...")
    plot_signal_and_spectrum(t, y, fs, expr, save_to_downloads=True)


    print("\n" + "=" * 60)
    save_ans = input("🎵 Сохранить звуковой файл (WAV)? (y/n): ").strip().lower()
    if save_ans == 'y':
        fname = input("  Имя файла (signal.wav): ").strip()
        if not fname:
            fname = "signal.wav"
        if not fname.endswith('.wav'):
            fname += '.wav'
        saved_path = save_wav(y, fs, fname)
        if saved_path:
            print(f"\n✨ Готово! Файл можно найти в {DOWNLOAD_FOLDER}")
    
    print("\n🎉 Программа завершена успешно!")
    print("💡 Совет: Закройте окно с графиком, чтобы продолжить работу")

if __name__ == "__main__":
    main()
