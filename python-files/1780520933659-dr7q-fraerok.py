import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class FootballPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система прогнозов футбольных матчей")
        self.root.geometry("600x500")

        