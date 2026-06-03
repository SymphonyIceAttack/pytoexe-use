import tkinter as tk
from tkinter import ttk, messagebox

class FootballPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор футбольных прогнозов (Мульти-матч)")
        self.root.geometry("800x600")

        self.matches = []  