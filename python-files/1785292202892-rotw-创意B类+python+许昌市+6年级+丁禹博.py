import turtle
import random
print("端午节小课堂")
print("端午节是农历五月初五")
print("是为了纪念爱国诗人屈原。")
print("习俗有：赛龙舟、吃粽子、挂艾草等")
print("今天我们来赛龙舟")

print("请你选择你支持的龙舟")
print("1————红队💓")
print("2————绿队💚")
print("3————蓝队💙")
choice =input("请输入1/2/3：").strip()

screen=turtle.Screen()
screen.bgcolor("lightblue")
screen.title("端午节赛龙舟")

t=turtle.Turtle()
t.speed(0)
t.hideturtle()

def draw_boat(x,y,color):
    t.penup()
    t.goto(x,y)
    t.pendown()
    t.color(color,color)
    t.begin_fill()
    t.forward(60)
    t.left(120)
    t.forward(20)
    t.left(60)
    t.forward(20)
    t.left(60)
    t.forward(20)
    t.left(120)
    t.forward(60)
    t.left(90)
    t.forward(15)
    t.left(90)
    t.forward(60)
    t.left(90)
    t.forward(15)
    t.end_fill()
    
def draw_track():
    t.color("black")
    for y in [-40,0,40]:
        t.penup()
        t.goto(-300,y-10)
        t.pendown()
        t.forward(600)

def draw_flag():
    t.penup()
    t.goto(250,-60)
    t.pendown()
    t.color("black")
    t.setheading(90)
    t.forward(140)
    t.right(90)
    t.color("red")
    t.begin_fill()
    for _ in range(2):
        t.forward(30)
        t.right(90)
        t.forward(20)
        t.right(90)
    t.end_fill()
    
draw_track()
draw_flag()
x_positions=[-280,-280,-280]
y_positions=[40,0,-40]
colors=["red","green","blue"]
for i in range (3):
    draw_boat(x_positions[i],y_positions[i],colors[i])

print("\n🏁比赛开始")
winner = None
round_count=0
while winner is None:
    round_count+=1
    for i in range (3):
        speed=random.randint(2,10)
        x_positions[i]+=speed
        
        t.penup()
        t.goto(x_positions[i],y_positions[i])
        t.pendown()
        t.color(colors[i])
        t.dot(40,colors[i])
        if x_positions[i]>=220 and winner is None:
            winner =i+1
print (f"\n比赛结束！一共用了{round_count}轮！")
print(f"冠军是{winner}号龙舟！")
if choice ==str(winner):
    print("太棒了，你猜对了！")
else:
    print("比赛很精彩，很可惜你没有猜对")
t.penup()
t.goto(0,-120)
t.color("black")
t.write(f"冠军：{winner}号龙舟！",align="center",font=("楷体",20,"bold"))
turtle.done()

    





