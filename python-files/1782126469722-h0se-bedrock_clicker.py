"""
=============================================================================
  Bedrock Clicker Engine  –  Production-Ready Minecraft Auto-Clicker
=============================================================================
  Architecture
  ─────────────────────────────────────────────────────────────────────────
  • Main thread   → CustomTkinter GUI (always responsive, never blocked)
  • Daemon thread → ClickerEngine loop (low-latency click dispatch)

  Requirements (install once):
      pip install customtkinter pywin32 keyboard

  Compatibility: Windows 10 / 11  •  Python 3.10+
=============================================================================
"""

# ── Standard Library ───────────────────────────────────────────────────────
import threading
import random
import time

# ── Third-Party ────────────────────────────────────────────────────────────
try:
    import customtkinter as ctk
    import win32api
    import win32gui
    import win32con
    import keyboard
except ImportError as exc:
    raise SystemExit(
        f"\n[Import Error] Missing dependency: {exc}\n"
        "Run:  pip install customtkinter pywin32 keyboard\n"
    ) from exc


# ══════════════════════════════════════════════════════════════════════════
#  CONSTANTS & DEFAULTS
# ══════════════════════════════════════════════════════════════════════════

APP_TITLE       = "Bedrock Clicker Engine"
APP_VERSION     = "v2.4"
WIN_W, WIN_H    = 445, 600              # Fixed window size (pixels)

# CPS defaults – the engine will randomise within [min, max] each click
DEFAULT_MIN_CPS = 10
DEFAULT_MAX_CPS = 14

# Global hotkeys
DEFAULT_TOGGLE  = "F4"                  # Flip active state
DEFAULT_SUSPEND = "c"                   # Hold-to-pause (e.g. block placing)

# Active window title check (case-sensitive substring)
MC_TITLE_HINT   = "Minecraft"

# Click hold duration range (seconds): simulates finger press variation
CLICK_HOLD_MIN  = 0.010                 # 10 ms
CLICK_HOLD_MAX  = 0.040                 # 40 ms

# Idle poll interval while conditions are not met (keeps CPU near 0 %)
IDLE_POLL_S     = 0.005                 # 5 ms → 200 checks/second

# Hand jitter: max pixel deviation in any direction
JITTER_MAX_PX   = 2


# ══════════════════════════════════════════════════════════════════════════
#  CLICKER ENGINE  ─  pure logic, zero GUI knowledge
# ══════════════════════════════════════════════════════════════════════════

class ClickerEngine:
    """
    Encapsulates all click dispatch logic and condition guards.

    The GUI thread sets public attributes (active, min_cps, …) and the
    daemon thread reads them.  Python's GIL makes simple attribute
    reads/writes on CPython inherently thread-safe without explicit locks.
    """

    def __init__(self) -> None:
        # ── State flags (written by GUI, read by daemon) ──────────────────
        self.active:          bool  = False   # Master on/off switch
        self.suspended:       bool  = False   # True while suspend key held
        self.jitter_enabled:  bool  = False   # Micro-movement emulation
        self.avoid_gui:       bool  = True    # Halt when cursor is visible

        # ── Mutable settings (updated from GUI callbacks) ─────────────────
        self.min_cps:    float = float(DEFAULT_MIN_CPS)
        self.max_cps:    float = float(DEFAULT_MAX_CPS)
        self.toggle_key: str   = DEFAULT_TOGGLE
        self.suspend_key:str   = DEFAULT_SUSPEND

    # ── Condition guards ──────────────────────────────────────────────────

    def _minecraft_focused(self) -> bool:
        """
        Returns True only when the Win32 foreground window title contains
        the Minecraft hint string.

        Wrapped in try/except so that rapid Alt-Tab / window changes never
        cause an unhandled exception in the daemon thread.
        """
        try:
            hwnd  = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            return MC_TITLE_HINT in title
        except Exception:
            return False   # Fail-safe: don't click during uncertainty

    def _cursor_is_visible(self) -> bool:
        """
        Queries the Win32 cursor visibility flag via GetCursorInfo().

        Returned flags:
            0  → cursor hidden   → player is in first-person gameplay
            1  → cursor visible  → inventory / chat / pause / desktop

        When avoid_gui is enabled, a visible cursor acts as a hard stop,
        preventing both accidental GUI misclicks and unnecessary activity
        while menus are open.

        Falls back to True (conservative) on any API error.
        """
        try:
            flags, _hcursor, _pos = win32gui.GetCursorInfo()
            return flags != 0
        except Exception:
            return True    # Fail-safe: assume visible, skip click

    def _suspend_key_held(self) -> bool:
        """Polls the suspend key; silently swallows all keyboard-lib errors."""
        try:
            return keyboard.is_pressed(self.suspend_key)
        except Exception:
            return False

    # ── Click dispatcher ──────────────────────────────────────────────────

    def _fire_click(self) -> None:
        """
        Dispatches one left mouse click via win32api.mouse_event.

        Humanisation steps (when enabled):
          1. Capture current cursor position.
          2. Apply a ±JITTER_MAX_PX random offset to X and Y (MOUSEDOWN).
          3. Hold for a random duration [CLICK_HOLD_MIN, CLICK_HOLD_MAX].
          4. Release (MOUSEUP) then restore the original position.

        The restore step ensures that over many clicks the drift stays
        imperceptible to the player while still producing natural micro-
        variation in click coordinates.

        All win32 calls are inside try/except – momentary failures during
        focus changes or window minimisation are silently ignored.
        """
        try:
            saved_pos = None

            if self.jitter_enabled:
                ox, oy    = win32api.GetCursorPos()
                saved_pos = (ox, oy)
                jx = ox + random.randint(-JITTER_MAX_PX, JITTER_MAX_PX)
                jy = oy + random.randint(-JITTER_MAX_PX, JITTER_MAX_PX)
                win32api.SetCursorPos((jx, jy))

            # Simulate left button press + hold + release
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(CLICK_HOLD_MIN, CLICK_HOLD_MAX))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,   0, 0, 0, 0)

            # Restore original position after jitter release
            if self.jitter_enabled and saved_pos is not None:
                win32api.SetCursorPos(saved_pos)

        except Exception:
            pass   # Ignore transient win32 errors (focus changes, etc.)

    # ── Main daemon loop ──────────────────────────────────────────────────

    def run_forever(self) -> None:
        """
        Infinite loop – intended as the target of a daemon thread.

        Per-iteration decision tree:
            1. Is the master switch active?
            2. Is the suspend key currently held?
            3. Is Minecraft the foreground window?
            4. Is the cursor hidden (avoid_gui guard)?
            ── All conditions pass → fire click ──
            5. Compute dynamic sleep:  delay = 1 / random.uniform(min, max)
               so every click interval is independently randomised within
               the user-configured CPS band.
        """
        while True:
            # Update suspend flag every iteration (cheap key poll)
            self.suspended = self._suspend_key_held()

            all_clear = (
                self.active
                and not self.suspended
                and self._minecraft_focused()
                and not (self.avoid_gui and self._cursor_is_visible())
            )

            if all_clear:
                self._fire_click()

                # ── Dynamic CPS randomisation ────────────────────────────
                # Picking a fresh CPS value each iteration means the inter-
                # click delay fluctuates continuously, unlike a fixed timer.
                cps_now = random.uniform(self.min_cps, self.max_cps)
                time.sleep(1.0 / cps_now)
            else:
                # Idle: minimal CPU usage while waiting for conditions
                time.sleep(IDLE_POLL_S)


# ══════════════════════════════════════════════════════════════════════════
#  GUI APPLICATION  ─  CustomTkinter, runs on the main thread
# ══════════════════════════════════════════════════════════════════════════

class BedrockClickerApp(ctk.CTk):
    """
    Dark-themed, fixed-size window that exposes every engine parameter
    through sliders, dropdowns, and checkboxes.

    Layout (top → bottom):
        ┌─ Header bar: title  +  live status badge ─┐
        │  Master toggle button                      │
        │  CPS range sliders (Min / Max)             │
        │  Keybind selectors (Toggle / Suspend)      │
        │  Feature checkboxes (Jitter / Avoid GUI)   │
        └─ Info footer                              ─┘
    """

    # ── Colour palette ─────────────────────────────────────────────────────
    C = {
        "bg":        "#0f0f1a",   # Window background
        "panel":     "#1a1a2e",   # Card panels
        "btn_on":    "#5c0000",   # Disable-button red
        "btn_off":   "#1e3a5f",   # Enable-button blue
        "btn_on_hov":"#3b0000",
        "btn_off_hov":"#0f2840",
        "green":     "#00ff88",   # ACTIVE badge
        "red":       "#ff4444",   # DISABLED badge
        "orange":    "#ff9900",   # SUSPENDED badge
        "text":      "#e0e0e0",   # Primary text
        "muted":     "#666688",   # Subdued text
        "slider":    "#4a9eff",   # Slider accent
        "check":     "#00ff88",   # Checkbox tick
    }

    def __init__(self) -> None:
        super().__init__()

        self.engine = ClickerEngine()

        # ── CustomTkinter global config ───────────────────────────────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── Window config ─────────────────────────────────────────────────
        self.title(f"{APP_TITLE}  {APP_VERSION}")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.configure(fg_color=self.C["bg"])
        self.attributes("-topmost", True)   # Always above Minecraft window
        self.attributes("-alpha",   0.97)   # Slight transparency (aesthetic)

        # ── Build UI then wire up backend ─────────────────────────────────
        self._build_ui()
        self._register_hotkey(self.engine.toggle_key)
        self._start_engine_thread()
        self._status_tick()   # Begin 100 ms UI refresh loop

    # ─────────────────────────────────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Creates and packs every widget in the window."""

        # ── 1. Header ─────────────────────────────────────────────────────
        hdr = self._card()
        hdr.pack(fill="x", padx=14, pady=(14, 6))

        ctk.CTkLabel(
            hdr, text="⚡  Bedrock Clicker Engine",
            font=ctk.CTkFont("Segoe UI", 17, "bold"),
            text_color=self.C["text"]
        ).pack(side="left", padx=14, pady=12)

        self.status_badge = ctk.CTkLabel(
            hdr, text="● DISABLED",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=self.C["red"]
        )
        self.status_badge.pack(side="right", padx=14, pady=12)

        # ── 2. Master toggle button ────────────────────────────────────────
        btn_card = self._card()
        btn_card.pack(fill="x", padx=14, pady=6)

        self.toggle_btn = ctk.CTkButton(
            btn_card,
            text="▶   ENABLE CLICKER",
            height=48,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=self.C["btn_off"],
            hover_color=self.C["btn_off_hov"],
            corner_radius=8,
            command=self._gui_toggle
        )
        self.toggle_btn.pack(fill="x", padx=12, pady=12)

        # ── 3. CPS sliders ────────────────────────────────────────────────
        cps_card = self._card()
        cps_card.pack(fill="x", padx=14, pady=6)

        self._section_label(cps_card, "🖱   Click Rate  (CPS)")
        self._separator(cps_card)

        # Min CPS — slider range 5–15, default 10
        self._slider_row(
            parent   = cps_card,
            label    = "Min  CPS",
            from_    = 5,
            to       = 15,
            default  = DEFAULT_MIN_CPS,
            steps    = 10,
            callback = self._on_min_cps,
        )

        # Max CPS — slider range 8–25, default 14
        self._slider_row(
            parent      = cps_card,
            label       = "Max  CPS",
            from_       = 8,
            to          = 25,
            default     = DEFAULT_MAX_CPS,
            steps       = 17,
            callback    = self._on_max_cps,
            bottom_pad  = 12,
        )

        # ── 4. Keybind selectors ──────────────────────────────────────────
        key_card = self._card()
        key_card.pack(fill="x", padx=14, pady=6)

        self._section_label(key_card, "⌨   Keybinds")
        self._separator(key_card)

        self._keybind_row(
            parent   = key_card,
            label    = "Toggle Key",
            values   = ["F1","F2","F3","F4","F5","F6","F7","F8",
                        "INSERT","HOME","END","PAGE UP"],
            default  = DEFAULT_TOGGLE,
            callback = self._on_toggle_key,
        )
        self._keybind_row(
            parent      = key_card,
            label       = "Suspend Key",
            values      = ["c","v","b","x","z","g","h",
                           "left shift","left ctrl","left alt"],
            default     = DEFAULT_SUSPEND,
            callback    = self._on_suspend_key,
            bottom_pad  = 12,
        )

        # ── 5. Feature checkboxes ──────────────────────────────────────────
        feat_card = self._card()
        feat_card.pack(fill="x", padx=14, pady=6)

        self._section_label(feat_card, "✦   Humanization")
        self._separator(feat_card)

        self.jitter_var    = ctk.BooleanVar(value=False)
        self.avoid_gui_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            feat_card,
            text="Enable Hand Jitter  (±1–2 px micro-movement per click)",
            variable=self.jitter_var,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=self.C["text"],
            checkmark_color=self.C["check"],
            command=self._on_jitter
        ).pack(anchor="w", padx=14, pady=(6, 4))

        ctk.CTkCheckBox(
            feat_card,
            text="Avoid Inventory / GUI Clicking",
            variable=self.avoid_gui_var,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=self.C["text"],
            checkmark_color=self.C["check"],
            command=self._on_avoid_gui
        ).pack(anchor="w", padx=14, pady=(4, 14))

        # Pre-select the default "avoid GUI" option
        self.avoid_gui_var.set(True)

        # ── 6. Info footer ─────────────────────────────────────────────────
        foot = ctk.CTkFrame(self, fg_color=self.C["panel"], corner_radius=10)
        foot.pack(fill="x", padx=14, pady=(4, 14))

        info_text = (
            f"ℹ  Clicks only while Minecraft is the foreground window\n"
            f"    Hold  [{DEFAULT_SUSPEND.upper()}]  to suspend  •  "
            f"[{DEFAULT_TOGGLE}]  to toggle on / off"
        )
        ctk.CTkLabel(
            foot, text=info_text,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=self.C["muted"],
            justify="left"
        ).pack(padx=14, pady=10, anchor="w")

    # ─────────────────────────────────────────────────────────────────────
    #  WIDGET FACTORY HELPERS  (keep _build_ui readable)
    # ─────────────────────────────────────────────────────────────────────

    def _card(self) -> ctk.CTkFrame:
        """Returns a styled panel frame (card)."""
        return ctk.CTkFrame(self, fg_color=self.C["panel"], corner_radius=10)

    def _section_label(self, parent: ctk.CTkFrame, text: str) -> None:
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=self.C["text"]
        ).pack(anchor="w", padx=14, pady=(12, 2))

    def _separator(self, parent: ctk.CTkFrame) -> None:
        """Thin horizontal line divider under section labels."""
        ctk.CTkFrame(
            parent, height=1, fg_color="#2a2a4e", corner_radius=0
        ).pack(fill="x", padx=12, pady=(2, 4))

    def _slider_row(
        self, parent: ctk.CTkFrame,
        label: str, from_: float, to: float,
        default: float, steps: int,
        callback,
        bottom_pad: int = 4,
    ) -> None:
        """
        Builds one [label ── slider ── value] row inside a card.
        The value label is stored on `self` so the callback can update it.
        """
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(4, bottom_pad))

        ctk.CTkLabel(
            row, text=label, width=72,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=self.C["text"]
        ).pack(side="left")

        # Numeric readout (right side, updated by callback)
        val_lbl = ctk.CTkLabel(
            row, text=str(int(default)), width=28,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=self.C["slider"]
        )
        val_lbl.pack(side="right")

        ctk.CTkSlider(
            row, from_=from_, to=to,
            number_of_steps=steps,
            progress_color=self.C["slider"],
            button_color=self.C["slider"],
            button_hover_color="#78bfff",
            command=lambda v, lbl=val_lbl: callback(v, lbl)
        ).set(default)  # Note: pack() called on the slider object next

        # Retrieve the last widget added to the row and pack it
        # (ctk sliders don't chain .pack() directly after .set())
        for widget in row.winfo_children():
            if isinstance(widget, ctk.CTkSlider):
                widget.pack(side="left", fill="x", expand=True, padx=(8, 8))

    def _keybind_row(
        self, parent: ctk.CTkFrame,
        label: str, values: list, default: str,
        callback,
        bottom_pad: int = 4,
    ) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(4, bottom_pad))

        ctk.CTkLabel(
            row, text=label, width=90,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=self.C["text"]
        ).pack(side="left")

        menu = ctk.CTkOptionMenu(
            row, values=values,
            font=ctk.CTkFont("Segoe UI", 12),
            width=130, height=30,
            command=callback
        )
        menu.set(default)
        menu.pack(side="right")

    # ─────────────────────────────────────────────────────────────────────
    #  GUI EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────

    def _gui_toggle(self) -> None:
        """Called by the toggle button click; flips engine active state."""
        self.engine.active = not self.engine.active
        self._apply_toggle_visuals()

    def _apply_toggle_visuals(self) -> None:
        """
        Syncs the toggle button's colour + text with engine.active.
        Safe to call from any thread (Tkinter after() handles it from
        hotkey callbacks; direct call is fine from the main thread).
        """
        if self.engine.active:
            self.toggle_btn.configure(
                text="■   DISABLE CLICKER",
                fg_color=self.C["btn_on"],
                hover_color=self.C["btn_on_hov"]
            )
        else:
            self.toggle_btn.configure(
                text="▶   ENABLE CLICKER",
                fg_color=self.C["btn_off"],
                hover_color=self.C["btn_off_hov"]
            )

    # ── Slider callbacks ──────────────────────────────────────────────────

    def _on_min_cps(self, value: float, label: ctk.CTkLabel) -> None:
        """Clamps min so it never meets or exceeds max; updates engine + label."""
        v = int(value)
        if v >= int(self.engine.max_cps):
            v = max(5, int(self.engine.max_cps) - 1)
        self.engine.min_cps = float(v)
        label.configure(text=str(v))

    def _on_max_cps(self, value: float, label: ctk.CTkLabel) -> None:
        """Clamps max so it never meets or goes below min; updates engine + label."""
        v = int(value)
        if v <= int(self.engine.min_cps):
            v = min(25, int(self.engine.min_cps) + 1)
        self.engine.max_cps = float(v)
        label.configure(text=str(v))

    # ── Keybind callbacks ─────────────────────────────────────────────────

    def _on_toggle_key(self, new_key: str) -> None:
        """Removes the old global hotkey binding then registers the new one."""
        try:
            keyboard.remove_hotkey(self.engine.toggle_key)
        except Exception:
            pass   # Harmless if key was never registered
        self.engine.toggle_key = new_key
        self._register_hotkey(new_key)

    def _on_suspend_key(self, new_key: str) -> None:
        self.engine.suspend_key = new_key

    # ── Feature checkbox callbacks ────────────────────────────────────────

    def _on_jitter(self) -> None:
        self.engine.jitter_enabled = self.jitter_var.get()

    def _on_avoid_gui(self) -> None:
        self.engine.avoid_gui = self.avoid_gui_var.get()

    # ─────────────────────────────────────────────────────────────────────
    #  GLOBAL HOTKEY REGISTRATION
    # ─────────────────────────────────────────────────────────────────────

    def _register_hotkey(self, key: str) -> None:
        """
        Binds a system-wide hotkey using the keyboard library.
        suppress=False means the keypress still reaches Minecraft.
        """
        try:
            keyboard.add_hotkey(key, self._hotkey_fired, suppress=False)
        except Exception as exc:
            # Non-fatal – user can still click the button manually
            print(f"[Hotkey] Could not register '{key}': {exc}")

    def _hotkey_fired(self) -> None:
        """
        Invoked from the keyboard-lib listener thread (not the main thread).
        Flips engine state, then safely schedules the visual update via
        Tkinter's after() which is thread-safe.
        """
        self.engine.active = not self.engine.active
        self.after(0, self._apply_toggle_visuals)

    # ─────────────────────────────────────────────────────────────────────
    #  BACKGROUND ENGINE THREAD
    # ─────────────────────────────────────────────────────────────────────

    def _start_engine_thread(self) -> None:
        """
        Launches the clicker loop in a daemon thread.

        daemon=True → the thread is automatically killed when the main
        (GUI) thread exits, preventing zombie processes on window close.
        """
        t = threading.Thread(
            target=self.engine.run_forever,
            name="ClickerEngine",
            daemon=True
        )
        t.start()

    # ─────────────────────────────────────────────────────────────────────
    #  LIVE STATUS BADGE REFRESH  (100 ms interval)
    # ─────────────────────────────────────────────────────────────────────

    def _status_tick(self) -> None:
        """
        Runs on the Tkinter event loop every 100 ms via after().

        Reflects three distinct states in the header badge:
            DISABLED   → master switch is off                 [red]
            SUSPENDED  → active but suspend key is held       [orange]
            ACTIVE     → clicking freely                      [green]
        """
        if not self.engine.active:
            self.status_badge.configure(
                text="● DISABLED", text_color=self.C["red"]
            )
        elif self.engine.suspended:
            self.status_badge.configure(
                text="● SUSPENDED", text_color=self.C["orange"]
            )
        else:
            self.status_badge.configure(
                text="● ACTIVE", text_color=self.C["green"]
            )

        self.after(100, self._status_tick)   # Re-schedule next tick


# ══════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = BedrockClickerApp()
    app.mainloop()
