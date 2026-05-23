import tkinter as tk
        # 按钮
        self.start_btn = tk.Button(
            left,
            text="一键开启",
            font=("微软雅黑", 14),
            width=20,
            height=2,
            command=self.run_cmd
        )
        self.start_btn.grid(row=4, column=0, columnspan=2, pady=30)

        # CMD 输出框
        self.output = ScrolledText(right, bg="black", fg="#00ff00", font=("Consolas", 11))
        self.output.pack(fill="both", expand=True)

    def write_log(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)

    def run_cmd(self):
        threading.Thread(target=self.execute, daemon=True).start()

    def execute(self):
        ip = self.ip_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        mac = self.mac_entry.get().strip()

        exe_name = "go_build_zte_go.exe"

        current_dir = os.path.dirname(os.path.abspath(__file__))
        exe_path = os.path.join(current_dir, exe_name)

        if not os.path.exists(exe_path):
            self.write_log(f"[错误] 未找到 {exe_name}")
            return

        cmd = (
            f'"{exe_path}" '
            f'-addr http://{ip} '
            f'-mac {mac} '
            f'-password "{password}" '
            f'-username "{username}"'
        )

        self.write_log(f"> {cmd}")
        self.write_log("--------------------------------------------------")

        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.write_log(line.rstrip())

            process.wait()
            self.write_log("\n[完成] 命令执行结束")

        except Exception as e:
            self.write_log(f"[异常] {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TelnetTool(root)
    root.mainloop()