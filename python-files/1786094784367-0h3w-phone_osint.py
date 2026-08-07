import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import requests
import json
import re
import os
from datetime import datetime

def clean_phone(phone):
    """Очищает номер от лишних символов"""
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

def get_phone_info(phone):
    """Базовая информация по номеру"""
    try:
        num = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(num):
            return {'error': 'Неверный формат номера'}
        
        country = geocoder.description_for_number(num, 'ru')
        operator = carrier.name_for_number(num, 'ru')
        tz = timezone.time_zones_for_number(num)
        
        # Определяем страну по коду
        country_code = str(num.country_code)
        
        return {
            'phone': phone,
            'country': country,
            'country_code': country_code,
            'operator': operator if operator else 'Не определён',
            'timezone': list(tz) if tz else ['Не определён'],
            'is_valid': True,
            'is_possible': phonenumbers.is_possible_number(num)
        }
    except Exception as e:
        return {'error': str(e)}

def check_breach_db(phone):
    """Проверка номера в публичных базах утечек (через Have I Been Pwned)"""
    try:
        # Убираем + для запроса
        clean = phone.replace('+', '').replace(' ', '')
        # Проверяем через API
        url = f"https://haveibeenpwned.com/api/v3/phone/{clean}"
        headers = {'User-Agent': 'RyzenOSINT/1.0'}
        response = requests.get(url, timeout=10, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'found_in_breaches': True,
                'breaches': data if isinstance(data, list) else [data]
            }
        elif response.status_code == 404:
            return {'found_in_breaches': False}
        else:
            return {'error': f'Статус {response.status_code}'}
    except:
        return {'error': 'Не удалось проверить базы'}

def get_geolocation(phone):
    """Попытка определить регион по первым цифрам (только страна)"""
    # Здесь можно добавить API 2GIS или Dadata для более точной геолокации
    # Но без платного API точного местоположения не получить
    return {'location': 'Определяется только страна по коду'}

def save_report(data, phone):
    """Сохраняет отчёт в файл"""
    filename = f"report_{phone.replace('+', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("ОТЧЁТ ПО НОМЕРУ ТЕЛЕФОНА\n")
        f.write("="*50 + "\n\n")
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
    return filename

def main():
    print("\n" + "="*50)
    print("   RYZEN PHONE OSINT TOOL v1.0")
    print("="*50 + "\n")
    
    phone_input = input("Введите номер телефона (например, +79991234567): ").strip()
    phone = clean_phone(phone_input)
    
    print("\n[+] Обработка...\n")
    
    # Получаем базовую информацию
    info = get_phone_info(phone)
    
    if 'error' in info:
        print(f"[!] Ошибка: {info['error']}")
        return
    
    print("[+] Данные по номеру:")
    print("-"*40)
    print(f"  Номер: {info['phone']}")
    print(f"  Страна: {info['country']}")
    print(f"  Код страны: +{info['country_code']}")
    print(f"  Оператор: {info['operator']}")
    print(f"  Часовой пояс: {', '.join(info['timezone'])}")
    print(f"  Корректный: {'Да' if info['is_valid'] else 'Нет'}")
    
    # Проверка в базах (опционально)
    print("\n[+] Проверка в базах утечек...")
    breach = check_breach_db(phone)
    
    if 'found_in_breaches' in breach:
        if breach['found_in_breaches']:
            print(f"  [!] Номер найден в базах утечек!")
            if 'breaches' in breach and breach['breaches']:
                for b in breach['breaches']:
                    if isinstance(b, dict):
                        print(f"      - {b.get('Name', 'Неизвестно')}")
        else:
            print("  [✓] Номер не найден в публичных базах")
    else:
        print(f"  [!] {breach.get('error', 'Ошибка проверки')}")
    
    # Сохраняем отчёт
    report_data = {**info, **breach}
    filename = save_report(report_data, phone)
    print(f"\n[✓] Отчёт сохранён в файл: {filename}")
    
    input("\nНажмите Enter для выхода...")

if __name__ == '__main__':
    main()