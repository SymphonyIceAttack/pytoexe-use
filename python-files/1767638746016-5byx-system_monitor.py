import psutil
import GPUtil
import wmi
import time

c = wmi.WMI(namespace="root\\OpenHardwareMonitor")

def get_cpu_temp():
    temps = []
    for sensor in c.Sensor():
        if sensor.SensorType == u'Temperature' and 'CPU' in sensor.Name:
            temps.append(sensor.Value)
    return max(temps) if temps else "غير متاح"

def get_gpu_temp():
    temps = []
    for sensor in c.Sensor():
        if sensor.SensorType == u'Temperature' and 'GPU' in sensor.Name:
            temps.append(sensor.Value)
    return max(temps) if temps else "غير متاح"

def get_disk_health():
    disks = []
    for disk in c.Sensor():
        if disk.SensorType == u'Load' and 'HDD' in disk.Name:
            disks.append(disk.Value)
    return disks[0] if disks else "غير متاح"

while True:
    print("="*40)

    # RAM
    ram = psutil.virtual_memory()
    print(f"استهلاك الرام: {ram.percent}%")
    print(f"الرام المستخدمة: {ram.used // (1024**3)} GB")
    print(f"الرام المتاحة: {ram.available // (1024**3)} GB")

    # CPU
    print(f"استهلاك المعالج: {psutil.cpu_percent()}%")
    print(f"حرارة المعالج: {get_cpu_temp()} °C")

    # GPU
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]
        print(f"كرت الشاشة: {gpu.name}")
        print(f"استهلاك GPU: {gpu.load * 100:.1f}%")
        print(f"حرارة GPU: {gpu.temperature} °C")
    else:
        print("كرت الشاشة: غير متاح")

    # Disk
    disk = psutil.disk_usage('/')
    print(f"الهارد المستخدم: {disk.percent}%")
    print(f"المساحة الفاضية: {disk.free // (1024**3)} GB")

    print("="*40)
    time.sleep(5)
