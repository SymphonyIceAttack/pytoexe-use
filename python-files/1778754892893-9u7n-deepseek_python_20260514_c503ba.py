import requests
from bs4 import BeautifulSoup
import webbrowser
import os
import sys
import json
from urllib.parse import quote

# ===== НАСТРОЙКИ АПТЕК =====
PHARMACIES = [
    {
        "name": "Планета Здоровья",
        "url": "https://planetazdorovo.ru/search/?q={QUERY}",
        "name_selector": "[itemprop='name']",
        "price_selector": "[itemprop='price']"
    },
    {
        "name": "apteka-april.ru",
        "url": "https://apteka-april.ru/search/{QUERY}",
        "product_selector": ".c-product-card",
        "name_selector": ".name span",
        "price_selector": ".prices > div:nth-of-type(1) span:last-child"
    },
    {
        "name": "Аптека.ру",
        "url": "https://apteka.ru/search/?q={QUERY}",
        "price_selector": ".CardPrice span"
    }
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}

def search_pharmacy(pharmacy, drug):
    """Ищет препарат в одной аптеке"""
    url = pharmacy['url'].replace('{QUERY}', quote(drug))
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return [{'name': drug, 'price': f'ошибка: {str(e)[:50]}'}]
    
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []
    
    # Метод 1: product_selector
    if 'product_selector' in pharmacy:
        cards = soup.select(pharmacy['product_selector'])
        for card in cards:
            name_el = card.select_one(pharmacy['name_selector']) if pharmacy.get('name_selector') else None
            price_el = card.select_one(pharmacy['price_selector']) if pharmacy.get('price_selector') else None
            
            name = name_el.text.strip() if name_el else ''
            price = price_el.text.strip() if price_el else ''
            
            if name and price and drug.lower() in name.lower():
                items.append({'name': name, 'price': price})
    
    # Метод 2: name_selector + price_selector
    if not items and pharmacy.get('name_selector') and pharmacy.get('price_selector'):
        names = soup.select(pharmacy['name_selector'])
        prices = soup.select(pharmacy['price_selector'])
        
        for i, name_el in enumerate(names):
            name = name_el.text.strip()
            if drug.lower() not in name.lower():
                continue
            
            price = prices[i].get('content', prices[i].text.strip()) if i < len(prices) else ''
            if price:
                items.append({'name': name, 'price': price})
    
    # Метод 3: только price_selector
    if not items and pharmacy.get('price_selector'):
        price_els = soup.select(pharmacy['price_selector'])
        for el in price_els[:10]:
            price = el.get('content', el.text.strip())
            if price:
                items.append({'name': drug, 'price': price})
    
    return items if items else [{'name': drug, 'price': 'не найдено'}]

def compare_prices(drugs, selected_pharmacies):
    """Сравнивает цены по всем выбранным аптекам"""
    results = []
    
    for drug in drugs:
        drug_results = {'drug': drug, 'prices': []}
        print(f'🔍 Ищем: {drug}')
        
        for pharmacy in selected_pharmacies:
            print(f'  📋 {pharmacy["name"]}...')
            items = search_pharmacy(pharmacy, drug)
            for item in items:
                drug_results['prices'].append({
                    'pharmacy': pharmacy['name'],
                    'name': item['name'],
                    'price': item['price']
                })
        
        results.append(drug_results)
    
    return results

def generate_html(results):
    """Создаёт HTML-страницу с результатами"""
    html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Сравнение цен на лекарства</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; max-width: 900px; margin: 0 auto; padding: 20px; }
        h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: #4a90e2; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
        .drug-section { margin: 30px 0; }
        .drug-title { color: #4a90e2; border-bottom: 2px solid #4a90e2; padding-bottom: 5px; }
    </style>
</head>
<body>
    <h2>💊 Результаты сравнения цен</h2>
'''
    
    for result in results:
        html += f'<div class="drug-section"><h3 class="drug-title">{result["drug"]}</h3>'
        html += '<table><tr><th>Аптека</th><th>Товар</th><th>Цена</th></tr>'
        
        for item in result['prices']:
            html += f'<tr><td>{item["pharmacy"]}</td><td>{item["name"]}</td><td>{item["price"]}</td></tr>'
        
        html += '</table></div>'
    
    html += '</body></html>'
    return html

def main():
    print('\n' + '='*50)
    print('💊 СРАВНЕНИЕ ЦЕН НА ЛЕКАРСТВА')
    print('='*50)
    
    # Выбор аптек
    print('\n📋 Доступные аптеки:')
    for i, ph in enumerate(PHARMACIES, 1):
        print(f'  {i}. {ph["name"]}')
    
    print('\nВведите номера аптек через запятую (например: 1,2,3)')
    print('Или нажмите Enter для выбора всех:')
    
    choice = input('> ').strip()
    
    if choice:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [PHARMACIES[i] for i in indices if 0 <= i < len(PHARMACIES)]
        except:
            print('❌ Ошибка ввода. Выбраны все аптеки.')
            selected = PHARMACIES
    else:
        selected = PHARMACIES
    
    if not selected:
        print('❌ Не выбрано ни одной аптеки.')
        input('Нажмите Enter для выхода...')
        return
    
    print(f'\n✅ Выбрано аптек: {len(selected)}')
    
    # Ввод препаратов
    print('\n🔍 Введите препараты (каждый с новой строки):')
    print('Введите "готово" для завершения:')
    
    drugs = []
    while True:
        drug = input('> ').strip()
        if drug.lower() == 'готово':
            break
        if drug:
            drugs.append(drug)
    
    if not drugs:
        print('❌ Не введено ни одного препарата.')
        input('Нажмите Enter для выхода...')
        return
    
    # Поиск
    print('\n⏳ Выполняется поиск...')
    results = compare_prices(drugs, selected)
    
    # Сохранение результатов
    html = generate_html(results)
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prices_result.html')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'\n✅ Результаты сохранены: {filepath}')
    webbrowser.open('file://' + filepath)
    
    print('\nНажмите Enter для выхода...')
    input()

if __name__ == '__main__':
    main()