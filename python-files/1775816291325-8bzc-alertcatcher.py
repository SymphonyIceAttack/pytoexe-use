import os
import time

MT4_DATA_PATH = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\XXXX"

print("Alert Catcher Started")

while True:
    if os.path.exists(MT4_DATA_PATH):
        print("MT4 folder found")
    else:
        print("MT4 folder not found")

    time.sleep(5)