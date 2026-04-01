import requests, json, string, random, time
from urllib import parse

# define a string pool for generate random string
all_chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
deviceid_chars = string.ascii_uppercase + string.digits
# use requests.Session to handle cookies automatically
login_session = requests.Session()

deviceid = ''.join(random.choice(deviceid_chars) for _ in range(32))
timestamp = str(int(time.time() * 1000))
verify_session = ''.join(random.choice(all_chars) for _ in range(32))
print("verify_session:", verify_session)
print("timestamp:", timestamp)
print("deviceid:", deviceid)
username = input("username: ")
password = input("password: ")

# download captcha image
image_bytes = requests.get(f"http://ptlogin.4399.com/ptlogin/captcha.do?captchaId={verify_session}&xx=1").content
with open("captcha.png", "wb") as f:
    f.write(image_bytes)
print("captcha image written to captcha.png")
verify_code = input("verify_code: ")
login_data = "loginFrom=uframe&"
login_data += "postLoginHandler=default&"
login_data += "layoutSelfAdapting=true&"
login_data += "externalLogin=qq&"
login_data += "displayMode=popup&"
login_data += "layout=vertical&"
login_data += "bizId=2201001794&"
login_data += "appId=kid_wdsj&"
login_data += "gameId=wd&"
login_data += "css=http://microgame.5054399.net/v2/resource/cssSdk/default/login.css&"
login_data += "redirectUrl=&"
login_data += "mainDivId=popup_login_div&"
login_data += "includeFcmInfo=false&"
login_data += "level=8&"
login_data += "regLevel=8&"
login_data += "userNameLabel=4399%E7%94%A8%E6%88%B7%E5%90%8D&"
login_data += "userNameTip=%E8%AF%B7%E8%BE%93%E5%85%A54399%E7%94%A8%E6%88%B7%E5%90%8D&"
login_data += "welcomeTip=%E6%AC%A2%E8%BF%8E%E5%9B%9E%E5%88%B04399&"
login_data += f"sec=1&sessionId={verify_session}&"
login_data += f"inputCaptcha={verify_code}&"
login_data += f"username={username}&"
login_data += f"password={password}"
login_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Referer": "https://ptlogin.4399.com/ptlogin/regFrame.do?regMode=reg_normal&postLoginHandler=default&bizId=&redirectUrl=&displayMode=popup&css=&appId=www_home&gameId=&noEmail=false&regIdcard=false&autoLogin=true&cid=&aid=&level=4&mainDivId=popup_reg_div&includeFcmInfo=false&externalLogin=qq&fcmFakeValidate=true&expandFcmInput=true&userNameLabel=4399%E7%94%A8%E6%88%B7%E5%90%8D&userNameTip=%E8%AF%B7%E8%BE%93%E5%85%A54399%E7%94%A8%E6%88%B7%E5%90%8D&welcomeTip=%E6%AC%A2%E8%BF%8E%E5%9B%9E%E5%88%B04399&v=1720684215067&iframeId=popup_reg_frame",
    "Origin": "https://ptlogin.4399.com",
    "Content-type": "application/x-www-form-urlencoded"
}
login_resp = login_session.post("https://ptlogin.4399.com/ptlogin/login.do?v=1", headers=login_header, data=login_data)

if login_resp.text.find("验证码错误") != -1:
    raise Exception("验证码错误")

if login_resp.text.find("密码错误") != -1:
    raise Exception("密码错误")

if login_resp.text.find("用户名不存在") != -1:
    raise Exception("用户名不存在")

check_kid = login_session.post(f"http://ptlogin.4399.com/ptlogin/checkKidLoginUserCookie.do?appId=kid_wdsj&gameUrl=http://cdn.h5wan.4399sj.com/microterminal-h5-frame?game_id=500352&rand_time={timestamp}&nick=null&onLineStart=false&show=1&isCrossDomain=1&retUrl=http%253A%252F%252Fptlogin.4399.com%252Fresource%252Fucenter.html%253Faction%253Dlogin%2526appId%253Dkid_wdsj%2526loginLevel%253D8%2526regLevel%253D8%2526bizId%253D2201001794%2526externalLogin%253Dqq%2526qrLogin%253Dtrue%2526layout%253Dvertical%2526level%253D101%2526css%253Dhttp%253A%252F%252Fmicrogame.5054399.net%252Fv2%252Fresource%252FcssSdk%252Fdefault%252Flogin.css%2526v%253D2018_11_26_16%2526postLoginHandler%253Dredirect%2526checkLoginUserCookie%253Dtrue%2526redirectUrl%253Dhttp%25253A%25252F%25252Fcdn.h5wan.4399sj.com%25252Fmicroterminal-h5-frame%25253Fgame_id%25253D500352%252526rand_time%25253D{timestamp}", allow_redirects=False)
query_str = parse.quote(parse.urlparse(check_kid.headers['Location']).query)
print("query_str:", query_str)

sdk_info = login_session.get(f"https://microgame.5054399.net/v2/service/sdk/info?callback=&queryStr={query_str}")
sdk_info_data = parse.parse_qs(sdk_info.json()["data"]["sdk_login_data"])
sdk_username = sdk_info_data.get("username")[0]
sdk_uid = sdk_info_data.get("uid")[0]
sdk_token = sdk_info_data.get("token")[0]
sdk_time = sdk_info_data.get("time")[0]
print("sdk_username:", sdk_username)
print("uid:", sdk_uid)
print("token:", sdk_token)
print("time:", sdk_time)

sauth_json_text = json.dumps({
  "timestamp": sdk_time,
  "userid": sdk_username,
  "realname": "{\"realname_type\":\"0\"}",
  "gameid": "x19",
  "login_channel": "4399pc",
  "app_channel": "4399pc",
  "platform": "pc",
  "sdkuid": sdk_uid,
  "sessionid": sdk_token,
  "sdk_version": "1.0.0",
  "udid": deviceid,
  "deviceid": deviceid,
  "aim_info": "{\"aim\":\"100.100.100.100\",\"country\":\"CN\",\"tz\":\"+0800\",\"tzid\":\"\"}",
  "client_login_sn": deviceid,
  "gas_token": "",
  "source_platform": "pc",
  "ip": "100.100.100.100"
})
sauth = {
    "sauth_json": sauth_json_text
}
print("sauth:", json.dumps(sauth))