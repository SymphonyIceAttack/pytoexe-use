# sample_code.py
# Function to calculate factorial
def factorial(n):
   """Return the factorial of a number."""
   result = 1
   for i in range(2, n + 1):
       result *= i
   return result
# Main execution block
if __name__ == "__main__":
   # Taking user input
   num = int(input("Enter a number: "))
   # Calculating factorial
   fact = factorial(num)
   print(f"Factorial of {num} is {fact}")
   # Writing result to a file
   with open("result.txt", "w") as f:
       f.write(f"Factorial of {num} is {fact}\n")
   # Reading the file content back
   with open("result.txt", "r") as f:
       content = f.read()
       print("File Content:")
       print(content)