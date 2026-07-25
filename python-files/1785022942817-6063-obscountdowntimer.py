import threading
import keyboard
import time
import random
from rich import print
from dd_obs_websockets import OBSWebsocketsManager
from dd_audio_player import AudioManager

STARTING_TIME = 10 * 60  # in seconds (Min * Sec)

OBS_TIMER_TEXT = "??? Timer Text - Seconds ???"
OBS_TIMER_BACKGROUND = "Black Background 3"
OBS_BEES_SCENE = "/// Countdown Timer"  # scene containing the "bees" source
OBS_TIMER_GROUP = "Fake livesplit"  # group containing the timer text + background, moved as one unit

time_left = STARTING_TIME
countdown_timer_active = True
obswebsockets_manager = OBSWebsocketsManager()
audio_manager = AudioManager()


def format_time(seconds):
    seconds = int(seconds)
    total_minutes = seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    remaining_seconds = seconds % 60
    if hours > 0:
        # Format with hours: HH:MM:SS
        time_string = f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
    else:
        # Format without hours: MM:SS
        time_string = f"{minutes:02d}:{remaining_seconds:02d}"
    return time_string


# Counts down time
class CountdownTimerBot:
    def __init__(self):
        obswebsockets_manager.set_source_visibility("/// Countdown Timer", OBS_TIMER_TEXT, True)
        obswebsockets_manager.set_source_visibility("/// Countdown Timer", OBS_TIMER_BACKGROUND, True)

    def run(self):
        global countdown_timer_active, time_left
        time_left = STARTING_TIME
        how_long_is_a_second = 1

        while True:

            if countdown_timer_active:

                obswebsockets_manager.set_text(OBS_TIMER_TEXT, f"{format_time(time_left)}")

                if time_left <= 0:
                    # Time is up!
                    countdown_timer_active = False
                    print("[bold red]TIME'S UP![/bold red]")

                if time_left > 0:
                    randy = random.randint(1, 100)

                    # OUR PLAN
                    # 5% it adds second
                    if randy <= 5:
                        time_left += 1
                        print(f"[green]+1 second[/green] -> {format_time(time_left)}")
                    # 1% that it adds a MINUTE
                    elif randy <= 6:
                        time_left += 60
                        print(f"[green]+60 seconds[/green] -> {format_time(time_left)}")
                    # 1% chance that it drops a MINUTE
                    elif randy <= 7:
                        time_left -= 60
                        print(f"[red]-60 seconds[/red] -> {format_time(time_left)}")
                    # 5% that it freezes for 5 "seconds"
                    elif randy <= 12:
                        print(f"[blue]Freeze for {4 * how_long_is_a_second:.2f}s[/blue]")
                        time.sleep(4 * how_long_is_a_second)
                    # 1% chance that it doubles
                    elif randy <= 13:
                        time_left = time_left * 2
                        print(f"[magenta]Time doubled![/magenta] -> {format_time(time_left)}")
                    # 1% chance that it halves
                    elif randy <= 14:
                        time_left = time_left / 2
                        print(f"[magenta]Time halved![/magenta] -> {format_time(time_left)}")
                    # 1% that the seconds and the minutes swap
                    elif randy <= 15:
                        current_min = time_left // 60
                        current_sec = time_left % 60
                        time_left = (current_sec * 60) + current_min
                        print(f"[magenta]Minutes/seconds swapped![/magenta] -> {format_time(time_left)}")
                    # 1% it rounds to the nearest minute
                    elif randy <= 16:
                        time_left = round((time_left / 60) * 60)
                        print(f"[magenta]Rounded to nearest minute[/magenta] -> {format_time(time_left)}")
                    # 1% for timer to move to random spot
                    elif randy <= 17:
                        print("[cyan]Timer teleported![/cyan]")
                        new_pos = {"positionX": random.randint(0, 1820), "positionY": random.randint(0, 1010)}
                        obswebsockets_manager.set_source_transform(
                            new_pos, scene_name=OBS_BEES_SCENE, source_name=OBS_TIMER_GROUP
                        )
                    # 1% change a second becomes twice as fast
                    elif randy <= 18:
                        how_long_is_a_second = how_long_is_a_second / 2
                        print(f"[yellow]Time now moves 2x faster[/yellow] (1s = {how_long_is_a_second:.3f}s real)")
                    # 1% change a second becomes twice as long
                    elif randy <= 19:
                        how_long_is_a_second = how_long_is_a_second * 2
                        print(f"[yellow]Time now moves 2x slower[/yellow] (1s = {how_long_is_a_second:.3f}s real)")
                    # 1% BEE MODE
                    elif randy <= 20:
                        print("[bold yellow]BEES![/bold yellow]")
                        obswebsockets_manager.set_source_visibility(OBS_BEES_SCENE, "bees", True)
                        audio_manager.play_audio("bee.mp3", False, False, False)
                        time.sleep(how_long_is_a_second)
                        obswebsockets_manager.set_source_visibility(OBS_BEES_SCENE, "bees", False)
                    # 80% it deducts a second
                    else:
                        time_left -= 1

                    if randy < 10:
                        continue

            time.sleep(1)


# Listens to hotkey presses
class KeyPressBot:

    def run(self):
        global countdown_timer_active, time_left

        def toggle_pause():
            global countdown_timer_active
            countdown_timer_active = not countdown_timer_active
            state = "resumed" if countdown_timer_active else "paused"
            print(f"[yellow]Timer {state}[/yellow]")

        def reset_timer():
            global time_left, countdown_timer_active
            time_left = STARTING_TIME
            countdown_timer_active = True
            print("[green]Timer reset[/green]")

        def add_time(seconds):
            global time_left
            time_left += seconds
            print(f"[cyan]{seconds:+d} seconds -> {format_time(time_left)}[/cyan]")

        # F7: pause/resume
        keyboard.add_hotkey("f7", toggle_pause)
        # F5: reset back to STARTING_TIME
        keyboard.add_hotkey("f5", reset_timer)
        # Up/Down arrow: nudge by 10 seconds
        keyboard.add_hotkey("up", lambda: add_time(10))
        keyboard.add_hotkey("down", lambda: add_time(-10))
        # Esc: quit everything
        keyboard.add_hotkey("esc", lambda: (_ for _ in ()).throw(SystemExit))

        print("[bold]Hotkeys ready:[/bold] f7=pause/resume, f5=reset, up/down=+/-10s, esc=quit")

        # Blocks this thread forever, listening for the hotkeys above
        keyboard.wait("esc")


if __name__ == "__main__":
    countdown_bot = CountdownTimerBot()
    keypress_bot = KeyPressBot()

    countdown_thread = threading.Thread(target=countdown_bot.run, daemon=True)
    keypress_thread = threading.Thread(target=keypress_bot.run, daemon=True)

    countdown_thread.start()
    keypress_thread.start()

    try:
        while keypress_thread.is_alive():
            keypress_thread.join(timeout=0.5)
    except (KeyboardInterrupt, SystemExit):
        print("[red]Shutting down...[/red]")
