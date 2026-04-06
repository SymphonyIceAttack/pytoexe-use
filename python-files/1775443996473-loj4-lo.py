import os, base64, urllib.parse, re

# ------------------- 节点解析函数 -------------------
def parse_vless(link):
    if not link.startswith("vless://"): return None
    link = link[7:]
    m = re.match(r'([0-9a-fA-F-]+)@([^?]+)\??(.*)', link)
    if not m: return None
    uuid, server_port, query = m.groups()
    server, port = (server_port.split(':') if ':' in server_port else (server_port, 443))
    params = {}
    if query:
        for kv in urllib.parse.unquote(query).split('&'):
            if '=' in kv: k,v = kv.split('=',1); params[k]=v
    tls = params.get("security","").lower() in ["tls","xtls"]
    network = params.get("type","tcp")
    ws_path = params.get("path","")
    host = params.get("host","")
    grpc_service = params.get("serviceName","")
    flow = params.get("flow","")
    yaml = f"- name: \"VLESS_NODE\"\n  type: vless\n  server: \"{server}\"\n  port: {port}\n  uuid: \"{uuid}\"\n  tls: {str(tls).lower()}\n  network: {network}"
    if network=="ws": yaml += f"\n  ws-path: \"{ws_path}\"\n  ws-headers:\n    Host: \"{host}\""
    if network=="grpc": yaml += f"\n  grpc-opts:\n    grpc-service-name: \"{grpc_service}\""
    if flow: yaml += f"\n  flow: {flow}"
    return yaml

def parse_ss(link):
    if not link.startswith("ss://"): return None
    link, _, _ = link.partition('#')
    try:
        decoded = base64.urlsafe_b64decode(link + '='*(4-len(link)%4)).decode()
        method, rest = decoded.split(':',1)
        password, server_port = rest.split('@')
        server, port = server_port.split(':')
        yaml = f"- name: \"SS_NODE\"\n  type: ss\n  server: \"{server}\"\n  port: {port}\n  cipher: \"{method}\"\n  password: \"{password}\""
        return yaml
    except: return None

def parse_trojan(link):
    if not link.startswith("trojan://"): return None
    link = link[9:]
    password, rest = link.split('@')
    server, port = rest.split(':')
    yaml = f"- name: \"TROJAN_NODE\"\n  type: trojan\n  server: \"{server}\"\n  port: {port}\n  password: \"{password}\""
    return yaml

def parse_link(link):
    if link.startswith("vless://"): return parse_vless(link)
    elif link.startswith("ss://"): return parse_ss(link)
    elif link.startswith("trojan://"): return parse_trojan(link)
    else: return f"# 不支持的协议: {link}"

# ------------------- 主程序 -------------------
if __name__=="__main__":
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(desktop, "clash_node.yaml")
    print("==== 多协议节点 → Clash YAML 转换器 ====")
    print(f"生成的文件将保存到桌面：{output_file}\n")

    while True:
        links = input("请输入节点链接（多条空格或换行，exit退出）：\n")
        if links.lower()=="exit": break
        results = []
        for link in links.strip().split():
            yaml = parse_link(link)
            results.append(yaml)
        final = "proxies:\n" + "\n\n".join(results)
        print("\n生成的 Clash YAML 节点：\n")
        print(final)

        save = input(f"是否保存到桌面 {output_file} 文件？(y/n): ")
        if save.lower() == "y":
            with open(output_file,"a",encoding="utf-8") as f:
                f.write(final + "\n\n")
            print(f"已保存到桌面：{output_file}\n")