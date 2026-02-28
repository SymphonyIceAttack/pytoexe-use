import time
import sys
import tkinter as tk
import random

# --- Terminal Animation ---
def show_terminal_animation():
    # ANSI Escape Code für grüne Farbe
    GREEN = "\033[92m"
    RESET = "\033[0m"
    
    # ASCII Art für "Arne Dettmer"
    ascii_name = """
      _                        ____       _   _                       
     / \   _ __ _ __   ___    |  _ \  ___| |_| |_ _ __ ___   ___  _ __ 
    / _ \ | '__| '_ \ / _ \   | | | |/ _ \ __| __| '_ ` _ \ / _ \| '__|
   / ___ \| |  | | | |  __/   | |_| |  __/ |_| |_| | | | | |  __/| |   
  /_/   \_\_|  |_| |_|\___|   |____/ \___|\__|\__|_| |_| |_|\___||_|   
                                                                       
    """
    
    # Terminal leeren
    print("\033[H\033[J")
    
    for line in ascii_name.split('\n'):
        print(GREEN + line + RESET)
        time.sleep(0.05)
        
    print(GREEN + "\n   Lade Anwendung..." + RESET)
    time.sleep(2)

# Terminal Animation starten
show_terminal_animation()

# --- Hauptprogramm (GUI) ---
player_wins = 0
computer_wins = 0

def play_round(player_choice):
    global player_wins, computer_wins
    choices = ["rock", "paper", "scissors"]
    computer_choice = random.choice(choices)

    player_choice_label.config(text=f"You chose: {player_choice}")
    computer_choice_label.config(text=f"Computer chose: {computer_choice}")

    winner = ""
    if (player_choice == "rock" and computer_choice == "scissors") or \
       (player_choice == "scissors" and computer_choice == "paper") or \
       (player_choice == "paper" and computer_choice == "rock"):
        winner = "Player"
    elif player_choice == computer_choice:
        winner = "Tie"
    else:
        winner = "Computer"

    if winner == "Player":
        message_label.config(text=f"You won with {player_choice}!")
        player_wins += 1
    elif winner == "Computer":
        message_label.config(text=f"Computer won with {computer_choice}!")
        computer_wins += 1
    else:
        message_label.config(text="It's a tie!")

    score_label.config(text=f"Score - Player: {player_wins}, Computer: {computer_wins}")

    if player_wins >= 2 or computer_wins >= 2:
        if player_wins > computer_wins:
            final_message_label.config(text="Congratulations! You won the game!")
        else:
            final_message_label.config(text="Computer won the game!")
        rock_button.config(state=tk.DISABLED)
        paper_button.config(state=tk.DISABLED)
        scissors_button.config(state=tk.DISABLED)

# Set up the main window
root = tk.Tk()
root.title("Rock, Paper, Scissors")

# Create labels and buttons
instruction_label = tk.Label(root, text="Choose your move:")
instruction_label.pack(pady=10)

player_choice_label = tk.Label(root, text="You chose: ")
player_choice_label.pack()

computer_choice_label = tk.Label(root, text="Computer chose: ")
computer_choice_label.pack()

message_label = tk.Label(root, text="")
message_label.pack(pady=5)

score_label = tk.Label(root, text=f"Score - Player: {player_wins}, Computer: {computer_wins}")
score_label.pack(pady=5)

final_message_label = tk.Label(root, text="", font=("Arial", 12, "bold"))
final_message_label.pack(pady=10)

rock_button = tk.Button(root, text="Rock", command=lambda: play_round("rock"))
rock_button.pack(side=tk.LEFT, padx=10)

paper_button = tk.Button(root, text="Paper", command=lambda: play_round("paper"))
paper_button.pack(side=tk.LEFT, padx=10)

scissors_button = tk.Button(root, text="Scissors", command=lambda: play_round("scissors"))
scissors_button.pack(side=tk.LEFT, padx=10)

root.mainloop()