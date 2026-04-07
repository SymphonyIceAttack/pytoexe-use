import os
import threading
from file_scanner import scan_file
from report_generator import save_report
from config import ENABLE_MULTITHREADING, SCAN_PATH

# Scan all files in the given directory (recursive)
def scan_directory(directory):
    print(f"\n Scanning directory: {directory}")
    threads = []

    def worker(file_path):
        matches = scan_file(file_path)
        if matches:
            save_report(file_path, matches)

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if ENABLE_MULTITHREADING:
                thread = threading.Thread(target=worker, args=(file_path,))
                threads.append(thread)
                thread.start()
            else:
                worker(file_path)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print("\n Scan Complete. Check the 'output' folder for results.")