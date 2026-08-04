def main():
    print("--- Item Price Calculator & 20% Discount on Lowest Item ---")
    
    try:
        num_items = int(input("Enter amount for item (number of items): "))
        if num_items <= 0:
            print("Please enter a number greater than 0.")
            return
        discount_precent = int(input("Enter Discount In precent (Ex. 50% enter 50): "))
    except ValueError:
        print("Invalid input. Please enter a valid integer.")
        return

    prices = []
    for i in range(1, num_items + 1):
        while True:
            try:
                price = float(input(f"Enter price for item {i}: "))
                if price < 0:
                    print("Price cannot be negative. Try again.")
                    continue
                prices.append(price)
                break
            except ValueError:
                print("Invalid input. Please enter a valid number for the price.")

    lowest_price = min(prices)
    
    discount_amount = lowest_price * (discount_precent / 100)
    total_price = sum(prices)-discount_amount

    print("\n" + "="*40)
    print(f"All prices entered: {prices}")
    print(f"The lowest price is: {lowest_price:.2f}")
    print(f"{discount_precent}% discount applied: -{discount_amount:.2f}")
    print(f"Total price:{total_price}")
    print("="*40)

if __name__ == "__main__":
    main()