import pyautogui
import time
import json
import os
import pyperclip


class GModFastCommander:
    def __init__(self, config_file="steam_ids.json"):
        self.config_file = config_file
        self.steam_ids = self.load_steam_ids()
        self.delay = 0.5  # Быстрая задержка между командами

    def load_steam_ids(self):
        """Загружает Steam ID из JSON файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("steam_ids", [])
            except:
                print("❌ Ошибка чтения файла. Создаю новый список.")
                return []
        return []

    def save_steam_ids(self, ids_list):
        """Сохраняет Steam ID в JSON файл"""
        data = {"steam_ids": ids_list}
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_txt(self):
        """Импортирует Steam ID из текстового файла"""
        print("\n📥 ИМПОРТ ИЗ ТЕКСТОВОГО ФАЙЛА")
        print("Формат файла: каждый Steam ID на новой строке")
        print("Пример:")
        print("STEAM_0:0:499240319")
        print("STEAM_0:1:514343291")
        print("-" * 40)

        file_path = input("Введите путь к файлу (или нажмите Enter для 'steam_ids.txt'): ").strip()

        if not file_path:
            file_path = "steam_ids.txt"

        try:
            if not os.path.exists(file_path):
                print(f"❌ Файл не найден: {file_path}")
                return

            imported_ids = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        if line.startswith('STEAM_'):
                            # Автоматически генерируем имя
                            name = f"ID_{len(self.steam_ids) + len(imported_ids) + 1}"
                            imported_ids.append({"id": line, "name": name})
                            print(f"   {line_num}: ✅ {line}")
                        else:
                            print(f"   {line_num}: ⚠ Пропущено (неправильный формат): {line}")

            if imported_ids:
                confirm = input(f"\nНайдено {len(imported_ids)} Steam ID. Добавить в список? (y/n): ").lower()
                if confirm == 'y':
                    self.steam_ids.extend(imported_ids)
                    self.save_steam_ids(self.steam_ids)
                    print(f"✅ Импортировано {len(imported_ids)} Steam ID")
                else:
                    print("❌ Импорт отменен")
            else:
                print("❌ В файле не найдено подходящих Steam ID")

        except Exception as e:
            print(f"❌ Ошибка при чтении файла: {e}")

    def send_command_fast(self, steam_id):
        """Быстро печатает команду 'say !info STEAMID'"""
        command = f'say !info {steam_id}'

        # Используем буфер обмена для надежности
        pyperclip.copy(command)

        # Даем небольшую паузу для буфера обмена
        time.sleep(0.1)

        # Быстрая вставка из буфера обмена
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)  # Пауза для вставки

        # Нажимаем Enter
        pyautogui.press('enter')
        time.sleep(0.2)  # Пауза после отправки

        return command

    def send_all_commands_fast(self):
        """Быстро отправляет все команды"""
        if not self.steam_ids:
            print("❌ Нет Steam ID в списке!")
            print("Сначала добавьте Steam ID через меню (опция 3 или 4)")
            return

        print(f"\n⚡ Начинаю быструю отправку {len(self.steam_ids)} команд...")
        print(f"⏱️ Задержка между командами: {self.delay} сек")
        print("\n⚠ ИНСТРУКЦИЯ:")
        print("1. Откройте Garry's Mod")
        print("2. Откройте консоль (клавиша `)")
        print("3. Убедитесь, что курсор мигает в поле ввода")
        print("4. Убедитесь, что в поле ввода НИЧЕГО НЕТ")
        print("5. Не трогайте мышь/клавиатуру")
        print("6. Убедитесь, что в игре ВЫБРАН АНГЛИЙСКИЙ ЯЗЫК РАСКЛАДКИ!")
        print("\n⏳ Начинаю через 5 секунд...")

        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)

        print("\n🚀 Начинаю отправку!")

        for idx, player in enumerate(self.steam_ids, 1):
            steam_id = player['id']

            print(f"{idx}/{len(self.steam_ids)}: say !info {steam_id}")

            # Отправляем команду
            try:
                self.send_command_fast(steam_id)
                print(f"   ✅ Успешно")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

            # Ждем перед следующей командой
            if idx < len(self.steam_ids):
                time.sleep(self.delay)

        print(f"\n✅ Готово! Отправлено {len(self.steam_ids)} команд")

    def add_steam_id(self):
        """Добавляет Steam ID вручную - БЕЗ ЗАПРОСА НИКА"""
        print("\n➕ ДОБАВЛЕНИЕ STEAM ID")
        steam_id = input("Введите Steam ID (например STEAM_0:1:503730268): ").strip()

        if steam_id:
            # Автоматически генерируем имя
            name = f"ID_{len(self.steam_ids) + 1}"

            self.steam_ids.append({"id": steam_id, "name": name})
            self.save_steam_ids(self.steam_ids)
            print(f"✅ Добавлен Steam ID: {steam_id}")
        else:
            print("❌ Steam ID не может быть пустым!")

    def remove_selected_steam_id(self):
        """Удаляет выбранный Steam ID"""
        if not self.steam_ids:
            print("❌ Список пуст! Нечего удалять.")
            return

        # Показываем список с номерами
        print("\n🗑️ УДАЛЕНИЕ STEAM ID")
        print("Список Steam ID:")
        print("-" * 50)
        for idx, player in enumerate(self.steam_ids, 1):
            print(f"{idx}. {player['id']}")
        print("-" * 50)

        try:
            choice = input(f"\nВведите номер для удаления (1-{len(self.steam_ids)}) или 0 для отмены: ").strip()

            if choice == '0':
                print("❌ Удаление отменено")
                return

            idx = int(choice) - 1

            if 0 <= idx < len(self.steam_ids):
                removed_id = self.steam_ids[idx]['id']
                self.steam_ids.pop(idx)
                self.save_steam_ids(self.steam_ids)
                print(f"✅ Удален Steam ID: {removed_id}")
            else:
                print("❌ Неверный номер!")

        except ValueError:
            print("❌ Введите корректный номер!")
        except Exception as e:
            print(f"❌ Ошибка при удалении: {e}")

    def clear_all_ids(self):
        """Очищает все Steam ID"""
        if not self.steam_ids:
            print("❌ Список уже пустой!")
            return

        confirm = input("Очистить весь список Steam ID? (y/n): ").lower()
        if confirm == 'y':
            self.steam_ids = []
            self.save_steam_ids(self.steam_ids)
            print("✅ Весь список очищен!")
        else:
            print("❌ Отменено.")

    def show_steam_ids(self):
        """Показывает список Steam ID"""
        if not self.steam_ids:
            print("❌ Список пуст!")
            return

        print(f"\n📋 Steam ID в списке ({len(self.steam_ids)}):")
        print("-" * 50)
        for idx, player in enumerate(self.steam_ids, 1):
            print(f"{idx}. {player['id']}")
        print("-" * 50)

    def export_to_txt(self):
        """Экспортирует Steam ID в текстовый файл"""
        if not self.steam_ids:
            print("❌ Нет Steam ID для экспорта!")
            return

        print("\n📤 ЭКСПОРТ В ТЕКСТОВЫЙ ФАЙЛ")
        file_path = input("Введите путь к файлу (или нажмите Enter для 'exported_steamids.txt'): ").strip()

        if not file_path:
            file_path = "exported_steamids.txt"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for player in self.steam_ids:
                    f.write(f"{player['id']}\n")

            print(f"✅ Экспортировано {len(self.steam_ids)} Steam ID в файл: {file_path}")

        except Exception as e:
            print(f"❌ Ошибка при экспорте: {e}")

    def test_command(self):
        """Тест отправки одной команды"""
        if not self.steam_ids:
            print("❌ Нет Steam ID для теста!")
            return

        print("\n🧪 ТЕСТ ОДНОЙ КОМАНДЫ")
        print("Убедитесь, что консоль GMod открыта и активно!")
        print("\n⏳ Начинаю через 5 секунд...")

        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)

        # Берем первый Steam ID
        steam_id = self.steam_ids[0]['id']
        command = f'say !info {steam_id}'

        print(f"\nОтправляю: {command}")

        try:
            self.send_command_fast(steam_id)
            print(f"✅ Команда отправлена!")
            print("Проверьте в чате GMod")
        except Exception as e:
            print(f"❌ Ошибка: {e}")


def main():
    print("=" * 60)
    print("⚡ Упрощенный пробив стимаков for ST состав UmbrellaRP")
    print("⚡ Автоматически вводит say !info со стимаками из списка")
    print("⚡ made by Less ")
    print("=" * 60)

    commander = GModFastCommander()

    while True:
        print(f"\n📊 Steam ID в списке: {len(commander.steam_ids)}")
        print(f"⏱️ Задержка: {commander.delay} сек")
        print("\n📱 МЕНЮ:")
        print("1 - Быстро отправить ВСЕ команды")
        print("2 - Показать список Steam ID")
        print("3 - Добавить Steam ID ")
        print("4 - Удалить выбранный Steam ID")
        print("5 - Импортировать из текстового файла")
        print("6 - Очистить весь список")
        print("0 - Выход")
        print("-" * 40)

        try:
            choice = input("Выбор: ").strip()

            if choice == "1":
                commander.send_all_commands_fast()

            elif choice == "2":
                commander.show_steam_ids()

            elif choice == "3":
                commander.add_steam_id()

            elif choice == "4":
                commander.remove_selected_steam_id()

            elif choice == "5":
                commander.import_from_txt()

            elif choice == "6":
                commander.test_command()

            elif choice == "0":
                print("👋 Выход...")
                break

            else:
                print("❌ Неверный выбор!")

        except KeyboardInterrupt:
            print("\n\n⚠ Программа прервана")
            break


if __name__ == "__main__":

    try:
        import pyautogui
        import pyperclip

        # Установим паузу для безопасности
        pyautogui.PAUSE = 0.1

        # Проверка доступности буфера обмена
        try:
            test_text = "test"
            pyperclip.copy(test_text)
            time.sleep(0.1)
            if pyperclip.paste() == test_text:
                print()
            else:
                print("⚠ Возможны проблемы с буфером обмена")
        except:
            print("⚠ Проблемы с доступом к буферу обмена")

        main()
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Установите библиотеки: pip install pyautogui pyperclip")
        input("Нажмите Enter...")