# -*- coding: utf-8 -*-
import random
import uuid
from collections import Counter

from flask import Flask, request, jsonify, redirect, url_for, render_template_string
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"
socketio = SocketIO(app, cors_allowed_origins="*")

# -----------------------------
# 内嵌页面（Lobby + Room）
# -----------------------------

BASE_CSS = r"""
<style>
body { font-family: Arial, sans-serif; background: #f5f6f7; margin: 0; }
.container { max-width: 1100px; margin: 20px auto; padding: 0 12px; }
h1 { margin: 8px 0 12px; }
h2 { margin: 0 0 10px; }
.card { background: white; border-radius: 10px; padding: 14px; margin: 12px 0; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.row { display: flex; gap: 10px; align-items: center; margin: 10px 0; flex-wrap: wrap; }
label { width: 90px; color: #333; }
input { padding: 8px 10px; border: 1px solid #ccc; border-radius: 8px; min-width: 220px; }
button { padding: 9px 12px; border: 0; border-radius: 8px; cursor: pointer; background: #2d6cdf; color: white; }
button:disabled { opacity: .45; cursor: not-allowed; }
.hint { color: #666; font-size: 13px; }
.tag { display: inline-block; background: #eef2ff; color: #2d6cdf; padding: 2px 8px; border-radius: 999px; margin-left: 6px; font-size: 12px; }
.roomRow { display:flex; justify-content: space-between; align-items:center; padding: 10px 0; border-bottom: 1px dashed #ddd; gap: 10px; }
.playerRow { padding: 6px 0; border-bottom: 1px dashed #eee; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
.hand { display:flex; flex-wrap:wrap; gap:8px; padding: 8px 0; }
.cardItem { user-select:none; padding: 8px 10px; border-radius: 10px; border: 1px solid #ddd; background: #fafafa; cursor:pointer; }
.cardItem.sel { border-color: #2d6cdf; background: #eaf0ff; }
.turn { font-size: 16px; margin-bottom: 8px; }
.lastplay .played { margin-top: 8px; font-size: 18px; letter-spacing: 1px; }
.topbar { display:flex; justify-content: space-between; align-items: center; gap: 10px; }
</style>
"""

INDEX_HTML = r"""
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Lobby</title>
  {{ css|safe }}
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
  <div class="container">
    <h1>多人联机扑克牌（房间大厅）</h1>

    <div class="card">
      <h2>创建房间</h2>
      <div class="row">
        <label>昵称</label>
        <input id="nick" placeholder="例如：Alice"/>
      </div>
      <div class="row">
        <label>房间名</label>
        <input id="rname" placeholder="例如：FunRoom"/>
      </div>
      <div class="row">
        <label>几副牌</label>
        <input id="decks" type="number" min="1" max="8" value="1"/>
      </div>
      <button id="btnCreate">创建</button>
      <p class="hint">创建后在下方列表点“加入”。（≥2人即可开始）</p>
    </div>

    <div class="card">
      <h2>房间列表</h2>
      <button id="btnRefresh">刷新</button>
      <div id="rooms"></div>
    </div>
  </div>

<script>
const socket = io();

function esc(s){return (s||"").replace(/[&<>"']/g,m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[m]));}

async function refreshRooms(){
  const res = await fetch("/api/rooms");
  const rooms = await res.json();
  renderRooms(rooms);
}
function renderRooms(rooms){
  const wrap = document.getElementById("rooms");
  if(!rooms.length){
    wrap.innerHTML = "<p class='hint'>当前没有房间。</p>";
    return;
  }
  wrap.innerHTML = rooms.map(r=>{
    const status = r.started ? "已开始" : "等待中";
    return `
      <div class="roomRow">
        <div>
          <b>${esc(r.name)}</b>
          <span class="tag">${status}</span>
          <span class="tag">${r.players} 人</span>
          <span class="tag">${r.decks} 副</span>
          <span class="tag">id: ${esc(r.id)}</span>
        </div>
        <button onclick="joinRoom('${esc(r.id)}')">加入</button>
      </div>
    `;
  }).join("");
}

window.joinRoom = function(rid){
  const nick = document.getElementById("nick").value.trim();
  if(!nick){ alert("请先输入昵称"); return; }
  location.href = `/room/${rid}?name=${encodeURIComponent(nick)}`;
}

document.getElementById("btnCreate").onclick = ()=>{
  const nickname = document.getElementById("nick").value.trim();
  const room_name = document.getElementById("rname").value.trim() || "Room";
  const decks = parseInt(document.getElementById("decks").value || "1", 10);
  if(!nickname){ alert("请先输入昵称"); return; }
  socket.emit("create_room", {nickname, room_name, decks});
};

document.getElementById("btnRefresh").onclick = refreshRooms;

socket.on("room_created", (d)=>{
  alert("房间已创建: " + d.room_id + "（在列表中加入）");
  refreshRooms();
});
socket.on("rooms_update", (d)=>{
  if(d && d.rooms) renderRooms(d.rooms);
});
socket.on("error_msg", (d)=> alert(d.msg || "Error"));

refreshRooms();
</script>
</body>
</html>
"""

ROOM_HTML = r"""
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Room</title>
  {{ css|safe }}
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
</head>
<body>
  <div class="container">
    <div class="topbar">
      <div>
        <h1>房间：{{ room_id }}</h1>
        <div class="hint">你是：<b id="meName"></b></div>
      </div>
      <div>
        <button onclick="location.href='/'">回大厅</button>
      </div>
    </div>

    <div class="grid2">
      <div class="card">
        <h2>玩家</h2>
        <div id="players"></div>
        <div class="row">
          <button id="btnStart">开始（≥2人）</button>
        </div>
        <div class="hint">只会显示你自己的手牌；其他人只显示剩余张数。</div>
      </div>

      <div class="card">
        <h2>桌面</h2>
        <div id="turnInfo" class="turn"></div>
        <div id="lastPlay" class="lastplay"></div>
      </div>
    </div>

    <div class="card">
      <h2>你的手牌</h2>
      <div id="hand" class="hand"></div>

      <div class="row">
        <button id="btnPlay">出牌</button>
        <button id="btnPass">不要</button>
        <button id="btnClear">清空选择</button>
      </div>
      <div class="hint">点击牌即可选择/取消。</div>
    </div>
  </div>

<script>
const ROOM_ID = "{{ room_id }}";
const NICKNAME = "{{ nickname }}";

const socket = io();
let myHand = [];
let selected = new Set();
let lastState = null;

function esc(s){return (s||"").replace(/[&<>"']/g,m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[m]));}
function sortHand(cards){
  cards.sort((a,b)=> (a.v-b.v) || (a.s>b.s?1:-1));
  return cards;
}

function renderHand(){
  const wrap = document.getElementById("hand");
  if(!myHand.length){
    wrap.innerHTML = "<p class='hint'>还没发牌。人齐后点开始。</p>";
    return;
  }
  wrap.innerHTML = myHand.map(c=>{
    const isSel = selected.has(c.id);
    return `<span class="cardItem ${isSel?'sel':''}" data-id="${esc(c.id)}">${esc(c.text)}</span>`;
  }).join("");

  wrap.querySelectorAll(".cardItem").forEach(el=>{
    el.onclick = ()=>{
      const id = el.getAttribute("data-id");
      if(selected.has(id)) selected.delete(id); else selected.add(id);
      renderHand();
    }
  });
}

function renderPlayers(state){
  document.getElementById("meName").textContent = NICKNAME;

  const wrap = document.getElementById("players");
  wrap.innerHTML = state.players.map(p=>{
    const turn = state.turn_name === p.name ? "（当前回合）" : "";
    return `<div class="playerRow"><b>${esc(p.name)}</b>${esc(turn)} <span class="tag">${p.count} 张</span></div>`;
  }).join("");

  const turnInfo = document.getElementById("turnInfo");
  turnInfo.innerHTML = state.started
    ? `轮到：<b>${esc(state.turn_name||"")}</b>`
    : `<span class="tag">等待中</span>（≥2人可开始）`;

  const lastPlay = document.getElementById("lastPlay");
  if(state.last_play){
    const lp = state.last_play;
    const cardsText = (lp.cards||[]).map(x=>esc(x.text)).join(" ");
    lastPlay.innerHTML = `
      <div>上一手：<b>${esc(lp.by)}</b> <span class="tag">${esc(lp.type)}</span></div>
      <div class="played">${cardsText}</div>
    `;
  }else{
    lastPlay.innerHTML = `<div class="hint">无人出牌（新一轮）。轮到领头者必须出。</div>`;
  }

  const myTurn = (state.turn_sid && socket.id && state.turn_sid === socket.id);
  document.getElementById("btnPlay").disabled = !(state.started && myTurn);
  document.getElementById("btnPass").disabled = !(state.started && myTurn);
  document.getElementById("btnClear").disabled = !(state.started && myHand.length);
  document.getElementById("btnStart").disabled = state.started;
}

document.getElementById("btnStart").onclick = ()=>{
  socket.emit("start_game", {room_id: ROOM_ID});
};
document.getElementById("btnClear").onclick = ()=>{
  selected.clear(); renderHand();
};
document.getElementById("btnPlay").onclick = ()=>{
  const ids = Array.from(selected);
  if(!ids.length){ alert("请先选牌"); return; }
  socket.emit("play_cards", {room_id: ROOM_ID, card_ids: ids});
};
document.getElementById("btnPass").onclick = ()=>{
  socket.emit("pass_turn", {room_id: ROOM_ID});
};

socket.on("connect", ()=>{
  socket.emit("join_game", {room_id: ROOM_ID, nickname: NICKNAME});
});

socket.on("hand", (d)=>{
  myHand = sortHand(d.cards || []);
  const ids = new Set(myHand.map(c=>c.id));
  selected = new Set(Array.from(selected).filter(x=>ids.has(x)));
  renderHand();
});

socket.on("room_state", (state)=>{
  lastState = state;
  renderPlayers(state);
});

socket.on("game_over", (d)=>{
  alert("游戏结束！获胜者：" + (d.winner || ""));
  selected.clear();
});

socket.on("error_msg", (d)=> alert(d.msg || "Error"));
</script>
</body>
</html>
"""

# -----------------------------
# 扑克牌 + 规则判断（斗地主风格压牌）
# -----------------------------

RANK_LABELS = {
    3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
    11: "J", 12: "Q", 13: "K", 14: "A", 15: "2", 16: "SJ", 17: "BJ"
}
SUIT_SYMBOL = {"S": "♠", "H": "♥", "C": "♣", "D": "♦", "J": ""}

def build_deck(num_decks):
    suits = ["S", "H", "C", "D"]
    deck = []
    for di in range(num_decks):
        for s in suits:
            for v in range(3, 16):
                cid = "%s-%s-%s-%s" % (di, s, v, uuid.uuid4().hex[:6])
                deck.append({"id": cid, "v": v, "s": s,
                             "text": "%s%s" % (SUIT_SYMBOL[s], RANK_LABELS[v])})
        # jokers per deck
        for v, s in [(16, "J"), (17, "J")]:
            cid = "%s-J-%s-%s" % (di, v, uuid.uuid4().hex[:6])
            deck.append({"id": cid, "v": v, "s": "J", "text": RANK_LABELS[v]})
    return deck

def is_consecutive(vals):
    if not vals:
        return False
    vals = sorted(vals)
    for i in range(1, len(vals)):
        if vals[i] != vals[i-1] + 1:
            return False
    return True

def analyze_play(cards):
    """
    识别牌型：不合规返回 None
    支持：
    single/pair/triple
    triple_single(3+1) triple_pair(3+2)
    straight(>=5, 不含2/王)
    pair_seq(>=3对, 不含2/王)
    four_two_single(4+1+1) four_two_pair(4+2+2)
    bomb(同点数>=4)  rocket(SJ+BJ)
    airplane / airplane_wing_single / airplane_wing_pair（限制：三张必须恰好为3张且连续）
    """
    n = len(cards)
    if n == 0:
        return None

    vals = [c["v"] for c in cards]
    cnt = Counter(vals)
    items = sorted(cnt.items(), key=lambda x: x[0])

    # rocket
    if n == 2 and set(vals) == set([16, 17]):
        return {"type": "rocket", "main": 17, "size": 2}

    # bomb (>=4 same)
    if len(cnt) == 1 and n >= 4:
        v = items[0][0]
        return {"type": "bomb", "main": v, "size": n}

    if n == 1:
        return {"type": "single", "main": vals[0], "size": 1}
    if n == 2 and len(cnt) == 1:
        v = items[0][0]
        return {"type": "pair", "main": v, "size": 2}
    if n == 3 and len(cnt) == 1:
        v = items[0][0]
        return {"type": "triple", "main": v, "size": 3}

    # 3+1
    if n == 4 and sorted(cnt.values()) == [1, 3]:
        triple_v = [v for v, c in cnt.items() if c == 3][0]
        return {"type": "triple_single", "main": triple_v, "size": 4}

    # 3+2
    if n == 5 and sorted(cnt.values()) == [2, 3]:
        triple_v = [v for v, c in cnt.items() if c == 3][0]
        return {"type": "triple_pair", "main": triple_v, "size": 5}

    # straight
    if n >= 5 and all(c == 1 for c in cnt.values()):
        uniq = sorted(cnt.keys())
        if max(uniq) <= 14 and min(uniq) >= 3 and is_consecutive(uniq):
            return {"type": "straight", "main": max(uniq), "size": n}

    # pair sequence
    if n >= 6 and n % 2 == 0 and all(c == 2 for c in cnt.values()):
        uniq = sorted(cnt.keys())
        if len(uniq) >= 3 and max(uniq) <= 14 and min(uniq) >= 3 and is_consecutive(uniq):
            return {"type": "pair_seq", "main": max(uniq), "size": len(uniq)}

    # four + two singles
    if n == 6 and 4 in cnt.values() and list(cnt.values()).count(4) == 1:
        four_v = [v for v, c in cnt.items() if c == 4][0]
        if all(c == 1 for v, c in cnt.items() if v != four_v):
            return {"type": "four_two_single", "main": four_v, "size": 6}

    # four + two pairs
    if n == 8 and 4 in cnt.values() and list(cnt.values()).count(4) == 1:
        four_v = [v for v, c in cnt.items() if c == 4][0]
        if all(c == 2 for v, c in cnt.items() if v != four_v):
            return {"type": "four_two_pair", "main": four_v, "size": 8}

    # airplane (限制：三张必须恰好为3张，且<=A)
    triple_ranks = sorted([v for v, c in cnt.items() if c == 3 and v <= 14])
    if len(triple_ranks) >= 2 and is_consecutive(triple_ranks):
        k = len(triple_ranks)
        remain = []
        for v, c in cnt.items():
            if v in triple_ranks:
                continue
            remain += [v] * c

        if len(remain) == 0:
            return {"type": "airplane", "main": max(triple_ranks), "size": k}

        if len(remain) == k:
            rc = Counter(remain)
            if all(c == 1 for c in rc.values()):
                return {"type": "airplane_wing_single", "main": max(triple_ranks), "size": k}

        if len(remain) == 2 * k:
            rc = Counter(remain)
            if all(c == 2 for c in rc.values()) and len(rc) == k:
                return {"type": "airplane_wing_pair", "main": max(triple_ranks), "size": k}

    return None

def beats(play, last_play):
    """判断 play 是否能压过 last_play（last_play=None 表示新一轮领头可随便出）"""
    if play is None:
        return False
    if last_play is None:
        return True

    if play["type"] == "rocket":
        return True
    if last_play["type"] == "rocket":
        return False

    if play["type"] == "bomb":
        if last_play["type"] != "bomb":
            return True
        # 多副牌：先比炸弹张数，再比点数
        if play["size"] != last_play["size"]:
            return play["size"] > last_play["size"]
        return play["main"] > last_play["main"]

    if last_play["type"] == "bomb":
        return False

    if play["type"] != last_play["type"]:
        return False

    # 这些牌型必须结构/长度一致
    if play["type"] == "straight":
        if play["size"] != last_play["size"]:
            return False
    if play["type"] == "pair_seq":
        if play["size"] != last_play["size"]:
            return False
    if play["type"] in ("airplane", "airplane_wing_single", "airplane_wing_pair"):
        if play["size"] != last_play["size"]:
            return False

    return play["main"] > last_play["main"]

# -----------------------------
# 房间状态（内存版）
# -----------------------------
rooms = {}  # rid -> room dict

def public_rooms_list():
    out = []
    for rid, r in rooms.items():
        out.append({
            "id": rid,
            "name": r["name"],
            "players": len(r["players"]),
            "started": r["started"],
            "decks": r["decks"]
        })
    out.sort(key=lambda x: x["name"])
    return out

def get_player(room, sid):
    for p in room["players"]:
        if p["sid"] == sid:
            return p
    return None

def next_turn_index(room, from_index=None):
    if not room["players"]:
        return 0
    if from_index is None:
        from_index = room["turn_index"]
    return (from_index + 1) % len(room["players"])

def broadcast_state(rid):
    room = rooms.get(rid)
    if not room:
        return
    turn_sid = None
    turn_name = None
    if room["players"]:
        turn_sid = room["players"][room["turn_index"]]["sid"]
        turn_name = room["players"][room["turn_index"]]["name"]

    state = {
        "room_id": rid,
        "room_name": room["name"],
        "started": room["started"],
        "decks": room["decks"],
        "players": [{"name": p["name"], "count": len(p["hand"])} for p in room["players"]],
        "turn_sid": turn_sid,
        "turn_name": turn_name,
        "last_play": room["last_play_public"],  # 只广播公共信息
    }
    socketio.emit("room_state", state, room=rid)

def deal_cards(room):
    deck = build_deck(room["decks"])
    random.shuffle(deck)

    players = room["players"]
    for p in players:
        p["hand"] = []

    # 轮流发完
    for i, card in enumerate(deck):
        players[i % len(players)]["hand"].append(card)

    for p in players:
        p["hand"].sort(key=lambda c: (c["v"], c["s"]))

    # 起手：最小牌者先（简单规则）
    best_i, best_v = 0, 999
    for i, p in enumerate(players):
        mv = min([c["v"] for c in p["hand"]]) if p["hand"] else 999
        if mv < best_v:
            best_v = mv
            best_i = i

    room["turn_index"] = best_i
    room["leader_index"] = best_i
    room["pass_count"] = 0
    room["last_play"] = None
    room["last_play_public"] = None

    # 只把“自己的手牌”发给自己
    for p in players:
        socketio.emit("hand", {"cards": p["hand"]}, room=p["sid"])

# -----------------------------
# HTTP Routes（内嵌页面）
# -----------------------------
@app.route("/")
def index():
    return render_template_string(INDEX_HTML, css=BASE_CSS)

@app.route("/api/rooms")
def api_rooms():
    return jsonify(public_rooms_list())

@app.route("/room/<rid>")
def room_page(rid):
    name = (request.args.get("name") or "").strip()
    if not name:
        return redirect(url_for("index"))
    if rid not in rooms:
        return redirect(url_for("index"))
    return render_template_string(ROOM_HTML, css=BASE_CSS, room_id=rid, nickname=name)

# -----------------------------
# Socket Events
# -----------------------------
@socketio.on("create_room")
def on_create_room(data):
    nickname = (data.get("nickname") or "").strip()
    room_name = (data.get("room_name") or "Room").strip()
    decks = int(data.get("decks") or 1)
    decks = max(1, min(decks, 8))

    if not nickname:
        emit("error_msg", {"msg": "请先输入昵称"})
        return

    rid = uuid.uuid4().hex[:8]
    rooms[rid] = {
        "name": room_name,
        "decks": decks,
        "started": False,
        "players": [],
        "turn_index": 0,
        "leader_index": 0,
        "pass_count": 0,
        "last_play": None,
        "last_play_public": None,
    }
    emit("room_created", {"room_id": rid})
    socketio.emit("rooms_update", {"rooms": public_rooms_list()})

@socketio.on("join_game")
def on_join_game(data):
    rid = data.get("room_id")
    nickname = (data.get("nickname") or "").strip()
    if not rid or rid not in rooms:
        emit("error_msg", {"msg": "房间不存在"})
        return
    if not nickname:
        emit("error_msg", {"msg": "昵称必填"})
        return

    room = rooms[rid]
    if room["started"]:
        emit("error_msg", {"msg": "游戏已开始（此简化版不支持观战）"})
        return

    existing_names = set([p["name"] for p in room["players"]])
    if nickname in existing_names:
        nickname = nickname + "_" + uuid.uuid4().hex[:3]

    room["players"].append({"sid": request.sid, "name": nickname, "hand": []})
    join_room(rid)

    emit("joined_ok", {"room_id": rid, "nickname": nickname})
    socketio.emit("rooms_update", {"rooms": public_rooms_list()})
    broadcast_state(rid)

@socketio.on("start_game")
def on_start_game(data):
    rid = data.get("room_id")
    if not rid or rid not in rooms:
        emit("error_msg", {"msg": "房间不存在"})
        return
    room = rooms[rid]
    if room["started"]:
        return
    if len(room["players"]) < 2:
        emit("error_msg", {"msg": "至少2人才能开始"})
        return

    room["started"] = True
    deal_cards(room)
    broadcast_state(rid)

@socketio.on("play_cards")
def on_play_cards(data):
    rid = data.get("room_id")
    card_ids = data.get("card_ids") or []
    if not rid or rid not in rooms:
        emit("error_msg", {"msg": "房间不存在"})
        return
    room = rooms[rid]
    if not room["started"]:
        emit("error_msg", {"msg": "还没开始"})
        return
    if not room["players"]:
        return

    turn_player = room["players"][room["turn_index"]]
    if turn_player["sid"] != request.sid:
        emit("error_msg", {"msg": "还没轮到你"})
        return

    player = get_player(room, request.sid)
    if not player:
        emit("error_msg", {"msg": "你不在房间里"})
        return
    if not card_ids:
        emit("error_msg", {"msg": "请先选牌"})
        return

    # 必须是自己手里的牌（禁止亮牌/偷牌）
    hand_by_id = {c["id"]: c for c in player["hand"]}
    chosen = []
    for cid in card_ids:
        if cid not in hand_by_id:
            emit("error_msg", {"msg": "选牌无效（不在你手里）"})
            return
        chosen.append(hand_by_id[cid])

    play = analyze_play(chosen)
    if play is None:
        emit("error_msg", {"msg": "牌型不合规"})
        return
    if not beats(play, room["last_play"]):
        emit("error_msg", {"msg": "压不住上一手"})
        return

    # 出牌生效：从手里移除
    chosen_set = set(card_ids)
    player["hand"] = [c for c in player["hand"] if c["id"] not in chosen_set]

    room["last_play"] = play
    room["last_play_public"] = {
        "by": player["name"],
        "type": play["type"],
        "cards": [{"text": c["text"], "v": c["v"]} for c in chosen],
    }
    room["pass_count"] = 0
    room["leader_index"] = room["turn_index"]

    # 胜利判定
    if len(player["hand"]) == 0:
        socketio.emit("game_over", {"winner": player["name"]}, room=rid)
        room["started"] = False
        room["last_play"] = None
        room["last_play_public"] = None
        room["pass_count"] = 0
        broadcast_state(rid)
        socketio.emit("rooms_update", {"rooms": public_rooms_list()})
        return

    # 轮到下家
    room["turn_index"] = next_turn_index(room)

    # 更新自己手牌（只发给自己）
    socketio.emit("hand", {"cards": player["hand"]}, room=player["sid"])
    broadcast_state(rid)

@socketio.on("pass_turn")
def on_pass_turn(data):
    rid = data.get("room_id")
    if not rid or rid not in rooms:
        emit("error_msg", {"msg": "房间不存在"})
        return
    room = rooms[rid]
    if not room["started"]:
        emit("error_msg", {"msg": "还没开始"})
        return
    if not room["players"]:
        return

    turn_player = room["players"][room["turn_index"]]
    if turn_player["sid"] != request.sid:
        emit("error_msg", {"msg": "还没轮到你"})
        return

    # 领头不能不要
    if room["last_play"] is None:
        emit("error_msg", {"msg": "你是领头，本轮必须出牌"})
        return

    room["pass_count"] += 1
    room["turn_index"] = next_turn_index(room)

    # 若除领头外全都不要 -> 清空上一手，领头继续带牌
    if room["pass_count"] >= max(0, len(room["players"]) - 1):
        room["last_play"] = None
        room["last_play_public"] = None
        room["pass_count"] = 0
        room["turn_index"] = room["leader_index"]

    broadcast_state(rid)

@socketio.on("disconnect")
def on_disconnect():
    to_delete = []
    for rid, room in rooms.items():
        before = len(room["players"])
        room["players"] = [p for p in room["players"] if p["sid"] != request.sid]
        after = len(room["players"])
        if after != before:
            if room["started"]:
                # 简化处理：有人掉线直接结束本局
                room["started"] = False
                room["last_play"] = None
                room["last_play_public"] = None
                room["pass_count"] = 0
            if after == 0:
                to_delete.append(rid)
            else:
                room["turn_index"] = min(room["turn_index"], after - 1)
                room["leader_index"] = min(room["leader_index"], after - 1)
                broadcast_state(rid)

    for rid in to_delete:
        rooms.pop(rid, None)
    socketio.emit("rooms_update", {"rooms": public_rooms_list()})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
