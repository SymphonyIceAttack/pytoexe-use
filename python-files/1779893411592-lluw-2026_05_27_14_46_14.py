#!/usr/bin/env python3
import hashlib
import subprocess
import platform
import os
import sys

STR_ID1 = "uZGYTuHBTc2aXUa7WmBUckZxMQFHEgUzHpxgz7NyLNsSzsstfCzRrjttJJRvzAynxUuf3U"
STR_ID2 = "5ZsdJVUmLt3qnzZfnweXzgFMXMDCrVWGcjvMCxWWcmhUgM5gHx9fY8nctbYNyVfyKjsCnS"
DEFAULT_SERIAL = "123456"

PRODUCTS = {
    1: {"name": "Aryson OST to PST Converter", "order_value": "ARYOSTPSTORD", "title": "Aryson OST to PST Converter", "product_code": "1"}
}

def get_windows_serial():
    try:
        drive_letter = os.path.expanduser("~")[0]
        vbs_script = (
            f'Set objFSO = CreateObject("Scripting.FileSystemObject")\n'
            f'Set colDrives = objFSO.Drives\n'
            f'Set objDrive = colDrives.item("{drive_letter}")\n'
            f'Wscript.Echo objDrive.SerialNumber'
        )
        vbs_path = os.path.join(os.environ.get('TEMP'), 'realhowto.vbs')
        with open(vbs_path, 'w') as f:
            f.write(vbs_script)
        result = subprocess.run(['cscript', '//NoLogo', vbs_path], capture_output=True, text=True, timeout=5)
        os.remove(vbs_path)
        serial = result.stdout.strip()
        if serial:
            return serial
    except Exception:
        pass
    return DEFAULT_SERIAL

def get_macos_serial():
    try:
        result = subprocess.run(
            ['bash', '-c', 'system_profiler SPHardwareDataType | awk \'/Serial/ {print $4}\''],
            capture_output=True, text=True, timeout=5
        )
        serial = result.stdout.strip()
        if serial:
            return serial
    except Exception:
        pass
    return DEFAULT_SERIAL

def get_linux_serial():
    try:
        if os.path.exists('/etc/machine-id'):
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()[:16]
    except Exception:
        pass
    return DEFAULT_SERIAL

def get_hardware_serial():
    os_name = platform.system().lower()
    if 'windows' in os_name:
        return get_windows_serial()
    elif 'darwin' in os_name:
        return get_macos_serial()
    else:
        return get_linux_serial()

def calculate_hash(str_serial_number):
    raw_string = STR_ID1 + str_serial_number + STR_ID1 + STR_ID2
    md5_bytes = hashlib.md5(raw_string.encode('utf-8')).digest()
    big_int = int.from_bytes(md5_bytes, byteorder='big')
    hex_str = format(big_int, 'x')
    while len(hex_str) < 32:
        hex_str = "0" + hex_str
    return hex_str.upper()

def save_license_file(activation_key, messagebox_title):
    os_name = platform.system().lower()
    if 'windows' in os_name:
        folder = os.path.join(os.environ.get('APPDATA'), messagebox_title)
    elif 'darwin' in os_name:
        folder = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', messagebox_title)
    else:
        folder = os.path.join(os.path.expanduser('~'), '.config', messagebox_title)
    try:
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, 'license.lic')
        with open(file_path, 'w') as f:
            f.write(activation_key)
        return file_path
    except Exception:
        return None

def generate_license(product_id, license_type):
    product = PRODUCTS[product_id]
    hw_serial = get_hardware_serial()
    order_value = product['order_value']
    product_code = product['product_code']
    full_serial = f"{hw_serial}{product_code}{order_value}"
    hash_key = calculate_hash(full_serial)
    final_key = f"{hash_key}{license_type}"
    return {
        "hw_serial": hw_serial,
        "product_code": product_code,
        "order_value": order_value,
        "full_serial": full_serial,
        "hash_key": hash_key,
        "final_key": final_key,
        "title": product['title']
    }

def main():
    hw_id = get_hardware_serial()
    print(f"[SYSTEM] OS: {platform.system()} {platform.release()}")
    print(f"[SYSTEM] Hardware ID: {hw_id}\n")

    print("[SELECT PRODUCT]")
    for id, p in PRODUCTS.items():
        print(f" [{id}] {p['name']}")

    try:
        choice = int(input("[?] Enter choice: ").strip())
    except ValueError:
        print("[!] Invalid input.")
        sys.exit(1)

    print("\n[SELECT LICENSE TYPE / EDITION]")
    print(" [1] Enterprise / Full (Recommended)")
    print(" [2] Personal / Home")
    print(" [3] Professional")
    print(" [4] Trial / Demo\n")

    try:
        lic_type = input("[?] Enter license type (default 1): ").strip()
        if not lic_type:
            lic_type = "1"
        if int(lic_type) not in [1, 2, 3, 4]:
            lic_type = "1"
    except ValueError:
        lic_type = "1"

    if choice == 0:
        print("\n" + "-"*65)
        print("GENERATING KEYS FOR ALL PRODUCTS")
        print("-"*65)
        for pid in PRODUCTS:
            result = generate_license(pid, lic_type)
            print(f"\n[{result['title']}]" )
            print(f"Key: {result['final_key']}")
            save_path = save_license_file(result['final_key'], result['title'])
            if save_path:
                print(f"Saved: {save_path}")
        print("\n" + "-"*65)

    elif choice in PRODUCTS:
        result = generate_license(choice, lic_type)

        print("\n" + "-"*65)
        print("[DEBUG INFO]")
        print("-"*65)
        print(f" Hardware Serial : {result['hw_serial']}")
        print(f" Product Code : {result['product_code']}")
        print(f" Order Value : {result['order_value']}")
        print(f" Concat Serial : {result['full_serial']}")
        print(f" MD5 Hash : {result['hash_key']}")
        print(f" License Type : {lic_type}")
        print("-"*65)

        print(f"\n[★] YOUR ACTIVATION KEY ({len(result['final_key'])} chars):")
        print(f"\n {result['final_key']}\n")
        print("-"*65)

        try:
            import pyperclip
            pyperclip.copy(result['final_key'])
            print("[+] Key copied to clipboard!")
        except ImportError:
            pass

        save_path = save_license_file(result['final_key'], result['title'])
        if save_path:
            print(f"[+] License file saved to: {save_path}")

    else:
        print("[!] Invalid product selection.")
        sys.exit(1)


if __name__ == "__main__":
    main()