import subprocess
import time

for i in range(10000):
    subprocess.Popen('explorer')
    time.sleep(0.00000001)  # small delay to avoid system overload

print("10000 conductors opened.")
