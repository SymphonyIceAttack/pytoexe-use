# 积分管理系统 - 儿童友好版
import sys, json, os, datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ---------- 数据管理 ----------
class Data:
    def __init__(self):
        self.f = "points_data.json"
        self.d = {"points":0, "records":[], "parents":{"妈妈":"0000","爸爸":"0000","爷爷":"0000","奶奶":"0000","贝爷":"0000","婆婆":"0000"}, "goals":[]}
        if os.path.exists(self.f):
            try: self.d = json.load(open(self.f,"r",encoding="utf-8"))
            except: pass
    def save(self):
        json.dump(self.d, open(self.f,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    def get_points(self): return self.d["points"]
    def set_points(self,v): self.d["points"]=v; self.save()
    def add_record(self,who,reason,change):
        t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.d["records"].insert(0, {"time":t,"who":who,"reason":reason,"change":change,"balance":self.d["points"]})
        if len(self.d["records"])>1000: self.d["records"]=self.d["records"][:1000]
        self.save()
    def get_records(self,n=5): return self.d["records"][:n]
    def all_records(self): return self.d["records"]
    def delete_record(self,index):
        if 0<=index<len(self.d["records"]):
            del self.d["records"][index]; self.save()
    def check_password(self,name,pwd):
        return self.d["parents"].get(name) == pwd
    def change_password(self,name,old,new):
        if self.check_password(name,old):
            self.d["parents"][name]=new; self.save(); return True
        return False
    def get_goals(self): return self.d["goals"]
    def add_goal(self,desc,pts):
        self.d["goals"].append({"desc":desc,"points":pts}); self.save()
    def remove_goal(self,i):
        if 0<=i<len(self.d["goals"]): del self.d["goals"][i]; self.save()

# ---------- 启动窗口 ----------
class Splash(QWidget):
    def __init__(self,go):
        super().__init__()
        self.go=go
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420,280)
        c=QWidget(self); c.setGeometry(0,0,420,280)
        c.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FFF9C4,stop:1 #FFD54F);border-radius:24px;border:2px solid #FFB300")
        l=QVBoxLayout(c); l.setContentsMargins(30,30,30,30)
        t=QLabel("积分管理系统"); t.setStyleSheet("font-size:36px;font-weight:bold;color:#8B4513;background:transparent")
        t.setAlignment(Qt.AlignCenter); l.addWidget(t)
        b=QPushButton("✨ 点击进入 ✨"); b.setFixedSize(200,50)
        b.setStyleSheet("QPushButton{background:#FFD700;border:2px solid #DAA520;border-radius:25px;color:#5D4037;font-size:20px;font-weight:bold}QPushButton:hover{background:#FFE082}")
        b.clicked.connect(self.enter)
        l.addWidget(b,alignment=Qt.AlignCenter)
        l.addStretch()
        sh=QGraphicsDropShadowEffect(); sh.setBlurRadius(40); sh.setColor(QColor(0,0,0,150)); self.setGraphicsEffect(sh)
        scr=QApplication.primaryScreen().geometry()
        self.move((scr.width()-420)//2,(scr.height()-280)//2)
        QTimer.singleShot(5000,self.enter)
    def enter(self): self.close(); self.go()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        for x,y in [(100,50),(280,80),(170,170),(360,190)]:
            r=16; g=QRadialGradient(x,y,r,x-4,y-4)
            g.setColorAt(0,QColor("#FFF8DC"));g.setColorAt(0.5,QColor("#FFD700"));g.setColorAt(1,QColor("#DAA520"))
            p.setBrush(QBrush(g));p.setPen(QPen(QColor("#B8860B"),1))
            p.drawEllipse(QPoint(x,y),r,r)
        p.end()

# ---------- 主窗口（贝贝界面）----------
class MainWindow(QMainWindow):
    def __init__(self,data):
        super().__init__()
        self.data=data
        self.points=data.get_points()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        self.setStyleSheet("QMainWindow{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1a1a2e,stop:1 #16213e)}QLabel{background:transparent;color:white}QPushButton{background:rgba(255,255,255,0.06);border:1px solid rgba(255,215,0,0.2);border-radius:18px;color:#FFD700;font-size:16px;padding:8px 20px}QPushButton:hover{background:rgba(255,215,0,0.12)}")
        self.build_ui()
        self.update_display()

    def build_ui(self):
        w=QWidget(); self.setCentralWidget(w)
        l=QVBoxLayout(w); l.setContentsMargins(40,20,40,30)
        # 顶栏（问号 + 叉）
        top=QWidget(); top.setFixedHeight(50)
        tl=QHBoxLayout(top); tl.setContentsMargins(0,0,0,0)
        help_btn=QPushButton("?"); help_btn.setFixedSize(40,40)
        help_btn.setStyleSheet("QPushButton{background:rgba(255,215,0,0.08);border:1px solid rgba(255,215,0,0.2);border-radius:20px;color:#FFD700;font-size:22px;font-weight:bold}QPushButton:hover{background:rgba(255,215,0,0.2)}")
        help_btn.clicked.connect(self.show_help)
        tl.addWidget(help_btn)
        tl.addStretch()
        close_btn=QPushButton("✕"); close_btn.setFixedSize(40,40)
        close_btn.setStyleSheet("QPushButton{background:rgba(255,80,80,0.1);border:1px solid rgba(255,80,80,0.2);border-radius:20px;color:#FF8A8A;font-size:20px}QPushButton:hover{background:rgba(255,80,80,0.2)}")
        close_btn.clicked.connect(self.confirm_exit)
        tl.addWidget(close_btn)
        l.addWidget(top)
        # 中央内容
        center=QWidget()
        cl=QVBoxLayout(center); cl.setAlignment(Qt.AlignCenter)
        cl.setSpacing(15)
        # 头像（圆形，显示“贝”字）
        avatar=QLabel("贝")
        avatar.setFixedSize(100,100)
        avatar.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #FFD700,stop:1 #FFA500);border-radius:50px;color:#5D4037;font-size:48px;font-weight:bold")
        avatar.setAlignment(Qt.AlignCenter)
        cl.addWidget(avatar,alignment=Qt.AlignCenter)
        # 名字
        name=QLabel("贝贝")
        name.setStyleSheet("font-size:28px;font-weight:bold;color:#FFD700;background:transparent")
        name.setAlignment(Qt.AlignCenter)
        cl.addWidget(name)
        # 积分
        self.points_label=QLabel("0")
        self.points_label.setStyleSheet("font-size:72px;font-weight:bold;color:#FFD700;background:transparent")
        self.points_label.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.points_label)
        unit=QLabel("分")
        unit.setStyleSheet("font-size:20px;color:#BBB;background:transparent")
        unit.setAlignment(Qt.AlignCenter)
        cl.addWidget(unit)
        # 三个按钮（居中）
        btn_w=QWidget()
        btn_l=QVBoxLayout(btn_w); btn_l.setSpacing(12); btn_l.setAlignment(Qt.AlignCenter)
        hist_btn=QPushButton("📋 历史记录"); hist_btn.setFixedSize(240,50)
        hist_btn.clicked.connect(self.show_history)
        btn_l.addWidget(hist_btn,alignment=Qt.AlignCenter)
        goal_btn=QPushButton("🎯 目标"); goal_btn.setFixedSize(240,50)
        goal_btn.clicked.connect(self.show_goals)
        btn_l.addWidget(goal_btn,alignment=Qt.AlignCenter)
        parent_btn=QPushButton("👪 登录家长账号"); parent_btn.setFixedSize(240,50)
        parent_btn.clicked.connect(self.login_parent)
        btn_l.addWidget(parent_btn,alignment=Qt.AlignCenter)
        cl.addWidget(btn_w,alignment=Qt.AlignCenter)
        l.addWidget(center,1)

    def show_help(self):
        QMessageBox.information(self,"帮助","欢迎使用积分管理系统！\n\n• 点击「历史记录」查看积分变动\n• 点击「目标」查看奖励规则\n• 点击「登录家长账号」由家长管理积分\n• 右上角✕退出程序\n\n家长初始密码：0000")

    def confirm_exit(self):
        reply=QMessageBox.question(self,"确认","确定要退出吗？",QMessageBox.Yes|QMessageBox.No)
        if reply==QMessageBox.Yes: QApplication.quit()

    def login_parent(self):
        # 选择家长
        names=list(self.data.d["parents"].keys())
        name,ok=QInputDialog.getItem(self,"选择家长","请选择您的角色：",names,0,False)
        if not ok: return
        # 输入密码
        pwd,ok=QInputDialog.getText(self,"密码验证","请输入密码：",echo=QLineEdit.Password)
        if not ok: return
        if self.data.check_password(name,pwd):
            self.parent_window=ParentWindow(self.data,name,self)
            self.parent_window.show()
            self.hide()
        else:
            QMessageBox.warning(self,"错误","密码错误！")

    def show_history(self):
        records=self.data.all_records()
        if not records:
            QMessageBox.information(self,"历史记录","暂无记录")
            return
        d=QDialog(self); d.setWindowTitle("历史记录"); d.resize(600,500)
        d.setStyleSheet("QDialog{background:#1a1a2e}QListWidget{background:rgba(0,0,0,0.3);border:1px solid rgba(255,215,0,0.1);border-radius:12px;color:#CCC;font-size:13px}")
        l=QVBoxLayout(d)
        list_w=QListWidget()
        for i,r in enumerate(records):
            who=r["who"]; reason=r["reason"]; change=r["change"]; bal=r["balance"]; t=r["time"]
            sign="+" if change>0 else ""
            item=QListWidgetItem(f"[{t}] {who}: {sign}{change} ({reason}) → 余额:{bal}")
            item.setForeground(QColor("#7ECF7E" if change>0 else "#FF8A8A"))
            item.setData(Qt.UserRole,i)
            list_w.addItem(item)
        l.addWidget(list_w)
        # 删除按钮
        btn_layout=QHBoxLayout()
        del_btn=QPushButton("删除选中记录")
        del_btn.clicked.connect(lambda: self.delete_selected(list_w,d))
        btn_layout.addWidget(del_btn)
        close_btn=QPushButton("关闭"); close_btn.clicked.connect(d.close)
        btn_layout.addWidget(close_btn)
        l.addLayout(btn_layout)
        d.exec_()

    def delete_selected(self,list_w,dialog):
        item=list_w.currentItem()
        if item is None:
            QMessageBox.warning(self,"提示","请先选中一条记录")
            return
        idx=item.data(Qt.UserRole)
        reply=QMessageBox.question(self,"确认","确定要删除这条记录吗？",QMessageBox.Yes|QMessageBox.No)
        if reply==QMessageBox.Yes:
            self.data.delete_record(idx)
            dialog.close()
            self.show_history()  # 刷新

    def show_goals(self):
        goals=self.data.get_goals()
        if not goals:
            QMessageBox.information(self,"目标","暂无目标，请联系家长设置")
            return
        text="🎯 目标列表：\n\n"
        for g in goals:
            text+=f"• {g['desc']}  ➜  +{g['points']}分\n"
        QMessageBox.information(self,"目标",text)

    def update_display(self):
        self.points_label.setText(str(self.points))

# ---------- 家长窗口 ----------
class ParentWindow(QMainWindow):
    def __init__(self,data,parent_name,main_win):
        super().__init__()
        self.data=data
        self.parent_name=parent_name
        self.main_win=main_win
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        self.setStyleSheet("QMainWindow{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1a1a2e,stop:1 #16213e)}QLabel{background:transparent;color:white}QPushButton{background:rgba(255,255,255,0.06);border:1px solid rgba(255,215,0,0.2);border-radius:18px;color:#FFD700;font-size:16px;padding:8px 20px}QPushButton:hover{background:rgba(255,215,0,0.12)}")
        self.build_ui()

    def build_ui(self):
        w=QWidget(); self.setCentralWidget(w)
        l=QVBoxLayout(w); l.setContentsMargins(40,20,40,30)
        # 顶栏
        top=QWidget(); top.setFixedHeight(50)
        tl=QHBoxLayout(top); tl.setContentsMargins(0,0,0,0)
        help_btn=QPushButton("?"); help_btn.setFixedSize(40,40)
        help_btn.setStyleSheet("QPushButton{background:rgba(255,215,0,0.08);border:1px solid rgba(255,215,0,0.2);border-radius:20px;color:#FFD700;font-size:22px;font-weight:bold}QPushButton:hover{background:rgba(255,215,0,0.2)}")
        help_btn.clicked.connect(lambda: QMessageBox.information(self,"帮助","家长功能：\n• 加/减积分（需输入原因）\n• 兑换礼物\n• 设置目标\n• 修改密码\n\n右上角✕可选择退出或返回贝贝界面"))
        tl.addWidget(help_btn)
        tl.addStretch()
        close_btn=QPushButton("✕"); close_btn.setFixedSize(40,40)
        close_btn.setStyleSheet("QPushButton{background:rgba(255,80,80,0.1);border:1px solid rgba(255,80,80,0.2);border-radius:20px;color:#FF8A8A;font-size:20px}QPushButton:hover{background:rgba(255,80,80,0.2)}")
        close_btn.clicked.connect(self.confirm_exit_or_back)
        tl.addWidget(close_btn)
        l.addWidget(top)
        # 标题
        title=QLabel(f"家长：{self.parent_name}")
        title.setStyleSheet("font-size:24px;font-weight:bold;color:#FFD700;background:transparent")
        title.setAlignment(Qt.AlignCenter)
        l.addWidget(title)
        l.addSpacing(20)
        # 五个功能按钮
        btn_w=QWidget()
        btn_l=QVBoxLayout(btn_w); btn_l.setSpacing(15); btn_l.setAlignment(Qt.AlignCenter)
        add_btn=QPushButton("➕ 加积分"); add_btn.setFixedSize(260,55)
        add_btn.clicked.connect(lambda: self.change_points(1))
        btn_l.addWidget(add_btn,alignment=Qt.AlignCenter)
        sub_btn=QPushButton("➖ 减积分"); sub_btn.setFixedSize(260,55)
        sub_btn.clicked.connect(lambda: self.change_points(-1))
        btn_l.addWidget(sub_btn,alignment=Qt.AlignCenter)
        gift_btn=QPushButton("🎁 兑换礼物"); gift_btn.setFixedSize(260,55)
        gift_btn.clicked.connect(self.exchange_gift)
        btn_l.addWidget(gift_btn,alignment=Qt.AlignCenter)
        goal_btn=QPushButton("🎯 设置目标"); goal_btn.setFixedSize(260,55)
        goal_btn.clicked.connect(self.set_goal)
        btn_l.addWidget(goal_btn,alignment=Qt.AlignCenter)
        pwd_btn=QPushButton("🔑 修改密码"); pwd_btn.setFixedSize(260,55)
        pwd_btn.clicked.connect(self.change_pwd)
        btn_l.addWidget(pwd_btn,alignment=Qt.AlignCenter)
        l.addWidget(btn_w,alignment=Qt.AlignCenter)
        l.addStretch()

    def confirm_exit_or_back(self):
        reply=QMessageBox.question(self,"选择","您要做什么？",QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel,text1="退出软件",text2="返回贝贝界面",text3="取消")
        if reply==QMessageBox.Yes:
            QApplication.quit()
        elif reply==QMessageBox.No:
            self.close()
            self.main_win.show()

    def change_points(self,direction):
        # 输入原因
        reason,ok=QInputDialog.getText(self,"原因","请输入加/减分的原因：")
        if not ok or not reason.strip(): return
        # 输入分数
        pts,ok=QInputDialog.getInt(self,"分数","请输入分数（正数）：",value=10,min=1,max=99999)
        if not ok: return
        # 再次验证密码
        pwd,ok=QInputDialog.getText(self,"安全验证","请再次输入密码以确认：",echo=QLineEdit.Password)
        if not ok: return
        if not self.data.check_password(self.parent_name,pwd):
            QMessageBox.warning(self,"错误","密码错误，操作取消")
            return
        # 执行
        change=pts*direction
        new_points=self.data.get_points()+change
        if new_points<0:
            QMessageBox.warning(self,"错误","积分不足，无法扣除")
            return
        self.data.set_points(new_points)
        self.data.add_record(self.parent_name,reason.strip(),change)
        self.main_win.points=new_points
        self.main_win.update_display()
        QMessageBox.information(self,"成功",f"操作成功！当前积分：{new_points}")

    def exchange_gift(self):
        # 兑换礼物（消耗积分）
        gifts={"小玩具":20,"冰淇淋":10,"书":30,"游戏时间":15,"零食":5}
        gift_names=list(gifts.keys())
        gift,ok=QInputDialog.getItem(self,"兑换礼物","请选择要兑换的礼物：",gift_names,0,False)
        if not ok: return
        cost=gifts[gift]
        current=self.data.get_points()
        if current<cost:
            QMessageBox.warning(self,"积分不足",f"需要{cost}分，当前只有{current}分")
            return
        # 确认密码
        pwd,ok=QInputDialog.getText(self,"安全验证","请再次输入密码：",echo=QLineEdit.Password)
        if not ok: return
        if not self.data.check_password(self.parent_name,pwd):
            QMessageBox.warning(self,"错误","密码错误")
            return
        new_points=current-cost
        self.data.set_points(new_points)
        self.data.add_record(self.parent_name,f"兑换{gift}",-cost)
        self.main_win.points=new_points
        self.main_win.update_display()
        QMessageBox.information(self,"成功",f"兑换成功！消耗{cost}分，剩余{new_points}分")

    def set_goal(self):
        desc,ok=QInputDialog.getText(self,"目标描述","请输入目标内容：")
        if not ok or not desc.strip(): return
        pts,ok=QInputDialog.getInt(self,"奖励积分","完成该目标可获得多少积分？",value=10,min=1,max=99999)
        if not ok: return
        self.data.add_goal(desc.strip(),pts)
        QMessageBox.information(self,"成功","目标已添加！")

    def change_pwd(self):
        old,ok=QInputDialog.getText(self,"旧密码","请输入当前密码：",echo=QLineEdit.Password)
        if not ok: return
        new1,ok=QInputDialog.getText(self,"新密码","请输入新密码：",echo=QLineEdit.Password)
        if not ok: return
        new2,ok=QInputDialog.getText(self,"确认新密码","请再次输入新密码：",echo=QLineEdit.Password)
        if not ok: return
        if new1!=new2:
            QMessageBox.warning(self,"错误","两次输入不一致")
            return
        if self.data.change_password(self.parent_name,old,new1):
            QMessageBox.information(self,"成功","密码已修改！")
        else:
            QMessageBox.warning(self,"错误","原密码错误")

# ---------- 启动 ----------
app=QApplication(sys.argv)
data=Data()
def run(): m=MainWindow(data); m.show()
s=Splash(run); s.show()
sys.exit(app.exec_())
