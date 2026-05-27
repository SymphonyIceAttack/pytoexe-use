class TuringMachine:
    def __init__(self, initial_tape, transition_rules,
                 initial_state='q0',
                 accept_state='q_accept',
                 reject_state='q_reject',
                 blank='_'):
        # 纸带：使用字典支持真正的无限长纸带（左右都能扩展）
        self.tape = {}
        # 初始化纸带内容
        for i, symbol in enumerate(initial_tape):
            self.tape[i] = symbol
        self.head_position = 0  # 读写头位置
        self.current_state = initial_state
        self.rules = transition_rules
        self.accept = accept_state
        self.reject = reject_state
        self.blank = blank  # 空白符号

    def get_current_symbol(self):
        # 获取当前读写头指向的符号，没有则返回空白
        return self.tape.get(self.head_position, self.blank)

    def write_symbol(self, symbol):
        # 在当前位置写入符号
        self.tape[self.head_position] = symbol

    def move_head(self, direction):
        # 移动读写头 L=左 R=右 N=不动
        if direction == 'L':
            self.head_position -= 1
        elif direction == 'R':
            self.head_position += 1

    def step(self):
        # 执行一步
        current_symbol = self.get_current_symbol()
        key = (self.current_state, current_symbol)

        # 无规则匹配 → 进入拒绝状态
        if key not in self.rules:
            self.current_state = self.reject
            return

        # 读取规则
        new_symbol, move_dir, new_state = self.rules[key]

        # 执行操作
        self.write_symbol(new_symbol)
        self.move_head(move_dir)
        self.current_state = new_state

    def get_tape_contents(self):
        # 把纸带字典转换成字符串用于显示
        if not self.tape:
            return self.blank

        min_pos = min(self.tape.keys())
        max_pos = max(self.tape.keys())
        result = []
        for pos in range(min_pos, max_pos + 1):
            result.append(self.tape.get(pos, self.blank))
        return ''.join(result)

    def print_state(self):
        # 打印当前状态
        tape_str = self.get_tape_contents()
        min_pos = min(self.tape.keys()) if self.tape else 0
        head_index = self.head_position - min_pos
        head_mark = ' ' * head_index + '↑'
        print(f"纸带: {tape_str}")
        print(f"读写头: {head_mark}")
        print(f"状态: {self.current_state}\n")

    def run(self, delay=0.5):
        # 运行图灵机直到停机
        print("=" * 30)
        print("      图灵机开始运行")
        print("=" * 30)
        step = 0

        while True:
            print(f"--- 步骤 {step} ---")
            self.print_state()

            # 终止条件
            if self.current_state == self.accept:
                print("✅ 成功停机：计算完成！")
                break
            if self.current_state == self.reject:
                print("❌ 失败停机：无匹配规则！")
                break

            self.step()
            step += 1

        print("=" * 30)
        print(f"最终纸带: {self.get_tape_contents()}")
        print("=" * 30)


# =========================
# 【你可以自由自定义的区域】
# =========================

if __name__ == '__main__':
    # ========== 示例1：二进制数 1+1 = 10（最经典演示）==========
    # 初始纸带
    tape = ['1', '+', '1']

    # 转移规则：(当前状态, 当前符号) → (写入符号, 移动方向, 新状态)
    rules = {
        ('q0', '1'): ('1', 'R', 'q0'),
        ('q0', '+'): ('+', 'R', 'q1'),
        ('q1', '1'): ('0', 'L', 'q2'),
        ('q2', '+'): ('1', 'L', 'q3'),
        ('q3', '1'): ('1', 'R', 'q_accept'),
    }

    # ========== 示例2：判断二进制数是否为偶数 ==========
    # tape = ['1', '0', '1', '0']
    # rules = {
    #     ('q0', '0'): ('0', 'N', 'q_accept'),
    #     ('q0', '1'): ('1', 'N', 'q_reject'),
    # }

    # ========== 示例3：清空纸带 ==========
    # tape = ['a', 'b', 'c', '1', '2', '3']
    # rules = {
    #     ('q0', 'a'): ('_', 'R', 'q0'),
    #     ('q0', 'b'): ('_', 'R', 'q0'),
    #     ('q0', 'c'): ('_', 'R', 'q0'),
    #     ('q0', '1'): ('_', 'R', 'q0'),
    #     ('q0', '2'): ('_', 'R', 'q0'),
    #     ('q0', '3'): ('_', 'R', 'q0'),
    #     ('q0', '_'): ('_', 'N', 'q_accept'),
    # }

    # 创建并运行
    tm = TuringMachine(
        initial_tape=tape,
        transition_rules=rules
    )
    tm.run()

