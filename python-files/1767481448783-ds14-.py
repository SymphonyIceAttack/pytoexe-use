def evaluate_water_quality(ph_value):
    """
    Evaluate water quality based on pH value from 1 to 14
    """
    if ph_value < 1 or ph_value > 14:
        return "Invalid pH value! (Enter 1-14)"
    
    if 1 <= ph_value <= 3:
        return "Very acidic ❌ - Not safe to drink"
    elif 4 <= ph_value <= 6:
        return "Slightly acidic ⚠️ - Usually not recommended"
    elif 7 == ph_value:
        return "Neutral ✅ - Safe to drink"
    elif 8 <= ph_value <= 10:
        return "Slightly alkaline ⚠️ - Usually safe"
    elif 11 <= ph_value <= 14:
        return "Very alkaline ❌ - Not safe to drink"

def main():
    while True:
        ph_input = input("Enter water pH value (1-14) or type 'exit' to quit: ")
        
        if ph_input.lower() == 'exit':
            print("Program exited.")
            break
        
        try:
            ph_value = int(ph_input)  # Using int because pH is now from 1-14
            result = evaluate_water_quality(ph_value)
            print("Water quality result:", result)
        except ValueError:
            print("Please enter a valid number between 1 and 14!")

if __name__ == "__main__":
    main()

