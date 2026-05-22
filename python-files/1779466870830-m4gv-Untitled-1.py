x1 = float(input("Введите x1: "))
x2 = float(input("Введите x2: "))
# скрытый слой
# нейрон 1
w11 = 0.5
w12 = 0.3
b1 = 0.1
h1 = x1 * w11 + x2 * w12 + b1
if h1 > 0.5:
    h1 = 1
else:
    h1 = 0
# нейрон 2
w21 = 0.4
w22 = 0.7
b2 = 0.2
h2 = x1 * w21 + x2 * w22 + b2
if h2 > 0.5:
    h2 = 1
else:
    h2 = 0
# выходной слой
w_out1 = 0.6
w_out2 = 0.6
b_out = 0.1
output = h1 * w_out1 + h2 * w_out2 + b_out
if output > 0.5:
    output = 1
else:
    output = 0
print("Скрытый слой:", h1, h2)
print("Результат:", output)
input()