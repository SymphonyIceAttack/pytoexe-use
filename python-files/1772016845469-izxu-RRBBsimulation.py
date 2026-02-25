
import sys
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QLayout, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QTextEdit, QGridLayout, QFileDialog, QSizePolicy, QSplitter, QCheckBox, QLineEdit
)
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QFont, QIntValidator

class RouletteTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Roulette Tracker")
        self.setMinimumSize(640, 950)  # Increased height for additional controls
        
        # Data structures
        self.spin_history = []  # All spins in background
        self.repeat_history = []
        self.number_sequence = [str(i) for i in range(37)]
        self.spin_count = 0
        self.last_repeat_index = -1
        self.buttons = {}
        self.red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.black_numbers = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        
        # New variables for cycle length control
        self.max_cycle_length = None
        self.current_cycle_numbers = set()
        self.cycle_display_spins = []  # Only the limited set numbers to display in Spin Results
        
        # Hit counter for all numbers
        self.hit_counts = defaultdict(int)
        
        # Hit counter for numbers that win cycles
        self.cycle_win_counts = defaultdict(int)
        
        # List to track the most recent unique cycle winners (most recent first)
        self.recent_cycle_winners = []
        
        # Variables for series/cycle display mode
        self.show_series_mode = False  # False = normal mode, True = series mode
        
        # Filter for hit-based stream
        self.top_hits_limit = None  # None means show all
        self.hits_source = "all"  # "all", "cycle_wins", or "recent_cycle_wins"
        self.previous_top_numbers = set()  # Track previous top numbers for comparison
        self.notification_messages = []  # Store notification messages
        
        self.initUI()

    def initUI(self):
        self.setup_styles()
        main_layout = QVBoxLayout()
        main_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        
        # Cycle length control section
        cycle_control_layout = QHBoxLayout()
        
        self.cycle_checkbox = QCheckBox("Limit Cycle Length")
        self.cycle_checkbox.setStyleSheet("color: white; padding: 5px; font-family: 'Instraction'; font-size: 14px;")
        self.cycle_checkbox.stateChanged.connect(self.toggle_cycle_limit)
        cycle_control_layout.addWidget(self.cycle_checkbox)
        
        max_numbers_label = QLabel("Max Numbers:")
        max_numbers_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px;")
        cycle_control_layout.addWidget(max_numbers_label)
        
        self.cycle_length_input = QLineEdit()
        self.cycle_length_input.setValidator(QIntValidator(1, 36))
        self.cycle_length_input.setMaximumWidth(50)
        self.cycle_length_input.setText("3")
        self.cycle_length_input.setEnabled(False)
        self.cycle_length_input.setStyleSheet("font-family: 'Instraction'; font-size: 14px;")
        cycle_control_layout.addWidget(self.cycle_length_input)
        
        cycle_control_layout.addStretch(1)
        main_layout.addLayout(cycle_control_layout)
        
        # Top section: Number grid
        self.main_grid = self.create_number_grid()
        main_layout.addLayout(self.main_grid)
        
        # Middle section: Results and Repeats side by side
        results_repeats_layout = QHBoxLayout()
        
        # Spin results display (left)
        spin_results_layout = QVBoxLayout()
        self.results_label = QLabel("Spin Results:")
        self.results_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px; padding: 5px;")
        spin_results_layout.addWidget(self.results_label)
        self.results_box = QTextEdit()
        self.results_box.setReadOnly(True)
        self.results_box.setFont(QFont("Instraction", 12))
        self.results_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spin_results_layout.addWidget(self.results_box)
        
        # Repeat numbers display (right)
        repeat_layout = QVBoxLayout()
        self.repeat_label = QLabel("(Rp):")
        self.repeat_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px; padding: 5px;")
        repeat_layout.addWidget(self.repeat_label)
        self.repeat_box = QTextEdit()
        self.repeat_box.setReadOnly(True)
        self.repeat_box.setFont(QFont("Instraction", 12))
        self.repeat_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        repeat_layout.addWidget(self.repeat_box)
        
        results_repeats_layout.addLayout(spin_results_layout, 60)
        results_repeats_layout.addLayout(repeat_layout, 40)
        
        main_layout.addLayout(results_repeats_layout, 60)
        
        # Bottom section: Number sequence (original NS stream)
        sequence_layout = QVBoxLayout()
        self.sequence_label = QLabel("NS:")
        self.sequence_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px; padding: 5px;")
        sequence_layout.addWidget(self.sequence_label)
        self.sequence_box = QTextEdit()
        self.sequence_box.setReadOnly(True)
        self.sequence_box.setFont(QFont("Instraction", 12))
        self.sequence_box.setMaximumHeight(100)
        self.sequence_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sequence_layout.addWidget(self.sequence_box)
        
        main_layout.addLayout(sequence_layout, 10)
        
        # New section: Hit-based stream control
        hits_control_layout = QVBoxLayout()
        
        # First row: Source selection
        source_layout = QHBoxLayout()
        self.hits_label = QLabel("Hit-Based Stream:")
        self.hits_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px; padding: 5px;")
        source_layout.addWidget(self.hits_label)
        
        # Checkbox for most hit numbers (default)
        self.all_hits_checkbox = QCheckBox("Most Hit Numbers")
        self.all_hits_checkbox.setStyleSheet("color: white; padding: 5px; font-family: 'Instraction'; font-size: 14px;")
        self.all_hits_checkbox.setChecked(True)
        self.all_hits_checkbox.stateChanged.connect(lambda state: self.toggle_hits_source("all", state))
        source_layout.addWidget(self.all_hits_checkbox)
        
        # Checkbox for cycle wins mode
        self.cycle_wins_checkbox = QCheckBox("Based on Cycle Wins")
        self.cycle_wins_checkbox.setStyleSheet("color: white; padding: 5px; font-family: 'Instraction'; font-size: 14px;")
        self.cycle_wins_checkbox.stateChanged.connect(lambda state: self.toggle_hits_source("cycle_wins", state))
        source_layout.addWidget(self.cycle_wins_checkbox)
        
        # Checkbox for most recent cycle wins
        self.recent_cycle_wins_checkbox = QCheckBox("Most Recent Cycle Wins")
        self.recent_cycle_wins_checkbox.setStyleSheet("color: white; padding: 5px; font-family: 'Instraction'; font-size: 14px;")
        self.recent_cycle_wins_checkbox.stateChanged.connect(lambda state: self.toggle_hits_source("recent_cycle_wins", state))
        source_layout.addWidget(self.recent_cycle_wins_checkbox)
        
        source_layout.addStretch(1)
        hits_control_layout.addLayout(source_layout)
        
        # Second row: Filter controls
        filter_layout = QHBoxLayout()
        
        # Add checkbox to enable/disable the filter
        self.hits_filter_checkbox = QCheckBox("Show Top")
        self.hits_filter_checkbox.setStyleSheet("color: white; padding: 5px; font-family: 'Instraction'; font-size: 14px;")
        self.hits_filter_checkbox.stateChanged.connect(self.toggle_hits_filter)
        filter_layout.addWidget(self.hits_filter_checkbox)
        
        # Add input field for top N hits
        self.hits_filter_input = QLineEdit()
        self.hits_filter_input.setValidator(QIntValidator(1, 37))
        self.hits_filter_input.setMaximumWidth(50)
        self.hits_filter_input.setText("5")
        self.hits_filter_input.setEnabled(False)
        self.hits_filter_input.setStyleSheet("font-family: 'Instraction'; font-size: 14px;")
        self.hits_filter_input.textChanged.connect(self.update_hits_filter)
        filter_layout.addWidget(self.hits_filter_input)
        
        filter_layout.addStretch(1)
        hits_control_layout.addLayout(filter_layout)
        
        main_layout.addLayout(hits_control_layout)
        
        # Hit-based stream display
        hits_display_layout = QVBoxLayout()
        self.hits_box = QTextEdit()
        self.hits_box.setReadOnly(True)
        self.hits_box.setFont(QFont("Instraction", 12))
        self.hits_box.setMaximumHeight(100)
        self.hits_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hits_display_layout.addWidget(self.hits_box)
        
        main_layout.addLayout(hits_display_layout, 10)
        
        # Series display area
        series_layout = QVBoxLayout()
        self.series_label = QLabel("Series/Cycles:")
        self.series_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px; padding: 5px; color: #55AAFF;")
        series_layout.addWidget(self.series_label)
        
        self.series_box = QTextEdit()
        self.series_box.setReadOnly(True)
        self.series_box.setFont(QFont("Instraction", 12))
        self.series_box.setMaximumHeight(100)
        self.series_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.series_box.setStyleSheet("background-color: #2c2c2c; border: 1px solid #55AAFF;")
        series_layout.addWidget(self.series_box)
        
        main_layout.addLayout(series_layout, 10)
        
        # Notification area for hits stream changes
        notification_layout = QVBoxLayout()
        self.notification_label = QLabel("Stream Changes:")
        self.notification_label.setStyleSheet("font-family: 'Instraction'; font-size: 14px; padding: 5px; color: #FFFF00;")
        notification_layout.addWidget(self.notification_label)
        
        self.notification_box = QTextEdit()
        self.notification_box.setReadOnly(True)
        self.notification_box.setFont(QFont("Instraction", 12))
        self.notification_box.setMaximumHeight(60)
        self.notification_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.notification_box.setStyleSheet("background-color: #2c2c2c; color: #FFFF00; border: 1px solid #FFFF00;")
        notification_layout.addWidget(self.notification_box)
        
        main_layout.addLayout(notification_layout, 8)
        
        # Control buttons at the very bottom
        control_layout = QHBoxLayout()
        self.setup_controls(control_layout)
        main_layout.addLayout(control_layout)
        
        self.setLayout(main_layout)
        self.update_sequence_display()
        self.update_hits_stream()

    def toggle_hits_source(self, source, state):
        """Toggle between different hit sources."""
        if state == Qt.Checked:
            # Uncheck other checkboxes
            if source == "all":
                self.cycle_wins_checkbox.setChecked(False)
                self.recent_cycle_wins_checkbox.setChecked(False)
                self.hits_source = "all"
                self.hits_label.setText("Hit-Based Stream:")
            elif source == "cycle_wins":
                self.all_hits_checkbox.setChecked(False)
                self.recent_cycle_wins_checkbox.setChecked(False)
                self.hits_source = "cycle_wins"
                self.hits_label.setText("Cycle Win Stream:")
            elif source == "recent_cycle_wins":
                self.all_hits_checkbox.setChecked(False)
                self.cycle_wins_checkbox.setChecked(False)
                self.hits_source = "recent_cycle_wins"
                self.hits_label.setText("Recent Cycle Wins Stream:")
            
            # Clear previous tracking when changing mode
            self.previous_top_numbers = set()
            self.update_hits_stream()
        else:
            # If unchecking the current source, revert to "all"
            if self.hits_source == source:
                self.all_hits_checkbox.setChecked(True)
                self.hits_source = "all"
                self.hits_label.setText("Hit-Based Stream:")
                self.previous_top_numbers = set()
                self.update_hits_stream()

    def toggle_hits_filter(self, state):
        """Enable/disable the hits filter input based on checkbox state."""
        if state == Qt.Checked:
            self.hits_filter_input.setEnabled(True)
            try:
                self.top_hits_limit = int(self.hits_filter_input.text())
                if self.top_hits_limit < 1:
                    self.top_hits_limit = 5
                    self.hits_filter_input.setText("5")
            except:
                self.top_hits_limit = 5
                self.hits_filter_input.setText("5")
        else:
            self.hits_filter_input.setEnabled(False)
            self.top_hits_limit = None
        
        # Clear previous tracking when toggling filter
        self.previous_top_numbers = set()
        self.update_hits_stream()

    def update_hits_filter(self):
        """Update the hits filter when the input value changes."""
        if self.hits_filter_checkbox.isChecked():
            try:
                self.top_hits_limit = int(self.hits_filter_input.text())
                if self.top_hits_limit < 1:
                    self.top_hits_limit = 5
                    self.hits_filter_input.setText("5")
            except:
                self.top_hits_limit = 5
                self.hits_filter_input.setText("5")
            # Clear previous tracking when filter value changes
            self.previous_top_numbers = set()
            self.update_hits_stream()

    def show_notification(self, message):
        """Show a notification message in the notification box."""
        self.notification_messages.append(message)
        
        # Keep only last 3 messages
        if len(self.notification_messages) > 3:
            self.notification_messages.pop(0)
        
        # Display all messages
        self.notification_box.setText("\n".join(self.notification_messages))
        
        # Clear notification after 5 seconds
        QTimer.singleShot(5000, self.clear_notification)

    def clear_notification(self):
        """Clear the notification box."""
        self.notification_messages = []
        self.notification_box.clear()

    def get_number_color_html(self, num_str, count=None):
        """Get HTML formatted number with proper color."""
        num = int(num_str)
        
        # Determine color based on number
        if num in self.red_numbers:
            bg_color = "#FF3300"
            text_color = "white"
        elif num in self.black_numbers:
            bg_color = "#000000"
            text_color = "white"
        else:  # 0
            bg_color = "#99FF99"
            text_color = "black"
        
        # Format the number with or without count
        if count is not None:
            return (f'<span style="background-color: {bg_color}; color: {text_color}; '
                    f'border-radius: 4px; padding: 2px 4px; margin: 1px; '
                    f'font-family: Instraction; font-size: 14px; display: inline-block;">'
                    f'{num}<sub style="font-size: 18px;">-{count}</sub></span>')
        else:
            return (f'<span style="background-color: {bg_color}; color: {text_color}; '
                    f'border-radius: 4px; padding: 2px 4px; margin: 1px; '
                    f'font-family: Instraction; font-size: 14px; display: inline-block;">'
                    f'{num}</span>')

    def update_hits_stream(self):
        """Update the hit-based stream with numbers ordered by selected source."""
        # Get the appropriate data based on mode
        if self.hits_source == "cycle_wins":
            # Get cycle win counts (sorted by count)
            counts_dict = self.cycle_win_counts
            source_name = "Cycle Wins"
            sorted_items = sorted(counts_dict.items(), key=lambda x: x[1], reverse=True)
            
        elif self.hits_source == "recent_cycle_wins":
            # Get most recent cycle winners (most recent first)
            source_name = "Recent Cycle Wins"
            
            # The recent_cycle_winners list is already in most-recent-first order
            # and maintains the fixed-size unique winners
            display_items = []
            for idx, num in enumerate(self.recent_cycle_winners):
                # For display, we show position number (starting from 1)
                display_items.append((num, idx + 1))
            
            sorted_items = display_items
            
        else:  # "all"
            counts_dict = self.hit_counts
            source_name = "Hits"
            sorted_items = sorted(counts_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Get current top numbers
        if self.top_hits_limit is not None:
            current_top = set(num for num, _ in sorted_items[:self.top_hits_limit])
            current_display = sorted_items[:self.top_hits_limit]
        else:
            current_top = set(num for num, _ in sorted_items)
            current_display = sorted_items
        
        # Check for changes if filter is enabled and we have previous data
        if (self.top_hits_limit is not None and 
            self.previous_top_numbers and 
            current_top != self.previous_top_numbers):
            
            # Find what was added
            added_numbers = current_top - self.previous_top_numbers
            # Find what was removed
            removed_numbers = self.previous_top_numbers - current_top
            
            # Show notifications for changes
            if added_numbers:
                added_html = []
                for num in added_numbers:
                    for num_str, count in sorted_items:
                        if num_str == num:
                            if self.hits_source == "recent_cycle_wins":
                                # Show position instead of count for recent wins
                                added_html.append(self.get_number_color_html(num_str))
                            else:
                                added_html.append(self.get_number_color_html(num_str, count))
                            break
                self.show_notification(f"ADDED ({source_name}): {' '.join(added_html)}")
            
            if removed_numbers:
                removed_html = []
                for num in removed_numbers:
                    if self.hits_source == "recent_cycle_wins":
                        removed_html.append(self.get_number_color_html(num))
                    else:
                        # Find the count before removal
                        counts_dict = self.cycle_win_counts if self.hits_source == "cycle_wins" else self.hit_counts
                        for num_str, count in counts_dict.items():
                            if num_str == num:
                                removed_html.append(self.get_number_color_html(num_str, count))
                                break
                self.show_notification(f"REMOVED ({source_name}): {' '.join(removed_html)}")
        
        # Update previous top numbers
        if self.top_hits_limit is not None:
            self.previous_top_numbers = current_top
        
        # Generate HTML for display
        html_text = []
        if self.hits_source == "recent_cycle_wins":
            # For recent cycle wins, show with position number
            for idx, (num_str, position) in enumerate(current_display):
                html_text.append(f'<span style="font-family: Instraction; font-size: 14px; margin: 1px;">'
                               f'<span style="color: #888888;">{position}.</span> '
                               f'{self.get_number_color_html(num_str)}</span>')
        else:
            # For other modes, show with count
            for num_str, count in current_display:
                html_text.append(self.get_number_color_html(num_str, count))
        
        if html_text:
            self.hits_box.setHtml(" ".join(html_text))
        else:
            self.hits_box.setHtml(f"<span style='color: #888888; font-family: Instraction;'>No {source_name.lower()} yet</span>")

    def toggle_cycle_limit(self, state):
        """Enable/disable the cycle length input based on checkbox state."""
        if state == Qt.Checked:
            self.cycle_length_input.setEnabled(True)
            try:
                self.max_cycle_length = int(self.cycle_length_input.text())
                if self.max_cycle_length < 1:
                    self.max_cycle_length = 3
                    self.cycle_length_input.setText("3")
            except:
                self.max_cycle_length = 3
                self.cycle_length_input.setText("3")
        else:
            self.cycle_length_input.setEnabled(False)
            self.max_cycle_length = None
        
        self.reset_system()

    def setup_styles(self):
        """Configure the UI stylesheet for a professional dark theme."""
        self.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: white;
                font-family: 'Instraction';
                font-size: 14px;
            }
            QTextEdit {
                background-color: #2c2c2c;
                border: 0px solid #444444;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Instraction';
                font-size: 14px;
            }
            QPushButton {
                background-color: #333333;
                border: 0px solid #444444;
                border-radius: 4px;
                padding: 3px;
                min-width: 30px;
                min-height: 30px;
                font-family: 'Instraction';
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLabel {
                padding: 2px;
                font-family: 'Instraction';
                font-size: 14px;
            }
            QCheckBox {
                spacing: 5px;
                font-family: 'Instraction';
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #444444;
                background-color: #2c2c2c;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #444444;
                background-color: #55AAFF;
            }
            QLineEdit {
                background-color: #2c2c2c;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 2px 5px;
                color: white;
                font-family: 'Instraction';
                font-size: 14px;
            }
        """)

    def create_number_grid(self):
        """Create a number grid for inputting spins."""
        grid = QGridLayout()
        number_layout = [
            [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
        ]

        for row_idx, row in enumerate(number_layout):
            for col_idx, number in enumerate(row):
                btn = QPushButton(str(number))
                btn.setFixedSize(QSize(50, 40))
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                btn.setFont(QFont("Instraction", 12))
                self.set_button_color(btn, number)
                btn.clicked.connect(lambda checked, n=number: self.add_result(n))
                self.buttons[number] = btn
                grid.addWidget(btn, row_idx, col_idx + 1)

        zero_btn = QPushButton("0")
        zero_btn.setFixedSize(QSize(50, 40))
        zero_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        zero_btn.setStyleSheet("background-color: #99FF99; color: black; font-family: 'Instraction'; font-size: 14px;")
        zero_btn.clicked.connect(lambda: self.add_result(0))
        self.buttons[0] = zero_btn
        grid.addWidget(zero_btn, 0, 0, 3, 1)

        return grid

    def set_button_color(self, btn, number):
        """Set button color based on number (red, black, or green for zero)."""
        if number in self.red_numbers:
            btn.setStyleSheet("background-color: #FF3300; color: white; font-family: 'Instraction'; font-size: 14px;")
        elif number in self.black_numbers:
            btn.setStyleSheet("background-color: #000000; color: white; font-family: 'Instraction'; font-size: 14px;")
        else:
            btn.setStyleSheet("background-color: #99FF99; color: black; font-family: 'Instraction'; font-size: 14px;")

    def setup_controls(self, layout):
        """Set up control buttons."""
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_system)
        reset_btn.setStyleSheet("background-color: #FF5555; font-family: 'Instraction'; font-size: 14px;")
        layout.addWidget(reset_btn)
        
        # Show Series button
        self.series_btn = QPushButton("Show Series")
        self.series_btn.clicked.connect(self.toggle_series_mode)
        self.series_btn.setStyleSheet("background-color: #55AAFF; font-family: 'Instraction'; font-size: 14px;")
        layout.addWidget(self.series_btn)
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_spins)
        import_btn.setStyleSheet("background-color: #55AAFF; font-family: 'Instraction'; font-size: 14px;")
        layout.addWidget(import_btn)
        
        layout.addStretch(1)

    def toggle_series_mode(self):
        """Toggle between normal display and series/cycle display."""
        try:
            self.show_series_mode = not self.show_series_mode
            
            if self.show_series_mode:
                self.series_btn.setText("Hide Series")
                self.series_btn.setStyleSheet("background-color: #FFAA55; font-family: 'Instraction'; font-size: 14px;")
                self.update_series_display()
            else:
                self.series_btn.setText("Show Series")
                self.series_btn.setStyleSheet("background-color: #55AAFF; font-family: 'Instraction'; font-size: 14px;")
                self.series_box.clear()
        except Exception as e:
            print(f"Error in toggle_series_mode: {e}")

    def update_series_display(self):
        """Update the series/cycle display with the Tkinter logic."""
        try:
            if not self.show_series_mode:
                return
                
            if not self.spin_history:
                self.series_box.setText("=== SERIES/CYCLE DISPLAY ===\n\nNo outcomes yet.")
                return
            
            # Simple implementation matching Tkinter logic
            outcomes = self.spin_history.copy()
            series_list = []
            current_series = []
            series_count = 0
            
            for i, num in enumerate(outcomes):
                current_series.append(num)
                
                # Check if current number repeats in the current series
                if len(current_series) > 1:
                    # Check all positions except the last one
                    for j in range(len(current_series) - 1):
                        if current_series[j] == num:  # Found a repeat
                            # Get the series between the two occurrences
                            series_between = current_series[j+1:-1]
                            if series_between:
                                series_count += 1
                                unique_count = len(set(series_between))
                                series_list.append(f"Series {series_count}: {series_between}, Unique count: {unique_count}")
                            
                            # Reset current_series to start from the repeated number
                            current_series = [num]
                            break
            
            # Build display text
            display_text = "=== SERIES/CYCLE DISPLAY ===\n\n"
            
            if series_list:
                for series in series_list:
                    display_text += series + "\n"
            
            # Show current incomplete series
            if current_series:
                # Show all but the last number (matching Tkinter behavior)
                if len(current_series) > 1:
                    current_display = current_series[:-1]
                else:
                    current_display = current_series
                
                if current_display:
                    display_text += f"\nCurrent outcomes: {current_display}\n"
            
            if not series_list and not current_series:
                display_text += "No outcomes yet.\n"
            elif not series_list and current_series:
                display_text += "No complete series yet.\n"
            
            self.series_box.setText(display_text)
            
        except Exception as e:
            print(f"Error in update_series_display: {e}")
            self.series_box.setText(f"Error displaying series. Please check console for details.")

    def add_result(self, number):
        """Add a spin result and update all displays."""
        try:
            self.spin_count += 1
            number_str = str(number)
            
            # Update hit counts
            self.hit_counts[number_str] += 1
            
            # Always track ALL spins in background
            self.spin_history.append(number_str)
            
            # Track if this spin ends a cycle (winning number)
            ends_cycle = False
            
            if self.max_cycle_length is not None:
                ends_cycle = self.handle_limited_cycle_logic(number_str)
            else:
                # Original logic
                start_index = self.last_repeat_index + 1 if self.last_repeat_index >= 0 else 0
                if number_str in self.spin_history[start_index:-1]:
                    ends_cycle = True
                    self.repeat_history.append(number_str)
                    self.last_repeat_index = len(self.spin_history) - 1
                    self.number_sequence = [number_str]
                    self.cycle_display_spins = [number_str]
                else:
                    if number_str in self.number_sequence:
                        self.number_sequence.remove(number_str)
                    self.number_sequence.insert(0, number_str)
                    self.cycle_display_spins.insert(0, number_str)
            
            # If this spin ends a cycle, update cycle win counts
            if ends_cycle:
                self.cycle_win_counts[number_str] += 1
                
                # Update most recent cycle winners list
                self.update_recent_cycle_winners(number_str)
            
            self.update_results_display()
            self.update_repeat_display()
            self.update_sequence_display()
            self.update_hits_stream()  # Update the new hits stream
            
            # Update series display if in series mode
            if self.show_series_mode:
                self.update_series_display()
            
        except Exception as e:
            print(f"Error adding result for number {number}: {e}")

    def update_recent_cycle_winners(self, number_str):
        """Update the list of most recent unique cycle winners."""
        # Check if the number is already in the list
        if number_str in self.recent_cycle_winners:
            # Remove it from its current position
            self.recent_cycle_winners.remove(number_str)
        
        # Add it to the front (most recent)
        self.recent_cycle_winners.insert(0, number_str)
        
        # If we have a limit and the list is too long, remove the oldest
        if self.top_hits_limit is not None and len(self.recent_cycle_winners) > self.top_hits_limit:
            # Remove the last (oldest) element
            self.recent_cycle_winners.pop()

    def handle_limited_cycle_logic(self, number_str):
        """Handle the logic when cycle length limiting is enabled.
        Returns True if this spin ends a cycle (winning number)."""
        current_cycle_start = self.last_repeat_index + 1 if self.last_repeat_index >= 0 else 0
        current_cycle_spins = self.spin_history[current_cycle_start:]
        
        # If this is the start of a new cycle
        if len(current_cycle_spins) == 1:
            self.current_cycle_numbers = {number_str}
            self.number_sequence = [number_str]
            self.cycle_display_spins = [number_str]
            return False
        
        # Check if current number is in our limited cycle set
        if number_str in self.current_cycle_numbers:
            # REPEAT FOUND - end cycle
            self.repeat_history.append(number_str)
            self.last_repeat_index = len(self.spin_history) - 1
            self.number_sequence = [number_str]
            self.current_cycle_numbers = {number_str}
            self.cycle_display_spins = [number_str]
            return True
        else:
            # No repeat - check if we can add to limited set
            if len(self.current_cycle_numbers) < self.max_cycle_length:
                # Add to limited set (cycle is not full yet)
                self.current_cycle_numbers.add(number_str)
                if number_str in self.number_sequence:
                    self.number_sequence.remove(number_str)
                self.number_sequence.insert(0, number_str)
                self.cycle_display_spins.insert(0, number_str)
            else:
                # Cycle is full - don't add to limited set or display
                # Just track in background but don't show in Spin Results
                pass
            return False

    def update_results_display(self):
        """Update the spin results column with ONLY limited set numbers."""
        output = []
        current_cycle_start = 0
        
        for i, num in enumerate(self.spin_history):
            cycle_end = False
            
            if i > current_cycle_start:
                if self.max_cycle_length is not None:
                    # For limited cycles, only show numbers that are in the limited set
                    # Check if this number should end the cycle (is in limited set and repeats)
                    current_cycle_display = []
                    limited_set = set()
                    
                    # Reconstruct what was displayed in this cycle
                    j = current_cycle_start
                    while j < i and len(limited_set) < self.max_cycle_length:
                        spin_num = self.spin_history[j]
                        if spin_num not in limited_set:
                            limited_set.add(spin_num)
                            current_cycle_display.append(spin_num)
                        j += 1
                    
                    # Check if current number is in the limited set AND appears again
                    if num in limited_set and num in self.spin_history[current_cycle_start:i]:
                        cycle_end = True
                
                else:
                    # Original logic
                    if num in self.spin_history[current_cycle_start:i]:
                        cycle_end = True
            
            if cycle_end:
                output.append(f"Y\t{num}")
                current_cycle_start = i
            else:
                # Only show numbers that were in the limited set at that time
                if self.max_cycle_length is not None:
                    # Determine if this number was in the limited set when it was spun
                    limited_set_at_time = set()
                    k = current_cycle_start
                    while k <= i and len(limited_set_at_time) < self.max_cycle_length:
                        limited_set_at_time.add(self.spin_history[k])
                        k += 1
                    
                    if num in limited_set_at_time:
                        output.append(f"\t{num}")
                    # Don't show numbers that weren't in the limited set
                else:
                    output.append(f"\t{num}")
                
        self.results_box.setText("\n".join(output))
        self.results_box.verticalScrollBar().setValue(self.results_box.verticalScrollBar().maximum())

    def update_repeat_display(self):
        """Update the repeated numbers (Rp) column with repeat indicators and counter."""
        output = []
        seen_numbers = set()
        last_18 = self.number_sequence[:18]
        number_counts = defaultdict(int)
        for num in last_18:
            number_counts[num] += 1
        
        for num in self.repeat_history:
            count = number_counts[num]
            if num in seen_numbers:
                output.append(f"Y\t{num}\t[{count}]")
            else:
                output.append(f"\t{num}\t[{count}]")
                seen_numbers.add(num)
        self.repeat_box.setText("\n".join(output))
        self.repeat_box.verticalScrollBar().setValue(self.repeat_box.verticalScrollBar().maximum())

    def update_sequence_display(self):
        """Update the number sequence display with colored numbers."""
        html_text = []
        for num in self.number_sequence:
            num_int = int(num)
            if num in self.repeat_history:
                color = "#FFFF00"
                text_color = "black"
            elif num_int in self.red_numbers:
                color = "#FF3300"
                text_color = "white"
            elif num_int in self.black_numbers:
                color = "#000000"
                text_color = "white"
            else:
                color = "#99FF99"
                text_color = "black"
            html_text.append(f'<span style="color: {color}; background-color: {color}; border-radius: 4px; padding: 2px; margin: 2px; color: {text_color}; font-family: Instraction; font-size: 14px;">{num}</span>')
        self.sequence_box.setHtml(" ".join(html_text))

    def import_spins(self):
        """Import spin history from a text file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Spin History",
            "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    spins = [int(line.strip()) for line in file if line.strip().isdigit()]
                    self.reset_system()
                    for number in spins:
                        self.add_result(number)
            except Exception as e:
                print(f"Error importing spins: {e}")

    def reset_system(self):
        """Reset all data and displays."""
        self.spin_history = []
        self.repeat_history = []
        self.number_sequence = [str(i) for i in range(37)]
        self.spin_count = 0
        self.last_repeat_index = -1
        self.current_cycle_numbers = set()
        self.cycle_display_spins = []
        self.hit_counts.clear()  # Clear hit counts
        self.cycle_win_counts.clear()  # Clear cycle win counts
        self.recent_cycle_winners.clear()  # Clear recent cycle winners
        self.previous_top_numbers = set()  # Clear previous tracking
        self.show_series_mode = False  # Reset to normal mode
        self.series_btn.setText("Show Series")
        self.series_btn.setStyleSheet("background-color: #55AAFF; font-family: 'Instraction'; font-size: 14px;")
        self.clear_notification()  # Clear notifications
        self.results_box.clear()
        self.repeat_box.clear()
        self.series_box.clear()  # Clear series display
        self.update_sequence_display()
        self.update_hits_stream()  # Update hits stream after reset

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tracker = RouletteTracker()
    tracker.show()
    sys.exit(app.exec_())
