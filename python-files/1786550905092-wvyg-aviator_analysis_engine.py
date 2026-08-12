#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AVIATOR ANALYSIS ENGINE v1.0
Professional Analysis Tool for Aviator Crash Game
Features: Markov Chains, Entropy Analysis, Bayesian Updating, 
Kelly Criterion, Monte Carlo Simulation, Pattern Detection
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import random
import math
import statistics
import csv
import json
from datetime import datetime
from collections import Counter, defaultdict

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# ============================================================
# CORE ANALYSIS ENGINE
# ============================================================

class AviatorAnalyzer:
    """Core analysis engine for Aviator game data"""

    def __init__(self):
        self.history = []
        self.threshold = 2.0
        self.house_edge = 0.03  # 3% house edge

    def add_round(self, multiplier):
        """Add a new round result to history"""
        self.history.append(float(multiplier))

    def get_last_n(self, n=10):
        """Get last n rounds"""
        return self.history[-n:] if len(self.history) >= n else self.history

    def categorize(self, multiplier):
        """Categorize as OVER or UNDER threshold"""
        return "OVER" if multiplier >= self.threshold else "UNDER"

    def get_sequence(self, n=10):
        """Get sequence of OVER/UNDER for last n rounds"""
        rounds = self.get_last_n(n)
        return [self.categorize(m) for m in rounds]

    # ---------- STATISTICAL ANALYSIS ----------

    def basic_stats(self, n=10):
        """Calculate basic statistics"""
        rounds = self.get_last_n(n)
        if not rounds:
            return {}
        return {
            'count': len(rounds),
            'mean': statistics.mean(rounds),
            'median': statistics.median(rounds),
            'stdev': statistics.stdev(rounds) if len(rounds) > 1 else 0,
            'min': min(rounds),
            'max': max(rounds),
            'over_count': sum(1 for m in rounds if m >= self.threshold),
            'under_count': sum(1 for m in rounds if m < self.threshold),
            'over_pct': sum(1 for m in rounds if m >= self.threshold) / len(rounds) * 100
        }

    def theoretical_prob_over(self):
        """Theoretical probability of OVER 2x: P = (1 - house_edge) / 2 = 0.485"""
        return (1 - self.house_edge) / self.threshold

    # ---------- MARKOV CHAIN ANALYSIS ----------

    def markov_analysis(self, n=50):
        """Analyze state transitions using Markov Chains"""
        seq = self.get_sequence(n)
        if len(seq) < 3:
            return None

        transitions = {'OVER→OVER': 0, 'OVER→UNDER': 0, 
                       'UNDER→OVER': 0, 'UNDER→UNDER': 0}

        for i in range(len(seq) - 1):
            key = f"{seq[i]}→{seq[i+1]}"
            if key in transitions:
                transitions[key] += 1

        # Calculate transition probabilities
        over_total = transitions['OVER→OVER'] + transitions['OVER→UNDER']
        under_total = transitions['UNDER→OVER'] + transitions['UNDER→UNDER']

        result = {
            'transitions': transitions,
            'P(OVER|OVER)': transitions['OVER→OVER'] / over_total if over_total > 0 else 0.5,
            'P(UNDER|OVER)': transitions['OVER→UNDER'] / over_total if over_total > 0 else 0.5,
            'P(OVER|UNDER)': transitions['UNDER→OVER'] / under_total if under_total > 0 else 0.5,
            'P(UNDER|UNDER)': transitions['UNDER→UNDER'] / under_total if under_total > 0 else 0.5,
        }

        # Predict next based on last state
        last_state = seq[-1] if seq else 'OVER'
        if last_state == 'OVER':
            result['prediction'] = 'OVER' if result['P(OVER|OVER)'] > 0.5 else 'UNDER'
            result['confidence'] = max(result['P(OVER|OVER)'], result['P(UNDER|OVER)'])
        else:
            result['prediction'] = 'OVER' if result['P(OVER|UNDER)'] > 0.5 else 'UNDER'
            result['confidence'] = max(result['P(OVER|UNDER)'], result['P(UNDER|UNDER)'])

        return result

    # ---------- ENTROPY ANALYSIS ----------

    def entropy_analysis(self, n=50):
        """Calculate Shannon entropy to detect non-randomness"""
        seq = self.get_sequence(n)
        if len(seq) < 10:
            return None

        # Binary entropy
        over_count = seq.count('OVER')
        under_count = seq.count('UNDER')
        total = len(seq)

        p_over = over_count / total
        p_under = under_count / total

        entropy = 0
        if p_over > 0:
            entropy -= p_over * math.log2(p_over)
        if p_under > 0:
            entropy -= p_under * math.log2(p_under)

        # Max entropy for binary = 1.0
        normalized_entropy = entropy / 1.0

        # Runs test
        runs = 1
        for i in range(1, len(seq)):
            if seq[i] != seq[i-1]:
                runs += 1

        expected_runs = (2 * over_count * under_count) / total + 1
        variance_runs = (2 * over_count * under_count * (2 * over_count * under_count - total)) / (total * total * (total - 1))

        z_score = (runs - expected_runs) / math.sqrt(variance_runs) if variance_runs > 0 else 0

        return {
            'entropy': entropy,
            'normalized_entropy': normalized_entropy,
            'randomness_quality': 'HIGH' if normalized_entropy > 0.9 else 'MEDIUM' if normalized_entropy > 0.7 else 'LOW',
            'runs': runs,
            'expected_runs': expected_runs,
            'z_score': z_score,
            'pattern_detected': abs(z_score) > 1.96
        }

    # ---------- BAYESIAN ANALYSIS ----------

    def bayesian_prediction(self, n=20):
        """Bayesian updating for next round prediction"""
        rounds = self.get_last_n(n)
        if len(rounds) < 5:
            return None

        # Prior: theoretical probability
        prior_over = self.theoretical_prob_over()
        prior_under = 1 - prior_over

        # Likelihood from recent data
        recent_over = sum(1 for m in rounds if m >= self.threshold) / len(rounds)

        # Bayesian update with weight
        weight = min(len(rounds) / 100, 0.5)  # Max 50% weight to data
        posterior_over = (1 - weight) * prior_over + weight * recent_over

        return {
            'prior_over': prior_over,
            'likelihood_over': recent_over,
            'posterior_over': posterior_over,
            'posterior_under': 1 - posterior_over,
            'prediction': 'OVER' if posterior_over > 0.5 else 'UNDER',
            'confidence': max(posterior_over, 1 - posterior_over)
        }

    # ---------- PATTERN DETECTION ----------

    def detect_patterns(self, n=30):
        """Detect repeating patterns in sequences"""
        seq = self.get_sequence(n)
        if len(seq) < 10:
            return []

        patterns = []

        # Check for streaks
        current_streak = 1
        max_streak_over = 0
        max_streak_under = 0

        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_streak += 1
            else:
                if seq[i-1] == 'OVER':
                    max_streak_over = max(max_streak_over, current_streak)
                else:
                    max_streak_under = max(max_streak_under, current_streak)
                current_streak = 1

        # Check last streak
        if seq[-1] == 'OVER':
            max_streak_over = max(max_streak_over, current_streak)
        else:
            max_streak_under = max(max_streak_under, current_streak)

        # Current streak
        current_streak_type = seq[-1]
        current_streak_len = 1
        for i in range(len(seq)-2, -1, -1):
            if seq[i] == current_streak_type:
                current_streak_len += 1
            else:
                break

        patterns.append({
            'type': 'streak',
            'current_streak_type': current_streak_type,
            'current_streak_length': current_streak_len,
            'max_streak_over': max_streak_over,
            'max_streak_under': max_streak_under
        })

        # Check for alternating pattern
        alternating = all(seq[i] != seq[i+1] for i in range(len(seq)-1))
        if alternating:
            patterns.append({'type': 'alternating', 'description': 'Perfect alternation detected'})

        # Check for clustering
        window_size = 5
        over_ratios = []
        for i in range(len(seq) - window_size + 1):
            window = seq[i:i+window_size]
            over_ratios.append(window.count('OVER') / window_size)

        if over_ratios:
            avg_ratio = statistics.mean(over_ratios)
            if avg_ratio > 0.7:
                patterns.append({'type': 'clustering', 'description': 'OVER clustering detected', 'ratio': avg_ratio})
            elif avg_ratio < 0.3:
                patterns.append({'type': 'clustering', 'description': 'UNDER clustering detected', 'ratio': avg_ratio})

        return patterns

    # ---------- KELLY CRITERION ----------

    def kelly_criterion(self, bankroll, prob_over=None):
        """Calculate optimal bet size using Kelly Criterion"""
        if prob_over is None:
            prob_over = self.theoretical_prob_over()

        # For OVER 2x bet: win 1x (get 2x total, profit 1x), lose 1x
        b = 1.0  # odds received on win (profit/bet)
        p = prob_over
        q = 1 - p

        # Kelly fraction: f* = (bp - q) / b
        kelly = (b * p - q) / b

        # Conservative: half Kelly
        half_kelly = kelly / 2

        return {
            'kelly_fraction': kelly,
            'half_kelly_fraction': half_kelly,
            'optimal_bet': bankroll * max(0, half_kelly),
            'recommendation': 'BET' if kelly > 0 else 'NO BET'
        }

    # ---------- MONTE CARLO SIMULATION ----------

    def monte_carlo_simulation(self, strategy, bankroll=1000, bet_size=10, 
                                target=2.0, num_simulations=1000, max_rounds=100):
        """Simulate betting strategy"""
        results = []

        for sim in range(num_simulations):
            balance = bankroll
            rounds_played = 0
            max_balance = bankroll
            min_balance = bankroll
            wins = 0
            losses = 0

            for round_num in range(max_rounds):
                if balance <= 0:
                    break

                # Simulate round (using theoretical distribution)
                # P(reach m) = (1 - house_edge) / m
                # Generate multiplier: inverse CDF
                u = random.random()
                multiplier = (1 - self.house_edge) / u if u > 0 else 999

                actual_bet = min(bet_size, balance)

                if multiplier >= target:
                    # Win: get bet * target
                    profit = actual_bet * (target - 1)
                    balance += profit
                    wins += 1
                else:
                    # Lose bet
                    balance -= actual_bet
                    losses += 1

                rounds_played += 1
                max_balance = max(max_balance, balance)
                min_balance = min(min_balance, balance)

            results.append({
                'final_balance': balance,
                'rounds_played': rounds_played,
                'max_balance': max_balance,
                'min_balance': min_balance,
                'wins': wins,
                'losses': losses,
                'win_rate': wins / (wins + losses) if (wins + losses) > 0 else 0,
                'profit': balance - bankroll
            })

        # Aggregate results
        profits = [r['profit'] for r in results]
        final_balances = [r['final_balance'] for r in results]

        return {
            'simulations': num_simulations,
            'avg_profit': statistics.mean(profits),
            'median_profit': statistics.median(profits),
            'profit_stdev': statistics.stdev(profits) if len(profits) > 1 else 0,
            'avg_final_balance': statistics.mean(final_balances),
            'bust_rate': sum(1 for r in results if r['final_balance'] <= 0) / num_simulations * 100,
            'profit_rate': sum(1 for r in results if r['profit'] > 0) / num_simulations * 100,
            'max_profit': max(profits),
            'max_loss': min(profits),
            'details': results[:10]  # First 10 for display
        }

    # ---------- MASTER PREDICTION ----------

    def predict(self, n=10):
        """Master prediction combining all methods"""
        if len(self.history) < n:
            return {
                'error': f'Need at least {n} rounds. Currently have {len(self.history)}.'
            }

        # Get all analyses
        markov = self.markov_analysis(n * 5)  # Use more data for Markov
        entropy = self.entropy_analysis(n * 5)
        bayesian = self.bayesian_prediction(n)
        patterns = self.detect_patterns(n * 3)
        stats = self.basic_stats(n)

        # Weighted ensemble prediction
        votes = {'OVER': 0, 'UNDER': 0}
        weights = {'markov': 0.25, 'bayesian': 0.35, 'entropy': 0.20, 'stats': 0.20}

        if markov:
            votes[markov['prediction']] += weights['markov'] * markov['confidence']

        if bayesian:
            votes[bayesian['prediction']] += weights['bayesian'] * bayesian['confidence']

        if entropy:
            # If low entropy, trust pattern more
            if entropy['randomness_quality'] == 'LOW':
                # Use pattern direction
                if patterns and patterns[0]['type'] == 'streak':
                    streak_type = patterns[0]['current_streak_type']
                    streak_len = patterns[0]['current_streak_length']
                    if streak_len >= 3:
                        # Mean reversion or continuation?
                        votes['OVER' if streak_type == 'UNDER' else 'UNDER'] += weights['entropy'] * 0.6
                    else:
                        votes[streak_type] += weights['entropy'] * 0.6

        # Statistical bias
        if stats['over_pct'] > 55:
            votes['OVER'] += weights['stats'] * (stats['over_pct'] / 100)
        elif stats['over_pct'] < 45:
            votes['UNDER'] += weights['stats'] * ((100 - stats['over_pct']) / 100)

        # Final prediction
        total_votes = votes['OVER'] + votes['UNDER']
        if total_votes == 0:
            prediction = 'OVER' if random.random() > 0.5 else 'UNDER'
            confidence = 0.5
        else:
            prediction = 'OVER' if votes['OVER'] > votes['UNDER'] else 'UNDER'
            confidence = max(votes['OVER'], votes['UNDER']) / total_votes

        # Risk assessment
        risk = 'HIGH' if confidence < 0.55 else 'MEDIUM' if confidence < 0.70 else 'LOW'

        # Kelly suggestion
        prob = votes['OVER'] / total_votes if total_votes > 0 else 0.5
        kelly = self.kelly_criterion(1000, prob)

        return {
            'prediction': prediction,
            'confidence': round(confidence * 100, 1),
            'risk': risk,
            'votes': votes,
            'markov': markov,
            'bayesian': bayesian,
            'entropy': entropy,
            'patterns': patterns,
            'stats': stats,
            'kelly': kelly,
            'suggested_bet': kelly['optimal_bet'] if kelly['recommendation'] == 'BET' else 0
        }


# ============================================================
# GUI APPLICATION
# ============================================================

class AviatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AVIATOR ANALYSIS ENGINE v1.0")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0a')

        self.analyzer = AviatorAnalyzer()
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        bg_color = '#0a0a0a'
        fg_color = '#00ff88'
        accent_color = '#ff3366'
        secondary_color = '#3366ff'

        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Consolas', 10))
        style.configure('TButton', background=secondary_color, foreground='white', 
                       font=('Consolas', 10, 'bold'), padding=10)
        style.configure('TEntry', fieldbackground='#1a1a1a', foreground=fg_color, 
                       insertcolor=fg_color, font=('Consolas', 12))

        # Custom styles
        style.configure('Header.TLabel', font=('Consolas', 16, 'bold'), foreground='#ffffff')
        style.configure('Prediction.TLabel', font=('Consolas', 24, 'bold'))
        style.configure('Over.TLabel', foreground='#00ff88')
        style.configure('Under.TLabel', foreground='#ff3366')

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header = ttk.Label(main_frame, text="⚡ AVIATOR ANALYSIS ENGINE v1.0 ⚡", 
                          style='Header.TLabel')
        header.pack(pady=10)

        subtitle = ttk.Label(main_frame, 
                            text="Markov Chains | Bayesian Analysis | Entropy | Kelly Criterion | Monte Carlo",
                            font=('Consolas', 9))
        subtitle.pack(pady=(0, 10))

        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Data Input
        self.create_data_tab()

        # Tab 2: Analysis
        self.create_analysis_tab()

        # Tab 3: Strategy Simulator
        self.create_strategy_tab()

        # Tab 4: History
        self.create_history_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(5, 0))

    def create_data_tab(self):
        """Create data input tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Data Input")

        # Left panel - Input
        left_frame = ttk.Frame(tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(left_frame, text="Enter Round Multipliers:", 
                 font=('Consolas', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        # Input frame with scroll
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill=tk.BOTH, expand=True)

        self.input_text = scrolledtext.ScrolledText(input_frame, width=30, height=20,
                                                     bg='#1a1a1a', fg='#00ff88',
                                                     font=('Consolas', 12),
                                                     insertbackground='#00ff88')
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.insert(tk.END, "1.23\n2.45\n1.01\n3.12\n1.87\n1.45\n2.01\n1.33\n1.98\n2.34")

        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="➕ Add to History", 
                  command=self.add_to_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🎲 Generate Test Data", 
                  command=self.generate_test_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📁 Load CSV", 
                  command=self.load_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear", 
                  command=self.clear_data).pack(side=tk.LEFT, padx=5)

        # Right panel - Quick Stats
        right_frame = ttk.Frame(tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(right_frame, text="Quick Statistics:", 
                 font=('Consolas', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        self.quick_stats_text = scrolledtext.ScrolledText(right_frame, width=50, height=20,
                                                           bg='#1a1a1a', fg='#00ff88',
                                                           font=('Consolas', 10))
        self.quick_stats_text.pack(fill=tk.BOTH, expand=True)
        self.quick_stats_text.config(state=tk.DISABLED)

    def create_analysis_tab(self):
        """Create analysis tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔍 Analysis")

        # Top - Prediction Display
        pred_frame = ttk.Frame(tab)
        pred_frame.pack(fill=tk.X, padx=20, pady=20)

        self.prediction_label = ttk.Label(pred_frame, text="PREDICTION: --", 
                                         style='Prediction.TLabel')
        self.prediction_label.pack()

        self.confidence_label = ttk.Label(pred_frame, text="Confidence: --%", 
                                         font=('Consolas', 14))
        self.confidence_label.pack(pady=5)

        self.risk_label = ttk.Label(pred_frame, text="Risk Level: --", 
                                   font=('Consolas', 12))
        self.risk_label.pack()

        # Analyze button
        ttk.Button(tab, text="🔮 RUN FULL ANALYSIS", 
                  command=self.run_analysis, 
                  style='TButton').pack(pady=10)

        # Results notebook
        results_notebook = ttk.Notebook(tab)
        results_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Sub-tabs
        self.markov_text = self.create_result_tab(results_notebook, "Markov Chains")
        self.bayesian_text = self.create_result_tab(results_notebook, "Bayesian")
        self.entropy_text = self.create_result_tab(results_notebook, "Entropy")
        self.patterns_text = self.create_result_tab(results_notebook, "Patterns")
        self.kelly_text = self.create_result_tab(results_notebook, "Kelly Criterion")

    def create_result_tab(self, parent, title):
        """Create a result sub-tab"""
        tab = ttk.Frame(parent)
        parent.add(tab, text=title)
        text = scrolledtext.ScrolledText(tab, bg='#1a1a1a', fg='#00ff88',
                                         font=('Consolas', 10), wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.config(state=tk.DISABLED)
        return text

    def create_strategy_tab(self):
        """Create strategy simulator tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎯 Strategy Simulator")

        # Parameters
        params_frame = ttk.Frame(tab)
        params_frame.pack(fill=tk.X, padx=20, pady=20)

        # Bankroll
        ttk.Label(params_frame, text="Bankroll ($):").grid(row=0, column=0, padx=5, pady=5)
        self.bankroll_var = tk.StringVar(value="1000")
        ttk.Entry(params_frame, textvariable=self.bankroll_var, width=15).grid(row=0, column=1, padx=5, pady=5)

        # Bet Size
        ttk.Label(params_frame, text="Bet Size ($):").grid(row=0, column=2, padx=5, pady=5)
        self.bet_var = tk.StringVar(value="10")
        ttk.Entry(params_frame, textvariable=self.bet_var, width=15).grid(row=0, column=3, padx=5, pady=5)

        # Target Multiplier
        ttk.Label(params_frame, text="Target (x):").grid(row=1, column=0, padx=5, pady=5)
        self.target_var = tk.StringVar(value="2.0")
        ttk.Entry(params_frame, textvariable=self.target_var, width=15).grid(row=1, column=1, padx=5, pady=5)

        # Simulations
        ttk.Label(params_frame, text="Simulations:").grid(row=1, column=2, padx=5, pady=5)
        self.sims_var = tk.StringVar(value="1000")
        ttk.Entry(params_frame, textvariable=self.sims_var, width=15).grid(row=1, column=3, padx=5, pady=5)

        # Run button
        ttk.Button(tab, text="🚀 RUN MONTE CARLO SIMULATION", 
                  command=self.run_simulation).pack(pady=10)

        # Results
        self.sim_results_text = scrolledtext.ScrolledText(tab, bg='#1a1a1a', fg='#00ff88',
                                                          font=('Consolas', 10))
        self.sim_results_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.sim_results_text.config(state=tk.DISABLED)

    def create_history_tab(self):
        """Create history tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📜 History")

        # History display
        self.history_text = scrolledtext.ScrolledText(tab, bg='#1a1a1a', fg='#00ff88',
                                                      font=('Consolas', 10))
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.history_text.config(state=tk.DISABLED)

        # Export button
        ttk.Button(tab, text="💾 Export to CSV", 
                  command=self.export_csv).pack(pady=10)

    # ---------- BUTTON HANDLERS ----------

    def add_to_history(self):
        """Add input data to history"""
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some data!")
            return

        lines = text.split('\n')
        added = 0
        for line in lines:
            line = line.strip()
            if line:
                try:
                    val = float(line.replace(',', '.'))
                    if val > 0:
                        self.analyzer.add_round(val)
                        added += 1
                except ValueError:
                    continue

        self.status_var.set(f"Added {added} rounds. Total: {len(self.analyzer.history)}")
        self.update_quick_stats()
        self.update_history_display()
        messagebox.showinfo("Success", f"Added {added} rounds to history!")

    def generate_test_data(self):
        """Generate realistic test data"""
        self.analyzer.history = []
        for _ in range(100):
            u = random.random()
            if u < 0.03:
                multiplier = 1.0
            else:
                multiplier = (1 - 0.03) / u
            self.analyzer.add_round(min(multiplier, 100))

        self.status_var.set(f"Generated 100 test rounds")
        self.update_quick_stats()
        self.update_history_display()
        messagebox.showinfo("Success", "Generated 100 realistic test rounds!")

    def load_csv(self):
        """Load data from CSV"""
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    reader = csv.reader(f)
                    added = 0
                    for row in reader:
                        for val in row:
                            try:
                                m = float(val.strip())
                                if m > 0:
                                    self.analyzer.add_round(m)
                                    added += 1
                            except:
                                continue
                self.status_var.set(f"Loaded {added} rounds from CSV")
                self.update_quick_stats()
                self.update_history_display()
                messagebox.showinfo("Success", f"Loaded {added} rounds!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def clear_data(self):
        """Clear all data"""
        self.analyzer.history = []
        self.status_var.set("History cleared")
        self.update_quick_stats()
        self.update_history_display()

    def update_quick_stats(self):
        """Update quick statistics display"""
        self.quick_stats_text.config(state=tk.NORMAL)
        self.quick_stats_text.delete("1.0", tk.END)

        if len(self.analyzer.history) == 0:
            self.quick_stats_text.insert(tk.END, "No data yet.\n\nEnter multipliers or generate test data.")
        else:
            stats = self.analyzer.basic_stats(len(self.analyzer.history))
            self.quick_stats_text.insert(tk.END, f"""
Total Rounds: {stats['count']}
Mean: {stats['mean']:.2f}x
Median: {stats['median']:.2f}x
Std Dev: {stats['stdev']:.2f}
Min: {stats['min']:.2f}x
Max: {stats['max']:.2f}x

OVER 2x: {stats['over_count']} ({stats['over_pct']:.1f}%)
UNDER 2x: {stats['under_count']} ({100-stats['over_pct']:.1f}%)

Theoretical OVER %: 48.5%
Deviation: {stats['over_pct'] - 48.5:+.1f}%
""")
        self.quick_stats_text.config(state=tk.DISABLED)

    def update_history_display(self):
        """Update history tab"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)

        for i, m in enumerate(self.analyzer.history, 1):
            cat = self.analyzer.categorize(m)
            symbol = "▲" if cat == "OVER" else "▼"
            self.history_text.insert(tk.END, f"Round {i:4d}: {m:6.2f}x {symbol} {cat}\n")

        self.history_text.config(state=tk.DISABLED)

    def run_analysis(self):
        """Run full analysis"""
        if len(self.analyzer.history) < 10:
            messagebox.showwarning("Warning", "Need at least 10 rounds for analysis!")
            return

        result = self.analyzer.predict(n=10)

        if 'error' in result:
            messagebox.showerror("Error", result['error'])
            return

        # Update prediction display
        pred = result['prediction']
        conf = result['confidence']
        risk = result['risk']

        self.prediction_label.config(
            text=f"PREDICTION: {pred} 2x",
            style='Over.TLabel' if pred == 'OVER' else 'Under.TLabel'
        )
        self.confidence_label.config(text=f"Confidence: {conf}%")
        self.risk_label.config(text=f"Risk Level: {risk}")

        # Update Markov
        self.update_text_widget(self.markov_text, self.format_markov(result['markov']))

        # Update Bayesian
        self.update_text_widget(self.bayesian_text, self.format_bayesian(result['bayesian']))

        # Update Entropy
        self.update_text_widget(self.entropy_text, self.format_entropy(result['entropy']))

        # Update Patterns
        self.update_text_widget(self.patterns_text, self.format_patterns(result['patterns']))

        # Update Kelly
        self.update_text_widget(self.kelly_text, self.format_kelly(result['kelly'], result['suggested_bet']))

        self.status_var.set(f"Analysis complete. Prediction: {pred} ({conf}% confidence)")

    def update_text_widget(self, widget, text):
        """Update a text widget"""
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    def format_markov(self, markov):
        if not markov:
            return "Insufficient data for Markov analysis.\nNeed at least 10 rounds."
        return f"""
MARKOV CHAIN ANALYSIS
{'='*50}

Transition Counts:
  OVER → OVER:   {markov['transitions']['OVER→OVER']:4d}
  OVER → UNDER:  {markov['transitions']['OVER→UNDER']:4d}
  UNDER → OVER:  {markov['transitions']['UNDER→OVER']:4d}
  UNDER → UNDER: {markov['transitions']['UNDER→UNDER']:4d}

Transition Probabilities:
  P(OVER | OVER)   = {markov['P(OVER|OVER)']:.3f}
  P(UNDER | OVER)  = {markov['P(UNDER|OVER)']:.3f}
  P(OVER | UNDER)  = {markov['P(OVER|UNDER)']:.3f}
  P(UNDER | UNDER) = {markov['P(UNDER|UNDER)']:.3f}

Prediction based on last state:
  → {markov['prediction']} (confidence: {markov['confidence']:.1%})
"""

    def format_bayesian(self, bayesian):
        if not bayesian:
            return "Insufficient data for Bayesian analysis."
        return f"""
BAYESIAN ANALYSIS
{'='*50}

Prior (Theoretical):
  P(OVER) = {bayesian['prior_over']:.3f}
  P(UNDER) = {1-bayesian['prior_over']:.3f}

Likelihood (Recent Data):
  P(OVER|data) = {bayesian['likelihood_over']:.3f}

Posterior (Updated):
  P(OVER) = {bayesian['posterior_over']:.3f}
  P(UNDER) = {bayesian['posterior_under']:.3f}

Prediction: {bayesian['prediction']}
Confidence: {bayesian['confidence']:.1%}
"""

    def format_entropy(self, entropy):
        if not entropy:
            return "Insufficient data for entropy analysis."
        return f"""
ENTROPY ANALYSIS
{'='*50}

Shannon Entropy: {entropy['entropy']:.3f} bits
Normalized: {entropy['normalized_entropy']:.3f} (max = 1.0)
Randomness Quality: {entropy['randomness_quality']}

Runs Test:
  Observed Runs: {entropy['runs']}
  Expected Runs: {entropy['expected_runs']:.1f}
  Z-Score: {entropy['z_score']:.3f}

Pattern Detected: {'YES' if entropy['pattern_detected'] else 'NO'}
{'⚠️ WARNING: Non-random pattern detected!' if entropy['pattern_detected'] else '✓ Randomness appears normal'}
"""

    def format_patterns(self, patterns):
        if not patterns:
            return "No patterns detected yet."
        text = "PATTERN DETECTION\n" + "="*50 + "\n\n"
        for p in patterns:
            if p['type'] == 'streak':
                text += f"""Streak Analysis:
  Current Streak: {p['current_streak_length']} x {p['current_streak_type']}
  Max OVER Streak: {p['max_streak_over']}
  Max UNDER Streak: {p['max_streak_under']}
"""
            elif p['type'] == 'alternating':
                text += f"Alternating Pattern: {p['description']}\n"
            elif p['type'] == 'clustering':
                text += f"Clustering: {p['description']} (ratio: {p['ratio']:.2f})\n"
        return text

    def format_kelly(self, kelly, suggested):
        return f"""
KELLY CRITERION
{'='*50}

Kelly Fraction: {kelly['kelly_fraction']:.3f}
Half Kelly (Conservative): {kelly['half_kelly_fraction']:.3f}

Recommendation: {kelly['recommendation']}

Suggested Bet: ${suggested:.2f}

Note: Kelly Criterion maximizes long-term growth.
Half-Kelly reduces volatility while maintaining most growth.
"""

    def run_simulation(self):
        """Run Monte Carlo simulation"""
        try:
            bankroll = float(self.bankroll_var.get())
            bet = float(self.bet_var.get())
            target = float(self.target_var.get())
            sims = int(self.sims_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid input values!")
            return

        self.status_var.set("Running Monte Carlo simulation...")
        self.root.update()

        results = self.analyzer.monte_carlo_simulation(
            strategy="fixed", bankroll=bankroll, bet_size=bet,
            target=target, num_simulations=sims, max_rounds=100
        )

        text = f"""
MONTE CARLO SIMULATION RESULTS
{'='*60}

Parameters:
  Starting Bankroll: ${bankroll:.2f}
  Bet Size: ${bet:.2f}
  Target Multiplier: {target}x
  Simulations: {sims:,}

Results:
  Average Profit: ${results['avg_profit']:.2f}
  Median Profit: ${results['median_profit']:.2f}
  Profit Std Dev: ${results['profit_stdev']:.2f}

  Average Final Balance: ${results['avg_final_balance']:.2f}

  Bust Rate (lost everything): {results['bust_rate']:.1f}%
  Profit Rate (ended positive): {results['profit_rate']:.1f}%

  Best Case Profit: ${results['max_profit']:.2f}
  Worst Case Loss: ${results['max_loss']:.2f}

Interpretation:
  {'⚠️ NEGATIVE EXPECTATION - House edge wins in long run' if results['avg_profit'] < 0 else '✓ POSITIVE EXPECTATION - Possible edge detected'}

  Theoretical win rate at {target}x: ~{(1-0.03)/target*100:.1f}%
"""

        self.sim_results_text.config(state=tk.NORMAL)
        self.sim_results_text.delete("1.0", tk.END)
        self.sim_results_text.insert(tk.END, text)
        self.sim_results_text.config(state=tk.DISABLED)

        self.status_var.set(f"Simulation complete. Avg profit: ${results['avg_profit']:.2f}")

    def export_csv(self):
        """Export history to CSV"""
        if not self.analyzer.history:
            messagebox.showwarning("Warning", "No data to export!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Round', 'Multiplier', 'Category'])
                    for i, m in enumerate(self.analyzer.history, 1):
                        writer.writerow([i, m, self.analyzer.categorize(m)])
                messagebox.showinfo("Success", f"Exported {len(self.analyzer.history)} rounds to CSV!")
            except Exception as e:
                messagebox.showerror("Error", str(e))


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    root = tk.Tk()
    app = AviatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
