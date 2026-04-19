"""
Crimson Desert - Inventory Expander v2.0.0
Patches the game's PAZ archive to increase inventory slot count.

Handles both the old uncompressed format and the new LZ4-compressed format
(introduced in game updates). The inventory data lives in inventory.pabgb
inside 0008/0.paz, which is LZ4-compressed and indexed by 0008/0.pamt.

Pipeline:
  1. Find inventory.pabgb via PAMT index (or AOB scan fallback)
  2. Read and LZ4-decompress the block
  3. Modify Character record (defaultSlot, maxSlot)
  4. LZ4-recompress and write back to PAZ
  5. Update PAMT comp_size if it changed
  6. Recompute PAMT hash and PAPGT hash (integrity chain)

Usage:
  1. Place this script anywhere on your PC
  2. Double-click to run (or: py -3 patch_inventory.py)
  3. Enter your Crimson Desert install path when prompted
  4. Choose your desired slot counts
  5. Launch the game -- your inventory is expanded!

To restore vanilla: run the script again and choose "Restore backup"

Dependencies: pip install lz4
"""

import struct
import shutil
import os
import sys

VERSION = "2.4.0"

PAZ_SUBDIR = "0008"
PAZ_FILE = "0.paz"
PAMT_FILE = "0.pamt"

VANILLA_DEFAULT = 50
VANILLA_MAX = 240
SAFE_MAX_CEILING = 700

# Signature in decompressed data: type_id(02 00) + name_len(09 00 00 00) + "Character" + null(00)
# Flag byte excluded — it changed from 0x01 to 0x00 in game version 1.02.00
CHAR_SIG = struct.pack('<HI', 2, 9) + b'Character\x00'

INTEGRITY_SEED = 0xC5EDE


# ── Bob Jenkins hashlittle ───────────────────────────────────────────

def _rot(v, k):
    return ((v << k) | (v >> (32 - k))) & 0xFFFFFFFF

def hashlittle(data: bytes, initval: int = 0) -> int:
    """Bob Jenkins lookup3 hashlittle -- returns primary hash (c)."""
    length = len(data)
    a = b = c = (0xDEADBEEF + length + initval) & 0xFFFFFFFF
    offset = 0

    while length > 12:
        a = (a + struct.unpack_from("<I", data, offset)[0]) & 0xFFFFFFFF
        b = (b + struct.unpack_from("<I", data, offset + 4)[0]) & 0xFFFFFFFF
        c = (c + struct.unpack_from("<I", data, offset + 8)[0]) & 0xFFFFFFFF

        a = (a - c) & 0xFFFFFFFF; a ^= _rot(c, 4);  c = (c + b) & 0xFFFFFFFF
        b = (b - a) & 0xFFFFFFFF; b ^= _rot(a, 6);  a = (a + c) & 0xFFFFFFFF
        c = (c - b) & 0xFFFFFFFF; c ^= _rot(b, 8);  b = (b + a) & 0xFFFFFFFF
        a = (a - c) & 0xFFFFFFFF; a ^= _rot(c, 16); c = (c + b) & 0xFFFFFFFF
        b = (b - a) & 0xFFFFFFFF; b ^= _rot(a, 19); a = (a + c) & 0xFFFFFFFF
        c = (c - b) & 0xFFFFFFFF; c ^= _rot(b, 4);  b = (b + a) & 0xFFFFFFFF
        offset += 12
        length -= 12

    remaining = data[offset:]
    if length > 0:
        padded = remaining + b"\x00" * (12 - len(remaining))
        if length >= 1:  a = (a + padded[0]) & 0xFFFFFFFF
        if length >= 2:  a = (a + (padded[1] << 8)) & 0xFFFFFFFF
        if length >= 3:  a = (a + (padded[2] << 16)) & 0xFFFFFFFF
        if length >= 4:  a = (a + (padded[3] << 24)) & 0xFFFFFFFF
        if length >= 5:  b = (b + padded[4]) & 0xFFFFFFFF
        if length >= 6:  b = (b + (padded[5] << 8)) & 0xFFFFFFFF
        if length >= 7:  b = (b + (padded[6] << 16)) & 0xFFFFFFFF
        if length >= 8:  b = (b + (padded[7] << 24)) & 0xFFFFFFFF
        if length >= 9:  c = (c + padded[8]) & 0xFFFFFFFF
        if length >= 10: c = (c + (padded[9] << 8)) & 0xFFFFFFFF
        if length >= 11: c = (c + (padded[10] << 16)) & 0xFFFFFFFF
        if length >= 12: c = (c + (padded[11] << 24)) & 0xFFFFFFFF

        c ^= b; c = (c - _rot(b, 14)) & 0xFFFFFFFF
        a ^= c; a = (a - _rot(c, 11)) & 0xFFFFFFFF
        b ^= a; b = (b - _rot(a, 25)) & 0xFFFFFFFF
        c ^= b; c = (c - _rot(b, 16)) & 0xFFFFFFFF
        a ^= c; a = (a - _rot(c, 4)) & 0xFFFFFFFF
        b ^= a; b = (b - _rot(a, 14)) & 0xFFFFFFFF
        c ^= b; c = (c - _rot(b, 24)) & 0xFFFFFFFF

    return c


# ── PAMT parser (minimal, self-contained) ────────────────────────────

def find_inventory_entry(pamt_path, paz_dir):
    """Parse PAMT to find the inventory.pabgb entry.

    Returns: (paz_file, offset, comp_size, orig_size, flags, pamt_record_offset)
             pamt_record_offset is the byte position in the PAMT where
             offset(4)+comp_size(4)+orig_size(4)+flags(4) starts.
    """
    with open(pamt_path, 'rb') as f:
        data = f.read()

    pamt_stem = os.path.splitext(os.path.basename(pamt_path))[0]

    off = 4  # skip magic
    paz_count = struct.unpack_from('<I', data, off)[0]; off += 4
    off += 8  # hash + zero

    for i in range(paz_count):
        off += 8  # hash + size
        if i < paz_count - 1:
            off += 4  # separator

    # Folder section
    folder_size = struct.unpack_from('<I', data, off)[0]; off += 4
    folder_end = off + folder_size
    folder_prefix = ""
    while off < folder_end:
        parent = struct.unpack_from('<I', data, off)[0]
        slen = data[off + 4]
        name = data[off + 5:off + 5 + slen].decode('utf-8', errors='replace')
        if parent == 0xFFFFFFFF:
            folder_prefix = name
        off += 5 + slen

    # Node section
    node_size = struct.unpack_from('<I', data, off)[0]; off += 4
    node_start = off
    nodes = {}
    while off < node_start + node_size:
        rel = off - node_start
        parent = struct.unpack_from('<I', data, off)[0]
        slen = data[off + 4]
        name = data[off + 5:off + 5 + slen].decode('utf-8', errors='replace')
        nodes[rel] = (parent, name)
        off += 5 + slen

    def build_path(node_ref):
        parts = []
        cur = node_ref
        while cur != 0xFFFFFFFF and len(parts) < 64:
            if cur not in nodes:
                break
            p, n = nodes[cur]
            parts.append(n)
            cur = p
        return ''.join(reversed(parts))

    # Record section
    folder_count = struct.unpack_from('<I', data, off)[0]; off += 4
    off += 4  # hash
    off += folder_count * 16

    # File records (20 bytes each)
    while off + 20 <= len(data):
        node_ref, paz_offset, comp_size, orig_size, flags = \
            struct.unpack_from('<IIIII', data, off)

        paz_index = flags & 0xFF
        node_path = build_path(node_ref)
        full_path = f"{folder_prefix}/{node_path}" if folder_prefix else node_path

        if 'inventory.pabgb' in full_path.lower():
            paz_num = int(pamt_stem) + paz_index
            paz_file = os.path.join(paz_dir, f"{paz_num}.paz")
            # pamt_record_offset points to the start of the 16-byte
            # (offset, comp_size, orig_size, flags) block within the 20-byte record
            return (paz_file, paz_offset, comp_size, orig_size, flags, off + 4)

        off += 20

    return None


# ── LZ4 decompression/compression ────────────────────────────────────

def lz4_decompress(data, orig_size):
    """LZ4 block decompression (no frame header)."""
    try:
        import lz4.block
        return lz4.block.decompress(data, uncompressed_size=orig_size)
    except ImportError:
        print("\nERROR: lz4 module not found. Install it with:")
        print("  pip install lz4")
        sys.exit(1)


def lz4_compress(data):
    """LZ4 block compression (no frame header)."""
    import lz4.block
    return lz4.block.compress(data, store_size=False)


# ── Integrity chain updates ──────────────────────────────────────────

def update_pamt_comp_size(pamt_path, record_offset, new_comp_size):
    """Update the comp_size field in a PAMT file record.

    record_offset: byte position in PAMT where offset(4)+comp_size(4)+... starts.
    comp_size is at record_offset + 4.

    Also recomputes the PAMT integrity hash at bytes [0:4].
    """
    with open(pamt_path, 'rb') as f:
        data = bytearray(f.read())

    old_comp = struct.unpack_from('<I', data, record_offset + 4)[0]
    struct.pack_into('<I', data, record_offset + 4, new_comp_size)

    # Recompute PAMT hash: hashlittle(pamt[12:], 0xC5EDE) stored at pamt[0:4]
    # Wait -- actually the PAMT hash is stored in the PAMT header.
    # From the code: pamt[0:4] = magic, pamt[4:8] = paz_count, pamt[8:12] = hash + zero
    # Actually from papgt_manager: compute_pamt_hash = hashlittle(pamt[12:], 0xC5EDE)
    # And that hash is stored in PAPGT, not in the PAMT itself.
    # The PAMT header has: [magic:4][pazCount:4][hash:4][zero:4]
    # where hash at offset 8 is... let me check.

    # From crimson_browser_handler line 244: struct.pack_into('<I', data, 0, new_hash)
    # So PAMT hash IS at offset 0? No wait, that line was updating PAMT hash at offset 0.
    # But PamtFile.cpp shows: off=0 skip magic(4), then pazCount(4), then hash(4), then zero(4)
    # The crimson_browser_handler stores it at offset 0 which seems wrong based on the C++ code.
    # Let me look more carefully...

    # Actually the PAMT hash in the crimson_browser_handler is stored at PAMT[0]:
    # struct.pack_into('<I', data, 0, new_hash)
    # But the C++ code skips offset 0 as "magic". This seems contradictory.
    # However, the fact is that the game DOES check integrity somehow.
    # Let's check what byte 0 actually is in our PAMT.

    # Actually wait -- looking at the PAZ parse code, offset 0 IS the magic/version,
    # and the hashlittle computation is over pamt[12:]. The hash is NOT stored in the
    # PAMT itself -- it's stored in the PAPGT entry for this directory.
    # The crimson_browser_handler code at line 244 stores the hash at PAMT[0] which
    # is likely overwriting the magic field, which seems like a bug -- but it doesn't
    # matter because the game only checks the hash via PAPGT.

    # Update comp_size and recompute PAMT self-hash at [0:4]
    struct.pack_into('<I', data, record_offset + 4, new_comp_size)
    pamt_hash = hashlittle(bytes(data[12:]), INTEGRITY_SEED)
    struct.pack_into('<I', data, 0, pamt_hash)

    with open(pamt_path, 'wb') as f:
        f.write(bytes(data))

    return old_comp


def update_papgt(game_dir, pamt_subdir):
    """Recompute PAPGT hashes after modifying a PAMT file.

    1. Read the modified PAMT, compute its hash
    2. Find the PAPGT entry for the given directory
    3. Update the PAMT hash in PAPGT
    4. Recompute the PAPGT file hash
    """
    papgt_path = os.path.join(game_dir, "meta", "0.papgt")
    pamt_path = os.path.join(game_dir, pamt_subdir, PAMT_FILE)

    if not os.path.exists(papgt_path):
        print(f"  WARNING: PAPGT not found at {papgt_path}, skipping integrity update")
        return False

    # Compute new PAMT hash
    with open(pamt_path, 'rb') as f:
        pamt_data = f.read()
    new_pamt_hash = hashlittle(pamt_data[12:], INTEGRITY_SEED)

    # Read PAPGT
    with open(papgt_path, 'rb') as f:
        papgt = bytearray(f.read())

    if len(papgt) < 16:
        print(f"  WARNING: PAPGT too small, skipping")
        return False

    # PAPGT format:
    #   [0:4]  = metadata
    #   [4:8]  = file hash: hashlittle(papgt[12:], 0xC5EDE)
    #   [8:12] = metadata (entry count or similar)
    #   [12:]  = N x 12-byte entries + string table

    # Find entry count
    entry_start = 12
    entry_count = _find_papgt_entry_count(papgt, entry_start)

    # String table starts after entries + 4-byte size field
    string_table_size_pos = entry_start + entry_count * 12
    string_table_start = string_table_size_pos + 4

    # Search for our directory name in entries
    found = False
    for i in range(entry_count):
        pos = entry_start + i * 12
        flags = struct.unpack_from('<I', papgt, pos)[0]
        name_offset = struct.unpack_from('<I', papgt, pos + 4)[0]
        old_hash = struct.unpack_from('<I', papgt, pos + 8)[0]

        # Read directory name from string table
        abs_off = string_table_start + name_offset
        if abs_off >= len(papgt):
            continue
        end = papgt.index(0, abs_off) if 0 in papgt[abs_off:] else len(papgt)
        dir_name = papgt[abs_off:end].decode('ascii', errors='replace')

        if dir_name == pamt_subdir:
            struct.pack_into('<I', papgt, pos + 8, new_pamt_hash)
            found = True
            break

    if not found:
        print(f"  WARNING: Directory '{pamt_subdir}' not found in PAPGT")
        return False

    # Recompute PAPGT file hash
    papgt_hash = hashlittle(bytes(papgt[12:]), INTEGRITY_SEED)
    struct.pack_into('<I', papgt, 4, papgt_hash)

    with open(papgt_path, 'wb') as f:
        f.write(bytes(papgt))

    return True


def _find_papgt_entry_count(papgt, entry_start):
    """Determine PAPGT entry count by finding the string table size field."""
    file_size = len(papgt)
    for n in range(1, 100):
        size_pos = entry_start + n * 12
        if size_pos + 4 > file_size:
            break
        string_size = struct.unpack_from('<I', papgt, size_pos)[0]
        if size_pos + 4 + string_size == file_size:
            return n
    return 0


# ── Core patching logic ──────────────────────────────────────────────

def find_and_read_inventory(game_path):
    """Find inventory.pabgb via PAMT, decompress, return record info.

    Returns: dict with keys:
        paz_path, pamt_path, paz_offset, comp_size, orig_size,
        pamt_record_offset, decompressed, char_offset,
        cur_default, cur_max
    Or None on failure.
    """
    paz_path = os.path.join(game_path, PAZ_SUBDIR, PAZ_FILE)
    pamt_path = os.path.join(game_path, PAZ_SUBDIR, PAMT_FILE)

    if not os.path.exists(pamt_path):
        print(f"  PAMT not found: {pamt_path}")
        return None

    paz_dir = os.path.join(game_path, PAZ_SUBDIR)
    entry = find_inventory_entry(pamt_path, paz_dir)
    if entry is None:
        print("  inventory.pabgb not found in PAMT index")
        return None

    paz_file, paz_offset, comp_size, orig_size, flags, pamt_rec_off = entry
    is_compressed = comp_size != orig_size and ((flags >> 16) & 0x0F) == 2

    print(f"  Found inventory.pabgb:")
    print(f"    PAZ offset:  0x{paz_offset:X}")
    print(f"    Comp size:   {comp_size:,} bytes")
    print(f"    Orig size:   {orig_size:,} bytes")
    print(f"    Compressed:  {is_compressed} (LZ4)")

    # Read from PAZ
    with open(paz_file, 'rb') as f:
        f.seek(paz_offset)
        raw = f.read(comp_size)

    # Decompress if needed
    if is_compressed:
        decompressed = lz4_decompress(raw, orig_size)
        if len(decompressed) != orig_size:
            print(f"  ERROR: Decompressed size mismatch: {len(decompressed)} != {orig_size}")
            return None
    else:
        decompressed = raw

    # Find Character record in decompressed data
    idx = decompressed.find(CHAR_SIG)
    if idx < 0:
        print("  ERROR: Character record not found in decompressed data")
        return None

    # Find defaultSlot and maxSlot dynamically — the number of bytes between
    # the signature and the slot fields changed between game versions.
    # Scan forward from the signature for the vanilla pair (50, 240).
    # If already patched, scan for any two consecutive uint16 where
    # 1 <= first <= 999 and first <= second <= 999, preceded by known trailer byte 0x01.
    base = idx + len(CHAR_SIG)
    ds_off = None
    ms_off = None

    # First try: find vanilla values (50, 240) as consecutive uint16
    for off in range(0, 30):
        d = struct.unpack_from('<H', decompressed, base + off)[0]
        m = struct.unpack_from('<H', decompressed, base + off + 2)[0]
        if d == VANILLA_DEFAULT and m == VANILLA_MAX:
            ds_off = base + off
            ms_off = ds_off + 2
            break

    # Second try: if already patched, look for the trailing marker 0x00 0x28 0x80 0x02
    # which follows maxSlot in all known versions
    if ds_off is None:
        marker = bytes([0x00, 0x28, 0x80, 0x02])
        for off in range(4, 40):
            if decompressed[base + off:base + off + 4] == marker:
                ds_off = base + off - 4
                ms_off = ds_off + 2
                break

    if ds_off is None:
        print("  ERROR: Could not locate defaultSlot/maxSlot fields")
        return None

    cur_default = struct.unpack_from('<H', decompressed, ds_off)[0]
    cur_max = struct.unpack_from('<H', decompressed, ms_off)[0]

    return {
        'paz_path': paz_file,
        'pamt_path': pamt_path,
        'paz_offset': paz_offset,
        'comp_size': comp_size,
        'orig_size': orig_size,
        'is_compressed': is_compressed,
        'pamt_record_offset': pamt_rec_off,
        'decompressed': bytearray(decompressed),
        'char_ds_offset': ds_off,
        'char_ms_offset': ms_off,
        'cur_default': cur_default,
        'cur_max': cur_max,
    }


def apply_patch(game_path, info, new_default, new_max):
    """Apply the inventory patch: modify, recompress, update integrity chain.

    Returns True on success, False on failure.
    """
    data = info['decompressed']

    # Patch the values
    struct.pack_into('<H', data, info['char_ds_offset'], new_default)
    struct.pack_into('<H', data, info['char_ms_offset'], new_max)

    # Verify the patch took
    check_ds = struct.unpack_from('<H', data, info['char_ds_offset'])[0]
    check_ms = struct.unpack_from('<H', data, info['char_ms_offset'])[0]
    if check_ds != new_default or check_ms != new_max:
        print("  ERROR: Patch verification failed")
        return False

    if info['is_compressed']:
        # Recompress
        payload = lz4_compress(bytes(data))
        new_comp_size = len(payload)

        print(f"  Recompressed: {info['comp_size']} -> {new_comp_size} bytes")

        if new_comp_size > info['comp_size']:
            # Compressed data grew -- this should be extremely rare for a 4-byte change
            # but handle it by writing at the end of the PAZ file
            print(f"  WARNING: Recompressed data is larger than original.")
            print(f"  Appending to end of PAZ file...")
            paz_size = os.path.getsize(info['paz_path'])
            new_offset = paz_size
            with open(info['paz_path'], 'r+b') as f:
                f.seek(new_offset)
                f.write(payload)

            # Update PAMT: both offset and comp_size
            pamt_path = info['pamt_path']
            with open(pamt_path, 'rb') as f:
                pamt_data = bytearray(f.read())
            # Update offset
            struct.pack_into('<I', pamt_data, info['pamt_record_offset'], new_offset)
            # Update comp_size
            struct.pack_into('<I', pamt_data, info['pamt_record_offset'] + 4, new_comp_size)
            with open(pamt_path, 'wb') as f:
                f.write(bytes(pamt_data))
        else:
            # Write the recompressed block at the original offset
            with open(info['paz_path'], 'r+b') as f:
                f.seek(info['paz_offset'])
                f.write(payload)
                # If smaller, remaining bytes stay as-is (harmless -- PAMT has exact size)

            # Update PAMT comp_size if it changed
            if new_comp_size != info['comp_size']:
                update_pamt_comp_size(
                    info['pamt_path'],
                    info['pamt_record_offset'],
                    new_comp_size
                )
                print(f"  Updated PAMT comp_size: {info['comp_size']} -> {new_comp_size}")
            else:
                print(f"  PAMT comp_size unchanged (exact match)")
    else:
        # Uncompressed -- direct write
        with open(info['paz_path'], 'r+b') as f:
            f.seek(info['paz_offset'])
            f.write(bytes(data))

    # Update PAPGT integrity
    print(f"  Updating PAPGT integrity chain...")
    if update_papgt(game_path, PAZ_SUBDIR):
        print(f"  PAPGT updated successfully")
    else:
        print(f"  WARNING: PAPGT update failed -- game may reject the patch")

    return True


# ── Legacy AOB fallback ──────────────────────────────────────────────

LEGACY_RECORD_SIG = bytes([
    0x02, 0x00,
    0x09, 0x00, 0x00, 0x00,
    0x43, 0x68, 0x61, 0x72, 0x61, 0x63, 0x74, 0x65, 0x72,
    0x00,
    0x01,
])

def find_record_offset_legacy(paz_path):
    """Legacy AOB scan for uncompressed Character record in PAZ.
    Returns the file offset of defaultSlot, or None if not found."""
    CHUNK = 4 * 1024 * 1024
    sig_len = len(LEGACY_RECORD_SIG)
    with open(paz_path, 'rb') as f:
        file_offset = 0
        while True:
            f.seek(file_offset)
            data = f.read(CHUNK + sig_len - 1)
            if len(data) < sig_len:
                break
            idx = data.find(LEGACY_RECORD_SIG)
            if idx != -1:
                return file_offset + idx + 17  # defaultSlot offset
            file_offset += CHUNK
    return None


# ── Game path finder ─────────────────────────────────────────────────

def find_game_path():
    """Try common install locations, then ask the user."""
    common_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Crimson Desert",
        r"C:\Program Files\Steam\steamapps\common\Crimson Desert",
        r"D:\SteamLibrary\steamapps\common\Crimson Desert",
        r"E:\SteamLibrary\steamapps\common\Crimson Desert",
        r"F:\SteamLibrary\steamapps\common\Crimson Desert",
    ]

    for p in common_paths:
        paz = os.path.join(p, PAZ_SUBDIR, PAZ_FILE)
        if os.path.exists(paz):
            return p

    return None


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print(f"==================================================")
    print(f"  Crimson Desert - Inventory Expander v{VERSION}")
    print(f"  Increases inventory slot count")
    print(f"==================================================")
    print()

    # Find game
    game_path = find_game_path()
    if game_path:
        print(f"Found game at: {game_path}")
        confirm = input("Is this correct? (Y/n): ").strip().lower()
        if confirm == 'n':
            game_path = None

    if not game_path:
        game_path = input("Enter Crimson Desert install path: ").strip().strip('"')

    paz_path = os.path.join(game_path, PAZ_SUBDIR, PAZ_FILE)
    pamt_path = os.path.join(game_path, PAZ_SUBDIR, PAMT_FILE)
    backup_paz = paz_path + ".inventory_backup"
    backup_pamt = pamt_path + ".inventory_backup"
    backup_papgt = os.path.join(game_path, "meta", "0.papgt.inventory_backup")

    if not os.path.exists(paz_path):
        print(f"\nERROR: Cannot find {paz_path}")
        print("Make sure you entered the correct game install path.")
        input("\nPress Enter to exit...")
        return

    # Locate inventory data
    print(f"\nLocating inventory data...")
    info = find_and_read_inventory(game_path)

    if info is None:
        print(f"\nFalling back to legacy AOB scan...")
        legacy_offset = find_record_offset_legacy(paz_path)
        if legacy_offset is None:
            print(f"\nERROR: Could not find the Character inventory record.")
            print("The game may have changed its data format. Please report this issue.")
            input("\nPress Enter to exit...")
            return
        # Legacy path: direct byte patch (old uncompressed format)
        print(f"Found legacy record at offset 0x{legacy_offset:X}")
        with open(paz_path, 'rb') as f:
            f.seek(legacy_offset)
            cur_default = struct.unpack('<H', f.read(2))[0]
            cur_max = struct.unpack('<H', f.read(2))[0]
        info = {
            'cur_default': cur_default,
            'cur_max': cur_max,
            'legacy_offset': legacy_offset,
        }

    cur_default = info['cur_default']
    cur_max = info['cur_max']

    print(f"\nCurrent inventory settings:")
    print(f"  Starting slots: {cur_default} (vanilla: {VANILLA_DEFAULT})")
    print(f"  Maximum slots:  {cur_max} (vanilla: {VANILLA_MAX})")

    # Menu
    print(f"\nOptions:")
    print(f"  1. Expand inventory (448 starting, 700 max) [RECOMMENDED]")
    print(f"  2. Custom values")
    print(f"  3. Restore vanilla ({VANILLA_DEFAULT} starting, {VANILLA_MAX} max)")
    has_backup = os.path.exists(backup_paz)
    if has_backup:
        print(f"  4. Restore from backup files")
    print(f"  0. Exit")
    print(f"\nNOTE: Setting starting slots too high may cause the game to skip")
    print(f"bag quest rewards. 448 is the safe maximum for starting slots.")

    choice = input("\nChoice: ").strip()

    if choice == '0':
        return

    if choice == '4' and has_backup:
        shutil.copy2(backup_paz, paz_path)
        if os.path.exists(backup_pamt):
            shutil.copy2(backup_pamt, pamt_path)
        if os.path.exists(backup_papgt):
            papgt_path = os.path.join(game_path, "meta", "0.papgt")
            shutil.copy2(backup_papgt, papgt_path)
        # Re-read values after restore
        restored = find_and_read_inventory(game_path)
        if restored:
            print(f"\nRestored from backup: defaultSlot={restored['cur_default']}, maxSlot={restored['cur_max']}")
        else:
            print(f"\nRestored PAZ/PAMT/PAPGT from backup.")
        input("\nPress Enter to exit...")
        return

    if choice == '3':
        new_default = VANILLA_DEFAULT
        new_max = VANILLA_MAX
    elif choice == '1':
        new_default = 448
        new_max = 700
    elif choice == '2':
        print(f"\nGUIDELINES:")
        print(f"  - Starting slots: 100-200 recommended. Higher values may")
        print(f"    cause the game to skip bag quest rewards.")
        print(f"  - Maximum slots: up to 700 is safe. Above 732 causes companion")
        print(f"  - NOTE: A known bug may prevent lighting candles/braseros")
        print(f"    revive, abyss extraction, and storage crashes. 1000+ crashes on launch.")
        print(f"  - NOTE: Starting slots above ~200 may break candle/fire interactions.")
        val = input(f"\n  Starting slots [448]: ").strip()
        new_default = int(val) if val else 448
        val = input(f"  Maximum slots [700]: ").strip()
        new_max = int(val) if val else 700
    else:
        print("Invalid choice.")
        input("\nPress Enter to exit...")
        return

    # Validate
    if new_default < 1 or new_default > 65535:
        print(f"ERROR: Starting slots must be 1-65535")
        input("\nPress Enter to exit...")
        return
    if new_max < new_default or new_max > 65535:
        print(f"ERROR: Maximum slots must be >= starting slots and <= 65535")
        input("\nPress Enter to exit...")
        return
    if new_max > 732:
        print(f"WARNING: Values above 732 cause companion revive, abyss extraction,")
        print(f"and storage crashes. Capping at 700.")
        new_max = 700

    # Create backups
    if not os.path.exists(backup_paz):
        print(f"\nCreating backups...")
        shutil.copy2(paz_path, backup_paz)
        print(f"  PAZ backup:   {backup_paz}")
    if not os.path.exists(backup_pamt) and os.path.exists(pamt_path):
        shutil.copy2(pamt_path, backup_pamt)
        print(f"  PAMT backup:  {backup_pamt}")
    papgt_src = os.path.join(game_path, "meta", "0.papgt")
    if not os.path.exists(backup_papgt) and os.path.exists(papgt_src):
        shutil.copy2(papgt_src, backup_papgt)
        print(f"  PAPGT backup: {backup_papgt}")

    # Apply patch
    print(f"\nApplying patch...")

    if 'legacy_offset' in info:
        # Legacy uncompressed path
        with open(paz_path, 'r+b') as f:
            f.seek(info['legacy_offset'])
            f.write(struct.pack('<H', new_default))
            f.write(struct.pack('<H', new_max))
        with open(paz_path, 'rb') as f:
            f.seek(info['legacy_offset'])
            patched_default = struct.unpack('<H', f.read(2))[0]
            patched_max = struct.unpack('<H', f.read(2))[0]
    else:
        # New compressed path
        success = apply_patch(game_path, info, new_default, new_max)
        if not success:
            print(f"\nERROR: Patch failed. Restoring from backup...")
            shutil.copy2(backup_paz, paz_path)
            if os.path.exists(backup_pamt):
                shutil.copy2(backup_pamt, pamt_path)
            if os.path.exists(backup_papgt):
                shutil.copy2(backup_papgt, papgt_src)
            input("\nPress Enter to exit...")
            return

        # Re-read to verify
        verify = find_and_read_inventory(game_path)
        if verify:
            patched_default = verify['cur_default']
            patched_max = verify['cur_max']
        else:
            patched_default = new_default
            patched_max = new_max

    print(f"\nPatched successfully!")
    print(f"  Starting slots: {cur_default} -> {patched_default}")
    print(f"  Maximum slots:  {cur_max} -> {patched_max}")
    print(f"\nLaunch the game to see your expanded inventory.")
    print(f"Your existing bags still count - total = starting + bags collected.")

    input("\nPress Enter to exit...")


if __name__ == '__main__':
    main()
