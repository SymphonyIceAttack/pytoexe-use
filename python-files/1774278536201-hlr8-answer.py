import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List


class SimpleCrypto:
    """简单的XOR加密类"""

    def __init__(self):
        self.key = "admin"

    def encrypt(self, data: str) -> str:
        """加密/解密（XOR对称加密）"""
        result = []
        for i, ch in enumerate(data):
            result.append(chr(ord(ch) ^ ord(self.key[i % len(self.key)])))
        return ''.join(result)

    def decrypt(self, data: str) -> str:
        return self.encrypt(data)


class PasswordEntry:
    """密码条目类"""

    def __init__(self, entry_id: int = 0, platform: str = "", account: str = "", password: str = ""):
        self.id = entry_id
        self.platform = platform
        self.account = account
        self.password = password

    def to_string(self) -> str:
        return f"{self.id}|{self.platform}|{self.account}|{self.password}"

    @staticmethod
    def from_string(data: str):
        parts = data.split('|')
        if len(parts) >= 4:
            return PasswordEntry(
                entry_id=int(parts[0]),
                platform=parts[1],
                account=parts[2],
                password=parts[3]
            )
        return PasswordEntry()


class PasswordManagerApp:
    """图形化密码管理器"""

    def __init__(self):
        self.entries: List[PasswordEntry] = []
        self.crypto = SimpleCrypto()
        self.filename = "answer.txt"
        self.pwd_file = "password.txt"
        self.access_password = ""

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("密码管理器")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # 加载数据
        self._load_password()
        self._load_from_file()

        # 显示登录对话框
        self._show_login()

    def _reorder_ids(self):
        """重新排序ID"""
        for i, entry in enumerate(self.entries):
            entry.id = i + 1
        self._save_to_file()

    def _load_password(self):
        """加载访问密码"""
        try:
            with open(self.pwd_file, 'r', encoding='utf-8') as f:
                encrypted = f.read().strip()
                self.access_password = self.crypto.decrypt(encrypted)
        except FileNotFoundError:
            self.access_password = "admin"
            self._save_password()

    def _save_password(self):
        """保存访问密码"""
        with open(self.pwd_file, 'w', encoding='utf-8') as f:
            f.write(self.crypto.encrypt(self.access_password))

    def _load_from_file(self):
        """从文件加载数据"""
        self.entries.clear()
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        decrypted = self.crypto.decrypt(line)
                        self.entries.append(
                            PasswordEntry.from_string(decrypted))
        except FileNotFoundError:
            pass

    def _save_to_file(self):
        """保存数据到文件"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            for entry in self.entries:
                f.write(self.crypto.encrypt(entry.to_string()) + '\n')

    def _show_login(self):
        """显示登录对话框"""
        login_dialog = tk.Toplevel(self.root)
        login_dialog.title("身份验证")
        login_dialog.geometry("300x150")
        login_dialog.transient(self.root)
        login_dialog.grab_set()

        # 居中显示
        login_dialog.update_idletasks()
        x = (login_dialog.winfo_screenwidth() // 2) - \
            (login_dialog.winfo_width() // 2)
        y = (login_dialog.winfo_screenheight() // 2) - \
            (login_dialog.winfo_height() // 2)
        login_dialog.geometry(f"+{x}+{y}")

        tk.Label(login_dialog, text="请输入访问密码",
                 font=("Arial", 12)).pack(pady=15)
        tk.Label(login_dialog, text="默认密码: admin", fg="gray").pack()

        pwd_entry = tk.Entry(login_dialog, show="*",
                             width=25, font=("Arial", 10))
        pwd_entry.pack(pady=10)
        pwd_entry.focus()

        def verify():
            password = pwd_entry.get()
            if password == self.access_password:
                login_dialog.destroy()
                self._create_main_interface()
            else:
                messagebox.showerror("错误", "密码错误！")
                login_dialog.destroy()
                self.root.quit()

        def on_enter(event):
            verify()

        pwd_entry.bind('<Return>', on_enter)
        tk.Button(login_dialog, text="确定",
                  command=verify, width=10).pack(pady=5)

    def _create_main_interface(self):
        """创建主界面"""
        # 菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        password_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="密码管理", menu=password_menu)
        password_menu.add_command(label="添加密码", command=self._add_entry)
        password_menu.add_command(label="修改密码", command=self._modify_entry)
        password_menu.add_command(label="删除密码", command=self._delete_entry)
        password_menu.add_separator()
        password_menu.add_command(
            label="修改访问密码", command=self._change_password)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

        # 工具栏
        toolbar = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="添加", command=self._add_entry,
                  width=8).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="修改", command=self._modify_entry,
                  width=8).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="删除", command=self._delete_entry,
                  width=8).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="刷新", command=self._refresh_display,
                  width=8).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="修改密码", command=self._change_password,
                  width=10).pack(side=tk.RIGHT, padx=2, pady=2)

        # 创建Treeview表格
        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(self.tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 表格
        columns = ("id", "platform", "account", "password")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings",
                                 yscrollcommand=scrollbar.set, height=20)
        scrollbar.config(command=self.tree.yview)

        # 设置列标题
        self.tree.heading("id", text="序号")
        self.tree.heading("platform", text="平台")
        self.tree.heading("account", text="账号")
        self.tree.heading("password", text="密码")

        # 设置列宽
        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("platform", width=180, anchor=tk.W)
        self.tree.column("account", width=180, anchor=tk.W)
        self.tree.column("password", width=200, anchor=tk.W)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # 绑定双击事件
        self.tree.bind("<Double-Button-1>", self._on_double_click)

        # 状态栏
        self.statusbar = tk.Label(
            self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 刷新显示
        self._refresh_display()

    def _refresh_display(self):
        """刷新表格显示"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 插入数据
        for entry in self.entries:
            self.tree.insert("", tk.END, values=(
                entry.id, entry.platform, entry.account, entry.password))

        self.statusbar.config(text=f"共 {len(self.entries)} 条记录")

    def _add_entry(self):
        """添加密码条目"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加密码")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - \
            (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - \
            (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="平台:", font=("Arial", 10)).place(x=50, y=30)
        platform_entry = tk.Entry(dialog, width=30)
        platform_entry.place(x=120, y=30)

        tk.Label(dialog, text="账号:", font=("Arial", 10)).place(x=50, y=80)
        account_entry = tk.Entry(dialog, width=30)
        account_entry.place(x=120, y=80)

        tk.Label(dialog, text="密码:", font=("Arial", 10)).place(x=50, y=130)
        password_entry = tk.Entry(dialog, width=30)
        password_entry.place(x=120, y=130)

        def save():
            platform = platform_entry.get().strip()
            account = account_entry.get().strip()
            password = password_entry.get().strip()

            if not platform or not account or not password:
                messagebox.showwarning("警告", "请填写完整信息！")
                return

            new_entry = PasswordEntry()
            new_entry.id = len(self.entries) + 1
            new_entry.platform = platform
            new_entry.account = account
            new_entry.password = password

            self.entries.append(new_entry)
            self._save_to_file()
            self._refresh_display()
            dialog.destroy()
            self.statusbar.config(text=f"添加成功！共 {len(self.entries)} 条记录")

        tk.Button(dialog, text="确定", command=save,
                  width=10).place(x=120, y=190)
        tk.Button(dialog, text="取消", command=dialog.destroy,
                  width=10).place(x=220, y=190)

    def _modify_entry(self):
        """修改密码条目"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要修改的记录！")
            return

        item = self.tree.item(selected[0])
        values = item['values']
        if not values:
            return

        entry_id = values[0]

        # 查找对应的条目
        target_entry = None
        for entry in self.entries:
            if entry.id == entry_id:
                target_entry = entry
                break

        if not target_entry:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("修改密码")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - \
            (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - \
            (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="平台:", font=("Arial", 10)).place(x=50, y=30)
        platform_entry = tk.Entry(dialog, width=30)
        platform_entry.place(x=120, y=30)
        platform_entry.insert(0, target_entry.platform)

        tk.Label(dialog, text="账号:", font=("Arial", 10)).place(x=50, y=80)
        account_entry = tk.Entry(dialog, width=30)
        account_entry.place(x=120, y=80)
        account_entry.insert(0, target_entry.account)

        tk.Label(dialog, text="密码:", font=("Arial", 10)).place(x=50, y=130)
        password_entry = tk.Entry(dialog, width=30)
        password_entry.place(x=120, y=130)
        password_entry.insert(0, target_entry.password)

        def save():
            platform = platform_entry.get().strip()
            account = account_entry.get().strip()
            password = password_entry.get().strip()

            if not platform or not account or not password:
                messagebox.showwarning("警告", "请填写完整信息！")
                return

            target_entry.platform = platform
            target_entry.account = account
            target_entry.password = password

            self._save_to_file()
            self._refresh_display()
            dialog.destroy()
            self.statusbar.config(text="修改成功！")

        tk.Button(dialog, text="确定", command=save,
                  width=10).place(x=120, y=190)
        tk.Button(dialog, text="取消", command=dialog.destroy,
                  width=10).place(x=220, y=190)

    def _delete_entry(self):
        """删除密码条目"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的记录！")
            return

        if messagebox.askyesno("确认", "确定要删除选中的记录吗？"):
            item = self.tree.item(selected[0])
            values = item['values']
            if values:
                entry_id = values[0]
                for i, entry in enumerate(self.entries):
                    if entry.id == entry_id:
                        self.entries.pop(i)
                        break

                self._reorder_ids()
                self._refresh_display()
                self.statusbar.config(text="删除成功！")

    def _on_double_click(self, event):
        """双击查看/编辑"""
        self._modify_entry()

    def _change_password(self):
        """修改访问密码"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改访问密码")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - \
            (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - \
            (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="原密码:", font=("Arial", 10)).place(x=50, y=30)
        old_pwd = tk.Entry(dialog, show="*", width=25)
        old_pwd.place(x=130, y=30)

        tk.Label(dialog, text="新密码:", font=("Arial", 10)).place(x=50, y=70)
        new_pwd = tk.Entry(dialog, show="*", width=25)
        new_pwd.place(x=130, y=70)

        tk.Label(dialog, text="确认密码:", font=("Arial", 10)).place(x=50, y=110)
        confirm_pwd = tk.Entry(dialog, show="*", width=25)
        confirm_pwd.place(x=130, y=110)

        def change():
            old = old_pwd.get()
            new = new_pwd.get()
            confirm = confirm_pwd.get()

            if old != self.access_password:
                messagebox.showerror("错误", "原密码错误！")
                return

            if new != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致！")
                return

            if not new:
                messagebox.showerror("错误", "新密码不能为空！")
                return

            self.access_password = new
            self._save_password()
            messagebox.showinfo("成功", "密码修改成功！")
            dialog.destroy()

        tk.Button(dialog, text="确定", command=change,
                  width=10).place(x=100, y=150)
        tk.Button(dialog, text="取消", command=dialog.destroy,
                  width=10).place(x=200, y=150)

    def _show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于", "密码管理器 v1.0\n\n一个简单的本地密码管理工具\n\n数据使用XOR加密存储")

    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    app = PasswordManagerApp()
    app.run()


if __name__ == "__main__":
    main()
