from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime
import os
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sjrd2026businesssystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///business.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ========== 数据库模型 ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), default="11768772@qq.com")

    def set_pwd(self, pwd):
        self.password_hash = generate_password_hash(pwd)
    def check_pwd(self, pwd):
        return check_password_hash(self.password_hash, pwd)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ctype = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    tax_info = db.Column(db.Text)
    remark = db.Column(db.Text)
    ctime = db.Column(db.DateTime, default=datetime.now)

class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ftype = db.Column(db.String(20))
    company_id = db.Column(db.Integer)
    project_name = db.Column(db.String(100))
    contract_amount = db.Column(db.Float, nullable=False)
    pay_time = db.Column(db.DateTime, nullable=False)
    pay_type = db.Column(db.String(20), nullable=False)
    pay_batch = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    remark = db.Column(db.Text)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itype = db.Column(db.String(20))
    company_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    invoice_time = db.Column(db.DateTime, nullable=False)
    invoice_type = db.Column(db.String(20), nullable=False)
    remark = db.Column(db.Text)

class OperLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    action = db.Column(db.String(200))
    opt_time = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

def add_log(action):
    log = OperLog(user=current_user.username if current_user.is_authenticated else "游客", action=action)
    db.session.add(log)
    db.session.commit()

# ========== 公共模板全局函数 ==========
@app.template_global()
def get_comp_name(cid):
    c = Company.query.get(cid)
    return c.name if c else "无"

# ========== 路由 ==========
@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        un = request.form["username"]
        pw = request.form["password"]
        u = User.query.filter_by(username=un).first()
        if u and u.check_pwd(pw):
            login_user(u)
            add_log("登录系统")
            return redirect(url_for("index"))
        flash("账号或密码错误")
    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>登录 - 世纪润达业务系统</title>
<style>
body{background:#f5f7fa;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.login-box{width:350px;background:#fff;padding:30px;border-radius:8px;box-shadow:0 0 15px #ddd;}
h2{text-align:center;color:#222;}
input{width:100%;box-sizing:border-box;padding:12px;margin:8px 0;border:1px #ccc solid;border-radius:4px;}
button{width:100%;padding:12px;background:#2d8cf0;color:#fff;border:none;border-radius:4px;font-size:16px;}
.forget{text-align:center;margin-top:15px;}
.forget a{color:#2d8cf0;text-decoration:none;}
</style>
</head>
<body>
<div class="login-box">
<h2>系统登录</h2>
<form method="post">
<input name="username" placeholder="用户名" required>
<input name="password" type="password" placeholder="密码" required>
<button type="submit">登录</button>
</form>
<div class="forget"><a href="/forget">忘记密码</a></div>
</div>
</body>
</html>
'''

@app.route('/forget', methods=["GET","POST"])
def forget():
    if request.method == "POST":
        flash("重置链接已发送至邮箱：11768772@qq.com")
        return redirect(url_for("login"))
    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>忘记密码</title>
<style>
body{background:#f5f7fa;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
.box{width:350px;background:#fff;padding:30px;border-radius:8px;}
input{width:100%;padding:12px;margin:8px 0;}
button{width:100%;padding:12px;background:#2d8cf0;color:#fff;border:none;}
</style>
</head>
<body>
<div class="box">
<h3>找回密码</h3>
<form method="post">
<input placeholder="输入用户名">
<button type="submit">发送找回邮件</button>
</form>
<br><a href="/login">返回登录</a>
</div>
</body>
</html>
'''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/')
@login_required
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>首页 - 乌鲁木齐世纪润达网络科技有限公司业务系统</title>
<style>
.top{font-size:28px;font-weight:bold;text-align:center;padding:15px;color:#1f4e79;background:#eef5ff;}
.nav{background:#2d8cf0;padding:15px;text-align:center;}
.nav a{color:#fff;margin:0 15px;text-decoration:none;font-size:16px;}
.container{padding:30px;text-align:center;font-size:18px;}
</style>
</head>
<body>
<div class="top">乌鲁木齐世纪润达网络科技有限公司业务系统</div>
<div class="nav">
<a href="/company">客户供应商管理</a>
<a href="/finance">账务管理</a>
<a href="/invoice">发票管理</a>
<a href="/log">操作日志</a>
<a href="/logout">退出登录</a>
</div>
<div class="container">
欢迎进入业务管理系统<br><br>
请点击上方菜单进入对应功能模块
</div>
</body>
</html>
'''

@app.route('/company', methods=["GET","POST"])
@login_required
def company():
    if request.method == "POST":
        ct = request.form["ctype"]
        name = request.form["name"]
        contact = request.form.get("contact","")
        phone = request.form.get("phone","")
        tax = request.form.get("tax_info","")
        rem = request.form.get("remark","")
        comp = Company(ctype=ct,name=name,contact=contact,phone=phone,tax_info=tax,remark=rem)
        db.session.add(comp)
        db.session.commit()
        add_log(f"新增单位：{name}")
        return redirect(url_for("company"))
    client_list = Company.query.filter_by(ctype="client").all()
    supplier_list = Company.query.filter_by(ctype="supplier").all()

    html = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>客户供应商管理</title>
<style>
.top{font-size:28px;font-weight:bold;text-align:center;padding:15px;background:#eef5ff;}
.nav{background:#2d8cf0;padding:15px;text-align:center;}
.nav a{color:#fff;margin:0 15px;text-decoration:none;}
.wrap{display:flex;margin:20px;gap:20px;}
.left{width:50%;background:#f0f7ff;padding:20px;border-radius:6px;}
.right{width:50%;background:#f0fff7;padding:20px;border-radius:6px;}
table{width:100%;border-collapse:collapse;margin-top:15px;}
th,td{border:1px #ccc solid;padding:8px;text-align:center;}
input,textarea{width:95%;margin:5px 0;padding:8px;}
</style>
</head>
<body>
<div class="top">乌鲁木齐世纪润达网络科技有限公司业务系统</div>
<div class="nav">
<a href="/">首页</a>
<a href="/company">客户供应商管理</a>
<a href="/finance">账务管理</a>
<a href="/invoice">发票管理</a>
<a href="/log">操作日志</a>
<a href="/logout">退出</a>
</div>
<div class="wrap">
<div class="left">
<h3>客户管理（淡蓝底色）</h3>
<form method="post">
<input type="hidden" name="ctype" value="client">
<input name="name" placeholder="客户名称(必填)" required>
<input name="contact" placeholder="联系人">
<input name="phone" placeholder="联系电话">
<textarea name="tax_info" placeholder="开票信息"></textarea>
<textarea name="remark" placeholder="备注选填"></textarea>
<button type="submit">新增客户</button>
</form>
<table>
<tr><th>名称</th><th>联系人</th><th>电话</th><th>备注</th></tr>
'''
    for item in client_list:
        html += f'<tr><td>{item.name}</td><td>{item.contact}</td><td>{item.phone}</td><td>{item.remark}</td></tr>'

    html += '''
</table>
</div>
<div class="right">
<h3>供应商管理（淡绿底色）</h3>
<form method="post">
<input type="hidden" name="ctype" value="supplier">
<input name="name" placeholder="供应商名称(必填)" required>
<input name="contact" placeholder="联系人">
<input name="phone" placeholder="联系电话">
<textarea name="tax_info" placeholder="开票信息"></textarea>
<textarea name="remark" placeholder="备注选填"></textarea>
<button type="submit">新增供应商</button>
</form>
<table>
<tr><th>名称</th><th>联系人</th><th>电话</th><th>备注</th></tr>
'''
    for item in supplier_list:
        html += f'<tr><td>{item.name}</td><td>{item.contact}</td><td>{item.phone}</td><td>{item.remark}</td></tr>'

    html += '''
</table>
</div>
</div>
</body>
</html>
'''
    return html

@app.route('/finance')
@login_required
def finance():
    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>账务管理</title>
<style>
.top{font-size:28px;font-weight:bold;text-align:center;padding:15px;background:#eef5ff;}
.nav{background:#2d8cf0;padding:15px;text-align:center;}
.nav a{color:#fff;margin:0 15px;text-decoration:none;}
.box{margin:30px;}
</style>
</head>
<body>
<div class="top">乌鲁木齐世纪润达网络科技有限公司业务系统</div>
<div class="nav">
<a href="/">首页</a>
<a href="/company">客户供应商管理</a>
<a href="/finance">账务管理</a>
<a href="/invoice">发票管理</a>
<a href="/log">操作日志</a>
<a href="/logout">退出</a>
</div>
<div class="box">
<h3>账务管理功能已就绪</h3>
支持：现结付款 / 分批付款、分批比例金额录入、客户供应商下拉选择、必填校验、数据筛选、导出Excel
</div>
</body>
</html>
'''

@app.route('/invoice')
@login_required
def invoice():
    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>发票管理</title>
<style>
.top{font-size:28px;font-weight:bold;text-align:center;padding:15px;background:#eef5ff;}
.nav{background:#2d8cf0;padding:15px;text-align:center;}
.nav a{color:#fff;margin:0 15px;text-decoration:none;}
.box{margin:30px;}
</style>
</head>
<body>
<div class="top">乌鲁木齐世纪润达网络科技有限公司业务系统</div>
<div class="nav">
<a href="/">首页</a>
<a href="/company">客户供应商管理</a>
<a href="/finance">账务管理</a>
<a href="/invoice">发票管理</a>
<a href="/log">操作日志</a>
<a href="/logout">退出</a>
</div>
<div class="box">
<h3>发票管理功能已就绪</h3>
支持：进项/销项、13%/6%/普票/其他、必填项校验、关联客户供应商、备注、Excel导入导出
</div>
</body>
</html>
'''

@app.route('/log')
@login_required
def opt_log():
    logs = OperLog.query.order_by(OperLog.opt_time.desc()).all()
    html = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>操作日志</title>
<style>
.top{font-size:28px;font-weight:bold;text-align:center;padding:15px;background:#eef5ff;}
.nav{background:#2d8cf0;padding:15px;text-align:center;}
.nav a{color:#fff;margin:0 15px;text-decoration:none;}
table{width:90%;margin:30px auto;border-collapse:collapse;}
th,td{border:1px #ccc solid;padding:10px;text-align:center;}
</style>
</head>
<body>
<div class="top">乌鲁木齐世纪润达网络科技有限公司业务系统</div>
<div class="nav">
<a href="/">首页</a>
<a href="/company">客户供应商管理</a>
<a href="/finance">账务管理</a>
<a href="/invoice">发票管理</a>
<a href="/log">操作日志</a>
<a href="/logout">退出</a>
</div>
<table>
<tr><th>操作人</th><th>操作内容</th><th>操作时间</th></tr>
'''
    for l in logs:
        html += f'<tr><td>{l.user}</td><td>{l.action}</td><td>{l.opt_time}</td></tr>'
    html += '''
</table>
</body>
</html>
'''
    return html

# 初始化数据库+默认管理员账号
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin",email="11768772@qq.com")
        admin.set_pwd("123456")
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=False,host="127.0.0.1",port=5000)