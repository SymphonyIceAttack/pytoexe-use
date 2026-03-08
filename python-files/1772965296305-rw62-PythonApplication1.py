import tkinter as tk
from tkinter import ttk, messagebox

# ����������ã��Ƴ����ʣ������������������㣩
CURRENCY_CONFIG = {
    "��Ԫ": {
        "denominations": [50, 20, 10],
        "per_stack": 100  # 1��=100��
    },
    "ŷԪ": {
        "denominations": [50, 20, 10],
        "per_stack": 100
    },
    "��Ԫ": {
        "denominations": [5000, 1000],
        "per_stack": 100
    },
    "Ӣ��": {
        "denominations": [20, 10, 5],
        "per_stack": 100
    }
}

class CoinDeliveryCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("佱�ģ���� - �ֽ����ͼ�����")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)

        # �洢����ؼ��ı���
        self.task_amount_var = tk.StringVar()
        self.submitted_amount_var = tk.StringVar()
        self.currency_type_var = tk.StringVar(value="��Ԫ")
        
        # �洢������������������
        self.stack_vars = self._init_stack_vars()
        
        # ����UI
        self._build_ui()

    def _init_stack_vars(self):
        """��ʼ�����������������������"""
        stack_vars = {}
        for currency, config in CURRENCY_CONFIG.items():
            stack_vars[currency] = {}
            for denom in config["denominations"]:
                stack_vars[currency][denom] = tk.StringVar(value="0")
        return stack_vars

    def _build_ui(self):
        """��������"""
        # 1. ��������������
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="�����").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(top_frame, textvariable=self.task_amount_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(top_frame, text="�������ͣ�").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        currency_combobox = ttk.Combobox(
            top_frame, textvariable=self.currency_type_var, 
            values=list(CURRENCY_CONFIG.keys()), width=10, state="readonly"
        )
        currency_combobox.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(top_frame, text="���ύ��").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(top_frame, textvariable=self.submitted_amount_var, width=15).grid(row=0, column=5, padx=5, pady=5)

        # 2. ���������������
        stack_frame = ttk.LabelFrame(self.root, text="����ÿ��������������(1��=100��)��", padding="10")
        stack_frame.pack(fill=tk.X, padx=10, pady=10)

        # �����ҷ�����ʾ��������
        currencies = list(CURRENCY_CONFIG.keys())
        for col, currency in enumerate(currencies):
            ttk.Label(stack_frame, text=currency, font=("Arial", 10, "bold")).grid(row=0, column=col*2, padx=15, pady=5)
            config = CURRENCY_CONFIG[currency]
            for row, denom in enumerate(config["denominations"], 1):
                ttk.Label(stack_frame, text=f"{denom}{currency}").grid(row=row, column=col*2, padx=5, pady=3, sticky=tk.E)
                ttk.Entry(
                    stack_frame, textvariable=self.stack_vars[currency][denom], 
                    width=8, justify=tk.CENTER
                ).grid(row=row, column=col*2+1, padx=5, pady=3)

        # 3. ���ܰ�ť����
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame, text="����������", command=self.calculate_by_stack
        ).grid(row=0, column=0, padx=10, pady=5)
        
        ttk.Button(
            btn_frame, text="�����ύ������", command=self.calculate_by_submitted
        ).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Button(
            btn_frame, text="�������", command=self.clear_all_input
        ).grid(row=0, column=2, padx=10, pady=5)

        # 4. �����ʾ����
        result_note = ttk.Label(self.root, text="����������100������Ԫ��ŷԪ��10000������ԪΪ׼", foreground="gray")
        result_note.pack(padx=10, anchor=tk.W)

        # 4.1 ���ܽ������
        summary_frame = ttk.Frame(self.root, padding="10")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        summary_tree = ttk.Treeview(
            summary_frame, 
            columns=("state", "total_amount", "diff_amount", "diff_cards", "diff_stacks", "target_amount"),
            show="headings", height=1
        )
        summary_tree.heading("state", text="״̬")
        summary_tree.heading("total_amount", text="��ǰ�ܽ��")
        summary_tree.heading("diff_amount", text="�����")
        summary_tree.heading("diff_cards", text="�������")
        summary_tree.heading("diff_stacks", text="�������")
        summary_tree.heading("target_amount", text="Ŀ����")
        
        # �����п�
        for col in summary_tree["columns"]:
            summary_tree.column(col, width=120, anchor=tk.CENTER)
        summary_tree.pack(fill=tk.X)
        self.summary_tree = summary_tree

        # 4.2 �����ϸ����
        detail_frame = ttk.Frame(self.root, padding="10")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        detail_tree = ttk.Treeview(
            detail_frame,
            columns=("denomination", "cards", "stacks"),
            show="headings", height=max([len(config["denominations"]) for config in CURRENCY_CONFIG.values()])
        )
        detail_tree.heading("denomination", text="���")
        detail_tree.heading("cards", text="����")
        detail_tree.heading("stacks", text="����")
        
        detail_tree.column("denomination", width=150, anchor=tk.CENTER)
        detail_tree.column("cards", width=150, anchor=tk.CENTER)
        detail_tree.column("stacks", width=150, anchor=tk.CENTER)
        detail_tree.pack(fill=tk.BOTH, expand=True)
        self.detail_tree = detail_tree

        # ��ʼ����ϸ�����У���ѡ�еĻ������ͣ�
        self._init_detail_table()

    def _init_detail_table(self):
        """����ѡ�еĻ������ͳ�ʼ����ϸ����"""
        # ���ԭ����ϸ
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        # ��ȡ��ǰѡ�еĻ�������
        current_currency = self.currency_type_var.get()
        # �����Ӧ������
        for denom in CURRENCY_CONFIG[current_currency]["denominations"]:
            self.detail_tree.insert("", tk.END, values=(f"{denom}{current_currency}", "0.00", "0.00"))
        # �󶨻������ͱ���¼�
        self.currency_type_var.trace_add("write", lambda *args: self._init_detail_table())

    def _get_numeric_value(self, var):
        """��ȫ��ȡ��ֵ��������ֵ/�����֣�"""
        try:
            return float(var.get().strip() or 0)
        except ValueError:
            return 0.0

    def calculate_by_stack(self):
        """������������������ܽ����ȣ��޻��ʣ�"""
        # 1. ��ȡ��ǰѡ�еĻ�������
        current_currency = self.currency_type_var.get()
        config = CURRENCY_CONFIG[current_currency]
        
        # 2. ����ѡ�л��ҵ��ܽ���������
        total_amount = 0.0
        # �ȼ���ѡ�л��ҵ�������Ӧ�Ľ��
        for denom, var in self.stack_vars[current_currency].items():
            stack_num = self._get_numeric_value(var)
            # ���� -> ���� -> ���
            amount = stack_num * config["per_stack"] * denom
            total_amount += amount

        # 3. ��ȡ������
        task_amount = self._get_numeric_value(self.task_amount_var)

        # 4. ������
        diff_amount = task_amount - total_amount
        
        # ����������������Ӧ������Ԫ/ŷԪ��100����Ԫ��10000��Ӣ����100��
        if current_currency == "��Ԫ":
            diff_cards = diff_amount / 10000 if diff_amount >= 0 else 0
        else:
            diff_cards = diff_amount / 100 if diff_amount >= 0 else 0
        diff_stacks = diff_cards / 100  # 1��=100��

        # 5. ���»��ܱ���
        self._update_summary_table(
            state="����������",
            total_amount=f"{total_amount:.2f}{current_currency}",
            diff_amount=f"{diff_amount:.2f}{current_currency}",
            diff_cards=f"{diff_cards:.2f}",
            diff_stacks=f"{diff_stacks:.2f}",
            target_amount=f"{task_amount:.2f}{current_currency}"
        )

        # 6. ������ϸ���񣨰���ǰ��������ֲ�
        self._update_detail_table(diff_amount, current_currency)

    def calculate_by_submitted(self):
        """�������ύ��������޻��ʣ�"""
        # 1. ��ȡ��ǰѡ�еĻ�������
        current_currency = self.currency_type_var.get()
        
        # 2. ��ȡ���ύ����������
        submitted_amount = self._get_numeric_value(self.submitted_amount_var)
        task_amount = self._get_numeric_value(self.task_amount_var)

        # 3. ������
        diff_amount = task_amount - submitted_amount
        
        # ����������������Ӧ����
        if current_currency == "��Ԫ":
            diff_cards = diff_amount / 10000 if diff_amount >= 0 else 0
        else:
            diff_cards = diff_amount / 100 if diff_amount >= 0 else 0
        diff_stacks = diff_cards / 100

        # 4. ���»��ܱ���
        self._update_summary_table(
            state="�����ύ������",
            total_amount=f"{submitted_amount:.2f}{current_currency}",
            diff_amount=f"{diff_amount:.2f}{current_currency}",
            diff_cards=f"{diff_cards:.2f}",
            diff_stacks=f"{diff_stacks:.2f}",
            target_amount=f"{task_amount:.2f}{current_currency}"
        )

        # 5. ������ϸ����
        self._update_detail_table(diff_amount, current_currency)

    def _update_summary_table(self, state, total_amount, diff_amount, diff_cards, diff_stacks, target_amount):
        """���»��ܽ������"""
        # ���ԭ������
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        # ����������
        self.summary_tree.insert(
            "", tk.END,
            values=(state, total_amount, diff_amount, diff_cards, diff_stacks, target_amount)
        )

    def _update_detail_table(self, diff_amount, current_currency):
        """����ǰ��������ֲ�������ϸ����"""
        # ���ԭ����ϸ
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        
        remaining = diff_amount if diff_amount >= 0 else 0
        denominations = CURRENCY_CONFIG[current_currency]["denominations"]

        # �����Ӵ�С���
        for denom in denominations:
            # �������������
            cards = remaining // denom
            stacks = cards / 100  # ת��Ϊ����
            # ������ϸ��
            self.detail_tree.insert(
                "", tk.END,
                values=(f"{denom}{current_currency}", f"{cards:.2f}", f"{stacks:.2f}")
            )
            # ʣ����
            remaining -= cards * denom

    def clear_all_input(self):
        """������������"""
        self.task_amount_var.set("")
        self.submitted_amount_var.set("")
        self.currency_type_var.set("��Ԫ")
        
        # ���������������
        for currency in self.stack_vars.values():
            for var in currency.values():
                var.set("0")
        
        # ��ս������
        self._update_summary_table("", "", "", "", "", "")
        # ���³�ʼ����ϸ��
        self._init_detail_table()

        messagebox.showinfo("��ʾ", "������������գ�")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoinDeliveryCalculator(root)
    root.mainloop()