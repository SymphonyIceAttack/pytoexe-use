import sys
import json
import time
import ctypes
import threading
import os
import requests
import re
import hashlib
import base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import webview
import wmi
import platform

import pymem
import pymem.process
import pymem.pattern

ntdll = ctypes.WinDLL('ntdll', use_last_error=True)

class IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [('Status', ctypes.c_int), ('Information', ctypes.c_void_p)]

NtWriteVirtualMemory = ntdll.NtWriteVirtualMemory
NtWriteVirtualMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(IO_STATUS_BLOCK)]
NtWriteVirtualMemory.restype = ctypes.c_int

MANUAL_OFFSETS = {
    'SimAdaptiveUseNewVelocityCriteria': 108776176,
    'InterpolationFrameVelocityThresholdMillionth': 108459896,
    'FullWindowMessages': 108711568,
    'RenderLocalLightFadeInMs': 108541544,
    'FixWallsOcclusion': 108805064,
    'RenderHighlightTransparency': 109010464,
    'HighlightOutlinesOnMobile': 109012272,
    'RenderPerformanceOverlay': 109010368,
    'DebugHighlightSpecificFont': 108792816,
    'LargeJohnson': 116695336,
    'BulletContactBreakChance': 116695472,
    'RagdollConstraintSolverIterationCount': 116695720,
    'FixRagdollSolverJank': 116696000,
    'DebugSimIntegrationStabilityTesting': 116695456,
    'SimFixAssemblyRadiusCalc': 112502439,
    'ISRLimitSimulationRadiusToNOUCount': 110805172
}

PATTERNS = [
    b"\x48\x83\xEC\x38\x48\x8B\x0D....\x4C\x8D\x05",
    b"\x48\x83\xEC\x38\x48\x8B\x0D....\x4C\x8D\x05",
    b"\x48\x83\xEC\x38\x48\x8B\x0D....\x4C\x8D\x05",
    b"\x48\x83\xEC\x28\x48\x8B\x0D....\xE8....\x48\x8B\x0D",
    b"\x48\x8B\x0D....\x48\x85\xC9\x74.\x48\x83\xC1",
]

FFLAG_LIST_PTR_OFFSET = 0x7B1F538

FNV_BASIS = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3

OFF_FFLAG_VALUE_PTR = 0xC0
OFF_MAP_END         = 0x00
OFF_MAP_LIST        = 0x10
OFF_MAP_MASK        = 0x28
OFF_ENTRY_FORWARD   = 0x08
OFF_ENTRY_STRING    = 0x10
OFF_ENTRY_GET_SET   = 0x30
OFF_STR_SIZE        = 0x10
OFF_STR_ALLOC       = 0x18

FFLAG_PREFIXES = {
    "DFString": 8,
    "FString":  7,
    "DFInt":    5,
    "FInt":     4,
    "DFLog":    5,
    "FLog":     4,
    "DFFlag":   6,
    "FFlag":    5,
}

DUMMY_VALUES = {0}

VALUE_OFFSETS = [
    0xA8, 0xB0, 0xB8, 0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8, 0xF0,
    0xF8, 0x100, 0x108, 0x110, 0x118, 0x120, 0x128, 0x130, 0x138,
    0x140, 0x148, 0x150, 0x158, 0x160, 0x168, 0x170, 0x178, 0x180
]

MAP_SIGNATURE  = 0x3F800000
DUMP_STRIDE    = 0x10
DUMP_NODE_OFF  = 0x00
LOG_BATCH_SIZE = 100

class KeySystem:
    def __init__(self):
        self.license_dir = os.path.join(os.path.expanduser("~"), ".Mango License")
        self.key_file = os.path.join(self.license_dir, "key")
        self.github_url = "https://raw.githubusercontent.com/azayan165-svg/keysystem2/refs/heads/main/keys.txt"
        self.validated = False
        
    def get_hwid(self):
        try:
            c = wmi.WMI()
            cpu_info = c.Win32_Processor()[0]
            disk_info = c.Win32_DiskDrive()[0]
            
            hwid_string = f"{cpu_info.ProcessorId}{disk_info.SerialNumber}{platform.node()}"
            hwid_hash = hashlib.sha256(hwid_string.encode()).hexdigest()
            return hwid_hash[:32]
        except:
            fallback = f"{platform.node()}{os.environ.get('COMPUTERNAME', '')}"
            return hashlib.sha256(fallback.encode()).hexdigest()[:32]
    
    def load_keys_from_github(self):
        try:
            response = requests.get(self.github_url, timeout=10)
            if response.status_code == 200:
                keys = {}
                for line in response.text.strip().split('\n'):
                    if ' - ' in line:
                        key, hwid = line.strip().split(' - ')
                        keys[key.strip()] = hwid.strip()
                return keys
        except:
            return {}
        return {}
    
    def validate_key(self, user_key):
        user_key = user_key.strip()
        keys = self.load_keys_from_github()
        
        if not keys:
            return False
        
        if user_key not in keys:
            return False
        
        expected_hwid = keys[user_key]
        current_hwid = self.get_hwid()
        
        if expected_hwid == current_hwid or expected_hwid == "*":
            self.save_license(user_key, current_hwid)
            self.validated = True
            return True
        
        return False
    
    def save_license(self, key, hwid):
        try:
            if not os.path.exists(self.license_dir):
                os.makedirs(self.license_dir)
            
            data = {
                'key': key,
                'hwid': hwid,
                'timestamp': datetime.now().isoformat()
            }
            
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode()).decode()
            
            with open(self.key_file, 'w') as f:
                f.write(encoded)
        except:
            pass
    
    def load_saved_license(self):
        try:
            if not os.path.exists(self.key_file):
                return None
            
            with open(self.key_file, 'r') as f:
                encoded = f.read().strip()
            
            json_str = base64.b64decode(encoded).decode()
            data = json.loads(json_str)
            
            return data
        except:
            return None
    
    def check_saved_license(self):
        saved = self.load_saved_license()
        if not saved:
            return False
        
        current_hwid = self.get_hwid()
        
        if saved['hwid'] != current_hwid:
            return False
        
        keys = self.load_keys_from_github()
        if saved['key'] not in keys:
            return False
        
        expected_hwid = keys[saved['key']]
        if expected_hwid != current_hwid and expected_hwid != "*":
            return False
        
        self.validated = True
        return True

def clean_flag_name(flag_name):
    for prefix in ["FFlag", "FInt", "FString", "FLog", "DFFlag", "DFInt", "DFString", "DFLog"]:
        if flag_name.startswith(prefix):
            return flag_name[len(prefix):]
    return flag_name

def find_roblox_processes():
    pids = []
    try:
        for p in pymem.process.list_processes():
            exe_name = p.szExeFile.decode('utf-8', 'ignore').lower()
            if p.th32ProcessID and 'robloxplayerbeta.exe' in exe_name:
                pids.append(p.th32ProcessID)
    except Exception:
        pass
    return pids

def get_module_base(pid):
    kernel32 = ctypes.windll.kernel32
    psapi    = ctypes.windll.psapi
    PROCESS_QUERY_INFORMATION = 1024
    PROCESS_VM_READ           = 16
    hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not hProcess:
        return None
    hModules = (ctypes.c_void_p * 1024)()
    cbNeeded = ctypes.c_size_t()
    if psapi.EnumProcessModules(hProcess, ctypes.byref(hModules), ctypes.sizeof(hModules), ctypes.byref(cbNeeded)):
        if cbNeeded.value >= ctypes.sizeof(ctypes.c_void_p):
            kernel32.CloseHandle(hProcess)
            return int(hModules[0])
    kernel32.CloseHandle(hProcess)
    return None

class LogBridge:
    def __init__(self):
        self.logs = []
        self.callbacks = []
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def log(self, msg, type="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'message': msg,
            'type': type
        }
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs.pop(0)
        
        for callback in self.callbacks:
            try:
                callback(log_entry)
            except:
                pass

class FFlagMonitor:
    def __init__(self, si, log_bridge):
        self.si = si
        self.log = log_bridge
        self.last_known_values = {}
        self.monitoring = False
        self.monitor_thread = None
        self.check_interval = 0.5
        self.injected_flags = []
        self.reinjected_count = 0
        self.reinjected_history = []
        self.show_reinject_messages = False

    def start_monitoring(self):
        if self.monitoring:
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False

    def update_injected_flags(self, flags):
        self.injected_flags = flags
        self.last_known_values.clear()
        self.reinjected_count = 0
        self.reinjected_history = []
        
        for flag in flags:
            try:
                name = flag["name"]
                clean = clean_flag_name(name)
                flag_type = flag.get("type", "string").lower()
                
                current_value = None
                if flag_type == "string":
                    current_value = self.si.get_string(clean)
                elif flag_type == "int":
                    val = self.si.get_int(clean)
                    if val is not None:
                        current_value = str(val)
                elif flag_type == "bool":
                    val = self.si.get_int(clean)
                    if val is not None:
                        current_value = "True" if val else "False"
                
                self.last_known_values[clean] = {
                    'desired': flag["value"],
                    'current': current_value if current_value is not None else flag["value"],
                    'type': flag_type,
                    'last_reinjected': time.time()
                }
            except Exception as e:
                if "reinject" not in str(e).lower():
                    self.log.log(f"Error initializing flag {flag.get('name', 'unknown')}: {e}", "error")
                self.last_known_values[clean_flag_name(flag["name"])] = {
                    'desired': flag["value"],
                    'current': flag["value"],
                    'type': flag.get("type", "string").lower(),
                    'last_reinjected': time.time()
                }

    def clear_injected_flags(self):
        self.injected_flags = []
        self.last_known_values = {}
        self.reinjected_count = 0
        self.reinjected_history = []

    def get_reinjected_count(self):
        return self.reinjected_count

    def _monitor_loop(self):
        time.sleep(2)
        while self.monitoring:
            try:
                if not self.injected_flags:
                    time.sleep(1)
                    continue
                if not self.si.pid or not self.si.h_process:
                    time.sleep(1)
                    continue
                self._check_and_fix_changes()
                time.sleep(self.check_interval)
            except Exception:
                time.sleep(5)

    def _check_and_fix_changes(self):
        flags_to_fix = []
        for flag in self.injected_flags:
            try:
                name = flag["name"]
                clean = clean_flag_name(name)
                desired_value = flag["value"]
                flag_type = flag.get("type", "string").lower()
                
                if clean not in self.last_known_values:
                    continue
                    
                current_value = None
                if flag_type == "string":
                    current_value = self.si.get_string(clean)
                elif flag_type == "int":
                    val = self.si.get_int(clean)
                    if val is not None:
                        current_value = str(val)
                elif flag_type == "bool":
                    val = self.si.get_int(clean)
                    if val is not None:
                        current_value = "True" if val else "False"
                    
                if current_value is None:
                    continue
                
                current_normalized = current_value.strip().lower() if isinstance(current_value, str) else current_value
                desired_normalized = desired_value.strip().lower() if isinstance(desired_value, str) else desired_value
                
                has_changed = False
                if flag_type == "bool":
                    current_bool = current_normalized in ("true", "1", "yes")
                    desired_bool = desired_normalized in ("true", "1", "yes")
                    has_changed = current_bool != desired_bool
                elif flag_type == "int":
                    try:
                        has_changed = int(current_normalized) != int(desired_normalized)
                    except (ValueError, TypeError):
                        has_changed = True
                else:
                    has_changed = current_value != desired_value
                    
                if has_changed:
                    if self.show_reinject_messages:
                        self.log.log(f"Flag {name} changed - reinjecting", "warning")
                    flags_to_fix.append(flag)
                    
            except Exception as e:
                if self.show_reinject_messages and "reinject" not in str(e).lower():
                    self.log.log(f"Error checking flag {flag.get('name', 'unknown')}: {e}", "error")
                continue
                
        for flag in flags_to_fix:
            try:
                if self._reinject_flag(flag):
                    self.reinjected_count += 1
                    self.reinjected_history.append({'name': flag['name'], 'timestamp': time.time()})
                    if self.show_reinject_messages:
                        self.log.log(f"Reinjected {flag['name']}", "success")
            except Exception as e:
                if self.show_reinject_messages and "reinject" not in str(e).lower():
                    self.log.log(f"Failed to reinject {flag.get('name', 'unknown')}: {e}", "error")
                continue

    def _reinject_flag(self, flag):
        name = flag["name"]
        clean = clean_flag_name(name)
        value = flag["value"]
        flag_type = flag.get("type", "string").lower()
        success = False
        
        try:
            if flag_type == "string":
                success = self.si.set_string(clean, value)
            elif flag_type == "int":
                success = self.si.set_int(clean, int(value))
            elif flag_type == "bool":
                bool_value = 1 if str(value).lower() in ("true", "1", "yes") else 0
                success = self.si.set_int(clean, bool_value)
                
            if success:
                self.last_known_values[clean]['current'] = value
                self.last_known_values[clean]['last_reinjected'] = time.time()
        except Exception as e:
            if self.show_reinject_messages and "reinject" not in str(e).lower():
                self.log.log(f"Reinjection error for {name}: {e}", "error")
            return False
            
        return success

class OffsetInjection:
    def __init__(self, pm, base, offsets, log_bridge):
        self.pm = pm
        self.base = base
        self.offsets = offsets
        self.log = log_bridge
        self.safe_mode = True

    def _parse_bool(self, value):
        return str(value).strip().lower() in ['true', '1']

    def _values_equal(self, current, desired, flag_type):
        if flag_type == 'bool':
            return self._parse_bool(current) == self._parse_bool(desired)
        if flag_type == 'int':
            return int(current) == int(desired)
        if flag_type in ['float', 'double']:
            return abs(float(current) - float(desired)) < 1e-06
        return str(current) == str(desired)

    def _read_memory(self, addr, flag_type):
        if flag_type == 'bool':
            return 'True' if self.pm.read_bool(addr) else 'False'
        elif flag_type == 'int':
            try:
                ptr = self.pm.read_ulonglong(addr)
                if ptr > 65536:
                    return str(self.pm.read_int(ptr))
            except:
                pass
            return str(self.pm.read_int(addr))
        elif flag_type in ('float', 'double'):
            return str(self.pm.read_float(addr))
        elif flag_type == 'string':
            try:
                ptr = self.pm.read_ulonglong(addr)
                target = ptr if ptr > 65536 else addr
                b = self.pm.read_bytes(target, 256)
                return b.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
            except:
                return ''
        else:
            raise RuntimeError('Read failed')

    def _write_memory(self, addr, value, flag_type, max_retries=3):
        backoff = 0.05
        for attempt in range(max_retries + 1):
            try:
                value_to_write = value
                original_int = None
                if self.safe_mode and flag_type in ['int', 'bool']:
                    try:
                        original_int = int(value)
                        value_to_write = original_int ^ 3735928559
                    except:
                        pass
                success = False
                if self.safe_mode and flag_type in ['int', 'bool', 'float']:
                    h_process = self.pm.process_handle
                    if h_process:
                        buffer = ctypes.c_byte * 8
                        data_buf = buffer()
                        size = 0
                        if flag_type == 'bool':
                            ctypes.memmove(data_buf, ctypes.byref(ctypes.c_bool(self._parse_bool(value_to_write))), 1)
                            size = 1
                        elif flag_type == 'int':
                            val = original_int if original_int is not None else int(value)
                            ctypes.memmove(data_buf, ctypes.byref(ctypes.c_int32(val)), 4)
                            size = 4
                        elif flag_type == 'float':
                            ctypes.memmove(data_buf, ctypes.byref(ctypes.c_float(float(value))), 4)
                            size = 4
                        io_status = IO_STATUS_BLOCK()
                        status = NtWriteVirtualMemory(h_process, addr, data_buf, size, ctypes.byref(io_status))
                        success = status == 0
                else:
                    if flag_type == 'bool':
                        self.pm.write_bool(addr, self._parse_bool(value_to_write))
                    elif flag_type == 'int':
                        ival = int(value_to_write) if self.safe_mode and original_int is not None else int(value)
                        try:
                            ptr = self.pm.read_ulonglong(addr)
                            self.pm.write_int(ptr if ptr > 65536 else addr, ival)
                        except:
                            self.pm.write_int(addr, ival)
                    elif flag_type in ['float', 'double']:
                        self.pm.write_float(addr, float(value))
                    elif flag_type == 'string':
                        b = str(value).encode('utf-8')[:255] + b'\x00'
                        try:
                            ptr = self.pm.read_ulonglong(addr)
                            self.pm.write_bytes(ptr if ptr > 65536 else addr, b, len(b))
                        except:
                            self.pm.write_bytes(addr, b, len(b))
                    success = True
                if self._values_equal(self._read_memory(addr, flag_type), value, flag_type):
                    return (True, None)
                else:
                    raise Exception('Verification failed')
            except Exception as e:
                if attempt == max_retries:
                    return (False, str(e))
            time.sleep(backoff)
            backoff *= 2
        return (False, 'Max retries exceeded')

class SingletonInjection:
    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_ALL_ACCESS = 0x1F0FFF

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),
            ("szExeFile", ctypes.c_char * 260),
        ]

    def __init__(self, log_bridge):
        self.k32 = ctypes.windll.kernel32
        self.pid = 0
        self.h_process = None
        self.pm = None
        self.module = None
        self.base = 0
        self.cached_singleton = 0
        self.flag_cache = {}
        self.log = log_bridge
        self._map_end = 0
        self._map_list = 0
        self._map_mask = 0
        self.default_values = {}

    def attach_with_handle(self, pid, pm, base):
        try:
            self.pid = pid
            self.pm = pm
            self.base = base
            self.h_process = pm.process_handle
            self.module = pymem.process.module_from_name(pm.process_handle, 'RobloxPlayerBeta.exe')
            return True
        except Exception:
            return False

    def attach(self, timeout_seconds: int = 120) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            pid = self._find_pid_via_snapshot("RobloxPlayerBeta.exe")
            if pid:
                h = self.k32.OpenProcess(self.PROCESS_ALL_ACCESS, False, pid)
                if h:
                    try:
                        pm = pymem.Pymem(pid)
                        mod = pymem.process.module_from_name(pm.process_handle, "RobloxPlayerBeta.exe")
                        self.pid = pid
                        self.h_process = h
                        self.pm = pm
                        self.module = mod
                        self.base = mod.lpBaseOfDll
                        return True
                    except Exception:
                        self.k32.CloseHandle(h)
            time.sleep(0.8)
        return False

    def _find_pid_via_snapshot(self, target: str) -> int:
        snap = self.k32.CreateToolhelp32Snapshot(self.TH32CS_SNAPPROCESS, 0)
        if snap == ctypes.c_void_p(-1).value:
            return 0
        entry = self.PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(self.PROCESSENTRY32)
        found = 0
        if self.k32.Process32First(snap, ctypes.byref(entry)):
            while True:
                if entry.szExeFile.decode("utf-8", errors="ignore").lower() == target.lower():
                    found = entry.th32ProcessID
                    break
                if not self.k32.Process32Next(snap, ctypes.byref(entry)):
                    break
        self.k32.CloseHandle(snap)
        return found

    def get_singleton(self) -> int:
        if self.cached_singleton:
            return self.cached_singleton
        for i, pattern in enumerate(PATTERNS):
            try:
                self.log.log(f"Trying pattern {i+1}/{len(PATTERNS)}...", "info")
                result = pymem.pattern.pattern_scan_module(self.pm.process_handle, self.module, pattern)
                if result:
                    if pattern[0] == 0x48 and pattern[1] == 0x83 and pattern[2] == 0xEC:
                        relative = self.pm.read_int(result + 7)
                        target = (result + 11) + relative
                    else:
                        relative = self.pm.read_int(result + 3)
                        target = (result + 7) + relative
                    self.cached_singleton = self.pm.read_ulonglong(target)
                    self.log.log(f"Found singleton at {hex(self.cached_singleton)}", "success")
                    return self.cached_singleton
            except:
                continue
        return 0

    def _get_map_header(self) -> bool:
        if self._map_mask:
            return True
        singleton = self.get_singleton()
        if not singleton:
            return False
        try:
            raw = self.pm.read_bytes(singleton + 8, 56)
        except Exception:
            return False
        end = int.from_bytes(raw[OFF_MAP_END: OFF_MAP_END + 8], "little")
        lst = int.from_bytes(raw[OFF_MAP_LIST: OFF_MAP_LIST + 8], "little")
        mask = int.from_bytes(raw[OFF_MAP_MASK: OFF_MAP_MASK + 8], "little")
        if mask == 0 or lst == 0:
            return False
        self._map_end = end
        self._map_list = lst
        self._map_mask = mask
        return True

    def find_flag(self, name: str) -> int:
        if name in self.flag_cache:
            return self.flag_cache[name]
        if not self._get_map_header():
            return 0
        h = FNV_BASIS
        for ch in name:
            h ^= ord(ch)
            h = (h * FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
        bucket_base = self._map_list + ((h & self._map_mask) * 16)
        try:
            node_ptr = int.from_bytes(self.pm.read_bytes(bucket_base, 16)[8:16], "little")
        except Exception:
            return 0
        if node_ptr == self._map_end:
            return 0
        visited = set()
        while node_ptr and node_ptr != self._map_end:
            if node_ptr in visited:
                break
            visited.add(node_ptr)
            try:
                entry = self.pm.read_bytes(node_ptr, 56)
            except Exception:
                break
            forward = int.from_bytes(entry[OFF_ENTRY_FORWARD: OFF_ENTRY_FORWARD + 8], "little")
            s = OFF_ENTRY_STRING
            str_size = int.from_bytes(entry[s + OFF_STR_SIZE: s + OFF_STR_SIZE + 8], "little")
            str_alloc = int.from_bytes(entry[s + OFF_STR_ALLOC: s + OFF_STR_ALLOC + 8], "little")
            try:
                if str_alloc > 0xF:
                    ptr = int.from_bytes(entry[s: s + 8], "little")
                    entry_name = self.pm.read_bytes(ptr, str_size).decode("utf-8", errors="ignore")
                else:
                    entry_name = entry[s: s + str_size].decode("utf-8", errors="ignore")
            except Exception:
                entry_name = ""
            if str_size == len(name) and entry_name == name:
                get_set = int.from_bytes(entry[OFF_ENTRY_GET_SET: OFF_ENTRY_GET_SET + 8], "little")
                self.flag_cache[name] = get_set
                return get_set
            if forward == 0 or forward == node_ptr:
                break
            node_ptr = forward
        return 0

    def _write_memory(self, address: int, data: bytes) -> bool:
        buf = (ctypes.c_char * len(data))(*data)
        written = ctypes.c_size_t(0)
        ok = self.k32.WriteProcessMemory(
            self.h_process, ctypes.c_void_p(address),
            buf, len(data), ctypes.byref(written),
        )
        return bool(ok) and written.value == len(data)

    def set_string(self, name: str, value: str) -> bool:
        addr = self.find_flag(name)
        if not addr:
            return False
        try:
            struct = self.pm.read_bytes(addr, 0xD0)
            value_inst = int.from_bytes(struct[OFF_FFLAG_VALUE_PTR: OFF_FFLAG_VALUE_PTR + 8], "little")
            if not value_inst:
                return False
            buf_ptr = self.pm.read_ulonglong(value_inst)
            capacity = self.pm.read_ulonglong(value_inst + 0x10)
            enc = value.encode("utf-8")
            if len(enc) > capacity:
                return False
            self._write_memory(buf_ptr, enc + b"\x00")
            self._write_memory(value_inst + 0x8, len(enc).to_bytes(8, "little"))
            return True
        except Exception:
            return False

    def set_int(self, name: str, value: int) -> bool:
        addr = self.find_flag(name)
        if not addr:
            return False
        try:
            struct = self.pm.read_bytes(addr, 0xD0)
            value_ptr = int.from_bytes(struct[OFF_FFLAG_VALUE_PTR: OFF_FFLAG_VALUE_PTR + 8], "little")
            if not value_ptr:
                return False
            self._write_memory(value_ptr, value.to_bytes(4, "little", signed=True))
            return True
        except Exception:
            return False

    def get_string(self, name: str):
        addr = self.find_flag(name)
        if not addr:
            return None
        try:
            struct = self.pm.read_bytes(addr, 0xD0)
            value_inst = int.from_bytes(struct[OFF_FFLAG_VALUE_PTR: OFF_FFLAG_VALUE_PTR + 8], 'little')
            if not value_inst:
                return None
            buffer_ptr = self.pm.read_ulonglong(value_inst)
            length = self.pm.read_ulonglong(value_inst + 0x8)
            if length > 0:
                return self.pm.read_string(buffer_ptr, int(length))
            return ""
        except:
            return None

    def get_int(self, name: str):
        addr = self.find_flag(name)
        if not addr:
            return None
        try:
            struct = self.pm.read_bytes(addr, 0xD0)
            value_ptr = int.from_bytes(struct[OFF_FFLAG_VALUE_PTR: OFF_FFLAG_VALUE_PTR + 8], 'little')
            if not value_ptr:
                return None
            return self.pm.read_int(value_ptr)
        except:
            return None

    def store_default_value(self, name: str):
        try:
            clean = clean_flag_name(name)
            addr = self.find_flag(clean)
            if not addr:
                return
                
            struct = self.pm.read_bytes(addr, 0xD0)
            flag_type_offset = 0xB8
            flag_type = int.from_bytes(struct[flag_type_offset:flag_type_offset+4], "little")
            
            if flag_type == 3:
                value = self.get_string(clean)
                if value is not None:
                    self.default_values[name] = {'type': 'string', 'value': value}
            elif flag_type == 1:
                value = self.get_int(clean)
                if value is not None:
                    self.default_values[name] = {'type': 'int', 'value': value}
            elif flag_type == 0:
                value = self.get_int(clean)
                if value is not None:
                    self.default_values[name] = {'type': 'bool', 'value': 'True' if value else 'False'}
        except:
            pass

    def restore_to_default(self, flags):
        success_count = 0
        for flag in flags:
            try:
                name = flag["name"]
                clean = clean_flag_name(name)
                
                if name in self.default_values:
                    default = self.default_values[name]
                    if default['type'] == 'string':
                        if self.set_string(clean, default['value']):
                            success_count += 1
                    elif default['type'] == 'int':
                        if self.set_int(clean, int(default['value'])):
                            success_count += 1
                    elif default['type'] == 'bool':
                        bool_val = 1 if str(default['value']).lower() == "true" else 0
                        if self.set_int(clean, bool_val):
                            success_count += 1
            except:
                continue
        return success_count

    def set_json_flags(self, json_str: str, progress_cb=None):
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return 0, 0, []

        ok = fail = 0
        total = len(data)
        done = 0
        failed_names = []
        injected_flags = []

        for raw_key, val in data.items():
            done += 1
            prefix_len = 0
            flag_type = "unknown"
            for prefix, strip_len in FFLAG_PREFIXES.items():
                if raw_key.startswith(prefix):
                    prefix_len = strip_len
                    flag_type = prefix
                    break

            clean = raw_key[prefix_len:] if prefix_len else raw_key
            val_s = str(val)

            self.store_default_value(raw_key)

            actual_type = "string"
            if flag_type in ("FFlag", "DFFlag"):
                actual_type = "bool"
            elif flag_type in ("FInt", "DFInt", "FLog", "DFLog"):
                actual_type = "int"
            elif flag_type in ("FString", "DFString"):
                actual_type = "string"
            else:
                if val_s.lower() in ("true", "false"):
                    actual_type = "bool"
                else:
                    try:
                        int(val_s)
                        actual_type = "int"
                    except:
                        actual_type = "string"

            if flag_type in ("FString", "DFString"):
                success = self.set_string(clean, val_s)
            elif flag_type in ("FInt", "DFInt", "FLog", "DFLog"):
                try:
                    success = self.set_int(clean, int(val))
                except (ValueError, TypeError):
                    success = False
            elif flag_type in ("FFlag", "DFFlag"):
                success = self.set_int(clean, 1 if val_s.lower() == "true" else 0)
            else:
                if val_s.lower() in ("true", "false"):
                    success = self.set_int(clean, 1 if val_s.lower() == "true" else 0)
                else:
                    try:
                        success = self.set_int(clean, int(val_s))
                    except (ValueError, TypeError):
                        success = self.set_string(clean, val_s)

            if success:
                ok += 1
                injected_flags.append({"name": raw_key, "value": val_s, "type": actual_type})
            else:
                fail += 1
                failed_names.append(raw_key)

            if progress_cb and done % LOG_BATCH_SIZE == 0:
                progress_cb(f"Progress: {done}/{total} ({int(done/total*100)}%) - {ok} ok, {fail} failed")

        if progress_cb:
            progress_cb(f"Final: {ok}/{total} flags applied, {fail} failed")

        return ok, fail, injected_flags

    def reset(self):
        self.flag_cache.clear()
        self.cached_singleton = 0
        self._map_end = 0
        self._map_list = 0
        self._map_mask = 0

class FFlagDumper:
    def __init__(self, singleton, log_bridge):
        self.si = singleton
        self.log = log_bridge
        self._map_end = 0
        self._map_list = 0
        self._map_mask = 0
        self.flags = {}
        self.flags_lock = threading.Lock()

    def _read_bytes(self, addr: int, size: int) -> bytes:
        try:
            return self.si.pm.read_bytes(addr, size)
        except Exception:
            return b""

    def _verify_singleton(self, addr: int) -> bool:
        try:
            data = self._read_bytes(addr + 8, 56)
            if len(data) < 56:
                return False
            map_end = int.from_bytes(data[OFF_MAP_END: OFF_MAP_END + 8], "little")
            map_list = int.from_bytes(data[OFF_MAP_LIST: OFF_MAP_LIST + 8], "little")
            map_mask = int.from_bytes(data[OFF_MAP_MASK: OFF_MAP_MASK + 8], "little")
            if map_mask > 0 and (map_mask & (map_mask + 1)) == 0:
                test = self._read_bytes(map_list, 16)
                if len(test) == 16:
                    return True
        except:
            pass
        return False

    def _get_map_from_singleton(self) -> bool:
        try:
            singleton = self.si.get_singleton()
            if not singleton:
                return False
            raw = self.si.pm.read_bytes(singleton + 8, 56)
            if len(raw) < 56:
                return False
            end = int.from_bytes(raw[OFF_MAP_END: OFF_MAP_END + 8], "little")
            lst = int.from_bytes(raw[OFF_MAP_LIST: OFF_MAP_LIST + 8], "little")
            mask = int.from_bytes(raw[OFF_MAP_MASK: OFF_MAP_MASK + 8], "little")
            if mask == 0 or lst == 0:
                return False
            self._map_end = end
            self._map_list = lst
            self._map_mask = mask
            self.log.log(f"Got map from singleton - buckets: {mask+1}, list: {hex(lst)}", "success")
            return True
        except Exception as e:
            self.log.log(f"Failed to get map from singleton: {e}", "error")
            return False

    def _find_map_via_signature(self) -> int:
        self.log.log("Scanning for map signature...", "info")
        scan_start = self.si.base + 0x7000000
        scan_end = self.si.base + 0x8000000
        chunk = 0x10000
        for addr in range(scan_start, scan_end, chunk):
            data = self._read_bytes(addr, chunk)
            if len(data) < 8:
                continue
            pos = 0
            while pos < len(data) - 8:
                val = int.from_bytes(data[pos:pos+8], "little")
                if val == MAP_SIGNATURE:
                    cand = addr + pos
                    try:
                        lst = self.si.pm.read_ulonglong(cand + 0x10)
                        mask = self.si.pm.read_ulonglong(cand + 0x28)
                        if lst > 0x10000 and mask > 0xFFF and (mask & (mask + 1)) == 0:
                            self.log.log(f"Map header at {hex(cand)} (mask={hex(mask)})", "success")
                            return cand
                    except:
                        pass
                pos += 1
        return 0

    def _process_node(self, node_ptr: int) -> int:
        try:
            entry = self._read_bytes(node_ptr, 64)
            if len(entry) < 56:
                return 0

            s = OFF_ENTRY_STRING
            str_size = int.from_bytes(entry[s + OFF_STR_SIZE: s + OFF_STR_SIZE + 8], "little")

            if not (2 <= str_size <= 100):
                return 0

            if str_size > 0xF:
                name_ptr = int.from_bytes(entry[s: s + 8], "little")
                name_bytes = self._read_bytes(name_ptr, min(str_size, 64))
            else:
                name_bytes = entry[s: s + str_size]

            name = name_bytes.decode("utf-8", errors="ignore").rstrip("\x00")
            if len(name) < 2:
                return 0

            getset = int.from_bytes(entry[OFF_ENTRY_GET_SET: OFF_ENTRY_GET_SET + 8], "little")
            if not getset:
                return 0

            getset_data = self._read_bytes(getset, 0x200)
            if len(getset_data) < 0x200:
                return 0

            found = 0
            for voff in VALUE_OFFSETS:
                try:
                    if voff + 8 > len(getset_data):
                        continue
                    val_ptr = int.from_bytes(getset_data[voff: voff + 8], "little")
                    if val_ptr == 0 or val_ptr in DUMMY_VALUES:
                        continue
                    rva = val_ptr - self.si.base
                    if 0x400000 <= rva < 0xB0000000:
                        clean = re.sub(r'[^a-zA-Z0-9]', '', name)
                        if clean:
                            with self.flags_lock:
                                if clean not in self.flags:
                                    self.flags[clean] = hex(rva)
                                    found += 1
                except:
                    continue
            return found
        except:
            return 0

    def dump(self) -> dict:
        self.flags = {}

        if not self._get_map_from_singleton():
            self.log.log("Could not get map from singleton", "error")
            return self.flags

        self.log.log("Dumping flags from map...", "info")

        table_size = (self._map_mask + 1) * 16
        table_data = self._read_bytes(self._map_list, table_size)

        if len(table_data) < table_size:
            self.log.log("Failed to read bucket table", "error")
            return self.flags

        nodes = []
        for i in range(self._map_mask + 1):
            offset = i * 16 + 8
            if offset + 8 > len(table_data):
                continue
            node_ptr = int.from_bytes(table_data[offset: offset + 8], "little")
            if node_ptr == 0 or node_ptr == self._map_end:
                continue

            current = node_ptr
            visited = set()
            while current and current != self._map_end:
                if current in visited or len(visited) > 50:
                    break
                visited.add(current)
                nodes.append(current)
                try:
                    entry = self._read_bytes(current, 64)
                    if len(entry) < 56:
                        break
                    forward = int.from_bytes(entry[OFF_ENTRY_FORWARD: OFF_ENTRY_FORWARD + 8], "little")
                    current = forward
                except:
                    break

        self.log.log(f"Processing {len(nodes)} nodes...", "info")

        flags_found = 0
        processed = 0
        batch_size = 100

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for node in nodes:
                if len(futures) >= batch_size:
                    for future in as_completed(futures):
                        flags_found += future.result()
                        processed += 1
                        if processed % 500 == 0:
                            self.log.log(f"Processed {processed}/{len(nodes)} nodes, found {flags_found} flags", "info")
                    futures = []
                futures.append(executor.submit(self._process_node, node))

            for future in as_completed(futures):
                flags_found += future.result()
                processed += 1
                if processed % 500 == 0:
                    self.log.log(f"Processed {processed}/{len(nodes)} nodes, found {flags_found} flags", "info")

        self.log.log(f"Found total of {flags_found} flags", "success")
        return self.flags

class HybridInjector:
    def __init__(self, log_bridge):
        self.log = log_bridge
        self.all_offsets = {}
        self.connected_processes = {}
        self._original_values = {}
        self.safe_mode = True
        self.current_injection_type = "Auto"

        self.singleton_injector = None
        self.offset_injector = None
        self.monitor = None
        self.monitoring_enabled = True

        self.auto_inject_pending = False
        self.pending_flags = []
        self.currently_injected_flags = []

        self._waiting_message_shown = False
        self.roblox_detected = False

        threading.Thread(target=self._monitor_roblox, daemon=True).start()

    def sync_offsets(self):
        url = 'https://raw.githubusercontent.com/azayan165-svg/fflags.hpp/refs/heads/main/fflags.hpp'
        try:
            r = requests.get(url, timeout=10)
            matches = re.findall(r'uintptr_t\s+(\w+)\s*=\s*(0x[0-9A-Fa-f]+);', r.text)
            online = {name: int(offset, 16) for name, offset in matches}
            final = online.copy()
            final.update(MANUAL_OFFSETS)
            self.all_offsets = final
            return len(final)
        except Exception:
            return 0

    def set_injection_type(self, type_name):
        self.current_injection_type = type_name

    def _monitor_roblox(self):
        while True:
            try:
                current_pids = find_roblox_processes()
                known_pids = set(self.connected_processes.keys())
                new_pids = set(current_pids) - known_pids
                lost_pids = known_pids - set(current_pids)

                for pid in lost_pids:
                    if pid in self.connected_processes:
                        del self.connected_processes[pid]
                    if not self.connected_processes:
                        self.roblox_detected = False

                for pid in new_pids:
                    try:
                        pm = pymem.Pymem(pid)
                        base = get_module_base(pid)
                        if base:
                            self.connected_processes[pid] = {'pm': pm, 'base': base}
                            self.offset_injector = OffsetInjection(pm, base, self.all_offsets, self.log)
                            self.singleton_injector = SingletonInjection(self.log)
                            self.singleton_injector.attach_with_handle(pid, pm, base)
                            self.monitor = FFlagMonitor(self.singleton_injector, self.log)
                            if self.monitoring_enabled:
                                self.monitor.start_monitoring()
                            
                            self.roblox_detected = True
                            self.log.log("Connected to Roblox", "success")
                            
                            if self.auto_inject_pending and self.pending_flags:
                                self.log.log("Roblox detected - auto-injecting flags...", "info")
                                threading.Thread(
                                    target=lambda: self._apply_flags_async(self.pending_flags),
                                    daemon=True
                                ).start()
                                self.auto_inject_pending = False
                    except Exception:
                        continue

                if not self.connected_processes and not self._waiting_message_shown:
                    self.log.log("Waiting for Roblox...", "info")
                    self._waiting_message_shown = True
                elif self.connected_processes and self._waiting_message_shown:
                    self._waiting_message_shown = False

            except Exception:
                pass
            time.sleep(2)

    def _apply_flags_async(self, flags):
        self.apply_flags(flags)

    def uninject_current(self):
        if not self.connected_processes:
            return {'success': 0, 'fail': 0, 'message': 'No Roblox process attached'}

        if self.currently_injected_flags and self.singleton_injector:
            self.log.log("Restoring flags to default state...", "info")
            
            restored = self.singleton_injector.restore_to_default(self.currently_injected_flags)
            
            self._original_values.clear()
            self.currently_injected_flags = []
            if self.monitor:
                self.monitor.clear_injected_flags()
                
            return {'success': restored, 'fail': len(self.currently_injected_flags) - restored, 'message': f'Restored {restored} flags to default'}
        
        return {'success': 0, 'fail': 0, 'message': 'No flags to uninject'}

    def apply_flags(self, flags):
        if not self.connected_processes:
            self.auto_inject_pending = True
            self.pending_flags = flags
            return {'success': 0, 'fail': len(flags), 'message': 'Roblox not attached. Will auto-inject when detected.'}

        if self.currently_injected_flags:
            self.uninject_current()
            if self.monitor:
                self.monitor.clear_injected_flags()

        if self.current_injection_type == "Auto":
            if self.singleton_injector and self.singleton_injector.get_singleton():
                result = self._apply_singleton(flags)
            elif self.offset_injector and self.all_offsets:
                result = self._apply_offset(flags)
            else:
                return {'success': 0, 'fail': len(flags), 'message': 'No injection method available'}
        elif self.current_injection_type == "Singleton":
            if self.singleton_injector:
                result = self._apply_singleton(flags)
            else:
                return {'success': 0, 'fail': len(flags), 'message': 'Singleton injector not available'}
        elif self.current_injection_type == "Offset":
            if self.offset_injector and self.all_offsets:
                result = self._apply_offset(flags)
            else:
                return {'success': 0, 'fail': len(flags), 'message': 'Offset injector not available'}

        if result['success'] > 0:
            self.currently_injected_flags = flags
        return result

    def _apply_singleton(self, flags):
        try:
            flags_json = {f['name']: f['value'] for f in flags}
            json_str = json.dumps(flags_json)
            ok, fail, injected = self.singleton_injector.set_json_flags(json_str, progress_cb=lambda msg: self.log.log(msg, "info"))
            if self.monitor and self.monitoring_enabled and ok > 0:
                self.monitor.update_injected_flags(injected)
                if not self.monitor.monitoring:
                    self.monitor.start_monitoring()
            return {'success': ok, 'fail': fail, 'message': 'Injected via Singleton'}
        except Exception as e:
            return {'success': 0, 'fail': len(flags), 'message': f'Error: {str(e)}'}

    def _apply_offset(self, flags):
        total_success = 0
        total_fail = 0
        injected_flags = []
        for pid, info in self.connected_processes.items():
            pm = info['pm']
            base = info['base']
            offset_inj = OffsetInjection(pm, base, self.all_offsets, self.log)
            for flag in flags:
                clean_name = clean_flag_name(flag['name'])
                if clean_name not in self.all_offsets:
                    total_fail += 1
                    continue
                addr = base + self.all_offsets[clean_name]
                value = flag['value']
                ftype = flag.get('type', 'string').lower()
                if flag['name'] not in self._original_values:
                    try:
                        if ftype == 'bool':
                            self._original_values[flag['name']] = 'True' if pm.read_bool(addr) else 'False'
                        elif ftype == 'int':
                            self._original_values[flag['name']] = str(pm.read_int(addr))
                    except:
                        pass
                ok, err = offset_inj._write_memory(addr, value, ftype)
                if ok:
                    total_success += 1
                    injected_flags.append(flag)
                else:
                    total_fail += 1
        return {'success': total_success, 'fail': total_fail, 'message': 'Injected via Offsets'}

    def uninject_flags(self):
        if not self.connected_processes or not self._original_values:
            return {'success': 0, 'fail': 0, 'message': 'No values to restore'}
        restore_flags = []
        for name, val in self._original_values.items():
            t = 'string'
            if val in ['True', 'False']:
                t = 'bool'
            elif val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                t = 'int'
            restore_flags.append({'name': name, 'value': val, 'type': t})
        if self.current_injection_type == "Auto":
            if self.singleton_injector and self.singleton_injector.get_singleton():
                result = self._apply_singleton(restore_flags)
            elif self.offset_injector and self.all_offsets:
                result = self._apply_offset(restore_flags)
            else:
                result = {'success': 0, 'fail': len(restore_flags), 'message': 'No injection method available'}
        elif self.current_injection_type == "Singleton":
            result = self._apply_singleton(restore_flags)
        else:
            result = self._apply_offset(restore_flags)
        self._original_values.clear()
        self.currently_injected_flags = []
        if self.monitor:
            self.monitor.clear_injected_flags()
        return result

    def toggle_monitoring(self):
        if not self.monitor:
            return False
        if self.monitor.monitoring:
            self.monitor.stop_monitoring()
            self.monitoring_enabled = False
        else:
            self.monitor.start_monitoring()
            self.monitoring_enabled = True
        return self.monitor.monitoring

    def get_reinjected_count(self):
        if self.monitor:
            return self.monitor.get_reinjected_count()
        return 0

class Api:
    def __init__(self, injector, log_bridge, key_system):
        self.injector = injector
        self.log = log_bridge
        self.key_system = key_system
        self._loaded_flags = None
        self._current_file = ""
        self.validated = False
        self.window = None

    def set_window(self, window):
        self.window = window

    def get_initial_state(self):
        return {
            'status': 'ready',
            'version': '1.0.0',
            'name': "Mango"
        }

    def check_validation(self):
        if self.key_system.check_saved_license():
            self.validated = True
            return {'validated': True}
        return {'validated': False}

    def validate_key(self, key):
        if self.key_system.validate_key(key):
            self.validated = True
            if self.window:
                time.sleep(1.5)
                self.window.load_html(APP_HTML)
            return {'success': True, 'message': 'Key validated successfully'}
        return {'success': False, 'message': 'Invalid key'}

    def get_hwid(self):
        return self.key_system.get_hwid()

    def sync_offsets(self):
        if not self.validated:
            return {'success': False, 'message': 'Not validated'}
        try:
            count = self.injector.sync_offsets()
            self.log.log(f"Synced {count} offsets", "success")
            return {'success': True, 'count': count}
        except Exception as e:
            self.log.log(f"Failed to sync offsets: {e}", "error")
            return {'success': False, 'error': str(e)}

    def get_status(self):
        if not self.validated:
            return {'connected': False, 'injection_type': 'Locked', 'reinjected_count': 0, 'flags_injected': 0}
        return {
            'connected': self.injector.roblox_detected,
            'injection_type': self.injector.current_injection_type,
            'reinjected_count': self.injector.get_reinjected_count(),
            'flags_injected': len(self.injector.currently_injected_flags)
        }

    def set_injection_type(self, type_name):
        if not self.validated:
            return {'success': False}
        self.injector.set_injection_type(type_name)
        self.log.log(f"Injection method set to: {type_name}", "info")
        return {'success': True}

    def load_flags(self, file_data, file_name):
        if not self.validated:
            return {'success': False}
        try:
            flags = json.loads(file_data)
            self._loaded_flags = flags
            self._current_file = file_name
            self.log.log(f"Loaded {len(flags)} flags from {file_name}", "success")
            return {'success': True, 'count': len(flags)}
        except Exception as e:
            self.log.log(f"Error loading flags: {e}", "error")
            return {'success': False, 'error': str(e)}

    def apply_flags(self):
        if not self.validated:
            return {'success': 0, 'fail': 0, 'message': 'Not validated'}
        if not self._loaded_flags:
            self.log.log("No flags loaded", "warning")
            return {'success': 0, 'fail': 0, 'message': 'No flags loaded'}
        
        try:
            flags_list = [{"name": k, "value": v} for k, v in self._loaded_flags.items()]
            result = self.injector.apply_flags(flags_list)
            if result['success'] > 0:
                self.log.log(f"Successfully injected {result['success']} flags", "success")
            else:
                self.log.log(result['message'], "warning")
            return result
        except Exception as e:
            self.log.log(f"Error applying flags: {e}", "error")
            return {'success': 0, 'fail': 0, 'message': str(e)}

    def uninject_all(self):
        if not self.validated:
            return {'success': 0}
        result = self.injector.uninject_current()
        if result['success'] > 0:
            self.log.log(f"Successfully restored {result['success']} flags to default", "success")
        else:
            self.log.log(result['message'], "info")
        return result

    def toggle_monitor(self):
        if not self.validated:
            return {'success': False, 'monitoring': False}
        if not self.injector.monitor:
            return {'success': False, 'monitoring': False}
        is_monitoring = self.injector.toggle_monitoring()
        status = "started" if is_monitoring else "stopped"
        self.log.log(f"Monitor {status}", "info")
        return {'success': True, 'monitoring': is_monitoring}

    def dump_flags(self):
        if not self.validated:
            return {'success': False}
        if not self.injector or not self.injector.singleton_injector:
            self.log.log("Not attached to Roblox yet", "error")
            return {'success': False, 'message': 'Not attached to Roblox'}

        def dump_worker():
            try:
                dumper = FFlagDumper(self.injector.singleton_injector, self.log)
                flags = dumper.dump()
                if flags:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    out_path = os.path.join(script_dir, "Mango_FFlags.txt")
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(f"// Dumped by Mango\n")
                        f.write(f"// Dumped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"// Total FFlags: {len(flags):,}\n\n")
                        f.write("#pragma once\n\n")
                        f.write("namespace FFlags \n\n{\n")
                        for name, addr in sorted(flags.items()):
                            f.write(f"    inline uintptr_t {name} = {addr};\n")
                        f.write("}")
                    self.log.log(f"Dumped {len(flags):,} flags -> Mango_FFlags.txt", "success")
                else:
                    self.log.log("No flags found", "warning")
            except Exception as e:
                self.log.log(f"Dump error: {e}", "error")

        threading.Thread(target=dump_worker, daemon=True).start()
        return {'success': True}

    def exit_app(self):
        if self.window:
            self.window.destroy()
        os._exit(0)

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mango</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        body {
            background: linear-gradient(145deg, #0B1120 0%, #1A2F4A 100%);
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        body::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }

        .login-container {
            width: 420px;
            background: rgba(18, 28, 46, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 32px;
            border: 1px solid rgba(255, 215, 0, 0.15);
            padding: 45px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 215, 0, 0.1) inset;
            position: relative;
            overflow: hidden;
            z-index: 1;
        }

        .login-container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255, 215, 0, 0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
            z-index: -1;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .mango-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            border-radius: 30px 30px 40px 40px;
            margin: 0 auto 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            box-shadow: 0 15px 30px -10px rgba(255, 215, 0, 0.3);
            color: #0B1120;
            font-size: 40px;
        }

        .mango-icon::before {
            content: '';
            position: absolute;
            top: -5px;
            left: 35px;
            width: 10px;
            height: 15px;
            background: #4CAF50;
            border-radius: 5px 5px 0 0;
            transform: rotate(-15deg);
        }

        .brand {
            text-align: center;
            margin-bottom: 35px;
        }

        .brand-name {
            font-size: 42px;
            font-weight: 800;
            background: linear-gradient(135deg, #FFD700, #FFB347);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            text-shadow: 0 5px 15px rgba(255, 215, 0, 0.2);
        }

        .brand-sub {
            color: #88B0D4;
            font-size: 14px;
            letter-spacing: 1px;
            font-weight: 400;
        }

        .input-group {
            margin-bottom: 25px;
        }

        .input-label {
            display: block;
            margin-bottom: 8px;
            color: #A0C0E0;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        .input-field {
            width: 100%;
            background: rgba(10, 20, 35, 0.6);
            border: 1px solid rgba(255, 215, 0, 0.2);
            color: #ffffff;
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 14px;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }

        .input-field:focus {
            outline: none;
            border-color: #FFD700;
            box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.1);
            background: rgba(20, 35, 55, 0.8);
        }

        .input-field::placeholder {
            color: #4A6380;
        }

        .btn {
            width: 100%;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            border: none;
            color: #0a1420;
            padding: 16px;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 10px 20px -8px rgba(255, 215, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px -8px rgba(255, 215, 0, 0.4);
            background: linear-gradient(135deg, #FFE55C, #FFB347);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.5;
            transform: none;
            box-shadow: none;
            cursor: not-allowed;
        }

        .status-message {
            text-align: center;
            font-size: 13px;
            min-height: 24px;
            margin-top: 15px;
            color: #FF8B8B;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 12px;
            background: rgba(255, 139, 139, 0.1);
        }

        .status-message.success {
            color: #9BFF9B;
            background: rgba(155, 255, 155, 0.1);
        }

        .hwid-info {
            text-align: center;
            font-size: 11px;
            color: #5A738F;
            margin-top: 20px;
            padding: 10px;
            border-top: 1px solid rgba(255, 215, 0, 0.1);
            font-family: 'Monaco', 'Consolas', monospace;
            letter-spacing: 0.5px;
        }

        .mango-decoration {
            position: absolute;
            font-size: 100px;
            opacity: 0.03;
            pointer-events: none;
            z-index: 0;
            color: #FFD700;
        }

        .mango-1 { top: 10%; left: 5%; transform: rotate(-15deg); }
        .mango-2 { bottom: 10%; right: 5%; transform: rotate(25deg); }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="mango-decoration mango-1">⏣</div>
    <div class="mango-decoration mango-2">⬤</div>

    <div class="login-container">
        <div class="mango-icon">
            <i class="fas fa-leaf"></i>
        </div>
        
        <div class="brand">
            <div class="brand-name">MANGO</div>
            <div class="brand-sub">PREMIUM EXTERNAL</div>
        </div>

        <div class="input-group">
            <label class="input-label">LICENSE KEY</label>
            <input type="text" class="input-field" id="keyInput" placeholder="Enter your Mango key" autocomplete="off">
        </div>

        <button class="btn" onclick="validateKey()" id="validateBtn">
            <i class="fas fa-key"></i>
            <span>ACTIVATE</span>
        </button>

        <div class="status-message" id="statusMessage"></div>
        <div class="hwid-info" id="hwidDisplay">
            <i class="fas fa-fingerprint"></i> Loading HWID...
        </div>
    </div>

    <script>
        function showMessage(message, isSuccess = false) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.textContent = message;
            statusEl.className = 'status-message ' + (isSuccess ? 'success' : '');
        }

        function validateKey() {
            const key = document.getElementById('keyInput').value.trim();
            const validateBtn = document.getElementById('validateBtn');
            
            if (!key) {
                showMessage('Please enter a license key');
                return;
            }

            showMessage('Validating key...');
            validateBtn.disabled = true;
            validateBtn.style.opacity = '0.5';
            
            pywebview.api.validate_key(key).then(result => {
                if (result.success) {
                    showMessage('✓ Welcome to Mango! Loading...', true);
                } else {
                    showMessage('✗ ' + result.message);
                    validateBtn.disabled = false;
                    validateBtn.style.opacity = '1';
                }
            }).catch(error => {
                showMessage('Error validating key');
                validateBtn.disabled = false;
                validateBtn.style.opacity = '1';
                console.error(error);
            });
        }

        pywebview.api.get_hwid().then(hwid => {
            document.getElementById('hwidDisplay').innerHTML = '<i class="fas fa-fingerprint"></i> HWID: ' + hwid;
        }).catch(error => {
            document.getElementById('hwidDisplay').innerHTML = '<i class="fas fa-exclamation-triangle"></i> HWID: Error loading';
        });

        pywebview.api.check_validation().then(result => {
            if (result.validated) {
                window.location.reload();
            }
        }).catch(error => {
            console.error(error);
        });

        document.getElementById('keyInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                validateKey();
            }
        });
    </script>
</body>
</html>
"""

APP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mango</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        body {
            background: #0B1120;
            color: #e0e0e0;
            height: 100vh;
            overflow: hidden;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 215, 0, 0.2);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 215, 0, 0.3);
        }

        .window {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .title-bar {
            height: 48px;
            background: rgba(8, 15, 26, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 215, 0, 0.1);
            display: flex;
            align-items: center;
            padding: 0 20px;
            -webkit-app-region: drag;
        }

        .window-controls {
            display: flex;
            gap: 10px;
            margin-right: 20px;
            -webkit-app-region: no-drag;
        }

        .window-control {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.2s;
        }

        .window-control.close { background: #ff5f57; }
        .window-control.close:hover { background: #ff7b74; transform: scale(1.1); }
        .window-control.minimize { background: #ffbd2e; }
        .window-control.minimize:hover { background: #ffd45c; transform: scale(1.1); }
        .window-control.maximize { background: #28c840; }
        .window-control.maximize:hover { background: #4fe066; transform: scale(1.1); }

        .title {
            color: #FFD700;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .main-container {
            flex: 1;
            display: flex;
            padding: 24px;
            gap: 24px;
            overflow: hidden;
        }

        /* Dashboard Cards */
        .dashboard {
            flex: 1;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: auto 1fr;
            gap: 24px;
            overflow: hidden;
        }

        /* Status Cards */
        .stat-card {
            background: rgba(18, 28, 46, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 215, 0, 0.1);
            border-radius: 20px;
            padding: 20px;
            transition: all 0.3s;
        }

        .stat-card:hover {
            border-color: rgba(255, 215, 0, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 10px 30px -15px rgba(255, 215, 0, 0.2);
        }

        .stat-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
        }

        .stat-icon {
            width: 40px;
            height: 40px;
            background: rgba(255, 215, 0, 0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: #FFD700;
        }

        .stat-title {
            color: #88B0D4;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #FFD700;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #5A738F;
            font-size: 12px;
        }

        /* Main Content Area */
        .main-content {
            grid-column: span 3;
            background: rgba(18, 28, 46, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 215, 0, 0.1);
            border-radius: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .content-tabs {
            display: flex;
            gap: 10px;
            padding: 20px 20px 0 20px;
            border-bottom: 1px solid rgba(255, 215, 0, 0.1);
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: #88B0D4;
            padding: 12px 24px;
            border-radius: 12px 12px 0 0;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            position: relative;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tab-btn:hover {
            color: #FFD700;
            background: rgba(255, 215, 0, 0.05);
        }

        .tab-btn.active {
            color: #FFD700;
        }

        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: #FFD700;
            border-radius: 2px 2px 0 0;
        }

        .content-panel {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }

        /* Action Grid */
        .action-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }

        .action-card {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 215, 0, 0.1);
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }

        .action-card:hover {
            border-color: #FFD700;
            background: rgba(255, 215, 0, 0.05);
            transform: translateY(-2px);
        }

        .action-icon {
            font-size: 28px;
            color: #FFD700;
        }

        .action-title {
            font-size: 14px;
            font-weight: 600;
            color: #FFD700;
        }

        .action-desc {
            font-size: 11px;
            color: #5A738F;
            text-align: center;
        }

        /* Method Selector */
        .method-selector {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 215, 0, 0.2);
            color: #fff;
            padding: 10px 16px;
            border-radius: 30px;
            font-size: 13px;
            outline: none;
            cursor: pointer;
            width: 200px;
        }

        .method-selector:hover {
            border-color: #FFD700;
        }

        .method-selector option {
            background: #1A2F4A;
        }

        /* Console */
        .console {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 215, 0, 0.1);
            border-radius: 16px;
            margin-top: 20px;
            overflow: hidden;
        }

        .console-header {
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 215, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .console-title {
            color: #88B0D4;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .console-dot {
            width: 8px;
            height: 8px;
            background: #FFD700;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        .console-content {
            height: 250px;
            padding: 15px;
            overflow-y: auto;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.6;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 4px 0;
            border-bottom: 1px solid rgba(255, 215, 0, 0.05);
        }

        .log-time {
            color: #5A738F;
            font-size: 11px;
            min-width: 60px;
        }

        .log-type-info .log-message { color: #88B0D4; }
        .log-type-success .log-message { color: #9bff9b; }
        .log-type-error .log-message { color: #ff8b8b; }
        .log-type-warning .log-message { color: #ffd966; }

        /* File Info */
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 215, 0, 0.1);
            padding: 8px 16px;
            border-radius: 30px;
            font-size: 12px;
        }

        .file-name {
            color: #FFD700;
        }

        /* Buttons */
        .btn-small {
            background: transparent;
            border: 1px solid rgba(255, 215, 0, 0.2);
            color: #e0e0e0;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-small:hover {
            border-color: #FFD700;
            color: #FFD700;
            background: rgba(255, 215, 0, 0.05);
        }

        .file-input {
            display: none;
        }

        /* Toolbar */
        .toolbar {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="window">
        <div class="title-bar">
            <div class="window-controls">
                <div class="window-control close" onclick="pywebview.api.exit_app()"></div>
                <div class="window-control minimize" onclick="window.minimize()"></div>
                <div class="window-control maximize" onclick="window.maximize()"></div>
            </div>
            <div class="title">
                <i class="fas fa-leaf" style="color: #FFD700;"></i>
                <span>MANGO CONTROL PANEL</span>
            </div>
        </div>

        <div class="main-container">
            <div class="dashboard">
                <!-- Status Cards -->
                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-icon"><i class="fas fa-plug"></i></div>
                        <div class="stat-title">CONNECTION</div>
                    </div>
                    <div class="stat-value" id="statusText">Waiting</div>
                    <div class="stat-label" id="statusDetail">Roblox status</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-icon"><i class="fas fa-cog"></i></div>
                        <div class="stat-title">METHOD</div>
                    </div>
                    <div class="stat-value" id="methodStatus">Auto</div>
                    <div class="stat-label">Injection method</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-icon"><i class="fas fa-sync-alt"></i></div>
                        <div class="stat-title">REINJECTIONS</div>
                    </div>
                    <div class="stat-value" id="reinjectCounter">0</div>
                    <div class="stat-label">Flags protected</div>
                </div>

                <!-- Main Content -->
                <div class="main-content">
                    <div class="content-tabs">
                        <button class="tab-btn active" onclick="switchTab('injector')">
                            <i class="fas fa-syringe"></i>
                            <span>INJECTOR</span>
                        </button>
                        <button class="tab-btn" onclick="switchTab('dumper')">
                            <i class="fas fa-dumpster"></i>
                            <span>DUMPER</span>
                        </button>
                    </div>

                    <div class="content-panel">
                        <!-- Injector Tab -->
                        <div id="injectorTab">
                            <!-- Toolbar -->
                            <div class="toolbar">
                                <select class="method-selector" id="methodSelector" onchange="changeMethod(this.value)">
                                    <option value="Auto">Auto (Recommended)</option>
                                    <option value="Singleton">Singleton</option>
                                    <option value="Offset">Offset</option>
                                </select>

                                <div class="file-info" id="fileInfo" style="display: none;">
                                    <i class="fas fa-file-alt"></i>
                                    <span class="file-name" id="fileName"></span>
                                </div>

                                <div style="flex: 1;"></div>

                                <button class="btn-small" onclick="syncOffsets()">
                                    <i class="fas fa-sync-alt"></i>
                                    <span>Sync</span>
                                </button>
                                <button class="btn-small" onclick="clearConsole()">
                                    <i class="fas fa-eraser"></i>
                                    <span>Clear</span>
                                </button>
                            </div>

                            <!-- Action Grid -->
                            <div class="action-grid">
                                <div class="action-card" onclick="loadFile()">
                                    <div class="action-icon"><i class="fas fa-folder-open"></i></div>
                                    <div class="action-title">LOAD FLAGS</div>
                                    <div class="action-desc">Import JSON configuration</div>
                                </div>
                                <div class="action-card" onclick="applyFlags()">
                                    <div class="action-icon"><i class="fas fa-bolt"></i></div>
                                    <div class="action-title">INJECT</div>
                                    <div class="action-desc">Apply loaded flags</div>
                                </div>
                                <div class="action-card" onclick="uninjectAll()">
                                    <div class="action-icon"><i class="fas fa-undo-alt"></i></div>
                                    <div class="action-title">UNINJECT</div>
                                    <div class="action-desc">Restore defaults</div>
                                </div>
                            </div>

                            <!-- Console -->
                            <div class="console">
                                <div class="console-header">
                                    <div class="console-dot"></div>
                                    <div class="console-title">
                                        <i class="fas fa-terminal"></i>
                                        <span>LIVE CONSOLE</span>
                                    </div>
                                    <div style="flex: 1;"></div>
                                    <button class="btn-small" onclick="toggleMonitor()" id="monitorBtn">
                                        <i class="fas fa-pause-circle"></i>
                                        <span>Stop Monitor</span>
                                    </button>
                                </div>
                                <div class="console-content" id="console"></div>
                            </div>
                        </div>

                        <!-- Dumper Tab -->
                        <div id="dumperTab" style="display: none;">
                            <div class="action-grid" style="grid-template-columns: 1fr;">
                                <div class="action-card" onclick="dumpFlags()">
                                    <div class="action-icon"><i class="fas fa-download"></i></div>
                                    <div class="action-title">DUMP FFLAGS</div>
                                    <div class="action-desc">Extract all flags from memory</div>
                                </div>
                            </div>

                            <div class="console" style="margin-top: 20px;">
                                <div class="console-header">
                                    <div class="console-dot"></div>
                                    <div class="console-title">
                                        <i class="fas fa-dumpster"></i>
                                        <span>DUMPER OUTPUT</span>
                                    </div>
                                </div>
                                <div class="console-content" id="dumperConsole"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <input type="file" id="fileInput" class="file-input" accept=".json">

    <script>
        let currentTab = 'injector';
        let logs = [];
        let dumperLogs = [];
        let monitorActive = true;

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('injectorTab').style.display = tab === 'injector' ? 'block' : 'none';
            document.getElementById('dumperTab').style.display = tab === 'dumper' ? 'block' : 'none';
            
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }

        function addLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
            const logEntry = { timestamp, message, type };
            logs.push(logEntry);
            if (logs.length > 100) logs.shift();
            
            const consoleEl = document.getElementById('console');
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry log-type-${type}`;
            logDiv.innerHTML = `<span class="log-time">[${timestamp}]</span><span class="log-message">${message}</span>`;
            consoleEl.appendChild(logDiv);
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }

        function addDumperLog(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
            const logEntry = { timestamp, message, type };
            dumperLogs.push(logEntry);
            if (dumperLogs.length > 100) dumperLogs.shift();
            
            const consoleEl = document.getElementById('dumperConsole');
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry log-type-${type}`;
            logDiv.innerHTML = `<span class="log-time">[${timestamp}]</span><span class="log-message">${message}</span>`;
            consoleEl.appendChild(logDiv);
            consoleEl.scrollTop = consoleEl.scrollHeight;
        }

        function clearConsole() {
            document.getElementById('console').innerHTML = '';
            logs = [];
            addLog('Console cleared', 'info');
        }

        function updateStatus() {
            pywebview.api.get_status().then(status => {
                const statusText = document.getElementById('statusText');
                const statusDetail = document.getElementById('statusDetail');
                const methodStatus = document.getElementById('methodStatus');
                const reinjectCounter = document.getElementById('reinjectCounter');
                
                if (status.connected) {
                    statusText.textContent = 'Connected';
                    statusDetail.textContent = 'Roblox detected';
                } else {
                    statusText.textContent = 'Waiting';
                    statusDetail.textContent = 'Waiting for Roblox';
                }
                
                methodStatus.textContent = status.injection_type;
                reinjectCounter.textContent = status.reinjected_count;
            }).catch(error => {
                console.error('Status update error:', error);
            });
        }

        function changeMethod(method) {
            pywebview.api.set_injection_type(method).then(() => {
                addLog(`Injection method changed to ${method}`, 'info');
            }).catch(error => {
                addLog('Failed to change method', 'error');
            });
        }

        function syncOffsets() {
            pywebview.api.sync_offsets().then(result => {
                if (result.success) {
                    addLog(`Synced ${result.count} offsets`, 'success');
                } else {
                    addLog('Failed to sync offsets', 'error');
                }
            }).catch(error => {
                addLog('Sync error', 'error');
            });
        }

        function loadFile() {
            document.getElementById('fileInput').click();
        }

        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                const fileData = e.target.result;
                const fileName = file.name;
                
                document.getElementById('fileInfo').style.display = 'flex';
                document.getElementById('fileName').textContent = fileName;
                
                pywebview.api.load_flags(fileData, fileName).then(result => {
                    if (result.success) {
                        addLog(`Loaded ${result.count} flags from ${fileName}`, 'success');
                    } else {
                        addLog('Failed to load flags', 'error');
                    }
                }).catch(error => {
                    addLog('Error loading file', 'error');
                });
            };
            reader.readAsText(file);
        });

        function applyFlags() {
            pywebview.api.apply_flags().then(result => {
                if (result.success > 0) {
                    addLog(`Successfully injected ${result.success} flags`, 'success');
                } else if (result.message) {
                    addLog(result.message, 'warning');
                }
            }).catch(error => {
                addLog('Injection error', 'error');
            });
        }

        function uninjectAll() {
            pywebview.api.uninject_all().then(result => {
                if (result.success > 0) {
                    addLog(`Restored ${result.success} flags to default`, 'success');
                }
            }).catch(error => {
                addLog('Uninject error', 'error');
            });
        }

        function dumpFlags() {
            addDumperLog('Starting FFlag dump...', 'info');
            pywebview.api.dump_flags().then(() => {
                addDumperLog('Dump process started', 'success');
            }).catch(error => {
                addDumperLog('Dump error', 'error');
            });
        }

        function toggleMonitor() {
            monitorActive = !monitorActive;
            const btn = document.getElementById('monitorBtn');
            if (monitorActive) {
                btn.innerHTML = '<i class="fas fa-pause-circle"></i><span>Stop Monitor</span>';
            } else {
                btn.innerHTML = '<i class="fas fa-play-circle"></i><span>Start Monitor</span>';
            }
            pywebview.api.toggle_monitor().then(result => {
                if (result.success) {
                    addLog(`Monitor ${result.monitoring ? 'started' : 'stopped'}`, 'info');
                }
            }).catch(error => {
                addLog('Monitor toggle error', 'error');
            });
        }

        setInterval(updateStatus, 1000);

        window.addEventListener('pywebviewready', function() {
            addLog('Mango Control Panel initialized', 'success');
            updateStatus();
        });
    </script>
</body>
</html>
"""

def main():
    log_bridge = LogBridge()
    injector = HybridInjector(log_bridge)
    key_system = KeySystem()
    api = Api(injector, log_bridge, key_system)

    def on_log(log_entry):
        try:
            if webview.windows and len(webview.windows) > 0:
                if api.validated:
                    webview.windows[0].evaluate_js(f'addLog("{log_entry["message"]}", "{log_entry["type"]}")')
        except Exception as e:
            print(f"Log error: {e}")

    log_bridge.add_callback(on_log)

    if key_system.check_saved_license():
        api.validated = True
        html_content = APP_HTML
    else:
        html_content = LOGIN_HTML

    window = webview.create_window(
        "Mango Premium",
        html=html_content,
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
        fullscreen=False,
        min_size=(1000, 600),
        easy_drag=False
    )
    
    api.set_window(window)
    webview.start(debug=False, private_mode=False)

if __name__ == "__main__":
    main()