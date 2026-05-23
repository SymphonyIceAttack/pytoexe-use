def print_board(board):
    """Выводит игровое поле"""
    print("\n")
    for i in range(3):
        print(" " + " | ".join(board[i*3:(i+1)*3]))
        if i < 2:
            print("---+---+---")
    print("\n")

def check_winner(board, player):
    """Проверяет, выиграл ли игрок"""
    win_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # горизонтали
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # вертикали
        [0, 4, 8], [2, 4, 6]              # диагонали
    ]
    
    for combo in win_combinations:
        if all(board[pos] == player for pos in combo):
            return True
    return False

def is_board_full(board):
    """Проверяет, заполнено ли поле"""
    return all(cell != " " for cell in board)

def get_player_move(board, player):
    """Получает ход от игрока"""
    while True:
        try:
            move = input(f"Игрок {player}, введите номер клетки (1-9): ")
            move = int(move) - 1  # Преобразуем в индекс (0-8)
            
            if move < 0 or move > 8:
                print("Пожалуйста, введите число от 1 до 9.")
                continue
                
            if board[move] != " ":
                print("Эта клетка уже занята! Выберите другую.")
                continue
                
            return move
        except ValueError:
            print("Пожалуйста, введите число от 1 до 9.")

def play_game():
    """Основная функция игры"""
    print("=" * 40)
    print("       КРЕСТИКИ-НОЛИКИ")
    print("=" * 40)
    print("\nКлетки пронумерованы так:")
    print(" 1 | 2 | 3 ")
    print("---+---+---")
    print(" 4 | 5 | 6 ")
    print("---+---+---")
    print(" 7 | 8 | 9 ")
    print("\n" + "=" * 40)
    
    # Инициализация игры
    board = [" "] * 9  # Пустое поле 3x3
    current_player = "X"
    game_over = False
    
    while not game_over:
        print_board(board)
        
        # Ход игрока
        move = get_player_move(board, current_player)
        board[move] = current_player
        
        # Проверка на победу
        if check_winner(board, current_player):
            print_board(board)
            print(f"🎉 Поздравляем! Игрок {current_player} победил! 🎉")
            game_over = True
        # Проверка на ничью
        elif is_board_full(board):
            print_board(board)
            print("🤝 Игра закончилась вничью! 🤝")
            game_over = True
        else:
            # Смена игрока
            current_player = "O" if current_player == "X" else "X"
    
    # Предложение сыграть еще раз
    play_again = input("\nХотите сыграть еще раз? (да/нет): ").lower()
    if play_again in ["да", "д", "yes", "y"]:
        play_game()
    else:
        print("\nСпасибо за игру! До свидания!")

def play_with_computer():
    """Игра против компьютера"""
    import random
    
    print("=" * 40)
    print("   КРЕСТИКИ-НОЛИКИ (против компьютера)")
    print("=" * 40)
    print("\nКлетки пронумерованы так:")
    print(" 1 | 2 | 3 ")
    print("---+---+---")
    print(" 4 | 5 | 6 ")
    print("---+---+---")
    print(" 7 | 8 | 9 ")
    print("\nВы играете за X, компьютер за O")
    print("=" * 40)
    
    board = [" "] * 9
    player = "X"
    computer = "O"
    game_over = False
    
    while not game_over:
        print_board(board)
        
        if player == "X":  # Ход игрока
            move = get_player_move(board, player)
            board[move] = player
        else:  # Ход компьютера
            # Простая логика компьютера: случайный ход
            available_moves = [i for i, cell in enumerate(board) if cell == " "]
            if available_moves:
                move = random.choice(available_moves)
                board[move] = computer
                print(f"Компьютер выбрал клетку {move + 1}")
        
        # Проверка на победу
        if check_winner(board, player if player == "X" else computer):
            print_board(board)
            winner = "Вы" if (player == "X" and check_winner(board, "X")) or \
                            (player == "O" and check_winner(board, "O")) else "Компьютер"
            print(f"🎉 {winner} победили! 🎉")
            game_over = True
        # Проверка на ничью
        elif is_board_full(board):
            print_board(board)
            print("🤝 Игра закончилась вничью! 🤝")
            game_over = True
        else:
            # Смена игрока
            player = "O" if player == "X" else "X"
    
    # Предложение сыграть еще раз
    play_again = input("\nХотите сыграть еще раз? (да/нет): ").lower()
    if play_again in ["да", "д", "yes", "y"]:
        play_with_computer()
    else:
        print("\nСпасибо за игру! До свидания!")

def main_menu():
    """Главное меню игры"""
    while True:
        print("\n" + "=" * 40)
        print("       ГЛАВНОЕ МЕНЮ")
        print("=" * 40)
        print("1. Играть вдвоем")
        print("2. Играть против компьютера")
        print("3. Выход")
        print("=" * 40)
        
        choice = input("Выберите режим (1-3): ")
        
        if choice == "1":
            play_game()
        elif choice == "2":
            play_with_computer()
        elif choice == "3":
            print("\nДо свидания!")
            break
        else:
            print("Неверный выбор. Пожалуйста, выберите 1, 2 или 3.")

# Запуск игры
if __name__ == "__main__":
    main_menu()