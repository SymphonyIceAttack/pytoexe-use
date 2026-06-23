import tkinter as tk
from tkinter import messagebox
import time

class TypingTest:
    def __init__(self, master):
        self.master = master
        self.master.title("Тест скорости печати")
        self.text_to_type = ""
        self.start_time = None
        self.end_time = None
        self.timer_running = False

        