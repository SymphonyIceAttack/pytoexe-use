# ДОБАВЬТЕ ЭТО В САМОЕ НАЧАЛО ФАЙЛА (перед всеми импортами)
import sys
import os
import requests
import json
import time
import logging
import base64
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import threading
import hashlib
import ssl
import configparser

# Проверяем requests_toolbelt
try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder

    REQUESTS_TOOLBELT_AVAILABLE = True
except ImportError:
    REQUESTS_TOOLBELT_AVAILABLE = False


    # Создаем заглушку для MultipartEncoder
    class MultipartEncoder:
        def __init__(self, fields):
            self.fields = fields
            self.content_type = 'multipart/form-data'
            self.boundary_value = 'boundary'

        def to_string(self):
            return str(self.fields)

        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except:
            pass

        # Настройка сессии requests для игнорирования SSL
        import warnings
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        #
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Класс для загрузки конфигурационных файлов"""

    @staticmethod
    def get_env_files() -> List[str]:
        """Получить список всех .env файлов в директории"""
        env_files = []
        try:
            for file in os.listdir('.'):
                if file.endswith('.env'):
                    env_files.append(file)
            return sorted(env_files)
        except Exception as e:
            logger.error(f"Ошибка поиска .env файлов: {e}")
            return []

    @staticmethod
    def load_credentials_from_env(env_file: str) -> Dict[str, str]:
        """Загрузка учетных данных из .env файла"""
        credentials = {}
        try:
            # Используем configparser для чтения .env файла
            config = configparser.ConfigParser()

            # Читаем как обычный текстовый файл
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        credentials[key.strip()] = value.strip()

            # Проверяем наличие обязательных полей
            required_fields = ['CLIENT_ID', 'CLIENT_SECRET', 'USERNAME',
                               'PASSWORD', 'TOKEN_URL', 'BASE_URL']
            missing_fields = [field for field in required_fields
                              if field not in credentials]

            if missing_fields:
                logger.error(f"В файле {env_file} отсутствуют поля: {', '.join(missing_fields)}")
                raise ValueError(f"Отсутствуют обязательные поля: {', '.join(missing_fields)}")

            logger.info(f"Успешно загружено {len(credentials)} параметров из {env_file}")
            return credentials

        except FileNotFoundError:
            logger.error(f"Файл {env_file} не найден")
            raise
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {env_file}: {e}")
            raise

    @staticmethod
    def load_mac_addresses(file_path: str) -> List[str]:
        """Загрузка MAC-адресов (devEui) из файла"""
        addresses = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    addr = line.strip()
                    if addr and not addr.startswith('#'):
                        addresses.append(addr)
            return addresses
        except FileNotFoundError:
            logger.error(f"Файл {file_path} не найден")
            raise
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {e}")
            raise


class LarTechAPI:
    """Класс для работы с REST API Lartech с OAuth аутентификацией"""

    def __init__(self, credentials: Dict[str, str]):
        """
        Инициализация API клиента

        Args:
            credentials: Словарь с учетными данными из .env файла
        """
        self.credentials = credentials

        # ВАЖНО: Извлекаем URL из credentials
        self.token_url = credentials.get('TOKEN_URL', 'https://auth.lar.tech:443/oauth/token')
        self.base_url = credentials.get('BASE_URL', 'https://rest-api.lar.tech:9001/info_api/v1')

        # Очищаем URL от возможных завершающих слэшей
        self.base_url = self.base_url.rstrip('/')

        self.session = requests.Session()
        self.access_token = None
        self.token_expires_at = 0

        # Настраиваем сессию для игнорирования SSL ошибок
        self.session.verify = False

        # Логируем используемые URL для отладки
        logger.info(f"Инициализирован API клиент с:")
        logger.info(f"  Token URL: {self.token_url}")
        logger.info(f"  Base URL: {self.base_url}")

    def _normalize_urls(self):
        """Нормализация URL для совместимости"""
        # Если token_url не указан, но есть base_url, попробуем вывести его
        if not self.token_url and self.base_url:
            # Пробуем угадать token_url на основе base_url
            if 'rest-api.lar.tech' in self.base_url:
                self.token_url = 'https://auth.lar.tech:443/oauth/token'
            elif 'test-' in self.base_url or 'staging' in self.base_url:
                # Для тестовых окружений
                self.token_url = self.base_url.replace('rest-api', 'auth').replace('/v1', '/oauth/token')

            logger.info(f"Предполагаемый Token URL: {self.token_url}")

    def authenticate(self) -> bool:
        """
        Получение OAuth токена через grant_type=password

        Returns:
            True если аутентификация успешна
        """

        try:
            # Формируем данные для OAuth запроса
            auth_data = {
                'grant_type': 'password',
                'username': self.credentials['USERNAME'],
                'password': self.credentials['PASSWORD'],
                'client_id': self.credentials['CLIENT_ID'],
                'client_secret': self.credentials['CLIENT_SECRET']
            }

            # Добавляем Basic Auth заголовок (client_id:client_secret)
            client_auth = base64.b64encode(
                f"{self.credentials['CLIENT_ID']}:{self.credentials['CLIENT_SECRET']}".encode()
            ).decode()

            headers = {
                'Authorization': f'Basic {client_auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            logger.info(f"Отправка запроса на аутентификацию: {self.token_url}")

            response = self.session.post(
                self.token_url,
                data=auth_data,
                headers=headers,
                timeout=30
            )

            logger.debug(f"Auth response status: {response.status_code}")

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')

                if self.access_token:
                    # Устанавливаем токен в заголовки сессии
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    })

                    # Рассчитываем время истечения токена
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = time.time() + expires_in

                    logger.info(f"Успешная аутентификация. Токен получен.")
                    logger.debug(f"Token type: {token_data.get('token_type')}")
                    logger.debug(f"Expires in: {expires_in} сек")

                    return True
                else:
                    logger.error("Токен не найден в ответе")
                    return False
            else:
                logger.error(f"Ошибка аутентификации: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка подключения при аутентификации: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при аутентификации: {e}")
            return False

    def ensure_auth(self) -> bool:
        """Проверка и обновление токена если нужно"""
        if not self.access_token or time.time() > self.token_expires_at - 300:  # 5 минут до истечения
            logger.info("Токен истек или отсутствует, запрашиваем новый...")
            return self.authenticate()
        return True

    def _try_alternative_auth(self) -> bool:
        """Попробовать альтернативные методы аутентификации"""
        try:
            logger.info("Пробуем альтернативный метод аутентификации...")

            # Вариант для Lartech API: grant_type=client_credentials может быть нужен
            auth_data = {
                'grant_type': 'client_credentials',  # Попробуем этот grant_type
                'client_id': self.credentials['CLIENT_ID'],
                'client_secret': self.credentials['CLIENT_SECRET']
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = self.session.post(
                self.token_url,
                data=auth_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')

                if self.access_token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    })

                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = time.time() + expires_in

                    logger.info("Аутентификация через client_credentials успешна")
                    return True

            # Если не сработало, возвращаемся к grant_type=password
            logger.warning("client_credentials не сработал, возвращаемся к password")
            return False

        except Exception as e:
            logger.error(f"Ошибка в альтернативной аутентификации: {e}")
            return False

    def send_otap_update(self, dev_eui: str, firmware_path: str, lora_class: str = "C") -> Tuple[bool, str]:
        """
        Отправка OTAP обновления на устройство через multipart/form-data
        """
        try:
            # Проверяем аутентификацию
            if not self.ensure_auth():
                return False, "Ошибка аутентификации"

            # Проверяем файл прошивки
            if not Path(firmware_path).exists():
                return False, f"Файл прошивки не найден: {firmware_path}"

            file_path = Path(firmware_path)
            file_name = file_path.name

            # Читаем файл прошивки
            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()

            file_size = len(firmware_data)
            logger.info(f"Файл прошивки: {file_name} ({file_size} байт)")

            # Формируем URL
            if '/info_api/v1' in self.base_url:
                base_for_otap = self.base_url
            else:
                base_for_otap = f"{self.base_url}/info_api/v1"

            dev_eui_encoded = dev_eui.replace(':', '%3A')
            otap_url = f"{base_for_otap}/devices/{dev_eui_encoded}/otapv2"

            logger.info(f"Отправка OTAP на {dev_eui}")
            logger.info(f"OTAP URL: {otap_url}")

            # ВАЖНО: Используем нативный multipart если нет requests_toolbelt
            if REQUESTS_TOOLBELT_AVAILABLE:
                # Используем requests_toolbelt если доступен
                multipart_data = MultipartEncoder(
                    fields={
                        'loraClass': lora_class,
                        'rawImage': (file_name, firmware_data, 'application/octet-stream')
                    }
                )

                auth_header = self.session.headers.get('Authorization', '')
                headers = {
                    'Content-Type': multipart_data.content_type,
                    'Accept': 'application/json',
                    'Authorization': auth_header
                }

                logger.info("Используем requests_toolbelt для multipart")
                response = self.session.post(
                    otap_url,
                    data=multipart_data,
                    headers=headers,
                    timeout=120
                )
            else:
                # Нативный способ через files параметр
                logger.info("Используем нативный multipart (без requests_toolbelt)")
                files = {
                    'loraClass': (None, lora_class),
                    'rawImage': (file_name, firmware_data, 'application/octet-stream')
                }

                response = self.session.post(
                    otap_url,
                    files=files,
                    timeout=120
                )

            logger.info(f"HTTP статус: {response.status_code}")
            logger.debug(f"Заголовки ответа: {dict(response.headers)}")

            # Обработка ответов
            if response.status_code == 200:
                if response.content:
                    try:
                        result = response.json()
                        logger.info(f"Успешно! Ответ: {result}")
                    except:
                        logger.info(f"Успешно! Текст ответа: {response.text[:200]}")
                else:
                    logger.info("Успешно! (пустой ответ)")
                return True, "OTAP обновление успешно отправлено"

            elif response.status_code == 201:
                logger.info(f"Запрос создан (201): {response.text[:200]}")
                return True, "Запрос создан"

            elif response.status_code == 202:
                logger.info(f"Запрос принят в обработку (202): {response.text[:200]}")
                return True, "Запрос принят в обработку"

            elif response.status_code == 400:
                error_text = response.text[:500] if response.text else "Bad Request"
                logger.error(f"Ошибка 400 (Bad Request)")
                logger.error(f"Тело ответа: {error_text}")

                # Попробуем альтернативный формат данных
                return self._try_alternative_multipart(dev_eui, dev_eui_encoded, firmware_path, lora_class, auth_header)

            elif response.status_code == 401:
                logger.error(f"Ошибка 401 - Unauthorized")
                logger.error(f"Токен: {auth_header[:50]}...")

                # Пробуем обновить токен
                if self.authenticate():
                    auth_header = self.session.headers.get('Authorization', '')
                    headers['Authorization'] = auth_header

                    response = self.session.post(
                        otap_url,
                        data=multipart_data,
                        headers=headers,
                        timeout=120
                    )

                    if response.status_code == 200:
                        return True, "Успешно после повторной аутентификации"

                return False, "Ошибка аутентификации (401)"

            elif response.status_code == 404:
                logger.error(f"Endpoint не найден (404)")
                logger.error(f"URL: {otap_url}")

                # Пробуем без кодирования двоеточий
                otap_url_alt = f"https://rest-api.lar.tech:9001/info_api/v1/devices/{dev_eui}/otapv2"
                logger.info(f"Пробуем без кодирования: {otap_url_alt}")

                response = self.session.post(
                    otap_url_alt,
                    data=multipart_data,
                    headers=headers,
                    timeout=120
                )

                if response.status_code == 200:
                    logger.info("Успешно без кодирования devEui")
                    return True, "Успешно отправлено"

                return False, f"Endpoint не найден (пробовали оба варианта)"

            elif response.status_code == 500:
                error_text = response.text[:500] if response.text else "Internal Server Error"
                logger.error(f"Внутренняя ошибка сервера (500)")
                logger.error(f"Тело ответа: {error_text}")

                # Детальная диагностика
                if 'errorCode' in error_text and '-1' in error_text:
                    logger.error("Ошибка -1: Проверьте данные запроса")
                    logger.error(f"devEui: {dev_eui}")
                    logger.error(f"Файл: {file_name} ({file_size} байт)")
                    logger.error(f"LoRa class: {lora_class}")
                    logger.error(f"Content-Type заголовок: {headers['Content-Type']}")

                # Попробуем другой формат multipart
                return self._try_alternative_multipart(dev_eui, dev_eui_encoded, firmware_path, lora_class, auth_header)

            else:
                error_text = response.text[:500] if response.text else "No response"
                logger.error(f"Неизвестная ошибка: {response.status_code}")
                logger.error(f"Тело ответа: {error_text}")
                return False, f"Ошибка API: {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"Таймаут запроса")
            return False, "Таймаут"
        except requests.exceptions.ConnectionError:
            logger.error(f"Ошибка соединения")
            return False, "Ошибка соединения"
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, f"Ошибка: {str(e)}"

    def _try_alternative_multipart(self, dev_eui: str, dev_eui_encoded: str, firmware_path: str,
                                   lora_class: str, auth_header: str) -> Tuple[bool, str]:
        """Попробовать альтернативные форматы multipart данных"""
        try:
            otap_url = f"https://rest-api.lar.tech:9001/info_api/v1/devices/{dev_eui_encoded}/otapv2"
            file_path = Path(firmware_path)
            file_name = file_path.name

            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()

            logger.info("Пробуем альтернативные форматы multipart...")

            # Вариант 1: loraClass как часть fields, но без content-type для файла
            multipart_data1 = MultipartEncoder(
                fields={
                    'loraClass': lora_class,
                    'rawImage': (file_name, firmware_data)  # Без content-type
                }
            )

            headers = {
                'Content-Type': multipart_data1.content_type,
                'Accept': 'application/json',
                'Authorization': auth_header
            }

            logger.info("Пробуем вариант 1: rawImage без content-type")
            response = self.session.post(otap_url, data=multipart_data1, headers=headers, timeout=60)

            if response.status_code == 200:
                logger.info("Успешно с вариантом 1")
                return True, "Успешно (вариант 1)"

            # Вариант 2: Используем files параметр requests (старый метод)
            logger.info("Пробуем вариант 2: через files параметр requests")
            files = {
                'loraClass': (None, lora_class),
                'rawImage': (file_name, firmware_data, 'application/octet-stream')
            }

            response = self.session.post(
                otap_url,
                files=files,
                headers={'Accept': 'application/json', 'Authorization': auth_header},
                timeout=60
            )

            if response.status_code == 200:
                logger.info("Успешно с вариантом 2")
                return True, "Успешно (вариант 2)"

            # Вариант 3: Только файл, loraClass как параметр
            logger.info("Пробуем вариант 3: loraClass как data параметр")
            data = {'loraClass': lora_class}
            files = {'rawImage': (file_name, firmware_data, 'application/octet-stream')}

            response = self.session.post(
                otap_url,
                data=data,
                files=files,
                headers={'Accept': 'application/json', 'Authorization': auth_header},
                timeout=60
            )

            if response.status_code == 200:
                logger.info("Успешно с вариантом 3")
                return True, "Успешно (вариант 3)"

            logger.error("Все альтернативные форматы не сработали")
            return False, "Все форматы multipart не сработали"

        except Exception as e:
            logger.error(f"Ошибка в альтернативных форматах: {e}")
            return False, f"Ошибка альтернативных форматов: {e}"

    def test_connection(self) -> Tuple[bool, str]:
        """Тестирование соединения с API"""
        try:
            # Пробуем получить информацию о пользователе или другие публичные данные
            test_url = f"{self.base_url}/user/me"

            if not self.ensure_auth():
                return False, "Ошибка аутентификации"

            response = self.session.get(test_url, timeout=10)

            if response.status_code == 200:
                return True, "Соединение успешно"
            else:
                return False, f"Ошибка: {response.status_code}"

        except Exception as e:
            return False, f"Ошибка соединения: {e}"

    def logout(self):
        """Завершение сессии"""
        try:
            # Для OAuth можно отозвать токен
            if self.access_token:
                revoke_url = self.token_url.replace('/token', '/revoke')
                revoke_data = {
                    'token': self.access_token,
                    'client_id': self.credentials['CLIENT_ID'],
                    'client_secret': self.credentials['CLIENT_SECRET']
                }
                self.session.post(revoke_url, data=revoke_data, timeout=5)
        except:
            pass
        finally:
            self.session.close()
            logger.info("Сессия API завершена")

class OTAPUpdaterGUI:
    """Графический интерфейс утилиты OTAP обновления"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lartech Updater")

        # Инициализация переменных
        self.api_client = None
        self.credentials = None
        self.current_env_file = None

        # Переменные для элементов управления
        self.firmware_path_var = tk.StringVar()
        self.delay_var = tk.StringVar(value="10")
        self.lora_class_var = tk.StringVar(value="C")

        # Переменные для отслеживания размера
        self.last_width = 0
        self.last_height = 0

        self.setup_ui()

    def setup_ui(self):
        """Настройка полностью адаптивного пользовательского интерфейса"""
        # Стили
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Red.TLabel', foreground='red')
        style.configure('Green.TLabel', foreground='green')

        # Устанавливаем начальный размер и разрешаем изменение
        self.root.minsize(800, 600)  # Минимальный размер
        self.root.geometry("900x800")  # Стартовый размер

        # Включаем изменение размера окна
        self.root.resizable(True, True)

        # Основной контейнер с весами для всех направлений
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настраиваем веса для главного окна и фрейма
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Настраиваем сетку main_frame (5 строк, 1 колонка с весом)
        for i in range(8):  # 0-7 строки
            main_frame.grid_rowconfigure(i, weight=0)
        main_frame.grid_rowconfigure(4, weight=1)  # Строка с устройствами - расширяемая
        main_frame.grid_rowconfigure(6, weight=1)  # Строка с логами - расширяемая
        main_frame.grid_columnconfigure(0, weight=1)


        # Секция: Статус подключения (компактная)
        status_frame = ttk.LabelFrame(main_frame, text="Статус подключения", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.grid_columnconfigure(1, weight=1)

        self.status_label = ttk.Label(status_frame, text="Не подключено", style='Red.TLabel')
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        ttk.Button(status_frame, text="Проверить подключение",
                   command=self.test_connection).grid(row=0, column=1, padx=(20, 10), sticky=tk.W)

        ttk.Button(status_frame, text="Сменить конфиг",
                   command=self.change_config).grid(row=0, column=2, padx=(10, 0), sticky=tk.E)

        # Секция: Выбор файла прошивки
        firmware_frame = ttk.LabelFrame(main_frame, text="Файл прошивки (.lz1x)", padding="10")
        firmware_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        firmware_frame.grid_columnconfigure(0, weight=1)

        # Поле ввода пути к файлу с кнопкой обзора
        input_frame = ttk.Frame(firmware_frame)
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)

        self.firmware_entry = ttk.Entry(input_frame, textvariable=self.firmware_path_var)
        self.firmware_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Button(input_frame, text="Обзор...",
                   command=self.browse_firmware, width=10).grid(row=0, column=1, sticky=tk.E)

        self.firmware_info_label = ttk.Label(firmware_frame, text="Файл не выбран", foreground="gray")
        self.firmware_info_label.grid(row=1, column=0, sticky=tk.W)

        # Секция: Параметры обновления (компактная, в одну строку)
        settings_frame = ttk.LabelFrame(main_frame, text="Параметры обновления", padding="10")
        settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Используем grid с пропорциональным распределением
        settings_frame.grid_columnconfigure(1, weight=1)
        settings_frame.grid_columnconfigure(3, weight=1)

        ttk.Label(settings_frame, text="Задержка (сек):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.delay_spinbox = ttk.Spinbox(settings_frame, from_=1, to=30,
                                         textvariable=self.delay_var, width=8)
        self.delay_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(settings_frame, text="Класс LoRa:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))

        self.lora_class_combo = ttk.Combobox(settings_frame, textvariable=self.lora_class_var,
                                             values=["A", "B", "C"], width=5, state="readonly")
        self.lora_class_combo.grid(row=0, column=3, sticky=tk.W)

        # Секция: Список устройств (РАСШИРЯЕМАЯ)
        devices_frame = ttk.LabelFrame(main_frame, text="Устройства для обновления", padding="10")
        devices_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Настраиваем расширяемость внутри фрейма устройств
        devices_frame.grid_rowconfigure(0, weight=1)  # Список расширяется
        devices_frame.grid_columnconfigure(0, weight=1)

        # Прокручиваемый список устройств
        list_container = ttk.Frame(devices_frame)
        list_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_container.grid_rowconfigure(0, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        self.devices_listbox = tk.Listbox(list_container, selectmode=tk.EXTENDED)
        self.devices_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        list_scrollbar = ttk.Scrollbar(list_container, command=self.devices_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.devices_listbox.config(yscrollcommand=list_scrollbar.set)

        # Кнопка для устройств (под списком)
        ttk.Button(devices_frame, text="Загрузить устройства из файла",
                   command=self.load_devices_file, width=25).grid(row=1, column=0, pady=(10, 0))

        # Секция: Прогресс выполнения
        progress_frame = ttk.LabelFrame(main_frame, text="Прогресс выполнения", padding="10")
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.progress_label = ttk.Label(progress_frame, text="Готово к работе")
        self.progress_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # Секция: Логи (РАСШИРЯЕМАЯ)
        log_frame = ttk.LabelFrame(main_frame, text="Логи выполнения", padding="10")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Настраиваем расширяемость логов
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Текстовое поле для логов с прокруткой
        text_frame = ttk.Frame(log_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED, height=6)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        log_scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Секция: Кнопки управления (фиксированная высота)
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=7, column=0, pady=(10, 0), sticky=(tk.W, tk.E))

        # Распределяем кнопки равномерно
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=1)

        self.start_button = ttk.Button(buttons_frame, text="Запустить обновление",
                                       command=self.start_update, state=tk.DISABLED,
                                       width=20)
        self.start_button.grid(row=0, column=0, sticky=tk.W)

        ttk.Button(buttons_frame, text="Показать логи",
                   command=self.show_logs, width=15).grid(row=0, column=1, padx=10)

        ttk.Button(buttons_frame, text="Выход",
                   command=self.root.quit, width=10).grid(row=0, column=2, sticky=tk.E)

        # Привязываем обработчик изменения размера окна
        self.root.bind('<Configure>', self.on_window_resize)

        # Применяем начальные настройки
        self.root.update_idletasks()
        self.adjust_ui_elements()

    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        if event.widget == self.root:
            # Небольшая задержка для стабилизации размера
            self.root.after(100, self.adjust_ui_elements)

    def adjust_ui_elements(self):
        """Адаптивная настройка элементов интерфейса"""
        try:
            # Получаем текущую ширину окна
            window_width = self.root.winfo_width()

            # Адаптируем ширину элементов ввода
            if window_width < 850:
                # Для маленьких окон уменьшаем ширину полей ввода
                self.firmware_entry.config(width=40)
            elif window_width < 1000:
                self.firmware_entry.config(width=50)
            else:
                self.firmware_entry.config(width=60)

            # Адаптируем количество видимых строк в списке устройств
            listbox_height = max(5, min(15, (self.root.winfo_height() - 400) // 25))
            self.devices_listbox.config(height=listbox_height)

            # Адаптируем высоту поля логов
            log_height = max(4, min(10, (self.root.winfo_height() - 500) // 20))
            self.log_text.config(height=log_height)

            # Обновляем прогресс-бар
            self.progress_bar.config(length=window_width - 200)

            # Принудительное обновление геометрии
            self.root.update_idletasks()

        except Exception as e:
            # Игнорируем ошибки при начальной настройке
            pass

    def load_credentials(self):
        """Загрузка учетных данных при запуске"""
        try:
            # Получаем список .env файлов
            env_files = ConfigLoader.get_env_files()

            if not env_files:
                self.log_message("Не найдены .env файлы в текущей директории", "error")
                messagebox.showerror(
                    "Ошибка",
                    "В текущей директории не найдены .env файлы.\n\n"
                    "Создайте файл с расширением .env содержащий:\n"
                    "CLIENT_ID=ваш_client_id\n"
                    "CLIENT_SECRET=ваш_client_secret\n"
                    "USERNAME=ваш_логин\n"
                    "PASSWORD=ваш_пароль\n"
                    "TOKEN_URL=https://auth.lar.tech:443/oauth/token\n"
                    "BASE_URL=https://rest-api.lar.tech:9001/info_api/v1/devices"
                )
                return

            # Показываем диалог выбора .env файла
            self.select_env_file(env_files)

        except Exception as e:
            self.log_message(f"Ошибка загрузки credentials: {str(e)}", "error")

    def select_env_file(self, env_files):
        """Показать диалог выбора .env файла"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор конфигурации")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Выберите .env файл для загрузки:",
                  style='Subtitle.TLabel').pack(pady=(20, 10))

        # Список файлов
        listbox = tk.Listbox(dialog, height=10, width=50)
        listbox.pack(pady=10, padx=20)

        for env_file in env_files:
            listbox.insert(tk.END, env_file)

        # Выбрать первый файл по умолчанию
        if env_files:
            listbox.selection_set(0)

        def load_selected():
            selection = listbox.curselection()
            if selection:
                selected_file = env_files[selection[0]]
                try:
                    # Загружаем credentials
                    self.credentials = ConfigLoader.load_credentials_from_env(selected_file)
                    self.current_env_file = selected_file

                    # Подключаемся к API
                    self.connect_to_api()

                    dialog.destroy()

                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить {selected_file}: {str(e)}")
            else:
                messagebox.showwarning("Внимание", "Выберите файл из списка")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Загрузить",
                   command=load_selected).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Отмена",
                   command=self.root.quit).pack(side=tk.LEFT, padx=10)

        listbox.bind('<Double-Button-1>', lambda e: load_selected())
        listbox.focus_set()

    def connect_to_api(self):
        """Подключение к API с использованием загруженных credentials"""
        try:
            if not self.credentials:
                self.log_message("Не загружены учетные данные", "error")
                return

            self.api_client = LarTechAPI(self.credentials)

            if self.api_client.authenticate():
                self.status_label.config(
                    text=f"Подключено ({self.current_env_file})",
                    style='Green.TLabel'
                )
                self.log_message(f"Успешное подключение с {self.current_env_file}", "info")
                self.check_start_conditions()
            else:
                self.status_label.config(text="Ошибка аутентификации", style='Red.TLabel')
                self.log_message("Ошибка аутентификации", "error")

        except Exception as e:
            self.status_label.config(text="Ошибка подключения", style='Red.TLabel')
            self.log_message(f"Ошибка подключения: {str(e)}", "error")

    def change_config(self):
        """Смена конфигурационного файла"""
        env_files = ConfigLoader.get_env_files()

        if not env_files:
            messagebox.showinfo("Информация", "Нет доступных .env файлов")
            return

        self.select_env_file(env_files)

    def test_connection(self):
        """Тестирование соединения с API"""
        if not self.api_client:
            messagebox.showerror("Ошибка", "API клиент не инициализирован")
            return

        success, message = self.api_client.test_connection()

        if success:
            messagebox.showinfo("Успех", "Соединение с API установлено успешно")
            self.log_message("Тест подключения: успешно", "info")
        else:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {message}")
            self.log_message(f"Тест подключения: {message}", "error")

    def browse_firmware(self):
        """Открыть диалог выбора файла прошивки ТОЛЬКО с расширением .lz1x"""
        filetypes = [
            ("Файлы прошивки LZ1X", "*.lz1x"),
            ("Все файлы", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="Выберите файл прошивки (.lz1x)",
            filetypes=filetypes
        )

        if filename:
            self.firmware_path_var.set(filename)
            file_path = Path(filename)

            try:
                file_size = file_path.stat().st_size
                self.firmware_info_label.config(
                    text=f"{file_path.name} ({file_size:,} байт)",
                    foreground="black"
                )
                self.log_message(f"Выбран файл прошивки: {file_path.name}", "info")
                self.check_start_conditions()
            except Exception as e:
                self.log_message(f"Ошибка чтения файла: {str(e)}", "error")

    def load_devices_file(self):
        """Загрузить список устройств из файла"""
        filename = filedialog.askopenfilename(
            title="Выберите файл со списком устройств",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )

        if filename:
            try:
                devices = ConfigLoader.load_mac_addresses(filename)

                if devices:
                    # Очищаем и добавляем новые устройства
                    self.devices_listbox.delete(0, tk.END)
                    for device in devices:
                        self.devices_listbox.insert(tk.END, device)

                    self.log_message(f"Загружено {len(devices)} устройств из файла", "info")
                    self.check_start_conditions()

                    # Показываем сообщение в статусе
                    messagebox.showinfo("Успех", f"Загружено {len(devices)} устройств")
                else:
                    messagebox.showwarning("Внимание", "Файл не содержит устройств")
                    self.log_message("Файл не содержит устройств", "warning")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
                self.log_message(f"Ошибка загрузки устройств: {str(e)}", "error")



        def add_and_close():
            dev_eui = dev_eui_var.get().strip()
            if dev_eui:
                self.devices_listbox.insert(tk.END, dev_eui)
                self.log_message(f"Добавлено устройство: {dev_eui}", "info")
                self.check_start_conditions()
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Добавить", command=add_and_close).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

        entry.focus_set()
        dialog.bind('<Return>', lambda e: add_and_close())

    def check_start_conditions(self):
        """Проверить условия для запуска обновления"""
        has_firmware = bool(self.firmware_path_var.get() and
                            Path(self.firmware_path_var.get()).exists())
        has_devices = self.devices_listbox.size() > 0
        is_connected = "Подключено" in self.status_label.cget("text")

        # Активируем кнопку запуска обновления
        if has_firmware and has_devices and is_connected:
            self.start_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.DISABLED)

    def start_update(self):
        """Начать процесс обновления"""
        # Получаем список устройств
        devices = list(self.devices_listbox.get(0, tk.END))

        if not devices:
            messagebox.showerror("Ошибка", "Список устройств пуст!")
            return

        # Получаем параметры
        firmware_path = self.firmware_path_var.get()
        delay = int(self.delay_var.get())

        # Подтверждение
        confirm_msg = (
            f"Начать обновление {len(devices)} устройств?\n\n"
            f"Файл прошивки: {Path(firmware_path).name}\n"
            f"Задержка: {delay} сек\n"
            f"Класс LoRa: {self.lora_class_var.get()}"
        )

        if not messagebox.askyesno("Подтверждение", confirm_msg):
            return

        # Запускаем в отдельном потоке
        thread = threading.Thread(
            target=self.run_update_thread,
            args=(devices, firmware_path, delay),
            daemon=True
        )
        thread.start()

    def run_update_thread(self, devices, firmware_path, delay):
        """Запуск обновления в отдельном потоке"""
        try:
            # Блокируем интерфейс
            self.start_button.config(state=tk.DISABLED)
            self.progress_var.set(0)

            total = len(devices)
            successful = 0
            failed = 0

            for i, dev_eui in enumerate(devices, 1):
                # Обновляем прогресс
                progress = (i / total) * 100
                self.progress_var.set(progress)
                self.progress_label.config(
                    text=f"Обработка {i}/{total}: {dev_eui}"
                )

                self.log_message(f"Отправка OTAP на {dev_eui}...", "info")

                # Отправляем обновление
                success, message = self.api_client.send_otap_update(
                    dev_eui=dev_eui,
                    firmware_path=firmware_path,
                    lora_class=self.lora_class_var.get()
                )

                if success:
                    successful += 1
                    self.log_message(f"✓ {dev_eui}: успешно", "success")
                else:
                    failed += 1
                    self.log_message(f"✗ {dev_eui}: {message}", "error")

                # Задержка между запросами (кроме последнего)
                if i < total:
                    time.sleep(delay)

                # Обновляем интерфейс
                self.root.update_idletasks()

            # Итоги
            self.progress_label.config(text="Обновление завершено!")

            # Показываем результаты
            result_text = (
                f"Обновление завершено!\n\n"
                f"Всего устройств: {total}\n"
                f"Успешно: {successful}\n"
                f"Не удалось: {failed}"
            )

            # В GUI потоке показываем сообщение
            self.root.after(0, lambda: messagebox.showinfo("Завершено", result_text))

            self.log_message(f"ИТОГ: {successful}/{total} успешно",
                             "success" if successful == total else "warning")

        except Exception as e:
            error_msg = f"Ошибка в процессе обновления: {str(e)}"
            self.log_message(error_msg, "error")
            self.root.after(0, lambda: messagebox.showerror("Ошибка", error_msg))

        finally:
            # Разблокируем интерфейс
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.progress_var.set(100)

    def log_message(self, message: str, level: str = "info"):
        """Добавить сообщение в лог с адаптивным управлением"""
        timestamp = time.strftime("%H:%M:%S")

        # Цвета для разных уровней
        colors = {
            "info": "black",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }

        color = colors.get(level, "black")

        # Добавляем в текстовое поле
        self.log_text.config(state=tk.NORMAL)

        # Автоматическая обрезка старых сообщений для производительности
        current_lines = int(self.log_text.index('end-1c').split('.')[0])
        max_lines = 1000  # Максимальное количество строк

        if current_lines > max_lines:
            # Удаляем самые старые 200 строк
            delete_count = min(200, current_lines - 500)
            self.log_text.delete('1.0', f'{delete_count}.0')

        # Вставляем новое сообщение
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
        self.log_text.tag_config(level, foreground=color)

        # Авто-скроллинг к новым сообщениям
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Также логируем в файл
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    def show_logs(self):
        """Показать файл логов"""
        log_file = "update_log.txt"
        if Path(log_file).exists():
            import subprocess
            import os
            if os.name == 'nt':  # Windows
                os.startfile(log_file)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.run(['open', log_file] if sys.platform == 'darwin'
                               else ['xdg-open', log_file])
        else:
            messagebox.showinfo("Информация", "Файл логов ещё не создан")

    def run(self):
        """Запуск главного цикла приложения"""
        self.root.mainloop()


def main():
    """Основная функция программы"""
    logger.info("=" * 60)
    logger.info("Запуск Lartech OTAP Updater v2.0")
    logger.info("=" * 60)

    try:
        # Запускаем GUI
        app = OTAPUpdaterGUI()
        app.run()

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        messagebox.showerror("Ошибка", f"Критическая ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()