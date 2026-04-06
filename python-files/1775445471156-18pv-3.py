import os, base64, urllib.parse, re

# ------------------- 辅助函数 -------------------
def clean_name(name):
    # 处理节点名称，防止引号导致 YAML 格式错乱
    return urllib.parse.unquote(name).replace('"', '').strip() if name else "UNNAMED_NODE"

# ------------------- 节点解析函数 -------------------
def parse_vless(link):
    if not link.startswith("vless://"): return None, None
    link, _, remarks = link.partition('#')
    node_name = clean_name(remarks)
    
    link = link[8:]
    m = re.match(r'([0-9a-fA-F-]+)@([^?]+)\??(.*)', link)
    if not m: return None, node_name
    uuid, server_port, query = m.groups()
    
    server, port = (server_port.split(':') if ':' in server_port else (server_port, 443))
    
    params = {}
    if query:
        for kv in query.split('&'):
            if '=' in kv: 
                k, v = kv.split('=', 1)
                params[k] = urllib.parse.unquote(v)
                
    tls_str = params.get("security", "").lower()
    tls = tls_str in ["tls", "xtls", "reality"]
    network = params.get("type", "tcp")
    sni = params.get("sni", server)
    
    # 修复了严格的 2空格与4空格 YAML 缩进对齐
    lines = [
        f"  - name: \"{node_name}\"",
        "    type: vless",
        f"    server: \"{server}\"",
        f"    port: {port}",
        f"    uuid: \"{uuid}\"",
        f"    tls: {str(tls).lower()}",
        f"    network: {network}"
    ]
    
    if tls:
        lines.append(f"    servername: \"{sni}\"")
        if tls_str == "reality":
            lines.append("    reality-opts:")
            lines.append(f"      public-key: \"{params.get('pbk', '')}\"")
            if "fp" in params:
                lines.append(f"      client-fingerprint: {params.get('fp')}")
                
    flow = params.get("flow", "")
    if flow: lines.append(f"    flow: {flow}")
        
    if network == "ws":
        lines.append("    ws-opts:")
        lines.append(f"      path: \"{params.get('path', '/')}\"")
        if "host" in params:
            lines.append("      headers:")
            lines.append(f"        Host: \"{params.get('host')}\"")
    elif network == "grpc":
        lines.append("    grpc-opts:")
        lines.append(f"      grpc-service-name: \"{params.get('serviceName', '')}\"")
        
    return "\n".join(lines), node_name

def parse_ss(link):
    if not link.startswith("ss://"): return None, None
    link, _, remarks = link.partition('#')
    node_name = clean_name(remarks)
    try:
        pad = 4 - len(link) % 4
        if pad < 4: link += '=' * pad
        decoded = base64.urlsafe_b64decode(link).decode()
        method, rest = decoded.split(':', 1)
        password, server_port = rest.split('@')
        server, port = server_port.split(':')
        
        yaml_str = f"  - name: \"{node_name}\"\n    type: ss\n    server: \"{server}\"\n    port: {port}\n    cipher: \"{method}\"\n    password: \"{password}\""
        return yaml_str, node_name
    except: return None, node_name

def parse_trojan(link):
    if not link.startswith("trojan://"): return None, None
    link, _, remarks = link.partition('#')
    node_name = clean_name(remarks)
    try:
        link = link[9:]
        password, rest = link.split('@')
        server, port = rest.split(':')
        
        yaml_str = f"  - name: \"{node_name}\"\n    type: trojan\n    server: \"{server}\"\n    port: {port}\n    password: \"{password}\""
        return yaml_str, node_name
    except: return None, node_name

def parse_link(link):
    link = link.strip()
    if link.startswith("vless://"): return parse_vless(link)
    elif link.startswith("ss://"): return parse_ss(link)
    elif link.startswith("trojan://"): return parse_trojan(link)
    else: return None, None

# ------------------- 主程序 -------------------
if __name__=="__main__":
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(desktop, "clash_full_config.yaml")
    print("==== 多协议节点 -> Clash 完整配置生成器 ====")
    print(f"生成的配置文件将可以直接导入 Clash，路径：{output_file}\n")

    while True:
        links = input("请输入节点链接（多条空格或换行，exit退出）：\n")
        if links.strip().lower() == "exit": break
        if not links.strip(): continue
        
        node_yamls = []
        node_names = []
        
        for link in links.strip().split():
            yaml_str, name = parse_link(link)
            if yaml_str and name:
                node_yamls.append(yaml_str)
                node_names.append(name)
        
        if not node_yamls:
            print("没有解析出有效节点，请检查链接格式。\n")
            continue
            
        # 1. 组合所有节点的 YAML
        proxy_str = "\n".join(node_yamls)
        
        # 2. 生成策略组里需要的节点名称列表 (格式: - "节点名")
        group_proxies = "\n".join([f"      - \"{n}\"" for n in node_names])
        
        # 3. 嵌入到完整的 Clash 基础模板中
        final_config = f"""port: 7890
socks-port: 7891
allow-lan: true
mode: rule
log-level: info

proxies:
{proxy_str}

proxy-groups:
  - name: "🚀 节点选择"
    type: select
    proxies:
      - "⚡ 自动测速"
{group_proxies}
      - DIRECT
  
  - name: "⚡ 自动测速"
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    proxies:
{group_proxies}

rules:
  - MATCH,🚀 节点选择
"""
        
        print("\n生成的 Clash 完整配置（预览）：\n")
        print(final_config)

        save = input(f"是否覆盖保存到桌面文件？(y/n): ")
        if save.lower() == "y":
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(final_config)
            print(f"已生成完整配置！请前往桌面把 {output_file} 导入 Clash。\n")