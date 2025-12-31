import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import struct
import webbrowser

file_path = None
is_fullscreen = False

# ============================================
# EASILY EDITABLE OFFSET CONFIGURATION SECTION
# ============================================

# All 9042 position offsets
POSITION_OFFSETS_9042 = [
    ["ClassOverlay X", 0xBD4],
    ["ClassOverlay Y", 0xBD8],
    ["Glint X", 0xD3C],
    ["Glint Y", 0xD40],
    ["Top X", 0xDDC],
    ["Top Y", 0xDE0],
    ["Main X", 0xE2C],
    ["Main Y", 0xE30],
    ["Text X", 0xE7C],
    ["Text Y", 0xE80],
    ["League X", 0xECC],
    ["League Y", 0xED0],
    ["Text2 X", 0xF1C],
    ["Text2 Y", 0xF20],
    ["League2 X", 0xF6C],
    ["League2 Y", 0xF70],
    ["Text3 X", 0xFBC],
    ["Text3 Y", 0xFC0],
    ["TextStadium X", 0x100C],
    ["TextStadium Y", 0x1010],
    ["TextAway X", 0x105C],
    ["TextAway Y", 0x1060],
    ["TextHome X", 0x10AC],
    ["TextHome Y", 0x10B0],
    ["Panel X", 0x10FC],
    ["Panel Y", 0x1100],
    ["VS X", 0x114C],
    ["VS Y", 0x1150],
    ["Texts X", 0x119C],
    ["Texts Y", 0x11A0],
    ["CrestLoaderHome X", 0x11EC],
    ["CrestLoaderHome Y", 0x11F0],
    ["CrestLoaderAway X", 0x123C],
    ["CrestLoaderAway Y", 0x1240],
]

# All 9003 position offsets
POSITION_OFFSETS_9003 = [
    ["ClassOverlay X", 0x124C],
    ["ClassOverlay Y", 0x1250],
    ["redHome0 X", 0x1B3C],
    ["redHome0 Y", 0x1B40],
    ["redHome1 X", 0x1B8C],
    ["redHome1 Y", 0x1B90],
    ["redHome2 X", 0x1BDC],
    ["redHome2 Y", 0x1BE0],
    ["redHome3 X", 0x1C2C],
    ["redHome3 Y", 0x1C30],
    ["redHome4 X", 0x1C7C],
    ["redHome4 Y", 0x1C80],
    ["redHome5 X", 0x1CCC],
    ["redHome5 Y", 0x1CD0],
    ["redAway5 X", 0x1D1C],
    ["redAway5 Y", 0x1D20],
    ["redAway4 X", 0x1D6C],
    ["redAway4 Y", 0x1D70],
    ["redAway3 X", 0x1DBC],
    ["redAway3 Y", 0x1DC0],
    ["redAway2 X", 0x1E0C],
    ["redAway2 Y", 0x1E10],
    ["redAway1 X", 0x1E5C],
    ["redAway1 Y", 0x1E60],
    ["redAway0 X", 0x1EAC],
    ["redAway0 Y", 0x1EB0],
    ["greenHome0 X", 0x1EFC],
    ["greenHome0 Y", 0x1F00],
    ["greenHome1 X", 0x1F4C],
    ["greenHome1 Y", 0x1F50],
    ["greenHome2 X", 0x1F9C],
    ["greenHome2 Y", 0x1FA0],
    ["greenHome3 X", 0xF93],
    ["greenHome3 Y", 0xF97],
    ["greenHome4 X", 0x203C],
    ["greenHome4 Y", 0x2040],
    ["greenHome5 X", 0x208C],
    ["greenHome5 Y", 0x2090],
    ["greenAway5 X", 0x20DC],
    ["greenAway5 Y", 0x20E0],
    ["greenAway4 X", 0x212C],
    ["greenAway4 Y", 0x2130],
    ["greenAway3 X", 0x217C],
    ["greenAway3 Y", 0x2180],
    ["greenAway2 X", 0x21CC],
    ["greenAway2 Y", 0x21D0],
    ["greenAway1 X", 0x221C],
    ["greenAway1 Y", 0x2220],
    ["greenAway0 X", 0x226C],
    ["greenAway0 Y", 0x2270],
    ["CrestLoaderHome X", 0x253C],
    ["CrestLoaderHome Y", 0x2540],
    ["CrestLoaderAway X", 0x18B],
    ["CrestLoaderAway Y", 0x18F],
    ["TeamBacking X", 0x25DC],
    ["TeamBacking Y", 0x25E0],
    ["ScoreBacking X", 0x262C],
    ["ScoreBacking Y", 0x2630],
    ["Content X", 0x267C],
    ["Content Y", 0x2680],
]

# All 6073 position offsets
POSITION_OFFSETS_6073 = [
    ["ClassOverlay X", 0x674],
    ["ClassOverlay Y", 0x678],
    ["ArrowIn X", 0x794],
    ["ArrowIn Y", 0x798],
    ["ArrowOut X", 0x7E4],
    ["ArrowOut Y", 0x7E8],
    ["Title X", 0x834],
    ["Title Y", 0x838],
    ["PlayerNameIn X", 0x884],
    ["PlayerNameIn Y", 0x888],
    ["PlayerNameOut X", 0x8D4],
    ["PlayerNameOut Y", 0x8D8],
]

# All 9044 position offsets
POSITION_OFFSETS_9044 = [
    ["ClassOverlay X", 0x664],
    ["ClassOverlay Y", 0x668],
    ["MainCommentator X", 0x734],
    ["MainCommentator Y", 0x738],
    ["ColourCommentator X", 0x784],
    ["ColourCommentator Y", 0x788],
    ["SlideUp X", 0x8C4],
    ["SlideUp Y", 0x8C8],
    ["Content X", 0x914],
    ["Content Y", 0x918],
    ["ScorelineBg X", 0x964],
    ["ScorelineBg Y", 0x968],
]

# All 6072 position offsets
POSITION_OFFSETS_6072 = [
    ["ClassOverlay X", 0x5EC],
    ["ClassOverlay Y", 0x5F0],
    ["InjuryIcon X", 0x6BC],
    ["InjuryIcon Y", 0x6C0],
    ["YellowCardIcon X", 0x70C],
    ["YellowCardIcon Y", 0x710],
    ["RedCardIcon X", 0x75C],
    ["RedCardIcon Y", 0x760],
    ["YellowToRedCardIcon X", 0x7AC],
    ["YellowToRedCardIcon Y", 0x7B0],
    ["GoalIcon X", 0x7FC],
    ["GoalIcon Y", 0x800],
    ["PlayerName X", 0x84C],
    ["PlayerName Y", 0x850],
    ["EventIconWrapper X", 0x89C],
    ["EventIconWrapper Y", 0x8A0],
    ["SecondaryMessage X", 0x8EC],
    ["SecondaryMessage Y", 0x8F0],
]

# All 9018 position offsets
POSITION_OFFSETS_9018 = [
    ["ClassOverlay X", 0x1734],
    ["ClassOverlay Y", 0x1738],
    ["ShirtLoader X", 0x1AC4],
    ["ShirtLoader Y", 0x1AC8],
    ["Pitch X", 0x1BB4],
    ["Pitch Y", 0x1BB8],
    ["Player10 X", 0x1C04],
    ["Player10 Y", 0x1C08],
    ["Player9 X", 0x1C54],
    ["Player9 Y", 0x1C58],
    ["Player8 X", 0x1CA4],
    ["Player8 Y", 0x1CA8],
    ["Player7 X", 0x1CF4],
    ["Player7 Y", 0x1CF8],
    ["Player6 X", 0x1D44],
    ["Player6 Y", 0x1D48],
    ["Player5 X", 0x1D94],
    ["Player5 Y", 0x1D98],
    ["Player4 X", 0x1DE4],
    ["Player4 Y", 0x1DE8],
    ["Player3 X", 0x1E34],
    ["Player3 Y", 0x1E38],
    ["Player2 X", 0x1E84],
    ["Player2 Y", 0x1E88],
    ["Player1 X", 0x1ED4],
    ["Player1 Y", 0x1ED8],
    ["Player0 X", 0x1F24],
    ["Player0 Y", 0x1F28],
    ["Sub11 X", 0x1FC4],
    ["Sub11 Y", 0x1FC8],
    ["Sub14 X", 0x2014],
    ["Sub14 Y", 0x2018],
    ["Sub15 X", 0x2064],
    ["Sub15 Y", 0x2068],
    ["Sub16 X", 0x20B4],
    ["Sub16 Y", 0x20B8],
    ["Sub17 X", 0x2104],
    ["Sub17 Y", 0x2108],
    ["Sub13 X", 0x2154],
    ["Sub13 Y", 0x2158],
    ["Sub12 X", 0x21A4],
    ["Sub12 Y", 0x21A8],
    ["Subs X", 0x21F4],
    ["Subs Y", 0x21F8],
    ["Panel X", 0x22E4],
    ["Panel Y", 0x22E8],
    ["FormationsContent X", 0x2334],
    ["FormationsContent Y", 0x2338],
    ["SubContents X", 0x2384],
    ["SubContents Y", 0x2388],
    ["Row0 X", 0x23D4],
    ["Row0 Y", 0x23D8],
    ["Row1 X", 0x2424],
    ["Row1 Y", 0x2428],
    ["Row2 X", 0x2474],
    ["Row2 Y", 0x2478],
    ["Row3 X", 0x24C4],
    ["Row3 Y", 0x24C8],
    ["Row4 X", 0x2514],
    ["Row4 Y", 0x2518],
    ["Row5 X", 0x2564],
    ["Row5 Y", 0x2568],
    ["Row6 X", 0x25B4],
    ["Row6 Y", 0x25B8],
    ["Row7 X", 0x2604],
    ["Row7 Y", 0x2608],
    ["Row8 X", 0x2654],
    ["Row8 Y", 0x2658],
    ["Row9 X", 0x26A4],
    ["Row9 Y", 0x26A8],
    ["Row10 X", 0x26F4],
    ["Row10 Y", 0x26F8],
    ["Mask X", 0x2744],
    ["Mask Y", 0x2748],
    ["TeamName X", 0x27E4],
    ["TeamName Y", 0x27E8],
    ["LeagueLoader X", 0x2834],
    ["LeagueLoader Y", 0x2838],
    ["RibbonOut X", 0x2884],
    ["RibbonOut Y", 0x2888],
    ["Orb X", 0x28D4],
    ["Orb Y", 0x28D8],
    ["Ribbon X", 0x2924],
    ["Ribbon Y", 0x2928],
    ["StaticRibbon X", 0x9333],
    ["StaticRibbon Y", 0x9337],
]

# Empty lists for colors and sizes (add if needed)
COLOR_OFFSETS_9042 = []
COLOR_OFFSETS_9003 = []
COLOR_OFFSETS_6073 = []
COLOR_OFFSETS_9044 = []
COLOR_OFFSETS_6072 = []
COLOR_OFFSETS_9018 = []

SIZE_OFFSETS_9042 = []
SIZE_OFFSETS_9003 = []
SIZE_OFFSETS_6073 = []
SIZE_OFFSETS_9044 = []
SIZE_OFFSETS_6072 = []
SIZE_OFFSETS_9018 = []

# ============================================
# END OF EDITABLE SECTION
# ============================================

# Supported internal names
SUPPORTED_INTERNAL_NAMES = ["9042", "9003", "6073", "9044", "6072", "9018"]

# Global variables
current_internal_name = None
offsets_vars = {}
offsets_values = {}
color_vars = {}
color_values = {}
color_previews = {}
previous_file_path = None
previous_offsets_values = {}
previous_color_values = {}

def read_internal_name(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            decoded_text = file_content.decode('utf-8', errors='ignore')
            
            for internal_name in SUPPORTED_INTERNAL_NAMES:
                if internal_name in decoded_text:
                    return internal_name
            return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read internal name: {e}")
        return None

def open_file():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("FIFA Big Files", "*.big")])
    if file_path:
        update_status(f"File Loaded: {file_path}", "blue")
        add_internal_name()
        load_current_values()

def load_current_values():
    global file_path, previous_file_path, previous_offsets_values, previous_color_values
    if not file_path:
        return
    
    try:
        with open(file_path, 'rb') as file:
            # Load position and size offset values
            for name, offset in get_all_offsets().items():
                file.seek(offset)
                data = file.read(4)
                if len(data) == 4:
                    value = struct.unpack('<f', data)[0]
                    offsets_vars[offset].set(f"{value:.2f}")
                    previous_offsets_values[offset] = value
            
            # Load color values
            color_dict = get_color_offsets()
            for name, offset in color_dict.items():
                file.seek(offset)
                data = file.read(4)
                if len(data) >= 3:
                    # Read the color in little-endian format
                    color_code = f'#{data[2]:02X}{data[1]:02X}{data[0]:02X}'
                    color_vars[offset].set(color_code)
                    if offset in color_previews:
                        color_previews[offset].config(bg=color_code)
                    previous_color_values[offset] = color_code
        
        update_status(f"Values loaded for {current_internal_name}", "green")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load values: {e}")

def get_all_offsets():
    """Get all position and size offsets for current internal name"""
    all_offsets = {}
    
    if current_internal_name == "9042":
        for name, offset in POSITION_OFFSETS_9042:
            all_offsets[name] = offset
        for name, offset in SIZE_OFFSETS_9042:
            all_offsets[name] = offset
    elif current_internal_name == "9003":
        for name, offset in POSITION_OFFSETS_9003:
            all_offsets[name] = offset
        for name, offset in SIZE_OFFSETS_9003:
            all_offsets[name] = offset
    elif current_internal_name == "6073":
        for name, offset in POSITION_OFFSETS_6073:
            all_offsets[name] = offset
        for name, offset in SIZE_OFFSETS_6073:
            all_offsets[name] = offset
    elif current_internal_name == "9044":
        for name, offset in POSITION_OFFSETS_9044:
            all_offsets[name] = offset
        for name, offset in SIZE_OFFSETS_9044:
            all_offsets[name] = offset
    elif current_internal_name == "6072":
        for name, offset in POSITION_OFFSETS_6072:
            all_offsets[name] = offset
        for name, offset in SIZE_OFFSETS_6072:
            all_offsets[name] = offset
    elif current_internal_name == "9018":
        for name, offset in POSITION_OFFSETS_9018:
            all_offsets[name] = offset
        for name, offset in SIZE_OFFSETS_9018:
            all_offsets[name] = offset
    
    return all_offsets

def get_color_offsets():
    """Get color offsets for current internal name"""
    color_dict = {}
    
    if current_internal_name == "9042":
        for name, offset in COLOR_OFFSETS_9042:
            color_dict[name] = offset
    elif current_internal_name == "9003":
        for name, offset in COLOR_OFFSETS_9003:
            color_dict[name] = offset
    elif current_internal_name == "6073":
        for name, offset in COLOR_OFFSETS_6073:
            color_dict[name] = offset
    elif current_internal_name == "9044":
        for name, offset in COLOR_OFFSETS_9044:
            color_dict[name] = offset
    elif current_internal_name == "6072":
        for name, offset in COLOR_OFFSETS_6072:
            color_dict[name] = offset
    elif current_internal_name == "9018":
        for name, offset in COLOR_OFFSETS_9018:
            color_dict[name] = offset
    
    return color_dict

def add_internal_name():
    global file_path, previous_file_path, previous_offsets_values, previous_color_values, current_internal_name
    internal_name = read_internal_name(file_path)
    if internal_name:
        current_internal_name = internal_name
        internal_name_label.config(text=f"Internal Name: {internal_name}")
        recreate_widgets()
        # Store the current file path and values as the last valid ones
        previous_file_path = file_path
        previous_offsets_values = {offset: float(offsets_vars[offset].get()) for offset in offsets_vars if offsets_vars[offset].get()}
        if color_vars:  # Only if there are colors
            previous_color_values = {offset: color_vars[offset].get() for offset in color_vars}
    else:
        messagebox.showerror("Error", f"File is not a supported scoreboard. Supported: {', '.join(SUPPORTED_INTERNAL_NAMES)}")
        if previous_file_path:
            file_path = previous_file_path
            load_previous_values()
        else:
            update_status("No valid file to revert to.", "red")
        return

def load_previous_values():
    global file_path
    if previous_file_path:
        file_path = previous_file_path
        for offset in previous_offsets_values:
            if offset in offsets_vars:
                offsets_vars[offset].set(f"{previous_offsets_values[offset]:.2f}")
        for offset in previous_color_values:
            if offset in color_vars:
                color_vars[offset].set(previous_color_values[offset])
                if offset in color_previews:
                    color_previews[offset].config(bg=previous_color_values[offset])
        update_status(f"Reverted to previous file: {file_path}", "orange")

def recreate_widgets():
    global offsets_vars, offsets_values, color_vars, color_values, color_previews

    # Clear previous widgets
    for widget in positions_frame.winfo_children():
        widget.destroy()
    for widget in sizes_frame.winfo_children():
        widget.destroy()
    for widget in colors_frame.winfo_children():
        widget.destroy()

    # Initialize variables
    offsets_vars = {}
    offsets_values = {}
    color_vars = {}
    color_values = {}
    color_previews = {}

    # Get the right offset lists based on current internal name
    if current_internal_name == "9042":
        position_offsets = POSITION_OFFSETS_9042
        size_offsets = SIZE_OFFSETS_9042
        color_offsets = COLOR_OFFSETS_9042
    elif current_internal_name == "9003":
        position_offsets = POSITION_OFFSETS_9003
        size_offsets = SIZE_OFFSETS_9003
        color_offsets = COLOR_OFFSETS_9003
    elif current_internal_name == "6073":
        position_offsets = POSITION_OFFSETS_6073
        size_offsets = SIZE_OFFSETS_6073
        color_offsets = COLOR_OFFSETS_6073
    elif current_internal_name == "9044":
        position_offsets = POSITION_OFFSETS_9044
        size_offsets = SIZE_OFFSETS_9044
        color_offsets = COLOR_OFFSETS_9044
    elif current_internal_name == "6072":
        position_offsets = POSITION_OFFSETS_6072
        size_offsets = SIZE_OFFSETS_6072
        color_offsets = COLOR_OFFSETS_6072
    elif current_internal_name == "9018":
        position_offsets = POSITION_OFFSETS_9018
        size_offsets = SIZE_OFFSETS_9018
        color_offsets = COLOR_OFFSETS_9018
    else:
        return

    # Show or hide tabs based on what we have
    has_positions = len(position_offsets) > 0
    has_sizes = len(size_offsets) > 0
    has_colors = len(color_offsets) > 0
    
    # Show/hide tabs
    notebook.tab(0, state='normal' if has_positions else 'hidden')
    notebook.tab(1, state='normal' if has_sizes else 'hidden')
    notebook.tab(2, state='normal' if has_colors else 'hidden')

    # Add positions to Positions tab
    if has_positions:
        row = 0
        # Use a scrollable canvas for positions
        canvas = tk.Canvas(positions_frame)
        scrollbar = ttk.Scrollbar(positions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for label_text, offset in position_offsets:
            col = 0 if " X" in label_text else 2
            tk.Label(scrollable_frame, text=label_text).grid(row=row, column=col, padx=10, pady=5)
            entry = tk.Entry(scrollable_frame, textvariable=offsets_vars.setdefault(offset, tk.StringVar(value="0.00")))
            entry.grid(row=row, column=col+1, padx=10, pady=5)
            entry.bind("<KeyRelease>", lambda e, offset=offset, var=offsets_vars[offset]: update_value(offset, var))
            entry.bind('<KeyPress-Up>', lambda e, var=offsets_vars[offset]: increment_value(e, var))
            entry.bind('<KeyPress-Down>', lambda e, var=offsets_vars[offset]: increment_value(e, var))
            if col == 2:
                row += 1
            offsets_values[offset] = 0.0
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # Add sizes to Sizes tab
    if has_sizes:
        row = 0
        for label_text, offset in size_offsets:
            tk.Label(sizes_frame, text=label_text).grid(row=row, column=0, padx=10, pady=5)
            entry = tk.Entry(sizes_frame, textvariable=offsets_vars.setdefault(offset, tk.StringVar(value="0.00")))
            entry.grid(row=row, column=1, padx=10, pady=5)
            entry.bind("<KeyRelease>", lambda e, offset=offset, var=offsets_vars[offset]: update_value(offset, var))
            entry.bind('<KeyPress-Up>', lambda e, var=offsets_vars[offset]: increment_value(e, var))
            entry.bind('<KeyPress-Down>', lambda e, var=offsets_vars[offset]: increment_value(e, var))
            row += 1
            offsets_values[offset] = 0.0

    # Add colors to Colors tab
    if has_colors:
        row = 0
        for label_text, offset in color_offsets:
            tk.Label(colors_frame, text=label_text).grid(row=row, column=0, padx=10, pady=5)
            entry = tk.Entry(colors_frame, textvariable=color_vars.setdefault(offset, tk.StringVar(value='#000000')))
            entry.grid(row=row, column=1, padx=10, pady=5)
            entry.bind('<KeyPress>', lambda e, var=color_vars[offset]: restrict_color_entry(e, var))
            entry.bind('<KeyRelease>', lambda e, offset=offset, var=color_vars[offset]: update_color_preview(offset, var.get()))
            color_preview = tk.Label(colors_frame, bg='#000000', width=2)
            color_preview.grid(row=row, column=2, padx=10, pady=5)
            color_preview.bind("<Button-1>", lambda e, offset=offset, var=color_vars[offset]: choose_color(offset, var))
            color_previews[offset] = color_preview
            update_func = lambda offset=offset, var=color_vars[offset]: update_color(offset, var)
            tk.Button(colors_frame, text="Update", command=update_func).grid(row=row, column=3, padx=10, pady=5)
            row += 1
            color_values[offset] = "#000000"

def save_file():
    if not file_path:
        messagebox.showerror("Error", "No file loaded.")
        return
    
    try:
        with open(file_path, 'r+b') as file:
            # Save all offset values (positions and sizes)
            all_offsets = get_all_offsets()
            for name, offset in all_offsets.items():
                if offset in offsets_vars:
                    value_str = offsets_vars[offset].get()
                    try:
                        value = float(value_str)
                        file.seek(offset)
                        file.write(struct.pack('<f', value))
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {name}: {value_str}")
                        return
            
            # Save color values
            color_dict = get_color_offsets()
            for name, offset in color_dict.items():
                if offset in color_vars:
                    color_code = color_vars[offset].get()
                    try:
                        # Convert color to little-endian format
                        if color_code.startswith('#') and len(color_code) == 7:
                            color_bytes = bytes.fromhex(color_code[1:])[::-1]
                            if len(color_bytes) == 3:
                                color_bytes += b'\xFF'  # Add alpha channel
                            file.seek(offset)
                            file.write(color_bytes[:4])
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid color for {name}: {color_code}")
                        return
        
        update_status(f"File saved successfully! ({current_internal_name})", "green")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")

def update_value(offset, var):
    try:
        value = float(var.get())
        offsets_values[offset] = value
        update_status("Value Updated!", "green")
    except ValueError:
        update_status("Invalid value", "red")

def increment_value(event, var):
    try:
        value = float(var.get())
        if event.state & 0x0001:  # Shift key
            value += 0.1 if event.keysym == 'Up' else -0.1
        else:
            value += 1.0 if event.keysym == 'Up' else -1.0
        var.set(f"{value:.2f}")
    except ValueError:
        update_status("Invalid value", "red")

def update_color_preview(offset, color):
    if offset in color_previews:
        color_previews[offset].config(bg=color)

def choose_color(offset, var):
    color_code = colorchooser.askcolor()[1]
    if color_code:
        var.set(color_code)
        update_color_preview(offset, color_code)

def update_color(offset, var):
    color_values[offset] = var.get()
    update_color_preview(offset, var.get())

def update_status(message, color):
    status_label.config(text=message, fg=color)

def toggle_fullscreen(event=None):
    global is_fullscreen
    is_fullscreen = not is_fullscreen
    root.attributes('-fullscreen', is_fullscreen)
    update_status("Fullscreen: " + ("ON" if is_fullscreen else "OFF"), "blue")

def about():
    about_window = tk.Toplevel(root)
    about_window.title("About")
    about_window.geometry("420x400")
    about_window.resizable(False, False)
    bold_font = ("Helvetica", 12, "bold")
    tk.Label(about_window, text="FLP Scoreboard Editor 14 - Multi-Format", pady=10, font=bold_font).pack()
    tk.Label(about_window, text=f"Version 1.5 [Supports {len(SUPPORTED_INTERNAL_NAMES)} formats]", pady=10).pack()
    
    # Show format counts
    tk.Label(about_window, text=f"9042: {len(POSITION_OFFSETS_9042)} positions", pady=2).pack()
    tk.Label(about_window, text=f"9003: {len(POSITION_OFFSETS_9003)} positions", pady=2).pack()
    tk.Label(about_window, text=f"6073: {len(POSITION_OFFSETS_6073)} positions", pady=2).pack()
    tk.Label(about_window, text=f"9044: {len(POSITION_OFFSETS_9044)} positions", pady=2).pack()
    tk.Label(about_window, text=f"6072: {len(POSITION_OFFSETS_6072)} positions", pady=2).pack()
    tk.Label(about_window, text=f"9018: {len(POSITION_OFFSETS_9018)} positions", pady=2).pack()
    
    tk.Label(about_window, text="© 2024 FIFA Legacy Project. All Rights Reserved.", pady=10).pack()
    tk.Label(about_window, text="Designed & Developed By Emran_Ahm3d.", pady=10).pack()
    link = tk.Label(about_window, text="Official Forum Thread", fg="blue", cursor="hand2")
    link.pack(pady=5)
    link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.soccergaming.com/index.php?threads/download-flp-scoreboard-editor-14.6473355/post-6801850"))
    tk.Label(about_window, text="Discord: @emran_ahm3d", pady=10).pack()

def show_documentation():
    webbrowser.open("https://soccergaming.com/index.php?threads/emrans-fifa-14-overlays-research.6473147/")

def restrict_color_entry(event, var):
    if event.keysym == 'BackSpace' and var.get() == '#':
        return 'break'

def exit_app():
    if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
        root.destroy()

# ============================================
# MAIN APPLICATION START
# ============================================

# Main Window
root = tk.Tk()
root.title(f"FLP Scoreboard Editor 14 - Multi-Format (v1.5)")
root.geometry("800x600")
root.resizable(True, True)

# Fullscreen support
root.bind('<F11>', toggle_fullscreen)
root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))

# Menu
menubar = tk.Menu(root)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open                        ", command=open_file)
filemenu.add_command(label="Save", command=save_file)
filemenu.add_separator()
filemenu.add_command(label="Fullscreen (F11)", command=toggle_fullscreen)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit_app)
menubar.add_cascade(label="    File    ", menu=filemenu)

helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About                        ", command=about)
helpmenu.add_separator()
helpmenu.add_command(label="Documentation", command=show_documentation)
menubar.add_cascade(label="    Help    ", menu=helpmenu)

root.config(menu=menubar)

# Tabs
notebook = ttk.Notebook(root)
positions_frame = ttk.Frame(notebook)
sizes_frame = ttk.Frame(notebook)
colors_frame = ttk.Frame(notebook)

notebook.add(positions_frame, text="Positions")
notebook.add(sizes_frame, text="Sizes")
notebook.add(colors_frame, text="Colors")
notebook.pack(expand=1, fill="both")

# Frame to hold both labels
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Internal Name Label
internal_name_label = tk.Label(bottom_frame, text="Internal Name: Not Loaded", anchor=tk.E)
internal_name_label.pack(side=tk.RIGHT, padx='10', pady=0)

# Status Bar
status_label = tk.Label(bottom_frame, text=f"Ready - Supports: {', '.join(SUPPORTED_INTERNAL_NAMES)}", anchor=tk.W, fg="blue")
status_label.pack(side=tk.LEFT, padx='5', pady=0)

# SAVE button
def place_save_button():
    save_button = ttk.Button(root, text="SAVE", style="Large.TButton", command=save_file)
    save_button.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-30)

root.style = ttk.Style()
root.style.configure('Large.TButton', font=('Helvetica', 15), foreground='green')
place_save_button()

root.mainloop()