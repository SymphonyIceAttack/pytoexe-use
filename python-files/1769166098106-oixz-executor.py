import operator

class Executor:
    """
    Интерпретатор стековой машины.
    Выполняет инструкции из списка ПОЛИЗ (RPN).
    """
    def __init__(self, input_func=input, output_func=print):
        self.stack = []      
        self.variables = {}  
        
        # Функции ввода-вывода
        self.input_func = input_func
        self.output_func = output_func
        
        self.ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '<': operator.lt,
            '>': operator.gt,
            '=': operator.eq,
            '<>': operator.ne,
            '<=': operator.le,
            '>=': operator.ge,
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y,
        }

    def execute(self, rpn):
        pc = 0
        while pc < len(rpn):
            cmd = rpn[pc]
            pc += 1

            if isinstance(cmd, (int, float, bool)):
                self.stack.append(cmd)
            elif isinstance(cmd, str) and cmd not in self.ops and cmd not in ('as', 'read', 'write', '!', '!F', 'not'):
                self.stack.append(cmd)
            
            elif cmd == 'as':
                val = self.stack.pop()
                var_name = self.stack.pop()
                self.variables[var_name] = val
            
            elif cmd == 'read':
                var_name = self.stack.pop()
                try:
                    # Используем переданную функцию ввода
                    val_str = self.input_func(f"Введите значение для {var_name}:")
                    
                    if val_str is None: # Если нажали Отмена
                        raise ValueError("Input canceled")
                        
                    if '.' in val_str:
                        val = float(val_str)
                    else:
                        val = int(val_str)
                    self.variables[var_name] = val
                except ValueError:
                    self.output_func(f"Ошибка: Некорректный ввод для {var_name}")
                    self.variables[var_name] = 0

            elif cmd == 'write':
                val = self.stack.pop()
                if isinstance(val, str) and val in self.variables:
                    val = self.variables[val]
                # Используем переданную функцию вывода
                self.output_func(f"Output: {val}")

            elif cmd == '!':
                target_addr = self.stack.pop()
                pc = target_addr
            
            elif cmd == '!F':
                target_addr = self.stack.pop()
                cond = self.stack.pop()
                if isinstance(cond, str):
                    cond = self.variables[cond]
                if not cond:
                    pc = target_addr

            elif cmd in self.ops:
                right = self.stack.pop()
                left = self.stack.pop()
                if isinstance(right, str): right = self.variables[right]
                if isinstance(left, str): left = self.variables[left]
                res = self.ops[cmd](left, right)
                self.stack.append(res)

            elif cmd == 'not':
                val = self.stack.pop()
                if isinstance(val, str): val = self.variables[val]
                self.stack.append(not val)