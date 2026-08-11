import sys,socket,json,threading,base64,os,webbrowser
from PyQt6.QtCore import Qt,pyqtSignal,QSize,QUrl
from PyQt6.QtGui import QFont,QDesktopServices
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,
QPushButton,QLineEdit,QListWidget,QListWidgetItem,QDialog,QMessageBox,QTextEdit,QInputDialog,
QFrame,QScrollArea,QToolButton,QFileDialog,QDialogButtonBox,QCheckBox)

SERVER_IP="127.0.0.1"; SERVER_PORT=5555

STYLE="""
*{font-family:"Segoe UI";}
QMainWindow{background:#f6f7fb;}
QWidget#rail{background:#171827;}
QWidget#sidebar,QWidget#info{background:#fff;border-right:1px solid #e5e6ee;}
QWidget#chat{background:#f7f8fc;}
QLineEdit#search{background:#f0f1f7;border:0;border-radius:14px;padding:11px;color:#252638;}
QListWidget{background:#fff;border:0;outline:0;}
QListWidget::item{padding:8px;margin:2px 7px;border-radius:12px;}
QListWidget::item:selected{background:#eeefff;}
QFrame#topbar{background:#fff;border-bottom:1px solid #e5e6ee;}
QLabel#title{font-size:18px;font-weight:700;color:#171827;}
QLabel#sub{font-size:12px;color:#85889a;}
QFrame#composer{background:#fff;border:1px solid #e0e1e9;border-radius:18px;}
QLineEdit#input{background:transparent;border:0;padding:12px;font-size:14px;}
QToolButton#icon{background:transparent;border:0;color:#6f7183;font-size:19px;border-radius:10px;}
QToolButton#icon:hover{background:#f0f1f7;}
QPushButton#send{background:#6557e8;color:white;border:0;border-radius:13px;min-width:43px;min-height:43px;}
QPushButton#primary{background:#6557e8;color:white;border:0;border-radius:12px;padding:11px;}
QPushButton#secondary{background:#f0f1f7;color:#303245;border:0;border-radius:12px;padding:11px;}
QPushButton#profile{background:#f0f1f7;border:0;border-radius:12px;padding:10px;text-align:left;}
QLabel#in{background:#fff;color:#252638;border-radius:15px;padding:10px 13px;}
QLabel#out{background:#6557e8;color:#fff;border-radius:15px;padding:10px 13px;}
"""

class Avatar(QLabel):
    def __init__(self,text,size=44):
        super().__init__(text[:1].upper() if text else "D"); self.setFixedSize(size,size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"background:#6557e8;color:white;border-radius:{size//2}px;font-weight:700;font-size:{max(12,size//3)}px;")

class Auth(QDialog):
    def __init__(self,s):
        super().__init__(); self.s=s; self.result=None; self.setWindowTitle("DanChat"); self.setFixedSize(430,480); self.setStyleSheet(STYLE)
        l=QVBoxLayout(self); l.setContentsMargins(42,30,42,30); l.setSpacing(12)
        a=Avatar("D",82); a.setStyleSheet("background:#6557e8;color:white;border-radius:41px;font-size:32px;font-weight:800;"); l.addWidget(a,0,Qt.AlignmentFlag.AlignHCenter)
        x=QLabel("DanChat"); x.setStyleSheet("font-size:30px;font-weight:800;color:#171827"); x.setAlignment(Qt.AlignmentFlag.AlignCenter); l.addWidget(x)
        self.e=QLineEdit(); self.e.setObjectName("search"); self.e.setPlaceholderText("Email"); l.addWidget(self.e)
        self.p=QLineEdit(); self.p.setObjectName("search"); self.p.setPlaceholderText("Пароль"); self.p.setEchoMode(QLineEdit.EchoMode.Password); l.addWidget(self.p)
        b=QPushButton("Войти"); b.setObjectName("primary"); b.clicked.connect(self.login); l.addWidget(b)
        b=QPushButton("Создать аккаунт"); b.setObjectName("secondary"); b.clicked.connect(self.reg); l.addWidget(b)
        hint=QLabel("Без SMS и без подтверждения email."); hint.setStyleSheet("color:#999bab;font-size:11px;"); l.addWidget(hint)
    def send(self,o): self.s.sendall((json.dumps(o,ensure_ascii=False)+"\n").encode())
    def recv(self):
        data=self.s.recv(65536)
        if not data:
            raise ConnectionError("Сервер закрыл соединение")
        line=data.decode("utf-8",errors="replace").splitlines()[0]
        return json.loads(line)
    def reg(self):
        try:
            self.send({"type":"register","email":self.e.text(),"password":self.p.text()}); d=self.recv()
            QMessageBox.information(self,"DanChat",d.get("text","")) if d.get("type")=="register_ok" else QMessageBox.warning(self,"Ошибка",d.get("text",""))
        except Exception as e:
            QMessageBox.critical(self,"Ошибка соединения","Сервер закрыл соединение.\n\nЗапусти server.py заново.\n\n"+str(e))
    def login(self):
        try:
            self.send({"type":"login","email":self.e.text(),"password":self.p.text()}); d=self.recv()
            if d.get("type")=="login_ok": self.result=d; self.accept()
            else: QMessageBox.warning(self,"Ошибка",d.get("text","Ошибка"))
        except Exception as e:
            QMessageBox.critical(self,"Ошибка соединения","Сервер закрыл соединение.\n\nПроверь окно server.py.\n\n"+str(e))

class UserRow(QWidget):
    def __init__(self,u):
        super().__init__(); l=QHBoxLayout(self); l.setContentsMargins(5,3,5,3)
        l.addWidget(Avatar(u["email"],43)); b=QVBoxLayout(); b.setSpacing(1)
        n=QLabel(u["email"].split("@")[0]); n.setStyleSheet("font-weight:700;color:#26283a")
        st=QLabel("● онлайн" if u["online"] else (u["status"] or "был недавно")); st.setStyleSheet("font-size:11px;color:#8a8da0")
        b.addWidget(n); b.addWidget(st); l.addLayout(b); l.addStretch()

class Bubble(QWidget):
    def __init__(self,text,out,filename=None,download=None):
        super().__init__(); row=QHBoxLayout(self); row.setContentsMargins(8,3,8,3)
        box=QVBoxLayout(); lab=QLabel(text); lab.setWordWrap(True); lab.setMaximumWidth(570); lab.setObjectName("out" if out else "in"); box.addWidget(lab)
        if filename and download:
            b=QPushButton("📎  "+filename); b.setObjectName("secondary"); b.clicked.connect(download); box.addWidget(b)
        if out: row.addStretch(); row.addLayout(box)
        else: row.addLayout(box); row.addStretch()

class Main(QMainWindow):
    incoming=pyqtSignal(dict)
    def __init__(self,s,d):
        super().__init__(); self.s=s; self.me=d["email"]; self.users=d["users"]; self.current=None
        self.setWindowTitle("DanChat"); self.resize(1450,850); self.setMinimumSize(1100,680); self.setStyleSheet(STYLE); self.incoming.connect(self.handle)
        self.build()
        threading.Thread(target=self.reader,daemon=True).start()
    def send(self,o):
        try:self.s.sendall((json.dumps(o,ensure_ascii=False)+"\n").encode())
        except:pass
    def reader(self):
        for line in self.s.makefile("r",encoding="utf-8"):
            try:
                self.incoming.emit(json.loads(line))
            except Exception as e:
                print("Packet error:",e)

    def build(self):
        root=QWidget(); self.setCentralWidget(root); main=QHBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)
        rail=QWidget(); rail.setObjectName("rail"); rail.setFixedWidth(78); r=QVBoxLayout(rail); r.setContentsMargins(10,18,10,18)
        a=Avatar("D",48); a.setStyleSheet("background:#6557e8;color:#fff;border-radius:24px;font-size:21px;font-weight:800"); r.addWidget(a,0,Qt.AlignmentFlag.AlignHCenter)
        self.rail_buttons=[]
        for icon,tip,fn in [("💬","Чаты",self.show_chats),("👥","Контакты",self.contacts),("🔔","Уведомления",self.notifications),("📁","Файлы",self.files)]:
            b=QToolButton(); b.setObjectName("icon"); b.setText(icon); b.setToolTip(tip); b.setFixedSize(50,50); b.clicked.connect(fn); r.addWidget(b); self.rail_buttons.append(b)
        r.addStretch(); b=QToolButton(); b.setObjectName("icon"); b.setText("⚙"); b.setToolTip("Настройки"); b.setFixedSize(50,50); b.clicked.connect(self.settings); r.addWidget(b)
        main.addWidget(rail)
        side=QWidget(); side.setObjectName("sidebar"); side.setFixedWidth(330); sl=QVBoxLayout(side); sl.setContentsMargins(16,18,16,12)
        h=QHBoxLayout(); t=QLabel("Сообщения"); t.setStyleSheet("font-size:24px;font-weight:800;color:#171827"); h.addWidget(t); h.addStretch()
        b=QToolButton(); b.setObjectName("icon"); b.setText("✎"); b.setToolTip("Новый чат"); b.clicked.connect(self.new_chat); h.addWidget(b); sl.addLayout(h)
        self.search=QLineEdit(); self.search.setObjectName("search"); self.search.setPlaceholderText("🔎  Поиск чатов"); self.search.textChanged.connect(self.refresh); sl.addWidget(self.search)
        sec=QLabel("Все чаты"); sec.setObjectName("section"); sl.addWidget(sec); self.list=QListWidget(); self.list.itemClicked.connect(self.open_chat); sl.addWidget(self.list)
        b=QPushButton("  👤  "+self.me); b.setObjectName("profile"); b.setToolTip("Изменить статус"); b.clicked.connect(self.change_status); sl.addWidget(b)
        main.addWidget(side)

        chat=QWidget(); chat.setObjectName("chat"); cl=QVBoxLayout(chat); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        top=QFrame(); top.setObjectName("topbar"); tb=QHBoxLayout(top); tb.setContentsMargins(18,10,18,10); tb.addWidget(Avatar("D",46))
        z=QVBoxLayout(); self.title=QLabel("Выберите чат"); self.title.setObjectName("title"); self.sub=QLabel("Нажмите на пользователя слева"); self.sub.setObjectName("sub"); z.addWidget(self.title); z.addWidget(self.sub); tb.addLayout(z); tb.addStretch()
        for icon,tip,fn in [("🔎","Поиск в чате",self.chat_search),("📞","Позвонить",self.call),("⋮","Меню",self.chat_menu)]:
            b=QToolButton(); b.setObjectName("icon"); b.setText(icon); b.setToolTip(tip); b.setFixedSize(42,42); b.clicked.connect(fn); tb.addWidget(b)
        cl.addWidget(top)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.Shape.NoFrame); self.msgw=QWidget(); self.msgl=QVBoxLayout(self.msgw); self.msgl.setContentsMargins(22,18,22,18); self.msgl.addStretch(); self.scroll.setWidget(self.msgw); cl.addWidget(self.scroll)
        cw=QWidget(); c=QHBoxLayout(cw); c.setContentsMargins(18,8,18,14); frame=QFrame(); frame.setObjectName("composer"); cc=QHBoxLayout(frame); cc.setContentsMargins(6,5,6,5)
        for icon,tip,fn in [("＋","Прикрепить файл",self.attach),("😊","Эмодзи",self.emoji)]:
            b=QToolButton(); b.setObjectName("icon"); b.setText(icon); b.setToolTip(tip); b.clicked.connect(fn); cc.addWidget(b)
        self.input=QLineEdit(); self.input.setObjectName("input"); self.input.setPlaceholderText("Напишите сообщение…"); self.input.returnPressed.connect(self.send_message); cc.addWidget(self.input)
        b=QPushButton("➤"); b.setObjectName("send"); b.clicked.connect(self.send_message); cc.addWidget(b); c.addWidget(frame); cl.addWidget(cw); main.addWidget(chat,1)

        info=QWidget(); info.setObjectName("info"); info.setFixedWidth(280); il=QVBoxLayout(info); il.setContentsMargins(20,25,20,20)
        sec=QLabel("Профиль"); sec.setObjectName("section"); il.addWidget(sec); self.ia=Avatar("D",90); il.addWidget(self.ia,0,Qt.AlignmentFlag.AlignHCenter)
        self.iname=QLabel("DanChat"); self.iname.setStyleSheet("font-size:19px;font-weight:800;color:#171827"); self.iname.setAlignment(Qt.AlignmentFlag.AlignCenter); il.addWidget(self.iname)
        self.ist=QLabel("Выберите чат"); self.ist.setStyleSheet("color:#85889a"); self.ist.setAlignment(Qt.AlignmentFlag.AlignCenter); il.addWidget(self.ist); il.addSpacing(15)
        for text,fn in [("🖼  Фото и видео",self.media),("📎  Файлы",self.files),("🔗  Ссылки",self.links),("🔔  Уведомления",self.toggle_notifications)]:
            b=QPushButton(text); b.setObjectName("secondary"); b.clicked.connect(fn); il.addWidget(b)
        il.addStretch(); main.addWidget(info); self.refresh()

    def show_chats(self):
        self.search.setFocus()
        self.refresh(self.search.text())

    def contacts(self):
        emails=[u["email"] for u in self.users if u["email"]!=self.me]
        QMessageBox.information(self,"Контакты","\\n".join(emails) if emails else "Пока нет других пользователей.")

    def notifications(self):
        QMessageBox.information(self,"Уведомления","🔔 Уведомления включены.")

    def files(self):
        QMessageBox.information(self,"Файлы","Файлы можно отправлять через кнопку 📎 в чате.")

    def refresh(self,q=""):
        self.list.clear()
        for u in self.users:
            if u["email"]==self.me or q.lower() not in u["email"].lower(): continue
            it=QListWidgetItem(); it.setSizeHint(QSize(290,63)); it.setData(Qt.ItemDataRole.UserRole,u["email"]); self.list.addItem(it); self.list.setItemWidget(it,UserRow(u))
    def open_chat(self,it):
        self.current=it.data(Qt.ItemDataRole.UserRole); u=next((x for x in self.users if x["email"]==self.current),None)
        self.title.setText(self.current.split("@")[0]); self.sub.setText("● онлайн" if u and u["online"] else (u["status"] if u else ""))
        self.iname.setText(self.current.split("@")[0]); self.ist.setText(self.current); self.send({"type":"history","with":self.current})
    def send_message(self):
        t=self.input.text().strip()
        if self.current and t:self.send({"type":"message","to":self.current,"text":t}); self.input.clear()
    def clear(self):
        while self.msgl.count():
            x=self.msgl.takeAt(0)
            if x.widget():x.widget().deleteLater()
        self.msgl.addStretch()
    def add(self,text,out,filename=None,data=None):
        self.msgl.takeAt(self.msgl.count()-1)
        def save():
            path,_=QFileDialog.getSaveFileName(self,"Сохранить файл",filename or "file")
            if path:
                try:open(path,"wb").write(base64.b64decode(data))
                except Exception as e:QMessageBox.warning(self,"Ошибка",str(e))
        self.msgl.addWidget(Bubble(text,out,filename,save if data else None)); self.msgl.addStretch(); QApplication.processEvents(); self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
    def handle(self,d):
        if d.get("type")=="users":
            self.users=d["users"]
            if hasattr(self,"search"):
                self.refresh(self.search.text())
        elif d.get("type")=="history":
            self.clear()
            for x in d["messages"]:
                self.add(x["text"] if x["kind"]=="text" else "📎 Файл",x["from"]==self.me,x.get("filename"),x.get("data"))
        elif d.get("type")=="message" and (d.get("from")==self.current or d.get("to")==self.current):
            self.add(d.get("text") if d.get("kind")=="text" else "📎 Файл",d["from"]==self.me,d.get("filename"),d.get("data"))
        elif d.get("type")=="error": QMessageBox.warning(self,"DanChat",d["text"])
    def attach(self):
        if not self.current:return QMessageBox.information(self,"DanChat","Сначала выбери чат.")
        path,_=QFileDialog.getOpenFileName(self,"Выберите файл")
        if not path:return
        if os.path.getsize(path)>5*1024*1024:return QMessageBox.warning(self,"DanChat","Для этой версии файл должен быть меньше 5 MB.")
        data=base64.b64encode(open(path,"rb").read()).decode()
        self.send({"type":"file","to":self.current,"filename":os.path.basename(path),"data":data})
    def emoji(self):
        x,ok=QInputDialog.getItem(self,"Эмодзи","Выбери:",["😀","😂","❤️","🔥","👍","😎","🎮","🚗","💀","😭"],False)
        if ok:self.input.insert(x)
    def change_status(self):
        x,ok=QInputDialog.getText(self,"Статус","Новый статус:")
        if ok:self.send({"type":"status","text":x})
    def new_chat(self):
        emails=[u["email"] for u in self.users if u["email"]!=self.me]
        if not emails:return QMessageBox.information(self,"DanChat","Пока нет других пользователей.")
        x,ok=QInputDialog.getItem(self,"Новый чат","Пользователь:",emails,0,False)
        if ok:
            it=QListWidgetItem(); it.setData(Qt.ItemDataRole.UserRole,x); self.open_chat(it)
    def settings(self):
        d=QDialog(self); d.setWindowTitle("Настройки"); d.setFixedSize(400,300); l=QVBoxLayout(d)
        head=QLabel("Настройки DanChat"); head.setStyleSheet("font-size:22px;font-weight:800"); l.addWidget(head)
        l.addWidget(QLabel("Аккаунт: "+self.me)); l.addWidget(QCheckBox("Уведомления"))
        l.addWidget(QCheckBox("Звуки сообщений")); l.addWidget(QCheckBox("Показывать онлайн-статус"))
        b=QPushButton("Готово"); b.setObjectName("primary"); b.clicked.connect(d.accept); l.addWidget(b); d.exec()
    def chat_search(self):
        if not self.current:return
        x,ok=QInputDialog.getText(self,"Поиск","Слово или фраза:")
        if ok and x:
            self.send({"type":"history","with":self.current}); QMessageBox.information(self,"Поиск","Поиск по загруженной истории: «"+x+"»")
    def call(self): QMessageBox.information(self,"Звонок","Кнопка звонка готова для подключения голосового сервера. В этой версии звонки не запускаются.")
    def chat_menu(self):
        x,ok=QInputDialog.getItem(self,"Меню чата","Действие:",["Очистить окно","Профиль","Отмена"],False)
        if ok and x=="Очистить окно":self.clear()
        elif ok and x=="Профиль":self.info_profile()
    def info_profile(self): QMessageBox.information(self,"Профиль",self.current or "Нет выбранного пользователя")
    def media(self): QMessageBox.information(self,"Фото и видео","В этой версии медиа можно отправлять через 📎 как файл.")
    def links(self): QMessageBox.information(self,"Ссылки","Ссылки из истории пока показываются как обычный текст.")
    def toggle_notifications(self): QMessageBox.information(self,"Уведомления","Уведомления для этого чата включены.")

def main():
    app=QApplication(sys.argv); s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:s.connect((SERVER_IP,SERVER_PORT))
    except Exception as e:QMessageBox.critical(None,"DanChat","Сервер недоступен:\n"+str(e));return
    s.recv(1024); a=Auth(s)
    if a.exec()!=QDialog.DialogCode.Accepted:return
    try:
        w=Main(s,a.result)
        w.show()
        sys.exit(app.exec())
    except Exception:
        import traceback
        err=traceback.format_exc()
        print(err)
        QMessageBox.critical(None,"DanChat — ошибка запуска",err)
        return
if __name__=="__main__":main()
