import random
import time
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def intro():
    clear()
    print("🔥 BRANDON'S MULTI-LEVEL CHAOS GAME 🔥")
    print("Survive each level. Numbers dodge. Traps appear. Chaos rules! 😤\n")
    input("Press Enter to start…")

def random_event(score, level):
    # Frustrating random events
    chance = random.random()
    if chance < 0.1 + level*0.01:  # higher levels = more chaos
        print("💥 TRAP! You lost ALL your points! 😱")
        return 0
    elif chance < 0.3:
        lose = random.randint(1, max(score,1))
        print(f"⚡ CHAOS STRIKE! You lose {lose} points 😵")
        return max(0, score - lose)
    elif chance > 0.95:
        gain = random.randint(1, level)
        print(f"🎉 LUCKY STRIKE! You gain {gain} bonus points! 😲")
        return score + gain
    return score

def play_level(level, score):
    print(f"\n🌟 LEVEL {level} 🌟")
    print("Pick a number 1-5 (or 'q' to quit):")
    choice = input("> ")

    if choice.lower() == 'q':
        return score, True  # quit game

    if choice not in ['1','2','3','4','5']:
        print("🤪 INVALID CHOICE! Chaos happens anyway!")
        time.sleep(1.2)
        return score, False

    guess = int(choice)
    # Correct number
    correct = random.randint(1,5)

    # Dodge chance increases with level
    if random.random() < 0.3 + level*0.02:
        correct = random.randint(1,5)

    if guess == correct:
        print("🎯 HIT! +1 POINT")
        score += 1
    else:
        print(f"😬 MISS! The correct number was {correct}. -1 POINT")
        score = max(0, score - 1)

    # Random chaotic events
    score = random_event(score, level)
    time.sleep(1.5)
    return score, False

def game():
    score = 0
    level = 1
    intro()
    quit_game = False

    while not quit_game:
        clear()
        print(f"Level: {level} | Score: {score}")
        score, quit_game = play_level(level, score)
        level += 1

    print(f"\nFinal Score: {score} — Did you survive the chaos? 😅")

if __name__ == "__main__":
    game()
