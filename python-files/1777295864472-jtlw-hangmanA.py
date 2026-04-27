from random import choice
print("there are no duplicates")
word = choice(["water", "flame", "audio", "sixty", "apple", "pause", "great", "sigma", "crazy","belts"])
out = ""
letters = list(word)
letter1 = letters[0]
letter2 = letters[1]
letter3 = letters[2]
letter4 = letters[3]
letter5 = letters[4]
answer = list(["_","_","_","_","_"])
timescorrect = 0
timeswrong = 0
worda = ""
def finish():
    print("you won with",timeswrong,"wrong guesses, 5 right guesses with a total amount of",totalguesses,"guesses")
def finish2():
    print("you won with",timeswrong,"wrong guess, 5 right guesses with a total amount of",totalguesses,"guesses")
def finish3():
    print("you lost with 7 wrong guesses,",timescorrect," right guesses with a total amount of",totalguesses,"guesses")
def finish4():
    print("you lost with 7 wrong guesses,",timescorrect," right guess with a total amount of",totalguesses,"guesses")
for count in range(100):
    print("guess a letter", out)
    guess = input("")
    if guess in word:
        if guess in worda:
            print("stop tryna cheat")
            break
        if guess == letter1:
            answer[0] = guess
        elif guess == letter2:
            answer[1] = guess
        elif guess == letter3:
            answer[2] = guess
        elif guess == letter4:
            answer[3] = guess
        else:
            answer[4] = guess
        timescorrect = timescorrect+1
        worda = ''.join(map(str, answer))
        print(worda)
        if timescorrect == 5 and timeswrong != 1:
            totalguesses = timeswrong + 5
            finish()
        elif timescorrect ==5 and timeswrong == 1:
            totalguesses = timeswrong + 5
            finish2()
            break
        
    
    else:
        worda = ''.join(map(str, answer))
        print(worda)
        timeswrong = timeswrong + 1
        if timeswrong == 7 and timescorrect != 1:
            totalguesses = timescorrect + 7
            finish3()
            break
        elif timeswrong == 7 and timescorrect == 1:
            totalguesses = timescorrect + 7
            finish4()
            break
        
