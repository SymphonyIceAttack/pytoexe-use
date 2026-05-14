import urllib.request
import urllib.parse
from html.parser import HTMLParser
import webbrowser
import os
import json
import re

# ===== НАСТРОЙКИ АПТЕК =====
PHARMACIES = [
    {
        "name": "Планета Здоровья",
        "url": "https://planetazdorovo.ru/search/?q={QUERY}"
    },
    {
        "name": "apteka-april.ru",
        "url": "https://apteka-april.ru/search/{QUERY}"
    },
    {
        "name": "Аптека.ру",
        "url": "https://apteka.ru/search/?q={QUERY}"
    }
]

def fetch_page(url):
    """Загружает страницу"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def extract_prices(html, drug):
    """Извлекает цены из HTML"""
    prices = []
    
    # Ищем цены по паттерну: цифры + пробел + ₽/руб
    price_pattern = re.findall(r'(\d+[.,]?\d*)\s*[₽руб]', html)
    
    # Ищем названия товаров рядом с ценами
    name_pattern = re.findall(r'itemprop="name"[^>]*>([^<]+)', html)
    
    # Если есть и названия и цены
    if name_pattern and price_pattern:
        for i, name in enumerate(name_pattern):
            if drug.lower() in name.lower() and i < len(price_pattern):
                prices.append({
                    'name': name.strip(),
                    'price': price_pattern[i] + ' ₽'
                })
    
    # Если только цены
    if not prices and price_pattern:
        for p in price_pattern[:10]:
            prices.append({
                'name': drug,
                'price': p + ' ₽'
            })
    
    return prices

def search_pharmacy(pharmacy, drug):
    """Ищет препарат в аптеке"""
    url = pharmacy['url'].replace('{QUERY}', urllib.parse.quote(drug))
    html = fetch_page(url)
    
    if not html:
        return [{'name': drug, 'price': 'ошибка загрузки'}]
    
    items = extract_prices(html, drug)
    return items if items else [{'name': drug, 'price': 'не найдено'}]

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
    
    print('\nВведите номера аптек через запятую (или Enter для всех):')
    choice = input('> ').strip()
    
    if choice:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [PHARMACIES[i] for i in indices if 0 <= i < len(PHARMACIES)]
        except:
            selected = PHARMACIES
    else:
        selected = PHARMACIES
    
    print(f'\n✅ Выбрано аптек: {len(selected)}')
    
    # Ввод препаратов
    print('\n🔍 Введите препараты (каждый с новой строки, "готово" для завершения):')
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
    results = []
    for drug in drugs:
        print(f'\n🔍 Ищем: {drug}')
        drug_results = {'drug': drug, 'prices': []}
        
        for pharmacy in selected:
            print(f'  📋 {pharmacy["name"]}...', end=' ')
            items = search_pharmacy(pharmacy, drug)
            print(f'найдено: {len(items)}')
            
            for item in items:
                drug_results['prices'].append({
                    'pharmacy': pharmacy['name'],
                    'name': item['name'],
                    'price': item['price']
                })
        
        results.append(drug_results)
    
    # Сохранение
    html = generate_html(results)
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prices_result.html')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'\n✅ Результаты сохранены: {filepath}')
    webbrowser.open('file://' + filepath)
    input('\nНажмите Enter для выхода...')

if __name__ == '__main__':
    main()