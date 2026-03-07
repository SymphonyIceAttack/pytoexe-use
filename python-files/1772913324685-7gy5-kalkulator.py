while True:
    a = float(input())
    op = input()
    b = float(input())

    if op == "+":
        print(a + b)
    elif op == "-":
        print(a - b)
    elif op == "*":
        print(a * b)
    elif op == "/":
        if b == 0:
            print("error")
        else:
            print(a / b)
