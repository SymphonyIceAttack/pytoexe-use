import time

print("Welcome to the GC STEM escape room, where your team shall crack the 4 locks each themed around Maths, Physics, Chemistry and Biology.")
print("Once you have gathered the master password you shall type it here and if you got it right you will be allowed to leave.")
print("Type in 'start' when you are ready and I will start the timer.")

PASSWORD = "2690"
TIME_LIMIT = 300

while True:
    cmd = input("> ").lower().strip()
    if cmd == "start":
        break

start_time = time.time()

while True:
    if time.time() - start_time > TIME_LIMIT:
        print("Time is up! You failed to escape.")
        exit()

    guess = input("Enter the master password: ")

    if guess == PASSWORD:
        elapsed = time.time() - start_time
        print(f"Congratulation you have cracked the code in {elapsed:.2f} seconds")
        break
    else:
        print("Incorrect password.")

while True:
    cmd = input("Type 'end' to close the program: ").lower().strip()
    if cmd == "end":
        break