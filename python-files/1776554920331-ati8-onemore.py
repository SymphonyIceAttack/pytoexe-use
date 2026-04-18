import os, sys, json, time, socket, subprocess, threading, shutil, uuid, tempfile, base64, gzip as _gzip_mod
import webview
import keyboard as _kb
 
# â”€â”€â”€ Paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Keep config/logs in LocalAppData, but keep traffic capture in Temp to avoid
# MS-Store Python file virtualization mismatches with external mitmdump.exe.
APPDATA_DIR  = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'OneMore')
TRAFFIC_DIR  = os.path.join(tempfile.gettempdir(), 'OneMore')
CONFIG_FILE  = os.path.join(APPDATA_DIR, 'config.json')
TRAFFIC_FILE = os.path.join(TRAFFIC_DIR, 'traffic.jsonl')
LEGACY_TRAFFIC_FILE = os.path.join(APPDATA_DIR, 'traffic.jsonl')
PROXY_SCRIPT = os.path.join(APPDATA_DIR, 'proxy_addon.py')
LOG_FILE     = os.path.join(APPDATA_DIR, 'onemore.log')
NO_WINDOW    = 0x08000000
 
os.makedirs(APPDATA_DIR, exist_ok=True)
os.makedirs(TRAFFIC_DIR, exist_ok=True)
 
 
def _traffic_files_ordered():
  """Return existing traffic files in oldest->newest mtime order."""
  candidates = [TRAFFIC_FILE, LEGACY_TRAFFIC_FILE]
  for p in [os.path.realpath(TRAFFIC_FILE), os.path.realpath(LEGACY_TRAFFIC_FILE)]:
    if p not in candidates:
      candidates.append(p)
 
  existing = []
  for p in candidates:
    try:
      if p and os.path.exists(p) and p not in existing:
        existing.append(p)
    except Exception:
      pass
 
  try:
    existing.sort(key=lambda p: os.path.getmtime(p))
  except Exception:
    pass
  return existing
 
 
def _iter_traffic_lines():
  """Yield lines from all known traffic files in oldest->newest order."""
  for fp in _traffic_files_ordered():
    try:
      with open(fp, 'r', encoding='utf-8') as f:
        for line in f:
          yield line
    except Exception:
      continue
 
# â”€â”€â”€ Item name lookup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import re as _re
 
_ITEM_NAMES = {}
 
# 1) Load static fallback from ID.txt
try:
    _bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    _id_candidates = [
        os.path.join(_bundle_dir, 'ID.txt'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ID.txt'),
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ID.txt'),
        os.path.join(os.getcwd(), 'OneMore', 'ID.txt'),
        os.path.join(os.getcwd(), 'ID.txt'),
    ]
    for _c in _id_candidates:
        if os.path.isfile(_c):
            _kv_re = _re.compile(r'^\s*"(-?\d+)"\s*:\s*"(.+?)"\s*,?\s*$')
            with open(_c, encoding='utf-8') as _f:
                for _line in _f:
                    _m = _kv_re.match(_line)
                    if _m:
                        _ITEM_NAMES[int(_m.group(1))] = _m.group(2)
            break
except Exception:
    pass
 
def _load_names_from_traffic():
    """Extract item names from game-data captured in traffic (offer descriptions)."""
    if not _traffic_files_ordered():
        return
    game_data = None
    loc_data = None
    try:
        for line in _iter_traffic_lines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get('status') != 200:
                    continue
                url = entry.get('url', '')
                res = entry.get('res_body')
                if not res:
                    continue
                if isinstance(res, str):
                    try:
                        res = json.loads(res)
                    except Exception:
                        continue
                if not isinstance(res, dict):
                    continue
                if url.rstrip('/').endswith('/game-data') and '/pioneer/game-data' in url:
                    game_data = res
                elif '/pioneer/game-data' in url and not game_data:
                    game_data = res
                elif 'localizations' in url and not loc_data:
                    loc_data = res
            except Exception:
                continue
    except Exception:
        return
 
    if not game_data:
        # Fallback: search for offer data in any response
        try:
            for line in _iter_traffic_lines():
                try:
                    entry = json.loads(line.strip())
                    res = entry.get('res_body')
                    if isinstance(res, str):
                        res = json.loads(res)
                    if isinstance(res, dict) and ('offer-descriptions' in res or 'offerDescriptions' in res):
                        game_data = res
                        break
                except Exception:
                    continue
        except Exception:
            pass
 
    if not game_data:
        return
 
    # Build localization lookup
    loc_map = {}
    if loc_data:
        entries = loc_data.get('entries', []) if isinstance(loc_data, dict) else []
        for e in entries:
            k = e.get('key', '')
            v = e.get('value', '')
            if k and v:
                loc_map[k] = v
 
    def resolve_loc(s):
        if isinstance(s, str) and s.startswith('l0c4l1z3d_'):
            return loc_map.get(s, s)
        return s
 
    # Extract offers
    offers = []
    od = game_data.get('offer-descriptions')
    if isinstance(od, dict):
        offers = od.get('offerDescriptions', [])
    if not offers:
        offers = game_data.get('offerDescriptions', [])
 
    # Pass 1: "Salvage X" offers â†’ cost item has that name
    for offer in offers:
        title = resolve_loc(offer.get('title', ''))
        if not title or not title.startswith('Salvage '):
            continue
        name = title[8:]
        for ci in ((offer.get('costPackage') or {}).get('costItems', []) or []):
            if isinstance(ci, dict) and ci.get('gameAssetId'):
                _ITEM_NAMES[int(ci['gameAssetId'])] = name
 
    # Pass 2: Non-salvage offer rewards (crafting products)
    for offer in offers:
        title = resolve_loc(offer.get('title', ''))
        if not title or title.startswith('Salvage ') or title.startswith('Contribute '):
            continue
        if 'Generator Level' in title:
            continue
        if title.lower().startswith('s[removed]') or ('_' in title and any(c.isdigit() for c in title.split('_')[-1])):
            continue
        for ri in ((offer.get('rewardPackage') or {}).get('rewardedItems', []) or []):
            if isinstance(ri, dict) and ri.get('gameAssetId'):
                gid = int(ri['gameAssetId'])
                if gid not in _ITEM_NAMES:
                    _ITEM_NAMES[gid] = title
 
    # Pass 3: ownerGameAssetId
    for offer in offers:
        owner_gid = offer.get('ownerGameAssetId')
        title = resolve_loc(offer.get('title', ''))
        if owner_gid and title:
            gid = int(owner_gid)
            if gid not in _ITEM_NAMES:
                clean = title
                for pfx in ('Salvage ', 'Craft ', 'Unlock '):
                    if clean.startswith(pfx):
                        clean = clean[len(pfx):]
                        break
                _ITEM_NAMES[gid] = clean
 
    # Pass 4: itemDescriptions â€” skins, mods, etc.
    items_desc = []
    id_ = game_data.get('items-description')
    if isinstance(id_, dict):
        items_desc = id_.get('itemDescriptions', [])
    if not items_desc:
        items_desc = game_data.get('itemDescriptions', [])
 
    for item in items_desc:
        gid = int(item.get('gameAssetId', 0))
        if gid in _ITEM_NAMES:
            continue
        item_type = item.get('itemType', '')
        tags = item.get('tags') or []
        if item_type == 'CharacterItem':
            skin = slot = ''
            for t in tags:
                parts = t.split('.')
                if len(parts) >= 3:
                    if parts[1] == 'Skin':
                        skin = parts[2]
                    elif parts[1] == 'Slot':
                        slot = parts[2]
            if skin:
                name = _re.sub(r'([a-z])([A-Z])', r'\1 \2', skin)
                name = _re.sub(r'(\D)(\d)', r'\1 \2', name)
                name = name.replace('_', ' ')
                if slot:
                    slot_h = _re.sub(r'([a-z])([A-Z])', r'\1 \2', slot)
                    name = f"{name} ({slot_h})"
                _ITEM_NAMES[gid] = name
            elif slot:
                _ITEM_NAMES[gid] = _re.sub(r'([a-z])([A-Z])', r'\1 \2', slot)
        elif item_type == 'InventoryStructure':
            sc = item.get('slotConfig') or {}
            disc = sc.get('discriminator', '')
            if disc == 'singleSlot':
                aids = sc.get('allowedSlotAssetIds') or []
                for aid in aids:
                    n = _ITEM_NAMES.get(aid)
                    if n:
                        _ITEM_NAMES[gid] = n
                        break
            elif disc == 'arraySlot':
                sa = sc.get('slotAssetId')
                n = _ITEM_NAMES.get(sa)
                if n:
                    _ITEM_NAMES[gid] = n
 
# Load traffic-based names on top of ID.txt names
_load_names_from_traffic()
 
def _item_name(game_asset_id):
    try:
        gid = int(game_asset_id)
    except (TypeError, ValueError):
        gid = game_asset_id
    return _ITEM_NAMES.get(gid, f'Unknown({game_asset_id})')
 
# â”€â”€â”€ Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
import datetime as _dt
 
def _log(msg):
    ts = _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}\n'
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass
 
_log(f'ID.txt loaded: {len(_ITEM_NAMES)} items')
 
# Migrate config from MS-Store virtualized path if needed
_OLD_VIRTUAL_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'OneMore')
if _OLD_VIRTUAL_DIR != APPDATA_DIR and not os.path.exists(CONFIG_FILE):
    _old_cfg = os.path.join(_OLD_VIRTUAL_DIR, 'config.json')
    if os.path.exists(_old_cfg):
        try:
            shutil.copy2(_old_cfg, CONFIG_FILE)
        except Exception:
            pass
 
# â”€â”€â”€ Augment GID Tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
AUGMENT_TABLE = {
    "NO MK": {
        "backpack":    -900626342,
        "quickuse":    -1657530589,
        "safepocket":  742274453,
    },
    "Looting Mk1": {
        "backpack":    202906145,
        "quickuse":    1454995512,
        "safepocket":  634916076,
    },
    "Looting Mk2": {
        "backpack":    1757735240,
        "quickuse":    838324696,
        "safepocket":  -2105475031,
        "augment":     -36502079,
    },
    "Looting Mk3 - Cautious": {
        "backpack":    -835379180,
        "quickuse":    -25855644,
        "safepocket":  1196619436,
    },
    "Looting Mk3 - Survivor": {
        "backpack":    1450686663,
        "quickuse":    -890187561,
        "safepocket":  -2004748456,
    },
}
 
# â”€â”€â”€ Globals â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_proxy_process = None
_proxy_running = False
CURRENT_PROXY_PORT = 58742
_proxy_script_path = PROXY_SCRIPT
 
# â”€â”€â”€ MITM Proxy Addon Script (written to disk) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PROXY_ADDON_CODE = r'''
import json, time, os
 
_DUMP_PATH = __DUMP_PATH_PLACEHOLDER__
 
def _log_flow(flow):
    try:
    req = getattr(flow, 'request', None)
    resp = getattr(flow, 'response', None)
    if not req:
      return
 
    url = getattr(req, 'pretty_url', '') or ''
    host = getattr(req, 'host', '') or ''
    # Capture game traffic domains where Authorization and inventory calls appear.
    if ('es-pio.net' not in host) and ('embark.net' not in host):
      return
 
    dur_ms = 0
    try:
      ts_start = getattr(req, 'timestamp_start', None)
      ts_end = getattr(resp, 'timestamp_end', None) if resp else None
      if ts_start is not None and ts_end is not None:
        dur_ms = int((ts_end - ts_start) * 1000)
    except Exception:
      dur_ms = 0
 
    resp_bytes = b''
    if resp:
      try:
        resp_bytes = resp.get_content() or b''
      except Exception:
        resp_bytes = b''
    resp_size = len(resp_bytes)
 
    req_body = None
    res_body = None
    ct_req = ''
    try:
      ct_req = req.headers.get('Content-Type', '')
    except Exception:
      ct_req = ''
    if 'json' in ct_req:
      try:
        req_body = json.loads(req.get_text())
      except Exception:
        pass
 
    if resp:
      ct_res = ''
      try:
        ct_res = resp.headers.get('Content-Type', '')
      except Exception:
        ct_res = ''
      if 'json' in ct_res and resp_size < 5_000_000:
        try:
          res_body = json.loads(resp.get_text())
        except Exception:
          pass
 
    req_hdrs = {}
    try:
      req_hdrs = dict(req.headers)
    except Exception:
      req_hdrs = {}
 
    resp_hdrs = {}
    try:
      resp_hdrs = dict(resp.headers) if resp else {}
    except Exception:
      resp_hdrs = {}
 
    reason = ''
    if resp:
      reason = getattr(resp, 'reason', '') or getattr(resp, 'reason_phrase', '') or ''
 
    entry = {
      "ts": time.time(),
      "method": req.method,
      "url": url[:500],
      "host": host,
      "path": req.path,
      "status": resp.status_code if resp else 0,
      "reason": reason,
      "dur": dur_ms,
      "size": resp_size,
      "req_hdrs": req_hdrs,
      "resp_hdrs": resp_hdrs,
      "req_body": req_body,
      "res_body": res_body,
    }
 
    try:
      os.makedirs(os.path.dirname(_DUMP_PATH), exist_ok=True)
    except Exception:
      pass
    with open(_DUMP_PATH, "a", encoding="utf-8") as f:
      f.write(json.dumps(entry, default=str))
      f.write("\n")
  except Exception:
        pass
 
def response(flow):
    _log_flow(flow)
'''
 
# â”€â”€â”€ Config helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}
 
def _save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
 
# â”€â”€â”€ Proxy helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _refresh_proxy_settings():
    try:
        import ctypes
        wininet = ctypes.windll.wininet
        wininet.InternetSetOptionW(0, 39, 0, 0)
        wininet.InternetSetOptionW(0, 37, 0, 0)
    except Exception:
        pass
 
def _enable_proxy(port):
    reg = r'HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
    subprocess.run(f'reg add "{reg}" /v ProxyEnable /t REG_DWORD /d 1 /f',
                   shell=True, creationflags=NO_WINDOW, capture_output=True)
    subprocess.run(f'reg add "{reg}" /v ProxyServer /t REG_SZ /d "127.0.0.1:{port}" /f',
                   shell=True, creationflags=NO_WINDOW, capture_output=True)
    _refresh_proxy_settings()
 
def _disable_proxy():
    reg = r'HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
    subprocess.run(f'reg add "{reg}" /v ProxyEnable /t REG_DWORD /d 0 /f',
                   shell=True, creationflags=NO_WINDOW, capture_output=True)
    _refresh_proxy_settings()
 
def _find_free_port(start=58742):
    port = start
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    return 8080
 
def _find_mitmdump():
    md = shutil.which('mitmdump')
    if md:
        return md
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment') as k:
            sys_path = winreg.QueryValueEx(k, 'Path')[0]
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment') as k:
            usr_path = winreg.QueryValueEx(k, 'Path')[0]
        os.environ['PATH'] = sys_path + ';' + usr_path
        md = shutil.which('mitmdump')
        if md:
            return md
    except Exception:
        pass
    for d in [
        os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'mitmproxy', 'bin'),
        os.path.join(os.environ.get('LocalAppData', ''), 'Programs', 'mitmproxy', 'bin'),
        os.path.join(os.path.dirname(sys.executable), 'Scripts'),
    ]:
        p = os.path.join(d, 'mitmdump.exe')
        if os.path.isfile(p):
            os.environ['PATH'] = os.environ.get('PATH', '') + ';' + d
            return p
    return None
 
def _kill_stale_mitmdump():
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == 'mitmdump.exe':
                try:
                    proc.kill()
                except Exception:
                    pass
    except Exception:
        pass
 
def _write_proxy_script(path):
    # Build script from explicit lines so indentation is always valid.
    code_lines = [
    'import json, time, os',
    '',
    f'_DUMP_PATH = {repr(TRAFFIC_FILE)}',
    '',
    'def _log_flow(flow):',
    '    try:',
    '        req = getattr(flow, "request", None)',
    '        resp = getattr(flow, "response", None)',
    '        if not req:',
    '            return',
    '',
    '        url = getattr(req, "pretty_url", "") or ""',
    '        host = getattr(req, "host", "") or ""',
    '        if ("es-pio.net" not in host) and ("embark.net" not in host):',
    '            return',
    '',
    '        dur_ms = 0',
    '        try:',
    '            ts_start = getattr(req, "timestamp_start", None)',
    '            ts_end = getattr(resp, "timestamp_end", None) if resp else None',
    '            if ts_start is not None and ts_end is not None:',
    '                dur_ms = int((ts_end - ts_start) * 1000)',
    '        except Exception:',
    '            dur_ms = 0',
    '',
    '        resp_bytes = b""',
    '        if resp:',
    '            try:',
    '                resp_bytes = resp.get_content() or b""',
    '            except Exception:',
    '                resp_bytes = b""',
    '        resp_size = len(resp_bytes)',
    '',
    '        req_body = None',
    '        res_body = None',
    '        ct_req = ""',
    '        try:',
    '            ct_req = req.headers.get("Content-Type", "")',
    '        except Exception:',
    '            ct_req = ""',
    '        if "json" in ct_req:',
    '            try:',
    '                req_body = json.loads(req.get_text())',
    '            except Exception:',
    '                pass',
    '',
    '        if resp:',
    '            ct_res = ""',
    '            try:',
    '                ct_res = resp.headers.get("Content-Type", "")',
    '            except Exception:',
    '                ct_res = ""',
    '            if "json" in ct_res and resp_size < 5000000:',
    '                try:',
    '                    res_body = json.loads(resp.get_text())',
    '                except Exception:',
    '                    pass',
    '',
    '        req_hdrs = {}',
    '        try:',
    '            req_hdrs = dict(req.headers)',
    '        except Exception:',
    '            req_hdrs = {}',
    '',
    '        resp_hdrs = {}',
    '        try:',
    '            resp_hdrs = dict(resp.headers) if resp else {}',
    '        except Exception:',
    '            resp_hdrs = {}',
    '',
    '        reason = ""',
    '        if resp:',
    '            reason = getattr(resp, "reason", "") or getattr(resp, "reason_phrase", "") or ""',
    '',
    '        entry = {',
    '            "ts": time.time(),',
    '            "method": req.method,',
    '            "url": url[:500],',
    '            "host": host,',
    '            "path": req.path,',
    '            "status": resp.status_code if resp else 0,',
    '            "reason": reason,',
    '            "dur": dur_ms,',
    '            "size": resp_size,',
    '            "req_hdrs": req_hdrs,',
    '            "resp_hdrs": resp_hdrs,',
    '            "req_body": req_body,',
    '            "res_body": res_body,',
    '        }',
    '',
    '        try:',
    '            os.makedirs(os.path.dirname(_DUMP_PATH), exist_ok=True)',
    '        except Exception:',
    '            pass',
    '        with open(_DUMP_PATH, "a", encoding="utf-8") as f:',
    '            f.write(json.dumps(entry, default=str))',
    '            f.write("\\n")',
    '    except Exception:',
    '        pass',
    '',
    'def response(flow):',
    '    _log_flow(flow)',
    '',
    ]
    code = '\n'.join(code_lines)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
 
# â”€â”€â”€ Auth token reader â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _get_auth_token():
    """Read latest auth token from captured traffic."""
    latest = _get_latest_headers()
    if not latest:
        return None
    return latest.get('Authorization') or latest.get('authorization', '')
 
 
_LATEST_HEADERS_CACHE_KEY = None
_LATEST_HEADERS_CACHE_VAL = None
 
 
def _traffic_files_signature():
    sig = []
    for p in _traffic_files_ordered():
        try:
            st = os.stat(p)
            sig.append((p, st.st_mtime_ns, st.st_size))
        except Exception:
            continue
    return tuple(sig)
 
 
def _iter_recent_lines(path, max_bytes=600000):
  """Yield recent lines from a file in reverse order (newest first)."""
  try:
    size = os.path.getsize(path)
    if size <= 0:
      return
    with open(path, 'rb') as f:
      if size > max_bytes:
        f.seek(size - max_bytes)
        data = f.read()
        # Drop the first partial line when reading from mid-file.
        try:
          text = data.decode('utf-8', errors='replace')
        except Exception:
          text = ''
        lines = text.splitlines()
        if lines:
          lines = lines[1:]
      else:
        data = f.read()
        try:
          text = data.decode('utf-8', errors='replace')
        except Exception:
          text = ''
        lines = text.splitlines()
  except Exception:
    return
 
  for ln in reversed(lines):
    yield ln
 
def _get_latest_headers():
    """Get the full set of latest headers from es-pio traffic."""
    global _LATEST_HEADERS_CACHE_KEY, _LATEST_HEADERS_CACHE_VAL
 
    sig = _traffic_files_signature()
    if not sig:
        _LATEST_HEADERS_CACHE_KEY = None
        _LATEST_HEADERS_CACHE_VAL = None
        return None
 
    if _LATEST_HEADERS_CACHE_KEY == sig:
        return _LATEST_HEADERS_CACHE_VAL
 
    latest = None
 
    # Fast path: scan recent tail of newest files first.
    for p in reversed(_traffic_files_ordered()):
      for line in _iter_recent_lines(p):
        line = line.strip()
        if not line:
          continue
        try:
          entry = json.loads(line)
        except Exception:
          continue
        if 'es-pio.net' not in entry.get('host', ''):
          continue
        hdrs = entry.get('req_hdrs', {})
        auth = hdrs.get('Authorization') or hdrs.get('authorization', '')
        if auth:
          latest = hdrs
          break
      if latest:
        break
 
    # Fallback for edge cases where recent tails miss the auth line.
    if not latest:
      for line in _iter_traffic_lines():
        line = line.strip()
        if not line:
          continue
        try:
          entry = json.loads(line)
        except Exception:
          continue
        if 'es-pio.net' not in entry.get('host', ''):
          continue
        hdrs = entry.get('req_hdrs', {})
        auth = hdrs.get('Authorization') or hdrs.get('authorization', '')
        if auth:
          latest = hdrs
 
    _LATEST_HEADERS_CACHE_KEY = sig
    _LATEST_HEADERS_CACHE_VAL = latest
    return latest
 
 
def _extract_jwt_exp(auth_header):
    """Return JWT exp claim (unix ts) from Authorization header, if present."""
    if not auth_header:
        return None
    token = auth_header.strip()
    if token.lower().startswith('bearer '):
        token = token[7:].strip()
    parts = token.split('.')
    if len(parts) < 2:
        return None
    payload = parts[1]
    payload += '=' * (-len(payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode('ascii')).decode('utf-8', errors='replace'))
    except Exception:
        return None
    exp = data.get('exp') if isinstance(data, dict) else None
    if isinstance(exp, (int, float)):
        return int(exp)
    if isinstance(exp, str) and exp.isdigit():
        return int(exp)
    return None
 
# â”€â”€â”€ API Call â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _api_request(method, path, body=None, headers=None):
    """Make HTTPS request to the game API."""
    import http.client as _hc, ssl as _ssl
    host = 'api-gateway.europe.es-pio.net'
    ctx = _ssl.create_default_context()
    conn = _hc.HTTPSConnection(host, timeout=15, context=ctx)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        data = resp.read()
        if resp.getheader('Content-Encoding', '').lower() == 'gzip':
            data = _gzip_mod.decompress(data)
        return resp.status, data
    finally:
        conn.close()
 
 
def _inventory_http_error(status, raw):
    """Build a user-friendly inventory error message from status/body."""
    body = ''
    try:
        if isinstance(raw, (bytes, bytearray)):
            body = raw.decode('utf-8', errors='replace').strip()
        elif isinstance(raw, str):
            body = raw.strip()
    except Exception:
        body = ''
    body = body[:200]
    low = body.lower()
 
    if status == 401:
        if ('jwt' in low and 'expired' in low) or ('token' in low and 'expired' in low):
            return 'Auth token expired. Start Proxy, play for a few seconds, then try again.'
        return 'Auth failed (401). Start Proxy and play the game to capture a fresh token.'
 
    if body:
        return f'Inventory returned HTTP {status}: {body}'
    return f'Inventory returned HTTP {status}'
 
# â”€â”€â”€ The API class exposed to JS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class Api:
    def __init__(self):
        self._window = None
 
    def move_window(self, dx, dy):
        if self._window:
            self._window.move(self._window.x + int(dx), self._window.y + int(dy))
 
    def _js(self, code):
        if self._window:
            self._window.evaluate_js(code)
 
    # â”€â”€ Setup checks â”€â”€
    def check_mitmproxy_installed(self):
        return _find_mitmdump() is not None
 
    def get_installer_path(self):
        """Return the bundled installer path if it exists."""
        # Check next to the exe / script
        base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        for name in os.listdir(base):
            if 'mitmproxy' in name.lower() and name.lower().endswith('.exe'):
                return os.path.join(base, name)
        # Check in same folder as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for name in os.listdir(script_dir):
            if 'mitmproxy' in name.lower() and name.lower().endswith('.exe'):
                return os.path.join(script_dir, name)
        return None
 
    def launch_installer(self):
        p = self.get_installer_path()
        if p and os.path.isfile(p):
            os.startfile(p)
            return True
        return False
 
    # â”€â”€ Proxy control â”€â”€
    def start_proxy(self):
        global _proxy_process, _proxy_running, CURRENT_PROXY_PORT, _proxy_script_path
        md = _find_mitmdump()
        if not md:
            return {'ok': False, 'error': 'mitmdump not found'}
        _kill_stale_mitmdump()
        CURRENT_PROXY_PORT = _find_free_port()
 
        script_candidates = [
          os.path.join(tempfile.gettempdir(), f'OneMore_proxy_addon_{os.getpid()}.py'),
          os.path.join(tempfile.gettempdir(), 'OneMore_proxy_addon.py'),
          PROXY_SCRIPT,
        ]
        script_err = ''
        _proxy_script_path = ''
        for cand in script_candidates:
            try:
                _write_proxy_script(cand)
                if os.path.isfile(cand) and os.path.getsize(cand) > 0:
                    _proxy_script_path = cand
                    break
            except Exception as e:
                script_err = str(e)
 
        if not _proxy_script_path:
            return {'ok': False, 'error': f'Failed to create proxy script: {script_err or "unknown error"}'}
 
        try:
            _proxy_process = subprocess.Popen(
                [md, '-s', _proxy_script_path, '-p', str(CURRENT_PROXY_PORT),
                 '--set', 'ssl_insecure=true', '--quiet'],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                creationflags=NO_WINDOW,
            )
            time.sleep(1.0)
            if _proxy_process.poll() is not None:
                err_detail = _proxy_process.stderr.read().decode(errors='replace').strip()
                _proxy_process = None
                _proxy_running = False
                return {'ok': False, 'error': f'Proxy exited immediately: {err_detail[:300]} (script={_proxy_script_path})'}
            _enable_proxy(CURRENT_PROXY_PORT)
            _proxy_running = True
            return {'ok': True, 'port': CURRENT_PROXY_PORT}
        except Exception as e:
            _proxy_process = None
            _proxy_running = False
            return {'ok': False, 'error': str(e)}
 
    def stop_proxy(self):
        global _proxy_process, _proxy_running, _proxy_script_path
        _proxy_running = False
        _disable_proxy()
        if _proxy_process:
            try:
                _proxy_process.terminate()
                _proxy_process.wait(timeout=3)
            except Exception:
                try:
                    _proxy_process.kill()
                except Exception:
                    pass
            _proxy_process = None
        if _proxy_script_path and os.path.exists(_proxy_script_path):
            try:
                os.remove(_proxy_script_path)
            except Exception:
                pass
        _proxy_script_path = PROXY_SCRIPT
        return {'ok': True}
 
    def toggle_proxy(self):
        if _proxy_running:
            return self.stop_proxy()
        else:
            return self.start_proxy()
 
    def is_proxy_running(self):
        return _proxy_running
 
    # â”€â”€ Cert â”€â”€
    def open_cert(self):
        cert = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.p12')
        if os.path.exists(cert):
            os.startfile(cert)
            return True
        return False
 
    def is_cert_exists(self):
        cert = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.p12')
        return os.path.exists(cert)
 
    def mark_cert_done(self):
        cfg = _load_config()
        cfg['cert_done'] = True
        _save_config(cfg)
        return True
 
    # â”€â”€ Config â”€â”€
    def get_config(self):
        return _load_config()
 
    def save_augment(self, augment_name):
        if augment_name not in AUGMENT_TABLE:
            return {'ok': False, 'error': 'Invalid augment'}
        cfg = _load_config()
        cfg['augment'] = augment_name
        _save_config(cfg)
        return {'ok': True}
 
    def get_augment_list(self):
        return list(AUGMENT_TABLE.keys())
 
    def save_hotkey(self, key):
        cfg = _load_config()
        cfg['hotkey'] = key
        _save_config(cfg)
        self._register_all_hotkeys()
        return {'ok': True}
 
    def get_hotkey(self):
        cfg = _load_config()
        return cfg.get('hotkey', '')
 
    def save_refresh_hotkey(self, key):
        cfg = _load_config()
        cfg['refresh_hotkey'] = key
        _save_config(cfg)
        self._register_all_hotkeys()
        return {'ok': True}
 
    def get_refresh_hotkey(self):
        cfg = _load_config()
        return cfg.get('refresh_hotkey', '')
 
    def save_super_refresh_hotkey(self, key):
        cfg = _load_config()
        cfg['super_refresh_hotkey'] = key
        _save_config(cfg)
        self._register_all_hotkeys()
        return {'ok': True}
 
    def get_super_refresh_hotkey(self):
        cfg = _load_config()
        return cfg.get('super_refresh_hotkey', '')
 
    def save_test_hotkey(self, key):
        cfg = _load_config()
        cfg['test_hotkey'] = key
        _save_config(cfg)
        self._register_all_hotkeys()
        return {'ok': True}
 
    def get_test_hotkey(self):
        cfg = _load_config()
        return cfg.get('test_hotkey', '')
 
    def _register_all_hotkeys(self):
        """Register all system-wide hotkeys (SECRET + REFRESH + SUPER REFRESH)."""
        try:
            _kb.unhook_all_hotkeys()
        except Exception:
            pass
        cfg = _load_config()
        secret_key = cfg.get('hotkey', '')
        refresh_key = cfg.get('refresh_hotkey', '')
        super_refresh_key = cfg.get('super_refresh_hotkey', '')
        if secret_key:
            try:
                _kb.add_hotkey(secret_key.lower(), self._on_global_hotkey, suppress=False)
            except Exception:
                pass
        if refresh_key:
            try:
                _kb.add_hotkey(refresh_key.lower(), self._on_refresh_hotkey, suppress=False)
            except Exception:
                pass
        if super_refresh_key:
            try:
                _kb.add_hotkey(super_refresh_key.lower(), self._on_super_refresh_hotkey, suppress=False)
            except Exception:
                pass
        test_key = cfg.get('test_hotkey', '')
        if test_key:
            try:
                _kb.add_hotkey(test_key.lower(), self._on_test_hotkey, suppress=False)
            except Exception:
                pass
 
    def _on_global_hotkey(self):
        """Called from keyboard lib thread when SECRET global hotkey is pressed."""
        if not self._window:
            return
        threading.Thread(target=self._run_secret_from_hotkey, daemon=True).start()
 
    def _run_secret_from_hotkey(self):
        try:
            self._window.evaluate_js(
                "(function(){"
                "var b=document.getElementById('btnSecret');"
                "if(b&&!b.disabled){onSecret();}"
                "})()"
            )
        except Exception:
            pass
 
    def _on_refresh_hotkey(self):
        """Called from keyboard lib thread when REFRESH global hotkey is pressed."""
        if not self._window:
            return
        threading.Thread(target=self._run_refresh_from_hotkey, daemon=True).start()
 
    def _run_refresh_from_hotkey(self):
        try:
            self._window.evaluate_js(
                "(function(){"
                "var b=document.getElementById('btnRefresh');"
                "if(b&&!b.disabled){onRefresh();}"
                "})()"
            )
        except Exception:
            pass
 
    def _on_super_refresh_hotkey(self):
        """Called from keyboard lib thread when SUPER REFRESH global hotkey is pressed."""
        if not self._window:
            return
        threading.Thread(target=self._run_super_refresh_from_hotkey, daemon=True).start()
 
    def _run_super_refresh_from_hotkey(self):
        try:
            self._window.evaluate_js(
                "(function(){"
                "var b=document.getElementById('btnSuperRefresh');"
                "if(b&&!b.disabled){onSuperRefresh();}"
                "})()"
            )
        except Exception:
            pass
 
    def _on_test_hotkey(self):
        """Called from keyboard lib thread when TEST global hotkey is pressed."""
        if not self._window:
            return
        threading.Thread(target=self._run_test_from_hotkey, daemon=True).start()
 
    def _run_test_from_hotkey(self):
        try:
            self._window.evaluate_js(
                "(function(){"
                "var b=document.getElementById('btnTest');"
                "if(b&&!b.disabled){onTest();}"
                "})()"
            )
        except Exception:
            pass
 
    def is_configured(self):
        cfg = _load_config()
        return cfg.get('augment') is not None
 
    def is_setup_done(self):
        cfg = _load_config()
        return cfg.get('cert_done', False)
 
    # â”€â”€ Has captured token? â”€â”€
    def has_token(self):
      latest_hdrs = _get_latest_headers()
      if not latest_hdrs:
        return False
      token = latest_hdrs.get('Authorization') or latest_hdrs.get('authorization', '')
      if not token:
        return False
      exp_ts = _extract_jwt_exp(token)
      if exp_ts is not None and exp_ts <= int(time.time()):
        return False
      return True
 
    def detect_latest_token(self):
      """Validate latest captured Authorization token from traffic."""
      latest_hdrs = _get_latest_headers()
      if not latest_hdrs:
        return {
          'ok': False,
          'found': False,
          'error': 'No auth token captured. Start Proxy, then play the game.'
        }
 
      auth_token = latest_hdrs.get('Authorization') or latest_hdrs.get('authorization', '')
      if not auth_token:
        return {
          'ok': False,
          'found': False,
          'error': 'No Authorization header in captured traffic.'
        }
 
      exp_ts = _extract_jwt_exp(auth_token)
      now_ts = int(time.time())
      if exp_ts is not None and exp_ts <= now_ts:
        return {
          'ok': False,
          'found': True,
          'expired': True,
          'exp': exp_ts,
          'error': 'Latest token is expired. Keep Proxy ON and play to capture a fresh token.'
        }
 
      host = 'api-gateway.europe.es-pio.net'
      api_headers = {
        'Authorization': auth_token,
        'Content-Type': 'application/json',
        'x-embark-request-id': '',
        'x-embark-telemetry-client-platform': '12',
        'Accept': '*/*',
        'Host': host,
      }
      for hk in ['x-embark-manifest-id', 'User-Agent']:
        if hk in latest_hdrs:
          api_headers[hk] = latest_hdrs[hk]
 
      try:
        status, raw = _api_request('GET', '/v1/pioneer/inventory', headers=api_headers)
      except Exception as e:
        return {
          'ok': False,
          'found': True,
          'exp': exp_ts,
          'error': f'Token check failed: {e}'
        }
 
      if status == 200:
        return {
          'ok': True,
          'found': True,
          'expired': False,
          'exp': exp_ts,
          'message': 'Latest token detected and valid.'
        }
 
      err_msg = _inventory_http_error(status, raw)
      return {
        'ok': False,
        'found': True,
        'expired': status == 401,
        'exp': exp_ts,
        'error': err_msg
      }
 
    # â”€â”€ SECRET â€” single batch overstash â”€â”€
    def execute_secret(self):
        """
        One-shot: GET inventory, find all items in the 3 configured containers
        (backpack, quickuse, safepocket), then batch-mutate them all in a SINGLE
        POST request with slots=[''] to overstash everything.
        """
        _log('â•' * 60)
        _log('SECRET â€” Starting overstash')
        cfg = _load_config()
        aug_name = cfg.get('augment')
        if not aug_name or aug_name not in AUGMENT_TABLE:
            _log('ERROR: Not configured')
            return {'ok': False, 'error': 'Not configured. Go to Config first.'}
 
        gids = AUGMENT_TABLE[aug_name]
        target_gids = set(gids.values())
        _log(f'Config: {aug_name} â€” target GIDs: {gids}')
 
        latest_hdrs = _get_latest_headers()
        if not latest_hdrs:
            _log('ERROR: No auth token')
            return {'ok': False, 'error': 'No auth token captured. Start proxy, then play the game.'}
 
        auth_token = latest_hdrs.get('Authorization') or latest_hdrs.get('authorization', '')
        if not auth_token:
            _log('ERROR: No Authorization header')
            return {'ok': False, 'error': 'No Authorization header in captured traffic.'}
 
        host = 'api-gateway.europe.es-pio.net'
        api_headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json',
            'x-embark-request-id': '',
            'x-embark-telemetry-client-platform': '12',
            'Accept': '*/*',
            'Host': host,
        }
        for hk in ['x-embark-manifest-id', 'User-Agent']:
            if hk in latest_hdrs:
                api_headers[hk] = latest_hdrs[hk]
 
        last_error = None
        # Reuse ONE TLS connection for all API calls
        import http.client as _hc, ssl as _ssl
        _ctx = _ssl.create_default_context()
        _conn = _hc.HTTPSConnection(host, timeout=15, context=_ctx)
        def _api(method, path, body=None):
            try:
                _conn.request(method, path, body=body, headers=api_headers)
                resp = _conn.getresponse()
                data = resp.read()
                if resp.getheader('Content-Encoding', '').lower() == 'gzip':
                    data = _gzip_mod.decompress(data)
                return resp.status, data
            except Exception:
                _conn.close()
                _conn.connect()
                _conn.request(method, path, body=body, headers=api_headers)
                resp = _conn.getresponse()
                data = resp.read()
                if resp.getheader('Content-Encoding', '').lower() == 'gzip':
                    data = _gzip_mod.decompress(data)
                return resp.status, data
 
        for attempt in range(2):
            _log(f'Attempt {attempt + 1}/2 â€” Fetching inventoryâ€¦')
            try:
                status, raw = _api('GET', '/v1/pioneer/inventory')
            except Exception as e:
                _log(f'ERROR: Inventory request failed: {e}')
                return {'ok': False, 'error': f'Inventory request failed: {e}'}
 
            if status != 200:
              err_msg = _inventory_http_error(status, raw)
              _log(f'ERROR: Inventory HTTP {status} - {err_msg}')
              return {'ok': False, 'error': err_msg}
 
            try:
                inv = json.loads(raw)
            except Exception:
                _log('ERROR: Failed to parse inventory JSON')
                return {'ok': False, 'error': 'Failed to parse inventory JSON'}
 
            items = inv.get('items', [])
            _log(f'Inventory loaded: {len(items)} total items')
 
            children_ids = set()
            for it in items:
                if it.get('gameAssetId') in target_gids:
                    cname = _item_name(it['gameAssetId'])
                    slots = [s for s in it.get('slots', []) if s and s.strip()]
                    _log(f'  Container: {cname} (gid {it["gameAssetId"]}) â€” {len(slots)} slots')
                    for slot_id in slots:
                        children_ids.add(slot_id)
 
            movable = [it for it in items if it['instanceId'] in children_ids]
            _log(f'Found {len(movable)} items to overstash')
 
            if not movable:
                _log('ERROR: No items in containers')
                return {'ok': False, 'error': 'No items found inside your containers. Play the game and loot first.'}
 
            for it in movable:
                _log(f'  â†’ {_item_name(it["gameAssetId"])} | iid={it["instanceId"][:12]}â€¦ | amt={it.get("amount",1)} | gid={it["gameAssetId"]}')
 
            mutations = []
            for it in movable:
                mutations.append({
                    'discriminator': 'update',
                    'instanceId': it['instanceId'],
                    'amount': it.get('amount', 1),
                    'slots': [],
                    'etag': it.get('etag', ''),
                })
 
            _log(f'Sending {len(mutations)} mutationsâ€¦')
            payload = json.dumps({'mutations': mutations, 'requestId': ''})
 
            try:
                status2, raw2 = _api_request('POST', '/v1/pioneer/inventory/v1/mutate',
                                             body=payload.encode('utf-8'), headers=api_headers)
            except Exception as e:
                _log(f'ERROR: Mutate request failed: {e}')
                return {'ok': False, 'error': f'Mutate failed: {e}'}
 
            if status2 == 200:
                _log(f'SUCCESS â€” {len(mutations)} items overstashed')
                return {'ok': True, 'moved': len(mutations), 'status': status2}
 
            if status2 == 412 and attempt == 0:
                _log('Got 412 (stale etags) â€” retrying with fresh inventoryâ€¦')
                time.sleep(0.3)
                continue
 
            try:
                err_body = json.loads(raw2)
            except Exception:
                err_body = raw2.decode('utf-8', errors='replace')[:200]
            _log(f'ERROR: Mutate HTTP {status2} â€” {str(err_body)[:300]}')
            last_error = {'ok': False, 'error': f'Mutate HTTP {status2}', 'detail': str(err_body)[:300]}
 
        _log(f'FAILED after retries')
        return last_error or {'ok': False, 'error': 'Mutate failed after retry'}
 
    # â”€â”€ REFRESH â€” stash refresh using deleteâ†’createâ†’update â”€â”€
    def execute_refresh(self):
        """
        Fetch inventory, find equipped backpack,
        walk tree to find leaf items (including weapons without attachments),
        then refresh each leaf by deleteâ†’createâ†’update with a new UUID.
        """
        print('[REFRESH] execute_refresh called', flush=True)
        try:
            return self._execute_refresh_inner()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f'[REFRESH] EXCEPTION: {tb}', flush=True)
            _log(f'REFRESH EXCEPTION: {e}\n{tb}')
            return {'ok': False, 'error': f'Internal error: {e}'}
 
    def _execute_refresh_inner(self):
        print('[REFRESH] _execute_refresh_inner entered', flush=True)
        _log('â•' * 60)
        _log('REFRESH â€” Starting stash refresh')
        print('[REFRESH] after _log', flush=True)
 
        latest_hdrs = _get_latest_headers()
        print(f'[REFRESH] latest_hdrs={bool(latest_hdrs)}', flush=True)
        if not latest_hdrs:
            _log('ERROR: No auth token')
            return {'ok': False, 'error': 'No auth token captured. Start proxy, then play the game.'}
 
        auth_token = latest_hdrs.get('Authorization') or latest_hdrs.get('authorization', '')
        if not auth_token:
            _log('ERROR: No Authorization header')
            return {'ok': False, 'error': 'No Authorization header in captured traffic.'}
 
        host = 'api-gateway.europe.es-pio.net'
        api_headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json',
            'x-embark-request-id': '',
            'x-embark-telemetry-client-platform': '12',
            'Accept': '*/*',
            'Host': host,
        }
        for hk in ['x-embark-manifest-id', 'User-Agent']:
            if hk in latest_hdrs:
                api_headers[hk] = latest_hdrs[hk]
 
        EQUIPPED_BACKPACK_GID = -900626342
        UUID_RE = __import__('re').compile(
            r'(?:item with id|instanceId|instance_id|item):\s*"?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"?',
            __import__('re').IGNORECASE,
        )
 
        last_error = None
        # Reuse ONE TLS connection for all API calls
        import http.client as _hc, ssl as _ssl
        _ctx = _ssl.create_default_context()
        _conn = _hc.HTTPSConnection(host, timeout=15, context=_ctx)
        def _api(method, path, body=None):
            try:
                _conn.request(method, path, body=body, headers=api_headers)
                resp = _conn.getresponse()
                data = resp.read()
                if resp.getheader('Content-Encoding', '').lower() == 'gzip':
                    data = _gzip_mod.decompress(data)
                return resp.status, data
            except Exception:
                _conn.close()
                _conn.connect()
                _conn.request(method, path, body=body, headers=api_headers)
                resp = _conn.getresponse()
                data = resp.read()
                if resp.getheader('Content-Encoding', '').lower() == 'gzip':
                    data = _gzip_mod.decompress(data)
                return resp.status, data
 
        for attempt in range(2):
            print(f'[REFRESH] Attempt {attempt+1} â€” fetching inventory...', flush=True)
            _log(f'Attempt {attempt + 1}/2 â€” Fetching inventoryâ€¦')
            try:
                status, raw = _api_request('GET', '/v1/pioneer/inventory', headers=api_headers)
            except Exception as e:
                print(f'[REFRESH] inventory exception: {e}', flush=True)
                _log(f'ERROR: Inventory request failed: {e}')
                return {'ok': False, 'error': f'Inventory request failed: {e}'}
 
            print(f'[REFRESH] inventory HTTP {status}, {len(raw)} bytes', flush=True)
            if status != 200:
              err_msg = _inventory_http_error(status, raw)
              _log(f'ERROR: Inventory HTTP {status} - {err_msg}')
              return {'ok': False, 'error': err_msg}
 
            try:
                inv = json.loads(raw)
            except Exception:
                _log('ERROR: Failed to parse inventory JSON')
                return {'ok': False, 'error': 'Failed to parse inventory JSON'}
 
            items = inv.get('items', [])
            by_iid = {i['instanceId']: i for i in items}
            _log(f'Inventory loaded: {len(items)} total items')
            print(f'[REFRESH] Inventory: {len(items)} items', flush=True)
 
            backpack = next((i for i in items if i.get('gameAssetId') == EQUIPPED_BACKPACK_GID), None)
            if not backpack:
                print('[REFRESH] No backpack found!', flush=True)
                _log('ERROR: No Equipped Backpack found')
                return {'ok': False, 'error': 'No Equipped Backpack found in inventory.'}
 
            # Structure: Backpack â†’ Inventory Slot (container) â†’ actual item
            # Walk through Inventory Slot containers to find real items inside them.
            INVENTORY_SLOT_GID = 1440007245
            bp_slots = backpack.get('slots') or []
            filled = [s for s in bp_slots if s]
            _log(f'Equipped Backpack: {len(bp_slots)} slots, {len(filled)} filled')
            print(f'[REFRESH] Backpack: {len(bp_slots)} slots, {len(filled)} filled', flush=True)
 
            all_leaves = []
            for s in filled:
                inv_slot = by_iid.get(s)
                if not inv_slot:
                    continue
                # Each Inventory Slot container has its own slots pointing to real items
                inner_slots = [c for c in (inv_slot.get('slots') or []) if c]
                for c in inner_slots:
                    child = by_iid.get(c)
                    if not child:
                        continue
                    if child.get('gameAssetId') == INVENTORY_SLOT_GID:
                        continue  # skip nested empty placeholders
                    all_leaves.append((child, inv_slot))
                    print(f'[REFRESH]   Found: gid={child.get("gameAssetId")} name={_ITEM_NAMES.get(child.get("gameAssetId",0),"?")} parent_slot={s[:8]}â€¦', flush=True)
 
            _log(f'Found {len(all_leaves)} items in backpack')
            print(f'[REFRESH] Items to refresh: {len(all_leaves)}', flush=True)
            for leaf, parent in all_leaves:
                name = _ITEM_NAMES.get(leaf.get('gameAssetId', 0), f"gid={leaf.get('gameAssetId')}")
                print(f'[REFRESH]   Item: {name} gid={leaf.get("gameAssetId")} slots={leaf.get("slots")}', flush=True)
                _log(f'  Item: {name} iid={leaf["instanceId"][:8]}â€¦ parent={parent["instanceId"][:8]}â€¦ slots={leaf.get("slots")}')
            if not all_leaves:
                _log('ERROR: No items in equipped backpack')
                return {'ok': False, 'error': 'No items found in equipped backpack.'}
 
            pairs = [(leaf, parent, leaf['instanceId'], str(uuid.uuid4())) for leaf, parent in all_leaves]
 
            # Per-item mutations: deleteâ†’createâ†’update (matches proven working pattern)
            def _build_mutations(batch):
                mutations = []
                for leaf, parent, old, new in batch:
                    new_slots = [new if s == old else s for s in (parent.get('slots') or [])]
                    mutations.append({'discriminator': 'delete', 'instanceId': old})
                    mutations.append(
                        {'discriminator': 'create', 'gameAssetId': leaf['gameAssetId'],
                         'instanceId': new, 'amount': leaf.get('amount', 1),
                         'slots': leaf.get('slots') or [], 'etag': leaf.get('etag', '')})
                    mutations.append(
                        {'discriminator': 'update', 'instanceId': parent['instanceId'],
                         'amount': parent.get('amount', 1),
                         'slots': new_slots, 'etag': parent.get('etag', '')})
                return mutations
 
            def _apply_success(batch, res):
                updated = {u['instanceId']: u for u in
                           ((res.get('changeset') or {}).get('items', {}).get('updated') or [])}
                for leaf, parent, old, new in batch:
                    by_iid.pop(old, None)
                    leaf['instanceId'] = new
                    by_iid[new] = leaf
                    parent['slots'] = [new if s == old else s for s in (parent.get('slots') or [])]
                    if parent['instanceId'] in updated:
                        parent['etag'] = updated[parent['instanceId']].get('etag', parent['etag'])
 
            def _send_batch(batch):
                bad = set()
                while True:
                    active = [t for t in batch if t[2] not in bad]
                    if not active:
                        break
                    mutations = _build_mutations(active)
                    payload = json.dumps({'mutations': mutations, 'requestId': ''})
                    print(f'[REFRESH] _send_batch: {len(active)} active items, {len(mutations)} mutations, payload size={len(payload)}', flush=True)
                    print(f'[REFRESH] _send_batch: calling _api_request POST...', flush=True)
                    try:
                        st, raw = _api('POST', '/v1/pioneer/inventory/v1/mutate',
                                        body=payload.encode('utf-8'))
                    except Exception as e:
                        _log(f'ERROR: Mutate exception: {e}')
                        print(f'[REFRESH] _send_batch EXCEPTION: {e}', flush=True)
                        return 0, bad, str(e)
                    print(f'[REFRESH] _send_batch: got HTTP {st}, raw size={len(raw)}', flush=True)
                    _log(f'  Mutate response: HTTP {st}')
                    if 200 <= st < 300:
                        try:
                            res = json.loads(raw)
                        except Exception:
                            res = {}
                        _apply_success(active, res)
                        return len(active), bad, ''
                    err = ''
                    try:
                        err_body = json.loads(raw)
                        err = err_body.get('message') or str(err_body)[:300]
                    except Exception:
                        err = raw.decode('utf-8', errors='replace')[:300]
                    print(f'[REFRESH] _send_batch ERROR: HTTP {st} â€” {err[:200]}', flush=True)
                    _log(f'  Error body: {err[:300]}')
                    m = UUID_RE.search(err)
                    if m:
                        bad.add(m.group(1))
                        print(f'[REFRESH] _send_batch: retrying, skipping {m.group(1)[:8]}â€¦', flush=True)
                        _log(f'  Retrying â€” skipping {m.group(1)[:8]}â€¦')
                    else:
                        _log(f'ERROR: HTTP {st} â€” {err}')
                        return 0, bad, f'HTTP {st}: {err[:200]}'
                return 0, bad, 'All items skipped'
 
            BATCH = len(pairs)  # send ALL items in one call
            total_refreshed = 0
            refreshed_details = []
            last_err = ''
 
            for i in range(0, len(pairs), BATCH):
                batch = pairs[i:i + BATCH]
                print(f'[REFRESH] Batch {i//BATCH+1}: {len(batch)} items', flush=True)
                _log(f'Sending batch {i//BATCH+1}: {len(batch)} items, {len(batch)*3} mutations')
                n, bad, err = _send_batch(batch)
                print(f'[REFRESH] Batch result: n={n}, bad={len(bad)}, err={err}', flush=True)
                _log(f'Batch result: {n} refreshed, {len(bad)} skipped')
                if err:
                    last_err = err
                if n > 0:
                    for leaf, parent, old, new in batch:
                        if old not in bad:
                            leaf_name = _item_name(leaf.get('gameAssetId', 0))
                            parent_name = _item_name(parent.get('gameAssetId', 0))
                            if leaf_name.startswith('Unknown') and not parent_name.startswith('Unknown'):
                                display_name = parent_name
                            else:
                                display_name = leaf_name
                            amt = leaf.get('amount', 1)
                            if amt > 1:
                                display_name = f'{display_name} x{amt}'
                            refreshed_details.append({
                                'name': display_name,
                                'gid': leaf.get('gameAssetId', 0),
                                'amount': amt,
                                'old': old[:12],
                                'new': new[:12],
                            })
                    total_refreshed += n
 
            if total_refreshed > 0:
                _log(f'SUCCESS â€” {total_refreshed} items refreshed')
                print(f'[REFRESH] SUCCESS: {total_refreshed} items refreshed', flush=True)
                return {'ok': True, 'refreshed': total_refreshed, 'skipped': 0, 'details': refreshed_details}
            else:
                if attempt == 0:
                    _log(f'Failed â€” {last_err} â€” retrying with fresh inventoryâ€¦')
                    print(f'[REFRESH] Failed attempt 1: {last_err} â€” retrying', flush=True)
                    continue
                _log(f'FAILED â€” {last_err}')
                print(f'[REFRESH] FAILED: {last_err}', flush=True)
                return {'ok': False, 'error': last_err or 'Refresh failed'}
 
        _log('FAILED after retries')
        print('[REFRESH] FAILED after retries', flush=True)
        return {'ok': False, 'error': 'Refresh failed after retry'}
 
    # â”€â”€ TEST â€” reverse-order refresh (deleteâ†’updateâ†’create) â”€â”€
    def execute_test(self):
        """
        Same as REFRESH but mutation order is reversed:
        delete all old â†’ update parents â†’ create all new.
        """
        _log('â•' * 60)
        _log('TEST â€” Starting reverse-order refresh')
 
        latest_hdrs = _get_latest_headers()
        if not latest_hdrs:
            _log('ERROR: No auth token')
            return {'ok': False, 'error': 'No auth token captured. Start proxy, then play the game.'}
 
        auth_token = latest_hdrs.get('Authorization') or latest_hdrs.get('authorization', '')
        if not auth_token:
            _log('ERROR: No Authorization header')
            return {'ok': False, 'error': 'No Authorization header in captured traffic.'}
 
        host = 'api-gateway.europe.es-pio.net'
        api_headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json',
            'x-embark-request-id': '',
            'x-embark-telemetry-client-platform': '12',
            'Accept': '*/*',
            'Host': host,
        }
        for hk in ['x-embark-manifest-id', 'User-Agent']:
            if hk in latest_hdrs:
                api_headers[hk] = latest_hdrs[hk]
 
        cfg = _load_config()
        aug_name = cfg.get('augment', 'NO MK')
        aug_entry = AUGMENT_TABLE.get(aug_name, AUGMENT_TABLE['NO MK'])
        # Collect all container GIDs to refresh (backpack, quickuse, safepocket, augment if present)
        container_gids = {}
        for ctype in ('backpack', 'quickuse', 'safepocket', 'augment'):
            gid = aug_entry.get(ctype)
            if gid is not None:
                container_gids[ctype] = gid
        _log(f'Using augment: {aug_name} â€" containers: {container_gids}')
        UUID_RE = __import__('re').compile(
            r'(?:item with id|instanceId|instance_id|item):\s*"?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"?',
            __import__('re').IGNORECASE,
        )
 
        last_error = None
        # Reuse ONE TLS connection for all API calls
        import http.client as _hc, ssl as _ssl
        _ctx = _ssl.create_default_context()
        _conn = _hc.HTTPSConnection(host, timeout=15, context=_ctx)
        def _api(method, path, body=None):
            try:
                _conn.request(method, path, body=body, headers=api_headers)
                resp = _conn.getresponse()
                data = resp.read()
                if resp.getheader('Content-Encoding', '').lower() == 'gzip':
                    data = _gzip_mod.decompress(data)
                return resp.status, data
            except Exception:
                _conn.close()
                _conn.connect()
                _conn.request(method, path, body=body, headers=api_headers)
                resp = _conn.getresponse()
                data = resp.read()
                if resp.getheader('Content-Encoding', '').lower() == 'gzip':
                    data = _gzip_mod.decompress(data)
                return resp.status, data
 
        for attempt in range(2):
            _log(f'Attempt {attempt + 1}/2 â€” Fetching inventoryâ€¦')
            try:
                status, raw = _api('GET', '/v1/pioneer/inventory')
            except Exception as e:
                _log(f'ERROR: Inventory request failed: {e}')
                _conn.close()
                return {'ok': False, 'error': f'Inventory request failed: {e}'}
 
            if status != 200:
              err_msg = _inventory_http_error(status, raw)
              _log(f'ERROR: Inventory HTTP {status} - {err_msg}')
              return {'ok': False, 'error': err_msg}
 
            try:
                inv = json.loads(raw)
            except Exception:
                _log('ERROR: Failed to parse inventory JSON')
                return {'ok': False, 'error': 'Failed to parse inventory JSON'}
 
            items = inv.get('items', [])
            by_iid = {i['instanceId']: i for i in items}
            _log(f'Inventory loaded: {len(items)} total items')
 
            def _is_structural(item):
                s = item.get('slots')
                return isinstance(s, list) and not any(s)
 
            def _collect_leaves(root):
                leaves = []
                skipped = 0
                def walk(iid, parent):
                    nonlocal skipped
                    item = by_iid.get(iid)
                    if not item:
                        return
                    if _is_structural(item):
                        skipped += 1
                        return
                    kids = [s for s in (item.get('slots') or []) if s]
                    if not kids:
                        leaves.append((item, parent))
                    else:
                        for c in kids:
                            walk(c, item)
                for s in (root.get('slots') or []):
                    if s:
                        walk(s, root)
                return leaves, skipped
 
            # Find and collect leaves from ALL configured containers
            all_leaves = []
            total_skipped = 0
            found_any_container = False
            for ctype, gid in container_gids.items():
                container = next((i for i in items if i.get('gameAssetId') == gid), None)
                if not container:
                    _log(f'  {ctype} (GID {gid}): not found in inventory â€" skipping')
                    continue
                found_any_container = True
                c_slots = container.get('slots') or []
                c_filled = [s for s in c_slots if s]
                leaves, skipped = _collect_leaves(container)
                all_leaves.extend(leaves)
                total_skipped += skipped
                _log(f'  {ctype} (GID {gid}): {len(c_slots)} slots, {len(c_filled)} filled, {len(leaves)} items, {skipped} empty')
 
            if not found_any_container:
                _log('ERROR: No containers found in inventory')
                return {'ok': False, 'error': 'No containers (backpack/quickuse/safepocket/augment) found in inventory.'}
 
            _log(f'Total: {len(all_leaves)} items across all containers, {total_skipped} empty slots skipped')
            if not all_leaves:
                _log('ERROR: No items in any container')
                return {'ok': False, 'error': 'No items found in any container.'}
 
            pairs = [(leaf, parent, leaf['instanceId'], str(uuid.uuid4())) for leaf, parent in all_leaves]
 
            # Build mutations: REVERSED ORDER â€” delete â†’ create â†’ update
            def _build_mutations(batch):
                mutations = []
                parent_map = {}
                for leaf, parent, old, new in batch:
                    pid = parent['instanceId']
                    if pid not in parent_map:
                        parent_map[pid] = (parent, {})
                    parent_map[pid][1][old] = new
 
                # 1. Delete all old items first
                for leaf, parent, old, new in batch:
                    mutations.append({'discriminator': 'delete', 'instanceId': old})
 
                # 2. Create all new items
                for leaf, parent, old, new in batch:
                    mutations.append(
                        {'discriminator': 'create', 'gameAssetId': leaf['gameAssetId'],
                         'instanceId': new, 'amount': leaf.get('amount', 1),
                         'slots': [], 'etag': leaf.get('etag', '')})
 
                # 3. Update parents with new slot references last
                for pid, (parent, replacements) in parent_map.items():
                    new_slots = [replacements.get(s, s) for s in (parent.get('slots') or [])]
                    mutations.append(
                        {'discriminator': 'update', 'instanceId': pid,
                         'amount': parent.get('amount', 1),
                         'slots': new_slots, 'etag': parent.get('etag', '')})
 
                return mutations
 
            def _apply_success(batch, res):
                updated = {u['instanceId']: u for u in
                           ((res.get('changeset') or {}).get('items', {}).get('updated') or [])}
                for leaf, parent, old, new in batch:
                    by_iid.pop(old, None)
                    leaf['instanceId'] = new
                    by_iid[new] = leaf
                    parent['slots'] = [new if s == old else s for s in (parent.get('slots') or [])]
                    if parent['instanceId'] in updated:
                        parent['etag'] = updated[parent['instanceId']].get('etag', parent['etag'])
 
            def _send_batch(batch):
                bad = set()
                transient_retries = 0
                while True:
                    active = [t for t in batch if t[2] not in bad]
                    if not active:
                        break
                    mutations = _build_mutations(active)
                    payload = json.dumps({'mutations': mutations, 'requestId': ''})
                    try:
                        st, raw = _api('POST', '/v1/pioneer/inventory/v1/mutate',
                                        body=payload.encode('utf-8'))
                    except Exception as e:
                        _log(f'ERROR: Mutate exception: {e}')
                        return 0, bad, str(e)
                    _log(f'  Mutate response: HTTP {st}')
                    if 200 <= st < 300:
                        try:
                            res = json.loads(raw)
                        except Exception:
                            res = {}
                        _apply_success(active, res)
                        return len(active), bad, ''
                    err = ''
                    try:
                        err_body = json.loads(raw)
                        err = err_body.get('message') or str(err_body)[:300]
                    except Exception:
                        err = raw.decode('utf-8', errors='replace')[:300]
                    _log(f'  Error body: {err[:300]}')
 
                    if st >= 500:
                        transient_retries += 1
                        if transient_retries <= 1:
                            _log(f'  Transient HTTP {st} ({transient_retries}/1) â€” retrying batchâ€¦')
                            continue
 
                    transient_retries = 0
                    m = UUID_RE.search(err)
                    if m:
                        bad.add(m.group(1))
                        _log(f'  Retrying â€” skipping {m.group(1)[:8]}â€¦')
                    else:
                        _log(f'ERROR: HTTP {st} â€” {err}')
                        return 0, bad, f'HTTP {st}: {err[:200]}'
                return 0, bad, 'All items skipped'
 
            BATCH = len(pairs)  # send ALL items in one call
            total_refreshed = 0
            refreshed_details = []
            last_err = ''
 
            for i in range(0, len(pairs), BATCH):
                batch = pairs[i:i + BATCH]
                _log(f'Sending batch {i//BATCH+1}: {len(batch)} items, {len(batch)*3} mutations')
                n, bad, err = _send_batch(batch)
 
                # If a full TEST batch hits server-side 500, isolate with split retries first.
                if err and ('HTTP 500' in err) and len(batch) > 1:
                    _log('Batch hit HTTP 500 - isolating with split retries...')
                    n = 0
                    bad = set()
                    item_errs = []
                    queue = [batch]
 
                    while queue:
                        chunk = queue.pop(0)
                        n1, bad1, err1 = _send_batch(chunk)
                        n += n1
                        bad.update(bad1)
 
                        if not err1:
                            continue
 
                        if 'HTTP 500' in err1 and len(chunk) > 1:
                            mid = max(1, len(chunk) // 2)
                            queue.append(chunk[:mid])
                            queue.append(chunk[mid:])
                            continue
 
                        if len(chunk) > 1:
                            for one in chunk:
                                queue.append([one])
                            continue
 
                        one = chunk[0]
                        bad.add(one[2])
                        item_errs.append(f'{one[2][:8]}: {err1}')
 
                    if item_errs:
                        _log(f'Item-level errors: {"; ".join(item_errs[:3])}')
                        err = '; '.join(item_errs[:3])
                    else:
                        err = ''
 
                _log(f'Batch result: {n} refreshed, {len(bad)} skipped')
                if err:
                    last_err = err
                if n > 0:
                    for leaf, parent, old, new in batch:
                        if old not in bad:
                            leaf_name = _item_name(leaf.get('gameAssetId', 0))
                            parent_name = _item_name(parent.get('gameAssetId', 0))
                            if leaf_name.startswith('Unknown') and not parent_name.startswith('Unknown'):
                                display_name = parent_name
                            else:
                                display_name = leaf_name
                            amt = leaf.get('amount', 1)
                            if amt > 1:
                                display_name = f'{display_name} x{amt}'
                            refreshed_details.append({
                                'name': display_name,
                                'gid': leaf.get('gameAssetId', 0),
                                'amount': amt,
                                'old': old[:12],
                                'new': new[:12],
                            })
                    total_refreshed += n
 
            if total_refreshed > 0:
                _log(f'SUCCESS â€” {total_refreshed} items refreshed (TEST order)')
                _conn.close()
                return {'ok': True, 'refreshed': total_refreshed, 'skipped': total_skipped, 'details': refreshed_details}
            else:
                if attempt == 0:
                    _log(f'Failed â€” {last_err} â€” retrying with fresh inventoryâ€¦')
                    continue
                _log(f'FAILED â€” {last_err}')
                _conn.close()
                return {'ok': False, 'error': last_err or 'Test failed'}
 
        _log('FAILED after retries')
        _conn.close()
        return {'ok': False, 'error': 'Test failed after retry'}
 
    # â”€â”€ SUPER REFRESH â€” entire stash â”€â”€
    def execute_super_refresh(self):
        """Refresh ALL items in the stash (gid -2121050171) with new instance IDs."""
        _log('â•' * 60)
        _log('SUPER REFRESH â€” Starting full stash refresh')
 
        latest_hdrs = _get_latest_headers()
        if not latest_hdrs:
            _log('ERROR: No auth token')
            return {'ok': False, 'error': 'No auth token captured. Start proxy, then play the game.'}
 
        auth_token = latest_hdrs.get('Authorization') or latest_hdrs.get('authorization', '')
        if not auth_token:
            _log('ERROR: No Authorization header')
            return {'ok': False, 'error': 'No auth token found.'}
 
        host = 'api-gateway.europe.es-pio.net'
        api_headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json',
            'x-embark-request-id': '',
            'x-embark-telemetry-client-platform': '12',
            'Accept': '*/*',
            'Host': host,
        }
        for hk in ['x-embark-manifest-id', 'User-Agent']:
            if hk in latest_hdrs:
                api_headers[hk] = latest_hdrs[hk]
 
        STASH_GID = -2121050171
        UUID_RE = __import__('re').compile(
            r'(?:item with id|instanceId|instance_id|item):\s*"?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"?',
            __import__('re').IGNORECASE,
        )
 
        last_error = None
        for attempt in range(2):
            _log(f'Attempt {attempt + 1}/2 â€” Fetching inventoryâ€¦')
            try:
                status, raw = _api_request('GET', '/v1/pioneer/inventory', headers=api_headers)
            except Exception as e:
                _log(f'ERROR: Inventory request failed: {e}')
                return {'ok': False, 'error': f'Inventory request failed: {e}'}
 
            if status != 200:
              err_msg = _inventory_http_error(status, raw)
              _log(f'ERROR: Inventory HTTP {status} - {err_msg}')
              return {'ok': False, 'error': err_msg}
 
            try:
                inv = json.loads(raw)
            except Exception:
                _log('ERROR: Failed to parse inventory JSON')
                return {'ok': False, 'error': 'Failed to parse inventory JSON'}
 
            items = inv.get('items', [])
            by_iid = {i['instanceId']: i for i in items}
            _log(f'Inventory loaded: {len(items)} total items')
 
            # Find stash container
            stash = next((i for i in items if i.get('gameAssetId') == STASH_GID), None)
            if not stash:
                _log('ERROR: No stash container found')
                return {'ok': False, 'error': 'No stash container found in inventory.'}
 
            # Stash has one slot pointing to stash root
            root_iid = (stash.get('slots') or [None])[0]
            root = by_iid.get(root_iid) if root_iid else None
            if not root:
                _log('ERROR: Stash root not found')
                return {'ok': False, 'error': 'Stash root not found.'}
 
            # Walk tree to find leaf items
            def _is_structural(item):
                s = item.get('slots')
                return isinstance(s, list) and not any(s)
 
            def _collect_leaves(root):
                leaves = []
                skipped = 0
                def walk(iid, parent):
                    nonlocal skipped
                    item = by_iid.get(iid)
                    if not item:
                        return
                    if _is_structural(item):
                        skipped += 1
                        return
                    kids = [s for s in (item.get('slots') or []) if s]
                    if not kids:
                        leaves.append((item, parent))
                    else:
                        for c in kids:
                            walk(c, item)
                for s in (root.get('slots') or []):
                    if s:
                        walk(s, root)
                return leaves, skipped
 
            all_leaves, total_skipped = _collect_leaves(root)
            _log(f'Stash: found {len(all_leaves)} items, {total_skipped} empty slots skipped')
 
            if not all_leaves:
                _log('ERROR: No items in stash')
                return {'ok': False, 'error': 'No items found in stash.'}
 
            pairs = [(leaf, parent, leaf['instanceId'], str(uuid.uuid4())) for leaf, parent in all_leaves]
 
            def _build_mutations(batch):
                mutations = []
                parent_map = {}
                for leaf, parent, old, new in batch:
                    pid = parent['instanceId']
                    if pid not in parent_map:
                        parent_map[pid] = (parent, {})
                    parent_map[pid][1][old] = new
 
                for leaf, parent, old, new in batch:
                    mutations.append(
                        {'discriminator': 'create', 'gameAssetId': leaf['gameAssetId'],
                         'instanceId': new, 'amount': leaf.get('amount', 1),
                         'slots': [], 'etag': leaf.get('etag', '')})
 
                for pid, (parent, replacements) in parent_map.items():
                    new_slots = [replacements.get(s, s) for s in (parent.get('slots') or [])]
                    mutations.append(
                        {'discriminator': 'update', 'instanceId': pid,
                         'amount': parent.get('amount', 1),
                         'slots': new_slots, 'etag': parent.get('etag', '')})
 
                for leaf, parent, old, new in batch:
                    mutations.append({'discriminator': 'delete', 'instanceId': old})
 
                return mutations
 
            def _apply_success(batch, res):
                updated = {u['instanceId']: u for u in
                           ((res.get('changeset') or {}).get('items', {}).get('updated') or [])}
                for leaf, parent, old, new in batch:
                    by_iid.pop(old, None)
                    leaf['instanceId'] = new
                    by_iid[new] = leaf
                    parent['slots'] = [new if s == old else s for s in (parent.get('slots') or [])]
                    if parent['instanceId'] in updated:
                        parent['etag'] = updated[parent['instanceId']].get('etag', parent['etag'])
 
            def _send_batch(batch):
                bad = set()
                while True:
                    active = [t for t in batch if t[2] not in bad]
                    if not active:
                        break
                    mutations = _build_mutations(active)
                    payload = json.dumps({'mutations': mutations, 'requestId': ''})
                    try:
                        st, raw = _api_request('POST', '/v1/pioneer/inventory/v1/mutate',
                                               body=payload.encode('utf-8'), headers=api_headers)
                    except Exception as e:
                        _log(f'ERROR: Mutate exception: {e}')
                        return 0, bad, str(e)
                    _log(f'  Mutate response: HTTP {st}')
                    if 200 <= st < 300:
                        try:
                            res = json.loads(raw)
                        except Exception:
                            res = {}
                        _apply_success(active, res)
                        return len(active), bad, ''
                    err = ''
                    try:
                        err_body = json.loads(raw)
                        err = err_body.get('message') or str(err_body)[:300]
                    except Exception:
                        err = raw.decode('utf-8', errors='replace')[:300]
                    _log(f'  Error body: {err[:300]}')
                    m = UUID_RE.search(err)
                    if m:
                        bad.add(m.group(1))
                        _log(f'  Retrying â€” skipping {m.group(1)[:8]}â€¦')
                        time.sleep(0.1)
                    else:
                        _log(f'ERROR: HTTP {st} â€” {err}')
                        return 0, bad, f'HTTP {st}: {err[:200]}'
                return 0, bad, 'All items skipped'
 
            BATCH = 24
            total_refreshed = 0
            refreshed_details = []
            last_err = ''
 
            for i in range(0, len(pairs), BATCH):
                batch = pairs[i:i + BATCH]
                _log(f'Sending batch {i//BATCH+1}/{(len(pairs)+BATCH-1)//BATCH}: {len(batch)} items')
                n, bad, err = _send_batch(batch)
                _log(f'Batch result: {n} refreshed, {len(bad)} skipped')
                if err:
                    last_err = err
                if n > 0:
                    for leaf, parent, old, new in batch:
                        if old not in bad:
                            leaf_name = _item_name(leaf.get('gameAssetId', 0))
                            parent_name = _item_name(parent.get('gameAssetId', 0))
                            if leaf_name.startswith('Unknown') and not parent_name.startswith('Unknown'):
                                display_name = parent_name
                            else:
                                display_name = leaf_name
                            amt = leaf.get('amount', 1)
                            if amt > 1:
                                display_name = f'{display_name} x{amt}'
                            refreshed_details.append({
                                'name': display_name,
                                'gid': leaf.get('gameAssetId', 0),
                                'amount': amt,
                                'old': old[:12],
                                'new': new[:12],
                            })
                    total_refreshed += n
 
            if total_refreshed > 0:
                _log(f'SUPER REFRESH SUCCESS â€” {total_refreshed} items refreshed')
                return {'ok': True, 'refreshed': total_refreshed, 'skipped': total_skipped, 'details': refreshed_details}
            else:
                if attempt == 0:
                    _log(f'Failed â€” {last_err} â€” retrying with fresh inventoryâ€¦')
                    time.sleep(0.2)
                    continue
                _log(f'SUPER REFRESH FAILED â€” {last_err}')
                return {'ok': False, 'error': last_err or 'Super refresh failed'}
 
        _log('SUPER REFRESH FAILED after retries')
        return {'ok': False, 'error': 'Super refresh failed after retry'}
 
    # â”€â”€ Shutdown â”€â”€
    def shutdown(self):
        global _proxy_process, _proxy_running
        _proxy_running = False
        _disable_proxy()
        if _proxy_process:
            try:
                _proxy_process.terminate()
            except Exception:
                pass
            _proxy_process = None
 
 
# â”€â”€â”€ HTML / CSS / JS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OneMore</title>
<style>
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   ONEMORE â€” Liquid Architectural Glass System
   True transparent window. Desktop visible behind everything.
   Only glass surfaces render. Everything else is void.
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
:root {
  /* Glass fills â€” obsidian / graphite / smoked tones, LOW opacity */
  --glass-0: rgba(10, 10, 18, 0.42);
  --glass-1: rgba(14, 14, 24, 0.52);
  --glass-2: rgba(18, 18, 30, 0.58);
  --glass-3: rgba(22, 22, 36, 0.64);
 
  /* Edge system â€” cold silver highlights */
  --edge-faint:   rgba(180, 200, 220, 0.06);
  --edge-subtle:  rgba(180, 200, 220, 0.10);
  --edge-soft:    rgba(200, 215, 230, 0.14);
  --edge-medium:  rgba(210, 225, 240, 0.19);
  --edge-bright:  rgba(220, 235, 250, 0.28);
 
  /* Inner sheen â€” top-edge specular */
  --sheen-faint:  rgba(255, 255, 255, 0.04);
  --sheen-subtle: rgba(255, 255, 255, 0.07);
  --sheen-soft:   rgba(255, 255, 255, 0.11);
 
  /* Blur â€” variable by elevation */
  --blur-0: 18px;
  --blur-1: 28px;
  --blur-2: 36px;
  --blur-3: 48px;
 
  /* Accent â€” icy blue-violet, single hue */
  --accent:        #7b9fdb;
  --accent-pure:   #6e8fd4;
  --accent-dim:    rgba(110, 143, 212, 0.12);
  --accent-mid:    rgba(110, 143, 212, 0.28);
  --accent-glow:   rgba(110, 143, 212, 0.45);
  --accent-text:   #a8c4e8;
 
  /* Semantic */
  --ok:       #5ee6b4;
  --ok-dim:   rgba(94, 230, 180, 0.10);
  --ok-glow:  rgba(94, 230, 180, 0.30);
  --err:      #f07070;
  --err-dim:  rgba(240, 112, 112, 0.10);
  --warn:     #e8c45a;
  --warn-dim: rgba(232, 196, 90, 0.10);
 
  /* Text hierarchy */
  --t-1: rgba(235, 240, 250, 0.94);
  --t-2: rgba(190, 200, 220, 0.70);
  --t-3: rgba(150, 165, 185, 0.48);
  --t-4: rgba(130, 145, 165, 0.30);
 
  /* Shadow system */
  --sh-glass:
    0 1px 1px rgba(0,0,0,0.08),
    0 4px 12px rgba(0,0,0,0.12),
    0 12px 36px rgba(0,0,0,0.10),
    0 36px 80px rgba(0,0,0,0.08);
  --sh-glass-hover:
    0 2px 2px rgba(0,0,0,0.10),
    0 6px 18px rgba(0,0,0,0.14),
    0 18px 48px rgba(0,0,0,0.12),
    0 48px 96px rgba(0,0,0,0.10);
  --sh-elevated:
    0 2px 4px rgba(0,0,0,0.14),
    0 8px 24px rgba(0,0,0,0.16),
    0 24px 64px rgba(0,0,0,0.12);
 
  /* Motion */
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --dur-fast:  100ms;
  --dur-med:   250ms;
  --dur-slow:  450ms;
  --dur-lux:   700ms;
 
  /* Radii */
  --r-s:  10px;
  --r-m:  14px;
  --r-l:  18px;
  --r-xl: 22px;
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   RESET & AMBIENT BACKDROP
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
 
html {
  background: #080810 !important;
}
body {
  font-family: -apple-system, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  font-size: 13px;
  line-height: 1.5;
  color: var(--t-1);
  height: 100vh;
  overflow: hidden;
  user-select: none;
  -webkit-user-select: none;
  -webkit-font-smoothing: antialiased;
  background: linear-gradient(160deg, #0a0e1a 0%, #080810 40%, #0c0816 100%) !important;
}
 
/* Ambient backdrop layer â€” rendered as a real div to avoid
   pseudo-element hit-testing issues in WebView2 transparent mode */
.ambient-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 55% 45% at 15% 15%, rgba(110,143,212,0.18) 0%, transparent 65%),
    radial-gradient(ellipse 45% 55% at 85% 80%, rgba(100,60,200,0.14) 0%, transparent 60%),
    radial-gradient(ellipse 40% 35% at 70% 20%, rgba(60,140,180,0.08) 0%, transparent 55%),
    radial-gradient(ellipse 60% 30% at 40% 95%, rgba(80,50,160,0.10) 0%, transparent 65%);
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   APP LAYOUT â€” No outer frame. Panels float in the void.
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.app {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 0;
  background: transparent;
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   DRAGBAR â€” Thin floating glass strip at top
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.dragbar {
  position: relative;
  z-index: 100;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  margin: 8px 8px 0 8px;
  border-radius: var(--r-l);
  background: var(--glass-2);
  backdrop-filter: blur(var(--blur-2)) saturate(1.4) brightness(0.95);
  -webkit-backdrop-filter: blur(var(--blur-2)) saturate(1.4) brightness(0.95);
  border: 1px solid var(--edge-subtle);
  box-shadow:
    var(--sh-glass),
    inset 0 1px 0 var(--sheen-subtle);
  cursor: grab;
  flex-shrink: 0;
}
.dragbar:active { cursor: grabbing; }
 
.drag-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.drag-logo {
  width: 18px; height: 18px;
  border-radius: 6px;
  background: linear-gradient(135deg, var(--accent-pure), rgba(110,143,212,0.6));
  box-shadow: 0 0 10px var(--accent-dim);
  display: flex; align-items: center; justify-content: center;
  font-size: 8.5px; font-weight: 800; color: #fff;
}
.drag-title {
  font-size: 11px; font-weight: 650; letter-spacing: 2.2px;
  text-transform: uppercase; color: var(--t-3);
}
 
.drag-controls {
  display: flex; align-items: center; gap: 12px;
  cursor: default;
}
 
/* â”€â”€ Proxy pill â”€â”€ */
.proxy-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 3px 10px 3px 7px;
  border-radius: 100px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--edge-faint);
  cursor: pointer;
  transition: all var(--dur-fast);
}
.proxy-pill:hover { background: rgba(255,255,255,0.06); border-color: var(--edge-subtle); }
.proxy-pill.on { background: var(--ok-dim); border-color: rgba(94,230,180,0.18); }
 
.pdot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--err);
  transition: all var(--dur-med) var(--ease-out);
}
.pdot.active {
  background: var(--ok);
  box-shadow: 0 0 8px var(--ok-glow);
  animation: pdotPulse 2.5s ease-in-out infinite;
}
 @Keyframes pdotPulse {
  0%,100% { box-shadow: 0 0 5px rgba(94,230,180,0.25); }
  50%     { box-shadow: 0 0 12px rgba(94,230,180,0.45); }
}
.plabel {
  font-size: 9px; font-weight: 650; letter-spacing: 1px;
  text-transform: uppercase; color: var(--t-4);
  transition: color var(--dur-fast);
}
.proxy-pill.on .plabel { color: var(--ok); }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   CONTENT â€” Scrollable transparent area
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.content {
  flex: 1;
  overflow-y: auto; overflow-x: hidden;
  padding: 14px 8px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}
.content::-webkit-scrollbar { width: 4px; }
.content::-webkit-scrollbar-track { background: transparent; }
.content::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.08); border-radius: 100px;
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   GLASS SURFACE â€” The core material
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.glass {
  position: relative;
  width: 100%; max-width: 460px;
  padding: 20px 22px;
  border-radius: var(--r-xl);
  background: var(--glass-1);
  backdrop-filter: blur(var(--blur-1)) saturate(1.35) brightness(0.92);
  -webkit-backdrop-filter: blur(var(--blur-1)) saturate(1.35) brightness(0.92);
  border: 1px solid var(--edge-subtle);
  box-shadow: var(--sh-glass);
  transition:
    transform var(--dur-med) var(--ease-out),
    box-shadow var(--dur-med) var(--ease-out),
    border-color var(--dur-med);
}
/* Top-edge specular sheen */
.glass::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  background: linear-gradient(
    90deg, transparent 5%, var(--sheen-soft) 30%,
    var(--sheen-subtle) 50%, var(--sheen-soft) 70%, transparent 95%
  );
  pointer-events: none;
}
/* Inner reflection */
.glass::after {
  content: '';
  position: absolute; inset: 0;
  border-radius: inherit; pointer-events: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.028) 0%, transparent 35%);
}
.glass:hover {
  transform: translateY(-1px);
  box-shadow: var(--sh-glass-hover);
  border-color: var(--edge-soft);
}
.glass--compact { padding: 12px 16px; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SECTION LABEL
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.sec-label {
  font-size: 9.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2.5px; color: var(--t-4); margin-bottom: 6px;
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   BUTTONS
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.btn {
  position: relative;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 9px 18px;
  border: 1px solid transparent; border-radius: var(--r-s);
  font-family: inherit; font-size: 11.5px; font-weight: 600;
  letter-spacing: 0.4px; color: var(--t-1);
  cursor: pointer; outline: none; overflow: hidden; background: none;
  transition: all var(--dur-fast) var(--ease-out);
}
.btn:active { transform: scale(0.97); }
 
.btn-pri {
  background: linear-gradient(135deg, rgba(110,143,212,0.45), rgba(90,120,190,0.50));
  border-color: rgba(110,143,212,0.25);
  box-shadow: 0 2px 8px rgba(110,143,212,0.18), inset 0 1px 0 rgba(255,255,255,0.08);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.btn-pri:hover {
  background: linear-gradient(135deg, rgba(110,143,212,0.55), rgba(90,120,190,0.60));
  box-shadow: 0 4px 16px rgba(110,143,212,0.28), inset 0 1px 0 rgba(255,255,255,0.12);
  border-color: rgba(110,143,212,0.35);
}
.btn-pri:disabled { opacity: 0.30; cursor: not-allowed; box-shadow: none; transform: none; }
 
.btn-ghost {
  background: rgba(255,255,255,0.03); border-color: var(--edge-faint);
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
}
.btn-ghost:hover { background: rgba(255,255,255,0.06); border-color: var(--edge-subtle); }
 
.btn-ok {
  background: linear-gradient(135deg, rgba(94,230,180,0.35), rgba(70,200,150,0.40));
  border-color: rgba(94,230,180,0.22);
  box-shadow: 0 2px 8px rgba(94,230,180,0.14), inset 0 1px 0 rgba(255,255,255,0.06);
}
 
.btn-w { width: 100%; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SECRET BUTTON â€” Hero element
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.secret-outer { position: relative; width: 100%; max-width: 460px; display: flex; gap: 10px; align-items: stretch; }
.btn-setkey {
  padding: 12px 14px; font-size: 11px; font-weight: 600; letter-spacing: 1.5px;
  text-transform: uppercase; color: rgba(200,210,230,0.8);
  border: 1px solid rgba(110,143,212,0.15); border-radius: var(--r-lg);
  cursor: pointer; font-family: inherit;
  background: var(--glass-0); backdrop-filter: blur(var(--blur-1));
  -webkit-backdrop-filter: blur(var(--blur-1));
  transition: border-color var(--dur-fast), background var(--dur-fast);
  white-space: nowrap; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
}
.btn-setkey:hover { border-color: rgba(110,143,212,0.35); background: var(--glass-1); }
.btn-setkey .hk-label { font-size: 9px; opacity: 0.5; letter-spacing: 0.5px; }
.hotkey-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.65); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.hotkey-modal {
  background: var(--glass-2); border: 1px solid rgba(110,143,212,0.25);
  border-radius: var(--r-xl); padding: 40px 48px; text-align: center;
  box-shadow: 0 16px 64px rgba(0,0,0,0.4);
}
.hotkey-modal h3 { margin: 0 0 8px; font-size: 15px; font-weight: 600; letter-spacing: 2px; color: rgba(220,230,250,0.9); }
.hotkey-modal p { margin: 0 0 20px; font-size: 12px; color: rgba(180,190,210,0.6); }
.hotkey-modal .hk-display {
  font-size: 22px; font-weight: 700; letter-spacing: 3px; color: rgba(110,170,255,0.95);
  padding: 16px 32px; border: 1px dashed rgba(110,143,212,0.3); border-radius: var(--r-lg);
  min-width: 120px; min-height: 28px;
}
.hotkey-modal .hk-hint { margin-top: 16px; font-size: 10px; color: rgba(180,190,210,0.4); }
.btn-secret {
  position: relative; width: 100%; padding: 24px;
  font-size: 14px; font-weight: 700; letter-spacing: 5px;
  text-transform: uppercase; color: rgba(235,240,250,0.92);
  border: 1px solid rgba(110,143,212,0.18);
  border-radius: var(--r-xl); cursor: pointer;
  font-family: inherit; overflow: hidden;
  background: var(--glass-1);
  backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  -webkit-backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  box-shadow:
    var(--sh-elevated),
    inset 0 1px 0 var(--sheen-subtle),
    inset 0 0 40px rgba(110,143,212,0.04);
  transition:
    box-shadow var(--dur-med) var(--ease-out),
    border-color var(--dur-med),
    transform var(--dur-fast);
}
.btn-secret .stxt { position: relative; z-index: 2; }
 
/* Sweeping specular */
.btn-secret::before {
  content: '';
  position: absolute; top: 0; left: -120%;
  width: 50%; height: 100%;
  background: linear-gradient(
    90deg, transparent, rgba(255,255,255,0.03),
    rgba(255,255,255,0.06), rgba(255,255,255,0.03), transparent
  );
  transform: skewX(-18deg);
  animation: specSweep 8s ease-in-out infinite;
  z-index: 1;
}
/* Top glow */
.btn-secret::after {
  content: '';
  position: absolute; inset: -1px;
  border-radius: inherit; pointer-events: none;
  background: radial-gradient(
    ellipse at 50% 0%, rgba(110,143,212,0.06) 0%, transparent 55%
  );
  z-index: 1;
}
.btn-secret:hover {
  border-color: rgba(110,143,212,0.32);
  box-shadow:
    0 4px 12px rgba(110,143,212,0.18),
    0 16px 48px rgba(110,143,212,0.08),
    0 32px 80px rgba(0,0,0,0.10),
    inset 0 1px 0 var(--sheen-soft),
    inset 0 0 56px rgba(110,143,212,0.07);
  transform: translateY(-1px);
}
.btn-secret:active {
  transform: scale(0.985);
  box-shadow: 0 2px 6px rgba(110,143,212,0.22), inset 0 0 48px rgba(110,143,212,0.12);
}
.btn-secret:disabled {
  opacity: 0.20; cursor: not-allowed;
  box-shadow: var(--sh-glass); transform: none;
}
.btn-secret:disabled::before,
.btn-secret:disabled::after { display: none; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   REFRESH BUTTON
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.refresh-outer { position: relative; width: 100%; max-width: 460px; display: flex; gap: 10px; align-items: stretch; }
.btn-refresh {
  position: relative; width: 100%; padding: 18px;
  font-size: 13px; font-weight: 700; letter-spacing: 4px;
  text-transform: uppercase; color: rgba(180,240,220,0.92);
  border: 1px solid rgba(94,230,180,0.18);
  border-radius: var(--r-xl); cursor: pointer;
  font-family: inherit; overflow: hidden;
  background: var(--glass-1);
  backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  -webkit-backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  box-shadow:
    var(--sh-elevated),
    inset 0 1px 0 var(--sheen-subtle),
    inset 0 0 40px rgba(94,230,180,0.04);
  transition:
    box-shadow var(--dur-med) var(--ease-out),
    border-color var(--dur-med),
    transform var(--dur-fast);
}
.btn-refresh .rtxt { position: relative; z-index: 2; }
.btn-refresh::before {
  content: '';
  position: absolute; top: 0; left: -120%;
  width: 50%; height: 100%;
  background: linear-gradient(
    90deg, transparent, rgba(94,230,180,0.03),
    rgba(94,230,180,0.06), rgba(94,230,180,0.03), transparent
  );
  transform: skewX(-18deg);
  animation: specSweepGreen 8s ease-in-out infinite;
  z-index: 1;
}
.btn-refresh::after {
  content: '';
  position: absolute; inset: -1px;
  border-radius: inherit; pointer-events: none;
  background: radial-gradient(
    ellipse at 50% 0%, rgba(94,230,180,0.06) 0%, transparent 55%
  );
  z-index: 1;
}
.btn-refresh:hover {
  border-color: rgba(94,230,180,0.32);
  box-shadow:
    0 4px 12px rgba(94,230,180,0.18),
    0 16px 48px rgba(94,230,180,0.08),
    0 32px 80px rgba(0,0,0,0.10),
    inset 0 1px 0 var(--sheen-soft),
    inset 0 0 56px rgba(94,230,180,0.07);
  transform: translateY(-1px);
}
.btn-refresh:active {
  transform: scale(0.985);
  box-shadow: 0 2px 6px rgba(94,230,180,0.22), inset 0 0 48px rgba(94,230,180,0.12);
}
.btn-refresh:disabled {
  opacity: 0.20; cursor: not-allowed;
  box-shadow: var(--sh-glass); transform: none;
}
.btn-refresh:disabled::before,
.btn-refresh:disabled::after { display: none; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   TEST BUTTON
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.test-outer { position: relative; width: 100%; max-width: 460px; display: flex; gap: 10px; align-items: stretch; }
.btn-test {
  position: relative; width: 100%; padding: 18px;
  font-size: 13px; font-weight: 700; letter-spacing: 4px;
  text-transform: uppercase; color: rgba(200,160,255,0.92);
  border: 1px solid rgba(160,100,240,0.18);
  border-radius: var(--r-xl); cursor: pointer;
  font-family: inherit; overflow: hidden;
  background: var(--glass-1);
  backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  -webkit-backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  box-shadow:
    var(--sh-elevated),
    inset 0 1px 0 var(--sheen-subtle),
    inset 0 0 40px rgba(160,100,240,0.04);
  transition:
    box-shadow var(--dur-med) var(--ease-out),
    border-color var(--dur-med),
    transform var(--dur-fast);
}
.btn-test .ttxt { position: relative; z-index: 2; }
.btn-test::before {
  content: '';
  position: absolute; top: 0; left: -120%;
  width: 50%; height: 100%;
  background: linear-gradient(
    90deg, transparent, rgba(160,100,240,0.03),
    rgba(160,100,240,0.06), rgba(160,100,240,0.03), transparent
  );
  transform: skewX(-18deg);
  animation: specSweepPurple 8s ease-in-out infinite;
  z-index: 1;
}
.btn-test::after {
  content: '';
  position: absolute; inset: -1px;
  border-radius: inherit; pointer-events: none;
  background: radial-gradient(
    ellipse at 50% 0%, rgba(160,100,240,0.06) 0%, transparent 55%
  );
  z-index: 1;
}
.btn-test:hover {
  border-color: rgba(160,100,240,0.32);
  box-shadow:
    0 4px 12px rgba(160,100,240,0.18),
    0 16px 48px rgba(160,100,240,0.08),
    0 32px 80px rgba(0,0,0,0.10),
    inset 0 1px 0 var(--sheen-soft),
    inset 0 0 56px rgba(160,100,240,0.07);
  transform: translateY(-1px);
}
.btn-test:active {
  transform: scale(0.985);
  box-shadow: 0 2px 6px rgba(160,100,240,0.22), inset 0 0 48px rgba(160,100,240,0.12);
}
.btn-test:disabled {
  opacity: 0.20; cursor: not-allowed;
  box-shadow: var(--sh-glass); transform: none;
}
.btn-test:disabled::before,
.btn-test:disabled::after { display: none; }
 
 @Keyframes specSweepPurple {
  0%   { left: -120%; }
  35%  { left: 170%; }
  100% { left: 170%; }
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SUPER REFRESH BUTTON
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.super-refresh-outer { position: relative; width: 100%; max-width: 460px; display: flex; gap: 10px; align-items: stretch; }
.btn-super-refresh {
  position: relative; width: 100%; padding: 18px;
  font-size: 13px; font-weight: 700; letter-spacing: 4px;
  text-transform: uppercase; color: rgba(255,200,100,0.92);
  border: 1px solid rgba(255,165,0,0.18);
  border-radius: var(--r-xl); cursor: pointer;
  font-family: inherit; overflow: hidden;
  background: var(--glass-1);
  backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  -webkit-backdrop-filter: blur(var(--blur-2)) saturate(1.5);
  box-shadow:
    var(--sh-elevated),
    inset 0 1px 0 var(--sheen-subtle),
    inset 0 0 40px rgba(255,165,0,0.04);
  transition:
    box-shadow var(--dur-med) var(--ease-out),
    border-color var(--dur-med),
    transform var(--dur-fast);
}
.btn-super-refresh .srtxt { position: relative; z-index: 2; }
.btn-super-refresh::before {
  content: '';
  position: absolute; top: 0; left: -120%;
  width: 50%; height: 100%;
  background: linear-gradient(
    90deg, transparent, rgba(255,165,0,0.03),
    rgba(255,165,0,0.06), rgba(255,165,0,0.03), transparent
  );
  transform: skewX(-18deg);
  animation: specSweepOrange 8s ease-in-out infinite;
  z-index: 1;
}
.btn-super-refresh::after {
  content: '';
  position: absolute; inset: -1px;
  border-radius: inherit; pointer-events: none;
  background: radial-gradient(
    ellipse at 50% 0%, rgba(255,165,0,0.06) 0%, transparent 55%
  );
  z-index: 1;
}
.btn-super-refresh:hover {
  border-color: rgba(255,165,0,0.32);
  box-shadow:
    0 4px 12px rgba(255,165,0,0.18),
    0 16px 48px rgba(255,165,0,0.08),
    0 32px 80px rgba(0,0,0,0.10),
    inset 0 1px 0 var(--sheen-soft),
    inset 0 0 56px rgba(255,165,0,0.07);
  transform: translateY(-1px);
}
.btn-super-refresh:active {
  transform: scale(0.985);
  box-shadow: 0 2px 6px rgba(255,165,0,0.22), inset 0 0 48px rgba(255,165,0,0.12);
}
.btn-super-refresh:disabled {
  opacity: 0.20; cursor: not-allowed;
  box-shadow: var(--sh-glass); transform: none;
}
.btn-super-refresh:disabled::before,
.btn-super-refresh:disabled::after { display: none; }
 
 @Keyframes specSweepOrange {
  0%   { left: -120%; }
  35%  { left: 170%; }
  100% { left: 170%; }
}
 
 @Keyframes specSweepGreen {
  0%   { left: -120%; }
  35%  { left: 170%; }
  100% { left: 170%; }
}
 
 @Keyframes specSweep {
  0%   { left: -120%; }
  35%  { left: 170%; }
  100% { left: 170%; }
}
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   BADGES
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 8px; border-radius: 6px;
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; border: 1px solid transparent;
}
.badge-ok   { background: var(--ok-dim);   color: var(--ok);   border-color: rgba(94,230,180,0.16); }
.badge-warn { background: var(--warn-dim); color: var(--warn); border-color: rgba(232,196,90,0.16); }
.badge-err  { background: var(--err-dim);  color: var(--err);  border-color: rgba(240,112,112,0.16); }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SETUP STEPS
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.step {
  display: flex; align-items: flex-start; gap: 13px;
  position: relative; padding-bottom: 16px;
}
.step:last-child { padding-bottom: 0; }
.step:not(:last-child)::after {
  content: '';
  position: absolute; left: 13px; top: 30px; bottom: 0;
  width: 1px; background: var(--edge-faint);
}
.step-pip {
  flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: var(--accent-text);
  background: var(--accent-dim);
  border: 1px solid rgba(110,143,212,0.22);
  position: relative; z-index: 1;
  transition: all var(--dur-med) var(--ease-out);
}
.step-pip.done {
  background: var(--ok-dim); border-color: rgba(94,230,180,0.22);
  color: var(--ok); box-shadow: 0 0 10px rgba(94,230,180,0.12);
}
.step-body { flex: 1; min-width: 0; }
.step-body h3 { font-size: 12px; font-weight: 600; margin-bottom: 2px; color: var(--t-1); }
.step-body p { font-size: 11px; color: var(--t-3); line-height: 1.55; }
.step-actions { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   AUGMENT SELECTOR
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.aug {
  display: flex; align-items: center; gap: 11px;
  padding: 11px 13px; margin-bottom: 5px;
  border-radius: var(--r-s);
  border: 1px solid var(--edge-faint);
  background: rgba(255,255,255,0.015);
  cursor: pointer;
  transition: background var(--dur-fast), border-color var(--dur-fast),
    box-shadow var(--dur-med) var(--ease-out);
}
.aug:hover { background: rgba(110,143,212,0.04); border-color: rgba(110,143,212,0.16); }
.aug.sel {
  background: rgba(110,143,212,0.06);
  border-color: rgba(110,143,212,0.28);
  box-shadow: inset 0 0 18px rgba(110,143,212,0.05);
}
.aug-radio {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.14);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: border-color var(--dur-fast);
}
.aug.sel .aug-radio { border-color: var(--accent); }
.aug.sel .aug-radio::after {
  content: ''; width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); box-shadow: 0 0 5px var(--accent-mid);
}
.aug-name { font-size: 12px; font-weight: 550; color: var(--t-1); }
.aug-sub { font-size: 9.5px; color: var(--t-4); margin-top: 1px; font-variant-numeric: tabular-nums; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   NAV ITEMS
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.nav-list {
  width: 100%; max-width: 460px;
  display: flex; flex-direction: column; gap: 5px;
}
.nav-item {
  position: relative;
  display: flex; align-items: center; gap: 10px;
  padding: 11px 14px;
  border-radius: var(--r-m);
  background: var(--glass-0);
  backdrop-filter: blur(var(--blur-0)) saturate(1.2);
  -webkit-backdrop-filter: blur(var(--blur-0)) saturate(1.2);
  border: 1px solid var(--edge-faint);
  box-shadow: var(--sh-glass);
  cursor: pointer;
  transition: background var(--dur-fast), border-color var(--dur-fast),
    box-shadow var(--dur-med), transform var(--dur-med) var(--ease-out);
  font-size: 12px; font-weight: 550;
  color: var(--t-2); letter-spacing: 0.3px;
}
.nav-item::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  border-radius: inherit;
  background: linear-gradient(90deg, transparent, var(--sheen-faint), transparent);
  pointer-events: none;
}
.nav-item:hover {
  background: var(--glass-1); border-color: var(--edge-soft);
  box-shadow: var(--sh-glass-hover); transform: translateY(-1px);
  color: var(--t-1);
}
.nav-item:active {
  box-shadow: inset 0 0 20px rgba(110,143,212,0.06);
  transform: translateY(0);
}
.nicon { width: 16px; height: 16px; opacity: 0.35; flex-shrink: 0; }
.nav-item:hover .nicon { opacity: 0.6; }
.narrow { margin-left: auto; width: 12px; height: 12px; opacity: 0.2; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   BACK LINK
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.back {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 550; color: var(--t-3);
  cursor: pointer; transition: color var(--dur-fast);
  margin-bottom: 6px; width: 100%; max-width: 460px;
}
.back:hover { color: var(--t-1); }
.back svg { width: 13px; height: 13px; }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   TOAST
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.toast {
  position: fixed; bottom: 20px; left: 50%;
  transform: translateX(-50%) translateY(70px);
  padding: 9px 18px; border-radius: var(--r-m);
  background: var(--glass-2);
  backdrop-filter: blur(var(--blur-2));
  -webkit-backdrop-filter: blur(var(--blur-2));
  border: 1px solid var(--edge-subtle);
  box-shadow: var(--sh-elevated);
  font-size: 11px; font-weight: 600; z-index: 500;
  transition: transform var(--dur-slow) var(--ease-out), opacity var(--dur-slow);
  opacity: 0; pointer-events: none;
}
.toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
.toast.success { border-color: rgba(94,230,180,0.25); color: var(--ok); }
.toast.error   { border-color: rgba(240,112,112,0.25); color: var(--err); }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   DETAILS OVERLAY
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.details-overlay {
  position: fixed; inset: 0; z-index: 9998;
  background: rgba(0,0,0,0.65); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.details-panel {
  background: var(--glass-2); border: 1px solid rgba(94,230,180,0.2);
  border-radius: var(--r-xl); padding: 24px;
  width: 90%; max-width: 440px; max-height: 70vh;
  display: flex; flex-direction: column;
  box-shadow: 0 16px 64px rgba(0,0,0,0.4);
}
.details-panel h3 {
  margin: 0 0 4px; font-size: 14px; font-weight: 700;
  letter-spacing: 2px; color: rgba(94,230,180,0.9); text-transform: uppercase;
}
.details-panel .dp-sub {
  margin: 0 0 14px; font-size: 11px; color: rgba(180,190,210,0.5);
}
.details-list {
  flex: 1; overflow-y: auto; margin: 0; padding: 0; list-style: none;
}
.details-list li {
  padding: 7px 0; border-bottom: 1px solid rgba(110,143,212,0.08);
  font-size: 11px; color: rgba(210,220,240,0.85); display: flex; flex-direction: column; gap: 2px;
}
.details-list li:last-child { border-bottom: none; }
.details-list .dl-name {
  font-weight: 700; font-size: 12px; color: rgba(220,235,250,0.95);
}
.details-list .dl-ids {
  font-size: 10px; color: rgba(160,170,200,0.55); font-family: monospace; letter-spacing: 0.5px;
}
.details-list .dl-parent {
  font-size: 10px; color: rgba(94,230,180,0.5);
}
.details-close {
  margin-top: 14px; padding: 10px; width: 100%; font-size: 11px;
  font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase;
  color: rgba(200,210,230,0.8); background: var(--glass-1);
  border: 1px solid rgba(110,143,212,0.15); border-radius: var(--r-lg);
  cursor: pointer; font-family: inherit;
}
.details-close:hover { border-color: rgba(110,143,212,0.35); background: var(--glass-2); }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SPINNER
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.spin {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.12);
  border-top-color: rgba(255,255,255,0.65);
  border-radius: 50%;
  animation: spinr 0.6s linear infinite;
  display: inline-block; vertical-align: middle;
}
 @Keyframes spinr { to { transform: rotate(360deg); } }
 
/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   SECTIONS
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */
.sec {
  display: none;
  flex-direction: column; align-items: center; gap: 10px;
  width: 100%;
  animation: secIn var(--dur-lux) var(--ease-out);
}
.sec.active { display: flex; }
 @Keyframes secIn {
  from { opacity: 0; transform: translateY(8px) scale(0.995); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
 
/* STATUS ROW */
.status-row {
  display: flex; justify-content: space-between; align-items: center; width: 100%;
}
 
/* DIVIDER */
.divider {
  width: 100%; max-width: 460px;
  height: 1px; background: var(--edge-faint); margin: 2px 0;
}
</style>
</head>
<body>
 
<div class="ambient-bg"></div>
 
<div class="app">
 
  <!-- â”€â”€â”€â”€ Dragbar â”€â”€â”€â”€ -->
  <div class="dragbar">
    <div class="drag-brand">
      <div class="drag-logo">O</div>
      <span class="drag-title">OneMore</span>
    </div>
    <div class="drag-controls">
      <div class="proxy-pill" id="proxyPill" onclick="onToggleProxy()">
        <div class="pdot" id="proxyDot"></div>
        <span class="plabel" id="proxyLabel">OFF</span>
      </div>
    </div>
  </div>
 
  <!-- â”€â”€â”€â”€ Content â”€â”€â”€â”€ -->
  <div class="content">
 
    <!-- SEC: Setup -->
    <div class="sec active" id="secSetup">
      <div class="glass">
        <div class="sec-label">Proxy Setup</div>
 
        <div class="step">
          <div class="step-pip" id="stepNum1">1</div>
          <div class="step-body">
            <h3>Install mitmproxy</h3>
            <p id="mitmStatus">Checking&hellip;</p>
            <div class="step-actions" id="mitmAction"></div>
          </div>
        </div>
 
        <div class="step">
          <div class="step-pip" id="stepNum2">2</div>
          <div class="step-body">
            <h3>Start Proxy</h3>
            <p>Launch the MITM proxy to begin capturing traffic.</p>
            <div class="step-actions">
              <button class="btn btn-pri" id="btnStartProxy" onclick="onStartProxy()" disabled>Start Proxy</button>
            </div>
          </div>
        </div>
 
        <div class="step">
          <div class="step-pip" id="stepNum3">3</div>
          <div class="step-body">
            <h3>Install Certificate</h3>
            <p>Open the .p12 cert and follow the wizard with defaults.</p>
            <div class="step-actions">
              <button class="btn btn-ghost" id="btnCert" onclick="onOpenCert()" disabled>Open .p12</button>
              <button class="btn btn-ok" id="btnCertDone" onclick="onCertDone()" disabled>Done</button>
            </div>
          </div>
        </div>
      </div>
    </div>
 
    <!-- SEC: Home -->
    <div class="sec" id="secHome">
 
      <div class="glass glass--compact">
        <div class="status-row">
          <span class="badge badge-warn" id="tokenBadge">NO TOKEN</span>
          <span class="badge badge-warn" id="augBadge">NOT CONFIGURED</span>
        </div>
        <div class="step-actions" style="margin-top:8px; justify-content:center;">
          <button class="btn btn-ghost" id="btnDetectToken" onclick="onDetectToken()">Detect Token</button>
        </div>
      </div>
 
      <div class="secret-outer">
        <button class="btn-secret" id="btnSecret" onclick="onSecret()" disabled>
          <span class="stxt">SECRET</span>
        </button>
        <button class="btn-setkey" id="btnSetKey" onclick="openHotkeyModal()">
          SET
          <span class="hk-label" id="hkLabel">---</span>
        </button>
      </div>
 
      <div class="refresh-outer">
        <button class="btn-refresh" id="btnRefresh" onclick="onRefresh()" disabled>
          <span class="rtxt">REFRESH</span>
        </button>
        <button class="btn-setkey" id="btnSetRefreshKey" onclick="openRefreshHotkeyModal()">
          SET
          <span class="hk-label" id="refreshHkLabel">---</span>
        </button>
      </div>
 
      <div class="test-outer">
        <button class="btn-test" id="btnTest" onclick="onTest()" disabled>
          <span class="ttxt">TEST</span>
        </button>
        <button class="btn-setkey" id="btnSetTestKey" onclick="openTestHotkeyModal()">
          SET
          <span class="hk-label" id="testHkLabel">---</span>
        </button>
      </div>
 
      <div class="super-refresh-outer">
        <button class="btn-super-refresh" id="btnSuperRefresh" onclick="onSuperRefresh()" disabled>
          <span class="srtxt">SUPER REFRESH</span>
        </button>
        <button class="btn-setkey" id="btnSetSuperRefreshKey" onclick="openSuperRefreshHotkeyModal()">
          SET
          <span class="hk-label" id="superRefreshHkLabel">---</span>
        </button>
      </div>
 
      <div class="divider"></div>
 
      <div class="nav-list">
        <div class="nav-item" onclick="showSection('secConfig')">
          <svg class="nicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
          Configuration
          <svg class="narrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </div>
        <div class="nav-item" onclick="showSection('secSetup')">
          <svg class="nicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Proxy Setup
          <svg class="narrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </div>
      </div>
    </div>
 
    <!-- SEC: Config -->
    <div class="sec" id="secConfig">
      <div class="back" onclick="showSection('secHome')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        Back
      </div>
 
      <div class="glass">
        <div class="sec-label">Augment Tier</div>
        <div id="augList"></div>
        <div style="margin-top:12px">
          <button class="btn btn-pri btn-w" onclick="onSaveAugment()">Save Configuration</button>
        </div>
      </div>
    </div>
 
  </div>
</div>
 
<div class="toast" id="toast"></div>
 
<script>
var _selectedAug = null;
var _proxyOn = false;
 
/* â”€â”€ Toast â”€â”€ */
function showToast(msg, type) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + (type||'') + ' show';
  setTimeout(function(){ t.classList.remove('show'); }, 3200);
}
 
/* â”€â”€ Section nav â”€â”€ */
function showSection(id) {
  var all = document.querySelectorAll('.sec');
  for (var i=0;i<all.length;i++) all[i].classList.remove('active');
  document.getElementById(id).classList.add('active');
  if (id==='secHome') refreshHome();
  if (id==='secSetup') initSetup();
  if (id==='secConfig') buildAugList();
}
 
/* â”€â”€ Proxy toggle â”€â”€ */
function updateProxyUI(on) {
  _proxyOn = on;
  var dot = document.getElementById('proxyDot');
  var pill = document.getElementById('proxyPill');
  var label = document.getElementById('proxyLabel');
  if (on) { dot.classList.add('active'); pill.classList.add('on'); label.textContent='ON'; }
  else    { dot.classList.remove('active'); pill.classList.remove('on'); label.textContent='OFF'; }
}
 
async function onToggleProxy() {
  var res = await pywebview.api.toggle_proxy();
  if (res.ok !== undefined) {
    var running = await pywebview.api.is_proxy_running();
    updateProxyUI(running);
    showToast(running ? 'Proxy started':'Proxy stopped', running ? 'success':'');
  }
  if (res.error) showToast(res.error, 'error');
}
 
/* â”€â”€ Setup flow â”€â”€ */
async function initSetup() {
  var installed = await pywebview.api.check_mitmproxy_installed();
  var se = document.getElementById('mitmStatus');
  var ae = document.getElementById('mitmAction');
  var s1 = document.getElementById('stepNum1');
  if (installed) {
    se.textContent='mitmproxy is installed.';
    s1.classList.add('done'); s1.textContent='\u2713';
    ae.innerHTML='<span class="badge badge-ok">Installed</span>';
    document.getElementById('btnStartProxy').disabled=false;
  } else {
    se.textContent='mitmproxy not found. Install to continue.';
    var has = await pywebview.api.get_installer_path();
    if (has) ae.innerHTML='<button class="btn btn-pri" onclick="onInstallMitm()">Install mitmproxy</button>';
    else ae.innerHTML='<span class="badge badge-err">Place installer next to app</span>';
  }
  var cd = (await pywebview.api.get_config()).cert_done;
  if (cd) { document.getElementById('stepNum3').classList.add('done'); document.getElementById('stepNum3').textContent='\u2713'; }
}
 
async function onInstallMitm() {
  var ok = await pywebview.api.launch_installer();
  if (ok) { showToast('Installer launched','success'); setTimeout(async function(){ if(await pywebview.api.check_mitmproxy_installed()) initSetup(); },5000); }
  else showToast('Could not launch installer','error');
}
 
async function onStartProxy() {
  var b = document.getElementById('btnStartProxy');
  b.disabled=true; b.innerHTML='<span class="spin"></span> Starting';
  var res = await pywebview.api.start_proxy();
  if (res.ok) {
    updateProxyUI(true);
    document.getElementById('stepNum2').classList.add('done');
    document.getElementById('stepNum2').textContent='\u2713';
    b.textContent='Running'; b.disabled=true;
    document.getElementById('btnCert').disabled=false;
    document.getElementById('btnCertDone').disabled=false;
    showToast('Proxy on port '+res.port,'success');
  } else { b.disabled=false; b.textContent='Start Proxy'; showToast(res.error||'Start failed','error'); }
}
 
async function onOpenCert() {
  var e = await pywebview.api.is_cert_exists();
  if (!e) { showToast('Cert not generated yet','error'); return; }
  var ok = await pywebview.api.open_cert();
  if (ok) showToast('Certificate wizard opened','success');
  else showToast('Certificate not found','error');
}
 
async function onCertDone() {
  await pywebview.api.mark_cert_done();
  document.getElementById('stepNum3').classList.add('done');
  document.getElementById('stepNum3').textContent='\u2713';
  showToast('Setup complete','success');
  setTimeout(function(){ showSection('secHome'); },800);
}
 
/* â”€â”€ Home â”€â”€ */
async function refreshHome() {
  var ht = await pywebview.api.has_token();
  var cf = await pywebview.api.is_configured();
  var cfg = await pywebview.api.get_config();
  var tb = document.getElementById('tokenBadge');
  tb.className = 'badge '+(ht?'badge-ok':'badge-warn');
  tb.textContent = ht?'TOKEN CAPTURED':'NO TOKEN';
  var ab = document.getElementById('augBadge');
  ab.className = 'badge '+(cf?'badge-ok':'badge-warn');
  ab.textContent = cf?(cfg.augment||'CONFIGURED'):'NOT CONFIGURED';
  document.getElementById('btnSecret').disabled=!(ht&&cf);
  document.getElementById('btnRefresh').disabled=!ht;
  document.getElementById('btnTest').disabled=!ht;
  document.getElementById('btnSuperRefresh').disabled=!ht;
}
 
async function onDetectToken() {
  var b = document.getElementById('btnDetectToken');
  if (!b) return;
  b.disabled = true;
  b.innerHTML = '<span class="spin"></span> Detecting';
  var res = await pywebview.api.detect_latest_token();
  b.disabled = false;
  b.textContent = 'Detect Token';
 
  var tb = document.getElementById('tokenBadge');
  if (tb) {
    if (res.ok) {
      tb.className = 'badge badge-ok';
      tb.textContent = 'TOKEN READY';
    } else if (res.found) {
      tb.className = 'badge badge-warn';
      tb.textContent = res.expired ? 'TOKEN EXPIRED' : 'TOKEN CAPTURED';
    } else {
      tb.className = 'badge badge-warn';
      tb.textContent = 'NO TOKEN';
    }
  }
 
  if (res.ok) {
    showToast(res.message || 'Latest token is valid', 'success');
  } else {
    showToast(res.error || 'Token detection failed', 'error');
  }
 
  var ht = !!res.ok;
  document.getElementById('btnRefresh').disabled=!ht;
  document.getElementById('btnTest').disabled=!ht;
  document.getElementById('btnSuperRefresh').disabled=!ht;
}
 
/* â”€â”€ Config â”€â”€ */
async function buildAugList() {
  var augs = await pywebview.api.get_augment_list();
  var cfg = await pywebview.api.get_config();
  _selectedAug = cfg.augment||null;
  var c = document.getElementById('augList');
  c.innerHTML='';
  var t={"NO MK":{"backpack":-900626342,"quickuse":-1657530589,"safepocket":742274453},"Looting Mk1":{"backpack":202906145,"quickuse":1454995512,"safepocket":634916076},"Looting Mk2":{"backpack":1757735240,"quickuse":838324696,"safepocket":-2105475031,"augment":-36502079},"Looting Mk3 - Cautious":{"backpack":-835379180,"quickuse":-25855644,"safepocket":1196619436},"Looting Mk3 - Survivor":{"backpack":1450686663,"quickuse":-890187561,"safepocket":-2004748456}};
  for (var i=0;i<augs.length;i++) {
    var n=augs[i], g=t[n]||{};
    var el=document.createElement('div');
    el.className='aug'+(n===_selectedAug?' sel':'');
    el.setAttribute('data-aug',n);
    el.onclick=(function(x){return function(){selectAug(x);};})(n);
    el.innerHTML='<div class="aug-radio"></div><div><div class="aug-name">'+esc(n)+'</div><div class="aug-sub">BP '+(g.backpack||'?')+'  QU '+(g.quickuse||'?')+'  SP '+(g.safepocket||'?')+'</div></div>';
    c.appendChild(el);
  }
}
 
function selectAug(name) {
  _selectedAug=name;
  document.querySelectorAll('.aug').forEach(function(el){ el.classList.toggle('sel',el.getAttribute('data-aug')===name); });
}
 
async function onSaveAugment() {
  if (!_selectedAug) { showToast('Select an augment','error'); return; }
  var res = await pywebview.api.save_augment(_selectedAug);
  if (res.ok) { showToast('Saved: '+_selectedAug,'success'); setTimeout(function(){showSection('secHome');},600); }
  else showToast(res.error||'Save failed','error');
}
 
/* â”€â”€ HOTKEY â”€â”€ */
var _hotkeyCombo = '';
function openHotkeyModal() {
  var ov = document.createElement('div');
  ov.className = 'hotkey-overlay';
  ov.id = 'hotkeyOverlay';
  ov.innerHTML = '<div class="hotkey-modal"><h3>SET HOTKEY</h3><p>Press any key combo (e.g. Ctrl+Shift+F)</p><div class="hk-display" id="hkDisplay">...</div><div class="hk-hint">ESC to cancel â€¢ ENTER to confirm</div></div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function(e){ if(e.target===ov) closeHotkeyModal(false); });
  document.addEventListener('keydown', hotkeyCapture, true);
}
function hotkeyCapture(e) {
  e.preventDefault(); e.stopPropagation();
  if (e.key === 'Escape') { closeHotkeyModal(false); return; }
  if (e.key === 'Enter' && _hotkeyCombo) { closeHotkeyModal(true); return; }
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.length === 0) return;
  _hotkeyCombo = parts.join('+');
  var d = document.getElementById('hkDisplay');
  if (d) d.textContent = _hotkeyCombo;
}
async function closeHotkeyModal(save) {
  document.removeEventListener('keydown', hotkeyCapture, true);
  var ov = document.getElementById('hotkeyOverlay');
  if (ov) ov.remove();
  if (save && _hotkeyCombo) {
    await pywebview.api.save_hotkey(_hotkeyCombo);
    document.getElementById('hkLabel').textContent = _hotkeyCombo;
    showToast('Hotkey set: ' + _hotkeyCombo, 'success');
    installHotkeyListener();
  }
}
function installHotkeyListener() {
  document.removeEventListener('keydown', globalHotkeyHandler, true);
  if (_hotkeyCombo) document.addEventListener('keydown', globalHotkeyHandler, true);
}
function globalHotkeyHandler(e) {
  if (!_hotkeyCombo) return;
  if (document.getElementById('hotkeyOverlay')) return;
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.join('+') === _hotkeyCombo) {
    e.preventDefault(); e.stopPropagation();
    var b = document.getElementById('btnSecret');
    if (b && !b.disabled) onSecret();
  }
}
 
/* â”€â”€ REFRESH â”€â”€ */
async function onRefresh() {
  var b=document.getElementById('btnRefresh');
  b.disabled=true;
  b.innerHTML='<span class="rtxt"><span class="spin"></span> REFRESHING</span>';
  var res = await pywebview.api.execute_refresh();
  if (res.ok) {
    b.innerHTML='<span class="rtxt">\u2713 '+res.refreshed+' REFRESHED</span>';
    showToast('Refreshed '+res.refreshed+' items \u2014 tap for details','success');
    showRefreshDetails(res.details || [], res.refreshed);
  } else {
    b.innerHTML='<span class="rtxt">REFRESH</span>';
    var msg = (res.error||'Failed')+(res.detail?' \u2014 '+res.detail:'');
    if (res.partial) msg += ' ('+res.partial+' partial)';
    showToast(msg,'error');
    if (res.details && res.details.length) showRefreshDetails(res.details, res.partial||0);
  }
  setTimeout(function(){ b.innerHTML='<span class="rtxt">REFRESH</span>'; b.disabled=false; refreshHome(); },5000);
}
 
function showRefreshDetails(details, total) {
  var old = document.getElementById('detailsOverlay');
  if (old) old.remove();
  var ov = document.createElement('div');
  ov.className = 'details-overlay'; ov.id = 'detailsOverlay';
  var html = '<div class="details-panel">';
  html += '<h3>\u2713 LOADOUT REFRESHED</h3>';
  html += '<div class="dp-sub">'+total+' item'+(total!==1?'s':'')+' refreshed</div>';
  html += '<ul class="details-list">';
  for (var i=0; i<details.length; i++) {
    var d = details[i];
    html += '<li>';
    html += '<span class="dl-name">'+ esc(d.name) +'</span>';
    html += '<span class="dl-ids">'+ d.old +'\u2026 \u2192 '+ d['new'] +'\u2026</span>';
    html += '</li>';
  }
  html += '</ul>';
  html += '<button class="details-close" onclick="closeDetails()">Close</button>';
  html += '</div>';
  ov.innerHTML = html;
  ov.addEventListener('click', function(e){ if(e.target===ov) closeDetails(); });
  document.body.appendChild(ov);
}
function closeDetails() {
  var ov = document.getElementById('detailsOverlay');
  if (ov) ov.remove();
}
 
/* â”€â”€ TEST â”€â”€ */
async function onTest() {
  var b=document.getElementById('btnTest');
  b.disabled=true;
  b.innerHTML='<span class="ttxt"><span class="spin"></span> TESTING</span>';
  var res = await pywebview.api.execute_test();
  if (res.ok) {
    b.innerHTML='<span class="ttxt">\u2713 '+res.refreshed+' REFRESHED</span>';
    showToast('Test: '+res.refreshed+' items refreshed','success');
    showRefreshDetails(res.details || [], res.refreshed);
  } else {
    b.innerHTML='<span class="ttxt">TEST</span>';
    var msg = (res.error||'Failed')+(res.detail?' \u2014 '+res.detail:'');
    if (res.partial) msg += ' ('+res.partial+' partial)';
    showToast(msg,'error');
    if (res.details && res.details.length) showRefreshDetails(res.details, res.partial||0);
  }
  setTimeout(function(){ b.innerHTML='<span class="ttxt">TEST</span>'; b.disabled=false; refreshHome(); },5000);
}
 
/* â”€â”€ TEST HOTKEY â”€â”€ */
var _testHotkeyCombo = '';
function openTestHotkeyModal() {
  var ov = document.createElement('div');
  ov.className = 'hotkey-overlay';
  ov.id = 'testHotkeyOverlay';
  ov.innerHTML = '<div class="hotkey-modal"><h3>SET TEST HOTKEY</h3><p>Press any key combo (e.g. Ctrl+Shift+T)</p><div class="hk-display" id="testHkDisplay">...</div><div class="hk-hint">ESC to cancel \u2022 ENTER to confirm</div></div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function(e){ if(e.target===ov) closeTestHotkeyModal(false); });
  document.addEventListener('keydown', testHotkeyCapture, true);
}
function testHotkeyCapture(e) {
  e.preventDefault(); e.stopPropagation();
  if (e.key === 'Escape') { closeTestHotkeyModal(false); return; }
  if (e.key === 'Enter' && _testHotkeyCombo) { closeTestHotkeyModal(true); return; }
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.length === 0) return;
  _testHotkeyCombo = parts.join('+');
  var d = document.getElementById('testHkDisplay');
  if (d) d.textContent = _testHotkeyCombo;
}
async function closeTestHotkeyModal(save) {
  document.removeEventListener('keydown', testHotkeyCapture, true);
  var ov = document.getElementById('testHotkeyOverlay');
  if (ov) ov.remove();
  if (save && _testHotkeyCombo) {
    await pywebview.api.save_test_hotkey(_testHotkeyCombo);
    document.getElementById('testHkLabel').textContent = _testHotkeyCombo;
    showToast('Test hotkey set: ' + _testHotkeyCombo, 'success');
    installTestHotkeyListener();
  }
}
function installTestHotkeyListener() {
  document.removeEventListener('keydown', globalTestHotkeyHandler, true);
  if (_testHotkeyCombo) document.addEventListener('keydown', globalTestHotkeyHandler, true);
}
function globalTestHotkeyHandler(e) {
  if (!_testHotkeyCombo) return;
  if (document.getElementById('hotkeyOverlay') || document.getElementById('refreshHotkeyOverlay') || document.getElementById('testHotkeyOverlay') || document.getElementById('superRefreshHotkeyOverlay')) return;
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.join('+') === _testHotkeyCombo) {
    e.preventDefault(); e.stopPropagation();
    var b = document.getElementById('btnTest');
    if (b && !b.disabled) onTest();
  }
}
 
/* â”€â”€ SUPER REFRESH â”€â”€ */
async function onSuperRefresh() {
  var b=document.getElementById('btnSuperRefresh');
  b.disabled=true;
  b.innerHTML='<span class="srtxt"><span class="spin"></span> REFRESHING STASH</span>';
  var res = await pywebview.api.execute_super_refresh();
  if (res.ok) {
    b.innerHTML='<span class="srtxt">\u2713 '+res.refreshed+' REFRESHED</span>';
    showToast('Super Refresh: '+res.refreshed+' stash items refreshed','success');
    showRefreshDetails(res.details || [], res.refreshed);
  } else {
    b.innerHTML='<span class="srtxt">SUPER REFRESH</span>';
    var msg = (res.error||'Failed')+(res.detail?' \u2014 '+res.detail:'');
    if (res.partial) msg += ' ('+res.partial+' partial)';
    showToast(msg,'error');
    if (res.details && res.details.length) showRefreshDetails(res.details, res.partial||0);
  }
  setTimeout(function(){ b.innerHTML='<span class="srtxt">SUPER REFRESH</span>'; b.disabled=false; refreshHome(); },5000);
}
 
/* â”€â”€ SUPER REFRESH HOTKEY â”€â”€ */
var _superRefreshHotkeyCombo = '';
function openSuperRefreshHotkeyModal() {
  var ov = document.createElement('div');
  ov.className = 'hotkey-overlay';
  ov.id = 'superRefreshHotkeyOverlay';
  ov.innerHTML = '<div class="hotkey-modal"><h3>SET SUPER REFRESH HOTKEY</h3><p>Press any key combo (e.g. Ctrl+Shift+S)</p><div class="hk-display" id="superRefreshHkDisplay">...</div><div class="hk-hint">ESC to cancel \u2022 ENTER to confirm</div></div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function(e){ if(e.target===ov) closeSuperRefreshHotkeyModal(false); });
  document.addEventListener('keydown', superRefreshHotkeyCapture, true);
}
function superRefreshHotkeyCapture(e) {
  e.preventDefault(); e.stopPropagation();
  if (e.key === 'Escape') { closeSuperRefreshHotkeyModal(false); return; }
  if (e.key === 'Enter' && _superRefreshHotkeyCombo) { closeSuperRefreshHotkeyModal(true); return; }
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.length === 0) return;
  _superRefreshHotkeyCombo = parts.join('+');
  var d = document.getElementById('superRefreshHkDisplay');
  if (d) d.textContent = _superRefreshHotkeyCombo;
}
async function closeSuperRefreshHotkeyModal(save) {
  document.removeEventListener('keydown', superRefreshHotkeyCapture, true);
  var ov = document.getElementById('superRefreshHotkeyOverlay');
  if (ov) ov.remove();
  if (save && _superRefreshHotkeyCombo) {
    await pywebview.api.save_super_refresh_hotkey(_superRefreshHotkeyCombo);
    document.getElementById('superRefreshHkLabel').textContent = _superRefreshHotkeyCombo;
    showToast('Super Refresh hotkey set: ' + _superRefreshHotkeyCombo, 'success');
    installSuperRefreshHotkeyListener();
  }
}
function installSuperRefreshHotkeyListener() {
  document.removeEventListener('keydown', globalSuperRefreshHotkeyHandler, true);
  if (_superRefreshHotkeyCombo) document.addEventListener('keydown', globalSuperRefreshHotkeyHandler, true);
}
function globalSuperRefreshHotkeyHandler(e) {
  if (!_superRefreshHotkeyCombo) return;
  if (document.getElementById('hotkeyOverlay') || document.getElementById('refreshHotkeyOverlay') || document.getElementById('superRefreshHotkeyOverlay')) return;
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.join('+') === _superRefreshHotkeyCombo) {
    e.preventDefault(); e.stopPropagation();
    var b = document.getElementById('btnSuperRefresh');
    if (b && !b.disabled) onSuperRefresh();
  }
}
 
/* â”€â”€ REFRESH HOTKEY â”€â”€ */
var _refreshHotkeyCombo = '';
function openRefreshHotkeyModal() {
  var ov = document.createElement('div');
  ov.className = 'hotkey-overlay';
  ov.id = 'refreshHotkeyOverlay';
  ov.innerHTML = '<div class="hotkey-modal"><h3>SET REFRESH HOTKEY</h3><p>Press any key combo (e.g. Ctrl+Shift+R)</p><div class="hk-display" id="refreshHkDisplay">...</div><div class="hk-hint">ESC to cancel \u2022 ENTER to confirm</div></div>';
  document.body.appendChild(ov);
  ov.addEventListener('click', function(e){ if(e.target===ov) closeRefreshHotkeyModal(false); });
  document.addEventListener('keydown', refreshHotkeyCapture, true);
}
function refreshHotkeyCapture(e) {
  e.preventDefault(); e.stopPropagation();
  if (e.key === 'Escape') { closeRefreshHotkeyModal(false); return; }
  if (e.key === 'Enter' && _refreshHotkeyCombo) { closeRefreshHotkeyModal(true); return; }
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.length === 0) return;
  _refreshHotkeyCombo = parts.join('+');
  var d = document.getElementById('refreshHkDisplay');
  if (d) d.textContent = _refreshHotkeyCombo;
}
async function closeRefreshHotkeyModal(save) {
  document.removeEventListener('keydown', refreshHotkeyCapture, true);
  var ov = document.getElementById('refreshHotkeyOverlay');
  if (ov) ov.remove();
  if (save && _refreshHotkeyCombo) {
    await pywebview.api.save_refresh_hotkey(_refreshHotkeyCombo);
    document.getElementById('refreshHkLabel').textContent = _refreshHotkeyCombo;
    showToast('Refresh hotkey set: ' + _refreshHotkeyCombo, 'success');
    installRefreshHotkeyListener();
  }
}
function installRefreshHotkeyListener() {
  document.removeEventListener('keydown', globalRefreshHotkeyHandler, true);
  if (_refreshHotkeyCombo) document.addEventListener('keydown', globalRefreshHotkeyHandler, true);
}
function globalRefreshHotkeyHandler(e) {
  if (!_refreshHotkeyCombo) return;
  if (document.getElementById('hotkeyOverlay') || document.getElementById('refreshHotkeyOverlay')) return;
  var parts = [];
  if (e.ctrlKey) parts.push('Ctrl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');
  var k = e.key;
  if (['Control','Alt','Shift','Meta'].indexOf(k) === -1) {
    parts.push(k.length===1 ? k.toUpperCase() : k);
  }
  if (parts.join('+') === _refreshHotkeyCombo) {
    e.preventDefault(); e.stopPropagation();
    var b = document.getElementById('btnRefresh');
    if (b && !b.disabled) onRefresh();
  }
}
 
/* â”€â”€ SECRET â”€â”€ */
async function onSecret() {
  var b=document.getElementById('btnSecret');
  b.disabled=true;
  b.innerHTML='<span class="stxt"><span class="spin"></span> EXECUTING</span>';
  var res = await pywebview.api.execute_secret();
  if (res.ok) {
    b.innerHTML='<span class="stxt">\u2713 '+res.moved+' ITEMS MOVED</span>';
    showToast('Overstashed '+res.moved+' items','success');
  } else {
    b.innerHTML='<span class="stxt">SECRET</span>';
    showToast((res.error||'Failed')+(res.detail?' â€” '+res.detail:''),'error');
  }
  setTimeout(function(){ b.innerHTML='<span class="stxt">SECRET</span>'; b.disabled=false; refreshHome(); },3000);
}
 
function esc(s){ var d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
 
/* â”€â”€ Dragbar window drag â”€â”€ */
function initDrag() {
  var bar = document.querySelector('.dragbar');
  var dragging = false, sx, sy;
  bar.addEventListener('mousedown', function(e){
    if (e.target.closest('.drag-controls')) return;
    dragging = true; sx = e.screenX; sy = e.screenY;
    e.preventDefault();
  });
  document.addEventListener('mousemove', function(e){
    if (!dragging) return;
    var dx = e.screenX - sx, dy = e.screenY - sy;
    sx = e.screenX; sy = e.screenY;
    pywebview.api.move_window(dx, dy);
  });
  document.addEventListener('mouseup', function(){ dragging = false; });
}
 
/* â”€â”€ Init â”€â”€ */
window.addEventListener('pywebviewready', async function() {
  initDrag();
  var sd = await pywebview.api.is_setup_done();
  updateProxyUI(await pywebview.api.is_proxy_running());
  var hk = await pywebview.api.get_hotkey();
  if (hk) {
    _hotkeyCombo = hk;
    document.getElementById('hkLabel').textContent = hk;
    installHotkeyListener();
  }
  var rhk = await pywebview.api.get_refresh_hotkey();
  if (rhk) {
    _refreshHotkeyCombo = rhk;
    document.getElementById('refreshHkLabel').textContent = rhk;
    installRefreshHotkeyListener();
  }
  var srhk = await pywebview.api.get_super_refresh_hotkey();
  if (srhk) {
    _superRefreshHotkeyCombo = srhk;
    document.getElementById('superRefreshHkLabel').textContent = srhk;
    installSuperRefreshHotkeyListener();
  }
  var thk = await pywebview.api.get_test_hotkey();
  if (thk) {
    _testHotkeyCombo = thk;
    document.getElementById('testHkLabel').textContent = thk;
    installTestHotkeyListener();
  }
  if (sd) showSection('secHome');
  else { showSection('secSetup'); }
});
</script>
</body>
</html>
"""
 
 
# â”€â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def main():
    api = Api()
    window = webview.create_window(
        'OneMore',
        html=HTML,
        width=520,
        height=760,
        resizable=True,
        frameless=True,
        easy_drag=False,
        js_api=api,
        background_color='#080810',
    )
    api._window = window
 
    def on_loaded():
        # Register all global hotkeys on startup
        api._register_all_hotkeys()
 
    def on_closing():
        try:
            _kb.unhook_all_hotkeys()
        except Exception:
            pass
        api.shutdown()
 
    window.events.loaded += on_loaded
    window.events.closing += on_closing
 
    webview.start(debug=False)
 
 
if __name__ == '__main__':
    main()