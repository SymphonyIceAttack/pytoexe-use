from wxauto4 import WeChat
import schedule
import time
import json
import os
from datetime import datetime, timedelta

# =====================【配置区】=====================
GROUP_NAME = "暧昧排档群🈲闲聊（新）"
OWNER = "꧁༃ༀIC科技ༀ༃꧂"  # 你的昵称 永久机主
MAX_MIC_NUM = 7
KOU_PAI_CODE = "P"
SUPPLEMENT_CODE = "补"
SEND_MIC_MINUTE = 40
START_KOUPAI_MINUTE = 45
CUT_OFF_MINUTE = 58
SUPPLEMENT_TIME_WINDOW = 20
# 默认初始管理员
DEFAULT_ADMINS = ["小虞宝（判官宝贝）", "许嘉树", "Sounds.Sky", "A李舒辞", "洛曦", "白漫安"]
# ====================================================

wx = WeChat()
wx.AddListenChat(who=GROUP_NAME, savepic=False)
data_file = "maixu_data.json"

# 初始化数据结构
bot_data = {
    "current_host": "",
    "host_time": "",
    "mic_list": [],
    "buwei_list": [],
    "shouguang_records": [],
    "heimai_records": [],
    "qupai_records": [],
    "baobei_records": [],
    "host_record": [],
    "mic_record": [],
    "buwei_record": [],
    "koupai_running": False,
    "round_end_time": None,
    "admin_list": DEFAULT_ADMINS.copy()
}

def load_data():
    global bot_data
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                load_json = json.load(f)
                # 读取存档，保留持久化的管理员列表
                bot_data = load_json
        except Exception as e:
            print("配置文件读取异常，使用默认配置")

def save_data():
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(bot_data, f, ensure_ascii=False, indent=2)

# 判断是否机主
def is_owner(name):
    return name == OWNER

# 判断是否管理员（机主自动拥有管理员权限）
def is_admin(name):
    if is_owner(name):
        return True
    return name in bot_data["admin_list"]

# 判断补位窗口
def can_supplement() -> bool:
    if bot_data["round_end_time"] is None:
        return False
    try:
        end_time = datetime.fromisoformat(bot_data["round_end_time"])
        now = datetime.now()
        return now <= end_time + timedelta(minutes=SUPPLEMENT_TIME_WINDOW)
    except:
        return False

# 开档公告
def get_open_notice(host_name, time_range):
    today = datetime.now().strftime("%Y-%m-%d")
    text = f"""当前主持:{host_name}
时间:{time_range}
日期：{today}
·-------------------------
接档状态积极，热情与老板互动！
1、麦克风清晰。
2、提前五分钟到厅。
3、尊重主持和老板，本档主持最大。
4、接活速度不要墨迹。
5、黑麦罚款10元，麦序作废
6、40分发麦序，58截止
7、无特殊情况不可取排，有任务排不可取，未回厅、取排黑麦处理！
8、报备15分钟内必须回厅，未回麦序作废
⚠️补充：每档58分结束后20分钟内发送【补】可以参与补位！
·-------------------------
排档扣：{KOU_PAI_CODE}"""
    return text

def send_msg(text):
    wx.SendMsg(text, GROUP_NAME)

# 定时40分提醒
def task_40_notice():
    if not bot_data["current_host"]:
        return
    msg = f"⏰【麦序通知】本档主持：{bot_data['current_host']}\n即将开始扣牌！扣牌代码：{KOU_PAI_CODE}\n麦序上限{MAX_MIC_NUM}位，58分截止！\n扣牌结束后20分钟内发送【补】可参与补位"
    send_msg(msg)

# 定时45分开扣牌
def task_45_start():
    bot_data["koupai_running"] = True
    bot_data["mic_list"].clear()
    bot_data["buwei_list"].clear()
    bot_data["round_end_time"] = None
    save_data()
    send_msg(f"🔥扣牌正式开启！输入【{KOU_PAI_CODE}】上麦，最多{MAX_MIC_NUM}麦序！")

# 定时58分结束扣牌
def task_58_stop():
    bot_data["koupai_running"] = False
    bot_data["round_end_time"] = datetime.now().isoformat()
    save_data()
    if len(bot_data["mic_list"]) > 0:
        mic_str = "\n".join([f"{i+1}.{name}" for i, name in enumerate(bot_data["mic_list"])])
    else:
        mic_str = "暂无上麦人员"
    msg = f"""✅本轮扣牌结束！
【本档麦序名单】
{mic_str}
⚠️接下来20分钟内发送【补】可以进行补位！
————————————
即将开启下一轮扣牌！"""
    send_msg(msg)
    bot_data["mic_record"].extend(bot_data["mic_list"])
    bot_data["buwei_record"].extend(bot_data["buwei_list"])
    save_data()

# 每周一9点周报
def weekly_stat_report():
    host_count = len(bot_data["host_record"])
    mic_total = len(bot_data["mic_record"])
    buwei_total = len(bot_data["buwei_record"])
    heimai_cnt = len(bot_data["heimai_records"])
    report = f"""📊【上周麦序统计周报】
主持档总数：{host_count}档
有效麦序总数：{mic_total}个
补位记录总数：{buwei_total}条
黑麦记录：{heimai_cnt}条"""
    send_msg(report)

def handle_message(sender, content):
    content = content.strip()
    # 开档
    if content.startswith("开档 "):
        args = content.split(" ")
        if len(args) >= 3:
            host = args[1]
            time_period = args[2]
            bot_data["current_host"] = host
            bot_data["host_time"] = time_period
            bot_data["host_record"].append({"host": host, "time": time_period, "create": str(datetime.now())})
            save_data()
            send_msg(get_open_notice(host, time_period))
        else:
            send_msg("格式错误！示例：开档 补天 20-21")

    # 扣牌 P
    if content == KOU_PAI_CODE and bot_data["koupai_running"]:
        if sender not in bot_data["mic_list"]:
            if len(bot_data["mic_list"]) < MAX_MIC_NUM:
                bot_data["mic_list"].append(sender)
                send_msg(f"✅{sender}成功上麦！当前麦序{len(bot_data['mic_list'])}/{MAX_MIC_NUM}")
            else:
                bot_data["buwei_list"].append(sender)
                send_msg(f"⚠️麦序已满，{sender}进入补位名单")
            save_data()

    # 补位 补
    if content == SUPPLEMENT_CODE:
        if bot_data["koupai_running"]:
            send_msg("❌当前正在扣牌时段，请等待扣牌结束后再补位！")
            return
        if not can_supplement():
            send_msg("❌已超出补位时间，无法补位！")
            return
        if sender in bot_data["mic_list"]:
            send_msg(f"❌{sender}已经在麦序中，无需重复补位！")
            return
        if len(bot_data["mic_list"]) < MAX_MIC_NUM:
            bot_data["mic_list"].append(sender)
            save_data()
            send_msg(f"✅{sender}补位成功！当前麦序{len(bot_data['mic_list'])}/{MAX_MIC_NUM}")
        else:
            send_msg("❌麦序已满，暂时无法补位！")

    if content == "!麦序":
        if len(bot_data["mic_list"]) == 0:
            send_msg("📋暂无麦序名单")
        else:
            mic_str = "\n".join([f"{i+1}.{n}" for i, n in enumerate(bot_data["mic_list"])])
            send_msg(f"【当前麦序】\n{mic_str}")

    if content.startswith("!收光"):
        bot_data["shouguang_records"].append({"sender":sender,"text":content,"time":str(datetime.now())})
        save_data()
        send_msg(f"📝收光记录已保存：{content}")

    if content.startswith("!报备"):
        bot_data["baobei_records"].append({"sender":sender,"text":content,"time":str(datetime.now())})
        save_data()
        send_msg(f"⏳{sender}报备成功！请15分钟内返回厅内，超时麦序作废！")

    if content.startswith("!取排"):
        bot_data["qupai_records"].append({"sender":sender,"text":content,"time":str(datetime.now())})
        save_data()
        send_msg(f"📌{sender}提交取排申请，若无任务擅自取排按黑麦处理！")

    # =====机主专属：增删管理员=====
    if content.startswith("!添加管理 ") and is_owner(sender):
        name = content.replace("!添加管理 ","").strip()
        if name == OWNER:
            send_msg("❌无法操作机主账号！")
            return
        if name in bot_data["admin_list"]:
            send_msg(f"❌{name}已经是管理员！")
        else:
            bot_data["admin_list"].append(name)
            save_data()
            send_msg(f"✅成功添加管理员：{name}")

    if content.startswith("!移除管理 ") and is_owner(sender):
        name = content.replace("!移除管理 ","").strip()
        if name == OWNER:
            send_msg("❌禁止移除机主！")
            return
        if name in bot_data["admin_list"]:
            bot_data["admin_list"].remove(name)
            save_data()
            send_msg(f"✅成功移除管理员：{name}")
        else:
            send_msg(f"❌{name}不在管理员列表！")

    # =====管理员通用指令=====
    if content.startswith("!黑麦") and is_admin(sender):
        bot_data["heimai_records"].append({"op":sender,"text":content,"time":str(datetime.now())})
        save_data()
        send_msg(f"🚨黑麦登记完成！罚款10元，麦序作废\n{content}")

    if content == "!启动扣牌" and is_admin(sender):
        task_45_start()
    if content == "!停止扣牌" and is_admin(sender):
        task_58_stop()
    if content == "!清空麦序" and is_admin(sender):
        bot_data["mic_list"].clear()
        bot_data["buwei_list"].clear()
        bot_data["round_end_time"] = None
        save_data()
        send_msg("🗑️麦序、补位名单已清空！")

    if content == "!帮助":
        help_text = """🤖麦序机器人指令大全
开档 昵称 时段 → 发布主持公告
P → 扣牌时段参与上麦
补 → 扣牌结束20分钟内进行补位
!麦序 → 查询当前麦序
!收光 内容 → 记录收光
!报备 事由 → 临时报备
!取排 事由 → 申请取排
【管理员指令】
!黑麦 @xx →登记黑麦
!启动扣牌
!停止扣牌
!清空麦序
【机主专属】
!添加管理 昵称
!移除管理 昵称"""
        send_msg(help_text)

# 定时任务注册
def init_schedule():
    schedule.every().hour.at(f":{SEND_MIC_MINUTE}").do(task_40_notice)
    schedule.every().hour.at(f":{START_KOUPAI_MINUTE}").do(task_45_start)
    schedule.every().hour.at(f":{CUT_OFF_MINUTE}").do(task_58_stop)
    schedule.every().monday.at("09:00").do(weekly_stat_report)

if __name__ == "__main__":
    load_data()
    init_schedule()
    print("======================================")
    print("✅麦序机器人启动成功")
    print("⚠️1.Windows讲述人必须开启")
    print("⚠️2.微信保持群窗口打开")
    print("======================================")
    while True:
        msgs = wx.GetListenMessage()
        for chat in msgs:
            one_msg = msgs[chat]
            for msg in one_msg:
                sender = msg.sender
                content = msg.content
                if msg.type == "msg":
                    handle_message(sender, content)
        schedule.run_pending()
        time.sleep(0.8)
