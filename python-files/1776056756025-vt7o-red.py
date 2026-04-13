from scapy.all import ARP, Ether, srp
import socket
import pyperclip

resultados = []

def escanear_red(ip_rango):
    global resultados
    resultados = []
    try:
        arp = ARP(pdst=ip_rango)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        paquete = ether / arp
        respuestas, _ = srp(paquete, timeout=2, verbose=False)

        for _, recibido in respuestas:
            ip = recibido.psrc
            mac = recibido.hwsrc
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                hostname = "Desconocido"
            resultados.append({'IP': ip, 'MAC': mac, 'Hostname': hostname})

        print("✅ Escaneo completado.")
        mostrar_resultados()
    except Exception as e:
        print(f"❌ Error al escanear: {e}")

def mostrar_resultados():
    if not resultados:
        print("No hay resultados aún. Usa la opción 1 para escanear.")
        return
    print("\n" + "-" * 70)
    print("IP\t\t\tMAC\t\t\t\tHostname")
    print("-" * 70)
    for d in resultados:
        print(f"{d['IP']}\t{d['MAC']}\t{d['Hostname']}")

def copiar_resultados():
    if not resultados:
        print("❌ No hay resultados para copiar.")
        return
    try:
        texto = "IP\t\t\tMAC\t\t\t\tHostname\n"
        texto += "-" * 70 + "\n"
        for d in resultados:
            texto += f"{d['IP']}\t{d['MAC']}\t{d['Hostname']}\n"
        pyperclip.copy(texto)
        print("📋 Resultados copiados al portapapeles.")
    except Exception as e:
        print(f"❌ Error al copiar: {e}")

def menu():
    ip_rango = "192.168.1.1/24"  # Cambia según tu red
    while True:
        print("\n" + "="*50)
        print("       🛰️ MENÚ DE ESCANEO DE RED")
        print("="*50)
        print("1 → Iniciar escaneo de red")
        print("2 → Copiar resultados al portapapeles")
        print("0 → Salir")
        print("="*50)
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            print(f"Escaneando red: {ip_rango}...")
            escanear_red(ip_rango)
        elif opcion == "2"   