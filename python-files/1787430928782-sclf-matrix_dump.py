#!/usr/bin/env python3
"""
Precte raw stav matice klavesnice pres VIA protokol (id_get_keyboard_value / id_switch_matrix_state).
Nezavisi na nactenem JSON definicnim souboru ve VIA appce - jde primo na HID rozhrani.

Instalace (Windows/Linux/Mac):
    pip install hid

Pouziti:
    1. Zavri VIA appku (nebo alespon zavri tab s touto klavesnici) - jinak si o HID rozhrani "peruje" ona.
    2. Pripoj klavesnici KABELEM.
    3. Uprav VID/PID nize, pokud je potreba (aktualne 0x320F / 0x5088).
    4. Spust: python matrix_dump.py
    5. Mackej postupne KAZDOU fyzickou klavesu (jednu po druhe, s malou pauzou mezi nimi).
       Skript vypise, ktere bajty/bity se zmenily -> to je pozice te klavesy v matici.
"""

import hid
import time
import sys

VID = 0x320F
PID = 0x5088
USAGE_PAGE = 0xFF60  # VIA raw HID usage page

def find_via_interface():
    candidates = [d for d in hid.enumerate(VID, PID) if d.get('usage_page') == USAGE_PAGE]
    if not candidates:
        print("Nenalezeno HID rozhrani s usage_page 0xFF60 pro dane VID/PID.")
        print("Vsechna nalezena rozhrani pro toto VID/PID:")
        for d in hid.enumerate(VID, PID):
            print(f"  path={d['path']} usage_page={hex(d.get('usage_page', 0))} usage={hex(d.get('usage', 0))} interface={d.get('interface_number')}")
        sys.exit(1)
    return candidates[0]['path']

def get_matrix_state(dev, report_len=32):
    # bajt 0 = report id (0x00 pokud se nepouziva), bajt 1 = command, bajt 2 = subcommand
    # VIA obvykle pouziva 32-bajtove (nebo 33 s report id) HID reporty - pokud selze, zkus 33.
    buf = [0x00] * report_len
    buf[0] = 0x02  # id_get_keyboard_value
    buf[1] = 0x03  # id_switch_matrix_state
    dev.write(buf)
    time.sleep(0.01)
    data = dev.read(report_len, timeout_ms=200)
    return data

def main():
    path = find_via_interface()
    print(f"Otevirem HID zarizeni: {path}")
    dev = hid.device()
    dev.open_path(path)
    dev.set_nonblocking(True)

    print("Pripojeno. Mackej postupne kazdou fyzickou klavesu (jednu po druhe).")
    print("Ctrl+C pro ukonceni.\n")

    prev = None
    try:
        while True:
            data = get_matrix_state(dev)
            if data and data != prev:
                # vypis jako hex i binarne, ať je videt, ktery bit se zmenil
                hex_str = " ".join(f"{b:02x}" for b in data)
                print(f"RAW: {hex_str}")
                if prev is not None:
                    diffs = []
                    for i, (a, b) in enumerate(zip(prev, data)):
                        if a != b:
                            diffs.append((i, a, b))
                    if diffs:
                        print("  Zmeny (byte_index, stara_hodnota, nova_hodnota):")
                        for idx, a, b in diffs:
                            print(f"    byte {idx}: {a:08b} -> {b:08b}")
                prev = data
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nKonec.")
    finally:
        dev.close()

if __name__ == "__main__":
    main()
