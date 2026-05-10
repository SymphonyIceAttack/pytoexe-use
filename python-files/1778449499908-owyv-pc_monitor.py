import serial
import serial.tools.list_ports
import time
import psutil
import wmi

def find_arduino():
    ports = serial.tools.list_ports.comports()

    for port in ports:

        desc = port.description.lower()

        if (
            "arduino" in desc or
            "leonardo" in desc or
            "pro micro" in desc
        ):
            return port.device

    return None

port_name = find_arduino()

if port_name is None:
    print("No Pro Micro found")
    input("Press Enter to exit...")
    quit()

print("Connected to:", port_name)

ser = serial.Serial(port_name, 115200)

w = wmi.WMI(namespace="root\\OpenHardwareMonitor")

def get_cpu_temp():

    try:
        temperature_infos = w.Sensor()

        for sensor in temperature_infos:

            if sensor.SensorType == u'Temperature':

                if 'CPU Package' in sensor.Name:
                    return int(sensor.Value)

                if 'CPU Core' in sensor.Name:
                    return int(sensor.Value)

    except:
        pass

    return 0

while True:

    try:

        cpu_load = int(psutil.cpu_percent(interval=1))

        mem_load = int(psutil.virtual_memory().percent)

        cpu_temp = get_cpu_temp()

        data = f"{cpu_temp},{cpu_load},{mem_load}\n"

        ser.write(data.encode())

        print(data.strip())

        time.sleep(1)

    except:
        pass
