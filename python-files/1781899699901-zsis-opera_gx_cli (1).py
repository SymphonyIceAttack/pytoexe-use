#!/usr/bin/env python3
"""
opera_gx_cli.py
===============

An interactive command-line automation tool that launches and controls
Opera GX using Playwright. Opera GX is Chromium-based, so this uses
Playwright's chromium.launch() pointed at Opera GX's actual executable.

Designed to be used in a loop with an AI assistant:
  1. You run a command (e.g. take a screenshot).
  2. You share/describe the screenshot to your assistant.
  3. The assistant gives you back coordinates / actions.
  4. You type those into this tool.

USAGE:
    python opera_gx_cli.py

Then type `help` to see all commands.
"""

import sys
import os
import shlex
import platform
import traceback
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("[ERROR] Playwright is not installed.")
    print()
    print("Install it with:")
    print("    pip install playwright")
    print("    playwright install chromium")
    print()
    sys.exit(1)


SCREENSHOT_DIR = Path("./screenshots")
DEFAULT_VIEWPORT = {"width": 1280, "height": 800}


# ----------------------------------------------------------------------
# Opera GX path detection
# ----------------------------------------------------------------------

def find_opera_gx_path() -> str:
    """
    Attempts to auto-detect the Opera GX executable on Windows, Mac, or Linux.
    Returns the path as a string, or None if not found.
    """
    system = platform.system()
    candidates = []

    if system == "Windows":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        candidates = [
            os.path.join(local_appdata, "Programs", "Opera GX", "launcher.exe"),
            os.path.join(local_appdata, "Programs", "Opera GX", "opera.exe"),
            os.path.join(program_files, "Opera GX", "launcher.exe"),
            os.path.join(program_files, "Opera GX", "opera.exe"),
            os.path.join(program_files_x86, "Opera GX", "launcher.exe"),
            os.path.join(program_files_x86, "Opera GX", "opera.exe"),
        ]

    elif system == "Darwin":  # macOS
        candidates = [
            "/Applications/Opera GX.app/Contents/MacOS/Opera GX",
            os.path.expanduser("~/Applications/Opera GX.app/Contents/MacOS/Opera GX"),
        ]

    elif system == "Linux":
        candidates = [
            "/usr/bin/opera-gx",
            "/usr/lib/x86_64-linux-gnu/opera-gx/opera-gx",
            "/opt/opera-gx/opera-gx",
            os.path.expanduser("~/.local/bin/opera-gx"),
        ]

    for path in candidates:
        if path and os.path.isfile(path):
            return path

    return None


# ----------------------------------------------------------------------
# Browser session wrapper
# ----------------------------------------------------------------------

class OperaGXSession:
    """Wraps a Playwright browser/page launched against Opera GX's binary."""

    def __init__(self, executable_path: str, headless: bool = False, viewport=None, user_data_dir: str = None):
        self.executable_path = executable_path
        self.headless = headless
        self.viewport = viewport or dict(DEFAULT_VIEWPORT)
        self.user_data_dir = user_data_dir or self._default_user_data_dir()
        self.playwright = None
        self.browser = None  # not used for persistent context, kept for API symmetry
        self.context = None
        self.page = None
        self.screenshot_count = 0

    @staticmethod
    def _default_user_data_dir() -> str:
        """
        A dedicated profile folder for automation, NOT your real Opera GX
        profile. Reusing your live profile makes Playwright fight with any
        already-running Opera GX instance over the same lock files, which is
        what was causing the launch failures. This folder will be created
        on first run and Opera GX will treat it as a fresh profile (you'll
        need to sign in / re-add extensions here once).
        """
        if platform.system() == "Windows":
            base = os.environ.get("LOCALAPPDATA", str(Path.home()))
        else:
            base = str(Path.home())
        return os.path.join(base, "opera_gx_cli_profile")

    def start(self):
        print("🚀 Launching Opera GX...")
        self.playwright = sync_playwright().start()
        try:
            # FIXED: user_data_dir must go to launch_persistent_context(),
            # not as a --user-data-dir arg to launch(). Newer Playwright
            # versions reject the latter outright.
            self.context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                executable_path=self.executable_path,
                headless=self.headless,
                viewport=self.viewport,
                args=["--start-maximized"] if not self.headless else [],
            )
        except Exception as e:
            raise RuntimeError(
                f"Could not launch Opera GX at '{self.executable_path}'.\n"
                f"Underlying error: {e}"
            )

        # launch_persistent_context() usually opens with one blank page already
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        print(f"✅ Opera GX is open. Viewport: {self.viewport['width']}x{self.viewport['height']}")
        print(f"✅ Using automation profile at: {self.user_data_dir}")

    def stop(self):
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"⚠️  Warning during shutdown: {e}")

    # ---------- actions ----------

    def goto(self, url: str):
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        print(f"🌐 Navigating to {url} ...")
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print(f"✅ Loaded: {self.page.title()}")

    def click_at(self, x: float, y: float, button: str = "left", clicks: int = 1):
        label = {"left": "Left-click", "right": "Right-click"}.get(button, "Click")
        if clicks == 2:
            label = "Double-click"
        print(f"🖱️  {label} at ({x}, {y}) ...")
        self.page.mouse.click(x, y, button=button, click_count=clicks)
        print("✅ Click sent.")

    def double_click_at(self, x: float, y: float):
        self.click_at(x, y, clicks=2)

    def right_click_at(self, x: float, y: float):
        self.click_at(x, y, button="right")

    def move_to(self, x: float, y: float):
        print(f"🖱️  Moving mouse to ({x}, {y}) ...")
        self.page.mouse.move(x, y)
        print("✅ Mouse moved.")

    def type_text(self, text: str, delay_ms: int = 20):
        print(f"⌨️  Typing: {text!r}")
        self.page.keyboard.type(text, delay=delay_ms)
        print("✅ Text typed.")

    def press_key(self, key: str):
        # Examples: Enter, Tab, Escape, Backspace, ArrowDown, ArrowUp,
        # ArrowLeft, ArrowRight, Control+A, Shift+Tab, PageDown, Home, End
        print(f"⌨️  Pressing key: {key}")
        self.page.keyboard.press(key)
        print("✅ Key pressed.")

    def scroll(self, dx: int = 0, dy: int = 0):
        print(f"📜 Scrolling by (dx={dx}, dy={dy}) ...")
        self.page.mouse.wheel(dx, dy)
        print("✅ Scrolled.")

    def screenshot(self, filename: str = None) -> str:
        SCREENSHOT_DIR.mkdir(exist_ok=True)
        if not filename:
            self.screenshot_count += 1
            filename = f"shot_{self.screenshot_count:03d}.png"
        if not filename.lower().endswith(".png"):
            filename += ".png"
        path = SCREENSHOT_DIR / filename
        self.page.screenshot(path=str(path))
        print(f"📸 Screenshot saved: {path.resolve()}")
        return str(path.resolve())

    def set_viewport(self, width: int, height: int):
        self.viewport = {"width": width, "height": height}
        self.page.set_viewport_size(self.viewport)
        print(f"✅ Viewport set to {width}x{height}")

    def show_viewport(self):
        size = self.page.viewport_size or self.viewport
        print(f"📐 Current viewport: {size['width']}x{size['height']}")

    def go_back(self):
        print("⬅️  Going back...")
        self.page.go_back()
        print("✅ Done.")

    def go_forward(self):
        print("➡️  Going forward...")
        self.page.go_forward()
        print("✅ Done.")

    def reload(self):
        print("🔄 Reloading page...")
        self.page.reload()
        print("✅ Reloaded.")

    def wait(self, seconds: float):
        print(f"⏳ Waiting {seconds}s ...")
        self.page.wait_for_timeout(seconds * 1000)
        print("✅ Done waiting.")

    def current_info(self):
        print(f"🔗 URL:   {self.page.url}")
        print(f"📄 Title: {self.page.title()}")
        self.show_viewport()


# ----------------------------------------------------------------------
# Command parsing
# ----------------------------------------------------------------------

HELP_TEXT = """
📋 AVAILABLE COMMANDS
----------------------------------------------------------------
  goto <url>              🌐 Navigate to a URL (e.g. goto example.com)
  click <x> <y>            🖱️  Left-click at pixel coordinates
  rclick <x> <y>           🖱️  Right-click at pixel coordinates
  dclick <x> <y>           🖱️  Double-click at pixel coordinates
  move <x> <y>             🖱️  Move mouse without clicking
  type <text...>           ⌨️  Type text into the focused element
  press <key>              ⌨️  Press a key (Enter, Tab, Escape, Backspace,
                              ArrowDown, ArrowUp, ArrowLeft, ArrowRight,
                              Control+A, Shift+Tab, PageDown, Home, End...)
  scroll <dx> <dy>         📜 Scroll the page (e.g. scroll 0 500 = scroll down)
  viewport [w] [h]         📐 Show viewport size, or set it (viewport 1366 768)
  screenshot [name.png]    📸 Save a screenshot to ./screenshots/
  back                     ⬅️  Go back in history
  forward                  ➡️  Go forward in history
  reload                   🔄 Reload the current page
  wait <seconds>           ⏳ Pause (e.g. wait 1.5)
  info                     ℹ️  Show current URL, title, and viewport
  help                     📋 Show this help message
  quit / exit              ❌ Close Opera GX and exit
----------------------------------------------------------------
💡 TIP: Coordinates are pixels from the top-left (0,0) of the page
   viewport — not the OS window. Take a screenshot, describe it to
   your AI assistant, and they'll give you (x, y) to click.
"""


def parse_and_run(session: OperaGXSession, line: str) -> bool:
    """Parses and executes one command line. Returns False to quit."""
    line = line.strip()
    if not line:
        return True

    try:
        parts = shlex.split(line)
    except ValueError as e:
        print(f"❌ Could not parse command: {e}")
        return True

    cmd = parts[0].lower()
    args = parts[1:]

    try:
        if cmd in ("quit", "exit"):
            return False

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "goto":
            if not args:
                print("Usage: goto <url>")
            else:
                session.goto(" ".join(args))

        elif cmd == "click":
            if len(args) < 2:
                print("Usage: click <x> <y>")
            else:
                session.click_at(float(args[0]), float(args[1]))

        elif cmd == "rclick":
            if len(args) < 2:
                print("Usage: rclick <x> <y>")
            else:
                session.right_click_at(float(args[0]), float(args[1]))

        elif cmd == "dclick":
            if len(args) < 2:
                print("Usage: dclick <x> <y>")
            else:
                session.double_click_at(float(args[0]), float(args[1]))

        elif cmd == "move":
            if len(args) < 2:
                print("Usage: move <x> <y>")
            else:
                session.move_to(float(args[0]), float(args[1]))

        elif cmd == "type":
            if not args:
                print("Usage: type <text...>")
            else:
                session.type_text(" ".join(args))

        elif cmd == "press":
            if not args:
                print("Usage: press <KeyName>  (e.g. press Enter, press Control+A)")
            else:
                session.press_key(args[0])

        elif cmd == "scroll":
            if len(args) < 2:
                print("Usage: scroll <dx> <dy>  (e.g. scroll 0 500)")
            else:
                session.scroll(int(float(args[0])), int(float(args[1])))

        elif cmd == "viewport":
            if not args:
                session.show_viewport()
            elif len(args) == 2:
                session.set_viewport(int(args[0]), int(args[1]))
            else:
                print("Usage: viewport            (show current size)")
                print("       viewport <w> <h>     (set size, e.g. viewport 1366 768)")

        elif cmd == "screenshot":
            name = args[0] if args else None
            session.screenshot(name)

        elif cmd == "back":
            session.go_back()

        elif cmd == "forward":
            session.go_forward()

        elif cmd == "reload":
            session.reload()

        elif cmd == "wait":
            if not args:
                print("Usage: wait <seconds>")
            else:
                session.wait(float(args[0]))

        elif cmd == "info":
            session.current_info()

        else:
            print(f"❓ Unknown command: '{cmd}'. Type 'help' to see all commands.")

    except PlaywrightTimeoutError:
        print("⏱️  Action timed out. The page may not have loaded, or the element may be unreachable.")
    except ValueError as e:
        print(f"❌ Invalid argument: {e}")
    except Exception as e:
        print(f"❌ Error running command: {e}")
        traceback.print_exc()

    return True


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main():
    print("=" * 64)
    print(" 🎮 Opera GX Browser Automation CLI (Playwright)")
    print("=" * 64)

    opera_path = find_opera_gx_path()

    if not opera_path:
        print()
        print("❌ Could not auto-detect Opera GX on this system.")
        print(f"   (Detected OS: {platform.system()})")
        print()
        manual_path = input(
            "👉 Please paste the full path to your Opera GX executable\n"
            "   (or press Enter to cancel): "
        ).strip().strip('"')
        if not manual_path:
            print("No path provided. Exiting.")
            sys.exit(1)
        if not os.path.isfile(manual_path):
            print(f"❌ That path does not exist: {manual_path}")
            sys.exit(1)
        opera_path = manual_path
    else:
        print(f"✅ Found Opera GX at: {opera_path}")

    print()
    print(HELP_TEXT)

    session = OperaGXSession(executable_path=opera_path, headless=False)
    try:
        session.start()
    except Exception as e:
        print(f"❌ Failed to start Opera GX: {e}")
        print()
        print("Common fixes:")
        print("  - Make sure Opera GX is fully closed before running this script")
        print("    (Playwright launches its own instance and may conflict with")
        print("    an already-running one using the same profile).")
        print("  - Double-check the executable path is correct.")
        print("  - On Windows, try the 'launcher.exe' path rather than 'opera.exe'")
        print("    if one doesn't work.")
        sys.exit(1)

    try:
        while True:
            try:
                line = input("\n🎮 opera-gx> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Exiting...")
                break

            keep_going = parse_and_run(session, line)
            if not keep_going:
                print("👋 Closing Opera GX...")
                break
    finally:
        session.stop()
        print("✅ Done. Goodbye!")


if __name__ == "__main__":
    main()