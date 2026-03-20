from itertools import permutations, combinations

def generate_word_combinations():
    # Запрашиваем ввод слов у пользователя
    input_words = input("Введите слова через пробел: ").strip()
    
    # Проверяем, что ввод не пустой
    if not input_words:
        print("Список слов пуст")
        return
    
    # Разбиваем введенные слова на список
    words_list = input_words.split()
    
    # Проверяем, что список не пустой после разбиения
    if not words_list:
        print("Список слов пуст после обработки")
        return
    
    print("\nВсе возможные перестановки слов:")
    for perm in permutations(words_list):
        print(' '.join(perm))
    
    print("\nВсе возможные комбинации слов:")
    for r in range(1, len(words_list) + 1):
        print(f"\nКомбинации из {r} слов:")
        for comb in combinations(words_list, r):
            print(' '.join(comb))

# Запуск программы
if __name__ == "__main__":
    generate_word_combinations()
