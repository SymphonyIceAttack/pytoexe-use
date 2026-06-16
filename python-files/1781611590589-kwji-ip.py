import socket
import subprocess

nomOrdi = socket.gethostname()
ip = socket.gethostbyname(nomOrdi)
print("Le nom de l''ordi est:", nomOrdi)
print("L'adresse ip de l'ordi est:", ip)


cmd = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True).stdout
NbDHCP = cmd.find("Serveur DHCP")
print(NbDHCP)

if NbDHCP > 0:
    print("L'ordi est en DHCP")
else:
    print("l'ordi n'est pas en dhcp")