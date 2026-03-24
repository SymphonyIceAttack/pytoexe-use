from pypresence import Presence
import pygetwindow as gw
import time
import os

# Твой Application ID
client_id = '1234567890123456789'  

def get_packet_tracer_status():
    """Ищет окно Packet Tracer и пытается достать название открытого файла"""
    try:
        # Получаем все заголовки всех открытых окон
        titles = gw.getAllTitles()
        
        # Ищем окно, в названии которого есть Cisco Packet Tracer
        for title in titles:
            if "Cisco Packet Tracer" in title:
                # Если открыт файл, заголовок обычно выглядит так:
                # "Cisco Packet Tracer - C:\Users\Name\Desktop\lab.pkt"
                if "-" in title and (".pkt" in title or ".pka" in title):
                    # Разбиваем строку и берем правую часть (путь к файлу)
                    filepath = title.split("-")[-1].strip()
                    # Достаем только имя файла без длинного пути (lab.pkt)
                    filename = os.path.basename(filepath)
                    return f"Работает над: {filename}"
                else:
                    return "В главном меню"
                    
        return "Программа закрыта"
    except Exception:
        return "Неизвестный статус"

def connect_rpc():
    try:
        RPC = Presence(client_id)
        RPC.connect()
        print("Успешно подключено к Discord!")

        start_time = time.time() # Таймер "В игре уже..."

        while True:
            # Получаем актуальный статус из заголовка окна
            current_file_status = get_packet_tracer_status()
            
            # Если программа закрыта, можно очистить статус (или оставить как есть)
            if current_file_status == "Программа закрыта":
                RPC.clear()
                print("Packet Tracer не найден. Ждем...")
            else:
                # Обновляем статус в реальном времени
                RPC.update(
                    details="Cisco Packet Tracer", 
                    state=current_file_status,          # Сюда пойдет "Работает над: lab.pkt"
                    large_image="cisco_logo",           
                    large_text="Packet Tracer",         
                    start=start_time                    
                )
                print(f"Статус обновлен: {current_file_status}")
            
            # ВАЖНО: Discord разрешает обновлять статус не чаще, чем раз в 15 секунд
            time.sleep(15) 

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    connect_rpc()