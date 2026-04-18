import easygui as gui

gui.msgbox("欢迎来到全能计算器！", "全能计算器v2.0", "好的")

while True:
    a = gui.buttonbox('你要选择什么功能？', choices=('加减乘除', '方程式', '退出'))

    if a == '加减乘除':
        op = gui.buttonbox('请选择要进行的运算', choices=('加法', '减法', '乘法', '除法'))
        
        if op is None:
            continue

        nums = []
        gui.msgbox("开始输入数字，输入 exit 结束输入", "提示", "开始")

        while True:
            num_str = gui.enterbox(f"已输入 {len(nums)} 个数字\n请输入下一个数字（输入 exit 结束）：", "连续输入")
            
            if num_str is None or num_str.strip().lower() == "exit":
                break
            
            try:
                num = float(num_str)
                nums.append(num)
            except ValueError:
                gui.msgbox("输入无效，请输入数字或 exit！", "错误", "知道了")
                continue

        if len(nums) < 2:
            gui.msgbox("至少需要输入 2 个数字才能计算！", "提示", "返回")
            continue

        result = 0
        valid = True
        
        if op == '加法':
            result = sum(nums)
        elif op == '减法':
            result = nums[0]
            for num in nums[1:]:
                result -= num
        elif op == '乘法':
            result = 1
            for num in nums:
                result *= num
        elif op == '除法':
            result = nums[0]
            for num in nums[1:]:
                if num == 0:
                    gui.msgbox("除数不能为0！", "错误", "知道了")
                    valid = False
                    break
                result /= num
            if not valid:
                continue

        gui.msgbox(f"计算结果：{result}", "结果", "好的")

    elif a == '方程式':
        eq = gui.enterbox("请输入方程，例如 2x+3=7、x^2+2x+1=0", "解方程")
        
        if eq is None:
            continue
            
        try:
            eq = eq.replace('²','^2').replace('×','*').replace('÷','/')
            left, right = eq.split('=')
            left = left.replace('x','*x').replace('*-','-').replace('+*-','-')
            right = right.replace('x','*x').replace('*-','-').replace('+*-','-')
            expr = f"({left})-({right})"
            
            def calc(x_val):
                return eval(expr.replace('x',str(x_val)))
            
            b = calc(0)
            k = calc(1)-b
            sol_list = []
            
            if k == 0:
                if b == 0:
                    gui.msgbox("方程有无数解", "结果", "好的")
                else:
                    gui.msgbox("方程无解", "结果", "好的")
            else:
                x = -b/k
                gui.msgbox(f"方程解：x = {x}", "结果", "好的")
        except:
            gui.msgbox("输入格式错误", "错误", "知道了")

    elif a == '退出' or a is None:
        gui.msgbox("感谢使用全能计算器，再见！", "再见", "拜拜")
        break
