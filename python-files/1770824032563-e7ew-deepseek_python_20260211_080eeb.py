import requests
import re
import json
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set, Tuple
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyParser:
    def __init__(self):
        self.proxies = {
            'http': [],
            'https': [],
            'socks4': [],
            'socks5': []
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    # ==================== ИСТОЧНИКИ ДАННЫХ ====================
    
    def parse_github_speedx(self) -> List[str]:
        """Парсинг GitHub репозитория TheSpeedX (очень актуальный источник)"""
        urls = [
            'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
            'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
            'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt'
        ]
        result = []
        for url in urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    proxy_type = 'http' if 'http' in url else 'socks4' if 'socks4' in url else 'socks5'
                    proxies = response.text.strip().split('\n')
                    self.proxies[proxy_type].extend(proxies)
                    result.extend(proxies)
                    logger.info(f"GitHub SpeedX: загружено {len(proxies)} {proxy_type} прокси")
            except Exception as e:
                logger.error(f"Ошибка GitHub SpeedX: {e}")
        return result
    
    def parse_spys_one(self) -> List[str]:
        """Парсинг spys.one - HTTP/HTTPS прокси"""
        proxies = []
        try:
            url = 'https://spys.one/en/proxy-list/'
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            
            # Ищем IP:PORT в тексте
            pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})'
            matches = re.findall(pattern, response.text)
            
            for ip, port in matches:
                proxy = f"{ip}:{port}"
                if self.is_valid_ip_port(proxy):
                    proxies.append(proxy)
                    self.proxies['http'].append(proxy)
            
            logger.info(f"Spys.one: найдено {len(proxies)} прокси")
        except Exception as e:
            logger.error(f"Ошибка Spys.one: {e}")
        return proxies
    
    def parse_proxyscrape_api(self) -> List[str]:
        """Парсинг API proxyscrape.com - быстрый и надежный источник"""
        urls = [
            'https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=10000',
            'https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&timeout=10000',
            'https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5&timeout=10000'
        ]
        result = []
        for url in urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    proxy_type = 'http' if 'http' in url else 'socks4' if 'socks4' in url else 'socks5'
                    proxies = response.text.strip().split('\r\n')
                    self.proxies[proxy_type].extend(proxies)
                    result.extend(proxies)
                    logger.info(f"ProxyScrape: загружено {len(proxies)} {proxy_type} прокси")
            except Exception as e:
                logger.error(f"Ошибка ProxyScrape: {e}")
        return result
    
    def parse_free_proxy_list_net(self) -> List[str]:
        """Парсинг free-proxy-list.net - популярный источник"""
        proxies = []
        try:
            url = 'https://free-proxy-list.net/'
            response = self.session.get(url, timeout=15)
            
            # Поиск строк с прокси в HTML таблице
            rows = re.findall(r'<tr><td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td>', response.text)
            
            for ip, port in rows:
                proxy = f"{ip}:{port}"
                if self.is_valid_ip_port(proxy):
                    proxies.append(proxy)
                    self.proxies['http'].append(proxy)
                    self.proxies['https'].append(proxy)
            
            logger.info(f"Free-proxy-list: найдено {len(proxies)} прокси")
        except Exception as e:
            logger.error(f"Ошибка free-proxy-list: {e}")
        return proxies
    
    def parse_socks_proxy_net(self) -> List[str]:
        """Парсинг socks-proxy.net - специализированный источник SOCKS"""
        proxies = []
        try:
            url = 'https://www.socks-proxy.net/'
            response = self.session.get(url, timeout=15)
            
            rows = re.findall(r'<tr><td>(\d+\.\d+\.\d+\.\d+)</td><td>(\d+)</td><td>([^<]+)</td>', response.text)
            
            for ip, port, ptype in rows:
                proxy = f"{ip}:{port}"
                if self.is_valid_ip_port(proxy):
                    proxies.append(proxy)
                    if 'socks4' in ptype.lower():
                        self.proxies['socks4'].append(proxy)
                    elif 'socks5' in ptype.lower():
                        self.proxies['socks5'].append(proxy)
            
            logger.info(f"Socks-proxy.net: найдено {len(proxies)} SOCKS прокси")
        except Exception as e:
            logger.error(f"Ошибка socks-proxy.net: {e}")
        return proxies
    
    def parse_geonode_com(self) -> List[str]:
        """Парсинг geonode.com - современный API"""
        proxies = []
        try:
            url = 'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc'
            response = self.session.get(url, timeout=15)
            data = response.json()
            
            for proxy_data in data.get('data', []):
                ip = proxy_data.get('ip')
                port = proxy_data.get('port')
                protocols = proxy_data.get('protocols', [])
                
                if ip and port:
                    proxy = f"{ip}:{port}"
                    for protocol in protocols:
                        if protocol in self.proxies:
                            self.proxies[protocol].append(proxy)
                            proxies.append(proxy)
            
            logger.info(f"Geonode: загружено {len(proxies)} прокси")
        except Exception as e:
            logger.error(f"Ошибка Geonode: {e}")
        return proxies
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
    
    @staticmethod
    def is_valid_ip_port(proxy: str) -> bool:
        """Базовая проверка формата IP:PORT"""
        pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}$'
        if not re.match(pattern, proxy):
            return False
        
        ip, port = proxy.split(':')
        port = int(port)
        
        # Проверка октета IP
        for octet in ip.split('.'):
            if int(octet) > 255:
                return False
        
        # Проверка порта
        if port < 1 or port > 65535:
            return False
            
        return True
    
    def check_proxy(self, proxy: str, proxy_type: str = 'http') -> bool:
        """Проверка работоспособности прокси"""
        test_url = 'http://httpbin.org/ip'
        if proxy_type in ['socks4', 'socks5']:
            test_url = 'http://httpbin.org/ip'
        
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        
        try:
            response = requests.get(
                test_url, 
                proxies=proxies, 
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except:
            return False
    
    def check_all_proxies(self, max_workers=20):
        """Проверка всех собранных прокси"""
        logger.info("Начинаем проверку работоспособности прокси...")
        
        for proxy_type in self.proxies:
            working = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_proxy = {
                    executor.submit(self.check_proxy, proxy, proxy_type): proxy 
                    for proxy in self.proxies[proxy_type]
                }
                
                for future in as_completed(future_to_proxy):
                    proxy = future_to_proxy[future]
                    try:
                        if future.result():
                            working.append(proxy)
                    except Exception as e:
                        pass
            
            logger.info(f"{proxy_type}: {len(working)} рабочих из {len(self.proxies[proxy_type])}")
            self.proxies[proxy_type] = working
    
    # ==================== СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ====================
    
    def save_to_txt(self, filename_prefix: str = 'proxies'):
        """Сохранение в текстовые файлы"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for proxy_type, proxy_list in self.proxies.items():
            if proxy_list:
                filename = f"{filename_prefix}_{proxy_type}_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(proxy_list))
                logger.info(f"Сохранено {len(proxy_list)} {proxy_type} прокси в {filename}")
    
    def save_to_json(self, filename: str = 'proxies.json'):
        """Сохранение в JSON"""
        timestamp = datetime.now().isoformat()
        data = {
            'timestamp': timestamp,
            'total': sum(len(v) for v in self.proxies.values()),
            'proxies': self.proxies
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Данные сохранены в {filename}")
    
    def save_to_csv(self, filename: str = 'proxies.csv'):
        """Сохранение в CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['IP', 'Port', 'Type'])
            
            for proxy_type, proxy_list in self.proxies.items():
                for proxy in proxy_list:
                    ip, port = proxy.split(':')
                    writer.writerow([ip, port, proxy_type])
        
        logger.info(f"Данные сохранены в {filename}")
    
    # ==================== ОСНОВНОЙ ЗАПУСК ====================
    
    def run(self, check_proxies: bool = True):
        """Запуск полного цикла парсинга"""
        logger.info("=" * 60)
        logger.info("НАЧАЛО СБОРА ПРОКСИ")
        logger.info("=" * 60)
        
        # Парсинг всех источников
        parsers = [
            self.parse_github_speedx,
            self.parse_proxyscrape_api,
            self.parse_spys_one,
            self.parse_free_proxy_list_net,
            self.parse_socks_proxy_net,
            self.parse_geonode_com
        ]
        
        for parser in parsers:
            try:
                parser()
            except Exception as e:
                logger.error(f"Ошибка в {parser.__name__}: {e}")
        
        # Удаление дубликатов
        for proxy_type in self.proxies:
            self.proxies[proxy_type] = list(set(self.proxies[proxy_type]))
        
        # Подсчет статистики
        total = sum(len(v) for v in self.proxies.values())
        logger.info(f"\nВсего собрано уникальных прокси: {total}")
        for proxy_type, proxy_list in self.proxies.items():
            logger.info(f"  {proxy_type}: {len(proxy_list)}")
        
        # Проверка работоспособности
        if check_proxies:
            self.check_all_proxies()
        
        # Сохранение результатов
        self.save_to_txt()
        self.save_to_json()
        self.save_to_csv()
        
        logger.info("=" * 60)
        logger.info("РАБОТА ЗАВЕРШЕНА")
        logger.info("=" * 60)
        
        return self.proxies

# ==================== ТОЧКА ВХОДА ====================

def main():
    """Основная функция запуска"""
    parser = ProxyParser()
    
    # Параметры: 
    # check_proxies=False - отключить проверку (быстрее, но прокси могут быть мертвые)
    # check_proxies=True - включить проверку (медленнее, но только рабочие)
    proxies = parser.run(check_proxies=True)
    
    return proxies

if __name__ == "__main__":
    main()