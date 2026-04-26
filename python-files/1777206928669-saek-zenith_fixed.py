import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

# ==================== CONFIGURATION ====================
COLORS = {
    'bg': '#0C0C0C',
    'bg2': '#111111',
    'card': '#181818',
    'card_hover': '#1F1F1F',
    'border': '#2A2A2A',
    'fg': '#E8E4DE',
    'fg2': '#C4BFB6',
    'muted': '#6B6660',
    'accent': '#D4943A',
    'accent2': '#E8A838',
    'accent_dim': '#3D2E1A',
    'danger': '#D94848',
    'success': '#3DB86A',
    'info': '#4A9BD9'
}

DATA_FILE = 'zenith_data.json'

# ==================== DATA MANAGEMENT ====================
class DataManager:
    def __init__(self):
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self.create_fresh_state()

    def create_fresh_state(self):
        return {
            'tasks': [],
            'notes': [],
            'habits': [],
            'pomodoro': {'sessions_today': 0, 'total_minutes': 0},
            'activity': [0, 0, 0, 0, 0, 0, 0],
            'next_id': 1,
            'created_at': str(datetime.now())
        }

    def save(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get_next_id(self):
        nid = self.data['next_id']
        self.data['next_id'] += 1
        return nid

data_manager = DataManager()

# ==================== MAIN APPLICATION ====================
class ZenithApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Zenith — Productivity Suite")
        self.geometry("1200x800")
        self.configure(bg=COLORS['bg'])

        self.main_container = tk.Frame(self, bg=COLORS['bg'])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.create_sidebar()
        self.create_content_area()

        self.current_view = None
        self.show_view('dashboard')

    def create_sidebar(self):
        self.sidebar = tk.Frame(self.main_container, bg=COLORS['bg2'], width=72)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg=COLORS['accent'], width=40, height=40)
        logo_frame.place(x=16, y=20)
        logo_label = tk.Label(logo_frame, text="Z", font=('Segoe UI', 18, 'bold'),
                              bg=COLORS['accent'], fg=COLORS['bg'])
        logo_label.pack(expand=True)

        nav_items = [
            ('dashboard', '📊', 'Dashboard'),
            ('focus',     '⏱️', 'Focus'),
            ('tasks',     '✅', 'Tasks'),
            ('notes',     '📝', 'Notes'),
            ('habits',    '🔥', 'Habits')
        ]

        self.nav_buttons = {}
        y_pos = 90

        for view_id, icon, tooltip in nav_items:
            btn = tk.Button(self.sidebar, text=icon, font=('Segoe UI', 16),
                            bg=COLORS['bg2'], fg=COLORS['muted'],
                            activebackground=COLORS['accent_dim'],
                            activeforeground=COLORS['fg2'],
                            relief=tk.FLAT, cursor='hand2',
                            width=3, height=1,
                            command=lambda v=view_id: self.show_view(v))
            btn.place(x=12, y=y_pos, width=48, height=48)
            self.create_tooltip(btn, tooltip)
            self.nav_buttons[view_id] = btn
            y_pos += 56

    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+25}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background=COLORS['card'],
                             foreground=COLORS['fg'], font=('Segoe UI', 10),
                             padx=10, pady=5, relief=tk.SOLID, borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            def hide():
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
                    del widget.tooltip
            widget.after(2000, hide)

        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def create_content_area(self):
        self.content_area = tk.Frame(self.main_container, bg=COLORS['bg'])
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.create_topbar()
        self.views_container = tk.Frame(self.content_area, bg=COLORS['bg'])
        self.views_container.pack(fill=tk.BOTH, expand=True, padx=28, pady=28)

    def create_topbar(self):
        topbar = tk.Frame(self.content_area, bg=COLORS['bg2'], height=60)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)

        greeting_frame = tk.Frame(topbar, bg=COLORS['bg2'])
        greeting_frame.pack(side=tk.LEFT, padx=32, pady=15)

        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"

        tk.Label(greeting_frame, text=greeting, font=('Segoe UI', 18, 'bold'),
                 bg=COLORS['bg2'], fg=COLORS['fg']).pack(anchor='w')
        tk.Label(greeting_frame, text="Let's make today count",
                 font=('Segoe UI', 11), bg=COLORS['bg2'], fg=COLORS['muted']).pack(anchor='w')

        date_str = datetime.now().strftime("%A, %B %d, %Y")
        date_label = tk.Label(topbar, text=date_str, font=('Segoe UI', 11),
                              bg=COLORS['card'], fg=COLORS['muted'],
                              padx=14, pady=8, relief=tk.SOLID, borderwidth=1)
        date_label.place(relx=0.95, rely=0.5, anchor='e', x=-32)

    def show_view(self, view_name):
        for widget in self.views_container.winfo_children():
            widget.destroy()

        for vid, btn in self.nav_buttons.items():
            if vid == view_name:
                btn.configure(bg=COLORS['accent_dim'], fg=COLORS['accent'])
            else:
                btn.configure(bg=COLORS['bg2'], fg=COLORS['muted'])

        self.current_view = view_name

        views = {
            'dashboard': DashboardView,
            'focus':     FocusView,
            'tasks':     TasksView,
            'notes':     NotesView,
            'habits':    HabitsView,
        }
        if view_name in views:
            views[view_name](self.views_container)

# ==================== DASHBOARD VIEW ====================
class DashboardView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS['bg'])
        self.pack(fill=tk.BOTH, expand=True)
        self.create_stats_row()
        self.create_main_content()

    def create_stats_row(self):
        stats_frame = tk.Frame(self, bg=COLORS['bg'])
        stats_frame.pack(fill=tk.X, pady=(0, 24))

        active_tasks    = len([t for t in data_manager.data['tasks'] if not t.get('done')])
        completed_tasks = len([t for t in data_manager.data['tasks'] if t.get('done')])
        focus_minutes   = data_manager.data['pomodoro']['total_minutes']
        active_habits   = len(data_manager.data['habits'])

        stats = [
            ('📋', active_tasks,    'Active Tasks',   COLORS['accent']),
            ('✅', completed_tasks, 'Completed',      COLORS['success']),
            ('⏰', focus_minutes,   'Focus Minutes',  COLORS['info']),
            ('🔥', active_habits,   'Active Habits',  '#9B4DCA'),
        ]

        for i, (icon, value, label, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg=COLORS['card'], relief=tk.SOLID, borderwidth=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                      padx=(0, 16) if i < 3 else (0, 0))
            card.pack_propagate(False)
            card.configure(height=120)

            inner = tk.Frame(card, bg=COLORS['card'])
            inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

            tk.Label(inner, text=icon, font=('Segoe UI', 16),
                     bg=COLORS['card'], fg=color).pack(anchor='w')
            tk.Label(inner, text=str(value), font=('Segoe UI', 28, 'bold'),
                     bg=COLORS['card'], fg=COLORS['fg']).pack(anchor='w', pady=(4, 0))
            tk.Label(inner, text=label, font=('Segoe UI', 11),
                     bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w', pady=(2, 0))

    def create_main_content(self):
        content = tk.Frame(self, bg=COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True)

        top_row = tk.Frame(content, bg=COLORS['bg'])
        top_row.pack(fill=tk.X, pady=(0, 24))

        tasks_card = self.create_card(top_row, "📋 Today's Tasks", COLORS['accent'])
        tasks_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        self.render_dashboard_tasks(tasks_card)

        activity_card = self.create_card(top_row, "📈 Weekly Activity", COLORS['success'])
        activity_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        activity_card.configure(width=300)
        self.render_activity_chart(activity_card)

        bottom_row = tk.Frame(content, bg=COLORS['bg'])
        bottom_row.pack(fill=tk.BOTH, expand=True)

        notes_card = self.create_card(bottom_row, "📝 Recent Notes", COLORS['info'])
        notes_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        self.render_dashboard_notes(notes_card)

        habits_card = self.create_card(bottom_row, "🔥 Habit Streaks", COLORS['danger'])
        habits_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.render_dashboard_habits(habits_card)

    def create_card(self, parent, title, accent_color):
        outer = tk.Frame(parent, bg=COLORS['border'], relief=tk.FLAT)
        inner = tk.Frame(outer, bg=COLORS['card'], relief=tk.FLAT)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        header = tk.Frame(inner, bg=COLORS['card'])
        header.pack(fill=tk.X, padx=20, pady=(16, 12))

        tk.Label(header, text=title, font=('Segoe UI', 13, 'bold'),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(side=tk.LEFT)

        return inner

    def render_dashboard_tasks(self, parent):
        container = tk.Frame(parent, bg=COLORS['card'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        tasks = data_manager.data['tasks'][:5]
        if not tasks:
            tk.Label(container, text="➕ Add tasks from the Tasks view",
                     font=('Segoe UI', 11), bg=COLORS['card'], fg=COLORS['muted']).pack(pady=40)
            return

        for task in tasks:
            row = tk.Frame(container, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=4)

            check_var = tk.BooleanVar(value=task.get('done', False))
            tk.Checkbutton(row, variable=check_var,
                           bg=COLORS['card'], selectcolor=COLORS['card'],
                           activebackground=COLORS['card'],
                           command=lambda t=task['id']: self.toggle_task(t)).pack(side=tk.LEFT)

            fg = COLORS['muted'] if task.get('done') else COLORS['fg']
            tk.Label(row, text=task['text'], font=('Segoe UI', 12),
                     bg=COLORS['card'], fg=fg, anchor='w').pack(
                     side=tk.LEFT, padx=8, fill=tk.X, expand=True)

    def render_activity_chart(self, parent):
        container = tk.Frame(parent, bg=COLORS['card'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        days     = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        activity = data_manager.data['activity']
        max_act  = max(max(activity), 1)
        today    = datetime.now().weekday()

        bars_frame = tk.Frame(container, bg=COLORS['card'])
        bars_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        for i, (day, val) in enumerate(zip(days, activity)):
            col = tk.Frame(bars_frame, bg=COLORS['card'])
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

            height = max(10, int((val / max_act) * 120))
            color  = COLORS['accent'] if i == today else COLORS['border']

            tk.Frame(col, bg=color, height=height).pack(side=tk.BOTTOM, fill=tk.X)
            tk.Label(col, text=day[:1], font=('Segoe UI', 9),
                     bg=COLORS['card'], fg=COLORS['muted']).pack(side=tk.BOTTOM, pady=(4, 0))

    def render_dashboard_notes(self, parent):
        container = tk.Frame(parent, bg=COLORS['card'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        notes = data_manager.data['notes'][:3]
        if not notes:
            tk.Label(container, text="✍️ Create notes from the Notes view",
                     font=('Segoe UI', 11), bg=COLORS['card'], fg=COLORS['muted']).pack(pady=40)
            return

        for note in notes:
            row = tk.Frame(container, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=6)

            tk.Frame(row, bg=note.get('color', COLORS['accent']), width=4).pack(
                side=tk.LEFT, fill=tk.Y, padx=(0, 10))

            info = tk.Frame(row, bg=COLORS['card'])
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(info, text=note['title'], font=('Segoe UI', 12, 'bold'),
                     bg=COLORS['card'], fg=COLORS['fg'], anchor='w').pack(fill=tk.X)

            raw = note.get('content', '')
            preview = (raw[:50] + '...') if len(raw) > 50 else raw
            tk.Label(info, text=preview, font=('Segoe UI', 10),
                     bg=COLORS['card'], fg=COLORS['muted'], anchor='w').pack(fill=tk.X)

    def render_dashboard_habits(self, parent):
        container = tk.Frame(parent, bg=COLORS['card'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        habits = data_manager.data['habits']
        if not habits:
            tk.Label(container, text="🌱 Track habits from the Habits view",
                     font=('Segoe UI', 11), bg=COLORS['card'], fg=COLORS['muted']).pack(pady=40)
            return

        for habit in habits:
            row = tk.Frame(container, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=6)

            streak = sum(habit.get('days', [False]*7))

            # FIX: original had font=('Segoe UI', 14') — stray quote before closing paren
            tk.Label(row, text=habit.get('icon', '🎯'),
                     font=('Segoe UI', 14),
                     bg=COLORS['card'],
                     fg=habit.get('color', COLORS['accent'])).pack(side=tk.LEFT)

            tk.Label(row, text=habit['name'], font=('Segoe UI', 12),
                     bg=COLORS['card'], fg=COLORS['fg'], anchor='w').pack(
                     side=tk.LEFT, padx=10, fill=tk.X, expand=True)

            tk.Label(row, text=f"{streak}/7", font=('Segoe UI', 12, 'bold'),
                     bg=COLORS['card'], fg=habit.get('color', COLORS['accent'])).pack(side=tk.RIGHT)

    def toggle_task(self, task_id):
        for task in data_manager.data['tasks']:
            if task['id'] == task_id:
                task['done'] = not task['done']
                if task['done']:
                    data_manager.data['activity'][datetime.now().weekday()] += 1
                data_manager.save()
                break
        self.master.show_view('dashboard')

# ==================== FOCUS TIMER VIEW ====================
class FocusView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS['bg'])
        self.pack(fill=tk.BOTH, expand=True)

        self.running    = False
        self.time_left  = 25 * 60
        self.total_time = 25 * 60
        self.mode       = "Focus"

        self.create_ui()

    def create_ui(self):
        center = tk.Frame(self, bg=COLORS['bg'])
        center.place(relx=0.5, rely=0.5, anchor='center')

        card = tk.Frame(center, bg=COLORS['card'], relief=tk.SOLID, borderwidth=1)
        card.pack(pady=20)

        inner = tk.Frame(card, bg=COLORS['card'], width=400)
        inner.pack(padx=40, pady=40)
        inner.pack_propagate(False)

        tk.Label(inner, text="🎯 Focus Timer", font=('Segoe UI', 16, 'bold'),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(pady=(0, 24))

        self.time_display = tk.Label(inner, text="25:00", font=('Consolas', 56, 'bold'),
                                     bg=COLORS['card'], fg=COLORS['fg'])
        self.time_display.pack(pady=20)

        self.mode_display = tk.Label(inner, text="Focus", font=('Segoe UI', 12),
                                     bg=COLORS['card'], fg=COLORS['muted'])
        self.mode_display.pack()

        controls = tk.Frame(inner, bg=COLORS['card'])
        controls.pack(pady=24)

        tk.Button(controls, text="↺ Reset", font=('Segoe UI', 11),
                  bg=COLORS['bg'], fg=COLORS['fg2'], activebackground=COLORS['border'],
                  relief=tk.FLAT, cursor='hand2', command=self.reset_timer,
                  padx=12, pady=8).pack(side=tk.LEFT, padx=4)

        self.start_btn = tk.Button(controls, text="▶ Start", font=('Segoe UI', 13, 'bold'),
                                   bg=COLORS['accent'], fg=COLORS['bg'],
                                   activebackground=COLORS['accent2'],
                                   relief=tk.FLAT, cursor='hand2',
                                   command=self.toggle_timer, padx=30, pady=12)
        self.start_btn.pack(side=tk.LEFT, padx=8)

        tk.Button(controls, text="⏭ Skip", font=('Segoe UI', 11),
                  bg=COLORS['bg'], fg=COLORS['fg2'], activebackground=COLORS['border'],
                  relief=tk.FLAT, cursor='hand2', command=self.skip_session,
                  padx=12, pady=8).pack(side=tk.LEFT, padx=4)

        modes_frame = tk.Frame(inner, bg=COLORS['card'])
        modes_frame.pack(pady=12)

        self.mode_buttons = {}
        for mode_name, minutes, active in [("Focus", 25, True), ("Short Break", 5, False), ("Long Break", 15, False)]:
            btn = tk.Button(modes_frame, text=mode_name, font=('Segoe UI', 10),
                            bg=COLORS['accent_dim'] if active else COLORS['bg'],
                            fg=COLORS['accent'] if active else COLORS['fg2'],
                            activebackground=COLORS['accent_dim'],
                            relief=tk.FLAT, cursor='hand2',
                            command=lambda m=mode_name, mins=minutes: self.set_mode(m, mins),
                            padx=14, pady=6)
            btn.pack(side=tk.LEFT, padx=3)
            self.mode_buttons[mode_name] = btn

        # Sessions card
        sess_card = tk.Frame(center, bg=COLORS['card'], relief=tk.SOLID, borderwidth=1)
        sess_card.pack(pady=20, fill=tk.X, padx=100)
        sess_inner = tk.Frame(sess_card, bg=COLORS['card'])
        sess_inner.pack(padx=24, pady=20)

        tk.Label(sess_inner, text="🏆 Sessions Today", font=('Segoe UI', 13, 'bold'),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w', pady=(0, 12))

        self.sessions_display = tk.Frame(sess_inner, bg=COLORS['card'])
        self.sessions_display.pack(fill=tk.X)
        self.update_sessions_display()

    def toggle_timer(self):
        if self.running:
            self.running = False
            self.start_btn.config(text="▶ Start")
        else:
            self.running = True
            self.start_btn.config(text="⏸ Pause")
            self.run_timer()

    def run_timer(self):
        if self.running and self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            self.after(1000, self.run_timer)
        elif self.time_left <= 0:
            self.timer_complete()

    def timer_complete(self):
        self.running = False
        self.start_btn.config(text="▶ Start")
        if self.total_time == 25 * 60:
            data_manager.data['pomodoro']['sessions_today'] += 1
            data_manager.data['pomodoro']['total_minutes'] += 25
            data_manager.save()
            messagebox.showinfo("Session Complete!", "Great work! Focus session completed.")
            self.update_sessions_display()
        else:
            messagebox.showinfo("Break Over!", "Ready for another round?")

    def reset_timer(self):
        self.running = False
        self.time_left = self.total_time
        self.start_btn.config(text="▶ Start")
        self.update_display()

    def skip_session(self):
        self.running = False
        if self.total_time == 25 * 60:
            data_manager.data['pomodoro']['sessions_today'] += 1
            data_manager.data['pomodoro']['total_minutes'] += 25
            data_manager.save()
            self.update_sessions_display()
        self.time_left = self.total_time
        self.start_btn.config(text="▶ Start")
        self.update_display()

    def set_mode(self, mode, minutes):
        self.mode = mode
        self.total_time = minutes * 60
        self.time_left  = minutes * 60
        self.running    = False
        self.start_btn.config(text="▶ Start")
        for m, btn in self.mode_buttons.items():
            btn.config(bg=COLORS['accent_dim'] if m == mode else COLORS['bg'],
                       fg=COLORS['accent']     if m == mode else COLORS['fg2'])
        self.update_display()

    def update_display(self):
        self.time_display.config(text=f"{self.time_left//60:02d}:{self.time_left%60:02d}")
        self.mode_display.config(text=self.mode)

    def update_sessions_display(self):
        for w in self.sessions_display.winfo_children():
            w.destroy()
        n = data_manager.data['pomodoro']['sessions_today']
        if n == 0:
            tk.Label(self.sessions_display, text="No sessions yet today. Start focusing!",
                     font=('Segoe UI', 11), bg=COLORS['card'], fg=COLORS['muted']).pack()
        else:
            for _ in range(n):
                dot = tk.Frame(self.sessions_display, bg=COLORS['accent_dim'], width=36, height=36)
                dot.pack(side=tk.LEFT, padx=3)
                dot.pack_propagate(False)
                tk.Label(dot, text="✓", font=('Segoe UI', 12),
                         bg=COLORS['accent_dim'], fg=COLORS['accent']).pack(expand=True)

# ==================== TASKS VIEW ====================
class TasksView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS['bg'])
        self.pack(fill=tk.BOTH, expand=True)
        self.filter_mode = 'all'
        self.create_ui()
        self.render_tasks()

    def create_ui(self):
        header = tk.Frame(self, bg=COLORS['bg'])
        header.pack(fill=tk.X, pady=(0, 20))

        tk.Label(header, text="Tasks", font=('Segoe UI', 24, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['fg']).pack(side=tk.LEFT)

        right = tk.Frame(header, bg=COLORS['bg'])
        right.pack(side=tk.RIGHT)

        filters_frame = tk.Frame(right, bg=COLORS['bg'])
        filters_frame.pack(side=tk.LEFT, padx=(0, 12))

        self.filter_buttons = {}
        for label, ftype in [('All', 'all'), ('Active', 'active'), ('Done', 'completed')]:
            btn = tk.Button(filters_frame, text=label, font=('Segoe UI', 11),
                            bg=COLORS['accent_dim'] if ftype == 'all' else COLORS['bg'],
                            fg=COLORS['accent']     if ftype == 'all' else COLORS['fg2'],
                            activebackground=COLORS['accent_dim'],
                            relief=tk.FLAT, cursor='hand2',
                            command=lambda f=ftype: self.set_filter(f),
                            padx=12, pady=6)
            btn.pack(side=tk.LEFT, padx=2)
            self.filter_buttons[ftype] = btn

        tk.Button(right, text="+ Add Task", font=('Segoe UI', 11, 'bold'),
                  bg=COLORS['accent'], fg=COLORS['bg'], activebackground=COLORS['accent2'],
                  relief=tk.FLAT, cursor='hand2', command=self.add_task_dialog,
                  padx=16, pady=8).pack(side=tk.LEFT)

        self.tasks_list = tk.Frame(self, bg=COLORS['bg'])
        self.tasks_list.pack(fill=tk.BOTH, expand=True)

    def set_filter(self, f):
        self.filter_mode = f
        for ft, btn in self.filter_buttons.items():
            btn.config(bg=COLORS['accent_dim'] if ft == f else COLORS['bg'],
                       fg=COLORS['accent']     if ft == f else COLORS['fg2'])
        self.render_tasks()

    def render_tasks(self):
        for w in self.tasks_list.winfo_children():
            w.destroy()

        tasks = data_manager.data['tasks']
        if self.filter_mode == 'active':
            tasks = [t for t in tasks if not t.get('done')]
        elif self.filter_mode == 'completed':
            tasks = [t for t in tasks if t.get('done')]

        if not tasks:
            msgs = {'all': 'No tasks yet. Add one to get started.',
                    'active': 'All caught up! Nothing active.',
                    'completed': 'No completed tasks yet.'}
            tk.Label(self.tasks_list, text=f"✅ {msgs[self.filter_mode]}",
                     font=('Segoe UI', 12), bg=COLORS['bg'], fg=COLORS['muted']).pack(pady=80)
            return

        for task in tasks:
            self.create_task_item(task)

    def create_task_item(self, task):
        item = tk.Frame(self.tasks_list, bg=COLORS['card'], relief=tk.SOLID, borderwidth=1)
        item.pack(fill=tk.X, pady=4)
        inner = tk.Frame(item, bg=COLORS['card'])
        inner.pack(fill=tk.X, padx=14, pady=12)

        check_var = tk.BooleanVar(value=task.get('done', False))
        tk.Checkbutton(inner, variable=check_var,
                       bg=COLORS['card'], selectcolor=COLORS['card'],
                       activebackground=COLORS['card'],
                       command=lambda tid=task['id']: self.toggle_task(tid)).pack(side=tk.LEFT)

        info = tk.Frame(inner, bg=COLORS['card'])
        info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        fg = COLORS['muted'] if task.get('done') else COLORS['fg']
        tk.Label(info, text=task['text'], font=('Segoe UI', 13),
                 bg=COLORS['card'], fg=fg, anchor='w').pack(fill=tk.X)

        meta = tk.Frame(info, bg=COLORS['card'])
        meta.pack(fill=tk.X, pady=(4, 0))

        cat_colors = {'work': COLORS['info'], 'personal': COLORS['accent'],
                      'health': COLORS['success'], 'learning': '#9B4DCA'}
        cat = task.get('category', 'work')
        tk.Label(meta, text=cat.capitalize(), font=('Segoe UI', 10),
                 bg=cat_colors.get(cat, COLORS['border']), fg='white',
                 padx=8, pady=2).pack(side=tk.LEFT)

        pri_colors = {'high': COLORS['danger'], 'medium': COLORS['accent'], 'low': COLORS['success']}
        pri = task.get('priority', 'medium')
        tk.Label(meta, text=f"● {pri.capitalize()}", font=('Segoe UI', 10),
                 bg=COLORS['card'], fg=pri_colors.get(pri, COLORS['muted'])).pack(side=tk.LEFT, padx=8)

        tk.Button(inner, text="🗑", font=('Segoe UI', 11),
                  bg=COLORS['card'], fg=COLORS['danger'], activebackground='#3D1515',
                  relief=tk.FLAT, cursor='hand2',
                  command=lambda tid=task['id']: self.delete_task(tid)).pack(side=tk.RIGHT)

    def toggle_task(self, task_id):
        for task in data_manager.data['tasks']:
            if task['id'] == task_id:
                task['done'] = not task['done']
                if task['done']:
                    data_manager.data['activity'][datetime.now().weekday()] += 1
                data_manager.save()
                break
        self.render_tasks()

    def delete_task(self, task_id):
        if messagebox.askyesno("Delete Task", "Are you sure you want to delete this task?"):
            data_manager.data['tasks'] = [t for t in data_manager.data['tasks'] if t['id'] != task_id]
            data_manager.save()
            self.render_tasks()

    def add_task_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Task")
        dialog.geometry("450x350")
        dialog.configure(bg=COLORS['card'])
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.winfo_rootx()+250, self.winfo_rooty()+150))

        frame = tk.Frame(dialog, bg=COLORS['card'], padx=28, pady=28)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="New Task", font=('Segoe UI', 18, 'bold'),
                 bg=COLORS['card'], fg=COLORS['fg']).pack(anchor='w', pady=(0, 20))

        tk.Label(frame, text="What needs to be done?", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        task_entry = tk.Entry(frame, font=('Segoe UI', 12), bg=COLORS['bg'],
                              fg=COLORS['fg'], insertbackground=COLORS['fg'],
                              relief=tk.FLAT, padx=12, pady=8)
        task_entry.pack(fill=tk.X, pady=(6, 16))
        task_entry.focus_set()

        tk.Label(frame, text="Category", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        cat_var = tk.StringVar(value='work')
        ttk.Combobox(frame, textvariable=cat_var,
                     values=['work', 'personal', 'health', 'learning'],
                     state='readonly', font=('Segoe UI', 11)).pack(fill=tk.X, pady=(6, 16))

        tk.Label(frame, text="Priority", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        pri_var = tk.StringVar(value='medium')
        ttk.Combobox(frame, textvariable=pri_var, values=['high', 'medium', 'low'],
                     state='readonly', font=('Segoe UI', 11)).pack(fill=tk.X, pady=(6, 20))

        btn_frame = tk.Frame(frame, bg=COLORS['card'])
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Cancel", font=('Segoe UI', 11),
                  bg=COLORS['bg'], fg=COLORS['fg2'], activebackground=COLORS['border'],
                  relief=tk.FLAT, cursor='hand2', command=dialog.destroy,
                  padx=16, pady=8).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(btn_frame, text="Add Task", font=('Segoe UI', 11, 'bold'),
                  bg=COLORS['accent'], fg=COLORS['bg'], activebackground=COLORS['accent2'],
                  relief=tk.FLAT, cursor='hand2',
                  command=lambda: self.save_new_task(
                      task_entry.get(), cat_var.get(), pri_var.get(), dialog),
                  padx=16, pady=8).pack(side=tk.RIGHT)

    def save_new_task(self, text, category, priority, dialog):
        if not text.strip():
            messagebox.showwarning("Warning", "Please enter a task description!")
            return
        data_manager.data['tasks'].insert(0, {
            'id': data_manager.get_next_id(),
            'text': text.strip(),
            'category': category,
            'priority': priority,
            'done': False,
            'created': str(datetime.now())
        })
        data_manager.save()
        dialog.destroy()
        self.render_tasks()

# ==================== NOTES VIEW ====================
class NotesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS['bg'])
        self.pack(fill=tk.BOTH, expand=True)
        self.note_colors = ['#4A9BD9', '#9B4DCA', '#3DB86A', '#D4943A', '#D94848', '#E8A838']
        self.create_ui()
        self.render_notes()

    def create_ui(self):
        header = tk.Frame(self, bg=COLORS['bg'])
        header.pack(fill=tk.X, pady=(0, 20))

        tk.Label(header, text="Notes", font=('Segoe UI', 24, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['fg']).pack(side=tk.LEFT)
        tk.Button(header, text="+ New Note", font=('Segoe UI', 11, 'bold'),
                  bg=COLORS['accent'], fg=COLORS['bg'], activebackground=COLORS['accent2'],
                  relief=tk.FLAT, cursor='hand2', command=self.add_note_dialog,
                  padx=16, pady=8).pack(side=tk.RIGHT)

        self.notes_grid = tk.Frame(self, bg=COLORS['bg'])
        self.notes_grid.pack(fill=tk.BOTH, expand=True)

    def render_notes(self):
        for w in self.notes_grid.winfo_children():
            w.destroy()
        notes = data_manager.data['notes']
        if not notes:
            tk.Label(self.notes_grid, text="📝 No notes yet. Create one to get started.",
                     font=('Segoe UI', 12), bg=COLORS['bg'], fg=COLORS['muted']).pack(pady=80)
            return
        for i, note in enumerate(notes):
            col = i % 3
            self.notes_grid.columnconfigure(col, weight=1)
            self.create_note_card(note, i // 3, col)

    def create_note_card(self, note, row, col):
        card = tk.Frame(self.notes_grid, bg=COLORS['card'], relief=tk.SOLID,
                        borderwidth=1, cursor='hand2')
        card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
        card.bind('<Button-1>', lambda e, n=note: self.edit_note_dialog(n))

        inner = tk.Frame(card, bg=COLORS['card'], padx=18, pady=18)
        inner.pack(fill=tk.BOTH, expand=True)

        hdr = tk.Frame(inner, bg=COLORS['card'])
        hdr.pack(fill=tk.X, pady=(0, 10))

        tk.Label(hdr, text="●", font=('Segoe UI', 12),
                 bg=COLORS['card'], fg=note.get('color', COLORS['accent'])).pack(side=tk.LEFT)
        tk.Label(hdr, text=note['title'], font=('Segoe UI', 14, 'bold'),
                 bg=COLORS['card'], fg=COLORS['fg']).pack(side=tk.LEFT, padx=8)
        tk.Button(hdr, text="🗑", font=('Segoe UI', 10),
                  bg=COLORS['card'], fg=COLORS['danger'], activebackground='#3D1515',
                  relief=tk.FLAT, cursor='hand2',
                  command=lambda n=note: self.delete_note(n)).pack(side=tk.RIGHT)

        content = note.get('content', '')
        preview = (content[:100] + '...') if len(content) > 100 else content
        tk.Label(inner, text=preview, font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['fg2'],
                 justify=tk.LEFT, anchor='nw', wraplength=250).pack(fill=tk.X)

        try:
            date_str = datetime.fromisoformat(note['created']).strftime("%b %d, %Y")
        except:
            date_str = note.get('created', '')
        tk.Label(inner, text=date_str, font=('Segoe UI', 9),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w', pady=(12, 0))

    def add_note_dialog(self, edit_note=None):
        dialog = tk.Toplevel(self)
        dialog.title("Edit Note" if edit_note else "New Note")
        dialog.geometry("500x450")
        dialog.configure(bg=COLORS['card'])
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.winfo_rootx()+200, self.winfo_rooty()+100))

        frame = tk.Frame(dialog, bg=COLORS['card'], padx=28, pady=28)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Edit Note" if edit_note else "New Note",
                 font=('Segoe UI', 18, 'bold'), bg=COLORS['card'],
                 fg=COLORS['fg']).pack(anchor='w', pady=(0, 20))

        tk.Label(frame, text="Note Title", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        title_entry = tk.Entry(frame, font=('Segoe UI', 12), bg=COLORS['bg'],
                               fg=COLORS['fg'], insertbackground=COLORS['fg'],
                               relief=tk.FLAT, padx=12, pady=8)
        title_entry.pack(fill=tk.X, pady=(6, 16))
        if edit_note:
            title_entry.insert(0, edit_note['title'])

        tk.Label(frame, text="Content", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        content_text = tk.Text(frame, font=('Segoe UI', 11), bg=COLORS['bg'],
                               fg=COLORS['fg'], insertbackground=COLORS['fg'],
                               relief=tk.FLAT, padx=12, pady=8, height=8)
        content_text.pack(fill=tk.X, pady=(6, 16))
        if edit_note:
            content_text.insert('1.0', edit_note.get('content', ''))

        tk.Label(frame, text="Color", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        colors_frame = tk.Frame(frame, bg=COLORS['card'])
        colors_frame.pack(fill=tk.X, pady=(6, 20))
        color_var = tk.StringVar(
            value=edit_note.get('color', self.note_colors[0]) if edit_note else self.note_colors[0])
        for c in self.note_colors:
            tk.Radiobutton(colors_frame, text="", value=c, variable=color_var,
                           bg=c, selectcolor=c, indicatoron=0,
                           width=3, height=1, activebackground=c).pack(side=tk.LEFT, padx=3)

        btn_frame = tk.Frame(frame, bg=COLORS['card'])
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Cancel", font=('Segoe UI', 11),
                  bg=COLORS['bg'], fg=COLORS['fg2'], activebackground=COLORS['border'],
                  relief=tk.FLAT, cursor='hand2', command=dialog.destroy,
                  padx=16, pady=8).pack(side=tk.RIGHT, padx=(8, 0))

        save_lbl = "Save Changes" if edit_note else "Create Note"
        tk.Button(btn_frame, text=save_lbl, font=('Segoe UI', 11, 'bold'),
                  bg=COLORS['accent'], fg=COLORS['bg'], activebackground=COLORS['accent2'],
                  relief=tk.FLAT, cursor='hand2',
                  command=lambda: self.save_note(
                      title_entry.get(), content_text.get('1.0', 'end').strip(),
                      color_var.get(), edit_note, dialog),
                  padx=16, pady=8).pack(side=tk.RIGHT)

    def edit_note_dialog(self, note):
        self.add_note_dialog(edit_note=note)

    def save_note(self, title, content, color, edit_note, dialog):
        if not title.strip():
            messagebox.showwarning("Warning", "Please enter a title!")
            return
        if edit_note:
            for n in data_manager.data['notes']:
                if n['id'] == edit_note['id']:
                    n.update({'title': title.strip(), 'content': content, 'color': color})
                    break
        else:
            data_manager.data['notes'].insert(0, {
                'id': data_manager.get_next_id(),
                'title': title.strip(),
                'content': content,
                'color': color,
                'created': str(datetime.now())
            })
        data_manager.save()
        dialog.destroy()
        self.render_notes()

    def delete_note(self, note):
        if messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?"):
            data_manager.data['notes'] = [n for n in data_manager.data['notes'] if n['id'] != note['id']]
            data_manager.save()
            self.render_notes()

# ==================== HABITS VIEW ====================
class HabitsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS['bg'])
        self.pack(fill=tk.BOTH, expand=True)
        self.habit_icons  = ['🧠','💪','📚','🚫','❤️','🌙','🍎','✏️','🎵','🚴']
        self.habit_colors = ['#4A9BD9','#9B4DCA','#3DB86A','#D4943A','#D94848','#E8A838','#3DB8B8','#BD4DA8']
        self.day_labels   = ['M','T','W','T','F','S','S']
        self.create_ui()
        self.render_habits()

    def create_ui(self):
        header = tk.Frame(self, bg=COLORS['bg'])
        header.pack(fill=tk.X, pady=(0, 20))

        tk.Label(header, text="Habits", font=('Segoe UI', 24, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['fg']).pack(side=tk.LEFT)
        tk.Button(header, text="+ Add Habit", font=('Segoe UI', 11, 'bold'),
                  bg=COLORS['accent'], fg=COLORS['bg'], activebackground=COLORS['accent2'],
                  relief=tk.FLAT, cursor='hand2', command=self.add_habit_dialog,
                  padx=16, pady=8).pack(side=tk.RIGHT)

        self.habits_list = tk.Frame(self, bg=COLORS['bg'])
        self.habits_list.pack(fill=tk.BOTH, expand=True)

    def render_habits(self):
        for w in self.habits_list.winfo_children():
            w.destroy()
        habits = data_manager.data['habits']
        if not habits:
            tk.Label(self.habits_list,
                     text="🔥 No habits tracked yet. Start building good routines.",
                     font=('Segoe UI', 12), bg=COLORS['bg'], fg=COLORS['muted']).pack(pady=80)
            return
        for habit in habits:
            self.create_habit_card(habit)

    def create_habit_card(self, habit):
        card = tk.Frame(self.habits_list, bg=COLORS['card'], relief=tk.SOLID, borderwidth=1)
        card.pack(fill=tk.X, pady=6)
        inner = tk.Frame(card, bg=COLORS['card'], padx=20, pady=16)
        inner.pack(fill=tk.X)

        hdr = tk.Frame(inner, bg=COLORS['card'])
        hdr.pack(fill=tk.X, pady=(0, 14))

        icon_frame = tk.Frame(hdr, bg=habit.get('color', COLORS['accent']), width=40, height=40)
        icon_frame.pack(side=tk.LEFT)
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text=habit.get('icon', '🎯'), font=('Segoe UI', 16),
                 bg=habit.get('color', COLORS['accent']), fg='white').pack(expand=True)

        tk.Label(hdr, text=habit['name'], font=('Segoe UI', 14, 'bold'),
                 bg=COLORS['card'], fg=COLORS['fg']).pack(side=tk.LEFT, padx=12)

        streak = sum(habit.get('days', [False]*7))
        tk.Label(hdr, text=f"{streak}/7 this week", font=('Segoe UI', 12),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(side=tk.LEFT, padx=8)

        tk.Button(hdr, text="🗑", font=('Segoe UI', 10),
                  bg=COLORS['card'], fg=COLORS['danger'], activebackground='#3D1515',
                  relief=tk.FLAT, cursor='hand2',
                  command=lambda h=habit: self.delete_habit(h)).pack(side=tk.RIGHT)

        days_frame = tk.Frame(inner, bg=COLORS['card'])
        days_frame.pack(fill=tk.X)

        for i, (dl, done) in enumerate(zip(self.day_labels, habit.get('days', [False]*7))):
            box = tk.Frame(days_frame, bg=COLORS['card'])
            box.pack(side=tk.LEFT, padx=4)
            tk.Label(box, text=dl, font=('Segoe UI', 9),
                     bg=COLORS['card'], fg=COLORS['muted']).pack()
            color = habit.get('color', COLORS['accent']) if done else COLORS['border']
            tk.Button(box, text="✓" if done else "", font=('Segoe UI', 10, 'bold'),
                      bg=color, fg='white' if done else color,
                      activebackground=habit.get('color', COLORS['accent']),
                      width=3, height=1, relief=tk.FLAT, cursor='hand2',
                      command=lambda h=habit, idx=i: self.toggle_day(h, idx)).pack(pady=(2, 0))

        prog_frame = tk.Frame(inner, bg=COLORS['card'])
        prog_frame.pack(fill=tk.X, pady=(12, 0))
        bar_bg = tk.Frame(prog_frame, bg=COLORS['border'], height=6)
        bar_bg.pack(fill=tk.X, expand=True)
        tk.Frame(bar_bg, bg=habit.get('color', COLORS['accent']), height=6).place(
            relx=0, rely=0, relwidth=streak/7, relheight=1)

    def toggle_day(self, habit, day_index):
        habit['days'][day_index] = not habit['days'][day_index]
        data_manager.save()
        self.render_habits()

    def delete_habit(self, habit):
        if messagebox.askyesno("Delete Habit", f"Are you sure you want to delete '{habit['name']}'?"):
            data_manager.data['habits'] = [h for h in data_manager.data['habits'] if h['id'] != habit['id']]
            data_manager.save()
            self.render_habits()

    def add_habit_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Habit")
        dialog.geometry("500x500")
        dialog.configure(bg=COLORS['card'])
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("+%d+%d" % (self.winfo_rootx()+200, self.winfo_rooty()+80))

        frame = tk.Frame(dialog, bg=COLORS['card'], padx=28, pady=28)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="New Habit", font=('Segoe UI', 18, 'bold'),
                 bg=COLORS['card'], fg=COLORS['fg']).pack(anchor='w', pady=(0, 20))

        tk.Label(frame, text="Habit Name (e.g., Meditate)", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        name_entry = tk.Entry(frame, font=('Segoe UI', 12), bg=COLORS['bg'],
                              fg=COLORS['fg'], insertbackground=COLORS['fg'],
                              relief=tk.FLAT, padx=12, pady=8)
        name_entry.pack(fill=tk.X, pady=(6, 16))
        name_entry.focus_set()

        tk.Label(frame, text="Icon", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        icons_frame = tk.Frame(frame, bg=COLORS['card'])
        icons_frame.pack(fill=tk.X, pady=(6, 16))
        icon_var = tk.StringVar(value=self.habit_icons[0])
        for icon in self.habit_icons:
            tk.Radiobutton(icons_frame, text=icon, value=icon, variable=icon_var,
                           bg=COLORS['bg'], selectcolor=COLORS['accent_dim'],
                           activebackground=COLORS['bg'], font=('Segoe UI', 14),
                           padx=8, pady=4).pack(side=tk.LEFT, padx=2)

        tk.Label(frame, text="Color", font=('Segoe UI', 11),
                 bg=COLORS['card'], fg=COLORS['muted']).pack(anchor='w')
        colors_frame = tk.Frame(frame, bg=COLORS['card'])
        colors_frame.pack(fill=tk.X, pady=(6, 20))
        color_var = tk.StringVar(value=self.habit_colors[0])
        for c in self.habit_colors:
            tk.Radiobutton(colors_frame, text="", value=c, variable=color_var,
                           bg=c, selectcolor=c, indicatoron=0,
                           width=3, height=1, activebackground=c).pack(side=tk.LEFT, padx=3)

        btn_frame = tk.Frame(frame, bg=COLORS['card'])
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Cancel", font=('Segoe UI', 11),
                  bg=COLORS['bg'], fg=COLORS['fg2'], activebackground=COLORS['border'],
                  relief=tk.FLAT, cursor='hand2', command=dialog.destroy,
                  padx=16, pady=8).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(btn_frame, text="Add Habit", font=('Segoe UI', 11, 'bold'),
                  bg=COLORS['accent'], fg=COLORS['bg'], activebackground=COLORS['accent2'],
                  relief=tk.FLAT, cursor='hand2',
                  command=lambda: self.save_habit(
                      name_entry.get(), icon_var.get(), color_var.get(), dialog),
                  padx=16, pady=8).pack(side=tk.RIGHT)

    def save_habit(self, name, icon, color, dialog):
        if not name.strip():
            messagebox.showwarning("Warning", "Please enter a habit name!")
            return
        data_manager.data['habits'].append({
            'id': data_manager.get_next_id(),
            'name': name.strip(),
            'icon': icon,
            'color': color,
            'days': [False] * 7
        })
        data_manager.save()
        dialog.destroy()
        self.render_habits()

# ==================== RUN APPLICATION ====================
if __name__ == "__main__":
    app = ZenithApp()

    def on_closing():
        data_manager.save()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()
