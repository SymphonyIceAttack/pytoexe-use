
from datetime import date

def say_happy_birthday_early():
    name = "Kyawt Thinegi"
    today = date.today()
    
    # Set the target birthday for the current year
    birthday = date(today.year, 5, 3)
    
    # Calculate the difference
    days_to_go = (birthday - today).days
    
    # The Message
    print("✨ EARLY BIRTHDAY WISH ✨")
    print("-" * 30)
    print(f"Dear {name},")
    print(f"I know your birthday isn't until May 3rd,")
    print(f"but I wanted to be the first to say it!")
    print(f"\n🎉 HAPPY BIRTHDAY (in {days_to_go} days)! 🎉")
    print("-" * 30)

if __name__ == "__main__":
    say_happy_birthday_early()
