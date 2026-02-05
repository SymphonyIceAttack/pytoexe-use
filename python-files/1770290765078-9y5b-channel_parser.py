
import re

def parse_js_config(input_text):
    # 正则表达式匹配 jsSetConfig 函数调用中的参数
    pattern = r"jsSetConfig\([^)]*\)"
    match = re.search(pattern, input_text)
    if not match:
        return ""
    
    config_str = match.group(0)
    
    # 提取 ChannelName
    channel_name_match = re.search(r'ChannelName="([^"]*)"', config_str)
    channel_name = channel_name_match.group(1) if channel_name_match else ""
    
    # 提取 ChannelURL
    channel_url_match = re.search(r'ChannelURL="([^"]*)"', config_str)
    channel_url = channel_url_match.group(1) if channel_url_match else ""
    
    # 构造输出内容
    output = f"#EXTINF:-1,{channel_name}\n{channel_url}"
    return output

# 示例输入
input_text = '''jsSetConfig('Channel','ChannelID="ch13093011261236109792",ChannelName="CCTV1",UserChannelID="1",ChannelURL="rtsp://117.57.69.4:554/live/ch13093011261236109792.sdp?playtype=1&boid=001&clienttype=1&time=20260205165929+08&life=172800&ifpricereqsnd=1&vcdnid=001&userid=p56100023058&mediaid=ch13093011261236109792&ctype=2&TSTVTimeLife=7200&authid=0&terminalflag=1&UserLiveType=0&stbid=00100516060100A000007847E33275AE&nodelevel=3&profilecode=&AuthInfo=kxUwnvMmKy1U%2F7TTXUskOlavQlPW8ycdB8GhT9zx8yq0JMDlx%2F%2B3lYqbK0yFsGrVnj89fLkc62wThiU1pNYT1w%3D%3D&usersessionid=1484852656&bitrate=3000&distype=0",TimeShift="1",ChannelSDP="",TimeShiftURL="rtsp://117.57.69.4:554/live/ch13093011261236109792.sdp?playtype=1&boid=001&clienttype=1&time=20260205165929+08&life=172800&ifpricereqsnd=0&vcdnid=001&userid=p56100023058&mediaid=ch13093011261236109792&ctype=5&TSTVTimeLife=7200&authid=0&UserLiveType=0&stbid=00100516060100A000007847E33275AE&nodelevel=3&terminalflag=1&profilecode=&AuthInfo=kxUwnvMmKy1U%2F7TTXUskOlavQlPW8ycdB8GhT9zx8yq0JMDlx%2F%2B3lYqbK0yFsGrVnj89fLkc62wThiU1pNYT1w%3D%3D&bitrate=3000&distype=0&usersessionid=1484852655",ChannelLogURL="",PositionX="0",PositionY="0",BeginTime="0",Interval="-1",Lasting="0",ChannelType="4",ChannelPurchased="",LocalTimeShift="1",UserTeamChannelID="1",TimeShiftLength="7200",telecomcode="00000001000000050000000000000055"');'''

# 执行解析
result = parse_js_config(input_text)
print(result)
