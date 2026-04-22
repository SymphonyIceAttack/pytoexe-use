from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import datetime
from collections import defaultdict
import time
import csv
import io

app = Flask(__name__)
app.secret_key = "rfid_wip_final"

wip_records = []
start_time = time.time()

# 一级主工序
main_process = ["毛坯准备", "零件加工", "热处理", "表面处理", "检验", "出库"]

#终11道工序顺序
process_sequence = [
    "毛坯准备",
    "车削",
    "铣削",
    "磨削",
    "铰孔",
    "钻孔",
    "热处理",
    "氧化处理",
    "电镀",
    "涂料",
    "出库"
]

# 工序别名映射
process_alias = {
    "车削(零件加工)": "车削",
    "铣削(零件加工)": "铣削",
    "磨削(零件加工)": "磨削",
    "铰孔(零件加工)": "铰孔",
    "钻孔(零件加工)": "钻孔",
    "涂装(表面处理)": "涂料",
    "氧化处理(表面处理)": "氧化处理",
    "电镀(表面处理)": "电镀",
}

def get_simple_proc(p):
    return process_alias.get(p, p)

def get_main_process(p):
    sp = get_simple_proc(p)
    if sp == "毛坯准备": return "毛坯准备"
    if sp in ["车削","铣削","磨削","铰孔","钻孔"]: return "零件加工"
    if sp == "热处理": return "热处理"
    if sp in ["氧化处理","电镀","涂料"]: return "表面处理"
    if sp == "检验": return "检验"
    if sp == "出库": return "出库"
    return sp

def get_rfid_status(rfid):
    records = [r for r in wip_records if r.get("rfid") == rfid]
    if not records: return None
    return sorted(records, key=lambda x: x["time"], reverse=True)[0]

# 一级工序弹窗
@app.route('/process_detail')
def process_detail():
    proc = request.args.get('proc', '').strip()
    details = []
    for r in wip_records:
        if get_main_process(r['process']) == proc:
            details.append({
                'time': r['time'], 'work_order': r['work_order'],
                'rfid': r['rfid'], 'process': r['process'], 'abnormal': r.get('abnormal', False)
            })
    return jsonify(details)

# 二级工序弹窗
@app.route('/sub_process_detail')
def sub_process_detail():
    sub_proc = request.args.get('sub_proc', '').strip()
    details = []
    for r in wip_records:
        if get_simple_proc(r['process']) == sub_proc:
            details.append({
                'time': r['time'], 'work_order': r['work_order'],
                'rfid': r['rfid'], 'process': r['process'], 'abnormal': r.get('abnormal', False)
            })
    return jsonify(details)

@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')
    search_rfid = request.args.get('rfid', '').strip()
    current_status = get_rfid_status(search_rfid) if search_rfid else None

    count = defaultdict(int)
    for r in wip_records:
        count[get_main_process(r["process"])] += 1

    part_list = ["车削","铣削","磨削","铰孔","钻孔"]
    part_count = defaultdict(int)
    for r in wip_records:
        sp = get_simple_proc(r["process"])
        if sp in part_list:
            part_count[sp] += 1

    surface_list = ["氧化处理","电镀","涂料"]
    surface_count = defaultdict(int)
    for r in wip_records:
        sp = get_simple_proc(r["process"])
        if sp in surface_list:
            surface_count[sp] += 1

    abnormal_list = [r for r in wip_records if r.get("abnormal")]
    recent = list(reversed(wip_records))[-15:]
    values = [count[p] for p in main_process]
    uptime = int(time.time() - start_time)
    uptime_str = f"{uptime//3600}h {(uptime%3600)//60}m {uptime%60}s"
    part_data = [{'name': k, 'value': part_count[k]} for k in part_list]
    surface_data = [{'name': k, 'value': surface_count[k]} for k in surface_list]

    # ===================== 订单看板：全部出库=已完成 =====================
    order_groups = defaultdict(list)
    for r in wip_records:
        order_groups[r['work_order']].append(r)

    order_board = []
    for idx, (wo, rows) in enumerate(order_groups.items(), 1):
        all_rfid = set(x['rfid'] for x in rows)
        out_rfid = set(x['rfid'] for x in rows if get_simple_proc(x['process']) == "出库")
        status = "已完成" if (all_rfid and out_rfid == all_rfid) else "未完成"
        mat = rows[0].get('material', '-') if rows else '-'
        order_board.append({"id": idx, "wo": wo, "material": mat, "status": status})

    # ===================== 任务看板：11项  =====================
    TASK_LIST = [
        "毛坯准备", "车削", "铣削", "磨削", "铰孔", "钻孔",
        "热处理", "氧化处理", "电镀", "涂料", "出库"
    ]

    task_board = []
    total_unique = len(set(r['rfid'] for r in wip_records))

    for task in TASK_LIST:
        if task == "出库":
            # 出库：只统计当前工序数量
            done = len(set(x['rfid'] for x in wip_records if get_simple_proc(x['process']) == "出库"))
        else:
            # 其他：走到后序=完成
            try:
                task_idx = process_sequence.index(task)
            except:
                task_idx = 999
            done = 0
            for rfid in set(x['rfid'] for x in wip_records):
                max_idx = -1
                for p in [get_simple_proc(x['process']) for x in wip_records if x['rfid'] == rfid]:
                    try:
                        idx = process_sequence.index(p)
                        if idx > max_idx:
                            max_idx = idx
                    except:
                        continue
                if max_idx > task_idx:
                    done += 1

        rate = int((done / total_unique) * 100) if total_unique > 0 else 0
        task_board.append({
            "name": task,
            "done": done,
            "total": total_unique,
            "progress": f"{done}/{total_unique}",
            "rate": rate
        })

    return render_template_string('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>RFID在制品追踪系统</title>
    <script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:"Microsoft YaHei",system-ui;}
        body{background:#0f1223;color:#e8e8e8;padding:20px;}
        .container{max-width:1800px;margin:0 auto;}
        .navbar{
            background:rgba(255,255,255,0.05);padding:14px 24px;border-radius:14px;
            display:flex;justify-content:space-between;align-items:center;
            margin-bottom:20px;backdrop-filter:blur(10px);
            border:1px solid rgba(255,255,255,0.1);
        }
        .navbar h2{
            background:linear-gradient(90deg,#4fc3f7,#64ffda);
            -webkit-background-clip:text;color:transparent;
        }
        .nav-btns{display:flex;gap:10px;align-items:center;}
        .time-text{color:#aaa;font-size:14px;}
        .btn{
            padding:8px 16px;background:linear-gradient(90deg,#2196F3,#00BCD4);
            color:white;border:none;border-radius:10px;
            text-decoration:none;cursor:pointer;transition:0.3s;
            font-size:14px;font-weight:500;
        }
        .btn:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(33,150,243,0.3);}
        .btn-danger{background:linear-gradient(90deg,#ff5252,#ff1744);}
        .search-bar{
            background:rgba(255,255,255,0.04);border-radius:14px;
            padding:14px 20px;margin-bottom:16px;
            border:1px solid rgba(255,255,255,0.1);
            display:flex;gap:10px;align-items:center;
        }
        .input{
            padding:8px 12px;background:#1a1c2d;color:#fff;
            border:1px solid #333;border-radius:8px;width:220px;
        }
        .grid{
            display:grid;grid-template-columns:repeat(6,1fr);
            gap:14px;margin-bottom:20px;
        }
        .card{
            background:rgba(255,255,255,0.04);cursor:pointer;
            border:1px solid rgba(255,255,255,0.1);
            border-radius:16px;padding:20px;text-align:center;
            backdrop-filter:blur(6px);box-shadow:0 8px 24px rgba(0,0,0,0.2);
            transition:0.3s;
        }
        .card:hover{transform:translateY(-4px);border-color:#4fc3f7;}
        .card p{font-size:14px;color:#aaa;margin-bottom:6px;}
        .num{font-size:26px;font-weight:600;color:#4fc3f7;}
        .chart-row{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}
        .chart-box{
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.1);
            border-radius:16px;padding:20px;height:300px;
        }
        .list-box{
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.1);
            border-radius:16px;padding:20px;height:400px;overflow-y:auto;
        }
        .list-box.bottom{height:320px;}
        .list-box h4{margin-bottom:12px;color:#ddd;}
        .item{
            padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.08);
            font-size:14px;color:#bbb;
        }
        .abnormal-item{
            padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.08);
            font-size:14px;color:#ff5252;
        }

        /* 统一弹窗动画 */
        .modal{
            position:fixed;top:0;left:0;width:100%;height:100%;
            background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;
            z-index:9999;display:none; animation:fadeIn 0.3s;
        }
        @keyframes fadeIn { from{opacity:0;} to{opacity:1;} }
        .modal-content{
            background:#1a1c2d;width:90%;max-width:800px;
            border-radius:16px;padding:24px;border:1px solid #444;
            max-height:80vh;overflow-y:auto;
            animation:scaleIn 0.3s;
        }
        @keyframes scaleIn { from{transform:scale(0.9);} to{transform:scale(1);} }
        .modal-header{
            display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;
        }
        .close-btn{
            background:#444;color:#fff;border:none;padding:6px 12px;border-radius:8px;cursor:pointer;
        }
        .detail-item{
            padding:10px;border-bottom:1px solid #333;color:#eee;
        }
        .detail-abnormal{color:#ff5252;}

        .board-table{width:100%;border-collapse:collapse;margin-top:10px;}
        .board-table th,.board-table td{padding:8px;text-align:center;border-bottom:1px solid #333;color:#ccc;}
        .board-table th{background:rgba(79,195,247,0.1);color:#4fc3f7;}
        .status-done{color:#69f0ae;}
        .status-doing{color:#4fc3f7;}

        /* 任务进度条 */
        .progress-wrap{width:100%;height:10px;background:#333;border-radius:5px;overflow:hidden;margin-top:4px;}
        .progress-bar{height:100%;background:linear-gradient(90deg,#69f0ae,#4fc3f7);}
        .rate-text{font-size:12px;color:#ccc;margin-top:2px;}

        ::-webkit-scrollbar{width:6px;}
        ::-webkit-scrollbar-thumb{background:#4fc3f7;border-radius:3px;}
    </style>
</head>
<body>
<div class="container">
    <div class="navbar">
        <h2>RFID 在制品智能追踪系统</h2>
        <div class="nav-btns">
            <span class="time-text" id="clock"></span>
            <span class="time-text">运行：{{uptime_str}}</span>
            <a href="/scan" class="btn">单次刷卡</a>
            <a href="/import" class="btn">导入</a>
            <a href="/clear" class="btn btn-danger">清空</a>
            <a href="/logout" class="btn">退出</a>
        </div>
    </div>

    <div class="search-bar">
        <span>🔍 RFID查询：</span>
        <form method="get" style="display:flex;gap:10px">
            <input class="input" name="rfid" placeholder="输入RFID" value="{{search_rfid}}">
            <button class="btn">查询</button>
            {% if search_rfid %}<a href="/" class="btn" style="background:#555">重置</a>{% endif %}
        </form>
    </div>

    <div class="grid">
        {% for i in range(6) %}
        <div class="card" onclick="showMainProc('{{main_process[i]}}')">
            <p>{{main_process[i]}}</p><div class="num">{{values[i]}}</div>
        </div>
        {% endfor %}
    </div>

    <div class="chart-row">
        <div class="chart-box" id="partPie"></div>
        <div class="chart-box" id="surfacePie"></div>
    </div>

    <div class="chart-row">
        <div class="list-box">
            <h4>订单看板</h4>
            <table class="board-table">
                <tr><th>序号</th><th>工单号</th><th>物料</th><th>状态</th></tr>
                {% for o in order_board %}
                <tr>
                    <td>{{o.id}}</td><td>{{o.wo}}</td><td>{{o.material}}</td>
                    <td class="{{'status-done' if o.status=='已完成' else 'status-doing'}}">{{o.status}}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="list-box">
            <h4>任务看板（11项）</h4>
            <table class="board-table">
                <tr><th>工序</th><th>进度</th><th>完成率</th></tr>
                {% for t in task_board %}
                <tr>
                    <td>{{t.name}}</td>
                    <td>{{t.progress}}</td>
                    <td style="min-width:120px">
                        <div class="progress-wrap">
                            <div class="progress-bar" style="width:{{t.rate}}%"></div>
                        </div>
                        <div class="rate-text">{{t.rate}}%</div>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div class="list-box bottom">
        <h4>⚠️ 异常工序</h4>
        {% for r in abnormal_list %}
        <div class="abnormal-item">[{{r.time}}] {{r.work_order}} {{r.rfid}} {{r.process}}</div>
        {% endfor %}
        <h4 style="margin-top:20px;">最近过站</h4>
        {% for r in recent %}
        <div class="item">[{{r.time}}] {{r.work_order}} {{r.rfid}} {{r.process}}</div>
        {% endfor %}
    </div>
</div>

<!-- 统一弹窗 -->
<div class="modal" id="procModal">
    <div class="modal-content">
        <div class="modal-header">
            <h3 id="modalTitle">工序详情</h3>
            <button class="close-btn" onclick="closeModal()">关闭</button>
        </div>
        <div id="modalBody"></div>
    </div>
</div>

<script>
    function updateClock(){document.getElementById('clock').innerText = new Date().toLocaleString();}
    setInterval(updateClock,1000); updateClock();

    function showMainProc(proc){
        document.getElementById('modalTitle').textContent = proc + " 详情";
        fetch('/process_detail?proc='+encodeURIComponent(proc))
        .then(r=>r.json()).then(data=>{
            let html = '';
            data.forEach(i=>{
                let cls = i.abnormal ? 'detail-abnormal' : '';
                html += `<div class="detail-item ${cls}">
                    [${i.time}] ${i.work_order} | ${i.rfid} | ${i.process} ${i.abnormal?'【异常】':''}
                </div>`;
            });
            document.getElementById('modalBody').innerHTML = html;
            document.getElementById('procModal').style.display = 'flex';
        });
    }

    function showSubProc(sub){
        document.getElementById('modalTitle').textContent = sub + " 详情";
        fetch('/sub_process_detail?sub_proc='+encodeURIComponent(sub))
        .then(r=>r.json()).then(data=>{
            let html = '';
            data.forEach(i=>{
                let cls = i.abnormal ? 'detail-abnormal' : '';
                html += `<div class="detail-item ${cls}">
                    [${i.time}] ${i.work_order} | ${i.rfid} | ${i.process} ${i.abnormal?'【异常】':''}
                </div>`;
            });
            document.getElementById('modalBody').innerHTML = html;
            document.getElementById('procModal').style.display = 'flex';
        });
    }

    function closeModal(){document.getElementById('procModal').style.display = 'none';}

    var partPie = echarts.init(document.getElementById('partPie'));
    partPie.setOption({
        backgroundColor:'transparent', title:{text:'零件加工',textStyle:{color:'#ccc'}},
        series:[{type:'pie',radius:['40%','70%'],data:{{ part_data|tojson }}}]
    });
    partPie.on('click', p=>showSubProc(p.name));

    var surfacePie = echarts.init(document.getElementById('surfacePie'));
    surfacePie.setOption({
        backgroundColor:'transparent', title:{text:'表面处理',textStyle:{color:'#ccc'}},
        series:[{type:'pie',radius:['40%','70%'],data:{{ surface_data|tojson }}}]
    });
    surfacePie.on('click', p=>showSubProc(p.name));

    window.addEventListener('resize', ()=>{ partPie.resize(); surfacePie.resize(); });
</script>
</body>
</html>
''',
    main_process=main_process, values=values, uptime_str=uptime_str,
    part_data=part_data, surface_data=surface_data,
    order_board=order_board, task_board=task_board,
    abnormal_list=abnormal_list, recent=recent
)

@app.route('/login', methods=['GET','POST'])
def login():
    msg = ""
    if request.method == 'POST':
        if request.form['user'] == 'ZZ22-SZY' and request.form['pwd'] == '123456':
            session['user'] = 'admin'
            return redirect('/')
        msg = "账号或密码错误"
    return render_template_string('''
<div style="max-width:400px;margin:60px auto;padding:40px;background:#1a1c2d;border-radius:20px;color:#eee">
    <h2 style="text-align:center;color:#4fc3f7">登录</h2>
    {% if msg %}<p style="color:red;text-align:center">{{msg}}</p>{% endif %}
    <form method="post">
        <input name="user" placeholder="账号" style="width:100%;padding:14px;margin:8px 0;background:#252a41;border:none;border-radius:12px;color:#fff">
        <input name="pwd" type="password" placeholder="密码" style="width:100%;padding:14px;margin:8px 0;background:#252a41;border:none;border-radius:12px;color:#fff">
        <button style="width:100%;padding:14px;background:linear-gradient(90deg,#2196F3,#00BCD4);color:white;border:none;border-radius:12px">登录</button>
    </form>
</div>
''', msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/scan', methods=['GET','POST'])
def scan():
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        rfid = request.form['rfid'].strip()
        wo = request.form['wo'].strip()
        proc = request.form['proc'].strip()
        mat = request.form['material'].strip()
        abnormal = request.form.get('abnormal') == 'on'
        if proc == "出库" and abnormal:
            return "<h3 style='color:red;text-align:center'>异常不可出库</h3>"
        wip_records.append({
            "rfid":rfid,"work_order":wo,"process":proc,"material":mat,
            "abnormal":abnormal,"time":datetime.datetime.now().strftime("%m-%d %H:%M:%S")
        })
        return redirect('/')
    return render_template_string('''
<div style="max-width:500px;margin:40px auto;padding:40px;background:#1a1c2d;border-radius:20px;color:#eee">
<a href="/" style="color:#4fc3f7">← 返回</a>
<h2>刷卡</h2>
<form method="post">
    <input name="rfid" placeholder="RFID" required style="width:100%;padding:14px;margin:8px 0;background:#252a41;border:none;border-radius:12px;color:#fff">
    <input name="wo" placeholder="工单号" required style="width:100%;padding:14px;margin:8px 0;background:#252a41;border:none;border-radius:12px;color:#fff">
    <input name="material" placeholder="物料" required style="width:100%;padding:14px;margin:8px 0;background:#252a41;border:none;border-radius:12px;color:#fff">
    <select name="proc" required style="width:100%;padding:14px;margin:8px 0;background:#252a41;border:none;border-radius:12px;color:#fff">
        <option>毛坯准备</option>
        <option>车削(零件加工)</option>
        <option>铣削(零件加工)</option>
        <option>磨削(零件加工)</option>
        <option>铰孔(零件加工)</option>
        <option>钻孔(零件加工)</option>
        <option>热处理</option>
        <option>氧化处理(表面处理)</option>
        <option>电镀(表面处理)</option>
        <option>涂装(表面处理)</option>
        <option>出库</option>
    </select>
    <label style="color:#ccc"><input type="checkbox" name="abnormal"> 异常</label>
    <button style="width:100%;padding:14px;background:linear-gradient(90deg,#2196F3,#00BCD4);color:white;border:none;border-radius:12px;margin-top:12px">提交</button>
</form>
</div>
''')

@app.route('/import', methods=['GET','POST'])
def import_page():
    if 'user' not in session: return redirect('/login')
    msg = ''
    if request.method == 'POST':
        f = request.files['file']
        s = io.StringIO(f.read().decode('utf-8'))
        reader = csv.reader(s)
        next(reader)
        for row in reader:
            if len(row)<4: continue
            rfid, wo, proc, mat = row[0], row[1], row[2], row[3]
            abnormal = len(row)>=5 and row[4].strip()=="是"
            if proc=="出库" and abnormal: continue
            wip_records.append({
                "rfid":rfid,"work_order":wo,"process":proc,"material":mat,
                "abnormal":abnormal,"time":datetime.datetime.now().strftime("%m-%d %H:%M:%S")
            })
        msg = "导入成功"
    return render_template_string('''
<div style="max-width:500px;margin:40px auto;padding:40px;background:#1a1c2d;border-radius:20px;color:#eee">
<a href="/" style="color:#4fc3f7">← 返回</a>
<h2>CSV导入</h2>
<p style="color:#999">格式：RFID,工单号,工序,物料,是否异常</p>
<form method="post" enctype="multipart/form-data">
    <input type="file" name="file" accept=".csv" style="color:#ccc;margin-bottom:16px">
    <button class="btn">导入</button>
</form>
<p style="color:#64ffda;margin-top:16px">{{msg}}</p>
</div>
''', msg=msg)

@app.route('/clear')
def clear():
    global wip_records
    wip_records = []
    return redirect('/')

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)