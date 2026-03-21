from flask import Flask, render_template_string, request
import pyautogui

app = Flask(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

html = """

<!DOCTYPE html>
<html>
<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Ultimate Gaming Controller</title>

<style>

body{
margin:0;
background:#020617;
color:white;
font-family:Segoe UI;
text-align:center;
overflow:hidden;
touch-action:none;
user-select:none;
}

#pad{
width:95%;
height:40vh;
margin:auto;
margin-top:10px;
background:#0f172a;
border-radius:20px;
touch-action:none;
}

button{
padding:12px 16px;
margin:5px;
font-size:16px;
border:none;
border-radius:10px;
background:#2563eb;
color:white;
}

button:active{
background:#1d4ed8;
}

#mode{
background:#16a34a;
}

#settings{
position:fixed;
top:5px;
left:5px;
}

#panel{
display:none;
position:fixed;
top:40px;
left:5px;
background:#0f172a;
padding:10px;
border-radius:10px;
}

.gamebtn{
width:70px;
height:70px;
font-size:20px;
position:absolute;
touch-action:none;
}

#spacebtn{
width:150px;
}

#keyboard{
width:85%;
padding:12px;
margin-top:10px;
border-radius:10px;
border:none;
font-size:16px;
}

</style>
</head>

<body oncontextmenu="return false">

<h3>Touch Gaming Controller</h3>

<div id="settings">
<button onclick="openSettings()">⚙</button>
</div>

<div id="panel">
<p>Drag buttons to reposition</p>
<button onclick="closeSettings()">OK</button>
</div>

<button id="mode" onclick="toggleMode()">Mobile Mode OFF</button>

<div id="pad"></div>

<div>
<button onclick="leftClick()">Left Click</button>
<button onclick="rightClick()">Right Click</button>
</div>

<input id="keyboard" placeholder="Type here (Wireless Keyboard)">

<button class="gamebtn" id="wbtn" style="top:55%;left:70%">W</button>
<button class="gamebtn" id="abtn" style="top:65%;left:60%">A</button>
<button class="gamebtn" id="sbtn" style="top:65%;left:70%">S</button>
<button class="gamebtn" id="dbtn" style="top:65%;left:80%">D</button>
<button class="gamebtn" id="spacebtn" style="top:80%;left:65%">SPACE</button>

<script>

let editMode=false
let mobileMode=false

function toggleMode(){
mobileMode=!mobileMode
document.getElementById("mode").innerText=
mobileMode?"Mobile Mode ON":"Mobile Mode OFF"
}

/* SETTINGS */

function openSettings(){
editMode=true
document.getElementById("panel").style.display="block"
}

function closeSettings(){
editMode=false
document.getElementById("panel").style.display="none"
}

/* GAME BUTTONS */

function bindButton(id,key){

let btn=document.getElementById(id)

let offsetX=0
let offsetY=0

btn.addEventListener("touchstart",function(e){

e.preventDefault()

let t=e.touches[0]

offsetX=t.clientX-btn.offsetLeft
offsetY=t.clientY-btn.offsetTop

if(!editMode){
fetch("/keydown?key="+key)
}

},{passive:false})

btn.addEventListener("touchmove",function(e){

if(!editMode) return

e.preventDefault()

let t=e.touches[0]

btn.style.left=(t.clientX-offsetX)+"px"
btn.style.top=(t.clientY-offsetY)+"px"

},{passive:false})

btn.addEventListener("touchend",function(e){

e.preventDefault()

if(!editMode){
fetch("/keyup?key="+key)
}

},{passive:false})

}

bindButton("wbtn","w")
bindButton("abtn","a")
bindButton("sbtn","s")
bindButton("dbtn","d")
bindButton("spacebtn","space")

/* TOUCHPAD */

let pad=document.getElementById("pad")

let startX=0
let startY=0
let lastX=0
let lastY=0
let moved=false
let tapTime=0
let twoFinger=false

pad.addEventListener("touchstart",function(e){

e.preventDefault()

if(e.touches.length==2){
twoFinger=true
lastY=e.touches[0].clientY
return
}

twoFinger=false

let t=e.touches[0]

startX=t.clientX
startY=t.clientY
lastX=t.clientX
lastY=t.clientY

moved=false

},{passive:false})

pad.addEventListener("touchmove",function(e){

e.preventDefault()

if(twoFinger && e.touches.length==2){

let y=e.touches[0].clientY
let dy=y-lastY

fetch("/scroll?y="+dy)

lastY=y
return
}

let t=e.touches[0]

if(!mobileMode){

let dx=(t.clientX-lastX)*1.5
let dy=(t.clientY-lastY)*1.5

if(Math.abs(dx)>2 || Math.abs(dy)>2){
moved=true
}

fetch("/move?x="+dx+"&y="+dy)

lastX=t.clientX
lastY=t.clientY

}

},{passive:false})

pad.addEventListener("touchend",function(e){

if(twoFinger) return

let now=Date.now()

if(!mobileMode){

if(moved) return

if(now-tapTime<300){
fetch("/doubleclick")
}else{
fetch("/click")
}

tapTime=now
return
}

let t=e.changedTouches[0]

let dx=t.clientX-startX
let dy=t.clientY-startY

let absX=Math.abs(dx)
let absY=Math.abs(dy)

if(Math.max(absX,absY)<20) return

if(absX>absY){

if(dx<0){
fetch("/keypress?key=a")
}else{
fetch("/keypress?key=d")
}

}else{

if(dy<0){
fetch("/keypress?key=w")
}else{
fetch("/keypress?key=s")
}

}

},{passive:false})

/* MOUSE BUTTONS */

function leftClick(){
fetch("/click")
}

function rightClick(){
fetch("/rightclick")
}

/* WIRELESS KEYBOARD */

let lastVal=""

document.getElementById("keyboard").addEventListener("input",function(e){

let val=e.target.value

if(val.length>lastVal.length){
let char=val.slice(-1)
fetch("/keypress?key="+encodeURIComponent(char))
}

if(val.length<lastVal.length){
fetch("/keypress?key=backspace")
}

lastVal=val

})

</script>

</body>
</html>

"""

@app.route("/")
def home():
    return render_template_string(html)

@app.route("/click")
def click():
    pyautogui.click()
    return "OK"

@app.route("/doubleclick")
def doubleclick():
    pyautogui.doubleClick()
    return "OK"

@app.route("/rightclick")
def rightclick():
    pyautogui.rightClick()
    return "OK"

@app.route("/move")
def move():
    x=float(request.args.get("x"))
    y=float(request.args.get("y"))
    pyautogui.moveRel(x,y)
    return "OK"

@app.route("/scroll")
def scroll():
    y=float(request.args.get("y"))
    pyautogui.scroll(-y)
    return "OK"

@app.route("/keydown")
def keydown():
    key=request.args.get("key")
    pyautogui.keyDown(key)
    return "OK"

@app.route("/keyup")
def keyup():
    key=request.args.get("key")
    pyautogui.keyUp(key)
    return "OK"

@app.route("/keypress")
def keypress():
    key=request.args.get("key")
    pyautogui.press(key)
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
