import webview

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>USB</title>
<style>

/* ===== LOSS OVERRIDES (STRONGER THAN THEMES) ===== */
td.open.exploded,
td.theme-neon.open.exploded,
td.theme-retro.open.exploded,
td.theme-plastic.open.exploded { background: linear-gradient(145deg,#ff4d4d,#b30000) !important; border: 2px solid #ff0000 !important; box-shadow: 0 0 14px rgba(255,0,0,0.9) !important;}
/* Wrong flags */
td.wrong-flag,
td.theme-neon.wrong-flag,
td.theme-retro.wrong-flag,
td.theme-plastic.wrong-flag { background: linear-gradient(145deg,#ff4d4d,#c70000) !important; border: 2px solid #900 !important; box-shadow: inset 0 0 8px rgba(0,0,0,0.7) !important;}
/* ----------------- LIGHT MODE ----------------- */
body.light { background:#f0f0f0; color:black; }
body.light #panel, body.light #session-stats { background:#dcdcdc; border:2px solid #999; }
body.light .counter { background:white; color:red; border:2px inset #ccc; }
body.light #smiley { border:2px outset #ccc; }
body.light #board { background:#e0e0e0; border:4px solid #999; box-shadow:0 0 15px rgba(0,0,0,0.2); }
body.light td { background: linear-gradient(145deg,#fff,#d0d0d0); border-top:2px solid #fff; border-left:2px solid #fff; border-bottom:2px solid #aaa; border-right:2px solid #aaa; box-shadow: inset 1px 1px 2px #ccc, inset -1px -1px 2px #aaa; }
body.light td.open { background: linear-gradient(145deg,#d0d0d0,#b0b0b0); border:1px solid #999; box-shadow: inset 0 0 0 #000; }

/* ----------------- DARK MODE ----------------- */
body.dark { background:#303030; color:white; }
body.dark #panel, body.dark #session-stats { background:#404040; border:2px solid #808080; }
body.dark .counter { background:black; color:red; border:2px inset #fff; }
body.dark #smiley { border:2px outset #fff; }
body.dark #board { background:#505050; border:4px solid #808080; box-shadow:0 0 15px rgba(0,0,0,0.5); }
body.dark td { background: linear-gradient(145deg,#6b6b6b,#404040); border-top:2px solid #808080; border-left:2px solid #808080; border-bottom:2px solid #303030; border-right:2px solid #303030; box-shadow: inset 1px 1px 2px #707070, inset -1px -1px 2px #303030; }
body.dark td.open { background: linear-gradient(145deg,#404040,#2a2a2a); border:1px solid #202020; box-shadow: inset 0 0 0 #000; }

/* ----------------- COMMON STYLES ----------------- */
body { font-family:Tahoma,Verdana,sans-serif; display:flex; justify-content:center; margin-top:40px; transition: background 0.3s,color 0.3s; }
#game { display:flex; gap:20px; }
#board-container { display:flex; flex-direction:column; align-items:center; max-width:100%; max-height:90vh; overflow:auto; }
#panel { display:flex; justify-content:space-between; padding:4px 10px; width: fit-content; margin-bottom:6px; }
.counter { font-family:"Courier New", monospace; font-size:20px; padding:2px 6px; min-width:50px; text-align:center; }
#smiley { font-size:28px; cursor:pointer; padding:2px 6px; }
#board { table-layout:fixed; width:max-content; height:max-content; border-collapse:collapse; border-radius:8px; }
td { width:24px; height:24px; text-align:center; font-weight:bold; font-size:16px; cursor:pointer; user-select:none; vertical-align:middle; transition: background 0.2s, transform 0.1s; }
td.open { transform: translateY(1px); cursor: default; }
td.n1 { color:#00bfff; } td.n2 { color:#00ff00; } td.n3 { color:#ff4040; } td.n4 { color:#0000ff; }
td.n5 { color:#ff8000; } td.n6 { color:#00ffff; } td.n7 { color:white; } td.n8 { color:gray; }
#status { margin-top:6px; font-weight:bold; text-align:center; }
.win { color:lightgreen; } .lose { color:red; }
#side { display:flex; flex-direction:column; gap:10px; }
#side h3 { margin:0 0 4px 0; } select { font-size:14px; }
#session-stats { padding:6px; font-size:14px; width:180px; }
#mode-toggle { margin-top:10px; padding:4px 10px; cursor:pointer; font-size:14px; border-radius:4px; border:none; }
#custom-settings input { width:60px; margin-left:4px; }
td.wrong-flag { background: linear-gradient(145deg,#ff4d4d,#c70000)!important; transition: background 0.3s; }
    td.exploded { background: linear-gradient(145deg,#ff4d4d,#b30000) !important; border: 2px solid #ff0000 !important; box-shadow: 0 0 12px rgba(255,0,0,0.9) !important;}
td.wrong-flag { background: linear-gradient(145deg,#ff4d4d,#c70000) !important; box-shadow: inset 0 0 6px rgba(0,0,0,0.6) !important;}

/* ----- Open Cell Themes ----- */
td.theme-classic.open { background: linear-gradient(145deg,#d0d0d0,#b0b0b0); border:1px solid #999; box-shadow: inset 0 0 0 #000; color: inherit; }
/*Neon Theme*/
td.theme-neon,
body.dark td.theme-neon,
body.light td.theme-neon { background: #0a0015 !important; border: 1px solid #00f8ff !important; box-shadow: 0 0 7px #00f8ff, inset 0 0 4px #00f8ff !important; color: #00ffe9 !important;}
td.theme-neon.open,
body.dark td.theme-neon.open,
body.light td.theme-neon.open { background: #140028 !important; border: 1px solid #ff00d4 !important; box-shadow: inset 0 0 9px #ff00d4 !important;}
td.theme-neon.open { background: #140028 !important; border: 1px solid #ff00d4 !important; box-shadow: inset 0 0 9px #ff00d4 !important; color: #00ffe9 !important; }
/* Retro */
td.theme-retro,
body.dark td.theme-retro,
body.light td.theme-retro { background: #d5cba9 !important; border: 3px outset #8f7f5f !important; font-family: "Courier New", Courier, monospace !important; color: #35280e !important;}
td.theme-retro.open,
body.dark td.theme-retro.open,
body.light td.theme-retro.open { background: #b9ad89 !important; border: 1px solid #6b5a3f !important;}
td.theme-retro.open { background: #b9ad89 !important; border: 1px solid #6b5a3f !important; color: #35280e !important; font-family: "Courier New", Courier, monospace !important; }
/* Plastic */
td.theme-plastic,
body.dark td.theme-plastic,
body.light td.theme-plastic { background: linear-gradient(135deg, #e8f8ff, #bbe9ff) !important; border: 2px outset #4da8ff !important; box-shadow: inset 1px 1px 4px rgba(255,255,255,0.7), 0 1px 3px rgba(0,0,0,0.2) !important;}
td.theme-plastic.open,
body.dark td.theme-plastic.open,
body.light td.theme-plastic.open { background: linear-gradient(135deg, #bbe9ff, #87d4ff) !important; border: 1px solid #0280c7 !important; box-shadow: inset 0 1px 4px rgba(0,0,0,0.2) !important;}
td.theme-plastic.open { background: linear-gradient(135deg, #bbe9ff, #87d4ff) !important; border: 1px solid #0280c7 !important; box-shadow: inset 0 1px 4px rgba(0,0,0,0.2) !important; color: #004466 !important; }

/* ===== LOSS STATE OVERRIDES ===== */
/* Exploded bomb */
body.lost td.exploded { background: linear-gradient(145deg,#ff4d4d,#b30000) !important; border: 2px solid #ff0000 !important; box-shadow: 0 0 16px rgba(255,0,0,0.9) !important;}
/* Wrong flag */
body.lost td.wrong-flag { background: linear-gradient(145deg,#ff4d4d,#c70000) !important; border: 2px solid #900 !important; box-shadow: inset 0 0 8px rgba(0,0,0,0.7) !important;}
/* ===== EXPLODED BOMB (MAX PRIORITY) ===== */
body.dark td.open.exploded,
body.light td.open.exploded,
body.dark td.theme-neon.open.exploded,
body.light td.theme-neon.open.exploded,
body.dark td.theme-retro.open.exploded,
body.light td.theme-retro.open.exploded,
body.dark td.theme-plastic.open.exploded,
body.light td.theme-plastic.open.exploded { background: linear-gradient(145deg,#ff4d4d,#b30000) !important; border: 2px solid #ff0000 !important; box-shadow: 0 0 16px rgba(255,0,0,0.9) !important;}
/* ----- GAME RESULT BORDERS ----- */
#board.win-border {border: 4px solid #00ff66 !important;box-shadow: 0 0 18px rgba(0,255,102,0.6);}
#board.lose-border {border: 4px solid #ff3333 !important;box-shadow: 0 0 18px rgba(255,51,51,0.6);}
</style>
</head>
<body class="dark">
<div id="game">

<div id="board-container">
    <div id="panel">
        <div id="bombs" class="counter">000</div>
        <div id="smiley">🙂</div>
        <div id="timer" class="counter">00:00:00</div>
    </div>
    <table id="board"></table>
    <div id="status"></div>
</div>

<div id="side">
    <div>
        <h3>⚙ Difficulty</h3>
        <select id="difficulty">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="expert">Expert</option>
            <option value="custom">Custom</option>
        </select>
        <div id="custom-settings" style="display:none; margin-top:6px;">
            <label>Rows: <input type="number" id="custom-rows" value="2" min="2" max="100"></label><br>
            <label>Columns: <input type="number" id="custom-cols" value="2" min="2" max="100"></label><br>
            <label>Mines: <input type="number" id="custom-mines" value="1" min="1"></label>
        </div>
    </div>
    <div id="session-stats">
        <h3>Session Stats</h3>
        <div>Games Played: <span id="games-played">0</span></div>
        <div>Wins: <span id="wins">0</span></div>
        <div>Losses: <span id="losses">0</span></div>
        <div>Best Time: <span id="best-time">---</span></div>
    </div>
    <button id="mode-toggle">Toggle Light/Dark Mode</button>
    <!-- Settings panel (collapsed by default) -->
    <div id="settings-panel" style="display:none; margin-top:12px; padding:10px; border-radius:6px; background:rgba(100,100,100,0.25);">
        <h4 style="margin:0 0 10px 0;">Appearance</h4>
        <div style="margin-bottom:10px;">
            <label>Background: </label><br>
            <input type="color" id="bg-color" value="#1e1e2e" style="width:100%; height:32px; padding:2px;">
        </div>
        <div>
            <label>Tile style: </label><br>
            <select id="tile-theme" style="width:100%;">
                <option value="classic">Classic</option>
                <option value="neon">Neon</option>
                <option value="retro">Retro</option>
                <option value="plastic">Plastic</option>
            </select>
        </div>
    </div>
    <button id="settings-btn" style="margin-top:10px; width:100%; padding:8px;">⚙ Settings</button>
</div>

<script>
// ---------- GAME LOGIC ----------
const boardElem = document.getElementById("board");
const bombsDiv = document.getElementById("bombs");
const timerDiv = document.getElementById("timer");
const smiley = document.getElementById("smiley");
const statusDiv = document.getElementById("status");
const difficulty = document.getElementById("difficulty");
const toggleBtn = document.getElementById("mode-toggle");
const settingsBtn = document.getElementById("settings-btn");
const settingsPanel = document.getElementById("settings-panel");
const bgColorInput = document.getElementById("bg-color");
const themeSelect = document.getElementById("tile-theme");
const stats = {
    beginner:     { wins: 0, losses: 0, bestTime: null },
    intermediate: { wins: 0, losses: 0, bestTime: null },
    expert:       { wins: 0, losses: 0, bestTime: null },
    custom:       { wins: 0, losses: 0, bestTime: null }
};

// Custom inputs
const customSettings = document.getElementById("custom-settings");
const customRows = document.getElementById("custom-rows");
const customCols = document.getElementById("custom-cols");
const customMines = document.getElementById("custom-mines");

const gamesPlayedSpan = document.getElementById("games-played");
const winsSpan = document.getElementById("wins");
const lossesSpan = document.getElementById("losses");
const bestTimeSpan = document.getElementById("best-time");

let totalGamesPlayed = 0;
let rows = 9, cols = 9, bombsCount = 10;
let board = [], gameOver = false, firstClick = true;
let flagsLeft = 0, timer = 0, timerInt;
let explodedCell = null; // 🔹 Important

// ---------- DIFFICULTY & EVENTS ----------
difficulty.onchange = () => {
    customSettings.style.display = (difficulty.value==="custom") ? "block" : "none";
    setDifficulty();
    updateSessionStats();
};

smiley.onclick = startGame;
window.onload = () => {
    setDifficulty();
    updateAppearance();
};
[customRows, customCols, customMines].forEach(input => input.oninput = setDifficulty);
toggleBtn.onclick = () => { document.body.classList.toggle("light"); document.body.classList.toggle("dark"); };
settingsBtn.onclick = () => {
    settingsPanel.style.display = settingsPanel.style.display === "none" ? "block" : "none";
};
bgColorInput.oninput = updateAppearance;
themeSelect.onchange = updateAppearance;

// ---------- TIMER ----------
function formatTime(seconds){
    const h = Math.floor(seconds/3600), m = Math.floor((seconds%3600)/60), s = seconds%60;
    return [h,m,s].map(n => String(n).padStart(2,"0")).join(":");
}

// ---------- GAME FUNCTIONS ----------
function setDifficulty(){
    if(difficulty.value==="beginner")[rows,cols,bombsCount]=[9,9,10];
    else if(difficulty.value==="intermediate")[rows,cols,bombsCount]=[16,16,40];
    else if(difficulty.value==="expert")[rows,cols,bombsCount]=[16,30,99];
    else if(difficulty.value==="custom"){
        rows = Math.min(Math.max(parseInt(customRows.value)||2,2),100);
        cols = Math.min(Math.max(parseInt(customCols.value)||2,2),100);
        let maxMines = rows*cols;
        bombsCount = Math.min(Math.max(parseInt(customMines.value)||1,1), maxMines-1);
        customRows.value = rows; customCols.value = cols; customMines.value = bombsCount; customMines.max = maxMines-1;
    }
    startGame();
}

function startGame(){
    boardElem.classList.remove("win-border","lose-border");
    clearInterval(timerInt);
    timer = 0; firstClick = true; gameOver = false;
    explodedCell = null;
    flagsLeft = bombsCount; bombsDiv.textContent = flagsLeft;
    timerDiv.textContent = "00:00:00";
    statusDiv.textContent = ""; smiley.textContent = "🙂";
    board = Array.from({length:rows},()=>Array.from({length:cols},()=>({mine:false,open:false,flag:false,count:0,wrongFlag:false})));
    drawBoard();
    updateSessionStats(); 

}

const valid = (r,c) => r>=0 && c>=0 && r<rows && c<cols;

function placeMines(sr,sc){
    let p=0;
    while(p<bombsCount){
        let r=Math.floor(Math.random()*rows), c=Math.floor(Math.random()*cols);
        if((r===sr && c===sc) || board[r][c].mine) continue;
        board[r][c].mine = true; p++;
    }
    for(let r=0;r<rows;r++) for(let c=0;c<cols;c++)
        if(!board[r][c].mine) board[r][c].count = countMines(r,c);
}

function currentDifficultyKey(){
    return difficulty.value;
}

function countMines(r,c){
    let n=0;
    for(let dr=-1;dr<=1;dr++) for(let dc=-1;dc<=1;dc++)
        if(valid(r+dr,c+dc) && board[r+dr][c+dc].mine) n++;
    return n;
}

// ---------- DRAW BOARD ----------
function drawBoard(){
    boardElem.innerHTML = "";
    for(let r=0;r<rows;r++){
        const tr = document.createElement("tr");
        for(let c=0;c<cols;c++){
            const td = document.createElement("td");
            const cell = board[r][c];

            td.className = "";

            // Apply theme class to closed cells
            if(!cell.open){
                td.classList.add(`theme-${themeSelect.value}`);
            } else {
                // Apply open theme class
                td.classList.add(`theme-${themeSelect.value}`, "open");
            }

            // Content
            if(cell.open){
                if(cell.mine) td.textContent = "💣";
                else if(cell.count) { td.textContent = cell.count; td.classList.add("n"+cell.count); }
                if(explodedCell && explodedCell.r===r && explodedCell.c===c){
                    td.classList.add("exploded");
                }
            } else if(cell.flag){
                td.textContent = "🚩";
                if(cell.wrongFlag) td.classList.add("wrong-flag");
            }

            td.onclick = () => openCell(r,c);
            td.oncontextmenu = e => { e.preventDefault(); toggleFlag(r,c); };

            tr.appendChild(td);
        }
        boardElem.appendChild(tr);
    }
}

// ---------- OPEN CELL ----------
function openCell(r,c){
    if(gameOver) return;
    const cell = board[r][c];
    if(cell.open && cell.count && countFlags(r,c)===cell.count){ openAround(r,c); drawBoard(); return; }
    if(cell.open || cell.flag) return;

    if(firstClick){ placeMines(r,c); firstClick=false; timerInt=setInterval(()=>timerDiv.textContent=formatTime(++timer),1000); }

    cell.open = true;

    if(cell.mine){
        explodedCell = { r, c };
        clearInterval(timerInt);
        gameOver = true;

        document.body.classList.add("lost"); // ✅ ADD

        revealAll();
        boardElem.classList.add("lose-border");
        smiley.textContent="😵";
        statusDiv.textContent="💥 You lost!";
        statusDiv.className="lose";

        stats[difficulty.value].losses++;
        totalGamesPlayed++;
        updateSessionStats();
        drawBoard();
        return;
    } else if(cell.count===0) flood(r,c);

    checkWin(); drawBoard();
}

// ---------- FLOOD FILL ----------
function flood(r,c){
    for(let dr=-1;dr<=1;dr++) for(let dc=-1;dc<=1;dc++){
        const nr = r+dr, nc = c+dc;
        if(valid(nr,nc) && !board[nr][nc].open && !board[nr][nc].mine){
            board[nr][nc].open = true;
            if(board[nr][nc].count===0) flood(nr,nc);
        }
    }
}

// ---------- FLAG ----------
function toggleFlag(r,c){
    if(gameOver || board[r][c].open) return;
    board[r][c].flag = !board[r][c].flag;
    flagsLeft += board[r][c].flag ? -1 : 1;
    bombsDiv.textContent = flagsLeft;
    drawBoard();
}

function countFlags(r,c){
    let n=0;
    for(let dr=-1;dr<=1;dr++) for(let dc=-1;dc<=1;dc++)
        if(valid(r+dr,c+dc) && board[r+dr][c+dc].flag) n++;
    return n;
}

function openAround(r,c){
    for(let dr=-1;dr<=1;dr++) for(let dc=-1;dc<=1;dc++){
        const nr=r+dr, nc=c+dc;
        if(valid(nr,nc) && !board[nr][nc].flag && !board[nr][nc].open) openCell(nr,nc);
    }
}

// ---------- REVEAL ALL ----------
function revealAll(){
    for(let r=0;r<rows;r++) for(let c=0;c<cols;c++){
        const cell = board[r][c];

        // Show unflagged mines only
        if(cell.mine && !cell.flag){
            cell.open = true;
        }

        // Mark incorrect flags
        if(cell.flag && !cell.mine){
            cell.wrongFlag = true;
        }
    }
    drawBoard();
}


// ---------- CHECK WIN ----------
function checkWin(){
    if(gameOver) return;

    for(let r=0;r<rows;r++){
        for(let c=0;c<cols;c++){
            if(!board[r][c].mine && !board[r][c].open) return;
        }
    }

    clearInterval(timerInt);
    gameOver = true;

    const diff = difficulty.value;

    stats[diff].wins++;
    totalGamesPlayed++;

    if(stats[diff].bestTime === null || timer < stats[diff].bestTime){
        stats[diff].bestTime = timer;
    }

    autoFlagRemainingMines();
    drawBoard();

    boardElem.classList.add("win-border");
    smiley.textContent = "😎";
    statusDiv.textContent = "🎉 You win!";
    statusDiv.className = "win";

    updateSessionStats();
}

// ---------- SESSION STATS ----------
function updateSessionStats(){
    const diff = difficulty.value;
    const s = stats[diff];

    gamesPlayedSpan.textContent = totalGamesPlayed;
    winsSpan.textContent = s.wins;
    lossesSpan.textContent = s.losses;
    bestTimeSpan.textContent = s.bestTime !== null
        ? formatTime(s.bestTime)
        : "---";
}

function autoFlagRemainingMines(){
    for(let r=0;r<rows;r++) for(let c=0;c<cols;c++){
        const cell = board[r][c];
        if(cell.mine && !cell.flag) cell.flag = true;
    }
    flagsLeft = 0;
    bombsDiv.textContent="0";
}

// ---------- APPEARANCE ----------
function updateAppearance(){
    document.body.style.background = bgColorInput.value;
    document.querySelectorAll("td").forEach(td => {
        td.classList.remove("theme-classic","theme-neon","theme-retro","theme-plastic");
        if(!td.classList.contains("open")) td.classList.add(`theme-${themeSelect.value}`);
    });
}
</script>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    webview.create_window(
        title="Minesweeper",
        html=HTML,
        width=1100,
        height=750,
        resizable=True
    )
    webview.start()
