#!/usr/bin/env python3
"""
天气仪表盘 — 中科天玑
======================
零依赖、单文件、一键启动。

用法:
    python3 weather.py               # 默认端口 8765
    python3 weather.py --public      # 允许局域网设备访问

然后浏览器自动打开 → http://localhost:8765/
"""
import json, urllib.request, urllib.parse, urllib.error, socket, sys, os, webbrowser, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== 配置 ====================
API_KEY  = "aok37vonmuw20t5iz1a03nkz"
API_BASE = "https://api.tjweather.com/beta"
PORT     = 8765
BIND     = "127.0.0.1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==================== 内置 HTML 页面 ====================
HTML_PAGE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>天气仪表盘 - 中科天玑</title>
<style>
:root{--bg:#f0f2f5;--card:#fff;--border:#e8e8e8;--text:#333;--sub:#999;--accent:#1890ff;--green:#52c41a;--orange:#fa8c16;--purple:#722ed1;--teal:#13c2c2}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;min-height:100vh;padding:16px}
.header{text-align:center;padding:20px 0 24px}
.header h1{font-size:26px;font-weight:600;color:#1a1a1a}
.header .sub{color:var(--sub);font-size:13px;margin-top:6px}
.dashboard{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));max-width:1400px;margin:0 auto}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04)}
.card.span2{grid-column:span 2}.card.full{grid-column:1/-1}
.card-title{font-size:12px;font-weight:600;color:var(--sub);letter-spacing:1px;margin-bottom:16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.dot{width:8px;height:8px;border-radius:50%}.dot.teal{background:var(--teal)}.dot.green{background:var(--green)}.dot.blue{background:var(--accent)}.dot.purple{background:var(--purple)}
.hero-row{display:grid;gap:16px;grid-template-columns:2fr 1fr;max-width:1400px;margin:0 auto 16px}
.main-weather{display:flex;align-items:center;gap:30px;padding:10px 0}
.temp-big{font-size:96px;font-weight:700;line-height:1;color:#1a1a1a}
.weather-meta{display:flex;flex-direction:column;gap:6px}
.weather-meta .lbl{font-size:11px;color:var(--sub)}.weather-meta .val{font-size:16px;font-weight:500}
.dg{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.dg-item{text-align:center;padding:12px 8px;background:#fafafa;border-radius:8px}
.dg-item .v{font-size:24px;font-weight:600}.dg-item .l{font-size:11px;color:var(--sub);margin-top:3px}
.fc-row{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px}
.fc-day{flex:0 0 110px;text-align:center;padding:14px 8px;background:#fafafa;border-radius:8px}
.fc-day .dn{font-size:12px;font-weight:600;margin-bottom:4px;color:var(--teal)}
.fc-day .di{font-size:28px;margin:6px 0}
.fc-day .dt{font-size:11px;color:var(--sub);line-height:1.4}
.fc-day .dr{font-size:14px;font-weight:600;margin-top:4px}
svg.chart{width:100%;height:auto;max-height:280px}
.src-badge{font-size:10px;padding:2px 10px;border-radius:10px;margin-left:4px;color:#fff;font-weight:500}
.src-tj{background:#13c2c2}
.loading{text-align:center;padding:60px;color:var(--sub)}
.spinner{display:inline-block;width:40px;height:40px;border:3px solid #e8e8e8;border-top-color:var(--teal);border-radius:50%;animation:spin 1s linear infinite;margin-bottom:12px}
@keyframes spin{to{transform:rotate(360deg)}}
.error-box{background:#fff2f0;border:1px solid #ffccc7;border-radius:8px;padding:16px;color:#cf1322;text-align:center;margin:20px auto;max-width:600px}
.note{text-align:center;color:var(--sub);font-size:12px;padding:20px;max-width:1400px;margin:0 auto}
@media(max-width:800px){.hero-row{grid-template-columns:1fr}.main-weather{flex-direction:column;gap:14px}.temp-big{font-size:64px}.card.span2{grid-column:span 1}}
</style>
</head>
<body>
<div class="header"><h1>🌤️ 实时天气仪表盘</h1><div class="sub"><span id="locLabel">📍 定位中...</span></div><div class="sub" id="updateTime">加载中...</div></div>
<div class="loading" id="loading"><div class="spinner"></div><p>正在获取中科天玑气象数据...</p></div>
<div class="error-box" id="errorBox" style="display:none"></div>
<div id="app" style="display:none">
<div class="hero-row">
<div class="card">
<div class="card-title"><span class="dot teal"></span> 当前气象 <span class="src-badge src-tj">中科天玑</span></div>
<div class="main-weather"><div class="temp-big" id="mainTemp">--°</div>
<div class="weather-meta"><div><span class="lbl">温度范围（今日） </span><span class="val" id="tempRange">--</span></div>
<div><span class="lbl">风速风向 </span><span class="val" id="windInfo">--</span></div>
<div><span class="lbl">相对湿度 </span><span class="val" id="humInfo">--</span></div>
<div><span class="lbl">降水率 </span><span class="val" id="precipInfo">--</span></div></div></div></div>
<div class="card">
<div class="card-title"><span class="dot green"></span> 气象要素速览</div>
<div class="dg">
<div class="dg-item"><div class="v" id="temperature">--</div><div class="l">温度 °C</div></div>
<div class="dg-item"><div class="v" id="humidity">--</div><div class="l">相对湿度 %</div></div>
<div class="dg-item"><div class="v" id="precip">--</div><div class="l">降水率 mm/hr</div></div>
<div class="dg-item"><div class="v" id="windSpeed">--</div><div class="l">风速 m/s</div></div>
<div class="dg-item"><div class="v" id="windDir">--</div><div class="l">风向</div></div>
<div class="dg-item"><div class="v" id="todayPrecip">--</div><div class="l">今日累计降水 mm</div></div></div></div></div>
<div class="dashboard">
<div class="card span2"><div class="card-title"><span class="dot teal"></span> 今日温度（逐小时） <span class="src-badge src-tj">中科天玑</span></div><svg class="chart" id="tempSvg" viewBox="0 0 800 280" preserveAspectRatio="xMidYMid meet"></svg></div>
<div class="card span2"><div class="card-title"><span class="dot blue"></span> 今日风速（逐小时） <span class="src-badge src-tj">中科天玑</span></div><svg class="chart" id="windSvg" viewBox="0 0 800 220" preserveAspectRatio="xMidYMid meet"></svg></div>
<div class="card full"><div class="card-title"><span class="dot purple"></span> 7天预报 <span class="src-badge src-tj">中科天玑</span></div><div class="fc-row" id="fcRow"></div></div></div>
<div class="note">数据来源：中科天玑 api.tjweather.com 数值预报 | 要素：2米温度、10米风速/风向、2米相对湿度、总降水率</div></div>
<script>
const $=id=>document.getElementById(id);
const FIELDS='t2m,ws10m,wd10m,rh2m,tp';
function windDirText(d){const dirs=['北','东北偏北','东北','东北偏东','东','东南偏东','东南','东南偏南','南','西南偏南','西南','西南偏西','西','西北偏西','西北','西北偏北'];return dirs[Math.round(d/22.5)%16]}
function weatherIcon(t,p,h){if(p>1)return'🌧️';if(p>.1)return'🌦️';if(h>90)return'🌫️';if(h>70)return'☁️';if(t>30)return'☀️';if(t>20)return'🌤️';if(t<5)return'❄️';if(t<15)return'⛅';return'🌤️'}
async function getLoc(){if(navigator.geolocation)try{const p=await new Promise((r,j)=>{const t=setTimeout(()=>j(new Error('timeout')),3000);navigator.geolocation.getCurrentPosition(x=>{clearTimeout(t);r(x)},e=>{clearTimeout(t);j(e)},{timeout:3000,maximumAge:600000})});return{lat:p.coords.latitude,lon:p.coords.longitude,method:'GPS'}}catch(e){}try{const c=new AbortController();const t=setTimeout(()=>c.abort(),3000);const r=await fetch('https://ipapi.co/json/',{signal:c.signal});clearTimeout(t);if(r.ok){const d=await r.json();return{lat:d.latitude,lon:d.longitude,city:d.city,country:d.country_name,method:'IP'}}}catch(e){}return{lat:39.9,lon:116.4,city:'北京',country:'中国',method:'默认'}}
async function fetchData(lat,lon){const p=new URLSearchParams({fields:FIELDS,loc:lon.toFixed(2)+','+lat.toFixed(2),fcst_days:'7',fcst_hours:'24'});const r=await fetch('/api/weather?'+p.toString());if(!r.ok)throw Error('HTTP '+r.status);const j=await r.json();if(j.code!==200)throw Error('['+j.code+'] '+j.message);return j.data}
function extractDaily(data){const m={};for(const e of data){const d=e.time.slice(0,10);if(!m[d])m[d]={date:d,temps:[],precip:0,winds:[],hums:[]};const o=m[d];if(e.t2m!=null)o.temps.push(e.t2m);if(e.tp!=null)o.precip+=e.tp;if(e.ws10m!=null)o.winds.push(e.ws10m);if(e.rh2m!=null)o.hums.push(e.rh2m)}return Object.values(m).sort((a,b)=>a.date.localeCompare(b.date)).map(d=>({date:d.date,tmin:d.temps.length?Math.min(...d.temps):null,tmax:d.temps.length?Math.max(...d.temps):null,precipSum:d.precip,avgWind:d.winds.length?d.winds.reduce((a,b)=>a+b,0)/d.winds.length:null,avgHum:d.hums.length?d.hums.reduce((a,b)=>a+b,0)/d.hums.length:null}))}
function render(loc,tj){const cur=tj.data[0],daily=extractDaily(tj.data),now=new Date(),todayStr=now.toISOString().slice(0,10),todayData=tj.data.filter(e=>e.time.slice(0,10)===todayStr),td=daily.find(d=>d.date===todayStr);const cityStr=loc.city?loc.city+', '+(loc.country||''):loc.lat.toFixed(2)+', '+loc.lon.toFixed(2);$('locLabel').innerHTML='📍 '+cityStr+' &nbsp;|&nbsp; '+loc.method+'定位 &nbsp;|&nbsp; 坐标('+loc.lat.toFixed(2)+','+loc.lon.toFixed(2)+')';$('updateTime').textContent='🕐 模式起报: '+tj.time_init+' | 数据时间: '+cur.time+' | 刷新: '+now.toLocaleString('zh-CN',{timeZone:'Asia/Shanghai'});$('mainTemp').textContent=Math.round(cur.t2m)+'°';$('tempRange').textContent='↑ '+(td?Math.round(td.tmax):'--')+'° / ↓ '+(td?Math.round(td.tmin):'--')+'°';$('windInfo').textContent=cur.ws10m.toFixed(1)+' m/s '+windDirText(cur.wd10m)+' ('+Math.round(cur.wd10m)+'°)';$('humInfo').textContent=Math.round(cur.rh2m)+'%';$('precipInfo').textContent=cur.tp.toFixed(2)+' mm/hr';$('temperature').textContent=cur.t2m.toFixed(1)+'°';$('humidity').textContent=Math.round(cur.rh2m)+'%';$('precip').textContent=cur.tp.toFixed(2);$('windSpeed').textContent=cur.ws10m.toFixed(1);$('windDir').innerHTML='<svg width="20" height="20" viewBox="0 0 20 20" style="vertical-align:middle;transform:rotate('+cur.wd10m+'deg)"><line x1="10" y1="17" x2="10" y2="3" stroke="#13c2c2" stroke-width="2" stroke-linecap="round"/><polygon points="10,0 6,6 14,6" fill="#13c2c2"/></svg> '+Math.round(cur.wd10m)+'° '+windDirText(cur.wd10m);$('todayPrecip').textContent=td?td.precipSum.toFixed(1)+' mm':'--';let fc='';const dl=['周日','周一','周二','周三','周四','周五','周六'];for(let i=0;i<daily.length&&i<7;i++){const d=daily[i];const dn=i===0?'今天':(i===1?'明天':dl[(now.getDay()+i)%7]);fc+='<div class="fc-day"><div class="dn">'+dn+'</div><div class="di">'+weatherIcon(d.tmax,d.precipSum,d.avgHum)+'</div><div class="dt">'+d.date.slice(5)+'</div><div class="dr">↑'+Math.round(d.tmax)+'° ↓'+Math.round(d.tmin)+'°</div><div style="font-size:10px;color:#999">💧'+d.precipSum.toFixed(1)+'mm</div><div style="font-size:10px;color:#999">💨'+d.avgWind.toFixed(1)+'m/s</div></div>'} $('fcRow').innerHTML=fc;drawTempChart(todayData);drawWindChart(todayData)}
function drawTempChart(td){const svg=$('tempSvg');if(!td.length){svg.innerHTML='<text x="400" y="150" fill="#999" font-size="14" text-anchor="middle">暂无今日数据</text>';return}const pts=td.map(e=>({hour:parseInt(e.time.slice(11,13)),temp:e.t2m}));if(pts.length<2){svg.innerHTML='<text x="400" y="150" fill="#999" font-size="14" text-anchor="middle">数据不足</text>';return}const temps=pts.map(p=>p.temp),minT=Math.floor(Math.min(...temps)-1),maxT=Math.ceil(Math.max(...temps)+1),range=maxT-minT||1,L=60,R=30,T=24,B=36,PW=800-L-R,PH=280-T-B,N=pts.length-1,xOf=i=>L+(N>0?(PW/N)*i:PW/2),yOf=t=>T+PH-((t-minT)/range)*PH;let h='';for(let i=0;i<=5;i++){const v=maxT-(range/5)*i,y=yOf(v);h+='<line x1="'+L+'" y1="'+y+'" x2="'+(800-R)+'" y2="'+y+'" stroke="#e8e8e8" stroke-width="0.8"/><text x="'+(L-6)+'" y="'+(y+4)+'" fill="#999" font-size="12" text-anchor="end">'+Math.round(v)+'°</text>'}const step=pts.length<=12?1:(pts.length<=24?2:3);for(let i=0;i<pts.length;i+=step){const x=xOf(i);h+='<line x1="'+x+'" y1="'+(T+PH)+'" x2="'+x+'" y2="'+(T+PH+6)+'" stroke="#d9d9d9" stroke-width="0.8"/><text x="'+x+'" y="'+(T+PH+20)+'" fill="#999" font-size="11" text-anchor="middle">'+pts[i].hour+'时</text>'}h+='<line x1="'+L+'" y1="'+T+'" x2="'+L+'" y2="'+(T+PH)+'" stroke="#d9d9d9" stroke-width="1"/><line x1="'+L+'" y1="'+(T+PH)+'" x2="'+(800-R)+'" y2="'+(T+PH)+'" stroke="#d9d9d9" stroke-width="1"/>';h+='<defs><linearGradient id="fg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#13c2c2" stop-opacity="0.3"/><stop offset="100%" stop-color="#13c2c2" stop-opacity="0.03"/></linearGradient></defs>';let ap='M '+xOf(0)+' '+(T+PH);for(let i=0;i<pts.length;i++)ap+=' L '+xOf(i)+' '+yOf(pts[i].temp);ap+=' L '+xOf(pts.length-1)+' '+(T+PH)+' Z';h+='<path d="'+ap+'" fill="url(#fg)"/>';let lp='M '+xOf(0)+' '+yOf(pts[0].temp);for(let i=1;i<pts.length;i++)lp+=' L '+xOf(i)+' '+yOf(pts[i].temp);h+='<path d="'+lp+'" fill="none" stroke="#13c2c2" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>';const ds=pts.length<=12?1:(pts.length<=24?2:3);for(let i=0;i<pts.length;i+=ds)h+='<circle cx="'+xOf(i)+'" cy="'+yOf(pts[i].temp)+'" r="3.5" fill="#13c2c2" stroke="#fff" stroke-width="1.2"/>';const nh=new Date().getHours();let hi=pts.length-1;for(let i=0;i<pts.length;i++){if(pts[i].hour>nh){hi=Math.max(0,i-1);break}}const lx=xOf(hi),ly=yOf(pts[hi].temp);h+='<circle cx="'+lx+'" cy="'+ly+'" r="6" fill="none" stroke="#13c2c2" stroke-width="2.5"/><text x="'+lx+'" y="'+(ly-14)+'" fill="#13c2c2" font-size="15" font-weight="bold" text-anchor="middle">'+Math.round(pts[hi].temp)+'°</text><text x="'+lx+'" y="'+(ly+28)+'" fill="#999" font-size="10" text-anchor="middle">现在</text>';svg.innerHTML=h}
function drawWindChart(td){const svg=$('windSvg');if(!td.length){svg.innerHTML='<text x="400" y="120" fill="#999" font-size="14" text-anchor="middle">暂无数据</text>';return}const pts=td.map(e=>({hour:parseInt(e.time.slice(11,13)),ws:e.ws10m}));if(pts.length<2){svg.innerHTML='<text x="400" y="120" fill="#999" font-size="14" text-anchor="middle">数据不足</text>';return}const speeds=pts.map(p=>p.ws),maxS=Math.ceil(Math.max(...speeds)+1),L=60,R=30,T=20,B=32,PW=800-L-R,PH=220-T-B,N=pts.length-1,xOf=i=>L+(N>0?(PW/N)*i:PW/2),yOf=s=>T+PH-(s/maxS)*PH;let h='';for(let i=0;i<=4;i++){const v=(maxS/4)*i,y=yOf(v);h+='<line x1="'+L+'" y1="'+y+'" x2="'+(800-R)+'" y2="'+y+'" stroke="#e8e8e8" stroke-width="0.8"/><text x="'+(L-6)+'" y="'+(y+4)+'" fill="#999" font-size="12" text-anchor="end">'+v.toFixed(1)+'</text>'}const step=pts.length<=12?1:(pts.length<=24?2:3);for(let i=0;i<pts.length;i+=step){const x=xOf(i);h+='<line x1="'+x+'" y1="'+(T+PH)+'" x2="'+x+'" y2="'+(T+PH+6)+'" stroke="#d9d9d9" stroke-width="0.8"/><text x="'+x+'" y="'+(T+PH+18)+'" fill="#999" font-size="11" text-anchor="middle">'+pts[i].hour+'时</text>'}h+='<line x1="'+L+'" y1="'+T+'" x2="'+L+'" y2="'+(T+PH)+'" stroke="#d9d9d9" stroke-width="1"/><line x1="'+L+'" y1="'+(T+PH)+'" x2="'+(800-R)+'" y2="'+(T+PH)+'" stroke="#d9d9d9" stroke-width="1"/>';h+='<defs><linearGradient id="wg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1890ff" stop-opacity="0.3"/><stop offset="100%" stop-color="#1890ff" stop-opacity="0.03"/></linearGradient></defs>';let ap='M '+xOf(0)+' '+(T+PH);for(let i=0;i<pts.length;i++)ap+=' L '+xOf(i)+' '+yOf(pts[i].ws);ap+=' L '+xOf(pts.length-1)+' '+(T+PH)+' Z';h+='<path d="'+ap+'" fill="url(#wg)"/>';let lp='M '+xOf(0)+' '+yOf(pts[0].ws);for(let i=1;i<pts.length;i++)lp+=' L '+xOf(i)+' '+yOf(pts[i].ws);h+='<path d="'+lp+'" fill="none" stroke="#1890ff" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>';const ds=pts.length<=12?1:(pts.length<=24?2:3);for(let i=0;i<pts.length;i+=ds)h+='<circle cx="'+xOf(i)+'" cy="'+yOf(pts[i].ws)+'" r="3" fill="#1890ff" stroke="#fff" stroke-width="1.2"/>';const nh=new Date().getHours();let hi=pts.length-1;for(let i=0;i<pts.length;i++){if(pts[i].hour>nh){hi=Math.max(0,i-1);break}}const lx=xOf(hi),ly=yOf(pts[hi].ws);h+='<circle cx="'+lx+'" cy="'+ly+'" r="5" fill="none" stroke="#1890ff" stroke-width="2.2"/><text x="'+lx+'" y="'+(ly-12)+'" fill="#1890ff" font-size="14" font-weight="bold" text-anchor="middle">'+pts[hi].ws.toFixed(1)+' m/s</text>';svg.innerHTML=h}
(async function(){try{const loc=await getLoc();console.log('📍 定位:',loc);const tj=await fetchData(loc.lat,loc.lon);console.log('✅ 数据:',tj.data.length,'条');render(loc,tj)}catch(e){console.error(e);const eb=$('errorBox');eb.style.display='block';eb.innerHTML='⚠️ 数据加载失败：'+e.message+'<br><small>请检查网络连接后刷新重试</small>'}finally{$('loading').style.display='none';$('app').style.display=''}})();
</script>
</body></html>'''


# ==================== HTTP 服务器 ====================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path

        # API 代理 → 中科天玑
        if path.startswith("/api/weather"):
            qs = urllib.parse.urlparse(path).query
            params = urllib.parse.parse_qs(qs)
            api_params = {
                "key": API_KEY,
                "fields": params.get("fields", ["t2m,ws10m,wd10m,rh2m,tp"])[0],
                "loc": params.get("loc", ["116.40,39.90"])[0],
                "fcst_days": params.get("fcst_days", ["7"])[0],
                "fcst_hours": params.get("fcst_hours", ["24"])[0],
            }
            url = f"{API_BASE}?{urllib.parse.urlencode(api_params)}"
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "WeatherApp/1.0")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", len(data))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=300")
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                err = json.dumps({"code": -1, "message": str(e), "data": None})
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(err.encode())
            return

        # 健康检查
        if path == "/api/health":
            data = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
            return

        # 所有其他路径 → 返回 HTML 页面
        html = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f"  {args[0]}")


# ==================== 启动 ====================
def main():
    bind = BIND
    port = PORT
    args = sys.argv[1:]
    if "--public" in args:
        bind = "0.0.0.0"
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args):
            port = int(args[idx + 1])

    # 获取本机 IP（用于显示）
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        pass

    server = HTTPServer((bind, port), Handler)
    print("=" * 50)
    print("  🌤️  天气仪表盘 — 中科天玑")
    print("=" * 50)
    print(f"  本机访问: http://localhost:{port}/")
    print(f"           http://127.0.0.1:{port}/")
    if bind == "0.0.0.0" and local_ip != "127.0.0.1":
        print(f"  局域网:   http://{local_ip}:{port}/")
    print()
    print(f"  按 Ctrl+C 停止")
    print("=" * 50)

    # 自动打开浏览器
    def open_browser():
        import time
        time.sleep(0.5)
        webbrowser.open(f"http://localhost:{port}/")
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止")
        server.server_close()


if __name__ == "__main__":
    main()
