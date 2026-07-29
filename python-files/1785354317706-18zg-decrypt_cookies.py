import os
import sqlite3
import shutil
import sys

try:
    import win32crypt
except ImportError:
    print("Installing pypiwin32...")
    os.system(f"{sys.executable} -m pip install pypiwin32")
    import win32crypt

def get_roblox_cookie():
    # Edge cookie database path
    edge_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies")
    
    if not os.path.exists(edge_path):
        print(f"Cookie database not found at: {edge_path}")
        return
    
    # Create temp copy to avoid database lock
    temp_db = os.path.join(os.getcwd(), "edge_cookies_temp.db")
    
    try:
        shutil.copy2(edge_path, temp_db)
    except PermissionError:
        print("ERROR: Close Edge browser first, then run this script!")
        return
    
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT host_key, name, encrypted_value, path, expires_utc 
        FROM cookies 
        WHERE host_key LIKE '%roblox.com%' AND name = '.ROBLOSECURITY'
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No .ROBLOSECURITY cookie found. Make sure you're logged into Roblox in Edge.")
        conn.close()
        os.remove(temp_db)
        return
    
    for host_key, name, encrypted_value, path, expires in results:
        try:
            # Decrypt using Windows DPAPI
            decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)
            cookie_value = decrypted[1].decode('utf-8')
            
            print(f"\n{'='*60}")
            print(f"HOST: {host_key}")
            print(f"NAME: {name}")
            print(f"PATH: {path}")
            print(f"VALUE: {cookie_value}")
            print(f"{'='*60}\n")
            
            # Also save to file
            with open("roblox_cookie.txt", "w") as f:
                f.write(cookie_value)
            print("Cookie also saved to: roblox_cookie.txt")
            
        except Exception as e:
            print(f"Decryption failed: {e}")
            print("Try running as the same user who is logged into Windows")
    
    conn.close()
    os.remove(temp_db)

if __name__ == "__main__":
    get_roblox_cookie()