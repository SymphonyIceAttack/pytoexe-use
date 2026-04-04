import webview
import os
import json
import shutil
import webbrowser

class TrackerAPI:
    def __init__(self):
        # Create a physical folder on the computer to store 100MB+ PDFs and data
        self.app_dir = os.path.join(os.path.expanduser('~'), '.liquid_tracker_data')
        self.pdf_dir = os.path.join(self.app_dir, 'pdfs')
        self.data_file = os.path.join(self.app_dir, 'tracker_state.json')
        
        os.makedirs(self.pdf_dir, exist_ok=True)

    def save_state(self, state_json):
        # Saves the tracker progress (notes, streaks, dates) to a physical JSON file
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                f.write(state_json)
            return True
        except Exception as e:
            print("Save error:", e)
            return False

    def load_state(self):
        # Loads the tracker progress on startup
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                pass
        return None

    def select_pdf(self, key):
        # Opens the native OS File Picker, completely bypassing browser memory limits
        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.OPEN_DIALOG, 
            allow_multiple=False, 
            file_types=('PDF Files (*.pdf)', 'All Files (*.*)')
        )
        
        if result:
            source_path = result[0]
            filename = os.path.basename(source_path)
            # We add the day key to the filename so they don't overwrite each other
            dest_path = os.path.join(self.pdf_dir, f"{key}_{filename}")
            
            # Copy the massive file physically on the hard drive
            shutil.copy2(source_path, dest_path)
            
            return {
                "success": True, 
                "filename": filename, 
                "path": dest_path, 
                "size": os.path.getsize(dest_path)
            }
        return {"success": False}

    def view_pdf(self, path):
        # Opens the massive PDF natively in your default computer PDF viewer (e.g. Adobe Acrobat / Chrome)
        if os.path.exists(path):
            webbrowser.open('file://' + os.path.realpath(path))

    def delete_pdf(self, path):
        # Cleans up the hard drive when you remove a PDF
        if os.path.exists(path):
            os.remove(path)


def launch_tracker():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>21 Day Challenge</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');
*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #F7F4EF; --bg2: #EFEDE8; --surface: rgba(255,255,255,0.85); --surface2: rgba(255,255,255,0.6);
  --border: rgba(0,0,0,0.09); --border2: rgba(0,0,0,0.06); --ink: #1A1A18; --ink2: #5A5A52; --ink3: #9A9A90;
  --accent: #7FA87A; --accent2: #C4956A; --accent-bg: rgba(127,168,122,0.12); --accent2-bg: rgba(196,149,106,0.12);
  --radius: 18px; --radius-sm: 10px; --ease: cubic-bezier(0.34, 1.56, 0.64, 1); --ease-s: cubic-bezier(0.25, 1, 0.5, 1);
}
.theme-dark { --bg: #141412; --bg2: #1C1C1A; --surface: rgba(30,30,28,0.9); --surface2: rgba(40,40,38,0.7); --border: rgba(255,255,255,0.1); --border2: rgba(255,255,255,0.06); --ink: #F0EDE8; --ink2: #A0A098; --ink3: #606058; --accent: #8FBF8A; --accent2: #D4A574; --accent-bg: rgba(143,191,138,0.15); --accent2-bg: rgba(212,165,116,0.15); }
.theme-rose { --bg: #FDF4F4; --bg2: #F8ECEC; --surface: rgba(255,255,255,0.9); --surface2: rgba(255,248,248,0.7); --border: rgba(180,80,80,0.1); --border2: rgba(180,80,80,0.06); --ink: #2A1A1A; --ink2: #7A5252; --ink3: #B09090; --accent: #C47A7A; --accent2: #E8A87A; --accent-bg: rgba(196,122,122,0.12); --accent2-bg: rgba(232,168,122,0.12); }
.theme-ocean { --bg: #F0F4F9; --bg2: #E8EEF6; --surface: rgba(255,255,255,0.88); --surface2: rgba(240,246,255,0.7); --border: rgba(50,100,180,0.1); --border2: rgba(50,100,180,0.06); --ink: #1A1E2A; --ink2: #4A5272; --ink3: #8A92B0; --accent: #5A82C4; --accent2: #7ABCCC; --accent-bg: rgba(90,130,196,0.12); --accent2-bg: rgba(122,188,204,0.12); }
.theme-glass { --bg: #C8D8E8; --bg2: #B8C8D8; --surface: rgba(255,255,255,0.18); --surface2: rgba(255,255,255,0.1); --border: rgba(255,255,255,0.4); --border2: rgba(255,255,255,0.2); --ink: #0A0A12; --ink2: #2A2A3A; --ink3: #5A5A6A; --accent: #4A8AE8; --accent2: #E85A8A; --accent-bg: rgba(74,138,232,0.2); --accent2-bg: rgba(232,90,138,0.2); }
.app { font-family: 'DM Sans', sans-serif; background: var(--bg); min-height: 100vh; color: var(--ink); transition: background 0.5s ease, color 0.5s ease; position: relative; overflow: hidden; padding: 1.5rem 1rem 3rem; }
.theme-glass .app { background: linear-gradient(135deg, #8ECAE6 0%, #A8DADC 25%, #CDB4DB 50%, #FFC8DD 75%, #BDE0FE 100%); }
.orb { position: fixed; border-radius: 50%; filter: blur(70px); pointer-events: none; z-index: 0; transition: all 0.8s ease; }
.orb1 { width: 500px; height: 500px; background: radial-gradient(circle, var(--accent-bg) 0%, transparent 70%); top: -150px; right: -100px; animation: floatOrb 8s ease-in-out infinite alternate; }
.orb2 { width: 350px; height: 350px; background: radial-gradient(circle, var(--accent2-bg) 0%, transparent 70%); bottom: -80px; left: -80px; animation: floatOrb 10s ease-in-out infinite alternate-reverse; }
@keyframes floatOrb { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(30px,-40px) scale(1.1); } }
.inner { max-width: 700px; margin: 0 auto; position: relative; z-index: 1; }
.theme-bar { display: flex; gap: 8px; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap; animation: fadeUp 0.5s var(--ease-s) both; }
.theme-btn { display: flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 99px; border: 1px solid var(--border); background: var(--surface); color: var(--ink2); font-size: 13px; font-family: inherit; cursor: pointer; transition: all 0.3s var(--ease); font-weight: 500; backdrop-filter: blur(8px); }
.theme-btn:hover { border-color: var(--accent); color: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.theme-btn.active { background: var(--accent); color: white; border-color: var(--accent); transform: scale(1.05); }
.theme-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.glass-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); backdrop-filter: blur(20px) saturate(1.8); -webkit-backdrop-filter: blur(20px) saturate(1.8); transition: background 0.4s, border 0.4s, transform 0.3s var(--ease), box-shadow 0.3s var(--ease); position: relative; overflow: hidden; }
.theme-glass .glass-card { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.45); box-shadow: 0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.6), inset 0 -1px 0 rgba(255,255,255,0.1); backdrop-filter: blur(24px) saturate(2) brightness(1.05); }
.theme-glass .glass-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.8), rgba(255,255,255,0.4), transparent); pointer-events: none; }
.theme-glass .glass-card::after { content: ''; position: absolute; top: 0; left: -100%; width: 60%; height: 100%; background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.15) 50%, transparent 60%); pointer-events: none; animation: glassShimmer 6s ease-in-out infinite; }
@keyframes glassShimmer { 0%{left:-100%;} 100%{left:200%;} }
.hero { text-align: center; margin-bottom: 2.5rem; animation: fadeUp 0.6s var(--ease-s) 0.05s both; }
.eyebrow { font-size: 12px; letter-spacing: 4px; text-transform: uppercase; color: var(--accent); margin-bottom: 12px; font-weight: 500; }
.hero-title { font-family: 'DM Serif Display', serif; font-size: clamp(36px, 8vw, 56px); line-height: 1.1; color: var(--ink); }
.hero-title em { font-style: italic; color: var(--accent); }
.hero-sub { font-size: 15px; color: var(--ink3); margin-top: 8px; font-weight: 300; }
.setup { padding: 1.5rem; margin-bottom: 1.5rem; animation: fadeUp 0.6s var(--ease-s) 0.1s both; }
.setup-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 140px; }
.field label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--ink3); font-weight: 500; }
.field input { font-family: inherit; font-size: 14px; padding: 12px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface2); color: var(--ink); outline: none; transition: all 0.3s var(--ease); backdrop-filter: blur(8px); }
.field input:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-bg); background: var(--surface); }
.begin-btn { font-family: inherit; font-size: 14px; font-weight: 600; padding: 12px 28px; border-radius: var(--radius-sm); border: none; background: var(--ink); color: var(--bg); cursor: pointer; transition: all 0.3s var(--ease); white-space: nowrap; }
.begin-btn:hover { opacity: 0.9; transform: translateY(-2px) scale(1.02); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.begin-btn:active { transform: scale(0.98); }
.theme-glass .begin-btn { background: rgba(255,255,255,0.3); color: var(--ink); border: 1px solid rgba(255,255,255,0.6); backdrop-filter: blur(12px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-bottom: 1.5rem; animation: fadeUp 0.6s var(--ease-s) 0.15s both; }
.stat { padding: 1.25rem; text-align: center; }
.stat:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
.stat-l { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--ink3); margin-bottom: 6px; font-weight: 500; }
.stat-v { font-family: 'DM Serif Display', serif; font-size: 40px; line-height: 1; }
.stat-v.a1 { color: var(--accent); }
.stat-v.a2 { color: var(--accent2); }
.prog-wrap { margin-bottom: 1.5rem; animation: fadeUp 0.6s var(--ease-s) 0.2s both; }
.prog-meta { display: flex; justify-content: space-between; margin-bottom: 8px; }
.prog-meta span { font-size: 13px; color: var(--ink3); font-weight: 500; }
.prog-meta strong { font-size: 13px; color: var(--accent); font-weight: 600; }
.prog-track { height: 6px; background: var(--border2); border-radius: 99px; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05); }
.prog-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent2)); border-radius: 99px; transition: width 0.8s cubic-bezier(0.25, 1, 0.5, 1); }
.grid-section { margin-bottom: 1.5rem; }
.wday-row { display: grid; grid-template-columns: repeat(7,1fr); gap: 8px; margin-bottom: 8px; animation: fadeUp 0.6s var(--ease-s) 0.25s both; }
.wday-row span { font-size: 10px; text-align: center; letter-spacing: 1.5px; text-transform: uppercase; color: var(--ink3); font-weight: 600; }
.grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 8px; }
.day { aspect-ratio: 1; border-radius: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; position: relative; overflow: hidden; background: var(--surface2); border: 1px solid var(--border2); transition: all 0.3s var(--ease); gap: 2px; opacity: 0; transform: translateY(15px); }
.day:not(.future):hover { transform: translateY(-4px) scale(1.08); border-color: var(--accent); box-shadow: 0 8px 16px rgba(0,0,0,0.08); z-index: 5; background: var(--surface); }
.day.done { background: var(--accent); border-color: var(--accent); transform: scale(1); }
.day.done:hover { transform: translateY(-4px) scale(1.08); }
.day.done .dn { color: white; }
.day.done .dw { color: rgba(255,255,255,0.8); }
.day.today { border-color: var(--accent2); border-width: 2px; box-shadow: 0 0 0 3px var(--accent2-bg); }
.day.today .dn { color: var(--accent2); font-weight: 600; }
.day.future { opacity: 0.3 !important; cursor: default; pointer-events: none; }
.day.has-pdf .pdf-pip { display: block !important; }
.day.has-note .note-pip { display: block !important; }
.dn { font-size: 15px; font-weight: 500; color: var(--ink); position: relative; z-index: 1; transition: color 0.3s; }
.dw { font-size: 10px; letter-spacing: 0.5px; text-transform: uppercase; color: var(--ink3); position: relative; z-index: 1; transition: color 0.3s; }
.pip-row { display: flex; gap: 3px; position: absolute; top: 6px; right: 6px; z-index: 2; }
.pdf-pip, .note-pip { width: 6px; height: 6px; border-radius: 50%; display: none; }
.pdf-pip { background: var(--accent2); }
.note-pip { background: var(--accent); animation: pulse-pip 2s ease-in-out infinite; }
@keyframes pulse-pip { 0%,100%{transform:scale(1);opacity:1;} 50%{transform:scale(1.3);opacity:0.6;} }
.check-svg { position: absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:2; pointer-events:none; }
.check-svg svg { opacity:0; transform:scale(0.5) rotate(-30deg); transition: all 0.4s var(--ease); stroke-dasharray: 20; stroke-dashoffset: 20; }
.day.done .check-svg svg { opacity:1; transform:scale(1.2) rotate(0deg); stroke-dashoffset: 0; }
.day.done .dn, .day.done .dw { opacity: 0.15; }
.theme-glass .day:not(.done) { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.4); backdrop-filter: blur(16px) saturate(1.8); box-shadow: inset 0 1px 0 rgba(255,255,255,0.5), 0 2px 8px rgba(0,0,0,0.05); }
.theme-glass .day:not(.future):hover { background: rgba(255,255,255,0.3); box-shadow: inset 0 1px 0 rgba(255,255,255,0.8), 0 8px 20px rgba(0,0,0,0.1); }
.theme-glass .day.done { background: rgba(74,138,232,0.4); border-color: rgba(74,138,232,0.6); box-shadow: inset 0 1px 0 rgba(255,255,255,0.5), 0 4px 16px rgba(74,138,232,0.25); }
.panel { padding: 1.75rem; animation: slideUp 0.4s var(--ease) both; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; }
.panel-title { font-family: 'DM Serif Display', serif; font-size: 24px; color: var(--ink); line-height: 1; }
.panel-date { font-size: 13px; color: var(--ink3); margin-top: 4px; font-weight: 500; }
.close-btn { width: 32px; height: 32px; border-radius: 50%; border: 1px solid var(--border); background: var(--surface2); color: var(--ink2); cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: all 0.3s var(--ease); flex-shrink: 0; }
.close-btn:hover { transform: scale(1.15) rotate(90deg); background: var(--accent-bg); border-color: var(--accent); color: var(--accent); }
.tabs { display: flex; gap: 8px; margin-bottom: 1.25rem; }
.tab { padding: 8px 16px; border-radius: 99px; font-size: 13px; font-weight: 500; font-family: inherit; border: 1px solid var(--border); background: transparent; color: var(--ink3); cursor: pointer; transition: all 0.3s var(--ease); }
.tab:hover { background: var(--surface2); color: var(--ink); }
.tab.active { background: var(--accent); color: white; border-color: var(--accent); transform: scale(1.05); }
.tab-content { display: none; }
.tab-content.visible { display: block; animation: fadeUp 0.3s var(--ease-s) both; }
.note-ta { width: 100%; min-height: 100px; font-family: inherit; font-size: 14px; font-weight: 400; line-height: 1.6; padding: 14px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface2); color: var(--ink); resize: none; outline: none; transition: all 0.3s var(--ease); backdrop-filter: blur(8px); }
.note-ta::placeholder { color: var(--ink3); font-style: italic; }
.note-ta:focus { border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-bg); background: var(--surface); }
.note-hint { font-size: 11px; color: var(--ink3); text-align: right; margin-top: 8px; font-weight: 500; }
.save-status { color: var(--accent); transition: opacity 0.3s; opacity: 0; }
.save-status.show { opacity: 1; }

.pdf-drop { border: 2px dashed var(--border); border-radius: var(--radius-sm); padding: 2.5rem 1rem; text-align: center; cursor: pointer; transition: all 0.3s var(--ease); background: var(--surface2); }
.pdf-drop:hover { border-color: var(--accent2); background: var(--accent2-bg); transform: scale(1.02); }
.pdf-icon { font-size: 32px; margin-bottom: 8px; }
.pdf-drop p { font-size: 14px; color: var(--ink3); }
.pdf-drop strong { color: var(--accent2); font-weight: 600; }
.pdf-preview { display: flex; align-items: center; gap: 14px; padding: 14px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface); margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
.pdf-icon-sm { width: 40px; height: 40px; border-radius: 10px; background: var(--accent2-bg); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.pdf-info { flex: 1; min-width: 0; }
.pdf-name { font-size: 14px; font-weight: 600; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pdf-size { font-size: 12px; color: var(--ink3); margin-top: 4px; }
.pdf-actions { display: flex; gap: 8px; }
.pdf-btn { padding: 6px 14px; border-radius: var(--radius-sm); font-size: 12px; font-weight: 500; font-family: inherit; cursor: pointer; border: 1px solid var(--border); background: var(--surface2); color: var(--ink2); transition: all 0.3s var(--ease); }
.pdf-btn:hover { border-color: var(--accent2); color: var(--accent2); background: var(--surface); transform: translateY(-2px); }
.pdf-btn.danger { border-color: rgba(200,80,80,0.3); color: #C45050; }
.pdf-btn.danger:hover { background: rgba(200,80,80,0.1); color: #B33A3A; border-color: rgba(200,80,80,0.5); }

.mood-row { display: flex; gap: 10px; margin-bottom: 10px; }
.mood-btn { flex: 1; padding: 10px 4px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface2); font-size: 22px; cursor: pointer; text-align: center; transition: all 0.3s var(--ease); }
.mood-btn:hover { transform: translateY(-4px) scale(1.15); background: var(--surface); box-shadow: 0 8px 16px rgba(0,0,0,0.05); }
.mood-btn.selected { border-color: var(--accent); background: var(--accent-bg); transform: scale(1.1); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.mood-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--ink3); margin-bottom: 8px; font-weight: 600; }
.streak-banner { background: linear-gradient(135deg, var(--accent-bg), var(--accent2-bg)); border: 1px solid var(--accent); border-radius: var(--radius-sm); padding: 14px 18px; font-size: 14px; font-weight: 500; color: var(--ink); margin-bottom: 1.5rem; display: none; animation: bounceIn 0.6s var(--ease) both; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; }
.streak-banner.show { display: block; }
@keyframes bounceIn { 0% { transform: scale(0.9) translateY(10px); opacity: 0; } 100% { transform: scale(1) translateY(0); opacity: 1; } }
.confetti-piece { position: fixed; width: 10px; height: 10px; border-radius: 3px; pointer-events: none; z-index: 9999; animation: confettiFall 3s var(--ease-s) forwards; }
@keyframes confettiFall { 0% { transform: translateY(-20px) rotate(0deg) scale(1); opacity: 1; } 100% { transform: translateY(110vh) rotate(720deg) scale(0.5); opacity: 0; } }
.empty { text-align: center; padding: 3rem; color: var(--ink3); font-size: 15px; font-weight: 400; animation: fadeUp 0.6s var(--ease-s) both; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(30px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.8) translateY(15px); } to { opacity: 1; transform: scale(1) translateY(0); } }
</style>
</head>
<body>
<div class="app" id="app">
  <div class="orb orb1"></div>
  <div class="orb orb2"></div>
  <div class="inner">
    <div class="theme-bar">
      <button class="theme-btn active" onclick="setTheme('')" data-t=""><span class="theme-dot" style="background:#7FA87A;"></span>Sage</button>
      <button class="theme-btn" onclick="setTheme('dark')" data-t="dark"><span class="theme-dot" style="background:#2A2A28;border:1px solid #555;"></span>Dark</button>
      <button class="theme-btn" onclick="setTheme('rose')" data-t="rose"><span class="theme-dot" style="background:#C47A7A;"></span>Rose</button>
      <button class="theme-btn" onclick="setTheme('ocean')" data-t="ocean"><span class="theme-dot" style="background:#5A82C4;"></span>Ocean</button>
      <button class="theme-btn" onclick="setTheme('glass')" data-t="glass"><span class="theme-dot" style="background:linear-gradient(135deg,#8ECAE6,#CDB4DB);"></span>Liquid Glass</button>
    </div>
    <div class="hero">
      <div class="eyebrow">your journey</div>
      <h1 class="hero-title" id="htitle">21 <em>days</em></h1>
      <p class="hero-sub" id="hsub">Small steps. Big change.</p>
    </div>
    <div class="glass-card setup" id="setup-card">
      <div class="setup-row">
        <div class="field"><label>Challenge name</label><input type="text" id="name-in" placeholder="Morning runs, No sugar…" /></div>
        <div class="field" style="max-width:160px;"><label>Start date</label><input type="date" id="date-in" /></div>
        <button class="begin-btn" onclick="applySetup()">Begin Journey</button>
      </div>
    </div>
    <div id="tracker" style="display:none;">
      <div id="streak-banner" class="streak-banner"></div>
      <div class="stats">
        <div class="stat glass-card"><div class="stat-l">Completed</div><div class="stat-v a1" id="s-done">0</div></div>
        <div class="stat glass-card"><div class="stat-l">Streak 🔥</div><div class="stat-v" id="s-streak">0</div></div>
        <div class="stat glass-card"><div class="stat-l">Remaining</div><div class="stat-v a2" id="s-left">21</div></div>
      </div>
      <div class="prog-wrap">
        <div class="prog-meta"><span>Progress</span><strong id="ppct">0 / 21</strong></div>
        <div class="prog-track"><div class="prog-fill" id="pfill" style="width:0%"></div></div>
      </div>
      <div class="grid-section">
        <div class="wday-row"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div>
        <div class="grid" id="day-grid"></div>
      </div>
      <div id="panel-wrap" style="display:none;"><div class="glass-card panel" id="main-panel"></div></div>
    </div>
    <div id="empty-msg" class="empty"><p>Enter your challenge details above and press <strong>Begin Journey</strong></p></div>
  </div>
</div>

<script>
const S = { name:'', start:null, done:{}, notes:{}, moods:{}, pdfs:{}, active:null, activeTab:'note', theme: '' };
const nc = {};

// --- PYTHON API BRIDGE ---
function saveToLocal() {
  if (window.pywebview) {
    const dataToSave = { name: S.name, start: S.start ? S.start.toISOString() : null, done: S.done, notes: S.notes, moods: S.moods, pdfs: S.pdfs, theme: S.theme };
    window.pywebview.api.save_state(JSON.stringify(dataToSave)).then(() => {
      const status = document.getElementById('save-status');
      if (status) { status.classList.add('show'); setTimeout(() => status.classList.remove('show'), 1500); }
    });
  }
}

function loadFromLocal() {
  if (window.pywebview) {
    window.pywebview.api.load_state().then(saved => {
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          S.name = parsed.name || ''; S.start = parsed.start ? new Date(parsed.start) : null; S.done = parsed.done || {}; S.notes = parsed.notes || {}; S.moods = parsed.moods || {}; S.pdfs = parsed.pdfs || {}; S.theme = parsed.theme || '';
          if (S.theme) setTheme(S.theme);
          if (S.start) {
            document.getElementById('name-in').value = S.name; document.getElementById('date-in').value = dk(S.start);
            document.getElementById('empty-msg').style.display = 'none'; document.getElementById('tracker').style.display = 'block';
            document.getElementById('htitle').innerHTML = (S.name.length > 16 ? S.name.substring(0,14)+'…' : S.name) + ' <em>✦</em>';
            render();
          }
        } catch(e) {}
      }
    });
  }
}

// Ensure the API is ready before loading
window.addEventListener('pywebviewready', loadFromLocal);
// ------------------------

function pad(n){return String(n).padStart(2,'0');}
function dk(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
function addD(d,n){const r=new Date(d);r.setDate(r.getDate()+n);return r;}
function fmtSize(b){if(b<1024)return b+'B';if(b<1048576)return Math.round(b/1024)+'KB';return (b/1048576).toFixed(1)+'MB';}

function setTheme(t) { S.theme = t; const app = document.getElementById('app'); app.className = 'app' + (t ? ' theme-'+t : ''); document.querySelectorAll('.theme-btn').forEach(b => { b.classList.toggle('active', b.dataset.t === t); }); saveToLocal(); }
function applySetup() { const name = document.getElementById('name-in').value.trim(); const raw = document.getElementById('date-in').value; if(!raw) return; S.name = name || '21 Day Challenge'; S.start = new Date(raw+'T00:00:00'); saveToLocal(); document.getElementById('empty-msg').style.display = 'none'; document.getElementById('tracker').style.display = 'block'; document.getElementById('htitle').innerHTML = (S.name.length > 16 ? S.name.substring(0,14)+'…' : S.name) + ' <em>✦</em>'; render(); }

function render() {
  if(!S.start) return; const today = new Date(); today.setHours(0,0,0,0); let done=0, streak=0;
  for(let i=0;i<21;i++){ const d=addD(S.start,i); if(S.done[dk(d)]) done++; }
  let cur=0; for(let i=0;i<21;i++){ const d=addD(S.start,i); if(d>today) break; if(S.done[dk(d)]) cur++; else cur=0; streak=Math.max(streak,cur); }
  streak=cur; animNum('s-done',done); animNum('s-streak',streak); animNum('s-left',21-done);
  const pct=Math.round((done/21)*100); document.getElementById('pfill').style.width=pct+'%'; document.getElementById('ppct').textContent=done+' / 21 days';
  const dayIdx=Math.max(0,Math.floor((today-S.start)/86400000)); const dn=Math.min(21,dayIdx+1);
  const sub=today<S.start?'Starting '+S.start.toLocaleDateString('en',{month:'short',day:'numeric'}): done===21?'Challenge complete! 🎉': 'Day '+dn+' of 21 · '+pct+'% done';
  document.getElementById('hsub').textContent=sub;
  const banner=document.getElementById('streak-banner'); if(streak>=3){ banner.className='streak-banner show'; banner.textContent='🔥 '+streak+' day streak! You are unstoppable.'; } else { banner.className='streak-banner'; }
  buildGrid(today); if(S.active) renderPanel();
}

function animNum(id,val){ const el=document.getElementById(id); const prev=nc[id]||0; if(prev===val){el.textContent=val;return;} nc[id]=val; let st=null; const dur=400; function step(ts){ if(!st)st=ts; const p=Math.min((ts-st)/dur,1); el.textContent=Math.round(prev+(val-prev)*p); if(p<1)requestAnimationFrame(step); else el.textContent=val; } requestAnimationFrame(step); }

function buildGrid(today){
  const grid=document.getElementById('day-grid');
  if(grid.children.length===0){
    for(let i=0;i<21;i++){
      const d=addD(S.start,i); const wd=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][(d.getDay()+6)%7]; const cell=document.createElement('div'); cell.className='day'; cell.style.animation = `scaleIn 0.5s var(--ease) ${0.1 + (i * 0.03)}s forwards`; cell.innerHTML=`<div class="pip-row"><span class="pdf-pip"></span><span class="note-pip"></span></div><div class="check-svg"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17L4 12" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></div><span class="dn">${pad(i+1)}</span><span class="dw">${wd}</span>`;
      if(d>today){ cell.classList.add('future'); } else { if(dk(d)===dk(today)) cell.classList.add('today'); cell.addEventListener('click',()=>clickDay(dk(d),i+1,d)); }
      grid.appendChild(cell);
    }
  }
  for(let i=0;i<21;i++){ const d=addD(S.start,i); const k=dk(d); const c=grid.children[i]; c.classList.toggle('done',!!S.done[k]); c.classList.toggle('has-note',!!(S.notes[k]&&S.notes[k].trim())); c.classList.toggle('has-pdf',!!(S.pdfs[k])); }
}

function clickDay(key,dayNum,date){ S.done[key]=!S.done[key]; S.active={key,dayNum,date}; S.activeTab='note'; saveToLocal(); if(S.done[key] && Object.values(S.done).filter(Boolean).length===21) fireConfetti(); render(); }

function renderPanel(){
  const wrap=document.getElementById('panel-wrap'); const panel=document.getElementById('main-panel'); if(!S.active){wrap.style.display='none';return;} wrap.style.display='block';
  const{key,dayNum,date}=S.active; const label=date.toLocaleDateString('en',{weekday:'long',month:'long',day:'numeric'}); const pdf=S.pdfs[key]; const moods=['😊','😐','😔','🔥','😴'];
  panel.innerHTML=`
    <div class="panel-head"><div><div class="panel-title">Day ${dayNum}</div><div class="panel-date">${label}</div></div><button class="close-btn" onclick="closePanel()">✕</button></div>
    <div class="mood-label">How are you feeling?</div><div class="mood-row">${moods.map(m=>`<button class="mood-btn${S.moods[key]===m?' selected':''}" onclick="setMood('${key}','${m}',this)">${m}</button>`).join('')}</div>
    <div class="tabs"><button class="tab${S.activeTab==='note'?' active':''}" onclick="switchTab('note')">📝 Note</button><button class="tab${S.activeTab==='pdf'?' active':''}" onclick="switchTab('pdf')">📎 Document</button></div>
    <div class="tab-content${S.activeTab==='note'?' visible':''}" id="tc-note"><textarea class="note-ta" id="note-ta" placeholder="How did it go? Any reflections, wins, struggles…" rows="4">${S.notes[key]||''}</textarea><div class="note-hint"><span id="save-status" class="save-status">✓ Saved</span> Auto-saved as you type</div></div>
    <div class="tab-content${S.activeTab==='pdf'?' visible':''}" id="tc-pdf">
      ${pdf ? `<div class="pdf-preview"><div class="pdf-icon-sm">📄</div><div class="pdf-info"><div class="pdf-name">${pdf.name}</div><div class="pdf-size">${fmtSize(pdf.size)}</div></div><div class="pdf-actions"><button class="pdf-btn" onclick="viewPdf('${key}')">View</button><button class="pdf-btn danger" onclick="removePdf('${key}')">Remove</button></div></div>` : 
      `<div class="pdf-drop" onclick="triggerNativeUpload('${key}')"><div class="pdf-icon">📂</div><p>Click to <strong>browse</strong> your computer</p><p style="margin-top:6px;font-size:12px;color:var(--accent);">Supports 100MB+ (Saved locally)</p></div>`}
    </div>`;
  const ta=document.getElementById('note-ta'); if(ta) { ta.oninput = () => { S.notes[key] = ta.value; saveToLocal(); render(); }; }
  setTimeout(()=>{if(ta)ta.focus();},50);
}

function setMood(key,m,btn){ S.moods[key]=S.moods[key]===m?null:m; saveToLocal(); document.querySelectorAll('.mood-btn').forEach(b=>b.classList.remove('selected')); if(S.moods[key]) btn.classList.add('selected'); }
function switchTab(t){ S.activeTab=t; document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.textContent.includes(t==='note'?'Note':'Document'))); document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('visible')); const tc=document.getElementById('tc-'+t); if(tc){tc.classList.add('visible');} }

// --- NATIVE OS FILE HANDLING ---
function triggerNativeUpload(key){
  if(window.pywebview) {
    window.pywebview.api.select_pdf(key).then(response => {
      if(response.success) {
        S.pdfs[key] = { name: response.filename, size: response.size, path: response.path };
        saveToLocal();
        render();
        renderPanel();
      }
    });
  }
}

function viewPdf(key){ 
  const pdf=S.pdfs[key]; 
  if(!pdf || !pdf.path) return; 
  if(window.pywebview) window.pywebview.api.view_pdf(pdf.path); 
}

function removePdf(key){ 
  const pdf=S.pdfs[key]; 
  if(pdf && pdf.path && window.pywebview) {
    window.pywebview.api.delete_pdf(pdf.path);
  }
  delete S.pdfs[key]; 
  saveToLocal(); 
  render(); 
  renderPanel(); 
}
// --------------------------------

function closePanel(){ S.active=null; document.getElementById('panel-wrap').style.display='none'; }
function fireConfetti(){ const colors=['#7FA87A','#C4956A','#8ECAE6','#CDB4DB','#FFD166','#EF476F']; for(let i=0;i<80;i++){ setTimeout(()=>{ const c=document.createElement('div'); c.className='confetti-piece'; c.style.left=Math.random()*100+'vw'; c.style.top='-10px'; c.style.background=colors[Math.floor(Math.random()*colors.length)]; c.style.transform=`rotate(${Math.random()*360}deg)`; c.style.animationDuration=(2+Math.random()*1.5)+'s'; c.style.animationDelay=(Math.random()*0.2)+'s'; document.body.appendChild(c); setTimeout(()=>c.remove(),4000); },i*15); } }

const t=new Date(); document.getElementById('date-in').value=t.getFullYear()+'-'+pad(t.getMonth()+1)+'-'+pad(t.getDate());
</script>
</body>
</html>"""

    # Instantiate the API to act as the bridge
    api = TrackerAPI()

    # Create the standalone window, passing the API bridge to the frontend
    window = webview.create_window(
        title='21 Day Challenge Tracker', 
        html=html_content, 
        js_api=api,
        width=800, 
        height=850, 
        min_size=(600, 700)
    )
    
    webview.start()

if __name__ == '__main__':
    launch_tracker()