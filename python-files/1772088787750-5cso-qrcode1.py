import qrcode
import os

def create_qr():
    """
    Функция для создания QR-кода из пользовательского ввода.
    Сохраняет результат в PNG-файл.
    """
    print("=== Генератор QR-кода ===")
    
    # Получаем текст от пользователя
    text = input("Введите текст или ссылку для кодирования: ").strip()
    
    if not text:
        print("Ошибка: ничего не введено!")
        return
    
    # Спрашиваем имя файла (по умолчанию — qr_code.png)
    filename = input("Имя файла (без расширения, по умолчанию 'qr_code'): ").strip()
    if not filename:
        filename = "qr_code"
    filename = f"{filename}.png"  # Добавляем расширение
    
    
    try:
        # Создаём объект QR-кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Добавляем данные
        qr.add_data(text)
        qr.make(fit=True)
        
        # Генерируем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохраняем файл
        img.save(filename)
        
        print(f"\n✓ QR-код успешно создан: {os.path.abspath(filename)}")
        print(f"Размер изображения: {img.size} пикселей")
        print("\nТеперь вы можете отсканировать QR-код камерой смартфона!")
        
    except Exception as e:
        print(f"\n✗ Ошибка при создании QR-кода: {type(e).__name__}: {e}")


if __name__ == "__main__":
    create_qr()
