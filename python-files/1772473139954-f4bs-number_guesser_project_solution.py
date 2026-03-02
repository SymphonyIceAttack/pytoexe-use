import random
import time

#secret_number is a random number between 1 & 100
secret_number = random.randint(1,100)

guess = ""

while guess != secret_number:

    guess = int(input("Guess the number: "))

    if guess > 100 or guess < 0 :
        print("Type a number between 0 and 100")
    
    elif guess > secret_number:
        print("Lower")

    elif guess < secret_number:
        print("Higher")

print("Congratulations! You got it")

time.sleep(3)

input("Type anything to exit program")


    
        
