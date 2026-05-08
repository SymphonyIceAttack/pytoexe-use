import random
import math
import tkinter
from tkinter import *
from tkinter import ttk

window = Tk()
window.resizable(width=False, height=False)

a=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]

canvas1 = Canvas(bg="white", width=420,height=420)

VA=5
VB=0

def button4AA():
    global canvas1
    global button4AB
    global button4AC
    global button4AD
    global text4AA
    global buttonA
    window.geometry("720x420")
    canvas1 = Canvas(bg="white", width=720, height=720)
    canvas1.pack(expand=1)
    button4AB = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3", fg="black", bg="white")
    button4AB.place(x=250, y=100)
    button4AC = tkinter.Button(window, text="Средний текст(4-6 класс)", command=button4AF, width="35", height="3", fg="black", bg="white")
    button4AC.place(x=250, y=175)
    button4AD = tkinter.Button(window, text="Большой текст(7-11 класс)", command=button4AG, width="35", height="3", fg="black", bg="white")
    button4AD.place(x=250, y=250)
    text4AA=canvas1.create_text(360,360,text="Во время чтения текста, попробуйте запомнить основной смысл текста, а не каждую деталь в нём.",font=("Times New Roman", 14),width=600)
    buttonA = ttk.Button(text="<-", command=button2)
    buttonA.place(x=5, y=1)

def button4AG():
    global canvas1
    global VB
    global timer
    global buttonA
    global textAA
    canvas1.destroy()
    buttonA.destroy()
    window.geometry("1280x720")
    canvas1 = Canvas(bg="white", width=1280, height=720)
    canvas1.pack(expand=1)
    VB = 0
    textAA=canvas1.create_text(620,350,text="Мы пришли в отчаяние. Мы не знали, как поймать этого рыжего кота. Он обворовывал нас каждую ночь. Он так ловко прятался, что никто из нас его толком не видел. Только через неделю удалось, наконец, установить, что у кота разорвано ухо и отрублен кусок грязного хвоста. Это был кот, потерявший всякую совесть, кот — бродяга и бандит. Звали его за глаза Ворюгой. Он воровал всё: рыбу, мясо, сметану и хлеб. Однажды он даже разрыл в чулане жестяную банку с червями. Их он не съел, но на разрытую банку сбежались куры и склевали весь наш запас червей. Объевшиеся куры лежали на солнце и стонали. Мы ходили около них и ругались, но рыбная ловля всё равно была сорвана. Почти месяц мы потратили на то, чтобы выследить рыжего кота. Деревенские мальчишки помогали нам в этом. Однажды они примчались. И, запыхавшись, рассказали, что на рассвете кот пронёсся, приседая, через огороды и протащил в зубах кукан с окунями. Мы бросились в погреб и обнаружили пропажу кукана; на нём было десять жирных окуней, пойманных на Прорве. Это было уже не воровство, а грабёж средь бела дня. Мы поклялись поймать кота и вздуть его за бандитские проделки. Кот попался этим же вечером. Он украл со стола кусок ливерной колбасы и полез с ним на берёзу. Мы начали трясти берёзу. Кот уронил колбасу, она упала на голову Рувиму. Кот смотрел на нас сверху дикими глазами и грозно выл. Но спасения не было, и кот решился на отчаянный поступок. С ужасающим воем он сорвался с берёзы, упал на землю, подскочил, как футбольный мяч, и умчался под дом. Дом был маленький. Он стоял в глухом, заброшенном саду. Каждую ночь нас будил стук диких яблок, падавших с веток на его тесовую крышу. Дом был завален удочками, дробью, яблоками и сухими листьями. Мы в нём только ночевали. Все дни, от рассвета до темноты, мы проводили на берегах бесчисленных протоков и озёр. Там мы ловили рыбу и разводили костры в прибрежных зарослях. Чтобы пройти к берегу озёр, приходилось вытаптывать узкие тропинки в душистых высоких травах. Их венчики качались над головами и осыпали плечи жёлтой цветочной пылью. Возвращались мы вечером, исцарапанные шиповником, усталые, сожжённые солнцем, со связками серебристой рыбы, и каждый раз нас встречали рассказами о новых босяцких выходках рыжего кота. Но, наконец, кот попался. Он залез под дом в единственный узкий лаз. Выхода оттуда не было. Мы заложили лаз старой рыболовной сетью и начали ждать. Но кот не выходил. Он противно выл, как подземный дух, выл непрерывно и без всякого утомления. Прошёл час, два, три... Пора было ложиться спать, но кот выл и ругался под домом, и это действовало нам на нервы. Тогда был вызван Лёнька, сын деревенского сапожника. Лёнька славился бесстрашием и ловкостью. Ему поручили вытащить из-под дома кота.",font=("Times New Roman", 18),width=1220)
    buttonA = ttk.Button(text="->", command=button4DA)
    buttonA.place(x=1200, y=690)
    canvas1.after(1000, timer1)

def button4DA():
    global canvas1
    global textAA
    global buttonA
    canvas1.delete(textAA)
    buttonA.destroy()
    textAA=canvas1.create_text(620,350,text="Мы услышали хруст и хищное щёлканье — кот вцепился зубами в рыбью голову. Он вцепился мёртвой хваткой. Лёнька потащил за леску. Кот отчаянно упирался, но Лёнька был сильнее, и, кроме того, кот не хотел выпускать вкусную рыбу. Через минуту голова кота с зажатой в зубах плотицей показалась в отверстии лаза. Лёнька схватил кота за шиворот и поднял над землёй. Мы впервые его рассмотрели как следует. Кот зажмурил глаза и прижал уши. Хвост он на всякий случай подобрал под себя. Это оказался тощий, несмотря на постоянное воровство, огненно-рыжий кот-беспризорник с белыми подпалинами на животе. Рассмотрев кота, Рувим задумчиво спросил: — Что же нам с ним делать? — Выдрать! — сказал я. — Не поможет, — сказал Лёнька. — У него с детства характер такой. Попробуйте его накормить как следует. Кот ждал, зажмурив глаза. Мы последовали этому совету, втащили кота в чулан и дали ему замечательный ужин: жареную свинину, заливное из окуней, творожники и сметану. Кот ел больше часа. Он вышел из чулана пошатываясь, сел на пороге и мылся, поглядывая на нас и на низкие звёзды зелёными нахальными глазами. После умывания он долго фыркал и тёрся головой о пол. Это, очевидно, должно было обозначать веселье. Мы боялись, что он протрёт себе шерсть на затылке. Потом кот перевернулся на спину, поймал свой хвост, пожевал его, выплюнул, растянулся у печки и мирно захрапел. С этого дня он у нас прижился и перестал воровать. На следующее утро он даже совершил благородный и неожиданный поступок. Куры влезли на стол в саду и, толкая друг друга и переругиваясь, начали склёвывать из тарелок гречневую кашу. Кот, дрожа от негодования, прокрался к курам и с коротким победным криком прыгнул на стол. Куры взлетели с отчаянным воплем. Они перевернули кувшин с молоком и бросились, теряя перья, удирать из сада. Впереди мчался, икая, голенастый петух-дурак, прозванный Горлачом. Кот нёсся за ними на трёх лапах, а четвёртой, передней лапой бил петуха по спине. От петуха летели пыль и пух. Внутри его от каждого удара что- то бухало и гудело, будто кот бил по резиновому мячу. После этого петух несколько минут лежал в припадке, закатив глаза, и тихо стонал. Его облили холодной водой, и он отошёл. С тех пор куры опасались воровать. Увидев кота, они с писком и толкотнёй прятались под домом. Кот ходил по дому и саду, как хозяин и сторож. Он тёрся головой о наши ноги. Он требовал благодарности, оставляя на наших брюках клочья рыжей шерсти. Мы переименовали его из Ворюги в Милиционера. Хотя Рувим и утверждал, что это не совсем удобно, но мы были уверены, что милиционеры не будут на нас за это в обиде. Лёнька взял шёлковую леску, привязал к ней за хвост пойманную днём плотицу и закинул её через лаз в подполье. Вой прекратился.",font=("Times New Roman", 18),width=1220)
    buttonA = ttk.Button(text="завершить чтение", command=button4DB)
    buttonA.place(x=1170, y=690)

def button4DB():
    global textAA
    global buttonA
    canvas1.delete(textAA)
    buttonA.destroy()
    canvas1.create_text(640,50,text="Вопросы для самопроверки",font=("Times New Roman", 20))
    canvas1.create_text(640, 100, text="Какой дом был у людей?", font=("Times New Roman", 20))
    canvas1.create_text(640, 150, text="Как кот показал свою благодарность ребятам?", font=("Times New Roman", 20))
    canvas1.create_text(640, 200, text="Каким способом они поймали кота?", font=("Times New Roman", 20))
    canvas1.create_text(640, 250, text="В каком состоянии был кот?", font=("Times New Roman", 20))
    canvas1.create_text(640, 350, text=str(math.floor(VB/60))+":"+str(VB%60), font=("Times New Roman", 30))
    canvas1.create_text(640, 300, text="Время чтения текста", font=("Times New Roman", 25))
    buttonA = ttk.Button(text="Выйти из задания", command=button2)
    buttonA.place(x=590, y=400)

def button4AF():
    global canvas1
    global VB
    global timer
    global buttonA
    global textAA
    canvas1.destroy()
    buttonA.destroy()
    window.geometry("1080x720")
    canvas1 = Canvas(bg="white", width=1080, height=720)
    canvas1.pack(expand=1)
    VB = 0
    textAA=canvas1.create_text(520,300,text="В одном далёком королевстве жила была Принцесса. И всё у неё было: и большой дворец, и самые красивые наряды, но ей всегда было мало. Увидит у кого – ни будь понравившуюся вещь и тут – же кричит: «Это моё платье!», «Мои туфли!», «Моя кофта!», «Моё пальто!», «Моя шубка!», «Моя шапка!» А Король не мог своей любимой дочке отказать и слуги отбирали понравившуюся вещь и отдавали Принцессе – лишь бы она не плакала. Однажды Принцесса вышла на прогулку и увидела красивого белого коня. «Мой конь» - сказала она приказным тоном и слуги тотчас отобрали его у хозяина. Но как только она на него села, конь галопом поскакал в лес и там сбросил свою наездницу. Испугалась Принцесса – в этом лесу жили страшные дикие звери! И вдруг рядом с ней из берлоги вылез медведь и как зарычит: «Моя добыча! Моя! Моя!» Еле – еле Принцесса от него убежала и вернулась во дворец. С тех пор Принцесса перестала говорить «Моя или моё» - уж очень сильно медведь её напугал.",font=("Times new roman", 24),width=1020)
    buttonA = ttk.Button(text="Завершить чтение текста", command=button4CA)
    buttonA.place(x=900, y=690)
    canvas1.after(1000, timer1)

def button4CA():
    global textAA
    global buttonA
    canvas1.delete(textAA)
    buttonA.destroy()
    canvas1.create_text(540, 50, text="Вопросы для самопроверки", font=("Times New Roman", 20))
    canvas1.create_text(540, 100, text="Что есть у Принцессы?", font=("Times New Roman", 20))
    canvas1.create_text(540, 150, text="Куда поскакал конь и с кем?", font=("Times New Roman", 20))
    canvas1.create_text(540, 200, text="Почему Принцесса перестала требовать все вещи вокруг себя?", font=("Times New Roman", 20))
    canvas1.create_text(540, 350, text=str(math.floor(VB / 60)) + ":" + str(VB % 60), font=("Times New Roman", 30))
    canvas1.create_text(540, 300, text="Время чтения текста", font=("Times New Roman", 25))
    buttonA = ttk.Button(text="Выйти из задания", command=button2)
    buttonA.place(x=490, y=400)

def button4AE():
    global canvas1
    global VB
    global timer
    global buttonA
    global textAA
    canvas1.destroy()
    buttonA.destroy()
    window.geometry("1080x720")
    canvas1 = Canvas(bg="white", width=1080, height=720)
    canvas1.pack(expand=1)
    VB = 0
    textAA=canvas1.create_text(520,180,text="Как-то в зоопарке поселился очень злой лев. Он рычал дни и ночи напролёт, пугал всех посетителей зоопарка и злился даже на тех, кто его кормил. Одним солнечным утром в вольер ко льву залетела маленькая храбрая птичка. Ей стало жалко сердитого льва, и она устроилась возле него на деревне. Лев только собрался зарычать и прогнать её, но тут птичка запела, да так прекрасно, что он замер. С тех пор лев боялся рычать слишком громко, чтобы не спугнуть прекрасную птичку.",font=("Times New Roman", 26),width=1020)
    buttonA = ttk.Button(text="Завершить чтение текста", command=button4BA)
    buttonA.place(x=900, y=690)
    canvas1.after(1000, timer1)

def button4BA():
    global textAA
    global buttonA
    canvas1.delete(textAA)
    buttonA.destroy()
    canvas1.create_text(540, 50, text="Вопросы для самопроверки", font=("Times New Roman", 20))
    canvas1.create_text(540, 100, text="На кого рычал лев?", font=("Times New Roman", 20))
    canvas1.create_text(540, 150, text="Почему лев перестал рычать так громко?", font=("Times New Roman", 20))
    canvas1.create_text(540, 350, text=str(math.floor(VB / 60)) + ":" + str(VB % 60), font=("Times New Roman", 30))
    canvas1.create_text(540, 300, text="Время чтения текста", font=("Times New Roman", 25))
    buttonA = ttk.Button(text="Выйти из задания", command=button2)
    buttonA.place(x=490, y=400)

def timer1():
    global VB
    global canvas1
    VB+=1
    canvas1.after(1000,timer1)

def button1AB():
    global VA
    global sizecheck
    if VA > 3:
        VA=VA-1
        sizecheck.config(text=str(VA) + "x" + str(VA))

def button1AC():
    global VA
    global sizecheck
    if VA < 9:
        VA=VA+1
        sizecheck.config(text=str(VA) + "x" + str(VA))

def button3():
    global buttonA
    global canvas1
    global button4AB
    global button4AC
    global button4AD
    button4AB = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3",fg="black", bg="white")
    button4AC = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3",fg="black", bg="white")
    button4AD = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3",fg="black", bg="white")
    b=["го","ка","ло","ко","сто","мя","во","на","ру","ше","ре","ча","вк","ку","це","бо","ку","сле","дра","ме","на","ве","со","сме","сце","му","вы","ра","ры","от","те","го","би","гла","за","ве"]
    c=["сти", "ша", "жка","шка","лб","та","лк","бор","ка","лк","чь","шка","ус","ст","лое","кс","ча","за","ма","тро","лог","дро","сна","на","на","сор","зов","зум","ба","бор","нь","нка","лет","ва","пах","чер"]
    window.geometry("720x600")
    canvas1=Canvas(bg="white", width=720, height=720)
    canvas1.pack(expand=1)
    d=list(zip(b,c))
    random.shuffle(d)
    b,c=zip(*d)
    canvas1.create_line(300, 60, 420, 60)
    canvas1.create_line(270, 120, 450, 120)
    canvas1.create_line(240, 180, 480, 180)
    canvas1.create_line(210, 240, 510, 240)
    canvas1.create_line(180, 300, 540, 300)
    canvas1.create_line(150, 360, 570, 360)
    canvas1.create_line(120, 420, 600, 420)
    canvas1.create_line(90, 480, 630, 480)
    canvas1.create_line(60, 540, 660, 540)
    canvas1.create_text(360, 50, text="1",font=("Times New Roman", 20))
    canvas1.create_text(360, 110, text="2", font=("Times New Roman", 20))
    canvas1.create_text(360, 170, text="3", font=("Times New Roman", 20))
    canvas1.create_text(360, 230, text="4", font=("Times New Roman", 20))
    canvas1.create_text(360, 290, text="5", font=("Times New Roman", 20))
    canvas1.create_text(360, 350, text="6", font=("Times New Roman", 20))
    canvas1.create_text(360, 410, text="7", font=("Times New Roman", 20))
    canvas1.create_text(360, 470, text="8", font=("Times New Roman", 20))
    canvas1.create_text(360, 530, text="9", font=("Times New Roman", 20))
    canvas1.create_text(280, 50, text=str(''.join(map(str, b[:1]))), font=("Times New Roman", 20))
    canvas1.create_text(440, 50, text=str(''.join(map(str, c[:1]))), font=("Times New Roman", 20))
    canvas1.create_text(250, 110, text=str(''.join(map(str, b[1:2]))), font=("Times New Roman", 20))
    canvas1.create_text(470, 110, text=str(''.join(map(str, c[1:2]))), font=("Times New Roman", 20))
    canvas1.create_text(220, 170, text=str(''.join(map(str, b[2:3]))), font=("Times New Roman", 20))
    canvas1.create_text(500, 170, text=str(''.join(map(str, c[2:3]))), font=("Times New Roman", 20))
    canvas1.create_text(190, 230, text=str(''.join(map(str, b[3:4]))), font=("Times New Roman", 20))
    canvas1.create_text(530, 230, text=str(''.join(map(str, c[3:4]))), font=("Times New Roman", 20))
    canvas1.create_text(160, 290, text=str(''.join(map(str, b[4:5]))), font=("Times New Roman", 20))
    canvas1.create_text(560, 290, text=str(''.join(map(str, c[4:5]))), font=("Times New Roman", 20))
    canvas1.create_text(130, 350, text=str(''.join(map(str, b[5:6]))), font=("Times New Roman", 20))
    canvas1.create_text(590, 350, text=str(''.join(map(str, c[5:6]))), font=("Times New Roman", 20))
    canvas1.create_text(100, 410, text=str(''.join(map(str, b[6:7]))), font=("Times New Roman", 20))
    canvas1.create_text(620, 410, text=str(''.join(map(str, c[6:7]))), font=("Times New Roman", 20))
    canvas1.create_text(70, 470, text=str(''.join(map(str, b[7:8]))), font=("Times New Roman", 20))
    canvas1.create_text(650, 470, text=str(''.join(map(str, c[7:8]))), font=("Times New Roman", 20))
    canvas1.create_text(40, 530, text=str(''.join(map(str, b[8:9]))), font=("Times New Roman", 20,))
    canvas1.create_text(680, 530, text=str(''.join(map(str, c[8:9]))), font=("Times New Roman", 20))
    buttonA=ttk.Button(text="<-",command=button2)
    buttonA.place(x=5,y=1)

def button2():
    global button4AB
    global button4AC
    global button4AD
    canvas1.destroy()
    buttonA.destroy()
    button4AB.destroy()
    button4AC.destroy()
    button4AD.destroy()
    window.geometry("720x420")

def button1():
    global buttonA
    global canvas1
    global button4AB
    global button4AC
    global button4AD
    button4AB = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3",fg="black", bg="white")
    button4AC = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3",fg="black", bg="white")
    button4AD = tkinter.Button(window, text="Короткий текст(1-3 класс)", command=button4AE, width="35", height="3",fg="black", bg="white")
    VB=0
    LA = list(range(1, (pow(VA, 2) + 1)))
    random.shuffle(LA)
    window.geometry(str(VA*84)+"x"+str(VA*84))
    canvas1 = Canvas(bg="white", width=VA*84, height=VA*84)
    canvas1.pack(expand=1)
    for RC in range(1,VA):
        canvas1.create_line(RC*84,0,RC*84,VA*84)
        canvas1.create_line(0,RC*84,VA*84,RC*84)
    for RA in range(1,VA+1):
        for RB in range(1,VA+1):
            canvas1.create_text(42+(RB-1)*84,42+(RA-1)*84, text=str(''.join(map(str, LA[VB:VB+1]))), font=("Times New Roman", 20))
            VB=VB+1
    buttonA=ttk.Button(text="<-",command=button2)
    buttonA.place(x=5,y=1)


window.title("Программа для скорочтния")
window.geometry("720x420")
window["bg"] = "white"

titler=tkinter.Label(window, text="Программа для скорочтения",font=("Times New Roman", 20), fg="black", bg="white")
titler.pack()
titler.place(x=200, y=50)

buttonAA=tkinter.Button(window, text="Таблица Шульте", command=button1,width="35",height="3",fg="black",bg="white")
buttonAA.place(x=250, y=100)

buttonAB=tkinter.Button(window, text="-", command=button1AB,width="3",height="1",fg="black",bg="white")
buttonAB.place(x=600, y=100)
buttonAC=tkinter.Button(window, text="+", command=button1AC,width="3",height="1",fg="black",bg="white")
buttonAC.place(x=630, y=100)
sizecheck=tkinter.Label(window, text=str(VA)+"x"+str(VA),font=("Times New Roman", 14), fg="black", bg="white")
sizecheck.pack()
sizecheck.place(x=613, y=130)

buttonBB=tkinter.Button(window, text="Клиновидная таблица", command=button3,width="35",height="3",fg="black",bg="white")
buttonBB.place(x=250, y=175)

titlerer=tkinter.Label(window, text="Постарайся делать упражнения смотря на середину!",font=("Times New Roman", 14), fg="black", bg="white")
titlerer.place(x=160, y=320)

button4=tkinter.Button(window, text="Тексты для проверки навыков скорочтения", command=button4AA,width="35",height="3",fg="black",bg="white")
button4.place(x=250, y=360)

window.mainloop()