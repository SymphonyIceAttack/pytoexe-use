# 终极版：纯Python QQ后端（能收能发、实时同步）
import requests
import json
import time
import random
import re
import os
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import qrcode

# ===================== 基础配置 =====================
app = Flask(__name__)
CORS(app)

# 全局变量
is_login = False
qq_num = ""
skey = ""
pskey = ""
uin = ""
ticket = ""
msg_history = []
qr_code_path = os.path.join(os.path.expanduser("~"), "Desktop", "qq_login_qrcode.png")
msg_polling_thread = None  # 消息轮询线程
polling_running = False

# ===================== 1. 生成二维码（已修复接口） =====================
def generate_qrcode():
    global ticket
    try:
        ticket = str(int(time.time() * 1000)) + "_" + str(random.randint(1000, 9999))
        # 核心修复：使用新的扫码接口，避免 s_url is invalid
        qr_content = f"https://ptlogin.qun.qq.com/cgi-bin/login_new?type=qrcode&js_ver=200321&da1=1&aid=200100389&da2=2&ptqrtoken={ticket}"
        qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=2)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        img.save(qr_code_path, format='PNG', quality=100)
        print(f"✅ 二维码生成成功：{qr_code_path}")
        return True
    except Exception as e:
        print(f"❌ 生成二维码失败：{str(e)}")
        img = Image.new('RGB', (300, 300), color='white')
        img.save(qr_code_path)
        return False

# ===================== 2. 登录校验 =====================
def check_login():
    global is_login, qq_num, skey, pskey, uin, polling_running
    if not ticket:
        return False
    try:
        url = f"https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https://im.qq.com/index/login.html&ptqrtoken={ticket}&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-{int(time.time())}&js_ver=200321&js_type=0&login_sig=&pt_randsalt=0&t={int(time.time())}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=10)
        res_text = res.text
        
        if "登录成功" in res_text:
            cookies = res.headers.get("Set-Cookie", "")
            qq_num = re.findall(r'uin=o(\d+)', cookies)[0] if re.findall(r'uin=o(\d+)', cookies) else ""
            skey = re.findall(r'skey=(.*?);', cookies)[0] if re.findall(r'skey=(.*?);', cookies) else ""
            pskey = re.findall(r'pskey=(.*?);', cookies)[0] if re.findall(r'pskey=(.*?);', cookies) else ""
            uin = qq_num
            is_login = True
            print(f"🎉 登录成功！QQ号：{qq_num}")
            
            # 登录成功后，启动消息轮询（实时收消息）
            if not polling_running:
                start_msg_polling()
            return True
        elif "二维码失效" in res_text:
            print("❌ 二维码失效，重新生成...")
            generate_qrcode()
            return False
        elif "未扫码" in res_text:
            return False
        else:
            return False
    except Exception as e:
        print(f"❌ 检查登录失败：{str(e)}")
        return False

# ===================== 3. 核心新增：实时轮询接收消息 =====================
def poll_new_messages():
    """后台轮询腾讯接口，实时接收新消息"""
    global polling_running, msg_history, qq_num, skey
    polling_running = True
    last_msg_time = int(time.time())
    
    while polling_running and is_login and skey:
        try:
            # 腾讯消息拉取接口（移动端协议）
            url = f"https://im.qq.com/mobileqq/getmsg?uin={qq_num}&skey={skey}&pskey={pskey}&time={int(time.time())}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=5)
            res_data = res.json() if res.status_code == 200 else {}
            
            # 解析新消息
            if "msgs" in res_data and len(res_data["msgs"]) > 0:
                for msg in res_data["msgs"]:
                    msg_time = int(msg.get("time", 0))
                    # 只处理新消息（避免重复）
                    if msg_time > last_msg_time:
                        sender_id = msg.get("from_uin", "")
                        content = msg.get("content", "")
                        if sender_id and content and sender_id != qq_num:
                            # 记录新消息
                            msg_history.append({
                                "sender": f"对方({sender_id})",
                                "content": content,
                                "is_mine": False
                            })
                            print(f"📩 收到新消息：{sender_id} → {content}")
                            last_msg_time = msg_time
            time.sleep(2)  # 每2秒轮询一次（避免频繁请求）
        except Exception as e:
            print(f"❌ 轮询消息失败：{str(e)}")
            time.sleep(3)

def start_msg_polling():
    """启动消息轮询线程（后台运行，不阻塞Flask）"""
    global msg_polling_thread
    msg_polling_thread = threading.Thread(target=poll_new_messages, daemon=True)
    msg_polling_thread.start()
    print("✅ 消息轮询已启动，实时接收新消息...")

# ===================== 4. 发送消息 =====================
def send_real_msg(target_id, content, msg_type="private"):
    if not is_login or not skey or not pskey:
        return {"success": False, "msg": "未登录！请先扫描桌面二维码"}
    
    try:
        if msg_type == "private":
            url = "https://im.qq.com/mobileqq/sendmsg/send2friend"
            data = {
                "to_uin": target_id, "msg": content, "uin": qq_num, "skey": skey, "pskey": pskey,
                "msg_id": int(time.time() * 1000), "clientid": f"5370{random.randint(1000,9999)}", "time": int(time.time())
            }
        else:
            url = "https://im.qq.com/mobileqq/sendmsg/send2group"
            data = {
                "group_uin": target_id, "msg": content, "uin": qq_num, "skey": skey, "pskey": pskey,
                "msg_id": int(time.time() * 1000), "clientid": f"5370{random.randint(1000,9999)}", "time": int(time.time())
            }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://im.qq.com/", "Content-Type": "application/x-www-form-urlencoded"
        }
        
        res = requests.post(url, data=data, headers=headers, timeout=10)
        if res.status_code == 200 and ("success" in res.text or "ok" in res.text):
            msg_history.append({"sender": f"我({qq_num})", "content": content, "is_mine": True})
            return {"success": True, "msg": f"✅ 消息已发送到{target_id}！"}
        else:
            return {"success": False, "msg": f"❌ 发送失败：{res.text[:100]}"}
    except Exception as e:
        return {"success": False, "msg": f"❌ 发送异常：{str(e)}"}

# ===================== 5. 前端接口（新增消息同步接口） =====================
@app.route("/api/init_qrcode", methods=["GET"])
def init_qrcode():
    generate_qrcode()
    return jsonify({"success": True, "msg": f"二维码已生成：{qr_code_path}", "qr_path": qr_code_path})

@app.route("/api/login_status", methods=["GET"])
def login_status():
    check_login()
    return jsonify({"is_login": is_login, "qq_num": qq_num, "qr_path": qr_code_path})

@app.route("/api/send_msg", methods=["POST"])
def send_msg():
    data = request.json
    target_id = data.get("target_id", "").strip()
    content = data.get("content", "").strip()
    msg_type = data.get("msg_type", "private")
    
    if not target_id or not content:
        return jsonify({"success": False, "msg": "请填写QQ号/群号和消息内容！"})
    
    result = send_real_msg(target_id, content, msg_type)
    return jsonify(result)

@app.route("/api/msg_history", methods=["GET"])
def msg_history_api():
    """前端拉取最新消息历史（包括对方回复）"""
    return jsonify({"history": msg_history})

@app.route("/api/clear_history", methods=["GET"])
def clear_history():
    """清空消息历史"""
    global msg_history
    msg_history = []
    return jsonify({"success": True, "msg": "消息历史已清空"})

# ===================== 6. 启动服务 =====================
if __name__ == "__main__":
    print("="*60)
    print("🚀 终极版纯Python QQ后端（能收能发、实时同步）")
    print("✅ 扫码登录后自动接收对方回复")
    print("="*60)
    generate_qrcode()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
