import curses
import time
import random
import sys

def draw_progress_bar(win, y, x, width, percent, color_pair):
    percent = max(0, min(100, percent))
    filled_len = int(width * percent / 100)
    empty_len = width - filled_len

    bar = ''
    if filled_len > 0:
        win.attron(curses.color_pair(color_pair))
        bar += '█' * filled_len
        win.attroff(curses.color_pair(color_pair))
    if empty_len > 0:
        bar += '░' * empty_len

    win.addstr(y, x, bar)
    percent_str = f'{percent:3d}%'
    win.addstr(y, x + width + 1, percent_str)

def run_progress(win, duration, color_pair, task_name):
    start_time = time.time()
    bar_width = 36 # чуть уже, чтобы поместиться в 50 колонок
    y_pos = 5
    x_pos = 5

    for i in range(3, 11):
        win.move(i, 0)
        win.clrtoeol()

    win.addstr(3, 5, f"Задача: {task_name}")
    win.refresh()

    while True:
        elapsed = time.time() - start_time
        percent = min(100, int((elapsed / duration) * 100))
        draw_progress_bar(win, y_pos, x_pos, bar_width, percent, color_pair)
        win.refresh()
        if elapsed >= duration:
            break
        time.sleep(0.05)

    draw_progress_bar(win, y_pos, x_pos, bar_width, 100, color_pair)
    win.refresh()

def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)

    height, width = 19, 50 # окно 50x19
    my_win = curses.newwin(height, width, 0, 0)
    my_win.keypad(True)
    curses.curs_set(1)
    my_win.nodelay(False)

    my_win.clear()
    my_win.box()
    my_win.addstr(0, 2, " ТЕРМИНАЛ 50x19 ", curses.A_REVERSE)
    my_win.refresh()

    prompt_color = curses.color_pair(1) | curses.A_BOLD

    while True:
        prompt_y = height - 2
        my_win.move(prompt_y, 2)
        my_win.clrtoeol()

        my_win.attron(prompt_color)
        my_win.addstr(prompt_y, 2, "arch@~$ ")
        my_win.attroff(prompt_color)
        my_win.refresh()

        curses.echo()
        command = my_win.getstr(prompt_y, 2 + len("arch@~$ "), 20).decode('utf-8').strip().lower()
        curses.noecho()
        my_win.move(prompt_y, 2)
        my_win.clrtoeol()

        if command == 'exit':
            break
        elif command == 'pkg':
            run_progress(my_win, 60, 1, "pkg install")
            my_win.addstr(9, 5, "Готово! ")
            my_win.refresh()
            time.sleep(1)
        elif command == 'apt':
            run_progress(my_win, 120, 2, "apt mining")
            earned = random.randint(1, 20)
            result_msg = f"mained {earned} ₽"
            my_win.addstr(9, 5, result_msg + " " * (width - len(result_msg) - 10))
            my_win.refresh()
            time.sleep(2)
        # Неизвестные команды игнорируются

        for i in range(3, 11):
            my_win.move(i, 1)
            my_win.clrtoeol()
        my_win.refresh()

    my_win.addstr(height-1, 2, "Выход...")
    my_win.refresh()
    time.sleep(1)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        pass # никаких сообщений об ошибках

