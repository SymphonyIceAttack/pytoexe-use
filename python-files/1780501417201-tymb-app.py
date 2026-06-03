import os, json, sqlite3, threading, webbrowser, datetime, hashlib
from flask import Flask, request, jsonify, render_template_string
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path.home() / "hq_data.db"
ACCESS_CODE = "224831"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        priority TEXT DEFAULT 'HIGH',
        status TEXT DEFAULT 'active',
        estimated_mins INTEGER DEFAULT 30,
        actual_mins INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT,
        due_date TEXT
    );
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'active',
        deadline TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS project_phases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        name TEXT,
        status TEXT DEFAULT 'pending',
        order_num INTEGER DEFAULT 0,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    );
    CREATE TABLE IF NOT EXISTS pomodoros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duration_mins INTEGER DEFAULT 25,
        mode TEXT DEFAULT 'deep',
        completed INTEGER DEFAULT 0,
        started_at TEXT DEFAULT (datetime('now')),
        ended_at TEXT
    );
    CREATE TABLE IF NOT EXISTS finances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT,
        amount REAL NOT NULL,
        description TEXT,
        date TEXT DEFAULT (date('now'))
    );
    CREATE TABLE IF NOT EXISTS vitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT DEFAULT (date('now')),
        sleep_hours REAL DEFAULT 0,
        sleep_quality INTEGER DEFAULT 0,
        water_ml INTEGER DEFAULT 0,
        calories INTEGER DEFAULT 0,
        workout_mins INTEGER DEFAULT 0,
        energy_level INTEGER DEFAULT 5,
        weight REAL
    );
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        streak INTEGER DEFAULT 0,
        last_checked TEXT,
        color TEXT DEFAULT '#4af'
    );
    CREATE TABLE IF NOT EXISTS habit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER,
        date TEXT DEFAULT (date('now')),
        FOREIGN KEY(habit_id) REFERENCES habits(id)
    );
    CREATE TABLE IF NOT EXISTS forge_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'skill',
        mastery INTEGER DEFAULT 0,
        sessions INTEGER DEFAULT 0,
        total_mins INTEGER DEFAULT 0,
        last_session TEXT,
        notes TEXT
    );
    CREATE TABLE IF NOT EXISTS forge_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        duration_mins INTEGER DEFAULT 30,
        quality INTEGER DEFAULT 3,
        notes TEXT,
        date TEXT DEFAULT (date('now')),
        FOREIGN KEY(item_id) REFERENCES forge_items(id)
    );
    CREATE TABLE IF NOT EXISTS social (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        relationship TEXT,
        last_contact TEXT,
        health INTEGER DEFAULT 100,
        notes TEXT,
        contact_frequency_days INTEGER DEFAULT 14
    );
    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        mood INTEGER DEFAULT 5,
        tags TEXT,
        is_shadow INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        type TEXT DEFAULT 'public',
        target_date TEXT,
        progress INTEGER DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS xp_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount INTEGER NOT NULL,
        source TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS war_room (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_start TEXT,
        wins TEXT,
        losses TEXT,
        priorities TEXT,
        battle_plan TEXT,
        jp_assessment TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    db.commit()
    db.close()

def award_xp(amount, source):
    db = get_db()
    db.execute("INSERT INTO xp_log (amount, source) VALUES (?, ?)", (amount, source))
    db.commit()
    db.close()

def get_total_xp():
    db = get_db()
    row = db.execute("SELECT COALESCE(SUM(amount),0) as total FROM xp_log").fetchone()
    db.close()
    return row["total"]

def xp_to_level(xp):
    levels = [
        (0, "Recruit"), (500, "Operator"), (1500, "Specialist"),
        (3500, "Ghost"), (7000, "Commander"), (15000, "Legend")
    ]
    level_num = 1
    rank = "Recruit"
    for threshold, name in levels:
        if xp >= threshold:
            level_num = levels.index((threshold, name)) + 1
            rank = name
    return level_num, rank

def compute_productivity_score():
    db = get_db()
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    tasks_done = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='done' AND completed_at >= ?", (week_ago,)).fetchone()["c"]
    tasks_total = db.execute("SELECT COUNT(*) as c FROM tasks WHERE created_at >= ?", (week_ago,)).fetchone()["c"]
    pomos = db.execute("SELECT COUNT(*) as c FROM pomodoros WHERE completed=1 AND started_at >= ?", (week_ago,)).fetchone()["c"]
    vitals_row = db.execute("SELECT AVG(energy_level) as e, AVG(sleep_hours) as s FROM vitals WHERE date >= ?", (week_ago,)).fetchone()
    db.close()
    task_score = (tasks_done / max(tasks_total, 1)) * 40
    pomo_score = min(pomos * 3, 30)
    energy = vitals_row["e"] or 5
    sleep = vitals_row["s"] or 6
    vitals_score = ((energy / 10) * 15) + (min(sleep / 8, 1) * 15)
    return round(task_score + pomo_score + vitals_score)

def compute_momentum():
    db = get_db()
    scores = []
    for i in range(7):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        tasks = db.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(completed_at)=?", (d,)).fetchone()["c"]
        pomos = db.execute("SELECT COUNT(*) as c FROM pomodoros WHERE completed=1 AND DATE(started_at)=?", (d,)).fetchone()["c"]
        vitals = db.execute("SELECT energy_level FROM vitals WHERE date=?", (d,)).fetchone()
        day_score = min((tasks * 10) + (pomos * 8) + ((vitals["energy_level"] if vitals else 5) * 2), 100)
        scores.append(day_score)
    db.close()
    return list(reversed(scores))

def compute_entropy():
    db = get_db()
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    planned = db.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(created_at) < ? AND created_at >= ?", (today, week_ago)).fetchone()["c"]
    unplanned = db.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(created_at)=?", (today,)).fetchone()["c"]
    overdue = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='active' AND due_date < ?", (today,)).fetchone()["c"]
    db.close()
    entropy = min(round((unplanned * 15) + (overdue * 20)), 100)
    if entropy < 25: label = "STABLE"
    elif entropy < 55: label = "ELEVATED"
    elif entropy < 80: label = "CHAOTIC"
    else: label = "CRITICAL"
    return entropy, label

def compute_cognitive_load():
    db = get_db()
    today = datetime.date.today().isoformat()
    added = db.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(created_at)=?", (today,)).fetchone()["c"]
    done = db.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(completed_at)=?", (today,)).fetchone()["c"]
    active = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='active'", ).fetchone()["c"]
    db.close()
    load = min(round((active * 8) + ((added - done) * 12)), 100)
    if load < 30: label = "COASTING"
    elif load < 65: label = "OPTIMAL"
    else: label = "OVERLOADED"
    return load, label

def jp_analyze(context_data):
    tasks = context_data.get("tasks", [])
    vitals = context_data.get("vitals", {})
    score = context_data.get("productivity_score", 0)
    momentum = context_data.get("momentum", [])
    entropy, entropy_label = compute_entropy()
    load, load_label = compute_cognitive_load()
    overdue = [t for t in tasks if t.get("status") == "active" and t.get("due_date") and t["due_date"] < datetime.date.today().isoformat()]
    critical = [t for t in tasks if t.get("priority") == "CRITICAL" and t.get("status") == "active"]
    avg_momentum = round(sum(momentum) / max(len(momentum), 1)) if momentum else 0
    response_parts = []
    if overdue:
        response_parts.append(f"Chief, I've identified {len(overdue)} overdue task{'s' if len(overdue)>1 else ''}. These are classified as active threats and require immediate attention.")
    if critical:
        response_parts.append(f"You have {len(critical)} critical priority item{'s' if len(critical)>1 else ''} pending. I recommend addressing those before anything else today.")
    if load_label == "OVERLOADED":
        response_parts.append("Your cognitive load is in the red zone. I strongly advise against adding new tasks until the backlog clears.")
    elif load_label == "COASTING":
        response_parts.append("You appear to be coasting, Chief. Productivity score suggests you have capacity for a high-value task.")
    if entropy_label in ["CHAOTIC", "CRITICAL"]:
        response_parts.append("Entropy levels are dangerously high. A system recalibration session is recommended — clear the backlog before planning new missions.")
    if avg_momentum < 30:
        response_parts.append("Your momentum index has been declining. Consistency is the variable, Chief. Even one completed task per day reverses the curve.")
    elif avg_momentum > 70:
        response_parts.append("Momentum index is strong. You are in an optimal performance window. Do not break the chain.")
    sleep = vitals.get("sleep_hours", 0)
    if sleep and sleep < 6:
        response_parts.append("Sleep data shows you are operating under-recovered. Cognitive performance degrades 20 percent below 6 hours. Factor that in.")
    if score > 75:
        response_parts.append(f"Overall productivity score stands at {score}. Excellent output, Chief.")
    elif score < 35:
        response_parts.append(f"Productivity score is at {score}. The system recommends a full reset: one focused pomodoro, one task completed, then reassess.")
    if not response_parts:
        response_parts.append("All systems nominal, Chief. No critical threats detected. Recommend maintaining current operational tempo.")
    return " ".join(response_parts)

def jp_respond_to_query(query, app_data):
    query_lower = query.lower()
    tasks = app_data.get("tasks", [])
    active_tasks = [t for t in tasks if t.get("status") == "active"]
    done_tasks = [t for t in tasks if t.get("status") == "done"]
    score = app_data.get("productivity_score", 0)
    momentum = app_data.get("momentum", [])
    xp = app_data.get("xp", 0)
    level, rank = xp_to_level(xp)
    entropy, entropy_label = compute_entropy()
    load, load_label = compute_cognitive_load()
    overdue = [t for t in active_tasks if t.get("due_date") and t["due_date"] < datetime.date.today().isoformat()]

    if any(w in query_lower for w in ["how am i", "status", "overview", "brief", "summary", "doing"]):
        return jp_analyze(app_data)
    if any(w in query_lower for w in ["task", "todo", "what should i", "what to do", "priority"]):
        if not active_tasks:
            return "Task queue is clear, Chief. Either you have conquered everything or you have not loaded your missions yet."
        critical = [t for t in active_tasks if t.get("priority") == "CRITICAL"]
        if critical:
            return f"Chief, I recommend starting with your {len(critical)} critical task{'s' if len(critical)>1 else ''}: {', '.join(t['title'] for t in critical[:3])}. After that, address the {len(active_tasks)-len(critical)} remaining items."
        return f"You have {len(active_tasks)} active tasks. Top priority: {active_tasks[0]['title']}. I recommend tackling the highest priority items before 2pm when cognitive sharpness typically declines."
    if any(w in query_lower for w in ["focus", "pomodoro", "work session", "concentrate"]):
        if load_label == "OVERLOADED":
            return "Chief, cognitive load is critical. A 25-minute deep work session on your top priority task is the prescription. Remove all distractions first."
        return "Recommend initiating a 25-minute deep work session. Your focus rate improves by approximately 40 percent when tasks are pre-selected before starting the timer. Choose your target now."
    if any(w in query_lower for w in ["motivation", "motivate", "inspire", "push me", "fire me up"]):
        motivations = [
            f"Chief, you are ranked {rank} with {xp} XP. Every task you complete today compounds. The gap between where you are and where you want to be closes one action at a time.",
            f"Your productivity score is {score}. That number is not your ceiling, it is your floor. You built it. Now exceed it.",
            f"Momentum index shows {'a strong upward' if sum(momentum[-3:])>sum(momentum[:3]) else 'a recoverable'} trend. The machine runs on consistency, Chief. Not perfection.",
            "Entropy is just chaos waiting to be organized. Every item you clear is a system restored. Get to work, Chief."
        ]
        import random
        return random.choice(motivations)
    if any(w in query_lower for w in ["xp", "level", "rank", "progress"]):
        return f"Current rank: {rank}. Level {level}. Total XP: {xp}. {'You are performing at peak rank capacity.' if rank == 'Legend' else 'Next promotion requires sustained performance across all modules.'}"
    if any(w in query_lower for w in ["sleep", "rest", "recovery", "tired"]):
        db = get_db()
        latest = db.execute("SELECT * FROM vitals ORDER BY date DESC LIMIT 1").fetchone()
        db.close()
        if latest and latest["sleep_hours"]:
            s = latest["sleep_hours"]
            if s < 6:
                return f"Last logged sleep was {s} hours, Chief. That is below operational threshold. Cognitive performance, memory consolidation, and decision quality are all compromised. Prioritize recovery tonight."
            elif s >= 8:
                return f"Sleep data shows {s} hours. You are well-recovered. Optimal window for deep work and complex decisions."
            else:
                return f"Sleep logged at {s} hours. Acceptable but not peak. Aim for 7.5 to 8 for full cognitive restoration."
        return "No sleep data logged yet, Chief. I recommend using the Vitals module to track recovery. It directly affects your performance score."
    if any(w in query_lower for w in ["finance", "money", "budget", "spend", "income"]):
        db = get_db()
        month_start = datetime.date.today().replace(day=1).isoformat()
        income = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='income' AND date >= ?", (month_start,)).fetchone()["t"]
        expenses = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='expense' AND date >= ?", (month_start,)).fetchone()["t"]
        db.close()
        balance = income - expenses
        if income == 0:
            return "No financial data logged this month yet, Chief. Head to Asset Tracker to begin monitoring your resources."
        return f"This month: income {income:.0f}, expenses {expenses:.0f}, net balance {balance:.0f}. {'Operational surplus detected.' if balance > 0 else 'Warning: expenditure exceeds income. Recalibration recommended.'}"
    if any(w in query_lower for w in ["hello", "hi ", "hey", "good morning", "good evening"]):
        hour = datetime.datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        return f"{greeting}, Chief. Systems are online. Productivity score at {score}. {len(active_tasks)} missions pending. How can I assist?"
    if any(w in query_lower for w in ["overdue", "late", "behind", "threat"]):
        if not overdue:
            return "No overdue items detected, Chief. All deadlines are either clear or have not been set. The threat matrix is clean."
        return f"Threat matrix shows {len(overdue)} overdue item{'s' if len(overdue)>1 else ''}: {', '.join(t['title'] for t in overdue[:3])}{'...' if len(overdue)>3 else ''}. These require immediate classification and action."
    if any(w in query_lower for w in ["plan my day", "today", "schedule"]):
        critical = [t for t in active_tasks if t.get("priority") == "CRITICAL"]
        high = [t for t in active_tasks if t.get("priority") == "HIGH"]
        return f"Daily operations briefing, Chief. {'Critical items: ' + ', '.join(t['title'] for t in critical[:2]) + '. ' if critical else ''}{'High priority queue: ' + ', '.join(t['title'] for t in high[:3]) + '. ' if high else ''}Recommend 3 focused pomodoro sessions. Avoid scheduling complex decisions after 4pm. Entropy is currently {entropy_label.lower()}."
    if any(w in query_lower for w in ["entropy", "chaos", "messy", "overwhelm"]):
        return f"Entropy scanner reads {entropy}/100 — status {entropy_label}. {'System is stable, Chief.' if entropy_label == 'STABLE' else 'I recommend a recalibration: clear completed items, consolidate overdue tasks, and run one focused session before adding anything new to the queue.'}"
    return f"Understood, Chief. I have analyzed your current data: {len(active_tasks)} active tasks, productivity at {score}, momentum {entropy_label.lower()}. If you need specific analysis, ask me about your tasks, focus, finances, vitals, or current threats."

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HQ — Command Center</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
:root {
--bg: #080a0f;
--bg2: #0d1117;
--bg3: #111820;
--border: rgba(255,255,255,0.07);
--border2: rgba(255,255,255,0.14);
--text: #c8d6e5;
--text2: #6b7f99;
--text3: #3d4f63;
--blue: #2d7dd2;
--blue-dim: #1a4a7a;
--blue-bright: #4a9eff;
--amber: #d4a017;
--amber-bright: #f5c842;
--red: #c0392b;
--red-bright: #e74c3c;
--green: #1a8a4a;
--green-bright: #27ae60;
--teal: #0e7c7b;
--teal-bright: #1abc9c;
--purple: #6c3483;
--purple-bright: #9b59b6;
--silver: #7f8c8d;
--silver-bright: #bdc3c7;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:'Rajdhani',sans-serif; font-size:15px; overflow-x:hidden; }
#lockscreen { position:fixed; inset:0; background:var(--bg); display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:9999; }
.lock-title { font-size:48px; font-weight:700; letter-spacing:12px; color:var(--blue-bright); margin-bottom:8px; font-family:'Share Tech Mono',monospace; }
.lock-sub { font-size:13px; letter-spacing:6px; color:var(--text2); margin-bottom:60px; }
.lock-input-wrap { position:relative; }
#lock-code { background:transparent; border:1px solid var(--border2); color:var(--text); font-family:'Share Tech Mono',monospace; font-size:28px; letter-spacing:16px; text-align:center; padding:16px 32px; width:280px; outline:none; }
#lock-code:focus { border-color:var(--blue); }
.lock-hint { font-size:11px; color:var(--text3); text-align:center; margin-top:12px; letter-spacing:3px; }
.lock-error { color:var(--red-bright); font-size:12px; text-align:center; margin-top:8px; letter-spacing:2px; display:none; }
#app { display:none; height:100vh; flex-direction:column; }
.topbar { background:var(--bg2); border-bottom:1px solid var(--border); padding:0 20px; height:48px; display:flex; align-items:center; gap:20px; flex-shrink:0; }
.topbar-brand { font-family:'Share Tech Mono',monospace; font-size:16px; color:var(--blue-bright); letter-spacing:4px; }
.topbar-sep { width:1px; height:24px; background:var(--border); }
.topbar-stats { display:flex; gap:16px; flex:1; }
.ts { font-size:12px; color:var(--text2); display:flex; align-items:center; gap:6px; }
.ts-val { color:var(--text); font-weight:600; }
.ts-dot { width:6px; height:6px; border-radius:50%; }
.topbar-right { display:flex; gap:8px; align-items:center; }
.jp-btn { background:transparent; border:1px solid var(--silver); color:var(--silver-bright); font-family:'Rajdhani',sans-serif; font-size:12px; letter-spacing:2px; padding:4px 12px; cursor:pointer; }
.jp-btn:hover { border-color:var(--silver-bright); }
.main-layout { display:flex; flex:1; overflow:hidden; }
.sidebar { width:52px; background:var(--bg2); border-right:1px solid var(--border); display:flex; flex-direction:column; align-items:center; padding:8px 0; gap:2px; flex-shrink:0; overflow-y:auto; }
.nav-item { width:40px; height:40px; display:flex; align-items:center; justify-content:center; cursor:pointer; border:1px solid transparent; font-size:11px; color:var(--text3); flex-direction:column; gap:2px; transition:all .15s; position:relative; }
.nav-item:hover { color:var(--text2); border-color:var(--border); background:var(--bg3); }
.nav-item.active { color:var(--blue-bright); border-color:var(--blue-dim); background:rgba(45,125,210,0.08); }
.nav-item svg { width:18px; height:18px; fill:none; stroke:currentColor; stroke-width:1.5; }
.nav-label { font-size:8px; letter-spacing:1px; }
.content { flex:1; overflow-y:auto; padding:20px; background:var(--bg); }
.module { display:none; }
.module.active { display:block; }
.mod-header { display:flex; align-items:center; gap:12px; margin-bottom:20px; border-bottom:1px solid var(--border); padding-bottom:12px; }
.mod-title { font-size:22px; font-weight:700; letter-spacing:4px; }
.mod-badge { font-size:10px; letter-spacing:3px; padding:3px 10px; border:1px solid; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }
.grid3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:16px; }
.grid4 { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.card { background:var(--bg2); border:1px solid var(--border); padding:16px; }
.card-title { font-size:11px; letter-spacing:3px; color:var(--text2); margin-bottom:12px; }
.stat-big { font-size:36px; font-weight:700; line-height:1; }
.stat-label { font-size:11px; color:var(--text2); letter-spacing:2px; margin-top:4px; }
.mini-stat { background:var(--bg3); padding:12px; display:flex; flex-direction:column; gap:4px; }
.mini-val { font-size:24px; font-weight:700; font-family:'Share Tech Mono',monospace; }
.mini-lbl { font-size:10px; letter-spacing:2px; color:var(--text2); }
.progress-bar { height:4px; background:var(--bg3); margin-top:8px; }
.progress-fill { height:100%; transition:width .5s; }
.ring-wrap { display:flex; flex-direction:column; align-items:center; gap:8px; }
.ring-label { font-size:10px; letter-spacing:2px; color:var(--text2); }
input[type=text], input[type=number], input[type=date], select, textarea {
background:var(--bg3); border:1px solid var(--border); color:var(--text); font-family:'Rajdhani',sans-serif; font-size:14px; padding:8px 12px; outline:none; width:100%;
}
input:focus, select:focus, textarea:focus { border-color:var(--blue); }
.btn { background:transparent; border:1px solid var(--border2); color:var(--text); font-family:'Rajdhani',sans-serif; font-size:13px; letter-spacing:2px; padding:8px 20px; cursor:pointer; transition:all .15s; }
.btn:hover { background:var(--bg3); border-color:var(--border2); }
.btn-primary { border-color:var(--blue); color:var(--blue-bright); }
.btn-primary:hover { background:rgba(45,125,210,0.15); }
.btn-danger { border-color:var(--red); color:var(--red-bright); }
.btn-success { border-color:var(--green); color:var(--green-bright); }
.btn-sm { padding:4px 12px; font-size:11px; }
.task-list { display:flex; flex-direction:column; gap:6px; }
.task-item { background:var(--bg3); border:1px solid var(--border); padding:10px 14px; display:flex; align-items:center; gap:12px; transition:all .2s; }
.task-item:hover { border-color:var(--border2); }
.task-item.done { opacity:0.4; }
.task-check { width:16px; height:16px; border:1px solid var(--text2); cursor:pointer; flex-shrink:0; display:flex; align-items:center; justify-content:center; }
.task-check.checked { background:var(--green); border-color:var(--green); }
.task-title { flex:1; font-size:14px; }
.task-title.done-txt { text-decoration:line-through; color:var(--text2); }
.priority-badge { font-size:9px; letter-spacing:2px; padding:2px 8px; }
.p-critical { background:rgba(192,57,43,0.2); color:var(--red-bright); border:1px solid var(--red); }
.p-high { background:rgba(212,160,23,0.2); color:var(--amber-bright); border:1px solid var(--amber); }
.p-low { background:rgba(26,138,74,0.2); color:var(--green-bright); border:1px solid var(--green); }
.quick-add { display:flex; gap:8px; margin-bottom:16px; }
.quick-add input { flex:1; }
.threat-item { background:var(--bg3); border-left:3px solid; padding:10px 14px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center; }
.threat-critical { border-color:var(--red-bright); }
.threat-elevated { border-color:var(--amber-bright); }
.threat-low { border-color:var(--green-bright); }
.pomo-display { text-align:center; padding:30px 0; }
.pomo-time { font-family:'Share Tech Mono',monospace; font-size:72px; font-weight:400; color:var(--red-bright); letter-spacing:4px; }
.pomo-ring { width:200px; height:200px; margin:0 auto 20px; position:relative; }
.pomo-ring svg { transform:rotate(-90deg); }
.pomo-ring-text { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.pomo-controls { display:flex; gap:12px; justify-content:center; margin-top:20px; }
.jp-panel { background:var(--bg2); border:1px solid var(--silver); padding:16px; height:420px; display:flex; flex-direction:column; }
.jp-messages { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; margin-bottom:12px; padding-right:4px; }
.jp-msg { padding:10px 14px; max-width:85%; font-size:13px; line-height:1.6; }
.jp-msg.jp { background:var(--bg3); border-left:2px solid var(--silver); align-self:flex-start; color:var(--silver-bright); }
.jp-msg.user { background:rgba(45,125,210,0.1); border-left:2px solid var(--blue); align-self:flex-end; color:var(--blue-bright); }
.jp-msg-name { font-size:10px; letter-spacing:2px; margin-bottom:4px; color:var(--text2); }
.jp-input-row { display:flex; gap:8px; }
.jp-input-row input { flex:1; }
.heatmap { display:grid; grid-template-columns:repeat(7,1fr); gap:3px; }
.hm-cell { height:24px; background:var(--bg3); transition:background .3s; }
.gauge-wrap { position:relative; display:flex; flex-direction:column; align-items:center; }
.gauge-label { font-size:10px; letter-spacing:2px; color:var(--text2); margin-top:8px; }
.gauge-val { font-family:'Share Tech Mono',monospace; font-size:20px; font-weight:400; }
.waveform { display:flex; align-items:flex-end; gap:3px; height:60px; }
.wv-bar { flex:1; background:var(--blue-dim); transition:height .5s, background .3s; min-height:4px; }
.xp-bar-wrap { background:var(--bg3); height:8px; margin:8px 0; position:relative; }
.xp-fill { height:100%; background:var(--purple-bright); transition:width .8s; }
.finance-row { display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border); font-size:13px; }
.income-val { color:var(--green-bright); }
.expense-val { color:var(--red-bright); }
.social-item { background:var(--bg3); border:1px solid var(--border); padding:12px 14px; display:flex; gap:12px; align-items:center; margin-bottom:6px; }
.social-avatar { width:36px; height:36px; background:var(--bg2); border:1px solid var(--border2); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0; }
.health-bar { height:3px; background:var(--bg); margin-top:4px; }
.health-fill { height:100%; transition:width .4s; }
.forge-item { background:var(--bg3); border:1px solid var(--border); padding:14px; margin-bottom:8px; }
.mastery-ring-row { display:flex; gap:16px; flex-wrap:wrap; }
.journal-entry { background:var(--bg3); border-left:2px solid var(--purple); padding:12px 16px; margin-bottom:8px; }
.journal-date { font-size:10px; color:var(--text3); letter-spacing:2px; margin-bottom:6px; }
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:1000; display:none; align-items:center; justify-content:center; }
.modal-overlay.show { display:flex; }
.modal { background:var(--bg2); border:1px solid var(--border2); padding:24px; width:460px; max-width:95vw; }
.modal-title { font-size:16px; font-weight:700; letter-spacing:4px; margin-bottom:20px; }
.form-row { margin-bottom:12px; }
.form-label { font-size:11px; letter-spacing:2px; color:var(--text2); margin-bottom:6px; display:block; }
.form-row-inline { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px; }
.modal-btns { display:flex; gap:8px; justify-content:flex-end; margin-top:20px; }
.notification { position:fixed; bottom:20px; right:20px; background:var(--bg2); border:1px solid var(--border2); padding:12px 20px; z-index:2000; font-size:13px; letter-spacing:1px; transform:translateX(120%); transition:transform .3s; max-width:320px; }
.notification.show { transform:translateX(0); }
.notification.jp-notif { border-color:var(--silver); color:var(--silver-bright); }
.section-divider { height:1px; background:var(--border); margin:16px 0; }
.chart-wrap { position:relative; margin-top:12px; }
.tag { font-size:10px; letter-spacing:2px; padding:2px 8px; border:1px solid var(--border); color:var(--text2); display:inline-block; margin:2px; }
.war-room-step { background:var(--bg3); border:1px solid var(--border); padding:14px; margin-bottom:10px; }
.war-step-num { font-family:'Share Tech Mono',monospace; font-size:11px; color:var(--blue-bright); margin-bottom:6px; letter-spacing:2px; }
.dossier-section { border-left:2px solid var(--border2); padding-left:14px; margin-bottom:16px; }
.goal-item { background:var(--bg3); border:1px solid var(--border); padding:12px 14px; margin-bottom:6px; }
.radar-wrap { display:flex; justify-content:center; margin:12px 0; }
.chrono-mode-btn { padding:6px 16px; border:1px solid var(--border); cursor:pointer; font-family:'Rajdhani',sans-serif; font-size:12px; letter-spacing:2px; background:transparent; color:var(--text2); }
.chrono-mode-btn.active { border-color:var(--red); color:var(--red-bright); background:rgba(192,57,43,0.1); }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border2); }
.scan-line { position:fixed; top:0; left:0; right:0; height:2px; background:rgba(45,125,210,0.3); animation:scan 4s linear infinite; pointer-events:none; z-index:9998; }
@keyframes scan { 0%{top:0} 100%{top:100vh} }
.blink { animation:blink 1.2s step-end infinite; }
@keyframes blink { 50%{opacity:0} }
</style>
</head>
<body>
<div class="scan-line"></div>

<div id="lockscreen">
  <div class="lock-title">H Q</div>
  <div class="lock-sub">COMMAND CENTER v1.0</div>
  <div class="lock-input-wrap">
    <input type="password" id="lock-code" placeholder="______" maxlength="6" autocomplete="off">
  </div>
  <div class="lock-hint">ENTER ACCESS CODE</div>
  <div class="lock-error" id="lock-err">ACCESS DENIED — INVALID CODE</div>
</div>

<div id="app">
  <div class="topbar">
    <div class="topbar-brand">HQ</div>
    <div class="topbar-sep"></div>
    <div class="topbar-stats">
      <div class="ts"><div class="ts-dot" style="background:var(--blue-bright)"></div>SCORE <span class="ts-val" id="tb-score">0</span></div>
      <div class="ts"><div class="ts-dot" style="background:var(--purple-bright)"></div>XP <span class="ts-val" id="tb-xp">0</span></div>
      <div class="ts"><div class="ts-dot" style="background:var(--amber-bright)"></div>RANK <span class="ts-val" id="tb-rank">Recruit</span></div>
      <div class="ts"><div class="ts-dot" style="background:var(--red-bright)" id="tb-threat-dot"></div>THREATS <span class="ts-val" id="tb-threats">0</span></div>
      <div class="ts"><div class="ts-dot" style="background:var(--teal-bright)"></div>LOAD <span class="ts-val" id="tb-load">--</span></div>
    </div>
    <div class="topbar-right">
      <div style="font-size:11px;color:var(--silver);letter-spacing:2px;" id="tb-time"></div>
      <button class="jp-btn" onclick="openJP()">JEAN-PHILIP</button>
    </div>
  </div>
  <div class="main-layout">
    <div class="sidebar" id="sidebar">
      <div class="nav-item active" data-mod="dashboard" onclick="switchMod(this)" title="Dashboard">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
        <span class="nav-label">HQ</span>
      </div>
      <div class="nav-item" data-mod="dailyops" onclick="switchMod(this)" title="Daily Ops">
        <svg viewBox="0 0 24 24"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
        <span class="nav-label">OPS</span>
      </div>
      <div class="nav-item" data-mod="missions" onclick="switchMod(this)" title="Mission Control">
        <svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        <span class="nav-label">MSNS</span>
      </div>
      <div class="nav-item" data-mod="chrono" onclick="switchMod(this)" title="Chrono">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
        <span class="nav-label">TIME</span>
      </div>
      <div class="nav-item" data-mod="assets" onclick="switchMod(this)" title="Asset Tracker">
        <svg viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6"/></svg>
        <span class="nav-label">ASST</span>
      </div>
      <div class="nav-item" data-mod="vitals" onclick="switchMod(this)" title="Vitals">
        <svg viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        <span class="nav-label">VTAL</span>
      </div>
      <div class="nav-item" data-mod="opstats" onclick="switchMod(this)" title="Operator Stats">
        <svg viewBox="0 0 24 24"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
        <span class="nav-label">STAT</span>
      </div>
      <div class="nav-item" data-mod="intel" onclick="switchMod(this)" title="Intel / Jean-Philip">
        <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        <span class="nav-label">INTL</span>
      </div>
      <div class="nav-item" data-mod="forge" onclick="switchMod(this)" title="Forge">
        <svg viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>
        <span class="nav-label">FRGE</span>
      </div>
      <div class="nav-item" data-mod="social" onclick="switchMod(this)" title="Social Command">
        <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
        <span class="nav-label">SOCL</span>
      </div>
      <div class="nav-item" data-mod="vault" onclick="switchMod(this)" title="Mind Vault">
        <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
        <span class="nav-label">VULT</span>
      </div>
      <div class="nav-item" data-mod="goals" onclick="switchMod(this)" title="Shadow Goals">
        <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
        <span class="nav-label">GOAL</span>
      </div>
      <div class="nav-item" data-mod="warroom" onclick="switchMod(this)" title="War Room">
        <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><path d="M9 22V12h6v10"/></svg>
        <span class="nav-label">WAR</span>
      </div>
    </div>

    <div class="content">

      <!-- DASHBOARD -->
      <div class="module active" id="mod-dashboard">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--blue-bright)">COMMAND CENTER</div>
          <div class="mod-badge" style="border-color:var(--blue);color:var(--blue-bright)" id="dash-date"></div>
        </div>
        <div class="grid4">
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--blue-bright)" id="d-score">0</div>
            <div class="mini-lbl">PRODUCTIVITY</div>
            <div class="progress-bar"><div class="progress-fill" style="background:var(--blue-bright)" id="d-score-bar"></div></div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--purple-bright)" id="d-xp">0</div>
            <div class="mini-lbl">TOTAL XP</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--amber-bright)" id="d-tasks">0</div>
            <div class="mini-lbl">ACTIVE TASKS</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" id="d-threats" style="color:var(--red-bright)">0</div>
            <div class="mini-lbl">THREATS</div>
          </div>
        </div>
        <div class="grid2">
          <div class="card">
            <div class="card-title">MOMENTUM INDEX — 7D</div>
            <div class="waveform" id="momentum-wave"></div>
            <div style="font-size:10px;color:var(--text3);margin-top:6px;letter-spacing:2px;">MON — SUN</div>
          </div>
          <div class="card">
            <div class="card-title">SYSTEM STATUS</div>
            <div id="system-status-list"></div>
          </div>
        </div>
        <div class="grid3">
          <div class="card">
            <div class="card-title">COGNITIVE LOAD</div>
            <div class="gauge-wrap">
              <canvas id="gauge-load" width="120" height="70"></canvas>
              <div class="gauge-val" id="gauge-load-val" style="color:var(--amber-bright)">--</div>
              <div class="gauge-label" id="gauge-load-lbl">CALCULATING</div>
            </div>
          </div>
          <div class="card">
            <div class="card-title">ENTROPY SCANNER</div>
            <div class="gauge-wrap">
              <canvas id="gauge-entropy" width="120" height="70"></canvas>
              <div class="gauge-val" id="gauge-entropy-val" style="color:var(--teal-bright)">--</div>
              <div class="gauge-label" id="gauge-entropy-lbl">SCANNING</div>
            </div>
          </div>
          <div class="card">
            <div class="card-title">OPERATOR RANK</div>
            <div style="text-align:center;padding:8px 0">
              <div style="font-size:28px;font-weight:700;letter-spacing:4px;color:var(--purple-bright)" id="d-rank">--</div>
              <div style="font-size:11px;color:var(--text2);letter-spacing:2px;margin-top:4px">LEVEL <span id="d-level">1</span></div>
              <div class="xp-bar-wrap" style="margin:12px 0 4px"><div class="xp-fill" id="d-xp-bar" style="width:0%"></div></div>
              <div style="font-size:10px;color:var(--text3);letter-spacing:1px"><span id="d-xp-cur">0</span> / <span id="d-xp-next">500</span> XP</div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">THREAT MATRIX</div>
          <div id="threat-matrix-list"></div>
        </div>
        <div class="card" style="margin-top:16px">
          <div class="card-title">JEAN-PHILIP — MORNING BRIEFING</div>
          <div id="jp-briefing" style="font-size:13px;color:var(--silver-bright);line-height:1.8;font-style:italic;min-height:40px">Analyzing systems, Chief...</div>
          <button class="btn btn-sm" style="margin-top:10px;border-color:var(--silver);color:var(--silver)" onclick="runBriefing()">REFRESH BRIEFING</button>
          <button class="btn btn-sm" style="margin-top:10px;border-color:var(--silver);color:var(--silver);margin-left:8px" onclick="speakBriefing()">SPEAK</button>
        </div>
      </div>

      <!-- DAILY OPS -->
      <div class="module" id="mod-dailyops">
        <div class="mod-header">
          <div class="mod-title" style="color:#4a9eff">DAILY OPS</div>
          <div class="mod-badge" style="border-color:#4a9eff;color:#4a9eff">TASKS</div>
        </div>
        <div class="quick-add">
          <input type="text" id="task-input" placeholder="QUICK DUMP — TYPE TASK AND HIT ENTER" onkeydown="if(event.key==='Enter')addTask()">
          <select id="task-priority" style="width:130px">
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH" selected>HIGH</option>
            <option value="LOW">LOW</option>
          </select>
          <input type="date" id="task-due" style="width:150px">
          <input type="number" id="task-est" placeholder="MINS" style="width:80px" value="30">
          <button class="btn btn-primary" onclick="addTask()">ADD</button>
        </div>
        <div class="grid3" style="margin-bottom:16px">
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--red-bright)" id="tasks-critical">0</div>
            <div class="mini-lbl">CRITICAL</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--amber-bright)" id="tasks-active">0</div>
            <div class="mini-lbl">ACTIVE</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--green-bright)" id="tasks-done-today">0</div>
            <div class="mini-lbl">DONE TODAY</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:12px">
          <button class="btn btn-sm active" onclick="filterTasks('active',this)" id="filter-active">ACTIVE</button>
          <button class="btn btn-sm" onclick="filterTasks('done',this)" id="filter-done">COMPLETED</button>
          <button class="btn btn-sm" onclick="filterTasks('all',this)">ALL</button>
        </div>
        <div class="task-list" id="task-list"></div>
        <div style="margin-top:16px">
          <div class="card-title">END-OF-DAY EFFICIENCY</div>
          <div id="eod-efficiency" style="font-size:13px;color:var(--text2);margin-top:8px"></div>
        </div>
      </div>

      <!-- MISSIONS -->
      <div class="module" id="mod-missions">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--amber-bright)">MISSION CONTROL</div>
          <div class="mod-badge" style="border-color:var(--amber);color:var(--amber-bright)">PROJECTS</div>
        </div>
        <button class="btn btn-primary" style="margin-bottom:16px" onclick="openModal('modal-project')">+ NEW MISSION</button>
        <div id="project-list"></div>
      </div>

      <!-- CHRONO -->
      <div class="module" id="mod-chrono">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--red-bright)">CHRONO</div>
          <div class="mod-badge" style="border-color:var(--red);color:var(--red-bright)">FOCUS ENGINE</div>
        </div>
        <div class="grid2">
          <div class="card">
            <div style="display:flex;gap:8px;justify-content:center;margin-bottom:20px">
              <button class="chrono-mode-btn active" id="mode-deep" onclick="setPomoMode('deep',this)">DEEP WORK</button>
              <button class="chrono-mode-btn" id="mode-shallow" onclick="setPomoMode('shallow',this)">SHALLOW</button>
              <button class="chrono-mode-btn" id="mode-break" onclick="setPomoMode('break',this)">BREAK</button>
            </div>
            <div class="pomo-display">
              <div class="pomo-ring">
                <svg width="200" height="200" viewBox="0 0 200 200">
                  <circle cx="100" cy="100" r="88" fill="none" stroke="#1a2030" stroke-width="8"/>
                  <circle id="pomo-arc" cx="100" cy="100" r="88" fill="none" stroke="#c0392b" stroke-width="8" stroke-dasharray="553" stroke-dashoffset="0" stroke-linecap="round"/>
                </svg>
                <div class="pomo-ring-text">
                  <div class="pomo-time" id="pomo-display">25:00</div>
                  <div style="font-size:10px;letter-spacing:3px;color:var(--text2)" id="pomo-mode-lbl">DEEP WORK</div>
                </div>
              </div>
              <div class="pomo-controls">
                <button class="btn" onclick="pomoStart()" id="pomo-start-btn">START</button>
                <button class="btn" onclick="pomoPause()" id="pomo-pause-btn" style="display:none">PAUSE</button>
                <button class="btn btn-danger" onclick="pomoReset()">RESET</button>
              </div>
            </div>
            <div style="display:flex;gap:12px;justify-content:center;margin-top:12px">
              <div class="mini-stat" style="text-align:center;min-width:80px">
                <div class="mini-val" style="color:var(--red-bright)" id="pomo-count">0</div>
                <div class="mini-lbl">TODAY</div>
              </div>
              <div class="mini-stat" style="text-align:center;min-width:80px">
                <div class="mini-val" style="color:var(--amber-bright)" id="pomo-streak">0</div>
                <div class="mini-lbl">STREAK</div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-title">FLOW STATE DETECTOR</div>
            <div id="flow-state-display" style="padding:20px 0;text-align:center">
              <div style="font-size:32px;font-weight:700;letter-spacing:4px;color:var(--text3)" id="flow-status">INACTIVE</div>
              <div style="font-size:11px;color:var(--text3);letter-spacing:2px;margin-top:8px" id="flow-desc">Complete 3 sessions to detect flow</div>
            </div>
            <div class="section-divider"></div>
            <div class="card-title">AMBIENT SOUND</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
              <button class="btn btn-sm" onclick="setAmbient('off')" id="amb-off" style="border-color:var(--blue);color:var(--blue-bright)">SILENCE</button>
              <button class="btn btn-sm" onclick="setAmbient('white')">WHITE NOISE</button>
              <button class="btn btn-sm" onclick="setAmbient('rain')">RAIN</button>
              <button class="btn btn-sm" onclick="setAmbient('focus')">FOCUS</button>
            </div>
            <div class="section-divider"></div>
            <div class="card-title">CUSTOM DURATION</div>
            <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
              <input type="number" id="custom-mins" value="25" min="1" max="120" style="width:80px">
              <span style="font-size:12px;color:var(--text2);letter-spacing:2px">MINUTES</span>
              <button class="btn btn-sm" onclick="setCustomMins()">SET</button>
            </div>
          </div>
        </div>
        <div class="card" style="margin-top:0">
          <div class="card-title">SESSION HISTORY — THIS WEEK</div>
          <div class="chart-wrap" style="height:160px">
            <canvas id="pomo-chart" role="img" aria-label="Pomodoro sessions per day this week">Weekly pomodoro data</canvas>
          </div>
        </div>
      </div>

      <!-- ASSETS -->
      <div class="module" id="mod-assets">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--green-bright)">ASSET TRACKER</div>
          <div class="mod-badge" style="border-color:var(--green);color:var(--green-bright)">FINANCE</div>
        </div>
        <div class="grid4">
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--green-bright)" id="fin-income">0</div>
            <div class="mini-lbl">INCOME (MO)</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--red-bright)" id="fin-expenses">0</div>
            <div class="mini-lbl">EXPENSES (MO)</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" id="fin-balance">0</div>
            <div class="mini-lbl">NET BALANCE</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--amber-bright)" id="fin-runway">--</div>
            <div class="mini-lbl">RUNWAY (MO)</div>
          </div>
        </div>
        <div class="quick-add" style="margin-bottom:16px">
          <select id="fin-type" style="width:120px">
            <option value="income">INCOME</option>
            <option value="expense">EXPENSE</option>
          </select>
          <input type="text" id="fin-desc" placeholder="DESCRIPTION" style="flex:1">
          <input type="number" id="fin-amount" placeholder="AMOUNT" style="width:120px">
          <select id="fin-cat" style="width:140px">
            <option value="salary">SALARY</option>
            <option value="freelance">FREELANCE</option>
            <option value="food">FOOD</option>
            <option value="transport">TRANSPORT</option>
            <option value="utilities">UTILITIES</option>
            <option value="entertainment">ENTERTAINMENT</option>
            <option value="health">HEALTH</option>
            <option value="other">OTHER</option>
          </select>
          <input type="date" id="fin-date" style="width:150px">
          <button class="btn btn-success" onclick="addFinance()">LOG</button>
        </div>
        <div class="grid2">
          <div class="card">
            <div class="card-title">MONTHLY BREAKDOWN</div>
            <div class="chart-wrap" style="height:200px">
              <canvas id="fin-chart" role="img" aria-label="Monthly income vs expenses">Finance chart</canvas>
            </div>
          </div>
          <div class="card">
            <div class="card-title">WEALTH TRAJECTORY</div>
            <div id="wealth-trajectory" style="font-size:13px;color:var(--text2);line-height:2"></div>
          </div>
        </div>
        <div class="card" style="margin-top:0">
          <div class="card-title">TRANSACTION LOG</div>
          <div id="fin-log"></div>
        </div>
      </div>

      <!-- VITALS -->
      <div class="module" id="mod-vitals">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--teal-bright)">VITALS</div>
          <div class="mod-badge" style="border-color:var(--teal);color:var(--teal-bright)">HEALTH MATRIX</div>
        </div>
        <div class="grid4">
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--teal-bright)" id="v-sleep">--</div>
            <div class="mini-lbl">SLEEP HRS</div>
            <div class="progress-bar"><div class="progress-fill" style="background:var(--teal-bright)" id="v-sleep-bar"></div></div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--blue-bright)" id="v-water">--</div>
            <div class="mini-lbl">WATER ML</div>
            <div class="progress-bar"><div class="progress-fill" style="background:var(--blue-bright)" id="v-water-bar"></div></div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--amber-bright)" id="v-calories">--</div>
            <div class="mini-lbl">CALORIES</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--green-bright)" id="v-workout">--</div>
            <div class="mini-lbl">WORKOUT MINS</div>
          </div>
        </div>
        <div class="grid2">
          <div class="card">
            <div class="card-title">LOG TODAY'S VITALS</div>
            <div class="form-row-inline">
              <div><label class="form-label">SLEEP HOURS</label><input type="number" id="v-in-sleep" min="0" max="24" step="0.5" placeholder="7.5"></div>
              <div><label class="form-label">SLEEP QUALITY (1-10)</label><input type="number" id="v-in-quality" min="1" max="10" placeholder="7"></div>
            </div>
            <div class="form-row-inline">
              <div><label class="form-label">WATER (ML)</label><input type="number" id="v-in-water" placeholder="2000"></div>
              <div><label class="form-label">CALORIES</label><input type="number" id="v-in-calories" placeholder="2200"></div>
            </div>
            <div class="form-row-inline">
              <div><label class="form-label">WORKOUT MINS</label><input type="number" id="v-in-workout" placeholder="45"></div>
              <div><label class="form-label">ENERGY LEVEL (1-10)</label><input type="number" id="v-in-energy" min="1" max="10" placeholder="7"></div>
            </div>
            <div class="form-row">
              <label class="form-label">WEIGHT (KG)</label>
              <input type="number" id="v-in-weight" step="0.1" placeholder="optional">
            </div>
            <button class="btn btn-primary" onclick="logVitals()" style="width:100%;margin-top:8px">LOG VITALS</button>
          </div>
          <div class="card">
            <div class="card-title">PEAK PERFORMANCE WINDOW</div>
            <div id="peak-window" style="font-size:13px;color:var(--text2);line-height:2;padding:8px 0"></div>
            <div class="section-divider"></div>
            <div class="card-title">RECOVERY SCORE</div>
            <div style="display:flex;align-items:center;gap:16px;padding:8px 0">
              <div style="font-size:36px;font-weight:700;color:var(--teal-bright)" id="recovery-score">--</div>
              <div style="font-size:12px;color:var(--text2)" id="recovery-label">LOG DATA TO CALCULATE</div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">7-DAY VITALS TREND</div>
          <div class="chart-wrap" style="height:200px">
            <canvas id="vitals-chart" role="img" aria-label="7 day vitals trend">Vitals trend chart</canvas>
          </div>
        </div>
      </div>

      <!-- OPERATOR STATS -->
      <div class="module" id="mod-opstats">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--purple-bright)">OPERATOR STATS</div>
          <div class="mod-badge" style="border-color:var(--purple);color:var(--purple-bright)">HUD</div>
        </div>
        <div class="grid4">
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--purple-bright)" id="os-xp">0</div>
            <div class="mini-lbl">TOTAL XP</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--amber-bright)" id="os-rank">--</div>
            <div class="mini-lbl">RANK</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--blue-bright)" id="os-score">0</div>
            <div class="mini-lbl">PROD SCORE</div>
          </div>
          <div class="mini-stat">
            <div class="mini-val" style="color:var(--green-bright)" id="os-streak">0</div>
            <div class="mini-lbl">DAY STREAK</div>
          </div>
        </div>
        <div class="grid2">
          <div class="card">
            <div class="card-title">ACTIVITY HEATMAP — 28 DAYS</div>
            <div class="heatmap" id="heatmap" style="margin-top:8px"></div>
            <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
              <span style="font-size:10px;color:var(--text3)">LOW</span>
              <div style="width:12px;height:12px;background:var(--bg3)"></div>
              <div style="width:12px;height:12px;background:#1a4a7a"></div>
              <div style="width:12px;height:12px;background:#2d7dd2"></div>
              <div style="width:12px;height:12px;background:#4a9eff"></div>
              <span style="font-size:10px;color:var(--text3)">HIGH</span>
            </div>
          </div>
          <div class="card">
            <div class="card-title">LIFE RADAR — PENTAGON</div>
            <div class="radar-wrap">
              <canvas id="radar-chart" width="220" height="200" role="img" aria-label="Life performance radar chart">Radar chart of life areas</canvas>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">PERSONAL RECORDS</div>
          <div id="personal-records" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:8px"></div>
        </div>
        <div class="card" style="margin-top:16px">
          <div class="card-title">CHRONOBIOLOGY OPTIMIZER</div>
          <div id="chrono-optimizer" style="font-size:13px;color:var(--text2);line-height:2;padding:8px 0"></div>
        </div>
      </div>

      <!-- INTEL -->
      <div class="module" id="mod-intel">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--silver-bright)">INTEL</div>
          <div class="mod-badge" style="border-color:var(--silver);color:var(--silver-bright)">JEAN-PHILIP</div>
        </div>
        <div class="jp-panel" style="height:500px">
          <div style="font-size:11px;letter-spacing:3px;color:var(--silver);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <div style="width:8px;height:8px;border-radius:50%;background:var(--green-bright)" class="blink"></div>
            JEAN-PHILIP — ONLINE
          </div>
          <div class="jp-messages" id="jp-messages"></div>
          <div class="jp-input-row">
            <input type="text" id="jp-query" placeholder="SPEAK TO JEAN-PHILIP..." onkeydown="if(event.key==='Enter')sendToJP()">
            <button class="btn" onclick="startVoiceInput()" id="voice-btn">MIC</button>
            <button class="btn" style="border-color:var(--silver);color:var(--silver-bright)" onclick="sendToJP()">SEND</button>
          </div>
        </div>
        <div class="card" style="margin-top:16px">
          <div class="card-title">DECISION ENGINE</div>
          <div style="font-size:12px;color:var(--text2);margin-bottom:8px;letter-spacing:1px">Describe a decision. Jean-Philip analyzes it against your current data.</div>
          <textarea id="decision-input" rows="3" placeholder="I need to decide whether to..."></textarea>
          <button class="btn btn-primary" style="margin-top:8px" onclick="analyzeDecision()">ANALYZE DECISION</button>
          <div id="decision-output" style="font-size:13px;color:var(--silver-bright);line-height:1.8;margin-top:12px;font-style:italic"></div>
        </div>
      </div>

      <!-- FORGE -->
      <div class="module" id="mod-forge">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--amber-bright)">FORGE</div>
          <div class="mod-badge" style="border-color:var(--amber);color:var(--amber-bright)">SKILLS + HOBBIES</div>
        </div>
        <button class="btn btn-primary" style="margin-bottom:16px" onclick="openModal('modal-forge')">+ NEW SKILL / HOBBY</button>
        <div id="forge-list"></div>
      </div>

      <!-- SOCIAL -->
      <div class="module" id="mod-social">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--teal-bright)">SOCIAL COMMAND</div>
          <div class="mod-badge" style="border-color:var(--teal);color:var(--teal-bright)">NETWORK</div>
        </div>
        <button class="btn btn-primary" style="margin-bottom:16px" onclick="openModal('modal-social')">+ ADD CONTACT</button>
        <div id="social-list"></div>
      </div>

      <!-- VAULT -->
      <div class="module" id="mod-vault">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--purple-bright)">MIND VAULT</div>
          <div class="mod-badge" style="border-color:var(--purple);color:var(--purple-bright)">PRIVATE</div>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:16px">
          <button class="btn btn-sm active" id="vault-public-btn" onclick="setVaultMode(0,this)">PUBLIC ENTRIES</button>
          <button class="btn btn-sm" id="vault-shadow-btn" onclick="setVaultMode(1,this)" style="border-color:var(--purple);color:var(--purple-bright)">SHADOW MODE</button>
        </div>
        <div class="card" style="margin-bottom:16px">
          <div class="card-title">NEW ENTRY</div>
          <textarea id="journal-input" rows="4" placeholder="DUMP YOUR THOUGHTS, CHIEF..."></textarea>
          <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
            <label class="form-label" style="margin:0;min-width:60px">MOOD (1-10)</label>
            <input type="number" id="journal-mood" min="1" max="10" value="7" style="width:80px">
            <input type="text" id="journal-tags" placeholder="TAGS (comma separated)" style="flex:1">
            <button class="btn btn-primary" onclick="addJournalEntry()">LOCK IN</button>
          </div>
        </div>
        <div id="jp-pattern" class="card" style="margin-bottom:16px;border-color:var(--purple)">
          <div class="card-title">JEAN-PHILIP PATTERN ANALYSIS</div>
          <div id="jp-pattern-text" style="font-size:13px;color:var(--silver-bright);line-height:1.8;font-style:italic">Insufficient data. Log more entries for pattern analysis.</div>
        </div>
        <div id="journal-list"></div>
      </div>

      <!-- GOALS -->
      <div class="module" id="mod-goals">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--red-bright)">TARGET SYSTEM</div>
          <div class="mod-badge" style="border-color:var(--red);color:var(--red-bright)">GOALS</div>
        </div>
        <button class="btn btn-primary" style="margin-bottom:16px" onclick="openModal('modal-goal')">+ NEW OBJECTIVE</button>
        <div id="goals-list"></div>
      </div>

      <!-- WAR ROOM -->
      <div class="module" id="mod-warroom">
        <div class="mod-header">
          <div class="mod-title" style="color:var(--red-bright)">WAR ROOM</div>
          <div class="mod-badge" style="border-color:var(--red);color:var(--red-bright)">WEEKLY OPS</div>
        </div>
        <div class="grid2" style="margin-bottom:16px">
          <div class="war-room-step">
            <div class="war-step-num">01 / DEBRIEF — LAST WEEK</div>
            <div class="form-row">
              <label class="form-label">WINS</label>
              <textarea id="war-wins" rows="3" placeholder="What went well..."></textarea>
            </div>
            <div class="form-row">
              <label class="form-label">LOSSES / GAPS</label>
              <textarea id="war-losses" rows="3" placeholder="What slipped..."></textarea>
            </div>
          </div>
          <div class="war-room-step">
            <div class="war-step-num">02 / PRIORITIES — THIS WEEK</div>
            <div class="form-row">
              <textarea id="war-priorities" rows="6" placeholder="Top 3 missions this week..."></textarea>
            </div>
          </div>
        </div>
        <button class="btn btn-primary" style="width:100%;margin-bottom:16px" onclick="generateBattlePlan()">GENERATE BATTLE PLAN</button>
        <div id="battle-plan-output" class="card" style="display:none">
          <div class="card-title">WEEKLY BATTLE PLAN</div>
          <div id="battle-plan-text" style="font-size:13px;color:var(--silver-bright);line-height:1.8;white-space:pre-line"></div>
          <button class="btn btn-sm" style="margin-top:12px;border-color:var(--silver);color:var(--silver)" onclick="speakBattlePlan()">SPEAK PLAN</button>
        </div>
        <div class="card" style="margin-top:16px">
          <div class="card-title">PAST WAR REPORTS</div>
          <div id="war-history"></div>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- MODALS -->
<div class="modal-overlay" id="modal-project">
  <div class="modal">
    <div class="modal-title" style="color:var(--amber-bright)">NEW MISSION</div>
    <div class="form-row"><label class="form-label">MISSION NAME</label><input type="text" id="proj-name" placeholder="Operation..."></div>
    <div class="form-row"><label class="form-label">DESCRIPTION</label><textarea id="proj-desc" rows="2"></textarea></div>
    <div class="form-row"><label class="form-label">DEADLINE</label><input type="date" id="proj-deadline"></div>
    <div class="form-row">
      <label class="form-label">PHASES (one per line)</label>
      <textarea id="proj-phases" rows="4" placeholder="Phase 1 — Research&#10;Phase 2 — Execution&#10;Phase 3 — Review"></textarea>
    </div>
    <div class="modal-btns">
      <button class="btn" onclick="closeModal('modal-project')">CANCEL</button>
      <button class="btn btn-primary" onclick="addProject()">DEPLOY MISSION</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal-forge">
  <div class="modal">
    <div class="modal-title" style="color:var(--amber-bright)">NEW SKILL / HOBBY</div>
    <div class="form-row"><label class="form-label">NAME</label><input type="text" id="forge-name" placeholder="Guitar, Python, Chess..."></div>
    <div class="form-row">
      <label class="form-label">TYPE</label>
      <select id="forge-type"><option value="skill">SKILL</option><option value="hobby">HOBBY</option></select>
    </div>
    <div class="form-row"><label class="form-label">NOTES / GOAL</label><textarea id="forge-notes" rows="2"></textarea></div>
    <div class="modal-btns">
      <button class="btn" onclick="closeModal('modal-forge')">CANCEL</button>
      <button class="btn btn-primary" onclick="addForgeItem()">ADD TO FORGE</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal-social">
  <div class="modal">
    <div class="modal-title" style="color:var(--teal-bright)">ADD CONTACT</div>
    <div class="form-row"><label class="form-label">NAME</label><input type="text" id="soc-name"></div>
    <div class="form-row"><label class="form-label">RELATIONSHIP</label><input type="text" id="soc-rel" placeholder="Friend, Mentor, Client..."></div>
    <div class="form-row"><label class="form-label">CONTACT EVERY (DAYS)</label><input type="number" id="soc-freq" value="14"></div>
    <div class="form-row"><label class="form-label">NOTES</label><textarea id="soc-notes" rows="2"></textarea></div>
    <div class="modal-btns">
      <button class="btn" onclick="closeModal('modal-social')">CANCEL</button>
      <button class="btn btn-primary" onclick="addContact()">ADD CONTACT</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal-goal">
  <div class="modal">
    <div class="modal-title" style="color:var(--red-bright)">NEW OBJECTIVE</div>
    <div class="form-row"><label class="form-label">OBJECTIVE</label><input type="text" id="goal-title"></div>
    <div class="form-row">
      <label class="form-label">TYPE</label>
      <select id="goal-type">
        <option value="public">PUBLIC GOAL</option>
        <option value="shadow">SHADOW GOAL (private)</option>
      </select>
    </div>
    <div class="form-row"><label class="form-label">TARGET DATE</label><input type="date" id="goal-date"></div>
    <div class="form-row"><label class="form-label">NOTES</label><textarea id="goal-notes" rows="2"></textarea></div>
    <div class="modal-btns">
      <button class="btn" onclick="closeModal('modal-goal')">CANCEL</button>
      <button class="btn btn-primary" onclick="addGoal()">SET OBJECTIVE</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal-forge-session">
  <div class="modal">
    <div class="modal-title" style="color:var(--amber-bright)">LOG SESSION</div>
    <input type="hidden" id="forge-session-id">
    <div class="form-row"><label class="form-label">DURATION (MINS)</label><input type="number" id="fs-duration" value="60"></div>
    <div class="form-row"><label class="form-label">QUALITY (1-5)</label><input type="number" id="fs-quality" min="1" max="5" value="3"></div>
    <div class="form-row"><label class="form-label">NOTES</label><textarea id="fs-notes" rows="2"></textarea></div>
    <div class="modal-btns">
      <button class="btn" onclick="closeModal('modal-forge-session')">CANCEL</button>
      <button class="btn btn-primary" onclick="logForgeSession()">LOG SESSION</button>
    </div>
  </div>
</div>

<div class="notification" id="notification"></div>

<script>
const ACCESS = "224831";
let pomoTimer = null, pomoSeconds = 25*60, pomoTotal = 25*60, pomoRunning = false, pomoMode = 'deep';
let todayPomos = 0, consecutivePomos = 0;
let currentVaultMode = 0;
let taskFilter = 'active';
let speechSynth = window.speechSynthesis;
let ambientCtx = null, ambientNode = null;
let allTasksCache = [];
let allFinanceCache = [];
let radarChart = null, finChart = null, pomoChart = null, vitalsChart = null;

document.getElementById('lock-code').addEventListener('input', function() {
  if (this.value.length === 6) {
    if (this.value === ACCESS) {
      document.getElementById('lockscreen').style.opacity = '0';
      document.getElementById('lockscreen').style.transition = 'opacity 0.8s';
      setTimeout(() => {
        document.getElementById('lockscreen').style.display = 'none';
        document.getElementById('app').style.display = 'flex';
        onAppStart();
      }, 800);
    } else {
      document.getElementById('lock-err').style.display = 'block';
      this.value = '';
      setTimeout(() => document.getElementById('lock-err').style.display = 'none', 2000);
    }
  }
});

function onAppStart() {
  updateClock();
  setInterval(updateClock, 1000);
  loadDashboard();
  loadTasks();
  jpAddMessage('jean-philip', "Identity confirmed. Welcome back, Chief. All systems are online and your data has been loaded. How can I assist you today?");
  speak("Identity confirmed. Welcome back, Chief.");
  setInterval(checkSocialAlerts, 60000);
  setTimeout(runBriefing, 2000);
}

function updateClock() {
  const now = new Date();
  document.getElementById('tb-time').textContent = now.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

function switchMod(el) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.module').forEach(m => m.classList.remove('active'));
  el.classList.add('active');
  const mod = el.dataset.mod;
  document.getElementById('mod-' + mod).classList.add('active');
  if (mod === 'dashboard') loadDashboard();
  if (mod === 'dailyops') loadTasks();
  if (mod === 'missions') loadProjects();
  if (mod === 'assets') loadFinance();
  if (mod === 'vitals') loadVitals();
  if (mod === 'opstats') loadOpStats();
  if (mod === 'forge') loadForge();
  if (mod === 'social') loadSocial();
  if (mod === 'vault') loadJournal();
  if (mod === 'goals') loadGoals();
  if (mod === 'warroom') loadWarRoom();
  if (mod === 'chrono') loadChronoStats();
}

function openJP() {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.module').forEach(m => m.classList.remove('active'));
  document.querySelector('[data-mod="intel"]').classList.add('active');
  document.getElementById('mod-intel').classList.add('active');
}

function speak(text) {
  if (!speechSynth) return;
  speechSynth.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = 'en-GB';
  utt.rate = 0.95;
  utt.pitch = 0.9;
  const voices = speechSynth.getVoices();
  const british = voices.find(v => v.lang === 'en-GB' || v.name.toLowerCase().includes('british') || v.name.toLowerCase().includes('daniel'));
  if (british) utt.voice = british;
  speechSynth.speak(utt);
}

function notify(msg, type) {
  const n = document.getElementById('notification');
  n.textContent = msg;
  n.className = 'notification show' + (type === 'jp' ? ' jp-notif' : '');
  setTimeout(() => n.classList.remove('show'), 4000);
}

async function apiCall(endpoint, method, data) {
  const opts = { method: method || 'GET', headers: {'Content-Type':'application/json'} };
  if (data) opts.body = JSON.stringify(data);
  const res = await fetch(endpoint, opts);
  return res.json();
}

async function loadDashboard() {
  const data = await apiCall('/api/dashboard');
  document.getElementById('d-score').textContent = data.productivity_score;
  document.getElementById('d-score-bar').style.width = data.productivity_score + '%';
  document.getElementById('d-xp').textContent = data.xp;
  document.getElementById('d-tasks').textContent = data.active_tasks;
  document.getElementById('d-threats').textContent = data.threats;
  document.getElementById('d-rank').textContent = data.rank;
  document.getElementById('d-level').textContent = data.level;
  document.getElementById('tb-score').textContent = data.productivity_score;
  document.getElementById('tb-xp').textContent = data.xp;
  document.getElementById('tb-rank').textContent = data.rank;
  document.getElementById('tb-threats').textContent = data.threats;
  document.getElementById('tb-load').textContent = data.load_label;
  const xpLevels = [0,500,1500,3500,7000,15000,99999];
  const lvl = data.level - 1;
  const cur = data.xp - xpLevels[Math.min(lvl, xpLevels.length-1)];
  const next = xpLevels[Math.min(lvl+1, xpLevels.length-1)] - xpLevels[Math.min(lvl, xpLevels.length-1)];
  document.getElementById('d-xp-cur').textContent = data.xp;
  document.getElementById('d-xp-next').textContent = xpLevels[Math.min(lvl+1, xpLevels.length-1)];
  document.getElementById('d-xp-bar').style.width = Math.round((cur/Math.max(next,1))*100) + '%';
  drawMomentumWave(data.momentum);
  drawGauge('gauge-load', data.cognitive_load, '#d4a017');
  document.getElementById('gauge-load-val').textContent = data.cognitive_load;
  document.getElementById('gauge-load-lbl').textContent = data.load_label;
  drawGauge('gauge-entropy', data.entropy, '#0e7c7b');
  document.getElementById('gauge-entropy-val').textContent = data.entropy;
  document.getElementById('gauge-entropy-lbl').textContent = data.entropy_label;
  renderThreatMatrix(data.threats_detail);
  renderSystemStatus(data);
  document.getElementById('dash-date').textContent = new Date().toLocaleDateString('en-GB', {weekday:'short',day:'numeric',month:'short'}).toUpperCase();
}

function drawMomentumWave(data) {
  const wrap = document.getElementById('momentum-wave');
  wrap.innerHTML = '';
  const max = Math.max(...data, 1);
  data.forEach(v => {
    const bar = document.createElement('div');
    bar.className = 'wv-bar';
    const pct = Math.round((v / max) * 100);
    bar.style.height = Math.max(pct, 4) + '%';
    const intensity = pct > 70 ? '#4a9eff' : pct > 40 ? '#2d7dd2' : '#1a4a7a';
    bar.style.background = intensity;
    wrap.appendChild(bar);
  });
}

function drawGauge(canvasId, value, color) {
  const c = document.getElementById(canvasId);
  if (!c) return;
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, 120, 70);
  ctx.strokeStyle = '#1a2030';
  ctx.lineWidth = 8;
  ctx.beginPath();
  ctx.arc(60, 65, 50, Math.PI, 0);
  ctx.stroke();
  ctx.strokeStyle = color;
  ctx.lineWidth = 8;
  ctx.beginPath();
  ctx.arc(60, 65, 50, Math.PI, Math.PI + (Math.PI * Math.min(value,100) / 100));
  ctx.stroke();
}

function renderThreatMatrix(threats) {
  const el = document.getElementById('threat-matrix-list');
  if (!threats || !threats.length) { el.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:8px 0">NO ACTIVE THREATS DETECTED</div>'; return; }
  el.innerHTML = threats.map(t => `
    <div class="threat-item threat-${t.severity.toLowerCase()}">
      <div>
        <div style="font-size:12px;letter-spacing:1px">${t.title}</div>
        <div style="font-size:10px;color:var(--text3);letter-spacing:1px;margin-top:2px">${t.type}</div>
      </div>
      <div style="font-size:10px;letter-spacing:2px;color:var(--${t.severity==='CRITICAL'?'red':'amber'}-bright)">${t.severity}</div>
    </div>`).join('');
}

function renderSystemStatus(data) {
  const el = document.getElementById('system-status-list');
  const items = [
    {label:'TASK LOAD', val:data.load_label, color: data.load_label==='OPTIMAL'?'green':'red'},
    {label:'ENTROPY', val:data.entropy_label, color: data.entropy_label==='STABLE'?'green':'amber'},
    {label:'MOMENTUM', val:Math.round(data.momentum.reduce((a,b)=>a+b,0)/7)+'%', color:'blue'},
    {label:'SCORE', val:data.productivity_score+'%', color: data.productivity_score>60?'green':'red'}
  ];
  el.innerHTML = items.map(i => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--border)">
      <span style="font-size:11px;letter-spacing:2px;color:var(--text2)">${i.label}</span>
      <span style="font-size:12px;font-weight:600;letter-spacing:2px;color:var(--${i.color}-bright)">${i.val}</span>
    </div>`).join('');
}

async function runBriefing() {
  const data = await apiCall('/api/dashboard');
  const briefing = await apiCall('/api/jp/briefing', 'POST', data);
  document.getElementById('jp-briefing').textContent = briefing.text;
}

function speakBriefing() {
  const text = document.getElementById('jp-briefing').textContent;
  speak(text);
}

async function loadTasks() {
  const data = await apiCall('/api/tasks');
  allTasksCache = data.tasks;
  renderTasks(data.tasks);
  const today = new Date().toISOString().split('T')[0];
  const critical = data.tasks.filter(t => t.priority==='CRITICAL' && t.status==='active').length;
  const active = data.tasks.filter(t => t.status==='active').length;
  const doneToday = data.tasks.filter(t => t.status==='done' && t.completed_at && t.completed_at.startsWith(today)).length;
  document.getElementById('tasks-critical').textContent = critical;
  document.getElementById('tasks-active').textContent = active;
  document.getElementById('tasks-done-today').textContent = doneToday;
  const eff = active > 0 ? Math.round((doneToday / (doneToday + active)) * 100) : (doneToday > 0 ? 100 : 0);
  document.getElementById('eod-efficiency').textContent = `Today's efficiency: ${eff}% — ${doneToday} completed, ${active} remaining. ${eff>70?'Strong output, Chief.':eff>40?'Acceptable tempo. Push harder.':'Below threshold. Recalibrate and execute.'}`;
}

function filterTasks(filter, btn) {
  taskFilter = filter;
  document.querySelectorAll('#mod-dailyops .btn-sm').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderTasks(allTasksCache);
}

function renderTasks(tasks) {
  const list = document.getElementById('task-list');
  let filtered = tasks;
  if (taskFilter === 'active') filtered = tasks.filter(t => t.status === 'active');
  if (taskFilter === 'done') filtered = tasks.filter(t => t.status === 'done');
  if (!filtered.length) { list.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:16px 0">NO TASKS IN THIS VIEW</div>'; return; }
  const sorted = [...filtered].sort((a,b) => {
    const po = {CRITICAL:0,HIGH:1,LOW:2};
    return (po[a.priority]||1) - (po[b.priority]||1);
  });
  list.innerHTML = sorted.map(t => `
    <div class="task-item ${t.status==='done'?'done':''}">
      <div class="task-check ${t.status==='done'?'checked':''}" onclick="toggleTask(${t.id},'${t.status}')">
        ${t.status==='done'?'<svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="white" stroke-width="2"><path d="M1 5l3 3 5-5"/></svg>':''}
      </div>
      <div class="task-title ${t.status==='done'?'done-txt':''}">${t.title}</div>
      <div class="priority-badge p-${t.priority.toLowerCase()}">${t.priority}</div>
      ${t.due_date?`<div style="font-size:10px;color:var(--text3);letter-spacing:1px">${t.due_date}</div>`:''}
      ${t.estimated_mins?`<div style="font-size:10px;color:var(--text3)">${t.estimated_mins}m</div>`:''}
      <button class="btn btn-sm btn-danger" onclick="deleteTask(${t.id})" style="padding:2px 8px;font-size:10px">X</button>
    </div>`).join('');
}

async function addTask() {
  const title = document.getElementById('task-input').value.trim();
  if (!title) return;
  const priority = document.getElementById('task-priority').value;
  const due_date = document.getElementById('task-due').value;
  const estimated_mins = parseInt(document.getElementById('task-est').value) || 30;
  await apiCall('/api/tasks', 'POST', {title, priority, due_date, estimated_mins});
  document.getElementById('task-input').value = '';
  loadTasks();
  notify('TASK LOGGED', 'success');
}

async function toggleTask(id, status) {
  if (status === 'active') {
    await apiCall('/api/tasks/' + id + '/complete', 'POST');
    speak("Target neutralised, Chief.");
    notify('TARGET NEUTRALISED', 'jp');
  } else {
    await apiCall('/api/tasks/' + id + '/reopen', 'POST');
  }
  loadTasks();
  loadDashboard();
}

async function deleteTask(id) {
  await apiCall('/api/tasks/' + id, 'DELETE');
  loadTasks();
}

async function loadProjects() {
  const data = await apiCall('/api/projects');
  const list = document.getElementById('project-list');
  if (!data.projects.length) { list.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:16px 0">NO ACTIVE MISSIONS</div>'; return; }
  list.innerHTML = data.projects.map(p => {
    const phases = p.phases || [];
    const done = phases.filter(ph => ph.status === 'done').length;
    const pct = phases.length ? Math.round((done / phases.length) * 100) : 0;
    const daysLeft = p.deadline ? Math.ceil((new Date(p.deadline) - new Date()) / 86400000) : null;
    let killProb = 'LOW';
    let killColor = 'green';
    if (daysLeft !== null && daysLeft < 7 && pct < 50) { killProb = 'CRITICAL'; killColor = 'red'; }
    else if (daysLeft !== null && daysLeft < 14 && pct < 30) { killProb = 'ELEVATED'; killColor = 'amber'; }
    return `<div class="card" style="margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
        <div>
          <div style="font-size:16px;font-weight:700;letter-spacing:2px">${p.name}</div>
          ${p.description?`<div style="font-size:12px;color:var(--text2);margin-top:2px">${p.description}</div>`:''}
        </div>
        <div style="text-align:right">
          <div style="font-size:10px;letter-spacing:2px;color:var(--${killColor}-bright)">KILL PROB: ${killProb}</div>
          ${daysLeft!==null?`<div style="font-size:10px;color:var(--text3);margin-top:2px">${daysLeft}D REMAINING</div>`:''}
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <div style="flex:1"><div class="progress-bar" style="height:6px"><div class="progress-fill" style="background:var(--amber-bright);width:${pct}%"></div></div></div>
        <div style="font-size:14px;font-weight:700;color:var(--amber-bright);min-width:40px">${pct}%</div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        ${phases.map(ph => `
          <div style="display:flex;align-items:center;gap:4px;cursor:pointer" onclick="togglePhase(${ph.id})">
            <div style="width:10px;height:10px;border:1px solid ${ph.status==='done'?'var(--green)':'var(--border2)'};background:${ph.status==='done'?'var(--green)':'transparent'}"></div>
            <span style="font-size:11px;color:${ph.status==='done'?'var(--green-bright)':'var(--text2)'};letter-spacing:1px;${ph.status==='done'?'text-decoration:line-through':''}">${ph.name}</span>
          </div>`).join('')}
      </div>
      <button class="btn btn-sm btn-danger" style="margin-top:10px" onclick="deleteProject(${p.id})">ABORT MISSION</button>
    </div>`;
  }).join('');
}

async function addProject() {
  const name = document.getElementById('proj-name').value.trim();
  if (!name) return;
  const phases = document.getElementById('proj-phases').value.split('\n').map(s=>s.trim()).filter(Boolean);
  await apiCall('/api/projects', 'POST', {
    name, description: document.getElementById('proj-desc').value,
    deadline: document.getElementById('proj-deadline').value, phases
  });
  closeModal('modal-project');
  loadProjects();
  notify('MISSION DEPLOYED', 'success');
  speak("New mission deployed, Chief.");
}

async function togglePhase(id) {
  await apiCall('/api/phases/' + id + '/toggle', 'POST');
  loadProjects();
}

async function deleteProject(id) {
  await apiCall('/api/projects/' + id, 'DELETE');
  loadProjects();
}

function setPomoMode(mode, btn) {
  pomoMode = mode;
  document.querySelectorAll('.chrono-mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const mins = mode==='deep'?25:mode==='shallow'?15:5;
  pomoSeconds = mins * 60;
  pomoTotal = mins * 60;
  pomoRunning = false;
  clearInterval(pomoTimer);
  document.getElementById('pomo-start-btn').style.display = '';
  document.getElementById('pomo-pause-btn').style.display = 'none';
  updatePomoDisplay();
  document.getElementById('pomo-mode-lbl').textContent = mode.toUpperCase() + (mode==='deep'?' WORK':mode==='shallow'?' WORK':' BREAK');
}

function pomoStart() {
  if (pomoRunning) return;
  pomoRunning = true;
  document.getElementById('pomo-start-btn').style.display = 'none';
  document.getElementById('pomo-pause-btn').style.display = '';
  apiCall('/api/pomodoro/start', 'POST', {mode: pomoMode, duration: Math.round(pomoTotal/60)});
  pomoTimer = setInterval(() => {
    pomoSeconds--;
    updatePomoDisplay();
    if (pomoSeconds <= 0) {
      clearInterval(pomoTimer);
      pomoRunning = false;
      pomoComplete();
    }
  }, 1000);
}

function pomoPause() {
  clearInterval(pomoTimer);
  pomoRunning = false;
  document.getElementById('pomo-start-btn').style.display = '';
  document.getElementById('pomo-pause-btn').style.display = 'none';
}

function pomoReset() {
  clearInterval(pomoTimer);
  pomoRunning = false;
  const mins = pomoMode==='deep'?25:pomoMode==='shallow'?15:5;
  pomoSeconds = mins * 60;
  pomoTotal = mins * 60;
  document.getElementById('pomo-start-btn').style.display = '';
  document.getElementById('pomo-pause-btn').style.display = 'none';
  updatePomoDisplay();
}

function pomoComplete() {
  todayPomos++;
  consecutivePomos++;
  document.getElementById('pomo-count').textContent = todayPomos;
  document.getElementById('pomo-streak').textContent = consecutivePomos;
  apiCall('/api/pomodoro/complete', 'POST', {});
  document.getElementById('pomo-start-btn').style.display = '';
  document.getElementById('pomo-pause-btn').style.display = 'none';
  pomoSeconds = pomoTotal;
  updatePomoDisplay();
  if (pomoMode !== 'break') {
    speak("Focus session complete. Recommend a brief systems check, Chief.");
    notify('SESSION COMPLETE — +15 XP', 'jp');
    if (consecutivePomos >= 3) {
      document.getElementById('flow-status').textContent = 'FLOW STATE';
      document.getElementById('flow-status').style.color = 'var(--blue-bright)';
      document.getElementById('flow-desc').textContent = 'You are in flow. Do not stop now, Chief.';
      speak("Chief, you have entered flow state. I strongly advise against stopping now.");
    }
  }
}

function updatePomoDisplay() {
  const m = Math.floor(pomoSeconds / 60).toString().padStart(2,'0');
  const s = (pomoSeconds % 60).toString().padStart(2,'0');
  document.getElementById('pomo-display').textContent = m + ':' + s;
  const progress = 1 - (pomoSeconds / pomoTotal);
  const circumference = 553;
  document.getElementById('pomo-arc').style.strokeDashoffset = circumference * (1 - progress);
}

function setCustomMins() {
  const mins = parseInt(document.getElementById('custom-mins').value) || 25;
  pomoSeconds = mins * 60;
  pomoTotal = mins * 60;
  pomoRunning = false;
  clearInterval(pomoTimer);
  updatePomoDisplay();
}

function setAmbient(type) {
  document.querySelectorAll('#mod-chrono .btn-sm').forEach(b => {
    if (['SILENCE','WHITE NOISE','RAIN','FOCUS'].includes(b.textContent)) {
      b.style.borderColor = '';
      b.style.color = '';
    }
  });
  if (ambientCtx) { ambientCtx.close(); ambientCtx = null; }
  if (type === 'off') return;
  try {
    ambientCtx = new AudioContext();
    const bufferSize = 2 * ambientCtx.sampleRate;
    const noiseBuffer = ambientCtx.createBuffer(1, bufferSize, ambientCtx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) output[i] = Math.random() * 2 - 1;
    const source = ambientCtx.createBufferSource();
    source.buffer = noiseBuffer;
    source.loop = true;
    const gainNode = ambientCtx.createGain();
    gainNode.gain.value = type === 'white' ? 0.05 : 0.03;
    if (type === 'focus') gainNode.gain.value = 0.02;
    source.connect(gainNode);
    gainNode.connect(ambientCtx.destination);
    source.start();
    ambientNode = source;
  } catch(e) {}
}

async function loadChronoStats() {
  const data = await apiCall('/api/pomodoro/stats');
  document.getElementById('pomo-count').textContent = data.today;
  if (pomoChart) { pomoChart.destroy(); pomoChart = null; }
  const ctx = document.getElementById('pomo-chart').getContext('2d');
  pomoChart = new Chart(ctx, {
    type:'bar',
    data:{ labels:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], datasets:[{label:'Sessions',data:data.week_data,backgroundColor:'rgba(192,57,43,0.6)',borderColor:'#c0392b',borderWidth:1}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#6b7f99'}},y:{ticks:{color:'#6b7f99',stepSize:1},grid:{color:'rgba(255,255,255,0.04)'}}}}
  });
}

async function loadFinance() {
  const data = await apiCall('/api/finance');
  allFinanceCache = data.transactions;
  document.getElementById('fin-income').textContent = Math.round(data.monthly_income);
  document.getElementById('fin-expenses').textContent = Math.round(data.monthly_expenses);
  const bal = data.monthly_income - data.monthly_expenses;
  const balEl = document.getElementById('fin-balance');
  balEl.textContent = Math.round(bal);
  balEl.style.color = bal >= 0 ? 'var(--green-bright)' : 'var(--red-bright)';
  const runway = data.monthly_expenses > 0 ? (bal > 0 ? Math.round(bal / data.monthly_expenses * 10) / 10 : 0) : '--';
  document.getElementById('fin-runway').textContent = runway;
  const wt = document.getElementById('wealth-trajectory');
  const mo3 = bal * 3, mo6 = bal * 6, mo12 = bal * 12;
  wt.innerHTML = `
    <div class="finance-row"><span>3 MONTHS</span><span class="${mo3>=0?'income':'expense'}-val">${mo3>=0?'+':''}${Math.round(mo3)}</span></div>
    <div class="finance-row"><span>6 MONTHS</span><span class="${mo6>=0?'income':'expense'}-val">${mo6>=0?'+':''}${Math.round(mo6)}</span></div>
    <div class="finance-row"><span>12 MONTHS</span><span class="${mo12>=0?'income':'expense'}-val">${mo12>=0?'+':''}${Math.round(mo12)}</span></div>
    <div style="margin-top:8px;font-size:11px;color:var(--text3);letter-spacing:1px">${bal>0?'Surplus trajectory detected. Allocation recommended.':'Warning: expenditure exceeds income. Recalibration required.'}</div>`;
  if (finChart) { finChart.destroy(); finChart = null; }
  const ctx = document.getElementById('fin-chart').getContext('2d');
  finChart = new Chart(ctx, {
    type:'bar',
    data:{labels:data.monthly_labels, datasets:[
      {label:'Income',data:data.monthly_income_data,backgroundColor:'rgba(26,138,74,0.6)',borderColor:'#27ae60',borderWidth:1},
      {label:'Expenses',data:data.monthly_expense_data,backgroundColor:'rgba(192,57,43,0.4)',borderColor:'#c0392b',borderWidth:1}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#6b7f99'}},y:{ticks:{color:'#6b7f99'},grid:{color:'rgba(255,255,255,0.04)'}}}}
  });
  const log = document.getElementById('fin-log');
  if (!data.transactions.length) { log.innerHTML = '<div style="color:var(--text3);font-size:12px;padding:12px 0;letter-spacing:2px">NO TRANSACTIONS LOGGED</div>'; return; }
  log.innerHTML = data.transactions.slice(0,20).map(t => `
    <div class="finance-row">
      <span style="font-size:11px;color:var(--text2)">${t.date}</span>
      <span style="flex:1;margin:0 12px;font-size:13px">${t.description||t.category}</span>
      <span class="${t.type==='income'?'income':'expense'}-val">${t.type==='income'?'+':'−'}${Math.round(t.amount)}</span>
      <button class="btn btn-sm" style="margin-left:8px;padding:2px 6px;font-size:10px;border-color:var(--red);color:var(--red-bright)" onclick="deleteFinance(${t.id})">X</button>
    </div>`).join('');
}

async function addFinance() {
  const amount = parseFloat(document.getElementById('fin-amount').value);
  if (!amount) return;
  await apiCall('/api/finance', 'POST', {
    type: document.getElementById('fin-type').value,
    description: document.getElementById('fin-desc').value,
    amount, category: document.getElementById('fin-cat').value,
    date: document.getElementById('fin-date').value || new Date().toISOString().split('T')[0]
  });
  document.getElementById('fin-amount').value = '';
  document.getElementById('fin-desc').value = '';
  loadFinance();
  notify('TRANSACTION LOGGED', 'success');
}

async function deleteFinance(id) {
  await apiCall('/api/finance/' + id, 'DELETE');
  loadFinance();
}

async function loadVitals() {
  const data = await apiCall('/api/vitals');
  const today = data.today;
  if (today) {
    document.getElementById('v-sleep').textContent = today.sleep_hours || '--';
    document.getElementById('v-water').textContent = today.water_ml || '--';
    document.getElementById('v-calories').textContent = today.calories || '--';
    document.getElementById('v-workout').textContent = today.workout_mins || '--';
    document.getElementById('v-sleep-bar').style.width = Math.min(((today.sleep_hours||0)/10)*100,100)+'%';
    document.getElementById('v-water-bar').style.width = Math.min(((today.water_ml||0)/3000)*100,100)+'%';
    const rec = Math.round(((today.sleep_hours||6)/8)*50 + ((today.energy_level||5)/10)*50);
    document.getElementById('recovery-score').textContent = rec;
    document.getElementById('recovery-label').style.color = rec>70?'var(--green-bright)':rec>40?'var(--amber-bright)':'var(--red-bright)';
    document.getElementById('recovery-label').textContent = rec>70?'FULLY RECOVERED':rec>40?'ADEQUATE':'UNDER-RECOVERED';
  }
  const peak = document.getElementById('peak-window');
  peak.innerHTML = `
    <div class="finance-row"><span style="color:var(--text2)">DEEP WORK WINDOW</span><span style="color:var(--blue-bright)">09:00 — 12:00</span></div>
    <div class="finance-row"><span style="color:var(--text2)">CREATIVE TASKS</span><span style="color:var(--amber-bright)">14:00 — 16:00</span></div>
    <div class="finance-row"><span style="color:var(--text2)">ADMIN / LOW EFFORT</span><span style="color:var(--text)">16:00 — 18:00</span></div>
    <div style="font-size:10px;color:var(--text3);margin-top:6px;letter-spacing:1px">Based on standard chronobiology data. Will refine with your logged vitals over time.</div>`;
  if (vitalsChart) { vitalsChart.destroy(); vitalsChart = null; }
  const ctx = document.getElementById('vitals-chart').getContext('2d');
  vitalsChart = new Chart(ctx, {
    type:'line',
    data:{labels:data.labels, datasets:[
      {label:'Sleep',data:data.sleep_data,borderColor:'#1abc9c',backgroundColor:'transparent',tension:0.3,pointRadius:3},
      {label:'Energy',data:data.energy_data,borderColor:'#4a9eff',backgroundColor:'transparent',tension:0.3,pointRadius:3,borderDash:[4,2]}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#6b7f99'}},y:{ticks:{color:'#6b7f99'},grid:{color:'rgba(255,255,255,0.04)'}}}}
  });
}

async function logVitals() {
  await apiCall('/api/vitals', 'POST', {
    sleep_hours: parseFloat(document.getElementById('v-in-sleep').value)||0,
    sleep_quality: parseInt(document.getElementById('v-in-quality').value)||0,
    water_ml: parseInt(document.getElementById('v-in-water').value)||0,
    calories: parseInt(document.getElementById('v-in-calories').value)||0,
    workout_mins: parseInt(document.getElementById('v-in-workout').value)||0,
    energy_level: parseInt(document.getElementById('v-in-energy').value)||5,
    weight: parseFloat(document.getElementById('v-in-weight').value)||null
  });
  loadVitals();
  notify('VITALS LOGGED', 'success');
  speak("Vitals recorded, Chief.");
}

async function loadOpStats() {
  const data = await apiCall('/api/opstats');
  document.getElementById('os-xp').textContent = data.xp;
  document.getElementById('os-rank').textContent = data.rank;
  document.getElementById('os-score').textContent = data.productivity_score;
  document.getElementById('os-streak').textContent = data.streak;
  renderHeatmap(data.heatmap);
  if (radarChart) { radarChart.destroy(); radarChart = null; }
  const ctx = document.getElementById('radar-chart').getContext('2d');
  radarChart = new Chart(ctx, {
    type:'radar',
    data:{labels:['TASKS','PROJECTS','FOCUS','FINANCE','HEALTH'],datasets:[{
      data:data.radar,backgroundColor:'rgba(107,52,131,0.2)',borderColor:'#9b59b6',pointBackgroundColor:'#9b59b6',borderWidth:2,pointRadius:3
    }]},
    options:{responsive:false,plugins:{legend:{display:false}},scales:{r:{min:0,max:100,ticks:{display:false,stepSize:20},grid:{color:'rgba(255,255,255,0.07)'},angleLines:{color:'rgba(255,255,255,0.07)'},pointLabels:{color:'#6b7f99',font:{size:10}}}}}
  });
  const pr = document.getElementById('personal-records');
  pr.innerHTML = [
    {label:'LONGEST STREAK', val: data.streak + ' DAYS'},
    {label:'BEST SCORE', val: data.best_score + '%'},
    {label:'MOST TASKS (1 DAY)', val: data.max_tasks_day},
    {label:'TOTAL TASKS DONE', val: data.total_done},
    {label:'TOTAL FOCUS SESSIONS', val: data.total_pomos},
    {label:'TOTAL XP', val: data.xp}
  ].map(r => `<div class="mini-stat"><div class="mini-val" style="font-size:18px;color:var(--purple-bright)">${r.val}</div><div class="mini-lbl">${r.label}</div></div>`).join('');
  document.getElementById('chrono-optimizer').innerHTML = `
    <div class="finance-row"><span>PEAK COMPLETION RATE</span><span style="color:var(--blue-bright)">09:00 — 12:00</span></div>
    <div class="finance-row"><span>AVG TASKS COMPLETED/DAY</span><span style="color:var(--amber-bright)">${data.avg_tasks_day}</span></div>
    <div class="finance-row"><span>BEST DAY OF WEEK</span><span style="color:var(--green-bright)">${data.best_day}</span></div>
    <div style="font-size:11px;color:var(--text3);margin-top:6px;letter-spacing:1px">Schedule deep work and critical tasks in your peak window, Chief.</div>`;
}

function renderHeatmap(data) {
  const wrap = document.getElementById('heatmap');
  wrap.innerHTML = '';
  data.forEach(val => {
    const cell = document.createElement('div');
    cell.className = 'hm-cell';
    if (val > 0) cell.style.background = val > 60 ? '#4a9eff' : val > 30 ? '#2d7dd2' : '#1a4a7a';
    wrap.appendChild(cell);
  });
}

function jpAddMessage(from, text) {
  const msgs = document.getElementById('jp-messages');
  const div = document.createElement('div');
  div.className = 'jp-msg ' + (from === 'jean-philip' ? 'jp' : 'user');
  div.innerHTML = `<div class="jp-msg-name">${from === 'jean-philip' ? 'JEAN-PHILIP' : 'CHIEF'}</div>${text}`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

async function sendToJP() {
  const input = document.getElementById('jp-query');
  const query = input.value.trim();
  if (!query) return;
  jpAddMessage('user', query);
  input.value = '';
  const data = await apiCall('/api/jp/query', 'POST', {query});
  jpAddMessage('jean-philip', data.response);
  speak(data.response);
}

async function analyzeDecision() {
  const input = document.getElementById('decision-input').value.trim();
  if (!input) return;
  const data = await apiCall('/api/jp/decision', 'POST', {decision: input});
  document.getElementById('decision-output').textContent = data.response;
  speak(data.response);
}

function startVoiceInput() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    notify('VOICE INPUT NOT SUPPORTED IN THIS BROWSER', '');
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = 'en-US';
  rec.onresult = e => { document.getElementById('jp-query').value = e.results[0][0].transcript; sendToJP(); };
  rec.start();
  document.getElementById('voice-btn').textContent = '...';
  rec.onend = () => document.getElementById('voice-btn').textContent = 'MIC';
}

async function loadForge() {
  const data = await apiCall('/api/forge');
  const list = document.getElementById('forge-list');
  if (!data.items.length) { list.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:16px 0">NO SKILLS OR HOBBIES TRACKED YET</div>'; return; }
  list.innerHTML = data.items.map(item => {
    const lastSession = item.last_session || 'Never';
    const daysSince = item.last_session ? Math.ceil((new Date()-new Date(item.last_session))/86400000) : null;
    const neglected = daysSince && daysSince > 7;
    return `<div class="forge-item ${neglected?'border: 1px solid var(--amber)!important':''}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
        <div>
          <span style="font-size:15px;font-weight:700;letter-spacing:2px">${item.name}</span>
          <span style="font-size:10px;letter-spacing:2px;padding:2px 8px;border:1px solid var(--border);color:var(--text2);margin-left:8px">${item.type.toUpperCase()}</span>
          ${neglected?`<span style="font-size:10px;color:var(--amber-bright);margin-left:8px;letter-spacing:1px">NEGLECTED — ${daysSince}D</span>`:''}
        </div>
        <div style="text-align:right">
          <div style="font-size:24px;font-weight:700;color:var(--amber-bright)">${item.mastery}%</div>
          <div style="font-size:10px;color:var(--text3)">MASTERY</div>
        </div>
      </div>
      <div class="progress-bar" style="height:6px;margin-bottom:8px"><div class="progress-fill" style="background:var(--amber-bright);width:${item.mastery}%"></div></div>
      <div style="display:flex;gap:16px;font-size:11px;color:var(--text2);letter-spacing:1px;margin-bottom:10px">
        <span>SESSIONS: ${item.sessions}</span>
        <span>TOTAL: ${Math.round((item.total_mins||0)/60)}H</span>
        <span>LAST: ${lastSession}</span>
      </div>
      <button class="btn btn-sm btn-primary" onclick="openForgeSession(${item.id})">+ LOG SESSION</button>
      <button class="btn btn-sm btn-danger" style="margin-left:8px" onclick="deleteForge(${item.id})">REMOVE</button>
    </div>`;
  }).join('');
}

function openForgeSession(id) {
  document.getElementById('forge-session-id').value = id;
  openModal('modal-forge-session');
}

async function logForgeSession() {
  const id = document.getElementById('forge-session-id').value;
  await apiCall('/api/forge/' + id + '/session', 'POST', {
    duration_mins: parseInt(document.getElementById('fs-duration').value)||60,
    quality: parseInt(document.getElementById('fs-quality').value)||3,
    notes: document.getElementById('fs-notes').value
  });
  closeModal('modal-forge-session');
  loadForge();
  notify('SESSION LOGGED — MASTERY INCREASING', 'success');
}

async function addForgeItem() {
  const name = document.getElementById('forge-name').value.trim();
  if (!name) return;
  await apiCall('/api/forge', 'POST', {name, type: document.getElementById('forge-type').value, notes: document.getElementById('forge-notes').value});
  closeModal('modal-forge');
  loadForge();
}

async function deleteForge(id) {
  await apiCall('/api/forge/' + id, 'DELETE');
  loadForge();
}

async function loadSocial() {
  const data = await apiCall('/api/social');
  const list = document.getElementById('social-list');
  if (!data.contacts.length) { list.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:16px 0">NO CONTACTS ADDED YET</div>'; return; }
  const today = new Date();
  list.innerHTML = data.contacts.map(c => {
    const initials = c.name.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
    const daysSince = c.last_contact ? Math.ceil((today - new Date(c.last_contact)) / 86400000) : null;
    const health = daysSince ? Math.max(0, Math.round(100 - (daysSince / c.contact_frequency_days) * 100)) : 100;
    const healthColor = health > 60 ? 'var(--green-bright)' : health > 30 ? 'var(--amber-bright)' : 'var(--red-bright)';
    return `<div class="social-item">
      <div class="social-avatar" style="color:var(--teal-bright)">${initials}</div>
      <div style="flex:1">
        <div style="font-size:14px;font-weight:700">${c.name}</div>
        <div style="font-size:11px;color:var(--text2);letter-spacing:1px;margin-top:2px">${c.relationship||'—'} ${daysSince?`· ${daysSince}d ago`:''}</div>
        <div class="health-bar" style="width:120px;margin-top:6px"><div class="health-fill" style="background:${healthColor};width:${health}%"></div></div>
      </div>
      <button class="btn btn-sm btn-success" onclick="contactLogged(${c.id})">CONTACTED</button>
      <button class="btn btn-sm btn-danger" style="margin-left:6px" onclick="deleteSocial(${c.id})">X</button>
    </div>`;
  }).join('');
}

async function contactLogged(id) {
  await apiCall('/api/social/' + id + '/contact', 'POST');
  loadSocial();
}

async function deleteSocial(id) {
  await apiCall('/api/social/' + id, 'DELETE');
  loadSocial();
}

async function addContact() {
  const name = document.getElementById('soc-name').value.trim();
  if (!name) return;
  await apiCall('/api/social', 'POST', {name, relationship:document.getElementById('soc-rel').value, contact_frequency_days:parseInt(document.getElementById('soc-freq').value)||14, notes:document.getElementById('soc-notes').value});
  closeModal('modal-social');
  loadSocial();
}

function checkSocialAlerts() {
  apiCall('/api/social').then(data => {
    if (!data.contacts) return;
    const today = new Date();
    data.contacts.forEach(c => {
      if (!c.last_contact) return;
      const daysSince = Math.ceil((today - new Date(c.last_contact)) / 86400000);
      if (daysSince > c.contact_frequency_days + 3) {
        speak(`Chief, you haven't contacted ${c.name} in ${daysSince} days. Relationship health declining.`);
      }
    });
  });
}

function setVaultMode(mode, btn) {
  currentVaultMode = mode;
  document.getElementById('vault-public-btn').classList.remove('active');
  document.getElementById('vault-shadow-btn').classList.remove('active');
  btn.classList.add('active');
  loadJournal();
}

async function loadJournal() {
  const data = await apiCall('/api/journal?shadow=' + currentVaultMode);
  const list = document.getElementById('journal-list');
  if (!data.entries.length) { list.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:16px 0">VAULT IS EMPTY</div>'; return; }
  list.innerHTML = data.entries.map(e => `
    <div class="journal-entry">
      <div class="journal-date">${e.created_at} ${e.tags?'· '+e.tags:''} · MOOD ${e.mood}/10</div>
      <div style="font-size:13px;line-height:1.7">${e.content}</div>
    </div>`).join('');
  if (data.entries.length >= 3) {
    const moods = data.entries.slice(0,10).map(e=>e.mood);
    const avgMood = (moods.reduce((a,b)=>a+b,0)/moods.length).toFixed(1);
    document.getElementById('jp-pattern-text').textContent = `Pattern analysis: ${data.entries.length} entries logged. Average mood score: ${avgMood}/10. ${avgMood < 5 ? 'Chief, recurring low mood patterns detected. A recalibration session may be warranted.' : avgMood > 7 ? 'Mood patterns indicate sustained positive operational state.' : 'Mood is within normal operational range.'} ${currentVaultMode ? 'Shadow mode active. These entries remain private.' : ''}`;
  }
}

async function addJournalEntry() {
  const content = document.getElementById('journal-input').value.trim();
  if (!content) return;
  await apiCall('/api/journal', 'POST', {content, mood:parseInt(document.getElementById('journal-mood').value)||7, tags:document.getElementById('journal-tags').value, is_shadow:currentVaultMode});
  document.getElementById('journal-input').value = '';
  loadJournal();
  notify('ENTRY LOCKED IN VAULT', 'success');
}

async function loadGoals() {
  const data = await apiCall('/api/goals');
  const list = document.getElementById('goals-list');
  if (!data.goals.length) { list.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:16px 0">NO OBJECTIVES SET</div>'; return; }
  list.innerHTML = data.goals.map(g => `
    <div class="goal-item">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
        <div>
          <span style="font-size:14px;font-weight:700">${g.title}</span>
          <span style="font-size:10px;letter-spacing:2px;padding:2px 8px;border:1px solid ${g.type==='shadow'?'var(--purple)':'var(--border)'};color:${g.type==='shadow'?'var(--purple-bright)':'var(--text2)'};margin-left:8px">${g.type.toUpperCase()}</span>
        </div>
        <div style="font-size:24px;font-weight:700;color:var(--red-bright)">${g.progress}%</div>
      </div>
      ${g.target_date?`<div style="font-size:10px;color:var(--text3);margin-bottom:8px">TARGET: ${g.target_date}</div>`:''}
      <div class="progress-bar"><div class="progress-fill" style="background:var(--red-bright);width:${g.progress}%"></div></div>
      <div style="display:flex;gap:8px;margin-top:10px;align-items:center">
        <input type="range" min="0" max="100" value="${g.progress}" style="flex:1" oninput="updateGoalProgress(${g.id},this.value)">
        <span style="font-size:12px;color:var(--red-bright);min-width:36px" id="gp-${g.id}">${g.progress}%</span>
        <button class="btn btn-sm btn-danger" onclick="deleteGoal(${g.id})">X</button>
      </div>
    </div>`).join('');
}

async function updateGoalProgress(id, val) {
  document.getElementById('gp-'+id).textContent = val+'%';
  await apiCall('/api/goals/'+id+'/progress', 'POST', {progress: parseInt(val)});
}

async function addGoal() {
  const title = document.getElementById('goal-title').value.trim();
  if (!title) return;
  await apiCall('/api/goals', 'POST', {title, type:document.getElementById('goal-type').value, target_date:document.getElementById('goal-date').value, notes:document.getElementById('goal-notes').value});
  closeModal('modal-goal');
  loadGoals();
}

async function deleteGoal(id) {
  await apiCall('/api/goals/'+id, 'DELETE');
  loadGoals();
}

async function loadWarRoom() {
  const data = await apiCall('/api/warroom');
  const hist = document.getElementById('war-history');
  if (!data.reports.length) { hist.innerHTML = '<div style="color:var(--text3);font-size:12px;letter-spacing:2px;padding:12px 0">NO PREVIOUS REPORTS</div>'; return; }
  hist.innerHTML = data.reports.map(r => `
    <div class="dossier-section" style="margin-bottom:12px">
      <div style="font-size:11px;letter-spacing:2px;color:var(--blue-bright);margin-bottom:6px">WEEK OF ${r.week_start}</div>
      ${r.battle_plan?`<div style="font-size:12px;color:var(--text2);line-height:1.7;white-space:pre-line">${r.battle_plan}</div>`:''}
    </div>`).join('');
}

async function generateBattlePlan() {
  const wins = document.getElementById('war-wins').value;
  const losses = document.getElementById('war-losses').value;
  const priorities = document.getElementById('war-priorities').value;
  const data = await apiCall('/api/warroom', 'POST', {wins, losses, priorities});
  document.getElementById('battle-plan-text').textContent = data.plan;
  document.getElementById('battle-plan-output').style.display = 'block';
  speak("Battle plan generated, Chief. Reviewing now.");
}

function speakBattlePlan() {
  speak(document.getElementById('battle-plan-text').textContent);
}

function openModal(id) { document.getElementById(id).classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('show'); });
});
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/dashboard')
def dashboard():
    db = get_db()
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    active_tasks = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='active'").fetchone()["c"]
    overdue = db.execute("SELECT * FROM tasks WHERE status='active' AND due_date < ? AND due_date != ''", (today,)).fetchall()
    critical_tasks = db.execute("SELECT * FROM tasks WHERE priority='CRITICAL' AND status='active'").fetchall()
    all_tasks = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 100").fetchall()]
    db.close()
    xp = get_total_xp()
    level, rank = xp_to_level(xp)
    score = compute_productivity_score()
    momentum = compute_momentum()
    entropy, entropy_label = compute_entropy()
    load, load_label = compute_cognitive_load()
    threats = []
    for t in overdue:
        threats.append({"title": t["title"], "type": "OVERDUE TASK", "severity": "CRITICAL" if t["priority"]=="CRITICAL" else "ELEVATED"})
    for t in critical_tasks:
        if not any(th["title"]==t["title"] for th in threats):
            threats.append({"title": t["title"], "type": "CRITICAL PRIORITY", "severity": "ELEVATED"})
    if entropy_label == "CRITICAL":
        threats.append({"title": "ENTROPY CRITICAL", "type": "SYSTEM HEALTH", "severity": "CRITICAL"})
    elif entropy_label == "CHAOTIC":
        threats.append({"title": "HIGH ENTROPY DETECTED", "type": "SYSTEM HEALTH", "severity": "ELEVATED"})
    return jsonify({
        "productivity_score": score, "xp": xp, "level": level, "rank": rank,
        "active_tasks": active_tasks, "threats": len(threats), "threats_detail": threats,
        "momentum": momentum, "cognitive_load": load, "load_label": load_label,
        "entropy": entropy, "entropy_label": entropy_label, "tasks": all_tasks
    })

@app.route('/api/jp/briefing', methods=['POST'])
def jp_briefing():
    data = request.json or {}
    text = jp_analyze(data)
    return jsonify({"text": text})

@app.route('/api/jp/query', methods=['POST'])
def jp_query():
    data = request.json or {}
    query = data.get("query", "")
    db = get_db()
    tasks = [dict(r) for r in db.execute("SELECT * FROM tasks").fetchall()]
    vitals = dict(db.execute("SELECT * FROM vitals ORDER BY date DESC LIMIT 1").fetchone() or {})
    db.close()
    xp = get_total_xp()
    score = compute_productivity_score()
    momentum = compute_momentum()
    app_data = {"tasks": tasks, "vitals": vitals, "xp": xp, "productivity_score": score, "momentum": momentum}
    response = jp_respond_to_query(query, app_data)
    return jsonify({"response": response})

@app.route('/api/jp/decision', methods=['POST'])
def jp_decision():
    data = request.json or {}
    decision = data.get("decision", "")
    db = get_db()
    tasks_active = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='active'").fetchone()["c"]
    vitals = db.execute("SELECT * FROM vitals ORDER BY date DESC LIMIT 1").fetchone()
    month_start = datetime.date.today().replace(day=1).isoformat()
    income = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='income' AND date >= ?", (month_start,)).fetchone()["t"]
    expenses = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='expense' AND date >= ?", (month_start,)).fetchone()["t"]
    db.close()
    score = compute_productivity_score()
    entropy, entropy_label = compute_entropy()
    load, load_label = compute_cognitive_load()
    energy = vitals["energy_level"] if vitals and vitals["energy_level"] else 5
    sleep = vitals["sleep_hours"] if vitals and vitals["sleep_hours"] else 7
    balance = income - expenses
    response_parts = [f"Decision analysis for: '{decision}'."]
    if load_label == "OVERLOADED":
        response_parts.append("Chief, your cognitive load is currently elevated. I advise against adding major new commitments until the current backlog clears.")
    if energy < 5:
        response_parts.append(f"Energy level is logged at {energy}/10. Sub-optimal state for high-stakes decisions. Recommend sleeping on this.")
    if balance < 0 and any(w in decision.lower() for w in ["buy","spend","invest","hire","pay"]):
        response_parts.append(f"Financial data shows negative monthly balance of {abs(balance):.0f}. Any expenditure decision carries elevated risk at this time.")
    if tasks_active > 10:
        response_parts.append(f"You currently have {tasks_active} active tasks. Taking on new responsibilities may compound the backlog.")
    if entropy_label in ["CHAOTIC","CRITICAL"]:
        response_parts.append("System entropy is high. New initiatives tend to fail when launched from chaotic operational states.")
    response_parts.append("Recommendation: Proceed only if this decision directly serves your top 3 current priorities. If it does not, defer it to the War Room planning session.")
    return jsonify({"response": " ".join(response_parts)})

@app.route('/api/tasks')
def get_tasks():
    db = get_db()
    tasks = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY CASE priority WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 ELSE 2 END, created_at DESC").fetchall()]
    db.close()
    return jsonify({"tasks": tasks})

@app.route('/api/tasks', methods=['POST'])
def add_task():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO tasks (title,priority,due_date,estimated_mins) VALUES (?,?,?,?)", (d["title"],d.get("priority","HIGH"),d.get("due_date",""),d.get("estimated_mins",30)))
    db.commit()
    db.close()
    award_xp(5, "task_added")
    return jsonify({"ok": True})

@app.route('/api/tasks/<int:tid>/complete', methods=['POST'])
def complete_task(tid):
    db = get_db()
    db.execute("UPDATE tasks SET status='done', completed_at=? WHERE id=?", (datetime.datetime.now().isoformat(), tid))
    db.commit()
    db.close()
    award_xp(20, "task_completed")
    return jsonify({"ok": True})

@app.route('/api/tasks/<int:tid>/reopen', methods=['POST'])
def reopen_task(tid):
    db = get_db()
    db.execute("UPDATE tasks SET status='active', completed_at=NULL WHERE id=?", (tid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
def delete_task(tid):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id=?", (tid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/projects')
def get_projects():
    db = get_db()
    projects = [dict(r) for r in db.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()]
    for p in projects:
        p["phases"] = [dict(r) for r in db.execute("SELECT * FROM project_phases WHERE project_id=? ORDER BY order_num", (p["id"],)).fetchall()]
    db.close()
    return jsonify({"projects": projects})

@app.route('/api/projects', methods=['POST'])
def add_project():
    d = request.json
    db = get_db()
    cur = db.execute("INSERT INTO projects (name,description,deadline) VALUES (?,?,?)", (d["name"],d.get("description",""),d.get("deadline","")))
    pid = cur.lastrowid
    for i, phase in enumerate(d.get("phases", [])):
        db.execute("INSERT INTO project_phases (project_id,name,order_num) VALUES (?,?,?)", (pid, phase, i))
    db.commit()
    db.close()
    award_xp(30, "project_created")
    return jsonify({"ok": True})

@app.route('/api/projects/<int:pid>', methods=['DELETE'])
def delete_project(pid):
    db = get_db()
    db.execute("DELETE FROM project_phases WHERE project_id=?", (pid,))
    db.execute("DELETE FROM projects WHERE id=?", (pid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/phases/<int:phid>/toggle', methods=['POST'])
def toggle_phase(phid):
    db = get_db()
    cur = db.execute("SELECT status FROM project_phases WHERE id=?", (phid,)).fetchone()
    new_status = "done" if cur["status"] == "pending" else "pending"
    db.execute("UPDATE project_phases SET status=? WHERE id=?", (new_status, phid))
    db.commit()
    db.close()
    if new_status == "done":
        award_xp(15, "phase_completed")
    return jsonify({"ok": True})

@app.route('/api/pomodoro/start', methods=['POST'])
def start_pomo():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO pomodoros (duration_mins,mode) VALUES (?,?)", (d.get("duration",25), d.get("mode","deep")))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/pomodoro/complete', methods=['POST'])
def complete_pomo():
    db = get_db()
    latest = db.execute("SELECT id FROM pomodoros ORDER BY id DESC LIMIT 1").fetchone()
    if latest:
        db.execute("UPDATE pomodoros SET completed=1, ended_at=? WHERE id=?", (datetime.datetime.now().isoformat(), latest["id"]))
    db.commit()
    db.close()
    award_xp(15, "pomodoro_completed")
    return jsonify({"ok": True})

@app.route('/api/pomodoro/stats')
def pomo_stats():
    db = get_db()
    today = datetime.date.today().isoformat()
    today_count = db.execute("SELECT COUNT(*) as c FROM pomodoros WHERE completed=1 AND DATE(started_at)=?", (today,)).fetchone()["c"]
    week_data = []
    for i in range(6, -1, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        c = db.execute("SELECT COUNT(*) as c FROM pomodoros WHERE completed=1 AND DATE(started_at)=?", (d,)).fetchone()["c"]
        week_data.append(c)
    db.close()
    return jsonify({"today": today_count, "week_data": week_data})

@app.route('/api/finance')
def get_finance():
    db = get_db()
    transactions = [dict(r) for r in db.execute("SELECT * FROM finances ORDER BY date DESC LIMIT 50").fetchall()]
    month_start = datetime.date.today().replace(day=1).isoformat()
    monthly_income = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='income' AND date>=?", (month_start,)).fetchone()["t"]
    monthly_expenses = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='expense' AND date>=?", (month_start,)).fetchone()["t"]
    labels, inc_data, exp_data = [], [], []
    for i in range(5, -1, -1):
        d = datetime.date.today().replace(day=1) - datetime.timedelta(days=i*28)
        ms = d.replace(day=1).isoformat()
        me = (d.replace(day=1) + datetime.timedelta(days=32)).replace(day=1).isoformat()
        labels.append(d.strftime("%b"))
        inc = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='income' AND date>=? AND date<?", (ms,me)).fetchone()["t"]
        exp = db.execute("SELECT COALESCE(SUM(amount),0) as t FROM finances WHERE type='expense' AND date>=? AND date<?", (ms,me)).fetchone()["t"]
        inc_data.append(round(inc))
        exp_data.append(round(exp))
    db.close()
    return jsonify({"transactions": transactions, "monthly_income": monthly_income, "monthly_expenses": monthly_expenses, "monthly_labels": labels, "monthly_income_data": inc_data, "monthly_expense_data": exp_data})

@app.route('/api/finance', methods=['POST'])
def add_finance():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO finances (type,category,amount,description,date) VALUES (?,?,?,?,?)", (d["type"],d.get("category","other"),d["amount"],d.get("description",""),d.get("date",datetime.date.today().isoformat())))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/finance/<int:fid>', methods=['DELETE'])
def delete_finance(fid):
    db = get_db()
    db.execute("DELETE FROM finances WHERE id=?", (fid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/vitals')
def get_vitals():
    db = get_db()
    today = datetime.date.today().isoformat()
    today_vitals = db.execute("SELECT * FROM vitals WHERE date=?", (today,)).fetchone()
    labels, sleep_data, energy_data = [], [], []
    for i in range(6, -1, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        labels.append(datetime.date.fromisoformat(d).strftime("%a"))
        row = db.execute("SELECT * FROM vitals WHERE date=?", (d,)).fetchone()
        sleep_data.append(row["sleep_hours"] if row and row["sleep_hours"] else 0)
        energy_data.append(row["energy_level"] if row and row["energy_level"] else 0)
    db.close()
    return jsonify({"today": dict(today_vitals) if today_vitals else None, "labels": labels, "sleep_data": sleep_data, "energy_data": energy_data})

@app.route('/api/vitals', methods=['POST'])
def log_vitals():
    d = request.json
    today = datetime.date.today().isoformat()
    db = get_db()
    existing = db.execute("SELECT id FROM vitals WHERE date=?", (today,)).fetchone()
    if existing:
        db.execute("UPDATE vitals SET sleep_hours=?,sleep_quality=?,water_ml=?,calories=?,workout_mins=?,energy_level=?,weight=? WHERE date=?",
                   (d.get("sleep_hours"),d.get("sleep_quality"),d.get("water_ml"),d.get("calories"),d.get("workout_mins"),d.get("energy_level",5),d.get("weight"),today))
    else:
        db.execute("INSERT INTO vitals (date,sleep_hours,sleep_quality,water_ml,calories,workout_mins,energy_level,weight) VALUES (?,?,?,?,?,?,?,?)",
                   (today,d.get("sleep_hours"),d.get("sleep_quality"),d.get("water_ml"),d.get("calories"),d.get("workout_mins"),d.get("energy_level",5),d.get("weight")))
    db.commit()
    db.close()
    award_xp(10, "vitals_logged")
    return jsonify({"ok": True})

@app.route('/api/opstats')
def get_opstats():
    db = get_db()
    xp = get_total_xp()
    level, rank = xp_to_level(xp)
    score = compute_productivity_score()
    total_done = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='done'").fetchone()["c"]
    total_pomos = db.execute("SELECT COUNT(*) as c FROM pomodoros WHERE completed=1").fetchone()["c"]
    heatmap = []
    for i in range(27, -1, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        tasks = db.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(completed_at)=?", (d,)).fetchone()["c"]
        pomos = db.execute("SELECT COUNT(*) as c FROM pomodoros WHERE completed=1 AND DATE(started_at)=?", (d,)).fetchone()["c"]
        heatmap.append(min((tasks*15)+(pomos*10),100))
    task_score = min(total_done*2, 100)
    proj_done = db.execute("SELECT COUNT(*) as c FROM project_phases WHERE status='done'").fetchone()["c"]
    proj_score = min(proj_done*5, 100)
    fin_data = db.execute("SELECT COUNT(*) as c FROM finances").fetchone()["c"]
    fin_score = min(fin_data*5, 100)
    vitals_count = db.execute("SELECT COUNT(*) as c FROM vitals").fetchone()["c"]
    health_score = min(vitals_count*7, 100)
    avg_tasks = round(total_done / max(1, 30), 1)
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_counts = []
    for i, day in enumerate(days):
        c = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='done' AND strftime('%w',completed_at)=?", (str((i+1)%7),)).fetchone()["c"]
        day_counts.append(c)
    best_day = days[day_counts.index(max(day_counts))] if any(day_counts) else "Monday"
    db.close()
    return jsonify({"xp":xp,"level":level,"rank":rank,"productivity_score":score,"streak":1,"best_score":score,"max_tasks_day":max(heatmap),"total_done":total_done,"total_pomos":total_pomos,"avg_tasks_day":avg_tasks,"best_day":best_day,"heatmap":heatmap,"radar":[task_score,proj_score,min(total_pomos*3,100),fin_score,health_score]})

@app.route('/api/forge')
def get_forge():
    db = get_db()
    items = [dict(r) for r in db.execute("SELECT * FROM forge_items ORDER BY mastery DESC").fetchall()]
    db.close()
    return jsonify({"items": items})

@app.route('/api/forge', methods=['POST'])
def add_forge():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO forge_items (name,type,notes) VALUES (?,?,?)", (d["name"],d.get("type","skill"),d.get("notes","")))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/forge/<int:fid>/session', methods=['POST'])
def log_forge_session(fid):
    d = request.json
    db = get_db()
    db.execute("INSERT INTO forge_sessions (item_id,duration_mins,quality,notes) VALUES (?,?,?,?)", (fid,d.get("duration_mins",60),d.get("quality",3),d.get("notes","")))
    item = db.execute("SELECT * FROM forge_items WHERE id=?", (fid,)).fetchone()
    new_sessions = (item["sessions"] or 0) + 1
    new_mins = (item["total_mins"] or 0) + d.get("duration_mins", 60)
    mastery_gain = min(d.get("quality",3) * 3, 15)
    new_mastery = min((item["mastery"] or 0) + mastery_gain, 100)
    db.execute("UPDATE forge_items SET sessions=?,total_mins=?,mastery=?,last_session=? WHERE id=?", (new_sessions,new_mins,new_mastery,datetime.date.today().isoformat(),fid))
    db.commit()
    db.close()
    award_xp(12, "forge_session")
    return jsonify({"ok": True})

@app.route('/api/forge/<int:fid>', methods=['DELETE'])
def delete_forge(fid):
    db = get_db()
    db.execute("DELETE FROM forge_sessions WHERE item_id=?", (fid,))
    db.execute("DELETE FROM forge_items WHERE id=?", (fid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/social')
def get_social():
    db = get_db()
    contacts = [dict(r) for r in db.execute("SELECT * FROM social ORDER BY name").fetchall()]
    db.close()
    return jsonify({"contacts": contacts})

@app.route('/api/social', methods=['POST'])
def add_social():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO social (name,relationship,contact_frequency_days,notes) VALUES (?,?,?,?)", (d["name"],d.get("relationship",""),d.get("contact_frequency_days",14),d.get("notes","")))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/social/<int:sid>/contact', methods=['POST'])
def log_contact(sid):
    db = get_db()
    db.execute("UPDATE social SET last_contact=?,health=100 WHERE id=?", (datetime.date.today().isoformat(),sid))
    db.commit()
    db.close()
    award_xp(5, "social_contact")
    return jsonify({"ok": True})

@app.route('/api/social/<int:sid>', methods=['DELETE'])
def delete_social(sid):
    db = get_db()
    db.execute("DELETE FROM social WHERE id=?", (sid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/journal')
def get_journal():
    shadow = request.args.get('shadow', '0')
    db = get_db()
    entries = [dict(r) for r in db.execute("SELECT * FROM journal WHERE is_shadow=? ORDER BY created_at DESC", (shadow,)).fetchall()]
    db.close()
    return jsonify({"entries": entries})

@app.route('/api/journal', methods=['POST'])
def add_journal():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO journal (content,mood,tags,is_shadow) VALUES (?,?,?,?)", (d["content"],d.get("mood",7),d.get("tags",""),d.get("is_shadow",0)))
    db.commit()
    db.close()
    award_xp(8, "journal_entry")
    return jsonify({"ok": True})

@app.route('/api/goals')
def get_goals():
    db = get_db()
    goals = [dict(r) for r in db.execute("SELECT * FROM goals ORDER BY created_at DESC").fetchall()]
    db.close()
    return jsonify({"goals": goals})

@app.route('/api/goals', methods=['POST'])
def add_goal():
    d = request.json
    db = get_db()
    db.execute("INSERT INTO goals (title,type,target_date,notes) VALUES (?,?,?,?)", (d["title"],d.get("type","public"),d.get("target_date",""),d.get("notes","")))
    db.commit()
    db.close()
    award_xp(15, "goal_set")
    return jsonify({"ok": True})

@app.route('/api/goals/<int:gid>/progress', methods=['POST'])
def update_goal_progress(gid):
    d = request.json
    db = get_db()
    db.execute("UPDATE goals SET progress=? WHERE id=?", (d["progress"],gid))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/goals/<int:gid>', methods=['DELETE'])
def delete_goal(gid):
    db = get_db()
    db.execute("DELETE FROM goals WHERE id=?", (gid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route('/api/warroom')
def get_warroom():
    db = get_db()
    reports = [dict(r) for r in db.execute("SELECT * FROM war_room ORDER BY created_at DESC LIMIT 10").fetchall()]
    db.close()
    return jsonify({"reports": reports})

@app.route('/api/warroom', methods=['POST'])
def add_warroom():
    d = request.json
    wins = d.get("wins","")
    losses = d.get("losses","")
    priorities = d.get("priorities","")
    score = compute_productivity_score()
    entropy, entropy_label = compute_entropy()
    momentum = compute_momentum()
    avg_momentum = round(sum(momentum)/max(len(momentum),1))
    plan = f"""WEEKLY BATTLE PLAN — {datetime.date.today().strftime('%d %B %Y')}

LAST WEEK DEBRIEF:
Wins logged: {wins if wins else 'None recorded.'}
Gaps identified: {losses if losses else 'None recorded.'}

THIS WEEK'S PRIORITY MISSIONS:
{priorities if priorities else 'No priorities set.'}

JEAN-PHILIP ASSESSMENT:
Productivity score entering this week: {score}/100.
Momentum index: {avg_momentum}/100 — {'Strong momentum. Maintain operational tempo.' if avg_momentum > 60 else 'Momentum requires rebuilding. Start with quick wins.'}
System entropy: {entropy_label} — {'All clear. Proceed with ambitious targets.' if entropy_label == 'STABLE' else 'Recalibrate before taking on new missions.'}

TACTICAL RECOMMENDATIONS:
1. Address all CRITICAL tasks within first 48 hours.
2. Schedule one deep work block per day, minimum 25 minutes.
3. Review this plan on Thursday and adjust if needed.
4. Log vitals daily — recovery directly impacts execution.

DIRECTIVE: Execute with precision. One mission at a time. Stay in the fight, Chief."""
    db = get_db()
    week_start = datetime.date.today().strftime('%d %b %Y')
    db.execute("INSERT INTO war_room (week_start,wins,losses,priorities,battle_plan) VALUES (?,?,?,?,?)", (week_start,wins,losses,priorities,plan))
    db.commit()
    db.close()
    return jsonify({"plan": plan})

if __name__ == '__main__':
    init_db()
    threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(debug=False, port=5000)
