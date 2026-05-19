#!/usr/bin/env python3
"""
Serveur Web — Caisse & Gestion de Stock
Accessible sur tout le réseau local via le navigateur.
"""
from flask import Flask, jsonify, request, render_template_string
import json, os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.expanduser("~"), "Documents", "caisse_data.json")

# ─── Données ──────────────────────────────────────────────────────────────────
def _load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {"articles": [], "factures": [], "equipes": 0, "next_id": 1}

def _save(d):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ─── API Articles ──────────────────────────────────────────────────────────────
@app.route('/api/articles', methods=['GET'])
def get_articles(): return jsonify(_load()['articles'])

@app.route('/api/articles', methods=['POST'])
def add_article():
    d = _load(); b = request.json
    nom = (b.get('nom') or '').strip()
    if not nom: return jsonify({'error': 'Nom requis'}), 400
    if any(a['nom'].lower() == nom.lower() for a in d['articles']):
        return jsonify({'error': 'Article déjà existant'}), 409
    try: pa = float(b['prix_achat']); pv = float(b['prix_vente']); st = int(b['stock'])
    except: return jsonify({'error': 'Données invalides'}), 400
    a = {'id': d['next_id'], 'nom': nom, 'prix_achat': pa, 'prix_vente': pv,
         'stock': st, 'stock_initial': st}
    d['articles'].append(a); d['next_id'] += 1; _save(d)
    return jsonify(a), 201

@app.route('/api/articles/<int:aid>', methods=['PUT'])
def update_article(aid):
    d = _load(); b = request.json
    for a in d['articles']:
        if a['id'] == aid:
            if 'nom' in b: a['nom'] = b['nom'].strip()
            if 'prix_achat' in b: a['prix_achat'] = float(b['prix_achat'])
            if 'prix_vente' in b: a['prix_vente'] = float(b['prix_vente'])
            if 'stock' in b: a['stock'] = int(b['stock'])
            _save(d); return jsonify(a)
    return jsonify({'error': 'Introuvable'}), 404

@app.route('/api/articles/<int:aid>', methods=['DELETE'])
def delete_article(aid):
    d = _load(); d['articles'] = [a for a in d['articles'] if a['id'] != aid]
    _save(d); return jsonify({'ok': True})

# ─── API Factures ──────────────────────────────────────────────────────────────
@app.route('/api/factures', methods=['GET'])
def get_factures(): return jsonify(_load()['factures'])

@app.route('/api/factures', methods=['POST'])
def add_facture():
    d = _load(); b = request.json
    for item in b.get('items', []):
        if not item.get('libre'):
            for a in d['articles']:
                if a['id'] == item.get('article_id'):
                    a['stock'] = max(0, a['stock'] - item['qte']); break
    num = (max(f['numero'] for f in d['factures']) + 1) if d['factures'] else 1
    fac = {'numero': num,
           'heure': b.get('heure') or datetime.now().strftime('%H:%M'),
           'date': datetime.now().strftime('%Y-%m-%d'),
           'items': b.get('items', []),
           'total': float(b.get('total', 0))}
    d['factures'].append(fac); _save(d); return jsonify(fac), 201

# ─── API Équipes (global, saisie une seule fois) ───────────────────────────────
@app.route('/api/equipes', methods=['GET', 'PUT'])
def equipes():
    d = _load()
    if request.method == 'PUT':
        d['equipes'] = max(0, int(request.json.get('equipes', 0))); _save(d)
    return jsonify({'equipes': d.get('equipes', 0)})

# ─── API Bilan ─────────────────────────────────────────────────────────────────
@app.route('/api/bilan', methods=['GET'])
def bilan():
    d = _load()
    arts, facs, eq = d['articles'], d['factures'], d.get('equipes', 0)
    total_ventes = sum(f['total'] for f in facs)
    eq_rev = eq * 5; total_recup = total_ventes + eq_rev
    total_investi = sum(a['prix_achat'] * a.get('stock_initial', a['stock']) for a in arts)
    vpa = {}; rev_pa = {}
    for fac in facs:
        for item in fac['items']:
            if not item.get('libre'):
                n = item.get('nom','')
                vpa[n]    = vpa.get(n, 0)    + item['qte']
                rev_pa[n] = rev_pa.get(n, 0) + item['total']
    by_hour = {}
    for fac in facs:
        h = (fac.get('heure') or '--')[:5]
        by_hour[h] = by_hour.get(h, 0) + fac['total']
    by_date = {}
    for fac in facs:
        dt = fac.get('date','?')
        by_date[dt] = by_date.get(dt, 0) + fac['total']
    return jsonify({
        'total_ventes': total_ventes, 'eq_rev': eq_rev, 'equipes': eq,
        'total_recup': total_recup, 'total_investi': total_investi,
        'benefice': total_recup - total_investi, 'nb_commandes': len(facs),
        'articles': [{'nom': a['nom'], 'stock_initial': a.get('stock_initial', a['stock']),
                      'stock': a['stock'], 'vendus': vpa.get(a['nom'], 0),
                      'revenue': rev_pa.get(a['nom'], 0)} for a in arts],
        'by_hour': [{'h': k, 'v': v} for k, v in sorted(by_hour.items())],
        'by_date': [{'d': k, 'v': v} for k, v in sorted(by_date.items())]
    })

# ─── Frontend ──────────────────────────────────────────────────────────────────
@app.route('/')
def index(): return render_template_string(PAGE)

# ══════════════════════════════════════════════════════════════════════════════
PAGE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>⬛ CaisseApp</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Azeret+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080B12;--s1:#0E1320;--s2:#141926;--s3:#1C2235;--s4:#232A3E;
  --amber:#F5A623;--amber2:#FFB830;--amber3:rgba(245,166,35,.12);
  --green:#18C27D;--green2:rgba(24,194,125,.12);
  --red:#E84545;--red2:rgba(232,69,69,.12);
  --blue:#3E8BFF;--blue2:rgba(62,139,255,.12);
  --purple:#9B6DFF;
  --text:#EBF0FC;--text2:#7A86A1;--text3:#3E4A63;
  --border:#1F2840;--border2:#2A3450;
  --font:'Syne',sans-serif;--mono:'Azeret Mono',monospace;
  --r:10px;--r2:14px;
}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:var(--font)}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

/* ── Layout ── */
#app{display:flex;flex-direction:column;height:100vh}

/* ── Topbar ── */
.topbar{
  height:54px;background:var(--s1);
  border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 18px;gap:6px;flex-shrink:0;
  position:relative;z-index:100;
}
.logo{font-size:1.15rem;font-weight:800;letter-spacing:-0.5px;color:var(--amber);margin-right:14px;white-space:nowrap}
.logo span{color:var(--text2);font-weight:400}
.tab-btn{
  padding:7px 16px;border-radius:8px;border:none;cursor:pointer;
  font-weight:700;font-size:.82rem;font-family:var(--font);
  color:var(--text2);background:transparent;letter-spacing:.3px;
  transition:all .2s;white-space:nowrap;
}
.tab-btn:hover{background:var(--s3);color:var(--text)}
.tab-btn.active{background:var(--amber);color:#000}
.topbar-right{margin-left:auto;font-family:var(--mono);font-size:.72rem;color:var(--text3);text-align:right;line-height:1.4}

/* ── Pages ── */
.pages{flex:1;overflow:hidden;position:relative}
.page{position:absolute;inset:0;overflow-y:auto;padding:20px;display:none}
.page.active{display:block}
#pg-caisse{padding:0;overflow:hidden}

/* ── Toast ── */
#toasts{position:fixed;top:62px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:6px;pointer-events:none}
.toast{
  padding:11px 18px;border-radius:10px;font-size:.84rem;font-weight:700;
  animation:slideIn .22s ease;box-shadow:0 6px 24px rgba(0,0,0,.5);pointer-events:all;
  font-family:var(--font);letter-spacing:.2px;
}
.toast-success{background:var(--green);color:#fff}
.toast-error  {background:var(--red);color:#fff}
.toast-info   {background:var(--blue);color:#fff}
@keyframes slideIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:none}}

/* ── Generic ── */
.card{background:var(--s2);border:1px solid var(--border);border-radius:var(--r2)}
.card2{background:var(--s1);border:1px solid var(--border);border-radius:var(--r)}
.section-lbl{font-size:.68rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text3);margin-bottom:8px}
.btn{padding:9px 16px;border-radius:var(--r);border:none;cursor:pointer;font-weight:700;font-size:.82rem;font-family:var(--font);transition:all .18s;letter-spacing:.3px}
.btn-amber{background:var(--amber);color:#000}
.btn-amber:hover{background:var(--amber2)}
.btn-green{background:var(--green);color:#fff}
.btn-green:hover{filter:brightness(1.1)}
.btn-red{background:var(--red);color:#fff}
.btn-red:hover{filter:brightness(1.1)}
.btn-ghost{background:var(--s3);color:var(--text);border:1px solid var(--border2)}
.btn-ghost:hover{background:var(--s4)}
.btn-sm{padding:5px 11px;font-size:.75rem}
.btn-xs{padding:3px 8px;font-size:.72rem;border-radius:6px}
.form-label{font-size:.72rem;font-weight:700;color:var(--text2);letter-spacing:.5px;text-transform:uppercase;display:block;margin-bottom:5px}
.form-input{
  background:var(--s3);border:1px solid var(--border2);border-radius:var(--r);
  padding:9px 12px;color:var(--text);font-family:var(--font);font-size:.88rem;
  outline:none;transition:border-color .18s;width:100%;
}
.form-input:focus{border-color:var(--amber);box-shadow:0 0 0 2px var(--amber3)}
.form-input::placeholder{color:var(--text3)}
.mono{font-family:var(--mono)}
.text-amber{color:var(--amber)}
.text-green{color:var(--green)}
.text-red{color:var(--red)}
.text-sub{color:var(--text2)}
.text-xs{font-size:.78rem}
.flex{display:flex}.aic{align-items:center}.jcb{justify-content:space-between}
.gap4{gap:4px}.gap8{gap:8px}.gap12{gap:12px}.gap16{gap:16px}
.ml-auto{margin-left:auto}
.bold{font-weight:700}

/* ══════════════════════════════
   CAISSE PAGE
══════════════════════════════ */
.caisse-grid{display:grid;grid-template-columns:1fr 370px;height:calc(100vh - 54px)}

/* Left panel */
.caisse-left{overflow-y:auto;padding:18px 16px;display:flex;flex-direction:column;gap:14px;background:var(--bg)}

/* Équipes banner */
.eq-banner{
  background:linear-gradient(135deg, var(--s2) 0%, var(--s3) 100%);
  border:1px solid var(--amber);border-radius:var(--r2);
  padding:14px 18px;display:flex;align-items:center;gap:14px;
  box-shadow:0 0 20px rgba(245,166,35,.08);
}
.eq-icon{font-size:1.5rem;flex-shrink:0}
.eq-info{flex:1;min-width:0}
.eq-title{font-size:.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text3);margin-bottom:2px}
.eq-val{font-size:1rem;font-weight:700}
.eq-val .num{color:var(--amber);font-family:var(--mono);font-size:1.15rem}
.eq-controls{display:flex;align-items:center;gap:6px;flex-shrink:0}
.eq-stepper{
  display:flex;align-items:center;background:var(--s1);border:1px solid var(--border2);
  border-radius:var(--r);overflow:hidden;
}
.eq-step-btn{
  width:34px;height:34px;border:none;background:transparent;color:var(--text2);
  font-size:1.1rem;cursor:pointer;transition:all .15s;font-weight:700;
}
.eq-step-btn:hover{background:var(--amber);color:#000}
.eq-num-input{
  width:52px;text-align:center;background:transparent;border:none;
  color:var(--text);font-family:var(--mono);font-size:1rem;font-weight:700;
  outline:none;padding:0 4px;
}
.eq-save-btn{padding:7px 12px;border-radius:8px;border:1px solid var(--amber);background:transparent;color:var(--amber);font-size:.78rem;font-weight:700;cursor:pointer;font-family:var(--font);transition:all .18s;white-space:nowrap}
.eq-save-btn:hover{background:var(--amber);color:#000}

/* Search */
.search-wrap{position:relative}
.search-input-big{
  width:100%;background:var(--s2);border:2px solid var(--border);
  border-radius:var(--r2);padding:14px 18px 14px 46px;
  font-size:1.05rem;color:var(--text);font-family:var(--font);
  outline:none;transition:all .2s;
}
.search-input-big:focus{border-color:var(--amber);box-shadow:0 0 0 3px var(--amber3);background:var(--s1)}
.search-input-big::placeholder{color:var(--text3)}
.search-icon{position:absolute;left:15px;top:50%;transform:translateY(-50%);font-size:1rem;color:var(--text3);pointer-events:none}

/* Autocomplete */
.ac-drop{
  position:absolute;top:calc(100% + 4px);left:0;right:0;
  background:var(--s1);border:1px solid var(--amber);
  border-radius:var(--r2);z-index:200;overflow:hidden;
  box-shadow:0 12px 40px rgba(0,0,0,.6);
}
.ac-item{
  padding:11px 16px;cursor:pointer;display:flex;justify-content:space-between;
  align-items:center;gap:12px;border-bottom:1px solid var(--border);
  transition:background .12s;
}
.ac-item:last-child{border-bottom:none}
.ac-item:hover,.ac-item.sel{background:var(--s3)}
.ac-item-name{font-weight:700;font-size:.9rem}
.ac-item-stock{font-size:.74rem;margin-top:2px}
.ac-item-price{font-family:var(--mono);font-weight:700;color:var(--amber);font-size:1rem;flex-shrink:0}

/* Staging area */
.staging-card{
  background:var(--s2);border:2px solid var(--amber);border-radius:var(--r2);
  padding:16px;display:flex;align-items:center;gap:14px;
  box-shadow:0 0 24px rgba(245,166,35,.1);
  animation:fadeUp .18s ease;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.stg-info{flex:1;min-width:0}
.stg-name{font-size:1.05rem;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stg-meta{font-size:.78rem;color:var(--text2);margin-top:3px}
.stg-price{font-family:var(--mono);font-size:1.5rem;font-weight:700;color:var(--amber);flex-shrink:0}
.qty-ctrl{display:flex;align-items:center;background:var(--s1);border:1px solid var(--border2);border-radius:var(--r);overflow:hidden;flex-shrink:0}
.qty-btn{width:32px;height:36px;border:none;background:transparent;color:var(--text2);font-size:1rem;cursor:pointer;font-weight:700;transition:all .12s;font-family:var(--mono)}
.qty-btn:hover{background:var(--amber);color:#000}
.qty-val{width:48px;text-align:center;background:transparent;border:none;color:var(--text);font-family:var(--mono);font-size:.95rem;font-weight:700;outline:none;padding:4px}

/* Libre */
.libre-grid{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:10px;align-items:end}

/* Footer bar caisse */
.caisse-footer{display:flex;align-items:center;gap:14px;padding:10px 0 2px;margin-top:auto}
.time-block .time-val{font-family:var(--mono);font-size:1.1rem;font-weight:700;color:var(--amber);line-height:1}
.facture-block .fac-val{font-family:var(--mono);font-size:.95rem;font-weight:700;color:var(--blue)}

/* ── Receipt panel (right) ── */
.receipt-panel{
  background:var(--s1);border-left:1px solid var(--border);
  display:flex;flex-direction:column;overflow:hidden;
}
.receipt-header{
  padding:14px 18px 12px;border-bottom:1px solid var(--border);flex-shrink:0;
}
.receipt-header-top{display:flex;align-items:baseline;gap:10px;margin-bottom:2px}
.receipt-lbl{font-size:.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text3)}
.receipt-num{font-family:var(--mono);font-size:1.3rem;font-weight:700;color:var(--blue)}
.receipt-body{flex:1;overflow-y:auto;padding:8px 16px}
.empty-receipt{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:var(--text3);text-align:center;gap:8px;
}
.empty-receipt .emp-icon{font-size:2.5rem;opacity:.4}
.empty-receipt p{font-size:.82rem}

/* Receipt items */
.r-item{
  display:flex;align-items:center;gap:8px;
  padding:10px 0;border-bottom:1px dashed var(--border);
  animation:fadeUp .15s ease;
}
.r-item:last-child{border-bottom:none}
.r-nom{flex:1;font-size:.88rem;font-weight:600;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.r-qty-badge{background:var(--s3);color:var(--text2);font-family:var(--mono);font-size:.72rem;font-weight:700;padding:2px 6px;border-radius:4px;flex-shrink:0}
.r-price{font-family:var(--mono);font-weight:700;font-size:.9rem;color:var(--amber);min-width:62px;text-align:right;flex-shrink:0}
.r-del{background:none;border:none;color:var(--text3);cursor:pointer;font-size:.85rem;padding:3px 5px;border-radius:4px;transition:color .12s;flex-shrink:0}
.r-del:hover{color:var(--red)}
.r-libre-tag{font-size:.62rem;color:var(--purple);font-weight:700;letter-spacing:.5px;background:rgba(155,109,255,.1);padding:1px 5px;border-radius:3px}

/* Separator */
.receipt-sep{border:none;border-top:2px dashed var(--border);margin:0 16px;flex-shrink:0}

/* Total display */
.total-panel{
  padding:14px 18px 10px;flex-shrink:0;
  background:var(--s2);
}
.total-lbl{font-size:.62rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--text3);margin-bottom:4px}
.total-amount{
  font-family:var(--mono);font-size:2.8rem;font-weight:700;
  color:var(--amber);line-height:1;
  text-shadow:0 0 40px rgba(245,166,35,.35);
  letter-spacing:-1px;
}
.total-items-count{font-size:.72rem;color:var(--text3);margin-top:3px;font-family:var(--mono)}

/* Validate btn */
.btn-validate{
  width:100%;border:none;cursor:pointer;font-family:var(--font);
  padding:18px;font-size:1.05rem;font-weight:800;letter-spacing:1px;
  background:linear-gradient(135deg,#18C27D,#12A268);color:#fff;
  transition:filter .18s;flex-shrink:0;
  position:relative;overflow:hidden;
}
.btn-validate::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(255,255,255,.12),transparent);
}
.btn-validate:hover{filter:brightness(1.08)}
.btn-validate:active{filter:brightness(.92)}
.btn-cancel-sale{
  width:100%;border:none;cursor:pointer;font-family:var(--font);
  padding:10px;font-size:.8rem;font-weight:600;letter-spacing:.5px;
  background:var(--s3);color:var(--text2);flex-shrink:0;
  transition:background .15s;
}
.btn-cancel-sale:hover{background:var(--s4);color:var(--red)}

/* ══════════════════════════════
   STOCK PAGE
══════════════════════════════ */
.stock-form-card{padding:20px;margin-bottom:18px}
.stock-form-grid{display:grid;grid-template-columns:2.5fr 1fr 1fr 1fr auto;gap:12px;align-items:end}
.stock-table-card{}
.stock-table-header{padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px}
.tbl{width:100%;border-collapse:collapse}
.tbl th{
  padding:9px 14px;text-align:left;font-size:.68rem;font-weight:700;
  letter-spacing:1.5px;text-transform:uppercase;color:var(--text3);
  background:var(--s3);border-bottom:1px solid var(--border);
}
.tbl td{padding:11px 14px;border-bottom:1px solid var(--border);font-size:.87rem}
.tbl tbody tr:hover td{background:var(--s3)}
.badge{display:inline-flex;align-items:center;gap:3px;padding:3px 9px;border-radius:20px;font-size:.73rem;font-weight:700;letter-spacing:.3px}
.badge-ok  {background:var(--green2);color:var(--green)}
.badge-low {background:rgba(245,166,35,.15);color:var(--amber)}
.badge-zero{background:var(--red2);color:var(--red)}
.badge-info{background:var(--blue2);color:var(--blue)}
.edit-mode-badge{background:rgba(245,166,35,.18);color:var(--amber);font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:6px;letter-spacing:.3px}

/* ══════════════════════════════
   BILAN PAGE
══════════════════════════════ */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}
.kpi-card{padding:18px 20px}
.kpi-lbl{font-size:.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text3);margin-bottom:8px}
.kpi-val{font-family:var(--mono);font-size:1.75rem;font-weight:700;line-height:1}
.kpi-sub{font-size:.74rem;color:var(--text2);margin-top:4px;font-family:var(--mono)}
.eq-bilan-bar{
  padding:14px 20px;margin-bottom:18px;
  display:flex;align-items:center;gap:16px;
  background:linear-gradient(135deg,var(--s2),var(--s3));
  border:1px solid rgba(245,166,35,.25);
}
.charts-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.chart-card{padding:18px}
.chart-title{font-size:.72rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--text3);margin-bottom:14px}
.chart-card.wide{grid-column:span 2}
.chart-card canvas{max-height:190px}
.chart-card.wide canvas{max-height:220px}
.bilan-refresh-btn{margin-left:auto}

/* Number input arrows hide */
input[type=number]::-webkit-outer-spin-button,
input[type=number]::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
input[type=number]{-moz-appearance:textfield}
</style>
</head>
<body>
<div id="app">
<div id="toasts"></div>

<!-- ── Topbar ── -->
<div class="topbar">
  <div class="logo">⬛<span>Caisse</span>App</div>
  <button class="tab-btn active"  onclick="showPage('caisse',this)">🧾 Caisse</button>
  <button class="tab-btn"        onclick="showPage('stock',this)">📦 Stock</button>
  <button class="tab-btn"        onclick="showPage('bilan',this)">📊 Bilan</button>
  <div class="topbar-right" id="srv-info">chargement...</div>
</div>

<!-- ── Pages ── -->
<div class="pages">

<!-- ======== CAISSE ======== -->
<div class="page active" id="pg-caisse">
<div class="caisse-grid">

  <!-- Left -->
  <div class="caisse-left">

    <!-- Équipes -->
    <div>
      <div class="section-lbl">Équipes inscrites</div>
      <div class="eq-banner">
        <div class="eq-icon">⚽</div>
        <div class="eq-info">
          <div class="eq-title">Participation — 5 € / équipe</div>
          <div class="eq-val">
            <span class="num" id="eq-disp">0</span>
            <span class="text-sub" style="font-size:.85rem"> équipe(s) = </span>
            <span class="num" id="eq-total-disp">0.00 €</span>
          </div>
        </div>
        <div class="eq-controls">
          <div class="eq-stepper">
            <button class="eq-step-btn" onclick="stepEq(-1)">−</button>
            <input class="eq-num-input" id="eq-input" type="number" value="0" min="0" onchange="setEq(+this.value)">
            <button class="eq-step-btn" onclick="stepEq(1)">+</button>
          </div>
          <button class="eq-save-btn" onclick="saveEq()">Enregistrer</button>
        </div>
      </div>
    </div>

    <!-- Search -->
    <div>
      <div class="section-lbl">Rechercher un article</div>
      <div class="search-wrap">
        <span class="search-icon">🔍</span>
        <input class="search-input-big" id="search" type="text"
          placeholder="Commencez à taper le nom d'un article…"
          autocomplete="off" oninput="onSearch(this.value)" onkeydown="onSearchKey(event)">
        <div class="ac-drop" id="ac-drop" style="display:none"></div>
      </div>
    </div>

    <!-- Staging -->
    <div id="staging" style="display:none">
      <div class="section-lbl">Article sélectionné</div>
      <div class="staging-card">
        <div class="stg-info">
          <div class="stg-name" id="stg-name">—</div>
          <div class="stg-meta" id="stg-meta">—</div>
        </div>
        <div class="stg-price" id="stg-price">0.00 €</div>
        <div class="qty-ctrl">
          <button class="qty-btn" onclick="stepQty(-1)">−</button>
          <input class="qty-val" id="qty-input" type="number" value="1" min="1" onkeydown="onQtyKey(event)">
          <button class="qty-btn" onclick="stepQty(1)">+</button>
        </div>
        <button class="btn btn-amber" onclick="addToCart()" style="white-space:nowrap">➕ Panier</button>
        <button class="btn btn-ghost btn-sm" onclick="clearStaging()" title="Annuler">✕</button>
      </div>
    </div>

    <!-- Libre -->
    <div>
      <div class="section-lbl">Article à prix libre</div>
      <div class="card2" style="padding:14px">
        <div class="libre-grid">
          <div>
            <label class="form-label">Désignation</label>
            <input class="form-input" id="lib-nom" placeholder="Ex : Boisson spéciale">
          </div>
          <div>
            <label class="form-label">Prix (€)</label>
            <input class="form-input" id="lib-px" type="number" step="0.01" min="0" placeholder="0.00">
          </div>
          <div>
            <label class="form-label">Quantité</label>
            <input class="form-input" id="lib-qty" type="number" min="1" value="1">
          </div>
          <button class="btn btn-green" onclick="addLibre()" style="height:40px;align-self:end">➕</button>
        </div>
      </div>
    </div>

    <!-- Footer bar -->
    <div class="caisse-footer">
      <div class="time-block">
        <div class="section-lbl" style="margin-bottom:2px">Heure de vente</div>
        <div class="time-val" id="time-disp">—</div>
      </div>
      <button class="btn btn-ghost btn-sm" onclick="stampTime()">⏰ Horodater</button>
      <div class="ml-auto flex aic gap8">
        <div style="text-align:right">
          <div class="section-lbl" style="margin-bottom:2px">N° Facture</div>
          <div class="mono bold text-sub" id="fac-num-disp" style="font-size:.95rem">#1</div>
        </div>
      </div>
    </div>

  </div><!-- /caisse-left -->

  <!-- Receipt panel -->
  <div class="receipt-panel">
    <div class="receipt-header">
      <div class="receipt-header-top">
        <div class="receipt-lbl">Ticket</div>
        <div class="receipt-num" id="receipt-num">#1</div>
      </div>
      <div style="display:flex;align-items:center;gap:6px;margin-top:4px">
        <div style="font-size:.72rem;color:var(--text3)" id="receipt-time">—</div>
        <button class="btn btn-ghost btn-xs ml-auto" onclick="cancelSale()" style="color:var(--red);border-color:var(--red)">✕ Annuler</button>
      </div>
    </div>

    <div class="receipt-body" id="receipt-body">
      <div class="empty-receipt" id="empty-receipt">
        <div class="emp-icon">🧾</div>
        <p>Aucun article</p>
        <p style="font-size:.74rem;margin-top:2px">Utilisez la recherche pour ajouter des produits</p>
      </div>
    </div>

    <hr class="receipt-sep">

    <div class="total-panel">
      <div class="total-lbl">Total à payer</div>
      <div class="total-amount" id="total-disp">0.00 €</div>
      <div class="total-items-count" id="total-items">0 article(s)</div>
    </div>

    <button class="btn-validate" onclick="validateSale()">✅&nbsp;&nbsp;VALIDER LA VENTE</button>
    <button class="btn-cancel-sale" onclick="cancelSale()">Annuler et vider le panier</button>
  </div>

</div><!-- /caisse-grid -->
</div><!-- /pg-caisse -->

<!-- ======== STOCK ======== -->
<div class="page" id="pg-stock">

  <div class="card stock-form-card" style="margin-bottom:18px">
    <div class="flex aic gap8" style="margin-bottom:14px">
      <div style="font-size:1.1rem;font-weight:800">📦 Catalogue articles</div>
      <div id="form-mode-badge" class="badge badge-ok">Nouvel article</div>
      <button class="btn btn-ghost btn-sm ml-auto" onclick="resetForm()" id="btn-cancel-edit" style="display:none">✕ Annuler modification</button>
    </div>
    <div class="stock-form-grid">
      <div>
        <label class="form-label">Nom de l'article *</label>
        <input class="form-input" id="s-nom" placeholder="Ex : Coca-Cola 33cl">
      </div>
      <div>
        <label class="form-label">Prix d'achat €</label>
        <input class="form-input" id="s-pa" type="number" step="0.01" min="0" placeholder="0.00">
      </div>
      <div>
        <label class="form-label">Prix de vente €</label>
        <input class="form-input" id="s-pv" type="number" step="0.01" min="0" placeholder="0.00">
      </div>
      <div>
        <label class="form-label">Stock initial</label>
        <input class="form-input" id="s-qty" type="number" min="0" placeholder="0">
      </div>
      <div style="display:flex;gap:8px;align-items:flex-end">
        <button class="btn btn-amber" onclick="submitForm()" style="height:40px;padding:0 18px">Valider</button>
      </div>
    </div>
  </div>

  <div class="card stock-table-card">
    <div class="stock-table-header">
      <span style="font-weight:800">Articles en stock</span>
      <span class="badge badge-info" id="stock-count-badge">0</span>
      <button class="btn btn-ghost btn-sm ml-auto" onclick="loadArticles(false)">🔄 Rafraîchir</button>
    </div>
    <div style="overflow-x:auto">
      <table class="tbl">
        <thead><tr>
          <th>Article</th>
          <th>Prix achat</th>
          <th>Prix vente</th>
          <th>Stock</th>
          <th>Valeur stock</th>
          <th>Marge</th>
          <th>Actions</th>
        </tr></thead>
        <tbody id="stock-tbody"></tbody>
      </table>
    </div>
  </div>

</div><!-- /pg-stock -->

<!-- ======== BILAN ======== -->
<div class="page" id="pg-bilan">

  <div class="kpi-row">
    <div class="card kpi-card">
      <div class="kpi-lbl">💰 Argent récupéré</div>
      <div class="kpi-val text-amber" id="kpi-recup">—</div>
      <div class="kpi-sub" id="kpi-recup-sub"></div>
    </div>
    <div class="card kpi-card">
      <div class="kpi-lbl">💸 Argent investi</div>
      <div class="kpi-val text-red" id="kpi-investi">—</div>
    </div>
    <div class="card kpi-card">
      <div class="kpi-lbl">📈 Bénéfice net</div>
      <div class="kpi-val" id="kpi-benefice">—</div>
    </div>
    <div class="card kpi-card">
      <div class="kpi-lbl">🧾 Commandes</div>
      <div class="kpi-val text-blue" id="kpi-cmds">—</div>
    </div>
  </div>

  <div class="card eq-bilan-bar">
    <span style="font-size:1.4rem">⚽</span>
    <div>
      <div style="font-size:.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text3);margin-bottom:3px">Équipes inscrites</div>
      <div class="flex aic gap8">
        <span class="mono bold text-amber" id="b-eq-cnt">0</span>
        <span class="text-sub text-xs">équipe(s) × 5 €</span>
        <span class="mono bold text-amber">=</span>
        <span class="mono bold text-amber" id="b-eq-rev">0.00 €</span>
      </div>
    </div>
    <button class="btn btn-ghost btn-sm ml-auto bilan-refresh-btn" onclick="loadBilan()">🔄 Actualiser</button>
  </div>

  <div class="charts-grid">
    <div class="card chart-card">
      <div class="chart-title">Quantités vendues vs restantes</div>
      <canvas id="c-pie-qty"></canvas>
    </div>
    <div class="card chart-card">
      <div class="chart-title">Argent : investi / ventes / équipes</div>
      <canvas id="c-pie-money"></canvas>
    </div>
    <div class="card chart-card">
      <div class="chart-title">Stock par article</div>
      <canvas id="c-bar-stock"></canvas>
    </div>
    <div class="card chart-card wide">
      <div class="chart-title">Chiffre d'affaires par article</div>
      <canvas id="c-bar-ca"></canvas>
    </div>
    <div class="card chart-card">
      <div class="chart-title">Ventes par heure</div>
      <canvas id="c-line-hour"></canvas>
    </div>
  </div>

</div><!-- /pg-bilan -->

</div><!-- /pages -->
</div><!-- /app -->

<script>
// ──────────────────────────────────────────────────────────────
//  STATE
// ──────────────────────────────────────────────────────────────
const S = {
  articles: [],
  cart: [],        // [{nom, prix_unit, qte, total, libre, article_id?}]
  selected: null,
  equipes: 0,
  saleTime: null,
  editingId: null,
  charts: {}
};

// ──────────────────────────────────────────────────────────────
//  INIT
// ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Show server IP hint
  document.getElementById('srv-info').innerHTML =
    'Réseau : <strong>' + location.host + '</strong><br>Partagez cette adresse';

  await loadArticles(false);
  await loadEq();
  await refreshInvoiceNum();
});

// ──────────────────────────────────────────────────────────────
//  NAV
// ──────────────────────────────────────────────────────────────
function showPage(name, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
  document.getElementById('pg-' + name).classList.add('active');
  if (btn) btn.classList.add('active');
  if (name === 'bilan') loadBilan();
  if (name === 'stock') renderStockTable();
}

// ──────────────────────────────────────────────────────────────
//  API helpers
// ──────────────────────────────────────────────────────────────
const api = {
  get:    url     => fetch(url).then(r => r.json()),
  post:   (u, b)  => fetch(u, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}).then(r=>r.json()),
  put:    (u, b)  => fetch(u, {method:'PUT',  headers:{'Content-Type':'application/json'}, body:JSON.stringify(b)}).then(r=>r.json()),
  delete: url     => fetch(url, {method:'DELETE'}).then(r=>r.json())
};

// ──────────────────────────────────────────────────────────────
//  TOAST
// ──────────────────────────────────────────────────────────────
function toast(msg, type='info') {
  const el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.textContent = msg;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => el.style.transition = 'opacity .3s', 2700);
  setTimeout(() => el.remove(), 3100);
}

// ──────────────────────────────────────────────────────────────
//  ÉQUIPES
// ──────────────────────────────────────────────────────────────
async function loadEq() {
  const res = await api.get('/api/equipes');
  S.equipes = res.equipes;
  document.getElementById('eq-input').value = S.equipes;
  renderEq();
}
function stepEq(d) {
  const v = Math.max(0, S.equipes + d);
  S.equipes = v;
  document.getElementById('eq-input').value = v;
  renderEq();
}
function setEq(v) {
  S.equipes = Math.max(0, parseInt(v)||0);
  renderEq();
}
function renderEq() {
  const total = S.equipes * 5;
  document.getElementById('eq-disp').textContent = S.equipes;
  document.getElementById('eq-total-disp').textContent = total.toFixed(2) + ' €';
}
async function saveEq() {
  await api.put('/api/equipes', {equipes: S.equipes});
  toast('✓ ' + S.equipes + ' équipe(s) enregistrée(s)', 'success');
}

// ──────────────────────────────────────────────────────────────
//  ARTICLES / STOCK
// ──────────────────────────────────────────────────────────────
async function loadArticles(silent=true) {
  S.articles = await api.get('/api/articles');
  renderStockTable();
  if (!silent) document.getElementById('stock-count-badge').textContent = S.articles.length;
}

function renderStockTable() {
  const tbody = document.getElementById('stock-tbody');
  document.getElementById('stock-count-badge').textContent = S.articles.length;
  if (!S.articles.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text3)">Aucun article — ajoutez votre premier produit ci-dessus</td></tr>`;
    return;
  }
  tbody.innerHTML = S.articles.map(a => {
    const val  = a.prix_achat * a.stock;
    const mg   = a.prix_achat > 0 ? ((a.prix_vente - a.prix_achat)/a.prix_achat*100) : 0;
    const bc   = a.stock === 0 ? 'badge-zero' : a.stock <= 5 ? 'badge-low' : 'badge-ok';
    const stxt = a.stock === 0 ? '⚠ RUPTURE' : a.stock <= 5 ? `⚠ ${a.stock}` : a.stock;
    return `<tr>
      <td><strong>${esc(a.nom)}</strong></td>
      <td class="mono text-sub">${a.prix_achat.toFixed(2)} €</td>
      <td class="mono text-amber bold">${a.prix_vente.toFixed(2)} €</td>
      <td><span class="badge ${bc}">${stxt}</span></td>
      <td class="mono">${val.toFixed(2)} €</td>
      <td class="mono text-sub">${mg.toFixed(1)} %</td>
      <td><div class="flex gap4">
        <button class="btn btn-ghost btn-xs" onclick="editArticle(${a.id})">✏️</button>
        <button class="btn btn-xs" style="background:var(--red2);color:var(--red)" onclick="deleteArticle(${a.id})">🗑️</button>
      </div></td>
    </tr>`;
  }).join('');
}

async function submitForm() {
  const nom = document.getElementById('s-nom').value.trim();
  const pa  = parseFloat(document.getElementById('s-pa').value)||0;
  const pv  = parseFloat(document.getElementById('s-pv').value)||0;
  const qty = parseInt(document.getElementById('s-qty').value)||0;
  if (!nom) { toast('Le nom est requis', 'error'); return; }
  if (S.editingId !== null) {
    const res = await api.put('/api/articles/' + S.editingId, {nom, prix_achat:pa, prix_vente:pv, stock:qty});
    if (res.error) { toast(res.error, 'error'); return; }
    toast(`✓ "${nom}" modifié`, 'success');
  } else {
    const res = await api.post('/api/articles', {nom, prix_achat:pa, prix_vente:pv, stock:qty});
    if (res.error) { toast(res.error, 'error'); return; }
    toast(`✓ "${nom}" ajouté`, 'success');
  }
  await loadArticles(false);
  resetForm();
}

function editArticle(id) {
  const a = S.articles.find(x => x.id === id); if (!a) return;
  S.editingId = id;
  document.getElementById('s-nom').value = a.nom;
  document.getElementById('s-pa').value  = a.prix_achat;
  document.getElementById('s-pv').value  = a.prix_vente;
  document.getElementById('s-qty').value = a.stock;
  document.getElementById('form-mode-badge').textContent = 'Modification';
  document.getElementById('form-mode-badge').className   = 'badge badge-low edit-mode-badge';
  document.getElementById('btn-cancel-edit').style.display = '';
  showPage('stock', document.querySelectorAll('.tab-btn')[1]);
  document.getElementById('s-nom').focus();
}

async function deleteArticle(id) {
  const a = S.articles.find(x => x.id === id);
  if (!confirm(`Supprimer "${a?.nom}" définitivement ?`)) return;
  await api.delete('/api/articles/' + id);
  toast('Article supprimé', 'info');
  await loadArticles(false);
}

function resetForm() {
  S.editingId = null;
  ['s-nom','s-pa','s-pv','s-qty'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('form-mode-badge').textContent = 'Nouvel article';
  document.getElementById('form-mode-badge').className   = 'badge badge-ok';
  document.getElementById('btn-cancel-edit').style.display = 'none';
}

// ──────────────────────────────────────────────────────────────
//  AUTOCOMPLETE
// ──────────────────────────────────────────────────────────────
let _debounce = null;
function onSearch(q) {
  const dd = document.getElementById('ac-drop');
  clearTimeout(_debounce);
  if (!q.trim()) { dd.style.display='none'; return; }
  _debounce = setTimeout(() => {
    const matches = S.articles.filter(a => a.nom.toLowerCase().includes(q.toLowerCase()));
    if (!matches.length) { dd.style.display='none'; return; }
    dd.innerHTML = matches.map(a => {
      const inCart = S.cart.filter(i=>!i.libre && i.article_id===a.id).reduce((s,i)=>s+i.qte,0);
      const avail  = a.stock - inCart;
      const sc = avail <= 0 ? 'text-red' : avail <= 5 ? 'text-amber' : 'text-sub';
      const st = avail <= 0 ? '⚠ Rupture' : `Stock : ${avail}`;
      return `<div class="ac-item" onclick="selectArticle(${a.id})">
        <div><div class="ac-item-name">${esc(a.nom)}</div>
        <div class="ac-item-stock ${sc} text-xs">${st}</div></div>
        <div class="ac-item-price">${a.prix_vente.toFixed(2)} €</div>
      </div>`;
    }).join('');
    dd.style.display = 'block';
  }, 70);
}

function onSearchKey(e) {
  const dd = document.getElementById('ac-drop');
  const items = dd.querySelectorAll('.ac-item');
  let cur = dd.querySelector('.ac-item.sel');
  if (e.key==='ArrowDown') {
    e.preventDefault();
    if (!cur) items[0]?.classList.add('sel');
    else { cur.classList.remove('sel'); (cur.nextElementSibling||items[0])?.classList.add('sel'); }
  } else if (e.key==='ArrowUp') {
    e.preventDefault();
    if (!cur) items[items.length-1]?.classList.add('sel');
    else { cur.classList.remove('sel'); (cur.previousElementSibling||items[items.length-1])?.classList.add('sel'); }
  } else if (e.key==='Enter') {
    e.preventDefault();
    const sel = dd.querySelector('.ac-item.sel');
    if (sel) { const id = parseInt(sel.getAttribute('onclick').match(/\d+/)[0]); selectArticle(id); }
  } else if (e.key==='Escape') { dd.style.display='none'; }
}

function selectArticle(id) {
  const a = S.articles.find(x => x.id === id); if (!a) return;
  S.selected = a;
  document.getElementById('ac-drop').style.display = 'none';
  document.getElementById('search').value = '';
  const inCart = S.cart.filter(i=>!i.libre&&i.article_id===a.id).reduce((s,i)=>s+i.qte,0);
  const avail  = a.stock - inCart;
  document.getElementById('stg-name').textContent  = a.nom;
  document.getElementById('stg-price').textContent = a.prix_vente.toFixed(2) + ' €';
  document.getElementById('stg-meta').textContent  =
    avail <= 0 ? '⚠ Rupture de stock !' : `Disponible : ${avail} unité(s)`;
  document.getElementById('stg-meta').style.color = avail<=0 ? 'var(--red)' : avail<=5 ? 'var(--amber)' : 'var(--text2)';
  const qi = document.getElementById('qty-input');
  qi.value = 1; qi.max = Math.max(1, avail);
  document.getElementById('staging').style.display = '';
  qi.focus(); qi.select();
}

function clearStaging() {
  S.selected = null;
  document.getElementById('staging').style.display = 'none';
  document.getElementById('search').value = '';
  document.getElementById('search').focus();
}

function stepQty(d) {
  const qi = document.getElementById('qty-input');
  qi.value = Math.max(1, (parseInt(qi.value)||1) + d);
}

function onQtyKey(e) {
  if (e.key === 'Enter') { e.preventDefault(); addToCart(); }
  if (e.key === 'Escape') clearStaging();
}

// ──────────────────────────────────────────────────────────────
//  CART
// ──────────────────────────────────────────────────────────────
function addToCart() {
  const a = S.selected; if (!a) return;
  const qty = Math.max(1, parseInt(document.getElementById('qty-input').value)||1);
  const inCart = S.cart.filter(i=>!i.libre&&i.article_id===a.id).reduce((s,i)=>s+i.qte,0);
  if (inCart + qty > a.stock) {
    toast(`Stock insuffisant (dispo : ${a.stock - inCart})`, 'error'); return;
  }
  const exist = S.cart.find(i=>!i.libre&&i.article_id===a.id);
  if (exist) {
    exist.qte += qty; exist.total = exist.prix_unit * exist.qte;
  } else {
    S.cart.push({nom:a.nom, prix_unit:a.prix_vente, qte:qty,
                  total:a.prix_vente*qty, libre:false, article_id:a.id});
  }
  renderReceipt(); updateTotal(); clearStaging();
  toast(`✓ ${a.nom} × ${qty}`, 'success');
}

function addLibre() {
  const nom  = document.getElementById('lib-nom').value.trim();
  const prix = parseFloat(document.getElementById('lib-px').value)||0;
  const qty  = parseInt(document.getElementById('lib-qty').value)||1;
  if (!nom) { toast('Désignation requise', 'error'); return; }
  S.cart.push({nom, prix_unit:prix, qte:qty, total:prix*qty, libre:true});
  renderReceipt(); updateTotal();
  document.getElementById('lib-nom').value='';
  document.getElementById('lib-px').value='';
  document.getElementById('lib-qty').value=1;
  toast(`✓ ${nom} (prix libre)`, 'success');
}

function removeFromCart(i) {
  S.cart.splice(i,1); renderReceipt(); updateTotal();
}

function renderReceipt() {
  const body = document.getElementById('receipt-body');
  if (!S.cart.length) {
    body.innerHTML = `<div class="empty-receipt"><div class="emp-icon">🧾</div><p>Aucun article</p><p style="font-size:.74rem;margin-top:2px">Utilisez la recherche pour ajouter des produits</p></div>`;
    return;
  }
  body.innerHTML = S.cart.map((item,i) => `
    <div class="r-item">
      <div class="r-nom">
        ${esc(item.nom)}
        ${item.libre ? '<span class="r-libre-tag">LIBRE</span>' : ''}
      </div>
      ${item.qte > 1 ? `<div class="r-qty-badge">×${item.qte}</div>` : ''}
      <div class="r-price">${item.total.toFixed(2)} €</div>
      <button class="r-del" onclick="removeFromCart(${i})" title="Retirer">✕</button>
    </div>`).join('');
}

function updateTotal() {
  const tot = S.cart.reduce((s,i)=>s+i.total,0);
  document.getElementById('total-disp').textContent  = tot.toFixed(2) + ' €';
  document.getElementById('total-items').textContent = S.cart.length + ' article(s)';
  document.getElementById('receipt-time').textContent = S.saleTime || '—';
}

function stampTime() {
  S.saleTime = new Date().toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
  document.getElementById('time-disp').textContent = S.saleTime;
  document.getElementById('receipt-time').textContent = S.saleTime;
  toast('⏰ ' + S.saleTime, 'info');
}

async function refreshInvoiceNum() {
  const facs = await api.get('/api/factures');
  const num = facs.length ? Math.max(...facs.map(f=>f.numero)) + 1 : 1;
  document.getElementById('fac-num-disp').textContent = '#' + num;
  document.getElementById('receipt-num').textContent  = '#' + num;
}

async function validateSale() {
  if (!S.cart.length) { toast('Le panier est vide', 'error'); return; }
  const total = S.cart.reduce((s,i)=>s+i.total,0);
  const lines = S.cart.map(i=>` • ${i.nom} ×${i.qte} = ${i.total.toFixed(2)}€`).join('\n');
  if (!confirm(`Confirmer la vente ?\n\n${lines}\n\nTOTAL : ${total.toFixed(2)} €`)) return;
  if (!S.saleTime) stampTime();
  const res = await api.post('/api/factures', {heure:S.saleTime, items:S.cart, total});
  if (res.error) { toast(res.error, 'error'); return; }
  toast(`✅ Facture #${res.numero} — ${total.toFixed(2)} €`, 'success');
  await loadArticles(true);
  cancelSale();
}

function cancelSale() {
  S.cart=[]; S.saleTime=null; S.selected=null;
  document.getElementById('time-disp').textContent='—';
  document.getElementById('search').value='';
  document.getElementById('staging').style.display='none';
  document.getElementById('ac-drop').style.display='none';
  renderReceipt(); updateTotal(); refreshInvoiceNum();
}

// ──────────────────────────────────────────────────────────────
//  BILAN
// ──────────────────────────────────────────────────────────────
async function loadBilan() {
  const b = await api.get('/api/bilan');
  document.getElementById('kpi-recup').textContent    = b.total_recup.toFixed(2) + ' €';
  document.getElementById('kpi-recup-sub').textContent= `dont équipes : ${b.eq_rev.toFixed(2)} €`;
  document.getElementById('kpi-investi').textContent  = b.total_investi.toFixed(2) + ' €';
  const bel = document.getElementById('kpi-benefice');
  bel.textContent = (b.benefice>=0?'+':'')+b.benefice.toFixed(2)+' €';
  bel.className   = 'kpi-val ' + (b.benefice>=0?'text-green':'text-red');
  document.getElementById('kpi-cmds').textContent     = b.nb_commandes;
  document.getElementById('b-eq-cnt').textContent     = b.equipes;
  document.getElementById('b-eq-rev').textContent     = b.eq_rev.toFixed(2)+' €';

  const arts = b.articles;
  const noms = arts.map(a=>a.nom);
  const tv   = arts.reduce((s,a)=>s+a.vendus,0);
  const tr   = arts.reduce((s,a)=>s+a.stock,0);
  const CO   = ['#18C27D','#F5A623','#3E8BFF','#E84545','#9B6DFF','#FFB830','#00C8FF','#FF6B6B'];

  mkChart('c-pie-qty','doughnut',{
    labels:['Vendus','Restants'],
    datasets:[{data:[tv,tr],backgroundColor:['#18C27D','#F5A623'],borderWidth:0,hoverOffset:4}]
  });

  mkChart('c-pie-money','doughnut',{
    labels:['Investi','Ventes produits','Équipes'],
    datasets:[{data:[b.total_investi,b.total_ventes,b.eq_rev],backgroundColor:['#E84545','#18C27D','#F5A623'],borderWidth:0,hoverOffset:4}]
  });

  mkChart('c-bar-stock','bar',{
    labels:noms,
    datasets:[
      {label:'Vendus',  data:arts.map(a=>a.vendus),  backgroundColor:'#18C27D',borderRadius:4},
      {label:'Restants',data:arts.map(a=>a.stock),   backgroundColor:'#F5A623',borderRadius:4}
    ]
  },{scales:{x:{ticks:{color:'#7A86A1'},grid:{color:'#1F2840'}},y:{ticks:{color:'#7A86A1'},grid:{color:'#1F2840'}}}});

  mkChart('c-bar-ca','bar',{
    labels:noms,
    datasets:[{label:'CA (€)',data:arts.map(a=>a.revenue),
      backgroundColor:noms.map((_,i)=>CO[i%CO.length]),borderRadius:5}]
  },{indexAxis:'y',plugins:{legend:{display:false}},
     scales:{x:{ticks:{color:'#7A86A1'},grid:{color:'#1F2840'}},y:{ticks:{color:'#7A86A1'},grid:{color:'#1F2840'}}}});

  const hours = b.by_hour;
  mkChart('c-line-hour','line',{
    labels:hours.map(h=>h.h),
    datasets:[{label:'Ventes (€)',data:hours.map(h=>h.v),
      borderColor:'#F5A623',backgroundColor:'rgba(245,166,35,.1)',
      fill:true,tension:.4,pointBackgroundColor:'#F5A623',pointRadius:4}]
  },{plugins:{legend:{display:false}},
     scales:{x:{ticks:{color:'#7A86A1'},grid:{color:'#1F2840'}},y:{ticks:{color:'#7A86A1'},grid:{color:'#1F2840'}}}});
}

function mkChart(id, type, data, extra={}) {
  if (S.charts[id]) { S.charts[id].destroy(); delete S.charts[id]; }
  const ctx = document.getElementById(id)?.getContext('2d');
  if (!ctx) return;
  const opts = deepMerge({
    responsive:true, maintainAspectRatio:true,
    animation:{duration:500},
    plugins:{legend:{labels:{color:'#7A86A1',padding:12,font:{size:11,family:'Syne'}}}}
  }, extra);
  S.charts[id] = new Chart(ctx, {type, data, options:opts});
}

function deepMerge(t, s) {
  const o = {...t};
  for (const k in s) {
    if (s[k] && typeof s[k]==='object' && !Array.isArray(s[k])) o[k]=deepMerge(t[k]||{},s[k]);
    else o[k]=s[k];
  }
  return o;
}

// ──────────────────────────────────────────────────────────────
//  UTILS
// ──────────────────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Close autocomplete on outside click
document.addEventListener('click', e => {
  if (!e.target.closest('.search-wrap')) document.getElementById('ac-drop').style.display='none';
});
</script>
</body>
</html>
"""

# ─── Lancement ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import socket
    try: ip = socket.gethostbyname(socket.gethostname())
    except: ip = 'IP introuvable'
    print('\n' + '='*55)
    print('  ⬛  CaisseApp — Serveur démarré !')
    print('='*55)
    print(f'  ➜  Votre PC    : http://localhost:5000')
    print(f'  ➜  Réseau local: http://{ip}:5000')
    print('\n  Partagez l\'adresse réseau avec vos collègues.')
    print('  Ctrl+C pour arrêter le serveur.')
    print('='*55 + '\n')
    app.run(host='0.0.0.0', port=5000, debug=False)
