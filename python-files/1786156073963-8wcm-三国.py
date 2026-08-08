<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>三国‑太守判定优化｜副将改名武将可出战</title>
<style>
*{margin:0;padding:0}
body{background:#222;color:#fff;font-size:14px}
#menu{text-align:center;margin-top:150px}
button{padding:15px 40px;margin:8px;font-size:18px}
#stageSel{display:none;text-align:center;margin-top:80px;}
#lordSel{display:none;text-align:center;margin-top:80px;}
#game{display:none;padding:10px}
#map{border:2px solid #666;display:block}
#cityInfo{margin-top:12px;padding:12px;border:1px solid #444;min-height:160px}
.avatar{width:64px;height:64px;border:1px solid white;margin:6px 0}
input{padding:4px;width:180px;color:#000}

/*出征弹窗 */
#popUp{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
background:#333;padding:25px;border:2px solid white;min-width:450px}
/*独立战斗界面 */
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
<div id="menu">
<h2>三国群雄</h2>
<button onclick="openStage()">开始游戏</button>
<button onclick="openSaveSelect()">继续游戏</button>
</div>

<div id="stageSel">
    <h3>选择历史时期</h3>
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

<!--出征弹窗 -->
<div id="popUp">
<h3>配置出征部队(最多携带10名武将，普通武将允许出战)</h3>
<div id="selectHeroBox"></div>
<br>
<div>出征兵力：<input type="number" id="armyInput"></div>
<br>
<button onclick="startBattle()">开启战斗</button>
<button onclick="closePop()">关闭</button>
</div>

<!--2D交互战斗页面 -->
<div id="battlePage">
<h2>平面战场交战</h2>
<canvas id="battleCanvas" width="950" height="550"></canvas>
<div style="margin-top:8px">
<button id="soldierAttackBtn" onclick="soldierGroupAttack()">军团士兵发起进攻</button>
<button id="endTurnBtn" onclick="enemyAiTurn()">结束我方回合</button>
<button style="display:none" id="exitBattle" onclick="exitBattle()">退出战斗</button>
<span id="battleTip">点击我方武将头像，之后点击敌方武将进行攻击</span>
<br>
<button onclick="backMenu()">返回主菜单</button>
</div>
</div>

<!--存档选择弹窗 -->
<div id="savePop" style="display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#333;padding:30px;border:2px solid white">
<h3>选择存档槽</h3>
<button class="save-btn" onclick="loadSave(1)">读取存档1</button>
<button class="save-btn" onclick="loadSave(2)">读取存档2</button>
<br>
<button onclick="closeSavePop()">关闭</button>
</div>

<script>
let canvas,ctx,cityList=[],turn=1,cool=0,bandit=[];
let nowIndex = 0;
let playerLord = "";
let gold = 5000;
let selectCity = null;
let attackTargetCity = null;
let selectedHeroList = [];
let sendSoldierNum = 0;
let powerUsedHero = {};

//战斗变量
let battleCanvas,battleCtx;
let playerBattleHero = [];
let enemyBattleHero = [];
let battlePlayerArmy = 0;
let battleEnemyArmy = 0;
let selectedHeroIndex = -1;
let playerCanOperate = true;

//本地存储双存档
const SAVE_KEY1 = "save_slot_1";
const SAVE_KEY2 = "save_slot_2";

//势力专属配色
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

//分剧本‑各个势力专属武将池
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

//拼音头像映射表（已修改为武将‑wujiang）
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

//头像加载兜底
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

//创建武将，守卫标记移除，普通武将可以出战
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

//获取城池武力最高武将，只剩君主返回null，用于太守‑无判定
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
    for(let c of cityList){
        if(Math.hypot(mx-c.x,my-c.y)<30){
            selectCity = c;
            selectedHeroList = [];
            sendSoldierNum=0;
            showCityInfo(c);
            return;
        }
    }
}

function openPop(){
    document.getElementById("popUp").style.display="block";
    let heroBox = document.getElementById("selectHeroBox");
    heroBox.innerHTML = "";
    let heroes = getAllMyHero();
    //所有武将全部允许出战
    heroes.forEach(h=>{
        heroBox.innerHTML += `<div onclick="toggleHero('${h.name}')">${h.name} 武力${h.force} ${selectedHeroList.includes(h)?'✅已选中':'☐未选中'}</div>`
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

function startBattle(){
    sendSoldierNum = Number(document.getElementById("armyInput").value);
    if(cool>0){alert("出征冷却未结束");return}
    if(selectedHeroList.length===0){alert("请挑选出征武将");return}
    if(!sendSoldierNum||sendSoldierNum<=0){alert("填写出征兵力");return}

    let totalTroop = 0;
    cityList.filter(x=>x.owner===playerLord).forEach(c=>totalTroop+=c.army);
    if(sendSoldierNum>totalTroop){alert("兵力不足");return}

    battleCanvas=document.getElementById("battleCanvas");
    battleCtx=battleCanvas.getContext("2d");
    battlePlayerArmy = sendSoldierNum;
    battleEnemyArmy = attackTargetCity.army;
    playerBattleHero = JSON.parse(JSON.stringify(selectedHeroList));
    enemyBattleHero = JSON.parse(JSON.stringify(attackTargetCity.generals));
    selectedHeroIndex = -1;
    playerCanOperate = true;

    document.getElementById("game").style.display="none";
    document.getElementById("battlePage").style.display="block";
    document.getElementById("exitBattle").style.display="none";
    document.getElementById("battleTip").innerText="点击我方武将头像选中，再点击敌方武将攻击";
    renderBattleCanvas();
    closePop();
}

function renderBattleCanvas(){
    battleCtx.clearRect(0,0,950,550);
    battleCtx.fillStyle="#48e848";
    battleCtx.font="18px 微软雅黑";
    battleCtx.fillText("我方兵力:"+battlePlayerArmy,30,30);
    for(let i=0;i<Math.min(battlePlayerArmy/80,28);i++){
        battleCtx.fillRect(30+i*30,50,22,22);
    }

    battleCtx.fillStyle="#ff5555";
    battleCtx.fillText("敌方兵力:"+battleEnemyArmy,520,30);
    for(let i=0;i<Math.min(battleEnemyArmy/80,28);i++){
        battleCtx.fillRect(520+i*30,50,22,22);
    }

    playerBattleHero.forEach((hero,idx)=>{
        let x=40,y=100+idx*75;
        let img=getHeroImg(hero.name);
        img.onload=()=>{
            battleCtx.drawImage(img,x,y,60,60);
        }
        if(selectedHeroIndex===idx){
            battleCtx.strokeStyle="#ffff00";
            battleCtx.lineWidth=4;
            battleCtx.strokeRect(x,y,60,60);
        }
        battleCtx.fillStyle="#ffffff";
        battleCtx.fillText(`${hero.name} HP:${Math.round(hero.hp)}`,110,135+idx*75);
    })

    enemyBattleHero.forEach((hero,idx)=>{
        let x=600,y=100+idx*75;
        let img=getHeroImg(hero.name);
        img.onload=()=>{
            battleCtx.drawImage(img,x,y,60,60);
        }
        battleCtx.fillStyle="#ffffff";
        battleCtx.fillText(`${hero.name} HP:${Math.round(hero.hp)}`,670,135+idx*75);
    })
}

battleCanvas.onclick=function(e){
    if(!playerCanOperate)return;
    let rect = battleCanvas.getBoundingClientRect();
    let mx = e.clientX - rect.left;
    let my = e.clientY - rect.top;

    for(let i=0;i<playerBattleHero.length;i++){
        let h = playerBattleHero[i];
        let x=40,y=100+i*75;
        if(mx>=x&&mx<=x+60&&my>=y&&my<=y+60&&h.hp>0){
            selectedHeroIndex = i;
            renderBattleCanvas();
            document.getElementById("battleTip").innerText="已经选中"+h.name+"，点击敌方武将发起攻击";
            return;
        }
    }
    if(selectedHeroIndex!==-1){
        let attacker = playerBattleHero[selectedHeroIndex];
        if(attacker.hp<=0) return;
        for(let i=0;i<enemyBattleHero.length;i++){
            let eh = enemyBattleHero[i];
            let x=600,y=100+i*75;
            if(mx>=x&&mx<=x+60&&my>=y&&my<=y+60&&eh.hp>0){
                let damage = attacker.force*Math.random()*0.4;
                eh.hp -= damage;
                document.getElementById("battleTip").innerText=attacker.name+"攻击"+eh.name+"，造成"+Math.round(damage)+"伤害";
                selectedHeroIndex=-1;
                renderBattleCanvas();
                checkBattleResult();
                return;
            }
        }
    }
}

function soldierGroupAttack(){
    if(!playerCanOperate) return;
    if(battlePlayerArmy<=0){
        document.getElementById("battleTip").innerText="我方士兵已经全部阵亡";
        return;
    }
    let aliveEnemy = enemyBattleHero.filter(e=>e.hp>0);
    if(aliveEnemy.length<=0)return;
    let target = aliveEnemy[Math.floor(Math.random()*aliveEnemy.length)];
    let damage = battlePlayerArmy*0.08;
    target.hp -= damage;
    battleEnemyArmy -= battlePlayerArmy*0.2;
    document.getElementById("battleTip").innerText("全军士兵进攻 "+target.name+"！");
    renderBattleCanvas();
    checkBattleResult();
}

function enemyAiTurn(){
    playerCanOperate=false;
    document.getElementById("battleTip").innerText="敌方回合正在行动";
    for(let h of enemyBattleHero){
        if(h.hp<=0)continue;
        let alivePlayer = playerBattleHero.filter(p=>p.hp>0);
        if(alivePlayer.length===0)break;
        let target = alivePlayer[Math.floor(Math.random()*alivePlayer.length)];
        let damage = h.force*Math.random()*0.4;
        target.hp -= damage;
    }
    battlePlayerArmy -= battleEnemyArmy*0.2;
    renderBattleCanvas();
    checkBattleResult();
    if(!checkBattleOver){
        playerCanOperate=true;
        document.getElementById("battleTip").innerText="轮到我方，点击武将头像进行攻击";
    }
}

let checkBattleOver=false;
function checkBattleResult(){
    checkBattleOver=false;
    if(battleEnemyArmy<=0||enemyBattleHero.every(x=>x.hp<=0)){
        checkBattleOver=true;
        document.getElementById("battleTip").innerText="战斗胜利，占领城池";
        attackTargetCity.owner = playerLord;
        attackTargetCity.army = Math.max(0,battlePlayerArmy);
        cool=2;turn++;gold +=1200;
        turnIncome();aiAttackWork();
        document.getElementById("endTurnBtn").style.display="none";
        document.getElementById("soldierAttackBtn").style.display="none";
        document.getElementById("exitBattle").style.display="block";
    }
    if(battlePlayerArmy<=0||playerBattleHero.every(x=>x.hp<=0)){
        checkBattleOver=true;
        document.getElementById("battleTip").innerText="部队战败全军覆没";
        cool=2;turn++;turnIncome();aiAttackWork();
        document.getElementById("endTurnBtn").style.display="none";
        document.getElementById("soldierAttackBtn").style.display="none";
        document.getElementById("exitBattle").style.display="block";
    }
}

function exitBattle(){
    document.getElementById("battlePage").style.display="none";
    document.getElementById("game").style.display="block";
    render();
    selectedHeroList = [];
}

//城池详情、太守无逻辑
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