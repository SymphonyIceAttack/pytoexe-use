from scapy.all import ARP, Ether, srp
import socket
import sys

def escanear(ip_rango):
    arp = ARP(pdst=ip_rango)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    paquete = ether / arp
    respuestas, _ = srp(paquete, timeout=2, verbose=False)

    dispositivos = []
    for _, recibido in respuestas:
        ip = recibido.psrc
        mac = recibido.hwsrc
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            hostname = "Desconocido"
        dispositivos.append({'IP': ip, 'MAC': mac, 'Hostname': hostname})
    return dispositivos

if __name__ == "__main__":
    rango = input("Ingresa el rango de red (ej. 192.168.1.1/24): ")
    dispositivos = escanear(rango)
    print("\nIP\t\t\tMAC\t\t\t\tHostname")
    print("-" * 60)
    for d in dispositivos:
        print(f"{d['IP']}\t{d['MAC']}\t{d['Hostname']}")
    input("\nPresiona Enter para salir...")   