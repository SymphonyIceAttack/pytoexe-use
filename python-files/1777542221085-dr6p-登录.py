import tkinter as tk
import random as r
name1="wyt"
mm1="wyt131428"
win=tk.Tk()
win.title("登录")
win.config(bg="DarkSlateGray")
win.geometry("400x350")
tk.Label(win,text="用户名：",font=("黑体",15,"bold"),bg="DarkSlateGray",fg="black").place(x=0,y=17)
tk.Label(win,text="密码：",font=("黑体",16,"bold"),bg="DarkSlateGray",fg="black").place(x=15,y=80)
pic1 = tk.PhotoImage(file=r"D:\素材\2打勾.png")
pic2=tk.PhotoImage(file=r"D:\素材\1.png")
p1=tk.Entry(win,bg="DarkGray",fg="black")
p1.pack(ipadx=50,ipady=10,padx=10,pady=10)
p2=tk.Entry(win,bg="DarkGray",fg="black",show="*")
p2.pack(ipadx=50,ipady=10,padx=10,pady=15)
def dl():
    name = p1.get().strip()
    mm = p2.get().strip()
    if name==name1:
        if mm==mm1:
            tx=tk.Toplevel()
            tx.title("系统消息")
            tx.geometry("300x400")
            tk.Label(tx,text="登录成功！",font=("黑体",20,"bold"),fg="green",image=pic1,compound="top").pack()
            tx.resizable(False,False)
        elif mm != mm1:
            tx = tk.Toplevel()
            tx.title("系统消息")
            tx.geometry("250x300")
            tk.Label(tx, text="密码错误！请重试。", font=("黑体", 15, "bold"),fg="red",image=pic2,compound="top").pack()
            tx.resizable(False, False)
    else:
        tx = tk.Toplevel()
        tx.title("系统消息")
        tx.geometry("250x300")
        tk.Label(tx, text="用户名错误！请重试。", font=("黑体", 15, "bold"),fg="red",image=pic2,compound="top").pack()
        tx.resizable(False, False)
b1=tk.Button(win,text="登录",font=("黑体",20,"bold"),command=dl,bg="LightGrey",fg="black")
b1.pack(ipadx=85,ipady=2)#登录模块
def zc():
    zcy=tk.Toplevel()
    zcy.resizable(False,False)
    zcy.title("注册新用户")
    zcy.config(bg="DarkSlateGray")
    zcy.geometry("700x500")
    tk.Label(zcy, text="输入一个新的用户名：", font=("黑体", 15, "bold"), bg="DarkSlateGray", fg="black").place(x=22, y=17)
    tk.Label(zcy, text="输入一个新密码：", font=("黑体", 16, "bold"), bg="DarkSlateGray", fg="black").place(x=50, y=80)
    tk.Label(zcy, text="输入验证码：", font=("黑体", 16, "bold"), bg="DarkSlateGray", fg="black").place(x=97, y=155)
    p3 = tk.Entry(zcy, bg="DarkGray", fg="black")
    p3.pack(ipadx=50, ipady=10, padx=10, pady=10)
    p4 = tk.Entry(zcy, bg="DarkGray", fg="black", show="*")
    p4.pack(ipadx=50, ipady=10, padx=10, pady=15)
    p5=tk.Entry(zcy, bg="DarkGray", fg="black")
    p5.pack(ipadx=50, ipady=10, padx=10, pady=20)
    yzm = int(r.randrange(100000, 1000000))
    def yzml():
        tk.Label(zcy, text=yzm, font=("黑体", 30, "bold"), bg="DarkCyan", fg="black").pack(ipadx=50, ipady=10, padx=10, pady=25)
        yzmhq.config(state="disabled")
        zc2.config(state="active")
    yzmhq=tk.Button(zcy,text="点击获取验证码",font=("黑体", 16, "bold"), bg="DarkSlateGray", fg="black",command=yzml)
    yzmhq.pack(ipadx=50, ipady=10, padx=10, pady=25)
    def zc22():
        name2=None
        mm2=None
        yzmyz = p5.get().strip()
        newname = p3.get().strip()
        newmm = p4.get().strip()
        yzmyzz = int(yzmyz)
        if yzmyzz==yzm:
            if newname=="wyt":
                tx = tk.Toplevel()
                tx.title("系统消息")
                tx.geometry("250x300")
                tk.Label(tx, text="用户名重复！请重试。", font=("黑体", 15, "bold"), fg="red", image=pic2,compound="top").pack()
                tx.resizable(False, False)
            else:
                tx = tk.Toplevel()
                tx.title("系统消息")
                tx.geometry("500x400")
                tk.Label(tx, text="注册成功！请在新登录窗口登录。", font=("黑体", 20, "bold"), fg="green", image=pic1, compound="top").pack()
                tx.resizable(False, False)
                zcy.withdraw()
                win.withdraw()
                name2=newname
                mm2=newmm
                xdl=tk.Toplevel()
                xdl.title("新登录")
                xdl.config(bg="DarkSlateGray")
                xdl.geometry("400x350")
                tk.Label(xdl, text="用户名：", font=("黑体", 15, "bold"), bg="DarkSlateGray", fg="black").place(x=0,y=17)
                tk.Label(xdl, text="密码：", font=("黑体", 16, "bold"), bg="DarkSlateGray", fg="black").place(x=15, y=80)
                p11 = tk.Entry(xdl, bg="DarkGray", fg="black")
                p11.pack(ipadx=50, ipady=10, padx=10, pady=10)
                p22 = tk.Entry(xdl, bg="DarkGray", fg="black", show="*")
                p22.pack(ipadx=50, ipady=10, padx=10, pady=15)
                def dl1():
                    name = p11.get().strip()
                    mm = p22.get().strip()
                    if name == name2:
                        if mm == mm2:
                            tx1 = tk.Toplevel()
                            tx1.title("系统消息")
                            tx1.geometry("300x400")
                            tk.Label(tx1, text="登录成功！", font=("黑体", 20, "bold"), fg="green", image=pic1,compound="top").pack()
                            tx1.resizable(False, False)
                        elif mm != mm2:
                            tx1 = tk.Toplevel()
                            tx1.title("系统消息")
                            tx1.geometry("250x300")
                            tk.Label(tx1, text="密码错误！请重试。", font=("黑体", 15, "bold"), fg="red", image=pic2,compound="top").pack()
                            tx1.resizable(False, False)
                    else:
                        tx1 = tk.Toplevel()
                        tx1.title("系统消息")
                        tx1.geometry("250x300")
                        tk.Label(tx1, text="用户名错误！请重试。", font=("黑体", 15, "bold"), fg="red", image=pic2,compound="top").pack()
                        tx1.resizable(False, False)
                b11 = tk.Button(xdl, text="登录", font=("黑体", 20, "bold"), command=dl1, bg="LightGrey", fg="black")
                b11.pack(ipadx=85, ipady=2)  # 登录模块
        else:
            tx = tk.Toplevel()
            tx.title("系统消息")
            tx.geometry("250x300")
            tk.Label(tx, text="验证码错误！请重试。", font=("黑体", 15, "bold"), fg="red", image=pic2,compound="top").pack()
            tx.resizable(False, False)
    zc2=tk.Button(zcy,text="注册",font=("黑体",20,"bold"),command=zc22,bg="LightGrey",fg="black",state="disabled")
    zc2.pack(ipadx=50,ipady=10, padx=10, pady=10)
b2=tk.Button(win,text="注册",font=("黑体",20,"bold"),command=zc,bg="LightGrey",fg="black")
b2.pack(ipadx=85,ipady=2,padx=10,pady=20)
win.resizable(False,False)
win.mainloop()