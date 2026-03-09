<script>
let jogadores=[]
let host=null
let meuNome=""
let turnoIndex=0      // jogador atual
let turnoInimigo=false // flag para alternar turno do inimigo
let inimigo=null
let jogo=false

function story(t){
    let d=document.getElementById("story")
    d.innerHTML+=t+"<br>"
    d.scrollTop=d.scrollHeight
}

function battle(t){
    let d=document.getElementById("battle")
    d.innerHTML+=t+"<br>"
    d.scrollTop=d.scrollHeight
}

function separadorTurno(){
    document.getElementById("story").innerHTML+="<hr>"
    document.getElementById("battle").innerHTML+="<hr>"
}

function roll(){
    return Math.floor(Math.random()*6)+1
}

const classes={
    guerreiro:{
        hp:100, atk:30,
        skills:[
            {nome:"Golpe de espada",tipo:"ataque",dano:5},
            {nome:"Bloqueio",tipo:"defesa",defesa:5},
            {nome:"Intimidar",tipo:"intimidar"},
            {nome:"Fugir",tipo:"fuga"}
        ]
    },
    mago:{
        hp:70, atk:35,
        skills:[
            {nome:"Bola de fogo",tipo:"ataque",dano:7},
            {nome:"Barreira",tipo:"defesa",defesa:5},
            {nome:"Feitiço do sono",tipo:"sono"},
            {nome:"Fugir",tipo:"fuga"}
        ]
    },
    paladino:{
        hp:110, atk:25,
        skills:[
            {nome:"Golpe de clava",tipo:"ataque",dano:4},
            {nome:"Cura",tipo:"cura",cura:4},
            {nome:"Distrair",tipo:"distrair"},
            {nome:"Fugir",tipo:"fuga"}
        ]
    },
    assassino:{
        hp:60, atk:35,
        skills:[
            {nome:"Facada",tipo:"ataque",dano:6},
            {nome:"Envenenar",tipo:"veneno"},
            {nome:"Ataque a espreita",tipo:"critico"},
            {nome:"Fugir",tipo:"fuga"}
        ]
    }
}

const inimigos=[
    {nome:"Goblin",hp:80,atk:10},
    {nome:"Orc",hp:120,atk:15},
    {nome:"Esqueleto",hp:90,atk:12}
]

function entrar(){
    if(jogadores.length >= 4){
        alert("Máximo de 4 jogadores!")
        return
    }
    let nome=document.getElementById("name").value.trim();
    if(!nome){ alert("Digite um nome!"); return }
    if(jogadores.some(p=>p.nome===nome)){ alert("Nome já utilizado!"); return }

    let classe=document.getElementById("classe").value
    let base=classes[classe]

    let jogador={
        nome:nome,
        classe:classe,
        hp:base.hp,
        maxhp:base.hp,
        atk:base.atk,
        bloqueio:0
    }
    jogadores.push(jogador)
    meuNome=nome

    if(jogadores.length===1){
        story(nome+" é o HOST e pode iniciar o jogo")
        renderHost()
    }

    renderPlayers()
}

function renderPlayers(){
    let div=document.getElementById("players")
    div.innerHTML=""
    jogadores.forEach((p,i)=>{
        let w=(p.hp/p.maxhp)*100
        let turnoAtual = (i===turnoIndex && !turnoInimigo && p.hp>0) ? "⬅️ Turno" : ""
        if(p.hp<=0){
            div.innerHTML+=`
            <div class="player" style="opacity:0.5">
            <b>${p.nome}</b> (${p.classe})<br>
            <b>MORTO</b> ${turnoAtual}<br>
            </div>`
        }else{
            div.innerHTML+=`
            <div class="player">
            <b>${p.nome}</b> (${p.classe}) ${turnoAtual}<br>
            HP: ${p.hp}/${p.maxhp}<br>
            ATK: ${p.atk}
            <div class="hpbar" style="width:${w}%"></div>
            </div>`
        }
    })
}

function renderHost(){
    let div=document.getElementById("hostControls")
    div.innerHTML=""
    if(jogadores.length>=1 && !jogo && meuNome===jogadores[0].nome){
        let b=document.createElement("button")
        b.innerText="Iniciar Jogo"
        b.onclick=iniciar
        div.appendChild(b)
    }
}

function iniciar(){
    if(jogo) return
    if(jogadores.length < 1) { alert("É necessário pelo menos 1 jogador"); return }
    jogo=true
    story("O jogo começou com "+jogadores.length+" jogador(es)!")
    spawnEnemy()
}

function spawnEnemy(){
    let base=inimigos[Math.floor(Math.random()*inimigos.length)]
    inimigo={
        nome:base.nome,
        hp:base.hp,
        maxhp:base.hp,
        atk:base.atk,
        venenoTurnos:0, sono:0, recuarTurnos:0, distraido:0
    }
    story("Um "+inimigo.nome+" aparece!")
    renderEnemy()
    turno()
}

function renderEnemy(){
    let div=document.getElementById("enemy")
    let w=(inimigo.hp/inimigo.maxhp)*100
    div.innerHTML=`
    <div class="player">
    <b>${inimigo.nome}</b><br>
    HP: ${inimigo.hp}/${inimigo.maxhp}<br>
    ATK: ${inimigo.atk}
    <div class="hpbar" style="width:${w}%"></div>
    </div>`
}

function turno(){
    separadorTurno()
    renderPlayers()
    renderEnemy()

    let vivos = jogadores.filter(p => p.hp > 0)
    if(vivos.length===0){
        story("<span style='color:red;font-weight:bold'>Todos os jogadores morreram! GAME OVER</span>")
        document.getElementById("actions").innerHTML = ""
        return
    }

    if(turnoInimigo){
        ataqueInimigo()
        turnoInimigo=false

        // avança para próximo jogador vivo
        do {
            turnoIndex++
            if(turnoIndex>=jogadores.length) turnoIndex=0
        } while(jogadores[turnoIndex].hp<=0)

        setTimeout(turno, 1000)
        return
    }

    // turno do jogador atual
    let j=jogadores[turnoIndex]
    story("Turno de "+j.nome)
    story(j.nome+" o que você faz?")
    mostrarAcoes(j)
}

function mostrarAcoes(j){
    let div=document.getElementById("actions")
    div.innerHTML=""
    if(j.hp<=0){
        div.innerHTML="Jogador morto, pulando turno..."
        setTimeout(()=>{
            turnoInimigo=true
            turno()
        },1000)
        return
    }

    classes[j.classe].skills.forEach(skill=>{
        let b=document.createElement("button")
        b.innerText=skill.nome
        b.onclick=()=>usarSkill(j,skill)
        div.appendChild(b)
    })
}

function usarSkill(j, skill){
    battle(j.nome+" usa "+skill.nome)
    let dadoJogador=roll()
    battle("🎲 dado jogador "+dadoJogador)

    // habilidades
    if(skill.tipo=="ataque"){
        let dano=dadoJogador*skill.dano
        battle("dano "+dano)
        inimigo.hp-=dano
    }
    if(skill.tipo=="defesa"){
        let defesa=dadoJogador*skill.defesa
        battle("bloqueio "+defesa)
        j.bloqueio=defesa
    }
    if(skill.tipo=="intimidar"){
        let dadoInimigo=roll()
        battle("🎲 dado inimigo "+dadoInimigo)
        if(dadoJogador>dadoInimigo){
            battle("Inimigo intimidado!")
            inimigo.recuarTurnos=2
            j.bloqueio=999
        }else battle("Intimidação falhou")
    }
    if(skill.tipo=="sono"){
        let dadoInimigo=roll()
        battle("🎲 dado inimigo "+dadoInimigo)
        if(dadoJogador>dadoInimigo){
            let diff=dadoJogador-dadoInimigo
            inimigo.sono=diff
            battle("Inimigo dormirá por "+diff+" turnos")
        }else battle("Feitiço falhou")
    }
    if(skill.tipo=="cura"){
        let cura=dadoJogador*skill.cura
        let alvo=jogadores.filter(p=>p.hp>0).reduce((a,b)=>(a.hp<b.hp?a:b))
        let antes=alvo.hp
        alvo.hp+=cura
        if(alvo.hp>alvo.maxhp)alvo.hp=alvo.maxhp
        battle(j.nome+" cura "+alvo.nome+" em "+(alvo.hp-antes))
    }
    if(skill.tipo=="distrair"){
        let dadoInimigo=roll()
        battle("🎲 dado inimigo "+dadoInimigo)
        if(dadoJogador>dadoInimigo){
            inimigo.distraido=2
            battle("Inimigo distraído por 2 turnos")
        }else battle("Falhou")
    }
    if(skill.tipo=="veneno"){
        inimigo.venenoTurnos=dadoJogador
        battle("Inimigo envenenado por "+dadoJogador+" turnos")
    }
    if(skill.tipo=="critico"){
        let dadoInimigo=roll()
        battle("🎲 dado inimigo "+dadoInimigo)
        if(dadoJogador>dadoInimigo){
            let dano=dadoJogador*6*2
            battle("CRÍTICO causando "+dano)
            inimigo.hp-=dano
            j.hp-=5
            battle(j.nome+" perde 5 HP pelo risco")
        }else battle("Ataque falhou")
    }
    if(skill.tipo=="fuga"){
        let dadoInimigo=roll()
        battle("🎲 dado inimigo "+dadoInimigo)
        if(dadoJogador>dadoInimigo){
            story("O grupo fugiu do combate!")
            spawnEnemy()
            return
        }else story("Fuga falhou!")
    }

    if(inimigo.hp<=0){
        story("O "+inimigo.nome+" foi derrotado!")
        spawnEnemy()
        return
    }

    renderPlayers()
    renderEnemy()

    // turno do inimigo agora
    turnoInimigo=true
    setTimeout(turno,1000)
}

function ataqueInimigo(){
    if(inimigo.sono>0){ battle("Inimigo está dormindo ("+inimigo.sono+" turnos)"); inimigo.sono--; return }
    if(inimigo.recuarTurnos>0){ battle("Inimigo recuando ("+inimigo.recuarTurnos+" turnos)"); inimigo.recuarTurnos--; return }
    if(inimigo.distraido>0){ battle("Inimigo distraído perdeu o ataque"); inimigo.distraido--; return }
    if(inimigo.venenoTurnos>0){ battle("Veneno causa 6 de dano"); inimigo.hp-=6; inimigo.venenoTurnos-- }

    let vivos=jogadores.filter(p=>p.hp>0)
    if(vivos.length===0) return

    let alvo=vivos[Math.floor(Math.random()*vivos.length)]
    let dano=inimigo.atk
    if(alvo.bloqueio){
        if(alvo.bloqueio>=dano){ battle(alvo.nome+" bloqueou todo o dano!"); dano=0 }
        else dano-=alvo.bloqueio
        alvo.bloqueio=0
    }
    battle(inimigo.nome+" ataca "+alvo.nome+" causando "+dano)
    alvo.hp-=dano
    if(alvo.hp<0)alvo.hp=0
}
</script>