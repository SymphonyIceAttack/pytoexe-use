from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse
import socket
import json
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class AdvancedIPScanner:
    def __init__(self, timeout=30, max_workers=10):
        self.timeout = timeout
        self.max_workers = max_workers
        
    def get_ips_with_partial_load(self, url):
        """
        Получаем IP даже для частично загруженных ресурсов
        """
        
        print(f"\n{'='*60}")
        print(f"ПРОДВИНУТОЕ СКАНИРОВАНИЕ: {url}")
        print(f"Таймаут: {self.timeout} секунд")
        print(f"{'='*60}")
        
        # Настройка браузера с дополнительными опциями
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Увеличиваем буфер для логов
        options.set_capability('goog:loggingPrefs', {
            'performance': 'ALL',
            'browser': 'ALL'
        })
        
        # Дополнительные настройки для лучшего захвата запросов
        experimental_options = {
            'excludeSwitches': ['enable-automation'],
            'useAutomationExtension': False,
        }
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = None
        all_ips = set()
        all_domains = set()
        
        try:
            # Создаем драйвер
            driver = webdriver.Chrome(options=options)
            
            # Устанавливаем таймауты
            driver.set_page_load_timeout(self.timeout)
            driver.set_script_timeout(self.timeout)
            
            # Включаем сетевые условия (имитируем медленное соединение для захвата большего кол-ва запросов)
            try:
                driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                    'offline': False,
                    'latency': 100,  # 100ms задержка
                    'downloadThroughput': 1.5 * 1024 * 1024,  # 1.5 Mbps
                    'uploadThroughput': 750 * 1024,  # 750 Kbps
                    'connectionType': 'cellular3g'
                })
            except:
                pass  # Если не поддерживается, продолжаем
            
            print("\n1. НАЧАЛО ЗАГРУЗКИ СТРАНИЦЫ")
            print(f"   Время: {datetime.now().strftime('%H:%M:%S')}")
            
            # Запускаем мониторинг логов в отдельном потоке
            logs_buffer = []
            stop_monitoring = threading.Event()
            
            def monitor_logs():
                """Мониторим логи в реальном времени"""
                nonlocal logs_buffer
                try:
                    while not stop_monitoring.is_set():
                        try:
                            new_logs = driver.get_log('performance')
                            logs_buffer.extend(new_logs)
                            time.sleep(0.5)  # Частота опроса
                        except:
                            time.sleep(1)
                except:
                    pass
            
            # Запускаем мониторинг
            monitor_thread = threading.Thread(target=monitor_logs, daemon=True)
            monitor_thread.start()
            
            # Функция для захвата ресурсов, которые начинают загружаться
            capture_script = """
            // Захватываем все начатые загрузки
            window._capturedResources = new Set();
            
            // Перехватываем XMLHttpRequest
            (function() {
                var originalOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
                    if (url && url.startsWith('http')) {
                        window._capturedResources.add(url);
                    }
                    return originalOpen.apply(this, arguments);
                };
            })();
            
            // Перехватываем fetch
            (function() {
                var originalFetch = window.fetch;
                window.fetch = function(resource, init) {
                    if (resource && typeof resource === 'string' && resource.startsWith('http')) {
                        window._capturedResources.add(resource);
                    } else if (resource && resource.url) {
                        window._capturedResources.add(resource.url);
                    }
                    return originalFetch.apply(this, arguments);
                };
            })();
            
            // Мониторим создание элементов
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1) { // ELEMENT_NODE
                                ['src', 'href', 'data', 'action'].forEach(function(attr) {
                                    var value = node.getAttribute(attr);
                                    if (value && value.startsWith('http')) {
                                        window._capturedResources.add(value);
                                    }
                                });
                            }
                        });
                    }
                });
            });
            
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
            
            return 'Resource capture initialized';
            """
            
            # Внедряем скрипт для захвата ресурсов
            try:
                driver.execute_script(capture_script)
                print("   ✓ Система захвата ресурсов активирована")
            except:
                print("   ⚠ Не удалось активировать захват ресурсов")
            
            # Загружаем страницу
            start_time = time.time()
            load_success = False
            
            try:
                driver.get(url)
                
                # Ждем хотя бы частичной загрузки
                try:
                    driver.execute_async_script("""
                        var callback = arguments[arguments.length - 1];
                        var checkState = function() {
                            if (document.readyState === 'complete' || 
                                document.readyState === 'interactive' ||
                                document.querySelector('body')) {
                                callback('loaded');
                            } else {
                                setTimeout(checkState, 100);
                            }
                        };
                        checkState();
                    """)
                    load_success = True
                    print("   ✓ Страница начала загружаться")
                except:
                    print("   ⚠ Страница загружается медленно")
                    
            except TimeoutException:
                print("   ⚠ ТАЙМАУТ: Превышено время ожидания загрузки")
                print("   Продолжаем анализ уже начатых запросов...")
            except Exception as e:
                print(f"   ✗ Ошибка загрузки: {str(e)[:100]}...")
            
            # Даем время для начала загрузки ресурсов
            print(f"\n2. ОЖИДАНИЕ НАЧАЛА ЗАГРУЗКИ РЕСУРСОВ")
            print("   (ждем начала сетевых запросов)")
            
            wait_start = time.time()
            resources_found = 0
            
            while time.time() - wait_start < min(15, self.timeout/2):
                try:
                    # Проверяем количество логов
                    current_logs = len(logs_buffer)
                    
                    # Пытаемся получить ресурсы через внедренный скрипт
                    try:
                        captured = driver.execute_script("return Array.from(window._capturedResources || [])")
                        if captured and len(captured) > resources_found:
                            resources_found = len(captured)
                            print(f"   ✓ Найдено ресурсов: {resources_found}")
                    except:
                        pass
                    
                    if current_logs > 50 or resources_found > 20:
                        print(f"   ✓ Достаточно ресурсов для анализа")
                        break
                    
                    time.sleep(1)
                    
                except:
                    time.sleep(1)
            
            # Останавливаем мониторинг
            stop_monitoring.set()
            monitor_thread.join(timeout=2)
            
            print(f"\n3. АНАЛИЗ ЗАХВАЧЕННЫХ ДАННЫХ")
            
            # Собираем все URL из разных источников
            all_urls = set()
            
            # 1. Из логов DevTools
            print(f"   Анализ логов DevTools ({len(logs_buffer)} записей)...")
            for entry in logs_buffer:
                try:
                    log_data = json.loads(entry['message'])['message']
                    
                    # Запросы, которые начались
                    if log_data['method'] in ['Network.requestWillBeSent', 'Network.responseReceived']:
                        if 'params' in log_data and 'request' in log_data['params']:
                            request_url = log_data['params']['request']['url']
                            if request_url:
                                all_urls.add(request_url)
                    
                    # WebSocket соединения
                    elif log_data['method'] in ['Network.webSocketCreated', 'Network.webSocketWillSendHandshakeRequest']:
                        if 'params' in log_data and 'url' in log_data['params']:
                            ws_url = log_data['params']['url']
                            if ws_url:
                                all_urls.add(ws_url)
                                
                except:
                    continue
            
            # 2. Из внедренного скрипта
            print("   Анализ перехваченных ресурсов...")
            try:
                captured_resources = driver.execute_script("return Array.from(window._capturedResources || [])")
                for resource in captured_resources:
                    if resource:
                        all_urls.add(resource)
            except:
                pass
            
            # 3. Из DOM элементов
            print("   Анализ DOM элементов...")
            try:
                selectors = [
                    '[src]', '[href]', '[data-src]', '[data-href]', 
                    '[action]', 'link[href]', 'script[src]', 'img[src]',
                    'iframe[src]', 'source[src]', 'video[src]', 'audio[src]',
                    'embed[src]', 'object[data]'
                ]
                
                for selector in selectors:
                    try:
                        elements = driver.find_elements_by_css_selector(selector)
                        for elem in elements:
                            for attr in ['src', 'href', 'data-src', 'data-href', 'action', 'data']:
                                value = elem.get_attribute(attr)
                                if value and (value.startswith('http://') or value.startswith('https://')):
                                    all_urls.add(value)
                    except:
                        continue
            except:
                pass
            
            # 4. Из JavaScript переменных (попытка найти скрытые URL)
            print("   Поиск URL в JavaScript...")
            js_patterns = [
                "Array.from(document.querySelectorAll('*')).map(el => el.outerHTML).join(' ')",
                "JSON.stringify(window.performance.getEntriesByType('resource').map(r => r.name))",
                "(function(){ var urls=[]; for(var key in window){ if(window[key] && typeof window[key] === 'string' && window[key].match(/https?:\\/\\//)){ urls.push(window[key]); } } return JSON.stringify(urls); })()"
            ]
            
            for pattern in js_patterns:
                try:
                    result = driver.execute_script(f"try {{ return {pattern} }} catch(e) {{ return '' }}")
                    if result:
                        import re
                        found_urls = re.findall(r'https?://[^\s\"\']+', str(result))
                        for found_url in found_urls:
                            all_urls.add(found_url)
                except:
                    pass
            
            # Добавляем основной URL
            all_urls.add(url)
            
            print(f"\n4. ОБРАБОТКА НАЙДЕННЫХ URL")
            print(f"   Всего URL: {len(all_urls)}")
            
            # Извлекаем домены
            for url_item in all_urls:
                try:
                    parsed = urlparse(url_item)
                    if parsed.netloc:
                        domain = parsed.netloc.split(':')[0]
                        if domain and domain not in ['localhost', '127.0.0.1', '']:
                            all_domains.add(domain)
                except:
                    continue
            
            print(f"   Уникальных доменов: {len(all_domains)}")
            
            # Разрешаем домены в IP (параллельно для скорости)
            print(f"\n5. РАЗРЕШЕНИЕ ДОМЕНОВ В IP")
            print(f"   Используется {self.max_workers} потоков...")
            
            resolved_ips = {}
            
            def resolve_domain(domain):
                try:
                    ip = socket.gethostbyname(domain)
                    return domain, ip
                except:
                    return domain, None
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_domain = {executor.submit(resolve_domain, domain): domain for domain in all_domains}
                
                resolved_count = 0
                for future in as_completed(future_to_domain):
                    domain = future_to_domain[future]
                    try:
                        domain, ip = future.result(timeout=5)
                        if ip:
                            all_ips.add(ip)
                            resolved_ips[domain] = ip
                            resolved_count += 1
                            
                            # Прогресс
                            if resolved_count % 10 == 0:
                                print(f"   Разрешено: {resolved_count}/{len(all_domains)}")
                                
                    except Exception as e:
                        continue
            
            elapsed_time = time.time() - start_time
            
            # Результат
            print(f"\n{'='*60}")
            print("ИТОГОВЫЙ РЕЗУЛЬТАТ:")
            print(f"{'='*60}")
            
            result_info = {
                'total_time': elapsed_time,
                'urls_found': len(all_urls),
                'domains_found': len(all_domains),
                'ips_resolved': len(all_ips),
                'load_success': load_success,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n• Время анализа: {elapsed_time:.1f} секунд")
            print(f"• Найдено URL: {len(all_urls)}")
            print(f"• Найдено доменов: {len(all_domains)}")
            print(f"• Разрешено IP: {len(all_ips)}")
            print(f"• Статус загрузки: {'Полная' if load_success else 'Частичная/Таймаут'}")
            
            if all_ips:
                return sorted(list(all_ips)), resolved_ips, result_info
            else:
                return [], {}, result_info
            
        except Exception as e:
            print(f"\n✗ Критическая ошибка: {e}")
            return [], {}, {'error': str(e)}
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

def save_advanced_results(ips, domain_ip_map, info, url, filename=None):
    """Сохраняем результаты продвинутого сканирования"""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"advanced_ips_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#" * 60 + "\n")
        f.write("# ПРОДВИНУТОЕ СКАНИРОВАНИЕ IP-АДРЕСОВ\n")
        f.write("#" * 60 + "\n\n")
        
        f.write(f"Целевой URL: {url}\n")
        f.write(f"Время начала: {info.get('timestamp', 'N/A')}\n")
        f.write(f"Общее время: {info.get('total_time', 0):.1f} секунд\n")
        f.write(f"Статус загрузки: {'Полная' if info.get('load_success') else 'Частичная/Таймаут'}\n\n")
        
        f.write(f"СТАТИСТИКА:\n")
        f.write(f"• Найдено URL: {info.get('urls_found', 0)}\n")
        f.write(f"• Найдено доменов: {info.get('domains_found', 0)}\n")
        f.write(f"• Разрешено IP: {info.get('ips_resolved', 0)}\n\n")
        
        f.write("-" * 60 + "\n")
        f.write("СПИСОК IP-АДРЕСОВ:\n")
        f.write("(включая адреса из начатых, но не завершенных загрузок)\n")
        f.write("-" * 60 + "\n\n")
        
        # Сортируем IP
        sorted_ips = sorted(ips)
        for i, ip in enumerate(sorted_ips, 1):
            # Находим домены для этого IP
            domains = [d for d, ip_addr in domain_ip_map.items() if ip_addr == ip]
            domains_str = ", ".join(domains[:3])
            if len(domains) > 3:
                domains_str += f" [+{len(domains)-3}]"
            
            f.write(f"{i:3}. {ip:20} ← {domains_str}\n")
    
    return filename

# Основная функция
def main():
    print("=" * 70)
    print("ПРОДВИНУТЫЙ СКАНЕР IP-АДРЕСОВ")
    print("Захватывает даже начатые, но не завершенные загрузки")
    print("=" * 70)
    
    url = input("\nВведите URL для сканирования: ").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        timeout = int(input("Таймаут загрузки (сек, 10-60) [30]: ") or "30")
        timeout = max(10, min(60, timeout))  # Ограничиваем 10-60 секундами
    except:
        timeout = 30
    
    print(f"\nЗапуск сканирования с таймаутом {timeout} секунд...")
    
    scanner = AdvancedIPScanner(timeout=timeout, max_workers=15)
    ips, domain_ip_map, info = scanner.get_ips_with_partial_load(url)
    
    if ips:
        print(f"\n✓ УСПЕХ: Найдено {len(ips)} IP-адресов")
        print("\nПервые 20 IP-адресов:")
        print("-" * 50)
        
        for i, ip in enumerate(sorted(ips)[:20], 1):
            domains = [d for d, ip_addr in domain_ip_map.items() if ip_addr == ip]
            print(f"{i:2}. {ip:15} ← {', '.join(domains[:2])}")
        
        if len(ips) > 20:
            print(f"... и еще {len(ips) - 20} адресов")
        
        # Сохраняем
        filename = save_advanced_results(ips, domain_ip_map, info, url)
        print(f"\n✓ Полные результаты сохранены в: {filename}")
        
        # Дополнительно: сохраняем детальный отчет
        detail_file = f"detailed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(detail_file, 'w', encoding='utf-8') as f:
            f.write(f"Детальный отчет по сканированию: {url}\n")
            f.write(f"{'='*60}\n\n")
            
            f.write("ВСЕ ДОМЕНЫ И ИХ IP:\n")
            f.write("-" * 40 + "\n")
            for domain, ip in sorted(domain_ip_map.items()):
                f.write(f"{domain}\n  → {ip}\n")
            
            f.write(f"\n{'='*60}\n")
            f.write("ИСТОЧНИКИ ДАННЫХ:\n")
            f.write(f"• Логи DevTools Network API\n")
            f.write(f"• Перехваченные XHR/Fetch запросы\n")
            f.write(f"• DOM элементы с внешними ресурсами\n")
            f.write(f"• JavaScript анализ\n")
            f.write(f"• WebSocket соединения\n")
        
        print(f"✓ Детальный отчет сохранен в: {detail_file}")
        
    else:
        print("\n✗ IP-адресы не найдены")
        print("Рекомендации:")
        print("1. Попробуйте увеличить таймаут (60 секунд)")
        print("2. Проверьте доступность сайта")
        print("3. Возможно, сайт блокирует автоматизированные запросы")

if __name__ == "__main__":
    main()
