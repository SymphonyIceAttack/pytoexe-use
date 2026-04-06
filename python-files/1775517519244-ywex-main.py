
import time

#Welcome speech
print("Welcome, player.")
name = input("What is your name?\n")
print()

#Choice 1
choice1 = input("Would you like to play a game, "+name+"?\n")

print()

if choice1.lower() == "yes":
    print("Marvelous! Let's get started.")

elif choice1.lower() == "no": 
    print("Goodbye then.")

else: 
    print("Please try again using yes or no.")
    

#Start game
print("Are you good at solving ciphers?")

time.sleep(1)

print("That was rhetorical; I don't actually care.")
print()
print("You must answer all three questions correctly,")
print("or I will melt this chocolate in front of you.")

print()

time.sleep(1)

score = 0

# Question 1
answer1 = input("1) What is the capital of Assyria?\n").strip().lower()
if answer1 == "ninevah":
    score += 1

# Question 2
print()
answer2 = input("2) When did Knightshade first appear at UCF?\n").strip().lower()
if answer2 in ["october 8, 2025", "10/8/25", "oct 8"]:
    score += 1

# Question 3
print()
answer3 = input("3) What's black and white and purple all over?\n").strip().lower()
if answer3 == "gamemaster when knightshade beats him":
    score += 1

# Final result
print()
if score == 3:
    print("Congratulations. You don't entirely suck.")
    print("Collect your prize.")
else:
    print("You failed. Oh well. Bye bye!")
    
time.sleep(10)