import threading
import math


def cpu_intensive_task():
    while True:
        math.factorial(100000)

def gpu_emulation_task():
    while True:
        result = 0
        for i in range(1000000):
            result += i * i
        if result == 0:
            break

if __name__ == "__main__":
    num_threads = 4
    cpu_threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=cpu_intensive_task)
        t.start()
        cpu_threads.append(t)
    
    gpu_thread = threading.Thread(target=gpu_emulation_task)
    gpu_thread.start()
    
    for t in cpu_threads:
        t.join()
    gpu_thread.join()