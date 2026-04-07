import tkinter as tk
from tkinter import filedialog, messagebox
import scapy.all as scapy
from scapy.layers.inet import IP, TCP, UDP
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PCAPAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("PCAP Analyzer")
        self.root.geometry("1200x800")
        self.file_path = None
        self.packets = []
        self.create_widgets()

    def create_widgets(self):
        # 文件选择
        file_frame = tk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(file_frame, text="打开PCAP文件", command=self.open_pcap).pack()

        # 数据包列表
        packet_listbox = tk.Listbox(self.root, width=100)
        packet_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        packet_listbox.bind('<<ListboxSelect>>', self.show_packet_details)

        # 数据包详情
        details_text = tk.Text(self.root, height=10, wrap=tk.WORD)
        details_text.pack(fill=tk.X, padx=10, pady=10)
        details_text.config(state=tk.DISABLED)

        # 分析可视化
        analysis_frame = tk.Frame(self.root)
        analysis_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(analysis_frame, text="分析流量", command=self.analyze_traffic).pack()

        figure = plt.Figure(figsize=(6,5), dpi=100)
        ax = figure.add_subplot(111)
        canvas = FigureCanvasTkAgg(figure, analysis_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 编辑按钮
        edit_frame = tk.Frame(self.root)
        edit_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(edit_frame, text="复制数据包", command=self.copy_packet).pack(side=tk.LEFT, padx=5)
        tk.Button(edit_frame, text="删除数据包", command=self.delete_packet).pack(side=tk.LEFT, padx=5)
        tk.Button(edit_frame, text="保存修改", command=self.save_changes).pack(side=tk.LEFT, padx=5)

    def open_pcap(self):
        self.file_path = filedialog.askopenfilename(title="打开PCAP文件", filetypes=[("PCAP文件", "*.pcap *.pcapng")])
        if self.file_path:
            self.load_pcap()

    def load_pcap(self):
        try:
            self.packets = scapy.rdpcap(self.file_path)
            self.update_packet_list()
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")

    def update_packet_list(self):
        self.packet_listbox.delete(0, tk.END)
        for packet in self.packets:
            if IP in packet:
                item = f"{packet[IP].src} → {packet[IP].dst} ({len(packet)}字节)"
            else:
                item = f"未知协议 ({len(packet)}字节)"
            self.packet_listbox.insert(tk.END, item)

    def show_packet_details(self, event):
        if not self.packet_listbox.curselection(): return
        index = self.packet_listbox.curselection()[0]
        packet = self.packets[index]
        details = f"数据包详情:\n长度: {len(packet)}字节\n"
        if IP in packet:
            details += f"源IP: {packet[IP].src}\n目标IP: {packet[IP].dst}\n"
            if TCP in packet:
                details += f"源端口: {packet[TCP].sport}\n目标端口: {packet[TCP].dport}\n"
            elif UDP in packet:
                details += f"源端口: {packet[UDP].sport}\n目标端口: {packet[UDP].dport}\n"
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.details_text.config(state=tk.DISABLED)

    def analyze_traffic(self):
        if not self.packets: return
        protocols = {}
        for packet in self.packets:
            proto = "TCP" if TCP in packet else "UDP" if UDP in packet else "IP" if IP in packet else "其他"
            protocols[proto] = protocols.get(proto, 0) + 1
        
        # 绘制协议分布图
        self.ax.clear()
        self.ax.pie(protocols.values(), labels=protocols.keys(), autopct='%1.1f%%')
        self.ax.set_title("协议分布")
        self.canvas.draw()

    def copy_packet(self):
        if not self.packet_listbox.curselection(): return
        index = self.packet_listbox.curselection()[0]
        self.copied_packet = self.packets[index]
        messagebox.showinfo("提示", "数据包已复制到剪贴板")

    def delete_packet(self):
        if not self.packet_listbox.curselection(): return
        index = self.packet_listbox.curselection()[0]
        self.packets.pop(index)
        self.update_packet_list()
        messagebox.showinfo("提示", "数据包已删除")

    def save_changes(self):
        if not self.file_path: return
        try:
            scapy.wrpcap(self.file_path, self.packets)
            messagebox.showinfo("成功", "修改已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PCAPAnalyzer(root)
    root.mainloop()
