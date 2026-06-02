
import ctypes
import math
import struct
import sys
import threading
import time
from dataclasses import dataclass

import pymem
import pymem.process

try:
from keystone import Ks, KS_ARCH_X86, KS_MODE_64
except ImportError:
print("[-] Install keystone-engine: pip install keystone-engine")
sys.exit(1)


# ================================================== ===========================
# Config
# ================================================== ===========================

PROCESS_NAME = "Trove_x64.exe"

ENTITY_REFRESH_DELAY = 0.03
TARGET_UPDATE_MIN_DELTA = 0.01

# Max silent-aim target range.
# This does NOT affect entity extraction.
# It only decides whether the closest extracted entity is allowed as a target.
MAX_RANGE = 50.0

# Entity base position is usually low. This lifts the aim point into the body.
AIM_Y_OFFSET = 0.45

# Full camera/projectile parallax compensation.
PARALLAX = 1.0
MIN_LEN_SQ = 0.000001

# Contains-based blacklist:
# If the entity name contains any keyword anywhere, it is ignored.
blacklist_keywords = [
"pet",
"portal",
"abilities",
"cornerstone",
"services",
"client",
#"mana",
"karma",
"adventure",
"placeable",
]


# ================================================== ===========================
# RVAs / offsets
# ================================================== ===========================

EntityList = 0x1396BC0
LOCAL_BASE_PTR = 0x0139F870

CAM_ROOT_OFFSET = 0x40
CAM_POS_OFFSET = 0x140

# Confirmed active SetProjectileOrigin variant.
# Entry args:
# rdx = projectile origin pointer
# r8 = projectile direction pointer
HOOK_RVA = 0x77E9E0
PATCH_LEN = 14
RETURN_RVA = HOOK_RVA + PATCH_LEN

EXPECTED_ORIGINAL = bytes.fromhex(
"48 8B C4 48 89 58 10 44 89 48 20 55 56 57"
)

OFFSETS = {
"hash_base": 0xE0,
"hash_stride": 0xE8,
"hash_count": 0xF0,

"node_next": 0x00,
"node_object": 0x10,

"name": [0x98, 0x0],
"position": [0x130, 0x8, 0xD0],
"scale": [0x130, 0x8, 0x178],
"level": [0x130, 0xA8, 0x208],
"current_health": [0x130, 0x108, 0xD8],
}

NODE_MARK_MASK = 0xFFFFFFFFFFFFFFFE
MAX_BUCKETS = 8192
MAX_CHAIN_DEPTH = 256
MAX_TOTAL_NODES = 30000
NAME_MAX_LEN = 160


# ================================================== ===========================
# Shared data block
# ================================================== ===========================

# Python writes target data here. The codecave reads it on each projectile call.
DATA_ENABLED = 0x00 # u32
DATA_VALID = 0x04 # u32
DATA_X = 0x08 # float
DATA_Y = 0x0C # float
DATA_Z = 0x10 # float
DATA_PARALLAX = 0x14 # float
DATA_MIN_LEN_SQ = 0x18 # float
DATA_LOCAL_BASE_PTR = 0x20 # u64


# ================================================== ===========================
# WinAPI
# ================================================== ===========================

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

VirtualAllocEx = kernel32.VirtualAllocEx
VirtualAllocEx.argtypes = [
ctypes.c_void_p,
ctypes.c_void_p,
ctypes.c_size_t,
ctypes.c_uint32,
ctypes.c_uint32,
]
VirtualAllocEx.restype = ctypes.c_void_p

VirtualFreeEx = kernel32.VirtualFreeEx
VirtualFreeEx.argtypes = [
ctypes.c_void_p,
ctypes.c_void_p,
ctypes.c_size_t,
ctypes.c_uint32,
]
VirtualFreeEx.restype = ctypes.c_bool

VirtualProtectEx = kernel32.VirtualProtectEx
VirtualProtectEx.argtypes = [
ctypes.c_void_p,
ctypes.c_void_p,
ctypes.c_size_t,
ctypes.c_uint32,
ctypes.POINTER(ctypes.c_uint32),
]
VirtualProtectEx.restype = ctypes.c_bool

FlushInstructionCache = kernel32.FlushInstructionCache
FlushInstructionCache.argtypes = [
ctypes.c_void_p,
ctypes.c_void_p,
ctypes.c_size_t,
]
FlushInstructionCache.restype = ctypes.c_bool


@dataclass(slots=True)
class Entity:
address: int
name: str
hp: float
x: float
y: float
z: float
dist: float = 0.0


class RemoteAlloc:
"""Simple wrapper around VirtualAllocEx / VirtualFreeEx."""

def __init__(self, pm: pymem.Pymem, size: int):
self.pm = pm
self.size = size

self.address = int(VirtualAllocEx(
pm.process_handle,
None,
size,
MEM_COMMIT | MEM_RESERVE,
PAGE_EXECUTE_READWRITE,
))

if not self.address:
raise ctypes.WinError(ctypes.get_last_error())

def free(self) -> None:
if self.address:
VirtualFreeEx(
self.pm.process_handle,
ctypes.c_void_p(self.address),
0,
MEM_RELEASE,
)
self.address = 0


# ================================================== ===========================
# Memory helpers
# ================================================== ===========================

def valid_ptr(value: int) -> bool:
return 0x10000 <= value <= 0x00007FFFFFFFFFFF


def module_base(pm: pymem.Pymem, name: str) -> int:
mod = pymem.process.module_from_name(pm.process_handle, name)

if mod is None:
raise RuntimeError(f"Module not found: {name}")

return mod.lpBaseOfDll


def rp(pm: pymem.Pymem, addr: int) -> int:
try:
value = pm.read_ulonglong(addr)
return value if valid_ptr(value) else 0
except Exception:
return 0


def ru64(pm: pymem.Pymem, addr: int) -> int | None:
try:
return pm.read_ulonglong(addr)
except Exception:
return None


def rf32(pm: pymem.Pymem, addr: int) -> float | None:
try:
value = pm.read_float(addr)
return value if math.isfinite(value) else None
except Exception:
return None


def rf64(pm: pymem.Pymem, addr: int) -> float | None:
try:
value = pm.read_double(addr)
return value if math.isfinite(value) else None
except Exception:
return None


def wb(pm: pymem.Pymem, addr: int, data: bytes) -> None:
pm.write_bytes(addr, data, len(data))


def wu32(pm: pymem.Pymem, addr: int, value: int) -> None:
wb(pm, addr, struct.pack("<I", value & 0xFFFFFFFF))


def wu64(pm: pymem.Pymem, addr: int, value: int) -> None:
wb(pm, addr, struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF))


def wf32(pm: pymem.Pymem, addr: int, value: float) -> None:
wb(pm, addr, struct.pack("<f", float(value)))


def protect(pm: pymem.Pymem, addr: int, size: int, prot: int) -> int:
old = ctypes.c_uint32(0)

ok = VirtualProtectEx(
pm.process_handle,
ctypes.c_void_p(addr),
size,
prot,
ctypes.byref(old),
)

if not ok:
raise ctypes.WinError(ctypes.get_last_error())

return old.value


def flush(pm: pymem.Pymem, addr: int, size: int) -> None:
FlushInstructionCache(
pm.process_handle,
ctypes.c_void_p(addr),
size,
)


# ================================================== ===========================
# Entity reading
# ================================================== ===========================

def chain_addr(pm: pymem.Pymem, base: int, chain: list[int]) -> int:
"""Resolve pointer chain and return final value address."""
cur = base

for off in chain[:-1]:
cur = rp(pm, cur + off)

if not valid_ptr(cur):
return 0

addr = cur + chain[-1]
return addr if valid_ptr(addr) else 0


def read_str(pm: pymem.Pymem, addr: int, max_len: int = NAME_MAX_LEN) -> str:
if not valid_ptr(addr):
return ""

try:
raw = pm.read_bytes(addr, max_len).split(b"\0", 1)[0]
return raw.decode("latin-1", errors="replace").strip() if raw else ""
except Exception:
return ""


def read_name(pm: pymem.Pymem, ent: int) -> str:
"""Name may be direct or behind one extra pointer."""
addr = chain_addr(pm, ent, OFFSETS["name"])

direct = read_str(pm, addr)
if direct:
return direct

return read_str(pm, rp(pm, addr))


def read_vec3(pm: pymem.Pymem, addr: int) -> tuple[float, float, float] | None:
x = rf32(pm, addr)
y = rf32(pm, addr + 4)
z = rf32(pm, addr + 8)

if x is None or y is None or z is None:
return None

if abs(x) > 1_000_000 or abs(y) > 1_000_000 or abs(z) > 1_000_000:
return None

if abs(x) < 0.0001 and abs(y) < 0.0001 and abs(z) < 0.0001:
return None

return x, y, z


def read_vec3_chain(pm: pymem.Pymem, ent: int, chain: list[int]) -> tuple[float, float, float] | None:
return read_vec3(pm, chain_addr(pm, ent, chain))


def blacklisted(name: str) -> bool:
"""
Contains-based blacklist.

This does not require the entity name to start with the keyword.
If the keyword appears anywhere in the name, the entity is ignored.
"""
low = name.lower()
return any(keyword.lower() in low for keyword in blacklist_keywords)


def read_entity(pm: pymem.Pymem, ent: int) -> Entity | None:
name = read_name(pm, ent)

if not name or blacklisted(name):
return None

pos = read_vec3_chain(pm, ent, OFFSETS["position"])
if pos is None:
return None

hp_addr = chain_addr(pm, ent, OFFSETS["current_health"])
hp = rf64(pm, hp_addr)

x, y, z = pos
return Entity(ent, name, hp, x, y, z)


def collect_entities(pm: pymem.Pymem, owner: int) -> list[Entity]:
"""
Walk the entity hash table and return valid targets only.

Important:
MAX_RANGE is not applied here.
This function only extracts valid entities.
Range filtering happens later in closest_entity().
"""
base = rp(pm, owner + OFFSETS["hash_base"])
stride = ru64(pm, owner + OFFSETS["hash_stride"])
count = ru64(pm, owner + OFFSETS["hash_count"])

if not valid_ptr(base) or stride is None or count is None:
return []

if stride <= 0 or stride > 0x400 or count <= 0 or count > MAX_BUCKETS:
return []

out: list[Entity] = []
seen_nodes: set[int] = set()
seen_entities: set[int] = set()
nodes = 0

for bucket in range(int(count)):
node = base + bucket * int(stride)
depth = 0

while valid_ptr(node) and depth < MAX_CHAIN_DEPTH and nodes < MAX_TOTAL_NODES:
if node in seen_nodes:
break

seen_nodes.add(node)
nodes += 1

raw_next = rp(pm, node + OFFSETS["node_next"])
next_node = raw_next & NODE_MARK_MASK if raw_next else 0

ent_ptr = rp(pm, node + OFFSETS["node_object"])

if valid_ptr(ent_ptr) and ent_ptr not in seen_entities:
seen_entities.add(ent_ptr)

ent = read_entity(pm, ent_ptr)
if ent is not None:
out.append(ent)

if raw_next == 1 or not valid_ptr(next_node) or next_node == node:
break

node = next_node
depth += 1

return out


# ================================================== ===========================
# Target selection
# ================================================== ===========================

def cam_pos(pm: pymem.Pymem, base: int) -> tuple[float, float, float] | None:
"""Read current camera position."""
local = rp(pm, base + LOCAL_BASE_PTR)
if not valid_ptr(local):
return None

root = rp(pm, local + CAM_ROOT_OFFSET)
if not valid_ptr(root):
return None

return read_vec3(pm, root + CAM_POS_OFFSET)


def dist3(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
dx = a[0] - b[0]
dy = a[1] - b[1]
dz = a[2] - b[2]

return math.sqrt(dx * dx + dy * dy + dz * dz)


def aim_pos(ent: Entity) -> tuple[float, float, float]:
"""Convert entity base position to aim point."""
return ent.x, ent.y + AIM_Y_OFFSET, ent.z


def closest_entity(
entities: list[Entity],
camera: tuple[float, float, float],
) -> Entity | None:
"""
Select the closest entity inside MAX_RANGE only.

This does not affect extraction.
If all extracted entities are outside MAX_RANGE, return None.
Returning None disables silent aim until a valid target enters range.
"""
best = None
best_dist = float("inf")

for ent in entities:
d = dist3(camera, aim_pos(ent))

if d > MAX_RANGE:
continue

if d < best_dist:
best_dist = d
ent.dist = d
best = ent

return best


# ================================================== ===========================
# Codecave
# ================================================== ===========================

def asm_bytes(asm: str) -> bytes:
"""Assemble code with Keystone after removing comments/empty lines."""
clean = "\n".join(
line.split(";", 1)[0].strip()
for line in asm.splitlines()
if line.split(";", 1)[0].strip()
)

ks = Ks(KS_ARCH_X86, KS_MODE_64)
code, _ = ks.asm(clean)

if not code:
raise RuntimeError("Keystone returned empty code")

return bytes(code)


def jmp_abs(addr: int) -> bytes:
"""14-byte absolute jump, works even when cave is far away."""
return b"\xFF\x25\x00\x00\x00\x00" + struct.pack("<Q", addr)


def init_data(pm: pymem.Pymem, data: int, local_base_ptr: int) -> None:
"""Initialize shared block read by the injected cave."""
wu32(pm, data + DATA_ENABLED, 1)
wu32(pm, data + DATA_VALID, 0)

wf32(pm, data + DATA_X, 0.0)
wf32(pm, data + DATA_Y, 0.0)
wf32(pm, data + DATA_Z, 0.0)

wf32(pm, data + DATA_PARALLAX, PARALLAX)
wf32(pm, data + DATA_MIN_LEN_SQ, MIN_LEN_SQ)

wu64(pm, data + DATA_LOCAL_BASE_PTR, local_base_ptr)


def build_cave(data: int, ret: int) -> bytes:
"""
Entry hook for SetProjectileOrigin.

It writes a corrected normalized direction directly into [r8],
because r8 is the incoming projectile direction pointer.
"""
return asm_bytes(f"""
pushfq
push rax
push rdx
push r10
push r11

sub rsp, 0x60
movdqu xmmword ptr [rsp + 0x00], xmm0
movdqu xmmword ptr [rsp + 0x10], xmm1
movdqu xmmword ptr [rsp + 0x20], xmm2
movdqu xmmword ptr [rsp + 0x30], xmm3
movdqu xmmword ptr [rsp + 0x40], xmm4
movdqu xmmword ptr [rsp + 0x50], xmm5

mov r10, 0x{data:X}

cmp dword ptr [r10 + 0x{DATA_ENABLED:X}], 1
jne skip

cmp dword ptr [r10 + 0x{DATA_VALID:X}], 1
jne skip

test rdx, rdx
je skip

test r8, r8
je skip

mov rax, qword ptr [r10 + 0x{DATA_LOCAL_BASE_PTR:X}]
test rax, rax
je skip

mov rax, qword ptr [rax]
test rax, rax
je skip

mov r11, qword ptr [rax + 0x{CAM_ROOT_OFFSET:X}]
test r11, r11
je skip

movss xmm0, dword ptr [r10 + 0x{DATA_X:X}]
movss xmm3, dword ptr [r11 + 0x{CAM_POS_OFFSET + 0:X}]
movss xmm4, xmm3
subss xmm4, dword ptr [rdx + 0x00]
mulss xmm4, dword ptr [r10 + 0x{DATA_PARALLAX:X}]
addss xmm0, xmm4
subss xmm0, xmm3

movss xmm1, dword ptr [r10 + 0x{DATA_Y:X}]
movss xmm3, dword ptr [r11 + 0x{CAM_POS_OFFSET + 4:X}]
movss xmm4, xmm3
subss xmm4, dword ptr [rdx + 0x04]
mulss xmm4, dword ptr [r10 + 0x{DATA_PARALLAX:X}]
addss xmm1, xmm4
subss xmm1, xmm3

movss xmm2, dword ptr [r10 + 0x{DATA_Z:X}]
movss xmm3, dword ptr [r11 + 0x{CAM_POS_OFFSET + 8:X}]
movss xmm4, xmm3
subss xmm4, dword ptr [rdx + 0x08]
mulss xmm4, dword ptr [r10 + 0x{DATA_PARALLAX:X}]
addss xmm2, xmm4
subss xmm2, xmm3

movss xmm3, xmm0
mulss xmm3, xmm3

movss xmm4, xmm1
mulss xmm4, xmm4
addss xmm3, xmm4

movss xmm5, xmm2
mulss xmm5, xmm5
addss xmm3, xmm5

comiss xmm3, dword ptr [r10 + 0x{DATA_MIN_LEN_SQ:X}]
jbe skip

sqrtss xmm3, xmm3

divss xmm0, xmm3
divss xmm1, xmm3
divss xmm2, xmm3

movss dword ptr [r8 + 0x00], xmm0
movss dword ptr [r8 + 0x04], xmm1
movss dword ptr [r8 + 0x08], xmm2

skip:
movdqu xmm0, xmmword ptr [rsp + 0x00]
movdqu xmm1, xmmword ptr [rsp + 0x10]
movdqu xmm2, xmmword ptr [rsp + 0x20]
movdqu xmm3, xmmword ptr [rsp + 0x30]
movdqu xmm4, xmmword ptr [rsp + 0x40]
movdqu xmm5, xmmword ptr [rsp + 0x50]

add rsp, 0x60

pop r11
pop r10
pop rdx
pop rax
popfq

mov rax, rsp
mov qword ptr [rax + 0x10], rbx
mov dword ptr [rax + 0x20], r9d
push rbp
push rsi
push rdi

mov r11, 0x{ret:X}
jmp r11
""")


def install_hook(pm: pymem.Pymem, hook: int, cave: int) -> bytes:
"""Patch the function entry with an absolute jump."""
original = pm.read_bytes(hook, PATCH_LEN)

if original != EXPECTED_ORIGINAL:
raise RuntimeError(
"Hook bytes mismatch\n"
f"expected: {EXPECTED_ORIGINAL.hex(' ').upper()}\n"
f"actual : {original.hex(' ').upper()}"
)

patch = jmp_abs(cave)
old = protect(pm, hook, PATCH_LEN, PAGE_EXECUTE_READWRITE)

try:
wb(pm, hook, patch)
flush(pm, hook, PATCH_LEN)
finally:
protect(pm, hook, PATCH_LEN, old)

return original


def uninstall_hook(pm: pymem.Pymem, hook: int, original: bytes) -> None:
"""Restore original function bytes."""
old = protect(pm, hook, len(original), PAGE_EXECUTE_READWRITE)

try:
wb(pm, hook, original)
flush(pm, hook, len(original))
finally:
protect(pm, hook, len(original), old)


# ================================================== ===========================
# Target updater
# ================================================== ===========================

def set_valid(pm: pymem.Pymem, data: int, valid: bool) -> None:
wu32(pm, data + DATA_VALID, 1 if valid else 0)


def write_target(pm: pymem.Pymem, data: int, pos: tuple[float, float, float]) -> None:
"""Write selected target position to shared block."""
wf32(pm, data + DATA_X, pos[0])
wf32(pm, data + DATA_Y, pos[1])
wf32(pm, data + DATA_Z, pos[2])
wu32(pm, data + DATA_VALID, 1)


def target_loop(pm: pymem.Pymem, base: int, data: int, stop: threading.Event) -> None:
"""
Background thread.

It extracts entities normally, then applies MAX_RANGE only during final
target selection. This keeps extraction independent from range filtering.
"""
owner_ptr = base + EntityList
last_addr = 0
last_pos = None
last_clear = 0.0

while not stop.is_set():
try:
camera = cam_pos(pm, base)
owner = rp(pm, owner_ptr)

if camera is None or not valid_ptr(owner):
if time.time() - last_clear >= 0.25:
set_valid(pm, data, False)
last_clear = time.time()

time.sleep(ENTITY_REFRESH_DELAY)
continue

entities = collect_entities(pm, owner)
target = closest_entity(entities, camera)

if target is None:
last_addr = 0
last_pos = None

if time.time() - last_clear >= 0.25:
set_valid(pm, data, False)
last_clear = time.time()

time.sleep(ENTITY_REFRESH_DELAY)
continue

pos = aim_pos(target)
moved = 999999.0 if last_pos is None else dist3(last_pos, pos)

if target.address != last_addr or last_pos is None or moved >= TARGET_UPDATE_MIN_DELTA:
write_target(pm, data, pos)
last_addr = target.address
last_pos = pos

time.sleep(ENTITY_REFRESH_DELAY)

except Exception:
set_valid(pm, data, False)
time.sleep(ENTITY_REFRESH_DELAY)


# ================================================== ===========================
# Main
# ================================================== ===========================

def main() -> None:
print(f"[*] Attaching to {PROCESS_NAME}...")

pm = pymem.Pymem(PROCESS_NAME)
base = module_base(pm, PROCESS_NAME)

hook = base + HOOK_RVA
ret = base + RETURN_RVA
local_base_ptr = base + LOCAL_BASE_PTR

data = RemoteAlloc(pm, 0x1000)
cave = RemoteAlloc(pm, 0x4000)

original = b""
installed = False
stop = threading.Event()
worker = None

try:
init_data(pm, data.address, local_base_ptr)

cave_code = build_cave(data.address, ret)
wb(pm, cave.address, cave_code)
flush(pm, cave.address, len(cave_code))

original = install_hook(pm, hook, cave.address)
installed = True

worker = threading.Thread(
target=target_loop,
args=(pm, base, data.address, stop),
daemon=True,
)
worker.start()

print("[+] Silent aim running")
print(f"[+] max range = {MAX_RANGE:.1f}")
print("[*] Press Ctrl+C to stop")

while True:
time.sleep(1)

except KeyboardInterrupt:
print("\n[*] Stopping...")

finally:
stop.set()

if worker is not None:
worker.join(timeout=1.0)

# Disable the cave logic before restoring/freeing memory.
# This makes shutdown safer if the game hits the hook during cleanup.
if data is not None and data.address:
try:
wu32(pm, data.address + DATA_ENABLED, 0)
wu32(pm, data.address + DATA_VALID, 0)
except Exception:
pass

if installed:
try:
uninstall_hook(pm, hook, original)
print("[+] Hook restored")
except Exception as exc:
print(f"[-] Failed to restore hook: {exc}")

if cave is not None:
try:
cave.free()
except Exception:
pass

if data is not None:
try:
data.free()
except Exception:
pass

print("[+] Done")

if __name__ == "__main__":
main()