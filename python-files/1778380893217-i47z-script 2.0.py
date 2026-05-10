import zipfile

def make_simple_zip_bomb(output_file="D:/file.zip", num_files=100, file_size_mb=1):
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i in range(num_files):
            data = b'\x00' * (1024 * 1024 * file_size_mb)
            zf.writestr(f"file_{i}.txt", data)
    print(f"Created {output_file} successfully!")
make_simple_zip_bomb()
def repeat(func, times):
    for _ in range(times):
        func()

# Example usage:
repeat(make_simple_zip_bomb, 2)
import time

def task():
    print("Starting task...")
    time.sleep(2)  # simulate work
    print("Task finished")

def repeat_forever(func):
    cycle = 1
    while True:
        print(f"\n--- Cycle {cycle} ---")
        start = time.time()

        func()  # run the task

        end = time.time()
        print(f"Cycle {cycle} completed in {end - start:.2f} seconds")

        cycle += 1

repeat_forever(task)
