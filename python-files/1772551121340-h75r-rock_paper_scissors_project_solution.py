import random

#A list which contains rock, paper, and scissors
rps = ["rock","paper","scissors"]

human_score = 0

computer_score = 0

print("Best 2 out of 3 rock paper scissors vs. the computer")

while human_score < 2 and computer_score < 2:

    # The computer's random choice of rock, paper, or scissors
    computer_choice = random.choice(rps)

    # The user chooses rock, paper, or scissors
    human_choice = input('Do you choose rock, paper, or scissors?')

    print("The computer chose: ",computer_choice)

    if computer_choice == human_choice:
        print("It's a tie! Try again!")

    elif computer_choice == "rock" and human_choice == "scissors":
        print("You lose!")

    elif computer_choice == "rock" and human_choice == "paper":
        print("You win")

        human_score = human_score + 1
    
    elif computer_choice == "scissors" and human_choice == "rock":
        print("You win!")

        human_score = human_score + 1

    elif computer_choice == "scissors" and human_choice == "paper":
        print("You lose!")

        computer_score = computer_score + 1

    elif computer_choice == "paper" and human_choice == "rock":
        print("You lose!")

        computer_score += 1
        
    elif computer_choice == "paper" and human_choice == "scissors":
        print("You win!")

        human_score += 1 
    else:
        print("You entered your guess wrong try again!")

    print("Your score: ",human_score,"Computer score: ",computer_score)

input('Game over! Press any button to exit')
