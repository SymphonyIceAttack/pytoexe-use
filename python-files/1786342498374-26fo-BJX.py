import base64
import hashlib
import os
import re
import socket
import ssl
import struct
import threading
import time

try:
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Hash import SHA512, SHA1, SHA256
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    raise SystemExit("pycryptodome required: pip install pycryptodome")

_RK_PEM = """-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----"""

_PK_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxABI8XC5dAnqbJX6ZLWj
wiAPl18Pj/5q1E8I8raxRRJb7i7wmCuUEExKfwOBjbF4y4Wiugt8cloQniGqTzL7
JfvjpaZWYuM7OTd9YjACJRmm6CDjNsAxAA6PzH7B9LJd49Cp4ViHME65uUorsnQ6
riq0wbZSwNLaKWi9yoLlEX8Ru2CRgHJte35Fo1BcbB2S36SfwBu9tKMUbn1sAqjG
Mnzu8Slm9smtIoeugfvBEz4rpPpBH8n4/Nv89pZPf12O/64bHBfuK4v/g6Ig3T4M
T73MmXfxP4Hv3pI9+9ydnkzc3uZ+4LZbONVCyjJHcndeOcTzw2VIcJP5gVAxgaW
6WQIDAQAB
-----END PUBLIC KEY-----"""

_CK_STR = (
    "MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEArZ9KPHbgRlwgsJSDZKXN"
    "ge4iG99WocrlS8Vy8tm9DlnnAcJZJGYWv1EFhr5ZgV43v4eyh/QI+czayvSuBckX"
    "NbYuyMh1a8ML9nqZDalXhc06eCWINsDPCEfo+cW9Qewk2sq9gXqIaAyfRDlZEr5Z"
    "0ScKxoE/Petd7kfp0OgaYc9NfoNOLLEeHjw58vppnLBEO8A82orcqzUtOj3Yltrf"
    "bSI3oJrxhIwMR+DfCHY0RF11Pk6vNc4w6ePIaz/FBycZ3v+s+roBf56iujh01MOq"
    "OfzCHwlK7pm+uuMvpFruNgkOJlga1Vui2JCukZ0LXdd3vjBoNvEsLsCTVm2akQdL"
    "7auUQvwFfsNugx9iqBlvz8BVFovg7oyyUWKg7jPLMCZW3kq4kkZBGVEmJAXmooOT"
    "LSuWS2M7CvO8X5YVwCNSqk5gsFmT9JqQ3VlY30zmF5BQwb/GtRF2hdMZrZUrQIKQ"
    "sIZvWqIQrWo7tpxxv9e5biInUohyqv1U5UFhmrRNmuof3axhpuD5OAQVF6RjpoUk"
    "hIkjxkTBeeeSpvehLHsC+IZ7Jy5uUFglAI7aWWORYvliK2Ivhdy1BfyV3QA2nh4u"
    "RQiKcp38W8IRzZJo6UApGdBzbx2OOIKQt0IJMWWHU+GuSz4d27lqt72nMFAk1yBe"
    "6VWJsbcBW+I4xxj/ZKpbCQcCAwEAAQ=="
)

_TAG = bytes.fromhex("F4AD529CDE170EE1D1029B4A3CA89820")
_VSTR = "1.18.4.47"
_PATH = "/vanguard/v1/gateway"
_PORT = 8443
_AGENT = "vanguard/1.18.4-29+20260714.000000"
_APP = "com.riotgames.valorant"

_HOSTS = {
    "la": "latam.vg.ac.pvp.net", "br": "br.vg.ac.pvp.net",
    "na": "na.vg.ac.pvp.net", "eu": "eu.vg.ac.pvp.net",
    "ap": "ap.vg.ac.pvp.net", "kr": "kr.vg.ac.pvp.net",
}

_RAI = 1500


def get_host(r: str) -> str:
    return _HOSTS.get((r or "na").lower()[:2], "na.vg.ac.pvp.net")


def _enc_varint(v: int) -> bytes:
    o = b""
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            o += bytes([b | 0x80])
        else:
            o += bytes([b])
            break
    return o


def _enc_tag(f: int, w: int) -> bytes:
    return _enc_varint((f << 3) | w)


def _enc_str(s: str) -> bytes:
    if not s:
        return b""
    b = s.encode("latin-1", errors="replace")
    return _enc_varint(len(b)) + b


def _enc_i32(v: int) -> bytes:
    if v == 0:
        return b""
    return _enc_varint(v & 0xFFFFFFFF)


def _enc_emb(f: int, inner: bytes) -> bytes:
    return _enc_tag(f, 2) + _enc_varint(len(inner)) + inner if inner else b""


def _enc_sf(f: int, s: str) -> bytes:
    if not s:
        return b""
    return _enc_tag(f, 2) + _enc_str(s)


def _enc_if(f: int, v: int) -> bytes:
    if v == 0:
        return b""
    return _enc_tag(f, 0) + _enc_i32(v)


def _sub(f1: int, f2: int, ver: str, var: int = 0) -> bytes:
    b = b""
    b += _enc_if(1, f1)
    b += _enc_if(2, f2)
    if var != 0:
        b += _enc_if(3, var)
    b += _enc_sf(4, ver)
    return b


def _osi(ver: str) -> bytes:
    bd = 19045
    if "." in ver:
        try:
            bd = int(ver.rsplit(".", 1)[1])
        except Exception:
            pass
    b = b""
    b += _enc_if(1, 1)
    b += _enc_if(2, bd)
    b += _enc_sf(3, "Professional")
    b += _enc_sf(4, ver)
    return b


def _mem() -> bytes:
    return b"\x08" + _enc_varint(17179869184)


def _cput(brand: str, model: str) -> bytes:
    return _enc_sf(1, brand) + _enc_sf(2, model)


def _gput(model: str) -> bytes:
    return _enc_sf(2, model)


def _osi2(var: str, ver: str) -> bytes:
    return _enc_sf(3, var) + _enc_sf(4, ver)


def _sec(name: str, state: int = 1) -> bytes:
    return _enc_sf(1, name) + _enc_if(2, state)


def _kv(k: str, v: str) -> bytes:
    return _enc_sf(1, k) + _enc_sf(2, v)


def _ver(a: int, b: int, c: int, d: int) -> bytes:
    return (_enc_if(1, a) + _enc_if(2, b) +
            _enc_if(3, c) + _enc_if(4, d))


def _dev(os_ver: str, cpu_b: str, cpu_m: str) -> bytes:
    return (_enc_emb(1, _osi(os_ver)) +
            _enc_emb(2, _mem()) +
            _enc_emb(3, _cput(cpu_b, cpu_m)))


def build_auth(mid, gt, esid, gid, bs,
               cpub="", hv="", eid="",
               cb="", cm="", gm="",
               ov="Windows 10 Pro", ov2="10.0.19045") -> bytes:
    buf = b""
    buf += _enc_sf(1, mid)
    buf += _enc_emb(2, _sub(1, 2, "10.0.19045"))
    buf += _enc_sf(4, gt)
    buf += _enc_sf(5, cpub or _CK_STR)
    vv = _ver(1, 18, 4, 47)
    buf += _enc_emb(6, vv)
    buf += _enc_emb(7, vv)
    buf += _enc_sf(8, gid)
    buf += _enc_if(9, bs)
    if eid:
        buf += _enc_sf(10, eid)
    core = b""
    if cb or cm:
        core += _enc_emb(1, _cput(cb, cm))
    if gm:
        core += _enc_emb(2, _gput(gm))
    osi = b""
    osi += _enc_if(3, 1)
    osi += _enc_sf(4, ov2 or "10.0.19045")
    core += _enc_emb(3, osi)
    buf += _enc_emb(11, core)
    if esid:
        buf += _enc_sf(13, esid)
    for ft in ("HVCI", "IOMMU", "SB", "TPM2", "VBS"):
        buf += _enc_emb(14, _sec(ft, 1))
    if hv:
        buf += _enc_emb(15, _kv("ht", hv))
    return buf


def build_access(tok: str) -> bytes:
    return _enc_sf(1, tok)


def build_hb(tok: str) -> bytes:
    now_ms = int(time.time() * 1000)
    b = b""
    b += _enc_sf(1, tok)
    b += b"\x10" + _enc_varint(now_ms)
    b += _enc_if(4, 1)
    b += b"\x30" + _enc_varint(1)
    return b


class AuthResp:
    def __init__(self):
        self.token = ""
        self.expiry = ""
        self.srv_pub = ""
        self.sid = ""
        self.eid = ""
        self.uid1 = 0
        self.uid2 = 0


def _dec_varint(data, pos):
    v = 0
    sh = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        v |= (b & 0x7F) << sh
        if not (b & 0x80):
            break
        sh += 7
    return v, pos


def parse_auth(data) -> AuthResp:
    r = AuthResp()
    pos = 0
    while pos < len(data):
        tag, pos = _dec_varint(data, pos)
        f = tag >> 3
        w = tag & 0x7
        if w == 0:
            v, pos = _dec_varint(data, pos)
            if f == 3:
                r.uid1 = v
            elif f == 9:
                r.uid2 = v
        elif w == 2:
            sl, pos = _dec_varint(data, pos)
            if pos + sl > len(data):
                break
            s = data[pos:pos + sl]
            pos += sl
            if f == 1:
                r.token = s.decode("latin-1", "replace")
            elif f == 2:
                r.expiry = s.decode("latin-1", "replace")
            elif f == 4:
                r.srv_pub = s.decode("latin-1", "replace")
            elif f == 8:
                r.sid = s.decode("latin-1", "replace")
            elif f == 10:
                r.eid = s.decode("latin-1", "replace")
        elif w == 5:
            pos += 4
        elif w == 1:
            pos += 8
        else:
            break
    return r


def _b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def gcm_enc(key: bytes, pt: bytes):
    iv = get_random_bytes(12)
    c = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=16)
    ct, tag = c.encrypt_and_digest(pt)
    return ct, tag, iv


def rsa_enc(pub_pem: str, data: bytes) -> bytes:
    k = RSA.import_key(pub_pem)
    c = PKCS1_OAEP.new(k, hashAlgo=SHA512)
    return c.encrypt(data)


def _norm_pub(spub) -> str:
    if not spub:
        return None
    if spub.startswith("-----BEGIN"):
        try:
            RSA.import_key(spub)
            return spub
        except Exception:
            pass
    try:
        der = base64.b64decode(spub)
        from Crypto.Util.asn1 import DerSequence
        seq = DerSequence().decode(der)
        n = int(seq[0][1][1][0])
        e = int(seq[0][1][1][1])
        k = RSA.construct((n, e))
        return k.export_key().decode("ascii")
    except Exception:
        return None


def make_env(proto: bytes, pub_pem: str, tb: int) -> bytes:
    ak = get_random_bytes(32)
    ct, tag, iv = gcm_enc(ak, proto)
    re = rsa_enc(pub_pem, ak)
    inner = b"\x52\x47\x01\x00" + re + iv + ct + tag
    env = b"\x08" + bytes([tb]) + b"\x12" + _enc_varint(len(inner)) + inner
    return env


def decrypt_resp(payload: bytes) -> bytes:
    pos = 0
    if pos >= len(payload) or payload[pos] != 0x08:
        return b""
    pos += 1
    if pos >= len(payload):
        return b""
    pos += 1
    if pos >= len(payload) or payload[pos] != 0x12:
        return b""
    pos += 1
    ln, pos = _dec_varint(payload, pos)
    if ln > len(payload) - pos:
        ln = len(payload) - pos
    if pos + 4 > len(payload) or payload[pos:pos + 2] != b"\x52\x47":
        return b""
    if payload[pos + 3] > 2:
        return b""
    pos += 4
    pk = _load_priv()
    rl = pk.size_in_bytes() if pk else 256
    if pos + rl + 12 + 16 > len(payload):
        return b""
    ek = payload[pos:pos + rl]
    pos += rl
    iv = payload[pos:pos + 12]
    pos += 12
    ct = payload[pos:len(payload) - 16]
    tag = payload[len(payload) - 16:]
    ak = rsa_dec(ek)
    if len(ak) != 32:
        return b""
    try:
        c = AES.new(ak, AES.MODE_GCM, nonce=iv, mac_len=16)
        pt = c.decrypt_and_verify(ct, tag)
        return pt
    except Exception:
        return b""


_pk_obj = None
_pk_loaded = False


def _load_priv():
    global _pk_obj, _pk_loaded
    if not _pk_loaded:
        _pk_loaded = True
        try:
            _pk_obj = RSA.import_key(_RK_PEM)
        except Exception:
            _pk_obj = None
    return _pk_obj


def rsa_dec(cb: bytes) -> bytes:
    k = _load_priv()
    if k is None:
        return b""
    try:
        c = PKCS1_OAEP.new(k, hashAlgo=SHA512)
        return c.decrypt(cb)
    except Exception:
        return b""


def jwt_payload(jwt: str) -> str:
    try:
        parts = jwt.split(".")
        if len(parts) < 2:
            return ""
        p = parts[1]
        p += "=" * (-len(p) % 4)
        raw = base64.urlsafe_b64decode(p)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def jget(payload: str, key: str) -> str:
    m = re.search(r'"%s"\s*:\s*"([^"]*)"' % re.escape(key), payload)
    if m:
        return m.group(1)
    m = re.search(r'"%s"\s*:\s*(\d+|\btrue\b|\bfalse\b|\bnull\b)' % re.escape(key), payload)
    if m:
        return m.group(1)
    return ""


def _nshard(v: str) -> str:
    v = v.strip().lower()
    if not v:
        return ""
    if v in ("la2", "la1", "la"):
        return "la"
    if v in ("br1", "br"):
        return "br"
    if v in ("na1", "na"):
        return "na"
    if v in ("eu1", "eu2", "eu3", "eu"):
        return "eu"
    if v in ("ap1", "ap2", "ap"):
        return "ap"
    if v == "kr":
        return "kr"
    return ""


def get_shard(jwt: str) -> str:
    p = jwt_payload(jwt)
    if not p:
        return ""
    dp = p.find('"dat"')
    if dp != -1:
        br = p.find("{", dp)
        cl = p.find("}", br)
        if br != -1 and cl != -1:
            do = p[br:cl + 1]
            for k in ("r", "region", "affinity"):
                if v := _nshard(jget(do, k)):
                    return v
    for key in ("r", "affinity", "region", "shard", "player_region", "geo_region", "geo", "loc"):
        if v := _nshard(jget(p, key)):
            return v

    def _cr(cty: str) -> str:
        cty = cty.lower()
        if cty in ("usa", "us", "can", "ca", "mex", "mx"):
            return "na"
        if cty in ("kor", "kr"):
            return "kr"
        if cty in ("bra", "br", "arg", "ar", "chl", "cl", "col", "co", "per", "pe",
                   "ven", "ve", "ecu", "ec", "bol", "bo", "pry", "py", "ury", "uy"):
            return "br"
        if cty in ("gtm", "gt", "cri", "cr", "pan", "pa", "hnd", "hn", "slv", "sv",
                   "nic", "ni", "dom", "do"):
            return "la"
        if cty in ("deu", "de", "fra", "fr", "gbr", "gb", "uk", "esp", "es", "ita", "it",
                   "pol", "pl", "tur", "tr", "nld", "nl", "bel", "be", "che", "ch",
                   "aut", "at", "swe", "se", "nor", "no", "dnk", "dk", "fin", "fi",
                   "prt", "pt", "grc", "gr", "cze", "cz", "hun", "hu", "rou", "ro",
                   "rus", "ru", "ukr", "ua", "mda", "md"):
            return "eu"
        if cty in ("jpn", "jp", "aus", "au", "sgp", "sg", "nzl", "nz", "phl", "ph",
                   "tha", "th", "idn", "id", "mys", "my", "vnm", "vn", "twn", "tw",
                   "hkg", "hk", "mmr", "mm", "pak", "pk"):
            return "ap"
        return ""

    for ck in ("cty", "lcty"):
        if v := _cr(jget(p, ck)):
            return v
    iss = jget(p, "iss").lower()
    for mk, rg in ((".la.", "la"), ("latam", "la"), (".br.", "br"),
                   (".na.", "na"), ("na1", "na"), (".eu.", "eu"),
                   ("eu1", "eu"), ("emea", "eu"), ("europe", "eu"),
                   (".ap.", "ap"), ("ap1", "ap"), (".kr.", "kr")):
        if mk in iss:
            return rg
    return ""


def get_puuid(jwt: str) -> str:
    p = jwt_payload(jwt)
    for k in ("sub", "puuid"):
        v = jget(p, k)
        if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", v):
            return v
    m = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", p)
    return m.group(0) if m else ""


def get_sid(jwt: str, sid: str, puuid: str) -> str:
    if sid and sid != puuid:
        return sid
    jp = get_puuid(jwt)
    if sid and sid != jp:
        return sid
    return ""


class HwProf:
    def __init__(self):
        self.cpu_b = ""
        self.cpu_m = ""
        self.cpu_c = 0
        self.gpu_b = ""
        self.gpu_m = ""
        self.bios_v = ""
        self.bios_r = ""
        self.mb_m = ""
        self.vol_s = ""
        self.mguid = ""
        self.hn = ""
        self.os_v = ""
        self.os_b = ""


_CPU_LIST = [
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i5-9400F CPU @ 2.90GHz", 6),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz", 12),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz", 8),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz", 16),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i5-11400F CPU @ 2.60GHz", 12),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i7-11700K CPU @ 3.60GHz", 16),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i5-12400F CPU @ 2.50GHz", 12),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i7-12700K CPU @ 3.60GHz", 20),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i9-12900K CPU @ 3.20GHz", 24),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i5-13400F CPU @ 2.50GHz", 16),
    ("GenuineIntel", "Intel", "Intel(R) Core(TM) i7-13700K CPU @ 3.40GHz", 24),
    ("AuthenticAMD", "AMD", "AMD Ryzen 5 3600 6-Core Processor", 12),
    ("AuthenticAMD", "AMD", "AMD Ryzen 7 3700X 8-Core Processor", 16),
    ("AuthenticAMD", "AMD", "AMD Ryzen 5 5600X 6-Core Processor", 12),
    ("AuthenticAMD", "AMD", "AMD Ryzen 7 5700X 8-Core Processor", 16),
    ("AuthenticAMD", "AMD", "AMD Ryzen 7 5800X 8-Core Processor", 16),
    ("AuthenticAMD", "AMD", "AMD Ryzen 9 5900X 12-Core Processor", 24),
    ("AuthenticAMD", "AMD", "AMD Ryzen 5 7600X 6-Core Processor", 12),
    ("AuthenticAMD", "AMD", "AMD Ryzen 7 7700X 8-Core Processor", 16),
    ("AuthenticAMD", "AMD", "AMD Ryzen 9 7900X 12-Core Processor", 24),
]

_GPU_LIST = [
    ("NVIDIA", "NVIDIA GeForce GTX 1660 SUPER"),
    ("NVIDIA", "NVIDIA GeForce GTX 1660 Ti"),
    ("NVIDIA", "NVIDIA GeForce RTX 2060"),
    ("NVIDIA", "NVIDIA GeForce RTX 2070 SUPER"),
    ("NVIDIA", "NVIDIA GeForce RTX 3060"),
    ("NVIDIA", "NVIDIA GeForce RTX 3060 Ti"),
    ("NVIDIA", "NVIDIA GeForce RTX 3070"),
    ("NVIDIA", "NVIDIA GeForce RTX 3080"),
    ("NVIDIA", "NVIDIA GeForce RTX 4060"),
    ("NVIDIA", "NVIDIA GeForce RTX 4060 Ti"),
    ("NVIDIA", "NVIDIA GeForce RTX 4070"),
    ("AMD", "AMD Radeon RX 6600"),
    ("AMD", "AMD Radeon RX 6600 XT"),
    ("AMD", "AMD Radeon RX 6700 XT"),
    ("AMD", "AMD Radeon RX 6800 XT"),
    ("AMD", "AMD Radeon RX 7600"),
    ("AMD", "AMD Radeon RX 7700 XT"),
]

_MB_I = [
    ("American Megatrends Inc.", "ASUS PRIME Z490-P", "0501"),
    ("American Megatrends Inc.", "ASUS ROG STRIX Z490-F", "0603"),
    ("American Megatrends Inc.", "ASUS PRIME Z590-P", "0606"),
    ("American Megatrends Inc.", "ASUS TUF GAMING Z590", "1401"),
    ("American Megatrends Inc.", "ASUS PRIME Z690-P", "1201"),
    ("American Megatrends Inc.", "ASUS ROG STRIX Z690-F", "1403"),
    ("American Megatrends Inc.", "MSI MAG Z490 TOMAHAWK", "A.40"),
    ("American Megatrends Inc.", "MSI MPG Z590 GAMING", "A.60"),
    ("American Megatrends Inc.", "MSI MAG Z690 TOMAHAWK", "A.80"),
    ("American Megatrends Inc.", "Gigabyte Z490 AORUS", "F60"),
    ("American Megatrends Inc.", "Gigabyte Z590 AORUS", "F65"),
    ("American Megatrends Inc.", "Gigabyte Z690 AORUS", "F10"),
]

_MB_A = [
    ("American Megatrends Inc.", "ASUS ROG STRIX X570-E", "2606"),
    ("American Megatrends Inc.", "ASUS TUF GAMING X570", "2803"),
    ("American Megatrends Inc.", "ASUS PRIME B550-PLUS", "2402"),
    ("American Megatrends Inc.", "MSI MAG X570 TOMAHAWK", "A.60"),
    ("American Megatrends Inc.", "MSI MPG B550 GAMING", "A.40"),
    ("American Megatrends Inc.", "Gigabyte X570 AORUS", "F34"),
    ("American Megatrends Inc.", "Gigabyte B550 AORUS", "F17"),
    ("American Megatrends Inc.", "ASRock X570 Phantom", "P4.10"),
]

_OS_VER = ["10.0.19044", "10.0.19045", "10.0.22000", "10.0.22621", "10.0.22631", "10.0.26100"]


def rand_hw() -> HwProf:
    sd = os.urandom(64)
    p = HwProf()
    cpu = _CPU_LIST[sd[0] % len(_CPU_LIST)]
    gpu = _GPU_LIST[sd[1] % len(_GPU_LIST)]
    mbs = _MB_I if cpu[0] == "GenuineIntel" else _MB_A
    mb = mbs[sd[2] % len(mbs)]
    p.cpu_b = cpu[1]
    p.cpu_m = cpu[2]
    p.cpu_c = cpu[3]
    p.gpu_b = gpu[0]
    p.gpu_m = gpu[1]
    p.bios_v = mb[0]
    p.bios_r = mb[2]
    p.mb_m = mb[1]
    p.vol_s = "%08X" % int.from_bytes(sd[4:8], "big")
    g = sd[8:24]
    p.mguid = ("%02x%02x%02x%02x-%02x%02x-4%01x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x"
               % (g[0], g[1], g[2], g[3], g[4], g[5],
                  g[6] & 0x0F, g[7], (g[8] & 0x3F) | 0x80, g[9],
                  g[10], g[11], g[12], g[13], g[14], g[15]))
    pfx = "DESKTOP-" if sd[24] % 2 == 0 else "WIN-"
    cs = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    p.hn = pfx + "".join(cs[b % len(cs)] for b in sd[25:32])
    p.os_v = _OS_VER[sd[32] % len(_OS_VER)]
    try:
        p.os_b = int(p.os_v.rsplit(".", 1)[1])
    except Exception:
        p.os_b = 19045
    return p


_PIPE = r"\\.\pipe\933823D3-C77B-4BAE-89D7-A92B567236BC"
_MUTEX = "Global\\587203BC-5798-47BA-8BDA-C63D7DE25FCD"

_URX = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_JRX = re.compile(r"(eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})")


def find_jwts(buf: bytes) -> list:
    s = "".join(chr(b) if 0x20 <= b < 0x7F else " " for b in buf)
    return [m[0] for m in _JRX.finditer(s)]


def find_uuids(buf: bytes) -> list:
    s = "".join(chr(b) if 0x20 <= b < 0x7F else " " for b in buf)
    return _URX.findall(s)


def uuid_b16(u: str) -> bytes:
    if len(u) != 36:
        return b""
    h = u.replace("-", "")
    if len(h) != 32:
        return b""
    r = bytes.fromhex(h)
    return bytes([r[3], r[2], r[1], r[0],
                  r[5], r[4],
                  r[7], r[6]]) + r[8:]


def read_lpstr(buf: bytes, off):
    if off + 4 > len(buf):
        return "", off
    ln = int.from_bytes(buf[off:off + 4], "big")
    off += 4
    if off + ln > len(buf):
        return "", off
    s = buf[off:off + ln].decode("latin-1", "replace")
    off += ln
    return s, off


def proc_auth(jwt: str, puuid: str, sid: str) -> bytes:
    r = bytearray()
    if jwt and puuid:
        r.append(0x00)
        pb = puuid.encode("latin-1", "replace")
        r += len(pb).to_bytes(4, "big") + pb
        if sid:
            sb = sid.encode("latin-1", "replace")
            r += len(sb).to_bytes(4, "big") + sb
    else:
        r.append(0x01)
    return bytes(r)


def proc_tasks(pkt: bytes) -> bytes:
    if len(pkt) >= 8:
        return bytes([(pkt[0] + 1) & 0xFF, 0, 0, 0, pkt[4], pkt[5], pkt[6], pkt[7]])
    return b"\x66\x00\x00\x00\x00\x00\x00\x00"


class _MState:
    def __init__(self):
        self.step = -1
        self.lock = threading.Lock()

    def next(self, magic: int) -> int:
        with self.lock:
            self.step = (self.step + 1) % 5
            if self.step == 0:
                return magic + 1
            if self.step == 1:
                return magic + 3
            if self.step == 2:
                return magic - 1
            if self.step == 3:
                return magic + 2
            return magic + 5


class PipeSvc:
    def __init__(self, cli: "Client"):
        self.cli = cli
        self.ms = _MState()
        self.running = False
        self._th = None
        self.cur = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()

    def push_auth(self):
        p = self.cur
        if p is None:
            return False
        try:
            import win32file
            mg = int.from_bytes(b"\x00\x00\x00\x00", "little")
            inj = bytearray(40)
            rm = self.ms.next(mg)
            rm_u = (rm if rm >= 0 else rm + (1 << 32)) & 0xFFFFFFFF
            inj[0:4] = rm_u.to_bytes(4, "little")
            inj[4:8] = (40).to_bytes(4, "little")
            inj[8:12] = (9).to_bytes(4, "little")
            win32file.WriteFile(p, bytes(inj))
            self.cli.log("[P][RA] fresh type-9 injected (40B)")
            return True
        except Exception as e:
            self.cli.log("[P][RA] inject fail: %s" % e)
            return False

    def stop(self):
        self.running = False

    def _w(self, p, data: bytes, tag: str):
        if not data:
            self.cli.log(tag + " skipped empty")
            return False
        try:
            import win32file
            win32file.WriteFile(p, data)
            self.cli.log(tag + " ok=%d" % len(data))
            return True
        except Exception as e:
            self.cli.log(tag + " err=%s" % e)
            return False

    def _handle(self, p):
        self.cur = p
        self.cli.pipe_on = True
        self.cli.log("[P] registered")
        hb = 0
        pc = 0
        import win32file
        import pywintypes
        try:
            ch = bytearray(36)
            ch[0:8] = (0x24000003E9).to_bytes(8, "little")
            ch[8:16] = (1).to_bytes(8, "little")
            ch[24:28] = (4).to_bytes(4, "little")
            self._w(p, bytes(ch), "[P] init 36B")

            while self.running:
                try:
                    hr, data = win32file.ReadFile(p, 16384)
                    if not data:
                        break
                except pywintypes.error:
                    break
                pc += 1
                self.cli.log("[P] pkt#%d %dB(0x%02x)" % (pc, len(data), data[0] if data else 0))

                if len(data) == 40 and data[0] == 0x03:
                    r = bytearray(data)
                    r[0] = 0x04
                    hb += 1
                    self._w(p, bytes(r), "[P][HB] ack#%d" % hb)
                    continue

                if data[0] == 0x64:
                    hx = " ".join("%02x" % b for b in data[:16])
                    self.cli.log("[P][64] AUTH %dB %s" % (len(data), hx))
                    if len(data) > 40:
                        self.cli.log("[P][64] scanning...")
                        self.cli.on_pipe_data(data)
                    jwt = self.cli.jwt
                    puuid = self.cli.puuid
                    sid = self.cli.sid
                    if not jwt:
                        self.cli.log("[P][64] no jwt, wait 2s")
                        time.sleep(2)
                        jwt, puuid, sid = self.cli.jwt, self.cli.puuid, self.cli.sid
                    self.cli.log("[P][64] jwt=%s pid=%s" %
                                 ("--" if not jwt else jwt[:20] + "..",
                                  "--" if not puuid else puuid[:8] + ".."))
                    r = proc_auth(jwt, puuid, sid)
                    self._w(p, r, "[P][64] AUTH resp")
                    self.cli.log("[P][64] done")
                    continue

                if len(data) >= 36:
                    ct = int.from_bytes(data[8:12], "little")
                    if ct in (1, 2, 4, 5, 6):
                        mg = int.from_bytes(data[0:4], "little")
                        self.cli.log("[P][C] type=%d mg=0x%x %dB" % (ct, mg, len(data)))
                        inj9 = False
                        if ct == 6:
                            reply = bytes([8, 9, 18, 0])
                        elif ct == 5:
                            reply = bytearray(56)
                            rm = self.ms.next(mg)
                            reply[0:4] = rm.to_bytes(4, "little")
                            reply[4:8] = (56).to_bytes(4, "little")
                            reply[8:12] = (1).to_bytes(4, "little")
                            reply[24:28] = (16).to_bytes(4, "little")
                            reply = bytes(reply)
                        elif ct == 4:
                            if len(data) > 100:
                                self.cli.log("[P][C] t4 scan")
                                self.cli.on_pipe_data(data)
                            au = ""
                            uu = find_uuids(data)
                            if uu:
                                au = uu[0]
                            if not au:
                                au = self.cli.sid or self.cli.puuid
                            if not au:
                                au = "00000000-0000-0000-0000-000000000000"
                            reply = bytearray(0x3C)
                            reply[0:4] = (mg + 1).to_bytes(4, "little")
                            reply[4:8] = (0x40).to_bytes(4, "little")
                            reply[8:12] = (1).to_bytes(4, "little")
                            reply[24:28] = (0x18).to_bytes(4, "little")
                            gd = uuid_b16(au)
                            if gd:
                                reply[0x24:0x34] = gd
                            reply[0x34:0x3C] = int(time.time() * 1000).to_bytes(8, "little")
                            reply = bytes(reply)
                            inj9 = True
                            self.cli.log("[P][C] t4 ack uuid=%s mg=0x%x" % (au, mg + 1))
                        elif ct == 1:
                            reply = bytearray(data)
                            rm = self.ms.next(mg)
                            reply[0:4] = rm.to_bytes(4, "little")
                            reply = bytes(reply)
                            self.cli.log("[P][C] t1 echo mg=0x%x" % rm)
                        elif ct == 2:
                            reply = bytearray(48)
                            rm = self.ms.next(mg)
                            reply[0:4] = rm.to_bytes(4, "little")
                            reply[4:8] = (48).to_bytes(4, "little")
                            reply[8:12] = (1).to_bytes(4, "little")
                            reply[24:28] = (8).to_bytes(4, "little")
                            reply = bytes(reply)
                            self.cli.log("[P][C] t2 ack mg=0x%x" % rm)

                        self._w(p, reply, "[P][C] t%d" % ct)
                        if inj9:
                            time.sleep(0.2)
                            inj = bytearray(40)
                            rm = self.ms.next(mg)
                            inj[0:4] = rm.to_bytes(4, "little")
                            inj[4:8] = (40).to_bytes(4, "little")
                            inj[8:12] = (9).to_bytes(4, "little")
                            self._w(p, bytes(inj), "[P][C] inj t9")
                        continue

                if data[0] == 0x65 and len(data) >= 4:
                    ack = proc_tasks(data)
                    self._w(p, ack, "[P][65] TASKS ack")
                    self.cli.log("[P][65] done")
                    if len(data) > 100:
                        self.cli.log("[P][65] scan...")
                        old = self.cli.jwt
                        self.cli.on_pipe_data(data)
                        new = self.cli.jwt
                        if new and new != old and old:
                            self.cli.log("[L] jwt changed -> reauth")
                            self.cli.req_reauth()
                    continue

                if data[0] == 0x66 and len(data) >= 4:
                    ack = proc_tasks(data)
                    self._w(p, ack, "[P][66] MOD ack")
                    self.cli.log("[P][66] done")
                    continue

                if data[0] == 0x67 and len(data) >= 8:
                    self.cli.vgk_data = data
                    self.cli.log("[P][67] captured %dB" % len(data))
                    if len(data) >= 4:
                        ec = bytearray(data)
                        nm = (int.from_bytes(data[0:4], "little") + 1) & 0xFFFFFFFF
                        ec[0:4] = nm.to_bytes(4, "little")
                        self._w(p, bytes(ec), "[P][67] echo")
                    continue

                if data[0] == 0x68 and len(data) == 68:
                    self._w(p, data, "[P][68] echo")
                    continue

                if len(data) > 100:
                    self.cli.log("[P] scan...")
                    self.cli.on_pipe_data(data)
                if len(data) >= 4:
                    ec = bytearray(data)
                    nm = (int.from_bytes(data[0:4], "little") + 1) & 0xFFFFFFFF
                    ec[0:4] = nm.to_bytes(4, "little")
                    self._w(p, bytes(ec), "[P] echo")
        except Exception as e:
            self.cli.log("[P] err: %s" % e)
        finally:
            self.cli.pipe_on = False
            self.cur = None
            try:
                win32file.CloseHandle(p)
            except Exception:
                pass
            self.cli.log("[P] disconnected")

    def _loop(self):
        import win32pipe
        import pywintypes
        while self.running:
            try:
                p = win32pipe.CreateNamedPipe(
                    _PIPE,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    1048576, 1048576, 500, None)
            except pywintypes.error:
                time.sleep(1)
                continue
            self.cli.log("[P] waiting...")
            try:
                win32pipe.ConnectNamedPipe(p, None)
            except pywintypes.error as e:
                if e.winerror != 535:
                    try:
                        win32file.CloseHandle(p)
                    except Exception:
                        pass
                    continue
            self.cli.log("[P] connected")
            threading.Thread(target=self._handle, args=(p,), daemon=True).start()


def make_mutex():
    try:
        import win32event
        import win32api
        return win32event.CreateMutex(None, False, _MUTEX)
    except Exception:
        return None


class GwSess:
    def __init__(self):
        self.last_resp = b""
        self.srv_pub = ""
        self.tok = ""
        self.eid = ""
        self.ok = False

    def reset(self):
        self.__init__()


def beep(f=880, d=120):
    try:
        import winsound
        winsound.Beep(f, d)
    except Exception:
        pass


def stop_svc():
    try:
        import subprocess
        fl = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        subprocess.run(["sc", "stop", "vgc"], capture_output=True, timeout=15,
                       creationflags=fl)
    except Exception:
        pass


def start_svc():
    try:
        import subprocess
        fl = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        subprocess.run(["sc", "start", "vgc"], capture_output=True, timeout=15,
                       creationflags=fl)
    except Exception:
        pass


def svc_running():
    try:
        import subprocess
        fl = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        r = subprocess.run(["sc", "query", "vgc"], capture_output=True, timeout=10,
                           creationflags=fl, text=True)
        return "RUNNING" in r.stdout
    except Exception:
        return False


def game_running():
    try:
        import subprocess
        fl = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq VALORANT-Win64-Shipping.exe"],
                           capture_output=True, timeout=10, creationflags=fl, text=True)
        return "VALORANT" in r.stdout
    except Exception:
        return False


def ksvc_running():
    try:
        import subprocess
        fl = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq vgksvc.exe"],
                           capture_output=True, timeout=10, creationflags=fl, text=True)
        return "vgksvc" in r.stdout
    except Exception:
        return False


class Client:
    def __init__(self, log_cb=None):
        self.log = log_cb or (lambda m: print(m))
        self.jwt = ""
        self.sid = ""
        self.puuid = ""
        self.region = ""
        self.sess = GwSess()
        self.pool = []
        self.idx = 0
        self.hw = rand_hw()
        self.ka_on = False
        self.stop_ev = threading.Event()
        self._pf = None
        self._lk = threading.Lock()
        self.vgk_data = b""
        self.auto = True
        self.ra_pend = threading.Event()
        self.last_ra = 0.0
        self.pipe_on = False
        self.cool_until = 0.0
        self.f2_int = 360
        self.last_f2 = 0.0
        self.pipe_svc = None

    def on_pipe_data(self, data: bytes):
        jwts = find_jwts(data)
        if not jwts:
            self.log("[P] no jwt found")
            return
        jwt = jwts[0]
        self.log("[P] jwt found=%d" % len(jwts))
        uu = find_uuids(data)
        fu = uu[0] if uu else ""
        lu = uu[-1] if uu else ""
        puuid = fu or get_puuid(jwt)
        sid = get_sid(jwt, lu, puuid)
        self.log("[P] pid=%s sid=%s" % (puuid[:8], sid[:8]))
        with self._lk:
            if jwt == self.jwt and sid == self.sid:
                return
            self.jwt = jwt
            self.sid = sid
            self.puuid = puuid
        self.log("[P] NEW TOKEN captured (%d)" % len(jwt))
        if self.auto:
            self.log("[P] auto send enabled")
            threading.Thread(target=self._mint_async, args=(jwt, sid, puuid), daemon=True).start()
        else:
            self.log("[P] token saved -- press F1")

    def _mint_async(self, jwt, sid, puuid):
        try:
            self.mint(jwt, sid, puuid)
        except Exception as e:
            self.log("[G] mint err: %s" % e)

    def req_reauth(self):
        self.log("[K] reauth forced")
        threading.Thread(target=self.reauth, daemon=True).start()

    def set_pool_file(self, path):
        self._pf = path

    def ensure_pool(self, count=3000):
        with self._lk:
            if self.pool:
                return True
            if self._pf and os.path.isfile(self._pf):
                try:
                    with open(self._pf, encoding="utf-8") as f:
                        cur = {}
                        for line in f:
                            line = line.rstrip("\r\n")
                            if not line or line.startswith("#"):
                                if cur.get("mid") and cur.get("ht"):
                                    self.pool.append((cur["mid"], cur["ht"]))
                                cur = {}
                            elif line.startswith("machine_id="):
                                cur["mid"] = line[11:]
                            elif line.startswith("ht="):
                                cur["ht"] = line[3:]
                        if cur.get("mid") and cur.get("ht"):
                            self.pool.append((cur["mid"], cur["ht"]))
                    self.log("[G] pool loaded: %d" % len(self.pool))
                    return bool(self.pool)
                except Exception as e:
                    self.log("[G] pool read err: %s" % e)
            self.log("[G] generating pool (%d)..." % count)
            self.pool = gen_pool(count)
            if self._pf:
                try:
                    with open(self._pf, "w", encoding="utf-8") as f:
                        for i, (mid, ht) in enumerate(self.pool, 1):
                            f.write("# %d\nmachine_id=%s\nht=%s\n\n" % (i, mid, ht))
                    self.log("[G] pool saved -> %s" % self._pf)
                except Exception:
                    pass
            return True

    def select_machine(self):
        with self._lk:
            if not self.pool:
                return None, None
            self.idx = self.idx % len(self.pool)
            return self.pool[self.idx]

    def next_machine(self):
        with self._lk:
            if not self.pool:
                return None, None
            self.idx = (self.idx + 1) % len(self.pool)
            return self.pool[self.idx]

    def resolve_region(self, jwt=None):
        if self.region:
            return self.region
        rg = get_shard(jwt or self.jwt)
        if not rg:
            rg = "na"
        return rg

    def build_auth_env(self, mid, ht, jwt, sid):
        proto = build_auth(
            mid, jwt, sid, _APP, 3, _CK_STR, ht, "",
            self.hw.cpu_b, self.hw.cpu_m, self.hw.gpu_m,
            "Windows 10 Pro", self.hw.os_v)
        return make_env(proto, _PK_PEM, 0x03)

    def do_auth(self, region, mid, ht):
        env = self.build_auth_env(mid, ht, self.jwt, self.sid)
        if not env:
            return False
        self.log("[G] POST %s r=%s a=3 %dB" % (get_host(region), region, len(env)))
        try:
            st, body = send_req(env, self.puuid, region, 3)
        except Exception as e:
            self.log("[G] AUTH exc: %r" % e)
            return False
        self.log("[G] HTTP %d a=3 %dB %s" %
                 (st, len(body), body[:80].hex() if body else ""))
        if st == 200 and body:
            self.sess.last_resp = body
            try:
                dec = decrypt_resp(body)
            except Exception as e:
                self.log("[G] decrypt exc: %r" % e)
                return False
            if dec:
                r = parse_auth(dec)
                self.sess.srv_pub = r.srv_pub
                self.sess.tok = r.token
                self.sess.eid = r.eid
                self.sess.ok = True
            self.log("[G] *** AUTH OK r=%s ***" % region)
            self.sess.ok = True
            self.last_ra = time.time()
            beep(880, 120)
            stop_svc()
            return True
        if st == 429:
            self.cool_until = time.time() + 180
            self.log("[G] 429 -> cooldown +180s")
        if st in (429, 500, 503):
            self.log("[G] rate-limited/err (HTTP %d)" % st)
        return False

    def do_access(self, region):
        if not self.sess.last_resp:
            return False
        sp = self.sess.srv_pub
        if not sp:
            return False
        if sp.startswith("-----BEGIN"):
            from Crypto.PublicKey import RSA
            from Crypto.Util.asn1 import DerSequence
            try:
                pub = RSA.import_key(sp)
                der = pub.export_key(format="DER")
                from Crypto.Cipher import PKCS1_OAEP
                from Crypto.PublicKey import RSA as _R
                key = _R.import_key(sp)
                c = PKCS1_OAEP.new(key, hashAlgo=SHA512)
            except Exception as e:
                self.log("[G] access pubkey fail: %s" % e)
                return False
        else:
            der = base64.b64decode(sp)
            from Crypto.PublicKey import RSA as _R
            from Crypto.Util.asn1 import DerSequence
            try:
                seq = DerSequence().decode(der)
                key = _R.construct((int(seq[0][1][1][0]), int(seq[0][1][1][1])))
            except Exception as e:
                self.log("[G] access pubkey parse fail: %s" % e)
                return False
        proto = build_access(self.sess.tok)
        env = make_env(proto, sp, 0x04)
        self.log("[G] POST %s a=4 %dB" % (get_host(region), len(env)))
        st, body = send_req(env, self.puuid, region, 4)
        self.log("[G] HTTP %d a=4 %dB" % (st, len(body)))
        return st == 200 and bool(body)

    def do_hb(self, region):
        if not self.sess.last_resp:
            return False
        pub = _norm_pub(self.sess.srv_pub)
        if not pub:
            self.log("[G] hb skip: bad pubkey")
            return False
        proto = build_hb(self.sess.tok)
        env = make_env(proto, pub, 0x07)
        st, body = send_req(env, self.puuid, region, 7)
        self.log("[G] HTTP %d a=7" % st)
        return st == 200

    def mint(self, jwt, sid, puuid):
        if time.time() < self.cool_until:
            self.log("[G] mint skip: cooldown (%ds)" %
                     int(self.cool_until - time.time()))
            return False
        self.jwt = jwt
        self.sid = sid
        self.puuid = puuid
        region = self.resolve_region(jwt)
        self.region = region
        self.log("[G] mint r=%s" % region)
        if not self.ensure_pool():
            self.log("[G] ERR: no pool")
            return False
        mid, ht = self.next_machine()
        if not mid:
            return False
        if self.do_auth(region, mid, ht):
            return True
        return False

    def reauth(self):
        try:
            return self._reauth_impl()
        except Exception as e:
            self.log("[K] reauth exc: %r" % e)
            import traceback
            self.log("[K] " + traceback.format_exc())
            return False

    def _reauth_impl(self):
        if self.ra_pend.is_set():
            self.log("[K] reauth skip: in progress")
            return False
        if not self.jwt or not self.puuid:
            self.log("[K] reauth skip: no jwt/puuid")
            beep(440, 120)
            return False
        if time.time() < self.cool_until:
            self.log("[K] reauth skip: cooldown (%ds)" %
                     int(self.cool_until - time.time()))
            return False
        self.ra_pend.set()
        try:
            return self._do_reauth()
        finally:
            self.ra_pend.clear()

    def _do_reauth(self):
        region = self.resolve_region()
        mid, ht = self.next_machine()
        if not mid:
            return False
        self.log("[K] reauth -> %s (idx=%d)" % (region, self.idx))
        ok = self.do_auth(region, mid, ht)
        if ok:
            self.last_ra = time.time()
            self.log("[K] reauth OK -> %s" % region)
            beep(880, 120)
            try:
                self.do_access(region)
            except Exception as e:
                self.log("[K] access fail: %s" % e)
            try:
                self.do_hb(region)
            except Exception as e:
                self.log("[K] hb fail: %s" % e)
            if self.pipe_svc is not None:
                try:
                    self.pipe_svc.push_auth()
                except Exception as e:
                    self.log("[K] push fail: %s" % e)
        else:
            self.log("[K] reauth FAIL")
        return ok

    def manual_refresh(self):
        self.log("[U] refresh requested")
        self.log("[U] jwt=%s pid=%s r=%s" %
                 (bool(self.jwt), bool(self.puuid), self.region))
        beep(880, 80)
        threading.Thread(target=self.reauth, daemon=True).start()

    def _safe_reauth(self):
        try:
            self.reauth()
        except Exception as e:
            self.log("[K] exc: %s" % e)

    def _ka_tick(self):
        try:
            if self.sess.last_resp and self.sess.tok:
                if time.time() < self.cool_until:
                    self.log("[K] hb skip: cooldown")
                    return
                region = self.resolve_region()
                self.do_hb(region)
                self.log("[K] hb done -> alive")
            else:
                self.manual_refresh()
        except Exception as e:
            self.log("[K] tick exc: %s" % e)

    def start_keepalive(self, interval_sec=None):
        if interval_sec is None:
            interval_sec = _RAI
        if self.ka_on:
            return
        self.stop_ev.clear()
        self.ka_on = True
        self.f2_int = interval_sec

        def loop():
            while self.ka_on and not self.stop_ev.is_set():
                for _ in range(interval_sec):
                    if not self.ka_on or self.stop_ev.is_set():
                        return
                    time.sleep(1)
                self.last_f2 = time.time()
                threading.Thread(target=self._ka_tick, daemon=True).start()

        threading.Thread(target=loop, daemon=True).start()
        self.log("[K] keepalive started (%ds)" % interval_sec)

        def hk_loop():
            import ctypes
            u32 = ctypes.windll.user32
            VK_F2 = 0x71
            prev = False
            while self.ka_on and not self.stop_ev.is_set():
                try:
                    st = (u32.GetAsyncKeyState(VK_F2) & 0x8000) != 0
                    if st and not prev:
                        self.manual_refresh()
                    prev = st
                except Exception:
                    pass
                time.sleep(0.05)

        threading.Thread(target=hk_loop, daemon=True).start()
        self.log("[U] hotkey active")

    def stop(self):
        self.stop_ev.set()
        self.ka_on = False


def _rb64(n: int) -> str:
    return base64.b64encode(os.urandom(n)).decode("ascii")


def _tok6() -> str:
    hid = os.urandom(8).hex().upper()
    p = [hid[i:i + 4] for i in range(0, 16, 4)]
    pfx = "0000_0000_0000_0000_{}_{}_{}_{}.SAMSUNG MZVL21T0".format(*p)
    first = pfx.encode("ascii").ljust(97, b"\x00")
    z = b"\x00" * 97
    segs = [base64.b64encode(x).decode("ascii") for x in [first, z, z, z, z]]
    return ";".join(segs)


def gen_entry() -> tuple:
    mid = (
        "||1;" + _rb64(16) +
        "||2;" + _rb64(64) +
        "||3;" + _rb64(64) +
        "||4" +
        "||5;" + _rb64(6) +
        "||6;" + _tok6()
    )
    toks = {}
    for part in mid.split("||"):
        if part:
            toks[part[0]] = part
    concat = (toks["6"] + toks["1"] + toks["2"] + toks["3"] + toks["5"] + _VSTR)
    dg = hashlib.sha1(concat.encode("ascii") + _TAG).digest()
    ht = base64.b64encode(dg).decode("ascii")
    return mid, ht


def gen_pool(count: int) -> list:
    return [gen_entry() for _ in range(count)]


def send_req(env: bytes, puuid: str, region: str, vtype: int = 3,
             timeout: float = 15.0) -> tuple:
    host = get_host(region)
    url = "https://{}:{}{}".format(host, _PORT, _PATH)
    headers = {
        "User-Agent": _AGENT,
        "Content-Type": "application/x-protobuf",
        "X-VG-1": str(vtype),
        "X-VG-3": "1",
        "Accept": "*/*",
    }
    if puuid:
        headers["X-VG-2"] = puuid
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    import http.client
    conn = http.client.HTTPSConnection(host, _PORT, timeout=timeout, context=ctx)
    try:
        conn.request("POST", _PATH, body=env, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        return resp.status, body
    finally:
        conn.close()


REGIONS = ["na", "eu", "ap", "kr", "br", "la"]


def _read_region():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "region.txt"),
                  encoding="utf-8") as f:
            v = f.read().strip().lower()
        if v in REGIONS:
            return v
    except Exception:
        pass
    return "ap"


def _write_region(r):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "region.txt"),
                  "w", encoding="utf-8") as f:
            f.write(r + "\n")
    except Exception:
        pass


def _cli():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--region", choices=REGIONS, default=_read_region())
    ap.add_argument("-i", "--interval", type=int, default=360)
    args = ap.parse_args()

    _write_region(args.region)
    base = os.path.dirname(os.path.abspath(__file__))
    pool_file = os.path.join(base, "build", "output.txt")

    cli = Client(log_cb=lambda m: print(m))
    cli.region = args.region
    cli.auto = True
    cli.set_pool_file(pool_file)
    cli.ensure_pool(3000)
    cli.start_keepalive(args.interval)

    pipe = PipeSvc(cli)
    cli.pipe_svc = pipe
    pipe.start()
    make_mutex()

    if svc_running():
        print("[*] vgc RUNNING")
    else:
        print("[*] vgc NOT running -- starting...")
        start_svc()
        time.sleep(2)
        if svc_running():
            print("[*] vgc started OK")
        else:
            print("[*] vgc could not start -- open game to trigger")

    def _watch():
        was = False
        while True:
            try:
                go = game_running()
                ok = svc_running()
                if go and not was:
                    print("[*] game detected")
                    if not ok:
                        start_svc()
                        time.sleep(3)
                        if svc_running():
                            print("[*] vgc started after game launch")
                        else:
                            print("[*] vgc still not running")
                    else:
                        print("[*] vgc already running with game")
                was = go
                time.sleep(5)
            except Exception:
                time.sleep(5)

    threading.Thread(target=_watch, daemon=True).start()

    print("[*] region=%s interval=%ds" % (args.region, args.interval))
    print("[*] press F2 to refresh, Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] stopping...")
        pipe.stop()
        cli.stop()
        print("[*] stopped")


if __name__ == "__main__":
    _cli()
