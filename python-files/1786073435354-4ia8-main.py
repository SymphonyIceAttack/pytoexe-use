# -*- coding: utf-8 -*-
"""
Fastener Generator v12 — main entry point.
Launches the Tkinter GUI application.
"""

import tkinter as tk
from tkinter import ttk

from fastener_gen.app import BoltGeneratorApp


def main() -> None:
    root = tk.Tk()

    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass

    app = BoltGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
