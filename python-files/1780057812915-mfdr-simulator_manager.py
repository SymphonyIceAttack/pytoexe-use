import os
import subprocess
import time
import threading
from datetime import datetime, timedelta

# 配置参数（已修改为您的实际路径）
LD_PATH = r"D:\leidian\LDPlayer4"  # 已修改为您的实际路径
CONSOLE_PATH = os.path.join(LD_PATH, "ldconsole.exe")
TOTAL_SIMULATORS = 140
GROUP_SIZE = 4
TARGET_COUNT = 28
RUN_TIME = 288  # 运行分钟数
START_INTERVAL = 4  # 组间启动间隔（分钟）
INFINITE_LOOP = True  # 设置为True表示无限循环运行

class SimulatorManager:
    def __init__(self):
        self.running_simulators = {}  # {index: start_time}
        self.lock = threading.Lock()
        self.cycle_count = 0  # 循环次数计数器
        
    def get_simulator_list(self):
        """获取所有模拟器列表"""
        result = subprocess.run(
            [CONSOLE_PATH, "list2"],
            capture_output=True, text=True
        )
        instances = []
        for item in result.stdout.strip().split(';'):
            if not item:
                continue
            fields = {}
            for kv in item.split(','):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    fields[k] = v
            if 'index' in fields:
                instances.append(fields)
        return instances

    def get_running_count(self):
        """获取当前运行的模拟器数量（排除0号）"""
        instances = self.get_simulator_list()
        count = 0
        for inst in instances:
            index = int(inst.get('index', -1))
            status = int(inst.get('status', 0))
            if index > 0 and status == 1:  # index>0排除0号，status=1表示运行中
                count += 1
        return count

    def start_simulator(self, index):
        """启动指定索引的模拟器"""
        try:
            subprocess.run([CONSOLE_PATH, "launch", "--index", str(index)])
            print(f"已启动模拟器 {index}")
        except Exception as e:
            print(f"启动模拟器 {index} 失败: {e}")

    def stop_simulator(self, index):
        """关闭指定索引的模拟器"""
        try:
            subprocess.run([CONSOLE_PATH, "quit", "--index", str(index)])
            print(f"已关闭模拟器 {index}")
        except Exception as e:
            print(f"关闭模拟器 {index} 失败: {e}")

    def force_stop(self, index):
        """强制关闭模拟器（通过进程）"""
        try:
            os.system(f"taskkill /f /im LDPlayer.exe /fi \"windowtitle eq 模拟器{index}\"")
            print(f"强制关闭模拟器 {index}")
        except Exception as e:
            print(f"强制关闭模拟器 {index} 失败: {e}")

    def check_and_close_timeout(self):
        """检测并关闭运行超时的模拟器"""
        while True:
            time.sleep(60)  # 每分钟检测一次
            current_time = datetime.now()
            with self.lock:
                to_remove = []
                for index, start_time in self.running_simulators.items():
                    elapsed = (current_time - start_time).total_seconds() / 60
                    if elapsed >= RUN_TIME:
                        print(f"模拟器 {index} 已运行 {elapsed:.1f} 分钟，准备关闭")
                        # 尝试正常关闭
                        self.stop_simulator(index)
                        time.sleep(5)
                        # 检查是否关闭成功
                        instances = self.get_simulator_list()
                        still_running = any(
                            int(inst.get('index', -1)) == index and 
                            int(inst.get('status', 0)) == 1 
                            for inst in instances
                        )
                        if still_running:
                            print(f"模拟器 {index} 正常关闭失败，强制关闭")
                            self.force_stop(index)
                        to_remove.append(index)
                
                for index in to_remove:
                    del self.running_simulators[index]
                    print(f"模拟器 {index} 已移除运行列表")

    def maintain_target_count(self):
        """维持模拟器数量在28个"""
        while True:
            time.sleep(120)  # 每2分钟检查一次
            current_count = self.get_running_count()
            print(f"当前运行模拟器数量: {current_count}")
            
            if current_count < TARGET_COUNT:
                need_count = TARGET_COUNT - current_count
                print(f"需要补充 {need_count} 个模拟器")
                
                # 获取所有模拟器状态
                instances = self.get_simulator_list()
                not_running = []
                for inst in instances:
                    index = int(inst.get('index', -1))
                    status = int(inst.get('status', 0))
                    if index > 0 and status == 0:  # 未运行的模拟器
                        not_running.append(index)
                
                # 按分组顺序启动，每组启动后间隔4分钟
                not_running.sort()
                group_start_count = 0
                for start_idx in range(0, len(not_running), GROUP_SIZE):
                    if group_start_count >= need_count:
                        break
                    
                    group = not_running[start_idx:start_idx + GROUP_SIZE]
                    for idx in group:
                        if group_start_count >= need_count:
                            break
                        self.start_simulator(idx)
                        with self.lock:
                            self.running_simulators[idx] = datetime.now()
                        group_start_count += 1
                    
                    if group_start_count < need_count:
                        print(f"等待 {START_INTERVAL} 分钟后启动下一组")
                        time.sleep(START_INTERVAL * 60)

    def start_initial_batch(self):
        """初始启动28个模拟器（按组启动，间隔4分钟）"""
        print("开始初始启动流程...")
        
        # 获取未运行的模拟器列表
        instances = self.get_simulator_list()
        not_running = [
            int(inst.get('index', -1)) 
            for inst in instances 
            if int(inst.get('index', -1)) > 0 and int(inst.get('status', 0)) == 0
        ]
        not_running.sort()
        
        # 按组启动，直到达到28个
        started_count = 0
        for start_idx in range(0, len(not_running), GROUP_SIZE):
            if started_count >= TARGET_COUNT:
                break
            
            group = not_running[start_idx:start_idx + GROUP_SIZE]
            print(f"启动第 {start_idx // GROUP_SIZE + 1} 组: {group}")
            
            for idx in group:
                if started_count >= TARGET_COUNT:
                    break
                self.start_simulator(idx)
                with self.lock:
                    self.running_simulators[idx] = datetime.now()
                started_count += 1
                time.sleep(2)  # 单个模拟器启动间隔
            
            # 等待4分钟后启动下一组
            if started_count < TARGET_COUNT:
                print(f"已启动 {started_count} 个，等待 {START_INTERVAL} 分钟后启动下一组")
                time.sleep(START_INTERVAL * 60)
        
        print(f"初始启动完成，共启动 {started_count} 个模拟器")
        return started_count

    def arrange_windows(self):
        """使用雷电多开器排列窗口"""
        try:
            subprocess.run([CONSOLE_PATH, "arrange"])
            print("已执行窗口排列")
        except Exception as e:
            print(f"窗口排列失败: {e}")

    def stop_all_simulators(self):
        """停止所有模拟器"""
        print("正在停止所有模拟器...")
        try:
            subprocess.run([CONSOLE_PATH, "quitall"])
            print("已发送关闭所有模拟器命令")
        except Exception as e:
            print(f"关闭所有模拟器失败: {e}")
        
        # 强制关闭残留进程
        time.sleep(10)
        try:
            os.system("taskkill /f /im LDPlayer.exe 2>nul")
            os.system("taskkill /f /im dnplayer.exe 2>nul")
            os.system("taskkill /f /im adb.exe 2>nul")
            print("已强制关闭残留进程")
        except:
            pass
        
        with self.lock:
            self.running_simulators.clear()

    def run_one_cycle(self):
        """运行一个完整的周期"""
        self.cycle_count += 1
        print(f"\n{'='*60}")
        print(f"=== 开始第 {self.cycle_count} 个运行周期 ===")
        print(f"{'='*60}")
        
        # 启动检测超时线程
        timeout_thread = threading.Thread(target=self.check_and_close_timeout, daemon=True)
        timeout_thread.start()
        
        # 启动数量维持线程
        maintain_thread = threading.Thread(target=self.maintain_target_count, daemon=True)
        maintain_thread.start()
        
        # 初始启动
        started = self.start_initial_batch()
        
        # 排列窗口
        time.sleep(10)
        self.arrange_windows()
        
        # 等待所有模拟器运行完成
        print(f"等待所有模拟器运行 {RUN_TIME} 分钟...")
        while True:
            time.sleep(60)
            with self.lock:
                if len(self.running_simulators) == 0:
                    print("所有模拟器已完成运行")
                    break
                current_count = self.get_running_count()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 运行中: {current_count} 个")
        
        # 确保所有模拟器都已关闭
        time.sleep(30)
        self.stop_all_simulators()
        time.sleep(10)
        
        print(f"\n第 {self.cycle_count} 个运行周期完成!")
        return True

    def run(self):
        """主运行函数（支持无限循环）"""
        print("=== 雷电模拟器自动化管理程序启动 ===")
        print(f"目标数量: {TARGET_COUNT} | 运行时间: {RUN_TIME}分钟 | 组间隔: {START_INTERVAL}分钟")
        print(f"无限循环模式: {INFINITE_LOOP}")
        
        if INFINITE_LOOP:
            print("程序将以无限循环模式运行，按 Ctrl+C 可手动停止")
            while True:
                self.run_one_cycle()
                print(f"\n等待 5 分钟后开始下一个周期...")
                time.sleep(300)  # 周期之间等待5分钟
        else:
            self.run_one_cycle()
            
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            self.stop_all_simulators()

if __name__ == "__main__":
    manager = SimulatorManager()
    manager.run()
