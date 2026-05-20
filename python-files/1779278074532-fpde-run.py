# -*- coding: utf-8 -*-
import sys, os, json, urllib.request, urllib.parse, datetime, secrets, socket, csv, io, asyncio, smtplib, ssl, hashlib, random, time, shutil
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException, Header, Depends, Request, UploadFile, File, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# ================= 基础配置 =================
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "system.db")

app = FastAPI(title="音符游戏+后台管理")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ADMIN_PASSWORD = "Red Johnny"
sessions = {}
UPLOAD_DIR = os.path.join(BASE_DIR, "version_updates")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

SMTP_HOST = "smtp.qq.com"; SMTP_PORT = 465
SMTP_USER = "255519175@qq.com"; SMTP_PASS = "wngqnkyasmsxbhdd"
verification_codes = {}
chat_clients = []

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

def send_email_code(email: str, code: str) -> bool:
    try:
        msg = MIMEText(f"【音符游戏】验证码：{code}，5分钟有效。", "plain", "utf-8")
        msg["Subject"] = "验证码"; msg["From"] = SMTP_USER; msg["To"] = email
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context()) as server:
            server.login(SMTP_USER, SMTP_PASS); server.sendmail(SMTP_USER, [email], msg.as_string())
        return True
    except Exception as e: print(f"❌ 邮件发送失败: {e}"); return False

def hash_password(p, s): return hashlib.sha256((p+s).encode()).hexdigest()

def get_music_files() -> List[dict]:
    if not os.path.exists(MUSIC_DIR): return []
    return sorted([{"id": hashlib.md5(f.encode()).hexdigest()[:8], "name": os.path.splitext(f)[0], "filename": f, "url": f"/static/{MUSIC_DIR}/{f}", "size": os.path.getsize(os.path.join(MUSIC_DIR, f))//1024} for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3','.wav','.ogg','.flac'))], key=lambda x: x["name"])

def init_db():
    import sqlite3
    print(f"🔍 数据库路径: {DB}")
    if os.path.exists(DB):
        try: conn=sqlite3.connect(DB,timeout=1); conn.execute("SELECT 1"); conn.close()
        except: print("⚠️ 清理损坏数据库..."); os.remove(DB)
    conn=sqlite3.connect(DB,timeout=10); c=conn.cursor(); c.execute("PRAGMA journal_mode=WAL;")
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS music_prefs (user_email TEXT PRIMARY KEY, selected_music_id TEXT, volume REAL DEFAULT 0.7)''')
    conn.commit(); conn.close(); print("✅ 数据库初始化完成")

def get_db():
    import sqlite3; conn=sqlite3.connect(DB,timeout=10); conn.row_factory=sqlite3.Row; return conn

class LoginReq(BaseModel): password: str
class AuthEmailReq(BaseModel): email: str
class AuthRegisterReq(BaseModel): email: str; code: str; password: str
class AuthLoginReq(BaseModel): email: str; password: str
class MusicPrefReq(BaseModel): music_id: Optional[str] = None; volume: Optional[float] = None

def verify_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "未授权")
    token = authorization.split(" ", 1)[1]
    if token not in sessions: raise HTTPException(401, "会话已过期")
    return True

# ================= API 路由 =================
@app.post("/api/auth/send-code")
def send_code(req: AuthEmailReq):
    if not req.email.endswith("@qq.com") or not req.email.replace("@qq.com","").isdigit(): raise HTTPException(400, "仅支持QQ邮箱")
    code="".join([str(random.randint(0,9)) for _ in range(6)]); verification_codes[req.email]={"code":code,"expires":time.time()+300}
    if not send_email_code(req.email, code): raise HTTPException(500, "发送失败")
    return {"message":"已发送"}

@app.post("/api/auth/register")
def register(req: AuthRegisterReq):
    stored=verification_codes.get(req.email)
    if not stored or stored["expires"]<time.time() or stored["code"]!=req.code: raise HTTPException(400,"验证码错误")
    if len(req.password)<6: raise HTTPException(400,"密码至少6位")
    conn=get_db()
    try:
        if conn.execute("SELECT id FROM users WHERE email=?",(req.email,)).fetchone(): raise HTTPException(400,"已注册")
        conn.execute("INSERT INTO users(email,password_hash) VALUES(?,?)",(req.email,hash_password(req.password,req.email))); conn.commit()
        token=secrets.token_hex(16); sessions[token]=req.email; del verification_codes[req.email]
        return {"token":token,"message":"注册成功"}
    finally: conn.close()

@app.post("/api/auth/login")
def login(req: AuthLoginReq):
    conn=get_db()
    try:
        row=conn.execute("SELECT password_hash FROM users WHERE email=?",(req.email,)).fetchone()
        if not row or row["password_hash"]!=hash_password(req.password,req.email): raise HTTPException(400,"账号或密码错误")
        token=secrets.token_hex(16); sessions[token]=req.email; return {"token":token,"message":"登录成功"}
    finally: conn.close()

@app.post("/api/admin/login")
def admin_login(req: LoginReq):
    if req.password==ADMIN_PASSWORD:
        token=secrets.token_hex(16); sessions[token]="admin"; print(f"✅ 后台登录成功"); return {"token":token,"message":"登录成功"}
    raise HTTPException(401,"密码错误")

@app.get("/api/admin/users")
def get_users(_:bool=Depends(verify_admin)):
    conn=get_db()
    try: return {"users":[{"id":r[0],"email":r[1],"created_at":r[2]} for r in conn.execute("SELECT id,email,created_at FROM users ORDER BY id DESC").fetchall()]}
    finally: conn.close()

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id:int, _:bool=Depends(verify_admin)):
    conn=get_db()
    try: conn.execute("DELETE FROM users WHERE id=?",(user_id,)); conn.commit()
    finally: conn.close()
    return {"message":"已删除"}

@app.get("/api/music/list")
def list_music(_:bool=Depends(verify_admin)): return {"music":get_music_files()}

@app.post("/api/music/upload")
async def upload_music(file:UploadFile=File(...), _:bool=Depends(verify_admin)):
    if not file.filename: raise HTTPException(400,"未选择文件")
    safe="".join(c for c in file.filename if c.isalnum() or c in '._- ')
    if not safe.lower().endswith(('.mp3','.wav','.ogg','.flac')): raise HTTPException(400,"仅支持音频")
    with open(os.path.join(MUSIC_DIR,safe),"wb") as f: shutil.copyfileobj(file.file,f)
    return {"message":f"上传成功：{safe}"}

@app.delete("/api/music/{filename}")
def delete_music(filename:str, _:bool=Depends(verify_admin)):
    p=os.path.join(MUSIC_DIR,os.path.basename(filename))
    if os.path.exists(p): os.remove(p); return {"message":"删除成功"}
    raise HTTPException(404,"文件不存在")

@app.get("/api/music/pref")
def get_music_pref(email:str=Query(...)):
    conn=get_db()
    try:
        row=conn.execute("SELECT selected_music_id,volume FROM music_prefs WHERE user_email=?",(email,)).fetchone()
        return {"music_id":row["selected_music_id"] if row else None, "volume":row["volume"] if row else 0.7}
    finally: conn.close()

@app.post("/api/music/pref")
def set_music_pref(req:MusicPrefReq, email:str=Query(...)):
    conn=get_db()
    try:
        if req.music_id: conn.execute("INSERT OR REPLACE INTO music_prefs(user_email,selected_music_id) VALUES(?,?)",(email,req.music_id))
        if req.volume is not None: conn.execute("INSERT OR REPLACE INTO music_prefs(user_email,volume) VALUES(?,?)",(email,req.volume))
        conn.commit(); return {"message":"保存成功"}
    finally: conn.close()

# ================= WebSocket (仅聊天室) =================
@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_clients.append(websocket)
    sender = "匿名"
    try:
        auth = await websocket.receive_json()
        if auth.get("type") == "auth": sender = auth.get("name", "玩家")
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "chat":
                content = data.get("content", "").strip()
                if not content: continue
                for word in ["垃圾", "傻逼"]: content = content.replace(word, "***")
                msg = {"type": "chat", "sender": sender, "content": content, "time": datetime.datetime.now().strftime("%H:%M")}
                for client in chat_clients[:]:
                    try: await client.send_json(msg)
                    except: chat_clients.remove(client)
    except WebSocketDisconnect:
        if websocket in chat_clients: chat_clients.remove(websocket)

# ================= 前端页面 =================
def html_resp(content:str): return HTMLResponse(content=content, headers={"Cache-Control":"no-cache"})

GAME_PAGE = r"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><title>音符游戏</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0f0f1a;color:#fff;font-family:'Microsoft YaHei',sans-serif;overflow:hidden}
#auth-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,15,26,0.98);z-index:9000;display:flex;justify-content:center;align-items:center}
.auth-box{background:#16213e;padding:40px;border-radius:15px;width:350px;text-align:center}
.auth-box h2{color:#4ecdc4;margin-bottom:25px}
.auth-input{width:100%;padding:12px;margin:10px 0;background:#0f0f1a;border:1px solid #333;color:#fff;border-radius:8px;font-size:14px}
.auth-btn{width:100%;padding:12px;background:#e94560;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:16px;margin-top:15px}
.auth-btn:hover{background:#c13651}
#msg{font-size:12px;margin-top:15px;color:#888;min-height:18px}
#menu-screen{display:flex;flex-direction:column;align-items:center;padding-top:60px}
#menu-screen h1{color:#4ecdc4;margin-bottom:30px;text-shadow:0 0 20px rgba(78,205,196,0.5)}
.level-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:25px;width:90%;max-width:900px}
.l-card{background:#16213e;padding:30px;border-radius:15px;text-align:center;cursor:pointer;border:2px solid #333;transition:all 0.3s}
.l-card:hover{border-color:#4ecdc4;transform:translateY(-8px)}
.l-card h3{color:#4ecdc4;margin-bottom:10px}
.l-card p{color:#888;font-size:13px}
#game{position:relative;width:400px;height:100vh;margin:0 auto;border-left:1px solid #333;border-right:1px solid #333;background:rgba(255,255,255,0.02)}
.lane{position:absolute;width:25%;height:100%;border-right:1px solid #222}
.target{position:absolute;bottom:100px;left:0;right:0;height:60px;border-top:2px dashed #e94560;border-bottom:2px dashed #e94560;display:flex}
.t{flex:1;display:flex;justify-content:center;align-items:center;font-size:26px;color:#4ecdc4}
.t.active{background:rgba(233,69,96,0.6);color:#fff}
.note{position:absolute;width:25%;height:45px;background:#e94560;border-radius:10px}
.note.hit{background:#4ecdc4}
#hud{position:fixed;top:20px;left:20px;font-size:20px;z-index:50}
#timer{position:fixed;top:20px;right:20px;font-size:20px;z-index:50}
#chat-btn{position:fixed;bottom:20px;right:20px;width:55px;height:55px;background:#4ecdc4;border-radius:50%;display:flex;justify-content:center;align-items:center;cursor:pointer;z-index:200;font-size:26px;color:#000;box-shadow:0 5px 15px rgba(0,0,0,0.5)}
#chat-panel{position:fixed;right:-350px;top:0;width:320px;height:100%;background:#111;border-left:1px solid #333;z-index:150;transition:right 0.3s;display:flex;flex-direction:column}
#chat-panel.open{right:0}
#chat-msgs{flex:1;overflow-y:auto;padding:15px}
#chat-input-area{padding:15px;border-top:1px solid #333;display:flex}
#chat-input{flex:1;background:#222;border:none;color:#fff;padding:12px;border-radius:6px;outline:none}
.msg{margin-bottom:10px;padding:10px;border-radius:8px;font-size:14px;max-width:85%}
.msg.self{background:#4ecdc4;color:#000;margin-left:auto}
.msg.other{background:#222;color:#fff}
</style></head><body>
<div id="auth-overlay"><div class="auth-box">
  <h2>🔐 登录/注册</h2>
  <div id="login-form"><input class="auth-input" id="l-email" placeholder="QQ邮箱" type="email"><input class="auth-input" id="l-pwd" placeholder="密码" type="password"><button class="auth-btn" onclick="doLogin()">进入游戏</button></div>
  <div id="reg-form" style="display:none"><input class="auth-input" id="r-email" placeholder="QQ邮箱" type="email"><input class="auth-input" id="r-code" placeholder="验证码" maxlength="6"><button class="auth-btn" style="background:#333;margin:8px 0" onclick="sendCode()">获取验证码</button><input class="auth-input" id="r-pwd" placeholder="设置密码(至少6位)" type="password"><button class="auth-btn" onclick="doReg()">注册并进入</button></div>
  <div id="msg"></div>
  <p style="margin-top:15px;color:#4ecdc4;cursor:pointer;font-size:13px" onclick="toggleForm()">切换 登录/注册</p>
</div></div>
<div id="app-container" style="display:none">
  <div id="menu-screen"><h1>🎵 节奏大师</h1><div class="level-grid" id="lvl-grid"></div></div>
  <div id="game" style="display:none"><div class="lane"></div><div class="lane"></div><div class="lane"></div><div class="lane"></div><div class="target"><div class="t" data-k="d">D</div><div class="t" data-k="f">F</div><div class="t" data-k="j">J</div><div class="t" data-k="k">K</div></div></div>
  <div id="hud" style="display:none">得分：<span id="score">0</span> | 连击：<span id="combo">0</span></div>
  <div id="timer" style="display:none">剩余：<span id="time">0</span>s</div>
  <div id="chat-btn" onclick="toggleChat()">💬</div>
  <div id="chat-panel"><div style="padding:15px;border-bottom:1px solid #333;display:flex;justify-content:space-between"><span>💬 聊天室</span><span onclick="toggleChat()" style="cursor:pointer">✕</span></div><div id="chat-msgs"></div><div id="chat-input-area"><input type="text" id="chat-input" placeholder="输入消息..." maxlength="50"><button onclick="sendMsg()" style="background:#4ecdc4;border:none;padding:0 18px;border-radius:6px;margin-left:8px;cursor:pointer;color:#000">发送</button></div></div>
</div>
<script>
const LEVELS=[{id:1,name:"入门",dur:15,spd:4,rate:700},{id:2,name:"进阶",dur:20,spd:6,rate:500},{id:3,name:"大师",dur:25,spd:8,rate:350}];
let ws,userEmail,userToken,gameActive=false,notes=[],score=0,combo=0,animFrameId,spawnTimer,countDownTimer;
function showMsg(t,c='#888'){document.getElementById('msg').textContent=t;document.getElementById('msg').style.color=c}
function toggleForm(){document.getElementById('login-form').style.display=document.getElementById('login-form').style.display==='none'?'block':'none';document.getElementById('reg-form').style.display=document.getElementById('reg-form').style.display==='none'?'block':'none';showMsg('');}
async function doLogin(){const e=document.getElementById('l-email').value.trim(),p=document.getElementById('l-pwd').value;try{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p})});const d=await r.json();if(!r.ok)throw new Error(d.detail);userToken=d.token;userEmail=e.toLowerCase();connectWS();}catch(e){showMsg(e.message,'#ff6b6b')}}
async function doReg(){const e=document.getElementById('r-email').value.trim(),c=document.getElementById('r-code').value,p=document.getElementById('r-pwd').value;try{const r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,code:c,password:p})});const d=await r.json();if(!r.ok)throw new Error(d.detail);userToken=d.token;userEmail=e.toLowerCase();connectWS();}catch(e){showMsg(e.message,'#ff6b6b')}}
async function sendCode(){const e=document.getElementById('r-email').value.trim();try{await fetch('/api/auth/send-code',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e})});showMsg('✅ 验证码已发送','#4ecdc4');}catch(e){showMsg('发送失败','#ff6b6b')}}
function renderLevels(){const grid=document.getElementById('lvl-grid');grid.innerHTML='';LEVELS.forEach(lv=>{const div=document.createElement('div');div.className='l-card';div.innerHTML=`<h3>${lv.name}</h3><p>${lv.dur}秒 | 速度:${lv.spd}</p>`;div.onclick=()=>startGame(lv);grid.appendChild(div);});}
function connectWS(){document.getElementById('auth-overlay').style.display='none';document.getElementById('app-container').style.display='block';renderLevels();const proto=location.protocol==='https:'?'wss:':'ws:';ws=new WebSocket(proto+'//'+location.host+'/ws/chat');ws.onopen=()=>{console.log('🔌 聊天室已连接');ws.send(JSON.stringify({type:'auth',name:userEmail.split('@')[0]}));};ws.onmessage=e=>{const d=JSON.parse(e.data);if(d.type==='chat')addChatMsg(d.sender,d.content,d.sender===userEmail.split('@')[0]);};ws.onclose=()=>console.warn('🔌 聊天室已断开');}
function startGame(lv){score=0;combo=0;notes=[];gameActive=true;document.getElementById('menu-screen').style.display='none';document.getElementById('game').style.display='block';document.getElementById('hud').style.display='block';document.getElementById('timer').style.display='block';let t=lv.dur;document.getElementById('time').innerText=t;countDownTimer=setInterval(()=>{t--;document.getElementById('time').innerText=t;if(t<=0)endGame();},1000);spawnTimer=setInterval(()=>{if(gameActive)spawnNote(lv)},lv.rate);requestAnimationFrame(()=>gameLoop(lv));}
function spawnNote(lv){const lane=Math.floor(Math.random()*4);const n=document.createElement('div');n.className='note';n.style.left=(lane*25)+'%';n.style.top='-45px';n.dataset.lane=lane;document.getElementById('game').appendChild(n);notes.push(n);}
function gameLoop(lv){if(!gameActive)return;const hitY=document.getElementById('game').offsetHeight-100;for(let i=notes.length-1;i>=0;i--){let n=notes[i],y=parseFloat(n.style.top)+lv.spd;n.style.top=y+'px';if(y>hitY+60){n.remove();notes.splice(i,1);combo=0;updateHUD();}}animFrameId=requestAnimationFrame(()=>gameLoop(lv));}
document.addEventListener('keydown',e=>{if(!gameActive)return;const k=e.key.toLowerCase(),map={'d':0,'f':1,'j':2,'k':3};if(!(k in map))return;document.querySelector('.t[data-k="'+k+'"]').classList.add('active');setTimeout(()=>document.querySelector('.t[data-k="'+k+'"]').classList.remove('active'),100);const hitY=document.getElementById('game').offsetHeight-100;let hit=false;for(let i=notes.length-1;i>=0;i--){let n=notes[i];if(parseInt(n.dataset.lane)===map[k]&&Math.abs(parseFloat(n.style.top)-hitY)<65){score+=100+combo*10;combo++;n.classList.add('hit');hit=true;setTimeout(()=>{n.remove()},100);notes.splice(i,1);break;}}if(!hit)combo=0;updateHUD();});
function updateHUD(){document.getElementById('score').innerText=score;document.getElementById('combo').innerText=combo;}
function endGame(){gameActive=false;clearInterval(countDownTimer);clearInterval(spawnTimer);cancelAnimationFrame(animFrameId);document.getElementById('game').style.display='none';document.getElementById('hud').style.display='none';document.getElementById('timer').style.display='none';alert('游戏结束！得分：'+score+' | 连击：'+combo);location.reload();}
function sendMsg(){const input=document.getElementById('chat-input'),txt=input.value.trim();if(!txt||!ws||ws.readyState!==1)return;ws.send(JSON.stringify({type:'chat',content:txt}));input.value='';}
document.getElementById('chat-input').addEventListener('keydown',e=>{if(e.key==='Enter')sendMsg();});
function addChatMsg(user,text,isSelf){const div=document.createElement('div');div.className='msg '+(isSelf?'self':'other');div.innerText=user+': '+text;document.getElementById('chat-msgs').appendChild(div);document.getElementById('chat-msgs').scrollTop=100000;}
function toggleChat(){document.getElementById('chat-panel').classList.toggle('open');}
</script></body></html>"""

# 🛡️ 彻底重构的后台页面：状态与请求分离，杜绝闪退
ADMIN_PAGE = r"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><title>后台管理</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Microsoft YaHei',sans-serif;background:#f0f2f5;color:#333}
#login-box{position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;justify-content:center;align-items:center;z-index:9999}
.login-card{background:#fff;padding:50px;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:400px;text-align:center}
.login-card h2{color:#667eea;margin-bottom:30px;font-size:28px}
.login-input{width:100%;padding:15px;margin:15px 0;border:2px solid #e1e1e1;border-radius:8px;font-size:16px;outline:none}
.login-input:focus{border-color:#667eea}
.login-btn{width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;margin-top:20px}
.login-btn:disabled{opacity:0.6;cursor:not-allowed}
#login-msg{margin-top:15px;font-size:14px;min-height:20px}
#panel{display:none;padding:30px;max-width:1200px;margin:0 auto}
.header{background:#fff;padding:25px;border-radius:12px;margin-bottom:25px;box-shadow:0 2px 10px rgba(0,0,0,0.05);display:flex;justify-content:space-between;align-items:center}
.header h1{color:#667eea;font-size:26px}
.logout-btn{padding:10px 25px;background:#e74c3c;color:#fff;border:none;border-radius:6px;cursor:pointer}
.card{background:#fff;padding:30px;border-radius:12px;margin-bottom:25px;box-shadow:0 2px 10px rgba(0,0,0,0.05)}
.card h3{color:#667eea;margin-bottom:20px;font-size:20px;border-bottom:2px solid #f0f0f0;padding-bottom:12px}
table{width:100%;border-collapse:collapse}th,td{padding:14px;text-align:left;border-bottom:1px solid #f0f0f0}
th{background:#f8f9fa;color:#667eea;font-weight:600}
.action-btn{padding:6px 12px;background:#e74c3c;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px}
.upload-area{display:flex;gap:15px;margin-bottom:20px;align-items:center}
.upload-area input[type="file"]{flex:1;padding:12px;border:2px dashed #ddd;border-radius:8px}
.upload-btn{padding:12px 30px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer}
.music-item{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid #f0f0f0}
.empty-msg{text-align:center;color:#999;padding:30px}
</style></head><body>
<div id="login-box">
  <div class="login-card">
    <h2>🔐 后台管理</h2>
    <input type="password" id="pwd" class="login-input" placeholder="请输入管理员密码" onkeydown="if(event.key==='Enter')doLogin()">
    <button class="login-btn" onclick="doLogin()">登录系统</button>
    <div id="login-msg"></div>
  </div>
</div>
<div id="panel">
  <div class="header"><h1>🎵 后台管理系统</h1><button class="logout-btn" onclick="logout()">退出登录</button></div>
  <div class="card"><h3>👥 用户管理</h3><table><thead><tr><th>ID</th><th>邮箱</th><th>注册时间</th><th>操作</th></tr></thead><tbody id="user-tb"></tbody></table></div>
  <div class="card"><h3>🎵 音乐管理</h3><div class="upload-area"><input type="file" id="music-file" accept=".mp3,.wav,.ogg,.flac"><button class="upload-btn" onclick="uploadMusic()">上传</button></div><div id="music-list"></div></div>
</div>
<script>
let token = localStorage.getItem('admin_token') || '';
const getHeaders = () => ({'Content-Type':'application/json', ...(token ? {'Authorization':'Bearer '+token} : {})});

function showLogin(){document.getElementById('login-box').style.display='flex';document.getElementById('panel').style.display='none';}
function showPanel(){document.getElementById('login-box').style.display='none';document.getElementById('panel').style.display='block';}

async function apiFetch(url, opts={}){
  const res = await fetch(url, {...opts, headers:getHeaders()});
  if(res.status===401){ token=''; localStorage.removeItem('admin_token'); showLogin(); return null; }
  if(!res.ok) throw new Error((await res.json()).detail || '请求失败');
  return res.json();
}

async function doLogin(){
  const pwd=document.getElementById('pwd').value.trim();
  const msg=document.getElementById('login-msg');
  if(!pwd){msg.textContent='❌ 请输入密码';msg.style.color='#e74c3c';return;}
  msg.textContent='验证中...';msg.style.color='#667eea';
  document.getElementById('pwd').disabled=true;
  try{
    const res=await fetch('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pwd})});
    const data=await res.json();
    if(!res.ok) throw new Error(data.detail||'密码错误');
    token=data.token; localStorage.setItem('admin_token',token);
    msg.textContent=''; showPanel(); loadData();
  }catch(e){msg.textContent='❌ '+e.message;msg.style.color='#e74c3c';}
  finally{document.getElementById('pwd').disabled=false;document.getElementById('pwd').focus();}
}

function logout(){token='';localStorage.removeItem('admin_token');document.getElementById('pwd').value='';document.getElementById('login-msg').textContent='';showLogin();}

async function loadData(){
  try{
    const u=await apiFetch('/api/admin/users');
    const tb=document.getElementById('user-tb'); tb.innerHTML='';
    if(!u||!u.users.length) tb.innerHTML='<tr><td colspan="4" class="empty-msg">暂无用户</td></tr>';
    else u.users.forEach(r=>tb.innerHTML+=`<tr><td>${r.id}</td><td>${r.email}</td><td>${r.created_at||'-'}</td><td><button class="action-btn" onclick="delUser(${r.id})">删除</button></td></tr>`);
    
    const m=await apiFetch('/api/music/list');
    const list=document.getElementById('music-list'); list.innerHTML='';
    if(!m||!m.music.length) list.innerHTML='<div class="empty-msg">暂无音乐</div>';
    else m.music.forEach(r=>list.innerHTML+=`<div class="music-item"><span>🎵 ${r.name} <small>(${r.size}KB)</small></span><button class="action-btn" onclick="delMusic('${r.filename}')">删除</button></div>`);
  }catch(e){console.error(e);alert('数据加载失败');}
}

async function delUser(id){if(!confirm('确定删除？'))return;await apiFetch(`/api/admin/users/${id}`,{method:'DELETE'});loadData();}
async function delMusic(f){if(!confirm('确定删除？'))return;await apiFetch(`/api/music/${encodeURIComponent(f)}`,{method:'DELETE'});loadData();}
async function uploadMusic(){
  const file=document.getElementById('music-file').files[0];
  if(!file)return alert('请选择文件');
  const fd=new FormData();fd.append('file',file);
  const res=await fetch('/api/music/upload',{method:'POST',headers:{'Authorization':'Bearer '+token},body:fd});
  alert((await res.json()).message);loadData();document.getElementById('music-file').value='';
}

document.addEventListener('DOMContentLoaded',()=>{ token ? showPanel() && loadData() : showLogin(); });
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def index(): return html_resp(GAME_PAGE)
@app.get("/game", response_class=HTMLResponse)
async def game_page(): return html_resp(GAME_PAGE)
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(): return html_resp(ADMIN_PAGE)

if __name__ == "__main__":
    init_db()
    port = 8000
    while port < 8010:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: s.bind(("127.0.0.1", port)); break
        except OSError: port += 1
    if port >= 8010: print("❌ 无法找到可用端口"); input("按回车退出..."); sys.exit(1)
    print(f"\n{'='*50}\n🎵 系统启动成功！\n{'='*50}\n🎮 游戏页面：http://127.0.0.1:{port}/\n🔐 后台管理：http://127.0.0.1:{port}/admin\n🔒 安全提示：请使用预设密码在网页端登录后台\n{'='*50}\n")
    try: uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e: print(f"❌ 启动失败：{e}")from fastapi import FastAPI
app = FastAPI()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app="run:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )