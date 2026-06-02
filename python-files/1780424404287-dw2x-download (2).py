import tkinter as tk
from tkinter import ttk, messagebox
import time
import random

class OrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Органайзер и Тест Печати")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        