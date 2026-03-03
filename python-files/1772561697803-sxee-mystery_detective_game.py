print("🕵️ SCIENCE LAB MYSTERY 🧪")
print("The robotics prototype was stolen at 2:15 PM.")
print("You must determine who did it.\n")

print("Suspects:")
print("1. Mia")
print("2. Leo")
print("3. Ava\n")

# Interview Mia
print("You interview Mia.")
print("She says: 'I was in math class at 2:15.'")
print("The math teacher confirms Mia was in class.\n")

# Interview Leo
print("You interview Leo.")
print("He says: 'I was in the cafeteria at 2:15.'")
print("The lunch monitor confirms Leo bought food at 2:10,")
print("but says Leo left the cafeteria around 2:13.\n")

# Interview Ava
print("You interview Ava.")
print("She says: 'I was in the library at 2:15.'")
print("The librarian confirms Ava checked out a book at 2:20.")
print("Security footage shows Ava entering the library at 2:18.\n")

print("🧠 Think carefully...")
print("The theft happened at 2:15 PM.\n")

accuse = input("Who stole the prototype? (Mia, Leo, Ava) ").lower()

print("\n")

if accuse == "leo":
    print("✅ Correct!")
    print("Leo left the cafeteria BEFORE 2:15.")
    print("He had time to steal the prototype!")
elif accuse == "mia":
    print("❌ Not quite.")
    print("Mia was confirmed to be in math class at 2:15.")
elif accuse == "ava":
    print("❌ Not quite.")
    print("Ava didn't enter the library until AFTER 2:15.")
else:
    print("That's not a valid suspect.")
