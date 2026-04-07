import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from scapy.all import rdpcap, wrpcap, Packet, Raw
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.l2 import Ether, ARP
import os
from datetime import datetime

class PcapAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("PCAP 流量分析编辑器 v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 数据存储
        self.packets = []  # 当前加载的所有包
        self.filtered_packets = []  # 过滤后的包（用于显示）
        self.current_file = None
        self.selected_indices = set()  # 选中的原始索引
        
        self.setup_ui()
        
    def setup_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="打开 PCAP", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存 PCAP", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="另存为", command=self.save_as).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="删除选中", command=self.delete_selected, bootstyle="danger").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="复制选中", command=self.copy_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="统计信息", command=self.show_stats).pack(side=tk.LEFT, padx=2)
        
        # 过滤栏
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(filter_frame, text="过滤:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="应用", command=self.apply_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="清除", command=self.clear_filter).pack(side=tk.LEFT, padx=2)
        ttk.Label(filter_frame, text="(支持: ip/tcp/udp/icmp/arp/port 80/host 1.2.3.4)").pack(side=tk.LEFT, padx=5)
        
        # 主内容区 - 左右分割
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧包列表
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=3)
        
        # 包列表表格
        columns = ("index", "time", "src", "dst", "proto", "len", "info")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("index", text="#")
        self.tree.heading("time", text="时间")
        self.tree.heading("src", text="源地址")
        self.tree.heading("dst", text="目标地址")
        self.tree.heading("proto", text="协议")
        self.tree.heading("len", text="长度")
        self.tree.heading("info", text="信息")
        
        self.tree.column("index", width=50, anchor="center")
        self.tree.column("time", width=100)
        self.tree.column("src", width=120)
        self.tree.column("dst", width=120)
        self.tree.column("proto", width=60, anchor="center")
        self.tree.column("len", width=60, anchor="center")
        self.tree.column("info", width=200)
        
        # 滚动条
        vsb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(left_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.show_packet_detail)
        
        # 右侧详情区
        right_frame = ttk.Notebook(paned)
        paned.add(right_frame, weight=2)
        
        # 概要标签页
        self.summary_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Consolas", 10))
        right_frame.add(self.summary_text, text="概要")
        
        # 十六进制标签页
        self.hex_text = scrolledtext.ScrolledText(right_frame, wrap=tk.NONE, font=("Consolas", 10))
        right_frame.add(self.hex_text, text="十六进制")
        
        # 原始数据标签页
        self.raw_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Consolas", 9))
        right_frame.add(self.raw_text, text="原始数据")
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PCAP files", "*.pcap *.pcapng"), ("All files", "*.*")]
        )
        if not file_path:
            return
            
        try:
            self.current_file = file_path
            self.packets = rdpcap(file_path)
            self.filtered_packets = list(enumerate(self.packets))
            self.selected_indices.clear()
            self.display_packets()
            self.status_var.set(f"已加载: {os.path.basename(file_path)} | 共 {len(self.packets)} 个包")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件:\n{str(e)}")
            
    def display_packets(self):
        # 清空现有内容
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 填充数据
        for idx, pkt in self.filtered_packets:
            self.insert_packet_to_tree(idx, pkt)
            
    def insert_packet_to_tree(self, idx, pkt):
        # 提取基本信息
        time_str = datetime.fromtimestamp(float(pkt.time)).strftime("%H:%M:%S.%f")[:-3]
        
        src = ""
        dst = ""
        proto = "OTHER"
        length = len(pkt)
        info = ""
        
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst
            if TCP in pkt:
                proto = "TCP"
                info = f"{pkt[TCP].sport} -> {pkt[TCP].dport} [ACK]" if pkt[TCP].flags & 0x10 else f"{pkt[TCP].sport} -> {pkt[TCP].dport}"
            elif UDP in pkt:
                proto = "UDP"
                info = f"{pkt[UDP].sport} -> {pkt[UDP].dport}"
            elif ICMP in pkt:
                proto = "ICMP"
                info = f"Type={pkt[ICMP].type}"
        elif ARP in pkt:
            src = pkt[ARP].psrc
            dst = pkt[ARP].pdst
            proto = "ARP"
            info = "who has" if pkt[ARP].op == 1 else "is at"
        elif Ether in pkt:
            src = pkt[Ether].src
            dst = pkt[Ether].dst
            
        values = (idx, time_str, src, dst, proto, length, info)
        self.tree.insert("", tk.END, values=values, tags=(str(idx),))
        
    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item, "values")
        if not values:
            return
            
        idx = int(values[0])
        if idx < len(self.packets):
            pkt = self.packets[idx]
            self.show_packet_info(pkt)
            
    def show_packet_info(self, pkt):
        # 概要
        self.summary_text.delete(1.0, tk.END)
        summary = []
        
        if Ether in pkt:
            summary.append(f"以太网层: {pkt[Ether].src} -> {pkt[Ether].dst}")
        if IP in pkt:
            ip = pkt[IP]
            summary.append(f"IP层: {ip.src} -> {ip.dst}")
            summary.append(f"  TTL: {ip.ttl}, 标识: {ip.id}, 分片: {ip.flags}")
        if TCP in pkt:
            tcp = pkt[TCP]
            summary.append(f"TCP: {tcp.sport} -> {tcp.dport}")
            summary.append(f"  Seq: {tcp.seq}, Ack: {tcp.ack}")
            summary.append(f"  Flags: {tcp.flags}")
        elif UDP in pkt:
            udp = pkt[UDP]
            summary.append(f"UDP: {udp.sport} -> {udp.dport}")
            summary.append(f"  长度: {udp.len}")
        elif ICMP in pkt:
            icmp = pkt[ICMP]
            summary.append(f"ICMP: Type={icmp.type}, Code={icmp.code}")
            
        self.summary_text.insert(tk.END, "\n".join(summary))
        
        # 十六进制
        self.hex_text.delete(1.0, tk.END)
        raw = bytes(pkt)
        hex_str = ""
        for i in range(0, len(raw), 16):
            chunk = raw[i:i+16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            hex_str += f"{i:04x}  {hex_part:<48}  {ascii_part}\n"
        self.hex_text.insert(tk.END, hex_str)
        
        # 原始数据（可打印字符）
        self.raw_text.delete(1.0, tk.END)
        try:
            if Raw in pkt:
                payload = pkt[Raw].load
                # 尝试解码为文本
                decoded = payload.decode('utf-8', errors='replace')
                self.raw_text.insert(tk.END, decoded)
        except:
            self.raw_text.insert(tk.END, "[二进制数据无法显示为文本]")
            
    def show_packet_detail(self, event):
        # 双击显示详细窗口
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        idx = int(values[0])
        pkt = self.packets[idx]
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"包 #{idx} 详细信息")
        detail_window.geometry("600x500")
        
        text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, pkt.show(dump=True))
        
    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的包")
            return
            
        indices_to_delete = []
        for item in selection:
            values = self.tree.item(item, "values")
            idx = int(values[0])
            indices_to_delete.append(idx)
            
        # 确认删除
        if not messagebox.askyesno("确认", f"确定删除选中的 {len(indices_to_delete)} 个包吗?"):
            return
            
        # 删除（从大到小排序，避免索引错位）
        indices_to_delete.sort(reverse=True)
        for idx in indices_to_delete:
            del self.packets[idx]
            
        # 重新建立索引
        self.filtered_packets = list(enumerate(self.packets))
        self.display_packets()
        self.status_var.set(f"已删除 {len(indices_to_delete)} 个包，剩余 {len(self.packets)} 个")
        
    def copy_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要复制的包")
            return
            
        # 获取选中的包
        packets_to_copy = []
        for item in selection:
            values = self.tree.item(item, "values")
            idx = int(values[0])
            packets_to_copy.append(self.packets[idx].copy())
            
        # 在当前位置后插入副本
        insert_positions = []
        for item in selection:
            values = self.tree.item(item, "values")
            idx = int(values[0])
            insert_positions.append(idx)
            
        # 在原始位置后插入（从大到小处理）
        for i, idx in enumerate(sorted(insert_positions, reverse=True)):
            self.packets.insert(idx + 1, packets_to_copy[len(packets_to_copy)-1-i])
            
        self.filtered_packets = list(enumerate(self.packets))
        self.display_packets()
        self.status_var.set(f"已复制 {len(packets_to_copy)} 个包")
        
    def save_file(self):
        if not self.current_file:
            self.save_as()
            return
            
        try:
            wrpcap(self.current_file, self.packets)
            self.status_var.set(f"已保存: {os.path.basename(self.current_file)}")
            messagebox.showinfo("成功", "文件已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{str(e)}")
            
    def save_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pcap",
            filetypes=[("PCAP files", "*.pcap"), ("All files", "*.*")]
        )
        if not file_path:
            return
            
        try:
            wrpcap(file_path, self.packets)
            self.current_file = file_path
            self.status_var.set(f"已保存: {os.path.basename(file_path)}")
            messagebox.showinfo("成功", "文件已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{str(e)}")
            
    def apply_filter(self):
        filter_text = self.filter_var.get().lower().strip()
        if not filter_text:
            self.clear_filter()
            return
            
        self.filtered_packets = []
        for idx, pkt in enumerate(self.packets):
            match = False
            
            # IP过滤
            if "ip" in filter_text and IP in pkt:
                match = True
            # TCP过滤
            elif "tcp" in filter_text and TCP in pkt:
                match = True
            # UDP过滤
            elif "udp" in filter_text and UDP in pkt:
                match = True
            # ICMP过滤
            elif "icmp" in filter_text and ICMP in pkt:
                match = True
            # ARP过滤
            elif "arp" in filter_text and ARP in pkt:
                match = True
            # 端口过滤 port 80
            elif "port" in filter_text:
                try:
                    port_num = int(filter_text.split()[1])
                    if (TCP in pkt and (pkt[TCP].sport == port_num or pkt[TCP].dport == port_num)) or \
                       (UDP in pkt and (pkt[UDP].sport == port_num or pkt[UDP].dport == port_num)):
                        match = True
                except:
                    pass
            # IP地址过滤 host x.x.x.x
            elif "host" in filter_text:
                try:
                    ip_addr = filter_text.split()[1]
                    if IP in pkt and (pkt[IP].src == ip_addr or pkt[IP].dst == ip_addr):
                        match = True
                except:
                    pass
                    
            if match:
                self.filtered_packets.append((idx, pkt))
                
        self.display_packets()
        self.status_var.set(f"过滤完成: 显示 {len(self.filtered_packets)}/{len(self.packets)} 个包")
        
    def clear_filter(self):
        self.filter_var.set("")
        self.filtered_packets = list(enumerate(self.packets))
        self.display_packets()
        self.status_var.set(f"共 {len(self.packets)} 个包")
        
    def show_stats(self):
        if not self.packets:
            messagebox.showinfo("统计", "没有加载的数据包")
            return
            
        stats = {
            "total": len(self.packets),
            "tcp": 0,
            "udp": 0,
            "icmp": 0,
            "arp": 0,
            "other": 0,
            "size": sum(len(p) for p in self.packets)
        }
        
        for pkt in self.packets:
            if TCP in pkt:
                stats["tcp"] += 1
            elif UDP in pkt:
                stats["udp"] += 1
            elif ICMP in pkt:
                stats["icmp"] += 1
            elif ARP in pkt:
                stats["arp"] += 1
            else:
                stats["other"] += 1
                
        info = f"""流量统计信息:
        
总包数: {stats['total']}
总字节: {stats['size']} ({stats['size']/1024:.2f} KB)

协议分布:
  TCP:  {stats['tcp']} ({stats['tcp']/stats['total']*100:.1f}%)
  UDP:  {stats['udp']} ({stats['udp']/stats['total']*100:.1f}%)
  ICMP: {stats['icmp']} ({stats['icmp']/stats['total']*100:.1f}%)
  ARP:  {stats['arp']} ({stats['arp']/stats['total']*100:.1f}%)
  其他: {stats['other']} ({stats['other']/stats['total']*100:.1f}%)
"""
        messagebox.showinfo("统计信息", info)

if __name__ == "__main__":
    # 安装依赖提示
    try:
        from scapy.all import rdpcap
    except ImportError:
        print("请先安装依赖: pip install scapy")
        import sys
        sys.exit(1)
        
    root = tk.Tk()
    app = PcapAnalyzer(root)
    root.mainloop()