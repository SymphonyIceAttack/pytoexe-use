import os
import json
import threading
import time
from flask import Flask, request, render_template_string
from pyngrok import ngrok

# ====================== 配置 ======================
PORT = 5000
CONFIG_DIR = "./config"
RESOURCES_FILE = os.path.join(CONFIG_DIR, "resources.json")

DEFAULT_DATA = [
    {
        "name": "百度",
        "url": "https://www.baidu.com",
        "icon": "https://www.baidu.com/favicon.ico",
        "color": "#2382f6"
    },
    {
        "name": "哔哩哔哩",
        "url": "https://www.bilibili.com",
        "icon": "https://www.bilibili.com/favicon.ico",
        "color": "#fb5fa8"
    },
    {
        "name": "抖音",
        "url": "https://www.douyin.com",
        "icon": "https://www.douyin.com/favicon.ico",
        "color": "#fe2c55"
    }
]

# ====================== 自动创建配置文件 ======================
def load_data():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)
    with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if "title" in item and "name" not in item:
            item["name"] = item["title"]
    return data

data = load_data()
app = Flask(__name__)

# ====================== 主页 ======================
@app.route("/")
def index():
    q = request.args.get("q", "").lower()
    items = [x for x in data if q in x["name"].lower()]
    return render_template_string('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>快捷导航</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:system-ui,-apple-system,Segoe UI,Roboto}
        body{
            min-height:100vh;
            padding:30px 20px;
            transition: background 0.3s;
            background: linear-gradient(135deg, #e0f7ff 0%, #f5fcff 100%);
        }
        .container{max-width:1200px;margin:0 auto;}

        .top-bar{
            display:flex;
            justify-content:center;
            align-items:center;
            gap:12px;
            margin-bottom:20px;
            flex-wrap:wrap;
        }
        .theme-btn{
            width:32px;
            height:32px;
            border-radius:50%;
            border:none;
            cursor:pointer;
            box-shadow:0 0 6px rgba(0,0,0,0.15);
        }
        .setting-btn{
            padding:8px 14px;
            border-radius:12px;
            border:none;
            background:#fff;
            cursor:pointer;
            font-size:14px;
            box-shadow:0 2px 8px rgba(0,0,0,0.1);
        }

        .settings-panel{
            background:#fff;
            border-radius:16px;
            padding:20px;
            margin-bottom:24px;
            display:none;
            gap:16px;
            grid-template-columns:1fr;
            box-shadow:0 3px 12px rgba(0,0,0,0.08);
        }
        .settings-panel.active{display:grid;}
        .setting-item{
            display:flex;
            flex-direction:column;
            gap:8px;
        }
        .setting-item label{
            font-size:14px;
            color:#444;
            font-weight:500;
            display:flex;
            justify-content:space-between;
        }
        input[type="range"]{
            width:100%;
            height:6px;
            border-radius:3px;
            background:#ddd;
            outline:none;
            cursor:pointer;
        }

        h1{text-align:center;margin-bottom:24px;color:#222;font-size:28px;}
        .search{width:100%;padding:16px 20px;border-radius:16px;border:none;box-shadow:0 2px 10px rgba(0,0,0,0.05);margin-bottom:28px;font-size:18px;}
        
        .grid{
            display:grid;
            grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
            gap:20px;
        }
        .card{
            background:#fff;
            border-radius:20px;
            padding:32px 24px;
            text-align:center;
            box-shadow:0 3px 12px rgba(0,0,0,0.05);
            transition:all 0.25s cubic-bezier(0.25,0.8,0.25,1);
            height:160px;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            cursor:pointer;
            user-select:none;
            position:relative;
            overflow:hidden;
            opacity:0;
            transform:translateY(30px);
        }
        .card.visible{
            opacity:1;
            transform:translateY(0);
        }
        /* 3D 悬浮 */
        .card:hover{
            transform:translateY(-6px) scale(1.02) rotateX(3deg) rotateY(-3deg);
            box-shadow:0 12px 24px rgba(0,0,0,0.12);
        }
        /* 光泽扫过 */
        .card::before{
            content:'';
            position:absolute;
            top:0;left:-100%;
            width:100%;height:100%;
            background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);
            transition:left 0.6s ease;
            pointer-events:none;
        }
        .card:hover::before{left:100%;}
        /* 点击缩小 */
        .card.clicked{
            animation:pressAnim 0.3s ease forwards;
        }
        @keyframes pressAnim{
            0%{transform:scale(1);}
            50%{transform:scale(0.92);}
            100%{transform:scale(1);}
        }
        /* 选中彩虹光圈 */
        .card.selected::after{
            content:'';
            position:absolute;
            top:-3px;left:-3px;right:-3px;bottom:-3px;
            border-radius:inherit;
            background:linear-gradient(135deg,#3B82F6,#8B5CF6,#EC4899);
            z-index:-1;
            opacity:0;
            animation:selectAnim 0.25s ease forwards;
        }
        @keyframes selectAnim{
            0%{opacity:0;transform:scale(0.9);}
            50%{opacity:1;transform:scale(1.05);}
            100%{opacity:0;transform:scale(1);}
        }
        /* 点击波纹 */
        .ripple{
            position:absolute;
            border-radius:50%;
            background:rgba(255,255,255,0.4);
            transform:scale(0);
            animation:rippleAnim 0.6s linear;
            pointer-events:none;
        }
        @keyframes rippleAnim{
            to{transform:scale(4);opacity:0;}
        }
        .icon{width:70px;height:70px;margin:0 auto 16px;border-radius:16px;display:flex;align-items:center;justify-content:center;}
        .icon img{width:36px;height:36px;object-fit:contain;}
        .name{font-size:17px;font-weight:500;color:#222;margin-top:4px;}
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <button class="theme-btn" style="background:linear-gradient(135deg,#e0f7ff,#f5fcff)" onclick="setTheme('blue')"></button>
            <button class="theme-btn" style="background:linear-gradient(135deg,#f3e0ff,#f9f5ff)" onclick="setTheme('purple')"></button>
            <button class="theme-btn" style="background:linear-gradient(135deg,#e0ffe0,#f5fff5)" onclick="setTheme('green')"></button>
            <button class="theme-btn" style="background:linear-gradient(135deg,#ffe0f0,#fff5fa)" onclick="setTheme('pink')"></button>
            <button class="theme-btn" style="background:linear-gradient(135deg,#f0f0f0,#fafafa)" onclick="setTheme('gray')"></button>
            <button class="setting-btn" onclick="toggleSettings()">⚙️ 设置</button>
        </div>

        <div class="settings-panel" id="settingsPanel">
            <div class="setting-item">
                <label>卡片宽度 <span id="wVal">220</span>px</label>
                <input type="range" id="cardWidth" min="150" max="400" value="220">
            </div>
            <div class="setting-item">
                <label>卡片高度 <span id="hVal">160</span>px</label>
                <input type="range" id="cardHeight" min="100" max="300" value="160">
            </div>
            <div class="setting-item">
                <label>卡片间距 <span id="gVal">20</span>px</label>
                <input type="range" id="cardGap" min="5" max="50" value="20">
            </div>
            <div class="setting-item">
                <label>卡片圆角 <span id="rVal">20</span>px</label>
                <input type="range" id="cardRadius" min="0" max="50" value="20">
            </div>
        </div>

        <h1>快捷导航</h1>
        <form>
            <input class="search" type="text" name="q" placeholder="搜索..." value="{{q}}">
        </form>
        <div class="grid" id="cardGrid">
            {% for item in items %}
            <div class="card" data-url="{{item.url}}">
                <div class="icon" style="background:{{item.color}}20">
                    <img src="{{item.icon}}" alt="" onerror="this.style.display='none'">
                </div>
                <div class="name">{{item.name}}</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        const themes = {
            blue: "linear-gradient(135deg, #e0f7ff 0%, #f5fcff 100%)",
            purple: "linear-gradient(135deg, #f3e0ff 0%, #f9f5ff 100%)",
            green: "linear-gradient(135deg, #e0ffe0 0%, #f5fff5 100%)",
            pink: "linear-gradient(135deg, #ffe0f0 0%, #fff5fa 100%)",
            gray: "linear-gradient(135deg, #f0f0f0 0%, #fafafa 100%)"
        };

        function toggleSettings(){
            document.getElementById("settingsPanel").classList.toggle("active");
        }

        function applySettings(){
            const w = +document.getElementById("cardWidth").value;
            const h = +document.getElementById("cardHeight").value;
            const g = +document.getElementById("cardGap").value;
            const r = +document.getElementById("cardRadius").value;

            document.getElementById("wVal").textContent = w;
            document.getElementById("hVal").textContent = h;
            document.getElementById("gVal").textContent = g;
            document.getElementById("rVal").textContent = r;

            const grid = document.getElementById("cardGrid");
            const cards = document.querySelectorAll(".card");

            grid.style.gridTemplateColumns = `repeat(auto-fill,minmax(${w}px,1fr))`;
            grid.style.gap = `${g}px`;

            cards.forEach(c=>{
                c.style.height = h+"px";
                c.style.borderRadius = r+"px";
            });

            localStorage.setItem("cardSettings", JSON.stringify({w,h,g,r}));
        }

        function setTheme(name){
            document.body.style.background = themes[name];
            localStorage.setItem("navTheme", name);
        }

        // 波纹效果
        function createRipple(e,el){
            const r = document.createElement('span');
            r.className = 'ripple';
            const d = Math.max(el.clientWidth,el.clientHeight);
            r.style.width = r.style.height = d+'px';
            const rect = el.getBoundingClientRect();
            r.style.left = e.clientX - rect.left - d/2 + 'px';
            r.style.top = e.clientY - rect.top - d/2 + 'px';
            el.appendChild(r);
            setTimeout(()=>r.remove(),600);
        }

        // 点击逻辑
        function goTo(e){
            const el = this;
            const url = el.dataset.url;
            createRipple(e,el);
            
            el.classList.remove("clicked","selected");
            void el.offsetWidth;
            el.classList.add("clicked","selected");

            setTimeout(()=>{
                window.open(url,"_blank");
            },300);
        }

        // 长按
        let longPressTimer;
        function startLongPress(){
            longPressTimer = setTimeout(()=>{
                alert("长按触发 ✨");
            },500);
        }
        function clearLongPress(){
            clearTimeout(longPressTimer);
        }

        // 滚动渐入
        function initScrollFade(){
            const obs = new IntersectionObserver(es=>{
                es.forEach(e=>{
                    e.target.classList.toggle("visible",e.isIntersecting);
                });
            });
            document.querySelectorAll(".card").forEach(c=>obs.observe(c));
        }

        // 拖拽排序
        function initDrag(){
            let dragEl = null;
            document.querySelectorAll(".card").forEach(c=>{
                c.draggable = true;
                c.addEventListener("dragstart",()=>{
                    dragEl = c;
                    setTimeout(()=>c.style.opacity="0.5",0);
                });
                c.addEventListener("dragover",e=>e.preventDefault());
                c.addEventListener("drop",e=>{
                    e.preventDefault();
                    if(dragEl && dragEl!==c){
                        dragEl.parentNode.insertBefore(dragEl,c.nextSibling);
                    }
                    dragEl.style.opacity="1";
                    dragEl=null;
                });
            });
        }

        // 初始化
        window.onload = function(){
            // 主题
            const t = localStorage.getItem("navTheme")||"blue";
            document.body.style.background = themes[t];

            // 设置
            const s = localStorage.getItem("cardSettings");
            if(s){
                const d = JSON.parse(s);
                document.getElementById("cardWidth").value = d.w;
                document.getElementById("cardHeight").value = d.h;
                document.getElementById("cardGap").value = d.g;
                document.getElementById("cardRadius").value = d.r;
            }
            applySettings();

            // 卡片事件
            document.querySelectorAll(".card").forEach(c=>{
                c.addEventListener("click",goTo);
                c.addEventListener("mousedown",startLongPress);
                c.addEventListener("mouseup",clearLongPress);
                c.addEventListener("mouseleave",clearLongPress);
            });

            // 滑动条
            document.querySelectorAll("input[type='range']").forEach(i=>{
                i.addEventListener("input",applySettings);
            });

            initScrollFade();
            initDrag();
        }
    </script>
</body>
</html>
    ''', items=items, q=q)

# ====================== 启动服务 ======================
def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

def start_tunnel():
    try:
        ngrok.kill()
        return ngrok.connect(PORT).public_url
    except:
        return None

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(1.5)
    link = start_tunnel()
    print("本地地址:", f"http://127.0.0.1:{PORT}")
    print("公网地址:", link or "仅本地")
    while True:
        time.sleep(1)