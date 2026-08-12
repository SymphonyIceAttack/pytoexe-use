#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AVIATOR PREDICTOR v2.0
Simple & Smart - OVER/UNDER 2x Predictor
User enters results, AI learns and predicts.
"""

import tkinter as tk
from tkinter import messagebox, font
import json
import os
from datetime import datetime
from collections import Counter

# ============================================================
# SMART ANALYZER ENGINE
# ============================================================

class SmartAnalyzer:
    """Lightweight but smart pattern analyzer"""

    def __init__(self):
        self.history = []  # List of 'OVER' or 'UNDER'
        self.predictions = []  # List of (predicted, actual, correct)
        self.accuracy = 0.0
        self.total_predictions = 0
        self.correct_predictions = 0

    def add_result(self, result):
        """Add actual result: 'OVER' or 'UNDER'"""
        self.history.append(result)

    def add_prediction_result(self, predicted, actual):
        """Record prediction vs actual"""
        correct = (predicted == actual)
        self.predictions.append({
            'predicted': predicted,
            'actual': actual,
            'correct': correct,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        self.total_predictions += 1
        if correct:
            self.correct_predictions += 1
        self.accuracy = (self.correct_predictions / self.total_predictions) * 100

    def predict(self):
        """Smart prediction based on multiple signals"""
        n = len(self.history)
        if n < 10:
            return None, 0, "Need 10 rounds"

        last_10 = self.history[-10:]
        last_20 = self.history[-20:] if n >= 20 else last_10
        last_5 = self.history[-5:]

        signals = {'OVER': 0.0, 'UNDER': 0.0}

        # Signal 1: Markov Chain (last state transition)
        if n >= 2:
            last = self.history[-1]
            transitions = Counter()
            for i in range(n - 1):
                if self.history[i] == last:
                    transitions[self.history[i+1]] += 1
            total = sum(transitions.values())
            if total > 0:
                for outcome in ['OVER', 'UNDER']:
                    signals[outcome] += (transitions[outcome] / total) * 0.25

        # Signal 2: Streak Analysis (mean reversion vs continuation)
        streak = 1
        for i in range(n-2, -1, -1):
            if self.history[i] == self.history[-1]:
                streak += 1
            else:
                break

        if streak >= 3:
            # Mean reversion: long streak suggests opposite next
            opposite = 'UNDER' if self.history[-1] == 'OVER' else 'OVER'
            signals[opposite] += 0.20
        elif streak == 2:
            # Continuation slightly favored
            signals[self.history[-1]] += 0.15
        else:
            # Single, check previous pattern
            signals[self.history[-1]] += 0.10

        # Signal 3: Frequency Balance (regression to mean)
        over_count_10 = last_10.count('OVER')
        under_count_10 = last_10.count('UNDER')

        if over_count_10 >= 7:
            signals['UNDER'] += 0.15  # Too many OVER, expect UNDER
        elif under_count_10 >= 7:
            signals['OVER'] += 0.15   # Too many UNDER, expect OVER
        elif over_count_10 > under_count_10:
            signals['UNDER'] += 0.08
        elif under_count_10 > over_count_10:
            signals['OVER'] += 0.08

        # Signal 4: Pattern Matching (last 3 sequence)
        if n >= 13:
            last3 = tuple(self.history[-3:])
            next_counts = Counter()
            for i in range(n - 3):
                if tuple(self.history[i:i+3]) == last3:
                    next_counts[self.history[i+3]] += 1
            total_pat = sum(next_counts.values())
            if total_pat >= 2:
                for outcome in ['OVER', 'UNDER']:
                    signals[outcome] += (next_counts[outcome] / total_pat) * 0.20

        # Signal 5: Recent momentum (last 5)
        over_5 = last_5.count('OVER')
        under_5 = last_5.count('UNDER')
        if over_5 >= 4:
            signals['UNDER'] += 0.10
        elif under_5 >= 4:
            signals['OVER'] += 0.10

        # Signal 6: Historical accuracy feedback (learning from mistakes)
        if self.total_predictions >= 5:
            # Check if there's a bias in wrong predictions
            wrong_over = sum(1 for p in self.predictions if not p['correct'] and p['predicted'] == 'OVER')
            wrong_under = sum(1 for p in self.predictions if not p['correct'] and p['predicted'] == 'UNDER')
            if wrong_over > wrong_under * 1.5:
                signals['UNDER'] += 0.05  # We over-predict OVER, favor UNDER
            elif wrong_under > wrong_over * 1.5:
                signals['OVER'] += 0.05

        # Normalize and decide
        total_signal = signals['OVER'] + signals['UNDER']
        if total_signal == 0:
            prediction = 'OVER'
            confidence = 50.0
        else:
            over_prob = signals['OVER'] / total_signal
            under_prob = signals['UNDER'] / total_signal
            prediction = 'OVER' if over_prob > under_prob else 'UNDER'
            confidence = max(over_prob, under_prob) * 100

        # Risk level
        if confidence >= 60:
            risk = "LOW"
        elif confidence >= 52:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        # Reasoning
        reasons = []
        if streak >= 3:
            reasons.append(f"Streak of {streak} {self.history[-1]} → mean reversion")
        if over_count_10 >= 7 or under_count_10 >= 7:
            reasons.append("Frequency imbalance → regression")

        reasoning = " | ".join(reasons) if reasons else "Mixed signals"

        return prediction, confidence, risk, reasoning

    def get_stats(self):
        """Get current statistics"""
        n = len(self.history)
        if n == 0:
            return {"rounds": 0, "over": 0, "under": 0, "accuracy": 0, "predictions": 0}

        over_count = self.history.count('OVER')
        under_count = self.history.count('UNDER')

        return {
            "rounds": n,
            "over": over_count,
            "under": under_count,
            "over_pct": round(over_count / n * 100, 1),
            "under_pct": round(under_count / n * 100, 1),
            "accuracy": round(self.accuracy, 1),
            "predictions": self.total_predictions,
            "correct": self.correct_predictions,
            "wrong": self.total_predictions - self.correct_predictions
        }

    def save(self, filename="aviator_data.json"):
        """Save data to file"""
        data = {
            'history': self.history,
            'predictions': self.predictions,
            'accuracy': self.accuracy,
            'total': self.total_predictions,
            'correct': self.correct_predictions
        }
        with open(filename, 'w') as f:
            json.dump(data, f)

    def load(self, filename="aviator_data.json"):
        """Load data from file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            self.history = data.get('history', [])
            self.predictions = data.get('predictions', [])
            self.accuracy = data.get('accuracy', 0)
            self.total_predictions = data.get('total', 0)
            self.correct_predictions = data.get('correct', 0)


# ============================================================
# GUI APPLICATION
# ============================================================

class AviatorPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AVIATOR PREDICTOR v2.0")
        self.root.geometry("600x800")
        self.root.configure(bg='#0d0d0d')
        self.root.resizable(False, False)

        self.analyzer = SmartAnalyzer()
        self.analyzer.load()
        self.current_prediction = None

        # Colors
        self.BG = '#0d0d0d'
        self.OVER_COLOR = '#00ff88'
        self.UNDER_COLOR = '#ff3366'
        self.TEXT_COLOR = '#ffffff'
        self.GRAY = '#888888'
        self.DARK_GRAY = '#1a1a1a'

        self.setup_fonts()
        self.create_widgets()
        self.refresh_display()

    def setup_fonts(self):
        self.font_title = font.Font(family="Segoe UI", size=18, weight="bold")
        self.font_big = font.Font(family="Segoe UI", size=36, weight="bold")
        self.font_medium = font.Font(family="Segoe UI", size=16, weight="bold")
        self.font_normal = font.Font(family="Segoe UI", size=12)
        self.font_small = font.Font(family="Segoe UI", size=10)

    def create_widgets(self):
        # Main frame
        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # ===== TITLE =====
        title = tk.Label(main, text="⚡ AVIATOR PREDICTOR", 
                        font=self.font_title, bg=self.BG, fg=self.TEXT_COLOR)
        title.pack(pady=(0, 5))

        subtitle = tk.Label(main, text="Enter results → AI learns → Predicts", 
                           font=self.font_small, bg=self.BG, fg=self.GRAY)
        subtitle.pack(pady=(0, 15))

        # ===== HISTORY DISPLAY (Last 10) =====
        hist_frame = tk.Frame(main, bg=self.DARK_GRAY, bd=2, relief=tk.RIDGE)
        hist_frame.pack(fill=tk.X, pady=10, ipady=10)

        tk.Label(hist_frame, text="📊 HISTORY (Last 10)", 
                font=self.font_normal, bg=self.DARK_GRAY, fg=self.GRAY).pack()

        self.history_labels = []
        hist_row = tk.Frame(hist_frame, bg=self.DARK_GRAY)
        hist_row.pack(pady=5)

        for i in range(10):
            lbl = tk.Label(hist_row, text="—", font=self.font_medium,
                          bg=self.DARK_GRAY, fg=self.GRAY, width=4)
            lbl.pack(side=tk.LEFT, padx=2)
            self.history_labels.append(lbl)

        # ===== PREDICTION DISPLAY =====
        pred_frame = tk.Frame(main, bg=self.DARK_GRAY, bd=3, relief=tk.RIDGE)
        pred_frame.pack(fill=tk.X, pady=15, ipady=20)

        tk.Label(pred_frame, text="🔮 PREDICTION", 
                font=self.font_normal, bg=self.DARK_GRAY, fg=self.GRAY).pack()

        self.pred_label = tk.Label(pred_frame, text="WAITING...", 
                                  font=self.font_big, bg=self.DARK_GRAY, fg=self.GRAY)
        self.pred_label.pack(pady=5)

        self.conf_label = tk.Label(pred_frame, text="Enter 10 rounds first", 
                                  font=self.font_normal, bg=self.DARK_GRAY, fg=self.GRAY)
        self.conf_label.pack()

        self.reason_label = tk.Label(pred_frame, text="", 
                                    font=self.font_small, bg=self.DARK_GRAY, fg=self.GRAY,
                                    wraplength=500)
        self.reason_label.pack(pady=(5, 0))

        # ===== ACTION BUTTONS =====
        btn_frame = tk.Frame(main, bg=self.BG)
        btn_frame.pack(fill=tk.X, pady=20)

        self.over_btn = tk.Button(btn_frame, text="▲ OVER 2x", 
                                 font=self.font_medium,
                                 bg=self.OVER_COLOR, fg='#000000',
                                 activebackground='#00cc6a',
                                 width=12, height=3,
                                 cursor='hand2',
                                 command=lambda: self.on_result('OVER'))
        self.over_btn.pack(side=tk.LEFT, expand=True, padx=10)

        self.under_btn = tk.Button(btn_frame, text="▼ UNDER 2x", 
                                  font=self.font_medium,
                                  bg=self.UNDER_COLOR, fg='#ffffff',
                                  activebackground='#cc2952',
                                  width=12, height=3,
                                  cursor='hand2',
                                  command=lambda: self.on_result('UNDER'))
        self.under_btn.pack(side=tk.RIGHT, expand=True, padx=10)

        # ===== INSTRUCTIONS =====
        instr = tk.Label(main, 
                        text="After prediction appears, click the ACTUAL result
"
                             "Green = OVER 2x | Red = UNDER 2x",
                        font=self.font_small, bg=self.BG, fg=self.GRAY)
        instr.pack(pady=10)

        # ===== STATS =====
        stats_frame = tk.Frame(main, bg=self.DARK_GRAY, bd=2, relief=tk.RIDGE)
        stats_frame.pack(fill=tk.X, pady=10, ipady=10)

        tk.Label(stats_frame, text="📈 STATISTICS", 
                font=self.font_normal, bg=self.DARK_GRAY, fg=self.GRAY).pack()

        self.stats_label = tk.Label(stats_frame, text="Rounds: 0 | Accuracy: —", 
                                   font=self.font_normal, bg=self.DARK_GRAY, fg=self.TEXT_COLOR)
        self.stats_label.pack(pady=5)

        # ===== BOTTOM BUTTONS =====
        bottom = tk.Frame(main, bg=self.BG)
        bottom.pack(fill=tk.X, pady=10)

        tk.Button(bottom, text="🗑️ Clear All", font=self.font_small,
                 bg='#333333', fg=self.TEXT_COLOR,
                 command=self.clear_all).pack(side=tk.LEFT, padx=5)

        tk.Button(bottom, text="💾 Save", font=self.font_small,
                 bg='#333333', fg=self.TEXT_COLOR,
                 command=self.save_data).pack(side=tk.LEFT, padx=5)

        tk.Button(bottom, text="📂 Load", font=self.font_small,
                 bg='#333333', fg=self.TEXT_COLOR,
                 command=self.load_data).pack(side=tk.LEFT, padx=5)

        tk.Button(bottom, text="↩️ Undo", font=self.font_small,
                 bg='#333333', fg=self.TEXT_COLOR,
                 command=self.undo).pack(side=tk.RIGHT, padx=5)

    def on_result(self, result):
        """Handle result button click"""
        n = len(self.analyzer.history)

        if n >= 10 and self.current_prediction is not None:
            # This is the ACTUAL result after a prediction
            self.analyzer.add_prediction_result(self.current_prediction, result)
            self.analyzer.add_result(result)

            # Show feedback
            correct = (self.current_prediction == result)
            feedback = "✅ CORRECT!" if correct else "❌ WRONG"
            color = self.OVER_COLOR if correct else self.UNDER_COLOR

            self.pred_label.config(text=feedback, fg=color)
            self.conf_label.config(text=f"Prediction was: {self.current_prediction} | Actual: {result}")
            self.reason_label.config(text="")

            self.root.after(1500, self.refresh_after_feedback)
        else:
            # Just adding to history (building up to 10)
            self.analyzer.add_result(result)
            self.refresh_display()

    def refresh_after_feedback(self):
        """Refresh after showing feedback"""
        self.current_prediction = None
        self.refresh_display()

    def refresh_display(self):
        """Update all display elements"""
        n = len(self.analyzer.history)

        # Update history display
        last_10 = self.analyzer.history[-10:] if n >= 10 else self.analyzer.history
        for i in range(10):
            if i < len(last_10):
                val = last_10[i]
                color = self.OVER_COLOR if val == 'OVER' else self.UNDER_COLOR
                self.history_labels[i].config(text="▲" if val == 'OVER' else "▼", fg=color)
            else:
                self.history_labels[i].config(text="—", fg=self.GRAY)

        # Update stats
        stats = self.analyzer.get_stats()
        self.stats_label.config(
            text=f"Rounds: {stats['rounds']} | "
                 f"OVER: {stats['over']} ({stats['over_pct']}%) | "
                 f"UNDER: {stats['under']} ({stats['under_pct']}%) | "
                 f"Accuracy: {stats['accuracy']}% ({stats['correct']}/{stats['predictions']})"
        )

        # Generate prediction if we have 10+ rounds
        if n >= 10:
            pred_data = self.analyzer.predict()
            if pred_data[0] is not None:
                prediction, confidence, risk, reasoning = pred_data
                self.current_prediction = prediction

                color = self.OVER_COLOR if prediction == 'OVER' else self.UNDER_COLOR
                self.pred_label.config(text=f"{prediction} 2x", fg=color)
                self.conf_label.config(text=f"Confidence: {confidence:.0f}% | Risk: {risk}")
                self.reason_label.config(text=f"Reason: {reasoning}")

                # Highlight which button to bet on
                if prediction == 'OVER':
                    self.over_btn.config(bg='#00ff88', text="▲ BET HERE")
                    self.under_btn.config(bg='#444444', text="▼ SKIP")
                else:
                    self.under_btn.config(bg='#ff3366', text="▼ SKIP")
                    self.over_btn.config(bg='#444444', text="▲ SKIP")
            else:
                self.current_prediction = None
                self.pred_label.config(text="WAITING...", fg=self.GRAY)
                self.conf_label.config(text=pred_data[2])
                self.reason_label.config(text="")
                self.reset_buttons()
        else:
            self.current_prediction = None
            self.pred_label.config(text="WAITING...", fg=self.GRAY)
            self.conf_label.config(text=f"Enter {10 - n} more round(s)...")
            self.reason_label.config(text="")
            self.reset_buttons()

    def reset_buttons(self):
        self.over_btn.config(bg=self.OVER_COLOR, text="▲ OVER 2x")
        self.under_btn.config(bg=self.UNDER_COLOR, text="▼ UNDER 2x")

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Clear all history?"):
            self.analyzer = SmartAnalyzer()
            self.current_prediction = None
            self.refresh_display()

    def save_data(self):
        self.analyzer.save()
        messagebox.showinfo("Saved", "Data saved to aviator_data.json")

    def load_data(self):
        self.analyzer.load()
        self.current_prediction = None
        self.refresh_display()
        messagebox.showinfo("Loaded", "Data loaded from aviator_data.json")

    def undo(self):
        if self.analyzer.history:
            self.analyzer.history.pop()
            self.current_prediction = None
            self.refresh_display()


def main():
    root = tk.Tk()
    app = AviatorPredictorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
