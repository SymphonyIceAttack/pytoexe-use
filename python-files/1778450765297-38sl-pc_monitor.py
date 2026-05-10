import serial
import serial.tools.list_ports
import time
import psutil
import wmi

# ----------------------------
# Find Pro Micro Automatically
# ----------------------------
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


# ----------------------------
# Connect to Arduino
# ----------------------------
port_name = find_arduino()

if port_name is None:

    print("No Pro Micro found")
    input("Press Enter to exit...")
    quit()

print("Connected to:", port_name)

ser = serial.Serial(port_name, 115200)

# ----------------------------
# Connect to LibreHardwareMonitor
# ----------------------------
w = wmi.WMI(namespace="root\\LibreHardwareMonitor")

# ----------------------------
# Read CPU Temp
# ----------------------------
def get_cpu_temp():

    try:

        sensors = w.Sensor()

        for sensor in sensors:

            if sensor.SensorType == u'Temperature':

                name = sensor.Name.lower()

                if (
                    "cpu package" in name or
                    "core average" in name or
                    "ccd1" in name or
                    "cpu core" in name
                ):

                    return int(sensor.Value)

    except Exception as e:

        print("Temp Error:", e)

    return 0


# ----------------------------
# Main Loop
# ----------------------------
while True:

    try:

        cpu_load = int(psutil.cpu_percent(interval=1))

        mem_load = int(psutil.virtual_memory().percent)

        cpu_temp = get_cpu_temp()

        data = f"{cpu_temp},{cpu_load},{mem_load}\n"

        ser.write(data.encode())

        print(data.strip())

        time.sleep(1)

    except Exception as e:

        print("Error:", e)