import broadlink

# Vaši fiksni podaci za RM4C mini
DEVICE_IP = '192.168.1.4'
DEVICE_PORT = 80
DEVICE_MAC = b'\xe8\x16V}}\x8f'
DEVICE_TYPE = 21005  # Tip vašeg uređaja

#print("Trenutno povezivanje s RM4C mini...")

# Koristimo gendevice jer je kompatibilan sa svim verzijama broadlink knjižnice
device = broadlink.gendevice(DEVICE_TYPE, (DEVICE_IP, DEVICE_PORT), DEVICE_MAC)

# Autorizacija
device.auth()
    #print("Uređaj je spreman!")
    
    # Vaša IR naredba
naredba = bytes.fromhex("2600f000918f120e120f110f110f112f122f110f110f112f122f112f112f120f110f110f110f128f120e120f110f110f110f110f120e120f112f112f122f110f112f122f112f112f120f110f110f112f120006f2928f110f110f120e120f112f112f120f110f112f112f122f112f120e120f110f110f1190110f110f120e120f110f110f110f110f122f112f112f120f112f112f122f112f110f120f110f112f110006f3918f120f110f110f110f112f122f110f110f112f122f112f122f110f110f110f110f128f120e120f110f110f110f110f120f110f112f112f122f110f112f122f112f112f120f110f110f112f12000d05")
    
    # Slanje naredbe
device.send_data(naredba)
    #print("IR signal je poslan!")

    #print("Greška pri autorizaciji. Provjerite je li uređaj otključan u aplikaciji.")

