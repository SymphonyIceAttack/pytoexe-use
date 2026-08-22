import tkinter as tk


def open_text_windows():
	root = tk.Tk()
	root.title("Window Controls")
	root.geometry("140x70")
	root.resizable(False, False)

	def close_all_windows():
		root.destroy()

	passcode_window = tk.Toplevel(root)
	passcode_window.title("Passcode")
	passcode_window.geometry("260x145")
	passcode_window.resizable(False, False)

	tk_label = tk.Label(passcode_window, text="Enter passcode:")
	tk_label.pack(pady=(12, 4))
	passcode_entry = tk.Entry(passcode_window, show="*", width=24)
	passcode_entry.pack()
	status_label = tk.Label(passcode_window, text="")
	status_label.pack()

	def submit_passcode():
		if passcode_entry.get() == "proton":
			close_all_windows()
			return
		status_label.config(text="Incorrect passcode")
		passcode_entry.delete(0, tk.END)

	tk.Button(passcode_window, text="Submit", command=submit_passcode).pack(pady=8)

	button_positions = [(8, 8), (58, 8), (28, 38), (82, 38)]
	position_index = 0
	close_button = tk.Button(root, text="Close All", command=submit_passcode)
	close_button.place(x=button_positions[0][0], y=button_positions[0][1])

	def move_close_button(_event):
		nonlocal position_index
		position_index = (position_index + 1) % len(button_positions)
		button_x, button_y = button_positions[position_index]
		close_button.place(x=button_x, y=button_y)

	close_button.bind("<Enter>", move_close_button)

	for window_number in range(100, 1000):
		window = tk.Toplevel(root)
		window.title(f"Text Window {window_number}")
		window.geometry("500x300")

		text_box = tk.Text(window, wrap="word", undo=True)
		text_box.pack(fill="both", expand=True, padx=8, pady=8)
		text_box.insert("1.0", "chizburger")

	root.mainloop()


if __name__ == "__main__":
	open_text_windows()
