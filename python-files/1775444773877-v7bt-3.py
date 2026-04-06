import os, base64, urllib.parse, re

# ------------------- 节点解析函数 -------------------
def parse_vless(link):
    if not link.startswith("vless://"): return "# 不是 VLESS 节点"
    
    # 1. 提取节点别名 (解决名字冲突)
    link, _, remarks = link.partition('#')
    node_name = urllib.parse.unquote(remarks) if remarks else "VLESS_NODE"
    
    # 2. 修复截取错误 (vless:// 是 8 个字符)
    link = link[8:]
    
    m = re.match(r'([0-9a-fA-F-]+)@([^?]+)\??(.*)', link)
    if not m: return f"# VLESS 节点解析失败: {node_name}"
    uuid, server_port, query = m.groups()
    
    server, port = (server_port.split(':') if ':' in server_port else (server_port, 443))
    
    # 3. 更安全的 URL 参数解析
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
    
    # 4. 构建标准的 Clash YAML 字典
    yaml_lines = [
        f"- name: \"{node_name}\"",
        "  type: vless",
        f"  server: \"{server}\"",
        f"  port: {port}",
        f"  uuid: \"{uuid}\"",
        f"  tls: {str(tls).lower()}",
        f"  network: {network}"
    ]
    
    if tls:
        yaml_lines.append(f"  servername: \"{sni}\"")
        # Reality 特殊参数支持
        if tls_str == "reality":
            yaml_lines.append("  reality-opts:")
            yaml_lines.append(f"    public-key: \"{params.get('pbk', '')}\"")
            if "fp" in params:
                yaml_lines.append(f"    client-fingerprint: {params.get('fp')}")
                
    flow = params.get("flow", "")
    if flow:
        yaml_lines.append(f"  flow: {flow}")
        
    if network == "ws":
        yaml_lines.append("  ws-opts:")
        yaml_lines.append(f"    path: \"{params.get('path', '/')}\"")
        if "host" in params:
            yaml_lines.append("    headers:")
            yaml_lines.append(f"      Host: \"{params.get('host')}\"")
    elif network == "grpc":
        yaml_lines.append("  grpc-opts:")
        yaml_lines.append(f"    grpc-service-name: \"{params.get('serviceName', '')}\"")
        
    return "\n".join(yaml_lines)

def parse_ss(link):
    if not link.startswith("ss://"): return "# 不是 SS 节点"
    link, _, remarks = link.partition('#')
    node_name = urllib.parse.unquote(remarks) if remarks else "SS_NODE"
    try:
        # 修复 Base64 padding bug
        pad = 4 - len(link) % 4
        if pad < 4: 
            link += '=' * pad
            
        decoded = base64.urlsafe_b64decode(link).decode()
        method, rest = decoded.split(':', 1)
        password, server_port = rest.split('@')
        server, port = server_port.split(':')
        return f"- name: \"{node_name}\"\n  type: ss\n  server: \"{server}\"\n  port: {port}\n  cipher: \"{method}\"\n  password: \"{password}\""
    except: return f"# SS 节点解析失败: {node_name}"

def parse_trojan(link):
    if not link.startswith("trojan://"): return "# 不是 Trojan 节点"
    link, _, remarks = link.partition('#')
    node_name = urllib.parse.unquote(remarks) if remarks else "TROJAN_NODE"
    try:
        link = link[9:]
        password, rest = link.split('@')
        server, port = rest.split(':')
        return f"- name: \"{node_name}\"\n  type: trojan\n  server: \"{server}\"\n  port: {port}\n  password: \"{password}\""
    except: return f"# Trojan 节点解析失败: {node_name}"

def parse_link(link):
    link = link.strip()
    if link.startswith("vless://"): return parse_vless(link)
    elif link.startswith("ss://"): return parse_ss(link)
    elif link.startswith("trojan://"): return parse_trojan(link)
    else: return f"# 不支持的协议或空行: {link}"

# ------------------- 主程序 -------------------
if __name__=="__main__":
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_file = os.path.join(desktop, "clash_node.yaml")
    print("==== 多协议节点 -> Clash YAML 转换器 ====")
    print(f"生成的文件将保存到桌面：{output_file}\n")

    while True:
        links = input("请输入节点链接（多条空格或换行，exit退出）：\n")
        if links.strip().lower() == "exit": break
        if not links.strip(): continue # 防止直接回车报错
        
        results = []
        for link in links.strip().split():
            yaml = parse_link(link)
            results.append(yaml)
            
        final = "proxies:\n  " + "\n  ".join([r for r in results if r])
        print("\n生成的 Clash YAML 节点：\n")
        print(final)

        save = input(f"是否保存到桌面 {output_file} 文件？(y/n): ")
        if save.lower() == "y":
            with open(output_file, "w" if not os.path.exists(output_file) else "a", encoding="utf-8") as f:
                f.write(final + "\n\n")
            print(f"已保存到桌面：{output_file}\n")