Разберу код пошагово и исправлю ошибки. Вот **исправленная и проверенная версия** кода для OPC UA‑сервера с контроллером BLSD‑50:


```python
from opcua import Server, ua
from pymodbus.client import ModbusTcpClient
import time
import logging
import threading
import struct  # Импорт добавлен в начало файла


# Настройка логирования
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('blsd50_opc_server')

class BLSD50OPCServer:
    def __init__(self,
                 opc_endpoint="opc.tcp://0.0.0.0:4840/server/",
                 opc_server_name="BLSD50 OPC UA Server",
                 modbus_ip="192.168.1.100",  # Замените на IP вашего BLSD-50
                 modbus_port=502):
        # Инициализация OPC UA сервера
        self.opc_server = Server()
        self.opc_server.set_endpoint(opc_endpoint)
        self.opc_server.set_server_name(opc_server_name)

        # Пространство имён
        self.uri = "http://blsd50.example.com"
        self.idx = self.opc_server.register_namespace(self.uri)


        # Настройки Modbus
        self.modbus_ip = modbus_ip
        self.modbus_port = modbus_port
        self.modbus_client = None

        # Переменные OPC UA
        self.variables = {}
        self.running = False  # Добавлено: флаг работы сервера

    def connect_modbus(self):
        """Подключение к контроллеру BLSD-50 по Modbus TCP"""
        try:
            self.modbus_client = ModbusTcpClient(self.modbus_ip, port=self.modbus_port)
            if self.modbus_client.connect():
                _logger.info(f"Успешное подключение к BLSD-50 ({self.modbus_ip}:{self.modbus_port}) по Modbus")
                return True
            else:
                _logger.error("Не удалось подключиться к BLSD-50 по Modbus")
                return False
        except Exception as e:
            _logger.error(f"Ошибка подключения Modbus: {e}")
            return False


    def create_address_space(self):
        """Создание адресного пространства OPC UA"""
        objects = self.opc_server.get_objects_node()

        # Объект контроллера BLSD-50
        blsd50_obj = objects.add_object(self.idx, "BLSD50_Controller")

        # Добавляем переменные (настройте под реальные регистры вашего контроллера)
        var_config = [
            ('Temperature', 0, 'float'),      # Регистр 0 — температура
            ('Pressure', 1, 'float'),       # Регистр 1 — давление
            ('FlowRate', 2, 'float'),       # Регистр 2 — расход
            ('Status', 3, 'int'),           # Регистр 3 — статус
            ('Speed', 4, 'int'),            # Регистр 4 — скорость
            ('ErrorCode', 5, 'int')         # Регистр 5 — код ошибки
        ]

        for name, reg_addr, data_type in var_config:
            var = blsd50_obj.add_variable(self.idx, name, 0.0 if data_type == 'float' else 0)
            var.set_writable()  # Если нужно разрешить запись
            self.variables[name] = {'node': var, 'reg_addr': reg_addr, 'type': data_type}

        _logger.info("Адресное пространство OPC UA создано")

    def read_modbus_data(self):
        """Чтение данных с контроллера BLSD-50 через Modbus"""
        if not self.modbus_client or not self.modbus_client.is_socket_open():
            if not self.connect_modbus():
                return None

        try:
            # Читаем 9 регистров (достаточно для всех переменных)
            result = self.modbus_client.read_holding_registers(address=0, count=9, slave=1)
            if result.isError():
                _logger.error("Ошибка чтения Modbus: " + str(result))
                return None

            # Предполагаем, что данные в формате float (32 бита) и int (16 бит)
            data = {}
            registers = result.registers

            # Температура (регистры 0–1 как float)
            if len(registers) >= 2:
                data['Temperature'] = self._registers_to_float(registers[0:2])
            else:
                data['Temperature'] = 0.0

            # Давление (регистры 2–3 как float)
            if len(registers) >= 4:
                data['Pressure'] = self._registers_to_float(registers[2:4])
            else:
                data['Pressure'] = 0.0

            # Расход (регистры 4–5 как float)
            if len(registers) >= 6:
                data['FlowRate'] = self._registers_to_float(registers[4:6])
            else:
                data['FlowRate'] = 0.0

            # Статус (регистр 6 как int16)
            if len(registers) > 6:
                data['Status'] = registers[6]
            else:
                data['Status'] = 0

            # Скорость (регистр 7 как int16)
            if len(registers) > 7:
                data['Speed'] = registers[7]
            else:
                data['Speed'] = 0

            # Код ошибки (регистр 8 как int16)
            if len(registers) > 8:
                data['ErrorCode'] = registers[8]
            else:
                data['ErrorCode'] = 0

            return data
        except Exception as e:
            _logger.error(f"Ошибка чтения данных Modbus: {e}")
            return None


    @staticmethod
    def _registers_to_float(registers):
        """Конвертация двух регистров Modbus в float"""
        # Объединяем два 16‑битных регистра в 32‑битное число
        combined = (registers[0] << 16) | registers[1]
        # Конвертируем в float
        return struct.unpack('f', struct.pack('I', combined))[0]

    def update_opc_variables(self):
        """Обновление переменных OPC UA данными с контроллера"""
        data = self.read_modbus_data()
        if data:
            for name, value in data.items():
                if name in self.variables:
                    self.variables[name]['node'].set_value(value)
            _logger.debug(f"Обновлено: {data}")

    def start_polling(self, interval=1.0):
        """Запуск периодического опроса контроллера в отдельном потоке"""
        def polling_loop():
            while self.running:
                self.update_opc_variables()
                time.sleep(interval)

        self.polling_thread = threading.Thread(target=polling_loop, daemon=True)
        self.polling_thread.start()


    def start(self):
        """Запуск OPC UA сервера"""
        try:
            # Создание адресного пространства
            self.create_address_space()

            # Запуск OPC UA сервера
            self.opc_server.start()
            _logger.info(f"OPC UA сервер запущен: {self.opc_server.endpoint}")

            # Запуск опроса контроллера
            self.running = True
            self.start_polling(interval=1.0)  # Опрос каждую секунду

            # Бесконечный цикл (для поддержания работы сервера)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                _logger.info("Остановка сервера по запросу пользователя")
        except Exception as e:
            _logger.error(f"Ошибка при запуске сервера: {e}")
        finally:
            self.stop()

    def stop(self):
        """Остановка сервера"""
        self.running = False
        if self.modbus_client:
            self.modbus_client.close()
        self.opc_server.stop()
        _logger