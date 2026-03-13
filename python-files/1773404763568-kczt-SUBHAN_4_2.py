"""
PAK File Manager - Enhanced with All Features from SEN_4_2.py
Includes: Chunk Repack, Auto 120FPS, Antireset, Compare DAT, Search
"""

import os
import itertools as it
# Compatibility fix for Python versions older than 3.12
if not hasattr(it, 'batched'):
    def batched(iterable, n):
        import itertools
        if n < 1:
            raise ValueError('n must be at least one')
        it_obj = iter(iterable)
        while batch := tuple(itertools.islice(it_obj, n)):
            yield batch
    it.batched = batched

import math
import struct
import zlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePath, Path
import gmalg
from Crypto.Cipher import AES
from Crypto.Cipher.AES import MODE_CBC
from Crypto.Hash import SHA1
from Crypto.Util.Padding import unpad, pad
from zstandard import ZstdDecompressor, ZstdCompressor, ZstdCompressionDict, DICT_TYPE_AUTO
import const
import sys
import subprocess
import platform
import hashlib
import base64
import requests
import json
from datetime import datetime
import shutil
import traceback
import re
import uuid

# Get Termux device model
device_model = subprocess.getoutput("getprop ro.product.model").strip()

# Initialize colorama for Windows color support
try:
    import colorama
    colorama.init(autoreset=True)
except ImportError:
    pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn, TimeRemainingColumn
from rich import box
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt

console = Console()
from sm4_variant import SM4
import pyfiglet

# ------------------ KEY SYSTEM IMPORTS ------------------
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# -------------------------------------------------------

# ------------------ BANNER ------------------
def show_banner():
    banner_text = pyfiglet.figlet_format("SUBHAN", font="slant")
    console.print(Panel(Text(banner_text, justify="center", style="bold cyan"), title="Welcome", subtitle="Tool 4.2"))

# ------------------ KEY VERIFICATION FUNCTION ------------------
def verify_key():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("keys").sheet1
    except Exception as e:
        console.print(f"[bold red]Error accessing Google Sheet:[/bold red] {e}")
        return False

    user_key = Prompt.ask("Enter your key").strip()
    data = sheet.get_all_records()

    current_model = subprocess.getoutput("getprop ro.product.model").strip()
    console.print(f"[bold yellow]Detected device model:[/bold yellow] {current_model}")

    for row in data:
        if row.get("Key", "").strip() == user_key:
            # Check expiry
            try:
                expiry_date = datetime.strptime(row.get("Expiry", ""), "%Y-%m-%d")
            except:
                console.print("[bold red]❌ Invalid expiry format in Google Sheet![/bold red]")
                return False

            if datetime.now() > expiry_date:
                console.print("[bold red]❌ Key expired![/bold red]")
                return False

            # Check device model
            allowed_model = row.get("DeviceModel", "").strip()
            if allowed_model.upper() != "ANY" and allowed_model != current_model:
                console.print(f"[bold red]❌ Device mismatch! This key is not for this device ({current_model}).[/bold red]")
                return False

            console.print("[bold green]✅ Key verified! Access granted.[/bold green]")
            return True

    console.print("[bold red]❌ Invalid key![/bold red]")
    return False
# -------------------------------------------------------

# ------------------ RUN TOOL ------------------
if __name__ == "__main__":
    show_banner()
    if not verify_key():
        sys.exit("[bold red]Exiting tool. Invalid or expired key.[/bold red]")

    # ------------------ TOOL MAIN CODE ------------------
    console.print(Panel("[bold green]SUBHAN_4_2 Tool Running...[/bold green]", style="bold green"))
    # Your main tool code goes here

# ==================== TOOL CONFIGURATION ====================
TOOL_NAME = "SUBHAN PAK MANAGER"
BASE_DIR = Path(__file__).resolve().parent

# Folder structure with all types
FOLDER_STRUCTURE = {
    'ZSDIC': ['INPUT', 'REPACKED', 'EDITED', 'UNPACKED', 'SEARCH_RESULTS', 'COMPARE_DAT'],
    'MINI_OBB': ['INPUT', 'REPACKED', 'EDITED', 'UNPACKED', 'SEARCH_RESULTS', 'COMPARE_DAT'],
    'OD_PAK': ['INPUT', 'REPACKED', 'EDITED', 'UNPACKED', 'SEARCH_RESULTS', 'COMPARE_DAT'],
    'GAMEPATCH': ['INPUT', 'REPACKED', 'EDITED', 'UNPACKED', 'SEARCH_RESULTS', 'COMPARE_DAT'],
    'ANTIRESET': ['ORG_OBB', 'MODDED_OBB']
}

# Auto-scan configuration
AUTO_SCAN_EXTENSIONS = ['.uasset', '.uexp']
AUTO_SCAN_ENABLED = True

# ==================== MISC CLASSES ====================
class Misc:
    @staticmethod
    def pad_to_n(data: bytes, n: int) -> bytes:
        assert n > 0
        padding = n - len(data) % n
        if padding == n:
            return data
        else:
            return data + b'\x00' * padding
    @staticmethod
    def align_up(x: int, n: int) -> int:
        return (x + n - 1) // n * n

class Reader:
    def __init__(self, buffer, cursor=0):
        self._buffer = buffer
        self._cursor = cursor
    def u1(self, move_cursor=True) -> int:
        return self.unpack('B', move_cursor=move_cursor)[0]
    def u4(self, move_cursor=True) -> int:
        return self.unpack('<I', move_cursor=move_cursor)[0]
    def u8(self, move_cursor=True) -> int:
        return self.unpack('<Q', move_cursor=move_cursor)[0]
    def i1(self, move_cursor=True) -> int:
        return self.unpack('b', move_cursor=move_cursor)[0]
    def i4(self, move_cursor=True) -> int:
        return self.unpack('<i', move_cursor=move_cursor)[0]
    def i8(self, move_cursor=True) -> int:
        return self.unpack('<q', move_cursor=move_cursor)[0]
    def s(self, n: int, move_cursor=True) -> bytes:
        return self.unpack(f'{n}s', move_cursor=move_cursor)[0]
    def unpack(self, f: str | bytes, offset=0, move_cursor=True):
        x = struct.unpack_from(f, self._buffer, self._cursor + offset)
        if move_cursor:
            self._cursor += struct.calcsize(f)
        return x
    def string(self, move_cursor=True) -> str:
        length = self.i4(move_cursor=move_cursor)
        if length == 0:
            return str()
        else:
            assert length > 0
            offset = 0 if move_cursor else 4
            return self.unpack(f'{length}s', offset=offset, move_cursor=move_cursor)[0].rstrip(b'\x00').decode()

class Writer:
    def __init__(self):
        self._buffer = bytearray()
    def u1(self, value: int) -> None:
        self.pack('B', value)
    def u4(self, value: int) -> None:
        self.pack('<I', value)
    def u8(self, value: int) -> None:
        self.pack('<Q', value)
    def i1(self, value: int) -> None:
        self.pack('b', value)
    def i4(self, value: int) -> None:
        self.pack('<i', value)
    def i8(self, value: int) -> None:
        self.pack('<q', value)
    def s(self, data: bytes) -> None:
        self._buffer.extend(data)
    def pack(self, f: str, *values) -> None:
        self._buffer.extend(struct.pack(f, *values))
    def string(self, text: str) -> None:
        encoded = text.encode() + b'\x00'
        self.i4(len(encoded))
        self.s(encoded)
    def get_buffer(self) -> bytes:
        return bytes(self._buffer)
    def size(self) -> int:
        return len(self._buffer)
    def align_to(self, alignment: int) -> None:
        current_size = len(self._buffer)
        padding = (alignment - current_size % alignment) % alignment
        if padding > 0:
            self._buffer.extend(b'\x00' * padding)

# ==================== AUTO-SCAN REPACK CLASS ====================
class AutoScanRepack:
    """Handles automatic scanning and repacking of uasset/uexp files"""
    
    def __init__(self, pak_obj, edited_folder, manifest_reader, logger):
        self.pak_obj = pak_obj
        self.edited_folder = Path(edited_folder)
        self.manifest_reader = manifest_reader
        self.logger = logger
        self.scanned_files = []
        self.work_items = []
        self.modified_targets = []
        
    def scan_for_modifications(self):
        """Scan edited folder for uasset/uexp files and match them with PAK entries"""
        console.print("\n🔍 AUTO-SCAN: Looking for modified uasset/uexp files...")
        
        # Find all uasset and uexp files in edited folder
        found_files = []
        for ext in AUTO_SCAN_EXTENSIONS:
            found_files.extend(self.edited_folder.rglob(f'*{ext}'))
        
        if not found_files:
            console.print("   ⚠️ No uasset or uexp files found in edited folder")
            return False
        
        console.print(f"   ✅ Found {len(found_files)} files to process:")
        
        # Group files by their relative path structure
        file_matches = []
        for mod_file in found_files:
            try:
                # Get relative path from edited folder
                rel_path = mod_file.relative_to(self.edited_folder)
                rel_path_str = str(rel_path).replace('\\', '/')
                
                # Try to find in manifest
                manifest_info = self.manifest_reader.find_file_info(rel_path_str, quiet_on_exact_match=True)
                
                if manifest_info:
                    # Found by exact path - great!
                    console.print(f"   📄 {rel_path_str} [green]✓ Path match[/green]")
                    
                    # Find the actual PAK entry
                    entry_found = False
                    for dp, df in self.pak_obj._index.items():
                        for fn, ent in df.items():
                            full_pak_path = str(dp / fn).replace('\\', '/')
                            if full_pak_path == rel_path_str:
                                file_matches.append((mod_file, dp / fn, ent, rel_path_str))
                                entry_found = True
                                break
                        if entry_found:
                            break
                    
                    if not entry_found:
                        console.print(f"      [yellow]⚠️ PAK entry not found[/yellow]")
                else:
                    # Try filename only match (with warning)
                    filename = mod_file.name
                    matches = []
                    for dp, df in self.pak_obj._index.items():
                        for fn, ent in df.items():
                            if fn == filename:
                                full_pak_path = dp / fn
                                matches.append((full_pak_path, ent))
                    
                    if matches:
                        if len(matches) > 1:
                            console.print(f"   📄 {rel_path_str} [yellow]⚠️ Multiple matches:[/yellow]")
                            for match_path, _ in matches[:3]:
                                console.print(f"      • {match_path}")
                            if len(matches) > 3:
                                console.print(f"      ... and {len(matches)-3} more")
                            console.print(f"      Using first match - check path if wrong")
                        else:
                            console.print(f"   📄 {rel_path_str} [yellow]⚠️ Filename match only[/yellow]")
                        
                        # Use first match
                        file_matches.append((mod_file, matches[0][0], matches[0][1], rel_path_str))
                    else:
                        console.print(f"   📄 {rel_path_str} [red]❌ No match found[/red]")
                        
            except Exception as e:
                console.print(f"   ❌ Error processing {mod_file.name}: {e}")
        
        self.scanned_files = file_matches
        console.print(f"\n📊 Auto-scan complete: {len(self.scanned_files)} files matched for repacking")
        return len(self.scanned_files) > 0
    
    def process_files(self):
        """Process all scanned files through the repack system"""
        if not self.scanned_files:
            return False
        
        console.print("\n🔄 Auto-repack: Processing matched files...")
        
        for mod_file, pak_path, entry, rel_path in self.scanned_files:
            try:
                # Skip if encryption method 17 (unsupported)
                if entry.encrypted and entry.encryption_method == 17:
                    console.print(f"   ⚠️ Skipping {mod_file.name} - EM_UNKNOWN_17 (unsupported)")
                    self.logger.log_failure(rel_path, 'Unsupported encryption (EM_UNKNOWN_17)', {})
                    continue
                
                console.print(f"\n📦 Processing: {rel_path}")
                
                # Read the modified file
                mod_bytes = mod_file.read_bytes()
                console.print(f"   📊 Size: {len(mod_bytes):,} bytes (original: {entry.uncompressed_size:,} bytes)")
                
                # Size validation
                if len(mod_bytes) > entry.uncompressed_size * 1.5:  # 50% larger warning
                    console.print(f"   [yellow]⚠️ Warning: Modified file is significantly larger ({len(mod_bytes)/entry.uncompressed_size:.1f}x original)[/yellow]")
                
                # Create block logger for this file
                block_logger = BlockLogger(mod_file.name)
                
                # Process based on block structure
                if not entry.compressed_blocks:
                    # Uncompressed file
                    success = self._process_uncompressed(mod_file, pak_path, entry, mod_bytes, block_logger, rel_path)
                elif len(entry.compressed_blocks) == 1:
                    # Single block file
                    success = self._process_single_block(mod_file, pak_path, entry, mod_bytes, block_logger, rel_path)
                else:
                    # Multi-block file
                    success = self._process_multi_block(mod_file, pak_path, entry, mod_bytes, block_logger, rel_path)
                
                if success:
                    block_logger.print_summary()
                    self.logger.log_success(rel_path, entry.size, entry.size)
                else:
                    self.logger.log_failure(rel_path, 'Repack failed', {'size': len(mod_bytes)})
                    
            except Exception as e:
                console.print(f"   ❌ Error processing {mod_file.name}: {e}")
                self.logger.log_failure(rel_path, f'Exception: {str(e)}', {})
        
        return len(self.work_items) > 0
    
    def _process_uncompressed(self, mod_file, pak_path, entry, mod_bytes, block_logger, rel_path):
        """Process uncompressed file"""
        slot = entry.size
        console.print(f"   📦 Uncompressed slot: {slot:,} bytes")
        
        if len(mod_bytes) > slot:
            console.print(f"   ❌ Mod too large: {len(mod_bytes):,} > {slot:,}")
            return False
        
        result = mod_bytes
        encryption_method = entry.encryption_method if entry.encrypted else 0
        
        if entry.encrypted:
            cipher_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
            if len(result) > cipher_slot:
                raise ValueError(f'Entry data {len(result)} does not fit cipher slot {cipher_slot}')
            padded_plain = result + b'\x00' * (cipher_slot - len(result))
            cipher = PakCrypto.encrypt_block(padded_plain, pak_path, encryption_method)
            if len(cipher) != cipher_slot:
                raise ValueError(f'Encrypted entry size mismatch: got {len(cipher)} bytes, expected {cipher_slot}')
            result = cipher + b'\x00' * (slot - cipher_slot)
        
        block_logger.add_block(0, len(mod_bytes), len(result), 'NONE', -1, True, entry.offset, entry.offset + slot)
        self.work_items.append((pak_path, [(entry.offset, result)], False))
        self.modified_targets.append((pak_path, entry))
        return True
    
    def _process_single_block(self, mod_file, pak_path, entry, mod_bytes, block_logger, rel_path):
        """Process single-block compressed file"""
        block = entry.compressed_blocks[0]
        slot = block.end - block.start
        compression_method = entry.compression_method
        encryption_method = entry.encryption_method if entry.encrypted else 0
        
        comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')
        
        console.print(f"   📦 Single block slot: {slot:,} bytes")
        console.print(f"   🔧 Compression: {comp_method_str}")
        
        # Try to reuse original if unchanged
        try:
            orig_raw = self.pak_obj._peek_block_content(block, encryption_method)
            if entry.encrypted:
                orig_comp = PakCrypto.decrypt_block(orig_raw, pak_path, encryption_method)
            else:
                orig_comp = orig_raw
            
            orig_plain = PakCompression.decompress_block(orig_comp, self.pak_obj._zstd_dict, compression_method)
            
            if orig_plain == mod_bytes:
                console.print(f"   ♻️ File unchanged - reusing original")
                result = bytes(orig_raw)
                block_logger.add_block(0, len(mod_bytes), len(result), comp_method_str + " (REUSED)", -1, True, block.start, block.end)
                
                if entry.encrypted and len(result) != slot:
                    raise ValueError(f'Reused block size mismatch: {len(result)} != {slot}')
                
                self.work_items.append((pak_path, [(block.start, result)], False))
                self.modified_targets.append((pak_path, entry))
                return True
        except Exception as e:
            console.print(f"   ⚠️ Reuse check failed: {e}")
        
        # Need to compress
        usable_slot = slot
        if entry.encrypted:
            usable_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
        
        # Try compression levels
        result, level_used = self._try_compression(mod_bytes, compression_method, usable_slot, self.pak_obj._zstd_dict)
        
        if result is None:
            console.print(f"   ❌ Failed to fit in {slot} bytes")
            return False
        
        compressed_size_for_log = len(result)
        
        # Handle encryption
        if entry.encrypted:
            cipher_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
            if len(result) > cipher_slot:
                raise ValueError(f'Compressed data {len(result)} does not fit cipher slot {cipher_slot}')
            padded_plain = result + b'\x00' * (cipher_slot - len(result))
            cipher = PakCrypto.encrypt_block(padded_plain, pak_path, encryption_method)
            if len(cipher) != cipher_slot:
                raise ValueError(f'Encrypted block size mismatch: got {len(cipher)} bytes, expected {cipher_slot}')
            result = cipher + b'\x00' * (slot - cipher_slot)
        else:
            result = result + b'\x00' * (slot - len(result))
        
        block_logger.add_block(0, len(mod_bytes), compressed_size_for_log, comp_method_str, level_used, True, block.start, block.end)
        self.work_items.append((pak_path, [(block.start, result)], False))
        self.modified_targets.append((pak_path, entry))
        return True
    
    def _process_multi_block(self, mod_file, pak_path, entry, mod_bytes, block_logger, rel_path):
        """Process multi-block compressed file"""
        blocks = entry.compressed_blocks
        compression_method = entry.compression_method
        encryption_method = entry.encryption_method if entry.encrypted else 0
        block_size = entry.compression_block_size
        
        comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')
        
        total_slot = sum((b.end - b.start for b in blocks))
        console.print(f"   📦 Multi-block: {len(blocks)} blocks, total slot: {total_slot:,} bytes")
        
        # Split into chunks
        chunks = list(it.batched(mod_bytes, block_size))
        chunks = [bytes(chunk) if isinstance(chunk, tuple) else chunk for chunk in chunks]
        
        if len(chunks) > len(blocks):
            console.print(f"   ❌ Too many chunks: {len(chunks)} > {len(blocks)} blocks")
            return False
        
        # Get block permutation
        block_indices = PakCrypto.generate_block_indices(len(blocks), encryption_method)
        
        # Check for unchanged blocks
        block_reuse = {}
        try:
            # Try to find original file for comparison
            original_file_path = self.edited_folder.parent / str(rel_path)
            if original_file_path.exists():
                orig_data = original_file_path.read_bytes()
                orig_chunks = list(it.batched(orig_data, block_size))
                orig_chunks = [bytes(c) if isinstance(c, tuple) else c for c in orig_chunks]
                
                for idx, chunk in enumerate(chunks):
                    if idx < len(orig_chunks) and chunk == orig_chunks[idx]:
                        stored_idx = block_indices[idx] if idx < len(block_indices) else idx
                        block = blocks[stored_idx]
                        orig_raw = self.pak_obj._peek_block_content(block, encryption_method)
                        block_reuse[idx] = (True, bytes(orig_raw))
                        console.print(f"      Block {idx}: ♻️ Unchanged - reusing")
                    else:
                        block_reuse[idx] = (False, None)
                        console.print(f"      Block {idx}: 🔧 Modified - recompressing")
            else:
                # No original for comparison, assume all modified
                for idx in range(len(chunks)):
                    block_reuse[idx] = (False, None)
                console.print(f"      No original file for comparison, recompressing all blocks")
        except Exception as e:
            console.print(f"   ⚠️ Block reuse check failed: {e}")
            for idx in range(len(chunks)):
                block_reuse[idx] = (False, None)
        
        # Process each block
        compressed_chunks = []
        all_fit = True
        
        for idx, chunk in enumerate(chunks):
            stored_idx = block_indices[idx] if idx < len(block_indices) else idx
            block = blocks[stored_idx]
            slot = block.end - block.start
            usable_slot = slot
            if entry.encrypted:
                usable_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
            
            # Check if we can reuse
            if idx in block_reuse and block_reuse[idx][0]:
                result = block_reuse[idx][1]
                console.print(f"      Block {idx}: Using original ({len(result):,} bytes)")
                block_logger.add_block(idx, len(chunk), len(result), comp_method_str + " (REUSED)", -1, True, block.start, block.end)
                compressed_chunks.append((block.start, result))
                continue
            
            # Need to compress
            console.print(f"      Block {idx}: Compressing {len(chunk):,} bytes to fit {slot:,} slot...")
            
            result, level_used = self._try_compression(chunk, compression_method, usable_slot, self.pak_obj._zstd_dict)
            
            if result is None:
                console.print(f"         ❌ Failed to fit in {slot} bytes")
                all_fit = False
                block_logger.add_block(idx, len(chunk), len(chunk), comp_method_str, -1, False, block.start, block.end)
                break
            
            compressed_size_for_log = len(result)
            
            # Handle encryption
            if entry.encrypted:
                if PakCrypto.align_encrypted_content_size(slot, encryption_method) != slot:
                    raise ValueError(f'Block slot size {slot} not aligned')
                padded_plain = result + b'\x00' * (slot - len(result))
                result = PakCrypto.encrypt_block(padded_plain, pak_path, encryption_method)
                if len(result) != slot:
                    raise ValueError(f'Encrypted block size mismatch: {len(result)} != {slot}')
            else:
                result = result + b'\x00' * (slot - len(result))
            
            slot_usage = (compressed_size_for_log / slot) * 100
            console.print(f"         ✅ Compressed to {compressed_size_for_log:,} bytes ({slot_usage:.1f}% of slot)")
            
            block_logger.add_block(idx, len(chunk), compressed_size_for_log, comp_method_str, level_used, True, block.start, block.end)
            compressed_chunks.append((block.start, result))
        
        if all_fit:
            self.work_items.append((pak_path, compressed_chunks, True))
            self.modified_targets.append((pak_path, entry))
            return True
        else:
            return False
    
    def _try_compression(self, data, compression_method, target_size, zstd_dict=None):
        """Try compression levels to find one that fits target size"""
        if compression_method == const.CM_NONE:
            if len(data) <= target_size:
                return data, -1
            return None, -1
        
        # Determine max level
        if compression_method == const.CM_ZLIB:
            max_level = 9
            level_step = 1
        elif compression_method in [const.CM_ZSTD, const.CM_ZSTD_DICT]:
            max_level = 22
            level_step = 1
        else:
            return None, -1
        
        best_compressed = None
        best_size = float('inf')
        best_level = -1
        
        for lvl in range(max_level, 0, -level_step):
            try:
                if compression_method == const.CM_ZLIB:
                    actual_level = min(lvl, 9)
                    comp = zlib.compress(data, level=actual_level)
                elif compression_method == const.CM_ZSTD:
                    comp = ZstdCompressor(level=lvl).compress(data)
                elif compression_method == const.CM_ZSTD_DICT and zstd_dict:
                    comp = ZstdCompressor(level=lvl, dict_data=zstd_dict).compress(data)
                else:
                    continue
                
                if comp and len(comp) < best_size:
                    best_size = len(comp)
                    best_compressed = comp
                    best_level = lvl
                
                if comp and len(comp) <= target_size:
                    return comp, lvl
                    
            except Exception:
                continue
        
        if best_compressed and best_size <= target_size:
            return best_compressed, best_level
        
        return None, -1
    
    def get_results(self):
        """Return work items and modified targets"""
        return self.work_items, self.modified_targets

# ==================== BLOCK LOGGER ====================
class BlockLogger:
    """Detailed logging for each compression block"""
    def __init__(self, filename: str):
        self.filename = filename
        self.blocks = []
        self.original_total_size = 0
        self.compressed_total_size = 0
        
    def add_block(self, block_index: int, original_size: int, compressed_size: int, 
                  compression_method: str, level: int, success: bool, 
                  block_offset: int, block_end: int):
        block_data = {
            'index': block_index,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compressed_size / original_size if original_size > 0 else 0,
            'savings_percent': (1 - (compressed_size / original_size)) * 100 if original_size > 0 else 0,
            'compression_method': compression_method,
            'level': level,
            'success': success,
            'block_offset': block_offset,
            'block_end': block_end,
            'slot_size': block_end - block_offset,
            'utilization': (compressed_size / (block_end - block_offset)) * 100 if (block_end - block_offset) > 0 else 0
        }
        self.blocks.append(block_data)
        self.original_total_size += original_size
        self.compressed_total_size += compressed_size
        
    def print_summary(self):
        table = Table(title=f"📊 Block Compression Summary: {self.filename}", show_header=True, header_style="bold magenta")
        table.add_column("Block", style="cyan", width=6)
        table.add_column("Original", justify="right", width=12)
        table.add_column("Compressed", justify="right", width=12)
        table.add_column("Slot Size", justify="right", width=12)
        table.add_column("Free", justify="right", width=10)
        table.add_column("Method", width=12)
        table.add_column("Lvl", justify="center", width=5)
        table.add_column("Status", width=8)
        
        for block in self.blocks:
            status = "✅" if block['success'] else "❌"
            slot_size = block['slot_size']
            compressed = block['compressed_size']
            
            # FIXED: Free space should be: slot - compressed
            # Positive = space left, Negative = overflow
            free_space = slot_size - compressed
            
            # Handle REUSED in method name
            method = block['compression_method']
            level = str(block['level'] if block['level'] != -1 else "N/A")
            
            # Color code free space
            # Positive (green) = fits with room to spare
            # Near zero (yellow) = tight fit
            # Negative (red) = overflow, doesn't fit
            if free_space >= 0:
                free_str = f"[green]+{free_space:,}[/green]"
                if free_space < 100:
                    free_str = f"[yellow]+{free_space:,}[/yellow]"
            else:
                free_str = f"[red]{free_space:,}[/red]"  # Already has minus sign
            
            table.add_row(
                str(block['index']),
                f"{block['original_size']:,}",
                f"{compressed:,}",
                f"{slot_size:,}",
                free_str,
                method,
                level,
                status
            )
        
        console.print(table)
        
        # Overall summary
        overall_ratio = self.compressed_total_size / self.original_total_size if self.original_total_size > 0 else 0
        overall_savings = (1 - overall_ratio) * 100
        total_slot_size = sum(b['slot_size'] for b in self.blocks)
        total_free = total_slot_size - self.compressed_total_size
        
        console.print(f"\n📈 Overall Summary:")
        console.print(f"   Original Size: {self.original_total_size:,} bytes")
        console.print(f"   Compressed Size: {self.compressed_total_size:,} bytes")
        console.print(f"   Total Slot Size: {total_slot_size:,} bytes")
        console.print(f"   Free Space: {total_free:,} bytes ({(total_free/total_slot_size)*100:.1f}% unused)")
        console.print(f"   Compression Ratio: {overall_ratio:.3f} ({overall_savings:.1f}% savings)")
        console.print(f"   Total Blocks: {len(self.blocks)}")

# ==================== REPACK LOGGER ====================
class RepackLogger:
    """Logging for repack operations"""
    def __init__(self):
        self.successes = []
        self.failures = []
        
    def log_success(self, file_name: str, compressed_size: int, slot_size: int):
        self.successes.append({
            'file': file_name,
            'compressed': compressed_size,
            'slot': slot_size,
            'ratio': (compressed_size / slot_size) * 100 if slot_size > 0 else 0
        })
        
    def log_failure(self, file_name: str, reason: str, details: dict):
        self.failures.append({
            'file': file_name,
            'reason': reason,
            'details': details
        })
        
    def print_summary(self):
        if not self.successes and not self.failures:
            console.print("⚠️ No repack operations logged")
            return
        
        # Success table
        if self.successes:
            success_table = Table(title="✅ Successful Repacks", show_header=True, header_style="bold green")
            success_table.add_column("File", style="cyan")
            success_table.add_column("Compressed", justify="right")
            success_table.add_column("Slot", justify="right")
            success_table.add_column("Utilization", justify="right")
            
            for s in self.successes:
                success_table.add_row(
                    s['file'],
                    f"{s['compressed']:,}",
                    f"{s['slot']:,}",
                    f"{s['ratio']:.1f}%"
                )
            
            console.print(success_table)
        
        # Failure table
        if self.failures:
            failure_table = Table(title="❌ Failed Repacks", show_header=True, header_style="bold red")
            failure_table.add_column("File", style="cyan")
            failure_table.add_column("Reason", style="white")
            failure_table.add_column("Details", style="dim")
            
            for f in self.failures:
                details_str = ", ".join(f"{k}: {v}" for k, v in f['details'].items())
                failure_table.add_row(
                    f['file'],
                    f['reason'],
                    details_str if details_str else "-"
                )
            
            console.print(failure_table)
        
        # Overall panel
        total = len(self.successes) + len(self.failures)
        success_rate = (len(self.successes) / total * 100) if total > 0 else 0
        console.print(Panel(
            f"[green]Successes: {len(self.successes)}[/green]\n"
            f"[red]Failures: {len(self.failures)}[/red]\n"
            f"Success Rate: {success_rate:.1f}%",
            title="[bold]Repack Summary[/bold]"
        ))

# ==================== MANIFEST CLASSES ====================
class ManifestGenerator:
    """Generate manifest.json in real-time during unpack"""
    def __init__(self, pak_name: str, output_path=None):
        self.pak_name = pak_name
        self.output_path = output_path  # Real-time write location
        self.manifest = {
            'pak_file': pak_name,
            'created_at': datetime.now().isoformat(),
            'version': '3.0',  # UPDATED: Version bump for enhanced block tracking
            'total_files': 0,
            'total_blocks': 0,
            'compression_stats': {},
            'encryption_stats': {},
            'extraction_mode': 'full',
            'files': {},
            'block_files': {},  # Dictionary of block files keyed by extracted filename
            'block_file_mappings': {}  # NEW: Mapping from block filename to original file
        }
        
    def set_extraction_mode(self, use_block_splitting: bool):
        """Set whether blocks are being extracted separately"""
        self.manifest['extraction_mode'] = 'blocks' if use_block_splitting else 'full'
    
    def add_block_file_entry(self, original_file_path, block_index: int, block_size: int, entry):
        """Track individual block file entry (for block-based extraction)"""
        file_key = str(original_file_path).replace('\\', '/')
        
        # Create extracted filename (how it's actually saved on disk)
        filename = Path(original_file_path).name
        stem = Path(filename).stem
        ext = Path(filename).suffix
        extracted_filename = f"{stem}_block_{block_index}{ext}"
        
        # Map compression methods
        comp_names = {
            0: 'CM_NONE',
            1: 'CM_ZLIB',
            6: 'CM_ZSTD',
            8: 'CM_ZSTD_DICT'
        }
        
        compression_name = comp_names.get(entry.compression_method, f'UNKNOWN_{entry.compression_method}')
        
        # Store block file metadata with extracted filename as key
        block_entry = {
            'parent_file': file_key,
            'block_index': block_index,
            'block_size': block_size,
            'extracted_filename': extracted_filename,
            'original_filename': filename,
            'compression_method': entry.compression_method,
            'compression_method_name': compression_name,
            'encrypted': entry.encrypted,
            'encryption_method': entry.encryption_method if entry.encrypted else 0,
        }
        
        # Store in block_files dictionary with extracted filename as key
        self.manifest['block_files'][extracted_filename] = block_entry
        
        # Also store in mapping for quick lookup
        self.manifest['block_file_mappings'][extracted_filename] = file_key
        
        # Also keep track of parent file metadata
        if file_key not in self.manifest['files']:
            self.manifest['files'][file_key] = {
                'uncompressed_size': entry.uncompressed_size,
                'compression_method': entry.compression_method,
                'compression_method_name': compression_name,
                'num_blocks': 0,
                'extracted_as_blocks': True,
                'block_filenames': []  # List of block filenames
            }
            self.manifest['total_files'] += 1
        
        # Add block filename to parent's list
        self.manifest['files'][file_key]['block_filenames'].append(extracted_filename)
        
        # Increment block count
        self.manifest['files'][file_key]['num_blocks'] += 1
        
        if self.output_path:
            self._write_realtime()
        
    def add_file_entry(self, file_path, entry, actual_offset: int, actual_size: int):
        if entry.encrypted and entry.encryption_method == 17:
            return
            
        file_key = str(file_path).replace('\\', '/')
        
        # Map compression methods - From const.py
        comp_names = {
            0: 'CM_NONE',
            1: 'CM_ZLIB',
            6: 'CM_ZSTD',
            8: 'CM_ZSTD_DICT'
        }
        
        # Map encryption methods - From const.py (with SM4_NEW inference)
        enc_names = {
            1: 'EM_SIMPLE1',
            2: 'EM_SM4_2',
            4: 'EM_SM4_4',
            16: 'EM_SIMPLE2',
            17: 'EM_UNKNOWN_17',
            31: 'EM_SM4_NEW_31',
            32: 'EM_SM4_NEW_32',
            33: 'EM_SM4_NEW_33',
            34: 'EM_SM4_NEW_34',
            35: 'EM_SM4_NEW_35',
            36: 'EM_SM4_NEW_36',
            37: 'EM_SM4_NEW_37',
            38: 'EM_SM4_NEW_38',
            39: 'EM_SM4_NEW_39',
            40: 'EM_SM4_NEW_40',
            41: 'EM_SM4_NEW_41',
            42: 'EM_SM4_NEW_42',
            43: 'EM_SM4_NEW_43',
            44: 'EM_SM4_NEW_44',
            45: 'EM_SM4_NEW_45',
            0: 'NONE',
        }
        
        # Get encryption name
        if entry.encrypted:
            encryption_name = enc_names.get(entry.encryption_method, f'UNKNOWN_{entry.encryption_method}')
        else:
            encryption_name = 'NONE'
            
        # Get compression name
        compression_name = comp_names.get(entry.compression_method, f'UNKNOWN_{entry.compression_method}')
        
        # Build detailed block info
        block_info = []
        if hasattr(entry, 'compressed_blocks') and entry.compressed_blocks:
            for i, block in enumerate(entry.compressed_blocks):
                block_size = block.end - block.start
                block_info.append({
                    'index': i,
                    'start': block.start,
                    'end': block.end,
                    'size': block_size,
                    'offset_in_file': i * entry.compression_block_size if entry.compression_block_size > 0 else 0,
                    'max_size': entry.compression_block_size if entry.compression_block_size > 0 else block_size
                })
        
        file_entry = {
            'offset': actual_offset,
            'total_size': actual_size,
            'uncompressed_size': entry.uncompressed_size,
            'compression_method': entry.compression_method,
            'compression_method_name': compression_name,
            'compression_block_size': entry.compression_block_size,
            'encrypted': entry.encrypted,
            'encryption_method': entry.encryption_method if entry.encrypted else 0,
            'encryption_method_name': encryption_name,
            'blocks': block_info,
            'num_blocks': len(entry.compressed_blocks) if hasattr(entry, 'compressed_blocks') else 0,
            'content_hash': entry.content_hash.hex() if hasattr(entry, 'content_hash') and entry.content_hash else None,
            'unk1': entry.unk1 if hasattr(entry, 'unk1') else 0,
            'unk2': entry.unk2.hex() if hasattr(entry, 'unk2') and entry.unk2 else None
        }
        
        self.manifest['files'][file_key] = file_entry
        self.manifest['total_files'] += 1
        self.manifest['total_blocks'] += len(block_info)
        
        # Update compression stats
        comp_key = compression_name
        if comp_key not in self.manifest['compression_stats']:
            self.manifest['compression_stats'][comp_key] = 0
        self.manifest['compression_stats'][comp_key] += 1
        
        # Update encryption stats
        enc_key = encryption_name
        if enc_key not in self.manifest['encryption_stats']:
            self.manifest['encryption_stats'][enc_key] = 0
        self.manifest['encryption_stats'][enc_key] += 1
        
        # REAL-TIME: Write manifest immediately after each file
        if self.output_path:
            self._write_realtime()
    
    def _write_realtime(self):
        """Write manifest to disk in real-time (after each file)"""
        try:
            output_path = Path(self.output_path)
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            
            manifest_file = output_path / 'manifest.json'
            
            # Add summary stats
            self.manifest['summary'] = {
                'compression_distribution': self.manifest['compression_stats'],
                'encryption_distribution': self.manifest['encryption_stats'],
                'avg_blocks_per_file': self.manifest['total_blocks'] / self.manifest['total_files'] if self.manifest['total_files'] > 0 else 0
            }
            
            # Write to disk
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)
            
            # Show progress every 10 files
            if self.manifest['total_files'] % 10 == 0:
                print(f"[cyan]📋 Manifest updated: {self.manifest['total_files']} files")
        
        except Exception as e:
            print(f"[yellow]⚠️ Real-time manifest write error: {e}")
        
    def save(self, output_path):
        """Final save (manifest already written, just show summary)"""
        try:
            output_path = Path(output_path)
            
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            
            manifest_file = output_path / 'manifest.json'
            
            # Add summary stats
            self.manifest['summary'] = {
                'compression_distribution': self.manifest['compression_stats'],
                'encryption_distribution': self.manifest['encryption_stats'],
                'avg_blocks_per_file': self.manifest['total_blocks'] / self.manifest['total_files'] if self.manifest['total_files'] > 0 else 0
            }
            
            # Final write
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)
            
            # Print final summary
            console.print(Panel(
                f"[green]✅ Manifest Complete[/green]\n"
                f"• Location: {manifest_file}\n"
                f"• Files: {self.manifest['total_files']}\n"
                f"• Blocks: {self.manifest['total_blocks']}\n"
                f"• Compression: {', '.join(f'{k}:{v}' for k, v in self.manifest['compression_stats'].items())}\n"
                f"• Encryption: {', '.join(f'{k}:{v}' for k, v in self.manifest['encryption_stats'].items())}",
                title="[bold]Manifest Summary[/bold]"
            ))
            
            print(f"[green]✅ Manifest file verified at: {manifest_file}")
            return manifest_file
            
        except Exception as e:
            print(f"[red]❌ CRITICAL ERROR saving manifest:")
            print(f"[red]   {type(e).__name__}: {e}")
            traceback.print_exc()
            return None

class ManifestReader:
    """Read and use manifest data during repack"""
    def __init__(self, manifest_path):
        self.manifest_path = Path(manifest_path)
        self.manifest = {}
        self.extraction_mode = 'full'
        self.block_files = {}  # Dictionary of block files
        self.block_file_mappings = {}  # NEW: Mapping from block filename to original file
        self.load()
        
    def load(self):
        if not self.manifest_path.exists():
            raise FileNotFoundError(f'Manifest not found: {self.manifest_path}')
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            self.manifest = json.load(f)
        
        # Handle version 2.1 manifest (backward compatibility)
        manifest_version = self.manifest.get('version', '1.0')
        
        if manifest_version == '2.1':
            # Convert v2.1 format to v3.0 format
            self._convert_v21_to_v30()
        
        # Load extraction mode and block files
        self.extraction_mode = self.manifest.get('extraction_mode', 'full')
        self.block_files = self.manifest.get('block_files', {})
        self.block_file_mappings = self.manifest.get('block_file_mappings', {})
        
        # Show extraction mode info
        mode_display = "BLOCKS" if self.extraction_mode == 'blocks' else "FULL FILES"
        mode_color = "yellow" if self.extraction_mode == 'blocks' else "cyan"
        
        console.print(Panel(
            f"[green]📖 Manifest Loaded[/green]\n"
            f"• PAK: {self.manifest.get('pak_file', 'Unknown')}\n"
            f"• Files: {len(self.manifest.get('files', {}))}\n"
            f"• Version: {self.manifest.get('version', '1.0')}\n"
            f"• Extraction Mode: [{mode_color}]{mode_display}[/{mode_color}]",
            title="[bold]Repack Preparation[/bold]"
        ))
        
        # Show block mode warning
        if self.is_block_mode():
            block_count = len(self.block_files)
            console.print(f"[yellow]📦 Block mode detected - will reassemble {block_count} block files")
    
    def _convert_v21_to_v30(self):
        """Convert version 2.1 manifest format to version 3.0 format"""
        console.print("[yellow]⚠️ Converting manifest from v2.1 to v3.0 format...[/yellow]")
        
        # Create block_files dictionary if it doesn't exist
        if 'block_files' not in self.manifest:
            self.manifest['block_files'] = {}
        
        # Create block_file_mappings if it doesn't exist
        if 'block_file_mappings' not in self.manifest:
            self.manifest['block_file_mappings'] = {}
        
        # Process all files in the manifest
        for file_path, file_info in self.manifest.get('files', {}).items():
            if file_info.get('extracted_as_blocks'):
                block_filenames = file_info.get('block_files', [])
                
                for i, block_filename in enumerate(block_filenames):
                    # Create block entry
                    block_entry = {
                        'parent_file': file_path,
                        'block_index': i,
                        'block_size': 0,  # Size not stored in v2.1
                        'extracted_filename': block_filename,
                        'original_filename': Path(file_path).name,
                        'compression_method': file_info.get('compression_method', 0),
                        'compression_method_name': file_info.get('compression_method_name', 'UNKNOWN'),
                        'encrypted': file_info.get('encrypted', False),
                        'encryption_method': file_info.get('encryption_method', 0),
                    }
                    
                    # Add to block_files dictionary
                    self.manifest['block_files'][block_filename] = block_entry
                    
                    # Add to mappings
                    self.manifest['block_file_mappings'][block_filename] = file_path
        
        # Update version
        self.manifest['version'] = '3.0'
        console.print("[green]✅ Manifest converted to v3.0 format[/green]")
    
    def is_block_mode(self) -> bool:
        """Check if this manifest was created with block splitting"""
        return self.extraction_mode == 'blocks'
    
    def get_block_info_by_filename(self, block_filename: str):
        """Get block info for a specific block filename"""
        return self.block_files.get(block_filename)
    
    def get_original_file_for_block(self, block_filename: str):
        """Get original file path for a block filename"""
        return self.block_file_mappings.get(block_filename)
    
    def get_all_blocks_for_file(self, file_path: str):
        """Get all block entries for a given file"""
        normalized = file_path.replace('\\', '/')
        blocks = []
        
        for block_filename, block_info in self.block_files.items():
            if block_info.get('parent_file') == normalized:
                blocks.append(block_info)
        
        # Sort by block index
        blocks.sort(key=lambda x: x.get('block_index', 0))
        return blocks
        
    def find_file_info(self, file_path: str, quiet_on_exact_match=False):
        """Find file info by path (relative to mount point)
        
        Args:
            file_path: Path to search for
            quiet_on_exact_match: If True, don't print warnings when we have an exact match
        """
        # Try exact match first
        if file_path in self.manifest['files']:
            return self.manifest['files'][file_path]
        
        # Normalize path separators for comparison
        file_path_normalized = file_path.replace('\\', '/')
        for path in self.manifest['files']:
            if path.replace('\\', '/') == file_path_normalized:
                return self.manifest['files'][path]
        
        # Try filename only (least reliable, will return first match)
        filename = Path(file_path).name
        matches = []
        for path, info in self.manifest['files'].items():
            if Path(path).name == filename:
                matches.append((path, info))
        
        if len(matches) > 1 and not quiet_on_exact_match:
            console.print(f"[yellow]⚠️ Multiple manifest entries found for filename '{filename}':")
            for path, _ in matches:
                console.print(f"   • {path}")
            console.print(f"[yellow]   Using first match. Consider using full path for accuracy.")
        
        if matches:
            return matches[0][1]
        
        return None
    
    def get_file_blocks(self, file_path: str):
        """Get block information for a file"""
        info = self.find_file_info(file_path)
        if info and 'blocks' in info:
            return info['blocks']
        return []
    
    def print_file_details(self, file_path: str, quiet_on_exact_match=False):
        """Print detailed file information
        
        Args:
            file_path: Path to search for (can be full path or filename)
            quiet_on_exact_match: If True, don't print multiple match warnings when we have exact match
        """
        info = self.find_file_info(file_path, quiet_on_exact_match=quiet_on_exact_match)
        if not info:
            console.print(f"[yellow]⚠️ No manifest info for: {file_path}")
            return
        
        # Check if this was extracted as blocks
        if info.get('extracted_as_blocks'):
            blocks = self.get_all_blocks_for_file(file_path)
            console.print(f"[yellow]   📦 Extracted as {len(blocks)} block files")
            
            # Show expected block sizes
            if blocks:
                table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
                table.add_column("Block", width=6)
                table.add_column("Filename", width=30)
                table.add_column("Size", justify="right", width=12)
                
                for block in blocks:
                    table.add_row(
                        str(block['block_index']),
                        block.get('extracted_filename', 'unknown'),
                        f"{block.get('block_size', 0):,}"
                    )
                
                console.print(table)
            return
        
        # Normal file display
        table = Table(title=f"📋 Manifest Details: {Path(file_path).name}", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Compression", f"{info.get('compression_method_name', 'Unknown')} ({info.get('compression_method', 0)})")
        table.add_row("Encryption", f"{info.get('encryption_method_name', 'Unknown')} ({info.get('encryption_method', 0)})")
        table.add_row("Uncompressed Size", f"{info.get('uncompressed_size', 0):,} bytes")
        table.add_row("Total Size", f"{info.get('total_size', 0):,} bytes")
        table.add_row("Block Size", f"{info.get('compression_block_size', 0):,} bytes")
        table.add_row("Number of Blocks", str(info.get('num_blocks', 0)))
        
        if info.get('blocks'):
            table.add_row("Block Layout", f"{len(info['blocks'])} blocks, {sum(b['size'] for b in info['blocks']):,} total slot")
        
        console.print(table)
        
        # Print block details if available
        if info.get('blocks'):
            block_table = Table(title="Block Details", show_header=True)
            block_table.add_column("#", style="cyan", width=4)
            block_table.add_column("Start", justify="right", width=12)
            block_table.add_column("End", justify="right", width=12)
            block_table.add_column("Size", justify="right", width=12)
            block_table.add_column("Max", justify="right", width=12)
            
            for block in info['blocks']:
                block_table.add_row(
                    str(block['index']),
                    f"{block['start']:,}",
                    f"{block['end']:,}",
                    f"{block['size']:,}",
                    f"{block['max_size']:,}"
                )
            
            console.print(block_table)

# ==================== PAK STRUCTURE CLASSES ====================
class PakInfo:
    def __init__(self, buffer, keystream: list[int]):
        def decrypt_index_encrypted(x: int) -> int:
            MASK_8 = 255
            return (x ^ keystream[3]) & MASK_8
        def decrypt_magic(x: int) -> int:
            return x ^ keystream[2]
        def decrypt_index_hash(x: bytes) -> bytes:
            key = struct.pack('<5I', *keystream[4:][:5])
            assert len(x) == len(key)
            return bytes((a ^ b for a, b in zip(x, key)))
        def decrypt_index_size(x: int) -> int:
            return x ^ (keystream[10] << 32 | keystream[11])
        def decrypt_index_offset(x: int) -> int:
            return x ^ (keystream[0] << 32 | keystream[1])
        reader = Reader(buffer[-PakInfo._mem_size((-1)):])
        self.index_encrypted = decrypt_index_encrypted(reader.u1()) == 1
        self.magic = decrypt_magic(reader.u4())
        self.version = reader.u4()
        self.index_hash = decrypt_index_hash(reader.s(20)) if self.version >= 6 else bytes()
        self.index_size = decrypt_index_size(reader.u8())
        self.index_offset = decrypt_index_offset(reader.u8())
        if self.version <= 3:
            self.index_encrypted = False
    @staticmethod
    def _mem_size(_: int) -> int:
        return 45

class TencentPakInfo(PakInfo):
    def __init__(self, buffer, keystream: list[int]):
        def decrypt_unk(x: bytes) -> bytes:
            key = struct.pack('<8I', *keystream[7:][:8])
            assert len(x) == len(key)
            return bytes((a ^ b for a, b in zip(x, key)))
        def decrypt_stem_hash(x: int) -> int:
            return x ^ keystream[8]
        def decrypt_unk_hash(x: int) -> int:
            return x ^ keystream[9]
        super().__init__(buffer, keystream)
        reader = Reader(buffer[-TencentPakInfo._mem_size(self.version):])
        self.unk1 = decrypt_unk(reader.s(32)) if self.version >= 7 else bytes()
        self.packed_key = reader.s(256) if self.version >= 8 else bytes()
        self.packed_iv = reader.s(256) if self.version >= 8 else bytes()
        self.packed_index_hash = reader.s(256) if self.version >= 8 else bytes()
        self.stem_hash = decrypt_stem_hash(reader.u4()) if self.version >= 9 else 0
        self.unk2 = decrypt_unk_hash(reader.u4()) if self.version >= 9 else 0
        self.content_org_hash = reader.s(20) if self.version >= 12 else bytes()
    @staticmethod
    def _mem_size(version: int) -> int:
        size_for_7 = 32 if version >= 7 else 0
        size_for_8 = 768 if version >= 8 else 0
        size_for_9 = 8 if version >= 9 else 0
        size_for_12 = 20 if version >= 12 else 0
        return PakInfo._mem_size(version) + size_for_7 + size_for_8 + size_for_9 + size_for_12

class PakCompressedBlock:
    def __init__(self, reader: Reader):
        self.start = reader.u8()
        self.end = reader.u8()

@dataclass
class TencentPakEntry:
    def __init__(self, reader: Reader, version: int):
        self.content_hash = reader.s(20)
        if version <= 1:
            _ = reader.u8()
        self.offset = reader.u8()
        self.uncompressed_size = reader.u8()
        self.compression_method = reader.u4() & const.CM_MASK
        self.size = reader.u8()
        self.unk1 = reader.u1() if version >= 5 else 0
        self.unk2 = reader.s(20) if version >= 5 else bytes()
        self.compressed_blocks = [PakCompressedBlock(reader) for _ in range(reader.u4())] if self.compression_method != 0 and version >= 3 else []
        self.compression_block_size = reader.u4() if version >= 4 else 0
        self.encrypted = reader.u1() == 1 if version >= 4 else False
        self.encryption_method = reader.u4() if version >= 12 else 0
        self.index_new_sep = reader.u4() if version >= 12 else 0

# ==================== CRYPTO CLASS ====================
class PakCrypto:
    class _LCG:
        def __init__(self, seed: int):
            self.state = seed
        def next(self) -> int:
            MASK_32 = 4294967295
            MSB_1 = 2147483648
            def wrap(x: int) -> int:
                x &= MASK_32
                if not x & MSB_1:
                    return x
                else:
                    return (x + MSB_1 & MASK_32) - MSB_1
            x1 = wrap(1103515245 * self.state)
            self.state = wrap(x1 + 12345)
            x2 = wrap(x1 + 77880) if self.state < 0 else self.state
            return (x2 >> 16 & MASK_32) % 32767
    @staticmethod
    def zuc_keystream() -> list[int]:
        zuc = gmalg.ZUC(const.ZUC_KEY, const.ZUC_IV)
        return [struct.unpack('>I', zuc.generate())[0] for _ in range(16)]
    @staticmethod
    def _xorxor(buffer, x) -> bytes:
        return bytes((buffer[i] ^ x[i % len(x)] for i in range(len(buffer))))
    @staticmethod
    def _hashhash(buffer, n: int) -> bytes:
        result = bytes()
        for i in range(math.ceil(n / SHA1.digest_size)):
            result += SHA1.new(buffer).digest()
        if len(result) >= n:
            result = result[:n]
            return result
        else:
            result += b'\x00' * (n - len(result))
            return result
    @staticmethod
    def _meowmeow(buffer) -> bytes:
        def unpad(x):
            skip = 1 + next((i for i in range(len(x)) if x[i]!= 0))
            return x[skip:]
        if len(buffer) < 43:
            return bytes()
        else:
            x1 = buffer[1:][:SHA1.digest_size]
            x2 = buffer[SHA1.digest_size + 1:]
            x1 = PakCrypto._xorxor(x1, PakCrypto._hashhash(x2, len(x1)))
            x2 = PakCrypto._xorxor(x2, PakCrypto._hashhash(x1, len(x2)))
            part1, m = (x2[:SHA1.digest_size], x2[SHA1.digest_size:])
            if part1!= SHA1.new(b'\x00' * SHA1.digest_size).digest():
                return bytes()
            else:
                return unpad(m)
    @staticmethod
    def rsa_extract(signature: bytes, modulus: bytes) -> bytes:
        c = int.from_bytes(signature, 'little')
        n = int.from_bytes(modulus, 'little')
        e = 65537
        m = pow(c, e, n).to_bytes(256, 'little').rstrip(b'\x00')
        return PakCrypto._meowmeow(Misc.pad_to_n(m, 4))
    @staticmethod
    def _decrypt_simple1(ciphertext) -> bytes:
        return bytes((x ^ const.SIMPLE1_DECRYPT_KEY for x in ciphertext))
    @staticmethod
    def _decrypt_simple2(ciphertext) -> bytes:
        class RollingKey:
            def __init__(self, initial_value: int):
                self._value = initial_value
            def update(self, x: int) -> int:
                self._value ^= x
                return self._value
        assert len(ciphertext) % const.SIMPLE2_BLOCK_SIZE == 0
        initial_key, = struct.unpack('<I', const.SIMPLE2_DECRYPT_KEY)
        rolling_key = RollingKey(initial_key)
        plaintext = (struct.pack('<I', rolling_key.update(x)) for x in struct.unpack(f'<{len(ciphertext) // 4}I', ciphertext))
        return bytes(it.chain.from_iterable(plaintext))
    @staticmethod
    @lru_cache(maxsize=1)
    def _derive_sm4_key(file_path: PurePath, encryption_method: int) -> bytes:
        part1 = file_path.stem.lower()
        if encryption_method == const.EM_SM4_2:
            secret = const.SM4_SECRET_2
        else:
            if encryption_method == const.EM_SM4_4:
                secret = const.SM4_SECRET_4
            else:
                index = (encryption_method - const.EM_SM4_NEW_BASE) % len(const.SM4_SECRET_NEW)
                secret = f'{const.SM4_SECRET_NEW[index]}{encryption_method}'
        return SHA1.new(str(part1 + secret).encode()).digest()[:SM4.key_length()]
    @staticmethod
    @lru_cache(maxsize=1)
    def _sm4_context_for_key(key: bytes) -> SM4:
        return SM4(key)
    @staticmethod
    def _decrypt_sm4(ciphertext, file_path: PurePath, encryption_method: int) -> bytes:
        assert len(ciphertext) % SM4.block_length() == 0
        key = PakCrypto._derive_sm4_key(file_path, encryption_method)
        sm4 = PakCrypto._sm4_context_for_key(key)
        return bytes(it.chain.from_iterable((sm4.decrypt(x) for x in it.batched(ciphertext, SM4.block_length()))))
    @staticmethod
    def decrypt_index(ciphertext, pak_info: TencentPakInfo) -> bytes:
        if pak_info.version > 7:
            key = PakCrypto.rsa_extract(pak_info.packed_key, const.RSA_MOD_1)
            iv = PakCrypto.rsa_extract(pak_info.packed_iv, const.RSA_MOD_1)
            assert len(key) == 32 and len(iv) == 32
            aes = AES.new(key, MODE_CBC, iv[:16])
            return unpad(aes.decrypt(ciphertext), AES.block_size)
        else:
            return bytes(PakCrypto._decrypt_simple1(ciphertext))
    @staticmethod
    def _is_simple1_method(encryption_method: int) -> bool:
        return encryption_method == const.EM_SIMPLE1
    @staticmethod
    def _is_simple2_method(encryption_method: int) -> bool:
        return encryption_method == const.EM_SIMPLE2
    @staticmethod
    def _is_sm4_method(encryption_method: int) -> bool:
        return encryption_method == const.EM_SM4_2 or encryption_method == const.EM_SM4_4 or encryption_method & const.EM_SM4_NEW_MASK!= 0
    @staticmethod
    def align_encrypted_content_size(n: int, encryption_method: int) -> int:
        if PakCrypto._is_simple2_method(encryption_method):
            return Misc.align_up(n, const.SIMPLE2_BLOCK_SIZE)
        else:
            if PakCrypto._is_sm4_method(encryption_method):
                return Misc.align_up(n, SM4.block_length())
            else:
                return n

    @staticmethod
    def decrypt_block(ciphertext, file: PurePath, encryption_method: int) -> bytes:
        if encryption_method == 17:
            return ciphertext
        else:
            if PakCrypto._is_simple1_method(encryption_method):
                return PakCrypto._decrypt_simple1(ciphertext)
            else:
                if PakCrypto._is_simple2_method(encryption_method):
                    return PakCrypto._decrypt_simple2(ciphertext)
                else:
                    if PakCrypto._is_sm4_method(encryption_method):
                        return PakCrypto._decrypt_sm4(ciphertext, file, encryption_method)
                    else:
                        assert False
    @staticmethod
    @lru_cache(maxsize=33)
    def generate_block_indices(n: int, encryption_method: int) -> list[int]:
        if not PakCrypto._is_sm4_method(encryption_method):
            return list(range(n))
        else:
            permutation = []
            lcg = PakCrypto._LCG(n)
            while len(permutation)!= n:
                x = lcg.next() % n
                if x not in permutation:
                    permutation.append(x)
            inverse = [0] * len(permutation)
            for i, x in enumerate(permutation):
                inverse[x] = i
            return inverse
    @staticmethod
    def _encrypt_simple1(plaintext: bytes) -> bytes:
        return bytes((b ^ const.SIMPLE1_DECRYPT_KEY for b in plaintext))
    @staticmethod
    def _encrypt_simple2(plaintext: bytes) -> bytes:
        padded = Misc.pad_to_n(plaintext, const.SIMPLE2_BLOCK_SIZE)
        assert len(padded) % const.SIMPLE2_BLOCK_SIZE == 0
        initial_key, = struct.unpack('<I', const.SIMPLE2_DECRYPT_KEY)
        key_state = initial_key
        cipher_words = []
        plain_words = struct.unpack(f'<{len(padded) // 4}I', padded)
        for plain_word in plain_words:
            cipher_word = plain_word ^ key_state
            key_state = plain_word
            cipher_words.append(cipher_word)
        return struct.pack(f'<{len(cipher_words)}I', *cipher_words)
    @staticmethod
    def _encrypt_sm4(plaintext: bytes, file_path: PurePath, encryption_method: int) -> bytes:
        padded = Misc.pad_to_n(plaintext, SM4.block_length())
        key = PakCrypto._derive_sm4_key(file_path, encryption_method)
        sm4 = PakCrypto._sm4_context_for_key(key)
        encrypted = bytearray()
        for i in range(0, len(padded), SM4.block_length()):
            block = padded[i:i + SM4.block_length()]
            encrypted.extend(sm4.encrypt(block))
        return bytes(encrypted)
    @staticmethod
    def encrypt_block(plaintext: bytes, file: PurePath, encryption_method: int) -> bytes:
        if encryption_method == 17:
            return plaintext
        else:
            if PakCrypto._is_simple1_method(encryption_method):
                return PakCrypto._encrypt_simple1(plaintext)
            else:
                if PakCrypto._is_simple2_method(encryption_method):
                    return PakCrypto._encrypt_simple2(plaintext)
                else:
                    if PakCrypto._is_sm4_method(encryption_method):
                        return PakCrypto._encrypt_sm4(plaintext, file, encryption_method)
                    else:
                        assert False
    @staticmethod
    def encrypt_index(plaintext: bytes, pak_info: TencentPakInfo) -> bytes:
        keystream = PakCrypto.zuc_keystream()
        key = struct.pack('<5I', *keystream[4:][:5])
        if len(plaintext) < len(key):
            plaintext = plaintext + b'\x00' * (len(key) - len(plaintext))
        else:
            if len(plaintext) > len(key):
                key = (key * (len(plaintext) // len(key) + 1))[:len(plaintext)]
        return bytes((a ^ b for a, b in zip(plaintext, key)))
    @staticmethod
    def stat():
        print(PakCrypto._derive_sm4_key.cache_info())
        print(PakCrypto._sm4_context_for_key.cache_info())

class PakCompression:
    @staticmethod
    @lru_cache(maxsize=33)
    def _zstd_decompressor(dict: ZstdCompressionDict | bytes | None) -> ZstdDecompressor:
        if isinstance(dict, bytes):
            dict = ZstdCompressionDict(dict, DICT_TYPE_AUTO)
        return ZstdDecompressor(dict)
    @staticmethod
    def zstd_dictionary(dict_data) -> ZstdCompressionDict:
        return ZstdCompressionDict(dict_data, DICT_TYPE_AUTO)
    @staticmethod
    def decompress_block(block, dict: ZstdCompressionDict | bytes | None, compression_method: int) -> bytes:
        if compression_method == const.CM_ZLIB:
            return zlib.decompress(block)
        else:
            if compression_method == const.CM_ZSTD or compression_method == const.CM_ZSTD_DICT:
                if compression_method!= const.CM_ZSTD_DICT:
                    dict = None
                return PakCompression._zstd_decompressor(dict).decompress(block)
            else:
                assert False

class CompressionFinder:
    ZLIB_LEVELS_TO_TRY = list(range(9, 0, -1))
    ZSTD_LEVELS_TO_TRY = list(range(22, 0, -1)) + list(range(-1, -8, -1))

    @staticmethod
    def find_best_level(
        uncompressed_chunk: bytes, 
        original_compressed_size: int, 
        dict_data: bytes | None, 
        compression_method: int
    ) -> (int | None, int):
        
        levels_to_try = []
        default_level = 9
        if compression_method == const.CM_ZLIB:
            levels_to_try = CompressionFinder.ZLIB_LEVELS_TO_TRY
            default_level = 9
        elif compression_method in [const.CM_ZSTD, const.CM_ZSTD_DICT]:
            levels_to_try = CompressionFinder.ZSTD_LEVELS_TO_TRY
            default_level = 22
        else:
            return None, len(uncompressed_chunk)

        best_fit_level = None
        closest_size_so_far = -1

        for level in levels_to_try:
            compressed_data = PakCompression.compress_block(uncompressed_chunk, dict_data, compression_method, level=level)
            current_size = len(compressed_data)

            if original_compressed_size >= current_size > closest_size_so_far:
                closest_size_so_far = current_size
                best_fit_level = level
                if current_size == original_compressed_size:
                    break
        
        if best_fit_level is not None:
            return best_fit_level, closest_size_so_far

        final_compressed = PakCompression.compress_block(uncompressed_chunk, dict_data, compression_method, level=default_level)
        return default_level, len(final_compressed)

class TencentPakFile:
    def __init__(self, file_path: PurePath, is_od=False):
        self._file_path = file_path

        with open(file_path, 'rb') as file:
            self._file_content = memoryview(file.read())

        self._is_od = is_od
        self._mount_point = PurePath()
        self._is_zstd_with_dict = 'zsdic' in str(self._file_path)
        self._zstd_dict = None

        self._files = []
        self._index: dict[PurePath, dict[str, TencentPakEntry]] = {}

        # Pak info + crypto metadata
        self._pak_info = TencentPakInfo(self._file_content, PakCrypto.zuc_keystream())

        self._verify_stem_hash()
        self._tencent_load_index()

    # ---------- header / index loading ----------

    def _verify_stem_hash(self) -> None:
        if not self._is_od and self._pak_info.version >= 9:
            # crc32 over UTF-32LE stem, same as tool.py
            assert self._pak_info.stem_hash == zlib.crc32(self._file_path.stem.encode('utf-32le'))

    def _tencent_load_index(self) -> None:
        index_data = self._file_content[self._pak_info.index_offset:][:self._pak_info.index_size]

        if self._pak_info.index_encrypted:
            index_data = PakCrypto.decrypt_index(index_data, self._pak_info)

        self._verify_index_hash(index_data)
        self._load_index(index_data)

    def _verify_index_hash(self, index_data) -> None:
        expected_hash = self._pak_info.index_hash

        # For Tencent versions >= 8, index hash is also stored RSA-wrapped;
        # this assert mirrors original behavior.
        if not self._is_od and self._pak_info.version >= 8:
            assert expected_hash == PakCrypto.rsa_extract(self._pak_info.packed_index_hash, const.RSA_MOD_2)

        # Finally, compare against SHA1(index_data)
        assert expected_hash == SHA1.new(index_data).digest()

    @staticmethod
    def _construct_mount_point(mount_point: str) -> PurePath:
        result = PurePath()
        for part in PurePath(mount_point).parts:
            if part != '..':
                result /= part
        return result

    # ---------- content peeking helpers ----------

    def _peek_content(self, offset: int, size: int, encryption_method: int) -> memoryview:
        size = PakCrypto.align_encrypted_content_size(size, encryption_method)
        return self._file_content[offset:][:size]

    def _peek_block_content(self, block: PakCompressedBlock, encryption_method: int) -> memoryview:
        size = PakCrypto.align_encrypted_content_size(block.end - block.start, encryption_method)
        return self._file_content[block.start:][:size]

    # ---------- ZSTD dictionary handling ----------

    def _construct_zstd_dict(self, dict_entry: TencentPakEntry) -> None:
        assert not self._zstd_dict
        assert not dict_entry.encrypted
        assert dict_entry.compression_method == const.CM_NONE

        reader = Reader(self._peek_content(dict_entry.offset, dict_entry.size, 0))
        dict_size = reader.u8()
        _ = reader.u4()
        assert dict_size == reader.u4()
        dict_data = reader.s(dict_size)

        # Ensure dict_data is bytes, not tuple
        if isinstance(dict_data, tuple):
            dict_data = dict_data[0] if dict_data else b''
        
        # Wrap in ZstdCompressionDict for proper usage
        self._zstd_dict = ZstdCompressionDict(dict_data, dict_type=DICT_TYPE_AUTO)

    # ---------- index parsing ----------

    def _load_index(self, index_data) -> None:
        assert not self._pak_info.version <= 10

        reader = Reader(index_data)
        self._mount_point = self._construct_mount_point(reader.string())
        self._files = [TencentPakEntry(reader, self._pak_info.version) for _ in range(reader.u4())]

        for _ in range(reader.u8()):
            dir_path = PurePath(reader.string())
            e = {reader.string(): self._files[~reader.i4()] for _ in range(reader.u8())}

            # Special zstd dictionary pak
            if self._is_zstd_with_dict and dir_path.name == 'zstddic':
                assert len(e) == 1
                self._construct_zstd_dict(e[[*e.keys()][0]])
            else:
                self._index.update({PurePath(dir_path): e})

    # ---------- core file write ----------

    def _write_to_disk(self, file_path: PurePath, entry: TencentPakEntry) -> None:
        if entry.encrypted and entry.encryption_method == 17:
            print(f'   ⚠️ Skipping {file_path.name} - EM_UNKNOWN_17 (unsupported encryption)')
            return

        encryption_method = entry.encryption_method
        compression_method = entry.compression_method

        with open(file_path, 'wb') as file:
            # Uncompressed file
            if compression_method == const.CM_NONE:
                data = self._peek_content(entry.offset, entry.size, encryption_method)

                if entry.encrypted:
                    data = PakCrypto.decrypt_block(data, file_path, encryption_method)

                file.write(data)
                return

            # Compressed file: iterate blocks in logical order
            for x in PakCrypto.generate_block_indices(len(entry.compressed_blocks), encryption_method):
                data = self._peek_block_content(entry.compressed_blocks[x], encryption_method)

                if entry.encrypted:
                    data = PakCrypto.decrypt_block(data, file_path, encryption_method)

                data = PakCompression.decompress_block(data, self._zstd_dict, compression_method)
                file.write(data)

    # ---------- UNPACK + MANIFEST (real-time) ----------

    def dump(self, out_path: PurePath, use_block_splitting: bool = False) -> None:
        """Enhanced dump with manifest generation - OPTIMIZED FOR SPEED
        
        Args:
            out_path: Output directory path
            use_block_splitting: If True, extract files as separate .block_N files (for easier editing)
        """
        # Store the base output path (WITHOUT mount point) for manifest
        base_out_path = Path(out_path)
        
        # Honor mount point for file extraction
        out_path = base_out_path / self._mount_point
        
        # Create a manifest for this PAK (NO real-time writing for speed)
        manifest = ManifestGenerator(self._file_path.name)
        manifest.set_extraction_mode(use_block_splitting)
        
        file_count = 0
        total_files = sum(len(files) for files in self._index.values())

        for dir_path, dir in self._index.items():
            current_out_path = Path(out_path / dir_path)
            if not current_out_path.exists():
                current_out_path.mkdir(parents=True, exist_ok=True)

            for file_name, entry in dir.items():
                file_count += 1
                
                # OPTIMIZATION: Batch progress (every 50 files)
                if file_count % 50 == 1 or file_count == total_files:
                    print(f'📊 Progress: {file_count}/{total_files} files')
                
                file_path = current_out_path / file_name
                full_rel_path = dir_path / file_name  # path inside pak

                # Figure out where the actual data is in the pak
                if entry.compressed_blocks:
                    actual_offset = entry.compressed_blocks[0].start
                    actual_size = entry.compressed_blocks[0].end - entry.compressed_blocks[0].start
                else:
                    actual_offset = entry.offset
                    actual_size = entry.size

                # Actually write file to disk
                if use_block_splitting and entry.compressed_blocks:
                    # Reconstruct full decompressed file in the SAME logical order as normal extraction,
                    # then split sequentially into fixed 64KB chunks (+ remainder as last chunk).
                    try:
                        encryption_method = entry.encryption_method
                        compression_method = entry.compression_method

                        plain_parts: list[bytes] = []
                        for x in PakCrypto.generate_block_indices(len(entry.compressed_blocks), encryption_method):
                            block = entry.compressed_blocks[x]
                            block_data = self._peek_block_content(block, encryption_method)

                            if entry.encrypted:
                                block_data = PakCrypto.decrypt_block(block_data, file_path, encryption_method)

                            block_plain = PakCompression.decompress_block(block_data, self._zstd_dict, compression_method)
                            plain_parts.append(block_plain)

                        full_plain = b''.join(plain_parts)

                        # Safety: trim to declared uncompressed size (avoids padding / over-read)
                        if entry.uncompressed_size and len(full_plain) > entry.uncompressed_size:
                            full_plain = full_plain[:entry.uncompressed_size]

                        # Always split into 64KB sequential blocks (and remainder as last)
                        block_size = 64 * 1024

                        stem = file_path.stem
                        ext = file_path.suffix

                        block_idx = 0
                        for off in range(0, len(full_plain), block_size):
                            chunk = full_plain[off:off + block_size]
                            block_file = file_path.parent / f'{stem}_block_{block_idx}{ext}'
                            block_file.write_bytes(chunk)

                            manifest.add_block_file_entry(full_rel_path, block_idx, len(chunk), entry)
                            block_idx += 1

                    except Exception as e:
                        print(f'Failed block-split of {file_name}: {e}')
                else:
                    # Normal full-file write
                    self._write_to_disk(file_path, entry)
                    # Only add to manifest for full files
                    manifest.add_file_entry(full_rel_path, entry, actual_offset, actual_size)

        # Final save with summary - save to BASE path, not the mount point subfolder
        print('💾 Finalizing manifest...')
        manifest.save(base_out_path)
        
        # Create 'edited' folder automatically for user convenience
        edited_folder = base_out_path / 'edited'
        if not edited_folder.exists():
            edited_folder.mkdir(parents=True, exist_ok=True)
            print(f'📁 Created "edited" folder: {edited_folder}')
            print('   💡 Place your modified files here for repacking')

    # ---------- REPACK (uses manifest.json) ----------

    def repack(self, input_folder: PurePath, output_pak: PurePath) -> None:
        logger = RepackLogger()
        # Track which PAK entries we modified so we can verify them after writing
        modified_targets: list[tuple[PurePath, TencentPakEntry]] = []

        print(f'🔄 Repacking from {input_folder} to {output_pak}')
        input_path = Path(input_folder)
        
        # Define unpacked_folder as the parent directory containing both 'extracted' and 'edited' folders
        unpacked_folder = input_path.parent

        if not input_path.exists():
            raise FileNotFoundError(f'Input folder not found: {input_folder}')
        else:
            manifest_reader = None
            manifest_path = input_path.parent / 'manifest.json'

            if manifest_path.exists():
                try:
                    manifest_reader = ManifestReader(manifest_path)
                except Exception as e:
                    print(f'⚠️ Manifest error: {e}')

            print('📋 Copying original pak...')

            temp_pak = Path(str(output_pak) + '.tmp')
            shutil.copy2(self._file_path, temp_pak)
            print('✅ Base copied')

            # ==================== AUTO-SCAN FEATURE ====================
            if AUTO_SCAN_ENABLED and manifest_reader:
                console.print("\n[bold cyan]🤖 AUTO-SCAN MODE ENABLED[/bold cyan]")
                console.print("Auto-scan will find and repack all modified uasset/uexp files in their correct locations.")
                
                # Initialize auto-scan repack
                auto_scanner = AutoScanRepack(self, input_path, manifest_reader, logger)
                
                # Scan for modified files
                if auto_scanner.scan_for_modifications():
                    # Process the scanned files
                    console.print("\n[cyan]⚙️ Auto-repacking matched files...[/cyan]")
                    auto_scanner.process_files()
                    
                    # Get results
                    work_items, modified_targets_from_auto = auto_scanner.get_results()
                    
                    # Extend our work items and modified targets
                    if work_items:
                        console.print(f"\n[green]✅ Auto-scan found {len(work_items)} files to repack[/green]")
                        # We'll integrate these with the main workflow
                        # For now, we'll just process them directly
                        
                        if work_items:
                            print(f'\n📝 Writing {len(work_items)} files from auto-scan...')

                            try:
                                with open(temp_pak, 'r+b') as fp:
                                    for entry_path, block_data, is_multi in work_items:
                                        try:
                                            for offset, data in block_data:
                                                fp.seek(offset)
                                                fp.write(data)

                                            print(f'✅ {Path(entry_path).name}: {len(block_data)} block(s) written')
                                        except Exception as e:
                                            print(f'❌ Write error for {Path(entry_path).name}: {e}')

                                temp_pak.replace(output_pak)
                                print(f'\n✅ Auto-Repack Complete! Saved to: {output_pak}')

                                # -------------------- Integrity verification --------------------
                                # Re-open the repacked PAK and attempt to decrypt+decompress all modified entries.
                                # This catches common corruption causes (wrong block order, padding, size issues).
                                try:
                                    with open(output_pak, 'rb') as vf:
                                        vbuf = memoryview(vf.read())

                                    ok = 0
                                    bad = 0
                                    for vpath, ventry in modified_targets_from_auto:
                                        try:
                                            enc_m = ventry.encryption_method
                                            comp_m = ventry.compression_method

                                            if ventry.encrypted and enc_m == 17:
                                                raise ValueError('EM_UNKNOWN_17 not supported')

                                            # Uncompressed
                                            if comp_m == const.CM_NONE:
                                                sz = PakCrypto.align_encrypted_content_size(ventry.size, enc_m)
                                                data = vbuf[ventry.offset:][:sz]
                                                if ventry.encrypted:
                                                    data = PakCrypto.decrypt_block(bytes(data), vpath, enc_m)
                                                plain = bytes(data)
                                            else:
                                                parts = []
                                                for bi in PakCrypto.generate_block_indices(len(ventry.compressed_blocks), enc_m):
                                                    b = ventry.compressed_blocks[bi]
                                                    bsz = PakCrypto.align_encrypted_content_size(b.end - b.start, enc_m)
                                                    blk = vbuf[b.start:][:bsz]
                                                    blk_bytes = bytes(blk)
                                                    if ventry.encrypted:
                                                        blk_bytes = PakCrypto.decrypt_block(blk_bytes, vpath, enc_m)
                                                    dec = PakCompression.decompress_block(blk_bytes, self._zstd_dict, comp_m)
                                                    parts.append(dec)
                                                plain = b''.join(parts)

                                            # Trim to declared uncompressed size for validation
                                            if ventry.uncompressed_size and len(plain) >= ventry.uncompressed_size:
                                                plain = plain[:ventry.uncompressed_size]

                                            if ventry.uncompressed_size and len(plain) != ventry.uncompressed_size:
                                                raise ValueError(f'Uncompressed size mismatch: got {len(plain)}, expected {ventry.uncompressed_size}')

                                            ok += 1
                                        except Exception as ve:
                                            bad += 1
                                            print(f'❌ Verify failed: {vpath} -> {ve}')

                                    if bad == 0:
                                        print(f'✅ Verification passed for {ok} modified entr(y/ies).')
                                    else:
                                        print(f'⚠️ Verification: {ok} passed, {bad} failed. The output PAK may be broken.')
                                except Exception as ve:
                                    print(f'⚠️ Verification step failed to run: {ve}')
                                # ----------------------------------------------------------------

                                logger.print_summary()
                                return  # Exit early since we processed everything
                            except Exception as e:
                                print(f'❌ File Error: {e}')
                else:
                    console.print("[yellow]⚠️ No uasset/uexp files found to auto-repack[/yellow]")
            
            # ==================== END AUTO-SCAN ====================
            
            # If auto-scan didn't process anything or is disabled, fall back to manual mode
            console.print("\n[cyan]📝 Switching to manual repack mode for remaining files...[/cyan]")
            
            # Get all files from the edited folder ONLY
            mod_files = []
            if input_path.exists():
                # Collect all relevant files
                for item in input_path.rglob('*'):
                    if item.is_file():
                        # Check if it's a file type we care about
                        if item.suffix.lower() in ['.uasset', '.uexp', '.ubulk', '.umap']:
                            mod_files.append(item)
                
                print(f"🔍 Found {len(mod_files)} files in edited folder")
                
                # Debug: Show what we found with full paths
                if mod_files:
                    print("   Files found with full paths:")
                    for i, f in enumerate(mod_files[:10]):  # Show first 10
                        try:
                            rel_path = f.relative_to(input_path)
                            print(f"   {i+1}. {rel_path} ({f.stat().st_size:,} bytes)")
                        except:
                            print(f"   {i+1}. {f.name} ({f.stat().st_size:,} bytes)")
                    if len(mod_files) > 10:
                        print(f"   ... and {len(mod_files) - 10} more files")
                else:
                    print("   ⚠️ No files found in edited folder!")
            else:
                print(f"❌ Edited folder does not exist: {input_path}")
                temp_pak.unlink(missing_ok=True)
                return

            # Build block file lookup from manifest - using full paths
            block_file_lookup = {}  # full_path_in_edited_folder -> block_info
            if manifest_reader:
                for block_filename, block_info in manifest_reader.block_files.items():
                    parent_file = block_info.get('parent_file')
                    if parent_file:
                        # Create the expected path in the edited folder
                        # parent_file is like "ShadowTrackerExtra/Content/MultiRegion/Content/IN/CSV/Item.uasset"
                        parent_dir = Path(parent_file).parent
                        block_filename = block_info.get('extracted_filename')
                        expected_relative_path = str(parent_dir / block_filename).replace('\\', '/')
                        
                        block_file_lookup[expected_relative_path] = {
                            'parent': parent_file,
                            'block_index': block_info.get('block_index', 0),
                            'block_size': block_info.get('block_size', 0),
                            'extracted_filename': block_filename
                        }
            
            # Group block files by parent based on actual file paths
            block_groups_by_parent = {}  # parent_pak_path -> [(block_index, filepath, size)]
            
            for mod_file in mod_files:
                # Get the relative path from edited folder
                try:
                    rel_path_str = str(mod_file.relative_to(input_path)).replace('\\', '/')
                    
                    # Check if this is a block file by looking up its relative path
                    if rel_path_str in block_file_lookup:
                        info = block_file_lookup[rel_path_str]
                        parent = info['parent']
                        
                        if parent not in block_groups_by_parent:
                            block_groups_by_parent[parent] = []
                        
                        block_groups_by_parent[parent].append((
                            info['block_index'],
                            mod_file,
                            info['block_size']
                        ))
                        continue
                    
                    # Also check if filename has _block_ pattern (for manual edits)
                    filename = mod_file.name
                    if '_block_' in filename:
                        # Try to match by reconstructing the parent path from directory structure
                        # Get the directory path relative to edited folder
                        rel_dir = str(mod_file.parent.relative_to(input_path)).replace('\\', '/')
                        
                        # Look for files in manifest that have this directory structure
                        for parent_path, file_info in manifest_reader.manifest.get('files', {}).items():
                            # Get the directory of the parent file in manifest
                            parent_dir = str(Path(parent_path).parent).replace('\\', '/')
                            
                            # Check if this matches and the file was extracted as blocks
                            if parent_dir == rel_dir and file_info.get('extracted_as_blocks'):
                                # Extract block index from filename
                                try:
                                    block_index = int(filename.split('_block_')[1].split('.')[0])
                                except (ValueError, IndexError):
                                    block_index = 0
                                
                                if parent_path not in block_groups_by_parent:
                                    block_groups_by_parent[parent_path] = []
                                
                                block_groups_by_parent[parent_path].append((
                                    block_index,
                                    mod_file,
                                    mod_file.stat().st_size
                                ))
                                break
                            
                except ValueError:
                    # File not in input_path (shouldn't happen)
                    continue
            
            # Sort blocks within each group
            for parent in block_groups_by_parent:
                block_groups_by_parent[parent].sort(key=lambda x: x[0])
            
            # Filter out block files from mod_files list (they'll be processed separately)
            regular_mod_files = []
            for f in mod_files:
                # Get relative path
                try:
                    rel_path_str = str(f.relative_to(input_path)).replace('\\', '/')
                    # Check if this file is in block_file_lookup or has _block_ pattern
                    if rel_path_str in block_file_lookup or '_block_' in f.name:
                        # It's a block file, skip from regular processing
                        continue
                except ValueError:
                    pass
                regular_mod_files.append(f)
            
            mod_files = regular_mod_files
            
            # Show what we found
            if block_groups_by_parent:
                console.print(f'\n📦 Found {len(block_groups_by_parent)} files with block-based extraction:')
                for parent, blocks in block_groups_by_parent.items():
                    parent_name = Path(parent).name
                    console.print(f'   • {parent_name}: {len(blocks)} block(s) at {parent}')
                    for block_idx, block_file, block_size in blocks[:3]:  # Show first 3 blocks
                        try:
                            rel_path = block_file.relative_to(input_path)
                            console.print(f'      - Block {block_idx}: {rel_path} ({block_size:,} bytes)')
                        except:
                            console.print(f'      - Block {block_idx}: {block_file.name} ({block_size:,} bytes)')
                    if len(blocks) > 3:
                        console.print(f'      ... and {len(blocks) - 3} more blocks')
            
            if not mod_files and not block_groups_by_parent:
                print('\n⚠️ No files found to repack')
                temp_pak.unlink(missing_ok=True)
                logger.print_summary()
                return
            else:
                total_files = len(mod_files) + len(block_groups_by_parent)
                print(f'\n📝 Found {total_files} files to process ({len(mod_files)} regular, {len(block_groups_by_parent)} block-based)\n')

                work_items = []

                # ============================================================
                # Process regular files (not block files)
                # ============================================================
                for mod_file in mod_files:
                    mod_name = mod_file.name
                    print(f'🔍 Processing regular file: {mod_name}')
                    
                    try:
                        mod_bytes = mod_file.read_bytes()
                    except Exception as e:
                        print(f'   ❌ Error reading file: {e}')
                        continue
                        
                    print(f'   📊 File size: {len(mod_bytes):,} bytes')

                    entries: list[tuple[PurePath, TencentPakEntry]] = []

                    # Use the relative path from input_folder to match PAK structure
                    try:
                        # Get relative path from edited folder
                        rel_path = mod_file.relative_to(input_path)
                        # Convert to string with forward slashes
                        rel_path_str = str(rel_path).replace('\\', '/')
                        print(f'   📁 Relative path: {rel_path_str}')
                        
                        # Use the full path for logging to avoid confusion with duplicate filenames
                        display_name = rel_path_str  # Use full path instead of just filename
                        
                        # Look for this exact path in the manifest
                        if manifest_reader:
                            manifest_info = manifest_reader.find_file_info(rel_path_str, quiet_on_exact_match=True)
                            if manifest_info:
                                # Found by relative path - great!
                                print(f'   ✅ Matched by relative path in manifest')
                                # Now we need to find the actual PAK entry
                                for dp, df in self._index.items():
                                    for fn, ent in df.items():
                                        full_pak_path = str(dp / fn).replace('\\', '/')
                                        if full_pak_path == rel_path_str:
                                            entries.append((dp / fn, ent))
                                            break
                                    if entries:
                                        break
                    
                    except ValueError:
                        # File not in input_path (shouldn't happen)
                        display_name = mod_name  # Fallback to filename only
                    
                    # If display_name wasn't set (shouldn't happen), use filename
                    if 'display_name' not in locals():
                        display_name = mod_name

                    # Fallback: if no path match, try filename-only match
                    if not entries:
                        for dp, df in self._index.items():
                            for fn, ent in df.items():
                                if fn == mod_name:
                                    full_pak_path = dp / fn
                                    pak_parts = full_pak_path.parts
                                    display_path = '/'.join(pak_parts[-min(4, len(pak_parts)):])
                                    print(f'   ⚠️ Warning: filename-only match: {display_path}')
                                    entries.append((full_pak_path, ent))
                    
                    # Now print manifest details for the matched entry
                    if manifest_reader and entries:
                        matched_pak_path = str(entries[0][0])
                        manifest_reader.print_file_details(matched_pak_path, quiet_on_exact_match=True)

                    if not entries:
                        print('   ⚠️ No match')
                        logger.log_failure(display_name, 'No matching PAK entry', {})
                        continue
                    
                    if len(entries) > 1:
                        print(f'   ⚠️ Warning: Found {len(entries)} potential matches for {mod_name}')
                        print(f'   💡 Tip: Organize your files in subfolders matching the PAK structure to ensure correct matching')
                        for idx, (epath, eentry) in enumerate(entries):
                            pak_path_display = '/'.join(epath.parts[-min(4, len(epath.parts)):])
                            print(f'      {idx+1}. {pak_path_display} (uncompressed: {eentry.uncompressed_size:,} bytes)')
                        print(f'   ℹ️ Will attempt repacking with the first valid match')
                    
                    # Early size validation
                    if entries:
                        matching_size_found = False
                        for epath, eentry in entries:
                            if eentry.uncompressed_size == len(mod_bytes):
                                matching_size_found = True
                                break
                        
                        if not matching_size_found:
                            print(f'   ⚠️ WARNING: Your file size ({len(mod_bytes):,} bytes) doesn\'t match any PAK entry!')
                            print(f'   Expected sizes for entries with this filename:')
                            for epath, eentry in entries:
                                pak_path_display = '/'.join(epath.parts[-min(4, len(epath.parts)):])
                                print(f'      • {pak_path_display}: {eentry.uncompressed_size:,} bytes')
                            print(f'   ℹ️ This usually means:')
                            print(f'      1. You\'re modifying a different version of the file than what\'s in the PAK')
                            print(f'      2. The file has been edited beyond what the original slots can accommodate')
                            print(f'      3. There are multiple files with this name and you need better path matching')

                    success = False

                    # Create per-file block logger
                    block_logger = BlockLogger(display_name)

                    for epath, eentry in entries:
                        if eentry.encrypted and eentry.encryption_method == 17:
                            print('   ⚠️ Skipping entry - EM_UNKNOWN_17 (unsupported encryption)')
                            continue

                        blocks = eentry.compressed_blocks
                        compression_method = eentry.compression_method
                        encryption_method = eentry.encryption_method if eentry.encrypted else 0

                        block_size_val = eentry.compression_block_size

                        if not blocks:
                            # Uncompressed (rare), treat as single block
                            slot = eentry.size
                            print(f'   📦 Uncompressed single slot: {slot:,} bytes')

                            if len(mod_bytes) > slot:
                                print(f'   ❌ Mod too large: {len(mod_bytes):,} > {slot:,}')
                                logger.log_failure(display_name, 'Mod too large for slot', {'mod_size': len(mod_bytes), 'slot': slot})
                                continue

                            result = mod_bytes  # raw bytes; padding/encryption handled below
                            level_used = -1  # No compression
                            comp_method_str = 'NONE'

                            if eentry.encrypted:
                                cipher_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
                                if len(result) > cipher_slot:
                                    raise ValueError(f'Entry data {len(result)} does not fit cipher slot {cipher_slot} (slot {slot}) for encryption method {encryption_method}')
                                padded_plain = result + b'\x00' * (cipher_slot - len(result))
                                cipher = PakCrypto.encrypt_block(padded_plain, epath, encryption_method)
                                if len(cipher) != cipher_slot:
                                    raise ValueError(f'Encrypted entry size mismatch: got {len(cipher)} bytes, expected {cipher_slot}')
                                result = cipher + b'\x00' * (slot - cipher_slot)

                            work_items.append((epath, [(eentry.offset, result)], False))
                            modified_targets.append((epath, eentry))
                            block_logger.add_block(0, len(mod_bytes), len(result), comp_method_str, level_used, True, eentry.offset, eentry.offset + slot)
                            # Log success for uncompressed single-block file
                            logger.log_success(display_name, slot, slot)
                            success = True
                            break

                        # Single-block
                        elif len(blocks) == 1:
                            block = blocks[0]
                            slot = block.end - block.start
                            
                            comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')
                            enc_method_str = {0: 'NONE', 2: 'AES', 40: 'SM4'}.get(encryption_method, 'UNKNOWN')
                            
                            print(f'   ╔═══════════════════════════════════════════════════════════════════════════════')
                            print(f'   ║ 📄 SINGLE-BLOCK FILE COMPRESSION')
                            print(f'   ╠═══════════════════════════════════════════════════════════════════════════════')
                            print(f'   ║ File: {mod_name}')
                            print(f'   ║ Modified size: {len(mod_bytes):,} bytes')
                            print(f'   ║ Slot size: {slot:,} bytes')
                            print(f'   ║ Compression: {comp_method_str} (method {compression_method})')
                            print(f'   ║ Encryption: {enc_method_str} (method {encryption_method})')
                            print(f'   ╚═══════════════════════════════════════════════════════════════════════════════')

                            result = None
                            level_used = -1

                            # ALWAYS RECOMPRESS - No reuse logic
                            best_compressed = None
                            best_size = float('inf')
                            best_level = -1
                            
                            # Determine compression method details
                            if compression_method == const.CM_ZLIB:
                                comp_method_name = "ZLIB"
                                max_level = 9
                                level_step = 1  # Try every level
                            elif compression_method in [const.CM_ZSTD, const.CM_ZSTD_DICT]:
                                comp_method_name = "ZSTD" if compression_method == const.CM_ZSTD else "ZSTD_DICT"
                                max_level = 22
                                level_step = 1  # Try every level for better fit
                            else:
                                comp_method_name = "UNKNOWN"
                                max_level = 9
                                level_step = 1
                            
                            print(f'   🔧 Compressing with {comp_method_name} (max level: {max_level}, trying all levels)')
                            print(f'   📏 Original: {len(mod_bytes):,} bytes, Target slot: {slot:,} bytes')
                            
                            # Calculate usable slot size (accounting for encryption overhead if needed)
                            usable_slot = slot
                            if eentry.encrypted:
                                usable_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
                            
                            attempts = 0
                            for lvl in range(max_level, 0, -level_step):
                                attempts += 1
                                comp = None

                                try:
                                    if compression_method == const.CM_ZLIB:
                                        actual_level = min(lvl, 9)
                                        comp = zlib.compress(mod_bytes, level=actual_level)
                                        lvl_display = actual_level
                                    elif compression_method == const.CM_ZSTD:
                                        comp = ZstdCompressor(level=lvl).compress(mod_bytes)
                                        lvl_display = lvl
                                    elif compression_method == const.CM_ZSTD_DICT and self._zstd_dict is not None:
                                        comp = ZstdCompressor(level=lvl, dict_data=self._zstd_dict).compress(mod_bytes)
                                        lvl_display = lvl
                                    else:
                                        print(f'   ❌ Unknown compression method: {compression_method}')
                                        break

                                    if comp:
                                        comp_size = len(comp)
                                        ratio = (comp_size / len(mod_bytes)) * 100
                                        savings = len(mod_bytes) - comp_size
                                        slot_usage = (comp_size / usable_slot) * 100
                                        
                                        fit_status = "✅ FIT" if comp_size <= slot else "❌ TOO BIG"
                                        
                                        print(f'   │ Attempt {attempts}: Level {lvl_display:>2} │ {len(mod_bytes):>8,} → {comp_size:>8,} bytes │ Ratio: {ratio:>6.2f}% │ Saved: {savings:>7,} │ Slot: {slot_usage:>6.2f}% │ {fit_status}')
                                        
                                        if comp_size < best_size:
                                            best_size = comp_size
                                            best_compressed = comp
                                            best_level = lvl_display

                                        if comp_size <= usable_slot:
                                            result = comp
                                            level_used = lvl_display
                                            print(f'   └─> ✅ SUCCESS! Compressed {len(mod_bytes):,} → {comp_size:,} bytes using level {lvl_display} ({slot_usage:.2f}% slot usage)')
                                            break
                                except Exception as e:
                                    print(f'   │ Attempt {attempts}: Level {lvl:>2} │ ⚠️ ERROR: {str(e)}')
                                    continue

                            if result is None:
                                if best_compressed:
                                    overage = best_size - slot
                                    overage_pct = (overage / slot) * 100
                                    print(f'   └─> ❌ FAILED! Best compression: {best_size:,} bytes at level {best_level}')
                                    print(f'       Target slot: {slot:,} bytes')
                                    print(f'       Overage: {overage:,} bytes ({overage_pct:.2f}% over limit)')
                                    print(f'       Tried {attempts} compression levels')
                                logger.log_failure(display_name, 'Compression failed to fit', {'best_size': best_size, 'slot': slot})
                                continue

                            # Store actual compressed size before padding/encryption
                            compressed_size_for_log = len(result)

                            # Always overwrite the full stored slot range (single-block)
                            if eentry.encrypted:
                                cipher_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
                                if len(result) > cipher_slot:
                                    raise ValueError(f'Compressed data {len(result)} does not fit cipher slot {cipher_slot} (slot {slot})')
                                padded_plain = result + b'\x00' * (cipher_slot - len(result))
                                cipher = PakCrypto.encrypt_block(padded_plain, epath, encryption_method)
                                if len(cipher) != cipher_slot:
                                    raise ValueError(f'Encrypted block size mismatch: got {len(cipher)} bytes, expected {cipher_slot}')
                                result = cipher + b'\x00' * (slot - cipher_slot)
                                print(f'   🔒 Encrypted with {enc_method_str}: {len(result):,} bytes ({cipher_slot:,} encrypted + {slot - cipher_slot} pad)')
                            else:
                                result = result + b'\x00' * (slot - len(result))

                            # Log actual compressed size, not padded
                            block_logger.add_block(0, len(mod_bytes), compressed_size_for_log, comp_method_str, level_used, True, block.start, block.end)

                            work_items.append((epath, [(block.start, result)], False))
                            modified_targets.append((epath, eentry))
                            # Log success for single-block file
                            logger.log_success(display_name, slot, slot)
                            success = True
                            break

                        # Multi-block (always per-chunk)
                        else:
                            total_slot_size = sum((b.end - b.start for b in blocks))
                            block_size_kb = block_size_val / 1024
                            total_slot_kb = total_slot_size / 1024
                            mod_size_kb = len(mod_bytes) / 1024
                            
                            comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')
                            enc_method_str = {0: 'NONE', 2: 'AES', 40: 'SM4'}.get(encryption_method, 'UNKNOWN')
                            
                            print(f'   ╔═══════════════════════════════════════════════════════════════════════════════')
                            print(f'   ║ 📦 MULTI-BLOCK FILE COMPRESSION')
                            print(f'   ╠═══════════════════════════════════════════════════════════════════════════════')
                            print(f'   ║ File: {mod_name}')
                            print(f'   ║ Modified size: {len(mod_bytes):,} bytes ({mod_size_kb:.2f} KB)')
                            print(f'   ║ Blocks: {len(blocks)} blocks × {block_size_val:,} bytes ({block_size_kb:.2f} KB per block)')
                            print(f'   ║ Total slot space: {total_slot_size:,} bytes ({total_slot_kb:.2f} KB)')
                            print(f'   ║ Compression: {comp_method_str} (method {compression_method})')
                            print(f'   ║ Encryption: {enc_method_str} (method {encryption_method})')
                            print(f'   ╚═══════════════════════════════════════════════════════════════════════════════')

                            chunks = list(it.batched(mod_bytes, block_size_val))
                            # Convert tuples to bytes (it.batched returns tuples)
                            chunks = [bytes(chunk) if isinstance(chunk, tuple) else chunk for chunk in chunks]
                            if len(chunks) > len(blocks):
                                print(f'   ❌ Too many chunks: {len(chunks)} > {len(blocks)} blocks')
                                logger.log_failure(display_name, 'Too many chunks', {'chunks': len(chunks), 'blocks': len(blocks)})
                                continue

                            # IMPORTANT: Some encryption methods (SM4 variants) permute block ordering.
                            # Use the same mapping as dump() so logical chunk i maps to the correct stored block.
                            block_indices = PakCrypto.generate_block_indices(len(blocks), encryption_method)

                            # ========== BLOCK REUSE OPTIMIZATION ==========
                            print(f'   🔍 Analyzing blocks for reuse...')
                            block_reuse_decisions = {}  # idx -> (should_reuse, original_compressed_data)
                            
                            try:
                                # Find the original unpacked file to compare
                                # It should be in: unpacked/{pak_name}/{relative_path}
                                original_file_path = unpacked_folder / str(epath).replace('\\', '/')
                                
                                if not original_file_path.exists():
                                    raise FileNotFoundError(f"Original file not found at: {original_file_path}")
                                
                                # Read original file from disk
                                with open(original_file_path, 'rb') as f:
                                    orig_data = f.read()
                                
                                orig_chunks = list(it.batched(orig_data, block_size_val))
                                orig_chunks = [bytes(c) if isinstance(c, tuple) else c for c in orig_chunks]
                                
                                unchanged_count = 0
                                changed_count = 0
                                
                                for idx in range(len(chunks)):
                                    # Compare this block with original
                                    if idx < len(orig_chunks) and chunks[idx] == orig_chunks[idx]:
                                        # UNCHANGED - can reuse original compressed block
                                        stored_idx = block_indices[idx] if idx < len(block_indices) else idx
                                        block = blocks[stored_idx]
                                        
                                        # Read the original compressed+encrypted block data from PAK
                                        orig_compressed = self._peek_block_content(block, encryption_method)
                                        
                                        block_reuse_decisions[idx] = (True, orig_compressed)
                                        unchanged_count += 1
                                    else:
                                        # CHANGED - must recompress
                                        block_reuse_decisions[idx] = (False, None)
                                        changed_count += 1
                                
                                print(f'   📊 Block analysis: ✅ {unchanged_count} unchanged (reuse), 🔄 {changed_count} changed (recompress)')
                                
                            except Exception as e:
                                print(f'   ⚠️  Could not analyze blocks: {e}')
                                print(f'   ⚠️  Falling back to recompressing all blocks')
                                # Fallback: recompress everything
                                block_reuse_decisions = {idx: (False, None) for idx in range(len(chunks))}
                            # ========== END BLOCK REUSE OPTIMIZATION ==========

                            compressed_chunks = []
                            all_fit = True
                            comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')

                            for idx, chunk in enumerate(chunks):
                                # idx is the logical chunk index; map to stored block index if needed
                                stored_idx = block_indices[idx] if idx < len(block_indices) else idx
                                block = blocks[stored_idx]
                                slot = block.end - block.start
                                usable_slot = slot
                                if eentry.encrypted:
                                    usable_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
                                orig_chunk_size = len(chunk)
                                print(f'      🔄 Block {idx}: {orig_chunk_size:,} bytes → Slot: {slot:,} bytes (must fit)')

                                result = None
                                level_used = -1

                                # ========== CHECK BLOCK REUSE DECISION ==========
                                should_reuse, orig_compressed = block_reuse_decisions.get(idx, (False, None))
                                
                                if should_reuse and orig_compressed:
                                    # Block unchanged - reuse original compressed data
                                    print(f'         ✅ UNCHANGED - Reusing original block ({len(orig_compressed):,} bytes, {(len(orig_compressed)/slot)*100:.1f}% of slot)')
                                    result = orig_compressed
                                    level_used = -1  # Original level
                                    
                                else:
                                    # Block changed - recompress
                                    print(f'         🔧 Compressing block...')

                                    # Recompress
                                    best_compressed = None
                                    best_size = float('inf')
                                    best_level = -1
                                    
                                    # Determine compression method details
                                    if compression_method == const.CM_ZLIB:
                                        comp_method_name = "ZLIB"
                                        max_level = 9
                                        level_step = 1  # Try every level
                                    elif compression_method in [const.CM_ZSTD, const.CM_ZSTD_DICT]:
                                        comp_method_name = "ZSTD" if compression_method == const.CM_ZSTD else "ZSTD_DICT"
                                        max_level = 22
                                        level_step = 1  # Try every level for better fit
                                    else:
                                        comp_method_name = "UNKNOWN"
                                        max_level = 9
                                        level_step = 1
                                    
                                    print(f'         🔧 Compressing with {comp_method_name} (trying levels 22→1)')
                                    
                                    attempts = 0
                                    for lvl in range(max_level, 0, -level_step):
                                        attempts += 1
                                        comp = None

                                        try:
                                            if compression_method == const.CM_ZLIB:
                                                actual_level = min(lvl, 9)
                                                comp = zlib.compress(chunk, level=actual_level)
                                                lvl_display = actual_level
                                            elif compression_method == const.CM_ZSTD:
                                                comp = ZstdCompressor(level=lvl).compress(chunk)
                                                lvl_display = lvl
                                            elif compression_method == const.CM_ZSTD_DICT and self._zstd_dict is not None:
                                                comp = ZstdCompressor(level=lvl, dict_data=self._zstd_dict).compress(chunk)
                                                lvl_display = lvl
                                            else:
                                                print(f'         ❌ Unknown compression method: {compression_method}')
                                                break

                                            if comp:
                                                comp_size = len(comp)
                                                slot_remaining = usable_slot - comp_size
                                                slot_usage = (comp_size / usable_slot) * 100
                                                
                                                fit_status = "✅" if comp_size <= usable_slot else "❌"
                                                
                                                print(f'         │ L{lvl_display:>2} │ {orig_chunk_size:>8,} → {comp_size:>8,} │ Slot: {usable_slot:>8,} ({slot_usage:>6.2f}%) │ Free: {slot_remaining:>7,} │ {fit_status}')
                                                
                                                if comp_size < best_size:
                                                    best_size = comp_size
                                                    best_compressed = comp
                                                    best_level = lvl_display

                                                if comp_size <= usable_slot:
                                                    result = comp
                                                    level_used = lvl_display
                                                    print(f'         └─> ✅ SUCCESS at Level {lvl_display}!')
                                                    break
                                        except Exception as e:
                                            print(f'         │ L{lvl:>2} │ ⚠️ ERROR: {str(e)}')
                                            continue

                                    if result is None:
                                        all_fit = False
                                        if best_compressed:
                                            overage = best_size - slot
                                            overage_pct = (overage / slot) * 100
                                            print(f'         └─> ❌ FAILED! Best: L{best_level} = {best_size:,} bytes (over by {overage:,} bytes / {overage_pct:.2f}%)')
                                        else:
                                            print(f'         └─> ❌ FAILED! No valid compression found')
                                        block_logger.add_block(idx, orig_chunk_size, best_size if best_compressed else orig_chunk_size, comp_method_str, best_level, False, block.start, block.end)
                                        break
                                # END of recompress block
                                
                                # Process the result (either reused or newly compressed)
                                # For reused blocks, result is already compressed+encrypted+padded from original
                                # For newly compressed blocks, we need to encrypt and pad
                                
                                if not should_reuse:
                                    # Newly compressed - need to encrypt and pad
                                    compressed_size_for_log = len(result)  # Store actual compressed size before padding
                                    
                                    if eentry.encrypted:
                                        cipher_slot = PakCrypto.align_encrypted_content_size(slot, encryption_method)
                                        if len(result) > cipher_slot:
                                            raise ValueError(f'Compressed data {len(result)} does not fit cipher slot {cipher_slot} (slot {slot})')
                                        padded_plain = result + b'\x00' * (cipher_slot - len(result))
                                        cipher = PakCrypto.encrypt_block(padded_plain, epath, encryption_method)
                                        if len(cipher) != cipher_slot:
                                            raise ValueError(f'Encrypted block size mismatch: got {len(cipher)} bytes, expected {cipher_slot}')
                                        result = cipher + b'\x00' * (slot - cipher_slot)
                                        print(f'         🔒 Encrypted: {len(result):,} bytes ({cipher_slot:,} encrypted + {slot - cipher_slot} pad)')
                                    else:
                                        # Unencrypted: pad to slot so we don't leave stale trailing bytes
                                        result = result + b'\x00' * (slot - len(result))

                                    # Log the ACTUAL compressed size and usable slot size, not the padded size
                                    block_logger.add_block(idx, orig_chunk_size, compressed_size_for_log, comp_method_str, level_used, True, block.start, block.start + usable_slot)
                                else:
                                    # Reused block - already compressed, encrypted, and padded
                                    # Just log it with original size
                                    block_logger.add_block(idx, orig_chunk_size, len(result), comp_method_str, -1, True, block.start, block.start + usable_slot)
                                
                                compressed_chunks.append((block.start, result))

                            if all_fit:
                                work_items.append((epath, compressed_chunks, True))
                                modified_targets.append((epath, eentry))
                                # For successful repacks, utilization is 100% (slot size / slot size)
                                logger.log_success(display_name, total_slot_size, total_slot_size)
                                success = True
                                break
                            else:
                                print('   ❌ Some blocks failed to fit')
                                logger.log_failure(display_name, 'Block compression failed', {'total_slot': total_slot_size})

                        # Print per-file block summary
                        if blocks:
                            block_logger.print_summary()

                    if not success:
                        print('   ⚠️ Repack failed for all candidates')
                
                # ============================================================
                # Process block-based files
                # ============================================================
                for parent_file_path, blocks_info in block_groups_by_parent.items():
                    print(f'\n🔍 Processing block-based file: {parent_file_path}')
                    console.print(f'   📦 Reassembling from {len(blocks_info)} blocks...')
                    
                    # Find the PAK entry for this parent file
                    parent_entry = None
                    parent_pak_path = None
                    
                    # Look for this file in the pak index
                    for dp, df in self._index.items():
                        for fn, ent in df.items():
                            full_pak_path = str(dp / fn).replace('\\', '/')
                            if full_pak_path == parent_file_path:
                                parent_entry = ent
                                parent_pak_path = dp / fn
                                break
                        if parent_entry:
                            break
                    
                    if not parent_entry:
                        console.print(f'   ❌ No PAK entry found for: {parent_file_path}')
                        logger.log_failure(Path(parent_file_path).name, 'No PAK entry found', {'path': parent_file_path})
                        continue
                    
                    # Get the expected block count from manifest
                    expected_block_count = 0
                    manifest_info = manifest_reader.find_file_info(parent_file_path, quiet_on_exact_match=True)
                    if manifest_info:
                        expected_block_count = manifest_info.get('num_blocks', 0)
                    
                    # Check if we have all expected blocks
                    if expected_block_count > 0 and len(blocks_info) != expected_block_count:
                        console.print(f'   ⚠️ Warning: Found {len(blocks_info)} blocks but expected {expected_block_count}')
                        console.print(f'   ℹ️ Make sure all block files are present in the edited folder')
                        
                        # List missing blocks
                        found_indices = [idx for idx, _, _ in blocks_info]
                        missing_indices = [i for i in range(expected_block_count) if i not in found_indices]
                        if missing_indices:
                            console.print(f'   ❌ Missing blocks: {missing_indices}')
                    
                    # Sort blocks by index
                    blocks_info.sort(key=lambda x: x[0])
                    
                    # Get PAK blocks info
                    pak_blocks = parent_entry.compressed_blocks
                    compression_method = parent_entry.compression_method
                    encryption_method = parent_entry.encryption_method
                    # Some encryption methods (SM4 variants) permute block ordering.
                    # Map logical block indices (block_N) to the stored block indices in the PAK.
                    block_indices = PakCrypto.generate_block_indices(len(pak_blocks), encryption_method)
                    
                    # SMART REUSE: Check each block file against original before assembly
                    block_reuse_decisions = {}  # block_idx -> (should_reuse, original_compressed_data)
                    
                    console.print(f'   🔍 Checking which blocks were actually modified...')
                    reused_count = 0
                    modified_count = 0
                    
                    for block_idx, block_file, expected_size in blocks_info:
                        if block_idx >= len(pak_blocks):
                            console.print(f'   ⚠️ Block {block_idx} index out of range')
                            block_reuse_decisions[block_idx] = (False, None)
                            modified_count += 1
                            continue
                        
                        stored_idx = block_indices[block_idx] if block_idx < len(block_indices) else block_idx
                        pak_block = pak_blocks[stored_idx]
                        
                        try:
                            # Read the block file
                            block_file_data = block_file.read_bytes()
                            
                            # Read original compressed block from PAK
                            orig_raw = self._peek_block_content(pak_block, encryption_method)
                            
                            # Decrypt if needed
                            if parent_entry.encrypted:
                                orig_comp = PakCrypto.decrypt_block(orig_raw, parent_pak_path, encryption_method)
                            else:
                                orig_comp = orig_raw
                            
                            # Decompress original to compare
                            orig_plain = PakCompression.decompress_block(orig_comp, self._zstd_dict, compression_method)
                            
                            # Compare with block file data
                            if orig_plain == block_file_data:
                                console.print(f'   ✅ Block {block_idx}: UNCHANGED - will reuse original ({len(orig_raw):,} bytes)')
                                block_reuse_decisions[block_idx] = (True, orig_raw)
                                reused_count += 1
                            else:
                                # Show detailed comparison for debugging
                                size_match = len(orig_plain) == len(block_file_data)
                                if size_match:
                                    # Find first difference
                                    first_diff = -1
                                    for i in range(len(orig_plain)):
                                        if orig_plain[i] != block_file_data[i]:
                                            first_diff = i
                                            break
                                    console.print(f'   🔧 Block {block_idx}: MODIFIED - will recompress (size OK, first diff at byte {first_diff})')
                                else:
                                    console.print(f'   🔧 Block {block_idx}: MODIFIED - will recompress (size: orig={len(orig_plain):,}, new={len(block_file_data):,})')
                                block_reuse_decisions[block_idx] = (False, None)
                                modified_count += 1
                        
                        except Exception as e:
                            console.print(f'   ⚠️ Block {block_idx}: Reuse check failed, will recompress - {e}')
                            block_reuse_decisions[block_idx] = (False, None)
                            modified_count += 1
                    
                    console.print(f'   📊 Summary: {reused_count} blocks to reuse, {modified_count} blocks to recompress')
                    
                    # Read all block files and assemble (still needed for modified blocks)
                    assembled_data = bytearray()
                    all_blocks_valid = True
                    
                    for block_idx, block_file, expected_size in blocks_info:
                        try:
                            block_data = block_file.read_bytes()
                            if expected_size > 0 and len(block_data) != expected_size:
                                console.print(f'   ⚠️ Block {block_idx} size mismatch: expected {expected_size:,}, got {len(block_data):,}')
                            assembled_data.extend(block_data)
                        except Exception as e:
                            console.print(f'   ❌ Error reading block {block_idx}: {e}')
                            all_blocks_valid = False
                            break
                    
                    if not all_blocks_valid:
                        console.print(f'   ❌ Failed to assemble blocks for {parent_file_path}')
                        continue
                    
                    assembled_bytes = bytes(assembled_data)
                    console.print(f'   ✅ Assembled: {len(assembled_bytes):,} bytes from {len(blocks_info)} blocks')
                    
                    # Check against expected uncompressed size
                    if manifest_info:
                        expected_size = manifest_info.get('uncompressed_size', 0)
                        if expected_size > 0 and len(assembled_bytes) != expected_size:
                            console.print(f'   ⚠️ Size mismatch: assembled {len(assembled_bytes):,} bytes but expected {expected_size:,}')
                    
                    # Now process this assembled file like a regular file
                    mod_name = Path(parent_file_path).name
                    
                    # Create per-file block logger
                    block_logger = BlockLogger(display_name)
                    
                    blocks = parent_entry.compressed_blocks
                    compression_method = parent_entry.compression_method
                    encryption_method = parent_entry.encryption_method if parent_entry.encrypted else 0
                    block_size_val = parent_entry.compression_block_size
                    
                    # Single-block (but assembled from multiple block files)
                    if len(blocks) == 1:
                        block = blocks[0]
                        slot = block.end - block.start
                        
                        comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')
                        enc_method_str = {0: 'NONE', 2: 'AES', 40: 'SM4'}.get(encryption_method, 'UNKNOWN')
                        
                        print(f'   ╔═══════════════════════════════════════════════════════════════════════════════')
                        print(f'   ║ 📄 SINGLE-BLOCK FILE COMPRESSION (FROM BLOCKS)')
                        print(f'   ╠═══════════════════════════════════════════════════════════════════════════════')
                        print(f'   ║ File: {mod_name}')
                        print(f'   ║ Assembled size: {len(assembled_bytes):,} bytes')
                        print(f'   ║ Slot size: {slot:,} bytes')
                        print(f'   ║ Compression: {comp_method_str} (method {compression_method})')
                        print(f'   ║ Encryption: {enc_method_str} (method {encryption_method})')
                        print(f'   ╚═══════════════════════════════════════════════════════════════════════════════')

                        result = None
                        level_used = -1

                        # Try reuse original compressed data
                        try:
                            orig_raw = self._peek_block_content(block, encryption_method)
                            orig_size = len(orig_raw)
                            if parent_entry.encrypted:
                                orig_comp = PakCrypto.decrypt_block(orig_raw, parent_pak_path, encryption_method)
                            else:
                                orig_comp = orig_raw

                            orig_plain = PakCompression.decompress_block(
                                orig_comp, self._zstd_dict, compression_method
                            )

                            if orig_plain == assembled_bytes:
                                result = bytes(orig_raw)
                                reuse_pct = (orig_size / slot) * 100
                                print(f'   🔁 REUSED ORIGINAL: {orig_size:,}/{slot:,} bytes ({reuse_pct:.2f}% slot usage)')
                                block_logger.add_block(0, len(assembled_bytes), orig_size, comp_method_str, -1, True, block.start, block.end)
                        except Exception as e:
                            print(f'   ⚠️ Reuse failed: {e}')

                        # If not reusable, recompress
                        if result is None:
                            best_compressed = None
                            best_size = float('inf')
                            best_level = -1
                            
                            # Determine compression method details
                            if compression_method == const.CM_ZLIB:
                                comp_method_name = "ZLIB"
                                max_level = 9
                                level_step = 1
                            elif compression_method in [const.CM_ZSTD, const.CM_ZSTD_DICT]:
                                comp_method_name = "ZSTD" if compression_method == const.CM_ZSTD else "ZSTD_DICT"
                                max_level = 22
                                level_step = 1
                            else:
                                comp_method_name = "UNKNOWN"
                                max_level = 9
                                level_step = 1
                            
                            print(f'   🔧 Compressing with {comp_method_name} (max level: {max_level}, trying all levels)')
                            print(f'   📏 Original: {len(assembled_bytes):,} bytes, Target slot: {slot:,} bytes')
                            
                            attempts = 0
                            for lvl in range(max_level, 0, -level_step):
                                attempts += 1
                                comp = None

                                try:
                                    if compression_method == const.CM_ZLIB:
                                        actual_level = min(lvl, 9)
                                        comp = zlib.compress(assembled_bytes, level=actual_level)
                                        lvl_display = actual_level
                                    elif compression_method == const.CM_ZSTD:
                                        comp = ZstdCompressor(level=lvl).compress(assembled_bytes)
                                        lvl_display = lvl
                                    elif compression_method == const.CM_ZSTD_DICT and self._zstd_dict is not None:
                                        comp = ZstdCompressor(level=lvl, dict_data=self._zstd_dict).compress(assembled_bytes)
                                        lvl_display = lvl
                                    else:
                                        print(f'   ❌ Unknown compression method: {compression_method}')
                                        break

                                    if comp:
                                        comp_size = len(comp)
                                        ratio = (comp_size / len(assembled_bytes)) * 100
                                        savings = len(assembled_bytes) - comp_size
                                        slot_usage = (comp_size / usable_slot) * 100
                                        
                                        fit_status = "✅ FIT" if comp_size <= slot else "❌ TOO BIG"
                                        
                                        print(f'   │ Attempt {attempts}: Level {lvl_display:>2} │ {len(assembled_bytes):>8,} → {comp_size:>8,} bytes │ Ratio: {ratio:>6.2f}% │ Saved: {savings:>7,} │ Slot: {slot_usage:>6.2f}% │ {fit_status}')
                                        
                                        if comp_size < best_size:
                                            best_size = comp_size
                                            best_compressed = comp
                                            best_level = lvl_display

                                        if comp_size <= usable_slot:
                                            result = comp
                                            level_used = lvl_display
                                            print(f'   └─> ✅ SUCCESS! Compressed {len(assembled_bytes):,} → {comp_size:,} bytes using level {lvl_display} ({slot_usage:.2f}% slot usage)')
                                            break
                                except Exception as e:
                                    print(f'   │ Attempt {attempts}: Level {lvl:>2} │ ⚠️ ERROR: {str(e)}')
                                    continue

                            if result is None:
                                if best_compressed:
                                    overage = best_size - slot
                                    overage_pct = (overage / slot) * 100
                                    print(f'   └─> ❌ FAILED! Best compression: {best_size:,} bytes at level {best_level}')
                                    print(f'       Target slot: {slot:,} bytes')
                                    print(f'       Overage: {overage:,} bytes ({overage_pct:.2f}% over limit)')
                                    print(f'       Tried {attempts} compression levels')
                                logger.log_failure(display_name, 'Compression failed to fit', {'best_size': best_size, 'slot': slot})
                                continue

                            block_logger.add_block(0, len(assembled_bytes), len(result), comp_method_str, level_used, True, block.start, block.end)

                        # Always overwrite the full stored slot range (block-based single-block)
                        if parent_entry.encrypted:
                            if PakCrypto.align_encrypted_content_size(slot, encryption_method) != slot:
                                raise ValueError(f'Block slot size {slot} is not aligned for encryption method {encryption_method}')
                            padded_plain = result + b'\x00' * (slot - len(result))
                            result = PakCrypto.encrypt_block(padded_plain, parent_pak_path, encryption_method)
                            if len(result) != slot:
                                raise ValueError(f'Encrypted block size mismatch: got {len(result)} bytes, expected {slot}')
                            print(f'   🔒 Encrypted with {enc_method_str} (slot-sized): {len(result):,} bytes')
                        else:
                            result = result + b'\x00' * (slot - len(result))

                        work_items.append((parent_pak_path, [(block.start, result)], False))
                        modified_targets.append((parent_pak_path, parent_entry))
                        block_logger.print_summary()
                    
                    # Multi-block (from reassembled data)
                    else:
                        total_slot_size = sum((b.end - b.start for b in blocks))
                        block_size_kb = block_size_val / 1024
                        total_slot_kb = total_slot_size / 1024
                        mod_size_kb = len(assembled_bytes) / 1024
                        
                        comp_method_str = {0: 'NONE', 1: 'ZLIB', 6: 'ZSTD', 8: 'ZSTD_DICT'}.get(compression_method, 'UNKNOWN')
                        enc_method_str = {0: 'NONE', 2: 'AES', 40: 'SM4'}.get(encryption_method, 'UNKNOWN')
                        
                        print(f'   ╔═══════════════════════════════════════════════════════════════════════════════')
                        print(f'   ║ 📦 MULTI-BLOCK FILE COMPRESSION (FROM BLOCKS)')
                        print(f'   ╠═══════════════════════════════════════════════════════════════════════════════')
                        print(f'   ║ File: {mod_name}')
                        print(f'   ║ Assembled size: {len(assembled_bytes):,} bytes ({mod_size_kb:.2f} KB)')
                        print(f'   ║ Blocks: {len(blocks)} blocks × {block_size_val:,} bytes ({block_size_kb:.2f} KB per block)')
                        print(f'   ║ Total slot space: {total_slot_size:,} bytes ({total_slot_kb:.2f} KB)')
                        print(f'   ║ Compression: {comp_method_str} (method {compression_method})')
                        print(f'   ║ Encryption: {enc_method_str} (method {encryption_method})')
                        print(f'   ╚═══════════════════════════════════════════════════════════════════════════════')

                        chunks = list(it.batched(assembled_bytes, block_size_val))
                        chunks = [bytes(chunk) if isinstance(chunk, tuple) else chunk for chunk in chunks]
                        if len(chunks) > len(blocks):
                            print(f'   ❌ Too many chunks: {len(chunks)} > {len(blocks)} blocks')
                            logger.log_failure(display_name, 'Too many chunks', {'chunks': len(chunks), 'blocks': len(blocks)})
                            continue

                        compressed_chunks = []
                        all_fit = True
                        
                        # Build a map of which actual block indices we have
                        actual_block_indices = sorted(block_reuse_decisions.keys())
                        
                        # Process ALL blocks (0 to len(blocks)-1), not just chunks
                        for actual_block_idx in range(len(blocks)):
                            # actual_block_idx here is the logical block index (block_N). Map to stored index.
                            stored_idx = block_indices[actual_block_idx] if actual_block_idx < len(block_indices) else actual_block_idx
                            block = blocks[stored_idx]
                            slot = block.end - block.start
                            
                            # Check if we have this block in our reuse decisions
                            if actual_block_idx in block_reuse_decisions:
                                should_reuse, orig_compressed = block_reuse_decisions[actual_block_idx]
                                
                                if should_reuse and orig_compressed:
                                    # Reuse original
                                    result = bytes(orig_compressed)
                                    print(f'      🔄 Block {actual_block_idx}: ♻️  REUSED original ({len(result):,} bytes)')
                                    block_logger.add_block(actual_block_idx, block_size_val if actual_block_idx < len(chunks) else 0, len(result), comp_method_str + " (REUSED)", -1, True, block.start, block.end)
                                    compressed_chunks.append((block.start, result))
                                    continue
                                else:
                                    # Block was modified - get the chunk data
                                    # Find this block in chunks list
                                    chunk_idx = actual_block_indices.index(actual_block_idx) if actual_block_idx in actual_block_indices else -1
                                    if chunk_idx < 0 or chunk_idx >= len(chunks):
                                        print(f'      ⚠️ Block {actual_block_idx}: Data not found in chunks')
                                        all_fit = False
                                        break
                                    
                                    chunk = chunks[chunk_idx]
                                    orig_chunk_size = len(chunk)
                                    print(f'      🔄 Block {actual_block_idx}: {orig_chunk_size:,} bytes → Slot: {slot:,} bytes (must fit)')
                                    print(f'         🔁 Block modified, recompressing...')
                            else:
                                # Block not in edited folder - must reuse original
                                try:
                                    orig_raw = self._peek_block_content(block, encryption_method)
                                    result = bytes(orig_raw)
                                    print(f'      🔄 Block {actual_block_idx}: ♻️  AUTO-REUSED (not in edited folder, {len(result):,} bytes)')
                                    block_logger.add_block(actual_block_idx, block_size_val, len(result), comp_method_str + " (AUTO-REUSED)", -1, True, block.start, block.end)
                                    compressed_chunks.append((block.start, result))
                                    continue
                                except Exception as e:
                                    print(f'      ❌ Block {actual_block_idx}: Failed to reuse original - {e}')
                                    all_fit = False
                                    break

                            result = None
                            level_used = -1

                            # Recompress this chunk
                            best_compressed = None
                            best_size = float('inf')
                            best_level = -1
                            
                            if compression_method == const.CM_ZLIB:
                                comp_method_name = "ZLIB"
                                max_level = 9
                                level_step = 1
                            elif compression_method in [const.CM_ZSTD, const.CM_ZSTD_DICT]:
                                comp_method_name = "ZSTD" if compression_method == const.CM_ZSTD else "ZSTD_DICT"
                                max_level = 22
                                level_step = 1
                            else:
                                comp_method_name = "UNKNOWN"
                                max_level = 9
                                level_step = 1
                            
                            print(f'         🔧 Compressing with {comp_method_name} (trying levels 22→1)')
                            
                            attempts = 0
                            for lvl in range(max_level, 0, -level_step):
                                attempts += 1
                                comp = None

                                try:
                                    if compression_method == const.CM_ZLIB:
                                        actual_level = min(lvl, 9)
                                        comp = zlib.compress(chunk, level=actual_level)
                                        lvl_display = actual_level
                                    elif compression_method == const.CM_ZSTD:
                                        comp = ZstdCompressor(level=lvl).compress(chunk)
                                        lvl_display = lvl
                                    elif compression_method == const.CM_ZSTD_DICT and self._zstd_dict is not None:
                                        comp = ZstdCompressor(level=lvl, dict_data=self._zstd_dict).compress(chunk)
                                        lvl_display = lvl
                                    else:
                                        break

                                    if comp:
                                        comp_size = len(comp)
                                        slot_remaining = usable_slot - comp_size
                                        slot_usage = (comp_size / usable_slot) * 100
                                        
                                        fit_status = "✅" if comp_size <= usable_slot else "❌"
                                        
                                        print(f'         │ L{lvl_display:>2} │ {orig_chunk_size:>8,} → {comp_size:>8,} │ Slot: {usable_slot:>8,} ({slot_usage:>6.2f}%) │ Free: {slot_remaining:>7,} │ {fit_status}')
                                        
                                        if comp_size < best_size:
                                            best_size = comp_size
                                            best_compressed = comp
                                            best_level = lvl_display
                                        
                                        if comp_size <= usable_slot:
                                            result = comp
                                            level_used = lvl_display
                                            print(f'         └─> ✅ SUCCESS at Level {lvl_display}!')
                                            break
                                except Exception as e:
                                    print(f'         │ L{lvl:>2} │ ⚠️ ERROR: {str(e)}')
                                    continue

                            if result is None:
                                all_fit = False
                                if best_compressed:
                                    overage = best_size - slot
                                    overage_pct = (overage / slot) * 100
                                    print(f'         └─> ❌ FAILED! Best: L{best_level} = {best_size:,} bytes (over by {overage:,} bytes / {overage_pct:.2f}%)')
                                else:
                                    print(f'         └─> ❌ FAILED! No valid compression found')
                                block_logger.add_block(actual_block_idx, orig_chunk_size, best_size if best_compressed else orig_chunk_size, comp_method_str, best_level, False, block.start, block.end)
                                break

                            # Always overwrite the full stored slot range.
                            if parent_entry.encrypted:
                                if PakCrypto.align_encrypted_content_size(slot, encryption_method) != slot:
                                    raise ValueError(f'Block slot size {slot} is not aligned for encryption method {encryption_method}')
                                padded_plain = result + b'\x00' * (slot - len(result))
                                result = PakCrypto.encrypt_block(padded_plain, parent_pak_path, encryption_method)
                                if len(result) != slot:
                                    raise ValueError(f'Encrypted block size mismatch: got {len(result)} bytes, expected {slot}')
                            else:
                                result = result + b'\x00' * (slot - len(result))

                            block_logger.add_block(actual_block_idx, orig_chunk_size, len(result), comp_method_str, level_used, True, block.start, block.end)
                            compressed_chunks.append((block.start, result))

                        if all_fit:
                            work_items.append((parent_pak_path, compressed_chunks, True))
                            modified_targets.append((parent_pak_path, parent_entry))
                            # For successful repacks, utilization is 100%
                            logger.log_success(display_name, total_slot_size, total_slot_size)
                            block_logger.print_summary()
                        else:
                            print('   ❌ Some blocks failed to fit')
                            logger.log_failure(display_name, 'Block compression failed', {'total_slot': total_slot_size})

            if not work_items:
                print('\n⚠️ Nothing to repack')
                temp_pak.unlink(missing_ok=True)
            else:
                print(f'\n📝 Writing {len(work_items)} files...')

                try:
                    with open(temp_pak, 'r+b') as fp:
                        for entry_path, block_data, is_multi in work_items:
                            try:
                                for offset, data in block_data:
                                    fp.seek(offset)
                                    fp.write(data)

                                print(f'✅ {Path(entry_path).name}: {len(block_data)} block(s) written')
                            except Exception as e:
                                print(f'❌ Write error for {Path(entry_path).name}: {e}')

                    temp_pak.replace(output_pak)
                    print(f'\n✅ Repack Complete! Saved to: {output_pak}')

                    # -------------------- Integrity verification --------------------
                    # Re-open the repacked PAK and attempt to decrypt+decompress all modified entries.
                    # This catches common corruption causes (wrong block order, padding, size issues).
                    try:
                        with open(output_pak, 'rb') as vf:
                            vbuf = memoryview(vf.read())

                        ok = 0
                        bad = 0
                        for vpath, ventry in modified_targets:
                            try:
                                enc_m = ventry.encryption_method
                                comp_m = ventry.compression_method

                                if ventry.encrypted and enc_m == 17:
                                    raise ValueError('EM_UNKNOWN_17 not supported')

                                # Uncompressed
                                if comp_m == const.CM_NONE:
                                    sz = PakCrypto.align_encrypted_content_size(ventry.size, enc_m)
                                    data = vbuf[ventry.offset:][:sz]
                                    if ventry.encrypted:
                                        data = PakCrypto.decrypt_block(bytes(data), vpath, enc_m)
                                    plain = bytes(data)
                                else:
                                    parts = []
                                    for bi in PakCrypto.generate_block_indices(len(ventry.compressed_blocks), enc_m):
                                        b = ventry.compressed_blocks[bi]
                                        bsz = PakCrypto.align_encrypted_content_size(b.end - b.start, enc_m)
                                        blk = vbuf[b.start:][:bsz]
                                        blk_bytes = bytes(blk)
                                        if ventry.encrypted:
                                            blk_bytes = PakCrypto.decrypt_block(blk_bytes, vpath, enc_m)
                                        dec = PakCompression.decompress_block(blk_bytes, self._zstd_dict, comp_m)
                                        parts.append(dec)
                                    plain = b''.join(parts)

                                # Trim to declared uncompressed size for validation
                                if ventry.uncompressed_size and len(plain) >= ventry.uncompressed_size:
                                    plain = plain[:ventry.uncompressed_size]

                                if ventry.uncompressed_size and len(plain) != ventry.uncompressed_size:
                                    raise ValueError(f'Uncompressed size mismatch: got {len(plain)}, expected {ventry.uncompressed_size}')

                                ok += 1
                            except Exception as ve:
                                bad += 1
                                print(f'❌ Verify failed: {vpath} -> {ve}')

                        if bad == 0:
                            print(f'✅ Verification passed for {ok} modified entr(y/ies).')
                        else:
                            print(f'⚠️ Verification: {ok} passed, {bad} failed. The output PAK may be broken.')
                    except Exception as ve:
                        print(f'⚠️ Verification step failed to run: {ve}')
                    # ----------------------------------------------------------------

                    logger.print_summary()
                except Exception as e:
                    print(f'❌ File Error: {e}')

# ==================== SEARCH FUNCTIONS (FROM SEN_4_2) ====================

def search_text_in_files(folder_type: str, type_name: str):
    """Search for text content in unpacked files."""
    unpacked_dir = BASE_DIR / folder_type / 'UNPACKED'
    
    if not unpacked_dir.exists() or not any(unpacked_dir.iterdir()):
        console.print(Panel(
            f"[red]❌ No unpacked data found for {type_name}![/red]\n"
            f"[cyan]💡 Please unpack files first to use search functionality.[/cyan]",
            title="Error",
            border_style="red"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    # Get all unpacked folders
    folders = [d for d in unpacked_dir.iterdir() if d.is_dir()]
    
    if not folders:
        console.print(Panel(
            f"[red]❌ No unpacked folders found for {type_name}![/red]",
            title="Error",
            border_style="red"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    # Show folder selection
    table = Table(title=f"Select Unpacked Folder - {type_name}", box=box.SIMPLE, style="cyan")
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("Folder Name", style="white")
    table.add_column("Files Count", style="yellow")
    
    for i, folder in enumerate(folders, 1):
        file_count = len(list(folder.rglob("*"))) if folder.exists() else 0
        table.add_row(str(i), folder.name, str(file_count))
    
    console.print(table)
    
    try:
        choice = int(Prompt.ask(f"[white]Select folder to search in (1-{len(folders)})[/white]", console=console))
        if not 1 <= choice <= len(folders):
            console.print(Panel("[red]❌ Invalid selection[/red]", title="Error", border_style="red"))
            return
        
        selected_folder = folders[choice - 1]
        
        # Get search text
        search_text = Prompt.ask("[white]Enter text to search[/white]", console=console).strip()
        if not search_text:
            console.print(Panel("[red]❌ Search text cannot be empty[/red]", title="Error", border_style="red"))
            return
        
        console.print(Panel(
            f"[blue]🔍 Searching for: '{search_text}' in {selected_folder.name}[/blue]",
            title="Searching",
            border_style="blue"
        ))
        
        # Create search results folder
        search_results_dir = BASE_DIR / folder_type / 'SEARCH_RESULTS' / f"text_search_{search_text[:20]}"
        search_results_dir.mkdir(parents=True, exist_ok=True)
        
        # Search in files
        found_files = []
        total_files = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
            expand=True
        ) as progress:
            task_id = progress.add_task("[cyan]Searching files...", total=0)
            
            # First, count total files for progress
            file_list = list(selected_folder.rglob("*"))
            file_list = [f for f in file_list if f.is_file()]
            total_files = len(file_list)
            progress.update(task_id, total=total_files)
            
            for file_path in file_list:
                progress.update(task_id, description=f"[cyan]Searching: {file_path.name[:30]}...")
                
                try:
                    # Try to read as text file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if search_text.lower() in content.lower():
                            found_files.append(file_path)
                            
                            # Copy to search results
                            relative_path = file_path.relative_to(selected_folder)
                            dest_path = search_results_dir / relative_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file_path, dest_path)
                            
                except:
                    # If text reading fails, try binary search
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            if search_text.encode('utf-8', errors='ignore') in content:
                                found_files.append(file_path)
                                
                                # Copy to search results
                                relative_path = file_path.relative_to(selected_folder)
                                dest_path = search_results_dir / relative_path
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(file_path, dest_path)
                    except:
                        pass
                
                progress.update(task_id, advance=1)
        
        # Show results
        console.print(Panel(
            f"[green]✅ Search complete![/green]\n"
            f"[cyan]📁 Searched in: {selected_folder.name}[/cyan]\n"
            f"[cyan]🔍 Search text: '{search_text}'[/cyan]\n"
            f"[cyan]📄 Files searched: {total_files}[/cyan]\n"
            f"[cyan]✅ Files found: {len(found_files)}[/cyan]\n"
            f"[cyan]📂 Results saved to: {search_results_dir}[/cyan]",
            title="Search Results",
            border_style="green"
        ))
        
        if found_files:
            table = Table(title="Found Files", box=box.SIMPLE, style="green")
            table.add_column("No.", style="green", justify="center")
            table.add_column("File Name", style="white")
            table.add_column("Path", style="yellow")
            
            for i, file_path in enumerate(found_files[:20], 1):  # Show first 20 files
                relative_path = file_path.relative_to(selected_folder)
                table.add_row(str(i), file_path.name, str(relative_path))
            
            if len(found_files) > 20:
                table.add_row("...", f"... and {len(found_files) - 20} more files", "...")
            
            console.print(table)
        
    except ValueError:
        console.print(Panel("[red]❌ Invalid input[/red]", title="Error", border_style="red"))
    except Exception as e:
        console.print(Panel(f"[red]❌ Search failed: {e}[/red]", title="Error", border_style="red"))
        traceback.print_exc()
    
    Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

def search_files_by_name(folder_type: str, type_name: str):
    """Search for files by name in unpacked folders."""
    unpacked_dir = BASE_DIR / folder_type / 'UNPACKED'
    
    if not unpacked_dir.exists() or not any(unpacked_dir.iterdir()):
        console.print(Panel(
            f"[red]❌ No unpacked data found for {type_name}![/red]\n"
            f"[cyan]💡 Please unpack files first to use search functionality.[/cyan]",
            title="Error",
            border_style="red"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    # Get all unpacked folders
    folders = [d for d in unpacked_dir.iterdir() if d.is_dir()]
    
    if not folders:
        console.print(Panel(
            f"[red]❌ No unpacked folders found for {type_name}![/red]",
            title="Error",
            border_style="red"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    # Show folder selection
    table = Table(title=f"Select Unpacked Folder - {type_name}", box=box.SIMPLE, style="cyan")
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("Folder Name", style="white")
    table.add_column("Files Count", style="yellow")
    
    for i, folder in enumerate(folders, 1):
        file_count = len(list(folder.rglob("*"))) if folder.exists() else 0
        table.add_row(str(i), folder.name, str(file_count))
    
    console.print(table)
    
    try:
        choice = int(Prompt.ask(f"[white]Select folder to search in (1-{len(folders)})[/white]", console=console))
        if not 1 <= choice <= len(folders):
            console.print(Panel("[red]❌ Invalid selection[/red]", title="Error", border_style="red"))
            return
        
        selected_folder = folders[choice - 1]
        
        # Get search filename
        search_filename = Prompt.ask("[white]Enter filename to search (supports * wildcards)[/white]", console=console).strip()
        if not search_filename:
            console.print(Panel("[red]❌ Filename cannot be empty[/red]", title="Error", border_style="red"))
            return
        
        console.print(Panel(
            f"[blue]🔍 Searching for: '{search_filename}' in {selected_folder.name}[/blue]",
            title="Searching",
            border_style="blue"
        ))
        
        # Create search results folder
        search_results_dir = BASE_DIR / folder_type / 'SEARCH_RESULTS' / f"name_search_{search_filename[:20].replace('*', 'wildcard')}"
        search_results_dir.mkdir(parents=True, exist_ok=True)
        
        # Search for files
        found_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
            expand=True
        ) as progress:
            # Convert wildcard pattern to regex
            pattern = search_filename.replace('*', '.*')
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Get all files
            file_list = list(selected_folder.rglob("*"))
            file_list = [f for f in file_list if f.is_file()]
            total_files = len(file_list)
            
            task_id = progress.add_task("[cyan]Searching files...", total=total_files)
            
            for file_path in file_list:
                progress.update(task_id, description=f"[cyan]Searching: {file_path.name[:30]}...")
                
                # Check if filename matches pattern
                if regex.search(file_path.name):
                    found_files.append(file_path)
                    
                    # Copy to search results
                    relative_path = file_path.relative_to(selected_folder)
                    dest_path = search_results_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
                
                progress.update(task_id, advance=1)
        
        # Show results
        console.print(Panel(
            f"[green]✅ Search complete![/green]\n"
            f"[cyan]📁 Searched in: {selected_folder.name}[/cyan]\n"
            f"[cyan]🔍 Search pattern: '{search_filename}'[/cyan]\n"
            f"[cyan]📄 Files searched: {total_files}[/cyan]\n"
            f"[cyan]✅ Files found: {len(found_files)}[/cyan]\n"
            f"[cyan]📂 Results saved to: {search_results_dir}[/cyan]",
            title="Search Results",
            border_style="green"
        ))
        
        if found_files:
            table = Table(title="Found Files", box=box.SIMPLE, style="green")
            table.add_column("No.", style="green", justify="center")
            table.add_column("File Name", style="white")
            table.add_column("Path", style="yellow")
            table.add_column("Size", style="cyan")
            
            for i, file_path in enumerate(found_files[:20], 1):  # Show first 20 files
                relative_path = file_path.relative_to(selected_folder)
                size = file_path.stat().st_size
                size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB"
                table.add_row(str(i), file_path.name, str(relative_path), size_str)
            
            if len(found_files) > 20:
                table.add_row("...", f"... and {len(found_files) - 20} more files", "...", "...")
            
            console.print(table)
        else:
            console.print(Panel(
                f"[yellow]⚠ No files found matching pattern: '{search_filename}'[/yellow]",
                title="No Results",
                border_style="yellow"
            ))
        
    except ValueError:
        console.print(Panel("[red]❌ Invalid input[/red]", title="Error", border_style="red"))
    except Exception as e:
        console.print(Panel(f"[red]❌ Search failed: {e}[/red]", title="Error", border_style="red"))
        traceback.print_exc()
    
    Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

# ==================== COMPARE DAT FUNCTIONS (FROM SEN_4_2) ====================

import hashlib

def quick_block_fingerprint(pak_path: Path, entry):
    """
    Fast fingerprint using first 1KB of each compressed block
    No decrypt, no decompress
    """
    h = hashlib.md5()

    indices = PakCrypto.generate_block_indices(
        len(entry.compressed_blocks),
        entry.encryption_method
    )

    with open(pak_path, "rb") as f:
        for real_idx in indices:
            block = entry.compressed_blocks[real_idx]
            f.seek(block.start)

            size = block.end - block.start
            data = f.read(min(1024, size))  # sirf 1KB
            h.update(data)

    return h.digest()

def fast_compare_and_extract_with_choice(folder_type: str):
    """Fast PAK Compare + Smart Extract"""

    console.print(Panel(
        "[cyan]⚡ Fast PAK Compare + Smart Extract[/cyan]",
        title="Fast Compare",
        border_style="cyan"
    ))

    compare_dir = BASE_DIR / folder_type / "COMPARE_DAT"
    original_dir = compare_dir / "Original_PAK"
    modded_dir   = compare_dir / "Modded_PAK"
    output_dir   = compare_dir / "Modified_Files"

    for d in [original_dir, modded_dir, output_dir]:
        d.mkdir(parents=True, exist_ok=True)

    original_paks = list(original_dir.glob("*.pak"))
    modded_paks   = list(modded_dir.glob("*.pak"))

    if not original_paks or not modded_paks:
        console.print("[red]❌ Original / Modded PAK missing[/red]")
        Prompt.ask("Press Enter...", default="")
        return

    # ---------- PAK SELECTION ----------

    def choose_pak(paks, title):
        console.print(f"\n[cyan]{title}[/cyan]")
        for i, p in enumerate(paks, 1):
            console.print(f"  [{i}] {p.name}")
        try:
            idx = int(Prompt.ask("Select number")) - 1
            return paks[idx]
        except:
            return None

    orig_pak = choose_pak(original_paks, "Select Original PAK")
    if not orig_pak:
        return

    mod_pak = choose_pak(modded_paks, "Select Modded PAK")
    if not mod_pak:
        return

    console.print("\n[yellow]🔄 Loading PAK indexes...[/yellow]")
    orig = TencentPakFile(orig_pak)
    mod  = TencentPakFile(mod_pak)

    # ---------- MODE ----------

    console.print("\n[cyan]Extraction Mode[/cyan]")
    console.print("  1️⃣ Normal Unpack")
    console.print("  2️⃣ Chunk Unpack")

    mode = Prompt.ask(
        "Choose mode",
        choices=["1", "2"],
        default="1"
    )

    modified = []

    console.print("\n[yellow]⚡ Fast Comparing (metadata + fingerprint)...[/yellow]")

    for dir_path, orig_files in orig._index.items():
        mod_files = mod._index.get(dir_path)
        if not mod_files:
            continue

        for name, o_entry in orig_files.items():
            m_entry = mod_files.get(name)
            if not m_entry:
                continue

            same = True

            # ---- metadata checks ----
            if o_entry.uncompressed_size != m_entry.uncompressed_size:
                same = False

            elif len(o_entry.compressed_blocks) != len(m_entry.compressed_blocks):
                same = False

            else:
                for ob, mb in zip(o_entry.compressed_blocks, m_entry.compressed_blocks):
                    if (ob.end - ob.start) != (mb.end - mb.start):
                        same = False
                        break

            # ---- fingerprint fallback ----
            if same:
                orig_fp = quick_block_fingerprint(orig_pak, o_entry)
                mod_fp  = quick_block_fingerprint(mod_pak,  m_entry)

                if orig_fp == mod_fp:
                    continue
                else:
                    same = False

            if same:
                continue

            modified.append((dir_path, name, m_entry))

    if not modified:
        console.print("[green]✅ No modified files found[/green]")
        Prompt.ask("Press Enter...", default="")
        return

    console.print(
        f"[bold green]✅ Modified Files Found:[/] {len(modified)}\n"
        f"[cyan]Starting extraction...[/cyan]"
    )

    # ---------- EXTRACTION ----------

    for dir_path, name, entry in modified:

        # generate correct block order
        indices = PakCrypto.generate_block_indices(
            len(entry.compressed_blocks),
            entry.encryption_method
        )

        # ===== NORMAL UNPACK (SAFE) =====
        if mode == "1":
            full_data = b""

            with open(mod_pak, "rb") as f:
                for real_idx in indices:
                    block = entry.compressed_blocks[real_idx]
                    f.seek(block.start)

                    raw_size = block.end - block.start
                    if entry.encrypted:
                        read_size = PakCrypto.align_encrypted_content_size(
                            raw_size,
                            entry.encryption_method
                        )
                    else:
                        read_size = raw_size

                    data = f.read(read_size)

                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(
                            data,
                            Path(name),
                            entry.encryption_method
                        )

                    if entry.compression_method != const.CM_NONE:
                        data = PakCompression.decompress_block(
                            data,
                            mod._zstd_dict,
                            entry.compression_method
                        )

                    full_data += data

            out_path = output_dir / dir_path / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(full_data)

            console.print(f"[green]✔ Unpacked:[/] {name}")

        # ===== CHUNK UNPACK =====
        else:
            file_base = Path(name).stem
            file_ext  = Path(name).suffix

            chunk_dir = output_dir / "CHUNK_UNPACK" / file_base
            chunk_dir.mkdir(parents=True, exist_ok=True)

            with open(mod_pak, "rb") as f:
                for i, real_idx in enumerate(indices):

                    block = entry.compressed_blocks[real_idx]
                    f.seek(block.start)

                    raw_size = block.end - block.start
                    if entry.encrypted:
                        read_size = PakCrypto.align_encrypted_content_size(
                            raw_size,
                            entry.encryption_method
                        )
                    else:
                        read_size = raw_size

                    data = f.read(read_size)

                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(
                            data,
                            Path(name),
                            entry.encryption_method
                        )

                    if entry.compression_method != const.CM_NONE:
                        data = PakCompression.decompress_block(
                            data,
                            mod._zstd_dict,
                            entry.compression_method
                        )

                    out_file = chunk_dir / f"{file_base}_{i}{file_ext}"
                    out_file.write_bytes(data)

            console.print(f"[green]✔ Chunk Unpacked:[/] {name}")

    console.print(
        Panel(
            f"[bold green]🎉 DONE[/bold green]\n"
            f"[cyan]Modified Files Extracted:[/] {len(modified)}",
            border_style="green"
        )
    )

    Prompt.ask("[white]Press Enter to continue...[/white]", default="")

# ==================== AUTO 120FPS FUNCTIONS (FROM SEN_4_2) ====================

def create_auto_120fps(base_dir: Path, user_model: str) -> bool:
    """Create auto 120fps modification for the user's device model."""
    console.print(Panel(
        f"[blue]🎮 Creating Auto 120FPS for model: {user_model}[/blue]",
        title="Auto 120FPS",
        border_style="blue"
    ))
    
    # Define paths - using GAMEPATCH folder structure
    fps_mapping_source = base_dir / 'GAMEPATCH' / 'UNPACKED' / 'game_patch_4.2.0.20750' / 'ShadowTrackerExtra' / 'Content' / 'CSV' / 'Client120FPSMapping.uexp'
    fps_mapping_dest_dir = base_dir / 'GAMEPATCH' / 'EDITED' / 'Content' / 'CSV'
    fps_mapping_dest = fps_mapping_dest_dir / 'Client120FPSMapping.uexp'
    
    # Check if source file exists
    if not fps_mapping_source.exists():
        console.print(Panel(
            f"[red]❌ FPS mapping file not found: {fps_mapping_source}[/red]\n"
            f"[cyan]💡 Please make sure you have unpacked the game patch first using GAME PATCH TOOL.[/cyan]",
            title="Error",
            border_style="red"
        ))
        return False
    
    # Create destination directory
    fps_mapping_dest_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Read the original file
        with open(fps_mapping_source, 'rb') as f:
            data = bytearray(f.read())
        
        console.print("[cyan]🔍 Scanning for 120FPS models...[/cyan]")
        
        # List of known 120FPS models from the file structure
        known_120fps_models = [
            "Infinix X6871",
            "Infinix X6871", 
            "XT2507-2",
            "CPH2613",
            "CPH2661",
            "V2241HA",
            "RMX5061",
            "NX712J",
            "XT2301-5",
            "M381Q",
            "PGT-AN20",
            "NX733J",
            "23046RP50C",
            "PJJ110",
            "24069PC21G",
            "NP03J",
            "NX769J",
            "V2332A",
            "A024",
            "OPD2415",
            "RMX5061",
            "PGFM10",
            "V2337A",
            "V2359A",
            "V2366GA",
            "V2217A",
            "PJD110",
            "PKC110",
            "PJE110",
            "25010PN30G",
            "24129PN74G",
            "A065",
            "SM-S926B",
            "A001",
            "Infinix X6871",
            "Infinix X6871",
            "A059",
            "Infinix X6871",
            "V2243A",
            "RMX5032",
            "ASUS_AI2205_C",
            "MEIZU 20",
            "V2232A",
            "25010PN30C",
            "I2405",
            "PKX110",
            "PLM110",
            "PLE110",
            "24069PC21I",
            "SM-S721B",
            "XT2507-2",
            "RMX5085",
            "SM-S937B",
            "motorola edge 60 pro",
            "RMX5030",
            "RMX5210",
            "RMX3851",
            "PLG110"
        ]
        
        # Try to find and replace each known 120FPS model
        replacement_done = False
        
        for target_model in known_120fps_models:
            old_bytes = target_model.encode('utf-8')
            new_bytes = user_model.encode('utf-8')
            
            # Only replace if the new model is not longer than the old one
            if len(new_bytes) <= len(old_bytes) and old_bytes in data:
                # Find all occurrences
                start_index = 0
                found_count = 0
                
                while True:
                    index = data.find(old_bytes, start_index)
                    if index == -1:
                        break
                    
                    # Check if this is followed by 120FPS pattern (not 90FPS)
                    # Look ahead to see if this has 120|120 pattern
                    check_ahead = data[index + len(old_bytes):index + len(old_bytes) + 50]
                    
                    # Check for 120FPS pattern: usually followed by \x04\x00\x00\x00120\x08\x00\x00\x00120|120
                    if b'120' in check_ahead and b'90' not in check_ahead:
                        # Replace this occurrence
                        data[index:index + len(old_bytes)] = new_bytes + b'\x00' * (len(old_bytes) - len(new_bytes))
                        console.print(f"[green]✅ Replaced '{target_model}' with '{user_model}'[/green]")
                        replacement_done = True
                        found_count += 1
                        break
                    
                    start_index = index + 1
                
                if replacement_done:
                    break
        
        if not replacement_done:
            console.print("[yellow]⚠ No suitable 120FPS model found for replacement[/yellow]")
            console.print("[cyan]🔄 Trying alternative method...[/cyan]")
            
            # Alternative: Just find any model and replace it
            for target_model in known_120fps_models:
                old_bytes = target_model.encode('utf-8')
                new_bytes = user_model.encode('utf-8')
                
                if len(new_bytes) <= len(old_bytes) and old_bytes in data:
                    index = data.find(old_bytes)
                    if index != -1:
                        data[index:index + len(old_bytes)] = new_bytes + b'\x00' * (len(old_bytes) - len(new_bytes))
                        console.print(f"[green]✅ Replaced '{target_model}' with '{user_model}' (alternative method)[/green]")
                        replacement_done = True
                        break
        
        if not replacement_done:
            console.print("[red]❌ Could not find any model to replace[/red]")
            return False

        # Write modified file
        with open(fps_mapping_dest, 'wb') as f:
            f.write(data)
        
        console.print(f"[green]✅ Auto 120FPS file created: {fps_mapping_dest}[/green]")
        return True
        
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Failed to create Auto 120FPS: {e}[/red]",
            title="Error",
            border_style="red"
        ))
        traceback.print_exc()
        return False

def process_auto_120fps(base_dir: Path) -> None:
    """Process auto 120fps creation and automatic repacking."""
    console.print(Panel(
        "[blue]🎮 Auto 120FPS Feature[/blue]",
        title="120FPS Setup",
        border_style="blue"
    ))
    
    # Get user model
    user_model = Prompt.ask("[white]Enter your device model[/white]", console=console).strip()
    if not user_model:
        console.print(Panel("[red]❌ No model entered[/red]", title="Error", border_style="red"))
        return
    
    # Check if game patch is unpacked first
    unpacked_dir = base_dir / 'GAMEPATCH' / 'UNPACKED'
    if not unpacked_dir.exists() or not any(unpacked_dir.iterdir()):
        console.print(Panel(
            f"[red]❌ Game patch not unpacked![/red]\n"
            f"[cyan]💡 Please unpack game patch first using GAME PATCH TOOL option 1.[/cyan]",
            title="Error",
            border_style="red"
        ))
        return
    
    # Create auto 120fps modification
    if not create_auto_120fps(base_dir, user_model):
        return
    
    # Find game patch file for repacking
    input_dir = base_dir / 'GAMEPATCH' / 'INPUT'
    if not input_dir.exists():
        console.print(Panel(f"[red]❌ Input folder not found: {input_dir}[/red]", title="Error", border_style="red"))
        return
    
    possible_paks = list(input_dir.glob("*.pak"))
    candidates = [p for p in possible_paks if 'patch' in p.name.lower()]
    
    if not candidates:
        console.print(Panel(
            f"[red]❌ No game patch .pak files found in {input_dir}![/red]",
            title="Error",
            border_style="red"
        ))
        return
    
    # Use the first candidate or let user select
    pak_file = candidates[0]
    if len(candidates) > 1:
        table = Table(title="Game Patches", box=box.SIMPLE, style="cyan")
        table.add_column("No.", style="cyan", justify="center")
        table.add_column("File Name", style="white")
        for i, p in enumerate(candidates, 1):
            table.add_row(str(i), p.name)
        console.print(table)
        
        try:
            selection = int(Prompt.ask(f"[white]Select patch file (1-{len(candidates)})[/white]", console=console)) - 1
            if 0 <= selection < len(candidates):
                pak_file = candidates[selection]
            else:
                console.print(Panel("[red]❌ Invalid selection.[/red]", title="Error", border_style="red"))
                return
        except ValueError:
            console.print(Panel("[red]❌ Invalid input.[/red]", title="Error", border_style="red"))
            return
    
    # Auto repack
    mod_folder = base_dir / 'GAMEPATCH' / 'EDITED'
    output_pak = base_dir / 'GAMEPATCH' / 'REPACKED' / f"{pak_file.stem}.pak"
    
    console.print(Panel(
        f"[blue]🔄 Auto-repacking with 120FPS modification...[/blue]",
        title="Repacking",
        border_style="blue"
    ))
    
    try:
        pak_instance = TencentPakFile(pak_file, is_od=False)
        pak_instance.repack(mod_folder, output_pak)
        console.print(Panel(
            f"[green]✅ Auto 120FPS complete! Modified PAK saved to: {output_pak}[/green]",
            title="Success",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(f"[red]❌ Auto repack failed: {e}[/red]", title="Error", border_style="red"))
        traceback.print_exc()

# ==================== ANTIRESET OBB FUNCTIONS (FROM SEN_4_2) ====================

def create_antireset_directories():
    """Required directories banata hai"""
    base_dir = BASE_DIR / "ANTIRESET"
    org_dir = base_dir / "ORG_OBB"
    mod_dir = base_dir / "MODDED_OBB"
    
    for directory in [base_dir, org_dir, mod_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    return org_dir, mod_dir

def list_obb_files_antireset(directory, folder_name):
    """Specific directory mein .obb files list karta hai"""
    obb_files = [f for f in os.listdir(directory) if f.endswith('.obb')]
    
    if not obb_files:
        console.print(f"❌ [red]No .obb files found in {folder_name}[/red]")
        return None
    
    console.print(f"\n📂 [bold cyan]Available .obb files in {folder_name}:[/bold cyan]")
    for i, file in enumerate(obb_files, 1):
        file_path = os.path.join(directory, file)
        try:
            file_size = os.path.getsize(file_path)
            console.print(f"   {i}. {file} ({file_size} bytes - 0x{file_size:X})")
        except:
            console.print(f"   {i}. {file} (Size unknown)")
    
    return obb_files

def select_obb_file_antireset(obb_files, folder_name):
    """User ko .obb file select karne deta hai"""
    while True:
        try:
            choice = console.input(f"\n🔢 [cyan]Select .obb file from {folder_name} (enter number 1-{len(obb_files)}): [/cyan]")
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(obb_files):
                    return obb_files[choice_num - 1]
                else:
                    console.print(f"❌ [red]Please enter number between 1 and {len(obb_files)}[/red]")
            else:
                console.print("❌ [red]Please enter a valid number[/red]")
        except KeyboardInterrupt:
            return None

def get_file_size_antireset(file_path):
    """File ka size aur last offset return karta hai"""
    try:
        size = os.path.getsize(file_path)
        return size, hex(size)
    except Exception as e:
        console.print(f"❌ [red]Error reading file: {e}[/red]")
        return None, None

def read_org_obb_offset(org_file_path):
    """ORG OBB ka last offset read karta hai"""
    console.print(f"\n📖 [yellow]Reading ORG OBB file: {org_file_path}[/yellow]")
    
    org_size, org_offset = get_file_size_antireset(org_file_path)
    if org_size is None:
        return None
    
    console.print(f"📊 [green]ORG OBB Size: {org_size} bytes[/green]")
    console.print(f"🎯 [green]ORG OBB Last Offset: {org_offset}[/green]")
    
    return org_size

def process_modded_obb_antireset(mod_file_path, target_size):
    """MODDED OBB ko process karta hai aur ORG OBB jitna offset add karta hai"""
    try:
        current_size, current_offset = get_file_size_antireset(mod_file_path)
        if current_size is None:
            return False
        
        console.print(f"📁 [cyan]MODDED OBB Current Size: {current_size} bytes (0x{current_size:X})[/cyan]")
        console.print(f"🎯 [cyan]Target Size (from ORG OBB): {target_size} bytes (0x{target_size:X})[/cyan]")
        
        if current_size > target_size:
            console.print("ℹ️ [yellow]MODDED OBB is already larger than ORG OBB[/yellow]")
            return False
        
        if current_size == target_size:
            console.print("✅ [green]MODDED OBB already matches ORG OBB size[/green]")
            return False
        
        bytes_to_add = target_size - current_size
        console.print(f"📊 [yellow]Need to add {bytes_to_add} bytes (0x{bytes_to_add:X})[/yellow]")
        
        mb_to_add = bytes_to_add / (1024 * 1024)
        console.print(f"💾 [yellow]Approximately {mb_to_add:.2f} MB to be added[/yellow]")
        
        confirm = console.input(f"\n❓ [bold yellow]Add {bytes_to_add} bytes to MODDED OBB? (y/n): [/bold yellow]")
        if confirm.lower() != 'y':
            console.print("❌ [red]Operation cancelled[/red]")
            return False
        
        console.print("⏳ [cyan]Adding zero bytes to MODDED OBB...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Adding zero bytes...", total=bytes_to_add)
            
            with open(mod_file_path, 'ab') as f:
                chunk_size = 1024 * 1024
                remaining = bytes_to_add
                
                while remaining > 0:
                    chunk = min(chunk_size, remaining)
                    f.write(b'\x00' * chunk)
                    remaining -= chunk
                    progress.update(task, advance=chunk)
        
        console.print("\n✅ [green]Zero bytes added successfully![/green]")
        
        new_size, new_offset = get_file_size_antireset(mod_file_path)
        console.print(f"📁 [green]New MODDED OBB Size: {new_size} bytes (0x{new_size:X})[/green]")
        
        if new_size == target_size:
            console.print("🎉 [bold green]Success! MODDED OBB now matches ORG OBB size[/bold green]")
        else:
            console.print(f"⚠️ [yellow]Warning: Sizes don't match (Difference: {new_size - target_size} bytes)[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"❌ [red]Error processing MODDED OBB: {e}[/red]")
        return False

def copy_obb_to_modded_antireset(org_file_path, mod_dir, org_file_name):
    """ORG OBB ko MODDED OBB folder mein copy karta hai (optional)"""
    mod_file_path = os.path.join(mod_dir, org_file_name)
    
    if not os.path.exists(mod_file_path):
        copy_choice = console.input(f"\n❓ [yellow]Copy {org_file_name} to MODDED OBB folder? (y/n): [/yellow]")
        if copy_choice.lower() == 'y':
            try:
                import shutil
                shutil.copy2(org_file_path, mod_file_path)
                console.print(f"✅ [green]Copied {org_file_name} to MODDED OBB folder[/green]")
                return mod_file_path
            except Exception as e:
                console.print(f"❌ [red]Error copying file: {e}[/red]")
    
    return None

def antireset_obb_processor():
    """Main Antireset OBB Processor function"""
    console.print(Panel.fit(
        "🛡️  [bold cyan]ANTIRESET OBB PROCESSOR[/bold cyan] 🛡️",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print("📁 [bold yellow]ORG OBB:[/bold yellow] Original OBB files")
    console.print("🔧 [bold yellow]MODDED OBB:[/bold yellow] Files to be modified")
    console.print("=" * 55)
    
    org_dir, mod_dir = create_antireset_directories()
    
    console.print("\n" + "=" * 40)
    org_obb_files = list_obb_files_antireset(org_dir, "ORG OBB")
    if not org_obb_files:
        console.print("\n📝 [yellow]Please copy your original OBB files to 'ORG_OBB' folder[/yellow]")
        console.print(f"📍 [cyan]Location: {org_dir}[/cyan]")
        return
    
    selected_org_file = select_obb_file_antireset(org_obb_files, "ORG OBB")
    if not selected_org_file:
        return
    org_file_path = os.path.join(org_dir, selected_org_file)
    
    target_size = read_org_obb_offset(org_file_path)
    if target_size is None:
        return
    
    console.print("\n" + "=" * 40)
    mod_obb_files = list_obb_files_antireset(mod_dir, "MODDED OBB")
    
    if not mod_obb_files:
        mod_file_path = copy_obb_to_modded_antireset(org_file_path, mod_dir, selected_org_file)
        if not mod_file_path:
            console.print(f"\n📝 [yellow]Please copy your modded OBB file to 'MODDED_OBB' folder[/yellow]")
            console.print(f"📍 [cyan]Location: {mod_dir}[/cyan]")
            return
        mod_obb_files = [selected_org_file]
    else:
        selected_mod_file = select_obb_file_antireset(mod_obb_files, "MODDED OBB")
        if not selected_mod_file:
            return
        mod_file_path = os.path.join(mod_dir, selected_mod_file)
    
    console.print("\n" + "=" * 40)
    console.print("🔄 [bold yellow]Starting OBB Processing...[/bold yellow]")
    success = process_modded_obb_antireset(mod_file_path, target_size)
    
    if success:
        console.print(Panel.fit(
            f"🎊 [bold green]OPERATION COMPLETED SUCCESSFULLY![/bold green]\n\n"
            f"✅ ORG OBB: {selected_org_file} - {target_size} bytes\n"
            f"✅ MODDED OBB: {os.path.basename(mod_file_path)} - Now {target_size} bytes",
            border_style="green"
        ))
    else:
        console.print("\nℹ️ [yellow]No changes made to MODDED OBB[/yellow]")

# ==================== CHUNK REPACK FUNCTIONS (FROM SEN_4_2) ====================

def chunk_repack_extracted(pak_instance, edited_dir: Path, target_pak_path: Path):
    """Chunk Repack Helper"""

    console.print("[cyan]🧩 Chunk Repack (Per-Chunk Mode)[/cyan]")

    chunk_pattern = re.compile(r"^(?P<base>.+)_(?P<idx>\d+)(?P<ext>\.[^.]+)$")

    chunk_files = []
    for f in edited_dir.rglob("*"):
        if not f.is_file():
            continue
        m = chunk_pattern.match(f.name)
        if m:
            base_filename = m.group("base") + m.group("ext")
            chunk_index = int(m.group("idx"))
            chunk_files.append((f, base_filename, chunk_index))

    if not chunk_files:
        console.print("[yellow]⚠ No chunk files found in EDITED folder[/yellow]")
        return

    with open(target_pak_path, "r+b") as f_pak:

        for src_file, base_filename, chunk_index in chunk_files:

            found = False

            for dir_path, files in pak_instance._index.items():
                entry = files.get(base_filename)
                if not entry:
                    continue

                found = True
                console.print(
                    f"[yellow]-> CHUNK REPACK:[/] {base_filename} | Block #{chunk_index}"
                )

                # 🔥 IMPORTANT FIX STARTS HERE 🔥
                indices = PakCrypto.generate_block_indices(
                    len(entry.compressed_blocks),
                    entry.encryption_method
                )

                if chunk_index >= len(indices):
                    console.print(
                        f"[red]❌ Invalid chunk index {chunk_index} "
                        f"(max {len(indices)-1})[/red]"
                    )
                    break

                real_idx = indices[chunk_index]
                block_meta = entry.compressed_blocks[real_idx]
                max_space = block_meta.end - block_meta.start
                # 🔥 IMPORTANT FIX ENDS HERE 🔥

                plain_chunk = src_file.read_bytes()

                # 🔹 compress
                if entry.compression_method != const.CM_NONE:
                    comp_data = PakCompression.compress_block(
                        plain_chunk,
                        pak_instance._zstd_dict,
                        entry.compression_method
                    )
                else:
                    comp_data = plain_chunk

                # 🔹 encrypt
                if entry.encrypted:
                    comp_data = PakCrypto.encrypt_block(
                        comp_data,
                        Path(base_filename),
                        entry.encryption_method
                    )

                # 🔹 align DATA size (old tool behavior)
                aligned_len = PakCrypto.align_encrypted_content_size(
                    len(comp_data),
                    entry.encryption_method
                )

                # 🔥 retry ZLIB if overflow
                if aligned_len > max_space and entry.compression_method == const.CM_ZLIB:
                    for level in (9, 6, 3, 1):
                        tmp = zlib.compress(plain_chunk, level)
                        if entry.encrypted:
                            tmp = PakCrypto.encrypt_block(
                                tmp,
                                Path(base_filename),
                                entry.encryption_method
                            )

                        tmp_aligned = PakCrypto.align_encrypted_content_size(
                            len(tmp),
                            entry.encryption_method
                        )

                        if tmp_aligned <= max_space:
                            comp_data = tmp
                            aligned_len = tmp_aligned
                            break

                # 🔴 final size check
                if aligned_len > max_space:
                    console.print(
                        f"[yellow]⚠ Block too large "
                        f"({aligned_len} > {max_space}), skipping[/yellow]"
                    )
                    break

                # ✅ write block
                f_pak.seek(block_meta.start)
                f_pak.write(comp_data)

                if aligned_len > len(comp_data):
                    f_pak.write(b"\x00" * (aligned_len - len(comp_data)))

                console.print(
                    f"[green]✔ Repacked {base_filename} "
                    f"block #{chunk_index}[/green]"
                )
                break

            if not found:
                console.print(
                    f"[red]❌ Original file not found for {src_file.name}[/red]"
                )

def unpack_file_blocks_using_filename(folder_type: str):
    """Unpack File Using File Name"""

    console.print(
        f"[cyan]📦 Unpack File Using File Name[/cyan]\n"
        f"[white]Module:[/] {folder_type}"
    )

    # 🔹 select PAK
    pak_file = select_pak_file(folder_type, "Select PAK File")
    if not pak_file:
        return

    pak_file = Path(pak_file)
    pak_instance = TencentPakFile(pak_file)

    # 🔹 ask filename
    target_filename = Prompt.ask(
        "Enter exact file name (with extension)",
        console=console
    ).strip()

    if not target_filename:
        console.print("[red]❌ No filename entered[/red]")
        return

    # 🔹 ask mode
    console.print("\n[cyan]Extraction Mode[/cyan]")
    console.print("  1️⃣ Normal Extract")
    console.print("  2️⃣ Chunk Extract")

    mode = Prompt.ask(
        "Choose mode",
        choices=["1", "2"],
        default="2",
        console=console
    )

    output_root = BASE_DIR / folder_type / "CHUNK_UNPACK"
    found = False

    for dir_path, files in pak_instance._index.items():
        entry = files.get(target_filename)
        if not entry:
            continue

        found = True

        file_base = Path(target_filename).stem
        file_ext  = Path(target_filename).suffix

        indices = PakCrypto.generate_block_indices(
            len(entry.compressed_blocks),
            entry.encryption_method
        )

        # ==================================================
        # 🔹 MODE 1: NORMAL EXTRACT (FULL FILE)
        # ==================================================
        if mode == "1":
            out_path = output_root / target_filename
            out_path.parent.mkdir(parents=True, exist_ok=True)

            full_data = bytearray()

            with open(pak_file, "rb") as f_pak:
                for real_idx in indices:
                    block = entry.compressed_blocks[real_idx]
                    f_pak.seek(block.start)

                    raw_size = block.end - block.start

                    if entry.encrypted:
                        read_size = PakCrypto.align_encrypted_content_size(
                            raw_size,
                            entry.encryption_method
                        )
                    else:
                        read_size = raw_size

                    data = f_pak.read(read_size)

                    # decrypt
                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(
                            data,
                            Path(target_filename),
                            entry.encryption_method
                        )

                    # decompress
                    if entry.compression_method != const.CM_NONE:
                        data = PakCompression.decompress_block(
                            data,
                            pak_instance._zstd_dict,
                            entry.compression_method
                        )

                    full_data.extend(data)

            out_path.write_bytes(full_data)

            console.print(
                f"[bold green]✅ File Extracted:[/] {out_path}"
            )
            break

        # ==================================================
        # 🔹 MODE 2: CHUNK EXTRACT
        # ==================================================
        out_dir = output_root / file_base
        out_dir.mkdir(parents=True, exist_ok=True)

        with open(pak_file, "rb") as f_pak:
            for i, real_idx in enumerate(indices):

                block = entry.compressed_blocks[real_idx]
                f_pak.seek(block.start)

                raw_size = block.end - block.start

                if entry.encrypted:
                    read_size = PakCrypto.align_encrypted_content_size(
                        raw_size,
                        entry.encryption_method
                    )
                else:
                    read_size = raw_size

                data = f_pak.read(read_size)

                if entry.encrypted:
                    data = PakCrypto.decrypt_block(
                        data,
                        Path(target_filename),
                        entry.encryption_method
                    )

                if entry.compression_method != const.CM_NONE:
                    data = PakCompression.decompress_block(
                        data,
                        pak_instance._zstd_dict,
                        entry.compression_method
                    )

                out_file = out_dir / f"{file_base}_{i}{file_ext}"
                out_file.write_bytes(data)

                console.print(f"[green]✔ Extracted[/green] {out_file.name}")

        console.print(
            f"[bold green]✅ Total Blocks Extracted:[/] {len(indices)}\n"
            f"[cyan]📁 Output:[/] {out_dir}"
        )
        break

    if not found:
        console.print(
            f"[red]❌ File not found in PAK:[/] {target_filename}"
        )

    Prompt.ask(
        "[yellow]Press Enter to continue...[/yellow]",
        console=console,
        default=""
    )

def normal_then_chunk_repack(folder_type: str, type_name: str):
    """
    SAFE PIPELINE

    1) Normal Repack (existing function)
    2) Pick output pak from REPACKED
    3) Chunk Repack on that pak
    4) Delete temp normal pak
    """

    console.print("[cyan]💛 Non Chunk + Chunk Repack [/cyan]")

    # ---------------- STEP 1 ----------------
    console.print("[yellow]🔁 Step 1: Non Chunk Repack[/yellow]")
    handle_repack(folder_type, type_name)

    repacked_dir = BASE_DIR / folder_type / "REPACKED"
    if not repacked_dir.exists():
        console.print("[red]❌ REPACKED folder not found[/red]")
        Prompt.ask("Press Enter...", default="")
        return

    # 🔍 get latest pak (normal repack output)
    repacked_paks = sorted(
        repacked_dir.glob("*.pak"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not repacked_paks:
        console.print("[red]❌ No repacked PAK found[/red]")
        Prompt.ask("Press Enter...", default="")
        return

    normal_pak = repacked_paks[0]
    console.print(f"[green]✔ Normal Repack Output:[/] {normal_pak.name}")
    
    # ---------------- STEP 2 ----------------
    console.print("[yellow]🧩 Step 2: Chunk Repack[/yellow]")

    edited_dir = BASE_DIR / folder_type / "EDITED"
    if not edited_dir.exists() or not any(edited_dir.rglob("*")):
        console.print("[red]❌ EDITED folder empty[/red]")
        Prompt.ask("Press Enter...", default="")
        return

    final_pak = repacked_dir / normal_pak.name

    is_od_pack = folder_type == "OD_PAK"
    pak_instance = TencentPakFile(normal_pak, is_od=is_od_pack)

    chunk_repack_extracted(
        pak_instance,
        edited_dir,
        final_pak
    )

    console.print(Panel(
        f"[bold green]✅ Non Chunk + Chunk Repack Completed[/bold green]\n"
        f"[cyan]{final_pak.name}[/cyan]",
        border_style="green"
    ))

    Prompt.ask("[white]Press Enter to continue...[/white]", default="")

# ==================== FOLDER MANAGEMENT FUNCTIONS (FROM SEN_4_2) ====================

def create_folder_structure() -> None:
    """Create the required folder structure if not exists."""
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        console.print(Panel(
            f"[green]✅ Created main tool directory: {BASE_DIR}[/green]",
            title="Folder Setup",
            border_style="green"
        ))
    
    for main_folder, sub_folders in FOLDER_STRUCTURE.items():
        folder_path = BASE_DIR / main_folder
        if not folder_path.exists():
            folder_path.mkdir(exist_ok=True)
            console.print(f"[cyan]📁 Created folder: {main_folder}[/cyan]")
        
        for sub_folder in sub_folders:
            sub_path = folder_path / sub_folder
            if not sub_path.exists():
                sub_path.mkdir(exist_ok=True)
                console.print(f"[cyan]   └── Created subfolder: {sub_folder}[/cyan]")
    
    # Create COMPARE_DAT subfolders
    for main_folder in FOLDER_STRUCTURE.keys():
        if main_folder != 'ANTIRESET':
            compare_dir = BASE_DIR / main_folder / 'COMPARE_DAT'
            for sub_folder in ['Original_PAK', 'Modded_PAK', 'Modified_Files']:
                sub_path = compare_dir / sub_folder
                if not sub_path.exists():
                    sub_path.mkdir(parents=True, exist_ok=True)
    
    console.print(Panel(
        f"[green]✅ Folder structure created/verified in: {BASE_DIR}[/green]",
        title="Setup Complete",
        border_style="green"
    ))

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    """Display the tool banner with SUBHAN."""
    clear_screen()
    
    # Create custom banner with SUBHAN
    banner_text = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗   ██╗██████╗ ██╗  ██╗ █████╗ ███╗   ██╗      ║
║   ██╔════╝██║   ██║██╔══██╗██║  ██║██╔══██╗████╗  ██║      ║
║   ███████╗██║   ██║██████╔╝███████║███████║██╔██╗ ██║      ║
║   ╚════██║██║   ██║██╔══██╗██╔══██║██╔══██║██║╚██╗██║      ║
║   ███████║╚██████╔╝██████╔╝██║  ██║██║  ██║██║ ╚████║      ║
║   ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝      ║
║                                                              ║
║              ██████╗ █████╗ ██╗  ██╗                        ║
║              ██╔══██╗██╔══██╗██║ ██╔╝                        ║
║              ██████╔╝███████║█████╔╝                         ║
║              ██╔══██╗██╔══██║██╔═██╗                         ║
║              ██████╔╝██║  ██║██║  ██╗                        ║
║              ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                        ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║             PAK FILE MANAGER - ULTIMATE EDITION              ║
║         All PUBG Unpacker & Repacker Tool Updated V5.0       ║
╚══════════════════════════════════════════════════════════════╝
"""
    console.print(Text(banner_text, style="bold cyan"))

# ==================== PAK FILE SELECTION FUNCTIONS ====================

def get_pak_files(folder_type: str) -> list[Path]:
    """Get list of .pak files in the INPUT folder for the given type."""
    input_dir = BASE_DIR / folder_type / 'INPUT'
    if not input_dir.exists():
        return []
    return list(input_dir.glob("*.pak"))

def select_pak_file(folder_type: str, title: str) -> Path | None:
    """Show list of .pak files and let user select one."""
    pak_files = get_pak_files(folder_type)
    
    if not pak_files:
        console.print(Panel(
            f"[red]❌ No .pak files found in {BASE_DIR / folder_type / 'INPUT'}![/red]\n"
            f"[cyan]💡 Please place your .pak files in the INPUT folder.[/cyan]",
            title="Error",
            border_style="red"
        ))
        return None
    
    table = Table(title=title, box=box.SIMPLE, style="cyan")
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("File Name", style="white")
    table.add_column("Size", style="yellow")
    
    for i, pak_file in enumerate(pak_files, 1):
        size = pak_file.stat().st_size
        size_str = f"{size / (1024*1024):.1f} MB" if size > 1024*1024 else f"{size / 1024:.1f} KB"
        table.add_row(str(i), pak_file.name, size_str)
    
    table.add_row(str(len(pak_files) + 1), "Back to Menu", "")
    console.print(table)
    
    try:
        choice = int(Prompt.ask(f"[white]Select file (1-{len(pak_files) + 1})[/white]", console=console))
        if choice == len(pak_files) + 1:
            return None
        elif 1 <= choice <= len(pak_files):
            return pak_files[choice - 1]
        else:
            console.print(Panel("[red]❌ Invalid selection[/red]", title="Error", border_style="red"))
            return None
    except ValueError:
        console.print(Panel("[red]❌ Invalid input[/red]", title="Error", border_style="red"))
        return None

# ==================== MAIN HANDLER FUNCTIONS ====================

def handle_unpack(folder_type: str, type_name: str):
    """Handle unpack operation for a specific type."""
    pak_file = select_pak_file(folder_type, f"Unpack {type_name}")
    if not pak_file:
        return
    
    # Show unpack options
    console.print(Panel(
        f"[cyan]📦 Unpack Options for: {pak_file.name}[/cyan]",
        title="Unpack Mode",
        border_style="cyan"
    ))
    
    table = Table(title="Select Unpack Mode", box=box.SIMPLE, style="cyan")
    table.add_column("Option", style="cyan", justify="center")
    table.add_column("Mode", style="white")
    table.add_column("Description", style="yellow")
    table.add_row("1", "📁 Normal Unpack", "Original folder structure maintain karega")
    table.add_row("2", "📦 Block-Based Unpack", "Split files into .block_N files for easier editing")
    console.print(table)
    
    try:
        unpack_mode = Prompt.ask("[white]Select unpack mode (1-2)[/white]", console=console).strip()
    except KeyboardInterrupt:
        return
    
    if unpack_mode not in ["1", "2"]:
        console.print(Panel("[red]❌ Invalid option[/red]", title="Error", border_style="red"))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    output_folder = BASE_DIR / folder_type / 'UNPACKED' / pak_file.stem
    
    try:
        is_od_pack = folder_type == 'OD_PAK'
        use_blocks = (unpack_mode == "2")
        pak_instance = TencentPakFile(pak_file, is_od=is_od_pack)
        pak_instance.dump(output_folder, use_block_splitting=use_blocks)
        
        console.print(Panel(
            f"[green]✅ Unpack complete![/green]\n"
            f"[cyan]📁 Files extracted to: {output_folder}[/cyan]\n"
            f"[yellow]💡 Use the EDITED folder for modifications[/yellow]",
            title="Success",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(f"[red]❌ Unpack failed: {e}[/red]", title="Error", border_style="red"))
        traceback.print_exc()
    
    Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

def handle_repack(folder_type: str, type_name: str):
    """Handle repack operation for a specific type."""
    pak_file = select_pak_file(folder_type, f"Repack {type_name}")
    if not pak_file:
        return
    
    edited_folder = BASE_DIR / folder_type / 'EDITED'
    if not edited_folder.exists() or not any(edited_folder.rglob("*")):
        console.print(Panel(
            f"[red]❌ No edited files found in {edited_folder}![/red]\n"
            f"[cyan]💡 Place your edited files in the EDITED folder with the same structure as UNPACKED.[/cyan]",
            title="Error",
            border_style="red"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    output_pak = BASE_DIR / folder_type / 'REPACKED' / f"{pak_file.stem}.pak"
    output_pak.parent.mkdir(exist_ok=True)
    
    console.print(Panel(
        f"[blue]🔄 Repacking {pak_file.name}...[/blue]",
        title="Repacking",
        border_style="blue"
    ))
    
    try:
        is_od_pack = folder_type == 'OD_PAK'
        pak_instance = TencentPakFile(pak_file, is_od=is_od_pack)
        pak_instance.repack(edited_folder, output_pak)
        
        console.print(Panel(
            f"[green]✅ Repack complete![/green]\n"
            f"[cyan]📦 New PAK saved to: {output_pak}[/cyan]",
            title="Success",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(f"[red]❌ Repack failed: {e}[/red]", title="Error", border_style="red"))
        traceback.print_exc()
    
    Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

def handle_clear_data(folder_type: str, type_name: str):
    """Handle clearing unpacked data for a specific type."""
    unpacked_dir = BASE_DIR / folder_type / 'UNPACKED'
    
    if not unpacked_dir.exists() or not any(unpacked_dir.iterdir()):
        console.print(Panel(
            f"[yellow]⚠ No unpacked data found for {type_name}[/yellow]",
            title="Info",
            border_style="yellow"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    folders = [d for d in unpacked_dir.iterdir() if d.is_dir()]
    
    if not folders:
        console.print(Panel(
            f"[yellow]⚠ No unpacked folders found for {type_name}[/yellow]",
            title="Info",
            border_style="yellow"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    table = Table(title=f"Unpacked Data - {type_name}", box=box.SIMPLE, style="cyan")
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("Folder Name", style="white")
    
    for i, folder in enumerate(folders, 1):
        table.add_row(str(i), folder.name)
    
    table.add_row(str(len(folders) + 1), "Delete All")
    table.add_row(str(len(folders) + 2), "Back to Menu")
    
    console.print(table)
    
    try:
        choice = int(Prompt.ask(f"[white]Select option (1-{len(folders) + 2})[/white]", console=console))
        
        if choice == len(folders) + 2:
            return
        elif choice == len(folders) + 1:
            confirm = Prompt.ask(
                f"[red]Delete ALL unpacked data for {type_name}? (y/n)[/red]",
                choices=['y', 'n'],
                console=console
            ).lower()
            if confirm == 'y':
                for folder in folders:
                    try:
                        shutil.rmtree(folder)
                        console.print(f"[green]✅ Deleted: {folder.name}[/green]")
                    except Exception as e:
                        console.print(f"[red]❌ Failed to delete {folder.name}: {e}[/red]")
        elif 1 <= choice <= len(folders):
            folder = folders[choice - 1]
            confirm = Prompt.ask(
                f"[red]Delete {folder.name}? (y/n)[/red]",
                choices=['y', 'n'],
                console=console
            ).lower()
            if confirm == 'y':
                try:
                    shutil.rmtree(folder)
                    console.print(f"[green]✅ Deleted: {folder.name}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to delete {folder.name}: {e}[/red]")
        else:
            console.print(Panel("[red]❌ Invalid selection[/red]", title="Error", border_style="red"))
    except ValueError:
        console.print(Panel("[red]❌ Invalid input[/red]", title="Error", border_style="red"))
    
    Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

def repack_menu(folder_type: str, type_name: str):
    """Repack menu with multiple options"""

    console.print(Panel(
        "[cyan]Select Repack Mode[/cyan]",
        title="Repack Menu",
        border_style="cyan"
    ))

    table = Table(box=box.SIMPLE)
    table.add_column("Option", justify="center")
    table.add_column("Mode")
    table.add_row("1", "🔁 Normal Repack")
    table.add_row("2", "🧩 Chunk Repack")
    table.add_row("3", "💛 Normal + Chunk")
    console.print(table)

    choice = Prompt.ask(
        "Select option (1-3)",
        choices=["1", "2", "3"],
        console=console
    )

    # ==================================================
    # 🔁 OPTION 1: NORMAL REPACK
    # ==================================================
    if choice == "1":
        handle_repack(folder_type, type_name)
        Prompt.ask("Press Enter to continue...", console=console, default="")
        return

    # ==================================================
    # 🧩 OPTION 2: CHUNK ONLY REPACK
    # ==================================================
    if choice == "2":
        pak_file = select_pak_file(folder_type, f"Chunk Repack {type_name}")
        if not pak_file:
            return

        pak_file = Path(pak_file)

        edited_folder = BASE_DIR / folder_type / "EDITED"
        if not edited_folder.exists() or not any(edited_folder.rglob("*")):
            console.print(Panel(
                "[red]❌ EDITED folder empty hai[/red]",
                title="Error",
                border_style="red"
            ))
            Prompt.ask("Press Enter...", console=console, default="")
            return

        output_pak = BASE_DIR / folder_type / "REPACKED" / f"{pak_file.stem}.pak"
        output_pak.parent.mkdir(exist_ok=True)

        try:
            shutil.copy2(pak_file, output_pak)

            is_od_pack = folder_type == "OD_PAK"
            pak_instance = TencentPakFile(pak_file, is_od=is_od_pack)

            chunk_repack_extracted(
                pak_instance,
                edited_folder,
                output_pak
            )

            console.print(Panel(
                f"[green]✅ Chunk Repack Completed[/green]\n"
                f"[cyan]{output_pak.name}[/cyan]",
                title="Success",
                border_style="green"
            ))

        except Exception as e:
            console.print(Panel(
                f"[red]❌ Chunk Repack failed[/red]\n{e}",
                title="Error",
                border_style="red"
            ))

        Prompt.ask("Press Enter to continue...", console=console, default="")
        return

    # ==================================================
    # 💛 OPTION 3: NORMAL → CHUNK (SAFE PIPELINE)
    # ==================================================
    if choice == "3":
        normal_then_chunk_repack(folder_type, type_name)
        return

def show_type_menu(folder_type: str, type_name: str):
    """Show menu for a specific type (ZSDIC, MINI_OBB, etc.)"""
    while True:
        show_banner()
        
        console.print(Panel(
            f"[cyan]📂 Current Directory: {BASE_DIR / folder_type}[/cyan]",
            title=f"{type_name} Manager",
            border_style="cyan"
        ))
        
        table = Table(title=f"{type_name} Menu", box=box.SIMPLE, style="cyan")
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Action", style="white")
        table.add_row("1", "📤 UNPACK")
        table.add_row("2", "📥 REPACK")
        table.add_row("3", "🔄 COMPARE DAT FILES")
        table.add_row("4", "🔍 SEARCH TEXT IN FILES")
        table.add_row("5", "📁 SEARCH FILES BY NAME")
        table.add_row("6", "🗑 CLEAR UNPACK DATA")
        table.add_row("7", "📜 UNPACK CHUNK USING FILE NAME")
        table.add_row("0", "🔙 BACK TO MAIN MENU")
        console.print(table)
        
        try:
            choice = Prompt.ask("[white]Select option (1-7)[/white]", console=console).strip()
        except KeyboardInterrupt:
            break
            
        if choice == "1":
            handle_unpack(folder_type, type_name)
        elif choice == "2":
            repack_menu(folder_type, type_name)
        elif choice == "3":
            fast_compare_and_extract_with_choice(folder_type)
        elif choice == "4":
            search_text_in_files(folder_type, type_name)
        elif choice == "5":
            search_files_by_name(folder_type, type_name)
        elif choice == "6":
            handle_clear_data(folder_type, type_name)
        elif choice == "7":
            unpack_file_blocks_using_filename(folder_type)
        elif choice == "0":
            break
        else:
            console.print(Panel("[red]❌ Invalid option[/red]", title="Error", border_style="red"))
            Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

def handle_auto_120fps():
    """Handle Auto 120 FPS feature."""
    show_banner()
    
    # Check prerequisites
    gamepatch_input = BASE_DIR / 'GAMEPATCH' / 'INPUT'
    gamepatch_unpacked = BASE_DIR / 'GAMEPATCH' / 'UNPACKED'
    
    if not any(gamepatch_input.glob("*.pak")):
        console.print(Panel(
            f"[red]❌ No game patch files found![/red]\n"
            f"[cyan]💡 Please place game patch .pak files in {gamepatch_input} first.[/cyan]",
            title="Error",
            border_style="red"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        return
    
    if not gamepatch_unpacked.exists() or not any(gamepatch_unpacked.iterdir()):
        console.print(Panel(
            f"[red]❌ Game patch not unpacked![/red]\n"
            f"[cyan]💡 Please unpack game patch first using GAME PATCH TOOL option 1.[/cyan]",
            title="Error",
            border_style="red"
        ))
        
        # Ask if user wants to unpack now
        unpack_now = Prompt.ask(
            "[yellow]Do you want to unpack game patch now? (y/n)[/yellow]",
            choices=['y', 'n'],
            console=console
        ).lower()
        
        if unpack_now == 'y':
            # Auto-select and unpack the first game patch
            pak_files = list(gamepatch_input.glob("*.pak"))
            if pak_files:
                pak_file = pak_files[0]
                console.print(Panel(
                    f"[blue]📁 Auto-unpacking: {pak_file.name}[/blue]",
                    title="Unpacking",
                    border_style="blue"
                ))
                
                try:
                    pak_instance = TencentPakFile(pak_file, is_od=False)
                    output_folder = BASE_DIR / 'GAMEPATCH' / 'UNPACKED' / pak_file.stem
                    pak_instance.dump(output_folder)
                    console.print(Panel(
                        f"[green]✅ Unpack complete![/green]\n"
                        f"[cyan]📁 Files extracted to: {output_folder}[/cyan]",
                        title="Success",
                        border_style="green"
                    ))
                except Exception as e:
                    console.print(Panel(f"[red]❌ Unpack failed: {e}[/red]", title="Error", border_style="red"))
                    traceback.print_exc()
                    return
            else:
                console.print(Panel("[red]❌ No .pak files found[/red]", title="Error", border_style="red"))
                return
        else:
            return
    
    # Show Auto 120FPS options
    console.print(Panel(
        "[blue]🎮 Auto 120 FPS Feature[/blue]\n"
        "[yellow]This feature will modify game files to enable 120 FPS on your device.[/yellow]",
        title="Auto 120 FPS",
        border_style="blue"
    ))
    
    table = Table(title="Auto 120FPS Options", box=box.SIMPLE, style="cyan")
    table.add_column("Option", style="cyan", justify="center")
    table.add_column("Action", style="white")
    table.add_row("1", " CREATE AUTO 120FPS MOD")
    table.add_row("2", " ABOUT AUTO 120FPS")
    table.add_row("0", " BACK TO MAIN MENU")
    console.print(table)
    
    try:
        choice = Prompt.ask("[white]Select option (1-3)[/white]", console=console).strip()
    except KeyboardInterrupt:
        return
    
    if choice == "1":
        process_auto_120fps(BASE_DIR)
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
    elif choice == "2":
        console.print(Panel(
            "[green]📖 Auto 120FPS Information[/green]\n\n"
            "[cyan]🎯 What it does:[/cyan]\n"
            "• Modifies the FPS mapping file to enable 120 FPS on your device\n"
            "• Replaces existing 120FPS-enabled device models with your model\n"
            "• Automatically repacks the game patch with the modification\n\n"
            "[cyan]📋 Requirements:[/cyan]\n"
            "• Game patch .pak file in GAMEPATCH/INPUT folder\n"
            "• Unpacked game patch in GAMEPATCH/UNPACKED folder\n"
            "• Your exact device model name\n\n"
            "[cyan]⚡ Supported Devices:[/cyan]\n"
            "• Various Samsung, Xiaomi, OPPO, Realme, Vivo devices\n"
            "• And many other 120FPS-capable devices\n\n"
            "[yellow]💡 Tip: Enter your exact device model as shown in settings[/yellow]",
            title="About Auto 120FPS",
            border_style="green"
        ))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
    elif choice == "0":
        return
    else:
        console.print(Panel("[red]❌ Invalid option[/red]", title="Error", border_style="red"))
        Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

def handle_antireset_tool():
    """Handle Antireset OBB Tool menu"""
    while True:
        show_banner()
        
        console.print(Panel(
            f"[cyan]📂 Current Directory: {BASE_DIR / 'ANTIRESET'}[/cyan]",
            title="✨ ANTIRESET OBB TOOL",
            border_style="cyan"
        ))
        
        table = Table(title="Antireset OBB Menu", box=box.SIMPLE, style="cyan")
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Action", style="white")
        table.add_row("1", " ANTIRESET OBB PROCESSOR")
        table.add_row("2", " ABOUT ANTIRESET TOOL")
        table.add_row("0", " BACK TO MAIN MENU")
        console.print(table)
        
        try:
            choice = Prompt.ask("[white]Select option (1-3)[/white]", console=console).strip()
        except KeyboardInterrupt:
            break
            
        if choice == "1":
            antireset_obb_processor()
            Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        elif choice == "2":
            console.print(Panel(
                "[green]📖 Antireset OBB Tool Information[/green]\n\n"
                "[cyan]🎯 What it does:[/cyan]\n"
                "• Prevents OBB file reset issues in PUBGM/All PUBG\n"
                "• Makes modded OBB files match original file size\n"
                "• Adds zero bytes padding to maintain file structure\n\n"
                "[cyan]📋 How to use:[/cyan]\n"
                "1. Place original OBB file in 'ORG_OBB' folder\n"
                "2. Place modded OBB file in 'MODDED_OBB' folder\n"
                "3. Run the Antireset OBB Processor\n"
                "4. Tool will automatically match file sizes\n\n"
                "[cyan]⚡ Benefits:[/cyan]\n"
                "• No more OBB file corruption\n"
                "• Stable modded OBB files\n"
                "• Prevents game from redownloading OBB\n\n"
                "[yellow]💡 Tip: Always backup your original OBB files[/yellow]",
                title="About Antireset Tool",
                border_style="green"
            ))
            Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")
        elif choice == "0":
            break
        else:
            console.print(Panel("[red]❌ Invalid option[/red]", title="Error", border_style="red"))
            Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function."""
    create_folder_structure()
    
    while True:
        show_banner()
        
        # Main menu with all options
        table = Table(title="Main Menu", box=box.SIMPLE, style="cyan")
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Tool", style="white")
        table.add_row("1", "🔧 ZSDIC TOOL")
        table.add_row("2", "📦 MINI OBB TOOL")
        table.add_row("3", "⚡ OD PAK TOOL")
        table.add_row("4", "🎮 GAME PATCH TOOL")
        table.add_row("5", "🚀 AUTO 120 FPS")
        table.add_row("6", "✨ ANTIRESET OBB TOOL")
        table.add_row("0", "❌ EXIT")
        console.print(table)
        
        try:
            choice = Prompt.ask("[white]Select option (1-7)[/white]", console=console).strip()
        except KeyboardInterrupt:
            console.print(Panel("[red]❌ Operation cancelled[/red]", title="Error", border_style="red"))
            break
            
        if choice == "1":
            show_type_menu('ZSDIC', 'ZSDIC TOOL')
        elif choice == "2":
            show_type_menu('MINI_OBB', 'MINI OBB TOOL')
        elif choice == "3":
            show_type_menu('OD_PAK', 'OD PAK TOOL')
        elif choice == "4":
            show_type_menu('GAMEPATCH', 'GAME PATCH TOOL')
        elif choice == "5":
            handle_auto_120fps()
        elif choice == "6":
            handle_antireset_tool()
        elif choice == "0":
            console.print(Panel("[green]🎉 Thank you for using SUBHAN PAK MANAGER![/green]", title="Goodbye", border_style="green"))
            break
        else:
            console.print(Panel("[red]❌ Invalid option[/red]", title="Error", border_style="red"))
            Prompt.ask("[white]Press Enter to continue...[/white]", console=console, default="")

if __name__ == "__main__":
    main()