<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>三国‑接壤城池连线版｜势力城池抱团</title>
<style>
*{margin:0;padding:0}
body{background:#222;color:#fff;font-size:14px}
/*开场视频样式 */
#openingVideo{
    position:fixed;
    top:0;
    left:0;
    width:100vw;
    height:100vh;
    background:#000;
    z-index:9999;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}
#openingVid{
    width:100%;
    height:100%;
    object-fit:cover;
}
#startVideoBtn{
    z-index:100;
    padding:16px 36px;
    font-size:18px;
    cursor:pointer;
}
#skipOpening{
    position:absolute;
    bottom:40px;
    right:40px;
    background:rgba(0,0,0,0.6);
    color:#ffffff;
    border:2px solid #fff;
    padding:12px 24px;
    font-size:16px;
    cursor:pointer;
}
#menu{
    width:100vw;
    height:100vh;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:30px;
    background: url("main_bg.png") center no-repeat;
    background-size: cover;
}
button{padding:15px 40px;margin:8px;font-size:18px}
#stageSel{display:none;text-align:center;margin-top:30px;}
#lordSel{display:none;text-align:center;margin-top:80px;}
#game{display:none;padding:10px}
#map{border:2px solid #666;display:block}
#cityInfo{margin-top:12px;padding:12px;border:1px solid #444;min-height:160px}
.avatar{width:64px;height:64px;border:1px solid white;margin:6px 0}
input{padding:4px;width:180px;color:#000}
#popUp{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
background:#333;padding:25px;border:2px solid white;min-width:450px}
#battlePage{display:none;padding:20px}
#battleCanvas{border:2px solid #fff;background:#383838}
.stage‑img{
    width:480px;
    height:270px;
    object-fit:cover;
    border:2px solid white;
    margin-bottom:20px;
}
.save-btn{
    padding:8px 16px;
    margin:4px;
}
</style>
</head>
<body>
<!--10秒自定义开场视频-->
<div id="openingVideo">
    <video id="openingVid" src="opening.mp4" muted playsinline></video>
    <button id="startVideoBtn">点击播放开场动画</button>
    <button id="skipOpening">直接跳过片头</button>
</div>

<div id="menu">
<h2>三国群雄</h2>
<button onclick="openStage()">开始游戏</button>
<button onclick="openSaveSelect()">继续游戏</button>
</div>

<div id="stageSel">
    <h3>选择历史时期（悬浮按钮预览地图）</h3>
    <img id="stagePreview" class="stage‑img">
    <div id="btnWrap"></div>
    <br>
    <button onclick="backMenu()">返回主菜单</button>
</div>

<div id="lordSel">
    <h3>选择你操控的君主</h3>
    <div id="lordWrap"></div>
    <br>
    <button onclick="backMenu()">返回主菜单</button>
</div>

<div id="game">
<div>回合:<span id="t">1</span> 出征冷却:<span id="cd">0</span> ｜ 金币：<span id="gold">5000</span>
<button class="save-btn" onclick="saveGame(1)">存档1</button>
<button class="save-btn" onclick="saveGame(2)">存档2</button>
<button onclick="backMenu()">退回主菜单</button>
</div>
<canvas id="map" width="900" height="600"></canvas>
<div id="msg"></div>
<div id="cityInfo">点击任意城池查看详情</div>
</div>

<div id="popUp">
<h3>配置出征部队(最多携带10名武将)</h3>
<div id="selectHeroBox"></div>
<br>
<button onclick="confirmArmy()">确认组建出征部队</button>
<button onclick="closePop()">关闭</button>
</div>

<div id="battlePage">
<h2>武将一对一单挑战场</h2>
<canvas id="battleCanvas" width="950" height="550"></canvas>
<div style="margin-top:8px">
<button id="endTurnBtn" onclick="enemyAiTurn()">敌方回合</button>
<button style="display:none" id="exitBattle" onclick="exitBattle()">退出战斗</button>
<span id="battleTip">点击按钮开启武将挑选对战</span>
<button onclick="openSelectBattle()">选择武将进行单挑</button>
<br>
<button onclick="backMenu()">返回主菜单</button>
</div>

<div id="savePop" style="display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#333;padding:30px;border:2px solid white">
<h3>选择存档槽</h3>
<button class="save-btn" onclick="loadSave(1)">读取存档1</button>
<button class="save-btn" onclick="loadSave(2)">读取存档2</button>
<br>
<button onclick="closeSavePop()">关闭</button>
</div>

<script>
//开场视频控制代码
const openingVideo = document.getElementById('openingVideo');
const openingVid = document.getElementById('openingVid');
const startVideoBtn = document.getElementById('startVideoBtn');
const skipOpening = document.getElementById('skipOpening');

//点击之后才播放视频，绕过浏览器自动播放限制
startVideoBtn.onclick=async function(){
    await openingVid.play();
    startVideoBtn.style.display="none";
}

//播放完毕关闭片头
openingVid.addEventListener('ended',()=>{
    openingVideo.style.opacity = "0";
    setTimeout(()=>{openingVideo.style.display = "none"},800)
})

//跳过片头
skipOpening.onclick = function(){
    openingVid.pause();
    openingVideo.style.opacity = "0";
    setTimeout(()=>{openingVideo.style.display = "none"},800)
}


let canvas,ctx,cityList=[],turn=1,cool=0,bandit=[];
let nowIndex = 0;
let playerLord = "";
let gold = 5000;
let selectCity = null;
let attackTargetCity = null;
let selectedHeroList = [];
let sendSoldierNum = 0;
let powerUsedHero = {};
//新增：部队待命标记
let armyReady = false;

let battleCanvas,battleCtx;
let playerBattleHero = [];
let enemyBattleHero = [];
let selectedHeroIndex = -1;
let playerCanOperate = true;

//战斗系统新增变量
let prisonerList = [];
let battleLog = [];

const SAVE_KEY1 = "save_slot_1";
const SAVE_KEY2 = "save_slot_2";

const lordColor = {
    "张角":"#cc2222",
    "何进":"#dddd22",
    "丁原":"#22ccdd",
    "卢植":"#aa55ff",
    "皇甫嵩":"#22dd55",
    "董卓":"#702020",
    "袁绍":"#e6b800",
    "曹操":"#4488ff",
    "孙坚":"#ff6622",
    "公孙瓒":"#88dd22",
    "刘备":"#dd2266",
    "刘表":"#995522",
    "张绣":"#663388",
    "吕布":"#c99400",
    "袁术":"#b82e9c",
    "刘璋":"#2e8b57",
    "孙策":"#ff8811",
    "马腾":"#22aaaa",
    "孙权":"#ff4444",
    "张鲁":"#8b4513",
    "马超":"#0099cc",
    "曹仁":"#3366cc",
    "吕蒙":"#208060",
    "曹丕":"#5577dd",
    "公孙渊":"#aa7722",
    "孟获":"#6b4422",
    "士燮":"#44aaaa",
    "曹休":"#7755cc",
    "诸葛亮":"#cc2255",
    "司马懿":"#882222",
    "姜维":"#227766",
    "邓艾":"#559922",
    "司马炎":"#4444aa",
    "刘禅":"#bb3377",
    "孙皓":"#dd6622",
    "司马昭":"#602040",
    "刘渊":"#993333"
};

const stage=[
{
    name:"黄巾之乱",
    lords:{
        "张角":["张梁","张宝","程远志","马元义","波才","严政","高升"],
        "何进":["卢植","皇甫嵩","邹靖"],
        "丁原":["张辽","张杨"],
        "卢植":["傅燮"],
        "皇甫嵩":["朱儁"]
    }
},
{
    name:"讨伐董卓",
    lords:{
        "董卓":["吕布","华雄","李儒","樊稠"],
        "袁绍":["颜良","文丑"],
        "曹操":["夏侯惇","许褚","郭嘉"],
        "孙坚":["程普","黄盖"],
        "公孙瓒":["赵云","严纲"]
    }
},
{
    name:"官渡之战",
    lords:{
        "袁绍":["颜良","文丑","淳于琼"],
        "曹操":["许褚","郭嘉","徐晃","张郃","夏侯惇"],
        "刘备":["关羽","张飞"],
        "刘表":["蔡瑁"],
        "张绣":["贾诩"]
    }
},
{
    name:"吕布之死",
    customCityCount:{"吕布":1,"曹操":8},
    lords:{
        "吕布":["陈宫","高顺","张辽","臧霸"],
        "曹操":["夏侯惇","许褚","郭嘉","徐晃","张郃","乐进","于禁","李典"],
        "刘备":["关羽","张飞"],
        "袁术":["纪灵"],
        "刘璋":["张任"]
    }
},
{
    name:"群雄逐鹿",
    lords:{
        "曹操":["夏侯惇","许褚","郭嘉"],
        "孙策":["周瑜","太史慈","甘宁","周泰"],
        "刘表":["蔡瑁"],
        "马腾":["韩遂"],
        "刘璋":["张任"]
    }
},
{
    name:"汉中之战",
    lords:{
        "刘备":["黄忠","赵云","严颜"],
        "曹操":["夏侯渊","庞德","王平"],
        "孙权":["周瑜","太史慈"],
        "张鲁":["杨松"],
        "马超":["马岱"]
    }
},
{
    name:"襄樊之战",
    lords:{
        "刘备":["关平","周仓"],
        "曹操":["曹仁","徐晃"],
        "孙权":["吕蒙","陆逊","蒋钦"],
        "曹仁":["满宠"],
        "吕蒙":["甘宁"]
    }
},
{
    name:"三国鼎立",
    lords:{
        "刘备":["诸葛亮","马谡"],
        "曹丕":["张辽","徐晃"],
        "孙权":["陆逊"],
        "公孙渊":["卑衍"],
        "孟获":["兀突骨"]
    }
},
{
    name:"火烧连营",
    lords:{
        "曹丕":["曹真","曹休"],
        "孙权":["陆抗"],
        "孟获":["带来洞主"],
        "士燮":["士壹"],
        "曹休":["贾逵"]
    }
},
{
    name:"北伐曹魏",
    lords:{
        "诸葛亮":["魏延","姜维"],
        "司马懿":["邓艾","钟会","郭淮","王基"],
        "姜维":["张翼"],
        "邓艾":["钟会"],
        "孙权":["吕蒙"]
    }
},
{
    name:"天下归晋",
    lords:{
        "司马炎":["司马昭","羊祜","杜预","王濬"],
        "刘禅":["姜维"],
        "孙皓":["陆抗"],
        "司马昭":["邓艾"],
        "刘渊":["刘曜"]
    }
}
];

const nameToPinyin = {
    "张角":"zhangjiao","张梁":"zhangliang","张宝":"zhangbao","何进":"hejin",
    "丁原":"dingyuan","卢植":"luzhi","皇甫嵩":"huangfusong","程远志":"chengyuanzhi",
    "马元义":"mayuanyi","波才":"bocai","邹靖":"zoujing","严政":"yanzheng",
    "高升":"gaosheng","董卓":"dongzhuo","袁绍":"yuanshao","曹操":"caocao",
    "孙坚":"sunjian","公孙瓒":"gongsunzan","吕布":"lvbu","华雄":"huaxiong",
    "李儒":"liru","程普":"chengpu","黄盖":"huanggai","颜良":"yanliang",
    "文丑":"wenchou","樊稠":"fanchou","许褚":"xuchu","郭嘉":"guojia",
    "关羽":"guanyu","张飞":"zhangfei","徐晃":"xuhuang","张郃":"zhanghe",
    "淳于琼":"chunyuqiong","陈宫":"chengong","高顺":"gaoshun","夏侯惇":"xiahoudun",
    "纪灵":"jiling","张辽":"zhangliao","臧霸":"zangba","孙策":"sunce",
    "刘表":"liubiao","马腾":"mateng","刘璋":"liuzhang","周瑜":"zhouyu",
    "太史慈":"taishici","韩遂":"hansui","张任":"zhangren","蔡瑁":"caimao",
    "甘宁":"ganning","周泰":"zhoutai","黄忠":"huangzhong","赵云":"zhaoyun",
    "夏侯渊":"xiahouyuan","庞德":"pangde","王平":"wangping","严颜":"yanyan",
    "曹仁":"caoren","吕蒙":"lvmeng","关平":"guanping","周仓":"zhoucang",
    "陆逊":"luxun","蒋钦":"jiangqin","曹丕":"caopi",
    "公孙渊":"gongsunyuan","孟获":"menghuo","诸葛亮":"zhugeliang","马谡":"masu",
    "兀突骨":"wutugu","士燮":"shixie","曹休":"caoxiu","陆抗":"lukang",
    "带来洞主":"dailaidongzhu","士壹":"shiyi","曹真":"caozhen","司马懿":"simayi",
    "姜维":"jiangwei","邓艾":"dengai","魏延":"weiyan","钟会":"zhonghui",
    "王基":"wangji","郭淮":"guohuai","司马炎":"simayan","刘禅":"liushan",
    "孙皓":"sunhao","司马昭":"simazhao","刘渊":"liuyuan","羊祜":"yanghu",
    "杜预":"duyu","王濬":"wangjun","乐进":"lejing","于禁":"yujin","李典":"lidian",
    "贾诩":"jiaxu","朱儁":"zhujun","傅燮":"fuxie","张杨":"zhangyang","严纲":"yangang",
    "马岱":"madai","杨松":"yangsong","满宠":"manchong","卑衍":"beiyan","张翼":"zhangyi","刘曜":"liuyao","贾逵":"jiakui",
    "武将":"wujiang"
};

function getHeroImg(heroName){
    let img=new Image();
    let fileName=nameToPinyin[heroName];
    if(!fileName)fileName="default";
    img.src=fileName+".png";
    img.onerror=function (){
        console.log(heroName + " 缺少头像文件：" + fileName + ".png");
        if(heroName === "武将"){
            img.src = "wujiang.png";
            this.onerror=null;
        }
    }
    return img;
}

function setStagePreview(index){
    const previewImg = document.getElementById("stagePreview");
    previewImg.src = "stage"+(index+1)+".png";
}

function backMenu(){
    document.getElementById("menu").style.display="flex";
    document.getElementById("stageSel").style.display="none";
    document.getElementById("lordSel").style.display="none";
    document.getElementById("game").style.display="none";
    document.getElementById("battlePage").style.display="none";
    document.getElementById("popUp").style.display="none";
}

function saveGame(slot){
    let saveData = {
        cityList:JSON.parse(JSON.stringify(cityList)),
        turn:turn,
        cool:cool,
        gold:gold,
        playerLord:playerLord,
        nowIndex:nowIndex,
        powerUsedHero:JSON.parse(JSON.stringify(powerUsedHero))
    };
    if(slot===1) localStorage.setItem(SAVE_KEY1,JSON.stringify(saveData));
    else localStorage.setItem(SAVE_KEY2,JSON.stringify(saveData));
    alert("成功保存至存档槽"+slot);
}

function openSaveSelect(){
    document.getElementById("savePop").style.display="block";
}
function closeSavePop(){
    document.getElementById("savePop").style.display="none";
}

function loadSave(slot){
    let raw;
    if(slot===1) raw = localStorage.getItem(SAVE_KEY1);
    else raw = localStorage.getItem(SAVE_KEY2);
    if(!raw){
        alert("该存档槽为空");
        return;
    }
    let data = JSON.parse(raw);
    cityList = data.cityList;
    turn = data.turn;
    cool = data.cool;
    gold = data.gold;
    playerLord = data.playerLord;
    nowIndex = data.nowIndex;
    powerUsedHero = data.powerUsedHero;

    closeSavePop();
    document.getElementById("menu").style.display="none";
    document.getElementById("game").style.display="block";
    canvas=document.getElementById("map");
    ctx=canvas.getContext("2d");
    refreshGoldUI();
    render();
}

function openStage(){
    document.getElementById("menu").style.display="none";
    document.getElementById("stageSel").style.display="flex";
    const wrap = document.getElementById("btnWrap");
    wrap.innerHTML = "";
    for(let i=0;i<stage.length;i++){
        let b = document.createElement("button");
        b.innerText = stage[i].name;
        b.onclick = function(){
            nowIndex = i;
            openLordSelect();
        }
        b.onmouseover=function(){
            setStagePreview(i);
        }
        wrap.appendChild(b);
    }
    setStagePreview(0);
}

function openLordSelect(){
    document.getElementById("stageSel").style.display="none";
    document.getElementById("lordSel").style.display="flex";
    const wrap = document.getElementById("lordWrap");
    wrap.innerHTML = "";
    let lordList = Object.keys(stage[nowIndex].lords);
    for(let name of lordList){
        let btn = document.createElement("button");
        btn.innerText = name;
        btn.onclick = function(){
            playerLord = name;
            newGame();
        }
        wrap.appendChild(btn);
    }
}

function createGeneral(name){
    return {
        name:name,
        force:60 + Math.floor(Math.random()*40),
        hp:100
    }
}

function getUnusedHero(lordName,pool){
    if(!powerUsedHero[lordName]) powerUsedHero[lordName] = [];
    for(let h of pool){
        if(!powerUsedHero[lordName].includes(h)){
            powerUsedHero[lordName].push(h);
            return h;
        }
    }
    return null;
}

function getTopGeneral(city){
    let heroArr = city.generals.filter(g=>g.name !== city.owner);
    if(heroArr.length === 0) return null;
    let top = heroArr[0];
    heroArr.forEach(g=>{
        if(g.force>top.force) top = g;
    })
    return top;
}

function getCityDistance(a,b){
    return Math.hypot(a.x - b.x, a.y - b.y);
}

function aiAttackWork(){
    let powerList = [];
    cityList.forEach(c=>{
        if(c.owner!="无主" && !powerList.includes(c.owner)){
            powerList.push(c.owner);
        }
    })
    for(let power of powerList){
        if(power === playerLord) continue;
        let myCities = cityList.filter(x=>x.owner===power);
        let nearEnemy = [];
        myCities.forEach(own=>{
            cityList.forEach(other=>{
                if(other.owner !== power && other.owner !== "无主" && getCityDistance(own,other)<130){
                    nearEnemy.push(other);
                }
            })
        })
        let enemyCities = nearEnemy.length>0 ? nearEnemy : cityList.filter(x=>x.owner!==power&&x.owner!="无主");
        if(myCities.length>0 && enemyCities.length>0){
            let attackCity = myCities[Math.floor(Math.random()*myCities.length)];
            let target = enemyCities[Math.floor(Math.random()*enemyCities.length)];
            let winRate = attackCity.army/(attackCity.army+target.army);
            if(Math.random()<winRate){
                target.owner = power;
                document.getElementById("msg").innerText=power+"攻占了"+target.name;
                render();
            }
        }
    }
}

function newGame(){
    document.getElementById("lordSel").style.display="none";
    document.getElementById("game").style.display="block";
    canvas=document.getElementById("map");
    ctx=canvas.getContext("2d");
    turn=1;cool=0;bandit=[];
    gold = 5000;
    selectCity=null;
    selectedHeroList = [];
    sendSoldierNum=0;
    armyReady = false;
    refreshGoldUI();
    powerUsedHero = {};

    cityList=[];
    for(let i=0;i<56;i++){
        cityList.push({
            name:"城池"+(i+1),
            x:40+Math.random()*820,
            y:40+Math.random()*520,
            owner:"无主",
            army:2000,
            generals:[]
        })
    }

    let data = stage[nowIndex];
    let lords = Object.keys(data.lords);
    let customCount = data.customCityCount || {};
    let defaultPiece = Math.floor(56 / lords.length);

    for(let s=0;s<lords.length;s++){
        let lordName = lords[s];
        let heroPool = data.lords[lordName];
        powerUsedHero[lordName] = [lordName];
        let needCityNum = customCount[lordName] ?? defaultPiece;

        let baseIndex = Math.floor(Math.random()*cityList.length);
        let baseCity = cityList[baseIndex];
        baseCity.owner = lordName;
        baseCity.generals.push(createGeneral(lordName));
        baseCity.generals.push(createGeneral("武将"));
        let ranName = getUnusedHero(lordName,heroPool);
        if(ranName) baseCity.generals.push(createGeneral(ranName));

        let restCities = cityList.filter(c=>c.owner === "无主");
        restCities.sort((a,b)=> getCityDistance(baseCity,a) - getCityDistance(baseCity,b));

        for(let i = 0;i < needCityNum-1 && i < restCities.length;i++){
            let nearCity = restCities[i];
            nearCity.owner = lordName;
            nearCity.generals.push(createGeneral(lordName));
            nearCity.generals.push(createGeneral("武将"));
            let newHero = getUnusedHero(lordName,heroPool);
            if(newHero) nearCity.generals.push(createGeneral(newHero));
        }
    }
    render();
}

function render(){
    ctx.clearRect(0,0,900,600);
    ctx.font="11px 微软雅黑";

    //改用二次贝塞尔曲线绘制弯曲连接线
    for(let i=0;i<cityList.length;i++){
        for(let j=i+1;j<cityList.length;j++){
            let a=cityList[i];
            let b=cityList[j];
            if(a.owner!="无主"&&a.owner===b.owner&&getCityDistance(a,b)<130){
                ctx.strokeStyle = a.owner===playerLord ? "#77ff77":"#ffffff";
                ctx.lineWidth=2;
                ctx.beginPath();
                //计算中点偏移，制造弯曲
                let midX=(a.x+b.x)/2 + (Math.random()*40-20);
                let midY=(a.y+b.y)/2 + (Math.random()*40-20);
                ctx.moveTo(a.x,a.y);
                ctx.quadraticCurveTo(midX,midY,b.x,b.y);
                ctx.stroke();
            }
        }
    }

    for(let c of cityList){
        let col="#777";
        if(c.owner===playerLord) col="#3c3";
        else if(c.owner!="无主") col = (lordColor[c.owner] || "#ff4444");
        ctx.fillStyle=col;
        ctx.beginPath();
        ctx.arc(c.x,c.y,12,0,Math.PI*2);
        ctx.fill();
        ctx.fillStyle="#ffffff";
        ctx.fillText(c.name,c.x-22,c.y-6);
        ctx.fillText(c.owner,c.x-22,c.y+20);
    }
}

document.querySelector("#map").onclick = function (e){
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx=(e.clientX - rect.left)*scaleX;
    const my=(e.clientY - rect.top)*scaleY;
    let clickCity = null;
    for(let c of cityList){
        if(Math.hypot(mx-c.x,my-c.y)<30){
            clickCity = c;
            break;
        }
    }
    //已经组建好出征部队，现在选择目标城池
    if(armyReady && clickCity){
        if(clickCity.owner === playerLord){
            //己方城池：部队移动进驻
            clickCity.generals.push(...selectedHeroList);
        }else if(clickCity.owner === "无主"){
            //空城直接占领
            clickCity.owner = playerLord;
            clickCity.generals.push(...selectedHeroList);
        }else{
            //敌方城池开启单挑战斗
            attackTargetCity = clickCity;
            startBattle();
        }
        //重置出征部队状态
        selectedHeroList = [];
        armyReady = false;
        render();
        return;
    }
    //普通点击城池查看详情
    if(clickCity){
        selectCity = clickCity;
        selectedHeroList = [];
        sendSoldierNum=0;
        showCityInfo(clickCity);
        return;
    }
}

function openPop(){
    document.getElementById("popUp").style.display="block";
    let heroBox = document.getElementById("selectHeroBox");
    heroBox.innerHTML = "";
    let heroes = getAllMyHero();
    heroes.forEach(h=>{
        heroBox.innerHTML += `<div onclick="toggleHero('${h.name}')">${h.name} 武力${h.force} HP:${h.hp} ${selectedHeroList.includes(h)?'✅已选中':'☐未选中'}</div>`
    })
}
function closePop(){
    document.getElementById("popUp").style.display="none";
}

function toggleHero(name){
    let hero = getAllMyHero().find(x=>x.name === name);
    let idx = selectedHeroList.indexOf(hero);
    if(idx>-1){
        selectedHeroList.splice(idx,1);
    }else{
        if(selectedHeroList.length<10) selectedHeroList.push(hero);
    }
    openPop();
}
//确认组建出征部队
function confirmArmy(){
    if(cool>0){alert("出征冷却未结束");return}
    if(selectedHeroList.length===0){alert("请挑选出征武将");return}
    armyReady = true;
    closePop();
    document.getElementById("msg").innerText="出征部队组建完毕，请点击目标城池";
}

function getAllMyHero(){
    let myCitys = cityList.filter(x=>x.owner===playerLord);
    let allMyHero = [];
    let heroNameArr=[];
    myCitys.forEach(c=>{
        c.generals.forEach(h=>{
            if(!heroNameArr.includes(h.name)){
                heroNameArr.push(h.name);
                allMyHero.push(h);
            }
        })
    })
    return allMyHero;
}

//====全新战斗模块，其余所有代码不动====
//筛选剔除俘虏，获取本场能够出战武将
function getAvailableHero(heroArray) {
    return heroArray.filter(hero => {
        return !prisonerList.some(p => p.name === hero.name);
    })
}

//手动选择敌我武将开启单挑
function openSelectBattle() {
    const usableMy = getAvailableHero(playerBattleHero);
    const usableEnemy = getAvailableHero(enemyBattleHero);

    if (usableMy.length <= 0) {
        alert("我方所有武将已经被俘，本次攻城失败");
        exitBattle();
        return;
    }
    if (usableEnemy.length <= 0) {
        alert("敌方武将全部被俘，成功拿下城池");
        attackTargetCity.owner = playerLord;
        turn++;gold +=1200;
        turnIncome();aiAttackWork();
        exitBattle();
        return;
    }

    const chooseMy = prompt(`我方存活武将：${usableMy.map(h=>h.name).join("、")}\n输入出战武将姓名`);
    const chooseEnemy = prompt(`敌方存活武将：${usableEnemy.map(h=>h.name).join("、")}\n选择对敌武将`);

    const myFight = usableMy.find(item => item.name === chooseMy);
    const enemyFight = usableEnemy.find(item => item.name === chooseEnemy);

    if(!myFight || !enemyFight){
        alert("武将选取无效，请重新操作");
        return;
    }
    runOneDuel(myFight,enemyFight);
}

//执行一次单挑对战，战败武将本场直接被俘
function runOneDuel(heroSelf,heroOpp){
    let selfSoldier = 10;
    let oppSoldier = 10;
    let selfForce = heroSelf.force;
    let oppForce = heroOpp.force;

    while(selfSoldier > 0 && oppSoldier > 0){
        oppSoldier -= Math.max(1,selfForce / 8);
        if(oppSoldier <= 0) break;
        selfSoldier -= Math.max(1,oppForce / 8);
    }

    if(selfSoldier <= 0){
        prisonerList.push(heroSelf);
        battleLog.push(`${heroSelf.name}战败被俘，本场无法再次出战`);
        document.getElementById("battleTip").innerText = `${heroSelf.name}战败被俘`;
        //主公被俘直接游戏结束，清空存档
        if(heroSelf.name === playerLord){
            localStorage.removeItem(SAVE_KEY1);
            localStorage.removeItem(SAVE_KEY2);
            alert("主公被俘！游戏结束，存档已经清除");
            backMenu();
            return;
        }
    }else{
        prisonerList.push(heroOpp);
        battleLog.push(`${heroOpp.name}战败被俘`);
        document.getElementById("battleTip").innerText = `${heroOpp.name}战败被俘`;
        if(heroOpp.name === attackTargetCity.owner){
            attackTargetCity.owner = playerLord;
        }
    }
    renderBattleCanvas();
}

//开启战斗界面并且初始化俘虏列表
function startBattle(){
    battleCanvas=document.getElementById("battleCanvas");
    battleCtx=battleCanvas.getContext("2d");
    playerBattleHero = JSON.parse(JSON.stringify(selectedHeroList));
    enemyBattleHero = JSON.parse(JSON.stringify(attackTargetCity.generals));
    prisonerList = [];
    battleLog = [];
    selectedHeroIndex = -1;
    playerCanOperate = true;

    document.getElementById("game").style.display="none";
    document.getElementById("battlePage").style.display="block";
    document.getElementById("exitBattle").style.display="none";
    document.getElementById("battleTip").innerText="点击【选择武将进行单挑】按钮";
    renderBattleCanvas();
    cool = 2;
}

function renderBattleCanvas(){
    battleCtx.clearRect(0,0,950,550);
    const usableMy = getAvailableHero(playerBattleHero);
    const usableEn = getAvailableHero(enemyBattleHero);

    playerBattleHero.forEach((hero,idx)=>{
        let x=40,y=100+idx*75;
        let img=getHeroImg(hero.name);
        img.onload=()=>{
            battleCtx.drawImage(img,x,y,60,60);
        }
        //被俘武将灰色遮罩
        if(prisonerList.some(p=>p.name===hero.name)){
            battleCtx.fillStyle="rgba(80,80,80,0.65)";
            battleCtx.fillRect(x,y,60,60);
        }
        battleCtx.fillStyle="#ffffff";
        battleCtx.font="16px 微软雅黑";
        battleCtx.fillText(`${hero.name} 武力:${hero.force}`,110,135+idx*75);
    })

    enemyBattleHero.forEach((hero,idx)=>{
        let x=600,y=100+idx*75;
        let img=getHeroImg(hero.name);
        img.onload=()=>{
            battleCtx.drawImage(img,x,y,60,60);
        }
        if(prisonerList.some(p=>p.name===hero.name)){
            battleCtx.fillStyle="rgba(80,80,80,0.65)";
            battleCtx.fillRect(x,y,60,60);
        }
        battleCtx.fillStyle="#ffffff";
        battleCtx.font="16px 微软雅黑";
        battleCtx.fillText(`${hero.name} 武力:${hero.force}`,670,135+idx*75);
    })
}

//敌方AI回合暂时保留，你手动单挑即可
function enemyAiTurn(){
    document.getElementById("battleTip").innerText="全部对战由你手动选择武将";
}

function exitBattle(){
    document.getElementById("battlePage").style.display="none";
    document.getElementById("game").style.display="block";
    render();
    selectedHeroList = [];
    armyReady = false;
}

function showCityInfo(city){
    let topGen = getTopGeneral(city);
    let taiShouText = topGen ? topGen.name : "无";
    let picName;
    if(topGen){
        picName = nameToPinyin[topGen.name] ?? "default";
    }else{
        picName="default";
    }
    let btnHtml = "";
    if(city.owner === playerLord){
        btnHtml = `<br><button onclick="attackTargetCity=selectCity;openPop()">出征</button>`
    }
    let html = `
        <div>城池名称：${city.name}</div>
        <div>所属势力：${city.owner}</div>
        <div>驻守兵力：${city.army}</div>
        <div>城内武将总数：${city.generals.length}</div>
        <div>当前太守：${taiShouText}
        </div>
        <img class="avatar" src="${picName}.png" 
        data‑lock="0"
        onerror="if(this.dataset.lock==='0'){this.src='wujiang.png';this.dataset.lock='1';}">
        ${btnHtml}
        <br>
        <button onclick="recruit('${city.name}')">花费800金币，征兵+1000士兵</button>
    `
    document.getElementById("cityInfo").innerHTML = html;
}

window.recruit = function(cityName){
    if(gold < 800){
        alert("金币不足，无法征兵");
        return;
    }
    let target = cityList.find(item=>item.name === cityName);
    target.army += 1000;
    gold -= 800;
    refreshGoldUI();
    showCityInfo(target);
}

function turnIncome(){
    let money = 0;
    cityList.forEach(c=>{
        if(c.owner === playerLord) money += 350;
    })
    gold += money;
}

function refreshGoldUI(){
    document.getElementById("gold").innerText = gold;
}

setInterval(function(){
    if(cool>0) cool--;
    document.getElementById("t").innerText=turn;
    document.getElementById("cd").innerText=cool;
},800)
</script>
</body>
</html>