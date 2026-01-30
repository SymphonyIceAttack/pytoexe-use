import time
import os
import socket
import sys

print("Consol")
print("Abak Console")
hostname = socket.gethostname()
print("Läuft auf",hostname)
print("Bereit")

behfel = input(f"{hostname}:")

if behfel == "exit":
    print(f"{behfel}...")
    time.sleep(1)
    sys.exit()
elif behfel == "create":
    data_1 = input("Title:")
    data_2 = input("Inhalt")
    data_3 = input("Pfad:")
    data_4_data =f"{data_3}/{data_1}.txt"
    with open(data_4_data, "w") as f:
        f.write(data_2)
        
    print("Createt")
    print(f"under:{data_4_data}")
    time.sleep(1)
    sys.exit()
elif behfel == "delet":
    data_2_1 = input("Title:")
    data_2_2 = input("Pfad:")
    data_2_3_data = f"{data_2_2}/{data_2_1}"
    data_2_4 = input("Bist du dir sicher?")
    
    if data_2_4 == "Ja":
        os.remove(data_2_3)
        print("Deletet")
        time.sleep(1)
        sys.exit()
    else:
        print("Abruch comopledet")
        time.sleep(1)
        sys.exit()
elif behfel == "username":
    print("username:",hostname)
    input("press button...")
    time.sleep(1)
    sys.exit()
else:
    print("Fail")
    print(f"{behfel} has not task")
    time.sleep(1)
    sys.exit()