import math


def calculate_probability(beta0, beta1, beta2, delta_xG, H):
    """
    Вычисляет вероятность P(home) по логистической функции:
    P(home) = 1 / (1 + exp(-(beta0 + beta1 * delta_xG + beta2 * H)))
    """
    linear_combination = beta0 + beta1 * delta_xG + beta2 * H
    try:
        probability = 1.0 / (1.0 + math.exp(-linear_combination))
    except OverflowError:
        # Если exp переполнен из-за очень большого положительного аргумента,
        # вероятность близка к 1.
        if linear_combination > 0:
            probability = 1.0
        else:
            probability = 0.0
    return probability


def main():
    print("Вычисление P(home) по формуле:")
    print("P = 1 / (1 + exp(-(β0 + β1·ΔxG + β2·H)))")
    print("Введите числовые значения (допускаются целые и дробные числа):")

    try:
        beta0 = float(input("β0 = "))
        beta1 = float(input("β1 = "))
        beta2 = float(input("β2 = "))
        delta_xG = float(input("ΔxG = "))
        H = float(input("H = "))
    except ValueError:
        print("Ошибка: необходимо вводить числа (целые или с плавающей точкой).")
        return

    prob = calculate_probability(beta0, beta1, beta2, delta_xG, H)
    print(f"\nРезультат: P(home) = {prob:.6f}")


if __name__ == "__main__":
    main()







