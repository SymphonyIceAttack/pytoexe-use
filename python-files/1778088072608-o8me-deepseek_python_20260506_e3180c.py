import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
from threading import Thread
import json
import os

class JobSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск вакансий и сбор контактов")
        self.root.geometry("900x700")
        
        # Загрузка сохраненных вакансий
        self.vacancies_file = "vacancies.json"
        self.load_vacancies()
        
        # Результаты поиска
        self.search_results = []
        
        self.setup_ui()
    
    def load_vacancies(self):
        """Загрузка списка вакансий из файла"""
        default_vacancies = ["Системный администратор", "Оператор call центра"]
        
        if os.path.exists(self.vacancies_file):
            try:
                with open(self.vacancies_file, 'r', encoding='utf-8') as f:
                    self.vacancies = json.load(f)
            except:
                self.vacancies = default_vacancies
        else:
            self.vacancies = default_vacancies
            self.save_vacancies()
    
    def save_vacancies(self):
        """Сохранение списка вакансий в файл"""
        with open(self.vacancies_file, 'w', encoding='utf-8') as f:
            json.dump(self.vacancies, f, ensure_ascii=False, indent=2)
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Заголовок
        title_label = tk.Label(self.root, text="Поиск вакансий и сбор контактов", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для выбора вакансии
        vacancy_frame = ttk.LabelFrame(main_frame, text="Выбор вакансии", padding="10")
        vacancy_frame.pack(fill=tk.X, pady=5)
        
        # Выпадающий список
        ttk.Label(vacancy_frame, text="Выберите вакансию:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.vacancy_var = tk.StringVar()
        self.vacancy_combo = ttk.Combobox(vacancy_frame, textvariable=self.vacancy_var, 
                                          values=self.vacancies, width=40)
        self.vacancy_combo.grid(row=0, column=1, pady=5, padx=5)
        
        # Добавление новой вакансии
        ttk.Label(vacancy_frame, text="Или добавьте новую:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.new_vacancy_entry = ttk.Entry(vacancy_frame, width=40)
        self.new_vacancy_entry.grid(row=1, column=1, pady=5, padx=5)
        
        add_button = ttk.Button(vacancy_frame, text="Добавить вакансию", 
                                command=self.add_vacancy)
        add_button.grid(row=1, column=2, pady=5, padx=5)
        
        # Кнопка поиска
        search_button = ttk.Button(main_frame, text="🔍 НАЧАТЬ ПОИСК", 
                                   command=self.start_search, style="Accent.TButton")
        search_button.pack(pady=10)
        
        # Лог выполнения
        log_frame = ttk.LabelFrame(main_frame, text="Лог поиска", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Статус
        self.status_label = ttk.Label(main_frame, text="Готов к работе", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=5)
        
    def add_vacancy(self):
        """Добавление новой вакансии"""
        new_vacancy = self.new_vacancy_entry.get().strip()
        if new_vacancy and new_vacancy not in self.vacancies:
            self.vacancies.append(new_vacancy)
            self.save_vacancies()
            self.vacancy_combo['values'] = self.vacancies
            self.new_vacancy_entry.delete(0, tk.END)
            self.log(f"✅ Добавлена новая вакансия: {new_vacancy}")
            messagebox.showinfo("Успех", f"Вакансия '{new_vacancy}' добавлена!")
        elif new_vacancy in self.vacancies:
            messagebox.showwarning("Предупреждение", "Такая вакансия уже существует!")
        else:
            messagebox.showwarning("Предупреждение", "Введите название вакансии!")
    
    def log(self, message):
        """Запись в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_status(self, message):
        """Обновление статуса"""
        self.status_label.config(text=message)
        self.root.update()
    
    def start_search(self):
        """Запуск поиска в отдельном потоке"""
        vacancy = self.vacancy_var.get().strip()
        if not vacancy:
            messagebox.showwarning("Предупреждение", "Выберите или добавьте вакансию для поиска!")
            return
        
        self.search_results = []
        self.log_text.delete(1.0, tk.END)
        self.log(f"🚀 Начинаем поиск вакансии: {vacancy}")
        
        # Запуск в потоке
        thread = Thread(target=self.search_vacancies, args=(vacancy,))
        thread.start()
    
    def search_vacancies(self, vacancy):
        """Поиск вакансий на всех сайтах"""
        sites = [
            {"name": "trudvsem.ru", "url": "https://trudvsem.ru/vacancy/search", "search_param": "text"},
            {"name": "joblab.ru", "url": "https://joblab.ru/search/", "search_param": "search"},
            {"name": "avito.ru", "url": "https://www.avito.ru/rossiya/vacancies", "search_param": "q"},
            {"name": "job50.ru", "url": "https://job50.ru/search/", "search_param": "search"},
            {"name": "jobinmoscow.ru", "url": "https://jobinmoscow.ru/vacancies", "search_param": "search"}
        ]
        
        for site in sites:
            self.update_status(f"Поиск на {site['name']}...")
            self.log(f"🔍 Поиск на {site['name']}...")
            
            try:
                if site['name'] == "trudvsem.ru":
                    self.parse_trudvsem(site, vacancy)
                elif site['name'] == "joblab.ru":
                    self.parse_joblab(site, vacancy)
                elif site['name'] == "avito.ru":
                    self.parse_avito(site, vacancy)
                elif site['name'] == "job50.ru":
                    self.parse_job50(site, vacancy)
                elif site['name'] == "jobinmoscow.ru":
                    self.parse_jobinmoscow(site, vacancy)
                    
                time.sleep(2)  # Задержка между запросами
                
            except Exception as e:
                self.log(f"❌ Ошибка при парсинге {site['name']}: {str(e)}")
        
        self.update_status("Поиск завершен!")
        self.log(f"✅ Поиск завершен! Найдено вакансий: {len(self.search_results)}")
        
        if self.search_results:
            self.save_to_excel()
        else:
            messagebox.showinfo("Результат", "Вакансий не найдено!")
    
    def extract_email(self, text):
        """Извлечение email из текста"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return ', '.join(emails[:3]) if emails else "Не указан"
    
    def extract_phone(self, text):
        """Извлечение телефона из текста"""
        phone_patterns = [
            r'\+7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'8\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\d{3}[-\s]?\d{3}[-\s]?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        # Убираем дубликаты
        phones = list(set(phones))
        return ', '.join(phones[:3]) if phones else "Не указан"
    
    def parse_trudvsem(self, site, vacancy):
        """Парсинг trudvsem.ru"""
        try:
            params = {site['search_param']: vacancy}
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(site['url'], params=params, headers=headers, timeout=10)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            vacancies = soup.find_all('div', class_='vacancy-item')[:5]  # Ограничим 5 вакансий
            
            for item in vacancies:
                company_name = item.find('div', class_='company-name')
                company = company_name.text.strip() if company_name else "Не указано"
                
                date_elem = item.find('div', class_='date')
                date = date_elem.text.strip() if date_elem else datetime.now().strftime("%d.%m.%Y")
                
                description = item.text
                email = self.extract_email(description)
                phone = self.extract_phone(description)
                
                self.search_results.append({
                    "Название фирмы": company,
                    "Дата размещения": date,
                    "Email": email,
                    "Телефон": phone,
                    "Сайт": site['name']
                })
                
            self.log(f"✅ На {site['name']} найдено {len(vacancies)} вакансий")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка при парсинге {site['name']}: {str(e)}")
    
    def parse_joblab(self, site, vacancy):
        """Парсинг joblab.ru"""
        try:
            params = {site['search_param']: vacancy}
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site['url'], params=params, headers=headers, timeout=10)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            vacancies = soup.find_all('div', class_='vacancy')[:5]
            
            for item in vacancies:
                company = item.find('div', class_='employer')
                company_name = company.text.strip() if company else "Не указано"
                
                date_elem = item.find('div', class_='date')
                date = date_elem.text.strip() if date_elem else "Не указана"
                
                text_content = item.text
                email = self.extract_email(text_content)
                phone = self.extract_phone(text_content)
                
                self.search_results.append({
                    "Название фирмы": company_name,
                    "Дата размещения": date,
                    "Email": email,
                    "Телефон": phone,
                    "Сайт": site['name']
                })
                
            self.log(f"✅ На {site['name']} найдено {len(vacancies)} вакансий")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка на {site['name']}: {str(e)}")
    
    def parse_avito(self, site, vacancy):
        """Парсинг avito.ru"""
        try:
            params = {site['search_param']: vacancy}
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site['url'], params=params, headers=headers, timeout=10)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', {'data-marker': 'item'})[:5]
            
            for item in items:
                company = item.find('div', class_='company')
                company_name = company.text.strip() if company else "Не указано"
                
                text_content = item.text
                email = self.extract_email(text_content)
                phone = self.extract_phone(text_content)
                
                self.search_results.append({
                    "Название фирмы": company_name,
                    "Дата размещения": datetime.now().strftime("%d.%m.%Y"),
                    "Email": email,
                    "Телефон": phone,
                    "Сайт": site['name']
                })
                
            self.log(f"✅ На {site['name']} найдено {len(items)} вакансий")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка на {site['name']}: {str(e)}")
    
    def parse_job50(self, site, vacancy):
        """Парсинг job50.ru"""
        try:
            params = {site['search_param']: vacancy}
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site['url'], params=params, headers=headers, timeout=10)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            vacancies = soup.find_all('div', class_='job-item')[:5]
            
            for item in vacancies:
                company = item.find('div', class_='company')
                company_name = company.text.strip() if company else "Не указано"
                
                text_content = item.text
                email = self.extract_email(text_content)
                phone = self.extract_phone(text_content)
                
                self.search_results.append({
                    "Название фирмы": company_name,
                    "Дата размещения": datetime.now().strftime("%d.%m.%Y"),
                    "Email": email,
                    "Телефон": phone,
                    "Сайт": site['name']
                })
                
            self.log(f"✅ На {site['name']} найдено {len(vacancies)} вакансий")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка на {site['name']}: {str(e)}")
    
    def parse_jobinmoscow(self, site, vacancy):
        """Парсинг jobinmoscow.ru"""
        try:
            params = {site['search_param']: vacancy}
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site['url'], params=params, headers=headers, timeout=10)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            vacancies = soup.find_all('div', class_='vacancy-card')[:5]
            
            for item in vacancies:
                company = item.find('div', class_='company-name')
                company_name = company.text.strip() if company else "Не указано"
                
                date_elem = item.find('div', class_='date')
                date = date_elem.text.strip() if date_elem else "Не указана"
                
                text_content = item.text
                email = self.extract_email(text_content)
                phone = self.extract_phone(text_content)
                
                self.search_results.append({
                    "Название фирмы": company_name,
                    "Дата размещения": date,
                    "Email": email,
                    "Телефон": phone,
                    "Сайт": site['name']
                })
                
            self.log(f"✅ На {site['name']} найдено {len(vacancies)} вакансий")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка на {site['name']}: {str(e)}")
    
    def save_to_excel(self):
        """Сохранение результатов в Excel"""
        try:
            filename = f"vacancies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(self.search_results)
            
            # Сохраняем в Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Вакансии', index=False)
                
                # Настройка ширины колонок
                worksheet = writer.sheets['Вакансии']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.log(f"📊 Результаты сохранены в файл: {filename}")
            messagebox.showinfo("Успех", f"Результаты сохранены в файл:\n{filename}")
            
        except Exception as e:
            self.log(f"❌ Ошибка при сохранении в Excel: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

# Установка необходимых библиотек
def install_requirements():
    """Установка необходимых пакетов"""
    required_packages = [
        'requests', 'beautifulsoup4', 'pandas', 'openpyxl', 'lxml'
    ]
    
    import subprocess
    import sys
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Устанавливаем {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    # Установка зависимостей
    print("Проверка и установка необходимых библиотек...")
    install_requirements()
    
    # Запуск приложения
    root = tk.Tk()
    app = JobSearchApp(root)
    root.mainloop()