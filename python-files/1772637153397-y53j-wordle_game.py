import random

words = ["apple", "grape", "tiger", "chair", "plant", "bread"]

secret = random.choice(words)
attempts = 6

print("Welcome to Word Guess!")
print("Correct spot = letter")
print("Wrong spot = O")
print("Not in word = X\n")

for turn in range(attempts):

    guess = input("Enter a 5-letter word: ").lower()

    if len(guess) != 5:
        print("Please enter exactly 5 letters.\n")
        continue

    result = []

    for i in range(5):

        if guess[i] == secret[i]:
            result.append(guess[i].upper())

        elif guess[i] in secret:
            result.append("O")

        else:
            result.append("X")

    print(" ".join(result))
    print()

    if guess == secret:
        print("🎉 You guessed the word!")
        break

else:
    print("Out of guesses!")
    print("The word was:", secret)
