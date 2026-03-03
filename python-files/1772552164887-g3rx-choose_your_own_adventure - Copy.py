# Your job is to create a program that takes user input
# to move through a series of decisions like a choose your own adventure game. 
import random

def intro():
    print("⚽ SOCCER SHOWDOWN ⚽")
    print("You have the ball at midfield.")
    print("The crowd is cheering...")
    print()

def midfield():
    print("You're at midfield. A defender is approaching!")
    print("Do you:")
    print("1 - Pass to your teammate")
    print("2 - Dribble forward")

    choice = input("Enter 1 or 2: ")

    if choice == "1":
        return pass_play()
    elif choice == "2":
        return dribble_play()
    else:
        print("Invalid choice! The defender steals the ball!")
        return "lose"

def pass_play():
    print("\nYou pass the ball!")
    success = random.choice([True, False])

    if success:
        print("Your teammate passes it back perfectly!")
        return penalty_area()
    else:
        print("Oh no! The pass was intercepted!")
        return "lose"

def dribble_play():
    print("\nYou try to dribble past the defender!")
    success = random.choice([True, False])

    if success:
        print("Nice move! You beat the defender!")
        return penalty_area()
    else:
        print("The defender tackles you and takes the ball!")
        return "lose"

def penalty_area():
    print("\nYou're near the goal now!")
    print("The goalie is ready.")
    print("Do you:")
    print("1 - Shoot immediately")
    print("2 - Fake left, shoot right")

    choice = input("Enter 1 or 2: ")

    if choice == "1":
        return shoot()
    elif choice == "2":
        return fake_shot()
    else:
        print("You hesitate too long!")
        return "lose"

def shoot():
    print("\nYou blast the ball toward the net!")
    success = random.choice([True, False])

    if success:
        return "win"
    else:
        return "lose"

def fake_shot():
    print("\nYou fake left and shoot right!")
    success = random.choice([True, True, False])  # Better odds!

    if success:
        return "win"
    else:
        return "lose"

def ending(result):
    print("\n--- FINAL RESULT ---")
    if result == "win":
        print("GOOOOOAL!!! 🎉⚽")
        print("You scored! The crowd goes wild!")
    else:
        print("Oh no! The other team counterattacks...")
        print("They score on your team! 😢")
        print("Better luck next time!")

# Main Game
intro()
result = midfield()
ending(result)
