#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Sorter v1.2.6
Программа для сортировки, фильтрации и анализа доменных имен
Автор: MashaGPT Project Team
Версия: 1.2.6
Дата: 2024
"""

import re
import sys
import argparse
from collections import Counter
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional
import socket
import tldextract
import ipaddress

class DomainSorter:
    """Основной класс для работы с доменными именами"""
    
    def __init__(self):
        self.domains = []
        self.stats = {
            'total': 0,
            'unique': 0,
            'by_tld': {},
            'by_length': {},
            'invalid': 0
        }
        
    def load_domains(self, input_file: str) -> None:
        """Загрузка доменов из файла"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                domain = line.strip()
                if domain and not domain.startswith('#'):
                    self.domains.append(domain)
                    
            self.stats['total'] = len(self.domains)
            self._update_stats()
            
        except FileNotFoundError:
            print(f"Ошибка: Файл '{input_file}' не найден")
            sys.exit(1)
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            sys.exit(1)
    
    def load_from_text(self, text: str) -> None:
        """Загрузка доменов из текста"""
        lines = text.strip().split('\n')
        for line in lines:
            domain = line.strip()
            if domain and not domain.startswith('#'):
                self.domains.append(domain)
        
        self.stats['total'] = len(self.domains)
        self._update_stats()
    
    def _update_stats(self) -> None:
        """Обновление статистики"""
        unique_domains = set(self.domains)
        self.stats['unique'] = len(unique_domains)
        
        # Статистика по TLD
        self.stats['by_tld'] = {}
        for domain in self.domains:
            ext = tldextract.extract(domain)
            tld = ext.suffix
            if tld:
                self.stats['by_tld'][tld] = self.stats['by_tld'].get(tld, 0) + 1
        
        # Статистика по длине
        self.stats['by_length'] = {}
        for domain in self.domains:
            length = len(domain)
            self.stats['by_length'][length] = self.stats['by_length'].get(length, 0) + 1
        
        # Подсчет невалидных доменов
        self.stats['invalid'] = sum(1 for d in self.domains if not self._is_valid_domain(d))
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Проверка валидности доменного имени"""
        if not domain or len(domain) > 253:
            return False
        
        # Проверка формата
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain))
    
    def sort_alphabetically(self, reverse: bool = False) -> List[str]:
        """Сортировка по алфавиту"""
        return sorted(self.domains, reverse=reverse)
    
    def sort_by_tld(self, reverse: bool = False) -> List[str]:
        """Сортировка по TLD"""
        return sorted(self.domains, 
                     key=lambda x: tldextract.extract(x).suffix, 
                     reverse=reverse)
    
    def sort_by_length(self, reverse: bool = False) -> List[str]:
        """Сортировка по длине"""
        return sorted(self.domains, key=len, reverse=reverse)
    
    def filter_by_tld(self, tld_list: List[str]) -> List[str]:
        """Фильтрация по TLD"""
        result = []
        for domain in self.domains:
            ext = tldextract.extract(domain)
            if ext.suffix in tld_list:
                result.append(domain)
        return result
    
    def filter_by_keyword(self, keyword: str, case_sensitive: bool = False) -> List[str]:
        """Фильтрация по ключевому слову"""
        result = []
        for domain in self.domains:
            if case_sensitive:
                if keyword in domain:
                    result.append(domain)
            else:
                if keyword.lower() in domain.lower():
                    result.append(domain)
        return result
    
    def filter_by_length(self, min_len: int = 0, max_len: int = 253) -> List[str]:
        """Фильтрация по длине"""
        return [d for d in self.domains if min_len <= len(d) <= max_len]
    
    def remove_duplicates(self) -> List[str]:
        """Удаление дубликатов"""
        seen = set()
        result = []
        for domain in self.domains:
            if domain not in seen:
                seen.add(domain)
                result.append(domain)
        return result
    
    def extract_subdomains(self) -> Dict[str, List[str]]:
        """Извлечение поддоменов"""
        subdomains = {}
        for domain in self.domains:
            ext = tldextract.extract(domain)
            if ext.subdomain:
                main_domain = f"{ext.domain}.{ext.suffix}"
                if main_domain not in subdomains:
                    subdomains[main_domain] = []
                subdomains[main_domain].append(ext.subdomain)
        return subdomains
    
    def group_by_tld(self) -> Dict[str, List[str]]:
        """Группировка по TLD"""
        groups = {}
        for domain in self.domains:
            ext = tldextract.extract(domain)
            tld = ext.suffix
            if tld not in groups:
                groups[tld] = []
            groups[tld].append(domain)
        return groups
    
    def get_statistics(self) -> Dict:
        """Получение статистики"""
        return {
            'total_domains': self.stats['total'],
            'unique_domains': self.stats['unique'],
            'duplicates': self.stats['total'] - self.stats['unique'],
            'invalid_domains': self.stats['invalid'],
            'top_tlds': sorted(self.stats['by_tld'].items(), key=lambda x: x[1], reverse=True)[:10],
            'average_length': sum(len(d) for d in self.domains) / max(1, len(self.domains)),
            'min_length': min(len(d) for d in self.domains) if self.domains else 0,
            'max_length': max(len(d)