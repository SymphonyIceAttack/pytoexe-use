import tkinter as tk
import random


def open_text_windows():
	background_color = "#808080"
	panel_color = "#242933"
	text_color = "#e6e9ef"
	icon_color = "#596273"
	icons = ("*", "+", "#", "@", "%", "&", "~")

	root = tk.Tk()
	root.title("Window Controls")
	root.geometry("320x150")
	root.resizable(False, False)
	root.configure(bg=background_color)

	def close_all_windows():
		root.destroy()

	passcode_window = tk.Toplevel(root)
	passcode_window.title("Passcode")
	passcode_window.geometry("260x145")
	passcode_window.resizable(False, False)
	passcode_window.configure(bg=background_color)
	passcode_window.overrideredirect(True)

	tk_label = tk.Label(
		passcode_window,
		text="Enter passcode:",
		bg=background_color,
		fg=text_color,
	)
	tk_label.pack(pady=(12, 4))
	passcode_entry = tk.Entry(
		passcode_window,
		show="*",
		width=24,
		bg=panel_color,
		fg=text_color,
		insertbackground=text_color,
	)
	passcode_entry.pack()
	status_label = tk.Label(passcode_window, text="", bg=background_color, fg="#ff7b72")
	status_label.pack()
	next_window_number = 100

	def create_text_window():
		nonlocal next_window_number
		window = tk.Toplevel(root)
		window.title(f"Text Window {next_window_number}")
		window.geometry("500x300")
		window.configure(bg=background_color)
		window.overrideredirect(True)
		window.protocol("WM_DELETE_WINDOW", submit_passcode)

		icon_label = tk.Label(
			window,
			text=random.choice(icons),
			font=("Segoe UI", 72, "bold"),
			bg=background_color,
			fg=icon_color,
		)
		icon_label.place(relx=0.86, rely=0.72, anchor="center")

		text_box = tk.Text(
			window,
			wrap="word",
			undo=True,
			bg=panel_color,
			fg=text_color,
			insertbackground=text_color,
			relief="flat",
		)
		text_box.pack(fill="both", expand=True, padx=(8, 82), pady=8)
		text_box.insert("1.0", "chizburger")
		next_window_number += 1

	def submit_passcode():
		if passcode_entry.get() == "proton":
			close_all_windows()
			return
		status_label.config(text="Incorrect passcode")
		passcode_entry.delete(0, tk.END)
		create_text_window()

	def keep_passcode_window_open():
		passcode_window.deiconify()
		passcode_window.lift()
		passcode_window.focus_force()

	root.protocol("WM_DELETE_WINDOW", submit_passcode)
	passcode_window.protocol("WM_DELETE_WINDOW", keep_passcode_window_open)

	button_positions = [(20, 20), (150, 20), (80, 85), (210, 85)]
	position_index = 0
	close_button = tk.Button(
		root,
		text="Close All",
		command=submit_passcode,
		width=12,
		height=2,
		bg=panel_color,
		fg=text_color,
		activebackground="#303846",
		activeforeground=text_color,
		relief="flat",
	)
	close_button.place(x=button_positions[0][0], y=button_positions[0][1])

	def move_close_button(_event):
		nonlocal position_index
		position_index = (position_index + 1) % len(button_positions)
		button_x, button_y = button_positions[position_index]
		close_button.place(x=button_x, y=button_y)

	close_button.bind("<Enter>", move_close_button)

	tk.Button(
		passcode_window,
		text="Submit",
		command=submit_passcode,
		bg=panel_color,
		fg=text_color,
		activebackground="#303846",
		activeforeground=text_color,
		relief="flat",
	).pack(pady=8)

	for _ in range(900):
		create_text_window()

	root.mainloop()


if __name__ == "__main__":
	open_text_windows()
