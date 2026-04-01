import tkinter as tk
from tkinter import ttk, messagebox

# 属性克制数据
EFFECTIVE_AGAINST = {
    "火": ["草", "机械", "虫"], "水": ["火", "石", "土"], "草": ["水", "土", "石"],
    "石": ["飞行", "火"], "土": ["火", "石", "毒", "机械", "电"], "毒": ["草", "萌"],
    "飞行": ["草", "虫"], "超能": ["毒", "萌"], "幽灵": ["萌", "幽灵"],
    "电": ["水", "飞行"], "冰": ["草", "龙", "土"]
}

WEAK_TO = {
    "火": ["水", "土", "石"], "水": ["草", "电"], "草": ["火", "飞行"],
    "石": ["普通", "飞行", "毒", "火"], "土": ["水", "草", "土"], "毒": ["水", "草", "土"],
    "飞行": ["水", "土", "火"], "超能": ["毒", "幽灵"], "幽灵": ["幽灵"],
    "电": ["土"], "冰": ["火", "石"]
}

class TypeCalcApp:
    def __init__(self, root):
        self.root = root
        self.root.title("属性克制计算器")
        self.root.geometry("400x500")
        
        ttk.Label(root, text="请勾选 1~3 个属性:", font=("微软雅黑", 11)).pack(pady=10)
        
        self.container = ttk.Frame(root)
        self.container.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.type_vars = {}
        all_types = sorted(list(set(list(EFFECTIVE_AGAINST.keys()) + ["普通", "机械", "虫", "龙"])))
        
        for i, t in enumerate(all_types):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.container, text=t, variable=var, command=self.calculate)
            chk.grid(row=i//4, column=i%4, sticky="w", padx=5, pady=2)
            self.type_vars[t] = var
            
        self.result_text = tk.Text(root, height=10, width=45)
        self.result_text.pack(pady=10, padx=10)

    def calculate(self):
        selected = [t for t, var in self.type_vars.items() if var.get()]
        if len(selected) > 3:
            self.type_vars[selected[-1]].set(False)
            messagebox.showwarning("限制", "最多只能选择 3 个属性！")
            return
        
        if not selected:
            self.result_text.delete(1.0, tk.END)
            return
            
        atk_map = {}
        def_map = {}
        for t in selected:
            for target in EFFECTIVE_AGAINST.get(t, []):
                atk_map[target] = atk_map.get(target, 1) * 2
            for attacker in WEAK_TO.get(t, []):
                def_map[attacker] = def_map.get(attacker, 1) * 2

        res = f"所选: {' + '.join(selected)}\n" + "-"*30 + "\n"
        res += "【克制对方】\n"
        for t, m in atk_map.items():
            res += f"  → {t}: {m}倍\n"
        res += "\n【被克制】\n"
        for t, m in def_map.items():
            res += f"  ← {t}: {m}倍\n"
            
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, res)

if __name__ == "__main__":
    root = tk.Tk()
    app = TypeCalcApp(root)
    root.mainloop()
