"""
OSD Tool for Resident Evil 4
By: اليمني
"""

import os
import struct


MAGIC  = bytes([0x44, 0x69, 0x73, 0x63])
FOOTER = bytes([0xCD, 0xCD, 0xCD, 0xCD])


# ══════════════════════════════════════════════════════
#  مساعدات نص
# ══════════════════════════════════════════════════════

def split_values(s: str) -> list:
    s = s.replace("،", " ").replace(",", " ")
    return [x for x in s.split() if x]

def join_values(vals: list) -> str:
    return ", ".join(str(v) for v in vals)


# ══════════════════════════════════════════════════════
#  قراءة بلوك واحد من موضع معروف
#  pos يجب أن يكون بعد Magic (أو في بداية البيانات لو FALSE)
# ══════════════════════════════════════════════════════

def read_block_data(data: bytes, pos: int, has_magic: bool) -> tuple:
    """
    يقرأ بيانات بلوك واحد بدءًا من pos (بعد تجاوز Magic إن وُجد)
    يرجع (block_dict, new_pos) أو (None, pos) لو البيانات ناقصة
    """
    try:
        aev_index = data[pos]; pos += 1
        num_items = data[pos]; pos += 1

        items      = []
        quantities = []
        for _ in range(num_items):
            item_id = struct.unpack_from('<H', data, pos)[0]; pos += 2
            qty     = struct.unpack_from('<H', data, pos)[0]; pos += 2
            items.append(item_id)
            quantities.append(qty)

        num_sf       = data[pos]; pos += 1
        success_aevs = list(data[pos:pos+num_sf]); pos += num_sf
        fail_aevs    = list(data[pos:pos+num_sf]); pos += num_sf

        return {
            "osd_op"       : has_magic,
            "aev_index"    : aev_index,
            "items"        : items,
            "quantities"   : quantities,
            "num_sf"       : num_sf,
            "success_aevs" : success_aevs,
            "fail_aevs"    : fail_aevs,
        }, pos
    except (IndexError, struct.error):
        return None, pos


def is_empty_block(block: dict) -> bool:
    """
    بلوك فاضي = AEV INDEX و NUM_ITEMS وأول qty كلهم 00
    هذا يُسكب ولا يظهر في Data.txt
    """
    if block["aev_index"] != 0:
        return False
    if len(block["items"]) != 0:
        return False
    return True


# ══════════════════════════════════════════════════════
#  كتابة بلوك ثنائي
# ══════════════════════════════════════════════════════

def write_block(block: dict) -> bytes:
    buf = bytearray()
    if block.get("osd_op", True):
        buf += MAGIC
    buf.append(block["aev_index"])
    buf.append(len(block["items"]))
    for item, qty in zip(block["items"], block["quantities"]):
        buf += struct.pack('<H', item)
        buf += struct.pack('<H', qty)
    num_sf = block["num_sf"]
    buf.append(num_sf)
    for a in block["success_aevs"]:
        buf.append(a)
    for a in block["fail_aevs"]:
        buf.append(a)
    return bytes(buf)


def write_empty_block() -> bytes:
    # بلوك فاضي: Magic + أصفار
    return MAGIC + bytes([0x00, 0x00, 0x00, 0x00, 0x00])


# ══════════════════════════════════════════════════════
#  EXT  ─  OSD  →  Data.txt
# ══════════════════════════════════════════════════════

def extract(osd_path: str):
    osd_path = osd_path.strip().strip('"')

    if not os.path.exists(osd_path):
        print(f"\n  [خطأ] الملف غير موجود: {osd_path}")
        return False

    with open(osd_path, "rb") as f:
        raw = f.read()

    # حذف Footer من النهاية
    data = raw.rstrip(b'\xCD')

    if len(data) < 4:
        print("\n  [خطأ] الملف فاضي أو صغير جدًا")
        return False

    # ── تحديد حدود الملف: أول Magic وآخر Magic ──
    first_magic = data.find(MAGIC)
    if first_magic == -1:
        print("\n  [خطأ] ما فيه OSD في الملف (Magic غير موجود)")
        return False

    # آخر Magic
    last_magic = data.rfind(MAGIC)

    # نقرأ فقط من أول Magic لنهاية آخر بلوك
    # نحدد نهاية آخر بلوك بقراءته
    temp_pos  = last_magic + 4  # تجاوز Magic الأخير
    last_block, end_pos = read_block_data(data, temp_pos, True)
    if last_block is None:
        print("\n  [خطأ] تعذّر قراءة آخر بلوك")
        return False

    # البيانات المفيدة: من first_magic إلى end_pos
    zone = data[first_magic:end_pos]

    # ── قراءة كل البلوكات داخل الـ zone ──
    blocks = []
    pos    = 0

    while pos < len(zone):
        # هل الموضع الحالي فيه Magic؟
        if zone[pos:pos+4] == MAGIC:
            has_magic = True
            pos += 4
        else:
            has_magic = False

        block, new_pos = read_block_data(zone, pos, has_magic)

        if block is None or new_pos == pos:
            # تقدم بايت وحد وحاول مرة ثانية (بيانات غير معروفة)
            pos += 1
            continue

        pos = new_pos

        # سكب البلوكات الفاضية
        if not is_empty_block(block):
            blocks.append(block)

    if not blocks:
        print("\n  [خطأ] لم يُعثر على بلوكات OSD قابلة للقراءة")
        return False

    # ── بناء المجلد وكتابة Data.txt ──
    folder_name = os.path.splitext(os.path.basename(osd_path))[0]
    out_dir     = os.path.join(os.path.dirname(os.path.abspath(osd_path)), folder_name)
    os.makedirs(out_dir, exist_ok=True)

    lines = []
    lines.append(f"NUMBER OF OSD = {len(blocks)}")
    lines.append("")

    for b in blocks:
        items_str = join_values([f"{i:X}" for i in b["items"]])
        qty_str   = join_values(["FFFF" if q == 0xFFFF else str(q) for q in b["quantities"]])
        suc_str   = join_values([f"{a:02X}" for a in b["success_aevs"]])
        fail_str  = join_values([f"{a:02X}" for a in b["fail_aevs"]])

        lines.append(f"OSD Operation = {'TRUE' if b['osd_op'] else 'FALSE'}")
        lines.append(f"AEV INDEX = {b['aev_index']:02X}")
        lines.append(f"Number OF ITEM = {len(b['items'])}")
        lines.append(f"Item Number = {items_str}")
        lines.append(f"Number of Quantity = {qty_str}")
        lines.append(f"Number of Success and Failure = {b['num_sf']}")
        lines.append(f"AEV Success = {suc_str}")
        lines.append(f"AEV Failure = {fail_str}")
        lines.append("")

    txt_path = os.path.join(out_dir, "Data.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  [OK] تم الاستخراج  -  {len(blocks)} بلوك")
    print(f"  المجلد : {out_dir}")
    print(f"  الملف  : Data.txt")
    print()
    print("  +-------------------------------------------------")
    for line in lines:
        print(f"  |  {line}" if line else "  |")
    print("  +-------------------------------------------------")
    return True


# ══════════════════════════════════════════════════════
#  REPACK  ─  Data.txt أو مسار OSD  →  OSD
# ══════════════════════════════════════════════════════

def resolve_txt_path(path: str):
    path = path.strip().strip('"')
    ext  = os.path.splitext(path)[1].lower()

    if ext == ".osd" or (ext != ".txt" and os.path.isfile(path)):
        base      = os.path.splitext(os.path.basename(path))[0]
        osd_dir   = os.path.dirname(os.path.abspath(path))
        candidate = os.path.join(osd_dir, base, "Data.txt")
        if os.path.exists(candidate):
            return candidate
        print(f"\n  [خطأ] ما لقيت مجلد '{base}' أو Data.txt بداخله")
        return None

    return path


def repack(input_path: str):
    txt_path = resolve_txt_path(input_path)
    if txt_path is None:
        return False

    if not os.path.exists(txt_path):
        print(f"\n  [خطأ] الملف غير موجود: {txt_path}")
        return False

    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()

    # قراءة NUMBER OF OSD
    num_osd = None
    for line in lines:
        if line.strip().upper().startswith("NUMBER OF OSD"):
            val = line.split("=", 1)[1].strip()
            if val.isdigit():
                num_osd = int(val)
            break

    # قراءة البلوكات
    raw_blocks = []
    current    = None

    for line in lines:
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip().upper()
        val = val.strip()

        if key == "OSD OPERATION":
            if current is not None:
                raw_blocks.append(current)
            current = {"OSD OPERATION": val.upper()}
        elif current is not None:
            current[key] = val

    if current is not None:
        raw_blocks.append(current)

    if num_osd is None:
        num_osd = len(raw_blocks)

    # بناء الملف الثنائي
    buf = bytearray()

    for i in range(num_osd):
        if i < len(raw_blocks):
            b = raw_blocks[i]

            osd_op    = b.get("OSD OPERATION", "TRUE") == "TRUE"
            aev_index = int(b.get("AEV INDEX", "00"), 16)

            items_raw = split_values(b.get("ITEM NUMBER", ""))
            items     = [int(x, 16) for x in items_raw if x]

            qty_raw    = split_values(b.get("NUMBER OF QUANTITY", ""))
            quantities = []
            for q in qty_raw:
                quantities.append(0xFFFF if q.upper() == "FFFF" else int(q))
            while len(quantities) < len(items):
                quantities.append(0xFFFF)

            num_sf_str   = b.get("NUMBER OF SUCCESS AND FAILURE", "0")
            num_sf       = int(num_sf_str) if num_sf_str.isdigit() else 0

            success_aevs = [int(x, 16) for x in split_values(b.get("AEV SUCCESS", "")) if x]
            fail_aevs    = [int(x, 16) for x in split_values(b.get("AEV FAILURE", "")) if x]

            success_aevs = (success_aevs + [0xFF] * num_sf)[:num_sf]
            fail_aevs    = (fail_aevs    + [0xFF] * num_sf)[:num_sf]

            buf += write_block({
                "osd_op"       : osd_op,
                "aev_index"    : aev_index,
                "items"        : items,
                "quantities"   : quantities,
                "num_sf"       : num_sf,
                "success_aevs" : success_aevs,
                "fail_aevs"    : fail_aevs,
            })
        else:
            buf += write_empty_block()

    # سؤال Footer
    print()
    while True:
        ans = input("  تبي تضيف CD CD CD CD في النهاية؟ [y/n] : ").strip().lower()
        if ans in ("y", "n"):
            break
        print("  [!] اكتب y أو n")
    if ans == "y":
        buf += FOOTER

    # حفظ الملف خارج المجلد
    txt_dir     = os.path.dirname(os.path.abspath(txt_path))
    parent_dir  = os.path.dirname(txt_dir)
    folder_name = os.path.basename(txt_dir)
    out_path    = os.path.join(parent_dir, f"{folder_name}.OSD")

    with open(out_path, "wb") as f:
        f.write(buf)

    blocks_written = min(num_osd, len(raw_blocks))
    empty_added    = max(0, num_osd - len(raw_blocks))

    print(f"\n  [OK] تم التجميع بنجاح!")
    print(f"  الملف      : {out_path}")
    print(f"  البلوكات   : {blocks_written} مكتوبة + {empty_added} فاضية")
    print(f"  الحجم      : {len(buf)} bytes")
    print(f"  HEX        : {buf.hex().upper()}")
    return True


# ══════════════════════════════════════════════════════
#  PATCH  ─  تركيب أكواد التفعيل في BIO4.EXE
# ══════════════════════════════════════════════════════

# ── النوع 1: Change to (بحث واستبدال) ──
PATCH_FIND = bytes.fromhex("81A0CC5200007FFFFFFFE84850D4")
PATCH_REPL = bytes.fromhex("E9892E00009090909090E84850D4")

# ── النوع 2: Find & Paste عند VA 0x002C6D88 ──
PATCH_FP1_OFF  = 0x002C6D88
PATCH_FP1_DATA = bytes.fromhex("81A0CC5200007FFFFFFF608B98344F000085DB7439813BCDCDCDCD7431813B44697363740343EBED8D5B040FB60B50515251E8C5A3D3FF83C4045A598BC85885C974E28D904027D1FF895140EBD761E928D1FFFF")

# ── النوع 2: Find & Paste عند VA 0x00568A20 ──
PATCH_FP2_OFF  = 0x00568A20
PATCH_FP2_DATA = bytes.fromhex(
    "608B82F4272F00"
    "8138CDCDCDCD0F84F3000000"
    "81384469736374034 0EBE9"
    "0FB64E363A480475F4"
    "8D40050FB61831C9"
    "0FB774880 10FB77C8803"
    "505152 8D8A34413000 56 E89A58AAFF"
    "5A6681FFFFFF74096639F80F829D000000"
    "595841 39D972CF"
    "31C90FB774880 10FB77C8803"
    "5051528D8A344130006A0156E84B22AAFF"
    "5A5A6681FFFFFF7421"
    "663B78027D09 66297802 6631FF EB1A"
    "662B78025051 5250 E966000000"
    "5A5958EB0885C075EE5958EB07595866 85FF75B6"
    "4139D97CA7"
    "0FB67C98018D449802 85FF743E"
    "0FB67438FF50535756E88E86A9FF"
    "5E85C07415F6403401750 46A01EB026A00"
    "56E84F90A9FF83C4085F5B584FEBCE"
    "59580FB67C98018D4498028D0438EBBE"
    "61C3"
    "E81FCDA9FFE84C96A9FFEB8E"
    .replace(" ", "")
)


def patch_exe(exe_path: str):
    exe_path = exe_path.strip().strip('"')

    if not os.path.exists(exe_path):
        print(f"\n  [خطأ] الملف غير موجود: {exe_path}")
        return False

    with open(exe_path, "rb") as f:
        data = bytearray(f.read())

    print()
    ok = 0
    err = 0

    # ── 1. Change to (بحث واستبدال) ──
    idx = data.find(PATCH_FIND)
    if idx == -1:
        if data.find(PATCH_REPL) != -1:
            print("  [--] التعديل 1 (Change to): موجود مسبقاً")
        else:
            print("  [خطأ] التعديل 1 (Change to): ما لقيت البايتات في الملف")
            err += 1
    else:
        data[idx : idx + len(PATCH_REPL)] = PATCH_REPL
        print("  [OK] التعديل 1 (Change to): تم")
        ok += 1

    # ── 2. Find & Paste عند file offset 0x002C6D88 ──
    off1 = PATCH_FP1_OFF
    if off1 + len(PATCH_FP1_DATA) > len(data):
        print(f"  [خطأ] التعديل 2 (0x{off1:08X}): الملف أصغر من المتوقع")
        err += 1
    else:
        data[off1 : off1 + len(PATCH_FP1_DATA)] = PATCH_FP1_DATA
        print(f"  [OK] التعديل 2 (Find & Paste @ 0x{off1:08X}): تم")
        ok += 1

    # ── 3. Find & Paste عند file offset 0x00568A20 ──
    off2 = PATCH_FP2_OFF
    if off2 + len(PATCH_FP2_DATA) > len(data):
        print(f"  [خطأ] التعديل 3 (0x{off2:08X}): الملف أصغر من المتوقع")
        err += 1
    else:
        data[off2 : off2 + len(PATCH_FP2_DATA)] = PATCH_FP2_DATA
        print(f"  [OK] التعديل 3 (Find & Paste @ 0x{off2:08X}): تم")
        ok += 1

    if err > 0:
        print(f"\n  [!] فيه {err} خطأ - الملف ما اتحفظ")
        return False

    with open(exe_path, "wb") as f:
        f.write(data)

    print(f"\n  [OK] تم تطبيق {ok} تعديل وحفظ الملف")
    print(f"  الملف : {exe_path}")
    return True


# ══════════════════════════════════════════════════════
#  القائمة التفاعلية
# ══════════════════════════════════════════════════════

def show_menu():
    print()
    print("  +============================================+")
    print("  |       OSD Tool  -  RE4 Modding             |")
    print("  |   استخراج وتجميع ملفات OSD                 |")
    print("  +============================================+")
    print("  |  [ 1 ]  استخراج  EXT    OSD  -> Data.txt   |")
    print("  |  [ 2 ]  تجميع   REPACK  Data.txt -> OSD    |")
    print("  |  [ 3 ]  تركيب أكواد OSD في BIO4.EXE        |")
    print("  |  [ 0 ]  خروج                               |")
    print("  +============================================+")
    print()


def run():
    while True:
        show_menu()
        choice = input("  اختر العملية [1/2/3/0] : ").strip()

        if choice == "0":
            print("\n  مع السلامة!\n")
            break

        elif choice == "1":
            print()
            print("  --- استخراج OSD -----------------------------------")
            print("  مثال : C:\\mods\\r100.OSD")
            print()
            path = input("  المسار : ")
            extract(path)
            print()
            input("  اضغط Enter للرجوع للقائمة...")

        elif choice == "2":
            print()
            print("  --- تجميع REPACK ----------------------------------")
            print("  تقدر تحط مسار ملف OSD أو مسار Data.txt مباشرة")
            print("  مثال 1 : C:\\mods\\r100.OSD")
            print("  مثال 2 : C:\\mods\\r100\\Data.txt")
            print()
            path = input("  المسار : ")
            repack(path)
            print()
            input("  اضغط Enter للرجوع للقائمة...")

        elif choice == "3":
            print()
            print("  --- تركيب أكواد OSD في BIO4.EXE ------------------")
            print("  مثال : C:\\RE4\\BIO4.EXE")
            print()
            path = input("  المسار : ")
            patch_exe(path)
            print()
            input("  اضغط Enter للرجوع للقائمة...")

        else:
            print("\n  [!] اختر 1 أو 2 أو 3 أو 0\n")


if __name__ == "__main__":
    run()
