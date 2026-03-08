import time

print("Welcome to the STEM Escape room. Inside this room there is 4 lock boxes themed around Maths, Physics, Chemistry and Biology.")
print("Those boxes contain the master password.")
print("Once you cracked all 4 boxes enter them in the following order: Maths, Physics, Chemistry and Biology.")
print("Once you are ready type in 'start' and you will have 5 minutes to escape.")

PASSWORD = "2690"
TIME_LIMIT = 300  # 5 minutes

# Wait for the user to start
while True:
    cmd = input("> ").lower().strip()
    if cmd == "start":
        break
    else:
        print("Please type 'start' when you are ready.")

start_time = time.time()

# Password entry phase
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

# Program stays open until 'end' is typed
while True:
    cmd = input("Type 'end' to close the program: ").lower().strip()
    if cmd == "end":
        break