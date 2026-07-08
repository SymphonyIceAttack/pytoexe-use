#!/usr/bin/env python3
"""
LimeWire encrypted downloader + decrypter
Uses the key from the URL fragment (after #) to decrypt AES‑GCM.
Works for files shared with a link like https://limewire.com/d/5LvmF#gSzbQzWSnp
"""

import sys
import json
import base64
import hashlib
import os
from pathlib import Path
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# ------------------------------------------------------------
# LimeWire decryption parameters (derived from their JS)
# They use PBKDF2-HMAC-SHA256 with 100000 iterations, 32‑byte salt
# The salt is the first 16 bytes of the encrypted payload.
# The key is derived from the passphrase (the fragment).
# The nonce is the next 12 bytes.
# The rest is the ciphertext + tag (16 bytes).
# ------------------------------------------------------------

def decrypt_limewire(encrypted_data: bytes, passphrase: str) -> bytes:
    # Extract salt (first 16 bytes)
    salt = encrypted_data[:16]
    # Extract nonce (next 12 bytes)
    nonce = encrypted_data[16:28]
    # The rest is ciphertext + auth tag (16 bytes)
    ciphertext_with_tag = encrypted_data[28:]

    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(passphrase.encode('utf-8'))

    # Decrypt (AES-GCM automatically verifies and strips tag)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return plaintext
    except Exception as e:
        raise RuntimeError(f"Decryption failed (wrong key or corrupted data): {e}")

def main():
    # The link you gave
    link = "https://limewire.com/d/5LvmF#gSzbQzWSnp"
    # Parse out file ID and key
    if '#' not in link:
        print("[-] Missing fragment (key) in URL")
        sys.exit(1)
    base_part, key = link.split('#', 1)
    file_id = base_part.rstrip('/').split('/')[-1]
    print(f"[*] File ID: {file_id}")
    print(f"[*] Key:     {key}")

    # 1. Get the download URL from LimeWire API
    api_url = f"https://api.limewire.com/file/{file_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        print(f"[-] API error: {resp.status_code} - {resp.text}")
        sys.exit(1)
    data = resp.json()
    # The API usually returns a 'downloadUrl' field for public files
    download_url = data.get('downloadUrl')
    if not download_url:
        # fallback: try to construct from metadata
        download_url = data.get('url')
    if not download_url:
        print("[-] Could not find download URL in API response")
        print(json.dumps(data, indent=2))
        sys.exit(1)

    print(f"[*] Downloading from: {download_url}")
    dl_resp = requests.get(download_url, headers=headers)
    if dl_resp.status_code != 200:
        print(f"[-] Download failed: {dl_resp.status_code}")
        sys.exit(1)

    encrypted = dl_resp.content
    print(f"[*] Downloaded {len(encrypted)} bytes (encrypted)")

    # 2. Decrypt
    print("[*] Decrypting...")
    try:
        plain = decrypt_limewire(encrypted, key)
    except Exception as e:
        print(f"[-] Decryption error: {e}")
        sys.exit(1)

    # 3. Save the decrypted file (likely a .7z archive)
    out_name = f"{file_id}.7z"
    Path(out_name).write_bytes(plain)
    print(f"[+] Decrypted file saved as: {out_name}")
    print(f"[*] Size: {len(plain)} bytes")
    print("[*] Done.")

if __name__ == "__main__":
    main()